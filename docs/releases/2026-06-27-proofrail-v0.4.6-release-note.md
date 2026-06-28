# ProofRail v0.4.6 — Gold Local Minimal Profile

ProofRail v0.4.6 adds a Gold Local Minimal Profile over the v0.4.0..v0.4.5 Gold artifact surface. It is a narrow incremental Gold release that adds a single profile descriptor (`profile_name = gold.local.minimal`, `profile_version = v0.1.0`) plus a single validator-only tool that performs a closed five-check structural conformance scan of the existing v0.4.0..v0.4.5 Gold artifact surface in this repository (15 schemas, 12 build/verify tools, 6 regression harnesses, 7 long-form docs, 6 demo READMEs, 7 inherited Makefile targets). v0.4.6 ships no runner, no wrapping manifest, no subject body, no JSON certificate, no signed assertion, and no portable artifact whatsoever; the conformance scan is the artifact. v0.4.6 introduces no new Gold tier, is not signed, is not federated, is not a registry, is not a federation handle, does not transfer reliance, and does not extend the substance of any inherited release. Local profile conformance does not equal institutional assurance. The v0.4.0..v0.4.5 annotated tags are preserved unchanged.

## What v0.4.6 Adds

v0.4.6 ships a single profile descriptor plus a single validator-only tool, and authors no wrapping manifest, no subject body, no JSON certificate, no signed assertion, and no portable artifact whatsoever:

- profile descriptor — `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md`, conformant to the v0.4.6-owned schema;
- schema — `schemas/gold-local-minimal-profile-v0.1.0.md`, declaring the descriptor section layout (9 fixed-order level-2 sections), the closed 46-path required-artifact set, the closed 7-target required-target set, the closed 8-phrase required-non-claim set, the per-token v0.4.6-owned reason taxonomy, and the validator CLI / exit-code specification;
- validator — `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py`, validator-only with CLI `[--repo-root <path>] [--make-binary <path>] [--skip-make]`;
- regression harness — `tests/test_gold_local_minimal_profile_v0_4_6.sh`, 15 numbered exercises;
- long-form doc — `docs/gold/gold-local-minimal-profile-v0.4.6.md`;
- demo pointer README — `demos/gold-demo-007-local-minimal-profile/README.md`, no `make run-*` target, no `/tmp/...` materialization;
- Makefile integration — `verify-gold-local-minimal-profile-v0-4-6` target plus one chaining line in `verify-gold-all`.

The v0.4.6 validator reads only repository files under `--repo-root` (default CWD) and emits exactly one closed-vocabulary text result on stdout/stderr plus a structural exit code. The validator performs a required-artifact existence scan over the 46-path closed set, a required-Makefile-target `.PHONY:` scan over the 7-target closed set, an exact-phrase non-claim scan over the descriptor's eight required non-claim assertions, a descriptor self-integrity scan against the fixed nine-section level-2 layout (presence, order, no duplicates, and enumeration parity with the schema's closed sets for required artifacts and required targets), and (under `--skip-make`-skippable subprocess sweep) `make`-invokes each of the six inherited per-release `verify-gold-*-v0-4-X` targets one at a time. Recognized inherited `FAIL: <R01..R61>:` lines are relayed byte-identically with no v0.4.6 wrapper; non-recognizable nonzero inherited exits surface under the single v0.4.6-owned reason for failed inherited execution.

## Reason Surface

v0.4.6 **preserves the inherited verifier reasons R01..R61** verbatim via subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` targets (24 from v0.4.0, 5 from v0.4.1, 9 from v0.4.2, 10 from v0.4.3 under the corrected v0.4.3.1 baseline, 6 from v0.4.4, and 7 from v0.4.5). v0.4.6 **adds 5 v0.4.6-owned reasons** over the validator's own structural checks (required-artifact existence, required-Makefile-target `.PHONY:` presence, failed inherited execution, required-non-claim exact-phrase presence, descriptor self-integrity). The closed verifier reason surface for v0.4.6 is therefore **66 = 61 inherited + 5 v0.4.6-owned**. Literal v0.4.6-owned reason token names are intentionally not enumerated in this release note; see `docs/gold/gold-local-minimal-profile-v0.4.6.md` and `schemas/gold-local-minimal-profile-v0.1.0.md` for the per-token surface.

v0.4.6 ships **no runner**, so the five v0.4.0 runner-only refusal tokens (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`) are not part of the v0.4.6 reason surface.

