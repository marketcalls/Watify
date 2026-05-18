---
id: TKT-0019
title: Auto-cycle wars connect when on_qr stops firing (5-min pairing timeout)
status: open
priority: P2
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-05, F-03
filed_via: verification_finding_iter31
---

## Summary
wars `pair()` documents a 5-minute timeout in wars.md. After that, the wars background thread stops issuing fresh QRs even though our state machine stays in `pairing`. Observed during iter31 verification: `last_event_at` was 297 s old. The UI countdown from TKT-0010 correctly shows the rose "expired" state, but the operator is then stuck unless they manually click Disconnect + Start pairing (or restart the backend).

## Reproduction
1. Visit `/connect`, see QR.
2. Walk away for ~6 minutes.
3. Return. UI shows rose "QR expired. Waiting for a fresh one to load..." indefinitely. Backend `last_event_at` no longer ticks.

## Expected
Backend self-heals:
- A watchdog thread (or APScheduler interval job) sees `state == "pairing"` AND `now - last_event_at > 45 s`.
- It calls `WaSingleton.disconnect()` then `WaSingleton.connect()` to start a fresh wars worker.
- A new QR fires within ~1 second; user's existing /connect tab sees it on the next 1s SWR poll.

## Fix sketch
- `app/whatsapp.py` adds a `_watchdog_loop()` daemon thread started alongside the wars worker on first connect.
- Loop polls `cls.snapshot()` every 5 s; if pairing and `last_event_at` age > 45 s, queue a `cycle` command to the worker.
- Worker handles `cycle` by calling `wa.disconnect()` then `wa.connect()`.
- Counter / metric for "auto-cycles fired today" surfaces in `/api/wa/state` for visibility.

## Risks
- Race against an actual user clicking Disconnect concurrently. Use `_lock` + check state hasn't changed since the snapshot before issuing the cycle.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32, sourced from iter31 verification log).
