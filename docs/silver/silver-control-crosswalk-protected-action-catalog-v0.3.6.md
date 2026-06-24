# Silver Control Crosswalk + Protected Action Catalog — v0.3.6

**Status:** Draft / ProofRail v0.3.6
**Release thesis:** ProofRail v0.3.6 introduces a deterministic local
Silver evidence primitive — a *control crosswalk + protected action
catalog* — paired with a byte-for-byte re-derivable *conformance
report* and a 2-subject manifest. An independent Silver reviewer can
re-run the unchanged v0.3.6 verifier against the manifest and re-derive
every structural check — without claiming that the control pack has
been approved by a regulator, auditor, or third party, that any control
design or operating effectiveness has been demonstrated, that any
specific upstream Silver evidence has been re-evaluated against the
catalog, or that any reliance instrument has been issued, transferred,
or accepted.

---

## v0.3.6 thesis

> A package owner can hand-author a structured local control pack that
> declares a closed-vocabulary protected action catalog and a closed
> crosswalk of those actions to ProofRail-internal evidence artifacts
> under conservative claim verbs; the v0.3.6 runner can byte-copy the
> control pack into a deterministic 2-subject package alongside a
> re-derivable conformance report with 24 pass entries; and the v0.3.6
> verifier can re-run 24 ordered structural checks on the control pack
> and byte-compare the re-derived report against the bundled report —
> while preserving the boundary that v0.3.6 does **not** assert
> compliance with any external framework, does **not** assert control
> design effectiveness or operating effectiveness, does **not**
> re-evaluate the referenced upstream Silver evidence in this release,
> does **not** issue, transfer, or accept any reliance instrument, and
> does **not** authorize production reliance.

## Control crosswalk + protected action catalog boundary

> A v0.3.6 control crosswalk + protected action catalog package is
> **not** a regulator action, an auditor finding, a SOC 2 / ISO / NIST
> / PCI / HIPAA mapping, a control design or operating effectiveness
> opinion, a certification, a Gold artifact, an upstream Silver
> evidence re-evaluation, or an authorization for production reuse. It
> is a deterministic local evidence artifact recording that a package
> owner has hand-authored a structured catalog and crosswalk, that the
> structure satisfies a fixed set of 24 ordered structural checks, and
> that an independent reviewer can re-derive the same conformance
> report byte-for-byte from the control pack alone.

v0.3.6 answers:

```
Can a package owner hand-author a structured local control pack
  declaring a non-empty protected action catalog and a non-empty
  crosswalk from those actions to ProofRail-internal evidence
  artifacts under a closed artifact_type vocabulary and a closed
  relationship vocabulary?
Can the runner byte-copy the control pack into a deterministic local
  2-subject package?
Can the runner deterministically re-derive a 24-entry conformance
  report whose canonical-JSON byte image depends only on the control
  pack?
Can the runner refuse five distinct preflight failures
  (path missing, path forbidden, file missing, read failed, JSON
  invalid) with stable runner-only refusal reasons that the
  downstream verifier never re-emits?
Can the runner relay the v0.3.6 verifier's own failure UNCHANGED on
  --self-validate, without wrapping it in a sixth runner-only code?
Can the verifier independently re-run 24 ordered structural checks
  on the control pack and the manifest, including:
    document_type / schema_version / profile sanity,
    package_owner / relying_party / catalog_authority identity,
    protected_action_catalog non-empty list,
    each catalog entry's description / category / environment_scope
      / actor_scope under closed enums,
    action_id grammar (lowercase dotted identifier),
    authority block (closed posture enum, delegation boolean,
      scoped_principals non-empty list),
    risk_boundary block (closed risk_class enum, blast_radius,
      rationale),
    control_crosswalk non-empty list,
    each crosswalk entry's mapping_id / action_id / artifact_type /
      artifact_path / relationship / control_concept_id /
      control_objective / claim verb + scope_text,
    catalog/crosswalk consistency (every crosswalk action_id is in
      the catalog),
    proofrail_artifact_type in the closed 43-entry repo-derived set,
    artifact_path relative and free of `..`,
    relationship in the closed evidence-relationship enum,
    control_concept_id grammar,
    control_objective non-empty,
    claim verb in the closed claim-verb set (`may_inform`,
      `may_evidence`, `may_support`),
    control_limitations entries (closed domain enum),
    dependency_references entries (closed reference_type enum,
      upstream_id / upstream_version structure),
    version_bindings entries (upstream_id / upstream_version,
      closed upstream_id set),
    scope_limitations and non_claims presence,
    a 32-token prohibited-claim guard outside scope_limitations,
      non_claims, and control_limitations?
Can the verifier byte-compare the bundled conformance report against
  a re-derivation drawn solely from the verified control pack and
  reject any disagreement?
```

