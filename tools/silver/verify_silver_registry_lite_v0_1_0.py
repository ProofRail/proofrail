#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.7 Registry Lite package.

Hash-first ordering. 24 stable failure reasons across 25 ordered checks:

   1.  check_01  manifest integrity            -> registry_manifest_invalid
   2.  check_02  registry is top-level object  -> registry_not_object
   3.  check_03  registry document_type/schema -> registry_schema_invalid
   4.  check_04  profile in closed set         -> registry_profile_unsupported
   5.  check_05  registry_id grammar + scope   -> registry_identity_invalid
   6.  check_06  authority block present       -> registry_authority_invalid
   7.  check_07  entities is non-empty list    -> registry_entity_set_invalid
   8.  check_08  entry required base fields    -> registry_entity_entry_invalid
   9.  check_09  entity_id grammar             -> registry_entity_identifier_invalid
  10.  check_10  role in closed set            -> registry_role_invalid
  11.  check_11  status in closed set          -> registry_status_invalid
  12.  check_12  effective_period valid        -> registry_effective_period_invalid
  13.  check_13  key_references valid          -> registry_key_reference_invalid
  14.  check_14  key_bindings valid            -> registry_key_binding_invalid
  15.  check_15  issuer entry valid            -> issuer_entry_invalid
  16.  check_16  verifier entry valid          -> verifier_entry_invalid
  17.  check_17  relying_party entry valid     -> relying_party_entry_invalid
  18.  check_18  policy_authority entry valid  -> policy_authority_entry_invalid
  19.  check_19  revocation_source entry valid -> revocation_source_entry_invalid
  20.  check_20  protected_action_authority    -> protected_action_authority_entry_invalid
  21.  check_21  trust_relationships valid     -> trust_relationship_invalid
  22.  check_22  version_bindings valid        -> version_binding_invalid
  23.  check_23  non_claims non-empty list     -> non_claims_missing
  24.  check_24  prohibited vocabulary scan    -> prohibited_registry_claim_present
  25.  post-structural conformance-report re-derivation byte compare
       -> any disagreement funnels back to registry_manifest_invalid
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

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.registry_lite_manifest"
REGISTRY_DOCUMENT_TYPE = "proofrail.silver.registry_lite"
REPORT_DOCUMENT_TYPE = "proofrail.silver.registry_lite_conformance_report"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "silver.registry_lite.v0.3.7"

SUBJECT_ORDER = (
    ("registry-lite.json", "registry_lite"),
    ("silver-registry-lite-conformance-report.json", "conformance_report"),
)

CLOSED_PROFILE_SET = frozenset({"silver.registry_lite.v0.3.7"})

CLOSED_REGISTRY_SCOPE_SET = frozenset({
    "demo", "staging", "production", "multi_environment", "out_of_scope",
})

CLOSED_RELEASE_BINDING_SET = frozenset({
    "silver.profile.v0.2.1",
    "silver.attestation.v0.2.2",
    "silver.authority.v0.2.3",
    "silver.composed.v0.2.7",
    "silver.acceptance.v0.2.8",
    "silver.drill.v0.2.9",
    "silver.handoff.v0.3.0",
    "silver.inspection.v0.3.1",
    "silver.trace_binding.v0.3.2",
    "silver.adapter_pilot.v0.3.3",
    "silver.challenge_withdrawal.v0.3.4",
    "silver.policy_pack.v0.3.5",
    "silver.control_crosswalk.v0.3.6",
    "silver.registry_lite.v0.3.7",
})

# Upstream-id set for `version_bindings[].upstream_id` (excludes the
# self-referential v0.3.7 token).
CLOSED_VERSION_BINDING_UPSTREAM_ID_SET = frozenset(
    CLOSED_RELEASE_BINDING_SET - {"silver.registry_lite.v0.3.7"}
)

CLOSED_VERSION_BINDING_UPSTREAM_VERSION_SET = frozenset({
    "v0.2.1", "v0.2.2", "v0.2.3", "v0.2.7", "v0.2.8", "v0.2.9",
    "v0.3.0", "v0.3.1", "v0.3.2", "v0.3.3", "v0.3.4", "v0.3.5", "v0.3.6",
})

CLOSED_ENTITY_ROLE_SET = frozenset({
    "issuer", "verifier", "relying_party", "policy_authority",
    "revocation_source", "protected_action_authority",
})

CLOSED_ENTITY_STATUS_SET = frozenset({
    "active", "provisional", "deprecated", "withdrawn", "out_of_scope",
})

CLOSED_KEY_ALGORITHM_SET = frozenset({
    "ed25519", "ecdsa_p256", "ecdsa_p384", "rsa_2048", "rsa_3072", "rsa_4096",
})

CLOSED_KEY_REFERENCE_TYPE_SET = frozenset({
    "local_fingerprint", "local_pem_path", "local_jwk_path",
})

CLOSED_KEY_BINDING_PURPOSE_SET = frozenset({
    "issue_evidence", "verify_evidence", "sign_policy",
    "sign_revocation", "sign_authority_decision",
})

# Forbidden private-key field names (rejected at key_reference scope).
FORBIDDEN_PRIVATE_KEY_FIELDS = frozenset({
    "private_key", "private_key_pem", "private_jwk", "secret_key", "secret",
})

CLOSED_ISSUER_SCOPE_SET = frozenset({
    "silver_evidence_only", "silver_and_bronze_evidence", "demo_scope_only",
})

CLOSED_VERIFIER_POSTURE_SET = frozenset({
    "independent", "self_attested", "demo_only",
})

