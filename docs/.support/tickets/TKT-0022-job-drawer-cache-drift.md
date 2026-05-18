---
id: TKT-0022
title: Job drawer attempts list lags the progress counter while running
status: open
priority: P3
area: frontend
created: 2026-05-19T00:08:00Z
updated: 2026-05-19T00:08:00Z
created_by: ticketing_agent
related_plan_item: F-06
filed_via: human_manual_input
---

## Summary
During a long-running job (random per-recipient delay 3-30s), the History page can show inconsistent state:
- Row-level progress: `1 / 2` (from `useJobs` polling /api/jobs every 3s)
- Drawer attempts table: both rows still `pending` (from `useJobDetail` polling /api/jobs/{id} every 2s)

The counter is right but the drawer hasn't repolled yet. User reads "1/2 progress + 2 pending = stuck", but in fact contact 1 already sent and the worker is in the random delay before contact 2.

## Reproduction
1. Create a group with 2 contacts.
2. Schedule a send with `min_delay_s=20, max_delay_s=30`.
3. After ~25 seconds, expand the job row in /history.
4. Observe the `1/2` counter while both attempts read `pending`.

## Expected
The two views never diverge by more than the poll interval. One of:
- Drive the row counter from the same `useJobDetail` cache so they refresh together.
- Cross-invalidate: when `useJobs` refresh reveals `counts.sent` has bumped, manually `mutate(detailKey)` to force the drawer to refresh.
- Bump `useJobDetail` poll interval to 1s while the job is running (currently 2s) so the gap shrinks.

## Fix sketch
In `frontend/src/hooks/useJobs.ts`, when the list reports a change in `counts.sent` or `counts.failed` for any open drawer's job id, call `mutate('/api/jobs/' + id)`.

Or more simply, in `JobRow.tsx`, derive `progressText` from `detail.counts` (the drawer's own data) when the drawer is open, falling back to the row-level `job.counts` when closed.

## Resolution history
- 2026-05-19T00:08:00Z -- filed by Ticketing Agent (live diagnosis: user reported "stuck running" but job actually completed 2/2 sent; the perception bug was the counter-vs-drawer drift during a 40s job window).
