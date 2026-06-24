# ProofRail Silver Artifact Map v0.1.7

**Suggested repo path:** `docs/reference/silver-artifact-map-v0.1.7.md`  
**Status:** Reviewed draft reference note  
**Applies to:** ProofRail v0.1.7

---

## Purpose

ProofRail v0.1.7 contains several related but distinct artifacts. This map explains what each artifact does, where it appears in the evidence chain, and what it does not claim.

The main point:

> Bronze structures local control evidence. Silver makes that evidence signed, revocable, reportable, and independently verifiable.

---

## Artifact Table

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Bronze | Bronze Claim | v0.1.2 | Structured local evidence claim | `schemas/bronze-claim-schema-v0.1.2.md` |
| Bronze | Evidence Bundle Manifest | v0.1.3 | Portable package integrity | `schemas/bronze-evidence-bundle-manifest-v0.1.3.md` |
| Silver | Signed Bundle Assertion | v0.1.0 | Issuer signature over bundle manifest | `schemas/silver-signed-bundle-assertion-v0.1.0.md` |
| Silver | Revocation List | v0.1.0 | Local relying-party trust withdrawal | `schemas/silver-revocation-list-v0.1.0.md` |
| Silver | Verification Report | v0.1.0 | Structured verifier decision artifact | `schemas/silver-verification-report-v0.1.0.md` |
| Silver | Independent Verification Package | v0.1.0 | Portable verifier input package | `demos/silver-demo-002-independent-verifier/` |
| Silver | Independent Verifier | v0.1.0 | Relying-party verification outside source tree | `demos/silver-demo-002-independent-verifier/verifier/independent_verify.py` |

---

## Evidence Chain

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
```

---

## Artifact Descriptions

### Bronze Claim v0.1.2

The Bronze claim is the structured local evidence claim.

It records the protected actuator set, controls, evidence references, limitations, and evidence checksums.

It answers:

> What did this local deployment claim, and what evidence files support it?

It does not prove external reliance, issuer trust, or certification.

### Bronze Evidence Bundle Manifest v0.1.3

The bundle manifest checksums the full portable evidence package, including the Bronze claim itself.

It solves the claim self-reference problem: the claim cannot checksum itself, but an external manifest can checksum the claim.

It answers:

> Does this package still contain the same files that were bundled?

It is unsigned by itself.

### Silver Signed Bundle Assertion v0.1.0

The signed assertion records that a demo issuer signed the raw bytes of the Bronze v0.1.3 bundle manifest.

It answers:

> Did a trusted issuer sign this exact evidence bundle manifest?

It does not certify the deployment. It signs evidence, not a live system.

### Silver Revocation List v0.1.0

The revocation list lets a relying party reject an otherwise valid signed assertion.

It supports revocation by:

- assertion ID;
- issuer key;
- bundle manifest hash.

It answers:

> Has the relying party withdrawn trust from this assertion, key, or bundle?

It is local demo revocation, not production PKI revocation.

### Silver Verification Report v0.1.0

The verification report records the verifier’s decision, inputs, check results, revocation status, and underlying bundle status.

It answers:

> What did the verifier check, and what decision did it reach?

It is not signed in v0.1.0. It is not a Gold certification decision.

### Independent Verification Package v0.1.0

The independent package is an exported, portable set of files that can be verified outside the original source tree.

It answers:

> Can this Silver evidence package be moved and verified separately?

It is a demo package, not a production distribution format.

### Independent Verifier v0.1.0

The independent verifier runs outside the original repo checkout and performs the Silver checks without importing or invoking the main verifier.

It answers:

> Can a separate relying-party verifier reproduce the Silver verification result?

It is not production software distribution or third-party certification.

---

## Versioning Note

The repo version and artifact versions are intentionally different.

```text
Repo release: v0.1.7

Bronze Claim Schema: v0.1.2
Bronze Bundle Manifest: v0.1.3
Silver Signed Bundle Assertion: v0.1.0
Silver Revocation List: v0.1.0
Silver Verification Report: v0.1.0
Independent Silver Verifier Demo: v0.1.0
```

This avoids forcing every artifact schema to increment whenever the repository adds a new demo or capability.

---

## What Silver Means at v0.1.7

At v0.1.7, Silver means:

> signed, revocable, reportable, independently verifiable evidence-package reliance.

It does not mean:

- production certification;
- regulator approval;
- third-party audit;
- Gold governance;
- public PKI;
- public transparency infrastructure.

---

## v0.2.0 Update: Silver Relying-Party Profile

Silver v0.2.0 adds the Silver Relying-Party Profile — the formal acceptance criteria for a Silver evidence package.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Profile | v0.2.0 | Formal acceptance criteria for Silver evidence packages | `profiles/silver/SILVER_PROFILE_v0.2.0.md` |
| Silver | Profile Conformance Report | v0.2.0 | Structured conformance decision artifact | `schemas/silver-profile-conformance-report-v0.2.0.md` |

The profile defines two modes:

- `silver.base` — Validates a Silver verification report from any conformant verifier. Revocation not performed produces a conditional pass with warning.
- `silver.independent` — Validates a Silver verification report from an independent verifier, requiring a valid package manifest and mandatory revocation.

The profile validator (`tools/silver/validate_silver_profile_v0_2_0.py`) consumes a Silver Verification Report v0.1.0 and optionally a package manifest, producing a profile conformance report.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
```

## v0.2.1 Update: Tightened Silver Profile

