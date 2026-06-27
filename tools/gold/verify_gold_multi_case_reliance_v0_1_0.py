#!/usr/bin/env python3
"""Verify a ProofRail Gold v0.4.5 Multi-Case Reliance Demo package.

The v0.4.5 verifier validates a 2-subject local hash-anchored
package. It owns seven new reasons (R55..R61) and DELEGATES the
inherited 54 R01..R54 reasons over subject [0] (the v0.4.4 wrapping
manifest) to the co-located v0.4.4 verifier via subprocess (which
in turn transitively delegates to v0.4.0..v0.4.3 verifiers under
R01..R48). A missing or unlaunchable v0.4.4 verifier, or one that
crashes with a non-FAIL non-zero exit (anything other than 0 or 1),
is treated as an ENVIRONMENT failure: a non-reason-shaped `INFRA:`
diagnostic is written to stderr, the verifier exits with code 3,
and MUST NOT collapse into any of the 61 public verifier reason
names or the 5 runner-only refusal names.

Public failure reasons (closed set of 61):

  R01..R54 inherited from v0.4.4 (relayed verbatim from the v0.4.4
  verifier on the v0.4.4 child wrapping manifest).

  R55..R61 introduced by v0.4.5 (owned by this verifier):

  R55 gold_multi_case_reliance_manifest_invalid
  R56 gold_multi_case_reliance_subject_digest_mismatch
  R57 gold_multi_case_reliance_index_invalid
  R58 gold_multi_case_reliance_child_manifest_binding_invalid
  R59 gold_multi_case_reliance_case_count_invalid
  R60 gold_multi_case_reliance_case_binding_invalid
  R61 gold_multi_case_reliance_index_rederive_mismatch

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
# Reason constants. R55..R61 are owned by v0.4.5; R01..R54 are
# surfaced only via inherited v0.4.4 verifier subprocess relay.
# ---------------------------------------------------------------------------

R55 = "gold_multi_case_reliance_manifest_invalid"
R56 = "gold_multi_case_reliance_subject_digest_mismatch"
R57 = "gold_multi_case_reliance_index_invalid"
R58 = "gold_multi_case_reliance_child_manifest_binding_invalid"
R59 = "gold_multi_case_reliance_case_count_invalid"
R60 = "gold_multi_case_reliance_case_binding_invalid"
R61 = "gold_multi_case_reliance_index_rederive_mismatch"

# Closed runner-only refusal set; the verifier never emits these.
RUNNER_ONLY_REFUSALS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

# ---------------------------------------------------------------------------
# Closed constants for the v0.4.5 wrapping manifest and index body.
# ---------------------------------------------------------------------------

EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.multi_case_reliance_package_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_RELEASE = "gold.multi_case_reliance.v0.4.5"
EXPECTED_HASH_ALGO = "sha256"

EXPECTED_INDEX_BODY_DOC_TYPE = "proofrail.gold.multi_case_reliance_index"
EXPECTED_INDEX_BODY_SCHEMA_VERSION = "v0.1.0"
EXPECTED_INDEX_BODY_RELEASE = "gold.multi_case_reliance.v0.4.5"

# Child closure layout. Subject [0] is the v0.4.4 wrapping manifest
# under `child-packages/v0.4.4/`. Subject [1] is the v0.4.5 index
# body at the package root.
V044_CHILD_DIR = "child-packages/v0.4.4"
V044_MANIFEST_FILENAME = "gold-reliance-package-index-manifest.json"
V044_INDEX_BODY_FILENAME = "gold-reliance-package-index.json"

V045_SUBJECT_PATH_V044_MANIFEST = f"{V044_CHILD_DIR}/{V044_MANIFEST_FILENAME}"
V045_INDEX_BODY_FILENAME = "gold-multi-case-reliance-index.json"

# v0.4.0..v0.4.3 body paths reached through the v0.4.4 child closure.
V044_V040_REL = "child-packages/v0.4.0/governed-reliance-scenarios.json"
V044_V041_REL = "child-packages/v0.4.1/gold-governed-reliance-decision-report.json"
V044_V042_REL = "child-packages/v0.4.2/gold-policy-evaluation-report.json"
V044_V043_REL = "child-packages/v0.4.3/challenge-lifecycle-records.json"

V045_DECISION_REPORT_REF = f"{V044_CHILD_DIR}/{V044_V041_REL}"

EXPECTED_SUBJECT_PATHS = (
    V045_SUBJECT_PATH_V044_MANIFEST,
    V045_INDEX_BODY_FILENAME,
)
EXPECTED_SUBJECT_ROLES = (
    "gold_reliance_package_index_manifest",
    "gold_multi_case_reliance_index",
)

PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
ISO_8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BARE_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Closed value sets for per-case fields, sourced from the v0.4.0
# governed_decisions taxonomy.
SCENARIO_TYPES = (
    "clean_acceptance",
    "policy_rejection",
    "challenge_filed",
    "withdrawal",
    "supersession",
)
DECISION_STATUSES = (
    "accepted",
    "rejected",
    "challenged",
    "withdrawn",
    "superseded",
)

# ---------------------------------------------------------------------------
# Co-located inherited verifier path (subprocess-invoked).
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent
GOLD_V044_VERIFIER = _TOOLS_DIR / "verify_gold_reliance_package_index_v0_1_0.py"


# ---------------------------------------------------------------------------
# Fail helpers and serializer.
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
# Phase 1: v0.4.5 wrapping manifest structural integrity (R55).
# Per-subject file-on-disk readability and digest check (R56).
# ---------------------------------------------------------------------------

_MANIFEST_TOP_LEVEL_FIELDS = (
    "document_type",
    "schema_version",
    "proofrail_release",
    "hash_algorithm",
    "manifest_id",
    "gold_multi_case_reliance_index_id",
    "package_id",
    "governed_reliance_demo_id",
    "gold_reliance_package_index_ref",
    "decision_report_ref",
    "generated_at",
    "subjects",
)

_MANIFEST_GRAMMAR_FIELDS = (
    "manifest_id",
    "gold_multi_case_reliance_index_id",
    "package_id",
    "governed_reliance_demo_id",
)


def _check_manifest_structure(
    manifest_path: Path,
) -> tuple[int, dict[str, Any] | None, bytes | None]:
    if not manifest_path.exists():
        return _emit_fail(R55, f"manifest path does not exist: {manifest_path}"), None, None
    try:
        raw = manifest_path.read_bytes()
    except OSError as e:
        return _emit_fail(R55, f"cannot read manifest: {e}"), None, None
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R55, f"manifest is not valid JSON: {e}"), None, None
    if not isinstance(manifest, dict):
        return _emit_fail(R55, "manifest is not a JSON object"), None, None

    for f in _MANIFEST_TOP_LEVEL_FIELDS:
        if f not in manifest:
            return _emit_fail(R55, f"manifest missing required field {f!r}"), None, None
    stray_top = set(manifest.keys()) - set(_MANIFEST_TOP_LEVEL_FIELDS)
    if stray_top:
        return _emit_fail(
            R55,
            f"manifest has stray top-level keys (closed shape): {sorted(stray_top)!r}",
        ), None, None

    if manifest.get("document_type") != EXPECTED_MANIFEST_DOC_TYPE:
        return _emit_fail(R55, f"document_type must be {EXPECTED_MANIFEST_DOC_TYPE!r}"), None, None
    if manifest.get("schema_version") != EXPECTED_MANIFEST_SCHEMA_VERSION:
        return _emit_fail(R55, f"schema_version must be {EXPECTED_MANIFEST_SCHEMA_VERSION!r}"), None, None
    if manifest.get("proofrail_release") != EXPECTED_MANIFEST_RELEASE:
        return _emit_fail(R55, f"proofrail_release must be {EXPECTED_MANIFEST_RELEASE!r}"), None, None
    if manifest.get("hash_algorithm") != EXPECTED_HASH_ALGO:
        return _emit_fail(R55, f"hash_algorithm must be {EXPECTED_HASH_ALGO!r}"), None, None

    for f in _MANIFEST_GRAMMAR_FIELDS:
        val = manifest.get(f)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R55, f"{f} must be a non-empty string"), None, None
        if not PACKAGE_ID_RE.fullmatch(val):
            return _emit_fail(R55, f"{f} fails closed identifier grammar: {val!r}"), None, None

    # gold_reliance_package_index_ref and decision_report_ref string +
    # path-grammar checks. Path-traversal BEFORE exact-path equality.
    grpi_ref = manifest.get("gold_reliance_package_index_ref")
    if not isinstance(grpi_ref, str) or grpi_ref == "":
        return _emit_fail(R55, "gold_reliance_package_index_ref must be a non-empty string"), None, None
    if _has_traversal(grpi_ref):
        return _emit_fail(R55, f"gold_reliance_package_index_ref contains path traversal: {grpi_ref!r}"), None, None
    if os.path.isabs(grpi_ref):
        return _emit_fail(R55, f"gold_reliance_package_index_ref must be relative: {grpi_ref!r}"), None, None
    if grpi_ref != V045_SUBJECT_PATH_V044_MANIFEST:
        return _emit_fail(
            R55,
            f"gold_reliance_package_index_ref must equal {V045_SUBJECT_PATH_V044_MANIFEST!r}, got {grpi_ref!r}",
        ), None, None

    dr_ref = manifest.get("decision_report_ref")
    if not isinstance(dr_ref, str) or dr_ref == "":
        return _emit_fail(R55, "decision_report_ref must be a non-empty string"), None, None
    if _has_traversal(dr_ref):
        return _emit_fail(R55, f"decision_report_ref contains path traversal: {dr_ref!r}"), None, None
    if os.path.isabs(dr_ref):
        return _emit_fail(R55, f"decision_report_ref must be relative: {dr_ref!r}"), None, None
    if dr_ref != V045_DECISION_REPORT_REF:
        return _emit_fail(
            R55,
            f"decision_report_ref must equal {V045_DECISION_REPORT_REF!r}, got {dr_ref!r}",
        ), None, None

    if not ISO_8601_UTC_RE.fullmatch(manifest["generated_at"]):
        return _emit_fail(
            R55,
            f"generated_at must be ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ, got {manifest['generated_at']!r}",
        ), None, None

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return _emit_fail(R55, "subjects must be a JSON array"), None, None
    if len(subjects) != 2:
        return _emit_fail(R55, f"subjects must hold exactly 2 entries, got {len(subjects)}"), None, None
    for idx, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return _emit_fail(R55, f"subjects[{idx}] is not an object"), None, None
        role = subj.get("role")
        path = subj.get("path")
        sha = subj.get("sha256")
        size = subj.get("size_bytes")
        if role != EXPECTED_SUBJECT_ROLES[idx]:
            return _emit_fail(
                R55,
                f"subjects[{idx}].role must be {EXPECTED_SUBJECT_ROLES[idx]!r}, got {role!r}",
            ), None, None
        if not isinstance(path, str) or path == "":
            return _emit_fail(R55, f"subjects[{idx}].path must be a non-empty string"), None, None
        # Path-traversal check BEFORE path-equality check (non-masking).
        if _has_traversal(path):
            return _emit_fail(R55, f"subjects[{idx}].path contains path traversal: {path!r}"), None, None
        if os.path.isabs(path):
            return _emit_fail(R55, f"subjects[{idx}].path must be relative: {path!r}"), None, None
        if path != EXPECTED_SUBJECT_PATHS[idx]:
            return _emit_fail(
                R55,
                f"subjects[{idx}].path must equal {EXPECTED_SUBJECT_PATHS[idx]!r}, got {path!r}",
            ), None, None
        if not isinstance(sha, str) or not BARE_HEX_SHA256_RE.fullmatch(sha):
            return _emit_fail(R55, f"subjects[{idx}].sha256 must be bare lowercase hex SHA-256"), None, None
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            return _emit_fail(R55, f"subjects[{idx}].size_bytes must be a non-negative integer"), None, None

    return 0, manifest, raw


def _check_subject_digests(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    """R56: per-subject file-on-disk existence, size byte-match, sha256 byte-match."""
    for idx, subj in enumerate(manifest["subjects"]):
        subj_path = manifest_dir / subj["path"]
        if not subj_path.exists():
            return _emit_fail(R56, f"subjects[{idx}] file does not exist: {subj['path']!r}")
        try:
            body = subj_path.read_bytes()
        except OSError as e:
            return _emit_fail(R56, f"subjects[{idx}] cannot be read: {e}")
        if len(body) != subj["size_bytes"]:
            return _emit_fail(
                R56,
                f"subjects[{idx}] size mismatch: manifest={subj['size_bytes']}, actual={len(body)}",
            )
        if _sha256_hex(body) != subj["sha256"]:
            return _emit_fail(
                R56,
                f"subjects[{idx}] sha256 mismatch: manifest={subj['sha256']}, actual={_sha256_hex(body)}",
            )
    return 0


# ---------------------------------------------------------------------------
# Phase 2: v0.4.5 index body (subject [1]) checks (R57..R61).
#
# Locked check order (R55 -> R56 -> R57 -> R58 -> R59 -> R60 -> R61):
#   R57 (index_invalid)  for not-object / top-level schema-shape /
#                        closed value sets / closed identifier grammar /
#                        relying_party shape / ref-path checks
#                        (path-traversal before exact-path equality).
#   R58 (binding)        v0.4.5-body-to-v0.4.4-child cross-anchor for
#                        the v0.4.4 wrapping manifest ref + the v0.4.4
#                        index body SHA + the v0.4.1 decision-report
#                        body SHA + the relying_party byte-anchor.
#   R59 (case_count)     cases[] count + natural-order pin
#                        (case_index == array position).
#   R60 (case_binding)   per-case shape + per-case cross-anchor with
#                        v0.4.0/v0.4.1/v0.4.2/v0.4.3 inherited bodies.
#   R61 (rederive)       multi_case_index_fingerprint re-derivation
#                        (independent recomputation over canonical
#                        body without that field).
# ---------------------------------------------------------------------------

_INDEX_BODY_TOP_LEVEL_FIELDS = (
    "document_type",
    "schema_version",
    "proofrail_release",
    "hash_algorithm",
    "gold_multi_case_reliance_index_id",
    "package_id",
    "governed_reliance_demo_id",
    "gold_reliance_package_index_ref",
    "gold_reliance_package_index_sha256",
    "decision_report_ref",
    "decision_report_sha256",
    "generated_at",
    "relying_party",
    "cases",
    "multi_case_index_fingerprint",
)

_INDEX_BODY_GRAMMAR_FIELDS = (
    "gold_multi_case_reliance_index_id",
    "package_id",
    "governed_reliance_demo_id",
)

_CASE_REQUIRED_FIELDS = (
    "case_id",
    "case_slug",
    "case_index",
    "governed_decision_id",
    "decision_row_id",
    "matrix_row_id",
    "evaluation_row_id",
    "lifecycle_record_id",
    "lifecycle_record_fingerprint",
    "outcome",
)


def _check_index_body_shape(body: dict[str, Any]) -> int:
    """R57: top-level required fields, types, allowed value sets,
    closed identifier grammar, relying_party object shape, ref-path
    checks. Path-traversal before exact-path equality."""
    for f in _INDEX_BODY_TOP_LEVEL_FIELDS:
        if f not in body:
            return _emit_fail(R57, f"index body missing required field {f!r}")
    stray_top = set(body.keys()) - set(_INDEX_BODY_TOP_LEVEL_FIELDS)
    if stray_top:
        return _emit_fail(
            R57,
            f"index body has stray top-level keys (closed shape): {sorted(stray_top)!r}",
        )

    if body.get("document_type") != EXPECTED_INDEX_BODY_DOC_TYPE:
        return _emit_fail(R57, f"document_type must be {EXPECTED_INDEX_BODY_DOC_TYPE!r}")
    if body.get("schema_version") != EXPECTED_INDEX_BODY_SCHEMA_VERSION:
        return _emit_fail(R57, f"schema_version must be {EXPECTED_INDEX_BODY_SCHEMA_VERSION!r}")
    if body.get("proofrail_release") != EXPECTED_INDEX_BODY_RELEASE:
        return _emit_fail(R57, f"proofrail_release must be {EXPECTED_INDEX_BODY_RELEASE!r}")
    if body.get("hash_algorithm") != EXPECTED_HASH_ALGO:
        return _emit_fail(R57, f"hash_algorithm must be {EXPECTED_HASH_ALGO!r}")

    for f in _INDEX_BODY_GRAMMAR_FIELDS:
        v = body.get(f)
        if not isinstance(v, str) or v == "":
            return _emit_fail(R57, f"{f} must be a non-empty string")
        if not PACKAGE_ID_RE.fullmatch(v):
            return _emit_fail(R57, f"{f} fails closed identifier grammar: {v!r}")

    grpi_ref = body.get("gold_reliance_package_index_ref")
    if not isinstance(grpi_ref, str) or grpi_ref == "":
        return _emit_fail(R57, "gold_reliance_package_index_ref must be a non-empty string")
    if _has_traversal(grpi_ref):
        return _emit_fail(R57, f"gold_reliance_package_index_ref contains path traversal: {grpi_ref!r}")
    if os.path.isabs(grpi_ref):
        return _emit_fail(R57, f"gold_reliance_package_index_ref must be relative: {grpi_ref!r}")
    if grpi_ref != V045_SUBJECT_PATH_V044_MANIFEST:
        return _emit_fail(
            R57,
            f"gold_reliance_package_index_ref must equal {V045_SUBJECT_PATH_V044_MANIFEST!r}, got {grpi_ref!r}",
        )

    dr_ref = body.get("decision_report_ref")
    if not isinstance(dr_ref, str) or dr_ref == "":
        return _emit_fail(R57, "decision_report_ref must be a non-empty string")
    if _has_traversal(dr_ref):
        return _emit_fail(R57, f"decision_report_ref contains path traversal: {dr_ref!r}")
    if os.path.isabs(dr_ref):
        return _emit_fail(R57, f"decision_report_ref must be relative: {dr_ref!r}")
    if dr_ref != V045_DECISION_REPORT_REF:
        return _emit_fail(
            R57,
            f"decision_report_ref must equal {V045_DECISION_REPORT_REF!r}, got {dr_ref!r}",
        )

    grpi_sha = body.get("gold_reliance_package_index_sha256")
    if not isinstance(grpi_sha, str) or not BARE_HEX_SHA256_RE.fullmatch(grpi_sha):
        return _emit_fail(R57, "gold_reliance_package_index_sha256 must be bare lowercase hex SHA-256")
    dr_sha = body.get("decision_report_sha256")
    if not isinstance(dr_sha, str) or not BARE_HEX_SHA256_RE.fullmatch(dr_sha):
        return _emit_fail(R57, "decision_report_sha256 must be bare lowercase hex SHA-256")

    if not isinstance(body.get("generated_at"), str) or not ISO_8601_UTC_RE.fullmatch(body["generated_at"]):
        return _emit_fail(
            R57,
            f"generated_at must be ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ, got {body.get('generated_at')!r}",
        )

    rp = body.get("relying_party")
    if not isinstance(rp, dict):
        return _emit_fail(R57, "relying_party must be a JSON object")

    if not isinstance(body.get("cases"), list):
        return _emit_fail(R57, "cases must be a JSON array")

    fp = body.get("multi_case_index_fingerprint")
    if not isinstance(fp, str) or not BARE_HEX_SHA256_RE.fullmatch(fp):
        return _emit_fail(R57, "multi_case_index_fingerprint must be bare lowercase hex SHA-256")

    return 0


def _check_case_count(body: dict[str, Any]) -> int:
    """R59: cases[] count and natural-order pin."""
    cases = body["cases"]
    if len(cases) != 5:
        return _emit_fail(R59, f"cases must hold exactly 5 entries, got {len(cases)}")
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            return _emit_fail(R59, f"cases[{i}] is not an object")
        ci = case.get("case_index")
        # case_index must be a real integer (not bool) equal to i.
        if not isinstance(ci, int) or isinstance(ci, bool):
            return _emit_fail(R59, f"cases[{i}].case_index must be an integer (not bool)")
        if ci != i:
            return _emit_fail(R59, f"cases[{i}].case_index must equal {i}, got {ci!r}")
    return 0


def _check_per_case_bindings(
    *,
    body: dict[str, Any],
    manifest_dir: Path,
    v044_child_ids_for_distinctness: set[str],
) -> int:
    """R60: per-case shape and per-case cross-anchor with inherited bodies."""
    cases = body["cases"]

    # Per-case shape + closed value sets + case_id distinctness +
    # case_id distinctness from v0.4.4-child identifiers + paired-null
    # for lifecycle_record_id/lifecycle_record_fingerprint.
    seen_case_ids: set[str] = set()
    for i, case in enumerate(cases):
        for f in _CASE_REQUIRED_FIELDS:
            if f not in case:
                return _emit_fail(R60, f"cases[{i}] missing required field {f!r}")
        stray = set(case.keys()) - set(_CASE_REQUIRED_FIELDS)
        if stray:
            return _emit_fail(
                R60,
                f"cases[{i}] has stray keys (closed shape): {sorted(stray)!r}",
            )

        cid = case["case_id"]
        if not isinstance(cid, str) or cid == "":
            return _emit_fail(R60, f"cases[{i}].case_id must be a non-empty string")
        if not PACKAGE_ID_RE.fullmatch(cid):
            return _emit_fail(R60, f"cases[{i}].case_id fails closed identifier grammar: {cid!r}")
        if cid in seen_case_ids:
            return _emit_fail(R60, f"cases[{i}].case_id duplicates a prior case_id: {cid!r}")
        seen_case_ids.add(cid)
        if cid in v044_child_ids_for_distinctness:
            return _emit_fail(
                R60,
                f"cases[{i}].case_id collides with a v0.4.4-child identifier: {cid!r}",
            )

        case_slug = case["case_slug"]
        if case_slug not in SCENARIO_TYPES:
            return _emit_fail(R60, f"cases[{i}].case_slug not in closed scenario_type set: {case_slug!r}")
        outcome = case["outcome"]
        if outcome not in DECISION_STATUSES:
            return _emit_fail(R60, f"cases[{i}].outcome not in closed decision_status set: {outcome!r}")
        gdid = case["governed_decision_id"]
        if not isinstance(gdid, str) or gdid == "":
            return _emit_fail(R60, f"cases[{i}].governed_decision_id must be a non-empty string")
        drid = case["decision_row_id"]
        if not isinstance(drid, str) or drid == "":
            return _emit_fail(R60, f"cases[{i}].decision_row_id must be a non-empty string")

        # matrix_row_id and evaluation_row_id may be null, otherwise
        # must be non-empty strings.
        mrid = case["matrix_row_id"]
        if mrid is not None and (not isinstance(mrid, str) or mrid == ""):
            return _emit_fail(R60, f"cases[{i}].matrix_row_id must be null or a non-empty string")
        erid = case["evaluation_row_id"]
        if erid is not None and (not isinstance(erid, str) or erid == ""):
            return _emit_fail(R60, f"cases[{i}].evaluation_row_id must be null or a non-empty string")

        # lifecycle_record_id and lifecycle_record_fingerprint paired-null.
        lrid = case["lifecycle_record_id"]
        lrfp = case["lifecycle_record_fingerprint"]
        if (lrid is None) != (lrfp is None):
            return _emit_fail(
                R60,
                f"cases[{i}] lifecycle_record_id and lifecycle_record_fingerprint must both be null or both non-null",
            )
        if lrid is not None and (not isinstance(lrid, str) or lrid == ""):
            return _emit_fail(R60, f"cases[{i}].lifecycle_record_id must be null or a non-empty string")
        if lrfp is not None and (
            not isinstance(lrfp, str) or not BARE_HEX_SHA256_RE.fullmatch(lrfp)
        ):
            return _emit_fail(
                R60,
                f"cases[{i}].lifecycle_record_fingerprint must be null or bare lowercase hex SHA-256",
            )

    # Cross-anchor per-case fields with inherited bodies reached
    # through the v0.4.4 child closure.
    v040_body = _read_child_body(manifest_dir, V044_V040_REL)
    v041_body = _read_child_body(manifest_dir, V044_V041_REL)
    v042_body = _read_child_body(manifest_dir, V044_V042_REL)
    v043_body = _read_child_body(manifest_dir, V044_V043_REL)
    if v040_body is None or v041_body is None or v042_body is None or v043_body is None:
        return _emit_fail(
            R60,
            "one or more inherited bodies reached through v0.4.4 child closure unreadable as JSON object",
        )

    governed_decisions = v040_body.get("governed_decisions")
    if not isinstance(governed_decisions, list) or len(governed_decisions) != 5:
        return _emit_fail(
            R60,
            "v0.4.0 governed_decisions[] missing or not length 5 for per-case cross-anchor",
        )

    drows = v041_body.get("decision_rows") if isinstance(v041_body.get("decision_rows"), list) else []
    erows = v042_body.get("evaluation_rows") if isinstance(v042_body.get("evaluation_rows"), list) else []
    lrecs = v043_body.get("lifecycle_records") if isinstance(v043_body.get("lifecycle_records"), list) else []

    drow_by_did: dict[str, dict[str, Any]] = {}
    for r in drows:
        if isinstance(r, dict) and isinstance(r.get("decision_id"), str):
            drow_by_did[r["decision_id"]] = r
    erow_by_did: dict[str, dict[str, Any]] = {}
    for r in erows:
        if isinstance(r, dict) and isinstance(r.get("decision_id"), str):
            erow_by_did[r["decision_id"]] = r
    lrec_by_tdid: dict[str, dict[str, Any]] = {}
    for r in lrecs:
        if isinstance(r, dict) and isinstance(r.get("target_decision_id"), str):
            lrec_by_tdid[r["target_decision_id"]] = r

    for i, case in enumerate(cases):
        gd = governed_decisions[i]
        if not isinstance(gd, dict):
            return _emit_fail(R60, f"v0.4.0 governed_decisions[{i}] is not an object")
        if case["case_slug"] != gd.get("scenario_type"):
            return _emit_fail(
                R60,
                f"cases[{i}].case_slug mismatch v0.4.0 governed_decisions[{i}].scenario_type",
            )
        if case["governed_decision_id"] != gd.get("decision_id"):
            return _emit_fail(
                R60,
                f"cases[{i}].governed_decision_id mismatch v0.4.0 governed_decisions[{i}].decision_id",
            )
        if case["outcome"] != gd.get("decision_status"):
            return _emit_fail(
                R60,
                f"cases[{i}].outcome mismatch v0.4.0 governed_decisions[{i}].decision_status",
            )

        gdid = case["governed_decision_id"]
        drow = drow_by_did.get(gdid)
        if drow is None:
            return _emit_fail(
                R60,
                f"cases[{i}].governed_decision_id {gdid!r} has no matching v0.4.1 decision_rows[] entry",
            )
        if case["decision_row_id"] != drow.get("row_id"):
            return _emit_fail(
                R60,
                f"cases[{i}].decision_row_id mismatch v0.4.1 decision_rows[] entry row_id for decision_id {gdid!r}",
            )

        erow = erow_by_did.get(gdid)
        if erow is None:
            return _emit_fail(
                R60,
                f"cases[{i}].governed_decision_id {gdid!r} has no matching v0.4.2 evaluation_rows[] entry",
            )
        if case["matrix_row_id"] != erow.get("matrix_row_id"):
            return _emit_fail(
                R60,
                f"cases[{i}].matrix_row_id mismatch v0.4.2 evaluation_rows[].matrix_row_id for decision_id {gdid!r}",
            )
        if case["evaluation_row_id"] != erow.get("evaluation_row_id"):
            return _emit_fail(
                R60,
                f"cases[{i}].evaluation_row_id mismatch v0.4.2 evaluation_rows[].evaluation_row_id for decision_id {gdid!r}",
            )

        lrec = lrec_by_tdid.get(gdid)
        if lrec is None:
            if case["lifecycle_record_id"] is not None or case["lifecycle_record_fingerprint"] is not None:
                return _emit_fail(
                    R60,
                    f"cases[{i}] lifecycle_record_id/lifecycle_record_fingerprint must be null when v0.4.3 has no matching record for decision_id {gdid!r}",
                )
        else:
            if case["lifecycle_record_id"] != lrec.get("lifecycle_id"):
                return _emit_fail(
                    R60,
                    f"cases[{i}].lifecycle_record_id mismatch v0.4.3 lifecycle_records[].lifecycle_id for decision_id {gdid!r}",
                )
            if case["lifecycle_record_fingerprint"] != lrec.get("lifecycle_fingerprint"):
                return _emit_fail(
                    R60,
                    f"cases[{i}].lifecycle_record_fingerprint mismatch v0.4.3 lifecycle_records[].lifecycle_fingerprint for decision_id {gdid!r}",
                )

    return 0


def _check_child_manifest_binding(
    *,
    body: dict[str, Any],
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    """R58: v0.4.5 body cross-anchor with v0.4.4 child closure.

    - gold_reliance_package_index_ref byte-matches subjects[0].path
      and the wrapping manifest's gold_reliance_package_index_ref.
    - gold_reliance_package_index_sha256 byte-matches the SHA-256
      re-derived from the v0.4.4 index body file on disk.
    - decision_report_ref byte-matches the wrapping manifest's
      decision_report_ref.
    - decision_report_sha256 byte-matches the SHA-256 re-derived
      from the v0.4.1 decision-report body file reached through the
      v0.4.4 child closure.
    - relying_party byte-equals (after canonical-JSON re-encoding)
      the v0.4.0 body's relying_party object reached through the
      v0.4.4 child closure.
    - gold_multi_case_reliance_index_id, package_id, and
      governed_reliance_demo_id byte-match the wrapping manifest.
    """
    if body["gold_multi_case_reliance_index_id"] != manifest["gold_multi_case_reliance_index_id"]:
        return _emit_fail(
            R58,
            "index body gold_multi_case_reliance_index_id mismatch with v0.4.5 wrapping manifest",
        )
    if body["package_id"] != manifest["package_id"]:
        return _emit_fail(R58, "index body package_id mismatch with v0.4.5 wrapping manifest")
    if body["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(R58, "index body governed_reliance_demo_id mismatch with v0.4.5 wrapping manifest")

    if body["gold_reliance_package_index_ref"] != manifest["gold_reliance_package_index_ref"]:
        return _emit_fail(R58, "index body gold_reliance_package_index_ref mismatch with v0.4.5 wrapping manifest")
    if body["gold_reliance_package_index_ref"] != manifest["subjects"][0]["path"]:
        return _emit_fail(R58, "index body gold_reliance_package_index_ref mismatch with subjects[0].path")
    if body["decision_report_ref"] != manifest["decision_report_ref"]:
        return _emit_fail(R58, "index body decision_report_ref mismatch with v0.4.5 wrapping manifest")

    # SHA-256 re-derivation against on-disk v0.4.4 index body file.
    v044_index_body_path = manifest_dir / V044_CHILD_DIR / V044_INDEX_BODY_FILENAME
    if not v044_index_body_path.exists():
        return _emit_fail(
            R58,
            f"v0.4.4 index body file does not exist at {V044_CHILD_DIR}/{V044_INDEX_BODY_FILENAME}",
        )
    try:
        v044_index_body_bytes = v044_index_body_path.read_bytes()
    except OSError as e:
        return _emit_fail(R58, f"v0.4.4 index body file unreadable: {e}")
    expected_v044_idx_sha = _sha256_hex(v044_index_body_bytes)
    if body["gold_reliance_package_index_sha256"] != expected_v044_idx_sha:
        return _emit_fail(
            R58,
            f"gold_reliance_package_index_sha256 mismatch: declared={body['gold_reliance_package_index_sha256']!r}, "
            f"re-derived={expected_v044_idx_sha!r}",
        )

    # SHA-256 re-derivation against on-disk v0.4.1 decision-report body.
    dr_path = manifest_dir / body["decision_report_ref"]
    if not dr_path.exists():
        return _emit_fail(R58, f"v0.4.1 decision-report body file does not exist at {body['decision_report_ref']!r}")
    try:
        dr_bytes = dr_path.read_bytes()
    except OSError as e:
        return _emit_fail(R58, f"v0.4.1 decision-report body file unreadable: {e}")
    expected_dr_sha = _sha256_hex(dr_bytes)
    if body["decision_report_sha256"] != expected_dr_sha:
        return _emit_fail(
            R58,
            f"decision_report_sha256 mismatch: declared={body['decision_report_sha256']!r}, "
            f"re-derived={expected_dr_sha!r}",
        )

    # relying_party byte-equality (after canonical-JSON re-encoding)
    # with the v0.4.0 body's relying_party reached through the v0.4.4
    # child closure.
    v040_body = _read_child_body(manifest_dir, V044_V040_REL)
    if v040_body is None:
        return _emit_fail(R58, "v0.4.0 body reached through v0.4.4 child closure unreadable for relying_party anchor")
    expected_rp = v040_body.get("relying_party")
    if not isinstance(expected_rp, dict):
        return _emit_fail(R58, "v0.4.0 body relying_party missing or not an object")
    if _canonical_json_bytes_no_newline(body["relying_party"]) != _canonical_json_bytes_no_newline(expected_rp):
        return _emit_fail(
            R58,
            "index body relying_party byte-mismatch with v0.4.0 body relying_party (canonical-JSON compare)",
        )

    return 0


def _check_rederive_fingerprint(body: dict[str, Any]) -> int:
    """R61: independent re-derivation of multi_case_index_fingerprint."""
    body_without_fp = {k: v for k, v in body.items() if k != "multi_case_index_fingerprint"}
    expected_fp = _sha256_hex(_canonical_json_bytes_no_newline(body_without_fp))
    declared = body.get("multi_case_index_fingerprint")
    if declared != expected_fp:
        return _emit_fail(
            R61,
            f"multi_case_index_fingerprint mismatch: declared={declared!r}, re-derived={expected_fp!r}",
        )
    return 0


def _read_child_body(manifest_dir: Path, relpath: str) -> dict[str, Any] | None:
    """Read a closure body file from underneath child-packages/v0.4.4/."""
    full = manifest_dir / V044_CHILD_DIR / relpath
    try:
        raw = full.read_bytes()
    except OSError:
        return None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _collect_v044_child_ids(manifest_dir: Path) -> set[str]:
    """Collect the v0.4.4 wrapping manifest's identifier values for
    pairwise-distinctness vs v0.4.5 case_id values.

    Falls back to an empty set when the v0.4.4 manifest is unreadable;
    the inherited v0.4.4 verifier will surface that under R01..R54.
    """
    v044_manifest_path = manifest_dir / V045_SUBJECT_PATH_V044_MANIFEST
    try:
        raw = v044_manifest_path.read_bytes()
        obj = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    if not isinstance(obj, dict):
        return set()
    ids: set[str] = set()
    for f in (
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
    ):
        v = obj.get(f)
        if isinstance(v, str) and v != "":
            ids.add(v)
    return ids


def _check_index_body(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    body_path = manifest_dir / V045_INDEX_BODY_FILENAME
    try:
        raw = body_path.read_bytes()
    except OSError as e:
        # Subject readability was already verified under R56.
        return _emit_fail(R56, f"index body unreadable after subject digest check: {e}")
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R57, f"index body is not valid JSON: {e}")
    if not isinstance(body, dict):
        return _emit_fail(R57, "index body is not a JSON object")

    rc = _check_index_body_shape(body)
    if rc != 0:
        return rc
    rc = _check_child_manifest_binding(body=body, manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc
    rc = _check_case_count(body)
    if rc != 0:
        return rc
    v044_child_ids = _collect_v044_child_ids(manifest_dir)
    rc = _check_per_case_bindings(
        body=body,
        manifest_dir=manifest_dir,
        v044_child_ids_for_distinctness=v044_child_ids,
    )
    if rc != 0:
        return rc
    rc = _check_rederive_fingerprint(body)
    if rc != 0:
        return rc
    return 0


# ---------------------------------------------------------------------------
# Phase 3: subprocess-invoke the v0.4.4 verifier on the v0.4.4 child
# wrapping-manifest path. R01..R54 are relayed verbatim. A missing or
# unlaunchable v0.4.4 verifier, or one that exits with a non-FAIL
# non-zero code, is treated as INFRA exit 3, never as a public
# v0.4.5 reason name.
# ---------------------------------------------------------------------------

def _run_inherited_v044(*, manifest_dir: Path) -> int:
    child_manifest_path = manifest_dir / V045_SUBJECT_PATH_V044_MANIFEST
    if not GOLD_V044_VERIFIER.exists():
        return _emit_infra(
            f"co-located v0.4.4 verifier unavailable for inherited check delegation: "
            f"expected at {GOLD_V044_VERIFIER}"
        )
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(GOLD_V044_VERIFIER),
                "--manifest",
                str(child_manifest_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (FileNotFoundError, PermissionError, OSError) as e:
        return _emit_infra(
            f"co-located v0.4.4 verifier unavailable for inherited check delegation: "
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
    # Any non-1 non-zero exit from the v0.4.4 verifier is INFRA (its
    # own exit 3 or a crash). MUST NOT collapse into a public v0.4.5
    # reason name.
    return _emit_infra(
        f"inherited v0.4.4 verifier exited with non-FAIL non-zero code {result.returncode}"
    )


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Gold v0.4.5 Multi-Case Reliance Demo package.",
    )
    parser.add_argument("--manifest", type=str, required=True,
                        help="Path to the v0.4.5 wrapping manifest gold-multi-case-reliance-package-manifest.json.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent

    # Phase 1a: v0.4.5 wrapping manifest structural integrity (R55).
    rc, manifest, _raw = _check_manifest_structure(manifest_path)
    if rc != 0 or manifest is None:
        return rc

    # Phase 1b: per-subject file-on-disk digest checks (R56).
    rc = _check_subject_digests(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 2: v0.4.5 index body checks (R57..R61). Owned by v0.4.5
    # and validated BEFORE invoking the inherited v0.4.4 verifier so
    # that the v0.4.5-owned reasons are reachable without
    # contaminating any inherited verifier's namespace.
    rc = _check_index_body(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 3: inherited v0.4.4 verifier via subprocess (R01..R54
    # relayed verbatim; INFRA exit 3 on env failure or non-FAIL
    # non-zero inherited exit).
    rc = _run_inherited_v044(manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    sys.stdout.write("PASS: gold v0.4.5 multi-case reliance demo package verified\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
