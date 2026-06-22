# Silver Demo 004 — Composed Gateway Evidence Walkthrough

**ProofRail release:** v0.2.7

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not
> integrate with a real gateway or certify gateway enforcement.

---

## 1. Inputs

The composer reads two committed inputs and two committed docs:

| Input | Path |
|---|---|
| Adapter descriptor (v0.2.6) | `examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json` |
| Gateway events (JSONL fixture) | `fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl` |
| Demo README | `demos/silver-demo-004-composed-gateway-evidence/README.md` |
| Demo walkthrough | `demos/silver-demo-004-composed-gateway-evidence/demo-walkthrough.md` |

No network, no live actuator, no real gateway, no live ingestion.

---

## 2. Composer steps

1. Refuse to overwrite a non-empty `--output-dir` unless `--force` is given.
2. Re-validate the adapter descriptor by invoking the v0.2.6 adapter validator
   (`tools/silver/validate_evidence_source_adapter_v0_1_0.py`) as a subprocess.
   Any nonzero exit is propagated as failure.
3. Confirm `adapter.source.source_type == "gateway"` and
   `adapter.trust_boundary.source_is_trust_authority == false`.
4. Parse the JSONL events line-by-line and validate each against the v0.1.0
   simulated gateway event schema, including cross-field consistency rules
   for bypass and revocation events.
5. Confirm exactly one event for each required `scenario_event_id`.
6. Confirm every `protected_action_id` is in the adapter's declared
   `protected_action_mapping.protected_action_ids` (or `null` for
   `gateway.message_observed`).
7. Confirm every event has `execution.performed == false`.
8. Copy the four committed input/doc files into the runtime output layout:
   `README.md`, `demo-walkthrough.md`, `adapter/gateway-mcp-simulated-v0.2.6.json`,
   `source/gateway-events.jsonl`.
9. Compute SHA-256 of the copied `source/gateway-events.jsonl`.
10. Derive the ten required claims from the parsed events and adapter, write
    `composed-gateway-evidence-report.json`.
11. Compute SHA-256 and size for the five package subjects, write
    `composed-gateway-evidence-manifest.json` with deterministic subject order
    and a `composition` block.

---

## 3. Required claim IDs and derivation

| Claim ID | Pass predicate |
|---|---|
| `gateway_source_described_by_adapter` | Copied adapter passes v0.2.6 validator |
| `gateway_source_not_trust_authority` | `adapter.trust_boundary.source_is_trust_authority == false` |
| `gateway_events_normalized` | All nine required scenarios present, valid, and represented in claims |
| `protected_actions_require_scoped_authority` | EVT-002/003 are `allow`/`authority_requirements_satisfied`; EVT-004 is `deny`/`authority_subject_mismatch`; EVT-006/007 are `deny`/`constraint_not_satisfied`; EVT-009 is `deny`/`authority_revoked` |
| `unauthorized_delegation_fails` | EVT-004 is `deny`/`authority_subject_mismatch` |
| `bypass_attempts_observed_or_blocked` | EVT-005 is `gateway.bypass_attempt`, `bypass_detected == true`, `decision == deny`, `reason == bypass_attempt_detected` |
| `revoked_authority_fails` | EVT-008 is `gateway.revocation_check`/`revocation_check`; EVT-009 is `deny`/`authority_revoked` with `revocation_checked == true` |
| `out_of_scope_actions_fail` | EVT-006 and EVT-007 are both `deny`/`constraint_not_satisfied` |
| `source_evidence_hash_verifiable` | SHA-256 of copied `source/gateway-events.jsonl` matches `source.source_events_sha256` |
| `no_protected_actions_executed` | `report.execution.protected_actions_performed == false`; every event has `execution.performed == false` |

The verifier re-derives every claim independently from the copied adapter and
JSONL. A composer-emitted status disagreeing with the re-derived status is
rejected as `normalized_claim_failed`.

---

## 4. Verifier steps

```bash
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \
  --manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json
```

Hash-first ordering:

1. Parse manifest. Reject on shape, document type, version, hash algorithm,
   subject count/order, or `composition` block errors with
   `invalid_composed_gateway_manifest`.
2. Reject any subject `path` containing `..` or starting with `/` with
   `composed_subject_path_traversal`.
3. Reject missing files with `composed_subject_file_missing`.
4. Recompute SHA-256 for every subject; reject mismatches with
   `composed_subject_hash_mismatch`.
5. Re-validate copied adapter with the v0.2.6 validator (subprocess); reject
   with `adapter_invalid`. If `source_type != "gateway"`, reject with
   `adapter_not_gateway_source`.
6. Re-parse JSONL. Reject malformed lines with `source_event_invalid`
   (no Python traceback). Reject empty file with `source_event_missing`.
   Reject duplicates with `source_event_duplicate`. Reject out-of-scope
   `protected_action_id` with `gateway_protected_action_mismatch`. Reject
   unknown decisions with `gateway_decision_mismatch`. Reject inconsistent
   bypass events with `gateway_bypass_mismatch`. Reject inconsistent revocation
   events with `gateway_revocation_mismatch`.
7. Load report. Reject shape errors with `normalized_report_invalid`. Reject
   missing required claim IDs with `normalized_claim_missing`. Reject wrong
   evidence ref paths with `normalized_evidence_ref_invalid`. Reject
   wrong-but-valid evidence refs (e.g. bypass claim pointing at EVT-001) with
   `normalized_evidence_ref_invalid` or `normalized_claim_failed`. Reject
   any claim whose composer-reported `status` disagrees with the re-derived
   status with `normalized_claim_failed`.
8. Reject any event with `execution.performed == true` and any report with
   `execution.protected_actions_performed != false` with `execution_violation`.

---

## 5. Stable failure reasons

```
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
```

---

## 6. Non-claims

- v0.2.7 does not integrate with any real gateway, observability stack, SIEM,
  policy engine, or GRC platform.
- v0.2.7 does not certify gateway enforcement.
- v0.2.7 does not execute any protected action.
- v0.2.7 does not assert that any real product behaves like the simulated
  fixture.
- v0.2.7 does not establish a new trust authority. The gateway remains an
  evidence source.
- The composed report is not signed; v0.2.7 ships local hash anchors only.
- v0.2.7 does not change Bronze, Silver Signed Bundle Assertion, Revocation
  List, Verification Report, Profile, Verifier Output Attestation,
  Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary
  Demo, or Evidence Source Adapter semantics.

---

## 7. Looking ahead

v0.2.8 will add a relying-party acceptance record. v0.2.7 is intentionally
narrower: it shows how an evidence package can be **composed** from a
gateway source and **verified**, while preserving the boundary that
acceptance is a separate decision.
