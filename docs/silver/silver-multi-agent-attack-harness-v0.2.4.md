# ProofRail Silver v0.2.4 Multi-Agent Attack Harness

**Date:** 2026-06-21
**Status:** Draft / Demo-informed reference note
**Applies to:** ProofRail v0.2.4

---

## Purpose

ProofRail v0.2.4 adds a deterministic, scripted multi-agent attack harness that routes structured protected-action attempts through the unchanged v0.2.3 authority evaluator and produces local evidence of what happened.

The release answers a narrow question:

> Can scripted multi-principal agent interactions be evaluated through controlled protected-action paths, producing deterministic evidence that harmless instructions proceed while unauthorized, delegated, bypass, revoked, and out-of-scope protected actions are denied or blocked?

The release does **not** answer:

> Can arbitrary prompts be understood, can prompt injection be detected, can live agents be trusted, can a production deployment prevent all bypasses, or is this Gold governed acceptance?

The boundary sentence:

> Silver v0.2.4 makes scripted multi-agent protected-action attempts visible, authority-gated, and locally evidence-producing. It does not prove live agent safety or certify a deployment.

---

## What v0.2.4 Adds

| Artifact | Version | Role |
|---|---|---|
| Silver Multi-Agent Harness Script | v0.1.0 | Deterministic structured event script |
| Silver Multi-Agent Harness Run Report | v0.1.0 | Per-event execution result artifact |
| Silver Multi-Agent Harness Evidence Manifest | v0.1.0 | Local SHA-256 integrity manifest |
| Canonical harness script fixture | — | `fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml` |
| Harness runner | v0.1.0 | `tools/silver/run_multi_agent_attack_harness_v0_1_0.py` |
| Harness evidence verifier | v0.1.0 | `tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py` |
| Regression test | — | `tests/test_silver_multi_agent_attack_harness_v0_2_4.sh` |

The release does **not** add:

- a new Silver Relying-Party Profile version;
- changes to the v0.2.3 authority fixture, request, or decision report schemas;
- a new Silver Verification Report version;
- a new Verifier Output Attestation version;
- signed harness evidence;
- a packaged demo (planned for v0.2.5).

---

## Conceptual Model

```
harness_script.yaml ──┐
                       │
authority_fixture.yaml ┼─►  run_multi_agent_attack_harness_v0_1_0.py  ──► output_dir/
                       │           │                                       ├─ harness-script.yaml
                       │           │                                       ├─ authority-fixture.yaml
                       │           │  (import v0.2.3 evaluate_request)     ├─ expected-outcomes.json
                       │           ▼                                       ├─ transcript.jsonl
                       │   evaluate_multi_principal_authority_v0_1_0.py    ├─ protected-action-requests/
                       │                                                   ├─ authority-decision-reports/
                       │                                                   ├─ harness-run-report.json
                       │                                                   └─ harness-evidence-manifest.json
                       │
                       └──►  verify_multi_agent_harness_evidence_v0_1_0.py  ──► PASS / FAIL
```

The harness script is the **single source of truth** for both event ordering and expected outcomes. The runner derives `expected-outcomes.json` as a runtime artifact and hashes it in the evidence manifest.

---

## Event Vocabulary

| event_type | Evaluator called? | Decision report? | Stable outcome |
|---|---|---|---|
| `agent_message` | no | no | `message_delivered` |
| `protected_action_attempt` | yes | yes | `action_allowed` or `action_denied` |
| `bypass_attempt` | no | no | `bypass_blocked` (reason: `bypass_attempt_detected`) |
| `revocation_marker` | no | no | `revocation_marked` |

For `protected_action_attempt`:

- the runner renders `request_template` into a v0.1.0 Silver Protected Action Request JSON;
- the runner invokes the v0.2.3 evaluator with the event `timestamp` as `--decision-time`;
- the runner writes the decision report to `authority-decision-reports/<event_id>.json`;
- the runner asserts `execution.performed == false` in the decision report.

For `bypass_attempt`:

- the runner does **not** call the evaluator;
- the runner does **not** generate a request or decision report;
- the harness blocks the attempt at the harness level by recording `bypass_blocked` and `bypass_attempt_detected` in the transcript.

For `revocation_marker`:

- the runner does **not** mutate the fixture;
- the marker is recorded in the transcript;
- subsequent `protected_action_attempt` events with timestamps at or after a fixture-recorded `revoked_at` produce `deny` / `authority_revoked` via the unchanged v0.2.3 evaluator.

---

## Canonical Harness Script

The canonical script under `fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml` exercises:

1. Harmless agent-to-agent message (allowed without authority evaluation).
2. Allowed payment release through controlled path (within constraint).
3. Allowed vendor approval before revocation.
4. Delegation-laundering attempt (subject mismatch deny).
5. Bypass attempt (harness-level block).
6. Out-of-scope data export (constraint deny).
7. Out-of-scope deploy change (constraint deny).
8. Revocation marker at the fixture revocation timestamp.
9. Vendor approval after revocation (authority_revoked deny).

This covers the eight questions enumerated in the v0.2.4 design brief.

---

## Evidence Outputs

Per harness run, the runner writes a deterministic output directory containing:

```
<output-dir>/
  harness-script.yaml                    # copy of input script
  authority-fixture.yaml                 # copy of input fixture
  expected-outcomes.json                 # derived from script.events[*].expected
  transcript.jsonl                       # one JSON line per event
  protected-action-requests/<event_id>.json   # one per protected_action_attempt
  authority-decision-reports/<event_id>.json  # one per protected_action_attempt
  harness-run-report.json                # aggregate result
  harness-evidence-manifest.json         # SHA-256 manifest over all above
```

All paths inside `harness-evidence-manifest.json` are intra-output relative paths. The verifier rejects any subject path containing `..`.

---

## Limitations and Non-Claims

The v0.2.4 harness:

- does not execute any protected action;
- does not parse natural language;
- does not detect arbitrary prompt injection;
- does not evaluate live model behavior;
- does not invoke any production authorization system;
- does not produce signed certification evidence;
- does not constitute Gold governed acceptance;
- does not represent regulator approval, third-party certification, or production deployment assurance.

Every decision report retains `execution.performed == false`. Every run report retains `execution.protected_actions_performed == false`.

---

## Backward Compatibility

v0.2.4 does not modify:

- the v0.2.3 authority fixture, request, or decision report schemas;
- the v0.2.3 authority evaluator semantics;
- the v0.2.2 verifier output attestation schema;
- the v0.2.1 Silver Relying-Party Profile;
- the v0.1.0 Silver Verification Report;
- the Bronze claim or evidence bundle manifest schemas.

The harness runner imports the existing top-level `evaluate_request(fixture, request, decision_time)` function from `tools/silver/evaluate_multi_principal_authority_v0_1_0.py` without changing it.

---

## Roadmap Position

```
v0.2.3: define executable multi-principal authority/delegation fixtures
v0.2.4: deterministic multi-agent attack harness + local evidence (this release)
v0.2.5: packaged multi-agent trust-boundary demo + first Gold boundary
```

The packaged demo, signed harness evidence, and Gold boundary are explicitly **not** part of v0.2.4.
