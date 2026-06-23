# Silver Handoff Inspector + Gold Gap Inventory (v0.3.1)

**Status:** Released / ProofRail v0.3.1
**Release thesis:** ProofRail v0.3.1 makes a v0.3.0 Silver acceptance
handoff package independently inspectable, producing a deterministic
review report that summarizes the verified chain, the carried-forward
caution posture, and the unresolved Gold-boundary gaps — without
claiming Gold readiness, Gold certification, regulator approval,
auditor approval, legal acceptance, production authorization, or
governed reliance.

---

## What v0.3.1 adds

v0.3.1 does **not** introduce a new evidence source, signature scheme,
trust authority, or runtime substrate. It introduces a single,
deterministic, local artifact:

> **A Silver handoff inspection package** that binds three subjects in
> fixed order — the unchanged v0.3.0 handoff manifest, a committed
> local Gold-boundary requirement set, and a re-derived inspection
> report — anchored by a 3-subject SHA-256 manifest.

The inspection package is **not** a certificate, audit, regulator
review, legal acceptance, or downstream-reliance recommendation. It is
the integrity anchor over a local review that preserves the difference
between verified Silver evidence and missing governed commitments.

## Boundary surfaced by v0.3.1

The inspection report explicitly records, for each of 13 governance
domains, one of four closed-set statuses:

```
silver_evidence_present       Silver evidence is present at this domain
silver_evidence_partial       Silver provides only a drill / local artifact
gold_prerequisite_unmet       Silver does not address this domain
out_of_scope_for_silver       Domain is outside any ProofRail Silver scope
```

`silver_evidence_present` means relevant Silver evidence is present
inside the ProofRail Silver chain. **It does not mean the Gold
prerequisite is satisfied.** The report-level `gold_boundary_status`
is forced to `gold_not_claimed` whenever any row is `silver_evidence_partial`,
`gold_prerequisite_unmet`, or `out_of_scope_for_silver`.

The 13 required domains are: `governed_acceptance_policy`,
`named_acceptance_authority`, `independent_verifier_identity`,
`evidence_retention_policy`, `change_control_policy`,
`revocation_operations`, `challenge_dispute_process`,
`audit_trail_and_review`, `runtime_operating_boundary`,
`external_accountability`, `public_or_shared_acceptance_record`,
`legal_or_contractual_basis`, `production_use_authorization`.

## Artifacts

### Schemas

- `schemas/silver-to-gold-requirement-set-v0.1.0.md`
- `schemas/silver-handoff-inspection-report-v0.1.0.md`
- `schemas/silver-handoff-inspection-manifest-v0.1.0.md`

### Fixture

- `fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json`
  (13-row committed Gold-boundary requirement set with deterministic
  status distribution: 1 present / 4 partial / 6 unmet / 2 out-of-scope)

### Tools

- `tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py` — runner
- `tools/silver/verify_silver_handoff_inspection_v0_1_0.py` — verifier
  (also exposes a `--validate-requirement-set` entry point used by the
  runner)

### Demo

- `demos/silver-demo-008-handoff-inspector-gap-inventory/`

### Regression test

- `tests/test_silver_handoff_inspector_v0_3_1.sh`

### Make targets

- `make run-silver-handoff-inspection-v0-3-1`
- `make verify-silver-handoff-inspection-v0-3-1`

`make verify-silver-all` now ends with `verify-silver-handoff-inspection-v0-3-1`.

## Inspection package layout

```
silver-handoff-inspection-package/
├── silver-acceptance-handoff/                    (byte-copy of v0.3.0)
│   ├── composed-gateway-evidence/                (v0.2.7 nested)
│   ├── acceptance-package/                       (v0.2.8 nested)
│   ├── revocation-challenge-drill/               (v0.2.9 nested)
│   ├── silver-acceptance-handoff-summary.json
│   └── silver-acceptance-handoff-manifest.json   (subject [0])
├── gold-boundary-requirements.json               (subject [1])
├── silver-handoff-inspection-report.json         (subject [2])
└── silver-handoff-inspection-manifest.json       (3-subject anchor)
```

