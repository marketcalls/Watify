---
id: TKT-0017
title: Add explicit phone_to_jid / jid_to_phone helpers
status: open
priority: P3
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-03, B-05
filed_via: gap_analysis
---

## Summary
wars accepts both bare-digit phone strings and full JIDs (`<digits>@s.whatsapp.net`). Watify uses bare digits everywhere; if we ever need group JIDs (`@g.us`) or want to log the routing target unambiguously, we'd be re-deriving JIDs in two or three places.

openalgo centralizes this in `phone_to_jid()` and `jid_to_phone()`.

## Expected
- `app/jid.py` gains:
  - `phone_to_jid(digits: str) -> str` -> `f"{digits}@s.whatsapp.net"`.
  - `jid_to_phone(jid: str) -> str` -> digits if 1:1, else "" for group JIDs.
- Callers in `sender.run_send_job` and `app/whatsapp.py` use the helpers explicitly.

## Fix sketch
- ~10 lines in `app/jid.py`.
- One-line refactor in `sender.run_send_job` for clarity (`wa.send(phone_to_jid(contact.phone_e164), message)` -- though wars handles both forms, the helper documents intent).

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
