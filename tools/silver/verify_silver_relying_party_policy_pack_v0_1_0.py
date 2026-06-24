#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.5 Relying-Party Policy Pack.

Non-masking, hash-first, fail-fast. The verifier:

  1. Validates manifest package integrity: subject count, fixed
     subject order, roles, paths (relative, no '..'), file existence,
     size, and sha256 for BOTH subjects.
  2. Parses subject [0] (policy pack JSON) and confirms it is a
     top-level JSON object.
  3. Runs the 22 ordered policy-pack structural checks
     (`policy_pack_schema_invalid` through `prohibited_claim_present`).
  4. Only AFTER all 24 structural checks pass, independently
     re-derives the conformance report from the bound policy pack and
     compares it byte-for-byte against the bundled subject [1]. A
     conformance-report mismatch on an otherwise valid pack emits
     `policy_pack_manifest_invalid`.

This ordering is non-masking by design: structural reasons in
checks 02 - 24 cannot be intercepted by a stale or fabricated bundled
conformance report.

Stable verifier failure reasons (24, exhaustive, no additions allowed):

   1.  policy_pack_manifest_invalid
   2.  policy_pack_not_object
   3.  policy_pack_schema_invalid
   4.  policy_pack_profile_unsupported
   5.  policy_pack_identity_invalid
   6.  policy_pack_authority_invalid
   7.  policy_scope_invalid
   8.  protected_action_scope_invalid
   9.  silver_handoff_requirement_invalid
  10.  verifier_requirement_invalid
  11.  issuer_requirement_invalid
  12.  revocation_requirement_invalid
  13.  freshness_requirement_invalid
  14.  challenge_requirement_invalid
  15.  withdrawal_requirement_invalid
  16.  supersession_requirement_invalid
  17.  acceptance_criteria_invalid
  18.  rejection_criteria_invalid
  19.  exception_policy_invalid
  20.  hard_stop_policy_invalid
  21.  warning_policy_invalid
  22.  reference_policy_invalid
  23.  non_claims_missing
  24.  prohibited_claim_present

Note: runner_input_path_missing, runner_input_path_forbidden,
runner_input_file_missing, runner_input_read_failed, and
runner_input_json_invalid are runner-only preflight refusal codes
emitted exclusively by build_silver_relying_party_policy_pack_v0_1_0.py.
They are NEVER emitted by this verifier.

Usage:
  python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/silver-relying-party-policy-pack-manifest.json

Exit codes:
  0 - package verified
  1 - package rejected (any stable reason above)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.relying_party_policy_pack_manifest"
POLICY_PACK_DOCUMENT_TYPE = "proofrail.silver.relying_party_policy_pack"
REPORT_DOCUMENT_TYPE = (
    "proofrail.silver.relying_party_policy_pack_conformance_report"
)
SCHEMA_VERSION = "0.1.0"
PROOFRAIL_RELEASE = "v0.3.5"
PROFILE = "relying_party_policy_pack.preview"

POLICY_PACK_REL = "silver-relying-party-policy-pack.json"
REPORT_REL = "silver-relying-party-policy-pack-conformance-report.json"

SUBJECT_ORDER = (
    (POLICY_PACK_REL, "policy_pack"),
    (REPORT_REL, "policy_pack_conformance_report"),
)

# Closed enum vocabularies.
HANDOFF_PROFILES = ("silver.acceptance_handoff.v0.3.0",)
HANDOFF_POSTURES = (
    "for_demo_scope",
    "review_required_before_reuse",
    "not_reusable_without_governed_review",
)
VERIFIER_POSTURES = (
    "silver.base",
    "silver.base.demo",
    "silver.independent",
)
REVOCATION_MODES = (
    "required",
    "required_with_warning_allowance",
    "not_required",
)
CHALLENGE_POSTURES = (
    "record_only",
    "record_and_pause_reuse",
    "record_and_require_review",
)
WITHDRAWAL_POSTURES = (
    "record_only",
    "record_and_pause_reuse",
    "record_and_block_reuse",
)
SUPERSESSION_POSTURES = (
    "record_only",
    "record_and_require_superseding_handoff",
    "record_and_block_until_superseded",
)
ACCEPTANCE_RESULTS = (
    "verifier_pass",
    "issuer_trusted",
    "revocation_check_performed",
    "freshness_window_ok",
    "attestation_present",
)
REJECTION_RESULTS = (
    "verifier_fail",
    "issuer_untrusted",
    "revocation_check_failed_or_skipped",
    "freshness_window_exceeded",
    "attestation_missing",
    "posture_downgrade",
)
WARNING_TREATMENTS = ("block", "review_required", "allow_with_logging")
UNKNOWN_WARNING_DEFAULTS = WARNING_TREATMENTS
SIGNATURE_ALGS = ("ed25519",)

