#!/usr/bin/env python3
"""Verify a ProofRail Gold v0.4.3 Challenge Lifecycle Lite package.

The v0.4.3 verifier extends the v0.4.2 Policy Evaluation Matrix
verifier with ten new ordered checks against the v0.4.3 challenge
lifecycle records body (subject [5]) and challenge lifecycle report
(subject [6]). The v0.4.3 verifier DELEGATES the inherited 38
v0.4.0/v0.4.1/v0.4.2 checks to the co-located v0.4.2 verifier
(`verify_gold_policy_evaluation_matrix_v0_1_0.py` under the same
`tools/gold/` directory) via subprocess against a synthesized
5-subject v0.4.2 manifest so the inherited 38 checks run without
duplication. A missing or unlaunchable v0.4.2 verifier is treated as
an ENVIRONMENT failure: it emits a non-reason-shaped `INFRA:`
diagnostic to stderr, exits with code 3, and MUST NOT collapse into
any of the 48 public verifier reason names or the 5 runner-only
refusal names.

Public failure reasons (closed set of 48, verbatim from the v0.4.3
spec, with 38 inherited from v0.4.2 and 10 introduced by v0.4.3):

  Inherited from v0.4.2 (relayed verbatim from the v0.4.2 verifier
  or emitted directly by v0.4.3 manifest-integrity / cross-anchor
  checks):

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
  30 gold_policy_matrix_not_object
  31 gold_policy_matrix_schema_invalid
  32 gold_policy_matrix_binding_invalid
  33 gold_policy_matrix_entry_invalid
  34 gold_policy_evaluation_report_not_object
  35 gold_policy_evaluation_report_schema_invalid
  36 gold_policy_evaluation_report_binding_invalid
  37 gold_policy_evaluation_result_invalid
  38 gold_policy_evaluation_summary_invalid

  Introduced by v0.4.3:

  39 gold_challenge_lifecycle_records_not_object
  40 gold_challenge_lifecycle_records_schema_invalid
  41 gold_challenge_lifecycle_records_binding_invalid
  42 gold_challenge_lifecycle_event_invalid
  43 gold_challenge_lifecycle_transition_invalid
  44 gold_challenge_lifecycle_report_not_object
  45 gold_challenge_lifecycle_report_schema_invalid
  46 gold_challenge_lifecycle_report_binding_invalid
  47 gold_challenge_lifecycle_projection_invalid
  48 gold_challenge_lifecycle_summary_invalid

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
# 48 approved verifier failure reasons (closed set, verbatim).
# ---------------------------------------------------------------------------

R01 = "gold_manifest_invalid"
R39 = "gold_challenge_lifecycle_records_not_object"
R40 = "gold_challenge_lifecycle_records_schema_invalid"
R41 = "gold_challenge_lifecycle_records_binding_invalid"
R42 = "gold_challenge_lifecycle_event_invalid"
R43 = "gold_challenge_lifecycle_transition_invalid"
R44 = "gold_challenge_lifecycle_report_not_object"
R45 = "gold_challenge_lifecycle_report_schema_invalid"
R46 = "gold_challenge_lifecycle_report_binding_invalid"
R47 = "gold_challenge_lifecycle_projection_invalid"
R48 = "gold_challenge_lifecycle_summary_invalid"

# Closed runner-only refusal set; the verifier never emits these.
RUNNER_ONLY_REFUSALS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

# ---------------------------------------------------------------------------
# Closed constants for v0.4.3 manifest, records body, lifecycle report.
# ---------------------------------------------------------------------------

EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.challenge_lifecycle_package_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_RELEASE = "gold.challenge_lifecycle_lite.v0.4.3"
EXPECTED_HASH_ALGO = "sha256"

EXPECTED_RECORDS_DOC_TYPE = "proofrail.gold.challenge_lifecycle_records"
EXPECTED_RECORDS_SCHEMA_VERSION = "v0.1.0"
EXPECTED_RECORDS_PROFILE = "gold.challenge_lifecycle_lite.v0.4.3"

EXPECTED_REPORT_DOC_TYPE = "proofrail.gold.challenge_lifecycle_report"
EXPECTED_REPORT_SCHEMA_VERSION = "v0.1.0"
EXPECTED_REPORT_PROFILE = "gold.challenge_lifecycle_lite.v0.4.3"

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"
MATRIX_SUBJECT_PATH = "gold-policy-evaluation-matrix.json"
EVALUATION_SUBJECT_PATH = "gold-policy-evaluation-report.json"
RECORDS_SUBJECT_PATH = "challenge-lifecycle-records.json"
LIFECYCLE_REPORT_SUBJECT_PATH = "gold-challenge-lifecycle-report.json"

EXPECTED_SUBJECT_PATHS = (
    PACKAGE_SUBJECT_PATH,
    CONFORMANCE_SUBJECT_PATH,
    DECISION_SUBJECT_PATH,
    MATRIX_SUBJECT_PATH,
    EVALUATION_SUBJECT_PATH,
    RECORDS_SUBJECT_PATH,
    LIFECYCLE_REPORT_SUBJECT_PATH,
)
EXPECTED_SUBJECT_ROLES = (
    "governed_reliance_package",
    "conformance_report",
    "decision_report",
    "policy_evaluation_matrix",
    "policy_evaluation_report",
    "challenge_lifecycle_records",
    "challenge_lifecycle_report",
)

PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
ROW_ID_RE = re.compile(r"^row_[0-9]{2}$")
LC_ROW_ID_RE = re.compile(r"^lc_row_[0-9]{2}$")
ISO_8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BARE_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Closed lifecycle vocabulary.
LIFECYCLE_STATUSES = ("filed", "acknowledged", "under_review",
                      "resolved_locally", "superseded", "withdrawn")
LIFECYCLE_STATUSES_SET = frozenset(LIFECYCLE_STATUSES)
TERMINAL_STATUSES = frozenset({"resolved_locally", "superseded", "withdrawn"})
EVENT_BASES = frozenset({
    "challenge_record", "acknowledgement_record", "review_update",
    "local_resolution_record", "supersession_record", "withdrawal_record",
})
ACTOR_ROLES = frozenset({
    "relying_party", "policy_authority", "reviewer", "system_recorder",
})
LIFECYCLE_EFFECTS = frozenset({
    "challenge_open", "local_resolution_recorded",
    "challenge_withdrawn", "challenge_superseded",
})

# Closed (event_status, event_basis) pair table.
STATUS_BASIS_PAIRS = frozenset({
    ("filed", "challenge_record"),
    ("acknowledged", "acknowledgement_record"),
    ("under_review", "review_update"),
    ("resolved_locally", "local_resolution_record"),
    ("superseded", "supersession_record"),
    ("withdrawn", "withdrawal_record"),
})

# Closed (event_status, lifecycle_effect) pair table (only the four
# statuses that carry an effect). `acknowledged` and `under_review`
# events MUST NOT carry a lifecycle_effect.
STATUS_EFFECT_PAIRS = frozenset({
    ("filed", "challenge_open"),
    ("resolved_locally", "local_resolution_recorded"),
    ("withdrawn", "challenge_withdrawn"),
    ("superseded", "challenge_superseded"),
})

# Closed transition graph (9 directed edges over the six statuses).
LIFECYCLE_TRANSITIONS = frozenset({
    ("filed", "acknowledged"),
    ("filed", "withdrawn"),
    ("filed", "superseded"),
    ("acknowledged", "under_review"),
    ("acknowledged", "withdrawn"),
    ("acknowledged", "superseded"),
    ("under_review", "resolved_locally"),
    ("under_review", "withdrawn"),
    ("under_review", "superseded"),
})

# Module constant exposing the v0.4.2 verifier path (subprocess-invoked).
GOLD_V042_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_policy_evaluation_matrix_v0_1_0.py"
)

# v0.4.2 manifest filename used for the synthesized inherited manifest.
INHERITED_V042_MANIFEST_FILENAME = "gold-policy-evaluation-matrix-package-manifest.json"


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
# Phase 1: v0.4.3 manifest structural integrity. All folds emit R01.
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

    string_fields = (
        "manifest_id",
        "conformance_report_id",
        "decision_report_id",
        "matrix_id",
        "policy_evaluation_report_id",
        "challenge_lifecycle_record_set_id",
        "challenge_lifecycle_report_id",
        "package_id",
        "governed_reliance_demo_id",
        "generated_at",
    )
    for field in string_fields:
        val = manifest.get(field)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R01, f"{field} must be a non-empty string"), None

    grammar_fields = (
        "manifest_id",
        "conformance_report_id",
        "decision_report_id",
        "matrix_id",
        "policy_evaluation_report_id",
        "challenge_lifecycle_record_set_id",
        "challenge_lifecycle_report_id",
        "package_id",
        "governed_reliance_demo_id",
    )
    for field in grammar_fields:
        if not PACKAGE_ID_RE.fullmatch(manifest[field]):
            return _emit_fail(R01, f"{field} fails closed identifier grammar: {manifest[field]!r}"), None

    if not ISO_8601_UTC_RE.fullmatch(manifest["generated_at"]):
        return _emit_fail(R01, f"generated_at must be ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ, got {manifest['generated_at']!r}"), None

    # Pairwise distinctness across the six collision-class identifiers.
    # `manifest_id`, `package_id`, and `governed_reliance_demo_id` are
    # explicitly excluded from the collision class per the v0.4.3
    # manifest schema.
    six = (
        ("conformance_report_id", manifest["conformance_report_id"]),
        ("decision_report_id", manifest["decision_report_id"]),
        ("matrix_id", manifest["matrix_id"]),
        ("policy_evaluation_report_id", manifest["policy_evaluation_report_id"]),
        ("challenge_lifecycle_record_set_id", manifest["challenge_lifecycle_record_set_id"]),
        ("challenge_lifecycle_report_id", manifest["challenge_lifecycle_report_id"]),
    )
    seen: dict[str, str] = {}
    for name, val in six:
        if val in seen:
            return _emit_fail(
                R01,
                f"{name} and {seen[val]} must be distinct (both equal {val!r})",
            ), None
        seen[val] = name

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return _emit_fail(R01, "subjects must be a JSON array"), None
    if len(subjects) != 7:
        return _emit_fail(R01, f"subjects must hold exactly 7 entries, got {len(subjects)}"), None

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

    # File-on-disk checks for all seven subjects.
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
# Phase 2: subprocess-invoke the unchanged v0.4.2 verifier on a synthesized
# 5-subject v0.4.2 manifest. Inherited 38 reasons are relayed verbatim.
# A missing or crashing v0.4.2 verifier emits an INFRA: diagnostic and
# exits with code 3.
# ---------------------------------------------------------------------------

def _run_inherited_v042_checks(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    package_subj = manifest["subjects"][0]
    conformance_subj = manifest["subjects"][1]
    decision_subj = manifest["subjects"][2]
    matrix_subj = manifest["subjects"][3]
    evaluation_subj = manifest["subjects"][4]
    for subj in (package_subj, conformance_subj, decision_subj, matrix_subj, evaluation_subj):
        if not (manifest_dir / subj["path"]).exists():
            return _emit_fail(R01, "subject file missing prior to inherited v0.4.2 verification")

    v042_manifest = {
        "document_type": "proofrail.gold.policy_evaluation_matrix_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.policy_evaluation_matrix.v0.4.2",
        "hash_algorithm": "sha256",
        "manifest_id": manifest["manifest_id"],
        "conformance_report_id": manifest["conformance_report_id"],
        "decision_report_id": manifest["decision_report_id"],
        "matrix_id": manifest["matrix_id"],
        "policy_evaluation_report_id": manifest["policy_evaluation_report_id"],
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
            {
                "role": "policy_evaluation_matrix",
                "path": MATRIX_SUBJECT_PATH,
                "sha256": matrix_subj["sha256"],
                "size_bytes": matrix_subj["size_bytes"],
            },
            {
                "role": "policy_evaluation_report",
                "path": EVALUATION_SUBJECT_PATH,
                "sha256": evaluation_subj["sha256"],
                "size_bytes": evaluation_subj["size_bytes"],
            },
        ],
    }

    with tempfile.TemporaryDirectory(prefix="v043_inherited_") as td:
        td_path = Path(td)
        for sub_name in (PACKAGE_SUBJECT_PATH, CONFORMANCE_SUBJECT_PATH,
                         DECISION_SUBJECT_PATH, MATRIX_SUBJECT_PATH,
                         EVALUATION_SUBJECT_PATH):
            shutil.copyfile(manifest_dir / sub_name, td_path / sub_name)
        synthesized = td_path / INHERITED_V042_MANIFEST_FILENAME
        synthesized.write_bytes(_canonical_json_bytes(v042_manifest))

        if not GOLD_V042_VERIFIER.exists():
            sys.stderr.write(
                "INFRA: co-located v0.4.2 verifier unavailable for inherited "
                f"check delegation: expected at {GOLD_V042_VERIFIER}\n"
            )
            return 3
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(GOLD_V042_VERIFIER),
                    "--manifest",
                    str(synthesized),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            sys.stderr.write(
                "INFRA: co-located v0.4.2 verifier unavailable for inherited "
                f"check delegation: {type(e).__name__}: {e}\n"
            )
            return 3
        if result.returncode != 0:
            if result.stdout:
                sys.stdout.buffer.write(result.stdout)
            if result.stderr:
                sys.stderr.buffer.write(result.stderr)
            # An infra-style failure from the delegated v0.4.2 verifier
            # (its own exit code 3 for INFRA, or any non-1 non-zero) must
            # NOT collapse into a public reason here either.
            if result.returncode != 1:
                return 3
            return result.returncode
    return 0


# ---------------------------------------------------------------------------
# Phase 3: v0.4.3 cross-anchor checks (R01 folds).
# ---------------------------------------------------------------------------

def _check_cross_anchors(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Validate v0.4.3 cross-anchors between the manifest and inherited subjects.

    Returns (rc, package_obj, decision_obj, evaluation_obj). The inherited
    subjects' structural conformance is guaranteed by Phase 2; here we only
    cross-anchor identifiers and SHA-256 values into the v0.4.3 manifest.
    """
    package_path = manifest_dir / PACKAGE_SUBJECT_PATH
    decision_path = manifest_dir / DECISION_SUBJECT_PATH
    evaluation_path = manifest_dir / EVALUATION_SUBJECT_PATH
    try:
        package_obj = json.loads(package_path.read_bytes().decode("utf-8"))
        decision_obj = json.loads(decision_path.read_bytes().decode("utf-8"))
        evaluation_obj = json.loads(evaluation_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"inherited subject unreadable for cross-anchor check: {e}"), None, None, None
    if not isinstance(package_obj, dict) or not isinstance(decision_obj, dict) \
            or not isinstance(evaluation_obj, dict):
        return _emit_fail(R01, "inherited subject is not an object for cross-anchor check"), None, None, None

    if package_obj.get("package_id") != manifest["package_id"]:
        return _emit_fail(R01, "package_id cross-anchor mismatch with package body"), None, None, None
    if package_obj.get("governed_reliance_demo_id") != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R01, "governed_reliance_demo_id cross-anchor mismatch with package body"), None, None, None
    if decision_obj.get("decision_report_id") != manifest["decision_report_id"]:
        return _emit_fail(R01, "decision_report_id cross-anchor mismatch with decision report"), None, None, None
    if evaluation_obj.get("policy_evaluation_report_id") != manifest["policy_evaluation_report_id"]:
        return _emit_fail(R01, "policy_evaluation_report_id cross-anchor mismatch with evaluation report"), None, None, None
    if evaluation_obj.get("matrix_id") != manifest["matrix_id"]:
        return _emit_fail(R01, "matrix_id cross-anchor mismatch with evaluation report"), None, None, None

    return 0, package_obj, decision_obj, evaluation_obj


