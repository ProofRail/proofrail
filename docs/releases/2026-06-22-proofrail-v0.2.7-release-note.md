# ProofRail v0.2.7 - Composed Silver Demo Over Simulated Gateway Evidence

Release date: 2026-06-22

Git tag: `v0.2.7`

ProofRail v0.2.7 adds a composed Silver demo over simulated external gateway evidence.

v0.2.6 defined Evidence Source Adapter descriptors. v0.2.7 demonstrates that idea in motion: a simulated gateway adapter descriptor and a static JSONL gateway event fixture are composed into a hash-anchored ProofRail evidence package, then independently verified.

The narrow claim is:

> ProofRail can verify a protected-action evidence package whose source evidence is produced by a simulated external gateway substrate, while preserving the boundary that the gateway is an evidence source, not a trust authority.

## What Changed

This release adds a deterministic composed gateway evidence demo.

The demo uses:

- the v0.2.6 simulated gateway adapter descriptor;
- a static nine-event simulated gateway JSONL fixture;
- a composer that packages source evidence into a ProofRail-shaped composed evidence package;
- a verifier that independently re-derives claims from the copied adapter and source events.

The simulated gateway event fixture covers:

- harmless message observation;
- authorized `payment.release`;
- authorized `vendor.approve`;
- unauthorized delegation laundering;
- bypass attempt observation;
- out-of-scope `data.export`;
- out-of-scope `deploy.change`;
- revocation marker;
- denied vendor approval after revocation.

The demo does not execute protected actions.

## New Artifacts

Added schemas:

- `schemas/silver-simulated-gateway-evidence-event-v0.1.0.md`
- `schemas/silver-composed-gateway-evidence-report-v0.1.0.md`
- `schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md`

Added documentation:

- `docs/silver/silver-composed-gateway-evidence-demo-v0.2.7.md`
- `demos/silver-demo-004-composed-gateway-evidence/README.md`
- `demos/silver-demo-004-composed-gateway-evidence/demo-walkthrough.md`
- `fixtures/silver-composed-gateway-evidence-v0.2.7/README.md`

Added fixture:

- `fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`

Added tools:

- `tools/silver/compose_gateway_evidence_demo_v0_1_0.py`
- `tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`

Added test:

- `tests/test_silver_composed_gateway_evidence_v0_2_7.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`

## Composer

The composer builds a runtime composed evidence package from the committed demo docs, the v0.2.6 simulated gateway adapter descriptor, and the v0.2.7 simulated gateway event fixture.

Example:

```bash
python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
  --demo-root demos/silver-demo-004-composed-gateway-evidence \
  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
  --generated-at 2026-06-22T00:00:00Z \
  --force
```

The composer emits:

- `README.md`
- `demo-walkthrough.md`
- `adapter/gateway-mcp-simulated-v0.2.6.json`
- `source/gateway-events.jsonl`
- `composed-gateway-evidence-report.json`
- `composed-gateway-evidence-manifest.json`

The manifest includes five deterministic subjects plus a `composition` block that records:

- `source_type: "gateway"`
- adapter descriptor path;
- source events path;
- composed report path;
- `source_is_trust_authority: false`

The composer also invokes the unchanged v0.2.6 adapter validator before composing the package.

## Verifier

The verifier checks the composed gateway evidence package from the manifest entry point.

Example:

```bash
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \
  --manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json
```

The verifier checks:

- manifest structure;
- deterministic subject order;
- subject path safety;
- subject existence;
- SHA-256 hashes;
- the manifest `composition` block;
- copied adapter validity through the v0.2.6 adapter validator;
- that the adapter source type is `gateway`;
- that the gateway is not a trust authority;
- simulated gateway event structure;
- required scenario event coverage;
- protected action IDs;
- bypass semantics;
- revocation semantics;
- normalized report structure;
- all required composed claims;
- evidence references;
- non-execution.

The verifier re-derives every required claim from the copied adapter and JSONL event stream. It does not trust the normalized report by itself.

## Required Claims

The composed report contains ten required claims:

- `gateway_source_described_by_adapter`
- `gateway_source_not_trust_authority`
- `gateway_events_normalized`
- `protected_actions_require_scoped_authority`
- `unauthorized_delegation_fails`
- `bypass_attempts_observed_or_blocked`
- `revoked_authority_fails`
- `out_of_scope_actions_fail`
- `source_evidence_hash_verifiable`
- `no_protected_actions_executed`

