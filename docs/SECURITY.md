# Watify -- Security & Public-Deploy Hardening

This is the checklist for taking a fresh Watify install from "running on a VM" to "exposed on a public domain". `install/install.sh` covers the application layer; the items below cover the host, network, and operational layers around it.

## What ships in the box (already done)

- **Auth**: argon2id passwords (min 12 chars), JWT HS256 in `httpOnly` + `SameSite=Lax` + `Secure` cookies (`watify_session` + `watify_refresh`), 15-min access + 7-day refresh rotation.
- **Single-user lock**: first `/register` claims the admin slot; subsequent registers return `409 registration_closed`.
- **Rate limits**: `/register` 3/min/IP, `/login` 5/min/IP with 5-in-10-min IP lockout, `/refresh` 30/min/IP, `/api/wa/test/self` 15/min, `/api/wa/test/to` 10/min, `/api/send` 5/min. All 429s carry `Retry-After`.
- **CSRF**: every state-changing `/api/*` call requires `X-Requested-With: XMLHttpRequest` OR a same-origin `Origin`; else `403 csrf_required`. Middleware order: CORS -> Auth -> CSRF (CSRF outermost).
- **CORS**: pinned to a single origin via `WATIFY_CORS_ORIGIN`. No wildcards.
- **Backend bind**: `127.0.0.1` only. Public ingress is Nginx -> unix socket.
- **Session encryption**: when `WATIFY_SESSION_ENCRYPTION_KEY` is set, the wars session blob is Fernet-encrypted at rest in `app.db.wa_session`. When unset, legacy plaintext at `backend/whatsapp.db`.
- **Phone redaction**: backend `PhoneRedactionFilter` rewrites runs of 10-15 digits to `+CC XXXXX <last 4>` in logs. Pair codes log only the length.
- **Nginx security headers** (SecurityHeaders.com grade A target): HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff, X-XSS-Protection, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy (20 features denied + `fullscreen=(self)`), X-Permitted-Cross-Domain-Policies none, COOP same-origin, CORP same-origin. CSP intentionally omitted.
- **systemd hardening** per unit: NoNewPrivileges, PrivateTmp, ProtectSystem=strict, ProtectHome=true, scoped ReadWritePaths.
- **File permissions**: `chmod 600` on `.env`, `app.db`, `whatsapp.db`; `www-data:www-data` ownership of `/var/www/watify`.
- **TLS**: Let's Encrypt via `certbot --nginx`, auto-renewal cron. HSTS preload-ready.

## Verify before flipping DNS to public

These are the items that could bite you in the first 48 hours after going public if they're wrong.

### 1. CORS origin matches your real domain
In `backend/.env`:
```
WATIFY_CORS_ORIGIN=https://watify.example.com
```
Not `http://localhost:3000`. Restart `watify.service`. Confirm with:
```bash
curl -i -X OPTIONS https://watify.example.com/api/wa/connect \
  -H "Origin: https://watify.example.com" \
  -H "Access-Control-Request-Method: POST"
```
Expect `access-control-allow-origin: https://watify.example.com` (NOT `*`).

### 2. UFW
Only 22, 80, 443 open. Everything else closed.
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
sudo ufw status verbose
```

### 3. Cloudflare-only ingress (recommended)
`install.sh` already configures Nginx to read `$http_cf_connecting_ip` so the backend sees real client IPs. To actually benefit from Cloudflare's WAF you must reject direct origin hits. Two options:

- **At Nginx**: whitelist Cloudflare IP ranges in `/etc/nginx/conf.d/cf-allow.conf` (allow each CIDR from <https://www.cloudflare.com/ips/> + `deny all;` in the `server` block). Refresh quarterly.
- **At UFW**: replace `allow 443/tcp` with `allow from <each-cf-cidr> to any port 443 proto tcp`.

Without this, an attacker can `dig +short watify.example.com @1.1.1.1` to find the origin IP and bypass Cloudflare entirely.

### 4. First-boot race -- claim the admin slot immediately
`install.sh` does NOT pre-create your user. The moment `watify.service` starts, `/register` is open. Anybody who beats you to it owns the box.

Right after the install banner finishes:
```bash
curl -s https://watify.example.com/api/health
# expect {"registered":false,...}
```
Then in a browser, open `https://watify.example.com/register` and create your account. Re-check:
```bash
curl -s https://watify.example.com/api/health
# expect {"registered":true,...}
```
Now `/register` returns 409 to anyone else.

