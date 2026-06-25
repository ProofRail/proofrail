# Gold Demo 003 — Walkthrough (v0.4.2)

This document records the step-by-step output of a clean v0.4.2 policy-evaluation-matrix run. It is illustrative; consult the live `make` targets for the authoritative invocation.

## Step 0 — Preconditions

The v0.4.0 canonical fixture must exist at `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`. The v0.4.2 matrix template must exist at `fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json`. The v0.4.0 and v0.4.1 runners and verifiers must be present under `tools/gold/`.

## Step 1 — Run the v0.4.2 runner

```
make run-gold-policy-evaluation-matrix-v0-4-2
```

The runner performs Phase A preflight on `--input-package` and `--matrix-input`, subprocesses the v0.4.1 runner into a tempdir (which itself subprocesses the v0.4.0 runner), byte-copies subjects [0], [1], and [2] into the v0.4.2 staging directory, injects the runtime-bound scalars into subject [3] (the runtime matrix), derives subject [4] (the evaluation report) and the 5-subject manifest, runs the v0.4.2 verifier against the staging directory under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination on success.

## Step 2 — Verify the published manifest

```
python3 tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py \
  --manifest /tmp/proofrail-gold-policy-evaluation-matrix-v0.4.2/gold-policy-evaluation-matrix-package-manifest.json
```

Expected output: a single `PASS:` line on stdout and exit code 0. The verifier subprocesses the co-located v0.4.1 verifier on a synthesized 3-subject v0.4.1 manifest assembled in a tempdir from subjects [0], [1], and [2]; the v0.4.1 verifier's PASS line is consumed (its 29 inherited reasons surface only on failure).

## Step 3 — Run the regression test

```
make verify-gold-policy-evaluation-matrix-v0-4-2
```

The test exercises 78 ordered cases:

- 6 positive-path
- 38 canonical verifier reasons (24 inherited from v0.4.0 + 5 inherited from v0.4.1 + 9 v0.4.2-owned)
- 3 runtime-scalar canonicals folding to the inherited matrix-shape and matrix-binding reasons
- 18 duplicate / secondary manifest-invalid
- 4 supplementals (binding cross-anchor, positive determinism, and limitations-block prohibited-token allowance)
- 6 runner-only refusals
- 1 runner-relay-of-verifier
- 1 verifier-relay-of-inherited
- 1 environment-failure INFRA diagnostic
- 1 TG1 taxonomy gate
- 1 scoped sha256 snapshot

The taxonomy gate enforces a closed allowlist limited to the five exact `coverage_summary` data-field names inherited from the v0.4.1 decision-report schema. The scoped snapshot proves that the test does not mutate v0.4.2-owned source files.

## Step 4 — Inspect the published package

```
ls /tmp/proofrail-gold-policy-evaluation-matrix-v0.4.2/
```

Six files appear:

- `governed-reliance-scenarios.json` (v0.4.0 package body, byte-copy)
- `silver-gold-governed-reliance-conformance-report.json` (v0.4.0 conformance report, byte-copy)
- `gold-governed-reliance-decision-report.json` (v0.4.1 decision report, byte-copy)
- `gold-policy-evaluation-matrix.json` (v0.4.2 runtime matrix, derived from the template plus the two injected runtime scalars)
- `gold-policy-evaluation-report.json` (v0.4.2 evaluation report, derived from the matrix and the decision report)
- `gold-policy-evaluation-matrix-package-manifest.json` (5-subject manifest)

The manifest cross-anchors `package_id` and `governed_reliance_demo_id` to the v0.4.0 body. The runtime matrix cross-anchors `decision_report_sha256` to subject [2]. The evaluation report cross-anchors `source_decision_report_sha256` and `source_matrix_sha256` to subjects [2] and [3] respectively.

## Reference

See `README.md` in this directory for the demo's framing, and `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md` for the release narrative and the closed reason surface.
