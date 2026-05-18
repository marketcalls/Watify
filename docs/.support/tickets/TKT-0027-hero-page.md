---
id: TKT-0027
title: Public hero page at /, move dashboard to /dashboard
status: open
priority: P2
area: frontend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
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
