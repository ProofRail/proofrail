# Gold Multi-Case Reliance Demo — v0.4.5

**Status:** In development — ProofRail v0.4.5 — narrow incremental Gold release
**Release thesis:** ProofRail v0.4.5 is a narrow, deterministic, hand-orchestrated wrapping of ONE unchanged v0.4.4 Gold Reliance Package Index child closure under a single 2-subject wrapping manifest and a single byte-stable v0.4.5-authored multi-case projection index body. The index body projects exactly five fixed-order case entries (one per v0.4.0 governed-reliance scenario in natural v0.4.0 order) drawn from the v0.4.4 child closure, computes a closed-key `coverage_summary`, and re-derives a top-level `multi_case_index_fingerprint`. v0.4.5 adds one new wrapping manifest layout (2 subjects: the v0.4.4 wrapping manifest plus the v0.4.5-owned index body), one new body file, seven v0.4.5-owned verifier reasons (R55..R61), and the runtime closure layout `child-packages/v0.4.4/...` (the entire unchanged v0.4.4 closure surfaces here verbatim, including its own nested `child-packages/v0.4.X/...` subtrees). v0.4.5 does NOT introduce a new Gold tier, does NOT sign anything, does NOT federate, does NOT transfer reliance, and does NOT extend the substance of the v0.4.4 surface or of any inherited release.

---

## v0.4.5 thesis

> A package owner can re-use the unchanged v0.4.4 Gold Reliance Package Index child closure (built under the corrected v0.4.3.1 verifier baseline, wrapping the unchanged v0.4.0 governed-reliance demo, v0.4.1 decision report, v0.4.2 policy evaluation matrix, and v0.4.3 challenge lifecycle), materialize exactly one copy of that child closure under its own `child-packages/v0.4.4/` subdirectory, project a deterministic local multi-case index body that names each of the five v0.4.0 governed-reliance scenarios as a closed-vocabulary case entry in natural v0.4.0 order, bind that index body and the v0.4.4 wrapping manifest under a 2-subject v0.4.5 wrapping manifest, and validate the entire structure end-to-end via the v0.4.5 verifier which subprocess-invokes the v0.4.4 verifier on the materialized child closure. The v0.4.5 runner consumes exactly the same three inherited input files as the v0.4.4 runner (`--input-package`, `--matrix-input`, `--lifecycle-input`); the v0.4.5 runner adds no new input template; the index body is fully derived from the materialized v0.4.4 child closure. v0.4.5 does **not** assert any signed reliance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, live policy-engine output, live lifecycle adjudication, signed lifecycle attestation, full Gold, or Platinum.

## Multi-case reliance boundary

> A v0.4.5 Gold Multi-Case Reliance Demo package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a registry; it is **not** a federation handle; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** live policy-engine output; it is **not** live challenge-lifecycle adjudication; it is **not** a signed lifecycle attestation; it is **not** an external reliance authority; it is **not** full Gold; it is **not** Platinum. It is a hand-orchestrated, deterministic local wrapping of ONE v0.4.4 child closure under a 2-subject manifest plus a byte-stable v0.4.5-authored multi-case projection index body with seven v0.4.5-owned structural checks and inherited-verifier subprocess relay for the inherited 54-reason surface (48 inherited from v0.4.0..v0.4.3 plus 6 from v0.4.4).

## Package layout

The runtime layout at `/tmp/proofrail-v045-multi-case-reliance-demo/` is a multi-file output:

```
<output-dir>/
├── gold-multi-case-reliance-package-manifest.json                   (wrapping manifest)
├── gold-multi-case-reliance-index.json                              (subject [1]: v0.4.5 index body)
└── child-packages/
    └── v0.4.4/
        ├── gold-reliance-package-index-manifest.json                (subject [0]: v0.4.4 wrapping manifest)
        ├── gold-reliance-package-index.json                         (v0.4.4-authored body)
        └── child-packages/                                          (unchanged v0.4.4 closure verbatim)
            ├── v0.4.0/...
            ├── v0.4.1/...
            ├── v0.4.2/...
            └── v0.4.3/...
```