### 5. SSH hardening
Edit `/etc/ssh/sshd_config`:
```
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
```
`sudo systemctl reload ssh`. Add `fail2ban`:
```bash
sudo apt install -y fail2ban
```
Default jail covers sshd; that's enough.

### 6. Backups
`app.db` carries everything except the wars session bytes (which are encrypted in the same DB when `WATIFY_SESSION_ENCRYPTION_KEY` is set). Nightly off-host backup:
```bash
sudo crontab -e -u www-data
```
```cron
0 2 * * *  sqlite3 /var/www/watify/backend/app.db ".backup '/var/lib/watify-backups/app.db.$(date +\%F).bak'"
# Optional: rclone copy /var/lib/watify-backups/ remote:watify-backups/
```
Rotate / prune older than 30 days. Test a restore once before you need one.

### 7. Secret rotation plan
If `WATIFY_APP_SECRET` ever leaks (forgot to chmod 600 before scp, env file accidentally pushed, host compromise), every issued JWT is forgeable. Watify has no token revocation list (single-user app -- the simplest revocation is "change the secret").

Rotation:
```bash
sudo sed -i "s|^WATIFY_APP_SECRET=.*|WATIFY_APP_SECRET=$(openssl rand -hex 32)|" /var/www/watify/backend/.env
sudo systemctl restart watify.service
```
You'll be logged out; log back in. All existing sessions invalidated.

Same procedure for `WATIFY_API_KEY` (used for the canary fixture allowlist).

`WATIFY_SESSION_ENCRYPTION_KEY` is different -- rotating it without first decrypting the existing session blob loses your WhatsApp pairing. Only rotate after a fresh re-pair.

## Optional hardening (nice but not required)

| Item | Why | Effort |
|---|---|---|
| TOTP 2FA on `/login` | Single-user means the blast radius is just your account, but 2FA is cheap. | Half a day. Add `pyotp`, render the QR on first setup. |
| Hash-based CSP | Currently omitted to keep grade A friction-free. Tailwind + the inline theme-init script need explicit hashes. | A few hours; revisit if SecurityHeaders.com grade A+ matters. |
| Dependabot or scheduled `uv pip list --outdated` | No automated patch monitoring today. | One commit -- enable GitHub Dependabot in repo settings. |
| Per-IP `slowapi` decorator on `/api/send` | `/send` is gated by the 3-30s per-recipient delay + 20-cap + one-job-at-a-time, but a per-IP knob costs nothing. | One decorator + one env var. |
| `HSTS preload` submission | Tells browsers to refuse plaintext HTTP for your domain forever. | One-shot. Submit at <https://hstspreload.org/>. |

## Things explicitly out of scope

- **WhatsApp ban risk**. WhatsApp will unlink the device or ban the account if send patterns look bot-like. The 3-30s per-recipient delay + 20-contact cap + one-job-at-a-time + soft daily-cap reminder (100/24h) are the mitigations; there is no perfect protection. See `docs/wars.md` "WhatsApp Terms of Service -- practical risk note".
- **Multi-tenancy**. Out of scope for v1.x. Anyone with the credentials owns the host's WhatsApp session.
- **Audit trail**. Send history is operator-visible only; there is no append-only audit log for compliance scenarios.

## Reporting

Found a security issue? Open a private security advisory at <https://github.com/marketcalls/Watify/security/advisories>. Do not file a public issue.
