# ProofRail™ Iron-plus v1.0.2 Evidence Attestation

**Status:** Public-safe draft
**Date:** 2026-06-01
**Version:** v0.1
**Subject:** ProofRail™ Iron-plus v1.0.2-final
**Reference profile:** Iron-plus v0.1.5
**Software version:** 1.0.2
**Purpose:** Publicly summarize the evidence supporting the ProofRail Iron-plus reference implementation claim while withholding sensitive deployment details.

---

## 1. Purpose of This Attestation

This attestation summarizes the evidence supporting the ProofRail Iron-plus v1.0.2-final reference implementation.

It is intended to provide a public-safe summary of what was implemented, tested, and evidenced without disclosing sensitive deployment details, credentials, private endpoints, raw logs, firewall details, or security-sensitive topology.

The full evidence package is maintained privately. This document summarizes the evidence and the claims supported by that evidence.

---

## 2. Summary Claim

ProofRail Iron-plus v1.0.2-final is an evidence-backed reference implementation for MCP actuation control.

It demonstrates that a declared protected actuator set can be:

* mediated through a control point;
* governed by enforce-mode policy decisions;
* blocked when actions are disallowed or identity confidence is insufficient;
* protected against tested bypass paths;
* subject to emergency stop and safe-mode behavior;
* audited through structured event records;
* emitted to multiple audit sinks;
* protected by a tamper-evident audit hash chain;
* measured against a defined performance threshold.

ProofRail Iron-plus does not claim to be a full enterprise gateway, enterprise IAM platform, SIEM, or complete Bronze implementation. It is a live reference baseline for the ProofRail evidence and conformance model.

---

## 3. Implementation Context

ProofRail Iron-plus v1.0.2-final is a standalone-proxy reference implementation focused on MCP actuation control.

The deployment profile includes:

* profile: `iron-plus`;
* topology: `standalone-proxy`;
* mode: `enforce`;
* reference profile version: `v0.1.5`;
* software version: `1.0.2`.

The implementation is designed to show that protected agent tool calls can be mediated, evaluated, audited, stopped, and tested for bypass prevention using a modest deployment footprint.

---

## 4. What Iron-plus Controls

Iron-plus controls a declared MCP actuator surface. The protected actuator set is represented as a canonical manifest with a reproducible hash.

Iron-plus applies policy and evidence controls to MCP tool calls, including:

* JSON and SSE transport paths;
* allow/block decisions;
* risk-tier classification;
* identity-confidence gating for higher-risk actions;
* per-agent rate limiting;
* emergency stop;
* D2 safe mode;
* audit emission;
* bypass-prevention testing.

The protected actuator set is intentionally explicit. ProofRail avoids vague claims such as “agents are governed” unless the covered actuators, control surfaces, and evidence are declared.

---

## 5. Evidence Summary

The private evidence package contains evidence for the following categories.

### 5.1 Conformance Evidence

The conformance matrix records:

* all numbered Iron-plus spec requirements passing;
* all unnumbered normative obligations passing;
* all acceptance tests passing;
* all v1.0.2 closure items passing.

### 5.2 Deployment Test Evidence

The deployment test closure records three complementary live-deployment suites:

* shell deployment test suite;
* in-container acceptance test suite;
* performance evidence suite.

The shell suite exercised deployment, login, health checks, proxy MCP endpoint behavior, JSON policy enforcement, SSE policy enforcement, bypass prevention, audit log verification, dashboard consistency, policy-change audit events, D2 safe mode, degradation-mode audit events, and webhook dual-sink delivery.

The in-container acceptance suite confirmed the acceptance-test set against the live deployment.

The performance suite confirmed the p95 ProofRail-added latency threshold under the documented test profile.

### 5.3 Bypass-prevention Evidence

The private evidence package includes bypass-prevention tests showing that protected actuator access is a deployment claim, not merely a design assertion.

The bypass tests cover the following categories:

* direct agent-to-upstream access;
* upstream credential placement;
* unauthorized workload behavior;
* successful mediated path through the declared control surface.

Public materials summarize the bypass-prevention result but do not disclose sensitive topology or credential placement details.

### 5.4 Audit Evidence

Iron-plus emits structured audit events for core control activities, including:

* `tool_call.attempt`;
* `tool_call.decision`;
* `tool_call.result`;
* `policy.change`;
* `degradation.mode_change`;
* `emergency.stop`;
* `emergency.resume`.

Audit events include fields needed for correlation and governance review, such as timestamp, agent ID, action type, target, decision, decision reason, correlation ID, session ID, risk tier, latency, surface, environment, and degradation state where applicable.

### 5.5 Audit Integrity Evidence

Iron-plus v1.0.2 includes a tamper-evident audit hash chain. Audit events are sealed using a hash-chain mechanism in which each event records an integrity hash and the previous event hash.

The private evidence package includes examples showing that consecutive events form an intact chain.

### 5.6 Emergency-stop and Degradation Evidence

Iron-plus includes emergency stop and resume behavior, along with D2 safe-mode behavior.

Evidence includes:

* emergency-stop event semantics;
* resume behavior;
* D2 safe-mode activation;
* Tier 2/3 blocking under safe mode;
* audit evidence for degradation-mode changes.

### 5.7 Performance Evidence

The performance evidence records a paired latency test comparing direct upstream calls with ProofRail-mediated calls.

The relevant performance result is:

* total request pairs: 300;
* errors: 0;
* p95 ProofRail-added latency: 39.77 ms;
* threshold: p95 ProofRail-added latency ≤ 50 ms;
* result: PASS.

This performance claim applies to the tested Iron-plus deployment and workload. It should not be generalized to every possible deployment, host, tool, or workload without additional testing.

---

## 6. Public vs. Private Evidence

### 6.1 Public-safe Materials

Public-safe materials may include:

* this attestation;
* high-level conformance summary;
* release note;
* sanitized performance summary;
* sanitized claim summary;
* high-level architecture description;
* public-safe Bronze strategy documents.

### 6.2 Private Evidence Package

The private evidence package may include:

* raw deployment test logs;
* raw performance samples;
* configuration snapshots;
* protected actuator set manifest;
* audit samples;
* hash-chain evidence;
* bypass-prevention output;
* firewall and deployment posture notes;
* runbooks;
* private endpoint references;
* deployment-specific topology details.

These materials are maintained privately to avoid exposing security-sensitive details.

### 6.3 Information Intentionally Withheld

This attestation does not disclose:

* secrets;
* credentials;
* tokens;
* private endpoint details;
* firewall rule internals;
* sensitive topology diagrams;
* raw production logs;
* unredacted configuration files;
* deployment details that could weaken the live reference implementation.

---

## 7. Claims Supported by the Evidence

This attestation supports the following claims.

### Claim 1: Live Reference Implementation

ProofRail Iron-plus v1.0.2-final is a live reference implementation of MCP actuation control.

### Claim 2: Enforce-mode Mediation

The deployment demonstrates enforce-mode mediation of declared MCP tool-call traffic.

### Claim 3: Protected Actuator Declaration

The deployment uses a declared protected actuator set represented by a manifest and hash.

### Claim 4: Bypass-prevention Evidence

The deployment includes bypass-prevention tests demonstrating that protected actuator control is not merely passive logging.

### Claim 5: Audit Evidence

The deployment emits structured audit evidence sufficient to support incident response and governance review for the controlled surface.

### Claim 6: Audit Integrity

The deployment includes tamper-evident audit hash-chain behavior.

### Claim 7: Emergency-stop and Safe-mode Behavior

The deployment demonstrates emergency-stop and D2 safe-mode behavior.

### Claim 8: Performance Evidence

The deployment meets the Iron-plus p95 ProofRail-added latency target under the documented test profile.

---

## 8. Claims Not Made

This attestation does not claim that ProofRail Iron-plus v1.0.2-final is:

* a full enterprise gateway;
* a complete MCP registry;
* a complete A2A gateway;
* a commercial SIEM;
* a full enterprise IAM system;
* a full Bronze implementation;
* a Silver, Gold, or Platinum implementation;
* a public certification authority;
* a guarantee that all possible agentic risks are controlled;
* a guarantee that all deployments using similar code will meet the same performance or security posture.

The evidence supports a reference implementation claim for the declared Iron-plus profile and tested deployment, not a universal guarantee.

---

## 9. Known Deferrals

The following items are intentionally deferred to Bronze or later tiers:

* multi-upstream routing and failover;
* enterprise IdP integration;
* durable audit queue or dead-letter queue;
* distributed tracing;
* policy versioning and rollback;
* external secrets manager integration;
* cross-vendor delegation semantics;
* cross-enterprise revocation;
* federated proof bundles;
* shared club governance;
* public or quasi-public oversight mechanisms.

These deferrals do not weaken the Iron-plus reference implementation claim. They define the boundary between Iron-plus, Bronze, Silver, Gold, and Platinum.

---

## 10. Relationship to Bronze Tier

Iron-plus provides an executable reference baseline for Bronze.

The Bronze strategy builds on Iron-plus by asking whether a local enterprise can produce a defensible agent-control claim across a heterogeneous stack.

Iron-plus proves that a rail can exist.

Bronze asks whether the rail can be assembled across a real enterprise stack using ProofRail-native components, vendor gateways, identity systems, SIEM/logging systems, observability tooling, and runbooks.

The private Iron-plus evidence package informed the Bronze evidence model, including:

* protected actuator set declaration;
* bypass-prevention evidence;
* audit schema;
* emergency-stop evidence;
* performance evidence;
* conformance claim structure;
* runbook/ownership discipline.

---

## 11. Public Positioning Statement

ProofRail is an evidence-first conformance and governance framework for AI agent actuation control.

ProofRail Iron-plus v1.0.2-final provides a live, evidence-backed reference implementation for MCP actuation control.

ProofRail Bronze extends this discipline into a local-enterprise conformance model, allowing enterprises to compose agent-control deployments from existing infrastructure while still producing a defensible ProofRail control claim.

---

## 12. Attestation Status

This attestation is a public-safe summary.

The underlying evidence package is maintained privately. Public materials summarize the evidence while withholding sensitive deployment details.

**Attestation status:** Draft
**Prepared by:** Thomas C. Williams
**Evidence basis:** Private ProofRail repository and associated release evidence bundle
**Timestamp convention:** UTC unless otherwise noted
**Local operator time zone:** Eastern Daylight Time, UTC-4

---

## 13. Short Form

ProofRail Iron-plus v1.0.2-final has a private evidence package supporting its reference-implementation claim, including protected actuator declaration, bypass-prevention testing, audit evidence, emergency-stop testing, D2 safe-mode testing, audit integrity evidence, and performance evidence. Public materials summarize the claim while withholding sensitive deployment details.
