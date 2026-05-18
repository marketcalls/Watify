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
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from wars import WhatsApp, qr_to_data_url

from app.settings import settings

log = logging.getLogger(__name__)

State = Literal["disconnected", "pairing", "ready", "error"]

DB_PATH = Path(settings.whatsapp_db).resolve()


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
            if cls._worker is not None and cls._worker.is_alive():
                return
            cls._ready_event.clear()
            cls._worker = threading.Thread(
                target=cls._worker_loop, name="wars-worker", daemon=True
            )
            cls._worker.start()

    @classmethod
    def _worker_loop(cls) -> None:
        try:
            wa = WhatsApp(str(DB_PATH))

            @wa.on_qr
            def _on_qr(code: str) -> None:
                try:
                    durl = qr_to_data_url(code)
                except Exception as e:  # noqa: BLE001
                    log.warning("qr_to_data_url failed: %s", e)
                    durl = None
                cls._set(state="pairing", qr_data_url=durl)
                log.info(
                    "wars on_qr: state=pairing qr_len=%s",
                    len(durl) if durl else 0,
                )

            @wa.on_connected
            def _on_connected() -> None:
                cls._set(state="ready", clear_qr=True, clear_error=True)
                log.info("wars on_connected: state=ready")

            @wa.on_disconnect
            def _on_disconnect() -> None:
                cls._set(state="disconnected", clear_qr=True)
                log.info("wars on_disconnect: state=disconnected")
        except Exception as e:  # noqa: BLE001
            log.exception("wars build failed")
            cls._set(state="error", last_error=f"build_failed: {e}")
            return

        cls._ready_event.set()
        log.info("wars-worker ready, waiting for commands")

        while True:
            try:
                cmd, arg = cls._cmd_q.get()
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
                if cmd == "connect":
                    wa.connect()
                elif cmd == "disconnect":
                    wa.disconnect()
                    cls._set(state="disconnected", clear_qr=True)
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
