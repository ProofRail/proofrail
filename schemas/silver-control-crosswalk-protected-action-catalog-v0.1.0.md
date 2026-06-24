# Silver Control Crosswalk + Protected Action Catalog Schema v0.1.0

> Release line: ProofRail Silver v0.3.6.
>
> This schema is structural. It does not declare compliance, certification, audit
> approval, regulator approval, production authorization, control design
> effectiveness, control operating effectiveness, runtime truth, transferred
> trust, or Gold-governed reliance.

## Document identity

| Field | Required | Type | Allowed value |
|---|---|---|---|
| `document_type` | yes | string | `proofrail.silver.control_crosswalk_protected_action_catalog` |
| `schema_version` | yes | string | `v0.1.0` |
| `profile` | yes | string | closed set: `{silver.control_crosswalk.v0.3.6}` |
| `control_pack_id` | yes | string | non-empty |

## Identity blocks

`package_owner`, `relying_party`, and `catalog_authority` are required objects.
Each must declare `identity_id`, `display_name`, and `role` as non-empty
strings. Missing or empty identity blocks fail as
`control_pack_identity_invalid`.

## `protected_action_catalog`

A non-empty JSON array of protected action entries. A missing or non-list
catalog fails as `protected_action_catalog_invalid`. Each entry must include:

| Field | Closed values |
|---|---|
| `action_id` | matches the protected action identifier grammar |
| `description` | non-empty string |
| `category` | `{financial, vendor, data, deployment, identity, configuration, communication}` |
| `environment_scope` | `{production, staging, test, demo}` |
| `actor_scope` | `{human, agent, system, mixed}` |
| `authority` | object — see below |
| `risk_boundary` | object — see below |

### Protected action identifier grammar

`action_id` must match:

```
^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$
```

Maximum length 64 characters. A violation fails as
`protected_action_identifier_invalid`.

Reference action examples: `payment.release`, `vendor.approve`, `data.export`,
`deploy.change`, `admin.rotate_secret`.

### `authority`

Required fields:

| Field | Closed values |
|---|---|
| `posture` | `{scoped_delegation, principal_only, joint_principal, deny_all}` |
| `delegation_allowed` | boolean |
| `scoped_principals` | non-empty list of non-empty strings |

A missing field or out-of-set posture fails as
`protected_action_authority_invalid`.

### `risk_boundary`

Required fields:

| Field | Closed values |
|---|---|
| `risk_class` | `{low, moderate, high, critical}` |
| `blast_radius` | non-empty string |
| `rationale` | non-empty string |

A missing field or out-of-set class fails as
`protected_action_risk_boundary_invalid`.

A missing scope field (`environment_scope`, `actor_scope`) fails as
`protected_action_scope_invalid`. A missing required descriptive field on the
entry itself (`description`, `category`) fails as
`protected_action_entry_invalid`.

## `control_crosswalk`

A non-empty JSON array of crosswalk entries. A missing or non-list crosswalk
fails as `control_crosswalk_invalid`. Each entry must include:

| Field | Closed values |
|---|---|
| `mapping_id` | non-empty string, unique within the crosswalk |
| `action_id` | must reference an `action_id` already present in the catalog |
| `artifact_type` | closed `proofrail_artifact_type` set (below) |
| `artifact_path` | non-empty string; must not be absolute and must not contain `..` |
| `relationship` | closed evidence-relationship verb set (below) |
| `control_concept_id` | non-empty string matching control-concept ID grammar |
| `control_objective` | non-empty narrow objective text |
| `claim` | object with `verb` and `scope_text` |

A missing required field fails as `crosswalk_entry_invalid`. A crosswalk
`action_id` not in the catalog fails as
`catalog_crosswalk_consistency_invalid`. An out-of-set `artifact_type`, an
absolute `artifact_path`, or a path containing `..` fails as
`proofrail_artifact_reference_invalid`. An out-of-set `relationship` fails as
`evidence_relationship_invalid`. An out-of-grammar `control_concept_id` fails
as `control_concept_reference_invalid`. An empty `control_objective` fails as
`control_objective_invalid`.

### Closed `proofrail_artifact_type` set

This closed set is derived from existing ProofRail v0.1.x–v0.3.5 artifact
families and is fixed in v0.3.6.

