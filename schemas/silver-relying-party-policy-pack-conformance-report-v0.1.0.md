# Silver Relying-Party Policy Pack Conformance Report v0.1.0

**Document type:**
`proofrail.silver.relying_party_policy_pack_conformance_report`

The conformance report is a derived JSON document recording the result
of the 24 ordered structural checks the v0.3.5 verifier performs
against the bound policy pack. The verifier **independently re-derives**
the report from the policy pack at verification time and compares it
to the bundled subject [1] bytes; the bundled report is never accepted
as proof of conformance on its own.

## Top-level shape

```jsonc
{
  "document_type": "proofrail.silver.relying_party_policy_pack_conformance_report",
  "schema_version": "0.1.0",
  "proofrail_release": "v0.3.5",
  "report_id": "<stable-id-string>",
  "policy_pack_id": "<stable-id-string>",
  "policy_pack_sha256": "sha256:<64-hex>",
  "generated_at": "<ISO-8601 UTC Z>",
  "checks": [
    {"check_id": "check_01", "approved_reason_name": "policy_pack_manifest_invalid",       "status": "pass"},
    {"check_id": "check_02", "approved_reason_name": "policy_pack_not_object",             "status": "pass"},
    {"check_id": "check_03", "approved_reason_name": "policy_pack_schema_invalid",         "status": "pass"},
    {"check_id": "check_04", "approved_reason_name": "policy_pack_profile_unsupported",    "status": "pass"},
    {"check_id": "check_05", "approved_reason_name": "policy_pack_identity_invalid",       "status": "pass"},
    {"check_id": "check_06", "approved_reason_name": "policy_pack_authority_invalid",      "status": "pass"},
    {"check_id": "check_07", "approved_reason_name": "policy_scope_invalid",               "status": "pass"},
    {"check_id": "check_08", "approved_reason_name": "protected_action_scope_invalid",     "status": "pass"},
    {"check_id": "check_09", "approved_reason_name": "silver_handoff_requirement_invalid", "status": "pass"},
    {"check_id": "check_10", "approved_reason_name": "verifier_requirement_invalid",       "status": "pass"},
    {"check_id": "check_11", "approved_reason_name": "issuer_requirement_invalid",         "status": "pass"},
    {"check_id": "check_12", "approved_reason_name": "revocation_requirement_invalid",     "status": "pass"},
    {"check_id": "check_13", "approved_reason_name": "freshness_requirement_invalid",      "status": "pass"},
    {"check_id": "check_14", "approved_reason_name": "challenge_requirement_invalid",      "status": "pass"},
    {"check_id": "check_15", "approved_reason_name": "withdrawal_requirement_invalid",     "status": "pass"},
    {"check_id": "check_16", "approved_reason_name": "supersession_requirement_invalid",   "status": "pass"},
    {"check_id": "check_17", "approved_reason_name": "acceptance_criteria_invalid",        "status": "pass"},
    {"check_id": "check_18", "approved_reason_name": "rejection_criteria_invalid",         "status": "pass"},
    {"check_id": "check_19", "approved_reason_name": "exception_policy_invalid",           "status": "pass"},
    {"check_id": "check_20", "approved_reason_name": "hard_stop_policy_invalid",           "status": "pass"},
    {"check_id": "check_21", "approved_reason_name": "warning_policy_invalid",             "status": "pass"},
    {"check_id": "check_22", "approved_reason_name": "reference_policy_invalid",           "status": "pass"},
    {"check_id": "check_23", "approved_reason_name": "non_claims_missing",                 "status": "pass"},
    {"check_id": "check_24", "approved_reason_name": "prohibited_claim_present",           "status": "pass"}
  ]
}
```

## Determinism contract

- Exactly 24 entries in `checks[]`, in the fixed order shown above.
- A passing report has every `status` equal to `"pass"`.
- A passing report is the only shape that may appear in a packaged
  manifest, since any structural failure short-circuits the verifier
  before report comparison and the runner stages the package only on
  a successful pre-staging self-validation.
- `report_id`, `policy_pack_id`, `policy_pack_sha256`, and
  `generated_at` are stable strings derived from the runner inputs.
- Canonical JSON serialization (`sort_keys=True`,
  `separators=(",",":")`) is required for re-derivation to match the
  bundled bytes byte-for-byte.

## Non-claims

The conformance report records only that the 24 structural checks
passed. It is not a certification, audit, regulator approval, or
governed reliance decision.
