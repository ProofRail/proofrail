# Gold Demo 001 — Minimal Gold Governed Reliance Demo (v0.4.0)

This demo is the deterministic, local Minimal Gold Governed Reliance
Demo package that ProofRail v0.4.0 derives from a single hand-authored
input:

- the canonical 5-scenario fixture
  (`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`).

It is the first Gold-tier release in the ProofRail framework. It
composes Silver-shaped inputs (Silver verification result, Silver
acceptance handoff, Silver relying-party policy pack, Silver registry
lite, Silver control crosswalk) and records 1..5 governed reliance
decisions under closed-vocabulary scenario / status / subject /
binding / action / scenario-state surfaces.

It answers a narrow question:

> Can a hand-authored Minimal Gold Governed Reliance Demo body —
> declaring up to five governed reliance decisions across the five
> recognized scenario types (clean_acceptance, policy_rejection,
> challenge_filed, withdrawal, supersession) under a closed
> vocabulary — be structurally validated against 24 ordered checks,
> paired with a deterministically re-derived conformance report (24
> pass entries, byte-identical re-derivation), and packaged alongside
> a 2-subject manifest cross-anchored by `package_id` and
> `governed_reliance_demo_id` — such that an independent Gold reviewer
> can re-run the unchanged v0.4.0 verifier and re-derive every check
> without claiming that the package constitutes a certificate, a
> signed reliance instrument, a federated acceptance, a transfer of
> reliance to any external party, a regulator or auditor approval,
> legal acceptance or enforceability, production authorization, or
> full Gold?

It does **not** answer:

- Is the package a Gold certificate?
- Is the package signed?
- Has any external party accepted the recorded reliance decisions?
- Have the recorded decisions been federated?
- Has any regulator, auditor, or third party approved the recorded
  decisions?
- Have the recorded decisions been adjudicated legally?
- Has the upstream Silver evidence been re-verified end-to-end against
  any live service?
- Is the demo production-authorized?
- Is the demo full Gold or Platinum?

## What the demo does

1. Validates the `--input-package` argv through 5 Phase A preflight
   checks (relative-path-only, no `..`, file exists, file is a
   regular file, file is valid JSON). Phase A emits only the 5
   approved runner-only refusal reasons: `runner_input_path_missing`,
   `runner_input_path_forbidden`, `runner_input_file_missing`,
   `runner_input_read_failed`, `runner_input_json_invalid`.
2. Stages output under `<output-dir>.staging.<pid>` and byte-copies
   the package body to
   `<staging>/governed-reliance-scenarios.json`.
3. Deterministically re-derives the conformance report (24 pass
   entries, one per approved verifier check) as canonical JSON bytes
   (`sort_keys=True`, `separators=(",",":"))`) with a trailing newline,
   and writes it to
   `<staging>/silver-gold-governed-reliance-conformance-report.json`.
4. Writes the 2-subject manifest at
   `<staging>/gold-governed-reliance-package-manifest.json`. The
   manifest carries `subjects[0]` = package body (role
   `governed_reliance_package`) and `subjects[1]` = conformance report
   (role `conformance_report`), each with `sha256` (`sha256:<64hex>`)
   and `size_bytes`. The manifest also carries `proofrail_release:
   gold.governed_reliance.v0.4.0`, `hash_algorithm: sha256`, and
   cross-anchored `package_id` and `governed_reliance_demo_id` fields.
5. If `--self-validate`, subprocess-invokes the v0.4.0 verifier
   against the staged manifest BEFORE the atomic publish. Any
   verifier failure is relayed UNCHANGED (the verifier's own stable
   reason is emitted; the runner does NOT wrap it in a sixth
   runner-only code). On self-validation failure the staging
   directory is removed and `<output-dir>` is left untouched.
6. Atomic publish: only AFTER a successful staging build (and, if
   `--self-validate`, a successful self-validation) does the runner
   remove an existing `--output-dir` (requires `--force`) and
   `os.replace()` the staging directory into place.

