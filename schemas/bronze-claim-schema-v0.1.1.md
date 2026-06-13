# ProofRail Bronze Claim Schema v0.1.1

**Version:** v0.1.1
**Date:** 2026-06-13
**Status:** Draft / Demo-informed schema
**Derived from:** ProofRail Composed Bronze Demo 001b
**Claim family:** ProofRail Bronze local-enterprise conformance/evidence claims

---

## 1. Purpose

The ProofRail Bronze Claim Schema defines the minimum structured YAML fields required to make a local Bronze-style conformance/evidence claim.

Version v0.1.1 incorporates lessons from **ProofRail Composed Bronze Demo 001b**, which demonstrated that a Bronze-style claim can be generated from a composed stack using an existing gateway substrate rather than a ProofRail-native proxy.

This schema supports both:

* **Native Bronze claims** — controls implemented directly by ProofRail-native components.
* **Composed Bronze claims** — controls satisfied by a composition of existing gateway, identity, logging, network, secret, runbook, and evidence components.

The purpose of v0.1.1 is not to create a production certification regime. It is to stabilize the schema semantics needed for early Bronze-style evidence packages and local validation.

---

## 2. Design Principles

### 2.1 Deployment claim, not merely product claim

A Bronze claim is a **deployment claim**, not merely a product claim.

A product or gateway may provide some required control capabilities, but a deployment is only claimable if the declared surface, protected actuator set, evidence files, and validation records collectively demonstrate the required control properties.

### 2.2 Composable control satisfaction

A composed deployment may satisfy Bronze controls using existing components, including:

* MCP gateways
* API gateways
* identity providers
* Docker or Kubernetes network segmentation
* secret stores
* SIEM/logging systems
* observability tools
* runbooks
* evidence-generation scripts

The claim must identify which component satisfied which control.

### 2.3 Truth-preserving mechanism details

A Bronze claim must be honest about what was actually observed.

Aggregated controls may be satisfied by alternative mechanisms, but the claim must preserve the observed mechanism details.

For example, the aggregate control:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true
```

may be supported by both observed rate limiting and observed circuit-breaker behavior:

```yaml
control_details:
  rate_limit_observed: true
  circuit_breaker_observed: true
```

or only by circuit-breaker behavior:

```yaml
control_details:
  rate_limit_observed: false
  circuit_breaker_observed: true
```

Both are valid if supported by evidence.

### 2.4 Evidence-first framing

A Bronze claim should be auditable from its evidence bundle.

The claim should not rely on prose assertions alone. It should identify:

* the protected actuator set
* the control surface
* the mediation substrate
* evidence files
* known limitations
* validation status

---

## 3. Claim Types

v0.1.1 supports two claim types:

```yaml
claim_type: "proofrail.bronze.native"
```

and:

```yaml
claim_type: "proofrail.bronze.composed"
```

### 3.1 Native Bronze claim

A native Bronze claim is used when the control plane is implemented directly by ProofRail-native components.

### 3.2 Composed Bronze claim

A composed Bronze claim is used when the deployment satisfies ProofRail Bronze controls through a composition of existing infrastructure components.

Composed claims must include a `substrate` section.

---

## 4. Required Top-Level Fields

A v0.1.1 Bronze claim must include:

```yaml
spec_version: "v0.1.1"
claim_type: "proofrail.bronze.composed"
claim_id: string
claim_label: string
profile: "bronze"
mode: "monitor" | "enforce"
environment: "dev" | "test" | "staging" | "prod"
surfaces_in_scope:
  - "mcp"
```

### 4.1 Field meanings

| Field               | Required | Meaning                                                      |
| ------------------- | -------: | ------------------------------------------------------------ |
| `spec_version`      |      Yes | Schema version. Must be `v0.1.1`.                            |
| `claim_type`        |      Yes | `proofrail.bronze.native` or `proofrail.bronze.composed`.    |
| `claim_id`          |      Yes | Unique identifier for this claim instance.                   |
| `claim_label`       |      Yes | Human-readable claim label.                                  |
| `profile`           |      Yes | Must be `bronze`.                                            |
| `mode`              |      Yes | Operating mode: `monitor` or `enforce`.                      |
| `environment`       |      Yes | Deployment environment: `dev`, `test`, `staging`, or `prod`. |
| `surfaces_in_scope` |      Yes | Protocol or actuation surfaces covered by this claim.        |

### 4.2 Surface values

Initial supported surface values include:

```yaml
surfaces_in_scope:
  - "mcp"
