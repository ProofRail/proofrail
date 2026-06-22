# Silver Relying-Party Review Event — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.9
**Document type:** `proofrail.silver.relying_party_review_event`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.9`

---

## Purpose

A relying-party review event is one line in a JSONL fixture of
post-acceptance review signals received by a Silver relying party. Each
event records that a challenge was received, that a revocation signal was
observed, or that the relying party re-ran the v0.2.8 acceptance
validator over the originally accepted package.

A review event is **not** a Gold challenge submission, a legal notice, a
live revocation publication, or a governed dispute filing. It is a
deterministic local input to the v0.2.9 revocation/challenge drill.

---

## Required top-level fields (every event)

```
document_type     — "proofrail.silver.relying_party_review_event"
schema_version    — "v0.1.0"
proofrail_release — "v0.2.9"
event_id          — non-empty string; unique within the events file
event_type        — one of:
                      "challenge.received"
                      "revocation.signal_received"
                      "acceptance.revalidation_performed"
event_time        — ISO-8601 UTC, Z-suffixed
target            — object (see §target)
```

---

## `target`

```
acceptance_record_id — non-empty string; MUST equal the bound
                        v0.2.8 acceptance record's record_id
purpose_id           — non-empty string; MUST equal the bound
                        v0.2.8 acceptance record's decision.purpose_id
```

The v0.2.9 verifier raises `review_event_target_mismatch` for any
non-revocation event whose target deviates from the bound acceptance
record, and raises `revocation_signal_target_mismatch` for any
`revocation.signal_received` event whose target deviates.

---

## Event-type-specific required fields

### `challenge.received`

```
submitted_by         — non-empty string
challenge_reason     — non-empty string
challenge_summary    — non-empty string
expected_local_handling — non-empty string
```

### `revocation.signal_received`

```
signal_kind          — non-empty string
signal_source        — non-empty string
signal_summary       — non-empty string
expected_local_handling — non-empty string
```

### `acceptance.revalidation_performed`

```
validator_tool       — non-empty string; repo-relative
validation_result    — non-empty string ("pass" or "fail")
expected_local_handling — non-empty string (optional but recommended)
```

---

## Ordering

`event_time` MUST be non-decreasing across the JSONL file. The v0.2.9
verifier raises `review_event_sequence_invalid` when this is violated.

---

## Non-claims about this schema

- A review event is not a real challenge submission, not a legal notice,
  not a regulator filing, and not a live revocation publication.
- A review event does not by itself revoke acceptance, invalidate the
  v0.2.8 acceptance record, or alter the v0.2.7 composed gateway evidence
  package.
- The set of recognized `event_type` values is closed for v0.2.9.
- Extensions to this set are out of scope for v0.2.9 and are not implied
  by this schema.
