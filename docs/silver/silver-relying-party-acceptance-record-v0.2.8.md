# Silver Relying-Party Acceptance Record — v0.2.8

**Status:** Draft / Composed Silver demo release
**Date:** 2026-06-22
**Schemas:**
- `schemas/silver-relying-party-acceptance-policy-v0.1.0.md`
- `schemas/silver-relying-party-acceptance-record-v0.1.0.md`
- `schemas/silver-relying-party-acceptance-package-manifest-v0.1.0.md`

---

## What v0.2.8 Adds

Silver v0.2.8 introduces the **Relying-Party Acceptance Record**: a
deterministic, hash-anchored local artifact that records a single relying
party's decision (accept / reject / accept-with-exceptions) over a verified
v0.2.7 composed gateway evidence package, bound to a named local policy, a
declared purpose, the v0.2.7 verifier outcome, revocation review,
exceptions, scope limitations, challenge window, and non-claims.

Core sentence (preserved across docs):

> v0.2.8 records a relying party's local acceptance decision over verified
> Silver evidence. It does not certify the evidence, the system, the
> gateway, or the relying party.

A relying-party acceptance record is not a Gold certificate, regulator
approval, third-party audit, or legal acceptance instrument.

v0.2.8 records acceptance context. It does not execute acceptance
governance.

---

## Position in the Stack

| Layer | Role |
|---|---|
| Bronze | Claim about a deployment and its evidence files. |
| Silver | Cross-cutting controls — signing, revocation, conformance, attestation, fixtures, adapters, composition, **acceptance**. |
| Gold | Out of scope for v0.2.8. |

v0.2.8 sits **on top of** v0.2.7. The v0.2.7 release produces a composed,
locally verifiable gateway evidence package. v0.2.8 adds a relying-party
acceptance record that *consumes* that package as input. v0.2.8 does not
re-derive any v0.2.7 claim; it consults the v0.2.7 verifier as a
subprocess and records its pass/fail outcome.

ProofRail is not the gateway, not the SIEM, not the policy engine, not the
GRC platform, not the relying party. ProofRail records the shape of the
acceptance and what each record does **not** assert.

---

## Three v0.2.8 Schemas

| Schema | Role |
|---|---|
| `proofrail.silver.relying_party_acceptance_policy` v0.1.0 | Static local policy declaring relying-party id, allowed purposes, allowed evidence types, required verification, revocation requirements, challenge window, and allowed decisions. |
| `proofrail.silver.relying_party_acceptance_record` v0.1.0 | The acceptance decision itself: relying party / policy binding, decision (status + purpose + decision maker + timestamps + rejection reason), evidence package anchor, verification outcome, revocation review, exceptions, scope limitations, challenge window, non-claims. |
| `proofrail.silver.relying_party_acceptance_package_manifest` v0.1.0 | Three-subject deterministic package manifest binding the policy, the verified evidence manifest, and the record. |

The package manifest's subject order is fixed:

1. `acceptance-policy.json` — role `acceptance_policy`
2. `evidence/composed-gateway-evidence-manifest.json` — role
   `verified_evidence_manifest`
3. `acceptance-record.json` — role `acceptance_record`

Only the copied v0.2.7 **manifest** is included in the v0.2.8 package; the
full v0.2.7 package remains external.

---

## Allowed Decisions

```
accepted
rejected
accepted_with_exceptions
```

Decision status invariants:

| Decision status | Required record shape |
|---|---|
| `accepted` | `verification.verification_result` equals `policy.required_verification.required_result`; no exception has `severity == "blocking"`. |
| `accepted_with_exceptions` | At least one exception with `severity`, `description`, `effect_on_scope`. |
| `rejected` | Non-empty `decision.rejection_reason` or non-empty `verification.failure_reason`. |

---

## Generator (`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`)

