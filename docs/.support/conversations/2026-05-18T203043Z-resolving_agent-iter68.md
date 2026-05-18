# Iteration 68 -- Resolving Agent (TKT-0027)

- **Started**: 2026-05-18T20:30:43Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0027 (P2 frontend) -- public hero + /dashboard move

## Plan
1. Move current dashboard component to `frontend/src/app/dashboard/page.tsx` (no content changes -- just the route).
2. Write new `frontend/src/app/page.tsx` as a public hero with: headline + subhead, two CTAs (Sign in -> /login, Get started -> /register), feature triplet, footer wars note. Plain text, no emojis, Tailwind only.
3. Update post-success redirects: `frontend/src/app/login/page.tsx` and `frontend/src/app/register/page.tsx` -- `router.push("/")` -> `router.push("/dashboard")`.
4. Audit other internal `Link href="/"` / `router.push("/")` that referenced the dashboard implicitly.
5. `npx tsc --noEmit` clean.
6. Mark TKT-0027 `resolved`, advance phase=verification, agent=verification_agent.

Out of scope: TopNav nav links update (that's TKT-0028) and route guards (TKT-0029). The TopNav can keep its current links pointing at `/`, `/connect`, `/groups`, etc.; `/` will become the hero so the home link goes to hero, not dashboard. That's the user-correct behavior already.

## Actions

1. Marked TKT-0027 `inprogress`.
2. Read existing `frontend/src/app/page.tsx` (the current dashboard). Identified internal refs to fix: login + register `router.push("/")`, TopNav `links[0].href` + brand `href`.
3. Wrote `frontend/src/app/dashboard/page.tsx` -- exact duplicate of the dashboard's previous contents (BackendStatus + SoftCapBanner + WhatsAppTile + useGroups/useJobs stats grid + Getting Started section).
4. Overwrote `frontend/src/app/page.tsx` with the new hero -- a server component with `metadata` export, headline + subhead + two CTAs + feature triplet + footer wars note. No `use client` directive because nothing in the hero needs client-side state.
5. Edited `frontend/src/app/login/page.tsx:50` `router.push("/")` -> `router.push("/dashboard")`.
6. Edited `frontend/src/app/register/page.tsx:42` `router.push("/")` -> `router.push("/dashboard")`.
7. Edited `frontend/src/components/TopNav.tsx:4` `Dashboard` link's href from `/` to `/dashboard` + added a one-line TKT comment. The brand `Link href="/"` is intentionally left as-is so clicking the wordmark goes home (the hero) -- standard marketing-site convention.
8. `npx --no-install tsc --noEmit` -> exit 0.
9. Smoke against the live dev server (pid 42204):
   - `curl http://localhost:3000/` -> HTTP 200; body contains all five hero copy strings ("Send WhatsApp messages", "on your own terms", "Sign in", "Get started", "Friend groups, capped at 20").
   - `curl http://localhost:3000/dashboard` -> HTTP 200; serves the dashboard.
10. Marked TKT-0027 `resolved` with the five-file Resolution history entry.

## Outcome
TKT-0027 resolved. `/` is now the public hero, `/dashboard` is the existing dashboard, post-login + post-register both push into `/dashboard`, and the TopNav's Dashboard link now points correctly. The user's iter57 question ("when I type localhost:3000 still why I see this?") is structurally fixed -- visiting `/` shows the hero, not the dashboard. Next: Verification Agent confirms both routes serve, copy is present, tsc is clean, and commits as `fix(TKT-0027): public hero page at /, move dashboard to /dashboard`.
