# ProofRail™

Status: public documentation repository and capability demonstrations. Specifications, profiles, sanitized attestations, and examples are published here. Raw deployment evidence and security-sensitive operational details remain private.

ProofRail™ is a vendor-neutral conformance and governance framework for AI agent actuation control. The current public release is [v0.2.3](https://github.com/ProofRail/proofrail/releases/tag/v0.2.3). The main branch includes Silver v0.2.4 deterministic multi-agent attack harness evidence, Silver v0.2.5 multi-agent trust-boundary demo packaging plus the first Gold boundary documentation, Silver v0.2.6 evidence source adapter descriptors, Silver v0.2.7 composed gateway evidence demo, Silver v0.2.8 relying-party acceptance record, Silver v0.2.9 revocation/challenge drill, Silver v0.3.0 acceptance handoff, and Silver v0.3.1 handoff inspector + Gold gap inventory.

As AI agents gain access to tools, APIs, workflows, other AI agents, and enterprise systems, organizations need more than logs or model-side guardrails. They need evidence that protected actions are actually controlled: declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

ProofRail defines that evidence layer.

This project began with Iron-plus, a live reference profile for MCP actuation control, and extended through Bronze, a local-enterprise conformance profile that can be implemented either through ProofRail-native components or through composed stacks using existing gateways, identity providers, observability tools, SIEM/logging systems, and runbooks. Silver adds signed, revocable, reportable, and independently verifiable evidence-package reliance. ProofRail v0.2.2 adds detached verifier output attestations, making Silver verification outputs attributable and tamper-evident while preserving the boundary between Silver evidence-package reliance and Gold governed acceptance. v0.2.3 adds deterministic multi-principal authority fixtures, showing that protected actions can be evaluated against scoped, revocation-aware authority before any simulated actuator path is allowed. v0.2.4 adds a deterministic, scripted multi-principal agent attack harness that drives the unchanged v0.2.3 evaluator across a canonical attack scenario and produces hash-anchored local harness evidence. v0.2.5 packages that harness evidence into a local multi-agent trust-boundary demo with eight deterministically derived claims, hash-anchored package manifest, and the first explicit Gold boundary documentation. v0.2.5 names the Gold boundary. It does not cross it. v0.2.6 adds an evidence source adapter profile: six canonical static JSON descriptors and a local structural validator that declare how evidence sources (gateway, observability trace, SIEM, policy engine, GRC platform, native ProofRail) map their outputs into ProofRail-relevant evidence fields. v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy. v0.2.7 adds a composed Silver demo that pairs the v0.2.6 simulated gateway adapter descriptor with a static JSONL fixture of nine gateway evidence events and deterministically composes a hash-anchored ProofRail evidence package with ten derived claims, independently re-verified by a separate verifier. v0.2.7 demonstrates substrate-neutral evidence composition. It does not integrate with a real gateway or certify gateway enforcement.

## Current Proof Chain

Iron-plus → Composed Bronze → Bronze v0.1.2 checksums → Bronze v0.1.3 bundle manifest → Minimal Silver signed assertion → local revocation → structured verifier report → verification outside the repo source tree → Silver relying-party profile → profile conformance report → verifier output attestation → deterministic authority fixtures → multi-agent attack harness → multi-agent trust-boundary demo → evidence source adapter descriptors → composed gateway evidence demo

ProofRail v0.2.0 defines and validates a local Silver relying-party profile for accepting a signed, revocable, reportable evidence package, with a stronger independent verification mode.  v0.2.2 provides verifier output attestation as attribution and tamper evidence for verifier outputs. It is not certification, regulator approval, production PKI, or Gold governed acceptance. v0.2.3 adds deterministic multi-principal authority fixtures.

The detailed proof chain is:

```text
Bronze v0.1.2
  → evidence checksums

Bronze v0.1.3
  → portable evidence bundle manifest

Silver Signed Bundle Assertion v0.1.0
  → Ed25519 signature over the bundle manifest

Silver Revocation List v0.1.0
  → local relying-party trust withdrawal

Silver Verification Report v0.1.0
  → structured verifier decision artifact

Silver Demo 002
  → independent verifier package operating outside the original source tree

Silver Relying-Party Profile v0.2.0
  → relying-party acceptance profile with base and independent modes

Silver Profile Conformance Report v0.2.1
  → structured conformance decision artifact

Silver Verifier Output Attestation v0.1.0
  → detached, signed verifier output attribution

Silver Multi-Principal Authority Fixture v0.1.0
  → deterministic scoped, delegated, revocation-aware authority evaluation

Silver Multi-Agent Harness Evidence Manifest v0.1.0
  → SHA-256 manifest over a deterministic multi-principal agent attack harness run

Silver Multi-Agent Demo Package Manifest v0.1.0
  → SHA-256 manifest packaging the v0.2.4 harness evidence into a local demo

Silver Multi-Agent Demo Summary v0.1.0
  → eight deterministically derived claims over the packaged harness evidence
```

In practical terms, the repository now demonstrates:

1. a local Bronze claim over a composed MCP-based actuator-control demo;
2. evidence-file integrity verification;
3. a portable bundle manifest that checksums the claim, evidence, schemas, tooling, and documentation;
4. a signed Silver assertion over the Bronze evidence bundle manifest;
5. local relying-party revocation for otherwise valid signed assertions;
6. a structured Silver verification report;
7. independent local verification from an exported verification package;
8. profile-level Silver relying-party conformance validation;
9. detached, signed verifier output attestations.

The primary release verification path is:

```bash
python3 -m pip install -r requirements.txt

make validate-silver-profile-demo-001
make validate-silver-profile-demo-002
make verify-silver-all
```

For the full step-by-step evidence path:

```bash
make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
make silver-demo-001
make verify-silver-demo-001
make verify-silver-revocation-demo-001
make verify-silver-report-demo-001
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
make validate-silver-profile-demo-001
make validate-silver-profile-demo-002
```

This is still a demo-grade framework. It does not claim production certification, public PKI, regulator approval, third-party audit, or Gold governance. It demonstrates the control-evidence mechanics needed to define those later layers.

---

## Current Artifact Family

| Layer | Artifact | Version | Purpose |
|---|---:|---:|---|
| Bronze | Bronze Claim Schema | v0.1.2 | Structured local evidence claim |
| Bronze | Evidence Bundle Manifest | v0.1.3 | Portable evidence-package integrity |
| Silver | Signed Bundle Assertion | v0.1.0 | Issuer signature over bundle manifest |
| Silver | Revocation List | v0.1.0 | Local relying-party trust withdrawal |
| Silver | Verification Report | v0.1.0 | Structured verifier decision artifact |
| Silver | Independent Verifier Demo | v0.1.0 | Portable relying-party verification demo |
| Silver | Relying-Party Profile | v0.2.1 | Formal acceptance criteria for Silver evidence packages |
| Silver | Profile Conformance Report | v0.2.1 | Structured profile conformance decision artifact |
| Silver | Verifier Output Attestation | v0.1.0 | Detached, signed verifier output attribution |
| Silver | Multi-Principal Authority Fixture | v0.1.0 | Deterministic scoped authority evaluation |
| Silver | Protected Action Request | v0.1.0 | Structured authority evaluation request |
| Silver | Protected Action Decision Report | v0.1.0 | Authority evaluation decision artifact |
| Silver | Multi-Agent Harness Script | v0.1.0 | Deterministic scripted multi-principal attack scenario |
| Silver | Multi-Agent Harness Run Report | v0.1.0 | Structured harness run summary with per-event match results |
| Silver | Multi-Agent Harness Evidence Manifest | v0.1.0 | SHA-256 manifest over harness output artifacts |
| Silver | Multi-Agent Demo Package Manifest | v0.1.0 | SHA-256 manifest packaging the v0.2.4 harness evidence into a local demo |
| Silver | Multi-Agent Demo Summary | v0.1.0 | Eight deterministically derived claims over the packaged harness evidence |
| Silver | Evidence Source Adapter Descriptor | v0.1.0 | Static declaration of how an evidence source maps into ProofRail-relevant fields |

Artifact schema versions and repository release versions intentionally differ. Repository releases advance when a new profile, demo, evidence chain, or conformance behavior becomes available; individual schemas advance only when that artifact changes.

---

## Silver v0.2.1 Profile Modes

The Silver Relying-Party Profile v0.2.1 defines three modes:

- `silver.base` validates a Silver verification report from a conformant Silver verifier. Revocation is required.
- `silver.base.demo` preserves the v0.2.0 `silver.base` semantics where revocation absence produces a warning-path pass.
- `silver.independent` validates a Silver verification report from an independent verifier package, with package manifest and verifier identity checks.

Revocation semantics are mode-dependent:

- `silver.base` and `silver.independent` require revocation checking.
- `silver.base.demo` may pass without revocation checking with an explicit warning reason: `profile_requirements_satisfied_with_revocation_warning`.

v0.2.0 made revocation absence visible. v0.2.1 makes revocation expected for ordinary Silver reliance. v0.2.2 provides attestable verifier outputs without making certification claims.

The independent mode preserves the key Silver idea: a relying party can verify a prepared evidence package outside the environment that produced it.

---

## What ProofRail v0.2.5 Shows

ProofRail v0.2.5 shows that a protected actuator-control evidence package can be:

```text
generated
  → integrity-checked
  → bundled
  → signed
  → locally revocation-checked
  → reported
  → independently re-verified
  → profile-validated for relying-party acceptance (with mandatory revocation)
  → verifier output attested (tamper-evident, attributable)
  → multi-principal authority evaluated (scoped, delegated, revocation-aware)
  → exercised by a deterministic multi-principal agent attack harness that produces hash-anchored, non-executing harness evidence
  → packaged as a local multi-agent trust-boundary demo whose claims are deterministically derived from the harness evidence and whose package manifest is hash-verifiable end to end
```

v0.2.5 also publishes the first explicit Gold boundary doc ([`docs/gold/gold-boundary-v0.2.5.md`](docs/gold/gold-boundary-v0.2.5.md)). It names — but does not introduce — Gold. There is no Gold schema, validator, or certificate in this release.

The main transition is:

```text
Silver v0.2.5:
  multi-agent trust-boundary demo packaged from v0.2.4 harness evidence,
  with hash-verifiable package manifest, deterministically derived claims,
  and the first explicit Gold boundary documentation

Next:
  stronger relying-party operating profile

Later:
  Gold governed acceptance / certification layer
```

Silver remains the evidence-package reliance layer. Gold begins only when the work shifts from verifier conformance to governed institutional acceptance, review, challenge, and certification workflows. v0.2.5 does not begin that work; it names the boundary so later releases can address it explicitly.

Run and verify the v0.2.5 demo locally:

```bash
make run-silver-multi-agent-demo-v0-2-5
make verify-silver-multi-agent-demo-v0-2-5
```

---

## What ProofRail v0.2.6 Adds

ProofRail v0.2.6 introduces the **Silver Evidence Source Adapter** profile. It adds:

- a structured descriptor schema (`schemas/silver-evidence-source-adapter-v0.1.0.md`);
- six canonical static JSON descriptors (`examples/silver-evidence-source-adapters/`) covering native ProofRail, gateway, observability trace, SIEM, policy engine, and GRC platform sources;
- a local pure-stdlib structural validator (`tools/silver/validate_evidence_source_adapter_v0_1_0.py`) supporting single-file and directory modes;
- an 18-step regression test (`tests/test_silver_evidence_source_adapter_v0_2_6.sh`).

A descriptor declares how an evidence source maps its records into ProofRail-relevant evidence fields, and — crucially — what the source does **not** assert. Each descriptor lists six required evidence capabilities (`decision_event`, `bypass_evidence`, `revocation_status`, `subject_hashes`, `source_identity`, `timestamp_integrity`) with `provided`, `not_provided`, or `not_applicable` status, mandatory limitation text for non-provided capabilities, and explicit `adapter_limitations` and `non_claims` blocks.

The GRC platform descriptor is explicitly framed as workflow / risk / approval evidence only. Its limitations state that workflow approval is **not technical enforcement** and **not sufficient by itself** for protected-action reliance — technical decision evidence from a gateway, policy engine, or native ProofRail run is required.

> v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy.

Run and verify the v0.2.6 descriptors locally:

```bash
make validate-silver-evidence-source-adapters-v0-2-6
make verify-silver-evidence-source-adapter-v0-2-6
```

---

## What ProofRail v0.2.7 Adds

ProofRail v0.2.7 introduces the **Composed Silver Demo Over Simulated Gateway Evidence**. It adds:

- a JSONL simulated gateway event schema (`schemas/silver-simulated-gateway-evidence-event-v0.1.0.md`);
- a composed gateway evidence report schema (`schemas/silver-composed-gateway-evidence-report-v0.1.0.md`);
- a composed gateway evidence manifest schema (`schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md`);
- a static nine-event JSONL fixture (`fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`);
- a composer (`tools/silver/compose_gateway_evidence_demo_v0_1_0.py`) that subprocess-invokes the unchanged v0.2.6 adapter validator, parses the fixture, derives ten required claims, and emits a five-subject manifest with a `composition` block;
- an independent verifier (`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`) that re-derives every claim from the copied adapter and JSONL, validates the manifest `composition` block against the deterministic package layout, and rejects wrong-but-valid evidence refs;
- a 28-step regression test (`tests/test_silver_composed_gateway_evidence_v0_2_7.sh`) that exercises all 18 stable failure reasons in the verifier.

The composer writes its runtime output to `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/` (never committed). The composed report is not signed; v0.2.7 ships local hash anchors only.

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not integrate with a real gateway or certify gateway enforcement.

The simulated gateway is an evidence source, not a trust authority.

Run and verify the v0.2.7 composed gateway demo locally:

```bash
make run-silver-composed-gateway-demo-v0-2-7
make verify-silver-composed-gateway-demo-v0-2-7
```

---

## What ProofRail v0.2.8 Adds

ProofRail v0.2.8 introduces the **Silver Relying-Party Acceptance Record**. It adds:

- an acceptance policy schema (`schemas/silver-relying-party-acceptance-policy-v0.1.0.md`) declaring the relying party's allowed purposes, allowed evidence types, required verification, revocation requirements, challenge window, and allowed decisions (`accepted`, `rejected`, `accepted_with_exceptions`);
- an acceptance record schema (`schemas/silver-relying-party-acceptance-record-v0.1.0.md`) for the decision itself (relying party / policy binding, decision status, verifier outcome, revocation review, exceptions, scope limitations, challenge window, non-claims);
- a three-subject package manifest schema (`schemas/silver-relying-party-acceptance-package-manifest-v0.1.0.md`) binding the policy, the verified v0.2.7 evidence manifest, and the record;
- a static fixture (`fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json`) describing a fictional demo relying party;
- a generator (`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`) that subprocess-invokes the unchanged v0.2.7 verifier and refuses `--decision accepted` with `FAIL: evidence_verification_failed: <detail>` (exit 1) when v0.2.7 verification fails;
- a validator (`tools/silver/validate_relying_party_acceptance_record_v0_1_0.py`) running 22 ordered checks over 21 stable failure reasons, with an optional `--evidence-package-root` re-verification mode that emits `external_evidence_verification_failed`;
- a 30-step regression test (`tests/test_silver_relying_party_acceptance_record_v0_2_8.sh`) covering every stable validator failure reason plus the generator-only `evidence_verification_failed` refusal.

The generator writes runtime output to `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/` (never committed). The acceptance record is not signed; v0.2.8 ships local hash anchors only.

> v0.2.8 records a relying party's local acceptance decision over verified Silver evidence. It does not certify the evidence, the system, the gateway, or the relying party.

A relying-party acceptance record is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument. v0.2.8 records acceptance context; it does not execute acceptance governance.

Run and verify the v0.2.8 acceptance demo locally:

```bash
make run-silver-relying-party-acceptance-demo-v0-2-8
make verify-silver-relying-party-acceptance-demo-v0-2-8
```

---

## What ProofRail v0.2.9 Adds

ProofRail v0.2.9 introduces the **Silver Revocation/Challenge Drill**: a deterministic, local, post-acceptance review drill that stress-tests an existing v0.2.8 relying-party acceptance record against challenge and revocation signals. It adds:

- a review event schema (`schemas/silver-relying-party-review-event-v0.1.0.md`) with three closed event types (`challenge.received`, `revocation.signal_received`, `acceptance.revalidation_performed`), each targeting a specific acceptance record and purpose;
- a drill report schema (`schemas/silver-revocation-challenge-drill-report-v0.1.0.md`) recording the bound v0.2.8 record, validation result, derived findings and review triggers, and a single `recommended_local_posture` drawn from a closed set;
- a three-subject drill package manifest schema (`schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md`) binding the nested v0.2.8 acceptance package manifest, the review-events JSONL, and the drill report;
- a static fixture (`fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl`) with one within-window challenge, one revocation signal, and one revalidation event;
- a runner (`tools/silver/run_revocation_challenge_drill_v0_1_0.py`) that subprocess-invokes the v0.2.8 acceptance validator, refuses with `acceptance_package_validation_failed` or `review_fixture_insufficient` when prerequisites are not met, and atomically moves a staging directory into place so refused runs leave no partial output;
- a verifier (`tools/silver/verify_revocation_challenge_drill_v0_1_0.py`) re-deriving every binding and classification from the nested v0.2.8 package and the review-events JSONL, with 22 stable failure reasons including `nested_acceptance_package_invalid`, `challenge_window_classification_mismatch`, `challenge_within_window_missing`, `revocation_signal_missing`, `revocation_signal_target_mismatch`, and `external_evidence_verification_failed`;
- a 33-case regression test (`tests/test_silver_revocation_challenge_drill_v0_2_9.sh`) covering every stable verifier failure reason plus both runner-only refusal codes plus a scoped sha256 snapshot of committed v0.2.9 source paths.

The drill writes runtime output to `/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/` (never committed). The drill report is not signed; v0.2.9 ships local hash anchors only. v0.2.9 introduces no new fields in v0.2.6, v0.2.7, or v0.2.8 schemas.

> v0.2.9 drills post-acceptance review signals over a Silver relying-party acceptance record. It does not adjudicate challenges, revoke acceptance, certify evidence, or execute Gold governance.

A revocation/challenge drill report is not a Gold certificate, regulator approval, third-party audit, legal revocation, dispute resolution, or acceptance governance workflow. v0.2.9 records review triggers; it does not decide their merits.

Run and verify the v0.2.9 drill locally:

```bash
make run-silver-revocation-challenge-drill-v0-2-9
make verify-silver-revocation-challenge-drill-v0-2-9
```

---

## What ProofRail v0.3.0 Adds

ProofRail v0.3.0 introduces the **Silver Acceptance Handoff**: a deterministic, local composition release that packages the completed v0.2.7 / v0.2.8 / v0.2.9 Silver acceptance chain into a single portable, hash-anchored handoff artifact. It adds:

- a handoff summary schema (`schemas/silver-acceptance-handoff-summary-v0.1.0.md`) recording the included v0.2.7 / v0.2.8 / v0.2.9 manifest hashes, the v0.2.8 acceptance record id, decision status, and purpose, the v0.2.9 recommended local posture, the derived v0.3.0 handoff posture, scope limitations, non-claims, and a non-empty `reuse_warning`;
- a four-subject handoff manifest schema (`schemas/silver-acceptance-handoff-manifest-v0.1.0.md`) binding the composed-gateway-evidence manifest, the acceptance-package manifest, the revocation/challenge drill manifest, and the handoff summary in a fixed deterministic order;
- a runner (`tools/silver/build_silver_acceptance_handoff_v0_1_0.py`) that subprocess-invokes the unchanged v0.2.7 verifier, v0.2.8 acceptance validator, and v0.2.9 drill verifier (the latter two without `--evidence-package-root` so v0.3.0 owns the four cross-copy chain-binding checks), refuses on nested-validator failure or chain-binding mismatch with stable refusal codes, byte-copies the three nested package roots under fixed top-level directories, and with `--self-validate` verifies the staging directory before the atomic move;
- a verifier (`tools/silver/verify_silver_acceptance_handoff_v0_1_0.py`) running 17 stable failure reasons including `handoff_chain_binding_mismatch`, `handoff_posture_downgrade`, and `handoff_overclaim`, re-running all three nested validators, re-deriving the four v0.3.0-owned chain-binding cross-checks, enforcing a closed-set posture rank ordering, and running a recursive overclaim guard against 15 forbidden positive tokens;
- a 31-case regression test (`tests/test_silver_acceptance_handoff_v0_3_0.sh`) covering every stable verifier failure reason plus the five runner-only refusal codes.

The handoff package is unsigned; v0.3.0 ships local hash anchors only.

> v0.3.0 packages already-verified Silver evidence. It does not extend the substance of what that evidence asserts.

A Silver acceptance handoff package is not a Gold certificate, regulator approval, auditor approval, legal acceptance, transferred reliance, adjudicated challenge resolution, legally revoked acceptance, production authorization, or a governance act. The `recommended_handoff_posture` is descriptive, not approval.

Run and verify the v0.3.0 acceptance handoff locally:

```bash
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
```

---

## What ProofRail v0.3.1 Adds

ProofRail v0.3.1 introduces the **Silver Handoff Inspector + Gold Gap Inventory**: a deterministic, local artifact that makes a v0.3.0 Silver acceptance handoff package independently inspectable, producing a hash-anchored review report that summarizes the verified chain, the carried-forward caution posture, and the unresolved Gold-boundary prerequisites. It adds:

- a Gold-boundary requirement set schema (`schemas/silver-to-gold-requirement-set-v0.1.0.md`) declaring exactly one row per each of 13 governance domains with one of four closed-set statuses (`silver_evidence_present`, `silver_evidence_partial`, `gold_prerequisite_unmet`, `out_of_scope_for_silver`);
- an inspection report schema (`schemas/silver-handoff-inspection-report-v0.1.0.md`) recording the bound v0.3.0 handoff, the re-derived handoff summary, per-component inspection rows, the gap inventory with recomputed counts, and a `gold_boundary_status` forced to `gold_not_claimed` whenever any row is partial / unmet / out-of-scope;
- a three-subject inspection manifest schema (`schemas/silver-handoff-inspection-manifest-v0.1.0.md`) binding the v0.3.0 handoff manifest, the requirement set, and the inspection report in fixed order;
- a committed fixture (`fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json`) with deterministic distribution: 1 present / 4 partial / 6 unmet / 2 out-of-scope;
- a runner (`tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py`) that subprocess-invokes the unchanged v0.3.0 handoff verifier and refuses with stable runner-only codes (`handoff_validation_failed`, `requirement_set_validation_failed`, `inspection_self_validation_failed`) on failure;
- a verifier (`tools/silver/verify_silver_handoff_inspection_v0_1_0.py`) with 20 stable failure reasons including `inspection_handoff_summary_mismatch` (non-posture fields only), `inspection_review_posture_downgrade` (posture path), `requirement_duplicate`, `requirement_domain_missing`, `inspection_count_mismatch`, `inspection_gold_overclaim`, and `nested_handoff_invalid`;
- a 30-case regression test (`tests/test_silver_handoff_inspector_v0_3_1.sh`) covering every stable verifier failure reason plus the three runner-only refusal codes.

The inspection package is unsigned; v0.3.1 ships local hash anchors only. The bound Gold-boundary requirement set is a local ProofRail demo inventory, not an external compliance standard. `silver_evidence_present` means relevant Silver evidence is present inside the ProofRail chain — it does **not** mean the corresponding Gold prerequisite is satisfied.

> v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable. It does not certify the handoff, the system, or the relying party, and it does not begin Gold governance.

A Silver handoff inspection package is not a Gold certificate, Gold readiness assessment, regulator approval, auditor approval, legal acceptance, transferred reliance, adjudicated challenge resolution, or production authorization.

Run and verify the v0.3.1 handoff inspection locally:

```bash
make run-silver-handoff-inspection-v0-3-1
make verify-silver-handoff-inspection-v0-3-1
```

---

## What ProofRail v0.3.2 Adds

ProofRail v0.3.2 introduces the **Silver Trace Binding Profile**: a deterministic, local artifact that binds protected-action claims to concrete trace events from the unchanged v0.2.6 simulated observability-trace adapter descriptor, producing a hash-anchored package whose every field a Silver reviewer can re-derive without trusting the observability substrate. It adds:

- four v0.1.0 schemas (`schemas/silver-trace-event-v0.1.0.md`, `schemas/silver-trace-claim-binding-set-v0.1.0.md`, `schemas/silver-trace-binding-report-v0.1.0.md`, `schemas/silver-trace-binding-manifest-v0.1.0.md`) declaring the JSONL event format with closed `decision` enum `{allow, deny, observe, block}`, the binding-row format with closed `expected_binding_status` enum `{bound, bound_with_warning, trace_gap_detected, out_of_scope_for_trace_binding}`, the deterministically derived report whose `binding_summary` counts are recomputed from `bindings[].binding_status` and never hand-authored, and the four-subject anchor manifest in fixed order;
- a committed fixture (`fixtures/silver-trace-binding-profile-v0.3.2/`) with eight trace events and nine binding rows producing the deterministic distribution `bound=5 bound_with_warning=1 trace_gap_detected=1 out_of_scope=2`;
- a runner (`tools/silver/build_silver_trace_binding_v0_1_0.py`) that performs a structural trust-authority pre-check on the adapter BEFORE the v0.2.6 adapter validator subprocess (Amendment 1), cross-checks every non-gap binding row against the resolved trace event so only `trace_gap_detected` rows may reference an absent event (Amendment 4), and refuses with stable runner-only codes (`adapter_validation_failed`, `trace_events_validation_failed`, `trace_binding_set_validation_failed`, `trace_binding_self_validation_failed`) on failure;
- a verifier (`tools/silver/verify_silver_trace_binding_v0_1_0.py`) with 22 stable failure reasons including `trace_source_marked_authority` (Amendment 1 — checked BEFORE the generic `trace_adapter_invalid`), `trace_warning_downgrade` (Amendment 2 — checked BEFORE the generic `trace_report_status_mismatch` so downgrades of `bound_with_warning` / `trace_gap_detected` / `out_of_scope_for_trace_binding` to `bound` are always attributed to the more specific reason), `trace_event_duplicate`, `trace_event_time_order_invalid`, `trace_binding_event_missing`, `trace_binding_field_mismatch`, `trace_binding_time_window_mismatch`, `trace_report_binding_mismatch`, `trace_report_count_mismatch`, `trace_limitations_missing`, `trace_non_claims_missing`, and `trace_overclaim` (scanning every string outside `scope_limitations` / `non_claims` for 22 forbidden positive tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance`);
- a 30-case regression test (`tests/test_silver_trace_binding_v0_3_2.sh`) covering 4 positive exercises, 22 verifier failure reasons, and 4 runner-only refusal codes.

The trace binding package is unsigned; v0.3.2 ships local hash anchors only. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority. `source_event_ref` values on each event are opaque labeled strings and v0.3.2 does not cross-validate them against any external package.

> v0.3.2 binds protected-action claims to deterministic trace evidence for independent Silver review. It does not make the observability source authoritative, prove runtime truth, certify OpenTelemetry conformance, certify the underlying system, transfer reliance, or execute Gold governance.

A Silver trace binding package is not a Gold certificate, OpenTelemetry conformance claim, production observability claim, regulator approval, third-party audit, legal acceptance, compliance certification, or production authorization.

Run and verify the v0.3.2 trace binding locally:

```bash
make run-silver-trace-binding-v0-3-2
make verify-silver-trace-binding-v0-3-2
```

---

## What ProofRail v0.3.3 Adds

ProofRail v0.3.3 introduces the **Silver Adapter Pilot Package**: a deterministic, local artifact that pilots an external-evidence adapter flow by normalizing an OpenTelemetry-shaped local source-export fixture into ProofRail v0.3.2 trace-binding inputs under a declarative, evidence-only mapping, while preserving the boundary that the source system is not a trust authority, OpenTelemetry conformance is not asserted, vendor integration is not asserted, and runtime truth is not proved. It adds:

- four v0.1.0 schemas (`schemas/silver-adapter-pilot-source-export-v0.1.0.md`, `schemas/silver-adapter-pilot-normalization-map-v0.1.0.md`, `schemas/silver-adapter-pilot-report-v0.1.0.md`, `schemas/silver-adapter-pilot-manifest-v0.1.0.md`) declaring the OpenTelemetry-shaped JSONL source-export format with closed `export_format = "proofrail.simulated_otel_trace_export.v0.1"` (explicitly disclaiming OpenTelemetry conformance and vendor exports), a tiny normalization-map language admitting only `<source.dot.path>` and `"constant:<literal>"` values, the deterministically derived report whose seven required claims are pre-baked with `status: pass` and whose `source_is_trust_authority` / `runtime_truth_claimed` flags are forced, and the seven-subject anchor manifest in fixed order;
- a committed fixture (`fixtures/silver-adapter-pilot-package-v0.3.3/`) with an 8-line OpenTelemetry-shaped source-export fixture and a declarative normalization map; dot-path resolution uses LONGEST-PREFIX KEY MATCHING at each step so OpenTelemetry-style flat-with-dots attribute keys (e.g. `proofrail.event_id`) can be addressed without quoting;
- a runner (`tools/silver/build_silver_adapter_pilot_v0_1_0.py`) that performs a structural trust-authority pre-check on the adapter BEFORE the v0.2.6 adapter validator subprocess, subprocess-invokes the unchanged v0.2.6 adapter validator and the unchanged v0.3.2 trace-binding builder, stages every byte under `<output-dir>.staging.<pid>`, and atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed — a refused run leaves no final directory and no staging sibling, so the Make target is safely repeatable; refusals use six stable runner-only codes (`adapter_validation_failed`, `source_export_validation_failed`, `normalization_map_validation_failed`, `binding_set_validation_failed`, `nested_trace_binding_generation_failed`, `adapter_pilot_self_validation_failed`);
- a verifier (`tools/silver/verify_silver_adapter_pilot_v0_1_0.py`) with 24 stable failure reasons across 25 ordered checks, enforcing four reachability orderings: path traversal BEFORE exact subject-path equality; adapter trust-authority pre-check BEFORE the v0.2.6 adapter validator subprocess; re-derived normalized bytes equal packaged normalized bytes BEFORE the nested v0.3.2 verifier subprocess; nested v0.3.2 verifier subprocess BEFORE the nested-manifest hash cross-check pairing outer subjects [0]/[3]/[4] with nested subjects [0]/[1]/[2]; the overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 23 forbidden positive tokens including `runtime truth proved`, `opentelemetry conformance`, `vendor certified`, and `production approved`;
- a 36-numbered-exercise regression test (`tests/test_silver_adapter_pilot_v0_3_3.sh`) covering 4 positive exercises, 25 verifier-mutation cases covering the 24 stable reasons (both path-traversal cases — `..` and absolute — map to `adapter_pilot_subject_path_traversal`), 6 runner-only refusal cases, and 1 scoped snapshot.

The adapter pilot package is unsigned; v0.3.3 ships local hash anchors only. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority. The OpenTelemetry-shaped envelope uses the explicit `export_format: "proofrail.simulated_otel_trace_export.v0.1"` so the fixture cannot be confused with a real vendor export. v0.3.3 carries `source_event_ref` strings unchanged through normalization as opaque labels and does not cross-validate them against any external package.

> v0.3.3 pilots a local external-evidence adapter flow. It does not perform a real OpenTelemetry, vendor, observability, SIEM, GRC, gateway, policy-engine, or ticketing-system integration; does not establish the source system as a trust authority; does not certify OpenTelemetry conformance; does not certify any vendor integration; does not prove runtime truth; and does not extend the substance of any earlier-release Silver evidence.

A Silver adapter pilot package is not a Gold certificate, OpenTelemetry conformance claim, vendor certification, production integration, regulator approval, third-party audit, legal acceptance, compliance certification, or production authorization.

Run and verify the v0.3.3 adapter pilot package locally:

```bash
make run-silver-adapter-pilot-v0-3-3
make verify-silver-adapter-pilot-v0-3-3
```

---

## What ProofRail v0.3.4 Adds

ProofRail v0.3.4 introduces the **Silver Challenge / Withdrawal Record Primitives**: two deterministic local Silver evidence record primitives — a *challenge record* and a *withdrawal record* — hash-anchored to an unchanged v0.3.0 Silver acceptance handoff target inside a single packaged manifest. It adds:

- four v0.1.0 schemas (`schemas/silver-challenge-record-v0.1.0.md`, `schemas/silver-withdrawal-record-v0.1.0.md`, `schemas/silver-challenge-withdrawal-summary-v0.1.0.md`, `schemas/silver-challenge-withdrawal-manifest-v0.1.0.md`) declaring closed enums for `challenge_reason` (10 values), `challenge_status` (4 values), `withdrawal_reason` (7 values), `withdrawal_status` (4 values), `withdrawal_effect` (4 values), and a 5-value `posture` set derived deterministically from `withdrawal_effect` via a closed mapping table, plus seven required summary claims and a fixed 4-subject manifest layout;
- a committed fixture (`fixtures/silver-challenge-withdrawal-primitives-v0.3.4/`) with one challenge record and one withdrawal record that carry the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in `target.target_manifest_sha256` so the input fixtures can be authored independently of the target handoff (the runner rewrites the placeholder during staging);
- a runner (`tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py`) that subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier on the target, structurally validates both records under the v0.3.4 closed enums, performs four binding cross-checks (both records' `target.target_record_id` equal `handoff_id`; withdrawal cites the challenge; monotone time-order chain across target / challenge / withdrawal; both records' `target.target_manifest_path` equal the packaged subject [0] path), byte-copies the v0.3.0 handoff package root under `target-handoff/`, derives the summary deterministically with seven required claims pre-baked at `status: pass` and the posture forced from the `withdrawal_effect → posture` table, and atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed — refusals use five stable runner-only codes (`handoff_validation_failed`, `challenge_record_validation_failed`, `withdrawal_record_validation_failed`, `challenge_withdrawal_binding_failed`, `challenge_withdrawal_self_validation_failed`);
- a verifier (`tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py`) with 24 stable failure reasons across 25 ordered checks, enforcing four reachability orderings: path traversal BEFORE exact subject-path equality; structural record parse BEFORE the dedicated placeholder check; subprocess-invokes the unchanged v0.3.0 handoff verifier on subject [0]; and posture-vs-effect as a dedicated reason distinct from the status-echo check; the overclaim guard scans every string value outside `scope_limitations` and `non_claims` for the v0.3.x shared set of 20+ forbidden positive tokens, including optional `claims[].description` strings;
- a 35-numbered-exercise regression test (`tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh`) covering 4 positive exercises, 25 verifier-mutation cases covering the 24 stable reasons (both path-traversal cases — `..` and absolute — map to `challenge_withdrawal_subject_path_traversal`), 5 runner-only refusal cases, and a scoped sha256 snapshot of the nine committed v0.3.4 source paths.

The challenge / withdrawal primitives package is unsigned; v0.3.4 ships local hash anchors only. The challenge record and withdrawal record are independently authored local statements: v0.3.4 does not verify the substantive truth of any free-text reason or counterparty assertion within them. The withdrawal record's `withdrawal_effect` describes the filer's local posture only.

> v0.3.4 records a structured local challenge and a structured local withdrawal posture against an already-verified Silver acceptance handoff target. It does not adjudicate the challenge, does not legally revoke reliance, does not certify the target handoff, does not transfer reliance to any downstream party, and does not extend the substance of any earlier-release Silver evidence.

A Silver challenge / withdrawal primitives package is not a Gold certificate, adjudication, legal revocation, regulator approval, auditor approval, third-party audit, legal acceptance, compliance certification, production authorization, or transfer of reliance.

Run and verify the v0.3.4 challenge / withdrawal primitives package locally:

```bash
make run-silver-acceptance-handoff-v0-3-0
make run-silver-challenge-withdrawal-primitives-v0-3-4
make verify-silver-challenge-withdrawal-primitives-v0-3-4
```

---

## What ProofRail v0.3.5 Adds

ProofRail v0.3.5 introduces the **Silver Relying-Party Policy Pack**: a deterministic local Silver evidence primitive — a hand-authored *relying-party policy pack* paired with a byte-for-byte re-derivable *conformance report* inside a single 2-subject packaged manifest. It adds:

- three v0.1.0 schemas (`schemas/silver-relying-party-policy-pack-v0.1.0.md`, `schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md`, `schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md`) declaring a closed enum surface of 11 enums covering acceptance / challenge / withdrawal / supersession postures (3 values), verifier / issuer / revocation / freshness modes, supported signature algorithms, criteria result enums (4 values), warning treatments, related-artifact reference policy, and exception / hard-stop modes; 24 required conformance-report claim ids in fixed order; and a fixed 2-subject manifest layout;
- a committed fixture set (`fixtures/silver-relying-party-policy-pack-v0.3.5/`) with one canonical passing policy pack plus three additional passing variants exercising the closed enum surface (strict verifier mode, optional signature mode, scope_limitations boundary phrasing) — every fixture is locally re-derivable into a passing conformance report;
- a runner (`tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py`) that performs five distinct preflight checks under five stable runner-only refusal codes (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`), byte-copies the policy pack into a deterministic staging directory, deterministically re-derives a 24-entry conformance report whose canonical-JSON byte image depends only on the policy pack, writes a 2-subject manifest, and atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed; on `--self-validate` failure the runner relays the v0.3.5 verifier's own failure code UNCHANGED with **no** sixth runner-only wrapper code;
- a verifier (`tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py`) with 24 stable failure reasons across 24 ordered structural checks, enforcing non-masking ordering (the 23 ordered policy-pack checks `check_02..check_24` all run BEFORE the post-structural conformance-report byte-compare re-derivation, so any earlier structural defect surfaces with its dedicated reason; the only public emitted reason for a bundled-report disagreement is `policy_pack_manifest_invalid`), path-traversal BEFORE exact subject-path equality, and a 23-token prohibited-claim guard that scans every string value outside `scope_limitations`, `non_claims`, and `relying_party.contact` for forbidden positive tokens (`certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`, `gold-ready`, `gold ready`, `gold_ready`, `runtime proof`, `authoritative trace`, `runtime truth proved`, `vendor certified`, `production approved`);
- a 47-numbered-exercise regression test (`tests/test_silver_relying_party_policy_pack_v0_3_5.sh`) covering 4 positive-path exercises (PP1..PP4), 24 canonical verifier-reason exercises (case01..case24) plus 11 duplicate manifest-invalid exercises (dup01..dup11) that share the structural reason `invalid_relying_party_policy_pack_manifest` to confirm reason stability under multiple distinct mutations, 5 runner-only refusal exercises (ro1..ro5), 1 runner-relay-of-verifier exercise (rel01) explicitly asserting NO sixth wrapper code, 1 taxonomy gate (TG1) enforcing that every reason-shaped token in v0.3.5 source belongs to the 24-reason verifier set ∪ 5 runner-only set ∪ a small documented allow-list of closed enum values and test-mutation labels, and 1 scoped sha256 snapshot (SS) over the committed v0.3.5 source paths.

The relying-party policy pack package is unsigned; v0.3.5 ships local hash anchors only. The policy pack is a hand-authored local declaration of acceptance posture; v0.3.5 does not approve, audit, or certify the policy pack and does not evaluate any specific upstream Silver evidence against it.

> v0.3.5 records that a relying party has hand-authored a structured local policy pack whose canonical-JSON byte image satisfies 24 ordered structural checks and that the bundled conformance report can be re-derived byte-for-byte from the policy pack alone. It does not approve the policy pack, does not adjudicate any specific challenge / withdrawal / supersession event against it, does not evaluate any specific upstream Silver evidence against it, and does not transfer reliance to any downstream party.

A Silver relying-party policy pack package is not a Gold certificate, regulator action, auditor finding, third-party endorsement, certification, compliance attestation, adjudication, evidence-evaluation result, transfer of reliance, or authorization for production reuse.

Run and verify the v0.3.5 relying-party policy pack locally:

```bash
make run-silver-relying-party-policy-pack-v0-3-5
make verify-silver-relying-party-policy-pack-v0-3-5
```

---

## What ProofRail v0.3.6 Adds

ProofRail v0.3.6 introduces the **Silver Control Crosswalk + Protected Action Catalog**: a deterministic local Silver evidence primitive — a hand-authored *control pack* declaring a closed-vocabulary protected action catalog and a closed crosswalk of those actions to ProofRail-internal evidence artifacts, paired with a byte-for-byte re-derivable *conformance report* inside a single 2-subject packaged manifest. It adds:

- three v0.1.0 schemas (`schemas/silver-control-crosswalk-protected-action-catalog-v0.1.0.md`, `schemas/silver-control-crosswalk-protected-action-catalog-manifest-v0.1.0.md`, `schemas/silver-control-crosswalk-protected-action-catalog-conformance-report-v0.1.0.md`) declaring a closed enum surface (catalog `category`, `environment_scope`, `actor_scope`; `authority.posture`; `risk_boundary.risk_class`; crosswalk `artifact_type` drawn from the repo-derived 43-entry ProofRail artifact_type set including Bronze claim and Bronze evidence-bundle concepts; crosswalk `relationship`; conservative claim verb set `may_inform` / `may_evidence` / `may_support`; control-limitation `domain`; dependency `reference_type`; and a closed Silver `upstream_id` set for version bindings) and a 2-subject manifest layout with `proofrail_release: silver.control_crosswalk.v0.3.6`;
- a committed fixture set (`fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/`) with one canonical passing control pack (five protected actions, five crosswalk entries) plus two additional passing variants exercising the dependency-reference and control-limitation surfaces — every fixture is locally re-derivable into a passing conformance report;
- a runner (`tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py`) that performs five distinct preflight checks under five stable runner-only refusal codes (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`), byte-copies the control pack into a deterministic staging directory, deterministically re-derives a 24-entry conformance report whose canonical-JSON byte image depends only on the control pack, writes a 2-subject manifest with a cross-anchored `control_pack_id`, and atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed; on `--self-validate` failure the runner relays the v0.3.6 verifier's own failure code UNCHANGED with **no** sixth runner-only wrapper code;
- a verifier (`tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py`) with 24 stable failure reasons across 25 ordered execution steps, enforcing non-masking ordering (the 24 ordered structural checks `check_01..check_24` all run BEFORE the post-structural conformance-report byte-compare re-derivation, so any earlier structural defect surfaces with its dedicated reason; the only public emitted reason for a bundled-report disagreement or `manifest.control_pack_id` cross-anchor mismatch is `control_pack_manifest_invalid`, deliberately funnelled to avoid introducing a twenty-fifth public reason), path-traversal BEFORE exact subject-path equality, and a 32-token prohibited-compliance-claim guard that scans every string value outside `scope_limitations`, `non_claims`, and `control_limitations` for forbidden positive tokens covering external framework names (`soc 2`, `iso 27001`, `nist 800-53`, `pci dss`, `hipaa`), control-effectiveness claims, audit-ready claims, regulator/auditor approval, production authorization, legal enforceability, transferred trust, runtime truth, and Gold reliance;
- a 47-numbered-exercise regression test (`tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh`) covering 4 positive-path exercises (PP1..PP4), 24 canonical verifier-reason exercises (case01..case24) plus 11 duplicate manifest-invalid exercises (dup01..dup11) that share the structural reason `control_pack_manifest_invalid` to confirm reason stability under multiple distinct mutations (subject [0] / [1] absolute path, subject [0] / [1] traversal, subject [0] file missing, subject [0] `size_bytes` mismatch, subject [0] `sha256` mismatch, wrong subject count, subject [0] role wrong, `control_pack_id` cross-anchor mismatch, and the non-masking post-structural conformance-report disagreement), 5 runner-only refusal exercises (ro1..ro5), 1 runner-relay-of-verifier exercise (rel01) explicitly asserting NO sixth wrapper code, 1 taxonomy gate (TG1) enforcing that every reason-shaped token in v0.3.6 source and v0.3.6-anchored sections of the cross-version docs belongs to the 24-reason verifier set ∪ 5 runner-only set ∪ a small documented allow-list, and 1 scoped sha256 snapshot (SS) over the committed v0.3.6 source paths.

The control crosswalk + protected action catalog package is unsigned; v0.3.6 ships local hash anchors only. The control pack is a hand-authored local declaration of a protected action catalog and an internal-evidence crosswalk; v0.3.6 does not approve, audit, or certify the catalog, does not map it to SOC 2 / ISO 27001 / NIST 800-53 / PCI DSS / HIPAA or any other external framework, does not opine on control design or operating effectiveness, and does not re-evaluate the referenced upstream Silver evidence against the catalog in this release.

> v0.3.6 records that a package owner has hand-authored a structured local control pack whose canonical-JSON byte image satisfies 24 ordered structural checks, that the catalog and crosswalk are internally consistent under closed vocabularies and conservative claim verbs, and that the bundled conformance report can be re-derived byte-for-byte from the control pack alone. It does not approve the catalog, does not map the catalog to any external framework, does not opine on control design or operating effectiveness, does not re-evaluate any specific upstream Silver evidence against the crosswalk, and does not transfer reliance to any downstream party.

A Silver control crosswalk + protected action catalog package is not a Gold certificate, regulator action, auditor finding, third-party endorsement, SOC 2 / ISO / NIST / PCI / HIPAA framework mapping, control effectiveness opinion, transfer of reliance, or authorization for production reuse.

Run and verify the v0.3.6 control crosswalk + protected action catalog locally:

```bash
make run-silver-control-crosswalk-protected-action-catalog-v0-3-6
make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
```

---

## What ProofRail Does Not Claim

ProofRail v0.3.5 does not claim:

- Gold certification;
- third-party certification;
- regulator approval;
- production PKI;
- production deployment assurance;
- audit opinion;
- public accreditation;
- that any real gateway, observability stack, SIEM, policy engine, or GRC platform is conformant with ProofRail.

Silver profile conformance is local relying-party verification, not certification of a live system. The v0.2.5 multi-agent trust-boundary demo is a local, deterministic re-packaging of v0.2.4 harness evidence; it does not execute live agents, does not invoke live actuators, does not parse natural-language prompts, does not detect prompt injection, and does not cross the Gold boundary. The v0.2.6 evidence source adapter descriptors are static declarations only; they do not integrate with any real product, do not certify their declared sources, and do not assert that a declared source actually behaves as described. The v0.2.7 composed gateway evidence demo is a substrate-neutral local composition over a static JSONL fixture; it does not integrate with any real MCP gateway, SIEM, observability stack, policy engine, or GRC platform, does not execute any protected action, does not establish the gateway as a trust authority, does not sign the composed report, and does not constitute a relying-party acceptance record. The v0.2.8 relying-party acceptance record is a local hash-anchored artifact recording a fictional demo relying party's decision over verified v0.2.7 evidence; it does not certify the evidence, does not certify any system, does not sign the record, does not coordinate multiple relying parties, does not establish a new trust authority, and is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument. The v0.2.9 revocation/challenge drill is a local hash-anchored review record over a v0.2.8 acceptance package; it does not query live revocation services, does not interact with any real challenge or dispute process, does not revoke acceptance, does not adjudicate challenges on the merits, does not alter the v0.2.7 evidence package or the v0.2.8 acceptance record, and is not a Gold certificate, regulator approval, third-party audit, or legal revocation instrument. The v0.3.0 acceptance handoff package is a local, deterministic, hash-anchored composition over the already-verified v0.2.7 / v0.2.8 / v0.2.9 chain; it does not extend the substance of what the nested evidence asserts, does not sign the handoff, does not transfer reliance from the original v0.2.8 relying party to any downstream party, does not adjudicate any challenge or revocation signal, does not constitute Gold conformance or regulator/auditor approval, and the `recommended_handoff_posture` is descriptive only — it is not an approval, decision, or governance act. The v0.3.1 handoff inspection package is a local, deterministic, hash-anchored review record over the unchanged v0.3.0 handoff plus a committed local Gold-boundary requirement set; it does not introduce a new evidence source, does not certify the underlying chain, does not sign the inspection package, does not transfer reliance, does not adjudicate any challenge or revocation signal, does not consult an external compliance standard, does not constitute Gold readiness or Gold certification, does not constitute regulator approval, auditor approval, legal acceptance, or production authorization, and `silver_evidence_present` in the gap inventory does **not** mean the corresponding Gold prerequisite is satisfied. The v0.3.2 trace binding package is a local, deterministic, hash-anchored binding artifact over a static trace event fixture and a binding set, anchored to the unchanged v0.2.6 simulated observability-trace adapter descriptor; it does not query any real observability, SIEM, GRC, gateway, policy-engine, or ticketing service, does not establish the observability substrate as a trust authority, does not prove that runtime behavior occurred exactly as described, does not certify OpenTelemetry conformance, does not sign the trace binding package, does not transfer reliance, does not adjudicate any challenge or revocation signal, does not extend the substance of any earlier-release Silver evidence, does not resolve or cross-validate `source_event_ref` strings against any external package, and does not constitute Gold readiness, regulator approval, auditor approval, legal acceptance, compliance certification, or production authorization. The v0.3.3 adapter pilot package is a local, deterministic, hash-anchored pilot of an external-evidence adapter flow that normalizes an OpenTelemetry-shaped local source-export fixture into v0.3.2 trace-binding inputs under a declarative mapping; it does not query any real OpenTelemetry collector, vendor service, observability platform, SIEM, GRC, gateway, policy-engine, or ticketing system, does not establish the source system as a trust authority, does not certify OpenTelemetry conformance, does not certify any vendor integration, does not prove runtime truth, does not sign the adapter pilot package, does not transfer reliance, does not adjudicate any challenge or revocation signal, does not extend the substance of any earlier-release Silver evidence, does not resolve or cross-validate `source_event_ref` strings against any external package, and does not constitute Gold readiness, regulator approval, auditor approval, legal acceptance, compliance certification, or production authorization. The v0.3.4 challenge / withdrawal primitives package is a local, deterministic, hash-anchored pair of evidence record primitives — one challenge record and one withdrawal record — hash-anchored to an unchanged v0.3.0 Silver acceptance handoff target inside a single packaged manifest; it does not adjudicate the challenge, does not legally revoke reliance, does not certify the target handoff, does not authorize production reuse, does not consult, notify, or coordinate with any regulator, auditor, third party, counterparty, or downstream relying party, does not verify the substantive truth of any free-text reason or counterparty assertion inside the records, does not sign the package, does not transfer reliance, does not extend the substance of any earlier-release Silver evidence, and does not constitute Gold readiness, regulator approval, auditor approval, legal acceptance, legal revocation, compliance certification, or production authorization. The `withdrawal_effect` enum describes the filer's local posture only. The v0.3.5 relying-party policy pack package is a local, deterministic, hash-anchored hand-authored policy declaration paired with a byte-for-byte re-derivable conformance report inside a single 2-subject packaged manifest; it does not approve, audit, or certify the policy pack, does not adjudicate any specific challenge / withdrawal / supersession event against it, does not evaluate any specific upstream Silver evidence against it, does not query, consult, notify, or coordinate with any regulator, auditor, third party, counterparty, or downstream relying party, does not sign the package, does not transfer reliance, does not extend the substance of any earlier-release Silver evidence, and does not constitute Gold readiness, regulator approval, auditor approval, legal acceptance, compliance certification, or production authorization.

---

## Current Focus Areas

ProofRail is not intended to replace enterprise gateways or security platforms. Its purpose is to define the control claims and evidence structure needed to trust deployments of agentic AI controls across heterogeneous enterprise stacks.

Current focus areas include:

- protected actuator set declaration and hashing;
- bypass-prevention evidence;
- emergency-stop and safe-mode semantics;
- normalized audit evidence;
- performance evidence;
- Bronze claim schemas and conformance profiles;
- composed Bronze stacks using existing gateway and observability components;
- Silver signed relying-party verification and local revocation;
- Silver evidence-package profile validation;
- stronger Silver relying-party operating profiles.

Raw deployment evidence, credentials, private topology, and security-sensitive operational details are not published here. Public materials are limited to specifications, profiles, sanitized attestations, examples, and implementation guidance.

## Start Here

1. [Silver Multi-Agent Trust-Boundary Demo v0.2.5](docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md)
2. [Gold Boundary v0.2.5](docs/gold/gold-boundary-v0.2.5.md)
3. [Silver Relying-Party Profile v0.2.1](https://github.com/ProofRail/proofrail/blob/main/profiles/silver/SILVER_PROFILE_v0.2.1.md)
4. [Silver profile conformance report schema v0.2.1](https://github.com/ProofRail/proofrail/blob/main/schemas/silver-profile-conformance-report-v0.2.1.md)
5. [Silver verification tools README](https://github.com/ProofRail/proofrail/blob/main/tools/silver/README.md)
6. [Independent Silver verifier demo](https://github.com/ProofRail/proofrail/tree/main/demos/silver-demo-002-independent-verifier)
7. [Evidence walkthrough](https://github.com/ProofRail/proofrail/blob/main/docs/walkthroughs/composed-bronze-demo-001b-evidence-walkthrough.md)
8. [Bronze demo folders](https://github.com/ProofRail/proofrail/tree/main/demos/composed-bronze-demo-001)
9. [ProofRail Bronze claim schema v0.1.2](https://github.com/ProofRail/proofrail/blob/main/schemas/bronze-claim-schema-v0.1.2.md)
10. [Bronze claim tools README](https://github.com/ProofRail/proofrail/blob/main/tools/claims/README.md)
