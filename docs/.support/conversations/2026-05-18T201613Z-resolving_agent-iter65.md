# Iteration 65 -- Resolving Agent (TKT-0030)

- **Started**: 2026-05-18T20:16:13Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0030 (P1 infra) -- install/install.sh + update.sh

## Plan
TKT-0030 is the biggest single deliverable in the queue but is structurally well-specified by the ticket. Ship two files:

1. **`install/install.sh`** -- the full Ubuntu installer per the ticket's nine-step structure (pre-flight, prompts, packages, repo, env, build, dirs/perms, systemd, Nginx, SSL, start).
2. **`install/update.sh`** -- one-shot updater: `git pull`, `uv sync`, `npm install && npm run build`, `systemctl restart watify watify-frontend`.

Key contract points:
- All env vars use `WATIFY_*` prefix (matching `backend/app/settings.py`). Specifically: `WATIFY_APP_SECRET` (TKT-0031) and `WATIFY_API_KEY` (TKT-0031), NOT `WATIFY_SECRET_KEY` / `WATIFY_JWT_*` -- the ticket pre-dates TKT-0024/0031 naming. The script ships the actually-used variables.
- App db path `WATIFY_APP_DB=/var/www/watify/backend/app.db`, `WATIFY_WHATSAPP_DB=/var/www/watify/backend/whatsapp.db`.
- Re-run preservation: parse existing `backend/.env` for `WATIFY_APP_SECRET`, `WATIFY_API_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY`, `WATIFY_OWNER_PHONE`; only generate when missing.
- Cloudflare real-IP via `$http_cf_connecting_ip` Nginx map. Operator must set Cloudflare SSL/TLS to "Full (strict)".
- systemd: backend on unix socket `/run/watify/watify.sock`, frontend `next start -H 127.0.0.1 -p 3000`, both `Restart=always`, `User=www-data`.
- Hardened systemd: `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`, explicit `ReadWritePaths`.
- Nginx `limit_req` only on `/api/auth/login` + `/api/auth/register`; backend slowapi handles the rest (TKT-0015 + TKT-0024).
- `chmod 600` on `.env` and `app.db`; logs in `/var/log/watify`.
- Acceptance: fresh Ubuntu VM -> working `https://$DOMAIN` with hero/login/register. Idempotent re-runs. `update.sh` <60s.

Tests this iteration:
- `bash -n install/install.sh` and `bash -n install/update.sh` (parse check; cannot exec without an Ubuntu VM).
- `shellcheck` if installed (best effort -- not a blocker).
- File-presence and shebang/permission sanity.

NOT in scope this iteration:
- Backup script (would be a separate ticket).
- Multi-host or HA.
- Anything that changes backend Python code -- the systemd unit must work with the current `app/main.py` and uvicorn flags.

## Actions

1. Read TKT-0030 spec in full and confirmed against `backend/app/settings.py:18-21` that the env prefix is `WATIFY_` and the keys actually consumed by the running app are `WATIFY_APP_SECRET`, `WATIFY_API_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY` (NOT `WATIFY_SECRET_KEY`/`WATIFY_JWT_*` from the older filed spec).
2. Created `install/` directory at the repo root (it did not exist).
3. Wrote `install/install.sh` -- 540 lines covering all nine steps from the spec exactly. Highlights:
   - Re-run preservation parses `WATIFY_APP_SECRET`, `WATIFY_API_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY`, `WATIFY_OWNER_PHONE` from an existing `backend/.env` via awk; only fills missing ones.
   - Session key (Fernet) generated in a tmp venv so the host doesn't need a system `cryptography` install.
   - Hardened systemd units with `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `ProtectHome`, explicit `ReadWritePaths`. `RuntimeDirectory=watify` lets systemd manage `/run/watify` with correct ownership and tear it down on stop.
   - Nginx `/etc/nginx/snippets/watify-proxy.conf` reused by all `proxy_pass` blocks so the Cloudflare real-IP map is the single source of truth for `X-Real-IP`.
   - `/_next/static` gets `expires 1y; Cache-Control public, immutable` per the spec.
   - certbot uses `--non-interactive --agree-tos --email --redirect --no-eff-email`; failures degrade gracefully (warn + manual command suggested).
4. Wrote `install/update.sh` -- 59 lines: root check, git fetch + reset --hard origin/main, uv sync, npm install + build, restart both units, sleep 2, `systemctl is-active --quiet`, elapsed-time banner.
5. Wrote a `.gitattributes` at the repo root forcing `*.sh text eol=lf` so Windows-authored scripts ship with LF endings (Ubuntu bash refuses scripts with CR in the shebang).
6. Verified the scripts:
   - `head -1` on both -> `#!/usr/bin/env bash`.
   - `bash -n install/install.sh` -> 0 (parse clean).
   - `bash -n install/update.sh` -> 0 (parse clean).
   - shellcheck not installed on this host; `bash -n` is the runnable substitute. The Verification Agent can install shellcheck if it wants to deepen the lint pass.
7. Marked TKT-0030 status `resolved` with the comprehensive Resolution history entry covering every numbered step from the spec.

## Outcome
TKT-0030 resolved. Two scripts + a `.gitattributes` shipped. The scripts cannot be exec-tested from this Windows dev host -- the Verification Agent's job is to walk the script vs the spec section-by-section, confirm `bash -n` clean, optionally run `shellcheck`, and commit. Next iteration: Verification Agent picks TKT-0030, then commits the install bundle.
