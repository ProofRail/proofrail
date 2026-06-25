# Gold Policy Evaluation Matrix — v0.4.2

**Status:** Draft / ProofRail v0.4.2 — Gold maintenance release
**Release thesis:** ProofRail v0.4.2 is a narrow, deterministic hardening of the Gold *policy evaluation matrix* surface. It adds two new artifacts (a hand-authored policy evaluation matrix and a byte-re-derivable policy evaluation report), one new manifest layout (5 subjects instead of 3), and nine additional verifier reasons (R30..R38) that surface matrix and evaluation-report defects without aliasing into the inherited v0.4.0 or v0.4.1 reasons. v0.4.2 does NOT extend Gold into federation, certification, regulator workflow, multi-party governed reliance, signed reliance instruments, live-policy-engine evaluation, or any other surface beyond making local policy evaluation explicit, tabular, and independently re-derivable.

---

## v0.4.2 thesis

> A package owner can re-use the unchanged v0.4.0 Minimal Gold Governed Reliance Demo body and the unchanged v0.4.1 Gold decision report and pair them with a hand-authored local policy evaluation matrix (one matrix row per recognized scenario, in natural order) to re-derive a deterministic local Gold policy evaluation report (a hand-authored structural projection of decision rows against matrix rows plus a closed-vocabulary coverage summary) into a 5-subject manifest cross-anchored to the v0.4.0 package body, the v0.4.0 conformance report, the v0.4.1 decision report, the v0.4.2 runtime matrix, and the v0.4.2 evaluation report; the v0.4.2 runner subprocesses the unchanged v0.4.1 runner (which itself subprocesses the v0.4.0 runner) to produce and validate subjects [0], [1], and [2], then injects two runtime-bound scalars (`decision_report_sha256` and `generated_at`) into the matrix template to produce subject [3], and derives subject [4] from the matrix and the decision report; the v0.4.2 verifier subprocess-invokes the co-located v0.4.1 verifier on a synthesized v0.4.1 manifest, then adds nine v0.4.2-owned structural checks (R30..R38) over the matrix and the evaluation report and their bindings — while preserving the boundary that v0.4.2 does **not** assert any signed reliance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, live-policy-engine output, or full Gold.

## Policy evaluation boundary

> A v0.4.2 Gold policy-evaluation-matrix package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** live policy-engine output; it is **not** full Gold. It is a hand-authored structural projection of an existing v0.4.0 governed-reliance package body and v0.4.1 decision report into a deterministic local policy evaluation matrix and a byte-re-derivable evaluation report, paired with the v0.4.0 conformance report and bound by a 5-subject manifest under nine additional v0.4.2-owned structural checks.

## Package layout

The runtime layout at `/tmp/proofrail-gold-policy-evaluation-matrix-v0.4.2/` holds exactly six files:

```
<output-dir>/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
├── gold-governed-reliance-decision-report.json               (subject [2])
├── gold-policy-evaluation-matrix.json                        (subject [3])
├── gold-policy-evaluation-report.json                        (subject [4])
└── gold-policy-evaluation-matrix-package-manifest.json       (5-subject anchor)
```

The manifest carries:

- `document_type: proofrail.gold.policy_evaluation_matrix_package_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.policy_evaluation_matrix.v0.4.2`
- `hash_algorithm: sha256`
- `manifest_id`, `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `generated_at`
- `package_id` and `governed_reliance_demo_id`, both cross-anchored to the package body's matching fields
- `subjects[0]`: role `governed_reliance_package`, path `governed-reliance-scenarios.json`
- `subjects[1]`: role `conformance_report`, path `silver-gold-governed-reliance-conformance-report.json`
- `subjects[2]`: role `decision_report`, path `gold-governed-reliance-decision-report.json`
- `subjects[3]`: role `policy_evaluation_matrix`, path `gold-policy-evaluation-matrix.json`
- `subjects[4]`: role `policy_evaluation_report`, path `gold-policy-evaluation-report.json`

Each subject carries a bare lowercase 64-hex `sha256` and a `size_bytes`. The manifest does NOT include a self-referential manifest-hash subject; v0.4.2 ships local hash anchors only.

## Matrix template and runtime matrix

The hand-authored fixture under `fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json` is a *template*, not a complete runtime matrix. It contains every substantive field that the v0.4.2 runner does not derive at runtime: `document_type`, `schema_version`, `profile`, `matrix_id`, `package_id`, `governed_reliance_demo_id`, `decision_report_ref`, `policy_pack_id`, `policy_pack_version`, `matrix_rows[]`, `scope_limitations`, and `non_claims`. The runner injects two runtime-bound scalar fields into subject [3]: `decision_report_sha256` (bare lowercase hex SHA-256 of the derived v0.4.1 decision-report bytes) and `generated_at` (ISO-8601 UTC supplied via CLI). The template omits both fields; the runtime matrix carries both.

## Subprocess delegation architecture

v0.4.2 does NOT re-implement the 29 inherited structural checks. The v0.4.2 runner subprocesses the unchanged v0.4.1 runner against `--input-package` (the v0.4.1 runner itself subprocesses the v0.4.0 runner). The v0.4.2 verifier subprocesses the co-located v0.4.1 verifier against a synthesized 3-subject v0.4.1 manifest assembled in a tempdir from the v0.4.2 manifest's first three subjects. The co-located v0.4.1 verifier's stdout/stderr is relayed verbatim; the v0.4.1 and v0.4.0 reason names appear unchanged in v0.4.2's failure output.

If the co-located v0.4.1 verifier is missing, non-executable, or crashes with no parseable output, the v0.4.2 verifier emits a non-reason-shaped `INFRA:` diagnostic on stderr and exits with code 3. The `INFRA:` diagnostic is deliberately not in the closed verifier reason set; it indicates an environmental failure, not a content failure of the v0.4.2-owned matrix or evaluation report.

## Identifier grammar ownership

v0.4.2 owns the grammar of two identifiers and inherits the grammar of the rest:

- v0.4.2-owned: `matrix_id`, `policy_evaluation_report_id`. The v0.4.2 Phase 1 grammar check enforces the closed identifier grammar on these two fields and emits `gold_manifest_invalid` on failure. `matrix_id` and `policy_evaluation_report_id` must be distinct from each other.
- Inherited from v0.4.0/v0.4.1: `package_id`, `governed_reliance_demo_id`, `manifest_id`, `conformance_report_id`, `decision_report_id`. Grammar of these five identifiers is validated by inherited checks; the v0.4.2 Phase 1 cross-anchors then enforce that the manifest's `package_id` and `governed_reliance_demo_id` equal the body's matching fields.

## 38 verifier reasons (24 + 5 + 9)

The v0.4.2 verifier's closed reason set is the union of the 24 inherited v0.4.0 reasons (relayed verbatim from the co-located v0.4.1 verifier, which itself relays them verbatim from the co-located v0.4.0 verifier), the 5 inherited v0.4.1 reasons (relayed verbatim from the co-located v0.4.1 verifier), and 9 v0.4.2-owned reasons covering the new matrix and evaluation-report subjects.

The 24 inherited v0.4.0 reasons appear in their original v0.4.0 forms; the 5 inherited v0.4.1 reasons (R25..R29) appear in their original v0.4.1 forms. The 9 v0.4.2-owned reasons are:

| # | Reason | Trigger |
|---|---|---|
| R30 | `gold_policy_matrix_not_object` | subject [3] file is not a JSON object |
| R31 | `gold_policy_matrix_schema_invalid` | top-level shape, `document_type`, `schema_version`, identifier grammar, required field set (including injected `decision_report_sha256` and `generated_at`) |
| R32 | `gold_policy_matrix_binding_invalid` | cross-anchors (`package_id`, `governed_reliance_demo_id`, `decision_report_ref`, `decision_report_sha256`) between matrix and manifest / package / decision report |
| R33 | `gold_policy_matrix_entry_invalid` | per-row matrix entry: closed-vocabulary tuple (`scenario_type`, `decision_status`, `policy_decision`, `action_category`, `action_environment`, `decision_authority_role`, `required_subject_type`, `evaluation_effect`, `row_rationale_code`) and position constraints |
| R34 | `gold_policy_evaluation_report_not_object` | subject [4] file is not a JSON object |
| R35 | `gold_policy_evaluation_report_schema_invalid` | top-level shape, `document_type`, `schema_version`, identifier grammar, required field set |
| R36 | `gold_policy_evaluation_report_binding_invalid` | cross-anchors (`package_id`, `governed_reliance_demo_id`, `source_decision_report_sha256`, `source_matrix_sha256`, `policy_evaluation_report_id`) between evaluation report and manifest / package / decision report / matrix |
| R37 | `gold_policy_evaluation_result_invalid` | per-row evaluation drift in `evaluation_rows[]` against the published matrix and decision rows, plus full-report byte drift outside `coverage_summary` |
| R38 | `gold_policy_evaluation_summary_invalid` | `coverage_summary` block: `decision_row_count`, `matrix_row_count`, `matched_count`, `unmatched_matrix_row_count`, `uncovered_decision_row_count`, `conflict_count`, and `aggregate_evaluation_fingerprint` must agree with the re-derived evaluation |

R37 and R38 are split: row-level evaluation drift and full-report byte drift outside `coverage_summary` route to R37; any drift inside `coverage_summary` routes to R38. The split keeps both reasons independently reachable.

## Reachability ordering

- v0.4.2 Phase 1 (manifest integrity, v0.4.2-owned identifier grammar, subject layout, cross-anchors) fires first and emits `gold_manifest_invalid` on failure.
- v0.4.1 subprocess delegation fires next. The co-located v0.4.1 verifier (which itself relays the v0.4.0 verifier) is invoked on a synthesized 3-subject v0.4.1 manifest. All 24 v0.4.0 and 5 v0.4.1 reason names surface unchanged.
- v0.4.2 Phase 3 (matrix-owned checks R30..R33) fires AFTER the v0.4.1 subprocess returns success.
- v0.4.2 Phase 4 (evaluation-report-owned checks R34..R38) fires AFTER Phase 3 passes.
- The inherited reasons are never re-emitted by v0.4.2's own code; they are always relayed from the co-located v0.4.1 verifier (which relays the v0.4.0 verifier).
- The 5 runner-only refusal codes (`runner_input_path_*`) are emitted only by the v0.4.2 runner during Phase A preflight on `--input-package`, BEFORE any output-directory touch and BEFORE the v0.4.1 runner subprocess; the v0.4.2 verifier never emits them.

## 5 runner-only refusal reasons

The v0.4.2 runner emits exactly these five preflight refusal codes against `--input-package` BEFORE any output directory touch. They are inherited unchanged from v0.4.1:

| Reason | Trigger |
|---|---|
| `runner_input_path_missing` | flag empty or unset |
| `runner_input_path_forbidden` | absolute path or contains `..` |
| `runner_input_file_missing` | relative path does not exist on disk |
| `runner_input_read_failed` | open/read fails or path is a directory |
| `runner_input_json_invalid` | path does not parse as JSON |

The runner never wraps a verifier failure under a sixth runner-only refusal code. With `--self-validate`, a verifier failure (v0.4.0-inherited, v0.4.1-inherited, or v0.4.2-owned) is relayed verbatim from the v0.4.2 verifier's own stdout/stderr.

## Commands

```bash
make run-gold-policy-evaluation-matrix-v0-4-2
make verify-gold-policy-evaluation-matrix-v0-4-2
make verify-gold-all
```

`run-gold-policy-evaluation-matrix-v0-4-2` builds the v0.4.2 package into `/tmp/proofrail-gold-policy-evaluation-matrix-v0.4.2/` with `--force --self-validate`, then runs the v0.4.2 verifier against the published manifest.

`verify-gold-policy-evaluation-matrix-v0-4-2` runs the dedicated regression test (`tests/test_gold_policy_evaluation_matrix_v0_4_2.sh`), which exercises 78 ordered cases:

- 6 positive-path (PP1..PP6)
- 38 canonical verifier reasons (case01..case38): 24 inherited from v0.4.0 via subprocess delegation, 5 inherited from v0.4.1, and 9 v0.4.2-owned (R30..R38)
- 3 runtime-scalar canonicals (rt1, rt1b, rt2) folding to the inherited matrix-shape and matrix-binding reasons
- 18 duplicate / secondary manifest-invalid cases (dup01..dup18) all routed to the single Phase 1 manifest-integrity reason
- 4 supplementals (sup01, sup02 evaluation-report binding; sup03 positive determinism; sup04 limitations-block prohibited-token allowance)
- 6 runner-only refusal exercises (ro1, ro2, ro2b, ro3..ro5) covering the 5 distinct runner-only reasons with `runner_input_path_forbidden` exercised twice
- 1 runner-relay-of-verifier-failure case (rel01)
- 1 verifier-relay-of-inherited-failure case (rel02)
- 1 environment-failure INFRA diagnostic case (env01)
- 1 taxonomy gate with environmental-wrapper deny-list (TG1)
- 1 scoped sha256 snapshot (SS)

`verify-gold-all` chains the v0.4.2 verifier into the framework-wide Gold chain after the v0.4.1 target.

## TG1 taxonomy gate scope

TG1 scans the v0.4.2-owned source surface only (three schemas, the matrix template README, the matrix template fixture, the runner, the verifier, the regression test, the v0.4.2 release narrative, and the v0.4.2 demo dir). For every reason-shaped token discovered in those files, TG1 requires the token to belong to the union of the 38-reason verifier set, the 5-reason runner-only set, and a closed allowlist.

The allowlist is intentionally tiny: it contains only the five exact `coverage_summary` field names inherited from the v0.4.1 decision-report schema (`decision_statuses_present`, `policy_decisions_present`, `protected_actions_present`, `registry_roles_present`, `scenario_types_present`). Those five tokens appear inside the v0.4.2 build tool because the v0.4.2 runner internally derives a v0.4.1 decision report. The allowlist does not admit any v0.4.2-introduced data-field name (none of the v0.4.2 coverage-summary keys trip the suffix filter), does not admit semantic synonyms, does not admit paraphrases of failure modes, and does not admit pattern-shaped entries.

TG1 additionally enforces an environmental-wrapper deny-list. Any reason-shaped token whose substring matches one of the deny entries (including `v042_verifier`, `v041_verifier`, `v040_verifier`, and the `subprocess`, `delegation_failure`, `environment_failure`, `infra_failure`, `inherited_verifier_*`, and `tool_unavailable` families, all constructed via string concatenation in the test source so the test's own source does not self-trip) is rejected. This catches the failure mode where an environmental wrapper token leaks into the verifier reason surface.

## Non-claims

- The v0.4.2 release is not full Gold and is not Platinum.
- The v0.4.2 release is not signed and ships local hash anchors only.
- The v0.4.2 release is not a certificate, not federated, and not a transfer of reliance to any external party.
- The v0.4.2 release does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, or compliance certification.
- The v0.4.2 release does not claim production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.
- The v0.4.2 release does not consult any live policy engine, GRC platform, gateway, observability backend, or external authority; it validates structural shape, cross-anchor binding, row-level projection, and `coverage_summary` re-derivation only.
- The v0.4.2 release does not perform end-to-end re-verification of the upstream Silver evidence chain.
- The v0.4.2 release does not extend the substance of the v0.4.0 package body or the v0.4.1 decision report; the matrix and the evaluation report are hand-authored structural records of local policy expectations and their derived re-projection.
- The v0.4.2 release does not introduce a new Gold tier; it is a v0.4.x maintenance hardening of the policy-evaluation surface.
