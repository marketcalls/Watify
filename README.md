# Watify

Single-user WhatsApp notification service for sending messages to curated friend watchlists. Built by a multi-agent loop; pipeline state and full ticket trail live in `docs/.support/`.

## Features
- Pair WhatsApp via browser QR scan or 8-character pair-code (Settings -> Linked devices -> Link with phone number).
- Multiple named friend groups, hard-capped at **20 contacts** each.
- Bulk-add contacts (max 20 rows per upload, all-or-nothing validation, duplicates skipped).
- Send Now or schedule a one-time future send. Per-recipient random delay between user-configured `min/max` seconds (default 3-30s). One message at a time per group; persistent across restarts via APScheduler.
- Live job + per-attempt history. Phone numbers redacted in logs.
- Single-user auth: argon2id password, JWT in httpOnly cookies, CSRF gate. The first `/register` claims the lone admin slot; subsequent register attempts return `409 registration_closed`.
- Dark + light theme toggle (persists in `localStorage`, dark by default).
- Test-connection button on `/connect` sends a canary to your own number.

## Stack
- **Backend**: Python 3.13+ (3.14 tested), FastAPI, SQLModel + SQLite, APScheduler with SQLAlchemyJobStore, `wars 0.1.x` for WhatsApp.
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, SWR for data.
- **Tooling**: `uv` for Python, `npm` for Node, Biome for lint+format, Vitest for unit tests, Playwright for e2e.

## Prereqs
| Tool | Min version | Notes |
|---|---|---|
| Python | 3.13 | Installed automatically by `uv` if missing. |
| Node | 20 LTS | 24.x tested locally. |
| `uv` | 0.9 | `pip install uv` or platform installer. |
| `npm` | 10 | Ships with Node. |
| `gh` | optional | Only needed for `git push origin` from the loop's Verification Agent. |

## First-time setup
```bash
git clone https://github.com/marketcalls/Watify.git
cd Watify

# Backend
cd backend
cp .env.example .env       # optional; defaults work for local dev
uv sync
cd ..

# Frontend
cd frontend
cp .env.local.example .env.local
npm install --no-audit --no-fund
cd ..
```

