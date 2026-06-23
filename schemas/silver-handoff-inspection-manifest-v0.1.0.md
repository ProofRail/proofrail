# Silver Handoff Inspection Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.1
**Document type:** `proofrail.silver.handoff_inspection_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.1`

---

## Purpose

The Silver handoff inspection manifest is the package-level SHA-256
hash anchor for a v0.3.1 Silver handoff inspection package. It binds
exactly three subjects in fixed order: the nested v0.3.0 Silver
acceptance handoff manifest, the bound Gold-boundary requirement set,
and the derived inspection report.

The inspection manifest is **not** a certificate, approval, audit, or
trust transfer. It is the integrity anchor over a deterministic local
inspection package whose chain binding the v0.3.1 verifier owns and
re-derives.

The nested v0.3.0 handoff manifest remains responsible for binding the
v0.3.0 handoff package's four subjects and their internal chain
bindings. The v0.3.1 manifest does not duplicate those bindings; the
v0.3.1 verifier subprocess-invokes the unchanged v0.3.0 verifier.

---

## Required top-level fields

```
document_type      — "proofrail.silver.handoff_inspection_manifest"
schema_version     — "v0.1.0"
proofrail_release  — "v0.3.1"
inspection_id      — non-empty string
generated_at       — ISO-8601 UTC, Z-suffixed
hash_algorithm     — "sha256"
subjects           — array of exactly 3 subjects in fixed order
scope_limitations  — array (presence/type checked early; emptiness checked later)
non_claims         — array (presence/type checked early; emptiness checked later)
```

---

## Subjects (fixed order, fixed roles)

```
[0] path: "silver-acceptance-handoff/silver-acceptance-handoff-manifest.json"
    role: "silver_acceptance_handoff_manifest"
[1] path: "gold-boundary-requirements.json"
    role: "gold_boundary_requirement_set"
[2] path: "silver-handoff-inspection-report.json"
    role: "silver_handoff_inspection_report"
```

Each subject MUST include:

```
path        — non-empty string, relative to the inspection package root
role        — exactly one of the three role strings above
sha256      — "sha256:<hex>"
size_bytes  — integer >= 0
```

A subject whose path is absolute or contains a `..` path component
raises `inspection_subject_path_traversal`. A missing subject file
raises `inspection_subject_file_missing`. A subject whose recomputed
SHA-256 disagrees with the recorded value raises
`inspection_subject_hash_mismatch`.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and typed as arrays
(`invalid_inspection_manifest` on missing key or wrong type). Empty
arrays or arrays with blank / whitespace-only entries raise the
specific reasons `inspection_limitations_missing` and
`inspection_non_claims_missing` respectively, not the generic
`invalid_inspection_manifest`.

---

## Verifier-owned bindings

The v0.3.1 verifier proves:

```
included v0.3.0 handoff manifest  == subject[0] sha256
                                  == report base_handoff.handoff_manifest_sha256
                                  == nested v0.3.0 handoff verifier PASSes

included requirement set          == subject[1] sha256
                                  == report gold_gap_inventory.requirements_sha256

included inspection report        == subject[2] sha256
```

---

## Non-claims about this schema

- The manifest is not a certificate.
- The manifest is not a Gold readiness assessment.
- The manifest is not regulator approval, auditor approval, legal
  advice, or production authorization.
- The manifest does not change the underlying v0.3.0 handoff package
  contents.
