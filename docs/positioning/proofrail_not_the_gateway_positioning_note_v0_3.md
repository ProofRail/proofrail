# ProofRail™ Is Not The Gateway

v0.3 - 2026-06-21

## Short Thesis

ProofRail™ is not an AI gateway, observability platform, model-evaluation suite, SIEM, or AI governance dashboard.

ProofRail is the evidence and reliance layer for protected action control.

Gateways may mediate traffic. Observability systems may record traces. Governance platforms may manage policies, risks, and approvals. ProofRail asks a narrower question:

> Can a relying party independently verify that a protected action was governed by a declared control boundary, scoped authority, revocation posture, bypass handling, and tamper-evident evidence?

That is the category ProofRail is trying to define.

## Why This Distinction Matters

The AI governance and agent-security market is filling quickly. Many products now claim some combination of agent governance, MCP security, tool-call policy, audit trails, compliance reporting, observability, red teaming, prompt-injection defense, or AI risk management.

Those are important capabilities. ProofRail should complement many of them.

But they do not, by themselves, answer the relying-party question:

> What exactly am I being asked to trust, who asserted it, what evidence supports it, how was it verified, what was revoked, and what happens if the claim is later challenged?

ProofRail starts from that reliance question and works backward to the minimum evidence needed for a protected action claim.

## The Positioning Boundary

ProofRail should not be positioned as:

- a better MCP gateway;
- a universal AI security platform;
- a prompt-injection detector;
- a model behavior evaluator;
- a general GRC workflow tool;
- a SIEM replacement;
- a production certification authority;
- a regulator, auditor, or approval body.

ProofRail should be positioned as:

- a vendor-neutral evidence and reliance framework;
- a way to define protected actuator sets and controlled action paths;
- a way to package evidence about enforcement, bypass handling, revocation, and emergency-stop behavior;
- a way for independent verifiers to check evidence without trusting the runner's narrative;
- a maturity ladder from local evidence to cross-party reliance and, eventually, governed acceptance.

## Category Map

| Market layer | What it usually does | ProofRail relationship |
|---|---|---|
| AI governance / GRC platform | Maintains AI inventory, policies, risks, assessments, approvals, and audit workflows. | ProofRail can supply machine-checkable evidence objects that support specific control claims. |
| AI gateway / MCP gateway / runtime policy layer | Mediates model, tool, API, MCP, or A2A traffic and may enforce authentication, authorization, rate limits, policy, and logging. | ProofRail can treat the gateway as a substrate, then ask whether its protected-action claims are evidenced and independently verifiable. |
| Observability / tracing / SIEM | Captures traces, logs, metrics, incidents, and operational telemetry. | ProofRail can bind selected traces or logs into a claim-specific evidence bundle. Telemetry alone is not reliance. |
| Model evaluation / red teaming | Tests model behavior, prompt robustness, tool misuse, jailbreaks, or unsafe outputs. | ProofRail is adjacent but different: it focuses on controlled action paths and evidence that protected actions could not proceed outside declared authority. |
| Compliance evidence automation | Maps controls to regulatory or framework obligations and generates audit artifacts. | ProofRail can provide concrete technical evidence for some claims, but does not claim compliance by itself. |
| ProofRail | Defines evidence requirements for protected action control and supports independent verification of those claims. | ProofRail is the reliance layer: what evidence survives inspection when someone asks, "Why should I trust this protected action boundary?" |

## The Core ProofRail Claim

ProofRail's strongest claim is deliberately narrow:

> A protected action should not be trusted merely because an agent, gateway, dashboard, or compliance report says it was controlled. It should be trusted only to the extent that the control claim is backed by scoped authority, declared control surfaces, bypass evidence, revocation posture, and independently verifiable artifacts.

In the Silver multi-agent line, the claim becomes:

> In a multi-principal agent environment, trust does not attach to the agent. Trust attaches to scoped authority, controlled action paths, and independently verifiable evidence.

## Why The Gateway Is Not Enough

A gateway can be essential infrastructure. It may enforce policy, authenticate callers, route traffic, manage MCP tools, emit logs, and block dangerous requests.

But a relying party still needs to know:

- Which actions were considered protected?
- Was the protected actuator set declared and hashed?
- Could the agent reach the actuator outside the gateway?
- Were bypass attempts tested?
- Were emergency-stop semantics tested?
- Were authority decisions recorded in a stable format?
- Was revocation checked?
- Were evidence artifacts signed, hashed, or otherwise tamper-evident?
- Did an independent verifier check the package?
- Did the verifier make a technical finding only, or did someone treat it as a certification decision?
- Who accepted the finding, under what policy, and with what right to challenge it?

That is the difference between runtime control and reliance-grade evidence.

## Unsupported Claims

A common failure mode involves a polished compliance narrative unsupported by shipped behavior or verifiable artifacts.

That is exactly the type of failure mode ProofRail is meant to make more difficult:

> A control claim should fail if the evidence does not support it, even when the surrounding compliance narrative sounds complete.

## Silver And Gold Boundary

Silver should answer:

- Was the evidence bundle well formed?
- Were required hashes present and correct?
- Was revocation considered?
- Did the verifier produce a structured report?
- Can the relying party inspect the evidence without trusting the original runner's story?
- In the multi-agent demo, do harmless messages, authorized actions, unauthorized delegation, bypass attempts, and revoked authority produce expected evidence?

Silver should not answer:

- Is the live deployment safe?
- Is the organization certified?
- Is the agent trustworthy in general?
- Is the runtime substrate production-ready?
- Has a regulator, auditor, or certifier approved the system?

ProofRail Gold starts where a relying party does more than verify evidence: verification outputs become inputs to governed acceptance, rejection, review, challenge, dispute handling, retention, and accountability workflows.

The correct v0.2.5 boundary is:

> v0.2.5 packages the Silver trust-boundary evidence. It does not certify live agents or create Gold acceptance.

And:

> v0.2.5 names the Gold boundary. It does not cross it.

## v0.2.6 Direction

The next step for ProofRail is an Evidence Source Adapter profile.

Gateways, observability systems, SIEMs, policy engines, GRC platforms, and native ProofRail deployments may all produce useful evidence. v0.2.6 should define how those sources describe their control surface, protected action IDs, decision events, bypass evidence, revocation posture, subject hashes, and normalization notes before entering a ProofRail bundle.

## Suggested Public Language

ProofRail is not trying to replace the AI gateway, the SIEM, the observability stack, or the governance dashboard.

Those systems may be where controls run, where events are observed, or where organizational workflows live.

ProofRail addresses the next question:

> When someone asks whether a protected action was actually controlled, what evidence can a relying party inspect, verify, reject, revoke, or later challenge?

That is why ProofRail starts with protected actuator sets, bypass-handling evidence, emergency-stop semantics, signed or hashed evidence bundles, revocation posture, independent verification reports, and a disciplined boundary between technical verification and governed acceptance.

The goal is not to create another place to click "approve."

ProofRail exists to make unsupported protected-action claims harder to make, easier to detect, and harder to rely on accidentally.

## One-Sentence Version

ProofRail is the vendor-neutral evidence and reliance layer for protected action control: gateways enforce, observability records, and governance tools manage workflows; but ProofRail defines what evidence must survive independent verification before a protected-action claim can be relied upon.

