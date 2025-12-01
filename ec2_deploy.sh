#!/bin/bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${PROJECT_ROOT}/app"
FLASK_SERVICE="flask.service"
FLASK_SERVICE_PATH="/etc/systemd/system/${FLASK_SERVICE}"

# CHANGE THIS TO YOUR SUBDOMAIN
SUBDOMAIN="aydelottecweb"

echo "=== URL Shortener Deployment Script ==="
sudo yum install redis6 -y

echo "Starting Redis6 service..."
sudo systemctl daemon-reload
sudo systemctl enable redis6
sudo systemctl restart redis6

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
cd "${APP_DIR}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# Install certbot
echo "Installing certbot..."
sudo python3 -m venv /opt/certbot/
sudo /opt/certbot/bin/pip install --upgrade pip
sudo /opt/certbot/bin/pip install certbot
sudo ln -sf /opt/certbot/bin/certbot /usr/bin/certbot

# Stop Flask to free port 80 for certbot
echo "Stopping Flask service if running..."
sudo systemctl stop flask 2>/dev/null || true

# Generate SSL certificate
echo "Generating SSL certificate for ${SUBDOMAIN}.moraviancs.click..."
echo "You will be prompted for your email and to agree to terms of service."
sudo certbot certonly --standalone -d "${SUBDOMAIN}.moraviancs.click"

# Deploy Flask systemd service
echo "Deploying Flask service..."
sudo cp "${PROJECT_ROOT}/${FLASK_SERVICE}" "${FLASK_SERVICE_PATH}"
sudo systemctl daemon-reload
sudo systemctl enable flask
sudo systemctl restart redis6
sudo systemctl restart flask

# Show service status
echo ""
echo "=== Service Status ==="
sudo systemctl status redis6 --no-pager
echo ""
sudo systemctl status flask --no-pager

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Your app is running at: https://${SUBDOMAIN}.moraviancs.click"
echo ""
echo "Certificate files:"
echo "  Cert: /etc/letsencrypt/live/${SUBDOMAIN}.moraviancs.click/fullchain.pem"
echo "  Key:  /etc/letsencrypt/live/${SUBDOMAIN}.moraviancs.click/privkey.pem"
echo ""
echo "Useful commands:"
echo "  Check Flask logs: sudo journalctl -u flask -f"
echo "  Check Redis logs: sudo journalctl -u redis6 -f"
echo "  Restart Flask: sudo systemctl restart flask"
echo "  Restart Redis: sudo systemctl restart redis6"
echo "  Renew cert: sudo certbot renew"