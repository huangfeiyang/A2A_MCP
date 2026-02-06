#!/usr/bin/env bash
set -euo pipefail

AGENT_URL="${AGENT_URL:-http://localhost:7002}"

curl -sf "$AGENT_URL/agent-card" >/dev/null

echo "Agent card OK"

payload='{"query": "现在几点了？"}'

curl -sf -H "Content-Type: application/json" -d "$payload" "$AGENT_URL/v1/ask" >/dev/null

echo "Ask endpoint OK"