# Prohibited-claim vocabulary (case-insensitive substring match,
# matched only OUTSIDE scope_limitations and non_claims at any depth).
PROHIBITED_CLAIM_TOKENS = (
    "certified",
    "certification",
    "compliant",
    "compliance",
    "legally enforceable",
    "legal enforceability",
    "production authorized",
    "production authorization",
    "authorized for production",
    "regulator approved",
    "regulator approval",
    "approved by regulator",
    "auditor approved",
    "auditor approval",
    "approved by auditor",
    "runtime truth",
    "proves runtime truth",
    "transferred trust",
    "trust transferred",
    "gold governed reliance",
    "gold governance",
    "gold accepted",
    "gold certified",
)

# 24 ordered checks in fixed correspondence with the 24 approved
# verifier reasons.
CHECKS_ORDER = (
    ("check_01", "policy_pack_manifest_invalid"),
    ("check_02", "policy_pack_not_object"),
    ("check_03", "policy_pack_schema_invalid"),
    ("check_04", "policy_pack_profile_unsupported"),
    ("check_05", "policy_pack_identity_invalid"),
    ("check_06", "policy_pack_authority_invalid"),
    ("check_07", "policy_scope_invalid"),
    ("check_08", "protected_action_scope_invalid"),
    ("check_09", "silver_handoff_requirement_invalid"),
    ("check_10", "verifier_requirement_invalid"),
    ("check_11", "issuer_requirement_invalid"),
    ("check_12", "revocation_requirement_invalid"),
    ("check_13", "freshness_requirement_invalid"),
    ("check_14", "challenge_requirement_invalid"),
    ("check_15", "withdrawal_requirement_invalid"),
    ("check_16", "supersession_requirement_invalid"),
    ("check_17", "acceptance_criteria_invalid"),
    ("check_18", "rejection_criteria_invalid"),
    ("check_19", "exception_policy_invalid"),
    ("check_20", "hard_stop_policy_invalid"),
    ("check_21", "warning_policy_invalid"),
    ("check_22", "reference_policy_invalid"),
    ("check_23", "non_claims_missing"),
    ("check_24", "prohibited_claim_present"),
)

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# Runner-only refusal reasons. The verifier never emits these.
RUNNER_ONLY_REFUSAL_REASONS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_label_bytes(data: bytes) -> str:
    return "sha256:" + sha256_hex_bytes(data)


def read_bytes(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read()


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def non_empty_str_list(v: Any) -> bool:
    return (
        isinstance(v, list)
        and len(v) > 0
        and all(non_empty_str(x) for x in v)
    )


def has_path_traversal(rel: Any) -> bool:
    if not isinstance(rel, str):
        return True
    if rel == "":
        return True
    p = Path(rel)
    if p.is_absolute():
        return True
    return ".." in p.parts


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
                value.replace("Z", "+0000"),
                "%Y-%m-%dT%H:%M:%S.%f%z",
            )
        except ValueError:
            return None


def is_non_negative_int(v: Any) -> bool:
    # Reject bools (isinstance(True, int) is True in Python).
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def is_positive_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


# ---------------------------------------------------------------------------
# Manifest integrity (check_01)
# ---------------------------------------------------------------------------


