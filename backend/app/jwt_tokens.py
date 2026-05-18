"""JWT encode / decode for Watify auth (TKT-0024).

Two token types:
- **access** -- HS256 signed with `settings.app_secret`. Short TTL
  (`jwt_access_minutes`, default 15). Used by the auth dependency
  on every authed request.
- **refresh** -- HS256 signed with a composite key
  `settings.app_secret + user.refresh_secret`. Long TTL
  (`jwt_refresh_days`, default 7). Rotating `user.refresh_secret`
  (done on logout, or anytime we want to invalidate all sessions)
  immediately breaks every existing refresh token because the HMAC
  no longer verifies. No revocation list needed.

Each token carries `"typ": "access" | "refresh"` so the access decoder
rejects a refresh token (and vice versa) -- a stolen refresh token
cannot be reused as an access token.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.settings import settings

ALGORITHM = "HS256"


class AuthConfigError(RuntimeError):
    """Raised by encode/decode when `app_secret` is empty. The auth
    router catches this and returns 503 `auth_not_configured`."""


class TokenInvalid(RuntimeError):
    """Raised when a token is malformed, has the wrong `typ`, or fails
    signature / expiry verification. Caller returns 401."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_secret() -> str:
    if not settings.app_secret:
        raise AuthConfigError("WATIFY_APP_SECRET is not set; auth is disabled")
    return settings.app_secret


def encode_access(user_id: int) -> str:
    secret = _require_secret()
    now = _now()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access(token: str) -> dict[str, Any]:
    secret = _require_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise TokenInvalid(f"access token invalid: {e}") from e
    if payload.get("typ") != "access":
        raise TokenInvalid("token typ != access")
    return payload


def encode_refresh(user_id: int, refresh_secret: str) -> str:
    secret = _require_secret() + refresh_secret
    now = _now()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_days)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_refresh(token: str, refresh_secret: str) -> dict[str, Any]:
    secret = _require_secret() + refresh_secret
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise TokenInvalid(f"refresh token invalid: {e}") from e
    if payload.get("typ") != "refresh":
        raise TokenInvalid("token typ != refresh")
    return payload


def decode_unverified_sub(token: str) -> str:
    """Pull the `sub` claim WITHOUT verifying signature or expiry.

    Used only by the refresh flow: we need `sub` to look up the user
    so we can fetch their `refresh_secret`, then we call
    `decode_refresh()` to fully verify. NEVER trust this value for
    authorization decisions on its own.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as e:
        raise TokenInvalid("cannot decode unverified sub") from e
    sub = payload.get("sub")
    if not sub:
        raise TokenInvalid("missing sub claim")
    return str(sub)
