# Silver Acceptance Handoff Summary — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.0
**Document type:** `proofrail.silver.acceptance_handoff_summary`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.0`

---

## Purpose

The Silver acceptance handoff summary records the deterministic facts
about a portable v0.3.0 Silver acceptance handoff package: what
nested release packages it includes, the acceptance record id, the
decision status, the purpose id, the post-acceptance review posture, and
the v0.3.0-level handoff posture.

It is emitted by
`tools/silver/build_silver_acceptance_handoff_v0_1_0.py` from
**derived** facts (the v0.2.8 acceptance record + v0.2.9 drill report).
It is **not** hand-authored and the v0.3.0 verifier re-derives every
field from the nested packages.

A handoff summary is **not** a certificate, approval, adjudication,
audit, or trust transfer. It preserves evidence and posture for an
independent reviewer.

---

## Required top-level fields

```
document_type     — "proofrail.silver.acceptance_handoff_summary"
schema_version    — "v0.1.0"
proofrail_release — "v0.3.0"
handoff_id        — non-empty string
generated_at      — ISO-8601 UTC, Z-suffixed
handoff_context   — object (see below)
included_chain    — object (see below)
handoff_result    — object (see below)
scope_limitations — non-empty array of non-empty strings
non_claims        — non-empty array of non-empty strings
```

---

## `handoff_context`

```
handoff_purpose        — non-empty string
recipient_role         — non-empty string
source_package_family  — non-empty string
```

These fields are descriptive labels supplied at the v0.3.0 build step.
They do not change the chain-binding outcome.

---

## `included_chain`

A three-key object recording the included v0.2.7, v0.2.8, and v0.2.9
package manifests, in this fixed key order:

```
composed_gateway_evidence:
  manifest_path        — "composed-gateway-evidence/composed-gateway-evidence-manifest.json"
  manifest_sha256      — "sha256:<hex>"
  source_release       — "v0.2.7"

relying_party_acceptance:
  manifest_path        — "acceptance-package/acceptance-package-manifest.json"
  manifest_sha256      — "sha256:<hex>"
  source_release       — "v0.2.8"
  acceptance_record_id — non-empty string (copied from v0.2.8 record)
  decision_status      — "accepted" | "rejected" | "accepted_with_exceptions"
  purpose_id           — non-empty string (copied from v0.2.8 record)

revocation_challenge_drill:
  manifest_path           — "revocation-challenge-drill/revocation-challenge-drill-manifest.json"
  manifest_sha256         — "sha256:<hex>"
  source_release          — "v0.2.9"
  recommended_local_posture — one of the v0.2.9 closed posture set
```

Every `manifest_sha256` MUST equal the recomputed SHA-256 of the file at
`manifest_path` under the handoff package root, which MUST in turn equal
the corresponding handoff manifest subject sha256. The v0.3.0 verifier
raises `handoff_summary_binding_mismatch` on disagreement.

---

## `handoff_result`

```
handoff_package_status        — "complete"
recommended_handoff_posture   — one of the closed handoff posture set
reuse_warning                 — non-empty string
```

### Closed handoff posture set

```
silver_handoff_complete_for_demo_scope            (rank 0)
silver_handoff_complete_review_required_before_reuse  (rank 1)
silver_handoff_not_reusable_without_governed_review   (rank 2)
```

### Drill-posture → minimum handoff-posture map

```
acceptance_stands_for_demo_scope                -> rank 0
acceptance_requires_review_before_reuse         -> rank 1
acceptance_not_reusable_without_governed_review -> rank 2
```

The v0.3.0 verifier:

- Rejects any `recommended_handoff_posture` outside the closed set with
  `handoff_posture_invalid`.
- Rejects any nested v0.2.9 posture outside the known map with
  `handoff_posture_invalid`.
- Rejects a `recommended_handoff_posture` whose rank is **lower** than
  the rank required by the nested v0.2.9 posture map with
  `handoff_posture_downgrade`.
- Accepts a `recommended_handoff_posture` whose rank is equal to or
  greater than (stricter than) the required rank.

`reuse_warning` MUST be non-empty when the nested v0.2.9 posture requires
review before reuse or is not-reusable.

---

## Acceptance record / purpose cross-checks

The v0.3.0 verifier raises:

- `handoff_record_mismatch` if
  `included_chain.relying_party_acceptance.acceptance_record_id` or
  `decision_status` disagrees with the nested v0.2.8 acceptance record.
- `handoff_purpose_mismatch` if
  `included_chain.relying_party_acceptance.purpose_id` disagrees with the
  nested v0.2.8 acceptance record's `decision.purpose_id`.

---

## Overclaim guard

The v0.3.0 verifier scans every string value in the summary (recursively)
**outside** the `scope_limitations` and `non_claims` arrays for positive
overclaim wording. Forbidden positive tokens (case-insensitive substring
match):

```
"certified", "approved", "audited",
"legally accepted", "legally revoked",
"challenge resolved",
"gold accepted", "gold certified",
"compliant", "production-approved", "production-ready",
"regulator-ready", "regulator approval",
"trust transferred", "trust transfer"
```

Any positive occurrence raises `handoff_overclaim`. The same words may
appear inside `scope_limitations` and `non_claims` (where they typically
appear in negated form to **deny** the overclaim).

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected for non-emptiness and (in the summary) are
exempt from the overclaim guard.

The v0.3.0 verifier raises `handoff_limitations_missing` and
`handoff_non_claims_missing` respectively when either is empty.

---

## Non-claims about this schema

- The summary is not a certificate.
- The summary does not assert that a downstream party should reuse the
  acceptance.
- The summary does not adjudicate any challenge or revocation signal.
- The summary does not transfer reliance.
- The summary does not establish Gold conformance.
- The summary does not approve production use.
- The summary does not assert legal acceptance or legal revocation.
