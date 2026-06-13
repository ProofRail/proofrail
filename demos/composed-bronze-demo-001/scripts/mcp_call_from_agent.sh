#!/usr/bin/env bash
set -euo pipefail

payload="${1:?JSON-RPC payload required}"
gateway_url="${GATEWAY_URL:-http://agentgateway:3000/mcp}"

docker compose exec -T agent sh -s <<SH_INNER
set -eu

INIT_HEADERS=/tmp/mcp-init.headers
INIT_BODY=/tmp/mcp-init.body

curl -sS -D "\$INIT_HEADERS" -o "\$INIT_BODY" -X POST "$gateway_url" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{"jsonrpc":"2.0","id":"init-1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"proofrail-demo-client","version":"0.1.0"}}}'

SESSION_ID=\$(awk 'tolower(\$1)=="mcp-session-id:" {print \$2}' "\$INIT_HEADERS" | tr -d "\\r")

if [ -z "\$SESSION_ID" ]; then
  echo "ERROR: no Mcp-Session-Id returned" >&2
  cat "\$INIT_HEADERS" >&2
  cat "\$INIT_BODY" >&2
  exit 1
fi

curl -sS --max-time 10 -X POST "$gateway_url" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "Mcp-Session-Id: \$SESSION_ID" \\
  -H "X-Agent-ID: demo-agent-001" \\
  -d '$payload'
SH_INNER
