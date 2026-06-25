# Gold Governed Reliance Decision Report Schema v0.1.0

Schema for the Gold v0.4.1 governed reliance decision report (subject
[2] in the v0.4.1 package manifest). The decision report is a
normalized projection of `governed_decisions[]` from a v0.4.0-shaped
governed reliance package body. It is derived deterministically by
the v0.4.1 runner from the package body and re-derived independently
by the v0.4.1 verifier as a byte-compare.

## Boundary

The decision report records a normalized per-row projection of the
governed reliance decisions in the package body, plus a derived
coverage summary. The decision report is not a signature, not a
certificate, not a substantive evaluation of the upstream Silver
evidence, not a transfer of reliance, not Gold certification, and not
full Gold.

The decision report's byte image depends only on the package body and
the manifest-supplied `decision_report_id` / `generated_at`. The
report introduces no facts that are not already in the package body,
and the verifier re-derives it from the package body using a
byte-identical serializer.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | string | yes | Must be `proofrail.gold.governed_reliance_decision_report`. |
| `schema_version` | string | yes | Must be `v0.1.0`. |
| `profile` | string | yes | Must be in the closed set `{gold.decision_report_hardening.v0.4.1}`. |
| `package_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. Cross-anchored to package body and to the manifest's `package_id`. |
| `governed_reliance_demo_id` | string | yes | Same grammar. Cross-anchored to package body and to the manifest's `governed_reliance_demo_id`. |
| `decision_report_id` | string | yes | Same grammar. Cross-anchored to the manifest's `decision_report_id`. Must be distinct from the inherited conformance report's `report_id` in the same manifest. The v0.4.1 decision report deliberately does NOT carry a generic `report_id` field. |
| `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `source_package_sha256` | string | yes | Bare lowercase hex SHA-256 of the package body bytes (subject [0]). No `sha256:` label prefix. |
| `decision_count` | integer | yes | Number of entries in `decision_rows`. Must equal the length of `governed_decisions[]` in the package body. Range 1..5. |
| `decision_rows` | array of objects | yes | Length 1..5. One entry per governed decision, in the same order as `governed_decisions[]`. |
| `coverage_summary` | object | yes | Derived. See "Coverage Summary". |
| `scope_limitations` | array of non-empty strings | yes | Non-empty. Mirrored from the package body. |
| `non_claims` | array of non-empty strings | yes | Non-empty. Mirrored from the package body. |

## Decision Row Shape

Each entry in `decision_rows[]` is a normalized projection of the
corresponding `governed_decisions[i]` entry in the package body. The
runner does not invent fields, does not re-rank evidence, and does not
mutate scenario-specific state. Field values are copied from the
source entry; derived row-level fields are explicitly marked below.

| Field | Type | Required | Notes |
|---|---|---|---|
| `row_id` | string | yes | `row_NN` where `NN` is `01`..`05`, assigned in source order. Derived. |
| `source_decision_index` | integer | yes | 0-based index into `governed_decisions[]`. Derived. |
| `decision_id` | string | yes | Mirrored from `governed_decisions[i].decision_id`. |
| `scenario_type` | string | yes | Mirrored. Closed set `{clean_acceptance, policy_rejection, challenge_filed, withdrawal, supersession}`. |
| `decision_status` | string | yes | Mirrored. Closed set `{accepted, rejected, challenged, withdrawn, superseded}`. |
| `decision_trigger` | string | yes | Mirrored. Closed set `{evidence_verified, policy_evaluated, challenge_received, revocation_observed, evidence_defect_observed, updated_evidence_received, updated_policy_received}`. |
| `recorded_at` | string | yes | Mirrored. ISO-8601 UTC. |
| `decision_subject` | object | yes | See "decision_subject". Mirrored. |
| `policy_binding` | object | yes | See "policy_binding". Mirrored. |
| `registry_binding` | object | yes | See "registry_binding". Mirrored. |
| `action_scope` | object | yes | See "action_scope". Mirrored. |
| `scenario_path_summary` | string | yes | Derived. See "scenario_path_summary". |
| `decision_fingerprint` | string | yes | Derived. Bare lowercase hex SHA-256. See "Decision Fingerprint". |

