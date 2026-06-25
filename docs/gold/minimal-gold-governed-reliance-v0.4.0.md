# Minimal Gold Governed Reliance Demo — v0.4.0

**Status:** Draft / ProofRail v0.4.0 — first Gold-tier release
**Release thesis:** ProofRail v0.4.0 introduces the first Gold-tier
deterministic local evidence primitive — a *Minimal Gold Governed
Reliance Demo package* — composed from already-released Silver-shaped
inputs (Silver verification result, Silver acceptance handoff, Silver
relying-party policy pack, Silver registry lite, Silver control
crosswalk) and a hand-authored set of 1..5 governed reliance decisions
under closed scenario / status / subject / binding / action vocabularies.
The package is paired with a byte-for-byte re-derivable 24-entry
conformance report and a 2-subject manifest cross-anchored by
`package_id` and `governed_reliance_demo_id`. An independent reviewer
can re-run the unchanged v0.4.0 verifier against the manifest and
re-derive every structural check — without claiming that the package
constitutes a certificate, a signed reliance instrument, a federated
acceptance, a transfer of reliance to any external party, a regulator
or auditor approval, legal acceptance or enforceability, production
authorization, or full Gold.

---

## v0.4.0 thesis

> A package owner can hand-author a structured local Minimal Gold
> Governed Reliance Demo body declaring at most five governed reliance
> decisions over Silver-shaped inputs under closed scenario_type,
> decision_status, subject_type, policy_decision, registry binding,
> action_scope, scenario-specific-state, and trigger vocabularies; the
> v0.4.0 runner can byte-copy the package body into a deterministic
> local 2-subject layout alongside a re-derivable conformance report
> with 24 pass entries; and the v0.4.0 verifier can re-run 24 ordered
> structural checks on the package body and byte-compare the re-derived
> report against the bundled report — while preserving the boundary
> that v0.4.0 does **not** assert any signed reliance instrument,
> certificate, federated acceptance, transferred reliance, regulator or
> auditor approval, legal acceptance, legal enforceability, production
> authorization, audit readiness, control operating effectiveness,
> runtime truth, or full Gold.

## Governed reliance demo boundary

> A v0.4.0 Minimal Gold Governed Reliance Demo package is **not** a
> certificate; it is **not** signed; it is **not** federated; it is
> **not** a transfer of reliance to any external party; it is **not** a
> regulator action, an auditor action, or a third-party endorsement;
> it is **not** legal acceptance, legal enforceability, or legal
> adjudication; it is **not** production authorization, production
> governance, or production PKI; it is **not** an audit-readiness
> assertion or a control-effectiveness assertion; it is **not** a
> runtime-truth oracle; it is **not** full Gold. It is a deterministic
> local evidence artifact recording that a package owner has
> hand-authored a structured set of governed reliance decisions
> composed from Silver-shaped inputs, that the structure satisfies a
> fixed set of 24 ordered structural checks under a closed-vocabulary
> surface, and that an independent reviewer can re-derive the same
> conformance report byte-for-byte from the package body alone.

v0.4.0 answers:

```
Can a package owner hand-author a structured local Minimal Gold
  Governed Reliance Demo body referencing five Silver-shaped inputs
  (silver_verification, silver_handoff, policy_pack, registry_lite,
  control_crosswalk) under closed input-type and input-ref shape?
Can the body declare 1..5 governed reliance decisions in natural
  order with unique scenario_type values drawn from the closed
  5-scenario set (clean_acceptance, policy_rejection, challenge_filed,
  withdrawal, supersession)?
Can each decision bind a decision_subject (closed subject_type), a
  policy_binding (closed policy_decision under the package's
  policy_pack), a registry_binding (closed decision_authority_role
  under the package's registry_lite relying_party), and an
  action_scope (closed protected_action_id / action_category /
  action_environment)?
Can each scenario_type be paired exactly once with a matching
  decision_status under a closed scenario -> status mapping, and with
  a matching scenario_specific_state block (acceptance_record_ref;
  rejection_reason + silver_verification_passing; challenge_record_ref
  + challenge_state; withdrawal_record_ref + withdrawal_trigger;
  prior_decision_ref_kind + prior_decision_id + supersession_trigger
  + superseding_input_ref)?
Can the runner byte-copy the package body into a deterministic local
  2-subject layout (governed-reliance-scenarios.json plus
  silver-gold-governed-reliance-conformance-report.json)?
Can the runner deterministically re-derive a 24-entry conformance
  report whose canonical-JSON byte image depends only on the package
  body?
Can the runner refuse five distinct preflight failures (path missing,
  path forbidden, file missing, read failed, JSON invalid) with stable
  runner-only refusal reasons that the downstream verifier never
  re-emits, and never wrap a verifier failure in a sixth runner-only
  code?
Can the runner relay the v0.4.0 verifier's own failure UNCHANGED on
  --self-validate, leaving the destination untouched?
Can the verifier independently re-run 24 ordered structural checks
  on the package body and the manifest, including:
    manifest integrity and cross-anchor (package_id,
      governed_reliance_demo_id),
    package body shape (document_type, schema_version,
      scope_limitations),
    profile (gold.governed_reliance.v0.4.0),
    package identity grammar (package_id, governed_reliance_demo_id,
      relying_party identity),
    five inputs blocks (silver_verification, silver_handoff,
      policy_pack, registry_lite, control_crosswalk) under closed
      input_type and input_ref grammar,
    governed_decisions[] (1..5 entries, unique scenario_type,
      natural-order placement),
    per-entry binding and status under closed enums,
    scenario-path-specific state (acceptance / rejection / challenge /
      withdrawal / supersession),
    non_claims presence,
    recursive prohibited-Gold-claim scan over all string values
      outside scope_limitations and non_claims,
    bundled report byte-identical re-derivation as a non-masking
      final step that folds any disagreement back into
      gold_manifest_invalid?
```

## Package layout

The runtime layout at `/tmp/proofrail-gold-governed-reliance-v0.4.0/`
holds exactly three files:

```
<output-dir>/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
└── gold-governed-reliance-package-manifest.json              (2-subject anchor)
```

The manifest carries:

- `document_type: proofrail.gold.governed_reliance_package_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.governed_reliance.v0.4.0`
- `hash_algorithm: sha256`
- `manifest_id`, `report_id`, `generated_at`
- `package_id` and `governed_reliance_demo_id`, both cross-anchored
  to the package body's matching fields
- `subjects[0]`: role `governed_reliance_package`, path
  `governed-reliance-scenarios.json`
- `subjects[1]`: role `conformance_report`, path
  `silver-gold-governed-reliance-conformance-report.json`

Each subject carries a `sha256:<64hex>` recomputed sha256 and
`size_bytes`. The manifest does NOT include a self-referential
manifest-hash subject; v0.4.0 ships local hash anchors only.

## Closed enum surface

The package body is governed by these closed enum vocabularies
(declared in `schemas/gold-governed-reliance-package-v0.1.0.md` and
enforced inside the verifier):

| Field path | Closed enum |
|---|---|
| `document_type` | `proofrail.gold.governed_reliance_package` |
| `schema_version` | `v0.1.0` |
| `profile` | `gold.governed_reliance.v0.4.0` |
| `inputs.silver_verification.input_type` | `silver_verification_result` |
| `inputs.silver_verification.expected_status` | `pass`, `fail`, `skipped` |
| `inputs.silver_handoff.input_type` | `silver_acceptance_handoff` |
| `inputs.silver_handoff.expected_handoff_posture` | `for_demo_scope`, `review_required_before_reuse`, `not_reusable_without_governed_review` |
| `inputs.policy_pack.input_type` | `silver_relying_party_policy_pack` |
| `inputs.registry_lite.input_type` | `silver_registry_lite` |
| `inputs.control_crosswalk.input_type` | `silver_control_crosswalk` |
| `governed_decisions[].scenario_type` | `clean_acceptance`, `policy_rejection`, `challenge_filed`, `withdrawal`, `supersession` |
| `governed_decisions[].decision_status` | `accepted`, `rejected`, `challenged`, `withdrawn`, `superseded` |
| `decision_subject.subject_type` | `silver_verification_result`, `silver_acceptance_handoff`, `silver_evidence_bundle` |
| `policy_binding.policy_decision` | `allow`, `deny`, `review`, `withhold`, `conditional` |
| `registry_binding.decision_authority_role` | `relying_party`, `policy_authority`, `protected_action_authority` |
| `action_scope.protected_action_id` | closed action id set drawn from the v0.3.6 catalog (`approve_vendor`, `release_funds`, `grant_access`, `publish_record`, `disclose_record`) |
| `action_scope.action_category` | `vendor_approval`, `financial_release`, `access_grant`, `record_publish`, `record_disclose` |
| `action_scope.action_environment` | `demo`, `production_simulated` |
| `decision_trigger` | `silver_verification_pass`, `policy_fail`, `challenge_filed`, `withdrawal_recorded`, `updated_evidence_received` |
| `scenario_specific_state.prior_decision_ref_kind` (supersession only) | `internal_decision_id`, `external_decision_id` |

