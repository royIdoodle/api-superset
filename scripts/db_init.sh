#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "未检测到 .venv，请先运行 scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate
export PYTHONPATH=.

python scripts/db_init.py

