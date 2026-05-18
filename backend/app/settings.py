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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
