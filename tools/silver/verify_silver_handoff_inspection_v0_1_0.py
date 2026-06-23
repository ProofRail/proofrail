#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.1 handoff inspection package.

Hash-first, fail-fast. The verifier:

  1.  Parses the inspection package manifest.
  2.  Validates manifest shape (document_type, schema_version,
      proofrail_release, hash_algorithm, inspection_id, generated_at,
      subject count (exactly three), subject ordering, role set,
      scope_limitations presence/type, non_claims presence/type).
  3.  Rejects any subject path containing '..' or that is absolute.
  4.  Checks subject path equality against the deterministic
      SUBJECT_ORDER.
  5.  Checks each subject file exists.
  6.  Recomputes SHA-256 for each subject and compares to the recorded
      sha256.
  7.  Subprocess-invokes the unchanged v0.3.0 handoff verifier on
      subject[0] (the nested v0.3.0 handoff manifest under
      silver-acceptance-handoff/). Failure surfaces as the stable
      v0.3.1 reason `nested_handoff_invalid`.
  8.  Validates the requirement set bound at subject[1] (structural /
      closed-status / required-domain / duplicate / overclaim).
  9.  Parses and structurally validates the inspection report at
      subject[2].
  10. Cross-checks base_handoff.handoff_manifest_sha256 against
      subject[0] sha256 (inspection_report_binding_mismatch).
  11. Cross-checks handoff_summary non-posture fields
      (acceptance_record_id, decision_status, purpose_id) against the
      nested v0.3.0 handoff summary (inspection_handoff_summary_mismatch).
      Per Amendment 1, posture and reuse_warning are NOT checked here.
  12. Independently checks the posture path
      (inspection_review_posture_downgrade): the report's
      recommended_handoff_posture rank must be >= the nested v0.3.0
      summary's rank; and reuse_warning must be a non-empty string when
      the nested rank is >= 1.
  13. Cross-checks component_inspection (exactly four rows, fixed
      component_id / component_type / source_release, status forced to
      "present_and_verified").
  14. Validates gold_gap_inventory: requirements_sha256 equals
      subject[1] sha256, requirement_count equals len(requirements),
      counts recomputed from rows match recorded counts, every
      requirement-set row has a matching report row with identical
      gap_status, gold_boundary_status forced to gold_not_claimed when
      any partial/unmet/out_of_scope row exists.
  15. Recursively scans every string in the report OUTSIDE
      scope_limitations and non_claims for forbidden positive tokens
      (inspection_gold_overclaim).
  16. Re-checks scope_limitations and non_claims for emptiness / blank
      entries (inspection_limitations_missing /
      inspection_non_claims_missing); per Amendment 2 these are
      reachable AFTER the early presence/type checks.

Stable failure reasons (20):

  invalid_inspection_manifest
  inspection_subject_path_traversal
  inspection_subject_file_missing
  inspection_subject_hash_mismatch
  inspection_limitations_missing
  inspection_non_claims_missing
  requirement_set_invalid
  requirement_duplicate
  requirement_domain_missing
  inspection_report_invalid
  inspection_report_binding_mismatch
  inspection_handoff_summary_mismatch
  inspection_review_posture_downgrade
  inspection_component_status_mismatch
  inspection_requirement_missing
  inspection_requirement_status_mismatch
  inspection_count_mismatch
  inspection_gold_status_invalid
  inspection_gold_overclaim
  nested_handoff_invalid

Note: handoff_validation_failed, requirement_set_validation_failed,
and inspection_self_validation_failed are runner-only codes (emitted
by inspect_silver_acceptance_handoff_v0_1_0.py) and are never emitted
by this verifier.

Usage:
  # Full inspection-package verification:
  python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-handoff-inspection-v0.3.1/silver-handoff-inspection-manifest.json

  # Requirement-set-only validation (entry point used by the runner):
  python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \\
    --validate-requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json

Exit codes:
  0 - inspection package valid (or requirement set valid)
  1 - verification failure (any stable failure reason above)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_silver_acceptance_handoff_v0_1_0.py"
)

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.handoff_inspection_manifest"
REPORT_DOCUMENT_TYPE = "proofrail.silver.handoff_inspection_report"
REQUIREMENT_SET_DOCUMENT_TYPE = "proofrail.silver_to_gold.requirement_set"
SUMMARY_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_summary"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.1"

# Fixed manifest subject layout (path, role).
SUBJECT_ORDER = [
    (
        "silver-acceptance-handoff/"
        "silver-acceptance-handoff-manifest.json",
        "silver_acceptance_handoff_manifest",
    ),
    (
        "gold-boundary-requirements.json",
        "gold_boundary_requirement_set",
    ),
    (
        "silver-handoff-inspection-report.json",
        "silver_handoff_inspection_report",
    ),
]

