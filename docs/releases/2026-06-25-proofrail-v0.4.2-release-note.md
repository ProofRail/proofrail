# ProofRail v0.4.2 — Gold Policy Evaluation Matrix

ProofRail v0.4.2 is a narrow Gold maintenance release.

v0.4.0 introduced the first Minimal Gold boundary: a deterministic local governed-reliance package that records 1..5 relying-party decisions over Silver-shaped inputs. v0.4.1 re-projected that body into a deterministic local Gold decision report bound by a 3-subject manifest. v0.4.2 leaves both bodies unchanged and pairs them with a deterministic local policy evaluation matrix and a byte-re-derivable policy evaluation report, bound by a 5-subject manifest cross-anchored to the v0.4.0 body and to the v0.4.1 decision report.

This release is intentionally narrow. It does not introduce a new Gold tier. It does not consult any live policy engine. It does not extend the substance of the v0.4.0 body or the v0.4.1 decision report. It is not signed. It is not a certificate. It is not federated. It is not a transfer of reliance to any external party.

The implementation is committed as `501694c` on `main`.

## What v0.4.2 Adds

v0.4.2 adds a deterministic local Gold policy evaluation matrix and a deterministic local Gold policy evaluation report. The matrix is a hand-authored template carrying one row per recognized governed-reliance scenario in natural order, plus two runtime-bound scalars (a SHA-256 anchor to the v0.4.1 decision report and an ISO-8601 UTC generation timestamp) that are injected by the v0.4.2 runner. The evaluation report folds the runtime matrix against the v0.4.1 decision report and re-derives a closed coverage summary over the same five data-field names already published by the v0.4.1 decision report:

- `decision_statuses_present`;
- `policy_decisions_present`;
- `protected_actions_present`;
- `registry_roles_present`;
- `scenario_types_present`.

No v0.4.2-introduced data-field names appear in the closed taxonomy gate's allowlist.

## 5-Subject Package Layout

The v0.4.2 package layout is:

- subject [0] — the unchanged v0.4.0 governed-reliance package body;
- subject [1] — the unchanged v0.4.0 conformance report;
- subject [2] — the unchanged v0.4.1 Gold decision report;
- subject [3] — the v0.4.2 runtime policy evaluation matrix;
- subject [4] — the v0.4.2 Gold policy evaluation report.

A 5-subject manifest cross-anchors all five by SHA-256, by the v0.4.0 `package_id` and `governed_reliance_demo_id`, and by distinct v0.4.1-owned `conformance_report_id` and `decision_report_id` and v0.4.2-owned `policy_evaluation_matrix_id` and `policy_evaluation_report_id`. The runtime matrix cross-anchors `decision_report_sha256` to subject [2]; the evaluation report cross-anchors `source_decision_report_sha256` and `source_matrix_sha256` to subjects [2] and [3].

## Matrix Template vs Runtime Matrix

The committed v0.4.2 fixture is a matrix template. The template carries the canonical row set and natural ordering but does not carry the two runtime-bound scalars. The runtime matrix is the template plus the injected `decision_report_sha256` and `generated_at` scalars, byte-re-derived and re-anchored by the runner at build time. The schema distinguishes the two shapes by an explicit Matrix Template vs Runtime Matrix section so that downstream tooling can verify either without confusion.

This split keeps the committed fixture stable across runs while letting the runtime matrix bind to the actual v0.4.1 decision report image produced by the chained runners.

## Subprocess Delegation Architecture

The v0.4.2 runner subprocesses the v0.4.1 runner into a tempdir (which itself subprocesses the unchanged v0.4.0 runner), byte-copies subjects [0], [1], and [2] into the v0.4.2 staging directory, injects the runtime-bound scalars to derive subject [3], folds subject [3] against subject [2] to derive subject [4] and the 5-subject manifest, runs the v0.4.2 verifier against the staging directory under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination on success.

The v0.4.2 verifier subprocesses the co-located v0.4.1 verifier on a synthesized 3-subject v0.4.1 manifest assembled in a tempdir from subjects [0], [1], and [2], and adds nine v0.4.2-owned structural checks over the matrix, the evaluation report, and the 5-subject manifest. This split keeps the v0.4.0 and v0.4.1 surfaces untouched. v0.4.0 and v0.4.1 fixtures, tools, tests, and manifests are not modified by v0.4.2. The v0.4.2 verifier never re-implements an inherited check; failures inherited from v0.4.0 or v0.4.1 are relayed unchanged.

## New Artifacts

This release adds:

- three v0.4.2 schemas (matrix, evaluation report, 5-subject manifest);
- a canonical v0.4.2 fixture (matrix template and fixture README pinned to the unchanged v0.4.0 fixture);
- a v0.4.2 Gold policy evaluation matrix runner and verifier under `tools/gold/`;
- a 78-exercise v0.4.2 regression test;
- a Gold Policy Evaluation Matrix release narrative;
- the third Gold demo walkthrough.

