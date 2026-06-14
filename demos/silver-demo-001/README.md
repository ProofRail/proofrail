# Minimal Silver Demo 001

## What This Demo Demonstrates

Minimal Silver Demo 001 demonstrates that a ProofRail Bronze v0.1.3 evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy.

This is the first Silver step in the ProofRail governance progression:

1. **Bronze v0.1.2** — Structured claim with evidence checksums.
2. **Bronze v0.1.3** — Unsigned bundle manifest checksumming the entire portable package (claim, evidence, schemas, tooling).
3. **Silver v0.1.0** — Signed assertion over the bundle manifest, verifiable against a local trust policy.

## How to Run

```bash
# End-to-end: generate Bronze claim, bundle manifest, sign, and verify
make silver-demo-001

# Run the full regression test (includes tamper, trust, and expiry checks)
make verify-silver-demo-001
```

## What Happens

The `silver-demo-001` target runs the following steps:

1. Generates the Bronze v0.1.2 claim from `demos/composed-bronze-demo-001/`.
2. Verifies Bronze v0.1.2 evidence checksums.
3. Generates the Bronze v0.1.3 evidence bundle manifest.
4. Verifies the v0.1.3 bundle manifest.
5. Generates a demo Ed25519 issuer keypair and a verifier trust policy.
6. Signs the v0.1.3 bundle manifest with the demo issuer's private key.
7. Verifies the signed Silver assertion against the trust policy, including signature verification, expiry check, and underlying bundle integrity.

## Generated Runtime Files

All runtime outputs are written to `demos/silver-demo-001/runtime/` and are **not committed** to the repository:

```
runtime/issuer-a/private-key.pem          # Demo Ed25519 private key (0600 permissions)
runtime/issuer-a/public-key.pem           # Demo Ed25519 public key
runtime/verifier-b/trust-policy.yaml      # Local trust policy for verifier
runtime/silver-signed-bundle-assertion-v0.1.0.yaml   # Signed assertion
runtime/verification-report.json          # Verification report
```

## Why Private Keys Are Runtime-Only

Private keys are generated fresh each time the Make target runs. They are never committed to version control. The `demos/silver-demo-001/runtime/` directory is listed in `.gitignore`.

This is a demo signing system. Real deployments would use proper key management infrastructure.

## What This Demo Proves

- A Bronze evidence bundle manifest can be signed with Ed25519.
- A relying-party verifier can confirm the signature against a local trust policy.
- The verifier checks issuer trust, key identity, signature validity, assertion expiry, manifest checksum, and underlying bundle integrity.
- Tampering with the manifest, evidence files, trust policy, or assertion expiry is detected.

## What This Demo Does Not Prove

- Production-grade PKI or key management.
- Third-party certification or regulatory approval.
- Full Silver governance (revocation, federation, transparency logs).
- Production deployment conformance.
- That the evidence files are truthful or the deployment is correctly configured.
