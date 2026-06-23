# Silver Challenge Record Schema v0.1.0 (ProofRail v0.3.4)

A Silver challenge record is a deterministic, local JSON document that
states a target Silver acceptance handoff artifact has been challenged
for a specific stated reason. It does **not** adjudicate the challenge.

## Document type

```text
proofrail.silver.challenge_record
```

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `document_type` | string | Must equal `proofrail.silver.challenge_record` |
| `schema_version` | string | Must equal `v0.1.0` |
| `proofrail_release` | string | Must equal `v0.3.4` |
| `challenge_record_id` | string | Non-empty, no leading/trailing whitespace |
| `filed_at` | string | ISO-8601 UTC, `Z`-suffixed (e.g. `2026-06-29T00:10:00Z`) |
| `filed_by` | object | `{principal_id: string, role: string}` (both non-empty) |
| `target` | object | See target object below |
| `challenge` | object | See challenge object below |
| `evidence_refs` | array of strings | Package-local relative paths only |
| `scope_limitations` | array of strings | Non-empty; no blank entries |
| `non_claims` | array of strings | Non-empty; no blank entries |

## Target object

| Field | Type | Notes |
|---|---|---|
| `target_type` | string | Must equal `silver_acceptance_handoff` |
| `target_manifest_path` | string | Package-local relative path; conventionally `target-handoff/silver-acceptance-handoff-manifest.json` |
| `target_manifest_sha256` | string | `sha256:<64 hex>` of the copied target manifest after binding |
| `target_record_id` | string | Non-empty `handoff_id` of the cited target handoff |

Fixture records before binding may carry the literal placeholder
`sha256:TO_BE_BOUND_BY_RUNNER`. The v0.3.4 runner rewrites the
placeholder to the actual digest of the copied target handoff manifest
before publishing. The verifier MUST reject any packaged record that
still contains the placeholder.

## Challenge object

| Field | Type | Notes |
|---|---|---|
| `challenge_reason` | string | Closed enum (see below) |
| `challenge_status` | string | Closed enum (see below) |
| `challenge_basis` | array of strings | Non-empty; descriptive only |
| `requested_action` | string | Non-empty free-text (e.g. `review_before_reuse`) |

### `challenge_reason` closed set (10 values)

```text
post_acceptance_review_required
revocation_status_changed
evidence_mismatch_claimed
scope_overreach_claimed
verifier_output_disputed
policy_conflict_claimed
stale_evidence_claimed
identity_or_registry_gap_claimed
adapter_normalization_disputed
administrative_correction_requested
```

### `challenge_status` closed set (4 values)

```text
filed
under_review
superseded
withdrawn_by_challenger
```

Adjudicative statuses such as `sustained`, `rejected`, `resolved`,
`approved`, and `certified` are intentionally **not** in this set.

## Evidence references

Every entry of `evidence_refs` must be a non-empty relative path with no
`..` component and no leading `/`. The verifier rejects any absolute
or traversing reference with the dedicated reason
`challenge_record_evidence_ref_invalid`.

## Non-claims (release boundary)

A Silver challenge record:

- does not adjudicate the challenge;
- does not legally revoke reliance;
- does not implement Gold governance;
- does not bind any external party;
- does not constitute regulator approval, auditor approval, third-party
  audit, legal acceptance, compliance certification, or production
  authorization;
- does not transfer reliance.

A challenge record only states that a stated reason for review was
recorded against a stated target.
