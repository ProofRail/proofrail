# Runbook — ProofRail Composed Bronze Demo 001

## Unsafe actuator definition

For Demo 001, an unsafe actuator is any MCP tool with Tier 2 or Tier 3 impact:

- `deploy.push` — mock production deployment
- `admin.rotate_secret` — mock credential rotation

## Stop authority

The demo operator with SSH access to the 1GB test droplet may trigger stop-control.

```bash
bash scripts/stop_control.sh stop
```

## Restore service

```bash
bash scripts/stop_control.sh resume
bash scripts/run_tests.sh
```

Before treating the demo as healthy, confirm:

- Gateway path works.
- Bypass tests still pass.
- `evidence/emergency-stop-test.md` shows stop-control blocking.
- `evidence/audit-sample.jsonl` contains allowed and blocked decisions.

## Incident investigation

Use `correlation_id` in `evidence/audit-sample.jsonl` to link test calls to:

- `evidence/agentgateway-log-sample.txt`
- `evidence/*-response.json`
- terminal output captured from `scripts/run_tests.sh`

## Evidence refresh

```bash
bash scripts/run_tests.sh
python3 scripts/generate_bronze_claim.py
python3 scripts/validate_claim_v0_1.py claims/bronze-claim-demo-001.yaml
```
