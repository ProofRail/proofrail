# ProofRail Gold Tools

This directory contains tooling for the ProofRail Minimal Gold tier
boundary. The first Gold tier release is **v0.4.0 Minimal Gold Governed
Reliance Demo**.

A v0.4.0 package is a deterministic local hand-authored record of
governed reliance decisions composed from Silver-shaped inputs. It is
NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold.

## Current supported schemas

- Gold Governed Reliance Package v0.1.0
- Gold Governed Reliance Package Manifest v0.1.0
- Gold Governed Reliance Conformance Report v0.1.0
- Gold Reliance Package Index v0.1.0
- Gold Reliance Package Index Manifest v0.1.0

## Gold Governed Reliance Demo Runner (v0.4.0)

Builds a deterministic, hash-anchored local v0.4.0 Minimal Gold
Governed Reliance Demo package from a hand-authored package body JSON
file. The runner emits exactly three files: the byte-copied package
body, a re-derived 24-entry conformance report, and a 2-subject
manifest.

```bash
python3 tools/gold/build_gold_governed_reliance_demo_v0_1_0.py \
  --input-package fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json \
  --manifest-id proofrail-gold-governed-reliance-manifest-demo-001 \
  --report-id proofrail-gold-governed-reliance-conformance-report-demo-001 \
  --generated-at 2026-09-15T00:30:00Z \
  --output-dir /tmp/proofrail-gold-governed-reliance-v0.4.0 \
  --force \
  --self-validate
```

The runner stages output under a sibling directory
`<output-dir>.staging.<pid>` and atomically publishes via
`os.replace()`. With `--self-validate` the runner invokes the v0.4.0
verifier against the staged package BEFORE the atomic move; on
self-validation failure the staging directory is removed and the
destination is left untouched. The runner relays the verifier's
failure UNCHANGED with no sixth runner-only wrapper code.

Output layout (deterministic):

```
<output-dir>/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
└── gold-governed-reliance-package-manifest.json              (manifest)
```

### Runner-only refusal reasons (5)

The runner emits exactly five preflight refusal codes against
`--input-package` BEFORE any output directory touch:

- `runner_input_path_missing`   — flag empty or unset
- `runner_input_path_forbidden` — absolute path or contains `..`
- `runner_input_file_missing`   — path does not exist on disk
- `runner_input_read_failed`    — open/read fails or path is a directory
- `runner_input_json_invalid`   — path does not parse as JSON

The runner never wraps a verifier failure under a sixth runner-only
refusal code. With `--self-validate`, a verifier failure is relayed
verbatim from the verifier's own stdout/stderr.

## Gold Governed Reliance Demo Verifier (v0.4.0)

Verifies a v0.4.0 Minimal Gold Governed Reliance Demo package by
re-running 24 ordered structural checks against the schema and
re-deriving the bundled conformance report byte-for-byte. The verifier
takes a single `--manifest` flag and prints `PASS: ...` on success or
`FAIL: <reason>: <detail>` on failure with exit code 1.

```bash
python3 tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py \
  --manifest /tmp/proofrail-gold-governed-reliance-v0.4.0/gold-governed-reliance-package-manifest.json
```

### Approved verifier failure reasons (24)

The verifier emits exactly these 24 reasons; no synonyms, no aliases,
no 25th reason. Reachability ordering ensures each reason is
reachable with a dedicated fixture mutation.

