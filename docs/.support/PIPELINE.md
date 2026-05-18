# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: resolving_agent
iteration: 37
last_updated: 2026-05-18T17:51:26Z
last_conversation: docs/.support/conversations/2026-05-18T175126Z-verification_agent-iter37.md
servers:
  backend_running: true
  backend_pid: 49412
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 10
  inprogress: 0
  resolved: 0
  verified: 10
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
  TKT-0012: open P2 backend RUST_LOG defaults
  TKT-0013: open P2 backend Lazy wars import + WarsNotInstalled
  TKT-0014: open P2 backend Pair-code mode alongside QR
  TKT-0015: open P2 backend Rate-limit middleware on send
  TKT-0016: open P3 backend Pair state machine paired vs ready
  TKT-0017: open P3 backend JID helpers
  TKT-0018: open P3 frontend SSE push of QR
  TKT-0019: verified P2 backend wars auto-cycle watchdog
  TKT-0020: verified P1 backend wars on_connected fallback
  TKT-0021: open P1 backend Wire encrypted wars session (0011b)
```

## Next Action
Highest-priority open: **TKT-0021** (P1 backend) -- wire the TKT-0011 infrastructure into WaSingleton. Auto-migrate `whatsapp.db` -> encrypted blob, boot from `from_bytes`, persist on `on_connected`. The live paired session is in `whatsapp.db` today; the migration will move it into `app.db` on next backend start when the operator sets `WATIFY_SESSION_ENCRYPTION_KEY`.

Recommended for iter38: `agent: resolving_agent`, ticket **TKT-0021**.

## History
- (iter0..iter35 abbreviated -- see git history)
- 2026-05-18T17:47:28Z iter36 resolving | TKT-0011 (0011a infra) shipped; TKT-0021 filed
- 2026-05-18T17:51:26Z iter37 verification_agent -> ticketing | TKT-0011 VERIFIED + committed: smoke 6/6, 8 symbols importable, wa_session table created, .env.example documented, live wars still ready | log: docs/.support/conversations/2026-05-18T175126Z-verification_agent-iter37.md
