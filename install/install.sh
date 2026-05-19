#!/usr/bin/env bash
#
# Watify -- single-host Ubuntu production installer.
#
# Tested target: Ubuntu 22.04 LTS and 24.04 LTS.
# Stack: FastAPI + uvicorn (uv) on a unix socket + Next.js (npm) on
# 127.0.0.1:3000, both fronted by Nginx with Let's Encrypt + a
# Cloudflare real-IP map. SQLite only -- no Postgres, Redis, or other
# datastore.
#
# Re-runs are safe. WATIFY_APP_SECRET, WATIFY_API_KEY,
# WATIFY_SESSION_ENCRYPTION_KEY and WATIFY_OWNER_PHONE are preserved
# from an existing /var/www/watify/backend/.env when present so the
# user's already-paired WhatsApp session and provisioned admin account
# survive a re-install.

set -euo pipefail

# ------------------------------------------------------------------
# Color helpers
# ------------------------------------------------------------------
if [ -t 1 ]; then
    C_BOLD=$'\033[1m'; C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
    C_YEL=$'\033[33m'; C_BLUE=$'\033[34m'; C_RESET=$'\033[0m'
else
    C_BOLD=""; C_RED=""; C_GREEN=""; C_YEL=""; C_BLUE=""; C_RESET=""
fi

step()  { echo; echo "${C_BOLD}${C_BLUE}==> $*${C_RESET}"; }
ok()    { echo "${C_GREEN}    [ok]${C_RESET} $*"; }
warn()  { echo "${C_YEL}    [warn]${C_RESET} $*"; }
die()   { echo "${C_RED}    [error]${C_RESET} $*" >&2; exit 1; }
info()  { echo "    $*"; }

# ------------------------------------------------------------------
# Pre-flight
# ------------------------------------------------------------------
APP_ROOT=/var/www/watify
LOG_DIR=/var/log/watify
BACKUP_DIR=/var/lib/watify-backups
RUN_DIR=/run/watify
# uv-managed Python install root. MUST sit outside /root so that
# `chmod 700 /root` (Ubuntu default) does not block www-data from
# resolving the venv's python3 symlink chain at service start.
UV_PYTHON_DIR=/opt/uv-python
REPO_URL=https://github.com/marketcalls/Watify.git
SVC_USER=www-data
SVC_GROUP=www-data

step "Watify installer pre-flight"

if [ "$(id -u)" -ne 0 ]; then
    die "must be run as root (try: sudo $0)"
fi

if [ ! -f /etc/os-release ]; then
    die "cannot detect OS (no /etc/os-release)"
fi
. /etc/os-release
if [ "${ID:-}" != "ubuntu" ]; then
    die "this installer targets Ubuntu (detected ID=$ID)"
fi
case "${VERSION_ID:-}" in
    22.04|24.04) ok "Ubuntu $VERSION_ID detected" ;;
    *) warn "untested Ubuntu version $VERSION_ID -- continuing" ;;
esac

REINSTALL=no
if [ -f "$APP_ROOT/backend/.env" ]; then
    REINSTALL=yes
    ok "existing install detected at $APP_ROOT (re-run mode: secrets will be preserved)"
fi

# ------------------------------------------------------------------
# Prompts
# ------------------------------------------------------------------
step "Configuration"

read -r -p "Domain to serve Watify on (e.g. watify.example.com): " DOMAIN
if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$ ]]; then
    die "invalid domain: $DOMAIN"
fi

DOTS=$(awk -F. '{print NF-1}' <<< "$DOMAIN")
WANT_WWW=no
if [ "$DOTS" -eq 1 ]; then
    read -r -p "Also serve www.$DOMAIN? [y/N]: " ans
    [[ "${ans,,}" == "y" ]] && WANT_WWW=yes
fi

