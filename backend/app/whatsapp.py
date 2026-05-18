"""Thread-safe wars singleton + state machine.

The `wars.WhatsApp` PyO3 object is `!Send` — every method call on it must
happen on the thread that constructed it, or the binding panics. To make
this usable from FastAPI handlers (which run on a thread pool), we own
the wa instance on a single long-lived worker thread and post commands
to it through a queue.

Callbacks (`on_qr`, `on_connected`, `on_disconnect`) fire on the wars
internal Tokio thread; they only mutate `ClientState` under a lock, so
the Send constraint does not apply to them.

Per wars.md §7, WhatsApp Web is one-device-per-session — never run
multiple worker processes against the same `whatsapp.db`.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

from app.settings import settings

if TYPE_CHECKING:
    from wars import WhatsApp  # type-only; runtime import goes through _import_wars

# TKT-0012 + TKT-0013: lazy wars import. The wars wheel is large
# (~30 MB native code with bundled Rust). If it is missing or fails
# to build, the rest of the FastAPI app still has to boot so the
# operator can hit /api/health, /api/groups, /api/jobs and read the
# /connect page's error state. The two pieces stay paired here:
#   - RUST_LOG defaults via setdefault BEFORE the actual import.
#   - WarsNotInstalled sentinel raised on ImportError / build error.
#     Worker thread catches it and sets state="error" + last_error so
#     the frontend ErrorPanel surfaces the install hint.

_WARS_INSTALL_HINT = (
    "wars package is not installed or failed to build. Run "
    "`uv sync` (or `uv pip install wars`) inside the backend/ "
    "directory to enable the WhatsApp integration."
)


class WarsNotInstalled(RuntimeError):
    """Sentinel raised when `import wars` fails. Carries the friendly
    install hint as its message and preserves the original cause for
    debugging."""

    def __init__(self, cause: BaseException | None = None) -> None:
        super().__init__(_WARS_INSTALL_HINT)
        if cause is not None:
            self.__cause__ = cause


# Module-level cache. Two-level: once we've tried and failed we don't
# retry on every connect call -- the operator needs to fix their env
# and restart.
_wars_module: Any | None = None
_wars_attempt_failed: bool = False
_wars_import_error: BaseException | None = None
_wars_import_lock = threading.Lock()


def _import_wars() -> Any:
    """Lazily import wars. Caches the module on success and the error
    on failure. Sets `RUST_LOG` defaults exactly once, immediately
    before the first import attempt (TKT-0012).
    """
    global _wars_module, _wars_attempt_failed, _wars_import_error
    with _wars_import_lock:
        if _wars_module is not None:
            return _wars_module
        if _wars_attempt_failed:
            raise WarsNotInstalled(_wars_import_error)

        os.environ.setdefault(
            "RUST_LOG",
            "error"
            ",wacore::send=off"
            ",whatsapp_rust::message=off"
            ",wacore_libsignal::protocol::session_cipher=off",
        )
        try:
            import wars as _mod
        except Exception as e:  # noqa: BLE001 -- catch ImportError + Rust build errors
            _wars_attempt_failed = True
            _wars_import_error = e
            log.exception("wars import failed; backend will report wars_not_installed state")
            raise WarsNotInstalled(e) from e
        _wars_module = _mod
        log.info("wars module loaded lazily (version=%s)", getattr(_mod, "__version__", "?"))
        return _wars_module

log = logging.getLogger(__name__)

State = Literal["disconnected", "pairing", "ready", "error"]

DB_PATH = Path(settings.whatsapp_db).resolve()

# Auto-cycle settings. wars's pairing window is ~5 minutes; if `on_qr`
# stops firing for more than QR_STALE_THRESHOLD_S the watchdog cycles
# the worker so the user is not left staring at a permanently expired
# QR. See TKT-0019.
QR_STALE_THRESHOLD_S = 45
WATCHDOG_INTERVAL_S = 5


@dataclass
class ClientState:
    state: State = "disconnected"
    qr_data_url: Optional[str] = None
    owner_phone: Optional[str] = None
    last_error: Optional[str] = None
    last_event_at: Optional[str] = None
    db_path: str = field(default_factory=lambda: str(DB_PATH))


class WaSingleton:
    _state = ClientState()
    _state_lock = threading.Lock()
    _cmd_q: "queue.Queue[tuple[str, Any]]" = queue.Queue()
    _worker: Optional[threading.Thread] = None
    _worker_lock = threading.Lock()
    _ready_event = threading.Event()

    # Watchdog state (TKT-0019). Updated by _on_qr only -- distinct from
    # the general `last_event_at` which moves on every state change.
    _last_qr_at: Optional[datetime] = None
    _cycling: bool = False
    _auto_cycle_count: int = 0
    _watchdog: Optional[threading.Thread] = None

    # --- state helpers ---

    @classmethod
    def snapshot(cls) -> ClientState:
        with cls._state_lock:
            return ClientState(
                state=cls._state.state,
                qr_data_url=cls._state.qr_data_url,
                owner_phone=cls._state.owner_phone,
                last_error=cls._state.last_error,
                last_event_at=cls._state.last_event_at,
                db_path=cls._state.db_path,
            )

    @classmethod
    def _set(
        cls,
        *,
        state: Optional[State] = None,
        qr_data_url: Optional[str] = None,
        clear_qr: bool = False,
        owner_phone: Optional[str] = None,
        last_error: Optional[str] = None,
        clear_error: bool = False,
    ) -> None:
        with cls._state_lock:
            if state is not None:
                cls._state.state = state
            if clear_qr:
                cls._state.qr_data_url = None
            elif qr_data_url is not None:
                cls._state.qr_data_url = qr_data_url
            if owner_phone is not None:
                cls._state.owner_phone = owner_phone
            if clear_error:
                cls._state.last_error = None
            elif last_error is not None:
                cls._state.last_error = last_error
            cls._state.last_event_at = datetime.now(timezone.utc).isoformat()

    # --- worker lifecycle ---

    @classmethod
    def _ensure_worker(cls) -> None:
        with cls._worker_lock:
            if cls._worker is None or not cls._worker.is_alive():
                cls._ready_event.clear()
                cls._worker = threading.Thread(
                    target=cls._worker_loop, name="wars-worker", daemon=True
                )
                cls._worker.start()
            if cls._watchdog is None or not cls._watchdog.is_alive():
                cls._watchdog = threading.Thread(
                    target=cls._watchdog_loop,
                    name="wars-watchdog",
                    daemon=True,
                )
                cls._watchdog.start()

    @classmethod
    def _watchdog_loop(cls) -> None:
        """TKT-0019. Polls state every WATCHDOG_INTERVAL_S. If we're
        sitting in `pairing` with no fresh `on_qr` for longer than
        QR_STALE_THRESHOLD_S, queue a `cycle` command on the worker to
        re-handshake. Bumps `_auto_cycle_count` for diagnostics.
        """
        log.info(
            "wars-watchdog started (threshold=%ss interval=%ss)",
            QR_STALE_THRESHOLD_S,
            WATCHDOG_INTERVAL_S,
        )
        while True:
            time.sleep(WATCHDOG_INTERVAL_S)
            snap = cls.snapshot()
            if snap.state != "pairing":
                continue
            if cls._cycling:
                continue
            with cls._state_lock:
                last_qr = cls._last_qr_at
            if last_qr is None:
                continue
            age = (datetime.now(timezone.utc) - last_qr).total_seconds()
            if age <= QR_STALE_THRESHOLD_S:
                continue
            cls._auto_cycle_count += 1
            log.warning(
                "wars-watchdog: no QR for %.0fs (>%ss), auto-cycling (count=%s)",
                age,
                QR_STALE_THRESHOLD_S,
                cls._auto_cycle_count,
            )
            cls._cmd_q.put(("cycle", None))

    @staticmethod
    def _delete_legacy_wa_db_files() -> int:
        """Remove `whatsapp.db` + sidecars from disk. Returns count of
        files actually removed. Safe to call when wars doesn't hold the
        files open -- on Windows in particular, this works at boot
        before `_build_wa` opens anything."""
        n = 0
        for path in (
            DB_PATH,
            DB_PATH.with_suffix(".db-wal"),
            DB_PATH.with_suffix(".db-shm"),
            DB_PATH.with_suffix(".db-journal"),
        ):
            try:
                if path.exists():
                    path.unlink()
                    n += 1
            except OSError as e:
                log.warning("could not remove %s: %s", path, e)
        return n

    @classmethod
    def _build_wa(cls) -> tuple["WhatsApp", bool]:
        """Pick a wars constructor based on session-encryption settings.

        Returns (wa_instance, migrated_from_file). The bool is True when
        we opened the legacy `whatsapp.db` file under encrypted mode and
        the worker should export+save+delete on first ready transition.

        Modes:
        - key unset: legacy file-backed -> WhatsApp(DB_PATH). Bool False.
        - key set + WaSession row exists: in-memory -> WhatsApp.from_bytes(blob). Bool False.
        - key set + no row but legacy file exists: bridge -> WhatsApp(DB_PATH), True (migrate after first ready).
        - key set + neither: fresh -> WhatsApp() (in-memory). Bool False.
        """
        wars = _import_wars()
        key = settings.session_encryption_key
        if not key:
            log.info("wars: legacy file-backed mode (whatsapp.db at %s)", DB_PATH)
            return wars.WhatsApp(str(DB_PATH)), False

        # Encrypted mode.
        from sqlmodel import Session

        from app import session_crypto as sc
        from app.db import engine

        try:
            with Session(engine) as db:
                if sc.has_session(db):
                    blob = sc.load_session(db, key)
                    log.info(
                        "wars: encrypted mode -- booting from WaSession row (%dB plaintext, in-memory)",
                        len(blob) if blob else 0,
                    )
                    # Cleanup any stale `whatsapp.db` that a previous
                    # run could not unlink while wars held it open.
                    # Safe here: we have not constructed wa yet.
                    removed = cls._delete_legacy_wa_db_files()
                    if removed:
                        log.info(
                            "wars: removed %d stale legacy whatsapp.db file(s) at boot",
                            removed,
                        )
                    return wars.WhatsApp.from_bytes(blob), False
        except Exception as e:  # noqa: BLE001
            log.exception(
                "wars: encrypted mode -- could not load WaSession (%s); falling back to fresh start",
                e,
            )

        if DB_PATH.exists():
            log.info(
                "wars: encrypted mode -- WaSession empty, whatsapp.db exists; will migrate on first ready",
            )
            return wars.WhatsApp(str(DB_PATH)), True

        log.info("wars: encrypted mode -- fresh start (in-memory, awaits pair)")
        return wars.WhatsApp(), False

    @classmethod
    def _worker_loop(cls) -> None:
        try:
            wa, migrated_from_file = cls._build_wa()
            migrate_state = {"pending": migrated_from_file}

            # TKT-0005: seed owner_phone from the env override if set.
            # Passive learning via @wa.on_message can still overwrite it
            # once a real echo arrives.
            if settings.owner_phone:
                from app.jid import normalize_phone, InvalidPhoneError

                try:
                    cls._set(owner_phone=normalize_phone(settings.owner_phone))
                    log.info("wars: owner_phone seeded from WATIFY_OWNER_PHONE")
                except InvalidPhoneError as e:
                    log.warning("WATIFY_OWNER_PHONE invalid (%s); ignoring", e)

            def _persist_session() -> None:
                """TKT-0021: on every state -> ready transition, export the
                wars session bytes, Fernet-encrypt them, upsert into
                WaSession. If the worker booted in migration mode, also
                delete the legacy `whatsapp.db` file + its sidecars now
                that the encrypted blob is durably stored.

                No-op when WATIFY_SESSION_ENCRYPTION_KEY is unset.
                Failures are logged and swallowed so a transient write
                error doesn't crash the worker.
                """
                key = settings.session_encryption_key
                if not key:
                    return
                try:
                    blob = wa.export_session()
                except Exception as e:  # noqa: BLE001
                    log.warning("wars: export_session failed (%s); skipping persist", e)
                    return
                try:
                    from sqlmodel import Session

                    from app import session_crypto as sc
                    from app.db import engine

                    with Session(engine) as db:
                        sc.save_session(db, blob, key)
                        db.commit()
                    log.info(
                        "wars: persisted encrypted session (plaintext=%dB)",
                        len(blob),
                    )
                except Exception as e:  # noqa: BLE001
                    log.exception("wars: save_session failed (%s); will retry on next ready", e)
                    return
                if migrate_state["pending"]:
                    # On POSIX this unlinks immediately. On Windows wars
                    # still holds open file handles, so unlink() typically
                    # fails -- the next backend boot will clean up via
                    # _build_wa's stale-file sweep. Either way, we clear
                    # the flag because the encrypted blob is now durable.
                    removed = cls._delete_legacy_wa_db_files()
                    migrate_state["pending"] = False
                    if removed:
                        log.info(
                            "wars: legacy whatsapp.db removed (%d files) -- encrypted mode is now the only at-rest store",
                            removed,
                        )
                    else:
                        log.info(
                            "wars: legacy whatsapp.db still held by wars (Windows file lock); next boot's stale-file sweep will remove it"
                        )


            wars_mod = _import_wars()  # cached; already loaded by _build_wa above

            @wa.on_qr
            def _on_qr(code: str) -> None:
                try:
                    durl = wars_mod.qr_to_data_url(code)
                except Exception as e:  # noqa: BLE001
                    log.warning("qr_to_data_url failed: %s", e)
                    durl = None
                with cls._state_lock:
                    cls._last_qr_at = datetime.now(timezone.utc)
                cls._set(state="pairing", qr_data_url=durl)
                log.info(
                    "wars on_qr: state=pairing qr_len=%s",
                    len(durl) if durl else 0,
                )

            @wa.on_connected
            def _on_connected() -> None:
                # Callback fires on the wars Tokio thread (!= worker thread).
                # Don't touch `wa` here -- PyO3 !Send panics. Queue the
                # persist for the worker, which owns wa.
                cls._set(state="ready", clear_qr=True, clear_error=True)
                log.info("wars on_connected: state=ready")
                cls._cmd_q.put(("persist", None))

            @wa.on_disconnect
            def _on_disconnect() -> None:
                # During a worker-initiated cycle (TKT-0019 watchdog),
                # wars fires on_disconnect mid-cycle. Don't flip the UI
                # to "disconnected" -- the immediate reconnect will take
                # us back through on_qr.
                if cls._cycling:
                    log.info("wars on_disconnect: suppressed during auto-cycle")
                    return
                cls._set(state="disconnected", clear_qr=True)
                log.info("wars on_disconnect: state=disconnected")

            @wa.on_message
            def _on_message(msg: Any) -> None:
                # TKT-0005: wars 0.1.3 has no owner accessor on the
                # WhatsApp object. The cheapest way to learn the linked
                # device's own number is to watch echoes of the user's
                # own outgoing messages -- they arrive with
                # is_from_me=True and `sender = <our-jid>`. We only
                # learn once; the explicit settings.owner_phone always
                # wins if set.
                if cls.snapshot().owner_phone:
                    return
                try:
                    if not getattr(msg, "is_from_me", False):
                        return
                    sender = getattr(msg, "sender", "") or ""
                    # 1:1 JIDs look like "<digits>@s.whatsapp.net"; group
                    # senders end in "@g.us" and are ignored.
                    if "@s.whatsapp.net" not in sender:
                        return
                    digits = sender.split("@", 1)[0]
                    # Strip any device suffix like "12345:67".
                    digits = digits.split(":", 1)[0]
                    if digits.isdigit() and len(digits) >= 6:
                        cls._set(owner_phone=digits)
                        log.info("wars: learned owner_phone passively from on_message echo")
                except Exception as e:  # noqa: BLE001
                    log.debug("on_message owner-learning failed: %s", e)
        except WarsNotInstalled as e:
            # TKT-0013: wars wheel missing or failed to build. Surface
            # the friendly install hint via state.last_error; rest of
            # the FastAPI app (groups, jobs, health) keeps working.
            log.error("wars build skipped: %s", e)
            cls._set(state="error", last_error=f"wars_not_installed: {e}")
            return
        except Exception as e:  # noqa: BLE001
            log.exception("wars build failed")
            cls._set(state="error", last_error=f"build_failed: {e}")
            return

        cls._ready_event.set()
        log.info("wars-worker ready, waiting for commands")

        def _check_connected() -> None:
            """TKT-0020: wars 0.1.3 does not always fire `on_connected`
            after a successful re-handshake from a persisted session, so
            our state can stay at "pairing" forever even though
            `wa.send` works. Poll `wa.is_connected()` between commands
            and flip state to "ready" when it returns True. Idempotent
            -- safe to call repeatedly."""
            try:
                if cls.snapshot().state == "pairing" and wa.is_connected():
                    cls._set(state="ready", clear_qr=True, clear_error=True)
                    log.info(
                        "wars: is_connected()==True, state=ready (callback fallback)"
                    )
                    _persist_session()
            except Exception:  # noqa: BLE001
                pass

        while True:
            try:
                cmd, arg = cls._cmd_q.get(timeout=2.0)
            except queue.Empty:
                _check_connected()
                continue
            except Exception:  # noqa: BLE001
                continue
            if cmd == "stop":
                try:
                    wa.disconnect()
                except Exception:  # noqa: BLE001
                    pass
                cls._set(state="disconnected", clear_qr=True)
                return
            try:
                if cmd == "persist":
                    _persist_session()
                    continue
                if cmd == "connect":
                    wa.connect()
                    _check_connected()
                elif cmd == "disconnect":
                    wa.disconnect()
                    cls._set(state="disconnected", clear_qr=True)
                elif cmd == "cycle":
                    # TKT-0019: watchdog-triggered fresh-QR refresh.
                    cls._cycling = True
                    try:
                        try:
                            wa.disconnect()
                        except Exception:  # noqa: BLE001
                            pass
                        # Brief settle so wars's internal Tokio runtime
                        # releases the previous noise session before we
                        # ask for a new one.
                        time.sleep(0.2)
                        wa.connect()
                    finally:
                        cls._cycling = False
                elif cmd == "send_self":
                    wa.send(arg)
                elif cmd == "send_to":
                    phone, text = arg
                    wa.send(phone, text)
            except Exception as e:  # noqa: BLE001
                log.exception("wars cmd %s failed", cmd)
                cls._set(state="error", last_error=f"{cmd}: {e}")

    # --- public API ---

    @classmethod
    def connect(cls) -> ClientState:
        cls._ensure_worker()
        cls._ready_event.wait(timeout=5.0)
        snap = cls.snapshot()
        if snap.state in ("ready", "pairing"):
            return snap
        cls._set(state="pairing", clear_error=True)
        cls._cmd_q.put(("connect", None))
        return cls.snapshot()

    @classmethod
    def disconnect(cls) -> ClientState:
        # Optimistic state flip: wars.disconnect is idempotent, the worker
        # will catch up. UI doesn't have to wait one poll for the truth.
        cls._set(state="disconnected", clear_qr=True)
        if cls._worker is not None and cls._worker.is_alive():
            cls._cmd_q.put(("disconnect", None))
        return cls.snapshot()

    @classmethod
    def send_self(cls, text: str) -> None:
        cls._cmd_q.put(("send_self", text))

    @classmethod
    def send_to(cls, phone: str, text: str) -> None:
        cls._cmd_q.put(("send_to", (phone, text)))
