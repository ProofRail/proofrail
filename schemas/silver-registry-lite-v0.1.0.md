# Silver Registry Lite Schema v0.1.0

> Release line: ProofRail Silver v0.3.7.
>
> This document defines the body schema for a Silver Registry Lite document.
> A registry-lite document is a deterministic, local, hand-authored
> declaration of ProofRail-internal Silver entity roles and their bindings.
> It is not a production PKI artifact, not a certificate authority record,
> not a federation registry, not a legal identity-proofing artifact, and
> not a compliance/audit/regulator approval.

## Document identity

| Field | Required | Type | Allowed value |
|---|---|---|---|
| `document_type` | yes | string | `proofrail.silver.registry_lite` |
| `schema_version` | yes | string | `v0.1.0` |
| `profile` | yes | string | `silver.registry_lite.v0.3.7` |
| `registry_id` | yes | string | matches `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$` |
| `generated_at` | yes | string | ISO-8601 UTC timestamp ending in `Z` |
| `registry_scope` | yes | string | closed set (see below) |
| `release_binding` | yes | string | closed set (see below) |
| `registry_authority` | yes | object | see below |
| `entities` | yes | array | non-empty; each entry is an entity entry (see below) |
| `trust_relationships` | yes | array | array of trust-relationship entries (may be empty in canonical fixture) |
| `version_bindings` | yes | array | non-empty; each entry is a version binding (see below) |
| `scope_limitations` | yes | array | non-empty; each entry is a non-empty string |
| `non_claims` | yes | array | non-empty; each entry is a non-empty string |

## Closed `registry_scope` values

| Value | Meaning |
|---|---|
| `demo` | Local demo registry; not production. |
| `staging` | Pre-production environment registry. |
| `production` | Production-environment registry. v0.3.7 does NOT authorize production reliance even when this value is declared. |
| `multi_environment` | Crosses multiple environments. |
| `out_of_scope` | Out of scope of this registry. |

## Closed `release_binding` values

| Value |
|---|
| `silver.profile.v0.2.1` |
| `silver.attestation.v0.2.2` |
| `silver.authority.v0.2.3` |
| `silver.composed.v0.2.7` |
| `silver.acceptance.v0.2.8` |
| `silver.drill.v0.2.9` |
| `silver.handoff.v0.3.0` |
| `silver.inspection.v0.3.1` |
| `silver.trace_binding.v0.3.2` |
| `silver.adapter_pilot.v0.3.3` |
| `silver.challenge_withdrawal.v0.3.4` |
| `silver.policy_pack.v0.3.5` |
| `silver.control_crosswalk.v0.3.6` |
| `silver.registry_lite.v0.3.7` |

## `registry_authority`

| Field | Required | Type |
|---|---|---|
| `identity_id` | yes | string matching `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` |
| `display_name` | yes | non-empty string |
| `contact` | yes | non-empty string (free-text; not scanned by the overclaim guard) |

## `entities[]` — base shape (all roles)

| Field | Required | Type |
|---|---|---|
| `entity_id` | yes | string matching `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` |
| `display_label` | yes | non-empty string |
| `role` | yes | closed entity-role set (see below) |
| `status` | yes | closed entity-status set (see below) |
| `effective_period` | yes | object `{starts_at, ends_at}`, both ISO-8601 UTC `Z`, `starts_at <= ends_at` |
| `key_references` | optional | array of key-reference objects (see below) |
| `key_bindings` | optional | array of key-binding objects (see below) |
| role-specific block | yes | one of the six role-specific blocks below, matching `role` |

### Closed entity-role set

| Value |
|---|
| `issuer` |
| `verifier` |
| `relying_party` |
| `policy_authority` |
| `revocation_source` |
| `protected_action_authority` |

### Closed entity-status set

| Value |
|---|
| `active` |
| `provisional` |
| `deprecated` |
| `withdrawn` |
| `out_of_scope` |

### `key_references[]`

