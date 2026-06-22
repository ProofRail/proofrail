# ProofRail Silver Multi-Agent Trust-Boundary Demo v0.2.5

**Version:** v0.2.5
**Date:** 2026-06-21
**Status:** Demo + boundary documentation
**Applies to:** ProofRail Silver, multi-agent trust-boundary scenario

---

## 1. What v0.2.5 Packages

v0.2.4 added a deterministic multi-agent attack harness and harness evidence verifier. v0.2.5 packages that harness into a small, credible, inspectable demo that can be run, verified, and explained end to end.

The release thesis is narrow:

> ProofRail v0.2.5 packages the Silver multi-agent trust-boundary scenario into a runnable local demo: harmless messages proceed, protected actions require scoped authority, unauthorized delegation and bypass attempts fail, revocation is honored, and evidence can be independently verified.

The release does **not** claim:

- live multi-agent safety;
- prompt-injection detection;
- LLM behavior evaluation;
- production enforcement;
- production authorization;
- certification;
- regulator approval;
- Gold conformance;
- governed institutional acceptance.

---

## 2. Scope

v0.2.5 ships:

- two new schemas (`silver-multi-agent-demo-package-manifest-v0.1.0`, `silver-multi-agent-demo-summary-v0.1.0`);
- a demo packager (`tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py`) that invokes the unchanged v0.2.4 harness runner and verifier;
- a demo verifier (`tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py`) that re-checks the package and delegates nested evidence verification to the v0.2.4 verifier;
- the demo directory `demos/silver-demo-003-multi-agent-trust-boundary/` with a README and walkthrough;
- a 17-step regression test;
- a Gold boundary document (`docs/gold/gold-boundary-v0.2.5.md`) describing what Silver still does not provide.

v0.2.5 does **not** ship:

- new authority semantics beyond v0.2.3;
- new harness semantics beyond v0.2.4;
- new signed evidence or verifier-output attestation logic;
- a Silver relying-party profile version bump;
- any Gold schema, validator, certificate, or badge.

---

## 3. Scenario

Three principals are defined by the unchanged v0.2.3 authority fixture:

- `buyerorg.agent` — holds scoped grants for `payment.release` and `vendor.approve`, and a delegated read-only `data.export` grant whose subject is the verifier;
- `vendororg.agent` — holds a staging-only `deploy.change` grant;
- `verifier.auditor` — holds a delegated read-only `data.export` grant scoped to audit datasets.

Four protected action identifiers are exercised (all simulated, never executed):

```text
payment.release
vendor.approve
data.export
deploy.change
```

The v0.2.4 harness script issues nine deterministic events covering:

1. a harmless agent-to-agent message;
2. an allowed payment release;
3. an allowed vendor approval;
4. an attempted delegation laundering (denied);
5. a bypass attempt (blocked);
6. an out-of-scope export attempt (denied);
7. an out-of-scope production deploy attempt (denied);
8. a revocation marker;
9. a post-revocation vendor approval retry (denied with `authority_revoked`).

Every protected-action decision report continues to record `execution.performed == false`. The harness never invokes a real actuator and the demo never executes anything.

---

## 4. The Eight Demo Claims

The packager derives eight claim outcomes directly from the v0.2.4 harness run report and transcript. No second hand-written expected-results source is maintained.

| Claim ID | Plain reading | Evidence source |
|---|---|---|
| `harmless_messages_proceed` | Harmless agent-to-agent messages do not invoke protected actions. | Transcript `agent_message` events. |
| `protected_actions_require_scoped_authority` | Protected actions reach `allow` only when a scoped grant matches. | Decision reports with `decision.status == "allow"`. |
| `unauthorized_delegation_fails` | A grant whose subject is principal A cannot be wielded by principal B. | Decision report with `decision.reason == "authority_subject_mismatch"`. |
| `bypass_attempts_blocked` | Calls outside the controlled path are not silently allowed. | Transcript `bypass_attempt` events with `harness_outcome == "bypass_blocked"`. |
| `revoked_authority_fails` | After a revocation point, the formerly-valid grant no longer satisfies authority. | Revocation marker event plus a later decision report with `decision.reason == "authority_revoked"`. |
| `out_of_scope_actions_fail` | An action outside the grant's declared scope is denied. | Decision report with `decision.reason == "constraint_not_satisfied"`. |
| `evidence_is_hash_verifiable` | The nested harness evidence manifest passes the v0.2.4 verifier. | `nested_verification.harness_evidence_verified == true` and a fresh v0.2.4 verifier invocation. |
| `no_protected_actions_executed` | The demo never executes a protected action. | Nested run report and every decision report record `execution.performed == false` (or `execution.protected_actions_performed == false`). |

