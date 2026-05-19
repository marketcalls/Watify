# Iteration 107 -- Resolving Agent + Verification Agent (TKT-0059 hotfix, operator-directive bundle)

- **Started**: 2026-05-19T03:55:00Z
- **Phase**: resolving (bundled with verification, operator-directive)
- **Active agent**: resolving_agent + verification_agent

## Trigger
Operator hit a Next.js dev-overlay "Runtime TypeError: Failed to fetch" while on /connect. Phase was `done` at iter106; this hotfix reopens the loop for one iteration and returns to `done` after the fix verifies.

## Diagnosis

1. `curl http://localhost:8000/api/health` -> 200 (backend healthy).
2. `curl http://localhost:3000/connect` -> 200 (frontend serving).
3. `curl -X OPTIONS /api/wa/connect ...` -> 200 with correct CORS headers (`access-control-allow-origin: http://localhost:3000`, `access-control-allow-credentials: true`).
4. `curl -X POST /api/wa/connect ...` -> 401 (auth_required, missing cookie) -- but a 401 surfaces as `ApiError`, not a fetch TypeError.
5. `docs/.support/logs/backend.log` shows every recent `/api/wa/connect` succeeding (`200 OK`), `on_qr` firing, `/api/wa/state` polls all 200.

So the backend was up; the operator's browser threw a network-level `TypeError: Failed to fetch` (Chrome's "fetch promise rejected before a response was returned" -- request aborted, extension blocked, transient connection refused during a dev reload, etc.).

Root cause of the user-visible overlay: `handleManualConnect()` in `frontend/src/app/connect/page.tsx` called `await connect()` with NO try/catch. The rejection bubbled to React's synthetic event handler, which Next.js dev surfaces as a "Runtime TypeError" overlay. The fetch transport blip would have been better handled as a soft toast.

The autopair useEffect at line 62 already had `.catch(() => {})`, `handlePairCodeConnect` already had a full try/catch, and `confirmDisconnect` already had try/catch -- this was the last unprotected `connect()` callsite. `handleModeChange` had a try/finally without `catch` -- same shape, same risk -- caught in the same iteration.

## Fix

`frontend/src/app/connect/page.tsx`:
1. `handleManualConnect()` (Start pairing button + ErrorPanel Retry button):
   - Wrapped `await connect()` in try/catch.
   - On failure: `toast.error(e instanceof Error ? e.message : "network error")`.
   - Added `setBusy(true/false)` book-ends so the button can't be double-clicked while the request is in flight.
2. `handleModeChange()` QR-branch:
   - Added a `catch` between `try` and `finally`. Same `toast.error(msg)` pattern.

No backend changes. No other frontend files touched.

## Verification proofs
- `npx --no-install tsc --noEmit` exit 0.
- `curl /connect` -> HTTP 200.
- Code inspection: `handleManualConnect` (lines 94-110) wraps the `await connect()` in try/catch; `handleModeChange` (lines 142-158) likewise. No remaining un-caught `connect()` callsite in this file.

## Outcome
TKT-0059 verified inline. The fetch-rejection-as-overlay class of bug is closed: every callsite of `connect()` in /connect/page.tsx now soft-toasts on failure. Phase goes back to `done`; v1.1 milestone holds. TKT-0058 remains as the v1.2 entry point.