| Field | Required | Type |
|---|---|---|
| `key_id` | yes | string matching `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$` |
| `algorithm` | yes | closed `{ed25519, ecdsa_p256, ecdsa_p384, rsa_2048, rsa_3072, rsa_4096}` |
| `public_key_fingerprint` | yes | string matching `sha256:<64-lowercase-hex>` |
| `key_reference_type` | yes | closed `{local_fingerprint, local_pem_path, local_jwk_path}` |
| `local_reference_path` | required when `key_reference_type ∈ {local_pem_path, local_jwk_path}` | relative path with no `..` segments |

Private-key material (any field named `private_key`, `private_key_pem`,
`private_jwk`, `secret_key`, or `secret`) is structurally rejected.

### `key_bindings[]`

| Field | Required | Type |
|---|---|---|
| `binding_id` | yes | string matching `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$` |
| `key_id` | yes | matches a `key_id` declared in the same entity's `key_references[]` |
| `binding_purpose` | yes | closed `{issue_evidence, verify_evidence, sign_policy, sign_revocation, sign_authority_decision}` |

## Role-specific blocks

### `issuer` (block name: `issuer`)
| Field | Required | Type |
|---|---|---|
| `issuer_scope` | yes | closed `{silver_evidence_only, silver_and_bronze_evidence, demo_scope_only}` |
| `signed_artifact_types` | yes | non-empty array of closed v0.2.x/v0.3.x artifact-type tokens (see Closed Artifact Type Set below) |
| `supported_profiles` | yes | non-empty array of closed v0.2.x/v0.3.x profile tokens (see Closed Profile Token Set below) |

### `verifier` (block name: `verifier`)
| Field | Required | Type |
|---|---|---|
| `verifier_profiles` | yes | non-empty array of closed v0.2.x/v0.3.x profile tokens |
| `verifier_posture` | yes | closed `{independent, self_attested, demo_only}` |

### `relying_party` (block name: `relying_party`)
| Field | Required | Type |
|---|---|---|
| `reliance_scope` | yes | closed `{demo_only, local_enterprise, multi_party_governed, out_of_scope}` |
| `local_policy_reference` | yes | relative path with no `..` segments |

### `policy_authority` (block name: `policy_authority`)
| Field | Required | Type |
|---|---|---|
| `policy_scope` | yes | closed `{relying_party_policy_only, multi_party_policy, demo_policy_only}` |
| `authority_boundary` | yes | closed `{local_demo, local_enterprise, multi_party_governed}` |

### `revocation_source` (block name: `revocation_source`)
| Field | Required | Type |
|---|---|---|
| `source_type` | yes | closed `{local_list, signed_revocation_record, challenge_drill_outcome}` |
| `status_mode` | yes | closed `{pull, push, snapshot}` |
| `supported_subject_scope` | yes | closed `{assertion_id_only, issuer_key_only, bundle_hash_only, all_three}` |

### `protected_action_authority` (block name: `protected_action_authority`)
| Field | Required | Type |
|---|---|---|
| `protected_action_scope` | yes | closed `{local_demo_actions, local_enterprise_actions, multi_party_governed_actions}` |
| `delegation_boundary` | yes | closed `{principal_only, scoped_delegation, joint_principal, delegation_with_break_glass}` |

## Closed Artifact Type Set

Used by `issuer.signed_artifact_types[]`:

`bronze_claim`, `bronze_evidence_bundle_manifest`, `silver_signed_bundle_assertion`,
`silver_revocation_list`, `silver_verification_report`,
`silver_verifier_output_attestation`,
`silver_composed_gateway_evidence_manifest`,
`silver_relying_party_acceptance_record`,
`silver_revocation_challenge_drill_report`,
`silver_acceptance_handoff_manifest`,
`silver_handoff_inspection_manifest`,
`silver_trace_binding_manifest`, `silver_adapter_pilot_manifest`,
`silver_challenge_withdrawal_manifest`,
`silver_relying_party_policy_pack_manifest`,
`silver_control_crosswalk_protected_action_catalog_manifest`,
`silver_registry_lite_manifest`.

