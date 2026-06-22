# Silver Relying-Party Acceptance Package Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.8
**Document type:** `proofrail.silver.relying_party_acceptance_package_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.8`

---

## Purpose

The acceptance package manifest is the package-level hash anchor for the
v0.2.8 relying-party acceptance package. It records the SHA-256 of every
subject in a fixed, deterministic order, plus a non-empty `limitations`
list and a non-empty `non_claims` list.

It is emitted by
`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py` and
verified by
`tools/silver/validate_relying_party_acceptance_record_v0_1_0.py`.

---

## Required top-level fields

```
document_type     — "proofrail.silver.relying_party_acceptance_package_manifest"
schema_version    — "v0.1.0"
proofrail_release — "v0.2.8"
package_id        — non-empty string
generated_at      — ISO-8601 timestamp (UTC, Z-suffixed)
hash_algorithm    — "sha256"
package_root      — "."
subjects          — array of exactly three subjects, in deterministic order
limitations       — non-empty array of non-empty strings
non_claims        — non-empty array of non-empty strings
```

---

## `subjects` (deterministic order)

The `subjects` array MUST contain exactly three entries, in this order:

```
[0] acceptance-policy.json                            role: acceptance_policy
[1] evidence/composed-gateway-evidence-manifest.json  role: verified_evidence_manifest
[2] acceptance-record.json                            role: acceptance_record
```

Each subject is an object with:

| Field | Type | Notes |
|---|---|---|
| `path` | string | Package-local relative path; no `..`; not absolute |
| `role` | string | One of the three fixed roles above |
| `sha256` | string | `"sha256:<hex>"` of the file at `path` |
| `size_bytes` | integer | File size in bytes |

The validator:

- Rejects any `path` containing `..` or starting with `/` with
  `acceptance_subject_path_traversal`.
- Rejects any missing file with `acceptance_subject_file_missing`.
- Rejects any mismatch between recomputed SHA-256 and recorded `sha256`
  with `acceptance_subject_hash_mismatch`.
- Rejects manifests whose document type, schema version, subject count,
  ordering, role set, or required field shape diverges from this schema
  with `invalid_acceptance_package_manifest`.

---

## `limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected only for non-emptiness.

---

## Non-claims about this schema

- The manifest is not signed.
- The manifest does not establish Gold conformance.
- The manifest does not certify the underlying evidence.
- The manifest does not record an institutional or legal acceptance.