def check_manifest_integrity(manifest_path: Path) -> tuple[dict, dict] | str:
    """Return (manifest_dict, subjects_indexed_by_role) on success,
    or an error detail string on failure.
    """
    try:
        manifest_bytes = read_bytes(manifest_path)
    except OSError as e:
        return f"unable to read manifest file at {manifest_path}: {e}"
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"manifest is not valid UTF-8 JSON: {e}"
    if not isinstance(manifest, dict):
        return "manifest top-level must be a JSON object"
    if manifest.get("document_type") != MANIFEST_DOCUMENT_TYPE:
        return (
            f"document_type must equal {MANIFEST_DOCUMENT_TYPE!r}, "
            f"got {manifest.get('document_type')!r}"
        )
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return (
            f"schema_version must equal {SCHEMA_VERSION!r}, "
            f"got {manifest.get('schema_version')!r}"
        )
    if manifest.get("proofrail_release") != PROOFRAIL_RELEASE:
        return (
            f"proofrail_release must equal {PROOFRAIL_RELEASE!r}, "
            f"got {manifest.get('proofrail_release')!r}"
        )
    if manifest.get("hash_algorithm") != "sha256":
        return (
            "hash_algorithm must equal 'sha256', "
            f"got {manifest.get('hash_algorithm')!r}"
        )
    for field in ("manifest_id", "policy_pack_id"):
        if not non_empty_str(manifest.get(field)):
            return f"{field} missing or empty"
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return (
            "generated_at missing or not an ISO-8601 UTC 'Z' timestamp"
        )
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return "subjects must be a list"
    if len(subjects) != len(SUBJECT_ORDER):
        return (
            f"subjects must contain exactly {len(SUBJECT_ORDER)} entries, "
            f"got {len(subjects)}"
        )
    for i, (expected_path, expected_role) in enumerate(SUBJECT_ORDER):
        sub = subjects[i]
        if not isinstance(sub, dict):
            return f"subjects[{i}] must be a JSON object"
        for field in ("role", "path", "sha256", "size_bytes"):
            if field not in sub:
                return f"subjects[{i}].{field} missing"
        if sub["role"] != expected_role:
            return (
                f"subjects[{i}].role must equal {expected_role!r}, "
                f"got {sub['role']!r}"
            )
        path_val = sub["path"]
        if not non_empty_str(path_val):
            return f"subjects[{i}].path missing or empty"
        if has_path_traversal(path_val):
            return (
                f"subjects[{i}].path is absolute or contains '..': "
                f"{path_val!r}"
            )
        if path_val != expected_path:
            return (
                f"subjects[{i}].path must equal {expected_path!r}, "
                f"got {path_val!r}"
            )
        sha = sub["sha256"]
        if not non_empty_str(sha) or not SHA256_RE.match(sha):
            return (
                f"subjects[{i}].sha256 must match 'sha256:<64-hex>', "
                f"got {sha!r}"
            )
        size = sub["size_bytes"]
        if not is_non_negative_int(size):
            return (
                f"subjects[{i}].size_bytes must be a non-negative integer, "
                f"got {size!r}"
            )
    # Disk recomputation.
    pkg_root = manifest_path.parent
    indexed: dict[str, dict] = {}
    for i, sub in enumerate(subjects):
        file_path = pkg_root / sub["path"]
        if not file_path.is_file():
            return (
                f"subjects[{i}] file missing on disk: {sub['path']}"
            )
        try:
            data = read_bytes(file_path)
        except OSError as e:
            return f"subjects[{i}] could not be read: {e}"
        recomputed = sha256_label_bytes(data)
        if recomputed != sub["sha256"]:
            return (
                f"subjects[{i}] recomputed sha256 ({recomputed}) "
                f"does not match recorded ({sub['sha256']})"
            )
        if len(data) != sub["size_bytes"]:
            return (
                f"subjects[{i}] recomputed size_bytes ({len(data)}) "
                f"does not match recorded ({sub['size_bytes']})"
            )
        indexed[sub["role"]] = {
            "path": sub["path"],
            "sha256": sub["sha256"],
            "size_bytes": sub["size_bytes"],
            "bytes": data,
            "file_path": file_path,
        }
    return manifest, indexed


# ---------------------------------------------------------------------------
# Policy-pack structural checks (check_02 .. check_24)
# ---------------------------------------------------------------------------


def parse_policy_pack(data: bytes) -> tuple[Any, str | None]:
    """Return (pack_obj, error_detail).

    error_detail is None on success and a string when parsing or
    object-shape fails (used by the dispatcher to decide between
    policy_pack_manifest_invalid (parse) and policy_pack_not_object
    (non-object)).
    """
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, f"policy pack subject [0] not valid UTF-8 JSON: {e}"
    if not isinstance(obj, dict):
        return None, "policy pack subject [0] top-level must be a JSON object"
    return obj, None


