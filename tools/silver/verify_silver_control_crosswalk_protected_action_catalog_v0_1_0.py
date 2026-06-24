#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.6 Control Crosswalk + Protected Action Catalog package.

Hash-first ordering. 24 stable failure reasons across 25 ordered checks:

   1.  check_01  manifest integrity            -> control_pack_manifest_invalid
   2.  check_02  control pack is top-level obj -> control_pack_not_object
   3.  check_03  pack document_type/schema    -> control_pack_schema_invalid
   4.  check_04  profile in closed set        -> control_pack_profile_unsupported
   5.  check_05  identity blocks present      -> control_pack_identity_invalid
   6.  check_06  catalog is non-empty list    -> protected_action_catalog_invalid
   7.  check_07  each entry has required desc -> protected_action_entry_invalid
   8.  check_08  action_id grammar            -> protected_action_identifier_invalid
   9.  check_09  env/actor scope fields       -> protected_action_scope_invalid
  10.  check_10  authority block present      -> protected_action_authority_invalid
  11.  check_11  risk_boundary block present  -> protected_action_risk_boundary_invalid
  12.  check_12  crosswalk is non-empty list  -> control_crosswalk_invalid
  13.  check_13  crosswalk entry required     -> crosswalk_entry_invalid
  14.  check_14  catalog/crosswalk consistent -> catalog_crosswalk_consistency_invalid
  15.  check_15  artifact_type/path safe      -> proofrail_artifact_reference_invalid
  16.  check_16  relationship in closed set   -> evidence_relationship_invalid
  17.  check_17  control_concept_id grammar   -> control_concept_reference_invalid
  18.  check_18  control_objective non-empty  -> control_objective_invalid
  19.  check_19  claim verb/scope_text valid  -> control_claim_invalid
  20.  check_20  control_limitations present  -> control_limitation_invalid
  21.  check_21  dependency_references safe   -> dependency_reference_invalid
  22.  check_22  version_bindings in set      -> version_binding_invalid
  23.  check_23  non_claims non-empty list    -> non_claims_missing
  24.  check_24  prohibited vocabulary scan   -> prohibited_compliance_claim_present
  25.  post-structural conformance-report re-derivation byte compare
       -> any disagreement funnels back to control_pack_manifest_invalid
          (no separate public reason is introduced)

The verifier NEVER emits any of the 5 runner-only refusal reasons:
   runner_input_path_missing | runner_input_path_forbidden |
   runner_input_file_missing | runner_input_read_failed   |
   runner_input_json_invalid

Output discipline:

   - On success, exit 0 and print a single line:
        PASS: <manifest path>
   - On failure, exit 1 and print exactly one line to stderr:
        FAIL: <approved_reason>: <human detail>
   - Argument errors exit 2 with prefix `FAIL: usage_error: ...`
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
# Closed protocol constants
# ---------------------------------------------------------------------------

MANIFEST_DOCUMENT_TYPE = (
    "proofrail.silver.control_crosswalk_protected_action_catalog_manifest"
)
PACK_DOCUMENT_TYPE = (
    "proofrail.silver.control_crosswalk_protected_action_catalog"
)
REPORT_DOCUMENT_TYPE = (
    "proofrail.silver.control_crosswalk_protected_action_catalog_conformance_report"
)
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "silver.control_crosswalk.v0.3.6"

SUBJECT_ORDER = (
    ("control-pack.json", "control_pack"),
    (
        "silver-control-crosswalk-protected-action-catalog-conformance-report.json",
        "conformance_report",
    ),
)

CLOSED_PROFILE_SET = frozenset({"silver.control_crosswalk.v0.3.6"})

CLOSED_CATEGORY_SET = frozenset({
    "financial", "vendor", "data", "deployment", "identity",
    "configuration", "communication",
})

CLOSED_ENVIRONMENT_SCOPE_SET = frozenset({"production", "staging", "test", "demo"})

CLOSED_ACTOR_SCOPE_SET = frozenset({"human", "agent", "system", "mixed"})

CLOSED_AUTHORITY_POSTURE_SET = frozenset({
    "scoped_delegation", "principal_only", "joint_principal", "deny_all",
})

CLOSED_RISK_CLASS_SET = frozenset({"low", "moderate", "high", "critical"})