The v0.4.5 wrapping manifest carries:

- `document_type: proofrail.gold.multi_case_reliance_package_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.multi_case_reliance.v0.4.5`
- `hash_algorithm: sha256`
- `manifest_id` (v0.4.5-owned; not in any collision class)
- `gold_multi_case_reliance_index_id` (v0.4.5-owned; cross-anchored to the index body)
- `package_id` and `governed_reliance_demo_id` (v0.4.5-owned binding anchors; cross-anchored to the index body)
- `gold_reliance_package_index_ref` (relative POSIX path to the v0.4.4 wrapping manifest under `child-packages/v0.4.4/`)
- `decision_report_ref` (relative POSIX path to a v0.4.1 decision-report payload reached through the v0.4.4 closure layout, recorded for downstream readability only; not re-verified by the v0.4.5 verifier — the v0.4.4 verifier re-validates its own closure)
- `generated_at` ISO-8601 UTC
- `subjects[0]`: role `gold_reliance_package_index_manifest`, path `child-packages/v0.4.4/gold-reliance-package-index-manifest.json`
- `subjects[1]`: role `gold_multi_case_reliance_index`, path `gold-multi-case-reliance-index.json`

Each subject carries a bare lowercase 64-hex `sha256` and an integer `size_bytes`. The wrapping manifest does NOT include a self-referential manifest-hash subject; v0.4.5 ships local hash anchors only.

Files under `child-packages/v0.4.4/` (the entire v0.4.4 closure, including its nested `child-packages/v0.4.X/` subtrees) are runtime support files for the v0.4.4 verifier; they are NOT enumerated as v0.4.5 wrapping-manifest subjects and have no v0.4.5-owned reason coverage of their own. Their integrity is enforced by the v0.4.4 verifier (and, transitively, by the inherited v0.4.0..v0.4.3 verifiers) via subprocess relay.

## Multi-case index body

The v0.4.5 index body at `gold-multi-case-reliance-index.json` (subject [1]) is the only v0.4.5-authored payload. It carries:

- `document_type: proofrail.gold.multi_case_reliance_index`
- `schema_version: v0.1.0`
- `proofrail_release: gold.multi_case_reliance.v0.4.5`
- `hash_algorithm: sha256`
- `gold_multi_case_reliance_index_id`, `package_id`, `governed_reliance_demo_id`, `generated_at`
- `gold_reliance_package_index_ref`, `gold_reliance_package_index_fingerprint`, `gold_reliance_package_index_size_bytes`, `gold_reliance_package_index_id` cross-anchor to the v0.4.4 wrapping manifest and to subject [0] of the v0.4.5 wrapping manifest (byte-equal sha256 / size_bytes / path).
- `cases[0..4]`: exactly five fixed-order case entries, one per v0.4.0 governed-reliance scenario in natural v0.4.0 order. Each entry carries `case_index` (0..4), `case_id` (`<case_id_prefix>_<case_index>`; default prefix `case`), `case_slug` (closed-vocabulary value drawn from the v0.4.0 scenario natural order: `clean_acceptance`, `policy_rejection`, `challenge_filed`, `withdrawal`, `supersession`), and the v0.4.4 child-closure anchors required to reach the per-case evidence (path under `child-packages/v0.4.4/...`, sha256, size_bytes for the v0.4.0 governed-reliance scenario row corresponding to this case).
- `coverage_summary`: closed-key object with `case_count = 5`, `case_slug_count = 5`, `package_id_anchor_consistency = true`, `governed_reliance_demo_id_anchor_consistency = true`, `gold_reliance_package_index_anchor_consistency = true`. Stray keys are rejected.
- `multi_case_index_fingerprint`: bare lowercase 64-hex SHA-256 over `json.dumps(body_obj_without_multi_case_index_fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")`.

## Subprocess delegation architecture