# Fixed component_inspection layout, matching the runner.
COMPONENT_INSPECTION_SPEC = [
    {
        "component_id": "v0.2.7-composed-gateway-evidence",
        "component_type": "composed_gateway_evidence",
        "source_release": "v0.2.7",
    },
    {
        "component_id": "v0.2.8-relying-party-acceptance",
        "component_type": "relying_party_acceptance",
        "source_release": "v0.2.8",
    },
    {
        "component_id": "v0.2.9-revocation-challenge-drill",
        "component_type": "revocation_challenge_drill",
        "source_release": "v0.2.9",
    },
    {
        "component_id": "v0.3.0-silver-acceptance-handoff",
        "component_type": "silver_acceptance_handoff",
        "source_release": "v0.3.0",
    },
]
COMPONENT_INSPECTION_VALID_STATUSES = {
    "present_and_verified",
    "present_with_warning",
    "not_inspected",
}

REQUIRED_DOMAINS = [
    "governed_acceptance_policy",
    "named_acceptance_authority",
    "independent_verifier_identity",
    "evidence_retention_policy",
    "change_control_policy",
    "revocation_operations",
    "challenge_dispute_process",
    "audit_trail_and_review",
    "runtime_operating_boundary",
    "external_accountability",
    "public_or_shared_acceptance_record",
    "legal_or_contractual_basis",
    "production_use_authorization",
]
REQUIRED_DOMAIN_COUNT = len(REQUIRED_DOMAINS)  # 13

GAP_STATUS_PRESENT = "silver_evidence_present"
GAP_STATUS_PARTIAL = "silver_evidence_partial"
GAP_STATUS_UNMET = "gold_prerequisite_unmet"
GAP_STATUS_OUT_OF_SCOPE = "out_of_scope_for_silver"
GAP_STATUS_SET = {
    GAP_STATUS_PRESENT,
    GAP_STATUS_PARTIAL,
    GAP_STATUS_UNMET,
    GAP_STATUS_OUT_OF_SCOPE,
}

GOLD_BOUNDARY_STATUS_SET = {
    "gold_not_claimed",
    "gold_gap_inventory_only",
}

# Closed handoff posture set (rank 0 = lightest), matching v0.3.0.
HANDOFF_POSTURES = (
    "silver_handoff_complete_for_demo_scope",
    "silver_handoff_complete_review_required_before_reuse",
    "silver_handoff_not_reusable_without_governed_review",
)
HANDOFF_POSTURE_RANK = {p: i for i, p in enumerate(HANDOFF_POSTURES)}

# Forbidden positive tokens for the overclaim guard. Includes the
# v0.3.0 set plus the v0.3.1 gold-ready variants.
FORBIDDEN_POSITIVE_TOKENS = [
    "certified",
    "approved",
    "audited",
    "legally accepted",
    "legally revoked",
    "challenge resolved",
    "gold accepted",
    "gold certified",
    "compliant",
    "production-approved",
    "production-ready",
    "regulator-ready",
    "regulator approval",
    "trust transferred",
    "trust transfer",
    "gold-ready",
    "gold ready",
    "gold_ready",
]

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_label(path: Path) -> str:
    return "sha256:" + sha256_hex(path)


