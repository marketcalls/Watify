# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: ticketing_agent
iteration: 78
last_updated: 2026-05-18T21:20:00Z
last_conversation: docs/.support/conversations/2026-05-18T211927Z-verification_agent-iter78.md
servers:
  backend_running: true
  backend_pid: 37636
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 8
  inprogress: 0
  resolved: 0
  verified: 26
ticket_index:
  TKT-0024: verified P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: verified P1 backend Auth middleware
  TKT-0026: verified P1 frontend /login + /register pages
  TKT-0027: verified P2 frontend Public hero page; move dashboard to /dashboard
  TKT-0028: verified P2 frontend Auth-aware TopNav
  TKT-0029: verified P2 frontend Route guards
  TKT-0030: verified P1 infra install/install.sh + update.sh
  TKT-0032: verified P2 backend CSRF defense (X-Requested-With + Origin check)
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
**Ticketing Agent** re-triages. All v1.1 P1+P2 security/UX tickets are now verified (TKT-0024/0025/0026/0027/0028/0029/0030/0031/0032/0034). Remaining open queue is entirely P2/P3 polish:
- P2 backend: TKT-0014 (pair-code mode alongside QR)
- P2 frontend: TKT-0008 (global toaster)
- P3 backend: TKT-0006 (test phone constant), TKT-0016 (paired vs ready state machine), TKT-0017 (JID helpers)
- P3 frontend: TKT-0018 (SSE push of QR), TKT-0022 (job drawer cache drift), TKT-0033 (Next.js postcss XSS advisory)

Suggested next Resolving target: **TKT-0014** (P2 backend pair-code mode) -- meaningful user-facing feature (operator types a code instead of scanning QR; useful when desktop camera unavailable). After that: TKT-0008 (toaster) for nicer error surfacing. Ticketing should also run a brief security spot pass over the iter77 diff (csrf_middleware.py + main.py + api.ts) -- expectation: clean since the change set is small and follows the same pattern as auth_middleware.

