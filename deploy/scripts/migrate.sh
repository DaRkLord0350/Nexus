#!/usr/bin/env bash
# Runs Alembic migrations against the configured DATABASE_URL.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/commerceos/apps/api}"
cd "$APP_DIR"

echo "==> Running alembic upgrade head"
.venv/bin/alembic upgrade head