v0.3.6 does **not** answer:

```
Is the control pack mapped to SOC 2 / ISO 27001 / NIST 800-53 / PCI
  DSS / HIPAA or any other external framework?
Has the control pack been approved by a regulator?
Has the control pack been approved by an auditor?
Has the control pack been endorsed by any third party?
Are the protected actions in the catalog controlled effectively at
  runtime in production?
Has any specific upstream Silver evidence (composed-gateway,
  trace-binding, acceptance-record, revocation-challenge drill)
  been re-evaluated against the crosswalk in this release?
Has any reliance instrument been issued, transferred, or accepted
  against this catalog?
Is the control pack legally enforceable on the package owner or the
  relying party?
Is the control pack Gold-conformant?
```

---

## Schemas

Three new v0.1.0 schemas ship with v0.3.6:

```
schemas/silver-control-crosswalk-protected-action-catalog-v0.1.0.md
schemas/silver-control-crosswalk-protected-action-catalog-manifest-v0.1.0.md
schemas/silver-control-crosswalk-protected-action-catalog-conformance-report-v0.1.0.md
```

### Control pack (`proofrail.silver.control_crosswalk_protected_action_catalog`)

The hand-authored evidence primitive. Required top-level fields:

```
document_type, schema_version, profile, control_pack_id,
package_owner, relying_party, catalog_authority,
protected_action_catalog, control_crosswalk,
control_limitations, dependency_references, version_bindings,
scope_limitations, non_claims
```

### Manifest (`proofrail.silver.control_crosswalk_protected_action_catalog_manifest`)

A 2-subject anchor over the control pack and the conformance report
in fixed roles and fixed order:

```
[0] control-pack.json                                                                role=control_pack
[1] silver-control-crosswalk-protected-action-catalog-conformance-report.json        role=conformance_report
```

Each subject carries `sha256` (`sha256:<64hex>`) and `size_bytes`.
The manifest carries `proofrail_release: silver.control_crosswalk.v0.3.6`,
`hash_algorithm: sha256`, and a `control_pack_id` that the verifier
cross-anchors against the control pack body. There is no
self-referential manifest hash subject; the manifest is itself the
anchor.

### Conformance report (`proofrail.silver.control_crosswalk_protected_action_catalog_conformance_report`)

A re-derivable record with 24 pass entries (one per approved verifier
check). The runner emits the report as canonical JSON bytes
(`sort_keys=True`, `separators=(",",":"))` with a trailing newline)
so the verifier can byte-compare its own re-derivation against the
bundled bytes.

---

## Verifier — 24 stable failure reasons (verifier-side)

The v0.3.6 verifier runs 24 ordered checks across 25 ordered
execution steps in fixed order with no masking. Each check emits
exactly one stable failure reason; the verifier never invents a sixth
wrapper code on a relayed failure.

| Check | Reason |
|---|---|
| `check_01` | `control_pack_manifest_invalid` |
| `check_02` | `control_pack_not_object` |
| `check_03` | `control_pack_schema_invalid` |
| `check_04` | `control_pack_profile_unsupported` |
| `check_05` | `control_pack_identity_invalid` |
| `check_06` | `protected_action_catalog_invalid` |
| `check_07` | `protected_action_entry_invalid` |
| `check_08` | `protected_action_identifier_invalid` |
| `check_09` | `protected_action_scope_invalid` |
| `check_10` | `protected_action_authority_invalid` |
| `check_11` | `protected_action_risk_boundary_invalid` |
| `check_12` | `control_crosswalk_invalid` |
| `check_13` | `crosswalk_entry_invalid` |
| `check_14` | `catalog_crosswalk_consistency_invalid` |
| `check_15` | `proofrail_artifact_reference_invalid` |
| `check_16` | `evidence_relationship_invalid` |
| `check_17` | `control_concept_reference_invalid` |
| `check_18` | `control_objective_invalid` |
| `check_19` | `control_claim_invalid` |
| `check_20` | `control_limitation_invalid` |
| `check_21` | `dependency_reference_invalid` |
| `check_22` | `version_binding_invalid` |
| `check_23` | `non_claims_missing` |
| `check_24` | `prohibited_compliance_claim_present` |

