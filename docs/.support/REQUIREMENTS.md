# Watify — Requirements

Captured from the initial user conversation on 2026-05-18. This document is the contract the agents build against. Any change requires explicit user approval.

## Product
A single-user WhatsApp notification service for sending messages to curated friend watchlists.

## Tech Stack
- **Backend**: Python 3.13+ via `uv`, FastAPI, SQLite, APScheduler, `wars` library for WhatsApp.
- **Frontend**: Next.js (latest stable, App Router), React, TypeScript, Tailwind CSS.
- **WhatsApp**: `wars` library — file-backed session at `backend/whatsapp.db`.
- **Repo**: GitHub `marketcalls/Watify`.

## Functional Requirements

### F1. WhatsApp Connection
- F1.1 — Pair via QR scanned on phone. QR rendered in the browser as a data URL (see `docs/wars.md` §4).
- F1.2 — Session persists across restarts via SQLite file `backend/whatsapp.db`.
- F1.3 — UI shows connection state: `disconnected`, `pairing`, `ready`, `error`.
- F1.4 — Disconnect / re-pair button.

### F2. Test Messaging
- F2.1 — Send a test message to self (owner number, single-arg `wa.send(text)`).
- F2.2 — Send a test message to an arbitrary WhatsApp number.

### F3. Friend Groups (Watchlists)
- F3.1 — User can create multiple named friend groups.
- F3.2 — **Hard cap: 20 contacts per group.** Backend enforces; frontend disables Add at 20.
- F3.3 — CRUD on groups and contacts (name + E.164 phone number).
- F3.4 — Bulk upload: CSV / paste — max 20 rows per upload; rejects the whole file if any row is invalid.
- F3.5 — Phone number normalization (digits / +CC / spaces — see wars JID normalization).

### F4. Sending Messages
- F4.1 — Compose message → pick target group → send.
- F4.2 — **One message at a time** (no parallel sends to a group).
- F4.3 — **Random per-recipient delay between min/max seconds. Default 3–30s. User-configurable per send.**
- F4.4 — Live progress UI: sent / pending / failed per recipient.
- F4.5 — Each send produces a job record visible in history.

