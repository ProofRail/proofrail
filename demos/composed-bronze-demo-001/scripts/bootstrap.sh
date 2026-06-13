#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p secrets logs state evidence claims
if [ ! -f secrets/upstream_mcp_api_key.txt ]; then
  openssl rand -hex 24 > secrets/upstream_mcp_api_key.txt
fi
cp config/agentgateway-run.yaml config/agentgateway-active.yaml

echo "[1/3] Building mock MCP images"
docker compose build mock-mcp stop-mcp

echo "[2/3] Starting stack"
docker compose up -d

echo "[3/3] Waiting for services"
sleep 5
docker compose ps

echo "Protected actuator set hash: $(python3 scripts/actuator_set_hash.py)"
echo "Gateway endpoint: http://127.0.0.1:3000/mcp"
echo "agentgateway admin UI: http://127.0.0.1:15000"
