#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "未检测到 .venv，请先运行 scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate
export PYTHONPATH=.

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

