#!/usr/bin/env python3
"""Build a ProofRail Gold v0.4.1 Decision Report Hardening package.

The runner composes a deterministic, hash-anchored local v0.4.1 Gold
Decision Report Hardening package on top of a v0.4.0-shaped governed
reliance package body. The runner:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package:
        - runner_input_path_missing       (argv missing / empty)
        - runner_input_path_forbidden     (absolute path or contains '..')
        - runner_input_file_missing       (path does not exist on disk)
        - runner_input_read_failed        (open/read fails OR path is a
                                          directory, portable)
        - runner_input_json_invalid       (path parses to non-JSON)
      These codes are emitted ONLY here and are NEVER wrapped or
      relayed by Phase B. A sixth runner-only refusal code is
      explicitly NOT introduced for verifier-relayed failures.
  2.  Phase B: build package.
      a. Resolves --output-dir, refusing to overwrite without --force.
      b. Stages under a sibling staging directory
             <output-dir>.staging.<pid>
         and atomically publishes via os.replace().
      c. Byte-copies the input package body JSON to
             <staging>/governed-reliance-scenarios.json
         The byte image is preserved exactly; structural defects in
         the input package remain in the staged copy.
      d. Derives the v0.4.0-shaped conformance report using
         BYTE-IDENTICAL canonical JSON serialization so the v0.4.0
         verifier (subprocess-invoked by the v0.4.1 verifier) matches
         it byte-for-byte.
      e. Derives the v0.4.1 decision report as a normalized projection
         of governed_decisions[] plus a derived coverage_summary.
      f. Builds the three-subject manifest in fixed subject order:
             [0] governed-reliance-scenarios.json
             [1] silver-gold-governed-reliance-conformance-report.json
             [2] gold-governed-reliance-decision-report.json
         with bare lowercase hex SHA-256 (no `sha256:` label prefix)
         and sizes recomputed from the staged copies.
      g. When --self-validate is supplied, subprocess-invokes the v0.4.1
         verifier on the staged manifest BEFORE the atomic move. On a
         non-zero exit, the verifier's stdout/stderr are RELAYED
         UNCHANGED and the staging directory is removed; the
         destination is left untouched.
      h. On success the staging directory is atomically replaced into
         --output-dir via os.replace().

A v0.4.1 package is a deterministic local hand-authored record. It is
NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Runner-only refusal reason vocabulary. Identical naming to the v0.4.0
# runner. A sixth runner-only refusal code is intentionally NOT introduced
# for verifier-relayed failures.
# ---------------------------------------------------------------------------

REFUSAL_PATH_MISSING = "runner_input_path_missing"
REFUSAL_PATH_FORBIDDEN = "runner_input_path_forbidden"
REFUSAL_FILE_MISSING = "runner_input_file_missing"
REFUSAL_READ_FAILED = "runner_input_read_failed"
REFUSAL_JSON_INVALID = "runner_input_json_invalid"


def _refuse(reason: str, detail: str) -> None:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Canonical JSON serialization. Byte-identical between runner and verifier
# so derived report bytes survive cross-tool re-derivation.
# ---------------------------------------------------------------------------

def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Phase A: preflight only. Closed set of 5 runner-only refusal reasons.
# ---------------------------------------------------------------------------

_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


def _preflight_input_path(input_package: str | None) -> Path:
    if input_package is None or input_package == "":
        _refuse(REFUSAL_PATH_MISSING, "--input-package is required and must be non-empty")
    p = input_package  # type: ignore[assignment]
    if os.path.isabs(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"absolute path is not permitted: {p!r}")
    if _has_traversal(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"path traversal is not permitted: {p!r}")
    pp = Path(p)
    if not pp.exists():
        _refuse(REFUSAL_FILE_MISSING, f"input path does not exist: {p!r}")
    # A directory at the input path is treated as a read failure rather than
    # an OS-level chmod, so the test suite does not need chmod 000.
    if pp.is_dir():
        _refuse(REFUSAL_READ_FAILED, f"input path is a directory, not a file: {p!r}")
    try:
        raw = pp.read_bytes()
    except OSError as e:
        _refuse(REFUSAL_READ_FAILED, f"cannot read input file: {p!r}: {e}")
    try:
        json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        _refuse(REFUSAL_JSON_INVALID, f"input is not valid JSON: {p!r}: {e}")
    return pp


# ---------------------------------------------------------------------------
# v0.4.0-shaped conformance report derivation. Byte-identical to the v0.4.0
# runner output so the subprocess-invoked v0.4.0 verifier accepts it.
# ---------------------------------------------------------------------------

APPROVED_VERIFIER_REASONS_ORDERED_V040 = (
    "gold_manifest_invalid",                          # 01
    "gold_package_not_object",                        # 02
    "gold_package_schema_invalid",                    # 03
    "gold_profile_unsupported",                       # 04
    "gold_package_identity_invalid",                  # 05
    "silver_verification_input_invalid",              # 06
    "silver_handoff_input_invalid",                   # 07
    "policy_pack_input_invalid",                      # 08
    "registry_lite_input_invalid",                    # 09
    "control_crosswalk_input_invalid",                # 10
    "governed_decision_set_invalid",                  # 11
    "governed_decision_entry_invalid",                # 12
    "decision_subject_binding_invalid",               # 13
    "decision_policy_binding_invalid",                # 14
    "decision_registry_binding_invalid",              # 15
    "decision_action_scope_invalid",                  # 16
    "decision_status_invalid",                        # 17
    "acceptance_path_invalid",                        # 18
    "rejection_path_invalid",                         # 19
    "challenge_path_invalid",                         # 20
    "withdrawal_path_invalid",                        # 21
    "supersession_path_invalid",                      # 22
    "non_claims_missing",                             # 23
    "prohibited_gold_claim_present",                  # 24
)

# Static check_name descriptions, copied byte-identically from the v0.4.0
# runner so the conformance-report byte image matches.
_CHECK_DETAILS_V040 = {
    "gold_manifest_invalid": "Manifest shape, two-subject layout, paths, and cross-anchors pass.",
    "gold_package_not_object": "Package body parses to a JSON object.",
    "gold_package_schema_invalid": "Package body declares document_type proofrail.gold.governed_reliance_package and schema_version v0.1.0.",
    "gold_profile_unsupported": "Package profile is the closed v0.4.0 value gold.governed_reliance.v0.4.0.",
    "gold_package_identity_invalid": "package_id, governed_reliance_demo_id, and relying_party.identity_id satisfy the closed identifier grammar.",
    "silver_verification_input_invalid": "silver_verification input shape and expected_status pass.",
    "silver_handoff_input_invalid": "silver_handoff input shape and expected_handoff_posture pass.",
    "policy_pack_input_invalid": "policy_pack input shape, policy_pack_id, and policy_pack_version pass.",
    "registry_lite_input_invalid": "registry_lite input shape and registry_id pass.",
    "control_crosswalk_input_invalid": "control_crosswalk input shape and control_pack_id pass.",
    "governed_decision_set_invalid": "governed_decisions list holds 1..5 entries in natural order with unique scenario_type values.",
    "governed_decision_entry_invalid": "Each governed decision entry holds the required fields under the closed grammar.",
    "decision_subject_binding_invalid": "Each decision_subject block holds a closed subject_type and a subject_ref.",
    "decision_policy_binding_invalid": "Each policy_binding block holds policy_pack_id, policy_pack_version, policy_clause_refs, and a closed policy_decision.",
    "decision_registry_binding_invalid": "Each registry_binding block holds relying_party_id and a closed decision_authority_role.",
    "decision_action_scope_invalid": "Each action_scope block holds a closed protected_action_id, action_category, and action_environment.",
    "decision_status_invalid": "Each decision_status value is in the closed status set and matches its scenario_type.",
    "acceptance_path_invalid": "The clean_acceptance entry's scenario_specific_state holds a non-empty acceptance_record_ref.",
    "rejection_path_invalid": "The policy_rejection entry's scenario_specific_state holds a closed rejection_reason and silver_verification_passing true.",
    "challenge_path_invalid": "The challenge_filed entry's scenario_specific_state holds a non-empty challenge_record_ref and a closed challenge_state.",
    "withdrawal_path_invalid": "The withdrawal entry's scenario_specific_state holds a non-empty withdrawal_record_ref and a closed withdrawal_trigger.",
    "supersession_path_invalid": "The supersession entry's scenario_specific_state holds a closed prior_decision_ref_kind, a resolvable prior_decision_id (when internal), a closed supersession_trigger, and a non-empty superseding_input_ref.",
    "non_claims_missing": "non_claims is present and non-empty.",
    "prohibited_gold_claim_present": "No prohibited Gold-claim token appears outside scope_limitations or non_claims.",
}


def _derive_v040_conformance_report(
    *,
    package_id: str,
    governed_reliance_demo_id: str,
    conformance_report_id: str,
    generated_at: str,
) -> dict[str, Any]:
    """Derive a v0.4.0-shaped conformance report byte-identically to v0.4.0."""
    entries = []
    for idx, reason in enumerate(APPROVED_VERIFIER_REASONS_ORDERED_V040, start=1):
        entries.append(
            {
                "check_id": f"check_{idx:02d}",
                "check_name": reason,
                "status": "pass",
                "detail": _CHECK_DETAILS_V040[reason],
            }
        )
    return {
        "document_type": "proofrail.gold.governed_reliance_conformance_report",
        "schema_version": "v0.1.0",
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "report_id": conformance_report_id,
        "generated_at": generated_at,
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# v0.4.1 decision report derivation. Normalized projection of
# governed_decisions[] plus a derived coverage_summary.
# ---------------------------------------------------------------------------

# Closed natural-order scenario_type sequence (mirrors v0.4.0 schema).
SCENARIO_TYPES_ORDERED = (
    "clean_acceptance",
    "policy_rejection",
    "challenge_filed",
    "withdrawal",
    "supersession",
)

# Fixed projection field order used inside decision_fingerprint. The runner
# and verifier MUST agree on the projection contents (not the JSON byte
# order; sort_keys handles that). The list documents the keys; the values
# are mirrored verbatim from the source entry.
DECISION_FINGERPRINT_KEYS = (
    "decision_id",
    "scenario_type",
    "decision_status",
    "decision_trigger",
    "recorded_at",
    "decision_subject",
    "policy_binding",
    "registry_binding",
    "action_scope",
    "scenario_specific_state",
)


def _decision_fingerprint(source_entry: dict[str, Any]) -> str:
    projection = {k: source_entry.get(k) for k in DECISION_FINGERPRINT_KEYS}
    return _sha256_hex(_canonical_json_bytes(projection))


def _derive_decision_rows(governed_decisions: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, entry in enumerate(governed_decisions):
        # The runner does not validate entry shape; the verifier's inherited
        # v0.4.0 checks govern that. If the input is structurally invalid,
        # the staged package will fail the v0.4.1 verifier's Phase 2.
        scenario_type = entry.get("scenario_type") if isinstance(entry, dict) else None
        decision_status = entry.get("decision_status") if isinstance(entry, dict) else None
        path_summary = f"{scenario_type}:{decision_status}"
        row = {
            "row_id": f"row_{idx + 1:02d}",
            "source_decision_index": idx,
            "decision_id": entry.get("decision_id") if isinstance(entry, dict) else None,
            "scenario_type": scenario_type,
            "decision_status": decision_status,
            "decision_trigger": entry.get("decision_trigger") if isinstance(entry, dict) else None,
            "recorded_at": entry.get("recorded_at") if isinstance(entry, dict) else None,
            "decision_subject": entry.get("decision_subject") if isinstance(entry, dict) else None,
            "policy_binding": entry.get("policy_binding") if isinstance(entry, dict) else None,
            "registry_binding": entry.get("registry_binding") if isinstance(entry, dict) else None,
            "action_scope": entry.get("action_scope") if isinstance(entry, dict) else None,
            "scenario_path_summary": path_summary,
            "decision_fingerprint": (
                _decision_fingerprint(entry) if isinstance(entry, dict) else ""
            ),
        }
        rows.append(row)
    return rows


def _derive_coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scenario_types = sorted({r["scenario_type"] for r in rows if r.get("scenario_type")})
    statuses = sorted({r["decision_status"] for r in rows if r.get("decision_status")})
    actions = sorted({
        (r.get("action_scope") or {}).get("protected_action_id")
        for r in rows
        if isinstance(r.get("action_scope"), dict)
        and (r.get("action_scope") or {}).get("protected_action_id")
    })
    pdec = sorted({
        (r.get("policy_binding") or {}).get("policy_decision")
        for r in rows
        if isinstance(r.get("policy_binding"), dict)
        and (r.get("policy_binding") or {}).get("policy_decision")
    })
    roles = sorted({
        (r.get("registry_binding") or {}).get("decision_authority_role")
        for r in rows
        if isinstance(r.get("registry_binding"), dict)
        and (r.get("registry_binding") or {}).get("decision_authority_role")
    })
    fp_list = [r["decision_fingerprint"] for r in rows]
    aggregate_fp = _sha256_hex(_canonical_json_bytes(fp_list))
    return {
        "decision_count": len(rows),
        "scenario_types_present": scenario_types,
        "decision_statuses_present": statuses,
        "protected_actions_present": actions,
        "policy_decisions_present": pdec,
        "registry_roles_present": roles,
        "aggregate_row_fingerprint": aggregate_fp,
    }


def _derive_decision_report(
    *,
    package_obj: dict[str, Any],
    package_id: str,
    governed_reliance_demo_id: str,
    decision_report_id: str,
    generated_at: str,
    source_package_sha256_hex: str,
) -> dict[str, Any]:
    governed_decisions = package_obj.get("governed_decisions", [])
    if not isinstance(governed_decisions, list):
        governed_decisions = []
    rows = _derive_decision_rows(governed_decisions)
    coverage = _derive_coverage_summary(rows)
    scope_limitations = package_obj.get("scope_limitations", [])
    if not isinstance(scope_limitations, list):
        scope_limitations = []
    non_claims = package_obj.get("non_claims", [])
    if not isinstance(non_claims, list):
        non_claims = []
    return {
        "document_type": "proofrail.gold.governed_reliance_decision_report",
        "schema_version": "v0.1.0",
        "profile": "gold.decision_report_hardening.v0.4.1",
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "decision_report_id": decision_report_id,
        "generated_at": generated_at,
        "source_package_sha256": source_package_sha256_hex,
        "decision_count": len(rows),
        "decision_rows": rows,
        "coverage_summary": coverage,
        "scope_limitations": scope_limitations,
        "non_claims": non_claims,
    }


# ---------------------------------------------------------------------------
# Phase B: package build.
# ---------------------------------------------------------------------------

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"
MANIFEST_FILENAME = "gold-decision-report-package-manifest.json"


def _build_manifest(
    *,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    package_path: Path,
    conformance_path: Path,
    decision_path: Path,
    package_sha256_hex: str,
    conformance_sha256_hex: str,
    decision_sha256_hex: str,
) -> dict[str, Any]:
    return {
        "document_type": "proofrail.gold.decision_report_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.decision_report_hardening.v0.4.1",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "conformance_report_id": conformance_report_id,
        "decision_report_id": decision_report_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "generated_at": generated_at,
        "subjects": [
            {
                "role": "governed_reliance_package",
                "path": PACKAGE_SUBJECT_PATH,
                "sha256": package_sha256_hex,
                "size_bytes": package_path.stat().st_size,
            },
            {
                "role": "conformance_report",
                "path": CONFORMANCE_SUBJECT_PATH,
                "sha256": conformance_sha256_hex,
                "size_bytes": conformance_path.stat().st_size,
            },
            {
                "role": "decision_report",
                "path": DECISION_SUBJECT_PATH,
                "sha256": decision_sha256_hex,
                "size_bytes": decision_path.stat().st_size,
            },
        ],
    }


def _atomic_publish(staging: Path, dest: Path) -> None:
    os.replace(staging, dest)


def _remove_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)


# Module constant exposing the verifier path for monkey-patch by tests.
GOLD_DECISION_REPORT_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_decision_report_hardening_v0_1_0.py"
)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.4.1 verifier. Relay unchanged on failure."""
    result = subprocess.run(
        [sys.executable, str(verifier_path), "--manifest", str(manifest_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a ProofRail Gold v0.4.1 Decision Report Hardening package.",
    )
    parser.add_argument(
        "--input-package",
        type=str,
        default=None,
        help="Path to the v0.4.0-shaped governed-reliance package body JSON.",
    )
    parser.add_argument(
        "--manifest-id",
        type=str,
        required=True,
        help="Stable manifest_id for the produced manifest.",
    )
    parser.add_argument(
        "--conformance-report-id",
        type=str,
        required=True,
        help="Stable report_id for the inherited v0.4.0 conformance report (subject [1]).",
    )
    parser.add_argument(
        "--decision-report-id",
        type=str,
        required=True,
        help="Stable decision_report_id for the v0.4.1 decision report (subject [2]). MUST differ from --conformance-report-id.",
    )
    parser.add_argument(
        "--generated-at",
        type=str,
        required=True,
        help="ISO-8601 UTC timestamp ending in 'Z'.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Destination directory for the published package.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination directory if it exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Invoke the v0.4.1 verifier against the staging directory BEFORE the atomic move.",
    )
    args = parser.parse_args(argv)

    # Phase A: preflight only.
    input_package_path = _preflight_input_path(args.input_package)

    # Phase B begins.
    out_dir = Path(args.output_dir)
    if out_dir.exists() and not args.force:
        sys.stderr.write(
            f"refuse: output dir already exists; pass --force to overwrite: {out_dir}\n"
        )
        return 1
    if out_dir.exists() and args.force:
        shutil.rmtree(out_dir)

    staging = out_dir.with_suffix(out_dir.suffix + f".staging.{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=False)

    try:
        # Byte-copy the input package body.
        staged_package = staging / PACKAGE_SUBJECT_PATH
        package_bytes = input_package_path.read_bytes()
        staged_package.write_bytes(package_bytes)
        package_sha256_hex = _sha256_hex(package_bytes)

        # Parse for identity extraction. Structural defects fall through to
        # the verifier.
        try:
            package_obj = json.loads(package_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            package_obj = None

        if isinstance(package_obj, dict) and isinstance(package_obj.get("package_id"), str):
            package_id = package_obj["package_id"]
        else:
            package_id = "proofrail-gold-decision-report-unknown"
        if isinstance(package_obj, dict) and isinstance(
            package_obj.get("governed_reliance_demo_id"), str
        ):
            governed_reliance_demo_id = package_obj["governed_reliance_demo_id"]
        else:
            governed_reliance_demo_id = "gold-decision-report-unknown"

        # Derive the v0.4.0-shaped conformance report (canonical JSON bytes).
        conformance_obj = _derive_v040_conformance_report(
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            conformance_report_id=args.conformance_report_id,
            generated_at=args.generated_at,
        )
        conformance_bytes = _canonical_json_bytes(conformance_obj)
        staged_conformance = staging / CONFORMANCE_SUBJECT_PATH
        staged_conformance.write_bytes(conformance_bytes)
        conformance_sha256_hex = _sha256_hex(conformance_bytes)

        # Derive the v0.4.1 decision report.
        decision_obj = _derive_decision_report(
            package_obj=package_obj if isinstance(package_obj, dict) else {},
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            decision_report_id=args.decision_report_id,
            generated_at=args.generated_at,
            source_package_sha256_hex=package_sha256_hex,
        )
        decision_bytes = _canonical_json_bytes(decision_obj)
        staged_decision = staging / DECISION_SUBJECT_PATH
        staged_decision.write_bytes(decision_bytes)
        decision_sha256_hex = _sha256_hex(decision_bytes)

        # Build the 3-subject manifest after all subjects are written.
        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            conformance_report_id=args.conformance_report_id,
            decision_report_id=args.decision_report_id,
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            generated_at=args.generated_at,
            package_path=staged_package,
            conformance_path=staged_conformance,
            decision_path=staged_decision,
            package_sha256_hex=package_sha256_hex,
            conformance_sha256_hex=conformance_sha256_hex,
            decision_sha256_hex=decision_sha256_hex,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = staging / MANIFEST_FILENAME
        staged_manifest.write_bytes(manifest_bytes)

        # Optional self-validation against the staging directory BEFORE the
        # atomic move. On failure, relay the v0.4.1 verifier's output
        # unchanged (no sixth runner-only refusal code).
        if args.self_validate:
            rc = _self_validate(GOLD_DECISION_REPORT_VERIFIER, staged_manifest)
            if rc != 0:
                _remove_staging(staging)
                return rc

        _atomic_publish(staging, out_dir)
    except Exception:
        _remove_staging(staging)
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
