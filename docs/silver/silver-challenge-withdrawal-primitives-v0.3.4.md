# Silver Challenge / Withdrawal Record Primitives — v0.3.4

**Status:** Draft / ProofRail v0.3.4
**Release thesis:** ProofRail v0.3.4 introduces two deterministic local
Silver evidence record primitives — a *challenge record* and a
*withdrawal record* — and hash-anchors them to an unchanged v0.3.0
Silver acceptance handoff target inside a single packaged manifest. An
independent Silver reviewer can re-run the unchanged v0.3.0 handoff
verifier, re-derive the summary deterministically, and confirm every
binding cross-check — without claiming that the challenge has been
adjudicated, that reliance has been legally revoked, that the target
handoff has been certified, or that any production reuse has been
authorized.

---

## v0.3.4 thesis

> A reviewer can verify that a Silver acceptance handoff target has
> been hash-bound to a structurally valid Silver challenge record and a
> structurally valid Silver withdrawal record under a closed enum
> vocabulary, that the withdrawal cites the challenge, that the time
> order chain is monotone, and that the derived summary posture is
> consistent with the recorded `withdrawal_effect` — while preserving
> the boundary that v0.3.4 does **not** adjudicate the challenge, does
> **not** legally revoke reliance, does **not** certify the target
> handoff, and does **not** authorize production reliance.

## Challenge / withdrawal primitives boundary

> A v0.3.4 challenge/withdrawal primitives package is **not** an
> adjudication, a legal revocation, a regulator action, a third-party
> audit, a Gold certificate, or an authorization for production reuse.
> It is a deterministic local evidence artifact recording that a
> reviewer has filed a structured challenge and a structured local
> withdrawal posture against a specific, already-verified Silver
> acceptance handoff target, and that every binding between those
> records, the target, and the summary is independently hash-verifiable
> and re-derivable.

v0.3.4 answers:

```
Can a Silver reviewer file a structured local challenge against a
  specific Silver acceptance handoff target?
Can the reviewer record a structured local withdrawal posture that
  cites that challenge?
Can the runner deterministically derive a single summary whose
  posture is implied by the recorded withdrawal_effect?
Can a verifier independently re-run the unchanged v0.3.0 handoff
  verifier on the bound target?
Can the verifier re-derive the summary, re-check every binding
  cross-check, and re-enforce the time-order chain?
Can the verifier reject target binding mismatches (placeholder
  unbound, target hash drift, or target record-id drift, all
  consolidated to a single per-record `*_target_mismatch` reason),
  withdrawal-vs-challenge binding mismatches, time-order violations,
  invalid records, invalid record enum values (reason / status),
  unsafe record evidence refs, summary-binding drift, count drift,
  posture-from-effect drift, invalid summaries (including missing or
  failed required claims), empty limitations / non-claims, and
  overclaims?
```

v0.3.4 does **not** answer:

```
Did the challenge succeed?
Has reliance been legally revoked?
Has a regulator, auditor, or third party reviewed the target?
Is the target handoff certified?
Is the target Gold-conformant?
Is the target ready for production reuse?
Has any downstream party accepted, transferred, or relied upon this
  evidence?
```

---

## Schemas

Four new v0.1.0 schemas ship with v0.3.4:

```
schemas/silver-challenge-record-v0.1.0.md
schemas/silver-withdrawal-record-v0.1.0.md
schemas/silver-challenge-withdrawal-summary-v0.1.0.md
schemas/silver-challenge-withdrawal-manifest-v0.1.0.md
```

### Challenge record (`proofrail.silver.challenge_record`)

A structured local record stating that a reviewer has challenged a
specific Silver acceptance handoff target. Required top-level fields:

```
document_type, schema_version, proofrail_release,
challenge_record_id, filed_at, filed_by, target,
challenge, evidence_refs, scope_limitations, non_claims
```

`challenge.challenge_reason` closed enum (10):

```
disputed_finding
disputed_recommended_posture
disputed_evidence_hash
disputed_evidence_scope
disputed_acceptance_record
disputed_decision_status
new_evidence_available
out_of_scope_for_demo
withdrawal_signal_observed
other_local_review_signal
```

