#!/usr/bin/env python3
"""Build a ProofRail Gold v0.4.2 Policy Evaluation Matrix package.

The v0.4.2 runner composes a deterministic, hash-anchored local
5-subject package on top of a v0.4.0-shaped governed reliance package
body and a hand-authored v0.4.2 matrix template. Phases:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package and --matrix-input under the closed
      runner-only refusal set; no other tokens are emitted here. A
      sixth runner-only refusal is explicitly NOT introduced for
      verifier-relayed failures.
  2.  Phase B: build package.
      a. Resolves --output-dir, refusing to overwrite without --force.
      b. Stages under <output-dir>.staging.<pid>; atomically publishes
         via os.replace() on success.
      c. Byte-copies the input package body to subject [0].
      d. Derives the v0.4.0-shaped conformance report (subject [1])
         BYTE-IDENTICALLY to v0.4.0.
      e. Derives the v0.4.1 decision report (subject [2])
         BYTE-IDENTICALLY to v0.4.1.
      f. Reads the matrix template, injects the two runtime-bound
         scalars (`decision_report_sha256`, `generated_at`), and
         serializes the runtime matrix canonically as subject [3].
      g. Derives the v0.4.2 policy evaluation report (subject [4])
         by the 6-step matching algorithm specified in the schema.
      h. Builds the 5-subject manifest in fixed subject order.
      i. When --self-validate is supplied, subprocess-invokes the
         v0.4.2 verifier against the staged manifest BEFORE the
         atomic move; on non-zero exit the staging directory is
         removed and the verifier output is relayed verbatim.

A v0.4.2 package is a deterministic local hand-authored record. It
is NOT a certificate, NOT signed, NOT federated, NOT a transfer of
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
# Runner-only refusal vocabulary (closed set of 5, identical to v0.4.0 /
# v0.4.1). A sixth refusal is intentionally NOT introduced.
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


_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


# ---------------------------------------------------------------------------
# Phase A: preflight only. Closed set of 5 runner-only refusal reasons.
# ---------------------------------------------------------------------------

def _preflight_input_path(input_path: str | None, arg_label: str) -> Path:
    if input_path is None or input_path == "":
        _refuse(REFUSAL_PATH_MISSING, f"{arg_label} is required and must be non-empty")
    p = input_path  # type: ignore[assignment]
    if os.path.isabs(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"absolute path is not permitted: {p!r}")
    if _has_traversal(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"path traversal is not permitted: {p!r}")
    pp = Path(p)
    if not pp.exists():
        _refuse(REFUSAL_FILE_MISSING, f"input path does not exist: {p!r}")
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
# runner output so the subprocess-invoked v0.4.0 verifier (via v0.4.1) accepts
# it.
# ---------------------------------------------------------------------------

APPROVED_VERIFIER_REASONS_ORDERED_V040 = (
    "gold_manifest_invalid",
    "gold_package_not_object",
    "gold_package_schema_invalid",
    "gold_profile_unsupported",
    "gold_package_identity_invalid",
    "silver_verification_input_invalid",
    "silver_handoff_input_invalid",
    "policy_pack_input_invalid",
    "registry_lite_input_invalid",
    "control_crosswalk_input_invalid",
    "governed_decision_set_invalid",
    "governed_decision_entry_invalid",
    "decision_subject_binding_invalid",
    "decision_policy_binding_invalid",
    "decision_registry_binding_invalid",
    "decision_action_scope_invalid",
    "decision_status_invalid",
    "acceptance_path_invalid",
    "rejection_path_invalid",
    "challenge_path_invalid",
    "withdrawal_path_invalid",
    "supersession_path_invalid",
    "non_claims_missing",
    "prohibited_gold_claim_present",
)

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
# v0.4.1 decision report derivation. Byte-identical to the v0.4.1 runner so
# the inherited subprocess-invoked v0.4.1 verifier accepts it.
# ---------------------------------------------------------------------------

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
# v0.4.2 runtime matrix construction. The runner reads the matrix template,
# injects the two runtime-bound scalars, and serializes canonically.
# ---------------------------------------------------------------------------

def _build_runtime_matrix(
    *,
    template_obj: dict[str, Any],
    decision_report_sha256_hex: str,
    generated_at: str,
) -> dict[str, Any]:
    runtime = dict(template_obj)
    runtime["decision_report_sha256"] = decision_report_sha256_hex
    runtime["generated_at"] = generated_at
    return runtime


# ---------------------------------------------------------------------------
# v0.4.2 evaluation report derivation. Six-step matching algorithm per
# schemas/gold-policy-evaluation-report-v0.1.0.md.
# ---------------------------------------------------------------------------

EVAL_ROW_PROJECTION_KEYS = (
    "matrix_row_id",
    "decision_id",
    "decision_row_id",
    "scenario_type",
    "decision_status",
    "policy_clause_ref",
    "policy_decision",
    "action_category",
    "action_environment",
    "decision_authority_role",
    "subject_type",
    "evaluation_status",
    "evaluation_effect",
)


def _eval_fingerprint(row: dict[str, Any]) -> str:
    projection = {k: row.get(k) for k in EVAL_ROW_PROJECTION_KEYS}
    return _sha256_hex(_canonical_json_bytes(projection))


def _matrix_row_matches_decision_row(
    mrow: dict[str, Any], drow: dict[str, Any]
) -> bool:
    if mrow.get("expected_scenario_type") != drow.get("scenario_type"):
        return False
    if mrow.get("expected_decision_status") != drow.get("decision_status"):
        return False
    pb = drow.get("policy_binding") or {}
    if mrow.get("expected_policy_decision") != pb.get("policy_decision"):
        return False
    asc = drow.get("action_scope") or {}
    if mrow.get("expected_action_category") != asc.get("action_category"):
        return False
    if mrow.get("expected_action_environment") != asc.get("action_environment"):
        return False
    rb = drow.get("registry_binding") or {}
    if mrow.get("expected_decision_authority_role") != rb.get("decision_authority_role"):
        return False
    ds = drow.get("decision_subject") or {}
    if mrow.get("required_subject_type") != ds.get("subject_type"):
        return False
    clauses = pb.get("policy_clause_refs") or []
    if not isinstance(clauses, list):
        return False
    if mrow.get("policy_clause_ref") not in clauses:
        return False
    return True


def _build_matched_row(
    idx: int, mr: dict[str, Any], drow: dict[str, Any], *, status: str
) -> dict[str, Any]:
    pb = drow.get("policy_binding") or {}
    asc = drow.get("action_scope") or {}
    rb = drow.get("registry_binding") or {}
    ds = drow.get("decision_subject") or {}
    effect = mr.get("evaluation_effect")
    return {
        "evaluation_row_id": f"erow_{idx:02d}",
        "matrix_row_id": mr.get("matrix_row_id"),
        "decision_id": drow.get("decision_id"),
        "decision_row_id": drow.get("row_id"),
        "scenario_type": drow.get("scenario_type"),
        "decision_status": drow.get("decision_status"),
        "policy_clause_ref": mr.get("policy_clause_ref"),
        "policy_decision": pb.get("policy_decision"),
        "action_category": asc.get("action_category"),
        "action_environment": asc.get("action_environment"),
        "decision_authority_role": rb.get("decision_authority_role"),
        "subject_type": ds.get("subject_type"),
        "evaluation_status": status,
        "evaluation_effect": effect,
    }


def _build_uncovered_row(idx: int, drow: dict[str, Any]) -> dict[str, Any]:
    pb = drow.get("policy_binding") or {}
    asc = drow.get("action_scope") or {}
    rb = drow.get("registry_binding") or {}
    ds = drow.get("decision_subject") or {}
    return {
        "evaluation_row_id": f"erow_{idx:02d}",
        "matrix_row_id": None,
        "decision_id": drow.get("decision_id"),
        "decision_row_id": drow.get("row_id"),
        "scenario_type": drow.get("scenario_type"),
        "decision_status": drow.get("decision_status"),
        "policy_clause_ref": None,
        "policy_decision": pb.get("policy_decision"),
        "action_category": asc.get("action_category"),
        "action_environment": asc.get("action_environment"),
        "decision_authority_role": rb.get("decision_authority_role"),
        "subject_type": ds.get("subject_type"),
        "evaluation_status": "decision_row_uncovered",
        "evaluation_effect": None,
    }


def _build_unmatched_matrix_row(idx: int, mr: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_row_id": f"erow_{idx:02d}",
        "matrix_row_id": mr.get("matrix_row_id"),
        "decision_id": None,
        "decision_row_id": None,
        "scenario_type": mr.get("expected_scenario_type"),
        "decision_status": mr.get("expected_decision_status"),
        "policy_clause_ref": mr.get("policy_clause_ref"),
        "policy_decision": mr.get("expected_policy_decision"),
        "action_category": mr.get("expected_action_category"),
        "action_environment": mr.get("expected_action_environment"),
        "decision_authority_role": mr.get("expected_decision_authority_role"),
        "subject_type": mr.get("required_subject_type"),
        "evaluation_status": "matrix_row_unmatched",
        "evaluation_effect": None,
    }


def _derive_evaluation_rows(
    matrix_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_rows: list[dict[str, Any]] = []
    matched_matrix_ids: set[str] = set()
    next_idx = 1

    for drow in decision_rows:
        matches = [mr for mr in matrix_rows if _matrix_row_matches_decision_row(mr, drow)]
        if len(matches) == 1:
            mr = matches[0]
            eval_rows.append(_build_matched_row(next_idx, mr, drow, status="matched"))
            matched_matrix_ids.add(mr.get("matrix_row_id"))
            next_idx += 1
        elif len(matches) >= 2:
            distinct = {
                (m.get("evaluation_effect"), m.get("row_rationale_code")) for m in matches
            }
            mr = matches[0]
            if len(distinct) == 1:
                eval_rows.append(
                    _build_matched_row(next_idx, mr, drow, status="matched")
                )
            else:
                eval_rows.append(
                    _build_matched_row(next_idx, mr, drow, status="matrix_conflict_detected")
                )
            for m in matches:
                matched_matrix_ids.add(m.get("matrix_row_id"))
            next_idx += 1
        else:
            eval_rows.append(_build_uncovered_row(next_idx, drow))
            next_idx += 1

    for mr in matrix_rows:
        if mr.get("matrix_row_id") not in matched_matrix_ids:
            eval_rows.append(_build_unmatched_matrix_row(next_idx, mr))
            next_idx += 1

    for r in eval_rows:
        r["evaluation_fingerprint"] = _eval_fingerprint(r)

    return eval_rows


def _derive_eval_coverage_summary(
    eval_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    distinct_drow_ids: set[str] = set()
    matched = unmatched = uncovered = conflict = 0
    for r in eval_rows:
        st = r.get("evaluation_status")
        if st == "matched":
            matched += 1
        elif st == "matrix_row_unmatched":
            unmatched += 1
        elif st == "decision_row_uncovered":
            uncovered += 1
        elif st == "matrix_conflict_detected":
            conflict += 1
        if st in ("matched", "matrix_conflict_detected", "decision_row_uncovered"):
            drid = r.get("decision_row_id")
            if isinstance(drid, str):
                distinct_drow_ids.add(drid)
    matrix_ids = {mr.get("matrix_row_id") for mr in matrix_rows}
    fp_list = [r.get("evaluation_fingerprint", "") for r in eval_rows]
    aggregate = _sha256_hex(_canonical_json_bytes(fp_list))
    return {
        "decision_row_count": len(distinct_drow_ids),
        "matrix_row_count": len(matrix_ids),
        "matched_count": matched,
        "unmatched_matrix_row_count": unmatched,
        "uncovered_decision_row_count": uncovered,
        "conflict_count": conflict,
        "aggregate_evaluation_fingerprint": aggregate,
    }


def _derive_evaluation_report(
    *,
    matrix_obj: dict[str, Any],
    decision_obj: dict[str, Any],
    policy_evaluation_report_id: str,
    generated_at: str,
    source_decision_report_sha256_hex: str,
    source_matrix_sha256_hex: str,
) -> dict[str, Any]:
    matrix_rows = matrix_obj.get("matrix_rows") or []
    decision_rows = decision_obj.get("decision_rows") or []
    eval_rows = _derive_evaluation_rows(matrix_rows, decision_rows)
    coverage = _derive_eval_coverage_summary(eval_rows, matrix_rows)
    scope_limitations = matrix_obj.get("scope_limitations") or []
    non_claims = matrix_obj.get("non_claims") or []
    return {
        "document_type": "proofrail.gold.policy_evaluation_report",
        "schema_version": "v0.1.0",
        "profile": "gold.policy_evaluation_matrix.v0.4.2",
        "package_id": matrix_obj.get("package_id"),
        "governed_reliance_demo_id": matrix_obj.get("governed_reliance_demo_id"),
        "matrix_id": matrix_obj.get("matrix_id"),
        "policy_evaluation_report_id": policy_evaluation_report_id,
        "generated_at": generated_at,
        "source_decision_report_sha256": source_decision_report_sha256_hex,
        "source_matrix_sha256": source_matrix_sha256_hex,
        "evaluation_rows": eval_rows,
        "coverage_summary": coverage,
        "scope_limitations": scope_limitations,
        "non_claims": non_claims,
    }


# ---------------------------------------------------------------------------
# Phase B: package build (5-subject manifest).
# ---------------------------------------------------------------------------

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"
MATRIX_SUBJECT_PATH = "gold-policy-evaluation-matrix.json"
EVALUATION_SUBJECT_PATH = "gold-policy-evaluation-report.json"
MANIFEST_FILENAME = "gold-policy-evaluation-matrix-package-manifest.json"


def _build_manifest(
    *,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    matrix_id: str,
    policy_evaluation_report_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    package_path: Path,
    conformance_path: Path,
    decision_path: Path,
    matrix_path: Path,
    evaluation_path: Path,
    package_sha256_hex: str,
    conformance_sha256_hex: str,
    decision_sha256_hex: str,
    matrix_sha256_hex: str,
    evaluation_sha256_hex: str,
) -> dict[str, Any]:
    return {
        "document_type": "proofrail.gold.policy_evaluation_matrix_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.policy_evaluation_matrix.v0.4.2",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "conformance_report_id": conformance_report_id,
        "decision_report_id": decision_report_id,
        "matrix_id": matrix_id,
        "policy_evaluation_report_id": policy_evaluation_report_id,
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
            {
                "role": "policy_evaluation_matrix",
                "path": MATRIX_SUBJECT_PATH,
                "sha256": matrix_sha256_hex,
                "size_bytes": matrix_path.stat().st_size,
            },
            {
                "role": "policy_evaluation_report",
                "path": EVALUATION_SUBJECT_PATH,
                "sha256": evaluation_sha256_hex,
                "size_bytes": evaluation_path.stat().st_size,
            },
        ],
    }


def _atomic_publish(staging: Path, dest: Path) -> None:
    os.replace(staging, dest)


def _remove_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)


# Module constant exposing the verifier path (subprocess-invoked).
GOLD_POLICY_EVALUATION_MATRIX_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_policy_evaluation_matrix_v0_1_0.py"
)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
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
        description="Build a ProofRail Gold v0.4.2 Policy Evaluation Matrix package.",
    )
    parser.add_argument("--input-package", type=str, default=None,
                        help="Path to the v0.4.0-shaped governed-reliance package body JSON.")
    parser.add_argument("--matrix-input", type=str, default=None,
                        help="Path to the v0.4.2 hand-authored matrix template JSON.")
    parser.add_argument("--manifest-id", type=str, required=True)
    parser.add_argument("--conformance-report-id", type=str, required=True)
    parser.add_argument("--decision-report-id", type=str, required=True)
    parser.add_argument("--policy-evaluation-report-id", type=str, required=True)
    parser.add_argument("--generated-at", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-validate", action="store_true")
    args = parser.parse_args(argv)

    # Phase A: preflight (5 runner-only refusals only).
    input_package_path = _preflight_input_path(args.input_package, "--input-package")
    matrix_input_path = _preflight_input_path(args.matrix_input, "--matrix-input")

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
        # Byte-copy the input package body (subject [0]).
        staged_package = staging / PACKAGE_SUBJECT_PATH
        package_bytes = input_package_path.read_bytes()
        staged_package.write_bytes(package_bytes)
        package_sha256_hex = _sha256_hex(package_bytes)

        # Parse for identity extraction; structural defects fall through.
        try:
            package_obj = json.loads(package_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            package_obj = None

        if isinstance(package_obj, dict) and isinstance(package_obj.get("package_id"), str):
            package_id = package_obj["package_id"]
        else:
            package_id = "proofrail-gold-policy-evaluation-matrix-unknown"
        if isinstance(package_obj, dict) and isinstance(
            package_obj.get("governed_reliance_demo_id"), str
        ):
            governed_reliance_demo_id = package_obj["governed_reliance_demo_id"]
        else:
            governed_reliance_demo_id = "gold-policy-evaluation-matrix-unknown"

        # Derive v0.4.0 conformance report (subject [1]).
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

        # Derive v0.4.1 decision report (subject [2]).
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

        # Read matrix template; structural defects fall through to verifier.
        matrix_template_bytes = matrix_input_path.read_bytes()
        try:
            matrix_template = json.loads(matrix_template_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            matrix_template = {}
        if not isinstance(matrix_template, dict):
            matrix_template = {}

        # Build runtime matrix by injecting the two runtime-bound scalars.
        runtime_matrix = _build_runtime_matrix(
            template_obj=matrix_template,
            decision_report_sha256_hex=decision_sha256_hex,
            generated_at=args.generated_at,
        )
        matrix_bytes = _canonical_json_bytes(runtime_matrix)
        staged_matrix = staging / MATRIX_SUBJECT_PATH
        staged_matrix.write_bytes(matrix_bytes)
        matrix_sha256_hex = _sha256_hex(matrix_bytes)

        # Derive policy evaluation report (subject [4]).
        evaluation_obj = _derive_evaluation_report(
            matrix_obj=runtime_matrix,
            decision_obj=decision_obj,
            policy_evaluation_report_id=args.policy_evaluation_report_id,
            generated_at=args.generated_at,
            source_decision_report_sha256_hex=decision_sha256_hex,
            source_matrix_sha256_hex=matrix_sha256_hex,
        )
        evaluation_bytes = _canonical_json_bytes(evaluation_obj)
        staged_evaluation = staging / EVALUATION_SUBJECT_PATH
        staged_evaluation.write_bytes(evaluation_bytes)
        evaluation_sha256_hex = _sha256_hex(evaluation_bytes)

        # Pull matrix_id from the template (hand-authored content).
        matrix_id = matrix_template.get("matrix_id") if isinstance(matrix_template.get("matrix_id"), str) \
            else "proofrail-gold-policy-evaluation-matrix-unknown"

        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            conformance_report_id=args.conformance_report_id,
            decision_report_id=args.decision_report_id,
            matrix_id=matrix_id,
            policy_evaluation_report_id=args.policy_evaluation_report_id,
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            generated_at=args.generated_at,
            package_path=staged_package,
            conformance_path=staged_conformance,
            decision_path=staged_decision,
            matrix_path=staged_matrix,
            evaluation_path=staged_evaluation,
            package_sha256_hex=package_sha256_hex,
            conformance_sha256_hex=conformance_sha256_hex,
            decision_sha256_hex=decision_sha256_hex,
            matrix_sha256_hex=matrix_sha256_hex,
            evaluation_sha256_hex=evaluation_sha256_hex,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = staging / MANIFEST_FILENAME
        staged_manifest.write_bytes(manifest_bytes)

        if args.self_validate:
            rc = _self_validate(GOLD_POLICY_EVALUATION_MATRIX_VERIFIER, staged_manifest)
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
