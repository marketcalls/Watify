# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: ticketing_agent
iteration: 57
last_updated: 2026-05-18T19:36:30Z
last_conversation: docs/.support/conversations/2026-05-18T193508Z-verification_agent-iter57.md
servers:
  backend_running: true
  backend_pid: 20252
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 13
  inprogress: 0
  resolved: 0
  verified: 19
ticket_index:
  TKT-0024: verified P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: verified P1 backend Auth middleware
  TKT-0026: open P1 frontend /login + /register pages
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
**Ticketing Agent** runs the standard re-triage + security pass per AGENTS.md, then queues the next Resolving target. The remaining P1 milestone tickets (priority order): **TKT-0026** (frontend /login + /register pages -- now unblocked because the backend auth gate is verified), then **TKT-0030** (install/install.sh + update.sh for Ubuntu + Cloudflare + Let's Encrypt). The Ticketing Agent should also confirm no new tickets are needed from the auth middleware ship (no leaks, no missing controls). Frontend `/api/auth/me` cookie-auth in the dashboard `useUser()` hook should still work because login now sets `watify_session`; spot-check by hitting `http://localhost:3000` and watching the network panel.

## History (latest only)
- 2026-05-18T19:22:23Z iter55 verification_agent -> ticketing | TKT-0024 VERIFIED + committed: cookies httpOnly+SameSite=lax, typ access/refresh differentiation honored, 503 auth_not_configured on all 5 when app_secret unset, non-auth endpoints unaffected | log: docs/.support/conversations/2026-05-18T192223Z-verification_agent-iter55.md
- 2026-05-18T19:45:00Z iter56 resolving_agent -> verification | TKT-0025 RESOLVED: app/auth_middleware.py (Starlette BaseHTTPMiddleware) + main.py wiring AFTER CORS so it sits outermost; bypass matrix non-/api, app_secret-empty (dev), OPTIONS, allowlist; 401 flat envelope; smoke passed in both configured + dev modes; persisted fresh app_secret + api_key in backend/.env until install.sh ships | log: docs/.support/conversations/2026-05-18T192734Z-resolving_agent-iter56.md
- 2026-05-18T19:36:30Z iter57 verification_agent -> ticketing | TKT-0025 VERIFIED + committed: (a) health 200 + fingerprint 6cf4a507, (b) /api/groups+jobs+wa/state no-cookie 401, (c) login 200 + both httpOnly cookies, (d) protected with cookie 200, (e) bad cookie 401, (f) 10x rapid no-cookie hits all 401 never 429 -> outermost confirmed; bonus: refresh-token-as-access rejected via typ discriminator; dev-mode: /api/groups 200 bypass, /api/auth/login 503 | log: docs/.support/conversations/2026-05-18T193508Z-verification_agent-iter57.md