The new Make targets are:

```bash
make run-gold-policy-evaluation-matrix-v0-4-2
make verify-gold-policy-evaluation-matrix-v0-4-2
```

`make verify-gold-all` runs the v0.4.0, v0.4.1, and v0.4.2 regression suites in sequence.

## Verification

Reported verification for the implementation:

- `make run-gold-policy-evaluation-matrix-v0-4-2` passed;
- `make verify-gold-policy-evaluation-matrix-v0-4-2` passed, 78/78 exercises;
- `make verify-gold-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- v0.3.6, v0.3.7, v0.4.0, and v0.4.1 taxonomy regressions passed;
- `git diff --check` was clean.

The v0.4.2 regression covers:

- 6 positive-path checks;
- 38 canonical verifier failure reasons (24 inherited via subprocess delegation to v0.4.0, plus 5 inherited via subprocess delegation to v0.4.1, plus 9 v0.4.2-introduced reasons);
- 3 runtime-scalar canonicals folding to the inherited matrix-shape and matrix-binding reasons;
- 18 duplicate / secondary `gold_manifest_invalid` cases;
- 4 supplemental cases covering binding cross-anchor, positive determinism, and limitations-block prohibited-token allowance;
- 6 runner-only refusal exercises covering 5 distinct runner-only reasons;
- runner relay of a v0.4.2 verifier failure without a wrapper reason;
- verifier relay of an inherited v0.4.0 or v0.4.1 failure without a v0.4.2 wrapper reason;
- environment-failure `INFRA:` diagnostic exercise;
- a taxonomy gate over v0.4.2-owned files with a closed five-entry allowlist limited to exact inherited v0.4.1 `coverage_summary` data-field names and an environmental-wrapper deny-list constructed by string concatenation to prevent self-trip;
- scoped source immutability snapshot.

## Stable Public Taxonomy

v0.4.2 preserves the project rule that public failure and refusal reason names are release contracts.

The v0.4.2 verifier exposes 38 approved failure reasons: the 24 inherited v0.4.0 reasons, the 5 inherited v0.4.1 reasons, and 9 v0.4.2-owned reasons covering the matrix (object shape, schema, runtime-scalar injection, binding to the v0.4.1 decision report), the evaluation report (object shape, schema, row-level fold against the matrix and decision report, coverage-summary re-derivation), and the 5-subject manifest. The runner exposes the same 5 runner-only refusal reasons as v0.4.0 and v0.4.1. Runner-only refusal reasons and verifier failure reasons remain separate public surfaces. Environmental failures (missing or crashing co-located v0.4.1 verifier) surface under a non-reason-shaped `INFRA:` diagnostic and never inflate the public reason surface.

Human-readable detail may vary after the public reason token, but the public token must remain stable:

```text
FAIL: <approved_reason>: <human detail>
```

The closed reason surface is documented in `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md`.

## Boundary

v0.4.2 hardens the local policy-evaluation surface over the unchanged v0.4.0 body and v0.4.1 decision report. It does not satisfy the multi-stakeholder commitments that full Gold would require.

It does not consult any live service, gateway, observability backend, policy engine, GRC platform, SIEM, certification authority, or external registry. It validates structural shape, runtime-scalar injection, cross-anchor binding, row-level fold, and coverage-summary re-derivation only. It does not perform end-to-end re-verification of the upstream Silver evidence chain; the v0.4.0 body's five Silver-shaped input blocks remain structural pointers under closed input-type and ref grammar only.

v0.4.2 is not a policy engine, not a GRC platform, not a gateway, not a SIEM, not an observability backend, not a certification authority, not a regulator, and not a production authorization system. It is a deterministic local re-derivation surface over already-published Gold artifacts.

It does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, compliance certification, production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.

Full Gold and Platinum remain conceptual future tiers. Their eventual form should be shaped by feedback from real relying-party, assurance, governance, and implementation contexts rather than assumed in advance.

## Why This Matters

v0.4.0 showed that a relying party can record an explicit reliance posture over a Silver verification result. v0.4.1 showed that that record can be re-projected into a deterministic, hash-anchored decision report whose every row and every coverage cell is re-derivable byte-for-byte from the unchanged v0.4.0 body. v0.4.2 shows that the same record can be folded against a deterministic local policy evaluation matrix, in natural row order, under explicit cross-anchor bindings, with the resulting evaluation report's every row and every coverage cell byte-re-derivable from the matrix template, the injected runtime scalars, and the unchanged v0.4.1 decision report, under a closed reason surface and a self-bounded taxonomy gate.

That is what this release means: not new claims, but a tighter local re-derivation surface around the same claims, with policy evaluation made explicit, tabular, and independently re-derivable.
