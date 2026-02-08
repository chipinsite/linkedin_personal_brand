#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-}"
RUN_MUTATING="${RUN_MUTATING:-0}"

if [[ -n "$API_KEY" ]]; then
  AUTH_HEADER=( -H "x-api-key: $API_KEY" )
else
  AUTH_HEADER=()
fi

call_get() {
  local path="$1"
  echo "[walkthrough] GET $path"
  curl -fsS "${AUTH_HEADER[@]}" "$API_BASE$path" | head -c 600
  echo
}

call_post() {
  local path="$1"
  local payload="$2"
  echo "[walkthrough] POST $path"
  curl -fsS "${AUTH_HEADER[@]}" -H 'Content-Type: application/json' -X POST "$API_BASE$path" -d "$payload" | head -c 600
  echo
}

echo "[walkthrough] API_BASE=$API_BASE"

call_get /health
call_get /health/readiness
call_get /admin/config
call_get /drafts
call_get /posts
call_get /engagement/status
call_get /reports/daily

if [[ "$RUN_MUTATING" == "1" ]]; then
  echo "[walkthrough] RUN_MUTATING=1 enabled"
  call_post /drafts/generate '{}'
  call_post /posts/publish-due '{}'
  call_post /engagement/poll '{}'
  call_post /learning/recompute '{}'
  call_post /reports/daily/send '{}'
else
  echo "[walkthrough] Skipping mutating calls (set RUN_MUTATING=1 to enable)."
fi

echo "[walkthrough] complete"