Local dev runs fine without `WATIFY_APP_SECRET` (auth endpoints return `503 auth_not_configured`). Set it once you want to claim a user and use the full UI:
```bash
# In backend/.env
WATIFY_APP_SECRET=<64 hex chars from `openssl rand -hex 32`>
WATIFY_API_KEY=<64 hex chars from `openssl rand -hex 32`>
WATIFY_SESSION_ENCRYPTION_KEY=<44-char Fernet key>   # optional but recommended
```
Generate the Fernet key with `uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

## Run

Two terminals: one for the backend on `:8000`, one for the frontend on `:3000`.

### Windows (PowerShell)
```powershell
.\scripts\dev-backend.ps1     # terminal 1
.\scripts\dev-frontend.ps1    # terminal 2
```

### POSIX
```bash
make dev-backend              # terminal 1
make dev-frontend             # terminal 2
```

### Direct (no helper scripts)
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Open http://localhost:3000. On first visit, click **Get started** -> create your single admin user -> log in.

## Pair WhatsApp

**Web (recommended)**: with both dev servers running and the user registered, open `/connect`. Two modes via the toggle:
- **Scan QR** -- default. WhatsApp rotates the code every 30s; the page polls and re-renders automatically.
- **Use pair code instead** -- enter your E.164 phone, get an 8-char code, type it into WhatsApp under Linked devices -> Link with phone number.

**CLI (headless)**:
```bash
make pair                     # POSIX
.\scripts\pair.ps1            # Windows
```
The paired session lands in `backend/whatsapp.db` (or as an encrypted blob in `app.db` if `WATIFY_SESSION_ENCRYPTION_KEY` is set). Subsequent backend startups reuse it.

**Disconnect**: the red Disconnect button on `/connect` opens a modal and fully wipes the saved session. The next pair requires a fresh QR or pair code -- there is no soft-disconnect.

## Where data lives
| Path | What | Tracked? |
|---|---|---|
| `backend/.env` | Local config (`WATIFY_*`). | gitignored |
| `frontend/.env.local` | Frontend public env. | gitignored |
| `backend/app.db` | Users, friend groups, contacts, send jobs, attempts, scheduler state, encrypted wars session blob. | gitignored |
| `backend/whatsapp.db` (+ `-wal`, `-shm`) | Legacy plaintext wars session (only when `WATIFY_SESSION_ENCRYPTION_KEY` is unset). **Sensitive.** | gitignored |
| `docs/.support/logs/backend.log` | Backend stdout/stderr (phone-redacted). | gitignored |
| `docs/.support/conversations/` | Per-iteration agent transcripts. | tracked |
| `docs/.support/tickets/` | Open / resolved / verified issues. | tracked |

## Production install (Ubuntu 22.04 / 24.04)

`install/install.sh` is a re-runnable one-shot that provisions a public-facing deploy:
- Apt deps (git, nginx, certbot, build-essential), Node 20, `uv`.
- Clones the repo to `/var/www/watify`, runs `uv sync` + `npm install && npm run build`.
- Generates `WATIFY_APP_SECRET`, `WATIFY_API_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY` on fresh install. **Preserves them on re-run.**
- Writes two hardened systemd units (`watify.service` on a unix socket, `watify-frontend.service` on 127.0.0.1:3000).
- Writes Nginx config with Cloudflare-aware real-IP map, per-IP rate-limit zone on `/api/auth/*`, security headers stack (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, CORP, X-Permitted-Cross-Domain-Policies -- SecurityHeaders.com grade A without CSP).
- Provisions Let's Encrypt via `certbot --nginx`; auto-renewal cron.
- Logrotate (100MB, keep 3). `chmod 600` on `.env`, `app.db`, `whatsapp.db`. `www-data:www-data` ownership.

```bash
sudo bash install/install.sh
```

To deploy a new version on a host that's already provisioned:
```bash
sudo bash install/update.sh
```

After first `install.sh`, immediately open `https://your-domain/register` to claim the admin slot before the door closes.

See **`docs/SECURITY.md`** for the public-deploy hardening checklist (UFW, Cloudflare-only ingress, SSH, backup, secret rotation).

## Troubleshooting

### `localhost:3000` shows a different app
A service worker from another project is intercepting requests. DevTools (F12) -> Application -> Service Workers -> Unregister anything scoped to `localhost:3000/` -> reload. Or visit `chrome://serviceworker-internals/`.

### "Failed to fetch" overlay on /connect
Backend was briefly unreachable (dev reload, browser extension block). Hard-refresh the page. As of TKT-0059, the click handlers toast the failure instead of overlaying.

### Disconnect bounces back to connected
Pre-TKT-0050 bug. Make sure you're on `main` past commit `a8f3557`. Current Disconnect = full unlink + session wipe; there is no soft-disconnect any more.

### Port already in use
Both dev servers bind to localhost. If `:8000` or `:3000` is taken, kill the holding process (`netstat -ano | findstr :8000` on Windows, `lsof -i :8000` on POSIX).

### Account suspended
WhatsApp may unlink the device or ban the account if send volume looks bot-like. See `docs/wars.md` "WhatsApp Terms of Service - practical risk note" for the thresholds. The dashboard shows a soft-cap reminder at 100 sent in 24h.

## Pointers
- `docs/PRD.md` -- product spec for what shipped in v1.1.
- `docs/SECURITY.md` -- public-deploy hardening checklist.
- `docs/wars.md` -- WhatsApp client library reference.
- `docs/.support/REQUIREMENTS.md` -- original contract the agents built against.
- `docs/.support/AGENTS.md` -- how the multi-agent loop builds and maintains the app.
- `docs/.support/PIPELINE.md` -- current phase and ticket queue.

## Disclaimer
Uses the unofficial `wars` WhatsApp client. Not affiliated with WhatsApp or Meta. Personal / low-volume use only.
