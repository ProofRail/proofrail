# Silver Demo 005 — Relying-Party Acceptance Record Walkthrough

**ProofRail release:** v0.2.8

> v0.2.8 records a relying party's local acceptance decision over verified
> Silver evidence. It does not certify the evidence, the system, the gateway,
> or the relying party.

---

## 1. Inputs

The generator reads two committed inputs:

| Input | Path |
|---|---|
| Acceptance policy fixture | `fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json` |
| Composed gateway evidence manifest (v0.2.7) | `<v0.2.7 package>/composed-gateway-evidence-manifest.json` |

The v0.2.7 evidence manifest is produced by
`tools/silver/compose_gateway_evidence_demo_v0_1_0.py` and verified by
`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`. v0.2.8
does not re-derive any v0.2.7 claim; it consults the v0.2.7 verifier as a
subprocess and records its pass/fail outcome.

No network, no live actuator, no real gateway, no real relying party,
no signing, no governance workflow.

---

## 2. Generator steps

(`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`)

1. Refuse to overwrite a non-empty `--output-dir` unless `--force` is given.
2. Validate ISO-8601 Z-suffixed `--generated-at`, `--challenge-closes-at`,
   and optional `--challenge-opens-at`.
3. Parse and structurally validate the supplied acceptance policy
   (document type, schema version, required fields, allowed_decisions set
   = `{accepted, rejected, accepted_with_exceptions}`).
4. Verify `--decision` is in `policy.allowed_decisions`.
5. Verify `--purpose` is in `policy.allowed_purposes`.
6. Subprocess-invoke
   `tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py` against
   `--evidence-manifest`. Capture pass/fail and the first `FAIL:` line as
   `failure_reason` on fail.
7. **Refusal:** if `--decision == accepted` and the v0.2.7 verifier exited
   non-zero, print
   `FAIL: evidence_verification_failed: <detail>`
   to stderr and exit **1**. No partial package is written.
8. Compute SHA-256 of the evidence manifest bytes (as-read).
9. Read the sibling `composed-gateway-evidence-report.json` if present and
   look up the `revoked_authority_fails` claim status to derive
   `revocation_review.outcome`:
   - `pass` → `no_revoked_authority_accepted`
   - `fail` or missing → `revoked_authority_rejected`
10. Copy the acceptance policy and the evidence manifest into the output
    directory under their canonical paths.
11. Emit `acceptance-record.json` with deterministic field shape and the
    derived revocation review.
12. Emit `acceptance-package-manifest.json` with the three subjects in the
    fixed v0.2.8 order, each carrying `sha256` and `size_bytes`.
13. Optionally subprocess-invoke the v0.2.8 validator on the produced
    manifest when `--self-validate` is supplied.

---

## 3. Validator steps

(`tools/silver/validate_relying_party_acceptance_record_v0_1_0.py`)

Hash-first, fail-fast ordering. The validator **never** emits
`evidence_verification_failed`; that code belongs only to the generator.

1. Parse manifest. Reject shape, document type, schema version, hash
   algorithm, subject count, role set, role order, limitations or
   non_claims errors with `invalid_acceptance_package_manifest`.
2. Reject any subject `path` containing `..` or starting with `/` with
   `acceptance_subject_path_traversal`.
3. Reject missing files with `acceptance_subject_file_missing`.
4. Recompute SHA-256 for every subject; reject mismatches with
   `acceptance_subject_hash_mismatch`.
5. Parse and structurally validate the acceptance policy. Reject with
   `invalid_acceptance_policy` on shape errors (including malformed JSON,
   missing required fields, wrong document_type, or `allowed_decisions !=
   {accepted, rejected, accepted_with_exceptions}`).
6. Parse and structurally validate the acceptance record. Reject with
   `invalid_acceptance_record` (including malformed JSON, no Python
   traceback).
7. Cross-check `record.relying_party.policy_id` and `.policy_version`
   against `policy.policy_id` and `.policy_version`. Reject with
   `policy_mismatch`.
8. Cross-check `record.relying_party.relying_party_id` against
   `policy.relying_party.relying_party_id`. Reject with
   `relying_party_mismatch`.
9. Cross-check `record.decision.purpose_id` against
   `policy.allowed_purposes`. Reject with `purpose_not_allowed`.
10. Cross-check `record.evidence_package.evidence_type` against
    `policy.allowed_evidence_types`. Reject with
    `evidence_type_not_allowed`.
11. Recompute SHA-256 of the copied evidence manifest. Reject with
    `evidence_manifest_hash_mismatch` if it disagrees with
    `record.evidence_package.manifest_sha256`.
12. Require `record.verification.verifier_tool` to equal
    `policy.required_verification.verifier_tool` and require
    `verification.verification_result` and `verification.verified_at` to be
    present. Reject with `evidence_verification_required`.
