# Iteration 12 — Backend Agent (B-07)

- **Started**: 2026-05-18T15:56:09Z
- **Finished**: 2026-05-18T16:02:00Z
- **Phase**: scaffold (B-07)
- **Active agent**: backend_agent
- **PLAN item**: B-07 — send-to-group orchestrator + APScheduler

## Files created
- `backend/app/scheduler.py` — singleton `BackgroundScheduler` with `SQLAlchemyJobStore(url=app.db, tablename="apscheduler_jobs")` + `start()`/`shutdown()`/`aps_job_id()` helpers.
- `backend/app/sender.py` — `run_send_job(job_id: int)`: walks contacts sequentially, picks `random.uniform(min, max)` delay per recipient, persists `SendAttempt` rows, checks `WaSingleton.snapshot().state == "ready"` before each queue, honors cancellation between attempts. Path-stable so APScheduler can rehydrate the callable across restarts (`"app.sender:run_send_job"`).
- `backend/app/routers/jobs.py` — endpoints:
  - `POST /api/send` (schedule="now" or ISO 8601, validates ranges 1..300, max>=min, group exists with >=1 contact).
  - `GET /api/jobs` (joined with group name, includes per-status counts).
  - `GET /api/jobs/{id}` (full message + attempts list with redacted phones).
  - `DELETE /api/jobs/{id}` (sets status=cancelled, removes APScheduler job; 409 if already terminal).

## Files modified
- `backend/app/main.py` — lifespan now starts the scheduler on startup and shuts it down on exit.
- `backend/pyproject.toml` / `uv.lock` — apscheduler 3.11.2, tzlocal 5.3.1, tzdata 2026.2.

## Smoke results
```
POST /api/groups            -> id=1
POST /api/groups/1/contacts (x2) -> 201 x2
POST /api/send schedule=now min=1 max=2
  job 1 status=pending
  +1s -> status=running counts=sent0/failed0/pending2
  +2s -> status=running counts=sent0/failed1/pending1
  +3s -> status=failed   counts=sent0/failed2/pending0
GET  /api/jobs/1 -> attempts: A -> failed wa_not_ready:disconnected, B -> failed wa_not_ready:disconnected (phones redacted "14XXXXX0001" / "14XXXXX0002")
POST /api/send schedule=2030-01-01... -> id=2 status=scheduled
DELETE /api/jobs/2 -> 204; subsequent GET shows status=cancelled
```

All four behaviors verified end-to-end:
1. APScheduler fires "now" jobs immediately and walks contacts sequentially.
2. Random delay 1-2s honored (3-attempt window for 2 contacts is consistent).
3. wa_not_ready failure path records per-attempt error and sets job status=failed.
4. Scheduled-future jobs go `scheduled`; DELETE flips them to `cancelled` and removes the APScheduler entry.

## Backend
Killed iter11 PID 43712. New PID 6160.

## Security audit notes (preview for Ticketing Agent)
- `SendAttemptRead.contact_phone_redacted` uses `redact_phone()`; the raw phone is never returned in jobs responses. PASS.
- `SendJobDetail.message` IS returned (intentional — user wants to see what was sent). Could be revisited if Ticketing thinks this is sensitive.
- APScheduler's `SQLAlchemyJobStore` stores the job callable as a string reference (`app.sender:run_send_job`) plus pickled args. No secrets in args (only the int `job_id`). PASS.
- Validation: schedule_in_past rejected; range 1..300 on delays; max>=min enforced via `field_validator`. PASS.

## Decisions
- Optimistic success: when wa is `ready` and `WaSingleton.send_to()` is called, the attempt is marked `sent` right after queueing into the wars worker. wars 0.1.3 doesn't expose a delivery-receipt callback the binding surfaces yet, so we record "queued = sent". Real delivery confirmation would need `wa.on_message` for echoes — out of scope for v1. Documented as a future ticket.
- Cancellation is between-attempt only. A long in-flight `wars.send()` will complete before the cancel takes effect on the next attempt. Acceptable for v1; can revisit if Ticketing surfaces it.
- The job's `created_at` (NOT `scheduled_at`) drives list ordering — most-recently-created at top.

## Commit
About to commit `feat(B-07): send-to-group orchestrator + APScheduler`.

## Next iteration
**Frontend Agent** runs F-05 (compose + schedule UI).
