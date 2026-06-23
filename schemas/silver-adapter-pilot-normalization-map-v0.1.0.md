# Silver Adapter Pilot Normalization Map — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.3
**Document type:** `proofrail.silver.adapter_pilot_normalization_map`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.3`

---

## Purpose

A Silver adapter pilot normalization map is a deterministic, hash-bound,
declarative description of how each field in an OpenTelemetry-shaped
local source-export record maps to a ProofRail v0.3.2 trace event
field.

The normalization map is **the only normalization mechanism** used by
the v0.3.3 adapter pilot. It expresses one of:

- a **dot-path** into the source record (e.g.
  `span.attributes.proofrail.event_id`); or
- a **constant value** prefixed with `constant:` (e.g.
  `constant:proofrail.silver.trace_event`).

The mapping language deliberately admits **no other operations**:
no Python `eval`, no JSONPath dependency, no regular expressions,
no embedded code, no helpers, no transformations, no plugins. The
verifier rejects any mapping value that is neither a dot-path nor a
`constant:<value>` literal.

The normalization map is **evidence input**. It is not a vendor
contract, not a production adapter, not OpenTelemetry conformance,
not runtime truth, and not a trust authority.

---

## Required top-level fields

```
document_type           — "proofrail.silver.adapter_pilot_normalization_map"
schema_version          — "v0.1.0"
proofrail_release       — "v0.3.3"
normalization_map_id    — non-empty string
source_format           — non-empty string;
                          MUST equal the export_format of every
                          source-export record processed
target_document_type    — "proofrail.silver.trace_event"
field_mappings          — JSON object;
                          keys are dot-path-into-target;
                          values are dot-path-into-source or "constant:<value>"
required_target_fields  — non-empty array of dot-path-into-target strings
scope_limitations       — array (presence/type checked early; emptiness checked later)
non_claims              — array (presence/type checked early; emptiness checked later)
```

---

## Mapping language

A target field is either:

- a **scalar leaf** keyed by a dot-path (e.g. `event_id`,
  `attributes.proofrail.scenario_id`); or
- an object whose leaves are themselves keyed by dot-paths.

Each mapping **value** is exactly one of:

```
<source.dot.path>          — copy the value at this path in the source record
                             if absent, the target field is omitted;
                             if the target field is in required_target_fields,
                             absence raises normalization_required_field_missing.
constant:<literal>         — set this target field to the literal string value.
                             empty literal is permitted only when the target field
                             is not in required_target_fields.
```

The verifier raises `normalization_map_invalid` on:

- missing required top-level field;
- wrong type;
- mapping value that is neither a non-empty dot-path nor a `constant:<value>`;
- mapping target dot-path that contains an empty component;
- duplicate target dot-path key in `field_mappings`;
- target document type other than `proofrail.silver.trace_event`.

---

## `required_target_fields`

The verifier checks every entry in `required_target_fields` is
present and non-empty in every re-derived normalized trace event.
A missing or empty required target field raises
`normalization_required_field_missing`.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays
(`normalization_map_invalid` on missing key or wrong type). Empty
arrays or arrays with blank / whitespace-only entries raise the
specific reasons `adapter_pilot_limitations_missing` and
`adapter_pilot_non_claims_missing` respectively, not the generic
`normalization_map_invalid`.

---

## Non-claims about this schema

- The normalization map is not OpenTelemetry conformance.
- The normalization map is not a vendor adapter contract.
- The normalization map is not a production integration.
- The normalization map does not make the source authoritative.
- The normalization map does not prove runtime truth.
- The normalization map is not a Gold readiness assessment,
  regulator approval, auditor approval, legal acceptance,
  compliance certification, or production authorization.
