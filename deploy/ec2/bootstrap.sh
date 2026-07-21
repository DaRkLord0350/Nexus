#!/usr/bin/env bash
# One-time setup for a fresh EC2 instance (Amazon Linux 2023 / Ubuntu 22.04+).
# Run once via SSM Session Manager or as part of the launch template user-data.
set -euo pipefail

APP_USER="commerceos"
APP_DIR="/opt/commerceos"
REPO_URL="${REPO_URL:-git@github.com:YOUR_GITHUB_ORG/commerceos.git}"
BRANCH="${BRANCH:-main}"

echo "==> Installing system packages"
if command -v dnf >/dev/null 2>&1; then
    sudo dnf update -y
    sudo dnf install -y python3.11 python3.11-pip git nginx nodejs npm
elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3.11 python3.11-venv python3-pip git nginx nodejs npm
else
    echo "Unsupported distro; install python3.11, git, nginx, and node manually." >&2
    exit 1
fi

echo "==> Creating application user"
id -u "$APP_USER" &>/dev/null || sudo useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
sudo mkdir -p "$APP_DIR"
sudo chown "$APP_USER:$APP_USER" "$APP_DIR"

echo "==> Cloning repository"
sudo -u "$APP_USER" git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR" 2>/dev/null || \
    (cd "$APP_DIR" && sudo -u "$APP_USER" git fetch && sudo -u "$APP_USER" git checkout "$BRANCH")

echo "==> Installing backend dependencies"
cd "$APP_DIR/apps/api"
sudo -u "$APP_USER" python3.11 -m venv .venv
sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt

echo "==> Installing frontend dependencies and building"
cd "$APP_DIR/apps/web"
sudo -u "$APP_USER" npm ci
sudo -u "$APP_USER" npm run build

echo "==> Installing systemd units"
sudo cp "$APP_DIR/deploy/systemd/commerceos-api.service" /etc/systemd/system/
sudo cp "$APP_DIR/deploy/systemd/commerceos-web.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable commerceos-api commerceos-web

echo "==> Installing nginx config"
sudo cp "$APP_DIR/deploy/nginx/commerceos.conf" /etc/nginx/conf.d/commerceos.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "==> Bootstrap complete."
echo "Populate $APP_DIR/apps/api/.env.production (or Secrets Manager secret 'commerceos/production/app'),"
echo "then run deploy/scripts/migrate.sh followed by 'systemctl start commerceos-api commerceos-web'."
