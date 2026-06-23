# Silver Demo 011 — Walkthrough (v0.3.4 Challenge / Withdrawal Primitives)

This walkthrough shows the exact steps the v0.3.4 runner and verifier
perform on the deterministic local fixtures.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.4).
- A working copy of ProofRail at v0.3.4 (HEAD includes
  `tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py`
  and
  `tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py`,
  plus the unchanged v0.3.0 acceptance handoff runner and verifier).
- A built v0.3.0 acceptance handoff package at
  `/tmp/proofrail-silver-acceptance-handoff-v0.3.0/`. Run
  `make run-silver-acceptance-handoff-v0-3-0` first.

## Step 1 — Build the challenge / withdrawal primitives package

```bash
python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py \
  --target-handoff-root /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
  --challenge-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json \
  --withdrawal-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json \
  --generated-at 2026-06-29T00:30:00Z \
  --output-dir /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-challenge-withdrawal-primitives-v0-3-4
```

Expected final stdout line:

```
PASS: silver challenge/withdrawal primitives package built at /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4
  manifest_id: proofrail-silver-challenge-withdrawal-manifest-demo-001
  summary_id: proofrail-silver-challenge-withdrawal-summary-demo-001
  target.target_record_id: <handoff_id from v0.3.0 manifest>
  summary.posture: challenged_with_local_reuse_paused_for_review
```

The runner performs these steps in this order:

1. Subprocess-invoke the unchanged v0.3.0 acceptance handoff verifier
   against
   `<target-handoff-root>/silver-acceptance-handoff-manifest.json`
   (runner-only reason `handoff_validation_failed`).
2. Structurally validate the input challenge record under the v0.3.4
   closed enum vocabulary (runner-only reason
   `challenge_record_validation_failed`); accept the literal
   placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in
   `target.target_manifest_sha256`.
3. Structurally validate the input withdrawal record under the v0.3.4
   closed enum vocabulary (runner-only reason
   `withdrawal_record_validation_failed`); same placeholder rule.
4. Perform four binding cross-checks against the parsed v0.3.0
   handoff manifest (runner-only reason
   `challenge_withdrawal_binding_failed`):
   - both records' `target.target_record_id` equal the v0.3.0
     handoff manifest's `handoff_id`;
   - withdrawal's `related_challenge_record_id` equals challenge's
     `challenge_record_id`;
   - the time-order chain is monotone;
   - both records' `target.target_manifest_path` equal
     `target-handoff/silver-acceptance-handoff-manifest.json`.
5. Stage the package directory under `<output-dir>.staging.<pid>`.
6. Byte-copy the v0.3.0 handoff package root into `target-handoff/`.
7. Recompute SHA-256 of the copied target handoff manifest and
   rewrite the literal placeholder
   `sha256:TO_BE_BOUND_BY_RUNNER` in both packaged record copies
   under `records/` to that recomputed hash label.
8. Derive `silver-challenge-withdrawal-summary.json` deterministically
   from the copied target manifest, the bound challenge record, and
   the bound withdrawal record; pre-bake the seven required claims
   with `status: pass`; force the posture from the
   `withdrawal_effect → posture` mapping table.
9. Build `silver-challenge-withdrawal-manifest.json` with four
   subjects in fixed order.
10. If `--self-validate`, subprocess-invoke the v0.3.4 verifier
    against the staged manifest BEFORE the atomic publish
    (runner-only reason `challenge_withdrawal_self_validation_failed`).
11. Atomic publish: only AFTER staging build and (optional)
    self-validation succeed does the runner remove an existing
    `--output-dir` (required `--force`) and `os.replace()` the
    staging directory into place. Any earlier failure leaves staging
    cleaned up and `--output-dir` untouched.

## Step 2 — Verify the challenge / withdrawal primitives package

```bash
python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py \
  --manifest /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-manifest.json
```

Expected output:

```
PASS: Silver challenge/withdrawal primitives valid (proofrail-silver-challenge-withdrawal-manifest-demo-001)
```

The verifier performs the following ordered checks. Each check maps
to a specific stable failure reason; OR-accepting adjacent reasons
is disallowed.

