#!/usr/bin/env python3
"""Validate a ProofRail Silver Verification Report v0.1.0 structure.

Performs structural validation only — does not rerun cryptographic verification.

Usage:
  python3 tools/silver/validate_silver_verification_report_v0_1_0.py <report.json>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")

REQUIRED_TOP_LEVEL = [
    "report_version",
    "report_type",
    "report_id",
    "generated_at",
    "generated_by",
    "verifier",
    "inputs",
    "decision",
    "checks",
    "limitations",
]

REQUIRED_CHECKS = [
    "trust_check",
    "algorithm_check",
    "validity_check",
    "bundle_manifest_checksum_check",
    "revocation_check",
    "signature_check",
    "underlying_bundle_check",
]

VALID_STATUSES = {"pass", "fail", "not_performed"}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate a Silver Verification Report v0.1.0"
    )
    parser.add_argument("report", help="Path to verification report JSON")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"ERROR: report not found: {report_path}", file=sys.stderr)
        return 2

    try:
        report = json.loads(report_path.read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL: invalid JSON: {e}")
        return 1

    if not isinstance(report, dict):
        print("FAIL: report root must be a JSON object")
        return 1

    errors: list[str] = []

    # Required top-level fields
    for field in REQUIRED_TOP_LEVEL:
        if field not in report:
            errors.append(f"missing required top-level field: {field}")

    if errors:
        _print_errors(errors)
        return 1

    # report_version
    if report["report_version"] != "v0.1.0":
        errors.append(f"report_version must be 'v0.1.0', got '{report['report_version']}'")

    # report_type
    if report["report_type"] != "proofrail.silver.verification_report":
        errors.append(f"report_type must be 'proofrail.silver.verification_report', got '{report['report_type']}'")

    # decision
    decision = report.get("decision", {})
    if not isinstance(decision, dict):
        errors.append("decision must be a JSON object")
    else:
        status = decision.get("status", "")
        if status not in ("pass", "fail"):
            errors.append(f"decision.status must be 'pass' or 'fail', got '{status}'")
        reason = decision.get("reason", "")
        if not reason or not isinstance(reason, str):
            errors.append("decision.reason must be a non-empty string")

    # verifier
    verifier = report.get("verifier", {})
    if not isinstance(verifier, dict):
        errors.append("verifier must be a JSON object")
    elif "verifier_id" not in verifier:
        errors.append("verifier.verifier_id is required")

    # inputs
    inputs = report.get("inputs", {})
    if not isinstance(inputs, dict):
        errors.append("inputs must be a JSON object")
    elif "assertion_path" not in inputs:
        errors.append("inputs.assertion_path is required")

    # checks
    checks = report.get("checks", {})
    if not isinstance(checks, dict):
        errors.append("checks must be a JSON object")
    else:
        for check_name in REQUIRED_CHECKS:
            if check_name not in checks:
                errors.append(f"missing required check block: {check_name}")
                continue

            check = checks[check_name]
            if not isinstance(check, dict):
                errors.append(f"{check_name} must be a JSON object")
                continue

            if "status" not in check:
                errors.append(f"{check_name}.status is required")
            elif check["status"] not in VALID_STATUSES:
                errors.append(f"{check_name}.status must be one of {VALID_STATUSES}, got '{check['status']}'")

            # revocation_check must have 'performed'
            if check_name == "revocation_check" and "performed" not in check:
                errors.append("revocation_check.performed is required")

    # SHA-256 field validation where present
    _check_sha256(report, "issuer.public_key_fingerprint_sha256", errors)
    _check_sha256(report, "subject.bundle_manifest_sha256", errors)
    if isinstance(checks, dict):
        checksum_check = checks.get("bundle_manifest_checksum_check", {})
        if isinstance(checksum_check, dict):
            for field in ("expected_sha256", "actual_sha256"):
                val = checksum_check.get(field, "")
                if val and not SHA256_RE.match(val):
                    errors.append(f"checks.bundle_manifest_checksum_check.{field} must match sha256:<64 hex>, got '{val}'")

    # limitations
    limitations = report.get("limitations", [])
    if not isinstance(limitations, list) or len(limitations) == 0:
        errors.append("limitations must be a non-empty list")

    if errors:
        _print_errors(errors)
        return 1

    print("PASS: Silver verification report v0.1.0 structurally valid")
    return 0


def _check_sha256(report: dict, dotpath: str, errors: list[str]) -> None:
    """Validate a sha256 field at a dotted path if present and non-empty."""
    parts = dotpath.split(".")
    obj = report
    for part in parts[:-1]:
        obj = obj.get(part, {})
        if not isinstance(obj, dict):
            return
    val = obj.get(parts[-1], "")
    if val and not SHA256_RE.match(val):
        errors.append(f"{dotpath} must match sha256:<64 hex>, got '{val}'")


def _print_errors(errors: list[str]) -> None:
    print("FAIL: Silver verification report v0.1.0 validation failed")
    for e in errors:
        print(f"  - {e}")


if __name__ == "__main__":
    raise SystemExit(main())