CLOSED_PROOFRAIL_ARTIFACT_TYPE_SET = frozenset({
    "bronze_claim",
    "bronze_evidence_bundle_manifest",
    "silver_signed_bundle_assertion",
    "silver_verification_report",
    "silver_revocation_list",
    "silver_verifier_output_attestation",
    "silver_profile_conformance_report",
    "silver_multi_principal_authority_fixture",
    "silver_protected_action_request",
    "silver_protected_action_decision_report",
    "silver_multi_agent_harness_run_report",
    "silver_multi_agent_harness_evidence_manifest",
    "silver_multi_agent_demo_package_manifest",
    "silver_multi_agent_demo_summary",
    "silver_evidence_source_adapter",
    "silver_simulated_gateway_evidence_event",
    "silver_composed_gateway_evidence_manifest",
    "silver_composed_gateway_evidence_report",
    "silver_relying_party_acceptance_policy",
    "silver_relying_party_acceptance_record",
    "silver_relying_party_acceptance_package_manifest",
    "silver_relying_party_review_event",
    "silver_revocation_challenge_drill_manifest",
    "silver_revocation_challenge_drill_report",
    "silver_acceptance_handoff_manifest",
    "silver_acceptance_handoff_summary",
    "silver_handoff_inspection_manifest",
    "silver_handoff_inspection_report",
    "silver_to_gold_requirement_set",
    "silver_trace_event",
    "silver_trace_claim_binding_set",
    "silver_trace_binding_manifest",
    "silver_trace_binding_report",
    "silver_adapter_pilot_source_export",
    "silver_adapter_pilot_normalization_map",
    "silver_adapter_pilot_manifest",
    "silver_adapter_pilot_report",
    "silver_challenge_record",
    "silver_withdrawal_record",
    "silver_challenge_withdrawal_manifest",
    "silver_challenge_withdrawal_summary",
    "silver_relying_party_policy_pack",
    "silver_relying_party_policy_pack_manifest",
    "silver_relying_party_policy_pack_conformance_report",
})

CLOSED_EVIDENCE_RELATIONSHIP_SET = frozenset({
    "describes", "declares", "mediates", "observes", "normalizes",
    "attests", "records_acceptance", "records_review", "packages",
    "inspects", "binds_trace", "declares_policy",
})

CLOSED_CLAIM_VERB_SET = frozenset({
    "may_inform", "may_support", "may_evidence",
    "declares_scope_for", "packages_for_review",
})

CLOSED_DEPENDENCY_REFERENCE_TYPE_SET = frozenset({
    "upstream_silver_release", "upstream_silver_profile", "prior_artifact",
})

CLOSED_SUPPORTED_UPSTREAM_VERSION_SET = frozenset({
    "v0.2.6", "v0.2.7", "v0.2.8", "v0.2.9",
    "v0.3.0", "v0.3.1", "v0.3.2", "v0.3.3", "v0.3.4", "v0.3.5",
})

# Closed prohibited compliance vocabulary. Case-insensitive substring match.
# Order is fixed for deterministic detail emission.
PROHIBITED_COMPLIANCE_VOCAB = (
    "certified",
    "certification",
    "compliant",
    "compliance",
    "SOC 2 compliant",
    "SOC2 compliant",
    "ISO certified",
    "NIST compliant",
    "PCI compliant",
    "HIPAA compliant",
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
    "audit ready",
    "operating effectiveness",
    "design effectiveness",
    "runtime truth",
    "proves runtime truth",
    "transferred trust",
    "trust transferred",
    "gold governed reliance",
    "gold governance",
    "gold accepted",
    "gold certified",
)

# Field names whose values are LIMITATIONS, not claims. The prohibited
# vocabulary scan SKIPS strings reachable through these field names.
LIMITATIONS_ONLY_FIELDS = frozenset({
    "non_claims", "scope_limitations", "control_limitations",
})

# The 24 ordered checks. Each emits exactly the second-field reason on first
# failure. Names are STRUCTURAL; the runner never emits these.
CHECKS_ORDER = (
    ("check_01", "control_pack_manifest_invalid"),
    ("check_02", "control_pack_not_object"),
    ("check_03", "control_pack_schema_invalid"),
    ("check_04", "control_pack_profile_unsupported"),
    ("check_05", "control_pack_identity_invalid"),
    ("check_06", "protected_action_catalog_invalid"),
    ("check_07", "protected_action_entry_invalid"),
    ("check_08", "protected_action_identifier_invalid"),
    ("check_09", "protected_action_scope_invalid"),
    ("check_10", "protected_action_authority_invalid"),
    ("check_11", "protected_action_risk_boundary_invalid"),
    ("check_12", "control_crosswalk_invalid"),
    ("check_13", "crosswalk_entry_invalid"),
    ("check_14", "catalog_crosswalk_consistency_invalid"),
    ("check_15", "proofrail_artifact_reference_invalid"),
    ("check_16", "evidence_relationship_invalid"),
    ("check_17", "control_concept_reference_invalid"),
    ("check_18", "control_objective_invalid"),
    ("check_19", "control_claim_invalid"),
    ("check_20", "control_limitation_invalid"),
    ("check_21", "dependency_reference_invalid"),
    ("check_22", "version_binding_invalid"),
    ("check_23", "non_claims_missing"),
    ("check_24", "prohibited_compliance_claim_present"),
)

