# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: resolving_agent
iteration: 55
last_updated: 2026-05-18T19:22:23Z
last_conversation: docs/.support/conversations/2026-05-18T192223Z-verification_agent-iter55.md
servers:
  backend_running: true
  backend_pid: 17608
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 14
  inprogress: 0
  resolved: 0
  verified: 18
ticket_index:
  TKT-0024: verified P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: open P1 backend Auth middleware
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
**Resolving Agent** picks **TKT-0025** (P1 backend) -- auth middleware. Promote the temp inline cookie-auth in `/api/auth/me` to a proper Starlette `BaseHTTPMiddleware` that runs BEFORE slowapi, enforces auth on every `/api/*` except the allowlist (`/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, OPTIONS preflight), and returns 401 with the flat envelope on failure.

## History (latest only)
- 2026-05-18T19:10:00Z iter53 verification | TKT-0031 VERIFIED + committed 915d305
- 2026-05-18T19:14:51Z iter54 resolving | TKT-0024 auth endpoints
- 2026-05-18T19:22:23Z iter55 verification_agent -> ticketing | TKT-0024 VERIFIED + committed: cookies httpOnly+SameSite=lax, typ access/refresh differentiation honored, 503 auth_not_configured on all 5 when app_secret unset, non-auth endpoints unaffected | log: docs/.support/conversations/2026-05-18T192223Z-verification_agent-iter55.md