`challenge.challenge_status` closed enum (4):

```
challenge_recorded
challenge_open_for_review
challenge_under_local_review
challenge_withdrawn_by_filer
```

### Withdrawal record (`proofrail.silver.withdrawal_record`)

A structured local record stating that a reviewer has withdrawn local
reuse / local reliance posture for a specific Silver acceptance
handoff target, optionally citing a related challenge record by id.
Required top-level fields:

```
document_type, schema_version, proofrail_release,
withdrawal_record_id, recorded_at, effective_at, recorded_by,
target, related_challenge_record_id, withdrawal,
evidence_refs, scope_limitations, non_claims
```

`withdrawal.withdrawal_reason` closed enum (7):

```
challenge_pending_review
disputed_evidence
local_policy_signal
out_of_scope_signal
record_superseded
filer_voluntary_withdrawal
other_local_review_signal
```

`withdrawal.withdrawal_status` closed enum (4):

```
withdrawal_recorded
withdrawal_pending_local_review
withdrawal_completed_for_local_scope
withdrawal_rescinded_by_filer
```

`withdrawal.withdrawal_effect` closed enum (4):

```
local_reuse_paused_for_review
local_reliance_withdrawn_for_review
acceptance_reuse_blocked_pending_review
record_superseded
```

The verifier enforces the monotone time-order chain
`target.generated_at ≤ challenge.filed_at ≤ withdrawal.recorded_at ≤
withdrawal.effective_at`.

### Challenge / withdrawal summary (`proofrail.silver.challenge_withdrawal_summary`)

Derived deterministically by the runner from the copied target
handoff manifest, the bound challenge record, and the bound
withdrawal record. Required fields:

```
summary_id, generated_at,
target { target_type, target_manifest_path, target_manifest_sha256 },
records { challenge_record_path, challenge_record_sha256,
          withdrawal_record_path, withdrawal_record_sha256 },
summary { challenge_count, withdrawal_count,
          challenge_status, withdrawal_status,
          withdrawal_effect, posture },
claims [...],
scope_limitations [...], non_claims [...]
```

`summary.posture` closed set (5 values):

```
challenge_recorded
challenged_with_local_reuse_paused_for_review
challenged_with_local_reliance_withdrawn_for_review
withdrawal_recorded_without_adjudication
record_superseded
```

Posture is derived deterministically from `withdrawal_effect`:

| `withdrawal_effect` | Derived `posture` |
|---|---|
| `local_reuse_paused_for_review` | `challenged_with_local_reuse_paused_for_review` |
| `local_reliance_withdrawn_for_review` | `challenged_with_local_reliance_withdrawn_for_review` |
| `acceptance_reuse_blocked_pending_review` | `challenged_with_local_reuse_paused_for_review` |
| `record_superseded` | `record_superseded` |

The seven required claim IDs (each `status: pass`, each with at least
one safe package-local `evidence_refs` entry):

```
target_handoff_verified
challenge_record_valid
withdrawal_record_valid
challenge_and_withdrawal_target_same_handoff
withdrawal_cites_challenge
time_order_valid
no_adjudication_claimed
```

Each claim may carry an optional `description` string, which the
overclaim guard scans like any other free-text field outside
`scope_limitations` and `non_claims`.

### Challenge / withdrawal manifest (`proofrail.silver.challenge_withdrawal_manifest`)

Fixed 4-subject SHA-256 anchor in deterministic order:

```
[0] target-handoff/silver-acceptance-handoff-manifest.json
                                       role: target_handoff_manifest
[1] records/challenge-record.json      role: challenge_record
[2] records/withdrawal-record.json     role: withdrawal_record
[3] silver-challenge-withdrawal-summary.json
                                       role: challenge_withdrawal_summary
```

Subject paths are rejected if absolute or if they contain `..` BEFORE
exact path equality.

---

## Package layout

