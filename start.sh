#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

if [ -f "frontend/package.json" ]; then
  npm --prefix frontend install
  npm --prefix frontend run build
fi

python3 -m pip --python .venv/bin/python install -r requirements.txt
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
