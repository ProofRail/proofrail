# Silver Demo 010 — Walkthrough (v0.3.3 Adapter Pilot Package)

This walkthrough shows the exact steps the v0.3.3 runner and verifier
perform on the deterministic local adapter pilot fixtures.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.3).
- A working copy of ProofRail at v0.3.3 (HEAD includes
  `tools/silver/build_silver_adapter_pilot_v0_1_0.py` and
  `tools/silver/verify_silver_adapter_pilot_v0_1_0.py`, plus the
  unchanged v0.2.6 adapter validator and v0.3.2 trace binding builder
  and verifier).

## Step 1 — Build the adapter pilot package

```bash
python3 tools/silver/build_silver_adapter_pilot_v0_1_0.py \
  --adapter examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json \
  --source-export fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl \
  --normalization-map fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json \
  --bindings fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json \
  --adapter-pilot-report-id silver-adapter-pilot-v0.3.3-demo-001 \
  --generated-at 2026-06-22T00:10:00Z \
  --output-dir /tmp/proofrail-silver-adapter-pilot-v0.3.3 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-adapter-pilot-v0-3-3
```

Expected final stdout line:

```
PASS: silver adapter pilot package built at /tmp/proofrail-silver-adapter-pilot-v0.3.3
  adapter_pilot_report_id: silver-adapter-pilot-v0.3.3-demo-001
  adapter: adapter/observability-trace-simulated-v0.2.6.json
  source_export.source_record_count: 8
  normalization.normalized_event_count: 8
  nested_trace_binding.verification_status: pass
```

The runner performs these steps in this order:

1. Structural pre-check: refuse if the adapter declares
   `trust_boundary.source_is_trust_authority` ≠ exactly `false`
   (runner-only reason `adapter_validation_failed`).
2. Subprocess-invoke the unchanged v0.2.6 adapter validator (same
   runner-only reason on failure).
3. Validate the source-export JSONL (runner-only reason
   `source_export_validation_failed`).
4. Validate the normalization map JSON (runner-only reason
   `normalization_map_validation_failed`).
5. Validate the binding set JSON structurally (runner-only reason
   `binding_set_validation_failed`).
6. Stage the package directory under
   `<output-dir>.staging.<pid>`.
7. Apply the normalization map to derive normalized trace events
   (same `normalization_map_validation_failed` reason on any
   required-field shortfall).
8. Subprocess-invoke the unchanged v0.3.2 trace binding builder with
   `--force --self-validate` on the normalized files (runner-only
   reason `nested_trace_binding_generation_failed`).
9. Derive `silver-adapter-pilot-report.json` and build
   `silver-adapter-pilot-manifest.json` with seven subjects in fixed
   order.
10. If `--self-validate`, subprocess-invoke the v0.3.3 verifier
    against the staged manifest BEFORE the atomic publish (runner-only
    reason `adapter_pilot_self_validation_failed`).
11. Atomic publish: only AFTER staging build and (optional)
    self-validation succeed does the runner remove an existing
    `--output-dir` (required `--force`) and `os.replace()` the
    staging directory into place. Any earlier failure leaves staging
    cleaned up and `--output-dir` untouched.

## Step 2 — Verify the adapter pilot package

```bash
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \
  --manifest /tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-manifest.json
```

Expected output:

```
PASS: Silver adapter pilot valid (silver-adapter-pilot-v0.3.3-demo-001)
```

The verifier performs the following ordered checks. Each check maps
to a specific stable failure reason; OR-accepting adjacent reasons
is disallowed.

