    #!/bin/bash
    set -euo pipefail

    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    APP_DIR="${PROJECT_ROOT}/app"
    FLASK_SERVICE="flask.service"
    FLASK_SERVICE_PATH="/etc/systemd/system/${FLASK_SERVICE}"

    echo "=== URL Shortener Deployment Script ==="

    sudo yum install redis6 -y

    echo "Setting up Python virtual environment..."
    cd "${APP_DIR}"
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    ./.venv/bin/pip install --upgrade pip
    ./.venv/bin/pip install -r requirements.txt

    sudo cp "${PROJECT_ROOT}/${FLASK_SERVICE}" "${FLASK_SERVICE_PATH}"
    sudo systemctl daemon-reload
    sudo systemctl enable redis6
    sudo systemctl enable flask
    sudo systemctl restart redis6
    sudo systemctl restart flask

    echo ""
    echo "=== Deployment Complete ==="
    echo ""
    echo "Useful commands:"
    echo "  Check Flask logs: sudo journalctl -u flask -f"
    echo "  Check Redis logs: sudo journalctl -u redis6 -f"
    echo "  Restart Flask: sudo systemctl restart flask"
    echo "  Restart Redis: sudo systemctl restart redis6"