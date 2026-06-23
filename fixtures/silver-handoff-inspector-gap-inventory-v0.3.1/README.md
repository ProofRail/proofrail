# Fixtures — Silver Handoff Inspector + Gold Gap Inventory (v0.3.1)

This directory holds the committed Gold-boundary requirement set
fixture consumed by `tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py`
to produce a v0.3.1 Silver handoff inspection package.

## Files

| File | Role |
|---|---|
| `gold-boundary-requirements.json` | Closed, 13-requirement Gold-boundary requirement set. |

## Requirement coverage (13 domains)

The fixture covers exactly one requirement per each of the 13 required
domains. The distribution reflects what ProofRail Silver actually
provides versus what a future Gold layer would still need to add:

| Domain | `expected_gap_status` | Notes |
|---|---|---|
| `governed_acceptance_policy` | `gold_prerequisite_unmet` | The v0.2.8 acceptance policy is a fictional local demo policy. |
| `named_acceptance_authority` | `gold_prerequisite_unmet` | The v0.2.8 relying party is fictional. |
| `independent_verifier_identity` | `silver_evidence_present` | Silver v0.2.2 verifier output attestation is a concrete Silver artifact addressing this domain. |
| `evidence_retention_policy` | `gold_prerequisite_unmet` | The v0.3.0 handoff is portable; no retention policy. |
| `change_control_policy` | `gold_prerequisite_unmet` | No change-control attestation accompanies the handoff. |
| `revocation_operations` | `silver_evidence_partial` | Silver v0.2.9 drill is a local evidence artifact, not an operational process. |
| `challenge_dispute_process` | `silver_evidence_partial` | Silver v0.2.9 classifies challenges; it does not adjudicate them. |
| `audit_trail_and_review` | `silver_evidence_partial` | Silver v0.2.4 / v0.2.5 produce hash-anchored evidence; no independent reviewer. |
| `runtime_operating_boundary` | `silver_evidence_partial` | Silver v0.2.4 / v0.2.7 produce harness and simulated-gateway evidence; no real substrate. |
| `external_accountability` | `gold_prerequisite_unmet` | The handoff is bound to a fictional local relying party. |
| `public_or_shared_acceptance_record` | `gold_prerequisite_unmet` | No public acceptance ledger is produced. |
| `legal_or_contractual_basis` | `out_of_scope_for_silver` | Legal effect is outside ProofRail's scope. |
| `production_use_authorization` | `out_of_scope_for_silver` | Production authorization is outside ProofRail's scope. |

Counts: `silver_evidence_present` = 1, `silver_evidence_partial` = 4,
`gold_prerequisite_unmet` = 6, `out_of_scope_for_silver` = 2.

## Status semantics (re-stated)

- `silver_evidence_present` — Relevant Silver evidence is present.
  **It does NOT mean the Gold prerequisite is satisfied.** It means the
  inspection can point at a concrete, hash-anchored Silver artifact
  that addresses the domain.
- `silver_evidence_partial` — Silver provides only a drill, fixture,
  or local artifact, not an operational process. The Gold prerequisite
  is not fully addressed.
- `gold_prerequisite_unmet` — Silver does not address the domain. The
  gap is preserved in the inventory.
- `out_of_scope_for_silver` — The domain is outside what any ProofRail
  Silver release is intended to provide.

## Non-claims

This requirement set:

- is not a Gold certification standard;
- is not a Gold readiness scorecard;
- is not legal advice, regulator approval, or auditor approval;
- is not a compliance crosswalk to any external framework;
- is a local ProofRail demo boundary inventory only.

A v0.3.1 Silver handoff inspection report bound to this fixture
preserves unresolved Gold prerequisites. It does not certify, approve,
audit, or transfer reliance.
