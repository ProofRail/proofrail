#!/usr/bin/env bash
set -euo pipefail

payload="${1:?JSON-RPC payload required}"
gateway_url="${GATEWAY_URL:-http://agentgateway:3000/mcp}"
allow_throttle="${ALLOW_THROTTLE:-0}"

docker compose exec -T agent sh -s <<SH_INNER
set -eu

payload='$payload'
gateway_url='$gateway_url'
allow_throttle='$allow_throttle'

INIT_HEADERS=/tmp/mcp-init.headers
INIT_BODY=/tmp/mcp-init.body
RESP_HEADERS=/tmp/mcp-response.headers
RESP_BODY=/tmp/mcp-response.body

summarize_throttle() {
  headers="\$1"
  body_file="\$2"
  stage="\$3"

  limit=\$(awk 'tolower(\$1)=="x-ratelimit-limit:" {print \$2}' "\$headers" | tr -d "\\r")
  remaining=\$(awk 'tolower(\$1)=="x-ratelimit-remaining:" {print \$2}' "\$headers" | tr -d "\\r")
  reset=\$(awk 'tolower(\$1)=="x-ratelimit-reset:" {print \$2}' "\$headers" | tr -d "\\r")
  body=\$(cat "\$body_file" | tr "\\n" " ")

  echo "THROTTLED: HTTP 429 during \$stage: \${body}; limit=\${limit:-unknown} remaining=\${remaining:-unknown} reset=\${reset:-unknown}"
}

init_status=\$(curl -sS -D "\$INIT_HEADERS" -o "\$INIT_BODY" -w "%{http_code}" -X POST "\$gateway_url" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{"jsonrpc":"2.0","id":"init-1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"proofrail-demo-client","version":"0.1.0"}}}')

if [ "\$init_status" = "429" ] && [ "\$allow_throttle" = "1" ]; then
  summarize_throttle "\$INIT_HEADERS" "\$INIT_BODY" "initialize"
  exit 0
fi

if [ "\$init_status" != "200" ]; then
  echo "ERROR: initialize failed with HTTP \$init_status" >&2
  cat "\$INIT_HEADERS" >&2
  echo >&2
  cat "\$INIT_BODY" >&2
  exit 1
fi

SESSION_ID=\$(awk 'tolower(\$1)=="mcp-session-id:" {print \$2}' "\$INIT_HEADERS" | tr -d "\\r")

if [ -z "\$SESSION_ID" ]; then
  echo "ERROR: initialize succeeded but no Mcp-Session-Id was returned" >&2
  cat "\$INIT_HEADERS" >&2
  echo >&2
  cat "\$INIT_BODY" >&2
  exit 1
fi

resp_status=\$(curl -sS --max-time 10 -D "\$RESP_HEADERS" -o "\$RESP_BODY" -w "%{http_code}" -X POST "\$gateway_url" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "Mcp-Session-Id: \$SESSION_ID" \\
  -H "X-Agent-ID: demo-agent-001" \\
  -d "\$payload")

if [ "\$resp_status" = "429" ] && [ "\$allow_throttle" = "1" ]; then
  summarize_throttle "\$RESP_HEADERS" "\$RESP_BODY" "request"
  exit 0
fi

if [ "\$resp_status" != "200" ]; then
  echo "ERROR: request failed with HTTP \$resp_status" >&2
  cat "\$RESP_HEADERS" >&2
  echo >&2
  cat "\$RESP_BODY" >&2
  exit 1
fi

cat "\$RESP_BODY"
SH_INNER
