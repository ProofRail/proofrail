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
