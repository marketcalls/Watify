---
id: TKT-0015
title: Real rate-limit middleware on send endpoints
status: open
priority: P2
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-06, B-07, S4
filed_via: gap_analysis
---

## Summary
Watify has the dashboard soft-cap reminder (TKT-0002 SoftCapBanner) but no real rate-limit gate on the backend. A buggy script or fat-finger could fire `POST /api/wa/test/to` in a tight loop and Meta would ban the device before the operator notices.

## Reference
- openalgo uses `flask-limiter` with `WHATSAPP_MESSAGE_RATE_LIMIT` from env (default `10 per minute`).
- wars.md "WhatsApp Terms of Service - practical risk note": send volume is the dominant ban trigger.

## Expected
- Add `slowapi` (FastAPI's idiomatic Flask-Limiter equivalent) and register limits:
  - `/api/wa/test/self` -> `15/minute`.
  - `/api/wa/test/to` -> `10/minute`.
  - `/api/send` -> `5/minute` (it's already throttled inside the job by the 3-30s per-recipient delay, but rate-limit at the entrypoint stops repeated job creation).
- Limits are env-overridable via `WATIFY_RATE_LIMIT_TEST_SELF`, `WATIFY_RATE_LIMIT_TEST_TO`, `WATIFY_RATE_LIMIT_SEND`.
- 429 response uses the flat envelope from TKT-0001: `{"error":"rate_limited","retry_after":...}`.
- Dashboard SoftCapBanner remains as the soft UI signal; this is the hard backend cap.

## Fix sketch
- `uv add slowapi`.
- `app/main.py` register limiter.
- Decorate handlers in `app/routers/whatsapp.py` and `app/routers/jobs.py`.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
