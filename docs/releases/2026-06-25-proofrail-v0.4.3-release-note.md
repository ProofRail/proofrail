# ProofRail v0.4.3 — Gold Challenge Lifecycle Lite

ProofRail v0.4.3 is a narrow incremental Gold release.

v0.4.0 introduced the first Minimal Gold boundary: a deterministic local governed-reliance package that records 1..5 relying-party decisions over Silver-shaped inputs. v0.4.1 re-projected that body into a deterministic local Gold decision report bound by a 3-subject manifest. v0.4.2 paired both bodies with a deterministic local policy evaluation matrix and a byte-re-derivable policy evaluation report, bound by a 5-subject manifest cross-anchored to the v0.4.0 body and to the v0.4.1 decision report. v0.4.3 leaves all four prior bodies unchanged and pairs them with a deterministic local runtime challenge-lifecycle records body and a deterministic local lifecycle report, bound by a 7-subject manifest cross-anchored to the v0.4.0 body, the v0.4.1 decision report, and the v0.4.2 policy-evaluation pair.

This release is intentionally narrow. It does not introduce a new Gold tier. It does not consult any live policy engine or live lifecycle adjudication authority. It does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair. It is not signed. It is not a certificate. It is not federated. It is not a transfer of reliance to any external party.

## What v0.4.3 Adds

v0.4.3 adds a deterministic local Gold challenge-lifecycle records body and a deterministic local Gold lifecycle report. The records body is a hand-authored template carrying 5 challenge-lifecycle records in natural order, plus runtime-bound scalars (a SHA-256 anchor to the v0.4.2 policy evaluation report, an ISO-8601 UTC generation timestamp, and a per-record `lifecycle_fingerprint` for each of the 5 records) that are injected by the v0.4.3 runner. The lifecycle report folds the runtime records body against the v0.4.1 decision report and re-derives a top-level `report_fingerprint` and a closed coverage summary over five data fields:

- `lifecycle_record_count`;
- `lifecycle_event_count`;
- `open_lifecycle_count`;
- `terminal_lifecycle_count`;
- `status_value_count`.

No v0.4.3-introduced data-field names appear in the closed taxonomy gate's allowlist.

## 7-Subject Package Layout

The v0.4.3 package layout is:

- subject [0] — the unchanged v0.4.0 governed-reliance package body;
- subject [1] — the unchanged v0.4.0 conformance report;
- subject [2] — the unchanged v0.4.1 Gold decision report;
- subject [3] — the unchanged v0.4.2 policy evaluation matrix (runtime);
- subject [4] — the unchanged v0.4.2 policy evaluation report;
- subject [5] — the v0.4.3 runtime challenge-lifecycle records body;
- subject [6] — the v0.4.3 Gold lifecycle report.

A 7-subject manifest cross-anchors all seven by SHA-256, by the v0.4.0 `package_id` and `governed_reliance_demo_id`, and by the distinct v0.4.0-owned `conformance_report_id`, v0.4.1-owned `decision_report_id`, v0.4.2-owned `matrix_id` and `policy_evaluation_report_id`, and v0.4.3-owned `challenge_lifecycle_record_set_id` and `challenge_lifecycle_report_id`. The runtime records body cross-anchors `policy_evaluation_report_sha256` to subject [4]; the lifecycle report cross-anchors `source_records_sha256`, `source_policy_evaluation_report_sha256`, and `source_decision_report_sha256` to subjects [5], [4], and [2] respectively, and each lifecycle row resolves a `(target_decision_id, target_decision_row_id)` pair into the single corresponding v0.4.1 decision report row.

## Records Template vs Runtime Records

The committed v0.4.3 fixture is a records template. The template carries the canonical 5-record set and natural ordering but does not carry the runtime-bound scalars. The runtime records body is the template plus the injected `policy_evaluation_report_sha256` and `generated_at` top-level scalars and the 5 per-record `lifecycle_fingerprint` values, byte-re-derived and re-anchored by the runner at build time. The schema distinguishes the two shapes by an explicit Records Template vs Runtime Records section so that downstream tooling can verify either without confusion.

