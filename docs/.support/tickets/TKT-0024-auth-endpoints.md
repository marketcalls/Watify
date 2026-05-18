---
id: TKT-0024
title: Auth endpoints + JWT cookies + auth rate limits
status: open
priority: P1
area: backend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: B-09, A2, A3, A5
related_tickets: TKT-0023
filed_via: human_manual_input
---

## Summary
Five endpoints under `/api/auth/*`, JWT-in-httpOnly-cookie session, slowapi rate limits matching REQUIREMENTS A5.

## Expected
- `uv add "pyjwt[crypto]"` -- HS256 with the SECRET_KEY from settings.
- `app/settings.py` adds:
  - `secret_key: str` (required at boot; backend fails fast with a clear message if unset).
  - `jwt_access_minutes: int = 15`
  - `jwt_refresh_days: int = 7`
- `app/routers/auth.py`:
  - `POST /api/auth/register` `{username, password}` -> 201 with the user + sets cookies. Returns **409 registration_closed** if any user exists. **Rate limit: 3/minute.**
  - `POST /api/auth/login` `{username, password}` -> 200 + cookies on success, 401 on bad creds. **Rate limit: 5/minute.** Sliding lockout (5 consecutive fails in 10 min -> 15-min IP lockout) implemented in-memory for now (Redis later).
  - `POST /api/auth/refresh` -> reads `watify_refresh` cookie, validates against the user's `refresh_secret`, issues a new access cookie. Rate limit: 30/minute.
  - `POST /api/auth/logout` -> clears both cookies + rotates `refresh_secret`.
  - `GET /api/auth/me` -> returns `{username, created_at}` when authed (gated by TKT-0025 middleware).
- Cookies: `httpOnly`, `SameSite=Lax`, `Secure` when `request.url.scheme == "https"`, paths `/`.
- All error bodies use the flat envelope from TKT-0001.
- Smoke script `scripts/smoke_auth_endpoints.py`: registers once (201), tries to register again (409), logs in (200 + Set-Cookie), bad creds (401), 5 bad creds in a row trigger lockout (429), refresh (200), logout (clears cookies).

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
