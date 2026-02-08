#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_LOG="/tmp/personal_brand_backend_e2e.log"
FRONTEND_LOG="/tmp/personal_brand_frontend_e2e.log"
BACKEND_URL="http://127.0.0.1:8000"
FRONTEND_URL="http://127.0.0.1:5173"
TIMEOUT_SECONDS="${E2E_TIMEOUT_SECONDS:-60}"
SKIP_SERVERS="${PLAY_E2E_SKIP_SERVERS:-0}"

cleanup() {
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

wait_for_url() {
  local url="$1"
  local label="$2"
  local started_at
  started_at="$(date +%s)"

  while true; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[play_mode_e2e] ${label} ready: ${url}"
      return 0
    fi

    local now
    now="$(date +%s)"
    if (( now - started_at >= TIMEOUT_SECONDS )); then
      echo "[play_mode_e2e] timeout waiting for ${label}: ${url}" >&2
      return 1
    fi

    sleep 1
  done
}

if [[ "$SKIP_SERVERS" == "1" ]]; then
  echo "[play_mode_e2e] PLAY_E2E_SKIP_SERVERS=1, skipping local server startup and live API walkthrough"
else
  echo "[play_mode_e2e] starting backend (log: ${BACKEND_LOG})"
  # Mirror run_frontend behavior by bootstrapping backend env on first run.
  if [[ ! -f "$ROOT_DIR/Backend/.env" ]]; then
    if [[ -f "$ROOT_DIR/Backend/.env.example" ]]; then
      cp "$ROOT_DIR/Backend/.env.example" "$ROOT_DIR/Backend/.env"
      echo "[play_mode_e2e] created Backend/.env from .env.example"
    else
      echo "[play_mode_e2e] missing Backend/.env and Backend/.env.example" >&2
      exit 1
    fi
  fi

  # Ensure migration/boot commands have a deterministic local DB target.
  if [[ -z "${DATABASE_URL:-}" ]]; then
    export DATABASE_URL="sqlite:///$ROOT_DIR/Backend/local_e2e.db"
    echo "[play_mode_e2e] using fallback DATABASE_URL=${DATABASE_URL}"
  fi

  (
    cd "$ROOT_DIR/Backend"
    if [[ ! -x ./.venv/bin/python ]]; then
      echo "[play_mode_e2e] missing Backend/.venv" >&2
      exit 1
    fi
    echo "[play_mode_e2e] applying migrations"
    ./.venv/bin/alembic upgrade head
    echo "[play_mode_e2e] starting uvicorn (no reload)"
    exec ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!

  wait_for_url "${BACKEND_URL}/health" "backend health"

  echo "[play_mode_e2e] starting frontend (log: ${FRONTEND_LOG})"
  "$ROOT_DIR/scripts/run_frontend.sh" >"$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!

  wait_for_url "${FRONTEND_URL}" "frontend"

  # Ensure dashboard route shell is served before running checks.
  curl -fsS "${FRONTEND_URL}" >/dev/null

  echo "[play_mode_e2e] running live API walkthrough"
  "$ROOT_DIR/scripts/live_api_walkthrough.sh"
fi

echo "[play_mode_e2e] running targeted dashboard/settings flow tests"
(
  cd "$ROOT_DIR/Frontend"
  npx vitest run src/__tests__/App.test.jsx -t "renders dashboard and loads initial data|shows operational alerts for critical dashboard conditions|shows algorithm alignment and recent audit entries in settings|filters audit trail entries in settings by query"
)

echo "[play_mode_e2e] completed"
