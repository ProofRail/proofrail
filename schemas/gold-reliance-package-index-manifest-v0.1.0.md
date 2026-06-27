# Gold Reliance Package Index Manifest Schema v0.1.0

Schema for the Gold v0.4.4 Reliance Package Index wrapping manifest.
The manifest anchors a five-subject hash-bound local package whose
subjects are, in fixed order, the v0.4.0 Gold Governed Reliance child
package manifest, the v0.4.1 Gold Decision Report Hardening child
package manifest, the v0.4.2 Gold Policy Evaluation Matrix child
package manifest, the v0.4.3 Gold Challenge Lifecycle Lite child
package manifest (under the corrected v0.4.3.1 verifier baseline),
and the v0.4.4 Gold Reliance Package Index body.

## Boundary

The manifest is a local hash anchor over five byte-stable subjects.
It is not a signature, not a certificate, not federated, not a
registry, not a federation handle, and not full Gold. v0.4.4 ships
local hash anchors only and does not transfer reliance.

The wrapping manifest itself is NOT counted as a subject. The
v0.4.4 package is a multi-file output: the wrapping manifest, the
index body file, and a `child-packages/v0.4.X/` closure for each of
the four inherited Gold releases. Closure files are runtime support
files that allow the v0.4.4 verifier to invoke each inherited
verifier on the corresponding child manifest path; they are NOT
v0.4.4 wrapping-manifest subjects.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.reliance_package_index_manifest`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.reliance_package_index.v0.4.4`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `conformance_report_id` | string | yes | Same grammar. Cross-anchored to the v0.4.0 child manifest's `report_id` and to the index body's matching entry. Member of the v0.4.4 collision class. |
| `decision_report_id` | string | yes | Same grammar. Cross-anchored to the v0.4.1 child manifest. Member of the v0.4.4 collision class. |
| `matrix_id` | string | yes | Same grammar. Cross-anchored to the v0.4.2 child manifest. Member of the v0.4.4 collision class. |
| `policy_evaluation_report_id` | string | yes | Same grammar. Cross-anchored to the v0.4.2 child manifest. Member of the v0.4.4 collision class. |
| `challenge_lifecycle_record_set_id` | string | yes | Same grammar. Cross-anchored to the v0.4.3 child manifest. Member of the v0.4.4 collision class. |
| `challenge_lifecycle_report_id` | string | yes | Same grammar. Cross-anchored to the v0.4.3 child manifest. Member of the v0.4.4 collision class. |
| `gold_reliance_package_index_id` | string | yes | Same grammar. Cross-anchored to the index body's top-level `gold_reliance_package_index_id`. Member of the v0.4.4 collision class. |
| `package_id` | string | yes | Same grammar. Cross-anchored to every child manifest's `package_id` and to the index body's `package_id`. NOT a member of the v0.4.4 collision class (it is a binding anchor). |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to every child manifest's `governed_reliance_demo_id` and to the index body's `governed_reliance_demo_id`. NOT a member of the v0.4.4 collision class (it is a binding anchor). |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `subjects` | array of exactly five objects | yes | Fixed order and roles. |

## subjects[]

Exactly five entries in fixed order. The v0.4.4 wrapping manifest
does NOT carry a self-referential manifest-hash subject. The four
inherited child manifests live under `child-packages/v0.4.X/`
subdirectories; the index body lives at the package root.

### subjects[0]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_governed_reliance_package_manifest`. |
| `path` | string | yes | Must equal `child-packages/v0.4.0/gold-governed-reliance-package-manifest.json`. Relative three-segment path with fixed leading segments `child-packages/` and `v0.4.0/`. Path traversal (`..`) and absolute paths are rejected. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.0 child wrapping-manifest bytes. No `sha256:` label prefix. |
| `size_bytes` | integer | yes | Byte length of the v0.4.0 child wrapping-manifest file. |

### subjects[1]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_decision_report_package_manifest`. |
| `path` | string | yes | Must equal `child-packages/v0.4.1/gold-decision-report-package-manifest.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.1 child wrapping-manifest bytes. |
| `size_bytes` | integer | yes | Byte length of the v0.4.1 child wrapping-manifest file. |

### subjects[2]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_policy_evaluation_matrix_package_manifest`. |
| `path` | string | yes | Must equal `child-packages/v0.4.2/gold-policy-evaluation-matrix-package-manifest.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.2 child wrapping-manifest bytes. |
| `size_bytes` | integer | yes | Byte length of the v0.4.2 child wrapping-manifest file. |

### subjects[3]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_challenge_lifecycle_package_manifest`. |
| `path` | string | yes | Must equal `child-packages/v0.4.3/gold-challenge-lifecycle-package-manifest.json`. Same path constraints. The child manifest at this path is verified under the corrected v0.4.3.1 verifier baseline. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.3 child wrapping-manifest bytes. |
| `size_bytes` | integer | yes | Byte length of the v0.4.3 child wrapping-manifest file. |

### subjects[4]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_reliance_package_index`. |
| `path` | string | yes | Must equal `gold-reliance-package-index.json`. Relative single-segment path. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.4 index body bytes (the canonical-JSON-encoded subject [4] file). |
| `size_bytes` | integer | yes | Byte length of the v0.4.4 index body file. |

## Collision Class (v0.4.4)

The following **seven** identifiers MUST be pairwise distinct:

- `conformance_report_id`
- `decision_report_id`
- `matrix_id`
- `policy_evaluation_report_id`
- `challenge_lifecycle_record_set_id`
- `challenge_lifecycle_report_id`
- `gold_reliance_package_index_id`

