---
id: TKT-0007
title: /connect re-triggers POST /api/wa/connect on every hot-reload
status: verified
priority: P2
area: frontend
created: 2026-05-18T16:14:48Z
updated: 2026-05-18T16:43:40Z
created_by: ticketing_agent
related_plan_item: F-03
---

## Summary
During dev, every Next.js hot-reload remounts `/connect`. The `useEffect([waState?.state])` fires and POSTs to `/api/wa/connect`, even if the wars singleton is already pairing. Backend ends up cycling pairing -> disconnected as the worker thread accepts new connect commands.

Observed across iter9, iter11, iter13, iter14 conversation logs — each one had to manually disconnect at the end to leave a clean state.

## Expected
The Connect page should only auto-pair when `state == "disconnected"` AND the user has not already initiated a connection in the same session. A `sessionStorage` flag or a single `useRef` guard suffices.

## Fix sketch
```tsx
const autoStarted = useRef(false);
useEffect(() => {
  if (autoStarted.current) return;
  if (waState?.state === "disconnected") {
    autoStarted.current = true;
    connect().catch(() => {});
  }
}, [waState?.state]);
```

## Resolution history
- 2026-05-18T16:14:48Z — filed by Ticketing Agent (iter16).
- 2026-05-18T16:39:01Z — Resolving Agent (iter21) set status to inprogress.
- 2026-05-18T16:40:30Z — Resolving Agent (iter21) shipped the three-layer guard in `frontend/src/app/connect/page.tsx`:
  1. `useRef(false)` (`autoStarted`) — survives re-renders in one mount.
  2. `sessionStorage` flag `watify.autopair.started` — survives Fast Refresh remounts within the same browser session.
  3. State check: if `waState.state !== "disconnected"`, the auto-pair is treated as already-fired (the wars worker is mid-flight; do not stampede).
  Manual `Disconnect` clears both guards so an explicit `Start pairing` click resumes the flow. `Retry` from the Error panel also re-sets the guards. Page compiled cleanly (Turbopack `Compiled in 22ms`); GET `/connect` -> 200; backend wa state remained `disconnected` after curl loads (no client JS executes through curl). Browser-driven confirmation deferred to Verification Agent.
  Status set to `resolved`.
- 2026-05-18T16:43:40Z — Verification Agent (iter22) PASSED:
  - Code review of `connect/page.tsx`: three guard layers (`autoStarted` ref, `sessionStorage`, state precheck) all wired; manual `Disconnect` clears both flags, `Start pairing` and `Retry` set both flags before calling `connect()`.
  - Compile clean (Turbopack `Compiled in 18ms`).
  - 5x rapid curl-storm against `/connect` all returned HTTP 200; backend wa state stayed `disconnected` (confirms no SSR side-effects).
  - Browser-driven test still blocked by TKT-0009 issue B (Strike Analytics service worker on localhost:3000). Same accepted-constraint as TKT-0002.
  - Status set to `verified`. Committed `fix(TKT-0007): guard /connect auto-pair against hot-reload stampede` and pushed.