v0.4.5 does NOT re-implement any of the 54 inherited verifier-reason checks (R01..R48 from v0.4.0..v0.4.3 and R49..R54 from v0.4.4). The v0.4.5 **runner** subprocess-invokes the co-located v0.4.4 runner EXACTLY ONCE into `child-packages/v0.4.4/` under the v0.4.5 staging tree, where the v0.4.4 runner writes its complete child closure (which itself contains the nested v0.4.0..v0.4.3 closures). The v0.4.4 runner is invoked WITHOUT `--self-validate`; the v0.4.5 verifier is the single entry point for chained verification on the v0.4.5 staged tree.

The v0.4.5 **verifier** subprocess-invokes the co-located v0.4.4 verifier on the materialized v0.4.4 wrapping-manifest path under `child-packages/v0.4.4/...`. The v0.4.4 verifier then subprocess-invokes each of the four co-located v0.4.0..v0.4.3 verifiers as documented in `gold-reliance-package-index-v0.4.4.md`. All inherited reasons R02..R54 are relayed verbatim through the v0.4.5 verifier with no v0.4.5 wrapper.

If the co-located v0.4.4 verifier is missing, non-executable, or crashes with a non-FAIL non-zero exit, the v0.4.5 verifier emits a non-reason-shaped `INFRA:` diagnostic on stderr and exits with code 3 (distinct from verifier-reason exit 1). The `INFRA:` diagnostic is deliberately not in the closed verifier reason set; it indicates an environmental failure of the v0.4.5 → v0.4.4 subprocess invocation, not a content failure of the v0.4.5-owned wrapping manifest, the v0.4.5-owned index body, or any inherited subject.

## Identifier grammar ownership

v0.4.5 owns the grammar of three identifiers and inherits the grammar of the rest:

- v0.4.5-owned: `manifest_id` (v0.4.5 wrapping manifest), `gold_multi_case_reliance_index_id`, `case_id` (each case entry; computed `<case_id_prefix>_<case_index>`). The v0.4.5 Phase 1 grammar check enforces the closed identifier grammar (`PACKAGE_ID_RE = ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`) on these fields and folds failures into `gold_multi_case_reliance_manifest_invalid` (v0.4.5 wrapping manifest layer) or `gold_multi_case_reliance_index_invalid` (index body layer).
- v0.4.5-bound, inherited grammar: `package_id` and `governed_reliance_demo_id` are v0.4.5-bound (the v0.4.5 wrapping manifest and index body carry their own copies and cross-anchor them to the v0.4.4 child wrapping manifest), but their grammar continues to be checked by the inherited v0.4.0 verifier via subprocess relay through v0.4.4.
- Inherited verbatim through the v0.4.4 → v0.4.0..v0.4.3 relay: every other identifier in the v0.4.4 wrapping manifest and in the v0.4.0..v0.4.3 wrapping manifests (`v044-manifest-id`, `v044-conformance-report-id`, `v044-decision-report-id`, `v044-policy-evaluation-report-id`, `v044-challenge-lifecycle-report-id`, `v044-gold-reliance-package-index-id`, plus the v0.4.0..v0.4.3 surfaces).

## Closed case-slug vocabulary

The five case slugs are drawn verbatim from the v0.4.0 governed-reliance closed scenario vocabulary, in natural v0.4.0 order:

- `cases[0].case_slug = clean_acceptance`
- `cases[1].case_slug = policy_rejection`
- `cases[2].case_slug = challenge_filed`
- `cases[3].case_slug = withdrawal`
- `cases[4].case_slug = supersession`

Any deviation from this fixed five-entry, fixed-order, closed-vocabulary set surfaces under one of three v0.4.5-owned index-body reasons (`gold_multi_case_reliance_index_invalid` for shape, `gold_multi_case_reliance_case_count_invalid` for wrong count, `gold_multi_case_reliance_case_binding_invalid` for wrong-but-closed slug at the wrong index). The reason taxonomy is documented per-token in the v0.4.5 schema files `schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md` and `schemas/gold-multi-case-reliance-index-v0.1.0.md` and exercised case-by-case in `tests/test_gold_multi_case_reliance_v0_4_5.sh`.

