# Gold Governed Reliance Package Schema v0.1.0

Schema for the Gold v0.4.0 Minimal Gold Governed Reliance Demo
package body (subject [0] in the v0.4.0 package manifest).

## Boundary

A v0.4.0 package is a deterministic local hand-authored record of
governed reliance decisions composed from Silver-shaped inputs. It is
not a certificate, not signed, not federated, not a transfer of
reliance to any external party, and not full Gold.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.governed_reliance_package`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Must be in the closed set `{gold.governed_reliance.v0.4.0}`. |
| `package_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `governed_reliance_demo_id` | string | yes | Same grammar. |
| `relying_party` | object | yes | See "Relying Party". |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `inputs` | object | yes | See "Inputs". |
| `governed_decisions` | array | yes | Between 1 and 5 entries, ordered by scenario natural order, with unique `scenario_type` values. See "Governed Decision Entry". |
| `scope_limitations` | array of non-empty strings | yes | Non-empty. |
| `non_claims` | array of non-empty strings | yes | Non-empty. |

## Relying Party

| Field | Type | Required | Notes |
|---|---|---|---|
| `identity_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`. |
| `display_name` | string | yes | Non-empty. |
| `contact` | string | yes | Non-empty. Not scanned by overclaim guard. |
| `registry_ref` | string | yes | Closed grammar identical to `identity_id`. |

## Inputs

Five typed input references. v0.4.0 does NOT re-verify these inputs
end-to-end. Verifier validates shape only.

```text
inputs.silver_verification    {input_type: silver_verification_result,    input_ref, expected_status}
inputs.silver_handoff         {input_type: silver_acceptance_handoff,    input_ref, expected_handoff_posture}
inputs.policy_pack            {input_type: silver_relying_party_policy_pack, input_ref, policy_pack_id, policy_pack_version}
inputs.registry_lite          {input_type: silver_registry_lite,          input_ref, registry_id}
inputs.control_crosswalk      {input_type: silver_control_crosswalk,      input_ref, control_pack_id}
```

Each `input_type` is fixed by name. `expected_status` for the Silver
verification input is the closed set `{pass}` (only passing inputs
qualify as Silver-derived inputs for v0.4.0).
`expected_handoff_posture` is the closed set `{for_demo_scope,
review_required_before_reuse, not_reusable_without_governed_review}`.

## Governed Decision Entry

`governed_decisions` is a list of 1 to 5 entries. The five recognized
scenario natural-order positions are:

| Natural index | scenario_type | decision_status |
|---|---|---|
| 0 | `clean_acceptance` | `accepted` |
| 1 | `policy_rejection` | `rejected` |
| 2 | `challenge_filed` | `challenged` |
| 3 | `withdrawal` | `withdrawn` |
| 4 | `supersession` | `superseded` |

Constraints (verifier enforces all of these under
`governed_decision_set_invalid` at check 11):

- `governed_decisions` must be a JSON array (non-empty: 1..5 entries).
- An empty list is rejected.
- A list with more than 5 entries is rejected.
- Each entry's `scenario_type` is drawn from the closed set above.
- `scenario_type` values across the list must be unique (no duplicates).
- Entries must appear in natural-order (the scenario_type natural-order
  indices listed above must be strictly increasing across the entry
  list). Out-of-order entries are rejected.
- The canonical demo fixture contains all five entries in natural
  order; it is the only full v0.4.0 Gold package shape.
- Single-scenario fixture variants are SCENARIO SLICES of the
  canonical fixture, not full canonical Gold packages. They contain
  exactly one entry of the named scenario_type. They exist to verify
  scenario-isolated paths; they are not Gold-complete.

