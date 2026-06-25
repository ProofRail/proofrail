# Gold Demo 002 — Decision Report Hardening (v0.4.1)

This demo is the deterministic, local Gold decision-report hardening package that ProofRail v0.4.1 derives from a single hand-authored input:

- the canonical 5-scenario v0.4.0 fixture
  (`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`).

It is a narrow Gold-tier maintenance release that hardens the v0.4.0 *decision report* surface. It does not introduce a new Gold tier, does not add new Silver-shaped inputs, and does not extend the substance of the v0.4.0 package body. It re-projects the body's governed decisions into a structured decision report, binds it alongside the v0.4.0 package body and v0.4.0 conformance report under a 3-subject manifest, and adds five v0.4.1-owned structural checks on top of the 24 inherited v0.4.0 checks.

It answers a narrow question:

> Can a v0.4.0 Minimal Gold Governed Reliance Demo body be re-projected into a deterministic local Gold decision report (a structural row-per-decision projection plus a closed-vocabulary coverage summary), paired with the v0.4.0 conformance report, and bound by a 3-subject manifest cross-anchored to the body and to the conformance report under five additional v0.4.1-owned structural checks — such that an independent Gold reviewer can re-run the unchanged v0.4.1 verifier (which delegates the 24 inherited structural checks to the co-located v0.4.0 verifier via subprocess) and re-derive every check, without claiming that the package constitutes a certificate, a signed reliance instrument, a federated acceptance, a transfer of reliance to any external party, a regulator or auditor approval, legal acceptance or enforceability, production authorization, or full Gold?

It does **not** answer:

- Is the package a Gold certificate?
- Is the package signed?
- Has any external party accepted the recorded decision report?
- Has the decision report been federated?
- Has any regulator, auditor, or third party approved the recorded decisions?
- Have the recorded decisions been adjudicated legally?
- Has the upstream Silver evidence been re-verified end-to-end against any live service?
- Is the demo production-authorized?
- Is the demo full Gold or Platinum?

## What the demo does

1. Validates the `--input-package` argv through 5 Phase A preflight checks against the v0.4.0 canonical fixture. Phase A emits only the 5 approved runner-only refusal reasons.
2. Subprocesses the unchanged v0.4.0 runner to produce subjects [0] and [1] in a tempdir.
3. Stages output under `<output-dir>.staging.<pid>` and byte-copies subjects [0] and [1] under the staging directory.
4. Derives the v0.4.1 decision report (subject [2]) deterministically: one row per governed decision (closed projection of `decision_id`, `scenario_type`, `decision_status`, `policy_decision`, `decision_authority_role`, `protected_action_id`, `action_category`, `action_environment`) plus a closed-vocabulary `coverage_summary` whose `total_decisions`, `unique_*` counts, and enum-presence indicators are computed from the decisions list.
5. Writes the 3-subject manifest cross-anchored by `package_id`, `governed_reliance_demo_id`, and the decision report's `source_package_sha256` / `source_conformance_report_sha256` anchors.
6. With `--self-validate`, invokes the v0.4.1 verifier against the staging directory BEFORE the atomic `os.replace()`. On self-validation failure the staging directory is removed and the destination is left untouched; the runner relays the verifier's failure UNCHANGED with no sixth runner-only wrapper code.

## What runs at runtime

The runtime layout at `/tmp/proofrail-gold-decision-report-hardening-v0.4.1/` holds exactly four files: the v0.4.0 package body, the v0.4.0 conformance report, the new v0.4.1 decision report, and the 3-subject manifest. The runtime directory is never staged into the repository.

## Run

```bash
make run-gold-decision-report-hardening-v0-4-1
make verify-gold-decision-report-hardening-v0-4-1
```

## Walkthrough

See `demo-walkthrough.md` for the step-by-step output of a clean run.

## Reference

See `docs/gold/gold-decision-report-hardening-v0.4.1.md` for the release narrative, the closed reason surface, reachability orderings, the TG1 allowlist discipline, and the non-claims.

## Non-claims

The v0.4.1 demo records a deterministic local hand-authored decision-report projection of the v0.4.0 body. It does not approve, audit, certify, federate, proof identity, evaluate, adjudicate, issue, transfer, or accept reliance to any external party. It does not extend the substance of the v0.4.0 body. It is not signed; it ships local hash anchors only. It is not a Gold certificate, not full Gold, not Platinum, not a transfer of reliance, not regulator / auditor / legal approval, and not production authorization.
