# Silver Withdrawal Record Schema v0.1.0 (ProofRail v0.3.4)

A Silver withdrawal record is a deterministic, local JSON document
that records that a local reliance or reuse posture has been withdrawn,
paused, or superseded for a stated reason. It does **not** constitute
legal revocation, certification withdrawal, regulator action, or Gold
governance.

## Document type

```text
proofrail.silver.withdrawal_record
```

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `document_type` | string | Must equal `proofrail.silver.withdrawal_record` |
| `schema_version` | string | Must equal `v0.1.0` |
| `proofrail_release` | string | Must equal `v0.3.4` |
| `withdrawal_record_id` | string | Non-empty |
| `recorded_at` | string | ISO-8601 UTC, `Z`-suffixed |
| `effective_at` | string | ISO-8601 UTC, `Z`-suffixed; `recorded_at <= effective_at` |
| `recorded_by` | object | `{principal_id: string, role: string}` (both non-empty) |
| `target` | object | Same shape as challenge record target |
| `related_challenge_record_id` | string | Must equal the cited challenge record's `challenge_record_id` |
| `withdrawal` | object | See withdrawal object below |
| `evidence_refs` | array of strings | Package-local relative paths only |
| `scope_limitations` | array of strings | Non-empty; no blank entries |
| `non_claims` | array of strings | Non-empty; no blank entries |

## Target object

Same shape as the challenge record target object. Both records must
target the same handoff artifact:

- `target_type == "silver_acceptance_handoff"`
- `target_manifest_path` matches the manifest's `target_handoff_manifest`
  subject path (`target-handoff/silver-acceptance-handoff-manifest.json`)
- `target_manifest_sha256` matches the manifest's
  `target_handoff_manifest` subject sha256 after binding (the runner
  rewrites the placeholder `sha256:TO_BE_BOUND_BY_RUNNER`)

## Withdrawal object

| Field | Type | Notes |
|---|---|---|
| `withdrawal_reason` | string | Closed enum (see below) |
| `withdrawal_status` | string | Closed enum (see below) |
| `withdrawal_effect` | string | Closed enum (see below) |

### `withdrawal_reason` closed set (7 values)

```text
challenge_pending_review
revocation_status_changed
evidence_defect_claimed
policy_superseded
scope_no_longer_applicable
review_window_expired
administrative_correction
```

### `withdrawal_status` closed set (4 values)

```text
withdrawal_recorded
reuse_paused
superseded
withdrawn_record_superseded
```

### `withdrawal_effect` closed set (4 values)

```text
local_reuse_paused_for_review
local_reliance_withdrawn_for_review
acceptance_reuse_blocked_pending_review
record_superseded
```

Legal/governance-coloured statuses such as `legally_revoked`,
`certification_revoked`, `Gold_rejected`, and `Gold_accepted` are
intentionally **not** in any of these sets.

## Evidence references

Same hygiene rule as the challenge record. The withdrawal record
typically cites the challenge record under `records/`, the handoff
summary, and the handoff manifest.

## Non-claims (release boundary)

A Silver withdrawal record:

- does not legally revoke reliance;
- does not adjudicate the related challenge;
- does not implement Gold governance;
- does not constitute regulator action, auditor action, third-party
  audit, legal revocation, certification withdrawal, dispute
  resolution, or production authorization;
- does not transfer reliance away from anyone but the local recording
  party.

A withdrawal record only states that the local recording party has
paused or withdrawn its own reuse / reliance posture pending review.
