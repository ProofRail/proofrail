# Gold Decision Report Package Manifest Schema v0.1.0

Schema for the Gold v0.4.1 Decision Report Hardening package
manifest. The manifest anchors a three-subject hash-bound local
package: the v0.4.0-shaped governed reliance package body, the
v0.4.0-shaped conformance report, and the v0.4.1 governed reliance
decision report.

## Boundary

The manifest is a local hash anchor over three byte-stable subjects.
It is not a signature, not a certificate, not federated, and not full
Gold. v0.4.1 ships local hash anchors only.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.decision_report_package_manifest`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.decision_report_hardening.v0.4.1`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `conformance_report_id` | string | yes | Same grammar. Anchors subject [1] (the inherited v0.4.0 conformance report). Cross-anchored to the conformance report's top-level `report_id`. The v0.4.1 manifest deliberately does NOT carry a generic `report_id`. |
| `decision_report_id` | string | yes | Same grammar. Anchors subject [2] (the v0.4.1 decision report). Cross-anchored to the decision report's top-level `decision_report_id`. MUST NOT equal `conformance_report_id`. |
| `package_id` | string | yes | Same grammar. Cross-anchored to the package body and to the decision report. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to the package body and to the decision report. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `subjects` | array of exactly three objects | yes | Fixed order and roles. |

## subjects[]

Exactly three entries in fixed order:

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

## Cross-Anchor Rules

- `package_id` must equal the package body's `package_id` and the
  decision report's `package_id`.
- `governed_reliance_demo_id` must equal the package body's
  `governed_reliance_demo_id` and the decision report's
  `governed_reliance_demo_id`.
- `conformance_report_id` must equal the inherited conformance
  report's top-level `report_id`.
- `decision_report_id` must equal the decision report's top-level
  `decision_report_id`.
- `decision_report_id` MUST NOT equal `conformance_report_id`.
- The decision report's `source_package_sha256` must equal
  `subjects[0].sha256` (byte-identical bare lowercase hex digest of
  the package body).

A failure of any of these cross-anchor rules surfaces as
`gold_manifest_invalid` (cross-anchor folding rule; not a 30th
reason).

## Path Constraints

- Subjects paths are single-segment file names.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Subject count must be exactly 3.
- Subject roles and order are fixed: `governed_reliance_package`,
  `conformance_report`, `decision_report`.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used by v0.4.1
runner output, manifest fields, or the decision report's
`source_package_sha256` field. v0.4.0 manifest behaviour
(label-tolerant) is preserved untouched in v0.4.0 code; v0.4.1
emits bare hex throughout.

## Verifier Reachability

The v0.4.1 verifier validates the manifest before parsing the
package body. Path-traversal is checked before exact path equality.
The five v0.4.1-introduced decision-report checks
(`gold_decision_report_not_object`, `gold_decision_report_schema_invalid`,
`gold_decision_report_binding_invalid`,
`gold_decision_report_projection_invalid`,
`gold_decision_report_summary_invalid`) run AFTER the inherited
v0.4.0 24 ordered checks against the package body have passed. The
post-structural conformance-report byte-compare re-derivation, if it
disagrees, surfaces as `gold_manifest_invalid` (consistent with
v0.4.0).

## Non-Claims

The manifest is not signed, not a certificate, not federated, and
not production PKI. It is a local hash anchor for the v0.4.1
Decision Report Hardening package. It does not transfer reliance,
does not authorize external acceptance, and is not Gold
certification.