CLOSED_RELIANCE_SCOPE_SET = frozenset({
    "demo_only", "local_enterprise", "multi_party_governed", "out_of_scope",
})

CLOSED_POLICY_SCOPE_SET = frozenset({
    "relying_party_policy_only", "multi_party_policy", "demo_policy_only",
})

CLOSED_AUTHORITY_BOUNDARY_SET = frozenset({
    "local_demo", "local_enterprise", "multi_party_governed",
})

CLOSED_REVOCATION_SOURCE_TYPE_SET = frozenset({
    "local_list", "signed_revocation_record", "challenge_drill_outcome",
})

CLOSED_REVOCATION_STATUS_MODE_SET = frozenset({"pull", "push", "snapshot"})

CLOSED_REVOCATION_SUBJECT_SCOPE_SET = frozenset({
    "assertion_id_only", "issuer_key_only", "bundle_hash_only", "all_three",
})

CLOSED_PROTECTED_ACTION_SCOPE_SET = frozenset({
    "local_demo_actions", "local_enterprise_actions",
    "multi_party_governed_actions",
})

CLOSED_DELEGATION_BOUNDARY_SET = frozenset({
    "principal_only", "scoped_delegation", "joint_principal",
    "delegation_with_break_glass",
})

CLOSED_ARTIFACT_TYPE_SET = frozenset({
    "bronze_claim",
    "bronze_evidence_bundle_manifest",
    "silver_signed_bundle_assertion",
    "silver_revocation_list",
    "silver_verification_report",
    "silver_verifier_output_attestation",
    "silver_composed_gateway_evidence_manifest",
    "silver_relying_party_acceptance_record",
    "silver_revocation_challenge_drill_report",
    "silver_acceptance_handoff_manifest",
    "silver_handoff_inspection_manifest",
    "silver_trace_binding_manifest",
    "silver_adapter_pilot_manifest",
    "silver_challenge_withdrawal_manifest",
    "silver_relying_party_policy_pack_manifest",
    "silver_control_crosswalk_protected_action_catalog_manifest",
    "silver_registry_lite_manifest",
})

CLOSED_PROFILE_TOKEN_SET = frozenset({
    "silver.base",
    "silver.base.demo",
    "silver.independent",
    "silver.attestation.v0.2.2",
    "silver.authority.v0.2.3",
    "silver.composed.v0.2.7",
    "silver.acceptance.v0.2.8",
    "silver.drill.v0.2.9",
    "silver.handoff.v0.3.0",
    "silver.inspection.v0.3.1",
    "silver.trace_binding.v0.3.2",
    "silver.adapter_pilot.v0.3.3",
    "silver.challenge_withdrawal.v0.3.4",
    "silver.policy_pack.v0.3.5",
    "silver.control_crosswalk.v0.3.6",
    "silver.registry_lite.v0.3.7",
})

CLOSED_RELATIONSHIP_VERB_SET = frozenset({
    "recognizes_issuer",
    "accepts_verifier_output",
    "references_policy_authority",
    "consults_revocation_source",
    "delegates_to_protected_action_authority",
    "declares_role_binding",
})

