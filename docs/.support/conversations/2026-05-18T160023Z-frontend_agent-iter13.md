# Iteration 13 — Frontend Agent (F-05)

- **Started**: 2026-05-18T16:00:23Z
- **Finished**: 2026-05-18T16:04:00Z
- **Phase**: scaffold (F-05)
- **Active agent**: frontend_agent
- **PLAN item**: F-05 — compose + schedule page

## Files created
- `frontend/src/hooks/useJobs.ts` — `useJobs()` (SWR `/api/jobs` w/ 3s refresh + `createSend` + `cancelJob`) and `useJobDetail(id)` (SWR keyed on id with 2s refresh while status is pending/scheduled/running, paused on terminal).

## Files modified
- `frontend/src/lib/api.ts` — added `JobStatus`, `AttemptStatus`, `JobCounts`, `SendJobRead`, `SendAttemptRead`, `SendJobDetail`, `SendRequest` types and `jobs.*` helper. Plus `DEFAULT_MIN_DELAY_S=3`, `DEFAULT_MAX_DELAY_S=30`, `MAX_DELAY_S=300` constants.
- `frontend/src/app/send/page.tsx` — full compose form:
  - Group `<select>` driven by `useGroups()`. Disables submit when 0 contacts.
  - Message textarea, 4096-char limit + live counter.
  - Send Now / Schedule toggle (custom pill buttons). Schedule mode reveals `<input type="datetime-local">` defaulting to "next minute" in local TZ.
  - Min/Max delay number inputs (clamped 1..300 with `Math.min/max` guards on change).
  - `rangeError` if min > max.
  - On submit, converts the local datetime input to a full ISO string before POSTing.
  - Surfaces 409 ("Backend not ready or job already terminal") and 422 (echoes server `detail`) inline.
  - On success, shows the created job id + status + a link to /history.

## Verification
- `GET /send` -> 200. Turbopack compiled cleanly.
- All other routes still 200.
- Hot-reload during dev kept retriggering the Connect page's auto-pair. Called `POST /api/wa/disconnect` afterwards; state confirmed disconnected.
- Did not submit a real send through the UI in this iteration (the backend orchestrator was already exercised end-to-end in iter12). The wiring is mechanical: form -> typed body -> `jobs.create` -> POST /api/send -> rendered confirmation.

## Security audit notes (preview for Ticketing Agent)
- Form bodies are typed via `SendRequest`. No raw `any` reaching the API. PASS.
- `process.env.NEXT_PUBLIC_API_BASE` is the only env read. PASS.
- Datetime conversion goes through `new Date(...).toISOString()` — no string concat into a URL or SQL. PASS.

## Decisions
- The "Each recipient: random N-Ms between sends" helper text is a one-liner so the user understands the cap math at a glance.
- No success-then-close behavior: the user stays on the form after submit (with the confirmation panel) so they can fire off another send fast.

## Commit
About to commit `feat(F-05): compose page with Send Now / Schedule + delay controls`.

## Next iteration
**Frontend Agent** runs F-06 (history table + Dashboard live counts).
