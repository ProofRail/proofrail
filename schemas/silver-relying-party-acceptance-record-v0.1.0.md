# Silver Relying-Party Acceptance Record — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.8
**Document type:** `proofrail.silver.relying_party_acceptance_record`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.8`

---

## Purpose

A relying-party acceptance record is the deterministic, package-local
record of one relying party's local decision (accept, reject, or accept
with exceptions) over one verified Silver evidence package, for one
purpose, under one named policy version. It is the v0.2.8 output of
`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`.

It is not a certificate. It is not Gold conformance. It is not
regulator approval. It is not legal acceptance.

---

## Required top-level fields

```
document_type        — "proofrail.silver.relying_party_acceptance_record"
schema_version       — "v0.1.0"
proofrail_release    — "v0.2.8"
record_id            — non-empty string
generated_at         — ISO-8601 timestamp (UTC, Z-suffixed)
relying_party        — object (see §relying_party)
decision             — object (see §decision)
evidence_package     — object (see §evidence_package)
verification         — object (see §verification)
revocation_review    — object (see §revocation_review)
exceptions           — array (possibly empty) of exception objects
scope_limitations    — non-empty array of non-empty strings
challenge_window     — object (see §challenge_window)
non_claims           — non-empty array of non-empty strings
```

---

## `relying_party`

```
relying_party_id  — non-empty string; MUST equal policy.relying_party.relying_party_id
policy_id         — non-empty string; MUST equal policy.policy_id
policy_version    — non-empty string; MUST equal policy.policy_version
```

---

## `decision`

```
status            — one of "accepted", "rejected", "accepted_with_exceptions"
                    AND in policy.allowed_decisions
purpose_id        — non-empty string; MUST be in policy.allowed_purposes
decision_basis    — non-empty string
decision_maker    — non-empty string
decision_time     — ISO-8601 timestamp (UTC, Z-suffixed)
rejection_reason  — string; required (non-empty) when status == "rejected"
                    and verification.failure_reason is null/empty
```

---

## `evidence_package`

```
evidence_type     — non-empty string; MUST be in policy.allowed_evidence_types
manifest_path     — exactly "evidence/composed-gateway-evidence-manifest.json"
manifest_sha256   — "sha256:<hex>" of the copied evidence manifest
source_release    — non-empty string identifying the source release
                    (e.g. "v0.2.7")
```

---

## `verification`

```
verifier_tool          — non-empty repo-relative path string; MUST equal
                         policy.required_verification.verifier_tool
verification_result    — non-empty string ("pass" or "fail")
verified_at            — ISO-8601 timestamp (UTC, Z-suffixed)
failure_reason         — string or null; non-empty when verification_result == "fail"
```

---

## `revocation_review`

```
performed         — boolean
outcome           — non-empty string; MUST be in
                    policy.revocation_requirements.accepted_outcomes
                    when policy requires revocation review
reviewed_at       — ISO-8601 timestamp (UTC, Z-suffixed)
notes             — non-empty string
```

When `policy.revocation_requirements.revocation_review_required` is true,
`performed` MUST be true AND `outcome` MUST be in the policy's
`accepted_outcomes`. Otherwise the validator raises
`revocation_review_missing`.

---

## `exceptions`

Each exception entry MUST be an object with:

```
severity         — one of "blocking", "advisory"
description      — non-empty string
effect_on_scope  — non-empty string
```

Rules:

- `decision.status == "accepted"` requires zero exceptions with
  `severity == "blocking"`. Otherwise →
  `accepted_record_has_blocking_exception`.
- `decision.status == "accepted_with_exceptions"` requires at least one
  exception entry conforming to the shape above. Otherwise →
  `accepted_with_exceptions_missing_exception`.

---

## `challenge_window`

```
opens_at           — ISO-8601 timestamp (UTC, Z-suffixed)
closes_at          — ISO-8601 timestamp (UTC, Z-suffixed); MUST be strictly
                     after opens_at
challenge_contact  — non-empty string
```

When `policy.challenge_window.required` is true, the span between
`opens_at` and `closes_at` MUST satisfy
`policy.challenge_window.minimum_days <= span_days <= policy.challenge_window.maximum_days`.
Otherwise → `challenge_window_invalid`.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected only for non-emptiness.

The validator raises `scope_limitations_missing` or
`acceptance_non_claims_missing` if either is empty.

---

## Decision-status invariants

| `decision.status` | Required conditions |
|---|---|
| `accepted` | `verification.verification_result == "pass"` AND no exception with `severity == "blocking"` |
| `accepted_with_exceptions` | ≥1 conforming exception (any severity) |
| `rejected` | non-empty `decision.rejection_reason` OR non-empty `verification.failure_reason` |

The acceptance record does not authorize execution and does not certify
the evidence. It records a local reliance decision.

---

## Non-claims about this schema

- This schema does not define a certificate.
- This schema does not implement governed acceptance.
- This schema does not encode legal authority.
- This schema does not implement a dispute or challenge workflow.
- This schema does not assert that the verified evidence is true; it
  records that the relying party chose to rely on it for a stated
  purpose.
