# Silver Relying-Party Policy Pack v0.1.0

**Document type:** `proofrail.silver.relying_party_policy_pack`

**Profile:** `relying_party_policy_pack.preview`

The Relying-Party Policy Pack is a structured JSON document declaring the
local policy a relying party would adopt **before** the Gold boundary.
v0.3.5 verifies the pack's structural conformance only. It does not
adjudicate any acceptance, rejection, challenge, withdrawal, or
supersession event. It does not transform a Silver verification result
into a governed reliance decision; that is a v0.4.0 Minimal Gold
concern.

## Top-level shape

```jsonc
{
  "document_type": "proofrail.silver.relying_party_policy_pack",
  "schema_version": "0.1.0",
  "policy_pack_id": "<stable-id-string>",
  "profile": "relying_party_policy_pack.preview",
  "relying_party": { ... },
  "policy_authority": { ... },
  "policy": { ... },
  "applicable_protected_actions": [ "<protected_action_id>", ... ],
  "applicable_environments": [ "<environment_label>", ... ],
  "silver_handoff_requirements": { ... },
  "verifier_requirements": { ... },
  "issuer_requirements": { ... },
  "revocation_requirements": { ... },
  "freshness_requirements": { ... },
  "challenge_handling": { ... },
  "withdrawal_handling": { ... },
  "supersession_handling": { ... },
  "acceptance_criteria": { ... },
  "rejection_criteria": { ... },
  "exceptions": [ ... ],
  "hard_stops": [ ... ],
  "warning_treatment": { ... },
  "related_silver_artifacts": [ ... ],
  "scope_limitations": [ "<string>", ... ],
  "non_claims": [ "<string>", ... ]
}
```

## Required sections

### `relying_party`
Object with non-empty string `identity_id`, `identity_label`, `contact`.

### `policy_authority`
Object with non-empty string `authority_id`, `authority_label`,
`approver_role`.

### `policy`
Object with:
- `version` — non-empty string
- `effective_period` — object with `starts_at` and `ends_at` (each an
  ISO-8601 UTC `Z` timestamp); `starts_at` must precede `ends_at`.

### `applicable_protected_actions`
Non-empty list of non-empty strings.

### `applicable_environments`
Non-empty list of non-empty strings.

### `silver_handoff_requirements`
Object with:
- `required_handoff_profiles` — non-empty list of strings from the
  closed set `{"silver.acceptance_handoff.v0.3.0"}`
- `minimum_handoff_posture` — one of
  `{"for_demo_scope","review_required_before_reuse","not_reusable_without_governed_review"}`
- `required_subject_roles` — non-empty list of non-empty strings.

### `verifier_requirements`
Object with:
- `minimum_posture` — one of `{"silver.base","silver.base.demo","silver.independent"}`
- `required_verifier_attestation` — boolean
- `required_verifier_attestor_ids` — list of non-empty strings (may be
  empty only when `required_verifier_attestation` is `false`)

### `issuer_requirements`
Object with:
- `trusted_issuer_ids` — non-empty list of non-empty strings
- `required_signature_algorithm` — closed set `{"ed25519"}`
- `minimum_key_id_count` — integer ≥ 1

### `revocation_requirements`
Object with:
- `mode` — one of `{"required","required_with_warning_allowance","not_required"}`
- `max_revocation_list_age_seconds` — non-negative integer

### `freshness_requirements`
Object with:
- `max_age_seconds` — non-negative integer (positive when relied upon)
- `freshness_anchor` — non-empty string identifying the timestamp field

### `challenge_handling`
Object with:
- `posture` — one of `{"record_only","record_and_pause_reuse","record_and_require_review"}`
- `within_window_required` — boolean

### `withdrawal_handling`
Object with:
- `posture` — one of `{"record_only","record_and_pause_reuse","record_and_block_reuse"}`
- `pause_local_reuse_on_withdrawal` — boolean

### `supersession_handling`
Object with:
- `posture` — one of `{"record_only","record_and_require_superseding_handoff","record_and_block_until_superseded"}`
- `require_superseding_handoff_id` — boolean

### `acceptance_criteria`
Object with:
- `required_silver_results` — non-empty list of strings from the closed set
  `{"verifier_pass","issuer_trusted","revocation_check_performed","freshness_window_ok","attestation_present"}`
- `required_handoff_subject_hash_match` — boolean

### `rejection_criteria`
Object with:
- `blocking_silver_results` — non-empty list of strings from the closed set
  `{"verifier_fail","issuer_untrusted","revocation_check_failed_or_skipped","freshness_window_exceeded","attestation_missing","posture_downgrade"}`

### `exceptions`
List (may be empty) of objects each with:
- `exception_id` — non-empty string
- `approver_id` — non-empty string
- `scope` — non-empty string
- `reason` — non-empty string
- `expires_at` — ISO-8601 UTC `Z` timestamp

### `hard_stops`
Non-empty list of objects each with:
- `hard_stop_id` — non-empty string
- `description` — non-empty string
- `overridable_by_exception` — literal `false` (a hard stop that is
  overridable contradicts the contract)

### `warning_treatment`
Object with:
- `unknown_warning_default` — one of `{"block","review_required","allow_with_logging"}`
- `warnings` — list (may be empty) of objects each with non-empty
  `warning_id` and `treatment` from the closed set above.

### `related_silver_artifacts`
List (may be empty) of objects each with:
- `artifact_role` — non-empty string
- `path` — non-empty string, relative, no `..`, not absolute
- `description` — non-empty string

### `scope_limitations`
Non-empty list of non-empty strings.

### `non_claims`
Non-empty list of non-empty strings.

## Non-claims (intrinsic to v0.3.5)

A Relying-Party Policy Pack does not:

- Certify, audit, or legally validate the relying party's policy.
- Constitute regulator approval, auditor approval, or legal
  authorization.
- Authorize production reliance.
- Adjudicate any challenge, withdrawal, or supersession event.
- Turn a passing Silver verification into a governed reliance decision
  (v0.4.0 Minimal Gold boundary).
- Assert compliance, runtime truth, or transferred trust.
- Validate the substantive content of free-text fields, approver
  identities, or external references.
- Bind v0.3.0–v0.3.4 manifests into the pack; only references by
  descriptor are permitted via `related_silver_artifacts`.
