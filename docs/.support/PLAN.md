# Watify — Master Plan

Source: `REQUIREMENTS.md`. Items are dependency-ordered top to bottom. The Backend Agent and Frontend Agent each consume their next undone item per iteration. `[ ]` = pending, `[~]` = in progress, `[x]` = done.

## Backend Items (B-NN)

- **[x] B-01** — Scaffold backend project. *(done iter2)*
  - Cwd: `backend/`. `uv init --package app --no-readme` plus `uv add fastapi uvicorn[standard] pydantic-settings`.
  - Files: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/main.py`.
  - `app.main:app` is a FastAPI app exposing `GET /api/health -> {"ok": true, "service": "watify"}`.
  - CORS allowlist `http://localhost:3000`.
  - Acceptance: `uv run uvicorn app.main:app --port 8000` boots; `curl localhost:8000/api/health` returns `{"ok": true, ...}`.

- **[x] B-02** — SQLAlchemy 2 + SQLModel data layer. *(done iter4)*
  - Add deps: `sqlmodel`, `alembic` (deferred — start with `SQLModel.metadata.create_all`).
  - Models: `FriendGroup(id, name, created_at)`, `Contact(id, group_id FK, name, phone_e164, created_at)`, `SendJob(id, group_id FK, message, status, scheduled_at, started_at, finished_at, min_delay_s, max_delay_s)`, `SendAttempt(id, job_id FK, contact_id FK, sent_at, status, error)`.
  - SQLite file `backend/app.db`. Session factory in `app/db.py`.
  - Acceptance: tables created on startup; basic `select` round-trip via a smoke script under `backend/scripts/`.

- **[x] B-03** — Friend Groups CRUD endpoints. *(done iter6)*
  - `POST /api/groups`, `GET /api/groups`, `GET /api/groups/{id}`, `PATCH /api/groups/{id}`, `DELETE /api/groups/{id}`.
  - Contact endpoints under group: `POST /api/groups/{id}/contacts`, `DELETE /api/groups/{id}/contacts/{cid}`.
  - **Enforce hard cap of 20** at insert; return HTTP 409 with body `{"error": "group_full", "max": 20}`.
  - Phone normalization helper using wars JID normalization rules (digits only, optional `+`).
  - Acceptance: 21st contact insert returns 409; CRUD round-trips work via httpie.

- **[x] B-04** — Bulk upload endpoint. *(done iter7)*
  - `POST /api/groups/{id}/contacts/bulk` accepts JSON `{"contacts": [{"name": "...", "phone": "..."}, ...]}` (max 20 entries per request).
  - All-or-nothing: if any row is invalid OR if adding the batch would push the group over 20, reject the whole batch with the offending indices listed.
  - Acceptance: valid batch inserts atomically; one bad row rejects the whole batch.

- **[x] B-05** — `wars` integration singleton + connection endpoints. *(done iter8)*
  - `app/whatsapp.py` lazy singleton per wars.md §7 with `Lock()`, `db_path="whatsapp.db"`, `OWNER` resolved post-pair.
  - Endpoints: `POST /api/wa/connect` (start), `POST /api/wa/disconnect`, `GET /api/wa/state` → `{state: disconnected|pairing|ready|error, qr_data_url: str|null}`.
  - Cache QR data URL via `@wa.on_qr` callback; clear when ready.
  - Acceptance: state machine moves disconnected → pairing → ready after QR scan; `wa.send("ping")` (test-to-self) succeeds.

- **[x] B-06** — Test message endpoints. *(done iter10)*
  - `POST /api/wa/test/self` — `wa.send(text)`; routes to owner.
  - `POST /api/wa/test/to` — `{"phone": "...", "text": "..."}` → `wa.send(phone, text)`.
  - Validation: backend rejects sends when state != ready (HTTP 409).
  - Acceptance: both endpoints succeed once paired.

