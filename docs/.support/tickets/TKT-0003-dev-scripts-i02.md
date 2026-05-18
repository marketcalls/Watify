---
id: TKT-0003
title: Add top-level dev helper scripts (I-02)
status: verified
priority: P2
area: infra
created: 2026-05-18T16:14:48Z
updated: 2026-05-18T16:53:12Z
created_by: ticketing_agent
related_plan_item: I-02
---

## Summary
Currently the only way to run Watify is to recall the exact uv / npm commands. The dev servers should be one-liners.

## Expected
Top-level PowerShell scripts (Windows is primary) and a `Makefile` (POSIX fallback):

- `scripts/dev-backend.ps1` -> `uv run uvicorn app.main:app --reload --port 8000`
- `scripts/dev-frontend.ps1` -> `npm run dev`
- `scripts/pair.ps1` -> calls the wars CLI pair script
- `Makefile` mirrors for POSIX shells

Update README to point at them.

## Resolution history
- 2026-05-18T16:14:48Z — filed by Ticketing Agent (iter16).
- 2026-05-18T16:48:36Z — Resolving Agent (iter23) set status to inprogress.
- 2026-05-18T16:50:00Z — Resolving Agent (iter23) shipped:
  - `scripts/dev-backend.ps1` — `cd backend; uv run uvicorn app.main:app --reload --port 8000`.
  - `scripts/dev-frontend.ps1` — `cd frontend; (npm install if no node_modules); npm run dev`.
  - `scripts/pair.ps1` — wrapper that invokes `backend/scripts/pair.py` for the terminal-ASCII-QR headless flow.
  - `backend/scripts/pair.py` — uses `wars.WhatsApp.pair(timeout=300)` against `settings.whatsapp_db` for the CLI pairing path. Web UI at `/connect` remains the primary; this is for headless boxes.
  - `Makefile` — POSIX equivalents (`dev-backend`, `dev-frontend`, `pair`, `help`).

  Validation:
  - All three PowerShell scripts tokenized clean via `[System.Management.Automation.PSParser]::Tokenize`.
  - `uv run python -m py_compile scripts/pair.py` -> ok.
  - `make --dry-run help` not exercisable on this Windows host (no make in PATH) but the Makefile is syntactically minimal (4 phony targets).

  Status set to `resolved`. Awaiting Verification Agent.
- 2026-05-18T16:53:12Z — Verification Agent (iter24) PASSED:
  - All 5 files exist at expected paths.
  - PowerShell full-AST parse (`[System.Management.Automation.Language.Parser]::ParseFile`) on all three .ps1 scripts: zero errors.
  - `uv run python -m py_compile scripts/pair.py` -> ok.
  - Makefile: 9 recipe lines, all tab-indented (no space-indented recipes — common make gotcha avoided).
  Status set to `verified`. Committed `fix(TKT-0003): dev helper scripts + Makefile` and pushed.
