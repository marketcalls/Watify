# Iteration 33 — Resolving Agent (TKT-0019)

- **Started**: 2026-05-18T17:35:56Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0019 (P2 backend) — auto-cycle wars when on_qr stops

## Trigger
User reported live: "QR expired. Waiting for a fresh one to load... fresh one is not loading yet." That is exactly TKT-0019's symptom -- wars's 5-minute pairing window timed out and on_qr stopped firing. Manually cycled (`disconnect`+`connect`) for immediate relief; now shipping the durable fix.

## Scope decision
Take TKT-0019 ahead of TKT-0011 in the priority order because (a) it directly unblocks the user's live pairing session, (b) TKT-0011 (encrypt at rest) would force the user to set `WATIFY_SESSION_KEY` mid-pair and break their flow, (c) TKT-0019 is small enough to ship verified in one iteration.

## Plan
1. Mark TKT-0019 `inprogress`.
2. `WaSingleton` adds:
   - `_last_qr_at: datetime | None` -- set ONLY in `_on_qr` callback (distinct from the general `last_event_at` so the watchdog can't confuse a state-change with a QR rotation).
   - `_cycling: bool` -- set true during a worker-initiated cycle so `_on_disconnect` doesn't flip state to "disconnected" mid-cycle (avoids UI flicker).
   - `_auto_cycle_count: int` -- counter for diagnostics.
   - `_watchdog_thread` started alongside `_worker_thread` on first `_ensure_worker()`. Loop polls every 5s; if `state == "pairing"` and `now - _last_qr_at > 45s`, queues a `cycle` command and bumps the counter.
3. Worker `cycle` handler: sets `_cycling=True`, calls `wa.disconnect()` then `wa.connect()`, clears `_cycling` in `finally`.
4. `_on_qr` callback updates `_last_qr_at` first thing.
5. `_on_disconnect` early-returns when `_cycling` is true.
6. `py_compile` the changes. **Do NOT restart the backend** (user is actively pairing).
7. Mark TKT-0019 `resolved`; PIPELINE -> verification.

## Actions
