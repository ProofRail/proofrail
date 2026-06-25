# Gold Policy Evaluation Report Schema v0.1.0

Schema for the Gold v0.4.2 policy evaluation report (subject [4] in
the v0.4.2 package manifest). The report is a deterministic local
derivation that binds each row of the v0.4.2 policy evaluation matrix
to one row of the v0.4.1 decision report, or to an explicit closed
miss status. The runner derives the report from the matrix bytes and
decision-report bytes; the verifier re-derives it byte-for-byte from
the same inputs.

## Boundary

The report records the local outcome of evaluating the hand-authored
matrix against the decision report. It is not a live policy engine
output, not a certification, not signed, not federated, not legally
binding, and not full Gold. It does not re-evaluate the substantive
merits of any upstream Silver evidence and does not authorize
external acceptance or production reliance.

The report's byte image depends only on the matrix bytes, the
decision-report bytes, and the manifest-supplied
`policy_evaluation_report_id` / `generated_at`. The report introduces
no facts that are not already in the matrix or decision report.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.policy_evaluation_report`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Must be in the closed set `{gold.policy_evaluation_matrix.v0.4.2}`. |
| `package_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Cross-anchored to package body, decision report, matrix, and manifest. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to package body, decision report, matrix, and manifest. |
| `matrix_id` | string | yes | Same grammar. Cross-anchored to the matrix's `matrix_id` and the manifest's `matrix_id`. |
| `policy_evaluation_report_id` | string | yes | Same grammar. Cross-anchored to the manifest's `policy_evaluation_report_id`. MUST NOT equal `decision_report_ref`, `conformance_report_ref` (if present in the manifest), or `matrix_id`. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `source_decision_report_sha256` | string | yes | Bare lowercase hex SHA-256 of the decision-report bytes (subject [2]). No `sha256:` label prefix. |
| `source_matrix_sha256` | string | yes | Bare lowercase hex SHA-256 of the matrix bytes (subject [3]). No `sha256:` label prefix. |
| `evaluation_rows` | array of objects | yes | Length 1..15. See "Evaluation Row Shape". |
| `coverage_summary` | object | yes | Derived. See "Coverage Summary". |
| `scope_limitations` | array of non-empty strings | yes | Non-empty. Mirrored from the matrix. |
| `non_claims` | array of non-empty strings | yes | Non-empty. Mirrored from the matrix. |

## Evaluation Row Shape

Each entry in `evaluation_rows[]` records exactly one of:

- a matrix row matched to a decision row (`evaluation_status = matched`);
- a matrix row with no matching decision row (`matrix_row_unmatched`);
- a decision row with no matching matrix row (`decision_row_uncovered`);
- a matrix conflict where multiple matrix rows match one decision row
  with disagreeing `evaluation_effect` or `row_rationale_code`
  (`matrix_conflict_detected`).

| Field | Type | Required | Notes |
|---|---|---|---|
| `evaluation_row_id` | string | yes | `erow_NN` where `NN` is `01`..`15`, assigned in derived order. |
| `matrix_row_id` | string \| null | yes | The matrix row's `matrix_row_id`, or `null` for `decision_row_uncovered`. |
| `decision_id` | string \| null | yes | The decision row's `decision_id`, or `null` for `matrix_row_unmatched`. |
| `decision_row_id` | string \| null | yes | The decision row's `row_id`, or `null` for `matrix_row_unmatched`. |
| `scenario_type` | string \| null | yes | The matched (or sole-side) `scenario_type`, or `null` if no side present. |
| `decision_status` | string \| null | yes | The matched (or sole-side) `decision_status`, or `null` if no side present. |
| `policy_clause_ref` | string \| null | yes | The matrix row's `policy_clause_ref`, or `null` for `decision_row_uncovered`. |
| `policy_decision` | string \| null | yes | The matched (or sole-side) `policy_decision`, or `null` if no side present. |
| `action_category` | string \| null | yes | The matched (or sole-side) `action_category`, or `null` if no side present. |
| `action_environment` | string \| null | yes | The matched (or sole-side) `action_environment`, or `null` if no side present. |
| `decision_authority_role` | string \| null | yes | The matched (or sole-side) `decision_authority_role`, or `null` if no side present. |
| `subject_type` | string \| null | yes | The matched (or sole-side) `subject_type`, or `null` if no side present. |
| `evaluation_status` | string | yes | Closed set `{matched, matrix_row_unmatched, decision_row_uncovered, matrix_conflict_detected}`. |
| `evaluation_effect` | string \| null | yes | The matrix row's `evaluation_effect` for `matched` and `matrix_conflict_detected`, or `null` for `matrix_row_unmatched` and `decision_row_uncovered`. |
| `evaluation_fingerprint` | string | yes | Derived. Bare lowercase hex SHA-256. See "Evaluation Fingerprint". |

