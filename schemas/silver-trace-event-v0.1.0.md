# Silver Trace Event — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.2
**Document type:** `proofrail.silver.trace_event`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.2`

---

## Purpose

A Silver trace event is one deterministic, locally re-derivable record
of a protected-action decision observed on a simulated observability
trace substrate. v0.3.2 uses trace events as **evidence inputs** to a
trace binding report. Trace events are **not** authoritative runtime
proof, OpenTelemetry conformance claims, production observability, or
governed reliance.

A trace event borrows OpenTelemetry-style field naming for
familiarity. ProofRail does not claim OpenTelemetry conformance.

---

## File format

Trace events are stored line-delimited JSON
(`trace-events.jsonl`). One JSON object per line. The file MUST be
sorted strictly by `(event_time, event_id)` ascending. Trailing or
blank lines are not permitted.

---

## Required top-level fields

```
document_type           — "proofrail.silver.trace_event"
schema_version          — "v0.1.0"
proofrail_release       — "v0.3.2"
event_id                — non-empty string, unique within the file
trace_id                — non-empty string
span_id                 — non-empty string;
                          (trace_id, span_id) MUST be unique within the file
event_time              — ISO-8601 UTC, Z-suffixed
principal_id            — non-empty string
protected_action_id     — non-empty string
decision                — closed enum (see below)
decision_reason         — non-empty string
source_event_ref        — non-empty string;
                          opaque labeled reference, e.g.
                          "gateway-event:EVT-002";
                          v0.3.2 does not cross-validate against any
                          external package
attributes              — JSON object (may be empty)
```

## Optional fields

```
parent_span_id          — string
counterparty_id         — string
authority_ref           — string
```

## `decision` closed enum

```
allow
deny
observe
block
```

Any other value raises `trace_events_invalid` in the v0.3.2 verifier.

---

## Determinism and ordering

- Strict ordering by `(event_time, event_id)`.
- No absolute paths or `..` components in `source_event_ref` or any
  other string field.
- Duplicate `event_id` raises `trace_event_duplicate`.
- Duplicate `(trace_id, span_id)` raises `trace_event_duplicate`.
- Ordering violation raises `trace_event_time_order_invalid`.

---

## Non-claims about this schema

- A trace event is not authoritative runtime proof.
- A trace event is not OpenTelemetry conformance evidence.
- A trace event does not assert that the observability substrate is a
  trust authority.
- A trace event does not claim production observability, regulator
  approval, auditor approval, or legal acceptance.
- `source_event_ref` is an opaque labeled string; v0.3.2 does not
  resolve or cross-validate it.
