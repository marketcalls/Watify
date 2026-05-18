# Watify Pipeline State

This file is the single source of truth for "what runs next". Each loop iteration reads this, executes one chunk as the named agent, then updates this file.

```yaml
phase: ticketing
agent: resolving_agent
iteration: 39
last_updated: 2026-05-18T18:01:04Z
last_conversation: docs/.support/conversations/2026-05-18T180104Z-verification_agent-iter39.md
servers:
  backend_running: true
  backend_pid: 5036
  backend_url: http://localhost:8000
  frontend_running: true
  frontend_pid: 42204
  frontend_url: http://localhost:3000
tickets:
  open: 9
  inprogress: 0
  resolved: 0
  verified: 11
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
  TKT-0021: verified P1 backend Encrypted wars session wired end-to-end
```

## Next Action
9 open tickets remain, no P1 left. Suggested order:
1. **TKT-0012** (P2 backend) -- RUST_LOG defaults silence wars protocol noise. One-line `os.environ.setdefault(...)` before the wars import.
2. **TKT-0013** (P2 backend) -- lazy `_import_wars()` + `WarsNotInstalled` sentinel. Small refactor.
3. TKT-0019-style auto-cycle / TKT-0008 toaster / TKT-0014 pair-code / TKT-0015 rate limit / TKT-0005 owner_phone -- bigger features.
4. TKT-0016 / TKT-0017 / TKT-0018 / TKT-0006 -- P3 polish.

Recommended for iter40: `agent: resolving_agent`, ticket **TKT-0012** (RUST_LOG suppress).

## History (latest only -- prior iterations in git history)
- 2026-05-18T17:51:26Z iter37 verification | TKT-0011 VERIFIED + committed 90e3ca8
- 2026-05-18T17:56:44Z iter38 resolving | TKT-0021 wiring shipped
- 2026-05-18T18:01:04Z iter39 verification_agent -> ticketing | TKT-0021 VERIFIED end-to-end after fixing 2 in-field bugs (cross-thread persist + Windows file-lock cleanup): migration moved 499712B session from whatsapp.db to encrypted WaSession blob; second boot reads from blob and sweeps stale files; whatsapp.db family is now absent | log: docs/.support/conversations/2026-05-18T180104Z-verification_agent-iter39.md
