# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: resolving_agent
iteration: 41
last_updated: 2026-05-18T18:12:28Z
last_conversation: docs/.support/conversations/2026-05-18T181228Z-verification_agent-iter41.md
servers:
  backend_running: true
  backend_pid: 37772
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 8
  inprogress: 0
  resolved: 0
  verified: 12
ticket_index:
  TKT-0001: verified P2 backend Flat error envelope
  TKT-0002: verified P1 frontend UX polish
  TKT-0003: verified P2 infra Dev helper scripts + Makefile
  TKT-0004: verified P2 infra README expanded
  TKT-0005: open P2 backend Surface owner_phone after wars pairing
  TKT-0006: open P3 backend Move test phone constant out of smoke_db.py
  TKT-0007: verified P2 frontend /connect auto-pair guard
  TKT-0008: open P2 frontend Global toaster
  TKT-0009: verified P2 backend Cascade-delete groups
  TKT-0010: verified P1 frontend QR pair UX countdown + dim on expiry
  TKT-0011: verified P1 backend Encrypted session infrastructure
  TKT-0012: verified P2 backend RUST_LOG defaults silence wars noise
  TKT-0013: open P2 backend Lazy wars import + WarsNotInstalled
  TKT-0014: open P2 backend Pair-code mode alongside QR
  TKT-0015: open P2 backend Rate-limit middleware on send
  TKT-0016: open P3 backend Pair state machine paired vs ready
  TKT-0017: open P3 backend JID helpers
  TKT-0018: open P3 frontend SSE push of QR
  TKT-0019: verified P2 backend wars auto-cycle watchdog
  TKT-0020: verified P1 backend wars on_connected fallback
  TKT-0021: verified P1 backend Encrypted wars session wired end-to-end
```

## Next Action
8 open tickets, all P2 or P3. Recommended order:
1. **TKT-0013** (P2 backend) -- lazy `_import_wars()` + `WarsNotInstalled` sentinel. Small refactor; backend boots without wars wheel.
2. **TKT-0005** (P2 backend) -- surface owner_phone after pair.
3. **TKT-0015** (P2 backend) -- slowapi rate limit.
4. **TKT-0014** (P2 backend) -- pair-code mode.
5. **TKT-0008** (P2 frontend) -- global Toaster.
6. **TKT-0016 / TKT-0017 / TKT-0018 / TKT-0006** -- P3 polish.

Recommended for iter42: `agent: resolving_agent`, ticket **TKT-0013** (lazy wars import).

## History (latest only)
- 2026-05-18T18:01:04Z iter39 verification | TKT-0021 VERIFIED + committed 8b200ff
- 2026-05-18T18:07:43Z iter40 resolving | TKT-0012 RUST_LOG setdefault shipped
- 2026-05-18T18:12:28Z iter41 verification_agent -> ticketing | TKT-0012 VERIFIED + committed: 0 noisy log matches after restart + 10s idle; setdefault preserves operator RUST_LOG=warn; default writes silencing string | log: docs/.support/conversations/2026-05-18T181228Z-verification_agent-iter41.md
```