def check_schema(pack: dict) -> str | None:
    if pack.get("document_type") != POLICY_PACK_DOCUMENT_TYPE:
        return (
            f"document_type must equal {POLICY_PACK_DOCUMENT_TYPE!r}, "
            f"got {pack.get('document_type')!r}"
        )
    if pack.get("schema_version") != SCHEMA_VERSION:
        return (
            f"schema_version must equal {SCHEMA_VERSION!r}, "
            f"got {pack.get('schema_version')!r}"
        )
    if not non_empty_str(pack.get("policy_pack_id")):
        return "policy_pack_id missing or empty"
    return None


def check_profile(pack: dict) -> str | None:
    if pack.get("profile") != PROFILE:
        return (
            f"profile must equal {PROFILE!r}, "
            f"got {pack.get('profile')!r}"
        )
    return None


def check_identity(pack: dict) -> str | None:
    rp = pack.get("relying_party")
    if not isinstance(rp, dict):
        return "relying_party missing or not a JSON object"
    for field in ("identity_id", "identity_label", "contact"):
        if not non_empty_str(rp.get(field)):
            return f"relying_party.{field} missing or empty"
    return None


def check_authority(pack: dict) -> str | None:
    pa = pack.get("policy_authority")
    if not isinstance(pa, dict):
        return "policy_authority missing or not a JSON object"
    for field in ("authority_id", "authority_label", "approver_role"):
        if not non_empty_str(pa.get(field)):
            return f"policy_authority.{field} missing or empty"
    return None


def check_policy_scope(pack: dict) -> str | None:
    pol = pack.get("policy")
    if not isinstance(pol, dict):
        return "policy missing or not a JSON object"
    if not non_empty_str(pol.get("version")):
        return "policy.version missing or empty"
    ep = pol.get("effective_period")
    if not isinstance(ep, dict):
        return "policy.effective_period missing or not a JSON object"
    starts = parse_iso_8601_z(ep.get("starts_at"))
    if starts is None:
        return (
            "policy.effective_period.starts_at missing or not "
            "ISO-8601 UTC 'Z'"
        )
    ends = parse_iso_8601_z(ep.get("ends_at"))
    if ends is None:
        return (
            "policy.effective_period.ends_at missing or not "
            "ISO-8601 UTC 'Z'"
        )
    if not (starts < ends):
        return (
            f"policy.effective_period.starts_at ({ep.get('starts_at')!r}) "
            f"must precede ends_at ({ep.get('ends_at')!r})"
        )
    return None


def check_protected_action_scope(pack: dict) -> str | None:
    if not non_empty_str_list(pack.get("applicable_protected_actions")):
        return (
            "applicable_protected_actions must be a non-empty list of "
            "non-empty strings"
        )
    if not non_empty_str_list(pack.get("applicable_environments")):
        return (
            "applicable_environments must be a non-empty list of "
            "non-empty strings"
        )
    return None


def check_silver_handoff_requirements(pack: dict) -> str | None:
    sh = pack.get("silver_handoff_requirements")
    if not isinstance(sh, dict):
        return "silver_handoff_requirements missing or not a JSON object"
    profiles = sh.get("required_handoff_profiles")
    if not non_empty_str_list(profiles):
        return (
            "silver_handoff_requirements.required_handoff_profiles must "
            "be a non-empty list of non-empty strings"
        )
    for p in profiles:
        if p not in HANDOFF_PROFILES:
            return (
                f"silver_handoff_requirements.required_handoff_profiles "
                f"contains unknown profile {p!r}; allowed: "
                f"{list(HANDOFF_PROFILES)!r}"
            )
    posture = sh.get("minimum_handoff_posture")
    if posture not in HANDOFF_POSTURES:
        return (
            f"silver_handoff_requirements.minimum_handoff_posture must be "
            f"in {list(HANDOFF_POSTURES)!r}, got {posture!r}"
        )
    if not non_empty_str_list(sh.get("required_subject_roles")):
        return (
            "silver_handoff_requirements.required_subject_roles must be "
            "a non-empty list of non-empty strings"
        )
    return None


