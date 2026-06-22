# ProofRail Silver Evidence Source Adapter Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Profile-informed schema
**Claim family:** ProofRail Silver evidence source adapter descriptors

---

## 1. Purpose

A Silver Evidence Source Adapter descriptor declares how an evidence source — gateway, observability trace system, SIEM, policy engine, GRC platform, or native ProofRail tooling — maps its events, controls, revocation posture, bypass handling, and subject hashes into ProofRail-relevant evidence fields.

A descriptor is **not** evidence by itself, **not** a trust decision, and **not** a certification. It is a structured declaration that lets a relying party inspect the shape of source evidence before that evidence is folded into a Bronze claim or a Silver evidence bundle.

> v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy.

---

## 2. Format

JSON. UTF-8 encoded. Two-space indentation in committed canonical examples.

Validators do not require a particular serialization. They parse the file as JSON and operate on the parsed structure.

---

## 3. Top-Level Structure

```json
{
  "document_type": "proofrail.silver.evidence_source_adapter",
  "schema_version": "v0.1.0",
  "proofrail_release": "v0.2.6",
  "adapter_id": "<dotted identifier>",
  "adapter_version": "v0.1.0",
  "source": { ... },
  "trust_boundary": { ... },
  "control_surface": { ... },
  "protected_action_mapping": { ... },
  "evidence_capabilities": { ... },
  "normalization": { ... },
  "sample_artifact_refs": [ ... ],
  "adapter_limitations": [ ... ],
  "non_claims": [ ... ]
}
```

All top-level fields except `sample_artifact_refs` are required. `sample_artifact_refs` is optional; when present, it is structurally validated.

| Field | Notes |
|---|---|
| `document_type` | Must equal `proofrail.silver.evidence_source_adapter`. |
| `schema_version` | Must equal `v0.1.0`. |
| `proofrail_release` | Must equal `v0.2.6`. |
| `adapter_id` | Stable identifier; lowercase letters, digits, dots, underscores, hyphens; must start with a lowercase letter or digit. |
| `adapter_version` | Adapter descriptor revision (free-form short string, e.g. `v0.1.0`). |

---

## 4. `source`

Declares the evidence source category and provenance metadata.

```json
{
  "source_type": "<one of: native_proofrail | gateway | observability_trace | siem_log | policy_engine | grc_platform>",
  "source_name": "<human-readable name>",
  "vendor_or_project": "<string; use 'simulated' for canonical examples>",
  "product_or_component": "<string>",
  "source_version": "<string>",
  "deployment_scope": "<string; e.g. 'simulated_external', 'native_local'>"
}
```

The set of `source_type` values is closed at v0.2.6:

| `source_type` | Meaning |
|---|---|
| `native_proofrail` | Evidence produced directly by existing ProofRail tools. |
| `gateway` | Tool/MCP gateway decision events. |
| `observability_trace` | Trace spans binding actor/action/decision context. |
| `siem_log` | Security event or incident log evidence. |
| `policy_engine` | Policy decision event source. |
| `grc_platform` | Workflow/risk/approval source; **not** technical enforcement. |

Real vendor names must not appear in canonical examples.

---

## 5. `trust_boundary`

Records the explicit non-authority position of the source.

```json
{
  "source_is_trust_authority": false,
  "proofrail_role": "evidence_source",
  "reliance_statement": "<short string>"
}
```

| Field | Required value |
|---|---|
| `source_is_trust_authority` | Must be exactly `false`. Any other value → `source_marked_as_trust_authority`. |
| `proofrail_role` | Must equal `evidence_source`. |
| `reliance_statement` | Non-empty string; must not present the source as authoritative. |

---

## 6. `control_surface`

Declares the source's control surface shape.

```json
{
  "control_surface_type": "<string>",
  "description": "<string>",
  "controlled_path_required": true,
  "protected_action_channel": "<string>",
  "bypass_observation_point": "<string>",
  "revocation_observation_point": "<string>"
}
```

All fields are required. `controlled_path_required` must be a boolean.

---

## 7. `protected_action_mapping`

Lists the protected actions the source can observe and how source fields map into ProofRail's actor/action/subject model.

```json
{
  "protected_action_ids": ["payment.release", "vendor.approve", "data.export", "deploy.change"],
  "source_action_field": "<source field path>",
  "source_actor_field": "<source field path>",
  "source_subject_field": "<source field path>"
}
```

`protected_action_ids` must be a non-empty list of dotted identifiers matching `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`. All three source field mappings must be non-empty strings.

---

## 8. `evidence_capabilities`

Every descriptor must declare all six required capabilities:

```text
decision_event
bypass_evidence
revocation_status
subject_hashes
source_identity
timestamp_integrity
```

Each capability is a JSON object with at least:

```json
{
  "status": "provided | not_provided | not_applicable",
  "description": "<string>"
}
```

