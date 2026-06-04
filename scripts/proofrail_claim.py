#!/usr/bin/env python3
"""ProofRail Bronze Claim Tool v0.1

Structural validator, summarizer, and scaffold generator for ProofRail Bronze
claim YAML files.

This tool performs structural validation only.  It does not certify deployments
or verify full semantic conformance.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required.  Install with:  pip install PyYAML")

VERSION = "0.1"

# ---------------------------------------------------------------------------
# Enums and constants
# ---------------------------------------------------------------------------

VALID_CLAIM_TYPES = {"composed_bronze", "native_bronze_preview"}
VALID_CLAIM_STATUSES = {"draft", "tested", "evidence_closed", "superseded"}
VALID_VALIDATION_RESULTS = {"draft", "pass", "fail", "conditional"}
VALID_BYPASS_LEVELS = {"design", "deployment"}

REQUIRED_TOP_LEVEL_SECTIONS = [
    "schema_version",
    "claim_id",
    "claim_type",
    "claim_status",
    "profile",
    "claim_subject",
    "protected_actuator_set",
    "declared_control_surfaces",
    "identity_treatment",
    "enforcement_decision_model",
    "rate_limit_or_circuit_breaker",
    "emergency_stop",
    "bypass_prevention",
    "audit_evidence",
    "performance_evidence",
    "ownership_and_runbook",
    "evidence_bundle",
    "validation",
]

MINIMUM_DECISION_VOCABULARY = {"allow", "block", "rate_limit", "emergency_stop"}

MINIMUM_EVENT_TYPES = {
    "tool_call.attempt",
    "tool_call.decision",
    "tool_call.result",
    "emergency.stop",
    "emergency.resume",
}

# Paths to check when --evidence-root is provided.
# Each entry is (dotted_path, is_list_field).
EVIDENCE_PATH_FIELDS = [
    ("protected_actuator_set.manifest_path", False),
    ("declared_control_surfaces[].configuration_evidence.config_snapshot_path", True),
    ("identity_treatment.evidence.identity_mapping_path", False),
    ("enforcement_decision_model.policy_model.policy_snapshot_path", False),
    ("rate_limit_or_circuit_breaker.test_results_path", False),
    ("emergency_stop.evidence.runbook_path", False),
    ("emergency_stop.evidence.emergency_stop_test_path", False),
    ("bypass_prevention.evidence.bypass_results_path", False),
    ("audit_evidence.normalized_mapping.mapping_path", False),
    ("audit_evidence.evidence.sample_events_path", False),
    ("performance_evidence.evidence.summary_md_path", False),
    ("ownership_and_runbook.runbook_path", False),
    ("evidence_bundle.bundle_path", False),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(data, dotted_path, default=None):
    """Walk *data* along a dot-separated path, returning *default* on miss."""
    parts = dotted_path.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part, default)
        if current is default:
            return default
    return current


def _resolve_evidence_paths(claim, evidence_root):
    """Return a list of (field_description, resolved_path) tuples."""
    results = []
    for field_spec, is_list_field in EVIDENCE_PATH_FIELDS:
        if is_list_field:
            # Handle declared_control_surfaces[].config...
            parts = field_spec.split("[].")
            if len(parts) != 2:
                continue
            list_key = parts[0]
            sub_path = parts[1]
            items = _get(claim, list_key)
            if not isinstance(items, list):
                continue
            for i, item in enumerate(items):
                val = _get(item, sub_path)
                if val and isinstance(val, str):
                    results.append(
                        (f"{list_key}[{i}].{sub_path}",
                         Path(evidence_root) / val)
                    )
        else:
            val = _get(claim, field_spec)
            if val and isinstance(val, str):
                results.append((field_spec, Path(evidence_root) / val))
    return results


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def validate_claim(raw, strict=False, evidence_root=None):
    """Run all structural checks.  Return (errors, warnings, checks)."""
    errors = []
    warnings = []
    checks = []

    def _pass(msg):
        checks.append(("PASS", msg))

    def _fail(msg):
        errors.append(msg)
        checks.append(("FAIL", msg))

    def _warn(msg):
        warnings.append(msg)
        checks.append(("WARN", msg))

    # 1. Root object
    if not isinstance(raw, dict) or "proofrail_bronze_claim" not in raw:
        _fail("Missing root key: proofrail_bronze_claim")
        return errors, warnings, checks

    _pass("Root key proofrail_bronze_claim present")
    claim = raw["proofrail_bronze_claim"]
    if not isinstance(claim, dict):
        _fail("proofrail_bronze_claim is not a mapping")
        return errors, warnings, checks

    # 2. Required sections
    for section in REQUIRED_TOP_LEVEL_SECTIONS:
        if section not in claim:
            _fail(f"Missing required section: {section}")
        else:
            _pass(f"Section present: {section}")

    # Stop early if critical sections are missing.
    if errors:
        return errors, warnings, checks

    # 3. Enum checks
    ct = claim.get("claim_type")
    if ct not in VALID_CLAIM_TYPES:
        _fail(f"Invalid claim_type '{ct}'; expected one of {sorted(VALID_CLAIM_TYPES)}")
    else:
        _pass(f"claim_type '{ct}' is valid")

    cs = claim.get("claim_status")
    if cs not in VALID_CLAIM_STATUSES:
        _fail(f"Invalid claim_status '{cs}'; expected one of {sorted(VALID_CLAIM_STATUSES)}")
    else:
        _pass(f"claim_status '{cs}' is valid")

    vr = _get(claim, "validation.validation_result")
    if vr not in VALID_VALIDATION_RESULTS:
        _fail(
            f"Invalid validation.validation_result '{vr}'; "
            f"expected one of {sorted(VALID_VALIDATION_RESULTS)}"
        )
    else:
        _pass(f"validation.validation_result '{vr}' is valid")

    # 4. Protected actuator set
    pas = claim.get("protected_actuator_set", {})
    for field in ("name", "version", "manifest_path", "hash_algorithm", "hash"):
        if not _get(pas, field):
            _fail(f"Missing protected_actuator_set.{field}")
        else:
            _pass(f"protected_actuator_set.{field} present")

    pas_hash = _get(pas, "hash", "")
    if isinstance(pas_hash, str) and not pas_hash.startswith("sha256:"):
        if strict:
            _fail(f"protected_actuator_set.hash does not start with 'sha256:' (strict)")
        else:
            _warn("protected_actuator_set.hash does not start with 'sha256:'")
    elif isinstance(pas_hash, str) and pas_hash == "sha256:example":
        _warn("protected_actuator_set.hash is a placeholder value")
    else:
        _pass("protected_actuator_set.hash format ok")

    # 5. Control surfaces
    dcs = claim.get("declared_control_surfaces")
    if not isinstance(dcs, list) or len(dcs) == 0:
        _fail("declared_control_surfaces must contain at least one item")
    else:
        _pass(f"declared_control_surfaces contains {len(dcs)} item(s)")
        for i, surface in enumerate(dcs):
            for field in ("surface_id", "surface_type", "substrate", "role"):
                if not _get(surface, field):
                    _fail(f"declared_control_surfaces[{i}] missing {field}")
                else:
                    _pass(f"declared_control_surfaces[{i}].{field} present")

    # 6. Identity treatment
    it = claim.get("identity_treatment", {})
    if not _get(it, "identity_model"):
        _fail("Missing identity_treatment.identity_model")
    else:
        _pass("identity_treatment.identity_model present")

    icp = _get(it, "identity_confidence_policy")
    if not isinstance(icp, dict):
        _fail("Missing identity_treatment.identity_confidence_policy")
    else:
        _pass("identity_treatment.identity_confidence_policy present")
        for field in ("default_confidence", "tier_2_minimum", "tier_3_minimum"):
            if not _get(icp, field):
                _fail(f"Missing identity_confidence_policy.{field}")
            else:
                _pass(f"identity_confidence_policy.{field} present")

    # 7. Enforcement decision model
    edm = claim.get("enforcement_decision_model", {})
    dv = _get(edm, "decision_vocabulary")
    if not isinstance(dv, list):
        _fail("Missing enforcement_decision_model.decision_vocabulary")
    else:
        _pass("enforcement_decision_model.decision_vocabulary present")
        dv_set = set(dv)
        missing_vocab = MINIMUM_DECISION_VOCABULARY - dv_set
        if missing_vocab:
            _warn(
                f"enforcement_decision_model.decision_vocabulary missing "
                f"recommended terms: {sorted(missing_vocab)}"
            )
        else:
            _pass("enforcement_decision_model.decision_vocabulary includes minimum terms")

    pm = _get(edm, "policy_model")
    if not isinstance(pm, dict):
        _fail("Missing enforcement_decision_model.policy_model")
    else:
        _pass("enforcement_decision_model.policy_model present")

    # 8. Rate limit / circuit breaker
    rl = claim.get("rate_limit_or_circuit_breaker", {})
    if "implemented" not in rl:
        _fail("Missing rate_limit_or_circuit_breaker.implemented")
    else:
        _pass("rate_limit_or_circuit_breaker.implemented present")
        if not rl["implemented"]:
            _warn("rate_limit_or_circuit_breaker.implemented is not true")

    if not _get(rl, "control_type"):
        _fail("Missing rate_limit_or_circuit_breaker.control_type")
    else:
        _pass("rate_limit_or_circuit_breaker.control_type present")

    # 9. Emergency stop
    es = claim.get("emergency_stop", {})
    if "implemented" not in es:
        _fail("Missing emergency_stop.implemented")
    else:
        _pass("emergency_stop.implemented present")
        if not es["implemented"]:
            _warn("emergency_stop.implemented is not true")

    for field in ("activation_method", "resume_method"):
        if not _get(es, field):
            _fail(f"Missing emergency_stop.{field}")
        else:
            _pass(f"emergency_stop.{field} present")

    # 10. Bypass prevention
    bp = claim.get("bypass_prevention", {})
    cl = _get(bp, "claim_level")
    if not cl:
        _fail("Missing bypass_prevention.claim_level")
    elif cl not in VALID_BYPASS_LEVELS:
        _fail(
            f"Invalid bypass_prevention.claim_level '{cl}'; "
            f"expected one of {sorted(VALID_BYPASS_LEVELS)}"
        )
    else:
        _pass(f"bypass_prevention.claim_level '{cl}' is valid")
        if cl == "design":
            _warn("bypass_prevention.claim_level is 'design'; Bronze should prefer 'deployment'")

    if not _get(bp, "evidence"):
        _fail("Missing bypass_prevention.evidence")
    else:
        _pass("bypass_prevention.evidence present")

    # 11. Audit evidence
    ae = claim.get("audit_evidence", {})
    for field in ("audit_schema", "audit_sinks", "required_event_types"):
        val = _get(ae, field)
        if not val:
            _fail(f"Missing audit_evidence.{field}")
        else:
            _pass(f"audit_evidence.{field} present")

    sinks = _get(ae, "audit_sinks")
    if isinstance(sinks, list) and len(sinks) == 0:
        _fail("audit_evidence.audit_sinks must contain at least one sink")

    evt = _get(ae, "required_event_types")
    if isinstance(evt, list):
        evt_set = set(evt)
        missing_events = MINIMUM_EVENT_TYPES - evt_set
        if missing_events:
            _warn(
                f"audit_evidence.required_event_types missing recommended types: "
                f"{sorted(missing_events)}"
            )
        else:
            _pass("audit_evidence.required_event_types includes minimum types")

    # 12. Performance evidence
    pe = claim.get("performance_evidence", {})
    for field in ("required", "metric", "threshold_ms", "test_method"):
        if field not in pe:
            _fail(f"Missing performance_evidence.{field}")
        else:
            _pass(f"performance_evidence.{field} present")

    results = _get(pe, "results")
    if results is None:
        _warn("performance_evidence.results is null")
    elif isinstance(results, dict):
        if results.get("pass") is None:
            _warn("performance_evidence.results.pass is null")
        elif results.get("pass") is False:
            if strict:
                _fail("performance_evidence.results.pass is false (strict)")
            else:
                _warn("performance_evidence.results.pass is false")
        else:
            _pass("performance_evidence.results.pass is true")

    # 13. Ownership and runbook
    oar = claim.get("ownership_and_runbook", {})
    for field in ("platform_owner", "security_owner", "system_owner", "runbook_path"):
        val = _get(oar, field)
        if not val:
            _fail(f"Missing ownership_and_runbook.{field}")
        else:
            _pass(f"ownership_and_runbook.{field} present")
            if isinstance(val, str) and val.upper() == "TBD":
                _warn(f"ownership_and_runbook.{field} is 'TBD'")

    # 14. Evidence bundle
    eb = claim.get("evidence_bundle", {})
    for field in ("bundle_id", "bundle_path", "bundle_hash_algorithm"):
        if not _get(eb, field):
            _fail(f"Missing evidence_bundle.{field}")
        else:
            _pass(f"evidence_bundle.{field} present")

    bundle_hash = _get(eb, "bundle_hash")
    if not bundle_hash:
        _warn("evidence_bundle.bundle_hash is missing or empty")
    elif isinstance(bundle_hash, str) and bundle_hash in ("sha256:example", "sha256:placeholder"):
        _warn("evidence_bundle.bundle_hash is a placeholder value")
    else:
        _pass("evidence_bundle.bundle_hash present")

    # 15. Evidence file existence
    if evidence_root:
        paths = _resolve_evidence_paths(claim, evidence_root)
        for field_desc, resolved in paths:
            if not resolved.exists():
                msg = f"Evidence file not found: {field_desc} -> {resolved}"
                if strict:
                    _fail(msg)
                else:
                    _warn(msg)
            else:
                _pass(f"Evidence file exists: {field_desc}")

    return errors, warnings, checks


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _result_label(errors, warnings):
    if errors:
        return "FAIL"
    if warnings:
        return "PASS WITH WARNINGS"
    return "PASS"


def _result_key(errors, warnings):
    if errors:
        return "fail"
    if warnings:
        return "pass_with_warnings"
    return "pass"


def format_text(claim, errors, warnings, checks):
    lines = [f"ProofRail Bronze Claim Validator v{VERSION}", ""]
    lines.append(f"Claim: {_get(claim, 'claim_id', 'unknown')}")
    lines.append(f"Type:  {_get(claim, 'claim_type', 'unknown')}")
    lines.append(f"Status: {_get(claim, 'claim_status', 'unknown')}")
    lines.append("")

    lines.append("Structural checks:")
    for status, msg in checks:
        lines.append(f"  {status}  {msg}")
    lines.append("")

    if warnings:
        lines.append("Warnings:")
        for w in warnings:
            lines.append(f"  WARN  {w}")
        lines.append("")

    result = _result_label(errors, warnings)
    lines.append(f"Result: {result}")
    return "\n".join(lines)


def format_json(claim, errors, warnings, checks):
    obj = {
        "claim_id": _get(claim, "claim_id", "unknown"),
        "claim_type": _get(claim, "claim_type", "unknown"),
        "claim_status": _get(claim, "claim_status", "unknown"),
        "result": _result_key(errors, warnings),
        "errors": errors,
        "warnings": warnings,
        "checks": [{"status": s, "message": m} for s, m in checks],
    }
    return json.dumps(obj, indent=2)


# ---------------------------------------------------------------------------
# summarize command
# ---------------------------------------------------------------------------


def summarize_claim(raw):
    if not isinstance(raw, dict) or "proofrail_bronze_claim" not in raw:
        return "Error: missing proofrail_bronze_claim root key."
    c = raw["proofrail_bronze_claim"]

    def g(path, fallback="—"):
        val = _get(c, path, fallback)
        return fallback if val is None else val

    dcs = c.get("declared_control_surfaces")
    surface_count = len(dcs) if isinstance(dcs, list) else 0

    sinks = _get(c, "audit_evidence.audit_sinks")
    sink_count = len(sinks) if isinstance(sinks, list) else 0

    known = _get(c, "validation.known_limitations")
    if isinstance(known, list):
        known_str = "; ".join(known)
    else:
        known_str = str(known) if known else "—"

    lines = [
        f"ProofRail Bronze Claim Summary v{VERSION}",
        "",
        f"Claim ID:                  {g('claim_id')}",
        f"Claim type:                {g('claim_type')}",
        f"Claim status:              {g('claim_status')}",
        f"Profile version:           {g('profile.version')}",
        f"Environment:               {g('claim_subject.environment')}",
        f"Deployment:                {g('claim_subject.deployment_name')}",
        f"Protected actuator set:    {g('protected_actuator_set.name')}",
        f"  Hash:                    {g('protected_actuator_set.hash')}",
        f"Control surface count:     {surface_count}",
        f"Identity model:            {g('identity_treatment.identity_model')}",
        f"Policy source:             {g('enforcement_decision_model.policy_model.policy_source')}",
        f"Rate-limit/CB:             implemented={g('rate_limit_or_circuit_breaker.implemented')}",
        f"Emergency-stop:            implemented={g('emergency_stop.implemented')}",
        f"Bypass claim level:        {g('bypass_prevention.claim_level')}",
        f"Audit sink count:          {sink_count}",
        f"Performance threshold:     {g('performance_evidence.threshold_ms')} ms",
        f"Validation result:         {g('validation.validation_result')}",
        f"Known limitations:         {known_str}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# init command – template generation
# ---------------------------------------------------------------------------


def _build_template(claim_type_key):
    """Return a claim dict for the given type."""
    if claim_type_key == "native":
        ctype = "native_bronze_preview"
        cid = "bronze-native-YYYYMMDD-001"
        dname = "bronze-native-example"
        did = "example-002"
        substrate = "ProofRail-native"
        surface_type = "proofrail_proxy"
        surface_id = "proofrail-proxy-001"
        policy_source = "proofrail_native_policy"
        bundle_id = "bronze-native-evidence-YYYYMMDD"
    else:
        ctype = "composed_bronze"
        cid = "bronze-composed-YYYYMMDD-001"
        dname = "bronze-composed-example"
        did = "example-001"
        substrate = "generic_gateway"
        surface_type = "mcp_gateway"
        surface_id = "mcp-gateway-001"
        policy_source = "gateway_native_policy"
        bundle_id = "bronze-composed-evidence-YYYYMMDD"

    return {
        "proofrail_bronze_claim": {
            "schema_version": "v0.1",
            "claim_id": cid,
            "claim_type": ctype,
            "claim_status": "draft",
            "profile": {
                "name": "ProofRail Bronze",
                "version": "v0.1-draft",
                "baseline_reference": {
                    "name": "ProofRail Iron-plus",
                    "version": "v1.0.2-final",
                    "spec_version": "v0.1.5",
                },
            },
            "claim_subject": {
                "organization": "REPLACE_ME",
                "environment": "REPLACE_ME",
                "deployment_name": dname,
                "deployment_id": did,
                "claim_scope_summary": "MCP tool-call mediation for a declared protected actuator set",
            },
            "protected_actuator_set": {
                "name": "REPLACE_ME",
                "version": "v0.1",
                "manifest_path": "evidence/protected_actuator_set.json",
                "hash_algorithm": "sha256",
                "hash": "sha256:REPLACE_ME",
                "actuator_count": 0,
                "surfaces": ["mcp"],
            },
            "declared_control_surfaces": [
                {
                    "surface_id": surface_id,
                    "surface_type": surface_type,
                    "substrate": substrate,
                    "role": "primary_mediation_point",
                    "configuration_evidence": {
                        "config_snapshot_path": "evidence/gateway/config_snapshot.yaml",
                        "config_hash": "sha256:REPLACE_ME",
                    },
                }
            ],
            "identity_treatment": {
                "identity_model": "static_agent_id",
                "identity_confidence_policy": {
                    "default_confidence": "low",
                    "tier_2_minimum": "medium",
                    "tier_3_minimum": "medium",
                },
                "captured_fields": ["agent_id", "session_id", "correlation_id"],
            },
            "enforcement_decision_model": {
                "decision_vocabulary": [
                    "allow",
                    "block",
                    "degrade",
                    "rate_limit",
                    "require_approval",
                    "emergency_stop",
                ],
                "policy_model": {
                    "policy_source": policy_source,
                    "policy_version": "REPLACE_ME",
                    "policy_hash": "sha256:REPLACE_ME",
                    "policy_snapshot_path": "evidence/policy/policy_snapshot.yaml",
                },
            },
            "rate_limit_or_circuit_breaker": {
                "implemented": True,
                "control_type": "rate_limit",
                "scope": "per_agent",
                "test_results_path": "evidence/rate_limit/rate_limit_test_results.md",
            },
            "emergency_stop": {
                "implemented": True,
                "activation_method": "admin_api",
                "resume_method": "explicit_confirmation",
                "evidence": {
                    "runbook_path": "docs/runbook.md",
                    "emergency_stop_test_path": "evidence/emergency_stop/test_results.md",
                },
            },
            "bypass_prevention": {
                "claim_level": "deployment",
                "evidence": {
                    "bypass_results_path": "evidence/bypass/bypass_results.md",
                    "network_diagram_path": "docs/architecture/network_topology.md",
                    "credential_placement_path": "evidence/bypass/credential_placement.md",
                },
            },
            "audit_evidence": {
                "audit_schema": "proofrail_audit_v0",
                "audit_sinks": [
                    {
                        "sink_type": "jsonl",
                        "path_or_target": "evidence/audit/sample_audit.jsonl",
                    }
                ],
                "normalized_mapping": {
                    "mapping_target": "ECS",
                    "mapping_path": "evidence/ecs_mapping.json",
                },
                "required_event_types": [
                    "tool_call.attempt",
                    "tool_call.decision",
                    "tool_call.result",
                    "policy.change",
                    "degradation.mode_change",
                    "emergency.stop",
                    "emergency.resume",
                ],
            },
            "performance_evidence": {
                "required": True,
                "metric": "p95_added_latency_ms",
                "threshold_ms": 100,
                "test_method": "paired_upstream_vs_controlled_path",
                "results": {
                    "p95_added_latency_ms": None,
                    "error_count": None,
                    "pass": None,
                },
            },
            "ownership_and_runbook": {
                "platform_owner": "REPLACE_ME",
                "security_owner": "REPLACE_ME",
                "system_owner": "REPLACE_ME",
                "incident_commander": "REPLACE_ME",
                "runbook_path": "docs/runbook.md",
            },
            "evidence_bundle": {
                "bundle_id": bundle_id,
                "bundle_path": "evidence/bundle.zip",
                "bundle_hash_algorithm": "sha256",
                "bundle_hash": "sha256:REPLACE_ME",
            },
            "validation": {
                "validation_type": "self_attested_demo",
                "validator": "REPLACE_ME",
                "validation_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "validation_result": "draft",
                "known_limitations": [
                    "REPLACE_ME with actual limitations.",
                ],
            },
        }
    }


INIT_HEADER = (
    "# Generated by ProofRail Bronze Claim Tool v{version}\n"
    "#\n"
    "# This is an example only. Not a conformance claim.\n"
    "# Values are illustrative and do not describe a real deployment.\n"
    "# Replace all REPLACE_ME values with real deployment data.\n\n"
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_validate(args):
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    with open(path, "r") as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Error: invalid YAML: {exc}", file=sys.stderr)
            return 1

    evidence_root = args.evidence_root if hasattr(args, "evidence_root") and args.evidence_root else None
    strict = args.strict if hasattr(args, "strict") else False

    errors, warnings, checks = validate_claim(raw, strict=strict, evidence_root=evidence_root)

    claim = raw.get("proofrail_bronze_claim", {}) if isinstance(raw, dict) else {}

    fmt = getattr(args, "format", "text") or "text"
    if fmt == "json":
        print(format_json(claim, errors, warnings, checks))
    else:
        print(format_text(claim, errors, warnings, checks))

    return 1 if errors else 0


def cmd_summarize(args):
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    with open(path, "r") as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Error: invalid YAML: {exc}", file=sys.stderr)
            return 1

    print(summarize_claim(raw))
    return 0


def cmd_init(args):
    profile = args.profile
    if profile != "bronze":
        print(f"Error: unsupported profile '{profile}'; only 'bronze' is supported in v0.1", file=sys.stderr)
        return 1

    type_key = args.type
    if type_key not in ("composed", "native"):
        print(f"Error: --type must be 'composed' or 'native'", file=sys.stderr)
        return 1

    template = _build_template(type_key)
    header = INIT_HEADER.format(version=VERSION)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        f.write(header)
        yaml.dump(template, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Wrote {out_path}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="proofrail_claim",
        description=f"ProofRail Bronze Claim Tool v{VERSION}",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Generate a minimal Bronze claim scaffold")
    p_init.add_argument("--profile", required=True, help="Claim profile (bronze)")
    p_init.add_argument("--type", required=True, help="Claim type (composed | native)")
    p_init.add_argument("--out", required=True, help="Output file path")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate a Bronze claim YAML file")
    p_val.add_argument("file", help="Path to claim YAML file")
    p_val.add_argument("--strict", action="store_true", help="Promote warnings to failures")
    p_val.add_argument("--evidence-root", default=None, help="Root path for evidence file checks")
    p_val.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # summarize
    p_sum = subparsers.add_parser("summarize", help="Print a human-readable claim summary")
    p_sum.add_argument("file", help="Path to claim YAML file")

    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "summarize":
        return cmd_summarize(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
