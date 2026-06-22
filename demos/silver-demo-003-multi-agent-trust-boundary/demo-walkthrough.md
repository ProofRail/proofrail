# ProofRail Silver Demo 003 — Walkthrough

**Release:** v0.2.5
**Source harness:** v0.2.4 multi-agent attack harness
**Authority fixture:** v0.2.3 multi-principal authority

This walkthrough explains the demo's nine harness events and maps each one to the eight claims in `demo-summary.json`.

The harness runs entirely on local fixtures. No live agent is invoked. No live actuator is invoked. Every decision report records `execution.performed == false`.

---

## Event-by-Event Walkthrough

### EVT-001 — Harmless message

```text
buyerorg.agent  ----status request---->  vendororg.agent
```

- `event_type`: `agent_message`
- `actual.harness_outcome`: `message_delivered`
- No protected action attempted.
- **Maps to claim:** `harmless_messages_proceed`.

---

### EVT-002 — Allowed payment release

```text
buyerorg.agent  ----payment.release(amount_usd=1250)---->  proofrail.harness
```

- `event_type`: `protected_action_attempt`
- Grant: `buyer-payment-release-direct` (scoped, in-band).
- `decision.status`: `allow`
- `decision.reason`: `authority_requirements_satisfied`
- `execution.performed`: `false` (no real release).
- **Maps to claim:** `protected_actions_require_scoped_authority`.

---

### EVT-003 — Allowed vendor approval

```text
buyerorg.agent  ----vendor.approve(vendor=vendororg)---->  proofrail.harness
```

- Grant: `buyer-vendor-approval-direct`.
- `decision.status`: `allow`; `execution.performed`: `false`.
- **Maps to claim:** `protected_actions_require_scoped_authority`.

---

### EVT-004 — Delegation laundering attempt

```text
vendororg.agent  ----data.export with buyer-export-readonly-delegated---->  proofrail.harness
```

- VendorOrg attempts to use a delegated grant whose subject is `verifier.auditor`, not VendorOrg.
- `decision.status`: `deny`
- `decision.reason`: `authority_subject_mismatch`
- **Maps to claim:** `unauthorized_delegation_fails`.

---

### EVT-005 — Bypass attempt

```text
vendororg.agent  ----direct call to payment.release (bypass ProofRail)---->  payment.release
```

- `event_type`: `bypass_attempt`
- `actual.harness_outcome`: `bypass_blocked`
- `actual.harness_reason`: `bypass_attempt_detected`
- No decision report is generated. The bypass is recorded as transcript evidence.
- **Maps to claim:** `bypass_attempts_blocked`.

---

### EVT-006 — Out-of-scope data export

```text
verifier.auditor  ----data.export(dataset=customer-raw)---->  proofrail.harness
```

- Grant `buyer-export-readonly-delegated` is scoped to audit datasets, not `customer-raw`.
- `decision.status`: `deny`
- `decision.reason`: `constraint_not_satisfied`
- **Maps to claim:** `out_of_scope_actions_fail`.

---

### EVT-007 — Out-of-scope production deploy

```text
vendororg.agent  ----deploy.change(env=production)---->  proofrail.harness
```

- Grant `vendor-deploy-staging-direct` is scoped to staging only.
- `decision.status`: `deny`
- `decision.reason`: `constraint_not_satisfied`
- **Maps to claim:** `out_of_scope_actions_fail`.

---

### EVT-008 — Revocation marker

```text
proofrail.harness  ----revocation point: revoke-vendor-approval-001---->  proofrail.harness
```

- `event_type`: `revocation_marker`
- `actual.harness_outcome`: `revocation_marked`
- Aligned with the authority fixture's revocation entry `revoke-vendor-approval-001`.

---

### EVT-009 — Vendor approval after revocation

```text
buyerorg.agent  ----vendor.approve (after revocation)---->  proofrail.harness
```

- The same `buyer-vendor-approval-direct` grant that worked in EVT-003.
- After the EVT-008 revocation point, this request is denied.
- `decision.status`: `deny`
- `decision.reason`: `authority_revoked`
- **Maps to claim:** `revoked_authority_fails` (combined with EVT-008).

---

## Claims → Evidence Map

| Claim ID | Events | Concrete evidence |
|---|---|---|
| `harmless_messages_proceed` | EVT-001 | `harness-evidence/transcript.jsonl` |
| `protected_actions_require_scoped_authority` | EVT-002, EVT-003 | `harness-evidence/authority-decision-reports/EVT-002-allowed-payment-release.json`, `harness-evidence/authority-decision-reports/EVT-003-allowed-vendor-approval.json` |
| `unauthorized_delegation_fails` | EVT-004 | `harness-evidence/authority-decision-reports/EVT-004-delegation-laundering.json` |
| `bypass_attempts_blocked` | EVT-005 | `harness-evidence/transcript.jsonl` |
| `revoked_authority_fails` | EVT-008 + EVT-009 | `harness-evidence/transcript.jsonl` (marker) + `harness-evidence/authority-decision-reports/EVT-009-vendor-approval-after-revocation.json` |
| `out_of_scope_actions_fail` | EVT-006, EVT-007 | `harness-evidence/authority-decision-reports/EVT-006-data-export-out-of-scope.json`, `harness-evidence/authority-decision-reports/EVT-007-deploy-change-out-of-scope.json` |
| `evidence_is_hash_verifiable` | All | `harness-evidence/harness-evidence-manifest.json` (verified by v0.2.4 verifier) |
| `no_protected_actions_executed` | All | `harness-evidence/harness-run-report.json` (`execution.protected_actions_performed: false`) and every decision report (`execution.performed: false`) |

---

## Inspecting the Demo

After `make run-silver-multi-agent-demo-v0-2-5`, the relying party can:

1. Read `demo-summary.json` to see the claim → evidence map.
2. Walk the referenced evidence files in `harness-evidence/`.
3. Re-verify integrity with:

   ```bash
   python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \
     --package-manifest /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json
   ```

The verifier exits 0 on a clean package and 1 with a stable failure reason on tampering or malformed inputs. See `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md` for the full failure-reason table.

---

## Where Silver Ends, Where Gold Would Begin

Silver v0.2.5 demonstrates local hash-verifiable evidence of a deterministic multi-agent scenario. It does not provide signed certification, governed acceptance, change-control, retention, or external audit binding.

See `docs/gold/gold-boundary-v0.2.5.md` for the boundary list.

> v0.2.5 names the Gold boundary. It does not cross it.
