#!/usr/bin/env python3
"""Package the ProofRail Silver v0.2.5 multi-agent trust-boundary demo.

The packager invokes the unchanged v0.2.4 harness runner and verifier as
subprocesses, then assembles a small, inspectable demo package:

  <output-dir>/
    README.md
    demo-walkthrough.md
    demo-summary.json
    demo-package-manifest.json
    harness-evidence/
      ...v0.2.4 harness output...
      harness-evidence-manifest.json

No live agent runs, no live actuators invoked, no LLM call, no NL parsing.

Usage:
  python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py \\
    --demo-root demos/silver-demo-003-multi-agent-trust-boundary \\
    --harness-script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \\
    --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \\
    --output-dir /tmp/proofrail-silver-multi-agent-demo-v0.2.5 \\
    [--generated-at 2026-06-21T12:30:01Z] \\
    [--force]

Exit codes:
  0 package generated and self-verified
  1 packaging failed (nested verification, derivation, or path traversal)
  2 usage/input error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_RUNNER = REPO_ROOT / "tools/silver/run_multi_agent_attack_harness_v0_1_0.py"
HARNESS_VERIFIER = REPO_ROOT / "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py"

PACKAGE_MANIFEST_TYPE = "proofrail.silver.multi_agent_demo_package_manifest"
PACKAGE_MANIFEST_VERSION = "v0.1.0"
SUMMARY_TYPE = "proofrail.silver.multi_agent_demo_summary"
SUMMARY_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.5"
DEMO_ID = "proofrail-silver-demo-003-multi-agent-trust-boundary"

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

CLAIM_DESCRIPTIONS = {
    "harmless_messages_proceed":
        "Harmless agent-to-agent messages do not invoke protected actions.",
    "protected_actions_require_scoped_authority":
        "Protected actions reach 'allow' only when a scoped grant matches.",
    "unauthorized_delegation_fails":
        "A grant whose subject is one principal cannot be wielded by another.",
    "bypass_attempts_blocked":
        "Bypass attempts outside the controlled path are recorded and not silently allowed.",
    "revoked_authority_fails":
        "After a revocation point, the formerly-valid grant no longer satisfies authority.",
    "out_of_scope_actions_fail":
        "An action outside a grant's declared scope is denied.",
    "evidence_is_hash_verifiable":
        "The nested v0.2.4 harness evidence manifest passes the v0.2.4 verifier.",
    "no_protected_actions_executed":
        "The demo never executes a protected action.",
}

LIMITATIONS_PACKAGE_MANIFEST = [
    "Local hash-based integrity evidence only.",
    "Not a signed certification artifact.",
    "Not Bronze, Silver Signed Bundle Assertion, or Verifier Output Attestation evidence.",
    "Not production-grade evidence packaging.",
    "Not Gold certification.",
]

LIMITATIONS_SUMMARY = [
    "Local deterministic demo summary only.",
    "Derived from v0.2.4 multi-agent harness evidence.",
    "No live agents executed.",
    "No live actuators invoked.",
    "Not natural-language prompt parsing.",
    "Not prompt-injection detection.",
    "Not Gold certification.",
]


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_of_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def has_traversal(rel: str) -> bool:
    parts = Path(rel).parts
    return ".." in parts or rel.startswith("/")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def derive_claims(
    harness_dir: Path,
    run_report: dict,
    transcript: list[dict],
) -> tuple[list[dict], str | None]:
    """Derive the eight required claims from the v0.2.4 nested evidence.

    Returns (claims, error_reason). claims is the list of claim entries.
    error_reason is None on success, otherwise a stable string explaining
    which claim could not be derived (the package as a whole must fail).
    """
    # Index transcript by event_id and event_type.
    by_id: dict[str, dict] = {r["event_id"]: r for r in transcript if "event_id" in r}

    agent_message_events = [
        r for r in transcript
        if r.get("event_type") == "agent_message"
        and isinstance(r.get("actual"), dict)
        and r["actual"].get("harness_outcome") == "message_delivered"
    ]
    bypass_events = [
        r for r in transcript
        if r.get("event_type") == "bypass_attempt"
        and isinstance(r.get("actual"), dict)
        and r["actual"].get("harness_outcome") == "bypass_blocked"
        and r["actual"].get("harness_reason") == "bypass_attempt_detected"
    ]
    revocation_markers = [
        r for r in transcript
        if r.get("event_type") == "revocation_marker"
        and isinstance(r.get("actual"), dict)
        and r["actual"].get("harness_outcome") == "revocation_marked"
    ]

    # Walk the on-disk decision reports.
    decision_reports_dir = harness_dir / "authority-decision-reports"
    decision_files: list[Path] = []
    if decision_reports_dir.exists():
        decision_files = sorted(
            (p for p in decision_reports_dir.iterdir() if p.is_file() and p.suffix == ".json"),
            key=lambda p: p.name,
        )

    allow_refs: list[dict] = []
    subject_mismatch_refs: list[dict] = []
    constraint_refs: list[dict] = []
    revoked_refs: list[dict] = []
    all_execution_false = True
    for dpath in decision_files:
        try:
            dr = json.loads(dpath.read_text())
        except json.JSONDecodeError:
            return [], f"decision_report_invalid:{dpath.name}"
        decision = dr.get("decision", {}) if isinstance(dr.get("decision"), dict) else {}
        execution = dr.get("execution", {}) if isinstance(dr.get("execution"), dict) else {}
        if execution.get("performed") is not False:
            all_execution_false = False
        rel_path = "harness-evidence/authority-decision-reports/" + dpath.name
        event_id = dpath.stem
        ref = {"artifact": rel_path, "event_id": event_id}
        if decision.get("status") == "allow":
            allow_refs.append(ref)
        elif decision.get("status") == "deny":
            reason = decision.get("reason")
            if reason == "authority_subject_mismatch":
                subject_mismatch_refs.append(ref)
            elif reason == "constraint_not_satisfied":
                constraint_refs.append(ref)
            elif reason == "authority_revoked":
                revoked_refs.append(ref)

    claims: list[dict] = []

    # 1. harmless_messages_proceed
    if not agent_message_events:
        return [], "harmless_messages_proceed: no qualifying agent_message event"
    claims.append({
        "claim_id": "harmless_messages_proceed",
        "description": CLAIM_DESCRIPTIONS["harmless_messages_proceed"],
        "status": "pass",
        "evidence_refs": [
            {"artifact": "harness-evidence/transcript.jsonl", "event_id": e["event_id"]}
            for e in agent_message_events
        ],
    })

    # 2. protected_actions_require_scoped_authority
    if not allow_refs:
        return [], "protected_actions_require_scoped_authority: no allow decision report"
    claims.append({
        "claim_id": "protected_actions_require_scoped_authority",
        "description": CLAIM_DESCRIPTIONS["protected_actions_require_scoped_authority"],
        "status": "pass",
        "evidence_refs": list(allow_refs),
    })

    # 3. unauthorized_delegation_fails
    if not subject_mismatch_refs:
        return [], "unauthorized_delegation_fails: no authority_subject_mismatch decision report"
    claims.append({
        "claim_id": "unauthorized_delegation_fails",
        "description": CLAIM_DESCRIPTIONS["unauthorized_delegation_fails"],
        "status": "pass",
        "evidence_refs": list(subject_mismatch_refs),
    })

    # 4. bypass_attempts_blocked
    if not bypass_events:
        return [], "bypass_attempts_blocked: no qualifying bypass_attempt event"
    claims.append({
        "claim_id": "bypass_attempts_blocked",
        "description": CLAIM_DESCRIPTIONS["bypass_attempts_blocked"],
        "status": "pass",
        "evidence_refs": [
            {"artifact": "harness-evidence/transcript.jsonl", "event_id": e["event_id"]}
            for e in bypass_events
        ],
    })

    # 5. revoked_authority_fails (marker + later denial)
    if not revocation_markers or not revoked_refs:
        return [], "revoked_authority_fails: missing revocation marker or authority_revoked decision"
    revoked_evidence: list[dict] = [
        {"artifact": "harness-evidence/transcript.jsonl", "event_id": m["event_id"]}
        for m in revocation_markers
    ]
    revoked_evidence.extend(revoked_refs)
    claims.append({
        "claim_id": "revoked_authority_fails",
        "description": CLAIM_DESCRIPTIONS["revoked_authority_fails"],
        "status": "pass",
        "evidence_refs": revoked_evidence,
    })

    # 6. out_of_scope_actions_fail
    if not constraint_refs:
        return [], "out_of_scope_actions_fail: no constraint_not_satisfied decision report"
    claims.append({
        "claim_id": "out_of_scope_actions_fail",
        "description": CLAIM_DESCRIPTIONS["out_of_scope_actions_fail"],
        "status": "pass",
        "evidence_refs": list(constraint_refs),
    })

    # 7. evidence_is_hash_verifiable (set after nested verifier returns 0)
    claims.append({
        "claim_id": "evidence_is_hash_verifiable",
        "description": CLAIM_DESCRIPTIONS["evidence_is_hash_verifiable"],
        "status": "pass",
        "evidence_refs": [
            {"artifact": "harness-evidence/harness-evidence-manifest.json"}
        ],
    })

    # 8. no_protected_actions_executed
    run_exec = run_report.get("execution", {}) if isinstance(run_report.get("execution"), dict) else {}
    if run_exec.get("protected_actions_performed") is not False:
        return [], "no_protected_actions_executed: run report execution.protected_actions_performed is not false"
    if not all_execution_false:
        return [], "no_protected_actions_executed: a decision report has execution.performed != false"
    claims.append({
        "claim_id": "no_protected_actions_executed",
        "description": CLAIM_DESCRIPTIONS["no_protected_actions_executed"],
        "status": "pass",
        "evidence_refs": [
            {"artifact": "harness-evidence/harness-run-report.json"}
        ],
    })

    # Sanity: every required claim present.
    seen = {c["claim_id"] for c in claims}
    for cid in REQUIRED_CLAIMS:
        if cid not in seen:
            return [], f"missing_required_claim:{cid}"

    return claims, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package the ProofRail Silver v0.2.5 multi-agent trust-boundary demo."
    )
    parser.add_argument("--demo-root", required=True,
                        help="Path to the committed demo directory (source of README.md and demo-walkthrough.md).")
    parser.add_argument("--harness-script", required=True,
                        help="Path to the v0.2.4 harness script YAML.")
    parser.add_argument("--authority-fixture", required=True,
                        help="Path to the v0.2.3 authority fixture YAML.")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory for the assembled demo package.")
    parser.add_argument("--generated-at", default=None,
                        help="Optional ISO-8601 UTC timestamp to embed in manifests (default: now).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite the output directory if it exists.")
    args = parser.parse_args()

    demo_root = Path(args.demo_root)
    script_path = Path(args.harness_script)
    fixture_path = Path(args.authority_fixture)
    output_dir = Path(args.output_dir)

    if not demo_root.exists() or not demo_root.is_dir():
        err(f"demo_root not found or not a directory: {demo_root}")
        return 2
    src_readme = demo_root / "README.md"
    src_walkthrough = demo_root / "demo-walkthrough.md"
    if not src_readme.exists():
        err(f"demo_root missing README.md: {src_readme}")
        return 2
    if not src_walkthrough.exists():
        err(f"demo_root missing demo-walkthrough.md: {src_walkthrough}")
        return 2
    if not script_path.exists():
        err(f"harness-script not found: {script_path}")
        return 2
    if not fixture_path.exists():
        err(f"authority-fixture not found: {fixture_path}")
        return 2
    if not HARNESS_RUNNER.exists() or not HARNESS_VERIFIER.exists():
        err("v0.2.4 harness runner or verifier missing under tools/silver/")
        return 2

    if output_dir.exists():
        if not args.force:
            err(f"output_exists_without_force: {output_dir}")
            return 1
        if output_dir.is_dir():
            shutil.rmtree(output_dir)
        else:
            output_dir.unlink()
    output_dir.mkdir(parents=True, exist_ok=False)

    generated_at = args.generated_at or now_utc_iso()
    if not isinstance(generated_at, str) or not generated_at:
        err("invalid --generated-at value")
        return 2

    # Step 1: Run the unchanged v0.2.4 harness runner into <output-dir>/harness-evidence/.
    harness_dir = output_dir / "harness-evidence"
    runner_cmd = [
        sys.executable, str(HARNESS_RUNNER),
        "--script", str(script_path),
        "--authority-fixture", str(fixture_path),
        "--output-dir", str(harness_dir),
        "--force",
    ]
    runner_proc = subprocess.run(runner_cmd, capture_output=True, text=True)
    if runner_proc.returncode != 0:
        err("nested_harness_run_failed: v0.2.4 harness runner exited non-zero")
        if runner_proc.stdout:
            sys.stderr.write(runner_proc.stdout)
        if runner_proc.stderr:
            sys.stderr.write(runner_proc.stderr)
        return 1
    nested_manifest = harness_dir / "harness-evidence-manifest.json"
    if not nested_manifest.exists():
        err("nested_harness_run_failed: harness-evidence-manifest.json not produced")
        return 1

    # Step 2: Verify the nested manifest with the unchanged v0.2.4 verifier.
    verifier_cmd = [
        sys.executable, str(HARNESS_VERIFIER),
        "--manifest", str(nested_manifest),
    ]
    verifier_proc = subprocess.run(verifier_cmd, capture_output=True, text=True)
    if verifier_proc.returncode != 0:
        err("nested_harness_evidence_invalid: v0.2.4 verifier rejected the nested manifest")
        if verifier_proc.stdout:
            sys.stderr.write(verifier_proc.stdout)
        if verifier_proc.stderr:
            sys.stderr.write(verifier_proc.stderr)
        return 1

    # Step 3: Load the nested run report and transcript for derivation.
    run_report_path = harness_dir / "harness-run-report.json"
    transcript_path = harness_dir / "transcript.jsonl"
    if not run_report_path.exists() or not transcript_path.exists():
        err("nested_harness_evidence_invalid: missing harness-run-report.json or transcript.jsonl")
        return 1
    try:
        run_report = json.loads(run_report_path.read_text())
    except json.JSONDecodeError as e:
        err(f"nested_harness_evidence_invalid: harness-run-report.json: {e}")
        return 1
    try:
        transcript = read_jsonl(transcript_path)
    except json.JSONDecodeError as e:
        err(f"nested_harness_evidence_invalid: transcript.jsonl: {e}")
        return 1
    harness_script_id = run_report.get("script_id", "")

    # Step 4: Copy README.md and demo-walkthrough.md into the output directory.
    dst_readme = output_dir / "README.md"
    dst_walkthrough = output_dir / "demo-walkthrough.md"
    shutil.copyfile(src_readme, dst_readme)
    shutil.copyfile(src_walkthrough, dst_walkthrough)

    # Step 5: Derive the eight claims.
    claims, derive_err = derive_claims(harness_dir, run_report, transcript)
    if derive_err is not None:
        err(f"demo_claim_derivation_failed: {derive_err}")
        return 1

    # Sanity: every evidence_ref path is package-local (no '..', not absolute).
    for c in claims:
        for ref in c.get("evidence_refs", []):
            art = ref.get("artifact", "")
            if not isinstance(art, str) or not art or has_traversal(art):
                err(f"demo_evidence_ref_invalid: claim '{c['claim_id']}' artifact '{art}'")
                return 1
            target = output_dir / art
            if not target.exists():
                err(f"demo_evidence_ref_invalid: claim '{c['claim_id']}' artifact '{art}' not found")
                return 1

    # Step 6: Emit demo-summary.json.
    summary_obj = {
        "document_type": SUMMARY_TYPE,
        "schema_version": SUMMARY_VERSION,
        "demo_id": DEMO_ID,
        "proofrail_release": PROOFRAIL_RELEASE,
        "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
        "generated_at": generated_at,
        "source_harness": {
            "harness_release": "v0.2.4",
            "harness_script_id": harness_script_id,
            "harness_manifest_path": "harness-evidence/harness-evidence-manifest.json",
            "harness_run_report_path": "harness-evidence/harness-run-report.json",
        },
        "claims": claims,
        "execution": {
            "protected_actions_performed": False,
            "reason": "demo_evidence_only",
        },
        "limitations": list(LIMITATIONS_SUMMARY),
    }
    summary_path = output_dir / "demo-summary.json"
    write_json(summary_path, summary_obj)

    # Step 7: Build the package manifest subjects.
    def subject(role: str, path: Path) -> dict:
        rel = str(path.relative_to(output_dir))
        if has_traversal(rel):
            err(f"demo_subject_path_traversal: '{rel}'")
            raise SystemExit(1)
        digest, size = sha256_of_file(path)
        return {
            "role": role,
            "path": rel,
            "sha256": f"sha256:{digest}",
            "size_bytes": size,
        }

    subjects = [
        subject("demo_readme", dst_readme),
        subject("demo_walkthrough", dst_walkthrough),
        subject("demo_summary", summary_path),
        subject("nested_harness_evidence_manifest", nested_manifest),
    ]

    package_manifest = {
        "document_type": PACKAGE_MANIFEST_TYPE,
        "schema_version": PACKAGE_MANIFEST_VERSION,
        "demo_id": DEMO_ID,
        "proofrail_release": PROOFRAIL_RELEASE,
        "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
        "generated_at": generated_at,
        "package_root": ".",
        "hash_algorithm": "sha256",
        "subjects": subjects,
        "nested_verification": {
            "harness_evidence_verified": True,
            "verifier": "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py",
            "nested_manifest_path": "harness-evidence/harness-evidence-manifest.json",
        },
        "limitations": list(LIMITATIONS_PACKAGE_MANIFEST),
    }
    package_manifest_path = output_dir / "demo-package-manifest.json"
    write_json(package_manifest_path, package_manifest)

    print(f"Package generated: {output_dir}")
    print(f"Demo summary:      {summary_path}")
    print(f"Package manifest:  {package_manifest_path}")
    print(f"Nested manifest:   {nested_manifest}")
    print(f"Claims emitted:    {len(claims)} (all 'pass')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