| #  | Check                                                                                            | Failure reason on disagreement              |
|----|--------------------------------------------------------------------------------------------------|---------------------------------------------|
| 1  | Parse and structurally validate the manifest                                                     | `invalid_adapter_pilot_manifest`            |
| 2  | Subject path traversal (BEFORE exact path equality)                                              | `adapter_pilot_subject_path_traversal`      |
| 3  | Exact subject path + role equality against `SUBJECT_ORDER`                                       | `invalid_adapter_pilot_manifest`            |
| 4  | Subject file existence                                                                           | `adapter_pilot_subject_file_missing`        |
| 5  | Subject SHA-256 + size recomputation                                                             | `adapter_pilot_subject_hash_mismatch`       |
| 6  | Adapter structural pre-check (BEFORE v0.2.6 validator subprocess)                                | `adapter_pilot_source_marked_authority`     |
| 7  | v0.2.6 adapter validator subprocess                                                              | `adapter_pilot_adapter_invalid`             |
| 8  | Parse source export; field/enum checks                                                           | `source_export_invalid`                     |
| 9  | Unique `export_record_id` and unique `(trace_id, span_id)`                                       | `source_export_duplicate`                   |
| 10 | Strict `(span.start_time, export_record_id)` ascending ordering                                  | `source_export_time_order_invalid`          |
| 11 | Parse normalization map; field/mapping language checks                                           | `normalization_map_invalid`                 |
| 12 | Re-derive normalized events; required target field present per record                            | `normalization_required_field_missing`      |
| 13 | Parse packaged normalized trace events                                                           | `normalized_trace_invalid`                  |
| 14 | Re-derived normalized bytes equal packaged normalized bytes                                      | `normalized_trace_mismatch`                 |
| 15 | Subprocess-invoke unchanged v0.3.2 verifier on nested manifest                                   | `nested_trace_binding_invalid`              |
| 16 | Nested manifest subjects[0]/[1]/[2] hashes equal outer subjects[0]/[3]/[4]                       | `nested_trace_binding_mismatch`             |
| 17 | Parse report; field/enum checks                                                                  | `adapter_pilot_report_invalid`              |
| 18 | Cross-check report hashes / paths / source_format vs manifest and inputs                         | `adapter_pilot_report_binding_mismatch`     |
| 19 | Re-compute source_record_count and normalized_event_count                                        | `adapter_pilot_report_count_mismatch`       |
| 20 | Required claim IDs present                                                                       | `adapter_pilot_claim_missing`               |
| 21 | Required claims status == `pass`                                                                 | `adapter_pilot_claim_failed`                |
| 22 | Evidence refs package-local and safe (no `..`, no absolute paths)                                | `adapter_pilot_evidence_ref_invalid`        |
| 23 | `scope_limitations` non-empty / non-blank (manifest, report)                                     | `adapter_pilot_limitations_missing`         |
| 24 | `non_claims` non-empty / non-blank (manifest, report)                                            | `adapter_pilot_non_claims_missing`          |
| 25 | Overclaim scan OUTSIDE `scope_limitations` / `non_claims`                                        | `adapter_pilot_overclaim`                   |

24 stable failure reasons across the 25 ordered checks (steps 1 and 3
share `invalid_adapter_pilot_manifest`). The six runner-only refusal
codes (`adapter_validation_failed`,
`source_export_validation_failed`,
`normalization_map_validation_failed`,
`binding_set_validation_failed`,
`nested_trace_binding_generation_failed`,
`adapter_pilot_self_validation_failed`) are NEVER emitted by the
verifier.

## Step 3 — Inspect the report

```bash
python3 -c "import json; d = json.load(open('/tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-report.json')); print(json.dumps(d['pilot_summary'], indent=2))"
```

Expected output:

```json
{
  "nested_trace_binding_status": "pass",
  "normalization_status": "pass",
  "normalized_events_match_source": true,
  "runtime_truth_claimed": false,
  "source_is_trust_authority": false
}
```

## Step 4 — Run the regression test

```bash
make verify-silver-adapter-pilot-v0-3-3
```

This runs `tests/test_silver_adapter_pilot_v0_3_3.sh`, which
exercises every stable verifier failure reason (24) and every
runner-only refusal reason (6). The test prints a final stable PASS
line.

## What the demo intentionally does **not** do

- It does not query any real OpenTelemetry collector, vendor service,
  observability platform, SIEM, GRC, gateway, policy-engine, or
  ticketing system.
- It does not assert that the source system is a trust authority.
- It does not certify OpenTelemetry conformance.
- It does not certify any vendor integration.
- It does not authorize production reliance, regulator acceptance,
  auditor acceptance, or legal acceptance.
- It does not extend the substance of any earlier-release Silver
  evidence.
- It does not resolve or cross-validate `source_event_ref` strings
  against any external package; v0.3.3 carries them through
  normalization as opaque labels.
