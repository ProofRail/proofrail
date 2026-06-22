# Silver Composed Gateway Evidence Report — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.7
**Document type:** `proofrail.silver.composed_gateway_evidence_report`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.7`

---

## Purpose

The composed gateway evidence report is the ProofRail-normalized output derived
from the v0.2.6 simulated gateway adapter descriptor and the v0.2.7 simulated
gateway event fixture.

It is emitted by `tools/silver/compose_gateway_evidence_demo_v0_1_0.py` and
re-derived independently by
`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`. The verifier
does not trust the report alone — it re-derives every required claim from the
copied adapter and source events.

---

## Required top-level fields

```
document_type       — "proofrail.silver.composed_gateway_evidence_report"
schema_version      — "v0.1.0"
proofrail_release   — "v0.2.7"
demo_id             — "proofrail-silver-demo-004-composed-gateway-evidence"
generated_at        — ISO-8601 timestamp (UTC, Z-suffixed)
adapter             — object (see §adapter block)
source              — object (see §source block)
claims              — array (see §claims; exactly the 10 required claim IDs)
execution           — object (see §execution)
limitations         — array of non-empty strings
non_claims          — array of non-empty strings
```

---

## `adapter` block

```
adapter_id                  — string; matches adapter file's adapter_id
adapter_path                — package-local relative path to adapter copy
source_type                 — "gateway"
source_is_trust_authority   — false
```

The verifier rejects any value of `source_is_trust_authority` other than `false`.

---

## `source` block

```
source_events_path     — package-local relative path to the JSONL events copy
source_event_count     — integer; total event lines in the JSONL file
source_events_sha256   — "sha256:<hex>"; SHA-256 of the copied JSONL file
```

---

## `claims`

`claims` is an array of objects. The set of `claim_id` values MUST exactly equal
this closed set (no missing, no extras):

```
gateway_source_described_by_adapter
gateway_source_not_trust_authority
gateway_events_normalized
protected_actions_require_scoped_authority
unauthorized_delegation_fails
bypass_attempts_observed_or_blocked
revoked_authority_fails
out_of_scope_actions_fail
source_evidence_hash_verifiable
no_protected_actions_executed
```

Each claim object has the following required fields:

| Field | Type | Notes |
|---|---|---|
| `claim_id` | string | Must be from the closed set above |
| `description` | string | Non-empty human description |
| `status` | string | Must be `"pass"` |
| `evidence_refs` | array | At least one package-local evidence reference |

Each `evidence_refs[i]` is an object with:

| Field | Type | Notes |
|---|---|---|
| `artifact` | string | Package-local relative path; no `..`; not absolute |
| `source_event_id` | string (optional) | `source_event_id` of the referenced JSONL event when applicable |
| `scenario_event_id` | string (optional) | `scenario_event_id` of the referenced JSONL event when applicable |

The verifier rejects any `artifact` path containing `..` or starting with `/`
(or a Windows drive prefix) with `normalized_evidence_ref_invalid`.

The verifier rejects a wrong-but-valid evidence reference. For example, if the
bypass claim's evidence references EVT-001 (harmless message) instead of
EVT-005 (bypass), the verifier rejects with `normalized_evidence_ref_invalid`
or, if the wrong reference still resolves to a valid file but disagrees with
the re-derived claim, `normalized_claim_failed`.

A required claim missing from `claims` is rejected with `normalized_claim_missing`.
A required claim with `status != "pass"` is rejected with `normalized_claim_failed`.

---

## Claim derivation rules

The verifier re-derives each claim from the copied adapter and JSONL events.
A composer-emitted status that disagrees with the verifier's re-derived
status is rejected with `normalized_claim_failed`.

```
gateway_source_described_by_adapter
    copied adapter validates with v0.2.6 adapter validator

gateway_source_not_trust_authority
    adapter.trust_boundary.source_is_trust_authority == false

gateway_events_normalized
    all required scenario events present, valid, and represented in claims

protected_actions_require_scoped_authority
    EVT-002, EVT-003: decision=allow, reason=authority_requirements_satisfied
    EVT-004:          decision=deny,  reason=authority_subject_mismatch
    EVT-006, EVT-007: decision=deny,  reason=constraint_not_satisfied
    EVT-009:          decision=deny,  reason=authority_revoked

unauthorized_delegation_fails
    EVT-004 decision=deny, reason=authority_subject_mismatch

bypass_attempts_observed_or_blocked
    EVT-005 event_type=gateway.bypass_attempt
            bypass_detected=true
            decision=deny
            reason=bypass_attempt_detected

revoked_authority_fails
    EVT-008 event_type=gateway.revocation_check, reason=revocation_check
    EVT-009 decision=deny, reason=authority_revoked, revocation_checked=true

out_of_scope_actions_fail
    EVT-006, EVT-007: decision=deny, reason=constraint_not_satisfied

source_evidence_hash_verifiable
    sha256(copied source/gateway-events.jsonl) == source.source_events_sha256

no_protected_actions_executed
    report.execution.protected_actions_performed == false
    every source event has execution.performed == false
```

---

## `execution`

```
protected_actions_performed  — false
reason                       — non-empty string explaining why
```

The verifier rejects any value of `protected_actions_performed` other than
`false` with `execution_violation`. Any source event with
`execution.performed == true` is rejected with `execution_violation`.

---

## `limitations` and `non_claims`

Both are arrays of non-empty strings. They MUST be present and non-empty in
the composed report.

Typical entries:

```
limitations:
- "Simulated gateway evidence only; no real gateway integration."
- "Static JSONL fixture; not live traffic."
- "Local SHA-256 integrity only; not signed."

non_claims:
- "v0.2.7 does not certify any real gateway."
- "v0.2.7 does not perform runtime enforcement."
- "v0.2.7 is not Gold acceptance."
```

---

## Non-claims about this schema

- The composed report does not assert that any real gateway behaves like the
  fixture.
- The composed report is not a Bronze claim, not a Silver Signed Bundle
  Assertion, and not a Verifier Output Attestation.
- The composed report does not establish a relying-party trust decision.
