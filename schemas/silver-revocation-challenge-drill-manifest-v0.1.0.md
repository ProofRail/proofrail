# Silver Revocation/Challenge Drill Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.9
**Document type:** `proofrail.silver.revocation_challenge_drill_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.9`

---

## Purpose

The drill manifest is the package-level hash anchor for the v0.2.9
revocation/challenge drill package. It records the SHA-256 of every
subject in a fixed, deterministic order, plus a non-empty
`scope_limitations` list and a non-empty `non_claims` list.

It is emitted by
`tools/silver/run_revocation_challenge_drill_v0_1_0.py` and verified by
`tools/silver/verify_revocation_challenge_drill_v0_1_0.py`.

---

## Required top-level fields

```
document_type     — "proofrail.silver.revocation_challenge_drill_manifest"
schema_version    — "v0.1.0"
proofrail_release — "v0.2.9"
drill_id          — non-empty string
generated_at      — ISO-8601 UTC, Z-suffixed
hash_algorithm    — "sha256"
package_root      — "."
subjects          — array of exactly three subjects, in deterministic order
scope_limitations — non-empty array of non-empty strings
non_claims        — non-empty array of non-empty strings
```

---

## `subjects` (deterministic order)

The `subjects` array MUST contain exactly three entries, in this order:

```
[0] acceptance-package/acceptance-package-manifest.json
    role: nested_acceptance_package_manifest
[1] review-events.jsonl
    role: review_events
[2] revocation-challenge-drill-report.json
    role: revocation_challenge_drill_report
```

Each subject is an object with:

| Field | Type | Notes |
|---|---|---|
| `path` | string | Package-local relative path; no `..`; not absolute |
| `role` | string | One of the three fixed roles above |
| `sha256` | string | `"sha256:<hex>"` of the file at `path` |
| `size_bytes` | integer | File size in bytes |

The v0.2.9 verifier:

- Rejects any `path` containing `..` or starting with `/` with
  `drill_subject_path_traversal`.
- Rejects any missing file with `drill_subject_file_missing`.
- Rejects any mismatch between recomputed SHA-256 and recorded `sha256`
  with `drill_subject_hash_mismatch`.
- Rejects manifests whose document type, schema version, hash algorithm,
  package_root, subject count, ordering, or role set diverges from this
  schema with `invalid_drill_package_manifest`.

The drill package also contains the full v0.2.8 acceptance package under
`acceptance-package/` (policy, evidence manifest, acceptance record).
Those nested files are **not** subjects of this manifest. They are
anchored transitively through subject [0] (the nested v0.2.8 package
manifest), which the v0.2.9 verifier delegates to the unchanged v0.2.8
validator via subprocess.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected only for non-emptiness.

The v0.2.9 verifier raises `scope_limitations_missing` and
`drill_non_claims_missing` respectively when violated.

---

## Non-claims about this schema

- The manifest is not signed.
- The manifest does not establish Gold conformance.
- The manifest does not certify the underlying evidence.
- The manifest does not adjudicate any challenge.
- The manifest does not revoke the v0.2.8 acceptance record.
