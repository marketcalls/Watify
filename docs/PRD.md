# Watify -- Product Requirements (v1.1, shipped)

This document captures what Watify actually ships, not what was originally specified. For the original contract, see `docs/.support/REQUIREMENTS.md`. For the full ticket trail of every decision, see `docs/.support/PIPELINE.md` and `docs/.support/tickets/`.

Status: **v1.1 shipped** (iter107, 2026-05-19). 57 tickets verified, 1 closed-deferred (TKT-0052 -> re-filed as TKT-0058 for v1.2).

---

## 1. Product

A single-user WhatsApp notification service that lets one operator broadcast text messages to curated friend watchlists from a self-hosted web app. Designed for personal / low-volume use, not bulk marketing.

**Non-goals (v1):**
- Multi-user / team accounts.
- Receiving messages (no bot mode).
- WhatsApp group chats (distinct from Watify friend groups).
- Recurring cron-style schedules (one-shot only).
- Media attachments (text only).
- Delivery / read receipts (deferred to v1.2 -- see TKT-0058).

---

## 2. User journey

1. Operator clones the repo (or runs `install/install.sh` on a fresh Ubuntu VM).
2. Opens the app, clicks **Get started**, registers the single admin user.
3. Logs in. The TopNav flips from `[Sign in | Get started]` to `[Dashboard | Connect | Groups | Send | History | Logout]`.
4. Goes to `/connect`, pairs WhatsApp via QR or 8-char pair code.
5. Optionally clicks **Test connection** to send a canary message to their own number.
6. Goes to `/groups`, creates a named friend group, adds up to 20 contacts (name + E.164 phone). CSV/paste bulk-add is one shot, max 20 rows per upload.
7. Goes to `/send`, picks a group, composes a message, optionally schedules it, sets the per-recipient delay (default 3-30s).
8. Watches `/history` for live job progress. Each attempt shows sent / pending / failed plus the redacted phone.
9. Disconnects when done (red Disconnect button on `/connect` opens a modal and wipes the session).

---

## 3. Functional spec

### F1. WhatsApp connection
- **F1.1 QR pairing**. `wars` emits a fresh QR every 30 seconds; the page polls `/api/wa/state` at 1s while pairing and re-renders the data-URL.
- **F1.2 Pair-code pairing**. Operator enters their phone in E.164; backend asks wars for an 8-character code; UI shows a chunked monospaced display ("ABCD-EFGH") with instructions to type it on the phone.
- **F1.3 Connection states**: `disconnected | pairing | paired | ready | error`. The `paired` state is reserved for post-handshake pre-sync; current wars version collapses it to `ready`.
- **F1.4 Disconnect = full unlink**. The Disconnect button opens a styled modal (no browser `confirm()`), shows a "Disconnecting..." progress state, then wipes the session blob and any legacy `whatsapp.db*` files. There is no soft-disconnect path. Next pairing requires a fresh QR / pair code.
- **F1.5 Session persistence**. The wars session is encrypted (Fernet) and stored in `app.db.wa_session` when `WATIFY_SESSION_ENCRYPTION_KEY` is set; otherwise plaintext at `backend/whatsapp.db`. Survives restarts.

### F2. Test messaging
- **F2.1 Send-to-self**. `/api/wa/test/self` posts a canary message to the linked-device's own number. Rate-limited 15/minute. The message body carries a local-time timestamp.

### F3. Friend groups
- **F3.1 CRUD**. Create, rename, delete groups. Add and remove contacts. Each contact is name + E.164 phone.
- **F3.2 Hard cap 20**. Backend enforces; frontend disables Add at 20 with a tooltip.
- **F3.3 Bulk upload**. CSV or paste. Max 20 rows per upload. All-or-nothing -- if any row is invalid (bad phone, malformed name) the whole batch rejects with per-row reasons.
- **F3.4 Phone normalization**. One helper normalizes to E.164 before any DB write or wars call. Accepts `+919876543210`, `919876543210`, or spaced variants; rejects locally-formatted numbers.

