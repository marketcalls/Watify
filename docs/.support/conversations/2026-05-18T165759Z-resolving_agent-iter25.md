# Iteration 25 — Resolving Agent (TKT-0004)

- **Started**: 2026-05-18T16:57:59Z
- **Finished**: 2026-05-18T17:01:00Z
- **Phase entering**: resolving
- **Phase exiting**: verification
- **Active agent**: resolving_agent
- **Ticket**: TKT-0004 (P2 infra) — expand README with local-run instructions

## Files modified
- `README.md` — rewritten from the 28-line bootstrap stub into a ~100-line operational guide:
  - **Features** — what the app does (max 20 per group, random delay, schedule).
  - **Stack** — Python 3.13+ / Node 20+ / FastAPI / Next 16 / Tailwind 4 / wars 0.1.x.
  - **Prereqs** — table with versions + notes.
  - **First-time setup** — git clone, copy env files, `uv sync`, `npm install`.
  - **Run** — three ways: Windows PowerShell scripts, POSIX `make`, direct commands.
  - **Pair WhatsApp** — both web (visit `/connect`) and CLI (`make pair` / `scripts/pair.ps1`).
  - **Where data lives** — table per path with gitignore status.
  - **Troubleshooting** — Strike-SW unregister steps (closes TKT-0009 issue B), port-in-use, account-suspension link to `docs/wars.md`.
  - **Pointers** — to REQUIREMENTS / AGENTS / PIPELINE / wars.md.

- `docs/.support/PLAN.md` — I-02 marked done (TKT-0003), I-03 marked done (this ticket).

## Decisions / Notes
- README points at scripts already verified in iter24 (`scripts/dev-*.ps1`, Makefile targets); no dangling references.
- Did not embed screenshots — the loop has no image artifacts and adding them is out of scope.
- Strike-SW unregister steps live in README troubleshooting per TKT-0009 issue B's deferred resolution.

## Ticket transitions
- TKT-0004: `open` -> `inprogress` -> `resolved`.

## Next iteration
**Verification Agent** runs TKT-0004. On pass: commit `fix(TKT-0004): README expanded with local-run instructions`, push.
