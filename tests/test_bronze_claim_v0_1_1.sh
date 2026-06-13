#!/usr/bin/env bash
set -euo pipefail

CLAIM="demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml"

python3 tools/claims/validate_bronze_claim_v0_1_1.py "$CLAIM"

grep -q 'spec_version: "v0.1.1"' "$CLAIM"
grep -q 'rate_limit_observed: true' "$CLAIM"
grep -q 'circuit_breaker_observed: true' "$CLAIM"
grep -q 'rate_limit_or_circuit_breaker_demonstrated: true' "$CLAIM"

echo "PASS: Bronze claim v0.1.1 regression fixture valid"
