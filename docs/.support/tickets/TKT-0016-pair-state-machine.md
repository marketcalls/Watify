---
id: TKT-0016
title: Distinguish `paired` from `ready` in the wa state machine
status: open
priority: P3
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-05
filed_via: gap_analysis
---

## Summary
Today's states: `disconnected | pairing | ready | error`. After a successful pair, `ready` is set; on backend restart with a persisted session, the worker re-`connect()`s and eventually reaches `ready` again. The intermediate state ("we have a session blob; we're attempting to reconnect; we have not yet received `on_connected`") is currently indistinguishable from a fresh pair.

openalgo's machine is `idle | starting | awaiting_scan | paired | failed`, where `paired` means "blob saved on disk" and `connected` ("running" in their terminology) means "wars background loop says we're online".

## Expected
- New state set: `disconnected | pairing | paired | ready | error`.
- `paired` set on `on_connected` (one-shot) plus session-export commit; persists across restarts on its own.
- `ready` set on every backend boot once the wars worker is `is_connected() == True`.
- UI Ready panel says "Connected" only for `ready`; if state is `paired` but not `ready`, show "Reconnecting..." instead of dropping to disconnected.

## Fix sketch
- `app/whatsapp.py` `State` literal extends with `paired`.
- Worker tracks "session blob present" -> set `paired` on startup before the first `on_connected`.
- Frontend `useWaState` and `WhatsAppTile` add the new label.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