def parse_iso_8601_z(value: Any) -> datetime | None:
    if not isinstance(value, str) or not ISO_8601_RE.match(value):
        return None
    try:
        return datetime.strptime(
            value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z"
        )
    except ValueError:
        try:
            return datetime.strptime(
                value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            return None


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def has_path_traversal(rel: str) -> bool:
    if not isinstance(rel, str) or rel == "":
        return True
    if rel.startswith("/"):
        return True
    parts = rel.replace("\\", "/").split("/")
    if ".." in parts:
        return True
    return False


def array_of_strings_present(arr: Any) -> bool:
    """Presence/type check only (per Amendment 2). Does NOT check
    for emptiness or blank entries."""
    if not isinstance(arr, list):
        return False
    for entry in arr:
        if not isinstance(entry, str):
            return False
    return True


def array_of_strings_non_empty(arr: list) -> bool:
    """Later check: array non-empty and every entry non-blank."""
    if len(arr) == 0:
        return False
    for entry in arr:
        if not non_empty_str(entry):
            return False
    return True


def collect_strings_outside_arrays(
    node: Any, exclude_keys: set[str], out: list[str], in_excluded: bool = False
) -> None:
    """Recursively gather every string value EXCEPT strings reachable
    through any path that traverses an excluded key (typically
    scope_limitations and non_claims)."""
    if in_excluded:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if k in exclude_keys:
                continue
            collect_strings_outside_arrays(v, exclude_keys, out, False)
    elif isinstance(node, list):
        for item in node:
            collect_strings_outside_arrays(item, exclude_keys, out, False)
    elif isinstance(node, str):
        out.append(node)


def detect_overclaim(node: Any) -> str | None:
    """Returns the first matched forbidden token if present in any
    string outside scope_limitations / non_claims, else None."""
    strings: list[str] = []
    collect_strings_outside_arrays(
        node, {"scope_limitations", "non_claims"}, strings
    )
    for s in strings:
        lower = s.lower()
        for token in FORBIDDEN_POSITIVE_TOKENS:
            if token.lower() in lower:
                return token
    return None


# ---------------------------------------------------------------------------
# Requirement set validator (used by both --validate-requirement-set entry
# point and by manifest-mode verification).
# ---------------------------------------------------------------------------

def validate_requirement_set_object(req_set: Any) -> tuple[str, str] | None:
    """Returns (reason, detail) on failure, None on pass."""
    if not isinstance(req_set, dict):
        return ("requirement_set_invalid", "requirement set is not a JSON object")

    # Early structural checks
    expected_fields = {
        "document_type": REQUIREMENT_SET_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
    }
    for k, expected in expected_fields.items():
        v = req_set.get(k)
        if v != expected:
            return (
                "requirement_set_invalid",
                f"{k} must be {expected!r}, got {v!r}",
            )

    for k in (
        "requirement_set_id",
        "requirement_set_version",
        "scope",
    ):
        if not non_empty_str(req_set.get(k)):
            return (
                "requirement_set_invalid",
                f"{k} must be a non-empty string",
            )

    requirements = req_set.get("requirements")
    if not isinstance(requirements, list):
        return (
            "requirement_set_invalid",
            "requirements must be an array",
        )
    if len(requirements) != REQUIRED_DOMAIN_COUNT:
        return (
            "requirement_set_invalid",
            f"requirements must contain exactly {REQUIRED_DOMAIN_COUNT} "
            f"entries, got {len(requirements)}",
        )

    # Per Amendment 2: presence/type check only here.
    scope_limitations = req_set.get("scope_limitations")
    non_claims = req_set.get("non_claims")
    if not array_of_strings_present(scope_limitations):
        return (
            "requirement_set_invalid",
            "scope_limitations must be an array of strings",
        )
    if not array_of_strings_present(non_claims):
        return (
            "requirement_set_invalid",
            "non_claims must be an array of strings",
        )

    # Per-requirement structural checks (do not yet check duplicates /
    # missing domains; reserve those for the dedicated reasons).
    seen_ids: dict[str, int] = {}
    seen_domains: dict[str, int] = {}
    found_unmet_row = False
    for idx, req in enumerate(requirements):
        if not isinstance(req, dict):
            return (
                "requirement_set_invalid",
                f"requirements[{idx}] is not an object",
            )
        for field in ("requirement_id", "domain", "title", "gold_prerequisite", "reason"):
            if not non_empty_str(req.get(field)):
                return (
                    "requirement_set_invalid",
                    f"requirements[{idx}].{field} must be a non-empty string",
                )
        evidence_mapping = req.get("silver_evidence_mapping")
        if not isinstance(evidence_mapping, list):
            return (
                "requirement_set_invalid",
                f"requirements[{idx}].silver_evidence_mapping must be an array",
            )
        for j, ref in enumerate(evidence_mapping):
            if not non_empty_str(ref):
                return (
                    "requirement_set_invalid",
                    f"requirements[{idx}].silver_evidence_mapping[{j}] must "
                    f"be a non-empty string",
                )
        status = req.get("expected_gap_status")
        if status not in GAP_STATUS_SET:
            return (
                "requirement_set_invalid",
                f"requirements[{idx}].expected_gap_status {status!r} is "
                f"not in the closed set",
            )
        if status == GAP_STATUS_UNMET:
            found_unmet_row = True

        # Track duplicate ids / domains.
        r_id = req["requirement_id"]
        r_domain = req["domain"]
        if r_id in seen_ids:
            return (
                "requirement_duplicate",
                f"duplicate requirement_id {r_id!r} (first at index "
                f"{seen_ids[r_id]}, again at index {idx})",
            )
        seen_ids[r_id] = idx
        if r_domain in seen_domains:
            return (
                "requirement_duplicate",
                f"duplicate domain {r_domain!r} (first at index "
                f"{seen_domains[r_domain]}, again at index {idx})",
            )
        seen_domains[r_domain] = idx

    # Required domain coverage check (Amendment 3: dedicated reason).
    required_set = set(REQUIRED_DOMAINS)
    present_set = set(seen_domains.keys())
    missing = required_set - present_set
    if missing:
        return (
            "requirement_domain_missing",
            "required domain(s) missing from requirement set: "
            + ", ".join(sorted(missing)),
        )
    extra = present_set - required_set
    if extra:
        return (
            "requirement_set_invalid",
            "requirement set contains unknown domain(s): "
            + ", ".join(sorted(extra)),
        )

    if not found_unmet_row:
        return (
            "requirement_set_invalid",
            "requirement set MUST contain at least one row with "
            "expected_gap_status == gold_prerequisite_unmet",
        )

    # Overclaim guard on the requirement set, OUTSIDE scope_limitations /
    # non_claims (per requirement set schema).
    over = detect_overclaim(req_set)
    if over is not None:
        return (
            "inspection_gold_overclaim",
            f"requirement set contains forbidden positive token "
            f"{over!r} outside scope_limitations / non_claims",
        )

    # Per Amendment 2: emptiness / blank entries surface AFTER the
    # early structural / overclaim checks.
    if not array_of_strings_non_empty(scope_limitations):
        return (
            "inspection_limitations_missing",
            "requirement set scope_limitations is empty or contains "
            "blank/whitespace-only entries",
        )
    if not array_of_strings_non_empty(non_claims):
        return (
            "inspection_non_claims_missing",
            "requirement set non_claims is empty or contains "
            "blank/whitespace-only entries",
        )

    return None


# ---------------------------------------------------------------------------
# Manifest + report verification.
# ---------------------------------------------------------------------------

def validate_manifest_structure(manifest: Any) -> tuple[str, str] | None:
    if not isinstance(manifest, dict):
        return ("invalid_inspection_manifest", "manifest is not a JSON object")
    expected_fields = {
        "document_type": MANIFEST_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "hash_algorithm": "sha256",
    }
    for k, expected in expected_fields.items():
        v = manifest.get(k)
        if v != expected:
            return (
                "invalid_inspection_manifest",
                f"{k} must be {expected!r}, got {v!r}",
            )
    if not non_empty_str(manifest.get("inspection_id")):
        return (
            "invalid_inspection_manifest",
            "inspection_id must be a non-empty string",
        )
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return (
            "invalid_inspection_manifest",
            "generated_at must be ISO-8601 UTC Z-suffixed",
        )
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return (
            "invalid_inspection_manifest",
            "subjects must be an array",
        )
    if len(subjects) != len(SUBJECT_ORDER):
        return (
            "invalid_inspection_manifest",
            f"subjects must contain exactly {len(SUBJECT_ORDER)} "
            f"entries, got {len(subjects)}",
        )
    for i, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return (
                "invalid_inspection_manifest",
                f"subjects[{i}] is not an object",
            )
        # Path traversal is checked BEFORE exact SUBJECT_ORDER equality
        # so that the dedicated stable failure reason
        # `inspection_subject_path_traversal` is directly reachable when
        # the manifest subject path is a string but absolute or contains
        # '..'. Non-string paths fall through to the path-equality check
        # below and surface as `invalid_inspection_manifest`.
        path_val = subj.get("path")
        if isinstance(path_val, str) and has_path_traversal(path_val):
            return (
                "inspection_subject_path_traversal",
                f"subjects[{i}].path {path_val!r} is absolute or "
                f"contains '..'",
            )
        expected_path, expected_role = SUBJECT_ORDER[i]
        if path_val != expected_path:
            return (
                "invalid_inspection_manifest",
                f"subjects[{i}].path must be {expected_path!r}, got "
                f"{path_val!r}",
            )
        if subj.get("role") != expected_role:
            return (
                "invalid_inspection_manifest",
                f"subjects[{i}].role must be {expected_role!r}, got "
                f"{subj.get('role')!r}",
            )
        if not (isinstance(subj.get("sha256"), str)
                and subj["sha256"].startswith("sha256:")
                and len(subj["sha256"]) == 7 + 64):
            return (
                "invalid_inspection_manifest",
                f"subjects[{i}].sha256 must be 'sha256:<64-hex>'",
            )
        size_bytes = subj.get("size_bytes")
        if not (isinstance(size_bytes, int) and not isinstance(size_bytes, bool)
                and size_bytes >= 0):
            return (
                "invalid_inspection_manifest",
                f"subjects[{i}].size_bytes must be a non-negative integer",
            )
    if not array_of_strings_present(manifest.get("scope_limitations")):
        return (
            "invalid_inspection_manifest",
            "scope_limitations must be an array of strings",
        )
    if not array_of_strings_present(manifest.get("non_claims")):
        return (
            "invalid_inspection_manifest",
            "non_claims must be an array of strings",
        )
    return None


def validate_report_structure(report: Any) -> tuple[str, str] | None:
    if not isinstance(report, dict):
        return ("inspection_report_invalid", "report is not a JSON object")
    expected_fields = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
    }
    for k, expected in expected_fields.items():
        v = report.get(k)
        if v != expected:
            return (
                "inspection_report_invalid",
                f"{k} must be {expected!r}, got {v!r}",
            )
    if not non_empty_str(report.get("inspection_id")):
        return (
            "inspection_report_invalid",
            "inspection_id must be a non-empty string",
        )
    if parse_iso_8601_z(report.get("generated_at")) is None:
        return (
            "inspection_report_invalid",
            "generated_at must be ISO-8601 UTC Z-suffixed",
        )
    base = report.get("base_handoff")
    if not isinstance(base, dict):
        return (
            "inspection_report_invalid",
            "base_handoff must be an object",
        )
    for field in (
        "handoff_id",
        "handoff_manifest_path",
        "handoff_manifest_sha256",
        "handoff_verification_status",
    ):
        if not non_empty_str(base.get(field)):
            return (
                "inspection_report_invalid",
                f"base_handoff.{field} must be a non-empty string",
            )
    if base.get("handoff_verification_status") != "pass":
        return (
            "inspection_report_invalid",
            "base_handoff.handoff_verification_status must be 'pass'",
        )
    if base.get("handoff_manifest_path") != (
        "silver-acceptance-handoff/silver-acceptance-handoff-manifest.json"
    ):
        return (
            "inspection_report_invalid",
            "base_handoff.handoff_manifest_path must equal the fixed "
            "subject[0] path",
        )

    summary = report.get("handoff_summary")
    if not isinstance(summary, dict):
        return (
            "inspection_report_invalid",
            "handoff_summary must be an object",
        )
    for field in (
        "acceptance_record_id",
        "decision_status",
        "purpose_id",
        "recommended_handoff_posture",
    ):
        if not non_empty_str(summary.get(field)):
            return (
                "inspection_report_invalid",
                f"handoff_summary.{field} must be a non-empty string",
            )
    if not isinstance(summary.get("reuse_warning"), str):
        return (
            "inspection_report_invalid",
            "handoff_summary.reuse_warning must be a string",
        )

    components = report.get("component_inspection")
    if not isinstance(components, list):
        return (
            "inspection_report_invalid",
            "component_inspection must be an array",
        )

    inv = report.get("gold_gap_inventory")
    if not isinstance(inv, dict):
        return (
            "inspection_report_invalid",
            "gold_gap_inventory must be an object",
        )
    for field in (
        "requirement_set_id",
        "requirement_set_version",
        "requirements_path",
        "requirements_sha256",
        "gold_boundary_status",
    ):
        if not non_empty_str(inv.get(field)):
            return (
                "inspection_report_invalid",
                f"gold_gap_inventory.{field} must be a non-empty string",
            )
    if inv.get("requirements_path") != "gold-boundary-requirements.json":
        return (
            "inspection_report_invalid",
            "gold_gap_inventory.requirements_path must equal "
            "'gold-boundary-requirements.json'",
        )
    if not isinstance(inv.get("requirement_count"), int) or isinstance(
        inv.get("requirement_count"), bool
    ):
        return (
            "inspection_report_invalid",
            "gold_gap_inventory.requirement_count must be an integer",
        )
    if not isinstance(inv.get("gold_prerequisites_unmet"), bool):
        return (
            "inspection_report_invalid",
            "gold_gap_inventory.gold_prerequisites_unmet must be a boolean",
        )
    if not isinstance(inv.get("counts"), dict):
        return (
            "inspection_report_invalid",
            "gold_gap_inventory.counts must be an object",
        )
    if not isinstance(inv.get("requirements"), list):
        return (
            "inspection_report_invalid",
            "gold_gap_inventory.requirements must be an array",
        )

    if not array_of_strings_present(report.get("scope_limitations")):
        return (
            "inspection_report_invalid",
            "scope_limitations must be an array of strings",
        )
    if not array_of_strings_present(report.get("non_claims")):
        return (
            "inspection_report_invalid",
            "non_claims must be an array of strings",
        )
    return None


