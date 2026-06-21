#!/usr/bin/env bash
set -euo pipefail

BRONZE_ROOT="demos/composed-bronze-demo-001"
SILVER_ROOT="demos/silver-demo-001"
DEMO_002="demos/silver-demo-002-independent-verifier"
REPORT="$SILVER_ROOT/runtime/verification-report.json"
PACKAGE_DIR="$DEMO_002/runtime/package"
PACKAGE_MANIFEST="$PACKAGE_DIR/package-manifest.yaml"
INDEPENDENT_REPORT="$PACKAGE_DIR/verification-report.json"

# Temp directory for patched reports — cleaned up on exit
TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

echo "=== Step 1: Generate v0.1.2 claim ==="
python3 tools/claims/generate_bronze_claim_v0_1_2.py "$BRONZE_ROOT"

echo "=== Step 2: Verify v0.1.2 evidence checksums ==="
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py \
  "$BRONZE_ROOT/claims/bronze-claim-demo-001.yaml" "$BRONZE_ROOT"

echo "=== Step 3: Generate v0.1.3 bundle manifest ==="
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py "$BRONZE_ROOT"

echo "=== Step 4: Verify v0.1.3 bundle manifest ==="
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py \
  "$BRONZE_ROOT/evidence-bundle-manifest-v0.1.3.yaml" "$BRONZE_ROOT"

echo "=== Step 5: Run silver-demo-001 ==="
make silver-demo-001

echo "=== Step 6: Validate silver.base profile against Demo 001 report ==="
BASE_CONFORMANCE="$TMPDIR_ROOT/base-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.base \
  --verification-report "$REPORT" \
  --output "$BASE_CONFORMANCE"

echo "=== Step 7: Inline checks on silver.base conformance report ==="
python3 - "$BASE_CONFORMANCE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("conformance_report_version", report.get("conformance_report_version") == "v0.2.0"),
    ("conformance_report_type", report.get("conformance_report_type") == "proofrail.silver.profile_conformance_report"),
    ("profile.profile_mode", report.get("profile", {}).get("profile_mode") == "silver.base"),
    ("decision.status", report.get("decision", {}).get("status") == "pass"),
    ("decision.reason", report.get("decision", {}).get("reason") == "profile_requirements_satisfied"),
    ("checks.verification_report_valid.status", report.get("checks", {}).get("verification_report_valid", {}).get("status") == "pass"),
    ("checks.decision_passed.status", report.get("checks", {}).get("decision_passed", {}).get("status") == "pass"),
    ("checks.required_checks_passed.status", report.get("checks", {}).get("required_checks_passed", {}).get("status") == "pass"),
    ("checks.revocation_requirement.status", report.get("checks", {}).get("revocation_requirement", {}).get("status") == "pass"),
    ("checks.independent_package_manifest_valid.status", report.get("checks", {}).get("independent_package_manifest_valid", {}).get("status") == "not_applicable"),
    ("checks.limitations_present.status", report.get("checks", {}).get("limitations_present", {}).get("status") == "pass"),
    ("warnings_empty", report.get("warnings") == []),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: silver.base conformance inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.base conformance inline checks valid")
PY

echo "=== Step 8: Export independent verification package ==="
python3 tools/silver/export_independent_verification_package_v0_1_0.py \
  --bronze-root "$BRONZE_ROOT" \
  --silver-root "$SILVER_ROOT" \
  --output "$PACKAGE_DIR" \
  --force

echo "=== Step 9: Run independent verifier, produce report ==="
python3 "$DEMO_002/verifier/independent_verify.py" \
  --package "$PACKAGE_DIR" \
  --report "$INDEPENDENT_REPORT"

echo "=== Step 10: Validate silver.independent profile ==="
INDEPENDENT_CONFORMANCE="$TMPDIR_ROOT/independent-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.independent \
  --verification-report "$INDEPENDENT_REPORT" \
  --package-manifest "$PACKAGE_MANIFEST" \
  --output "$INDEPENDENT_CONFORMANCE"

