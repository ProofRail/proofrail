# Gold Challenge Lifecycle Lite Package Manifest Schema v0.1.0

Schema for the Gold v0.4.3 Challenge Lifecycle Lite package manifest.
The manifest anchors a seven-subject hash-bound local package: the
v0.4.0-shaped governed reliance package body, the v0.4.0-shaped
conformance report, the v0.4.1 governed reliance decision report, the
v0.4.2 policy evaluation matrix, the v0.4.2 policy evaluation report,
the v0.4.3 challenge lifecycle records body, and the v0.4.3 challenge
lifecycle report.

## Boundary

The manifest is a local hash anchor over seven byte-stable subjects.
It is not a signature, not a certificate, not federated, and not
full Gold. v0.4.3 ships local hash anchors only.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.challenge_lifecycle_package_manifest`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.challenge_lifecycle_lite.v0.4.3`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `conformance_report_id` | string | yes | Same grammar. Anchors subject [1] (the inherited v0.4.0 conformance report). Cross-anchored to the conformance report's top-level `report_id`. Member of the v0.4.3 collision class. |
| `decision_report_id` | string | yes | Same grammar. Anchors subject [2] (the v0.4.1 decision report). Cross-anchored to the decision report's top-level `decision_report_id`. Member of the v0.4.3 collision class. |
| `matrix_id` | string | yes | Same grammar. Anchors subject [3] (the v0.4.2 policy evaluation matrix). Cross-anchored to the matrix's top-level `matrix_id`. Member of the v0.4.3 collision class. |
| `policy_evaluation_report_id` | string | yes | Same grammar. Anchors subject [4] (the v0.4.2 policy evaluation report). Cross-anchored to the report's top-level `policy_evaluation_report_id`. Member of the v0.4.3 collision class. |
| `challenge_lifecycle_record_set_id` | string | yes | Same grammar. Anchors subject [5] (the v0.4.3 records body). Cross-anchored to the records body's top-level `lifecycle_record_set_id` and the lifecycle report's `lifecycle_record_set_id`. Member of the v0.4.3 collision class. |
| `challenge_lifecycle_report_id` | string | yes | Same grammar. Anchors subject [6] (the v0.4.3 lifecycle report). Cross-anchored to the lifecycle report's top-level `challenge_lifecycle_report_id`. Member of the v0.4.3 collision class. |
| `package_id` | string | yes | Same grammar. Cross-anchored to the package body, decision report, matrix, evaluation report, records body, and lifecycle report. Not a member of the v0.4.3 collision class. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to the same six bodies. Not a member of the v0.4.3 collision class. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `subjects` | array of exactly seven objects | yes | Fixed order and roles. |

## subjects[]

Exactly seven entries in fixed order. The v0.4.3 manifest does NOT
carry a self-referential manifest-hash subject.

### subjects[0]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `governed_reliance_package`. |
| `path` | string | yes | Must equal `governed-reliance-scenarios.json`. Relative single-segment path. Path traversal (`..`) and absolute paths are rejected by the verifier. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.0-shaped package body. No `sha256:` label prefix. |
| `size_bytes` | integer | yes | Byte length of the package body. |

### subjects[1]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `conformance_report`. |
| `path` | string | yes | Must equal `silver-gold-governed-reliance-conformance-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.0 conformance report bytes. |
| `size_bytes` | integer | yes | Byte length of the derived conformance report. |

### subjects[2]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `decision_report`. |
| `path` | string | yes | Must equal `gold-governed-reliance-decision-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.1 decision report bytes. |
| `size_bytes` | integer | yes | Byte length of the derived decision report. |

### subjects[3]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `policy_evaluation_matrix`. |
| `path` | string | yes | Must equal `gold-policy-evaluation-matrix.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.2 policy evaluation matrix bytes. |
| `size_bytes` | integer | yes | Byte length of the matrix. |

### subjects[4]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `policy_evaluation_report`. |
| `path` | string | yes | Must equal `gold-policy-evaluation-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.2 policy evaluation report bytes. |
| `size_bytes` | integer | yes | Byte length of the derived policy evaluation report. |

### subjects[5]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `challenge_lifecycle_records`. |
| `path` | string | yes | Must equal `challenge-lifecycle-records.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the runtime v0.4.3 records body bytes (after the runner injects `policy_evaluation_report_sha256` and `generated_at`). |
| `size_bytes` | integer | yes | Byte length of the runtime records body. |

### subjects[6]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `challenge_lifecycle_report`. |
| `path` | string | yes | Must equal `gold-challenge-lifecycle-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.3 lifecycle report bytes. |
| `size_bytes` | integer | yes | Byte length of the derived lifecycle report. |

## Collision Class (v0.4.3)

The following **six** identifiers MUST be pairwise distinct:

- `conformance_report_id`
- `decision_report_id`
- `matrix_id`
- `policy_evaluation_report_id`
- `challenge_lifecycle_record_set_id`
- `challenge_lifecycle_report_id`

Explicitly excluded from the collision class (these are
cross-anchor identifiers, not report/lifecycle artifact IDs, and
MAY share a value with any field outside this class subject to its
own grammar):

- `manifest_id`
- `package_id`
- `governed_reliance_demo_id`

