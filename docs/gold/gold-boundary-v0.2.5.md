# ProofRail Gold Boundary Document — v0.2.5

**Version:** v0.2.5 (boundary document only)
**Date:** 2026-06-21
**Status:** Boundary documentation. **Not** a Gold conformance, certification, or acceptance specification.

---

## 1. Purpose

This document names the Gold boundary as observed from ProofRail v0.2.5. It states what Silver currently demonstrates, what Silver still does not provide, what a future Gold layer would need to add, and what must remain outside Gold until independently specified.

This document is the first time ProofRail names the Gold boundary. It does not cross it.

> **v0.2.5 names the Gold boundary. It does not cross it.**

---

## 2. What This Document Is Not

This document does **not**:

- define a Gold profile;
- define a Gold schema, validator, certificate, or badge;
- describe a certification process;
- describe an auditor approval flow;
- describe a regulator workflow;
- assert governed institutional acceptance;
- assert production safety, agent safety, or prompt-injection resistance;
- create acceptance authority for any party.

No Gold artifact is shipped in v0.2.5.

---

## 3. What Silver v0.2.5 Now Demonstrates

After v0.2.5 the Silver layer demonstrates, with local deterministic evidence, that:

- harmless agent-to-agent messages do not invoke protected actions;
- protected actions reach `allow` only when a scoped authority grant matches the requesting principal and the request constraints;
- a grant whose subject is principal A cannot be wielded by principal B (`authority_subject_mismatch`);
- bypass attempts outside the controlled path are recorded and not silently allowed;
- after a revocation point, the formerly-valid grant no longer satisfies authority (`authority_revoked`);
- an action outside the grant's declared scope is denied (`constraint_not_satisfied`);
- the harness evidence is locally hash-verifiable by an unchanged v0.2.4 verifier;
- the demo never executes a protected action (`execution.performed == false`).

The demo package adds one more layer: a manifest that hashes the package's documentation and summary, references the nested harness evidence manifest, and is independently verifiable by a relying-party-side tool.

---

## 4. What Silver v0.2.5 Still Does Not Provide

Silver v0.2.5 is explicit about what it does **not** establish:

- it does not demonstrate that any live agent is safe;
- it does not detect prompt injection;
- it does not parse or evaluate natural-language instructions;
- it does not certify a production deployment;
- it does not impose a runtime substrate (agentgateway, ContextForge, Lasso, Kubernetes, service mesh, etc.);
- it does not exercise real protected actuators;
- it does not require signed evidence;
- it does not require a verifier identity attestation;
- it does not bind any institutional acceptance.

The Silver Signed Bundle Assertion (v0.1.0) and Verifier Output Attestation (v0.1.0) remain available for relying parties that want signed evidence on top of Silver. They are not required by the demo.

---

## 5. What a Future Gold Layer Would Need to Add

A future Gold layer is not specified by v0.2.5. The list below is a non-binding inventory of areas that would have to be specified, with public artifacts, before Gold could exist as more than a boundary:

- **Governed acceptance criteria.** A documented, externally-visible specification of what acceptance means, who can grant it, and under what conditions it can be withdrawn.
- **Named relying-party operating policies.** Stable, version-controlled policies describing what a relying party commits to when accepting evidence at the Gold level.
- **Independent verifier identity and accountability.** A registered verifier identity model with public binding, key rotation discipline, and an accountable operator.
- **Evidence retention expectations.** Durations, formats, hand-off rules, and tamper-evident storage expectations for retained evidence.
- **Change-control expectations.** Required change-control records for the authority fixtures, harness scripts, packager configuration, and verifier code that produced any accepted evidence.
- **Revocation and dispute handling expectations.** Public processes for revoking accepted evidence, opening disputes, and recording rejection.
- **External audit or certification process.** A defined external review process with auditor identity, scope, sampling discipline, and reporting expectations.
- **Controlled runtime substrate evidence.** Where applicable, evidence that the runtime substrate enforced the same authority semantics observed in the Silver demo, with deployment-side controls and not only fixture-side claims.
- **Acceptance and rejection records.** A public ledger or equivalent record of accepted and rejected evidence under the Gold layer.

Each of these is a multi-stakeholder commitment. None of them are technical schema additions alone.

---

## 6. What Must Remain Outside Gold Until Independently Specified

Even after a future Gold layer is specified, the following must remain outside its claims unless independently specified by their respective communities:

- regulator approval;
- certification with legal force;
- liability allocation;
- standards-body conformance unrelated to ProofRail;
- production safety guarantees for live agents;
- prompt-injection resistance guarantees;
- LLM behavior guarantees.

ProofRail's role is to make evidence inspectable. It is not to substitute for these external decisions.

---

## 7. Boundary Sentence

The release line for v0.2.5 is:

> ProofRail v0.2.5 packages the deterministic Silver multi-agent trust-boundary demo and verifies its package evidence. It also defines the first Gold boundary as documentation only.

And:

> v0.2.5 names the Gold boundary. It does not cross it.

---

## 8. Changelog

- **v0.2.5 (2026-06-21):** First Gold boundary document. Documentation only.

---

## 9. Note on v0.2.8 Relying-Party Acceptance Record

Silver v0.2.8 introduces a deterministic, hash-anchored local relying-party acceptance record over a verified v0.2.7 composed gateway evidence package. The record binds a named local acceptance policy, declared purpose, verifier outcome, revocation review, exceptions, scope limitations, and challenge window.

The v0.2.8 acceptance record is the first ProofRail artifact that explicitly names a relying-party acceptance decision. It is **still Silver, not Gold**:

- It records *one* fictional demo relying party's decision under that party's *own* local policy. It does not coordinate, chain, federate, or arbitrate decisions across parties.
- It is not signed. v0.2.8 ships local hash anchors only.
- It does not invoke any external acceptance authority, governance workflow, regulator, auditor, registry, or sign-off body.
- The fixture relying party (`demo.relying_party`) is fictional. No real relying-party has authored that policy.
- The record's challenge window is a *local* placeholder for the period during which the relying party will entertain a recorded objection; it is not a formal dispute process.

