# ProofRail Silver Protected Action Decision Report Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-principal authority evaluation

---

## 1. Purpose

The Silver Protected Action Decision Report schema defines a structured JSON format for recording the outcome of evaluating a protected action request against a multi-principal authority fixture.

A decision report records whether the request was allowed or denied, which checks were performed, the delegation chain, and explicit evidence that no protected action was executed.

---

## 2. Format

JSON. UTF-8 encoded. Single object.

---

## 3. Top-Level Structure

```json
{
  "report_type": "proofrail.silver.protected_action_decision_report",
  "report_version": "v0.1.0",
  "fixture_id": "<string>",
  "request_id": "<string>",
  "decision_time": "<ISO-8601>",
  "decision": {
    "status": "allow|deny",
    "reason": "<string>"
  },
  "execution": {
    "performed": false,
    "reason": "decision_report_only"
  },
  "principal": {
    "requesting_principal_id": "<string>"
  },
  "action": {
    "action_id": "<string>",
    "required_scope": "<string>"
  },
  "authority": {
    "claimed_grant_id": "<string>",
    "matched_grant_id": "<string>|null",
    "delegation_chain": []
  },
  "checks": [],
  "limitations": []
}
```

All top-level fields are required.

---

## 4. Field Descriptions

| Field | Type | Description |
|---|---|---|
| `report_type` | string | Must be `proofrail.silver.protected_action_decision_report` |
| `report_version` | string | Must be `v0.1.0` |
| `fixture_id` | string | Fixture that was evaluated against |
| `request_id` | string | Request that was evaluated |
| `decision_time` | string | ISO-8601 timestamp of evaluation |
| `decision` | object | Decision outcome |
| `execution` | object | Execution evidence (always `performed: false`) |
| `principal` | object | Requesting principal identity |
| `action` | object | Requested action metadata |
| `authority` | object | Authority resolution result |
| `checks` | array | Ordered check results |
| `limitations` | array | Non-empty list of limitation strings |

---

## 5. Decision

```json
{
  "status": "allow",
  "reason": "authority_requirements_satisfied"
}
```

Or:

```json
{
  "status": "deny",
  "reason": "<deny_reason_code>"
}
```

### 5.1 Decision Reason Codes

| Reason | Status | Description |
|---|---|---|
| `authority_requirements_satisfied` | allow | All checks passed |
| `invalid_request_structure` | deny | Request type/version/fields malformed |
| `unknown_principal` | deny | Principal not in fixture |
| `unknown_protected_action` | deny | Action not in fixture |
| `unknown_authority_grant` | deny | Grant ID not in fixture |
| `authority_subject_mismatch` | deny | Grant subject != requesting principal |
| `delegation_chain_invalid` | deny | Delegation chain broken or cyclic |
| `delegation_not_permitted` | deny | Parent grant disallows delegation |
| `authority_revoked` | deny | Grant or chain member revoked at decision time |
| `authority_expired` | deny | Grant or chain member expired at decision time |
| `scope_not_authorized` | deny | Action scope not in grant scopes |
| `delegation_scope_expanded` | deny | Delegated scopes exceed parent |
| `constraint_not_satisfied` | deny | Request parameter violates constraint |
| `constraint_value_missing` | deny | Required request parameter absent |

---

## 6. Execution Evidence

```json
{
  "performed": false,
  "reason": "decision_report_only"
}
```

The evaluator never executes a protected action. This field provides structural proof.

---

## 7. Checks

An ordered array of check results:

```json
[
  {
    "check_id": "<string>",
    "status": "pass|fail",
    "detail": "<string>"
  }
]
```

All checks up to and including the first failing check are recorded. If all pass, all checks are recorded.

---

## 8. Authority Resolution

```json
{
  "claimed_grant_id": "<string>",
  "matched_grant_id": "<string>|null",
  "delegation_chain": ["<grant_id>", ...]
}
```

`delegation_chain` lists grant IDs from the claimed grant to the root (direct) grant. Empty for direct grants that are matched directly.

---

## 9. Limitations

A required, non-empty list of strings documenting what the decision report does not claim.

---

## 10. Examples

See `fixtures/silver-multi-principal-authority-v0.2.3/expected/` for canonical decision report fixtures.

---

## 11. Changelog

| Version | Change |
|---|---|
| v0.1.0 | Initial schema: decision, execution evidence, checks, authority resolution, limitations |
