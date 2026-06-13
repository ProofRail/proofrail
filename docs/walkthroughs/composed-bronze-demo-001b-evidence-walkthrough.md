# ProofRail Composed Bronze Demo 001b — Evidence Walkthrough

**Demo:** Composed Bronze Demo 001b
**Status:** Evidence-frozen, schema-formalized, regression-tested
**Substrate:** agentgateway
**Surface:** MCP
**Profile:** Bronze
**Claim schema:** Bronze Claim Schema v0.1.1
**Environment:** Local Docker Compose test environment on a DigitalOcean 1GB test droplet

---

## 1. What This Walkthrough Explains

This walkthrough explains the evidence package produced by **ProofRail Composed Bronze Demo 001b**.

The purpose of the demo was to show that a ProofRail Bronze-style claim can be generated from a **composed stack** using existing infrastructure components, rather than only from a ProofRail-native proxy.

In this demo, ProofRail does not provide the gateway itself. Instead, the deployment composes:

* an open-source MCP gateway substrate,
* Docker Compose network segmentation,
* Docker secrets,
* mock MCP actuator services,
* stop-control behavior,
* rate limiting,
* evidence-generation scripts,
* normalized audit-style evidence,
* and a Bronze claim YAML.

The result is a structurally valid ProofRail Bronze v0.1.1 claim supported by an evidence bundle.

---

## 2. Why This Demo Matters

ProofRail is a vendor-neutral conformance and evidence framework for AI agent actuation control.

The core question for Composed Bronze is:

> Can ProofRail claims be generated from a stack using existing gateway, security, identity, observability, and operational components?

Demo 001b answers yes for a minimal local MCP stack.

The demo shows that ProofRail does not need to replace existing infrastructure. It can define the claim structure, evidence requirements, and control semantics that allow an existing substrate to participate in a ProofRail-style conformance story.

This is the key distinction between:

* **ProofRail-native Bronze**, where ProofRail components directly enforce the control surface, and
* **Composed Bronze**, where existing components collectively satisfy the required control evidence.

---

## 3. Demo Architecture

The demo stack consists of the following containers:

| Component       | Role                                    |
| --------------- | --------------------------------------- |
| `agent`         | Simulated agent-side client container   |
| `agentgateway`  | MCP mediation substrate                 |
| `mock-mcp`      | Mock protected MCP actuator server      |
| `stop-mcp`      | Emergency-stop / circuit-breaker target |
| `bypass-tester` | Agent-side bypass test container        |

The Docker Compose topology uses two networks:

| Network        | Purpose                                                             |
| -------------- | ------------------------------------------------------------------- |
| `agent_net`    | Agent-side network where the simulated agent and bypass tester live |
| `actuator_net` | Internal actuator-side network where protected MCP services live    |

The intended access path is:

```text
agent -> agentgateway -> mock-mcp
```

The prohibited bypass path is:

```text
agent -> mock-mcp
```

The demo verifies that the prohibited bypass path fails.

---

## 4. Protected Actuator Set

The protected actuator set is a mock MCP tool set exposed by `mock-mcp`.

It includes:

| Tool                  |   Tier | Description                     |
| --------------------- | -----: | ------------------------------- |
| `demo.read`           | Tier 0 | Read-only demo tool             |
| `ticket.create`       | Tier 1 | Reversible ticket creation      |
| `deploy.push`         | Tier 2 | Mock production deployment push |
| `admin.rotate_secret` | Tier 3 | Mock credential rotation action |

The actuator set is declared in:

```text
evidence/protected_actuator_set.json
```

The claim includes a deterministic SHA-256 hash of the canonical actuator manifest.

This matters because ProofRail claims should not merely say “a gateway was tested.” They should identify the specific protected action surface in scope.

---

## 5. Evidence Files

The Demo 001b evidence bundle includes the following key evidence files:

| Evidence file                          | Purpose                                                    |
| -------------------------------------- | ---------------------------------------------------------- |
| `docs/architecture.md`                 | Describes the composed demo architecture                   |
| `docs/runbook.md`                      | Describes operational procedures and stop-control handling |
| `evidence/protected_actuator_set.json` | Canonical protected actuator manifest                      |
| `evidence/bypass-test-results.md`      | Bypass prevention evidence                                 |
| `evidence/emergency-stop-test.md`      | Stop-control / circuit-breaker evidence                    |
| `evidence/rate-limit-test.md`          | Rate-limit evidence                                        |
| `evidence/audit-sample.jsonl`          | Normalized ProofRail-style audit sample                    |
| `evidence/latency-benchmark.md`        | Latency smoke benchmark                                    |
| `evidence/agentgateway-log-sample.txt` | Substrate log sample                                       |
| `claims/bronze-claim-demo-001.yaml`    | Generated Bronze claim YAML                                |
| `DEMO_001B_RESULTS.md`                 | Demo summary                                               |
| `DEMO_001C_HARNESS_CLEANUP.md`         | Harness cleanup note                                       |

