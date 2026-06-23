# Silver Adapter Pilot Manifest — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.3
**Document type:** `proofrail.silver.adapter_pilot_manifest`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.3`

---

## Purpose

The Silver adapter pilot manifest is the package-level SHA-256 hash
anchor for a v0.3.3 adapter pilot package. It binds exactly seven
subjects in fixed order: the copied v0.2.6 observability-trace
adapter descriptor, the source export fixture, the normalization
map, the derived normalized trace events, the copied trace claim
binding set, the nested v0.3.2 trace binding manifest, and the
derived adapter pilot report.

The manifest is **not** a certificate, approval, audit, or trust
transfer. It is the integrity anchor over a deterministic local
adapter pilot package whose chain binding the v0.3.3 verifier owns
and re-derives.

The copied v0.2.6 adapter descriptor remains responsible for its own
v0.2.6 structural validity; the v0.3.3 verifier subprocess-invokes
the unchanged v0.2.6 adapter validator. The nested v0.3.2 trace
binding package remains responsible for its own v0.3.2 structural
validity; the v0.3.3 verifier subprocess-invokes the unchanged v0.3.2
verifier against `trace-binding/silver-trace-binding-manifest.json`.

---

## Required top-level fields

```
document_type             — "proofrail.silver.adapter_pilot_manifest"
schema_version            — "v0.1.0"
proofrail_release         — "v0.3.3"
adapter_pilot_report_id   — non-empty string
generated_at              — ISO-8601 UTC, Z-suffixed
hash_algorithm            — "sha256"
subjects                  — array of exactly 7 subjects in fixed order
scope_limitations         — array (presence/type checked early; emptiness checked later)
non_claims                — array (presence/type checked early; emptiness checked later)
```

---

## Subjects (fixed order, fixed roles)

```
[0] path: "adapter/observability-trace-simulated-v0.2.6.json"
    role: "adapter_descriptor"
[1] path: "source/source-otel-trace-export.jsonl"
    role: "source_export"
[2] path: "normalization/normalization-map.json"
    role: "normalization_map"
[3] path: "normalized/trace-events.jsonl"
    role: "normalized_trace_events"
[4] path: "normalized/trace-claim-bindings.json"
    role: "normalized_trace_claim_bindings"
[5] path: "trace-binding/silver-trace-binding-manifest.json"
    role: "nested_trace_binding_manifest"
[6] path: "silver-adapter-pilot-report.json"
    role: "adapter_pilot_report"
```

Each subject MUST include:

```
path        — non-empty string, relative to the adapter pilot package root
role        — exactly the role string for its index above
sha256      — "sha256:<hex>"
size_bytes  — integer >= 0
```

A subject whose path is absolute or contains a `..` path component
raises `adapter_pilot_subject_path_traversal` (checked **before**
exact path equality). A missing subject file raises
`adapter_pilot_subject_file_missing`. A subject whose recomputed
SHA-256 disagrees with the recorded value raises
`adapter_pilot_subject_hash_mismatch`.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays
(`invalid_adapter_pilot_manifest` on missing key or wrong type).
Empty arrays or arrays with blank / whitespace-only entries raise
the specific reasons `adapter_pilot_limitations_missing` and
`adapter_pilot_non_claims_missing` respectively, not the generic
`invalid_adapter_pilot_manifest`.

---

## Verifier-owned bindings

The v0.3.3 verifier proves:

```
included adapter descriptor      == subject[0] sha256
                                 == report adapter.adapter_sha256
                                 == v0.2.6 adapter validator PASSes
                                 == source_is_trust_authority is exactly false

included source export           == subject[1] sha256
                                 == report source_export.source_export_sha256
                                 == strict (span.start_time, export_record_id) order
                                 == unique export_record_id and (trace_id, span_id)

included normalization map       == subject[2] sha256
                                 == report normalization.normalization_map_sha256

included normalized events       == subject[3] sha256
                                 == report normalization.normalized_trace_events_sha256
                                 == re-derived from source export + normalization map

included normalized bindings     == subject[4] sha256

included nested manifest         == subject[5] sha256
                                 == report nested_trace_binding.manifest_sha256
                                 == v0.3.2 verifier PASSes
                                 == nested manifest subjects[0]/[1]/[2] hashes match
                                    the v0.3.3 manifest subjects[0]/[3]/[4] hashes

included adapter pilot report    == subject[6] sha256
                                 == required claim IDs present and pass
                                 == counts match re-derived counts
                                 == evidence_refs are package-local and safe
                                 == no forbidden overclaim wording
```

---

## Non-claims about this schema

- The manifest is not a certificate.
- The manifest is not runtime proof.
- The manifest does not make the source authoritative.
- The manifest is not OpenTelemetry conformance.
- The manifest is not a vendor certification.
- The manifest is not a production integration.
- The manifest is not a Gold readiness assessment, regulator
  approval, auditor approval, legal acceptance, compliance
  certification, or production authorization.
