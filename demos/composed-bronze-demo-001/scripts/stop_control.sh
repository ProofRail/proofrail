#!/usr/bin/env bash
set -euo pipefail

mkdir -p state
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
MODE="${1:-status}"

case "$MODE" in
  stop)
    cp config/agentgateway-stop.yaml config/agentgateway-active.yaml
    docker compose restart agentgateway
    echo "stop_mode=true" > state/stop_control.state
    echo "ProofRail stop-control mode activated"
    ;;
  resume)
    cp config/agentgateway-run.yaml config/agentgateway-active.yaml
    docker compose restart agentgateway
    echo "stop_mode=false" > state/stop_control.state
    echo "ProofRail stop-control mode resumed"
    ;;
  status)
    cat state/stop_control.state 2>/dev/null || echo "stop_mode=false"
    ;;
  *)
    echo "Usage: $0 {stop|resume|status}" >&2
    exit 2
    ;;
esac
