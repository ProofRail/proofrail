#!/usr/bin/env bash
set -euo pipefail

BRONZE_ROOT="demos/composed-bronze-demo-001"
SILVER_ROOT="demos/silver-demo-001"
DEMO_002="demos/silver-demo-002-independent-verifier"
CLAIM="$BRONZE_ROOT/claims/bronze-claim-demo-001.yaml"
BUNDLE_MANIFEST="$BRONZE_ROOT/evidence-bundle-manifest-v0.1.3.yaml"
PRIVATE_KEY="$SILVER_ROOT/runtime/issuer-a/private-key.pem"
ASSERTION="$SILVER_ROOT/runtime/silver-signed-bundle-assertion-v0.1.0.yaml"
TRUST_POLICY="$SILVER_ROOT/runtime/verifier-b/trust-policy.yaml"
REVOCATION_LIST="$SILVER_ROOT/runtime/verifier-b/revocation-list.yaml"
REPORT="$SILVER_ROOT/runtime/verification-report.json"
PACKAGE_DIR="$DEMO_002/runtime/package"

# Temp directory for independence test — cleaned up on exit
TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

echo "=== Step 1: Generate v0.1.2 claim ==="
python3 tools/claims/generate_bronze_claim_v0_1_2.py "$BRONZE_ROOT"

echo "=== Step 2: Verify v0.1.2 evidence checksums ==="
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py "$CLAIM" "$BRONZE_ROOT"

echo "=== Step 3: Generate v0.1.3 bundle manifest ==="
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py "$BRONZE_ROOT"

echo "=== Step 4: Verify v0.1.3 bundle manifest ==="
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py "$BUNDLE_MANIFEST" "$BRONZE_ROOT"

echo "=== Step 5: Generate demo issuer keypair + trust policy ==="
python3 tools/silver/generate_demo_issuer_v0_1_0.py "$SILVER_ROOT" --force

echo "=== Step 6: Generate empty revocation list ==="
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force

echo "=== Step 7: Sign v0.1.3 bundle manifest ==="
python3 tools/silver/sign_bundle_manifest_v0_1_0.py "$SILVER_ROOT" \
  --private-key "$PRIVATE_KEY" \
  --output "$ASSERTION"

echo "=== Step 8: Verify with main Silver verifier ==="
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$ASSERTION" "$TRUST_POLICY" \
  --silver-root "$SILVER_ROOT" \
  --bronze-package-root "$BRONZE_ROOT" \
  --revocation-list "$REVOCATION_LIST" \
  --report "$REPORT"

echo "=== Step 9: Export independent verification package ==="
python3 tools/silver/export_independent_verification_package_v0_1_0.py \
  --bronze-root "$BRONZE_ROOT" \
  --silver-root "$SILVER_ROOT" \
  --output "$PACKAGE_DIR" \
  --force

echo "=== Step 10: Copy package AND verifier to temp dir ==="
TEMP_PKG="$TMPDIR_ROOT/package"
TEMP_VERIFIER="$TMPDIR_ROOT/verifier"
cp -r "$PACKAGE_DIR" "$TEMP_PKG"
cp -r "$DEMO_002/verifier" "$TEMP_VERIFIER"

TEMP_REPORT="$TEMP_PKG/verification-report.json"

echo "=== Step 11: Run independent verifier from temp dir ==="
python3 "$TEMP_VERIFIER/independent_verify.py" \
  --package "$TEMP_PKG" \
  --report "$TEMP_REPORT"

echo "=== Step 12: Validate independent verifier report ==="
python3 tools/silver/validate_silver_verification_report_v0_1_0.py "$TEMP_REPORT"

echo "=== Step 13: Inline checks on pass report ==="
python3 - "$TEMP_REPORT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("report_version", report.get("report_version") == "v0.1.0"),
    ("report_type", report.get("report_type") == "proofrail.silver.verification_report"),
    ("report_id", report.get("report_id") == "proofrail-silver-demo-002-independent-verifier-report"),
    ("decision.status", report.get("decision", {}).get("status") == "pass"),
    ("decision.reason", report.get("decision", {}).get("reason") == "all_checks_passed"),
    ("issuer.issuer_id", bool(report.get("issuer", {}).get("issuer_id"))),
    ("subject.bundle_manifest_sha256", bool(report.get("subject", {}).get("bundle_manifest_sha256"))),
    ("checks.trust_check.status", report.get("checks", {}).get("trust_check", {}).get("status") == "pass"),
    ("checks.algorithm_check.status", report.get("checks", {}).get("algorithm_check", {}).get("status") == "pass"),
    ("checks.validity_check.status", report.get("checks", {}).get("validity_check", {}).get("status") == "pass"),
    ("checks.bundle_manifest_checksum_check.status", report.get("checks", {}).get("bundle_manifest_checksum_check", {}).get("status") == "pass"),
    ("checks.revocation_check.performed", report.get("checks", {}).get("revocation_check", {}).get("performed") is True),
    ("checks.revocation_check.status", report.get("checks", {}).get("revocation_check", {}).get("status") == "pass"),
    ("checks.signature_check.status", report.get("checks", {}).get("signature_check", {}).get("status") == "pass"),
    ("checks.underlying_bundle_check.status", report.get("checks", {}).get("underlying_bundle_check", {}).get("status") == "pass"),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: independent pass report inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: independent pass report inline checks valid")
