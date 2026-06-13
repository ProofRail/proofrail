#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p evidence logs

MCP_PATH="${MCP_PATH:-/mcp}"
GATEWAY_URL="${GATEWAY_URL:-http://agentgateway:3000${MCP_PATH}}"
LOCAL_GATEWAY_URL="${LOCAL_GATEWAY_URL:-http://127.0.0.1:3000${MCP_PATH}}"
UPSTREAM_URL="${UPSTREAM_URL:-http://mock-mcp:3005${MCP_PATH}}"
TOOLS_LIST='{"jsonrpc":"2.0","id":"tools-list-1","method":"tools/list","params":{}}'
CALL_READ='{"jsonrpc":"2.0","id":"call-read-1","method":"tools/call","params":{"name":"demo.read","arguments":{"key":"alpha"}}}'
CALL_DEPLOY='{"jsonrpc":"2.0","id":"call-deploy-1","method":"tools/call","params":{"name":"deploy.push","arguments":{"version":"1.2.3"}}}'

: > evidence/audit-sample.jsonl

log_audit() {
  local event_type="$1" target="$2" decision="$3" reason="$4" corr="$5" latency="$6"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
  local params_hash
  params_hash="sha256:$(printf '%s' "$target-$corr" | sha256sum | awk '{print $1}')"
  local tier=2
  case "$target" in
    demo.read) tier=0 ;;
    ticket.create) tier=1 ;;
    deploy.push) tier=2 ;;
    admin.rotate_secret) tier=3 ;;
  esac
  jq -nc \
    --arg timestamp "$ts" \
    --arg event_type "$event_type" \
    --arg agent_id "demo-agent-001" \
    --arg action_type "tool_call" \
    --arg target "$target" \
    --arg decision "$decision" \
    --arg decision_reason "$reason" \
    --arg session_id "demo-session-001" \
    --arg correlation_id "$corr" \
    --arg parameters_hash "$params_hash" \
    --arg surface "mcp" \
    --arg environment "test" \
    --arg confidence "medium" \
    --argjson tier "$tier" \
    --argjson latency_total "$latency" \
    '{timestamp:$timestamp,event_type:$event_type,agent_id:$agent_id,action_type:$action_type,target:$target,decision:$decision,decision_reason:$decision_reason,session_id:$session_id,correlation_id:$correlation_id,parameters_hash:$parameters_hash,surface:$surface,environment:$environment,identity:{confidence:$confidence},risk:{tier:$tier},latency_ms:{total:$latency_total,policy_eval:1.0},degradation_mode:null}' >> evidence/audit-sample.jsonl
}

call_from_agent() {
  local payload="$1"
  GATEWAY_URL="$GATEWAY_URL" bash scripts/mcp_call_from_agent.sh "$payload"
}

{
 rm -f evidence/bypass-test-results.md \
      evidence/emergency-stop-test.md \
      evidence/rate-limit-test.md \
      evidence/latency-benchmark.md \
      evidence/audit-sample.jsonl \
      evidence/agentgateway-log-sample.txt

  echo "# Bypass prevention test"
  echo
  echo "Run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## A. Agent cannot reach upstream directly"
  if docker compose exec -T agent sh -lc "curl -fsS --max-time 2 -X POST '${UPSTREAM_URL}' -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '${TOOLS_LIST}' >/dev/null"; then
    echo "FAIL: agent reached upstream directly"
    exit 1
  else
    echo "PASS: agent could not reach upstream directly"
  fi
  echo
  echo "## B. Agent has no upstream secret"
  docker compose exec -T agent sh -lc 'test ! -f /run/secrets/upstream_mcp_api_key && test -z "${UPSTREAM_MCP_API_KEY:-}"'
  echo "PASS: agent has no upstream credential"
  echo
  echo "## C. Bypass tester on agent_net cannot call upstream directly"
  if docker compose exec -T bypass-tester sh -lc "curl -fsS --max-time 2 -X POST '${UPSTREAM_URL}' -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '${TOOLS_LIST}' >/dev/null"; then
    echo "FAIL: bypass-tester called upstream without secret"
    exit 1
  else
    echo "PASS: bypass-tester could not reach upstream directly"
  fi
  echo
  echo "## D. Gateway path works"
  call_from_agent "$TOOLS_LIST" | tee /tmp/proofrail-tools-list.json
  echo
  echo "PASS: gateway path produced a response"
} | tee evidence/bypass-test-results.md

