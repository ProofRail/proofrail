# Gold Policy Evaluation Matrix Package Manifest Schema v0.1.0

Schema for the Gold v0.4.2 Policy Evaluation Matrix package manifest.
The manifest anchors a five-subject hash-bound local package: the
v0.4.0-shaped governed reliance package body, the v0.4.0-shaped
conformance report, the v0.4.1 governed reliance decision report,
the v0.4.2 policy evaluation matrix, and the v0.4.2 policy
evaluation report.

## Boundary

The manifest is a local hash anchor over five byte-stable subjects.
It is not a signature, not a certificate, not federated, and not
full Gold. v0.4.2 ships local hash anchors only.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.policy_evaluation_matrix_package_manifest`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.policy_evaluation_matrix.v0.4.2`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `conformance_report_id` | string | yes | Same grammar. Anchors subject [1] (the inherited v0.4.0 conformance report). Cross-anchored to the conformance report's top-level `report_id`. |
| `decision_report_id` | string | yes | Same grammar. Anchors subject [2] (the v0.4.1 decision report). Cross-anchored to the decision report's top-level `decision_report_id`. MUST NOT equal `conformance_report_id`. |
| `matrix_id` | string | yes | Same grammar. Anchors subject [3] (the v0.4.2 policy evaluation matrix). Cross-anchored to the matrix's top-level `matrix_id`. MUST NOT equal `conformance_report_id`, `decision_report_id`, or `policy_evaluation_report_id`. |
| `policy_evaluation_report_id` | string | yes | Same grammar. Anchors subject [4] (the v0.4.2 policy evaluation report). Cross-anchored to the report's top-level `policy_evaluation_report_id`. MUST NOT equal `conformance_report_id`, `decision_report_id`, or `matrix_id`. |
| `package_id` | string | yes | Same grammar. Cross-anchored to the package body, decision report, matrix, and evaluation report. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to the package body, decision report, matrix, and evaluation report. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `subjects` | array of exactly five objects | yes | Fixed order and roles. |

## subjects[]

Exactly five entries in fixed order. The v0.4.2 manifest deliberately
does NOT carry a self-referential manifest-hash subject.

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
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.0 conformance report bytes. No label prefix. |
| `size_bytes` | integer | yes | Byte length of the derived conformance report. |

### subjects[2]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `decision_report`. |
| `path` | string | yes | Must equal `gold-governed-reliance-decision-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.1 decision report bytes. No label prefix. |
| `size_bytes` | integer | yes | Byte length of the derived decision report. |

### subjects[3]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `policy_evaluation_matrix`. |
| `path` | string | yes | Must equal `gold-policy-evaluation-matrix.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.2 policy evaluation matrix bytes. No label prefix. |
| `size_bytes` | integer | yes | Byte length of the matrix. |

### subjects[4]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `policy_evaluation_report`. |
| `path` | string | yes | Must equal `gold-policy-evaluation-report.json`. Same path constraints. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the derived v0.4.2 policy evaluation report bytes. No label prefix. |
| `size_bytes` | integer | yes | Byte length of the derived policy evaluation report. |

## Cross-Anchor Rules

- `package_id` must equal the package body's `package_id`, the
  decision report's `package_id`, the matrix's `package_id`, and
  the policy evaluation report's `package_id`.
- `governed_reliance_demo_id` must equal the package body's
  `governed_reliance_demo_id`, the decision report's
  `governed_reliance_demo_id`, the matrix's
  `governed_reliance_demo_id`, and the policy evaluation report's
  `governed_reliance_demo_id`.
- `conformance_report_id` must equal the inherited conformance
  report's top-level `report_id`.
- `decision_report_id` must equal the decision report's top-level
  `decision_report_id`.
- `matrix_id` must equal the matrix's top-level `matrix_id` and the
  policy evaluation report's top-level `matrix_id`.
- `policy_evaluation_report_id` must equal the policy evaluation
  report's top-level `policy_evaluation_report_id`.
- The four identifiers `conformance_report_id`, `decision_report_id`,
  `matrix_id`, and `policy_evaluation_report_id` MUST be pairwise
  distinct.
- The decision report's `source_package_sha256` must equal
  `subjects[0].sha256`.
- The matrix's `decision_report_sha256` must equal
  `subjects[2].sha256`.
- The policy evaluation report's `source_decision_report_sha256`
  must equal `subjects[2].sha256`.
- The policy evaluation report's `source_matrix_sha256` must equal
  `subjects[3].sha256`.

A failure of any of these cross-anchor rules surfaces as
`gold_manifest_invalid` (cross-anchor folding rule; not a new public
reason).

## Path Constraints

- Subject paths are single-segment file names.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Subject count must be exactly 5.
- Subject roles and order are fixed: `governed_reliance_package`,
  `conformance_report`, `decision_report`, `policy_evaluation_matrix`,
  `policy_evaluation_report`.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used by v0.4.2
runner output, manifest fields, or any v0.4.2 report's
`source_*_sha256` field.

## Verifier Reachability

The v0.4.2 verifier validates the manifest before any subject body.
Path-traversal is checked before exact path equality. The inherited
v0.4.1 24+5 ordered checks against the package body, conformance
report, and decision report are delegated by subprocess to the
co-located v0.4.1 verifier (see `tools/gold/README.md`). The
v0.4.2-introduced ordered checks (`check_30` through `check_38`) run
AFTER the inherited 29 checks have passed against the body,
conformance report, and decision report. Path-traversal of the
matrix or policy-evaluation-report subjects is surfaced as
`gold_manifest_invalid`, not as a matrix or evaluation reason.

If the co-located v0.4.1 verifier is missing or crashes with a
non-FAIL non-zero exit, the v0.4.2 verifier emits a non-reason-shaped
`INFRA:` diagnostic on stderr, exits with a distinct non-1 code, and
MUST NOT emit any public reason-shaped token.

## Non-Claims

The manifest is not signed, not a certificate, not federated, and
not production PKI. It is a local hash anchor for the v0.4.2 Policy
Evaluation Matrix package. It does not transfer reliance, does not
authorize external acceptance, and is not Gold certification.
