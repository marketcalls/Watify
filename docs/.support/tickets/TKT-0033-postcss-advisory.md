---
id: TKT-0033
title: Track Next.js postcss XSS advisory (GHSA-qx2v-qp2m-jg93)
status: verified
priority: P3
area: frontend
created: 2026-05-18T19:01:30Z
updated: 2026-05-18T19:01:30Z
created_by: ticketing_agent
related_plan_item: -
filed_via: security_audit_iter51
---

## Summary
`npm audit` flags 2 moderate vulnerabilities in `frontend/`:
- `postcss < 8.5.10` -- XSS via unescaped `</style>` in CSS Stringify output (GHSA-qx2v-qp2m-jg93).
- `next` (16.2.6) depends on the vulnerable postcss transitively.

`npm audit fix --force` would install `next@9.3.3` -- a catastrophic major downgrade from 16.x. **Do NOT run it.**

## Risk assessment
The advisory matters when an app generates CSS at runtime from untrusted input. Watify:
- Tailwind compiles at build time, statically.
- No runtime CSS-in-JS with user data.
- No `<style dangerouslySetInnerHTML>`.

Effective real-world impact for Watify: **near zero**. Tracking for visibility, not urgent.

## Expected
1. Wait for Next.js to bump its bundled postcss in a patch release; update with the next normal upgrade window.
2. As a near-term option: add an npm `overrides` block in `package.json`:
   ```json
   "overrides": { "postcss": "^8.5.10" }
   ```
   Smoke-test the build; if the override compiles clean, ship it.
3. Periodically re-run `npm audit` (e.g. in a CI step) and re-evaluate.

## Resolution history
- 2026-05-18T19:01:30Z -- filed by Ticketing Agent (iter51, npm audit).
- 2026-05-18T22:18:00Z -- resolved by Resolving Agent (iter89). Pre-fix state: `next@16.2.6` bundled `postcss@8.4.31` (vulnerable); `@tailwindcss/postcss@4.3.0` bundled `postcss@8.5.14` (already patched). `npm audit` reported 2 moderate advisories. Fix: added `"overrides": { "postcss": "^8.5.10" }` to `frontend/package.json`; ran `npm install` (exit 0). Post-fix `npm ls postcss`: both `@tailwindcss/postcss@4.3.0` and `next@16.2.6` now resolve `postcss@8.5.14` (next's is deduped via the override). `npm audit` reports 0 vulnerabilities across all severities (down from 2 moderate). Build smoke: first attempt of `npm run build` failed at `Generating static pages` for `/login` -- the Next.js 16 static-prerender path requires `useSearchParams()` (added in iter74 for `?next=` open-redirect handling) to sit inside a Suspense boundary; the dev server tolerated the bare hook but the production build does not. Inline fix in the same iteration since the smoke is part of TKT-0033's acceptance: split `/login`'s default export into a Suspense wrapper around the existing `LoginForm` body, with `import { Suspense, useState } from "react"` and `<Suspense fallback={null}>`. Re-ran `npm run build` -- exit 0, all 11 pages prerender as static content. tsc exit 0. Dev-server smoke (pid 42204): `curl http://localhost:3000/login` HTTP 200 with the three expected copy strings still present, so HMR also re-rendered cleanly. Conversation: `docs/.support/conversations/2026-05-18T221640Z-resolving_agent-iter89.md`.
- 2026-05-18T22:22:00Z -- VERIFIED by Verification Agent (iter90). Six proofs reproduced independently: (a) `frontend/package.json:24-26` contains `"overrides": { "postcss": "^8.5.10" }`. (b) `npm ls postcss` shows both `@tailwindcss/postcss@4.3.0 -> postcss@8.5.14 overridden` and `next@16.2.6 -> postcss@8.5.14 deduped` -- both copies are at the patched version, no version older than 8.5.10 anywhere in the tree. (c) `npm audit --json` reports `{info:0, low:0, moderate:0, high:0, critical:0, total:0}` -- zero vulnerabilities across all severities. (d) `frontend/src/app/login/page.tsx:3` imports `Suspense`; `:46` opens `<Suspense fallback={null}>` inside the default LoginPage export; `:52` declares `function LoginForm()` which holds the actual form body. (e) `npx --no-install tsc --noEmit` exit 0. (f) `npm run build` exit 0; all 9 routes (`/`, `/_not-found`, `/connect`, `/dashboard`, `/groups`, `/history`, `/login`, `/register`, `/send`) prerender as Static. Verified.
