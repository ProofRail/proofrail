# ProofRail Claim Tools

This directory contains lightweight local tooling for generating and validating ProofRail claim YAML files.

## Current supported schema

- Bronze Claim Schema v0.1.1

## Validator

The validator performs structural validation only. It does not certify production conformance, inspect live systems, verify evidence truthfulness, or replace third-party review.

```bash
python3 tools/claims/validate_bronze_claim_v0_1_1.py \
  demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml
