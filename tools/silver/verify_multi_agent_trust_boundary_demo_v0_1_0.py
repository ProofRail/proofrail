#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.2.5 multi-agent trust-boundary demo package.

The verifier:

  1. Parses the package manifest JSON.
  2. Validates manifest structure, hash algorithm, and nested_verification block.
  3. Rejects subject paths containing '..' or starting with '/'.
  4. Confirms every package subject exists.
  5. Recomputes SHA-256 for every package subject and compares to the manifest.
  6. Parses demo-summary.json and structurally validates it (no Python tracebacks).
  7. Confirms every required demo claim is present with status 'pass'.
  8. Cross-checks each claim's evidence references against the nested v0.2.4
     run report and decision reports (not only structural presence).
  9. Confirms execution.protected_actions_performed == false in the summary
     and in the nested run report.
 10. Invokes the v0.2.4 harness evidence verifier as a subprocess on the
     nested harness-evidence-manifest.json. Any nested failure is surfaced
     at the package level as 'nested_harness_evidence_invalid' (the nested
     reason may be included as context only).
 11. Exits 0 only if all checks pass.

Usage:
  python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \\
    --package-manifest <demo-package-manifest.json>

Exit codes:
  0 package and nested harness evidence both valid
  1 package invalid (stable reason printed)
  2 usage/input error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_VERIFIER = REPO_ROOT / "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py"

PACKAGE_MANIFEST_TYPE = "proofrail.silver.multi_agent_demo_package_manifest"
PACKAGE_MANIFEST_VERSION = "v0.1.0"
SUMMARY_TYPE = "proofrail.silver.multi_agent_demo_summary"
SUMMARY_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.5"
RUN_REPORT_TYPE = "proofrail.silver.multi_agent_harness_run_report"
DECISION_REPORT_TYPE = "proofrail.silver.protected_action_decision_report"

REQUIRED_CLAIMS = [
    "harmless_messages_proceed",
    "protected_actions_require_scoped_authority",
    "unauthorized_delegation_fails",
    "bypass_attempts_blocked",
    "revoked_authority_fails",
    "out_of_scope_actions_fail",
    "evidence_is_hash_verifiable",
    "no_protected_actions_executed",
]

REQUIRED_PACKAGE_ROLES = [
    "demo_readme",
    "demo_walkthrough",
    "demo_summary",
    "nested_harness_evidence_manifest",
]


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def fail(reason: str, detail: str = "") -> int:
    if detail:
        print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    else:
        print(f"FAIL: {reason}", file=sys.stderr)
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
    if not isinstance(rel, str) or not rel:
        return True
    parts = Path(rel).parts
    return ".." in parts or rel.startswith("/")


