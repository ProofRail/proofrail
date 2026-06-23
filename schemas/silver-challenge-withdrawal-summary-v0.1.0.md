# Silver Challenge/Withdrawal Summary Schema v0.1.0 (ProofRail v0.3.4)

The challenge/withdrawal summary is a deterministic JSON document
derived by the v0.3.4 runner from the copied target handoff manifest,
the bound challenge record, and the bound withdrawal record. The
summary is hash-bound by the v0.3.4 manifest as subject [3].

## Document type

```text
proofrail.silver.challenge_withdrawal_summary
```

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `document_type` | string | Must equal `proofrail.silver.challenge_withdrawal_summary` |
| `schema_version` | string | Must equal `v0.1.0` |
| `proofrail_release` | string | Must equal `v0.3.4` |
| `summary_id` | string | Non-empty |
| `generated_at` | string | ISO-8601 UTC, `Z`-suffixed |
| `target` | object | `{target_type, target_manifest_path, target_manifest_sha256}` |
| `records` | object | See records object below |
| `summary` | object | See summary object below |
| `claims` | array of objects | Required 7 claims (see below) |
| `scope_limitations` | array of strings | Non-empty; no blank entries |
| `non_claims` | array of strings | Non-empty; no blank entries |

## `records` object

```text
challenge_record_path     -- "records/challenge-record.json"
challenge_record_sha256   -- sha256 of subject [1]
withdrawal_record_path    -- "records/withdrawal-record.json"
withdrawal_record_sha256  -- sha256 of subject [2]
```

## `summary` object

```text
challenge_count       -- integer; equal to re-derived count (1 in v0.3.4)
withdrawal_count      -- integer; equal to re-derived count (1 in v0.3.4)
challenge_status      -- echoes the challenge record's challenge.challenge_status
withdrawal_status     -- echoes the withdrawal record's withdrawal.withdrawal_status
withdrawal_effect     -- echoes the withdrawal record's withdrawal.withdrawal_effect
posture               -- closed enum (see below)
```

### `posture` closed set (5 values)

```text
challenge_recorded
challenged_with_local_reuse_paused_for_review
challenged_with_local_reliance_withdrawn_for_review
withdrawal_recorded_without_adjudication
record_superseded
```

### Posture derivation rule

The runner picks the posture deterministically from
`withdrawal_effect`:

| `withdrawal_effect` | posture |
|---|---|
| `local_reuse_paused_for_review` | `challenged_with_local_reuse_paused_for_review` |
| `local_reliance_withdrawn_for_review` | `challenged_with_local_reliance_withdrawn_for_review` |
| `acceptance_reuse_blocked_pending_review` | `challenged_with_local_reuse_paused_for_review` |
| `record_superseded` | `record_superseded` |

The verifier checks that the recorded posture is in the closed set and
that it matches the row above for the recorded `withdrawal_effect`.

## Required claims (7)

All seven claim IDs must be present and each must have `status: "pass"`
with at least one safe package-local `evidence_refs` entry:

```text
target_handoff_verified
challenge_record_valid
withdrawal_record_valid
challenge_and_withdrawal_target_same_handoff
withdrawal_cites_challenge
time_order_valid
no_adjudication_claimed
```

Each claim may carry an optional `description` string, which the
overclaim guard scans like any other free-text field outside
`scope_limitations` and `non_claims`.

## Non-claims (release boundary)

The challenge/withdrawal summary:

- does not adjudicate the challenge;
- does not legally revoke reliance;
- does not implement Gold governance;
- does not certify the target handoff;
- does not say the challenge is correct.
