#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.4 challenge/withdrawal primitives package.

Hash-first, fail-fast. The verifier:

  1.  Parses the package manifest JSON.
  2.  Validates manifest shape: document_type, schema_version,
      proofrail_release, manifest_id, generated_at, hash_algorithm,
      subjects (exactly four), scope_limitations + non_claims present.
  3.  Rejects any subject path that is absolute or contains '..'
      BEFORE comparing it to the fixed SUBJECT_ORDER table.
  4.  Checks each subject path / role / sha256 / size against the
      fixed SUBJECT_ORDER table and recomputes the SHA-256.
  5.  Subprocess-invokes the unchanged v0.3.0 acceptance handoff
      verifier on subject [0] (target handoff manifest).
  6.  Parses both packaged records and structurally validates them
      (presence/type only; closed-enum and evidence_refs checks are
      reserved for the dedicated reasons in steps 7-9).
  7.  Closed-enum checks on the packaged challenge record (split):
        challenge_record_reason_invalid, challenge_record_status_invalid.
  8.  Closed-enum checks on the packaged withdrawal record (split):
        withdrawal_record_reason_invalid, withdrawal_record_status_invalid.
        (withdrawal_effect has no dedicated reason; a wrong value
        falls through to withdrawal_record_invalid in step 6.)
  9.  evidence_refs validation on both packaged records (split):
        challenge_record_evidence_ref_invalid,
        withdrawal_record_evidence_ref_invalid.
 10.  challenge_record_target_mismatch — consolidates: placeholder
      still present, target.target_manifest_sha256 disagrees with
      recomputed subject [0] sha256, or target.target_record_id
      disagrees with the parsed handoff_id.
 11.  withdrawal_record_target_mismatch — same trio for the
      withdrawal record.
 12.  withdrawal_record_challenge_ref_mismatch —
      withdrawal.related_challenge_record_id disagrees with
      challenge.challenge_record_id.
 13.  challenge_withdrawal_time_order_invalid — enforces:
        target.generated_at      <= challenge.filed_at
        challenge.filed_at       <= withdrawal.recorded_at
        withdrawal.recorded_at   <= withdrawal.effective_at.
 14.  challenge_withdrawal_summary_invalid — parses and structurally
      validates the summary, including the seven required claims
      (any claims-list problem also folds into this reason).
 15.  challenge_withdrawal_summary_binding_mismatch — summary's
      target / records sha256 fields and the status / effect echoes
      both flow into this reason.
 16.  challenge_withdrawal_summary_count_mismatch —
      summary.summary.challenge_count and withdrawal_count must each
      equal 1.
 17.  challenge_withdrawal_posture_invalid — posture is in the
      closed posture set AND matches the withdrawal_effect -> posture
      table.
 18.  challenge_withdrawal_overclaim — recursive scan of every string
      value outside scope_limitations and non_claims (including the
      optional claim.description field per Amendment 3) for forbidden
      positive tokens.
 19.  challenge_withdrawal_limitations_missing /
      challenge_withdrawal_non_claims_missing — non-empty lists with
      no blank entries in BOTH the manifest and the summary.

Stable failure reasons (24, exhaustive, no additions allowed):

   1.  invalid_challenge_withdrawal_manifest
   2.  challenge_withdrawal_subject_file_missing
   3.  challenge_withdrawal_subject_path_traversal
   4.  challenge_withdrawal_subject_hash_mismatch
   5.  nested_handoff_invalid
   6.  challenge_record_invalid
   7.  challenge_record_target_mismatch
   8.  challenge_record_reason_invalid
   9.  challenge_record_status_invalid
  10.  challenge_record_evidence_ref_invalid
  11.  withdrawal_record_invalid
  12.  withdrawal_record_target_mismatch
  13.  withdrawal_record_challenge_ref_mismatch
  14.  withdrawal_record_reason_invalid
  15.  withdrawal_record_status_invalid
  16.  withdrawal_record_evidence_ref_invalid
  17.  challenge_withdrawal_time_order_invalid
  18.  challenge_withdrawal_summary_invalid
  19.  challenge_withdrawal_summary_binding_mismatch
  20.  challenge_withdrawal_summary_count_mismatch
  21.  challenge_withdrawal_posture_invalid
  22.  challenge_withdrawal_overclaim
  23.  challenge_withdrawal_limitations_missing
  24.  challenge_withdrawal_non_claims_missing

Note: handoff_validation_failed, challenge_record_validation_failed,
withdrawal_record_validation_failed, challenge_withdrawal_binding_failed,
and challenge_withdrawal_self_validation_failed are runner-only codes
(used by build_silver_challenge_withdrawal_primitives_v0_1_0.py) and
are NEVER emitted by this verifier.

Usage:
  python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-manifest.json

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
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_VERIFIER = (
    REPO_ROOT
    / "tools"
    / "silver"
    / "verify_silver_acceptance_handoff_v0_1_0.py"
)

CHALLENGE_RECORD_DOCUMENT_TYPE = "proofrail.silver.challenge_record"
WITHDRAWAL_RECORD_DOCUMENT_TYPE = "proofrail.silver.withdrawal_record"
SUMMARY_DOCUMENT_TYPE = "proofrail.silver.challenge_withdrawal_summary"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.challenge_withdrawal_manifest"
TARGET_HANDOFF_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_manifest"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.4"

