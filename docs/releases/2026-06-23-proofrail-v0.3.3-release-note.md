# ProofRail v0.3.3 - Silver Adapter Pilot Package

Release date: 2026-06-23

Git tag: `v0.3.3`

ProofRail v0.3.3 adds a Silver Adapter Pilot Package.

v0.3.2 introduced trace binding: a way to bind protected-action claims to trace-shaped evidence without claiming that traces are themselves trust authorities. v0.3.3 adds the next pre-Gold step: a deterministic local adapter pilot that takes simulated external observability evidence, normalizes it into ProofRail trace-binding evidence, and packages the result for independent verification.

The narrow claim is:

> ProofRail can verify whether a local adapter pilot correctly normalized simulated external trace evidence into ProofRail trace-binding evidence, without treating the source system as a trust authority, proving runtime truth, claiming OpenTelemetry conformance, or entering Gold governance.

## What Changed

This release adds the Silver Adapter Pilot Package.

The package demonstrates a constrained adapter flow:

- copy and validate a v0.2.6 evidence source adapter descriptor;
- copy a static OTel-shaped source export fixture;
- copy and validate a deterministic normalization map;
- derive ProofRail v0.3.2-shaped trace events;
- run the unchanged v0.3.2 trace-binding builder and verifier over the normalized output;
- emit an adapter pilot report;
- emit a hash-anchored adapter pilot manifest.

The adapter pilot is intentionally local and deterministic. It is a substrate-neutral evidence packaging exercise, not a live integration.

## New Artifacts

Added schemas:

- `schemas/silver-adapter-pilot-manifest-v0.1.0.md`
- `schemas/silver-adapter-pilot-normalization-map-v0.1.0.md`
- `schemas/silver-adapter-pilot-report-v0.1.0.md`
- `schemas/silver-adapter-pilot-source-export-v0.1.0.md`

Added documentation:

- `docs/silver/silver-adapter-pilot-package-v0.3.3.md`
- `demos/silver-demo-010-adapter-pilot-package/README.md`
- `demos/silver-demo-010-adapter-pilot-package/demo-walkthrough.md`
- `fixtures/silver-adapter-pilot-package-v0.3.3/README.md`

Added fixture data:

- `fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl`
- `fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json`

Added tools:

- `tools/silver/build_silver_adapter_pilot_v0_1_0.py`
- `tools/silver/verify_silver_adapter_pilot_v0_1_0.py`

Added test:

- `tests/test_silver_adapter_pilot_v0_3_3.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`
- `docs/gold/gold-boundary-v0.2.5.md`

## Adapter Pilot Package

The generated package contains:

```text
adapter/
source/
normalization/
normalized/
trace-binding/
silver-adapter-pilot-report.json
silver-adapter-pilot-manifest.json
```

The manifest hashes seven subjects in fixed order:

- adapter descriptor;
- source export;
- normalization map;
- normalized trace events;
- normalized trace claim bindings;
- nested v0.3.2 trace-binding manifest;
- adapter pilot report.

The nested trace-binding package remains governed by the unchanged v0.3.2 verifier. v0.3.3 verifies the adapter-pilot layer around it.

## Runner

Example:

```bash
make run-silver-adapter-pilot-v0-3-3
```

The runner:

- validates the copied v0.2.6 evidence source adapter descriptor;
- rejects an adapter that marks the source as a trust authority;
- parses a static OTel-shaped source export fixture;
- applies a deterministic field-level normalization map;
- writes normalized ProofRail trace events;
- copies the trace claim binding set;
- invokes the unchanged v0.3.2 trace-binding builder;
- emits `silver-adapter-pilot-report.json`;
- emits `silver-adapter-pilot-manifest.json`;
- optionally self-validates before atomic publish.

Refused runs leave no partial output package behind.

## Verifier

Example:

```bash
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \
  --manifest /tmp/proofrail-silver-adapter-pilot-demo-v0.3.3/silver-adapter-pilot-manifest.json
```

The verifier checks:

- manifest structure;
- subject path safety;
- subject existence;
- subject hashes;
- adapter validity;
- adapter source-is-not-trust-authority boundary;
- source export structure;
- duplicate source event detection;
- source export ordering;
- normalization map structure;
- required normalization fields;
- normalized trace parseability;
- normalized trace re-derivation;
- nested v0.3.2 trace-binding validity;
- nested trace-binding hash consistency;
- adapter pilot report structure;
- report-to-manifest binding;
- report counts;
- required claims;
- claim status;
- evidence reference safety;
- limitations;
- non-claims;
- overclaim language.

