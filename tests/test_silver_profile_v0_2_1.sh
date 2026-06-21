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

echo "=== Step 6: silver.base positive test (Demo 001 report has revocation) ==="
BASE_CONFORMANCE="$TMPDIR_ROOT/base-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_1.py \
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
    ("conformance_report_version", report.get("conformance_report_version") == "v0.2.1"),
    ("conformance_report_type", report.get("conformance_report_type") == "proofrail.silver.profile_conformance_report"),
    ("profile.profile_mode", report.get("profile", {}).get("profile_mode") == "silver.base"),
    ("profile.profile_version", report.get("profile", {}).get("profile_version") == "v0.2.1"),
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
    print("FAIL: silver.base v0.2.1 conformance inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.base v0.2.1 conformance inline checks valid")
PY

echo "=== Step 8: Patch report — revocation not performed ==="
PATCHED_REPORT_NO_REV="$TMPDIR_ROOT/patched-report-no-rev.json"
python3 - "$REPORT" "$PATCHED_REPORT_NO_REV" <<'PY'
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

echo "=== Step 9: silver.base with patched report (no revocation) → expect FAIL ==="
BASE_NO_REV_CONFORMANCE="$TMPDIR_ROOT/base-no-rev-conformance.json"
BASE_NO_REV_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report "$PATCHED_REPORT_NO_REV" \
  --output "$BASE_NO_REV_CONFORMANCE" 2>&1 || true)

if echo "$BASE_NO_REV_OUTPUT" | grep -q "revocation_not_performed"; then
    echo "PASS: silver.base correctly rejected report without revocation"
else
    echo "FAIL: expected 'revocation_not_performed' in output"
    echo "  Output: $BASE_NO_REV_OUTPUT"
    exit 1
fi

echo "=== Step 10: silver.base.demo with patched report (no revocation) → expect PASS with warning ==="
DEMO_WARN_CONFORMANCE="$TMPDIR_ROOT/demo-warn-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base.demo \
  --verification-report "$PATCHED_REPORT_NO_REV" \
  --output "$DEMO_WARN_CONFORMANCE"

echo "=== Step 11: Inline checks on silver.base.demo warning path ==="
python3 - "$DEMO_WARN_CONFORMANCE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("conformance_report_version", report.get("conformance_report_version") == "v0.2.1"),
    ("profile.profile_mode", report.get("profile", {}).get("profile_mode") == "silver.base.demo"),
    ("decision.status", report.get("decision", {}).get("status") == "pass"),
    ("decision.reason", report.get("decision", {}).get("reason") == "profile_requirements_satisfied_with_revocation_warning"),
    ("warnings_non_empty", len(report.get("warnings", [])) > 0),
    ("revocation_requirement.status", report.get("checks", {}).get("revocation_requirement", {}).get("status") == "pass"),
    ("independent_package_manifest_valid.status", report.get("checks", {}).get("independent_package_manifest_valid", {}).get("status") == "not_applicable"),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: silver.base.demo warning path inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.base.demo revocation warning path conformance valid")
PY

echo "=== Step 12: Export independent package (v0.2.1) ==="
python3 tools/silver/export_independent_verification_package_v0_2_1.py \
  --bronze-root "$BRONZE_ROOT" \
  --silver-root "$SILVER_ROOT" \
  --output "$PACKAGE_DIR" \
  --force

echo "=== Step 12a: Validate v0.2.1 package manifest handoff fields ==="
python3 - "$PACKAGE_MANIFEST" "$PACKAGE_DIR" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required", file=sys.stderr)
    sys.exit(2)

manifest_path = Path(sys.argv[1])
package_root = Path(sys.argv[2])
manifest = yaml.safe_load(manifest_path.read_text())

errors = []

# package_format_version
if manifest.get("package_format_version") != "v0.2.1":
    errors.append(f"package_format_version: expected 'v0.2.1', got '{manifest.get('package_format_version')}'")

# package_version may remain v0.1.0 (structural layout unchanged)
if manifest.get("package_version") != "v0.1.0":
    errors.append(f"package_version: expected 'v0.1.0', got '{manifest.get('package_version')}'")

# profile_compatibility
pc = manifest.get("profile_compatibility")
if not isinstance(pc, list) or "silver.independent" not in pc:
    errors.append(f"profile_compatibility must include 'silver.independent', got {pc}")

# inputs block exists with expected keys
inputs = manifest.get("inputs")
if not isinstance(inputs, dict):
    errors.append("inputs block missing")
else:
    for key in ["signed_bundle_assertion", "trust_policy", "revocation_list", "bronze_bundle_manifest", "evidence_root"]:
        if key not in inputs:
            errors.append(f"inputs.{key} missing")

    # input paths resolve inside the package
    for key in ["signed_bundle_assertion", "trust_policy", "revocation_list", "bronze_bundle_manifest"]:
        ip = inputs.get(key, "")
        if ip and not (package_root / ip).exists():
            errors.append(f"inputs.{key} path not found: {ip}")

    ev_root = inputs.get("evidence_root", "")
    if ev_root and not (package_root / ev_root).is_dir():
        errors.append(f"inputs.evidence_root directory not found: {ev_root}")

