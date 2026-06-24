# Silver Control Crosswalk + Protected Action Catalog Conformance Report Schema v0.1.0

> Release line: ProofRail Silver v0.3.6.
>
> A conformance report is a deterministic restatement of structural facts
> derived from a verified control pack. It is not a compliance attestation,
> certification, audit decision, regulator decision, authorization, or
> Gold-governed reliance decision.

## Document identity

| Field | Required | Type | Allowed value |
|---|---|---|---|
| `document_type` | yes | string | `proofrail.silver.control_crosswalk_protected_action_catalog_conformance_report` |
| `schema_version` | yes | string | `v0.1.0` |
| `report_id` | yes | string | non-empty |
| `generated_at` | yes | string | ISO-8601 UTC timestamp ending in `Z` |

## `control_pack_binding`

| Field | Required | Value |
|---|---|---|
| `control_pack_id` | yes | string copied from the control pack |
| `control_pack_sha256` | yes | lowercase hex string of length 64 of the bytes at `subjects[0].path` |
| `profile` | yes | string copied from the control pack `profile` field |

## `summary`

The report records the following deterministically derived counts and lists:

- `protected_action_count` (integer)
- `protected_action_ids` (sorted list of strings)
- `crosswalk_entry_count` (integer)
- `crosswalk_mapping_ids` (sorted list of strings)
- `referenced_artifact_types` (sorted list of strings)
- `referenced_control_concept_ids` (sorted list of strings)
- `control_limitation_count` (integer)
- `dependency_reference_count` (integer)
- `version_binding_count` (integer)
- `non_claim_count` (integer)

## Re-derivation rule

The verifier independently re-derives every field of the conformance report
from the verified control pack at `subjects[0].path`. A byte disagreement
between the bundled report at `subjects[1].path` and the re-derived report
emits `control_pack_manifest_invalid`. The verifier does not emit a separate
`conformance_report_mismatch` reason; the re-derivation runs only AFTER all
22 structural control-pack checks pass, so any earlier structural defect
surfaces with its dedicated structural reason.

## Non-claims

The conformance report is not a compliance attestation, certification, audit
decision, regulator decision, authorization, or Gold-governed reliance
decision. It is a deterministic restatement of structural facts and counts.
