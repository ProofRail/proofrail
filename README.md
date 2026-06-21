ProofRail™

Status: public documentation repository and capability demonstrations. Specifications, profiles, sanitized attestations, and examples will be published here. Raw deployment evidence and security-sensitive operational details remain private.

ProofRail™ is a vendor-neutral conformance and governance framework for AI agent actuation control.  The current release is [v0.1.5](https://github.com/ProofRail/proofrail/releases/tag/v0.1.5).  

As AI agents gain access to tools, APIs, workflows, and enterprise systems, organizations need more than logs or model-side guardrails. They need evidence that protected actions are actually controlled: declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

ProofRail defines that evidence layer.

This project began with Iron-plus, a live reference profile for MCP actuation control, and extended through Bronze, a local-enterprise conformance profile that can be implemented either through ProofRail-native components or through composed stacks using existing gateways, identity providers, observability tools, SIEM/logging systems, and runbooks.   Early Silver will demonstrate how a ProofRail Bronze evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy, while preserving the underlying Bronze evidence-integrity checks.

# Current Proof Chain

Iron-plus → Composed Bronze → Bronze v0.1.2 checksums → Bronze v0.1.3 bundle manifest → Minimal Silver signed assertion → structured verifier decision artifact → verification outside repo source tree

ProofRail v0.1.7 demonstrates a reproducible path from local agentic-control evidence to a signed, revocable, independently verifiable Silver evidence package.

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
```

In practical terms, the repository now demonstrates:

1. a local Bronze claim over a composed MCP-based actuator-control demo;
2. evidence-file integrity verification;
3. a portable bundle manifest that checksums the claim, evidence, schemas, tooling, and documentation;
4. a signed Silver assertion over the Bronze evidence bundle manifest;
5. local relying-party revocation for otherwise valid signed assertions;
6. a structured Silver verification report;
7. independent local verification from an exported verification package.

The main verification path is:

```bash
python3 -m pip install -r requirements.txt

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
```

This is still a demo-grade framework. It does not claim production certification, public PKI, regulator approval, or Gold governance. It demonstrates the control-evidence mechanics needed to define those later layers.

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

---

## What ProofRail v0.1.7 Shows

ProofRail v0.1.7 shows that a protected actuator-control evidence package can be:

```text
generated
  → integrity-checked
  → bundled
  → signed
  → verified
  → revoked
  → reported
  → independently re-verified
```

The next planned milestone is **Silver v0.2.0**, which should formalize the relying-party verification profile: what a verifier must check before accepting a ProofRail Silver evidence package.

ProofRail is not intended to replace enterprise gateways or security platforms. Its purpose is to define the control claims and evidence structure needed to trust deployments of agentic AI controls across heterogeneous enterprise stacks.

Current focus areas include:

protected actuator set declaration and hashing;
bypass-prevention evidence;
emergency-stop and safe-mode semantics;
normalized audit evidence;
performance evidence;
Bronze claim schemas and conformance profiles;
composed Bronze stacks using existing gateway and observability components
Minimal Silver signed relying-party verification and local revocation
enhancement of Silver evidence verification profile

Raw deployment evidence, credentials, private topology, and security-sensitive operational details are not published here. Public materials are limited to specifications, profiles, sanitized attestations, examples, and implementation guidance.


Start here:
1. [Evidence walkthrough](https://github.com/ProofRail/proofrail/blob/main/docs/walkthroughs/composed-bronze-demo-001b-evidence-walkthrough.md)
2. [Bronze demo folders](https://github.com/ProofRail/proofrail/tree/main/demos/composed-bronze-demo-001)
3. [Silver demo folder](https://github.com/ProofRail/proofrail/tree/main/demos/silver-demo-001)
4. [ProofRail Bronze claim schema v0.1.1](https://github.com/ProofRail/proofrail/blob/main/schemas/bronze-claim-schema-v0.1.1.md)
5. [Bronze claim tools README](https://github.com/ProofRail/proofrail/blob/main/tools/claims/README.md)
6. [Silver verification tools README](https://github.com/ProofRail/proofrail/blob/main/tools/silver/README.md)
