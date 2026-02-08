#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/Frontend"

if [[ ! -d node_modules ]]; then
  echo "[run_frontend] Installing dependencies"
  npm install
fi

if [[ ! -f .env ]]; then
  echo "[run_frontend] Creating .env from .env.example"
  cp .env.example .env
fi

echo "[run_frontend] Starting UI on http://127.0.0.1:5173"
exec npm run dev -- --host 127.0.0.1 --port 5173
