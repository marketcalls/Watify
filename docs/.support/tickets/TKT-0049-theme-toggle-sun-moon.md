---
id: TKT-0049
title: Theme toggle uses sun / moon / system SVG icons instead of text labels
status: verified
priority: P3
area: frontend
related_tickets: TKT-0043
created: 2026-05-19T03:06:00Z
updated: 2026-05-19T03:06:00Z
created_by: resolving_agent
filed_via: user_direct_request
---

## Summary
Operator directive: "theme switcher user sun / moon theme switcher." Replace the text label with sun/moon SVG icons. Override of the project's general no-icons rule for this specific control because sun/moon are the universally-recognized theme-switch convention.

## Fix
`frontend/src/components/ThemeToggle.tsx` -- the button now renders one of three inline SVG icons based on the active theme:
- Light -> Sun (circle + 8 rays)
- Dark -> Moon (crescent)
- System -> Monitor (rectangle + base)

Text label is preserved in a `sr-only` span for screen readers; aria-label still describes the current state.

Padding changed `px-3 py-1.5` -> `p-2` so the button is a square 32px tap-target rather than wider than tall.

`npx tsc --noEmit` exit 0. Build smoke: dev HMR picks up; production build still prerenders.

## Resolution history
- 2026-05-19T03:06:00Z -- filed and resolved + verified inline per operator directive.
