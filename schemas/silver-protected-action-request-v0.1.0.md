# ProofRail Silver Protected Action Request Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-principal authority evaluation

---

## 1. Purpose

The Silver Protected Action Request schema defines a structured JSON format for requesting evaluation of a protected action against a multi-principal authority fixture.

A request specifies who is requesting, what action, with what parameters, and under what claimed authority.

---

## 2. Format

JSON. UTF-8 encoded. Single object.

---

## 3. Top-Level Structure

```json
{
  "request_type": "proofrail.silver.protected_action_request",
  "request_version": "v0.1.0",
  "request_id": "<string>",
  "requesting_principal_id": "<string>",
  "action_id": "<string>",
  "parameters": {},
  "claimed_authority": {
    "grant_id": "<string>"
  },
  "context": {
    "source": "fixture",
    "instruction_id": "<string>"
  }
}
```

All top-level fields are required.

---

## 4. Field Descriptions

| Field | Type | Description |
|---|---|---|
| `request_type` | string | Must be `proofrail.silver.protected_action_request` |
| `request_version` | string | Must be `v0.1.0` |
| `request_id` | string | Unique request identifier |
| `requesting_principal_id` | string | Principal making the request |
| `action_id` | string | Protected action being requested |
| `parameters` | object | Action-specific parameters for constraint evaluation |
| `claimed_authority` | object | Authority claim (contains `grant_id`) |
| `context` | object | Request context metadata |

---

## 5. Parameters

The `parameters` object contains action-specific values used for constraint evaluation:

| Parameter key | Type | Used by constraint |
|---|---|---|
| `amount_usd` | number | `max_amount_usd` |
| `vendor_id` | string | `allowed_vendor_ids` |
| `dataset_id` | string | `allowed_dataset_ids` |
| `environment` | string | `allowed_environments` |
| `change_type` | string | `allowed_change_types` |

---

## 6. Claimed Authority

The `claimed_authority` object identifies the grant under which the request is made:

```json
{
  "grant_id": "<string>"
}
```

The evaluator resolves this grant ID against the authority fixture.

---

## 7. Context

The `context` object provides metadata about the request origin:

```json
{
  "source": "fixture",
  "instruction_id": "<string>"
}
```

For fixture-based evaluation, `source` is always `"fixture"`.

---

## 8. Examples

See `fixtures/silver-multi-principal-authority-v0.2.3/requests/` for canonical request fixtures.

---

## 9. Changelog

| Version | Change |
|---|---|
| v0.1.0 | Initial schema: request type, principal, action, parameters, claimed authority, context |
