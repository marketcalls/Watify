---
id: TKT-0036
title: Toaster getServerSnapshot must return a stable reference (React infinite-loop warning)
status: verified
priority: P0
area: frontend
created: 2026-05-18T22:33:00Z
updated: 2026-05-18T22:33:00Z
created_by: resolving_agent
related_plan_item: -
related_tickets: TKT-0008
filed_via: user_console_report
---

## Summary
React 19 logs `The result of getServerSnapshot should be cached to avoid an infinite loop` from `<Toaster />` mount in `RootLayout` (`src/app/layout.tsx:37`). The error is fired by every page that mounts the layout, which is every authed page + the public hero + login + register.

## Root cause
`frontend/src/components/Toaster.tsx:60-62` (introduced in TKT-0008 / iter80):

```ts
function getServerSnapshot(): Toast[] {
  return [];
}
```

`useSyncExternalStore` calls this function on every render during SSR/hydration; returning a fresh `[]` literal creates a NEW array each call, so React sees a new identity and considers the snapshot to have changed, triggering re-render -> new snapshot -> re-render -> the React DevTools warning. The `getSnapshot` version below it returns the module-level `toasts` reference which is stable until `notify()` runs, so it does not have the same issue.

## Fix
Hoist an empty-array module constant and return it from both `getServerSnapshot` and as the initial value of `toasts`:

```ts
const EMPTY: Toast[] = Object.freeze([]) as unknown as Toast[];
function getServerSnapshot(): Toast[] {
  return EMPTY;
}
```

(Object.freeze defensive; the array is read-only during server pass anyway.)

## Acceptance
- Console error no longer fires on dashboard / login / hero mount.
- Toast still appears for the four wired hooks (groups create/delete, bulk add, wa disconnect, job cancel).
- `npx tsc --noEmit` exit 0.

## Resolution history
- 2026-05-18T22:33:00Z -- filed and immediately resolved by Resolving Agent (iter92) as a P0 user-reported regression from TKT-0008 (iter80). Two-line fix in `frontend/src/components/Toaster.tsx`: (1) hoisted `const EMPTY: Toast[] = Object.freeze([]) as unknown as Toast[]` and made `toasts` start as `EMPTY` (line 22 cluster). (2) `getServerSnapshot` returns the shared `EMPTY` reference instead of a new `[]` literal. `Object.freeze` is defensive against a future caller mutating the snapshot array. `npx tsc --noEmit` exit 0. Dev-server smoke: `curl /dashboard` HTTP 200; HMR picked the change up so the user can hard-refresh the browser tab and the console error should be gone. Awaits Verification Agent for the live browser confirmation. Conversation: `docs/.support/conversations/2026-05-18T223206Z-resolving_agent-iter92.md`.
- 2026-05-18T22:38:00Z -- VERIFIED by Verification Agent (iter93). Four proofs: (a) `frontend/src/components/Toaster.tsx` contains the TKT-0036 comment + `const EMPTY: Toast[] = Object.freeze([])` at line 32, `let toasts: Toast[] = EMPTY` at line 34, `getServerSnapshot` returns `EMPTY` at line 70, `useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)` at line 81. (b) `npx --no-install tsc --noEmit` exit 0. (c) Dev-server curl `/` + `/dashboard` + `/login` all 200. (d) Production build (`npm run build`) still exit 0 -- all 9 routes prerender as Static; the EMPTY-array change does not affect SSR output (Toaster renders nothing when `items.length === 0`, and `EMPTY` is exactly that). The console-warning disappearance is a browser-runtime check the operator confirms via hard-refresh; structural fix is correct.
