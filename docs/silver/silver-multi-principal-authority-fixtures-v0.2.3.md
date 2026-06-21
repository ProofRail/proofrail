# Silver Multi-Principal Authority Fixtures — v0.2.3

**Status:** Draft / Demo-informed walkthrough
**Date:** 2026-06-21

---

## What v0.2.3 Adds

Silver v0.2.3 adds deterministic, executable fixtures for scoped multi-principal authority and delegation. A local evaluator processes structured protected-action requests against an authority fixture (principals, grants, delegation chains, constraints, revocations) and emits decision reports.

No live agents. No LLM calls. No real actuators.

Core claim:

> A protected action request is allowed only when the acting principal has valid, scoped, non-revoked authority for that action and its constraints.

---

## Authority Model

The authority model is:

1. **Principals** hold identity. They do not inherently have authority.
2. **Protected actions** define what can be authorized.
3. **Authority grants** bind a principal to a set of scopes with constraints.
4. **Delegation** allows a grant holder to issue narrower grants to other principals.
5. **Revocations** withdraw authority at a specific point in time.
6. **Decision-time evaluation** determines whether a request is allowed at a given moment.

---

## Principals

Five canonical principals in two organizations plus an auditor:

| Principal ID | Type | Organization | Role |
|---|---|---|---|
| `buyerorg.admin` | admin | BuyerOrg | Grant issuer |
| `buyerorg.agent` | agent | BuyerOrg | Operational agent |
| `vendororg.admin` | admin | VendorOrg | Grant issuer |
| `vendororg.agent` | agent | VendorOrg | Operational agent |
| `verifier.auditor` | verifier | AuditorOrg | Auditor / verifier |

Admins issue grants. Agents receive authority and act. The verifier audits.

---

## Protected Actions

Four canonical protected actions:

| Action ID | Scope | Description |
|---|---|---|
| `payment.release` | `payment.release` | Release a payment to a vendor |
| `vendor.approve` | `vendor.approve` | Approve a vendor relationship |
| `data.export` | `data.export` | Export a dataset |
| `deploy.change` | `deploy.change` | Deploy a configuration change |

All actuators are simulated. No real payment, approval, export, or deployment occurs.

---

## Grants and Delegation

Authority flows from admins (issuers) to agents (subjects) via direct grants. Agents may delegate narrower authority to other principals if the grant permits it.

**Direct grant example:**
- BuyerOrg Admin → BuyerOrg Agent: payment.release (max $5000, vendororg only)

**Delegated grant example:**
- BuyerOrg Agent → Verifier/Auditor: data.export (audit-summary only, narrowed from parent)

Delegation rules:
- Scopes can only narrow (subset of parent).
- Constraints can only tighten (numeric <=, lists subset).
- Parent must have `delegation.permitted == true`.
- Omitting a parent constraint weakens authority (invalid).
- Adding a new constraint narrows authority (valid).

---

## Constraints

Constraints limit authority within a scope:

| Constraint | Type | Evaluation |
|---|---|---|
| `max_amount_usd` | numeric | request amount <= grant max |
| `allowed_vendor_ids` | list | request vendor in grant list |
| `allowed_dataset_ids` | list | request dataset in grant list |
| `allowed_environments` | list | request environment in grant list |
| `allowed_change_types` | list | request change_type in grant list |

Missing request parameters for required constraints produce `constraint_value_missing` denials.

---

## Revocation

Revocations withdraw authority at a specific time. A grant is revoked if `revoked_at <= decision_time`.

When evaluating delegated grants, every grant in the chain is checked for revocation. A revoked parent invalidates all downstream delegated authority.

---

## Decision-Time Evaluation

The evaluator performs 10 ordered checks (short-circuit on first deny):

1. **request_structure** — Valid request format
2. **principal_known** — Principal exists in fixture
3. **action_known** — Action exists in fixture
4. **grant_exists** — Claimed grant exists
5. **grant_subject_match** — Grant subject == requesting principal
6. **delegation_chain_valid** — Chain from grant to root is valid
7. **grant_not_revoked** — No applicable revocation at decision time
8. **grant_not_expired** — All grants in chain are within validity period
9. **scope_authorized** — Action scope in grant scopes
10. **constraints_satisfied** — Request parameters satisfy all constraints

All passing checks are recorded. The first failing check determines the deny reason.

---

## What This Does Not Claim

- Not a live multi-agent runtime.
- Not prompt-injection detection.
- Not model behavior evaluation.
- Not production authorization infrastructure.
- Not Gold certification.
- Not a replacement for OAuth, RBAC, or enterprise IAM.

---

## Relationship to v0.2.4 / Gold

v0.2.3 makes multi-principal authority executable as deterministic local fixtures. It establishes the semantics that a future governed layer (Gold) could rely on for multi-party authority decisions.

v0.2.3 does not implement:
- Multi-party approval workflows.
- Challenge/response governance.
- Institutional acceptance decisions.
- Certification over authority models.

---

## Limitations

Every decision report includes explicit limitations:

1. Local deterministic authority fixture only.
2. No live actuators invoked.
3. Not a production authorization system.
4. Not prompt-injection detection.
5. Not Gold certification.

The `execution.performed` field is always `false` in every decision report, providing structural proof that no actuator was invoked.
