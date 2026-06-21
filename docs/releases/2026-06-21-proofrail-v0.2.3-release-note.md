# ProofRail v0.2.3 - Silver Multi-Principal Authority Fixtures

Release date: 2026-06-21

Git tag: `v0.2.3`

ProofRail v0.2.3 adds deterministic multi-principal authority fixtures for Silver.

Earlier v0.2.x releases tightened Silver relying-party acceptance and made verifier outputs attestable. v0.2.3 adds the next foundation for the planned multi-agent trust-boundary demo: structured principals, protected actions, scoped authority grants, delegation rules, revocation-aware evaluation, and local decision reports.

The narrow claim is:

> A protected action request is allowed only when the acting principal has valid, scoped, non-revoked authority for that action and its constraints.

## What Changed

This release adds a deterministic authority evaluation layer for multi-principal Silver fixtures.

The canonical fixture models:

- `buyerorg.agent`
- `vendororg.agent`
- `verifier.auditor`
- supporting admin principals for coherent grant issuance

The protected actions are simulated identifiers only:

- `payment.release`
- `vendor.approve`
- `data.export`
- `deploy.change`

The evaluator produces decision reports. It does not execute any protected action.

Every decision report includes:

```json
"execution": {
  "performed": false,
  "reason": "decision_report_only"
}
```

## New Artifacts

Added schemas:

- `schemas/silver-multi-principal-authority-fixture-v0.1.0.md`
- `schemas/silver-protected-action-request-v0.1.0.md`
- `schemas/silver-protected-action-decision-report-v0.1.0.md`

Added documentation:

- `docs/silver/silver-multi-principal-authority-fixtures-v0.2.3.md`
- `fixtures/silver-multi-principal-authority-v0.2.3/README.md`

Added fixture set:

- `fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml`
- seven protected action request fixtures
- seven expected decision result fixtures
- `fixtures/silver-multi-principal-authority-v0.2.3/invalid-fixtures/invalid-delegation-laundering.yaml`

Added tools:

- `tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py`
- `tools/silver/evaluate_multi_principal_authority_v0_1_0.py`

Added test:

- `tests/test_silver_multi_principal_authority_v0_2_3.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`

## Authority Validator

The fixture validator checks the structural integrity of the multi-principal authority fixture.

Example:

```bash
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml
```

It checks canonical principals, protected actions, grant references, delegation rules, constraint narrowing, revocation targets, and limitations.

The canonical fixture must pass. The invalid delegation fixture must fail with a stable delegation failure reason.

## Authority Evaluator

The evaluator processes a structured protected action request against the fixture and emits a decision report.

Example:

```bash
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --request fixtures/silver-multi-principal-authority-v0.2.3/requests/allow-payment-release-direct.json \
  --decision-time 2026-06-21T10:00:00Z \
  --output /tmp/proofrail-authority-decision.json
```

Deny decisions are successful evaluator outputs, not tool failures. The evaluator exits successfully when it produces a well-formed allow or deny decision report.

Stable decision reasons include:

- `authority_requirements_satisfied`
- `authority_subject_mismatch`
- `authority_revoked`
- `delegation_not_permitted`
- `delegation_chain_invalid`
- `scope_not_authorized`
- `constraint_not_satisfied`
- `constraint_value_missing`

## Regression Coverage

The v0.2.3 regression test covers:

- canonical fixture validation;
- direct payment release allowed;
- direct vendor approval allowed before revocation;
- unauthorized vendor payment release denied;
- delegation laundering denied;
- data export outside delegated scope denied;
- deploy change outside staging scope denied;
- revoked vendor approval denied after the revocation time;
- invalid delegation fixture rejected;
- deny decisions exit successfully when a decision report is produced;
- malformed input exits nonzero;
- every decision report states that no protected action was executed.

Primary commands:

```bash
make validate-silver-authority-fixtures-v0-2-3
make verify-silver-authority-v0-2-3
make verify-silver-all
git diff --check
```

The implementation run reported all of these passing.

## Why This Matters

v0.2.3 isolates the core trust-boundary claim before the larger multi-agent demo:

> In a multi-principal agent environment, trust does not attach to the agent. Trust attaches to scoped authority, controlled action paths, and independently inspectable decision evidence.

For this release, the evidence is deterministic and local: fixtures, requests, decision reports, and regression tests.

## What This Release Does Not Claim

ProofRail v0.2.3 does not claim:

- a live multi-agent runtime;
- prompt-injection detection;
- model behavior evaluation;
- production authorization infrastructure;
- production PKI;
- Gold certification;
- third-party certification;
- regulator approval;
- production deployment assurance;
- governed institutional acceptance.

The correct boundary is:

> Silver v0.2.3 makes multi-principal authority executable as deterministic local fixtures. It does not make agents trustworthy or certify a deployment.

## What Comes Next

v0.2.3 provides the authority fixture foundation.

Next:

- v0.2.4 should add a deterministic multi-agent attack harness and evidence production;
- v0.2.5 should package the multi-agent trust-boundary demo and define the first Gold boundary.

The intended progression is:

```text
v0.2.1:
  stricter Silver reliance and cleaner handoff

v0.2.2:
  verifier output attribution and tamper evidence

v0.2.3:
  executable multi-principal authority fixtures

v0.2.4:
  deterministic attack harness and evidence production

v0.2.5:
  packaged multi-agent trust-boundary demo and first Gold boundary
```

## Summary

ProofRail v0.2.3 makes scoped authority explicit and executable.

It does not ask whether an agent is trustworthy. It asks whether a protected action request has the right scoped, non-revoked authority to proceed, and records the answer in a deterministic decision report.