def check_verifier_requirements(pack: dict) -> str | None:
    vr = pack.get("verifier_requirements")
    if not isinstance(vr, dict):
        return "verifier_requirements missing or not a JSON object"
    posture = vr.get("minimum_posture")
    if posture not in VERIFIER_POSTURES:
        return (
            f"verifier_requirements.minimum_posture must be in "
            f"{list(VERIFIER_POSTURES)!r}, got {posture!r}"
        )
    rva = vr.get("required_verifier_attestation")
    if not isinstance(rva, bool):
        return (
            "verifier_requirements.required_verifier_attestation must "
            "be a boolean"
        )
    ids = vr.get("required_verifier_attestor_ids")
    if not isinstance(ids, list) or not all(
        non_empty_str(x) for x in ids
    ):
        return (
            "verifier_requirements.required_verifier_attestor_ids must "
            "be a list of non-empty strings"
        )
    if rva and len(ids) == 0:
        return (
            "verifier_requirements.required_verifier_attestor_ids must "
            "be non-empty when required_verifier_attestation is true"
        )
    return None


def check_issuer_requirements(pack: dict) -> str | None:
    ir = pack.get("issuer_requirements")
    if not isinstance(ir, dict):
        return "issuer_requirements missing or not a JSON object"
    if not non_empty_str_list(ir.get("trusted_issuer_ids")):
        return (
            "issuer_requirements.trusted_issuer_ids must be a non-empty "
            "list of non-empty strings"
        )
    alg = ir.get("required_signature_algorithm")
    if alg not in SIGNATURE_ALGS:
        return (
            f"issuer_requirements.required_signature_algorithm must be "
            f"in {list(SIGNATURE_ALGS)!r}, got {alg!r}"
        )
    if not is_positive_int(ir.get("minimum_key_id_count")):
        return (
            "issuer_requirements.minimum_key_id_count must be an integer "
            ">= 1"
        )
    return None


def check_revocation_requirements(pack: dict) -> str | None:
    rr = pack.get("revocation_requirements")
    if not isinstance(rr, dict):
        return "revocation_requirements missing or not a JSON object"
    mode = rr.get("mode")
    if mode not in REVOCATION_MODES:
        return (
            f"revocation_requirements.mode must be in "
            f"{list(REVOCATION_MODES)!r}, got {mode!r}"
        )
    age = rr.get("max_revocation_list_age_seconds")
    if not is_non_negative_int(age):
        return (
            "revocation_requirements.max_revocation_list_age_seconds "
            "must be a non-negative integer"
        )
    return None


def check_freshness_requirements(pack: dict) -> str | None:
    fr = pack.get("freshness_requirements")
    if not isinstance(fr, dict):
        return "freshness_requirements missing or not a JSON object"
    age = fr.get("max_age_seconds")
    if not is_non_negative_int(age):
        return (
            "freshness_requirements.max_age_seconds must be a "
            "non-negative integer"
        )
    if not non_empty_str(fr.get("freshness_anchor")):
        return "freshness_requirements.freshness_anchor missing or empty"
    return None


def check_challenge_handling(pack: dict) -> str | None:
    ch = pack.get("challenge_handling")
    if not isinstance(ch, dict):
        return "challenge_handling missing or not a JSON object"
    posture = ch.get("posture")
    if posture not in CHALLENGE_POSTURES:
        return (
            f"challenge_handling.posture must be in "
            f"{list(CHALLENGE_POSTURES)!r}, got {posture!r}"
        )
    if not isinstance(ch.get("within_window_required"), bool):
        return (
            "challenge_handling.within_window_required must be a boolean"
        )
    return None


def check_withdrawal_handling(pack: dict) -> str | None:
    wh = pack.get("withdrawal_handling")
    if not isinstance(wh, dict):
        return "withdrawal_handling missing or not a JSON object"
    posture = wh.get("posture")
    if posture not in WITHDRAWAL_POSTURES:
        return (
            f"withdrawal_handling.posture must be in "
            f"{list(WITHDRAWAL_POSTURES)!r}, got {posture!r}"
        )
    if not isinstance(wh.get("pause_local_reuse_on_withdrawal"), bool):
        return (
            "withdrawal_handling.pause_local_reuse_on_withdrawal must "
            "be a boolean"
        )
    return None


def check_supersession_handling(pack: dict) -> str | None:
    sh = pack.get("supersession_handling")
    if not isinstance(sh, dict):
        return "supersession_handling missing or not a JSON object"
    posture = sh.get("posture")
    if posture not in SUPERSESSION_POSTURES:
        return (
            f"supersession_handling.posture must be in "
            f"{list(SUPERSESSION_POSTURES)!r}, got {posture!r}"
        )
    if not isinstance(sh.get("require_superseding_handoff_id"), bool):
        return (
            "supersession_handling.require_superseding_handoff_id must "
            "be a boolean"
        )
    return None


