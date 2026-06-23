# ProofRail Silver v0.1.7 Limitations and Non-Claims

**Suggested repo path:** `docs/reference/silver-limitations-and-non-claims.md`  
**Status:** Reviewed reference note  
**Applies to:** ProofRail v0.1.7 and pre-v0.2.0 planning

---

## Purpose

This note defines what ProofRail Silver does and does not claim at the v0.1.7 stage.

Its purpose is to prevent overclaiming as the Silver machinery becomes more formal.

---

## Core Silver Claim

At v0.1.7, the defensible claim is:

> ProofRail demonstrates that a Bronze evidence package can be checksummed, bundled, signed, locally revoked, verified, reported, exported, and independently re-verified by a local relying-party verifier.

More compactly:

> Silver means signed, revocable, reportable, independently verifiable evidence-package reliance.

---

## What Silver v0.1.7 Does Claim

Silver v0.1.7 demonstrates the following:

1. A Bronze evidence bundle manifest can be signed.
2. The signature is over the raw bytes of the bundle manifest.
3. A verifier can check issuer trust using a local trust policy.
4. A verifier can check assertion expiry.
5. A verifier can check bundle-manifest integrity.
6. A verifier can check revocation by assertion ID, issuer key, or bundle hash.
7. A verifier can verify the underlying Bronze evidence bundle.
8. A verifier can emit a structured Silver Verification Report.
9. An independent verifier package can perform the same local verification outside the original source tree.

---

## What Silver Does Not Claim

Silver does **not** mean:

```text
certified safe
regulator-approved
production-grade PKI
third-party audited
publicly accredited
legally certified
Gold certified
production deployment assured
```

Silver does not certify that a live AI system is safe.

Silver does not certify that evidence files are truthful.

Silver does not certify that a deployment is correctly configured in production.

Silver does not certify that a party has legal authority to operate the system.

Silver verifies a package and records a relying-party verification decision.

---

## Specific Non-Claims

### No Production PKI

The demo uses Ed25519 keys and local trust policies.

It does not implement:

- certificate authorities;
- X.509;
- OCSP;
- public CRLs;
- hardware-backed keys;
- cloud KMS;
- enterprise key lifecycle management.

### No Public Revocation Infrastructure

The Silver Revocation List v0.1.0 demonstrates local relying-party revocation.

It does not implement:

- public revocation registries;
- transparency-log-backed revocation;
- regulator-backed revocation;
- signed revocation lists;
- distributed revocation propagation.

### No Third-Party Certification

A Silver verifier can be independent from the original source tree, but that does not make it a third-party certifier.

Silver does not claim:

- external audit;
- accredited assessment;
- legal certification;
- regulator acceptance.

### No Gold Governance

Gold will require governed certification decisions, authorized certifiers, defined review profiles, challenge paths, and revocation of certification decisions.

Silver stops earlier:

```text
Silver = relying-party verification
Gold = governed acceptance / certification decision
```

### No Production Deployment Assurance

The current demos use local evidence and test fixtures.

They do not prove:

- production configuration;
- production monitoring;
- production incident response;
- production control operation;
- complete enterprise control coverage.

---

## Correct Language to Use

Use:

```text
ProofRail v0.1.7 demonstrates a reproducible local evidence chain from Bronze control evidence to signed, revocable, independently verifiable Silver evidence packages.
```

Use:

```text
Silver v0.1.7 verification means the evidence package passed defined verifier checks under a local relying-party policy.
```

Avoid:

```text
ProofRail certifies the system is safe.
```

Avoid:

```text
The deployment is Gold certified.
```

Avoid:

```text
This is regulator-grade assurance.
```

Avoid:

```text
This proves production conformance.
```

---

## v0.2.0 Silver Relying-Party Profile

Silver v0.2.0 formalizes the relying-party verification profile. The profile defines:

- what inputs a relying-party verifier must receive;
- what checks it must perform;
- what failure modes must be recognized;
- what report must be produced;
- what revocation means (mode-dependent);
- what independence means (structural checks, not execution assertion);
- what limitations must accompany any Silver acceptance.

