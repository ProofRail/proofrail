# Silver Trace Binding Report — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.2
**Document type:** `proofrail.silver.trace_binding_report`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.2`

---

## Purpose

The Silver trace binding report records the deterministic result of
binding each protected-action claim in a v0.3.2 trace claim binding
set to a specific trace event in a v0.3.2 trace event fixture. The
report's fields are entirely derived from the inputs by the v0.3.2
runner; no field may be hand-authored.

The report is **not** runtime proof, OpenTelemetry conformance, a
Gold certificate, regulator approval, auditor approval, legal
acceptance, or governed reliance.

---

## Required top-level fields

```
document_type             — "proofrail.silver.trace_binding_report"
schema_version            — "v0.1.0"
proofrail_release         — "v0.3.2"
trace_binding_report_id   — non-empty string
generated_at              — ISO-8601 UTC, Z-suffixed
trace_source              — object (see below)
trace_events              — object (see below)
binding_set               — object (see below)
binding_summary           — object (see below)
bindings                  — array of binding rows (see below)
scope_limitations         — non-empty array of non-blank strings
non_claims                — non-empty array of non-blank strings
```

## `trace_source`

```
source_type                 — "observability_trace"
source_is_trust_authority   — exactly false (forced by runner)
adapter_descriptor_path     — relative path under package root
                              (no '..', no absolute prefix)
adapter_descriptor_sha256   — "sha256:<hex>"
```

If `source_is_trust_authority` is not exactly `false`, the verifier
raises `trace_source_marked_authority`. The runner forces the field
to `false` regardless of input; only a tampered report can carry a
different value.

## `trace_events`

```
events_path        — "trace-events.jsonl"
events_sha256      — "sha256:<hex>"
event_count        — integer >= 1
time_window        — {opens_at, closes_at} (copied from binding set)
```

## `binding_set`

```
binding_set_id     — string (copied from binding set)
bindings_path      — "trace-claim-bindings.json"
bindings_sha256    — "sha256:<hex>"
binding_count      — integer >= 1
```

## `binding_summary`

```
bound_count                        — derived from bindings[].binding_status
bound_with_warning_count           — derived
trace_gap_detected_count           — derived
out_of_scope_count                 — derived
source_is_trust_authority          — exactly false
```

The verifier independently recomputes each count from
`bindings[].binding_status` and raises `trace_report_count_mismatch`
on any disagreement.

## `bindings[i]`

Each binding row MUST include:

```
claim_id              — string (matches binding-set row)
trace_event_id        — string (matches the resolved event, or the
                        required_trace_event_id for gap rows)
trace_id              — string
span_id               — string
protected_action_id   — string
principal_id          — string
decision              — string (from the resolved event,
                        or "" for trace_gap_detected)
binding_status        — closed enum, identical to expected_binding_status
                        of the source row (see below)
evidence_refs         — array of strings; each string is
                        "trace-events.jsonl#<event_id>" (no '..',
                        no absolute prefix) for resolved rows,
                        or [] for trace_gap_detected rows
warning               — string or null;
                        non-null for bound_with_warning,
                        trace_gap_detected, and
                        out_of_scope_for_trace_binding rows;
                        null for bound rows
```

`binding_status` MUST exactly equal the source row's
`expected_binding_status`. Any divergence raises
`trace_report_status_mismatch`, except where the divergence is a
downgrade from a non-clean status (`bound_with_warning`,
`trace_gap_detected`, `out_of_scope_for_trace_binding`) to `bound`,
which raises the more specific `trace_warning_downgrade` and is
checked first.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays of strings
(`trace_report_invalid` on missing key or wrong type). Empty arrays
or arrays containing blank / whitespace-only entries raise the
specific reasons `trace_limitations_missing` and
`trace_non_claims_missing` respectively.

---

## Forbidden positive overclaim tokens

The verifier rejects any of the following tokens when they appear
outside `scope_limitations` or `non_claims` arrays:

```
gold-ready, ready for Gold, certified, approved, audited,
legally accepted, legally revoked, challenge resolved, Gold accepted,
compliant, production-approved, regulator-ready, trust transferred,
runtime proof, authoritative trace, OpenTelemetry compliant,
OpenTelemetry conformance
```

Violations raise `trace_overclaim`.

---

## Non-claims about this schema

- The report is not runtime proof.
- The report does not make the trace source authoritative.
- The report is not OpenTelemetry conformance.
- The report is not a Gold certificate, regulator approval, auditor
  approval, legal acceptance, compliance certification, production
  authorization, or governed reliance.
