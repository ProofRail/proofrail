#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.2.7 composed gateway evidence package.

The verifier:

  1. Parses the manifest JSON.
  2. Validates manifest document type, schema version, release, hash algorithm,
     package root, subjects order, and the composition block.
  3. Rejects any subject path containing '..' or starting with '/'.
  4. Confirms every subject file exists.
  5. Recomputes SHA-256 for every subject and compares to the manifest.
  6. Re-validates the copied adapter with the v0.2.6 adapter validator
     (subprocess invocation).
  7. Confirms adapter source.source_type == "gateway".
  8. Confirms adapter.trust_boundary.source_is_trust_authority == false.
  9. Re-parses source/gateway-events.jsonl and re-validates every event.
 10. Requires every required scenario event exactly once.
 11. Requires every protected_action_id to match the adapter's declared IDs.
 12. Loads composed-gateway-evidence-report.json and validates shape.
 13. Confirms every required report claim is present with status 'pass'.
 14. Confirms every evidence reference is package-local and safe.
 15. Re-derives every required claim from source events and adapter metadata.
 16. Confirms report execution.protected_actions_performed == false and no
     event has execution.performed == true.

Stable failure reasons:

  invalid_composed_gateway_manifest
  composed_subject_file_missing
  composed_subject_path_traversal
  composed_subject_hash_mismatch
  adapter_invalid
  adapter_not_gateway_source
  source_event_invalid
  source_event_missing
  source_event_duplicate
  gateway_protected_action_mismatch
  gateway_decision_mismatch
  gateway_bypass_mismatch
  gateway_revocation_mismatch
  normalized_report_invalid
  normalized_claim_missing
  normalized_claim_failed
  normalized_evidence_ref_invalid
  execution_violation

Usage:
  python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \\
    --manifest <composed-gateway-evidence-manifest.json>

Exit codes:
  0 - package valid
  1 - verification failure (stable reason printed)
  2 - usage or input-file error
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
ADAPTER_VALIDATOR = REPO_ROOT / "tools/silver/validate_evidence_source_adapter_v0_1_0.py"

REPORT_DOCUMENT_TYPE = "proofrail.silver.composed_gateway_evidence_report"
REPORT_SCHEMA_VERSION = "v0.1.0"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.composed_gateway_evidence_manifest"
MANIFEST_SCHEMA_VERSION = "v0.1.0"
EVENT_DOCUMENT_TYPE = "proofrail.silver.simulated_gateway_event"
EVENT_SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.7"

REQUIRED_SUBJECT_ORDER = [
    ("README.md", "demo_readme"),
    ("demo-walkthrough.md", "demo_walkthrough"),
    ("adapter/gateway-mcp-simulated-v0.2.6.json", "adapter_descriptor"),
    ("source/gateway-events.jsonl", "source_events"),
    ("composed-gateway-evidence-report.json", "composed_report"),
]

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


def fail(reason: str, detail: str = "") -> int:
    if detail:
        print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    else:
        print(f"FAIL: {reason}", file=sys.stderr)
    return 1


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def has_traversal(rel: Any) -> bool:
    if not isinstance(rel, str) or not rel:
        return True
    if rel.startswith("/"):
        return True
    # Windows-style drive prefix guard.
    if len(rel) >= 2 and rel[1] == ":":
        return True
    parts = Path(rel).parts
    return ".." in parts


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json_or_fail(path: Path, reason: str) -> tuple[Any, int]:
    try:
        text = path.read_text()
    except OSError as exc:
        err(f"cannot read {path}: {exc}")
        return None, 2
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, fail(reason, f"{path.name}: {exc.msg}")
    return obj, 0


def validate_adapter_with_v026(adapter_path: Path) -> tuple[bool, str]:
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


