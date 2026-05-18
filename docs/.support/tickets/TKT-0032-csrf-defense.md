---
id: TKT-0032
title: CSRF defense on state-changing endpoints (X-Requested-With + Origin check)
status: verified
priority: P2
area: backend
created: 2026-05-18T19:01:30Z
updated: 2026-05-18T19:01:30Z
created_by: ticketing_agent
related_plan_item: A4
related_tickets: TKT-0024, TKT-0025
filed_via: security_audit_iter51
---

## Summary
Once cookie auth lands (TKT-0024 + TKT-0025), `SameSite=Lax` cookies block CSRF for cross-origin POSTs in modern browsers. That's good but not complete:

- A malicious site can still issue top-level GET navigations that the browser will send the cookie for. Watify's read endpoints are idempotent so this is mostly fine, but `GET` should never have side effects (audit existing routes).
- A malicious page on a flaw'd subdomain (or via XSS elsewhere) could attempt fetch with `credentials: "include"` -- the same-origin policy + CORS allowlist blocks the response read but the request itself fires.

Defense in depth: require a custom header `X-Requested-With: XMLHttpRequest` on all state-changing endpoints (`POST`, `PATCH`, `DELETE`). Simple HTML forms can't set custom headers; a fetch from our own frontend can. This is the same trick Django uses.

## Expected
- `app/main.py` adds a middleware that runs AFTER auth and BEFORE the rate-limit handler:
  - For methods in `{POST, PATCH, PUT, DELETE}` against `/api/*` (except `/api/auth/login` and `/api/auth/register` -- those start without auth state and need to work on first visit), require either `X-Requested-With: XMLHttpRequest` OR a same-origin `Origin` header matching `settings.cors_origin`.
  - Reject with 403 `{"error":"csrf_required","detail":"missing X-Requested-With or invalid Origin"}`.
- `frontend/src/lib/api.ts` adds `X-Requested-With: XMLHttpRequest` to every request alongside the existing Content-Type header.

## Acceptance
- curl POST without the header -> 403.
- curl POST with `-H "X-Requested-With: XMLHttpRequest"` -> works as before.
- Frontend keeps working (api.ts sets the header).
- Login + register still work (allowlisted).

## Resolution history
- 2026-05-18T19:01:30Z -- filed by Ticketing Agent (iter51, security audit defense-in-depth).
- 2026-05-18T21:15:00Z -- resolved by Resolving Agent (iter77). Three-file change set: (1) `backend/app/csrf_middleware.py` (new) -- 70-line Starlette `BaseHTTPMiddleware`; bypass matrix: non-`/api/*` -> bypass, safe methods (GET/HEAD/OPTIONS) -> bypass, allowlist `{/api/auth/login, /api/auth/register}` -> bypass; for any other state-changing method, accepts the request if EITHER `X-Requested-With: XMLHttpRequest` OR `Origin == settings.cors_origin`, otherwise returns 403 with the flat envelope `{"error":"csrf_required","detail":"missing X-Requested-With or invalid Origin"}`. (2) `backend/app/main.py` -- import CSRFMiddleware + `app.add_middleware(CSRFMiddleware)` AFTER the existing `app.add_middleware(AuthMiddleware)` line, with an inline comment explaining the resulting outer-to-inner order: CSRF -> Auth -> CORS -> handler. (3) `frontend/src/lib/api.ts` -- injected `"X-Requested-With": "XMLHttpRequest"` into the default headers of `apiFetch` (between `Content-Type` and the spread of caller-provided headers) with a TKT-0032 comment. `uv run python -m py_compile` clean on both backend files; `npx tsc --noEmit` exit 0. Backend restarted (pid 37636, fingerprint 6cf4a507). Smoke (8 cases): (1) GET /api/groups no cookie -> 401 (CSRF doesn't gate safe methods, Auth fires); (2) POST /api/groups no header no Origin -> 403 csrf_required; (3) POST + X-Requested-With -> 401 auth_required (CSRF passed, Auth fired); (4) POST + Origin=cors_origin -> 401 auth_required; (5) POST + Origin=http://evil.com -> 403 csrf_required; (6) /api/auth/login allowlisted (no X-Requested-With) with wrong creds -> 401 invalid_credentials; (7) login + X-Requested-With with wrong creds -> 401 invalid_credentials; (8) OPTIONS preflight -> 200 OK. Conversation: `docs/.support/conversations/2026-05-18T211414Z-resolving_agent-iter77.md`.
- 2026-05-18T21:20:00Z -- VERIFIED by Verification Agent (iter78). Four structural checks plus 8 smokes all independently reproduced. (a) `uv run python -m py_compile app/csrf_middleware.py app/main.py` clean. (b) `npx --no-install tsc --noEmit` from `frontend/` exits 0. (c) `grep 'X-Requested-With' frontend/src/lib/api.ts` returns hit at line 50: `"X-Requested-With": "XMLHttpRequest",`. (d) `grep 'app.add_middleware' backend/app/main.py` returns three lines in order: CORSMiddleware at line 57, AuthMiddleware at line 70, CSRFMiddleware at line 78 -- CSRF is registered AFTER Auth, so per FastAPI's reverse-order semantics CSRF is the OUTERMOST middleware (request order: CSRF -> Auth -> CORS -> handler). Smoke (all 8 reproduced via curl against the running backend pid 37636): (1) GET /api/groups no-cookie -> 401 auth_required (CSRF passes safe methods); (2) POST /api/groups no header no Origin -> 403 csrf_required; (3) POST + X-Requested-With: XMLHttpRequest -> 401 auth_required (CSRF gate passed, Auth fired); (4) POST + Origin: http://localhost:3000 -> 401 auth_required; (5) POST + Origin: http://evil.com -> 403 csrf_required; (6) /api/auth/login wrong creds no header -> 401 invalid_credentials (allowlisted, reached the handler); (7) /api/auth/login wrong creds + X-Requested-With -> 401 invalid_credentials; (8) OPTIONS preflight -> 200 OK. Verified.