## 61 verifier reasons (54 inherited + 7 v0.4.5-owned)

The v0.4.5 verifier's closed reason set is the union of 54 inherited reasons R01..R54 (relayed verbatim from the co-located v0.4.4 verifier via subprocess, which itself relays R01..R48 from the v0.4.0..v0.4.3 verifiers) and 7 v0.4.5-owned reasons R55..R61 over the v0.4.5 wrapping manifest and the v0.4.5-authored index body.

The 54 inherited reasons appear in their original v0.4.0..v0.4.4 forms. The 7 v0.4.5-owned reasons are documented in the v0.4.5 schema files and exercised exhaustively in the v0.4.5 regression harness; their token names are deliberately not enumerated in shared documentation files older TG gates may scan.

The 7-reason surface decomposes as:

- 1 wrapping-manifest integrity reason (Phase 1)
- 1 wrapping-manifest subject-binding reason (Phase 1)
- 1 index-body shape reason (Phase 2, body re-derivation)
- 1 index-body cross-anchor reason against the v0.4.4 wrapping manifest (Phase 2)
- 1 index-body case-count reason (Phase 2)
- 1 index-body case-binding reason (closed-vocabulary slug at the wrong index) (Phase 2)
- 1 index-body fingerprint re-derivation reason (Phase 2, fires last)

## Reachability orderings (v0.4.5-owned phases)

- **Phase 1 — wrapping-manifest integrity.** Manifest shape, subject path constraints (path-traversal rejected BEFORE exact path equality), subject count == 2, subject role/order, subject SHA-256 / size_bytes match against the bytes on disk, identifier grammar on `manifest_id` and `gold_multi_case_reliance_index_id`. All shape and grammar failures here fold into the v0.4.5 wrapping-manifest integrity reason. Subject-digest mismatches fold into the v0.4.5 wrapping-manifest subject-binding reason.
- **Phase 2 — v0.4.5 index body re-derivation, fixed locked order:** wrapping-manifest integrity → subject-digest → index-body shape → child-manifest cross-anchor → case-count → case-binding → index-body fingerprint re-derivation. The order is locked in the v0.4.5 verifier and asserted end-to-end by the v0.4.5 regression harness (`r55` → `r56` → `r57` → `r58` → `r59` → `r60` → `r61`), with per-case re-anchoring to avoid earlier-order shadowing.
- **Phase 3 — inherited verifier invocation.** The v0.4.5 verifier subprocess-invokes the v0.4.4 verifier on the materialized v0.4.4 wrapping-manifest path under `child-packages/v0.4.4/...`. Any inherited reason R02..R54 surfaces UNCHANGED through the chain. Environmental failure surfaces under a non-reason-shaped `INFRA:` diagnostic with exit code 3.

The 7 v0.4.5-owned reasons are validated BEFORE any inherited verifier subprocess so that the v0.4.5-owned reasons are reachable without contaminating any inherited verifier's namespace.

## Runner architecture

Phase A (preflight) emits exactly the same 5 approved runner-only refusal reasons as v0.4.0..v0.4.4, applied to every input-path argument BEFORE any output directory touch:

- `runner_input_path_missing`
- `runner_input_path_forbidden`
- `runner_input_file_missing`
- `runner_input_read_failed`
- `runner_input_json_invalid`

The runner never wraps a verifier failure under a sixth runner-only refusal code. With `--self-validate`, a verifier failure is relayed verbatim from the v0.4.5 verifier's own stdout/stderr; the staging directory is removed (via `_safe_rmtree`, which refuses any path outside the v0.4.5 scratch prefix) and the destination is left untouched.

Phase A.5 (scratch input bundle) copies all three inputs by byte content into a disposable scratch directory at `/tmp/proofrail-v045-bundle-<pid>/`. The v0.4.4 runner is invoked against the scratch copies ONLY; tracked repo paths are NEVER forwarded to the v0.4.4 runner.

