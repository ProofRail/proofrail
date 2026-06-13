# ProofRail Composed Bronze Demo 001b Results

**Date:** 2026-06-13
**Demo:** Composed Bronze Demo 001b
**Substrate:** agentgateway Docker image
**Environment:** DigitalOcean 1GB test droplet
**Status:** Evidence-frozen; Bronze claim YAML structurally valid using local validator shim

## 1. Purpose

Composed Bronze Demo 001b demonstrates that a ProofRail Bronze-style evidence and claim loop can be produced from a composed stack using an existing open-source gateway substrate, rather than a ProofRail-native proxy.

The demo uses agentgateway as the MCP mediation layer, a mock protected MCP actuator set, Docker Compose network segmentation, stop-control behavior, rate limiting, evidence normalization scripts, and a local ProofRail Bronze claim validator shim.

The main purpose was not to produce a production-ready deployment, but to validate the concept that ProofRail claims can be generated from existing gateway/security/observability components when those components collectively satisfy the required control evidence.

## 2. Stack Summary

The Demo 001b stack consists of:

* `agentgateway` as the MCP gateway substrate
* `mock-mcp` as the protected actuator MCP server
* `stop-mcp` as the emergency-stop target
* `agent` as the simulated agent-side client container
* `bypass-tester` as an additional agent-side bypass test container
* Docker Compose network segmentation:

  * `agent_net`
  * `actuator_net`
* Docker secret file for upstream mock MCP credential containment
* ProofRail evidence scripts and claim generator

The protected actuator set includes:

* `demo.read` — Tier 0 read-only demo tool
* `ticket.create` — Tier 1 reversible ticket creation
* `deploy.push` — Tier 2 mock production deployment push
* `admin.rotate_secret` — Tier 3 mock credential rotation action

## 3. Evidence Freeze

Frozen evidence tarballs were created on the test droplet and downloaded to the Mac.

The frozen evidence package includes:

* `claims/`
* `docs/`
* `evidence/`
* `config/`
* `scripts/`
* `docker-compose.yml`
* `services/`

The evidence freeze preserves the runnable demo state, generated evidence files, configuration files, scripts, mock services, and the validated Bronze claim YAML.

A separate SHA-256 checksum file should be maintained on the Mac for long-term identification of the frozen evidence tarballs.

## 4. Test Run Summary

The final clean test run was executed with:

```bash
bash scripts/run_tests.sh
python3 scripts/generate_bronze_claim.py
python3 scripts/validate_claim_v0_1.py claims/bronze-claim-demo-001.yaml
```

The local validator returned:

```text
PASS: claims/bronze-claim-demo-001.yaml is structurally valid for local ProofRail Bronze claim v0.1 shim
```

The final claim contained:

```yaml
rate_limit_or_circuit_breaker_demonstrated: true
rate_limit_observed: true
circuit_breaker_observed: true
```

## 5. Controls Demonstrated

### 5.1 Bypass Prevention

The agent-side container could not resolve or reach the upstream mock MCP actuator directly.

Observed result:

```text
PASS: agent could not reach upstream directly
```

The bypass tester container, also placed on the agent-side network, likewise could not reach the upstream mock MCP actuator directly.

Observed result:

```text
PASS: bypass-tester could not reach upstream directly
```

This demonstrates that the mock actuator is only reachable through the gateway-mediated path.

### 5.2 Credential Containment

The agent container did not have access to the upstream mock MCP credential.

Observed result:

```text
PASS: agent has no upstream credential
```

This supports the ProofRail claim that the agent cannot bypass the gateway merely by using the upstream actuator credential directly.

### 5.3 Gateway Mediation

The agent successfully accessed the protected actuator set through agentgateway.

Observed result:

```text
PASS: gateway path produced a response
```

The mediated `tools/list` call returned the protected actuator set:

* `demo.read`
* `ticket.create`
* `deploy.push`
* `admin.rotate_secret`

