#!/usr/bin/env python3
"""Build a ProofRail Silver v0.3.6 Control Crosswalk + Protected Action Catalog package.

The runner composes a deterministic, hash-anchored local Silver package
that binds a hand-authored control pack JSON document to a re-derived
conformance report and a two-subject manifest.

Behavior:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-pack:
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
      c. Byte-copies the input control pack JSON to
             <staging>/control-pack.json
         The byte image is preserved exactly; structural defects in
         the input pack remain in the staged copy.
      d. Builds the conformance report using BYTE-IDENTICAL canonical
         JSON serialization (sort_keys=True, separators=(",", ":"),
         trailing newline) so a passing pack's report will match the
         verifier's re-derivation byte-for-byte.
      e. Builds the two-subject manifest in fixed subject order:
             [0] control-pack.json
             [1] silver-control-crosswalk-protected-action-catalog-
                  conformance-report.json
         with sha256 and size recomputed from the staged copies.
      f. When --self-validate is supplied, subprocess-invokes the v0.3.6
         verifier on the staged manifest BEFORE the atomic move. On a
         non-zero exit, the verifier's stdout/stderr are RELAYED
         UNCHANGED and the staging directory is removed; the
         destination is left untouched.
      g. On success the staging directory is atomically replaced into
         --output-dir via os.replace().

No external services. No signing. No certification. No Gold
governance. No trust transfer.
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
# Runner-only refusal reason vocabulary. Identical to the v0.3.5 runner.
# A sixth runner-only refusal code is intentionally NOT introduced for
# verifier-relayed failures.
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


def _preflight_input_path(input_pack: str | None) -> Path:
    if input_pack is None or input_pack == "":
        _refuse(REFUSAL_PATH_MISSING, "--input-pack is required and must be non-empty")
    p = input_pack  # type: ignore[assignment]
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
# control pack. The runner attempts derivation against an unverified pack
# only to the extent of producing a stable skeleton; structural defects in
# the pack are detected by the verifier and not by this runner.
# ---------------------------------------------------------------------------

# The 24 approved verifier reasons, in fixed order, recorded in the
# conformance report as structural-check identifiers. These ride alongside
# the human-readable summary so the verifier can cross-check independent
# re-derivation. The runner never EMITS these reasons; only the verifier
# does. They appear here as DATA only.
APPROVED_VERIFIER_REASONS_ORDERED = (
    "control_pack_manifest_invalid",
    "control_pack_not_object",
    "control_pack_schema_invalid",
    "control_pack_profile_unsupported",
    "control_pack_identity_invalid",
    "protected_action_catalog_invalid",
    "protected_action_entry_invalid",
    "protected_action_identifier_invalid",
    "protected_action_scope_invalid",
    "protected_action_authority_invalid",
    "protected_action_risk_boundary_invalid",
    "control_crosswalk_invalid",
    "crosswalk_entry_invalid",
    "catalog_crosswalk_consistency_invalid",
    "proofrail_artifact_reference_invalid",
    "evidence_relationship_invalid",
    "control_concept_reference_invalid",
    "control_objective_invalid",
    "control_claim_invalid",
    "control_limitation_invalid",
    "dependency_reference_invalid",
    "version_binding_invalid",
    "non_claims_missing",
    "prohibited_compliance_claim_present",
)


def _derive_conformance_report(
    *,
    report_id: str,
    generated_at: str,
    pack_obj: Any,
    pack_sha256: str,
) -> dict[str, Any]:
    """Derive a deterministic conformance report from a control pack.

    Field values are computed structurally. The report does not assert
    that the pack is valid; the verifier independently re-derives this
    report from the pack subject and compares byte-for-byte.
    """
    pack = pack_obj if isinstance(pack_obj, dict) else {}

    # Catalog summary
    catalog = pack.get("protected_action_catalog")
    if not isinstance(catalog, list):
        catalog = []
    action_ids: list[str] = []
    for entry in catalog:
        if isinstance(entry, dict):
            aid = entry.get("action_id")
            if isinstance(aid, str):
                action_ids.append(aid)
    protected_action_count = len(catalog)
    protected_action_ids = sorted(set(action_ids))

    # Crosswalk summary
    crosswalk = pack.get("control_crosswalk")
    if not isinstance(crosswalk, list):
        crosswalk = []
    mapping_ids: list[str] = []
    referenced_artifact_types: list[str] = []
    referenced_control_concept_ids: list[str] = []
    for entry in crosswalk:
        if isinstance(entry, dict):
            m = entry.get("mapping_id")
            if isinstance(m, str):
                mapping_ids.append(m)
            at = entry.get("artifact_type")
            if isinstance(at, str):
                referenced_artifact_types.append(at)
            cc = entry.get("control_concept_id")
            if isinstance(cc, str):
                referenced_control_concept_ids.append(cc)
    crosswalk_entry_count = len(crosswalk)

    # Limitations / dependencies / version bindings / non_claims counts
    limitations = pack.get("control_limitations")
    control_limitation_count = len(limitations) if isinstance(limitations, list) else 0
    deps = pack.get("dependency_references")
    dependency_reference_count = len(deps) if isinstance(deps, list) else 0
    vbs = pack.get("version_bindings")
    version_binding_count = len(vbs) if isinstance(vbs, list) else 0
    ncs = pack.get("non_claims")
    non_claim_count = len(ncs) if isinstance(ncs, list) else 0

    profile = pack.get("profile")
    if not isinstance(profile, str):
        profile = ""
    control_pack_id = pack.get("control_pack_id")
    if not isinstance(control_pack_id, str):
        control_pack_id = ""

    report = {
        "document_type": "proofrail.silver.control_crosswalk_protected_action_catalog_conformance_report",
        "schema_version": "v0.1.0",
        "report_id": report_id,
        "generated_at": generated_at,
        "control_pack_binding": {
            "control_pack_id": control_pack_id,
            "control_pack_sha256": pack_sha256,
            "profile": profile,
        },
        "summary": {
            "protected_action_count": protected_action_count,
            "protected_action_ids": protected_action_ids,
            "crosswalk_entry_count": crosswalk_entry_count,
            "crosswalk_mapping_ids": sorted(set(mapping_ids)),
            "referenced_artifact_types": sorted(set(referenced_artifact_types)),
            "referenced_control_concept_ids": sorted(set(referenced_control_concept_ids)),
            "control_limitation_count": control_limitation_count,
            "dependency_reference_count": dependency_reference_count,
            "version_binding_count": version_binding_count,
            "non_claim_count": non_claim_count,
        },
        "structural_check_ids": list(APPROVED_VERIFIER_REASONS_ORDERED),
        "non_claims": [
            "This conformance report is a deterministic restatement of structural facts.",
            "It is not a compliance attestation, certification, audit decision, regulator decision, authorization, or governed reliance decision.",
        ],
    }
    return report


# ---------------------------------------------------------------------------
# Phase B: package build.
# ---------------------------------------------------------------------------

def _build_manifest(
    *,
    manifest_id: str,
    control_pack_id: str,
    generated_at: str,
    pack_path: Path,
    report_path: Path,
    pack_sha256_label: str,
    report_sha256_label: str,
) -> dict[str, Any]:
    pack_size = pack_path.stat().st_size
    report_size = report_path.stat().st_size
    manifest = {
        "document_type": "proofrail.silver.control_crosswalk_protected_action_catalog_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "silver.control_crosswalk.v0.3.6",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "control_pack_id": control_pack_id,
        "generated_at": generated_at,
        "package": {
            "package_family": "silver_control_crosswalk_protected_action_catalog",
            "release_line": "silver.control_crosswalk.v0.3.6",
            "package_root_layout": "control-pack.json + silver-control-crosswalk-protected-action-catalog-conformance-report.json + silver-control-crosswalk-protected-action-catalog-manifest.json",
        },
        "subjects": [
            {
                "role": "control_pack",
                "path": "control-pack.json",
                "sha256": pack_sha256_label,
                "size_bytes": pack_size,
            },
            {
                "role": "conformance_report",
                "path": "silver-control-crosswalk-protected-action-catalog-conformance-report.json",
                "sha256": report_sha256_label,
                "size_bytes": report_size,
            },
        ],
    }
    return manifest


def _atomic_publish(staging: Path, dest: Path) -> None:
    # os.replace is atomic on POSIX when src and dest are on the same
    # filesystem. We staged under a sibling directory of the destination
    # so this holds for the typical /tmp deployment in this repo.
    os.replace(staging, dest)


def _remove_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.3.6 verifier. Relay unchanged on failure."""
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
        description="Build a ProofRail Silver v0.3.6 Control Crosswalk + Protected Action Catalog package.",
    )
    parser.add_argument(
        "--input-pack",
        type=str,
        default=None,
        help="Path to the input control pack JSON.",
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
        help="Invoke the v0.3.6 verifier against the staging directory BEFORE the atomic move.",
    )
    args = parser.parse_args(argv)

    # Phase A: preflight only.
    input_pack_path = _preflight_input_path(args.input_pack)

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
        # Byte-copy the input pack.
        staged_pack = staging / "control-pack.json"
        pack_bytes = input_pack_path.read_bytes()
        staged_pack.write_bytes(pack_bytes)
        pack_sha256_hex = _sha256_hex(pack_bytes)
        pack_sha256_label = _sha256_label(pack_bytes)

        # Parse the pack for report derivation. The runner never enforces
        # structural rules against the pack here; the verifier does.
        try:
            pack_obj = json.loads(pack_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pack_obj = None

        # Derive the conformance report (canonical JSON bytes).
        report_obj = _derive_conformance_report(
            report_id=args.report_id,
            generated_at=args.generated_at,
            pack_obj=pack_obj,
            pack_sha256=pack_sha256_hex,
        )
        report_bytes = _canonical_json_bytes(report_obj)
        staged_report = (
            staging
            / "silver-control-crosswalk-protected-action-catalog-conformance-report.json"
        )
        staged_report.write_bytes(report_bytes)
        report_sha256_label = _sha256_label(report_bytes)

        # Derive control_pack_id for the manifest. The verifier independently
        # cross-checks this against the pack's control_pack_id field. We
        # tolerate a missing or non-string id here; the verifier surfaces
        # that as a structural defect on the pack itself.
        if isinstance(pack_obj, dict) and isinstance(pack_obj.get("control_pack_id"), str):
            control_pack_id = pack_obj["control_pack_id"]
        else:
            control_pack_id = "proofrail-silver-control-crosswalk-protected-action-catalog-unknown"

        # Build the manifest after the two subjects are written.
        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            control_pack_id=control_pack_id,
            generated_at=args.generated_at,
            pack_path=staged_pack,
            report_path=staged_report,
            pack_sha256_label=pack_sha256_label,
            report_sha256_label=report_sha256_label,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = (
            staging / "silver-control-crosswalk-protected-action-catalog-manifest.json"
        )
        staged_manifest.write_bytes(manifest_bytes)

        # Optional self-validation against the staging directory BEFORE the
        # atomic move.
        if args.self_validate:
            verifier_path = (
                Path(__file__).resolve().parent
                / "verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py"
            )
            rc = _self_validate(verifier_path, staged_manifest)
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