### decision_subject

| Field | Type | Required | Notes |
|---|---|---|---|
| `subject_type` | string | yes | Closed set `{silver_verification_result, silver_acceptance_handoff, challenge_withdrawal_record}`. |
| `subject_ref` | string | yes | Closed identifier grammar. |

### policy_binding

| Field | Type | Required | Notes |
|---|---|---|---|
| `policy_pack_id` | string | yes | Mirrored from the package body's policy_pack input where the source entry mirrors it; otherwise the source value verbatim. |
| `policy_pack_version` | string | yes | Mirrored. |
| `policy_clause_refs` | array of non-empty strings | yes | Mirrored, ordering preserved. |
| `policy_decision` | string | yes | Closed set `{allow, deny, conditional, withhold, review}`. |

### registry_binding

| Field | Type | Required | Notes |
|---|---|---|---|
| `relying_party_id` | string | yes | Closed identifier grammar. |
| `decision_authority_role` | string | yes | Closed set `{issuer, verifier, relying_party, policy_authority, revocation_source, protected_action_authority}`. |

### action_scope

| Field | Type | Required | Notes |
|---|---|---|---|
| `protected_action_id` | string | yes | Closed set `{release_payment, export_data, change_deployment, rotate_secret, approve_vendor}`. |
| `action_category` | string | yes | Closed set `{financial_release, data_export, deployment_change, secret_rotation, vendor_approval}`. |
| `action_environment` | string | yes | Closed set `{demo, staging, production_simulated}`. |

### scenario_path_summary

A short derived string of the form `<scenario_type>:<decision_status>`.

The runner emits exactly one of:

```text
clean_acceptance:accepted
policy_rejection:rejected
challenge_filed:challenged
withdrawal:withdrawn
supersession:superseded
```

The runner derives the string by joining the source entry's
`scenario_type` and `decision_status` with a single literal `:`. The
verifier re-derives the string the same way and compares it
byte-for-byte to the value in the decision row.

### Decision Fingerprint

`decision_fingerprint` is the bare lowercase hex SHA-256 over the
canonical JSON bytes of a fixed projection of the source decision
entry. The projection is the ordered object:

```text
{
  "decision_id":         <source decision_id>,
  "scenario_type":       <source scenario_type>,
  "decision_status":     <source decision_status>,
  "decision_trigger":    <source decision_trigger>,
  "recorded_at":         <source recorded_at>,
  "decision_subject":    <source decision_subject>,
  "policy_binding":      <source policy_binding>,
  "registry_binding":    <source registry_binding>,
  "action_scope":        <source action_scope>,
  "scenario_specific_state": <source scenario_specific_state>
}
```

Canonical JSON serialization:

```python
json.dumps(projection_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The runner computes the SHA-256 of the resulting UTF-8 bytes and
emits the bare lowercase hex digest as `decision_fingerprint`. The
verifier re-derives the projection and digest from the source entry
and compares byte-for-byte.

The fingerprint does not include `decision_id`-extrinsic narrative
fields and does not include the runner-derived `row_id`,
`source_decision_index`, or `scenario_path_summary`. The fingerprint
is a stable identity hash for the substance of one source decision
entry.

## Coverage Summary

`coverage_summary` is fully derived from `decision_rows[]`. The
runner constructs it deterministically; the verifier re-derives it
the same way and compares byte-for-byte.

| Field | Type | Required | Notes |
|---|---|---|---|
| `decision_count` | integer | yes | Length of `decision_rows[]`. |
| `scenario_types_present` | array of strings | yes | Sorted set (lexicographic ascending) of `scenario_type` values across `decision_rows[]`. |
| `decision_statuses_present` | array of strings | yes | Sorted set of `decision_status` values. |
| `protected_actions_present` | array of strings | yes | Sorted set of `action_scope.protected_action_id` values. |
| `policy_decisions_present` | array of strings | yes | Sorted set of `policy_binding.policy_decision` values. |
| `registry_roles_present` | array of strings | yes | Sorted set of `registry_binding.decision_authority_role` values. |
| `aggregate_row_fingerprint` | string | yes | Bare lowercase hex SHA-256. See "Aggregate Row Fingerprint". |

The five "*_present" arrays are sorted-unique lists with no duplicate
entries. Empty arrays are not permitted: every row contributes one
value to each of the five families. (A 1-row package therefore has
five 1-element arrays.)

### Aggregate Row Fingerprint

`aggregate_row_fingerprint` is the bare lowercase hex SHA-256 over
the canonical JSON bytes of the ordered list of per-row fingerprints:

```text
[decision_rows[0].decision_fingerprint,
 decision_rows[1].decision_fingerprint,
 ...,
 decision_rows[N-1].decision_fingerprint]
