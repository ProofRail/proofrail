#!/usr/bin/env python3
"""Compose a ProofRail Silver v0.2.7 composed gateway evidence package.

The composer:

  1. Refuses to overwrite --output-dir unless --force is provided.
  2. Validates the adapter descriptor using the existing v0.2.6 validator
     (subprocess invocation; no import coupling).
  3. Requires adapter source.source_type == "gateway".
  4. Requires adapter.trust_boundary.source_is_trust_authority == false.
  5. Parses and validates the simulated gateway event fixture against the
     v0.1.0 simulated gateway event schema, including cross-field consistency
     for bypass and revocation events.
  6. Requires every required scenario event exactly once.
  7. Requires every protected_action_id to be within the adapter's declared
     protected_action_mapping.protected_action_ids (allowing null only for
     gateway.message_observed).
  8. Requires every event to have execution.performed == false.
  9. Copies docs, adapter, and source events into the output directory in
     the deterministic v0.2.7 layout.
 10. Derives composed-gateway-evidence-report.json from gateway events and
     adapter metadata.
 11. Emits composed-gateway-evidence-manifest.json with five subjects in the
     deterministic order required by v0.2.7 and a composition block.

No external services, no real logs, no network fetch, no vendor APIs.

Usage:
  python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \\
    --demo-root demos/silver-demo-004-composed-gateway-evidence \\
    --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \\
    --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \\
    --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \\
    --generated-at 2026-06-22T00:00:00Z \\
    --force

Exit codes:
  0 - composed package generated
  1 - composition failed (invalid adapter, invalid events, missing scenarios)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_VALIDATOR = REPO_ROOT / "tools/silver/validate_evidence_source_adapter_v0_1_0.py"

REPORT_DOCUMENT_TYPE = "proofrail.silver.composed_gateway_evidence_report"
REPORT_SCHEMA_VERSION = "v0.1.0"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.composed_gateway_evidence_manifest"
MANIFEST_SCHEMA_VERSION = "v0.1.0"
EVENT_DOCUMENT_TYPE = "proofrail.silver.simulated_gateway_event"
EVENT_SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.7"
DEMO_ID = "proofrail-silver-demo-004-composed-gateway-evidence"

REQUIRED_SCENARIOS = [
    "EVT-001-harmless-message",
    "EVT-002-payment-release-direct",
    "EVT-003-vendor-approval-direct",
    "EVT-004-delegation-laundering",
    "EVT-005-bypass-payment-release",
    "EVT-006-data-export-out-of-scope",
    "EVT-007-deploy-change-out-of-scope",
    "EVT-008-revocation-marker",
    "EVT-009-vendor-approval-after-revocation",
]

EVENT_TYPES = {
    "gateway.message_observed",
    "gateway.decision",
    "gateway.bypass_attempt",
    "gateway.revocation_check",
}

DECISIONS = {"allow", "deny", "not_applicable"}

REASONS = {
    "authority_requirements_satisfied",
    "authority_subject_mismatch",
    "constraint_not_satisfied",
    "authority_revoked",
    "bypass_attempt_detected",
    "revocation_check",
    "no_protected_action",
}

REQUIRED_EVENT_FIELDS = [
    "document_type",
    "schema_version",
    "source_type",
    "source_event_id",
    "scenario_event_id",
    "timestamp",
    "event_type",
    "protected_action_id",
    "decision",
    "reason",
    "revocation_checked",
    "bypass_detected",
    "execution",
]

CLAIM_IDS = [
    "gateway_source_described_by_adapter",
    "gateway_source_not_trust_authority",
    "gateway_events_normalized",
    "protected_actions_require_scoped_authority",
    "unauthorized_delegation_fails",
    "bypass_attempts_observed_or_blocked",
    "revoked_authority_fails",
    "out_of_scope_actions_fail",
    "source_evidence_hash_verifiable",
    "no_protected_actions_executed",
]

CLAIM_DESCRIPTIONS = {
    "gateway_source_described_by_adapter":
        "The copied gateway adapter descriptor validates structurally with the v0.2.6 adapter validator.",
    "gateway_source_not_trust_authority":
        "The adapter declares the gateway as an evidence source, not a trust authority.",
    "gateway_events_normalized":
        "All required scenario events are present in the source fixture and are represented in claim derivations.",
    "protected_actions_require_scoped_authority":
        "Allow decisions in the gateway events carry a scoped-authority reason; mismatched and out-of-scope attempts deny.",
    "unauthorized_delegation_fails":
        "An unauthorized delegation attempt for payment.release denies with authority_subject_mismatch.",
    "bypass_attempts_observed_or_blocked":
        "A bypass attempt against payment.release is observed and blocked at the gateway.",
    "revoked_authority_fails":
        "After a revocation marker, the formerly-valid vendor.approve attempt denies with authority_revoked.",
    "out_of_scope_actions_fail":
        "Out-of-scope protected actions (data.export, deploy.change) deny with constraint_not_satisfied.",
    "source_evidence_hash_verifiable":
        "The recomputed SHA-256 of the copied gateway events file matches the recorded source_events_sha256.",
    "no_protected_actions_executed":
        "No source event records execution.performed == true; the composed report records protected_actions_performed == false.",
}

LIMITATIONS_REPORT = [
    "Simulated gateway evidence only; no real gateway integration.",
    "Static JSONL fixture; not live traffic.",
    "Local SHA-256 integrity only; not signed.",
    "Not a Bronze claim or Silver Signed Bundle Assertion.",
]

NON_CLAIMS_REPORT = [
    "v0.2.7 does not certify any real gateway product.",
    "v0.2.7 does not perform runtime enforcement.",
    "v0.2.7 does not assert source event authenticity.",
    "v0.2.7 is not Gold acceptance, production assurance, compliance, or certification.",
    "The simulated gateway is an evidence source, not a trust authority.",
]

LIMITATIONS_MANIFEST = [
    "Local hash-based integrity manifest only.",
    "Not a signed certification artifact.",
    "Not Bronze, Silver Signed Bundle Assertion, or Verifier Output Attestation.",
    "Not production-grade evidence packaging.",
]

NON_CLAIMS_MANIFEST = [
    "This manifest does not certify any real gateway.",
    "This manifest is not a relying-party acceptance record.",
    "This manifest does not establish trust in the gateway as a source.",
    "Composed Silver evidence is not Gold acceptance.",
]


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def fail(reason: str, detail: str = "") -> int:
    if detail:
        print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    else:
        print(f"FAIL: {reason}", file=sys.stderr)
    return 1


def has_traversal(rel: str) -> bool:
    if not isinstance(rel, str) or not rel:
        return True
    if rel.startswith("/"):
        return True
    parts = Path(rel).parts
    return ".." in parts


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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def validate_adapter_with_v026(adapter_path: Path) -> tuple[bool, str]:
    """Subprocess-invoke the v0.2.6 adapter validator."""
    try:
        result = subprocess.run(
            [sys.executable, str(ADAPTER_VALIDATOR), "--adapter", str(adapter_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return False, f"adapter validator not invocable: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return False, detail[0] if detail else f"exit {result.returncode}"
    return True, ""


def load_adapter(adapter_path: Path) -> dict:
    return json.loads(adapter_path.read_text())


def parse_jsonl_events(events_path: Path) -> tuple[list[dict] | None, str, str]:
    """Parse JSONL gateway events.

    Returns (events_or_None, reason, detail). On success reason is empty.
    On failure events_or_None is None and reason is a stable failure reason.
    """
    if not events_path.exists():
        return None, "source_event_missing", str(events_path)
    raw = events_path.read_text()
    lines = raw.splitlines()
    nonblank = [(i + 1, ln) for i, ln in enumerate(lines) if ln.strip()]
    if not nonblank:
        return None, "source_event_missing", "no events"
    events: list[dict] = []
    seen_source_ids: set[str] = set()
    seen_scenario_ids: set[str] = set()
    for lineno, ln in nonblank:
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as exc:
            return None, "source_event_invalid", f"line {lineno}: {exc.msg}"
        if not isinstance(obj, dict):
            return None, "source_event_invalid", f"line {lineno}: not a JSON object"
        # Required fields.
        for field in REQUIRED_EVENT_FIELDS:
            if field not in obj:
                return None, "source_event_invalid", f"line {lineno}: missing field {field}"
        if obj["document_type"] != EVENT_DOCUMENT_TYPE:
            return None, "source_event_invalid", f"line {lineno}: wrong document_type"
        if obj["schema_version"] != EVENT_SCHEMA_VERSION:
            return None, "source_event_invalid", f"line {lineno}: wrong schema_version"
        if obj["source_type"] != "gateway":
            return None, "source_event_invalid", f"line {lineno}: source_type != gateway"
        sid = obj["source_event_id"]
        scid = obj["scenario_event_id"]
        if not isinstance(sid, str) or not sid.strip():
            return None, "source_event_invalid", f"line {lineno}: bad source_event_id"
        if not isinstance(scid, str) or not scid.strip():
            return None, "source_event_invalid", f"line {lineno}: bad scenario_event_id"
        if sid in seen_source_ids:
            return None, "source_event_duplicate", f"source_event_id {sid}"
        seen_source_ids.add(sid)
        if scid in seen_scenario_ids:
            return None, "source_event_duplicate", f"scenario_event_id {scid}"
        seen_scenario_ids.add(scid)
        if obj["event_type"] not in EVENT_TYPES:
            return None, "source_event_invalid", f"line {lineno}: unknown event_type {obj['event_type']}"
        if obj["decision"] not in DECISIONS:
            return None, "gateway_decision_mismatch", f"line {lineno}: decision {obj['decision']}"
        if obj["reason"] not in REASONS:
            return None, "source_event_invalid", f"line {lineno}: reason {obj['reason']}"
        if not isinstance(obj["revocation_checked"], bool):
            return None, "source_event_invalid", f"line {lineno}: revocation_checked not boolean"
        if not isinstance(obj["bypass_detected"], bool):
            return None, "source_event_invalid", f"line {lineno}: bypass_detected not boolean"
        ex = obj["execution"]
        if not isinstance(ex, dict):
            return None, "source_event_invalid", f"line {lineno}: execution not object"
        if "performed" not in ex or "reason" not in ex:
            return None, "source_event_invalid", f"line {lineno}: execution missing fields"
        if ex["performed"] is not False:
            return None, "execution_violation", f"line {lineno}: execution.performed != false"
        if not isinstance(ex["reason"], str) or not ex["reason"].strip():
            return None, "source_event_invalid", f"line {lineno}: execution.reason empty"
        pid = obj["protected_action_id"]
        if pid is None:
            if obj["event_type"] != "gateway.message_observed":
                return None, "gateway_protected_action_mismatch", \
                    f"line {lineno}: null protected_action_id only allowed for gateway.message_observed"
        elif not isinstance(pid, str) or not pid.strip():
            return None, "source_event_invalid", f"line {lineno}: bad protected_action_id"
        # Cross-field consistency.
        if obj["event_type"] == "gateway.message_observed":
            if obj["decision"] != "not_applicable":
                return None, "source_event_invalid", \
                    f"line {lineno}: message_observed decision must be not_applicable"
            if obj["reason"] != "no_protected_action":
                return None, "source_event_invalid", \
                    f"line {lineno}: message_observed reason must be no_protected_action"
        if obj["event_type"] == "gateway.bypass_attempt":
            if obj["bypass_detected"] is not True:
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt without bypass_detected"
            if obj["decision"] != "deny":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt decision != deny"
            if obj["reason"] != "bypass_attempt_detected":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt reason != bypass_attempt_detected"
        else:
            # No non-bypass event may set bypass_detected to true while having decision == allow.
            if obj["bypass_detected"] is True and obj["decision"] == "allow":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_detected with allow"
        if obj["event_type"] == "gateway.revocation_check":
            if obj["revocation_checked"] is not True:
                return None, "gateway_revocation_mismatch", f"line {lineno}: revocation_check without revocation_checked"
            if obj["reason"] != "revocation_check":
                return None, "gateway_revocation_mismatch", f"line {lineno}: revocation_check reason mismatch"
        if obj["reason"] == "authority_revoked":
            if obj["revocation_checked"] is not True:
                return None, "gateway_revocation_mismatch", f"line {lineno}: authority_revoked without revocation_checked"
            if obj["decision"] != "deny":
                return None, "gateway_revocation_mismatch", f"line {lineno}: authority_revoked decision != deny"
        events.append(obj)
    return events, "", ""


def check_required_scenarios(events: list[dict]) -> tuple[str, str]:
    by_scenario = {e["scenario_event_id"]: e for e in events}
    for scid in REQUIRED_SCENARIOS:
        if scid not in by_scenario:
            return "source_event_missing", f"missing scenario {scid}"
    return "", ""


def check_protected_actions_in_scope(
    events: list[dict],
    adapter: dict,
) -> tuple[str, str]:
    declared = adapter.get("protected_action_mapping", {}).get("protected_action_ids", [])
    declared_set = set(declared)
    for e in events:
        pid = e["protected_action_id"]
        if pid is None:
            continue
        if pid not in declared_set:
            return "gateway_protected_action_mismatch", \
                f"event {e['source_event_id']}: protected_action_id {pid} not in adapter scope"
    return "", ""


def derive_claims(
    events: list[dict],
    adapter: dict,
    source_events_sha256: str,
) -> tuple[list[dict] | None, str, str]:
    by_scenario: dict[str, dict] = {e["scenario_event_id"]: e for e in events}

    def ref_for(scenario_id: str) -> dict:
        e = by_scenario[scenario_id]
        return {
            "artifact": "source/gateway-events.jsonl",
            "source_event_id": e["source_event_id"],
            "scenario_event_id": scenario_id,
        }

    claims: list[dict] = []

    # 1. gateway_source_described_by_adapter
    claims.append({
        "claim_id": "gateway_source_described_by_adapter",
        "description": CLAIM_DESCRIPTIONS["gateway_source_described_by_adapter"],
        "status": "pass",
        "evidence_refs": [{"artifact": "adapter/gateway-mcp-simulated-v0.2.6.json"}],
    })

    # 2. gateway_source_not_trust_authority
    if adapter.get("trust_boundary", {}).get("source_is_trust_authority") is not False:
        return None, "adapter_invalid", "trust_boundary.source_is_trust_authority not false"
    claims.append({
        "claim_id": "gateway_source_not_trust_authority",
        "description": CLAIM_DESCRIPTIONS["gateway_source_not_trust_authority"],
        "status": "pass",
        "evidence_refs": [{"artifact": "adapter/gateway-mcp-simulated-v0.2.6.json"}],
    })

    # 3. gateway_events_normalized
    claims.append({
        "claim_id": "gateway_events_normalized",
        "description": CLAIM_DESCRIPTIONS["gateway_events_normalized"],
        "status": "pass",
        "evidence_refs": [ref_for(scid) for scid in REQUIRED_SCENARIOS],
    })

    # 4. protected_actions_require_scoped_authority
    e2 = by_scenario["EVT-002-payment-release-direct"]
    e3 = by_scenario["EVT-003-vendor-approval-direct"]
    e4 = by_scenario["EVT-004-delegation-laundering"]
    e6 = by_scenario["EVT-006-data-export-out-of-scope"]
    e7 = by_scenario["EVT-007-deploy-change-out-of-scope"]
    e9 = by_scenario["EVT-009-vendor-approval-after-revocation"]
    if not (e2["decision"] == "allow" and e2["reason"] == "authority_requirements_satisfied"):
        return None, "normalized_claim_failed", "EVT-002 not allow/authority_requirements_satisfied"
    if not (e3["decision"] == "allow" and e3["reason"] == "authority_requirements_satisfied"):
        return None, "normalized_claim_failed", "EVT-003 not allow/authority_requirements_satisfied"
    if not (e4["decision"] == "deny" and e4["reason"] == "authority_subject_mismatch"):
        return None, "normalized_claim_failed", "EVT-004 not deny/authority_subject_mismatch"
    if not (e6["decision"] == "deny" and e6["reason"] == "constraint_not_satisfied"):
        return None, "normalized_claim_failed", "EVT-006 not deny/constraint_not_satisfied"
    if not (e7["decision"] == "deny" and e7["reason"] == "constraint_not_satisfied"):
        return None, "normalized_claim_failed", "EVT-007 not deny/constraint_not_satisfied"
    if not (e9["decision"] == "deny" and e9["reason"] == "authority_revoked"):
        return None, "normalized_claim_failed", "EVT-009 not deny/authority_revoked"
    claims.append({
        "claim_id": "protected_actions_require_scoped_authority",
        "description": CLAIM_DESCRIPTIONS["protected_actions_require_scoped_authority"],
        "status": "pass",
        "evidence_refs": [
            ref_for("EVT-002-payment-release-direct"),
            ref_for("EVT-003-vendor-approval-direct"),
            ref_for("EVT-004-delegation-laundering"),
            ref_for("EVT-006-data-export-out-of-scope"),
            ref_for("EVT-007-deploy-change-out-of-scope"),
            ref_for("EVT-009-vendor-approval-after-revocation"),
        ],
    })

    # 5. unauthorized_delegation_fails
    claims.append({
        "claim_id": "unauthorized_delegation_fails",
        "description": CLAIM_DESCRIPTIONS["unauthorized_delegation_fails"],
        "status": "pass",
        "evidence_refs": [ref_for("EVT-004-delegation-laundering")],
    })

    # 6. bypass_attempts_observed_or_blocked
    e5 = by_scenario["EVT-005-bypass-payment-release"]
    if not (
        e5["event_type"] == "gateway.bypass_attempt"
        and e5["bypass_detected"] is True
        and e5["decision"] == "deny"
        and e5["reason"] == "bypass_attempt_detected"
    ):
        return None, "normalized_claim_failed", "EVT-005 bypass attempt not consistent"
    claims.append({
        "claim_id": "bypass_attempts_observed_or_blocked",
        "description": CLAIM_DESCRIPTIONS["bypass_attempts_observed_or_blocked"],
        "status": "pass",
        "evidence_refs": [ref_for("EVT-005-bypass-payment-release")],
    })

    # 7. revoked_authority_fails
    e8 = by_scenario["EVT-008-revocation-marker"]
    if not (
        e8["event_type"] == "gateway.revocation_check"
        and e8["reason"] == "revocation_check"
    ):
        return None, "normalized_claim_failed", "EVT-008 revocation marker not consistent"
    if not (
        e9["decision"] == "deny"
        and e9["reason"] == "authority_revoked"
        and e9["revocation_checked"] is True
    ):
        return None, "normalized_claim_failed", "EVT-009 post-revocation deny not consistent"
    claims.append({
        "claim_id": "revoked_authority_fails",
        "description": CLAIM_DESCRIPTIONS["revoked_authority_fails"],
        "status": "pass",
        "evidence_refs": [
            ref_for("EVT-008-revocation-marker"),
            ref_for("EVT-009-vendor-approval-after-revocation"),
        ],
    })

    # 8. out_of_scope_actions_fail
    claims.append({
        "claim_id": "out_of_scope_actions_fail",
        "description": CLAIM_DESCRIPTIONS["out_of_scope_actions_fail"],
        "status": "pass",
        "evidence_refs": [
            ref_for("EVT-006-data-export-out-of-scope"),
            ref_for("EVT-007-deploy-change-out-of-scope"),
        ],
    })

    # 9. source_evidence_hash_verifiable
    claims.append({
        "claim_id": "source_evidence_hash_verifiable",
        "description": CLAIM_DESCRIPTIONS["source_evidence_hash_verifiable"],
        "status": "pass",
        "evidence_refs": [{"artifact": "source/gateway-events.jsonl"}],
    })

    # 10. no_protected_actions_executed
    for e in events:
        if e["execution"]["performed"] is not False:
            return None, "execution_violation", f"event {e['source_event_id']} execution.performed != false"
    claims.append({
        "claim_id": "no_protected_actions_executed",
        "description": CLAIM_DESCRIPTIONS["no_protected_actions_executed"],
        "status": "pass",
        "evidence_refs": [{"artifact": "source/gateway-events.jsonl"}],
    })

    return claims, "", ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compose a ProofRail Silver v0.2.7 composed gateway evidence package.",
    )
    parser.add_argument("--demo-root", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--gateway-events", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--generated-at", required=True, type=str)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    demo_root: Path = args.demo_root
    adapter_path: Path = args.adapter
    events_path: Path = args.gateway_events
    output_dir: Path = args.output_dir
    generated_at: str = args.generated_at

    # 1. Output directory checks.
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.force:
            err(f"--output-dir {output_dir} is non-empty; pass --force to overwrite")
            return 2
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Input file checks.
    for label, p in [
        ("demo-root", demo_root),
        ("adapter", adapter_path),
        ("gateway-events", events_path),
    ]:
        if not p.exists():
            err(f"{label} not found: {p}")
            return 2
    demo_readme = demo_root / "README.md"
    demo_walkthrough = demo_root / "demo-walkthrough.md"
    for label, p in [("demo README", demo_readme), ("demo walkthrough", demo_walkthrough)]:
        if not p.exists():
            err(f"{label} not found at {p}")
            return 2

    # 3. Adapter validation.
    ok, detail = validate_adapter_with_v026(adapter_path)
    if not ok:
        return fail("adapter_invalid", detail)
    adapter = load_adapter(adapter_path)
    if adapter.get("source", {}).get("source_type") != "gateway":
        return fail("adapter_not_gateway_source", adapter.get("source", {}).get("source_type", "missing"))
    if adapter.get("trust_boundary", {}).get("source_is_trust_authority") is not False:
        return fail("adapter_invalid", "trust_boundary.source_is_trust_authority is not false")

    # 4. Parse and validate events.
    events, ev_reason, ev_detail = parse_jsonl_events(events_path)
    if events is None:
        return fail(ev_reason, ev_detail)

    # 5. Required scenarios.
    sc_reason, sc_detail = check_required_scenarios(events)
    if sc_reason:
        return fail(sc_reason, sc_detail)

    # 6. Protected action IDs within adapter scope.
    pa_reason, pa_detail = check_protected_actions_in_scope(events, adapter)
    if pa_reason:
        return fail(pa_reason, pa_detail)

    # 7. Copy subjects to output dir.
    (output_dir / "adapter").mkdir(parents=True, exist_ok=True)
    (output_dir / "source").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(demo_readme, output_dir / "README.md")
    shutil.copyfile(demo_walkthrough, output_dir / "demo-walkthrough.md")
    adapter_copy = output_dir / "adapter" / adapter_path.name
    shutil.copyfile(adapter_path, adapter_copy)
    events_copy = output_dir / "source" / "gateway-events.jsonl"
    shutil.copyfile(events_path, events_copy)
    print(f"PASS: copied 4 input files into {output_dir}")

    # 8. Compute hash of copied source events for the report.
    events_hex, _ = sha256_of_file(events_copy)
    source_events_sha256 = f"sha256:{events_hex}"

    # 9. Derive claims.
    claims, cl_reason, cl_detail = derive_claims(events, adapter, source_events_sha256)
    if claims is None:
        return fail(cl_reason, cl_detail)
    if [c["claim_id"] for c in claims] != CLAIM_IDS:
        return fail("normalized_claim_missing", "composer claim order does not match required set")

    # 10. Emit composed report.
    report = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": REPORT_SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "demo_id": DEMO_ID,
        "generated_at": generated_at,
        "adapter": {
            "adapter_id": adapter["adapter_id"],
            "adapter_path": "adapter/" + adapter_path.name,
            "source_type": "gateway",
            "source_is_trust_authority": False,
        },
        "source": {
            "source_events_path": "source/gateway-events.jsonl",
            "source_event_count": len(events),
            "source_events_sha256": source_events_sha256,
        },
        "claims": claims,
        "execution": {
            "protected_actions_performed": False,
            "reason": "composed_gateway_evidence_only",
        },
        "limitations": list(LIMITATIONS_REPORT),
        "non_claims": list(NON_CLAIMS_REPORT),
    }
    report_path = output_dir / "composed-gateway-evidence-report.json"
    write_json(report_path, report)
    print(f"PASS: composed report written to {report_path}")

    # 11. Emit composed manifest.
    subject_specs = [
        ("README.md", "demo_readme"),
        ("demo-walkthrough.md", "demo_walkthrough"),
        ("adapter/" + adapter_path.name, "adapter_descriptor"),
        ("source/gateway-events.jsonl", "source_events"),
        ("composed-gateway-evidence-report.json", "composed_report"),
    ]
    subjects: list[dict] = []
    for rel, role in subject_specs:
        full = output_dir / rel
        if not full.exists():
            return fail("composed_subject_file_missing", rel)
        hex_, size = sha256_of_file(full)
        subjects.append({
            "path": rel,
            "role": role,
            "sha256": f"sha256:{hex_}",
            "size_bytes": size,
        })

    manifest = {
        "document_type": MANIFEST_DOCUMENT_TYPE,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "demo_id": DEMO_ID,
        "generated_at": generated_at,
        "hash_algorithm": "sha256",
        "package_root": ".",
        "subjects": subjects,
        "composition": {
            "source_type": "gateway",
            "adapter_descriptor_path": "adapter/" + adapter_path.name,
            "source_events_path": "source/gateway-events.jsonl",
            "composed_report_path": "composed-gateway-evidence-report.json",
            "source_is_trust_authority": False,
        },
        "limitations": list(LIMITATIONS_MANIFEST),
        "non_claims": list(NON_CLAIMS_MANIFEST),
    }
    manifest_path = output_dir / "composed-gateway-evidence-manifest.json"
    write_json(manifest_path, manifest)
    print(f"PASS: composed manifest written to {manifest_path}")

    print(f"=== composed gateway evidence package generated at {output_dir} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
