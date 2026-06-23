#!/usr/bin/env python3
"""Build a ProofRail Silver v0.3.4 challenge/withdrawal primitives package.

The runner composes a deterministic, hash-anchored, local Silver
package that binds a v0.3.0 acceptance handoff target with two new
record primitives:

  - a Silver challenge record;
  - a Silver withdrawal record;

and a derived challenge/withdrawal summary.

Behavior:

  1.  Parses CLI; validates --generated-at as ISO-8601 UTC Z-suffixed.
  2.  Refuses to overwrite --output-dir unless --force is supplied.
  3.  Resolves --target-handoff-root and locates the v0.3.0 acceptance
      handoff manifest at
          <target-handoff-root>/silver-acceptance-handoff-manifest.json
  4.  Subprocess-invokes the unchanged v0.3.0 handoff verifier on that
      manifest. On non-zero exit prints
          FAIL: handoff_validation_failed: <detail>
      and exits 1.
  5.  Parses the input --challenge-record fixture and structurally
      validates it (closed enums, ISO-8601 times, target object,
      filed_by, evidence_refs, scope_limitations, non_claims). Refuses
      with
          FAIL: challenge_record_validation_failed: <detail>
      on any structural issue. The runner accepts the literal
      placeholder
          "sha256:TO_BE_BOUND_BY_RUNNER"
      in target.target_manifest_sha256 of the INPUT fixture only; it
      is rewritten to the real sha256 of the copied target manifest
      before staging the bound record. (The v0.3.4 verifier rejects
      that placeholder in any packaged record.)
  6.  Parses the input --withdrawal-record fixture and structurally
      validates it (closed enums, ISO-8601 times, target object,
      recorded_by, related_challenge_record_id, evidence_refs,
      scope_limitations, non_claims). Refuses with
          FAIL: withdrawal_record_validation_failed: <detail>
      on any structural issue. The same placeholder rule applies.
  7.  Cross-binds the two input records against the target handoff
      (target_record_id == handoff_id, target_manifest_path matches),
      enforces time order
          target.generated_at <= challenge.filed_at
          challenge.filed_at  <= withdrawal.recorded_at
          withdrawal.recorded_at <= withdrawal.effective_at
      and enforces withdrawal.related_challenge_record_id ==
      challenge.challenge_record_id. Refuses with
          FAIL: challenge_withdrawal_binding_failed: <detail>
      on any binding failure.
  8.  Stages output under a sibling staging directory.
  9.  Byte-copies the target handoff package root into
          <staging>/target-handoff/
 10.  Hashes the copied target manifest, rewrites both records'
      target.target_manifest_sha256 from the placeholder to the real
      sha256, and writes the BOUND records to
          <staging>/records/challenge-record.json
          <staging>/records/withdrawal-record.json
      as canonical deterministic JSON (sorted keys, stable indent).
      The post-binding bytes are what the manifest hashes; the runner
      does not promise input-fixture byte preservation.
 11.  Derives the challenge/withdrawal summary deterministically from
      the bound records and the copied target handoff:
        - records.*_sha256 from the staged record bytes;
        - summary.challenge_count = 1, withdrawal_count = 1;
        - summary.challenge_status echoes the bound challenge;
        - summary.withdrawal_status / withdrawal_effect echo the bound
          withdrawal;
        - summary.posture is selected by the closed
          withdrawal_effect -> posture table; and
        - the seven required claims are emitted in the fixed order
          with status "pass" and safe package-local evidence_refs.
      Writes
          <staging>/silver-challenge-withdrawal-summary.json
 12.  Builds the v0.3.4 manifest with exactly four subjects in fixed
      order:
        [0] target-handoff/silver-acceptance-handoff-manifest.json
        [1] records/challenge-record.json
        [2] records/withdrawal-record.json
        [3] silver-challenge-withdrawal-summary.json
      Writes
          <staging>/silver-challenge-withdrawal-manifest.json
 13.  When --self-validate is supplied, subprocess-invokes the v0.3.4
      verifier on the staged manifest BEFORE moving into place. On
      non-zero exit prints
          FAIL: challenge_withdrawal_self_validation_failed: <detail>
      removes the staging directory (leaving the destination
      untouched), and exits 1.
 14.  Atomically replaces --output-dir with the staging directory via
      os.replace().

No external services. No real challenge adjudication. No revocation.
No signing. No Gold governance.

Usage:
  python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py \\
    --target-handoff-root /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \\
    --challenge-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json \\
    --withdrawal-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json \\
    --manifest-id proofrail-silver-challenge-withdrawal-manifest-demo-001 \\
    --summary-id proofrail-silver-challenge-withdrawal-summary-demo-001 \\
    --generated-at 2026-06-29T00:30:00Z \\
    --output-dir /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4 \\
    --force \\
    [--self-validate]

Exit codes:
  0 - package generated
  1 - refusal (handoff_validation_failed,
      challenge_record_validation_failed,
      withdrawal_record_validation_failed,
      challenge_withdrawal_binding_failed,
      challenge_withdrawal_self_validation_failed)
  2 - usage or input-file error
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
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools" / "silver"

HANDOFF_VERIFIER = TOOLS_DIR / "verify_silver_acceptance_handoff_v0_1_0.py"

# Module constant so the regression test can monkey-patch the verifier
# path used for --self-validate.
CHALLENGE_WITHDRAWAL_VERIFIER = (
    TOOLS_DIR / "verify_silver_challenge_withdrawal_primitives_v0_1_0.py"
)

CHALLENGE_RECORD_DOCUMENT_TYPE = "proofrail.silver.challenge_record"
WITHDRAWAL_RECORD_DOCUMENT_TYPE = "proofrail.silver.withdrawal_record"
SUMMARY_DOCUMENT_TYPE = "proofrail.silver.challenge_withdrawal_summary"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.challenge_withdrawal_manifest"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.4"

PLACEHOLDER_SHA256 = "sha256:TO_BE_BOUND_BY_RUNNER"

TARGET_HANDOFF_MANIFEST_NAME = "silver-acceptance-handoff-manifest.json"
TARGET_HANDOFF_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_manifest"

TARGET_HANDOFF_REL = (
    "target-handoff/silver-acceptance-handoff-manifest.json"
)
CHALLENGE_RECORD_REL = "records/challenge-record.json"
WITHDRAWAL_RECORD_REL = "records/withdrawal-record.json"
SUMMARY_REL = "silver-challenge-withdrawal-summary.json"

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

# withdrawal_effect -> posture
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

DEFAULT_SUMMARY_SCOPE_LIMITATIONS = [
    "This summary applies only to the bound v0.3.0 acceptance handoff "
    "target, the bound challenge record, and the bound withdrawal "
    "record.",
    "This summary records local review posture only; it does not "
    "adjudicate the challenge or finalize a legal withdrawal.",
    "This summary does not implement Gold governance and does not "
    "transfer reliance to any downstream party.",
]
DEFAULT_SUMMARY_NON_CLAIMS = [
    "This summary is not a Gold certificate.",
    "This summary is not a regulator approval.",
    "This summary is not a legal revocation of reliance.",
    "This summary is not a third-party audit.",
    "This summary is not an adjudication of the recorded challenge.",
    "This summary is not approved for production reliance.",
]

DEFAULT_MANIFEST_SCOPE_LIMITATIONS = [
    "This manifest hash-anchors a local, demo Silver "
    "challenge/withdrawal primitives package; it is not signed.",
    "This manifest does not establish Gold conformance.",
    "This manifest does not transfer reliance to any downstream party.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This manifest does not adjudicate the challenge.",
    "This manifest does not legally revoke reliance.",
    "This manifest does not certify the target handoff.",
    "This manifest does not approve production reliance.",
]

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
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


def sha256_bytes_label(buf: bytes) -> str:
    return "sha256:" + hashlib.sha256(buf).hexdigest()


def dump_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, 2-space indent, trailing \\n."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


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
# Input record structural validation
# --------------------------------------------------------------------


def validate_principal_block(block: Any) -> str | None:
    if not isinstance(block, dict):
        return "principal block missing or not an object"
    if not non_empty_str(block.get("principal_id")):
        return "principal_id missing or empty"
    if not non_empty_str(block.get("role")):
        return "role missing or empty"
    return None


def validate_target_block(block: Any) -> str | None:
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
    if sha != PLACEHOLDER_SHA256 and not re.match(
        r"^sha256:[0-9a-f]{64}$", sha
    ):
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


def validate_challenge_record(rec: Any) -> str | None:
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
    err = validate_target_block(rec.get("target"))
    if err is not None:
        return f"target: {err}"
    ch = rec.get("challenge")
    if not isinstance(ch, dict):
        return "challenge block missing or not an object"
    if ch.get("challenge_reason") not in CHALLENGE_REASONS:
        return (
            f"challenge.challenge_reason not in closed set "
            f"{CHALLENGE_REASONS}: {ch.get('challenge_reason')!r}"
        )
    if ch.get("challenge_status") not in CHALLENGE_STATUSES:
        return (
            f"challenge.challenge_status not in closed set "
            f"{CHALLENGE_STATUSES}: {ch.get('challenge_status')!r}"
        )
    if not non_empty_str_list(ch.get("challenge_basis")):
        return (
            "challenge.challenge_basis must be a non-empty list of "
            "non-empty strings"
        )
    if not non_empty_str(ch.get("requested_action")):
        return "challenge.requested_action missing or empty"
    err = validate_evidence_refs(rec.get("evidence_refs"))
    if err is not None:
        return f"evidence_refs: {err}"
    if not non_empty_str_list(rec.get("scope_limitations")):
        return "scope_limitations must be a non-empty list of non-empty strings"
    if not non_empty_str_list(rec.get("non_claims")):
        return "non_claims must be a non-empty list of non-empty strings"
    return None


def validate_withdrawal_record(rec: Any) -> str | None:
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
    err = validate_target_block(rec.get("target"))
    if err is not None:
        return f"target: {err}"
    if not non_empty_str(rec.get("related_challenge_record_id")):
        return "related_challenge_record_id missing or empty"
    wd = rec.get("withdrawal")
    if not isinstance(wd, dict):
        return "withdrawal block missing or not an object"
    if wd.get("withdrawal_reason") not in WITHDRAWAL_REASONS:
        return (
            f"withdrawal.withdrawal_reason not in closed set "
            f"{WITHDRAWAL_REASONS}: {wd.get('withdrawal_reason')!r}"
        )
    if wd.get("withdrawal_status") not in WITHDRAWAL_STATUSES:
        return (
            f"withdrawal.withdrawal_status not in closed set "
            f"{WITHDRAWAL_STATUSES}: {wd.get('withdrawal_status')!r}"
        )
    if wd.get("withdrawal_effect") not in WITHDRAWAL_EFFECTS:
        return (
            f"withdrawal.withdrawal_effect not in closed set "
            f"{WITHDRAWAL_EFFECTS}: {wd.get('withdrawal_effect')!r}"
        )
    err = validate_evidence_refs(rec.get("evidence_refs"))
    if err is not None:
        return f"evidence_refs: {err}"
    if not non_empty_str_list(rec.get("scope_limitations")):
        return "scope_limitations must be a non-empty list of non-empty strings"
    if not non_empty_str_list(rec.get("non_claims")):
        return "non_claims must be a non-empty list of non-empty strings"
    return None


# --------------------------------------------------------------------
# Target handoff manifest probe
# --------------------------------------------------------------------


def parse_target_handoff_manifest(manifest_path: Path) -> tuple[Any, str | None]:
    if not manifest_path.exists():
        return None, f"target handoff manifest not found: {manifest_path}"
    try:
        obj = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return None, f"target handoff manifest is not valid JSON: {e}"
    if not isinstance(obj, dict):
        return None, "target handoff manifest is not a JSON object"
    if obj.get("document_type") != TARGET_HANDOFF_DOCUMENT_TYPE:
        return None, (
            f"target handoff manifest document_type must equal "
            f"{TARGET_HANDOFF_DOCUMENT_TYPE!r}, got "
            f"{obj.get('document_type')!r}"
        )
    if not non_empty_str(obj.get("handoff_id")):
        return None, "target handoff manifest handoff_id missing or empty"
    if parse_iso_8601_z(obj.get("generated_at")) is None:
        return None, (
            "target handoff manifest generated_at not ISO-8601 UTC "
            "Z-suffixed"
        )
    return obj, None


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a ProofRail Silver v0.3.4 challenge/withdrawal "
            "primitives package that hash-binds a v0.3.0 acceptance "
            "handoff target to a Silver challenge record, a Silver "
            "withdrawal record, and a derived summary."
        )
    )
    parser.add_argument("--target-handoff-root", required=True, type=Path)
    parser.add_argument("--challenge-record", required=True, type=Path)
    parser.add_argument("--withdrawal-record", required=True, type=Path)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--manifest-id",
        default="proofrail-silver-challenge-withdrawal-manifest-demo-001",
    )
    parser.add_argument(
        "--summary-id",
        default="proofrail-silver-challenge-withdrawal-summary-demo-001",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help=(
            "Run the v0.3.4 verifier on the staged package BEFORE "
            "moving into place. On failure, the staging directory is "
            "removed and the destination is left untouched."
        ),
    )
    args = parser.parse_args(argv)

    if parse_iso_8601_z(args.generated_at) is None:
        return usage_error("--generated-at must be ISO-8601 UTC Z-suffixed")
    if not non_empty_str(args.manifest_id):
        return usage_error("--manifest-id must be a non-empty string")
    if not non_empty_str(args.summary_id):
        return usage_error("--summary-id must be a non-empty string")

    target_root = args.target_handoff_root.resolve()
    if not target_root.exists():
        return usage_error(
            f"--target-handoff-root not found: {target_root}"
        )
    if not target_root.is_dir():
        return usage_error(
            f"--target-handoff-root is not a directory: {target_root}"
        )

    target_manifest = target_root / TARGET_HANDOFF_MANIFEST_NAME
    if not target_manifest.exists():
        return usage_error(
            f"target handoff manifest not found at "
            f"{target_manifest}"
        )

    challenge_input = args.challenge_record.resolve()
    if not challenge_input.exists() or not challenge_input.is_file():
        return usage_error(
            f"--challenge-record not found or not a file: {challenge_input}"
        )

    withdrawal_input = args.withdrawal_record.resolve()
    if not withdrawal_input.exists() or not withdrawal_input.is_file():
        return usage_error(
            f"--withdrawal-record not found or not a file: {withdrawal_input}"
        )

    out = args.output_dir.resolve()
    if out.exists() and not args.force:
        return usage_error(
            f"--output-dir already exists: {out} (use --force)"
        )

    # --- Subprocess-invoke v0.3.0 handoff verifier ---
    proc = subprocess.run(
        [
            sys.executable,
            str(HANDOFF_VERIFIER),
            "--manifest",
            str(target_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "handoff_validation_failed", collect_fail_detail(proc)
        )

    # --- Parse target handoff manifest (post-verify, trusted shape) ---
    target_obj, err = parse_target_handoff_manifest(target_manifest)
    if err is not None:
        return fail("handoff_validation_failed", err)
    target_handoff_id = target_obj.get("handoff_id")
    target_generated_at = target_obj.get("generated_at")
    target_generated_dt = parse_iso_8601_z(target_generated_at)
    if target_generated_dt is None:
        # Unreachable after parse_target_handoff_manifest, but kept
        # defensive.
        return fail(
            "handoff_validation_failed",
            "target handoff generated_at not parseable",
        )

    # --- Parse + structurally validate input challenge record ---
    try:
        challenge_in = json.loads(challenge_input.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "challenge_record_validation_failed",
            f"--challenge-record is not valid JSON: {e}",
        )
    err = validate_challenge_record(challenge_in)
    if err is not None:
        return fail("challenge_record_validation_failed", err)

    # --- Parse + structurally validate input withdrawal record ---
    try:
        withdrawal_in = json.loads(withdrawal_input.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "withdrawal_record_validation_failed",
            f"--withdrawal-record is not valid JSON: {e}",
        )
    err = validate_withdrawal_record(withdrawal_in)
    if err is not None:
        return fail("withdrawal_record_validation_failed", err)

    # --- Cross-binding checks (challenge_withdrawal_binding_failed) ---

    # target_record_id binding
    if challenge_in["target"]["target_record_id"] != target_handoff_id:
        return fail(
            "challenge_withdrawal_binding_failed",
            f"challenge.target.target_record_id "
            f"({challenge_in['target']['target_record_id']!r}) does "
            f"not match target handoff_id "
            f"({target_handoff_id!r})",
        )
    if withdrawal_in["target"]["target_record_id"] != target_handoff_id:
        return fail(
            "challenge_withdrawal_binding_failed",
            f"withdrawal.target.target_record_id "
            f"({withdrawal_in['target']['target_record_id']!r}) does "
            f"not match target handoff_id "
            f"({target_handoff_id!r})",
        )

    # both records must target the SAME handoff (record id symmetry)
    if (
        challenge_in["target"]["target_record_id"]
        != withdrawal_in["target"]["target_record_id"]
    ):
        return fail(
            "challenge_withdrawal_binding_failed",
            "challenge and withdrawal target.target_record_id values "
            "disagree",
        )

    # target_manifest_path is checked by validate_*_record to equal
    # TARGET_HANDOFF_REL.

    # related_challenge_record_id binding
    if (
        withdrawal_in["related_challenge_record_id"]
        != challenge_in["challenge_record_id"]
    ):
        return fail(
            "challenge_withdrawal_binding_failed",
            f"withdrawal.related_challenge_record_id "
            f"({withdrawal_in['related_challenge_record_id']!r}) does "
            f"not match challenge.challenge_record_id "
            f"({challenge_in['challenge_record_id']!r})",
        )

    # Time ordering:
    #   target.generated_at <= challenge.filed_at
    #   challenge.filed_at  <= withdrawal.recorded_at
    #   withdrawal.recorded_at <= withdrawal.effective_at
    challenge_filed_dt = parse_iso_8601_z(challenge_in["filed_at"])
    withdrawal_recorded_dt = parse_iso_8601_z(withdrawal_in["recorded_at"])
    withdrawal_effective_dt = parse_iso_8601_z(withdrawal_in["effective_at"])
    if challenge_filed_dt < target_generated_dt:
        return fail(
            "challenge_withdrawal_binding_failed",
            f"challenge.filed_at ({challenge_in['filed_at']!r}) "
            f"precedes target.generated_at "
            f"({target_generated_at!r})",
        )
    if withdrawal_recorded_dt < challenge_filed_dt:
        return fail(
            "challenge_withdrawal_binding_failed",
            f"withdrawal.recorded_at "
            f"({withdrawal_in['recorded_at']!r}) precedes "
            f"challenge.filed_at "
            f"({challenge_in['filed_at']!r})",
        )
    if withdrawal_effective_dt < withdrawal_recorded_dt:
        return fail(
            "challenge_withdrawal_binding_failed",
            f"withdrawal.effective_at "
            f"({withdrawal_in['effective_at']!r}) precedes "
            f"withdrawal.recorded_at "
            f"({withdrawal_in['recorded_at']!r})",
        )

    # --- Stage output ---
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = out.parent / f"{out.name}.staging.{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)

    def cleanup_staging() -> None:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    try:
        staging.mkdir(parents=True)

        # --- Byte-copy target handoff package root ---
        dest_target = staging / "target-handoff"
        shutil.copytree(target_root, dest_target)

        copied_target_manifest = (
            dest_target / TARGET_HANDOFF_MANIFEST_NAME
        )
        if not copied_target_manifest.exists():
            cleanup_staging()
            return fail(
                "challenge_withdrawal_binding_failed",
                "target handoff manifest missing after byte-copy",
            )

        # --- Hash the copied target manifest ---
        target_manifest_sha = sha256_label(copied_target_manifest)

        # --- Bind records: rewrite placeholder to real sha256 ---
        bound_challenge = json.loads(json.dumps(challenge_in))
        bound_challenge["target"]["target_manifest_sha256"] = (
            target_manifest_sha
        )

        bound_withdrawal = json.loads(json.dumps(withdrawal_in))
        bound_withdrawal["target"]["target_manifest_sha256"] = (
            target_manifest_sha
        )

        # --- Write bound records as canonical deterministic JSON ---
        records_dir = staging / "records"
        records_dir.mkdir(parents=True)
        bound_challenge_path = records_dir / "challenge-record.json"
        bound_withdrawal_path = records_dir / "withdrawal-record.json"
        bound_challenge_path.write_text(dump_json(bound_challenge))
        bound_withdrawal_path.write_text(dump_json(bound_withdrawal))

        challenge_sha = sha256_label(bound_challenge_path)
        withdrawal_sha = sha256_label(bound_withdrawal_path)

        # --- Derive summary ---
        withdrawal_effect = bound_withdrawal["withdrawal"]["withdrawal_effect"]
        posture = WITHDRAWAL_EFFECT_TO_POSTURE[withdrawal_effect]

        # Build claims (in fixed order). Each claim status is "pass"
        # with at least one safe package-local evidence_ref. No
        # description is emitted by default; the schema reserves
        # description as the optional free-text field the overclaim
        # guard scans (used by the regression test).
        claims_by_id = {
            "target_handoff_verified": [
                TARGET_HANDOFF_REL,
            ],
            "challenge_record_valid": [
                CHALLENGE_RECORD_REL,
            ],
            "withdrawal_record_valid": [
                WITHDRAWAL_RECORD_REL,
            ],
            "challenge_and_withdrawal_target_same_handoff": [
                CHALLENGE_RECORD_REL,
                WITHDRAWAL_RECORD_REL,
            ],
            "withdrawal_cites_challenge": [
                CHALLENGE_RECORD_REL,
                WITHDRAWAL_RECORD_REL,
            ],
            "time_order_valid": [
                TARGET_HANDOFF_REL,
                CHALLENGE_RECORD_REL,
                WITHDRAWAL_RECORD_REL,
            ],
            "no_adjudication_claimed": [
                CHALLENGE_RECORD_REL,
                WITHDRAWAL_RECORD_REL,
            ],
        }
        claims = [
            {
                "claim_id": cid,
                "status": "pass",
                "evidence_refs": list(claims_by_id[cid]),
            }
            for cid in REQUIRED_CLAIMS
        ]

        summary = {
            "document_type": SUMMARY_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "summary_id": args.summary_id,
            "generated_at": args.generated_at,
            "target": {
                "target_type": "silver_acceptance_handoff",
                "target_manifest_path": TARGET_HANDOFF_REL,
                "target_manifest_sha256": target_manifest_sha,
            },
            "records": {
                "challenge_record_path": CHALLENGE_RECORD_REL,
                "challenge_record_sha256": challenge_sha,
                "withdrawal_record_path": WITHDRAWAL_RECORD_REL,
                "withdrawal_record_sha256": withdrawal_sha,
            },
            "summary": {
                "challenge_count": 1,
                "withdrawal_count": 1,
                "challenge_status": bound_challenge["challenge"][
                    "challenge_status"
                ],
                "withdrawal_status": bound_withdrawal["withdrawal"][
                    "withdrawal_status"
                ],
                "withdrawal_effect": withdrawal_effect,
                "posture": posture,
            },
            "claims": claims,
            "scope_limitations": list(DEFAULT_SUMMARY_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_SUMMARY_NON_CLAIMS),
        }

        summary_path = staging / SUMMARY_REL
        summary_path.write_text(dump_json(summary))
        summary_sha = sha256_label(summary_path)

        # --- Build manifest (4 subjects, fixed order) ---
        subjects_spec = [
            (TARGET_HANDOFF_REL, "target_handoff_manifest", target_manifest_sha),
            (CHALLENGE_RECORD_REL, "challenge_record", challenge_sha),
            (WITHDRAWAL_RECORD_REL, "withdrawal_record", withdrawal_sha),
            (SUMMARY_REL, "challenge_withdrawal_summary", summary_sha),
        ]
        subjects: list[dict] = []
        for rel, role, sha in subjects_spec:
            full = staging / rel
            subjects.append(
                {
                    "path": rel,
                    "role": role,
                    "sha256": sha,
                    "size_bytes": full.stat().st_size,
                }
            )

        manifest = {
            "document_type": MANIFEST_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "manifest_id": args.manifest_id,
            "generated_at": args.generated_at,
            "hash_algorithm": "sha256",
            "subjects": subjects,
            "scope_limitations": list(DEFAULT_MANIFEST_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
        }
        manifest_path = staging / "silver-challenge-withdrawal-manifest.json"
        manifest_path.write_text(dump_json(manifest))

        # --- Self-validate BEFORE atomic move ---
        if args.self_validate:
            sv = subprocess.run(
                [
                    sys.executable,
                    str(CHALLENGE_WITHDRAWAL_VERIFIER),
                    "--manifest",
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )
            if sv.returncode != 0:
                detail = collect_fail_detail(sv)
                cleanup_staging()
                return fail(
                    "challenge_withdrawal_self_validation_failed",
                    detail,
                )

        # --- Atomic move ---
        if out.exists():
            shutil.rmtree(out)
        os.replace(str(staging), str(out))
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(
        f"PASS: silver challenge/withdrawal primitives package built at {out}"
    )
    print(f"  manifest_id: {args.manifest_id}")
    print(f"  summary_id:  {args.summary_id}")
    print(f"  target handoff_id: {target_handoff_id}")
    print(f"  posture: {posture}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
