"""Sliding lockout for failed login attempts (TKT-0024 / REQUIREMENTS A5).

slowapi enforces a per-IP rate cap (5/min on /login). This module adds
the second layer: track only FAILED credential attempts per IP, and
when an IP accumulates `FAIL_THRESHOLD` failures within `FAIL_WINDOW`,
lock that IP out of /login for `LOCK_DURATION`.

State is in-memory -- the app is single-host, single-process; a
restart clears the counters which is acceptable (attacker would have
to start over anyway). If we ever move to multi-process, swap the
dicts for Redis.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

FAIL_WINDOW = timedelta(minutes=10)
LOCK_DURATION = timedelta(minutes=15)
FAIL_THRESHOLD = 5

_lock = threading.Lock()
_fails: dict[str, list[datetime]] = {}
_locked: dict[str, datetime] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def check_locked(ip: str) -> datetime | None:
    """Return `locked_until` UTC datetime if the IP is currently
    locked, else None. Auto-clears expired locks (and the related
    failure history) so a returning IP starts fresh."""
    with _lock:
        until = _locked.get(ip)
        if until is None:
            return None
        if _now() >= until:
            del _locked[ip]
            _fails.pop(ip, None)
            return None
        return until


def record_fail(ip: str) -> datetime | None:
    """Append a failure for `ip`. Returns `locked_until` if this
    failure pushed the IP over the threshold; otherwise None."""
    now = _now()
    with _lock:
        # Already locked -- don't extend; just return the existing
        # locked_until so the caller can surface the same Retry-After.
        until = _locked.get(ip)
        if until is not None and now < until:
            return until

        fails = [t for t in _fails.get(ip, []) if t > now - FAIL_WINDOW]
        fails.append(now)
        _fails[ip] = fails
        if len(fails) >= FAIL_THRESHOLD:
            locked_until = now + LOCK_DURATION
            _locked[ip] = locked_until
            return locked_until
        return None


def clear(ip: str) -> None:
    """Successful login wipes the IP's failure history and any lock."""
    with _lock:
        _fails.pop(ip, None)
        _locked.pop(ip, None)


def reset_all() -> None:
    """Test hook -- never called from production."""
    with _lock:
        _fails.clear()
        _locked.clear()