13. For `decision.status == "accepted"`, require
    `verification.verification_result == policy.required_verification
    .required_result` (typically `"pass"`). Reject with
    `accepted_record_verification_failed`.
14. For `decision.status == "accepted"`, reject any exception with
    `severity == "blocking"` using
    `accepted_record_has_blocking_exception`.
15. For `decision.status == "accepted_with_exceptions"`, require at least
    one exception with `severity`, `description`, and `effect_on_scope`.
    Reject with `accepted_with_exceptions_missing_exception`.
16. For `decision.status == "rejected"`, require a non-empty
    `decision.rejection_reason` or non-empty
    `verification.failure_reason`. Reject with
    `rejected_record_missing_reason`.
17. When `policy.revocation_requirements.revocation_review_required ==
    true`, require `record.revocation_review.performed == true` and
    `record.revocation_review.outcome` in
    `policy.revocation_requirements.accepted_outcomes`. Reject with
    `revocation_review_missing`.
18. When `policy.challenge_window.required == true`, require
    `opens_at < closes_at` and span_days in
    `[policy.challenge_window.minimum_days,
    policy.challenge_window.maximum_days]`. Reject with
    `challenge_window_invalid`.
19. Require non-empty `record.scope_limitations`. Reject with
    `scope_limitations_missing`.
20. Require non-empty `record.non_claims`. Reject with
    `acceptance_non_claims_missing`.
21. **Optional opt-in:** with `--evidence-package-root <path>`,
    subprocess-invoke the v0.2.7 verifier against
    `<path>/composed-gateway-evidence-manifest.json` and compute its
    sha256. Reject with `external_evidence_verification_failed` on
    non-zero exit **or** when the external sha256 disagrees with
    `record.evidence_package.manifest_sha256`.

---

## 4. Stable failure reasons (22 total)

Validator (21):

```
invalid_acceptance_package_manifest
acceptance_subject_file_missing
acceptance_subject_path_traversal
acceptance_subject_hash_mismatch
invalid_acceptance_policy
invalid_acceptance_record
policy_mismatch
relying_party_mismatch
purpose_not_allowed
evidence_type_not_allowed
evidence_manifest_hash_mismatch
evidence_verification_required
accepted_record_verification_failed
accepted_record_has_blocking_exception
accepted_with_exceptions_missing_exception
rejected_record_missing_reason
revocation_review_missing
challenge_window_invalid
scope_limitations_missing
acceptance_non_claims_missing
external_evidence_verification_failed
```

Generator-only (1):

```
evidence_verification_failed
```

`evidence_verification_required`, `evidence_verification_failed`, and
`external_evidence_verification_failed` are distinct codes:

| Code | Emitted by | Trigger |
|---|---|---|
| `evidence_verification_required` | Validator | Record's verifier metadata missing or disagrees with policy. |
| `evidence_verification_failed` | Generator | Generator's subprocess invocation of the v0.2.7 verifier failed and `--decision accepted` was requested. Exits 1. |
| `external_evidence_verification_failed` | Validator (with `--evidence-package-root`) | Re-invocation of the v0.2.7 verifier against the original package fails, or the original package's manifest sha256 disagrees with the record's manifest sha256. |

---

## 5. Decision status invariants

| Decision status | Required record shape |
|---|---|
| `accepted` | `verification.verification_result` equals policy's required result; no exception has `severity == "blocking"`. |
| `accepted_with_exceptions` | At least one exception with `severity`, `description`, `effect_on_scope`. |
| `rejected` | Non-empty `decision.rejection_reason` or non-empty `verification.failure_reason`. |

---

## 6. Non-claims

- v0.2.8 records local reliance decisions over verified Silver evidence.
  It does not certify the evidence, the system, the gateway, or the
  relying party.
- A relying-party acceptance record is not a Gold certificate, regulator
  approval, third-party audit, or legal acceptance instrument.
- v0.2.8 records acceptance context. It does not execute acceptance
  governance.
- v0.2.8 does not sign the acceptance record. v0.2.8 ships local hash
  anchors only.
- v0.2.8 does not change Bronze, Silver Signed Bundle Assertion,
  Revocation List, Verification Report, Profile, Verifier Output
  Attestation, Multi-principal Authority, Multi-agent Harness,
  Multi-agent Trust-boundary, Evidence Source Adapter, or Composed
  Gateway Evidence semantics.
- The relying party named here (`demo.relying_party`) is fictional. No
  real relying party authored this policy.

---

## 7. Looking ahead

v0.2.8 records a *single* relying party's *local* acceptance decision.
It does not coordinate multiple relying parties, does not chain
acceptances, does not sign the record, does not move toward Gold
conformance, and does not provide governance workflow. Future ProofRail
releases may extend acceptance to multi-party, signed, or governed
forms. v0.2.8 is intentionally the minimum local artifact.
