# Gold Challenge Lifecycle Report Schema v0.1.0

Schema for the Gold v0.4.3 Challenge Lifecycle Lite report artifact.
A lifecycle report is a deterministic byte-re-derivable local
projection of a hand-authored v0.4.3 lifecycle records body, anchored
to the v0.4.2 policy evaluation report and the v0.4.1 decision report,
and produced as subject [6] of the v0.4.3 manifest.

## Boundary

The lifecycle report is a local hand-derived projection, not signed,
not a certificate, not federated, not full Gold. It re-projects the
v0.4.3 records body once-per-record into a stable row table with a
small coverage rollup. It does not consult any live policy engine,
does not transfer reliance, and is not an external acceptance
statement.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.challenge_lifecycle_report`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Closed set `{gold.challenge_lifecycle_lite.v0.4.3}`. |
| `challenge_lifecycle_report_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Mirrored by the manifest's `challenge_lifecycle_report_id`. Subject to the v0.4.3 6-ID pairwise-distinct collision class. |
| `lifecycle_record_set_id` | string | yes | Same grammar. Must equal the records body's `lifecycle_record_set_id` and the manifest's `challenge_lifecycle_record_set_id`. |
| `package_id` | string | yes | Same grammar. Cross-anchor to the v0.4.0 body, v0.4.1 decision report, v0.4.2 matrix, v0.4.2 policy evaluation report, and v0.4.3 records body. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchor to the same five documents. |
| `policy_evaluation_report_id` | string | yes | Same grammar. Must equal the v0.4.2 policy evaluation report's top-level `policy_evaluation_report_id` and the manifest's `policy_evaluation_report_id`. Subject to the 6-ID collision class. |
| `source_records_sha256` | string | yes | Bare lowercase hex SHA-256 of the runtime records body bytes (subject [5] of the v0.4.3 manifest). No `sha256:` prefix. |
| `source_policy_evaluation_report_sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.2 policy evaluation report bytes (subject [4] of the v0.4.3 manifest). |
| `source_decision_report_sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.1 decision report bytes (subject [2] of the v0.4.3 manifest). |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. Equal to the records body's runtime `generated_at`. |
| `lifecycle_rows` | array of objects | yes | One row per record, in records-body input order. |
| `coverage_summary` | object | yes | Deterministic rollup over `lifecycle_rows`. |
| `report_fingerprint` | string | yes | Bare lowercase hex SHA-256 over the canonical-JSON serialization of the report body excluding this `report_fingerprint` field itself. |

## lifecycle_rows[]

Exactly one row per record in `lifecycle_records[]`, preserving the
records body's input order.

| Field | Type | Required | Notes |
|---|---|---|---|
| `row_id` | string | yes | Closed grammar `^lc_row_[0-9]{2}$`. Assigned by stable position: row index N in records body input order receives `lc_row_<NN>` (1-based, zero-padded width 2). |
| `lifecycle_id` | string | yes | Equal to the records body's `lifecycle_records[N].lifecycle_id`. |
| `target_decision_id` | string | yes | Equal to the records body's `lifecycle_records[N].target_decision_id`. |
| `target_decision_row_id` | string | yes | Equal to the records body's `lifecycle_records[N].target_decision_row_id`. Closed grammar `^row_[0-9]{2}$`. |
| `current_status` | string | yes | Equal to the records body's `lifecycle_records[N].current_status`. Closed set `{filed | acknowledged | under_review | resolved_locally | superseded | withdrawn}`. |
| `is_terminal` | boolean | yes | `true` iff `current_status ∈ {resolved_locally, superseded, withdrawn}`. |
| `event_count` | integer | yes | Length of the records body's `lifecycle_records[N].events`. |
| `first_event_id` | string | yes | Equal to `events[0].event_id`. |
| `final_event_id` | string | yes | Equal to `events[event_count - 1].event_id`. |
| `final_event_timestamp` | string | yes | Equal to `events[event_count - 1].event_timestamp`. |
| `lifecycle_fingerprint` | string | yes | Equal to the records body's `lifecycle_records[N].lifecycle_fingerprint`. Re-included verbatim; not recomputed at projection time. |

## coverage_summary

A fixed-shape rollup. Numeric fields are non-negative integers.

| Field | Type | Required | Notes |
|---|---|---|---|
| `lifecycle_record_count` | integer | yes | Length of `lifecycle_rows`. |
| `lifecycle_event_count` | integer | yes | Sum of `lifecycle_rows[*].event_count`. |
| `open_lifecycle_count` | integer | yes | Count of rows with `is_terminal == false`. |
| `terminal_lifecycle_count` | integer | yes | Count of rows with `is_terminal == true`. Must equal `lifecycle_record_count - open_lifecycle_count`. |
| `status_value_count` | object | yes | Map with exactly the six keys `filed`, `acknowledged`, `under_review`, `resolved_locally`, `superseded`, `withdrawn`. Each value is the count of rows whose `current_status` equals the key. Keys with no occurrences carry the value `0`. Sum of values must equal `lifecycle_record_count`. |

