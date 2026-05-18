# Iteration 77 -- Resolving Agent (TKT-0032)

- **Started**: 2026-05-18T21:14:14Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0032 (P2 backend) -- CSRF defense

## Plan
1. New `backend/app/csrf_middleware.py` -- Starlette `BaseHTTPMiddleware`. Logic:
   - Bypass non-`/api/*` paths.
   - Bypass safe methods (`GET`, `HEAD`, `OPTIONS`).
   - Bypass allowlist (`/api/auth/login`, `/api/auth/register`).
   - For `POST|PATCH|PUT|DELETE` on `/api/*`, accept if EITHER `X-Requested-With: XMLHttpRequest` header is present OR `Origin` header equals `settings.cors_origin` exactly. Otherwise 403 with the flat envelope `{"error":"csrf_required","detail":"missing X-Requested-With or invalid Origin"}`.
2. Register in `main.py` via `app.add_middleware(CSRFMiddleware)` AFTER the existing `app.add_middleware(AuthMiddleware)` call. FastAPI applies middleware in reverse order of `add_middleware`, so the LAST-added is the OUTERMOST. Adding CSRF after Auth makes CSRF the outermost; on an incoming state-changing request the order is: CSRF -> Auth -> CORS preflight handling -> route handler. CSRF therefore returns 403 BEFORE Auth would return 401 for the same request -- that's the spec's intent (the CSRF check is a defense-in-depth gate that should not even let unauthenticated state-changing requests reach the auth check).
3. Update `frontend/src/lib/api.ts` -- inject `X-Requested-With: XMLHttpRequest` into the default headers of `apiFetch` so every browser-driven request passes the gate. Callers can still override per-call via `init?.headers`.
4. Smoke:
   - `curl -X POST http://localhost:8000/api/groups -H "Content-Type: application/json" -d '{"name":"x"}'` (no cookie, no X-Requested-With, no Origin) -> 403 csrf_required.
   - Same + `-H "X-Requested-With: XMLHttpRequest"` -> goes through CSRF; AuthMiddleware then returns 401 (no cookie).
   - Same + `-H "Origin: http://localhost:3000"` -> goes through CSRF (Origin matches); AuthMiddleware returns 401.
   - `curl -X POST /api/auth/login -d '{...}'` without X-Requested-With or Origin -> allowed (allowlisted), responds 200 or 401 invalid_credentials depending on creds.
5. `uv run python -m py_compile backend/app/csrf_middleware.py backend/app/main.py` clean.
6. `npx tsc --noEmit` clean.

## Actions

1. Marked TKT-0032 `inprogress`.
2. Wrote `backend/app/csrf_middleware.py` -- 70-line `BaseHTTPMiddleware`. Bypass matrix non-/api/* -> safe-methods -> allowlist (login + register) -> require X-Requested-With OR matching Origin. 403 csrf_required with flat envelope on rejection. INFO-log on rejection (no sensitive data, just method + path + xrw + origin values).
3. Edited `backend/app/main.py`: imported CSRFMiddleware, added `app.add_middleware(CSRFMiddleware)` AFTER the AuthMiddleware line with an inline comment explaining FastAPI's reverse-order middleware semantics and the resulting CSRF -> Auth -> CORS -> handler order.
4. Edited `frontend/src/lib/api.ts`: injected `"X-Requested-With": "XMLHttpRequest"` into the default fetch headers between `Content-Type` and the caller-provided header spread. Caller headers still override per-call.
5. `uv run python -m py_compile app/csrf_middleware.py app/main.py` -> clean.
6. `npx --no-install tsc --noEmit` -> exit 0.
7. Restarted backend (pid 37636) and ran 8 smokes:
   - GET no cookie -> 401 (CSRF passes safe methods, Auth fires).
   - POST no header no Origin -> 403 csrf_required.
   - POST + X-Requested-With -> 401 auth_required.
   - POST + Origin=http://localhost:3000 -> 401 auth_required.
   - POST + Origin=http://evil.com -> 403 csrf_required.
   - /api/auth/login wrong creds (no header) -> 401 invalid_credentials (allowlisted).
   - /api/auth/login wrong creds + X-Requested-With -> 401 invalid_credentials.
   - OPTIONS preflight -> 200 OK.
8. Marked TKT-0032 `resolved` with the 8-smoke Resolution history.

## Outcome
TKT-0032 resolved. The CSRF gate is live as a defense-in-depth layer on top of SameSite=Lax cookies. A forged cross-site POST from a malicious page cannot set `X-Requested-With` (simple HTML form attack vector) and its `Origin` header is set by the browser to the attacker's origin (which won't match `settings.cors_origin`), so the gate returns 403 before the request reaches the auth check. The frontend's apiFetch wrapper carries the header automatically, so all existing dashboard calls continue to work post-login. Next: Verification Agent reproduces the 8 smokes and commits.
