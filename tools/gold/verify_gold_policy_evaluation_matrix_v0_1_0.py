#!/usr/bin/env python3
"""Verify a ProofRail Gold v0.4.2 Policy Evaluation Matrix package.

The v0.4.2 verifier extends the v0.4.1 Decision Report Hardening
verifier with nine new ordered checks against the v0.4.2 matrix and
policy evaluation report subjects. The v0.4.2 verifier DELEGATES the
inherited 24+5 v0.4.0/v0.4.1 checks to the co-located v0.4.1
verifier (`verify_gold_decision_report_hardening_v0_1_0.py` under
the same `tools/gold/` directory) via subprocess against a synthesized
3-subject v0.4.1 manifest so the inherited 29 checks run without
duplication. A missing or unlaunchable v0.4.1 verifier is treated as
an ENVIRONMENT failure: it emits a non-reason-shaped `INFRA:`
diagnostic to stderr, exits with code 3, and MUST NOT collapse into
any of the 38 public verifier reason names or the 5 runner-only
refusal names.

Public failure reasons (closed set of 38, verbatim from the v0.4.2
spec, with 29 inherited from v0.4.1 and 9 introduced by v0.4.2):

  Inherited from v0.4.1 (relayed verbatim from the v0.4.1 verifier
  or emitted directly by v0.4.2 manifest-integrity checks):

  01 gold_manifest_invalid
  02 gold_package_not_object
  03 gold_package_schema_invalid
  04 gold_profile_unsupported
  05 gold_package_identity_invalid
  06 silver_verification_input_invalid
  07 silver_handoff_input_invalid
  08 policy_pack_input_invalid
  09 registry_lite_input_invalid
  10 control_crosswalk_input_invalid
  11 governed_decision_set_invalid
  12 governed_decision_entry_invalid
  13 decision_subject_binding_invalid
  14 decision_policy_binding_invalid
  15 decision_registry_binding_invalid
  16 decision_action_scope_invalid
  17 decision_status_invalid
  18 acceptance_path_invalid
  19 rejection_path_invalid
  20 challenge_path_invalid
  21 withdrawal_path_invalid
  22 supersession_path_invalid
  23 non_claims_missing
  24 prohibited_gold_claim_present
  25 gold_decision_report_not_object
  26 gold_decision_report_schema_invalid
  27 gold_decision_report_binding_invalid
  28 gold_decision_report_projection_invalid
  29 gold_decision_report_summary_invalid

  Introduced by v0.4.2:

  30 gold_policy_matrix_not_object
  31 gold_policy_matrix_schema_invalid
  32 gold_policy_matrix_binding_invalid
  33 gold_policy_matrix_entry_invalid
  34 gold_policy_evaluation_report_not_object
  35 gold_policy_evaluation_report_schema_invalid
  36 gold_policy_evaluation_report_binding_invalid
  37 gold_policy_evaluation_result_invalid
  38 gold_policy_evaluation_summary_invalid

The verifier never emits the 5 runner-only refusal reasons
(`runner_input_*`).
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
import tempfile
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 38 approved verifier failure reasons (closed set, verbatim).
# ---------------------------------------------------------------------------

R01 = "gold_manifest_invalid"
R30 = "gold_policy_matrix_not_object"
R31 = "gold_policy_matrix_schema_invalid"
R32 = "gold_policy_matrix_binding_invalid"
R33 = "gold_policy_matrix_entry_invalid"
R34 = "gold_policy_evaluation_report_not_object"
R35 = "gold_policy_evaluation_report_schema_invalid"
R36 = "gold_policy_evaluation_report_binding_invalid"
R37 = "gold_policy_evaluation_result_invalid"
R38 = "gold_policy_evaluation_summary_invalid"

# Closed runner-only refusal set; the verifier never emits these.
RUNNER_ONLY_REFUSALS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

# ---------------------------------------------------------------------------
# Closed constants for v0.4.2 manifest, matrix, evaluation report.
# ---------------------------------------------------------------------------

EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.policy_evaluation_matrix_package_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_RELEASE = "gold.policy_evaluation_matrix.v0.4.2"
EXPECTED_HASH_ALGO = "sha256"

EXPECTED_MATRIX_DOC_TYPE = "proofrail.gold.policy_evaluation_matrix"
EXPECTED_MATRIX_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MATRIX_PROFILE = "gold.policy_evaluation_matrix.v0.4.2"

EXPECTED_EVAL_DOC_TYPE = "proofrail.gold.policy_evaluation_report"
EXPECTED_EVAL_SCHEMA_VERSION = "v0.1.0"
EXPECTED_EVAL_PROFILE = "gold.policy_evaluation_matrix.v0.4.2"

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"
MATRIX_SUBJECT_PATH = "gold-policy-evaluation-matrix.json"
EVALUATION_SUBJECT_PATH = "gold-policy-evaluation-report.json"

EXPECTED_SUBJECT_PATHS = (
    PACKAGE_SUBJECT_PATH,
    CONFORMANCE_SUBJECT_PATH,
    DECISION_SUBJECT_PATH,
    MATRIX_SUBJECT_PATH,
    EVALUATION_SUBJECT_PATH,
)
EXPECTED_SUBJECT_ROLES = (
    "governed_reliance_package",
    "conformance_report",
    "decision_report",
    "policy_evaluation_matrix",
    "policy_evaluation_report",
)

PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
BARE_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Closed sets from the matrix schema.
SCENARIO_TYPES = {"clean_acceptance", "policy_rejection", "challenge_filed", "withdrawal", "supersession"}
DECISION_STATUSES = {"accepted", "rejected", "challenged", "withdrawn", "superseded"}
POLICY_DECISIONS = {"allow", "deny", "conditional", "withhold", "review"}
ACTION_CATEGORIES = {"financial_release", "data_export", "deployment_change", "secret_rotation", "vendor_approval"}
ACTION_ENVIRONMENTS = {"demo", "staging", "production_simulated"}
AUTHORITY_ROLES = {"issuer", "verifier", "relying_party", "policy_authority", "revocation_source", "protected_action_authority"}
SUBJECT_TYPES = {"silver_verification_result", "silver_acceptance_handoff", "challenge_withdrawal_record"}
EVAL_EFFECTS = {"supports_decision", "blocks_decision", "requires_review", "withholds_reliance", "supersedes_prior"}
ROW_RATIONALES = {"silver_pass_policy_allow", "silver_pass_policy_deny", "challenge_requires_review", "withdrawal_requires_withhold", "supersession_updates_basis"}
EVAL_STATUSES = {"matched", "matrix_row_unmatched", "decision_row_uncovered", "matrix_conflict_detected"}

SCENARIO_STATUS_PAIRS = {
    ("clean_acceptance", "accepted"),
    ("policy_rejection", "rejected"),
    ("challenge_filed", "challenged"),
    ("withdrawal", "withdrawn"),
    ("supersession", "superseded"),
}
SCENARIO_EFFECT_PAIRS = {
    ("clean_acceptance", "supports_decision"),
    ("policy_rejection", "blocks_decision"),
    ("challenge_filed", "requires_review"),
    ("withdrawal", "withholds_reliance"),
    ("supersession", "supersedes_prior"),
}
SCENARIO_RATIONALE_PAIRS = {
    ("clean_acceptance", "silver_pass_policy_allow"),
    ("policy_rejection", "silver_pass_policy_deny"),
    ("challenge_filed", "challenge_requires_review"),
    ("withdrawal", "withdrawal_requires_withhold"),
    ("supersession", "supersession_updates_basis"),
}

# Module constant exposing the v0.4.1 verifier path (subprocess-invoked).
GOLD_V041_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_decision_report_hardening_v0_1_0.py"
)


# ---------------------------------------------------------------------------
# Fail helpers and serializer.
# ---------------------------------------------------------------------------

def _emit_fail(reason: str, detail: str) -> int:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    return 1


def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


# ---------------------------------------------------------------------------
# Phase 1: v0.4.2 manifest structural integrity. All folds emit R01.
# ---------------------------------------------------------------------------

def _check_manifest(manifest_path: Path) -> tuple[int, dict[str, Any] | None]:
    if not manifest_path.exists():
        return _emit_fail(R01, f"manifest path does not exist: {manifest_path}"), None
    try:
        raw = manifest_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"cannot read manifest: {e}"), None
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"manifest is not valid JSON: {e}"), None
    if not isinstance(manifest, dict):
        return _emit_fail(R01, "manifest is not a JSON object"), None

    if manifest.get("document_type") != EXPECTED_MANIFEST_DOC_TYPE:
        return _emit_fail(R01, f"document_type must be {EXPECTED_MANIFEST_DOC_TYPE!r}"), None
    if manifest.get("schema_version") != EXPECTED_MANIFEST_SCHEMA_VERSION:
        return _emit_fail(R01, f"schema_version must be {EXPECTED_MANIFEST_SCHEMA_VERSION!r}"), None
    if manifest.get("proofrail_release") != EXPECTED_MANIFEST_RELEASE:
        return _emit_fail(R01, f"proofrail_release must be {EXPECTED_MANIFEST_RELEASE!r}"), None
    if manifest.get("hash_algorithm") != EXPECTED_HASH_ALGO:
        return _emit_fail(R01, f"hash_algorithm must be {EXPECTED_HASH_ALGO!r}"), None

    for field in (
        "manifest_id",
        "conformance_report_id",
        "decision_report_id",
        "matrix_id",
        "policy_evaluation_report_id",
        "package_id",
        "governed_reliance_demo_id",
        "generated_at",
    ):
        val = manifest.get(field)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R01, f"{field} must be a non-empty string"), None

    for field in (
        "manifest_id",
        "conformance_report_id",
        "decision_report_id",
        "matrix_id",
        "policy_evaluation_report_id",
    ):
        if not PACKAGE_ID_RE.fullmatch(manifest[field]):
            return _emit_fail(R01, f"{field} fails closed identifier grammar: {manifest[field]!r}"), None

    # Pairwise distinctness across the four subject-bound identifiers.
    quartet = (
        ("conformance_report_id", manifest["conformance_report_id"]),
        ("decision_report_id", manifest["decision_report_id"]),
        ("matrix_id", manifest["matrix_id"]),
        ("policy_evaluation_report_id", manifest["policy_evaluation_report_id"]),
    )
    seen: dict[str, str] = {}
    for name, val in quartet:
        if val in seen:
            return _emit_fail(
                R01,
                f"{name} and {seen[val]} must be distinct (both equal {val!r})",
            ), None
        seen[val] = name

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return _emit_fail(R01, "subjects must be a JSON array"), None
    if len(subjects) != 5:
        return _emit_fail(R01, f"subjects must hold exactly 5 entries, got {len(subjects)}"), None

    for idx, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return _emit_fail(R01, f"subjects[{idx}] is not an object"), None
        role = subj.get("role")
        path = subj.get("path")
        sha = subj.get("sha256")
        size = subj.get("size_bytes")
        if role != EXPECTED_SUBJECT_ROLES[idx]:
            return _emit_fail(R01, f"subjects[{idx}].role must be {EXPECTED_SUBJECT_ROLES[idx]!r}, got {role!r}"), None
        if not isinstance(path, str) or path == "":
            return _emit_fail(R01, f"subjects[{idx}].path must be a non-empty string"), None
        if _has_traversal(path):
            return _emit_fail(R01, f"subjects[{idx}].path contains path traversal: {path!r}"), None
        if os.path.isabs(path):
            return _emit_fail(R01, f"subjects[{idx}].path must be relative: {path!r}"), None
        if path != EXPECTED_SUBJECT_PATHS[idx]:
            return _emit_fail(R01, f"subjects[{idx}].path must equal {EXPECTED_SUBJECT_PATHS[idx]!r}, got {path!r}"), None
        if not isinstance(sha, str) or not BARE_HEX_SHA256_RE.fullmatch(sha):
            return _emit_fail(R01, f"subjects[{idx}].sha256 must be bare lowercase hex SHA-256"), None
        if not isinstance(size, int) or size < 0:
            return _emit_fail(R01, f"subjects[{idx}].size_bytes must be a non-negative integer"), None

    # File-on-disk checks for all five subjects.
    manifest_dir = manifest_path.parent
    for idx, subj in enumerate(subjects):
        subj_path = manifest_dir / subj["path"]
        if not subj_path.exists():
            return _emit_fail(R01, f"subjects[{idx}] file does not exist: {subj['path']!r}"), None
        try:
            body = subj_path.read_bytes()
        except OSError as e:
            return _emit_fail(R01, f"subjects[{idx}] cannot be read: {e}"), None
        if len(body) != subj["size_bytes"]:
            return _emit_fail(
                R01,
                f"subjects[{idx}] size mismatch: manifest={subj['size_bytes']}, actual={len(body)}",
            ), None
        if _sha256_hex(body) != subj["sha256"]:
            return _emit_fail(
                R01,
                f"subjects[{idx}] sha256 mismatch: manifest={subj['sha256']}, actual={_sha256_hex(body)}",
            ), None

    return 0, manifest


# ---------------------------------------------------------------------------
# Phase 2: subprocess-invoke the unchanged v0.4.1 verifier on a synthesized
# 3-subject v0.4.1 manifest. Inherited 29 reasons are relayed verbatim.
# A missing or crashing v0.4.1 verifier emits an INFRA: diagnostic and
# exits with code 3 (distinct from verifier-reason exit 1, INFRA never
# collapses into any of the 38 public reasons).
# ---------------------------------------------------------------------------

def _run_inherited_v041_checks(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    package_subj = manifest["subjects"][0]
    conformance_subj = manifest["subjects"][1]
    decision_subj = manifest["subjects"][2]
    for subj in (package_subj, conformance_subj, decision_subj):
        if not (manifest_dir / subj["path"]).exists():
            return _emit_fail(R01, "subject file missing prior to inherited v0.4.1 verification")

    v041_manifest = {
        "document_type": "proofrail.gold.decision_report_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.decision_report_hardening.v0.4.1",
        "hash_algorithm": "sha256",
        "manifest_id": manifest["manifest_id"],
        "conformance_report_id": manifest["conformance_report_id"],
        "decision_report_id": manifest["decision_report_id"],
        "package_id": manifest["package_id"],
        "governed_reliance_demo_id": manifest["governed_reliance_demo_id"],
        "generated_at": manifest["generated_at"],
        "subjects": [
            {
                "role": "governed_reliance_package",
                "path": PACKAGE_SUBJECT_PATH,
                "sha256": package_subj["sha256"],
                "size_bytes": package_subj["size_bytes"],
            },
            {
                "role": "conformance_report",
                "path": CONFORMANCE_SUBJECT_PATH,
                "sha256": conformance_subj["sha256"],
                "size_bytes": conformance_subj["size_bytes"],
            },
            {
                "role": "decision_report",
                "path": DECISION_SUBJECT_PATH,
                "sha256": decision_subj["sha256"],
                "size_bytes": decision_subj["size_bytes"],
            },
        ],
    }

    with tempfile.TemporaryDirectory(prefix="v042_inherited_") as td:
        td_path = Path(td)
        shutil.copyfile(manifest_dir / PACKAGE_SUBJECT_PATH, td_path / PACKAGE_SUBJECT_PATH)
        shutil.copyfile(manifest_dir / CONFORMANCE_SUBJECT_PATH, td_path / CONFORMANCE_SUBJECT_PATH)
        shutil.copyfile(manifest_dir / DECISION_SUBJECT_PATH, td_path / DECISION_SUBJECT_PATH)
        synthesized = td_path / "gold-decision-report-package-manifest.json"
        synthesized.write_bytes(_canonical_json_bytes(v041_manifest))

        if not GOLD_V041_VERIFIER.exists():
            sys.stderr.write(
                "INFRA: co-located v0.4.1 verifier unavailable for inherited "
                f"check delegation: expected at {GOLD_V041_VERIFIER}\n"
            )
            return 3
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(GOLD_V041_VERIFIER),
                    "--manifest",
                    str(synthesized),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            sys.stderr.write(
                "INFRA: co-located v0.4.1 verifier unavailable for inherited "
                f"check delegation: {type(e).__name__}: {e}\n"
            )
            return 3
        if result.returncode != 0:
            if result.stdout:
                sys.stdout.buffer.write(result.stdout)
            if result.stderr:
                sys.stderr.buffer.write(result.stderr)
            # An infra-style failure from the delegated v0.4.1 verifier
            # (its own exit code 2 for INFRA, or any non-1 non-zero) must
            # NOT collapse into a public reason here either.
            if result.returncode != 1:
                return 3
            return result.returncode
    return 0


# ---------------------------------------------------------------------------
# Phase 3: v0.4.2 cross-anchor checks against the package body, decision
# report, matrix, and evaluation report (R01 folds).
# ---------------------------------------------------------------------------

def _check_cross_anchors(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None]:
    package_path = manifest_dir / PACKAGE_SUBJECT_PATH
    try:
        package_obj = json.loads(package_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"package body unreadable for cross-anchor check: {e}"), None, None
    if not isinstance(package_obj, dict):
        return _emit_fail(R01, "package body is not an object for cross-anchor check"), None, None

    if package_obj.get("package_id") != manifest["package_id"]:
        return _emit_fail(
            R01,
            f"package_id cross-anchor mismatch: manifest={manifest['package_id']!r}, "
            f"package={package_obj.get('package_id')!r}",
        ), None, None
    if package_obj.get("governed_reliance_demo_id") != manifest["governed_reliance_demo_id"]:
        return _emit_fail(
            R01,
            f"governed_reliance_demo_id cross-anchor mismatch: "
            f"manifest={manifest['governed_reliance_demo_id']!r}, "
            f"package={package_obj.get('governed_reliance_demo_id')!r}",
        ), None, None

    decision_path = manifest_dir / DECISION_SUBJECT_PATH
    try:
        decision_obj = json.loads(decision_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"decision report unreadable for cross-anchor check: {e}"), None, None
    if not isinstance(decision_obj, dict):
        return _emit_fail(R01, "decision report is not an object for cross-anchor check"), None, None
    if decision_obj.get("decision_report_id") != manifest["decision_report_id"]:
        return _emit_fail(
            R01,
            f"decision_report_id cross-anchor mismatch: "
            f"manifest={manifest['decision_report_id']!r}, "
            f"report={decision_obj.get('decision_report_id')!r}",
        ), None, None

    return 0, package_obj, decision_obj


# ---------------------------------------------------------------------------
# Phase 4: v0.4.2 matrix subject checks (R30..R33).
# ---------------------------------------------------------------------------

MATRIX_REQUIRED_FIELDS = (
    "document_type", "schema_version", "profile",
    "matrix_id", "package_id", "governed_reliance_demo_id",
    "decision_report_ref", "decision_report_sha256",
    "policy_pack_id", "policy_pack_version", "generated_at",
    "matrix_rows", "scope_limitations", "non_claims",
)

MATRIX_ROW_FIELDS = (
    "matrix_row_id", "policy_clause_ref",
    "expected_scenario_type", "expected_decision_status",
    "expected_policy_decision", "expected_action_category",
    "expected_action_environment", "expected_decision_authority_role",
    "required_subject_type", "evaluation_effect", "row_rationale_code",
)

POLICY_CLAUSE_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")


def _check_matrix(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
    package_obj: dict[str, Any],
    decision_obj: dict[str, Any],
) -> tuple[int, dict[str, Any] | None]:
    matrix_path = manifest_dir / MATRIX_SUBJECT_PATH
    try:
        raw = matrix_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"matrix file unreadable: {e}"), None

    # check_30 gold_policy_matrix_not_object
    try:
        matrix = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R30, f"matrix is not valid JSON: {e}"), None
    if not isinstance(matrix, dict):
        return _emit_fail(R30, "matrix is not a JSON object"), None

    # check_31 gold_policy_matrix_schema_invalid
    for f in MATRIX_REQUIRED_FIELDS:
        if f not in matrix:
            return _emit_fail(R31, f"matrix is missing required field {f!r}"), None
    if matrix.get("document_type") != EXPECTED_MATRIX_DOC_TYPE:
        return _emit_fail(R31, f"document_type must be {EXPECTED_MATRIX_DOC_TYPE!r}"), None
    if matrix.get("schema_version") != EXPECTED_MATRIX_SCHEMA_VERSION:
        return _emit_fail(R31, f"schema_version must be {EXPECTED_MATRIX_SCHEMA_VERSION!r}"), None
    if matrix.get("profile") != EXPECTED_MATRIX_PROFILE:
        return _emit_fail(R31, f"profile must be {EXPECTED_MATRIX_PROFILE!r}"), None
    for f in ("matrix_id", "package_id", "governed_reliance_demo_id",
              "decision_report_ref", "policy_pack_id", "policy_pack_version",
              "generated_at"):
        val = matrix.get(f)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R31, f"{f} must be a non-empty string"), None
    for f in ("matrix_id", "package_id", "governed_reliance_demo_id",
              "decision_report_ref", "policy_pack_id"):
        if not PACKAGE_ID_RE.fullmatch(matrix[f]):
            return _emit_fail(R31, f"{f} fails closed identifier grammar: {matrix[f]!r}"), None
    if not isinstance(matrix.get("decision_report_sha256"), str) or \
       not BARE_HEX_SHA256_RE.fullmatch(matrix["decision_report_sha256"]):
        return _emit_fail(R31, "decision_report_sha256 must be bare lowercase hex SHA-256"), None
    if not isinstance(matrix.get("matrix_rows"), list):
        return _emit_fail(R31, "matrix_rows must be a JSON array"), None
    if not (1 <= len(matrix["matrix_rows"]) <= 10):
        return _emit_fail(R31, f"matrix_rows length must be 1..10, got {len(matrix['matrix_rows'])}"), None
    for f in ("scope_limitations", "non_claims"):
        val = matrix.get(f)
        if not isinstance(val, list) or len(val) == 0:
            return _emit_fail(R31, f"{f} must be a non-empty array"), None
        for s in val:
            if not isinstance(s, str) or s.strip() == "":
                return _emit_fail(R31, f"{f} entries must be non-blank strings"), None
    # Per-row schema (shape + closed sets).
    for idx, row in enumerate(matrix["matrix_rows"]):
        if not isinstance(row, dict):
            return _emit_fail(R31, f"matrix_rows[{idx}] is not an object"), None
        for f in MATRIX_ROW_FIELDS:
            if f not in row:
                return _emit_fail(R31, f"matrix_rows[{idx}] missing required field {f!r}"), None
        mrid = row["matrix_row_id"]
        if not isinstance(mrid, str) or not re.fullmatch(r"mrow_(0[1-9]|10)", mrid):
            return _emit_fail(R31, f"matrix_rows[{idx}].matrix_row_id fails grammar: {mrid!r}"), None
        if not isinstance(row["policy_clause_ref"], str) or not POLICY_CLAUSE_RE.fullmatch(row["policy_clause_ref"]):
            return _emit_fail(R31, f"matrix_rows[{idx}].policy_clause_ref fails grammar: {row['policy_clause_ref']!r}"), None
        if row["expected_scenario_type"] not in SCENARIO_TYPES:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_scenario_type not in closed set"), None
        if row["expected_decision_status"] not in DECISION_STATUSES:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_decision_status not in closed set"), None
        if row["expected_policy_decision"] not in POLICY_DECISIONS:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_policy_decision not in closed set"), None
        if row["expected_action_category"] not in ACTION_CATEGORIES:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_action_category not in closed set"), None
        if row["expected_action_environment"] not in ACTION_ENVIRONMENTS:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_action_environment not in closed set"), None
        if row["expected_decision_authority_role"] not in AUTHORITY_ROLES:
            return _emit_fail(R31, f"matrix_rows[{idx}].expected_decision_authority_role not in closed set"), None
        if row["required_subject_type"] not in SUBJECT_TYPES:
            return _emit_fail(R31, f"matrix_rows[{idx}].required_subject_type not in closed set"), None
        if row["evaluation_effect"] not in EVAL_EFFECTS:
            return _emit_fail(R31, f"matrix_rows[{idx}].evaluation_effect not in closed set"), None
        if row["row_rationale_code"] not in ROW_RATIONALES:
            return _emit_fail(R31, f"matrix_rows[{idx}].row_rationale_code not in closed set"), None

    # check_32 gold_policy_matrix_binding_invalid
    if matrix["package_id"] != manifest["package_id"]:
        return _emit_fail(R32, f"matrix package_id mismatch: matrix={matrix['package_id']!r}, manifest={manifest['package_id']!r}"), None
    if matrix["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R32, "matrix governed_reliance_demo_id mismatch with manifest"), None
    if matrix["matrix_id"] != manifest["matrix_id"]:
        return _emit_fail(R32, f"matrix matrix_id mismatch with manifest: matrix={matrix['matrix_id']!r}, manifest={manifest['matrix_id']!r}"), None
    # MUST NOT equal other manifest identifiers.
    for other in ("conformance_report_id", "decision_report_id", "policy_evaluation_report_id"):
        if matrix["matrix_id"] == manifest[other]:
            return _emit_fail(R32, f"matrix_id collides with manifest {other}: {matrix['matrix_id']!r}"), None
    if matrix["decision_report_ref"] != manifest["decision_report_id"]:
        return _emit_fail(R32, "matrix decision_report_ref mismatch with manifest decision_report_id"), None
    if matrix["decision_report_ref"] != decision_obj.get("decision_report_id"):
        return _emit_fail(R32, "matrix decision_report_ref mismatch with decision report decision_report_id"), None
    if matrix["decision_report_sha256"] != manifest["subjects"][2]["sha256"]:
        return _emit_fail(
            R32,
            f"matrix decision_report_sha256 mismatch with manifest subjects[2].sha256: "
            f"matrix={matrix['decision_report_sha256']!r}, manifest={manifest['subjects'][2]['sha256']!r}",
        ), None
    pkg_policy = (package_obj.get("inputs") or {}).get("policy_pack") or {}
    if matrix["policy_pack_id"] != pkg_policy.get("policy_pack_id"):
        return _emit_fail(R32, "matrix policy_pack_id mismatch with package body inputs.policy_pack.policy_pack_id"), None
    if matrix["policy_pack_version"] != pkg_policy.get("policy_pack_version"):
        return _emit_fail(R32, "matrix policy_pack_version mismatch with package body inputs.policy_pack.policy_pack_version"), None

    # check_33 gold_policy_matrix_entry_invalid
    seen_ids: set[str] = set()
    for idx, row in enumerate(matrix["matrix_rows"]):
        if row["matrix_row_id"] in seen_ids:
            return _emit_fail(R33, f"duplicate matrix_row_id at matrix_rows[{idx}]: {row['matrix_row_id']!r}"), None
        seen_ids.add(row["matrix_row_id"])
        expected_id = f"mrow_{idx + 1:02d}"
        if row["matrix_row_id"] != expected_id:
            return _emit_fail(R33, f"matrix_rows[{idx}].matrix_row_id must be {expected_id!r}, got {row['matrix_row_id']!r}"), None
        if (row["expected_scenario_type"], row["expected_decision_status"]) not in SCENARIO_STATUS_PAIRS:
            return _emit_fail(R33, f"matrix_rows[{idx}] (scenario_type, decision_status) not in allowed pairs"), None
        if (row["expected_scenario_type"], row["evaluation_effect"]) not in SCENARIO_EFFECT_PAIRS:
            return _emit_fail(R33, f"matrix_rows[{idx}] (scenario_type, evaluation_effect) not in allowed pairs"), None
        if (row["expected_scenario_type"], row["row_rationale_code"]) not in SCENARIO_RATIONALE_PAIRS:
            return _emit_fail(R33, f"matrix_rows[{idx}] (scenario_type, row_rationale_code) not in allowed pairs"), None

    return 0, matrix


# ---------------------------------------------------------------------------
# Phase 5: v0.4.2 evaluation report subject checks (R34..R38).
# ---------------------------------------------------------------------------

EVAL_REQUIRED_FIELDS = (
    "document_type", "schema_version", "profile",
    "package_id", "governed_reliance_demo_id",
    "matrix_id", "policy_evaluation_report_id", "generated_at",
    "source_decision_report_sha256", "source_matrix_sha256",
    "evaluation_rows", "coverage_summary",
    "scope_limitations", "non_claims",
)

EVAL_ROW_PROJECTION_KEYS = (
    "matrix_row_id", "decision_id", "decision_row_id",
    "scenario_type", "decision_status", "policy_clause_ref",
    "policy_decision", "action_category", "action_environment",
    "decision_authority_role", "subject_type",
    "evaluation_status", "evaluation_effect",
)


def _eval_fingerprint(row: dict[str, Any]) -> str:
    projection = {k: row.get(k) for k in EVAL_ROW_PROJECTION_KEYS}
    return _sha256_hex(_canonical_json_bytes(projection))


def _matrix_row_matches_decision_row(mrow: dict[str, Any], drow: dict[str, Any]) -> bool:
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


def _build_matched_row(idx: int, mr: dict[str, Any], drow: dict[str, Any], *, status: str) -> dict[str, Any]:
    pb = drow.get("policy_binding") or {}
    asc = drow.get("action_scope") or {}
    rb = drow.get("registry_binding") or {}
    ds = drow.get("decision_subject") or {}
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
        "evaluation_effect": mr.get("evaluation_effect"),
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
            distinct = {(m.get("evaluation_effect"), m.get("row_rationale_code")) for m in matches}
            mr = matches[0]
            if len(distinct) == 1:
                eval_rows.append(_build_matched_row(next_idx, mr, drow, status="matched"))
            else:
                eval_rows.append(_build_matched_row(next_idx, mr, drow, status="matrix_conflict_detected"))
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


def _derive_coverage_summary(
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


def _check_evaluation_report(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
    matrix: dict[str, Any],
    decision_obj: dict[str, Any],
) -> int:
    evaluation_path = manifest_dir / EVALUATION_SUBJECT_PATH
    try:
        raw = evaluation_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"evaluation report file unreadable: {e}")

    # check_34 gold_policy_evaluation_report_not_object
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R34, f"evaluation report is not valid JSON: {e}")
    if not isinstance(report, dict):
        return _emit_fail(R34, "evaluation report is not a JSON object")

    # check_35 gold_policy_evaluation_report_schema_invalid
    for f in EVAL_REQUIRED_FIELDS:
        if f not in report:
            return _emit_fail(R35, f"evaluation report missing required field {f!r}")
    if report.get("document_type") != EXPECTED_EVAL_DOC_TYPE:
        return _emit_fail(R35, f"document_type must be {EXPECTED_EVAL_DOC_TYPE!r}")
    if report.get("schema_version") != EXPECTED_EVAL_SCHEMA_VERSION:
        return _emit_fail(R35, f"schema_version must be {EXPECTED_EVAL_SCHEMA_VERSION!r}")
    if report.get("profile") != EXPECTED_EVAL_PROFILE:
        return _emit_fail(R35, f"profile must be {EXPECTED_EVAL_PROFILE!r}")
    for f in ("package_id", "governed_reliance_demo_id", "matrix_id",
              "policy_evaluation_report_id", "generated_at"):
        v = report.get(f)
        if not isinstance(v, str) or v == "":
            return _emit_fail(R35, f"{f} must be a non-empty string")
    for f in ("package_id", "governed_reliance_demo_id", "matrix_id", "policy_evaluation_report_id"):
        if not PACKAGE_ID_RE.fullmatch(report[f]):
            return _emit_fail(R35, f"{f} fails closed identifier grammar: {report[f]!r}")
    for f in ("source_decision_report_sha256", "source_matrix_sha256"):
        v = report.get(f)
        if not isinstance(v, str) or not BARE_HEX_SHA256_RE.fullmatch(v):
            return _emit_fail(R35, f"{f} must be bare lowercase hex SHA-256")
    if not isinstance(report.get("evaluation_rows"), list):
        return _emit_fail(R35, "evaluation_rows must be a JSON array")
    if not (1 <= len(report["evaluation_rows"]) <= 15):
        return _emit_fail(R35, f"evaluation_rows length must be 1..15, got {len(report['evaluation_rows'])}")
    if not isinstance(report.get("coverage_summary"), dict):
        return _emit_fail(R35, "coverage_summary must be a JSON object")
    for f in ("scope_limitations", "non_claims"):
        val = report.get(f)
        if not isinstance(val, list) or len(val) == 0:
            return _emit_fail(R35, f"{f} must be a non-empty array")
        for s in val:
            if not isinstance(s, str) or s.strip() == "":
                return _emit_fail(R35, f"{f} entries must be non-blank strings")

    # check_36 gold_policy_evaluation_report_binding_invalid
    if report["package_id"] != manifest["package_id"]:
        return _emit_fail(R36, "evaluation report package_id mismatch with manifest")
    if report["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R36, "evaluation report governed_reliance_demo_id mismatch with manifest")
    if report["matrix_id"] != manifest["matrix_id"]:
        return _emit_fail(R36, "evaluation report matrix_id mismatch with manifest")
    if report["matrix_id"] != matrix["matrix_id"]:
        return _emit_fail(R36, "evaluation report matrix_id mismatch with matrix")
    if report["policy_evaluation_report_id"] != manifest["policy_evaluation_report_id"]:
        return _emit_fail(R36, "evaluation report policy_evaluation_report_id mismatch with manifest")
    for other in ("decision_report_id", "conformance_report_id", "matrix_id"):
        if report["policy_evaluation_report_id"] == manifest[other]:
            return _emit_fail(R36, f"policy_evaluation_report_id collides with manifest {other}")
    if report["source_decision_report_sha256"] != manifest["subjects"][2]["sha256"]:
        return _emit_fail(R36, "evaluation report source_decision_report_sha256 mismatch with manifest subjects[2].sha256")
    if report["source_matrix_sha256"] != manifest["subjects"][3]["sha256"]:
        return _emit_fail(R36, "evaluation report source_matrix_sha256 mismatch with manifest subjects[3].sha256")

    # check_37 gold_policy_evaluation_result_invalid (per-row drift).
    expected_rows = _derive_evaluation_rows(matrix["matrix_rows"], decision_obj.get("decision_rows") or [])
    actual_rows = report["evaluation_rows"]
    if len(expected_rows) != len(actual_rows):
        return _emit_fail(
            R37,
            f"evaluation_rows length mismatch: report={len(actual_rows)}, "
            f"re-derived={len(expected_rows)}",
        )
    for idx, (exp, act) in enumerate(zip(expected_rows, actual_rows)):
        if _canonical_json_bytes(act) != _canonical_json_bytes(exp):
            return _emit_fail(
                R37,
                f"evaluation_rows[{idx}] mismatch: re-derived row does not match published row",
            )

    # check_38 gold_policy_evaluation_summary_invalid (coverage drift).
    expected_coverage = _derive_coverage_summary(expected_rows, matrix["matrix_rows"])
    if _canonical_json_bytes(expected_coverage) != _canonical_json_bytes(report["coverage_summary"]):
        return _emit_fail(
            R38,
            "coverage_summary mismatch: re-derived summary does not match published summary",
        )

    # Mirrored scope_limitations / non_claims drift folds back to R37
    # (projection drift between the matrix and the evaluation report).
    if report["scope_limitations"] != matrix["scope_limitations"]:
        return _emit_fail(R37, "evaluation report scope_limitations drifts from matrix")
    if report["non_claims"] != matrix["non_claims"]:
        return _emit_fail(R37, "evaluation report non_claims drifts from matrix")

    return 0


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Gold v0.4.2 Policy Evaluation Matrix package.",
    )
    parser.add_argument("--manifest", type=str, required=True,
                        help="Path to the v0.4.2 manifest gold-policy-evaluation-matrix-package-manifest.json.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent

    # Phase 1: v0.4.2 manifest integrity (R01 folds).
    rc, manifest = _check_manifest(manifest_path)
    if rc != 0 or manifest is None:
        return rc

    # Phase 2: inherited v0.4.1 (24+5) structural checks via subprocess.
    rc = _run_inherited_v041_checks(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 3: v0.4.2 cross-anchors (R01 folds).
    rc, package_obj, decision_obj = _check_cross_anchors(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0 or package_obj is None or decision_obj is None:
        return rc

    # Phase 4: matrix checks (R30..R33).
    rc, matrix = _check_matrix(
        manifest=manifest,
        manifest_dir=manifest_dir,
        package_obj=package_obj,
        decision_obj=decision_obj,
    )
    if rc != 0 or matrix is None:
        return rc

    # Phase 5: evaluation report checks (R34..R38).
    rc = _check_evaluation_report(
        manifest=manifest,
        manifest_dir=manifest_dir,
        matrix=matrix,
        decision_obj=decision_obj,
    )
    if rc != 0:
        return rc

    sys.stdout.write("PASS: gold v0.4.2 policy evaluation matrix package verified\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
