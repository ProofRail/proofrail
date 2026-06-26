# Gold Challenge Lifecycle Records Schema v0.1.0

Schema for the Gold v0.4.3 Challenge Lifecycle Lite records artifact.
A records document is a hand-authored deterministic local body of one
or more challenge-lifecycle records, each bound to exactly one
governed reliance decision row from the v0.4.0 package body (as
projected by the v0.4.1 decision report) and anchored against the
v0.4.2 policy evaluation report.

## Boundary

The records document is a local hand-authored body, not signed, not
a certificate, not federated, not full Gold. It records local
challenge-lifecycle state and event history over the closed v0.4.0
governed-reliance decision set. It does not consult any live policy
engine, does not transfer reliance, and does not authorize external
acceptance.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.challenge_lifecycle_records`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Closed set `{gold.challenge_lifecycle_lite.v0.4.3}`. |
| `lifecycle_record_set_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Mirrored by the manifest's `challenge_lifecycle_record_set_id` and the lifecycle report's `lifecycle_record_set_id`. |
| `package_id` | string | yes | Same grammar. Cross-anchor to the v0.4.0 governed reliance package body's `package_id`, the v0.4.1 decision report's `package_id`, the v0.4.2 matrix's `package_id`, and the v0.4.2 policy evaluation report's `package_id`. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchor to the same four documents' `governed_reliance_demo_id`. |
| `policy_evaluation_report_ref` | string | yes | Same grammar. Must equal the v0.4.2 policy evaluation report's top-level `policy_evaluation_report_id`. |
| `policy_evaluation_report_sha256` | string | yes (runtime) | Bare lowercase hex SHA-256 of the v0.4.2 policy evaluation report bytes. No `sha256:` prefix. Runtime-injected by the v0.4.3 runner. The on-disk fixture template excludes this field. |
| `generated_at` | string | yes (runtime) | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. Runtime-injected by the v0.4.3 runner from `--generated-at`. The on-disk fixture template excludes this field. |

The on-disk template includes every hand-authored field documented
above except `policy_evaluation_report_sha256`, `generated_at`, and
per-record `lifecycle_fingerprint`, which the v0.4.3 runner injects
into the runtime records body before writing it to subject [5] of the
v0.4.3 manifest.
| `lifecycle_records` | array of objects | yes | One or more records, in stable input order. Count and ordering are preserved verbatim from the input fixture. |

## lifecycle_records[]

Each record corresponds to exactly one v0.4.0 governed-reliance
decision row.