Each entry has the following fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `decision_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. |
| `scenario_type` | string | yes | Closed set above. |
| `decision_status` | string | yes | Closed set `{accepted, rejected, challenged, withdrawn, superseded}`. |
| `decision_subject` | object | yes | `{subject_type, subject_ref}`. |
| `policy_binding` | object | yes | `{policy_pack_id, policy_pack_version, policy_clause_refs[], policy_decision}`. |
| `registry_binding` | object | yes | `{relying_party_id, decision_authority_role}`. |
| `action_scope` | object | yes | `{protected_action_id, action_category, action_environment}`. |
| `decision_trigger` | string | yes | Closed set (see below). |
| `scenario_specific_state` | object | yes | Closed shape per scenario_type. |
| `recorded_at` | string | yes | ISO-8601 UTC. |

### Closed Vocabularies

```text
decision_status              {accepted, rejected, challenged, withdrawn, superseded}
scenario_type                {clean_acceptance, policy_rejection, challenge_filed, withdrawal, supersession}
decision_subject.subject_type {silver_verification_result, silver_acceptance_handoff, challenge_withdrawal_record}
policy_binding.policy_decision {allow, deny, conditional, withhold, review}
registry_binding.decision_authority_role
                             {issuer, verifier, relying_party, policy_authority,
                              revocation_source, protected_action_authority}
decision_trigger             {evidence_verified, policy_evaluated, challenge_received,
                              revocation_observed, evidence_defect_observed,
                              updated_evidence_received, updated_policy_received}
action_scope.action_category {financial_release, data_export, deployment_change,
                              secret_rotation, vendor_approval}
action_scope.action_environment {demo, staging, production_simulated}
action_scope.protected_action_id closed v0.4.0 demo subset:
                             {release_payment, export_data, change_deployment,
                              rotate_secret, approve_vendor}
```

### Scenario-Specific State Shapes

`clean_acceptance`:
```text
{acceptance_record_ref: closed-grammar string}
```

`policy_rejection`:
```text
{rejection_reason: closed enum
   {policy_scope_excluded, posture_below_threshold, evidence_outside_environment,
    relying_party_excluded, action_not_authorized},
 silver_verification_passing: true}
```

The literal Boolean value `true` is required to honour the
"rejection despite Silver passing" invariant.

`challenge_filed`:
```text
{challenge_record_ref: closed-grammar string,
 challenge_state: closed enum {open, under_review, closed_resolved, closed_withdrawn}}
```

`withdrawal`:
```text
{withdrawal_record_ref: closed-grammar string,
 withdrawal_trigger: closed enum
   {challenge_filed, revocation_observed, evidence_defect_observed}}
```

`supersession`:
```text
{prior_decision_ref_kind: closed enum
   {internal_decision_id, external_decision_id},
 prior_decision_id: closed-grammar string,
 supersession_trigger: closed enum
   {updated_evidence, updated_policy, updated_registry},
 superseding_input_ref: closed-grammar string}
```

`prior_decision_ref_kind` is required and closed:

- `internal_decision_id`: `prior_decision_id` MUST resolve to a
  `decision_id` of another entry in the SAME `governed_decisions[]`
  list. If it does not resolve, the verifier surfaces
  `supersession_path_invalid`.
- `external_decision_id`: `prior_decision_id` references a decision
  outside this package. The verifier does NOT require resolution
  within `governed_decisions[]`.

The canonical 5-scenario fixture uses `internal_decision_id`. The
single-scenario supersession fixture uses `external_decision_id`.

## scope_limitations

Required non-empty list of strings. Each entry is a non-blank string.
Tokens from the prohibited Gold claim vocabulary are permitted inside
this block when used to disclaim.

## non_claims

Required non-empty list of strings. Each entry is a non-blank string.
Tokens from the prohibited Gold claim vocabulary are permitted inside
this block when used to disclaim.

## Deterministic Serialization

The package body is written by the v0.4.0 runner as a byte-copy of the
input file. The runner does not normalize or reorder the input.

## Verifier Notes

The 24 approved verifier failure reasons that govern this schema are
defined in the v0.4.0 release narrative
(`docs/gold/minimal-gold-governed-reliance-v0.4.0.md`). The verifier
runs ordered checks against this schema; each failure surfaces with
its dedicated reason and is not aliased into adjacent reasons.

## Non-Claims

A v0.4.0 package is not signed, not certified, not approved, not
audited, not a legal instrument, not a transfer of reliance, not
production governance, and not full Gold. v0.4.0 records local
governed reliance decision states, including the local `accepted`
state, but does not claim legal issuance, external acceptance, or
enforceability of reliance.