Silver v0.2.1 adds a third profile mode and tightens revocation requirements.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Profile | v0.2.1 | Tightened acceptance criteria (revocation required for silver.base) | `profiles/silver/SILVER_PROFILE_v0.2.1.md` |
| Silver | Profile Conformance Report | v0.2.1 | Structured conformance decision artifact (three modes) | `schemas/silver-profile-conformance-report-v0.2.1.md` |
| Silver | Independent Verification Package Format | v0.2.1 | Package handoff format specification | `docs/silver/independent-verification-package-format-v0.2.1.md` |

The profile defines three modes:

- `silver.base` — Revocation required. No warning path.
- `silver.base.demo` — Preserves v0.2.0 `silver.base` semantics (revocation warning path).
- `silver.independent` — Unchanged from v0.2.0.

The v0.2.1 package exporter adds `package_format_version`, `profile_compatibility`, `inputs`, and `path_map` to the manifest. The independent verifier requires no changes.

## v0.2.2 Update: Verifier Output Attestation

Silver v0.2.2 adds detached, signed attestations over verifier outputs.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Verifier Output Attestation | v0.1.0 | Detached, signed verifier output attribution | `schemas/silver-verifier-output-attestation-v0.1.0.md` |

The attestation binds a verifier's identity to its verification report and profile conformance report. For `silver.independent` mode, it also covers the package manifest.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
```

## v0.2.3 Update: Multi-Principal Authority Fixtures

Silver v0.2.3 adds deterministic multi-principal authority evaluation fixtures.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Multi-Principal Authority Fixture | v0.1.0 | Deterministic scoped authority evaluation | `schemas/silver-multi-principal-authority-fixture-v0.1.0.md` |
| Silver | Protected Action Request | v0.1.0 | Structured authority evaluation request | `schemas/silver-protected-action-request-v0.1.0.md` |
| Silver | Protected Action Decision Report | v0.1.0 | Authority evaluation decision artifact | `schemas/silver-protected-action-decision-report-v0.1.0.md` |

The authority evaluation extends the evidence chain with scoped, delegation-aware, revocation-aware authority decisions:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
```

The authority evaluator never executes a protected action. Every decision report includes `execution.performed == false` as structural proof.

## v0.2.4 Update: Multi-Agent Attack Harness Evidence

Silver v0.2.4 adds a deterministic, scripted multi-principal agent attack harness that drives the unchanged v0.2.3 authority evaluator across a canonical attack scenario and produces local evidence.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Multi-Agent Harness Script | v0.1.0 | Scripted multi-principal attack scenario (events, expected outcomes) | `schemas/silver-multi-agent-harness-script-v0.1.0.md` |
| Silver | Multi-Agent Harness Run Report | v0.1.0 | Structured run summary with per-event match results | `schemas/silver-multi-agent-harness-run-report-v0.1.0.md` |
| Silver | Multi-Agent Harness Evidence Manifest | v0.1.0 | SHA-256 manifest over the harness output artifacts | `schemas/silver-multi-agent-harness-evidence-manifest-v0.1.0.md` |

The harness runner:

- Consumes the v0.2.3 fixture and the unchanged authority evaluator (`evaluate_request` callable; no v0.2.3 refactor).
- Routes `protected_action_attempt` events through the evaluator, writing requests and decision reports.
- Records `bypass_attempt` events at harness level only — no evaluator call, no request file, no decision report.
- Records `revocation_marker` events without mutating the fixture; the decision time on subsequent events drives revocation semantics.
- Emits a transcript, derived `expected-outcomes.json`, a run report with `execution.protected_actions_performed == false`, and an evidence manifest with deterministic subject ordering.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
```

The harness never executes a protected action. Both the run report and every decision report carry structural execution proof (`execution.protected_actions_performed == false` and `execution.performed == false` respectively).

## v0.2.5 Update: Multi-Agent Trust-Boundary Demo + First Gold Boundary Doc

Silver v0.2.5 packages the v0.2.4 harness evidence into a local multi-agent trust-boundary demo with deterministically derived claims and the first explicit Gold boundary documentation.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Multi-Agent Demo Package Manifest | v0.1.0 | SHA-256 manifest packaging v0.2.4 harness evidence into a local demo | `schemas/silver-multi-agent-demo-package-manifest-v0.1.0.md` |
| Silver | Multi-Agent Demo Summary | v0.1.0 | Eight deterministically derived claims over the packaged harness evidence | `schemas/silver-multi-agent-demo-summary-v0.1.0.md` |
| Doc | Silver Multi-Agent Trust-Boundary Demo | v0.2.5 | Demo narrative document | `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md` |
| Doc | Gold Boundary | v0.2.5 | First explicit Gold boundary documentation (text-only; no Gold schema/validator/certificate) | `docs/gold/gold-boundary-v0.2.5.md` |

The packager:

- Invokes the v0.2.4 harness runner and evidence verifier as subprocesses (no v0.2.4 refactor).
- Derives eight required claims (`harmless_messages_proceed`, `protected_actions_require_scoped_authority`, `unauthorized_delegation_fails`, `bypass_attempts_blocked`, `revoked_authority_fails`, `out_of_scope_actions_fail`, `evidence_is_hash_verifiable`, `no_protected_actions_executed`) from the nested run report and transcript.
- Writes `demo-summary.json` and `demo-package-manifest.json` with four subjects in deterministic order.

The verifier recomputes SHA-256 for every package subject, validates the demo summary, cross-checks every claim against the nested run report and decision reports, and delegates nested evidence verification to the unchanged v0.2.4 verifier. Nested verifier failures are surfaced as the stable top-level reason `nested_harness_evidence_invalid`.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
```

v0.2.5 names the Gold boundary. It does not cross it. There is no Gold schema, validator, or certificate in this release. See `docs/gold/gold-boundary-v0.2.5.md`.

## v0.2.6 Update: Evidence Source Adapter Profile

