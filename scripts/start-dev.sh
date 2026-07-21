#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cleanup() {
  jobs -p | xargs -r kill
}
trap cleanup EXIT INT TERM

.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000 &
npm --prefix frontend run dev &
wait