The profile preserves this distinction:

> Silver is verifiable reliance on an evidence package, not certification of a live system.

Silver profile conformance is local demo conformance. It does not constitute Gold certification, third-party certification, regulatory approval, production PKI, production deployment assurance, or audit opinion.

See `profiles/silver/SILVER_PROFILE_v0.2.0.md` for the full profile specification.

## v0.2.1 Silver Profile Tightening

Silver v0.2.1 tightens revocation requirements for the `silver.base` mode. In v0.2.0, `silver.base` allowed revocation absence with a warning path. In v0.2.1, `silver.base` requires revocation — if revocation is not performed, the profile fails.

The v0.2.0 warning path is preserved in a new `silver.base.demo` mode for demo and development workflows.

This change reflects the principle that ordinary Silver reliance should include revocation checking. The demo mode exists to support development workflows where revocation infrastructure may not be configured.

See `profiles/silver/SILVER_PROFILE_v0.2.1.md` for the full v0.2.1 profile specification.

## v0.2.2 Verifier Output Attestation

Silver v0.2.2 adds detached, signed attestations over verifier outputs. This makes Silver verification outputs attributable and tamper-evident.

Verifier output attestation is:

- **attribution**: it records which verifier produced which outputs;
- **tamper evidence**: it detects modification of verification reports and conformance reports.

Verifier output attestation is **not**:

- certification of the underlying evidence or deployment;
- Gold certification;
- regulator approval;
- production PKI;
- production deployment assurance;
- third-party audit.

The attestor key is separate from the issuer key. Both use Ed25519 in demo mode but serve different roles. Subject paths containing `..` components are rejected by both the signer and verifier.

## v0.2.3 Multi-Principal Authority Fixtures

Silver v0.2.3 adds deterministic multi-principal authority fixtures. The authority evaluator processes structured requests against scoped, delegation-aware, revocation-aware authority grants and emits decision reports.

Multi-principal authority fixtures are:

- **scoped authority evaluation**: principals hold authority only for declared scopes with declared constraints;
- **delegation-aware**: authority can be narrowly delegated; weakening is rejected;
- **revocation-aware**: authority can be withdrawn at a specific point in time;
- **deterministic**: evaluation is local, against a fixture, with an explicit decision time.

Multi-principal authority fixtures are **not**:

- a live multi-agent runtime;
- prompt-injection detection;
- model behavior evaluation;
- production authorization infrastructure;
- Gold certification;
- a replacement for OAuth, RBAC, or enterprise IAM.

Every decision report includes `execution.performed == false`, providing structural proof that no actuator was invoked.

Silver v0.2.3 makes multi-principal authority executable as deterministic local fixtures. It does not make agents trustworthy or certify a deployment.

## v0.2.4 Multi-Agent Attack Harness Evidence

Silver v0.2.4 adds a deterministic, scripted multi-principal agent attack harness that consumes the v0.2.3 fixture and the unchanged authority evaluator and produces local harness evidence: a transcript, per-event protected action requests and decision reports, a structured run report, and a SHA-256 evidence manifest.

The harness is:

- **deterministic**: scripted events, ordered execution, fixed inputs;
- **multi-principal**: events drive multiple principals (buyer agent, vendor agent, verifier auditor);
- **non-executing**: protected actions are never performed; the run report and every decision report carry structural execution proof;
- **evidence-only**: outputs are local, hash-anchored, and verifiable by an independent verifier tool.

The harness is **not**:

- a live multi-agent runtime;
- a prompt-injection detector;
- a model behavior evaluation;
- a network-driven actuator harness;
- a Gold conformance claim;
- a signed evidence artifact (the manifest is unsigned local integrity evidence).

Bypass events are harness-level only: they record `bypass_blocked` with reason `bypass_attempt_detected`, without invoking the authority evaluator and without producing a request or decision report. Revocation marker events do not mutate the fixture; subsequent events' decision times drive revocation semantics through the unchanged evaluator.

The evidence verifier rejects subject paths containing `..`, recomputes SHA-256 of every subject, and confirms the run report and every decision report carry `execution.protected_actions_performed == false` / `execution.performed == false`.

