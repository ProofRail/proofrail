# Silver Relying-Party Acceptance Policy — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.8
**Document type:** `proofrail.silver.relying_party_acceptance_policy`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.8`

---

## Purpose

A relying-party acceptance policy is a local, structured statement of what
a relying party will accept, for which purposes, over which evidence types,
under which verification requirements, with which revocation review, and
within which challenge window. It is the *input* to the v0.2.8 acceptance
record generator.

It is not a certification policy, not a regulator approval policy, and not
a legal acceptance instrument. It is a deterministic local fixture that
the relying party owns.

---

## Required top-level fields

```
document_type        — "proofrail.silver.relying_party_acceptance_policy"
schema_version       — "v0.1.0"
proofrail_release    — "v0.2.8"
policy_id            — non-empty string
policy_version       — non-empty string
relying_party        — object (see §relying_party)
allowed_purposes     — non-empty array of non-empty strings
allowed_evidence_types
                     — non-empty array of non-empty strings
required_verification
                     — object (see §required_verification)
revocation_requirements
                     — object (see §revocation_requirements)
challenge_window     — object (see §challenge_window)
allowed_decisions    — array containing exactly the three strings
                       "accepted", "rejected", "accepted_with_exceptions"
                       (order does not matter; set equality is checked)
non_claims           — non-empty array of non-empty strings
```

---

## `relying_party`

```
relying_party_id  — non-empty string (e.g. "demo.relying_party")
display_name      — non-empty string
```

---

## `required_verification`

```
verifier_tool     — non-empty repo-relative path string
                    (e.g. "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py")
required_result   — non-empty string (e.g. "pass")
```

---

## `revocation_requirements`

```
revocation_review_required   — boolean
accepted_outcomes            — array of non-empty strings;
                               MUST be non-empty when
                               revocation_review_required is true
```

---

## `challenge_window`

```
required        — boolean
minimum_days    — integer >= 0; MUST be present when required is true
maximum_days    — integer >= minimum_days; MUST be present when required is true
```

---

## `non_claims`

Non-empty array of non-empty strings. Entries are inspected only for
non-emptiness. Each entry is a sentence declaring something the policy
does NOT establish (e.g. "This policy is not Gold certification.").

---

## Validator behavior

The v0.2.8 acceptance record validator parses this policy as part of
package validation. Structural violations raise `invalid_acceptance_policy`.
Cross-checks (purpose, evidence type, verifier tool, revocation, challenge
window) raise more specific reasons; see the acceptance record schema
and the validator.

---

## Non-claims about this schema

- This schema does not define Gold certification policy.
- This schema does not define third-party audit policy.
- This schema does not encode legal acceptance terms.
- This schema does not assert that any relying party is institutionally
  authorized to bind anyone other than itself.
