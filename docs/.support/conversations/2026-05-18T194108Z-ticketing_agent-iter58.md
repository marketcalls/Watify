# Iteration 58 -- Ticketing Agent

- **Started**: 2026-05-18T19:41:08Z
- **Phase**: ticketing
- **Active agent**: ticketing_agent

## Plan
The previous iteration (iter57) verified the backend auth gate (TKT-0025). The user immediately observed that `localhost:3000` still renders the legacy dashboard with stale / zeroed cards, and asked why. Investigation in iter57 turned up a concrete frontend gap: `frontend/src/lib/api.ts` calls `fetch(url, {...})` without `credentials: "include"`, so the browser never sends the `watify_session` cookie cross-origin (3000 -> 8000). With the gate live, every authenticated dashboard call now silently 401s and the UI falls back to zeros.

Two things to do this iteration:

1. **File a new ticket** for the missing `credentials: "include"` in the frontend API client. This blocks the v1.1 auth experience and TKT-0026 ([[/login + /register]]) cannot succeed end-to-end without it.
2. **Standard Ticketing security pass** per AGENTS.md before queuing the next Resolving target. The pass MUST cover: hardcoded secrets, .env gitignore + ls-files, .env.example coverage, Pydantic models on handlers, CORS pinned, no `dangerouslySetInnerHTML`/`eval`, phone redaction in logs, db files not tracked.
3. **Queue TKT-0026** as the next Resolving target (P1 frontend `/login` + `/register` pages) but ONLY after the new ticket is filed and the security pass is clean.

Skipping Chrome MCP for this iteration -- iter57 already inspected the live dashboard via the user's screenshot and the cause is identified at the source. Re-opening Chrome would burn iteration budget without adding evidence.

## Actions

1. **Security pass** per AGENTS.md "Security audit pass (every Ticketing iteration)":
   - `git ls-files | grep -E "(\.env(\.|$)|\.db($|-)|whatsapp\.db|app\.db)"` (excluding `.env.example`) -> empty. No secrets or DB files tracked.
   - `backend/.env` exists + gitignored. `frontend/.env.local` exists + gitignored.
   - `.env.example` present for both: `backend/.env.example` (2260 bytes, lists all WATIFY_* vars including APP_SECRET, API_KEY, SESSION_ENCRYPTION_KEY) and `frontend/.env.local.example`.
   - CORS: `app/main.py:58 allow_origins=[settings.cors_origin]` with default `cors_origin = "http://localhost:3000"` in `settings.py:28`. No wildcards.
   - Backend bind: `settings.py:26 host = "127.0.0.1"`. Not exposed to 0.0.0.0.
   - `dangerouslySetInnerHTML` / `eval(` in `frontend/src` -> empty.
   - Raw `dict` body params on FastAPI handlers -> empty. All use Pydantic.
   - `f"SELECT..."` / `f"INSERT..."` / `f"UPDATE..."` / `f"DELETE..."` in `backend/app` -> empty.
   - Hex secret literals `= "[a-f0-9]{32,}"` in `backend/app` and `frontend/src` -> empty (outside tests).
   - Phone redaction filter active: `app/logging_setup.py:38 PhoneRedactionFilter` attached to both file and stream handlers at lines 75 and 80.
   - Hardcoded phone numbers outside test/fixture/example/smoke files -> empty.
   - Result: security pass CLEAN.

2. **Filed TKT-0034** (P1 frontend) -- `frontend/src/lib/api.ts` missing `credentials: "include"`. Evidence:
   - `grep -rn "fetch(\|axios\." frontend/src` returns exactly one hit at `frontend/src/lib/api.ts:34`. Single source of truth -- one-line fix touches every dashboard call site.
   - Backend CORS already sets `allow_credentials=True` so the gap is purely on the frontend side.
   - This blocks TKT-0026 e2e: login response will set cookies but subsequent dashboard reads still 401 without this fix.

3. **Updated PIPELINE.md**:
   - iteration 57 -> 58
   - phase ticketing -> resolving, agent ticketing_agent -> resolving_agent
   - tickets.open 13 -> 14 (TKT-0034 added)
   - ticket_index: added `TKT-0034: open P1 frontend apiFetch credentials include (blocks TKT-0026 e2e)`
   - Next Action: directs Resolving Agent to TKT-0034 first, then TKT-0026, then TKT-0030.
   - History: appended the iter58 one-liner; trimmed older entries beyond the latest three.

## Outcome
TKT-0034 filed (P1 frontend, one-line fix). Security pass clean -- no new tickets from the auth middleware ship beyond the credentials-include gap already identified. Next iteration: Resolving Agent picks TKT-0034. After that resolves and verifies, TKT-0026 (login/register UI) becomes the immediate next P1 frontend target, then TKT-0030 (install.sh).
