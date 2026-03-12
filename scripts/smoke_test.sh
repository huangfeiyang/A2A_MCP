#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

AGENT_URL="${AGENT_URL:-$(python - <<'PY'
from client.settings import get_settings

print(get_settings().agent_base_url)
PY
)}"

curl -sf "$AGENT_URL/agent-card" >/dev/null

echo "Agent card OK"

payload='{"query": "现在几点了？"}'

curl -sf -H "Content-Type: application/json" -d "$payload" "$AGENT_URL/v1/ask" >/dev/null

echo "Ask endpoint OK"