# ---------------------------------------------------------------------------
# Phase 4: v0.4.3 records body checks (R39..R43).
# ---------------------------------------------------------------------------

RECORDS_REQUIRED_FIELDS = (
    "document_type", "schema_version", "profile",
    "lifecycle_record_set_id", "package_id", "governed_reliance_demo_id",
    "policy_evaluation_report_ref", "policy_evaluation_report_sha256",
    "generated_at", "lifecycle_records",
)

RECORD_REQUIRED_FIELDS = (
    "lifecycle_id", "target_decision_id", "target_decision_row_id",
    "current_status", "events", "lifecycle_fingerprint",
)

EVENT_REQUIRED_FIELDS = (
    "event_id", "event_status", "event_basis", "actor_role",
    "event_timestamp", "event_basis_ref",
)


def _check_records_body(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
    decision_obj: dict[str, Any],
    evaluation_obj: dict[str, Any],
    package_obj: dict[str, Any],
) -> tuple[int, dict[str, Any] | None]:
    records_path = manifest_dir / RECORDS_SUBJECT_PATH
    try:
        raw = records_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"records body unreadable: {e}"), None

    # R39 not_object
    try:
        records_body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R39, f"records body is not valid JSON: {e}"), None
    if not isinstance(records_body, dict):
        return _emit_fail(R39, "records body is not a JSON object"), None

    # R40 gold_challenge_lifecycle_records_schema_invalid
    for f in RECORDS_REQUIRED_FIELDS:
        if f not in records_body:
            return _emit_fail(R40, f"records body missing required field {f!r}"), None
    if records_body.get("document_type") != EXPECTED_RECORDS_DOC_TYPE:
        return _emit_fail(R40, f"document_type must be {EXPECTED_RECORDS_DOC_TYPE!r}"), None
    if records_body.get("schema_version") != EXPECTED_RECORDS_SCHEMA_VERSION:
        return _emit_fail(R40, f"schema_version must be {EXPECTED_RECORDS_SCHEMA_VERSION!r}"), None
    if records_body.get("profile") != EXPECTED_RECORDS_PROFILE:
        return _emit_fail(R40, f"profile must be {EXPECTED_RECORDS_PROFILE!r}"), None
    for f in ("lifecycle_record_set_id", "package_id", "governed_reliance_demo_id",
              "policy_evaluation_report_ref", "generated_at"):
        v = records_body.get(f)
        if not isinstance(v, str) or v == "":
            return _emit_fail(R40, f"{f} must be a non-empty string"), None
    for f in ("lifecycle_record_set_id", "package_id", "governed_reliance_demo_id",
              "policy_evaluation_report_ref"):
        if not PACKAGE_ID_RE.fullmatch(records_body[f]):
            return _emit_fail(R40, f"{f} fails closed identifier grammar: {records_body[f]!r}"), None
    if not ISO_8601_UTC_RE.fullmatch(records_body["generated_at"]):
        return _emit_fail(R40, f"generated_at must be ISO-8601 UTC, got {records_body['generated_at']!r}"), None
    sha = records_body.get("policy_evaluation_report_sha256")
    if not isinstance(sha, str) or not BARE_HEX_SHA256_RE.fullmatch(sha):
        return _emit_fail(R40, "policy_evaluation_report_sha256 must be bare lowercase hex SHA-256"), None
    if not isinstance(records_body.get("lifecycle_records"), list):
        return _emit_fail(R40, "lifecycle_records must be a JSON array"), None
    if len(records_body["lifecycle_records"]) == 0:
        return _emit_fail(R40, "lifecycle_records must be non-empty"), None

    for idx, record in enumerate(records_body["lifecycle_records"]):
        if not isinstance(record, dict):
            return _emit_fail(R40, f"lifecycle_records[{idx}] is not an object"), None
        for f in RECORD_REQUIRED_FIELDS:
            if f not in record:
                return _emit_fail(R40, f"lifecycle_records[{idx}] missing required field {f!r}"), None
        for f in ("lifecycle_id", "target_decision_id", "target_decision_row_id",
                  "current_status", "lifecycle_fingerprint"):
            v = record.get(f)
            if not isinstance(v, str) or v == "":
                return _emit_fail(R40, f"lifecycle_records[{idx}].{f} must be a non-empty string"), None
        for f in ("lifecycle_id", "target_decision_id"):
            if not PACKAGE_ID_RE.fullmatch(record[f]):
                return _emit_fail(R40, f"lifecycle_records[{idx}].{f} fails closed identifier grammar: {record[f]!r}"), None
        if not ROW_ID_RE.fullmatch(record["target_decision_row_id"]):
            return _emit_fail(R40, f"lifecycle_records[{idx}].target_decision_row_id fails grammar: {record['target_decision_row_id']!r}"), None
        if record["current_status"] not in LIFECYCLE_STATUSES_SET:
            return _emit_fail(R40, f"lifecycle_records[{idx}].current_status not in closed set: {record['current_status']!r}"), None
        if not BARE_HEX_SHA256_RE.fullmatch(record["lifecycle_fingerprint"]):
            return _emit_fail(R40, f"lifecycle_records[{idx}].lifecycle_fingerprint must be bare lowercase hex SHA-256"), None
        events = record.get("events")
        if not isinstance(events, list) or len(events) == 0:
            return _emit_fail(R40, f"lifecycle_records[{idx}].events must be a non-empty array"), None

    # R41 gold_challenge_lifecycle_records_binding_invalid
    if records_body["package_id"] != manifest["package_id"]:
        return _emit_fail(R41, "records body package_id mismatch with manifest"), None
    if records_body["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R41, "records body governed_reliance_demo_id mismatch with manifest"), None
    if records_body["lifecycle_record_set_id"] != manifest["challenge_lifecycle_record_set_id"]:
        return _emit_fail(
            R41,
            f"records body lifecycle_record_set_id={records_body['lifecycle_record_set_id']!r} "
            f"mismatch with manifest challenge_lifecycle_record_set_id={manifest['challenge_lifecycle_record_set_id']!r}",
        ), None
    if records_body["policy_evaluation_report_ref"] != manifest["policy_evaluation_report_id"]:
        return _emit_fail(R41, "records body policy_evaluation_report_ref mismatch with manifest policy_evaluation_report_id"), None
    if records_body["policy_evaluation_report_sha256"] != manifest["subjects"][4]["sha256"]:
        return _emit_fail(R41, "records body policy_evaluation_report_sha256 mismatch with manifest subjects[4].sha256"), None

    # 6-ID collision class involving lifecycle_record_set_id at the
    # records-body level: lifecycle_record_set_id MUST NOT collide with
    # any of the five other collision-class IDs.
    for other in ("conformance_report_id", "decision_report_id", "matrix_id",
                  "policy_evaluation_report_id", "challenge_lifecycle_report_id"):
        if manifest["challenge_lifecycle_record_set_id"] == manifest[other]:
            return _emit_fail(
                R41,
                f"challenge_lifecycle_record_set_id collides with manifest {other}: "
                f"{manifest['challenge_lifecycle_record_set_id']!r}",
            ), None

    # target_decision_id / target_decision_row_id binding to v0.4.1
    # decision report (and transitively to the v0.4.0 body).
    decision_rows = decision_obj.get("decision_rows") or []
    decision_index: dict[str, dict[str, Any]] = {}
    for drow in decision_rows:
        if isinstance(drow, dict) and isinstance(drow.get("decision_id"), str):
            decision_index[drow["decision_id"]] = drow
    governed_index: dict[str, dict[str, Any]] = {}
    for entry in package_obj.get("governed_decisions") or []:
        if isinstance(entry, dict) and isinstance(entry.get("decision_id"), str):
            governed_index[entry["decision_id"]] = entry

    seen_targets: dict[str, int] = {}
    for idx, record in enumerate(records_body["lifecycle_records"]):
        tdid = record["target_decision_id"]
        if tdid in seen_targets:
            return _emit_fail(
                R41,
                f"duplicate target_decision_id at lifecycle_records[{idx}]: {tdid!r} "
                f"already used by lifecycle_records[{seen_targets[tdid]}]",
            ), None
        seen_targets[tdid] = idx
        if tdid not in decision_index:
            return _emit_fail(
                R41,
                f"lifecycle_records[{idx}].target_decision_id {tdid!r} does not appear in v0.4.1 decision report",
            ), None
        drow = decision_index[tdid]
        if drow.get("row_id") != record["target_decision_row_id"]:
            return _emit_fail(
                R41,
                f"lifecycle_records[{idx}] target_decision_row_id={record['target_decision_row_id']!r} "
                f"does not match decision report row_id={drow.get('row_id')!r} for decision_id {tdid!r}",
            ), None
        # superseding_decision_id, when present, must reference a
        # distinct governed decision present in the v0.4.0 body.
        if record["current_status"] == "superseded":
            superseding = record.get("superseding_decision_id")
            if isinstance(superseding, str):
                if superseding == tdid:
                    return _emit_fail(
                        R41,
                        f"lifecycle_records[{idx}].superseding_decision_id must be distinct from target_decision_id",
                    ), None
                if superseding not in governed_index:
                    return _emit_fail(
                        R41,
                        f"lifecycle_records[{idx}].superseding_decision_id {superseding!r} not present in v0.4.0 body",
                    ), None

    # R42 gold_challenge_lifecycle_event_invalid: per-event validity +
    # conditional terminal refs + status/basis and status/effect pair tables.
    for idx, record in enumerate(records_body["lifecycle_records"]):
        events = record["events"]
        seen_ev_ids: set[str] = set()
        for j, ev in enumerate(events):
            if not isinstance(ev, dict):
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}] is not an object"), None
            for f in EVENT_REQUIRED_FIELDS:
                if f not in ev:
                    return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}] missing required field {f!r}"), None
            for f in ("event_id", "event_status", "event_basis", "actor_role",
                      "event_timestamp", "event_basis_ref"):
                v = ev.get(f)
                if not isinstance(v, str) or v == "":
                    return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].{f} must be a non-empty string"), None
            if not PACKAGE_ID_RE.fullmatch(ev["event_id"]):
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_id fails closed grammar: {ev['event_id']!r}"), None
            if ev["event_id"] in seen_ev_ids:
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_id {ev['event_id']!r} duplicates earlier event in same record"), None
            seen_ev_ids.add(ev["event_id"])
            if ev["event_status"] not in LIFECYCLE_STATUSES_SET:
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_status not in closed set: {ev['event_status']!r}"), None
            if ev["event_basis"] not in EVENT_BASES:
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_basis not in closed set: {ev['event_basis']!r}"), None
            if ev["actor_role"] not in ACTOR_ROLES:
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].actor_role not in closed set: {ev['actor_role']!r}"), None
            if not ISO_8601_UTC_RE.fullmatch(ev["event_timestamp"]):
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_timestamp must be ISO-8601 UTC: {ev['event_timestamp']!r}"), None
            if not PACKAGE_ID_RE.fullmatch(ev["event_basis_ref"]):
                return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].event_basis_ref fails closed grammar: {ev['event_basis_ref']!r}"), None
            if (ev["event_status"], ev["event_basis"]) not in STATUS_BASIS_PAIRS:
                return _emit_fail(
                    R42,
                    f"lifecycle_records[{idx}].events[{j}] (event_status, event_basis) "
                    f"=({ev['event_status']!r}, {ev['event_basis']!r}) not in closed pair table",
                ), None
            if "lifecycle_effect" in ev:
                effect = ev["lifecycle_effect"]
                if not isinstance(effect, str) or effect not in LIFECYCLE_EFFECTS:
                    return _emit_fail(R42, f"lifecycle_records[{idx}].events[{j}].lifecycle_effect not in closed set: {effect!r}"), None
                if ev["event_status"] in ("acknowledged", "under_review"):
                    return _emit_fail(
                        R42,
                        f"lifecycle_records[{idx}].events[{j}].lifecycle_effect must NOT appear on "
                        f"{ev['event_status']!r} events",
                    ), None
                if (ev["event_status"], effect) not in STATUS_EFFECT_PAIRS:
                    return _emit_fail(
                        R42,
                        f"lifecycle_records[{idx}].events[{j}] (event_status, lifecycle_effect) "
                        f"=({ev['event_status']!r}, {effect!r}) not in closed pair table",
                    ), None
            else:
                # filed events must carry lifecycle_effect = challenge_open.
                # Terminal events must carry the matching lifecycle_effect.
                if ev["event_status"] in ("filed", "resolved_locally", "withdrawn", "superseded"):
                    return _emit_fail(
                        R42,
                        f"lifecycle_records[{idx}].events[{j}] event_status {ev['event_status']!r} "
                        f"requires a matching lifecycle_effect",
                    ), None

        # Conditional terminal-status refs at the record level.
        cs = record["current_status"]
        if cs == "resolved_locally":
            ref = record.get("local_resolution_ref")
            if not isinstance(ref, str) or not PACKAGE_ID_RE.fullmatch(ref):
                return _emit_fail(
                    R42,
                    f"lifecycle_records[{idx}].local_resolution_ref is required when current_status=resolved_locally",
                ), None
        elif cs == "withdrawn":
            ref = record.get("withdrawal_record_ref")
            if not isinstance(ref, str) or not PACKAGE_ID_RE.fullmatch(ref):
                return _emit_fail(
                    R42,
                    f"lifecycle_records[{idx}].withdrawal_record_ref is required when current_status=withdrawn",
                ), None
        elif cs == "superseded":
            ref = record.get("superseding_decision_id")
            if not isinstance(ref, str) or not PACKAGE_ID_RE.fullmatch(ref):
                return _emit_fail(
                    R42,
                    f"lifecycle_records[{idx}].superseding_decision_id is required when current_status=superseded",
                ), None

    # R43 gold_challenge_lifecycle_transition_invalid: first event = filed;
    # monotonic timestamps; no event after terminal; current_status equals
    # final event status;
    # all consecutive (prev,next) status pairs in the closed transition
    # graph.
    for idx, record in enumerate(records_body["lifecycle_records"]):
        events = record["events"]
        first = events[0]
        if first["event_status"] != "filed":
            return _emit_fail(
                R43,
                f"lifecycle_records[{idx}].events[0].event_status must be 'filed', got {first['event_status']!r}",
            ), None
        prev_ts = None
        for j, ev in enumerate(events):
            ts = ev["event_timestamp"]
            if prev_ts is not None and ts < prev_ts:
                return _emit_fail(
                    R43,
                    f"lifecycle_records[{idx}].events[{j}].event_timestamp {ts!r} "
                    f"is earlier than previous event timestamp {prev_ts!r}",
                ), None
            prev_ts = ts
            if j < len(events) - 1 and ev["event_status"] in TERMINAL_STATUSES:
                return _emit_fail(
                    R43,
                    f"lifecycle_records[{idx}].events[{j}] is terminal "
                    f"({ev['event_status']!r}); no further events permitted",
                ), None
            if j > 0:
                prev_status = events[j - 1]["event_status"]
                if (prev_status, ev["event_status"]) not in LIFECYCLE_TRANSITIONS:
                    return _emit_fail(
                        R43,
                        f"lifecycle_records[{idx}].events[{j}] transition "
                        f"{prev_status!r} -> {ev['event_status']!r} not in closed transition graph",
                    ), None
        final_status = events[-1]["event_status"]
        if final_status != record["current_status"]:
            return _emit_fail(
                R43,
                f"lifecycle_records[{idx}].current_status={record['current_status']!r} "
                f"does not equal final event_status={final_status!r}",
            ), None

    # R41 gold_challenge_lifecycle_records_binding_invalid (post-event):
    # per-record lifecycle_fingerprint equality. Recompute SHA-256 of the
    # canonical JSON serialization of the record with the lifecycle_fingerprint
    # field removed and compare to the declared lifecycle_fingerprint. This
    # check is intentionally placed after the R43 transition block as a
    # deliberate non-masking post-event R41 check: invalid event shapes,
    # event grammar, and transition orderings must be reachable under R42
    # and R43 before a fingerprint mismatch can fire. The numeric ordering
    # of emitted reasons is not literal here; R41 is reached after R43 by
    # design and the records-shape R40 hex-shape check above only constrains
    # the declared bytes' format, not their byte-equality to the canonical
    # re-derivation. The recomputation is byte-identical to the runner's
    # per-record fingerprint derivation.
    for idx, record in enumerate(records_body["lifecycle_records"]):
        record_for_fp = {k: v for k, v in record.items() if k != "lifecycle_fingerprint"}
        expected_fp = _sha256_hex(_canonical_json_bytes(record_for_fp))
        if record["lifecycle_fingerprint"] != expected_fp:
            return _emit_fail(
                R41,
                f"lifecycle_records[{idx}].lifecycle_fingerprint mismatch: "
                f"declared={record['lifecycle_fingerprint']!r}, re-derived={expected_fp!r}",
            ), None

    return 0, records_body


