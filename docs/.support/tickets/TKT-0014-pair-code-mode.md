---
id: TKT-0014
title: Pair-code mode alongside QR (operator types a code on the phone)
status: open
priority: P2
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-05, F-03
filed_via: gap_analysis
---

## Summary
Watify is QR-only. wars supports an alternative pair-code flow (WhatsApp -> Linked devices -> Link with phone number) where wars asks Meta for an 8-character code and the operator types it on the phone. Useful when the operator can't easily scan a screen (remote desktop, narrow phone-to-screen geometry).

## Reference
- `docs/wars.md` lines ~50-60 and ~278: `wa.connect(phone)` -> pair-code; `@wa.on_pair_code(fn)` fires with the code.
- `docs/.support/openalgo/services/whatsapp_bot_service.py` `start_pair(phone=...)` accepts an E.164 phone and routes to wars' pair-code path; the code arrives on the `@on_pair_code` callback.

## Expected
- `POST /api/wa/connect` body extended to `{"phone": "+91 98765 43210"}` (optional). When set, wars uses pair-code mode.
- `WaSingleton` adds `pair_code: str | None` to ClientState; `@wa.on_pair_code` sets it.
- `WaState` API response gains `pair_code`.
- /connect page adds a "Use pair code instead" toggle. When toggled, a phone input replaces the QR card; on submit, a "Type this code on your phone" panel shows the 8-character code.

## Fix sketch
- `app/whatsapp.py` `connect(phone=None)` passes through to `wa.connect(phone)`; wires `@wa.on_pair_code` to update state.
- `app/routers/whatsapp.py` extends request body model.
- `frontend/src/app/connect/page.tsx` adds a small mode-switch and a `PairCodePanel`.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
