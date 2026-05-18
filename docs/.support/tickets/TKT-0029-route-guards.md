---
id: TKT-0029
title: Route guards on /dashboard, /connect, /groups, /send, /history
status: open
priority: P2
area: frontend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: F-08, A6
related_tickets: TKT-0026, TKT-0028
filed_via: human_manual_input
---

## Summary
The authed pages currently render whatever data they fetch. With auth enabled the API will 401; the UI should redirect to `/login` rather than show error toasts.

## Expected
Two layers:

1. **Server-side guard (preferred when feasible)** -- `app/(authed)/layout.tsx` reads the `watify_session` cookie in a Next.js Server Component, hits `/api/auth/me`, redirects to `/login` if 401. Routes that need auth move under that route group: `app/(authed)/dashboard/page.tsx` etc.
2. **Client-side guard fallback** -- `frontend/src/components/RequireAuth.tsx`: client component that calls `useAuth()`; while `isLoading` renders a thin skeleton; on `!user` calls `router.replace('/login?next=' + pathname)`. Wrap each authed page until the route group migration lands.

After login, the `?next=` param drives a redirect back. Sensible default: `/dashboard`.

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
