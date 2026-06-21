# Silver Multi-Principal Authority Fixtures — v0.2.3

This directory contains the canonical authority fixture, request fixtures, expected decision reports, and invalid fixture variants for ProofRail Silver v0.2.3.

## Structure

```
authority-fixture.yaml              # Canonical authority fixture
requests/                           # Protected action request fixtures
  allow-payment-release-direct.json
  allow-vendor-approval-direct.json
  deny-payment-release-unauthorized-vendor.json
  deny-delegation-laundering.json
  deny-data-export-out-of-scope.json
  deny-deploy-change-out-of-scope.json
  deny-revoked-authority.json
expected/                           # Expected decision reports
  allow-payment-release-direct.json
  allow-vendor-approval-direct.json
  deny-payment-release-unauthorized-vendor.json
  deny-delegation-laundering.json
  deny-data-export-out-of-scope.json
  deny-deploy-change-out-of-scope.json
  deny-revoked-authority.json
invalid-fixtures/                   # Invalid fixture variants
  invalid-delegation-laundering.yaml
```

## Running

```bash
# Validate the canonical fixture
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml

# Evaluate a request
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --request fixtures/silver-multi-principal-authority-v0.2.3/requests/allow-payment-release-direct.json \
  --decision-time 2026-06-21T10:00:00Z \
  --output /tmp/decision-report.json

# Run full regression test
bash tests/test_silver_multi_principal_authority_v0_2_3.sh
```

## What Each Request Tests

| Request | Expected | Tests |
|---|---|---|
| REQ-001: allow-payment-release-direct | allow | Direct grant, valid constraints |
| REQ-002: allow-vendor-approval-direct | allow | Direct grant before revocation time |
| REQ-003: deny-payment-release-unauthorized-vendor | deny | Subject mismatch (wrong principal) |
| REQ-004: deny-delegation-laundering | deny | Subject mismatch (delegation laundering) |
| REQ-005: deny-data-export-out-of-scope | deny | Constraint violation (dataset not in list) |
| REQ-006: deny-deploy-change-out-of-scope | deny | Constraint violation (environment not in list) |
| REQ-007: deny-revoked-authority | deny | Authority revoked at decision time |

## Limitations

- Local deterministic authority fixture only.
- No live actuators invoked.
- Not a production authorization system.
- Not prompt-injection detection.
- Not Gold certification.
