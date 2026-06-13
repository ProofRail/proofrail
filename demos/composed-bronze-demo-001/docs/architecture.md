# Architecture — ProofRail Composed Bronze Demo 001

```text
agent container
  └── MCP JSON-RPC over HTTP
      └── agentgateway container  (open-source MCP gateway substrate)
          ├── normal mode → mock-mcp container  (protected actuators)
          └── stop mode   → stop-mcp container  (returns stopped errors)

Docker networks:
  agent_net:    agent ↔ agentgateway
  actuator_net: agentgateway ↔ mock-mcp / stop-mcp / bypass-tester

The agent container is not attached to actuator_net, so direct upstream access fails.
The mock actuator requires X-Upstream-Api-Key, mounted only as a Docker secret in mock-mcp.
```

## Substrate responsibilities

- MCP mediation/routing: agentgateway
- Rate-limit / circuit-breaker behavior: agentgateway local rate limit policy
- Stop-control behavior: agentgateway target switch to stop-mcp server
- Observability source: agentgateway logs/metrics

## ProofRail evidence responsibilities

- Protected actuator set manifest and hash
- Bypass test output
- Stop-control test output
- Rate-limit test output
- Normalized audit sample JSONL
- Bronze claim YAML generation and structural validation

## Demo limitations

This is intentionally a composed demo, not a ProofRail-native proxy. It demonstrates whether a Bronze claim can be made from existing gateway/security/observability components plus evidence normalization.
