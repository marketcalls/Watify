# Iteration 21 — Resolving Agent (TKT-0007)

- **Started**: 2026-05-18T16:39:01Z
- **Finished**: 2026-05-18T16:41:00Z
- **Phase entering**: resolving
- **Phase exiting**: verification
- **Active agent**: resolving_agent
- **Ticket**: TKT-0007 (P2 frontend) — `/connect` auto-pair re-trigger on hot-reload

## Root cause
`ConnectPage` auto-pair `useEffect` is keyed on `waState?.state`. Every Fast Refresh remounts the component; SWR briefly returns the cached `disconnected` snapshot before the next poll lands; the effect sees "disconnected", fires `connect()`, the backend wars worker churns through `disconnected -> pairing` again. The component-local `busy` state does not survive remount.

## Fix (one file: `frontend/src/app/connect/page.tsx`)
Three guard layers:
1. `useRef<boolean>(false)` (`autoStarted`) — survives re-renders inside one mount.
2. `sessionStorage` flag `watify.autopair.started` — survives Fast Refresh remounts within the browser tab session.
3. State precheck — when `waState.state !== "disconnected"` (already pairing / ready / error), treat as if auto-pair has fired and set the guards, but do NOT call `connect()`.

Both guards are cleared by the explicit `Disconnect` button (new `handleDisconnect`) so the user can manually re-pair. `Start pairing` and `Retry` buttons go through `handleManualConnect` which sets the guards before calling `connect()` so a subsequent Fast Refresh does not stampede.

## Verification (pre-handoff)
- `GET /connect` -> 200.
- Turbopack `Compiled in 22ms` (and again on second save). No type errors.
- Backend wa state is `disconnected` baseline; curl loads do not trigger the client effect, so curl can't fully exercise the guard. Verification Agent will rely on code review + compile evidence (Chrome browser proof remains blocked by the Strike SW collision noted in TKT-0009 issue B).

## Ticket transition
- TKT-0007: `open` -> `inprogress` -> `resolved`.

## Next iteration
**Verification Agent** runs TKT-0007. On pass: commit `fix(TKT-0007): guard /connect auto-pair against hot-reload stampede`, push.