- **[x] B-07** — Send-to-group orchestrator + APScheduler. *(done iter12)*
  - APScheduler with `SQLAlchemyJobStore(url="sqlite:///app.db", tablename="apscheduler_jobs")`.
  - `POST /api/send` body: `{group_id, message, schedule: "now" | ISO8601, min_delay_s: 3, max_delay_s: 30}`.
  - Behavior: for each contact in group, sequentially: pick random delay ∈ [min,max], sleep, `wa.send(phone, message)`, persist `SendAttempt`. One message at a time per job. Per-job worker thread.
  - Validation: `1 <= min_delay_s <= max_delay_s <= 300`.
  - `GET /api/jobs`, `GET /api/jobs/{id}` returns job + attempts. `DELETE /api/jobs/{id}` cancels pending.
  - Acceptance: scheduled job survives restart; immediate job sends to a 2-contact group with observable delays in attempts.

- **[x] B-08** — Hardening + logging. *(done iter15)*
  - Structured logging via `logging` to `docs/.support/logs/backend.log`. Redact full phone numbers (`+91XXXXX1234`).
  - Settings via `pydantic-settings` reading `backend/.env`.
  - Global exception handler returning JSON errors.
  - Acceptance: error responses are JSON; logs do not contain unredacted numbers.

## Frontend Items (F-NN)

- **[x] F-01** — Scaffold Next.js (latest) frontend. *(done iter3)*
  - `npx create-next-app@latest frontend --ts --tailwind --app --src-dir --import-alias "@/*" --no-eslint --use-npm` (run with `--yes` equivalents to avoid prompts).
  - `.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000`.
  - Strip default landing page; add a top nav with links to Dashboard / Connect / Groups / Send / History.
  - Acceptance: `npm run dev` boots on :3000; nav renders; no console errors.

- **[x] F-02** — API client + state hooks. *(done iter5)*
  - Shipped: `src/lib/api.ts` typed fetch wrapper + `ApiError`, `src/hooks/useHealth.ts` (SWR 3s refresh), `src/components/BackendStatus.tsx`, Dashboard wires it.
  - Deferred: `useGroups.ts` moved to F-04 (depends on B-03 `/api/groups`). `useWaState.ts` lands with F-03. `useJobs.ts` lands with F-06.

- **[x] F-03** — `/connect` page (WhatsApp pairing). *(done iter9)*
  - Polls `GET /api/wa/state` every 2s while `disconnected` or `pairing`.
  - Shows QR `<img>` from `qr_data_url` once present.
  - When `ready`, shows owner number + Disconnect button.
  - Acceptance: full pair-flow works end-to-end with a real phone.

- **[x] F-04** — `/groups` page. *(done iter11)*
  - List groups; create new group form; click a group to drill into its contacts.
  - Contact list shows count `X / 20`; Add Contact disabled at 20.
  - Bulk upload modal: paste CSV (`name,phone`), preview, submit; surfaces row-level errors.
  - Acceptance: 20-cap enforced visually and by backend; bulk all-or-nothing.

- **[x] F-05** — `/send` page. *(done iter13)*
  - Choose group dropdown, message textarea, send mode toggle (Now / Schedule).
  - Schedule mode: native datetime input.
  - Delay controls: min/max sliders (range 1–300), default 3–30, with helper text "random per-recipient delay".
  - Submit → POST `/api/send`; show resulting job id.
  - Acceptance: schedule and immediate sends both create jobs visible on /history.

- **[x] F-06** — `/history` page (and `/`). *(done iter14)*
  - Table of recent jobs (status, group, message preview, scheduled_at, progress X/Y, cancel button if pending/scheduled).
  - Per-job detail drawer with attempt-level status (sent/failed/error).
  - Dashboard at `/` shows: WA state badge, total contacts, jobs today, last 24h sent count, link to history.
  - Acceptance: real-time-ish updates via SWR refetch every 3s.

- **[ ] F-07** — UX polish: empty states, error toasts, soft-cap reminder banner if daily send count > 100.

## Infra / Cross-cutting (I-NN)

- **[ ] I-01** — `backend/.env.example` and `frontend/.env.local.example` checked in.
- **[ ] I-02** — Top-level `Makefile` or PowerShell scripts: `dev-backend`, `dev-frontend`, `pair` (one-shot wars pair CLI).
- **[ ] I-03** — README updated with full local-run instructions once F-07 lands.
- **[ ] I-04** — `wars` install: verify `pip install wars` works in the uv env. If not, document fallback (build from source via maturin per wars.md §"Building from source").

## Done definition
PLAN is done when every `B-NN` and `F-NN` is `[x]`, all open tickets are `verified`, and the dashboard at `/` answers correctly with the backend reachable.
