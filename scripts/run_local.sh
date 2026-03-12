#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ "${1:-}" == "--reload" ]]; then
  export A2A_MCP_RELOAD=true
fi

python -m tool_server.server &
TOOL_PID=$!

echo "Tool server started (pid=$TOOL_PID)"

trap 'kill $TOOL_PID' EXIT

python -m agent_server.main
