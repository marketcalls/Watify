---
id: TKT-0025
title: Auth middleware -- protect /api/* (allowlist auth + health)
status: open
priority: P1
area: backend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
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