All pairwise collisions among the six collision-class IDs are
surfaced at the manifest-integrity layer under
`gold_manifest_invalid` (R01). The v0.4.3-owned
`*_records_binding_invalid` (R41) and `*_report_binding_invalid`
(R46) reasons are reserved for body-level cross-anchor mismatches
(e.g., records-body or lifecycle-report fields not matching the
manifest's IDs or SHA-256 anchors); they are not used for
manifest-level pairwise-distinctness violations. The conformance,
decision, and policy-evaluation report IDs share the same routing
discipline: pairwise collisions among them under the v0.4.3
collision class surface under `gold_manifest_invalid` rather than
under the per-tier body-binding reasons.

## Cross-Anchor Rules

- `package_id` must equal the package body's `package_id`, the
  decision report's `package_id`, the matrix's `package_id`, the
  policy evaluation report's `package_id`, the records body's
  `package_id`, and the lifecycle report's `package_id`.
- `governed_reliance_demo_id` must equal the same six documents'
  `governed_reliance_demo_id`.
- `conformance_report_id` must equal the inherited conformance
  report's top-level `report_id`.
- `decision_report_id` must equal the decision report's top-level
  `decision_report_id`.
- `matrix_id` must equal the matrix's top-level `matrix_id` and the
  policy evaluation report's top-level `matrix_id`.
- `policy_evaluation_report_id` must equal the policy evaluation
  report's top-level `policy_evaluation_report_id`, the records
  body's `policy_evaluation_report_ref`, and the lifecycle report's
  `policy_evaluation_report_id`.
- `challenge_lifecycle_record_set_id` must equal the records body's
  `lifecycle_record_set_id` and the lifecycle report's
  `lifecycle_record_set_id`.
- `challenge_lifecycle_report_id` must equal the lifecycle report's
  top-level `challenge_lifecycle_report_id`.
- The decision report's `source_package_sha256` must equal
  `subjects[0].sha256`.
- The matrix's `decision_report_sha256` must equal
  `subjects[2].sha256`.
- The policy evaluation report's `source_decision_report_sha256`
  must equal `subjects[2].sha256`.
- The policy evaluation report's `source_matrix_sha256` must equal
  `subjects[3].sha256`.
- The records body's runtime `policy_evaluation_report_sha256` must
  equal `subjects[4].sha256`.
- The lifecycle report's `source_records_sha256` must equal
  `subjects[5].sha256`.
- The lifecycle report's `source_policy_evaluation_report_sha256`
  must equal `subjects[4].sha256`.
- The lifecycle report's `source_decision_report_sha256` must equal
  `subjects[2].sha256`.

Cross-anchor rules are partitioned by the reason layer that owns
them. Manifest-level rules (subjects[0].sha256 ↔ decision report's
`source_package_sha256`; subjects[2].sha256 ↔ matrix's
`decision_report_sha256`; manifest-level ID grammar and pairwise
distinctness; manifest-level cross-anchor of `package_id` and
`governed_reliance_demo_id`) surface under `gold_manifest_invalid`.
Body-level cross-anchor rules surface under the per-tier
body-binding reason that owns the affected document: the v0.4.2
policy-evaluation-report's `source_decision_report_sha256` and
`source_matrix_sha256` are inherited v0.4.2 surface; the v0.4.3
records-body's runtime `policy_evaluation_report_sha256` mismatch
surfaces under `gold_challenge_lifecycle_records_binding_invalid`
(R41); the v0.4.3 lifecycle-report's `source_records_sha256`,
`source_policy_evaluation_report_sha256`, and
`source_decision_report_sha256` mismatches surface under
`gold_challenge_lifecycle_report_binding_invalid` (R46). No new
public reason is introduced by v0.4.3 solely for cross-anchor
folding; existing per-tier reasons own their layer.

## Path Constraints

- Subject paths are single-segment file names.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Subject count must be exactly 7.
- Subject roles and order are fixed: `governed_reliance_package`,
  `conformance_report`, `decision_report`, `policy_evaluation_matrix`,
  `policy_evaluation_report`, `challenge_lifecycle_records`,
  `challenge_lifecycle_report`.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used by v0.4.3
runner output, manifest fields, or any v0.4.3 body's `source_*_sha256`
field. The records body's runtime `policy_evaluation_report_sha256`
follows the same convention.

## Verifier Reachability

The v0.4.3 verifier validates the manifest before any subject body.
Path-traversal is checked before exact path equality. The inherited
v0.4.2 30+9 ordered checks (with v0.4.2 itself subprocess-delegating
to v0.4.1) are delegated by subprocess to the co-located v0.4.2
verifier. The v0.4.3-introduced ordered checks run AFTER the
inherited checks have passed against the body, conformance report,
decision report, matrix, and policy evaluation report. Path-traversal
of the records or lifecycle-report subjects is surfaced as
`gold_manifest_invalid`, not as a records or lifecycle-report reason.

If the co-located v0.4.2 verifier is missing or crashes with a
non-FAIL non-zero exit, the v0.4.3 verifier emits a non-reason-shaped
`INFRA:` diagnostic on stderr, exits with code 3 (distinct from
verifier-reason exit 1), and MUST NOT emit any public reason-shaped
token.

## Non-Claims

The manifest is not signed, not a certificate, not federated, and
not production PKI. It is a local hash anchor for the v0.4.3
Challenge Lifecycle Lite package. It does not transfer reliance,
does not authorize external acceptance, and is not Gold
certification.