# Closed prohibited registry-claim vocabulary. Case-insensitive substring
# match. Order is fixed for deterministic detail emission.
PROHIBITED_REGISTRY_VOCAB = (
    "production PKI",
    "certificate authority",
    "certification authority",
    "legal identity",
    "legally authoritative identity",
    "identity proofing",
    "proofed identity",
    "federated trust",
    "trust federation",
    "production trust registry",
    "authoritative trust registry",
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

# Field names whose values are LIMITATIONS prose, not claims. The
# prohibited vocabulary scan SKIPS strings reachable through these field
# names. The exclusion is intentionally narrow to non_claims and
# scope_limitations only; no other field is exempted from the scan.
LIMITATIONS_ONLY_FIELDS = frozenset({
    "non_claims", "scope_limitations",
})

# No additional dotted paths are exempted from the prohibited-vocabulary
# scan. registry_authority.contact (free-text string in the canonical
# fixture) is intentionally scanned along with every other field outside
# the two limitations-only blocks above.
PROHIBITED_SCAN_SKIP_PATHS: frozenset[str] = frozenset()

# The 24 ordered checks. Each emits exactly the second-field reason on first
# failure. Names are STRUCTURAL; the runner never emits these.
CHECKS_ORDER = (
    ("check_01", "registry_manifest_invalid"),
    ("check_02", "registry_not_object"),
    ("check_03", "registry_schema_invalid"),
    ("check_04", "registry_profile_unsupported"),
    ("check_05", "registry_identity_invalid"),
    ("check_06", "registry_authority_invalid"),
    ("check_07", "registry_entity_set_invalid"),
    ("check_08", "registry_entity_entry_invalid"),
    ("check_09", "registry_entity_identifier_invalid"),
    ("check_10", "registry_role_invalid"),
    ("check_11", "registry_status_invalid"),
    ("check_12", "registry_effective_period_invalid"),
    ("check_13", "registry_key_reference_invalid"),
    ("check_14", "registry_key_binding_invalid"),
    ("check_15", "issuer_entry_invalid"),
    ("check_16", "verifier_entry_invalid"),
    ("check_17", "relying_party_entry_invalid"),
    ("check_18", "policy_authority_entry_invalid"),
    ("check_19", "revocation_source_entry_invalid"),
    ("check_20", "protected_action_authority_entry_invalid"),
    ("check_21", "trust_relationship_invalid"),
    ("check_22", "version_binding_invalid"),
    ("check_23", "non_claims_missing"),
    ("check_24", "prohibited_registry_claim_present"),
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
REGISTRY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")
ENTITY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
LOCAL_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$")

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
# check_01 manifest integrity (-> registry_manifest_invalid)
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
    for field in ("manifest_id", "report_id", "registry_id"):
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
# check_02 registry is top-level object (-> registry_not_object)
# ---------------------------------------------------------------------------

def check_registry_is_object(registry_bytes: bytes) -> Any | str:
    try:
        obj = json.loads(registry_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"registry is not valid UTF-8 JSON: {e}"
    if not isinstance(obj, dict):
        return (
            f"registry top-level must be a JSON object, "
            f"got {type(obj).__name__}"
        )
    return obj


# ---------------------------------------------------------------------------
# check_03 registry schema (-> registry_schema_invalid)
# ---------------------------------------------------------------------------

def check_registry_schema(registry: dict) -> str | None:
    if registry.get("document_type") != REGISTRY_DOCUMENT_TYPE:
        return (
            f"document_type must equal {REGISTRY_DOCUMENT_TYPE!r}, "
            f"got {registry.get('document_type')!r}"
        )
    if registry.get("schema_version") != SCHEMA_VERSION:
        return (
            f"schema_version must equal {SCHEMA_VERSION!r}, "
            f"got {registry.get('schema_version')!r}"
        )
    if not non_empty_str(registry.get("registry_id")):
        return "registry_id missing or empty"
    if parse_iso_8601_z(registry.get("generated_at")) is None:
        return "generated_at missing or not an ISO-8601 UTC 'Z' timestamp"
    return None


# ---------------------------------------------------------------------------
# check_04 profile (-> registry_profile_unsupported)
# ---------------------------------------------------------------------------

def check_registry_profile(registry: dict) -> str | None:
    p = registry.get("profile")
    if not isinstance(p, str):
        return f"profile missing or not a string: {p!r}"
    if p not in CLOSED_PROFILE_SET:
        return (
            f"profile {p!r} is not in the closed v0.3.7 profile set "
            f"{sorted(CLOSED_PROFILE_SET)!r}"
        )
    rb = registry.get("release_binding")
    if not isinstance(rb, str):
        return f"release_binding missing or not a string: {rb!r}"
    if rb not in CLOSED_RELEASE_BINDING_SET:
        return (
            f"release_binding {rb!r} is not in the closed release-binding "
            f"set"
        )
    return None


# ---------------------------------------------------------------------------
# check_05 registry identity + scope (-> registry_identity_invalid)
# ---------------------------------------------------------------------------

def check_registry_identity(registry: dict) -> str | None:
    rid = registry.get("registry_id")
    if not isinstance(rid, str) or not REGISTRY_ID_RE.match(rid):
        return (
            f"registry_id {rid!r} does not match grammar "
            f"^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"
        )
    scope = registry.get("registry_scope")
    if not isinstance(scope, str):
        return f"registry_scope missing or not a string: {scope!r}"
    if scope not in CLOSED_REGISTRY_SCOPE_SET:
        return (
            f"registry_scope {scope!r} not in closed set "
            f"{sorted(CLOSED_REGISTRY_SCOPE_SET)!r}"
        )
    return None


# ---------------------------------------------------------------------------
# check_06 registry authority (-> registry_authority_invalid)
# ---------------------------------------------------------------------------

def check_registry_authority(registry: dict) -> str | None:
    ra = registry.get("registry_authority")
    if not isinstance(ra, dict):
        return "registry_authority missing or not an object"
    for field in ("identity_id", "display_name", "contact"):
        if not non_empty_str(ra.get(field)):
            return f"registry_authority.{field} missing or empty"
    if not ENTITY_ID_RE.match(ra["identity_id"]):
        return (
            f"registry_authority.identity_id {ra['identity_id']!r} does not "
            f"match grammar ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
        )
    return None


# ---------------------------------------------------------------------------
# check_07 entity set (-> registry_entity_set_invalid)
# ---------------------------------------------------------------------------

def check_entity_set(registry: dict) -> str | None:
    entities = registry.get("entities")
    if not isinstance(entities, list):
        return (
            f"entities missing or not a list: {type(entities).__name__}"
        )
    if len(entities) == 0:
        return "entities must be non-empty"
    sls = registry.get("scope_limitations")
    if not isinstance(sls, list):
        return "scope_limitations missing or not a list"
    if len(sls) == 0:
        return "scope_limitations must be non-empty"
    for i, s in enumerate(sls):
        if not non_empty_str(s):
            return f"scope_limitations[{i}] must be a non-empty string"
    return None


# ---------------------------------------------------------------------------
# check_08 entity entry base fields (-> registry_entity_entry_invalid)
# ---------------------------------------------------------------------------

def check_entity_entries(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        if not isinstance(entry, dict):
            return f"entities[{i}] must be an object"
        if not non_empty_str(entry.get("display_label")):
            return f"entities[{i}].display_label missing or empty"
        if "entity_id" not in entry:
            return f"entities[{i}].entity_id missing"
        if "role" not in entry:
            return f"entities[{i}].role missing"
        if "status" not in entry:
            return f"entities[{i}].status missing"
        if "effective_period" not in entry:
            return f"entities[{i}].effective_period missing"
    return None


# ---------------------------------------------------------------------------
# check_09 entity_id grammar (-> registry_entity_identifier_invalid)
# ---------------------------------------------------------------------------

def check_entity_identifiers(registry: dict) -> str | None:
    entities = registry["entities"]
    seen: set[str] = set()
    for i, entry in enumerate(entities):
        eid = entry.get("entity_id")
        if not isinstance(eid, str):
            return f"entities[{i}].entity_id missing or not a string"
        if not ENTITY_ID_RE.match(eid):
            return (
                f"entities[{i}].entity_id {eid!r} does not match grammar "
                f"^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
            )
        if eid in seen:
            return f"entities[{i}].entity_id {eid!r} duplicated"
        seen.add(eid)
    return None


# ---------------------------------------------------------------------------
# check_10 entity role (-> registry_role_invalid)
# ---------------------------------------------------------------------------

def check_entity_roles(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        role = entry.get("role")
        if not isinstance(role, str):
            return f"entities[{i}].role missing or not a string"
        if role not in CLOSED_ENTITY_ROLE_SET:
            return (
                f"entities[{i}].role {role!r} not in closed entity-role set "
                f"{sorted(CLOSED_ENTITY_ROLE_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_11 entity status (-> registry_status_invalid)
# ---------------------------------------------------------------------------

def check_entity_statuses(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        status = entry.get("status")
        if not isinstance(status, str):
            return f"entities[{i}].status missing or not a string"
        if status not in CLOSED_ENTITY_STATUS_SET:
            return (
                f"entities[{i}].status {status!r} not in closed status set "
                f"{sorted(CLOSED_ENTITY_STATUS_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_12 effective_period (-> registry_effective_period_invalid)
# ---------------------------------------------------------------------------

def _check_effective_period(label: str, ep: Any) -> str | None:
    if not isinstance(ep, dict):
        return f"{label} must be an object"
    starts_raw = ep.get("starts_at")
    ends_raw = ep.get("ends_at")
    starts = parse_iso_8601_z(starts_raw)
    if starts is None:
        return f"{label}.starts_at missing or not ISO-8601 'Z': {starts_raw!r}"
    ends = parse_iso_8601_z(ends_raw)
    if ends is None:
        return f"{label}.ends_at missing or not ISO-8601 'Z': {ends_raw!r}"
    if starts > ends:
        return (
            f"{label}.starts_at ({starts_raw!r}) is after ends_at "
            f"({ends_raw!r})"
        )
    return None


def check_entity_effective_periods(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        detail = _check_effective_period(
            f"entities[{i}].effective_period", entry.get("effective_period")
        )
        if detail is not None:
            return detail
    return None


# ---------------------------------------------------------------------------
# check_13 key_references (-> registry_key_reference_invalid)
# ---------------------------------------------------------------------------

def check_entity_key_references(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        krs = entry.get("key_references")
        if krs is None:
            continue
        if not isinstance(krs, list):
            return f"entities[{i}].key_references must be a list"
        seen_kids: set[str] = set()
        for j, kr in enumerate(krs):
            if not isinstance(kr, dict):
                return f"entities[{i}].key_references[{j}] must be an object"
            # Forbidden private-key fields first.
            for fk in FORBIDDEN_PRIVATE_KEY_FIELDS:
                if fk in kr:
                    return (
                        f"entities[{i}].key_references[{j}] contains "
                        f"forbidden private-key field {fk!r}"
                    )
            kid = kr.get("key_id")
            if not isinstance(kid, str) or not LOCAL_ID_RE.match(kid):
                return (
                    f"entities[{i}].key_references[{j}].key_id {kid!r} does "
                    f"not match grammar ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"
                )
            if kid in seen_kids:
                return (
                    f"entities[{i}].key_references[{j}].key_id {kid!r} "
                    f"duplicated"
                )
            seen_kids.add(kid)
            alg = kr.get("algorithm")
            if not isinstance(alg, str):
                return f"entities[{i}].key_references[{j}].algorithm missing"
            if alg not in CLOSED_KEY_ALGORITHM_SET:
                return (
                    f"entities[{i}].key_references[{j}].algorithm {alg!r} "
                    f"not in closed set {sorted(CLOSED_KEY_ALGORITHM_SET)!r}"
                )
            fp = kr.get("public_key_fingerprint")
            if not isinstance(fp, str) or not SHA256_RE.match(fp):
                return (
                    f"entities[{i}].key_references[{j}].public_key_fingerprint "
                    f"must match 'sha256:<64-hex>', got {fp!r}"
                )
            krt = kr.get("key_reference_type")
            if not isinstance(krt, str):
                return (
                    f"entities[{i}].key_references[{j}].key_reference_type "
                    f"missing"
                )
            if krt not in CLOSED_KEY_REFERENCE_TYPE_SET:
                return (
                    f"entities[{i}].key_references[{j}].key_reference_type "
                    f"{krt!r} not in closed set "
                    f"{sorted(CLOSED_KEY_REFERENCE_TYPE_SET)!r}"
                )
            if krt in ("local_pem_path", "local_jwk_path"):
                lrp = kr.get("local_reference_path")
                if not non_empty_str(lrp):
                    return (
                        f"entities[{i}].key_references[{j}].local_reference_path "
                        f"required when key_reference_type is {krt!r}"
                    )
                if has_path_traversal(lrp):
                    return (
                        f"entities[{i}].key_references[{j}].local_reference_path "
                        f"is absolute or contains '..': {lrp!r}"
                    )
    return None


# ---------------------------------------------------------------------------
# check_14 key_bindings (-> registry_key_binding_invalid)
# ---------------------------------------------------------------------------

def check_entity_key_bindings(registry: dict) -> str | None:
    entities = registry["entities"]
    for i, entry in enumerate(entities):
        kbs = entry.get("key_bindings")
        if kbs is None:
            continue
        if not isinstance(kbs, list):
            return f"entities[{i}].key_bindings must be a list"
        kids = set()
        krs = entry.get("key_references") or []
        if isinstance(krs, list):
            for kr in krs:
                if isinstance(kr, dict) and isinstance(kr.get("key_id"), str):
                    kids.add(kr["key_id"])
        seen_bids: set[str] = set()
        for j, kb in enumerate(kbs):
            if not isinstance(kb, dict):
                return f"entities[{i}].key_bindings[{j}] must be an object"
            bid = kb.get("binding_id")
            if not isinstance(bid, str) or not LOCAL_ID_RE.match(bid):
                return (
                    f"entities[{i}].key_bindings[{j}].binding_id {bid!r} "
                    f"does not match grammar ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"
                )
            if bid in seen_bids:
                return (
                    f"entities[{i}].key_bindings[{j}].binding_id {bid!r} "
                    f"duplicated"
                )
            seen_bids.add(bid)
            kid = kb.get("key_id")
            if not isinstance(kid, str):
                return f"entities[{i}].key_bindings[{j}].key_id missing"
            if kid not in kids:
                return (
                    f"entities[{i}].key_bindings[{j}].key_id {kid!r} does "
                    f"not match any key_references[].key_id in the same entity"
                )
            bp = kb.get("binding_purpose")
            if not isinstance(bp, str):
                return (
                    f"entities[{i}].key_bindings[{j}].binding_purpose missing"
                )
            if bp not in CLOSED_KEY_BINDING_PURPOSE_SET:
                return (
                    f"entities[{i}].key_bindings[{j}].binding_purpose {bp!r} "
                    f"not in closed set "
                    f"{sorted(CLOSED_KEY_BINDING_PURPOSE_SET)!r}"
                )
    return None


# ---------------------------------------------------------------------------
# check_15..check_20: role-specific blocks
# ---------------------------------------------------------------------------

def check_issuer_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "issuer":
            continue
        block = entry.get("issuer")
        if not isinstance(block, dict):
            return f"entities[{i}].issuer missing or not an object"
        scope = block.get("issuer_scope")
        if not isinstance(scope, str):
            return f"entities[{i}].issuer.issuer_scope missing"
        if scope not in CLOSED_ISSUER_SCOPE_SET:
            return (
                f"entities[{i}].issuer.issuer_scope {scope!r} not in closed "
                f"set {sorted(CLOSED_ISSUER_SCOPE_SET)!r}"
            )
        sats = block.get("signed_artifact_types")
        if not non_empty_str_list(sats):
            return (
                f"entities[{i}].issuer.signed_artifact_types must be a "
                f"non-empty list of non-empty strings"
            )
        for j, t in enumerate(sats):
            if t not in CLOSED_ARTIFACT_TYPE_SET:
                return (
                    f"entities[{i}].issuer.signed_artifact_types[{j}] {t!r} "
                    f"not in closed artifact-type set"
                )
        sps = block.get("supported_profiles")
        if not non_empty_str_list(sps):
            return (
                f"entities[{i}].issuer.supported_profiles must be a "
                f"non-empty list of non-empty strings"
            )
        for j, p in enumerate(sps):
            if p not in CLOSED_PROFILE_TOKEN_SET:
                return (
                    f"entities[{i}].issuer.supported_profiles[{j}] {p!r} "
                    f"not in closed profile-token set"
                )
    return None


def check_verifier_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "verifier":
            continue
        block = entry.get("verifier")
        if not isinstance(block, dict):
            return f"entities[{i}].verifier missing or not an object"
        vps = block.get("verifier_profiles")
        if not non_empty_str_list(vps):
            return (
                f"entities[{i}].verifier.verifier_profiles must be a "
                f"non-empty list of non-empty strings"
            )
        for j, p in enumerate(vps):
            if p not in CLOSED_PROFILE_TOKEN_SET:
                return (
                    f"entities[{i}].verifier.verifier_profiles[{j}] {p!r} "
                    f"not in closed profile-token set"
                )
        posture = block.get("verifier_posture")
        if not isinstance(posture, str):
            return f"entities[{i}].verifier.verifier_posture missing"
        if posture not in CLOSED_VERIFIER_POSTURE_SET:
            return (
                f"entities[{i}].verifier.verifier_posture {posture!r} not in "
                f"closed set {sorted(CLOSED_VERIFIER_POSTURE_SET)!r}"
            )
    return None


def check_relying_party_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "relying_party":
            continue
        block = entry.get("relying_party")
        if not isinstance(block, dict):
            return f"entities[{i}].relying_party missing or not an object"
        rs = block.get("reliance_scope")
        if not isinstance(rs, str):
            return f"entities[{i}].relying_party.reliance_scope missing"
        if rs not in CLOSED_RELIANCE_SCOPE_SET:
            return (
                f"entities[{i}].relying_party.reliance_scope {rs!r} not in "
                f"closed set {sorted(CLOSED_RELIANCE_SCOPE_SET)!r}"
            )
        lpr = block.get("local_policy_reference")
        if not non_empty_str(lpr):
            return (
                f"entities[{i}].relying_party.local_policy_reference missing "
                f"or empty"
            )
        if has_path_traversal(lpr):
            return (
                f"entities[{i}].relying_party.local_policy_reference is "
                f"absolute or contains '..': {lpr!r}"
            )
    return None


def check_policy_authority_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "policy_authority":
            continue
        block = entry.get("policy_authority")
        if not isinstance(block, dict):
            return f"entities[{i}].policy_authority missing or not an object"
        ps = block.get("policy_scope")
        if not isinstance(ps, str):
            return f"entities[{i}].policy_authority.policy_scope missing"
        if ps not in CLOSED_POLICY_SCOPE_SET:
            return (
                f"entities[{i}].policy_authority.policy_scope {ps!r} not in "
                f"closed set {sorted(CLOSED_POLICY_SCOPE_SET)!r}"
            )
        ab = block.get("authority_boundary")
        if not isinstance(ab, str):
            return (
                f"entities[{i}].policy_authority.authority_boundary missing"
            )
        if ab not in CLOSED_AUTHORITY_BOUNDARY_SET:
            return (
                f"entities[{i}].policy_authority.authority_boundary {ab!r} "
                f"not in closed set "
                f"{sorted(CLOSED_AUTHORITY_BOUNDARY_SET)!r}"
            )
    return None


def check_revocation_source_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "revocation_source":
            continue
        block = entry.get("revocation_source")
        if not isinstance(block, dict):
            return (
                f"entities[{i}].revocation_source missing or not an object"
            )
        st = block.get("source_type")
        if not isinstance(st, str):
            return f"entities[{i}].revocation_source.source_type missing"
        if st not in CLOSED_REVOCATION_SOURCE_TYPE_SET:
            return (
                f"entities[{i}].revocation_source.source_type {st!r} not in "
                f"closed set {sorted(CLOSED_REVOCATION_SOURCE_TYPE_SET)!r}"
            )
        sm = block.get("status_mode")
        if not isinstance(sm, str):
            return f"entities[{i}].revocation_source.status_mode missing"
        if sm not in CLOSED_REVOCATION_STATUS_MODE_SET:
            return (
                f"entities[{i}].revocation_source.status_mode {sm!r} not in "
                f"closed set {sorted(CLOSED_REVOCATION_STATUS_MODE_SET)!r}"
            )
        ss = block.get("supported_subject_scope")
        if not isinstance(ss, str):
            return (
                f"entities[{i}].revocation_source.supported_subject_scope "
                f"missing"
            )
        if ss not in CLOSED_REVOCATION_SUBJECT_SCOPE_SET:
            return (
                f"entities[{i}].revocation_source.supported_subject_scope "
                f"{ss!r} not in closed set "
                f"{sorted(CLOSED_REVOCATION_SUBJECT_SCOPE_SET)!r}"
            )
    return None


def check_protected_action_authority_entries(registry: dict) -> str | None:
    for i, entry in enumerate(registry["entities"]):
        if entry.get("role") != "protected_action_authority":
            continue
        block = entry.get("protected_action_authority")
        if not isinstance(block, dict):
            return (
                f"entities[{i}].protected_action_authority missing or not an "
                f"object"
            )
        pas = block.get("protected_action_scope")
        if not isinstance(pas, str):
            return (
                f"entities[{i}].protected_action_authority."
                f"protected_action_scope missing"
            )
        if pas not in CLOSED_PROTECTED_ACTION_SCOPE_SET:
            return (
                f"entities[{i}].protected_action_authority."
                f"protected_action_scope {pas!r} not in closed set "
                f"{sorted(CLOSED_PROTECTED_ACTION_SCOPE_SET)!r}"
            )
        db = block.get("delegation_boundary")
        if not isinstance(db, str):
            return (
                f"entities[{i}].protected_action_authority."
                f"delegation_boundary missing"
            )
        if db not in CLOSED_DELEGATION_BOUNDARY_SET:
            return (
                f"entities[{i}].protected_action_authority."
                f"delegation_boundary {db!r} not in closed set "
                f"{sorted(CLOSED_DELEGATION_BOUNDARY_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_21 trust_relationships (-> trust_relationship_invalid)
# ---------------------------------------------------------------------------

def check_trust_relationships(registry: dict) -> str | None:
    trels = registry.get("trust_relationships")
    if not isinstance(trels, list):
        return "trust_relationships missing or not a list"
    seen_ids: set[str] = set()
    entity_ids = {
        e["entity_id"] for e in registry["entities"]
        if isinstance(e, dict) and isinstance(e.get("entity_id"), str)
    }
    for i, entry in enumerate(trels):
        if not isinstance(entry, dict):
            return f"trust_relationships[{i}] must be an object"
        rid = entry.get("relationship_id")
        if not isinstance(rid, str) or not LOCAL_ID_RE.match(rid):
            return (
                f"trust_relationships[{i}].relationship_id {rid!r} does not "
                f"match grammar ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"
            )
        if rid in seen_ids:
            return (
                f"trust_relationships[{i}].relationship_id {rid!r} duplicated"
            )
        seen_ids.add(rid)
        for endpoint in ("from_entity_id", "to_entity_id"):
            v = entry.get(endpoint)
            if not isinstance(v, str):
                return (
                    f"trust_relationships[{i}].{endpoint} missing or not "
                    f"a string"
                )
            if v not in entity_ids:
                return (
                    f"trust_relationships[{i}].{endpoint} {v!r} does not "
                    f"match any declared entities[].entity_id"
                )
        verb = entry.get("relationship_verb")
        if not isinstance(verb, str):
            return f"trust_relationships[{i}].relationship_verb missing"
        if verb not in CLOSED_RELATIONSHIP_VERB_SET:
            return (
                f"trust_relationships[{i}].relationship_verb {verb!r} not "
                f"in closed verb set "
                f"{sorted(CLOSED_RELATIONSHIP_VERB_SET)!r}"
            )
        detail = _check_effective_period(
            f"trust_relationships[{i}].effective_period",
            entry.get("effective_period"),
        )
        if detail is not None:
            return detail
    return None


# ---------------------------------------------------------------------------
# check_22 version_bindings (-> version_binding_invalid)
# ---------------------------------------------------------------------------

def check_version_bindings(registry: dict) -> str | None:
    vbs = registry.get("version_bindings")
    if not isinstance(vbs, list):
        return "version_bindings missing or not a list"
    if len(vbs) == 0:
        return "version_bindings must be non-empty"
    seen: set[str] = set()
    for i, entry in enumerate(vbs):
        if not isinstance(entry, dict):
            return f"version_bindings[{i}] must be an object"
        bid = entry.get("binding_id")
        if not isinstance(bid, str) or not LOCAL_ID_RE.match(bid):
            return (
                f"version_bindings[{i}].binding_id {bid!r} does not match "
                f"grammar ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$"
            )
        if bid in seen:
            return f"version_bindings[{i}].binding_id {bid!r} duplicated"
        seen.add(bid)
        up = entry.get("upstream_id")
        if not isinstance(up, str):
            return f"version_bindings[{i}].upstream_id missing"
        if up not in CLOSED_VERSION_BINDING_UPSTREAM_ID_SET:
            return (
                f"version_bindings[{i}].upstream_id {up!r} not in closed "
                f"upstream-id set"
            )
        uv = entry.get("upstream_version")
        if not isinstance(uv, str):
            return f"version_bindings[{i}].upstream_version missing"
        if uv not in CLOSED_VERSION_BINDING_UPSTREAM_VERSION_SET:
            return (
                f"version_bindings[{i}].upstream_version {uv!r} not in "
                f"closed upstream-version set "
                f"{sorted(CLOSED_VERSION_BINDING_UPSTREAM_VERSION_SET)!r}"
            )
    return None


# ---------------------------------------------------------------------------
# check_23 non_claims (-> non_claims_missing)
# ---------------------------------------------------------------------------

def check_non_claims(registry: dict) -> str | None:
    ncs = registry.get("non_claims")
    if not isinstance(ncs, list) or len(ncs) == 0:
        return "non_claims missing or empty"
    for i, entry in enumerate(ncs):
        if not non_empty_str(entry):
            return f"non_claims[{i}] must be a non-empty string"
    return None


# ---------------------------------------------------------------------------
# check_24 prohibited registry vocabulary scan
#                                  (-> prohibited_registry_claim_present)
# ---------------------------------------------------------------------------

def _walk_strings_for_prohibited(
    node: Any, path: str, hits: list[str]
) -> None:
    if path in PROHIBITED_SCAN_SKIP_PATHS:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and k in LIMITATIONS_ONLY_FIELDS:
                # Skip limitations subtrees entirely.
                continue
            _walk_strings_for_prohibited(v, f"{path}.{k}", hits)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_strings_for_prohibited(v, f"{path}[{i}]", hits)
    elif isinstance(node, str):
        lc = node.lower()
        for token in PROHIBITED_REGISTRY_VOCAB:
            if token.lower() in lc:
                hits.append(f"{path}: {token!r}")
                return  # Report at most one token per leaf for determinism.


def check_prohibited_registry(registry: dict) -> str | None:
    hits: list[str] = []
    _walk_strings_for_prohibited(registry, "$", hits)
    if hits:
        return (
            f"prohibited registry vocabulary present outside non_claims / "
            f"scope_limitations at: {hits[0]}"
        )
    return None


# ---------------------------------------------------------------------------
# Conformance-report re-derivation (post-structural)
# ---------------------------------------------------------------------------

APPROVED_VERIFIER_REASONS_ORDERED = tuple(r for _cid, r in CHECKS_ORDER)


def derive_conformance_report(
    *,
    registry: dict,
    bundled_report_obj: Any,
    registry_sha256_hex: str,
) -> dict:
    """Re-derive a deterministic conformance report from the registry.

    The re-derivation reuses report_id and generated_at from the bundled
    report so a byte-identical round-trip is possible for an otherwise
    valid registry. The non-derived fields are deterministic functions
    of the registry.
    """
    if isinstance(bundled_report_obj, dict):
        report_id = bundled_report_obj.get("report_id", "")
        generated_at = bundled_report_obj.get("generated_at", "")
    else:
        report_id = ""
        generated_at = ""

    entities = registry.get("entities") or []
    trels = registry.get("trust_relationships") or []
    vbs = registry.get("version_bindings") or []
    sls = registry.get("scope_limitations") or []
    ncs = registry.get("non_claims") or []

    entity_ids: list[str] = []
    entity_roles: list[str] = []
    for entry in entities:
        if isinstance(entry, dict):
            eid = entry.get("entity_id")
            if isinstance(eid, str):
                entity_ids.append(eid)
            role = entry.get("role")
            if isinstance(role, str):
                entity_roles.append(role)
    relationship_verbs: list[str] = []
    for entry in trels:
        if isinstance(entry, dict):
            v = entry.get("relationship_verb")
            if isinstance(v, str):
                relationship_verbs.append(v)
    upstream_ids: list[str] = []
    for entry in vbs:
        if isinstance(entry, dict):
            u = entry.get("upstream_id")
            if isinstance(u, str):
                upstream_ids.append(u)

    checks = []
    for idx, reason in enumerate(APPROVED_VERIFIER_REASONS_ORDERED, start=1):
        checks.append(
            {
                "check_id": f"check_{idx:02d}",
                "reason": reason,
                "status": "pass",
            }
        )

    report = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "report_id": report_id,
        "registry_id": registry.get("registry_id", ""),
        "generated_at": generated_at,
        "registry_binding": {
            "registry_id": registry.get("registry_id", ""),
            "registry_sha256": registry_sha256_hex,
            "profile": registry.get("profile", ""),
        },
        "summary_counts": {
            "entity_count": len(entities) if isinstance(entities, list) else 0,
            "entity_id_set": sorted(set(entity_ids)),
            "entity_role_set": sorted(set(entity_roles)),
            "trust_relationship_count": len(trels) if isinstance(trels, list) else 0,
            "trust_relationship_verb_set": sorted(set(relationship_verbs)),
            "version_binding_count": len(vbs) if isinstance(vbs, list) else 0,
            "version_binding_upstream_id_set": sorted(set(upstream_ids)),
            "scope_limitation_count": len(sls) if isinstance(sls, list) else 0,
            "non_claim_count": len(ncs) if isinstance(ncs, list) else 0,
        },
        "checks": checks,
        "summary": {
            "checks_total": 24,
            "checks_passed": 24,
            "checks_not_passing": 0,
        },
        "non_claims": [
            "This conformance report is a deterministic restatement of structural facts.",
            "It is not a regulator decision, auditor decision, third-party endorsement, authorization, or governed reliance decision.",
        ],
    }
    return report


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

# Each structural-check entry (after check_01 and check_02) is a callable
# that takes the registry dict and returns a detail string on failure, or
# None on success.
STRUCTURAL_CHECKS = (
    ("check_03", "registry_schema_invalid", check_registry_schema),
    ("check_04", "registry_profile_unsupported", check_registry_profile),
    ("check_05", "registry_identity_invalid", check_registry_identity),
    ("check_06", "registry_authority_invalid", check_registry_authority),
    ("check_07", "registry_entity_set_invalid", check_entity_set),
    ("check_08", "registry_entity_entry_invalid", check_entity_entries),
    ("check_09", "registry_entity_identifier_invalid", check_entity_identifiers),
    ("check_10", "registry_role_invalid", check_entity_roles),
    ("check_11", "registry_status_invalid", check_entity_statuses),
    ("check_12", "registry_effective_period_invalid", check_entity_effective_periods),
    ("check_13", "registry_key_reference_invalid", check_entity_key_references),
    ("check_14", "registry_key_binding_invalid", check_entity_key_bindings),
    ("check_15", "issuer_entry_invalid", check_issuer_entries),
    ("check_16", "verifier_entry_invalid", check_verifier_entries),
    ("check_17", "relying_party_entry_invalid", check_relying_party_entries),
    ("check_18", "policy_authority_entry_invalid", check_policy_authority_entries),
    ("check_19", "revocation_source_entry_invalid", check_revocation_source_entries),
    ("check_20", "protected_action_authority_entry_invalid", check_protected_action_authority_entries),
    ("check_21", "trust_relationship_invalid", check_trust_relationships),
    ("check_22", "version_binding_invalid", check_version_bindings),
    ("check_23", "non_claims_missing", check_non_claims),
    ("check_24", "prohibited_registry_claim_present", check_prohibited_registry),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.7 Registry Lite package."
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
        return fail("registry_manifest_invalid", res)
    manifest, indexed = res

    registry_bytes = indexed["registry_lite"]["bytes"]

    # check_02 registry is top-level JSON object.
    registry_obj_or_err = check_registry_is_object(registry_bytes)
    if isinstance(registry_obj_or_err, str):
        return fail("registry_not_object", registry_obj_or_err)
    registry = registry_obj_or_err

    # Manifest's registry_id must match the registry's registry_id once the
    # registry is a valid object. A mismatch here is a manifest-integrity
    # defect, not a separate public reason.
    if non_empty_str(registry.get("registry_id")):
        if manifest.get("registry_id") != registry.get("registry_id"):
            return fail(
                "registry_manifest_invalid",
                (
                    f"manifest.registry_id "
                    f"({manifest.get('registry_id')!r}) does not match "
                    f"registry registry_id "
                    f"({registry.get('registry_id')!r})"
                ),
            )

    # check_03..check_24 in fixed order. First failure wins; this loop
    # surfaces the 22 dedicated structural reasons BEFORE the
    # post-structural conformance-report re-derivation.
    for cid, reason, fn in STRUCTURAL_CHECKS:
        detail = fn(registry)
        if detail is not None:
            return fail(reason, detail)

    # Post-structural conformance-report re-derivation. A byte disagreement
    # against the bundled report is reported as registry_manifest_invalid;
    # no separate public reason is introduced.
    report_bytes = indexed["conformance_report"]["bytes"]
    try:
        bundled_report = json.loads(report_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return fail(
            "registry_manifest_invalid",
            f"conformance report is not valid UTF-8 JSON: {e}",
        )
    registry_sha256_hex = sha256_hex_bytes(registry_bytes)
    rederived = derive_conformance_report(
        registry=registry,
        bundled_report_obj=bundled_report,
        registry_sha256_hex=registry_sha256_hex,
    )
    rederived_bytes = canonical_json_bytes(rederived)
    if rederived_bytes != report_bytes:
        return fail(
            "registry_manifest_invalid",
            (
                "bundled conformance report bytes disagree with verifier "
                "re-derivation; the bundled report does not match what the "
                "verified registry deterministically restates"
            ),
        )

    # Success.
    print(f"PASS: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
