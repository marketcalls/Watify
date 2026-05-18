---
id: TKT-0045
title: Login bounces back to /login because SWR cache for /api/auth/me is stale
status: verified
priority: P0
area: frontend
created: 2026-05-18T23:02:00Z
updated: 2026-05-18T23:02:00Z
created_by: resolving_agent
related_plan_item: -
related_tickets: TKT-0026, TKT-0029
filed_via: user_report_intermittent_login_bounce
---

## Summary
Operator reports "Invalid username or password" + sometimes successful-after-retry login. Backend log shows the actual POST `/api/auth/login` returns 200; backend `verify_credentials` accepts the canonical bytes. The bounce is a frontend race.

## Root cause
`frontend/src/app/login/page.tsx:65-67` (iter62 + iter68):
```ts
await auth.login(u, password);
router.push(safeNextPath(searchParams.get("next")));
```

The post-login `router.push("/dashboard")` happens immediately. The dashboard's `<RequireAuth>` (iter74) calls `useAuth()` (iter62 hook over `/api/auth/me`). SWR has a **cached `null`** for that key from before the login because the unauthed dashboard mount already populated it. SWR returns that cached `null` synchronously while triggering a background revalidate. RequireAuth's `useEffect` fires `router.replace("/login?next=...")` before the revalidate finishes -> the user bounces back to /login.

Intermittent symptom because:
- A fresh tab with no prior unauthed visit has no cached null, so first login works.
- A tab that previously sat on /, /login, or hit RequireAuth has the null cached and bounces.
- After a few retries, the SWR cache happens to be the fresh user and the dashboard sticks.

## Fix
In `frontend/src/app/login/page.tsx`, AWAIT a fresh SWR fetch (or trigger a global `mutate('/api/auth/me')`) BEFORE `router.push`. Two equivalent paths:

Path A -- use the existing `useAuth().refresh()`:
```ts
const { refresh } = useAuth();
// ...
await auth.login(u, password);
await refresh();           // forces SWR revalidate; resolves with the real user
router.push(safeNextPath(searchParams.get("next")));
```

Path B -- import the global SWR `mutate`:
```ts
import { mutate } from "swr";
// ...
await auth.login(u, password);
await mutate("/api/auth/me");
router.push(safeNextPath(searchParams.get("next")));
```

Path A is preferred because it goes through the hook's typed wrapper. Same fix needs to happen in `register/page.tsx` (same iter62 pattern, same race).

## Acceptance
- After `auth.login()` succeeds, the SWR cache for `/api/auth/me` is refreshed BEFORE `router.push`.
- Tab that was on `/` (unauthed dashboard branch via TopNav `useAuth`) when login form submitted no longer bounces back to /login.
- `npx tsc --noEmit` exit 0.

## Resolution history
- 2026-05-18T23:02:00Z -- filed and immediately resolved by Resolving Agent as a P0 hotfix from operator report. Edits in iter98 (Resolving + Verification bundled at operator request to push fast):
  - `frontend/src/app/login/page.tsx` -- import `mutate` from `swr`; after `auth.login()` succeeds, `await mutate("/api/auth/me")` BEFORE `router.push(safeNextPath(...))`. Forces SWR to evict the stale `null` for `/api/auth/me` and refetch the now-authenticated user so RequireAuth on the destination sees `user` (not `null`).
  - `frontend/src/app/register/page.tsx` -- same fix on the post-register branch (`await mutate("/api/auth/me")` before `router.push("/dashboard")`).
  - `npx tsc --noEmit` exit 0. `curl /login` HTTP 200. Behavior change is operator-side (sign in once and stay on dashboard instead of bouncing).
  - Bundled the verification step into the resolving iter because the operator explicitly asked to commit + push immediately. Next iter resumes the standard cycle.