Successful verification prints:

```text
PASS: Silver adapter pilot valid (proofrail-adapter-pilot-report-demo-001)
```

## Stable Failure Reasons

The v0.3.3 verifier exposes 24 stable failure reasons:

- `invalid_adapter_pilot_manifest`
- `adapter_pilot_subject_file_missing`
- `adapter_pilot_subject_path_traversal`
- `adapter_pilot_subject_hash_mismatch`
- `adapter_pilot_adapter_invalid`
- `adapter_pilot_source_marked_authority`
- `source_export_invalid`
- `source_export_duplicate`
- `source_export_time_order_invalid`
- `normalization_map_invalid`
- `normalization_required_field_missing`
- `normalized_trace_invalid`
- `normalized_trace_mismatch`
- `nested_trace_binding_invalid`
- `nested_trace_binding_mismatch`
- `adapter_pilot_report_invalid`
- `adapter_pilot_report_binding_mismatch`
- `adapter_pilot_report_count_mismatch`
- `adapter_pilot_claim_missing`
- `adapter_pilot_claim_failed`
- `adapter_pilot_evidence_ref_invalid`
- `adapter_pilot_overclaim`
- `adapter_pilot_limitations_missing`
- `adapter_pilot_non_claims_missing`

The runner also has refusal reasons for build-time failures:

- `adapter_validation_failed`
- `source_export_validation_failed`
- `normalization_map_validation_failed`
- `binding_set_validation_failed`
- `nested_trace_binding_generation_failed`
- `adapter_pilot_self_validation_failed`

## Regression Coverage

The v0.3.3 regression test covers 36 exercises:

- pristine adapter pilot package generation;
- independent adapter pilot verification;
- manifest layout checks;
- report content checks;
- all 24 stable verifier failure reasons;
- both `..` and absolute-path traversal cases;
- all six runner-only refusal reasons;
- atomic publish behavior;
- staging cleanup on refused runs;
- scoped mutation checks.

Primary commands:

```bash
make run-silver-adapter-pilot-v0-3-3
make verify-silver-adapter-pilot-v0-3-3
make verify-silver-trace-binding-v0-3-2
make verify-silver-evidence-source-adapter-v0-2-6
make verify-silver-all
python3 -m pytest tests/test_proofrail_claim.py
git diff --check
```

Reported verification:

- `make run-silver-adapter-pilot-v0-3-3` passed;
- `make verify-silver-adapter-pilot-v0-3-3` passed with 36 exercises;
- `make verify-silver-trace-binding-v0-3-2` passed;
- `make verify-silver-evidence-source-adapter-v0-2-6` passed;
- `make verify-silver-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed;
- `git diff --check` passed.

## What This Release Does Not Claim

ProofRail v0.3.3 does not claim:

- Gold certification;
- Gold conformance;
- regulator approval;
- auditor approval;
- legal acceptance;
- production integration;
- live gateway integration;
- live observability integration;
- OpenTelemetry conformance;
- runtime truth;
- semantic equivalence between source telemetry and protected-action authority;
- that any source system is a trust authority;
- that normalized evidence proves a protected action was actually controlled;
- transferred reliance;
- governed acceptance.

The source export fixture is static and OTel-shaped. The normalization map proves deterministic field-level mapping for this local fixture. It does not prove that a live OpenTelemetry collector, gateway, SIEM, GRC platform, or policy engine emitted equivalent evidence.

## What Comes Next

v0.3.3 strengthens ProofRail's position as the portable evidence/reliance layer above gateways, observability tools, policy engines, SIEMs, and AI GRC platforms.

The next work should continue toward Gold without crossing the certification boundary prematurely:

```text
v0.3.3:
  local adapter pilot package over simulated external trace evidence

Next:
  challenge and withdrawal record primitives

Later:
  relying-party policy pack, control crosswalk, protected action catalog, registry lite

Then:
  minimal Gold governed reliance demo
```

The through-line remains: external systems may produce events, traces, decisions, or dashboards; ProofRail asks whether protected-action claims survive independent verification.

## Summary

ProofRail v0.3.3 introduces a Silver Adapter Pilot Package that normalizes simulated external trace evidence into ProofRail trace-binding evidence and packages it for independent verification.

It does not claim live integration, OpenTelemetry conformance, runtime truth, production authorization, transferred reliance, or Gold governance.
