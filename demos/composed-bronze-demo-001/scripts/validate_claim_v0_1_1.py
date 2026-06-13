#!/usr/bin/env python3
"""Local structural validator for ProofRail Bronze Claim Schema v0.1.1.

This is a lightweight validator shim. It intentionally validates structure and
truth-preserving control semantics, not production conformance.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REQUIRED_TOP = [
    "spec_version",
    "claim_type",
    "claim_id",
    "claim_label",
    "profile",
    "mode",
    "environment",
    "surfaces_in_scope",
    "protected_actuator_set",
    "controls",
    "control_details",
    "control_mapping",
    "evidence",
    "validation",
    "limitations",
]

REQUIRED_COMPOSED_SUBSTRATE = [
    "name",
    "type",
    "version_declared",
    "role",
]

REQUIRED_ACTUATOR_SET = [
    "name",
    "surface",
    "hash",
]

REQUIRED_CONTROLS = [
    "declared_actuator_set",
    "gateway_mediation",
    "bypass_prevention_tested",
    "stop_control_demonstrated",
    "rate_limit_or_circuit_breaker_demonstrated",
    "normalized_audit_evidence",
    "performance_measured",
    "runbook_present",
]

REQUIRED_CONTROL_DETAILS = [
    "rate_limit_observed",
    "circuit_breaker_observed",
]

REQUIRED_EVIDENCE = [
    "architecture_notes",
    "runbook",
    "protected_actuator_set_manifest",
    "bypass_prevention_test",
    "stop_control_test",
    "rate_limit_circuit_breaker_test",
    "audit_sample",
    "performance_test",
]

REQUIRED_VALIDATION = [
    "type",
    "validator",
    "generated_at",
    "missing_evidence_files",
]


def err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def is_bool(x) -> bool:
    return isinstance(x, bool)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_bronze_claim_v0_1_1.py <claim.yaml>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    claim = yaml.safe_load(path.read_text())
    errors: list[str] = []

    if not isinstance(claim, dict):
        print("FAIL: claim root must be a mapping")
        return 1

    for key in REQUIRED_TOP:
        if key not in claim:
            err(errors, f"missing required top-level field: {key}")

    if claim.get("spec_version") != "v0.1.1":
        err(errors, "spec_version must be v0.1.1")

    if claim.get("claim_type") not in {"proofrail.bronze.composed", "proofrail.bronze.native"}:
        err(errors, "claim_type must be proofrail.bronze.composed or proofrail.bronze.native")

    if claim.get("profile") != "bronze":
        err(errors, "profile must be bronze")

    if claim.get("mode") not in {"monitor", "enforce"}:
        err(errors, "mode must be monitor or enforce")

    if claim.get("environment") not in {"dev", "test", "staging", "prod"}:
        err(errors, "environment must be dev, test, staging, or prod")

    surfaces = claim.get("surfaces_in_scope")
    if not isinstance(surfaces, list) or not surfaces:
        err(errors, "surfaces_in_scope must be a non-empty list")

    if claim.get("claim_type") == "proofrail.bronze.composed":
        substrate = claim.get("substrate")
        if not isinstance(substrate, dict):
            err(errors, "substrate is required for composed Bronze claims")
        else:
            for key in REQUIRED_COMPOSED_SUBSTRATE:
                if key not in substrate:
                    err(errors, f"substrate.{key} is required for composed Bronze claims")

    pas = claim.get("protected_actuator_set", {})
    if not isinstance(pas, dict):
        err(errors, "protected_actuator_set must be a mapping")
    else:
        for key in REQUIRED_ACTUATOR_SET:
            if key not in pas:
                err(errors, f"protected_actuator_set.{key} is required")

        h = pas.get("hash")
        if not isinstance(h, str) or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", h):
            err(errors, "protected_actuator_set.hash must be sha256:<64 hex chars>")

        if "contents" in pas and not isinstance(pas["contents"], list):
            err(errors, "protected_actuator_set.contents must be a list if present")

    controls = claim.get("controls", {})
    if not isinstance(controls, dict):
        err(errors, "controls must be a mapping")
    else:
        for key in REQUIRED_CONTROLS:
            if key not in controls:
                err(errors, f"controls.{key} is required")
            elif not is_bool(controls[key]):
                err(errors, f"controls.{key} must be boolean")
            elif controls[key] is not True:
                err(errors, f"controls.{key} must be true for a passing Bronze v0.1.1 claim")

    details = claim.get("control_details", {})
    if not isinstance(details, dict):
        err(errors, "control_details must be a mapping")
    else:
        for key in REQUIRED_CONTROL_DETAILS:
            if key not in details:
                err(errors, f"control_details.{key} is required")
            elif not is_bool(details[key]):
                err(errors, f"control_details.{key} must be boolean")

        aggregate = controls.get("rate_limit_or_circuit_breaker_demonstrated") is True
        if aggregate:
            if not (details.get("rate_limit_observed") is True or details.get("circuit_breaker_observed") is True):
                err(
                    errors,
                    "controls.rate_limit_or_circuit_breaker_demonstrated is true, "
                    "but neither control_details.rate_limit_observed nor "
                    "control_details.circuit_breaker_observed is true",
                )

    evidence = claim.get("evidence", {})
    if not isinstance(evidence, dict):
        err(errors, "evidence must be a mapping")
    else:
        for key in REQUIRED_EVIDENCE:
            if key not in evidence:
                err(errors, f"evidence.{key} is required")
            elif not isinstance(evidence[key], str) or not evidence[key]:
                err(errors, f"evidence.{key} must be a non-empty string")

    validation = claim.get("validation", {})
    if not isinstance(validation, dict):
        err(errors, "validation must be a mapping")
    else:
        for key in REQUIRED_VALIDATION:
            if key not in validation:
                err(errors, f"validation.{key} is required")

        if validation.get("type") not in {"self-attested-demo", "self-attested", "third-party"}:
            err(errors, "validation.type must be self-attested-demo, self-attested, or third-party")

        if not isinstance(validation.get("missing_evidence_files"), list):
            err(errors, "validation.missing_evidence_files must be a list")

    limitations = claim.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        err(errors, "limitations must be a non-empty list")
    elif not all(isinstance(x, str) and x.strip() for x in limitations):
        err(errors, "limitations must contain only non-empty strings")

    if errors:
        print("FAIL: claim validation errors")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"PASS: {path} is structurally valid for ProofRail Bronze Claim Schema v0.1.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
