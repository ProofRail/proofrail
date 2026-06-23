#!/usr/bin/env python3
"""Inspect a ProofRail Silver v0.3.0 acceptance handoff package and
produce a v0.3.1 Silver handoff inspection package (Silver Handoff
Inspector + Gold Gap Inventory).

The inspector composes a local, deterministic inspection package
binding three subjects in fixed order:

  [0] silver-acceptance-handoff/silver-acceptance-handoff-manifest.json
      (the unchanged v0.3.0 handoff package's manifest, byte-copied
      under silver-acceptance-handoff/)
  [1] gold-boundary-requirements.json
      (the committed, 13-domain Gold-boundary requirement set fixture,
      byte-copied at the inspection package root)
  [2] silver-handoff-inspection-report.json
      (the re-derived inspection report emitted by this runner)

Behavior:

  1. Parses CLI; validates --generated-at as ISO-8601 UTC Z-suffixed.
  2. Refuses to overwrite --output-dir unless --force is supplied.
  3. Subprocess-invokes the unchanged v0.3.0 handoff verifier on
     --handoff-manifest. On non-zero exit prints
         FAIL: handoff_validation_failed: <detail>
     and exits 1.
  4. Subprocess-invokes the v0.3.1 requirement set validator (a
     namespaced entry point inside the v0.3.1 inspection verifier
     module) on --requirement-set. On non-zero exit prints
         FAIL: requirement_set_validation_failed: <detail>
     and exits 1.
  5. Stages output in a sibling directory next to --output-dir.
  6. Byte-copies the v0.3.0 handoff package root into
         <staging>/silver-acceptance-handoff/
     and byte-copies the requirement set file to
         <staging>/gold-boundary-requirements.json
  7. Parses the nested v0.3.0 handoff summary at
         <staging>/silver-acceptance-handoff/silver-acceptance-handoff-summary.json
     and re-derives base_handoff / handoff_summary /
     component_inspection / gold_gap_inventory deterministically.
  8. Writes silver-handoff-inspection-report.json with deterministic
     field shape.
  9. Writes silver-handoff-inspection-manifest.json with three subjects
     in the fixed order required by the v0.3.1 schema; sha256 values
     are recomputed from on-disk bytes.
 10. When --self-validate is supplied, subprocess-invokes the v0.3.1
     inspection verifier on the staged manifest BEFORE moving into
     place. On non-zero exit prints
         FAIL: inspection_self_validation_failed: <detail>
     removes the staging directory (leaving the destination untouched),
     and exits 1.
 11. Atomically moves the staging directory to --output-dir.

The runner never modifies the v0.3.0 handoff package contents; the
copy under silver-acceptance-handoff/ is byte-identical to the input.
The runner does not adjudicate, certify, approve, audit, or transfer
reliance.

Usage:
  python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py \\
    --handoff-manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json \\
    --requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json \\
    --generated-at 2026-06-29T00:00:00Z \\
    --output-dir /tmp/proofrail-silver-handoff-inspection-v0.3.1 \\
    --force \\
    [--self-validate]

Exit codes:
  0 - inspection package generated
  1 - run refused (handoff_validation_failed,
      requirement_set_validation_failed,
      or inspection_self_validation_failed)
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
HANDOFF_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_silver_acceptance_handoff_v0_1_0.py"
)
INSPECTION_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_silver_handoff_inspection_v0_1_0.py"
)

REPORT_DOCUMENT_TYPE = "proofrail.silver.handoff_inspection_report"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.handoff_inspection_manifest"
REQUIREMENT_SET_DOCUMENT_TYPE = "proofrail.silver_to_gold.requirement_set"
SUMMARY_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_summary"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.1"

DEFAULT_INSPECTION_ID = "proofrail-silver-handoff-inspection-demo-001"

# Closed inspection_status set for component_inspection rows.
INSPECTION_STATUS_PRESENT_AND_VERIFIED = "present_and_verified"

# Closed gap_status set (per v0.1.0 requirement set schema).
GAP_STATUS_PRESENT = "silver_evidence_present"
GAP_STATUS_PARTIAL = "silver_evidence_partial"
GAP_STATUS_UNMET = "gold_prerequisite_unmet"
GAP_STATUS_OUT_OF_SCOPE = "out_of_scope_for_silver"
GAP_STATUS_SET = {
    GAP_STATUS_PRESENT,
    GAP_STATUS_PARTIAL,
    GAP_STATUS_UNMET,
    GAP_STATUS_OUT_OF_SCOPE,
}

# Closed gold_boundary_status set.
GOLD_BOUNDARY_STATUS_NOT_CLAIMED = "gold_not_claimed"
GOLD_BOUNDARY_STATUS_INVENTORY_ONLY = "gold_gap_inventory_only"

# Fixed component inspection rows derived from the v0.3.0 handoff
# manifest subjects. The four components are inspected in this fixed
# order. inspection_status is forced to "present_and_verified" because
# the runner already subprocess-validated the v0.3.0 handoff before
# reaching this point.
COMPONENT_INSPECTION_SPEC = [
    {
        "component_id": "v0.2.7-composed-gateway-evidence",
        "component_type": "composed_gateway_evidence",
        "source_release": "v0.2.7",
        "subject_role": "composed_gateway_evidence_manifest",
    },
    {
        "component_id": "v0.2.8-relying-party-acceptance",
        "component_type": "relying_party_acceptance",
        "source_release": "v0.2.8",
        "subject_role": "relying_party_acceptance_package_manifest",
    },
    {
        "component_id": "v0.2.9-revocation-challenge-drill",
        "component_type": "revocation_challenge_drill",
        "source_release": "v0.2.9",
        "subject_role": "revocation_challenge_drill_manifest",
    },
    {
        "component_id": "v0.3.0-silver-acceptance-handoff",
        "component_type": "silver_acceptance_handoff",
        "source_release": "v0.3.0",
        "subject_role": "silver_acceptance_handoff_summary",
    },
]

DEFAULT_REPORT_SCOPE_LIMITATIONS = [
    "This inspection applies only to the deterministic v0.2.7 / v0.2.8 "
    "/ v0.2.9 / v0.3.0 demo evidence chain bound by the v0.3.0 handoff "
    "package.",
    "This inspection does not transfer reliance from the original "
    "v0.2.8 relying party to any downstream party.",
    "This inspection does not adjudicate any challenge, revocation, or "
    "dispute signal preserved in the chain.",
    "The Gold-boundary requirement set bound by this inspection is a "
    "local ProofRail demo inventory, not an external compliance "
    "standard.",
]
DEFAULT_REPORT_NON_CLAIMS = [
    "This inspection report is not a Gold certificate.",
    "This inspection report is not a Gold readiness assessment.",
    "This inspection report is not regulator approval, auditor "
    "approval, or legal advice.",
    "This inspection report is not a downstream-reliance "
    "recommendation.",
    "This inspection report does not authorize production use.",
    "silver_evidence_present means relevant Silver evidence is present, "
    "not that the corresponding Gold prerequisite is satisfied.",
]
DEFAULT_MANIFEST_SCOPE_LIMITATIONS = [
    "This inspection manifest hash-anchors a local, demo Silver "
    "handoff inspection package; it is not signed.",
    "This inspection manifest does not certify the underlying v0.3.0 "
    "handoff package or its nested evidence chain.",
    "This inspection manifest does not transfer reliance.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This inspection manifest is not a Gold certificate.",
    "This inspection manifest is not a Gold readiness assessment.",
    "This inspection manifest does not adjudicate any challenge or "
    "revocation signal preserved in the chain.",
    "This inspection manifest does not authorize production use.",
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


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def parse_iso_8601_z(value: str) -> datetime | None:
    if not isinstance(value, str) or not ISO_8601_RE.match(value):
        return None
    try:
        return datetime.strptime(
            value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z"
        )
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
            "Inspect a ProofRail Silver v0.3.0 acceptance handoff "
            "package and produce a v0.3.1 Silver handoff inspection "
            "package (Silver Handoff Inspector + Gold Gap Inventory). "
            "Does not adjudicate, certify, approve, audit, or transfer "
            "reliance."
        )
    )
    parser.add_argument("--handoff-manifest", required=True, type=Path)
    parser.add_argument("--requirement-set", required=True, type=Path)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--inspection-id",
        default=DEFAULT_INSPECTION_ID,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Run the v0.3.1 inspection verifier on the staged package "
        "BEFORE moving into place. On failure, the staging directory "
        "is removed and the destination is left untouched.",
    )
    args = parser.parse_args(argv)

    # --- ISO-8601 sanity ---
    if parse_iso_8601_z(args.generated_at) is None:
        return usage_error("--generated-at must be ISO-8601 UTC Z-suffixed")

    if not non_empty_str(args.inspection_id):
        return usage_error("--inspection-id must be a non-empty string")

    # --- Input files exist ---
    handoff_manifest = args.handoff_manifest.resolve()
    requirement_set = args.requirement_set.resolve()
    for label, p in (
        ("--handoff-manifest", handoff_manifest),
        ("--requirement-set", requirement_set),
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

    # --- Subprocess-invoke unchanged v0.3.0 handoff verifier ---
    proc = subprocess.run(
        [
            sys.executable,
            str(HANDOFF_VERIFIER),
            "--manifest",
            str(handoff_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "handoff_validation_failed",
            collect_fail_detail(proc),
        )

    # --- Subprocess-invoke v0.3.1 requirement set validator entry point ---
    proc = subprocess.run(
        [
            sys.executable,
            str(INSPECTION_VERIFIER),
            "--validate-requirement-set",
            str(requirement_set),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "requirement_set_validation_failed",
            collect_fail_detail(proc),
        )

    # --- Parse the requirement set (already validated above) ---
    try:
        req_set = json.loads(requirement_set.read_text())
    except json.JSONDecodeError as e:
        return fail(
            "requirement_set_validation_failed",
            f"requirement set not valid JSON: {e}",
        )
    if not isinstance(req_set, dict):
        return fail(
            "requirement_set_validation_failed",
            "requirement set is not a JSON object",
        )
    req_set_id = req_set.get("requirement_set_id")
    req_set_version = req_set.get("requirement_set_version")
    requirements = req_set.get("requirements")
    if not (
        non_empty_str(req_set_id)
        and non_empty_str(req_set_version)
        and isinstance(requirements, list)
        and len(requirements) > 0
    ):
        return fail(
            "requirement_set_validation_failed",
            "requirement set missing requirement_set_id, "
            "requirement_set_version, or requirements[]",
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

        # --- Byte-copy v0.3.0 handoff package root under silver-acceptance-handoff/ ---
        handoff_root = handoff_manifest.parent.resolve()
        dest_handoff = staging / "silver-acceptance-handoff"
        shutil.copytree(handoff_root, dest_handoff)

        nested_handoff_manifest = (
            dest_handoff / "silver-acceptance-handoff-manifest.json"
        )
        nested_handoff_summary = (
            dest_handoff / "silver-acceptance-handoff-summary.json"
        )
        for label, p in (
            ("silver-acceptance-handoff-manifest.json", nested_handoff_manifest),
            ("silver-acceptance-handoff-summary.json", nested_handoff_summary),
        ):
            if not p.exists():
                cleanup_staging()
                return fail(
                    "handoff_validation_failed",
                    f"nested v0.3.0 handoff package missing {label}",
                )

        # --- Byte-copy requirement set to package root ---
        dest_req_set = staging / "gold-boundary-requirements.json"
        shutil.copyfile(requirement_set, dest_req_set)

        # --- Parse nested v0.3.0 handoff manifest + summary ---
        try:
            nested_manifest = json.loads(nested_handoff_manifest.read_text())
            nested_summary = json.loads(nested_handoff_summary.read_text())
        except json.JSONDecodeError as e:
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                f"nested v0.3.0 handoff manifest or summary not valid "
                f"JSON: {e}",
            )

        if not (
            isinstance(nested_manifest, dict)
            and isinstance(nested_summary, dict)
        ):
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                "nested v0.3.0 handoff manifest or summary is not a JSON "
                "object",
            )

        handoff_id = nested_summary.get("handoff_id")
        if not non_empty_str(handoff_id):
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                "nested v0.3.0 handoff summary missing handoff_id",
            )

        included_chain = nested_summary.get("included_chain")
        handoff_result = nested_summary.get("handoff_result")
        if not (
            isinstance(included_chain, dict)
            and isinstance(handoff_result, dict)
        ):
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                "nested v0.3.0 handoff summary missing included_chain "
                "or handoff_result object",
            )

        rpa = included_chain.get("relying_party_acceptance")
        if not isinstance(rpa, dict):
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                "nested v0.3.0 handoff summary "
                "included_chain.relying_party_acceptance missing",
            )
        acceptance_record_id = rpa.get("acceptance_record_id")
        decision_status = rpa.get("decision_status")
        purpose_id = rpa.get("purpose_id")
        recommended_handoff_posture = handoff_result.get(
            "recommended_handoff_posture"
        )
        reuse_warning = handoff_result.get("reuse_warning")
        if not (
            non_empty_str(acceptance_record_id)
            and non_empty_str(decision_status)
            and non_empty_str(purpose_id)
            and non_empty_str(recommended_handoff_posture)
            and isinstance(reuse_warning, str)
        ):
            cleanup_staging()
            return fail(
                "handoff_validation_failed",
                "nested v0.3.0 handoff summary missing "
                "acceptance_record_id / decision_status / purpose_id / "
                "recommended_handoff_posture / reuse_warning",
            )

        # --- Hash subject[0]: the nested v0.3.0 handoff manifest ---
        subj0_sha = sha256_label(nested_handoff_manifest)
        # --- Hash subject[1]: the requirement set fixture ---
        subj1_sha = sha256_label(dest_req_set)

        # --- Build component_inspection rows (fixed order) ---
        component_inspection: list[dict] = []
        for spec in COMPONENT_INSPECTION_SPEC:
            component_inspection.append(
                {
                    "component_id": spec["component_id"],
                    "component_type": spec["component_type"],
                    "source_release": spec["source_release"],
                    "inspection_status": INSPECTION_STATUS_PRESENT_AND_VERIFIED,
                }
            )

        # --- Build gold_gap_inventory ---
        gap_counts = {
            GAP_STATUS_PRESENT: 0,
            GAP_STATUS_PARTIAL: 0,
            GAP_STATUS_UNMET: 0,
            GAP_STATUS_OUT_OF_SCOPE: 0,
        }
        requirement_rows: list[dict] = []
        for req in requirements:
            if not isinstance(req, dict):
                cleanup_staging()
                return fail(
                    "requirement_set_validation_failed",
                    "requirement entry is not an object",
                )
            r_id = req.get("requirement_id")
            r_domain = req.get("domain")
            r_status = req.get("expected_gap_status")
            r_reason = req.get("reason")
            r_evidence = req.get("silver_evidence_mapping")
            if not (
                non_empty_str(r_id)
                and non_empty_str(r_domain)
                and r_status in GAP_STATUS_SET
                and non_empty_str(r_reason)
                and isinstance(r_evidence, list)
            ):
                cleanup_staging()
                return fail(
                    "requirement_set_validation_failed",
                    f"requirement {r_id!r} missing required fields or "
                    f"has unknown expected_gap_status {r_status!r}",
                )
            evidence_refs: list[str] = []
            for ref in r_evidence:
                if not non_empty_str(ref):
                    cleanup_staging()
                    return fail(
                        "requirement_set_validation_failed",
                        f"requirement {r_id!r} silver_evidence_mapping "
                        f"contains an empty or non-string entry",
                    )
                evidence_refs.append(ref)
            gap_counts[r_status] += 1
            requirement_rows.append(
                {
                    "requirement_id": r_id,
                    "domain": r_domain,
                    "gap_status": r_status,
                    "evidence_refs": evidence_refs,
                    "reason": r_reason,
                }
            )

        gold_prerequisites_unmet = (
            gap_counts[GAP_STATUS_PARTIAL]
            + gap_counts[GAP_STATUS_UNMET]
            + gap_counts[GAP_STATUS_OUT_OF_SCOPE]
        ) > 0
        # gold_boundary_status is forced to gold_not_claimed whenever
        # any row is silver_evidence_partial, gold_prerequisite_unmet,
        # or out_of_scope_for_silver. The closed alternative
        # gold_gap_inventory_only is reserved for a future hypothetical
        # all-silver_evidence_present requirement set, which the v0.3.1
        # demo fixture intentionally does not provide.
        if gold_prerequisites_unmet:
            gold_boundary_status = GOLD_BOUNDARY_STATUS_NOT_CLAIMED
        else:
            gold_boundary_status = GOLD_BOUNDARY_STATUS_INVENTORY_ONLY

        gold_gap_inventory = {
            "requirement_set_id": req_set_id,
            "requirement_set_version": req_set_version,
            "requirements_path": "gold-boundary-requirements.json",
            "requirements_sha256": subj1_sha,
            "requirement_count": len(requirement_rows),
            "gold_boundary_status": gold_boundary_status,
            "gold_prerequisites_unmet": gold_prerequisites_unmet,
            "counts": gap_counts,
            "requirements": requirement_rows,
        }

        # --- Build inspection report ---
        report = {
            "document_type": REPORT_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "inspection_id": args.inspection_id,
            "generated_at": args.generated_at,
            "base_handoff": {
                "handoff_id": handoff_id,
                "handoff_manifest_path": (
                    "silver-acceptance-handoff/"
                    "silver-acceptance-handoff-manifest.json"
                ),
                "handoff_manifest_sha256": subj0_sha,
                "handoff_verification_status": "pass",
            },
            "handoff_summary": {
                "acceptance_record_id": acceptance_record_id,
                "decision_status": decision_status,
                "purpose_id": purpose_id,
                "recommended_handoff_posture": recommended_handoff_posture,
                "reuse_warning": reuse_warning,
            },
            "component_inspection": component_inspection,
            "gold_gap_inventory": gold_gap_inventory,
            "scope_limitations": list(DEFAULT_REPORT_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_REPORT_NON_CLAIMS),
        }
        report_path = staging / "silver-handoff-inspection-report.json"
        report_path.write_text(dump_json(report))

        # --- Hash subject[2]: the inspection report just written ---
        subj2_sha = sha256_label(report_path)

        # --- Build inspection manifest (three subjects in fixed order) ---
        subjects_spec = [
            (
                "silver-acceptance-handoff/"
                "silver-acceptance-handoff-manifest.json",
                "silver_acceptance_handoff_manifest",
                nested_handoff_manifest,
                subj0_sha,
            ),
            (
                "gold-boundary-requirements.json",
                "gold_boundary_requirement_set",
                dest_req_set,
                subj1_sha,
            ),
            (
                "silver-handoff-inspection-report.json",
                "silver_handoff_inspection_report",
                report_path,
                subj2_sha,
            ),
        ]
        subjects: list[dict] = []
        for rel, role, on_disk_path, sha_label in subjects_spec:
            subjects.append(
                {
                    "path": rel,
                    "role": role,
                    "sha256": sha_label,
                    "size_bytes": on_disk_path.stat().st_size,
                }
            )

        manifest = {
            "document_type": MANIFEST_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "inspection_id": args.inspection_id,
            "generated_at": args.generated_at,
            "hash_algorithm": "sha256",
            "subjects": subjects,
            "scope_limitations": list(DEFAULT_MANIFEST_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
        }
        manifest_path = staging / "silver-handoff-inspection-manifest.json"
        manifest_path.write_text(dump_json(manifest))

        # --- Self-validate BEFORE atomic move ---
        if args.self_validate:
            sv = subprocess.run(
                [
                    sys.executable,
                    str(INSPECTION_VERIFIER),
                    "--manifest",
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )
            if sv.returncode != 0:
                detail = collect_fail_detail(sv)
                cleanup_staging()
                return fail("inspection_self_validation_failed", detail)

        # --- Atomically move staging into place ---
        if out.exists():
            shutil.rmtree(out)
        os.replace(str(staging), str(out))
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(f"PASS: silver handoff inspection package built at {out}")
    print(f"  inspection_id: {args.inspection_id}")
    print(f"  base_handoff.handoff_id: {handoff_id}")
    print(
        f"  handoff_summary.acceptance_record_id: {acceptance_record_id}"
    )
    print(f"  handoff_summary.decision_status: {decision_status}")
    print(
        f"  handoff_summary.recommended_handoff_posture: "
        f"{recommended_handoff_posture}"
    )
    print(
        f"  gold_gap_inventory.gold_boundary_status: "
        f"{gold_boundary_status}"
    )
    print(
        f"  gold_gap_inventory.counts: "
        f"present={gap_counts[GAP_STATUS_PRESENT]} "
        f"partial={gap_counts[GAP_STATUS_PARTIAL]} "
        f"unmet={gap_counts[GAP_STATUS_UNMET]} "
        f"out_of_scope={gap_counts[GAP_STATUS_OUT_OF_SCOPE]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