```

Future schemas may add:

```yaml
surfaces_in_scope:
  - "a2a"
  - "http"
  - "custom"
```

---

## 5. Substrate Section

For composed Bronze claims, `substrate` is required.

```yaml
substrate:
  name: string
  type: string
  version_declared: string
  role: string
  source_url: string
```

### 5.1 Required substrate fields

| Field              |    Required | Meaning                                              |
| ------------------ | ----------: | ---------------------------------------------------- |
| `name`             |         Yes | Name of the substrate or primary composed component. |
| `type`             |         Yes | Component type, such as `open-source MCP gateway`.   |
| `version_declared` |         Yes | Version asserted for the substrate.                  |
| `role`             |         Yes | Role played by the substrate in the deployment.      |
| `source_url`       | Recommended | Public or internal source URL for the substrate.     |

### 5.2 Example composed substrate

```yaml
substrate:
  name: "agentgateway"
  type: "open-source MCP gateway"
  version_declared: "v1.2.1 docker image"
  role: "MCP mediation, routing, protocol session enforcement, rate limiting, and observability source"
  source_url: "https://github.com/agentgateway/agentgateway"
```

### 5.3 Example native substrate

For native Bronze claims, `substrate` may be omitted or declared as:

```yaml
substrate:
  name: "ProofRail native"
  type: "native ProofRail implementation"
  version_declared: string
  role: "native ProofRail control surface"
```

---

## 6. Protected Actuator Set

A Bronze claim must declare the protected actuator set.

```yaml
protected_actuator_set:
  name: string
  surface: "mcp" | "a2a" | "http" | "custom"
  hash: "sha256:<hex>"
  contents:
    - string
```

### 6.1 Field meanings

| Field      |    Required | Meaning                                                 |
| ---------- | ----------: | ------------------------------------------------------- |
| `name`     |         Yes | Name of the protected actuator set.                     |
| `surface`  |         Yes | Surface to which the actuator set belongs.              |
| `hash`     |         Yes | Stable SHA-256 hash of the canonical actuator manifest. |
| `contents` | Recommended | Human-readable actuator names in scope.                 |

### 6.2 Hash rule

The protected actuator set hash must be computed from a canonical manifest.

The canonical manifest should use:

* sorted JSON keys
* deterministic serialization
* sorted `contents` list
* SHA-256 digest
* `sha256:` prefix

Example:

```yaml
protected_actuator_set:
  name: "proofrail-demo-001-mock-actuators"
  surface: "mcp"
  hash: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  contents:
    - "demo.read"
    - "ticket.create"
    - "deploy.push"
    - "admin.rotate_secret"
```

### 6.3 Contents disclosure

`contents` should be included for internal evidence bundles.

For public claims, `contents` may be redacted if a canonical manifest exists in the evidence bundle and the hash is preserved.

---

## 7. Controls Section

A v0.1.1 Bronze claim must include the following control booleans:

```yaml
controls:
  declared_actuator_set: true
  gateway_mediation: true
  bypass_prevention_tested: true
  stop_control_demonstrated: true
  rate_limit_or_circuit_breaker_demonstrated: true
  normalized_audit_evidence: true
  performance_measured: true
  runbook_present: true
```

All control values must be boolean.

For a passing Bronze v0.1.1 claim, all listed controls must be `true`.

### 7.1 Control meanings

#### `declared_actuator_set`

The claim identifies the protected actuator set in scope.

#### `gateway_mediation`

Actions in the declared surface were routed through a control point.

For composed claims, the gateway or mediation substrate must be identified in `substrate` and `control_mapping`.

#### `bypass_prevention_tested`

The evidence includes tests showing that agent workloads cannot directly reach or directly credential themselves against the protected actuator set.

Bypass prevention evidence should include at least one of:

* network isolation test
* credential containment test
* direct upstream reachability failure
* upstream secret absence from agent-side runtime
* equivalent deployment-specific bypass test

#### `stop_control_demonstrated`

The evidence shows that actuation can be blocked through a stop-control, emergency-stop, kill-switch, circuit-breaker, or equivalent halt mechanism.

#### `rate_limit_or_circuit_breaker_demonstrated`

The evidence shows either:

* rate limiting
* throttling
* quota enforcement
* circuit-breaker behavior
* emergency stop
* stop-control
* equivalent actuation halt or flow-control behavior

This is an aggregate control. It does not imply that both rate limiting and circuit-breaker behavior were observed unless `control_details` says so.

#### `normalized_audit_evidence`

The evidence includes structured ProofRail-style events or a normalization artifact mappable to ProofRail audit semantics.

For early demos, script-generated normalized evidence is acceptable if this limitation is disclosed.

#### `performance_measured`

The evidence includes latency or performance measurement.

If the measurement is only a smoke benchmark, the limitations section must say so.

#### `runbook_present`

A runbook exists and is included or referenced in evidence.

The runbook should describe:

* unsafe actuator definition
* stop-control procedure
* resume procedure
* incident investigation procedure
* evidence locations

---

## 8. Control Details Section

v0.1.1 adds `control_details` to prevent overclaiming.

```yaml
control_details:
  rate_limit_observed: true | false
  circuit_breaker_observed: true | false
  note: string
