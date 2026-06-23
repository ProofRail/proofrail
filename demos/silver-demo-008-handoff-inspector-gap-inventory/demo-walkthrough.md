# Silver Demo 008 — Walkthrough (v0.3.1)

This walkthrough shows the deterministic v0.3.1 Silver handoff
inspection chain end to end.

## 0. Prerequisites

A clean checkout with Python 3.8+ available as `python3`. No third-party
runtime dependencies are required for v0.3.1 (`pyyaml` / `cryptography`
are required for earlier Silver releases in the chain).

## 1. Rebuild the v0.2.7 → v0.2.8 → v0.2.9 → v0.3.0 chain

```bash
make run-silver-acceptance-handoff-v0-3-0
```

This produces:

```
/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/
/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/
/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/
/tmp/proofrail-silver-acceptance-handoff-v0.3.0/
```

## 2. Run the v0.3.1 inspector with self-validate

```bash
python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py \
  --handoff-manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json \
  --requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json \
  --generated-at 2026-06-29T00:00:00Z \
  --output-dir /tmp/proofrail-silver-handoff-inspection-v0.3.1 \
  --force \
  --self-validate
```

Expected output (counts will exactly match the fixture):

```
PASS: silver handoff inspection package built at /tmp/proofrail-silver-handoff-inspection-v0.3.1
  inspection_id: proofrail-silver-handoff-inspection-demo-001
  base_handoff.handoff_id: proofrail-silver-acceptance-handoff-demo-001
  handoff_summary.acceptance_record_id: proofrail-acceptance-record-demo-001
  handoff_summary.decision_status: accepted
  handoff_summary.recommended_handoff_posture: silver_handoff_complete_review_required_before_reuse
  gold_gap_inventory.gold_boundary_status: gold_not_claimed
  gold_gap_inventory.counts: present=1 partial=4 unmet=6 out_of_scope=2
```

`--self-validate` invokes the v0.3.1 verifier on the staged package
**before** the atomic move into place. If the verifier fails, the
staging directory is removed and the destination is left untouched
(stderr: `FAIL: inspection_self_validation_failed: <detail>`, exit 1).

## 3. Independently verify the inspection package

```bash
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \
  --manifest /tmp/proofrail-silver-handoff-inspection-v0.3.1/silver-handoff-inspection-manifest.json
```

Expected output:

```
PASS: silver handoff inspection package verified at /tmp/proofrail-silver-handoff-inspection-v0.3.1
  inspection_id: proofrail-silver-handoff-inspection-demo-001
  base_handoff.handoff_id: proofrail-silver-acceptance-handoff-demo-001
  handoff_summary.decision_status: accepted
  handoff_summary.recommended_handoff_posture: silver_handoff_complete_review_required_before_reuse
  gold_gap_inventory.gold_boundary_status: gold_not_claimed
  gold_gap_inventory.counts: present=1 partial=4 unmet=6 out_of_scope=2
```

The verifier:

1. Validates manifest shape and 3-subject layout.
2. Recomputes SHA-256 for each subject and compares to the recorded
   value.
3. Subprocess-invokes the unchanged v0.3.0 handoff verifier on
   subject [0] (failure surfaces as `nested_handoff_invalid`).
4. Re-validates the requirement set bound at subject [1]
   (requirement_set_invalid / requirement_duplicate /
   requirement_domain_missing / inspection_gold_overclaim).
5. Independently re-derives every field of the inspection report and
   rejects any disagreement under one of the 20 stable failure
   reasons.

## 4. Inspect the inspection report

```bash
cat /tmp/proofrail-silver-handoff-inspection-v0.3.1/silver-handoff-inspection-report.json
```

Notable fields:

```
base_handoff.handoff_manifest_sha256
  == manifest subject[0] sha256
  == nested v0.3.0 handoff manifest sha256 (re-verified)

handoff_summary.recommended_handoff_posture
  == nested v0.3.0 handoff summary handoff_result.recommended_handoff_posture
  (rank monotonically >= nested v0.2.9 drill rank)

gold_gap_inventory.requirements_sha256
  == manifest subject[1] sha256

gold_gap_inventory.gold_boundary_status
  == "gold_not_claimed"  (forced whenever any row is partial / unmet
                          / out_of_scope)

gold_gap_inventory.counts
  == {present: 1, partial: 4, unmet: 6, out_of_scope: 2}
```

## 5. Run the regression test

```bash
bash tests/test_silver_handoff_inspector_v0_3_1.sh
```

The regression test exercises every stable failure reason in the
v0.3.1 verifier plus the runner-only refusal codes
(`handoff_validation_failed`, `requirement_set_validation_failed`,
`inspection_self_validation_failed`).

## 6. What this demo does NOT do

- It does **not** assert Gold readiness, Gold certification, regulator
  approval, auditor approval, legal acceptance, or production
  authorization.
- It does **not** adjudicate any challenge or revocation signal in
  the chain.
- It does **not** transfer reliance to any downstream party.
- It does **not** extend the substance of what the v0.2.7 / v0.2.8 /
  v0.2.9 / v0.3.0 evidence asserts.
- It does **not** consult an external compliance standard; the bound
  Gold-boundary requirement set is a local ProofRail demo inventory.