If `status != "provided"`, the capability **must** include a non-empty `limitation` string explaining the gap. v0.2.6 makes evidence gaps explicit; hiding them is a validation failure (`evidence_capability_missing`).

### 8.1 `decision_event`

`decision_event.status` **must be `provided`** for a conforming v0.2.6 adapter. A source that cannot supply a decision event is not a conforming evidence source adapter for protected-action reliance.

When `provided`, the capability must include:

```json
{
  "status": "provided",
  "event_type": "<source event type>",
  "timestamp_field": "<source field path>",
  "decision_field": "<source field path>",
  "reason_field": "<source field path>",
  "source_record_id_field": "<source field path>",
  "description": "<string>"
}
```

Missing or empty mapping fields → `decision_event_mapping_missing`.

### 8.2 Other capabilities

`bypass_evidence`, `revocation_status`, `subject_hashes`, `source_identity`, `timestamp_integrity` follow the same status enum. When `provided`, they should include source-specific mapping detail appropriate to the capability. When `not_provided` or `not_applicable`, they must include a `limitation` string.

---

## 9. `normalization`

```json
{
  "normalized_event_type": "<string>",
  "normalization_notes": ["<note>", "<note>"]
}
```

`normalization_notes` must be a non-empty list of non-empty strings. Empty list or whitespace-only entries → `normalization_notes_missing`.

---

## 10. `sample_artifact_refs` (optional)

Optional list of references to sample artifacts the adapter may emit. When present, each entry is an object:

```json
{
  "path": "<relative path; no '..'; not absolute>",
  "role": "<short string>",
  "sha256": "<sha256:<hex> or example placeholder>"
}
```

Any path containing `..` or starting with `/` → `evidence_artifact_path_traversal`.

v0.2.6 canonical examples deliberately omit `sample_artifact_refs` so the examples are self-contained.

---

## 11. `adapter_limitations`

Non-empty list of non-empty strings declaring what the adapter does not prove. Whitespace-only entries → `adapter_limitations_missing`.

---

## 12. `non_claims`

Non-empty list of non-empty strings. At minimum, every canonical example states that the adapter is not a certification and does not make the source a trust authority. Whitespace-only entries → `adapter_non_claims_missing`.

---

## 13. Validation Rules (stable failure reasons)

The validator (`tools/silver/validate_evidence_source_adapter_v0_1_0.py`) emits one stable failure reason per failure mode:

```
invalid_adapter_descriptor
invalid_source_type
duplicate_adapter_id
source_marked_as_trust_authority
control_surface_missing
protected_action_mapping_missing
evidence_capability_missing
decision_event_mapping_missing
evidence_artifact_path_traversal
normalization_notes_missing
adapter_limitations_missing
adapter_non_claims_missing
```

Check order (short-circuit per descriptor):

1. JSON parse → `invalid_adapter_descriptor`.
2. Top-level shape, document type, schema version, release, `adapter_id` format → `invalid_adapter_descriptor`.
3. `source.source_type` ∈ closed set → `invalid_source_type`.
4. `trust_boundary.source_is_trust_authority == false` → else `source_marked_as_trust_authority`.
5. `trust_boundary.proofrail_role == "evidence_source"`, reliance_statement non-empty → `invalid_adapter_descriptor`.
6. `control_surface` and required subfields present → `control_surface_missing`.
7. `protected_action_mapping` non-empty, dotted-id format, mapping fields present → `protected_action_mapping_missing`.
8. `evidence_capabilities` contains all six required keys; non-`provided` capabilities carry non-empty `limitation`; capability `description` non-empty → `evidence_capability_missing`.
9. `decision_event.status == "provided"` and required mapping fields populated → `decision_event_mapping_missing`.
10. `sample_artifact_refs[*].path` (if present) has no `..` and is not absolute → `evidence_artifact_path_traversal`.
11. `normalization.normalization_notes` non-empty list of non-empty strings → `normalization_notes_missing`.
12. `adapter_limitations` non-empty list of non-empty strings → `adapter_limitations_missing`.
13. `non_claims` non-empty list of non-empty strings → `adapter_non_claims_missing`.

Directory mode additionally enforces `adapter_id` uniqueness → `duplicate_adapter_id`.

---

## 14. What This Schema Does Not Define

- A signed adapter envelope. Adapter descriptors are unsigned local declarations.
- An ingestion format. The schema does not specify how source events are read.
- A trust decision. Validation success means the descriptor is well-formed; it does not certify the source.
- A relying-party acceptance record. That is reserved for v0.2.8.
- A Gold artifact. v0.2.6 stays strictly Silver-side.

---

## 15. Versioning

Schema follows `vMAJOR.MINOR.PATCH`. Backward-incompatible changes increment MINOR or MAJOR. v0.1.0 is the initial release of the adapter descriptor schema and corresponds to ProofRail release v0.2.6.