```

### 8.1 Required fields

| Field                      |    Required | Meaning                                                                                    |
| -------------------------- | ----------: | ------------------------------------------------------------------------------------------ |
| `rate_limit_observed`      |         Yes | Whether rate limiting, throttling, or quota enforcement was observed.                      |
| `circuit_breaker_observed` |         Yes | Whether stop-control, emergency-stop, or equivalent circuit-breaker behavior was observed. |
| `note`                     | Recommended | Human-readable clarification.                                                              |

### 8.2 Aggregate validation rule

If:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true
```

then at least one of the following must also be true:

```yaml
control_details:
  rate_limit_observed: true
```

or:

```yaml
control_details:
  circuit_breaker_observed: true
```

### 8.3 Valid examples

Rate limit and circuit breaker both observed:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true

control_details:
  rate_limit_observed: true
  circuit_breaker_observed: true
  note: "Both local rate limiting and stop-control circuit-breaker behavior were observed."
```

Circuit breaker observed, rate limit not observed:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true

control_details:
  rate_limit_observed: false
  circuit_breaker_observed: true
  note: "Circuit-breaker behavior was observed. Rate-limit policy attachment remains unresolved."
```

Invalid example:

```yaml
controls:
  rate_limit_or_circuit_breaker_demonstrated: true

control_details:
  rate_limit_observed: false
  circuit_breaker_observed: false
```

---

## 9. Control Mapping Section

A Bronze claim should map each control to the component and evidence supporting it.

```yaml
control_mapping:
  gateway_mediation:
    component: string
    evidence: string
  bypass_prevention:
    component: string
    evidence: string
  stop_control:
    component: string
    evidence: string
  rate_limit_circuit_breaker:
    component: string
    evidence: string
  audit_normalization:
    component: string
    evidence: string
```

### 9.1 Purpose

The purpose of `control_mapping` is to show how the deployment satisfies the ProofRail claim without requiring every control to be implemented by a ProofRail-native component.

### 9.2 Example

```yaml
control_mapping:
  gateway_mediation:
    component: "agentgateway"
    evidence: "evidence/agentgateway-log-sample.txt"
  bypass_prevention:
    component: "Docker Compose network segmentation + Docker secrets"
    evidence: "evidence/bypass-test-results.md"
  stop_control:
    component: "agentgateway target switch to stop-mcp server"
    evidence: "evidence/emergency-stop-test.md"
  rate_limit_circuit_breaker:
    component: "agentgateway local rate limit + ProofRail stop-control circuit breaker"
    evidence: "evidence/rate-limit-test.md"
  audit_normalization:
    component: "ProofRail evidence scripts"
    evidence: "evidence/audit-sample.jsonl"
```

---

## 10. Evidence Section

A v0.1.1 Bronze claim must include evidence file references.

```yaml
evidence:
  architecture_notes: string
  runbook: string
  protected_actuator_set_manifest: string
  bypass_prevention_test: string
  stop_control_test: string
  rate_limit_circuit_breaker_test: string
  audit_sample: string
  performance_test: string
```

### 10.1 Required evidence keys

| Evidence key                      | Required | Meaning                                              |
| --------------------------------- | -------: | ---------------------------------------------------- |
| `architecture_notes`              |      Yes | Architecture description for the deployment.         |
| `runbook`                         |      Yes | Operational runbook.                                 |
| `protected_actuator_set_manifest` |      Yes | Canonical protected actuator set manifest.           |
| `bypass_prevention_test`          |      Yes | Bypass prevention test results.                      |
| `stop_control_test`               |      Yes | Stop-control or emergency-stop evidence.             |
| `rate_limit_circuit_breaker_test` |      Yes | Rate-limit, throttling, or circuit-breaker evidence. |
| `audit_sample`                    |      Yes | Structured or normalized audit sample.               |
| `performance_test`                |      Yes | Latency or performance evidence.                     |

