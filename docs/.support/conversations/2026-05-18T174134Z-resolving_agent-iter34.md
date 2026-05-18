# Iteration 34 — Resolving Agent (TKT-0020)

- **Started**: 2026-05-18T17:41:34Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0020 (P1 backend) — wars on_connected never fires; state stuck at "pairing"

## Why this ticket now (priority gymnastics)
PIPELINE.md on disk still shows iter32 (the iter33 PIPELINE write was interrupted when the user pivoted to live debugging). On-disk reality:
- iter33 shipped the TKT-0019 watchdog code; TKT-0019 frontmatter is `resolved`.
- iter33 also filed TKT-0020 (P1) after the live diagnosis.

The Verification Agent will need to restart the backend to smoke TKT-0019 -- but if we restart with the wars `on_connected` callback still broken (TKT-0020), the verification logs will be polluted by the same "state stuck at pairing" bug. Cleanest sequencing: resolve TKT-0020 (small, ~10 lines) in this iteration, then iter35 = single Verification pass that restarts once and confirms BOTH tickets.

## Plan
1. Mark TKT-0020 `inprogress`.
2. In `backend/app/whatsapp.py` worker loop:
   - Switch `cls._cmd_q.get()` to `cls._cmd_q.get(timeout=2.0)`.
   - On `queue.Empty`, if `snapshot().state == "pairing"` and `wa.is_connected()`, call `cls._set(state="ready", clear_qr=True, clear_error=True)`. Log a `wars: is_connected()==True, state=ready (callback fallback)` line so the bug-cause is obvious in logs.
3. Also fire the same check immediately after `wa.connect()` returns -- some pairs land before the worker idles.
4. `py_compile` the file.
5. Mark TKT-0020 `resolved`.
6. Update PIPELINE to reflect iter33 + iter34 history and queue Verification on both.

## Actions