## Closed Profile Token Set

Used by `issuer.supported_profiles[]` and `verifier.verifier_profiles[]`:

`silver.base`, `silver.base.demo`, `silver.independent`,
`silver.attestation.v0.2.2`, `silver.authority.v0.2.3`,
`silver.composed.v0.2.7`, `silver.acceptance.v0.2.8`,
`silver.drill.v0.2.9`, `silver.handoff.v0.3.0`,
`silver.inspection.v0.3.1`, `silver.trace_binding.v0.3.2`,
`silver.adapter_pilot.v0.3.3`,
`silver.challenge_withdrawal.v0.3.4`,
`silver.policy_pack.v0.3.5`,
`silver.control_crosswalk.v0.3.6`,
`silver.registry_lite.v0.3.7`.

## `trust_relationships[]`

| Field | Required | Type |
|---|---|---|
| `relationship_id` | yes | string matching `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$` |
| `from_entity_id` | yes | matches an `entity_id` declared in `entities[]` |
| `to_entity_id` | yes | matches an `entity_id` declared in `entities[]` |
| `relationship_verb` | yes | closed verb set (see below) |
| `effective_period` | yes | object `{starts_at, ends_at}`, both ISO-8601 UTC `Z`, `starts_at <= ends_at` |

### Closed `relationship_verb` set

| Value |
|---|
| `recognizes_issuer` |
| `accepts_verifier_output` |
| `references_policy_authority` |
| `consults_revocation_source` |
| `delegates_to_protected_action_authority` |
| `declares_role_binding` |

## `version_bindings[]`

| Field | Required | Type |
|---|---|---|
| `binding_id` | yes | string matching `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$` |
| `upstream_id` | yes | closed set of Silver upstream IDs (matches the `release_binding` allowed list, excluding `silver.registry_lite.v0.3.7`) |
| `upstream_version` | yes | closed `{v0.2.1, v0.2.2, v0.2.3, v0.2.7, v0.2.8, v0.2.9, v0.3.0, v0.3.1, v0.3.2, v0.3.3, v0.3.4, v0.3.5, v0.3.6}` |

## Prohibited registry-claim vocabulary (closed, scanned by verifier)

The following 36 case-insensitive substring tokens are forbidden in every
string value reachable in the registry-lite body OUTSIDE `non_claims` and
`scope_limitations`. No other field is exempt; the
`registry_authority.contact` field is scanned along with every other
non-limitations string:

`production PKI`, `certificate authority`, `certification authority`,
`legal identity`, `legally authoritative identity`, `identity proofing`,
`proofed identity`, `federated trust`, `trust federation`,
`production trust registry`, `authoritative trust registry`, `certified`,
`certification`, `compliant`, `compliance`, `legally enforceable`,
`legal enforceability`, `production authorized`, `production authorization`,
`authorized for production`, `regulator approved`, `regulator approval`,
`approved by regulator`, `auditor approved`, `auditor approval`,
`approved by auditor`, `audit ready`, `operating effectiveness`,
`design effectiveness`, `runtime truth`, `proves runtime truth`,
`transferred trust`, `trust transferred`, `gold governed reliance`,
`gold governance`, `gold accepted`, `gold certified`.

Any match emits the verifier reason `prohibited_registry_claim_present`.

## Non-claims

A registry-lite document is local, deterministic, hand-authored, and
unsigned. It declares ProofRail-internal Silver role bindings only and
does not constitute:

- a production PKI artifact, certificate authority record, certification
  authority record, or federation registry;
- a legal identity, identity-proofing record, or authoritative trust
  registry;
- a regulator approval, auditor approval, third-party endorsement,
  certification, or compliance attestation;
- a production authorization, audit-ready posture, or legally
  enforceable instrument;
- a runtime-truth oracle, transferred trust, or governed reliance;
- a Gold artifact, Gold acceptance, or advancement of the Gold boundary;
- a re-evaluation of any specific upstream Silver evidence against the
  registry;
- an issued, transferred, or accepted reliance instrument.
