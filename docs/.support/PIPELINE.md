# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: ticketing_agent
iteration: 69
last_updated: 2026-05-18T20:36:00Z
last_conversation: docs/.support/conversations/2026-05-18T203528Z-verification_agent-iter69.md
servers:
  backend_running: true
  backend_pid: 20252
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 11
  inprogress: 0
  resolved: 0
  verified: 23
ticket_index:
  TKT-0024: verified P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: verified P1 backend Auth middleware
  TKT-0026: verified P1 frontend /login + /register pages
  TKT-0027: verified P2 frontend Public hero page; move dashboard to /dashboard
  TKT-0030: verified P1 infra install/install.sh + update.sh
  TKT-0034: verified P1 frontend apiFetch credentials include
  TKT-0027: open P2 frontend Public hero page; move dashboard to /dashboard
  TKT-0028: open P2 frontend Auth-aware TopNav
  TKT-0029: open P2 frontend Route guards
  TKT-0030: open P1 infra install/install.sh + update.sh
  TKT-0032: open P2 backend CSRF defense (X-Requested-With + Origin check)
  TKT-0033: open P3 frontend Track Next.js postcss XSS advisory
  TKT-0006: open P3 backend Move test phone constant out of smoke_db.py
  TKT-0008: open P2 frontend Global toaster
  TKT-0014: open P2 backend Pair-code mode alongside QR
  TKT-0016: open P3 backend Pair state machine paired vs ready
  TKT-0017: open P3 backend JID helpers
  TKT-0018: open P3 frontend SSE push of QR
  TKT-0022: open P3 frontend Job drawer cache drift
```

## Next Action
**Ticketing Agent** re-triages after TKT-0027 verified. Open queue is now entirely P2/P3 polish. Suggested next Resolving target: **TKT-0028** (P2 frontend) -- auth-aware TopNav. The current TopNav unconditionally renders Dashboard/Connect/Groups/Send/History links plus a Watify wordmark; for the public hero + login + register routes (when not authed) it should instead render `[Watify wordmark] Sign in | Get started`. Use the existing `useAuth()` hook (TKT-0026) to drive the conditional render. After TKT-0028, TKT-0029 (route guards on the dashboard-side pages) closes the v1.1 polish chain. The Ticketing Agent should also run a brief security spot pass over the iter68 diff (TopNav + hero + dashboard move + login/register redirect change) -- no new env vars, no inline secrets, no dangerouslySetInnerHTML, no eval.

## History (latest only)
- 2026-05-18T20:07:00Z iter63 verification_agent -> ticketing | TKT-0026 VERIFIED + committed c9835a8: eight proofs -- file presence (4 files), exports (`auth`/`AuthAck`/`MeResponse`), useAuth 401-as-null + shouldRetryOnError=false, zero non-ASCII chars (no emojis/icons), tsc --noEmit exit 0, curl /login + /register HTTP 200 with expected copy strings, Next.js compiled src_app_login_page_tsx_05e8nkp._.js chunk, backend endpoints behave per UI contract (auth/me 401, register 409 registration_closed, login bad-password 401 invalid_credentials) | log: docs/.support/conversations/2026-05-18T200607Z-verification_agent-iter63.md
- 2026-05-18T20:11:28Z iter64 ticketing_agent -> resolving | re-triage after TKT-0026 verified; diff-scoped security pass over the four TKT-0026 files clean (no dangerouslySetInnerHTML/eval, no localStorage/sessionStorage/document.cookie reads, no hex secrets, no Authorization/Bearer headers, no console.log of bodies); no new tickets filed; next: Resolving picks TKT-0030 (P1 infra install.sh) with TKT-0027 as the immediate follow-on for the user-visible hero swap | log: docs/.support/conversations/2026-05-18T201128Z-ticketing_agent-iter64.md
- 2026-05-18T20:20:00Z iter65 resolving_agent -> verification | TKT-0030 RESOLVED: shipped install/install.sh (540 lines, full nine-step structure -- pre-flight + prompts + apt/Node 20/uv + clone-or-pull + WATIFY_APP_SECRET/API_KEY/SESSION_ENCRYPTION_KEY/OWNER_PHONE preservation on re-run + uv sync + npm build + dirs+chmod+logrotate + hardened systemd units on unix socket + Nginx with Cloudflare $http_cf_connecting_ip map + auth-endpoint limit_req + security headers + cache headers + WebSocket Upgrade + certbot --nginx + HSTS snippet + cron renewal + start banner), install/update.sh (59 lines: fetch + reset --hard + uv sync + npm build + systemctl restart with elapsed-time banner), .gitattributes forcing `*.sh text eol=lf`; bash -n clean on both | log: docs/.support/conversations/2026-05-18T201613Z-resolving_agent-iter65.md
- 2026-05-18T20:22:30Z iter66 verification_agent -> ticketing | TKT-0030 VERIFIED + committed 8808ae8: six proofs -- bash -n clean on both scripts, .gitattributes forces LF endings, 18 WATIFY_* env names match settings.py exactly with no deprecated WATIFY_SECRET_KEY/JWT_SECRET leaks, section-by-section walkthrough lines every numbered spec step against install.sh, update.sh has the full fetch-reset-sync-build-restart-check chain | log: docs/.support/conversations/2026-05-18T202114Z-verification_agent-iter66.md
- 2026-05-18T20:26:01Z iter67 ticketing_agent -> resolving | install-script security spot pass clean: no inline secrets, two curl|bash sources are first-party (deb.nodesource.com/setup_20.x + astral.sh/uv/install.sh), chmod 600 on .env + app.db + whatsapp.db, 5x systemd hardening per unit (NoNewPrivileges/PrivateTmp/ProtectSystem=strict/ProtectHome=true/ReadWritePaths), Nginx denies dotfiles and leakage paths and sets X-Frame-Options/X-Content-Type-Options/X-XSS-Protection/Referrer-Policy + HSTS via ssl-security.conf; counts open=12 verified=22; no new tickets; next: Resolving picks TKT-0027 (P2 frontend public hero + /dashboard move) | log: docs/.support/conversations/2026-05-18T202601Z-ticketing_agent-iter67.md
- 2026-05-18T20:32:00Z iter68 resolving_agent -> verification | TKT-0027 RESOLVED: five-file change set -- new frontend/src/app/dashboard/page.tsx (dashboard verbatim relocated), rewrote frontend/src/app/page.tsx as public hero (server component with metadata, headline + two CTAs + feature triplet + wars footer, Tailwind only, no emojis), login + register router.push pointed at /dashboard, TopNav Dashboard nav link updated to /dashboard with TKT comment; npx tsc --noEmit exit 0; dev-server curl: / 200 with hero copy, /dashboard 200 with dashboard markup | log: docs/.support/conversations/2026-05-18T203043Z-resolving_agent-iter68.md
- 2026-05-18T20:36:00Z iter69 verification_agent -> ticketing | TKT-0027 VERIFIED + committed: six proofs -- 5 files present (sizes 2965/2857/4951/5805/1278b), zero non-ASCII chars in any edited file, tsc --noEmit exit 0, dev-server curl / 200 (20565b, 7 hero copy strings) + /dashboard 200 (18447b, 4 dashboard markers) + /login + /register both 200, router.push("/dashboard") confirmed in login + register, TopNav links[0] href=/dashboard | log: docs/.support/conversations/2026-05-18T203528Z-verification_agent-iter69.md
