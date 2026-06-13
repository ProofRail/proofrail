#!/usr/bin/env python3
"""Local structural validator shim for Bronze claim YAML.

This is intentionally simple. Replace or compare with the official ProofRail claim
validator v0.1 when available in the repository/tooling path.
"""
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

REQUIRED_TOP_LEVEL = [
    "spec_version",
    "claim_type",
    "claim_id",
    "claim_label",
    "profile",
    "mode",
    "environment",
    "surfaces_in_scope",
    "substrate",
    "protected_actuator_set",
    "controls",
    "evidence",
    "validation",
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


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_claim_v0_1.py <claim.yaml>")
    path = Path(sys.argv[1])
    claim = yaml.safe_load(path.read_text())
    errors = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in claim:
            errors.append(f"missing top-level field: {key}")

    if claim.get("profile") != "bronze":
        errors.append("profile must be bronze")
    if "mcp" not in claim.get("surfaces_in_scope", []):
        errors.append("surfaces_in_scope must include mcp")

    pas = claim.get("protected_actuator_set", {})
    if not pas.get("name"):
        errors.append("protected_actuator_set.name is required")
    if not str(pas.get("hash", "")).startswith("sha256:"):
        errors.append("protected_actuator_set.hash must start with sha256:")
    if not pas.get("contents"):
        errors.append("protected_actuator_set.contents must be non-empty for this demo")

    controls = claim.get("controls", {})
    for key in REQUIRED_CONTROLS:
        if controls.get(key) is not True:
            errors.append(f"controls.{key} must be true")

    evidence = claim.get("evidence", {})
    missing_paths = []
    root = path.resolve().parents[1] if path.resolve().parent.name == "claims" else Path.cwd()
    for key, rel in evidence.items():
        p = (root / rel).resolve()
        if not p.exists() or p.stat().st_size == 0:
            missing_paths.append(f"{key}: {rel}")
    if missing_paths:
        errors.append("evidence files missing or empty: " + "; ".join(missing_paths))

    if errors:
        print("FAIL: claim validation errors")
        for err in errors:
            print("-", err)
        sys.exit(1)

    print(f"PASS: {path} is structurally valid for local ProofRail Bronze claim v0.1 shim")


if __name__ == "__main__":
    main()
