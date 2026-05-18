---
id: TKT-0026
title: /login + /register pages with forms, validation, cookie flow
status: open
priority: P1
area: frontend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: F-08, A3
related_tickets: TKT-0024
filed_via: human_manual_input
---

## Summary
Two new Next.js routes that consume TKT-0024's endpoints. Token storage lives in httpOnly cookies set by the backend -- the frontend never sees the JWT.

## Expected
- `frontend/src/app/login/page.tsx`:
  - Username + password fields, "Sign in" button.
  - On submit -> `fetch('/api/auth/login', {method:'POST', credentials:'include', body: json})`.
  - On 200 -> `router.push('/dashboard')`.
  - On 401 -> "Invalid username or password" inline.
  - On 429 -> show `Retry-After` in seconds + "Too many attempts, try again in N seconds".
- `frontend/src/app/register/page.tsx`:
  - Same form shape, "Create account" button.
  - Helper text: "Watify is single-user; only one account can be registered."
  - On 409 `registration_closed` -> render the "App already registered" panel + link to /login.
- `frontend/src/lib/api.ts` -> `auth.login`, `auth.register`, `auth.logout`, `auth.me` typed helpers with `credentials: "include"`.
- `frontend/src/hooks/useAuth.ts` -> SWR `/api/auth/me` (revalidate on focus, cache 60s). Exposes `{user, isLoading, isError, logout()}`.
- Form validation: password >= 12 chars (matches REQUIREMENTS A2).

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