# ---------------------------------------------------------------------------
# Phase 5: v0.4.3 lifecycle report checks (R44..R48).
# ---------------------------------------------------------------------------

REPORT_REQUIRED_FIELDS = (
    "document_type", "schema_version", "profile",
    "challenge_lifecycle_report_id", "lifecycle_record_set_id",
    "package_id", "governed_reliance_demo_id",
    "policy_evaluation_report_id",
    "source_records_sha256", "source_policy_evaluation_report_sha256",
    "source_decision_report_sha256",
    "generated_at", "lifecycle_rows", "coverage_summary",
    "report_fingerprint",
)

ROW_REQUIRED_FIELDS = (
    "row_id", "lifecycle_id", "target_decision_id", "target_decision_row_id",
    "current_status", "is_terminal", "event_count",
    "first_event_id", "final_event_id", "final_event_timestamp",
    "lifecycle_fingerprint",
)

COVERAGE_SUMMARY_FIELDS = (
    "lifecycle_record_count", "lifecycle_event_count",
    "open_lifecycle_count", "terminal_lifecycle_count",
    "status_value_count",
)


def _project_lifecycle_row(idx: int, record: dict[str, Any]) -> dict[str, Any]:
    events = record.get("events") if isinstance(record.get("events"), list) else []
    event_count = len(events)
    first_event_id = events[0].get("event_id") if event_count > 0 and isinstance(events[0], dict) else None
    final_event_id = events[-1].get("event_id") if event_count > 0 and isinstance(events[-1], dict) else None
    final_event_ts = events[-1].get("event_timestamp") if event_count > 0 and isinstance(events[-1], dict) else None
    current_status = record.get("current_status")
    is_terminal = current_status in TERMINAL_STATUSES
    return {
        "row_id": f"lc_row_{idx + 1:02d}",
        "lifecycle_id": record.get("lifecycle_id"),
        "target_decision_id": record.get("target_decision_id"),
        "target_decision_row_id": record.get("target_decision_row_id"),
        "current_status": current_status,
        "is_terminal": is_terminal,
        "event_count": event_count,
        "first_event_id": first_event_id,
        "final_event_id": final_event_id,
        "final_event_timestamp": final_event_ts,
        "lifecycle_fingerprint": record.get("lifecycle_fingerprint"),
    }