# path_map
pm = manifest.get("path_map")
if not isinstance(pm, dict):
    errors.append("path_map block missing")
elif pm.get("package_repo_root") != "source-repo-subset":
    errors.append(f"path_map.package_repo_root: expected 'source-repo-subset', got '{pm.get('package_repo_root')}'")

# existing paths block preserved
paths = manifest.get("paths")
if not isinstance(paths, dict):
    errors.append("paths block missing")
else:
    for key in ["signed_assertion", "trust_policy", "revocation_list", "bundle_manifest", "bronze_package_root", "report_output"]:
        if key not in paths:
            errors.append(f"paths.{key} missing")

if errors:
    print("FAIL: v0.2.1 package manifest handoff field validation failed")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("PASS: v0.2.1 package manifest handoff fields valid")
PY

echo "=== Step 13: Run independent verifier, produce report ==="
python3 "$DEMO_002/verifier/independent_verify.py" \
  --package "$PACKAGE_DIR" \
  --report "$INDEPENDENT_REPORT"

echo "=== Step 14: silver.independent positive test ==="
INDEPENDENT_CONFORMANCE="$TMPDIR_ROOT/independent-conformance.json"
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.independent \
  --verification-report "$INDEPENDENT_REPORT" \
  --package-manifest "$PACKAGE_MANIFEST" \
  --output "$INDEPENDENT_CONFORMANCE"

echo "=== Step 15: Inline checks on silver.independent conformance report ==="
python3 - "$INDEPENDENT_CONFORMANCE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())

checks = [
    ("conformance_report_version", report.get("conformance_report_version") == "v0.2.1"),
    ("profile.profile_mode", report.get("profile", {}).get("profile_mode") == "silver.independent"),
    ("profile.profile_version", report.get("profile", {}).get("profile_version") == "v0.2.1"),
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
    print("FAIL: silver.independent v0.2.1 conformance inline checks failed")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("PASS: silver.independent v0.2.1 conformance inline checks valid")
PY

echo "=== Step 16: silver.independent missing package manifest → expect package_manifest_missing ==="
NEG_PKG_CONFORMANCE="$TMPDIR_ROOT/neg-pkg-conformance.json"
NEG_PKG_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.independent \
  --verification-report "$INDEPENDENT_REPORT" \
  --output "$NEG_PKG_CONFORMANCE" 2>&1 || true)

if echo "$NEG_PKG_OUTPUT" | grep -q "package_manifest_missing"; then
    echo "PASS: profile validator rejected missing package manifest"
else
    echo "FAIL: expected 'package_manifest_missing' in output"
    echo "  Output: $NEG_PKG_OUTPUT"
    exit 1
fi

echo "=== Step 17: silver.independent patched revocation not performed → expect revocation_not_performed ==="
PATCHED_INDEP_REPORT="$TMPDIR_ROOT/patched-indep-report.json"
python3 - "$INDEPENDENT_REPORT" "$PATCHED_INDEP_REPORT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
report["checks"]["revocation_check"]["performed"] = False
report["checks"]["revocation_check"]["status"] = "not_performed"
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
PY

NEG_REV_CONFORMANCE="$TMPDIR_ROOT/neg-rev-conformance.json"
NEG_REV_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.independent \
  --verification-report "$PATCHED_INDEP_REPORT" \
  --package-manifest "$PACKAGE_MANIFEST" \
  --output "$NEG_REV_CONFORMANCE" 2>&1 || true)

if echo "$NEG_REV_OUTPUT" | grep -q "revocation_not_performed"; then
    echo "PASS: profile validator rejected revocation not performed (silver.independent)"
else
    echo "FAIL: expected 'revocation_not_performed' in output"
    echo "  Output: $NEG_REV_OUTPUT"
    exit 1
fi

echo "=== Step 18: Patch required check to fail → expect required_check_failed ==="
PATCHED_REQ_REPORT="$TMPDIR_ROOT/patched-req-report.json"
python3 - "$REPORT" "$PATCHED_REQ_REPORT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
report["checks"]["trust_check"]["status"] = "fail"
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
PY

NEG_REQ_CONFORMANCE="$TMPDIR_ROOT/neg-req-conformance.json"
NEG_REQ_OUTPUT=$(python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report "$PATCHED_REQ_REPORT" \
  --output "$NEG_REQ_CONFORMANCE" 2>&1 || true)

if echo "$NEG_REQ_OUTPUT" | grep -q "required_check_failed"; then
    echo "PASS: profile validator rejected failed required check"
else
    echo "FAIL: expected 'required_check_failed' in output"
    echo "  Output: $NEG_REQ_OUTPUT"
    exit 1
fi

echo "=== Step 19: Validate canonical examples ==="
bash tests/test_silver_profile_examples_v0_2_1.sh

echo "=== Step 20: PASS — Silver profile v0.2.1 regression fixture valid ==="
