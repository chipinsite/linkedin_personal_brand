#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_LOG="/tmp/personal_brand_backend.log"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "[play_mode] Starting backend in background (log: $BACKEND_LOG)"
"$ROOT_DIR/scripts/run_backend.sh" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

sleep 2
if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "[play_mode] Backend health check OK"
else
  echo "[play_mode] Backend not healthy yet. Check log: $BACKEND_LOG"
fi

echo "[play_mode] Starting frontend (Ctrl+C will stop both frontend and backend)"
"$ROOT_DIR/scripts/run_frontend.sh"