def check_acceptance_criteria(pack: dict) -> str | None:
    ac = pack.get("acceptance_criteria")
    if not isinstance(ac, dict):
        return "acceptance_criteria missing or not a JSON object"
    results = ac.get("required_silver_results")
    if not non_empty_str_list(results):
        return (
            "acceptance_criteria.required_silver_results must be a "
            "non-empty list of non-empty strings"
        )
    for r in results:
        if r not in ACCEPTANCE_RESULTS:
            return (
                f"acceptance_criteria.required_silver_results contains "
                f"unknown result {r!r}; allowed: {list(ACCEPTANCE_RESULTS)!r}"
            )
    if not isinstance(ac.get("required_handoff_subject_hash_match"), bool):
        return (
            "acceptance_criteria.required_handoff_subject_hash_match "
            "must be a boolean"
        )
    return None


def check_rejection_criteria(pack: dict) -> str | None:
    rc = pack.get("rejection_criteria")
    if not isinstance(rc, dict):
        return "rejection_criteria missing or not a JSON object"
    results = rc.get("blocking_silver_results")
    if not non_empty_str_list(results):
        return (
            "rejection_criteria.blocking_silver_results must be a "
            "non-empty list of non-empty strings"
        )
    for r in results:
        if r not in REJECTION_RESULTS:
            return (
                f"rejection_criteria.blocking_silver_results contains "
                f"unknown result {r!r}; allowed: {list(REJECTION_RESULTS)!r}"
            )
    return None


def check_exceptions(pack: dict) -> str | None:
    exceptions = pack.get("exceptions")
    if not isinstance(exceptions, list):
        return "exceptions must be a JSON array"
    for i, ex in enumerate(exceptions):
        if not isinstance(ex, dict):
            return f"exceptions[{i}] must be a JSON object"
        for field in ("exception_id", "approver_id", "scope", "reason"):
            if not non_empty_str(ex.get(field)):
                return f"exceptions[{i}].{field} missing or empty"
        if parse_iso_8601_z(ex.get("expires_at")) is None:
            return (
                f"exceptions[{i}].expires_at missing or not "
                "ISO-8601 UTC 'Z'"
            )
    return None


def check_hard_stops(pack: dict) -> str | None:
    hard_stops = pack.get("hard_stops")
    if not isinstance(hard_stops, list) or len(hard_stops) == 0:
        return "hard_stops must be a non-empty JSON array"
    for i, hs in enumerate(hard_stops):
        if not isinstance(hs, dict):
            return f"hard_stops[{i}] must be a JSON object"
        for field in ("hard_stop_id", "description"):
            if not non_empty_str(hs.get(field)):
                return f"hard_stops[{i}].{field} missing or empty"
        ovr = hs.get("overridable_by_exception")
        if ovr is not False:
            return (
                f"hard_stops[{i}].overridable_by_exception must be the "
                f"literal boolean false, got {ovr!r} (a hard stop that "
                "is overridable contradicts the hard-stop contract)"
            )
    return None


def check_warning_treatment(pack: dict) -> str | None:
    wt = pack.get("warning_treatment")
    if not isinstance(wt, dict):
        return "warning_treatment missing or not a JSON object"
    default = wt.get("unknown_warning_default")
    if default not in UNKNOWN_WARNING_DEFAULTS:
        return (
            f"warning_treatment.unknown_warning_default must be in "
            f"{list(UNKNOWN_WARNING_DEFAULTS)!r}, got {default!r}"
        )
    warnings = wt.get("warnings")
    if not isinstance(warnings, list):
        return "warning_treatment.warnings must be a JSON array"
    for i, w in enumerate(warnings):
        if not isinstance(w, dict):
            return f"warning_treatment.warnings[{i}] must be a JSON object"
        if not non_empty_str(w.get("warning_id")):
            return (
                f"warning_treatment.warnings[{i}].warning_id missing or "
                "empty"
            )
        t = w.get("treatment")
        if t not in WARNING_TREATMENTS:
            return (
                f"warning_treatment.warnings[{i}].treatment must be in "
                f"{list(WARNING_TREATMENTS)!r}, got {t!r}"
            )
    return None