### F5. Scheduling
- F5.1 — Send Now (immediate dispatch).
- F5.2 — Schedule one-time send at a future date+time (user's local TZ).
- F5.3 — APScheduler with SQLite jobstore so jobs survive restart.
- F5.4 — Cancel a pending scheduled job.

### F6. Safety
- F6.1 — No bulk-marketing patterns. Daily send-count surfaced in UI as a soft cap reminder.
- F6.2 — `whatsapp.db` is gitignored. Never commit session bytes.
- F6.3 — Treat all phone numbers as sensitive; no logging of full numbers in conversation logs.

## Non-functional
- **Single-user**. Only one human operates the app. Exactly one User row in `app.db`.
- Dev: backend on `http://localhost:8000`, frontend on `http://localhost:3000`.
- Production (v1.1): one Ubuntu VM, custom domain behind Cloudflare with Let's Encrypt origin certs.
- Dev servers stay running in the background while the loop iterates so the Verification Agent can hit them via Chrome MCP.

## Auth + multi-page surface (v1.1)

**A1. Public hero page** at `/` (no auth). Marketing copy: what Watify does, the 20-cap, 3-30s delay, screenshots/diagrams if available. CTAs to `/login` and `/register`.

**A2. Register-once-lock**.
- `POST /api/auth/register` accepts `{username, password}` ONCE. The first successful registration creates the singleton User row and marks them as the admin (the only role; this app has no others).
- Subsequent calls to `/register` return **409** `{"error":"registration_closed","detail":"this app already has its single user"}`.
- Password rules: minimum 12 characters, no other complexity rules (operator chooses their own strength).
- Hashing: **argon2** (via `passlib[argon2]` or `argon2-cffi` directly). Never store plaintext.

**A3. Login**.
- `POST /api/auth/login` accepts `{username, password}`. On success: returns a JWT (HS256) and sets it as an `httpOnly`, `Secure` (production), `SameSite=Lax` cookie named `watify_session`.
- Token TTL: 15 minutes access + a 7-day refresh token (separate cookie `watify_refresh`). Both server-rotate on refresh.
- `POST /api/auth/refresh` issues a new access token if the refresh cookie is valid.
- `POST /api/auth/logout` clears both cookies and rotates the user's refresh-token secret (so any stolen token is invalidated).
- `GET /api/auth/me` returns `{username, created_at}` when authed.

**A4. Auth middleware** (server-side gate).
- Every `/api/*` request must be authed EXCEPT the allowlist: `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`. Missing/invalid token returns 401 with the flat envelope from TKT-0001.
- Auth middleware runs BEFORE the rate-limit middleware so 429s never reveal token status.

**A5. Rate limits on auth**.
- `POST /api/auth/register`: hard `3/minute` per IP (any more is bot pressure).
- `POST /api/auth/login`: `5/minute` per IP, with an additional sliding lockout: 5 consecutive failures in 10 minutes -> 15-minute lockout for that IP. Surface as 429 with `Retry-After`.
- `POST /api/auth/refresh`: `30/minute` per IP.

**A6. Frontend routes**.
- Public: `/` (hero), `/login`, `/register`.
- Protected: `/dashboard`, `/connect`, `/groups`, `/send`, `/history` -- redirect to `/login` when not authed.
- TopNav swaps based on auth state: `[Watify] Login Register` vs `[Watify] Dashboard Connect Groups Send History Logout`.

**A7. Token storage**.
- HttpOnly cookie pair (`watify_session` + `watify_refresh`) -- not localStorage. SameSite=Lax. Secure flag in production.
- API base URL on the client uses `credentials: "include"` so the cookies travel.

**A8. Single-user enforcement at multiple layers**.
- Database: `User` table has a `UNIQUE(role='admin')` partial index -- only one admin row possible.
- Backend: `/register` checks `if any(session.exec(select(User))): return 409`.
- Frontend: when an authed user hits `/register` it 302s to `/dashboard`.

## Production install (v1.1)

**P1. Install script at `install/install.sh`** (Ubuntu 22.04 / 24.04), mirroring the Dittot pattern:
- Re-run safe (preserves existing `.env` SECRET_KEY + Fernet session key + DB).
- Prompts for custom domain (apex + optional `www.`), validates format.
- Prompts for Let's Encrypt email.
- Opens UFW 80/443.
- Installs system deps: git, curl, build-essential, python3-dev, nodejs 20, nginx, certbot.
- Installs `uv` for Python; `npm` for Node.
- Clones the repo to `/var/www/watify`.
- Generates `backend/.env` with `WATIFY_*` keys (auto-generates SECRET_KEY, JWT secret, Fernet session key on fresh install; preserves on re-run).
- `uv sync` in backend, `npm install && npm run build` in frontend.
- Creates two systemd units:
  - `watify.service` -- FastAPI/uvicorn via unix socket at `/run/watify/watify.sock`, 1 worker (the wars singleton is one-process-per-host).
  - `watify-frontend.service` -- `next start -H 127.0.0.1 -p 3000`.
- Writes Nginx config at `/etc/nginx/sites-available/watify`:
  - Cloudflare-aware: `map $http_cf_connecting_ip $watify_real_ip ...` so backend rate-limit middleware and Nginx auth-zone both see the real client IP.
  - Strict auth zone: `limit_req_zone $watify_real_ip zone=watify_login:10m rate=5r/m;` matched on `/api/auth/login` and `/api/auth/register` with `burst=3 nodelay`.
  - Connection limit: `limit_conn watify_conn 50`.
  - Standard security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
  - Gzip on for text/json/js/svg.
  - `client_max_body_size 10M`.
  - Frontend upstream `127.0.0.1:3000`, backend upstream unix socket.
  - SSL via certbot --nginx; HSTS snippet at `/etc/nginx/snippets/ssl-security.conf`; auto-renewal cron.
- Logrotate config at `/etc/logrotate.d/watify` rotating systemd stdout (100MB, keep 3).
- Permissions: `www-data:www-data` on `/var/www/watify` + `/var/log/watify`; `chmod 600` on `.env` and `app.db`.
- Health-checks each service after start and dumps `journalctl -n 20` on failure.

**P2. Sibling `install/update.sh`** -- `git pull`, `uv sync`, `npm install && npm run build`, restart both units. Re-runnable.

**P3. SQLite as the only datastore** -- explicitly NO Postgres, Redis, QuestDB. `app.db` lives at `/var/www/watify/backend/app.db`; nightly backups to `/var/lib/watify-backups/` (keep 30 days).

## Security & secrets

**S1. All configuration via `.env`.**
- `backend/.env` (gitignored) holds runtime config. `backend/.env.example` (committed) documents every variable with safe placeholders.
- `frontend/.env.local` (gitignored) holds public env. `frontend/.env.local.example` (committed) is its template.
- No secret, token, phone number, or path may be hardcoded in source. Read everything via `pydantic-settings` (backend) or `process.env.NEXT_PUBLIC_*` (frontend).

**S2. Encoding & input validation.**
- All API request/response bodies are typed Pydantic models (server) and TypeScript types (client). No `dict[str, Any]` reaching a handler boundary.
- Phone numbers normalize through one helper (E.164, digits only) before any DB write or wars call.
- HTML output uses React's default escaping. No `dangerouslySetInnerHTML`.
- SQL strictly via SQLModel / SQLAlchemy parameterized queries — no f-string SQL.

**S3. Database.**
- `app.db` and `whatsapp.db` are gitignored. They live next to the backend process, not in any shared path.
- File mode 0600 on the wars session DB (POSIX) — Windows relies on the user profile ACL.
- No raw connection string with credentials anywhere; SQLite uses local file paths only.

**S4. Network.**
- CORS allowlist is `http://localhost:3000` only. Wildcards rejected.
- Backend binds 127.0.0.1, never 0.0.0.0.
- Frontend never sends API requests to anything other than `NEXT_PUBLIC_API_BASE`.

**S5. Logging.**
- Phone numbers redacted to `+CC XXXXX <last 4>` in backend logs and in conversation logs.
- The conversation logs in `docs/.support/conversations/` MUST NOT contain raw phone numbers, session bytes, QR strings, or message bodies sent to real contacts.

**S6. Session handling.**
- `wars` session file path is configurable via env. Default `backend/whatsapp.db`.
- The session bytes never leave the backend process boundary except for the on-disk SQLite file.

The Ticketing Agent runs a security pass every Ticketing iteration — see AGENTS.md.

## Out of scope (v1)
- Multi-user / auth.
- Receiving messages / bot mode.
- Group chats (WhatsApp groups, distinct from friend groups).
- Recurring cron-style schedules.
- Media attachments (text only for v1).
