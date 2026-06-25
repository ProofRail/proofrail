# ProofRail v0.4.1 — Gold Decision Report Hardening

ProofRail v0.4.1 is a narrow Gold maintenance release.

v0.4.0 introduced the first Minimal Gold boundary: a deterministic local governed-reliance package that records 1..5 relying-party decisions over Silver-shaped inputs. v0.4.1 leaves the v0.4.0 package body unchanged and re-projects it into a deterministic local Gold decision report, paired with the unchanged v0.4.0 conformance report and bound by a 3-subject manifest cross-anchored to the v0.4.0 body.

This release is intentionally narrow. It does not introduce a new Gold tier. It does not add new Silver-shaped inputs. It does not extend the substance of the v0.4.0 body. It is not signed. It is not a certificate. It is not federated. It is not a transfer of reliance to any external party.

## What v0.4.1 Adds

v0.4.1 adds a deterministic local Gold decision report whose canonical byte image is derived only from the v0.4.0 governed-reliance package body. The decision report projects each governed decision into one row and re-derives a closed `coverage_summary` over five data fields:

- `decision_statuses_present`;
- `policy_decisions_present`;
- `protected_actions_present`;
- `registry_roles_present`;
- `scenario_types_present`.

The v0.4.1 package layout is:

- subject [0] — the unchanged v0.4.0 governed-reliance package body;
- subject [1] — the unchanged v0.4.0 conformance report;
- subject [2] — the v0.4.1 Gold decision report.

A 3-subject manifest cross-anchors all three by SHA-256, by the v0.4.0 `package_id` and `governed_reliance_demo_id`, and by distinct v0.4.1-owned `conformance_report_id` and `decision_report_id`.

## Subprocess Delegation Architecture

The v0.4.1 runner subprocesses the unchanged v0.4.0 runner to produce subjects [0] and [1] in a tempdir, then byte-copies them into the v0.4.1 staging directory and derives the v0.4.1 decision report as subject [2]. The v0.4.1 verifier subprocesses the co-located v0.4.0 verifier on a synthesized 2-subject v0.4.0 manifest and adds five v0.4.1-owned structural checks over the decision report.

This split keeps the v0.4.0 surface untouched. v0.4.0 fixtures, tools, tests, and manifests are not modified by v0.4.1. The v0.4.1 verifier never re-implements an inherited v0.4.0 check; failures inherited from v0.4.0 are relayed unchanged.

## New Artifacts

This release adds:

- two v0.4.1 schemas (decision report and 3-subject manifest);
- a canonical v0.4.1 fixture README pinned to the unchanged v0.4.0 fixture;
- a v0.4.1 Gold decision report runner and verifier under `tools/gold/`;
- a 61-exercise v0.4.1 regression test;
- a Gold Decision Report Hardening release narrative;
- the second Gold demo walkthrough.

The new Make targets are:

```bash
make run-gold-decision-report-hardening-v0-4-1
make verify-gold-decision-report-hardening-v0-4-1
```

`make verify-gold-all` runs the v0.4.0 and v0.4.1 regression suites in sequence.

## Verification

Reported verification for the implementation:

- `make run-gold-decision-report-hardening-v0-4-1` passed;
- `make verify-gold-decision-report-hardening-v0-4-1` passed, 61/61 exercises;
- `make verify-gold-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- v0.3.6, v0.3.7, and v0.4.0 taxonomy regressions passed (47/47, 48/48, 53/53);
- `git diff --check` was clean.

The v0.4.1 regression covers:

- 6 positive-path checks;
- 29 canonical verifier failure reasons (24 inherited via subprocess delegation to v0.4.0, plus 5 v0.4.1-introduced reasons);
- 15 duplicate / secondary `gold_manifest_invalid` cases;
- 1 supplemental decision-report binding case;
- 6 runner-only refusal exercises covering 5 distinct runner-only reasons;
- runner relay of a v0.4.1 verifier failure without a sixth wrapper reason;
- verifier relay of an inherited v0.4.0 failure without a v0.4.1 wrapper reason;
- a taxonomy gate over v0.4.1-owned files with a closed five-entry allowlist limited to exact `coverage_summary` data-field names and an environmental-wrapper deny-list constructed by string concatenation to prevent self-trip;
- scoped source immutability snapshot.

## Stable Public Taxonomy

v0.4.1 preserves the project rule that public failure and refusal reason names are release contracts.

The v0.4.1 verifier exposes 29 approved failure reasons: the 24 inherited v0.4.0 reasons plus five v0.4.1-owned reasons covering the decision report (object shape, schema, binding to the v0.4.0 body, row-level projection, and coverage-summary re-derivation). The runner exposes the same 5 runner-only refusal reasons as v0.4.0. Runner-only refusal reasons and verifier failure reasons remain separate public surfaces. Environmental failures (missing or crashing co-located v0.4.0 verifier) surface under a non-reason-shaped `INFRA:` diagnostic and never inflate the public reason surface.

Human-readable detail may vary after the public reason token, but the public token must remain stable:

```text
FAIL: <approved_reason>: <human detail>
```

## Boundary

v0.4.1 hardens the v0.4.0 decision-report surface. It does not satisfy the multi-stakeholder commitments that full Gold would require.

It does not consult any live service, gateway, observability backend, policy engine, GRC platform, or external registry. It validates structural shape, cross-anchor binding, row-level projection, and coverage-summary re-derivation only. It does not perform end-to-end re-verification of the upstream Silver evidence chain; the v0.4.0 body's five Silver-shaped input blocks remain structural pointers under closed input-type and ref grammar only.

It does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, compliance certification, production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.

Full Gold and Platinum remain conceptual future tiers. Their eventual form should be shaped by feedback from real relying-party, assurance, governance, and implementation contexts rather than assumed in advance.

## Why This Matters

v0.4.0 showed that a relying party can record an explicit reliance posture over a Silver verification result. v0.4.1 shows that that record can be re-projected into a deterministic, hash-anchored decision report whose every row and every coverage cell is re-derivable byte-for-byte from the unchanged v0.4.0 body, under a closed reason surface and a self-bounded taxonomy gate.

That is what "hardening" means in this release: not new claims, but tighter mechanics around the same claims, under a smaller and more closed verification surface.
