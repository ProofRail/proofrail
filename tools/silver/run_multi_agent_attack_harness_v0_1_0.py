#!/usr/bin/env python3
"""Run the ProofRail Silver v0.2.4 deterministic multi-agent attack harness.

The harness consumes a Silver Multi-Agent Harness Script v0.1.0 YAML and a
Silver Multi-Principal Authority Fixture v0.1.0 YAML, routes structured
protected-action attempts through the unchanged v0.2.3 authority evaluator,
and writes local evidence artifacts:

  <output-dir>/
    harness-script.yaml
    authority-fixture.yaml
    expected-outcomes.json
    transcript.jsonl
    protected-action-requests/<event_id>.json
    authority-decision-reports/<event_id>.json
    harness-run-report.json
    harness-evidence-manifest.json

No live agent runs, no live actuators invoked, no LLM call, no NL parsing.

Usage:
  python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \\
    --script <harness-script.yaml> \\
    --authority-fixture <authority-fixture.yaml> \\
    --output-dir <dir> \\
    [--force]

Exit codes:
  0 harness completed and all expected outcomes matched
  1 harness completed but expected outcomes failed, or script invalid
  2 usage/input error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Import the unchanged v0.2.3 authority evaluator callable.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
try:
    from evaluate_multi_principal_authority_v0_1_0 import (  # type: ignore
        evaluate_request,
        parse_iso8601 as _eval_parse_iso8601,
    )
except ImportError as e:
    print(f"ERROR: cannot import v0.2.3 evaluator: {e}", file=sys.stderr)
    sys.exit(2)


SCRIPT_TYPE = "proofrail.silver.multi_agent_harness_script"
SCRIPT_VERSION = "v0.1.0"
RUN_REPORT_TYPE = "proofrail.silver.multi_agent_harness_run_report"
RUN_REPORT_VERSION = "v0.1.0"
EVIDENCE_MANIFEST_TYPE = "proofrail.silver.multi_agent_harness_evidence_manifest"
EVIDENCE_MANIFEST_VERSION = "v0.1.0"
DECISION_REPORT_TYPE = "proofrail.silver.protected_action_decision_report"
DECISION_REPORT_VERSION = "v0.1.0"
REQUEST_TYPE = "proofrail.silver.protected_action_request"
REQUEST_VERSION = "v0.1.0"

VALID_EVENT_TYPES = {
    "agent_message",
    "protected_action_attempt",
    "bypass_attempt",
    "revocation_marker",
}

LIMITATIONS_RUN_REPORT = [
    "Local deterministic harness execution only.",
    "No live agents executed.",
    "No live actuators invoked.",
    "Not natural-language prompt parsing.",
    "Not prompt-injection detection.",
    "Not Gold certification.",
]

LIMITATIONS_MANIFEST = [
    "Local hash-based integrity evidence only.",
    "Not a signed certification artifact.",
    "Not production-grade evidence packaging.",
    "Not Gold certification.",
]


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(path: Path) -> tuple[str, int]:
    """Return (sha256_hex, size_bytes) for the given file."""
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


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def validate_script(script: Any) -> str | None:
    """Return None if valid, otherwise a stable failure reason."""
    if not isinstance(script, dict):
        return "invalid_harness_script: root must be a YAML mapping"
    if script.get("script_type") != SCRIPT_TYPE:
        return f"invalid_harness_script: script_type must be '{SCRIPT_TYPE}'"
    if script.get("script_version") != SCRIPT_VERSION:
        return f"invalid_harness_script: script_version must be '{SCRIPT_VERSION}'"
    for field in ("script_id", "authority_fixture", "description", "events", "limitations"):
        if field not in script:
            return f"invalid_harness_script: missing required field '{field}'"
    events = script.get("events")
    if not isinstance(events, list) or not events:
        return "invalid_harness_script: events must be a non-empty list"
    limitations = script.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        return "invalid_harness_script: limitations must be a non-empty list"

    seen_ids: set[str] = set()
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            return f"invalid_harness_script: events[{idx}] must be a mapping"
        for f in ("event_id", "event_type", "timestamp", "from_principal_id", "to_principal_id", "description", "expected"):
            if f not in event:
                return f"invalid_harness_script: events[{idx}] missing '{f}'"
        ev_id = event["event_id"]
        if not isinstance(ev_id, str) or not ev_id:
            return f"invalid_harness_script: events[{idx}].event_id must be a non-empty string"
        if ev_id in seen_ids:
            return f"invalid_harness_script: duplicate event_id '{ev_id}'"
        seen_ids.add(ev_id)
        ev_type = event["event_type"]
        if ev_type not in VALID_EVENT_TYPES:
            return f"invalid_harness_script: events[{idx}].event_type '{ev_type}' is not recognized"
        ts = event["timestamp"]
        if not isinstance(ts, str) or _eval_parse_iso8601(ts) is None:
            return f"invalid_harness_script: events[{idx}].timestamp is not ISO-8601"
        expected = event["expected"]
        if not isinstance(expected, dict) or "harness_outcome" not in expected:
            return f"invalid_harness_script: events[{idx}].expected.harness_outcome missing"
        if ev_type == "protected_action_attempt":
            pa = event.get("protected_action")
            if not isinstance(pa, dict) or pa.get("attempted") is not True:
                return f"invalid_harness_script: events[{idx}] protected_action_attempt requires protected_action.attempted=true"
            if "action_id" not in pa:
                return f"invalid_harness_script: events[{idx}].protected_action.action_id missing"
            tmpl = pa.get("request_template")
            if not isinstance(tmpl, dict):
                return f"invalid_harness_script: events[{idx}].protected_action.request_template missing"
            for tf in ("request_id", "requesting_principal_id", "parameters", "claimed_authority"):
                if tf not in tmpl:
                    return f"invalid_harness_script: events[{idx}].request_template missing '{tf}'"
            ca = tmpl["claimed_authority"]
            if not isinstance(ca, dict) or "grant_id" not in ca:
                return f"invalid_harness_script: events[{idx}].request_template.claimed_authority.grant_id missing"
            if "decision_status" not in expected or "decision_reason" not in expected:
                return f"invalid_harness_script: events[{idx}].expected requires decision_status and decision_reason"
        elif ev_type == "bypass_attempt":
            pa = event.get("protected_action")
            if not isinstance(pa, dict) or pa.get("attempted") is not True or pa.get("bypass_requested") is not True:
                return f"invalid_harness_script: events[{idx}] bypass_attempt requires protected_action.attempted=true and bypass_requested=true"
            if "action_id" not in pa:
                return f"invalid_harness_script: events[{idx}].protected_action.action_id missing"
            if "harness_reason" not in expected:
                return f"invalid_harness_script: events[{idx}].expected.harness_reason missing for bypass_attempt"
        elif ev_type == "revocation_marker":
            if "revocation_id" not in event:
                return f"invalid_harness_script: events[{idx}].revocation_id missing for revocation_marker"
    return None


def cross_check_fixture_references(script: dict, fixture: dict) -> str | None:
    """Validate that referenced principals and actions exist in the fixture."""
    principal_ids = {p.get("principal_id") for p in fixture.get("principals", []) if isinstance(p, dict)}
    principal_ids.add("proofrail.harness")  # allowed synthetic counterparty
    action_ids = {a.get("action_id") for a in fixture.get("protected_actions", []) if isinstance(a, dict)}
    grant_ids = {g.get("grant_id") for g in fixture.get("authority_grants", []) if isinstance(g, dict)}
    revocation_ids = {r.get("revocation_id") for r in fixture.get("revocations", []) if isinstance(r, dict)}

    for event in script["events"]:
        et = event["event_type"]
        from_p = event["from_principal_id"]
        to_p = event["to_principal_id"]
        if from_p not in principal_ids and from_p != "proofrail.harness":
            return f"unknown_principal: from_principal_id '{from_p}' not in fixture"
        if et == "protected_action_attempt":
            pa = event["protected_action"]
            action_id = pa["action_id"]
            if action_id not in action_ids:
                return f"unknown_protected_action: action_id '{action_id}' not in fixture"
            tmpl = pa["request_template"]
            req_principal = tmpl["requesting_principal_id"]
            if req_principal not in principal_ids:
                return f"unknown_principal: request_template.requesting_principal_id '{req_principal}' not in fixture"
            grant_id = tmpl["claimed_authority"]["grant_id"]
            if grant_id not in grant_ids:
                return f"unknown_authority_grant: grant '{grant_id}' not in fixture"
            # to_principal_id for protected_action_attempt is usually proofrail.harness
        elif et == "bypass_attempt":
            pa = event["protected_action"]
            if pa["action_id"] not in action_ids:
                return f"unknown_protected_action: action_id '{pa['action_id']}' not in fixture"
            # to_principal_id may be the action_id itself for bypass events (informational)
        elif et == "revocation_marker":
            if event["revocation_id"] not in revocation_ids:
                return f"unknown_revocation: revocation_id '{event['revocation_id']}' not in fixture"
        elif et == "agent_message":
            if to_p not in principal_ids:
                return f"unknown_principal: to_principal_id '{to_p}' not in fixture"
    return None


def render_request(event: dict) -> dict:
    """Render a Silver Protected Action Request JSON from an event's request_template.

    Injects request_type, request_version, and action_id (copied from
    event.protected_action.action_id) if not already present in the template.
    """
    pa = event["protected_action"]
    tmpl = pa["request_template"]
    rendered = dict(tmpl)
    rendered.setdefault("request_type", REQUEST_TYPE)
    rendered.setdefault("request_version", REQUEST_VERSION)
    rendered.setdefault("action_id", pa["action_id"])
    return rendered


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_jsonl_line(handle, obj: Any) -> None:
    handle.write(json.dumps(obj, sort_keys=True) + "\n")


def derive_expected_outcomes(script: dict) -> dict:
    """Project the script's per-event expected outcomes into a single document."""
    return {
        "document_type": "proofrail.silver.multi_agent_harness_expected_outcomes",
        "document_version": "v0.1.0",
        "script_id": script["script_id"],
        "events": [
            {
                "event_id": e["event_id"],
                "event_type": e["event_type"],
                "expected": e["expected"],
            }
            for e in script["events"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the ProofRail Silver v0.2.4 multi-agent attack harness."
    )
    parser.add_argument("--script", required=True, help="Path to harness script YAML")
    parser.add_argument("--authority-fixture", required=True, help="Path to v0.2.3 authority fixture YAML")
    parser.add_argument("--output-dir", required=True, help="Output directory for harness artifacts")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output directory")
    args = parser.parse_args()

    script_path = Path(args.script)
    fixture_path = Path(args.authority_fixture)
    output_dir = Path(args.output_dir)

    if not script_path.exists():
        err(f"script not found: {script_path}")
        return 2
    if not fixture_path.exists():
        err(f"authority fixture not found: {fixture_path}")
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

    # Load script
    try:
        script = load_yaml(script_path)
    except Exception as e:
        err(f"invalid_harness_script: failed to parse YAML: {e}")
        return 1
    script_err = validate_script(script)
    if script_err:
        err(script_err)
        return 1

    # Load fixture
    try:
        fixture = load_yaml(fixture_path)
    except Exception as e:
        err(f"invalid_authority_fixture: failed to parse YAML: {e}")
        return 1
    if not isinstance(fixture, dict):
        err("invalid_authority_fixture: root must be a YAML mapping")
        return 1
    fixture_id = fixture.get("fixture_id", "")

    # Cross-check references
    ref_err = cross_check_fixture_references(script, fixture)
    if ref_err:
        err(ref_err)
        return 1

    # Copy inputs into output dir (so manifest paths are clean intra-dir)
    script_out = output_dir / "harness-script.yaml"
    fixture_out = output_dir / "authority-fixture.yaml"
    shutil.copyfile(script_path, script_out)
    shutil.copyfile(fixture_path, fixture_out)

    # Emit derived expected-outcomes.json
    expected_out_path = output_dir / "expected-outcomes.json"
    write_json(expected_out_path, derive_expected_outcomes(script))

    requests_dir = output_dir / "protected-action-requests"
    decisions_dir = output_dir / "authority-decision-reports"
    transcript_path = output_dir / "transcript.jsonl"

    started_at = now_utc_iso()
    event_results: list[dict] = []
    summary = {
        "actions_allowed": 0,
        "actions_denied": 0,
        "bypass_attempts_blocked": 0,
        "events_failed": 0,
        "events_passed": 0,
        "events_total": 0,
        "protected_action_attempts": 0,
        "revocation_markers": 0,
        "status": "pass",
    }
    overall_status = "pass"
    fatal_violation_reason: str | None = None

    with transcript_path.open("w") as tx:
        for event in script["events"]:
            ev_id = event["event_id"]
            et = event["event_type"]
            ts = event["timestamp"]
            expected = event["expected"]
            actual: dict[str, Any] = {
                "harness_outcome": "event_failed",
                "decision_status": None,
                "decision_reason": None,
                "harness_reason": None,
            }
            request_rel: str | None = None
            decision_rel: str | None = None

            if et == "agent_message":
                actual["harness_outcome"] = "message_delivered"

            elif et == "protected_action_attempt":
                summary["protected_action_attempts"] += 1
                rendered = render_request(event)
                req_path = requests_dir / f"{ev_id}.json"
                write_json(req_path, rendered)
                request_rel = str(req_path.relative_to(output_dir))

                decision_time = _eval_parse_iso8601(ts)
                if decision_time is None:
                    err(f"authority_evaluator_failed: cannot parse timestamp '{ts}'")
                    return 1
                if decision_time.tzinfo is None:
                    decision_time = decision_time.replace(tzinfo=timezone.utc)

                try:
                    report = evaluate_request(fixture, rendered, decision_time)
                except Exception as e:
                    err(f"authority_evaluator_failed: {e}")
                    return 1

                if not isinstance(report, dict):
                    err("authority_evaluator_failed: evaluator did not return a mapping")
                    return 1

                # Enforce non-execution invariant on the decision report
                execution = report.get("execution", {})
                if not (isinstance(execution, dict) and execution.get("performed") is False):
                    err(f"decision_report_execution_violation: event '{ev_id}'")
                    fatal_violation_reason = "decision_report_execution_violation"
                    overall_status = "fail"

                dec_path = decisions_dir / f"{ev_id}.json"
                write_json(dec_path, report)
                decision_rel = str(dec_path.relative_to(output_dir))

                decision = report.get("decision", {})
                ds = decision.get("status")
                dr = decision.get("reason")
                actual["decision_status"] = ds
                actual["decision_reason"] = dr
                if ds == "allow":
                    actual["harness_outcome"] = "action_allowed"
                    summary["actions_allowed"] += 1
                elif ds == "deny":
                    actual["harness_outcome"] = "action_denied"
                    summary["actions_denied"] += 1
                else:
                    actual["harness_outcome"] = "event_failed"

            elif et == "bypass_attempt":
                actual["harness_outcome"] = "bypass_blocked"
                actual["harness_reason"] = "bypass_attempt_detected"
                summary["bypass_attempts_blocked"] += 1

            elif et == "revocation_marker":
                actual["harness_outcome"] = "revocation_marked"
                summary["revocation_markers"] += 1

            # Decide match
            match = (actual["harness_outcome"] == expected.get("harness_outcome"))
            if et == "protected_action_attempt":
                if expected.get("decision_status") != actual["decision_status"]:
                    match = False
                if expected.get("decision_reason") != actual["decision_reason"]:
                    match = False
            elif et == "bypass_attempt":
                if expected.get("harness_reason") != actual["harness_reason"]:
                    match = False

            if match:
                summary["events_passed"] += 1
            else:
                summary["events_failed"] += 1
                overall_status = "fail"

            summary["events_total"] += 1

            # Transcript
            tx_record = {
                "event_id": ev_id,
                "event_type": et,
                "timestamp": ts,
                "from_principal_id": event["from_principal_id"],
                "to_principal_id": event["to_principal_id"],
                "actual": actual,
                "expected": expected,
                "match": match,
                "outputs": {
                    "request_path": request_rel,
                    "decision_report_path": decision_rel,
                },
            }
            if et == "revocation_marker":
                tx_record["revocation_id"] = event["revocation_id"]
            if et == "bypass_attempt":
                tx_record["bypass_evidence"] = {
                    "from_principal_id": event["from_principal_id"],
                    "attempted_action_id": event["protected_action"]["action_id"],
                    "bypass_requested": True,
                    "harness_reason": "bypass_attempt_detected",
                }
            write_jsonl_line(tx, tx_record)

            event_results.append({
                "event_id": ev_id,
                "event_type": et,
                "timestamp": ts,
                "from_principal_id": event["from_principal_id"],
                "to_principal_id": event["to_principal_id"],
                "actual": actual,
                "expected": expected,
                "match": match,
                "outputs": {
                    "request_path": request_rel,
                    "decision_report_path": decision_rel,
                },
            })

    summary["status"] = overall_status

    run_report = {
        "report_type": RUN_REPORT_TYPE,
        "report_version": RUN_REPORT_VERSION,
        "script_id": script["script_id"],
        "authority_fixture_id": fixture_id,
        "started_at": started_at,
        "completed_at": now_utc_iso(),
        "summary": summary,
        "event_results": event_results,
        "outputs": {
            "transcript_path": "transcript.jsonl",
            "requests_dir": "protected-action-requests",
            "decision_reports_dir": "authority-decision-reports",
            "expected_outcomes_path": "expected-outcomes.json",
        },
        "execution": {
            "protected_actions_performed": False,
            "reason": "harness_decision_only",
        },
        "limitations": list(LIMITATIONS_RUN_REPORT),
    }
    run_report_path = output_dir / "harness-run-report.json"
    write_json(run_report_path, run_report)

    # Build evidence manifest. Subject ordering is deterministic:
    # 1. harness_script, 2. authority_fixture, 3. expected_outcomes,
    # 4. transcript, 5. protected_action_request (sorted), 6. authority_decision_report (sorted),
    # 7. harness_run_report.
    subjects: list[dict] = []

    def add_subject(subject_type: str, path: Path) -> None:
        digest, size = sha256_hex(path)
        subjects.append({
            "subject_type": subject_type,
            "path": str(path.relative_to(output_dir)),
            "sha256": f"sha256:{digest}",
            "size_bytes": size,
        })

    add_subject("harness_script", script_out)
    add_subject("authority_fixture", fixture_out)
    add_subject("expected_outcomes", expected_out_path)
    add_subject("transcript", transcript_path)
    if requests_dir.exists():
        for p in sorted(requests_dir.iterdir(), key=lambda x: x.name):
            if p.is_file():
                add_subject("protected_action_request", p)
    if decisions_dir.exists():
        for p in sorted(decisions_dir.iterdir(), key=lambda x: x.name):
            if p.is_file():
                add_subject("authority_decision_report", p)
    add_subject("harness_run_report", run_report_path)

    manifest = {
        "manifest_type": EVIDENCE_MANIFEST_TYPE,
        "manifest_version": EVIDENCE_MANIFEST_VERSION,
        "script_id": script["script_id"],
        "generated_by": "tools/silver/run_multi_agent_attack_harness_v0_1_0.py",
        "generated_at": now_utc_iso(),
        "hash_algorithm": "sha256",
        "subjects": subjects,
        "limitations": list(LIMITATIONS_MANIFEST),
    }
    manifest_path = output_dir / "harness-evidence-manifest.json"
    write_json(manifest_path, manifest)

    print(f"Harness completed: status={overall_status} events={summary['events_total']} passed={summary['events_passed']} failed={summary['events_failed']}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest: {manifest_path}")
    if fatal_violation_reason:
        return 1
    return 0 if overall_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