Silver v0.2.4 makes a multi-principal attack scenario reproducible as local evidence. It does not constitute red-teaming, attestation of safety, or certification of any deployment.

## v0.2.5 Multi-Agent Trust-Boundary Demo

Silver v0.2.5 packages the v0.2.4 harness evidence into a local multi-agent trust-boundary demo with eight deterministically derived claims, a hash-anchored package manifest, and the first explicit Gold boundary documentation.

The v0.2.5 demo is:

- **a re-packaging of v0.2.4 evidence**: the packager invokes the unchanged v0.2.4 harness runner and verifier as subprocesses; no v0.2.3 or v0.2.4 semantics are mutated;
- **deterministic**: claims are derived from the v0.2.4 run report and transcript by fixed rules; the package manifest hashes four subjects in fixed order;
- **hash-anchored**: every package subject is SHA-256-checksummed, and the nested v0.2.4 manifest is re-verified by the unchanged v0.2.4 verifier;
- **non-executing**: the eighth required claim `no_protected_actions_executed` is structurally anchored to `harness-run-report.json` with `execution.protected_actions_performed == false`;
- **stable-failure-reasoned**: ten stable top-level failure reasons cover the verifier surface, including `nested_harness_evidence_invalid` for any nested v0.2.4 failure.

The v0.2.5 demo is **not**:

- a live multi-agent system;
- a live actuator harness;
- a natural-language prompt parser;
- a prompt-injection detector;
- a signed evidence artifact (the package manifest is unsigned local integrity evidence);
- a Gold certification, accreditation, regulator approval, or third-party audit;
- a re-implementation of v0.2.4 — it delegates to the unchanged v0.2.4 verifier.

### First Explicit Gold Boundary

v0.2.5 publishes the first explicit Gold boundary documentation: `docs/gold/gold-boundary-v0.2.5.md`.

The key claim:

> v0.2.5 names the Gold boundary. It does not cross it.

There is no Gold schema, no Gold validator, no Gold certificate, no governing body, no certification process, and no governed-acceptance workflow in v0.2.5. The Gold boundary document exists so that later releases can address Gold explicitly rather than by implication.

---

## v0.2.6 Evidence Source Adapter Profile

Silver v0.2.6 adds an evidence source adapter descriptor profile: a structured way for an evidence source (gateway, observability trace system, SIEM, policy engine, GRC platform, or native ProofRail tooling) to declare how its records map into ProofRail-relevant evidence fields.

The v0.2.6 profile is:

- A schema, six canonical static JSON descriptors, and a pure-stdlib structural validator.
- A local, deterministic descriptor check (`tools/silver/validate_evidence_source_adapter_v0_1_0.py`).
- A statement of capability presence/absence per source, including explicit limitation strings for non-provided capabilities.
- A statement of `adapter_limitations` and `non_claims` per descriptor.

The v0.2.6 profile is **not**:

- Evidence by itself. A descriptor declares how an adapter would emit evidence; it is not evidence.
- A trust decision. `trust_boundary.source_is_trust_authority` must be exactly `false`. The descriptor's `proofrail_role` is `evidence_source`.
- A certification. The descriptors do not certify any real gateway, observability stack, SIEM, policy engine, or GRC platform.
- A runtime integration. Descriptors are static documents. No vendor APIs are called and no external logs are read.
- A claim that a declared source actually behaves as described. The validator only checks the descriptor shape.
- A claim that workflow approval is technical enforcement. The GRC platform descriptor is explicitly framed as workflow / risk / approval evidence only; its limitations state that workflow approval is **not technical enforcement** and **not sufficient by itself** for protected-action reliance — technical decision evidence from a gateway, policy engine, or native ProofRail run is required.

The key claim:

> v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy.

ProofRail is not the gateway, not the SIEM, not the policy engine, and not the GRC platform. v0.2.6 records what each kind of source contributes to ProofRail evidence and, just as importantly, what it explicitly does not assert.

---

## v0.2.7 Composed Silver Demo Over Simulated Gateway Evidence

