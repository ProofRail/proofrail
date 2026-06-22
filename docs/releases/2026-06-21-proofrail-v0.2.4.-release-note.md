# ProofRail v0.2.4 - Silver Multi-Agent Attack Harness Evidence

Release date: 2026-06-21

Git tag: `v0.2.4`

ProofRail v0.2.4 adds a deterministic Silver multi-agent attack harness and evidence verifier.

Earlier v0.2.x releases tightened Silver relying-party acceptance, made verifier outputs attestable, and added executable multi-principal authority fixtures. v0.2.4 uses that authority layer to run a scripted multi-agent trust-boundary scenario and produce local evidence that can be independently checked.

The narrow claim is:

> In a multi-principal agent environment, protected actions must flow through scoped authority checks and produce verifiable evidence. Trust does not attach to the agent itself.

## What Changed

This release adds a scripted multi-agent attack harness for the Silver line.

The harness models three principal roles:

- `buyerorg.agent`
- `vendororg.agent`
- `verifier.auditor`

It exercises the protected actions introduced in v0.2.3:

- `payment.release`
- `vendor.approve`
- `data.export`
- `deploy.change`

The harness runs deterministic events for:

- harmless agent-to-agent messages;
- authorized protected action attempts;
- unauthorized delegated action attempts;
- out-of-scope action attempts;
- bypass attempts that try to avoid ProofRail-controlled paths;
- a revocation marker followed by a revoked-authority denial.

The harness does not execute protected actions. It produces evidence about whether the action would be allowed or denied.

## New Artifacts

Added schemas:

- `schemas/silver-multi-agent-harness-script-v0.1.0.md`
- `schemas/silver-multi-agent-harness-run-report-v0.1.0.md`
- `schemas/silver-multi-agent-harness-evidence-manifest-v0.1.0.md`

Added documentation:

- `docs/silver/silver-multi-agent-attack-harness-v0.2.4.md`
- `fixtures/silver-multi-agent-attack-harness-v0.2.4/README.md`

Added fixture:

- `fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml`

Added tools:

- `tools/silver/run_multi_agent_attack_harness_v0_1_0.py`
- `tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py`

Added test:

- `tests/test_silver_multi_agent_attack_harness_v0_2_4.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`

## Harness Runner

The harness runner consumes:

- the v0.2.4 harness script;
- the v0.2.3 multi-principal authority fixture.

Example:

```bash
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
  --script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --output-dir /tmp/proofrail-silver-multi-agent-harness-v0.2.4 \
  --force
```

The runner emits:

- copied immutable inputs in the output directory;
- `expected-outcomes.json`, derived from the script's `expected` blocks;
- `transcript.jsonl`;
- protected action request files;
- authority decision report files;
- `harness-run-report.json`;
- `harness-evidence-manifest.json`.

The harness script is the single source of truth for expected outcomes. The generated `expected-outcomes.json` is a derived runtime evidence artifact, not a separate committed oracle.

## Bypass Handling

Bypass attempts are handled at the harness layer.

For a bypass event, the runner:

- does not call the authority evaluator;
- does not create a protected action request file;
- does not create an authority decision report;
- records `bypass_blocked` with reason `bypass_attempt_detected`.

This keeps the distinction clear: bypass attempts are not denied by normal authority evaluation. They are blocked because they attempted to avoid the controlled action path.

## Evidence Verifier

The harness evidence verifier checks the local harness evidence manifest.

Example:

```bash
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py \
  --manifest /tmp/proofrail-silver-multi-agent-harness-v0.2.4/harness-evidence-manifest.json
```

The verifier checks:

- manifest structure and version;
- stable subject ordering;
- that subject paths are relative to the harness output directory;
- that subject paths do not contain `..` and are not absolute;
- SHA-256 hashes for every subject;
- harness run status;
- that no protected actions were performed;
- that every authority decision report states `execution.performed == false`.

Stable verifier failures include:

- `invalid_evidence_manifest`
- `subject_file_missing`
- `subject_path_traversal`
- `subject_hash_mismatch`
- `harness_run_failed`
- `execution_violation`
- `decision_report_invalid`

## Regression Coverage

The v0.2.4 regression test covers:

- v0.2.3 authority fixture validation;
- v0.2.3 authority regression compatibility;
- harness execution into a temporary output directory;
- untampered evidence manifest verification;
- transcript event count;
- all per-event expected outcomes;
- decision report non-execution;
- harness run report non-execution;
- decision report tamper detection;
- transcript tamper detection;
- missing subject detection;
- `..` subject path traversal rejection;
- absolute subject path rejection;
- malformed harness script rejection;
- confirmation that committed harness and authority fixture paths are not modified by a harness run.

Primary commands:

```bash
make verify-silver-multi-agent-harness-v0-2-4
make verify-silver-all
git diff --check
```

The implementation run reported these passing.

## Why This Matters

v0.2.4 is the first ProofRail release that turns the planned multi-agent trust-boundary claim into a deterministic evidence-producing scenario.

The important behavior is not agent intelligence. The important behavior is boundary enforcement:

> Harmless messages can proceed, but protected actions require scoped authority, controlled action paths, and independently checkable evidence.

This release shows that:

- harmless agent messages are recorded without authority evaluation;
- authorized protected actions are allowed by scoped authority;
- unauthorized delegated instructions fail;
- out-of-scope actions fail;
- bypass attempts are blocked before authority evaluation;
- revoked authority fails after the revocation point;
- generated evidence can be checked for tampering and path manipulation.

## What This Release Does Not Claim

ProofRail v0.2.4 does not claim:

- a live multi-agent runtime;
- autonomous agent behavior;
- natural-language prompt injection detection;
- LLM behavior evaluation;
- real actuator integration;
- payment, deployment, export, or vendor-system execution;
- production authorization infrastructure;
- production PKI;
- Gold certification;
- third-party certification;
- regulator approval;
- production deployment assurance.

The correct boundary is:

> Silver v0.2.4 demonstrates deterministic local evidence for a multi-agent trust-boundary scenario. It does not certify live agents or a production environment.

## What Comes Next

v0.2.4 provides the attack harness and evidence layer.

Next:

- v0.2.5 should package the small multi-agent trust-boundary demo end to end;
- v0.2.5 should make the demo easier to run, explain, inspect, and verify;
- v0.2.5 should define the first explicit Gold boundary without claiming Gold certification.

The intended progression is:

```text
v0.2.3:
  executable multi-principal authority fixtures

v0.2.4:
  deterministic attack harness and evidence production

v0.2.5:
  packaged multi-agent trust-boundary demo and first Gold boundary
```

## Summary

ProofRail v0.2.4 shows a small but credible multi-agent trust-boundary scenario in deterministic Silver form.

It does not ask whether an agent is trustworthy. It asks whether protected actions flow through scoped authority, controlled paths, and verifiable evidence.
