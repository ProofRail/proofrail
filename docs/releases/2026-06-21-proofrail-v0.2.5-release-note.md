# ProofRail v0.2.5 - Silver Multi-Agent Trust-Boundary Demo Package

Release date: 2026-06-21

Git tag: `v0.2.5`

ProofRail v0.2.5 packages the Silver multi-agent trust-boundary scenario into a runnable local demo.

Earlier v0.2.x releases tightened Silver relying-party acceptance, made verifier outputs attestable, added multi-principal authority fixtures, and introduced a deterministic multi-agent attack harness. v0.2.5 packages that harness into a small demo that can be run, inspected, and verified end to end.

The narrow claim is:

> In a multi-principal agent environment, trust does not attach to the agent. Trust attaches to scoped authority, controlled action paths, and independently verifiable evidence.

## What Changed

This release adds a Silver demo package layer over the v0.2.4 multi-agent attack harness.

The packaged demo shows:

- harmless agent-to-agent messages proceeding;
- protected actions requiring scoped authority;
- unauthorized delegated instructions failing;
- bypass attempts being blocked;
- revoked authority failing after the revocation point;
- out-of-scope action attempts failing;
- package-level and nested harness evidence being hash-verifiable;
- no protected actions being executed.

The demo remains deterministic and local. It does not run live agents, call LLMs, parse arbitrary natural language, or execute real actuators.

## New Artifacts

Added schemas:

- `schemas/silver-multi-agent-demo-package-manifest-v0.1.0.md`
- `schemas/silver-multi-agent-demo-summary-v0.1.0.md`

Added documentation:

- `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md`
- `docs/gold/gold-boundary-v0.2.5.md`
- `demos/silver-demo-003-multi-agent-trust-boundary/README.md`
- `demos/silver-demo-003-multi-agent-trust-boundary/demo-walkthrough.md`

Added tools:

- `tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py`
- `tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py`

Added test:

- `tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`

## Demo Packager

The demo packager runs the v0.2.4 harness, verifies the nested harness evidence, and assembles a package-level demo output.

Example:

```bash
python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py \
  --demo-root demos/silver-demo-003-multi-agent-trust-boundary \
  --harness-script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --output-dir /tmp/proofrail-silver-multi-agent-demo-v0.2.5 \
  --force
```

The package output includes:

- `README.md`
- `demo-walkthrough.md`
- `demo-summary.json`
- `demo-package-manifest.json`
- `harness-evidence/`

The nested `harness-evidence/` directory is produced by the v0.2.4 harness. The package manifest hashes package-level artifacts and references the nested harness evidence manifest rather than duplicating every nested subject.

## Demo Summary

The generated `demo-summary.json` maps the demo's trust-boundary claims to concrete evidence.

Required claim IDs:

- `harmless_messages_proceed`
- `protected_actions_require_scoped_authority`
- `unauthorized_delegation_fails`
- `bypass_attempts_blocked`
- `revoked_authority_fails`
- `out_of_scope_actions_fail`
- `evidence_is_hash_verifiable`
- `no_protected_actions_executed`

Each claim must have `status: "pass"` and package-local evidence references. The verifier cross-checks those claims against nested harness artifacts, including the harness run report, transcript, and authority decision reports.

## Demo Verifier

The demo verifier checks both the package-level evidence and the nested harness evidence.

Example:

```bash
python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \
  --package-manifest /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json
```

The verifier checks:

- package manifest structure and version;
- package subject path safety;
- package subject existence;
- package subject SHA-256 hashes;
- demo summary structure;
- all required demo claims;
- claim evidence references;
- claim consistency against nested harness evidence;
- `execution.protected_actions_performed == false`;
- nested v0.2.4 harness evidence verification.

Stable verifier failures include:

- `invalid_demo_package_manifest`
- `demo_subject_file_missing`
- `demo_subject_path_traversal`
- `demo_subject_hash_mismatch`
- `invalid_demo_summary`
- `demo_claim_missing`
- `demo_claim_failed`
- `demo_evidence_ref_invalid`
- `demo_execution_violation`
- `nested_harness_evidence_invalid`

