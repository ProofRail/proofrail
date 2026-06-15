ProofRail™

Status: early public documentation repository. Specifications, profiles, sanitized attestations, and examples will be published here. Raw deployment evidence and security-sensitive operational details remain private.

ProofRail™ is a vendor-neutral conformance and governance framework for AI agent actuation control.

As AI agents gain access to tools, APIs, workflows, and enterprise systems, organizations need more than logs or model-side guardrails. They need evidence that protected actions are actually controlled: declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

ProofRail defines that evidence layer.

This project began with Iron-plus, a live reference profile for MCP actuation control, and extended through Bronze, a local-enterprise conformance profile that can be implemented either through ProofRail-native components or through composed stacks using existing gateways, identity providers, observability tools, SIEM/logging systems, and runbooks.   Early Silver will demonstrate how a ProofRail Bronze evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy, while preserving the underlying Bronze evidence-integrity checks.

Current proof chain:

Iron-plus → Composed Bronze → Bronze v0.1.2 checksums → Bronze v0.1.3 bundle manifest → Minimal Silver signed assertion

Specific milestones on the path to Silver are:

1. **Bronze v0.1.2** — generate a structured Bronze claim with evidence checksums.
2. **Bronze v0.1.3** — generate an unsigned evidence bundle manifest that checksums the whole portable package, including the claim file.
3. **Silver Signed Bundle Assertion v0.1.0** — sign the Bronze v0.1.3 bundle manifest and verify it against a local trust policy.

ProofRail is not intended to replace enterprise gateways or security platforms. Its purpose is to define the control claims and evidence structure needed to trust deployments of agentic AI controls across heterogeneous enterprise stacks.

Current focus areas include:

protected actuator set declaration and hashing;
bypass-prevention evidence;
emergency-stop and safe-mode semantics;
normalized audit evidence;
performance evidence;
Bronze claim schemas and conformance profiles;
composed Bronze stacks using existing gateway and observability components
Minimal Silver signed relying-party verification

Raw deployment evidence, credentials, private topology, and security-sensitive operational details are not published here. Public materials are limited to specifications, profiles, sanitized attestations, examples, and implementation guidance.


Start here:
1. [Evidence walkthrough](https://github.com/ProofRail/proofrail/blob/main/docs/walkthroughs/composed-bronze-demo-001b-evidence-walkthrough.md)
2. [Bronze demo folders](https://github.com/ProofRail/proofrail/tree/main/demos/composed-bronze-demo-001)
3. [Silver demo folder](https://github.com/ProofRail/proofrail/tree/main/demos/silver-demo-001)
4. [ProofRail Bronze claim schema v0.1.1](https://github.com/ProofRail/proofrail/blob/main/schemas/bronze-claim-schema-v0.1.1.md)
5. [Bronze claim tools README](https://github.com/ProofRail/proofrail/blob/main/tools/claims/README.md)
6. [Silver verification tools README](https://github.com/ProofRail/proofrail/blob/main/tools/silver/README.md)
