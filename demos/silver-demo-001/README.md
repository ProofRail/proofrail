# Minimal Silver Demo 001

## What This Demo Demonstrates

Minimal Silver Demo 001 demonstrates that a ProofRail Bronze v0.1.3 evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy.

This is the first Silver step in the ProofRail governance progression:

1. **Bronze v0.1.2** — Structured claim with evidence checksums.
2. **Bronze v0.1.3** — Unsigned bundle manifest checksumming the entire portable package (claim, evidence, schemas, tooling).
3. **Silver v0.1.0** — Signed assertion over the bundle manifest, verifiable against a local trust policy.
4. **Silver Revocation v0.1.0** — Local relying-party revocation list allowing trust withdrawal for specific assertions, issuer keys, or bundles.
5. **Silver Verification Report v0.1.0** — Structured, schema-backed verification report recording the verifier's decision, checks, and metadata.

## How to Run

```bash
# End-to-end: generate Bronze claim, bundle manifest, sign, and verify
make silver-demo-001

# Run the full regression test (includes tamper, trust, expiry, and revocation checks)
make verify-silver-demo-001

# Run only the revocation regression test
make verify-silver-revocation-demo-001

# Run only the verification report regression test
make verify-silver-report-demo-001
```

## What Happens

The `silver-demo-001` target runs the following steps:

1. Generates the Bronze v0.1.2 claim from `demos/composed-bronze-demo-001/`.
2. Verifies Bronze v0.1.2 evidence checksums.
3. Generates the Bronze v0.1.3 evidence bundle manifest.
4. Verifies the v0.1.3 bundle manifest.
5. Generates a demo Ed25519 issuer keypair and a verifier trust policy.
6. Generates an empty revocation list for the verifier.
7. Signs the v0.1.3 bundle manifest with the demo issuer's private key.
8. Verifies the signed Silver assertion against the trust policy and revocation list, including signature verification, expiry check, revocation check, and underlying bundle integrity.
9. Validates the verification report against the Silver Verification Report v0.1.0 schema.

## Generated Runtime Files

All runtime outputs are written to `demos/silver-demo-001/runtime/` and are **not committed** to the repository:

```
runtime/issuer-a/private-key.pem          # Demo Ed25519 private key (0600 permissions)
runtime/issuer-a/public-key.pem           # Demo Ed25519 public key
runtime/verifier-b/trust-policy.yaml      # Local trust policy for verifier
runtime/verifier-b/revocation-list.yaml   # Local revocation list for verifier
runtime/silver-signed-bundle-assertion-v0.1.0.yaml   # Signed assertion
runtime/verification-report.json          # Verification report (Silver Verification Report v0.1.0)
```

## Why Private Keys Are Runtime-Only

Private keys are generated fresh each time the Make target runs. They are never committed to version control. The `demos/silver-demo-001/runtime/` directory is listed in `.gitignore`.

This is a demo signing system. Real deployments would use proper key management infrastructure.

## What This Demo Proves

- A Bronze evidence bundle manifest can be signed with Ed25519.
- A relying-party verifier can confirm the signature against a local trust policy.
- The verifier checks issuer trust, key identity, signature validity, assertion expiry, manifest checksum, and underlying bundle integrity.
- Tampering with the manifest, evidence files, trust policy, or assertion expiry is detected.
- A relying-party verifier can reject an otherwise valid assertion via a local revocation list (revoking by assertion ID, issuer key, or bundle hash).
- Verification results are emitted as a structured, schema-backed Silver Verification Report v0.1.0.

## Silver Profile Conformance

Demo 001 can be validated against the Silver Relying-Party Profile v0.2.0 in `silver.base` mode:

```bash
# Validate silver.base profile conformance
make validate-silver-profile-demo-001

# Run the full profile regression test (both modes, negative tests)
make validate-silver-profile-demo-002
```

The `silver.base` profile validates that the verification report is structurally valid, the decision passed, all required checks passed, and limitations are present. When revocation was performed and passed, the profile produces a clean pass. When revocation was not performed, the profile still passes but with reason `profile_requirements_satisfied_with_revocation_warning`.

The conformance report is written to `runtime/silver-profile-conformance-report-v0.2.0.json`.

## What This Demo Does Not Prove

- Production-grade PKI or key management.
- Third-party certification or regulatory approval.
- Production PKI revocation, public certificate revocation, OCSP, or transparency-log-backed revocation. (v0.1.5 demonstrates local demo revocation only.)
- Signed verification reports. The report is unsigned in v0.1.0.
- Gold certification. The verification report is a Silver artifact, not a Gold certification decision.
- Full Silver governance (federation, transparency logs).
- Production deployment conformance.
- That the evidence files are truthful or the deployment is correctly configured.