def _rederive_coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    open_count = 0
    terminal_count = 0
    event_total = 0
    status_count = {s: 0 for s in LIFECYCLE_STATUSES}
    for r in rows:
        ec = r.get("event_count")
        if isinstance(ec, int):
            event_total += ec
        st = r.get("current_status")
        if isinstance(st, str) and st in status_count:
            status_count[st] += 1
        if r.get("is_terminal") is True:
            terminal_count += 1
        else:
            open_count += 1
    return {
        "lifecycle_record_count": len(rows),
        "lifecycle_event_count": event_total,
        "open_lifecycle_count": open_count,
        "terminal_lifecycle_count": terminal_count,
        "status_value_count": status_count,
    }


def _check_lifecycle_report(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
    records_body: dict[str, Any],
) -> int:
    report_path = manifest_dir / LIFECYCLE_REPORT_SUBJECT_PATH
    try:
        raw = report_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"lifecycle report unreadable: {e}")

    # R44 not_object
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R44, f"lifecycle report is not valid JSON: {e}")
    if not isinstance(report, dict):
        return _emit_fail(R44, "lifecycle report is not a JSON object")

    # R45 gold_challenge_lifecycle_report_schema_invalid
    for f in REPORT_REQUIRED_FIELDS:
        if f not in report:
            return _emit_fail(R45, f"lifecycle report missing required field {f!r}")
    if report.get("document_type") != EXPECTED_REPORT_DOC_TYPE:
        return _emit_fail(R45, f"document_type must be {EXPECTED_REPORT_DOC_TYPE!r}")
    if report.get("schema_version") != EXPECTED_REPORT_SCHEMA_VERSION:
        return _emit_fail(R45, f"schema_version must be {EXPECTED_REPORT_SCHEMA_VERSION!r}")
    if report.get("profile") != EXPECTED_REPORT_PROFILE:
        return _emit_fail(R45, f"profile must be {EXPECTED_REPORT_PROFILE!r}")
    for f in ("challenge_lifecycle_report_id", "lifecycle_record_set_id",
              "package_id", "governed_reliance_demo_id",
              "policy_evaluation_report_id", "generated_at"):
        v = report.get(f)
        if not isinstance(v, str) or v == "":
            return _emit_fail(R45, f"{f} must be a non-empty string")
    for f in ("challenge_lifecycle_report_id", "lifecycle_record_set_id",
              "package_id", "governed_reliance_demo_id",
              "policy_evaluation_report_id"):
        if not PACKAGE_ID_RE.fullmatch(report[f]):
            return _emit_fail(R45, f"{f} fails closed identifier grammar: {report[f]!r}")
    if not ISO_8601_UTC_RE.fullmatch(report["generated_at"]):
        return _emit_fail(R45, f"generated_at must be ISO-8601 UTC, got {report['generated_at']!r}")
    for f in ("source_records_sha256", "source_policy_evaluation_report_sha256",
              "source_decision_report_sha256", "report_fingerprint"):
        v = report.get(f)
        if not isinstance(v, str) or not BARE_HEX_SHA256_RE.fullmatch(v):
            return _emit_fail(R45, f"{f} must be bare lowercase hex SHA-256")
    if not isinstance(report.get("lifecycle_rows"), list):
        return _emit_fail(R45, "lifecycle_rows must be a JSON array")
    if not isinstance(report.get("coverage_summary"), dict):
        return _emit_fail(R45, "coverage_summary must be a JSON object")
    for idx, row in enumerate(report["lifecycle_rows"]):
        if not isinstance(row, dict):
            return _emit_fail(R45, f"lifecycle_rows[{idx}] is not an object")
        for f in ROW_REQUIRED_FIELDS:
            if f not in row:
                return _emit_fail(R45, f"lifecycle_rows[{idx}] missing required field {f!r}")
        if not isinstance(row["row_id"], str) or not LC_ROW_ID_RE.fullmatch(row["row_id"]):
            return _emit_fail(R45, f"lifecycle_rows[{idx}].row_id fails grammar: {row['row_id']!r}")
        if row["current_status"] not in LIFECYCLE_STATUSES_SET:
            return _emit_fail(R45, f"lifecycle_rows[{idx}].current_status not in closed set: {row['current_status']!r}")
        if not isinstance(row["is_terminal"], bool):
            return _emit_fail(R45, f"lifecycle_rows[{idx}].is_terminal must be a boolean")
        if not isinstance(row["event_count"], int) or row["event_count"] < 0:
            return _emit_fail(R45, f"lifecycle_rows[{idx}].event_count must be a non-negative integer")
        if not isinstance(row["lifecycle_fingerprint"], str) or not BARE_HEX_SHA256_RE.fullmatch(row["lifecycle_fingerprint"]):
            return _emit_fail(R45, f"lifecycle_rows[{idx}].lifecycle_fingerprint must be bare lowercase hex SHA-256")

    coverage = report["coverage_summary"]
    for f in COVERAGE_SUMMARY_FIELDS:
        if f not in coverage:
            return _emit_fail(R45, f"coverage_summary missing required field {f!r}")
    for f in ("lifecycle_record_count", "lifecycle_event_count",
              "open_lifecycle_count", "terminal_lifecycle_count"):
        v = coverage.get(f)
        if not isinstance(v, int) or v < 0:
            return _emit_fail(R45, f"coverage_summary.{f} must be a non-negative integer")
    svc = coverage.get("status_value_count")
    if not isinstance(svc, dict):
        return _emit_fail(R45, "coverage_summary.status_value_count must be a JSON object")
    if set(svc.keys()) != set(LIFECYCLE_STATUSES):
        return _emit_fail(
            R45,
            f"coverage_summary.status_value_count keys must equal the six closed statuses; got {sorted(svc.keys())!r}",
        )
    for k, v in svc.items():
        if not isinstance(v, int) or v < 0:
            return _emit_fail(R45, f"coverage_summary.status_value_count[{k!r}] must be a non-negative integer")
    if sum(svc.values()) != coverage["lifecycle_record_count"]:
        return _emit_fail(
            R45,
            f"coverage_summary.status_value_count sum={sum(svc.values())} must equal lifecycle_record_count={coverage['lifecycle_record_count']}",
        )
    if coverage["terminal_lifecycle_count"] != coverage["lifecycle_record_count"] - coverage["open_lifecycle_count"]:
        return _emit_fail(
            R45,
            "coverage_summary.terminal_lifecycle_count must equal lifecycle_record_count - open_lifecycle_count",
        )

    # R46 gold_challenge_lifecycle_report_binding_invalid
    if report["package_id"] != manifest["package_id"]:
        return _emit_fail(R46, "lifecycle report package_id mismatch with manifest")
    if report["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R46, "lifecycle report governed_reliance_demo_id mismatch with manifest")
    if report["challenge_lifecycle_report_id"] != manifest["challenge_lifecycle_report_id"]:
        return _emit_fail(R46, "lifecycle report challenge_lifecycle_report_id mismatch with manifest")
    if report["lifecycle_record_set_id"] != manifest["challenge_lifecycle_record_set_id"]:
        return _emit_fail(
            R46,
            f"lifecycle report lifecycle_record_set_id={report['lifecycle_record_set_id']!r} "
            f"mismatch with manifest challenge_lifecycle_record_set_id={manifest['challenge_lifecycle_record_set_id']!r}",
        )
    if report["lifecycle_record_set_id"] != records_body["lifecycle_record_set_id"]:
        return _emit_fail(R46, "lifecycle report lifecycle_record_set_id mismatch with records body")
    if report["policy_evaluation_report_id"] != manifest["policy_evaluation_report_id"]:
        return _emit_fail(R46, "lifecycle report policy_evaluation_report_id mismatch with manifest")
    if report["source_records_sha256"] != manifest["subjects"][5]["sha256"]:
        return _emit_fail(R46, "lifecycle report source_records_sha256 mismatch with manifest subjects[5].sha256")
    if report["source_policy_evaluation_report_sha256"] != manifest["subjects"][4]["sha256"]:
        return _emit_fail(R46, "lifecycle report source_policy_evaluation_report_sha256 mismatch with manifest subjects[4].sha256")
    if report["source_decision_report_sha256"] != manifest["subjects"][2]["sha256"]:
        return _emit_fail(R46, "lifecycle report source_decision_report_sha256 mismatch with manifest subjects[2].sha256")
    if report["generated_at"] != records_body["generated_at"]:
        return _emit_fail(R46, "lifecycle report generated_at mismatch with records body generated_at")
    # 6-ID collision class involving challenge_lifecycle_report_id at the
    # report-body level: challenge_lifecycle_report_id MUST NOT collide
    # with any of the five other collision-class IDs.
    for other in ("conformance_report_id", "decision_report_id", "matrix_id",
                  "policy_evaluation_report_id", "challenge_lifecycle_record_set_id"):
        if manifest["challenge_lifecycle_report_id"] == manifest[other]:
            return _emit_fail(
                R46,
                f"challenge_lifecycle_report_id collides with manifest {other}: "
                f"{manifest['challenge_lifecycle_report_id']!r}",
            )

    # R47 gold_challenge_lifecycle_projection_invalid: re-derive
    # lifecycle_rows from the records body and compare canonical bytes
    # per row, plus row count and order.
    raw_records = records_body["lifecycle_records"]
    expected_rows = [
        _project_lifecycle_row(idx, r)
        for idx, r in enumerate(raw_records)
        if isinstance(r, dict)
    ]
    actual_rows = report["lifecycle_rows"]
    if len(actual_rows) != len(expected_rows):
        return _emit_fail(
            R47,
            f"lifecycle_rows length mismatch: report={len(actual_rows)}, "
            f"re-projected={len(expected_rows)}",
        )
    for idx, (exp, act) in enumerate(zip(expected_rows, actual_rows)):
        if _canonical_json_bytes(act) != _canonical_json_bytes(exp):
            return _emit_fail(
                R47,
                f"lifecycle_rows[{idx}] mismatch: re-projected row does not match published row",
            )

    # R48 gold_challenge_lifecycle_summary_invalid: re-derive
    # coverage_summary over the published rows and compare canonical bytes.
    expected_coverage = _rederive_coverage_summary(actual_rows)
    if _canonical_json_bytes(expected_coverage) != _canonical_json_bytes(coverage):
        return _emit_fail(
            R48,
            "coverage_summary mismatch: re-derived summary does not match published summary",
        )

    # R47 gold_challenge_lifecycle_projection_invalid (post-summary):
    # top-level report_fingerprint equality. Recompute SHA-256 of the
    # canonical JSON serialization of the report with the report_fingerprint
    # field removed and compare to the declared report_fingerprint. This
    # check is intentionally placed after the R48 coverage-summary
    # re-derivation as a deliberate non-masking post-summary R47 check:
    # row-level projection mismatches and coverage-summary mismatches must
    # be reachable under the row-rederive R47 path and R48 before a
    # fingerprint mismatch can fire over the whole report body. The
    # numeric ordering of emitted reasons is not literal here; R47 is
    # reached after R48 by design and the R45 hex-shape check above only
    # constrains the declared bytes' format, not their byte-equality to
    # the canonical re-derivation. The recomputation is byte-identical to
    # the runner's report_fingerprint derivation.
    report_for_fp = {k: v for k, v in report.items() if k != "report_fingerprint"}
    expected_report_fp = _sha256_hex(_canonical_json_bytes(report_for_fp))
    if report["report_fingerprint"] != expected_report_fp:
        return _emit_fail(
            R47,
            f"report_fingerprint mismatch: "
            f"declared={report['report_fingerprint']!r}, re-derived={expected_report_fp!r}",
        )

    return 0


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Gold v0.4.3 Challenge Lifecycle Lite package.",
    )
    parser.add_argument("--manifest", type=str, required=True,
                        help="Path to the v0.4.3 manifest gold-challenge-lifecycle-package-manifest.json.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent

    # Phase 1: v0.4.3 manifest integrity (R01 folds).
    rc, manifest = _check_manifest(manifest_path)
    if rc != 0 or manifest is None:
        return rc

    # Phase 2: inherited v0.4.2 (29+9=38) structural checks via subprocess.
    rc = _run_inherited_v042_checks(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 3: v0.4.3 cross-anchors (R01 folds).
    rc, package_obj, decision_obj, evaluation_obj = _check_cross_anchors(
        manifest=manifest, manifest_dir=manifest_dir,
    )
    if rc != 0 or package_obj is None or decision_obj is None or evaluation_obj is None:
        return rc

    # Phase 4: records body checks (R39..R43).
    rc, records_body = _check_records_body(
        manifest=manifest,
        manifest_dir=manifest_dir,
        decision_obj=decision_obj,
        evaluation_obj=evaluation_obj,
        package_obj=package_obj,
    )
    if rc != 0 or records_body is None:
        return rc

    # Phase 5: lifecycle report checks (R44..R48).
    rc = _check_lifecycle_report(
        manifest=manifest,
        manifest_dir=manifest_dir,
        records_body=records_body,
    )
    if rc != 0:
        return rc

    sys.stdout.write("PASS: gold v0.4.3 challenge lifecycle lite package verified\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
