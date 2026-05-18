# Iteration 23 — Resolving Agent (TKT-0003)

- **Started**: 2026-05-18T16:48:36Z
- **Finished**: 2026-05-18T16:51:00Z
- **Phase entering**: resolving
- **Phase exiting**: verification
- **Active agent**: resolving_agent
- **Ticket**: TKT-0003 (P2 infra) — dev helper scripts (I-02)

## Files created
- `scripts/dev-backend.ps1` — PowerShell wrapper that cd's into `backend/` and runs `uv run uvicorn app.main:app --reload --port 8000`. Verifies the backend dir exists; errors out with a clear message otherwise. `$ErrorActionPreference = "Stop"`.
- `scripts/dev-frontend.ps1` — same shape for the Next.js dev server. Auto-runs `npm install --no-audit --no-fund` when `node_modules/` is missing.
- `scripts/pair.ps1` — thin shim that calls `backend/scripts/pair.py`. Documents both pairing paths (web UI vs CLI) in its preamble comment.
- `backend/scripts/pair.py` — minimal Python script using `wars.WhatsApp(settings.whatsapp_db).pair(timeout=300)`. Per wars.md, `pair()` falls back to ASCII QR in a terminal. Catches `TimeoutError` and `KeyboardInterrupt` with proper exit codes.
- `Makefile` — POSIX equivalents: `dev-backend`, `dev-frontend`, `pair`, plus a `help` target listing them.

## Validation
- PowerShell: tokenized all three .ps1 files via `[System.Management.Automation.PSParser]::Tokenize` -> all `ok`.
- Python: `uv run python -m py_compile scripts/pair.py` -> ok.
- Makefile: `make --dry-run help` not exercisable on this Windows host (no `make` in PATH). The Makefile is 4 phony targets, syntactically minimal.

## Decisions / Notes
- Did NOT actually run `dev-backend.ps1` end-to-end because the backend is already up on :8000 (pid 35788); a second `uvicorn` would hit the port-bind error path we already triaged in iter6.
- Did NOT run `pair.ps1` because that would mutate the wars session state mid-iteration. Verification Agent can do a dry-run of the preamble safely.
- README pointers to these scripts are TKT-0004's scope, not this one.

## Ticket transition
- TKT-0003: `open` -> `inprogress` -> `resolved`.

## Next iteration
**Verification Agent** runs TKT-0003. On pass: commit `fix(TKT-0003): dev helper scripts + Makefile`, push.