| # | Reason | Check |
|---|---|---|
| 01 | `gold_manifest_invalid` | manifest integrity, subject paths, hashes, cross-anchor, post-structural conformance-report byte-compare |
| 02 | `gold_package_not_object` | package body is not a JSON object |
| 03 | `gold_package_schema_invalid` | top-level `document_type` / `schema_version` / `scope_limitations` shape |
| 04 | `gold_profile_unsupported` | `profile` outside `{gold.governed_reliance.v0.4.0}` |
| 05 | `gold_package_identity_invalid` | `package_id` / `governed_reliance_demo_id` grammar |
| 06 | `silver_verification_input_invalid` | `inputs.silver_verification` shape / `expected_status` |
| 07 | `silver_handoff_input_invalid` | `inputs.silver_handoff` shape / `expected_handoff_posture` |
| 08 | `policy_pack_input_invalid` | `inputs.policy_pack` shape |
| 09 | `registry_lite_input_invalid` | `inputs.registry_lite` shape |
| 10 | `control_crosswalk_input_invalid` | `inputs.control_crosswalk` shape |
| 11 | `governed_decision_set_invalid` | list type, 1..5 entries, unique `scenario_type`, natural-order |
| 12 | `governed_decision_entry_invalid` | per-entry shape and grammar |
| 13 | `decision_subject_binding_invalid` | `decision_subject.subject_type` / `subject_ref` |
| 14 | `decision_policy_binding_invalid` | `policy_binding` shape vs. `inputs.policy_pack` |
| 15 | `decision_registry_binding_invalid` | `registry_binding.relying_party_id` / `decision_authority_role` |
| 16 | `decision_action_scope_invalid` | `action_scope` closed enums |
| 17 | `decision_status_invalid` | `decision_status` ↔ `scenario_type` mapping |
| 18 | `acceptance_path_invalid` | `clean_acceptance.acceptance_record_ref` |
| 19 | `rejection_path_invalid` | `policy_rejection.rejection_reason` / `silver_verification_passing` |
| 20 | `challenge_path_invalid` | `challenge_filed.challenge_record_ref` / `challenge_state` |
| 21 | `withdrawal_path_invalid` | `withdrawal.withdrawal_record_ref` / `withdrawal_trigger` |
| 22 | `supersession_path_invalid` | `supersession.prior_decision_ref_kind`, `prior_decision_id` resolution, `supersession_trigger`, `superseding_input_ref` |
| 23 | `non_claims_missing` | `non_claims` empty or all entries blank |
| 24 | `prohibited_gold_claim_present` | recursive scan of every string value outside `scope_limitations` / `non_claims` against the closed prohibited Gold-claim vocabulary |

### Reachability orderings

- Manifest integrity (R01) fires first.
- R02..R10 (package shape + inputs block) fire BEFORE R11 (decision set).
- R12..R17 (per-entry binding/status checks) fire AFTER R11 succeeds.
- R18..R22 fire only for entries whose `scenario_type` matches the
  path under check; each scenario path is reached by its dedicated
  reason without aliasing.
- R23 fires AFTER all entry-level checks; an empty or blank
  `non_claims` is reserved for this reason and never folds into R03.
- R24 (prohibited Gold-claim scan) fires AFTER all earlier structural
  checks succeed.
- Conformance-report byte-compare re-derivation runs LAST; any
  disagreement against a structurally valid package folds back into
  R01 (`gold_manifest_invalid`). This is intentional: there is no 25th
  public reason for bundled-report disagreement.

### supersession_path_invalid (R22) reachability

`scenario_specific_state` for `supersession` requires the closed
field `prior_decision_ref_kind ∈ {internal_decision_id,
external_decision_id}`.

- `internal_decision_id`: `prior_decision_id` MUST resolve to another
  entry's `decision_id` in the same `governed_decisions[]`. Failure
  to resolve emits `supersession_path_invalid`.
- `external_decision_id`: `prior_decision_id` references a decision
  outside this package. The verifier does NOT require resolution
  within `governed_decisions[]`.

The canonical 5-scenario fixture uses `internal_decision_id`; the
single-scenario supersession slice uses `external_decision_id`.

## Non-Claims

The v0.4.0 tooling does not certify, audit, approve, transfer, or
adjudicate the recorded governed reliance decisions. It records
deterministic local hand-authored decision state under a closed
vocabulary and validates structural shape, binding, and conformance
report byte-equality only. It does not consult any live service,
gateway, observability backend, policy engine, GRC platform, or
external registry. It is not signed and ships local hash anchors only.

## v0.4.1 Note

