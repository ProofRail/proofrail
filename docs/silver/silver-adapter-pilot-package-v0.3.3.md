# Silver Adapter Pilot Package — v0.3.3

**Status:** Draft / ProofRail v0.3.3
**Release thesis:** ProofRail v0.3.3 pilots a local external-evidence
adapter flow that normalizes an OpenTelemetry-shaped local source-export
fixture into the v0.3.2 trace-binding inputs, showing that an
independent Silver reviewer can hash-verify every input, re-derive every
normalized event byte-identically, and re-invoke the unchanged v0.3.2
verifier on the nested manifest — without claiming OpenTelemetry
conformance, vendor integration, source authority, or runtime truth.

---

## v0.3.3 thesis

> A reviewer can verify that an OpenTelemetry-shaped local source-export
> fixture has been normalized into a ProofRail v0.3.2 trace-binding
> input set under a declarative, evidence-only mapping, while preserving
> the boundary that the source system is not a trust authority,
> OpenTelemetry conformance is not asserted, vendor integration is not
> asserted, and runtime truth is not proved.

## Adapter pilot boundary

> An adapter pilot package is **not** proof of OpenTelemetry conformance,
> vendor integration, source authority, or runtime truth. It is a
> deterministic local evidence artifact showing that an
> OpenTelemetry-shaped local source-export fixture has been normalized
> into ProofRail v0.3.2 trace-binding inputs under a declarative mapping
> whose every input, output, and intermediate artifact is hash-anchored
> and independently re-derivable.

v0.3.3 answers:

```
Can a local OpenTelemetry-shaped trace export be normalized into
  ProofRail v0.3.2 trace events under a declarative mapping?
Can a verifier independently re-derive every normalized event byte for
  byte from the source export and the mapping?
Can the verifier hash-cross-check the nested v0.3.2 manifest against
  the outer adapter pilot manifest?
Can the verifier re-invoke the unchanged v0.3.2 verifier on the nested
  manifest, without modifying v0.3.2?
Can the verifier reject tampered adapter descriptors, tampered source
  exports, tampered mappings, tampered normalized outputs, tampered
  nested manifests, tampered reports, missing/failed required claims,
  unsafe evidence refs, empty limitations / non-claims, and overclaims?
```

v0.3.3 does **not** answer:

```
Did a real production OpenTelemetry collector emit these spans?
Is the simulated trace source authoritative?
Is this OpenTelemetry conformance?
Is this a vendor certification?
Does this prove runtime truth?
Does this satisfy a control framework?
Is the handoff Gold-ready?
Should a downstream relying party reuse this evidence?
```

---

## Schemas

Four new v0.1.0 schemas ship with v0.3.3:

```
schemas/silver-adapter-pilot-source-export-v0.1.0.md
schemas/silver-adapter-pilot-normalization-map-v0.1.0.md
schemas/silver-adapter-pilot-report-v0.1.0.md
schemas/silver-adapter-pilot-manifest-v0.1.0.md
```

### Source export (`proofrail.simulated_otel_trace_export.v0.1`)

JSONL, one OpenTelemetry-shaped envelope per line, sorted strictly by
`(span.start_time, export_record_id)` ascending. Required top-level
fields per record:

```
export_format, export_record_id, resource, scope, span
```

`export_format` is the closed literal
`"proofrail.simulated_otel_trace_export.v0.1"`; it disclaims real
OpenTelemetry conformance and disclaims any vendor export.

`span` carries `trace_id`, `span_id`, optional `parent_span_id`,
`start_time`, `end_time`, and `attributes`. `span.attributes` is a flat
dict whose keys may contain literal dots
(e.g. `proofrail.event_id`, `proofrail.principal_id`).

Required `span.attributes["proofrail.*"]` fields:

```
proofrail.event_id
proofrail.principal_id
proofrail.protected_action_id
proofrail.decision
proofrail.decision_reason
proofrail.source_event_ref
proofrail.trace_source
```

`proofrail.decision` closed enum: `allow`, `deny`, `observe`, `block`.
Optional `proofrail.counterparty_id` and `proofrail.authority_ref`
attributes are admitted but not required.

`export_record_id` is globally unique within the file; `(trace_id,
span_id)` is globally unique within the file. `source_event_ref` is an
opaque labeled string (e.g. `gateway-event:EVT-002`); v0.3.3 does not
resolve or cross-validate it against any external package.

### Normalization map (`proofrail.silver.adapter_pilot_normalization_map`)

A JSON object containing:

```
document_type, schema_version, proofrail_release,
normalization_map_id, source_format, target_document_type,
field_mappings
```

`source_format` MUST equal
`"proofrail.simulated_otel_trace_export.v0.1"`.
`target_document_type` MUST equal `"proofrail.silver.trace_event"`.

`field_mappings` is a mapping from the v0.3.2 trace-event target field
name to a value expression in a deliberately tiny language:

```
"<source.dot.path>"   — read the value at the dot path inside one
                        source-export record using LONGEST-PREFIX KEY
                        MATCHING at each step. This lets
                        OpenTelemetry-style flat-with-dots attribute
                        keys (e.g. proofrail.event_id) be addressed
                        without quoting.
"constant:<literal>"  — emit the literal string unchanged.
```

No eval, no JSONPath, no callable references. Required v0.3.2 target
fields (`document_type`, `schema_version`, `proofrail_release`,
`event_id`, `trace_id`, `span_id`, `event_time`, `principal_id`,
`protected_action_id`, `decision`, `decision_reason`,
`source_event_ref`, `attributes.proofrail.trace_source`) MUST be
populated for every record; any required-field shortfall is attributed
to the stable verifier reason `normalization_required_field_missing`.

### Adapter pilot report (`proofrail.silver.adapter_pilot_report`)

Derived deterministically from the inputs and the nested v0.3.2
outputs. Fields:

```
adapter_pilot_report_id, generated_at,
adapter_source { source_type, source_is_trust_authority (forced false),
                 adapter_descriptor_path, adapter_descriptor_sha256 },
source_export { source_format, export_path, export_sha256,
                source_record_count },
normalization { normalization_map_path, normalization_map_sha256,
                target_document_type, normalized_events_path,
                normalized_events_sha256, normalized_event_count,
                normalization_status (forced pass),
                normalized_events_match_source (forced true) },
nested_trace_binding { manifest_path, manifest_sha256,
                       report_path, report_sha256,
                       verification_status (forced pass),
                       trace_binding_report_id },
pilot_summary { source_is_trust_authority (forced false),
                runtime_truth_claimed (forced false),
                normalization_status (forced pass),
                normalized_events_match_source (forced true),
                nested_trace_binding_status (forced pass) },
required_claims [...],
scope_limitations [...], non_claims [...]
```

Required claim IDs (status MUST be `pass`):

```
adapter_source_described_by_descriptor
adapter_source_not_trust_authority
source_export_hash_verifiable
normalization_map_hash_verifiable
normalized_events_re_derivable
nested_trace_binding_verified
no_runtime_truth_claimed
```

No field may be hand-authored.

### Adapter pilot manifest (`proofrail.silver.adapter_pilot_manifest`)

Fixed 7-subject SHA-256 anchor in deterministic order:

```
[0] adapter/<filename>                       role: adapter_descriptor
[1] source/source-otel-trace-export.jsonl    role: source_export
[2] normalization/normalization-map.json     role: normalization_map
[3] normalized/trace-events.jsonl            role: normalized_trace_events
[4] normalized/trace-claim-bindings.json     role: normalized_trace_claim_bindings
[5] trace-binding/silver-trace-binding-manifest.json
                                             role: nested_trace_binding_manifest
[6] silver-adapter-pilot-report.json         role: adapter_pilot_report
```

Subject paths are rejected if absolute or if they contain `..`, BEFORE
exact path equality.

---

## Package layout

```
<output-dir>/
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
└── silver-adapter-pilot-manifest.json
```

---

## Runner usage

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

Runner exit codes:

```
0 — success
1 — adapter pilot package refused or self-validation failed
2 — usage or input-file error
```

Runner-only refusal reasons (6):

```
adapter_validation_failed
source_export_validation_failed
normalization_map_validation_failed
binding_set_validation_failed
nested_trace_binding_generation_failed
adapter_pilot_self_validation_failed
```

### Atomic publish (`--force` + `--self-validate`)

The runner stages the entire package under `<output-dir>.staging.<pid>`.
Only AFTER staging build and (if `--self-validate` is supplied)
self-validation both succeed does the runner:

1. Refuse if `<output-dir>` already exists and `--force` was not supplied.
2. If `<output-dir>` exists and `--force` was supplied, remove it.
3. `os.replace()` the staging directory into `<output-dir>`.

Any earlier failure cleans up the staging directory and leaves
`<output-dir>` untouched. A failed run leaves no final directory and no
staging sibling. The Make target is therefore safely repeatable.

---

## Verifier usage

```bash
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \
  --manifest /tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-manifest.json
```

Verifier exit codes:

```
0 — adapter pilot package valid
1 — verification failure (any stable reason below)
2 — usage or input-file error
```

### Stable verifier failure reasons (24)

```
invalid_adapter_pilot_manifest
adapter_pilot_subject_path_traversal
adapter_pilot_subject_file_missing
adapter_pilot_subject_hash_mismatch
adapter_pilot_source_marked_authority
adapter_pilot_adapter_invalid
source_export_invalid
source_export_duplicate
source_export_time_order_invalid
normalization_map_invalid
normalization_required_field_missing
normalized_trace_invalid
normalized_trace_mismatch
nested_trace_binding_invalid
nested_trace_binding_mismatch
adapter_pilot_report_invalid
adapter_pilot_report_binding_mismatch
adapter_pilot_report_count_mismatch
adapter_pilot_claim_missing
adapter_pilot_claim_failed
adapter_pilot_evidence_ref_invalid
adapter_pilot_limitations_missing
adapter_pilot_non_claims_missing
adapter_pilot_overclaim
```

The 6 runner-only refusal codes are NEVER emitted by the verifier.

### Reachability ordering

Four reachability constraints make every stable reason directly
attributable:

- **Path traversal BEFORE exact subject-path equality.** Subjects with
  absolute paths or `..` segments are attributed to
  `adapter_pilot_subject_path_traversal`, never collapsed into
  `invalid_adapter_pilot_manifest`.
- **Adapter trust-authority pre-check BEFORE the v0.2.6 adapter
  validator subprocess.** A tampered adapter declaring
  `trust_boundary.source_is_trust_authority: true` is attributed to
  `adapter_pilot_source_marked_authority`, never collapsed into
  `adapter_pilot_adapter_invalid`.
- **Re-derived normalized bytes equal packaged normalized bytes BEFORE
  the nested v0.3.2 verifier subprocess.** A normalization disagreement
  is attributed to `normalized_trace_mismatch`, never collapsed into
  `nested_trace_binding_invalid`.
- **Nested v0.3.2 verifier subprocess BEFORE the nested-manifest
  hash cross-check.** A fully corrupted nested manifest is attributed
  to `nested_trace_binding_invalid` first; only manifest tampering that
  the unchanged v0.3.2 verifier does not detect surfaces as
  `nested_trace_binding_mismatch`.

Limitations and non-claims emptiness checks are reserved for the
dedicated reasons `adapter_pilot_limitations_missing` and
`adapter_pilot_non_claims_missing`; early structural checks verify
presence/type only.

The overclaim scan runs OUTSIDE the `scope_limitations` /
`non_claims` arrays, so disclaimer text containing forbidden phrases
inside those arrays does not trigger `adapter_pilot_overclaim`.

---

## Regression coverage

`tests/test_silver_adapter_pilot_v0_3_3.sh` runs **36 numbered
exercises**:

- 4 positive (build, verify, inline manifest, inline report)
- 25 verifier-mutation cases (one per ordered check, covering 24 stable
  reasons; the two path-traversal cases — `..` and absolute — both map
  to `adapter_pilot_subject_path_traversal`)
- 6 runner-only refusal cases
- 1 scoped snapshot

The final PASS line states:

```
PASS: tests/test_silver_adapter_pilot_v0_3_3.sh (4 positive + 25 verifier + 6 runner-only + 1 scoped snapshot = 36 numbered exercises; scoped snapshot identical)
```

No reason is OR-accepted; each negative case asserts the exact stable
reason expected.

---

## Non-claims

- v0.3.3 pilots a local external-evidence adapter flow. It does not
  perform a real OpenTelemetry, vendor, observability, SIEM, GRC,
  gateway, policy-engine, or ticketing-system integration.
- An adapter pilot package is not a Gold certificate, OpenTelemetry
  conformance claim, vendor certification, production integration,
  regulator approval, third-party audit, legal acceptance, compliance
  certification, production authorization, or runtime truth guarantee.
- The simulated observability-trace adapter is an evidence-source
  descriptor, not a trust authority.
- The OpenTelemetry-shaped envelope uses the explicit
  `export_format: "proofrail.simulated_otel_trace_export.v0.1"` so the
  fixture cannot be confused with a real vendor export.
- v0.3.3 treats `source_event_ref` strings as opaque labels and carries
  them unchanged through normalization. v0.3.3 does not resolve or
  cross-validate them against any external package.
- v0.3.3 does not extend the substance of any earlier-release Silver
  evidence and does not advance the Gold boundary.

---

## Relationship to earlier and later releases

| Release | Relationship                                                                |
|---------|-----------------------------------------------------------------------------|
| v0.2.6  | v0.3.3 reuses the unmodified simulated observability-trace adapter descriptor and the unmodified v0.2.6 adapter validator (subprocess). |
| v0.2.7  | v0.3.3 does not modify composed gateway evidence semantics. v0.3.3 mirrors the evidence-source-not-trust-authority pattern for OpenTelemetry-shaped trace exports. |
| v0.2.8  | v0.3.3 does not modify relying-party acceptance record semantics. An adapter pilot package is not itself a v0.2.7 evidence package and is not consumed by the v0.2.8 acceptance flow. |
| v0.3.0  | v0.3.3 does not modify handoff semantics. The handoff packager does not (yet) ingest v0.3.3 adapter pilot evidence. |
| v0.3.1  | v0.3.3 does not modify inspection semantics. The handoff inspector does not (yet) ingest v0.3.3 adapter pilot evidence. |
| v0.3.2  | v0.3.3 invokes the unmodified v0.3.2 trace-binding builder and verifier (subprocess). The v0.3.3 manifest hash-cross-checks the nested v0.3.2 manifest. v0.3.2 semantics are unchanged. |
| v0.3.4+ | (planned) Challenge / withdrawal record primitives, relying-party policy pack, control crosswalk, registry-lite, and minimal Gold governed reliance demo all remain out of scope for v0.3.3. |
