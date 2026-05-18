# Iteration 56 — Resolving Agent (TKT-0025)

- **Started**: 2026-05-18T19:27:34Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0025 (P1 backend) -- auth middleware

## Plan
1. Mark TKT-0025 `inprogress`.
2. Create `app/auth_middleware.py` -- Starlette `BaseHTTPMiddleware`:
   - Non-`/api/*` paths -> bypass.
   - `settings.app_secret` empty (dev/unconfigured) -> bypass (preserve current dev UX).
   - `OPTIONS` method (CORS preflight) -> bypass.
   - Allowlist: `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh` -> bypass.
   - Everything else under `/api/*` -> require valid `watify_session` cookie; decode via `decode_access`; 401 with flat envelope on missing / invalid / expired.
3. Register in `main.py` AFTER CORS so AuthMiddleware is outermost (runs first on request).
4. Smoke:
   - With `app_secret` set: GET `/api/groups` no-cookie -> 401; login -> 200 + cookie; GET `/api/groups` with cookie -> 200; `/api/health` -> 200 either way.
   - Without `app_secret`: GET `/api/groups` -> 200 (dev bypass preserved).
5. Mark resolved.

## Note on slowapi ordering
slowapi is NOT a middleware -- it's a route-decorator + exception handler. Decorators wrap the handler, so they run INSIDE all middleware. Therefore AuthMiddleware naturally runs BEFORE slowapi as REQUIREMENTS A4 requires (so 429 never leaks token validity).

## Actions

1. Read `TKT-0025-auth-middleware.md`. Flipped status `inprogress`.
2. Created `backend/app/auth_middleware.py` per the bypass matrix above.
3. Edited `backend/app/main.py`: imported `AuthMiddleware`, registered via `app.add_middleware(AuthMiddleware)` AFTER `CORSMiddleware`. Added a code comment explaining the FastAPI reverse-order rule and why slowapi naturally sits inside the gate.
4. `py_compile`-validated both files; restarted backend with `WATIFY_APP_SECRET` injected.
5. Smoke (configured mode) -- all green:
   - `/api/health` 200
   - `/api/groups` no-cookie 401 with `{"error":"auth_required","detail":"missing watify_session cookie"}`
   - `/api/jobs` no-cookie 401
   - `/api/wa/state` no-cookie 401
   - `/api/auth/login` admin/twelve-chars-minimum -> 200 + httpOnly cookies (`watify_session`, `watify_refresh`)
   - `/api/groups` with cookie -> 200, returns the existing `test` group
   - `/api/jobs` with cookie -> 200, returns full history
   - Bad cookie `not.a.valid.jwt` -> 401 with `session token invalid or expired`
6. Smoke (dev mode, `WATIFY_APP_SECRET` unset):
   - `/api/health` -> 200 with `app_fingerprint=null`
   - `/api/groups` no-cookie -> 200 (dev bypass preserved)
   - `/api/auth/login` -> 503 `auth_not_configured`
7. Discovered `.env` was missing `WATIFY_APP_SECRET` / `WATIFY_API_KEY` -- iter55's smoke had injected them via `$env:`. Generated fresh 64-hex pair via `identity.generate_secret_hex()`, appended to `backend/.env` (gitignored). Restarted in configured mode; `app_fingerprint=6cf4a507`; protected paths 401 without cookie. This is a temporary bridge until install.sh (TKT-0030) ships -- the install script will own the .env lifecycle going forward.
8. Marked TKT-0025 `resolved`. Servers updated in PIPELINE.md.

## Outcome
TKT-0025 resolved. Auth gate is now production-grade: outermost in the middleware stack, 401 returned with the flat envelope before slowapi sees the request, dev/unconfigured mode preserved for legacy localhost setups. Next: Verification Agent (iter57) picks up TKT-0025.
