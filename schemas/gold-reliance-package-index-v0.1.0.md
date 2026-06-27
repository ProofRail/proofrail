# Gold Reliance Package Index Body Schema v0.1.0

Schema for the body file referenced as subject [4] of the v0.4.4
Gold Reliance Package Index wrapping manifest. The index body is
the only v0.4.4-authored payload in the v0.4.4 package; subjects
[0]..[3] are byte-copies of the four inherited Gold child wrapping
manifests.

## Boundary

The index body is a local, derived index over the inherited
v0.4.0..v0.4.3 Gold child wrapping manifests. It is not a
signature, not a certificate, not federated, not a registry, not a
federation handle, and not full Gold. It does not transfer
reliance.

The index body contains exactly four child entries (one per
inherited release), a coverage summary, top-level cross-anchor
binding identifiers, and a single canonical-JSON SHA-256 fingerprint
over its own canonical-JSON content (with the fingerprint field
excluded).

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.reliance_package_index`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.reliance_package_index.v0.4.4`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `gold_reliance_package_index_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Cross-anchored to the wrapping manifest's `gold_reliance_package_index_id`. Member of the v0.4.4 collision class. |
| `package_id` | string | yes | Same grammar. Cross-anchored to every child wrapping manifest's `package_id` and to the wrapping manifest's `package_id`. NOT a member of the v0.4.4 collision class (binding anchor). |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to every child wrapping manifest's `governed_reliance_demo_id` and to the wrapping manifest's `governed_reliance_demo_id`. NOT a member of the v0.4.4 collision class (binding anchor). |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `entries` | array of exactly four objects | yes | Fixed order and roles; one entry per inherited release. |
| `coverage_summary` | object | yes | See `coverage_summary` section. |
| `index_fingerprint` | string | yes | Bare lowercase hex SHA-256 (64 chars, `[0-9a-f]{64}`) of the canonical-JSON byte-encoding of this body object with the `index_fingerprint` field itself excluded. Canonical JSON is `json.dumps(obj, sort_keys=True, separators=(",",":")).encode("utf-8")`. |

## entries[]

Exactly four entries in fixed order. Each entry pins one inherited
Gold release into the index. The wrapping manifest's
`subjects[0]..subjects[3]` cross-anchor by `child_subject_index`
into this array.

### entries[0]
| Field | Type | Required | Notes |
|---|---|---|---|
| `release_label` | string | yes | Must be `gold.governed_reliance.v0.4.0`. |
| `child_subject_index` | integer | yes | Must be `0`. Refers to `subjects[0]` of the wrapping manifest. |
| `child_package_root` | string | yes | Must equal `child-packages/v0.4.0/`. Relative directory path with trailing slash. Path traversal (`..`) and absolute paths are rejected. |
| `child_manifest_path` | string | yes | Must equal `child-packages/v0.4.0/gold-governed-reliance-package-manifest.json`. |
| `child_manifest_fingerprint` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.0 child wrapping-manifest file. Must byte-match `subjects[0].sha256` of the wrapping manifest. |
| `child_manifest_size_bytes` | integer | yes | Must byte-match `subjects[0].size_bytes` of the wrapping manifest. |

### entries[1]
| Field | Type | Required | Notes |
|---|---|---|---|
| `release_label` | string | yes | Must be `gold.decision_report_hardening.v0.4.1`. |
| `child_subject_index` | integer | yes | Must be `1`. |
| `child_package_root` | string | yes | Must equal `child-packages/v0.4.1/`. Same path constraints. |
| `child_manifest_path` | string | yes | Must equal `child-packages/v0.4.1/gold-decision-report-package-manifest.json`. |
| `child_manifest_fingerprint` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.1 child wrapping-manifest file. Must byte-match `subjects[1].sha256`. |
| `child_manifest_size_bytes` | integer | yes | Must byte-match `subjects[1].size_bytes`. |

### entries[2]
| Field | Type | Required | Notes |
|---|---|---|---|
| `release_label` | string | yes | Must be `gold.policy_evaluation_matrix.v0.4.2`. |
| `child_subject_index` | integer | yes | Must be `2`. |
| `child_package_root` | string | yes | Must equal `child-packages/v0.4.2/`. Same path constraints. |
| `child_manifest_path` | string | yes | Must equal `child-packages/v0.4.2/gold-policy-evaluation-matrix-package-manifest.json`. |
| `child_manifest_fingerprint` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.2 child wrapping-manifest file. Must byte-match `subjects[2].sha256`. |
| `child_manifest_size_bytes` | integer | yes | Must byte-match `subjects[2].size_bytes`. |

### entries[3]
| Field | Type | Required | Notes |
|---|---|---|---|
| `release_label` | string | yes | Must be `gold.challenge_lifecycle_lite.v0.4.3`. |
| `child_subject_index` | integer | yes | Must be `3`. |
| `child_package_root` | string | yes | Must equal `child-packages/v0.4.3/`. Same path constraints. |
| `child_manifest_path` | string | yes | Must equal `child-packages/v0.4.3/gold-challenge-lifecycle-package-manifest.json`. |
| `child_manifest_fingerprint` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.3 child wrapping-manifest file. Must byte-match `subjects[3].sha256`. The v0.4.3 child manifest is generated and verified under the corrected v0.4.3.1 baseline. |
| `child_manifest_size_bytes` | integer | yes | Must byte-match `subjects[3].size_bytes`. |

## coverage_summary

The `coverage_summary` block is a closed, fixed-key object. Stray
keys are rejected.

| Field | Type | Required | Notes |
|---|---|---|---|
| `child_package_count` | integer | yes | Must equal `4`. |
| `inherited_release_count` | integer | yes | Must equal `4`. The number of inherited Gold releases indexed by this body. |
| `pairwise_distinct_id_count` | integer | yes | Must equal `7`. The size of the v0.4.4 pairwise-distinct collision class. The seven members are exactly: `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `gold_reliance_package_index_id`. `package_id` and `governed_reliance_demo_id` are binding anchors and are NOT counted here. |
| `package_id_anchor_consistency` | boolean | yes | Must be `true`. Asserts that the recorded `package_id` byte-matches every inherited child wrapping manifest's `package_id`. The verifier independently recomputes and confirms; a mismatch surfaces under R51. |
| `governed_reliance_demo_id_anchor_consistency` | boolean | yes | Must be `true`. Same discipline for `governed_reliance_demo_id`. |