| #  | Check                                                                                            | Failure reason on disagreement                              |
|----|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| 1  | Parse manifest JSON                                                                              | `invalid_challenge_withdrawal_manifest`                     |
| 2  | Manifest top-level shape                                                                         | `invalid_challenge_withdrawal_manifest`                     |
| 3  | Subjects array shape (exactly 4 entries)                                                         | `invalid_challenge_withdrawal_manifest`                     |
| 4  | Each subject is an object with non-empty `path`                                                  | `invalid_challenge_withdrawal_manifest`                     |
| 5  | Subject path traversal (BEFORE exact path equality)                                              | `challenge_withdrawal_subject_path_traversal`               |
| 6  | Exact subject path + role equality against `SUBJECT_ORDER`                                       | `invalid_challenge_withdrawal_manifest`                     |
| 7  | Each subject `sha256` / `size_bytes` shape                                                       | `invalid_challenge_withdrawal_manifest`                     |
| 8  | Each subject file exists                                                                         | `challenge_withdrawal_subject_file_missing`                 |
| 9  | Recompute SHA-256 + size for each subject                                                        | `challenge_withdrawal_subject_hash_mismatch` (size mismatch folds to `invalid_challenge_withdrawal_manifest`) |
| 10 | Subprocess-invoke unchanged v0.3.0 handoff verifier on subject [0]                               | `nested_handoff_invalid`                                    |
| 11 | Parse target handoff manifest for `handoff_id` / `generated_at`                                  | `nested_handoff_invalid`                                    |
| 12 | Parse and structurally validate (presence-only) the packaged challenge record                    | `challenge_record_invalid`                                  |
| 13 | Parse and structurally validate (presence-only) the packaged withdrawal record                   | `withdrawal_record_invalid`                                 |
| 14 | Closed-enum check on `challenge.challenge_reason`                                                | `challenge_record_reason_invalid`                           |
| 15 | Closed-enum check on `challenge.challenge_status`                                                | `challenge_record_status_invalid`                           |
| 16 | Challenge record `evidence_refs` validation                                                      | `challenge_record_evidence_ref_invalid`                     |
| 17 | Closed-enum check on `withdrawal.withdrawal_reason`                                              | `withdrawal_record_reason_invalid`                          |
| 18 | Closed-enum check on `withdrawal.withdrawal_status`                                              | `withdrawal_record_status_invalid`                          |
| 19 | Withdrawal record `evidence_refs` validation                                                     | `withdrawal_record_evidence_ref_invalid`                    |
| 20 | Packaged challenge record target binding (placeholder / sha256 / record_id chained)              | `challenge_record_target_mismatch`                          |
| 21 | Packaged withdrawal record target binding (placeholder / sha256 / record_id chained)             | `withdrawal_record_target_mismatch`                         |
| 22 | Withdrawal's `related_challenge_record_id` equals challenge's `challenge_record_id`              | `withdrawal_record_challenge_ref_mismatch`                  |
| 23 | Monotone time-order chain across target / challenge / withdrawal                                 | `challenge_withdrawal_time_order_invalid`                   |
| 24 | Parse + structurally validate the summary, incl. required-claims list                            | `challenge_withdrawal_summary_invalid`                      |
| 25 | Summary `target.*` / `records.*` cross-bind AND `challenge_status` / `withdrawal_status` / `withdrawal_effect` echo the bound records | `challenge_withdrawal_summary_binding_mismatch` |
| 26 | `summary.summary.challenge_count == 1` and `withdrawal_count == 1`                               | `challenge_withdrawal_summary_count_mismatch`               |
| 27 | `summary.summary.posture` in closed set AND matches `withdrawal_effect → posture` table          | `challenge_withdrawal_posture_invalid`                      |
| 28 | Overclaim scan OUTSIDE `scope_limitations` / `non_claims` (incl. optional `claim.description`)   | `challenge_withdrawal_overclaim`                            |
| 29 | `scope_limitations` non-empty / non-blank (manifest + summary), then `non_claims` non-empty / non-blank (manifest + summary) | `challenge_withdrawal_limitations_missing`, then `challenge_withdrawal_non_claims_missing` |

24 stable failure reasons across 29 ordered checks (manifest
structural failures throughout steps 1–9 share
`invalid_challenge_withdrawal_manifest`; step 29 covers both
`_limitations_missing` and `_non_claims_missing`). The 5 runner-only
refusal codes (`handoff_validation_failed`,
`challenge_record_validation_failed`,
`withdrawal_record_validation_failed`,
`challenge_withdrawal_binding_failed`,
`challenge_withdrawal_self_validation_failed`) are NEVER emitted by
the verifier.

## Step 3 — Inspect the summary

```bash
python3 -c "import json; d = json.load(open('/tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-summary.json')); print(json.dumps(d['summary'], indent=2))"
```

Expected output:

```json
{
  "challenge_count": 1,
  "challenge_status": "challenge_recorded",
  "posture": "challenged_with_local_reuse_paused_for_review",
  "withdrawal_count": 1,
  "withdrawal_effect": "local_reuse_paused_for_review",
  "withdrawal_status": "withdrawal_recorded"
}
```

## Step 4 — Run the regression test

```bash
make verify-silver-challenge-withdrawal-primitives-v0-3-4
```

This runs `tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh`,
which exercises every stable verifier failure reason (24) and every
runner-only refusal reason (5). The test prints a final stable PASS
line:

```
PASS: silver challenge/withdrawal primitives v0.3.4 regression test
```

## What the demo intentionally does **not** do

- It does not adjudicate the challenge.
- It does not legally revoke reliance.
- It does not certify the target handoff.
- It does not authorize production reuse.
- It does not contact, notify, or consult any regulator, auditor,
  third party, counterparty, or downstream relying party.
- It does not extend the substance of any earlier-release Silver
  evidence.
- It does not verify the substantive truth of free-text reasons or
  counterparty references inside the records.
- It does not bind a v0.3.2 trace binding manifest or a v0.3.3
  adapter pilot manifest into the challenge / withdrawal package.
