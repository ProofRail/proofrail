# Silver Trace Binding Profile v0.3.2 — Fixture

Deterministic local fixture for the ProofRail v0.3.2 trace binding
profile. Used by `tools/silver/build_silver_trace_binding_v0_1_0.py`
and `tools/silver/verify_silver_trace_binding_v0_1_0.py`.

## Files

```
trace-events.jsonl           — 8 deterministic trace events
trace-claim-bindings.json    — 9 binding rows over those events
```

The runner additionally consumes the v0.2.6 simulated observability
trace adapter descriptor from
`examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json`
(unmodified) and copies it into the trace binding package's
`adapter/` subdirectory.

## Trace event composition

8 events, sorted strictly by `(event_time, event_id)` ascending,
all inside the binding-set time window
`2026-06-22T00:00:00Z` → `2026-06-22T00:10:00Z`:

| event_id                                       | decision | scenario                              |
| ---------------------------------------------- | -------- | ------------------------------------- |
| TRACE-EVT-001-payment-release-allowed          | allow    | payment.release authorized            |
| TRACE-EVT-002-vendor-approve-allowed           | allow    | vendor.approve authorized             |
| TRACE-EVT-003-payment-release-deny-revoked     | deny     | payment.release after revocation      |
| TRACE-EVT-004-data-export-deny-out-of-scope    | deny     | data.export out of scope              |
| TRACE-EVT-005-deploy-change-deny-out-of-scope  | deny     | deploy.change out of scope            |
| TRACE-EVT-006-vendor-approve-deny-revoked      | deny     | vendor.approve after revocation       |
| TRACE-EVT-007-bypass-attempt-observed          | observe  | bypass attempt observed (not blocked) |
| TRACE-EVT-008-bypass-attempt-blocked           | block    | bypass attempt blocked                |

## Binding composition

9 bindings, distribution:

```
bound                            : 5  (events 001/002/003/006/008)
bound_with_warning               : 1  (event 007 — bypass observed)
out_of_scope_for_trace_binding   : 2  (events 004/005 — referenced events
                                       still exist and match required fields)
trace_gap_detected               : 1  (claim_id trace_binding_known_missing_event;
                                       references TRACE-EVT-099 which is
                                       intentionally absent from the fixture)
```

## Non-claims

- This fixture is not a real production trace.
- This fixture is not OpenTelemetry conformance evidence.
- This fixture does not make any observability source authoritative.
- This fixture does not authorize execution, claim regulator
  approval, claim auditor approval, or claim legal acceptance.
- `source_event_ref` strings on each event (e.g.
  `gateway-event:EVT-002`) are opaque labels; v0.3.2 does not
  cross-validate them against any external package.
