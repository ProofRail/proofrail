# Silver Trace Binding Profile — v0.3.2

**Status:** Draft / ProofRail v0.3.2
**Release thesis:** ProofRail v0.3.2 binds protected-action claims to
deterministic trace evidence, showing that traces can support Silver
review when they are hash-anchored, scoped, and independently checked,
without claiming the observability system is authoritative or that the
traces prove runtime truth by themselves.

---

## v0.3.2 thesis

> A reviewer can verify that protected-action claims reference concrete
> trace events with matching trace IDs, span IDs, action IDs, principal
> IDs, decision outcomes, timestamps, and hashes, while preserving the
> boundary that trace evidence is evidence input, not a trust authority.

## Trace binding boundary

> A trace binding report is **not** proof that runtime behavior
> occurred exactly as described. It is a deterministic local evidence
> artifact showing that protected-action claims are bound to specific
> trace events whose identifiers, decisions, principals, timestamps,
> and hashes can be independently checked.

v0.3.2 answers:

```
Can protected-action claims be bound to concrete trace events?
Can a verifier re-derive that each claim has matching
  trace / span / action / principal / decision fields?
Can trace evidence be hash-anchored without trusting the
  observability substrate?
Can the verifier reject missing events, duplicate events,
  malformed traces, wrong action IDs, wrong decisions,
  stale/out-of-window timestamps, unsafe paths, hash mismatches,
  downgraded warnings, and overclaims?
```

v0.3.2 does **not** answer:

```
Did a real production trace system observe this?
Is the trace source authoritative?
Is this OpenTelemetry conformance?
Does this prove runtime truth?
Does this satisfy a control framework?
Is the handoff Gold-ready?
Should a downstream relying party reuse the evidence?
```

---

## Schemas

Four new v0.1.0 schemas ship with v0.3.2:

```
schemas/silver-trace-event-v0.1.0.md
schemas/silver-trace-claim-binding-set-v0.1.0.md
schemas/silver-trace-binding-report-v0.1.0.md
schemas/silver-trace-binding-manifest-v0.1.0.md
```

### Trace event (`proofrail.silver.trace_event`)

JSONL, one event per line, sorted strictly by `(event_time, event_id)`
ascending. Required fields:

```
document_type, schema_version, proofrail_release,
event_id, trace_id, span_id, event_time, principal_id,
protected_action_id, decision, decision_reason,
source_event_ref, attributes
```

Optional fields: `parent_span_id`, `counterparty_id`, `authority_ref`.

`decision` closed enum: `allow`, `deny`, `observe`, `block`.

`source_event_ref` is an opaque labeled string (e.g.
`gateway-event:EVT-002`). v0.3.2 does not resolve or cross-validate it
against any external package.

OpenTelemetry-style field naming is used for familiarity. ProofRail
does **not** claim OpenTelemetry conformance.

### Trace claim binding set (`proofrail.silver.trace_claim_binding_set`)

A JSON object containing:

```
binding_set_id, trace_time_window {opens_at, closes_at},
bindings [...]
```

Each binding row contains:

```
claim_id, required_trace_event_id, required_trace_id,
required_span_id, required_protected_action_id,
required_principal_id, required_decision,
expected_binding_status
```

`expected_binding_status` closed enum:

```
bound                              — full match expected
bound_with_warning                 — match expected, with reviewer warning
trace_gap_detected                 — referenced event need not exist
out_of_scope_for_trace_binding     — referenced event must exist and match,
                                     binding declared out of scope
```

Only `trace_gap_detected` rows may reference an absent event.
`bound`, `bound_with_warning`, and `out_of_scope_for_trace_binding`
all require the referenced event to exist and to match all `required_*`
fields.

### Trace binding report (`proofrail.silver.trace_binding_report`)

Derived deterministically from the events + binding set. Fields:

```
trace_binding_report_id, generated_at,
trace_source { source_type, source_is_trust_authority (forced false),
               adapter_descriptor_path, adapter_descriptor_sha256 },
trace_events { events_path, events_sha256, event_count, time_window },
binding_set { binding_set_id, bindings_path, bindings_sha256,
              binding_count },
binding_summary { bound_count, bound_with_warning_count,
                  trace_gap_detected_count, out_of_scope_count,
                  source_is_trust_authority (forced false) },
bindings [...],
scope_limitations [...], non_claims [...]
```

`binding_summary` counts are recomputed from `bindings[].binding_status`.
No field may be hand-authored.

### Trace binding manifest (`proofrail.silver.trace_binding_manifest`)

Fixed 4-subject SHA-256 anchor:

```
[0] adapter/<filename>                  role: trace_source_adapter_descriptor
[1] trace-events.jsonl                  role: trace_events
[2] trace-claim-bindings.json           role: trace_claim_binding_set
[3] silver-trace-binding-report.json    role: silver_trace_binding_report
```

Subject paths are rejected if absolute or if they contain `..`, BEFORE
exact path equality.

---

## Package layout

```
<output-dir>/
├── adapter/
│   └── observability-trace-simulated-v0.2.6.json
├── trace-events.jsonl
├── trace-claim-bindings.json
├── silver-trace-binding-report.json
└── silver-trace-binding-manifest.json
```

---

## Runner usage

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

Runner exit codes:

```
0 — success
1 — trace binding refused or self-validation failed
2 — usage or input-file error
```

Runner-only refusal reasons (4):

```
adapter_validation_failed
trace_events_validation_failed
trace_binding_set_validation_failed
trace_binding_self_validation_failed
```

The runner uses a staging directory and `os.replace()` to publish.
Failed runs leave no partial output.

---

## Verifier usage

```bash
python3 tools/silver/verify_silver_trace_binding_v0_1_0.py \
  --manifest /tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-manifest.json
```

Verifier exit codes:

```
0 — trace binding package valid
1 — verification failure (any stable reason below)
2 — usage or input-file error
```

### Stable verifier failure reasons (22)

```
invalid_trace_binding_manifest
trace_subject_path_traversal
trace_subject_file_missing
trace_subject_hash_mismatch
trace_source_marked_authority
trace_adapter_invalid
trace_events_invalid
trace_event_duplicate
trace_event_time_order_invalid
trace_binding_set_invalid
trace_binding_duplicate
trace_binding_event_missing
trace_binding_field_mismatch
trace_binding_time_window_mismatch
trace_report_invalid
trace_report_binding_mismatch
trace_warning_downgrade
trace_report_status_mismatch
trace_report_count_mismatch
trace_limitations_missing
trace_non_claims_missing
trace_overclaim
```

The 4 runner-only refusal codes are NEVER emitted by the verifier.

### Reachability ordering

Two reasons require non-obvious ordering for direct reachability:

- `trace_source_marked_authority` — checked structurally BEFORE the
  v0.2.6 adapter validator subprocess. Otherwise the generic v0.2.6
  validator could collapse the same tamper into `trace_adapter_invalid`.
- `trace_warning_downgrade` — checked BEFORE the generic
  `trace_report_status_mismatch`. A downgrade from `bound_with_warning`,
  `trace_gap_detected`, or `out_of_scope_for_trace_binding` to `bound`
  is always attributed to the more specific downgrade reason.

Path traversal is checked BEFORE exact subject-path equality.
Limitations and non-claims emptiness checks are reserved for the
dedicated reasons `trace_limitations_missing` and
`trace_non_claims_missing`; early structural checks verify
presence/type only.

---

## Regression coverage

`tests/test_silver_trace_binding_v0_3_2.sh` runs **30 top-level
exercises**:

- 4 positive (build + verify + inline manifest + inline report)
- 22 verifier failure-reason cases (one per stable reason)
- 4 runner-only refusal cases

The final PASS line states:

```
PASS: tests/test_silver_trace_binding_v0_3_2.sh (4 positive + 22 verifier + 4 runner-only = 30 top-level exercises; scoped snapshot identical)
```

No reason is OR-accepted; each negative case asserts the exact stable
reason expected.

---

## Non-claims

- v0.3.2 binds protected-action claims to trace evidence for
  independent Silver review. It does not make the observability source
  authoritative, prove runtime truth, certify compliance, or execute
  Gold governance.
- A Silver trace binding report is not a Gold certificate,
  OpenTelemetry conformance claim, production observability claim,
  regulator approval, third-party audit, legal acceptance, compliance
  certification, production authorization, or runtime truth guarantee.
- v0.3.2 treats traces as evidence inputs. It does not decide whether
  a downstream relying party should reuse an acceptance.
- The simulated observability-trace adapter is an evidence-source
  descriptor, not a trust authority.
- `source_event_ref` strings are opaque labels; v0.3.2 does not
  resolve or cross-validate them against any external package.

---

## Relationship to earlier and later releases

| Release | Relationship                                                                |
|---------|-----------------------------------------------------------------------------|
| v0.2.6  | v0.3.2 reuses the unmodified simulated observability-trace adapter and the unmodified v0.2.6 adapter validator. |
| v0.2.7  | v0.2.7 binds gateway events to protected-action claims. v0.3.2 mirrors the evidence-source-not-trust-authority pattern for trace events. |
| v0.3.0  | v0.3.2 does not modify handoff semantics. v0.3.2 emits an additional Silver evidence artifact that later releases may inspect or adapt. |
| v0.3.1  | v0.3.2 does not modify inspection semantics. The handoff inspector does not (yet) ingest v0.3.2 trace binding evidence. |
| v0.3.3  | (planned) Adapter pilot packaging is reserved for v0.3.3. v0.3.2 does not pilot real adapter integrations. |
| v0.3.4+ | (planned) Challenge / withdrawal record primitives, relying-party policy pack, control crosswalk, registry-lite, and minimal Gold governed reliance demo all remain out of scope for v0.3.2. |