PLACEHOLDER_SHA256 = "sha256:TO_BE_BOUND_BY_RUNNER"

TARGET_HANDOFF_REL = (
    "target-handoff/silver-acceptance-handoff-manifest.json"
)
CHALLENGE_RECORD_REL = "records/challenge-record.json"
WITHDRAWAL_RECORD_REL = "records/withdrawal-record.json"
SUMMARY_REL = "silver-challenge-withdrawal-summary.json"

SUBJECT_ORDER = (
    (TARGET_HANDOFF_REL, "target_handoff_manifest"),
    (CHALLENGE_RECORD_REL, "challenge_record"),
    (WITHDRAWAL_RECORD_REL, "withdrawal_record"),
    (SUMMARY_REL, "challenge_withdrawal_summary"),
)

CHALLENGE_REASONS = (
    "post_acceptance_review_required",
    "evidence_quality_concern",
    "target_scope_concern",
    "time_window_concern",
    "identity_or_authority_concern",
    "policy_alignment_concern",
    "transparency_concern",
    "derived_signal_concern",
    "third_party_signal_concern",
    "other",
)
CHALLENGE_STATUSES = (
    "filed",
    "under_local_review",
    "locally_resolved",
    "withdrawn",
)
WITHDRAWAL_REASONS = (
    "challenge_pending_review",
    "scope_change",
    "evidence_supersession",
    "time_expiry",
    "policy_change",
    "voluntary_pause",
    "other",
)
WITHDRAWAL_STATUSES = (
    "withdrawal_recorded",
    "withdrawal_under_review",
    "withdrawal_finalized_locally",
    "withdrawal_revoked",
)
WITHDRAWAL_EFFECTS = (
    "local_reuse_paused_for_review",
    "local_reliance_withdrawn_for_review",
    "acceptance_reuse_blocked_pending_review",
    "record_superseded",
)
POSTURES = (
    "challenge_recorded",
    "challenged_with_local_reuse_paused_for_review",
    "challenged_with_local_reliance_withdrawn_for_review",
    "withdrawal_recorded_without_adjudication",
    "record_superseded",
)
WITHDRAWAL_EFFECT_TO_POSTURE = {
    "local_reuse_paused_for_review": "challenged_with_local_reuse_paused_for_review",
    "local_reliance_withdrawn_for_review": "challenged_with_local_reliance_withdrawn_for_review",
    "acceptance_reuse_blocked_pending_review": "challenged_with_local_reuse_paused_for_review",
    "record_superseded": "record_superseded",
}

REQUIRED_CLAIMS = (
    "target_handoff_verified",
    "challenge_record_valid",
    "withdrawal_record_valid",
    "challenge_and_withdrawal_target_same_handoff",
    "withdrawal_cites_challenge",
    "time_order_valid",
    "no_adjudication_claimed",
)

# Free-text overclaim tokens (case-insensitive substring match).
FORBIDDEN_TOKENS = (
    "certified",
    "approved",
    "audited",
    "legally accepted",
    "legally revoked",
    "challenge resolved",
    "gold accepted",
    "gold certified",
    "compliant",
    "production-approved",
    "production approved",
    "production-ready",
    "production ready",
    "regulator-ready",
    "regulator approval",
    "trust transferred",
    "trust transfer",
    "adjudicated",
    "adjudication complete",
    "gold-ready",
    "gold ready",
    "gold_ready",
)

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

ALLOWED_CLAIM_EVIDENCE_PREFIXES = (
    TARGET_HANDOFF_REL,
    CHALLENGE_RECORD_REL,
    WITHDRAWAL_RECORD_REL,
    SUMMARY_REL,
    "target-handoff/",  # any file inside the byte-copied handoff package
)


def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_label(path: Path) -> str:
    return "sha256:" + sha256_hex(path)


