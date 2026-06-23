# Silver Demo 011 — Challenge / Withdrawal Record Primitives (v0.3.4)

This demo is the deterministic, local Silver challenge / withdrawal
primitives package that ProofRail v0.3.4 derives from:

- the unchanged v0.3.0 Silver acceptance handoff package emitted by
  `make run-silver-acceptance-handoff-v0-3-0`
  (`/tmp/proofrail-silver-acceptance-handoff-v0.3.0/` by default);
- the v0.3.4 challenge record fixture
  (`fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json`);
- the v0.3.4 withdrawal record fixture
  (`fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json`).

It answers a narrow question:

> Can a Silver acceptance handoff target be hash-bound to a
> structurally valid challenge record and a structurally valid
> withdrawal record under a closed enum vocabulary, such that an
> independent Silver reviewer can re-run the unchanged v0.3.0 handoff
> verifier, re-derive the summary deterministically, and re-check
> every binding cross-check — without claiming that the challenge has
> been adjudicated, that reliance has been legally revoked, that the
> target handoff has been certified, or that production reuse has
> been authorized?

It does **not** answer:

- Did the challenge succeed?
- Has reliance been legally revoked?
- Has a regulator, auditor, or third party reviewed the target?
- Is the target handoff certified?
- Is the target Gold-conformant?
- Is the target ready for production reuse?
- Has any downstream party accepted, transferred, or relied upon
  this evidence?

## What the demo does

1. Subprocess-invokes the unchanged v0.3.0 acceptance handoff
   verifier against the target handoff manifest at
   `<target-handoff-root>/silver-acceptance-handoff-manifest.json`.
   Any v0.3.0 failure is refused at the runner with
   `FAIL: handoff_validation_failed: <detail>` and exit 1; no partial
   v0.3.4 package is written.
2. Structurally validates the input challenge record under the v0.3.4
   closed enum vocabulary (10 reasons, 4 statuses). The structural
   validator accepts the literal placeholder
   `sha256:TO_BE_BOUND_BY_RUNNER` as a syntactically valid
   `target.target_manifest_sha256` value so input fixtures can be
   authored independently of the target hash.
3. Structurally validates the input withdrawal record under the
   v0.3.4 closed enum vocabulary (7 reasons, 4 statuses, 4 effects)
   and the same placeholder rule.
4. Performs four runner-only binding cross-checks against the parsed
   v0.3.0 handoff manifest:
   - both records' `target.target_record_id` equal the v0.3.0
     handoff manifest's `handoff_id`;
   - the withdrawal record's `related_challenge_record_id` equals
     the input challenge record's `challenge_record_id`;
   - the time-order chain
     `target.generated_at ≤ challenge.filed_at ≤
     withdrawal.recorded_at ≤ withdrawal.effective_at` is monotone;
   - the input challenge record's `target.target_manifest_path` and
     withdrawal record's `target.target_manifest_path` both equal
     the packaged subject [0] path `target-handoff/silver-acceptance-handoff-manifest.json`.
   Any of those failures is refused at the runner with
   `FAIL: challenge_withdrawal_binding_failed: <detail>` and exit 1.
5. Stages the package under `<output-dir>.staging.<pid>` and
   byte-copies the v0.3.0 handoff package root into
   `target-handoff/`.
6. Recomputes the SHA-256 of the copied target handoff manifest and
   rewrites the literal `sha256:TO_BE_BOUND_BY_RUNNER` placeholder
   in both record copies under `records/` to that recomputed hash
   label. The packaged records carry the bound hash; the input
   fixtures may carry the placeholder.
7. Derives `silver-challenge-withdrawal-summary.json` deterministically
   from the copied target manifest, the bound challenge record, and
   the bound withdrawal record. The `summary.posture` field is
   derived from `withdrawal_effect` via the closed mapping table;
   the seven required claims are pre-baked with `status: pass` and
   safe package-local `evidence_refs`.
8. Emits `silver-challenge-withdrawal-manifest.json` with exactly
   four subjects in fixed order: target handoff manifest / challenge
   record / withdrawal record / challenge-withdrawal summary.
