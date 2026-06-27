# ProofRail v0.4.4 — Gold Reliance Package Index

ProofRail v0.4.4 adds a Gold Reliance Package Index over the v0.4.0..v0.4.3 Gold line. It is a narrow incremental Gold release that wraps the unchanged v0.4.0 Governed Reliance Demo, the v0.4.1 Decision Report Hardening package, the v0.4.2 Policy Evaluation Matrix package, and the v0.4.3 Challenge Lifecycle Lite package (verified under the corrected v0.4.3.1 baseline) under a single 5-subject index manifest plus a single byte-stable v0.4.4-owned index body. v0.4.4 introduces no new Gold tier, is not signed, is not federated, is not a registry, and does not extend the substance of any inherited release. The v0.4.3 and v0.4.3.1 annotated tags are preserved unchanged.

## What v0.4.4 Adds

v0.4.4 ships a single wrapping manifest with 5 fixed-order subjects, plus the v0.4.4-owned index body it anchors:

- subject [0] — v0.4.0 child wrapping package manifest (`gold_governed_reliance_package_manifest`), under `child-packages/v0.4.0/`;
- subject [1] — v0.4.1 child wrapping package manifest (`gold_decision_report_package_manifest`), under `child-packages/v0.4.1/`;
- subject [2] — v0.4.2 child wrapping package manifest (`gold_policy_evaluation_matrix_package_manifest`), under `child-packages/v0.4.2/`;
- subject [3] — v0.4.3 child wrapping package manifest (`gold_challenge_lifecycle_package_manifest`), under `child-packages/v0.4.3/`, **verified under the corrected v0.4.3.1 baseline**;
- subject [4] — the v0.4.4-owned `gold_reliance_package_index` body, at `gold-reliance-package-index.json`.

The v0.4.4 runner subprocess-invokes each of the four co-located inherited runners (v0.4.0, v0.4.1, v0.4.2, v0.4.3) once, into its own `child-packages/v0.4.X/` subdirectory under the v0.4.4 staging tree; the v0.4.3 child closure is built under the corrected v0.4.3.1 baseline. The v0.4.4 runner then derives the index body deterministically from the materialized child wrapping manifests (per-entry `child_manifest_fingerprint` / `child_manifest_size_bytes` / `child_manifest_path` byte-match the wrapping manifest's `subjects[i]`; closed-key `coverage_summary` arithmetic; top-level `index_fingerprint` over canonical JSON of the body excluding the fingerprint field), runs the v0.4.4 verifier under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination.

The v0.4.4 verifier validates the wrapping manifest (Phase 1) and wrapping-manifest cross-anchors (Phase 2), validates the v0.4.4-owned index body under six structural checks in the fixed order R49 → R50 → R52 → R53 → R51 → R54 (Phase 3), then subprocess-invokes each of the four co-located inherited verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) on its corresponding child wrapping-manifest path under `child-packages/v0.4.X/` (Phase 4). Inherited reasons R02..R48 are relayed verbatim with no v0.4.4 wrapper.

## Reason Surface

v0.4.4 **preserves the inherited verifier reasons R01..R48** verbatim (24 from v0.4.0, 5 from v0.4.1, 9 from v0.4.2, 10 from v0.4.3 under the corrected v0.4.3.1 baseline). v0.4.4 **adds 6 v0.4.4-owned reasons R49..R54** over the v0.4.4 index body and its cross-anchors. The closed verifier reason surface for v0.4.4 is therefore **54 = 48 inherited + 6 v0.4.4-owned**.

The runner-only refusal surface is **preserved at the same 5 reasons inherited verbatim from v0.4.0**: `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`. No sixth runner-only refusal. No sixth wrapper for verifier-relay on `--self-validate`.

A non-reason-shaped `INFRA: <one-line message>` channel on stderr followed by exit code 3 is reserved for environmental failures of the v0.4.4 verifier's subprocess invocation of an inherited verifier; `INFRA:` is not in the closed reason set and not in any TG1 allowlist or DENY pattern.

## 7-ID Pairwise-Distinctness Collision Class

