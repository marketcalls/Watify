"""Single source of truth for runtime configuration.

Reads from `backend/.env` (gitignored) plus the process environment.
Defaults match the values that were previously hardcoded so the app
keeps working with no env file present.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="WATIFY_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000
    cors_origin: str = "http://localhost:3000"

    app_db: str = Field(default=str(_BACKEND_DIR / "app.db"))
    whatsapp_db: str = Field(default=str(_BACKEND_DIR / "whatsapp.db"))

    min_delay_s: int = 3
    max_delay_s: int = 30
    group_max_contacts: int = 20

    log_level: str = "INFO"
    log_file: str = str(_BACKEND_DIR.parent / "docs" / ".support" / "logs" / "backend.log")

    # TKT-0011: when set, the WaSingleton stores the wars session as a
    # Fernet-encrypted blob in `app.db` instead of plaintext on disk.
    # Generate a key with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Leave unset for legacy file-backed mode (TKT-0011b will eventually
    # auto-migrate any existing whatsapp.db once a key is provided).
    session_encryption_key: str | None = None

    # TKT-0015: slowapi rate-limit strings for the three send endpoints.
    # Format is slowapi's "N/period" (e.g. "5/minute", "100/hour"). The
    # dashboard SoftCapBanner is a soft UX signal; these are the hard
    # backend caps that stop a buggy loop from triggering a WhatsApp ban.
    rate_limit_test_self: str = "15/minute"
    rate_limit_test_to: str = "10/minute"
    rate_limit_send: str = "5/minute"

    # TKT-0005: optional explicit override for the linked-device owner
    # phone. wars 0.1.3 does not expose an `owner` accessor and we
    # avoid sending a sentinel-to-self just to discover it. Passive
    # learning via @wa.on_message covers most cases; this env is the
    # fallback when the operator wants the Ready panel populated
    # before any echo arrives.
    owner_phone: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