# The 5 runner-only refusal reasons. The verifier MUST NEVER emit these.
RUNNER_ONLY_REFUSAL_REASONS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

ISO_8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
CONTROL_CONCEPT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
ACTION_ID_MAX_LEN = 64

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
    return isinstance(v, list) and len(v) > 0 and all(non_empty_str(x) for x in v)


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
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# check_01 manifest integrity (-> control_pack_manifest_invalid)
# ---------------------------------------------------------------------------

def check_manifest_integrity(manifest_path: Path) -> tuple[dict, dict] | str:
    """Return (manifest_dict, subjects_indexed_by_role) on success or a
    detail string on failure.

    Path traversal is checked BEFORE exact subject-path equality so the
    test suite can independently reach both failure modes.
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
            f"hash_algorithm must equal 'sha256', "
            f"got {manifest.get('hash_algorithm')!r}"
        )
    for field in ("manifest_id", "control_pack_id"):
        if not non_empty_str(manifest.get(field)):
            return f"{field} missing or empty"
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return "generated_at missing or not an ISO-8601 UTC 'Z' timestamp"
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
            return f"subjects[{i}] file missing on disk: {sub['path']}"
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
            "bytes": data,
            "size_bytes": sub["size_bytes"],
        }
    return manifest, indexed


# ---------------------------------------------------------------------------
# check_02 control pack is top-level object (-> control_pack_not_object)
# ---------------------------------------------------------------------------

def check_pack_is_object(pack_bytes: bytes) -> Any | str:
    try:
        obj = json.loads(pack_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"control pack is not valid UTF-8 JSON: {e}"
    if not isinstance(obj, dict):
        return (
            f"control pack top-level must be a JSON object, "
            f"got {type(obj).__name__}"
        )
    return obj


# ---------------------------------------------------------------------------
# check_03 pack schema (-> control_pack_schema_invalid)
# ---------------------------------------------------------------------------

def check_pack_schema(pack: dict) -> str | None:
    if pack.get("document_type") != PACK_DOCUMENT_TYPE:
        return (
            f"document_type must equal {PACK_DOCUMENT_TYPE!r}, "
            f"got {pack.get('document_type')!r}"
        )
    if pack.get("schema_version") != SCHEMA_VERSION:
        return (
            f"schema_version must equal {SCHEMA_VERSION!r}, "
            f"got {pack.get('schema_version')!r}"
        )
    if not non_empty_str(pack.get("control_pack_id")):
        return "control_pack_id missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_04 profile (-> control_pack_profile_unsupported)
# ---------------------------------------------------------------------------

def check_pack_profile(pack: dict) -> str | None:
    p = pack.get("profile")
    if not isinstance(p, str):
        return f"profile missing or not a string: {p!r}"
    if p not in CLOSED_PROFILE_SET:
        return (
            f"profile {p!r} is not in the closed v0.3.6 profile set "
            f"{sorted(CLOSED_PROFILE_SET)!r}"
        )
    return None


# ---------------------------------------------------------------------------
# check_05 identity blocks (-> control_pack_identity_invalid)
# ---------------------------------------------------------------------------

def check_pack_identity(pack: dict) -> str | None:
    for block_name in ("package_owner", "relying_party", "catalog_authority"):
        block = pack.get(block_name)
        if not isinstance(block, dict):
            return f"{block_name} missing or not an object"
        for field in ("identity_id", "display_name", "role"):
            if not non_empty_str(block.get(field)):
                return f"{block_name}.{field} missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_06 catalog is a non-empty list (-> protected_action_catalog_invalid)
# ---------------------------------------------------------------------------

def check_catalog_shape(pack: dict) -> str | None:
    catalog = pack.get("protected_action_catalog")
    if not isinstance(catalog, list):
        return f"protected_action_catalog missing or not a list: {type(catalog).__name__}"
    if len(catalog) == 0:
        return "protected_action_catalog must be non-empty"
    return None


# ---------------------------------------------------------------------------
# check_07 entry required descriptive fields (-> protected_action_entry_invalid)
# ---------------------------------------------------------------------------

def check_catalog_entries(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    for i, entry in enumerate(catalog):
        if not isinstance(entry, dict):
            return f"protected_action_catalog[{i}] must be an object"
        if not non_empty_str(entry.get("description")):
            return f"protected_action_catalog[{i}].description missing or empty"
        cat = entry.get("category")
        if not isinstance(cat, str):
            return f"protected_action_catalog[{i}].category missing or not a string"
        if cat not in CLOSED_CATEGORY_SET:
            return (
                f"protected_action_catalog[{i}].category {cat!r} not in closed set "
                f"{sorted(CLOSED_CATEGORY_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_08 action_id grammar (-> protected_action_identifier_invalid)
# ---------------------------------------------------------------------------

def check_action_ids(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    seen: set[str] = set()
    for i, entry in enumerate(catalog):
        aid = entry.get("action_id")
        if not isinstance(aid, str):
            return f"protected_action_catalog[{i}].action_id missing or not a string"
        if len(aid) > ACTION_ID_MAX_LEN:
            return (
                f"protected_action_catalog[{i}].action_id length {len(aid)} "
                f"exceeds maximum {ACTION_ID_MAX_LEN}"
            )
        if not ACTION_ID_RE.match(aid):
            return (
                f"protected_action_catalog[{i}].action_id {aid!r} does not match "
                f"grammar ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
            )
        if aid in seen:
            return f"protected_action_catalog[{i}].action_id {aid!r} duplicated"
        seen.add(aid)
    return None


# ---------------------------------------------------------------------------
# check_09 scope fields (-> protected_action_scope_invalid)
# ---------------------------------------------------------------------------

def check_action_scopes(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    for i, entry in enumerate(catalog):
        env_scope = entry.get("environment_scope")
        if not isinstance(env_scope, str):
            return f"protected_action_catalog[{i}].environment_scope missing"
        if env_scope not in CLOSED_ENVIRONMENT_SCOPE_SET:
            return (
                f"protected_action_catalog[{i}].environment_scope {env_scope!r} "
                f"not in closed set {sorted(CLOSED_ENVIRONMENT_SCOPE_SET)!r}"
            )
        actor_scope = entry.get("actor_scope")
        if not isinstance(actor_scope, str):
            return f"protected_action_catalog[{i}].actor_scope missing"
        if actor_scope not in CLOSED_ACTOR_SCOPE_SET:
            return (
                f"protected_action_catalog[{i}].actor_scope {actor_scope!r} "
                f"not in closed set {sorted(CLOSED_ACTOR_SCOPE_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_10 authority block (-> protected_action_authority_invalid)
# ---------------------------------------------------------------------------

def check_action_authority(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    for i, entry in enumerate(catalog):
        auth = entry.get("authority")
        if not isinstance(auth, dict):
            return f"protected_action_catalog[{i}].authority missing or not an object"
        posture = auth.get("posture")
        if not isinstance(posture, str):
            return f"protected_action_catalog[{i}].authority.posture missing"
        if posture not in CLOSED_AUTHORITY_POSTURE_SET:
            return (
                f"protected_action_catalog[{i}].authority.posture {posture!r} "
                f"not in closed set {sorted(CLOSED_AUTHORITY_POSTURE_SET)!r}"
            )
        if not isinstance(auth.get("delegation_allowed"), bool):
            return (
                f"protected_action_catalog[{i}].authority.delegation_allowed "
                f"must be a boolean"
            )
        if not non_empty_str_list(auth.get("scoped_principals")):
            return (
                f"protected_action_catalog[{i}].authority.scoped_principals "
                f"must be a non-empty list of non-empty strings"
            )
    return None


# ---------------------------------------------------------------------------
# check_11 risk_boundary block (-> protected_action_risk_boundary_invalid)
# ---------------------------------------------------------------------------

def check_action_risk(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    for i, entry in enumerate(catalog):
        rb = entry.get("risk_boundary")
        if not isinstance(rb, dict):
            return f"protected_action_catalog[{i}].risk_boundary missing or not an object"
        cls = rb.get("risk_class")
        if not isinstance(cls, str):
            return f"protected_action_catalog[{i}].risk_boundary.risk_class missing"
        if cls not in CLOSED_RISK_CLASS_SET:
            return (
                f"protected_action_catalog[{i}].risk_boundary.risk_class {cls!r} "
                f"not in closed set {sorted(CLOSED_RISK_CLASS_SET)!r}"
            )
        for field in ("blast_radius", "rationale"):
            if not non_empty_str(rb.get(field)):
                return (
                    f"protected_action_catalog[{i}].risk_boundary.{field} "
                    f"missing or empty"
                )
    return None


# ---------------------------------------------------------------------------
# check_12 crosswalk shape (-> control_crosswalk_invalid)
# ---------------------------------------------------------------------------

def check_crosswalk_shape(pack: dict) -> str | None:
    crosswalk = pack.get("control_crosswalk")
    if not isinstance(crosswalk, list):
        return (
            f"control_crosswalk missing or not a list: {type(crosswalk).__name__}"
        )
    if len(crosswalk) == 0:
        return "control_crosswalk must be non-empty"
    return None


# ---------------------------------------------------------------------------
# check_13 crosswalk entry required fields (-> crosswalk_entry_invalid)
# ---------------------------------------------------------------------------

def check_crosswalk_entries(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    seen_mapping_ids: set[str] = set()
    for i, entry in enumerate(crosswalk):
        if not isinstance(entry, dict):
            return f"control_crosswalk[{i}] must be an object"
        mid = entry.get("mapping_id")
        if not non_empty_str(mid):
            return f"control_crosswalk[{i}].mapping_id missing or empty"
        if mid in seen_mapping_ids:
            return f"control_crosswalk[{i}].mapping_id {mid!r} duplicated"
        seen_mapping_ids.add(mid)
        if not non_empty_str(entry.get("action_id")):
            return f"control_crosswalk[{i}].action_id missing or empty"
        if not isinstance(entry.get("claim"), dict):
            return f"control_crosswalk[{i}].claim missing or not an object"
    return None


# ---------------------------------------------------------------------------
# check_14 catalog/crosswalk consistency (-> catalog_crosswalk_consistency_invalid)
# ---------------------------------------------------------------------------

def check_catalog_crosswalk_consistency(pack: dict) -> str | None:
    catalog = pack["protected_action_catalog"]
    crosswalk = pack["control_crosswalk"]
    catalog_ids = {e["action_id"] for e in catalog if isinstance(e, dict)}
    for i, entry in enumerate(crosswalk):
        aid = entry.get("action_id")
        if aid not in catalog_ids:
            return (
                f"control_crosswalk[{i}].action_id {aid!r} is not present "
                f"in protected_action_catalog action_ids {sorted(catalog_ids)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_15 artifact_type and artifact_path (-> proofrail_artifact_reference_invalid)
# ---------------------------------------------------------------------------

def check_artifact_references(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    for i, entry in enumerate(crosswalk):
        at = entry.get("artifact_type")
        if not isinstance(at, str):
            return f"control_crosswalk[{i}].artifact_type missing"
        if at not in CLOSED_PROOFRAIL_ARTIFACT_TYPE_SET:
            return (
                f"control_crosswalk[{i}].artifact_type {at!r} not in closed "
                f"ProofRail artifact type set"
            )
        ap = entry.get("artifact_path")
        if not non_empty_str(ap):
            return f"control_crosswalk[{i}].artifact_path missing or empty"
        if has_path_traversal(ap):
            return (
                f"control_crosswalk[{i}].artifact_path is absolute or "
                f"contains '..': {ap!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_16 relationship verb (-> evidence_relationship_invalid)
# ---------------------------------------------------------------------------

def check_relationships(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    for i, entry in enumerate(crosswalk):
        rel = entry.get("relationship")
        if not isinstance(rel, str):
            return f"control_crosswalk[{i}].relationship missing"
        if rel not in CLOSED_EVIDENCE_RELATIONSHIP_SET:
            return (
                f"control_crosswalk[{i}].relationship {rel!r} not in closed "
                f"evidence-relationship verb set "
                f"{sorted(CLOSED_EVIDENCE_RELATIONSHIP_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_17 control_concept_id (-> control_concept_reference_invalid)
# ---------------------------------------------------------------------------

def check_control_concepts(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    for i, entry in enumerate(crosswalk):
        cc = entry.get("control_concept_id")
        if not isinstance(cc, str):
            return f"control_crosswalk[{i}].control_concept_id missing"
        if not CONTROL_CONCEPT_ID_RE.match(cc):
            return (
                f"control_crosswalk[{i}].control_concept_id {cc!r} does not "
                f"match grammar ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
            )
    return None


# ---------------------------------------------------------------------------
# check_18 control_objective (-> control_objective_invalid)
# ---------------------------------------------------------------------------

def check_control_objectives(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    for i, entry in enumerate(crosswalk):
        co = entry.get("control_objective")
        if not non_empty_str(co):
            return f"control_crosswalk[{i}].control_objective missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_19 claim block (-> control_claim_invalid)
# ---------------------------------------------------------------------------

def check_claim_blocks(pack: dict) -> str | None:
    crosswalk = pack["control_crosswalk"]
    for i, entry in enumerate(crosswalk):
        claim = entry["claim"]  # check_13 already verified this is a dict
        verb = claim.get("verb")
        if not isinstance(verb, str):
            return f"control_crosswalk[{i}].claim.verb missing"
        if verb not in CLOSED_CLAIM_VERB_SET:
            return (
                f"control_crosswalk[{i}].claim.verb {verb!r} not in closed "
                f"narrow claim verb set {sorted(CLOSED_CLAIM_VERB_SET)!r}"
            )
        if not non_empty_str(claim.get("scope_text")):
            return f"control_crosswalk[{i}].claim.scope_text missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_20 control_limitations (-> control_limitation_invalid)
# ---------------------------------------------------------------------------

def check_control_limitations(pack: dict) -> str | None:
    limitations = pack.get("control_limitations")
    if not isinstance(limitations, list):
        return f"control_limitations missing or not a list"
    if len(limitations) == 0:
        return "control_limitations must be non-empty"
    for i, entry in enumerate(limitations):
        if not isinstance(entry, dict):
            return f"control_limitations[{i}] must be an object"
        for field in ("limitation_id", "summary", "domain"):
            if not non_empty_str(entry.get(field)):
                return f"control_limitations[{i}].{field} missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_21 dependency_references (-> dependency_reference_invalid)
# ---------------------------------------------------------------------------

def check_dependency_references(pack: dict) -> str | None:
    deps = pack.get("dependency_references")
    if not isinstance(deps, list):
        return "dependency_references missing or not a list"
    for i, entry in enumerate(deps):
        if not isinstance(entry, dict):
            return f"dependency_references[{i}] must be an object"
        if not non_empty_str(entry.get("dependency_id")):
            return f"dependency_references[{i}].dependency_id missing or empty"
        rt = entry.get("reference_type")
        if not isinstance(rt, str):
            return f"dependency_references[{i}].reference_type missing"
        if rt not in CLOSED_DEPENDENCY_REFERENCE_TYPE_SET:
            return (
                f"dependency_references[{i}].reference_type {rt!r} not in closed set "
                f"{sorted(CLOSED_DEPENDENCY_REFERENCE_TYPE_SET)!r}"
            )
        up = entry.get("upstream_id")
        if not non_empty_str(up):
            return f"dependency_references[{i}].upstream_id missing or empty"
        if has_path_traversal(up):
            return (
                f"dependency_references[{i}].upstream_id is absolute or "
                f"contains '..': {up!r}"
            )
        if not non_empty_str(entry.get("upstream_version")):
            return f"dependency_references[{i}].upstream_version missing or empty"
    return None


# ---------------------------------------------------------------------------
# check_22 version_bindings (-> version_binding_invalid)
# ---------------------------------------------------------------------------

def check_version_bindings(pack: dict) -> str | None:
    vbs = pack.get("version_bindings")
    if not isinstance(vbs, list):
        return "version_bindings missing or not a list"
    if len(vbs) == 0:
        return "version_bindings must be non-empty"
    for i, entry in enumerate(vbs):
        if not isinstance(entry, dict):
            return f"version_bindings[{i}] must be an object"
        for field in ("binding_id", "upstream_id"):
            if not non_empty_str(entry.get(field)):
                return f"version_bindings[{i}].{field} missing or empty"
        uv = entry.get("upstream_version")
        if not isinstance(uv, str):
            return f"version_bindings[{i}].upstream_version missing"
        if uv not in CLOSED_SUPPORTED_UPSTREAM_VERSION_SET:
            return (
                f"version_bindings[{i}].upstream_version {uv!r} not in closed "
                f"supported upstream version set "
                f"{sorted(CLOSED_SUPPORTED_UPSTREAM_VERSION_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_23 non_claims (-> non_claims_missing)
# ---------------------------------------------------------------------------

def check_non_claims(pack: dict) -> str | None:
    ncs = pack.get("non_claims")
    if not isinstance(ncs, list) or len(ncs) == 0:
        return "non_claims missing or empty"
    for i, entry in enumerate(ncs):
        if not non_empty_str(entry):
            return f"non_claims[{i}] must be a non-empty string"
    return None


# ---------------------------------------------------------------------------
# check_24 prohibited compliance vocabulary scan
#                                  (-> prohibited_compliance_claim_present)
# ---------------------------------------------------------------------------

def _walk_strings_for_prohibited(node: Any, path: str, hits: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and k in LIMITATIONS_ONLY_FIELDS:
                # Skip limitations subtrees entirely; tokens are permitted
                # there as disclaim text.
                continue
            _walk_strings_for_prohibited(v, f"{path}.{k}", hits)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_strings_for_prohibited(v, f"{path}[{i}]", hits)
    elif isinstance(node, str):
        lc = node.lower()
        for token in PROHIBITED_COMPLIANCE_VOCAB:
            if token.lower() in lc:
                hits.append(f"{path}: {token!r}")
                return  # Report at most one token per leaf for determinism.


def check_prohibited_compliance(pack: dict) -> str | None:
    hits: list[str] = []
    _walk_strings_for_prohibited(pack, "$", hits)
    if hits:
        return (
            f"prohibited compliance vocabulary present outside non_claims / "
            f"scope_limitations / control_limitations at: {hits[0]}"
        )
    return None


# ---------------------------------------------------------------------------
# Conformance-report re-derivation (post-structural)
# ---------------------------------------------------------------------------

APPROVED_VERIFIER_REASONS_ORDERED = tuple(r for _cid, r in CHECKS_ORDER)


def derive_conformance_report(
    *,
    pack: dict,
    bundled_report_obj: Any,
    pack_sha256_hex: str,
) -> dict:
    """Re-derive a deterministic conformance report from the pack.

    The re-derivation reuses report_id and generated_at from the bundled
    report so a byte-identical round-trip is possible for an otherwise
    valid pack. The non-derived fields are deterministic functions of the
    pack.
    """
    if isinstance(bundled_report_obj, dict):
        report_id = bundled_report_obj.get("report_id", "")
        generated_at = bundled_report_obj.get("generated_at", "")
    else:
        report_id = ""
        generated_at = ""

    catalog = pack.get("protected_action_catalog", [])
    crosswalk = pack.get("control_crosswalk", [])
    action_ids: list[str] = []
    for entry in catalog:
        aid = entry.get("action_id")
        if isinstance(aid, str):
            action_ids.append(aid)
    mapping_ids: list[str] = []
    artifact_types: list[str] = []
    control_concept_ids: list[str] = []
    for entry in crosswalk:
        m = entry.get("mapping_id")
        if isinstance(m, str):
            mapping_ids.append(m)
        at = entry.get("artifact_type")
        if isinstance(at, str):
            artifact_types.append(at)
        cc = entry.get("control_concept_id")
        if isinstance(cc, str):
            control_concept_ids.append(cc)
    limitations = pack.get("control_limitations") or []
    deps = pack.get("dependency_references") or []
    vbs = pack.get("version_bindings") or []
    ncs = pack.get("non_claims") or []

    report = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "report_id": report_id,
        "generated_at": generated_at,
        "control_pack_binding": {
            "control_pack_id": pack.get("control_pack_id", ""),
            "control_pack_sha256": pack_sha256_hex,
            "profile": pack.get("profile", ""),
        },
        "summary": {
            "protected_action_count": len(catalog),
            "protected_action_ids": sorted(set(action_ids)),
            "crosswalk_entry_count": len(crosswalk),
            "crosswalk_mapping_ids": sorted(set(mapping_ids)),
            "referenced_artifact_types": sorted(set(artifact_types)),
            "referenced_control_concept_ids": sorted(set(control_concept_ids)),
            "control_limitation_count": len(limitations) if isinstance(limitations, list) else 0,
            "dependency_reference_count": len(deps) if isinstance(deps, list) else 0,
            "version_binding_count": len(vbs) if isinstance(vbs, list) else 0,
            "non_claim_count": len(ncs) if isinstance(ncs, list) else 0,
        },
        "structural_check_ids": list(APPROVED_VERIFIER_REASONS_ORDERED),
        "non_claims": [
            "This conformance report is a deterministic restatement of structural facts.",
            "It is not a compliance attestation, certification, audit decision, regulator decision, authorization, or governed reliance decision.",
        ],
    }
    return report


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

# Each structural-check entry (after check_01) is a callable that takes the
# pack dict and returns a detail string on failure, or None on success.
STRUCTURAL_CHECKS = (
    # (cid, reason, callable)
    ("check_03", "control_pack_schema_invalid", check_pack_schema),
    ("check_04", "control_pack_profile_unsupported", check_pack_profile),
    ("check_05", "control_pack_identity_invalid", check_pack_identity),
    ("check_06", "protected_action_catalog_invalid", check_catalog_shape),
    ("check_07", "protected_action_entry_invalid", check_catalog_entries),
    ("check_08", "protected_action_identifier_invalid", check_action_ids),
    ("check_09", "protected_action_scope_invalid", check_action_scopes),
    ("check_10", "protected_action_authority_invalid", check_action_authority),
    ("check_11", "protected_action_risk_boundary_invalid", check_action_risk),
    ("check_12", "control_crosswalk_invalid", check_crosswalk_shape),
    ("check_13", "crosswalk_entry_invalid", check_crosswalk_entries),
    ("check_14", "catalog_crosswalk_consistency_invalid", check_catalog_crosswalk_consistency),
    ("check_15", "proofrail_artifact_reference_invalid", check_artifact_references),
    ("check_16", "evidence_relationship_invalid", check_relationships),
    ("check_17", "control_concept_reference_invalid", check_control_concepts),
    ("check_18", "control_objective_invalid", check_control_objectives),
    ("check_19", "control_claim_invalid", check_claim_blocks),
    ("check_20", "control_limitation_invalid", check_control_limitations),
    ("check_21", "dependency_reference_invalid", check_dependency_references),
    ("check_22", "version_binding_invalid", check_version_bindings),
    ("check_23", "non_claims_missing", check_non_claims),
    ("check_24", "prohibited_compliance_claim_present", check_prohibited_compliance),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.6 Control Crosswalk + Protected "
            "Action Catalog package."
        )
    )
    parser.add_argument(
        "--manifest", type=str, required=True,
        help="Path to the manifest JSON for the package to verify.",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        return usage_error(f"--manifest path is not a file: {manifest_path}")

    # check_01 manifest integrity.
    res = check_manifest_integrity(manifest_path)
    if isinstance(res, str):
        return fail("control_pack_manifest_invalid", res)
    manifest, indexed = res

    pack_bytes = indexed["control_pack"]["bytes"]

    # check_02 control pack is top-level JSON object.
    pack_obj_or_err = check_pack_is_object(pack_bytes)
    if isinstance(pack_obj_or_err, str):
        return fail("control_pack_not_object", pack_obj_or_err)
    pack = pack_obj_or_err

    # Manifest's control_pack_id must match the pack's control_pack_id once
    # the pack is a valid object. A mismatch here is a manifest-integrity
    # defect, not a separate public reason.
    if non_empty_str(pack.get("control_pack_id")):
        if manifest.get("control_pack_id") != pack.get("control_pack_id"):
            return fail(
                "control_pack_manifest_invalid",
                (
                    f"manifest.control_pack_id "
                    f"({manifest.get('control_pack_id')!r}) does not match "
                    f"control pack control_pack_id "
                    f"({pack.get('control_pack_id')!r})"
                ),
            )

    # check_03..check_24 in fixed order. First failure wins; this loop
    # surfaces the 22 dedicated structural reasons BEFORE the
    # post-structural conformance-report re-derivation.
    for cid, reason, fn in STRUCTURAL_CHECKS:
        detail = fn(pack)
        if detail is not None:
            return fail(reason, detail)

    # Post-structural conformance-report re-derivation. A byte disagreement
    # against the bundled report is reported as control_pack_manifest_invalid;
    # no separate public reason is introduced.
    report_bytes = indexed["conformance_report"]["bytes"]
    try:
        bundled_report = json.loads(report_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return fail(
            "control_pack_manifest_invalid",
            f"conformance report is not valid UTF-8 JSON: {e}",
        )
    pack_sha256_hex = sha256_hex_bytes(pack_bytes)
    rederived = derive_conformance_report(
        pack=pack,
        bundled_report_obj=bundled_report,
        pack_sha256_hex=pack_sha256_hex,
    )
    rederived_bytes = canonical_json_bytes(rederived)
    if rederived_bytes != report_bytes:
        return fail(
            "control_pack_manifest_invalid",
            (
                "bundled conformance report bytes disagree with verifier "
                "re-derivation; the bundled report does not match what the "
                "verified control pack deterministically restates"
            ),
        )

    # Success.
    print(f"PASS: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