Silver v0.2.7 introduces a composed Silver demo built from a v0.2.6 simulated gateway adapter descriptor and a static JSONL fixture of nine gateway evidence events. The composer deterministically produces an evidence package; an independent verifier re-derives every claim from the copied adapter and JSONL.

The v0.2.7 demo is:

- **A composition demo**: a v0.2.6 adapter descriptor and a JSONL gateway event fixture become a hash-anchored ProofRail evidence package with a derived report and ten required claims.
- **Substrate-neutral**: the composer and verifier do not depend on any real gateway, SIEM, observability stack, policy engine, or GRC platform.
- **Hash-first verifiable**: the verifier rejects subject path traversal, missing subjects, hash mismatches, and a `composition` block that does not match the deterministic package layout before any semantic check.
- **Re-derivation-based**: the verifier re-derives every required claim independently, including wrong-but-valid evidence reference rejection (for example, a bypass claim that points at the harmless message event).
- **Non-executing**: every event has `execution.performed == false`; the report sets `execution.protected_actions_performed == false`; an `execution_violation` reason is reserved for any breach.

The v0.2.7 demo is **not**:

- An integration with any real MCP gateway, SIEM, observability stack, policy engine, or GRC platform.
- A certification that any real product behaves like the simulated fixture.
- A claim that the gateway is a trust authority. The adapter declares `source_is_trust_authority == false`; the manifest `composition` block restates this.
- A signed Silver artifact. The composed report is not signed; v0.2.7 ships local hash anchors only.
- A relying-party acceptance record (that is v0.2.8 work).
- A change to Bronze, Silver Signed Bundle Assertion, Revocation List, Verification Report, Profile, Verifier Output Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary Demo, or Evidence Source Adapter semantics.

The key claim:

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not integrate with a real gateway or certify gateway enforcement.

The simulated gateway is an evidence source, not a trust authority. Composed Silver evidence is not Gold acceptance, production assurance, compliance, or certification.

---

## v0.2.8 Relying-Party Acceptance Record

Silver v0.2.8 introduces a deterministic local relying-party acceptance record over a verified v0.2.7 composed gateway evidence package. The record binds a named local acceptance policy, a declared purpose, the v0.2.7 verifier outcome, a revocation review derived from the v0.2.7 report's `revoked_authority_fails` claim, exceptions, scope limitations, and a challenge window.

The v0.2.8 record is:

- **A local acceptance artifact**: a single named (fictional) relying party records its own decision (`accepted`, `rejected`, or `accepted_with_exceptions`) over a *verified* v0.2.7 evidence manifest.
- **Hash-anchored**: a three-subject package manifest binds the policy, the copied evidence manifest, and the record, all under SHA-256, with subject paths refused if they contain `..` or are absolute.
- **Bound to verification**: for `--decision accepted`, the generator refuses with `FAIL: evidence_verification_failed: <detail>` (exit 1) when the v0.2.7 verifier fails; the validator emits `accepted_record_verification_failed` for an accepted record whose recorded `verification_result` is not `pass`.
- **Optionally externally re-verifiable**: the validator's `--evidence-package-root` flag re-invokes the v0.2.7 verifier and re-checks the original package's manifest sha256, emitting `external_evidence_verification_failed` on disagreement.

The v0.2.8 record is **not**:

- A Gold certificate. A relying-party acceptance record is local, single-party, unsigned, and bound to a fictional demo policy. It does not certify the evidence, the system, the gateway, the policy, or the relying party.
- A regulator approval, third-party audit, or legal acceptance instrument. v0.2.8 records *one* relying party's local decision. It does not chain decisions, does not coordinate parties, and does not invoke any governance authority.
- A signed acceptance artifact. v0.2.8 ships local hash anchors only.
- A claim about any real relying party. The fixture relying party (`demo.relying_party`) is fictional.
- A change to Bronze, Silver Signed Bundle Assertion, Revocation List, Verification Report, Profile, Verifier Output Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary, Evidence Source Adapter, or Composed Gateway Evidence semantics.

The key claim:

> v0.2.8 records a relying party's local acceptance decision over verified Silver evidence. It does not certify the evidence, the system, the gateway, or the relying party.

A relying-party acceptance record is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument. v0.2.8 records acceptance context. It does not execute acceptance governance.

---

## v0.2.9 Revocation/Challenge Drill

Silver v0.2.9 layers a deterministic, hash-anchored local revocation/challenge drill on top of a v0.2.8 relying-party acceptance package. The drill consumes a static JSONL fixture of post-acceptance review signals (challenges, revocation signals, and acceptance revalidations), classifies them against the acceptance record's policy-derived challenge window, derives required findings and review triggers, and selects a single `recommended_local_posture` from a closed set.

The v0.2.9 drill is:

- **A post-acceptance review evidence artifact**: the drill records that review signals were detected, classified, and bound to a specific v0.2.8 acceptance package; it does not adjudicate them.
- **Hash-anchored**: a three-subject package manifest binds the byte-copied v0.2.8 acceptance-package manifest, the review-events JSONL, and the drill report under SHA-256, with subject paths refused if they contain `..` or are absolute.
- **Delegating, never re-implementing**: the runner subprocess-invokes the unchanged v0.2.8 acceptance validator; the verifier delegates nested acceptance-package validation to the same unchanged v0.2.8 validator. v0.2.8 failures surface as `nested_acceptance_package_invalid`; the v0.2.8 code `external_evidence_verification_failed` is preserved as a distinct v0.2.9 reason when `--evidence-package-root` is supplied.
- **Refusal-by-design**: the runner refuses with `FAIL: acceptance_package_validation_failed: <detail>` (exit 1) when the input v0.2.8 package fails validation, and with `FAIL: review_fixture_insufficient: <detail>` (exit 1) when the fixture has zero within-window challenges or zero revocation signals. A refused run leaves no partial drill package on disk. Both refusal codes are runner-only and are never emitted by the verifier.
- **Re-derivation-based**: the verifier re-derives the drill report's classification, findings, and triggers independently from the review events, including the within-window challenge classification (`challenge_window_classification_mismatch` fires before `challenge_within_window_missing`).
- **Closed-set posture**: `recommended_local_posture` is exactly one of `acceptance_stands_for_demo_scope`, `acceptance_requires_review_before_reuse`, `acceptance_not_reusable_without_governed_review`.

The v0.2.9 drill is **not**:

- A Gold certificate, regulator approval, third-party audit, legal revocation, dispute resolution, or acceptance governance workflow. The drill records review triggers; it does not decide their merits.
- A live revocation, challenge, or governance integration. The drill does not query live revocation services, real challenge systems, real gateways, real SIEM, real GRC, or any external service.
- A change to the v0.2.7 composed gateway evidence package or the v0.2.8 acceptance record. The drill never mutates a v0.2.8 acceptance package; the full v0.2.8 package subdirectory is byte-copied into the drill package.
- A signed Silver artifact. v0.2.9 ships local hash anchors only.
- A change to Bronze, Silver Signed Bundle Assertion, Revocation List, Verification Report, Profile, Verifier Output Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary Demo, Evidence Source Adapter, Composed Gateway Evidence, or Relying-Party Acceptance Record semantics.

The key claim:

> v0.2.9 drills post-acceptance review signals over a Silver relying-party acceptance record. It does not adjudicate challenges, revoke acceptance, certify evidence, or execute Gold governance.

---

## v0.3.0 Silver Acceptance Handoff

Silver v0.3.0 is a composition release. It packages the completed v0.2.7 composed gateway evidence, v0.2.8 relying-party acceptance, and v0.2.9 revocation/challenge drill into a single portable, hash-anchored Silver acceptance handoff artifact. v0.3.0 introduces no new evidence content.

The v0.3.0 handoff is:

- **A composition artifact**: the runner subprocess-invokes the unchanged v0.2.7 verifier, v0.2.8 validator, and v0.2.9 verifier — each **without** `--evidence-package-root` — so v0.3.0 alone owns the cross-package binding. The four nested packages remain unchanged on disk.
- **Hash-anchored**: a four-subject package manifest binds the v0.2.7 composed gateway evidence manifest, the v0.2.8 acceptance package manifest, the v0.2.9 drill manifest, and the v0.3.0 handoff summary under SHA-256 in fixed order with fixed roles. Subject paths are refused if they contain `..` or are absolute.
- **Chain-bound by v0.3.0**: four v0.3.0-owned cross-checks bind the top-level manifest subjects to the recorded sha256 fields inside the nested packages. Any mismatch fires the specific v0.3.0 reason `handoff_chain_binding_mismatch` (verifier) or `handoff_chain_binding_failed` (runner).
- **Posture-rank-bounded**: the runner maps the nested v0.2.9 `recommended_local_posture` onto a minimum handoff posture rank (`acceptance_stands_for_demo_scope` → 0, `acceptance_requires_review_before_reuse` → 1, `acceptance_not_reusable_without_governed_review` → 2). The selected `recommended_handoff_posture` must be no weaker than the rank required by the drill posture; an unknown posture fires `handoff_posture_invalid` and a weaker handoff posture fires `handoff_posture_downgrade`.
- **Overclaim-guarded**: the verifier scans every string value in the handoff summary (recursively) **outside** the `scope_limitations` and `non_claims` arrays for a closed set of forbidden positive tokens (`certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`). Any positive occurrence fires `handoff_overclaim`.
- **Self-validated before atomic move**: with `--self-validate`, the runner invokes the v0.3.0 verifier against the staging directory **before** `os.replace()`. On failure it removes staging, leaves the destination untouched, and exits 1 with `FAIL: self_validation_failed: <detail>`.
- **Stable-failure-reasoned**: 17 stable verifier failure reasons and 5 deliberately distinct runner-only refusal codes (`composed_evidence_validation_failed`, `acceptance_package_validation_failed`, `drill_package_validation_failed`, `handoff_chain_binding_failed`, `self_validation_failed`). The verifier never emits the runner-only codes.

The v0.3.0 handoff is **not**:

- A Gold certificate, Gold conformance, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge, legally revoked acceptance, or production authorization.
- A change to the v0.2.7 composed gateway evidence package, the v0.2.8 relying-party acceptance package, or the v0.2.9 revocation/challenge drill package. The full nested package roots are byte-copied; their semantics are unchanged.
- A signed Silver artifact. v0.3.0 ships local hash anchors only.
- A live integration with any real gateway, SIEM, observability stack, policy engine, GRC platform, or governance authority.
- A claim of new evidence content. The `recommended_handoff_posture` is descriptive. It is not an approval, not a decision, and not a governance act.
- A transfer of reliance from one relying party to another. v0.2.8 already recorded one relying party's local decision; v0.3.0 binds that decision into a portable package without extending what it asserts.
- A change to Bronze, Silver Signed Bundle Assertion, Revocation List, Verification Report, Profile, Verifier Output Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary Demo, Evidence Source Adapter, Composed Gateway Evidence, Relying-Party Acceptance Record, or Revocation/Challenge Drill semantics.

The key claim:

> v0.3.0 packages already-verified Silver evidence into a portable, hash-anchored handoff artifact whose chain binding the v0.3.0 verifier owns and re-derives end to end. It does not extend the substance of what that evidence asserts and it does not cross the Gold boundary.

---

## v0.3.1 Silver Handoff Inspector + Gold Gap Inventory

Silver v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable by deriving a deterministic, hash-anchored review report that summarizes the verified chain, the carried-forward caution posture, and the unresolved Gold-boundary prerequisites. v0.3.1 introduces no new evidence source, signature scheme, trust authority, or runtime substrate.

The v0.3.1 inspection package is:

- **A derived review artifact**: the runner subprocess-invokes the unchanged v0.3.0 handoff verifier and the v0.3.1 verifier in `--validate-requirement-set` mode, byte-copies the v0.3.0 handoff package root under `silver-acceptance-handoff/`, byte-copies the committed Gold-boundary requirement set, and re-derives the inspection report from the nested v0.3.0 handoff summary and the bound requirement set.
- **Hash-anchored**: a three-subject inspection manifest binds the v0.3.0 handoff manifest, the requirement set, and the inspection report under SHA-256 in fixed order. Subject paths are refused if they contain `..` or are absolute.
- **Chain-bound by v0.3.1**: `base_handoff.handoff_manifest_sha256` is cross-checked against subject [0]; `gold_gap_inventory.requirements_sha256` is cross-checked against subject [1]; every non-posture handoff summary field is cross-checked against the nested v0.3.0 summary under the dedicated reason `inspection_handoff_summary_mismatch`; the posture path (`recommended_handoff_posture` rank and `reuse_warning`) is reserved for the dedicated reason `inspection_review_posture_downgrade`, which remains reachable even when the non-posture cross-checks pass.
- **Status-set closed**: each row in `gold_gap_inventory.requirements` carries exactly one of four statuses: `silver_evidence_present`, `silver_evidence_partial`, `gold_prerequisite_unmet`, or `out_of_scope_for_silver`. The report-level `gold_boundary_status` is forced to `gold_not_claimed` whenever any row is partial, unmet, or out-of-scope; `inspection_gold_overclaim` fires if the report tries to record `gold_gap_inventory_only` under those conditions or includes a forbidden positive overclaim token in any string outside `scope_limitations` / `non_claims`.
- **Domain-complete**: the bound requirement set must cover exactly one row per each of 13 named governance domains (`governed_acceptance_policy`, `named_acceptance_authority`, `independent_verifier_identity`, `evidence_retention_policy`, `change_control_policy`, `revocation_operations`, `challenge_dispute_process`, `audit_trail_and_review`, `runtime_operating_boundary`, `external_accountability`, `public_or_shared_acceptance_record`, `legal_or_contractual_basis`, `production_use_authorization`). Missing domains fire `requirement_domain_missing`; duplicate ids or domains fire `requirement_duplicate`; malformed structure or unknown statuses fire `requirement_set_invalid`.
- **Self-validated before atomic move**: with `--self-validate`, the runner invokes the v0.3.1 verifier against the staging directory **before** `os.replace()`. On failure it removes staging, leaves the destination untouched, and exits 1 with `FAIL: inspection_self_validation_failed: <detail>`.
- **Stable-failure-reasoned**: 20 stable verifier failure reasons and 3 deliberately distinct runner-only refusal codes (`handoff_validation_failed`, `requirement_set_validation_failed`, `inspection_self_validation_failed`). The verifier never emits the runner-only codes.

The v0.3.1 inspection package is **not**:

- A Gold certificate, Gold readiness assessment, regulator approval, auditor approval, legal acceptance, transferred reliance, adjudicated challenge resolution, or production authorization.
- A change to the v0.3.0 Silver acceptance handoff package, the v0.2.9 revocation/challenge drill, the v0.2.8 relying-party acceptance, or the v0.2.7 composed gateway evidence. The full v0.3.0 handoff package root is byte-copied under `silver-acceptance-handoff/`; its semantics and on-disk bytes are unchanged.
- A signed Silver artifact. v0.3.1 ships local hash anchors only.
- A live integration with any real governance authority, regulator, auditor, or compliance framework.
- A consultation of an external compliance standard. The bound Gold-boundary requirement set is a local ProofRail demo inventory.
- A claim that `silver_evidence_present` rows satisfy any Gold prerequisite. `silver_evidence_present` means relevant Silver evidence is present inside the ProofRail chain; the corresponding Gold prerequisite (governed acceptance authority, governed change control, externally-published acceptance record, legal basis, audited operating boundary, etc.) remains unmet.
- A transfer of reliance to a downstream party. v0.3.1 records that a local reviewer could deterministically re-derive the same chain summary and gap inventory from the v0.3.0 handoff package; it does not authorize anyone to act on that summary.
- A change to Bronze, Silver Signed Bundle Assertion, Revocation List, Verification Report, Profile, Verifier Output Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent Trust-boundary Demo, Evidence Source Adapter, Composed Gateway Evidence, Relying-Party Acceptance Record, Revocation/Challenge Drill, or Silver Acceptance Handoff semantics.