---

## 6. Claim File

The generated Bronze claim is:

```text
claims/bronze-claim-demo-001.yaml
```

It conforms to:

```text
ProofRail Bronze Claim Schema v0.1.1
```

It was validated using:

```text
tools/claims/validate_bronze_claim_v0_1_1.py
```

The claim identifies itself as a composed Bronze claim:

```yaml
claim_type: proofrail.bronze.composed
profile: bronze
environment: test
surfaces_in_scope:
  - mcp
```

The claim identifies the substrate:

```yaml
substrate:
  name: agentgateway
  type: open-source MCP gateway
  version_declared: v1.2.1 docker image
  role: MCP mediation, routing, protocol session enforcement, rate limiting, and observability source
```

The claim includes the protected actuator set hash and evidence references.

---

## 7. Controls Demonstrated

### 7.1 Declared Actuator Set

The demo declares the protected MCP actuator set and computes a hash over the canonical manifest.

Claim field:

```yaml
controls:
  declared_actuator_set: true
```

Evidence:

```text
evidence/protected_actuator_set.json
```

This demonstrates that the claim is scoped to a specific actuator set.

---

### 7.2 Gateway Mediation

The simulated agent successfully accessed the mock MCP tools through agentgateway.

Evidence showed that `tools/list` returned the expected protected tool set:

```text
demo.read
ticket.create
deploy.push
admin.rotate_secret
```

Claim field:

```yaml
controls:
  gateway_mediation: true
```

Evidence:

```text
evidence/agentgateway-log-sample.txt
evidence/bypass-test-results.md
```

This demonstrates that the gateway path was functional.

---

### 7.3 Bypass Prevention

The demo tested whether the simulated agent could directly reach the upstream mock MCP actuator.

Observed result:

```text
PASS: agent could not reach upstream directly
```

The bypass tester container also failed to reach the upstream actuator directly:

```text
PASS: bypass-tester could not reach upstream directly
```

Claim field:

```yaml
controls:
  bypass_prevention_tested: true
```

Evidence:

```text
evidence/bypass-test-results.md
```

This demonstrates that the protected actuator server was not directly reachable from the agent-side network.

---

### 7.4 Credential Containment

The demo verified that the simulated agent did not possess the upstream MCP secret.

Observed result:

```text
PASS: agent has no upstream credential
```

This supports the bypass-prevention claim. Even if the agent knew the upstream service existed, it did not have the upstream credential.

Evidence:

```text
evidence/bypass-test-results.md
```

---

### 7.5 Stop-Control Circuit Breaker

The demo activated stop-control mode by switching the active agentgateway configuration to route to the `stop-mcp` service.

During stop-control mode, a mediated tool call returned an explicit emergency-stop response:

```json
{
  "jsonrpc": "2.0",
  "id": "call-read-1",
  "error": {
    "code": -32099,
    "message": "ProofRail stop control active",
    "data": {
      "reason": "emergency_stop",
      "proofrail_demo": "stop_mode"
    }
  }
}
```

Observed result:

```text
PASS: stop-control mode blocked tool call
```

Claim field:

```yaml
controls:
  stop_control_demonstrated: true
```

Evidence:

```text
evidence/emergency-stop-test.md
```

This demonstrates circuit-breaker behavior for agent actuation.

---

### 7.6 Rate Limiting

The demo used a rate-limit configuration for the explicit rate-limit section of the test.

The rate-limit test sent eight quick MCP requests. The gateway returned HTTP 429 responses after the allowed threshold was exceeded.

Observed throttling output after Demo 001c cleanup:

```text
THROTTLED: HTTP 429 during request: rate limit exceeded; limit=5 remaining=0 reset=56
THROTTLED: HTTP 429 during initialize: rate limit exceeded; limit=5 remaining=0 reset=55
```

Claim fields:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true

control_details:
  rate_limit_observed: true
  circuit_breaker_observed: true
```

Evidence:

```text
evidence/rate-limit-test.md
```

This demonstrates both rate-limit behavior and circuit-breaker behavior.

---

### 7.7 Normalized Audit Evidence

The demo generated normalized ProofRail-style audit evidence.

Claim field:

```yaml
controls:
  normalized_audit_evidence: true
```

Evidence:

```text
evidence/audit-sample.jsonl
```

This evidence is script-normalized demo evidence. It is not a production SIEM export.

That limitation is explicitly stated in the claim.

---

### 7.8 Performance Measurement

The demo includes a small latency smoke benchmark.

Example observed result:

```text
p95_ms: 338
samples: 20
```

Claim field:

```yaml
controls:
  performance_measured: true
```

Evidence:

```text
evidence/latency-benchmark.md
```

This is not a ProofRail-added latency measurement. It includes Docker execution overhead, MCP session initialization overhead, shell overhead, and the constraints of the 1GB test droplet.

The claim limitations explicitly state that this is only a smoke benchmark.

---

### 7.9 Runbook Present

The evidence bundle includes a runbook.

Claim field:

```yaml
controls:
  runbook_present: true
