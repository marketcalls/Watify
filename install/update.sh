#!/usr/bin/env bash
#
# Watify -- one-shot updater for an already-installed host.
#
# Pulls the latest origin/main, refreshes backend + frontend
# dependencies, rebuilds the frontend, and restarts both services.
# Preserves /var/www/watify/backend/.env (gitignored) -- secrets and
# the WhatsApp session blob in app.db are untouched.

set -euo pipefail

if [ -t 1 ]; then
    C_BOLD=$'\033[1m'; C_GREEN=$'\033[32m'; C_RED=$'\033[31m'; C_BLUE=$'\033[34m'; C_RESET=$'\033[0m'
else
    C_BOLD=""; C_GREEN=""; C_RED=""; C_BLUE=""; C_RESET=""
fi

step() { echo; echo "${C_BOLD}${C_BLUE}==> $*${C_RESET}"; }
ok()   { echo "${C_GREEN}    [ok]${C_RESET} $*"; }
die()  { echo "${C_RED}    [error]${C_RESET} $*" >&2; exit 1; }

APP_ROOT=/var/www/watify

[ "$(id -u)" -eq 0 ] || die "must be run as root (try: sudo $0)"
[ -d "$APP_ROOT/.git" ] || die "no Watify install at $APP_ROOT -- run install.sh first"
[ -f "$APP_ROOT/backend/.env" ] || die "missing $APP_ROOT/backend/.env -- re-run install.sh"

START=$(date +%s)

step "git pull"
git -C "$APP_ROOT" fetch --quiet origin
git -C "$APP_ROOT" reset --hard origin/main --quiet
ok "at $(git -C "$APP_ROOT" rev-parse --short HEAD)"

step "backend deps"
cd "$APP_ROOT/backend"
uv sync --quiet
ok "uv sync complete"

step "frontend build"
cd "$APP_ROOT/frontend"
npm install --silent --no-audit --no-fund
npm run build --silent
ok "Next.js build complete"

step "restart services"
systemctl restart watify.service watify-frontend.service
sleep 2
for u in watify watify-frontend; do
    if systemctl is-active --quiet "$u"; then
        ok "$u running"
    else
        die "$u failed to restart -- journalctl -u $u -n 50"
    fi
done

END=$(date +%s)
echo
echo "${C_BOLD}${C_GREEN}Watify updated in $((END - START))s${C_RESET}"
