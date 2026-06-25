# Gold Demo 002 — Walkthrough (v0.4.1)

This document records the step-by-step output of a clean v0.4.1 decision-report hardening run. It is illustrative; consult the live `make` targets for the authoritative invocation.

## Step 0 — Preconditions

The v0.4.0 canonical fixture must exist at `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`. The v0.4.0 runner and verifier must be present at `tools/gold/build_gold_governed_reliance_demo_v0_1_0.py` and `tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py`.

## Step 1 — Run the v0.4.1 runner

```
make run-gold-decision-report-hardening-v0-4-1
```

The runner performs Phase A preflight on `--input-package`, subprocesses the v0.4.0 runner into a tempdir, byte-copies subjects [0] and [1] into the v0.4.1 staging directory, derives subject [2] (the decision report) and the 3-subject manifest, runs the v0.4.1 verifier against the staging directory under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination on success.

## Step 2 — Verify the published manifest

```
python3 tools/gold/verify_gold_decision_report_hardening_v0_1_0.py \
  --manifest /tmp/proofrail-gold-decision-report-hardening-v0.4.1/gold-decision-report-package-manifest.json
```

Expected output: a single `PASS:` line on stdout and exit code 0. The verifier subprocesses the co-located v0.4.0 verifier on a synthesized 2-subject v0.4.0 manifest assembled in a tempdir from subjects [0] and [1]; the v0.4.0 verifier's PASS line is consumed (its 24 inherited reasons surface only on failure).

## Step 3 — Run the regression test

```
make verify-gold-decision-report-hardening-v0-4-1
```

The test exercises 61 ordered cases:

- 6 positive-path
- 29 canonical verifier reasons (24 inherited + 5 v0.4.1-owned)
- 15 duplicate / secondary `gold_manifest_invalid`
- 1 supplemental decision-report binding case (folds to R27)
- 6 runner-only refusals
- 1 runner-relay-of-verifier
- 1 verifier-relay-of-inherited
- 1 TG1 taxonomy gate
- 1 scoped sha256 snapshot

The taxonomy gate enforces a closed allowlist limited to the five exact `coverage_summary` data-field names. The scoped snapshot proves that the test does not mutate v0.4.1-owned source files.

## Step 4 — Inspect the published package

```
ls /tmp/proofrail-gold-decision-report-hardening-v0.4.1/
```

Four files appear:

- `governed-reliance-scenarios.json` (v0.4.0 package body, byte-copy)
- `silver-gold-governed-reliance-conformance-report.json` (v0.4.0 conformance report, byte-copy)
- `gold-governed-reliance-decision-report.json` (v0.4.1 decision report, derived)
- `gold-decision-report-package-manifest.json` (3-subject manifest)

The manifest cross-anchors `package_id` and `governed_reliance_demo_id` to the v0.4.0 body, and the decision report cross-anchors `source_package_sha256` and `source_conformance_report_sha256` to subjects [0] and [1] respectively.

## Reference

See `README.md` in this directory for the demo's framing, and `docs/gold/gold-decision-report-hardening-v0.4.1.md` for the release narrative and the closed reason surface.