After the 24 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected canonical-JSON byte image from the verified control pack,
and byte-compares the two. Disagreement surfaces as the verifier-side
reason `control_pack_manifest_invalid` (subject [1] does not describe
a passing verification of this control pack). This is the
non-masking funnel: no twenty-fifth public reason is introduced.

The verifier also cross-anchors `manifest.control_pack_id` against
the control pack body's `control_pack_id`; disagreement surfaces as
`control_pack_manifest_invalid`.

---

## Runner — 5 stable runner-only refusal reasons

The runner's Phase A preflight validates the `--input-pack` argv
under five ordered, mutually exclusive checks. Each emits a single,
distinct runner-only refusal reason, and the runner never touches
the output directory or staging sibling on refusal:

| Phase A check | Reason |
|---|---|
| argv missing or empty | `runner_input_path_missing` |
| absolute path or contains `..` | `runner_input_path_forbidden` |
| relative path does not exist on disk | `runner_input_file_missing` |
| path is a directory or unreadable | `runner_input_read_failed` |
| file is not valid UTF-8 JSON | `runner_input_json_invalid` |

On `--self-validate` the runner subprocess-invokes the v0.3.6
verifier against the staged manifest BEFORE the atomic publish.
**The runner relays the verifier's OWN stable reason UNCHANGED.** It
does NOT wrap a verifier failure in a sixth runner-only code. The
staging directory is removed on self-validation failure and
`--output-dir` is left untouched. There is no
`runner_self_validation_failed` code anywhere in the v0.3.6
taxonomy; the regression test explicitly asserts that no such
sixth code is ever emitted.

---

## Closed enum surface

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
| crosswalk entry `artifact_type` | the closed 43-entry ProofRail artifact_type set (Bronze claim, Bronze evidence bundle manifest, signed bundle assertion, revocation list, verification report, verifier output attestation, multi-principal authority fixture / decision report / harness manifest, trust-boundary demo package manifest, evidence-source adapter, composed-gateway evidence manifest, relying-party acceptance record, revocation-challenge drill manifest, acceptance-handoff manifest, handoff-inspection manifest, trace-binding manifest, adapter-pilot manifest, profile-conformance handoff manifest, relying-party policy pack manifest, plus the v0.3.6 manifest itself, etc.) |
| crosswalk entry `relationship` | `declares`, `mediates`, `binds_trace`, `records_acceptance`, `records_review`, `records_handoff`, `records_inspection`, `records_authority`, `records_attestation`, `records_revocation`, `records_drill` |
| crosswalk entry `claim.verb` | `may_inform`, `may_evidence`, `may_support` |
| `control_limitations[].domain` | `control_decision`, `framework_mapping`, `version_binding`, `evidence_scope`, `governance_scope` |
| `dependency_references[].reference_type` | `upstream_silver_profile`, `upstream_silver_artifact`, `upstream_silver_runner` |
| `version_bindings[].upstream_id` | `silver.composed_gateway_evidence`, `silver.trace_binding_profile`, `silver.relying_party_policy_pack`, `silver.acceptance_handoff`, `silver.handoff_inspection`, `silver.revocation_challenge_drill`, `silver.adapter_pilot_package`, `silver.relying_party_acceptance_record` |

---

## Prohibited-compliance-claim guard

The verifier's recursive scan rejects any string value OUTSIDE
`scope_limitations`, `non_claims`, and `control_limitations` that
contains any of these 32 forbidden positive tokens (case-insensitive
substring match):