Explicitly excluded from the collision class (these are
cross-anchor binding identifiers, not report / lifecycle / index
artifact IDs, and MAY share a value with any field outside this
class subject to its own grammar):

- `manifest_id`
- `package_id`
- `governed_reliance_demo_id`

All pairwise collisions among the seven collision-class IDs are
surfaced at the manifest-integrity layer under
`gold_manifest_invalid` (R01). The v0.4.4-owned reasons R49..R54 are
reserved for index-body-level violations and are not used for
manifest-level pairwise-distinctness violations.

## Cross-Anchor Rules

Manifest-level cross-anchor rules (surface under
`gold_manifest_invalid`, R01):

- `package_id` must equal every child wrapping-manifest's
  `package_id` (subjects [0]..[3]) and the index body's `package_id`.
- `governed_reliance_demo_id` must equal every child wrapping-
  manifest's `governed_reliance_demo_id` (subjects [0]..[3]) and the
  index body's `governed_reliance_demo_id`.
- `conformance_report_id` must equal subject [0]'s child manifest's
  `report_id`.
- `decision_report_id` must equal subject [1]'s child manifest's
  `decision_report_id`.
- `matrix_id` must equal subject [2]'s child manifest's `matrix_id`.
- `policy_evaluation_report_id` must equal subject [2]'s child
  manifest's `policy_evaluation_report_id`.
- `challenge_lifecycle_record_set_id` must equal subject [3]'s child
  manifest's `challenge_lifecycle_record_set_id`.
- `challenge_lifecycle_report_id` must equal subject [3]'s child
  manifest's `challenge_lifecycle_report_id`.
- `gold_reliance_package_index_id` must equal the index body's
  top-level `gold_reliance_package_index_id`.
- `subjects[i].sha256` must equal the SHA-256 of the byte-copied
  file at the corresponding subdirectory path for every `i` in
  `[0..3]`, and must equal the SHA-256 of the index body file at
  the package root for `i = 4`.

Index-body-level cross-anchor rules (surface under the v0.4.4-owned
R51 `gold_reliance_package_index_binding_invalid`) are specified in
`gold-reliance-package-index-v0.1.0.md`. The manifest layer does not
double-emit a binding reason for index-body content: index-body
content checks belong to R49..R54 owned by the index-body schema.

## Path Constraints

- Subject paths [0]..[3] are relative three-segment paths whose
  fixed leading two segments are exactly `child-packages/` and
  `v0.4.X/` for the matching inherited release, with the third
  segment being the canonical child wrapping-manifest filename.
- Subject path [4] is a relative single-segment file name.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Subject count must be exactly 5.
- Subject roles and order are fixed: `gold_governed_reliance_package_manifest`,
  `gold_decision_report_package_manifest`,
  `gold_policy_evaluation_matrix_package_manifest`,
  `gold_challenge_lifecycle_package_manifest`,
  `gold_reliance_package_index`.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used. This
matches the v0.4.0..v0.4.3 convention.

## Child Package Closure Layout

For each inherited release v0.4.X (X in {0,1,2,3}), the v0.4.4
output package directory contains a subdirectory:

```
child-packages/v0.4.X/
├── gold-<inherited>-package-manifest.json     (the child wrapping manifest)
└── <every subject file the child wrapping manifest references>
```

The closure files (every subject file referenced by the child
wrapping manifest) live alongside the child wrapping manifest in
the same `child-packages/v0.4.X/` directory so that the inherited
v0.4.X verifier, when invoked by the v0.4.4 verifier on the child
wrapping-manifest path, can resolve its referenced subject files
relative to the child manifest's directory using the inherited
verifier's existing path-resolution rules.

Closure files are NOT enumerated as v0.4.4 wrapping-manifest
subjects and have no v0.4.4-owned reason coverage of their own:
their integrity is enforced by the inherited verifier's own
existing reasons (R02..R48) via subprocess relay.

## Verifier Reachability

The v0.4.4 verifier validates the wrapping manifest before any
subject body. Path-traversal is checked before exact path equality.
The v0.4.4 verifier validates the index body (subject [4]) under
R49..R54 before invoking inherited verifiers on subjects [0]..[3],
because R49..R54 are owned by v0.4.4 and must be reachable without
contaminating any inherited verifier subprocess.

Inherited verifier invocation order:

1. v0.4.0 verifier on `child-packages/v0.4.0/<child manifest>`.
2. v0.4.1 verifier on `child-packages/v0.4.1/<child manifest>`.
3. v0.4.2 verifier on `child-packages/v0.4.2/<child manifest>`.
4. v0.4.3 verifier on `child-packages/v0.4.3/<child manifest>` under
   the corrected v0.4.3.1 baseline.

Each inherited verifier resolves its referenced subject files
relative to the child manifest's directory. Any inherited verifier
reason (R02..R48) is relayed verbatim by the v0.4.4 verifier with
no rewriting, no narrowing, and no sixth runner-only refusal. The
v0.4.4 verifier does NOT re-run any inherited builder; it verifies
the supplied closure via the inherited verifier.

If any inherited verifier is missing or crashes with a non-FAIL
non-zero exit, the v0.4.4 verifier emits a non-reason-shaped
`INFRA:` diagnostic on stderr, exits with code 3 (distinct from
verifier-reason exit 1), and MUST NOT emit any public reason-shaped
token.

## Non-Claims

The manifest is not signed, not a certificate, not federated, not a
registry, not a federation handle, and not production PKI. It is a
local hash anchor for the v0.4.4 Gold Reliance Package Index. It
does not transfer reliance, does not authorize external acceptance,
is not Gold certification, does not redefine R01..R48, does not
introduce a sixth runner-only refusal, and does not re-derive
inherited child manifests via any builder during verification.
