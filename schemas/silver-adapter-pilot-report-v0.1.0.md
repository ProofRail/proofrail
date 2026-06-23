# Silver Adapter Pilot Report — Schema v0.1.0

**Status:** Draft / ProofRail v0.3.3
**Document type:** `proofrail.silver.adapter_pilot_report`
**Schema version:** `v0.1.0`
**ProofRail release:** `v0.3.3`

---

## Purpose

A Silver adapter pilot report is the deterministic record produced by
the v0.3.3 adapter pilot runner. It captures the input identities
(adapter descriptor, source export, normalization map), the derived
normalized trace events, the nested v0.3.2 trace binding package
identity, and the required pilot claims.

The report is **derived evidence**. It is not a vendor certification,
not a production integration, not OpenTelemetry conformance, not
runtime truth, not a regulator approval, not an audit, not legal
acceptance, and not a Gold certificate.

---

## Required top-level fields

```
document_type                — "proofrail.silver.adapter_pilot_report"
schema_version               — "v0.1.0"
proofrail_release            — "v0.3.3"
adapter_pilot_report_id      — non-empty string
generated_at                 — ISO-8601 UTC, Z-suffixed
adapter                      — JSON object (see below)
source_export                — JSON object (see below)
normalization                — JSON object (see below)
nested_trace_binding         — JSON object (see below)
pilot_summary                — JSON object (see below)
claims                       — array of objects (see below)
scope_limitations            — array (presence/type checked early; emptiness checked later)
non_claims                   — array (presence/type checked early; emptiness checked later)
```

---

## `adapter` object

```
adapter_path                 — non-empty package-local string;
                               MUST equal "adapter/observability-trace-simulated-v0.2.6.json"
adapter_sha256               — "sha256:<hex>";
                               MUST equal manifest subjects[0].sha256
source_is_trust_authority    — boolean; MUST be exactly false
```

## `source_export` object

```
source_export_path           — non-empty package-local string;
                               MUST equal "source/source-otel-trace-export.jsonl"
source_export_sha256         — "sha256:<hex>";
                               MUST equal manifest subjects[1].sha256
source_record_count          — integer; MUST equal the line count of source export
source_format                — non-empty string;
                               MUST equal the export_format of every source-export record
```

## `normalization` object

```
normalization_map_path       — non-empty package-local string;
                               MUST equal "normalization/normalization-map.json"
normalization_map_sha256     — "sha256:<hex>";
                               MUST equal manifest subjects[2].sha256
normalized_trace_events_path — non-empty package-local string;
                               MUST equal "normalized/trace-events.jsonl"
normalized_trace_events_sha256
                             — "sha256:<hex>";
                               MUST equal manifest subjects[3].sha256
normalized_event_count       — integer; MUST equal source_record_count
```

## `nested_trace_binding` object

```
manifest_path                — non-empty package-local string;
                               MUST equal "trace-binding/silver-trace-binding-manifest.json"
manifest_sha256              — "sha256:<hex>";
                               MUST equal manifest subjects[5].sha256
verification_status          — string; MUST be exactly "pass"
```

## `pilot_summary` object

```
source_is_trust_authority    — boolean; MUST be exactly false
normalization_status         — string; MUST be exactly "pass"
nested_trace_binding_status  — string; MUST be exactly "pass"
normalized_events_match_source
                             — boolean; MUST be exactly true
runtime_truth_claimed        — boolean; MUST be exactly false
```

## `claims[]` objects

Each claim object MUST include:

```
claim_id        — non-empty string
status          — string; required claims MUST have status "pass"
evidence_refs   — array of non-empty strings;
                  each entry MUST be a package-local relative path
                  (no absolute paths; no ".." components)
```

The verifier requires exactly seven claim IDs to be present (extra
claims are permitted but every required claim MUST be present and
pass):

```
adapter_descriptor_valid
source_not_trust_authority
source_export_hash_verifiable
normalization_map_valid
normalized_trace_events_rederived
nested_trace_binding_valid
no_runtime_truth_claimed
```

Missing required claim raises `adapter_pilot_claim_missing`.
Required claim with non-`pass` status raises
`adapter_pilot_claim_failed`. Unsafe `evidence_refs` entries raise
`adapter_pilot_evidence_ref_invalid`.

---

## `scope_limitations` and `non_claims`

Both MUST be present and typed as arrays
(`adapter_pilot_report_invalid` on missing key or wrong type). Empty
arrays or arrays with blank / whitespace-only entries raise the
specific reasons `adapter_pilot_limitations_missing` and
`adapter_pilot_non_claims_missing` respectively, not the generic
`adapter_pilot_report_invalid`.

---

## Overclaim scan

The verifier rejects any positive token (in claim IDs, claim text,
or other report fields outside `scope_limitations` and
`non_claims`) that asserts production integration, source
authority, OpenTelemetry conformance, runtime truth or proof,
vendor certification, compliance, legal reliance, or Gold
conformance. Raised as `adapter_pilot_overclaim`.

---

## Non-claims about this schema

- The report is not a Gold certificate.
- The report is not a vendor certification.
- The report is not an OpenTelemetry conformance claim.
- The report is not a production integration claim.
- The report is not a regulator approval.
- The report is not a third-party audit.
- The report is not legal acceptance.
- The report is not a compliance certification.
- The report is not a production authorization.
- The report is not a runtime truth guarantee.
