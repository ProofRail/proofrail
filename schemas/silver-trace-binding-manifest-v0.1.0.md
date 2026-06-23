# Silver Trace Binding Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.2
**Document type:** `proofrail.silver.trace_binding_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.2`

---

## Purpose

The Silver trace binding manifest is the package-level SHA-256 hash
anchor for a v0.3.2 trace binding package. It binds exactly four
subjects in fixed order: the copied v0.2.6 observability-trace
adapter descriptor, the trace event fixture, the trace claim binding
set, and the derived trace binding report.

The manifest is **not** a certificate, approval, audit, or trust
transfer. It is the integrity anchor over a deterministic local
trace binding package whose chain binding the v0.3.2 verifier owns
and re-derives.

The copied v0.2.6 adapter descriptor remains responsible for its own
v0.2.6 structural validity; the v0.3.2 verifier subprocess-invokes
the unchanged v0.2.6 adapter validator. v0.3.2 additionally rejects
the descriptor if it claims the trace source is a trust authority.

---

## Required top-level fields

```
document_type             — "proofrail.silver.trace_binding_manifest"
schema_version            — "v0.1.0"
proofrail_release         — "v0.3.2"
trace_binding_report_id   — non-empty string
generated_at              — ISO-8601 UTC, Z-suffixed
hash_algorithm            — "sha256"
subjects                  — array of exactly 4 subjects in fixed order
scope_limitations         — array (presence/type checked early; emptiness checked later)
non_claims                — array (presence/type checked early; emptiness checked later)
```

---

## Subjects (fixed order, fixed roles)

```
[0] path: "adapter/observability-trace-simulated-v0.2.6.json"
    role: "trace_source_adapter_descriptor"
[1] path: "trace-events.jsonl"
    role: "trace_events"
[2] path: "trace-claim-bindings.json"
    role: "trace_claim_binding_set"
[3] path: "silver-trace-binding-report.json"
    role: "silver_trace_binding_report"
```

Each subject MUST include:

```
path        — non-empty string, relative to the trace binding package root
role        — exactly the role string for its index above
sha256      — "sha256:<hex>"
size_bytes  — integer >= 0
```

A subject whose path is absolute or contains a `..` path component
raises `trace_subject_path_traversal` (checked **before** exact
path equality). A missing subject file raises
`trace_subject_file_missing`. A subject whose recomputed SHA-256
disagrees with the recorded value raises
`trace_subject_hash_mismatch`.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays
(`invalid_trace_binding_manifest` on missing key or wrong type).
Empty arrays or arrays with blank / whitespace-only entries raise
the specific reasons `trace_limitations_missing` and
`trace_non_claims_missing` respectively, not the generic
`invalid_trace_binding_manifest`.

---

## Verifier-owned bindings

The v0.3.2 verifier proves:

```
included adapter descriptor      == subject[0] sha256
                                 == report trace_source.adapter_descriptor_sha256
                                 == v0.2.6 adapter validator PASSes
                                 == source_is_trust_authority is exactly false

included trace events            == subject[1] sha256
                                 == report trace_events.events_sha256
                                 == strict (event_time, event_id) order
                                 == unique event_id and (trace_id, span_id)

included binding set             == subject[2] sha256
                                 == report binding_set.bindings_sha256

included trace binding report    == subject[3] sha256
                                 == bindings[] re-derived from inputs
                                 == binding_summary counts recomputed
```

---

## Non-claims about this schema

- The manifest is not a certificate.
- The manifest is not runtime proof.
- The manifest does not make the trace source authoritative.
- The manifest is not OpenTelemetry conformance.
- The manifest is not a Gold readiness assessment, regulator
  approval, auditor approval, legal acceptance, compliance
  certification, or production authorization.