Nested verifier failures are surfaced under the stable package-level reason `nested_harness_evidence_invalid`, with nested context preserved as detail.

## Gold Boundary

v0.2.5 adds the first explicit ProofRail Gold boundary document:

- `docs/gold/gold-boundary-v0.2.5.md`

This is documentation only. It identifies what a future Gold layer would need to add, such as governed acceptance criteria, relying-party operating policy, independent accountability, evidence retention expectations, change control, revocation and dispute handling, runtime substrate evidence, and acceptance/rejection records.

The key boundary is:

> v0.2.5 names the Gold boundary. It does not cross it.

This release does not add Gold schemas, Gold validators, Gold certificates, certification workflows, regulator approval, or governed institutional acceptance.

## Regression Coverage

The v0.2.5 regression test covers:

- package generation;
- nested v0.2.4 harness evidence verification;
- untampered package verification;
- all eight required claim IDs;
- non-execution at the demo summary level;
- package manifest hash verification;
- demo summary tamper detection;
- missing package subject detection;
- `..` package subject path rejection;
- absolute package subject path rejection;
- nested harness evidence tamper detection;
- malformed demo summary handling without Python tracebacks;
- missing required claim detection;
- failed required claim detection;
- invalid evidence ref path detection;
- wrong-but-valid evidence ref detection;
- confirmation that committed v0.2.5 demo source files are not modified by runtime execution.

Primary commands:

```bash
make run-silver-multi-agent-demo-v0-2-5
make verify-silver-multi-agent-demo-v0-2-5
make verify-silver-all
git diff --check
```

The implementation run reported `verify-silver-all` passing, including the new v0.2.5 demo target. The v0.2.5 regression test reported `17/17 PASS`.

## Why This Matters

v0.2.5 makes the multi-agent trust-boundary scenario easier to run and verify.

The important behavior is not agent intelligence. The important behavior is that protected actions are routed through scoped authority decisions, bypass attempts are not treated as normal authority denials, revocation is honored, and the resulting evidence can be checked independently.

This release packages the demo so a relying party can inspect:

- the scenario walkthrough;
- the generated demo summary;
- the package manifest;
- the nested harness transcript;
- protected action requests;
- authority decision reports;
- the nested harness evidence manifest.

## What This Release Does Not Claim

ProofRail v0.2.5 does not claim:

- live multi-agent safety;
- autonomous agent behavior;
- prompt-injection detection;
- LLM behavior evaluation;
- production enforcement;
- real actuator integration;
- payment, deployment, export, or vendor-system execution;
- production authorization infrastructure;
- production PKI;
- Gold conformance;
- Gold certification;
- third-party certification;
- regulator approval;
- governed institutional acceptance;
- production deployment assurance.

The correct boundary is:

> ProofRail v0.2.5 packages a deterministic local Silver demo. It does not certify live agents, production deployments, or governed institutional acceptance.

## What Comes Next

v0.2.5 completes the Silver multi-agent trust-boundary demo package.

Next work should not simply add a larger agent ecosystem. The next useful step is to decide which boundary to strengthen:

- make the Silver demo handoff cleaner and easier to inspect;
- add signed package-level evidence using the existing verifier-output attestation direction;
- formalize relying-party operating expectations;
- select a substrate for a later Demo 002-style live environment;
- begin Gold design only where governed acceptance can be specified without overclaiming.

The intended progression is:

```text
v0.2.3:
  executable multi-principal authority fixtures

v0.2.4:
  deterministic attack harness and evidence production

v0.2.5:
  packaged multi-agent trust-boundary demo and first Gold boundary

later:
  stronger Silver operating profile or explicitly governed Gold layer
```

## Summary

ProofRail v0.2.5 packages the deterministic Silver multi-agent trust-boundary demo and verifies its package evidence.

It does not ask whether an agent is trustworthy. It asks whether protected actions flow through scoped authority, controlled paths, and independently verifiable evidence.
