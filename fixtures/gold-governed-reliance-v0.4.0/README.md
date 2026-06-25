# Gold Governed Reliance v0.4.0 Fixture Pack

This directory holds the canonical fixture and five single-scenario
variant fixtures consumed by the v0.4.0 Minimal Gold Governed Reliance
Demo runner and verifier.

These fixtures are deterministic local hand-authored JSON inputs. They
are NOT signed, NOT certified, NOT a transfer of reliance, and NOT
full Gold.

## Files

| Path | Decisions | Role |
|---|---|---|
| `governed-reliance-scenarios.json` | 5 | **Canonical v0.4.0 Gold package.** Full canonical demo body covering all five recognized scenarios in natural order. This is the only fixture in this pack that represents a full v0.4.0 Minimal Gold Governed Reliance Demo package shape. |
| `scenario-clean-acceptance.json` | 1 | Scenario slice covering only `clean_acceptance`. Not a full canonical Gold package. |
| `scenario-policy-rejection.json` | 1 | Scenario slice covering only `policy_rejection`. Not a full canonical Gold package. |
| `scenario-challenge-filed.json` | 1 | Scenario slice covering only `challenge_filed`. Not a full canonical Gold package. |
| `scenario-withdrawal.json` | 1 | Scenario slice covering only `withdrawal`. Not a full canonical Gold package. |
| `scenario-supersession.json` | 1 | Scenario slice covering only `supersession`. Not a full canonical Gold package. Uses `prior_decision_ref_kind: external_decision_id`. |

The five scenario-slice fixtures exist to verify scenario-isolated
paths under the schema's 1..5 entry tolerance. They are NOT a
substitute for the canonical fixture and do not claim to represent a
full v0.4.0 Minimal Gold Governed Reliance Demo body.

Each scenario-slice fixture has a unique `package_id`,
`governed_reliance_demo_id`, `decision_id`, and `generated_at` so
parallel runs do not collide.

## Schema References

- Package body schema: `schemas/gold-governed-reliance-package-v0.1.0.md`
- Manifest schema: `schemas/gold-governed-reliance-package-manifest-v0.1.0.md`
- Conformance report schema: `schemas/gold-governed-reliance-conformance-report-v0.1.0.md`

## Closed Vocabulary Coverage

The canonical fixture covers, across its five decisions:

- All five `scenario_type` values
- All five `decision_status` values
- All three `decision_subject.subject_type` values
- Five distinct `policy_decision` values (`allow`, `deny`, `review`, `withhold`, `conditional`)
- Five distinct `decision_trigger` values
- Five distinct `protected_action_id` values
- Five distinct `action_category` values
- Two distinct `action_environment` values (`demo`, `production_simulated`)

The scenario slices cover their respective scenario in isolation. The
supersession slice uses `prior_decision_ref_kind: external_decision_id`
to exercise the "prior decision outside this package" path permitted by
the schema. The canonical fixture uses `internal_decision_id` and its
`prior_decision_id` resolves to `decision-001-accepted` inside the
same package.

## Non-Claims

These fixtures record local hand-authored governed reliance decision
records. They do not represent live decisions, signed evidence,
external acceptance, certification, or any form of full Gold,
Platinum, or production governance.
