#!/usr/bin/env python3
"""Validate Silver Relying-Party Profile v0.2.1 conformance.

Consumes a Silver Verification Report v0.1.0 and checks whether it satisfies
the Silver profile requirements for the specified mode.

Usage:
  python3 tools/silver/validate_silver_profile_v0_2_1.py \
    --profile-mode silver.base \
    --verification-report <report.json> \
    [--output <conformance-report.json>]

  python3 tools/silver/validate_silver_profile_v0_2_1.py \
    --profile-mode silver.base.demo \
    --verification-report <report.json> \
    [--output <conformance-report.json>]

  python3 tools/silver/validate_silver_profile_v0_2_1.py \
    --profile-mode silver.independent \
    --verification-report <report.json> \
    --package-manifest <package-manifest.yaml> \
    [--output <conformance-report.json>]
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

VALID_MODES = {"silver.base", "silver.base.demo", "silver.independent"}

NOT_PERFORMED = {"status": "not_performed"}

REQUIRED_VERIFICATION_CHECKS = [
    "trust_check",
    "algorithm_check",
    "validity_check",
    "bundle_manifest_checksum_check",
    "signature_check",
    "underlying_bundle_check",
]

LIMITATIONS = [
    "Silver profile conformance is local demo conformance.",
    "Not Gold certification.",
    "Not production certification.",
]


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate Silver Relying-Party Profile v0.2.1 conformance"
    )
    parser.add_argument("--profile-mode", required=True, help="Profile mode: silver.base, silver.base.demo, or silver.independent")
    parser.add_argument("--verification-report", required=True, help="Path to Silver Verification Report JSON")
    parser.add_argument("--package-manifest", default=None, help="Path to package manifest YAML (required for silver.independent)")
    parser.add_argument("--output", default=None, help="Path to write conformance report JSON")
    args = parser.parse_args()

    mode = args.profile_mode
    if mode not in VALID_MODES:
        print(f"ERROR: --profile-mode must be one of {sorted(VALID_MODES)}, got '{mode}'", file=sys.stderr)
        return 2

    report_path = Path(args.verification_report)
    if not report_path.exists():
        print(f"ERROR: verification report not found: {report_path}", file=sys.stderr)
        return 2

    try:
        report = json.loads(report_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in verification report: {e}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("ERROR: verification report root must be a JSON object", file=sys.stderr)
        return 2

    # Build conformance report skeleton
    conformance: dict[str, Any] = {
        "conformance_report_version": "v0.2.1",
        "conformance_report_type": "proofrail.silver.profile_conformance_report",
        "generated_at": "",
        "generated_by": "tools/silver/validate_silver_profile_v0_2_1.py",
        "profile": {
            "profile_id": "proofrail.silver.profile",
            "profile_version": "v0.2.1",
            "profile_mode": mode,
        },
        "input": {
            "verification_report": str(args.verification_report),
            "package_manifest": args.package_manifest,
        },
        "decision": {"status": "", "reason": ""},
        "checks": {
            "verification_report_valid": dict(NOT_PERFORMED),
            "decision_passed": dict(NOT_PERFORMED),
            "required_checks_passed": dict(NOT_PERFORMED),
            "revocation_requirement": dict(NOT_PERFORMED),
            "independent_package_manifest_valid": {"status": "not_applicable"} if mode in ("silver.base", "silver.base.demo") else dict(NOT_PERFORMED),
            "limitations_present": dict(NOT_PERFORMED),
        },
        "warnings": [],
        "limitations": list(LIMITATIONS),
    }

    def _fail(reason: str) -> dict[str, Any]:
        conformance["decision"] = {"status": "fail", "reason": reason}
        conformance["generated_at"] = datetime.now(timezone.utc).isoformat()
        return conformance

    # --- 1. Structural validation via subprocess ---
    result = subprocess.run(
        [sys.executable, "tools/silver/validate_silver_verification_report_v0_1_0.py", str(report_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        conformance["checks"]["verification_report_valid"] = {"status": "fail"}
        _write(args.output, _fail("verification_report_invalid"))
        print("FAIL: Silver profile v0.2.1 conformance failed (verification_report_invalid)")
        return 1
    conformance["checks"]["verification_report_valid"] = {"status": "pass"}

    # --- 2. Decision check ---
    decision = report.get("decision", {})
    if decision.get("status") != "pass" or decision.get("reason") != "all_checks_passed":
        conformance["checks"]["decision_passed"] = {"status": "fail"}
        _write(args.output, _fail("verification_report_failed"))
        print("FAIL: Silver profile v0.2.1 conformance failed (verification_report_failed)")
        return 1
    conformance["checks"]["decision_passed"] = {"status": "pass"}

    # --- 3. Required checks ---
    checks = report.get("checks", {})
    failed_checks = []
    for check_name in REQUIRED_VERIFICATION_CHECKS:
        check = checks.get(check_name, {})
        if check.get("status") != "pass":
            failed_checks.append(check_name)

    if failed_checks:
        conformance["checks"]["required_checks_passed"] = {"status": "fail", "failed": failed_checks}
        _write(args.output, _fail("required_check_failed"))
        print("FAIL: Silver profile v0.2.1 conformance failed (required_check_failed)")
        return 1
    conformance["checks"]["required_checks_passed"] = {"status": "pass"}

    # --- 4. Revocation requirement ---
    revocation = checks.get("revocation_check", {})
    performed = revocation.get("performed", False)
    rev_status = revocation.get("status", "")

    revocation_warning = False

    if mode == "silver.independent":
        # Revocation must be performed and must pass
        if not (performed is True and rev_status == "pass"):
            conformance["checks"]["revocation_requirement"] = {"status": "fail"}
            _write(args.output, _fail("revocation_not_performed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (revocation_not_performed)")
            return 1
        conformance["checks"]["revocation_requirement"] = {"status": "pass"}
    elif mode == "silver.base":
        # v0.2.1: silver.base requires revocation
        if performed is True and rev_status == "pass":
            conformance["checks"]["revocation_requirement"] = {"status": "pass"}
        elif performed is True and rev_status == "fail":
            conformance["checks"]["revocation_requirement"] = {"status": "fail"}
            _write(args.output, _fail("required_check_failed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (required_check_failed)")
            return 1
        else:
            # performed == false / not_performed — fail in v0.2.1 silver.base
            conformance["checks"]["revocation_requirement"] = {"status": "fail"}
            _write(args.output, _fail("revocation_not_performed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (revocation_not_performed)")
            return 1
    else:
        # silver.base.demo — preserves v0.2.0 silver.base semantics
        if performed is True and rev_status == "pass":
            conformance["checks"]["revocation_requirement"] = {"status": "pass"}
        elif performed is True and rev_status == "fail":
            conformance["checks"]["revocation_requirement"] = {"status": "fail"}
            _write(args.output, _fail("required_check_failed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (required_check_failed)")
            return 1
        else:
            # performed == false / not_performed — pass with warning
            conformance["checks"]["revocation_requirement"] = {"status": "pass"}
            conformance["warnings"].append(
                "Revocation check was not performed. silver.base.demo allows this but the relying-party acceptance is weaker without revocation."
            )
            revocation_warning = True

    # --- 5. Independent package manifest check ---
    if mode == "silver.independent":
        if not args.package_manifest:
            conformance["checks"]["independent_package_manifest_valid"] = {"status": "fail"}
            _write(args.output, _fail("package_manifest_missing"))
            print("FAIL: Silver profile v0.2.1 conformance failed (package_manifest_missing)")
            return 1

        manifest_path = Path(args.package_manifest)
        if not manifest_path.exists():
            conformance["checks"]["independent_package_manifest_valid"] = {"status": "fail"}
            _write(args.output, _fail("package_manifest_missing"))
            print("FAIL: Silver profile v0.2.1 conformance failed (package_manifest_missing)")
            return 1

        try:
            manifest = yaml.safe_load(manifest_path.read_text())
        except Exception:
            conformance["checks"]["independent_package_manifest_valid"] = {"status": "fail"}
            _write(args.output, _fail("independence_requirement_failed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (independence_requirement_failed)")
            return 1

        if not isinstance(manifest, dict):
            conformance["checks"]["independent_package_manifest_valid"] = {"status": "fail"}
            _write(args.output, _fail("independence_requirement_failed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (independence_requirement_failed)")
            return 1

        independence_errors: list[str] = []

        if manifest.get("package_type") != "proofrail.silver.independent_verification_package":
            independence_errors.append("package_type mismatch")

        verifier_meta = manifest.get("verifier", {})
        if not isinstance(verifier_meta, dict):
            independence_errors.append("verifier metadata missing")
        else:
            for field in ("verifier_demo", "verifier_version", "expected_report_schema"):
                if field not in verifier_meta:
                    independence_errors.append(f"verifier.{field} missing")

        report_verifier_id = report.get("verifier", {}).get("verifier_id", "")
        if report_verifier_id != "proofrail-demo-independent-verifier":
            independence_errors.append(f"report verifier_id mismatch: expected 'proofrail-demo-independent-verifier', got '{report_verifier_id}'")

        # v0.2.1 package handoff field validation
        fmt_ver = manifest.get("package_format_version")
        if fmt_ver != "v0.2.1":
            independence_errors.append(f"package_format_version: expected 'v0.2.1', got '{fmt_ver}'")

        profile_compat = manifest.get("profile_compatibility")
        if not isinstance(profile_compat, list) or "silver.independent" not in profile_compat:
            independence_errors.append("profile_compatibility must include 'silver.independent'")

        inputs_block = manifest.get("inputs")
        if not isinstance(inputs_block, dict):
            independence_errors.append("inputs block missing")
        else:
            required_input_keys = ["signed_bundle_assertion", "trust_policy", "revocation_list", "bronze_bundle_manifest", "evidence_root"]
            for ik in required_input_keys:
                if ik not in inputs_block:
                    independence_errors.append(f"inputs.{ik} missing")
            # Verify input paths resolve inside the package (reject traversal)
            package_root = manifest_path.parent.resolve()
            for ik in ["signed_bundle_assertion", "trust_policy", "revocation_list", "bronze_bundle_manifest"]:
                ip = inputs_block.get(ik)
                if ip:
                    resolved = (package_root / ip).resolve()
                    if not str(resolved).startswith(str(package_root) + "/"):
                        independence_errors.append(f"inputs.{ik} resolves outside package root: {ip}")
                    elif not resolved.exists():
                        independence_errors.append(f"inputs.{ik} path not found in package: {ip}")
            # evidence_root should be a directory inside the package
            ev_root = inputs_block.get("evidence_root")
            if ev_root:
                resolved_ev = (package_root / ev_root).resolve()
                if not str(resolved_ev).startswith(str(package_root) + "/"):
                    independence_errors.append(f"inputs.evidence_root resolves outside package root: {ev_root}")
                elif not resolved_ev.is_dir():
                    independence_errors.append(f"inputs.evidence_root directory not found in package: {ev_root}")

        path_map = manifest.get("path_map")
        if not isinstance(path_map, dict):
            independence_errors.append("path_map block missing")
        elif path_map.get("package_repo_root") != "source-repo-subset":
            independence_errors.append(f"path_map.package_repo_root: expected 'source-repo-subset', got '{path_map.get('package_repo_root')}'")

        if independence_errors:
            conformance["checks"]["independent_package_manifest_valid"] = {"status": "fail", "errors": independence_errors}
            _write(args.output, _fail("independence_requirement_failed"))
            print("FAIL: Silver profile v0.2.1 conformance failed (independence_requirement_failed)")
            return 1

        conformance["checks"]["independent_package_manifest_valid"] = {"status": "pass"}

    # --- 6. Limitations check ---
    limitations = report.get("limitations", [])
    if not isinstance(limitations, list) or len(limitations) == 0:
        conformance["checks"]["limitations_present"] = {"status": "fail"}
        _write(args.output, _fail("limitations_missing"))
        print("FAIL: Silver profile v0.2.1 conformance failed (limitations_missing)")
        return 1
    conformance["checks"]["limitations_present"] = {"status": "pass"}

    # --- All checks passed ---
    if revocation_warning:
        conformance["decision"] = {"status": "pass", "reason": "profile_requirements_satisfied_with_revocation_warning"}
    else:
        conformance["decision"] = {"status": "pass", "reason": "profile_requirements_satisfied"}

    conformance["generated_at"] = datetime.now(timezone.utc).isoformat()
    _write(args.output, conformance)
    print("PASS: Silver profile v0.2.1 conformance valid")
    return 0


def _write(output_path: str | None, conformance: dict[str, Any]) -> None:
    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(conformance, indent=2, default=str) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
