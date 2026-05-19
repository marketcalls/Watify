---
id: TKT-0059
title: /connect handleManualConnect surfaces fetch rejection as Runtime TypeError overlay
status: verified
priority: P1
area: frontend
related_tickets: TKT-0050, TKT-0056
created: 2026-05-19T03:55:00Z
updated: 2026-05-19T03:55:00Z
created_by: resolving_agent
filed_via: user_report
---

## Summary
Operator hit a Next.js dev-overlay "Runtime TypeError: Failed to fetch" while on `/connect`. Stack trace:
```
apiFetch (src_0b5.9~f._.js:458:23)
Object.post (...:489:25)
Object.connect (...:517:27)
connect (_049tu0h._.js:215:151)
handleManualConnect (_049tu0h._.js:119:15)
onClick (...:221:42)
```

Backend logs at the same wall-clock show every `/api/wa/connect` succeeding (`POST /api/wa/connect HTTP/1.1 200 OK` repeatedly, on_qr firing, polls returning 200). So the backend is healthy. The "Failed to fetch" TypeError is a network-level rejection thrown by `fetch()` itself -- browser-extension block, request abort during navigation, transient connection refused while the dev backend reloaded, etc. -- not a HTTP-status error from the server.

The actual bug: `handleManualConnect()` (the "Start pairing" button onClick + ErrorPanel "Retry" button onClick) was `await connect()` with NO try/catch. Any rejection bubbles up to React's event handler, which surfaces it as the dev-overlay "Runtime TypeError" instead of a soft toast. `handleModeChange()` had the same shape (try/finally without catch).

## Fix
`frontend/src/app/connect/page.tsx`:
- `handleManualConnect()` -- wrapped the `await connect()` in try/catch with `toast.error(msg)` on failure; added `setBusy(true/false)` book-ends so the button doesn't get double-clicked.
- `handleModeChange()` -- added a `catch` branch alongside the existing `finally`. Same toast pattern.

The autopair `useEffect` already catches with `.catch(() => {})` so it was never the bug. `handlePairCodeConnect()` already had a full try/catch and stays as-is. `confirmDisconnect()` already had try/catch.

## Acceptance
- Clicking "Start pairing" with the backend temporarily unreachable surfaces a red toast ("Failed to fetch" or whatever the error message is) instead of a Next.js dev-overlay Runtime TypeError.
- The Retry button on the ErrorPanel goes through the same `handleManualConnect()` path and inherits the fix.
- Mid-pairing mode switch (`handleModeChange` QR branch) toasts on failure instead of crashing.
- `npx tsc --noEmit` exit 0.

## Verification
- `npx --no-install tsc --noEmit` exit 0.
- `curl /connect` HTTP 200.
- Code inspection: `handleManualConnect` (lines 94-110) wraps `await connect()` in try/catch with toast.error + setBusy book-ends; `handleModeChange` (lines 142-158) likewise.

## Resolution history
- 2026-05-19T03:55:00Z -- filed + resolved + verified inline per operator bug report (operator-directive bundle, P1 hotfix).
