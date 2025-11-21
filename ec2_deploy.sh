#!/bin/bash
cd app
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/gunicorn --bind 0.0.0.0:8000 app:app
