---
id: TKT-0014
title: Pair-code mode alongside QR (operator types a code on the phone)
status: verified
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
- 2026-05-18T21:48:00Z -- resolved by Resolving Agent (iter83), backend slice only. Three-file change set on the backend: (1) `backend/app/whatsapp.py` -- added `pair_code: Optional[str] = None` to `ClientState`; extended `_set` with `pair_code` + `clear_pair_code` kwargs; mirrored in `snapshot()`; added `@wa.on_pair_code` callback (gated on `hasattr(wa, "on_pair_code")` for forward/backward compat) that calls `cls._set(state="pairing", pair_code=code, clear_qr=True, clear_error=True)` -- runs on wars's Tokio thread but only touches our state lock, never `wa`; `on_connected` now also `clear_pair_code=True` since the code is stale once paired; worker `disconnect` + `cycle` + `stop` branches all `clear_pair_code=True`; the worker's `connect` command now accepts the arg as the phone -- when truthy it calls `wa.connect(arg)` (wars's pair-code path), else `wa.connect()` (QR path); public `WaSingleton.connect(phone: Optional[str] = None)` queues `("connect", phone)`. (2) `backend/app/routers/whatsapp.py` -- added `WaConnectRequest` Pydantic model with optional `phone: str | None` (Field min_length=1 max_length=40); extended `WaState` response with `pair_code: str | None = None`; `connect()` handler now accepts `body: WaConnectRequest | None = None`, validates `body.phone` via the existing `normalize_phone` helper (raises 422 invalid_phone on failure), and passes the normalized phone through to `WaSingleton.connect(phone)`. (3) `_snapshot_to_dto` carries pair_code through. `uv run python -m py_compile` clean. Smoke (against backend pid 16032 after restart): (A) `POST /api/wa/connect {}` -> 200 with `pair_code:null` (QR flow); (B) `GET /api/wa/state` -> response includes `pair_code` field; (C) `POST /api/wa/connect {"phone":"+919876543210"}` -> 200, state=pairing (worker switched to pair-code path; the `@on_pair_code` callback would populate `pair_code` once wars responds -- cannot be exercised end-to-end without a live phone); (D) `POST /api/wa/connect {"phone":"not-a-phone"}` -> 422 `{"error":"invalid_phone","detail":"phone must be 6-15 digits after normalization (got 0)"}`. Frontend follow-on filed as TKT-0035 (P3) -- mode-switch + PairCodePanel on /connect. Conversation: `docs/.support/conversations/2026-05-18T214324Z-resolving_agent-iter83.md`.
- 2026-05-18T21:50:00Z -- VERIFIED by Verification Agent (iter84). Eight checks: (a) `uv run python -m py_compile app/whatsapp.py app/routers/whatsapp.py` exit 0. (b) `ClientState.pair_code: Optional[str] = None` at `whatsapp.py:123`; `_set(pair_code: Optional[str])` kwarg at `:167`; `WaState.pair_code: str | None = None` at `routers/whatsapp.py:19`. (c) `@wa.on_pair_code` callback hasattr-gated at `whatsapp.py:421-423` -- defined inside `if hasattr(wa, "on_pair_code"):` so unsupported wars builds skip it gracefully. (d) `WaSingleton.connect(cls, phone: Optional[str] = None)` at `whatsapp.py:567`. (e) Worker `connect` dispatch at `whatsapp.py:526-532` -- `if isinstance(arg, str) and arg: wa.connect(arg)` else `wa.connect()`. (f) `class WaConnectRequest` at `routers/whatsapp.py:25` + `def connect(body: WaConnectRequest | None = None)` at `:73`. (g) `_snapshot_to_dto` carries `pair_code=snap.pair_code` at `routers/whatsapp.py:60`. (h) 4 smokes independently reproduced (admin login, then `wa.disconnect` to clear state, then): (A) `POST /api/wa/connect {}` -> 200 `{state:"pairing", pair_code:null, ...}`; (B) `GET /api/wa/state` returns keys `[last_error, last_event_at, owner_phone, pair_code, qr_data_url, state]` -- `pair_code` IS present; (C) `POST /api/wa/connect {"phone":"+919876543210"}` -> 200 `{state:"pairing", pair_code:null, ...}` (worker switched to pair-code path; the actual `@on_pair_code` fire requires a live phone); (D) `POST /api/wa/connect {"phone":"not-a-phone"}` -> 422 `{"error":"invalid_phone","detail":"phone must be 6-15 digits after normalization (got 0)"}`. Verified.
