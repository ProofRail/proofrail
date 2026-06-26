# Gold Challenge Lifecycle Lite — v0.4.3

**Status:** Draft / ProofRail v0.4.3 — Gold maintenance release (unreleased)
**Release thesis:** ProofRail v0.4.3 is a narrow, deterministic hardening of the Gold *challenge lifecycle* surface. It adds two new artifacts (a hand-authored runtime challenge-lifecycle records body and a deterministic local lifecycle report projected from that records body), one new manifest layout (7 subjects instead of 5), and ten additional verifier reasons (R39..R48) that surface lifecycle-records-body and lifecycle-report defects without aliasing into the inherited v0.4.0, v0.4.1, or v0.4.2 reasons. v0.4.3 does NOT extend Gold into federation, certification, regulator workflow, multi-party governed reliance, signed reliance instruments, live-policy-engine evaluation, signed lifecycle attestation, external lifecycle adjudication, or any other surface beyond making local challenge-lifecycle state explicit, row-shaped, and independently re-derivable.

---

## v0.4.3 thesis

> A package owner can re-use the unchanged v0.4.0 Minimal Gold Governed Reliance Demo body, the unchanged v0.4.1 Gold decision report, the unchanged v0.4.2 policy evaluation matrix, and the unchanged v0.4.2 policy evaluation report, and pair them with a hand-authored local runtime challenge-lifecycle records body (one lifecycle record per governed decision row, in natural order, with a closed-vocabulary event chain) to re-derive a deterministic local Gold lifecycle report (a row-per-record projection plus a closed-vocabulary coverage summary keyed on the six lifecycle status values) into a 7-subject manifest cross-anchored to the v0.4.0 package body, the v0.4.0 conformance report, the v0.4.1 decision report, the v0.4.2 runtime matrix, the v0.4.2 evaluation report, the v0.4.3 runtime records body, and the v0.4.3 lifecycle report; the v0.4.3 runner subprocesses the unchanged v0.4.2 runner (which itself subprocesses the v0.4.1 and v0.4.0 runners) to produce and validate subjects [0]..[4], then injects three runtime-bound scalars (top-level `policy_evaluation_report_sha256`, top-level `generated_at`, and per-record `lifecycle_fingerprint`) into the records template to produce subject [5], and derives subject [6] from the records body and the evaluation report; the v0.4.3 verifier subprocess-invokes the co-located v0.4.2 verifier on a synthesized v0.4.2 manifest, then adds ten v0.4.3-owned structural checks (R39..R48) over the records body and the lifecycle report and their bindings — while preserving the boundary that v0.4.3 does **not** assert any signed reliance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, live policy-engine output, live lifecycle adjudication, signed lifecycle attestation, or full Gold.

## Lifecycle boundary

> A v0.4.3 Gold challenge-lifecycle-lite package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** live policy-engine output; it is **not** live challenge-lifecycle adjudication; it is **not** a signed lifecycle attestation; it is **not** an external challenge-resolution authority; it is **not** full Gold. It is a hand-authored structural projection of an existing v0.4.0 governed-reliance package body, v0.4.1 decision report, and v0.4.2 policy-evaluation pair into a deterministic local runtime challenge-lifecycle records body and a byte-re-derivable lifecycle report, paired with the inherited five subjects and bound by a 7-subject manifest under ten additional v0.4.3-owned structural checks.

## Package layout

The runtime layout at `/tmp/proofrail-gold-challenge-lifecycle-lite-v0.4.3/` holds exactly eight files:

```
<output-dir>/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
├── gold-governed-reliance-decision-report.json               (subject [2])
├── gold-policy-evaluation-matrix.json                        (subject [3])
├── gold-policy-evaluation-report.json                        (subject [4])
├── gold-challenge-lifecycle-records.json                     (subject [5])
├── gold-challenge-lifecycle-report.json                      (subject [6])
└── gold-challenge-lifecycle-package-manifest.json            (7-subject anchor)
```

The manifest carries:

- `document_type: proofrail.gold.challenge_lifecycle_package_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.challenge_lifecycle_lite.v0.4.3`
- `hash_algorithm: sha256`
- `manifest_id`, `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `generated_at`
- `package_id` and `governed_reliance_demo_id`, both cross-anchored to the package body's matching fields
- `subjects[0]`: role `governed_reliance_package`, path `governed-reliance-scenarios.json`
- `subjects[1]`: role `conformance_report`, path `silver-gold-governed-reliance-conformance-report.json`
- `subjects[2]`: role `decision_report`, path `gold-governed-reliance-decision-report.json`
- `subjects[3]`: role `policy_evaluation_matrix`, path `gold-policy-evaluation-matrix.json`
- `subjects[4]`: role `policy_evaluation_report`, path `gold-policy-evaluation-report.json`
- `subjects[5]`: role `challenge_lifecycle_records`, path `gold-challenge-lifecycle-records.json`
- `subjects[6]`: role `challenge_lifecycle_report`, path `gold-challenge-lifecycle-report.json`

Each subject carries a bare lowercase 64-hex `sha256` and a `size_bytes`. The manifest does NOT include a self-referential manifest-hash subject; v0.4.3 ships local hash anchors only.

## Records template and runtime records body

The hand-authored fixture under `fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json` is a *template*, not a complete runtime records body. It contains every substantive field that the v0.4.3 runner does not derive at runtime: `document_type`, `schema_version`, `profile`, `lifecycle_record_set_id`, `package_id`, `governed_reliance_demo_id`, `policy_evaluation_report_ref`, `lifecycle_records[]` (each with `lifecycle_id`, `target_decision_id`, `target_decision_row_id`, `current_status`, `events[]`, and any required terminal-status ref), `scope_limitations`, and `non_claims`. The runner injects three runtime-bound scalar fields:

- top-level `policy_evaluation_report_sha256` — bare lowercase hex SHA-256 of the derived v0.4.2 evaluation report (subject [4]);
- top-level `generated_at` — ISO-8601 UTC supplied via `--generated-at`;
- per record in `lifecycle_records[]`, `lifecycle_fingerprint` — bare lowercase hex SHA-256 over the canonical-JSON serialization of the record body excluding the fingerprint field itself.

The template omits all three; the runtime records body carries all three.

## Subprocess delegation architecture

v0.4.3 does NOT re-implement the 38 inherited structural checks. The v0.4.3 runner subprocesses the unchanged v0.4.2 runner against `--input-package` and `--matrix-input` (the v0.4.2 runner itself subprocesses the v0.4.1 and v0.4.0 runners). The v0.4.3 verifier subprocesses the co-located v0.4.2 verifier against a synthesized 5-subject v0.4.2 manifest assembled in a tempdir from the v0.4.3 manifest's first five subjects. The co-located v0.4.2 verifier's stdout/stderr is relayed verbatim; the v0.4.0, v0.4.1, and v0.4.2 reason names appear unchanged in v0.4.3's failure output.

If the co-located v0.4.2 verifier is missing, non-executable, or crashes with no parseable output, the v0.4.3 verifier emits a non-reason-shaped `INFRA:` diagnostic on stderr and exits with code 3. The `INFRA:` diagnostic is deliberately not in the closed verifier reason set; it indicates an environmental failure, not a content failure of the v0.4.3-owned records body or lifecycle report.

## Identifier grammar ownership

v0.4.3 owns the grammar of two identifiers and inherits the grammar of the rest:

- v0.4.3-owned: `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`. The v0.4.3 Phase 1 grammar check enforces the closed identifier grammar on these two fields and emits `gold_manifest_invalid` on failure. The v0.4.3 6-ID pairwise-distinctness collision class is: `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`. Collision-class violations involving either of the two v0.4.3-owned IDs are recognized at the manifest-integrity level and routed to `gold_manifest_invalid`; the v0.4.3-owned `*_binding_invalid` reasons are reserved for body-level cross-anchor mismatches, not for manifest-level identifier-distinctness violations.
- Inherited from v0.4.0/v0.4.1/v0.4.2: `package_id`, `governed_reliance_demo_id`, `manifest_id`, `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`. Grammar of these seven identifiers is validated by inherited checks; the v0.4.3 Phase 1 cross-anchors then enforce that the manifest's `package_id` and `governed_reliance_demo_id` equal the body's matching fields.

## 48 verifier reasons (24 + 5 + 9 + 10)

The v0.4.3 verifier's closed reason set is the union of the 24 inherited v0.4.0 reasons (relayed verbatim from the co-located v0.4.2 verifier, which itself relays them verbatim from the co-located v0.4.1 verifier, which itself relays them verbatim from the co-located v0.4.0 verifier), the 5 inherited v0.4.1 reasons (R25..R29), the 9 inherited v0.4.2 reasons (R30..R38), and 10 v0.4.3-owned reasons covering the new records body and lifecycle report subjects.

The 24 inherited v0.4.0 reasons appear in their original v0.4.0 forms; the 5 inherited v0.4.1 reasons appear in their original v0.4.1 forms; the 9 inherited v0.4.2 reasons appear in their original v0.4.2 forms. The 10 v0.4.3-owned reasons are:

| # | Reason | Trigger |
|---|---|---|
| R39 | `gold_challenge_lifecycle_records_not_object` | subject [5] file is not a JSON object |
| R40 | `gold_challenge_lifecycle_records_schema_invalid` | top-level shape, `document_type`, `schema_version`, identifier grammar, required field set (including injected top-level `policy_evaluation_report_sha256`, top-level `generated_at`, and per-record `lifecycle_fingerprint`) |
| R41 | `gold_challenge_lifecycle_records_binding_invalid` | cross-anchors between records body and manifest / package / evaluation report (`package_id`, `governed_reliance_demo_id`, `policy_evaluation_report_ref`, `policy_evaluation_report_sha256`) |
| R42 | `gold_challenge_lifecycle_event_invalid` | per-event validity in `lifecycle_records[*].events[]`: closed-vocabulary pair table over `(event_status, event_basis)`, closed `actor_role`, closed `lifecycle_effect`, and per-record terminal-status required-ref enforcement (`resolved_locally` requires `local_resolution_ref`; `withdrawn` requires `withdrawal_record_ref`; `superseded` requires `superseding_decision_id`) |
| R43 | `gold_challenge_lifecycle_transition_invalid` | sequence / graph validity: first event's `event_status` must be `filed`; closed status-transition graph; strict non-decreasing `event_timestamp` monotonicity within each record; no events after a terminal status; record-level `current_status` must equal the final event's `event_status` |
| R44 | `gold_challenge_lifecycle_report_not_object` | subject [6] file is not a JSON object |
| R45 | `gold_challenge_lifecycle_report_schema_invalid` | top-level shape, `document_type`, `schema_version`, identifier grammar, required field set |
| R46 | `gold_challenge_lifecycle_report_binding_invalid` | cross-anchors between lifecycle report and manifest / package / records body (`package_id`, `governed_reliance_demo_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `source_records_sha256`, `source_policy_evaluation_report_sha256`) |
| R47 | `gold_challenge_lifecycle_projection_invalid` | per-row projection drift in `lifecycle_rows[]` against the published records body, plus full-report byte drift outside `coverage_summary` |
| R48 | `gold_challenge_lifecycle_summary_invalid` | `coverage_summary` block: `record_count`, terminal/open record counts, `status_value_count` (6-key closed map over `filed`, `acknowledged`, `under_review`, `resolved_locally`, `superseded`, `withdrawn`), `event_count`, and `aggregate_lifecycle_fingerprint` must agree with the re-derived projection |

