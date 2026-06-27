# ProofRail v0.4.5 — Gold Multi-Case Reliance Demo

ProofRail v0.4.5 adds a Gold Multi-Case Reliance Demo over the v0.4.4 Gold Reliance Package Index. It is a narrow incremental Gold release that wraps ONE unchanged v0.4.4 Gold Reliance Package Index child closure (which itself wraps the unchanged v0.4.0 Governed Reliance Demo, v0.4.1 Decision Report Hardening, v0.4.2 Policy Evaluation Matrix, and v0.4.3 Challenge Lifecycle Lite under the corrected v0.4.3.1 baseline) under a single 2-subject wrapping manifest plus a single byte-stable v0.4.5-authored multi-case projection index body. v0.4.5 introduces no new Gold tier, is not signed, is not federated, is not a registry, is not a federation handle, does not transfer reliance, and does not extend the substance of the v0.4.4 surface or of any inherited release. The v0.4.0..v0.4.4 annotated tags are preserved unchanged.

## What v0.4.5 Adds

v0.4.5 ships a single wrapping manifest with 2 fixed-order subjects, plus the v0.4.5-authored multi-case index body it anchors:

- subject [0] — v0.4.4 child wrapping package manifest (`gold_reliance_package_index_manifest`), under `child-packages/v0.4.4/`;
- subject [1] — the v0.4.5-authored `gold_multi_case_reliance_index` body, at `gold-multi-case-reliance-index.json`.

The v0.4.5 runner subprocess-invokes the co-located v0.4.4 runner EXACTLY ONCE (without `--self-validate`) into `child-packages/v0.4.4/` under the v0.4.5 staging tree, where the v0.4.4 runner writes its complete child closure (which itself materializes the nested v0.4.0..v0.4.3 closures via its own subprocess delegation). The v0.4.5 runner then projects the five v0.4.0 governed-reliance scenarios as fixed-order case entries (in natural v0.4.0 order: `clean_acceptance`, `policy_rejection`, `challenge_filed`, `withdrawal`, `supersession`), derives the v0.4.5 multi-case index body deterministically (closed-key `coverage_summary` with `case_count = 5` and three anchor-consistency booleans; top-level `multi_case_index_fingerprint` over canonical JSON of the body excluding the fingerprint field), builds the 2-subject v0.4.5 wrapping manifest, runs the v0.4.5 verifier under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination. v0.4.5 input copies are bundled to a disposable scratch directory (`/tmp/proofrail-v045-bundle-<pid>/`) BEFORE forwarding to the v0.4.4 runner; tracked repo paths are never forwarded.

The v0.4.5 verifier validates the v0.4.5 wrapping manifest and the v0.4.5-owned index body under seven v0.4.5-owned structural checks in a locked order (wrapping-manifest integrity → subject-digest binding → index-body shape → child-manifest cross-anchor → case-count → case-binding → index-body fingerprint re-derivation), then subprocess-invokes the v0.4.4 verifier on the materialized v0.4.4 wrapping-manifest path under `child-packages/v0.4.4/...`. The inherited 54-reason surface (R01..R48 from v0.4.0..v0.4.3 plus R49..R54 from v0.4.4) is relayed verbatim through the v0.4.5 verifier with no v0.4.5 wrapper.

## Reason Surface

v0.4.5 **preserves the inherited verifier reasons R01..R54** verbatim via subprocess relay through the v0.4.4 verifier (24 from v0.4.0, 5 from v0.4.1, 9 from v0.4.2, 10 from v0.4.3 under the corrected v0.4.3.1 baseline, and 6 from v0.4.4). v0.4.5 **adds 7 v0.4.5-owned reasons** over the v0.4.5 wrapping manifest, the v0.4.5-owned multi-case index body, and their cross-anchors. The closed verifier reason surface for v0.4.5 is therefore **61 = 54 inherited + 7 v0.4.5-owned**. Literal v0.4.5-owned reason token names are intentionally not enumerated in this release note; see `docs/gold/gold-multi-case-reliance-v0.4.5.md` and `schemas/gold-multi-case-reliance-{package-manifest,index}-v0.1.0.md` for the per-token surface.

The runner-only refusal surface is **preserved at the same 5 reasons inherited verbatim from v0.4.0**: `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`. No sixth runner-only refusal. No sixth wrapper for verifier-relay on `--self-validate`. Phase A preflight extends to all three inherited inputs and is followed by Phase A.5 scratch-bundle isolation so the v0.4.4 runner only ever sees scratch input copies.

A non-reason-shaped `INFRA: <one-line message>` channel on stderr followed by exit code 3 is reserved for environmental failures of the v0.4.5 verifier's subprocess invocation of the v0.4.4 verifier; `INFRA:` is not in the closed reason set and not in any TG1 allowlist or DENY pattern.

## Identifier Grammar Ownership

