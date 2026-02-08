#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[v1.0 smoke] backend tests"
(
  cd "$ROOT_DIR/Backend"
  ./.venv/bin/python -m unittest discover -v -s tests -p 'test_*.py'
)

echo "[v1.0 smoke] frontend tests and production build"
(
  cd "$ROOT_DIR/Frontend"
  npm test
  npm run build
)

echo "[v1.0 smoke] completed"