v0.4.4 introduces a 7-ID pairwise-distinctness invariant over `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, and the v0.4.4-owned `gold_reliance_package_index_id`. All 21 pairwise collisions surface at the manifest-integrity layer under `gold_manifest_invalid` (R01). `manifest_id`, `package_id`, and `governed_reliance_demo_id` are explicitly excluded from the collision class.

## Regression Harness

v0.4.4 ships a **103-exercise regression harness** at `tests/test_gold_reliance_package_index_v0_4_4.sh`. The harness reports `ALL 103 PASS` with top-level exit 0 and covers:

- 6 PP (PP1..PP6 pristine, fresh-copy, cascade-rebuild, runner `--self-validate`, alternate `generated_at`, and cascade-rebuild byte-idempotency);
- 6 v0.4.4-owned canonical (case49..case54 for R49..R54);
- 5 runner-only refusals (ro1..ro5 covering the five inherited runner-only reasons);
- 1 env01 INFRA diagnostic;
- 48 inherited canonical (case01..case48 for R01..R48);
- 21 collision-class pairs (col_01_02..col_06_07 covering all C(7,2) pairs in the 7-ID class);
- 5 subject-table mutations (sub01..sub05);
- 5 supplementals (sup01..sup05);
- 1 rel01 inherited-relay routing case;
- 1 sup_det positive determinism case (subjects-and-index-fingerprint byte-identical re-run);
- 1 `idem01` `--force` re-run idempotency case (see below);
- 1 no_residue maxdepth-1 scan;
- 1 tg01 closed-vocabulary token scan;
- 1 ss01 scoped byte-identical snapshot.

## macOS `/tmp` → `/private/tmp` `--force` / Idempotency Fix

The v0.4.4 runner's output-dir overwrite guard accepts `--force` only when `--output-dir` matches the v0.4.4 scratch prefix. On macOS, `os.path.realpath()` resolves `/tmp/foo` to `/private/tmp/foo` (because `/tmp` is a symlink to `/private/tmp`). The v0.4.4 runner's `_output_dir_is_under_scratch_prefix` check now accepts **both** rooted realpath forms — `/tmp/proofrail-v044-*` and `/private/tmp/proofrail-v044-*` — reusing the existing `_TMP_ROOTED_PREFIXES` dual-prefix discipline already used by `_safe_rmtree`. Without this fix, a `--force` re-run against the v0.4.4-scratch-prefixed `make run-gold-reliance-package-index-v0-4-4` output path was refused on macOS even though the path literally starts with `/tmp/proofrail-v044-`.

The new `idem01 double_force_run_idempotent` regression case in the harness builds the v0.4.4 package twice into the same v0.4.4-scratch-prefixed `--output-dir` (first call without `--force`, second call with `--force`) under `--self-validate` and asserts both builds succeed. This **regression-locks** the macOS `/tmp` → `/private/tmp` realpath behavior in the runner's output-dir overwrite guard. The `make run-gold-reliance-package-index-v0-4-4` target is correspondingly idempotent — a second invocation against the same `/tmp/proofrail-v044-reliance-package-index-demo` output path passes exit 0 on both Linux and macOS.

## v0.4.3 and v0.4.3.1 Tag Preservation

The v0.4.3 annotated tag (`bd780ca…` → commit `7566993…`) and the v0.4.3.1 annotated tag (`c4095e7…` → commit `cdef8d5…`) are **preserved unchanged**. v0.4.4 is a forward-only incremental Gold release on `main`. Any consumer of the v0.4.3 or v0.4.3.1 tags may continue to fetch the exact bytes of those releases; v0.4.4 is the new incremental baseline going forward.

## Verification

Reported verification for the v0.4.4 finalization:

- `python3 -m py_compile tools/gold/build_gold_reliance_package_index_v0_1_0.py tools/gold/verify_gold_reliance_package_index_v0_1_0.py` passed;
- `make run-gold-reliance-package-index-v0-4-4` passed on two consecutive invocations against the same `/tmp/proofrail-v044-reliance-package-index-demo` output directory (idempotency proven);
- `make verify-gold-reliance-package-index-v0-4-4` passed, 103/103 exercises;
- `make verify-gold-all` passed (4 inherited tiers v0.4.0..v0.4.3 + v0.4.4 at 103/103);
- `bash tests/test_gold_reliance_package_index_v0_4_4.sh` passed, `ALL 103 PASS`;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- `git diff --check` clean.

## Boundary

v0.4.4 adds a deterministic local re-derivation surface over already-published Gold artifacts. It is:

- not a registry;
- not a certificate;
- not a federation layer;
- not signed;
- not a federation handle;
- not a transfer of reliance to any external party;
- not a policy engine, GRC platform, gateway, SIEM, observability backend, certification authority, regulator, lifecycle adjudication authority, or production authorization system;
- does not consult any live policy engine or live lifecycle adjudication authority;
- does not re-derive or summarize any inherited subject body;
- does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, or the v0.4.3 lifecycle pair (under the corrected v0.4.3.1 baseline);
- not a signed reliance instrument;
- not a signed lifecycle attestation;
- not live lifecycle adjudication;
- not full Gold;
- not Platinum;
- does not represent runtime truth.

Full Gold and Platinum remain conceptual future tiers.

## Why This Matters

v0.4.0..v0.4.3 ship four co-located Gold artifacts whose closures must be re-derived in lockstep when a downstream relying party wants a single named reliance bundle. v0.4.4 packages those four child closures plus a deterministic index body under a single 5-subject wrapping manifest with a closed-vocabulary 6-reason verifier surface (R49..R54) layered cleanly over the inherited R01..R48 surface. The 103-exercise regression harness exercises every v0.4.4-owned reason, every inherited reason via subprocess relay, all 21 pairwise collisions in the 7-ID class, positive byte-identical re-derivation, `--force` idempotency under the macOS `/tmp` → `/private/tmp` realpath form, and the closed-vocabulary TG1 scan. v0.4.3 and v0.4.3.1 tags remain bit-identical to their published bytes.
