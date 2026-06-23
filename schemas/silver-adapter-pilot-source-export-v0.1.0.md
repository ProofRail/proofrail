# Silver Adapter Pilot Source Export — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.3
**Document type:** (line-delimited; no document-level wrapper)
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.3`

---

## Purpose

A Silver adapter pilot source export is a deterministic local fixture
that simulates an external observability/trace export in an
OpenTelemetry-shaped JSONL layout. The v0.3.3 adapter pilot runner
normalizes this fixture into ProofRail v0.3.2 trace events via a
declarative normalization map.

The source export is **evidence input** to the adapter pilot. It is
**not** an OpenTelemetry conformance claim, not a live
observability export, not a vendor integration, not runtime truth,
and not authoritative.

The fixture borrows OpenTelemetry-style field naming (`resource`,
`scope`, `span.trace_id`, `span.span_id`, `span.attributes.*`) for
familiarity. ProofRail v0.3.3 does not claim OpenTelemetry
conformance.

---

## File format

The source export is line-delimited JSON (`*.jsonl`). One JSON
object per line. Trailing or blank lines are not permitted. The
file MUST be sorted strictly ascending by
`(span.start_time, export_record_id)`.

---

## Required top-level fields (per line)

```
export_format                                   — non-empty string;
                                                  v0.3.3 fixture uses
                                                  "proofrail.simulated_otel_trace_export.v0.1"
                                                  to disclaim OT conformance
export_record_id                                — non-empty string; unique within file
resource                                        — JSON object (may include
                                                  service.name, service.namespace, etc.)
scope                                           — JSON object (may include name, version)
span                                            — JSON object (see below)
```

## Required `span` subfields

```
span.trace_id                                   — non-empty string
span.span_id                                    — non-empty string;
                                                  (trace_id, span_id) MUST be unique within file
span.name                                       — non-empty string
span.start_time                                 — ISO-8601 UTC, Z-suffixed
span.end_time                                   — ISO-8601 UTC, Z-suffixed
span.attributes                                 — JSON object
```

## Required `span.attributes.proofrail.*` subfields

```
span.attributes.proofrail.event_id              — non-empty string
span.attributes.proofrail.principal_id          — non-empty string
span.attributes.proofrail.protected_action_id   — non-empty string
span.attributes.proofrail.decision              — closed enum (see below)
span.attributes.proofrail.decision_reason       — non-empty string
span.attributes.proofrail.source_event_ref      — non-empty string
span.attributes.proofrail.scenario_id           — non-empty string
```

## Optional `span` and `span.attributes.proofrail.*` subfields

```
span.parent_span_id                             — string
span.attributes.proofrail.counterparty_id       — string
span.attributes.proofrail.authority_ref         — string
```

## `decision` closed enum (mirrors v0.3.2 trace event)

```
allow
deny
observe
block
```

Any other value raises `source_export_invalid` (parse stage) or
`normalized_trace_invalid` (after normalization) in the v0.3.3
adapter pilot verifier.

---

## Determinism and ordering

- Strict ascending sort by `(span.start_time, export_record_id)`.
- Duplicate `export_record_id` raises `source_export_duplicate`.
- Duplicate `(span.trace_id, span.span_id)` raises
  `source_export_duplicate`.
- Out-of-order records raise `source_export_time_order_invalid`.

The runner refuses to emit output if the export fails any of the
above structural checks
(runner-only reason `source_export_validation_failed`).

---

## Non-claims about this schema

- The source export is not OpenTelemetry conformance evidence.
- The source export is not a live or production trace export.
- The source export does not assert that the simulated trace
  collector is a trust authority.
- The source export is not vendor certification, regulator
  approval, auditor approval, or legal acceptance.
- `span.attributes.proofrail.source_event_ref` is an opaque labeled
  string; v0.3.3 does not resolve or cross-validate it.
