# ProofRail Silver Multi-Principal Authority Fixture Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-principal authority fixtures

---

## 1. Purpose

The Silver Multi-Principal Authority Fixture schema defines a structured YAML format for expressing scoped multi-principal authority relationships over protected actions.

A fixture contains principals, protected actions, authority grants (direct and delegated), constraints, revocation entries, and explicit limitations.

The purpose of this schema is to enable deterministic, local evaluation of authority claims without invoking any live actuator, LLM, or production authorization system.

---

## 2. Format

YAML. UTF-8 encoded. Single document.

---

## 3. Top-Level Structure

```yaml
fixture_type: proofrail.silver.multi_principal_authority_fixture
fixture_version: v0.1.0
fixture_id: <string>
description: <string>
principals: []
protected_actions: []
authority_grants: []
revocations: []
limitations: []
```

All top-level fields are required.

---

## 4. Principals

Each principal entry:

```yaml
- principal_id: <string>         # unique identifier
  principal_type: <string>       # admin | agent | verifier
  organization: <string>         # organizational affiliation
  display_name: <string>         # human-readable label
  roles: [<string>, ...]         # role tags
```

Required fields: `principal_id`, `principal_type`, `organization`, `display_name`, `roles`.

Canonical principals (must be present in any conformant fixture):
- `buyerorg.agent`
- `vendororg.agent`
- `verifier.auditor`

---

## 5. Protected Actions

Each protected action entry:

```yaml
- action_id: <string>           # unique identifier
  required_scope: <string>      # scope value required in grants
  actuator_type: simulated      # always simulated in fixtures
```

Required fields: `action_id`, `required_scope`, `actuator_type`.

Canonical protected actions (must be present in any conformant fixture):
- `payment.release`
- `vendor.approve`
- `data.export`
- `deploy.change`

---

## 6. Authority Grants

Each authority grant entry:

```yaml
- grant_id: <string>                    # unique identifier
  grant_type: direct | delegated        # direct = root, delegated = chain
  issuer_principal_id: <string>         # who issued this grant
  subject_principal_id: <string>        # who receives authority
  scopes: [<string>, ...]              # authorized scope values
  constraints: {}                       # constraint key-value pairs
  delegation:
    permitted: true | false             # whether further delegation is allowed
  # Optional fields:
  parent_grant_id: <string>            # required for delegated grants
  issued_at: <ISO-8601>                # optional validity start
  expires_at: <ISO-8601>               # optional validity end
```

Required fields: `grant_id`, `grant_type`, `issuer_principal_id`, `subject_principal_id`, `scopes`, `constraints`, `delegation`.

For `grant_type: delegated`, `parent_grant_id` is additionally required.

### 6.1 Constraint Types

| Constraint key | Type | Evaluation |
|---|---|---|
| `max_amount_usd` | numeric | request value `<=` grant value |
| `allowed_vendor_ids` | list | request value `in` grant list |
| `allowed_dataset_ids` | list | request value `in` grant list |
| `allowed_environments` | list | request value `in` grant list |
| `allowed_change_types` | list | request value `in` grant list |

### 6.2 Delegation Rules

- Delegated grant scopes must be a subset of parent grant scopes.
- Delegated grant constraints must not weaken parent constraints:
  - Numeric constraints: child `<=` parent.
  - List constraints: child must be subset of parent.
  - Child omitting a parent constraint = weakening = invalid.
  - Child adding a new constraint absent from parent = narrowing = valid.
- Parent grant must have `delegation.permitted == true`.

---

## 7. Revocations

Each revocation entry:

```yaml
- revocation_id: <string>
  target_type: authority_grant
  target_id: <string>            # grant_id being revoked
  revoked_at: <ISO-8601>        # revocation effective time
  reason: <string>              # human-readable reason
```

Required fields: `revocation_id`, `target_type`, `target_id`, `revoked_at`, `reason`.

### 7.1 Revocation Semantics

A grant is considered revoked at decision time `T` if there exists a revocation entry where `target_id == grant_id` and `revoked_at <= T`.

When evaluating delegated grants, all grants in the delegation chain are checked for revocation.

---

## 8. Decision-Time Semantics

Authority evaluation is performed against an explicit `decision_time` parameter. This enables deterministic evaluation of time-sensitive authority (expiry, revocation) without depending on wall clock time.

---

## 9. Limitations

The `limitations` field is a required, non-empty list of strings documenting what the fixture does not claim.

---

## 10. Examples

See `fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml` for the canonical conformant fixture.

---

## 11. Changelog

| Version | Change |
|---|---|
| v0.1.0 | Initial schema: principals, protected actions, authority grants, delegation, constraints, revocations, limitations |