## Cross-Anchor Rules

- `package_id`, `governed_reliance_demo_id`,
  `policy_evaluation_report_id`, and `lifecycle_record_set_id` must
  satisfy the cross-document anchors listed above.
- `source_records_sha256`, `source_policy_evaluation_report_sha256`,
  and `source_decision_report_sha256` must equal the v0.4.3 manifest's
  `subjects[5].sha256`, `subjects[4].sha256`, and `subjects[2].sha256`
  respectively.
- For each row N, `(target_decision_id, target_decision_row_id)` must
  identify the same single v0.4.1 decision report row.
- `lifecycle_rows` length must equal the records body's
  `lifecycle_records` length, and row order must match records body
  input order one-to-one.

## Deterministic Serialization

The v0.4.3 runner serializes the lifecycle report with
`json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"`. The
report is byte-re-derivable: running the runner twice over the same
records body and the same `--generated-at` must produce identical
bytes. All SHA-256 values are bare lowercase hex (64 characters,
`[0-9a-f]{64}`) with no `sha256:` label prefix.

## Verifier Reachability Summary (v0.4.3 lifecycle-report-body reasons)

The v0.4.3 verifier emits the lifecycle-report-body-level reasons in
the order documented under `tools/gold/README.md` (v0.4.3 section).
The report-body-relevant subset of the closed 48-reason public
taxonomy is:

- `gold_challenge_lifecycle_report_not_object` — the lifecycle report
  subject is not a JSON object (top-level array, scalar, or null).
- `gold_challenge_lifecycle_report_schema_invalid` — lifecycle report
  body shape / required-field / grammar defects: wrong
  `document_type`, wrong `schema_version`, `profile` outside the
  closed supported set, missing or malformed top-level field,
  `lifecycle_rows` not a list, per-row scalar shape defects unrelated
  to projection, `coverage_summary` shape defects,
  `status_value_count` key set or sum-shape violations,
  `is_terminal` not a boolean, `event_count` not a non-negative
  integer, `report_fingerprint` not bare lowercase hex.
- `gold_challenge_lifecycle_report_binding_invalid` — failures of
  `lifecycle_record_set_id`, `policy_evaluation_report_id`,
  `challenge_lifecycle_report_id`, `source_records_sha256`,
  `source_policy_evaluation_report_sha256`,
  `source_decision_report_sha256`, `package_id`, or
  `governed_reliance_demo_id` anchoring; 6-ID collision-class
  violations involving `challenge_lifecycle_report_id`.
- `gold_challenge_lifecycle_projection_invalid` — projection
  disagreement between the lifecycle report and a deterministic
  re-projection of the records body bytes carried by the manifest:
  row count, row order, per-row scalar mismatches (row_id,
  lifecycle_id, target_decision_id, target_decision_row_id,
  current_status, is_terminal, event_count, first_event_id,
  final_event_id, final_event_timestamp), wrong target binding at
  the row level, or wrong per-row `lifecycle_fingerprint`
  re-inclusion. The lifecycle row schema has no `effect` field; the
  per-row projection does not carry a per-row lifecycle_effect, so
  effect-projection mismatches are not in scope for this reason.
  Top-level `report_fingerprint` mismatch (canonical-JSON re-derivation
  over the report body excluding the fingerprint field) also routes
  to this reason; that sub-check is deliberately non-monotonic
  relative to the R48 coverage-summary re-derivation (see
  Reachability ordering).
- `gold_challenge_lifecycle_summary_invalid` — coverage_summary
  rollup disagreement with an independent re-derivation over
  `lifecycle_rows[]`: incorrect `lifecycle_record_count`,
  `lifecycle_event_count`, `open_lifecycle_count`,
  `terminal_lifecycle_count`, or `status_value_count` value
  mismatches (key set otherwise well-formed; values disagree with
  the row population).

Reachability ordering for the lifecycle report body is **not strictly
monotonic** in the public-token integer suffix. The natural-order
checks fire as: not-object (R44) first, schema-shape (R45) second,
binding (R46) third, row-level projection-derivation (R47) fourth,
coverage-summary derivation (R48) fifth. After R48 passes, the
verifier re-derives the top-level `report_fingerprint` (canonical
JSON of the report excluding the fingerprint field, SHA-256, bare
lowercase hex) and compares it against the declared value; a
mismatch surfaces under R47 (`gold_challenge_lifecycle_projection_invalid`).
The post-R48 R47 sub-check is a deliberate non-masking placement so
that row-level projection mismatches (R47) and coverage-summary
mismatches (R48) remain reachable on unmodified-fingerprint inputs;
the R47 public-token integer suffix is therefore not a strict
emission order. The R45 hex-shape check above only constrains the
declared `report_fingerprint` bytes' format, not their byte-equality
to the canonical re-derivation.

## Non-Claims

The lifecycle report is not signed, not a certificate, not federated,
not a transfer of reliance to any external party, does not consult
any live policy engine, and is not Gold certification. It is a
deterministic local projection of the v0.4.3 records body for the
Challenge Lifecycle Lite package.