### 10.2 Recommended evidence keys

```yaml
evidence:
  substrate_log_sample: string
  demo_summary: string
  checksum_file: string
```

### 10.3 Evidence path rule

Evidence paths should be relative to the claim package root unless an external URI is explicitly required.

---

## 11. Validation Section

A v0.1.1 Bronze claim must include a validation section.

```yaml
validation:
  type: "self-attested-demo" | "self-attested" | "third-party"
  validator: string
  generated_at: ISO-8601 timestamp
  missing_evidence_files:
    - string
```

### 11.1 Field meanings

| Field                    | Required | Meaning                                                                          |
| ------------------------ | -------: | -------------------------------------------------------------------------------- |
| `type`                   |      Yes | Validation type.                                                                 |
| `validator`              |      Yes | Validator name or description.                                                   |
| `generated_at`           |      Yes | Claim generation timestamp.                                                      |
| `missing_evidence_files` |      Yes | List of missing evidence files. Should be empty for a complete evidence package. |

### 11.2 Validation types

```yaml
validation:
  type: "self-attested-demo"
```

Used for local demos and experimental evidence loops.

```yaml
validation:
  type: "self-attested"
```

Used for organization-controlled internal assertions.

```yaml
validation:
  type: "third-party"
```

Reserved for future independent validation.

---

## 12. Limitations Section

v0.1.1 requires explicit limitations.

```yaml
limitations:
  - string
```

### 12.1 Purpose

The limitations section prevents overclaiming and distinguishes demos from production assertions.

A claim must include limitations clarifying whether the claim is:

* a local demo
* a production deployment assertion
* based on mock actuators
* based on script-normalized audit evidence
* based on smoke performance measurements
* dependent on manual configuration switching
* dependent on restarts
* limited to a specific protocol surface
* limited to a specific test environment

### 12.2 Example

```yaml
limitations:
  - "Demo 001b is a local Docker Compose test environment, not a production conformance assertion."
  - "The protected actuator set is a mock MCP actuator set."
  - "Stop control is implemented by switching gateway target configuration and restarting agentgateway."
  - "Audit evidence is normalized by demo scripts, not exported from a production SIEM."
  - "Latency measurement is a smoke benchmark and not a ProofRail-added latency assertion."
```

---

## 13. Minimal Valid v0.1.1 Example

```yaml
spec_version: "v0.1.1"
claim_type: "proofrail.bronze.composed"
claim_id: "proofrail-demo-001b-20260613"
claim_label: "ProofRail Composed Bronze Demo 001b — agentgateway MCP substrate — test env"
profile: "bronze"
mode: "enforce"
environment: "test"
surfaces_in_scope:
  - "mcp"

substrate:
  name: "agentgateway"
  type: "open-source MCP gateway"
  version_declared: "v1.2.1 docker image"
  role: "MCP mediation, routing, protocol session enforcement, rate limiting, and observability source"
  source_url: "https://github.com/agentgateway/agentgateway"

protected_actuator_set:
  name: "proofrail-demo-001-mock-actuators"
  surface: "mcp"
  hash: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  contents:
    - "demo.read"
    - "ticket.create"
    - "deploy.push"
    - "admin.rotate_secret"

controls:
  declared_actuator_set: true
  gateway_mediation: true
  bypass_prevention_tested: true
  stop_control_demonstrated: true
  rate_limit_or_circuit_breaker_demonstrated: true
  normalized_audit_evidence: true
  performance_measured: true
  runbook_present: true

control_details:
  rate_limit_observed: true
  circuit_breaker_observed: true
  note: "Demo 001b demonstrates both rate limiting and stop-control circuit-breaker behavior."

control_mapping:
  gateway_mediation:
    component: "agentgateway"
    evidence: "evidence/agentgateway-log-sample.txt"
  bypass_prevention:
    component: "Docker Compose network segmentation + Docker secrets"
    evidence: "evidence/bypass-test-results.md"
  stop_control:
    component: "agentgateway target switch to stop-mcp server"
    evidence: "evidence/emergency-stop-test.md"
  rate_limit_circuit_breaker:
    component: "agentgateway local rate limit + ProofRail stop-control circuit breaker"
    evidence: "evidence/rate-limit-test.md"
  audit_normalization:
    component: "ProofRail evidence scripts"
    evidence: "evidence/audit-sample.jsonl"

evidence:
  architecture_notes: "docs/architecture.md"
  runbook: "docs/runbook.md"
  protected_actuator_set_manifest: "evidence/protected_actuator_set.json"
  bypass_prevention_test: "evidence/bypass-test-results.md"
  stop_control_test: "evidence/emergency-stop-test.md"
  rate_limit_circuit_breaker_test: "evidence/rate-limit-test.md"
  audit_sample: "evidence/audit-sample.jsonl"
  performance_test: "evidence/latency-benchmark.md"
  substrate_log_sample: "evidence/agentgateway-log-sample.txt"
  demo_summary: "DEMO_001B_RESULTS.md"

validation:
  type: "self-attested-demo"
  validator: "ProofRail Bronze claim validator v0.1.1 structural check"
  generated_at: "2026-06-13T04:04:27Z"
  missing_evidence_files: []

limitations:
  - "Demo 001b is a local Docker Compose test environment, not a production conformance assertion."
  - "The protected actuator set is a mock MCP actuator set."
  - "Stop control is implemented by switching gateway target configuration and restarting agentgateway."
  - "Audit evidence is normalized by demo scripts, not exported from a production SIEM."
  - "Latency measurement is a smoke benchmark and not a ProofRail-added latency assertion."
```

