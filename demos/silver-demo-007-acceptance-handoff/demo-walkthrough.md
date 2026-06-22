# Silver Demo 007 — Acceptance Handoff Walkthrough

This walkthrough shows the v0.3.0 acceptance handoff end to end. All
runtime output is written under `/tmp/` and is not committed.

## Prerequisites

- Python 3 with `cryptography` and `PyYAML` installed
  (`pip install -r requirements.txt`).
- A clean repository checkout at the v0.3.0 line.

## Step 1 — Compose v0.2.7 gateway evidence

```bash
python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
  --demo-root demos/silver-demo-004-composed-gateway-evidence \
  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
  --generated-at 2026-06-22T00:00:00Z \
  --force
```

## Step 2 — Generate the v0.2.8 acceptance package

```bash
python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py \
  --policy fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json \
  --evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at 2026-06-22T00:00:00Z \
  --challenge-closes-at 2026-07-22T00:00:00Z \
  --output-dir /tmp/proofrail-silver-relying-party-acceptance-v0.2.8 \
  --force
```

## Step 3 — Run the v0.2.9 revocation/challenge drill

```bash
python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
  --generated-at 2026-06-27T00:00:00Z \
  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
  --force
```

## Step 4 — Build the v0.3.0 acceptance handoff package

```bash
python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py \
  --composed-evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --drill-manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  --generated-at 2026-06-28T00:00:00Z \
  --output-dir /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
  --force
```

The runner:

1. Subprocess-invokes the v0.2.7 verifier on the composed-evidence
   manifest. On non-zero exit it prints
   `FAIL: composed_evidence_validation_failed: <detail>` and exits 1
   without writing any output.
2. Subprocess-invokes the v0.2.8 acceptance validator on the
   acceptance manifest WITHOUT `--evidence-package-root`. On non-zero
   exit it prints `FAIL: acceptance_package_validation_failed: <detail>`
   and exits 1.
3. Subprocess-invokes the v0.2.9 drill verifier on the drill manifest
   WITHOUT `--evidence-package-root`. On non-zero exit it prints
   `FAIL: drill_package_validation_failed: <detail>` and exits 1.
4. Byte-copies the three nested package roots into a temporary
   staging directory under fixed top-level names:
     - `composed-gateway-evidence/` (v0.2.7 root)
     - `acceptance-package/` (v0.2.8 root)
     - `revocation-challenge-drill/` (v0.2.9 root)
5. Performs four chain-binding cross-checks:
     - top-level `composed-gateway-evidence/...-manifest.json` sha256
       equals the nested v0.2.8 record's
       `evidence_package.manifest_sha256`;
     - top-level `acceptance-package/acceptance-package-manifest.json`
       sha256 equals the nested v0.2.9 drill report's
       `base_acceptance.acceptance_package_manifest_sha256`;
     - the inner copy at
       `acceptance-package/evidence/composed-gateway-evidence-manifest.json`
       has the same sha256 as subject [0];
     - the inner copy at
       `revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json`
       has the same sha256 as subject [1].
   Any mismatch yields
   `FAIL: handoff_chain_binding_failed: <detail>` and exit 1.
6. Maps the nested v0.2.9 `recommended_local_posture` onto a minimum
   handoff posture rank and chooses `recommended_handoff_posture =
   silver_handoff_complete_review_required_before_reuse` for the
   deterministic demo fixture chain.
7. Writes `silver-acceptance-handoff-summary.json` and
   `silver-acceptance-handoff-manifest.json` into the staging
   directory.
8. With `--self-validate`, subprocess-invokes the v0.3.0 handoff
   verifier on the staged manifest BEFORE the atomic move. On failure
   it removes the staging directory, leaves the destination
   untouched, and exits 1.
9. Atomically moves the staging directory to `--output-dir`.

Resulting layout:

```
/tmp/proofrail-silver-acceptance-handoff-v0.3.0/
  composed-gateway-evidence/             (full v0.2.7 root byte-copy)
    composed-gateway-evidence-manifest.json
    composed-gateway-evidence-report.json
    adapter/
    source/
    README.md
    demo-walkthrough.md
  acceptance-package/                    (full v0.2.8 root byte-copy)
    acceptance-policy.json
    acceptance-record.json
    acceptance-package-manifest.json
    evidence/
      composed-gateway-evidence-manifest.json
  revocation-challenge-drill/            (full v0.2.9 root byte-copy)
    acceptance-package/
      acceptance-policy.json
      acceptance-record.json
      acceptance-package-manifest.json
      evidence/
        composed-gateway-evidence-manifest.json
    review-events.jsonl
    revocation-challenge-drill-report.json
    revocation-challenge-drill-manifest.json
  silver-acceptance-handoff-summary.json
  silver-acceptance-handoff-manifest.json
```

## Step 5 — Verify the handoff package

```bash
python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py \
  --manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json
```

Expected output:

```
PASS: silver acceptance handoff valid (proofrail-silver-acceptance-handoff-demo-001)
```

The verifier re-runs the unchanged v0.2.7 verifier, v0.2.8
validator, and v0.2.9 verifier as subprocesses (each without
`--evidence-package-root`), then performs the four v0.3.0-owned chain
bindings, the record / purpose cross-checks, the posture rank check,
and the overclaim guard.

## Non-claims

The v0.3.0 handoff package produces a deterministic, hash-anchored,
portable local artifact that binds three already-verified Silver
pipelines. It is **not** a certificate, Gold conformance, regulator
approval, auditor approval, legal acceptance, or a transfer of
reliance. The recommended handoff posture is descriptive; it does
not adjudicate or approve anything.
