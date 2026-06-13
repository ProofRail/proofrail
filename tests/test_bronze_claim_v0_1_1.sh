#!/usr/bin/env bash
set -euo pipefail

CLAIM="demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml"

python3 tools/claims/validate_bronze_claim_v0_1_1.py "$CLAIM"

python3 - <<'PY'
from pathlib import Path
import sys
import yaml

claim_path = Path("demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml")
claim = yaml.safe_load(claim_path.read_text())

checks = [
    ("spec_version", claim.get("spec_version") == "v0.1.1"),
    (
        "controls.rate_limit_or_circuit_breaker_demonstrated",
        claim.get("controls", {}).get("rate_limit_or_circuit_breaker_demonstrated") is True,
    ),
    (
        "control_details.rate_limit_observed",
        claim.get("control_details", {}).get("rate_limit_observed") is True,
    ),
    (
        "control_details.circuit_breaker_observed",
        claim.get("control_details", {}).get("circuit_breaker_observed") is True,
    ),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: Bronze claim regression checks failed")
    for name in failed:
        print(f"- {name}")
    sys.exit(1)

print("PASS: Bronze claim v0.1.1 regression fixture valid")
PY
