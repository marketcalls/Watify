# Watify

Single-user WhatsApp notification service for sending messages to curated friend watchlists. Built by a multi-agent loop; pipeline state and full ticket trail live in `docs/.support/`.

## Features
- Pair WhatsApp via QR scan from a browser at `/connect`, or from a terminal for headless boxes.
- Multiple named friend groups, hard-capped at **20 contacts** each.
- Bulk-add contacts (max 20 rows per upload, all-or-nothing validation, duplicates skipped).
- Send Now or schedule a one-time future send. Per-recipient random delay between user-configured `min/max` seconds (default 3-30s). One message at a time.
- Live job + per-attempt history with phone numbers redacted everywhere except the database.

## Stack
- **Backend**: Python 3.13+ (Python 3.14 tested), FastAPI, SQLModel + SQLite, APScheduler with SQLAlchemyJobStore, `wars 0.1.x` for WhatsApp.
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, SWR for data.
- **Tooling**: `uv` for Python, `npm` for Node.

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
cp .env.example .env       # optional; defaults work
uv sync
cd ..

# Frontend
cd frontend
cp .env.local.example .env.local
npm install --no-audit --no-fund
cd ..
```

## Run

You need two terminals: one for the backend on `:8000`, one for the frontend on `:3000`.

### Windows (PowerShell)
```powershell
# Terminal 1
.\scripts\dev-backend.ps1

# Terminal 2
.\scripts\dev-frontend.ps1
```

### POSIX
```bash
# Terminal 1
make dev-backend

# Terminal 2
make dev-frontend
```

### Direct (no helper scripts)
```bash
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:3000.

## Pair WhatsApp

**Web (recommended)**: with both dev servers running, open http://localhost:3000/connect and scan the QR with WhatsApp on your phone (WhatsApp settings -> Linked devices -> Link a device).

**CLI (headless)**: pair without a browser by running the terminal-ASCII-QR flow.
```powershell
.\scripts\pair.ps1
```
```bash
make pair
```
The paired session lands in `backend/whatsapp.db` (gitignored). Subsequent backend startups reuse it.

## Where data lives
| Path | What | Tracked? |
|---|---|---|
| `backend/.env` | Local config (`WATIFY_*`). | gitignored |
| `frontend/.env.local` | Frontend public env. | gitignored |
| `backend/app.db` | Friend groups, contacts, send jobs, attempts. SQLAlchemy + APScheduler. | gitignored |
| `backend/whatsapp.db` (+ `-wal`, `-shm`) | wars session keys for the linked device. **Sensitive.** | gitignored |
| `docs/.support/logs/backend.log` | Backend stdout/stderr (phone-redacted). | gitignored |
| `docs/.support/conversations/` | Per-iteration agent transcripts. | tracked |
| `docs/.support/tickets/` | Open / resolved / verified issues. | tracked |

## Troubleshooting

### `localhost:3000` shows a different app
If the browser shows a non-Watify page on `localhost:3000` (404 / login / dashboard from an unrelated project), an unrelated service worker is intercepting requests for that origin. Curl will confirm Watify is in fact running (`curl http://localhost:3000` shows Watify's HTML).

Fix in Chrome:
1. DevTools (F12) -> Application -> Service Workers
2. Find the entry scoped to `localhost:3000/` and click Unregister.
3. Reload.

Or visit `chrome://serviceworker-internals/` for a global view.

### `whatsapp.db` claims to be missing
The wars session file is created on first `connect()`. If `/connect` fails immediately with an "error" state and a permission complaint, check `backend/` is writable.

### Port already in use
Both dev servers bind to localhost. If `:8000` or `:3000` is taken, kill the holding process first (`netstat -ano | grep :8000`).

### Account suspended
WhatsApp may unlink the device or ban the account if send volume looks bot-like. See `docs/wars.md` "WhatsApp Terms of Service - practical risk note" for the thresholds. The Dashboard shows a soft-cap reminder at 100 sent in 24h.

## Pointers
- `docs/.support/REQUIREMENTS.md` - product contract.
- `docs/.support/AGENTS.md` - how the multi-agent loop builds and maintains the app.
- `docs/.support/PIPELINE.md` - current phase and ticket queue.
- `docs/wars.md` - WhatsApp client library reference.

## Disclaimer
Uses the unofficial `wars` WhatsApp client. Not affiliated with WhatsApp or Meta. Personal / low-volume use only.
