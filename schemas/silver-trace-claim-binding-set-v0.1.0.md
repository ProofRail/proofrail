# Silver Trace Claim Binding Set — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.2
**Document type:** `proofrail.silver.trace_claim_binding_set`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.2`

---

## Purpose

A Silver trace claim binding set declares the protected-action claims
that a Silver reviewer asserts can be bound to specific trace events
in a v0.3.2 trace event fixture. The binding set is a deterministic
input fixture, not a runtime decision and not an authority.

The v0.3.2 runner consumes the binding set and trace event fixture
together to derive a trace binding report. The v0.3.2 verifier
independently re-derives the same report.

---

## Required top-level fields

```
document_type        — "proofrail.silver.trace_claim_binding_set"
schema_version       — "v0.1.0"
proofrail_release    — "v0.3.2"
binding_set_id       — non-empty string
trace_time_window    — object {opens_at, closes_at}
                       both ISO-8601 UTC Z-suffixed; opens_at < closes_at
bindings             — non-empty array of binding rows
scope_limitations    — non-empty array of non-blank strings
non_claims           — non-empty array of non-blank strings
```

## Binding row fields

Each entry in `bindings` MUST include:

```
claim_id                       — non-empty string, unique within the set
required_trace_event_id        — non-empty string
required_trace_id              — non-empty string
required_span_id               — non-empty string
required_protected_action_id   — non-empty string
required_principal_id          — non-empty string
required_decision              — closed enum, same set as trace_event.decision
expected_binding_status        — closed enum (see below)
```

## `expected_binding_status` closed enum

```
bound                              — full match expected
bound_with_warning                 — match expected, with reviewer-supplied warning
trace_gap_detected                 — binding intentionally expects a gap;
                                     the required_trace_event_id need not exist
out_of_scope_for_trace_binding     — referenced event must still exist and
                                     match required fields, but the binding is
                                     declared out of scope for trace-binding purposes
```

`bound`, `bound_with_warning`, and `out_of_scope_for_trace_binding`
rows all require their referenced trace event to exist (raising
`trace_binding_event_missing` if absent) and to match all
`required_*` fields (raising `trace_binding_field_mismatch` if any
mismatch).

Only `trace_gap_detected` may intentionally lack a matching trace
event. Even so, its `required_*` fields are recorded so the gap is
explicit.

---

## Time-window constraint

Every referenced trace event whose `expected_binding_status` is **not**
`trace_gap_detected` MUST have its `event_time` inside
`trace_time_window` (inclusive at `opens_at`, inclusive at
`closes_at`). Violations raise `trace_binding_time_window_mismatch`.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays of strings
(`trace_binding_set_invalid` on missing key or wrong type). Empty
arrays or arrays containing blank / whitespace-only entries raise the
specific reasons `trace_limitations_missing` and
`trace_non_claims_missing` respectively, not the generic
`trace_binding_set_invalid`.

---

## Non-claims about this schema

- A binding set does not prove runtime truth.
- A binding set does not authorize execution.
- A binding set does not make the trace source authoritative.
- A binding set is not a Gold certificate, regulator approval,
  auditor approval, OpenTelemetry conformance, or legal acceptance.
