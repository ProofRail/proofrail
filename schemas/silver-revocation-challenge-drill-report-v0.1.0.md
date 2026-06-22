# Silver Revocation/Challenge Drill Report — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.9
**Document type:** `proofrail.silver.revocation_challenge_drill_report`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.9`

---

## Purpose

The drill report is the deterministic, package-local record of a v0.2.9
revocation/challenge drill over one v0.2.8 relying-party acceptance
package. It binds the nested acceptance record (by id, decision status,
purpose, policy id/version, and copied package-manifest sha256), the
review-events fixture (by sha256), the derived findings, the derived
review triggers, and a single `recommended_local_posture` chosen from a
closed set.

The drill report is **not** a Gold certificate, regulator approval,
auditor approval, legal revocation, governed acceptance workflow, or
adjudication of any challenge on the merits.

It is emitted by
`tools/silver/run_revocation_challenge_drill_v0_1_0.py` and verified by
`tools/silver/verify_revocation_challenge_drill_v0_1_0.py`.

---

## Required top-level fields

```
document_type        — "proofrail.silver.revocation_challenge_drill_report"
schema_version       — "v0.1.0"
proofrail_release    — "v0.2.9"
drill_id             — non-empty string
generated_at         — ISO-8601 UTC, Z-suffixed
base_acceptance      — object (see §base_acceptance)
base_acceptance_validation — object (see §base_acceptance_validation)
review_events        — object (see §review_events)
findings             — array of finding objects
review_triggers      — array of review-trigger objects
recommended_local_posture — one of (see §recommended_local_posture)
scope_limitations    — non-empty array of non-empty strings
non_claims           — non-empty array of non-empty strings
```

---

## `base_acceptance`

Derived from the nested v0.2.8 acceptance record, policy, and
package manifest. All fields are derived; the runner never accepts
user-supplied `base_acceptance.*` overrides.

```
acceptance_record_id              — record.record_id
decision_status                   — record.decision.status
purpose_id                        — record.decision.purpose_id
acceptance_policy_id              — record.relying_party.policy_id
acceptance_policy_version         — record.relying_party.policy_version
acceptance_package_manifest_sha256 — "sha256:<hex>" of the copied
                                     acceptance-package-manifest.json
challenge_window:
  opens_at                        — record.challenge_window.opens_at
  closes_at                       — record.challenge_window.closes_at
```

The v0.2.9 verifier raises `acceptance_record_binding_mismatch` for any
disagreement between these fields and the nested package. It raises
`challenge_window_missing` when `base_acceptance.challenge_window.opens_at`
or `closes_at` is missing or malformed.

---

## `base_acceptance_validation`

```
validator_tool   — "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
validation_result — "pass" (the runner refuses to author a report when the
                    v0.2.8 validator fails)
validated_at     — ISO-8601 UTC, Z-suffixed
failure_reason   — null
```

---

## `review_events`

```
events_path   — "review-events.jsonl"
events_sha256 — "sha256:<hex>" of the copied review-events file
event_count   — non-negative integer; MUST equal the number of JSONL
                lines parsed
```

The v0.2.9 verifier raises `review_events_hash_mismatch` when the
recomputed file sha256 disagrees with `events_sha256`.

---

## `findings`

Each finding is an object:

```
finding_id   — non-empty string
finding_type — one of:
                 "challenge_within_window"
                 "revocation_signal_recorded"
                 "acceptance_revalidated"
result       — "pass" or "advisory"
event_ids    — non-empty array of non-empty strings; each MUST refer to
               an event_id in review-events.jsonl
local_effect — non-empty string
```

The v0.2.9 verifier raises `required_finding_missing` when any required
finding type is absent.

For findings of type `challenge_within_window`, the verifier raises
`challenge_window_classification_mismatch` when the referenced
`challenge.received` event's `event_time` lies outside the bound
`challenge_window`. This classification check runs **before** the
verifier's missing-challenge check, so reports that mislabel an
outside-window event as within-window fail with
`challenge_window_classification_mismatch` rather than
`challenge_within_window_missing`.

---

## `review_triggers`

Each review trigger is an object:

```
trigger_type — one of:
                 "challenge_within_window"
                 "post_acceptance_revocation_signal"
severity     — one of:
                 "advisory"
                 "review_required"
event_id     — non-empty string; MUST refer to an event_id in
               review-events.jsonl
```

The v0.2.9 verifier raises `required_review_trigger_missing` when any
required trigger type is absent.

---

## `recommended_local_posture`

Closed set:

```
acceptance_stands_for_demo_scope
acceptance_requires_review_before_reuse
acceptance_not_reusable_without_governed_review
```

The v0.2.9 verifier raises `recommended_posture_invalid` when the value
is not in this set, or when review triggers are present and the value is
`acceptance_stands_for_demo_scope`.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. The verifier raises `scope_limitations_missing` and
`drill_non_claims_missing` respectively when violated.

---

## Non-claims about this schema

- The drill report is not a certificate.
- The drill report is not Gold conformance.
- The drill report is not regulator or auditor approval.
- The drill report does not adjudicate any challenge on the merits.
- The drill report does not revoke the v0.2.8 acceptance record.
- The drill report does not alter the v0.2.7 composed gateway evidence
  package.
