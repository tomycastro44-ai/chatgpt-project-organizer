#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then PYTHON="$ROOT/.venv/bin/python"; fi
PYTHONPATH=backend "$PYTHON" -m pytest -q backend/tests tests/contracts
(
  cd frontend
  npm test -- --run
  npm run build
)
PYTHONPATH=backend "$PYTHON" scripts/validate_ot012.py
