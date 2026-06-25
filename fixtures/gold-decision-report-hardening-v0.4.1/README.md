# Gold Decision Report Hardening v0.4.1 Fixture Pack

This directory holds the fixture index for the v0.4.1 Gold Decision
Report Hardening runner and verifier. v0.4.1 deliberately does NOT
duplicate the v0.4.0 governed reliance package body fixtures; the
v0.4.1 runner consumes them in place from the v0.4.0 fixture pack.

These fixtures and the v0.4.0 fixtures they reference are
deterministic local hand-authored JSON inputs. They are NOT signed,
NOT certified, NOT a transfer of reliance, and NOT full Gold.

## Inputs Reused from v0.4.0

The v0.4.1 runner consumes the same governed reliance package body
fixtures as v0.4.0. v0.4.1 introduces no new package-body fixtures
and no new variant package-body fixtures.

| Input role | Path | Notes |
|---|---|---|
| Canonical 5-scenario fixture | `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json` | The only fixture that represents a full canonical v0.4.0 Minimal Gold Governed Reliance Demo body. v0.4.1 canonical Decision Report Hardening runs use this fixture. |
| `clean_acceptance` slice | `fixtures/gold-governed-reliance-v0.4.0/scenario-clean-acceptance.json` | Scenario slice. 1-decision package body. |
| `policy_rejection` slice | `fixtures/gold-governed-reliance-v0.4.0/scenario-policy-rejection.json` | Scenario slice. 1-decision package body. |
| `challenge_filed` slice | `fixtures/gold-governed-reliance-v0.4.0/scenario-challenge-filed.json` | Scenario slice. 1-decision package body. |
| `withdrawal` slice | `fixtures/gold-governed-reliance-v0.4.0/scenario-withdrawal.json` | Scenario slice. 1-decision package body. |
| `supersession` slice | `fixtures/gold-governed-reliance-v0.4.0/scenario-supersession.json` | Scenario slice with `prior_decision_ref_kind: external_decision_id`. 1-decision package body. |

The v0.4.0 fixture pack README at
`fixtures/gold-governed-reliance-v0.4.0/README.md` documents the
shape and closed-vocabulary coverage of these inputs.

## v0.4.1 Decision Report Hardening Outputs

For each v0.4.0 package body input, the v0.4.1 runner emits a
3-subject package under the runner's `--output-dir`:

```text
<output-dir>/
  governed-reliance-scenarios.json                          (subject [0] — byte copy of input)
  silver-gold-governed-reliance-conformance-report.json     (subject [1] — derived v0.4.0 conformance report)
  gold-governed-reliance-decision-report.json               (subject [2] — derived v0.4.1 decision report)
  gold-decision-report-package-manifest.json                (3-subject manifest)
```

The decision report is a normalized projection of `governed_decisions[]`
plus a derived coverage summary; it does not introduce facts beyond
the source package body. The verifier re-derives the decision report
from the package body byte-for-byte.

## Schema References

- v0.4.0 package body schema: `schemas/gold-governed-reliance-package-v0.1.0.md`
- v0.4.0 conformance report schema: `schemas/gold-governed-reliance-conformance-report-v0.1.0.md`
- v0.4.1 decision report schema: `schemas/gold-governed-reliance-decision-report-v0.1.0.md`
- v0.4.1 manifest schema: `schemas/gold-decision-report-package-manifest-v0.1.0.md`

## Closed Vocabulary Coverage (Inherited)

The canonical fixture covers, across its five decisions:

- All five `scenario_type` values
- All five `decision_status` values
- All three `decision_subject.subject_type` values
- Five distinct `policy_decision` values
- Five distinct `decision_trigger` values
- Five distinct `protected_action_id` values
- Five distinct `action_category` values
- Two distinct `action_environment` values

For a canonical-fixture run, the v0.4.1 decision report's
`coverage_summary` carries 5-element `*_present` arrays for
scenario_types_present, decision_statuses_present,
protected_actions_present, and policy_decisions_present, and a
5-element `registry_roles_present` if the canonical fixture binds
five distinct roles (or fewer if the canonical fixture reuses a
role).

For a scenario-slice run, every `*_present` array has exactly one
element.

## Non-Claims

The v0.4.1 fixture index records that the v0.4.1 runner consumes
existing v0.4.0 hand-authored governed reliance package body
fixtures. v0.4.1 does not introduce new package-body fixtures, does
not represent live decisions, does not represent signed evidence, and
does not represent external acceptance, certification, or any form of
full Gold, Platinum, or production governance. The v0.4.1 decision
report is a normalized projection of the v0.4.0 package body and
nothing more.
