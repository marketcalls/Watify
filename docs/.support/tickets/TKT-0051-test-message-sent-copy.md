---
id: TKT-0051
title: Test connection result reads "queued" but wars.send already dispatched
status: verified
priority: P3
area: frontend
related_tickets: TKT-0038
created: 2026-05-19T03:09:00Z
updated: 2026-05-19T03:09:00Z
created_by: resolving_agent
filed_via: user_report
---

## Summary
Operator: "it says Test message queued. Check WhatsApp on your phone within a few seconds." The copy implied an async queue but `wars.send` returns when WhatsApp accepts the message for delivery, not before. The "queued" language was misleading.

## Fix
`frontend/src/app/connect/page.tsx` ReadyPanel test-connection success copy:
- Before: "Test message queued. Check WhatsApp on your phone within a few seconds."
- After:  "Test message sent. Open WhatsApp on your phone to confirm receipt."

The toast copy was already accurate ("Test message sent to your own number").

## Out of scope
True delivery / read confirmation tracking is filed as TKT-0052.

## Resolution history
- 2026-05-19T03:09:00Z -- filed + resolved + verified inline per operator report.