The key claim:

> v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable. It does not certify the handoff, the system, or the relying party, and it does not begin Gold governance. `silver_evidence_present` in the gap inventory does not mean the corresponding Gold prerequisite is satisfied.

---

## v0.3.2 Silver Trace Binding Profile

Silver v0.3.2 binds protected-action claims to deterministic trace event evidence anchored to the unchanged v0.2.6 simulated observability-trace adapter descriptor. v0.3.2 introduces no new signature scheme, trust authority, or runtime substrate.

The v0.3.2 trace binding package is:

- **A derived binding artifact**: the runner runs an adapter trust-authority pre-check, subprocess-invokes the unchanged v0.2.6 adapter validator, parses the static trace events JSONL and binding set JSON, cross-checks every non-gap binding row against its resolved trace event, and derives the trace binding report deterministically.
- **Hash-anchored**: a four-subject trace binding manifest binds the adapter, the trace events JSONL, the binding set JSON, and the trace binding report under SHA-256 in fixed order. Subject paths are refused if they contain `..` or are absolute, and path traversal is checked **before** exact subject-path equality.
- **Re-derivable by an independent reviewer**: every field in the trace binding report is re-derivable from the trace events and binding set. The verifier independently re-derives the same fields and rejects any disagreement under one of 22 stable failure reasons.
- **Reachability-ordered**: `trace_source_marked_authority` is checked **before** the v0.2.6 adapter validator subprocess so a tampered adapter with `source_is_trust_authority: true` is always attributed to the specific reason. `trace_warning_downgrade` is checked **before** the generic `trace_report_status_mismatch` so downgrades of `bound_with_warning` / `trace_gap_detected` / `out_of_scope_for_trace_binding` to `bound` are always attributed to the more specific reason.
- **Self-validated before atomic move**: with `--self-validate`, the runner invokes the v0.3.2 verifier against the staging directory **before** `os.replace()`. On failure it removes staging, leaves the destination untouched, and exits 1 with `FAIL: trace_binding_self_validation_failed: <detail>`.
- **Overclaim-guarded**: the verifier's recursive overclaim scan rejects 22 forbidden positive tokens — including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance` — anywhere outside `scope_limitations` and `non_claims`.

The v0.3.2 trace binding package is **not**:

- A claim that a real production trace system observed these events. The trace event fixture is static and committed; v0.3.2 does not query or consult any live observability substrate.
- An assertion that the observability source is a trust authority. The adapter declares `trust_boundary.source_is_trust_authority: false`, and the v0.3.2 runner and verifier refuse any adapter that declares otherwise.
- OpenTelemetry conformance. v0.3.2 uses OpenTelemetry-style field naming for familiarity only and does not claim conformance to the OpenTelemetry specification.
- Runtime truth. A trace binding report is evidence of declared trace events, not proof that runtime behavior occurred exactly as described.
- A signed Silver artifact. v0.3.2 ships local hash anchors only.
- A relying-party acceptance, an acceptance handoff, or a handoff inspection. v0.3.2 emits an additional Silver evidence artifact; it does not modify v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 / v0.3.1 semantics, and the v0.3.1 inspector does not (yet) ingest v0.3.2 trace binding evidence.
- A transfer of reliance to a downstream party. `source_event_ref` values are opaque labels; v0.3.2 does not resolve or cross-validate them against any external package.
- A regulator approval, third-party audit, auditor approval, legal acceptance, compliance certification, or production authorization.
- A claim that v0.3.2 begins Gold governance.

> v0.3.2 binds protected-action claims to deterministic trace evidence for independent Silver review. It does not make the observability source authoritative, prove runtime truth, certify OpenTelemetry conformance, certify the underlying system, transfer reliance, or execute Gold governance.

---

## Summary

Silver v0.1.7 is significant because it makes ProofRail evidence portable, signed, revocable, reportable, and independently verifiable.

However, it remains a relying-party verification layer.

It is not certification.

It is not Gold.

It is the first implementation of the layer Gold can later rely on.