Silver v0.2.6 adds an evidence source adapter descriptor profile. Six canonical static JSON descriptors declare how representative evidence sources map their outputs into ProofRail-relevant evidence fields. The descriptors are not evidence, not trust decisions, and not certifications.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Evidence Source Adapter Descriptor | v0.1.0 | Static declaration of how an evidence source maps to ProofRail-relevant fields | `schemas/silver-evidence-source-adapter-v0.1.0.md` |
| Doc | Silver Evidence Source Adapter Profile | v0.2.6 | Profile narrative document | `docs/silver/silver-evidence-source-adapter-profile-v0.2.6.md` |

Canonical descriptors (`examples/silver-evidence-source-adapters/`) cover six closed source types:

- `native_proofrail` — first-party ProofRail / Iron-plus / Bronze evidence emitter
- `gateway` — MCP / API / actuator gateway
- `observability_trace` — distributed trace collector
- `siem_log` — security log / correlator
- `policy_engine` — policy decision point
- `grc_platform` — governance / risk / compliance workflow source (explicitly framed as workflow approval evidence only, **not** technical enforcement)

The validator `tools/silver/validate_evidence_source_adapter_v0_1_0.py` is pure-stdlib and operates only on the parsed descriptor JSON. It rejects out-of-set source types, missing capabilities, missing `decision_event` mapping, empty/whitespace-only strings, sample-artifact-ref path traversal, and duplicate adapter IDs in directory mode.

The evidence chain is unchanged. Adapter descriptors sit **next to** Bronze claims and Silver bundles as static declarations of source-evidence shape, not above or below them. v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy.

## v0.2.7 Update: Composed Silver Demo Over Simulated Gateway Evidence

Silver v0.2.7 introduces a composed Silver demo built from a v0.2.6 simulated gateway adapter descriptor and a static JSONL gateway event fixture. The demo deterministically composes a ProofRail evidence package, computes hash anchors, derives ten claims, and is independently verified by a separate verifier.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Simulated Gateway Evidence Event | v0.1.0 | JSONL gateway event line schema for static fixtures | `schemas/silver-simulated-gateway-evidence-event-v0.1.0.md` |
| Silver | Composed Gateway Evidence Report | v0.1.0 | Composed report with ten derived claims over a gateway source | `schemas/silver-composed-gateway-evidence-report-v0.1.0.md` |
| Silver | Composed Gateway Evidence Manifest | v0.1.0 | SHA-256 manifest with deterministic subject order and `composition` block | `schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md` |
| Doc | Silver Composed Gateway Evidence Demo | v0.2.7 | Demo narrative document | `docs/silver/silver-composed-gateway-evidence-demo-v0.2.7.md` |

The composer (`tools/silver/compose_gateway_evidence_demo_v0_1_0.py`) subprocess-invokes the unchanged v0.2.6 adapter validator, validates the JSONL fixture, derives the ten required claims, and emits both the composed report and a manifest with five subjects in deterministic order plus a `composition` block.

The verifier (`tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py`) re-derives every claim independently from the copied adapter and JSONL, validates the manifest `composition` block, and rejects wrong-but-valid evidence refs.

The simulated gateway is an evidence source, not a trust authority. v0.2.7 demonstrates substrate-neutral evidence composition. It does not integrate with a real gateway or certify gateway enforcement. The composed report is not signed; v0.2.7 ships local hash anchors only.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
  → composed gateway evidence report + composed gateway evidence manifest
```

## v0.2.8 Update: Relying-Party Acceptance Record

Silver v0.2.8 introduces a local, hash-anchored relying-party acceptance record over a verified v0.2.7 composed gateway evidence package. The record binds a named local policy, declared purpose, verifier outcome, revocation review, exceptions, scope limitations, and challenge window. It is the first ProofRail artifact that explicitly names a relying-party decision.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Acceptance Policy | v0.1.0 | Static local policy declaring what a relying party will accept | `schemas/silver-relying-party-acceptance-policy-v0.1.0.md` |
| Silver | Relying-Party Acceptance Record | v0.1.0 | Local decision over a verified Silver evidence package | `schemas/silver-relying-party-acceptance-record-v0.1.0.md` |
| Silver | Relying-Party Acceptance Package Manifest | v0.1.0 | Three-subject hash anchor binding policy, evidence manifest, and record | `schemas/silver-relying-party-acceptance-package-manifest-v0.1.0.md` |
| Doc | Silver Relying-Party Acceptance Record | v0.2.8 | Release narrative document | `docs/silver/silver-relying-party-acceptance-record-v0.2.8.md` |

The generator (`tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`) subprocess-invokes the unchanged v0.2.7 verifier, derives the revocation review outcome from the sibling composed gateway evidence report's `revoked_authority_fails` claim, and refuses `--decision accepted` with `FAIL: evidence_verification_failed: <detail>` (exit 1) when v0.2.7 verification fails. The validator (`tools/silver/validate_relying_party_acceptance_record_v0_1_0.py`) runs 22 ordered hash-first checks against a 21-reason stable set and never emits the generator-only `evidence_verification_failed`. Three verification-related failure codes (`evidence_verification_required`, `evidence_verification_failed`, `external_evidence_verification_failed`) are deliberately distinct.

A relying-party acceptance record is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument. v0.2.8 records acceptance context. It does not execute acceptance governance.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
  → composed gateway evidence report + composed gateway evidence manifest
  → relying-party acceptance policy + acceptance record + acceptance package manifest
```

## v0.2.9 Update: Revocation/Challenge Drill