```
<output-dir>/
├── target-handoff/                                 (byte-copy of v0.3.0 package)
│   ├── composed-gateway-evidence/...
│   ├── acceptance-package/...
│   ├── revocation-challenge-drill/...
│   ├── silver-acceptance-handoff-summary.json
│   └── silver-acceptance-handoff-manifest.json     (subject [0])
├── records/
│   ├── challenge-record.json                       (subject [1])
│   └── withdrawal-record.json                      (subject [2])
├── silver-challenge-withdrawal-summary.json        (subject [3])
└── silver-challenge-withdrawal-manifest.json
```

The packaged `records/challenge-record.json` and
`records/withdrawal-record.json` are post-bind: any literal
`sha256:TO_BE_BOUND_BY_RUNNER` placeholder present in the INPUT
fixtures has been rewritten by the runner to the recomputed
subject [0] SHA-256 label. The verifier rejects any packaged record
that still carries the placeholder.

---

## Runner usage

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

Runner exit codes:

```
0 — success
1 — package refused or self-validation failed
2 — usage or input-file error
```

Runner-only refusal reasons (5):

```
handoff_validation_failed
challenge_record_validation_failed
withdrawal_record_validation_failed
challenge_withdrawal_binding_failed
challenge_withdrawal_self_validation_failed
```

### Atomic publish (`--force` + `--self-validate`)

The runner stages the entire package under
`<output-dir>.staging.<pid>`. Only AFTER staging build and (if
`--self-validate` is supplied) self-validation both succeed does the
runner:

1. Refuse if `<output-dir>` already exists and `--force` was not supplied.
2. If `<output-dir>` exists and `--force` was supplied, remove it.
3. `os.replace()` the staging directory into `<output-dir>`.

Any earlier failure cleans up the staging directory and leaves
`<output-dir>` untouched. A failed run leaves no final directory and
no staging sibling. The Make target is therefore safely repeatable.

---

## Verifier usage

```bash
python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py \
  --manifest /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-manifest.json
```

Verifier exit codes:

```
0 — package valid
1 — verification failure (any stable reason below)
2 — usage or input-file error
```

### Stable verifier failure reasons (24)

```
invalid_challenge_withdrawal_manifest
challenge_withdrawal_subject_path_traversal
challenge_withdrawal_subject_file_missing
challenge_withdrawal_subject_hash_mismatch
nested_handoff_invalid
challenge_record_invalid
withdrawal_record_invalid
challenge_record_target_mismatch
withdrawal_record_target_mismatch
challenge_record_reason_invalid
challenge_record_status_invalid
challenge_record_evidence_ref_invalid
withdrawal_record_reason_invalid
withdrawal_record_status_invalid
withdrawal_record_evidence_ref_invalid
withdrawal_record_challenge_ref_mismatch
challenge_withdrawal_time_order_invalid
challenge_withdrawal_summary_invalid
challenge_withdrawal_summary_binding_mismatch
challenge_withdrawal_summary_count_mismatch
challenge_withdrawal_posture_invalid
challenge_withdrawal_overclaim
challenge_withdrawal_limitations_missing
challenge_withdrawal_non_claims_missing
```

The 5 runner-only refusal codes are NEVER emitted by the verifier.

### Reachability ordering

Four reachability constraints make every stable reason directly
attributable:

- **Path traversal BEFORE exact subject-path equality.** Subjects with
  absolute paths or `..` segments are attributed to
  `challenge_withdrawal_subject_path_traversal`, never collapsed into
  `invalid_challenge_withdrawal_manifest`.
- **Structural parse BEFORE enum / evidence_ref / target checks.** The
  presence-only structural record validators (`challenge_record_invalid`
  / `withdrawal_record_invalid`) check shape only. The dedicated
  `*_reason_invalid`, `*_status_invalid`, `*_evidence_ref_invalid`, and
  `*_target_mismatch` checks are later, independently reachable steps,
  so enum, evidence-ref, or target failures are never collapsed into
  the generic `*_record_invalid` reason.
- **Target mismatch is one consolidated reason per record.** The
  per-record `*_target_mismatch` check chains placeholder-unbound →
  target manifest sha256 drift → target record id drift, all emitting
  the single consolidated reason `challenge_record_target_mismatch` or
  `withdrawal_record_target_mismatch`.