read -r -p "Email for Let's Encrypt: " LE_EMAIL
if ! [[ "$LE_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
    die "invalid email: $LE_EMAIL"
fi

echo
echo "${C_BOLD}Summary${C_RESET}"
echo "  Domain     : $DOMAIN${WANT_WWW:+ (+ www.$DOMAIN redirect)}"
echo "  Email      : $LE_EMAIL"
echo "  App root   : $APP_ROOT"
echo "  Service    : $SVC_USER:$SVC_GROUP"
echo "  Mode       : $([ "$REINSTALL" = yes ] && echo "re-install (preserving secrets)" || echo "fresh install")"
echo
read -r -p "Proceed with install? [y/N]: " ans
[[ "${ans,,}" != "y" ]] && die "aborted by operator"

# ------------------------------------------------------------------
# Step 1: system packages
# ------------------------------------------------------------------
step "Step 1/9 -- system packages"

if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        ufw allow 80/tcp >/dev/null
        ufw allow 443/tcp >/dev/null
        ok "ufw: allowed 80/tcp and 443/tcp"
    fi
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    git curl wget ca-certificates gnupg \
    build-essential python3-dev \
    nginx certbot python3-certbot-nginx \
    logrotate
ok "core packages installed"

# Node.js 20 via NodeSource
if ! command -v node >/dev/null 2>&1 || ! node -v | grep -q "^v20\."; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
    apt-get install -y -qq nodejs
fi
ok "Node.js $(node -v) installed"

# uv (Astral). The systemd unit uses ProtectHome=true, which hides
# /root from the service even if /usr/local/bin/uv is a symlink into
# /root/.local/bin. So we (a) try to install uv directly under
# /usr/local/bin, and (b) idempotently copy the real binary to
# /usr/local/bin/uv every run -- a stale symlink from an older
# installer gets replaced with a real file.
if ! command -v uv >/dev/null 2>&1; then
    curl -fsSL https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh >/dev/null 2>&1 || true
fi
UV_BIN="$(command -v uv || true)"
if [ -z "$UV_BIN" ]; then
    for cand in /usr/local/bin/uv /root/.local/bin/uv "$HOME/.local/bin/uv"; do
        if [ -x "$cand" ]; then UV_BIN="$cand"; break; fi
    done
fi
[ -n "$UV_BIN" ] && [ -x "$UV_BIN" ] || die "uv install failed; install manually then re-run"
if [ ! -f /usr/local/bin/uv ] || [ -L /usr/local/bin/uv ]; then
    cp -f "$UV_BIN" /usr/local/bin/uv
    chmod 0755 /usr/local/bin/uv
fi
ok "uv $(/usr/local/bin/uv --version | awk '{print $2}') installed at /usr/local/bin/uv"

# ------------------------------------------------------------------
# Step 2: repository
# ------------------------------------------------------------------
step "Step 2/9 -- repository"

if [ "$REINSTALL" = yes ] && [ -d "$APP_ROOT/.git" ]; then
    git -C "$APP_ROOT" fetch --quiet origin
    git -C "$APP_ROOT" reset --hard origin/main --quiet
    ok "repo updated to latest origin/main"
else
    mkdir -p "$(dirname "$APP_ROOT")"
    [ -d "$APP_ROOT" ] && rm -rf "$APP_ROOT"
    git clone --quiet "$REPO_URL" "$APP_ROOT"
    ok "repo cloned to $APP_ROOT"
fi

# Python interpreter for the service. We pin uv's python install dir
# to $UV_PYTHON_DIR (default /opt/uv-python) because uv's default
# (~/.local/share/uv/python under root's home) lives behind /root,
# which is mode 0700 on Ubuntu -- the service runs as www-data and
# cannot traverse /root, so the venv's python3 symlink chain fails
# to canonicalize at boot. /opt is world-traversable and outside
# ProtectHome's scope.
PY_REQ=$(awk -F'"' '/^requires-python/ {gsub(/[<>=! ]/, "", $2); print $2; exit}' "$APP_ROOT/backend/pyproject.toml" 2>/dev/null || true)
[ -z "$PY_REQ" ] && PY_REQ=3.14
mkdir -p "$UV_PYTHON_DIR"
UV_PYTHON_INSTALL_DIR="$UV_PYTHON_DIR" /usr/local/bin/uv python install "$PY_REQ" >/dev/null
chmod -R a+rX "$UV_PYTHON_DIR"
ok "python $PY_REQ installed under $UV_PYTHON_DIR"

# ------------------------------------------------------------------
# Step 3: backend .env
# ------------------------------------------------------------------
step "Step 3/9 -- backend .env"

OLD_ENV="$APP_ROOT/backend/.env"
APP_SECRET=""
API_KEY=""
SESSION_KEY=""
OWNER_PHONE=""
if [ -f "$OLD_ENV" ]; then
    APP_SECRET=$(awk -F= '/^WATIFY_APP_SECRET=/{sub(/^WATIFY_APP_SECRET=/, ""); print}' "$OLD_ENV" || true)
    API_KEY=$(awk -F= '/^WATIFY_API_KEY=/{sub(/^WATIFY_API_KEY=/, ""); print}' "$OLD_ENV" || true)
    SESSION_KEY=$(awk -F= '/^WATIFY_SESSION_ENCRYPTION_KEY=/{sub(/^WATIFY_SESSION_ENCRYPTION_KEY=/, ""); print}' "$OLD_ENV" || true)
    OWNER_PHONE=$(awk -F= '/^WATIFY_OWNER_PHONE=/{sub(/^WATIFY_OWNER_PHONE=/, ""); print}' "$OLD_ENV" || true)
fi
gen_hex() { openssl rand -hex 32; }
gen_fernet() {
    python3 - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
}
[ -z "$APP_SECRET" ] && APP_SECRET=$(gen_hex)
[ -z "$API_KEY" ] && API_KEY=$(gen_hex)
if [ -z "$SESSION_KEY" ]; then
    # cryptography may not be installed yet; use a tiny venv for the keygen.
    TMP_VENV=$(mktemp -d)
    python3 -m venv "$TMP_VENV" >/dev/null
    "$TMP_VENV/bin/pip" install -q cryptography
    SESSION_KEY=$("$TMP_VENV/bin/python" -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    rm -rf "$TMP_VENV"
fi

cat > "$OLD_ENV" <<EOF
# Watify backend configuration -- generated by install.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ).
# DO NOT commit this file. Secrets below are unique to this install.

# Server
WATIFY_HOST=127.0.0.1
WATIFY_PORT=8000
WATIFY_CORS_ORIGIN=https://$DOMAIN

# Storage
WATIFY_APP_DB=$APP_ROOT/backend/app.db
WATIFY_WHATSAPP_DB=$APP_ROOT/backend/whatsapp.db

# Sending defaults
WATIFY_MIN_DELAY_S=3
WATIFY_MAX_DELAY_S=30
WATIFY_GROUP_MAX_CONTACTS=20

# Rate limits (TKT-0015)
WATIFY_RATE_LIMIT_TEST_SELF=15/minute
WATIFY_RATE_LIMIT_TEST_TO=10/minute
WATIFY_RATE_LIMIT_SEND=5/minute

# Logging
WATIFY_LOG_LEVEL=INFO
WATIFY_LOG_FILE=$LOG_DIR/backend.log

# Session encryption (TKT-0011)
WATIFY_SESSION_ENCRYPTION_KEY=$SESSION_KEY

# Per-install identity (TKT-0031). Used to sign JWTs and as the API key.
WATIFY_APP_SECRET=$APP_SECRET
WATIFY_API_KEY=$API_KEY

# JWT (TKT-0024)
WATIFY_JWT_ACCESS_MINUTES=15
WATIFY_JWT_REFRESH_DAYS=7
EOF
if [ -n "$OWNER_PHONE" ]; then
    echo "WATIFY_OWNER_PHONE=$OWNER_PHONE" >> "$OLD_ENV"
fi
ok "backend/.env written (re-install preserved $([ -n "$OWNER_PHONE" ] && echo "owner_phone + ")secrets when present)"

# Frontend .env.production
cat > "$APP_ROOT/frontend/.env.production" <<EOF
NEXT_PUBLIC_API_BASE=https://$DOMAIN
EOF
ok "frontend/.env.production written"

# ------------------------------------------------------------------
# Step 4: build
# ------------------------------------------------------------------
step "Step 4/9 -- build"

cd "$APP_ROOT/backend"
# Pin both the Python install dir and the cache dir to the same paths
# the systemd unit uses at runtime. Re-runs on an already-built venv
# stay no-op fast.
UV_PYTHON_INSTALL_DIR="$UV_PYTHON_DIR" UV_CACHE_DIR="$APP_ROOT/.cache/uv" \
    uv sync --quiet
ok "backend dependencies synced"

cd "$APP_ROOT/frontend"
npm install --silent --no-audit --no-fund
npm run build --silent
ok "frontend production build complete"

# ------------------------------------------------------------------
# Step 5: directories + permissions
# ------------------------------------------------------------------
step "Step 5/9 -- directories and permissions"

mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$RUN_DIR" "$APP_ROOT/.cache/uv"
chown -R "$SVC_USER:$SVC_GROUP" "$APP_ROOT" "$LOG_DIR" "$BACKUP_DIR" "$RUN_DIR"
chmod 600 "$APP_ROOT/backend/.env"
[ -f "$APP_ROOT/backend/app.db" ] && chmod 600 "$APP_ROOT/backend/app.db"
[ -f "$APP_ROOT/backend/whatsapp.db" ] && chmod 600 "$APP_ROOT/backend/whatsapp.db"
chmod 770 "$LOG_DIR" "$BACKUP_DIR" "$RUN_DIR"
ok "ownership and permissions set"

cat > /etc/logrotate.d/watify <<EOF
$LOG_DIR/*.log {
    size 100M
    rotate 3
    missingok
    compress
    delaycompress
    copytruncate
    notifempty
    su $SVC_USER $SVC_GROUP
}
EOF
ok "logrotate installed (100M, keep 3)"

# ------------------------------------------------------------------
# Step 6: systemd
# ------------------------------------------------------------------
step "Step 6/9 -- systemd units"

cat > /etc/systemd/system/watify.service <<EOF
[Unit]
Description=Watify backend (FastAPI on unix socket)
After=network.target

[Service]
Type=simple
User=$SVC_USER
Group=$SVC_GROUP
WorkingDirectory=$APP_ROOT/backend
Environment=PATH=/usr/local/bin:/usr/bin:/bin
# ProtectSystem=strict + ProtectHome=true block the default home/cache
# locations uv would otherwise pick (e.g. /var/www/.cache/uv when the
# service user is www-data, or /root/.local/share/uv/python under
# root's home). Pin both to paths the service can reach: the cache
# inside the app root (already in ReadWritePaths) and the Python
# interpreter under /opt (world-traversable, outside ProtectHome).
Environment=UV_CACHE_DIR=$APP_ROOT/.cache/uv
Environment=UV_PYTHON_INSTALL_DIR=$UV_PYTHON_DIR
RuntimeDirectory=watify
RuntimeDirectoryMode=0770
ExecStart=/usr/local/bin/uv run uvicorn app.main:app --uds $RUN_DIR/watify.sock --workers 1 --log-level warning
Restart=always
RestartSec=3

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_ROOT $LOG_DIR $RUN_DIR $BACKUP_DIR

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/watify-frontend.service <<EOF
[Unit]
Description=Watify frontend (Next.js)
After=network.target

[Service]
Type=simple
User=$SVC_USER
Group=$SVC_GROUP
WorkingDirectory=$APP_ROOT/frontend
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=HOSTNAME=127.0.0.1
ExecStart=/usr/bin/npm run start -- -H 127.0.0.1 -p 3000
Restart=always
RestartSec=3

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_ROOT $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF
ok "systemd units written"

# ------------------------------------------------------------------
# Step 7: Nginx
# ------------------------------------------------------------------
step "Step 7/9 -- Nginx configuration"

cat > /etc/nginx/conf.d/watify-rate-limit.conf <<'EOF'
# Watify rate-limit zones. Key on the real visitor IP via Cloudflare's
# CF-Connecting-IP header when present; fall back to the direct peer
# for non-Cloudflare deployments.
map $http_cf_connecting_ip $watify_real_ip {
    default $http_cf_connecting_ip;
    ""      $remote_addr;
}
limit_req_zone $watify_real_ip zone=watify_login:10m rate=5r/m;
limit_conn_zone $watify_real_ip zone=watify_conn:10m;
EOF

UPSTREAM_BACKEND="unix:$RUN_DIR/watify.sock"

SERVER_NAMES="$DOMAIN"
[ "$WANT_WWW" = yes ] && SERVER_NAMES="$DOMAIN www.$DOMAIN"

cat > /etc/nginx/sites-available/watify <<EOF
upstream watify_backend {
    server $UPSTREAM_BACKEND;
    keepalive 32;
}

upstream watify_frontend {
    server 127.0.0.1:3000;
    keepalive 16;
}

server {
    listen 80;
    listen [::]:80;
    server_name $SERVER_NAMES;

    # certbot --nginx will rewrite this block to add SSL.
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $SERVER_NAMES;

    # SSL certs filled in by certbot --nginx.

    client_max_body_size 10M;
    limit_conn watify_conn 50;

    # Security headers (TKT-0054: aim for securityheaders.com grade A;
    # CSP intentionally omitted because Next.js inlines style + we use
    # a theme-init dangerouslySetInnerHTML script that would need a
    # per-request nonce -- file a follow-on ticket if CSP is wanted).
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "accelerometer=(), autoplay=(), camera=(), clipboard-read=(), display-capture=(), encrypted-media=(), fullscreen=(self), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), midi=(), payment=(), picture-in-picture=(), publickey-credentials-get=(), screen-wake-lock=(), sync-xhr=(), usb=(), web-share=(), xr-spatial-tracking=()" always;
    add_header X-Permitted-Cross-Domain-Policies "none" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Resource-Policy "same-origin" always;

    gzip on;
    gzip_proxied any;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/javascript application/javascript application/json application/xml image/svg+xml;

    # Deny dotfiles and obvious leakage paths.
    location ~ /\.(env|git|htaccess) { deny all; }
    location ~ \.(ini|log|sh|sql|conf)\$ { deny all; }

    # Auth endpoints get an extra Nginx-level rate limit on top of
    # slowapi (defense in depth).
    location = /api/auth/login {
        limit_req zone=watify_login burst=3 nodelay;
        proxy_pass http://watify_backend;
        include /etc/nginx/snippets/watify-proxy.conf;
    }
    location = /api/auth/register {
        limit_req zone=watify_login burst=3 nodelay;
        proxy_pass http://watify_backend;
        include /etc/nginx/snippets/watify-proxy.conf;
    }

    # Backend API
    location /api/ {
        proxy_pass http://watify_backend;
        include /etc/nginx/snippets/watify-proxy.conf;
    }

    # Next.js static cache
    location /_next/static {
        proxy_pass http://watify_frontend;
        proxy_set_header Host \$host;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend (with WebSocket upgrade for Next.js dev / SSE-like flows)
    location / {
        proxy_pass http://watify_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        include /etc/nginx/snippets/watify-proxy.conf;
    }
}
EOF

mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/watify-proxy.conf <<'EOF'
proxy_set_header Host $host;
proxy_set_header X-Real-IP $watify_real_ip;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_read_timeout 60s;
proxy_send_timeout 60s;
EOF

ln -sf /etc/nginx/sites-available/watify /etc/nginx/sites-enabled/watify
[ -L /etc/nginx/sites-enabled/default ] && rm -f /etc/nginx/sites-enabled/default

nginx -t
ok "Nginx config validated"
systemctl reload nginx
ok "Nginx reloaded"

# ------------------------------------------------------------------
# Step 8: SSL via Let's Encrypt
# ------------------------------------------------------------------
step "Step 8/9 -- Let's Encrypt"

CERTBOT_DOMAINS=(-d "$DOMAIN")
[ "$WANT_WWW" = yes ] && CERTBOT_DOMAINS+=(-d "www.$DOMAIN")

if ! certbot --nginx "${CERTBOT_DOMAINS[@]}" \
        --non-interactive --agree-tos --email "$LE_EMAIL" \
        --redirect --no-eff-email; then
    warn "certbot failed -- you can re-run it manually: certbot --nginx ${CERTBOT_DOMAINS[*]} --email $LE_EMAIL --agree-tos"
fi

# Drop a pre-1.1 ssl-security.conf snippet if a prior installer ever
# wrote one. Certbot already manages ssl_protocols / ssl_session_* /
# ssl_ciphers via /etc/letsencrypt/options-ssl-nginx.conf; duplicating
# them in a snippet causes "directive is duplicate" emerg on reload.
# HSTS now lives in the main server block above.
rm -f /etc/nginx/snippets/ssl-security.conf

# Renewal cron (certbot ships its own systemd timer on Ubuntu, but a
# belt-and-braces cron entry is harmless).
cat > /etc/cron.d/certbot-renewal <<'EOF'
0 3 * * * root certbot renew --quiet --no-self-upgrade --post-hook "systemctl reload nginx"
EOF
ok "SSL configured (Cloudflare operators: set SSL/TLS mode to 'Full (strict)')"

# ------------------------------------------------------------------
# Step 9: start services
# ------------------------------------------------------------------
step "Step 9/9 -- start services"

systemctl daemon-reload
systemctl enable --now watify.service watify-frontend.service

sleep 2
for u in watify watify-frontend; do
    if systemctl is-active --quiet "$u"; then
        ok "$u running"
    else
        warn "$u failed to start -- recent journal:"
        journalctl -u "$u" -n 20 --no-pager || true
    fi
done

# ------------------------------------------------------------------
# Banner
# ------------------------------------------------------------------
echo
echo "${C_BOLD}${C_GREEN}Watify install complete${C_RESET}"
echo
echo "  URL                  : https://$DOMAIN"
echo "  Backend health       : https://$DOMAIN/api/health"
echo "  App root             : $APP_ROOT"
echo "  Backend logs         : journalctl -fu watify -- or $LOG_DIR/backend.log"
echo "  Frontend logs        : journalctl -fu watify-frontend"
echo "  Restart              : systemctl restart watify watify-frontend"
echo "  Update to latest main: sudo $APP_ROOT/install/update.sh"
echo
echo "  Cloudflare operators : set SSL/TLS mode to 'Full (strict)' in the"
echo "                         Cloudflare dashboard so the Let's Encrypt cert"
echo "                         is honored end-to-end."
echo
echo "  First-time setup     : open https://$DOMAIN, hit 'Get started' on the"
echo "                         hero, then create the single admin account."
echo

exit 0
