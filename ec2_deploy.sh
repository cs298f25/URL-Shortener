#!/bin/bash
cd app
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python app.py