| Field | Type | Required | Notes |
|---|---|---|---|
| `lifecycle_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Distinct across all records. |
| `target_decision_id` | string | yes | Must match the `decision_id` of exactly one entry in the v0.4.0 body's `governed_decisions[]`. |
| `target_decision_row_id` | string | yes | Must match the `row_id` of the corresponding row in the v0.4.1 decision report (closed grammar `^row_[0-9]{2}$`). The `(target_decision_id, target_decision_row_id)` pair must be consistent with the v0.4.1 decision report row whose `decision_id` equals `target_decision_id`. |
| `current_status` | string | yes | Closed set `{filed | acknowledged | under_review | resolved_locally | superseded | withdrawn}`. |
| `events` | array of objects | yes | One or more events, in chronological order. Sequence MUST start with `event_status = filed`. |
| `local_resolution_ref` | string | conditional | Required iff `current_status == resolved_locally`. Closed grammar. Absent otherwise. |
| `withdrawal_record_ref` | string | conditional | Required iff `current_status == withdrawn`. Closed grammar. Absent otherwise. May reference the same withdrawal record as the v0.4.0 body's corresponding `withdrawal_record_ref`. |
| `superseding_decision_id` | string | conditional | Required iff `current_status == superseded`. Closed grammar. Must reference a distinct `decision_id` present in the v0.4.0 body's `governed_decisions[]`. |
| `lifecycle_fingerprint` | string | yes (runtime) | Bare lowercase hex SHA-256 over the canonical-JSON serialization of the record body excluding this `lifecycle_fingerprint` field itself. Runtime-injected by the v0.4.3 runner. The on-disk fixture template excludes this field. |

### events[]

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | yes | Closed grammar. Distinct within the parent record. Suggested form `<lifecycle_id>-ev-NNN`. |
| `event_status` | string | yes | Closed set `{filed | acknowledged | under_review | resolved_locally | superseded | withdrawn}`. |
| `event_basis` | string | yes | Closed set `{challenge_record | acknowledgement_record | review_update | local_resolution_record | supersession_record | withdrawal_record}`. |
| `actor_role` | string | yes | Closed set `{relying_party | policy_authority | reviewer | system_recorder}`. |
| `lifecycle_effect` | string | conditional | Closed set `{challenge_open | local_resolution_recorded | challenge_withdrawn | challenge_superseded}`. Required on the event whose `event_status` matches the record's terminal status (`resolved_locally`, `withdrawn`, `superseded`) and on the initial `filed` event (effect `challenge_open`). Absent on intermediate `acknowledged` and `under_review` events. |
| `event_timestamp` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. Strictly non-decreasing within the parent record's `events`. |
| `event_basis_ref` | string | yes | Closed grammar. Stable local identifier for the recording artifact backing the event. For `challenge_record` and `withdrawal_record` bases the value MAY equal the v0.4.0 body's `challenge_record_ref` / `withdrawal_record_ref` for the same row. |

## Closed Status / Basis / Effect Pairings

Each `(event_status, event_basis)` pair must satisfy the closed
matrix below. An event whose pair is not in the matrix is invalid.

| `event_status` | Allowed `event_basis` |
|---|---|
| `filed` | `challenge_record` |
| `acknowledged` | `acknowledgement_record` |
| `under_review` | `review_update` |
| `resolved_locally` | `local_resolution_record` |
| `superseded` | `supersession_record` |
| `withdrawn` | `withdrawal_record` |

Each `(event_status, lifecycle_effect)` pair, when `lifecycle_effect`
is present, must satisfy:

| `event_status` | Required `lifecycle_effect` |
|---|---|
| `filed` | `challenge_open` |
| `resolved_locally` | `local_resolution_recorded` |
| `withdrawn` | `challenge_withdrawn` |
| `superseded` | `challenge_superseded` |

`acknowledged` and `under_review` events MUST NOT carry a
`lifecycle_effect`.

## Closed Transition Graph

The v0.4.3 lifecycle is a closed directed graph over the six statuses:

```
filed -> acknowledged
filed -> withdrawn
filed -> superseded
acknowledged -> under_review
acknowledged -> withdrawn
acknowledged -> superseded
under_review -> resolved_locally
under_review -> withdrawn
under_review -> superseded
```

Terminal statuses are `resolved_locally`, `superseded`, and
`withdrawn`. No event MAY follow an event whose `event_status` is
terminal.

`current_status` MUST equal the `event_status` of the final entry of
`events`.

## Cross-Anchor Rules

- `package_id`, `governed_reliance_demo_id`, and
  `policy_evaluation_report_ref` cross-anchor the records body to the
  v0.4.0 package body, the v0.4.1 decision report, the v0.4.2 matrix,
  and the v0.4.2 policy evaluation report as documented above.
- `policy_evaluation_report_sha256` (runtime-injected) must equal the
  runtime SHA-256 of the v0.4.2 policy evaluation report bytes that
  appear as subject [4] of the v0.4.3 manifest.
- `(target_decision_id, target_decision_row_id)` MUST identify the
  same single row in the v0.4.1 decision report; the row's
  `decision_id` MUST equal `target_decision_id` and its `row_id` MUST
  equal `target_decision_row_id`.
- All `target_decision_id` values across `lifecycle_records[]` MUST
  be distinct (one lifecycle per governed decision row).
- Where present, `superseding_decision_id` MUST identify a row of the
  v0.4.0 body distinct from `target_decision_id`.

## Verifier Reachability Summary (v0.4.3 records-body reasons)

The v0.4.3 verifier emits the lifecycle-records-body-level reasons in
the order documented under `tools/gold/README.md` (v0.4.3 section).
The records-body-relevant subset of the closed 48-reason public
taxonomy is:

- `gold_challenge_lifecycle_records_not_object` — the records body
  subject is not a JSON object (top-level array, scalar, or null).
- `gold_challenge_lifecycle_records_schema_invalid` — records body
  shape / required-field / grammar defects: wrong `document_type`,
  wrong `schema_version`, `profile` outside the closed supported set,
  missing or non-list `lifecycle_records`, empty `lifecycle_records`,
  per-record shape defects, blank or missing limitations/non-claims
  sections where required, malformed top-level identifier grammars.
- `gold_challenge_lifecycle_records_binding_invalid` — failures of
  `target_decision_id ↔ decision_id`, `target_decision_row_id ↔
  row_id`, `policy_evaluation_report_ref`, or
  `policy_evaluation_report_sha256` anchoring, including duplicate
  `target_decision_id` across records, and 6-ID collision-class
  violations at the records body level.
- `gold_challenge_lifecycle_event_invalid` — malformed lifecycle
  event/status fields, missing required status-specific refs, invalid
  event/status payload shape. Specifically includes (a) malformed or
  missing per-event scalar fields (event_id, event_status,
  event_basis, actor_role, event_timestamp, event_basis_ref), (b)
  pair-table violations (status/basis or status/effect mismatch),
  (c) presence of `lifecycle_effect` on `acknowledged` or
  `under_review`, (d) missing required terminal-status ref fields at
  the record level (`local_resolution_ref` when terminal is
  `resolved_locally`, `withdrawal_record_ref` when terminal is
  `withdrawn`, `superseding_decision_id` when terminal is
  `superseded`).
- `gold_challenge_lifecycle_transition_invalid` — illegal lifecycle
  ordering, first event not `filed`, skipped/disallowed transition,
  event after terminal status, or `current_status` mismatch with
  final event. Includes monotonicity violations of
  `event_timestamp` within a record.

Reachability ordering for the records body: not-object first,
schema-shape second, binding third, per-event validity (R42) fourth,
sequence/graph validity (R43) last.

## Deterministic Serialization

When the v0.4.3 runner emits the runtime records body (after injecting
`policy_evaluation_report_sha256` and `generated_at`), it serializes
with `json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"`.
All SHA-256 values are bare lowercase hex (64 characters,
`[0-9a-f]{64}`) with no `sha256:` label prefix.

## Non-Claims

The records document is not signed, not a certificate, not
federated, not a transfer of reliance to any external party, does
not consult any live policy engine, and is not Gold certification.
It is a hand-authored deterministic local body for the v0.4.3
Challenge Lifecycle Lite package.
