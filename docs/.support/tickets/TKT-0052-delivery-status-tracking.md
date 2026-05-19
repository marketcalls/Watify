---
id: TKT-0052
title: Track WhatsApp delivery / read receipt and surface in /connect + /history
status: closed-deferred
priority: P3
area: backend+frontend
related_tickets: TKT-0038, TKT-0051, TKT-0058
created: 2026-05-19T03:10:00Z
updated: 2026-05-19T03:40:00Z
created_by: resolving_agent
filed_via: user_request
deferred_to: TKT-0058
---

## Summary
Operator: "cant i get the delivery status and say message delivered?" Currently `wa.send` returns when WhatsApp accepts the message, not when the recipient device shows the single check / double check / read receipt. Surface those states in the UI.

## Approach
1. Backend: hook `@wa.on_message_status` (wars 0.1.3 may expose this -- verify in `docs/wars.md`). Each callback carries the message id + status (`sent | delivered | read | failed`).
2. Persist statuses on `SendAttempt` with a new `delivery_status` column + `delivered_at` / `read_at` timestamps.
3. Frontend `/history` JobRow detail expands the per-attempt cells with the new status.
4. `/connect` Test connection: poll `/api/wa/test/self/{message_id}` for status updates, or pipe through the existing wa state poll.

## Out of scope
- Group chat delivery receipts (Watify is 1:1 only).
- Notifying the operator when a contact reads vs receives (would need push or persistent SSE per TKT-0018, which is closed designed-not-implemented).

## Resolution history
- 2026-05-19T03:10:00Z -- filed per operator request.
- 2026-05-19T03:40:00Z -- closed-deferred by ticketing_agent (iter106). Reason: shipping this in v1.1 requires a schema migration (`SendAttempt` needs `delivery_status` + `delivered_at` + `read_at` columns) but the project does not run Alembic; `init_db` calls `SQLModel.metadata.create_all` which adds tables, not columns. The only v1.1-compatible path is to drop `send_attempt` / `send_job` and rebuild, which would lose send history -- not acceptable absent an explicit operator directive. Re-filed as TKT-0058 (v1.2) which packages the migration-tool decision with the wars `on_message_status` wiring.