### F4. Sending
- **F4.1 Compose -> pick group -> send**. One-shot send form on `/send`.
- **F4.2 One message at a time per group**. Enforced by APScheduler job ID = group ID; a second send to the same group while the first is running gets `409 group_busy`.
- **F4.3 Per-recipient random delay**. Default `[3, 30]` seconds, both bounds operator-configurable per send (`min_delay_s`, `max_delay_s`). Max upper bound 300s.
- **F4.4 Progress UI**. `/history` JobRow shows sent / total / failed pills. Expanding the row streams per-attempt rows with status (pending | sent | failed), redacted phone, error message if any.
- **F4.5 Job persistence**. APScheduler with SQLAlchemyJobStore on `app.db` -- scheduled jobs survive restart.

### F5. Scheduling
- **F5.1 Send Now**. Immediate dispatch.
- **F5.2 Schedule one-time**. `<input type="datetime-local">` in the operator's TZ. Backend converts to UTC for storage; UI re-renders in local TZ.
- **F5.3 Cancel**. Cancel button on any pending / scheduled job. Cleans the APScheduler entry and marks the SendJob `cancelled`.

### F6. Safety / abuse mitigation
- **F6.1 Soft daily-send cap reminder**. Dashboard shows a banner once you cross 100 sent in 24h.
- **F6.2 Session bytes never committed**. `whatsapp.db` + `app.db` + `.env` all gitignored. Install script generates secrets and persists them across re-runs.
- **F6.3 Phone redaction in logs**. Backend logger filter (`PhoneRedactionFilter`) strips runs of 10-15 digits to `+CC XXXXX <last 4>`. Conversation logs in `docs/.support/conversations/` likewise contain no raw phones.
- **F6.4 Pair-code never logged in plaintext**. Backend logs `pair_code_len=8` not the code itself, so a screenshot of the server log doesn't leak the pair code.

---

## 4. Auth (single-user)

- **Argon2id** password hashing via `passlib[argon2]`. Minimum 12 chars; no other complexity rules (operator picks their own strength).
- **JWT HS256** signed with `WATIFY_APP_SECRET`. Access token 15 min, refresh token 7 days, both rotated on `/api/auth/refresh`. Stored in `httpOnly` + `SameSite=Lax` cookies (`watify_session`, `watify_refresh`). `Secure` flag set in production.
- **Register-once-lock**. First `POST /api/auth/register` creates the singleton User row; subsequent calls return `409 registration_closed`. Frontend `/api/health.registered` flips to `true` so the public hero hides the **Get started** CTA. Authed users hitting `/register` are redirected to `/dashboard`.
- **Rate limits** (slowapi): `/register` 3/min/IP; `/login` 5/min/IP with 5-failures-in-10-minutes -> 15-minute IP lockout; `/refresh` 30/min/IP. All 429s carry `Retry-After`.
- **CSRF defense-in-depth**. Every state-changing request must carry `X-Requested-With: XMLHttpRequest` OR a same-origin `Origin` header, else `403 csrf_required`. Middleware order: CORS -> Auth -> CSRF (outermost).
- **Auth middleware allowlist**: `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`. Everything else under `/api/` is gated.

---

## 5. Frontend surface

| Route | Auth | Purpose |
|---|---|---|
| `/` | public | Hero page. Pill badge, gradient headline, two CTAs (Sign in / Get started -- the latter hides once registered), three feature cards, GitHub link, wars footer. |
| `/login` | public | Username + password. Honors `?next=<safePath>` (open-redirect-validated). |
| `/register` | public (until claimed) | First-run admin signup. Returns 302 to `/dashboard` when already claimed. |
| `/dashboard` | gated | Overview cards (WhatsApp status, jobs in-flight, soft-cap reminder). |
| `/connect` | gated | Pair via QR or pair code; Ready panel with Test connection + Disconnect. |
| `/groups` | gated | Friend groups CRUD + bulk import. |
| `/send` | gated | Compose + schedule + per-recipient delay knobs. |
| `/history` | gated | Job + per-attempt history. Times shown in operator's local TZ. |

