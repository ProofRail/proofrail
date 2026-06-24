# Silver Demo 013 — Control Crosswalk + Protected Action Catalog (v0.3.6)

This demo is the deterministic, local Silver Control Crosswalk +
Protected Action Catalog package that ProofRail v0.3.6 derives from a
single hand-authored input:

- the canonical control pack fixture
  (`fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/control-pack.json`).

It answers a narrow question:

> Can a hand-authored control pack — declaring a closed-vocabulary
> protected action catalog and a closed crosswalk of those actions to
> ProofRail-internal evidence artifacts under conservative claim
> verbs — be structurally validated against 24 ordered checks under a
> closed enum / posture / artifact-type vocabulary, paired with a
> deterministically re-derived conformance report (24 pass entries,
> byte-identical re-derivation), and packaged alongside a 2-subject
> manifest — such that an independent Silver reviewer can re-run the
> unchanged v0.3.6 verifier and re-derive every check without
> claiming that the catalog has been approved by a regulator,
> auditor, or third party, that it maps to any external framework,
> that it demonstrates control design or operating effectiveness, or
> that it re-evaluates any specific upstream Silver evidence?

It does **not** answer:

- Has the catalog been approved by a regulator, auditor, or third
  party?
- Is the catalog mapped to SOC 2 / ISO 27001 / NIST 800-53 / PCI DSS
  / HIPAA or any other external framework?
- Is control design effectiveness or control operating effectiveness
  demonstrated?
- Has any specific upstream Silver evidence (composed-gateway,
  trace-binding, acceptance record, revocation-challenge drill,
  etc.) been re-evaluated against the crosswalk in this demo?
- Has any reliance instrument been issued, transferred, or accepted
  against the catalog?
- Is the catalog legally enforceable?
- Is the catalog Gold-conformant?

## What the demo does

1. Validates the `--input-pack` argv through 5 Phase A preflight
   checks (relative-path-only, no `..`, file exists, file is a
   regular file, file is valid JSON). Phase A emits only the 5
   approved runner-only refusal reasons: `runner_input_path_missing`,
   `runner_input_path_forbidden`, `runner_input_file_missing`,
   `runner_input_read_failed`, `runner_input_json_invalid`.
2. Stages output under `<output-dir>.staging.<pid>` and byte-copies
   the control pack to `<staging>/control-pack.json`.
