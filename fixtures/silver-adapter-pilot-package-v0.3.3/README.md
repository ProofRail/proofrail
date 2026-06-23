# Silver Adapter Pilot Fixtures — v0.3.3

This directory holds the two committed input fixtures for the
ProofRail v0.3.3 adapter pilot package. The v0.3.3 runner consumes
these fixtures together with the unchanged v0.2.6 simulated
observability-trace adapter descriptor and the unchanged v0.3.2 trace
claim binding set.

The fixtures are **evidence inputs**. They are not OpenTelemetry
conformance evidence, not vendor certifications, not production
integrations, not authoritative telemetry, and not runtime truth.

---

## Files

```
source-otel-trace-export.jsonl
    8-line OpenTelemetry-shaped local source-export fixture.
    Sorted ascending by (span.start_time, export_record_id).
    Conforms to schemas/silver-adapter-pilot-source-export-v0.1.0.md.
    Uses export_format "proofrail.simulated_otel_trace_export.v0.1"
    to disclaim OpenTelemetry conformance.

normalization-map.json
    Declarative normalization map from source export to ProofRail
    v0.3.2 trace events. Mapping language admits only
    <source.dot.path> values and "constant:<literal>" values.
    Conforms to schemas/silver-adapter-pilot-normalization-map-v0.1.0.md.
```

---

## Source event semantics (mirrors v0.3.2 fixture)

```
OTEL-EXPORT-001  payment.release allow (authorized scope)
OTEL-EXPORT-002  vendor.approve allow (authorized scope)
OTEL-EXPORT-003  payment.release deny (authority revoked)
OTEL-EXPORT-004  data.export deny (out of scope action)
OTEL-EXPORT-005  deploy.change deny (out of scope action)
OTEL-EXPORT-006  vendor.approve deny (authority revoked)
OTEL-EXPORT-007  payment.release observe (bypass attempt observed)
OTEL-EXPORT-008  payment.release block (bypass attempt blocked)
```

---

## How the v0.3.3 runner uses these fixtures

```
1. Subprocess-validate the v0.2.6 adapter descriptor.
2. Refuse if source_is_trust_authority != false.
3. Parse and structurally validate source-otel-trace-export.jsonl.
4. Parse and structurally validate normalization-map.json.
5. Parse and structurally validate the v0.3.2 trace claim binding set.
6. Normalize each source-export record into a v0.3.2 trace event by
   applying field_mappings (dot-path lookup or constant literal).
7. Subprocess-invoke the unchanged v0.3.2 trace binding builder
   against the normalized trace events and binding set.
8. Emit the adapter pilot report and adapter pilot manifest.
9. If --self-validate, subprocess-invoke the v0.3.3 verifier against
   the staging manifest before atomic publish.
10. Atomically replace the output directory with the staged package
    (only if --force is supplied when the output dir already exists).
```

---

## Non-claims

- This fixture is not OpenTelemetry conformance.
- This fixture is not a live, production, or vendor trace export.
- This fixture does not assert that the simulated trace collector is
  a trust authority.
- This fixture does not prove runtime truth.
- This fixture is not a regulator approval, third-party audit,
  legal acceptance, compliance certification, production
  authorization, or Gold readiness assessment.