TopNav flips between unauthed (`[Sign in | Get started]`) and authed (`[Dashboard | Connect | Groups | Send | History | Logout]`) based on `useAuth`.

**Theme**: two options, dark + light. Dark is the default. Toggle persists in `localStorage` under `watify.theme`. An inline no-flash script in `<head>` sets the `dark` class before React hydrates.

**Toaster**: global `useSyncExternalStore`-backed singleton. Bottom-right cards with success / error styling, click-to-dismiss, ARIA live region.

---

## 6. Production deployment

### Provisioning
- Single Ubuntu 22.04 / 24.04 VM.
- `install/install.sh` is re-runnable. On fresh install it generates `WATIFY_APP_SECRET`, `WATIFY_API_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY` via `openssl rand`. On re-run it preserves them.
- Two systemd units: `watify.service` (uvicorn on a unix socket, 1 worker because the wars singleton is one-process-per-host) + `watify-frontend.service` (`next start -H 127.0.0.1 -p 3000`).
- Both units hardened: `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `ProtectHome=true`, scoped `ReadWritePaths`.

### Network
- Backend binds 127.0.0.1; Nginx fronts it via the unix socket.
- CORS strictly `http://localhost:3000` for dev or `https://<domain>` for prod. No wildcards.
- Cloudflare-aware: `map $http_cf_connecting_ip $watify_real_ip ...` so rate-limit and auth-zone see the real client IP.

### Security headers (Nginx)
HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy (20 features denied, `fullscreen=(self)`), X-Permitted-Cross-Domain-Policies "none", Cross-Origin-Opener-Policy "same-origin", Cross-Origin-Resource-Policy "same-origin". CSP intentionally omitted -- Tailwind + the inline theme-init script would need a hash-based policy that's not worth the friction for v1.1. Target: SecurityHeaders.com grade A.

### Storage
- `app.db` (everything except wars plaintext) -- nightly `sqlite3 .backup` to `/var/lib/watify-backups/`, keep 30 days.
- `whatsapp.db` (legacy plaintext path; only when `WATIFY_SESSION_ENCRYPTION_KEY` is unset).
- `chmod 600` on all three files; `www-data:www-data` ownership.

### Updates
- `install/update.sh` is `git fetch && git reset --hard && uv sync && npm install && npm run build && systemctl restart`. Re-runnable, idempotent.

For the public-deploy hardening checklist (UFW, Cloudflare-only ingress, SSH, backups, secret rotation), see `docs/SECURITY.md`.

---

## 7. Deferred to v1.2 (TKT-0058)

- **Delivery / read receipt tracking**. Wire `@wa.on_message_status` callback on the wars worker, persist `delivery_status` + `delivered_at` + `read_at` columns on `SendAttempt`, render four-state pills (sent / delivered / read / failed) on `/history`.
- **Schema migration tool**. v1.1 cannot ship delivery tracking without first picking a real migration tool -- `SQLModel.metadata.create_all` only creates missing tables, not new columns on existing tables. Likely Alembic. The decision plus the wars hook is bundled in TKT-0058.

Optional v1.2+ candidates (no tickets yet):
- TOTP 2FA on `/login`.
- Hash-based CSP.
- Dependabot or scheduled `uv pip list --outdated` review.
- Per-IP `slowapi` decorator on `/api/send`.

---

## 8. Out of scope (v1.x)
- Multi-user / role-based access.
- WhatsApp group chats (Watify friend groups are an app-side abstraction over individual chats).
- Recurring cron-style schedules.
- Media attachments.
- Receiving messages or bot mode.
- Multi-device fan-out (wars is one process per linked device).
