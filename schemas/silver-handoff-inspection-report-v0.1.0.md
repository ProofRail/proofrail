# Silver Handoff Inspection Report — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.1
**Document type:** `proofrail.silver.handoff_inspection_report`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.1`

---

## Purpose

The Silver handoff inspection report is a deterministic local artifact
emitted by `tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py`.
It re-derives the observable facts of a verified v0.3.0 Silver
acceptance handoff package and binds them to a fixed local
Gold-boundary requirement set.

It is **not** a Gold certificate, Gold readiness assessment, regulator
approval, third-party audit, legal acceptance, legal revocation,
compliance certification, or production authorization. It preserves
the difference between verified Silver evidence and missing governed
commitments.

It is **not** hand-authored. Every field is re-derived by the v0.3.1
verifier from the nested v0.3.0 handoff summary and the bound
requirement set.

---

## Required top-level fields

```
document_type      — "proofrail.silver.handoff_inspection_report"
schema_version     — "v0.1.0"
proofrail_release  — "v0.3.1"
inspection_id      — non-empty string
generated_at       — ISO-8601 UTC, Z-suffixed
base_handoff       — object (see below)
handoff_summary    — object (see below)
component_inspection — array of exactly 4 component rows
gold_gap_inventory — object (see below)
scope_limitations  — array (presence/type checked early;
                    emptiness/blank entries checked later)
non_claims         — array (presence/type checked early;
                    emptiness/blank entries checked later)
```

---

## `base_handoff`

```
handoff_id                    — non-empty string (copied from nested v0.3.0 summary)
handoff_manifest_path         — "silver-acceptance-handoff/silver-acceptance-handoff-manifest.json"
handoff_manifest_sha256       — "sha256:<hex>" (== manifest subject[0] sha256)
handoff_verification_status   — "pass"
```

The verifier raises `inspection_report_binding_mismatch` if
`handoff_manifest_sha256` does not equal the inspection manifest
subject[0] sha256.

---

## `handoff_summary`

Re-derived from the nested v0.3.0 handoff summary:

```
acceptance_record_id          — copied from included_chain.relying_party_acceptance.acceptance_record_id
decision_status               — copied from included_chain.relying_party_acceptance.decision_status
purpose_id                    — copied from included_chain.relying_party_acceptance.purpose_id
recommended_handoff_posture   — copied from handoff_result.recommended_handoff_posture
reuse_warning                 — copied from handoff_result.reuse_warning
```

**Verifier ordering (amended):**

- `inspection_handoff_summary_mismatch` is reserved for disagreement on
  the non-posture fields (`acceptance_record_id`, `decision_status`,
  `purpose_id`).
- `inspection_review_posture_downgrade` is reserved for posture issues:
  a `recommended_handoff_posture` whose rank is **lower** than the
  v0.3.0 handoff summary's posture rank, or a missing / blank
  `reuse_warning` when the v0.3.0 summary's posture rank is ≥ 1.

---

## `component_inspection`

Exactly four rows, in fixed order, derived from the nested v0.3.0
handoff manifest subjects:

```
[0] component_id: "v0.2.7-composed-gateway-evidence"
    component_type: "composed_gateway_evidence"
    source_release: "v0.2.7"
    inspection_status: "present_and_verified"
[1] component_id: "v0.2.8-relying-party-acceptance"
    component_type: "relying_party_acceptance"
    source_release: "v0.2.8"
    inspection_status: "present_and_verified"
[2] component_id: "v0.2.9-revocation-challenge-drill"
    component_type: "revocation_challenge_drill"
    source_release: "v0.2.9"
    inspection_status: "present_and_verified"
[3] component_id: "v0.3.0-silver-acceptance-handoff"
    component_type: "silver_acceptance_handoff"
    source_release: "v0.3.0"
    inspection_status: "present_and_verified"
```

Closed `inspection_status` set:

```
present_and_verified
present_with_warning
not_inspected
```

The verifier raises `inspection_component_status_mismatch` on any
disagreement.

---

## `gold_gap_inventory`

```
requirement_set_id          — copied from requirement set
requirement_set_version     — copied from requirement set
requirements_path           — "gold-boundary-requirements.json"
requirements_sha256         — "sha256:<hex>" (== manifest subject[1] sha256)
requirement_count           — int, equals len(requirements)
gold_boundary_status        — "gold_not_claimed" | "gold_gap_inventory_only"
gold_prerequisites_unmet    — bool
counts                      — object (see below)
requirements                — array of per-requirement rows
```

### `counts`

```
silver_evidence_present   — int (count of rows with that gap_status)
silver_evidence_partial   — int
gold_prerequisite_unmet   — int
out_of_scope_for_silver   — int
```

Counts MUST be recomputed by the runner from the row statuses and
MUST equal the recomputed values in the verifier. Hand-authored counts
raise `inspection_count_mismatch`.

### `requirements[]` rows

```
requirement_id     — copied from requirement set
domain             — copied from requirement set
gap_status         — equals requirement set's expected_gap_status
evidence_refs      — array of non-empty strings
reason             — copied from requirement set
```

The verifier raises:

- `inspection_requirement_missing` if a requirement set row has no
  matching report row;
- `inspection_requirement_status_mismatch` if `gap_status` disagrees
  with the requirement set's `expected_gap_status` (any direction).

### Closed `gold_boundary_status` set

```
gold_not_claimed
gold_gap_inventory_only
```

`gold_boundary_status` MUST be `gold_not_claimed` when any row is
`silver_evidence_partial`, `gold_prerequisite_unmet`, or
`out_of_scope_for_silver`. Any other status (e.g. `gold_ready`,
`gold_valid`, `gold_certified`) raises
`inspection_gold_status_invalid`.

---

## Overclaim guard

The verifier recursively scans every string value in the report
**outside** the `scope_limitations` and `non_claims` arrays for the
same forbidden positive tokens listed in the requirement set schema
plus `"gold-ready"`, `"gold ready"`, `"gold_ready"`. Any positive
occurrence raises `inspection_gold_overclaim`.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and typed as arrays
(`inspection_report_invalid` on missing or wrong type). Empty arrays or
arrays with blank / whitespace-only entries raise the specific reasons
`inspection_limitations_missing` and `inspection_non_claims_missing`
respectively.

---

## Non-claims about this schema

- The report is not a Gold certificate.
- The report is not a Gold readiness assessment.
- The report is not regulator approval, auditor approval, legal
  advice, or production authorization.
- The report is not a downstream-reliance recommendation.
- The report does not adjudicate any challenge or revocation.
- The report does not transfer reliance.
