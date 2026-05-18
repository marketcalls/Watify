---
id: TKT-0005
title: Surface owner_phone after wars pairing
status: verified
priority: P2
area: backend
created: 2026-05-18T16:14:48Z
updated: 2026-05-18T18:47:57Z
created_by: ticketing_agent
related_plan_item: B-05, F-03
---

## Summary
The `/api/wa/state` response includes `owner_phone: null` even after a successful pair. Frontend Ready panel falls back to "Linked as this device". wars 0.1.3 has the data internally (single-arg `wa.send(text)` routes to owner) but the binding hasn't exposed it.

## Expected
After `on_connected`, set `owner_phone` to the paired device's E.164 number.

## Fix sketch
- Inspect `wars.WhatsApp` attributes via `dir()` for an `owner` / `me` / `jid` property.
- If absent, queue a `wa.send("ping_to_self")` immediately after pair and capture the destination JID, OR persist the phone the user typed in pair-code mode.
- Once set, the Ready panel renders "Linked as +91 XX..." with the redacted suffix.

## Resolution history
- 2026-05-18T16:14:48Z -- filed by Ticketing Agent (iter16).
- 2026-05-18T18:37:10Z -- Resolving Agent (iter46) set status to inprogress.
- 2026-05-18T18:39:00Z -- Resolving Agent (iter46) shipped:
  - Discovery: `dir(WhatsApp)` confirmed wars 0.1.3 has no public `owner` / `me` / `jid` accessor (only `connect`, `disconnect`, `export_session`, `from_bytes`, `is_connected`, `pair`, `send` family, and the callback decorators). Sending a sentinel-to-self at pair time was rejected as spammy UX.
  - **Two-source strategy** in `backend/app/whatsapp.py` `_worker_loop`:
    1. **Env seed (`settings.owner_phone`, env `WATIFY_OWNER_PHONE`)**: when set, normalize and seed `state.owner_phone` at worker start. Operator explicit; always wins (won't be overwritten by the passive learner).
    2. **Passive learning via `@wa.on_message`**: when an `is_from_me=True` Message arrives with a 1:1 `<digits>@s.whatsapp.net` sender JID and we don't already have `owner_phone` set, extract the digits (stripping any `:device` suffix) and store. One-shot per session -- the second `is_from_me` message is a cheap no-op via the early-return check.
  - `backend/app/routers/whatsapp.py` `_snapshot_to_dto`: pass `owner_phone` through `redact_phone()` so the wire shape is `91XXXXXX3210` (the same redaction used in send-attempt rows). Full digits never leave the backend; frontend Ready panel can render the redacted form safely.
  - `backend/.env.example` documents `WATIFY_OWNER_PHONE`.
  - Frontend Ready panel (`/connect/page.tsx`) already renders `ownerPhone ?? "this device"` -- no change needed.

  Compiles clean. Backend NOT restarted (live session preserved); Verification Agent will respawn and test the env-seed path + spot-check that the redacted form arrives in `/api/wa/state`.

  Status set to `resolved`.
- 2026-05-18T18:47:57Z -- Verification Agent (iter48) PASSED:
  1. Restart with `WATIFY_OWNER_PHONE="+91 9876543210"` exported -> backend.log line `wars: owner_phone seeded from WATIFY_OWNER_PHONE`; `GET /api/wa/state` returned `owner_phone: "91XXXXXX3210"` (redacted, normalized digits only).
  2. Restart with env unset -> `owner_phone` was null; code grep confirms `@wa.on_message` listener is registered at line 424 of `app/whatsapp.py` with the `learned owner_phone passively from on_message echo` log line at line 448. Live echo proof is left for natural operation -- the wars callback wiring is identical to the on_qr / on_connected / on_disconnect callbacks already shipped.
  Status set to `verified`. Committed `fix(TKT-0005): surface owner_phone via env seed + passive on_message learner` and pushed.