## History (latest only)
- 2026-05-18T20:07:00Z iter63 verification_agent -> ticketing | TKT-0026 VERIFIED + committed c9835a8: eight proofs -- file presence (4 files), exports (`auth`/`AuthAck`/`MeResponse`), useAuth 401-as-null + shouldRetryOnError=false, zero non-ASCII chars (no emojis/icons), tsc --noEmit exit 0, curl /login + /register HTTP 200 with expected copy strings, Next.js compiled src_app_login_page_tsx_05e8nkp._.js chunk, backend endpoints behave per UI contract (auth/me 401, register 409 registration_closed, login bad-password 401 invalid_credentials) | log: docs/.support/conversations/2026-05-18T200607Z-verification_agent-iter63.md
- 2026-05-18T20:11:28Z iter64 ticketing_agent -> resolving | re-triage after TKT-0026 verified; diff-scoped security pass over the four TKT-0026 files clean (no dangerouslySetInnerHTML/eval, no localStorage/sessionStorage/document.cookie reads, no hex secrets, no Authorization/Bearer headers, no console.log of bodies); no new tickets filed; next: Resolving picks TKT-0030 (P1 infra install.sh) with TKT-0027 as the immediate follow-on for the user-visible hero swap | log: docs/.support/conversations/2026-05-18T201128Z-ticketing_agent-iter64.md
- 2026-05-18T20:20:00Z iter65 resolving_agent -> verification | TKT-0030 RESOLVED: shipped install/install.sh (540 lines, full nine-step structure -- pre-flight + prompts + apt/Node 20/uv + clone-or-pull + WATIFY_APP_SECRET/API_KEY/SESSION_ENCRYPTION_KEY/OWNER_PHONE preservation on re-run + uv sync + npm build + dirs+chmod+logrotate + hardened systemd units on unix socket + Nginx with Cloudflare $http_cf_connecting_ip map + auth-endpoint limit_req + security headers + cache headers + WebSocket Upgrade + certbot --nginx + HSTS snippet + cron renewal + start banner), install/update.sh (59 lines: fetch + reset --hard + uv sync + npm build + systemctl restart with elapsed-time banner), .gitattributes forcing `*.sh text eol=lf`; bash -n clean on both | log: docs/.support/conversations/2026-05-18T201613Z-resolving_agent-iter65.md
- 2026-05-18T20:22:30Z iter66 verification_agent -> ticketing | TKT-0030 VERIFIED + committed 8808ae8: six proofs -- bash -n clean on both scripts, .gitattributes forces LF endings, 18 WATIFY_* env names match settings.py exactly with no deprecated WATIFY_SECRET_KEY/JWT_SECRET leaks, section-by-section walkthrough lines every numbered spec step against install.sh, update.sh has the full fetch-reset-sync-build-restart-check chain | log: docs/.support/conversations/2026-05-18T202114Z-verification_agent-iter66.md
- 2026-05-18T20:26:01Z iter67 ticketing_agent -> resolving | install-script security spot pass clean: no inline secrets, two curl|bash sources are first-party (deb.nodesource.com/setup_20.x + astral.sh/uv/install.sh), chmod 600 on .env + app.db + whatsapp.db, 5x systemd hardening per unit (NoNewPrivileges/PrivateTmp/ProtectSystem=strict/ProtectHome=true/ReadWritePaths), Nginx denies dotfiles and leakage paths and sets X-Frame-Options/X-Content-Type-Options/X-XSS-Protection/Referrer-Policy + HSTS via ssl-security.conf; counts open=12 verified=22; no new tickets; next: Resolving picks TKT-0027 (P2 frontend public hero + /dashboard move) | log: docs/.support/conversations/2026-05-18T202601Z-ticketing_agent-iter67.md
- 2026-05-18T20:32:00Z iter68 resolving_agent -> verification | TKT-0027 RESOLVED: five-file change set -- new frontend/src/app/dashboard/page.tsx (dashboard verbatim relocated), rewrote frontend/src/app/page.tsx as public hero (server component with metadata, headline + two CTAs + feature triplet + wars footer, Tailwind only, no emojis), login + register router.push pointed at /dashboard, TopNav Dashboard nav link updated to /dashboard with TKT comment; npx tsc --noEmit exit 0; dev-server curl: / 200 with hero copy, /dashboard 200 with dashboard markup | log: docs/.support/conversations/2026-05-18T203043Z-resolving_agent-iter68.md
- 2026-05-18T20:36:00Z iter69 verification_agent -> ticketing | TKT-0027 VERIFIED + committed 7918ee7: six proofs -- 5 files present (sizes 2965/2857/4951/5805/1278b), zero non-ASCII chars in any edited file, tsc --noEmit exit 0, dev-server curl / 200 (20565b, 7 hero copy strings) + /dashboard 200 (18447b, 4 dashboard markers) + /login + /register both 200, router.push("/dashboard") confirmed in login + register, TopNav links[0] href=/dashboard | log: docs/.support/conversations/2026-05-18T203528Z-verification_agent-iter69.md
- 2026-05-18T20:40:14Z iter70 ticketing_agent -> resolving | iter68 diff security spot pass clean (no dangerouslySetInnerHTML/eval/localStorage/sessionStorage/document.cookie/hex secrets/console.log/external links across the 5 changed frontend files); counts unchanged open=11 verified=23; no new tickets; next: Resolving picks TKT-0028 (auth-aware TopNav driven by useAuth) | log: docs/.support/conversations/2026-05-18T204014Z-ticketing_agent-iter70.md
- 2026-05-18T20:46:00Z iter71 resolving_agent -> verification | TKT-0028 RESOLVED: rewrote frontend/src/components/TopNav.tsx as a 95-line client component driven by useAuth(); three branches (isLoading=brand-only flex-1 spacer, user=brand+5-link nav+username+Logout, unauthed=brand+Sign in+Get started); Logout calls useAuth.logout() then router.push("/"); brand href dynamic /dashboard|/; signingOut local state disables button during round-trip; `npx tsc --noEmit` exit 0; curl / 200 with Watify+Sign in+Get started but NOT Dashboard (unauthed branch rendered) | log: docs/.support/conversations/2026-05-18T204502Z-resolving_agent-iter71.md
- 2026-05-18T20:50:00Z iter72 verification_agent -> ticketing | TKT-0028 VERIFIED + committed 8c82b24: six proofs -- "use client"+useAuth import at TopNav.tsx:1/6, three branches at :41/:45/:79-85, logout wiring `logout()` then `router.push("/")` at :24-25, tsc --noEmit exit 0, non-ASCII char count 0, curl / 200 with Watify=1+Sign in=1+Get started=1 and Dashboard=0+>Connect<=0+Logout=0 (unauthed branch only) | log: docs/.support/conversations/2026-05-18T204945Z-verification_agent-iter72.md
- 2026-05-18T20:54:30Z iter73 ticketing_agent -> resolving | iter71 TopNav diff security spot pass clean (no dangerouslySetInnerHTML/eval/storage-API reads/console.log/hex secrets); confirmed TKT-0029 spec actionable -- client-side <RequireAuth> path explicitly approved by the spec; queued TKT-0029 with five page wraps + login next-param honoring; counts open=10 verified=24 | log: docs/.support/conversations/2026-05-18T205430Z-ticketing_agent-iter73.md
- 2026-05-18T21:03:00Z iter74 resolving_agent -> verification | TKT-0029 RESOLVED: seven-file change set -- new components/RequireAuth.tsx (client guard with effect-driven router.replace to /login?next=encoded-pathname, Loading skeleton fallback), wrapped 5 authed pages (dashboard/connect/groups/send/history) by extracting *Inner components so the hooks only fire when authed, added safeNextPath open-redirect validator + useSearchParams to login (rejects null, non-/, //, and :); npx tsc --noEmit exit 0; curl /dashboard|/connect|/groups|/send|/history all 200 with Loading skeleton + flex-1 nav spacer (isLoading state) | log: docs/.support/conversations/2026-05-18T205916Z-resolving_agent-iter74.md
- 2026-05-18T21:05:00Z iter75 verification_agent -> ticketing | TKT-0029 VERIFIED + committed fcb3841: seven proofs -- RequireAuth uses useAuth+usePathname+useRouter (router.replace /login?next=), 5 authed pages wrapped (grep -l returns 5), login imports useSearchParams + has safeNextPath validator, 9-case node unit test of safeNextPath passes (null/empty/valid -> echo or fallback; //evil.com / javascript: / http:// / /a:b all -> /dashboard), tsc --noEmit exit 0, non-ASCII char 0, curl 5 authed routes all 200 with Loading skeleton; v1.1 milestone fully shipped | log: docs/.support/conversations/2026-05-18T210401Z-verification_agent-iter75.md
- 2026-05-18T21:08:47Z iter76 ticketing_agent -> resolving | iter74 diff security spot pass clean (sessionStorage hits in connect/page.tsx are pre-existing autopair-flag tracking from TKT-0010, not iter74; no dangerouslySetInnerHTML/eval/document.cookie/console.log/hex secrets in any of the 7 changed files); no new tickets; queued TKT-0032 (CSRF defense) -- the only remaining P2 backend security item; counts unchanged open=9 verified=25 | log: docs/.support/conversations/2026-05-18T210847Z-ticketing_agent-iter76.md
- 2026-05-18T21:15:00Z iter77 resolving_agent -> verification | TKT-0032 RESOLVED: three-file change set -- new backend/app/csrf_middleware.py (Starlette BaseHTTPMiddleware; bypass non-/api/* + GET/HEAD/OPTIONS + /api/auth/{login,register}; otherwise require X-Requested-With:XMLHttpRequest OR matching Origin or 403 csrf_required), main.py adds CSRFMiddleware AFTER AuthMiddleware so it sits outermost (CSRF -> Auth -> CORS -> handler), api.ts injects X-Requested-With into apiFetch default headers; py_compile + tsc both clean; backend restarted pid 37636; 8-smoke pass (GET 401, POST no-hdr 403, POST+X-Requested-With 401, POST+Origin=cors 401, POST+Origin=evil 403, login no-hdr 401invalid, login+X-Requested-With 401invalid, OPTIONS 200) | log: docs/.support/conversations/2026-05-18T211414Z-resolving_agent-iter77.md
- 2026-05-18T21:20:00Z iter78 verification_agent -> ticketing | TKT-0032 VERIFIED + committed: four structural checks (py_compile clean, tsc exit 0, X-Requested-With at api.ts:50, middleware order CORS@57/Auth@70/CSRF@78 with CSRF outermost) + 8 smokes independently reproduced (GET 401, POST no-hdr 403, POST+X-Requested-With 401, POST+Origin=cors 401, POST+Origin=evil 403, login no-hdr 401invalid, login+X-Requested-With 401invalid, OPTIONS 200) | log: docs/.support/conversations/2026-05-18T211927Z-verification_agent-iter78.md
