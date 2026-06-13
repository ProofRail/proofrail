# Demo 001 Build Plan

## Decision

Use **agentgateway** as the first Composed Bronze substrate.

## Why not ContextForge first?

ContextForge is stronger as an enterprise registry/proxy and has rich federation/admin capabilities, but it is broader than this first evidence loop. It can be Demo 002 after the claim/evidence loop is proven.

## Why not Lasso first?

Lasso is security-focused and Python-friendly, but the open-source gateway is primarily plugin/guardrail oriented. Demo 001 needs rate-limit/circuit-breaker and gateway observability with as little custom plugin work as possible.

## Acceptance gates

1. `docker compose up -d` starts the substrate and mock actuator set.
2. Agent can call `tools/list` and `tools/call` through the gateway.
3. Agent cannot reach mock actuator directly.
4. Agent cannot access upstream actuator credential.
5. Bypass tester with actuator network access but no secret cannot call actuator.
6. Stop-control mode blocks all tool calls.
7. Rate-limit/circuit-breaker behavior is observed or the schema issue is documented.
8. `evidence/audit-sample.jsonl` includes required ProofRail-style fields.
9. Claim YAML is generated.
10. Claim YAML passes the local structural validator and then the official validator v0.1.

## Open implementation risk

The main risk is agentgateway configuration schema drift. Validate `config/agentgateway-run.yaml` with the installed binary or `agctl` on the test droplet. If the simplified `mcp:` config and top-level `policies.localRateLimit` cannot be combined, migrate to the full listener/route policy syntax for v1.2.1.