A non-reason-shaped `INFRA: <one-line message>` channel on stderr followed by exit code 3 is reserved for environmental failures of the v0.4.6 validator's subprocess invocation of `make` (missing executable, OSError) and for cases where the descriptor itself cannot be opened or decoded as UTF-8; `INFRA:` is not in the closed reason set and not in any TG1 allowlist or DENY pattern. Structurally distinct from exit 1 (verifier reason) so downstream automation can route environmental and content failures separately.

## Locked Check Order

The v0.4.6 validator performs its five-check structural scan in a locked order: required-artifact scan → required-Makefile-target scan → required-non-claim scan → descriptor self-integrity scan → inherited-verifier subprocess sweep. The descriptor-shape check follows the cheaper file-and-target scans so that inherited surface gaps surface in the cheapest stage that can detect them. The inherited subprocess sweep is the final stage and is skippable under `--skip-make`. Single-FAIL discipline: the validator stops at the first failing check.

## Subprocess Delegation

The inherited-verifier sweep iterates a closed six-target execution set covering each of the per-release `verify-gold-*-v0-4-X` targets for v0.4.0..v0.4.5. `verify-gold-all` is intentionally **excluded** from the v0.4.6 execution-target set (it remains in the required-target set under the `.PHONY:` presence scan) to prevent Phase 4 recursion through `$(MAKE) verify-gold-local-minimal-profile-v0-4-6` back into the validator. The Phase 3 regression harness empirically confirms (audit01) that the validator never invokes `verify-gold-all`.

## Validator-Only Release Shape

v0.4.6 ships no runner, no `--input-package`, no `--matrix-input`, no `--lifecycle-input`, no `--output-dir`, no `--force`, no `--self-validate`, no wrapping manifest, no subject body, no JSON certificate, no signed assertion, and no portable artifact whatsoever. The descriptor at `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` and the schema at `schemas/gold-local-minimal-profile-v0.1.0.md` are the entire v0.4.6-authored declarative surface. The validator writes no file under the repo or under `/tmp/`; the regression harness's audit02 exercise empirically confirms this by repo-wide sha256 manifest comparison before and after a `--skip-make` run.

## Regression Harness

v0.4.6 ships a **15-exercise regression harness** at `tests/test_gold_local_minimal_profile_v0_4_6.sh`. The harness reports `ALL 15/15 PASS` with top-level exit 0 and covers:

- pp1 validator py_compile;
- pp2 live repo with `--skip-make`;
- pp3 live repo with full `make` subprocess sweep;
- r62..r66 — one canonical case per v0.4.6-owned reason in the locked-order sequence (five cases total);
- inh01 inherited verbatim-relay through a stub `make` emitting a recognized inherited `FAIL:` line; v0.4.6 stderr is byte-identical to the inherited line and contains no v0.4.6-owned token;
- env01 INFRA exit 3 on invalid `--make-binary` path, non-destructive;
- audit01 validator stderr/stdout scan empirically confirms `verify-gold-all` is never invoked;
- audit02 repo-wide sha256 manifest before/after a `--skip-make` run confirms zero file writes under the repo and zero file writes under `/tmp/proofrail-v046-*`;
- no_residue no stray `/tmp/proofrail-v046-test.*` scratch directory survives the harness's EXIT-trap cleanup;
- tg01 closed-vocabulary token-count gate over the v0.4.6-owned surface using a Python negative-lookahead boundary scan that excludes the validator's own filename fragment;
- ss01 scoped byte-identical sha256 snapshot over the v0.4.6-owned tracked surface (schema + descriptor + validator) before and after the harness run; the harness file itself is intentionally excluded from the snapshot.

