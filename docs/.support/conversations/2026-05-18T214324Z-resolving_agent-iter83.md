# Iteration 83 -- Resolving Agent (TKT-0014 backend slice)

- **Started**: 2026-05-18T21:43:24Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0014 (P2 backend) -- pair-code mode backend slice

## Plan
Ship the backend half this iteration. Four edits:

1. **`backend/app/whatsapp.py`**:
   - Add `pair_code: Optional[str] = None` to `ClientState`.
   - Extend `_set()` with `pair_code` + `clear_pair_code` kwargs.
   - Mirror in `snapshot()` so the DTO carries it.
   - Add `@wa.on_pair_code` callback (after the existing `@wa.on_qr` block) -- updates state with the code and logs. Per the existing pattern: only the worker thread can call into `wa` (PyO3 !Send), but `cls._set()` is just touching a Python `ClientState` dataclass and the lock -- safe from any thread. The wars Tokio callback can call `_set` directly without going through `_cmd_q`.
   - Extend the `connect` command in the worker loop: when the command arg is non-None, treat it as the phone for pair-code mode and call `wa.connect(arg)`; else `wa.connect()`.
   - Extend `WaSingleton.connect()` public method to accept `phone: str | None = None` and queue `("connect", phone)` instead of `("connect", None)`.
   - Clear `pair_code` on disconnect + on cycle + on `on_connected` (transitioning to ready makes the code stale).
2. **`backend/app/routers/whatsapp.py`**:
   - `WaConnectRequest` Pydantic model with optional `phone: str | None`. Validate with the existing `normalize_phone` helper (E.164) -- raise 422 on invalid.
   - Extend `WaState` response with `pair_code: str | None = None`.
   - `connect()` accepts an optional JSON body (FastAPI `Optional[WaConnectRequest]`); when `phone` is set, call `WaSingleton.connect(phone)`.
   - `_snapshot_to_dto` carries the pair_code through.
3. **Smoke**:
   - `POST /api/wa/connect` (no body) -> 200, state=`pairing|ready`, no pair_code.
   - `POST /api/wa/connect {"phone":"+919876543210"}` -> 200, the worker calls `wa.connect("+919876543210")` and `@on_pair_code` fires shortly after, surfacing the 8-char code in subsequent `GET /api/wa/state`.
   - Invalid phone -> 422.
   - This smoke cannot fully exercise wars without a live phone, but it confirms the FastAPI surface, the validator, the worker plumbing, and the state propagation.
4. `py_compile` clean.

Out of scope: /connect page mode-switch (frontend half). I'll file `TKT-0035: pair-code frontend toggle + panel` at end-of-iter, so the queue tracks the pending follow-on cleanly.

## Actions

1. Marked TKT-0014 `inprogress`.
2. Edited `backend/app/whatsapp.py`: added `pair_code` field to `ClientState`, threaded it through `_set` (+ `clear_pair_code` bool), `snapshot`, the `@wa.on_pair_code` callback (gated on `hasattr` for forward/backward compat), the worker `connect` branch (accepts a phone arg and calls `wa.connect(phone)`), `on_connected`/`disconnect`/`cycle`/`stop` all clear the code, and the public `WaSingleton.connect(phone: Optional[str] = None)`.
3. Edited `backend/app/routers/whatsapp.py`: added `WaConnectRequest` body model, extended `WaState` response with `pair_code`, made the `connect` handler accept an optional body, validate the phone via `normalize_phone`, raise 422 on invalid.
4. `uv run python -m py_compile app/whatsapp.py app/routers/whatsapp.py` -> clean.
5. Restarted backend (pid 16032), logged in to get the auth cookie, ran 4 smokes (A: no-body 200 QR path; B: state includes pair_code field; C: phone-body 200 pair-code path; D: garbage phone 422 invalid_phone).
6. Filed TKT-0035 (P3 frontend) for the /connect mode-switch + PairCodePanel.
7. Marked TKT-0014 `resolved` with a detailed Resolution history entry.

## Outcome
TKT-0014 backend slice resolved. Pair-code mode is wired end-to-end on the backend; the QR flow is fully backward-compatible (empty body). End-to-end exercise of the `@on_pair_code` callback requires a live phone -- the Verification Agent will confirm the structural pieces (schema, validator, worker plumbing) via the same 4-smoke pattern. Next: Verification Agent for TKT-0014.