Normal mediated tool calls also succeeded through the gateway:

* `demo.read`
* `deploy.push`

### 5.4 Stop-Control Circuit Breaker

Stop-control mode was activated by switching the active agentgateway config to route through `stop-mcp`.

A mediated tool call during stop-control mode returned an explicit emergency-stop error:

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

This demonstrates circuit-breaker behavior for the composed stack.

### 5.5 Rate Limiting

A separate `agentgateway-ratelimit.yaml` configuration was used for the rate-limit test.

The test sent eight quick requests against a configured target behavior of five requests per minute. The gateway returned HTTP 429 responses during the burst.

Observed rate-limit response:

```text
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 5
x-ratelimit-remaining: 0
x-ratelimit-reset: 55
rate limit exceeded
```

Observed result:

```text
PASS: rate-limit/circuit-breaker behavior observed
```

This demonstrates that the composed substrate can provide rate-limit behavior usable as ProofRail Bronze evidence.

### 5.6 Latency Smoke Benchmark

A small latency smoke benchmark was run over 20 calls after normal config was restored.

Observed result:

```text
p95_ms: 338
samples: 20
```

This value should not be treated as ProofRail-added gateway latency. It includes Docker execution overhead, MCP initialize/session overhead, shell overhead, and the constraints of the 1GB test droplet. It is retained only as a smoke benchmark.

## 6. Important Implementation Lessons

### 6.1 MCP Session Discipline

agentgateway enforced MCP Streamable HTTP session discipline.

Non-initialize requests required:

* `Accept: application/json, text/event-stream`
* a prior `initialize` call
* a returned `mcp-session-id`
* the `Mcp-Session-Id` header on subsequent requests

This was incorporated into `scripts/mcp_call_from_agent.sh`.

### 6.2 Docker Compose vs Gateway Config Boundary

A key integration lesson was that Docker Compose controls container topology, while agentgateway YAML controls gateway behavior.

`policies` cannot be added as a `services.agentgateway` property in `docker-compose.yml`. Docker Compose rejects that as an invalid service property.

Gateway policies must be placed in the mounted agentgateway configuration YAML.

### 6.3 Active Config Handling

The demo uses `config/agentgateway-active.yaml` as the live mounted file.

Helper behavior now distinguishes source configs from the live generated config:

* `config/agentgateway-normal.yaml` — normal routing source
* `config/agentgateway-ratelimit.yaml` — rate-limit source
* `config/agentgateway-stop.yaml` — emergency-stop source
* `config/agentgateway-active.yaml` — generated mounted file

`agentgateway-active.yaml` should not be edited directly.

## 7. Limitations

This is a local Docker Compose demonstration, not a production conformance assertion.

Known limitations:

* Stop-control is implemented by switching agentgateway configuration and restarting the gateway. A production-grade implementation should use dynamic policy, admin API control, or an external authorization path.
* Audit evidence is generated and normalized by demo scripts, not exported from a production SIEM.
* The latency result is only a smoke measurement.
* The Bronze validator is a local structural shim, not a final public ProofRail conformance validator.
* The protected actuator set is a mock actuator set, not a real enterprise action surface.
* The rate-limit test can interfere with later requests if the rate-limit bucket is not reset or if normal config is not restored. The final harness restores normal config after the rate-limit section.

## 8. Result

Composed Bronze Demo 001b successfully demonstrates that ProofRail Bronze-style evidence can be produced from a composed stack using an existing open-source gateway substrate.

The demo demonstrates:

* protected actuator set declaration
* gateway mediation
* bypass prevention
* credential containment
* stop-control circuit breaker behavior
* rate-limit behavior
* evidence normalization
* Bronze claim YAML generation
* structural validation of the Bronze claim

Final status:

**ProofRail Composed Bronze Demo 001b — agentgateway substrate, MCP mock actuator set, bypass prevention, stop-control circuit breaker, rate limiting, normalized evidence, valid Bronze claim YAML.**

