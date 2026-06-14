#!/usr/bin/env bash
set -euo pipefail

CLAIM="demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml"
PACKAGE_ROOT="demos/composed-bronze-demo-001"

echo "=== Step 1: Structural validation ==="
python3 tools/claims/validate_bronze_claim_v0_1_2.py "$CLAIM"

echo "=== Step 2: Evidence checksum verification ==="
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py "$CLAIM" "$PACKAGE_ROOT"

echo "=== Step 3: Inline regression checks ==="
python3 - <<'PY'
import re
import sys
from pathlib import Path
import yaml

claim_path = Path("demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml")
claim = yaml.safe_load(claim_path.read_text())

checks = [
    ("spec_version", claim.get("spec_version") == "v0.1.2"),
    (
        "controls.declared_actuator_set",
        claim.get("controls", {}).get("declared_actuator_set") is True,
    ),
    (
        "controls.gateway_mediation",
        claim.get("controls", {}).get("gateway_mediation") is True,
    ),
    (
        "controls.bypass_prevention_tested",
        claim.get("controls", {}).get("bypass_prevention_tested") is True,
    ),
    (
        "controls.stop_control_demonstrated",
        claim.get("controls", {}).get("stop_control_demonstrated") is True,
    ),
    (
        "controls.rate_limit_or_circuit_breaker_demonstrated",
        claim.get("controls", {}).get("rate_limit_or_circuit_breaker_demonstrated") is True,
    ),
    (
        "controls.normalized_audit_evidence",
        claim.get("controls", {}).get("normalized_audit_evidence") is True,
    ),
    (
        "controls.performance_measured",
        claim.get("controls", {}).get("performance_measured") is True,
    ),
    (
        "controls.runbook_present",
        claim.get("controls", {}).get("runbook_present") is True,
    ),
    (
        "evidence_checksums present",
        isinstance(claim.get("evidence_checksums"), dict) and len(claim.get("evidence_checksums", {})) > 0,
    ),
]

# Verify all checksum values match expected format
checksums = claim.get("evidence_checksums", {})
for path, value in checksums.items():
    checks.append((
        f"checksum format: {path}",
        isinstance(value, str) and bool(re.fullmatch(r"sha256:[0-9a-fA-F]{64}", value)),
    ))

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: Bronze claim v0.1.2 regression checks failed")
    for name in failed:
        print(f"- {name}")
    sys.exit(1)

print("PASS: Bronze claim v0.1.2 regression fixture valid")
PY

echo "=== Step 4: Tamper detection test ==="
# Pick an evidence file to tamper with
EVIDENCE_FILE="$PACKAGE_ROOT/evidence/audit-sample.jsonl"
TAMPER_COPY=$(mktemp)

# Copy the original file
cp "$EVIDENCE_FILE" "$TAMPER_COPY"

# Create a tampered version in a temporary file, then swap it in
TAMPERED=$(mktemp)
cp "$EVIDENCE_FILE" "$TAMPERED"
echo "TAMPERED_CONTENT" >> "$TAMPERED"

# Use trap to guarantee restoration even on failure
restore_original() {
    cp "$TAMPER_COPY" "$EVIDENCE_FILE"
    rm -f "$TAMPER_COPY" "$TAMPERED"
}
trap restore_original EXIT

# Replace with tampered version
cp "$TAMPERED" "$EVIDENCE_FILE"

# The verifier should fail
if python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py "$CLAIM" "$PACKAGE_ROOT" 2>/dev/null; then
    echo "FAIL: tamper detection — verifier should have failed on tampered file"
    exit 1
else
    echo "PASS: tamper detection — verifier correctly detected tampered evidence"
fi

# Restore happens via trap
echo "=== All v0.1.2 regression tests passed ==="
