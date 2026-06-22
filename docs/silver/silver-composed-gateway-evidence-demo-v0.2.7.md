# Silver Composed Gateway Evidence Demo — v0.2.7

**Status:** Draft / Composed Silver demo release
**Date:** 2026-06-22
**Schemas:**
- `schemas/silver-simulated-gateway-evidence-event-v0.1.0.md`
- `schemas/silver-composed-gateway-evidence-report-v0.1.0.md`
- `schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md`

---

## What v0.2.7 Adds

Silver v0.2.7 introduces the **Composed Silver Demo Over Simulated Gateway
Evidence**: a deterministic local demonstration that a Silver evidence package
can be composed from a v0.2.6 simulated gateway adapter descriptor and a
static JSONL gateway event fixture, then independently verified with hash
anchors, re-derived claims, and trust-boundary preservation.

Core sentence (preserved across docs):

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not
> integrate with a real gateway or certify gateway enforcement.

The simulated gateway is an evidence source, not a trust authority.

Composed Silver evidence is not Gold acceptance, production assurance,
compliance, or certification.

---

## Position in the Stack

| Layer | Role |
|---|---|
| Bronze | Claim about a deployment and its evidence files. |
| Silver | Cross-cutting controls — signing, revocation, conformance, attestation, fixtures, adapters, **composition**. |
| Gold | Out of scope for v0.2.7. |

v0.2.7 sits **between** the v0.2.6 adapter profile and v0.2.8's relying-party
acceptance record. It shows that an adapter-described source can be normalized
into a ProofRail evidence package; v0.2.8 will add the relying party's
acceptance decision on top of such a package.

ProofRail is not the gateway, not the SIEM, not the policy engine, not the
GRC platform. ProofRail records the shape of the evidence and what each
claim does **not** assert.

---

## Simulated Gateway Event Model

A JSON Lines fixture defines nine static events at
`fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`.

Closed event types:

```
gateway.message_observed
gateway.decision
gateway.bypass_attempt
gateway.revocation_check
```

Closed decisions: `allow`, `deny`, `not_applicable`.

Closed reasons:

```
authority_requirements_satisfied
authority_subject_mismatch
constraint_not_satisfied
authority_revoked
bypass_attempt_detected
revocation_check
no_protected_action
```

Closed protected action scope (matches the v0.2.6 simulated gateway adapter):

```
payment.release
vendor.approve
data.export
deploy.change
```

Every event has `execution.performed == false`.

---

## Required Scenarios

| scenario_event_id | event_type | protected_action_id | decision | reason |
|---|---|---|---|---|
| EVT-001-harmless-message | gateway.message_observed | (null) | not_applicable | no_protected_action |
| EVT-002-payment-release-direct | gateway.decision | payment.release | allow | authority_requirements_satisfied |
| EVT-003-vendor-approval-direct | gateway.decision | vendor.approve | allow | authority_requirements_satisfied |
| EVT-004-delegation-laundering | gateway.decision | payment.release | deny | authority_subject_mismatch |
| EVT-005-bypass-payment-release | gateway.bypass_attempt | payment.release | deny | bypass_attempt_detected |
| EVT-006-data-export-out-of-scope | gateway.decision | data.export | deny | constraint_not_satisfied |
| EVT-007-deploy-change-out-of-scope | gateway.decision | deploy.change | deny | constraint_not_satisfied |
| EVT-008-revocation-marker | gateway.revocation_check | vendor.approve | not_applicable | revocation_check |
| EVT-009-vendor-approval-after-revocation | gateway.decision | vendor.approve | deny | authority_revoked |

---

## Package Layout

Runtime output (never committed):

```
/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/
├── README.md
├── demo-walkthrough.md
├── adapter/
│   └── gateway-mcp-simulated-v0.2.6.json
├── source/
│   └── gateway-events.jsonl
├── composed-gateway-evidence-report.json
└── composed-gateway-evidence-manifest.json
```

Manifest deterministic subject order: `README.md`, `demo-walkthrough.md`,
`adapter/gateway-mcp-simulated-v0.2.6.json`, `source/gateway-events.jsonl`,
`composed-gateway-evidence-report.json`.

Manifest `composition` block:

```json
{
  "source_type": "gateway",
  "adapter_descriptor_path": "adapter/gateway-mcp-simulated-v0.2.6.json",
  "source_events_path": "source/gateway-events.jsonl",
  "composed_report_path": "composed-gateway-evidence-report.json",
  "source_is_trust_authority": false
}
```

---

## Composer (`tools/silver/compose_gateway_evidence_demo_v0_1_0.py`)

```bash
python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
  --demo-root demos/silver-demo-004-composed-gateway-evidence \
  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
  --generated-at 2026-06-22T00:00:00Z \
  --force
```

Composer steps and refusals are listed in
`demos/silver-demo-004-composed-gateway-evidence/demo-walkthrough.md`.

---

## Verifier (`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`)

```bash
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \
  --manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json
```

The verifier re-derives every required claim from the copied adapter and JSONL
events. It does not trust the report alone.

---

## Claim Derivation Table