Each claim entry in `demo-summary.json` has `status: "pass"`, package-local evidence references, and at least one reference to a concrete transcript event or decision report.

---

## 5. Local Run Command

```bash
make run-silver-multi-agent-demo-v0-2-5
```

This:

1. Removes any pre-existing output under `/tmp/proofrail-silver-multi-agent-demo-v0.2.5`.
2. Invokes `tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py` against the v0.2.4 harness script and v0.2.3 authority fixture.
3. The packager runs the unchanged v0.2.4 harness runner into `<output>/harness-evidence/`, then invokes the unchanged v0.2.4 verifier on the nested manifest.
4. The packager copies the demo README and walkthrough into the output directory, emits `demo-summary.json`, and emits `demo-package-manifest.json`.
5. The Make target then runs the v0.2.5 package verifier on the resulting package manifest.

Output layout:

```text
/tmp/proofrail-silver-multi-agent-demo-v0.2.5/
  README.md
  demo-walkthrough.md
  demo-summary.json
  demo-package-manifest.json
  harness-evidence/
    harness-script.yaml
    authority-fixture.yaml
    expected-outcomes.json
    transcript.jsonl
    protected-action-requests/EVT-002-...json
    authority-decision-reports/EVT-002-...json
    ...
    harness-run-report.json
    harness-evidence-manifest.json
```

---

## 6. Local Verify Command

```bash
make verify-silver-multi-agent-demo-v0-2-5
```

This runs the 17-step regression test `tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh`, which covers:

- a clean package generation and verification;
- demo summary structure and execution invariant;
- package manifest subject hashes;
- tamper detection on the demo summary, missing subjects, traversal and absolute paths;
- nested harness evidence tamper detection surfaced as `nested_harness_evidence_invalid`;
- malformed demo summary handling (no Python traceback);
- missing required claim, failed required claim, and wrong-but-valid evidence reference;
- evidence references containing `..` or absolute paths;
- a scoped check that the runtime did not modify committed v0.2.5 demo files.

A standalone verifier invocation:

```bash
python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \
  --package-manifest /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json
```

---

## 7. Stable Failure Reasons

| Reason | When emitted |
|---|---|
| `invalid_demo_package_manifest` | Package manifest is malformed, has wrong type/version, missing required fields, or malformed `nested_verification`. |
| `demo_subject_path_traversal` | A package subject path contains `..` or is absolute. |
| `demo_subject_file_missing` | A package subject's file is absent. |
| `demo_subject_hash_mismatch` | A package subject's recomputed SHA-256 does not match the manifest. |
| `invalid_demo_summary` | `demo-summary.json` is malformed JSON (caught and surfaced cleanly) or structurally invalid. |
| `demo_claim_missing` | A required claim ID is absent from the demo summary. |
| `demo_claim_failed` | A required claim has `status != "pass"` or its derivation rule fails against nested evidence. |
| `demo_evidence_ref_invalid` | A claim's evidence reference is malformed, contains `..` or absolute path, or points to a wrong event / file for that claim. |
| `demo_execution_violation` | The demo summary or nested run report records `protected_actions_performed: true`. |
| `nested_harness_evidence_invalid` | The v0.2.4 nested verifier exits non-zero. This is the top-level stable reason even when the nested reason is `subject_hash_mismatch`, `subject_path_traversal`, etc. |

The package verifier never raises Python tracebacks to stdout/stderr for parseable-but-malformed inputs. Such errors are caught and surfaced as the corresponding stable reason.

---

## 8. What Remains Silver, Not Gold

v0.2.5 is still Silver because:

- evidence is local hash-based integrity only;
- no signed assertion is required to run the demo;
- no Verifier Output Attestation is mandated;
- there is no governed acceptance, change-control, retention, or external audit binding;
- there is no relying-party identity registry, dispute process, or revocation infrastructure beyond the unchanged v0.2.3 authority revocation.

See `docs/gold/gold-boundary-v0.2.5.md` for what a future Gold layer would need to add.

The Silver Relying-Party Profile v0.2.1 is unchanged. No new Silver profile version is shipped in v0.2.5.

---

## 9. Non-Claims

```
v0.2.5 packages a deterministic local Silver demo. It does not certify live agents, production deployments, or governed institutional acceptance.
v0.2.5 names the Gold boundary. It does not cross it.
```

---

## 10. Changelog

- **v0.2.5 (2026-06-21):** Multi-agent trust-boundary demo package, package verifier, demo directory, and Gold boundary document.