def check_related_silver_artifacts(pack: dict) -> str | None:
    refs = pack.get("related_silver_artifacts")
    if not isinstance(refs, list):
        return "related_silver_artifacts must be a JSON array"
    for i, r in enumerate(refs):
        if not isinstance(r, dict):
            return f"related_silver_artifacts[{i}] must be a JSON object"
        for field in ("artifact_role", "description"):
            if not non_empty_str(r.get(field)):
                return (
                    f"related_silver_artifacts[{i}].{field} missing or empty"
                )
        path_val = r.get("path")
        if not non_empty_str(path_val):
            return f"related_silver_artifacts[{i}].path missing or empty"
        if has_path_traversal(path_val):
            return (
                f"related_silver_artifacts[{i}].path is absolute or "
                f"contains '..': {path_val!r}"
            )
    return None


def check_non_claims(pack: dict) -> str | None:
    if not non_empty_str_list(pack.get("non_claims")):
        return (
            "non_claims must be a non-empty list of non-empty strings"
        )
    return None


def _scan_prohibited(value: Any, path: str) -> str | None:
    if isinstance(value, str):
        lowered = value.lower()
        for token in PROHIBITED_CLAIM_TOKENS:
            if token in lowered:
                return (
                    f"forbidden token {token!r} found in free-text value "
                    f"at {path}: {value!r}"
                )
        return None
    if isinstance(value, dict):
        for k, v in value.items():
            sub_path = f"{path}.{k}" if path else str(k)
            err = _scan_prohibited(v, sub_path)
            if err is not None:
                return err
        return None
    if isinstance(value, list):
        for i, v in enumerate(value):
            sub_path = f"{path}[{i}]"
            err = _scan_prohibited(v, sub_path)
            if err is not None:
                return err
        return None
    return None


def check_prohibited_claims(pack: dict) -> str | None:
    # Skip recursion into the two permitted blocks at the top level.
    for k, v in pack.items():
        if k in ("scope_limitations", "non_claims"):
            continue
        err = _scan_prohibited(v, k)
        if err is not None:
            return err
    return None


STRUCTURAL_CHECKS = (
    # (check_id, reason, function)
    ("check_03", "policy_pack_schema_invalid", check_schema),
    ("check_04", "policy_pack_profile_unsupported", check_profile),
    ("check_05", "policy_pack_identity_invalid", check_identity),
    ("check_06", "policy_pack_authority_invalid", check_authority),
    ("check_07", "policy_scope_invalid", check_policy_scope),
    ("check_08", "protected_action_scope_invalid", check_protected_action_scope),
    ("check_09", "silver_handoff_requirement_invalid", check_silver_handoff_requirements),
    ("check_10", "verifier_requirement_invalid", check_verifier_requirements),
    ("check_11", "issuer_requirement_invalid", check_issuer_requirements),
    ("check_12", "revocation_requirement_invalid", check_revocation_requirements),
    ("check_13", "freshness_requirement_invalid", check_freshness_requirements),
    ("check_14", "challenge_requirement_invalid", check_challenge_handling),
    ("check_15", "withdrawal_requirement_invalid", check_withdrawal_handling),
    ("check_16", "supersession_requirement_invalid", check_supersession_handling),
    ("check_17", "acceptance_criteria_invalid", check_acceptance_criteria),
    ("check_18", "rejection_criteria_invalid", check_rejection_criteria),
    ("check_19", "exception_policy_invalid", check_exceptions),
    ("check_20", "hard_stop_policy_invalid", check_hard_stops),
    ("check_21", "warning_policy_invalid", check_warning_treatment),
    ("check_22", "reference_policy_invalid", check_related_silver_artifacts),
    ("check_23", "non_claims_missing", check_non_claims),
    ("check_24", "prohibited_claim_present", check_prohibited_claims),
)


# ---------------------------------------------------------------------------
# Conformance report re-derivation (post structural pass)
# ---------------------------------------------------------------------------


