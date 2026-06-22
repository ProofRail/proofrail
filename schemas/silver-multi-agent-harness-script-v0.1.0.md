# ProofRail Silver Multi-Agent Harness Script Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-agent attack harness scripts

---

## 1. Purpose

The Silver Multi-Agent Harness Script schema defines a deterministic, structured YAML format for expressing scripted multi-principal agent interaction flows.

A harness script enumerates a sequence of events that drive a local, non-executing harness through:

- harmless agent-to-agent messages;
- protected action attempts that must be routed through the v0.2.3 authority evaluator;
- bypass attempts that are blocked at the harness level;
- revocation markers that establish a deterministic point in time after which v0.2.3 revocation semantics apply.

The harness script is the single source of truth for both the harness runner and the test oracle. Expected outcomes are encoded per event and the runner emits a derived `expected-outcomes.json` artifact for evidence hashing.

The harness script is **not**:

- a live multi-agent runtime;
- natural-language prompt parsing;
- prompt-injection detection;
- model behavior evaluation;
- production authorization infrastructure;
- a signed certification artifact.

---

## 2. Relationship to v0.2.3 Authority Fixtures

The harness script references a v0.2.3 multi-principal authority fixture by path. Principals and protected action IDs referenced in events must exist in that fixture.

The harness does not duplicate authority rules. For every `protected_action_attempt` event, the harness invokes the v0.2.3 authority evaluator with the event timestamp as decision time, then maps the resulting decision status to a harness outcome.

Revocation markers do not mutate the authority fixture. They mark a point in time for human readability of the transcript. The next protected action attempt with a later timestamp than a fixture-recorded `revoked_at` is denied with `authority_revoked` by the unchanged v0.2.3 evaluator.

---

## 3. Format

YAML. UTF-8 encoded. Single document.

---

## 4. Top-Level Structure

```yaml
script_type: proofrail.silver.multi_agent_harness_script
script_version: v0.1.0
script_id: <string>
authority_fixture: <relative-path-to-v0.2.3-authority-fixture.yaml>
description: <string>
events: []
limitations: []
```

All top-level fields are required.

| Field | Type | Notes |
|---|---|---|
| `script_type` | string | Must equal `proofrail.silver.multi_agent_harness_script`. |
| `script_version` | string | Must equal `v0.1.0`. |
| `script_id` | string | Unique identifier for this harness script. |
| `authority_fixture` | string | Path to the v0.2.3 authority fixture YAML (informational; the runner uses `--authority-fixture` at execution time). |
| `description` | string | Human-readable description. |
| `events` | list | Ordered list of harness events. Must be non-empty. |
| `limitations` | list | Non-empty list of free-text non-claim strings. |

---

## 5. Event Types

Every event has these required fields:

```yaml
event_id: <string>           # unique within the script
event_type: <enum>           # see below
timestamp: <ISO-8601>        # event time; drives decision time for evaluator calls
from_principal_id: <string>  # source principal (or "proofrail.harness" for synthetic events)
to_principal_id: <string>    # destination principal or action ID
description: <string>        # free text; never parsed by the harness
expected:                    # required block; see Section 8
  harness_outcome: <enum>
```

Allowed `event_type` values:

| event_type | Semantics |
|---|---|
| `agent_message` | Harmless agent-to-agent message. No evaluator call. No request file written. |
| `protected_action_attempt` | Authority-gated action attempt. Routed through v0.2.3 evaluator with `timestamp` as decision time. |
| `bypass_attempt` | Direct call attempt that bypasses the controlled path. Blocked at harness level. No evaluator call. No request file. No decision report. |
| `revocation_marker` | Deterministic point-in-time marker. Recorded in transcript. No evaluator call. No fixture mutation. |

Event IDs must be unique within the script.

---

## 6. Protected Action Attempts

A `protected_action_attempt` event must include:

```yaml
protected_action:
  attempted: true
  action_id: <string>          # must exist in authority fixture
  request_template:
    request_id: <string>
    requesting_principal_id: <string>
    parameters: { ... }
    claimed_authority:
      grant_id: <string>
    context: { ... }           # optional
```

The runner renders the `request_template` into a v0.1.0 Silver Protected Action Request JSON, injecting `request_type: proofrail.silver.protected_action_request` and `request_version: v0.1.0` if absent.

The runner then invokes the v0.2.3 authority evaluator with `--decision-time` equal to the event `timestamp`. The decision report is written to `authority-decision-reports/<event_id>.json` inside the harness output directory.

The harness maps decision status to outcome:

