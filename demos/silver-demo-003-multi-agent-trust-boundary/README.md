# ProofRail Silver Demo 003 — Multi-Agent Trust-Boundary Demo

**Release:** v0.2.5
**Status:** Local deterministic demo. **Not** a certification, production deployment, or governed acceptance.

---

## What This Demo Shows

This demo packages the ProofRail Silver v0.2.4 multi-agent attack harness into a small, inspectable demo. Running one Make target produces a package containing:

- documentation;
- a `demo-summary.json` mapping eight claims to concrete v0.2.4 harness evidence;
- a `demo-package-manifest.json` hashing the package's documentation and summary, and referencing the nested harness evidence manifest by hash.

The package is then independently verifiable by `tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py`, which:

1. Recomputes SHA-256 for every package subject.
2. Validates the demo summary structure and the eight required claim outcomes against the nested harness run report and decision reports.
3. Re-invokes the unchanged v0.2.4 verifier on the nested harness evidence manifest.

---

## What This Demo Does Not Show

- This demo does **not** prove that any live agent is safe.
- It does **not** detect prompt injection or evaluate LLM behavior.
- It does **not** invoke real protected actuators. Every decision report records `execution.performed == false`.
- It does **not** create Gold conformance, certification, or governed acceptance. See `docs/gold/gold-boundary-v0.2.5.md`.

---

## The Three-Principal Scenario

The unchanged v0.2.3 authority fixture defines:

- `buyerorg.agent` — scoped grants for `payment.release`, `vendor.approve`, and a delegated read-only `data.export` whose subject is the verifier;
- `vendororg.agent` — a staging-only `deploy.change` grant;
- `verifier.auditor` — a delegated read-only `data.export` grant scoped to audit datasets.

Four protected action identifiers are exercised, all simulated:

```text
payment.release
vendor.approve
data.export
deploy.change
```

The v0.2.4 harness drives nine deterministic events through the v0.2.3 authority evaluator. See `demo-walkthrough.md` for the event-by-event mapping.

---

## Local Demo Command

From the repository root:

```bash
make run-silver-multi-agent-demo-v0-2-5
```

This packages the demo into `/tmp/proofrail-silver-multi-agent-demo-v0.2.5/` and runs the v0.2.5 package verifier on the resulting package manifest.

To run only the regression test:

```bash
make verify-silver-multi-agent-demo-v0-2-5
```

To inspect outputs after `run-silver-multi-agent-demo-v0-2-5`:

```bash
ls /tmp/proofrail-silver-multi-agent-demo-v0.2.5/
cat /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-summary.json
cat /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json
```

---

## Where Evidence Appears

```text
/tmp/proofrail-silver-multi-agent-demo-v0.2.5/
  README.md                              <- this file, copied by the packager
  demo-walkthrough.md                    <- walkthrough, copied by the packager
  demo-summary.json                      <- packager-emitted claim → evidence map
  demo-package-manifest.json             <- packager-emitted hash manifest
  harness-evidence/
    harness-script.yaml                  <- v0.2.4 input copy
    authority-fixture.yaml               <- v0.2.3 input copy
    expected-outcomes.json               <- v0.2.4 derived
    transcript.jsonl                     <- v0.2.4 transcript
    protected-action-requests/*.json     <- v0.2.4 per-event request
    authority-decision-reports/*.json    <- v0.2.4 per-event decision report
    harness-run-report.json              <- v0.2.4 run summary
    harness-evidence-manifest.json       <- v0.2.4 hash manifest
```

The committed demo directory contains only this README and the walkthrough. All runtime output is written under `/tmp` and is not committed.

---

## Why This Remains Silver

- Evidence is local hash-based integrity only.
- No signed assertion is required.
- No verifier-output attestation is mandated.
- There is no governed acceptance, change-control, retention, or external audit binding.

See `docs/gold/gold-boundary-v0.2.5.md` for what a future Gold layer would need to add.

---

## Non-Claims

```
ProofRail v0.2.5 packages a deterministic local Silver demo. It does not certify live agents, production deployments, or governed institutional acceptance.

v0.2.5 names the Gold boundary. It does not cross it.
```