```

Canonical JSON serialization:

```python
json.dumps(fingerprint_list, sort_keys=True, separators=(",", ":")) + "\n"
```

`sort_keys` is irrelevant for a list; the ordering of fingerprints in
the list itself is the row order (matching `decision_rows[]`). The
runner emits the bare lowercase hex digest of the resulting UTF-8
bytes.

## Deterministic Serialization

The v0.4.1 runner serializes the decision report with:

```python
json.dumps(report_obj, sort_keys=True, separators=(",", ":")) + "\n"
```

The verifier re-derives the entire decision report from the package
body and the manifest-supplied `decision_report_id` / `generated_at`,
using a byte-identical serializer. Any byte disagreement surfaces as
`gold_decision_report_projection_invalid` (substantive normalization
drift) or `gold_decision_report_summary_invalid` (coverage summary
drift), as appropriate. Top-level structural disagreement before
either of those checks surfaces as `gold_decision_report_not_object`
or `gold_decision_report_schema_invalid`.

## Derivation Inputs

The decision report's byte image depends only on:

- the package body's `package_id`, `governed_reliance_demo_id`, and
  every field reached by the per-row projection (decision_id,
  scenario_type, decision_status, decision_subject, policy_binding,
  registry_binding, action_scope, decision_trigger,
  scenario_specific_state, recorded_at), plus `scope_limitations` and
  `non_claims`;
- the manifest-supplied `decision_report_id` and `generated_at`;
- the manifest-anchored bare lowercase hex SHA-256 of the package
  body bytes (carried as `source_package_sha256`).

The decision report does NOT depend on the conformance report bytes,
on the manifest bytes outside the two named fields, or on any
external context. The verifier re-derives the report from the
package body and the two manifest-supplied scalar fields
(`decision_report_id` and `generated_at`).

## Verifier Notes

The decision-report-specific checks run AFTER all 24 v0.4.0
governed-reliance-package structural checks have passed. The
v0.4.1-introduced ordered checks (in fixed order) are:

```text
check_25  gold_decision_report_not_object
check_26  gold_decision_report_schema_invalid
check_27  gold_decision_report_binding_invalid
check_28  gold_decision_report_projection_invalid
check_29  gold_decision_report_summary_invalid
```

Each defect surfaces with its dedicated reason and is not aliased
into adjacent reasons. The five reasons are reachable independently;
no v0.4.1-introduced defect collapses into one of the inherited 24
v0.4.0 reasons or into `gold_manifest_invalid`.

## Identifier Distinctness

`decision_report_id` MUST NOT equal the inherited conformance
report's `report_id` in the same manifest. Identifier collision
surfaces under `gold_manifest_invalid` as a manifest-level
distinctness violation. The decision report's `decision_report_id`
is otherwise a closed-grammar local identifier with no
transfer-of-reliance meaning. The v0.4.1 decision report
deliberately does NOT carry a generic `report_id` field, so that
binding intent is unambiguous from name alone (`conformance_report_id`
for subject [1], `decision_report_id` for subject [2]).

## Non-Claims

The decision report is not signed, not certified, not approved, not
audited, not a legal instrument, not a transfer of reliance, not
production governance, not federation, and not full Gold. It records
a normalized per-row projection of the local v0.4.0-shaped governed
reliance package body, plus a derived coverage summary, and binds
that projection to the package body by a bare lowercase hex SHA-256
hash anchor. It does not re-evaluate the upstream Silver evidence,
does not opine on policy correctness, does not adjudicate any
specific challenge or withdrawal event, and does not authorize
external acceptance or production reliance.