## Stable failure reasons (20 verifier reasons + 3 runner-only)

### Verifier reasons (20)

```
invalid_inspection_manifest
inspection_subject_path_traversal
inspection_subject_file_missing
inspection_subject_hash_mismatch
inspection_limitations_missing
inspection_non_claims_missing
requirement_set_invalid
requirement_duplicate
requirement_domain_missing
inspection_report_invalid
inspection_report_binding_mismatch
inspection_handoff_summary_mismatch
inspection_review_posture_downgrade
inspection_component_status_mismatch
inspection_requirement_missing
inspection_requirement_status_mismatch
inspection_count_mismatch
inspection_gold_status_invalid
inspection_gold_overclaim
nested_handoff_invalid
```

### Runner-only refusal codes (3)

```
handoff_validation_failed
requirement_set_validation_failed
inspection_self_validation_failed
```

The runner-only codes are deliberately distinct from the verifier
reasons and are never emitted by the verifier.

## Verifier ordering (amended)

The v0.3.1 verifier preserves four important reachability invariants:

1. **`inspection_handoff_summary_mismatch` is reserved for non-posture
   summary fields** (`acceptance_record_id`, `decision_status`,
   `purpose_id`). It is NOT raised for posture or `reuse_warning`.

2. **`inspection_review_posture_downgrade` is reserved for the posture
   path:**
   - `recommended_handoff_posture` rank weaker than the nested v0.3.0
     summary's rank, OR
   - missing / blank `reuse_warning` when the nested rank is ≥ 1.

   The posture path is reached even when the non-posture cross-checks
   pass, so this reason is independently reachable.

3. **`inspection_limitations_missing` and `inspection_non_claims_missing`
   are reachable.** Early structural validators
   (`invalid_inspection_manifest`, `requirement_set_invalid`,
   `inspection_report_invalid`) only check presence and type. Empty
   arrays and blank entries surface later under the dedicated reasons.

4. **`requirement_duplicate` and `requirement_domain_missing` are
   reachable.** The generic `requirement_set_invalid` covers only
   malformed structure / unknown status. Duplicate ids or domains use
   `requirement_duplicate`. Missing required domains use
   `requirement_domain_missing`.

## What v0.3.1 deliberately does NOT do

- It does not introduce a new evidence source.
- It does not add a Gold certificate, Gold readiness scorecard, or
  Gold conformance assertion.
- It does not assert regulator approval, auditor approval, legal
  acceptance, or production authorization.
- It does not adjudicate any challenge, revocation, or dispute signal
  preserved in the v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 chain.
- It does not transfer reliance from the original v0.2.8 relying party
  to any downstream party.
- It does not consult an external compliance standard. The
  Gold-boundary requirement set is a local ProofRail demo inventory.
- It does not modify any v0.2.x or v0.3.0 schema, tool, fixture, demo,
  test, or Make target.

## Why this matters

v0.3.0 produces a portable handoff package. An independent reviewer
could already re-verify the chain. What v0.3.0 did **not** produce was
a deterministic, hash-anchored review *output* the reviewer's local
process could keep — one that explicitly names the governed-reliance
prerequisites Silver does NOT satisfy, so that downstream parties
cannot read the Silver chain as a Gold certificate.

v0.3.1 produces exactly that output, with all 20 stable failure reasons
independently reachable so that the report cannot be edited to overclaim
without being rejected by the verifier.

## Non-claims summary

- The inspection package is not a Gold certificate.
- The inspection package is not a Gold readiness assessment.
- The inspection package is not regulator approval, auditor approval,
  or legal acceptance.
- The inspection package does not authorize production use.
- The inspection package does not transfer reliance.
- The inspection package does not adjudicate any challenge or
  revocation signal.
- `silver_evidence_present` does not mean a Gold prerequisite is
  satisfied.
- The bound Gold-boundary requirement set is a local ProofRail demo
  inventory, not an external compliance standard.
