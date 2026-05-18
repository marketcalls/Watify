# Iteration 55 — Verification Agent (TKT-0024)

- **Started**: 2026-05-18T19:22:23Z
- **Phase entering**: verification
- **Active agent**: verification_agent
- **Ticket under test**: TKT-0024 -- auth endpoints + JWT cookies + auth rate limits

## Plan
1. Independent fresh-cycle: wipe user row, register, /me, logout, login, refresh, observe cookie flags via `Set-Cookie` raw response.
2. 503 path: restart backend without `WATIFY_APP_SECRET` -- every /api/auth/* should refuse with 503 `auth_not_configured`.
3. `typ` differentiation: feed a refresh token to /me (which decodes as access) -> 401.
4. On pass: commit + push.

## Actions
