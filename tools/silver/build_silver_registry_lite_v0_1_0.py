#!/usr/bin/env python3
"""Build a ProofRail Silver v0.3.7 Registry Lite package.

The runner composes a deterministic, hash-anchored local Silver package
that binds a hand-authored registry-lite JSON document to a re-derived
conformance report and a two-subject manifest.

Behavior:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-registry:
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
      c. Byte-copies the input registry-lite JSON to
             <staging>/registry-lite.json
         The byte image is preserved exactly; structural defects in
         the input registry remain in the staged copy.
      d. Builds the conformance report using BYTE-IDENTICAL canonical
         JSON serialization (sort_keys=True, separators=(",", ":"),
         trailing newline) so a passing registry's report will match
         the verifier's re-derivation byte-for-byte.
      e. Builds the two-subject manifest in fixed subject order:
             [0] registry-lite.json
             [1] silver-registry-lite-conformance-report.json
         with sha256 and size recomputed from the staged copies.
      f. When --self-validate is supplied, subprocess-invokes the v0.3.7
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
# Runner-only refusal reason vocabulary. Identical to the v0.3.5 / v0.3.6
# runner. A sixth runner-only refusal code is intentionally NOT introduced
# for verifier-relayed failures.
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


def _preflight_input_path(input_registry: str | None) -> Path:
    if input_registry is None or input_registry == "":
        _refuse(REFUSAL_PATH_MISSING, "--input-registry is required and must be non-empty")
    p = input_registry  # type: ignore[assignment]
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
# registry-lite body. The runner attempts derivation against an unverified
# registry only to the extent of producing a stable skeleton; structural
# defects in the registry are detected by the verifier and not by this
# runner.
# ---------------------------------------------------------------------------

# The 24 approved verifier reasons, in fixed order, recorded in the
# conformance report as structural-check identifiers. These ride alongside
# the human-readable summary so the verifier can cross-check independent
# re-derivation. The runner never EMITS these reasons; only the verifier
# does. They appear here as DATA only.
APPROVED_VERIFIER_REASONS_ORDERED = (
    "registry_manifest_invalid",
    "registry_not_object",
    "registry_schema_invalid",
    "registry_profile_unsupported",
    "registry_identity_invalid",
    "registry_authority_invalid",
    "registry_entity_set_invalid",
    "registry_entity_entry_invalid",
    "registry_entity_identifier_invalid",
    "registry_role_invalid",
    "registry_status_invalid",
    "registry_effective_period_invalid",
    "registry_key_reference_invalid",
    "registry_key_binding_invalid",
    "issuer_entry_invalid",
    "verifier_entry_invalid",
    "relying_party_entry_invalid",
    "policy_authority_entry_invalid",
    "revocation_source_entry_invalid",
    "protected_action_authority_entry_invalid",
    "trust_relationship_invalid",
    "version_binding_invalid",
    "non_claims_missing",
    "prohibited_registry_claim_present",
)


def _derive_conformance_report(
    *,
    report_id: str,
    generated_at: str,
    registry_obj: Any,
    registry_sha256: str,
) -> dict[str, Any]:
    """Derive a deterministic conformance report from a registry-lite body.

    Field values are computed structurally. The report does not assert
    that the registry is valid; the verifier independently re-derives this
    report from the registry subject and compares byte-for-byte.
    """
    registry = registry_obj if isinstance(registry_obj, dict) else {}

    # Entity summary
    entities = registry.get("entities")
    if not isinstance(entities, list):
        entities = []
    entity_count = len(entities)
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
    entity_id_set = sorted(set(entity_ids))
    role_set = sorted(set(entity_roles))

    # Trust relationship summary
    trels = registry.get("trust_relationships")
    if not isinstance(trels, list):
        trels = []
    trust_relationship_count = len(trels)
    relationship_verbs: list[str] = []
    for entry in trels:
        if isinstance(entry, dict):
            v = entry.get("relationship_verb")
            if isinstance(v, str):
                relationship_verbs.append(v)
    relationship_verb_set = sorted(set(relationship_verbs))

    # Version binding summary
    vbs = registry.get("version_bindings")
    if not isinstance(vbs, list):
        vbs = []
    version_binding_count = len(vbs)
    upstream_ids: list[str] = []
    for entry in vbs:
        if isinstance(entry, dict):
            u = entry.get("upstream_id")
            if isinstance(u, str):
                upstream_ids.append(u)
    upstream_id_set = sorted(set(upstream_ids))

    # Scope limitation and non-claim counts
    sls = registry.get("scope_limitations")
    scope_limitation_count = len(sls) if isinstance(sls, list) else 0
    ncs = registry.get("non_claims")
    non_claim_count = len(ncs) if isinstance(ncs, list) else 0

    profile = registry.get("profile")
    if not isinstance(profile, str):
        profile = ""
    registry_id = registry.get("registry_id")
    if not isinstance(registry_id, str):
        registry_id = ""

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
        "document_type": "proofrail.silver.registry_lite_conformance_report",
        "schema_version": "v0.1.0",
        "proofrail_release": "silver.registry_lite.v0.3.7",
        "report_id": report_id,
        "registry_id": registry_id,
        "generated_at": generated_at,
        "registry_binding": {
            "registry_id": registry_id,
            "registry_sha256": registry_sha256,
            "profile": profile,
        },
        "summary_counts": {
            "entity_count": entity_count,
            "entity_id_set": entity_id_set,
            "entity_role_set": role_set,
            "trust_relationship_count": trust_relationship_count,
            "trust_relationship_verb_set": relationship_verb_set,
            "version_binding_count": version_binding_count,
            "version_binding_upstream_id_set": upstream_id_set,
            "scope_limitation_count": scope_limitation_count,
            "non_claim_count": non_claim_count,
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
# Phase B: package build.
# ---------------------------------------------------------------------------

def _build_manifest(
    *,
    manifest_id: str,
    report_id: str,
    registry_id: str,
    generated_at: str,
    registry_path: Path,
    report_path: Path,
    registry_sha256_label: str,
    report_sha256_label: str,
) -> dict[str, Any]:
    registry_size = registry_path.stat().st_size
    report_size = report_path.stat().st_size
    manifest = {
        "document_type": "proofrail.silver.registry_lite_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "silver.registry_lite.v0.3.7",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "report_id": report_id,
        "registry_id": registry_id,
        "generated_at": generated_at,
        "package": {
            "package_family": "silver_registry_lite",
            "release_line": "silver.registry_lite.v0.3.7",
            "package_root_layout": "registry-lite.json + silver-registry-lite-conformance-report.json + silver-registry-lite-manifest.json",
        },
        "subjects": [
            {
                "role": "registry_lite",
                "path": "registry-lite.json",
                "sha256": registry_sha256_label,
                "size_bytes": registry_size,
            },
            {
                "role": "conformance_report",
                "path": "silver-registry-lite-conformance-report.json",
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


# Module constant exposing the verifier path for monkey-patch by tests.
REGISTRY_LITE_VERIFIER = (
    Path(__file__).resolve().parent / "verify_silver_registry_lite_v0_1_0.py"
)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.3.7 verifier. Relay unchanged on failure."""
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
        description="Build a ProofRail Silver v0.3.7 Registry Lite package.",
    )
    parser.add_argument(
        "--input-registry",
        type=str,
        default=None,
        help="Path to the input registry-lite JSON.",
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
        help="Invoke the v0.3.7 verifier against the staging directory BEFORE the atomic move.",
    )
    args = parser.parse_args(argv)

    # Phase A: preflight only.
    input_registry_path = _preflight_input_path(args.input_registry)

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
        # Byte-copy the input registry.
        staged_registry = staging / "registry-lite.json"
        registry_bytes = input_registry_path.read_bytes()
        staged_registry.write_bytes(registry_bytes)
        registry_sha256_hex = _sha256_hex(registry_bytes)
        registry_sha256_label = _sha256_label(registry_bytes)

        # Parse the registry for report derivation. The runner never enforces
        # structural rules against the registry here; the verifier does.
        try:
            registry_obj = json.loads(registry_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            registry_obj = None

        # Derive the conformance report (canonical JSON bytes).
        report_obj = _derive_conformance_report(
            report_id=args.report_id,
            generated_at=args.generated_at,
            registry_obj=registry_obj,
            registry_sha256=registry_sha256_hex,
        )
        report_bytes = _canonical_json_bytes(report_obj)
        staged_report = staging / "silver-registry-lite-conformance-report.json"
        staged_report.write_bytes(report_bytes)
        report_sha256_label = _sha256_label(report_bytes)

        # Derive registry_id for the manifest. The verifier independently
        # cross-checks this against the registry's registry_id field. We
        # tolerate a missing or non-string id here; the verifier surfaces
        # that as a structural defect on the registry itself.
        if isinstance(registry_obj, dict) and isinstance(registry_obj.get("registry_id"), str):
            registry_id = registry_obj["registry_id"]
        else:
            registry_id = "proofrail-silver-registry-lite-unknown"

        # Build the manifest after the two subjects are written.
        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            report_id=args.report_id,
            registry_id=registry_id,
            generated_at=args.generated_at,
            registry_path=staged_registry,
            report_path=staged_report,
            registry_sha256_label=registry_sha256_label,
            report_sha256_label=report_sha256_label,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = staging / "silver-registry-lite-manifest.json"
        staged_manifest.write_bytes(manifest_bytes)

        # Optional self-validation against the staging directory BEFORE the
        # atomic move.
        if args.self_validate:
            rc = _self_validate(REGISTRY_LITE_VERIFIER, staged_manifest)
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
