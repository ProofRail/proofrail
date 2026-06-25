# Gold Policy Evaluation Matrix Schema v0.1.0

Schema for the Gold v0.4.2 policy evaluation matrix (subject [3] in
the v0.4.2 package manifest). The matrix is a hand-authored local
artifact that records the relying party's policy expectations over
the rows of the v0.4.1 decision report. It is consumed by the v0.4.2
runner to derive the policy evaluation report and by the v0.4.2
verifier to re-derive that report independently.

## Boundary

The matrix is a hand-authored local table. It is not a live policy
engine, not a certification system, not a transfer of reliance, not
audit evidence, not signed, and not full Gold. v0.4.2 ships local
hash anchors only.

The matrix records policy expectations over the unchanged v0.4.0
governed-reliance package body and the unchanged v0.4.1 decision
report. The matrix introduces no facts that are not already in the
package body or decision report.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.policy_evaluation_matrix`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Must be in the closed set `{gold.policy_evaluation_matrix.v0.4.2}`. |
| `matrix_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Cross-anchored to the manifest's `matrix_id`. MUST NOT equal the manifest's `decision_report_id`, `conformance_report_id`, or `policy_evaluation_report_id`. |
| `package_id` | string | yes | Same grammar. Cross-anchored to package body, decision report, and manifest. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to package body, decision report, and manifest. |
| `decision_report_ref` | string | yes | Same grammar. Must equal the decision report's `decision_report_id`. |
| `decision_report_sha256` | string | yes | Bare lowercase hex SHA-256 of the decision report bytes (subject [2]). No `sha256:` label prefix. |
| `policy_pack_id` | string | yes | Closed grammar. Mirrored from the package body's `inputs.policy_pack.policy_pack_id`. |
| `policy_pack_version` | string | yes | Mirrored from the package body's `inputs.policy_pack.policy_pack_version`. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `matrix_rows` | array of objects | yes | Length 1..10. One entry per declared policy expectation. |
| `scope_limitations` | array of non-empty strings | yes | Non-empty. v0.4.2-owned local limitations. |
| `non_claims` | array of non-empty strings | yes | Non-empty. v0.4.2-owned local non-claims. |

## Matrix Row Shape

Each entry in `matrix_rows[]` records exactly one hand-authored
policy expectation over the decision report's rows. The runner does
not invent matrix rows; the matrix is hand-authored and verifier
re-derivation is byte-for-byte over the matrix bytes already on disk.

| Field | Type | Required | Notes |
|---|---|---|---|
| `matrix_row_id` | string | yes | `mrow_NN` where `NN` is `01`..`10`, assigned in declared order. MUST be unique within `matrix_rows[]`. |
| `policy_clause_ref` | string | yes | Closed identifier grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Must reference a clause expected on a matching decision row's `policy_binding.policy_clause_refs`. |
| `expected_scenario_type` | string | yes | Closed set `{clean_acceptance, policy_rejection, challenge_filed, withdrawal, supersession}`. |
| `expected_decision_status` | string | yes | Closed set `{accepted, rejected, challenged, withdrawn, superseded}`. |
| `expected_policy_decision` | string | yes | Closed set `{allow, deny, conditional, withhold, review}`. |
| `expected_action_category` | string | yes | Closed set `{financial_release, data_export, deployment_change, secret_rotation, vendor_approval}`. |
| `expected_action_environment` | string | yes | Closed set `{demo, staging, production_simulated}`. |
| `expected_decision_authority_role` | string | yes | Closed set `{issuer, verifier, relying_party, policy_authority, revocation_source, protected_action_authority}`. |
| `required_subject_type` | string | yes | Closed set `{silver_verification_result, silver_acceptance_handoff, challenge_withdrawal_record}`. |
| `evaluation_effect` | string | yes | Closed set `{supports_decision, blocks_decision, requires_review, withholds_reliance, supersedes_prior}`. |
| `row_rationale_code` | string | yes | Closed set `{silver_pass_policy_allow, silver_pass_policy_deny, challenge_requires_review, withdrawal_requires_withhold, supersession_updates_basis}`. |

Free-text rationale is NOT an evaluated field. If present anywhere
outside `non_claims` / `scope_limitations`, free-text strings are
still subject to the prohibited-claim scan.

## Closed Set Reuse

The closed sets for `expected_scenario_type`, `expected_decision_status`,
`expected_policy_decision`, `expected_action_category`,
`expected_action_environment`, `expected_decision_authority_role`,
and `required_subject_type` are inherited verbatim from v0.4.0 and
v0.4.1. The matrix does not extend or alter those vocabularies.

## Internal Consistency Constraints

Each matrix row must internally satisfy:

- `(expected_scenario_type, expected_decision_status)` is one of the
  five paired tuples derived from the closed-set pairs:
  - `clean_acceptance` / `accepted`
  - `policy_rejection` / `rejected`
  - `challenge_filed` / `challenged`
  - `withdrawal` / `withdrawn`
  - `supersession` / `superseded`