v0.4.1 is a narrow Gold maintenance release (Gold Decision Report
Hardening) that re-projects the unchanged v0.4.0 package body into a
deterministic local decision report and binds it under a 3-subject
manifest. v0.4.1 does not introduce a new Gold tier, is not signed,
is not a certificate, and does not extend the substance of the v0.4.0
body. The v0.4.1 release narrative
(`docs/gold/gold-decision-report-hardening-v0.4.1.md`) holds the
v0.4.1 reason surface, reachability orderings, runner architecture,
and non-claims.

## v0.4.3 Note

v0.4.3 is a narrow incremental Gold release (Gold Challenge Lifecycle
Lite) that pairs the unchanged v0.4.0 package body, v0.4.1 decision
report, and v0.4.2 policy-evaluation pair with a hand-authored
deterministic local runtime challenge-lifecycle records body and a
deterministic local lifecycle report, bound under a 7-subject manifest.
v0.4.3 does not introduce a new Gold tier, is not signed, is not a
certificate, is not federated, does not transfer reliance, does not
consult any live policy engine or live lifecycle adjudication
authority, and does not extend the substance of the v0.4.0 body,
the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair.
The v0.4.3 release narrative
(`docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md`) holds the
v0.4.3 reason surface, reachability orderings, runner and verifier
architecture, closed lifecycle vocabularies, and non-claims.

## Gold Reliance Package Index Runner (v0.4.4)

Builds a deterministic, hash-anchored local v0.4.4 Gold Reliance
Package Index by subprocess-invoking each of the four co-located
inherited runners (v0.4.0, v0.4.1, v0.4.2, v0.4.3) into its own
`child-packages/v0.4.X/` subdirectory under the v0.4.4 staging tree,
where each inherited runner writes its complete child closure (its
wrapping manifest plus every subject file the manifest references).
The v0.4.4 runner consumes exactly the inherited v0.4.3 input file
chain (`--input-package`, `--matrix-input`, `--lifecycle-input`) and
adds no new input template. The v0.4.3 child closure is built under
the corrected v0.4.3.1 baseline. Subjects [0]..[3] of the v0.4.4
wrapping manifest are the byte-stable child wrapping manifests
materialized under each `child-packages/v0.4.X/` subdirectory;
subject [4] is the v0.4.4-owned index body at the package root,
derived deterministically by re-projecting the inherited surface IDs
into a closed 7-ID identifier table.

```bash
python3 tools/gold/build_gold_reliance_package_index_v0_1_0.py \
  --input-package fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json \
  --matrix-input fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json \
  --lifecycle-input fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json \
  --manifest-id proofrail-gold-reliance-package-index-manifest-demo-001 \
  --conformance-report-id proofrail-gold-reliance-package-index-conformance-demo-001 \
  --decision-report-id proofrail-gold-decision-report-demo-001 \
  --policy-evaluation-report-id proofrail-gold-policy-evaluation-report-demo-001 \
  --challenge-lifecycle-report-id proofrail-gold-challenge-lifecycle-report-demo-001 \
  --gold-reliance-package-index-id proofrail-gold-reliance-package-index-demo-001 \
  --generated-at 2026-12-01T00:30:00Z \
  --output-dir /tmp/proofrail-v044-reliance-package-index-demo \
  --force \
  --self-validate
```

The runner stages output under a sibling directory
`<output-dir>.staging.<pid>` and atomically publishes via
`os.replace()`. With `--self-validate` the runner invokes the v0.4.4
verifier against the staged package BEFORE the atomic move; on
self-validation failure the staging directory is removed and the
destination is left untouched. The runner relays the verifier's
failure UNCHANGED with no sixth runner-only wrapper code.

### Runner-only refusal reasons (5)

The runner emits exactly the same five preflight refusal codes as
v0.4.0..v0.4.3, applied to every input-path argument BEFORE any output
directory touch:

- `runner_input_path_missing`   — flag empty or unset
- `runner_input_path_forbidden` — absolute path or contains `..`
- `runner_input_file_missing`   — path does not exist on disk
- `runner_input_read_failed`    — open/read fails or path is a directory
- `runner_input_json_invalid`   — path does not parse as JSON

The runner never wraps a verifier failure under a sixth runner-only
refusal code. With `--self-validate`, a verifier failure is relayed
verbatim from the verifier's own stdout/stderr.

## Gold Reliance Package Index Verifier (v0.4.4)

Verifies a v0.4.4 Gold Reliance Package Index by re-running the
closed 54-reason surface (48 inherited reasons R01..R48 + 6 v0.4.4-owned
reasons R49..R54) against a single `--manifest` flag.

```bash
python3 tools/gold/verify_gold_reliance_package_index_v0_1_0.py \
  --manifest /tmp/proofrail-v044-reliance-package-index-demo/gold-reliance-package-index-manifest.json
```

### Phase ordering

- **Phase 1** — manifest integrity, subject path/hash distinctness,
  cross-anchor consistency at the 5-subject index manifest layer; all
  collisions and binding mismatches at this layer fold into R01
  (`gold_manifest_invalid`).
- **Phase 2** — cross-anchor re-derivation of inherited surface IDs
  against the v0.4.4 index body (`package_id` and
  `governed_reliance_demo_id` to subject [0]; `conformance_report_id`
  to subject [1]; `decision_report_id` to subject [2]; v0.4.2 and
  v0.4.3 surface IDs to their respective inherited subjects via the
  Phase 4 subprocess relay). Failures at this layer also fold into R01.
- **Phase 3** — v0.4.4-owned index body re-derivation under six
  structural checks in the closed fixed order R49 → R50 → R52 → R53
  → R51 → R54: (1) body-is-JSON-object, (2) top-level / per-entry /
  coverage-summary shape, (3) per-entry value validity, (4)
  coverage-summary arithmetic, (5) index-body cross-anchor binding,
  (6) canonical-JSON index-fingerprint re-derivation. The six
  v0.4.4-owned reason names are enumerated in
  `docs/gold/gold-reliance-package-index-v0.4.4.md`.
- **Phase 4** — sequential subprocess invocation of each of the four
  co-located inherited verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) on
  the corresponding child wrapping-manifest path under
  `child-packages/v0.4.X/`. Each inherited verifier resolves its
  referenced subject files relative to the child manifest's directory
  using its own existing path-resolution rules. Any inherited reason
  R02..R48 surfaces UNCHANGED with no v0.4.4 wrapper. Environmental
  failures (missing, unlaunchable, or non-FAIL-non-zero-exit inherited
  verifier) surface under a non-reason-shaped `INFRA:` diagnostic on
  stderr with exit code 3.

### 7-ID pairwise-distinctness collision class

`conformance_report_id`, `decision_report_id`, `matrix_id`,
`policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`,
`challenge_lifecycle_report_id`, `gold_reliance_package_index_id`.
All 21 pairwise collisions across this class surface at the
manifest-integrity layer under R01 (`gold_manifest_invalid`); they do
NOT fold into the v0.4.4-owned R51 binding-invalid reason, which is
reserved for index-body cross-anchor mismatches.

## v0.4.4 Note

v0.4.4 is a narrow incremental Gold release (Gold Reliance Package
Index) that wraps the unchanged v0.4.3 surface under a deterministic
local 5-subject index manifest, projecting the closed 7-ID identifier
table and re-deriving an index fingerprint over canonical JSON. v0.4.4
does not introduce a new Gold tier, is not signed, is not a
certificate, is not federated, does not transfer reliance, does not
consult any live service, and does not extend the substance of the
v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation
pair, or the v0.4.3 lifecycle pair. The v0.4.4 release narrative
(`docs/gold/gold-reliance-package-index-v0.4.4.md`) holds the v0.4.4
reason surface, reachability orderings, runner and verifier
architecture, the 7-ID collision class, the TG1 allowlist discipline,
the INFRA diagnostic boundary, the test scratch path policy, and the
non-claims.