```bash
python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py \
  --policy fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json \
  --evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at 2026-06-22T00:00:00Z \
  --challenge-closes-at 2026-07-22T00:00:00Z \
  --output-dir /tmp/proofrail-silver-relying-party-acceptance-v0.2.8 \
  --force
```

Key behaviors:

- Subprocess-invokes `tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`
  on the supplied `--evidence-manifest`.
- For `--decision accepted` with a non-zero v0.2.7 verifier exit, refuses
  generation with stderr `FAIL: evidence_verification_failed: <detail>`
  and **exit 1**. No partial package is written.
- Derives `revocation_review.outcome` from the sibling
  `composed-gateway-evidence-report.json`'s `revoked_authority_fails`
  claim status when present.
- Emits the four-file package layout with deterministic JSON
  (`json.dumps(obj, indent=2, sort_keys=True) + "\n"`).
- `--self-validate` optionally subprocess-invokes the validator after
  emission.

Exit codes: `0` success, `1` generation refused / self-validate failed,
`2` usage or input error.

---

## Validator (`tools/silver/validate_relying_party_acceptance_record_v0_1_0.py`)

```bash
python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py \
  --manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]
```

Hash-first, fail-fast. The validator runs 22 ordered checks and **never**
emits `evidence_verification_failed` (that code belongs only to the
generator). With the optional `--evidence-package-root` flag, the
validator re-invokes the v0.2.7 verifier against the original package and
re-checks the manifest sha256.

---

## Verification-related Codes

Three codes are deliberately distinct:

| Code | Emitted by | Trigger |
|---|---|---|
| `evidence_verification_required` | Validator | Record's verifier metadata missing or disagrees with policy. Always available; no flag needed. |
| `evidence_verification_failed` | Generator | Subprocess invocation of the v0.2.7 verifier failed and `--decision accepted` was requested. Exits 1. Never emitted by the validator. |
| `external_evidence_verification_failed` | Validator (with `--evidence-package-root`) | Re-invocation of the v0.2.7 verifier against the supplied original package fails, or the original package's manifest sha256 disagrees with the record's manifest sha256. |

---

## Stable Failure Reasons (22)

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

---

## Fixture

`fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json`
declares a static demo relying party
(`demo.relying_party`, policy `proofrail-demo-relying-party-policy-v0.2.8`
v0.1.0) with:

- `allowed_purposes: ["demo_trust_boundary_review"]`
- `allowed_evidence_types:
  ["proofrail.silver.composed_gateway_evidence_manifest"]`
- `required_verification.verifier_tool:
  tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`,
  `required_result: "pass"`
- `revocation_requirements.revocation_review_required: true`,
  `accepted_outcomes: ["no_revoked_authority_accepted",
  "revoked_authority_rejected"]`
- `challenge_window.required: true`, `minimum_days: 7`,
  `maximum_days: 90`
- `allowed_decisions:
  ["accepted", "rejected", "accepted_with_exceptions"]`

The fixture is *demo only* and describes a fictional relying party. It is
not a Gold policy, not a third-party audit policy, and not an
institutional policy for any real relying party.

---

## Regression Test

`tests/test_silver_relying_party_acceptance_record_v0_2_8.sh` exercises
the generator and validator with a 30-case battery. The test uses
`mktemp -d` with `trap` cleanup, copies a fresh package for each tamper
case, and recomputes manifest hashes for the mutated subject so semantic
checks are reached when intended.

Cases (30):

1. Compose v0.2.7 evidence into tmp.
2. Generate accepted acceptance package over that evidence.
3. Validate the pristine acceptance package.
4. Validate the pristine package with `--evidence-package-root` over the
   original v0.2.7 package.
5. Inline check manifest subject order.
6. Inline check record fields (status, purpose, policy id/version,
   verifier, revocation, challenge, scope, non_claims).
7. Tamper record bytes without rehash →
   `acceptance_subject_hash_mismatch`.
