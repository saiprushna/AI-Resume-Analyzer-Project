#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$ROOT/app"
cd "$ROOT"
exec uvicorn main:app --app-dir app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
