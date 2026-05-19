"""User DAO + register-once lock (TKT-0023).

Watify is single-user. The `users` table holds exactly one row; any
second `create_admin` call raises `RegistrationClosed`. Auth endpoints
in TKT-0024 surface this as 409 `registration_closed`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, func, select

from app.auth_crypto import (
    AuthCryptoError,
    generate_refresh_secret,
    hash_password,
    verify_password as _verify_password,
)
from app.models import User


class RegistrationClosed(RuntimeError):
    """Raised when `create_admin` is called and a user already exists."""


class UsernameTaken(RuntimeError):
    """Raised when a profile update tries to rename to an already-used
    name. In single-user mode this only fires if the new name equals the
    sentinel of some future second row -- the UNIQUE index would also
    catch it, but raising here lets the router return a clean 409."""


def count_users(db: Session) -> int:
    return int(db.exec(select(func.count()).select_from(User)).one())


def get_user(db: Session, username: str) -> User | None:
    if not username:
        return None
    return db.exec(select(User).where(User.username == username)).first()


def get_singleton(db: Session) -> User | None:
    """Return the singleton User row regardless of username. Used by
    the JWT auth dependency to resolve the user from the `sub` claim
    (which is always the row id, 1)."""
    return db.exec(select(User).where(User.id == 1)).first()


def create_admin(db: Session, username: str, password: str) -> User:
    """Create the single user. Raises `RegistrationClosed` on the
    second call. Caller commits. Caller is also responsible for
    validating password length / username shape before calling this.
    """
    if count_users(db) > 0:
        raise RegistrationClosed("this app already has its single user")
    user = User(
        id=1,
        username=username,
        password_hash=hash_password(password),
        refresh_secret=generate_refresh_secret(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    return user


def verify_credentials(db: Session, username: str, password: str) -> User | None:
    """Return the User on a successful match, otherwise None. Hides the
    cause (no user / wrong password) so the caller cannot leak which
    side of the credential is invalid.
    """
    user = get_user(db, username)
    if user is None:
        # Run a dummy verify to keep timing roughly constant -- attacker
        # cannot probe usernames by measuring response time.
        try:
            _verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$" + "x" * 22 + "$" + "y" * 43)
        except AuthCryptoError:
            pass
        return None
    if _verify_password(password, user.password_hash):
        return user
    return None


def rotate_refresh_secret(db: Session, user: User) -> None:
    """Rotate the per-user refresh-secret. Called on logout (so a
    stolen refresh token is invalidated) and could be called on
    suspicious activity in the future."""
    user.refresh_secret = generate_refresh_secret()
    db.add(user)


def touch_last_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)


def update_credentials(
    db: Session,
    user: User,
    *,
    new_username: str | None,
    new_password: str | None,
) -> User:
    """Apply username and/or password changes to the singleton user and
    rotate the refresh secret. Caller commits.

    The refresh-secret rotation invalidates every extant refresh token,
    so any other browser the operator left signed in will be forced to
    re-authenticate the next time its access token expires. This is the
    desired behavior on a credential change.
    """
    if new_username is not None:
        clash = get_user(db, new_username)
        if clash is not None and clash.id != user.id:
            raise UsernameTaken("username already in use")
        user.username = new_username
    if new_password is not None:
        user.password_hash = hash_password(new_password)
    user.refresh_secret = generate_refresh_secret()
    db.add(user)
    return user