R47 and R48 are split: row-level projection drift and full-report byte drift outside `coverage_summary` route to R47; any drift inside `coverage_summary` routes to R48. The split keeps both reasons independently reachable.

## Reachability ordering

- v0.4.3 Phase 1 (manifest integrity, v0.4.3-owned identifier grammar, subject layout, 7-subject cross-anchors, 6-ID pairwise-distinctness collision class) fires first and emits `gold_manifest_invalid` on failure.
- v0.4.2 subprocess delegation fires next. The co-located v0.4.2 verifier (which itself relays the v0.4.1 verifier, which itself relays the v0.4.0 verifier) is invoked on a synthesized 5-subject v0.4.2 manifest. All 24 v0.4.0, 5 v0.4.1, and 9 v0.4.2 reason names surface unchanged.
- v0.4.3 Phase 3 (records-body-owned checks R39..R43) fires AFTER the v0.4.2 subprocess returns success.
- v0.4.3 Phase 4 (lifecycle-report-owned checks R44..R48) fires AFTER Phase 3 passes.
- Within records-body checks the ordering is: not-object (R39) → schema-shape (R40) → binding (R41) → per-event validity (R42) → sequence/graph validity (R43).
- Within lifecycle-report checks the ordering is: not-object (R44) → schema-shape (R45) → binding (R46) → projection (R47) → summary (R48).
- The inherited reasons are never re-emitted by v0.4.3's own code; they are always relayed from the co-located v0.4.2 verifier.
- The 5 runner-only refusal codes (`runner_input_path_*`) are emitted only by the v0.4.3 runner during Phase A preflight, BEFORE any output-directory touch and BEFORE the v0.4.2 runner subprocess; preflight applies to all three external inputs (`--input-package`, `--matrix-input`, `--lifecycle-input`); the v0.4.3 verifier never emits them.

