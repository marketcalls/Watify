---
id: TKT-0047
title: Hero CTAs misaligned -- Sign in renders below GitHub due to nested flex+mt-8
status: verified
priority: P1
area: frontend
created: 2026-05-19T03:00:00Z
updated: 2026-05-19T03:00:00Z
created_by: resolving_agent
related_tickets: TKT-0044, TKT-0046
filed_via: user_report_screenshot
---

## Summary
Operator screenshot of `localhost:3000` shows the hero CTAs not on the same baseline: "Sign in" sits 32px lower than the "GitHub" outlined button. Buttons look "not in shape".

## Root cause
`frontend/src/components/HeroCTAs.tsx` wraps the Sign in / Get started links in its OWN `<div className="mt-8 flex flex-wrap gap-3">`. That wrapper becomes a single flex item inside the page's outer `<div className="mt-8 flex flex-wrap items-center justify-center gap-3">`. Result: the inner div carries an extra `mt-8` and creates a layout breakpoint where the GitHub button (a sibling of HeroCTAs, not of its children) sits at the parent flex's baseline while Sign in/Get started sit lower inside their own row.

## Fix
HeroCTAs returns its links as siblings in a React fragment; the parent on `app/page.tsx` is the only flex container that lays them out. Also bump `rounded` -> `rounded-md` so the corners read as buttons, not as 4px-corner rectangles, against the dark grid backdrop.

## Acceptance
- All three buttons (Sign in, Get started, GitHub) sit on one baseline.
- `npx tsc --noEmit` exit 0.
- curl / 200.

## Resolution history
- 2026-05-19T03:00:00Z -- filed + resolved + verified inline as a P1 hotfix per operator screenshot.
