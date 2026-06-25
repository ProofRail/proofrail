#!/usr/bin/env python3
"""Verify a ProofRail Gold v0.4.1 Decision Report Hardening package.

The v0.4.1 verifier extends the v0.4.0 Minimal Gold Governed Reliance
Demo verifier with five new ordered checks against a v0.4.1 decision
report subject. The v0.4.1 verifier DELEGATES inherited checks to the
co-located v0.4.0 verifier (`verify_gold_governed_reliance_demo_v0_1_0.py`
under the same `tools/gold/` directory) via subprocess against a
synthesized 2-subject v0.4.0 manifest so the inherited 24 v0.4.0
structural checks run without duplication. This is a repo tooling
dependency: any change to the co-located v0.4.0 verifier requires
rerunning BOTH the v0.4.0 and v0.4.1 regression suites. A missing or
unlaunchable v0.4.0 verifier is treated as an ENVIRONMENT failure and
emits a non-reason-shaped `INFRA:` diagnostic to stderr; it MUST NOT
collapse into any of the 29 public verifier reason names or the 5
runner-only refusal names.

Public failure reasons (closed set of 29, verbatim from the v0.4.1
spec, with 24 inherited from v0.4.0 and 5 introduced by v0.4.1):

  Inherited from v0.4.0 (relayed verbatim from the v0.4.0 verifier or
  emitted directly by v0.4.1 manifest-integrity checks):

  01 gold_manifest_invalid                       (also: v0.4.1 manifest
                                                  shape, cross-anchors,
                                                  conformance-report
                                                  byte disagreement,
                                                  identifier collisions)
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

  Introduced by v0.4.1:

  25 gold_decision_report_not_object
  26 gold_decision_report_schema_invalid
  27 gold_decision_report_binding_invalid
  28 gold_decision_report_projection_invalid
  29 gold_decision_report_summary_invalid

The verifier never emits the 5 runner-only refusal reasons
(`runner_input_*`).

Reachability ordering:

  - v0.4.1 manifest integrity (all 01 folds) runs FIRST, BEFORE
    subprocess-invoking the v0.4.0 verifier.
  - The subprocess-invoked v0.4.0 verifier runs the inherited 24
    checks (02..24, plus its own 01 folds).
  - v0.4.1 cross-anchor checks (folding to 01) run AFTER the v0.4.0
    verifier passes.
  - The 5 v0.4.1 decision-report checks (25..29) run AFTER the
    cross-anchor checks pass, in fixed order.
  - check_25 fires BEFORE check_26 (shape before schema).
  - check_26 fires BEFORE check_27 (schema before binding).
  - check_27 fires BEFORE check_28 (binding before projection).
  - check_28 fires BEFORE check_29 (projection before summary).
  - Path traversal is checked BEFORE exact subject path equality.

A v0.4.1 package is NOT a certificate, NOT signed, NOT federated, NOT
a transfer of reliance, and NOT full Gold.
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
# 29 approved verifier failure reasons (closed set, verbatim).
# ---------------------------------------------------------------------------

R01 = "gold_manifest_invalid"
R02 = "gold_package_not_object"
R03 = "gold_package_schema_invalid"
R04 = "gold_profile_unsupported"
R05 = "gold_package_identity_invalid"
R06 = "silver_verification_input_invalid"
R07 = "silver_handoff_input_invalid"
R08 = "policy_pack_input_invalid"
R09 = "registry_lite_input_invalid"
R10 = "control_crosswalk_input_invalid"
R11 = "governed_decision_set_invalid"
R12 = "governed_decision_entry_invalid"
R13 = "decision_subject_binding_invalid"
R14 = "decision_policy_binding_invalid"
R15 = "decision_registry_binding_invalid"
R16 = "decision_action_scope_invalid"
R17 = "decision_status_invalid"
R18 = "acceptance_path_invalid"
R19 = "rejection_path_invalid"
R20 = "challenge_path_invalid"
R21 = "withdrawal_path_invalid"
R22 = "supersession_path_invalid"
R23 = "non_claims_missing"
R24 = "prohibited_gold_claim_present"
R25 = "gold_decision_report_not_object"
R26 = "gold_decision_report_schema_invalid"
R27 = "gold_decision_report_binding_invalid"
R28 = "gold_decision_report_projection_invalid"
R29 = "gold_decision_report_summary_invalid"

APPROVED_V041_REASONS = (
    R01, R02, R03, R04, R05, R06, R07, R08, R09, R10,
    R11, R12, R13, R14, R15, R16, R17, R18, R19, R20,
    R21, R22, R23, R24, R25, R26, R27, R28, R29,
)

# Closed runner-only refusal set; the verifier never emits these.
RUNNER_ONLY_REFUSALS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

# ---------------------------------------------------------------------------
# Closed constants for v0.4.1.
# ---------------------------------------------------------------------------

EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.decision_report_package_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_RELEASE = "gold.decision_report_hardening.v0.4.1"
EXPECTED_HASH_ALGO = "sha256"

EXPECTED_DECISION_DOC_TYPE = "proofrail.gold.governed_reliance_decision_report"
EXPECTED_DECISION_SCHEMA_VERSION = "v0.1.0"
EXPECTED_DECISION_PROFILE = "gold.decision_report_hardening.v0.4.1"

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"

EXPECTED_SUBJECT_PATHS = (
    PACKAGE_SUBJECT_PATH,
    CONFORMANCE_SUBJECT_PATH,
    DECISION_SUBJECT_PATH,
)
EXPECTED_SUBJECT_ROLES = (
    "governed_reliance_package",
    "conformance_report",
    "decision_report",
)

# Closed identifier grammars.
PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
BARE_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ---------------------------------------------------------------------------
# Module constant exposing the v0.4.0 verifier path (subprocess-invoked).
# ---------------------------------------------------------------------------

GOLD_V040_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_governed_reliance_demo_v0_1_0.py"
)


# ---------------------------------------------------------------------------
# Fail helpers.
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
# Phase 1: v0.4.1 manifest structural integrity. All folds emit R01.
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
        "package_id",
        "governed_reliance_demo_id",
        "generated_at",
    ):
        val = manifest.get(field)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R01, f"{field} must be a non-empty string"), None

    # Grammar check on v0.4.1-owned identifiers only. The inherited identifiers
    # package_id and governed_reliance_demo_id have their grammar validated by
    # the inherited v0.4.0 R05 check (gold_package_identity_invalid) on the
    # package body; Phase 3 cross-anchors enforce manifest equals body for
    # those two fields, so a body-grammar fail surfaces as v0.4.0 R05 verbatim.
    for field in ("manifest_id", "conformance_report_id", "decision_report_id"):
        if not PACKAGE_ID_RE.fullmatch(manifest[field]):
            return _emit_fail(R01, f"{field} fails closed identifier grammar: {manifest[field]!r}"), None

    # Identifier distinctness: conformance_report_id != decision_report_id.
    if manifest["conformance_report_id"] == manifest["decision_report_id"]:
        return _emit_fail(
            R01,
            "conformance_report_id and decision_report_id must be distinct",
        ), None

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return _emit_fail(R01, "subjects must be a JSON array"), None
    if len(subjects) != 3:
        return _emit_fail(R01, f"subjects must hold exactly 3 entries, got {len(subjects)}"), None

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
        # Path traversal BEFORE exact-path equality.
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

    # File-on-disk checks for all three subjects, with hash and size cross-checks.
    manifest_dir = manifest_path.parent
    for idx, subj in enumerate(subjects):
        subj_path = manifest_dir / subj["path"]
        if not subj_path.exists():
            return _emit_fail(R01, f"subjects[{idx}] file does not exist: {subj['path']!r}"), None
        try:
            body = subj_path.read_bytes()
        except OSError as e:
            return _emit_fail(R01, f"subjects[{idx}] cannot be read: {e}"), None
        actual_size = len(body)
        if actual_size != subj["size_bytes"]:
            return _emit_fail(
                R01,
                f"subjects[{idx}] size mismatch: manifest={subj['size_bytes']}, actual={actual_size}",
            ), None
        actual_sha = _sha256_hex(body)
        if actual_sha != subj["sha256"]:
            return _emit_fail(
                R01,
                f"subjects[{idx}] sha256 mismatch: manifest={subj['sha256']}, actual={actual_sha}",
            ), None

    return 0, manifest


# ---------------------------------------------------------------------------
# Phase 2: subprocess-invoke the unchanged v0.4.0 verifier on a synthesized
# 2-subject v0.4.0 manifest. The v0.4.0 verifier emits reasons 02..24
# verbatim; its R01 folds are relayed verbatim too (the v0.4.0 manifest is
# synthesized by this verifier, so any v0.4.0 R01 reflects an inherited
# defect surfaced through v0.4.0).
# ---------------------------------------------------------------------------

def _run_inherited_v040_checks(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> int:
    package_subj = manifest["subjects"][0]
    conformance_subj = manifest["subjects"][1]
    package_path = manifest_dir / package_subj["path"]
    conformance_path = manifest_dir / conformance_subj["path"]
    if not package_path.exists() or not conformance_path.exists():
        return _emit_fail(R01, "subject file missing prior to inherited v0.4.0 verification")

    # Synthesize a v0.4.0 manifest that the unchanged v0.4.0 verifier will
    # accept. The v0.4.0 manifest's `report_id` cross-anchors to the
    # conformance report's `report_id`, which the v0.4.1 runner set to the
    # v0.4.1 manifest's `conformance_report_id`. Reuse the v0.4.1
    # manifest_id as the v0.4.0 manifest_id (both are local identifiers
    # under the same closed grammar).
    v040_manifest = {
        "document_type": "proofrail.gold.governed_reliance_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.governed_reliance.v0.4.0",
        "hash_algorithm": "sha256",
        "manifest_id": manifest["manifest_id"],
        "report_id": manifest["conformance_report_id"],
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
        ],
    }

    with tempfile.TemporaryDirectory(prefix="v041_inherited_") as td:
        td_path = Path(td)
        # Byte-copy the two v0.4.0-shaped subjects into the temp directory.
        shutil.copyfile(package_path, td_path / PACKAGE_SUBJECT_PATH)
        shutil.copyfile(conformance_path, td_path / CONFORMANCE_SUBJECT_PATH)
        synthesized_manifest_path = td_path / "gold-governed-reliance-package-manifest.json"
        synthesized_manifest_path.write_bytes(_canonical_json_bytes(v040_manifest))

        # Repo tooling dependency: the co-located v0.4.0 verifier must exist
        # and be invocable. A missing or unlaunchable sibling verifier is an
        # ENVIRONMENT failure, not a package-conformance defect. The handler
        # below emits a non-reason-shaped diagnostic to stderr and returns
        # a non-zero exit code. It deliberately does NOT emit any of the
        # 29 verifier reason names or the 5 runner-only refusal names,
        # because doing so would let environment issues masquerade as
        # package defects.
        if not GOLD_V040_VERIFIER.exists():
            sys.stderr.write(
                "INFRA: co-located v0.4.0 verifier unavailable for inherited "
                f"check delegation: expected at {GOLD_V040_VERIFIER}\n"
            )
            return 2
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(GOLD_V040_VERIFIER),
                    "--manifest",
                    str(synthesized_manifest_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            sys.stderr.write(
                "INFRA: co-located v0.4.0 verifier unavailable for inherited "
                f"check delegation: {type(e).__name__}: {e}\n"
            )
            return 2
        if result.returncode != 0:
            # Relay v0.4.0 verifier's output unchanged. Its FAIL line uses
            # one of the 24 inherited reason names verbatim.
            if result.stdout:
                sys.stdout.buffer.write(result.stdout)
            if result.stderr:
                sys.stderr.buffer.write(result.stderr)
            return result.returncode
    return 0


# ---------------------------------------------------------------------------
# Phase 3: v0.4.1 cross-anchor checks. All folds emit R01.
# ---------------------------------------------------------------------------

def _check_cross_anchors(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
) -> tuple[int, dict[str, Any] | None]:
    package_path = manifest_dir / PACKAGE_SUBJECT_PATH
    try:
        package_obj = json.loads(package_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"package body unreadable for cross-anchor check: {e}"), None
    if not isinstance(package_obj, dict):
        return _emit_fail(R01, "package body is not an object for cross-anchor check"), None

    if package_obj.get("package_id") != manifest["package_id"]:
        return _emit_fail(
            R01,
            f"package_id cross-anchor mismatch: manifest={manifest['package_id']!r}, "
            f"package={package_obj.get('package_id')!r}",
        ), None
    if package_obj.get("governed_reliance_demo_id") != manifest["governed_reliance_demo_id"]:
        return _emit_fail(
            R01,
            f"governed_reliance_demo_id cross-anchor mismatch: "
            f"manifest={manifest['governed_reliance_demo_id']!r}, "
            f"package={package_obj.get('governed_reliance_demo_id')!r}",
        ), None
    return 0, package_obj


# ---------------------------------------------------------------------------
# Phase 4: the five new v0.4.1 decision-report checks (R25..R29).
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


def _derive_expected_rows(governed_decisions: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, entry in enumerate(governed_decisions):
        if not isinstance(entry, dict):
            rows.append({})
            continue
        scenario_type = entry.get("scenario_type")
        decision_status = entry.get("decision_status")
        rows.append({
            "row_id": f"row_{idx + 1:02d}",
            "source_decision_index": idx,
            "decision_id": entry.get("decision_id"),
            "scenario_type": scenario_type,
            "decision_status": decision_status,
            "decision_trigger": entry.get("decision_trigger"),
            "recorded_at": entry.get("recorded_at"),
            "decision_subject": entry.get("decision_subject"),
            "policy_binding": entry.get("policy_binding"),
            "registry_binding": entry.get("registry_binding"),
            "action_scope": entry.get("action_scope"),
            "scenario_path_summary": f"{scenario_type}:{decision_status}",
            "decision_fingerprint": _decision_fingerprint(entry),
        })
    return rows


def _derive_expected_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
    fp_list = [r.get("decision_fingerprint", "") for r in rows]
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


def _check_decision_report(
    *,
    manifest: dict[str, Any],
    manifest_dir: Path,
    package_obj: dict[str, Any],
) -> int:
    decision_path = manifest_dir / DECISION_SUBJECT_PATH
    try:
        raw = decision_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"decision report file unreadable: {e}")

    # check_25 gold_decision_report_not_object
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R25, f"decision report is not valid JSON: {e}")
    if not isinstance(report, dict):
        return _emit_fail(R25, "decision report is not a JSON object")

    # check_26 gold_decision_report_schema_invalid
    if report.get("document_type") != EXPECTED_DECISION_DOC_TYPE:
        return _emit_fail(R26, f"document_type must be {EXPECTED_DECISION_DOC_TYPE!r}")
    if report.get("schema_version") != EXPECTED_DECISION_SCHEMA_VERSION:
        return _emit_fail(R26, f"schema_version must be {EXPECTED_DECISION_SCHEMA_VERSION!r}")
    if report.get("profile") != EXPECTED_DECISION_PROFILE:
        return _emit_fail(R26, f"profile must be {EXPECTED_DECISION_PROFILE!r}")
    for field in (
        "package_id",
        "governed_reliance_demo_id",
        "decision_report_id",
        "generated_at",
        "source_package_sha256",
    ):
        val = report.get(field)
        if not isinstance(val, str) or val == "":
            return _emit_fail(R26, f"{field} must be a non-empty string")
    for field in ("package_id", "governed_reliance_demo_id", "decision_report_id"):
        if not PACKAGE_ID_RE.fullmatch(report[field]):
            return _emit_fail(R26, f"{field} fails closed identifier grammar: {report[field]!r}")
    if not BARE_HEX_SHA256_RE.fullmatch(report["source_package_sha256"]):
        return _emit_fail(R26, "source_package_sha256 must be bare lowercase hex SHA-256")
    if not isinstance(report.get("decision_count"), int) or report["decision_count"] < 0:
        return _emit_fail(R26, "decision_count must be a non-negative integer")
    if not isinstance(report.get("decision_rows"), list):
        return _emit_fail(R26, "decision_rows must be a JSON array")
    if not isinstance(report.get("coverage_summary"), dict):
        return _emit_fail(R26, "coverage_summary must be a JSON object")
    for field in ("scope_limitations", "non_claims"):
        val = report.get(field)
        if not isinstance(val, list) or len(val) == 0:
            return _emit_fail(R26, f"{field} must be a non-empty array")
        for s in val:
            if not isinstance(s, str) or s.strip() == "":
                return _emit_fail(R26, f"{field} entries must be non-blank strings")

    # check_27 gold_decision_report_binding_invalid
    if report["package_id"] != manifest["package_id"]:
        return _emit_fail(
            R27,
            f"decision report package_id mismatch: report={report['package_id']!r}, "
            f"manifest={manifest['package_id']!r}",
        )
    if report["governed_reliance_demo_id"] != manifest["governed_reliance_demo_id"]:
        return _emit_fail(
            R27,
            f"decision report governed_reliance_demo_id mismatch: "
            f"report={report['governed_reliance_demo_id']!r}, "
            f"manifest={manifest['governed_reliance_demo_id']!r}",
        )
    if report["decision_report_id"] != manifest["decision_report_id"]:
        return _emit_fail(
            R27,
            f"decision report decision_report_id mismatch: "
            f"report={report['decision_report_id']!r}, "
            f"manifest={manifest['decision_report_id']!r}",
        )
    expected_source_sha = manifest["subjects"][0]["sha256"]
    if report["source_package_sha256"] != expected_source_sha:
        return _emit_fail(
            R27,
            f"decision report source_package_sha256 mismatch: "
            f"report={report['source_package_sha256']!r}, "
            f"manifest subjects[0].sha256={expected_source_sha!r}",
        )
    governed_decisions = package_obj.get("governed_decisions", [])
    if not isinstance(governed_decisions, list):
        return _emit_fail(
            R27,
            "package body governed_decisions is not a list (cannot bind decision_count)",
        )
    if report["decision_count"] != len(governed_decisions):
        return _emit_fail(
            R27,
            f"decision_count binding mismatch: report={report['decision_count']}, "
            f"package governed_decisions length={len(governed_decisions)}",
        )
    if len(report["decision_rows"]) != len(governed_decisions):
        return _emit_fail(
            R27,
            f"decision_rows length binding mismatch: report={len(report['decision_rows'])}, "
            f"package governed_decisions length={len(governed_decisions)}",
        )

    # check_28 gold_decision_report_projection_invalid
    expected_rows = _derive_expected_rows(governed_decisions)
    actual_rows = report["decision_rows"]
    # Byte-compare row-by-row to surface the first projection drift with
    # row index detail.
    for idx, (exp, act) in enumerate(zip(expected_rows, actual_rows)):
        if _canonical_json_bytes(act) != _canonical_json_bytes(exp):
            return _emit_fail(
                R28,
                f"decision_rows[{idx}] projection mismatch: "
                f"re-derived row does not match published row",
            )
    # Also enforce that mirrored top-level scope_limitations / non_claims
    # come from the package body (substantive drift would surface here).
    expected_scope = package_obj.get("scope_limitations")
    expected_nc = package_obj.get("non_claims")
    if expected_scope is not None and report["scope_limitations"] != expected_scope:
        return _emit_fail(
            R28,
            "scope_limitations projection mismatch (decision report drifts from package body)",
        )
    if expected_nc is not None and report["non_claims"] != expected_nc:
        return _emit_fail(
            R28,
            "non_claims projection mismatch (decision report drifts from package body)",
        )

    # check_29 gold_decision_report_summary_invalid
    expected_coverage = _derive_expected_coverage(expected_rows)
    actual_coverage = report["coverage_summary"]
    if _canonical_json_bytes(actual_coverage) != _canonical_json_bytes(expected_coverage):
        return _emit_fail(
            R29,
            "coverage_summary mismatch: re-derived summary does not match published summary",
        )

    # Final byte-compare: the entire decision report must match the
    # re-derived report when projected from the package body. This is the
    # "normalized projection" guarantee. Any drift not already isolated by
    # the row/summary checks above surfaces as R28 (projection invariant).
    expected_report = {
        "document_type": EXPECTED_DECISION_DOC_TYPE,
        "schema_version": EXPECTED_DECISION_SCHEMA_VERSION,
        "profile": EXPECTED_DECISION_PROFILE,
        "package_id": report["package_id"],
        "governed_reliance_demo_id": report["governed_reliance_demo_id"],
        "decision_report_id": report["decision_report_id"],
        "generated_at": report["generated_at"],
        "source_package_sha256": report["source_package_sha256"],
        "decision_count": len(expected_rows),
        "decision_rows": expected_rows,
        "coverage_summary": expected_coverage,
        "scope_limitations": expected_scope if expected_scope is not None else report["scope_limitations"],
        "non_claims": expected_nc if expected_nc is not None else report["non_claims"],
    }
    if _canonical_json_bytes(expected_report) != raw:
        return _emit_fail(
            R28,
            "decision report byte image diverges from re-derived projection",
        )
    return 0


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Gold v0.4.1 Decision Report Hardening package.",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the v0.4.1 manifest gold-decision-report-package-manifest.json.",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent

    # Phase 1: v0.4.1 manifest integrity (R01 folds).
    rc, manifest = _check_manifest(manifest_path)
    if rc != 0 or manifest is None:
        return rc

    # Phase 2: inherited v0.4.0 24 structural checks.
    rc = _run_inherited_v040_checks(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0:
        return rc

    # Phase 3: cross-anchor checks (R01 folds).
    rc, package_obj = _check_cross_anchors(manifest=manifest, manifest_dir=manifest_dir)
    if rc != 0 or package_obj is None:
        return rc

    # Phase 4: 5 new decision-report checks (R25..R29).
    rc = _check_decision_report(
        manifest=manifest,
        manifest_dir=manifest_dir,
        package_obj=package_obj,
    )
    if rc != 0:
        return rc

    sys.stdout.write("PASS: gold v0.4.1 decision report hardening package verified\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