```

Evidence:

```text
docs/runbook.md
```

The runbook describes the demo’s unsafe actuator assumptions, stop-control procedure, resume procedure, and investigation path.

---

## 8. v0.1.1 Claim Semantics

Demo 001b directly informed the Bronze Claim Schema v0.1.1 update.

The most important schema improvement is the separation between the aggregate control:

```yaml
rate_limit_or_circuit_breaker_demonstrated: true
```

and the observed mechanism details:

```yaml
rate_limit_observed: true
circuit_breaker_observed: true
```

This prevents overclaiming.

A composed deployment may satisfy the aggregate Bronze control through rate limiting, circuit-breaker behavior, or both. The claim must preserve which mechanism was actually observed.

Demo 001b observed both.

---

## 9. What the Demo Proves

Demo 001b proves the following limited but important points:

1. A ProofRail Bronze-style claim can be produced from a composed stack.
2. The composed stack can use an existing MCP gateway substrate.
3. The protected actuator set can be declared and hashed.
4. Gateway mediation can be demonstrated.
5. Bypass prevention can be tested with network segmentation and credential containment.
6. Stop-control circuit-breaker behavior can be demonstrated.
7. Rate-limit behavior can be demonstrated.
8. Normalized audit-style evidence can be generated.
9. A Bronze claim YAML can be generated and structurally validated.
10. The demo can serve as a regression fixture for the Bronze v0.1.1 claim tooling.

---

## 10. What the Demo Does Not Prove

Demo 001b does not prove:

* production readiness
* third-party conformance
* cryptographic audit integrity
* real enterprise SIEM integration
* real protected enterprise actuator governance
* cross-organization federation
* dynamic policy management
* production-grade stop-control
* production latency performance
* broad compatibility with all MCP gateways
* compatibility with Lasso, ContextForge, Kong, or other substrates

The demo is intentionally local, minimal, and evidence-focused.

---

## 11. Known Limitations

The claim includes limitations, including:

* the demo is a local Docker Compose test environment
* the protected actuator set is a mock MCP actuator set
* stop-control is implemented by switching gateway target configuration and restarting agentgateway
* audit evidence is normalized by demo scripts, not exported from a production SIEM
* latency measurement is a smoke benchmark and not a ProofRail-added latency assertion

These limitations are not failures. They are part of the evidence discipline.

ProofRail claims should be clear about what they prove and what they do not prove.

---

## 12. How to Reproduce the Claim Validation

From a clean clone of the repo:

```bash
make generate-bronze-demo-001b
make validate-bronze-demo-001b
```

Expected result:

```text
PASS: demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml is structurally valid for ProofRail Bronze Claim Schema v0.1.1
PASS: Bronze claim v0.1.1 regression fixture valid
```

The generator uses:

```text
tools/claims/generate_bronze_claim_v0_1_1.py
```

The validator uses:

```text
tools/claims/validate_bronze_claim_v0_1_1.py
```

The demo input file is:

```text
demos/composed-bronze-demo-001/claim-input-v0.1.1.yaml
```

---

## 13. How to Reproduce the Live Demo Harness

From the demo directory:

```bash
cd demos/composed-bronze-demo-001
bash scripts/bootstrap.sh
docker compose up -d
bash scripts/run_tests.sh
python3 scripts/generate_bronze_claim.py
python3 scripts/validate_claim_v0_1_1.py claims/bronze-claim-demo-001.yaml
```

The harness requires Docker and Docker Compose.

The local upstream MCP secret is intentionally not committed. The bootstrap script creates local runtime state such as:

```text
secrets/upstream_mcp_api_key.txt
```

---

## 14. Evidence Freeze

The Demo 001b evidence was frozen into tarballs and downloaded to the local Mac.

Checksums were generated separately.

The frozen evidence package preserves:

* source files
* config files
* scripts
* evidence files
* claim YAML
* summary files
* Docker Compose topology
* mock services

The public repo contains the reproducible demo and evidence structure, but local secrets and frozen archives are intentionally not committed.

---

## 15. Interpretation

The most important result from Demo 001b is not that agentgateway is “the” ProofRail substrate.

The important result is that ProofRail can define a claim/evidence discipline that works across existing components.

In other words:

> ProofRail Bronze is not merely a proxy implementation. It is a structured deployment claim over a protected actuator set, supported by evidence.

Demo 001b is the first working example of that claim model in composed form.

---

## 16. Final Result

Final status:

**ProofRail Composed Bronze Demo 001b demonstrates a composed Bronze evidence loop using agentgateway as the MCP substrate, Docker Compose network segmentation, credential containment, stop-control circuit breaker behavior, rate limiting, normalized evidence, and a structurally valid Bronze Claim Schema v0.1.1 YAML claim.**

Demo 001c improves the harness so throttling evidence is recorded cleanly.

Together, Demo 001b and 001c establish the first durable composed Bronze reference example.