## TG1 Discipline

v0.4.6's TG1 is a strict numeric count gate. The harness sweeps the v0.4.6 validator source for `gold_local_minimal_profile_<suffix>` token occurrences using a Python negative-lookahead boundary regex (`(?![a-z0-9_])`) and asserts the appearance set is exactly five tokens corresponding to the five v0.4.6-owned reasons. The validator's `prog="verify_gold_local_minimal_profile_v0_1_0.py"` filename fragment ends with a digit and is excluded by the boundary lookahead. Any additional `gold_local_minimal_profile_*` token would be a v0.4.6-owned reason drift and fail TG1.

## v0.4.0..v0.4.5 Tag Preservation

The v0.4.0, v0.4.1, v0.4.2, v0.4.3, v0.4.3.1, v0.4.4, and v0.4.5 annotated tags are **preserved unchanged**. v0.4.6 is a forward-only incremental Gold release on `main`. Any consumer of those tags may continue to fetch their exact bytes; v0.4.6 is the new incremental baseline going forward.

## Verification

Reported verification for the v0.4.6 finalization:

- `python3 -m py_compile tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` passed;
- `make verify-gold-local-minimal-profile-v0-4-6` passed on two consecutive invocations (idempotency proven; validator-only, writes no file);
- `make verify-gold-all` passed (4 inherited tiers v0.4.0..v0.4.3 + v0.4.4 + v0.4.5 + v0.4.6 at 15/15);
- `bash tests/test_gold_local_minimal_profile_v0_4_6.sh` passed, `ALL 15/15 PASS`;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- `git diff --check` clean.

## Boundary

v0.4.6 adds a deterministic local validator-only structural conformance surface over the already-published v0.4.0..v0.4.5 Gold artifact surface. It is:

- not a registry;
- not a certificate;
- not a federation layer;
- not signed;
- not a federation handle;
- not a transfer of reliance to any external party;
- not a policy engine, GRC platform, gateway, SIEM, observability backend, certification authority, regulator, lifecycle adjudication authority, or production authorization system;
- does not consult any live service;
- does not re-derive, summarize, or modify any inherited schema, body, manifest, or subject;
- does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, the v0.4.3 lifecycle pair, the v0.4.4 reliance-package index, or the v0.4.5 multi-case reliance demo;
- does not write any file under the repo or under `/tmp/`;
- ships no portable artifact whatsoever (no JSON certificate, no signed assertion, no runtime materialization);
- not a signed reliance instrument;
- not a signed lifecycle attestation;
- not live lifecycle adjudication;
- not full Gold;
- not Platinum;
- does not represent runtime truth.

Local profile conformance does not equal institutional assurance. Full Gold and Platinum remain conceptual future tiers.

## Why This Matters

v0.4.0..v0.4.5 ship six Gold artifact surfaces (governed-reliance package, decision report, policy-evaluation matrix and report, challenge lifecycle records and report, reliance-package index, multi-case reliance demo) across 15 schemas, 12 build/verify tools, 6 regression harnesses, 7 long-form docs, and 6 demo READMEs. v0.4.6 declares that surface as a closed local minimal profile and ships a single validator-only tool that empirically scans the live repository for the profile's structural conformance under a locked five-check order, relaying the inherited 61-reason verifier surface (R01..R61) verbatim through subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` targets. The 15-exercise regression harness exercises every v0.4.6-owned reason under the locked check order, the inherited verbatim-relay path, the INFRA boundary, the no-builder / no-certificate rule, the no-file-writes rule, and the TG1 numeric-count gate. v0.4.0..v0.4.5 tags remain bit-identical to their published bytes. Local profile conformance does not equal institutional assurance.
