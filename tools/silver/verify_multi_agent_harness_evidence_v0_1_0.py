#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.2.4 multi-agent attack harness evidence manifest.

The verifier:
  1. Parses the evidence manifest JSON.
  2. Validates manifest_type, manifest_version, hash_algorithm, non-empty subjects.
  3. Rejects subject paths containing '..' components.
  4. Confirms every subject file exists.
  5. Recomputes SHA-256 for every subject and compares to the manifest.
  6. Validates the harness run report subject (type, version, summary.status,
     execution.protected_actions_performed).
  7. Validates every authority decision report subject (type, execution.performed).

Usage:
  python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py \\
    --manifest <harness-evidence-manifest.json>

Exit codes:
  0 evidence valid
  1 evidence invalid
  2 usage/input error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EVIDENCE_MANIFEST_TYPE = "proofrail.silver.multi_agent_harness_evidence_manifest"
EVIDENCE_MANIFEST_VERSION = "v0.1.0"
RUN_REPORT_TYPE = "proofrail.silver.multi_agent_harness_run_report"
RUN_REPORT_VERSION = "v0.1.0"
DECISION_REPORT_TYPE = "proofrail.silver.protected_action_decision_report"


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def has_traversal(rel: str) -> bool:
    parts = Path(rel).parts
    return ".." in parts or rel.startswith("/")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a Silver v0.2.4 multi-agent harness evidence manifest."
    )
    parser.add_argument("--manifest", required=True, help="Path to harness-evidence-manifest.json")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        err(f"manifest not found: {manifest_path}")
        return 2

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_evidence_manifest", f"JSON parse error: {e}")

    if not isinstance(manifest, dict):
        return fail("invalid_evidence_manifest", "root must be a JSON object")

    if manifest.get("manifest_type") != EVIDENCE_MANIFEST_TYPE:
        return fail("invalid_evidence_manifest", f"manifest_type must be '{EVIDENCE_MANIFEST_TYPE}'")
    if manifest.get("manifest_version") != EVIDENCE_MANIFEST_VERSION:
        return fail("invalid_evidence_manifest", f"manifest_version must be '{EVIDENCE_MANIFEST_VERSION}'")
    if manifest.get("hash_algorithm") != "sha256":
        return fail("invalid_evidence_manifest", "hash_algorithm must be 'sha256'")

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        return fail("invalid_evidence_manifest", "subjects must be a non-empty list")

    limitations = manifest.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        return fail("invalid_evidence_manifest", "limitations must be a non-empty list")

    base_dir = manifest_path.parent

    # Pre-pass: traversal check
    for s in subjects:
        if not isinstance(s, dict):
            return fail("invalid_evidence_manifest", "subject entry must be an object")
        rel = s.get("path", "")
        if not isinstance(rel, str) or not rel:
            return fail("invalid_evidence_manifest", "subject.path must be a non-empty string")
        if has_traversal(rel):
            return fail("subject_path_traversal", f"path '{rel}' contains '..' or is absolute")

    # Hash check pass
    run_report_subject_path: Path | None = None
    decision_report_paths: list[Path] = []
    for s in subjects:
        rel = s["path"]
        subject_type = s.get("subject_type", "")
        recorded = s.get("sha256", "")
        if not isinstance(recorded, str) or not recorded.startswith("sha256:"):
            return fail("invalid_evidence_manifest", f"subject.sha256 malformed for '{rel}'")
        target = base_dir / rel
        if not target.exists() or not target.is_file():
            return fail("subject_file_missing", f"path '{rel}'")
        actual = "sha256:" + sha256_hex(target)
        if actual != recorded:
            return fail("subject_hash_mismatch", f"path '{rel}': recorded={recorded} actual={actual}")
        if subject_type == "harness_run_report":
            run_report_subject_path = target
        elif subject_type == "authority_decision_report":
            decision_report_paths.append(target)

    # Run report semantic checks
    if run_report_subject_path is None:
        return fail("invalid_evidence_manifest", "no harness_run_report subject present")
    try:
        run_report = json.loads(run_report_subject_path.read_text())
    except json.JSONDecodeError as e:
        return fail("harness_run_failed", f"run report not valid JSON: {e}")
    if run_report.get("report_type") != RUN_REPORT_TYPE:
        return fail("harness_run_failed", f"run report_type must be '{RUN_REPORT_TYPE}'")
    if run_report.get("report_version") != RUN_REPORT_VERSION:
        return fail("harness_run_failed", f"run report_version must be '{RUN_REPORT_VERSION}'")
    summary = run_report.get("summary", {})
    if not isinstance(summary, dict) or summary.get("status") != "pass":
        return fail("harness_run_failed", f"summary.status != 'pass' (got {summary.get('status')!r})")
    execution = run_report.get("execution", {})
    if not isinstance(execution, dict) or execution.get("protected_actions_performed") is not False:
        return fail("execution_violation", "run report execution.protected_actions_performed must be false")

    # Decision report checks
    for dpath in decision_report_paths:
        try:
            dr = json.loads(dpath.read_text())
        except json.JSONDecodeError as e:
            return fail("decision_report_invalid", f"{dpath.name}: JSON parse error: {e}")
        if dr.get("report_type") != DECISION_REPORT_TYPE:
            return fail("decision_report_invalid", f"{dpath.name}: report_type must be '{DECISION_REPORT_TYPE}'")
        dex = dr.get("execution", {})
        if not isinstance(dex, dict) or dex.get("performed") is not False:
            return fail("execution_violation", f"{dpath.name}: execution.performed must be false")

    print(f"PASS: harness evidence manifest valid ({len(subjects)} subjects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
