#!/usr/bin/env python3
"""Validate Silver Multi-Principal Authority Fixture v0.1.0.

Checks structural validity of a multi-principal authority fixture YAML file.

Usage:
  python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
    --fixture <fixture.yaml>
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REQUIRED_TOP_LEVEL = [
    "fixture_type",
    "fixture_version",
    "fixture_id",
    "description",
    "principals",
    "protected_actions",
    "authority_grants",
    "revocations",
    "limitations",
]

CANONICAL_PRINCIPALS = ["buyerorg.agent", "vendororg.agent", "verifier.auditor"]
CANONICAL_ACTIONS = ["payment.release", "vendor.approve", "data.export", "deploy.change"]

NUMERIC_CONSTRAINTS = {"max_amount_usd"}
LIST_CONSTRAINTS = {"allowed_vendor_ids", "allowed_dataset_ids", "allowed_environments", "allowed_change_types"}


def validate_fixture(fixture: dict[str, Any]) -> list[tuple[str, str]]:
    """Validate fixture structure. Returns list of (reason_code, detail) errors."""
    errors: list[tuple[str, str]] = []

    # 1. Top-level structure
    for field in REQUIRED_TOP_LEVEL:
        if field not in fixture:
            errors.append(("invalid_fixture_structure", f"missing required field: {field}"))

    if errors:
        return errors

    if fixture.get("fixture_type") != "proofrail.silver.multi_principal_authority_fixture":
        errors.append(("invalid_fixture_structure", f"fixture_type must be 'proofrail.silver.multi_principal_authority_fixture', got '{fixture.get('fixture_type')}'"))
        return errors

    if fixture.get("fixture_version") != "v0.1.0":
        errors.append(("invalid_fixture_structure", f"fixture_version must be 'v0.1.0', got '{fixture.get('fixture_version')}'"))
        return errors

    principals = fixture.get("principals", [])
    protected_actions = fixture.get("protected_actions", [])
    authority_grants = fixture.get("authority_grants", [])
    revocations = fixture.get("revocations", [])
    limitations = fixture.get("limitations", [])

    if not isinstance(principals, list) or len(principals) == 0:
        errors.append(("invalid_fixture_structure", "principals must be a non-empty list"))
        return errors

    if not isinstance(protected_actions, list) or len(protected_actions) == 0:
        errors.append(("invalid_fixture_structure", "protected_actions must be a non-empty list"))
        return errors

    if not isinstance(authority_grants, list):
        errors.append(("invalid_fixture_structure", "authority_grants must be a list"))
        return errors

    if not isinstance(revocations, list):
        errors.append(("invalid_fixture_structure", "revocations must be a list"))
        return errors

    # 2. Canonical principals
    principal_ids = {p.get("principal_id") for p in principals if isinstance(p, dict)}
    for cp in CANONICAL_PRINCIPALS:
        if cp not in principal_ids:
            errors.append(("missing_canonical_principal", f"required canonical principal absent: {cp}"))

    # 3. Canonical protected actions
    action_ids = {a.get("action_id") for a in protected_actions if isinstance(a, dict)}
    action_scopes = {a.get("required_scope") for a in protected_actions if isinstance(a, dict)}
    for ca in CANONICAL_ACTIONS:
        if ca not in action_ids:
            errors.append(("missing_protected_action", f"required canonical action absent: {ca}"))

    # 4. Grant ID uniqueness
    grant_ids: set[str] = set()
    grant_map: dict[str, dict[str, Any]] = {}
    for grant in authority_grants:
        if not isinstance(grant, dict):
            continue
        gid = grant.get("grant_id", "")
        if gid in grant_ids:
            errors.append(("duplicate_grant_id", f"non-unique grant_id: {gid}"))
        grant_ids.add(gid)
        grant_map[gid] = grant

    # 5. Principal references in grants
    for grant in authority_grants:
        if not isinstance(grant, dict):
            continue
        gid = grant.get("grant_id", "<unknown>")
        issuer = grant.get("issuer_principal_id")
        subject = grant.get("subject_principal_id")
        if issuer and issuer not in principal_ids:
            errors.append(("unknown_principal_reference", f"grant '{gid}': issuer_principal_id '{issuer}' not in principals"))
        if subject and subject not in principal_ids:
            errors.append(("unknown_principal_reference", f"grant '{gid}': subject_principal_id '{subject}' not in principals"))

    # 6. Scope references in grants
    for grant in authority_grants:
        if not isinstance(grant, dict):
            continue
        gid = grant.get("grant_id", "<unknown>")
        scopes = grant.get("scopes", [])
        if isinstance(scopes, list):
            for scope in scopes:
                if scope not in action_scopes:
                    errors.append(("unknown_scope_reference", f"grant '{gid}': scope '{scope}' not in protected_actions"))

    # 7. Delegated grant validation
    for grant in authority_grants:
        if not isinstance(grant, dict):
            continue
        if grant.get("grant_type") != "delegated":
            continue
        gid = grant.get("grant_id", "<unknown>")
        parent_id = grant.get("parent_grant_id")

        # Parent exists?
        if parent_id not in grant_map:
            errors.append(("unknown_parent_grant", f"grant '{gid}': parent_grant_id '{parent_id}' not found"))
            continue

        parent = grant_map[parent_id]

        # Parent permits delegation?
        parent_delegation = parent.get("delegation", {})
        if not isinstance(parent_delegation, dict) or parent_delegation.get("permitted") is not True:
            errors.append(("delegation_not_permitted", f"grant '{gid}': parent '{parent_id}' has delegation.permitted != true"))

        # Scope subset check
        parent_scopes = set(parent.get("scopes", []))
        child_scopes = set(grant.get("scopes", []))
        if not child_scopes.issubset(parent_scopes):
            expanded = child_scopes - parent_scopes
            errors.append(("delegation_scope_expanded", f"grant '{gid}': scopes {sorted(expanded)} not in parent scopes {sorted(parent_scopes)}"))

        # Constraint weakening check
        parent_constraints = parent.get("constraints", {})
        child_constraints = grant.get("constraints", {})
        if isinstance(parent_constraints, dict) and isinstance(child_constraints, dict):
            for key, parent_val in parent_constraints.items():
                if key not in child_constraints:
                    # Child omits parent constraint = weakening
                    errors.append(("delegation_constraints_weakened", f"grant '{gid}': omits parent constraint '{key}' (weakening)"))
                else:
                    child_val = child_constraints[key]
                    if key in NUMERIC_CONSTRAINTS:
                        try:
                            if float(child_val) > float(parent_val):
                                errors.append(("delegation_constraints_weakened", f"grant '{gid}': constraint '{key}' value {child_val} exceeds parent {parent_val}"))
                        except (TypeError, ValueError):
                            pass
                    elif key in LIST_CONSTRAINTS:
                        if isinstance(parent_val, list) and isinstance(child_val, list):
                            if not set(child_val).issubset(set(parent_val)):
                                errors.append(("delegation_constraints_weakened", f"grant '{gid}': constraint '{key}' values {child_val} not subset of parent {parent_val}"))

    # 8. Revocation target references
    for rev in revocations:
        if not isinstance(rev, dict):
            continue
        target_id = rev.get("target_id")
        if target_id and target_id not in grant_ids:
            errors.append(("unknown_revocation_target", f"revocation targets non-existent grant: {target_id}"))

    # 9. Limitations present
    if not isinstance(limitations, list) or len(limitations) == 0:
        errors.append(("limitations_missing", "limitations must be a non-empty list"))

    return errors


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate Silver Multi-Principal Authority Fixture v0.1.0"
    )
    parser.add_argument("--fixture", required=True, help="Path to authority fixture YAML")
    args = parser.parse_args()

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

    errors = validate_fixture(fixture)

    if errors:
        print(f"FAIL: fixture validation failed with {len(errors)} error(s):")
        for reason, detail in errors:
            print(f"  [{reason}] {detail}")
        return 1

    print(f"PASS: fixture valid — {fixture.get('fixture_id', '<unknown>')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
