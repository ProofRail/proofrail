# Silver Composed Gateway Evidence Fixture — v0.2.7

**ProofRail release:** v0.2.7
**Schema:** `schemas/silver-simulated-gateway-evidence-event-v0.1.0.md`

This directory contains the static, simulated gateway event fixture used by
the v0.2.7 composed Silver evidence demo.

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not
> integrate with a real gateway or certify gateway enforcement.

## Files

- `gateway-events.jsonl` — Nine simulated gateway events, one per line.

## Scenario coverage

The fixture covers these nine `scenario_event_id` values:

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

Every event has `execution.performed == false`.

## Non-claims

- This fixture is not real gateway traffic.
- This fixture does not assert authenticity, completeness, or trustworthiness
  of any real gateway.
- The simulated gateway is an evidence source, not a trust authority.
- No protected actions are executed.
