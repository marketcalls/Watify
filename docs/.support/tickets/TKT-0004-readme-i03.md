---
id: TKT-0004
title: Expand README with local-run instructions (I-03)
status: verified
priority: P2
area: infra
created: 2026-05-18T16:14:48Z
updated: 2026-05-18T17:02:44Z
created_by: ticketing_agent
related_plan_item: I-03
---

## Summary
`README.md` is bootstrap-era; should cover:
- Prereqs (Python 3.13+ via `uv`, Node 20+).
- Setup: `cp backend/.env.example backend/.env`, `uv sync`, `npm install`.
- Run: backend + frontend commands (or the scripts from TKT-0003 once they land).
- Pair flow: visit /connect, scan QR.
- Where data lives: `backend/app.db`, `backend/whatsapp.db`, `docs/.support/logs/`.
- Pointer to `docs/.support/REQUIREMENTS.md` for the contract and `docs/.support/AGENTS.md` for how the loop builds the app.

## Resolution history
- 2026-05-18T16:14:48Z — filed by Ticketing Agent (iter16).
- 2026-05-18T16:57:59Z — Resolving Agent (iter25) set status to inprogress.
- 2026-05-18T17:00:00Z — Resolving Agent (iter25) rewrote `README.md` from the bootstrap stub into a full local-run guide:
  - Features overview + Stack + Prereqs table.
  - First-time setup (clone, `cp .env.example .env`, `uv sync`, `npm install`).
  - Run section showing Windows (PowerShell scripts from TKT-0003), POSIX (Makefile targets), and direct commands.
  - Pair WhatsApp section (web + headless CLI).
  - Where data lives table (gitignore status per file).
  - Troubleshooting section folding in TKT-0009 issue B's Chrome service-worker unregister steps, plus port-in-use and account-suspension notes (links to wars.md risk note).
  - Pointers to REQUIREMENTS / AGENTS / PIPELINE / wars.md.

  PLAN.md I-02 and I-03 marked done (I-02 ships in TKT-0003, I-03 in this ticket).

  Status set to `resolved`; awaiting Verification Agent.
- 2026-05-18T17:02:44Z — Verification Agent (iter26) PASSED:
  - All 10 required headings present: `# Watify`, `## Features`, `## Stack`, `## Prereqs`, `## First-time setup`, `## Run`, `## Pair WhatsApp`, `## Where data lives`, `## Troubleshooting`, `## Pointers`. Total 4805 chars.
  - All 7 referenced paths exist (`scripts/dev-backend.ps1`, `scripts/dev-frontend.ps1`, `scripts/pair.ps1`, `backend/scripts/pair.py`, `Makefile`, `backend/.env.example`, `frontend/.env.local.example`).
  - Grep for phone-like (`\+?[0-9]{8,15}`) or secret-like (`sk_*`, `api_key=...`) substrings: zero matches.
  Status set to `verified`. Committed `fix(TKT-0004): README expanded with local-run instructions` and pushed.
