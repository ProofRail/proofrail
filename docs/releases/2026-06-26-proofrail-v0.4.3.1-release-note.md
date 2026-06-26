# ProofRail v0.4.3.1 — Correct Gold Challenge Lifecycle Fingerprint Verification

ProofRail v0.4.3.1 is a narrow corrective patch release for v0.4.3 — Gold Challenge Lifecycle Lite. It corrects verifier under-enforcement of two fingerprint sub-checks that were declared in the v0.4.3 narrative and schemas but were not re-derived by the shipped v0.4.3 verifier. The v0.4.3 annotated tag is preserved unchanged; v0.4.3.1 is the corrected patch baseline.

## What v0.4.3.1 Fixes

v0.4.3 introduced two fingerprint fields whose values must be byte-re-derivable from the surrounding canonical JSON:

- per-record `lifecycle_fingerprint` on each entry of the runtime records body's `lifecycle_records[]` array (bare lowercase hex SHA-256 over canonical JSON of the record body with the `lifecycle_fingerprint` field removed);
- top-level `report_fingerprint` on the lifecycle report (bare lowercase hex SHA-256 over canonical JSON of the report body with the `report_fingerprint` field removed).

The shipped v0.4.3 verifier validated the presence, grammar, and `^[0-9a-f]{64}$` shape of each fingerprint, but did not recompute the canonical-JSON SHA-256 and did not fail on a value that was well-formed but did not match the surrounding body. A v0.4.3 package whose `lifecycle_fingerprint` or `report_fingerprint` had been mutated to any other well-formed hex string passed v0.4.3 verification.

v0.4.3.1 adds the missing re-derivation:

- mismatched per-record `lifecycle_fingerprint` now fails under existing `gold_challenge_lifecycle_records_binding_invalid` (R41), as a deliberate non-monotonic post-R43 sub-check;
- mismatched top-level `report_fingerprint` now fails under existing `gold_challenge_lifecycle_projection_invalid` (R47), as a deliberate non-monotonic post-R48 sub-check.

Both placements preserve the pre-existing reachability of R42, R43, R47-row-level, and R48 on unmodified-fingerprint inputs.

## Scope

This is a corrective patch. It is **not** a new Gold release:

- no new schema family;
- no new Gold feature;
- no new closed vocabulary;
- no new manifest shape;
- no new runner, demo, or fixture;
- no new release narrative document;
- no taxonomy expansion.

The closed verifier reason surface remains R01..R48 (24 inherited from v0.4.0 via subprocess relay, 5 inherited from v0.4.1 via subprocess relay, 9 inherited from v0.4.2 via subprocess relay, 10 v0.4.3-owned). No 49th reason. No 25th v0.4.0 reason. No sixth v0.4.1 reason. No tenth v0.4.2 reason. No eleventh v0.4.3 reason.

The runner-only refusal surface remains the same five reasons inherited verbatim from v0.4.0: `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`. No sixth runner-only refusal. No sixth wrapper for verifier-relay on `--self-validate`.

## v0.4.3 Tag Preservation

The v0.4.3 annotated tag (`bd780ca…` → commit `7566993…`) is preserved unchanged. v0.4.3.1 is a forward-only corrective patch on `main`. Any consumer of the v0.4.3 tag may continue to fetch the exact bytes of the v0.4.3 release; v0.4.3.1 is the corrected baseline going forward.

## Regression Harness

The v0.4.3 Gold Challenge Lifecycle Lite regression test now reports 101/101, raised from the v0.4.3 historical count of 99/99 by two new ordered cases that exercise the corrective sub-checks:

- `rt4`: a fifth runtime-scalar mutation variant that flips the first hex digit of `lifecycle_records[0].lifecycle_fingerprint` and asserts a `FAIL: gold_challenge_lifecycle_records_binding_invalid` (R41) before invoking the verifier;
- `sup06`: a sixth supplemental case that flips the first hex digit of the top-level `report_fingerprint` and asserts a `FAIL: gold_challenge_lifecycle_projection_invalid` (R47) before invoking the verifier.