v0.4.5 owns the grammar of three identifiers: the v0.4.5 wrapping `manifest_id`, the `gold_multi_case_reliance_index_id`, and each `case_id` (computed `<case_id_prefix>_<case_index>`, default prefix `case`). `package_id` and `governed_reliance_demo_id` are v0.4.5-bound but their grammar continues to be checked by the inherited v0.4.0 verifier via subprocess relay through v0.4.4. All other identifiers carried in the v0.4.4 wrapping manifest and in the nested v0.4.0..v0.4.3 surfaces are inherited verbatim through the relay chain.

## Closed Case-Slug Vocabulary

The five `cases[]` entries draw their `case_slug` values verbatim from the v0.4.0 governed-reliance closed scenario set, fixed per-index — `cases[0] = clean_acceptance`, `cases[1] = policy_rejection`, `cases[2] = challenge_filed`, `cases[3] = withdrawal`, `cases[4] = supersession`. Any deviation surfaces under one of the seven v0.4.5-owned structural checks (shape, count, or per-index binding) per the locked check order.

## Regression Harness

v0.4.5 ships a **21-exercise regression harness** at `tests/test_gold_multi_case_reliance_v0_4_5.sh`. The harness reports `ALL 21 PASS` with top-level exit 0 and covers:

- pp1 pristine build with `--self-validate`;
- pp2 standalone verifier pass;
- 7 v0.4.5-owned canonical mutation cases under the locked check order (`r55`..`r61`), with per-case hash-first re-anchoring to avoid earlier-order shadowing;
- inh01 inherited-verifier relay verbatim through the v0.4.4 chain;
- 5 runner-only refusals (ro1..ro5) covering the five inherited runner-only reasons;
- env01 INFRA exit-3 diagnostic on missing co-located v0.4.4 verifier (non-destructive);
- sup_det positive determinism re-run (subjects-and-index-fingerprint byte-identical);
- idem01 `--force` re-run byte-identical under the v0.4.5 scratch prefix;
- no_residue scratch + inherited-tier leak scan;
- tg01 closed-vocabulary token scan over the v0.4.5-owned surface (size-7 v0.4.5 reason set plus the size-5 inherited runner-only refusal set);
- ss01 scoped byte-identical sha256 snapshot over the 4 v0.4.5-owned source files (2 schemas + 2 tools; harness file intentionally excluded).

## v0.4.0..v0.4.4 Tag Preservation

The v0.4.0, v0.4.1, v0.4.2, v0.4.3, v0.4.3.1, and v0.4.4 annotated tags are **preserved unchanged**. v0.4.5 is a forward-only incremental Gold release on `main`. Any consumer of those tags may continue to fetch their exact bytes; v0.4.5 is the new incremental baseline going forward.

## Verification

Reported verification for the v0.4.5 finalization:

- `python3 -m py_compile tools/gold/build_gold_multi_case_reliance_v0_1_0.py tools/gold/verify_gold_multi_case_reliance_v0_1_0.py` passed;
- `make run-gold-multi-case-reliance-v0-4-5` passed on two consecutive invocations against the same `/tmp/proofrail-v045-multi-case-reliance-demo` output directory (idempotency proven);
- `make verify-gold-multi-case-reliance-v0-4-5` passed, 21/21 exercises;
- `make verify-gold-all` passed (4 inherited tiers v0.4.0..v0.4.3 + v0.4.4 + v0.4.5 at 21/21);
- `bash tests/test_gold_multi_case_reliance_v0_4_5.sh` passed, `ALL 21 PASS`;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- `git diff --check` clean.

## Boundary

v0.4.5 adds a deterministic local multi-case projection surface over the already-published v0.4.4 Gold Reliance Package Index. It is:

- not a registry;
- not a certificate;
- not a federation layer;
- not signed;
- not a federation handle;
- not a transfer of reliance to any external party;
- not a policy engine, GRC platform, gateway, SIEM, observability backend, certification authority, regulator, lifecycle adjudication authority, or production authorization system;
- does not consult any live service;
- does not re-derive or summarize any inherited subject body;
- does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, the v0.4.3 lifecycle pair, or the v0.4.4 reliance-package index;
- not a signed reliance instrument;
- not a signed lifecycle attestation;
- not live lifecycle adjudication;
- not full Gold;
- not Platinum;
- does not represent runtime truth.

Full Gold and Platinum remain conceptual future tiers.

## Why This Matters

v0.4.4 ships a single 5-subject reliance-package index that wraps four inherited Gold child closures under one wrapping manifest. v0.4.5 projects that wrapping into a closed-vocabulary five-case index whose `cases[]` entries enumerate the five v0.4.0 governed-reliance scenarios in fixed natural order, anchored back to the v0.4.4 wrapping manifest by a 2-subject v0.4.5 wrapping manifest and a single byte-stable v0.4.5-authored multi-case index body. The 21-exercise regression harness exercises every v0.4.5-owned reason under the locked check order, the inherited 54-reason surface via subprocess relay through the v0.4.4 chain, positive byte-identical re-derivation, `--force` idempotency under the v0.4.5 scratch prefix, and the closed-vocabulary TG1 scan over the v0.4.5-owned surface. v0.4.0..v0.4.4 tags remain bit-identical to their published bytes.
