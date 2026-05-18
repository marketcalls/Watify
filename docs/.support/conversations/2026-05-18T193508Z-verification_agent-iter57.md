# Iteration 57 -- Verification Agent (TKT-0025)

- **Started**: 2026-05-18T19:35:08Z
- **Phase**: verification
- **Active agent**: verification_agent
- **Ticket**: TKT-0025 (P1 backend, resolved) -- auth middleware

## Spec to reproduce (from PIPELINE.md next-action)

Configured mode:
- a. `/api/health` 200 + non-null `app_fingerprint`
- b. `/api/groups`, `/api/jobs`, `/api/wa/state` without cookie -> 401 `auth_required`
- c. login -> 200 + httpOnly cookies
- d. protected paths with cookie -> 200
- e. malformed cookie -> 401 `session token invalid or expired`
- f. AuthMiddleware OUTERMOST so 429 (slowapi) is unreachable without auth

Dev mode (`WATIFY_APP_SECRET` unset):
- `/api/groups` 200 (bypass preserved)
- `/api/auth/login` 503 `auth_not_configured`

## Plan
1. Independently inspect `backend/app/auth_middleware.py` + `backend/app/main.py` to confirm the wiring, bypass matrix, and 401 envelope shape match the spec (NOT just trust the resolving log).
2. Run smoke against the already-running backend (configured mode, fingerprint `6cf4a507` from iter56). Reset auth lockout first so rate-limit history from iter56 doesn't interfere.
3. Stop, unset `WATIFY_APP_SECRET`, restart, run dev-mode smoke, then restart with secrets restored.
4. Outermost-middleware check: a 401 must come back BEFORE slowapi's 429 counter ticks. Verify with rapid no-cookie hits to `/api/auth/login`.
5. Stage `backend/app/auth_middleware.py`, `backend/app/main.py`, ticket, conversation log, and the PIPELINE.md update; commit `fix(TKT-0025): auth middleware -- protect /api/* (allowlist auth + health)`; push to origin/main.
6. Do NOT stage `backend/.env`, `app.db`, `whatsapp.db*`, `docs/.support/logs/*`.

## Actions

1. Read `backend/app/auth_middleware.py` and `backend/app/main.py` directly. Confirmed: bypass matrix order is non-/api -> app_secret-empty -> OPTIONS -> allowlist; 401 envelope `{error:"auth_required", detail:...}` matches the TKT-0001 flat shape; `decode_access` is used (typ=access enforced); `AuthMiddleware` is registered AFTER `CORSMiddleware` in `main.py` so it sits OUTERMOST in the Starlette stack.
2. Reset `app.auth_lockout` so iter56 fail-counts don't pollute the smoke.
3. **Configured-mode smoke** against the already-running backend (pid 18308, fingerprint `6cf4a507`):
   - a. `GET /api/health` -> 200 with `app_fingerprint=6cf4a507`. PASS.
   - b. `GET /api/groups`, `/api/jobs`, `/api/wa/state` without cookie -> 401 `auth_required missing watify_session cookie`. PASS x3.
   - e. `GET /api/groups` with `Cookie: watify_session=not.a.valid.jwt` -> 401 `session token invalid or expired`. PASS.
   - c. Waited 60s past slowapi /login window; `POST /api/auth/login` admin/twelve-chars-minimum -> 200 + Set-Cookie for both `watify_session` (access JWT, typ=access, 15-min exp) and `watify_refresh` (refresh JWT, typ=refresh, 7-day exp). PASS.
   - d. `GET /api/groups` and `GET /api/jobs` with the jar -> 200 each. PASS.
   - Bonus: planted the `watify_refresh` token into the `watify_session` cookie slot -> 401. PASS. The typ discriminator + composite-key signing for refresh tokens means a refresh credential can never authenticate a request.
4. **Outermost-middleware test** (f): 10 rapid no-cookie hits to `/api/groups` -> `401 401 401 401 401 401 401 401 401 401`. Then 10 to `/api/jobs` POST -> `401 401 401 401 401 401 401 401 401 401`. The slowapi 429 path is unreachable without auth, so 429 cannot leak token validity. PASS.
5. **Dev-mode smoke**: stopped backend pid 18308 + the lingering listener; restarted with `WATIFY_APP_SECRET=""` overriding .env. `app_fingerprint=null`. `/api/groups` no-cookie -> 200 (dev bypass preserved). `/api/auth/login` -> 503 `auth_not_configured`. PASS.
6. Restored backend in configured mode (no env override; .env carries the new app_secret/api_key). New pid 20252, fingerprint `6cf4a507`. Wrote pid to `docs/.support/logs/backend.pid`.
7. Flipped TKT-0025 status `resolved` -> `verified`. Appended verification entry to Resolution history.
8. Updated `PIPELINE.md`: iteration=57, phase=ticketing, agent=ticketing_agent, ticket counts open=13 resolved=0 verified=19, server pid bumped.
9. Stage + commit + push (next step).

## Outcome
TKT-0025 VERIFIED. The auth gate is correct, outermost, dev-mode safe, and refresh-token-resistant. Commit `fix(TKT-0025): auth middleware -- protect /api/* (allowlist auth + health)` to follow. Next iteration: Ticketing Agent for re-triage (no `open` tickets are blocked by missing auth anymore; TKT-0026 frontend login UI is the next P1 implementation, but per loop convention we route through Ticketing first to do the security pass and pick the next Resolving target).