Silver v0.2.9 layers a deterministic, hash-anchored local revocation/challenge drill on top of a v0.2.8 relying-party acceptance package. The drill records post-acceptance review signals (challenges and revocation signals), classifies them against the acceptance record's policy-derived challenge window, and produces a single `recommended_local_posture` from a closed set. It does not adjudicate challenges, revoke acceptance, or execute Gold governance.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Review Event | v0.1.0 | JSONL event-line schema for post-acceptance review signals | `schemas/silver-relying-party-review-event-v0.1.0.md` |
| Silver | Revocation/Challenge Drill Report | v0.1.0 | Local report binding nested acceptance and classifying review events | `schemas/silver-revocation-challenge-drill-report-v0.1.0.md` |
| Silver | Revocation/Challenge Drill Manifest | v0.1.0 | Three-subject SHA-256 hash anchor binding nested acceptance manifest, review events, and drill report | `schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md` |
| Doc | Silver Revocation/Challenge Drill | v0.2.9 | Release narrative document | `docs/silver/silver-revocation-challenge-drill-v0.2.9.md` |

The runner (`tools/silver/run_revocation_challenge_drill_v0_1_0.py`) subprocess-invokes the unchanged v0.2.8 acceptance validator on the input package and refuses with `FAIL: acceptance_package_validation_failed: <detail>` (exit 1) when validation fails, or with `FAIL: review_fixture_insufficient: <detail>` (exit 1) when the fixture has zero within-window challenges or zero revocation signals. Output is staged in a sibling directory and atomically moved into place — a refused run leaves no partial drill package on disk. The full v0.2.8 package subdirectory is byte-copied under `acceptance-package/`; no v0.2.7 evidence package contents are duplicated.