def parse_jsonl_events(events_path: Path) -> tuple[list[dict] | None, str, str]:
    if not events_path.exists():
        return None, "source_event_missing", str(events_path)
    try:
        raw = events_path.read_text()
    except OSError as exc:
        return None, "source_event_invalid", f"cannot read events file: {exc}"
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
            return None, "source_event_invalid", f"line {lineno}: not object"
        for field in REQUIRED_EVENT_FIELDS:
            if field not in obj:
                return None, "source_event_invalid", f"line {lineno}: missing {field}"
        if obj["document_type"] != EVENT_DOCUMENT_TYPE:
            return None, "source_event_invalid", f"line {lineno}: wrong document_type"
        if obj["schema_version"] != EVENT_SCHEMA_VERSION:
            return None, "source_event_invalid", f"line {lineno}: wrong schema_version"
        if obj["source_type"] != "gateway":
            return None, "source_event_invalid", f"line {lineno}: source_type"
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
            return None, "source_event_invalid", f"line {lineno}: event_type {obj['event_type']}"
        if obj["decision"] not in DECISIONS:
            return None, "gateway_decision_mismatch", f"line {lineno}: decision {obj['decision']}"
        if obj["reason"] not in REASONS:
            return None, "source_event_invalid", f"line {lineno}: reason {obj['reason']}"
        if not isinstance(obj["revocation_checked"], bool):
            return None, "source_event_invalid", f"line {lineno}: revocation_checked not bool"
        if not isinstance(obj["bypass_detected"], bool):
            return None, "source_event_invalid", f"line {lineno}: bypass_detected not bool"
        ex = obj["execution"]
        if not isinstance(ex, dict) or "performed" not in ex or "reason" not in ex:
            return None, "source_event_invalid", f"line {lineno}: execution shape"
        if ex["performed"] is not False:
            return None, "execution_violation", f"line {lineno}: execution.performed != false"
        if not isinstance(ex["reason"], str) or not ex["reason"].strip():
            return None, "source_event_invalid", f"line {lineno}: execution.reason empty"
        pid = obj["protected_action_id"]
        if pid is None:
            if obj["event_type"] != "gateway.message_observed":
                return None, "gateway_protected_action_mismatch", \
                    f"line {lineno}: null protected_action_id only for gateway.message_observed"
        elif not isinstance(pid, str) or not pid.strip():
            return None, "source_event_invalid", f"line {lineno}: bad protected_action_id"
        # Cross-field consistency.
        if obj["event_type"] == "gateway.message_observed":
            if obj["decision"] != "not_applicable":
                return None, "source_event_invalid", f"line {lineno}: message_observed decision"
            if obj["reason"] != "no_protected_action":
                return None, "source_event_invalid", f"line {lineno}: message_observed reason"
        if obj["event_type"] == "gateway.bypass_attempt":
            if obj["bypass_detected"] is not True:
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt missing bypass_detected"
            if obj["decision"] != "deny":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt decision != deny"
            if obj["reason"] != "bypass_attempt_detected":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_attempt reason"
        else:
            if obj["bypass_detected"] is True and obj["decision"] == "allow":
                return None, "gateway_bypass_mismatch", f"line {lineno}: bypass_detected with allow"
        if obj["event_type"] == "gateway.revocation_check":
            if obj["revocation_checked"] is not True:
                return None, "gateway_revocation_mismatch", f"line {lineno}: revocation_check missing revocation_checked"
            if obj["reason"] != "revocation_check":
                return None, "gateway_revocation_mismatch", f"line {lineno}: revocation_check reason"
        if obj["reason"] == "authority_revoked":
            if obj["revocation_checked"] is not True:
                return None, "gateway_revocation_mismatch", f"line {lineno}: authority_revoked needs revocation_checked"
            if obj["decision"] != "deny":
                return None, "gateway_revocation_mismatch", f"line {lineno}: authority_revoked decision"
        events.append(obj)
    return events, "", ""


def check_required_scenarios(events: list[dict]) -> tuple[str, str]:
    have = {e["scenario_event_id"] for e in events}
    for scid in REQUIRED_SCENARIOS:
        if scid not in have:
            return "source_event_missing", f"missing scenario {scid}"
    return "", ""


