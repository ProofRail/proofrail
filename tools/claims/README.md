# ProofRail Claim Tools

This directory contains lightweight local tooling for generating and validating ProofRail claim YAML files.

## Current supported schemas

- Bronze Claim Schema v0.1.1
- Bronze Claim Schema v0.1.2

## Validator

The validator performs structural validation only. It does not certify production conformance, inspect live systems, verify evidence truthfulness, or replace third-party review.

```bash
# v0.1.1
python3 tools/claims/validate_bronze_claim_v0_1_1.py \
  demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml

# v0.1.2
python3 tools/claims/validate_bronze_claim_v0_1_2.py \
  demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml
```

## Evidence Verifier (v0.1.2+)

The evidence verifier recomputes SHA-256 checksums for all evidence files listed in the claim's `evidence_checksums` mapping and compares them against the recorded values. This detects file tampering or corruption after claim generation.

```bash
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py \
  demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml \
  demos/composed-bronze-demo-001
```

The verifier exits 0 on success, 1 on checksum mismatch or missing files, and 2 on usage error.

## Evidence Bundle Manifest (v0.1.3)

### Bundle Manifest Generator

The bundle manifest generator checksums the entire portable evidence package — claim file, evidence files, schema documents, tooling scripts, and documentation — producing a standalone manifest YAML.

```bash
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py \
  demos/composed-bronze-demo-001

python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py \
  demos/composed-bronze-demo-001 \
  --input bundle-input-v0.1.3.yaml \
  --output evidence-bundle-manifest-v0.1.3.yaml
```

The generator exits 0 on success, 1 if required files are missing (unless `--allow-missing`), and 2 on usage error.

### Bundle Manifest Verifier

The bundle manifest verifier recomputes SHA-256 checksums and file sizes for all files listed in a bundle manifest and verifies they match the recorded values.

```bash
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py \
  demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml \
  demos/composed-bronze-demo-001
```

The verifier exits 0 on success, 1 on checksum mismatch, size mismatch, or missing files, and 2 on usage error.