Both cases verify that the mutated value differs from the original. The 99/99 reachability surface from the v0.4.3 release is preserved verbatim — no v0.4.3 case is removed, reassigned, or renumbered.

The v0.4.0, v0.4.1, and v0.4.2 regressions are not touched and continue to pass at their respective shipped counts.

## Files Touched

The v0.4.3.1 corrective patch is intentionally narrow. The corrective implementation commit (`bcba56e…`, "Fix v0.4.3 lifecycle fingerprint verification") modifies exactly ten files:

- `tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py` — adds the two non-monotonic fingerprint re-derivation sub-checks under existing R41 and R47;
- `tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh` — adds `rt4` and `sup06`;
- `schemas/gold-challenge-lifecycle-records-v0.1.0.md`, `schemas/gold-challenge-lifecycle-report-v0.1.0.md`, `schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md` — narrow reconciliation of the fingerprint-field semantics with the corrected verifier behavior;
- `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md` — narrow reconciliation of the R41 / R47 reachability notes and 99 / 101 framing;
- `demos/gold-demo-004-challenge-lifecycle-lite/README.md`, `demos/gold-demo-004-challenge-lifecycle-lite/demo-walkthrough.md` — narrow reconciliation of the demo framing and walkthrough numbering;
- `docs/dev/gold-release-index.md` — narrow patch note pointing at v0.4.3.1;
- `tools/gold/README.md` — narrow reconciliation of the v0.4.3 tooling overview.

The v0.4.3.1 finalization commit additionally adds this release note and updates the `Current Status` / `Latest committed release` references in `README.md` and `CLAUDE.md`.

No v0.4.0, v0.4.1, or v0.4.2 tooling, schema, fixture, or test file is modified. No Bronze or Silver file is touched. `docs/dev/silver-release-index.md` is untouched.

## Verification

Reported verification for the v0.4.3.1 patch:

- `make run-gold-challenge-lifecycle-lite-v0-4-3` passed (both `--self-validate` during build and the standalone verifier re-run);
- `make verify-gold-challenge-lifecycle-lite-v0-4-3` passed, 101/101 exercises;
- `make verify-gold-all` passed;
- `make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6` passed;
- `make verify-silver-registry-lite-v0-3-7` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- `git diff --check` clean.

## Boundary

v0.4.3.1 corrects a verifier under-enforcement only. It does not change the Gold boundary, the closed reason surface, the closed lifecycle vocabularies, the manifest shape, the subprocess delegation chain, the runner-only refusal surface, the TG1 allowlist discipline, the test scratch path policy, or the v0.4.3 non-claims. v0.4.3 was, and v0.4.3.1 remains, a deterministic local re-derivation surface over already-published Gold artifacts:

- not signed;
- not a certificate;
- not federated;
- not a transfer of reliance to any external party;
- not a policy engine, GRC platform, gateway, SIEM, observability backend, certification authority, regulator, lifecycle adjudication authority, or production authorization system;
- does not consult any live policy engine or live lifecycle adjudication authority;
- does not perform end-to-end re-verification of the upstream Silver evidence chain;
- does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair;
- not a signed lifecycle attestation;
- not live lifecycle adjudication;
- not full Gold;
- not Platinum;
- does not represent runtime truth.

Full Gold and Platinum remain conceptual future tiers.

## Why This Matters

v0.4.3 said that the per-record `lifecycle_fingerprint` and the top-level `report_fingerprint` were byte-re-derivable from the surrounding canonical JSON. v0.4.3.1 actually re-derives them in the verifier. The corrective patch closes the small but real gap between the v0.4.3 narrative and the v0.4.3 shipped verifier, and brings the regression harness's 99/99 surface forward as 101/101 with two ordered cases that exercise the corrected sub-checks. The taxonomy, the runner-only refusal surface, and the Gold boundary all remain unchanged.
