---
id: TKT-0050
title: Disconnect bounces back to connected because auto-pair re-fires
status: verified
priority: P1
area: frontend
related_tickets: TKT-0010
created: 2026-05-19T03:09:00Z
updated: 2026-05-19T03:09:00Z
created_by: resolving_agent
filed_via: user_report
---

## Summary
Operator: "in /connect even if i disconnect it is again back to connect status." Clicking Disconnect successfully tears down wars's session for an instant, then the page's auto-pair `useEffect` sees `waState.state === "disconnected"` and immediately re-fires `connect()`.

## Root cause
`frontend/src/app/connect/page.tsx` `handleDisconnect` was clearing both `autoStarted.current` and `sessionStorage.AUTO_FLAG`. That undid the suppression that prevents the disconnected->auto-pair loop. So the next SWR poll showing `state=disconnected` re-triggered the auto-pair effect.

## Fix
`handleDisconnect` now SETS `autoStarted.current = true` and writes the AUTO_FLAG, so the auto-pair effect treats this mount as already-handled. The operator can still re-pair via the "Start pairing" button on the disconnected panel.

## Resolution history
- 2026-05-19T03:09:00Z -- filed + resolved + verified inline per operator report.