Each claim must have `status: "pass"` and safe package-local evidence references. The verifier independently re-derives those claims from the source events and adapter metadata.

## Stable Failure Reasons

The v0.2.7 verifier exposes stable top-level failure reasons:

- `invalid_composed_gateway_manifest`
- `composed_subject_file_missing`
- `composed_subject_path_traversal`
- `composed_subject_hash_mismatch`
- `adapter_invalid`
- `adapter_not_gateway_source`
- `source_event_invalid`
- `source_event_missing`
- `source_event_duplicate`
- `gateway_protected_action_mismatch`
- `gateway_decision_mismatch`
- `gateway_bypass_mismatch`
- `gateway_revocation_mismatch`
- `normalized_report_invalid`
- `normalized_claim_missing`
- `normalized_claim_failed`
- `normalized_evidence_ref_invalid`
- `execution_violation`

## Regression Coverage

The v0.2.7 regression test covers 28 cases and exercises all 18 stable verifier failure reasons.

Coverage includes:

- happy-path composition;
- happy-path verification;
- manifest subject order;
- required claim IDs;
- non-execution;
- source event hash verification;
- hash mismatch detection;
- missing subject detection;
- subject path traversal;
- malformed manifest detection;
- invalid adapter detection;
- non-gateway adapter rejection;
- malformed JSONL handling without Python tracebacks;
- missing source event detection;
- duplicate source event detection;
- protected action mismatch;
- decision mismatch;
- bypass mismatch;
- revocation mismatch;
- invalid normalized report;
- missing normalized claim;
- failed normalized claim;
- invalid evidence reference path;
- wrong-but-valid evidence reference;
- execution violation;
- scoped mutation check for committed v0.2.7 files.

Primary commands:

```bash
make run-silver-composed-gateway-demo-v0-2-7
make verify-silver-composed-gateway-demo-v0-2-7
make verify-silver-all
git diff --check
```

The implementation run reported `verify-silver-all` passing, `git diff --check` clean, and `tests/test_proofrail_claim.py` passing with 27 tests.

## Why This Matters

v0.2.7 is the first ProofRail demo showing source-neutral evidence composition over a non-native substrate.

The important behavior is not that the gateway is trusted. It is not.

The important behavior is that gateway-like source evidence can be:

- described by an adapter;
- copied into a package;
- hash-anchored;
- normalized into ProofRail-relevant claims;
- independently re-checked;
- rejected when source evidence, normalized claims, or references do not line up.

This supports the broader ProofRail positioning:

> Gateways may enforce, observability may record, and governance tools may manage workflows; ProofRail defines what evidence must survive independent verification before a protected-action claim can be relied on.

## What This Release Does Not Claim

ProofRail v0.2.7 does not claim:

- real gateway integration;
- real MCP gateway security;
- live gateway enforcement;
- live ingestion from APIs, logs, traces, SaaS products, or cloud systems;
- log authenticity;
- production assurance;
- protected action execution;
- real actuator integration;
- compliance;
- Gold conformance;
- Gold certification;
- third-party certification;
- regulator approval;
- governed institutional acceptance;
- relying-party acceptance records.

The correct boundary is:

> ProofRail v0.2.7 demonstrates substrate-neutral evidence composition. It does not integrate with a real gateway or certify gateway enforcement.

And:

> The simulated gateway is an evidence source, not a trust authority.

## What Comes Next

v0.2.7 demonstrates composed Silver evidence over simulated gateway evidence.

The next planned step is a Relying Party Acceptance Record:

- this relying party;
- under this policy version;
- reviewed these Silver reports and evidence packages;
- accepted or rejected them for this purpose;
- with these exceptions;
- with these revocation checks;
- under this challenge or review window.

That should remain a Gold precursor, not a Gold certificate.

The intended progression is:

```text
v0.2.6:
  evidence source adapter profile

v0.2.7:
  composed Silver demo over simulated gateway evidence

v0.2.8:
  relying-party acceptance record

v0.2.9:
  revocation/challenge drill

v0.3.0:
  Silver-to-Gold planning package, still no certification claim
```

## Summary

ProofRail v0.2.7 composes Silver evidence over a simulated gateway evidence source.

It does not ask the relying party to trust the gateway. It asks whether gateway-sourced protected-action claims survive adapter validation, hash checks, claim re-derivation, evidence-reference checks, and explicit non-execution constraints.