Phase B (staging) creates `/tmp/proofrail-v045-staging-<pid>/`, subprocess-invokes the v0.4.4 runner EXACTLY ONCE into `child-packages/v0.4.4/` (without `--self-validate`), reads the materialized v0.4.4 wrapping manifest plus the inherited bodies reached through the v0.4.4 closure layout, derives the v0.4.5 index body deterministically (five fixed-order case entries projected from the v0.4.0 governed-reliance scenarios, closed-key `coverage_summary`, top-level `multi_case_index_fingerprint` recomputed last), writes the v0.4.5 wrapping manifest and the v0.4.5 index body, runs the v0.4.5 verifier under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination. `--force` is permitted only when `--output-dir` lives under `V045_SCRATCH_PREFIX = "/tmp/proofrail-v045-"` (macOS `/private/tmp/proofrail-v045-` realpath form also accepted); otherwise `--force` is refused.

## TG1 allowlist discipline (v0.4.5 harness)

The v0.4.5 regression harness ships TG1 with a closed allowlist limited to **inherited-tier short-form data-field labels and inherited relay tokens** that share the v0.4.5 reason-shaped suffix grammar (`_invalid`, `_mismatch`, `_missing`, `_forbidden`, `_failed`). No v0.4.5-introduced data field is a substring of any v0.4.5 reason name in R55..R61: the v0.4.5 index body deliberately uses field names like `gold_multi_case_reliance_index_id`, `gold_reliance_package_index_fingerprint`, `gold_reliance_package_index_size_bytes`, `case_index`, `case_id`, `case_slug`, `case_count`, `case_slug_count`, `package_id_anchor_consistency`, `governed_reliance_demo_id_anchor_consistency`, `gold_reliance_package_index_anchor_consistency`, and `multi_case_index_fingerprint`, none of which match the reason-shaped suffix grammar of any v0.4.5 reason.

The TG1 DENY patterns are string-concatenated at runtime so the literal full token never appears in the scanner's own source; otherwise the scanner self-trips when this file is scanned. The DENY patterns target environmental-wrapper escape drift (`infra_*`, `env_*`, `runner_*_v045_*` composite escape patterns).

## INFRA diagnostic boundary

The `INFRA:` diagnostic is reserved for environmental failures of the v0.4.5 verifier's subprocess invocation of the v0.4.4 verifier. It is NOT a member of the closed verifier reason set and does NOT appear in any TG1 allowlist or DENY pattern. The diagnostic surface is exactly `INFRA: <one-line message>` on stderr followed by exit code 3.

## Test scratch path policy

The v0.4.5 regression harness scratch path is `WORK=$(mktemp -d /tmp/proofrail-v045-test.XXXXXX)` with an EXIT-trap cleanup. No test artifact is ever written under an inherited-tier fixture directory, under any tracked repo path, or under any non-`/tmp` filesystem location.

## Non-claims

The v0.4.5 tooling does not certify, audit, approve, transfer, federate, register, sign, attest, adjudicate, or operate any production system. It records a deterministic local hand-orchestrated wrapping of ONE unchanged v0.4.4 Gold Reliance Package Index child closure under a closed-vocabulary v0.4.5-owned multi-case projection index body (five fixed-order case entries, one per v0.4.0 governed-reliance scenario in natural v0.4.0 order) and a 2-subject wrapping manifest, validates structural shape, identifier grammar, the cross-anchor binding to the v0.4.4 wrapping manifest, the closed five-case projection (count + per-index slug + fingerprint re-derivation), and subprocess-relays the inherited 54-reason surface verbatim through the v0.4.4 verifier. It does not consult any live service, gateway, observability backend, policy engine, GRC platform, registry, federation, lifecycle adjudication authority, or external authority. It does not re-derive or summarize inherited subject bodies. It is not signed and ships local hash anchors only. It is not a new Gold tier. It is not full Gold. It is not Platinum.
