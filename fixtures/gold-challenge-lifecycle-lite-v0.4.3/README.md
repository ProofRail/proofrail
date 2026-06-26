# Gold Challenge Lifecycle Lite v0.4.3 Fixture Pack

This directory holds the canonical hand-authored template for the
v0.4.3 Minimal Gold Challenge Lifecycle Lite records body consumed by
the v0.4.3 runner.

These fixtures are deterministic local hand-authored JSON inputs.
They are NOT signed, NOT certified, NOT a transfer of reliance, NOT
live policy-engine output, and NOT full Gold.

## Files

| Path | Records | Role |
|---|---|---|
| `challenge-lifecycle-records.json` | 5 | **Canonical v0.4.3 records template.** One lifecycle record per v0.4.0 governed decision row, in natural order: clean acceptance, policy rejection, challenge filed, withdrawal, supersession. |

## Template vs Runtime Records Body

The hand-authored records body on disk in this directory is a
**template**, not a complete runtime records body. The template
contains every substantive field that the v0.4.3 runner does not
derive at runtime:

- `document_type`, `schema_version`, `profile`
- `lifecycle_record_set_id`, `package_id`, `governed_reliance_demo_id`
- `policy_evaluation_report_ref`
- `lifecycle_records[]` (the hand-authored lifecycle records, each
  with its `lifecycle_id`, `target_decision_id`,
  `target_decision_row_id`, `current_status`, `events[]`, and any
  conditional terminal-status refs)

The runner injects three runtime-bound values into the runtime
records body written under `subject [5]`:

- `policy_evaluation_report_sha256` (top-level) — bare lowercase hex
  SHA-256 of the derived v0.4.2 policy evaluation report bytes
  (subject [4]).
- `generated_at` (top-level) — ISO-8601 UTC timestamp supplied to the
  runner via CLI argument.
- `lifecycle_fingerprint` (per record in `lifecycle_records[]`) —
  bare lowercase hex SHA-256 over the canonical-JSON serialization of
  the record body excluding this `lifecycle_fingerprint` field itself.

The template omits all three. The template is therefore NOT directly
verifier-ready; running the v0.4.3 verifier against the template
would surface `gold_challenge_lifecycle_records_schema_invalid`
(missing required field). The template is intended only as runner
input. The
runner's job is to produce the final runtime records body at subject
[5] by reading this template, validating its substance, injecting the
three runtime-bound values, and writing the records body bytes in
canonical-JSON form.

## Schema References

- Records schema: `schemas/gold-challenge-lifecycle-records-v0.1.0.md`
- Lifecycle report schema: `schemas/gold-challenge-lifecycle-report-v0.1.0.md`
- Manifest schema: `schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md`

The records template's hand-authored content aligns with the
canonical v0.4.0 fixture
`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`
(five decisions, one per recognized scenario, in natural order). The
runner is expected to subprocess-delegate v0.4.2 (which itself
delegates v0.4.1 and v0.4.0) to derive the inherited five subjects,
then consume this records template to produce subjects [5] and [6].

## Lifecycle Shape Coverage

The five lifecycle records in the canonical template are aligned 1:1
with the v0.4.1 decision report rows (`row_01` through `row_05`),
which themselves project the v0.4.0 decisions (`decision-001-accepted`
through `decision-005-superseded`) in stable input order.

The hand-authored shapes are:

| Lifecycle | target_decision_id | row_id | current_status | events | terminal? | terminal ref |
|---|---|---|---|---|---|---|
| `lc-001` | `decision-001-accepted` | `row_01` | `filed` | 1 | no | — |
| `lc-002` | `decision-002-rejected` | `row_02` | `acknowledged` | 2 | no | — |
| `lc-003` | `decision-003-challenged` | `row_03` | `resolved_locally` | 4 | yes | `local_resolution_ref` |
| `lc-004` | `decision-004-withdrawn` | `row_04` | `withdrawn` | 3 | yes | `withdrawal_record_ref` |
| `lc-005` | `decision-005-superseded` | `row_05` | `superseded` | 2 | yes | `superseding_decision_id` |

Total: 12 events across 5 records, 2 open lifecycles, 3 terminal
lifecycles. The six `current_status` values are reachable as
follows: `filed`, `acknowledged`, `resolved_locally`, `superseded`,
and `withdrawn` each appear as the record-level `current_status` of
exactly one record; `under_review` appears only as an intermediate
`event_status` inside `lc-003`'s event chain (no record has
`current_status == under_review` in the canonical template). All 6
`event_status` values appear at least once in `events[]` across the
five records; all 6 `event_basis` values appear at least once; all 4
`actor_role` values appear at least once; all 4 `lifecycle_effect`
values (including `challenge_open`) appear at least once.

This intentionally mirrors the v0.4.2 canonical fixture's coverage
pattern so that a clean Phase 2 smoke run produces five projected
lifecycle rows, zero binding mismatches, zero projection
disagreements, zero collision-class violations, and a
`coverage_summary.status_value_count` map whose six values sum to 5
with the distribution `{filed: 1, acknowledged: 1, under_review: 0,
resolved_locally: 1, superseded: 1, withdrawn: 1}`.

## Closed Vocabulary Coverage

The five lifecycle records in the canonical template cover, across
all records and their events:

- All 6 `current_status` values reachable as either a record-level
  `current_status` or an intermediate `event_status`
  (`filed`, `acknowledged`, `under_review`, `resolved_locally`,
  `superseded`, `withdrawn`).
- All 6 `event_status` values used as event entries.
- All 6 `event_basis` values used as event entries.
- All 4 `actor_role` values used at least once.
- All 4 `lifecycle_effect` values used at least once.
- All 3 terminal `current_status` values exercised
  (`resolved_locally`, `superseded`, `withdrawn`), each carrying its
  required record-level ref field.
- At least one outgoing transition from each non-terminal status
  (`filed`, `acknowledged`, `under_review`) is exercised in the
  closed transition graph. The five distinct transitions exercised
  by the canonical template are: `filed → acknowledged` (lc-002,
  lc-003, lc-004), `filed → superseded` (lc-005), `acknowledged →
  under_review` (lc-003), `acknowledged → withdrawn` (lc-004), and
  `under_review → resolved_locally` (lc-003). The remaining four
  transitions in the closed graph (`filed → withdrawn`,
  `acknowledged → superseded`, `under_review → withdrawn`,
  `under_review → superseded`) are exercised by regression-test
  variants, not by the canonical template.

## Non-Claims

This fixture records local hand-authored lifecycle state and event
history. It does not represent live policy-engine output, signed
evidence, external acceptance, certification, or any form of full
Gold, Platinum, or production governance. The fixture is consumed by
the v0.4.3 runner; it is not itself a v0.4.3 release artifact.