The v0.4.0 verifier runs 24 ordered checks against the 2-subject
manifest. Checks fire in the documented order with no masking: 24
structural checks against the package body and manifest, then
conformance-report parse and byte-identical re-derivation. A
re-derivation disagreement is funnelled back to `gold_manifest_invalid`;
no 25th public reason is introduced. The verifier emits only the 24
approved verifier-side failure reasons listed in the schema and
release doc. It never invents a sixth runner-only wrapper code on a
relayed failure.

## Commands

```bash
make run-gold-governed-reliance-v0-4-0
make verify-gold-governed-reliance-v0-4-0
```

The `run-gold-governed-reliance-v0-4-0` target builds the v0.4.0
package into `/tmp/proofrail-gold-governed-reliance-v0.4.0/` with
`--force --self-validate`, then runs the v0.4.0 verifier against the
published manifest.

The `verify-gold-governed-reliance-v0-4-0` target runs the dedicated
regression test, which exercises 53 ordered cases (4 positive-path + 5
single-scenario fixture build+verify + 24 canonical verifier reason
mutations + 11 duplicate manifest-invalid mutations + 6 runner-only
refusal exercises covering 5 distinct runner-only reasons (ro1, ro2,
ro2b, ro3..ro5) + 1 runner-relay-of-verifier-failure case + 1
taxonomy gate + 1 scoped sha256 snapshot).

## Package layout

```
/tmp/proofrail-gold-governed-reliance-v0.4.0/
├── governed-reliance-scenarios.json                          (subject [0])
├── silver-gold-governed-reliance-conformance-report.json     (subject [1])
└── gold-governed-reliance-package-manifest.json              (2-subject anchor)
```

## Closed scenario / status / role surface

The canonical 5-scenario fixture covers, across its five decisions:

- All five `scenario_type` values: `clean_acceptance`,
  `policy_rejection`, `challenge_filed`, `withdrawal`, `supersession`
- All five `decision_status` values: `accepted`, `rejected`,
  `challenged`, `withdrawn`, `superseded`
- All three `decision_subject.subject_type` values:
  `silver_verification_result`, `silver_acceptance_handoff`,
  `silver_evidence_bundle`
- Five distinct `policy_decision` values: `allow`, `deny`, `review`,
  `withhold`, `conditional`
- Five distinct `decision_trigger` values
- Five distinct `protected_action_id` values
- Five distinct `action_category` values
- Two distinct `action_environment` values: `demo`,
  `production_simulated`

The scenario slices cover their respective scenario in isolation. The
supersession slice uses `prior_decision_ref_kind: external_decision_id`
to exercise the "prior decision outside this package" path permitted by
the schema. The canonical fixture uses `internal_decision_id` and its
`prior_decision_id` resolves to `decision-001-accepted` inside the
same package.

## Fixture variants

| File | Decisions | Role |
|---|---|---|
| `governed-reliance-scenarios.json` | 5 | Canonical v0.4.0 Gold package: full canonical demo body covering all five recognized scenarios in natural order |
| `scenario-clean-acceptance.json` | 1 | Scenario slice covering only `clean_acceptance` |
| `scenario-policy-rejection.json` | 1 | Scenario slice covering only `policy_rejection` |
| `scenario-challenge-filed.json` | 1 | Scenario slice covering only `challenge_filed` |
| `scenario-withdrawal.json` | 1 | Scenario slice covering only `withdrawal` |
| `scenario-supersession.json` | 1 | Scenario slice covering only `supersession`; uses `prior_decision_ref_kind: external_decision_id` |

## Non-claims

- The demo is not full Gold and is not Platinum.
- The demo is not signed and ships local hash anchors only.
- The demo is not a certificate, not federated, and not a transfer of
  reliance to any external party.
- The demo does not claim regulator approval, auditor approval,
  third-party endorsement, legal acceptance, legal adjudication, legal
  enforceability, or compliance certification.
- The demo does not claim production authorization, production
  governance, production PKI, audit readiness, or control operating /
  design effectiveness.
- The demo does not consult any live service, gateway, observability
  backend, policy engine, GRC platform, or external registry.
- The demo does not perform end-to-end re-verification of the upstream
  Silver evidence chain; the five `inputs.*` blocks are structural
  pointers under closed input-type and ref grammar only.
- The demo is scoped to one demo relying party and one demo scenario
  set; it does not represent runtime truth.
