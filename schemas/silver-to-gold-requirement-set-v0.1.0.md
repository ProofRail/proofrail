# Silver-to-Gold Requirement Set — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.1
**Document type:** `proofrail.silver_to_gold.requirement_set`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.1`

---

## Purpose

The Silver-to-Gold requirement set is a deterministic, committed,
intentionally local inventory of governance prerequisites that a future
Gold layer would have to satisfy. It is consumed by the v0.3.1 Silver
handoff inspector to produce a Gold-boundary gap inventory section
inside the inspection report.

A requirement set is **not** an external compliance standard, legal
framework, regulator approval criterion, or auditor scope. It is a
ProofRail demo boundary inventory used to make the gap to future Gold
governed reliance visible.

---

## Required top-level fields

```
document_type            — "proofrail.silver_to_gold.requirement_set"
schema_version           — "v0.1.0"
proofrail_release        — "v0.3.1"
requirement_set_id       — non-empty string
requirement_set_version  — non-empty string (e.g. "v0.1.0")
scope                    — non-empty string
requirements             — array, exactly 13 entries (see §Required domains)
scope_limitations        — non-empty array of non-empty strings
non_claims               — non-empty array of non-empty strings
```

Each `requirements[]` entry MUST contain:

```
requirement_id           — non-empty string, unique within the set
domain                   — string from the required domain set, unique within the set
title                    — non-empty string
gold_prerequisite        — non-empty string
silver_evidence_mapping  — array (possibly empty) of non-empty strings
expected_gap_status      — one of the closed status set (see below)
reason                   — non-empty string
```

---

## Required domains

The requirement set MUST include exactly one row per each of these 13
domains:

```
governed_acceptance_policy
named_acceptance_authority
independent_verifier_identity
evidence_retention_policy
change_control_policy
revocation_operations
challenge_dispute_process
audit_trail_and_review
runtime_operating_boundary
external_accountability
public_or_shared_acceptance_record
legal_or_contractual_basis
production_use_authorization
```

A missing or duplicated required domain raises
`requirement_domain_missing`. A duplicate `requirement_id` or duplicate
`domain` raises `requirement_duplicate`. Other malformed-structure /
unknown-status errors raise `requirement_set_invalid`.

---

## Closed `expected_gap_status` set

```
silver_evidence_present
silver_evidence_partial
gold_prerequisite_unmet
out_of_scope_for_silver
```

### Status semantics

- `silver_evidence_present` — Relevant Silver evidence is *present*
  inside the ProofRail Silver chain. **This does not mean the Gold
  prerequisite is satisfied.** It means the inspection can point at a
  concrete, hash-anchored Silver artifact that addresses the domain.
- `silver_evidence_partial` — Silver provides only a drill, fixture, or
  local artifact for the domain, not an operational process. The
  inspection can point at related Silver evidence but the Gold
  prerequisite is not fully addressed.
- `gold_prerequisite_unmet` — The Silver chain does not establish the
  governed-reliance prerequisite. The gap is preserved in the inventory.
- `out_of_scope_for_silver` — The domain is outside what any ProofRail
  Silver release is intended to provide (for example, legal authority).

The happy-path fixture distribution for v0.3.1:

```
silver_evidence_present       1   (independent_verifier_identity)
silver_evidence_partial       4   (revocation_operations,
                                  challenge_dispute_process,
                                  audit_trail_and_review,
                                  runtime_operating_boundary)
gold_prerequisite_unmet       6
out_of_scope_for_silver       2
```

At least one row MUST be `gold_prerequisite_unmet`. The report-level
`gold_boundary_status` MUST remain `gold_not_claimed`. No row may
claim Gold readiness, certification, approval, audit, legal effect,
production authorization, or transferred trust.

---

## Overclaim guard

The v0.3.1 verifier recursively scans every string value in the
requirement set **outside** the `scope_limitations` and `non_claims`
arrays for these forbidden positive tokens (case-insensitive substring
match):

```
"certified", "approved", "audited",
"legally accepted", "legally revoked",
"challenge resolved",
"gold accepted", "gold certified",
"compliant", "production-approved", "production-ready",
"regulator-ready", "regulator approval",
"trust transferred", "trust transfer",
"gold-ready", "gold ready", "gold_ready"
```

Any positive occurrence raises `inspection_gold_overclaim`. The same
tokens may appear inside `scope_limitations` and `non_claims` (where
they typically appear in negated form to **deny** the overclaim).

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and typed as arrays. Empty arrays or
arrays containing blank / whitespace-only entries raise the specific
reasons `inspection_limitations_missing` or
`inspection_non_claims_missing` respectively (not the generic
`requirement_set_invalid`).

---

## Non-claims about this schema

- A requirement set is not a Gold certification standard.
- A requirement set is not legal advice, regulator approval, or
  auditor approval.
- A requirement set is not a compliance crosswalk to any external
  framework.
- A requirement set is not an assertion that the Silver chain is
  Gold-ready.
- A requirement set is a *local* ProofRail demo inventory used to make
  the gap to future Gold governed reliance visible.