3. Deterministically re-derives the conformance report (24 pass
   entries, one per approved verifier check) as canonical JSON
   bytes (`sort_keys=True`, `separators=(",",":"))` with a trailing
   newline, and writes it to
   `<staging>/silver-control-crosswalk-protected-action-catalog-conformance-report.json`.
4. Writes the 2-subject manifest at
   `<staging>/silver-control-crosswalk-protected-action-catalog-manifest.json`.
   The manifest carries `subjects[0]` = control pack (role
   `control_pack`) and `subjects[1]` = conformance report (role
   `conformance_report`), each with `sha256` (`sha256:<64hex>`) and
   `size_bytes`. The manifest also carries `proofrail_release:
   silver.control_crosswalk.v0.3.6`, `hash_algorithm: sha256`, and a
   `control_pack_id` cross-anchored to the control pack body.
5. If `--self-validate`, subprocess-invokes the v0.3.6 verifier
   against the staged manifest BEFORE the atomic publish. Any
   verifier failure is relayed UNCHANGED (the verifier's own stable
   reason is emitted; the runner does NOT wrap it in a sixth
   runner-only code). On self-validation failure the staging
   directory is removed and `<output-dir>` is left untouched.
6. Atomic publish: only AFTER a successful staging build (and, if
   `--self-validate`, a successful self-validation) does the runner
   remove an existing `--output-dir` (requires `--force`) and
   `os.replace()` the staging directory into place.

The v0.3.6 verifier runs 24 ordered checks across 25 ordered
execution steps against the 2-subject manifest. Checks fire in the
documented order with no masking: 24 structural checks against the
control pack and manifest, then conformance-report parse and
byte-identical re-derivation. A re-derivation disagreement is
funnelled back to `control_pack_manifest_invalid`; no
twenty-fifth public reason is introduced. The verifier emits only
the 24 approved verifier-side failure reasons listed in the schema
and release doc. It never invents a sixth runner-only wrapper code
on a relayed failure.

## Commands

```bash
make run-silver-control-crosswalk-protected-action-catalog-v0-3-6
make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
```

The `run-silver-control-crosswalk-protected-action-catalog-v0-3-6`
target builds the v0.3.6 package into
`/tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/`
with `--force --self-validate`, then runs the v0.3.6 verifier against
the published manifest.

The `verify-silver-control-crosswalk-protected-action-catalog-v0-3-6`
target runs the dedicated regression test, which exercises 47 ordered
cases (4 positive-path + 24 canonical verifier reason mutations + 11
duplicate manifest-invalid mutations + 5 runner-only refusal cases +
1 runner-relay-of-verifier-failure case + 1 taxonomy gate + 1 scoped
sha256 snapshot).

## Control crosswalk + protected action catalog package layout

```
/tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/
├── control-pack.json                                                                (subject [0])
├── silver-control-crosswalk-protected-action-catalog-conformance-report.json        (subject [1])
└── silver-control-crosswalk-protected-action-catalog-manifest.json                  (2-subject anchor)
```

## Closed enum surface

The control pack body is governed by these closed enum vocabularies
(declared in
`schemas/silver-control-crosswalk-protected-action-catalog-v0.1.0.md`
and enforced inside the verifier; see also the three fixture
variants):

| Field path | Closed enum |
|---|---|
| `document_type` | `proofrail.silver.control_crosswalk_protected_action_catalog` |
| `schema_version` | `v0.1.0` |
| `profile` | `silver.control_crosswalk.v0.3.6` |
| catalog entry `category` | `financial`, `vendor`, `data`, `deployment`, `identity`, `infrastructure`, `communication`, `policy`, `safety`, `other` |
| catalog entry `environment_scope` | `production`, `staging`, `development`, `multi_environment`, `out_of_scope` |
| catalog entry `actor_scope` | `human`, `agent`, `system`, `mixed` |
| `authority.posture` | `principal_only`, `joint_principal`, `scoped_delegation`, `delegation_with_break_glass` |
| `risk_boundary.risk_class` | `critical`, `high`, `medium`, `low` |
| crosswalk entry `artifact_type` | closed 43-entry ProofRail artifact_type set |
| crosswalk entry `relationship` | `declares`, `mediates`, `binds_trace`, `records_acceptance`, `records_review`, `records_handoff`, `records_inspection`, `records_authority`, `records_attestation`, `records_revocation`, `records_drill` |
| crosswalk entry `claim.verb` | `may_inform`, `may_evidence`, `may_support` |
| `control_limitations[].domain` | `control_decision`, `framework_mapping`, `version_binding`, `evidence_scope`, `governance_scope` |
| `dependency_references[].reference_type` | `upstream_silver_profile`, `upstream_silver_artifact`, `upstream_silver_runner` |
| `version_bindings[].upstream_id` | closed Silver upstream_id set |

## Fixture variants

| File | Variant |
|---|---|
| `control-pack.json` | Canonical pack with five protected actions and five crosswalk entries (one per major v0.2.x/v0.3.x artifact_type family) |
| `control-pack-with-dependencies.json` | Exercises non-empty `dependency_references` across all three `reference_type` values |
| `control-pack-with-limitations.json` | Exercises a full `control_limitations` block plus exhaustive `non_claims` |

## Non-claims

- The control crosswalk + protected action catalog package is not
  a regulator, auditor, or third-party endorsement.
- The package is not a SOC 2, ISO 27001, NIST 800-53, PCI DSS,
  HIPAA, or any other external framework mapping.
- The package is not an opinion on control design effectiveness or
  control operating effectiveness.
- The packaged conformance report describes only that the control
  pack satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any specific upstream Silver
  evidence.
- v0.3.6 does not re-evaluate the referenced composed-gateway
  evidence, trace-binding evidence, acceptance record, revocation-
  challenge drill, or any other upstream Silver evidence against
  the catalog. References are structural pointers only.
- v0.3.6 does not issue, transfer, or accept any reliance
  instrument against the catalog.
- The v0.3.6 package is unsigned: it ships local hash anchors only.
- v0.3.6 does not extend the substance of any earlier-release Silver
  evidence, does not authorize production reliance, is not legally
  enforceable, is not a Gold artifact, and does not advance the
  Gold boundary.