- `(expected_scenario_type, evaluation_effect)` is one of:
  - `clean_acceptance` / `supports_decision`
  - `policy_rejection` / `blocks_decision`
  - `challenge_filed` / `requires_review`
  - `withdrawal` / `withholds_reliance`
  - `supersession` / `supersedes_prior`
- `(expected_scenario_type, row_rationale_code)` is one of:
  - `clean_acceptance` / `silver_pass_policy_allow`
  - `policy_rejection` / `silver_pass_policy_deny`
  - `challenge_filed` / `challenge_requires_review`
  - `withdrawal` / `withdrawal_requires_withhold`
  - `supersession` / `supersession_updates_basis`

A row that violates any of the three constraints above surfaces as
`gold_policy_matrix_entry_invalid`.

## Cross-Anchor Rules

- `package_id` must equal the package body's `package_id`, the
  decision report's `package_id`, and the manifest's `package_id`.
- `governed_reliance_demo_id` must equal the package body's
  `governed_reliance_demo_id`, the decision report's
  `governed_reliance_demo_id`, and the manifest's
  `governed_reliance_demo_id`.
- `decision_report_ref` must equal the decision report's
  `decision_report_id` and the manifest's `decision_report_id`.
- `decision_report_sha256` must equal the manifest's
  `subjects[2].sha256` (the bare lowercase hex SHA-256 of the
  decision-report bytes).
- `policy_pack_id` must equal the package body's
  `inputs.policy_pack.policy_pack_id`.
- `policy_pack_version` must equal the package body's
  `inputs.policy_pack.policy_pack_version`.
- `matrix_id` must equal the manifest's `matrix_id`.
- `matrix_id` MUST NOT equal the manifest's `decision_report_id`,
  `conformance_report_id`, or `policy_evaluation_report_id`.

A failure of any of these cross-anchor rules surfaces as
`gold_policy_matrix_binding_invalid` (binding-folding rule; not a
new public reason).

## Matrix Template and Runtime Matrix

The matrix is hand-authored content (`matrix_rows[]`,
`scope_limitations`, `non_claims`, `document_type`, `schema_version`,
`profile`, `matrix_id`, `package_id`, `governed_reliance_demo_id`,
`decision_report_ref`, `policy_pack_id`, `policy_pack_version`) plus
two runner-injected runtime-bound scalar fields:

- `decision_report_sha256` — bare lowercase hex SHA-256 of the
  derived v0.4.1 decision-report bytes (subject [2]). The runner
  computes the runtime decision-report bytes (byte-identically to
  v0.4.1) and injects this value before writing the runtime matrix
  to subject [3].
- `generated_at` — ISO-8601 UTC timestamp supplied to the runner via
  CLI argument. Injected before writing the runtime matrix.

The hand-authored fixture (template) supplies all other fields with
their final values. The runner does not modify the fixture in place;
it reads the fixture bytes, validates closed-set membership on
`document_type`, `schema_version`, `profile`, every row of
`matrix_rows[]`, and the cross-anchor scalars except the two
runtime-injected ones, then emits the runtime matrix at subject [3]
with the two runtime-injected scalars set.

The verifier reads subject [3] bytes from disk as-is and:

- parses the matrix as JSON;
- if the parse yields a non-object, surfaces
  `gold_policy_matrix_not_object`;
- if any required field is missing, wrongly typed, or violates the
  closed sets for `document_type`, `schema_version`, `profile`,
  surfaces `gold_policy_matrix_schema_invalid`;
- if any cross-anchor scalar disagrees with the package body, the
  decision report, the manifest, or any subject hash, surfaces
  `gold_policy_matrix_binding_invalid`;
- if any matrix row violates the per-row closed sets, the per-row
  internal consistency constraints, or has a duplicate
  `matrix_row_id`, surfaces `gold_policy_matrix_entry_invalid`.

The verifier does NOT re-derive the matrix bytes from any other
artifact; the matrix is hand-authored substantive content. The
verifier does re-derive the runtime decision-report bytes from the
package body and re-derives both runtime-injected scalars
(`decision_report_sha256`, `generated_at`) — the matrix's bound
values must equal the verifier's independently re-derived values.

## Deterministic Serialization

The v0.4.2 runner serializes the runtime matrix with:

```python
json.dumps(matrix_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The verifier byte-compares subject [3] against the same serialization
of the parsed matrix object (so reformatting drift surfaces as
`gold_manifest_invalid` through a subject [3] sha256 / size_bytes
disagreement, not as a separate matrix reason).

## Non-Claims

The matrix is not a live policy engine, not a certification record,
not signed, not federated, not legally binding, and not full Gold.
It records local hand-authored policy expectations over the v0.4.1
decision-report rows. It does not adjudicate any specific decision,
does not opine on the substantive merit of upstream Silver evidence,
and does not authorize external acceptance or production reliance.