def verify_manifest_mode(manifest_path: Path) -> int:
    # --- Step 1: parse manifest ---
    if not manifest_path.exists() or not manifest_path.is_file():
        return usage_error(f"--manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_inspection_manifest", f"not valid JSON: {e}")

    # --- Step 2: manifest structural validation (presence/type only) ---
    err = validate_manifest_structure(manifest)
    if err is not None:
        return fail(*err)

    package_root = manifest_path.parent.resolve()
    subjects = manifest["subjects"]

    # --- Step 3: path traversal ---
    for i, subj in enumerate(subjects):
        rel = subj["path"]
        if has_path_traversal(rel):
            return fail(
                "inspection_subject_path_traversal",
                f"subjects[{i}].path {rel!r} is absolute or contains '..'",
            )

    # --- Step 4-5: subject files exist ---
    subject_paths: list[Path] = []
    for i, subj in enumerate(subjects):
        sp = package_root / subj["path"]
        if not sp.exists() or not sp.is_file():
            return fail(
                "inspection_subject_file_missing",
                f"subjects[{i}].path {subj['path']!r} not found under "
                f"package root",
            )
        subject_paths.append(sp)

    # --- Step 6: subject sha256 recomputation ---
    recomputed_sha: list[str] = []
    for i, sp in enumerate(subject_paths):
        actual = sha256_label(sp)
        if actual != subjects[i]["sha256"]:
            return fail(
                "inspection_subject_hash_mismatch",
                f"subjects[{i}] recomputed sha256 {actual} does not "
                f"match recorded {subjects[i]['sha256']}",
            )
        recomputed_sha.append(actual)

    # --- Step 7: subprocess-invoke unchanged v0.3.0 handoff verifier ---
    proc = subprocess.run(
        [
            sys.executable,
            str(HANDOFF_VERIFIER),
            "--manifest",
            str(subject_paths[0]),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stdout + proc.stderr).strip().replace("\n", " ; ")
        if not detail:
            detail = f"subprocess exited {proc.returncode}"
        return fail("nested_handoff_invalid", detail)

    # --- Step 8: parse + validate the requirement set bound at subject[1] ---
    req_set_path = subject_paths[1]
    try:
        req_set = json.loads(req_set_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "requirement_set_invalid",
            f"requirement set at subjects[1] not valid JSON: {e}",
        )
    err = validate_requirement_set_object(req_set)
    if err is not None:
        return fail(*err)

    # --- Step 9: parse + validate inspection report at subject[2] ---
    report_path = subject_paths[2]
    try:
        report = json.loads(report_path.read_text())
    except json.JSONDecodeError as e:
        return fail("inspection_report_invalid", f"not valid JSON: {e}")
    err = validate_report_structure(report)
    if err is not None:
        return fail(*err)

    # --- Step 10: base_handoff.handoff_manifest_sha256 == subject[0] sha256 ---
    base = report["base_handoff"]
    if base["handoff_manifest_sha256"] != recomputed_sha[0]:
        return fail(
            "inspection_report_binding_mismatch",
            f"base_handoff.handoff_manifest_sha256 "
            f"{base['handoff_manifest_sha256']} does not match recomputed "
            f"subject[0] sha256 {recomputed_sha[0]}",
        )

    # --- Read the nested v0.3.0 handoff summary for cross-checks ---
    nested_summary_path = (
        package_root
        / "silver-acceptance-handoff"
        / "silver-acceptance-handoff-summary.json"
    )
    if not nested_summary_path.exists() or not nested_summary_path.is_file():
        return fail(
            "nested_handoff_invalid",
            "nested v0.3.0 handoff summary missing under "
            "silver-acceptance-handoff/",
        )
    try:
        nested_summary = json.loads(nested_summary_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "nested_handoff_invalid",
            f"nested v0.3.0 handoff summary not valid JSON: {e}",
        )
    if not isinstance(nested_summary, dict):
        return fail(
            "nested_handoff_invalid",
            "nested v0.3.0 handoff summary is not a JSON object",
        )
    nested_included = nested_summary.get("included_chain")
    nested_result = nested_summary.get("handoff_result")
    if not (isinstance(nested_included, dict)
            and isinstance(nested_result, dict)):
        return fail(
            "nested_handoff_invalid",
            "nested v0.3.0 handoff summary missing included_chain or "
            "handoff_result object",
        )
    nested_rpa = nested_included.get("relying_party_acceptance")
    if not isinstance(nested_rpa, dict):
        return fail(
            "nested_handoff_invalid",
            "nested v0.3.0 summary included_chain.relying_party_acceptance "
            "missing",
        )

    summary = report["handoff_summary"]

    # --- Step 11: handoff_summary non-posture cross-check (Amendment 1) ---
    for field in ("acceptance_record_id", "decision_status", "purpose_id"):
        expected = nested_rpa.get(field)
        actual = summary.get(field)
        if actual != expected:
            return fail(
                "inspection_handoff_summary_mismatch",
                f"handoff_summary.{field} {actual!r} does not match "
                f"nested v0.3.0 summary value {expected!r}",
            )

    # --- Step 12: posture path (Amendment 1) ---
    nested_posture = nested_result.get("recommended_handoff_posture")
    report_posture = summary.get("recommended_handoff_posture")
    if nested_posture not in HANDOFF_POSTURE_RANK:
        return fail(
            "nested_handoff_invalid",
            f"nested v0.3.0 summary recommended_handoff_posture "
            f"{nested_posture!r} is not in the closed set",
        )
    if report_posture not in HANDOFF_POSTURE_RANK:
        return fail(
            "inspection_review_posture_downgrade",
            f"handoff_summary.recommended_handoff_posture "
            f"{report_posture!r} is not in the closed handoff posture set",
        )
    nested_rank = HANDOFF_POSTURE_RANK[nested_posture]
    report_rank = HANDOFF_POSTURE_RANK[report_posture]
    if report_rank < nested_rank:
        return fail(
            "inspection_review_posture_downgrade",
            f"handoff_summary.recommended_handoff_posture "
            f"{report_posture!r} (rank {report_rank}) is weaker than "
            f"nested v0.3.0 summary posture {nested_posture!r} "
            f"(rank {nested_rank})",
        )
    if nested_rank >= 1 and not non_empty_str(summary.get("reuse_warning")):
        return fail(
            "inspection_review_posture_downgrade",
            f"handoff_summary.reuse_warning must be a non-empty string "
            f"when nested v0.3.0 summary posture rank is {nested_rank}",
        )

    # --- Step 13: component_inspection cross-check ---
    components = report["component_inspection"]
    if len(components) != len(COMPONENT_INSPECTION_SPEC):
        return fail(
            "inspection_component_status_mismatch",
            f"component_inspection must contain exactly "
            f"{len(COMPONENT_INSPECTION_SPEC)} rows, got {len(components)}",
        )
    for i, (row, spec) in enumerate(zip(components, COMPONENT_INSPECTION_SPEC)):
        if not isinstance(row, dict):
            return fail(
                "inspection_component_status_mismatch",
                f"component_inspection[{i}] is not an object",
            )
        for field in ("component_id", "component_type", "source_release"):
            if row.get(field) != spec[field]:
                return fail(
                    "inspection_component_status_mismatch",
                    f"component_inspection[{i}].{field} {row.get(field)!r} "
                    f"does not match expected {spec[field]!r}",
                )
        status = row.get("inspection_status")
        if status not in COMPONENT_INSPECTION_VALID_STATUSES:
            return fail(
                "inspection_component_status_mismatch",
                f"component_inspection[{i}].inspection_status {status!r} "
                f"is not in the closed set",
            )
        if status != "present_and_verified":
            return fail(
                "inspection_component_status_mismatch",
                f"component_inspection[{i}].inspection_status must be "
                f"'present_and_verified', got {status!r}",
            )

    # --- Step 14: gold_gap_inventory cross-check ---
    inv = report["gold_gap_inventory"]
    if inv["requirements_sha256"] != recomputed_sha[1]:
        return fail(
            "inspection_report_binding_mismatch",
            f"gold_gap_inventory.requirements_sha256 "
            f"{inv['requirements_sha256']} does not match recomputed "
            f"subject[1] sha256 {recomputed_sha[1]}",
        )
    if inv.get("requirement_set_id") != req_set["requirement_set_id"]:
        return fail(
            "inspection_report_invalid",
            "gold_gap_inventory.requirement_set_id does not match the "
            "bound requirement set",
        )
    if inv.get("requirement_set_version") != req_set["requirement_set_version"]:
        return fail(
            "inspection_report_invalid",
            "gold_gap_inventory.requirement_set_version does not match the "
            "bound requirement set",
        )
    requirements_rows = inv["requirements"]
    if inv["requirement_count"] != len(requirements_rows):
        return fail(
            "inspection_count_mismatch",
            f"gold_gap_inventory.requirement_count "
            f"({inv['requirement_count']}) does not match len(requirements) "
            f"({len(requirements_rows)})",
        )

    # Index report rows by requirement_id.
    report_rows_by_id: dict[str, dict] = {}
    for j, row in enumerate(requirements_rows):
        if not isinstance(row, dict):
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory.requirements[{j}] is not an object",
            )
        rid = row.get("requirement_id")
        if not non_empty_str(rid):
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory.requirements[{j}].requirement_id must "
                f"be a non-empty string",
            )
        if rid in report_rows_by_id:
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory.requirements has duplicate "
                f"requirement_id {rid!r}",
            )
        report_rows_by_id[rid] = row

    # Every requirement-set row must have a matching report row.
    for src in req_set["requirements"]:
        rid = src["requirement_id"]
        report_row = report_rows_by_id.get(rid)
        if report_row is None:
            return fail(
                "inspection_requirement_missing",
                f"requirement set row {rid!r} has no matching report row",
            )
        if report_row.get("domain") != src["domain"]:
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory row {rid!r}.domain "
                f"{report_row.get('domain')!r} does not match requirement "
                f"set domain {src['domain']!r}",
            )
        if report_row.get("gap_status") != src["expected_gap_status"]:
            return fail(
                "inspection_requirement_status_mismatch",
                f"gold_gap_inventory row {rid!r}.gap_status "
                f"{report_row.get('gap_status')!r} does not match "
                f"requirement set expected_gap_status "
                f"{src['expected_gap_status']!r}",
            )
        if report_row.get("reason") != src["reason"]:
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory row {rid!r}.reason does not match "
                f"requirement set reason",
            )
        ev_refs = report_row.get("evidence_refs")
        if not isinstance(ev_refs, list):
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory row {rid!r}.evidence_refs must be an "
                f"array",
            )
        for k, ref in enumerate(ev_refs):
            if not non_empty_str(ref):
                return fail(
                    "inspection_report_invalid",
                    f"gold_gap_inventory row {rid!r}.evidence_refs[{k}] "
                    f"must be a non-empty string",
                )
        if list(ev_refs) != list(src["silver_evidence_mapping"]):
            return fail(
                "inspection_report_invalid",
                f"gold_gap_inventory row {rid!r}.evidence_refs does not "
                f"match requirement set silver_evidence_mapping",
            )

    # Recompute counts from report rows, compare against recorded counts.
    recomputed_counts = {
        GAP_STATUS_PRESENT: 0,
        GAP_STATUS_PARTIAL: 0,
        GAP_STATUS_UNMET: 0,
        GAP_STATUS_OUT_OF_SCOPE: 0,
    }
    for row in requirements_rows:
        st = row.get("gap_status")
        if st not in GAP_STATUS_SET:
            return fail(
                "inspection_requirement_status_mismatch",
                f"gold_gap_inventory row gap_status {st!r} is not in the "
                f"closed set",
            )
        recomputed_counts[st] += 1
    recorded_counts = inv["counts"]
    for k in recomputed_counts:
        if recorded_counts.get(k) != recomputed_counts[k]:
            return fail(
                "inspection_count_mismatch",
                f"gold_gap_inventory.counts.{k} "
                f"{recorded_counts.get(k)!r} does not match recomputed "
                f"value {recomputed_counts[k]}",
            )
    # Recompute gold_prerequisites_unmet boolean.
    expected_unmet_bool = (
        recomputed_counts[GAP_STATUS_PARTIAL]
        + recomputed_counts[GAP_STATUS_UNMET]
        + recomputed_counts[GAP_STATUS_OUT_OF_SCOPE]
    ) > 0
    if inv["gold_prerequisites_unmet"] != expected_unmet_bool:
        return fail(
            "inspection_count_mismatch",
            f"gold_gap_inventory.gold_prerequisites_unmet "
            f"{inv['gold_prerequisites_unmet']!r} does not match the "
            f"recomputed value {expected_unmet_bool}",
        )

    # gold_boundary_status: closed set + must be gold_not_claimed when
    # any partial/unmet/out_of_scope row exists.
    gbs = inv["gold_boundary_status"]
    if gbs not in GOLD_BOUNDARY_STATUS_SET:
        return fail(
            "inspection_gold_status_invalid",
            f"gold_gap_inventory.gold_boundary_status {gbs!r} is not in "
            f"the closed set {sorted(GOLD_BOUNDARY_STATUS_SET)!r}",
        )
    if expected_unmet_bool and gbs != "gold_not_claimed":
        return fail(
            "inspection_gold_status_invalid",
            f"gold_gap_inventory.gold_boundary_status must be "
            f"'gold_not_claimed' when any row is silver_evidence_partial, "
            f"gold_prerequisite_unmet, or out_of_scope_for_silver; "
            f"got {gbs!r}",
        )

    # --- Step 15: overclaim guard on the report ---
    over = detect_overclaim(report)
    if over is not None:
        return fail(
            "inspection_gold_overclaim",
            f"inspection report contains forbidden positive token "
            f"{over!r} outside scope_limitations / non_claims",
        )

    # --- Step 16: emptiness / blank entries for limitations / non_claims
    # (Amendment 2 ordering: emptiness checked AFTER structural / binding /
    # overclaim) ---
    if not array_of_strings_non_empty(manifest["scope_limitations"]):
        return fail(
            "inspection_limitations_missing",
            "inspection manifest scope_limitations is empty or contains "
            "blank/whitespace-only entries",
        )
    if not array_of_strings_non_empty(manifest["non_claims"]):
        return fail(
            "inspection_non_claims_missing",
            "inspection manifest non_claims is empty or contains "
            "blank/whitespace-only entries",
        )
    if not array_of_strings_non_empty(report["scope_limitations"]):
        return fail(
            "inspection_limitations_missing",
            "inspection report scope_limitations is empty or contains "
            "blank/whitespace-only entries",
        )
    if not array_of_strings_non_empty(report["non_claims"]):
        return fail(
            "inspection_non_claims_missing",
            "inspection report non_claims is empty or contains "
            "blank/whitespace-only entries",
        )

    # --- Done ---
    print(f"PASS: silver handoff inspection package verified at {package_root}")
    print(f"  inspection_id: {manifest['inspection_id']}")
    print(f"  base_handoff.handoff_id: {base['handoff_id']}")
    print(
        f"  handoff_summary.decision_status: {summary['decision_status']}"
    )
    print(
        f"  handoff_summary.recommended_handoff_posture: "
        f"{summary['recommended_handoff_posture']}"
    )
    print(
        f"  gold_gap_inventory.gold_boundary_status: "
        f"{inv['gold_boundary_status']}"
    )
    print(
        f"  gold_gap_inventory.counts: "
        f"present={recomputed_counts[GAP_STATUS_PRESENT]} "
        f"partial={recomputed_counts[GAP_STATUS_PARTIAL]} "
        f"unmet={recomputed_counts[GAP_STATUS_UNMET]} "
        f"out_of_scope={recomputed_counts[GAP_STATUS_OUT_OF_SCOPE]}"
    )
    return 0


