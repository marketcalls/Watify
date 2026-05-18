# Iteration 47 — Ticketing Agent (auth + landing + install scope)

- **Started**: 2026-05-18T18:41:55Z
- **Phase**: ticketing
- **Active agent**: ticketing_agent
- **Trigger**: human manual input (3 messages combined):
  1. "I want to have a watify page with hero page and then login and register, the first user is the admin and it is a single user app. Only one user can login to the app. ensure rate limits are handled and i would like to install the app similar to [Dittot install.sh]"
  2. "keep the server installation in custom domain with cloudflare + letsencrypt config"
  3. "similar to the installation script provided" + "keep in install folder"

## Scope decision
This is a substantial product-spec change. Current REQUIREMENTS.md says "Single-user, runs locally. No auth UI." -- we are explicitly contradicting that. Treat as a milestone bump:

- Watify v1 was "single-user local dev tool".
- Watify v1.1 ("the v-milestone we're entering now") becomes a deployable single-user app with auth, marketing hero, and Ubuntu/Cloudflare/Let's-Encrypt install.

REQUIREMENTS.md gets an §"Auth + multi-page surface (v1.1)" section. PLAN.md gets new items B-09 / F-08 / I-05 to track. 8 tickets cover the implementation:

| Ticket | P | Area | Scope |
|---|---|---|---|
| TKT-0023 | P1 | backend | Single-user auth model (User SQLModel, argon2 hash, register-once lock) |
| TKT-0024 | P1 | backend | Auth endpoints (/api/auth/register, /login, /logout, /me) + rate limits |
| TKT-0025 | P1 | backend | Auth middleware -- protect /api/* (allowlist /api/auth/* + /api/health) |
| TKT-0026 | P1 | frontend | /login + /register pages -- forms, validation, token storage |
| TKT-0027 | P2 | frontend | Public hero page at /, move existing dashboard to /dashboard |
| TKT-0028 | P2 | frontend | Auth-aware nav (Login/Register vs Dashboard/Logout) |
| TKT-0029 | P2 | frontend | Route guards on /dashboard/connect/groups/send/history |
| TKT-0030 | P1 | infra | install/install.sh (+ install/update.sh) for Ubuntu + Cloudflare + Let's Encrypt |

These can ship in roughly that order. The dependency graph:
- 0023 -> 0024 -> 0025 -> 0026 (backend then frontend wiring)
- 0027/0028/0029 ride on top of 0026
- 0030 is independent but should wait until at least 0024 lands so the install script can reference real auth endpoints

Actions taken this iteration:
- Updated `REQUIREMENTS.md` §Auth + multi-page surface.
- Updated `PLAN.md` with B-09, F-08, I-05.
- Filed TKT-0023 through TKT-0030.
- Set PIPELINE next = TKT-0005 verification first (in-flight from iter46), then TKT-0023 resolve.

## Note on the priority context
TKT-0005 is still `resolved` (awaiting verification from iter46). I do NOT verify here; that is the Verification Agent's job. Iter48 should run Verification on TKT-0005 first, then iter49 starts on TKT-0023.

Alternative: if the user prefers the new feature to jump the queue, the Resolving Agent can pick up TKT-0023 in iter48 and TKT-0005's verification can slot in later (since 0005 has no impact on the live session and the env-seed path is trivial).
