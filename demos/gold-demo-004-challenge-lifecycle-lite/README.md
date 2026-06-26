# Gold Demo 004 — Challenge Lifecycle Lite (v0.4.3)

This demo is the deterministic, local Gold challenge-lifecycle-lite package that ProofRail v0.4.3 derives from three hand-authored inputs:

- the canonical 5-scenario v0.4.0 fixture
  (`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`);
- the canonical 5-row v0.4.2 matrix template
  (`fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json`); and
- the canonical 5-record v0.4.3 lifecycle records template
  (`fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json`).

It is a narrow Gold-tier maintenance release that hardens the v0.4.0 governed-reliance body with a v0.4.1-derived decision report, a v0.4.2-derived policy evaluation matrix and policy evaluation report, and a v0.4.3-derived runtime lifecycle records body and lifecycle report. It does not introduce a new Gold tier, does not consult any live policy engine, does not consult any live lifecycle adjudication authority, does not add new Silver-shaped inputs, and does not extend the substance of the v0.4.0 package body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair. It re-projects the lifecycle records against a hand-authored records template, binds them under a 7-subject manifest, and adds ten v0.4.3-owned structural checks on top of the inherited v0.4.0, v0.4.1, and v0.4.2 checks.

It answers a narrow question:

> Can a v0.4.0 Minimal Gold Governed Reliance Demo body, a v0.4.1 Gold decision report, and a v0.4.2 policy evaluation matrix and policy evaluation report be paired with a hand-authored local runtime challenge-lifecycle records body (one lifecycle record per governed decision row in natural order, with a closed-vocabulary event chain) and re-projected into a deterministic local Gold lifecycle report (a row-per-record projection with a closed-vocabulary coverage summary keyed on the six lifecycle status values), bound by a 7-subject manifest cross-anchored to the body, the conformance report, the decision report, the matrix, the evaluation report, the records body, and the lifecycle report — such that an independent Gold reviewer can re-run the unchanged v0.4.3 verifier (which delegates the 38 inherited structural checks to the co-located v0.4.2 verifier via subprocess) and re-derive every check, without claiming that the package constitutes a certificate, a signed reliance instrument, a federated acceptance, a transfer of reliance to any external party, a regulator or auditor approval, legal acceptance or enforceability, production authorization, signed lifecycle attestation, live lifecycle adjudication, or full Gold?

It does **not** answer:

- Is the package a Gold certificate?
- Is the package signed?
- Has any external party accepted the recorded lifecycle decisions?
- Have the lifecycle records been federated?
- Has any regulator, auditor, or third party approved the recorded lifecycle state?
- Have any challenge lifecycles been adjudicated by any live external authority?
- Has the upstream Silver evidence been re-verified end-to-end against any live service?
- Has any live policy engine evaluated the matrix?
- Is the demo production-authorized?
- Is the demo full Gold or Platinum?

## What the demo does

1. Validates `--input-package`, `--matrix-input`, and `--lifecycle-input` argvs through the Phase A preflight against the v0.4.0 canonical fixture, the v0.4.2 matrix template, and the v0.4.3 records template. Phase A emits only the 5 approved runner-only refusal reasons.
2. Subprocesses the unchanged v0.4.2 runner to produce subjects [0]..[4] in a tempdir; the v0.4.2 runner itself subprocesses the v0.4.1 and v0.4.0 runners.
3. Stages output under `<output-dir>.staging.<pid>` and byte-copies subjects [0]..[4] under the staging directory.
4. Reads the hand-authored records template at `--lifecycle-input`, injects the three runtime-bound scalars (top-level `policy_evaluation_report_sha256`, top-level `generated_at`, and per-record `lifecycle_fingerprint`), and writes the runtime records body as subject [5].
5. Derives the v0.4.3 lifecycle report (subject [6]) deterministically: one row per lifecycle record (closed projection of the record's `current_status`, terminal flag, event count, and terminal-ref shape) plus a closed-vocabulary `coverage_summary` with `record_count`, `terminal_record_count`, `open_record_count`, `status_value_count` (closed 6-key map), `event_count`, and a stable `aggregate_lifecycle_fingerprint`.
6. Writes the 7-subject manifest cross-anchored by `package_id`, `governed_reliance_demo_id`, and the lifecycle report's `source_records_sha256` / `source_policy_evaluation_report_sha256` anchors.
7. With `--self-validate`, invokes the v0.4.3 verifier against the staging directory BEFORE the atomic `os.replace()`. On self-validation failure the staging directory is removed and the destination is left untouched; the runner relays the verifier's failure UNCHANGED with no sixth runner-only wrapper code.

## What runs at runtime

The runtime layout at `/tmp/proofrail-gold-challenge-lifecycle-lite-v0.4.3/` holds exactly eight files: the v0.4.0 package body, the v0.4.0 conformance report, the v0.4.1 decision report, the v0.4.2 runtime matrix, the v0.4.2 evaluation report, the new v0.4.3 runtime records body, the new v0.4.3 lifecycle report, and the 7-subject manifest. The runtime directory is never staged into the repository.

## Run

```bash
make run-gold-challenge-lifecycle-lite-v0-4-3
make verify-gold-challenge-lifecycle-lite-v0-4-3
```

## Walkthrough

See `demo-walkthrough.md` for the step-by-step output of a clean run.

## Reference

See `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md` for the release narrative, the closed reason surface, reachability orderings, the TG1 allowlist discipline, the closed lifecycle vocabularies, and the non-claims.

## Non-claims

The v0.4.3 demo records a deterministic local hand-authored challenge-lifecycle projection over the v0.4.0 body, v0.4.1 decision report, and v0.4.2 policy-evaluation pair. It does not approve, audit, certify, federate, proof identity, evaluate against any live policy engine, adjudicate any challenge lifecycle against any live external authority, issue, transfer, or accept reliance to any external party. It does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair. It is not signed; it ships local hash anchors only. It is not a Gold certificate, not full Gold, not Platinum, not a transfer of reliance, not a signed lifecycle attestation, not regulator / auditor / legal approval, and not production authorization. The v0.4.3 release is unreleased at the time of demo authoring; the most recently released Gold tier is v0.4.2.