def parse_iso_8601_z(value: Any) -> datetime | None:
    if not isinstance(value, str) or not ISO_8601_RE.match(value):
        return None
    try:
        return datetime.strptime(value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            return datetime.strptime(
                value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            return None


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def non_empty_str_list(v: Any) -> bool:
    return (
        isinstance(v, list)
        and len(v) > 0
        and all(non_empty_str(x) for x in v)
    )


def has_path_traversal(rel: str) -> bool:
    if not isinstance(rel, str):
        return True
    if rel == "":
        return True
    p = Path(rel)
    if p.is_absolute():
        return True
    parts = p.parts
    if ".." in parts:
        return True
    return False


def collect_fail_detail(proc: subprocess.CompletedProcess) -> str:
    detail = (proc.stdout + proc.stderr).strip().replace("\n", " ; ")
    if not detail:
        detail = f"subprocess exited {proc.returncode}"
    return detail


# --------------------------------------------------------------------
# Packaged record structural validation
# --------------------------------------------------------------------


def validate_principal_block(block: Any) -> str | None:
    if not isinstance(block, dict):
        return "principal block missing or not an object"
    if not non_empty_str(block.get("principal_id")):
        return "principal_id missing or empty"
    if not non_empty_str(block.get("role")):
        return "role missing or empty"
    return None


def validate_packaged_target_block(block: Any) -> str | None:
    """Same as runner-side but ACCEPTS the placeholder syntactically.

    A separate later check rejects the literal placeholder under the
    dedicated reason so structural-vs-placeholder reachability is
    preserved (Amendment 4).
    """
    if not isinstance(block, dict):
        return "target block missing or not an object"
    if block.get("target_type") != "silver_acceptance_handoff":
        return (
            "target.target_type must be 'silver_acceptance_handoff', "
            f"got {block.get('target_type')!r}"
        )
    tmp = block.get("target_manifest_path")
    if not non_empty_str(tmp):
        return "target.target_manifest_path missing or empty"
    if has_path_traversal(tmp):
        return f"target.target_manifest_path is absolute or contains '..': {tmp!r}"
    if tmp != TARGET_HANDOFF_REL:
        return (
            f"target.target_manifest_path must equal "
            f"{TARGET_HANDOFF_REL!r}, got {tmp!r}"
        )
    sha = block.get("target_manifest_sha256")
    if not non_empty_str(sha):
        return "target.target_manifest_sha256 missing or empty"
    if sha != PLACEHOLDER_SHA256 and not SHA256_RE.match(sha):
        return (
            "target.target_manifest_sha256 must be the literal "
            f"{PLACEHOLDER_SHA256!r} or a real sha256:<64-hex>, "
            f"got {sha!r}"
        )
    if not non_empty_str(block.get("target_record_id")):
        return "target.target_record_id missing or empty"
    return None


def validate_evidence_refs(refs: Any) -> str | None:
    if not isinstance(refs, list) or len(refs) == 0:
        return "evidence_refs must be a non-empty list"
    for i, r in enumerate(refs):
        if not non_empty_str(r):
            return f"evidence_refs[{i}] not a non-empty string"
        if has_path_traversal(r):
            return f"evidence_refs[{i}] is absolute or contains '..': {r!r}"
    return None


def validate_packaged_challenge_record(rec: Any) -> str | None:
    """Structural-only validator for the packaged challenge record.

    Returns a detail string for any structural problem that should
    surface as ``challenge_record_invalid``. Closed-enum checks on
    ``challenge.challenge_reason`` / ``challenge.challenge_status`` and
    deep ``evidence_refs`` validation are DELIBERATELY excluded here
    so the dedicated reasons (``challenge_record_reason_invalid``,
    ``challenge_record_status_invalid``,
    ``challenge_record_evidence_ref_invalid``) are independently
    reachable in later ordered steps.
    """
    if not isinstance(rec, dict):
        return "challenge record is not a JSON object"
    if rec.get("document_type") != CHALLENGE_RECORD_DOCUMENT_TYPE:
        return (
            f"document_type must equal {CHALLENGE_RECORD_DOCUMENT_TYPE!r}, "
            f"got {rec.get('document_type')!r}"
        )
    if rec.get("schema_version") != SCHEMA_VERSION:
        return f"schema_version must equal {SCHEMA_VERSION!r}"
    if rec.get("proofrail_release") != PROOFRAIL_RELEASE:
        return f"proofrail_release must equal {PROOFRAIL_RELEASE!r}"
    if not non_empty_str(rec.get("challenge_record_id")):
        return "challenge_record_id missing or empty"
    if parse_iso_8601_z(rec.get("filed_at")) is None:
        return "filed_at not ISO-8601 UTC Z-suffixed"
    err = validate_principal_block(rec.get("filed_by"))
    if err is not None:
        return f"filed_by: {err}"
    err = validate_packaged_target_block(rec.get("target"))
    if err is not None:
        return f"target: {err}"
    ch = rec.get("challenge")
    if not isinstance(ch, dict):
        return "challenge block missing or not an object"
    if not non_empty_str(ch.get("challenge_reason")):
        return "challenge.challenge_reason missing or empty"
    if not non_empty_str(ch.get("challenge_status")):
        return "challenge.challenge_status missing or empty"
    if not non_empty_str_list(ch.get("challenge_basis")):
        return "challenge.challenge_basis must be a non-empty string list"
    if not non_empty_str(ch.get("requested_action")):
        return "challenge.requested_action missing or empty"
    if not isinstance(rec.get("evidence_refs"), list):
        return "evidence_refs missing or not a list"
    if not isinstance(rec.get("scope_limitations"), list):
        return "scope_limitations missing or not a list"
    if not isinstance(rec.get("non_claims"), list):
        return "non_claims missing or not a list"
    return None


def validate_packaged_withdrawal_record(rec: Any) -> str | None:
    """Structural-only validator for the packaged withdrawal record.

    Returns a detail string for any structural problem that should
    surface as ``withdrawal_record_invalid``. Closed-enum checks on
    ``withdrawal.withdrawal_reason`` / ``withdrawal.withdrawal_status``
    and deep ``evidence_refs`` validation are DELIBERATELY excluded
    here so the dedicated reasons
    (``withdrawal_record_reason_invalid``,
    ``withdrawal_record_status_invalid``,
    ``withdrawal_record_evidence_ref_invalid``) are independently
    reachable in later ordered steps. ``withdrawal_effect`` has no
    dedicated reason in the approved taxonomy; a wrong value
    therefore stays here under ``withdrawal_record_invalid``.
    """
    if not isinstance(rec, dict):
        return "withdrawal record is not a JSON object"
    if rec.get("document_type") != WITHDRAWAL_RECORD_DOCUMENT_TYPE:
        return (
            f"document_type must equal "
            f"{WITHDRAWAL_RECORD_DOCUMENT_TYPE!r}, "
            f"got {rec.get('document_type')!r}"
        )
    if rec.get("schema_version") != SCHEMA_VERSION:
        return f"schema_version must equal {SCHEMA_VERSION!r}"
    if rec.get("proofrail_release") != PROOFRAIL_RELEASE:
        return f"proofrail_release must equal {PROOFRAIL_RELEASE!r}"
    if not non_empty_str(rec.get("withdrawal_record_id")):
        return "withdrawal_record_id missing or empty"
    if parse_iso_8601_z(rec.get("recorded_at")) is None:
        return "recorded_at not ISO-8601 UTC Z-suffixed"
    if parse_iso_8601_z(rec.get("effective_at")) is None:
        return "effective_at not ISO-8601 UTC Z-suffixed"
    err = validate_principal_block(rec.get("recorded_by"))
    if err is not None:
        return f"recorded_by: {err}"
    err = validate_packaged_target_block(rec.get("target"))
    if err is not None:
        return f"target: {err}"
    if not non_empty_str(rec.get("related_challenge_record_id")):
        return "related_challenge_record_id missing or empty"
    wd = rec.get("withdrawal")
    if not isinstance(wd, dict):
        return "withdrawal block missing or not an object"
    if not non_empty_str(wd.get("withdrawal_reason")):
        return "withdrawal.withdrawal_reason missing or empty"
    if not non_empty_str(wd.get("withdrawal_status")):
        return "withdrawal.withdrawal_status missing or empty"
    # withdrawal_effect has no dedicated reason in the approved
    # taxonomy: keep the enum check here so a wrong value surfaces
    # as withdrawal_record_invalid.
    if wd.get("withdrawal_effect") not in WITHDRAWAL_EFFECTS:
        return (
            f"withdrawal.withdrawal_effect not in closed set: "
            f"{wd.get('withdrawal_effect')!r}"
        )
    if not isinstance(rec.get("evidence_refs"), list):
        return "evidence_refs missing or not a list"
    if not isinstance(rec.get("scope_limitations"), list):
        return "scope_limitations missing or not a list"
    if not isinstance(rec.get("non_claims"), list):
        return "non_claims missing or not a list"
    return None


# --------------------------------------------------------------------
# Summary structural validation
# --------------------------------------------------------------------


def validate_summary_shape(s: Any) -> str | None:
    if not isinstance(s, dict):
        return "summary is not a JSON object"
    if s.get("document_type") != SUMMARY_DOCUMENT_TYPE:
        return (
            f"document_type must equal {SUMMARY_DOCUMENT_TYPE!r}, "
            f"got {s.get('document_type')!r}"
        )
    if s.get("schema_version") != SCHEMA_VERSION:
        return f"schema_version must equal {SCHEMA_VERSION!r}"
    if s.get("proofrail_release") != PROOFRAIL_RELEASE:
        return f"proofrail_release must equal {PROOFRAIL_RELEASE!r}"
    if not non_empty_str(s.get("summary_id")):
        return "summary_id missing or empty"
    if parse_iso_8601_z(s.get("generated_at")) is None:
        return "generated_at not ISO-8601 UTC Z-suffixed"
    tgt = s.get("target")
    if not isinstance(tgt, dict):
        return "target block missing or not an object"
    if tgt.get("target_type") != "silver_acceptance_handoff":
        return "target.target_type must equal 'silver_acceptance_handoff'"
    if tgt.get("target_manifest_path") != TARGET_HANDOFF_REL:
        return (
            f"target.target_manifest_path must equal "
            f"{TARGET_HANDOFF_REL!r}"
        )
    if not isinstance(tgt.get("target_manifest_sha256"), str) or not SHA256_RE.match(
        tgt.get("target_manifest_sha256") or ""
    ):
        return "target.target_manifest_sha256 must be sha256:<64 hex>"
    recs = s.get("records")
    if not isinstance(recs, dict):
        return "records block missing or not an object"
    if recs.get("challenge_record_path") != CHALLENGE_RECORD_REL:
        return "records.challenge_record_path mismatch"
    if not SHA256_RE.match(recs.get("challenge_record_sha256") or ""):
        return "records.challenge_record_sha256 not sha256:<64 hex>"
    if recs.get("withdrawal_record_path") != WITHDRAWAL_RECORD_REL:
        return "records.withdrawal_record_path mismatch"
    if not SHA256_RE.match(recs.get("withdrawal_record_sha256") or ""):
        return "records.withdrawal_record_sha256 not sha256:<64 hex>"
    sm = s.get("summary")
    if not isinstance(sm, dict):
        return "summary.summary block missing or not an object"
    if not isinstance(sm.get("challenge_count"), int):
        return "summary.challenge_count missing or not an int"
    if not isinstance(sm.get("withdrawal_count"), int):
        return "summary.withdrawal_count missing or not an int"
    if not non_empty_str(sm.get("challenge_status")):
        return "summary.challenge_status missing or empty"
    if not non_empty_str(sm.get("withdrawal_status")):
        return "summary.withdrawal_status missing or empty"
    if not non_empty_str(sm.get("withdrawal_effect")):
        return "summary.withdrawal_effect missing or empty"
    if not non_empty_str(sm.get("posture")):
        return "summary.posture missing or empty"
    claims = s.get("claims")
    if not isinstance(claims, list):
        return "claims missing or not a list"
    if not isinstance(s.get("scope_limitations"), list):
        return "scope_limitations missing or not a list"
    if not isinstance(s.get("non_claims"), list):
        return "non_claims missing or not a list"
    return None


# --------------------------------------------------------------------
# Overclaim scan
# --------------------------------------------------------------------


def collect_strings_outside(
    obj: Any, exclude_top_keys: tuple[str, ...] = ()
) -> list[str]:
    """Collect every string value reachable inside obj EXCEPT inside
    top-level keys listed in exclude_top_keys."""
    out: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            out.append(node)

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in exclude_top_keys:
                continue
            walk(v)
    else:
        walk(obj)
    return out


def scan_overclaim(strings: list[str]) -> str | None:
    for s in strings:
        sl = s.lower()
        for token in FORBIDDEN_TOKENS:
            if token.lower() in sl:
                return (
                    f"forbidden overclaim token {token!r} found in "
                    f"free-text value {s!r}"
                )
    return None


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.4 challenge/withdrawal "
            "primitives package."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        return usage_error(f"--manifest not found: {manifest_path}")
    if not manifest_path.is_file():
        return usage_error(f"--manifest is not a file: {manifest_path}")

    package_root = manifest_path.parent

    # --- Step 1: parse manifest ---
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            f"manifest is not valid JSON: {e}",
        )

    # --- Step 2: manifest top-level shape ---
    if not isinstance(manifest, dict):
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "manifest is not a JSON object",
        )
    if manifest.get("document_type") != MANIFEST_DOCUMENT_TYPE:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            f"document_type must equal {MANIFEST_DOCUMENT_TYPE!r}, "
            f"got {manifest.get('document_type')!r}",
        )
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            f"schema_version must equal {SCHEMA_VERSION!r}",
        )
    if manifest.get("proofrail_release") != PROOFRAIL_RELEASE:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            f"proofrail_release must equal {PROOFRAIL_RELEASE!r}",
        )
    if not non_empty_str(manifest.get("manifest_id")):
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "manifest_id missing or empty",
        )
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "generated_at not ISO-8601 UTC Z-suffixed",
        )
    if manifest.get("hash_algorithm") != "sha256":
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "hash_algorithm must equal 'sha256'",
        )

    # presence-only check for scope_limitations / non_claims at this step
    if not isinstance(manifest.get("scope_limitations"), list):
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "scope_limitations missing or not a list",
        )
    if not isinstance(manifest.get("non_claims"), list):
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "non_claims missing or not a list",
        )

    # --- Step 3-4: subjects array shape ---
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return fail(
            "invalid_challenge_withdrawal_manifest",
            "subjects missing or not a list",
        )
    if len(subjects) != 4:
        return fail(
            "invalid_challenge_withdrawal_manifest",
            f"subjects must have exactly 4 entries, got {len(subjects)}",
        )

    # --- Step 5: path-traversal BEFORE exact path equality ---
    for i, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}] is not an object",
            )
        path_val = subj.get("path")
        if not isinstance(path_val, str) or path_val == "":
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}].path missing or empty",
            )
        if has_path_traversal(path_val):
            return fail(
                "challenge_withdrawal_subject_path_traversal",
                f"subjects[{i}].path is absolute or contains '..': {path_val!r}",
            )

    # --- Step 6: exact path / role match against fixed order ---
    for i, (expected_path, expected_role) in enumerate(SUBJECT_ORDER):
        if subjects[i].get("path") != expected_path:
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}].path must equal {expected_path!r}, "
                f"got {subjects[i].get('path')!r}",
            )
        if subjects[i].get("role") != expected_role:
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}].role must equal {expected_role!r}, "
                f"got {subjects[i].get('role')!r}",
            )

    # --- Step 7: each subject sha256 / size_bytes shape ---
    for i, subj in enumerate(subjects):
        sha = subj.get("sha256")
        if not isinstance(sha, str) or not SHA256_RE.match(sha):
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}].sha256 must be sha256:<64 hex>",
            )
        size_b = subj.get("size_bytes")
        if not isinstance(size_b, int) or size_b < 0:
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}].size_bytes must be a non-negative int",
            )

    # --- Step 8: each subject file exists ---
    for i, subj in enumerate(subjects):
        full = package_root / subj["path"]
        if not full.exists():
            return fail(
                "challenge_withdrawal_subject_file_missing",
                f"subjects[{i}] file missing on disk: {subj['path']}",
            )

    # --- Step 9: recompute sha256 + size for each subject ---
    for i, subj in enumerate(subjects):
        full = package_root / subj["path"]
        actual_sha = sha256_label(full)
        if actual_sha != subj["sha256"]:
            return fail(
                "challenge_withdrawal_subject_hash_mismatch",
                f"subjects[{i}] recomputed sha256 ({actual_sha}) does "
                f"not match recorded ({subj['sha256']})",
            )
        actual_size = full.stat().st_size
        if actual_size != subj["size_bytes"]:
            return fail(
                "invalid_challenge_withdrawal_manifest",
                f"subjects[{i}] size_bytes ({subj['size_bytes']}) does "
                f"not match actual ({actual_size})",
            )

    # --- Step 10: subprocess v0.3.0 verifier on target handoff ---
    target_manifest_path = package_root / TARGET_HANDOFF_REL
    proc = subprocess.run(
        [
            sys.executable,
            str(HANDOFF_VERIFIER),
            "--manifest",
            str(target_manifest_path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "nested_handoff_invalid",
            collect_fail_detail(proc),
        )

    # --- Step 11: parse target handoff manifest for cross-checks ---
    try:
        target_obj = json.loads(target_manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "nested_handoff_invalid",
            f"target handoff manifest not valid JSON: {e}",
        )
    if not isinstance(target_obj, dict):
        return fail(
            "nested_handoff_invalid",
            "target handoff manifest is not a JSON object",
        )
    target_handoff_id = target_obj.get("handoff_id")
    target_generated_at = target_obj.get("generated_at")
    target_generated_dt = parse_iso_8601_z(target_generated_at)
    if not non_empty_str(target_handoff_id) or target_generated_dt is None:
        return fail(
            "nested_handoff_invalid",
            "target handoff manifest missing handoff_id or "
            "generated_at after subprocess verification",
        )

    subj0_sha = subjects[0]["sha256"]
    subj1_sha = subjects[1]["sha256"]
    subj2_sha = subjects[2]["sha256"]
    subj3_sha = subjects[3]["sha256"]

    # --- Step 12: parse + structural-validate packaged challenge record ---
    challenge_path = package_root / CHALLENGE_RECORD_REL
    try:
        challenge_rec = json.loads(challenge_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "challenge_record_invalid",
            f"challenge record not valid JSON: {e}",
        )
    err = validate_packaged_challenge_record(challenge_rec)
    if err is not None:
        return fail("challenge_record_invalid", err)

    # --- Step 13: parse + structural-validate packaged withdrawal record ---
    withdrawal_path = package_root / WITHDRAWAL_RECORD_REL
    try:
        withdrawal_rec = json.loads(withdrawal_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "withdrawal_record_invalid",
            f"withdrawal record not valid JSON: {e}",
        )
    err = validate_packaged_withdrawal_record(withdrawal_rec)
    if err is not None:
        return fail("withdrawal_record_invalid", err)

    # --- Step 14: closed-enum check on challenge.challenge_reason ---
    ch_block = challenge_rec["challenge"]
    if ch_block["challenge_reason"] not in CHALLENGE_REASONS:
        return fail(
            "challenge_record_reason_invalid",
            f"challenge.challenge_reason not in closed set "
            f"{CHALLENGE_REASONS}: {ch_block['challenge_reason']!r}",
        )

    # --- Step 15: closed-enum check on challenge.challenge_status ---
    if ch_block["challenge_status"] not in CHALLENGE_STATUSES:
        return fail(
            "challenge_record_status_invalid",
            f"challenge.challenge_status not in closed set "
            f"{CHALLENGE_STATUSES}: {ch_block['challenge_status']!r}",
        )

    # --- Step 16: challenge record evidence_refs validation ---
    err = validate_evidence_refs(challenge_rec.get("evidence_refs"))
    if err is not None:
        return fail("challenge_record_evidence_ref_invalid", err)

    # --- Step 17: closed-enum check on withdrawal.withdrawal_reason ---
    wd_block = withdrawal_rec["withdrawal"]
    if wd_block["withdrawal_reason"] not in WITHDRAWAL_REASONS:
        return fail(
            "withdrawal_record_reason_invalid",
            f"withdrawal.withdrawal_reason not in closed set "
            f"{WITHDRAWAL_REASONS}: {wd_block['withdrawal_reason']!r}",
        )

    # --- Step 18: closed-enum check on withdrawal.withdrawal_status ---
    if wd_block["withdrawal_status"] not in WITHDRAWAL_STATUSES:
        return fail(
            "withdrawal_record_status_invalid",
            f"withdrawal.withdrawal_status not in closed set "
            f"{WITHDRAWAL_STATUSES}: {wd_block['withdrawal_status']!r}",
        )

    # --- Step 19: withdrawal record evidence_refs validation ---
    err = validate_evidence_refs(withdrawal_rec.get("evidence_refs"))
    if err is not None:
        return fail("withdrawal_record_evidence_ref_invalid", err)

    # --- Step 20: packaged challenge record target binding ---
    # Consolidates: placeholder still present, target_manifest_sha256
    # disagreement with subject [0], and target_record_id disagreement
    # with the parsed handoff_id.
    ch_target = challenge_rec["target"]
    if ch_target["target_manifest_sha256"] == PLACEHOLDER_SHA256:
        return fail(
            "challenge_record_target_mismatch",
            "packaged challenge record target.target_manifest_sha256 "
            f"still equals the literal placeholder {PLACEHOLDER_SHA256!r}",
        )
    if ch_target["target_manifest_sha256"] != subj0_sha:
        return fail(
            "challenge_record_target_mismatch",
            f"packaged challenge record target.target_manifest_sha256 "
            f"({ch_target['target_manifest_sha256']!r}) does not "
            f"match subject [0] sha256 ({subj0_sha!r})",
        )
    if ch_target["target_record_id"] != target_handoff_id:
        return fail(
            "challenge_record_target_mismatch",
            f"packaged challenge record target.target_record_id "
            f"({ch_target['target_record_id']!r}) does not match "
            f"target handoff_id ({target_handoff_id!r})",
        )

    # --- Step 21: packaged withdrawal record target binding ---
    wd_target = withdrawal_rec["target"]
    if wd_target["target_manifest_sha256"] == PLACEHOLDER_SHA256:
        return fail(
            "withdrawal_record_target_mismatch",
            "packaged withdrawal record target.target_manifest_sha256 "
            f"still equals the literal placeholder {PLACEHOLDER_SHA256!r}",
        )
    if wd_target["target_manifest_sha256"] != subj0_sha:
        return fail(
            "withdrawal_record_target_mismatch",
            f"packaged withdrawal record target.target_manifest_sha256 "
            f"({wd_target['target_manifest_sha256']!r}) does not "
            f"match subject [0] sha256 ({subj0_sha!r})",
        )
    if wd_target["target_record_id"] != target_handoff_id:
        return fail(
            "withdrawal_record_target_mismatch",
            f"packaged withdrawal record target.target_record_id "
            f"({wd_target['target_record_id']!r}) does not match "
            f"target handoff_id ({target_handoff_id!r})",
        )

    # --- Step 22: withdrawal cites challenge ---
    if (
        withdrawal_rec["related_challenge_record_id"]
        != challenge_rec["challenge_record_id"]
    ):
        return fail(
            "withdrawal_record_challenge_ref_mismatch",
            f"withdrawal.related_challenge_record_id "
            f"({withdrawal_rec['related_challenge_record_id']!r}) "
            f"does not match challenge.challenge_record_id "
            f"({challenge_rec['challenge_record_id']!r})",
        )

    # --- Step 23: time ordering ---
    cf = parse_iso_8601_z(challenge_rec["filed_at"])
    wr = parse_iso_8601_z(withdrawal_rec["recorded_at"])
    we = parse_iso_8601_z(withdrawal_rec["effective_at"])
    if cf < target_generated_dt:
        return fail(
            "challenge_withdrawal_time_order_invalid",
            f"challenge.filed_at ({challenge_rec['filed_at']!r}) "
            f"precedes target.generated_at ({target_generated_at!r})",
        )
    if wr < cf:
        return fail(
            "challenge_withdrawal_time_order_invalid",
            f"withdrawal.recorded_at ({withdrawal_rec['recorded_at']!r}) "
            f"precedes challenge.filed_at "
            f"({challenge_rec['filed_at']!r})",
        )
    if we < wr:
        return fail(
            "challenge_withdrawal_time_order_invalid",
            f"withdrawal.effective_at "
            f"({withdrawal_rec['effective_at']!r}) precedes "
            f"withdrawal.recorded_at "
            f"({withdrawal_rec['recorded_at']!r})",
        )

    # --- Step 24: parse + validate summary (incl. required-claims shape) ---
    summary_path = package_root / SUMMARY_REL
    try:
        summary = json.loads(summary_path.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "challenge_withdrawal_summary_invalid",
            f"summary not valid JSON: {e}",
        )
    err = validate_summary_shape(summary)
    if err is not None:
        return fail("challenge_withdrawal_summary_invalid", err)

    # The seven required claims are part of the summary document.
    # Any structural problem with the claims list folds into
    # challenge_withdrawal_summary_invalid (no dedicated reason in
    # the approved taxonomy).
    claims = summary["claims"]
    if len(claims) != len(REQUIRED_CLAIMS):
        return fail(
            "challenge_withdrawal_summary_invalid",
            f"claims list must have exactly {len(REQUIRED_CLAIMS)} "
            f"entries in fixed order, got {len(claims)}",
        )
    for i, expected_id in enumerate(REQUIRED_CLAIMS):
        c = claims[i]
        if not isinstance(c, dict):
            return fail(
                "challenge_withdrawal_summary_invalid",
                f"claims[{i}] is not an object",
            )
        if c.get("claim_id") != expected_id:
            return fail(
                "challenge_withdrawal_summary_invalid",
                f"claims[{i}].claim_id must equal {expected_id!r}, "
                f"got {c.get('claim_id')!r}",
            )
        if c.get("status") != "pass":
            return fail(
                "challenge_withdrawal_summary_invalid",
                f"claims[{i}].status must equal 'pass', got "
                f"{c.get('status')!r}",
            )
        refs = c.get("evidence_refs")
        if not isinstance(refs, list) or len(refs) == 0:
            return fail(
                "challenge_withdrawal_summary_invalid",
                f"claims[{i}].evidence_refs must be a non-empty list",
            )
        for j, r in enumerate(refs):
            if not non_empty_str(r):
                return fail(
                    "challenge_withdrawal_summary_invalid",
                    f"claims[{i}].evidence_refs[{j}] not a non-empty "
                    f"string",
                )
            if has_path_traversal(r):
                return fail(
                    "challenge_withdrawal_summary_invalid",
                    f"claims[{i}].evidence_refs[{j}] is absolute or "
                    f"contains '..': {r!r}",
                )
            if not any(
                r == p or r.startswith(p)
                for p in ALLOWED_CLAIM_EVIDENCE_PREFIXES
            ):
                return fail(
                    "challenge_withdrawal_summary_invalid",
                    f"claims[{i}].evidence_refs[{j}] {r!r} not within "
                    f"the allowed package-local prefix set "
                    f"{ALLOWED_CLAIM_EVIDENCE_PREFIXES}",
                )
        # If a "description" field is present, it must be a non-empty
        # string. Free-text overclaim scan picks it up below.
        if "description" in c and not non_empty_str(c.get("description")):
            return fail(
                "challenge_withdrawal_summary_invalid",
                f"claims[{i}].description present but not a non-empty "
                f"string",
            )

    # --- Step 25: summary target / records bindings + status echoes ---
    # The approved taxonomy folds status/effect echo divergences into
    # challenge_withdrawal_summary_binding_mismatch (the previous
    # `_status_mismatch` reason is removed).
    if summary["target"]["target_manifest_sha256"] != subj0_sha:
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.target.target_manifest_sha256 "
            f"({summary['target']['target_manifest_sha256']!r}) does "
            f"not match subject [0] sha256 ({subj0_sha!r})",
        )
    if summary["records"]["challenge_record_sha256"] != subj1_sha:
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.records.challenge_record_sha256 "
            f"({summary['records']['challenge_record_sha256']!r}) does "
            f"not match subject [1] sha256 ({subj1_sha!r})",
        )
    if summary["records"]["withdrawal_record_sha256"] != subj2_sha:
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.records.withdrawal_record_sha256 "
            f"({summary['records']['withdrawal_record_sha256']!r}) does "
            f"not match subject [2] sha256 ({subj2_sha!r})",
        )
    if (
        summary["summary"]["challenge_status"]
        != challenge_rec["challenge"]["challenge_status"]
    ):
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.summary.challenge_status "
            f"({summary['summary']['challenge_status']!r}) does not "
            f"echo challenge.challenge.challenge_status "
            f"({challenge_rec['challenge']['challenge_status']!r})",
        )
    if (
        summary["summary"]["withdrawal_status"]
        != withdrawal_rec["withdrawal"]["withdrawal_status"]
    ):
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.summary.withdrawal_status "
            f"({summary['summary']['withdrawal_status']!r}) does not "
            f"echo withdrawal.withdrawal.withdrawal_status "
            f"({withdrawal_rec['withdrawal']['withdrawal_status']!r})",
        )
    if (
        summary["summary"]["withdrawal_effect"]
        != withdrawal_rec["withdrawal"]["withdrawal_effect"]
    ):
        return fail(
            "challenge_withdrawal_summary_binding_mismatch",
            f"summary.summary.withdrawal_effect "
            f"({summary['summary']['withdrawal_effect']!r}) does not "
            f"echo withdrawal.withdrawal.withdrawal_effect "
            f"({withdrawal_rec['withdrawal']['withdrawal_effect']!r})",
        )

    # --- Step 26: counts (singular reason: _count_mismatch) ---
    if summary["summary"]["challenge_count"] != 1:
        return fail(
            "challenge_withdrawal_summary_count_mismatch",
            f"summary.summary.challenge_count must equal 1, got "
            f"{summary['summary']['challenge_count']!r}",
        )
    if summary["summary"]["withdrawal_count"] != 1:
        return fail(
            "challenge_withdrawal_summary_count_mismatch",
            f"summary.summary.withdrawal_count must equal 1, got "
            f"{summary['summary']['withdrawal_count']!r}",
        )

    # --- Step 27: posture closed set + table ---
    posture = summary["summary"]["posture"]
    if posture not in POSTURES:
        return fail(
            "challenge_withdrawal_posture_invalid",
            f"summary.summary.posture not in closed set {POSTURES}: "
            f"{posture!r}",
        )
    we_value = withdrawal_rec["withdrawal"]["withdrawal_effect"]
    expected_posture = WITHDRAWAL_EFFECT_TO_POSTURE.get(we_value)
    if expected_posture is None or posture != expected_posture:
        return fail(
            "challenge_withdrawal_posture_invalid",
            f"summary.summary.posture ({posture!r}) does not match "
            f"the posture mapping table entry for withdrawal_effect "
            f"({we_value!r}); expected {expected_posture!r}",
        )

    # --- Step 28: overclaim scan ---
    strings = collect_strings_outside(
        summary, exclude_top_keys=("scope_limitations", "non_claims")
    )
    err = scan_overclaim(strings)
    if err is not None:
        return fail("challenge_withdrawal_overclaim", err)

    # --- Step 29: scope_limitations / non_claims non-empty +
    #              no blank entries (manifest AND summary) ---
    for label, src in (
        ("manifest", manifest),
        ("summary", summary),
    ):
        sl = src.get("scope_limitations")
        if not isinstance(sl, list) or len(sl) == 0 or not all(
            non_empty_str(x) for x in sl
        ):
            return fail(
                "challenge_withdrawal_limitations_missing",
                f"{label}.scope_limitations must be a non-empty list "
                "of non-empty strings",
            )
    for label, src in (
        ("manifest", manifest),
        ("summary", summary),
    ):
        nc = src.get("non_claims")
        if not isinstance(nc, list) or len(nc) == 0 or not all(
            non_empty_str(x) for x in nc
        ):
            return fail(
                "challenge_withdrawal_non_claims_missing",
                f"{label}.non_claims must be a non-empty list of "
                "non-empty strings",
            )

    print(
        f"PASS: silver challenge/withdrawal primitives package verified "
        f"at {package_root}"
    )
    print(f"  manifest_id: {manifest['manifest_id']}")
    print(f"  summary_id:  {summary['summary_id']}")
    print(f"  posture:     {posture}")
    print(f"  target handoff_id: {target_handoff_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
