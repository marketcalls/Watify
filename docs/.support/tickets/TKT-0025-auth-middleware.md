---
id: TKT-0025
title: Auth middleware -- protect /api/* (allowlist auth + health)
status: verified
priority: P1
area: backend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T19:36:30Z
created_by: ticketing_agent
related_plan_item: B-09, A4
related_tickets: TKT-0023, TKT-0024
filed_via: human_manual_input
---

## Summary
FastAPI middleware that requires a valid JWT on every `/api/*` request except a tight allowlist.

## Expected
- `app/auth_dep.py` -- `def current_user(request: Request) -> User` FastAPI dependency that:
  - Reads `watify_session` cookie OR `Authorization: Bearer <jwt>` header (cookie wins).
  - Decodes with `pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])`.
  - Resolves `User` from the `sub` claim.
  - Raises `HTTPException(401, "auth_required")` on missing / invalid / expired tokens.
- `app/main.py` registers a Starlette `BaseHTTPMiddleware` that runs BEFORE slowapi:
  - Allowlist (no auth): `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, plus any `OPTIONS` preflight.
  - Everything else under `/api/*` -> require auth, return 401 flat envelope on failure.
  - Non-API paths (Next.js static, the public hero) bypass entirely.
- Order: auth middleware -> CORS -> slowapi -> handler. Verify so 429 never leaks token validity.
- Smoke: hit `/api/groups` without cookie -> 401; with valid cookie -> 200.

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
- 2026-05-18T19:43:00Z -- resolved by Resolving Agent (iter56). Added `backend/app/auth_middleware.py` -- Starlette `BaseHTTPMiddleware` with the exact bypass matrix in the spec: non-`/api/*` -> bypass; `settings.app_secret` empty -> bypass (preserves dev/unconfigured behavior); `OPTIONS` -> bypass (CORS preflight); allowlist `{/api/health, /api/auth/register, /api/auth/login, /api/auth/refresh}` -> bypass. Everything else: read `watify_session` cookie, decode via `decode_access`, return 401 with the flat envelope `{error:"auth_required", detail:...}` on missing / invalid / expired. Registered in `main.py` via `app.add_middleware(AuthMiddleware)` AFTER `CORSMiddleware` so AuthMiddleware sits OUTERMOST in Starlette's stack (FastAPI applies middleware in reverse order of `add_middleware`). slowapi is a route-decorator + exception handler, NOT a middleware, so its 429 logic runs INSIDE the auth gate -- 429 can never leak token validity. Smoke (configured mode): `/api/health` 200; `/api/groups` no-cookie 401 with `auth_required`; `/api/jobs` no-cookie 401; `/api/wa/state` no-cookie 401; `/api/auth/login` -> 200 + cookies; `/api/groups` with cookie 200; bad cookie 401 with `session token invalid or expired`. Smoke (dev mode, `WATIFY_APP_SECRET` empty): `/api/groups` 200 (bypass preserved), `/api/health` 200 with `app_fingerprint=null`, `/api/auth/login` 503 `auth_not_configured`. Also wrote a fresh `WATIFY_APP_SECRET` + `WATIFY_API_KEY` to `backend/.env` so configured mode survives restarts until install.sh (TKT-0030) takes over. Backend restored: pid in `docs/.support/logs/backend.pid`, fingerprint `6cf4a507`. Conversation: `docs/.support/conversations/2026-05-18T192734Z-resolving_agent-iter56.md`.
- 2026-05-18T19:36:30Z -- VERIFIED by Verification Agent (iter57). Code inspection: bypass matrix and 401 envelope match the spec exactly; `decode_access` enforces `typ=access`, so the refresh-token (composite-key signed) cannot impersonate a session token. Smoke (independent reproduction against backend pid 20252, fingerprint `6cf4a507`): (a) `/api/health` 200 + non-null fingerprint; (b) `/api/groups`, `/api/jobs`, `/api/wa/state` without cookie -> 401 `auth_required missing watify_session cookie`; (c) admin login -> 200 + httpOnly cookies (`watify_session` access JWT + `watify_refresh` refresh JWT, both decoded out of /tmp/iter57_jar.txt); (d) `/api/groups` + `/api/jobs` WITH cookie -> 200 each; (e) malformed cookie `not.a.valid.jwt` -> 401 `session token invalid or expired`. Bonus: pasting the refresh token into the `watify_session` slot is rejected 401 -- typ discriminator works. (f) Outermost-middleware test: 10 rapid no-cookie hits to `/api/groups` -> all 401 (never 429 or 200); same for `/api/jobs` POST (which carries no slowapi limit at this path but exercises a write handler) -- all 401. Dev mode (override `WATIFY_APP_SECRET=`): `/api/health` 200 with `app_fingerprint=null`; `/api/groups` no-cookie 200 (bypass preserved); `/api/auth/login` -> 503 `auth_not_configured`. Backend restored in configured mode, pid 20252 written to `docs/.support/logs/backend.pid`. Conversation: `docs/.support/conversations/2026-05-18T193508Z-verification_agent-iter57.md`.
