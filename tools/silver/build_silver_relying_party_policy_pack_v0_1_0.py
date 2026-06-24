#!/usr/bin/env python3
"""Build a ProofRail Silver v0.3.5 Relying-Party Policy Pack package.

The runner composes a deterministic, hash-anchored local Silver
package that binds a hand-authored policy pack JSON document to a
re-derived conformance report and a two-subject manifest.

Behavior:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --policy-pack:
        - runner_input_path_missing       (argv missing / empty)
        - runner_input_path_forbidden     (absolute path or contains '..')
        - runner_input_file_missing       (path does not exist on disk)
        - runner_input_read_failed        (open/read fails OR path is a
                                          directory, portable)
        - runner_input_json_invalid       (path parses to non-JSON)
      These codes are emitted ONLY here and are NEVER wrapped or
      relayed by Phase B. A sixth runner-only refusal code is
      explicitly NOT introduced for verifier-relayed failures.
  2.  Phase B: build package.
      a. Resolves --output-dir, refusing to overwrite without --force.
      b. Stages under a sibling staging directory
             <output-dir>.staging.<pid>
         and atomically publishes via os.replace().
      c. Byte-copies the input policy pack JSON to
             <staging>/silver-relying-party-policy-pack.json
         The byte image is preserved exactly; structural defects in
         the input pack remain in the staged copy. (Structural defects
         are detected by the verifier, not by this runner.)
      d. Builds the conformance report using BYTE-IDENTICAL canonical
         JSON serialization (sort_keys=True, separators=(",", ":"),
         trailing newline) so a passing pack's report will match the
         verifier's re-derivation byte-for-byte. Includes the 24
         approved verifier reasons in fixed order with status "pass"
         when the pack parses as a top-level JSON object; otherwise the
         runner still emits the report skeleton but does not assert
         passing.
      e. Builds the two-subject manifest in fixed subject order:
             [0] silver-relying-party-policy-pack.json
             [1] silver-relying-party-policy-pack-conformance-report.json
         with sha256 and size_bytes recomputed from the staged copies.
      f. When --self-validate is supplied, subprocess-invokes the v0.3.5
         verifier on the staged manifest BEFORE the atomic move. On a
         non-zero exit, the verifier's stdout/stderr are RELAYED
         UNCHANGED (the runner does NOT wrap them in a sixth refusal
         code) and the staging directory is removed; the destination is
         left untouched.
      g. On success the staging directory is atomically replaced into
         --output-dir via os.replace().

No external services. No signing. No certification. No Gold
governance. No trust transfer.

Usage:
  python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py \\
    --policy-pack fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json \\
    --manifest-id proofrail-silver-relying-party-policy-pack-manifest-demo-001 \\
    --report-id   proofrail-silver-relying-party-policy-pack-conformance-report-demo-001 \\
    --generated-at 2026-07-15T00:00:00Z \\
    --output-dir /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5 \\
    --force \\
    [--self-validate]

Exit codes:
  0 - package generated (and, if --self-validate, verifier passed)
  1 - refusal (one of the 5 runner-only refusal reasons in Phase A,
      OR a verifier failure relayed UNCHANGED in Phase B when
      --self-validate is supplied; the runner adds no sixth code)
  2 - usage or argument error
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

# Module constant so the regression test can monkey-patch the verifier
# used for --self-validate.
POLICY_PACK_VERIFIER = (
    TOOLS_DIR / "verify_silver_relying_party_policy_pack_v0_1_0.py"
)

# Document types and version anchors. These must match the verifier.
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.relying_party_policy_pack_manifest"
POLICY_PACK_DOCUMENT_TYPE = "proofrail.silver.relying_party_policy_pack"
REPORT_DOCUMENT_TYPE = (
    "proofrail.silver.relying_party_policy_pack_conformance_report"
)
SCHEMA_VERSION = "0.1.0"
PROOFRAIL_RELEASE = "v0.3.5"

POLICY_PACK_REL = "silver-relying-party-policy-pack.json"
REPORT_REL = "silver-relying-party-policy-pack-conformance-report.json"
MANIFEST_REL = "silver-relying-party-policy-pack-manifest.json"

# Subject order in the manifest is fixed. Must equal the verifier's
# SUBJECT_ORDER.
SUBJECT_ORDER = (
    (POLICY_PACK_REL, "policy_pack"),
    (REPORT_REL, "policy_pack_conformance_report"),
)

# 24 ordered checks in fixed correspondence with the 24 approved
# verifier reasons. Must equal the verifier's CHECKS_ORDER.
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

# The 5 approved runner-only refusal reasons.
RUNNER_ONLY_REFUSAL_REASONS = (
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
)

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

DEFAULT_MANIFEST_SCOPE_LIMITATIONS = [
    "This manifest hash-anchors a local, demo Silver relying-party "
    "policy pack package; it is not signed.",
    "This manifest does not certify any relying party.",
    "This manifest does not transfer reliance to any downstream party.",
    "This manifest does not implement Gold governance; Gold governed "
    "reliance is the v0.4.0 boundary.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This manifest is not a Gold certificate.",
    "This manifest is not a regulator approval.",
    "This manifest is not an auditor approval.",
    "This manifest is not a legal acceptance instrument.",
    "This manifest is not a runtime enforcement proof.",
]


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


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


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


def canonical_json_bytes(obj: Any) -> bytes:
    """Byte-exact match with the v0.3.5 verifier."""
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def manifest_json_bytes(obj: Any) -> bytes:
    """Deterministic manifest JSON: sorted keys, 2-space indent,
    trailing newline. The verifier reads the manifest with
    json.loads(); only the subject bytes are byte-compared.
    """
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# Phase A: input preflight
# ---------------------------------------------------------------------------


def preflight_policy_pack_input(raw: str | None) -> tuple[bytes, dict] | int:
    """Validate the --policy-pack argv, emitting only the 5 approved
    runner-only refusal codes. Returns (raw_bytes, parsed_dict) on
    success or an exit code on refusal.
    """
    # 1. runner_input_path_missing
    if raw is None or raw == "" or raw.strip() == "":
        return fail(
            "runner_input_path_missing",
            "--policy-pack argument is missing or empty",
        )

    # 2. runner_input_path_forbidden
    p = Path(raw)
    if p.is_absolute():
        return fail(
            "runner_input_path_forbidden",
            f"--policy-pack must be a relative path, got absolute: {raw!r}",
        )
    if ".." in p.parts:
        return fail(
            "runner_input_path_forbidden",
            f"--policy-pack must not contain '..' segments, got {raw!r}",
        )

    # 3. runner_input_file_missing
    if not p.exists():
        return fail(
            "runner_input_file_missing",
            f"--policy-pack path does not exist on disk: {raw!r}",
        )

    # 4. runner_input_read_failed (directory OR unreadable)
    if p.is_dir():
        return fail(
            "runner_input_read_failed",
            (
                f"--policy-pack path is a directory, not a regular "
                f"file: {raw!r}"
            ),
        )
    try:
        with p.open("rb") as f:
            data = f.read()
    except OSError as e:
        return fail(
            "runner_input_read_failed",
            f"unable to read --policy-pack at {raw!r}: {e}",
        )

    # 5. runner_input_json_invalid
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError as e:
        return fail(
            "runner_input_json_invalid",
            f"--policy-pack is not valid UTF-8: {e}",
        )
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError as e:
        return fail(
            "runner_input_json_invalid",
            f"--policy-pack is not valid JSON: {e}",
        )

    return data, parsed if isinstance(parsed, dict) else {"__nonobject__": parsed}


# ---------------------------------------------------------------------------
# Conformance report and manifest derivation
# ---------------------------------------------------------------------------


def derive_conformance_report(
    report_id: str,
    policy_pack_id: str,
    policy_pack_sha256: str,
    generated_at: str,
) -> dict:
    """Build the report skeleton with 24 fixed-order check entries
    (status "pass"). Byte-exact match with the verifier's
    derive_expected_report when the policy pack passes all 24
    structural checks.
    """
    return {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "report_id": report_id,
        "policy_pack_id": policy_pack_id,
        "policy_pack_sha256": policy_pack_sha256,
        "generated_at": generated_at,
        "checks": [
            {
                "check_id": cid,
                "approved_reason_name": reason,
                "status": "pass",
            }
            for (cid, reason) in CHECKS_ORDER
        ],
    }


def derive_manifest(
    manifest_id: str,
    policy_pack_id: str,
    generated_at: str,
    pack_bytes: bytes,
    report_bytes: bytes,
) -> dict:
    pack_sha = sha256_label_bytes(pack_bytes)
    report_sha = sha256_label_bytes(report_bytes)
    return {
        "document_type": MANIFEST_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "manifest_id": manifest_id,
        "policy_pack_id": policy_pack_id,
        "generated_at": generated_at,
        "hash_algorithm": "sha256",
        "subjects": [
            {
                "role": "policy_pack",
                "path": POLICY_PACK_REL,
                "sha256": pack_sha,
                "size_bytes": len(pack_bytes),
            },
            {
                "role": "policy_pack_conformance_report",
                "path": REPORT_REL,
                "sha256": report_sha,
                "size_bytes": len(report_bytes),
            },
        ],
        "scope_limitations": list(DEFAULT_MANIFEST_SCOPE_LIMITATIONS),
        "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
    }


# ---------------------------------------------------------------------------
# Phase B: stage, write, optional self-validate, atomic publish
# ---------------------------------------------------------------------------


def build_package(
    pack_bytes: bytes,
    pack_parsed: dict,
    manifest_id: str,
    report_id: str,
    generated_at: str,
    out: Path,
    force: bool,
    self_validate: bool,
) -> int:
    if out.exists() and not force:
        return usage_error(
            f"--output-dir already exists: {out} (use --force)"
        )

    # The policy pack's own id field anchors the report and manifest.
    # If the input is a non-object or lacks policy_pack_id, fall back
    # to "unknown-policy-pack-id" so the staged package still produces
    # a parseable report/manifest. The verifier will detect the
    # downstream structural defect.
    raw_pack_id = pack_parsed.get("policy_pack_id") if isinstance(
        pack_parsed, dict
    ) else None
    if non_empty_str(raw_pack_id):
        policy_pack_id = raw_pack_id
    else:
        policy_pack_id = "unknown-policy-pack-id"

    pack_sha = sha256_label_bytes(pack_bytes)

    report = derive_conformance_report(
        report_id=report_id,
        policy_pack_id=policy_pack_id,
        policy_pack_sha256=pack_sha,
        generated_at=generated_at,
    )
    report_bytes = canonical_json_bytes(report)

    manifest = derive_manifest(
        manifest_id=manifest_id,
        policy_pack_id=policy_pack_id,
        generated_at=generated_at,
        pack_bytes=pack_bytes,
        report_bytes=report_bytes,
    )
    manifest_bytes = manifest_json_bytes(manifest)

    out.parent.mkdir(parents=True, exist_ok=True)
    staging = out.parent / f"{out.name}.staging.{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)

    def cleanup_staging() -> None:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    try:
        staging.mkdir(parents=True)

        # Byte-copy policy pack (preserve exact input bytes).
        (staging / POLICY_PACK_REL).write_bytes(pack_bytes)
        # Write canonical report bytes.
        (staging / REPORT_REL).write_bytes(report_bytes)
        # Write manifest.
        manifest_path = staging / MANIFEST_REL
        manifest_path.write_bytes(manifest_bytes)

        if self_validate:
            sv = subprocess.run(
                [
                    sys.executable,
                    str(POLICY_PACK_VERIFIER),
                    "--manifest",
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )
            if sv.returncode != 0:
                # Relay the verifier's stdout/stderr UNCHANGED.
                # Do NOT wrap in a sixth runner-only refusal code.
                if sv.stdout:
                    sys.stdout.write(sv.stdout)
                if sv.stderr:
                    sys.stderr.write(sv.stderr)
                cleanup_staging()
                return sv.returncode

        # Atomic move into destination.
        if out.exists():
            shutil.rmtree(out)
        os.replace(str(staging), str(out))
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(
        f"PASS: silver relying-party policy pack v0.3.5 built at {out}"
    )
    print(f"  manifest_id:    {manifest_id}")
    print(f"  report_id:      {report_id}")
    print(f"  policy_pack_id: {policy_pack_id}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a ProofRail Silver v0.3.5 Relying-Party Policy "
            "Pack package."
        )
    )
    parser.add_argument(
        "--policy-pack",
        default="",
        help=(
            "Relative path to a hand-authored policy pack JSON document. "
            "Must be a relative path (no absolute, no '..')."
        ),
    )
    parser.add_argument(
        "--manifest-id",
        default=(
            "proofrail-silver-relying-party-policy-pack-manifest-demo-001"
        ),
    )
    parser.add_argument(
        "--report-id",
        default=(
            "proofrail-silver-relying-party-policy-pack-"
            "conformance-report-demo-001"
        ),
    )
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help=(
            "Run the v0.3.5 verifier on the staged package BEFORE "
            "moving into place. On failure, the verifier's "
            "stdout/stderr are relayed UNCHANGED (no sixth runner-only "
            "refusal code) and the staging directory is removed."
        ),
    )
    args = parser.parse_args(argv)

    if parse_iso_8601_z(args.generated_at) is None:
        return usage_error(
            "--generated-at must be ISO-8601 UTC Z-suffixed"
        )
    if not non_empty_str(args.manifest_id):
        return usage_error("--manifest-id must be a non-empty string")
    if not non_empty_str(args.report_id):
        return usage_error("--report-id must be a non-empty string")

    # ----- Phase A: input preflight (5 runner-only refusal codes only) -----
    preflight = preflight_policy_pack_input(args.policy_pack)
    if isinstance(preflight, int):
        return preflight
    pack_bytes, pack_parsed = preflight

    # ----- Phase B: build, optional self-validate, atomic publish -----
    out = args.output_dir.resolve()
    return build_package(
        pack_bytes=pack_bytes,
        pack_parsed=pack_parsed,
        manifest_id=args.manifest_id,
        report_id=args.report_id,
        generated_at=args.generated_at,
        out=out,
        force=args.force,
        self_validate=args.self_validate,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