## Decision-status / scenario-type mapping (closed)

The verifier enforces this 1-to-1 mapping at check R17:

| `scenario_type` | `decision_status` |
|---|---|
| `clean_acceptance` | `accepted` |
| `policy_rejection` | `rejected` |
| `challenge_filed` | `challenged` |
| `withdrawal` | `withdrawn` |
| `supersession` | `superseded` |

## 24 verifier reason mapping

| # | Reason | Trigger |
|---|---|---|
| 01 | `gold_manifest_invalid` | manifest integrity, subject paths, hashes, cross-anchor, post-structural conformance-report byte-compare |
| 02 | `gold_package_not_object` | package body is not a JSON object |
| 03 | `gold_package_schema_invalid` | top-level `document_type` / `schema_version` / `scope_limitations` shape; missing required top-level fields fold here |
| 04 | `gold_profile_unsupported` | `profile` outside `{gold.governed_reliance.v0.4.0}` |
| 05 | `gold_package_identity_invalid` | grammar of `package_id` / `governed_reliance_demo_id` / `relying_party.identity_id` / `relying_party.registry_ref` |
| 06 | `silver_verification_input_invalid` | `inputs.silver_verification` shape / closed `expected_status` |
| 07 | `silver_handoff_input_invalid` | `inputs.silver_handoff` shape / closed `expected_handoff_posture` |
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

## 5 runner-only refusal reasons

The runner emits exactly these five preflight refusal codes against
`--input-package` BEFORE any output directory touch:

| Reason | Trigger |
|---|---|
| `runner_input_path_missing` | flag empty or unset |
| `runner_input_path_forbidden` | absolute path or contains `..` |
| `runner_input_file_missing` | relative path does not exist on disk |
| `runner_input_read_failed` | open/read fails or path is a directory |
| `runner_input_json_invalid` | path does not parse as JSON |

The runner never wraps a verifier failure under a sixth runner-only
refusal code. With `--self-validate`, a verifier failure is relayed
verbatim from the verifier's own stdout/stderr.

## Reachability ordering

- Manifest integrity (R01) fires first.
- R02..R10 (package shape + inputs block) fire BEFORE R11 (decision
  set).
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
  R01 (`gold_manifest_invalid`). This is intentional: there is no
  25th public reason for bundled-report disagreement.

## Supersession resolution

`scenario_specific_state` for `supersession` requires the closed field
`prior_decision_ref_kind ∈ {internal_decision_id, external_decision_id}`.

- `internal_decision_id`: `prior_decision_id` MUST resolve to another
  entry's `decision_id` in the same `governed_decisions[]`. Failure
  to resolve emits `supersession_path_invalid`.
- `external_decision_id`: `prior_decision_id` references a decision
  outside this package. The verifier does NOT require resolution
  within `governed_decisions[]`.

The canonical 5-scenario fixture uses `internal_decision_id` and its
`prior_decision_id` resolves to `decision-001-accepted` inside the
same package. The single-scenario supersession slice uses
`external_decision_id`.

## Prohibited Gold-claim vocabulary

The R24 scan is a case-insensitive recursive walk of every string
value in the package body OUTSIDE `scope_limitations` and `non_claims`
against a closed set of prohibited positive tokens including:

- `signed gold reliance`, `gold reliance certificate`,
  `gold reliance signed`, `gold certificate`, `gold certified`,
  `gold accepted`, `full gold`
- `federated reliance`, `federated trust`, `transferred trust`,
  `trust transferred`, `transferred reliance`, `reliance transferred`
- `regulator approved`, `regulator approval`, `approved by regulator`,
  `auditor approved`, `auditor approval`, `approved by auditor`,
  `audit ready`, `audit readiness`, `audited`
- `legally accepted`, `legally enforceable`, `legal enforceability`,
  `legal adjudication`, `legally adjudicated`
- `production authorized`, `production authorization`,
  `production approved`, `production ready`, `production governance`,
  `production pki`, `certificate authority`, `certification authority`
- `control operating effective`, `control design effective`,
  `compliance certified`, `compliance ready`, `runtime truth`,
  `proves runtime truth`

The first match emits `prohibited_gold_claim_present` with a
`<path>: '<token>'` detail.

## Commands

```bash
make run-gold-governed-reliance-v0-4-0
make verify-gold-governed-reliance-v0-4-0
make verify-gold-all
```

`run-gold-governed-reliance-v0-4-0` builds the v0.4.0 package into
`/tmp/proofrail-gold-governed-reliance-v0.4.0/` with `--force
--self-validate`, then runs the v0.4.0 verifier against the
published manifest.

`verify-gold-governed-reliance-v0-4-0` runs the dedicated regression
test (`tests/test_gold_governed_reliance_v0_4_0.sh`), which exercises
53 ordered cases:

- 4 positive-path (PP1–PP4)
- 5 single-scenario fixture build+verify (SC1–SC5)
- 24 canonical verifier reason mutations (case01–case24)
- 11 duplicate manifest-invalid mutations (dup01–dup11) all routed
  to `gold_manifest_invalid`
- 6 runner-only refusal exercises (ro1, ro2, ro2b, ro3..ro5) covering
  the 5 distinct runner-only reasons with
  `runner_input_path_forbidden` exercised twice
- 1 runner-relay-of-verifier-failure case (rel01)
- 1 taxonomy gate (TG1)
- 1 scoped sha256 snapshot (SS)

`verify-gold-all` chains the v0.4.0 verifier into the framework-wide
chain at the end of the existing Silver chain.

## Fixture variants

| File | Decisions | Role |
|---|---|---|
| `governed-reliance-scenarios.json` | 5 | Canonical v0.4.0 Gold package: full canonical demo body covering all five recognized scenarios in natural order |
| `scenario-clean-acceptance.json` | 1 | Scenario slice covering only `clean_acceptance` |
| `scenario-policy-rejection.json` | 1 | Scenario slice covering only `policy_rejection` |
| `scenario-challenge-filed.json` | 1 | Scenario slice covering only `challenge_filed` |
| `scenario-withdrawal.json` | 1 | Scenario slice covering only `withdrawal` |
| `scenario-supersession.json` | 1 | Scenario slice covering only `supersession`; uses `prior_decision_ref_kind: external_decision_id` |

The single-scenario slices exercise scenario-isolated paths under the
schema's 1..5 entry tolerance; they are not a substitute for the
canonical fixture.

## Non-claims

- The v0.4.0 package is not full Gold and is not Platinum.
- The v0.4.0 package is not signed and ships local hash anchors only.
- The v0.4.0 package is not a certificate, not federated, and not a
  transfer of reliance to any external party.
- The v0.4.0 package does not claim regulator approval, auditor
  approval, third-party endorsement, legal acceptance, legal
  adjudication, legal enforceability, or compliance certification.
- The v0.4.0 package does not claim production authorization,
  production governance, production PKI, audit readiness, or control
  operating / design effectiveness.
- The v0.4.0 package does not consult any live service, gateway,
  observability backend, policy engine, GRC platform, or external
  registry; it validates structural shape, binding, and conformance
  report byte-equality only.
- The v0.4.0 package does not perform end-to-end re-verification of
  the upstream Silver evidence chain; the five `inputs.*` blocks are
  structural pointers under closed input-type and ref grammar only.
- The v0.4.0 package is scoped to one demo relying party and one demo
  scenario set; it does not represent runtime truth.
