# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: scaffold           # planning | scaffold | backend | frontend | ticketing | resolving | verification | done
agent: frontend_agent     # which AGENTS.md role runs next
iteration: 13
last_updated: 2026-05-18T16:00:23Z
last_conversation: docs/.support/conversations/2026-05-18T160023Z-frontend_agent-iter13.md
servers:
  backend_running: true
  backend_pid: 6160
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
Run the **Frontend Agent** on PLAN item **F-06** — `/history` page (and Dashboard wiring):
- `src/app/history/page.tsx`: table of jobs from `useJobs()` with columns: id, group, message preview, status badge, scheduled/started/finished, progress `sent/total` + `failed`, cancel button (visible when status is `scheduled | pending | running`).
- Per-job drawer or expand row that calls `useJobDetail(id)` and lists attempts with redacted phones + per-attempt status + error.
- Dashboard tiles: replace static `0` values with live counts derived from `useJobs()` and `useGroups()` (total groups, total contacts across groups, jobs today, last 24h sent count).
- Acceptance: visiting `/history` after iter12's smoke shows 2 jobs (1 failed, 1 cancelled); a fresh send from `/send` appears in the list within 3s.
- Mark F-06 `[x]`. Set `agent: backend_agent` next (B-08 — hardening + structured logging).
- Commit: `feat(F-06): history table with per-job drawer and live dashboard counts`.

## History
- 2026-05-18T00:00:00Z iter0 bootstrap -> planning | initial scaffold created by user | log: (none)
- 2026-05-18T14:58:56Z iter1 planning_agent -> scaffold | PLAN.md populated with 8 backend + 7 frontend + 4 infra items | log: docs/.support/conversations/2026-05-18T145856Z-planning_agent-iter1.md
- 2026-05-18T15:03:57Z iter2 backend_agent -> scaffold | B-01 done: backend/ scaffolded with uv, FastAPI 0.136.1, /api/health live on :8000 | log: docs/.support/conversations/2026-05-18T150357Z-backend_agent-iter2.md
- 2026-05-18T15:08:22Z iter3 frontend_agent -> scaffold | F-01 done: Next.js 16.2.6 + Tailwind 4 scaffold, top nav + 5 placeholder routes, dev server on :3000 | log: docs/.support/conversations/2026-05-18T150822Z-frontend_agent-iter3.md
- 2026-05-18T15:13:09Z iter4 backend_agent -> scaffold | B-02 done: SQLModel data layer + init_db lifespan + smoke_db.py green; AGENTS.md commit policy loosened; security audit added | log: docs/.support/conversations/2026-05-18T151309Z-backend_agent-iter4.md
- 2026-05-18T15:18:13Z iter5 frontend_agent -> scaffold | F-02 done: api.ts typed fetch + useHealth SWR + BackendStatus pill on Dashboard; useGroups deferred to F-04 | log: docs/.support/conversations/2026-05-18T151813Z-frontend_agent-iter5.md
- 2026-05-18T15:22:56Z iter6 backend_agent -> scaffold | B-03 done: friend groups CRUD + 20-cap enforced (HTTP 409 group_full), phone normalizer, schemas; backend pid 11132 | log: docs/.support/conversations/2026-05-18T152256Z-backend_agent-iter6.md
- 2026-05-18T15:29:16Z iter7 backend_agent -> scaffold | B-04 done: bulk-add contacts endpoint with all-or-nothing validation, dedupe, overflow guard; 5 curl cases verified; backend pid 39988 | log: docs/.support/conversations/2026-05-18T152916Z-backend_agent-iter7.md
- 2026-05-18T15:35:47Z iter8 backend_agent -> scaffold | B-05 done: wars singleton on dedicated worker thread (PyO3 !Send), /api/wa/state|connect|disconnect, QR data-url surfaced within ~4s; backend pid 48980 | log: docs/.support/conversations/2026-05-18T153547Z-backend_agent-iter8.md
- 2026-05-18T15:41:22Z iter9 frontend_agent -> scaffold | F-03 done: useWaState SWR hook, Connect page with auto-pair on mount, QR display, Disconnect button, error/retry path; Dashboard WhatsApp tile uses live state | log: docs/.support/conversations/2026-05-18T154122Z-frontend_agent-iter9.md
- 2026-05-18T15:46:09Z iter10 backend_agent -> scaffold | B-06 done: /api/wa/test/self|to endpoints; 409 not_ready when state!=ready; phone redaction in response; backend pid 43712 | log: docs/.support/conversations/2026-05-18T154609Z-backend_agent-iter10.md
- 2026-05-18T15:51:01Z iter11 frontend_agent -> scaffold | F-04 done: Groups page with two-column layout, create/select/rename/delete, contact CRUD with 20-cap disabled UI, BulkAddModal with paste-and-preview + per-row error surfacing | log: docs/.support/conversations/2026-05-18T155101Z-frontend_agent-iter11.md
- 2026-05-18T15:56:09Z iter12 backend_agent -> scaffold | B-07 done: scheduler.py (APScheduler 3.11 + SQLAlchemyJobStore), sender.run_send_job (sequential per-recipient with random delay), /api/send POST + /api/jobs[/{id}] + DELETE; 2-contact job ran end-to-end (failed with wa_not_ready as expected, phones redacted); scheduled-future job cancelled cleanly; backend pid 6160 | log: docs/.support/conversations/2026-05-18T155609Z-backend_agent-iter12.md
- 2026-05-18T16:00:23Z iter13 frontend_agent -> scaffold | F-05 done: useJobs SWR + useJobDetail, Send page with group dropdown, message textarea, Send Now/Schedule toggle with datetime-local, min/max delay number inputs (1..300 with clamps), inline 409/422 surfacing, created-job confirmation linking to /history | log: docs/.support/conversations/2026-05-18T160023Z-frontend_agent-iter13.md