def read_jsonl(path: Path) -> list[dict] | None:
    """Return list of records, or None if any line fails to parse."""
    records: list[dict] = []
    try:
        with path.open("r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        return None
    return records


def load_decision_report(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def cross_check_claim(
    claim: dict,
    package_root: Path,
    transcript: list[dict],
    decision_reports_dir: Path,
    nested_run_report: dict,
) -> tuple[str, str] | None:
    """Return (reason, detail) on failure, or None on pass."""
    claim_id = claim.get("claim_id", "")
    refs = claim.get("evidence_refs", [])
    if not isinstance(refs, list) or not refs:
        return ("demo_claim_failed", f"{claim_id}: evidence_refs must be a non-empty list")

    # Pre-validate every ref's artifact path.
    for ref in refs:
        if not isinstance(ref, dict):
            return ("demo_evidence_ref_invalid", f"{claim_id}: ref must be an object")
        art = ref.get("artifact")
        if not isinstance(art, str) or not art:
            return ("demo_evidence_ref_invalid", f"{claim_id}: artifact missing")
        if has_traversal(art):
            return ("demo_evidence_ref_invalid", f"{claim_id}: artifact '{art}' contains '..' or is absolute")
        target = package_root / art
        if not target.exists():
            return ("demo_evidence_ref_invalid", f"{claim_id}: artifact '{art}' not found")

    # Index transcript by event_id.
    transcript_by_id: dict[str, dict] = {r["event_id"]: r for r in transcript if "event_id" in r}

    if claim_id == "harmless_messages_proceed":
        for ref in refs:
            ev_id = ref.get("event_id")
            if not isinstance(ev_id, str) or ev_id not in transcript_by_id:
                return ("demo_evidence_ref_invalid",
                        f"{claim_id}: event_id '{ev_id}' not in transcript")
            rec = transcript_by_id[ev_id]
            if rec.get("event_type") != "agent_message":
                return ("demo_claim_failed",
                        f"{claim_id}: event '{ev_id}' is not an agent_message")
            actual = rec.get("actual", {}) if isinstance(rec.get("actual"), dict) else {}
            if actual.get("harness_outcome") != "message_delivered":
                return ("demo_claim_failed",
                        f"{claim_id}: event '{ev_id}' harness_outcome != 'message_delivered'")
        return None

    if claim_id == "bypass_attempts_blocked":
        for ref in refs:
            ev_id = ref.get("event_id")
            if not isinstance(ev_id, str) or ev_id not in transcript_by_id:
                return ("demo_evidence_ref_invalid",
                        f"{claim_id}: event_id '{ev_id}' not in transcript")
            rec = transcript_by_id[ev_id]
            if rec.get("event_type") != "bypass_attempt":
                return ("demo_claim_failed",
                        f"{claim_id}: event '{ev_id}' is not a bypass_attempt")
            actual = rec.get("actual", {}) if isinstance(rec.get("actual"), dict) else {}
            if actual.get("harness_outcome") != "bypass_blocked":
                return ("demo_claim_failed",
                        f"{claim_id}: event '{ev_id}' harness_outcome != 'bypass_blocked'")
            if actual.get("harness_reason") != "bypass_attempt_detected":
                return ("demo_claim_failed",
                        f"{claim_id}: event '{ev_id}' harness_reason != 'bypass_attempt_detected'")
        return None

    if claim_id == "revoked_authority_fails":
        has_marker = False
        has_revoked_decision = False
        for ref in refs:
            art = ref["artifact"]
            ev_id = ref.get("event_id")
            if art == "harness-evidence/transcript.jsonl":
                if not isinstance(ev_id, str) or ev_id not in transcript_by_id:
                    return ("demo_evidence_ref_invalid",
                            f"{claim_id}: transcript event_id '{ev_id}' not found")
                rec = transcript_by_id[ev_id]
                if rec.get("event_type") == "revocation_marker":
                    actual = rec.get("actual", {}) if isinstance(rec.get("actual"), dict) else {}
                    if actual.get("harness_outcome") == "revocation_marked":
                        has_marker = True
                    else:
                        return ("demo_claim_failed",
                                f"{claim_id}: marker event harness_outcome != 'revocation_marked'")
                else:
                    return ("demo_claim_failed",
                            f"{claim_id}: transcript event '{ev_id}' is not a revocation_marker")
            elif art.startswith("harness-evidence/authority-decision-reports/"):
                target = package_root / art
                dr = load_decision_report(target)
                if dr is None:
                    return ("demo_claim_failed",
                            f"{claim_id}: decision report '{art}' unreadable")
                decision = dr.get("decision", {}) if isinstance(dr.get("decision"), dict) else {}
                if decision.get("status") == "deny" and decision.get("reason") == "authority_revoked":
                    has_revoked_decision = True
                else:
                    return ("demo_claim_failed",
                            f"{claim_id}: decision report '{art}' is not a deny/authority_revoked")
            else:
                return ("demo_evidence_ref_invalid",
                        f"{claim_id}: artifact '{art}' not a transcript or decision report")
        if not has_marker:
            return ("demo_claim_failed",
                    f"{claim_id}: no revocation_marker among evidence_refs")
        if not has_revoked_decision:
            return ("demo_claim_failed",
                    f"{claim_id}: no authority_revoked decision report among evidence_refs")
        return None

    # The remaining claims share decision-report rule sets.
    if claim_id == "protected_actions_require_scoped_authority":
        expected_status, expected_reason = "allow", None
    elif claim_id == "unauthorized_delegation_fails":
        expected_status, expected_reason = "deny", "authority_subject_mismatch"
    elif claim_id == "out_of_scope_actions_fail":
        expected_status, expected_reason = "deny", "constraint_not_satisfied"
    elif claim_id == "evidence_is_hash_verifiable":
        # Must reference the nested manifest; nested verifier is re-run elsewhere.
        ok = any(ref.get("artifact") == "harness-evidence/harness-evidence-manifest.json"
                 for ref in refs)
        if not ok:
            return ("demo_claim_failed",
                    f"{claim_id}: must reference harness-evidence/harness-evidence-manifest.json")
        return None
    elif claim_id == "no_protected_actions_executed":
        ok = any(ref.get("artifact") == "harness-evidence/harness-run-report.json" for ref in refs)
        if not ok:
            return ("demo_claim_failed",
                    f"{claim_id}: must reference harness-evidence/harness-run-report.json")
        run_exec = nested_run_report.get("execution", {}) \
            if isinstance(nested_run_report.get("execution"), dict) else {}
        if run_exec.get("protected_actions_performed") is not False:
            return ("demo_execution_violation",
                    f"{claim_id}: nested run report protected_actions_performed != false")
        # Also walk every decision report on disk.
        if decision_reports_dir.exists():
            for p in sorted(decision_reports_dir.iterdir(), key=lambda x: x.name):
                if not p.is_file() or p.suffix != ".json":
                    continue
                dr = load_decision_report(p)
                if dr is None:
                    return ("demo_claim_failed",
                            f"{claim_id}: decision report '{p.name}' unreadable")
                dex = dr.get("execution", {}) if isinstance(dr.get("execution"), dict) else {}
                if dex.get("performed") is not False:
                    return ("demo_execution_violation",
                            f"{claim_id}: decision report '{p.name}' execution.performed != false")
        return None
    else:
        return ("demo_claim_failed", f"unknown claim_id: {claim_id}")

    # Decision-report rule path: every evidence_ref must be a decision report
    # whose decision.status/reason match expected.
    for ref in refs:
        art = ref["artifact"]
        if not art.startswith("harness-evidence/authority-decision-reports/"):
            return ("demo_evidence_ref_invalid",
                    f"{claim_id}: artifact '{art}' is not a decision report")
        target = package_root / art
        dr = load_decision_report(target)
        if dr is None:
            return ("demo_claim_failed",
                    f"{claim_id}: decision report '{art}' unreadable")
        if dr.get("report_type") != DECISION_REPORT_TYPE:
            return ("demo_claim_failed",
                    f"{claim_id}: decision report '{art}' report_type mismatch")
        decision = dr.get("decision", {}) if isinstance(dr.get("decision"), dict) else {}
        if decision.get("status") != expected_status:
            return ("demo_claim_failed",
                    f"{claim_id}: decision report '{art}' status != '{expected_status}'")
        if expected_reason is not None and decision.get("reason") != expected_reason:
            return ("demo_claim_failed",
                    f"{claim_id}: decision report '{art}' reason != '{expected_reason}'")
        execution = dr.get("execution", {}) if isinstance(dr.get("execution"), dict) else {}
        if execution.get("performed") is not False:
            return ("demo_execution_violation",
                    f"{claim_id}: decision report '{art}' execution.performed != false")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a Silver v0.2.5 multi-agent trust-boundary demo package."
    )
    parser.add_argument("--package-manifest", required=True,
                        help="Path to demo-package-manifest.json")
    args = parser.parse_args()

    manifest_path = Path(args.package_manifest)
    if not manifest_path.exists():
        err(f"package manifest not found: {manifest_path}")
        return 2
    if not HARNESS_VERIFIER.exists():
        err(f"v0.2.4 harness verifier not found: {HARNESS_VERIFIER}")
        return 2

    # 1. Parse package manifest.
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_demo_package_manifest", f"JSON parse error: {e}")
    if not isinstance(manifest, dict):
        return fail("invalid_demo_package_manifest", "root must be a JSON object")

    # 2. Validate structure.
    if manifest.get("document_type") != PACKAGE_MANIFEST_TYPE:
        return fail("invalid_demo_package_manifest", f"document_type must be '{PACKAGE_MANIFEST_TYPE}'")
    if manifest.get("schema_version") != PACKAGE_MANIFEST_VERSION:
        return fail("invalid_demo_package_manifest", f"schema_version must be '{PACKAGE_MANIFEST_VERSION}'")
    if manifest.get("proofrail_release") != PROOFRAIL_RELEASE:
        return fail("invalid_demo_package_manifest", f"proofrail_release must be '{PROOFRAIL_RELEASE}'")
    if manifest.get("hash_algorithm") != "sha256":
        return fail("invalid_demo_package_manifest", "hash_algorithm must be 'sha256'")
    if manifest.get("package_root") != ".":
        return fail("invalid_demo_package_manifest", "package_root must be '.'")
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        return fail("invalid_demo_package_manifest", "subjects must be a non-empty list")
    nv = manifest.get("nested_verification")
    if not isinstance(nv, dict):
        return fail("invalid_demo_package_manifest", "nested_verification missing")
    if nv.get("harness_evidence_verified") is not True:
        return fail("invalid_demo_package_manifest", "nested_verification.harness_evidence_verified must be true")
    if not isinstance(nv.get("verifier"), str) or not nv["verifier"]:
        return fail("invalid_demo_package_manifest", "nested_verification.verifier missing")
    if not isinstance(nv.get("nested_manifest_path"), str) or not nv["nested_manifest_path"]:
        return fail("invalid_demo_package_manifest", "nested_verification.nested_manifest_path missing")
    limitations = manifest.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        return fail("invalid_demo_package_manifest", "limitations must be a non-empty list")

    package_root = manifest_path.parent

    # 3. Path traversal pre-pass.
    for s in subjects:
        if not isinstance(s, dict):
            return fail("invalid_demo_package_manifest", "subject entry must be an object")
        rel = s.get("path", "")
        if has_traversal(rel):
            return fail("demo_subject_path_traversal", f"path '{rel}' contains '..' or is absolute")

    # Required roles must each appear at the expected path exactly once.
    role_to_path = {
        "demo_readme": "README.md",
        "demo_walkthrough": "demo-walkthrough.md",
        "demo_summary": "demo-summary.json",
        "nested_harness_evidence_manifest": "harness-evidence/harness-evidence-manifest.json",
    }
    seen_roles: dict[str, int] = {}
    for s in subjects:
        role = s.get("role", "")
        seen_roles[role] = seen_roles.get(role, 0) + 1
    for role in REQUIRED_PACKAGE_ROLES:
        if seen_roles.get(role, 0) < 1:
            return fail("invalid_demo_package_manifest", f"required role '{role}' missing")

    # Check the role-to-path expectation for the four required subjects.
    role_path_map: dict[str, str] = {}
    for s in subjects:
        role = s.get("role", "")
        if role in role_to_path:
            role_path_map[role] = s.get("path", "")
    for role, expected_path in role_to_path.items():
        if role_path_map.get(role) != expected_path:
            return fail("invalid_demo_package_manifest",
                        f"role '{role}' path must be '{expected_path}', got '{role_path_map.get(role)}'")

    # nested_verification.nested_manifest_path must match the nested subject's path.
    if nv["nested_manifest_path"] != "harness-evidence/harness-evidence-manifest.json":
        return fail("invalid_demo_package_manifest",
                    "nested_verification.nested_manifest_path must equal "
                    "'harness-evidence/harness-evidence-manifest.json'")

    # 4 + 5. Existence and hash check.
    for s in subjects:
        rel = s["path"]
        recorded = s.get("sha256", "")
        if not isinstance(recorded, str) or not recorded.startswith("sha256:"):
            return fail("invalid_demo_package_manifest", f"subject.sha256 malformed for '{rel}'")
        target = package_root / rel
        if not target.exists() or not target.is_file():
            return fail("demo_subject_file_missing", f"path '{rel}'")
        actual = "sha256:" + sha256_hex(target)
        if actual != recorded:
            return fail("demo_subject_hash_mismatch",
                        f"path '{rel}': recorded={recorded} actual={actual}")

    # 6. Parse demo summary. JSON parse errors must NOT leak as Python tracebacks.
    summary_path = package_root / "demo-summary.json"
    try:
        summary_text = summary_path.read_text()
    except OSError as e:
        return fail("invalid_demo_summary", f"cannot read demo-summary.json: {e}")
    try:
        summary = json.loads(summary_text)
    except json.JSONDecodeError as e:
        return fail("invalid_demo_summary", f"JSON parse error: {e}")
    if not isinstance(summary, dict):
        return fail("invalid_demo_summary", "root must be a JSON object")
    if summary.get("document_type") != SUMMARY_TYPE:
        return fail("invalid_demo_summary", f"document_type must be '{SUMMARY_TYPE}'")
    if summary.get("schema_version") != SUMMARY_VERSION:
        return fail("invalid_demo_summary", f"schema_version must be '{SUMMARY_VERSION}'")
    if summary.get("proofrail_release") != PROOFRAIL_RELEASE:
        return fail("invalid_demo_summary", f"proofrail_release must be '{PROOFRAIL_RELEASE}'")
    src = summary.get("source_harness")
    if not isinstance(src, dict):
        return fail("invalid_demo_summary", "source_harness missing")
    for f in ("harness_release", "harness_manifest_path", "harness_run_report_path"):
        if not isinstance(src.get(f), str) or not src[f]:
            return fail("invalid_demo_summary", f"source_harness.{f} missing")
    summary_limits = summary.get("limitations")
    if not isinstance(summary_limits, list) or not summary_limits:
        return fail("invalid_demo_summary", "limitations must be a non-empty list")
    execution_block = summary.get("execution")
    if not isinstance(execution_block, dict):
        return fail("invalid_demo_summary", "execution block missing")
    if execution_block.get("protected_actions_performed") is not False:
        return fail("demo_execution_violation",
                    "summary execution.protected_actions_performed != false")
    claims = summary.get("claims")
    if not isinstance(claims, list) or not claims:
        return fail("invalid_demo_summary", "claims must be a non-empty list")

    # Index claims by ID and confirm required IDs present.
    by_id: dict[str, dict] = {}
    for c in claims:
        if not isinstance(c, dict):
            return fail("invalid_demo_summary", "claim entry must be an object")
        cid = c.get("claim_id")
        if not isinstance(cid, str) or not cid:
            return fail("invalid_demo_summary", "claim.claim_id missing")
        by_id[cid] = c
    for rid in REQUIRED_CLAIMS:
        if rid not in by_id:
            return fail("demo_claim_missing", f"required claim '{rid}' absent")
    for rid in REQUIRED_CLAIMS:
        c = by_id[rid]
        if c.get("status") != "pass":
            return fail("demo_claim_failed", f"claim '{rid}' status != 'pass'")

    # 7. Load nested run report and transcript for cross-checks.
    nested_run_report_path = package_root / "harness-evidence/harness-run-report.json"
    nested_transcript_path = package_root / "harness-evidence/transcript.jsonl"
    nested_decisions_dir = package_root / "harness-evidence/authority-decision-reports"
    if not nested_run_report_path.exists():
        return fail("nested_harness_evidence_invalid",
                    "harness-evidence/harness-run-report.json missing")
    try:
        nested_run_report = json.loads(nested_run_report_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return fail("nested_harness_evidence_invalid",
                    f"harness-run-report.json parse error: {e}")
    if nested_run_report.get("report_type") != RUN_REPORT_TYPE:
        return fail("nested_harness_evidence_invalid",
                    "harness-run-report.json report_type mismatch")
    if not nested_transcript_path.exists():
        return fail("nested_harness_evidence_invalid",
                    "harness-evidence/transcript.jsonl missing")
    transcript = read_jsonl(nested_transcript_path)
    if transcript is None:
        return fail("nested_harness_evidence_invalid",
                    "harness-evidence/transcript.jsonl parse error")

    # 8. Cross-check every required claim against nested evidence.
    for rid in REQUIRED_CLAIMS:
        c = by_id[rid]
        result = cross_check_claim(c, package_root, transcript, nested_decisions_dir, nested_run_report)
        if result is not None:
            reason, detail = result
            return fail(reason, detail)

    # 9. Invoke v0.2.4 verifier on the nested manifest. Surface any failure
    # as nested_harness_evidence_invalid at the package level (the underlying
    # nested reason is included as context only).
    nested_manifest_path = package_root / "harness-evidence/harness-evidence-manifest.json"
    if not nested_manifest_path.exists():
        return fail("nested_harness_evidence_invalid", "nested manifest missing")
    verifier_cmd = [
        sys.executable, str(HARNESS_VERIFIER),
        "--manifest", str(nested_manifest_path),
    ]
    proc = subprocess.run(verifier_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        nested_context = (proc.stderr or proc.stdout or "").strip()
        # Extract a short nested reason if available (the v0.2.4 verifier prints
        # "FAIL: <reason>: <detail>" to stderr). We keep the package-level
        # stable reason as 'nested_harness_evidence_invalid'.
        nested_reason_summary = "nested verifier exit nonzero"
        for line in nested_context.splitlines():
            if line.startswith("FAIL:"):
                nested_reason_summary = line[len("FAIL:"):].strip()
                break
        return fail("nested_harness_evidence_invalid",
                    f"(nested context: {nested_reason_summary})")

    print(f"PASS: demo package valid ({len(subjects)} subjects, {len(REQUIRED_CLAIMS)} claims)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
