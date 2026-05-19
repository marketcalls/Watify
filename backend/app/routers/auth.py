"""Auth endpoints (TKT-0024).

Five endpoints under /api/auth. JWT-in-httpOnly-cookies; no token ever
crosses the wire in JSON. Each endpoint refuses (503) when
`settings.app_secret` is empty (TKT-0031 boot guard).

Cookies:
- `watify_session` -- access token (15-min default).
- `watify_refresh` -- refresh token, signed with composite key so
  rotating `user.refresh_secret` invalidates every extant one in
  one move (logout, suspicious-activity reset, etc).
- Both: httpOnly, SameSite=Lax, Secure when scheme==https.

Rate limits use the configured slowapi limiter; auth-specific
sliding lockout is a separate module (`app/auth_lockout.py`).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from slowapi.util import get_remote_address
from sqlmodel import Session

from app import auth_lockout, auth_repo
from app.db import get_session
from app.jwt_tokens import (
    AuthConfigError,
    TokenInvalid,
    decode_access,
    decode_refresh,
    decode_unverified_sub,
    encode_access,
    encode_refresh,
)
from app.limiter import limiter
from app.models import User
from app.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---- Schemas ----------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=200)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class MeResponse(BaseModel):
    username: str
    created_at: datetime


class AuthAck(BaseModel):
    ok: bool = True
    username: str


class ProfileUpdateRequest(BaseModel):
    """At least one of `new_username` / `new_password` must be set; the
    router rejects the all-empty case with 422. `current_password` is
    always required -- the session cookie alone is not enough to change
    credentials (defence against an unattended browser).
    """

    current_password: str = Field(min_length=1, max_length=200)
    new_username: str | None = Field(default=None, min_length=1, max_length=80)
    new_password: str | None = Field(default=None, min_length=12, max_length=200)


# ---- Helpers ----------------------------------------------------------


def _require_configured() -> None:
    if not settings.app_secret:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "auth_not_configured",
                "detail": "WATIFY_APP_SECRET is empty; auth is disabled",
            },
        )


def _set_cookies(response: Response, request: Request, user: User) -> None:
    """Issue fresh access + refresh cookies for the user."""
    secure = request.url.scheme == "https"
    access = encode_access(user.id)
    refresh = encode_refresh(user.id, user.refresh_secret)
    response.set_cookie(
        "watify_session",
        access,
        max_age=settings.jwt_access_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    response.set_cookie(
        "watify_refresh",
        refresh,
        max_age=settings.jwt_refresh_days * 86400,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def _clear_cookies(response: Response, request: Request) -> None:
    secure = request.url.scheme == "https"
    for name in ("watify_session", "watify_refresh"):
        response.delete_cookie(name, path="/", samesite="lax", secure=secure, httponly=True)


def _client_ip(request: Request) -> str:
    return get_remote_address(request) or "unknown"


def _retry_after_seconds(until: datetime) -> int:
    delta = (until - datetime.now(timezone.utc)).total_seconds()
    return max(1, math.ceil(delta))


def _current_user_or_401(
    watify_session: str | None,
    db: Session,
) -> User:
    """TEMPORARY inline auth dependency. TKT-0025 will replace this
    with proper middleware that runs before slowapi for ALL /api/*.
    For now /api/auth/me is the only endpoint using it."""
    if not watify_session:
        raise HTTPException(status_code=401, detail="auth_required")
    try:
        payload = decode_access(watify_session)
    except (AuthConfigError, TokenInvalid):
        raise HTTPException(status_code=401, detail="auth_required")
    user = auth_repo.get_singleton(db)
    if user is None or str(user.id) != str(payload.get("sub")):
        raise HTTPException(status_code=401, detail="auth_required")
    return user


# ---- Endpoints --------------------------------------------------------


@router.post("/register", status_code=201)
@limiter.limit("3/minute")
def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_session),
) -> AuthAck:
    _require_configured()
    if auth_repo.count_users(db) > 0:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "registration_closed",
                "detail": "this app already has its single user",
            },
        )
    user = auth_repo.create_admin(db, body.username.strip(), body.password)
    auth_repo.touch_last_login(db, user)
    db.commit()
    db.refresh(user)
    _set_cookies(response, request, user)
    return AuthAck(username=user.username)


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_session),
) -> AuthAck:
    _require_configured()
    ip = _client_ip(request)
    until = auth_lockout.check_locked(ip)
    if until is not None:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "locked_out",
                "detail": "too many failed login attempts",
                "retry_after": _retry_after_seconds(until),
            },
            headers={"Retry-After": str(_retry_after_seconds(until))},
        )
    user = auth_repo.verify_credentials(db, body.username.strip(), body.password)
    if user is None:
        locked = auth_lockout.record_fail(ip)
        if locked is not None:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "locked_out",
                    "detail": "too many failed login attempts",
                    "retry_after": _retry_after_seconds(locked),
                },
                headers={"Retry-After": str(_retry_after_seconds(locked))},
            )
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials", "detail": "wrong username or password"},
        )
    auth_lockout.clear(ip)
    auth_repo.touch_last_login(db, user)
    db.commit()
    db.refresh(user)
    _set_cookies(response, request, user)
    return AuthAck(username=user.username)


@router.post("/refresh")
@limiter.limit("30/minute")
def refresh(
    request: Request,
    response: Response,
    watify_refresh: str | None = Cookie(default=None),
    db: Session = Depends(get_session),
) -> AuthAck:
    _require_configured()
    if not watify_refresh:
        raise HTTPException(status_code=401, detail="auth_required")
    try:
        sub = decode_unverified_sub(watify_refresh)
    except TokenInvalid:
        raise HTTPException(status_code=401, detail="auth_required")
    user = auth_repo.get_singleton(db)
    if user is None or str(user.id) != sub:
        raise HTTPException(status_code=401, detail="auth_required")
    try:
        decode_refresh(watify_refresh, user.refresh_secret)
    except TokenInvalid:
        raise HTTPException(status_code=401, detail="auth_required")
    _set_cookies(response, request, user)
    return AuthAck(username=user.username)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
) -> dict[str, bool]:
    _require_configured()
    user = auth_repo.get_singleton(db)
    if user is not None:
        auth_repo.rotate_refresh_secret(db, user)
        db.commit()
    _clear_cookies(response, request)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(
    watify_session: str | None = Cookie(default=None),
    db: Session = Depends(get_session),
) -> MeResponse:
    _require_configured()
    user = _current_user_or_401(watify_session, db)
    return MeResponse(username=user.username, created_at=user.created_at)


@router.patch("/profile")
@limiter.limit("5/minute")
def update_profile(
    request: Request,
    body: ProfileUpdateRequest,
    response: Response,
    watify_session: str | None = Cookie(default=None),
    db: Session = Depends(get_session),
) -> AuthAck:
    """Change the username and/or password of the singleton admin.

    Requires the current password regardless of the active session so a
    walk-up attacker on an unattended browser cannot change credentials.
    On success: rotates `refresh_secret` (invalidating all other refresh
    tokens) and re-issues fresh access + refresh cookies for the current
    response so the operator stays signed in.
    """
    _require_configured()
    user = _current_user_or_401(watify_session, db)

    new_username = body.new_username.strip() if body.new_username is not None else None
    new_password = body.new_password if body.new_password is not None else None

    if new_username is None and new_password is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "no_changes",
                "detail": "provide new_username or new_password",
            },
        )
    if new_username is not None and len(new_username) == 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_username", "detail": "username cannot be blank"},
        )

    # Verify current password BEFORE applying anything. Re-fetch via
    # the username path so we exercise the same code path as login and
    # so a corrupted hash surfaces consistently.
    verified = auth_repo.verify_credentials(db, user.username, body.current_password)
    if verified is None or verified.id != user.id:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials", "detail": "current password is wrong"},
        )

    # No-op early-out so a user who submits their existing values does
    # not pay the rehash + cookie reissue cost.
    same_username = new_username is None or new_username == user.username
    if same_username and new_password is None:
        raise HTTPException(
            status_code=422,
            detail={"error": "no_changes", "detail": "nothing to update"},
        )

    try:
        auth_repo.update_credentials(
            db,
            user,
            new_username=None if same_username else new_username,
            new_password=new_password,
        )
    except auth_repo.UsernameTaken:
        raise HTTPException(
            status_code=409,
            detail={"error": "username_taken", "detail": "username already in use"},
        )
    db.commit()
    db.refresh(user)
    _set_cookies(response, request, user)
    return AuthAck(username=user.username)
