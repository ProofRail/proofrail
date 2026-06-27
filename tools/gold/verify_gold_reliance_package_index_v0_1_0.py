#!/usr/bin/env python3
"""Verify a ProofRail Gold v0.4.4 Reliance Package Index package.

The v0.4.4 verifier validates a 5-subject local hash-anchored
package. It owns six new reasons (R49..R54) over the v0.4.4 index
body (subject [4]) and DELEGATES the inherited 48 R01..R48 reasons
over subjects [0..3] to the corresponding co-located inherited
verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) via subprocess. A missing
or unlaunchable inherited verifier, or one that crashes with a
non-FAIL non-zero exit (i.e. anything other than 0 or 1), is treated
as an ENVIRONMENT failure: it emits a non-reason-shaped `INFRA:`
diagnostic to stderr, exits with code 3, and MUST NOT collapse into
any of the 54 public verifier reason names or the 5 runner-only
refusal names.

Public failure reasons (closed set of 54):

  R01..R24 inherited from v0.4.0 (relayed verbatim from the v0.4.0
  verifier or emitted directly by v0.4.4 manifest-integrity /
  cross-anchor checks under R01).

  R25..R29 inherited from v0.4.1 (relayed verbatim from the v0.4.1
  verifier).

  R30..R38 inherited from v0.4.2 (relayed verbatim from the v0.4.2
  verifier).

  R39..R48 inherited from v0.4.3 (relayed verbatim from the v0.4.3
  verifier).

  R49..R54 introduced by v0.4.4 (owned by this verifier, emitted
  directly):

  R49 gold_reliance_package_index_not_object
  R50 gold_reliance_package_index_schema_invalid
  R51 gold_reliance_package_index_binding_invalid
  R52 gold_reliance_package_index_entry_invalid
  R53 gold_reliance_package_index_summary_invalid
  R54 gold_reliance_package_index_fingerprint_invalid

The verifier never emits the 5 runner-only refusal reasons
(`runner_input_*`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Reason constants. R01 is emitted directly for v0.4.4 wrapping
# manifest integrity and cross-anchor checks; R02..R48 are surfaced via
# inherited verifier subprocess relay; R49..R54 are owned by v0.4.4.
# ---------------------------------------------------------------------------

R01 = "gold_manifest_invalid"

R49 = "gold_reliance_package_index_not_object"
R50 = "gold_reliance_package_index_schema_invalid"
R51 = "gold_reliance_package_index_binding_invalid"
R52 = "gold_reliance_package_index_entry_invalid"
R53 = "gold_reliance_package_index_summary_invalid"
R54 = "gold_reliance_package_index_fingerprint_invalid"

# Closed runner-only refusal set; the verifier never emits these.
RUNNER_ONLY_REFUSALS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

# ---------------------------------------------------------------------------
# Closed constants for the v0.4.4 wrapping manifest.
# ---------------------------------------------------------------------------

EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.reliance_package_index_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_RELEASE = "gold.reliance_package_index.v0.4.4"
EXPECTED_HASH_ALGO = "sha256"

EXPECTED_INDEX_BODY_DOC_TYPE = "proofrail.gold.reliance_package_index"
EXPECTED_INDEX_BODY_SCHEMA_VERSION = "v0.1.0"
EXPECTED_INDEX_BODY_RELEASE = "gold.reliance_package_index.v0.4.4"

# Child closure layout. Subjects [0..3] are the inherited child
# wrapping manifests under `child-packages/v0.4.X/`. Subject [4] is the
# v0.4.4 index body at the package root.
CHILD_DIR_V040 = "child-packages/v0.4.0"
CHILD_DIR_V041 = "child-packages/v0.4.1"
CHILD_DIR_V042 = "child-packages/v0.4.2"
CHILD_DIR_V043 = "child-packages/v0.4.3"

CHILD_MANIFEST_FILENAME_V040 = "gold-governed-reliance-package-manifest.json"
CHILD_MANIFEST_FILENAME_V041 = "gold-decision-report-package-manifest.json"
CHILD_MANIFEST_FILENAME_V042 = "gold-policy-evaluation-matrix-package-manifest.json"
CHILD_MANIFEST_FILENAME_V043 = "gold-challenge-lifecycle-package-manifest.json"

SUBJECT_PATH_V040 = f"{CHILD_DIR_V040}/{CHILD_MANIFEST_FILENAME_V040}"
SUBJECT_PATH_V041 = f"{CHILD_DIR_V041}/{CHILD_MANIFEST_FILENAME_V041}"
SUBJECT_PATH_V042 = f"{CHILD_DIR_V042}/{CHILD_MANIFEST_FILENAME_V042}"
SUBJECT_PATH_V043 = f"{CHILD_DIR_V043}/{CHILD_MANIFEST_FILENAME_V043}"

INDEX_BODY_FILENAME = "gold-reliance-package-index.json"

EXPECTED_SUBJECT_PATHS = (
    SUBJECT_PATH_V040,
    SUBJECT_PATH_V041,
    SUBJECT_PATH_V042,
    SUBJECT_PATH_V043,
    INDEX_BODY_FILENAME,
)
EXPECTED_SUBJECT_ROLES = (
    "gold_governed_reliance_package_manifest",
    "gold_decision_report_package_manifest",
    "gold_policy_evaluation_matrix_package_manifest",
    "gold_challenge_lifecycle_package_manifest",
    "gold_reliance_package_index",
)

# Per-entry release labels (fixed by the v0.4.4 body schema).
RELEASE_LABEL_V040 = "gold.governed_reliance.v0.4.0"
RELEASE_LABEL_V041 = "gold.decision_report_hardening.v0.4.1"
RELEASE_LABEL_V042 = "gold.policy_evaluation_matrix.v0.4.2"
RELEASE_LABEL_V043 = "gold.challenge_lifecycle_lite.v0.4.3"

EXPECTED_RELEASE_LABELS = (
    RELEASE_LABEL_V040,
    RELEASE_LABEL_V041,
    RELEASE_LABEL_V042,
    RELEASE_LABEL_V043,
)

EXPECTED_CHILD_PACKAGE_ROOTS = (
    f"{CHILD_DIR_V040}/",
    f"{CHILD_DIR_V041}/",
    f"{CHILD_DIR_V042}/",
    f"{CHILD_DIR_V043}/",
)

PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
ISO_8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BARE_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ---------------------------------------------------------------------------
# Co-located inherited verifier paths (subprocess-invoked).
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent

GOLD_V040_VERIFIER = _TOOLS_DIR / "verify_gold_governed_reliance_demo_v0_1_0.py"
GOLD_V041_VERIFIER = _TOOLS_DIR / "verify_gold_decision_report_hardening_v0_1_0.py"
GOLD_V042_VERIFIER = _TOOLS_DIR / "verify_gold_policy_evaluation_matrix_v0_1_0.py"
GOLD_V043_VERIFIER = _TOOLS_DIR / "verify_gold_challenge_lifecycle_lite_v0_1_0.py"


# ---------------------------------------------------------------------------
# Fail helpers and serializer.
#
#   _canonical_json_bytes_no_newline: used ONLY for the v0.4.4
#                                    `index_fingerprint` re-derivation
#                                    (matches the runner's
#                                    fingerprint domain per the v0.4.4
#                                    body schema). The body file's
#                                    on-disk SHA-256 is computed over
#                                    the file bytes as written (with
#                                    trailing newline) and lives in
#                                    the wrapping manifest's
#                                    subjects[4].sha256.
# ---------------------------------------------------------------------------

def _emit_fail(reason: str, detail: str) -> int:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    return 1


def _emit_infra(detail: str) -> int:
    sys.stderr.write(f"INFRA: {detail}\n")
    return 3


def _canonical_json_bytes_no_newline(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


# ---------------------------------------------------------------------------
# Phase 1: v0.4.4 wrapping manifest structural integrity. All folds
# emit R01.
# ---------------------------------------------------------------------------

# Top-level v0.4.4 manifest string fields.
_MANIFEST_STRING_FIELDS = (
    "manifest_id",
    "conformance_report_id",
    "decision_report_id",
    "matrix_id",
    "policy_evaluation_report_id",
    "challenge_lifecycle_record_set_id",
    "challenge_lifecycle_report_id",
    "gold_reliance_package_index_id",
    "package_id",
    "governed_reliance_demo_id",
    "generated_at",
)

# Top-level v0.4.4 manifest fields constrained by the closed
# identifier grammar.
_MANIFEST_GRAMMAR_FIELDS = (
    "manifest_id",
    "conformance_report_id",
    "decision_report_id",
    "matrix_id",
    "policy_evaluation_report_id",
    "challenge_lifecycle_record_set_id",
    "challenge_lifecycle_report_id",
    "gold_reliance_package_index_id",
    "package_id",
    "governed_reliance_demo_id",
)

# The seven v0.4.4 collision-class IDs. `manifest_id`, `package_id`,
# and `governed_reliance_demo_id` are explicitly excluded.
_COLLISION_CLASS_FIELDS = (
    "conformance_report_id",
    "decision_report_id",
    "matrix_id",
    "policy_evaluation_report_id",
    "challenge_lifecycle_record_set_id",
    "challenge_lifecycle_report_id",
    "gold_reliance_package_index_id",
)


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

    for field in _MANIFEST_STRING_FIELDS:
        val = manifest.get(field)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R01, f"{field} must be a non-empty string"), None

    for field in _MANIFEST_GRAMMAR_FIELDS:
        if not PACKAGE_ID_RE.fullmatch(manifest[field]):
            return _emit_fail(
                R01,
                f"{field} fails closed identifier grammar: {manifest[field]!r}",
            ), None

    if not ISO_8601_UTC_RE.fullmatch(manifest["generated_at"]):
        return _emit_fail(
            R01,
            f"generated_at must be ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ, got {manifest['generated_at']!r}",
        ), None

    # 7-ID pairwise distinctness over the v0.4.4 collision class.
    # `manifest_id`, `package_id`, and `governed_reliance_demo_id` are
    # explicitly excluded from the collision class per the v0.4.4
    # wrapping manifest schema; they MAY share a value with any field
    # outside this class subject to its own grammar.
    seen: dict[str, str] = {}
    for name in _COLLISION_CLASS_FIELDS:
        val = manifest[name]
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
        return _emit_fail(
            R01,
            f"subjects must hold exactly 5 entries, got {len(subjects)}",
        ), None

    for idx, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return _emit_fail(R01, f"subjects[{idx}] is not an object"), None
        role = subj.get("role")
        path = subj.get("path")
        sha = subj.get("sha256")
        size = subj.get("size_bytes")
        if role != EXPECTED_SUBJECT_ROLES[idx]:
            return _emit_fail(
                R01,
                f"subjects[{idx}].role must be {EXPECTED_SUBJECT_ROLES[idx]!r}, got {role!r}",
            ), None
        if not isinstance(path, str) or path == "":
            return _emit_fail(R01, f"subjects[{idx}].path must be a non-empty string"), None
        # Path-traversal check BEFORE path-equality check (non-masking).
        if _has_traversal(path):
            return _emit_fail(R01, f"subjects[{idx}].path contains path traversal: {path!r}"), None
        if os.path.isabs(path):
            return _emit_fail(R01, f"subjects[{idx}].path must be relative: {path!r}"), None
        if path != EXPECTED_SUBJECT_PATHS[idx]:
            return _emit_fail(
                R01,
                f"subjects[{idx}].path must equal {EXPECTED_SUBJECT_PATHS[idx]!r}, got {path!r}",
            ), None
        if not isinstance(sha, str) or not BARE_HEX_SHA256_RE.fullmatch(sha):
            return _emit_fail(R01, f"subjects[{idx}].sha256 must be bare lowercase hex SHA-256"), None
        if not isinstance(size, int) or size < 0:
            return _emit_fail(R01, f"subjects[{idx}].size_bytes must be a non-negative integer"), None

    # File-on-disk checks for all five subjects (size + sha).
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
# Phase 2: cross-anchor between the v0.4.4 wrapping manifest and each
# inherited child wrapping manifest. All folds emit R01 per the v0.4.4
# wrapping manifest schema's "Cross-Anchor Rules" section. Child
# manifest structural defects beyond the fields needed for cross-anchor
# are NOT surfaced here; they fall through to the inherited verifier
# subprocess (Phase 4) where they surface as R01..R48 in the inherited
# verifier's own namespace, relayed verbatim.
# ---------------------------------------------------------------------------

def _read_child_manifest_obj(manifest_dir: Path, subject_path: str) -> dict[str, Any] | None:
    p = manifest_dir / subject_path
    try:
        raw = p.read_bytes()
    except OSError:
        return None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _check_cross_anchors_with_children(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    v040 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V040)
    v041 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V041)
    v042 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V042)
    v043 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V043)
    if v040 is None or v041 is None or v042 is None or v043 is None:
        return _emit_fail(
            R01,
            "one or more inherited child wrapping manifests unreadable as JSON object for cross-anchor check",
        )

    # package_id binding anchor: must equal every child manifest's package_id.
    for label, child in (
        ("v0.4.0", v040), ("v0.4.1", v041), ("v0.4.2", v042), ("v0.4.3", v043),
    ):
        if child.get("package_id") != manifest["package_id"]:
            return _emit_fail(
                R01,
                f"{label} child manifest package_id mismatch with v0.4.4 manifest package_id",
            )
        if child.get("governed_reliance_demo_id") != manifest["governed_reliance_demo_id"]:
            return _emit_fail(
                R01,
                f"{label} child manifest governed_reliance_demo_id mismatch with v0.4.4 manifest governed_reliance_demo_id",
            )

    # Inherited identifier cross-anchors.
    if v040.get("report_id") != manifest["conformance_report_id"]:
        return _emit_fail(
            R01,
            "v0.4.0 child manifest report_id mismatch with v0.4.4 manifest conformance_report_id",
        )
    if v041.get("decision_report_id") != manifest["decision_report_id"]:
        return _emit_fail(
            R01,
            "v0.4.1 child manifest decision_report_id mismatch with v0.4.4 manifest decision_report_id",
        )
    if v042.get("matrix_id") != manifest["matrix_id"]:
        return _emit_fail(
            R01,
            "v0.4.2 child manifest matrix_id mismatch with v0.4.4 manifest matrix_id",
        )
    if v042.get("policy_evaluation_report_id") != manifest["policy_evaluation_report_id"]:
        return _emit_fail(
            R01,
            "v0.4.2 child manifest policy_evaluation_report_id mismatch with v0.4.4 manifest policy_evaluation_report_id",
        )
    if v043.get("challenge_lifecycle_record_set_id") != manifest["challenge_lifecycle_record_set_id"]:
        return _emit_fail(
            R01,
            "v0.4.3 child manifest challenge_lifecycle_record_set_id mismatch with v0.4.4 manifest challenge_lifecycle_record_set_id",
        )
    if v043.get("challenge_lifecycle_report_id") != manifest["challenge_lifecycle_report_id"]:
        return _emit_fail(
            R01,
            "v0.4.3 child manifest challenge_lifecycle_report_id mismatch with v0.4.4 manifest challenge_lifecycle_report_id",
        )
    return 0


# ---------------------------------------------------------------------------
# Phase 3: v0.4.4 index body (subject [4]) checks (R49..R54).
#
# Ordering rationale (non-masking):
#   R49 (not_object) before any structural fold
#   R50 (schema)     for top-level field presence/types/allowed values
#                    (excluding deep entries/coverage_summary internals)
#   R52 (entry)      for per-entry shape/order/count/field violations
#   R53 (summary)    for coverage_summary shape and arithmetic
#   R51 (binding)    cross-anchor checks with the wrapping manifest
#                    (requires shaped body and shaped manifest)
#   R54 (fingerprint) index_fingerprint re-derivation (requires fully
#                    shaped body so that the fingerprint domain is
#                    well-defined).
# ---------------------------------------------------------------------------

_INDEX_BODY_TOP_LEVEL_FIELDS = (
    "document_type",
    "schema_version",
    "proofrail_release",
    "hash_algorithm",
    "gold_reliance_package_index_id",
    "package_id",
    "governed_reliance_demo_id",
    "generated_at",
    "entries",
    "coverage_summary",
    "index_fingerprint",
)

_INDEX_BODY_GRAMMAR_FIELDS = (
    "gold_reliance_package_index_id",
    "package_id",
    "governed_reliance_demo_id",
)

_ENTRY_REQUIRED_FIELDS = (
    "release_label",
    "child_subject_index",
    "child_package_root",
    "child_manifest_path",
    "child_manifest_fingerprint",
    "child_manifest_size_bytes",
)

_COVERAGE_SUMMARY_FIELDS = (
    "child_package_count",
    "inherited_release_count",
    "pairwise_distinct_id_count",
    "package_id_anchor_consistency",
    "governed_reliance_demo_id_anchor_consistency",
)


def _check_index_body(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    body_path = manifest_dir / INDEX_BODY_FILENAME
    try:
        raw = body_path.read_bytes()
    except OSError as e:
        # Subject-file readability was already verified under R01;
        # reaching here implies a race or filesystem race condition.
        # Re-surface as R01 since this is a wrapping-manifest layer
        # invariant.
        return _emit_fail(R01, f"index body unreadable after manifest check: {e}")

    # R49: not_object
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R49, f"index body is not valid JSON: {e}")
    if not isinstance(body, dict):
        return _emit_fail(R49, "index body is not a JSON object")

    # R50: top-level schema (required fields, types, allowed value sets).
    # Stray-key discipline at the top level surfaces here under R50 as
    # well, per the v0.4.4 body schema's Stray-Key Discipline clause.
    for f in _INDEX_BODY_TOP_LEVEL_FIELDS:
        if f not in body:
            return _emit_fail(R50, f"index body missing required field {f!r}")
    stray_top = set(body.keys()) - set(_INDEX_BODY_TOP_LEVEL_FIELDS)
    if stray_top:
        return _emit_fail(
            R50,
            f"index body has stray top-level keys (closed shape): {sorted(stray_top)!r}",
        )
    if body.get("document_type") != EXPECTED_INDEX_BODY_DOC_TYPE:
        return _emit_fail(R50, f"document_type must be {EXPECTED_INDEX_BODY_DOC_TYPE!r}")
    if body.get("schema_version") != EXPECTED_INDEX_BODY_SCHEMA_VERSION:
        return _emit_fail(R50, f"schema_version must be {EXPECTED_INDEX_BODY_SCHEMA_VERSION!r}")
    if body.get("proofrail_release") != EXPECTED_INDEX_BODY_RELEASE:
        return _emit_fail(R50, f"proofrail_release must be {EXPECTED_INDEX_BODY_RELEASE!r}")
    if body.get("hash_algorithm") != EXPECTED_HASH_ALGO:
        return _emit_fail(R50, f"hash_algorithm must be {EXPECTED_HASH_ALGO!r}")
    for f in _INDEX_BODY_GRAMMAR_FIELDS:
        v = body.get(f)
        if not isinstance(v, str) or v == "":
            return _emit_fail(R50, f"{f} must be a non-empty string")
        if not PACKAGE_ID_RE.fullmatch(v):
            return _emit_fail(R50, f"{f} fails closed identifier grammar: {v!r}")
    if not isinstance(body.get("generated_at"), str) or not ISO_8601_UTC_RE.fullmatch(body["generated_at"]):
        return _emit_fail(
            R50,
            f"generated_at must be ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ, got {body.get('generated_at')!r}",
        )
    if not isinstance(body.get("entries"), list):
        return _emit_fail(R50, "entries must be a JSON array")
    if not isinstance(body.get("coverage_summary"), dict):
        return _emit_fail(R50, "coverage_summary must be a JSON object")
    fp = body.get("index_fingerprint")
    if not isinstance(fp, str) or not BARE_HEX_SHA256_RE.fullmatch(fp):
        return _emit_fail(R50, "index_fingerprint must be bare lowercase hex SHA-256")

    # R52: entries[] shape/order/count/per-entry field violations.
    entries = body["entries"]
    if len(entries) != 4:
        return _emit_fail(
            R52,
            f"entries must hold exactly 4 entries, got {len(entries)}",
        )
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return _emit_fail(R52, f"entries[{idx}] is not an object")
        for f in _ENTRY_REQUIRED_FIELDS:
            if f not in entry:
                return _emit_fail(R52, f"entries[{idx}] missing required field {f!r}")
        stray_entry = set(entry.keys()) - set(_ENTRY_REQUIRED_FIELDS)
        if stray_entry:
            return _emit_fail(
                R52,
                f"entries[{idx}] has stray keys (closed shape): {sorted(stray_entry)!r}",
            )
        if entry["release_label"] != EXPECTED_RELEASE_LABELS[idx]:
            return _emit_fail(
                R52,
                f"entries[{idx}].release_label must be {EXPECTED_RELEASE_LABELS[idx]!r}, got {entry['release_label']!r}",
            )
        if entry["child_subject_index"] != idx:
            return _emit_fail(
                R52,
                f"entries[{idx}].child_subject_index must be {idx}, got {entry['child_subject_index']!r}",
            )
        if not isinstance(entry["child_subject_index"], int) or isinstance(entry["child_subject_index"], bool):
            return _emit_fail(
                R52,
                f"entries[{idx}].child_subject_index must be an integer (not bool)",
            )
        cpr = entry["child_package_root"]
        if not isinstance(cpr, str) or cpr != EXPECTED_CHILD_PACKAGE_ROOTS[idx]:
            return _emit_fail(
                R52,
                f"entries[{idx}].child_package_root must equal {EXPECTED_CHILD_PACKAGE_ROOTS[idx]!r}, got {cpr!r}",
            )
        # Path-traversal/absolute-path checks BEFORE path-equality (non-masking).
        if _has_traversal(cpr) or os.path.isabs(cpr):
            return _emit_fail(
                R52,
                f"entries[{idx}].child_package_root must be a relative non-traversal path: {cpr!r}",
            )
        cmp_ = entry["child_manifest_path"]
        if not isinstance(cmp_, str) or cmp_ == "":
            return _emit_fail(R52, f"entries[{idx}].child_manifest_path must be a non-empty string")
        if _has_traversal(cmp_) or os.path.isabs(cmp_):
            return _emit_fail(
                R52,
                f"entries[{idx}].child_manifest_path must be a relative non-traversal path: {cmp_!r}",
            )
        if cmp_ != EXPECTED_SUBJECT_PATHS[idx]:
            return _emit_fail(
                R52,
                f"entries[{idx}].child_manifest_path must equal {EXPECTED_SUBJECT_PATHS[idx]!r}, got {cmp_!r}",
            )
        cmf = entry["child_manifest_fingerprint"]
        if not isinstance(cmf, str) or not BARE_HEX_SHA256_RE.fullmatch(cmf):
            return _emit_fail(
                R52,
                f"entries[{idx}].child_manifest_fingerprint must be bare lowercase hex SHA-256",
            )
        cms = entry["child_manifest_size_bytes"]
        if not isinstance(cms, int) or isinstance(cms, bool) or cms < 0:
            return _emit_fail(
                R52,
                f"entries[{idx}].child_manifest_size_bytes must be a non-negative integer",
            )

    # R53: coverage_summary shape and arithmetic.
    coverage = body["coverage_summary"]
    for f in _COVERAGE_SUMMARY_FIELDS:
        if f not in coverage:
            return _emit_fail(R53, f"coverage_summary missing required field {f!r}")
    stray_cov = set(coverage.keys()) - set(_COVERAGE_SUMMARY_FIELDS)
    if stray_cov:
        return _emit_fail(
            R53,
            f"coverage_summary has stray keys (closed shape): {sorted(stray_cov)!r}",
        )
    if coverage["child_package_count"] != 4 or isinstance(coverage["child_package_count"], bool):
        return _emit_fail(R53, f"coverage_summary.child_package_count must equal 4, got {coverage['child_package_count']!r}")
    if coverage["inherited_release_count"] != 4 or isinstance(coverage["inherited_release_count"], bool):
        return _emit_fail(R53, f"coverage_summary.inherited_release_count must equal 4, got {coverage['inherited_release_count']!r}")
    if coverage["pairwise_distinct_id_count"] != 7 or isinstance(coverage["pairwise_distinct_id_count"], bool):
        return _emit_fail(R53, f"coverage_summary.pairwise_distinct_id_count must equal 7, got {coverage['pairwise_distinct_id_count']!r}")
    if coverage["package_id_anchor_consistency"] is not True:
        return _emit_fail(R53, "coverage_summary.package_id_anchor_consistency must equal true")
    if coverage["governed_reliance_demo_id_anchor_consistency"] is not True:
        return _emit_fail(R53, "coverage_summary.governed_reliance_demo_id_anchor_consistency must equal true")

    # R51: body-level cross-anchor checks with the wrapping manifest.
    if body["gold_reliance_package_index_id"] != manifest["gold_reliance_package_index_id"]:
        return _emit_fail(
            R51,
            "index body gold_reliance_package_index_id mismatch with v0.4.4 wrapping manifest",
        )
    if body["package_id"] != manifest["package_id"]:
        return _emit_fail(R51, "index body package_id mismatch with v0.4.4 wrapping manifest")
    if body["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R51, "index body governed_reliance_demo_id mismatch with v0.4.4 wrapping manifest")
    for idx, entry in enumerate(entries):
        if entry["child_manifest_fingerprint"] != manifest["subjects"][idx]["sha256"]:
            return _emit_fail(
                R51,
                f"entries[{idx}].child_manifest_fingerprint mismatch with subjects[{idx}].sha256",
            )
        if entry["child_manifest_size_bytes"] != manifest["subjects"][idx]["size_bytes"]:
            return _emit_fail(
                R51,
                f"entries[{idx}].child_manifest_size_bytes mismatch with subjects[{idx}].size_bytes",
            )
        if entry["child_manifest_path"] != manifest["subjects"][idx]["path"]:
            return _emit_fail(
                R51,
                f"entries[{idx}].child_manifest_path mismatch with subjects[{idx}].path",
            )
    # Recompute anchor consistency independently and surface mismatches
    # as R51 (binding-anchor mismatch with the actual on-disk child
    # manifests), per the v0.4.4 body schema's coverage_summary
    # "verifier independently recomputes and confirms" clause.
    v040 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V040)
    v041 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V041)
    v042 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V042)
    v043 = _read_child_manifest_obj(manifest_dir, SUBJECT_PATH_V043)
    if v040 is None or v041 is None or v042 is None or v043 is None:
        return _emit_fail(
            R51,
            "one or more inherited child wrapping manifests unreadable for anchor-consistency recomputation",
        )
    for label, child in (("v0.4.0", v040), ("v0.4.1", v041), ("v0.4.2", v042), ("v0.4.3", v043)):
        if child.get("package_id") != body["package_id"]:
            return _emit_fail(
                R51,
                f"{label} child manifest package_id mismatch with index body package_id",
            )
        if child.get("governed_reliance_demo_id") != body["governed_reliance_demo_id"]:
            return _emit_fail(
                R51,
                f"{label} child manifest governed_reliance_demo_id mismatch with index body governed_reliance_demo_id",
            )

    # R54: index_fingerprint re-derivation.
    body_without_fp = {k: v for k, v in body.items() if k != "index_fingerprint"}
    expected_fp = _sha256_hex(_canonical_json_bytes_no_newline(body_without_fp))
    if body["index_fingerprint"] != expected_fp:
        return _emit_fail(
            R54,
            f"index_fingerprint mismatch: declared={body['index_fingerprint']!r}, re-derived={expected_fp!r}",
        )

    return 0


# ---------------------------------------------------------------------------
# Phase 4: subprocess-invoke each inherited verifier on its child
# wrapping-manifest path. R02..R48 are relayed verbatim. A missing or
# unlaunchable inherited verifier, or one that exits with a non-FAIL
# non-zero code, is treated as an environment failure (INFRA exit 3),
# never as a public reason name.
# ---------------------------------------------------------------------------

def _run_inherited_verifier(
    *,
    verifier_path: Path,
    child_manifest_path: Path,
    label: str,
) -> int:
    if not verifier_path.exists():
        return _emit_infra(
            f"co-located {label} verifier unavailable for inherited check delegation: "
            f"expected at {verifier_path}"
        )
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(verifier_path),
                "--manifest",
                str(child_manifest_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (FileNotFoundError, PermissionError, OSError) as e:
        return _emit_infra(
            f"co-located {label} verifier unavailable for inherited check delegation: "
            f"{type(e).__name__}: {e}"
        )
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    if result.returncode == 0:
        return 0
    if result.returncode == 1:
        # Inherited FAIL — relay verbatim.
        return 1
    # Any non-1 non-zero exit from the inherited verifier is treated as
    # INFRA (its own exit 3 or a crash). This MUST NOT collapse into any
    # public v0.4.4 reason name.
    return _emit_infra(
        f"inherited {label} verifier exited with non-FAIL non-zero code {result.returncode}"
    )


def _run_all_inherited_verifiers(
    *,
    manifest_dir: Path,
) -> int:
    for verifier_path, child_subject_path, label in (
        (GOLD_V040_VERIFIER, SUBJECT_PATH_V040, "v0.4.0"),
        (GOLD_V041_VERIFIER, SUBJECT_PATH_V041, "v0.4.1"),
        (GOLD_V042_VERIFIER, SUBJECT_PATH_V042, "v0.4.2"),
        (GOLD_V043_VERIFIER, SUBJECT_PATH_V043, "v0.4.3"),
    ):
        child_manifest_path = manifest_dir / child_subject_path
        rc = _run_inherited_verifier(
            verifier_path=verifier_path,
            child_manifest_path=child_manifest_path,
            label=label,
        )
        if rc != 0:
            return rc
    return 0


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Gold v0.4.4 Reliance Package Index package.",
    )
    parser.add_argument("--manifest", type=str, required=True,
                        help="Path to the v0.4.4 wrapping manifest gold-reliance-package-index-manifest.json.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent

    # Phase 1: v0.4.4 wrapping manifest integrity (R01 folds).
    rc, manifest = _check_manifest(manifest_path)
    if rc != 0 or manifest is None:
        return rc

    # Phase 2: cross-anchor between the v0.4.4 wrapping manifest and
    # each inherited child wrapping manifest (R01 folds).
    rc = _check_cross_anchors_with_children(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 3: v0.4.4 index body checks (R49..R54). Owned by v0.4.4 and
    # validated BEFORE any inherited verifier subprocess so that the
    # v0.4.4-owned reasons are reachable without contaminating any
    # inherited verifier's namespace.
    rc = _check_index_body(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 4: inherited verifiers via subprocess (R02..R48 relayed
    # verbatim; INFRA exit 3 on env failure or non-FAIL non-zero
    # inherited exit). Invocation order: v0.4.0, v0.4.1, v0.4.2,
    # v0.4.3.
    rc = _run_all_inherited_verifiers(manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    sys.stdout.write("PASS: gold v0.4.4 reliance package index package verified\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