```
certified, certification, compliant, compliance,
soc 2, soc2, iso 27001, iso27001, nist 800-53, nist800-53,
pci dss, pci-dss, hipaa,
regulator approved, auditor approved,
control design effective, control operating effective,
control design effectiveness, control operating effectiveness,
audit ready, audit-ready, audited,
production approved, production authorized,
production ready, production-ready,
legally enforceable, legally binding,
trust transferred, trust transfer,
runtime truth, governed reliance, gold governed reliance,
gold certified, gold accepted
```

The `scope_limitations` / `non_claims` / `control_limitations` escape
applies only to those three lists by exact key match; nested objects
with the same key elsewhere do not benefit.

---

## Package layout

```
<output-dir>/
├── control-pack.json                                                                (subject [0])
├── silver-control-crosswalk-protected-action-catalog-conformance-report.json        (subject [1])
└── silver-control-crosswalk-protected-action-catalog-manifest.json                  (2-subject anchor)
```

---

## Fixtures

Three hand-authored passing control packs ship under
`fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/`:

| File | Variant |
|---|---|
| `control-pack.json` | Canonical pack with five protected actions and five crosswalk entries (one per major v0.2.x/v0.3.x artifact_type family) |
| `control-pack-with-dependencies.json` | Exercises non-empty `dependency_references` across all three `reference_type` values |
| `control-pack-with-limitations.json` | Exercises a full `control_limitations` block plus exhaustive `non_claims` |

Every fixture is a passing control pack: parses to a top-level JSON
object, satisfies the 24 ordered structural checks, contains
non-empty `scope_limitations` and `non_claims`, and contains no
prohibited claim tokens outside those blocks.

---

## Tools

```
tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py
tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py
```

Pure-stdlib. No new runtime dependencies for v0.3.6.

---

## Make targets

```
make run-silver-control-crosswalk-protected-action-catalog-v0-3-6
make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
```

`verify-silver-all` chains the v0.3.6 regression test after v0.3.5.

---

## Regression test

```
tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh
```

47 ordered exercises:

- 4 positive-path checks (pristine build + verify, inline manifest
  layout, inline conformance report)
- 24 canonical verifier reason mutations (one per approved reason),
  hash-first re-anchored
- 11 duplicate manifest-invalid mutations (all routed to
  `control_pack_manifest_invalid`, including subject [0] / [1]
  absolute path, subject [0] / [1] traversal, subject [0] file
  missing, subject [0] `size_bytes` mismatch, subject [0] `sha256`
  mismatch, wrong subject count, subject [0] role wrong,
  `control_pack_id` cross-anchor mismatch, and the non-masking
  post-structural conformance-report disagreement)
- 5 runner-only refusal cases (one per Phase A reason)
- 1 runner-relay-of-verifier-failure case (verifier reason relayed
  UNCHANGED; no sixth wrapper)
- 1 taxonomy gate (TG1) over all v0.3.6-owned files and the
  v0.3.6-anchored sections of README.md, CLAUDE.md,
  `tools/silver/README.md`,
  `docs/silver/silver-artifact-map-v0.1.7.md`,
  `docs/silver/silver-limitations-and-non-claims.md`, and
  `docs/gold/gold-boundary-v0.2.5.md`
- 1 scoped sha256 snapshot before / after

---

## Limitations and non-claims

- The v0.3.6 control crosswalk + protected action catalog package
  is not a regulator, auditor, or third-party endorsement.
- The package is not a SOC 2, ISO 27001, NIST 800-53, PCI DSS,
  HIPAA, or any other external framework mapping.
- The package is not an opinion on control design effectiveness
  or control operating effectiveness.
- The packaged conformance report describes only that the control
  pack satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any specific upstream Silver
  evidence in this release.
- v0.3.6 does not re-evaluate the referenced composed-gateway
  evidence, trace-binding evidence, acceptance record, revocation-
  challenge drill, or any other upstream Silver evidence against
  the catalog. References are structural pointers only.
- v0.3.6 does not issue, transfer, or accept any reliance
  instrument against the catalog.
- v0.3.6 ships local hash anchors only; the package is unsigned.
- v0.3.6 does not authorize production reliance, is not legally
  enforceable, is not a Gold artifact, and does not advance the
  Gold boundary.