---

## 14. Validator Semantics

A local v0.1.1 validator should perform structural validation only.

It should not assert production conformance.

### 14.1 Required structural checks

A local validator should check:

* root is a YAML mapping
* `spec_version` is `v0.1.1`
* `claim_type` is one of:

  * `proofrail.bronze.native`
  * `proofrail.bronze.composed`
* `profile` is `bronze`
* `mode` is `monitor` or `enforce`
* `environment` is `dev`, `test`, `staging`, or `prod`
* `surfaces_in_scope` is a non-empty list
* composed claims include `substrate`
* protected actuator set includes `name`, `surface`, and valid `sha256:` hash
* all required controls exist and are boolean
* all required controls are `true` for a passing Bronze claim
* `control_details.rate_limit_observed` exists and is boolean
* `control_details.circuit_breaker_observed` exists and is boolean
* if `rate_limit_or_circuit_breaker_demonstrated` is true, at least one of `rate_limit_observed` or `circuit_breaker_observed` is true
* required evidence keys exist and are non-empty strings
* validation section includes required fields
* limitations is a non-empty list of non-empty strings

### 14.2 Non-goals

The local structural validator does not:

* inspect external systems
* independently confirm network topology
* verify cryptographic signatures
* certify production deployment conformance
* validate that evidence files are truthful
* replace human or third-party review

---

## 15. v0.1.0 to v0.1.1 Change Log

v0.1.1 adds:

* explicit `claim_type` distinction for composed vs native Bronze claims
* required `substrate` section for composed claims
* required `control_details`
* explicit distinction between:

  * `rate_limit_observed`
  * `circuit_breaker_observed`
* required `limitations`
* clearer evidence requirements for composed deployments
* clearer rule that `rate_limit_or_circuit_breaker_demonstrated` is an aggregate control, not a claim that both mechanisms were observed
* explicit validator semantics
* Demo 001b-informed examples

---

## 16. Interpretation Notes

### 16.1 Bronze is local-enterprise scoped

Bronze is intended for local deployment claims.

A Bronze claim does not imply federation, cross-organization revocation, external certification, or ecosystem-wide trust propagation.

### 16.2 Composed Bronze does not require ProofRail-native enforcement

A composed Bronze claim may rely on existing tools if the evidence demonstrates that the deployment satisfies the required control properties.

### 16.3 Bypass prevention is deployment-specific

Bypass prevention is not satisfied merely because a gateway exists.

The claim must include deployment-specific evidence showing that the agent-side workload cannot bypass the declared control point to reach or credential itself against the protected actuator set.

### 16.4 Rate limiting and circuit breaker are distinct observations

The aggregate control remains:

```yaml
rate_limit_or_circuit_breaker_demonstrated: true
```

But v0.1.1 requires the claim to state which mechanism was actually observed.

### 16.5 Limitations are required evidence hygiene

Limitations are not admissions of failure.

They are part of the evidence discipline that makes ProofRail claims trustworthy.

---

## 17. Recommended File Name

```text
schemas/bronze-claim-schema-v0.1.1.md
```

