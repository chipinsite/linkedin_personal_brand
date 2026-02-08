#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/Backend"

if [[ ! -x ./.venv/bin/python ]]; then
  echo "[run_backend] Missing Backend/.venv. Run: python3 -m venv .venv && ./.venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "[run_backend] Missing Backend/.env. Run: cp .env.example .env"
  exit 1
fi

echo "[run_backend] Applying migrations"
./.venv/bin/alembic upgrade head

echo "[run_backend] Starting API on http://127.0.0.1:8000"
exec ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
