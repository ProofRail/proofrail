# Gold Governed Reliance Conformance Report Schema v0.1.0

Schema for the Gold v0.4.0 conformance report (subject [1] in the
v0.4.0 package manifest). The report is derived deterministically by
the runner from the package body and re-derived independently by the
verifier as a byte-compare.

## Boundary

The conformance report records that the package body passes the v0.4.0
structural verifier checks. It is not a signature, not a certificate,
not a substantive evaluation of the upstream Silver evidence, and not
full Gold.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.governed_reliance_conformance_report`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `package_id` | string | yes | Cross-anchored to package body. |
| `governed_reliance_demo_id` | string | yes | Cross-anchored to package body. |
| `report_id` | string | yes | Closed grammar. |
| `generated_at` | string | yes | ISO-8601 UTC. |
| `entries` | array of exactly 24 objects | yes | One per approved verifier reason in fixed order. |

## entries[]

Exactly 24 entries in fixed order, one per approved verifier reason.
Order matches the verifier check ordering, with the first entry
corresponding to `gold_manifest_invalid`. Each entry shape:

| Field | Type | Required | Notes |
|---|---|---|---|
| `check_id` | string | yes | `check_NN` where `NN` is `01`..`24`. |
| `check_name` | string | yes | The approved verifier reason name verbatim. |
| `status` | string | yes | Always `pass` in a published conformance report. |
| `detail` | string | yes | Short human description of what passing means for that check. |

## Deterministic Serialization

The runner serializes the conformance report with:

```python
json.dumps(report_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The verifier re-derives the conformance report from the package body
using the same serializer. Any byte disagreement surfaces as
`gold_manifest_invalid` (no 25th reason).

## Derivation Inputs

The conformance report's byte image depends only on:

- the package body's `package_id`;
- the package body's `governed_reliance_demo_id`;
- the manifest's `report_id`;
- the manifest's `generated_at`;
- the fixed 24-entry schedule of `check_id`, `check_name`, `status`,
  and `detail`.

The 24-entry schedule itself is constant across all v0.4.0 packages.

## Verifier Notes

The byte-compare re-derivation runs only AFTER all 24 structural
checks against the package body have passed. A defect that any of
checks 01–24 would catch surfaces with its dedicated reason and never
collapses into the conformance-report disagreement check.

## Non-Claims

The conformance report is not signed, not certified, not approved, not
audited, not a legal instrument, not a transfer of reliance, and not
full Gold. It records that the local v0.4.0 structural verifier
passes against the supplied package body.
