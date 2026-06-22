# Silver Demo 006 — Revocation/Challenge Drill Walkthrough

This walkthrough shows the v0.2.9 revocation/challenge drill end to end.
All runtime output is written under `/tmp/` and is not committed.

## Prerequisites

- Python 3 with `cryptography` and `PyYAML` installed
  (`pip install -r requirements.txt`).
- A clean repository checkout at the v0.2.9 line.

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

Output: `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/`
containing `composed-gateway-evidence-report.json` and
`composed-gateway-evidence-manifest.json`.

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

Output: `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/`
containing `acceptance-policy.json`, `acceptance-record.json`,
`evidence/composed-gateway-evidence-manifest.json`, and
`acceptance-package-manifest.json`.

## Step 3 — Run the v0.2.9 revocation/challenge drill

```bash
python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
  --generated-at 2026-06-27T00:00:00Z \
  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
  --force
```

The runner:

1. Subprocess-invokes the v0.2.8 acceptance validator against the
   acceptance manifest. On non-zero exit it prints
   `FAIL: acceptance_package_validation_failed: <detail>` and exits 1
   without leaving any partial output on disk.
2. Copies the full v0.2.8 package into
   `acceptance-package/` inside a temporary staging directory next to
   the destination.
3. Copies the review-events fixture into the staging directory.
4. Parses the nested acceptance record, derives the bound
   `acceptance_record_id`, `decision.status`, `purpose_id`, policy
   id/version, and challenge window.
5. Parses the review-events JSONL strictly, asserts targets match the
   bound acceptance record, and asserts `event_time` monotonicity.
6. Refuses (`review_fixture_insufficient`) when the fixture contains no
   within-window challenge or no revocation signal.
7. Derives findings, review triggers, and
   `recommended_local_posture = acceptance_requires_review_before_reuse`.
8. Writes `revocation-challenge-drill-report.json` and
   `revocation-challenge-drill-manifest.json` into the staging
   directory, then atomically moves the staging directory to the final
   `--output-dir`.

Resulting layout:

```
/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/
  acceptance-package/
    acceptance-policy.json
    acceptance-record.json
    acceptance-package-manifest.json
    evidence/
      composed-gateway-evidence-manifest.json
  review-events.jsonl
  revocation-challenge-drill-report.json
  revocation-challenge-drill-manifest.json
```

## Step 4 — Verify the drill package

```bash
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \
  --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json
```

Expected output:

```
PASS: revocation/challenge drill valid (proofrail-revocation-challenge-drill-demo-001)
```

Optional — also revalidate the original v0.2.7 evidence package:

```bash
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \
  --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  --evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7
```

## Non-claims

The v0.2.9 drill produces a deterministic, hash-anchored local evidence
artifact. It records review triggers. It does **not** decide their
merits, revoke acceptance, certify the evidence, or execute Gold
governance.