def re_derive_expected_claims(
    events: list[dict],
    adapter: dict,
    package_root: Path,
) -> tuple[dict[str, dict] | None, str, str]:
    """Re-derive expected (claim_id -> evidence_refs canonical) for cross-check.

    Returns a dict mapping claim_id -> {
        "status": "pass",
        "expected_scenario_ids": set[str],
        "artifact_only": bool,
    }
    """
    by_scenario = {e["scenario_event_id"]: e for e in events}
    expected: dict[str, dict] = {}

    # gateway_source_described_by_adapter
    expected["gateway_source_described_by_adapter"] = {
        "expected_scenarios": set(),
        "expected_artifacts": {"adapter/gateway-mcp-simulated-v0.2.6.json"},
    }
    # gateway_source_not_trust_authority
    if adapter.get("trust_boundary", {}).get("source_is_trust_authority") is not False:
        return None, "adapter_invalid", "trust_boundary.source_is_trust_authority not false"
    expected["gateway_source_not_trust_authority"] = {
        "expected_scenarios": set(),
        "expected_artifacts": {"adapter/gateway-mcp-simulated-v0.2.6.json"},
    }
    # gateway_events_normalized
    expected["gateway_events_normalized"] = {
        "expected_scenarios": set(REQUIRED_SCENARIOS),
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # protected_actions_require_scoped_authority
    e2 = by_scenario["EVT-002-payment-release-direct"]
    e3 = by_scenario["EVT-003-vendor-approval-direct"]
    e4 = by_scenario["EVT-004-delegation-laundering"]
    e6 = by_scenario["EVT-006-data-export-out-of-scope"]
    e7 = by_scenario["EVT-007-deploy-change-out-of-scope"]
    e9 = by_scenario["EVT-009-vendor-approval-after-revocation"]
    if not (e2["decision"] == "allow" and e2["reason"] == "authority_requirements_satisfied"):
        return None, "normalized_claim_failed", "EVT-002 derivation mismatch"
    if not (e3["decision"] == "allow" and e3["reason"] == "authority_requirements_satisfied"):
        return None, "normalized_claim_failed", "EVT-003 derivation mismatch"
    if not (e4["decision"] == "deny" and e4["reason"] == "authority_subject_mismatch"):
        return None, "normalized_claim_failed", "EVT-004 derivation mismatch"
    if not (e6["decision"] == "deny" and e6["reason"] == "constraint_not_satisfied"):
        return None, "normalized_claim_failed", "EVT-006 derivation mismatch"
    if not (e7["decision"] == "deny" and e7["reason"] == "constraint_not_satisfied"):
        return None, "normalized_claim_failed", "EVT-007 derivation mismatch"
    if not (e9["decision"] == "deny" and e9["reason"] == "authority_revoked"):
        return None, "normalized_claim_failed", "EVT-009 derivation mismatch"
    expected["protected_actions_require_scoped_authority"] = {
        "expected_scenarios": {
            "EVT-002-payment-release-direct",
            "EVT-003-vendor-approval-direct",
            "EVT-004-delegation-laundering",
            "EVT-006-data-export-out-of-scope",
            "EVT-007-deploy-change-out-of-scope",
            "EVT-009-vendor-approval-after-revocation",
        },
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # unauthorized_delegation_fails
    expected["unauthorized_delegation_fails"] = {
        "expected_scenarios": {"EVT-004-delegation-laundering"},
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # bypass_attempts_observed_or_blocked
    e5 = by_scenario["EVT-005-bypass-payment-release"]
    if not (
        e5["event_type"] == "gateway.bypass_attempt"
        and e5["bypass_detected"] is True
        and e5["decision"] == "deny"
        and e5["reason"] == "bypass_attempt_detected"
    ):
        return None, "normalized_claim_failed", "EVT-005 derivation mismatch"
    expected["bypass_attempts_observed_or_blocked"] = {
        "expected_scenarios": {"EVT-005-bypass-payment-release"},
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # revoked_authority_fails
    e8 = by_scenario["EVT-008-revocation-marker"]
    if not (e8["event_type"] == "gateway.revocation_check" and e8["reason"] == "revocation_check"):
        return None, "normalized_claim_failed", "EVT-008 derivation mismatch"
    if not (
        e9["decision"] == "deny"
        and e9["reason"] == "authority_revoked"
        and e9["revocation_checked"] is True
    ):
        return None, "normalized_claim_failed", "EVT-009 revocation derivation mismatch"
    expected["revoked_authority_fails"] = {
        "expected_scenarios": {
            "EVT-008-revocation-marker",
            "EVT-009-vendor-approval-after-revocation",
        },
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # out_of_scope_actions_fail
    expected["out_of_scope_actions_fail"] = {
        "expected_scenarios": {
            "EVT-006-data-export-out-of-scope",
            "EVT-007-deploy-change-out-of-scope",
        },
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # source_evidence_hash_verifiable
    expected["source_evidence_hash_verifiable"] = {
        "expected_scenarios": set(),
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    # no_protected_actions_executed
    for e in events:
        if e["execution"]["performed"] is not False:
            return None, "execution_violation", f"event {e['source_event_id']}"
    expected["no_protected_actions_executed"] = {
        "expected_scenarios": set(),
        "expected_artifacts": {"source/gateway-events.jsonl"},
    }
    return expected, "", ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ProofRail Silver v0.2.7 composed gateway evidence package.",
    )
    parser.add_argument("--manifest", required=True, type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    manifest_path: Path = args.manifest
    if not manifest_path.exists():
        err(f"manifest not found: {manifest_path}")
        return 2

    package_root = manifest_path.parent

    # Step 1: parse manifest.
    manifest, rc = load_json_or_fail(manifest_path, "invalid_composed_gateway_manifest")
    if rc != 0:
        return rc
    if not isinstance(manifest, dict):
        return fail("invalid_composed_gateway_manifest", "manifest not object")

    # Step 2: manifest shape.
    if manifest.get("document_type") != MANIFEST_DOCUMENT_TYPE:
        return fail("invalid_composed_gateway_manifest", "document_type")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        return fail("invalid_composed_gateway_manifest", "schema_version")
    if manifest.get("proofrail_release") != PROOFRAIL_RELEASE:
        return fail("invalid_composed_gateway_manifest", "proofrail_release")
    if manifest.get("hash_algorithm") != "sha256":
        return fail("invalid_composed_gateway_manifest", "hash_algorithm")
    if manifest.get("package_root") != ".":
        return fail("invalid_composed_gateway_manifest", "package_root")
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return fail("invalid_composed_gateway_manifest", "limitations")
    for entry in manifest["limitations"]:
        if not isinstance(entry, str) or not entry.strip():
            return fail("invalid_composed_gateway_manifest", "limitations entry empty")
    if not isinstance(manifest.get("non_claims"), list) or not manifest["non_claims"]:
        return fail("invalid_composed_gateway_manifest", "non_claims")
    for entry in manifest["non_claims"]:
        if not isinstance(entry, str) or not entry.strip():
            return fail("invalid_composed_gateway_manifest", "non_claims entry empty")

    subjects = manifest.get("subjects")
    if not isinstance(subjects, list) or len(subjects) != len(REQUIRED_SUBJECT_ORDER):
        return fail("invalid_composed_gateway_manifest", "subjects count")
    for i, (expected_path, expected_role) in enumerate(REQUIRED_SUBJECT_ORDER):
        s = subjects[i]
        if not isinstance(s, dict):
            return fail("invalid_composed_gateway_manifest", f"subject {i} not object")
        for k in ("path", "role", "sha256", "size_bytes"):
            if k not in s:
                return fail("invalid_composed_gateway_manifest", f"subject {i} missing {k}")
        if s["role"] != expected_role:
            return fail("invalid_composed_gateway_manifest", f"subject {i} role {s['role']} != {expected_role}")
        # Path traversal must run before deeper checks.
        if has_traversal(s["path"]):
            return fail("composed_subject_path_traversal", s["path"])
        if s["path"] != expected_path:
            return fail("invalid_composed_gateway_manifest", f"subject {i} path {s['path']} != {expected_path}")

    comp = manifest.get("composition")
    if not isinstance(comp, dict):
        return fail("invalid_composed_gateway_manifest", "composition missing")
    if comp.get("source_type") != "gateway":
        return fail("invalid_composed_gateway_manifest", "composition.source_type")
    if comp.get("source_is_trust_authority") is not False:
        return fail("invalid_composed_gateway_manifest", "composition.source_is_trust_authority")
    for key, expected_path in [
        ("adapter_descriptor_path", "adapter/gateway-mcp-simulated-v0.2.6.json"),
        ("source_events_path", "source/gateway-events.jsonl"),
        ("composed_report_path", "composed-gateway-evidence-report.json"),
    ]:
        v = comp.get(key)
        if not isinstance(v, str) or not v:
            return fail("invalid_composed_gateway_manifest", f"composition.{key}")
        if has_traversal(v):
            return fail("composed_subject_path_traversal", v)
        if v != expected_path:
            return fail("invalid_composed_gateway_manifest", f"composition.{key} != {expected_path}")

    # Step 3-5: subject existence and hash recomputation.
    for s in subjects:
        rel = s["path"]
        full = package_root / rel
        if not full.exists():
            return fail("composed_subject_file_missing", rel)
        recomputed = sha256_hex(full)
        recorded = s["sha256"]
        if not isinstance(recorded, str) or not recorded.startswith("sha256:"):
            return fail("composed_subject_hash_mismatch", f"{rel}: bad sha256 format")
        if recorded.split(":", 1)[1] != recomputed:
            return fail("composed_subject_hash_mismatch", rel)
    print("PASS: manifest shape + composition block + subject hashes verified")

    # Step 6-8: adapter validation.
    adapter_full = package_root / "adapter/gateway-mcp-simulated-v0.2.6.json"
    ok, detail = validate_adapter_with_v026(adapter_full)
    if not ok:
        return fail("adapter_invalid", detail)
    adapter, rc = load_json_or_fail(adapter_full, "adapter_invalid")
    if rc != 0:
        return rc
    if adapter.get("source", {}).get("source_type") != "gateway":
        return fail("adapter_not_gateway_source", str(adapter.get("source", {}).get("source_type")))
    if adapter.get("trust_boundary", {}).get("source_is_trust_authority") is not False:
        return fail("adapter_invalid", "trust_boundary.source_is_trust_authority not false")
    print("PASS: adapter re-validated as v0.2.6 gateway evidence source")

    # Step 9-11: event parsing and consistency.
    events_full = package_root / "source/gateway-events.jsonl"
    events, ev_reason, ev_detail = parse_jsonl_events(events_full)
    if events is None:
        return fail(ev_reason, ev_detail)
    sc_reason, sc_detail = check_required_scenarios(events)
    if sc_reason:
        return fail(sc_reason, sc_detail)
    declared_set = set(adapter.get("protected_action_mapping", {}).get("protected_action_ids", []))
    for e in events:
        pid = e["protected_action_id"]
        if pid is None:
            continue
        if pid not in declared_set:
            return fail("gateway_protected_action_mismatch", f"{e['source_event_id']}: {pid}")
    print("PASS: source events re-parsed and consistent with adapter scope")

    # Step 12-16: load report and re-derive claims.
    report_full = package_root / "composed-gateway-evidence-report.json"
    report, rc = load_json_or_fail(report_full, "normalized_report_invalid")
    if rc != 0:
        return rc
    if not isinstance(report, dict):
        return fail("normalized_report_invalid", "report not object")
    for key, expected in [
        ("document_type", REPORT_DOCUMENT_TYPE),
        ("schema_version", REPORT_SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
    ]:
        if report.get(key) != expected:
            return fail("normalized_report_invalid", f"report.{key} != {expected}")
    if not isinstance(report.get("limitations"), list) or not report["limitations"]:
        return fail("normalized_report_invalid", "report.limitations")
    if not isinstance(report.get("non_claims"), list) or not report["non_claims"]:
        return fail("normalized_report_invalid", "report.non_claims")
    if report.get("adapter", {}).get("source_is_trust_authority") is not False:
        return fail("normalized_report_invalid", "report.adapter.source_is_trust_authority")
    if report.get("execution", {}).get("protected_actions_performed") is not False:
        return fail("execution_violation", "report.execution.protected_actions_performed")
    # Recompute source_events_sha256 against the copied events file and the
    # path the report claims to anchor.
    source_path_in_report = report.get("source", {}).get("source_events_path")
    if not isinstance(source_path_in_report, str) or not source_path_in_report:
        return fail("normalized_evidence_ref_invalid", "report.source.source_events_path missing")
    if has_traversal(source_path_in_report):
        return fail("normalized_evidence_ref_invalid", source_path_in_report)
    if source_path_in_report != "source/gateway-events.jsonl":
        return fail("normalized_evidence_ref_invalid",
                    f"report.source.source_events_path != source/gateway-events.jsonl")
    recorded_sha = report.get("source", {}).get("source_events_sha256")
    if not isinstance(recorded_sha, str) or not recorded_sha.startswith("sha256:"):
        return fail("normalized_report_invalid", "report.source.source_events_sha256 format")
    expected_sha = "sha256:" + sha256_hex(events_full)
    if recorded_sha != expected_sha:
        return fail("normalized_claim_failed", "source_evidence_hash_verifiable: sha256 mismatch")
    # Adapter path in report.
    adapter_path_in_report = report.get("adapter", {}).get("adapter_path")
    if not isinstance(adapter_path_in_report, str) or not adapter_path_in_report:
        return fail("normalized_evidence_ref_invalid", "report.adapter.adapter_path missing")
    if has_traversal(adapter_path_in_report):
        return fail("normalized_evidence_ref_invalid", adapter_path_in_report)
    if adapter_path_in_report != "adapter/gateway-mcp-simulated-v0.2.6.json":
        return fail("normalized_evidence_ref_invalid",
                    "report.adapter.adapter_path != adapter/gateway-mcp-simulated-v0.2.6.json")

    # Re-derive expected claim structure.
    expected_map, reason, detail = re_derive_expected_claims(events, adapter, package_root)
    if expected_map is None:
        return fail(reason, detail)

    claims = report.get("claims")
    if not isinstance(claims, list):
        return fail("normalized_report_invalid", "claims not list")
    seen_claim_ids: list[str] = []
    by_claim_id: dict[str, dict] = {}
    for c in claims:
        if not isinstance(c, dict):
            return fail("normalized_report_invalid", "claim entry not object")
        cid = c.get("claim_id")
        if not isinstance(cid, str) or not cid.strip():
            return fail("normalized_report_invalid", "claim missing claim_id")
        if cid in by_claim_id:
            return fail("normalized_report_invalid", f"duplicate claim {cid}")
        by_claim_id[cid] = c
        seen_claim_ids.append(cid)
    for required_cid in CLAIM_IDS:
        if required_cid not in by_claim_id:
            return fail("normalized_claim_missing", required_cid)
    # Validate each claim.
    by_scenario = {e["scenario_event_id"]: e for e in events}
    for cid in CLAIM_IDS:
        c = by_claim_id[cid]
        if c.get("status") != "pass":
            return fail("normalized_claim_failed", f"{cid} status != pass")
        refs = c.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            return fail("normalized_report_invalid", f"{cid} evidence_refs missing")
        ref_scenarios: set[str] = set()
        ref_artifacts: set[str] = set()
        for ref in refs:
            if not isinstance(ref, dict):
                return fail("normalized_report_invalid", f"{cid} evidence_ref not object")
            artifact = ref.get("artifact")
            if not isinstance(artifact, str) or not artifact:
                return fail("normalized_evidence_ref_invalid", f"{cid} artifact missing")
            if has_traversal(artifact):
                return fail("normalized_evidence_ref_invalid", artifact)
            # Artifact must resolve inside the package and exist.
            if not (package_root / artifact).exists():
                return fail("normalized_evidence_ref_invalid", f"{cid} artifact {artifact} not in package")
            ref_artifacts.add(artifact)
            scid = ref.get("scenario_event_id")
            sid = ref.get("source_event_id")
            if scid is not None:
                if not isinstance(scid, str) or scid not in by_scenario:
                    return fail("normalized_evidence_ref_invalid", f"{cid} unknown scenario_event_id {scid}")
                if sid is not None and by_scenario[scid].get("source_event_id") != sid:
                    return fail("normalized_evidence_ref_invalid",
                                f"{cid} source_event_id/scenario_event_id mismatch")
                ref_scenarios.add(scid)
        exp = expected_map[cid]
        if exp["expected_scenarios"] and ref_scenarios != exp["expected_scenarios"]:
            extras = ref_scenarios - exp["expected_scenarios"]
            missing = exp["expected_scenarios"] - ref_scenarios
            if extras or missing:
                return fail("normalized_evidence_ref_invalid",
                            f"{cid}: wrong scenarios; extras={sorted(extras)} missing={sorted(missing)}")
        if not exp["expected_artifacts"].issubset(ref_artifacts):
            return fail("normalized_evidence_ref_invalid",
                        f"{cid}: missing expected artifacts {sorted(exp['expected_artifacts'])}")
    print("PASS: composed report claims re-derived and evidence refs validated")

    # Final non-execution sanity.
    for e in events:
        if e["execution"]["performed"] is not False:
            return fail("execution_violation", f"event {e['source_event_id']}")

    demo_id = manifest.get("demo_id", "")
    print(f"PASS: composed gateway evidence package valid ({demo_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