## 5 runner-only refusal reasons

The v0.4.3 runner emits exactly these five preflight refusal codes BEFORE any output directory touch. They are inherited unchanged from v0.4.0:

| Reason | Trigger |
|---|---|
| `runner_input_path_missing` | flag empty or unset |
| `runner_input_path_forbidden` | absolute path or contains `..` |
| `runner_input_file_missing` | relative path does not exist on disk |
| `runner_input_read_failed` | open/read fails or path is a directory |
| `runner_input_json_invalid` | path does not parse as JSON |

The runner never wraps a verifier failure under a sixth runner-only refusal code. With `--self-validate`, a verifier failure (v0.4.0-inherited, v0.4.1-inherited, v0.4.2-inherited, or v0.4.3-owned) is relayed verbatim from the v0.4.3 verifier's own stdout/stderr.

## Closed lifecycle vocabularies

The v0.4.3 records-body schema enforces five closed vocabularies:

- 6 `current_status` values: `filed`, `acknowledged`, `under_review`, `resolved_locally`, `superseded`, `withdrawn`.
- 6 `event_status` values: identical to the 6 `current_status` values.
- 6 `event_basis` values: `acknowledgement_record`, `review_update`, `local_resolution`, `supersession_link`, `withdrawal_record`, `system_observation`.
- 4 `actor_role` values: `relying_party`, `policy_authority`, `protected_action_authority`, `system`.
- 4 `lifecycle_effect` values: `challenge_open`, `clarification`, `terminal_resolution`, `no_effect`.

Each event entry MUST contain a `(event_status, event_basis)` pair drawn from a closed pair table; pair violations are routed to R42. Terminal record-level statuses each require a record-level ref field (R42): `resolved_locally → local_resolution_ref`, `withdrawn → withdrawal_record_ref`, `superseded → superseding_decision_id`. The non-terminal statuses (`filed`, `acknowledged`, `under_review`) carry no record-level ref requirement.

The records-body schema additionally enforces a closed status-transition graph (R43) covering the eight permitted transitions: `filed → acknowledged`, `filed → withdrawn`, `filed → superseded`, `acknowledged → under_review`, `acknowledged → superseded`, `acknowledged → withdrawn`, `under_review → resolved_locally`, `under_review → superseded`, `under_review → withdrawn`. Any unlisted transition routes to R43.

## Commands

```bash
make run-gold-challenge-lifecycle-lite-v0-4-3
make verify-gold-challenge-lifecycle-lite-v0-4-3
make verify-gold-all
```

`run-gold-challenge-lifecycle-lite-v0-4-3` builds the v0.4.3 package into `/tmp/proofrail-gold-challenge-lifecycle-lite-v0.4.3/` with `--force --self-validate`, then runs the v0.4.3 verifier against the published manifest.

`verify-gold-challenge-lifecycle-lite-v0-4-3` runs the dedicated regression test (`tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh`), which exercises 99 ordered cases:

- 6 positive-path (PP1..PP6)
- 48 canonical verifier reasons (case01..case48): 24 inherited from v0.4.0, 5 inherited from v0.4.1, 9 inherited from v0.4.2, and 10 v0.4.3-owned (R39..R48)
- 4 runtime-scalar mutation variants (rt1, rt1b, rt2, rt3) folding to records-shape and records-binding reasons
- 23 duplicate / subject-table / collision cases (dup01..dup23) routed to the single Phase 1 manifest-integrity reason
- 5 supplementals (sup01 R42 withdrawn-without-`withdrawal_record_ref`; sup02 R43 first-event-not-`filed` distinct from canonical case43; sup03 R43 event-after-terminal; sup04 R43 `current_status`-vs-final-event; sup05 R46 `challenge_lifecycle_report_id` collides with `policy_evaluation_report_id` at the lifecycle-report-body level)
- 6 runner-only refusal exercises (ro1, ro2, ro2b, ro3, ro4, ro5) covering the 5 distinct runner-only reasons with `runner_input_path_forbidden` exercised twice
- 1 runner-relay-of-verifier-failure case (rel01)
- 1 verifier-relay-of-inherited-failure case (rel02)
- 1 environment-failure INFRA diagnostic case (env01)
- 1 positive-determinism re-run (sup_det)
- 1 no-residue assertion (scratch + inherited tiers)
- 1 taxonomy gate with environmental-wrapper deny-list (TG1)
- 1 scoped sha256 snapshot (SS)

