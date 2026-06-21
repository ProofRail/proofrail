#!/usr/bin/env bash
set -euo pipefail

EXAMPLES_DIR="examples/silver-profile-conformance"

VALID_MODES='["silver.base", "silver.base.demo", "silver.independent"]'

REQUIRED_CHECKS='["verification_report_valid", "decision_passed", "required_checks_passed", "revocation_requirement", "independent_package_manifest_valid", "limitations_present"]'

EXAMPLE_FILES=(
  "pass-base-v0.2.1.json"
  "pass-base-demo-revocation-warning-v0.2.1.json"
  "pass-independent-v0.2.1.json"
  "fail-missing-revocation-v0.2.1.json"
  "fail-missing-package-manifest-v0.2.1.json"
  "fail-required-check-v0.2.1.json"
)

echo "=== Validating ${#EXAMPLE_FILES[@]} canonical Silver profile conformance examples ==="

for f in "${EXAMPLE_FILES[@]}"; do
  FPATH="$EXAMPLES_DIR/$f"

  if [ ! -f "$FPATH" ]; then
    echo "FAIL: example file not found: $FPATH"
    exit 1
  fi

  echo "--- Validating: $f ---"

  python3 - "$FPATH" "$VALID_MODES" "$REQUIRED_CHECKS" <<'PY'
import json
import sys
from pathlib import Path

fpath = sys.argv[1]
valid_modes = json.loads(sys.argv[2])
required_checks = json.loads(sys.argv[3])

report = json.loads(Path(fpath).read_text())
errors = []

# Required top-level fields
for field in ["conformance_report_version", "conformance_report_type", "generated_at",
              "generated_by", "profile", "input", "decision", "checks", "warnings", "limitations"]:
    if field not in report:
        errors.append(f"missing top-level field: {field}")

# Version
if report.get("conformance_report_version") != "v0.2.1":
    errors.append(f"conformance_report_version: expected 'v0.2.1', got '{report.get('conformance_report_version')}'")

# Type
if report.get("conformance_report_type") != "proofrail.silver.profile_conformance_report":
    errors.append(f"conformance_report_type: expected 'proofrail.silver.profile_conformance_report', got '{report.get('conformance_report_type')}'")

# Profile block
profile = report.get("profile", {})
if profile.get("profile_mode") not in valid_modes:
    errors.append(f"profile_mode: expected one of {valid_modes}, got '{profile.get('profile_mode')}'")

if profile.get("profile_version") != "v0.2.1":
    errors.append(f"profile_version: expected 'v0.2.1', got '{profile.get('profile_version')}'")

# Decision block
decision = report.get("decision", {})
if decision.get("status") not in ("pass", "fail"):
    errors.append(f"decision.status: expected 'pass' or 'fail', got '{decision.get('status')}'")

if not decision.get("reason"):
    errors.append("decision.reason: must be a non-empty string")

# Check blocks
checks = report.get("checks", {})
for check_name in required_checks:
    if check_name not in checks:
        errors.append(f"missing check block: {check_name}")
    else:
        status = checks[check_name].get("status")
        if status not in ("pass", "fail", "not_performed", "not_applicable"):
            errors.append(f"{check_name}.status: invalid status '{status}'")

# Decision/status consistency
if decision.get("status") == "pass":
    # All reached checks must be pass or not_applicable
    for check_name in required_checks:
        if check_name in checks:
            s = checks[check_name].get("status")
            if s not in ("pass", "not_applicable"):
                errors.append(f"decision is pass but {check_name}.status is '{s}'")

# Warnings is a list
if not isinstance(report.get("warnings"), list):
    errors.append("warnings: must be a list")

# Limitations is a non-empty list
limitations = report.get("limitations", [])
if not isinstance(limitations, list) or len(limitations) == 0:
    errors.append("limitations: must be a non-empty list")

# revocation_warning reason restricted to silver.base.demo
if decision.get("reason") == "profile_requirements_satisfied_with_revocation_warning":
    if profile.get("profile_mode") != "silver.base.demo":
        errors.append(f"profile_requirements_satisfied_with_revocation_warning used in mode '{profile.get('profile_mode')}' (only valid for silver.base.demo)")

if errors:
    print(f"FAIL: {fpath}")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"PASS: {fpath}")
PY

done

echo "=== PASS: All ${#EXAMPLE_FILES[@]} canonical examples valid ==="
