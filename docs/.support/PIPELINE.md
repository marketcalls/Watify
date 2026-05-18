# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: resolving_agent
iteration: 48
last_updated: 2026-05-18T18:47:57Z
last_conversation: docs/.support/conversations/2026-05-18T184757Z-verification_agent-iter48.md
servers:
  backend_running: true
  backend_pid: 37808
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 14
  inprogress: 0
  resolved: 0
  verified: 15
ticket_index:
  TKT-0001: verified P2 backend Flat error envelope
  TKT-0002: verified P1 frontend UX polish
  TKT-0003: verified P2 infra Dev helper scripts + Makefile
  TKT-0004: verified P2 infra README expanded
  TKT-0005: verified P2 backend Surface owner_phone (env seed + on_message learner)
  TKT-0006: open P3 backend Move test phone constant out of smoke_db.py
  TKT-0007: verified P2 frontend /connect auto-pair guard
  TKT-0008: open P2 frontend Global toaster
  TKT-0009: verified P2 backend Cascade-delete groups
  TKT-0010: verified P1 frontend QR pair UX countdown + dim on expiry
  TKT-0011: verified P1 backend Encrypted session infrastructure
  TKT-0012: verified P2 backend RUST_LOG defaults silence wars noise
  TKT-0013: verified P2 backend Lazy wars import + WarsNotInstalled
  TKT-0014: open P2 backend Pair-code mode alongside QR
  TKT-0015: verified P2 backend slowapi rate-limit middleware
  TKT-0016: open P3 backend Pair state machine paired vs ready
  TKT-0017: open P3 backend JID helpers
  TKT-0018: open P3 frontend SSE push of QR
  TKT-0019: verified P2 backend wars auto-cycle watchdog
  TKT-0020: verified P1 backend wars on_connected fallback
  TKT-0021: verified P1 backend Encrypted wars session wired end-to-end
  TKT-0022: open P3 frontend Job drawer cache drift
  TKT-0023: open P1 backend Single-user auth model (User + argon2)
  TKT-0024: open P1 backend Auth endpoints + JWT cookies + auth rate limits
  TKT-0025: open P1 backend Auth middleware
  TKT-0026: open P1 frontend /login + /register pages
  TKT-0027: open P2 frontend Public hero page; move dashboard to /dashboard
  TKT-0028: open P2 frontend Auth-aware TopNav
  TKT-0029: open P2 frontend Route guards
  TKT-0030: open P1 infra install/install.sh + update.sh (Ubuntu + Cloudflare + LE)
```

## Next Action
The v1.1 milestone has 4 P1 tickets at the top of the queue. Start with **TKT-0023** (P1 backend) -- the User model + argon2 + register-once helpers. It is the foundation; TKT-0024 (auth endpoints), TKT-0025 (auth middleware), TKT-0026 (login/register pages) all depend on it.

Recommended for iter49: `agent: resolving_agent`, ticket **TKT-0023**.

## History (latest only)
- 2026-05-18T18:37:10Z iter46 resolving | TKT-0005 owner_phone (env seed + on_message learner)
- 2026-05-18T18:41:55Z iter47 ticketing | v1.1 scope filed: 8 tickets TKT-0023..TKT-0030
- 2026-05-18T18:47:57Z iter48 verification_agent -> ticketing | TKT-0005 VERIFIED + committed: env-seeded WATIFY_OWNER_PHONE surfaces as redacted 91XXXXXX3210 in API; on_message learner registered at line 424 (live echo proof deferred to natural operation) | log: docs/.support/conversations/2026-05-18T184757Z-verification_agent-iter48.md
