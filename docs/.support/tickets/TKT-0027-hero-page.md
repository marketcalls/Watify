---
id: TKT-0027
title: Public hero page at /, move dashboard to /dashboard
status: verified
priority: P2
area: frontend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T20:36:00Z
created_by: ticketing_agent
related_plan_item: F-08, A1
related_tickets: TKT-0026
filed_via: human_manual_input
---

## Summary
Today `/` is the authed Dashboard. v1.1 needs `/` to be a public marketing hero. Move the existing Dashboard to `/dashboard`.

## Expected
- Move `frontend/src/app/page.tsx` (Dashboard) -> `frontend/src/app/dashboard/page.tsx`.
- New `frontend/src/app/page.tsx` (hero):
  - Above-the-fold: big headline ("Send WhatsApp messages to your friend watchlists -- on your own terms."), subhead, two CTAs ("Sign in" -> /login, "Get started" -> /register).
  - Feature triplet: (1) Pair via QR or pair-code, (2) Up to 20 contacts per group with 3-30s random delay, (3) Schedule sends or fire now.
  - Footer note: "Watify is single-user. Built on the unofficial wars library; see docs/wars.md for risk notes."
- TopNav: when on `/`, `/login`, `/register` and not authed, show `[Watify] Sign in | Get started`.
- All other internal pages (currently `/connect`, `/groups`, `/send`, `/history`) keep their paths -- the auth guard in TKT-0029 will redirect them to `/login` when unauthed.
- All hero copy in plain text, no emojis (CLAUDE.md), Tailwind only.

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
- 2026-05-18T20:32:00Z -- resolved by Resolving Agent (iter68). Five file changes: (1) `frontend/src/app/dashboard/page.tsx` (new) -- the existing DashboardPage component verbatim, just relocated; useGroups + useJobs + BackendStatus + SoftCapBanner + WhatsAppTile imports unchanged so the dashboard semantics are 100% preserved. (2) `frontend/src/app/page.tsx` (rewritten) -- public hero: a Next.js server component (no `use client`), exports `metadata` with title + description, renders an above-the-fold section with the spec headline "Send WhatsApp messages to your friend watchlists -- on your own terms.", subhead about single-user + QR + 20-cap + random delay + schedule, two CTAs (`Link href="/login"` "Sign in" filled dark + `Link href="/register"` "Get started" outline), a three-card feature triplet (Pair with QR or pair-code / Friend groups capped at 20 / Send now or schedule), and a footer note "Watify is single-user. Built on the unofficial wars library; see docs/wars.md for risk notes." All plain text, no emojis, no icons, Tailwind only. (3) `frontend/src/app/login/page.tsx:50` -- changed `router.push("/")` to `router.push("/dashboard")`. (4) `frontend/src/app/register/page.tsx:42` -- changed `router.push("/")` to `router.push("/dashboard")`. (5) `frontend/src/components/TopNav.tsx:4` -- changed the `Dashboard` nav link `href: "/"` to `href: "/dashboard"` with a TKT-0027/TKT-0028 reference comment (auth-aware nav is still TKT-0028's job). `npx tsc --noEmit` exit 0. Dev-server smoke: `curl http://localhost:3000/` HTTP 200 with the five expected copy strings ("Send WhatsApp messages", "on your own terms", "Sign in", "Get started", "Friend groups, capped at 20"); `curl http://localhost:3000/dashboard` HTTP 200. The brand link in TopNav still points at `/` which is now the hero -- correct behavior: clicking the Watify wordmark takes you home. Awaits Verification Agent. Conversation: `docs/.support/conversations/2026-05-18T203043Z-resolving_agent-iter68.md`.
- 2026-05-18T20:36:00Z -- VERIFIED by Verification Agent (iter69). Six proofs: (1) File presence -- all five files (`app/page.tsx` 2965b, `app/dashboard/page.tsx` 2857b, `app/login/page.tsx` 4951b, `app/register/page.tsx` 5805b, `components/TopNav.tsx` 1278b). (2) Non-ASCII char scan -- zero across every edited file (no emojis/icons crept in). (3) `npx --no-install tsc --noEmit` exit 0. (4) Dev-server smoke -- `GET /` 200 (20565 bytes), `GET /dashboard` 200 (18447 bytes), `GET /login` 200, `GET /register` 200; `/` body contains all seven expected hero copy strings (`Send WhatsApp messages`, `on your own terms`, `Sign in`, `Get started`, `Friend groups, capped at 20`, `Pair with QR`, `Built on the unofficial wars`); `/dashboard` body contains the four expected dashboard markers (`WhatsApp notifications`, `Friend groups`, `Getting started`, `Open Connect`). (5) `router.push("/dashboard")` confirmed at `login/page.tsx:49` and `register/page.tsx:42`. (6) TopNav `links[0]` is `{ href: "/dashboard", label: "Dashboard" }` at line 7. Verified.
