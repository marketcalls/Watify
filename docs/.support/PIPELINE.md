# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: ticketing_agent
iteration: 66
last_updated: 2026-05-18T20:22:30Z
last_conversation: docs/.support/conversations/2026-05-18T202114Z-verification_agent-iter66.md
servers:
  backend_running: true
  backend_pid: 20252
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 12
  inprogress: 0
  resolved: 0
  verified: 22
ticket_index:
  TKT-0024: verified P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: verified P1 backend Auth middleware
  TKT-0026: verified P1 frontend /login + /register pages
  TKT-0027: open P2 frontend Public hero page; move dashboard to /dashboard
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
**Ticketing Agent** re-triages after TKT-0030 verified. Remaining open queue is now entirely P2/P3 polish; the v1.1 P1 milestone (TKT-0024/0025/0026/0030/0031/0034) is fully complete. Suggested next Resolving pick: **TKT-0027** (P2 frontend) -- public hero at `/`, move dashboard to `/dashboard`. This is the user-visible swap that addresses the iter57 screenshot ("when I type localhost:3000 still why I see this?"). Followed by TKT-0028 (auth-aware TopNav) and TKT-0029 (route guards). The Ticketing Agent should run a brief security spot pass over the install.sh / update.sh diff -- specifically confirm: no hardcoded secrets, no `curl | bash` patterns from untrusted sources (only `astral.sh/uv/install.sh` and `deb.nodesource.com/setup_20.x` -- both first-party), `chmod 600` on .env and DB files, hardened systemd directives present, Nginx denies dotfiles. Then queue TKT-0027.

## History (latest only)
- 2026-05-18T20:07:00Z iter63 verification_agent -> ticketing | TKT-0026 VERIFIED + committed c9835a8: eight proofs -- file presence (4 files), exports (`auth`/`AuthAck`/`MeResponse`), useAuth 401-as-null + shouldRetryOnError=false, zero non-ASCII chars (no emojis/icons), tsc --noEmit exit 0, curl /login + /register HTTP 200 with expected copy strings, Next.js compiled src_app_login_page_tsx_05e8nkp._.js chunk, backend endpoints behave per UI contract (auth/me 401, register 409 registration_closed, login bad-password 401 invalid_credentials) | log: docs/.support/conversations/2026-05-18T200607Z-verification_agent-iter63.md
- 2026-05-18T20:11:28Z iter64 ticketing_agent -> resolving | re-triage after TKT-0026 verified; diff-scoped security pass over the four TKT-0026 files clean (no dangerouslySetInnerHTML/eval, no localStorage/sessionStorage/document.cookie reads, no hex secrets, no Authorization/Bearer headers, no console.log of bodies); no new tickets filed; next: Resolving picks TKT-0030 (P1 infra install.sh) with TKT-0027 as the immediate follow-on for the user-visible hero swap | log: docs/.support/conversations/2026-05-18T201128Z-ticketing_agent-iter64.md
- 2026-05-18T20:20:00Z iter65 resolving_agent -> verification | TKT-0030 RESOLVED: shipped install/install.sh (540 lines, full nine-step structure -- pre-flight + prompts + apt/Node 20/uv + clone-or-pull + WATIFY_APP_SECRET/API_KEY/SESSION_ENCRYPTION_KEY/OWNER_PHONE preservation on re-run + uv sync + npm build + dirs+chmod+logrotate + hardened systemd units on unix socket + Nginx with Cloudflare $http_cf_connecting_ip map + auth-endpoint limit_req + security headers + cache headers + WebSocket Upgrade + certbot --nginx + HSTS snippet + cron renewal + start banner), install/update.sh (59 lines: fetch + reset --hard + uv sync + npm build + systemctl restart with elapsed-time banner), .gitattributes forcing `*.sh text eol=lf`; bash -n clean on both | log: docs/.support/conversations/2026-05-18T201613Z-resolving_agent-iter65.md
- 2026-05-18T20:22:30Z iter66 verification_agent -> ticketing | TKT-0030 VERIFIED + committed: six proofs -- bash -n clean on both scripts, .gitattributes forces LF endings, 18 WATIFY_* env names match settings.py exactly with no deprecated WATIFY_SECRET_KEY/JWT_SECRET leaks, section-by-section walkthrough lines every numbered spec step against install.sh, update.sh has the full fetch-reset-sync-build-restart-check chain | log: docs/.support/conversations/2026-05-18T202114Z-verification_agent-iter66.md
