# Silver Acceptance Handoff Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.0
**Document type:** `proofrail.silver.acceptance_handoff_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.0`

---

## Purpose

The Silver acceptance handoff manifest is the package-level hash anchor
for the v0.3.0 Silver acceptance handoff package. It records the SHA-256
of every subject in a fixed, deterministic order, plus a non-empty
`scope_limitations` list and a non-empty `non_claims` list.

It is emitted by
`tools/silver/build_silver_acceptance_handoff_v0_1_0.py` and verified by
`tools/silver/verify_silver_acceptance_handoff_v0_1_0.py`.

A handoff manifest is **not** a certificate, approval, adjudication,
audit, or trust transfer. It is the integrity anchor over a portable
evidence package that binds the v0.2.7 composed gateway evidence
manifest, the v0.2.8 relying-party acceptance package manifest, the
v0.2.9 revocation/challenge drill package manifest, and the v0.3.0
derived handoff summary.

---

## Required top-level fields

```
document_type     — "proofrail.silver.acceptance_handoff_manifest"
schema_version    — "v0.1.0"
proofrail_release — "v0.3.0"
handoff_id        — non-empty string
generated_at      — ISO-8601 UTC, Z-suffixed
hash_algorithm    — "sha256"
package_root      — "."
subjects          — array of exactly four subjects, in deterministic order
scope_limitations — non-empty array of non-empty strings
non_claims        — non-empty array of non-empty strings
```

---

## `subjects` (deterministic order)

The `subjects` array MUST contain exactly four entries, in this order:

```
[0] composed-gateway-evidence/composed-gateway-evidence-manifest.json
    role: composed_gateway_evidence_manifest
[1] acceptance-package/acceptance-package-manifest.json
    role: relying_party_acceptance_package_manifest
[2] revocation-challenge-drill/revocation-challenge-drill-manifest.json
    role: revocation_challenge_drill_manifest
[3] silver-acceptance-handoff-summary.json
    role: silver_acceptance_handoff_summary
```

Each subject is an object with:

| Field | Type | Notes |
|---|---|---|
| `path` | string | Package-local relative path; no `..`; not absolute |
| `role` | string | One of the four fixed roles above |
| `sha256` | string | `"sha256:<hex>"` of the file at `path` |
| `size_bytes` | integer | File size in bytes |

The v0.3.0 verifier:

- Rejects any `path` containing `..` or starting with `/` with
  `handoff_subject_path_traversal`.
- Rejects any missing file with `handoff_subject_file_missing`.
- Rejects any mismatch between recomputed SHA-256 and recorded `sha256`
  with `handoff_subject_hash_mismatch`.
- Rejects manifests whose document type, schema version, proofrail
  release, hash algorithm, package_root, subject count, ordering, or
  role set diverges from this schema with `invalid_handoff_manifest`.

The handoff package also contains the full v0.2.7, v0.2.8, and v0.2.9
package roots byte-copied under `composed-gateway-evidence/`,
`acceptance-package/`, and `revocation-challenge-drill/`. Those nested
files are **not** subjects of this manifest. They are anchored
transitively through subjects [0], [1], and [2] (the three nested
package manifests), which the v0.3.0 verifier delegates to the unchanged
v0.2.7 verifier, v0.2.8 validator, and v0.2.9 verifier via subprocess.

---

## `scope_limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected only for non-emptiness.

The v0.3.0 verifier raises `handoff_limitations_missing` and
`handoff_non_claims_missing` respectively when either is empty in the
manifest or in the handoff summary.

---

## Cross-binding to other v0.3.0 artifacts

The handoff manifest does not store the chain-binding hashes; those live
in the handoff summary's `included_chain.*.manifest_sha256` and in the
nested v0.2.8 record's `evidence_package.manifest_sha256` and the nested
v0.2.9 drill report's `base_acceptance.acceptance_package_manifest_sha256`.

The v0.3.0 verifier cross-checks:

- subject [0] `sha256` against the v0.2.8 record's
  `evidence_package.manifest_sha256`;
- subject [1] `sha256` against the v0.2.9 drill report's
  `base_acceptance.acceptance_package_manifest_sha256`;
- subject [0] `sha256` against the recomputed sha256 of the inner copy
  `acceptance-package/evidence/composed-gateway-evidence-manifest.json`;
- subject [1] `sha256` against the recomputed sha256 of the inner copy
  `revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json`.

Any of those four cross-checks failing surfaces as
`handoff_chain_binding_mismatch` (verifier) or `handoff_chain_binding_failed`
(runner).

---

## Non-claims about this schema

- The manifest is not signed.
- The manifest does not establish Gold conformance.
- The manifest does not certify the underlying evidence chain.
- The manifest does not transfer reliance to a downstream party.
- The manifest does not adjudicate any challenge or revocation.
- The manifest does not approve production use.
