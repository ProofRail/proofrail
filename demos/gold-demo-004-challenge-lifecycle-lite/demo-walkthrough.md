# Gold Demo 004 — Walkthrough (v0.4.3)

This document records the step-by-step output of a clean v0.4.3 challenge-lifecycle-lite run. It is illustrative; consult the live `make` targets for the authoritative invocation.

## Step 0 — Preconditions

The v0.4.0 canonical fixture must exist at `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`. The v0.4.2 matrix template must exist at `fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json`. The v0.4.3 records template must exist at `fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json`. The v0.4.0, v0.4.1, and v0.4.2 runners and verifiers must be present under `tools/gold/`.

## Step 1 — Run the v0.4.3 runner

```
make run-gold-challenge-lifecycle-lite-v0-4-3
```

The runner performs Phase A preflight on `--input-package`, `--matrix-input`, and `--lifecycle-input`, subprocesses the v0.4.2 runner into a tempdir (which itself subprocesses the v0.4.1 and v0.4.0 runners), byte-copies subjects [0]..[4] into the v0.4.3 staging directory, injects the runtime-bound scalars into subject [5] (the runtime records body), derives subject [6] (the lifecycle report) and the 7-subject manifest, runs the v0.4.3 verifier against the staging directory under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination on success.

## Step 2 — Verify the published manifest

```
python3 tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py \
  --manifest /tmp/proofrail-gold-challenge-lifecycle-lite-v0.4.3/gold-challenge-lifecycle-package-manifest.json
```

Expected output: a single `PASS:` line on stdout and exit code 0. The verifier subprocesses the co-located v0.4.2 verifier on a synthesized 5-subject v0.4.2 manifest assembled in a tempdir from subjects [0]..[4]; the v0.4.2 verifier's PASS line is consumed (its 38 inherited reasons surface only on failure).

## Step 3 — Run the regression test

```
make verify-gold-challenge-lifecycle-lite-v0-4-3
```

v0.4.3 shipped with 99 ordered cases:

- 6 positive-path
- 48 canonical verifier reasons (24 inherited from v0.4.0 + 5 inherited from v0.4.1 + 9 inherited from v0.4.2 + 10 v0.4.3-owned)
- 4 runtime-scalar mutation variants folding to records-shape and records-binding reasons
- 23 duplicate / subject-table / collision cases
- 5 supplementals (R42 × 1, R43 × 3, R46 × 1)
- 6 runner-only refusals across 5 approved reasons
- 1 runner-relay-of-verifier
- 1 verifier-relay-of-inherited
- 1 environment-failure INFRA diagnostic
- 1 positive-determinism re-run
- 1 no-residue assertion (scratch + inherited tiers)
- 1 TG1 taxonomy gate
- 1 scoped sha256 snapshot

The v0.4.3.1 corrective harness raises the regression to 101 ordered cases by appending two cases that exercise the deliberate non-monotonic fingerprint sub-checks added by the v0.4.3.1 verifier correction: rt4 (a fifth runtime-scalar mutation variant) flips the first hex digit of `lifecycle_records[0].lifecycle_fingerprint` and expects R41; sup06 (a sixth supplemental) flips the first hex digit of the top-level `report_fingerprint` and expects R47. Both cases assert that the replacement value differs from the original before invoking the verifier. The 99/99 reachability surface from the v0.4.3 release is preserved verbatim.

The taxonomy gate enforces a closed allowlist limited to the five inherited v0.4.1 decision-report `coverage_summary` enum-presence data-field names (`decision_statuses_present`, `policy_decisions_present`, `protected_actions_present`, `registry_roles_present`, `scenario_types_present`). No v0.4.3-introduced data-field name appears in the allowlist; the v0.4.3 coverage-summary names (`lifecycle_record_count`, `lifecycle_event_count`, `open_lifecycle_count`, `terminal_lifecycle_count`, `status_value_count`) do not satisfy the gate's reason-shaped suffix filter and therefore require no entry. The scoped snapshot proves that the test does not mutate v0.4.3-owned source files. The no-residue assertion proves that the test writes no artifacts under inherited-tier fixture directories and leaves no residue under the test-owned scratch path.

## Step 4 — Inspect the published package

```
ls /tmp/proofrail-gold-challenge-lifecycle-lite-v0.4.3/
```

Eight files appear:

- `governed-reliance-scenarios.json` (v0.4.0 package body, byte-copy)
- `silver-gold-governed-reliance-conformance-report.json` (v0.4.0 conformance report, byte-copy)
- `gold-governed-reliance-decision-report.json` (v0.4.1 decision report, byte-copy)
- `gold-policy-evaluation-matrix.json` (v0.4.2 runtime matrix, byte-copy)
- `gold-policy-evaluation-report.json` (v0.4.2 evaluation report, byte-copy)
- `challenge-lifecycle-records.json` (v0.4.3 runtime records body, derived from the template plus the three injected runtime scalars)
- `gold-challenge-lifecycle-report.json` (v0.4.3 lifecycle report, derived from the records body and the evaluation report)
- `gold-challenge-lifecycle-package-manifest.json` (7-subject manifest)

The manifest cross-anchors `package_id` and `governed_reliance_demo_id` to the v0.4.0 body. The runtime records body cross-anchors `policy_evaluation_report_sha256` to subject [4]. The lifecycle report cross-anchors `source_records_sha256`, `source_policy_evaluation_report_sha256`, and `source_decision_report_sha256` to subjects [5], [4], and [2] respectively.

## Reference

See `README.md` in this directory for the demo's framing, and `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md` for the release narrative and the closed reason surface.
