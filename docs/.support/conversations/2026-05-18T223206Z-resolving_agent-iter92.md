# Iteration 92 -- Resolving Agent (TKT-0006)

- **Started**: 2026-05-18T22:32:06Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0006 (P3 backend) -- move test phone constant out of smoke_db.py

## Plan
1. Create `backend/scripts/_fixtures.py` with a single canonical constant `TEST_PHONE_E164 = "+911234567890"` and a module docstring explaining its allowlist purpose. (The existing inline used the bare-digits form `"911234567890"`; the column is `phone_e164` which expects normalized E.164. The inline was pre-normalize-helper code; keep the bare-digits exported value AND a normalized form so the audit-allowlist regex catches both.)
2. Edit `backend/scripts/smoke_db.py:30` to import and use the constant.
3. `uv run python -m py_compile` clean on both files.
4. Optional: `uv run python -m scripts.smoke_db` exit 0 if the smoke is still meant to be runnable (it is -- it's the dev-time DB seeder).

## Actions

1. Started TKT-0006 (test phone constant). Marked inprogress, drafted the `_fixtures.py` plan, located the inline `911234567890` at `scripts/smoke_db.py:30`.
2. User reported a console error from the running dev server: `The result of getServerSnapshot should be cached to avoid an infinite loop` at Toaster mount in RootLayout. This is a P0 user-impact regression from TKT-0008 (iter80) -- my `getServerSnapshot` returns a fresh `[]` literal each call. Pre-empts TKT-0006 because the operator's UI is throwing on every page mount.
3. Out-of-band side track from the same user message: they asked whether I created the admin account for testing. Answered honestly -- yes, iter55 Verification Agent registered admin/twelve-chars-minimum-here during the TKT-0024 smoke. The account persisted, which is why their earlier login attempts with `Rajandran1028@` failed. Earlier same session I already reset the admin password hash to `Rajandran1028@` and renamed the username to `rajandran` at their request; those changes are in app.db, no code change.
4. Reverted TKT-0006 status `inprogress -> open` so it stays on the queue.
5. Filed TKT-0036 (P0 frontend, regression from TKT-0008) and immediately marked `inprogress`.
6. Edited `frontend/src/components/Toaster.tsx`:
   - Hoisted `const EMPTY: Toast[] = Object.freeze([]) as unknown as Toast[]`.
   - Made the module-level `toasts` start as `EMPTY` instead of a freshly-allocated `[]` (so the initial-render snapshot identity matches `getServerSnapshot`'s return).
   - `getServerSnapshot` now returns `EMPTY` instead of `[]`.
7. `npx --no-install tsc --noEmit` -> exit 0.
8. `curl /dashboard` -> 200. The Next.js dev server's HMR has picked up the change; user can refresh their browser tab.
9. Marked TKT-0036 `resolved`. Awaits Verification Agent.

## Outcome
TKT-0036 resolved (P0 hotfix). TKT-0006 returned to the queue, still open. Out-of-iteration: the admin user is now `rajandran / Rajandran1028@` (app.db update, not committed code). Next iteration: Verification Agent confirms TKT-0036, then Ticketing re-triages with TKT-0006 still as the smallest-scope next pick.
