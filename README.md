# ProofRail™

Status: public documentation repository and capability demonstrations. Specifications, profiles, sanitized attestations, and examples are published here. Raw deployment evidence and security-sensitive operational details remain private.

ProofRail™ is a vendor-neutral conformance and governance framework for AI agent actuation control. The current public release is [v0.2.3](https://github.com/ProofRail/proofrail/releases/tag/v0.2.3). The main branch includes Silver v0.2.4 deterministic multi-agent attack harness evidence and Silver v0.2.5 multi-agent trust-boundary demo packaging plus the first Gold boundary documentation.

As AI agents gain access to tools, APIs, workflows, other AI agents, and enterprise systems, organizations need more than logs or model-side guardrails. They need evidence that protected actions are actually controlled: declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

ProofRail defines that evidence layer.

This project began with Iron-plus, a live reference profile for MCP actuation control, and extended through Bronze, a local-enterprise conformance profile that can be implemented either through ProofRail-native components or through composed stacks using existing gateways, identity providers, observability tools, SIEM/logging systems, and runbooks. Silver adds signed, revocable, reportable, and independently verifiable evidence-package reliance. ProofRail v0.2.2 adds detached verifier output attestations, making Silver verification outputs attributable and tamper-evident while preserving the boundary between Silver evidence-package reliance and Gold governed acceptance. v0.2.3 adds deterministic multi-principal authority fixtures, showing that protected actions can be evaluated against scoped, revocation-aware authority before any simulated actuator path is allowed. v0.2.4 adds a deterministic, scripted multi-principal agent attack harness that drives the unchanged v0.2.3 evaluator across a canonical attack scenario and produces hash-anchored local harness evidence. v0.2.5 packages that harness evidence into a local multi-agent trust-boundary demo with eight deterministically derived claims, hash-anchored package manifest, and the first explicit Gold boundary documentation. v0.2.5 names the Gold boundary. It does not cross it.

## Current Proof Chain

Iron-plus → Composed Bronze → Bronze v0.1.2 checksums → Bronze v0.1.3 bundle manifest → Minimal Silver signed assertion → local revocation → structured verifier report → verification outside the repo source tree → Silver relying-party profile → profile conformance report → verifier output attestation → deterministic authority fixtures

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

## What ProofRail Does Not Claim

ProofRail v0.2.5 does not claim:

- Gold certification;
- third-party certification;
- regulator approval;
- production PKI;
- production deployment assurance;
- audit opinion;
- public accreditation.

Silver profile conformance is local relying-party verification, not certification of a live system. The v0.2.5 multi-agent trust-boundary demo is a local, deterministic re-packaging of v0.2.4 harness evidence; it does not execute live agents, does not invoke live actuators, does not parse natural-language prompts, does not detect prompt injection, and does not cross the Gold boundary.

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
