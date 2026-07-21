#!/usr/bin/env bash
# Rolling deploy on a single EC2 instance: pull the latest code, install
# dependencies, run migrations, restart services, and verify health. Exits
# non-zero (leaving the previous process running, since systemd only restarts
# on an explicit `systemctl restart`) if the post-restart health check fails.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/commerceos}"
BRANCH="${BRANCH:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Pulling $BRANCH"
cd "$APP_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "==> Installing backend dependencies"
cd "$APP_DIR/apps/api"
.venv/bin/pip install -r requirements.txt

echo "==> Running database migrations"
APP_DIR="$APP_DIR/apps/api" bash "$SCRIPT_DIR/migrate.sh"

echo "==> Building frontend"
cd "$APP_DIR/apps/web"
npm ci
npm run build

echo "==> Restarting services"
sudo systemctl restart commerceos-api
sudo systemctl restart commerceos-web

echo "==> Verifying health"
if ! bash "$SCRIPT_DIR/health-check.sh" http://127.0.0.1:8000/ready; then
    echo "Deploy failed health check. Check 'journalctl -u commerceos-api -n 100' for details." >&2
    exit 1
fi

echo "==> Deploy complete."
