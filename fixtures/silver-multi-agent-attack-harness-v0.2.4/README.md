# ProofRail Silver v0.2.4 Multi-Agent Attack Harness Fixture

This directory contains the canonical, deterministic script for the ProofRail Silver v0.2.4 multi-agent attack harness.

## Contents

- `harness-script.yaml` — Canonical harness script. Single source of truth for both event order and expected outcomes.
- `README.md` — This file.

No runtime outputs are committed here. The runner writes all generated artifacts to an output directory (typically under `/tmp`).

## Authority Source

The script references the v0.2.3 multi-principal authority fixture at:

```
fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml
```

The harness does not duplicate authority rules. Protected-action events are evaluated by the unchanged v0.2.3 authority evaluator at the event timestamp.

## Reproducing the Run

From the repository root:

```bash
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
  --script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --output-dir /tmp/proofrail-silver-multi-agent-harness-v0.2.4 \
  --force

python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py \
  --manifest /tmp/proofrail-silver-multi-agent-harness-v0.2.4/harness-evidence-manifest.json
```

Or via Make targets:

```bash
make run-silver-multi-agent-harness-v0-2-4
make verify-silver-multi-agent-harness-v0-2-4
```

## Canonical Scenarios

| # | Event ID | Type | Expected outcome | Notes |
|---|---|---|---|---|
| 1 | EVT-001-harmless-message | agent_message | message_delivered | No evaluator call. |
| 2 | EVT-002-allowed-payment-release | protected_action_attempt | action_allowed | Within constraint (amount 1250, vendor vendororg). |
| 3 | EVT-003-allowed-vendor-approval | protected_action_attempt | action_allowed | Before revocation marker. |
| 4 | EVT-004-delegation-laundering | protected_action_attempt | action_denied | Subject mismatch on delegated grant. |
| 5 | EVT-005-bypass-payment-release | bypass_attempt | bypass_blocked | Harness-level block. No evaluator call. |
| 6 | EVT-006-data-export-out-of-scope | protected_action_attempt | action_denied | Dataset outside allowed list. |
| 7 | EVT-007-deploy-change-out-of-scope | protected_action_attempt | action_denied | Environment outside allowed list. |
| 8 | EVT-008-revocation-marker | revocation_marker | revocation_marked | Aligned with fixture revoked_at. |
| 9 | EVT-009-vendor-approval-after-revocation | protected_action_attempt | action_denied | authority_revoked. |

## Non-Claims

This fixture and the harness around it do **not**:

- prove live multi-agent safety;
- parse natural language;
- detect arbitrary prompt injection;
- evaluate live model behavior;
- invoke any real actuator;
- produce signed certification evidence;
- constitute Gold governed acceptance.

Every decision report keeps `execution.performed == false`. Every run report keeps `execution.protected_actions_performed == false`.
