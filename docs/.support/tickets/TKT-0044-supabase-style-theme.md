---
id: TKT-0044
title: Supabase-style dark theme overhaul (hero + global)
status: open
priority: P2
area: frontend
created: 2026-05-18T22:56:00Z
updated: 2026-05-18T22:56:00Z
created_by: ticketing_agent
related_plan_item: -
related_tickets: TKT-0027, TKT-0043
filed_via: user_direct_request_with_reference_screenshot
---

## Summary
Operator wants Watify's hero + entire UI to match the OpenAlgo / Supabase aesthetic: pitch-black background, subtle grid overlay, gradient-text headline, lavender or emerald accent, pill-style badges, stat row, and pill-chip integrations strip.

Reference screenshots:
- OpenAlgo hero -- `c:\Users\Admin1\Desktop\2026-05-19_04-24-21.png` (operator-provided).
- Supabase: pitch-black `#0a0a0a`, signature emerald `#3ECF8E`, Inter typography, subtle grids.

## Scope (multi-iteration)
This is a substantial design overhaul touching every component. Recommended split into iterations (file as separate sub-tickets if useful):

### Iteration A -- design tokens + global shell
- Add a Tailwind theme extension (`frontend/tailwind.config.ts` or via `@theme` in globals.css) defining:
  - Brand palette: `brand-50` ... `brand-900` (pick emerald-leaning to match Supabase, OR violet-leaning to match OpenAlgo -- operator picks).
  - Accent: pulse-dot green.
  - Surface ramp: `surface-0` pitch-black, `surface-1` near-black, `surface-2` zinc-900, etc.
- Switch base `body` to pitch-black (`bg-[#0a0a0a]` or `bg-zinc-950`) in `globals.css`.
- Add a subtle grid background to the hero only -- CSS `background-image: linear-gradient(rgba(...) ...)` on the `<section>`.
- Switch font to Inter via `next/font/google` in `layout.tsx`. Remove Geist if operator prefers Supabase-style Inter; or leave Geist.
- `npx tsc --noEmit` exit 0; `npm run build` exit 0; visual regression: every existing page still renders without unstyled-element fallbacks.

### Iteration B -- new hero
- Rewrite `frontend/src/app/page.tsx`:
  - Top pill badge with a green pulse dot. Copy: e.g. "BETA - WhatsApp notifications for your friend watchlists" (operator picks the badge text).
  - Two-line gradient headline. Operator picks the exact wording; suggested: "Single-user / WhatsApp notifications" with the second line carrying a violet/emerald gradient via `bg-clip-text text-transparent bg-gradient-to-r from-purple-300 to-pink-300` (lavender) or `from-emerald-300 to-teal-300` (Supabase green).
  - Subhead in the brand color.
  - Long description in muted gray.
  - Stat row (three cells): e.g. "20 contacts/group", "3-30s random delay", "1 user only" -- factual stats from REQUIREMENTS, no fake numbers.
  - Two CTAs: filled-brand "Get started ->" + outlined "Sign in" (swap from current order). The OpenAlgo screenshot had a GitHub button; we can include a "GitHub" outlined button linking to `https://github.com/marketcalls/Watify` since the repo is public.
  - Below CTAs: "INTEGRATES WITH" pill-chip row -- single chip: "WhatsApp" (we don't integrate with anything else; the row is one chip).

### Iteration C -- TopNav + dashboard polish
- Restyle TopNav to match the dark aesthetic. Add a small green pulse dot next to "WhatsApp connected" indicator (which is currently text on the dashboard).
- Dashboard cards: switch to `bg-zinc-900/40` with brand-color hover states. Stat numbers in the brand color, labels in muted gray.
- /connect ReadyPanel: keep the existing emerald treatment (it already matches Supabase's green).
- /groups, /send, /history: bring tables / cards into the same dark palette.

### Iteration D -- pair with TKT-0043 (theme toggle)
- The toggle in TKT-0043 lets the user opt out of the new dark default to a light variant.
- After TKT-0044's iter A-C ship, the codebase is dark-first; the toggle becomes a "force light" or "force system" switch.

## Acceptance (across iterations)
- Hero matches the OpenAlgo / Supabase aesthetic in palette + layout. Operator review screenshot from the deployed dev server.
- Every authed page is legible in dark mode. No washed-out text.
- `npx tsc --noEmit` exit 0 throughout.
- `npm run build` exit 0 throughout. All 9 routes still prerender Static.
- TKT-0043 (theme toggle) still works after this lands.

## Out of scope
- Reskinning the install.sh banner colors (server-side, not visible to end users).
- Tablet/mobile breakpoints beyond what Tailwind already gives us.
- Logo design.

## Resolution history
- 2026-05-18T22:56:00Z -- filed by Ticketing Agent at operator request after they shared the OpenAlgo hero screenshot and asked for Supabase styling across the app.