Gold-level acceptance (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.2.8 does not add any of those.

The release sentence holds:

> v0.2.8 records a relying party's local acceptance decision over verified Silver evidence. It does not certify the evidence, the system, the gateway, or the relying party.

A relying-party acceptance record is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument.

v0.2.8 records acceptance context. It does not execute acceptance governance.

v0.2.8 names a relying-party decision. It does not cross the Gold boundary.

---

## 10. Note on v0.2.9 Revocation/Challenge Drill

Silver v0.2.9 layers a deterministic, hash-anchored local revocation/challenge drill on top of a v0.2.8 relying-party acceptance package. The drill consumes a static JSONL fixture of post-acceptance review signals, classifies them against the acceptance record's policy-derived challenge window, derives required findings and review triggers, and selects a single `recommended_local_posture` from a closed set.

The v0.2.9 drill is **still Silver, not Gold**:

- It records that local post-acceptance review signals were detected, classified, and bound to a specific v0.2.8 acceptance package. It does not adjudicate them.
- It does not invoke any external revocation authority, dispute-resolution body, regulator, auditor, registry, or sign-off process. The drill does not query live revocation services, real challenge systems, real gateways, real SIEM, real GRC, or any external service.
- It does not coordinate, chain, federate, or arbitrate decisions across parties. The drill is a single-relying-party, local-evidence artifact.
- It is not signed. v0.2.9 ships local hash anchors only.
- It never mutates the underlying v0.2.7 composed gateway evidence package or the v0.2.8 acceptance record. The full v0.2.8 package subdirectory is byte-copied into the drill package; the runner refuses to emit output when the v0.2.8 validator fails.
- The `recommended_local_posture` is exactly one of `acceptance_stands_for_demo_scope`, `acceptance_requires_review_before_reuse`, `acceptance_not_reusable_without_governed_review`. It is a recorded local recommendation, not a governed acceptance change.

Gold-level adjudication of challenges and revocations (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.2.9 does not add any of those.

The release sentence holds:

> v0.2.9 drills post-acceptance review signals over a Silver relying-party acceptance record. It does not adjudicate challenges, revoke acceptance, certify evidence, or execute Gold governance.

A revocation/challenge drill report is not a Gold certificate, regulator approval, third-party audit, legal revocation, dispute resolution, or acceptance governance workflow.

v0.2.9 records review triggers. It does not decide their merits.

v0.2.9 names a post-acceptance review drill. It does not cross the Gold boundary.

---

## 11. Note on v0.3.0 Silver Acceptance Handoff

ProofRail v0.3.0 is a composition release. It packages the completed v0.2.7 composed gateway evidence, v0.2.8 relying-party acceptance, and v0.2.9 revocation/challenge drill into a single portable, hash-anchored Silver acceptance handoff artifact. v0.3.0 introduces no new evidence content.

The v0.3.0 handoff is **still Silver, not Gold**:

- It is a composition. The runner subprocess-invokes the unchanged v0.2.7 verifier, v0.2.8 validator, and v0.2.9 verifier — each without `--evidence-package-root` — so v0.3.0 alone owns the cross-package chain binding. The nested packages remain unchanged on disk.
- The four v0.3.0-owned chain-binding cross-checks (top-level subject sha256 against nested `evidence_package.manifest_sha256`, against nested `base_acceptance.acceptance_package_manifest_sha256`, and against the inner byte-copies inside the v0.2.8 and v0.2.9 roots) are integrity checks. They are not acceptance decisions.
- The `recommended_handoff_posture` is a closed-set local recommendation (`silver_handoff_complete_for_demo_scope`, `silver_handoff_complete_review_required_before_reuse`, `silver_handoff_not_reusable_without_governed_review`) whose rank must be no weaker than the nested v0.2.9 drill posture. It is descriptive, not a governance act.
- The verifier's overclaim guard explicitly rejects the positive tokens `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer` anywhere outside `scope_limitations` and `non_claims`. The handoff is structurally prevented from claiming Gold conformance, regulator approval, audit, or trust transfer.
- It is not signed. v0.3.0 ships local hash anchors only.
- It does not invoke any external acceptance authority, governance workflow, regulator, auditor, registry, sign-off body, or trust-transfer mechanism.
- It does not adjudicate, decide, federate, chain, arbitrate, or transfer reliance. The nested v0.2.8 record remains exactly one fictional demo relying party's local decision.

Gold-level handoff (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.3.0 does not add any of those.

The release sentence holds:

> v0.3.0 packages already-verified Silver evidence into a portable, hash-anchored handoff artifact whose chain binding the v0.3.0 verifier owns and re-derives end to end. It does not extend the substance of what that evidence asserts.

A Silver acceptance handoff package is not a Gold certificate, Gold conformance, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge, legally revoked acceptance, or production authorization.

v0.3.0 packages acceptance evidence. It does not execute acceptance governance.

v0.3.0 names a portable Silver handoff. It does not cross the Gold boundary.

---

## 12. Note on v0.3.1 Silver Handoff Inspector + Gold Gap Inventory

ProofRail v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable. The v0.3.1 inspection package binds three subjects in fixed order — the unchanged v0.3.0 handoff manifest, a committed local Gold-boundary requirement set, and a re-derived inspection report — anchored by a 3-subject SHA-256 manifest. v0.3.1 introduces no new evidence source, signature scheme, trust authority, or runtime substrate.

The v0.3.1 inspection package is the first ProofRail artifact that explicitly enumerates the Gold-boundary prerequisites a Silver chain does not satisfy. It is **still Silver, not Gold**:

- It is a deterministic local derivation. The runner subprocess-invokes the unchanged v0.3.0 handoff verifier and the v0.3.1 verifier in `--validate-requirement-set` mode, byte-copies the v0.3.0 handoff root under `silver-acceptance-handoff/`, byte-copies the committed Gold-boundary requirement set, and re-derives every field of the inspection report from the nested v0.3.0 summary and the bound requirement set.
- The bound Gold-boundary requirement set is a **local ProofRail demo inventory**, not an external compliance standard, regulator framework, audit checklist, certification scheme, legal instrument, or governance policy. It enumerates exactly 13 governance domains (`governed_acceptance_policy`, `named_acceptance_authority`, `independent_verifier_identity`, `evidence_retention_policy`, `change_control_policy`, `revocation_operations`, `challenge_dispute_process`, `audit_trail_and_review`, `runtime_operating_boundary`, `external_accountability`, `public_or_shared_acceptance_record`, `legal_or_contractual_basis`, `production_use_authorization`) and assigns each row exactly one of four closed-set statuses: `silver_evidence_present`, `silver_evidence_partial`, `gold_prerequisite_unmet`, `out_of_scope_for_silver`.
- The status `silver_evidence_present` does **not** mean the corresponding Gold prerequisite is satisfied. It means relevant Silver evidence is present inside the ProofRail Silver chain (for example, an independent verifier identity is bound at the v0.2.2 verifier output attestation layer). The Gold prerequisite (a governed, externally-accountable verifier identity registered under a named acceptance authority) remains unmet by this fact alone. The report-level `gold_boundary_status` is forced to `gold_not_claimed` whenever any row is partial, unmet, or out-of-scope.
- The verifier's overclaim guard explicitly rejects positive tokens including `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `gold accepted`, `gold certified`, `gold ready`, `gold-ready`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`, `governance complete`, `acceptance governance executed` anywhere in the inspection report outside `scope_limitations` and `non_claims`. The inspection report is structurally prevented from claiming Gold readiness, Gold certification, regulator approval, audit, legal acceptance, or trust transfer.
- It is not signed. v0.3.1 ships local hash anchors only.
- It does not invoke any external governance authority, regulator, auditor, registry, sign-off body, or trust-transfer mechanism.
- It does not adjudicate, decide, federate, chain, arbitrate, or transfer reliance. The nested v0.2.8 record remains exactly one fictional demo relying party's local decision; the v0.3.0 handoff package remains unchanged on disk.

Gold-level readiness assessment, certification, regulator approval, audit opinion, legal acceptance, and production authorization (as inventoried in §5 above) still require the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity (governed, not merely declared), retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.3.1 does not add any of those. v0.3.1 enumerates the unmet ones so they cannot be elided.

The release sentence holds:

> v0.3.1 makes a v0.3.0 Silver acceptance handoff package independently inspectable. It does not certify the handoff, the system, or the relying party, and it does not begin Gold governance.

A Silver handoff inspection package is not a Gold certificate, Gold readiness assessment, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge resolution, legally revoked acceptance, or production authorization.

v0.3.1 enumerates Gold-boundary prerequisites. It does not satisfy them.

v0.3.1 names an inspectable Silver handoff and its Gold-boundary gap inventory. It does not cross the Gold boundary.

---

## 13. Note on v0.3.2 Silver Trace Binding Profile

ProofRail v0.3.2 binds protected-action claims to deterministic trace event evidence anchored to the unchanged v0.2.6 simulated observability-trace adapter descriptor. The v0.3.2 trace binding package binds four subjects in fixed order — the adapter descriptor, the trace events JSONL fixture, the trace claim binding set, and the derived trace binding report — anchored by a four-subject SHA-256 manifest. v0.3.2 introduces no new signature scheme, trust authority, or runtime substrate.

The v0.3.2 trace binding package is **still Silver, not Gold**:

- It is a deterministic local derivation. The runner runs an adapter trust-authority pre-check, subprocess-invokes the unchanged v0.2.6 adapter validator, parses the static trace events JSONL and binding set JSON, cross-checks every non-gap binding row against its resolved trace event, derives the trace binding report deterministically, and atomically `os.replace()`s the staging directory into place only after optional self-validation passes.
- It is not a runtime substrate, not OpenTelemetry conformance, not a production observability claim, and not a claim that any real trace system observed the recorded events. The trace event fixture is static and committed; v0.3.2 does not query or consult any live observability substrate.
- It does not establish the observability source as a trust authority. The adapter declares `trust_boundary.source_is_trust_authority: false`, and the v0.3.2 runner and verifier refuse any adapter that declares otherwise. Tampered adapters are always attributed to the specific reason `trace_source_marked_authority`, not collapsed into the generic `trace_adapter_invalid`.
- It is not signed. v0.3.2 ships local hash anchors only.
- It does not extend the substance of any earlier-release Silver evidence. v0.3.2 emits an additional Silver evidence artifact; it does not modify v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 / v0.3.1 semantics, and the v0.3.1 inspector does not (yet) ingest v0.3.2 trace binding evidence.
- It does not adjudicate, decide, federate, chain, arbitrate, or transfer reliance. `source_event_ref` values are opaque labels; v0.3.2 does not resolve or cross-validate them against any external package.

Gold-level handoff (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.3.2 does not add any of those.

The release sentence holds:

> v0.3.2 binds protected-action claims to deterministic trace evidence for independent Silver review. It does not make the observability source authoritative, prove runtime truth, certify OpenTelemetry conformance, certify the underlying system, transfer reliance, or execute Gold governance.

A Silver trace binding package is not a Gold certificate, OpenTelemetry conformance claim, production observability claim, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge resolution, legally revoked acceptance, compliance certification, or production authorization.

v0.3.2 binds trace evidence. It does not prove runtime truth.

v0.3.2 names a trace-bound Silver evidence package. It does not cross the Gold boundary.

---

## 14. Note on v0.3.3 Silver Adapter Pilot Package

ProofRail v0.3.3 pilots a local external-evidence adapter flow that normalizes an OpenTelemetry-shaped local source-export fixture into ProofRail v0.3.2 trace-binding inputs under a declarative, evidence-only mapping. The v0.3.3 adapter pilot package binds seven subjects in fixed order — the v0.2.6 adapter descriptor, the source-export JSONL fixture, the normalization map, the normalized trace events JSONL, the normalized trace claim binding set, the nested v0.3.2 trace-binding manifest, and the derived adapter pilot report — anchored by a seven-subject SHA-256 manifest. v0.3.3 introduces no new signature scheme, trust authority, or runtime substrate.

The v0.3.3 adapter pilot package is **still Silver, not Gold**:

- It is a deterministic local pilot. The runner subprocess-invokes the unchanged v0.2.6 adapter validator and the unchanged v0.3.2 trace-binding builder + verifier, byte-copies inputs, derives normalized trace events under a tiny declarative mapping language (`<source.dot.path>` and `"constant:<literal>"` only; longest-prefix key matching at each step), and re-derives every required claim from the inputs. The verifier independently re-derives the normalized trace-events JSONL byte-for-byte from the source export and the normalization map, and re-invokes the unchanged v0.3.2 verifier on the nested manifest.
- It is not a runtime substrate, not OpenTelemetry conformance, not a vendor certification, not a production integration, and not a claim that any real trace system observed the recorded events. The source-export fixture is static and committed; v0.3.3 does not query or consult any live OpenTelemetry collector, vendor service, observability platform, SIEM, GRC, gateway, policy-engine, or ticketing system.
- It does not establish the source system as a trust authority. The adapter declares `trust_boundary.source_is_trust_authority: false`, and the v0.3.3 runner and verifier refuse any adapter that declares otherwise. Tampered adapters are always attributed to the specific reason `adapter_pilot_source_marked_authority`, not collapsed into the generic `adapter_pilot_adapter_invalid`.
- It is not signed. v0.3.3 ships local hash anchors only.
- It does not extend the substance of any earlier-release Silver evidence. v0.3.3 emits an additional Silver evidence artifact; it does not modify v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 / v0.3.1 / v0.3.2 semantics, is not consumed by the v0.2.8 acceptance flow, the v0.3.0 handoff, or the v0.3.1 inspector, and the v0.3.2 verifier is invoked unmodified.
- It does not adjudicate, decide, federate, chain, arbitrate, or transfer reliance. `source_event_ref` values are opaque labels carried unchanged through normalization; v0.3.3 does not resolve or cross-validate them against any external package.

Gold-level handoff (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.3.3 does not add any of those, and explicitly does not introduce a live adapter integration as a Gold prerequisite or as a Gold satisfaction.

The release sentence holds:

> v0.3.3 pilots a local external-evidence adapter flow. It does not perform a real OpenTelemetry, vendor, observability, SIEM, GRC, gateway, policy-engine, or ticketing-system integration; does not establish the source system as a trust authority; does not certify OpenTelemetry conformance; does not certify any vendor integration; does not prove runtime truth; and does not extend the substance of any earlier-release Silver evidence.

A Silver adapter pilot package is not a Gold certificate, OpenTelemetry conformance claim, vendor certification, production integration, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge resolution, legally revoked acceptance, compliance certification, or production authorization.

v0.3.3 pilots an adapter normalization flow. It does not prove runtime truth.

v0.3.3 names an adapter-piloted Silver evidence package. It does not cross the Gold boundary.

---

## 15. Note on v0.3.4 Silver Challenge / Withdrawal Record Primitives

ProofRail v0.3.4 layers two structurally validated, hash-bound local records over an unchanged v0.3.0 acceptance handoff target: a challenge record under a closed `challenge_reason` (10 values) / `challenge_status` (4 values) vocabulary and a withdrawal record under a closed `withdrawal_reason` (7 values) / `withdrawal_status` (4 values) / `withdrawal_effect` (4 values) vocabulary, with a closed `withdrawal_effect → posture` derivation table (5 posture values). The v0.3.4 challenge / withdrawal primitives package binds four subjects in fixed order — the byte-copied v0.3.0 acceptance handoff manifest, the bound challenge record, the bound withdrawal record, and the derived challenge / withdrawal summary — anchored by a four-subject SHA-256 manifest. v0.3.4 introduces no new signature scheme, trust authority, runtime substrate, or adjudication.

The v0.3.4 challenge / withdrawal primitives package is **still Silver, not Gold**:

- It is a deterministic local record. The runner subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier on the target handoff manifest, structurally validates the input records under closed enums (accepting the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in **input** fixtures only), performs four runner-owned binding cross-checks against the parsed v0.3.0 handoff manifest, byte-copies the v0.3.0 handoff package root under `target-handoff/`, recomputes the SHA-256 of the copied target manifest, rewrites the placeholder in both packaged record copies under `records/` to that recomputed hash label, and derives the summary deterministically with `posture` forced from the closed `withdrawal_effect → posture` table. The verifier independently re-checks every binding, rejects the placeholder in **packaged** records via the dedicated consolidated `challenge_record_target_mismatch` / `withdrawal_record_target_mismatch` reasons (each covering placeholder-unbound, `target_manifest_sha256` drift against subject [0], and `target_record_id` drift against the v0.3.0 `handoff_id`), and re-invokes the unchanged v0.3.0 handoff verifier on subject [0].
- It is not an adjudication. The challenge record records that a challenge was filed under a closed vocabulary; it does not decide its merits. The v0.3.4 verifier does not consult any external adjudicator, regulator, auditor, or counterparty.
- It is not a legal revocation of reliance. The withdrawal record's `withdrawal_effect` describes the filer's local posture only; the closed posture vocabulary (`challenged_with_local_reuse_paused_for_review`, `challenged_with_local_reliance_withdrawn_for_review`, `record_superseded`, plus collapse from `acceptance_reuse_blocked_pending_review`) explicitly scopes the effect to local reuse / reliance, never to legal revocation of any prior acceptance instrument.
- It is not a certification of the target handoff. The v0.3.0 handoff target is byte-copied and re-verified by the unchanged v0.3.0 verifier; v0.3.4 does not certify, approve, or audit the underlying handoff.
- It is not signed. v0.3.4 ships local hash anchors only.
- It does not extend the substance of any earlier-release Silver evidence. v0.3.4 emits an additional Silver evidence artifact over a v0.3.0 target; it does not modify v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 / v0.3.1 / v0.3.2 / v0.3.3 semantics, the v0.3.0 handoff verifier is invoked unmodified, and v0.3.4 does not bind a v0.3.2 trace binding manifest or a v0.3.3 adapter pilot manifest into the challenge / withdrawal package.
- It does not federate, chain, arbitrate, notify external parties, or transfer reliance. v0.3.4 records the filer's local challenge / withdrawal posture only; it does not contact, notify, or consult any regulator, auditor, third party, counterparty, or downstream relying party.
- It does not verify the substantive truth of any free-text field. The challenge record's free-text `challenge_reason_description` and counterparty references and the withdrawal record's free-text fields are not adjudicated by v0.3.4; the overclaim guard scans every string outside `scope_limitations` / `non_claims` (including the optional `claim.description` field) for forbidden positive tokens.

Gold-level handoff (as inventoried in §5 above) still requires the multi-stakeholder commitments enumerated there: governed acceptance criteria, named operating policies, independent verifier identity, retention, change-control, governed challenge adjudication, governed revocation and dispute handling, external audit, runtime substrate evidence, and a public acceptance ledger. v0.3.4 does not add any of those, and explicitly does not introduce challenge / withdrawal primitives as a Gold prerequisite or as a Gold satisfaction.

The release sentence holds:

> v0.3.4 records local challenge / withdrawal primitives over an unchanged v0.3.0 acceptance handoff target. It does not adjudicate the challenge, does not legally revoke reliance, does not certify the target handoff, does not notify or consult any external party, does not prove the substantive truth of free-text fields, and does not extend the substance of any earlier-release Silver evidence.

A Silver challenge / withdrawal primitives package is not a Gold certificate, regulator approval, auditor approval, legal acceptance, governed acceptance, transferred reliance, adjudicated challenge resolution, legally revoked acceptance, compliance certification, or production authorization.

v0.3.4 records challenge / withdrawal primitives. It does not decide their merits.

v0.3.4 names a challenge / withdrawal primitives Silver evidence package. It does not cross the Gold boundary.
