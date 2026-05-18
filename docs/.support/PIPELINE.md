# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: scaffold           # planning | scaffold | backend | frontend | ticketing | resolving | verification | done
agent: backend_agent      # which AGENTS.md role runs next
iteration: 5
last_updated: 2026-05-18T15:18:13Z
last_conversation: docs/.support/conversations/2026-05-18T151813Z-frontend_agent-iter5.md
servers:
  backend_running: true
  backend_pid: 50004
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 0
  inprogress: 0
  resolved: 0
  verified: 0
```

## Next Action
Run the **Backend Agent** on PLAN item **B-03** — Friend Groups CRUD endpoints:
- Create `app/routers/groups.py` with router under `/api/groups`:
  - `POST /api/groups` body `{name: str}` → 201 `{id, name, created_at}`. 409 on duplicate name.
  - `GET /api/groups` → list of groups with `contact_count`.
  - `GET /api/groups/{id}` → group + contacts list.
  - `PATCH /api/groups/{id}` body `{name: str}` → 200.
  - `DELETE /api/groups/{id}` → 204 (cascades contacts).
  - `POST /api/groups/{id}/contacts` body `{name, phone}` → 201. **HTTP 409 with `{"error":"group_full","max":20}` when the group already has 20.**
  - `DELETE /api/groups/{id}/contacts/{cid}` → 204.
- Add `app/jid.py` — phone normalization (digits only; strip `+`, spaces, hyphens; validate length 6-15).
- All request/response bodies are Pydantic models (SQLModel `schemas` or separate `app/schemas.py`).
- Register router in `app/main.py`.
- Restart backend; verify CRUD round-trip with `curl` and confirm 21st contact rejected.
- Mark B-03 `[x]`. Set `agent: frontend_agent` next (F-03 — Connect / pairing UI; F-04 needs B-04 bulk endpoint).
- Commit per new policy: `feat(B-03): friend groups CRUD with 20-contact cap`.

## History
- 2026-05-18T00:00:00Z iter0 bootstrap -> planning | initial scaffold created by user | log: (none)
- 2026-05-18T14:58:56Z iter1 planning_agent -> scaffold | PLAN.md populated with 8 backend + 7 frontend + 4 infra items | log: docs/.support/conversations/2026-05-18T145856Z-planning_agent-iter1.md
- 2026-05-18T15:03:57Z iter2 backend_agent -> scaffold | B-01 done: backend/ scaffolded with uv, FastAPI 0.136.1, /api/health live on :8000 | log: docs/.support/conversations/2026-05-18T150357Z-backend_agent-iter2.md
- 2026-05-18T15:08:22Z iter3 frontend_agent -> scaffold | F-01 done: Next.js 16.2.6 + Tailwind 4 scaffold, top nav + 5 placeholder routes, dev server on :3000 | log: docs/.support/conversations/2026-05-18T150822Z-frontend_agent-iter3.md
- 2026-05-18T15:13:09Z iter4 backend_agent -> scaffold | B-02 done: SQLModel data layer + init_db lifespan + smoke_db.py green; AGENTS.md commit policy loosened; security audit added | log: docs/.support/conversations/2026-05-18T151309Z-backend_agent-iter4.md
- 2026-05-18T15:18:13Z iter5 frontend_agent -> scaffold | F-02 done: api.ts typed fetch + useHealth SWR + BackendStatus pill on Dashboard; useGroups deferred to F-04 | log: docs/.support/conversations/2026-05-18T151813Z-frontend_agent-iter5.md
