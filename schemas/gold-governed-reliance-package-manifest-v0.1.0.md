# Gold Governed Reliance Package Manifest Schema v0.1.0

Schema for the Gold v0.4.0 Minimal Gold Governed Reliance Demo
package manifest. The manifest anchors a two-subject hash-bound local
package.

## Boundary

The manifest is a local hash anchor over two byte-stable subjects. It
is not a signature, not a certificate, not federated, and not full
Gold.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.governed_reliance_package_manifest`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `proofrail_release` | string | yes | Must be `gold.governed_reliance.v0.4.0`. |
| `hash_algorithm` | string | yes | Must be `sha256`. |
| `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `report_id` | string | yes | Same grammar. |
| `package_id` | string | yes | Same grammar. Cross-anchored to package body. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to package body. |
| `generated_at` | string | yes | ISO-8601 UTC. |
| `subjects` | array of exactly two objects | yes | Fixed order and roles. |

## subjects[]

Exactly two entries in fixed order:

### subjects[0]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `governed_reliance_package`. |
| `path` | string | yes | Must equal `governed-reliance-scenarios.json`. Must be a relative single-segment path. Path traversal (`..`) and absolute paths are rejected by the verifier. |
| `sha256` | string | yes | Lowercase hex SHA-256 of the byte-copied package body. |
| `size_bytes` | integer | yes | Byte length of the package body. |

### subjects[1]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `conformance_report`. |
| `path` | string | yes | Must equal `silver-gold-governed-reliance-conformance-report.json`. Same path constraints. |
| `sha256` | string | yes | Lowercase hex SHA-256 of the derived conformance report bytes. |
| `size_bytes` | integer | yes | Byte length of the derived conformance report. |

## Cross-Anchor Rules

- `package_id` must equal the package body's `package_id`.
- `governed_reliance_demo_id` must equal the package body's
  `governed_reliance_demo_id`.

## Path Constraints

- Subjects paths are single-segment file names.
- Absolute paths are rejected.
- Paths containing `..` are rejected.
- Subject count must be exactly 2.
- Subject roles and order are fixed.

## Verifier Reachability

The verifier validates the manifest before parsing the package body.
Path-traversal is checked before exact path equality. The
post-structural conformance-report byte-compare re-derivation, if it
disagrees, surfaces as `gold_manifest_invalid` (not a 25th reason).

## Non-Claims

The manifest is not signed, not a certificate, not federated, and not
production PKI. It is a local hash anchor for the v0.4.0 demo
package.
