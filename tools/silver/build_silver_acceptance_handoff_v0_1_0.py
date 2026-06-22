#!/usr/bin/env python3
"""Build a ProofRail Silver v0.3.0 acceptance handoff package.

The runner composes a portable handoff package that binds three
upstream Silver pipelines:

  - v0.2.7 composed gateway evidence manifest
  - v0.2.8 relying-party acceptance package manifest
  - v0.2.9 revocation/challenge drill package manifest

Behavior:

  1. Parses CLI; validates --generated-at as ISO-8601 UTC Z-suffixed.
  2. Refuses to overwrite --output-dir unless --force is supplied.
  3. Subprocess-invokes the v0.2.7 verifier on
     --composed-evidence-manifest. On non-zero exit prints
         FAIL: composed_evidence_validation_failed: <detail>
     and exits 1.
  4. Subprocess-invokes the v0.2.8 acceptance validator on
     --acceptance-manifest (without --evidence-package-root). On
     non-zero exit prints
         FAIL: acceptance_package_validation_failed: <detail>
     and exits 1.
  5. Subprocess-invokes the v0.2.9 drill verifier on --drill-manifest
     (without --evidence-package-root). On non-zero exit prints
         FAIL: drill_package_validation_failed: <detail>
     and exits 1.
  6. Stages output in a sibling directory next to --output-dir.
  7. Byte-copies the v0.2.7 package root into
         <staging>/composed-gateway-evidence/
     the v0.2.8 package root into
         <staging>/acceptance-package/
     and the v0.2.9 package root into
         <staging>/revocation-challenge-drill/
  8. Parses the nested v0.2.8 acceptance record and v0.2.9 drill
     report. Performs the four chain-binding cross-checks. On any
     mismatch prints
         FAIL: handoff_chain_binding_failed: <detail>
     removes the staging directory, and exits 1.
  9. Maps the nested v0.2.9 recommended_local_posture onto a
     recommended_handoff_posture using the closed posture set
     and ordered severity ranks.
 10. Writes silver-acceptance-handoff-summary.json with deterministic
     field shape.
 11. Writes silver-acceptance-handoff-manifest.json with four subjects
     in the deterministic order required by the v0.3.0 schema.
 12. When --self-validate is supplied, subprocess-invokes the v0.3.0
     handoff verifier on the staged manifest BEFORE moving into place.
     On non-zero exit prints
         FAIL: self_validation_failed: <detail>
     removes the staging directory (leaving the destination untouched),
     and exits 1.
 13. Atomically moves the staging directory to --output-dir.

No external services, no real handoff transfer, no signing.

Usage:
  python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py \\
    --composed-evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \\
    --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \\
    --drill-manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \\
    --generated-at 2026-06-28T00:00:00Z \\
    --output-dir /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \\
    --force \\
    [--self-validate]

Exit codes:
  0 - handoff package generated
  1 - build refused (composed_evidence_validation_failed,
      acceptance_package_validation_failed,
      drill_package_validation_failed,
      handoff_chain_binding_failed, or self_validation_failed)
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
COMPOSED_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"
)
ACCEPTANCE_VALIDATOR = (
    REPO_ROOT / "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
)
DRILL_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_revocation_challenge_drill_v0_1_0.py"
)
HANDOFF_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_silver_acceptance_handoff_v0_1_0.py"
)

SUMMARY_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_summary"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_manifest"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.0"

# Closed handoff posture set, ordered by severity (rank 0 = lightest).
HANDOFF_POSTURES = (
    "silver_handoff_complete_for_demo_scope",
    "silver_handoff_complete_review_required_before_reuse",
    "silver_handoff_not_reusable_without_governed_review",
)
HANDOFF_POSTURE_RANK = {p: i for i, p in enumerate(HANDOFF_POSTURES)}

# Drill posture -> minimum handoff posture rank.
DRILL_POSTURE_MIN_RANK = {
    "acceptance_stands_for_demo_scope": 0,
    "acceptance_requires_review_before_reuse": 1,
    "acceptance_not_reusable_without_governed_review": 2,
}

DEFAULT_HANDOFF_PURPOSE = "demo_silver_acceptance_handoff"
DEFAULT_RECIPIENT_ROLE = "demo.handoff_recipient.local_reviewer"
DEFAULT_SOURCE_PACKAGE_FAMILY = (
    "proofrail.silver.composed_gateway_evidence_chain"
)

DEFAULT_SUMMARY_SCOPE_LIMITATIONS = [
    "This handoff applies only to the deterministic v0.2.7 / v0.2.8 / "
    "v0.2.9 demo evidence chain.",
    "This handoff does not transfer reliance from the original v0.2.8 "
    "relying party to any downstream party.",
    "This handoff does not execute acceptance governance or adjudicate "
    "any challenge or revocation signal.",
]
DEFAULT_SUMMARY_NON_CLAIMS = [
    "This handoff package is not a certificate.",
    "This handoff package is not Gold conformance.",
    "This handoff package is not regulator approval.",
    "This handoff package does not establish legally accepted reliance.",
    "This handoff package does not record challenge resolved status.",
    "This handoff package does not record legally revoked status.",
    "This handoff package is not approved for production reliance.",
]
DEFAULT_MANIFEST_SCOPE_LIMITATIONS = [
    "This handoff manifest hash-anchors a local, demo Silver acceptance "
    "handoff package; it is not signed.",
    "This handoff manifest does not establish Gold conformance.",
    "This handoff manifest does not transfer reliance.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This handoff manifest does not certify the underlying evidence "
    "chain.",
    "This handoff manifest does not adjudicate any challenge or "
    "revocation signal.",
    "This handoff manifest does not approve production reliance.",
]

REUSE_WARNING_BY_RANK = {
    0: (
        "Handoff is complete for the deterministic v0.2.7 / v0.2.8 / "
        "v0.2.9 demo scope only. Downstream reuse outside that scope "
        "requires an independent local review."
    ),
    1: (
        "The nested v0.2.9 drill recorded post-acceptance review "
        "triggers (challenge within window and/or revocation signal). "
        "Downstream reuse REQUIRES an independent local review before "
        "reliance."
    ),
    2: (
        "The nested v0.2.9 drill marked the underlying acceptance as "
        "NOT reusable without a governed review process. Downstream "
        "reuse is BLOCKED until that governed review is performed."
    ),
}

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


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def parse_iso_8601_z(value: str) -> datetime | None:
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


def collect_fail_detail(proc: subprocess.CompletedProcess) -> str:
    detail = (proc.stdout + proc.stderr).strip().replace("\n", " ; ")
    if not detail:
        detail = f"subprocess exited {proc.returncode}"
    return detail


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a ProofRail Silver v0.3.0 acceptance handoff package "
            "that composes a v0.2.7 composed gateway evidence manifest, "
            "a v0.2.8 relying-party acceptance package manifest, and a "
            "v0.2.9 revocation/challenge drill package manifest into a "
            "portable, hash-anchored handoff."
        )
    )
    parser.add_argument(
        "--composed-evidence-manifest", required=True, type=Path
    )
    parser.add_argument("--acceptance-manifest", required=True, type=Path)
    parser.add_argument("--drill-manifest", required=True, type=Path)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--handoff-id",
        default="proofrail-silver-acceptance-handoff-demo-001",
    )
    parser.add_argument(
        "--handoff-purpose",
        default=DEFAULT_HANDOFF_PURPOSE,
    )
    parser.add_argument(
        "--recipient-role",
        default=DEFAULT_RECIPIENT_ROLE,
    )
    parser.add_argument(
        "--source-package-family",
        default=DEFAULT_SOURCE_PACKAGE_FAMILY,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Run the v0.3.0 handoff verifier on the staged package "
        "BEFORE moving into place. On failure, the staging directory "
        "is removed and the destination is left untouched.",
    )
    args = parser.parse_args(argv)

    # --- ISO-8601 sanity ---
    if parse_iso_8601_z(args.generated_at) is None:
        return usage_error("--generated-at must be ISO-8601 UTC Z-suffixed")

    for label, value in (
        ("--handoff-id", args.handoff_id),
        ("--handoff-purpose", args.handoff_purpose),
        ("--recipient-role", args.recipient_role),
        ("--source-package-family", args.source_package_family),
    ):
        if not non_empty_str(value):
            return usage_error(f"{label} must be a non-empty string")

    # --- Input files exist ---
    composed_manifest = args.composed_evidence_manifest.resolve()
    accept_manifest = args.acceptance_manifest.resolve()
    drill_manifest = args.drill_manifest.resolve()
    for label, p in (
        ("--composed-evidence-manifest", composed_manifest),
        ("--acceptance-manifest", accept_manifest),
        ("--drill-manifest", drill_manifest),
    ):
        if not p.exists():
            return usage_error(f"{label} not found: {p}")
        if not p.is_file():
            return usage_error(f"{label} is not a file: {p}")

    # --- Output dir resolution ---
    out = args.output_dir.resolve()
    if out.exists() and not args.force:
        return usage_error(
            f"--output-dir already exists: {out} (use --force)"
        )

    # --- Subprocess-invoke v0.2.7 verifier ---
    proc = subprocess.run(
        [
            sys.executable,
            str(COMPOSED_VERIFIER),
            "--manifest",
            str(composed_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "composed_evidence_validation_failed",
            collect_fail_detail(proc),
        )

    # --- Subprocess-invoke v0.2.8 acceptance validator (NO evidence-root) ---
    proc = subprocess.run(
        [
            sys.executable,
            str(ACCEPTANCE_VALIDATOR),
            "--manifest",
            str(accept_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "acceptance_package_validation_failed",
            collect_fail_detail(proc),
        )

    # --- Subprocess-invoke v0.2.9 drill verifier (NO evidence-root) ---
    proc = subprocess.run(
        [
            sys.executable,
            str(DRILL_VERIFIER),
            "--manifest",
            str(drill_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "drill_package_validation_failed",
            collect_fail_detail(proc),
        )

    # --- Stage output in a sibling directory next to the destination ---
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = out.parent / f"{out.name}.staging.{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)

    def cleanup_staging() -> None:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    try:
        staging.mkdir(parents=True)

        # --- Byte-copy v0.2.7 / v0.2.8 / v0.2.9 roots ---
        composed_root = composed_manifest.parent.resolve()
        accept_root = accept_manifest.parent.resolve()
        drill_root = drill_manifest.parent.resolve()

        dest_composed = staging / "composed-gateway-evidence"
        dest_accept = staging / "acceptance-package"
        dest_drill = staging / "revocation-challenge-drill"

        shutil.copytree(composed_root, dest_composed)
        shutil.copytree(accept_root, dest_accept)
        shutil.copytree(drill_root, dest_drill)

        # --- Resolve nested files for the chain binding ---
        nested_composed_manifest = (
            dest_composed / "composed-gateway-evidence-manifest.json"
        )
        nested_accept_manifest = (
            dest_accept / "acceptance-package-manifest.json"
        )
        nested_drill_manifest = (
            dest_drill / "revocation-challenge-drill-manifest.json"
        )
        nested_record = dest_accept / "acceptance-record.json"
        nested_drill_report = (
            dest_drill / "revocation-challenge-drill-report.json"
        )
        inner_accept_evidence_manifest = (
            dest_accept
            / "evidence"
            / "composed-gateway-evidence-manifest.json"
        )
        inner_drill_accept_manifest = (
            dest_drill
            / "acceptance-package"
            / "acceptance-package-manifest.json"
        )

        required_files = [
            ("composed-gateway-evidence manifest", nested_composed_manifest),
            ("acceptance-package manifest", nested_accept_manifest),
            ("revocation-challenge-drill manifest", nested_drill_manifest),
            ("acceptance-record.json", nested_record),
            ("revocation-challenge-drill-report.json", nested_drill_report),
            (
                "acceptance-package/evidence/composed-gateway-evidence-manifest.json",
                inner_accept_evidence_manifest,
            ),
            (
                "revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json",
                inner_drill_accept_manifest,
            ),
        ]
        for label, p in required_files:
            if not p.exists():
                cleanup_staging()
                return fail(
                    "handoff_chain_binding_failed",
                    f"nested package missing required file: {label}",
                )

        # --- Parse nested v0.2.8 record + v0.2.9 report ---
        try:
            record = json.loads(nested_record.read_text())
            drill_report = json.loads(nested_drill_report.read_text())
        except json.JSONDecodeError as e:
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                f"nested v0.2.8 record or v0.2.9 report not valid JSON: {e}",
            )

        # --- Hash the three nested manifests at their top-level location ---
        subj0_sha = sha256_label(nested_composed_manifest)
        subj1_sha = sha256_label(nested_accept_manifest)
        subj2_sha = sha256_label(nested_drill_manifest)

        # --- Four chain-binding cross-checks (v0.3.0 owns this) ---
        record_evp = (
            record.get("evidence_package")
            if isinstance(record, dict)
            else None
        )
        if not isinstance(record_evp, dict):
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                "nested v0.2.8 record missing evidence_package object",
            )
        record_ev_sha = record_evp.get("manifest_sha256")
        if not non_empty_str(record_ev_sha):
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                "nested v0.2.8 record evidence_package.manifest_sha256 "
                "missing or empty",
            )

        drill_base = (
            drill_report.get("base_acceptance")
            if isinstance(drill_report, dict)
            else None
        )
        if not isinstance(drill_base, dict):
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                "nested v0.2.9 drill report missing base_acceptance object",
            )
        drill_accept_sha = drill_base.get("acceptance_package_manifest_sha256")
        if not non_empty_str(drill_accept_sha):
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                "nested v0.2.9 drill report "
                "base_acceptance.acceptance_package_manifest_sha256 "
                "missing or empty",
            )

        # (a) subject[0] sha256 == record.evidence_package.manifest_sha256
        if subj0_sha != record_ev_sha:
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                f"composed gateway evidence manifest sha256 ({subj0_sha}) "
                f"does not match nested v0.2.8 record "
                f"evidence_package.manifest_sha256 ({record_ev_sha})",
            )
        # (b) subject[1] sha256 == drill.base_acceptance.acceptance_package_manifest_sha256
        if subj1_sha != drill_accept_sha:
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                f"acceptance-package manifest sha256 ({subj1_sha}) "
                f"does not match nested v0.2.9 drill "
                f"base_acceptance.acceptance_package_manifest_sha256 "
                f"({drill_accept_sha})",
            )
        # (c) sha256 of v0.2.8's inner copy of the v0.2.7 manifest
        inner_accept_evidence_sha = sha256_label(inner_accept_evidence_manifest)
        if inner_accept_evidence_sha != subj0_sha:
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                f"acceptance-package inner v0.2.7 manifest sha256 "
                f"({inner_accept_evidence_sha}) does not match "
                f"top-level composed gateway evidence manifest sha256 "
                f"({subj0_sha})",
            )
        # (d) sha256 of v0.2.9's inner copy of the v0.2.8 manifest
        inner_drill_accept_sha = sha256_label(inner_drill_accept_manifest)
        if inner_drill_accept_sha != subj1_sha:
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                f"revocation-challenge-drill inner v0.2.8 manifest "
                f"sha256 ({inner_drill_accept_sha}) does not match "
                f"top-level acceptance-package manifest sha256 "
                f"({subj1_sha})",
            )

        # --- Derive summary fields ---
        record_id = record.get("record_id")
        decision = record.get("decision", {}) if isinstance(record, dict) else {}
        decision_status = decision.get("status")
        purpose_id = decision.get("purpose_id")
        if not (
            non_empty_str(record_id)
            and non_empty_str(decision_status)
            and non_empty_str(purpose_id)
        ):
            cleanup_staging()
            return fail(
                "handoff_chain_binding_failed",
                "nested v0.2.8 record missing record_id / decision.status "
                "/ decision.purpose_id",
            )

        drill_posture = drill_report.get("recommended_local_posture")
        if drill_posture not in DRILL_POSTURE_MIN_RANK:
            cleanup_staging()
            return fail(
                "drill_package_validation_failed",
                f"nested v0.2.9 drill recommended_local_posture not in "
                f"known closed set: {drill_posture!r}",
            )
        min_rank = DRILL_POSTURE_MIN_RANK[drill_posture]
        recommended_handoff_posture = HANDOFF_POSTURES[min_rank]
        reuse_warning = REUSE_WARNING_BY_RANK[min_rank]

        # --- Write summary JSON ---
        summary = {
            "document_type": SUMMARY_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "handoff_id": args.handoff_id,
            "generated_at": args.generated_at,
            "handoff_context": {
                "handoff_purpose": args.handoff_purpose,
                "recipient_role": args.recipient_role,
                "source_package_family": args.source_package_family,
            },
            "included_chain": {
                "composed_gateway_evidence": {
                    "manifest_path": (
                        "composed-gateway-evidence/"
                        "composed-gateway-evidence-manifest.json"
                    ),
                    "manifest_sha256": subj0_sha,
                    "source_release": "v0.2.7",
                },
                "relying_party_acceptance": {
                    "manifest_path": (
                        "acceptance-package/acceptance-package-manifest.json"
                    ),
                    "manifest_sha256": subj1_sha,
                    "source_release": "v0.2.8",
                    "acceptance_record_id": record_id,
                    "decision_status": decision_status,
                    "purpose_id": purpose_id,
                },
                "revocation_challenge_drill": {
                    "manifest_path": (
                        "revocation-challenge-drill/"
                        "revocation-challenge-drill-manifest.json"
                    ),
                    "manifest_sha256": subj2_sha,
                    "source_release": "v0.2.9",
                    "recommended_local_posture": drill_posture,
                },
            },
            "handoff_result": {
                "handoff_package_status": "complete",
                "recommended_handoff_posture": recommended_handoff_posture,
                "reuse_warning": reuse_warning,
            },
            "scope_limitations": list(DEFAULT_SUMMARY_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_SUMMARY_NON_CLAIMS),
        }
        summary_path = staging / "silver-acceptance-handoff-summary.json"
        summary_path.write_text(dump_json(summary))

        # --- Build manifest (four subjects in deterministic order) ---
        subjects_spec = [
            (
                "composed-gateway-evidence/composed-gateway-evidence-manifest.json",
                "composed_gateway_evidence_manifest",
            ),
            (
                "acceptance-package/acceptance-package-manifest.json",
                "relying_party_acceptance_package_manifest",
            ),
            (
                "revocation-challenge-drill/revocation-challenge-drill-manifest.json",
                "revocation_challenge_drill_manifest",
            ),
            (
                "silver-acceptance-handoff-summary.json",
                "silver_acceptance_handoff_summary",
            ),
        ]
        subjects: list[dict] = []
        for rel, role in subjects_spec:
            full = staging / rel
            subjects.append(
                {
                    "path": rel,
                    "role": role,
                    "sha256": "sha256:" + sha256_hex(full),
                    "size_bytes": full.stat().st_size,
                }
            )

        manifest = {
            "document_type": MANIFEST_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "handoff_id": args.handoff_id,
            "generated_at": args.generated_at,
            "hash_algorithm": "sha256",
            "package_root": ".",
            "subjects": subjects,
            "scope_limitations": list(DEFAULT_MANIFEST_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
        }
        manifest_path = staging / "silver-acceptance-handoff-manifest.json"
        manifest_path.write_text(dump_json(manifest))

        # --- Self-validate BEFORE atomic move (Amendment 3) ---
        if args.self_validate:
            sv = subprocess.run(
                [
                    sys.executable,
                    str(HANDOFF_VERIFIER),
                    "--manifest",
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )
            if sv.returncode != 0:
                detail = collect_fail_detail(sv)
                cleanup_staging()
                return fail("self_validation_failed", detail)

        # --- Atomically move staging into place ---
        if out.exists():
            shutil.rmtree(out)
        os.replace(str(staging), str(out))
    finally:
        # If staging still exists at this point (e.g. an unexpected
        # exception escaped one of the explicit cleanup_staging() calls
        # above), make sure it does not leak.
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(f"PASS: silver acceptance handoff package built at {out}")
    print(f"  handoff_id: {args.handoff_id}")
    print(f"  included_chain.relying_party_acceptance.acceptance_record_id: "
          f"{record_id}")
    print(f"  included_chain.relying_party_acceptance.decision_status: "
          f"{decision_status}")
    print(f"  included_chain.revocation_challenge_drill."
          f"recommended_local_posture: {drill_posture}")
    print(f"  handoff_result.recommended_handoff_posture: "
          f"{recommended_handoff_posture}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