PY

echo "=== Step 14: Tamper test A — corrupt evidence file ==="
# Re-copy fresh package for tamper test A
TAMPER_A_PKG="$TMPDIR_ROOT/tamper-a-package"
cp -r "$PACKAGE_DIR" "$TAMPER_A_PKG"
TAMPER_A_REPORT="$TAMPER_A_PKG/verification-report-tamper-a.json"

# Corrupt one evidence file
echo "TAMPERED CONTENT" >> "$TAMPER_A_PKG/source-repo-subset/demos/composed-bronze-demo-001/evidence/bypass-test-results.md"

TAMPER_A_OUTPUT=$(python3 "$TEMP_VERIFIER/independent_verify.py" \
  --package "$TAMPER_A_PKG" \
  --report "$TAMPER_A_REPORT" 2>&1 || true)

if echo "$TAMPER_A_OUTPUT" | grep -q "independent underlying bundle verification failed"; then
    echo "PASS: independent verifier detected tampered evidence"
else
    echo "FAIL: expected 'independent underlying bundle verification failed' in output"
    echo "  Output: $TAMPER_A_OUTPUT"
    exit 1
fi

echo "=== Step 15: Tamper test B — corrupt bundle manifest ==="
# Re-copy fresh package for tamper test B
TAMPER_B_PKG="$TMPDIR_ROOT/tamper-b-package"
cp -r "$PACKAGE_DIR" "$TAMPER_B_PKG"
TAMPER_B_REPORT="$TAMPER_B_PKG/verification-report-tamper-b.json"

# Corrupt the signed bundle manifest
echo "# tampered" >> "$TAMPER_B_PKG/source-repo-subset/demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml"

TAMPER_B_OUTPUT=$(python3 "$TEMP_VERIFIER/independent_verify.py" \
  --package "$TAMPER_B_PKG" \
  --report "$TAMPER_B_REPORT" 2>&1 || true)

if echo "$TAMPER_B_OUTPUT" | grep -q "independent bundle checksum mismatch\|independent signature verification failed"; then
    echo "PASS: independent verifier detected tampered manifest"
else
    echo "FAIL: expected checksum mismatch or signature failure in output"
    echo "  Output: $TAMPER_B_OUTPUT"
    exit 1
fi

echo "=== Step 16: Revocation test — revoke assertion ID ==="
# Re-copy fresh package for revocation test
REVOKE_PKG="$TMPDIR_ROOT/revoke-package"
cp -r "$PACKAGE_DIR" "$REVOKE_PKG"
REVOKE_REPORT="$REVOKE_PKG/verification-report-revoke.json"

# Write a revocation list that revokes the assertion ID
python3 - "$REVOKE_PKG/source-repo-subset/demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml" <<'PY'
import sys
import yaml
from pathlib import Path

rev_path = Path(sys.argv[1])
rev_list = yaml.safe_load(rev_path.read_text())
rev_list["revoked_assertions"] = [
    {"assertion_id": "proofrail-silver-demo-001", "reason": "regression test revocation"}
]
rev_path.write_text(yaml.safe_dump(rev_list, sort_keys=False, allow_unicode=True))
PY

REVOKE_OUTPUT=$(python3 "$TEMP_VERIFIER/independent_verify.py" \
  --package "$REVOKE_PKG" \
  --report "$REVOKE_REPORT" 2>&1 || true)

if echo "$REVOKE_OUTPUT" | grep -q "independent assertion revoked"; then
    echo "PASS: independent verifier detected revoked assertion"
else
    echo "FAIL: expected 'independent assertion revoked' in output"
    echo "  Output: $REVOKE_OUTPUT"
    exit 1
fi

# Validate the revocation failure report
python3 tools/silver/validate_silver_verification_report_v0_1_0.py "$REVOKE_REPORT"

echo "=== Step 17: Inline checks on revocation failure report ==="
python3 - "$REVOKE_REPORT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("decision.status", report.get("decision", {}).get("status") == "fail"),
    ("decision.reason", report.get("decision", {}).get("reason") == "assertion_revoked"),
    ("checks.revocation_check.performed", report.get("checks", {}).get("revocation_check", {}).get("performed") is True),
    ("checks.revocation_check.status", report.get("checks", {}).get("revocation_check", {}).get("status") == "fail"),
    ("checks.signature_check.status", report.get("checks", {}).get("signature_check", {}).get("status") == "not_performed"),
    ("checks.underlying_bundle_check.status", report.get("checks", {}).get("underlying_bundle_check", {}).get("status") == "not_performed"),
    ("checks.trust_check.status", report.get("checks", {}).get("trust_check", {}).get("status") == "pass"),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: revocation failure report inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: revocation failure report inline checks valid")
PY

echo "=== PASS: independent Silver verifier v0.1.0 regression fixture valid ==="