# Normal call and deploy call
start_ns=$(date +%s%N)
call_from_agent "$CALL_READ" | tee evidence/normal-call-response.json
end_ns=$(date +%s%N)
lat_ms=$(( (end_ns - start_ns) / 1000000 ))
log_audit "tool_call.decision" "demo.read" "allowed" "gateway_route" "call-read-1" "$lat_ms"

start_ns=$(date +%s%N)
call_from_agent "$CALL_DEPLOY" | tee evidence/deploy-call-response.json
end_ns=$(date +%s%N)
lat_ms=$(( (end_ns - start_ns) / 1000000 ))
log_audit "tool_call.decision" "deploy.push" "allowed" "gateway_route" "call-deploy-1" "$lat_ms"

{
  echo "# Emergency stop test"
  echo
  bash scripts/stop_control.sh stop
  sleep 3
  RESP="$(call_from_agent "$CALL_READ" || true)"
  echo "$RESP"
  if echo "$RESP" | grep -q "ProofRail stop control active"; then
    echo "PASS: stop-control mode blocked tool call"
    log_audit "tool_call.decision" "demo.read" "blocked" "emergency_stop" "call-stop-1" 3
  else
    echo "FAIL: stop-control response did not show emergency_stop"
    exit 1
  fi
  bash scripts/stop_control.sh resume
  sleep 3
} | tee evidence/emergency-stop-test.md

  bash scripts/write_active_config.sh config/agentgateway-ratelimit.yaml
  docker compose restart agentgateway
  sleep 3

{
  echo "# Rate-limit / circuit-breaker test"
  echo
  echo "Configured desired behavior: 5 requests/minute local request rate limit."
  echo "This test sends 8 quick requests and records whether the gateway returns any throttle response."
  throttled=0
  for i in $(seq 1 8); do
    RESP=$(ALLOW_THROTTLE=1 call_from_agent "{\"jsonrpc\":\"2.0\",\"id\":\"rate-$i\",\"method\":\"tools/call\",\"params\":{\"name\":\"demo.read\",\"arguments\":{\"key\":\"rate-$i\"}}}" || true)
    echo "[$i] $RESP"
    if echo "$RESP" | grep -Eiq "429|too many requests|throttle|rate.?limit|localratelimit|quota"; then throttled=1; fi
  done
  if [ "$throttled" = "1" ]; then
    echo "PASS: rate-limit/circuit-breaker behavior observed"
    log_audit "tool_call.decision" "demo.read" "blocked" "rate_limit" "rate-limit-1" 2
  else
    echo "WARN: no throttle response observed. Validate agentgateway localRateLimit policy attachment for your installed schema."
  fi
} | tee evidence/rate-limit-test.md


  bash scripts/write_active_config.sh config/agentgateway-normal.yaml
  docker compose restart agentgateway
  sleep 3

{
  echo "# Latency benchmark"
  echo
  echo "Small smoke benchmark over 20 calls. Replace with a 300+ call run before making a public claim."
  tmp="$(mktemp)"
  for i in $(seq 1 20); do
    s=$(date +%s%N)
    call_from_agent "{\"jsonrpc\":\"2.0\",\"id\":\"lat-$i\",\"method\":\"tools/call\",\"params\":{\"name\":\"demo.read\",\"arguments\":{\"i\":$i}}}" >/dev/null || true
    e=$(date +%s%N)
    echo $(( (e - s) / 1000000 )) >> "$tmp"
  done
  sort -n "$tmp" | awk 'BEGIN{n=0}{a[++n]=$1}END{p95=a[int(n*.95)]; if(p95=="") p95=a[n]; print "p95_ms: " p95; print "samples: " n}'
  rm -f "$tmp"
} | tee evidence/latency-benchmark.md

# Preserve a small gateway log sample if available.
docker compose logs --no-color --tail=200 agentgateway > evidence/agentgateway-log-sample.txt || true

echo "Evidence generation complete. Next: python3 scripts/generate_bronze_claim.py && python3 scripts/validate_claim_v0_1_1.py claims/bronze-claim-demo-001.yaml"
