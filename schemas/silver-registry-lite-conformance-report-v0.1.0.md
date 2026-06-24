# Silver Registry Lite Conformance Report Schema v0.1.0

> Release line: ProofRail Silver v0.3.7.
>
> The conformance report is the byte-for-byte re-derivable record of the 24
> ordered structural checks that the v0.3.7 verifier runs against the
> registry-lite body. It is not a regulator approval, auditor approval,
> third-party endorsement, compliance attestation, certification, legal
> instrument, or Gold artifact.

## Document identity

| Field | Required | Type | Allowed value |
|---|---|---|---|
| `document_type` | yes | string | `proofrail.silver.registry_lite_conformance_report` |
| `schema_version` | yes | string | `v0.1.0` |
| `proofrail_release` | yes | string | `silver.registry_lite.v0.3.7` |
| `report_id` | yes | string | non-empty |
| `registry_id` | yes | string | non-empty; copied from the registry-lite body `registry_id` field |
| `generated_at` | yes | string | ISO-8601 UTC timestamp ending in `Z` |
| `checks` | yes | array | exactly 24 entries, fixed order, all `status = "pass"` |
| `summary` | yes | object | `{checks_total: 24, checks_passed: 24, checks_not_passing: 0}` |

## `checks[]`

Each entry has fixed shape:

| Field | Required | Type |
|---|---|---|
| `check_id` | yes | string from the ordered closed set below (`check_01..check_24`) |
| `reason` | yes | string from the ordered closed set of 24 verifier reasons (see below) |
| `status` | yes | string; in the bundled conformance report this is always `pass` |

## Ordered check set

| Index | `check_id` | `reason` |
|---|---|---|
| 1 | `check_01` | `registry_manifest_invalid` |
| 2 | `check_02` | `registry_not_object` |
| 3 | `check_03` | `registry_schema_invalid` |
| 4 | `check_04` | `registry_profile_unsupported` |
| 5 | `check_05` | `registry_identity_invalid` |
| 6 | `check_06` | `registry_authority_invalid` |
| 7 | `check_07` | `registry_entity_set_invalid` |
| 8 | `check_08` | `registry_entity_entry_invalid` |
| 9 | `check_09` | `registry_entity_identifier_invalid` |
| 10 | `check_10` | `registry_role_invalid` |
| 11 | `check_11` | `registry_status_invalid` |
| 12 | `check_12` | `registry_effective_period_invalid` |
| 13 | `check_13` | `registry_key_reference_invalid` |
| 14 | `check_14` | `registry_key_binding_invalid` |
| 15 | `check_15` | `issuer_entry_invalid` |
| 16 | `check_16` | `verifier_entry_invalid` |
| 17 | `check_17` | `relying_party_entry_invalid` |
| 18 | `check_18` | `policy_authority_entry_invalid` |
| 19 | `check_19` | `revocation_source_entry_invalid` |
| 20 | `check_20` | `protected_action_authority_entry_invalid` |
| 21 | `check_21` | `trust_relationship_invalid` |
| 22 | `check_22` | `version_binding_invalid` |
| 23 | `check_23` | `non_claims_missing` |
| 24 | `check_24` | `prohibited_registry_claim_present` |

## Canonical byte image

The bundled conformance report is serialized with
`json.dumps(obj, sort_keys=True, separators=(",",":"))` followed by a
single trailing newline (`\n`). The byte image depends only on the verified
registry-lite body; the runner and the verifier produce byte-identical
output from the same registry-lite body.

## Non-claims

The conformance report describes only that the registry-lite body
satisfies the 24 ordered structural checks under the v0.3.7 closed
vocabulary. It does not describe a substantive review of any specific
upstream Silver evidence, does not approve, audit, or certify the
registry, and is not legally binding or a Gold artifact.
