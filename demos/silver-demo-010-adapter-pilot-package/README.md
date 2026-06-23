# Silver Demo 010 — Adapter Pilot Package (v0.3.3)

This demo is the deterministic, local Silver adapter pilot package
that ProofRail v0.3.3 derives from:

- the unchanged v0.2.6 simulated observability-trace adapter
  descriptor
  (`examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json`);
- the v0.3.3 OpenTelemetry-shaped local source-export fixture
  (`fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl`);
- the v0.3.3 normalization map
  (`fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json`);
- the unchanged v0.3.2 trace claim binding set
  (`fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json`).

It answers a narrow question:

> Can a local OpenTelemetry-shaped trace export be normalized into
> ProofRail v0.3.2 trace events under a declarative, evidence-only
> mapping such that an independent Silver reviewer can hash-verify
> every input, re-derive every normalized event byte-identically, and
> re-invoke the unchanged v0.3.2 verifier on the nested manifest —
> without claiming that the source system is a trust authority, that
> OpenTelemetry conformance has been established, that vendor
> integration has been performed, or that runtime truth has been
> proved?

It does **not** answer:

- Did a real production OpenTelemetry collector emit these spans?
- Is the simulated trace source authoritative?
- Is this OpenTelemetry conformance?
- Is this a vendor certification?
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
2. Parses the 8-record JSONL source-export fixture, enforcing strict
   `(span.start_time, export_record_id)` ordering, unique
   `export_record_id`, unique `(trace_id, span_id)`, required
   `proofrail.*` attributes, and a closed `decision` enum.
3. Parses the normalization map JSON. The mapping language admits
   only `<source.dot.path>` and `"constant:<literal>"` values; dot
   paths use longest-prefix key match at each step so OpenTelemetry's
   flat-with-dots attribute keys (e.g. `proofrail.event_id`) can be
   addressed without quoting.
4. Applies the map to each source record to derive a deterministic
   list of ProofRail v0.3.2 trace events; refuses if any required
   target field cannot be populated.
5. Subprocess-invokes the unchanged v0.3.2 trace binding builder
   (`tools/silver/build_silver_trace_binding_v0_1_0.py`) against the
   normalized files and the copied adapter descriptor, with
   `--force --self-validate`.
6. Derives `silver-adapter-pilot-report.json` deterministically from
   the inputs and the nested v0.3.2 outputs; pre-bakes the seven
   required claims with `status: pass` and forces every
   `source_is_trust_authority` / `runtime_truth_claimed` flag.
7. Emits `silver-adapter-pilot-manifest.json` with exactly seven
   subjects in fixed order: adapter / source export / normalization
   map / normalized trace events / normalized trace claim bindings /
   nested v0.3.2 manifest / adapter pilot report.
8. If `--self-validate`, runs the v0.3.3 verifier against the staged
   manifest BEFORE the atomic publish; only on a successful staging
   build (and successful self-validation) does the runner remove an
   existing `--output-dir` and `os.replace()` the staging directory
   into place. Failed runs leave no final directory and no staging
   sibling.

## Commands

```bash
make run-silver-adapter-pilot-v0-3-3
make verify-silver-adapter-pilot-v0-3-3
```

The `run-` target builds the package into
`/tmp/proofrail-silver-adapter-pilot-v0.3.3/` with
`--force --self-validate`, then runs the v0.3.3 verifier against the
published manifest.

The `verify-silver-adapter-pilot-v0-3-3` target runs the dedicated
regression test, which exercises every stable verifier failure
reason and every runner-only refusal reason.

## Adapter pilot package layout

```
/tmp/proofrail-silver-adapter-pilot-v0.3.3/
├── adapter/
│   └── observability-trace-simulated-v0.2.6.json     (subject [0])
├── source/
│   └── source-otel-trace-export.jsonl                (subject [1])
├── normalization/
│   └── normalization-map.json                        (subject [2])
├── normalized/
│   ├── trace-events.jsonl                            (subject [3])
│   └── trace-claim-bindings.json                     (subject [4])
├── trace-binding/                                    (nested v0.3.2 package)
│   ├── adapter/observability-trace-simulated-v0.2.6.json
│   ├── trace-events.jsonl
│   ├── trace-claim-bindings.json
│   ├── silver-trace-binding-report.json
│   └── silver-trace-binding-manifest.json            (subject [5])
├── silver-adapter-pilot-report.json                  (subject [6])
└── silver-adapter-pilot-manifest.json                (7-subject anchor)
```

## Source export composition

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

All eight records carry an OpenTelemetry-shaped envelope (`resource`,
`scope`, `span`) and a closed set of `span.attributes["proofrail.*"]`
fields. Records 1, 2, 3, and 6 also carry `counterparty_id` and
`authority_ref`; records 4, 5, 7, and 8 do not. This matches the
optionality of those fields in the v0.3.2 trace event fixture.

## Re-derivation guarantee

The v0.3.3 verifier independently re-derives the normalized
trace-events JSONL from the source export and the normalization map
and compares it byte-for-byte against the packaged file. Any
disagreement is attributed to the stable failure reason
`normalized_trace_mismatch`.

The nested v0.3.2 manifest's subjects[0]/[1]/[2] hashes (adapter /
trace events / binding set) are cross-checked against the v0.3.3
manifest's subjects[0]/[3]/[4] hashes; any disagreement is
attributed to `nested_trace_binding_mismatch`. Verifier-side failure
of the unchanged v0.3.2 verifier against the nested manifest is
attributed to the distinct reason `nested_trace_binding_invalid`.

The adapter trust-authority pre-check runs BEFORE the generic v0.2.6
adapter validator subprocess, so a tampered adapter with
`source_is_trust_authority: true` is always attributed to
`adapter_pilot_source_marked_authority`, not collapsed into
`adapter_pilot_adapter_invalid`.

## Non-claims

- The adapter pilot package is not a Gold certificate.
- The adapter pilot package is not a Gold readiness assessment.
- The adapter pilot package is not OpenTelemetry conformance.
- The adapter pilot package is not a vendor certification.
- The adapter pilot package is not a production integration.
- The adapter pilot package does not make the source system
  authoritative.
- The adapter pilot package does not assert that runtime behaviour
  occurred exactly as described.
- The adapter pilot package is not regulator approval, auditor
  approval, legal acceptance, compliance certification, or production
  authorization.
- The adapter pilot package does not transfer reliance to any
  downstream party.
- The adapter pilot package does not adjudicate any challenge or
  revocation signal.
- The simulated observability-trace adapter is an evidence-source
  descriptor, not a trust authority.
- The OpenTelemetry-shaped envelope uses the explicit
  `export_format: "proofrail.simulated_otel_trace_export.v0.1"` so
  the fixture cannot be confused with a real vendor export.
- `source_event_ref` on each event (e.g. `gateway-event:EVT-002`) is
  an opaque labeled string carried unchanged through normalization;
  v0.3.3 does not cross-validate it against any external package.