`verify-gold-all` chains the v0.4.3 verifier into the framework-wide Gold chain after the v0.4.2 target.

## TG1 taxonomy gate scope

TG1 scans the v0.4.3-owned source surface only (three schemas, the records template README, the records template fixture, the runner, the verifier, the regression test, the v0.4.3 release narrative, and the v0.4.3 demo dir). For every reason-shaped token discovered in those files, TG1 requires the token to belong to the union of the 48-reason verifier set, the 5-reason runner-only set, and a closed allowlist.

The allowlist is intentionally tiny: it carries forward the five inherited v0.4.1 `coverage_summary` data-field names plus the small fixed set of v0.4.3 `coverage_summary` data-field names (the closed lifecycle-status keys `filed`, `acknowledged`, `under_review`, `resolved_locally`, `superseded`, `withdrawn` appear inside the `status_value_count` map and are recognized as data values, not as reason names). The allowlist does not admit semantic synonyms, does not admit paraphrases of failure modes, and does not admit pattern-shaped entries.

TG1 additionally enforces an environmental-wrapper deny-list. Any reason-shaped token whose substring matches one of the deny entries (including `v043_verifier`, `v042_verifier`, `v041_verifier`, `v040_verifier`, and the `subprocess`, `delegation_failure`, `environment_failure`, `infra_failure`, `inherited_verifier_*`, and `tool_unavailable` families, all constructed via string concatenation in the test source so the test's own source does not self-trip) is rejected. This catches the failure mode where an environmental wrapper token leaks into the verifier reason surface.

## Scratch path policy

The v0.4.3 regression test writes runtime test artifacts (bad-input variants for the `runner_input_json_invalid` and runner-relay-of-verifier-failure exercises) under a v0.4.3/test-owned scratch path `tests/_tmp_gold_challenge_lifecycle_lite_v0_4_3/`. The suite setup fails safely if the scratch path already exists at start (no silent reuse). The EXIT trap removes only the test-owned scratch path and the per-suite work directory. An explicit `[no-residue]` assertion verifies, BEFORE the SS-AFTER snapshot, that the scratch path is empty and that no `_v043_*`, `ro5_*`, `rel01_*`, or `sup*_bad_*` residue exists under any inherited-tier fixture directory.

## Non-claims

- The v0.4.3 release is not full Gold and is not Platinum.
- The v0.4.3 release is not signed and ships local hash anchors only.
- The v0.4.3 release is not a certificate, not federated, and not a transfer of reliance to any external party.
- The v0.4.3 release does not claim regulator approval, auditor approval, third-party endorsement, legal acceptance, legal adjudication, legal enforceability, or compliance certification.
- The v0.4.3 release does not claim production authorization, production governance, production PKI, audit readiness, or control operating / design effectiveness.
- The v0.4.3 release does not consult any live policy engine, live lifecycle adjudication authority, GRC platform, gateway, observability backend, or external authority; it validates structural shape, cross-anchor binding, per-event validity, sequence / graph validity, row-level projection, and `coverage_summary` re-derivation only.
- The v0.4.3 release does not perform end-to-end re-verification of the upstream Silver evidence chain.
- The v0.4.3 release does not extend the substance of the v0.4.0 package body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair; the records body and the lifecycle report are hand-authored structural records of local lifecycle expectations and their derived re-projection.
- The v0.4.3 release does not introduce a new Gold tier; it is a v0.4.x maintenance hardening of the challenge-lifecycle surface.
- The v0.4.3 release is unreleased at the time of authoring; the most recently released Gold tier is v0.4.2.