## Row Derivation Algorithm

The runner derives `evaluation_rows[]` deterministically by the
following procedure. The verifier re-runs the same procedure and
compares the resulting bytes byte-for-byte to the report on disk.

1. For each `decision_rows[]` entry in the decision report, in
   source order, collect the set of `matrix_rows[]` entries whose
   `expected_scenario_type`, `expected_decision_status`,
   `expected_policy_decision`, `expected_action_category`,
   `expected_action_environment`,
   `expected_decision_authority_role`, and `required_subject_type`
   match the decision row's mirrored fields exactly, and whose
   `policy_clause_ref` appears in the decision row's
   `policy_binding.policy_clause_refs`.
2. If exactly one matrix row matches a decision row: emit one
   `matched` evaluation row binding both.
3. If two or more matrix rows match one decision row and they agree
   on `evaluation_effect` and `row_rationale_code`: emit one
   `matched` evaluation row for the first matching matrix row in
   declared order. (Agreement folds.)
4. If two or more matrix rows match one decision row and they
   disagree on either `evaluation_effect` or `row_rationale_code`:
   emit one `matrix_conflict_detected` evaluation row for the first
   matching matrix row in declared order.
5. If no matrix row matches a decision row: emit one
   `decision_row_uncovered` evaluation row with the decision row's
   identifying fields.
6. After all decision rows are processed, for each `matrix_rows[]`
   entry whose `matrix_row_id` did NOT appear in any emitted
   `matched` or `matrix_conflict_detected` row, in declared order:
   emit one `matrix_row_unmatched` evaluation row with the matrix
   row's identifying fields.

The `evaluation_row_id` values (`erow_01`, `erow_02`, ...) are
assigned in the order rows are emitted by the procedure above.

## Evaluation Fingerprint

`evaluation_fingerprint` is the bare lowercase hex SHA-256 over the
canonical JSON bytes of a fixed projection of the evaluation row.
The projection is the ordered object:

```text
{
  "matrix_row_id":           <or null>,
  "decision_id":             <or null>,
  "decision_row_id":         <or null>,
  "scenario_type":           <or null>,
  "decision_status":         <or null>,
  "policy_clause_ref":       <or null>,
  "policy_decision":         <or null>,
  "action_category":         <or null>,
  "action_environment":      <or null>,
  "decision_authority_role": <or null>,
  "subject_type":            <or null>,
  "evaluation_status":       <string>,
  "evaluation_effect":       <or null>
}
```

Canonical JSON serialization:

```python
json.dumps(projection_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The runner computes the SHA-256 of the resulting UTF-8 bytes and
emits the bare lowercase hex digest as `evaluation_fingerprint`. The
verifier re-derives the projection and digest the same way and
compares byte-for-byte. The fingerprint does not include the
runner-derived `evaluation_row_id`.

## Coverage Summary

`coverage_summary` is fully derived from `evaluation_rows[]`. The
runner constructs it deterministically; the verifier re-derives it
the same way and compares byte-for-byte.

| Field | Type | Required | Notes |
|---|---|---|---|
| `decision_row_count` | integer | yes | Number of distinct `decision_row_id` values appearing under `matched`, `matrix_conflict_detected`, or `decision_row_uncovered` evaluation rows. Must equal the decision report's `decision_count`. |
| `matrix_row_count` | integer | yes | Number of distinct `matrix_row_id` values declared in the matrix. Must equal the length of `matrix_rows[]`. |
| `matched_count` | integer | yes | Number of evaluation rows with `evaluation_status = matched`. |
| `unmatched_matrix_row_count` | integer | yes | Number of evaluation rows with `evaluation_status = matrix_row_unmatched`. |
| `uncovered_decision_row_count` | integer | yes | Number of evaluation rows with `evaluation_status = decision_row_uncovered`. |
| `conflict_count` | integer | yes | Number of evaluation rows with `evaluation_status = matrix_conflict_detected`. |
| `aggregate_evaluation_fingerprint` | string | yes | Bare lowercase hex SHA-256. See "Aggregate Evaluation Fingerprint". |

None of the seven `coverage_summary` field names end in a suffix
that the v0.4.2 regression-test reason-like filter recognizes
(`_present`, `_missing`, `_invalid`, `_failed`, `_forbidden`,
`_unsupported`, `_not_object`). The v0.4.2 TG1 allowlist is empty.

### Aggregate Evaluation Fingerprint

`aggregate_evaluation_fingerprint` is the bare lowercase hex SHA-256
over the canonical JSON bytes of the ordered list of per-row
fingerprints:

```text
[evaluation_rows[0].evaluation_fingerprint,
 evaluation_rows[1].evaluation_fingerprint,
 ...,
 evaluation_rows[N-1].evaluation_fingerprint]