| Claim ID | Pass predicate |
|---|---|
| `gateway_source_described_by_adapter` | Copied adapter passes v0.2.6 validator |
| `gateway_source_not_trust_authority` | `adapter.trust_boundary.source_is_trust_authority == false` |
| `gateway_events_normalized` | All nine scenario events present, valid, represented in claims |
| `protected_actions_require_scoped_authority` | EVT-002/003 allow/authority_requirements_satisfied; EVT-004 deny/authority_subject_mismatch; EVT-006/007 deny/constraint_not_satisfied; EVT-009 deny/authority_revoked |
| `unauthorized_delegation_fails` | EVT-004 deny/authority_subject_mismatch |
| `bypass_attempts_observed_or_blocked` | EVT-005 gateway.bypass_attempt, bypass_detected, deny, bypass_attempt_detected |
| `revoked_authority_fails` | EVT-008 revocation_check + EVT-009 deny/authority_revoked/revocation_checked |
| `out_of_scope_actions_fail` | EVT-006 + EVT-007 deny/constraint_not_satisfied |
| `source_evidence_hash_verifiable` | sha256(copied JSONL) == report.source.source_events_sha256 |
| `no_protected_actions_executed` | All events execution.performed == false; report execution.protected_actions_performed == false |

A wrong-but-valid evidence reference (e.g., bypass claim pointing at EVT-001
harmless message) is rejected with `normalized_evidence_ref_invalid` or
`normalized_claim_failed`.

---

## Stable Failure Reasons (18)

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

## Regression Test

`tests/test_silver_composed_gateway_evidence_v0_2_7.sh` exercises the composer
and verifier with the canonical fixture and a battery of tamper cases. The
test uses a `mktemp -d` working area with `trap` cleanup, copies a fresh
package for each tamper case, and recomputes manifest hashes for the
mutated subject so that semantic checks are reached when intended.

Cases covered:

1. v0.2.6 simulated gateway adapter validates.
2. Composer succeeds into a temporary directory.
3. Verifier accepts the untampered package.
4. Report contains all required claim IDs with `status == pass`.
5. Adapter copy has `source_is_trust_authority == false`.
6. Source events include all required `scenario_event_id` values.
7. Manifest subject hashes are valid (rechecked explicitly).
8. Tamper JSONL without rehash → `composed_subject_hash_mismatch`.
9. Tamper JSONL with rehash so EVT-002 decision becomes `deny` →
   `gateway_decision_mismatch` or `normalized_claim_failed`.
10. Tamper adapter so `decision_event` capability becomes `not_provided`,
    then rehash → `adapter_invalid`.
11. Tamper source event `protected_action_id` to an unsupported but
    valid-looking ID, then rehash → `gateway_protected_action_mismatch`.
12. Tamper bypass event so `bypass_detected == false`, then rehash →
    `gateway_bypass_mismatch`.
13. Tamper revocation event so `revocation_checked == false`, then rehash →
    `gateway_revocation_mismatch`.
14. Remove a required source event, then rehash → `source_event_missing`.
15. Duplicate a required source event, then rehash → `source_event_duplicate`.
16. Rewrite manifest subject path to contain `..` → `composed_subject_path_traversal`.
17. Rewrite manifest subject path to be absolute → `composed_subject_path_traversal`.
18. Tamper report claim status to `fail`, then rehash → `normalized_claim_failed`.
19. Tamper report evidence ref to contain `..`, then rehash →
    `normalized_evidence_ref_invalid`.
20. Tamper report evidence ref to point at wrong-but-valid event, then rehash
    → `normalized_evidence_ref_invalid` or `normalized_claim_failed`.
21. Tamper execution flag to `true` in a source event, then rehash →
    `execution_violation`.
22. Malformed gateway-events JSONL line, then rehash → `source_event_invalid`
    with no Python traceback.
23. Mutate manifest `composition.source_type` to a non-`gateway` value →
    `invalid_composed_gateway_manifest`.
24. Delete a referenced subject file (`source/gateway-events.jsonl`) without
    touching the manifest → `composed_subject_file_missing`.
25. Mutate adapter `source.source_type` to a v0.2.6-supported non-`gateway`
    value (`policy_engine`), then rehash → `adapter_not_gateway_source`.
26. Mutate `report.document_type` to an invalid value, then rehash →
    `normalized_report_invalid`.
27. Remove a required `claim_id` from `report.claims`, then rehash →
    `normalized_claim_missing`.
28. Scoped mutation check: committed v0.2.7 schemas, validator,
    composer, verifier, fixture, walkthrough, and demo README are unchanged
    by the test runtime.

These 28 cases collectively exercise all 18 stable failure reasons declared
by the v0.2.7 verifier.

The test prints
`=== ProofRail Silver v0.2.7 composed gateway evidence demo: 28/28 PASS ===`
on success.

---

## Make Targets

- `make run-silver-composed-gateway-demo-v0-2-7` — Compose the demo into
  `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7` **and** verify it
  with `verify_composed_gateway_evidence_demo_v0_1_0.py`.
- `make verify-silver-composed-gateway-demo-v0-2-7` — Run the 28-step
  regression test.

`verify-silver-composed-gateway-demo-v0-2-7` is appended to
`verify-silver-all`.

---

## What v0.2.7 Does Not Do

- Does not integrate with any real MCP gateway, observability stack, SIEM,
  policy engine, or GRC platform.
- Does not certify gateway enforcement.
- Does not execute any protected action.
- Does not assert that any real product behaves like the simulated fixture.
- Does not establish a new trust authority. The gateway remains an evidence
  source.
- Does not sign the composed report.
- Does not establish a relying-party acceptance record (that is v0.2.8 work).
- Does not change Bronze, Silver Signed Bundle Assertion, Revocation List,
  Verification Report, Profile, Verifier Output Attestation, Multi-principal
  Authority, Multi-agent Harness, Multi-agent Trust-boundary, or Evidence
  Source Adapter semantics.

The v0.2.7 release is a composed-demo release, intentionally narrow in scope
and conservative in claim.
