# Silver Control Crosswalk + Protected Action Catalog Manifest Schema v0.1.0

> Release line: ProofRail Silver v0.3.6.
>
> This manifest is a hash-anchored local package descriptor. It is not a
> signature, certificate, compliance attestation, audit approval, regulator
> approval, production authorization, runtime-truth oracle, or Gold-governed
> reliance instrument.

## Document identity

| Field | Required | Type | Allowed value |
|---|---|---|---|
| `document_type` | yes | string | `proofrail.silver.control_crosswalk_protected_action_catalog_manifest` |
| `schema_version` | yes | string | `v0.1.0` |
| `proofrail_release` | yes | string | `silver.control_crosswalk.v0.3.6` |
| `hash_algorithm` | yes | string | `sha256` |
| `manifest_id` | yes | string | non-empty |
| `control_pack_id` | yes | string | non-empty; copied from the control pack `control_pack_id` field |
| `generated_at` | yes | string | ISO-8601 UTC timestamp ending in `Z` |
| `package` | yes | object | see below |
| `subjects` | yes | array | exactly two entries, fixed order |

## `package`

| Field | Required | Value |
|---|---|---|
| `package_family` | yes | `silver_control_crosswalk_protected_action_catalog` |
| `release_line` | yes | `silver.control_crosswalk.v0.3.6` |
| `package_root_layout` | yes | non-empty string describing the package root |

The manifest itself is not listed as a subject. The manifest carries metadata
only; subject set must be exactly two files described below.

## `subjects`

`subjects` is a JSON array with exactly two entries in fixed order:

| Index | Role | Path |
|---|---|---|
| 0 | `control_pack` | `control-pack.json` |
| 1 | `conformance_report` | `silver-control-crosswalk-protected-action-catalog-conformance-report.json` |

Each subject must include:

| Field | Required | Type |
|---|---|---|
| `role` | yes | string from the closed set above |
| `path` | yes | non-absolute path with no `..` segments |
| `sha256` | yes | string matching `sha256:<64-lowercase-hex>` |
| `size_bytes` | yes | non-negative integer; byte size of the file |

A wrong subject count, wrong subject ordering, wrong role, missing `path`,
absolute or `..`-bearing `path`, sha256 disagreement against the recomputed
file digest, size disagreement, or missing subject file each fail as
`control_pack_manifest_invalid`.

A bundled conformance-report disagreement (where the bundled report at
`subjects[1].path` byte-disagrees with the report deterministically
re-derived from the verified control pack at `subjects[0].path`) also fails
as `control_pack_manifest_invalid`. The verifier does not introduce a
separate `conformance_report_mismatch` reason. Structural defects in the
control pack itself surface with their dedicated structural reasons before
the post-structural conformance-report re-derivation runs.

## Non-claims

The manifest is hash-anchored and unsigned. v0.3.6 ships local hash anchors
only. The manifest does not declare compliance, certification, audit
approval, regulator approval, auditor approval, production authorization,
operating effectiveness, design effectiveness, runtime truth, transferred
trust, Gold governance, or governed reliance.
