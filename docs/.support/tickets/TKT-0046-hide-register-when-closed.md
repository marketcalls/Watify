---
id: TKT-0046
title: Hide Get started / Register CTAs once the single user is registered
status: open
priority: P2
area: frontend
related_tickets: TKT-0026, TKT-0028, TKT-0027
created: 2026-05-18T23:03:00Z
updated: 2026-05-18T23:03:00Z
created_by: ticketing_agent
filed_via: user_direct_request
---

## Summary
Watify is single-user. After the admin account is created, every visit to `/register` returns 409 `registration_closed` (handled by the register page's "App already registered" panel). But the **invitations to register** are still everywhere:
- Public hero (`/`): "Get started" CTA links to `/register`.
- TopNav unauthed branch: "Get started" pill links to `/register`.
- Login page footer: "No account yet? Create the admin account" links to `/register`.

These should hide once registration is closed so the unauthed UX is just "Sign in" rather than a dead-end CTA.

## Approach
Need a no-auth signal that says "registration is closed". Three options:

### Option A -- extend `/api/health`
Add a boolean field `registered: bool` (derived from `auth_repo.count_users(db) > 0`). `/api/health` is already public + allowlisted in AuthMiddleware + CSRFMiddleware so no auth wiring required. The frontend's `useHealth()` hook already polls every 3s; consumers add a single conditional.

### Option B -- new `GET /api/auth/status`
Dedicated endpoint returning `{ registered, auth_configured }`. Cleaner separation but more wiring and another fetch. **Not recommended.**

### Option C -- silently let /register handle it
Keep the CTAs visible. The 409 + "App already registered" panel already informs the user. **Simplest, but worse UX -- the user clicks Get started expecting to register and gets a wall instead.**

**Pick Option A.**

## Expected deliverables (Option A)

1. **Backend** -- `backend/app/main.py:117` (the `/api/health` handler) adds a `registered: bool` field by importing `auth_repo.count_users` and resolving inside a `Session(engine)`. The field is `null` (or absent) when `app_secret` is empty (auth disabled).
2. **Frontend api.ts** -- extend the `Health` type with `registered: boolean | null`.
3. **Frontend useHealth** -- already polls /api/health every 3s, no change.
4. **Hero `app/page.tsx`** -- import `useHealth`. Hide the "Get started" CTA when `health?.registered === true`. Keep the "Sign in" CTA always.
5. **TopNav `components/TopNav.tsx`** -- in the unauthed branch, hide the "Get started" pill when `useHealth().health?.registered === true`.
6. **Login `app/login/page.tsx`** -- hide the "Create the admin account" footer link when `health?.registered === true`. (Optional polish.)
7. **Register `app/register/page.tsx`** -- no change needed; the 409 panel still works as a fallback if someone hand-navigates.

## Acceptance
- Backend: `curl /api/health` returns `{"ok":true,...,"registered":true}` when a user exists; `{"ok":true,...,"registered":false}` when no user exists.
- Frontend: with the admin already registered, visiting `/` shows only the "Sign in" CTA; TopNav's unauthed branch shows only "Sign in".
- `npx tsc --noEmit` exit 0.
- `npm run build` exit 0.

## Out of scope
- A "delete admin and reset" flow. Once registered, the operator can hand-edit `app.db` if they want to start over (operator already did this once in iter91).

## Resolution history
- 2026-05-18T23:03:00Z -- filed at operator's request after seeing the Get started CTA still active post-registration.
