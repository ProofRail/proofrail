#!/usr/bin/env python3
"""Build a ProofRail Minimal Gold v0.4.0 Governed Reliance Demo package.

The runner composes a deterministic, hash-anchored local Minimal Gold
package that records governed reliance decisions composed from
Silver-shaped inputs. It binds a hand-authored governed-reliance
package body JSON document to a re-derived 24-entry conformance report
and a two-subject manifest.

Behavior:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package:
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
      c. Byte-copies the input package body JSON to
             <staging>/governed-reliance-scenarios.json
         The byte image is preserved exactly; structural defects in
         the input package remain in the staged copy.
      d. Builds the conformance report using BYTE-IDENTICAL canonical
         JSON serialization (sort_keys=True, separators=(",", ":"),
         trailing newline) so a passing package's report will match
         the verifier's re-derivation byte-for-byte.
      e. Builds the two-subject manifest in fixed subject order:
             [0] governed-reliance-scenarios.json
             [1] silver-gold-governed-reliance-conformance-report.json
         with sha256 and size recomputed from the staged copies.
      f. When --self-validate is supplied, subprocess-invokes the v0.4.0
         verifier on the staged manifest BEFORE the atomic move. On a
         non-zero exit, the verifier's stdout/stderr are RELAYED
         UNCHANGED and the staging directory is removed; the
         destination is left untouched.
      g. On success the staging directory is atomically replaced into
         --output-dir via os.replace().

A v0.4.0 package is a deterministic local hand-authored record of
governed reliance decisions composed from Silver-shaped inputs. It is
NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold.
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
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Runner-only refusal reason vocabulary. Identical naming to the v0.3.5 /
# v0.3.6 / v0.3.7 runner. A sixth runner-only refusal code is intentionally
# NOT introduced for verifier-relayed failures.
# ---------------------------------------------------------------------------

REFUSAL_PATH_MISSING = "runner_input_path_missing"
REFUSAL_PATH_FORBIDDEN = "runner_input_path_forbidden"
REFUSAL_FILE_MISSING = "runner_input_file_missing"
REFUSAL_READ_FAILED = "runner_input_read_failed"
REFUSAL_JSON_INVALID = "runner_input_json_invalid"


def _refuse(reason: str, detail: str) -> None:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Canonical JSON serialization. Byte-identical between runner and verifier
# so that conformance-report bytes survive cross-tool re-derivation.
# ---------------------------------------------------------------------------

def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_label(data: bytes) -> str:
    return "sha256:" + _sha256_hex(data)


# ---------------------------------------------------------------------------
# Phase A: preflight only. Closed set of 5 runner-only refusal reasons.
# ---------------------------------------------------------------------------

_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


def _preflight_input_path(input_package: str | None) -> Path:
    if input_package is None or input_package == "":
        _refuse(REFUSAL_PATH_MISSING, "--input-package is required and must be non-empty")
    p = input_package  # type: ignore[assignment]
    if os.path.isabs(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"absolute path is not permitted: {p!r}")
    if _has_traversal(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"path traversal is not permitted: {p!r}")
    pp = Path(p)
    if not pp.exists():
        _refuse(REFUSAL_FILE_MISSING, f"input path does not exist: {p!r}")
    # A directory at the input path is treated as a read failure rather than
    # an OS-level chmod, so the test suite does not need chmod 000.
    if pp.is_dir():
        _refuse(REFUSAL_READ_FAILED, f"input path is a directory, not a file: {p!r}")
    try:
        raw = pp.read_bytes()
    except OSError as e:
        _refuse(REFUSAL_READ_FAILED, f"cannot read input file: {p!r}: {e}")
    try:
        json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        _refuse(REFUSAL_JSON_INVALID, f"input is not valid JSON: {p!r}: {e}")
    return pp


# ---------------------------------------------------------------------------
# Conformance-report derivation. Pure structural restatement of the verified
# package body. The runner attempts derivation against an unverified package
# only to the extent of producing a stable skeleton; structural defects in
# the package are detected by the verifier and not by this runner.
# ---------------------------------------------------------------------------

# The 24 approved verifier reasons, in fixed order, recorded in the
# conformance report as structural-check identifiers. These ride alongside
# the human-readable summary so the verifier can cross-check independent
# re-derivation. The runner never EMITS these reasons; only the verifier
# does. They appear here as DATA only.
APPROVED_VERIFIER_REASONS_ORDERED = (
    "gold_manifest_invalid",                          # 01
    "gold_package_not_object",                        # 02
    "gold_package_schema_invalid",                    # 03
    "gold_profile_unsupported",                       # 04
    "gold_package_identity_invalid",                  # 05
    "silver_verification_input_invalid",              # 06
    "silver_handoff_input_invalid",                   # 07
    "policy_pack_input_invalid",                      # 08
    "registry_lite_input_invalid",                    # 09
    "control_crosswalk_input_invalid",                # 10
    "governed_decision_set_invalid",                  # 11
    "governed_decision_entry_invalid",                # 12
    "decision_subject_binding_invalid",               # 13
    "decision_policy_binding_invalid",                # 14
    "decision_registry_binding_invalid",              # 15
    "decision_action_scope_invalid",                  # 16
    "decision_status_invalid",                        # 17
    "acceptance_path_invalid",                        # 18
    "rejection_path_invalid",                         # 19
    "challenge_path_invalid",                         # 20
    "withdrawal_path_invalid",                        # 21
    "supersession_path_invalid",                      # 22
    "non_claims_missing",                             # 23
    "prohibited_gold_claim_present",                  # 24
)

# Static check_name descriptions used in the conformance report. These are
# fixed across all v0.4.0 packages so the report byte image depends only
# on package_id, governed_reliance_demo_id, report_id, generated_at, and
# the constant 24-entry schedule (per the conformance report schema).
_CHECK_DETAILS = {
    "gold_manifest_invalid": "Manifest shape, two-subject layout, paths, and cross-anchors pass.",
    "gold_package_not_object": "Package body parses to a JSON object.",
    "gold_package_schema_invalid": "Package body declares document_type proofrail.gold.governed_reliance_package and schema_version v0.1.0.",
    "gold_profile_unsupported": "Package profile is the closed v0.4.0 value gold.governed_reliance.v0.4.0.",
    "gold_package_identity_invalid": "package_id, governed_reliance_demo_id, and relying_party.identity_id satisfy the closed identifier grammar.",
    "silver_verification_input_invalid": "silver_verification input shape and expected_status pass.",
    "silver_handoff_input_invalid": "silver_handoff input shape and expected_handoff_posture pass.",
    "policy_pack_input_invalid": "policy_pack input shape, policy_pack_id, and policy_pack_version pass.",
    "registry_lite_input_invalid": "registry_lite input shape and registry_id pass.",
    "control_crosswalk_input_invalid": "control_crosswalk input shape and control_pack_id pass.",
    "governed_decision_set_invalid": "governed_decisions list holds 1..5 entries in natural order with unique scenario_type values.",
    "governed_decision_entry_invalid": "Each governed decision entry holds the required fields under the closed grammar.",
    "decision_subject_binding_invalid": "Each decision_subject block holds a closed subject_type and a subject_ref.",
    "decision_policy_binding_invalid": "Each policy_binding block holds policy_pack_id, policy_pack_version, policy_clause_refs, and a closed policy_decision.",
    "decision_registry_binding_invalid": "Each registry_binding block holds relying_party_id and a closed decision_authority_role.",
    "decision_action_scope_invalid": "Each action_scope block holds a closed protected_action_id, action_category, and action_environment.",
    "decision_status_invalid": "Each decision_status value is in the closed status set and matches its scenario_type.",
    "acceptance_path_invalid": "The clean_acceptance entry's scenario_specific_state holds a non-empty acceptance_record_ref.",
    "rejection_path_invalid": "The policy_rejection entry's scenario_specific_state holds a closed rejection_reason and silver_verification_passing true.",
    "challenge_path_invalid": "The challenge_filed entry's scenario_specific_state holds a non-empty challenge_record_ref and a closed challenge_state.",
    "withdrawal_path_invalid": "The withdrawal entry's scenario_specific_state holds a non-empty withdrawal_record_ref and a closed withdrawal_trigger.",
    "supersession_path_invalid": "The supersession entry's scenario_specific_state holds a closed prior_decision_ref_kind, a resolvable prior_decision_id (when internal), a closed supersession_trigger, and a non-empty superseding_input_ref.",
    "non_claims_missing": "non_claims is present and non-empty.",
    "prohibited_gold_claim_present": "No prohibited Gold-claim token appears outside scope_limitations or non_claims.",
}


def _derive_conformance_report(
    *,
    package_id: str,
    governed_reliance_demo_id: str,
    report_id: str,
    generated_at: str,
) -> dict[str, Any]:
    """Derive a deterministic conformance report from package identity.

    The conformance report's byte image depends only on:
      - the package body's package_id
      - the package body's governed_reliance_demo_id
      - the manifest's report_id
      - the manifest's generated_at
      - the fixed 24-entry schedule

    Field values are computed structurally. The report does not assert
    that the package is valid; the verifier independently re-derives this
    report from the package subject and compares byte-for-byte.
    """
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

    report = {
        "document_type": "proofrail.gold.governed_reliance_conformance_report",
        "schema_version": "v0.1.0",
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "entries": entries,
    }
    return report


# ---------------------------------------------------------------------------
# Phase B: package build.
# ---------------------------------------------------------------------------

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
REPORT_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
MANIFEST_FILENAME = "gold-governed-reliance-package-manifest.json"


def _build_manifest(
    *,
    manifest_id: str,
    report_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    package_path: Path,
    report_path: Path,
    package_sha256_label: str,
    report_sha256_label: str,
) -> dict[str, Any]:
    package_size = package_path.stat().st_size
    report_size = report_path.stat().st_size
    manifest = {
        "document_type": "proofrail.gold.governed_reliance_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.governed_reliance.v0.4.0",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "report_id": report_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "generated_at": generated_at,
        "subjects": [
            {
                "role": "governed_reliance_package",
                "path": PACKAGE_SUBJECT_PATH,
                "sha256": package_sha256_label,
                "size_bytes": package_size,
            },
            {
                "role": "conformance_report",
                "path": REPORT_SUBJECT_PATH,
                "sha256": report_sha256_label,
                "size_bytes": report_size,
            },
        ],
    }
    return manifest


def _atomic_publish(staging: Path, dest: Path) -> None:
    os.replace(staging, dest)


def _remove_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)


# Module constant exposing the verifier path for monkey-patch by tests.
GOLD_GOVERNED_RELIANCE_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_governed_reliance_demo_v0_1_0.py"
)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.4.0 verifier. Relay unchanged on failure."""
    result = subprocess.run(
        [sys.executable, str(verifier_path), "--manifest", str(manifest_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a ProofRail Minimal Gold v0.4.0 Governed Reliance Demo package.",
    )
    parser.add_argument(
        "--input-package",
        type=str,
        default=None,
        help="Path to the input governed-reliance package body JSON.",
    )
    parser.add_argument(
        "--manifest-id",
        type=str,
        required=True,
        help="Stable manifest_id for the produced manifest.",
    )
    parser.add_argument(
        "--report-id",
        type=str,
        required=True,
        help="Stable report_id for the derived conformance report.",
    )
    parser.add_argument(
        "--generated-at",
        type=str,
        required=True,
        help="ISO-8601 UTC timestamp ending in 'Z'.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Destination directory for the published package.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination directory if it exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Invoke the v0.4.0 verifier against the staging directory BEFORE the atomic move.",
    )
    args = parser.parse_args(argv)

    # Phase A: preflight only.
    input_package_path = _preflight_input_path(args.input_package)

    # Phase B begins.
    out_dir = Path(args.output_dir)
    if out_dir.exists() and not args.force:
        sys.stderr.write(
            f"refuse: output dir already exists; pass --force to overwrite: {out_dir}\n"
        )
        return 1
    if out_dir.exists() and args.force:
        shutil.rmtree(out_dir)

    staging = out_dir.with_suffix(out_dir.suffix + f".staging.{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=False)

    try:
        # Byte-copy the input package body.
        staged_package = staging / PACKAGE_SUBJECT_PATH
        package_bytes = input_package_path.read_bytes()
        staged_package.write_bytes(package_bytes)
        package_sha256_label = _sha256_label(package_bytes)

        # Parse the package for identity field extraction.
        try:
            package_obj = json.loads(package_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            package_obj = None

        if isinstance(package_obj, dict) and isinstance(package_obj.get("package_id"), str):
            package_id = package_obj["package_id"]
        else:
            package_id = "proofrail-gold-governed-reliance-unknown"
        if isinstance(package_obj, dict) and isinstance(
            package_obj.get("governed_reliance_demo_id"), str
        ):
            governed_reliance_demo_id = package_obj["governed_reliance_demo_id"]
        else:
            governed_reliance_demo_id = "gold-governed-reliance-unknown"

        # Derive the conformance report (canonical JSON bytes).
        report_obj = _derive_conformance_report(
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            report_id=args.report_id,
            generated_at=args.generated_at,
        )
        report_bytes = _canonical_json_bytes(report_obj)
        staged_report = staging / REPORT_SUBJECT_PATH
        staged_report.write_bytes(report_bytes)
        report_sha256_label = _sha256_label(report_bytes)

        # Build the manifest after the two subjects are written.
        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            report_id=args.report_id,
            package_id=package_id,
            governed_reliance_demo_id=governed_reliance_demo_id,
            generated_at=args.generated_at,
            package_path=staged_package,
            report_path=staged_report,
            package_sha256_label=package_sha256_label,
            report_sha256_label=report_sha256_label,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = staging / MANIFEST_FILENAME
        staged_manifest.write_bytes(manifest_bytes)

        # Optional self-validation against the staging directory BEFORE the
        # atomic move.
        if args.self_validate:
            rc = _self_validate(GOLD_GOVERNED_RELIANCE_VERIFIER, staged_manifest)
            if rc != 0:
                _remove_staging(staging)
                return rc

        _atomic_publish(staging, out_dir)
    except Exception:
        _remove_staging(staging)
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
