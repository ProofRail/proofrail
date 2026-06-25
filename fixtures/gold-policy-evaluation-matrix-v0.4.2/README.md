# Gold Policy Evaluation Matrix v0.4.2 Fixture Pack

This directory holds the canonical hand-authored template for the
v0.4.2 Minimal Gold Policy Evaluation Matrix consumed by the v0.4.2
runner.

These fixtures are deterministic local hand-authored JSON inputs.
They are NOT signed, NOT certified, NOT a transfer of reliance, NOT
live policy-engine output, and NOT full Gold.

## Files

| Path | Rows | Role |
|---|---|---|
| `policy-evaluation-matrix.json` | 5 | **Canonical v0.4.2 matrix template.** One matrix row per recognized scenario in natural order: clean acceptance, policy rejection, challenge filed, withdrawal, supersession. |

## Template vs Runtime Matrix

The hand-authored matrix on disk in this directory is a **template**,
not a complete runtime matrix. The template contains every
substantive field that the v0.4.2 runner does not derive at runtime:

- `document_type`, `schema_version`, `profile`
- `matrix_id`, `package_id`, `governed_reliance_demo_id`
- `decision_report_ref`
- `policy_pack_id`, `policy_pack_version`
- `matrix_rows[]` (the hand-authored policy expectations)
- `scope_limitations`, `non_claims`

The runner injects two runtime-bound scalar fields into the runtime
matrix written under `subject [3]`:

- `decision_report_sha256` — bare lowercase hex SHA-256 of the
  derived v0.4.1 decision-report bytes (subject [2]).
- `generated_at` — ISO-8601 UTC timestamp supplied to the runner via
  CLI argument.

The fixture omits both fields. The fixture is therefore NOT directly
verifier-ready; running the v0.4.2 verifier against the fixture
would surface `gold_policy_matrix_schema_invalid` (missing required
field). The fixture is intended only as runner input. The runner's
job is to produce the final runtime matrix at subject [3] by reading
this template, validating its substance, and injecting the two
runtime-bound scalars.

## Schema References

- Matrix schema: `schemas/gold-policy-evaluation-matrix-v0.1.0.md`
- Evaluation report schema: `schemas/gold-policy-evaluation-report-v0.1.0.md`
- Manifest schema: `schemas/gold-policy-evaluation-matrix-package-manifest-v0.1.0.md`

The matrix template's hand-authored content aligns with the canonical
v0.4.0 fixture `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`
(five decisions, one per recognized scenario, in natural order). The
runner is expected to derive a v0.4.1 decision report from that v0.4.0
fixture and then evaluate this matrix template against the decision
report rows.

## Closed Vocabulary Coverage

The five matrix rows in the canonical template cover, across all
rows:

- All five `expected_scenario_type` values
- All five `expected_decision_status` values
- All five `evaluation_effect` values
- All five `row_rationale_code` values
- Five distinct `expected_policy_decision` values (`allow`, `deny`,
  `review`, `withhold`, `conditional`)
- Five distinct `expected_action_category` values
- Two distinct `expected_action_environment` values (`demo`,
  `production_simulated`)
- All three `required_subject_type` values

This intentionally mirrors the v0.4.0 canonical fixture's coverage so
that a clean Phase 2 smoke run produces five `matched` evaluation
rows, zero `matrix_row_unmatched`, zero `decision_row_uncovered`,
and zero `matrix_conflict_detected`.

## Non-Claims

This fixture records local hand-authored policy expectations. It
does not represent live policy-engine output, signed evidence,
external acceptance, certification, or any form of full Gold,
Platinum, or production governance. The fixture is consumed by the
v0.4.2 runner; it is not itself a v0.4.2 release artifact.
