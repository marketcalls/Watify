# Iteration 54 — Resolving Agent (TKT-0024)

- **Started**: 2026-05-18T19:14:51Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0024 (P1 backend) -- auth endpoints + JWT cookies + auth rate limits

## Plan
1. Mark TKT-0024 `inprogress`.
2. `uv add pyjwt`.
3. `app/settings.py` adds `jwt_access_minutes: int = 15` and `jwt_refresh_days: int = 7`.
4. `app/jwt_tokens.py`:
   - `encode_access(user_id)` -- HS256 with `settings.app_secret`, 15-min exp.
   - `decode_access(token)` -- raises on invalid/expired.
   - `encode_refresh(user_id, refresh_secret)` -- HS256 with `app_secret + refresh_secret` composite key, 7-day exp.
   - `decode_refresh(token, refresh_secret)` -- composite-key decode.
   - `decode_unverified_sub(token)` -- read `sub` claim without verifying signature (only used to look up the refresh_secret before verifying).
   - Each token carries `"typ": "access" | "refresh"` so the two cannot be substituted.
5. `app/auth_lockout.py` -- in-memory dict, threading.Lock. `check_locked(ip)`, `record_fail(ip)`, `clear(ip)`. 5 fails in 10 min -> 15-min lock.
6. `app/routers/auth.py`:
   - `POST /api/auth/register` body `{username, password}` -> on first call create_admin + set both cookies + 201; subsequent calls -> 409 registration_closed. Rate: 3/minute.
   - `POST /api/auth/login` `{username, password}` -> verify_credentials, on success: set both cookies, touch last_login, clear lockout, return 200; on failure: record_fail (which may engage the lockout) and return 401. Rate: 5/minute + sliding lockout.
   - `POST /api/auth/refresh` -- read refresh cookie, decode unverified to get sub, fetch user, decode with composite key, issue new access cookie. 30/minute.
   - `POST /api/auth/logout` -- rotate user.refresh_secret + clear cookies. 200.
   - `GET /api/auth/me` -- temp inline cookie-auth (until TKT-0025 middleware) returns `{username, created_at}`.
   - 503 `auth_not_configured` returned by ALL 5 when `app_secret` is empty.
7. Wire router in `app/main.py`.
8. Smoke `scripts/smoke_auth_endpoints.py` -- 7 cases.
9. Restart backend (with `WATIFY_APP_SECRET` set), run smoke, leave wars session intact.

## Notes
- TKT-0025 auth middleware lands later; until then `/api/auth/me` uses an inline `get_current_user` dependency. The other /api/* routes (groups, jobs, wars) remain unprotected. This is acceptable for v1.1 in flight; iter56+ closes that gap.
- The lockout is per-IP and in-memory. Survives the slowapi rate-limit storm because slowapi counts every attempt while the lockout counts only failed credentials. Both run; lockout wins when tripped.

## Actions