| Evaluator decision.status | Harness outcome |
|---|---|
| `allow` | `action_allowed` |
| `deny` | `action_denied` |

Every decision report **must** have `execution.performed == false`. The runner fails the event with `decision_report_execution_violation` if this invariant is broken.

---

## 7. Bypass Attempts

A `bypass_attempt` event must include:

```yaml
protected_action:
  attempted: true
  action_id: <string>
  bypass_requested: true
```

For bypass events:

- the runner does **not** invoke the v0.2.3 evaluator;
- the runner does **not** generate a protected action request file;
- the runner does **not** generate an authority decision report;
- the harness outcome is `bypass_blocked`;
- the harness reason is `bypass_attempt_detected`.

This is harness-level prevention by design. Bypass detection is not authority evaluation.

---

## 8. Expected Outcomes

Each event has an `expected` block describing the canonical outcome the harness must observe:

```yaml
expected:
  harness_outcome: <enum>
  decision_status: <allow|deny>          # required for protected_action_attempt events
  decision_reason: <stable-reason-code>  # required for protected_action_attempt events
  harness_reason: <stable-reason-code>   # required for bypass_attempt events
```

Allowed `harness_outcome` values:

```
message_delivered
action_allowed
action_denied
bypass_blocked
revocation_marked
event_failed
```

The harness script is the **single source of truth** for expected outcomes. The runner derives `expected-outcomes.json` from the script and emits it as a runtime artifact for evidence hashing. There is no separate committed oracle file.

---

## 9. Revocation Markers

A `revocation_marker` event must include:

```yaml
event_type: revocation_marker
timestamp: <ISO-8601>   # informational; should match or follow a revocation.revoked_at in the fixture
revocation_id: <string> # must reference an existing fixture revocation
```

The harness records the marker in the transcript. Subsequent `protected_action_attempt` events use their own event `timestamp` as decision time. If that timestamp is at or after a fixture-recorded `revoked_at` for any grant in the request's delegation chain, the unchanged v0.2.3 evaluator returns `deny` with reason `authority_revoked`.

---

## 10. Limitations and Non-Claims

The script `limitations` list must be non-empty. Recommended entries:

```
Local deterministic harness script only.
No live agents executed.
No live actuators invoked.
Not natural-language prompt parsing.
Not prompt-injection detection.
Not Gold certification.
```

---

## 11. Examples

### 11.1 Harmless message

```yaml
- event_id: EVT-001-harmless-message
  event_type: agent_message
  timestamp: "2026-06-21T10:00:00Z"
  from_principal_id: buyerorg.agent
  to_principal_id: vendororg.agent
  description: Harmless status request.
  protected_action:
    attempted: false
  expected:
    harness_outcome: message_delivered
```

### 11.2 Protected action attempt (allow)

```yaml
- event_id: EVT-002-allowed-payment-release
  event_type: protected_action_attempt
  timestamp: "2026-06-21T10:05:00Z"
  from_principal_id: buyerorg.agent
  to_principal_id: proofrail.harness
  description: BuyerOrg Agent requests payment release through controlled path.
  protected_action:
    attempted: true
    action_id: payment.release
    request_template:
      request_id: EVT-002-payment-release
      requesting_principal_id: buyerorg.agent
      parameters:
        amount_usd: 1250
        vendor_id: vendororg
      claimed_authority:
        grant_id: buyer-payment-release-direct
  expected:
    harness_outcome: action_allowed
    decision_status: allow
    decision_reason: authority_requirements_satisfied
```

### 11.3 Bypass attempt

```yaml
- event_id: EVT-005-bypass-payment-release
  event_type: bypass_attempt
  timestamp: "2026-06-21T10:20:00Z"
  from_principal_id: vendororg.agent
  to_principal_id: payment.release
  description: VendorOrg Agent attempts to bypass ProofRail and call payment.release directly.
  protected_action:
    attempted: true
    action_id: payment.release
    bypass_requested: true
  expected:
    harness_outcome: bypass_blocked
    harness_reason: bypass_attempt_detected
```

### 11.4 Revocation marker

```yaml
- event_id: EVT-008-revocation-marker
  event_type: revocation_marker
  timestamp: "2026-06-21T12:00:00Z"
  from_principal_id: proofrail.harness
  to_principal_id: proofrail.harness
  description: Marker aligned with fixture revocation revoke-vendor-approval-001.
  revocation_id: revoke-vendor-approval-001
  expected:
    harness_outcome: revocation_marked
```

---

## 12. Changelog

- **v0.1.0 (2026-06-21):** Initial schema.