The verifier (`tools/silver/verify_revocation_challenge_drill_v0_1_0.py`) delegates nested acceptance-package validation to the unchanged v0.2.8 validator (failures surface as `nested_acceptance_package_invalid`; v0.2.8's `external_evidence_verification_failed` is preserved as a distinct v0.2.9 reason when `--evidence-package-root` is supplied). It runs hash-first, re-derives the drill report's classification, findings, and triggers independently, and resolves 22 stable failure reasons. The runner-only codes `acceptance_package_validation_failed` and `review_fixture_insufficient` are never emitted by the verifier.

A revocation/challenge drill report is not a Gold certificate, regulator approval, third-party audit, legal revocation, dispute resolution, or acceptance governance workflow. v0.2.9 records review triggers. It does not decide their merits.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
  → composed gateway evidence report + composed gateway evidence manifest
  → relying-party acceptance policy + acceptance record + acceptance package manifest
  → relying-party review events + revocation/challenge drill report + drill manifest
```

## v0.3.0 Update: Silver Acceptance Handoff

ProofRail v0.3.0 is a composition release. It packages the completed v0.2.7 composed gateway evidence, v0.2.8 relying-party acceptance, and v0.2.9 revocation/challenge drill into a single portable, hash-anchored Silver acceptance handoff artifact. v0.3.0 introduces no new evidence content. It binds three already-verified Silver pipelines and lets the v0.3.0 verifier own and re-derive the cross-package binding end to end.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Acceptance Handoff Summary | v0.1.0 | Per-package summary recording included manifest hashes, record id, decision status, purpose, drill posture, derived handoff posture, and reuse warning | `schemas/silver-acceptance-handoff-summary-v0.1.0.md` |
| Silver | Acceptance Handoff Manifest | v0.1.0 | Four-subject SHA-256 hash anchor with fixed top-level layout and chain-binding cross-references | `schemas/silver-acceptance-handoff-manifest-v0.1.0.md` |
| Doc | Silver Acceptance Handoff | v0.3.0 | Release narrative document | `docs/silver/silver-acceptance-handoff-v0.3.0.md` |

The runner (`tools/silver/build_silver_acceptance_handoff_v0_1_0.py`) subprocess-invokes the unchanged v0.2.7, v0.2.8, and v0.2.9 validators **without** `--evidence-package-root`, so v0.3.0 alone owns the four chain-binding cross-checks. It byte-copies the three nested package roots into fixed top-level directories (`composed-gateway-evidence/`, `acceptance-package/`, `revocation-challenge-drill/`), maps the nested v0.2.9 `recommended_local_posture` onto a minimum handoff posture rank, runs self-validation against the staging directory **before** the atomic move, and refuses with one of five runner-only codes (`composed_evidence_validation_failed`, `acceptance_package_validation_failed`, `drill_package_validation_failed`, `handoff_chain_binding_failed`, `self_validation_failed`) on any failure.

The verifier (`tools/silver/verify_silver_acceptance_handoff_v0_1_0.py`) is hash-first, re-runs the unchanged nested validators as subprocesses, performs the same four v0.3.0-owned chain bindings, runs the record/purpose cross-checks, validates the closed-set posture rank, and runs a recursive overclaim guard over every summary string outside `scope_limitations` and `non_claims`. It resolves 17 stable failure reasons including `handoff_chain_binding_mismatch`, `handoff_posture_invalid`, `handoff_posture_downgrade`, and `handoff_overclaim`. The five runner-only refusal codes are deliberately distinct and never emitted by the verifier.

A Silver acceptance handoff package is not a certificate, Gold conformance, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge, legally revoked acceptance, or production authorization. The `recommended_handoff_posture` is descriptive, not a governance act. v0.3.0 packages already-verified Silver evidence. It does not extend the substance of what that evidence asserts.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
  → composed gateway evidence report + composed gateway evidence manifest
  → relying-party acceptance policy + acceptance record + acceptance package manifest
  → relying-party review events + revocation/challenge drill report + drill manifest
  → Silver acceptance handoff summary + handoff manifest
```

## v0.3.1 Update: Silver Handoff Inspector + Gold Gap Inventory

ProofRail v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable, producing a deterministic, hash-anchored review report that summarizes the verified chain, the carried-forward caution posture, and the unresolved Gold-boundary prerequisites. v0.3.1 introduces no new evidence source, signature scheme, trust authority, or runtime substrate. It introduces a single, deterministic, local inspection package.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Silver-to-Gold Requirement Set | v0.1.0 | Committed local 13-domain Gold-boundary requirement set with a four-status closed set | `schemas/silver-to-gold-requirement-set-v0.1.0.md` |
| Silver | Silver Handoff Inspection Report | v0.1.0 | Re-derived review report binding the nested v0.3.0 handoff to the requirement set, with recomputed gap counts and forced `gold_boundary_status` | `schemas/silver-handoff-inspection-report-v0.1.0.md` |
| Silver | Silver Handoff Inspection Manifest | v0.1.0 | Three-subject SHA-256 hash anchor (handoff manifest, requirement set, inspection report) | `schemas/silver-handoff-inspection-manifest-v0.1.0.md` |
| Doc | Silver Handoff Inspector + Gap Inventory | v0.3.1 | Release narrative document | `docs/gold/silver-handoff-inspector-and-gap-inventory-v0.3.1.md` |

The runner (`tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py`) subprocess-invokes the unchanged v0.3.0 handoff verifier and the v0.3.1 verifier in `--validate-requirement-set` mode, byte-copies the v0.3.0 handoff package root under `silver-acceptance-handoff/`, byte-copies the requirement set, re-derives the inspection report (`base_handoff`, `handoff_summary`, `component_inspection`, `gold_gap_inventory`), runs self-validation against the staging directory **before** the atomic move, and refuses with one of three runner-only codes (`handoff_validation_failed`, `requirement_set_validation_failed`, `inspection_self_validation_failed`) on any failure.

The verifier (`tools/silver/verify_silver_handoff_inspection_v0_1_0.py`) is hash-first, re-runs the unchanged v0.3.0 handoff verifier as a subprocess (failures surface as `nested_handoff_invalid`), re-validates the requirement set, and independently re-derives every field of the inspection report. It resolves 20 stable failure reasons including `inspection_handoff_summary_mismatch` (reserved for non-posture fields `acceptance_record_id`, `decision_status`, `purpose_id`), `inspection_review_posture_downgrade` (reserved for the posture path and reachable even when non-posture cross-checks pass), `requirement_duplicate`, `requirement_domain_missing`, `inspection_count_mismatch`, `inspection_gold_status_invalid`, and `inspection_gold_overclaim`. The three runner-only refusal codes are deliberately distinct and never emitted by the verifier.

The requirement set covers exactly 13 governance domains and one of four statuses per row: `silver_evidence_present` (Silver evidence is present at this domain), `silver_evidence_partial` (Silver provides only a drill or local artifact), `gold_prerequisite_unmet` (Silver does not address this domain), `out_of_scope_for_silver` (domain is outside any ProofRail Silver scope). The report-level `gold_boundary_status` is forced to `gold_not_claimed` whenever any row is partial / unmet / out-of-scope. `silver_evidence_present` means relevant Silver evidence is present inside the ProofRail Silver chain. It does **not** mean the corresponding Gold prerequisite is satisfied.

A Silver handoff inspection package is not a Gold certificate, Gold readiness assessment, regulator approval, auditor approval, legal acceptance, transferred reliance, adjudicated challenge resolution, or production authorization. The bound Gold-boundary requirement set is a local ProofRail demo inventory, not an external compliance standard.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
  → verifier output attestation
  → multi-principal authority decision reports
  → multi-agent harness transcript + run report + evidence manifest
  → multi-agent trust-boundary demo package manifest + demo summary
  → composed gateway evidence report + composed gateway evidence manifest
  → relying-party acceptance policy + acceptance record + acceptance package manifest
  → relying-party review events + revocation/challenge drill report + drill manifest
  → Silver acceptance handoff summary + handoff manifest
  → Gold-boundary requirement set + Silver handoff inspection report + inspection manifest
  → trace events + trace claim binding set + Silver trace binding report + trace binding manifest
```

## v0.3.2 Update: Silver Trace Binding Profile

ProofRail v0.3.2 binds protected-action claims to deterministic trace event evidence anchored to the unchanged v0.2.6 simulated observability-trace adapter descriptor, producing a hash-anchored four-subject package whose every field a Silver reviewer can independently re-derive. v0.3.2 introduces no new signature scheme, trust authority, or runtime substrate. It introduces a single, deterministic, local trace binding package.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Silver Trace Event | v0.1.0 | JSONL trace event record with closed `decision` enum `{allow, deny, observe, block}` | `schemas/silver-trace-event-v0.1.0.md` |
| Silver | Silver Trace Claim Binding Set | v0.1.0 | Binding rows with closed `expected_binding_status` enum `{bound, bound_with_warning, trace_gap_detected, out_of_scope_for_trace_binding}` and per-row `required_*` fields | `schemas/silver-trace-claim-binding-set-v0.1.0.md` |
| Silver | Silver Trace Binding Report | v0.1.0 | Deterministically derived report whose `binding_summary` counts are recomputed from `bindings[].binding_status` and never hand-authored | `schemas/silver-trace-binding-report-v0.1.0.md` |
| Silver | Silver Trace Binding Manifest | v0.1.0 | Four-subject SHA-256 hash anchor in fixed order (adapter, trace events, binding set, trace binding report) | `schemas/silver-trace-binding-manifest-v0.1.0.md` |
| Doc | Silver Trace Binding Profile | v0.3.2 | Release narrative document | `docs/silver/silver-trace-binding-profile-v0.3.2.md` |

The runner (`tools/silver/build_silver_trace_binding_v0_1_0.py`) performs a structural trust-authority pre-check on the adapter BEFORE the v0.2.6 adapter validator subprocess (Amendment 1), validates the trace events JSONL under strict `(event_time, event_id)` ordering with unique `event_id` and unique `(trace_id, span_id)`, validates the binding set under closed enums, cross-checks every non-gap binding row against its resolved trace event so only `trace_gap_detected` rows may reference an absent event (Amendment 4), runs self-validation against the staging directory **before** the atomic `os.replace()`, and refuses with one of four runner-only codes (`adapter_validation_failed`, `trace_events_validation_failed`, `trace_binding_set_validation_failed`, `trace_binding_self_validation_failed`) on any failure.

The verifier (`tools/silver/verify_silver_trace_binding_v0_1_0.py`) is hash-first and runs 22 stable failure reasons. Two reachability orderings are intentional: `trace_source_marked_authority` is checked BEFORE the v0.2.6 adapter validator subprocess so a tampered adapter is always attributed to the specific reason; `trace_warning_downgrade` is checked BEFORE the generic `trace_report_status_mismatch` so downgrades of `bound_with_warning` / `trace_gap_detected` / `out_of_scope_for_trace_binding` to `bound` are always attributed to the more specific reason. Path traversal is checked BEFORE exact subject-path equality. `scope_limitations` and `non_claims` emptiness checks are reserved for the dedicated `trace_limitations_missing` and `trace_non_claims_missing` reasons. The recursive overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 22 forbidden positive tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance`. The four runner-only refusal codes are deliberately distinct and never emitted by the verifier.

A Silver trace binding package is not a Gold certificate, OpenTelemetry conformance claim, production observability claim, regulator approval, third-party audit, legal acceptance, compliance certification, or production authorization. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority. `source_event_ref` values are opaque labeled strings and v0.3.2 does not cross-validate them against any external package. v0.3.2 binds protected-action claims to deterministic trace evidence for independent Silver review. It does not prove runtime truth.

## v0.3.3 Update: Silver Adapter Pilot Package

ProofRail v0.3.3 pilots a local external-evidence adapter flow that normalizes an OpenTelemetry-shaped local source-export fixture into ProofRail v0.3.2 trace-binding inputs under a declarative, evidence-only mapping. v0.3.3 introduces no new signature scheme, trust authority, or runtime substrate. It introduces a single, deterministic, local adapter pilot package with seven hash-anchored subjects in fixed order.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Silver Adapter Pilot Source Export | v0.1.0 | JSONL OpenTelemetry-shaped local source-export fixture with closed `export_format = "proofrail.simulated_otel_trace_export.v0.1"` and closed `proofrail.decision` enum | `schemas/silver-adapter-pilot-source-export-v0.1.0.md` |
| Silver | Silver Adapter Pilot Normalization Map | v0.1.0 | Declarative mapping from source-export records to v0.3.2 trace events; admits only `<source.dot.path>` and `"constant:<literal>"` values; dot-path resolution uses longest-prefix key matching | `schemas/silver-adapter-pilot-normalization-map-v0.1.0.md` |
| Silver | Silver Adapter Pilot Report | v0.1.0 | Deterministically derived report whose seven required claims are pre-baked with `status: pass` and whose `source_is_trust_authority` / `runtime_truth_claimed` flags are forced | `schemas/silver-adapter-pilot-report-v0.1.0.md` |
| Silver | Silver Adapter Pilot Manifest | v0.1.0 | Seven-subject SHA-256 hash anchor in fixed order (adapter / source export / normalization map / normalized trace events / normalized trace claim bindings / nested v0.3.2 manifest / adapter pilot report) | `schemas/silver-adapter-pilot-manifest-v0.1.0.md` |
| Doc | Silver Adapter Pilot Package | v0.3.3 | Release narrative document | `docs/silver/silver-adapter-pilot-package-v0.3.3.md` |

The runner (`tools/silver/build_silver_adapter_pilot_v0_1_0.py`) performs a structural trust-authority pre-check on the adapter BEFORE the v0.2.6 adapter validator subprocess, subprocess-invokes the unchanged v0.2.6 adapter validator and the unchanged v0.3.2 trace-binding builder with `--force --self-validate`, stages every byte under `<output-dir>.staging.<pid>`, runs self-validation against the staging directory **before** the atomic `os.replace()`, and refuses with one of six runner-only codes (`adapter_validation_failed`, `source_export_validation_failed`, `normalization_map_validation_failed`, `binding_set_validation_failed`, `nested_trace_binding_generation_failed`, `adapter_pilot_self_validation_failed`) on any failure. A refused run leaves no final directory and no staging sibling, so the Make target is safely repeatable.

The verifier (`tools/silver/verify_silver_adapter_pilot_v0_1_0.py`) is hash-first and runs 24 stable failure reasons across 25 ordered checks. Four reachability orderings are intentional: (a) path traversal is checked BEFORE exact subject-path equality so absolute or `..` subjects are always attributed to `adapter_pilot_subject_path_traversal`; (b) the adapter trust-authority pre-check runs BEFORE the v0.2.6 adapter validator subprocess so a tampered adapter is always attributed to `adapter_pilot_source_marked_authority`; (c) re-derived normalized bytes are compared against packaged normalized bytes BEFORE the nested v0.3.2 verifier subprocess so a normalization disagreement is always attributed to `normalized_trace_mismatch`; (d) the nested v0.3.2 verifier subprocess runs BEFORE the nested-manifest hash cross-check pairing outer subjects [0]/[3]/[4] with nested subjects [0]/[1]/[2], so a corrupted nested manifest is attributed to `nested_trace_binding_invalid` first. `scope_limitations` and `non_claims` emptiness checks are reserved for the dedicated `adapter_pilot_limitations_missing` and `adapter_pilot_non_claims_missing` reasons. The recursive overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 23 forbidden positive tokens including `runtime truth proved`, `opentelemetry conformance`, `vendor certified`, and `production approved`. The six runner-only refusal codes are deliberately distinct and never emitted by the verifier.

A Silver adapter pilot package is not a Gold certificate, OpenTelemetry conformance claim, vendor certification, production integration, regulator approval, third-party audit, legal acceptance, compliance certification, or production authorization. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority. The OpenTelemetry-shaped envelope uses the explicit `export_format: "proofrail.simulated_otel_trace_export.v0.1"` so the fixture cannot be confused with a real vendor export. `source_event_ref` strings are opaque labels carried unchanged through normalization; v0.3.3 does not cross-validate them against any external package. v0.3.3 pilots a local adapter flow. It does not perform a real OpenTelemetry, vendor, observability, SIEM, GRC, gateway, policy-engine, or ticketing-system integration, and it does not extend the substance of any earlier-release Silver evidence.

## v0.3.4 Update: Silver Challenge / Withdrawal Record Primitives

ProofRail v0.3.4 layers two structurally validated, hash-bound local records over an unchanged v0.3.0 acceptance handoff target: a challenge record (closed `challenge_reason` enum, 10 values; closed `challenge_status` enum, 4 values) and a withdrawal record (closed `withdrawal_reason` enum, 7 values; closed `withdrawal_status` enum, 4 values; closed `withdrawal_effect` enum, 4 values). v0.3.4 introduces no new signature scheme, trust authority, runtime substrate, or adjudication. It introduces a single, deterministic, local challenge / withdrawal primitives package with four hash-anchored subjects in fixed order.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Silver Challenge Record | v0.1.0 | Structurally validated local challenge record hash-bound to a v0.3.0 acceptance handoff target with a closed reason / status vocabulary | `schemas/silver-challenge-record-v0.1.0.md` |
| Silver | Silver Withdrawal Record | v0.1.0 | Structurally validated local withdrawal record hash-bound to the same v0.3.0 target with a closed reason / status / effect vocabulary and a closed `related_challenge_record_id` link | `schemas/silver-withdrawal-record-v0.1.0.md` |
| Silver | Silver Challenge / Withdrawal Summary | v0.1.0 | Deterministically derived summary whose seven required claims are pre-baked with `status: pass` and whose `posture` is forced from the closed `withdrawal_effect → posture` mapping table | `schemas/silver-challenge-withdrawal-summary-v0.1.0.md` |
| Silver | Silver Challenge / Withdrawal Manifest | v0.1.0 | Four-subject SHA-256 hash anchor in fixed order (target handoff manifest / challenge record / withdrawal record / challenge-withdrawal summary) | `schemas/silver-challenge-withdrawal-manifest-v0.1.0.md` |
| Doc | Silver Challenge / Withdrawal Record Primitives | v0.3.4 | Release narrative document | `docs/silver/silver-challenge-withdrawal-primitives-v0.3.4.md` |

The runner (`tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py`) subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier against the target handoff manifest, structurally validates the input challenge and withdrawal records (accepting the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in the input fixtures only), performs four binding cross-checks against the parsed v0.3.0 handoff manifest (both records' `target.target_record_id` equal the v0.3.0 `handoff_id`; withdrawal's `related_challenge_record_id` equals challenge's `challenge_record_id`; the time-order chain `target.generated_at ≤ challenge.filed_at ≤ withdrawal.recorded_at ≤ withdrawal.effective_at` is monotone; both records' `target.target_manifest_path` equal the packaged subject [0] path), stages every byte under `<output-dir>.staging.<pid>`, byte-copies the v0.3.0 handoff package root into `target-handoff/`, recomputes the SHA-256 of the copied target manifest and rewrites the placeholder in both packaged record copies under `records/` to that recomputed hash label, derives the summary deterministically, runs self-validation against the staging directory **before** the atomic `os.replace()`, and refuses with one of five runner-only codes (`handoff_validation_failed`, `challenge_record_validation_failed`, `withdrawal_record_validation_failed`, `challenge_withdrawal_binding_failed`, `challenge_withdrawal_self_validation_failed`) on any failure. A refused run leaves no final directory and no staging sibling, so the Make target is safely repeatable.

The verifier (`tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py`) is hash-first and runs 24 stable failure reasons across 29 ordered checks (manifest structural failures throughout steps 1–9 share `invalid_challenge_withdrawal_manifest`; step 29 covers both `_limitations_missing` and `_non_claims_missing`; no OR-accept). Path traversal is checked BEFORE exact subject-path equality so absolute or `..` subjects are always attributed to `challenge_withdrawal_subject_path_traversal`. The presence-only structural record validators run BEFORE the dedicated `*_reason_invalid` / `*_status_invalid` / `*_evidence_ref_invalid` / `*_target_mismatch` checks so enum / evidence-ref / target failures never collapse into the generic `*_record_invalid` reason; the structural validators accept `sha256:TO_BE_BOUND_BY_RUNNER` as a syntactically valid value and the dedicated `challenge_record_target_mismatch` / `withdrawal_record_target_mismatch` checks (each consolidating placeholder-unbound + target manifest sha256 drift + target record id drift) reject it in packaged records. The closed `withdrawal_effect → posture` table collapses `acceptance_reuse_blocked_pending_review` onto `challenged_with_local_reuse_paused_for_review` and leaves `record_superseded` unchanged. `scope_limitations` and `non_claims` emptiness checks are reserved for the dedicated `challenge_withdrawal_limitations_missing` and `challenge_withdrawal_non_claims_missing` reasons. The recursive overclaim guard scans every string value outside `scope_limitations` and `non_claims` (including the optional `claim.description` field) for forbidden positive tokens including `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, and `production-approved`. The five runner-only refusal codes are deliberately distinct and never emitted by the verifier.

A Silver challenge / withdrawal primitives package is not an adjudication, legal revocation of reliance, target-handoff certification, Gold certificate, regulator approval, third-party audit, legal acceptance, compliance certification, or production authorization. The challenge record's free-text `challenge_reason_description` and counterparty references are not verified for substantive truth by v0.3.4. The withdrawal record's `withdrawal_effect` describes the filer's local posture only; it does not constitute legal revocation of any prior acceptance instrument. v0.3.4 records challenge / withdrawal primitives. It does not decide their merits, and it does not extend the substance of any earlier-release Silver evidence.

## v0.3.5 Update: Silver Relying-Party Policy Pack

ProofRail v0.3.5 introduces a deterministic local Silver evidence primitive — a hand-authored relying-party policy pack — paired with a byte-for-byte re-derivable conformance report and a 2-subject manifest. v0.3.5 introduces no new signature scheme, trust authority, runtime substrate, or evaluation of any specific upstream Silver evidence. It introduces a single, deterministic, local Relying-Party Policy Pack package with two hash-anchored subjects in fixed order.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Silver Relying-Party Policy Pack | v0.1.0 | Hand-authored local policy pack declaring the relying party's Silver acceptance posture under a closed enum vocabulary | `schemas/silver-relying-party-policy-pack-v0.1.0.md` |
| Silver | Silver Relying-Party Policy Pack Manifest | v0.1.0 | 2-subject SHA-256 hash anchor in fixed order (policy pack / conformance report) | `schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md` |
| Silver | Silver Relying-Party Policy Pack Conformance Report | v0.1.0 | Re-derivable conformance record with 24 pass entries, one per approved verifier check; canonical-JSON byte image depends only on the policy pack | `schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md` |
| Doc | Silver Relying-Party Policy Pack | v0.3.5 | Release narrative document | `docs/silver/silver-relying-party-policy-pack-v0.3.5.md` |

The runner (`tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py`) runs five Phase A preflight checks against `--policy-pack` (each emitting a single, distinct, runner-only refusal reason: `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`); Phase A never touches the output directory or staging sibling. The runner then stages every byte under `<output-dir>.staging.<pid>`, byte-copies the policy pack to `<staging>/silver-relying-party-policy-pack.json`, deterministically re-derives the 24-entry conformance report as canonical JSON bytes, writes the 2-subject manifest, runs self-validation against the staging directory **before** the atomic `os.replace()`, and (on `--self-validate` failure) **relays the v0.3.5 verifier's OWN failure reason UNCHANGED** — the runner never wraps a verifier failure in a sixth runner-only code. A refused or self-validation-failed run leaves no final directory and no staging sibling, so the Make target is safely repeatable.

The verifier (`tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py`) is non-masking and runs 24 stable failure reasons across 24 ordered checks: `policy_pack_manifest_invalid`, `policy_pack_not_object`, `policy_pack_schema_invalid`, `policy_pack_profile_unsupported`, `policy_pack_identity_invalid`, `policy_pack_authority_invalid`, `policy_scope_invalid`, `protected_action_scope_invalid`, `silver_handoff_requirement_invalid`, `verifier_requirement_invalid`, `issuer_requirement_invalid`, `revocation_requirement_invalid`, `freshness_requirement_invalid`, `challenge_requirement_invalid`, `withdrawal_requirement_invalid`, `supersession_requirement_invalid`, `acceptance_criteria_invalid`, `rejection_criteria_invalid`, `exception_policy_invalid`, `hard_stop_policy_invalid`, `warning_policy_invalid`, `reference_policy_invalid`, `non_claims_missing`, `prohibited_claim_present`. All 22 dedicated structural checks run BEFORE the bundled conformance report is parsed and byte-compared against the deterministic re-derivation, so dedicated subject [0] failures are never masked behind a downstream report-disagreement reason. Bundled-report byte disagreement folds back to `policy_pack_manifest_invalid` (the bundled report does not describe a passing verification of this policy pack). `scope_limitations` and `non_claims` emptiness checks are reserved for the dedicated `non_claims_missing` reason. The recursive overclaim guard scans every string value outside `scope_limitations`, `non_claims`, and `relying_party.contact` for 23 forbidden positive tokens including `certified`, `approved`, `audited`, `compliance`, `regulator approved`, `auditor approved`, `gold accepted`, `gold certified`, `gold governed reliance`, `legally accepted`, `legally revoked`, `legally binding`, `production approved`, `production-ready`, `risk approved`, `trust transferred`, `challenge resolved`, and `withdrawal resolved`. The five runner-only refusal codes are deliberately distinct and never emitted by the verifier.

A Silver Relying-Party Policy Pack package is not regulator approval, auditor approval, third-party endorsement, certification, a Gold artifact, an adjudication, an evidence-evaluation result, legally binding, or production authorization. The packaged conformance report describes only that the policy pack satisfies the 24 ordered structural checks; it does not describe a substantive review of any specific upstream Silver evidence in this release. v0.3.5 packages a hand-authored relying-party policy declaration alongside a re-derivable structural-conformance report. It does not evaluate any specific upstream handoff, verifier, issuer, evidence package, challenge, withdrawal, supersession, or warning event against the policy, and it does not extend the substance of any earlier-release Silver evidence.