```

Canonical JSON serialization:

```python
json.dumps(fingerprint_list, sort_keys=True, separators=(",", ":")) + "\n"
```

`sort_keys` is irrelevant for a list; the ordering of fingerprints
in the list itself is the row order (matching `evaluation_rows[]`).
The runner emits the bare lowercase hex digest of the resulting
UTF-8 bytes.

## Deterministic Serialization

The v0.4.2 runner serializes the policy evaluation report with:

```python
json.dumps(report_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The verifier re-derives the entire report from the matrix bytes and
decision-report bytes plus the manifest-supplied
`policy_evaluation_report_id` / `generated_at`, using a
byte-identical serializer. Any byte disagreement surfaces as
`gold_policy_evaluation_result_invalid` (per-row drift) or
`gold_policy_evaluation_summary_invalid` (coverage-summary drift),
as appropriate. Top-level structural disagreement before either of
those checks surfaces as `gold_policy_evaluation_report_not_object`
or `gold_policy_evaluation_report_schema_invalid`.

## Cross-Anchor Rules

- `package_id` / `governed_reliance_demo_id` must equal the package
  body's, decision report's, matrix's, and manifest's values.
- `matrix_id` must equal the matrix's `matrix_id` and the manifest's
  `matrix_id`.
- `policy_evaluation_report_id` must equal the manifest's
  `policy_evaluation_report_id`.
- `policy_evaluation_report_id` MUST NOT equal `decision_report_ref`,
  `conformance_report_id` (in the manifest), or `matrix_id`.
- `source_decision_report_sha256` must equal the manifest's
  `subjects[2].sha256`.
- `source_matrix_sha256` must equal the manifest's
  `subjects[3].sha256`.

A failure of any of these cross-anchor rules surfaces as
`gold_policy_evaluation_report_binding_invalid` (binding-folding
rule; not a new public reason).

## Verifier Notes

The policy-evaluation-report-specific checks run AFTER:

- the v0.4.2 manifest integrity checks have passed;
- the inherited v0.4.1 decision-report-hardening checks have passed
  via subprocess delegation;
- the v0.4.2 matrix checks have passed.

The v0.4.2-introduced ordered checks (in fixed order) are:

```text
check_30  gold_policy_matrix_not_object
check_31  gold_policy_matrix_schema_invalid
check_32  gold_policy_matrix_binding_invalid
check_33  gold_policy_matrix_entry_invalid
check_34  gold_policy_evaluation_report_not_object
check_35  gold_policy_evaluation_report_schema_invalid
check_36  gold_policy_evaluation_report_binding_invalid
check_37  gold_policy_evaluation_result_invalid
check_38  gold_policy_evaluation_summary_invalid
```

Each defect surfaces with its dedicated reason and is not aliased
into adjacent reasons. The nine reasons are reachable independently;
no v0.4.2-introduced defect collapses into one of the inherited 29
v0.4.0 / v0.4.1 reasons or into `gold_manifest_invalid`.

## Non-Claims

The policy evaluation report is not signed, not certified, not
approved, not audited, not a legal instrument, not a transfer of
reliance, not production governance, not federation, not live policy
engine output, and not full Gold. It records the local outcome of
evaluating a hand-authored matrix against the v0.4.1 decision
report's rows, binds that outcome by bare lowercase hex SHA-256 hash
anchors to the matrix and decision-report bytes, and reports a
derived coverage summary. It does not re-evaluate the upstream
Silver evidence, does not opine on policy correctness, does not
adjudicate any specific decision, and does not authorize external
acceptance or production reliance.