def validate_requirement_set_mode(req_set_path: Path) -> int:
    if not req_set_path.exists() or not req_set_path.is_file():
        return usage_error(f"--validate-requirement-set not found: {req_set_path}")
    try:
        req_set = json.loads(req_set_path.read_text())
    except json.JSONDecodeError as e:
        return fail("requirement_set_invalid", f"not valid JSON: {e}")
    err = validate_requirement_set_object(req_set)
    if err is not None:
        return fail(*err)
    print(f"PASS: silver-to-gold requirement set valid at {req_set_path}")
    print(f"  requirement_set_id: {req_set['requirement_set_id']}")
    print(f"  requirement_set_version: {req_set['requirement_set_version']}")
    print(f"  requirement_count: {len(req_set['requirements'])}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.1 handoff inspection package "
            "(default mode --manifest) or validate a Silver-to-Gold "
            "requirement set in isolation (--validate-requirement-set, "
            "used by the v0.3.1 runner). Does not adjudicate, certify, "
            "approve, audit, or transfer reliance."
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", type=Path)
    group.add_argument("--validate-requirement-set", type=Path, dest="req_set")
    args = parser.parse_args(argv)
    if args.manifest is not None:
        return verify_manifest_mode(args.manifest.resolve())
    return validate_requirement_set_mode(args.req_set.resolve())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