echo "=== Step 11: Inline checks on silver.independent conformance report ==="
python3 - "$INDEPENDENT_CONFORMANCE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("conformance_report_version", report.get("conformance_report_version") == "v0.2.0"),
    ("profile.profile_mode", report.get("profile", {}).get("profile_mode") == "silver.independent"),
    ("decision.status", report.get("decision", {}).get("status") == "pass"),
    ("decision.reason", report.get("decision", {}).get("reason") == "profile_requirements_satisfied"),
    ("checks.verification_report_valid.status", report.get("checks", {}).get("verification_report_valid", {}).get("status") == "pass"),
    ("checks.decision_passed.status", report.get("checks", {}).get("decision_passed", {}).get("status") == "pass"),
    ("checks.required_checks_passed.status", report.get("checks", {}).get("required_checks_passed", {}).get("status") == "pass"),
    ("checks.revocation_requirement.status", report.get("checks", {}).get("revocation_requirement", {}).get("status") == "pass"),
    ("checks.independent_package_manifest_valid.status", report.get("checks", {}).get("independent_package_manifest_valid", {}).get("status") == "pass"),
    ("checks.limitations_present.status", report.get("checks", {}).get("limitations_present", {}).get("status") == "pass"),
    ("warnings_empty", report.get("warnings") == []),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: silver.independent conformance inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.independent conformance inline checks valid")
PY

echo "=== Step 12: Negative test A — failed verification report ==="
PATCHED_REPORT_A="$TMPDIR_ROOT/patched-report-a.json"
python3 - "$REPORT" "$PATCHED_REPORT_A" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
report["decision"]["status"] = "fail"
report["decision"]["reason"] = "test_forced_failure"
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
PY

NEG_A_CONFORMANCE="$TMPDIR_ROOT/neg-a-conformance.json"
NEG_A_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.base \
  --verification-report "$PATCHED_REPORT_A" \
  --output "$NEG_A_CONFORMANCE" 2>&1 || true)

if echo "$NEG_A_OUTPUT" | grep -q "verification_report_failed"; then
    echo "PASS: profile validator rejected failed verification report"
else
    echo "FAIL: expected 'verification_report_failed' in output"
    echo "  Output: $NEG_A_OUTPUT"
    exit 1
fi

echo "=== Step 13: Negative test B — missing package manifest for silver.independent ==="
NEG_B_CONFORMANCE="$TMPDIR_ROOT/neg-b-conformance.json"
NEG_B_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.independent \
  --verification-report "$INDEPENDENT_REPORT" \
  --output "$NEG_B_CONFORMANCE" 2>&1 || true)

if echo "$NEG_B_OUTPUT" | grep -q "package_manifest_missing"; then
    echo "PASS: profile validator rejected missing package manifest"
else
    echo "FAIL: expected 'package_manifest_missing' in output"
    echo "  Output: $NEG_B_OUTPUT"
    exit 1
fi

echo "=== Step 14: Negative test C — revocation not performed for silver.independent ==="
PATCHED_REPORT_C="$TMPDIR_ROOT/patched-report-c.json"
python3 - "$INDEPENDENT_REPORT" "$PATCHED_REPORT_C" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
report["checks"]["revocation_check"]["performed"] = False
report["checks"]["revocation_check"]["status"] = "not_performed"
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
PY

NEG_C_CONFORMANCE="$TMPDIR_ROOT/neg-c-conformance.json"
NEG_C_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.independent \
  --verification-report "$PATCHED_REPORT_C" \
  --package-manifest "$PACKAGE_MANIFEST" \
  --output "$NEG_C_CONFORMANCE" 2>&1 || true)

if echo "$NEG_C_OUTPUT" | grep -q "revocation_not_performed"; then
    echo "PASS: profile validator rejected revocation not performed (silver.independent)"
else
    echo "FAIL: expected 'revocation_not_performed' in output"
    echo "  Output: $NEG_C_OUTPUT"
    exit 1
fi

echo "=== Step 15: Positive test D — silver.base with revocation not performed ==="
PATCHED_REPORT_D="$TMPDIR_ROOT/patched-report-d.json"
python3 - "$REPORT" "$PATCHED_REPORT_D" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
report["checks"]["revocation_check"]["performed"] = False
report["checks"]["revocation_check"]["status"] = "not_performed"
if "revocation_list" in report["checks"]["revocation_check"]:
    del report["checks"]["revocation_check"]["revocation_list"]
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
PY

WARN_CONFORMANCE="$TMPDIR_ROOT/warn-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.base \
  --verification-report "$PATCHED_REPORT_D" \
  --output "$WARN_CONFORMANCE"

python3 - "$WARN_CONFORMANCE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("decision.status", report.get("decision", {}).get("status") == "pass"),
    ("decision.reason", report.get("decision", {}).get("reason") == "profile_requirements_satisfied_with_revocation_warning"),
    ("warnings_non_empty", len(report.get("warnings", [])) > 0),
    ("revocation_requirement.status", report.get("checks", {}).get("revocation_requirement", {}).get("status") == "pass"),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: revocation warning conformance inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.base revocation warning path conformance valid")
PY

echo "=== PASS: Silver profile v0.2.0 regression fixture valid ==="
