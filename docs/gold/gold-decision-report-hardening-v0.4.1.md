# Gold Decision Report Hardening — v0.4.1

**Status:** Draft / ProofRail v0.4.1 — Gold maintenance release
**Release thesis:** ProofRail v0.4.1 is a narrow, deterministic hardening of the Gold *decision report* surface introduced by v0.4.0. It adds one new artifact (a structured decision report), one new manifest layout (3 subjects instead of 2), and five additional verifier reasons (R25..R29) that surface decision-report defects without aliasing into the inherited v0.4.0 reasons. v0.4.1 does NOT extend Gold into federation, certification, regulator workflow, multi-party governed reliance, signed reliance instruments, or any other surface beyond hardening the v0.4.0 decision report.

---

## v0.4.1 thesis

> A package owner can re-use the unchanged v0.4.0 Minimal Gold Governed Reliance Demo body and re-derive a deterministic local Gold decision report (a hand-authored structural projection of the body's governed decisions plus a closed-vocabulary coverage summary) into a 3-subject manifest cross-anchored to the v0.4.0 package and to the v0.4.0 conformance report; the v0.4.1 runner subprocesses the unchanged v0.4.0 runner and verifier to produce and validate subjects [0] and [1], then byte-anchors the new decision report as subject [2]; the v0.4.1 verifier subprocess-invokes the co-located v0.4.0 verifier on a synthesized v0.4.0 manifest, then adds five v0.4.1-owned structural checks (R25..R29) over the decision report and its bindings — while preserving the boundary that v0.4.1 does **not** assert any signed reliance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, or full Gold.

## Decision report hardening boundary

> A v0.4.1 Gold decision report package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** full Gold. It is a structural projection of an existing v0.4.0 governed-reliance package body into a deterministic local decision report, paired with the v0.4.0 conformance report and bound by a 3-subject manifest under five additional v0.4.1-owned structural checks.

## Package layout

The runtime layout at `/tmp/proofrail-gold-decision-report-hardening-v0.4.1/` holds exactly four files:

```
<output-dir>/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
├── gold-governed-reliance-decision-report.json               (subject [2])
└── gold-decision-report-package-manifest.json                (3-subject anchor)
```

The manifest carries:

- `document_type: proofrail.gold.decision_report_package_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.decision_report_hardening.v0.4.1`
- `hash_algorithm: sha256`
- `manifest_id`, `conformance_report_id`, `decision_report_id`, `generated_at`
- `package_id` and `governed_reliance_demo_id`, both cross-anchored to the package body's matching fields
- `subjects[0]`: role `governed_reliance_package`, path `governed-reliance-scenarios.json`
- `subjects[1]`: role `conformance_report`, path `silver-gold-governed-reliance-conformance-report.json`
- `subjects[2]`: role `decision_report`, path `gold-governed-reliance-decision-report.json`

Each subject carries a bare lowercase 64-hex `sha256` and a `size_bytes`. The manifest does NOT include a self-referential manifest-hash subject; v0.4.1 ships local hash anchors only.

## Subprocess delegation architecture

v0.4.1 does NOT re-implement the 24 v0.4.0 structural checks. The v0.4.1 runner subprocesses the unchanged v0.4.0 runner against `--input-package` to produce subjects [0] and [1] in a tempdir, then byte-copies them under the v0.4.1 staging directory and derives the v0.4.1 decision report as subject [2]. The v0.4.1 verifier subprocesses the co-located v0.4.0 verifier against a synthesized 2-subject v0.4.0 manifest assembled in a tempdir from the v0.4.1 manifest's first two subjects. The co-located v0.4.0 verifier's stdout/stderr is relayed verbatim; the v0.4.0 reason names appear unchanged in v0.4.1's failure output.

If the co-located v0.4.0 verifier is missing, non-executable, or crashes with no parseable output, the v0.4.1 verifier emits a non-reason-shaped `INFRA:` diagnostic on stderr and exits with code 2. The `INFRA:` diagnostic is deliberately not in the closed verifier reason set; it indicates an environmental failure, not a content failure of the v0.4.1-owned manifest or decision report.

## Identifier grammar ownership

v0.4.1 owns the grammar of three identifiers and inherits the grammar of two:

- v0.4.1-owned: `manifest_id`, `conformance_report_id`, `decision_report_id`. The v0.4.1 Phase 1 grammar check enforces the closed identifier grammar on these three fields and emits `gold_manifest_invalid` on failure.
- Inherited from v0.4.0: `package_id`, `governed_reliance_demo_id`. Grammar of these two identifiers is validated by the inherited v0.4.0 R05 (`gold_package_identity_invalid`) check on the package body. The v0.4.1 Phase 3 cross-anchors then enforce that the manifest's `package_id` and `governed_reliance_demo_id` equal the body's matching fields.

`conformance_report_id` and `decision_report_id` must be distinct from each other (collision is rejected as `gold_manifest_invalid`).

## 29 verifier reasons (24 inherited + 5 v0.4.1-owned)

The v0.4.1 verifier's closed reason set is the union of the 24 inherited v0.4.0 verifier reasons (relayed verbatim from the co-located v0.4.0 verifier) and 5 v0.4.1-owned reasons covering the new decision report subject.

The 24 inherited reasons appear in their original v0.4.0 forms with the v0.4.0 verifier's own message text; see `tools/gold/README.md` for the v0.4.0 mapping. The 5 v0.4.1-owned reasons are:

| # | Reason | Trigger |
|---|---|---|
| R25 | `gold_decision_report_not_object` | subject [2] file is not a JSON object |
| R26 | `gold_decision_report_schema_invalid` | top-level shape, `document_type`, `schema_version`, identifier grammar, required field set |
| R27 | `gold_decision_report_binding_invalid` | cross-anchors (`source_package_sha256`, `source_conformance_report_sha256`, `decision_report_id`, `package_id`, `governed_reliance_demo_id`, `relying_party.identity_id`) between decision report and manifest / package / conformance report |
| R28 | `gold_decision_report_projection_invalid` | per-row projection of `decisions[]` against the body's `governed_decisions[]` (`decision_id`, `scenario_type`, `decision_status`, `policy_decision`, `decision_authority_role`, `protected_action_id`, `action_category`, `action_environment`), plus full-report byte drift outside `coverage_summary` |
| R29 | `gold_decision_report_summary_invalid` | `coverage_summary` block: enum-presence indicators (`decision_statuses_present`, `policy_decisions_present`, `protected_actions_present`, `registry_roles_present`, `scenario_types_present`), `total_decisions`, and `unique_*` counts must agree with `decisions[]` |

R28 and R29 are split: row-level projection drift and full-report byte drift outside `coverage_summary` route to R28; any drift inside `coverage_summary` routes to R29. The split keeps both reasons independently reachable.

## Reachability ordering

- v0.4.1 Phase 1 (manifest integrity, v0.4.1-owned identifier grammar, subject layout, cross-anchors) fires first and emits `gold_manifest_invalid` on failure.
- v0.4.0 subprocess delegation fires next. The co-located v0.4.0 verifier's stdout/stderr is relayed verbatim, so all 24 inherited reason names surface unchanged.
- v0.4.1 Phase 3 (decision-report-owned checks) fires AFTER the v0.4.0 subprocess returns success. R25 (`gold_decision_report_not_object`) fires first inside Phase 3; R26 follows; R27 (cross-anchor binding) follows; R28 (row projection + non-summary byte drift) follows; R29 (coverage summary drift) follows.
- The v0.4.0 inherited reasons are never re-emitted by v0.4.1's own code; they are always relayed from the co-located v0.4.0 verifier.
- The 5 runner-only refusal codes (`runner_input_path_*`) are emitted only by the v0.4.1 runner during Phase A preflight on `--input-package`, BEFORE any output-directory touch and BEFORE the v0.4.0 runner subprocess; the v0.4.1 verifier never emits them.

## 5 runner-only refusal reasons

The v0.4.1 runner emits exactly these five preflight refusal codes against `--input-package` BEFORE any output directory touch:

| Reason | Trigger |
|---|---|
| `runner_input_path_missing` | flag empty or unset |
| `runner_input_path_forbidden` | absolute path or contains `..` |
| `runner_input_file_missing` | relative path does not exist on disk |
| `runner_input_read_failed` | open/read fails or path is a directory |
| `runner_input_json_invalid` | path does not parse as JSON |

The runner never wraps a verifier failure under a sixth runner-only refusal code. With `--self-validate`, a verifier failure (either v0.4.0-inherited or v0.4.1-owned) is relayed verbatim from the v0.4.1 verifier's own stdout/stderr.

## Commands

```bash
make run-gold-decision-report-hardening-v0-4-1
make verify-gold-decision-report-hardening-v0-4-1
make verify-gold-all
```

`run-gold-decision-report-hardening-v0-4-1` builds the v0.4.1 package into `/tmp/proofrail-gold-decision-report-hardening-v0.4.1/` with `--force --self-validate`, then runs the v0.4.1 verifier against the published manifest.

`verify-gold-decision-report-hardening-v0-4-1` runs the dedicated regression test (`tests/test_gold_decision_report_hardening_v0_4_1.sh`), which exercises 61 ordered cases:

- 6 positive-path (PP1–PP6)
- 29 canonical verifier reasons (case01–case29): 24 inherited via subprocess delegation to the co-located v0.4.0 verifier, plus 5 v0.4.1-owned (R25..R29)
- 15 duplicate / secondary `gold_manifest_invalid` cases (dup01..dup15) all routed to the single Phase 1 manifest-integrity reason
- 1 supplemental decision-report binding case (sup01; folds to R27)
- 6 runner-only refusal exercises (ro1, ro2, ro2b, ro3..ro5) covering the 5 distinct runner-only reasons with `runner_input_path_forbidden` exercised twice
- 1 runner-relay-of-verifier-failure case (rel01)
- 1 verifier-relay-of-inherited-failure case (rel02; asserts that an inherited v0.4.0 reason is relayed unchanged)
- 1 taxonomy gate with environmental-wrapper deny-list (TG1)
- 1 scoped sha256 snapshot (SS)

`verify-gold-all` chains the v0.4.1 verifier into the framework-wide Gold chain after the v0.4.0 target.

## TG1 taxonomy gate scope

TG1 scans the v0.4.1-owned source surface only (schemas, the runner, the verifier, the regression test, the v0.4.1 fixture README, the v0.4.1 release narrative, and the v0.4.1 demo dir). For every reason-shaped token discovered in those files, TG1 requires the token to belong to the union of the 29-reason verifier set, the 5-reason runner-only set, and a closed allowlist. The allowlist is intentionally tiny: it contains only the five exact `coverage_summary` field names that coincidentally trip the `_present` suffix filter (`decision_statuses_present`, `policy_decisions_present`, `protected_actions_present`, `registry_roles_present`, `scenario_types_present`). The allowlist does not admit semantic synonyms, paraphrases of failure modes, or pattern-shaped entries.

TG1 additionally enforces an environmental-wrapper deny-list. Any reason-shaped token whose substring matches one of the deny entries (constructed via string concatenation in the test source so the test's own source does not self-trip) is rejected. This catches the failure mode where an environmental wrapper token (e.g. naming a verifier executable, a delegated subprocess, or an infrastructure failure mode) leaks into the verifier reason surface.

## Non-claims

- The v0.4.1 release is not full Gold and is not Platinum.
- The v0.4.1 release is not signed and ships local hash anchors only.
- The v0.4.1 release is not a certificate, not federated, and not a transfer of reliance to any external party.
- The v0.4.1 release does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, or compliance certification.
- The v0.4.1 release does not claim production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.
- The v0.4.1 release does not consult any live service, gateway, observability backend, policy engine, GRC platform, or external registry; it validates structural shape, cross-anchor binding, row-level projection, and `coverage_summary` re-derivation only.
- The v0.4.1 release does not perform end-to-end re-verification of the upstream Silver evidence chain; the v0.4.0 package body's five `inputs.*` blocks are structural pointers under closed input-type and ref grammar only.
- The v0.4.1 release does not extend the substance of the v0.4.0 package body; the decision report is a structural projection of decisions already present in the body, paired with a closed-vocabulary `coverage_summary` derived from those decisions.
- The v0.4.1 release does not introduce a new Gold tier; it is a v0.4.x maintenance hardening of the existing v0.4.0 decision-report surface.