8. Remove copied evidence manifest → `acceptance_subject_file_missing`.
9. Manifest subject path `..` → `acceptance_subject_path_traversal`.
10. Manifest subject path absolute → `acceptance_subject_path_traversal`.
11. Malformed acceptance record JSON + rehash →
    `invalid_acceptance_record` (no Python traceback).
12. Mutate package manifest document_type →
    `invalid_acceptance_package_manifest`.
13. Mutate policy document_type + rehash → `invalid_acceptance_policy`.
14. Mutate record `verification.verifier_tool` + rehash →
    `evidence_verification_required`.
15. Record `policy_id` mismatch + rehash → `policy_mismatch`.
16. Record `relying_party_id` mismatch + rehash →
    `relying_party_mismatch`.
17. Record purpose not in `policy.allowed_purposes` + rehash →
    `purpose_not_allowed`.
18. Record evidence_type not in `policy.allowed_evidence_types` + rehash
    → `evidence_type_not_allowed`.
19. Record `evidence_package.manifest_sha256` mutated + rehash →
    `evidence_manifest_hash_mismatch`.
20. Accepted record with `verification_result == fail` + rehash →
    `accepted_record_verification_failed`.
21. Accepted record with a blocking exception + rehash →
    `accepted_record_has_blocking_exception`.
22. `accepted_with_exceptions` with no exception + rehash →
    `accepted_with_exceptions_missing_exception`.
23. Rejected record without `rejection_reason` or `failure_reason` +
    rehash → `rejected_record_missing_reason`.
24. Remove revocation review + rehash → `revocation_review_missing`.
25. Challenge window shorter than policy minimum + rehash →
    `challenge_window_invalid`.
26. Empty `scope_limitations` + rehash → `scope_limitations_missing`.
27. Empty `non_claims` + rehash → `acceptance_non_claims_missing`.
28. Tamper original v0.2.7 package + validate w/
    `--evidence-package-root` → `external_evidence_verification_failed`.
29. Generator: tamper v0.2.7 evidence, run generator with
    `--decision accepted` → stderr
    `FAIL: evidence_verification_failed:` + exit 1 + no Python
    traceback.
30. Scoped mutation check: committed v0.2.8 schemas, fixture, tools,
    demo docs, release doc, and test are unchanged by the test runtime.

These 30 cases collectively exercise all 21 validator stable failure
reasons plus the generator-only `evidence_verification_failed` code.

The test prints
`=== ProofRail Silver v0.2.8 relying-party acceptance record: 30/30 PASS ===`
on success.

---

## Make Targets

- `make run-silver-relying-party-acceptance-demo-v0-2-8` — Compose the
  underlying v0.2.7 evidence and generate the v0.2.8 acceptance package
  into temporary directories.
- `make verify-silver-relying-party-acceptance-demo-v0-2-8` — Run the
  30-step regression test.

`verify-silver-relying-party-acceptance-demo-v0-2-8` is appended to
`verify-silver-all`. Bronze artifacts are restored after a full
`verify-silver-all` run to preserve clean-clone reproducibility for
Bronze demos.

---

## What v0.2.8 Does Not Do

- Does not integrate with any real relying party, governance workflow,
  GRC platform, ticketing system, sign-off authority, regulator, or
  auditor.
- Does not certify the evidence, the system, the gateway, or the
  relying party.
- Does not sign the acceptance record. v0.2.8 ships local hash anchors
  only.
- Does not coordinate multiple relying parties or chain acceptances.
- Does not establish a new trust authority. The relying party records
  *its own* acceptance; it does not authorize anything else.
- Does not execute or affect any protected action.
- Does not change Bronze, Silver Signed Bundle Assertion, Revocation
  List, Verification Report, Profile, Verifier Output Attestation,
  Multi-principal Authority, Multi-agent Harness, Multi-agent
  Trust-boundary, Evidence Source Adapter, or Composed Gateway Evidence
  semantics.
- The relying party in the demo fixture is fictional. No real relying
  party authored that policy.

The v0.2.8 release is a composed-demo release, intentionally narrow in
scope and conservative in claim.