This split keeps the committed fixture stable across runs while letting the runtime body bind to the actual v0.4.2 policy-evaluation-report image produced by the chained runners.

## Subprocess Delegation Architecture

The v0.4.3 runner subprocesses the v0.4.2 runner into a tempdir (which itself subprocesses the v0.4.1 runner, which subprocesses the unchanged v0.4.0 runner), byte-copies subjects [0] through [4] into the v0.4.3 staging directory, injects the runtime-bound scalars to derive subject [5], folds subject [5] against subjects [2] and [4] to derive subject [6] and the 7-subject manifest, runs the v0.4.3 verifier against the staging directory under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination on success.

The v0.4.3 verifier subprocesses the co-located v0.4.2 verifier on a synthesized 5-subject v0.4.2 manifest assembled in a tempdir from subjects [0] through [4], and adds ten v0.4.3-owned structural checks over the records body and the lifecycle report. The 7-subject manifest itself remains under the inherited `gold_manifest_invalid` reason surface. This split keeps the v0.4.0, v0.4.1, and v0.4.2 surfaces untouched. v0.4.0, v0.4.1, and v0.4.2 fixtures, tools, tests, and manifests are not modified by v0.4.3. The v0.4.3 verifier never re-implements an inherited check; failures inherited from v0.4.0, v0.4.1, or v0.4.2 are relayed unchanged.

## New Artifacts

This release adds:

- three v0.4.3 schemas (records body, lifecycle report, 7-subject manifest);
- a canonical v0.4.3 fixture (records template and fixture README pinned to the unchanged v0.4.2 fixture);
- a v0.4.3 Gold challenge-lifecycle-lite runner and verifier under `tools/gold/`;
- a 99-exercise v0.4.3 regression test;
- a Gold Challenge Lifecycle Lite release narrative;
- the fourth Gold demo walkthrough.

The new Make targets are:

```bash
make run-gold-challenge-lifecycle-lite-v0-4-3
make verify-gold-challenge-lifecycle-lite-v0-4-3
```

`make verify-gold-all` runs the v0.4.0, v0.4.1, v0.4.2, and v0.4.3 regression suites in sequence.

## Verification

Reported verification for the implementation:

- `make run-gold-challenge-lifecycle-lite-v0-4-3` passed;
- `make verify-gold-challenge-lifecycle-lite-v0-4-3` passed, 99/99 exercises;
- `make verify-gold-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- v0.3.6, v0.3.7, v0.4.0, v0.4.1, and v0.4.2 taxonomy regressions passed;
- `git diff --check` was clean.

The v0.4.3 regression covers:

- 6 positive-path checks;
- 48 canonical verifier failure reasons (24 inherited via subprocess delegation to v0.4.0, plus 5 inherited via subprocess delegation to v0.4.1, plus 9 inherited via subprocess delegation to v0.4.2, plus 10 v0.4.3-introduced reasons);
- 4 runtime-scalar canonicals folding to the v0.4.3-owned records-shape and records-binding reasons;
- 23 duplicate / secondary `gold_manifest_invalid` cases (including 6-ID pairwise-distinctness collision sub-cases);
- 5 supplemental cases covering missing required withdrawal reference, first event not filed, event after terminal status, `current_status` disagreement, and report-ID collision at report-body validation;
- 6 runner-only refusal exercises covering 5 distinct runner-only reasons;
- runner relay of a v0.4.3 verifier failure without a sixth wrapper reason;
- verifier relay of an inherited v0.4.0, v0.4.1, or v0.4.2 failure without a v0.4.3 wrapper reason;
- environment-failure `INFRA:` diagnostic exercise;
- a positive determinism re-run over the runtime scalars (subject [5].sha256, subject [6].sha256, all 5 per-record `lifecycle_fingerprint`, and `report_fingerprint`);
- a no-residue assertion over the v0.4.3 scratch path and the inherited tier fixtures;
- a taxonomy gate over v0.4.3-owned files with an environmental-wrapper deny-list constructed by string concatenation to prevent self-trip;
- scoped source immutability snapshot.

The 99-exercise decomposition is: 6 PP + 48 canonical + 4 runtime + 23 duplicate/collision + 5 supplemental + 6 runner-only + 2 relay + 1 environment + 1 determinism + 1 no-residue + 1 TG1 + 1 SS.

## Stable Public Taxonomy

v0.4.3 preserves the project rule that public failure and refusal reason names are release contracts.

The v0.4.3 verifier exposes 48 approved failure reasons: the 24 inherited v0.4.0 reasons, the 5 inherited v0.4.1 reasons, the 9 inherited v0.4.2 reasons, and 10 v0.4.3-owned reasons covering the records body (object shape, schema, binding to the v0.4.2 policy evaluation report, per-record event grammar, per-record transition orderings) and the lifecycle report (object shape, schema, binding to the runtime records body, row-level projection, coverage-summary re-derivation). The 7-subject manifest itself remains under the inherited `gold_manifest_invalid` reason. The runner exposes the same 5 runner-only refusal reasons as v0.4.0, v0.4.1, and v0.4.2. Runner-only refusal reasons and verifier failure reasons remain separate public surfaces. Environmental failures (missing or crashing co-located v0.4.2 verifier) surface under a non-reason-shaped `INFRA:` diagnostic and never inflate the public reason surface.

Human-readable detail may vary after the public reason token, but the public token must remain stable:

```text
FAIL: <approved_reason>: <human detail>
```

The closed reason surface is documented in `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md`.

## Boundary

v0.4.3 hardens the local challenge-lifecycle surface over the unchanged v0.4.0 body, v0.4.1 decision report, and v0.4.2 policy-evaluation pair. It does not satisfy the multi-stakeholder commitments that full Gold would require.

It does not consult any live service, gateway, observability backend, policy engine, lifecycle adjudication authority, GRC platform, SIEM, certification authority, or external registry. It validates structural shape, runtime-scalar injection, cross-anchor binding, per-record event and transition grammar, lifecycle row projection, and coverage-summary re-derivation only. It does not perform end-to-end re-verification of the upstream Silver evidence chain; the v0.4.0 body's five Silver-shaped input blocks remain structural pointers under closed input-type and ref grammar only.

v0.4.3 is not a policy engine, not a lifecycle adjudication authority, not a GRC platform, not a gateway, not a SIEM, not an observability backend, not a certification authority, not a regulator, and not a production authorization system. It is a deterministic local re-derivation surface over already-published Gold artifacts.

It does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, compliance certification, production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.

Full Gold and Platinum remain conceptual future tiers. Their eventual form should be shaped by feedback from real relying-party, assurance, governance, and implementation contexts rather than assumed in advance.

## Why This Matters

v0.4.0 showed that a relying party can record an explicit reliance posture over a Silver verification result. v0.4.1 showed that that record can be re-projected into a deterministic, hash-anchored decision report whose every row and every coverage cell is re-derivable byte-for-byte from the unchanged v0.4.0 body. v0.4.2 showed that the same record can be folded against a deterministic local policy evaluation matrix, in natural row order, under explicit cross-anchor bindings, with the resulting evaluation report's every row and every coverage cell byte-re-derivable from the matrix template, the injected runtime scalars, and the unchanged v0.4.1 decision report. v0.4.3 shows that the same record can carry a deterministic local runtime challenge-lifecycle record set whose closed event-pair grammar, closed transition orderings, per-record `lifecycle_fingerprint`, top-level `report_fingerprint`, and lifecycle-report row projection and coverage summary are all byte-re-derivable from the runtime records body, the runtime scalars, and the unchanged Gold artifacts beneath it, under a closed 48-reason surface and a self-bounded taxonomy gate.

That is what this release means: not new claims, but a tighter local re-derivation surface around the same claims, with challenge-lifecycle state made explicit, tabular, and independently re-derivable, while leaving any live lifecycle adjudication strictly outside scope.