## Collision Class Membership

The body asserts membership in the v0.4.4 collision class for
`gold_reliance_package_index_id`. The other six collision-class IDs
(`conformance_report_id`, `decision_report_id`, `matrix_id`,
`policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`,
`challenge_lifecycle_report_id`) are NOT carried directly on the
body's top-level; the verifier reads them from the wrapping manifest
and from the corresponding child wrapping manifests for binding
checks. All pairwise collisions among the seven collision-class IDs
are surfaced under R01 `gold_manifest_invalid` at the manifest
layer, not under R49..R54.

## Cross-Anchor Rules

Index-body-level cross-anchor rules (surface under R51
`gold_reliance_package_index_binding_invalid` unless otherwise
specified):

- The body's `package_id` must equal the wrapping manifest's
  `package_id` and every child wrapping manifest's `package_id`.
- The body's `governed_reliance_demo_id` must equal the wrapping
  manifest's `governed_reliance_demo_id` and every child wrapping
  manifest's `governed_reliance_demo_id`.
- The body's `gold_reliance_package_index_id` must equal the wrapping
  manifest's `gold_reliance_package_index_id`.
- For each `i` in `[0..3]`, `entries[i].child_manifest_fingerprint`
  must byte-match the wrapping manifest's `subjects[i].sha256`, and
  `entries[i].child_manifest_size_bytes` must byte-match the wrapping
  manifest's `subjects[i].size_bytes`.
- For each `i` in `[0..3]`, `entries[i].child_manifest_path` must
  byte-match the wrapping manifest's `subjects[i].path`.

Entry-level shape, order, count, and per-entry field violations
surface under R52 `gold_reliance_package_index_entry_invalid`.
Coverage-summary shape and arithmetic violations surface under R53
`gold_reliance_package_index_summary_invalid`. A recomputed
`index_fingerprint` that does not byte-match the body's embedded
`index_fingerprint` surfaces under R54
`gold_reliance_package_index_fingerprint_invalid`. A body that is
not a JSON object surfaces under R49
`gold_reliance_package_index_not_object`. A body whose top-level
schema-shape (required fields, types, allowed value sets) is
violated surfaces under R50
`gold_reliance_package_index_schema_invalid`.

## Fingerprint Rule

`index_fingerprint` is computed exactly as:

```
canonical = json.dumps(body_obj_without_index_fingerprint,
                       sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
index_fingerprint = hashlib.sha256(canonical).hexdigest()
```

where `body_obj_without_index_fingerprint` is the body object with
the `index_fingerprint` key removed. The output is bare lowercase
hexadecimal (64 chars, `[0-9a-f]{64}`). No `sha256:` label prefix.

## Path Constraints

- `child_package_root` is a relative two-segment directory path with
  a trailing slash, exactly `child-packages/v0.4.X/` for the matching
  inherited release.
- `child_manifest_path` is a relative three-segment file path,
  exactly the concatenation of `child_package_root` (which itself
  contributes two leading segments `child-packages/v0.4.X/`) and the
  canonical child wrapping-manifest filename as the third segment.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Entry count is exactly 4.
- Entry order is fixed: v0.4.0, v0.4.1, v0.4.2, v0.4.3.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used. This
matches the v0.4.0..v0.4.3 convention.

## Stray-Key Discipline

Top-level body fields, per-entry fields, and `coverage_summary`
fields are closed. Any stray key at any of these layers surfaces
under R50 `gold_reliance_package_index_schema_invalid`. Closed
discipline is what makes the empty TG closed-allowlist target
feasible: no v0.4.4-named data field is a substring of any v0.4.4
reason name in R49..R54.

## Non-Claims

The index body is not signed, not a certificate, not federated, not
a registry, not a federation handle, and not production PKI. It is
a local index over the inherited v0.4.0..v0.4.3 Gold child wrapping
manifests. It does not transfer reliance, does not authorize
external acceptance, and is not Gold certification. It does NOT
re-derive or summarize inherited subject bodies: per-entry
`child_manifest_fingerprint` references the inherited child wrapping
manifest only.
