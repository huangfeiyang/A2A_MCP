#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src"

RELOAD_FLAG=""
if [[ "${1:-}" == "--reload" ]]; then
  RELOAD_FLAG="--reload"
fi

uvicorn tool_server.server:app --host 0.0.0.0 --port 7001 $RELOAD_FLAG &
TOOL_PID=$!

echo "Tool server started (pid=$TOOL_PID)"

trap 'kill $TOOL_PID' EXIT

uvicorn agent_server.app:app --host 0.0.0.0 --port 7002 $RELOAD_FLAG
