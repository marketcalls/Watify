---
id: TKT-0058
title: v1.2 -- WhatsApp delivery/read tracking, bundled with a real schema migration tool decision
status: open
priority: P3
area: backend+frontend
related_tickets: TKT-0052, TKT-0038, TKT-0051
created: 2026-05-19T03:40:00Z
updated: 2026-05-19T03:40:00Z
created_by: ticketing_agent
filed_via: deferred_from_TKT-0052
target_milestone: v1.2
---

## Summary
Deferred follow-up to TKT-0052. Adding delivery + read receipt tracking to v1.2 requires both:
1. **wars `on_message_status` callback wiring** -- confirm wars 0.1.3 (or whichever pin v1.2 targets) actually exposes this hook in `docs/wars.md` before writing code. If absent, fall back to polling whatever status the existing `wa.send` result carries, OR upgrade wars.
2. **A schema migration tool** for the project. The current `init_db` -> `SQLModel.metadata.create_all` only creates missing tables; it cannot add columns to an existing `SendAttempt`. Adding `delivery_status` + `delivered_at` + `read_at` columns on a live `app.db` needs a real migration step.

## Decision points (must be answered before coding)
- **Migration tool**: pick one. Options:
  - **Alembic** (canonical for SQLAlchemy/SQLModel). Heavier setup, autogenerate works fine for SQLModel. Recommended.
  - **aerich** (Tortoise ORM tool). Wrong ecosystem; skip.
  - **Hand-rolled `ALTER TABLE` runner** at startup. Cheap for a single-user app, but easy to drift from the SQLModel schema. Reject unless v1.2 stays at exactly one migration.
  - **Destructive reset** (drop + create_all). Loses send history. Only acceptable if the operator agrees.
- **Status surface**: the four states (`sent`, `delivered`, `read`, `failed`) need a UI affordance on `/history` JobRow detail (per-attempt). Decide whether `/connect` Test connection also polls -- nice to have, not required.

## Scope (once decisions are made)
1. **Backend**:
   - Add migration tool to `pyproject.toml` + `uv sync`.
   - Generate initial migration capturing the current schema (so future ALTERs have a baseline).
   - Generate a second migration adding `delivery_status: str | None`, `delivered_at: datetime | None`, `read_at: datetime | None` to `SendAttempt`.
   - Wire `@wa.on_message_status` -- callback runs on wars Tokio thread; needs the same `WaSingleton._state_lock` + thread-bridge as the existing `on_qr` / `on_pair_code` callbacks. Persist the status by `(send_job_id, contact_id, message_id)` -- the wars callback gives the message id; `SendAttempt` will need an indexed `wa_message_id` column too.
2. **Frontend**:
   - Extend `SendAttemptRead` DTO with the new status fields.
   - JobRow detail renders a 4-state pill per attempt (sent | delivered | read | failed) instead of the 3-state today.
   - Optional `/connect` Test connection polls for status updates after the initial send.

## Out of scope (still)
- Group chat delivery receipts (Watify is 1:1 only).
- Realtime push of status changes to the browser (TKT-0018 closed designed-not-implemented; SWR polling is good enough).

## Resolution history
- 2026-05-19T03:40:00Z -- filed by ticketing_agent (iter106) as the v1.2 successor to the closed-deferred TKT-0052.
