# Silver Demo 009 — Walkthrough (v0.3.2 Trace Binding Profile)

This walkthrough shows the exact steps the v0.3.2 runner and verifier
perform on the deterministic local trace binding fixtures.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.2).
- A working copy of ProofRail at v0.3.2 (HEAD includes
  `tools/silver/build_silver_trace_binding_v0_1_0.py` and
  `tools/silver/verify_silver_trace_binding_v0_1_0.py`).

## Step 1 — Build the trace binding package

```bash
python3 tools/silver/build_silver_trace_binding_v0_1_0.py \
  --adapter examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json \
  --trace-events fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl \
  --bindings fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json \
  --trace-binding-report-id proofrail-trace-binding-report-demo-001 \
  --generated-at 2026-06-22T00:00:00Z \
  --output-dir /tmp/proofrail-silver-trace-binding-v0.3.2 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-trace-binding-v0-3-2
```

Expected output ends with:

```
PASS: silver trace binding package built at /tmp/proofrail-silver-trace-binding-v0.3.2
  trace_binding_report_id: proofrail-trace-binding-report-demo-001
  adapter: adapter/observability-trace-simulated-v0.2.6.json
  trace_events.event_count: 8
  binding_set.binding_count: 9
  binding_summary: bound=5 bound_with_warning=1 trace_gap_detected=1 out_of_scope=2
```

The runner performs nine steps in this order:

1. Structural pre-check: refuse if the adapter declares
   `trust_boundary.source_is_trust_authority` ≠ exactly `false`
   (runner-only reason `adapter_validation_failed`).
2. Subprocess-invoke the unchanged v0.2.6 adapter validator (same
   runner-only reason on failure).
3. Validate the trace events JSONL (runner-only reason
   `trace_events_validation_failed`).
4. Validate the binding set JSON, including the time-window and the
   cross-check that non-gap rows resolve to a matching event with all
   `required_*` fields equal (runner-only reason
   `trace_binding_set_validation_failed`).
5. Stage the package directory.
6. Derive `silver-trace-binding-report.json` from the inputs (counts
   computed from `bindings[].binding_status`, never hand-authored).
7. Build `silver-trace-binding-manifest.json` with exactly four
   subjects in fixed order.
8. If `--self-validate`, run the v0.3.2 verifier against the staged
   manifest (runner-only reason
   `trace_binding_self_validation_failed`).
9. `os.replace()` the staging directory into `--output-dir`. On any
   prior failure, the staging directory is removed and the destination
   is untouched.

## Step 2 — Verify the trace binding package

```bash
python3 tools/silver/verify_silver_trace_binding_v0_1_0.py \
  --manifest /tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-manifest.json
```

Expected output:

```
PASS: Silver trace binding valid (proofrail-trace-binding-report-demo-001)
```

The verifier performs the following ordered checks. Each check maps to
a specific stable failure reason; OR-accepting adjacent reasons is
disallowed.

| # | Check                                                                              | Failure reason on disagreement       |
|---|------------------------------------------------------------------------------------|--------------------------------------|
| 1 | Parse and structurally validate the manifest                                       | `invalid_trace_binding_manifest`     |
| 2 | Subject path traversal (BEFORE exact path equality)                                | `trace_subject_path_traversal`       |
| 3 | Exact subject path + role equality against `SUBJECT_ORDER`                         | `invalid_trace_binding_manifest`     |
| 4 | Subject file existence                                                             | `trace_subject_file_missing`         |
| 5 | Subject SHA-256 + size recomputation                                               | `trace_subject_hash_mismatch`        |
| 6 | Adapter structural pre-check (Amendment 1, BEFORE v0.2.6 validator subprocess)     | `trace_source_marked_authority`      |
| 7 | v0.2.6 adapter validator subprocess                                                | `trace_adapter_invalid`              |
| 8 | Parse trace events; field/enum checks                                              | `trace_events_invalid`               |
| 9 | Unique `event_id` and unique `(trace_id, span_id)`                                 | `trace_event_duplicate`              |
| 10 | Strict `(event_time, event_id)` ordering                                          | `trace_event_time_order_invalid`     |
| 11 | Parse binding set; field/enum checks                                              | `trace_binding_set_invalid`          |
| 12 | Unique `claim_id`                                                                 | `trace_binding_duplicate`            |
| 13 | Non-gap rows: referenced event exists                                             | `trace_binding_event_missing`        |
| 14 | Non-gap rows: `required_*` fields equal resolved event fields                     | `trace_binding_field_mismatch`       |
| 15 | Non-gap rows: event_time inside `trace_time_window`                               | `trace_binding_time_window_mismatch` |
| 16 | Parse report; field/enum checks                                                   | `trace_report_invalid`               |
| 17 | Cross-check report hashes / counts / time-window / ids vs manifest and inputs     | `trace_report_binding_mismatch`      |
| 18 | Warning/gap/out-of-scope downgrade (Amendment 2, BEFORE generic status mismatch)  | `trace_warning_downgrade`            |
| 19 | Per-row re-derivation equality                                                    | `trace_report_status_mismatch`       |
| 20 | Re-compute `binding_summary` counts                                               | `trace_report_count_mismatch`        |
| 21 | Overclaim scan OUTSIDE `scope_limitations` / `non_claims`                         | `trace_overclaim`                    |
| 22 | `scope_limitations` non-empty / non-blank (manifest, binding set, report)         | `trace_limitations_missing`          |
| 23 | `non_claims` non-empty / non-blank (manifest, binding set, report)                | `trace_non_claims_missing`           |

## Step 3 — Inspect the report

```bash
python3 -c "import json; d = json.load(open('/tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-report.json')); print(json.dumps(d['binding_summary'], indent=2))"
```

Expected output:

```json
{
  "bound_count": 5,
  "bound_with_warning_count": 1,
  "out_of_scope_count": 2,
  "source_is_trust_authority": false,
  "trace_gap_detected_count": 1
}
```

## Step 4 — Run the regression test

```bash
make verify-silver-trace-binding-v0-3-2
```

This runs `tests/test_silver_trace_binding_v0_3_2.sh`, which exercises
every stable verifier failure reason (22) and every runner-only
refusal reason (4). The test prints a final stable PASS line:

```
PASS: tests/test_silver_trace_binding_v0_3_2.sh (4 positive + 22 verifier + 4 runner-only = 30 top-level exercises; scoped snapshot identical)
```

## What the demo intentionally does **not** do

- It does not query any external observability, SIEM, GRC, gateway,
  policy-engine, or ticketing service.
- It does not assert that the observability substrate is a trust
  authority.
- It does not certify OpenTelemetry conformance.
- It does not authorize production reliance, regulator acceptance,
  auditor acceptance, or legal acceptance.
- It does not extend the substance of any earlier-release Silver
  evidence.
- It does not resolve or cross-validate `source_event_ref` strings
  against any external package; v0.3.2 treats those as opaque labels.
