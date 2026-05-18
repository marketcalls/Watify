"""Fernet wrap/unwrap for wars session bytes + persistence helpers.

The wars `export_session()` produces ~300 KB of Signal Protocol identity
keys, registration IDs, and noise-handshake state. Stored plaintext on
disk that file is enough for anyone with read access to impersonate
the linked device. TKT-0011 moves it into an encrypted column.

This module is the infrastructure for that: the actual wiring into
`WaSingleton` lives in TKT-0011b. Until then, callers that don't set
`WATIFY_SESSION_KEY` continue to use the file-backed mode.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlmodel import Session, select

from app.models import WaSession


class SessionCryptoError(RuntimeError):
    """Raised when a key is misconfigured or a ciphertext fails to decrypt.

    Distinct from `cryptography.fernet.InvalidToken` so callers can
    catch the family without depending on cryptography imports."""


def _fernet(key: str) -> Fernet:
    if not key:
        raise SessionCryptoError("WATIFY_SESSION_KEY is required for encrypted-session mode")
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as e:
        raise SessionCryptoError(
            "WATIFY_SESSION_KEY is not a valid Fernet key (must be url-safe base64-encoded 32-byte key)"
        ) from e


def generate_key() -> str:
    """Return a fresh url-safe base64 Fernet key suitable for env injection.

    Used by `scripts/generate_session_key.py` and the README bootstrap
    snippet. Never logs the value -- caller is responsible for not
    echoing it to logs / git.
    """
    return Fernet.generate_key().decode("ascii")


def encrypt_blob(blob: bytes, key: str) -> bytes:
    """Fernet-encrypt arbitrary bytes. Returns the ciphertext token."""
    return _fernet(key).encrypt(blob)


def decrypt_blob(ciphertext: bytes, key: str) -> bytes:
    """Fernet-decrypt. Raises SessionCryptoError if the token is invalid
    or was encrypted with a different key."""
    try:
        return _fernet(key).decrypt(ciphertext)
    except InvalidToken as e:
        raise SessionCryptoError("ciphertext failed to decrypt; key mismatch or tampered token") from e


def has_session(db: Session) -> bool:
    """Return True iff a WaSession row exists (regardless of decryptability)."""
    return db.exec(select(WaSession).where(WaSession.id == 1)).first() is not None


def load_session(db: Session, key: str) -> Optional[bytes]:
    """Read + decrypt the stored wars session blob. Returns None when no
    row exists. Raises SessionCryptoError on bad key / corrupted blob.
    """
    row = db.exec(select(WaSession).where(WaSession.id == 1)).first()
    if row is None:
        return None
    return decrypt_blob(row.ciphertext, key)


def save_session(db: Session, blob: bytes, key: str) -> None:
    """Encrypt and upsert the wars session blob into the singleton row.

    Caller commits. Idempotent -- replaces any existing row.
    """
    ciphertext = encrypt_blob(blob, key)
    existing = db.exec(select(WaSession).where(WaSession.id == 1)).first()
    if existing is None:
        db.add(WaSession(id=1, ciphertext=ciphertext))
    else:
        existing.ciphertext = ciphertext
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)


def clear_session(db: Session) -> None:
    """Drop the stored row. Used on disconnect/unpair."""
    row = db.exec(select(WaSession).where(WaSession.id == 1)).first()
    if row is not None:
        db.delete(row)
