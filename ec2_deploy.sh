#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${PROJECT_ROOT}/app"
SERVICE_NAME="urlshortener-redis.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

# Ensure Redis is installed (Debian/Ubuntu)
if ! command -v redis-server >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y redis-server
fi

# Deploy Redis systemd service
sudo cp "${PROJECT_ROOT}/redis.service" "${SERVICE_PATH}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

cd "${APP_DIR}"
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# Run gunicorn via sudo so it can bind to privileged port 80
sudo ./.venv/bin/gunicorn --bind 0.0.0.0:80 app:app