def canonical_json_bytes(obj: Any) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def parse_bundled_report(data: bytes) -> tuple[dict, str] | str:
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"bundled conformance report not valid UTF-8 JSON: {e}"
    if not isinstance(obj, dict):
        return "bundled conformance report top-level must be a JSON object"
    if obj.get("document_type") != REPORT_DOCUMENT_TYPE:
        return (
            f"bundled conformance report document_type must equal "
            f"{REPORT_DOCUMENT_TYPE!r}, got {obj.get('document_type')!r}"
        )
    if obj.get("schema_version") != SCHEMA_VERSION:
        return (
            f"bundled conformance report schema_version must equal "
            f"{SCHEMA_VERSION!r}, got {obj.get('schema_version')!r}"
        )
    if obj.get("proofrail_release") != PROOFRAIL_RELEASE:
        return (
            f"bundled conformance report proofrail_release must equal "
            f"{PROOFRAIL_RELEASE!r}, got {obj.get('proofrail_release')!r}"
        )
    if not non_empty_str(obj.get("report_id")):
        return "bundled conformance report report_id missing or empty"
    if parse_iso_8601_z(obj.get("generated_at")) is None:
        return (
            "bundled conformance report generated_at missing or not "
            "ISO-8601 UTC 'Z'"
        )
    return obj, "ok"


def derive_expected_report(
    bundled: dict,
    policy_pack_id: str,
    policy_pack_sha256: str,
) -> dict:
    """Build the expected report from the verifier's own pass results
    and the timestamps/ids carried by the bundled report.

    Any disagreement between this derived object's canonical bytes and
    the bundled bytes triggers policy_pack_manifest_invalid.
    """
    return {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "report_id": bundled.get("report_id"),
        "policy_pack_id": policy_pack_id,
        "policy_pack_sha256": policy_pack_sha256,
        "generated_at": bundled.get("generated_at"),
        "checks": [
            {
                "check_id": cid,
                "approved_reason_name": reason,
                "status": "pass",
            }
            for (cid, reason) in CHECKS_ORDER
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.5 Relying-Party Policy "
            "Pack package."
        )
    )
    p.add_argument(
        "--manifest",
        required=True,
        help="Path to silver-relying-party-policy-pack-manifest.json",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit:
        return 2

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        return usage_error(f"manifest file not found: {manifest_path}")

    # ----- check_01: manifest integrity (both subjects) -----
    result = check_manifest_integrity(manifest_path)
    if isinstance(result, str):
        return fail("policy_pack_manifest_invalid", result)
    manifest, subjects = result
    pack_subject = subjects["policy_pack"]
    report_subject = subjects["policy_pack_conformance_report"]

    # ----- check_02: policy pack is a top-level JSON object -----
    pack, err = parse_policy_pack(pack_subject["bytes"])
    if pack is None:
        # Bytes parsed OK but not a JSON object -> not_object.
        # Bytes did NOT parse as JSON -> manifest-invalid (since the
        # manifest claims the subject is the policy pack JSON).
        # parse_policy_pack distinguishes via the error_detail text;
        # we route based on whether json.loads succeeded.
        try:
            json.loads(pack_subject["bytes"].decode("utf-8"))
            parsed_top_level = True
        except Exception:
            parsed_top_level = False
        if not parsed_top_level:
            return fail("policy_pack_manifest_invalid", err)
        return fail("policy_pack_not_object", err)

    # ----- check_03 .. check_24: structural checks -----
    for _cid, reason, fn in STRUCTURAL_CHECKS:
        err = fn(pack)
        if err is not None:
            return fail(reason, err)

    # ----- post-structural: conformance report re-derivation -----
    bundled_parse = parse_bundled_report(report_subject["bytes"])
    if isinstance(bundled_parse, str):
        return fail("policy_pack_manifest_invalid", bundled_parse)
    bundled_report, _ = bundled_parse

    policy_pack_sha256 = pack_subject["sha256"]
    policy_pack_id = pack.get("policy_pack_id")
    if policy_pack_id != manifest.get("policy_pack_id"):
        return fail(
            "policy_pack_manifest_invalid",
            (
                f"manifest.policy_pack_id ({manifest.get('policy_pack_id')!r}) "
                f"disagrees with policy_pack.policy_pack_id ({policy_pack_id!r})"
            ),
        )

    expected_report = derive_expected_report(
        bundled_report,
        policy_pack_id,
        policy_pack_sha256,
    )
    expected_bytes = canonical_json_bytes(expected_report)
    if expected_bytes != report_subject["bytes"]:
        return fail(
            "policy_pack_manifest_invalid",
            (
                "re-derived conformance report bytes disagree with "
                "bundled subject [1]; the bundled report does not "
                "describe a passing verification of this policy pack"
            ),
        )

    manifest_id = manifest.get("manifest_id")
    print(
        f"PASS: Silver relying-party policy pack v0.3.5 valid "
        f"({manifest_id})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