9. If `--self-validate`, subprocess-invokes the v0.3.4 verifier
   against the staged manifest BEFORE the atomic publish. Any
   verifier failure is reported as `FAIL:
   challenge_withdrawal_self_validation_failed: <detail>` and exit 1;
   the staging directory is removed and `<output-dir>` is left
   untouched.
10. Atomic publish: only AFTER a successful staging build (and, if
    `--self-validate`, a successful self-validation) does the runner
    remove an existing `--output-dir` (required `--force`) and
    `os.replace()` the staging directory into place.

## Commands

```bash
make run-silver-acceptance-handoff-v0-3-0
make run-silver-challenge-withdrawal-primitives-v0-3-4
make verify-silver-challenge-withdrawal-primitives-v0-3-4
```

The `run-silver-acceptance-handoff-v0-3-0` target produces the v0.3.0
target package that v0.3.4 consumes.

The `run-silver-challenge-withdrawal-primitives-v0-3-4` target builds
the v0.3.4 package into
`/tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/` with
`--force --self-validate`, then runs the v0.3.4 verifier against the
published manifest.

The `verify-silver-challenge-withdrawal-primitives-v0-3-4` target runs
the dedicated regression test, which exercises every stable verifier
failure reason and every runner-only refusal reason.

## Challenge / withdrawal primitives package layout

```
/tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/
├── target-handoff/                                 (byte-copy of v0.3.0 package)
│   ├── composed-gateway-evidence/...
│   ├── acceptance-package/...
│   ├── revocation-challenge-drill/...
│   ├── silver-acceptance-handoff-summary.json
│   └── silver-acceptance-handoff-manifest.json     (subject [0])
├── records/
│   ├── challenge-record.json                       (subject [1], post-bind)
│   └── withdrawal-record.json                      (subject [2], post-bind)
├── silver-challenge-withdrawal-summary.json        (subject [3])
└── silver-challenge-withdrawal-manifest.json       (4-subject anchor)
```

## Demo timestamps

The committed fixture timestamps yield the monotone chain enforced by
the verifier:

```
target.generated_at      2026-06-28T00:00:00Z      (v0.3.0 handoff)
challenge.filed_at       2026-06-29T00:10:00Z
withdrawal.recorded_at   2026-06-29T00:20:00Z
withdrawal.effective_at  2026-06-29T00:20:00Z
summary.generated_at     2026-06-29T00:30:00Z      (passed via --generated-at)
```

## Posture derivation

The committed withdrawal fixture sets `withdrawal_effect =
local_reuse_paused_for_review`, so the derived summary posture is
deterministically `challenged_with_local_reuse_paused_for_review`.

| `withdrawal_effect` | Derived `posture` |
|---|---|
| `local_reuse_paused_for_review` | `challenged_with_local_reuse_paused_for_review` |
| `local_reliance_withdrawn_for_review` | `challenged_with_local_reliance_withdrawn_for_review` |
| `acceptance_reuse_blocked_pending_review` | `challenged_with_local_reuse_paused_for_review` |
| `record_superseded` | `record_superseded` |

## Non-claims

- The challenge / withdrawal primitives package is not an
  adjudication.
- The challenge / withdrawal primitives package does not legally
  revoke reliance.
- The challenge / withdrawal primitives package does not certify the
  target handoff.
- The challenge / withdrawal primitives package is not a Gold
  certificate, regulator approval, auditor approval, legal
  acceptance, compliance certification, production authorization, or
  transfer of reliance.
- The withdrawal record's `withdrawal_effect` describes the filer's
  local posture only; it does not constitute legal revocation of any
  prior acceptance instrument.
- The challenge record's free-text `challenge_reason_description` /
  counterparty references are not verified for substantive truth by
  v0.3.4.
- The v0.3.4 package is unsigned: it ships local hash anchors only.
- v0.3.4 does not extend the substance of any earlier-release Silver
  evidence and does not advance the Gold boundary.
