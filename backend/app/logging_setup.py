"""Single place that configures backend logging.

Two handlers are installed on the root logger: a rotating file at
`settings.log_file` and stderr. A `PhoneRedactionFilter` runs over every
record's formatted message and replaces phone-like digit runs with the
shape `+91XXXXXX1234`, so accidentally-logged contact numbers do not
leak to disk.

Output format is a single line per record:
    `<ISO time> <level> <logger> <message>`
suitable for grep, jq -R, and Vector / Promtail ingestion.
"""

from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

from app.settings import settings

_PHONE_RE = re.compile(r"\+?\d{8,15}")


def _redact_phone_str(s: str) -> str:
    def _sub(m: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) <= 4:
            return m.group(0)
        prefix = digits[:2]
        suffix = digits[-4:]
        return f"{prefix}{'X' * (len(digits) - 6)}{suffix}"

    return _PHONE_RE.sub(_sub, s)


class PhoneRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            redacted = _redact_phone_str(msg)
            if redacted != msg:
                record.msg = redacted
                record.args = None
        except Exception:  # noqa: BLE001
            pass
        return True


def configure() -> None:
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    # Wipe handlers that uvicorn or earlier configure() calls installed
    # so we have a deterministic configuration.
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.addFilter(PhoneRedactionFilter())
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.addFilter(PhoneRedactionFilter())
    root.addHandler(stream_handler)

    # Tame uvicorn's noisy access logger but keep errors.
    logging.getLogger("uvicorn.access").setLevel("INFO")
    logging.getLogger("apscheduler").setLevel("INFO")
