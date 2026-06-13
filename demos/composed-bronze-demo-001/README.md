# ProofRail Composed Bronze Demo 001

**Purpose:** demonstrate that a ProofRail Bronze claim can be composed from an existing MCP gateway substrate plus lightweight evidence tooling, without relying on the ProofRail Iron-plus native proxy.

**Chosen substrate:** `agentgateway` standalone Docker image.

Why this substrate for Demo 001:

- It is an open-source agentic proxy with MCP support.
- It has Docker deployment docs and an admin UI.
- It supports MCP targets and streamable HTTP routing.
- It has native rate-limiting, auth/policy, and OpenTelemetry/log observability hooks.
- It is lighter than a registry-first enterprise gateway stack and should be a better fit for a 1GB test droplet.

> This is a demo harness, not a production deployment. The agentgateway config files in `config/` should be validated against the installed `agentgateway` version on the droplet, because agentgateway’s schema is moving quickly.

## Demo claim

Composed Bronze Demo 001 shows:

1. A mock protected actuator set is declared and hashed.
2. Agent traffic reaches mock MCP actuators only through an open-source MCP gateway substrate.
3. Direct bypass from the agent network to the actuator network fails.
4. The upstream actuator credential is not present in the agent container.
5. A stop-control path can halt actuation by switching the gateway target to a stop server.
6. A rate-limit/circuit-breaker behavior is configured and tested.
7. Evidence files are normalized into ProofRail-style JSONL.
8. A Bronze claim YAML is generated and structurally validated.

## Directory layout

```text
config/
  agentgateway-run.yaml       # normal gateway config
  agentgateway-stop.yaml      # stop-mode gateway config
services/
  mock_mcp_server.py          # mock MCP actuator server, requires upstream secret
  stop_mcp_server.py          # MCP server that returns stopped errors
scripts/
  bootstrap.sh                # create secrets, build images, start stack
  run_tests.sh                # run demo evidence tests
  stop_control.sh             # switch gateway normal/stop mode
  actuator_set_hash.py        # deterministic actuator set hash
  generate_bronze_claim.py    # produce claim YAML from evidence
  validate_claim_v0_1.py      # local structural validator shim
evidence/
  protected_actuator_set.json # canonical covered tool list
  *.md / *.jsonl              # generated evidence
claims/
  bronze-claim-demo-001.yaml  # generated claim
```

## Quick start on the 1GB DigitalOcean test droplet

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin python3 python3-pip jq curl
sudo usermod -aG docker $USER
# log out/in or run: newgrp docker

cd ~/proofrail-composed-bronze-demo-001
bash scripts/bootstrap.sh
bash scripts/run_tests.sh
python3 scripts/generate_bronze_claim.py
python3 scripts/validate_claim_v0_1.py claims/bronze-claim-demo-001.yaml
```

## Expected evidence outputs

- `evidence/bypass-test-results.md`
- `evidence/emergency-stop-test.md`
- `evidence/rate-limit-test.md`
- `evidence/audit-sample.jsonl`
- `evidence/latency-benchmark.md`
- `claims/bronze-claim-demo-001.yaml`

## Important design notes

This demo intentionally avoids a heavy SIEM, identity provider, registry, or database. It uses Docker networks as the deployment control boundary and a local JSONL evidence bundle as the observable evidence layer.

The stop-control mechanism for Demo 001 is deliberately blunt: swap the gateway’s normal MCP target for a stop server and restart the gateway container. This is enough to demonstrate stoppability in a composed stack; later demos can replace it with native dynamic config reload, external authz, OPA/CEL policy, or a gateway plugin.

