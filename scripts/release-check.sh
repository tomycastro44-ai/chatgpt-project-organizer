#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing .venv. Run ./scripts/setup.sh first." >&2
  exit 1
fi

PYTHONPATH=backend "$PYTHON" -m pytest -q backend/tests tests/contracts
(
  cd frontend
  npm test -- --run
  npm run build
  npm audit --omit=dev --audit-level=high
)
"$PYTHON" -m pip check
"$PYTHON" -m compileall -q backend/app
PYTHONPATH=backend "$PYTHON" scripts/validate_ot013.py
PYTHONPATH=backend "$PYTHON" scripts/validate_ot014.py
