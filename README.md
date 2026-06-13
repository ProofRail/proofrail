ProofRail™

Status: early public documentation repository. Specifications, profiles, sanitized attestations, and examples will be published here. Raw deployment evidence and security-sensitive operational details remain private.

ProofRail™ is a vendor-neutral conformance and governance framework for AI agent actuation control.

As AI agents gain access to tools, APIs, workflows, and enterprise systems, organizations need more than logs or model-side guardrails. They need evidence that protected actions are actually controlled: declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

ProofRail defines that evidence layer.

This project begins with Iron-plus, a live reference profile for MCP actuation control, and extends toward Bronze, a local-enterprise conformance profile that can be implemented either through ProofRail-native components or through composed stacks using existing gateways, identity providers, observability tools, SIEM/logging systems, and runbooks.

ProofRail is not intended to replace enterprise gateways or security platforms. Its purpose is to define the control claims and evidence structure needed to trust deployments of agentic AI controls across heterogeneous enterprise stacks.

Current focus areas include:

protected actuator set declaration and hashing;
bypass-prevention evidence;
emergency-stop and safe-mode semantics;
normalized audit evidence;
performance evidence;
Bronze claim schemas and conformance profiles;
composed Bronze stacks using existing gateway and observability components.

Raw deployment evidence, credentials, private topology, and security-sensitive operational details are not published here. Public materials are limited to specifications, profiles, sanitized attestations, examples, and implementation guidance.

Bronze Claim Tool

The Bronze claim tool (scripts/proofrail_claim.py) performs structural validation of Bronze claim YAML files. It can generate claim scaffolds, validate claim structure and evidence references, and produce human-readable summaries. It does not certify deployments or verify full semantic conformance.

Usage:

    pip install -r requirements.txt
    python scripts/proofrail_claim.py init --profile bronze --type composed --out claim.yaml
    python scripts/proofrail_claim.py validate claim.yaml
    python scripts/proofrail_claim.py summarize claim.yaml

A demo (Demo 001B) of the claims tool on a simplified composed Bronze stack is available in the demos/composed-bronze-demo-001 folder.
