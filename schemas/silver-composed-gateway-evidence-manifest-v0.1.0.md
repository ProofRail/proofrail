# Silver Composed Gateway Evidence Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.2.7
**Document type:** `proofrail.silver.composed_gateway_evidence_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.2.7`

---

## Purpose

The composed gateway evidence manifest is the package-level hash anchor for
the v0.2.7 demo. It records the SHA-256 of every package subject in a fixed,
deterministic order, plus a `composition` block describing how the package
was assembled.

The manifest is emitted by
`tools/silver/compose_gateway_evidence_demo_v0_1_0.py` and verified by
`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`.

---

## Required top-level fields

```
document_type        — "proofrail.silver.composed_gateway_evidence_manifest"
schema_version       — "v0.1.0"
proofrail_release    — "v0.2.7"
demo_id              — "proofrail-silver-demo-004-composed-gateway-evidence"
generated_at         — ISO-8601 timestamp (UTC, Z-suffixed)
hash_algorithm       — "sha256"
package_root         — "."
subjects             — array of exactly five subjects, in deterministic order
composition          — object (see §composition)
limitations          — array of non-empty strings
non_claims           — array of non-empty strings
```

---

## `subjects` (deterministic order)

The `subjects` array MUST contain exactly five entries, in this order:

```
[0] README.md                                      role: demo_readme
[1] demo-walkthrough.md                            role: demo_walkthrough
[2] adapter/gateway-mcp-simulated-v0.2.6.json      role: adapter_descriptor
[3] source/gateway-events.jsonl                    role: source_events
[4] composed-gateway-evidence-report.json          role: composed_report
```

Each subject is an object with:

| Field | Type | Notes |
|---|---|---|
| `path` | string | Package-local relative path; no `..`; not absolute |
| `role` | string | One of the five fixed roles above |
| `sha256` | string | `"sha256:<hex>"` of the file at `path` |
| `size_bytes` | integer | File size in bytes |

The verifier:

- Rejects any `path` containing `..` or starting with `/` with
  `composed_subject_path_traversal`.
- Rejects any missing file with `composed_subject_file_missing`.
- Rejects any mismatch between recomputed SHA-256 and recorded `sha256`
  with `composed_subject_hash_mismatch`.
- Rejects manifests whose subject count, ordering, or role set diverges
  from the deterministic order above with `invalid_composed_gateway_manifest`.

---

## `composition`

The `composition` block MUST be present with these fields:

```
source_type                   — "gateway"
adapter_descriptor_path       — "adapter/gateway-mcp-simulated-v0.2.6.json"
source_events_path            — "source/gateway-events.jsonl"
composed_report_path          — "composed-gateway-evidence-report.json"
source_is_trust_authority     — false
```

Verifier rules:

- `source_type` must equal `"gateway"`. Otherwise → `invalid_composed_gateway_manifest`.
- `source_is_trust_authority` must equal `false`. Otherwise →
  `invalid_composed_gateway_manifest`.
- Each path field must be a package-local relative path with no `..` and
  must not be absolute. Otherwise → `composed_subject_path_traversal`.
- Each path field must match the corresponding `subjects[i].path` exactly.
  Otherwise → `invalid_composed_gateway_manifest`.

The `composition` block exists so that the manifest carries enough metadata
to describe the composition without a relying party having to open the
report or adapter.

---

## `limitations` and `non_claims`

Both arrays MUST be present and non-empty. Each entry MUST be a non-empty
string. Entries are inspected only for non-emptiness.

---

## Non-claims about this schema

- The manifest is not signed.
- The manifest does not establish a Silver Signed Bundle Assertion.
- The manifest does not assert relying-party acceptance.
- The manifest does not certify any real gateway product.