```
bronze_claim
bronze_evidence_bundle_manifest
silver_signed_bundle_assertion
silver_verification_report
silver_revocation_list
silver_verifier_output_attestation
silver_profile_conformance_report
silver_multi_principal_authority_fixture
silver_protected_action_request
silver_protected_action_decision_report
silver_multi_agent_harness_run_report
silver_multi_agent_harness_evidence_manifest
silver_multi_agent_demo_package_manifest
silver_multi_agent_demo_summary
silver_evidence_source_adapter
silver_simulated_gateway_evidence_event
silver_composed_gateway_evidence_manifest
silver_composed_gateway_evidence_report
silver_relying_party_acceptance_policy
silver_relying_party_acceptance_record
silver_relying_party_acceptance_package_manifest
silver_relying_party_review_event
silver_revocation_challenge_drill_manifest
silver_revocation_challenge_drill_report
silver_acceptance_handoff_manifest
silver_acceptance_handoff_summary
silver_handoff_inspection_manifest
silver_handoff_inspection_report
silver_to_gold_requirement_set
silver_trace_event
silver_trace_claim_binding_set
silver_trace_binding_manifest
silver_trace_binding_report
silver_adapter_pilot_source_export
silver_adapter_pilot_normalization_map
silver_adapter_pilot_manifest
silver_adapter_pilot_report
silver_challenge_record
silver_withdrawal_record
silver_challenge_withdrawal_manifest
silver_challenge_withdrawal_summary
silver_relying_party_policy_pack
silver_relying_party_policy_pack_manifest
silver_relying_party_policy_pack_conformance_report
```

### Closed evidence-relationship verb set

```
describes
declares
mediates
observes
normalizes
attests
records_acceptance
records_review
packages
inspects
binds_trace
declares_policy
```

### Control-concept ID grammar

```
^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$
```

### `claim`

Required fields:

| Field | Closed values |
|---|---|
| `verb` | `{may_inform, may_support, may_evidence, declares_scope_for, packages_for_review}` |
| `scope_text` | non-empty narrow scope text |

An out-of-set `verb` or empty `scope_text` fails as `control_claim_invalid`.

## `control_limitations`

A non-empty JSON array. Each entry must include `limitation_id`, `summary`,
and `domain` as non-empty strings. A missing block, empty list, or malformed
entry fails as `control_limitation_invalid`.

## `dependency_references`

A JSON array (possibly empty). Each entry must include `dependency_id`,
`reference_type` from the closed set
`{upstream_silver_release, upstream_silver_profile, prior_artifact}`,
`upstream_id`, and `upstream_version`. `upstream_id` must not be absolute and
must not contain `..`. A missing field, unsafe reference, or out-of-set type
fails as `dependency_reference_invalid`.

## `version_bindings`

A non-empty JSON array. Each entry must include `binding_id`, `upstream_id`,
and `upstream_version`. `upstream_version` must be from the closed set
`{v0.2.6, v0.2.7, v0.2.8, v0.2.9, v0.3.0, v0.3.1, v0.3.2, v0.3.3, v0.3.4, v0.3.5}`.
A missing field or out-of-set version fails as `version_binding_invalid`.

## `non_claims`

Required non-empty JSON array of non-empty disclaim strings. Empty or missing
fails as `non_claims_missing`.

## `scope_limitations`

Optional but conventional. When present, must be a JSON array of strings.

## Prohibited compliance vocabulary

Outside `non_claims`, `scope_limitations`, and `control_limitations`, no string
value in the control pack may contain a token from the closed prohibited
vocabulary (case-insensitive substring match): `certified`, `certification`,
`compliant`, `compliance`, `SOC 2 compliant`, `SOC2 compliant`,
`ISO certified`, `NIST compliant`, `PCI compliant`, `HIPAA compliant`,
`legally enforceable`, `legal enforceability`, `production authorized`,
`production authorization`, `authorized for production`, `regulator approved`,
`regulator approval`, `approved by regulator`, `auditor approved`,
`auditor approval`, `approved by auditor`, `audit ready`,
`operating effectiveness`, `design effectiveness`, `runtime truth`,
`proves runtime truth`, `transferred trust`, `trust transferred`,
`gold governed reliance`, `gold governance`, `gold accepted`,
`gold certified`. Any occurrence fails as
`prohibited_compliance_claim_present`.

## Non-claims

A v0.3.6 control pack does NOT declare compliance with any framework, does
NOT declare certification, does NOT declare audit approval or readiness, does
NOT declare regulator or auditor approval, does NOT declare production
authorization, does NOT declare control design or operating effectiveness,
does NOT declare legal enforceability, does NOT declare runtime truth, does
NOT declare transferred trust, and does NOT cross the Gold governance
boundary.
