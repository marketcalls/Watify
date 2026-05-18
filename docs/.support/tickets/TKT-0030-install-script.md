---
id: TKT-0030
title: install/install.sh + update.sh for Ubuntu + Cloudflare + Let's Encrypt
status: open
priority: P1
area: infra
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: I-05, P1, P2, P3
related_tickets: TKT-0024
filed_via: human_manual_input
---

## Summary
Ubuntu 22.04/24.04 production install for Watify, sibling to the dittot install.sh pattern but trimmed to **SQLite-only** -- no Postgres, no Redis, no QuestDB.

Lives at `install/install.sh` inside the Watify repo (the user pointed at `d:/FullStack Options/Day26/install/` -- empty sibling of the repo; we assume that's a misplaced folder and use `Watify/install/` per Dittot's `$APP_ROOT/install/` convention. Confirm with operator before shipping if uncertain).

## Script structure (matches Dittot)

### Pre-flight
- `set -e`, color helpers, root check, Ubuntu OS check.
- Detect re-run via `[ -f /var/www/watify/.env ]` -- preserve SECRET_KEY, JWT secret, Fernet session key, owner_phone.

### Prompts
- Domain (apex or subdomain), regex-validated.
- If apex (2 parts), offer `www.` redirect.
- Let's Encrypt email, regex-validated.
- Confirmation summary -> Y/n.

### Step 1: system packages
- `ufw allow 80/tcp 443/tcp` if active.
- `apt-get update`; install `git curl wget build-essential python3-dev`.
- Node.js 20 via NodeSource.
- Nginx, certbot + python3-certbot-nginx.
- `uv` via `astral.sh/uv/install.sh`, symlinked to `/usr/local/bin/uv`.
- NO Postgres, Redis, QuestDB, Java -- explicitly SQLite-only.

### Step 2: repo
- Clone `https://github.com/marketcalls/Watify.git` to `/var/www/watify` (or `git pull` on re-run).

### Step 3: backend env
- Generate `WATIFY_SECRET_KEY`, `WATIFY_SESSION_ENCRYPTION_KEY` (Fernet), `WATIFY_JWT_*` once; preserve on re-run by parsing `/var/www/watify/backend/.env`.
- Write `backend/.env` with WATIFY_* (host=127.0.0.1, port=8000, app_db=/var/www/watify/backend/app.db, cors_origin=https://$DOMAIN, all rate limits, session_encryption_key, secret_key, jwt secrets).
- Write `frontend/.env.production` with `NEXT_PUBLIC_API_BASE=https://$DOMAIN`.

### Step 4: build
- `cd backend && uv sync`.
- `cd frontend && npm install && npm run build`.

### Step 5: directories + permissions
- `mkdir -p /var/log/watify /var/lib/watify-backups`.
- `chown -R www-data:www-data /var/www/watify /var/log/watify /var/lib/watify-backups`.
- `chmod 600 /var/www/watify/backend/.env`.
- `chmod 600 /var/www/watify/backend/app.db` (if present).
- `chmod 770` on any backend writable dirs.
- Logrotate `/etc/logrotate.d/watify` (100MB, keep 3) on `/var/log/watify/*.log`.

### Step 6: systemd
- `/etc/systemd/system/watify.service` -- backend, unix socket `/run/watify/watify.sock`, 1 worker (`WORKERS=1` -- wars singleton is one-process-per-host), runs `uv run uvicorn app.main:app --uds /run/watify/watify.sock --workers 1 --log-level warning`, `Restart=always`, `User=www-data`, `ReadWritePaths=/var/www/watify /var/log/watify /run/watify /var/lib/watify-backups`, `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`.
- `/etc/systemd/system/watify-frontend.service` -- `next start -H 127.0.0.1 -p 3000`.

### Step 7: Nginx
- `/etc/nginx/conf.d/watify-rate-limit.conf`:
  ```
  map $http_cf_connecting_ip $watify_real_ip {
      default $http_cf_connecting_ip;
      ""      $remote_addr;
  }
  limit_req_zone $watify_real_ip zone=watify_login:10m rate=5r/m;
  limit_conn_zone $watify_real_ip zone=watify_conn:10m;
  ```
- `/etc/nginx/sites-available/watify`:
  - upstream `unix:/run/watify/watify.sock` (keepalive 32) + `127.0.0.1:3000` (keepalive 16).
  - security headers (X-Frame-Options SAMEORIGIN, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy strict-origin-when-cross-origin).
  - gzip on for text/css/json/js/svg.
  - `client_max_body_size 10M`.
  - `limit_conn watify_conn 50`.
  - `/api/auth/login` + `/api/auth/register` -> `limit_req zone=watify_login burst=3 nodelay`.
  - `/api/` catch-all -> backend (backend handles its own rate limits via slowapi).
  - `/_next/static` -> frontend with `expires 1y; Cache-Control "public, immutable"`.
  - `/` -> frontend with WebSocket upgrade headers.
  - Deny `\.env|\.git|\.htaccess|\.ini|\.log|\.sh|\.sql|\.conf` paths.

### Step 8: SSL
- `certbot --nginx -d $DOMAIN [-d www.$DOMAIN] --non-interactive --agree-tos --email $ADMIN_EMAIL --redirect`.
- `/etc/nginx/snippets/ssl-security.conf` with HSTS.
- Auto-renewal cron at `/etc/cron.d/certbot-renewal`.

### Step 9: start
- `systemctl daemon-reload`, enable both units, start, then `journalctl -n 20` if either failed.
- Final banner: URLs + useful commands.

## install/update.sh
- `cd /var/www/watify && git pull`.
- `cd backend && uv sync`.
- `cd frontend && npm install && npm run build`.
- `systemctl restart watify watify-frontend`.

## SQLite specifics for permissions
- The systemd unit user is `www-data`. `app.db` and `whatsapp.db` (legacy) must be owned by `www-data:www-data` with mode `600`. `ReadWritePaths` in the unit grants write to `/var/www/watify` so SQLite can open the WAL/SHM files.
- `app.db` lives at `/var/www/watify/backend/app.db`. WAL mode is acceptable -- single writer matches our single uvicorn worker.

## Cloudflare specifics
- Document in README that the operator should set Cloudflare SSL/TLS mode to "Full (strict)" so the origin Let's Encrypt cert is honored.
- The `map $http_cf_connecting_ip` in `/etc/nginx/conf.d/watify-rate-limit.conf` is what makes rate limiting key on the real visitor IP rather than Cloudflare's IPs.

## Acceptance
- Fresh Ubuntu 22.04 VM + `sudo ./install.sh` answering domain + email = working Watify at `https://<domain>` with hero page, login, register-once.
- `sudo ./install.sh` again is idempotent.
- `sudo ./update.sh` updates a running install in <60s.

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47).
