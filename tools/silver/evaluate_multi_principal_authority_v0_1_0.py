#!/usr/bin/env python3
"""Evaluate a protected action request against a multi-principal authority fixture.

Produces a Silver Protected Action Decision Report v0.1.0.

Usage:
  python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
    --fixture <fixture.yaml> \
    --request <request.json> \
    --decision-time <ISO-8601> \
    --output <decision-report.json>
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


LIMITATIONS = [
    "Local deterministic authority fixture only.",
    "No live actuators invoked.",
    "Not a production authorization system.",
    "Not prompt-injection detection.",
    "Not Gold certification.",
]

CONSTRAINT_PARAM_MAP = {
    "max_amount_usd": "amount_usd",
    "allowed_vendor_ids": "vendor_id",
    "allowed_dataset_ids": "dataset_id",
    "allowed_environments": "environment",
    "allowed_change_types": "change_type",
}


def parse_iso8601(s: str) -> datetime | None:
    """Parse an ISO-8601 timestamp string."""
    try:
        # Handle Z suffix
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def build_delegation_chain(grant_id: str, grant_map: dict[str, dict]) -> tuple[list[str], str | None]:
    """Build delegation chain from grant to root. Returns (chain, error_reason)."""
    chain: list[str] = []
    visited: set[str] = set()
    current_id = grant_id

    while True:
        if current_id in visited:
            return chain, "delegation_chain_invalid"
        visited.add(current_id)

        if current_id not in grant_map:
            return chain, "delegation_chain_invalid"

        grant = grant_map[current_id]
        chain.append(current_id)

        if grant.get("grant_type") == "direct":
            # Reached root
            return chain, None

        parent_id = grant.get("parent_grant_id")
        if not parent_id or parent_id not in grant_map:
            return chain, "delegation_chain_invalid"

        parent = grant_map[parent_id]
        parent_delegation = parent.get("delegation", {})
        if not isinstance(parent_delegation, dict) or parent_delegation.get("permitted") is not True:
            return chain, "delegation_not_permitted"

        # Validate scopes subset
        parent_scopes = set(parent.get("scopes", []))
        child_scopes = set(grant.get("scopes", []))
        if not child_scopes.issubset(parent_scopes):
            return chain, "delegation_scope_expanded"

        current_id = parent_id


def evaluate_request(
    fixture: dict[str, Any],
    request: dict[str, Any],
    decision_time: datetime,
) -> dict[str, Any]:
    """Evaluate a request against the fixture. Returns a decision report."""

    fixture_id = fixture.get("fixture_id", "")
    request_id = request.get("request_id", "")

    # Build lookup maps
    principal_ids = {p.get("principal_id") for p in fixture.get("principals", []) if isinstance(p, dict)}
    action_map = {a.get("action_id"): a for a in fixture.get("protected_actions", []) if isinstance(a, dict)}
    grant_map = {g.get("grant_id"): g for g in fixture.get("authority_grants", []) if isinstance(g, dict)}
    revocations = fixture.get("revocations", [])

    checks: list[dict[str, str]] = []

    def make_report(status: str, reason: str, matched_grant: str | None = None, chain: list[str] | None = None) -> dict[str, Any]:
        action_id = request.get("action_id", "")
        action = action_map.get(action_id, {})
        return {
            "report_type": "proofrail.silver.protected_action_decision_report",
            "report_version": "v0.1.0",
            "fixture_id": fixture_id,
            "request_id": request_id,
            "decision_time": decision_time.isoformat().replace("+00:00", "Z") if decision_time.tzinfo else decision_time.isoformat() + "Z",
            "decision": {"status": status, "reason": reason},
            "execution": {"performed": False, "reason": "decision_report_only"},
            "principal": {"requesting_principal_id": request.get("requesting_principal_id", "")},
            "action": {
                "action_id": action_id,
                "required_scope": action.get("required_scope", ""),
            },
            "authority": {
                "claimed_grant_id": request.get("claimed_authority", {}).get("grant_id", ""),
                "matched_grant_id": matched_grant,
                "delegation_chain": chain or [],
            },
            "checks": list(checks),
            "limitations": list(LIMITATIONS),
        }

    def deny(reason: str, detail: str, matched_grant: str | None = None, chain: list[str] | None = None) -> dict[str, Any]:
        checks.append({"check_id": reason.replace("authority_", "grant_not_").replace("constraint_", "constraints_") if "revoked" in reason or "expired" in reason else _current_check_id(), "status": "fail", "detail": detail})
        return make_report("deny", reason, matched_grant, chain)

    _check_id_holder: list[str] = [""]

    def _current_check_id() -> str:
        return _check_id_holder[0]

    def pass_check(check_id: str, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "pass", "detail": detail})

    # --- Check 1: request_structure ---
    _check_id_holder[0] = "request_structure"
    if request.get("request_type") != "proofrail.silver.protected_action_request":
        return deny("invalid_request_structure", "request_type must be 'proofrail.silver.protected_action_request'")
    if request.get("request_version") != "v0.1.0":
        return deny("invalid_request_structure", f"request_version must be 'v0.1.0', got '{request.get('request_version')}'")
    for field in ("request_id", "requesting_principal_id", "action_id", "parameters", "claimed_authority"):
        if field not in request:
            return deny("invalid_request_structure", f"missing required field: {field}")
    if not isinstance(request.get("claimed_authority"), dict) or "grant_id" not in request["claimed_authority"]:
        return deny("invalid_request_structure", "claimed_authority must contain grant_id")
    pass_check("request_structure", "request structure valid")

    # --- Check 2: principal_known ---
    _check_id_holder[0] = "principal_known"
    requesting_principal = request.get("requesting_principal_id", "")
    if requesting_principal not in principal_ids:
        return deny("unknown_principal", f"principal '{requesting_principal}' not in fixture")
    pass_check("principal_known", f"principal '{requesting_principal}' found in fixture")

    # --- Check 3: action_known ---
    _check_id_holder[0] = "action_known"
    action_id = request.get("action_id", "")
    if action_id not in action_map:
        return deny("unknown_protected_action", f"action '{action_id}' not in fixture")
    action = action_map[action_id]
    required_scope = action.get("required_scope", "")
    pass_check("action_known", f"action '{action_id}' found in fixture")

    # --- Check 4: grant_exists ---
    _check_id_holder[0] = "grant_exists"
    claimed_grant_id = request["claimed_authority"]["grant_id"]
    if claimed_grant_id not in grant_map:
        return deny("unknown_authority_grant", f"grant '{claimed_grant_id}' not in fixture")
    grant = grant_map[claimed_grant_id]
    pass_check("grant_exists", f"grant '{claimed_grant_id}' found in fixture")

    # --- Check 5: grant_subject_match ---
    _check_id_holder[0] = "grant_subject_match"
    grant_subject = grant.get("subject_principal_id", "")
    if grant_subject != requesting_principal:
        return deny("authority_subject_mismatch", f"grant subject '{grant_subject}' != requesting principal '{requesting_principal}'")
    pass_check("grant_subject_match", f"grant subject matches requesting principal")

    # --- Check 6: delegation_chain_valid ---
    _check_id_holder[0] = "delegation_chain_valid"
    chain, chain_error = build_delegation_chain(claimed_grant_id, grant_map)
    if chain_error:
        return deny(chain_error, f"delegation chain invalid for grant '{claimed_grant_id}'", claimed_grant_id, chain)
    pass_check("delegation_chain_valid", f"delegation chain valid: {' -> '.join(chain)}")

    # --- Check 7: grant_not_revoked ---
    _check_id_holder[0] = "grant_not_revoked"
    for chain_grant_id in chain:
        for rev in revocations:
            if not isinstance(rev, dict):
                continue
            if rev.get("target_id") == chain_grant_id:
                revoked_at = parse_iso8601(rev.get("revoked_at", ""))
                if revoked_at and revoked_at <= decision_time:
                    checks.append({"check_id": "grant_not_revoked", "status": "fail", "detail": f"grant '{chain_grant_id}' revoked at {rev.get('revoked_at')}"})
                    return make_report("deny", "authority_revoked", claimed_grant_id, chain)
    pass_check("grant_not_revoked", "no applicable revocations at decision time")

    # --- Check 8: grant_not_expired ---
    _check_id_holder[0] = "grant_not_expired"
    for chain_grant_id in chain:
        g = grant_map[chain_grant_id]
        issued_at_str = g.get("issued_at")
        expires_at_str = g.get("expires_at")
        if issued_at_str:
            issued_at = parse_iso8601(issued_at_str)
            if issued_at and decision_time < issued_at:
                checks.append({"check_id": "grant_not_expired", "status": "fail", "detail": f"grant '{chain_grant_id}' not yet valid (issued_at: {issued_at_str})"})
                return make_report("deny", "authority_expired", claimed_grant_id, chain)
        if expires_at_str:
            expires_at = parse_iso8601(expires_at_str)
            if expires_at and decision_time >= expires_at:
                checks.append({"check_id": "grant_not_expired", "status": "fail", "detail": f"grant '{chain_grant_id}' expired (expires_at: {expires_at_str})"})
                return make_report("deny", "authority_expired", claimed_grant_id, chain)
    pass_check("grant_not_expired", "all grants in chain within validity period")

    # --- Check 9: scope_authorized ---
    _check_id_holder[0] = "scope_authorized"
    grant_scopes = set(grant.get("scopes", []))
    if required_scope not in grant_scopes:
        return deny("scope_not_authorized", f"scope '{required_scope}' not in grant scopes {sorted(grant_scopes)}")
    pass_check("scope_authorized", f"scope '{required_scope}' authorized by grant")

    # --- Check 10: constraints_satisfied ---
    _check_id_holder[0] = "constraints_satisfied"
    grant_constraints = grant.get("constraints", {})
    parameters = request.get("parameters", {})

    if isinstance(grant_constraints, dict):
        for constraint_key, constraint_val in grant_constraints.items():
            param_key = CONSTRAINT_PARAM_MAP.get(constraint_key)
            if not param_key:
                continue

            if param_key not in parameters:
                checks.append({"check_id": "constraints_satisfied", "status": "fail", "detail": f"required parameter '{param_key}' missing for constraint '{constraint_key}'"})
                return make_report("deny", "constraint_value_missing", claimed_grant_id, chain)

            param_val = parameters[param_key]

            if constraint_key == "max_amount_usd":
                try:
                    if float(param_val) > float(constraint_val):
                        checks.append({"check_id": "constraints_satisfied", "status": "fail", "detail": f"amount_usd {param_val} exceeds max {constraint_val}"})
                        return make_report("deny", "constraint_not_satisfied", claimed_grant_id, chain)
                except (TypeError, ValueError):
                    checks.append({"check_id": "constraints_satisfied", "status": "fail", "detail": f"cannot compare amount_usd values"})
                    return make_report("deny", "constraint_not_satisfied", claimed_grant_id, chain)
            elif constraint_key in LIST_CONSTRAINTS:
                if not isinstance(constraint_val, list):
                    continue
                if param_val not in constraint_val:
                    checks.append({"check_id": "constraints_satisfied", "status": "fail", "detail": f"'{param_key}' value '{param_val}' not in allowed list {constraint_val}"})
                    return make_report("deny", "constraint_not_satisfied", claimed_grant_id, chain)

    pass_check("constraints_satisfied", "all constraints satisfied")

    # --- All checks passed ---
    return make_report("allow", "authority_requirements_satisfied", claimed_grant_id, chain)


LIST_CONSTRAINTS = {"allowed_vendor_ids", "allowed_dataset_ids", "allowed_environments", "allowed_change_types"}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Evaluate a protected action request against a multi-principal authority fixture"
    )
    parser.add_argument("--fixture", required=True, help="Path to authority fixture YAML")
    parser.add_argument("--request", required=True, help="Path to request JSON")
    parser.add_argument("--decision-time", required=True, help="Decision time (ISO-8601)")
    parser.add_argument("--output", required=True, help="Path to write decision report JSON")
    args = parser.parse_args()

    # Load fixture
    fixture_path = Path(args.fixture)
    if not fixture_path.exists():
        print(f"ERROR: fixture not found: {fixture_path}", file=sys.stderr)
        return 2

    try:
        fixture = yaml.safe_load(fixture_path.read_text())
    except Exception as e:
        print(f"ERROR: failed to parse fixture YAML: {e}", file=sys.stderr)
        return 2

    if not isinstance(fixture, dict):
        print("ERROR: fixture root must be a YAML mapping", file=sys.stderr)
        return 2

    # Load request
    request_path = Path(args.request)
    if not request_path.exists():
        print(f"ERROR: request not found: {request_path}", file=sys.stderr)
        return 2

    try:
        request = json.loads(request_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: failed to parse request JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(request, dict):
        print("ERROR: request root must be a JSON object", file=sys.stderr)
        return 1

    # Parse decision time
    decision_time = parse_iso8601(args.decision_time)
    if decision_time is None:
        print(f"ERROR: cannot parse decision-time: {args.decision_time}", file=sys.stderr)
        return 2

    # Ensure timezone-aware
    if decision_time.tzinfo is None:
        decision_time = decision_time.replace(tzinfo=timezone.utc)

    # Evaluate
    report = evaluate_request(fixture, request, decision_time)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, default=str) + "\n")

    status = report["decision"]["status"]
    reason = report["decision"]["reason"]
    print(f"{'ALLOW' if status == 'allow' else 'DENY'}: {reason} (request: {report['request_id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
