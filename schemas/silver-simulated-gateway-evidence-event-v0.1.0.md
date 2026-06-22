# Silver Simulated Gateway Evidence Event — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.7
**Document type:** `proofrail.silver.simulated_gateway_event`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.7`

---

## Scope

This schema defines the shape of a single line in the v0.2.7 simulated gateway
event fixture (`fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`).

Each line in the JSONL file is one event. Events are static and simulated.
They do not represent any real gateway product or any real traffic.

The schema is consumed by:

- `tools/silver/compose_gateway_evidence_demo_v0_1_0.py`
- `tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`

Neither tool fetches network resources or reads vendor logs.

---

## Required fields

Every event line MUST be a JSON object with these keys:

| Field | Type | Notes |
|---|---|---|
| `document_type` | string | Must equal `"proofrail.silver.simulated_gateway_event"` |
| `schema_version` | string | Must equal `"v0.1.0"` |
| `source_type` | string | Must equal `"gateway"` |
| `source_event_id` | string | Composer-stable identifier; unique within the JSONL file |
| `scenario_event_id` | string | Semantic scenario identifier (see §Required scenarios) |
| `timestamp` | string | ISO-8601 timestamp (`Z`-suffixed) |
| `event_type` | string | One of the closed event types in §Event types |
| `protected_action_id` | string or null | One of the closed action IDs in §Protected action scope; MAY be `null` only when `event_type == "gateway.message_observed"` |
| `decision` | string | One of `"allow"`, `"deny"`, `"not_applicable"` |
| `reason` | string | One of the closed reason codes in §Reason codes |
| `revocation_checked` | boolean | Whether revocation was consulted at decision time |
| `bypass_detected` | boolean | Whether a bypass attempt was observed |
| `execution` | object | `{ "performed": false, "reason": <non-empty string> }` |

`execution.performed` MUST be `false` for every event. Composer and verifier
both reject any event with `execution.performed != false`.

`subject_hash` is intentionally NOT a required field in v0.2.7. Subject-hash
semantics are deferred to a later release with explicit derivation rules.

---

## Optional fields

These fields are accepted but not required:

| Field | Type |
|---|---|
| `principal_id` | string |
| `target_principal_id` | string |
| `controlled_path` | boolean |
| `gateway_id` | string |

Any unknown additional field is ignored by the v0.2.7 verifier (forward-compatible
read), but composer and verifier do not derive claim status from unknown fields.

---

## Event types

Closed set:

```
gateway.message_observed
gateway.decision
gateway.bypass_attempt
gateway.revocation_check
```

Any other `event_type` is rejected with `source_event_invalid`.

---

## Decisions

Closed set:

```
allow
deny
not_applicable
```

Any other `decision` value is rejected with `gateway_decision_mismatch`.

---

## Reason codes

Closed set:

```
authority_requirements_satisfied
authority_subject_mismatch
constraint_not_satisfied
authority_revoked
bypass_attempt_detected
revocation_check
no_protected_action
```

`reason` must be a non-empty string and must be from the closed set above. Any
other value is rejected with `source_event_invalid`.

---

## Protected action scope

Closed set for v0.2.7:

```
payment.release
vendor.approve
data.export
deploy.change
```

These IDs are also the `protected_action_ids` declared by the v0.2.6 simulated
gateway adapter at
`examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json`.

Any other `protected_action_id` in an event is rejected with
`gateway_protected_action_mismatch`.

`protected_action_id` MAY be `null` only when `event_type == "gateway.message_observed"`.

---

## Cross-field consistency rules

- `event_type == "gateway.bypass_attempt"` requires `bypass_detected == true`
  and `decision == "deny"`. Any inconsistency is rejected with
  `gateway_bypass_mismatch`.
- `event_type == "gateway.revocation_check"` requires `revocation_checked == true`
  and `reason == "revocation_check"`. Any inconsistency is rejected with
  `gateway_revocation_mismatch`.
- `reason == "authority_revoked"` requires `revocation_checked == true` and
  `decision == "deny"`. Any inconsistency is rejected with
  `gateway_revocation_mismatch`.
- `event_type == "gateway.message_observed"` requires `decision == "not_applicable"`
  and `reason == "no_protected_action"`.

---

## Required scenarios (composer + verifier)

The JSONL fixture MUST contain exactly one event for each of these
`scenario_event_id` values, no duplicates:

```
EVT-001-harmless-message
EVT-002-payment-release-direct
EVT-003-vendor-approval-direct
EVT-004-delegation-laundering
EVT-005-bypass-payment-release
EVT-006-data-export-out-of-scope
EVT-007-deploy-change-out-of-scope
EVT-008-revocation-marker
EVT-009-vendor-approval-after-revocation
```

Missing → `source_event_missing`. Duplicates → `source_event_duplicate`.

---

## Non-claims

- This schema does not assert that any real gateway emits this shape.
- This schema does not certify any vendor product.
- The gateway remains an evidence source, not a trust authority.
- Static fixture only; no live traffic is ingested.
