#!/usr/bin/env python3
"""Verify a ProofRail Minimal Gold v0.4.0 Governed Reliance Demo package.

The verifier runs 24 ordered structural checks against a v0.4.0
package, followed by a 25th post-structural conformance-report
byte-compare re-derivation. Disagreement on the re-derivation surfaces
as `gold_manifest_invalid` (reason 01); a 25th public reason is NOT
introduced.

Public failure reasons (closed set of 24, verbatim from the v0.4.0
spec):

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

The verifier never emits the 5 runner-only refusal reasons
(`runner_input_*`).

Non-masking reachability ordering:
  - manifest integrity (01) before package body parse
  - package body presence/type (02–05) before input block checks
  - input block (06–10) before governed decisions (11+)
  - set-level (11) before entry-level (12–17)
  - 13/14/15/16 are dedicated per-binding reasons that never collapse
    into 12
  - scenario-path checks (18–22) fire only AFTER all entries pass
    structural checks; one dedicated reason per scenario
  - non_claims (23) and prohibited (24) at the end
  - path traversal is checked BEFORE exact subject path equality
  - conformance-report byte-compare re-derivation is the 25th
    execution step; disagreement funnels into reason 01.

A v0.4.0 package is NOT a certificate, NOT signed, NOT federated, NOT
a transfer of reliance, and NOT full Gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 24 approved verifier failure reasons (closed set, verbatim).
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

APPROVED_VERIFIER_REASONS_ORDERED = (
    R01, R02, R03, R04, R05, R06, R07, R08,
    R09, R10, R11, R12, R13, R14, R15, R16,
    R17, R18, R19, R20, R21, R22, R23, R24,
)

# Static check_name descriptions (must match the runner's exactly so the
# conformance-report byte image is identical).
_CHECK_DETAILS = {
    R01: "Manifest shape, two-subject layout, paths, and cross-anchors pass.",
    R02: "Package body parses to a JSON object.",
    R03: "Package body declares document_type proofrail.gold.governed_reliance_package and schema_version v0.1.0.",
    R04: "Package profile is the closed v0.4.0 value gold.governed_reliance.v0.4.0.",
    R05: "package_id, governed_reliance_demo_id, and relying_party.identity_id satisfy the closed identifier grammar.",
    R06: "silver_verification input shape and expected_status pass.",
    R07: "silver_handoff input shape and expected_handoff_posture pass.",
    R08: "policy_pack input shape, policy_pack_id, and policy_pack_version pass.",
    R09: "registry_lite input shape and registry_id pass.",
    R10: "control_crosswalk input shape and control_pack_id pass.",
    R11: "governed_decisions list holds 1..5 entries in natural order with unique scenario_type values.",
    R12: "Each governed decision entry holds the required fields under the closed grammar.",
    R13: "Each decision_subject block holds a closed subject_type and a subject_ref.",
    R14: "Each policy_binding block holds policy_pack_id, policy_pack_version, policy_clause_refs, and a closed policy_decision.",
    R15: "Each registry_binding block holds relying_party_id and a closed decision_authority_role.",
    R16: "Each action_scope block holds a closed protected_action_id, action_category, and action_environment.",
    R17: "Each decision_status value is in the closed status set and matches its scenario_type.",
    R18: "The clean_acceptance entry's scenario_specific_state holds a non-empty acceptance_record_ref.",
    R19: "The policy_rejection entry's scenario_specific_state holds a closed rejection_reason and silver_verification_passing true.",
    R20: "The challenge_filed entry's scenario_specific_state holds a non-empty challenge_record_ref and a closed challenge_state.",
    R21: "The withdrawal entry's scenario_specific_state holds a non-empty withdrawal_record_ref and a closed withdrawal_trigger.",
    R22: "The supersession entry's scenario_specific_state holds a closed prior_decision_ref_kind, a resolvable prior_decision_id (when internal), a closed supersession_trigger, and a non-empty superseding_input_ref.",
    R23: "non_claims is present and non-empty.",
    R24: "No prohibited Gold-claim token appears outside scope_limitations or non_claims.",
}

# ---------------------------------------------------------------------------
# Closed vocabularies.
# ---------------------------------------------------------------------------

EXPECTED_PACKAGE_DOC_TYPE = "proofrail.gold.governed_reliance_package"
EXPECTED_PACKAGE_SCHEMA_VERSION = "v0.1.0"
EXPECTED_PROFILE = "gold.governed_reliance.v0.4.0"
EXPECTED_MANIFEST_DOC_TYPE = "proofrail.gold.governed_reliance_package_manifest"
EXPECTED_MANIFEST_SCHEMA_VERSION = "v0.1.0"
EXPECTED_MANIFEST_PROOFRAIL_RELEASE = "gold.governed_reliance.v0.4.0"
EXPECTED_MANIFEST_HASH_ALGO = "sha256"

EXPECTED_REPORT_DOC_TYPE = "proofrail.gold.governed_reliance_conformance_report"
EXPECTED_REPORT_SCHEMA_VERSION = "v0.1.0"

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
REPORT_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"

# Identifier grammars.
PACKAGE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
DOTTED_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")

SUPPORTED_PROFILES = {EXPECTED_PROFILE}

# silver_verification
INPUT_TYPE_SILVER_VERIFICATION = "silver_verification_result"
EXPECTED_STATUS_SET = {"pass"}

# silver_handoff
INPUT_TYPE_SILVER_HANDOFF = "silver_acceptance_handoff"
EXPECTED_HANDOFF_POSTURE_SET = {
    "for_demo_scope",
    "review_required_before_reuse",
    "not_reusable_without_governed_review",
}

# policy_pack
INPUT_TYPE_POLICY_PACK = "silver_relying_party_policy_pack"

# registry_lite
INPUT_TYPE_REGISTRY_LITE = "silver_registry_lite"

# control_crosswalk
INPUT_TYPE_CONTROL_CROSSWALK = "silver_control_crosswalk"

# decision_status
DECISION_STATUS_SET = {
    "accepted", "rejected", "challenged", "withdrawn", "superseded",
}

# scenario_type natural order
SCENARIO_TYPES_ORDERED = (
    "clean_acceptance",
    "policy_rejection",
    "challenge_filed",
    "withdrawal",
    "supersession",
)
SCENARIO_TYPE_TO_INDEX = {st: i for i, st in enumerate(SCENARIO_TYPES_ORDERED)}

# scenario_type -> required decision_status
SCENARIO_TO_STATUS = {
    "clean_acceptance": "accepted",
    "policy_rejection": "rejected",
    "challenge_filed": "challenged",
    "withdrawal": "withdrawn",
    "supersession": "superseded",
}

# decision_subject.subject_type
SUBJECT_TYPE_SET = {
    "silver_verification_result",
    "silver_acceptance_handoff",
    "challenge_withdrawal_record",
}

# policy_binding.policy_decision
POLICY_DECISION_SET = {"allow", "deny", "conditional", "withhold", "review"}

# registry_binding.decision_authority_role
DECISION_AUTHORITY_ROLE_SET = {
    "issuer",
    "verifier",
    "relying_party",
    "policy_authority",
    "revocation_source",
    "protected_action_authority",
}

# decision_trigger
DECISION_TRIGGER_SET = {
    "evidence_verified",
    "policy_evaluated",
    "challenge_received",
    "revocation_observed",
    "evidence_defect_observed",
    "updated_evidence_received",
    "updated_policy_received",
}

# action_scope
ACTION_CATEGORY_SET = {
    "financial_release",
    "data_export",
    "deployment_change",
    "secret_rotation",
    "vendor_approval",
}
ACTION_ENVIRONMENT_SET = {"demo", "staging", "production_simulated"}
PROTECTED_ACTION_ID_SET = {
    "release_payment",
    "export_data",
    "change_deployment",
    "rotate_secret",
    "approve_vendor",
}

# scenario-specific enums
REJECTION_REASON_SET = {
    "policy_scope_excluded",
    "posture_below_threshold",
    "evidence_outside_environment",
    "relying_party_excluded",
    "action_not_authorized",
}
CHALLENGE_STATE_SET = {"open", "under_review", "closed_resolved", "closed_withdrawn"}
WITHDRAWAL_TRIGGER_SET = {
    "challenge_filed",
    "revocation_observed",
    "evidence_defect_observed",
}
SUPERSESSION_TRIGGER_SET = {"updated_evidence", "updated_policy", "updated_registry"}
PRIOR_DECISION_REF_KIND_SET = {"internal_decision_id", "external_decision_id"}

# Prohibited Gold-claim vocabulary (case-insensitive substring match).
PROHIBITED_GOLD_TOKENS = (
    "full gold",
    "full gold certified",
    "gold certified",
    "gold accepted",
    "gold governed reliance certified",
    "gold-ready",
    "gold ready",
    "gold_ready",
    "platinum",
    "certified",
    "certification",
    "audited",
    "audit ready",
    "audit-ready",
    "regulator approved",
    "regulator approval",
    "auditor approved",
    "auditor approval",
    "compliant",
    "compliance certified",
    "legally accepted",
    "legally enforceable",
    "legal enforceability",
    "legally binding",
    "production approved",
    "production authorized",
    "production governance",
    "production pki",
    "trust federation",
    "federated trust",
    "trust transferred",
    "trust transfer",
    "transferred trust",
    "runtime truth",
    "runtime truth proved",
    "runtime proof",
    "challenge resolved",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _emit_fail(reason: str, detail: str) -> int:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    return 1


def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strip_label(s: str) -> str:
    if s.startswith("sha256:"):
        return s[len("sha256:"):]
    return s


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


def _is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _matches_grammar(s: Any, regex: re.Pattern[str]) -> bool:
    return isinstance(s, str) and bool(regex.match(s))


# ---------------------------------------------------------------------------
# Conformance report re-derivation (must byte-match the runner).
# ---------------------------------------------------------------------------

def _derive_conformance_report(
    *,
    package_id: str,
    governed_reliance_demo_id: str,
    report_id: str,
    generated_at: str,
) -> dict[str, Any]:
    entries = []
    for idx, reason in enumerate(APPROVED_VERIFIER_REASONS_ORDERED, start=1):
        entries.append(
            {
                "check_id": f"check_{idx:02d}",
                "check_name": reason,
                "status": "pass",
                "detail": _CHECK_DETAILS[reason],
            }
        )
    return {
        "document_type": EXPECTED_REPORT_DOC_TYPE,
        "schema_version": EXPECTED_REPORT_SCHEMA_VERSION,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# Check 01 helpers: manifest integrity
# ---------------------------------------------------------------------------

def _check_manifest_integrity(
    manifest_path: Path,
) -> tuple[int, dict[str, Any] | None, Path | None, Path | None, bytes | None]:
    """Run reason 01 checks.

    Returns (rc, manifest_obj, package_path, report_path, package_bytes).
    On failure, rc is 1 and the remaining values are None.
    """
    if not manifest_path.exists():
        return _emit_fail(R01, f"manifest path does not exist: {manifest_path}"), None, None, None, None
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"cannot read manifest: {e}"), None, None, None, None
    try:
        manifest_obj = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R01, f"manifest is not valid JSON: {e}"), None, None, None, None
    if not isinstance(manifest_obj, dict):
        return _emit_fail(R01, "manifest is not a JSON object"), None, None, None, None

    for field, expected in (
        ("document_type", EXPECTED_MANIFEST_DOC_TYPE),
        ("schema_version", EXPECTED_MANIFEST_SCHEMA_VERSION),
        ("proofrail_release", EXPECTED_MANIFEST_PROOFRAIL_RELEASE),
        ("hash_algorithm", EXPECTED_MANIFEST_HASH_ALGO),
    ):
        if manifest_obj.get(field) != expected:
            return _emit_fail(R01, f"manifest.{field} must equal {expected!r}; got {manifest_obj.get(field)!r}"), None, None, None, None

    for field in ("manifest_id", "report_id", "package_id",
                  "governed_reliance_demo_id", "generated_at"):
        if not _is_nonempty_string(manifest_obj.get(field)):
            return _emit_fail(R01, f"manifest.{field} must be a non-empty string"), None, None, None, None

    subjects = manifest_obj.get("subjects")
    if not isinstance(subjects, list) or len(subjects) != 2:
        return _emit_fail(R01, "manifest.subjects must be a list of exactly 2 entries"), None, None, None, None

    expected_subjects = [
        ("governed_reliance_package", PACKAGE_SUBJECT_PATH),
        ("conformance_report", REPORT_SUBJECT_PATH),
    ]
    for i, (expected_role, expected_path) in enumerate(expected_subjects):
        sub = subjects[i]
        if not isinstance(sub, dict):
            return _emit_fail(R01, f"manifest.subjects[{i}] is not an object"), None, None, None, None
        if sub.get("role") != expected_role:
            return _emit_fail(R01, f"manifest.subjects[{i}].role must be {expected_role!r}; got {sub.get('role')!r}"), None, None, None, None
        path = sub.get("path")
        if not isinstance(path, str) or path == "":
            return _emit_fail(R01, f"manifest.subjects[{i}].path is missing or empty"), None, None, None, None
        # Path-traversal BEFORE exact-equality.
        if os.path.isabs(path):
            return _emit_fail(R01, f"manifest.subjects[{i}].path must not be absolute: {path!r}"), None, None, None, None
        if _has_traversal(path):
            return _emit_fail(R01, f"manifest.subjects[{i}].path must not contain path traversal: {path!r}"), None, None, None, None
        if path != expected_path:
            return _emit_fail(R01, f"manifest.subjects[{i}].path must equal {expected_path!r}; got {path!r}"), None, None, None, None
        if not isinstance(sub.get("size_bytes"), int) or sub["size_bytes"] < 0:
            return _emit_fail(R01, f"manifest.subjects[{i}].size_bytes must be a non-negative integer"), None, None, None, None
        sha = sub.get("sha256")
        if not isinstance(sha, str) or not (
            re.fullmatch(r"sha256:[0-9a-f]{64}", sha) or re.fullmatch(r"[0-9a-f]{64}", sha)
        ):
            return _emit_fail(R01, f"manifest.subjects[{i}].sha256 must be a lowercase hex SHA-256 (with or without sha256: prefix); got {sha!r}"), None, None, None, None

    # Cross-anchor and on-disk subject verification.
    manifest_dir = manifest_path.parent
    package_path = manifest_dir / PACKAGE_SUBJECT_PATH
    report_path = manifest_dir / REPORT_SUBJECT_PATH

    if not package_path.exists():
        return _emit_fail(R01, f"package subject [0] file missing: {package_path}"), None, None, None, None
    if not report_path.exists():
        return _emit_fail(R01, f"conformance report subject [1] file missing: {report_path}"), None, None, None, None

    try:
        package_bytes = package_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"cannot read package body: {e}"), None, None, None, None
    try:
        report_bytes = report_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"cannot read conformance report: {e}"), None, None, None, None

    pkg_size = len(package_bytes)
    rpt_size = len(report_bytes)
    if subjects[0]["size_bytes"] != pkg_size:
        return _emit_fail(R01, f"manifest.subjects[0].size_bytes {subjects[0]['size_bytes']} does not match on-disk size {pkg_size}"), None, None, None, None
    if subjects[1]["size_bytes"] != rpt_size:
        return _emit_fail(R01, f"manifest.subjects[1].size_bytes {subjects[1]['size_bytes']} does not match on-disk size {rpt_size}"), None, None, None, None

    pkg_sha_actual = _sha256_hex(package_bytes)
    rpt_sha_actual = _sha256_hex(report_bytes)
    if _strip_label(subjects[0]["sha256"]).lower() != pkg_sha_actual:
        return _emit_fail(R01, f"manifest.subjects[0].sha256 mismatch (manifest={subjects[0]['sha256']}, actual=sha256:{pkg_sha_actual})"), None, None, None, None
    if _strip_label(subjects[1]["sha256"]).lower() != rpt_sha_actual:
        return _emit_fail(R01, f"manifest.subjects[1].sha256 mismatch (manifest={subjects[1]['sha256']}, actual=sha256:{rpt_sha_actual})"), None, None, None, None

    return 0, manifest_obj, package_path, report_path, package_bytes


# ---------------------------------------------------------------------------
# Checks 02–05: package body presence/type
# ---------------------------------------------------------------------------

def _check_package_body_shape(
    manifest_obj: dict[str, Any], package_bytes: bytes
) -> tuple[int, dict[str, Any] | None]:
    try:
        package_obj = json.loads(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return _emit_fail(R02, f"package body is not valid JSON: {e}"), None
    if not isinstance(package_obj, dict):
        return _emit_fail(R02, "package body is not a JSON object"), None

    # R03: document_type, schema_version
    if package_obj.get("document_type") != EXPECTED_PACKAGE_DOC_TYPE:
        return _emit_fail(R03, f"package.document_type must equal {EXPECTED_PACKAGE_DOC_TYPE!r}; got {package_obj.get('document_type')!r}"), None
    if package_obj.get("schema_version") != EXPECTED_PACKAGE_SCHEMA_VERSION:
        return _emit_fail(R03, f"package.schema_version must equal {EXPECTED_PACKAGE_SCHEMA_VERSION!r}; got {package_obj.get('schema_version')!r}"), None
    # Required top-level fields presence (folded into R03 as schema-level
    # structural defect).
    for field in (
        "profile", "package_id", "governed_reliance_demo_id",
        "relying_party", "generated_at", "inputs", "governed_decisions",
        "scope_limitations", "non_claims",
    ):
        if field not in package_obj:
            return _emit_fail(R03, f"package.{field} is required"), None
    # scope_limitations must be a non-empty list. Per the plan, missing or
    # empty scope_limitations folds into R03 (NOT into a 25th reason).
    sl = package_obj.get("scope_limitations")
    if not isinstance(sl, list) or len(sl) == 0:
        return _emit_fail(R03, "package.scope_limitations must be a non-empty list of strings"), None
    for i, entry in enumerate(sl):
        if not _is_nonempty_string(entry):
            return _emit_fail(R03, f"package.scope_limitations[{i}] must be a non-empty string"), None

    # R04: profile
    if package_obj.get("profile") not in SUPPORTED_PROFILES:
        return _emit_fail(R04, f"package.profile must be one of {sorted(SUPPORTED_PROFILES)}; got {package_obj.get('profile')!r}"), None

    # R05: identity
    if not _matches_grammar(package_obj.get("package_id"), PACKAGE_ID_RE):
        return _emit_fail(R05, "package.package_id must satisfy ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"), None
    if not _matches_grammar(package_obj.get("governed_reliance_demo_id"), PACKAGE_ID_RE):
        return _emit_fail(R05, "package.governed_reliance_demo_id must satisfy ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"), None
    rp = package_obj.get("relying_party")
    if not isinstance(rp, dict):
        return _emit_fail(R05, "package.relying_party must be an object"), None
    if not _matches_grammar(rp.get("identity_id"), DOTTED_ID_RE):
        return _emit_fail(R05, "package.relying_party.identity_id must satisfy dotted-identity grammar"), None
    if not _is_nonempty_string(rp.get("display_name")):
        return _emit_fail(R05, "package.relying_party.display_name must be a non-empty string"), None
    if not _is_nonempty_string(rp.get("contact")):
        return _emit_fail(R05, "package.relying_party.contact must be a non-empty string"), None
    if not _matches_grammar(rp.get("registry_ref"), DOTTED_ID_RE):
        return _emit_fail(R05, "package.relying_party.registry_ref must satisfy dotted-identity grammar"), None
    if not _is_nonempty_string(package_obj.get("generated_at")):
        return _emit_fail(R05, "package.generated_at must be a non-empty ISO-8601 UTC string"), None

    # Cross-anchor: manifest package_id and governed_reliance_demo_id
    # must equal package body's. Funnels to R01 per plan §7.
    if manifest_obj["package_id"] != package_obj["package_id"]:
        return _emit_fail(R01, f"manifest.package_id {manifest_obj['package_id']!r} does not equal package.package_id {package_obj['package_id']!r}"), None
    if manifest_obj["governed_reliance_demo_id"] != package_obj["governed_reliance_demo_id"]:
        return _emit_fail(R01, f"manifest.governed_reliance_demo_id {manifest_obj['governed_reliance_demo_id']!r} does not equal package.governed_reliance_demo_id {package_obj['governed_reliance_demo_id']!r}"), None

    return 0, package_obj


# ---------------------------------------------------------------------------
# Checks 06–10: input block structural checks
# ---------------------------------------------------------------------------

def _check_inputs(package_obj: dict[str, Any]) -> int:
    inputs = package_obj.get("inputs")
    if not isinstance(inputs, dict):
        return _emit_fail(R06, "package.inputs must be an object")

    # R06: silver_verification
    sv = inputs.get("silver_verification")
    if not isinstance(sv, dict):
        return _emit_fail(R06, "inputs.silver_verification must be an object")
    if sv.get("input_type") != INPUT_TYPE_SILVER_VERIFICATION:
        return _emit_fail(R06, f"inputs.silver_verification.input_type must equal {INPUT_TYPE_SILVER_VERIFICATION!r}")
    if not _is_nonempty_string(sv.get("input_ref")):
        return _emit_fail(R06, "inputs.silver_verification.input_ref must be a non-empty string")
    if sv.get("expected_status") not in EXPECTED_STATUS_SET:
        return _emit_fail(R06, f"inputs.silver_verification.expected_status must be in {sorted(EXPECTED_STATUS_SET)}")

    # R07: silver_handoff
    sh = inputs.get("silver_handoff")
    if not isinstance(sh, dict):
        return _emit_fail(R07, "inputs.silver_handoff must be an object")
    if sh.get("input_type") != INPUT_TYPE_SILVER_HANDOFF:
        return _emit_fail(R07, f"inputs.silver_handoff.input_type must equal {INPUT_TYPE_SILVER_HANDOFF!r}")
    if not _is_nonempty_string(sh.get("input_ref")):
        return _emit_fail(R07, "inputs.silver_handoff.input_ref must be a non-empty string")
    if sh.get("expected_handoff_posture") not in EXPECTED_HANDOFF_POSTURE_SET:
        return _emit_fail(R07, f"inputs.silver_handoff.expected_handoff_posture must be in {sorted(EXPECTED_HANDOFF_POSTURE_SET)}")

    # R08: policy_pack
    pp = inputs.get("policy_pack")
    if not isinstance(pp, dict):
        return _emit_fail(R08, "inputs.policy_pack must be an object")
    if pp.get("input_type") != INPUT_TYPE_POLICY_PACK:
        return _emit_fail(R08, f"inputs.policy_pack.input_type must equal {INPUT_TYPE_POLICY_PACK!r}")
    if not _is_nonempty_string(pp.get("input_ref")):
        return _emit_fail(R08, "inputs.policy_pack.input_ref must be a non-empty string")
    if not _is_nonempty_string(pp.get("policy_pack_id")):
        return _emit_fail(R08, "inputs.policy_pack.policy_pack_id must be a non-empty string")
    if not _is_nonempty_string(pp.get("policy_pack_version")):
        return _emit_fail(R08, "inputs.policy_pack.policy_pack_version must be a non-empty string")

    # R09: registry_lite
    rl = inputs.get("registry_lite")
    if not isinstance(rl, dict):
        return _emit_fail(R09, "inputs.registry_lite must be an object")
    if rl.get("input_type") != INPUT_TYPE_REGISTRY_LITE:
        return _emit_fail(R09, f"inputs.registry_lite.input_type must equal {INPUT_TYPE_REGISTRY_LITE!r}")
    if not _is_nonempty_string(rl.get("input_ref")):
        return _emit_fail(R09, "inputs.registry_lite.input_ref must be a non-empty string")
    if not _matches_grammar(rl.get("registry_id"), PACKAGE_ID_RE):
        return _emit_fail(R09, "inputs.registry_lite.registry_id must satisfy closed grammar")

    # R10: control_crosswalk
    cc = inputs.get("control_crosswalk")
    if not isinstance(cc, dict):
        return _emit_fail(R10, "inputs.control_crosswalk must be an object")
    if cc.get("input_type") != INPUT_TYPE_CONTROL_CROSSWALK:
        return _emit_fail(R10, f"inputs.control_crosswalk.input_type must equal {INPUT_TYPE_CONTROL_CROSSWALK!r}")
    if not _is_nonempty_string(cc.get("input_ref")):
        return _emit_fail(R10, "inputs.control_crosswalk.input_ref must be a non-empty string")
    if not _is_nonempty_string(cc.get("control_pack_id")):
        return _emit_fail(R10, "inputs.control_crosswalk.control_pack_id must be a non-empty string")

    return 0


# ---------------------------------------------------------------------------
# Check 11: governed_decisions set-level
# ---------------------------------------------------------------------------

def _check_decision_set(package_obj: dict[str, Any]) -> int:
    gd = package_obj.get("governed_decisions")
    if not isinstance(gd, list):
        return _emit_fail(R11, "package.governed_decisions must be a list")
    if len(gd) == 0:
        return _emit_fail(R11, "package.governed_decisions must be a non-empty list (1..5 entries)")
    if len(gd) > 5:
        return _emit_fail(R11, f"package.governed_decisions must have at most 5 entries; got {len(gd)}")
    seen_scenarios: list[str] = []
    last_index = -1
    for i, entry in enumerate(gd):
        if not isinstance(entry, dict):
            return _emit_fail(R11, f"package.governed_decisions[{i}] must be an object")
        st = entry.get("scenario_type")
        if st not in SCENARIO_TYPE_TO_INDEX:
            return _emit_fail(R11, f"package.governed_decisions[{i}].scenario_type must be in {list(SCENARIO_TYPES_ORDERED)}; got {st!r}")
        if st in seen_scenarios:
            return _emit_fail(R11, f"package.governed_decisions[{i}].scenario_type duplicate: {st!r}")
        seen_scenarios.append(st)
        idx = SCENARIO_TYPE_TO_INDEX[st]
        if idx <= last_index:
            return _emit_fail(R11, f"package.governed_decisions[{i}].scenario_type {st!r} violates natural ordering (must strictly increase)")
        last_index = idx
    return 0


# ---------------------------------------------------------------------------
# Check 12: per-entry required fields
# Check 13–17: per-entry binding / status checks
# ---------------------------------------------------------------------------

def _check_entries_structural(package_obj: dict[str, Any]) -> int:
    gd = package_obj["governed_decisions"]
    inputs = package_obj["inputs"]
    expected_policy_pack_id = inputs["policy_pack"]["policy_pack_id"]
    expected_policy_pack_version = inputs["policy_pack"]["policy_pack_version"]

    for i, entry in enumerate(gd):
        # R12: required fields presence + decision_id grammar +
        # decision_trigger closed enum.
        for field in (
            "decision_id", "scenario_type", "decision_status",
            "decision_subject", "policy_binding", "registry_binding",
            "action_scope", "decision_trigger", "scenario_specific_state",
            "recorded_at",
        ):
            if field not in entry:
                return _emit_fail(R12, f"governed_decisions[{i}].{field} is required")
        if not _matches_grammar(entry.get("decision_id"), PACKAGE_ID_RE):
            return _emit_fail(R12, f"governed_decisions[{i}].decision_id must satisfy closed grammar")
        if not _is_nonempty_string(entry.get("recorded_at")):
            return _emit_fail(R12, f"governed_decisions[{i}].recorded_at must be a non-empty ISO-8601 UTC string")
        if entry.get("decision_trigger") not in DECISION_TRIGGER_SET:
            return _emit_fail(R12, f"governed_decisions[{i}].decision_trigger must be in {sorted(DECISION_TRIGGER_SET)}")
        if not isinstance(entry.get("scenario_specific_state"), dict):
            return _emit_fail(R12, f"governed_decisions[{i}].scenario_specific_state must be an object")

        # R13: decision_subject
        ds = entry["decision_subject"]
        if not isinstance(ds, dict):
            return _emit_fail(R13, f"governed_decisions[{i}].decision_subject must be an object")
        if ds.get("subject_type") not in SUBJECT_TYPE_SET:
            return _emit_fail(R13, f"governed_decisions[{i}].decision_subject.subject_type must be in {sorted(SUBJECT_TYPE_SET)}")
        if not _is_nonempty_string(ds.get("subject_ref")):
            return _emit_fail(R13, f"governed_decisions[{i}].decision_subject.subject_ref must be a non-empty string")
        # Cross-check subject_ref against the corresponding input_ref where
        # the closed mapping is unambiguous. Case13 plan trigger is "unknown
        # ref" → R13.
        if ds["subject_type"] == "silver_verification_result":
            if ds["subject_ref"] != inputs["silver_verification"]["input_ref"]:
                return _emit_fail(R13, f"governed_decisions[{i}].decision_subject.subject_ref {ds['subject_ref']!r} does not equal inputs.silver_verification.input_ref")
        elif ds["subject_type"] == "silver_acceptance_handoff":
            if ds["subject_ref"] != inputs["silver_handoff"]["input_ref"]:
                return _emit_fail(R13, f"governed_decisions[{i}].decision_subject.subject_ref {ds['subject_ref']!r} does not equal inputs.silver_handoff.input_ref")
        # challenge_withdrawal_record subject_ref is opaque; no cross-check.

        # R14: policy_binding
        pb = entry["policy_binding"]
        if not isinstance(pb, dict):
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding must be an object")
        if not _is_nonempty_string(pb.get("policy_pack_id")):
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_pack_id must be a non-empty string")
        if pb["policy_pack_id"] != expected_policy_pack_id:
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_pack_id {pb['policy_pack_id']!r} does not match inputs.policy_pack.policy_pack_id {expected_policy_pack_id!r}")
        if pb.get("policy_pack_version") != expected_policy_pack_version:
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_pack_version {pb.get('policy_pack_version')!r} does not match inputs.policy_pack.policy_pack_version {expected_policy_pack_version!r}")
        if not isinstance(pb.get("policy_clause_refs"), list) or len(pb["policy_clause_refs"]) == 0:
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_clause_refs must be a non-empty list")
        for j, cref in enumerate(pb["policy_clause_refs"]):
            if not _is_nonempty_string(cref):
                return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_clause_refs[{j}] must be a non-empty string")
        if pb.get("policy_decision") not in POLICY_DECISION_SET:
            return _emit_fail(R14, f"governed_decisions[{i}].policy_binding.policy_decision must be in {sorted(POLICY_DECISION_SET)}")

        # R15: registry_binding
        rb = entry["registry_binding"]
        if not isinstance(rb, dict):
            return _emit_fail(R15, f"governed_decisions[{i}].registry_binding must be an object")
        if not _is_nonempty_string(rb.get("relying_party_id")):
            return _emit_fail(R15, f"governed_decisions[{i}].registry_binding.relying_party_id must be a non-empty string")
        if rb["relying_party_id"] != package_obj["relying_party"]["identity_id"]:
            return _emit_fail(R15, f"governed_decisions[{i}].registry_binding.relying_party_id {rb['relying_party_id']!r} does not equal package.relying_party.identity_id")
        if rb.get("decision_authority_role") not in DECISION_AUTHORITY_ROLE_SET:
            return _emit_fail(R15, f"governed_decisions[{i}].registry_binding.decision_authority_role must be in {sorted(DECISION_AUTHORITY_ROLE_SET)}")

        # R16: action_scope
        ascope = entry["action_scope"]
        if not isinstance(ascope, dict):
            return _emit_fail(R16, f"governed_decisions[{i}].action_scope must be an object")
        if ascope.get("protected_action_id") not in PROTECTED_ACTION_ID_SET:
            return _emit_fail(R16, f"governed_decisions[{i}].action_scope.protected_action_id must be in {sorted(PROTECTED_ACTION_ID_SET)}")
        if ascope.get("action_category") not in ACTION_CATEGORY_SET:
            return _emit_fail(R16, f"governed_decisions[{i}].action_scope.action_category must be in {sorted(ACTION_CATEGORY_SET)}")
        if ascope.get("action_environment") not in ACTION_ENVIRONMENT_SET:
            return _emit_fail(R16, f"governed_decisions[{i}].action_scope.action_environment must be in {sorted(ACTION_ENVIRONMENT_SET)}")

        # R17: decision_status closed + scenario↔status mapping
        ds_status = entry.get("decision_status")
        if ds_status not in DECISION_STATUS_SET:
            return _emit_fail(R17, f"governed_decisions[{i}].decision_status must be in {sorted(DECISION_STATUS_SET)}")
        expected_status = SCENARIO_TO_STATUS[entry["scenario_type"]]
        if ds_status != expected_status:
            return _emit_fail(R17, f"governed_decisions[{i}].decision_status {ds_status!r} must equal {expected_status!r} for scenario_type {entry['scenario_type']!r}")

    return 0


# ---------------------------------------------------------------------------
# Checks 18–22: scenario-specific paths
# ---------------------------------------------------------------------------

def _check_scenario_paths(package_obj: dict[str, Any]) -> int:
    gd = package_obj["governed_decisions"]
    # Collect known decision_ids for internal supersession resolution.
    decision_ids = {entry["decision_id"] for entry in gd}

    for i, entry in enumerate(gd):
        st = entry["scenario_type"]
        sss = entry["scenario_specific_state"]
        if st == "clean_acceptance":
            if not _is_nonempty_string(sss.get("acceptance_record_ref")):
                return _emit_fail(R18, f"governed_decisions[{i}].scenario_specific_state.acceptance_record_ref must be a non-empty string")
        elif st == "policy_rejection":
            if sss.get("rejection_reason") not in REJECTION_REASON_SET:
                return _emit_fail(R19, f"governed_decisions[{i}].scenario_specific_state.rejection_reason must be in {sorted(REJECTION_REASON_SET)}")
            if sss.get("silver_verification_passing") is not True:
                return _emit_fail(R19, f"governed_decisions[{i}].scenario_specific_state.silver_verification_passing must be the literal boolean true")
        elif st == "challenge_filed":
            if not _is_nonempty_string(sss.get("challenge_record_ref")):
                return _emit_fail(R20, f"governed_decisions[{i}].scenario_specific_state.challenge_record_ref must be a non-empty string")
            if sss.get("challenge_state") not in CHALLENGE_STATE_SET:
                return _emit_fail(R20, f"governed_decisions[{i}].scenario_specific_state.challenge_state must be in {sorted(CHALLENGE_STATE_SET)}")
        elif st == "withdrawal":
            if not _is_nonempty_string(sss.get("withdrawal_record_ref")):
                return _emit_fail(R21, f"governed_decisions[{i}].scenario_specific_state.withdrawal_record_ref must be a non-empty string")
            if sss.get("withdrawal_trigger") not in WITHDRAWAL_TRIGGER_SET:
                return _emit_fail(R21, f"governed_decisions[{i}].scenario_specific_state.withdrawal_trigger must be in {sorted(WITHDRAWAL_TRIGGER_SET)}")
        elif st == "supersession":
            kind = sss.get("prior_decision_ref_kind")
            if kind not in PRIOR_DECISION_REF_KIND_SET:
                return _emit_fail(R22, f"governed_decisions[{i}].scenario_specific_state.prior_decision_ref_kind must be in {sorted(PRIOR_DECISION_REF_KIND_SET)}")
            prior_id = sss.get("prior_decision_id")
            if not _is_nonempty_string(prior_id):
                return _emit_fail(R22, f"governed_decisions[{i}].scenario_specific_state.prior_decision_id must be a non-empty string")
            if kind == "internal_decision_id":
                # Must resolve inside the package, excluding self.
                resolvable = {did for did in decision_ids if did != entry["decision_id"]}
                if prior_id not in resolvable:
                    return _emit_fail(R22, f"governed_decisions[{i}].scenario_specific_state.prior_decision_id {prior_id!r} does not resolve to another decision_id in governed_decisions[] (kind=internal_decision_id)")
            if sss.get("supersession_trigger") not in SUPERSESSION_TRIGGER_SET:
                return _emit_fail(R22, f"governed_decisions[{i}].scenario_specific_state.supersession_trigger must be in {sorted(SUPERSESSION_TRIGGER_SET)}")
            if not _is_nonempty_string(sss.get("superseding_input_ref")):
                return _emit_fail(R22, f"governed_decisions[{i}].scenario_specific_state.superseding_input_ref must be a non-empty string")
        # No else: scenario_type closed set was enforced earlier.

    return 0


# ---------------------------------------------------------------------------
# Check 23: non_claims
# ---------------------------------------------------------------------------

def _check_non_claims(package_obj: dict[str, Any]) -> int:
    nc = package_obj.get("non_claims")
    if not isinstance(nc, list) or len(nc) == 0:
        return _emit_fail(R23, "package.non_claims must be a non-empty list")
    for i, entry in enumerate(nc):
        if not _is_nonempty_string(entry):
            return _emit_fail(R23, f"package.non_claims[{i}] must be a non-empty string")
    return 0


# ---------------------------------------------------------------------------
# Check 24: prohibited Gold-claim scan.
# Scans every string value reachable in the package body OUTSIDE
# scope_limitations and non_claims for case-insensitive substring match
# against the closed prohibited token vocabulary.
# ---------------------------------------------------------------------------

def _scan_for_prohibited(package_obj: dict[str, Any]) -> int:
    EXCLUDED_TOP_KEYS = {"scope_limitations", "non_claims"}

    def _walk(node: Any, path: str) -> tuple[str, str, str] | None:
        if isinstance(node, dict):
            for k, v in node.items():
                child_path = f"{path}.{k}" if path else k
                hit = _walk(v, child_path)
                if hit is not None:
                    return hit
        elif isinstance(node, list):
            for idx, v in enumerate(node):
                child_path = f"{path}[{idx}]"
                hit = _walk(v, child_path)
                if hit is not None:
                    return hit
        elif isinstance(node, str):
            lower = node.lower()
            for tok in PROHIBITED_GOLD_TOKENS:
                if tok in lower:
                    return (path, tok, node)
        return None

    for k, v in package_obj.items():
        if k in EXCLUDED_TOP_KEYS:
            continue
        hit = _walk(v, k)
        if hit is not None:
            path, tok, value = hit
            return _emit_fail(R24, f"{path}: prohibited token {tok!r} present in value {value!r}")
    return 0


# ---------------------------------------------------------------------------
# Conformance report byte-compare re-derivation (post-structural step 25).
# Disagreement funnels into R01 per plan §7.
# ---------------------------------------------------------------------------

def _check_conformance_report(
    manifest_obj: dict[str, Any], report_path: Path, package_obj: dict[str, Any]
) -> int:
    expected = _derive_conformance_report(
        package_id=package_obj["package_id"],
        governed_reliance_demo_id=package_obj["governed_reliance_demo_id"],
        report_id=manifest_obj["report_id"],
        generated_at=manifest_obj["generated_at"],
    )
    expected_bytes = _canonical_json_bytes(expected)
    try:
        actual_bytes = report_path.read_bytes()
    except OSError as e:
        return _emit_fail(R01, f"cannot read conformance report: {e}")
    if actual_bytes != expected_bytes:
        return _emit_fail(R01, "conformance report bytes disagree with verifier re-derivation")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Minimal Gold v0.4.0 Governed Reliance Demo package.",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the v0.4.0 gold-governed-reliance-package-manifest.json.",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)

    # Step 1: manifest integrity (R01)
    rc, manifest_obj, package_path, report_path, package_bytes = _check_manifest_integrity(manifest_path)
    if rc != 0:
        return rc
    assert manifest_obj is not None
    assert report_path is not None
    assert package_bytes is not None

    # Steps 2–5: package body shape (R02..R05)
    rc, package_obj = _check_package_body_shape(manifest_obj, package_bytes)
    if rc != 0:
        return rc
    assert package_obj is not None

    # Steps 6–10: input block (R06..R10)
    rc = _check_inputs(package_obj)
    if rc != 0:
        return rc

    # Step 11: governed_decision_set_invalid (R11)
    rc = _check_decision_set(package_obj)
    if rc != 0:
        return rc

    # Steps 12–17: per-entry structural + bindings + status (R12..R17)
    rc = _check_entries_structural(package_obj)
    if rc != 0:
        return rc

    # Steps 18–22: scenario-specific paths (R18..R22)
    rc = _check_scenario_paths(package_obj)
    if rc != 0:
        return rc

    # Step 23: non_claims (R23)
    rc = _check_non_claims(package_obj)
    if rc != 0:
        return rc

    # Step 24: prohibited Gold-claim scan (R24)
    rc = _scan_for_prohibited(package_obj)
    if rc != 0:
        return rc

    # Step 25 (post-structural): conformance report byte-compare
    # re-derivation. Disagreement funnels into R01.
    rc = _check_conformance_report(manifest_obj, report_path, package_obj)
    if rc != 0:
        return rc

    sys.stdout.write(
        "PASS: gold.governed_reliance.v0.4.0 package "
        f"{package_obj['package_id']} verified against 24 structural checks "
        f"plus conformance report byte-compare re-derivation.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
