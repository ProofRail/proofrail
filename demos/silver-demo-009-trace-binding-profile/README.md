# Silver Demo 009 — Trace Binding Profile (v0.3.2)

This demo is the deterministic, local Silver trace binding package
that ProofRail v0.3.2 derives from:

- the unchanged v0.2.6 simulated observability-trace adapter
  descriptor (`examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json`);
- the committed v0.3.2 trace event fixture
  (`fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl`);
- the committed v0.3.2 trace claim binding set
  (`fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json`).

It answers a narrow question:

> Can protected-action claims be bound to concrete trace events whose
> trace IDs, span IDs, action IDs, principal IDs, decision outcomes,
> timestamps, and hashes can be independently re-derived by a Silver
> reviewer — without claiming that the observability substrate is
> authoritative, that runtime truth is proven, that OpenTelemetry
> conformance has been established, or that Gold governance has been
> executed?

It does **not** answer:

- Did a real production trace system observe these events?
- Is the trace source authoritative?
- Is this OpenTelemetry conformance?
- Does this prove runtime truth?
- Does this satisfy any external control framework?
- Is the handoff Gold-ready?
- Should a downstream relying party reuse this evidence?

## What the demo does

1. Validates the v0.2.6 observability-trace adapter descriptor with
   the unchanged v0.2.6 adapter validator
   (`tools/silver/validate_evidence_source_adapter_v0_1_0.py`), via
   subprocess. Refuses any adapter whose
   `trust_boundary.source_is_trust_authority` is not exactly `false`.
2. Parses the 8-event JSONL trace fixture, enforcing strict
   `(event_time, event_id)` ordering, unique `event_id`, unique
   `(trace_id, span_id)`, and a closed `decision` enum.
3. Parses the 9-row binding set, enforcing closed
   `expected_binding_status` and `required_decision` enums, unique
   `claim_id`, and the time-window constraint on every non-gap row.
4. Cross-checks every non-gap binding row against the resolved trace
   event (event existence + `required_*` field equality + event_time
   inside `trace_time_window`).
5. Derives `silver-trace-binding-report.json` deterministically from
   the trace events and binding set; forces
   `trace_source.source_is_trust_authority` and
   `binding_summary.source_is_trust_authority` to exactly `false`.
6. Emits `silver-trace-binding-manifest.json` with exactly four
   subjects in fixed order: adapter / trace events / binding set /
   trace binding report.
7. Self-validates the staged package with the v0.3.2 verifier before
   the atomic `os.replace()` publish, so failed verification leaves no
   partial output.

## Commands

```bash
make run-silver-trace-binding-v0-3-2
make verify-silver-trace-binding-v0-3-2
```

The `run-` target builds the package into
`/tmp/proofrail-silver-trace-binding-v0.3.2/` with `--self-validate`,
then runs the v0.3.2 verifier against the published manifest.

The `verify-silver-trace-binding-v0-3-2` target runs the dedicated
regression test, which exercises every stable verifier failure reason
and every runner-only refusal reason.

## Trace binding package layout

```
/tmp/proofrail-silver-trace-binding-v0.3.2/
├── adapter/
│   └── observability-trace-simulated-v0.2.6.json     (subject [0])
├── trace-events.jsonl                                (subject [1])
├── trace-claim-bindings.json                         (subject [2])
├── silver-trace-binding-report.json                  (subject [3])
└── silver-trace-binding-manifest.json                (4-subject anchor)
```

## Binding composition

```
bound                            : 5  (events 001/002/003/006/008)
bound_with_warning               : 1  (event 007 — bypass observed)
out_of_scope_for_trace_binding   : 2  (events 004/005 — referenced events
                                       still exist and required fields match)
trace_gap_detected               : 1  (claim_id trace_binding_known_missing_event;
                                       references TRACE-EVT-099 which is
                                       intentionally absent from the fixture)
```

Only `trace_gap_detected` rows are permitted to reference an absent
trace event. `bound_with_warning` and `out_of_scope_for_trace_binding`
rows still require their referenced event to exist and to match all
`required_*` fields. This keeps the gap-preservation path distinct
from the binding-error paths.

## Re-derivation guarantee

Every field in `silver-trace-binding-report.json` is re-derived
deterministically from the trace event fixture and the binding set.
The v0.3.2 verifier independently re-derives the same fields and
rejects any disagreement under one of 22 stable failure reasons. Four
additional refusal reasons are emitted only by the runner.

Warning, gap, and out-of-scope rows cannot be silently downgraded to
`bound`. The verifier checks `trace_warning_downgrade` BEFORE the
generic `trace_report_status_mismatch`, so a downgrade is always
attributed to the more specific reason.

The adapter trust-authority pre-check runs BEFORE the generic v0.2.6
adapter validator subprocess, so a tampered adapter with
`source_is_trust_authority: true` is always attributed to
`trace_source_marked_authority`, not collapsed into the generic
`trace_adapter_invalid`.

## Non-claims

- The trace binding package is not a Gold certificate.
- The trace binding package is not a Gold readiness assessment.
- The trace binding package is not OpenTelemetry conformance.
- The trace binding package does not make the observability substrate
  authoritative.
- The trace binding package does not assert that runtime behaviour
  occurred exactly as described.
- The trace binding package is not regulator approval, auditor
  approval, legal acceptance, compliance certification, or production
  authorization.
- The trace binding package does not transfer reliance to any
  downstream party.
- The trace binding package does not adjudicate any challenge or
  revocation signal.
- The simulated observability-trace adapter is an evidence-source
  descriptor, not a trust authority.
- `source_event_ref` on each event (e.g. `gateway-event:EVT-002`) is
  an opaque labeled string; v0.3.2 does not cross-validate it against
  any external package.
