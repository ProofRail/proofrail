# Gold Demo 003 — Policy Evaluation Matrix (v0.4.2)

This demo is the deterministic, local Gold policy-evaluation-matrix package that ProofRail v0.4.2 derives from two hand-authored inputs:

- the canonical 5-scenario v0.4.0 fixture
  (`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`); and
- the canonical 5-row v0.4.2 matrix template
  (`fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json`).

It is a narrow Gold-tier maintenance release that hardens the v0.4.0 governed-reliance body with a v0.4.1-derived decision report and a v0.4.2-derived policy evaluation matrix and policy evaluation report. It does not introduce a new Gold tier, does not consult any live policy engine, does not add new Silver-shaped inputs, and does not extend the substance of the v0.4.0 package body or the v0.4.1 decision report. It re-projects the decision rows against a hand-authored matrix template, binds them under a 5-subject manifest, and adds nine v0.4.2-owned structural checks on top of the inherited v0.4.0 and v0.4.1 checks.

It answers a narrow question:

> Can a v0.4.0 Minimal Gold Governed Reliance Demo body and a v0.4.1 Gold decision report be paired with a hand-authored local policy evaluation matrix (one matrix row per recognized scenario in natural order) and re-projected into a deterministic local Gold policy evaluation report (a row-per-decision evaluation with a closed-vocabulary coverage summary), bound by a 5-subject manifest cross-anchored to the body, the conformance report, the decision report, the matrix template, and the evaluation report — such that an independent Gold reviewer can re-run the unchanged v0.4.2 verifier (which delegates the 29 inherited structural checks to the co-located v0.4.1 verifier via subprocess) and re-derive every check, without claiming that the package constitutes a certificate, a signed reliance instrument, a federated acceptance, a transfer of reliance to any external party, a regulator or auditor approval, legal acceptance or enforceability, production authorization, or full Gold?

It does **not** answer:

- Is the package a Gold certificate?
- Is the package signed?
- Has any external party accepted the recorded policy expectations?
- Has the matrix been federated?
- Has any regulator, auditor, or third party approved the recorded policy expectations?
- Have the recorded decisions been adjudicated legally?
- Has the upstream Silver evidence been re-verified end-to-end against any live service?
- Has any live policy engine evaluated the matrix?
- Is the demo production-authorized?
- Is the demo full Gold or Platinum?

## What the demo does

1. Validates the `--input-package` argv through the inherited Phase A preflight checks against the v0.4.0 canonical fixture. Phase A emits only the 5 approved runner-only refusal reasons.
2. Subprocesses the unchanged v0.4.1 runner to produce subjects [0], [1], and [2] in a tempdir; the v0.4.1 runner itself subprocesses the v0.4.0 runner to produce subjects [0] and [1].
3. Stages output under `<output-dir>.staging.<pid>` and byte-copies subjects [0], [1], and [2] under the staging directory.
4. Reads the hand-authored matrix template at `--matrix-input`, injects the two runtime-bound scalars (`decision_report_sha256` and `generated_at`), and writes the runtime matrix as subject [3].
5. Derives the v0.4.2 policy evaluation report (subject [4]) deterministically: one row per governed decision (closed projection of the matched matrix row's clause, effect, and rationale) plus a closed-vocabulary `coverage_summary` with row counts and a stable aggregate evaluation fingerprint.
6. Writes the 5-subject manifest cross-anchored by `package_id`, `governed_reliance_demo_id`, and the evaluation report's `source_decision_report_sha256` / `source_matrix_sha256` anchors.
7. With `--self-validate`, invokes the v0.4.2 verifier against the staging directory BEFORE the atomic `os.replace()`. On self-validation failure the staging directory is removed and the destination is left untouched; the runner relays the verifier's failure UNCHANGED with no sixth runner-only wrapper code.

## What runs at runtime

The runtime layout at `/tmp/proofrail-gold-policy-evaluation-matrix-v0.4.2/` holds exactly six files: the v0.4.0 package body, the v0.4.0 conformance report, the v0.4.1 decision report, the new v0.4.2 runtime matrix, the new v0.4.2 evaluation report, and the 5-subject manifest. The runtime directory is never staged into the repository.

## Run

```bash
make run-gold-policy-evaluation-matrix-v0-4-2
make verify-gold-policy-evaluation-matrix-v0-4-2
```

## Walkthrough

See `demo-walkthrough.md` for the step-by-step output of a clean run.

## Reference

See `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md` for the release narrative, the closed reason surface, reachability orderings, the TG1 allowlist discipline, and the non-claims.

## Non-claims

The v0.4.2 demo records a deterministic local hand-authored policy-evaluation projection over the v0.4.0 body and v0.4.1 decision report. It does not approve, audit, certify, federate, proof identity, evaluate against any live policy engine, adjudicate, issue, transfer, or accept reliance to any external party. It does not extend the substance of the v0.4.0 body or the v0.4.1 decision report. It is not signed; it ships local hash anchors only. It is not a Gold certificate, not full Gold, not Platinum, not a transfer of reliance, not regulator / auditor / legal approval, and not production authorization.