- **Posture-vs-effect, summary-binding, and count drift have
  distinct reasons.** `summary.posture` divergence — either out-of-set
  or off the `withdrawal_effect → posture` mapping table — is
  attributed to `challenge_withdrawal_posture_invalid`. Summary
  echo drift on `challenge_status`, `withdrawal_status`, or
  `withdrawal_effect` against the bound records is attributed to
  `challenge_withdrawal_summary_binding_mismatch`. Re-derived
  count drift is attributed to
  `challenge_withdrawal_summary_count_mismatch` (singular).
  Missing-or-failed required claims are attributed to
  `challenge_withdrawal_summary_invalid` (folded into the summary
  structural reason).

Limitations and non-claims emptiness checks are reserved for the
dedicated reasons `challenge_withdrawal_limitations_missing` and
`challenge_withdrawal_non_claims_missing`; early structural checks
verify presence/type only.

The overclaim scan runs OUTSIDE the `scope_limitations` /
`non_claims` arrays and includes optional `claims[].description`
strings, so disclaimer text containing forbidden phrases inside the
limitations / non-claims arrays does not trigger
`challenge_withdrawal_overclaim`.

---

## Regression coverage

`tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh` runs
**36 numbered exercises** plus a scoped sha256 snapshot:

- 4 positive (build with `--self-validate`, independent verifier,
  inline manifest layout, inline summary contents)
- 25 verifier-mutation cases (one per ordered check, covering 24
  stable reasons; the two path-traversal cases — `..` and absolute —
  both map to `challenge_withdrawal_subject_path_traversal`)
- 5 runner-only refusal cases
- 1 taxonomy gate exercise (scans 13 v0.3.4-owned files plus 2
  sections of `tools/silver/README.md` for reason-like tokens and
  rejects any token outside the approved verifier / runner
  allowlists)
- 1 scoped sha256 snapshot of the nine committed v0.3.4 source paths

The final PASS line states:

```
PASS: silver challenge/withdrawal primitives v0.3.4 regression test
```

No reason is OR-accepted; each negative case asserts the exact stable
reason expected.

---

## Non-claims

- v0.3.4 ships local hash-anchored evidence record primitives. It
  does not adjudicate, decide, dispute-resolve, regulator-review,
  audit, or legally process the recorded challenge.
- v0.3.4 does not legally revoke reliance. The `withdrawal_effect`
  enum describes the filer's local posture only.
- v0.3.4 does not certify the target handoff. It re-runs the
  unchanged v0.3.0 handoff verifier as a binding check; the target
  handoff retains its v0.3.0 boundary.
- v0.3.4 is not a Gold certificate, regulator approval, auditor
  approval, legal acceptance, compliance certification, production
  authorization, or transfer of reliance.
- v0.3.4 is unsigned: it ships local hash anchors only.
- v0.3.4 does not extend the substance of any earlier-release Silver
  evidence.
- The `challenge_record` and `withdrawal_record` are independently
  authored local statements; v0.3.4 does not verify the truth of any
  free-text reason or counterparty assertion within them.

---

## Relationship to earlier and later releases

| Release | Relationship                                                                |
|---------|-----------------------------------------------------------------------------|
| v0.2.7 / v0.2.8 / v0.2.9 | v0.3.4 does not modify composed gateway evidence, relying-party acceptance record, or revocation/challenge drill semantics. v0.3.4 binds at the v0.3.0 acceptance handoff layer above them. |
| v0.3.0  | v0.3.4 re-invokes the unmodified v0.3.0 handoff verifier as a binding check on subject [0] (`target-handoff/silver-acceptance-handoff-manifest.json`). v0.3.0 semantics are unchanged. |
| v0.3.1  | v0.3.4 does not modify inspection semantics. The handoff inspector does not (yet) ingest v0.3.4 records. |
| v0.3.2 / v0.3.3 | v0.3.4 does not modify trace binding or adapter pilot semantics. v0.3.4 does not bind directly to a v0.3.2 trace binding manifest or a v0.3.3 adapter pilot manifest. |
| v0.3.5+ | (planned) A relying-party policy pack, control framework crosswalk, registry-lite, and minimal Gold governed-reliance demo all remain out of scope for v0.3.4. |
