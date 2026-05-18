---
id: TKT-0028
title: Auth-aware TopNav (Login/Register vs Dashboard/Logout)
status: open
priority: P2
area: frontend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: F-08, A6
related_tickets: TKT-0026
filed_via: human_manual_input
---

## Summary
TopNav currently always shows the authed links. Should branch on `useAuth()` state.

## Expected
- `frontend/src/components/TopNav.tsx`:
  - Authed: `[Watify] Dashboard Connect Groups Send History` + right-side `<username> Logout`.
  - Unauthed: `[Watify]` + right-side `Sign in | Get started`.
  - Loading (first paint while SWR resolves): show the brand only, no links. Avoids flash-of-wrong-state.
- Logout button posts `/api/auth/logout` then `mutate('/api/auth/me', null)` so SWR drops the cached user; `router.push('/')`.
- Username pulled from `useAuth().user?.username` (set by GET /api/auth/me).

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
