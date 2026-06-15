# ProofRail v0.1.5 — Bronze Evidence Bundles and Minimal Silver Revocation

ProofRail v0.1.5 is a cumulative release covering the work from v0.1.2 through v0.1.5.

This release advances ProofRail from a Bronze claim-generation and validation framework into a demonstrable evidence chain:

```text
Bronze claim
  → evidence checksums
  → portable evidence bundle manifest
  → signed Silver bundle assertion
  → relying-party verification
  → local revocation support
```

The release remains demo-grade. It does not claim production certification, public PKI, regulator approval, or full Silver/Gold governance. It demonstrates the core control-evidence mechanics needed for those later layers.

## Highlights

### Bronze v0.1.2 — Evidence Checksum Support

Bronze claims now support an optional `evidence_checksums` mapping.

This allows the files referenced by a Bronze claim to be verified after claim generation.

Added:

* `schemas/bronze-claim-schema-v0.1.2.md`
* `tools/claims/generate_bronze_claim_v0_1_2.py`
* `tools/claims/validate_bronze_claim_v0_1_2.py`
* `tools/claims/verify_bronze_claim_evidence_v0_1_2.py`
* `tests/test_bronze_claim_v0_1_2.sh`

Key capability:

```text
The verifier can detect modified or missing evidence files referenced by the Bronze claim.
```

### Bronze v0.1.3 — Evidence Bundle Manifest

v0.1.3 adds a standalone evidence bundle manifest.

The bundle manifest checksums the portable evidence package, including:

* the Bronze claim file,
* evidence files,
* schema files,
* selected tooling,
* selected documentation.

This solves the claim self-reference problem: the claim cannot contain its own checksum, but an external bundle manifest can checksum the claim.

Added:

* `schemas/bronze-evidence-bundle-manifest-v0.1.3.md`
* `tools/claims/generate_evidence_bundle_manifest_v0_1_3.py`
* `tools/claims/verify_evidence_bundle_manifest_v0_1_3.py`
* `demos/composed-bronze-demo-001/bundle-input-v0.1.3.yaml`
* `tests/test_bronze_evidence_bundle_v0_1_3.sh`

Key capability:

```text
The whole Bronze evidence package can be verified as a portable bundle.
```

### ProofRail v0.1.4 — Minimal Silver Signed Bundle Assertion

v0.1.4 introduces Minimal Silver Demo 001.

A demo issuer signs the Bronze v0.1.3 bundle manifest using Ed25519. A relying-party verifier checks:

* issuer trust policy,
* key ID,
* assertion expiry,
* bundle manifest hash,
* Ed25519 signature,
* underlying Bronze bundle integrity.

Added:

* `schemas/silver-signed-bundle-assertion-v0.1.0.md`
* `tools/silver/generate_demo_issuer_v0_1_0.py`
* `tools/silver/sign_bundle_manifest_v0_1_0.py`
* `tools/silver/verify_signed_bundle_assertion_v0_1_0.py`
* `tools/silver/README.md`
* `demos/silver-demo-001/README.md`
* `demos/silver-demo-001/silver-input-v0.1.0.yaml`
* `tests/test_silver_signed_bundle_assertion_v0_1_0.sh`

Key capability:

```text
A Bronze evidence bundle manifest can be signed and verified by a relying-party verifier using a local trust policy.
```

### ProofRail v0.1.5 — Silver Local Revocation List

v0.1.5 adds local relying-party revocation support.

A verifier can now reject an otherwise valid Silver Signed Bundle Assertion if the assertion, issuer key, or bundle manifest hash appears on a local revocation list.

Added:

* `schemas/silver-revocation-list-v0.1.0.md`
* `tools/silver/generate_demo_revocation_list_v0_1_0.py`
* `tests/test_silver_revocation_list_v0_1_0.sh`

Updated:

* `tools/silver/verify_signed_bundle_assertion_v0_1_0.py`
* `tools/silver/README.md`
* `demos/silver-demo-001/README.md`
* `Makefile`
* `CLAUDE.md`

Key capability:

```text
Trust is now withdrawable in the local verifier context.
```

## Verification

Fresh-clone verification passed using:

```bash
python3 -m pip install -r requirements.txt

make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
make silver-demo-001
make verify-silver-demo-001
make verify-silver-revocation-demo-001
```

Expected pass signals include:

```text
PASS: all 10 evidence checksums verified
PASS: all 16 bundle files verified
PASS: Silver signed bundle assertion verified
PASS: empty revocation list accepted valid assertion
PASS: assertion revocation detected
PASS: issuer key revocation detected
PASS: bundle revocation detected
PASS: Silver revocation list v0.1.0 regression fixture valid
```

The regression tests intentionally generate verifier failures during tamper and revocation tests. Those failures are expected and are treated as passes when the verifier rejects the corrupted, expired, untrusted, or revoked artifact for the intended reason.

## What This Release Demonstrates

ProofRail v0.1.5 demonstrates a complete local evidence chain:

```text
agentic actuation-control evidence
  → structured Bronze claim
  → evidence checksum verification
  → portable evidence bundle manifest
  → signed Silver assertion
  → relying-party verification
  → local revocation of otherwise-valid assertions
```

This is a meaningful step toward Silver-level ProofRail semantics.

Bronze establishes local evidence structure and integrity.

Silver begins to establish portable, signed, relying-party-verifiable evidence.

v0.1.5 adds the critical ability to withdraw local reliance through revocation.

## What This Release Does Not Claim

This release does not provide:

* production PKI,
* public certificate revocation,
* OCSP,
* transparency-log-backed revocation,
* regulator-backed revocation,
* third-party certification,
* full Silver governance,
* Gold certification,
* production deployment assurance.

The correct claim is narrower:

```text
ProofRail v0.1.5 demonstrates that a relying-party verifier can verify a signed ProofRail evidence bundle and reject it if the assertion, issuer key, or bundle manifest hash appears on a local revocation list.
```

## Versioning Notes

This is the first public release since v0.1.1.

The release includes multiple internal milestones:

```text
Bronze Claim Schema v0.1.2
Bronze Evidence Bundle Manifest v0.1.3
Silver Signed Bundle Assertion v0.1.0
Silver Revocation List v0.1.0
Repo release v0.1.5
```

The main Git tag for this release is:

```text
v0.1.5
```

## Suggested Next Steps

Possible next milestones:

1. **v0.1.6 — Structured Silver Verification Report**

   * Formalize the verifier report as a schema-backed artifact.

2. **v0.1.7 — Independent Verifier Demo**

   * Demonstrate relying-party verification from outside the main source tree.

3. **v0.2.0 — Silver Relying-Party Profile**

   * Define what a verifier must check before accepting a Silver assertion.

4. **v0.3.0 — Minimal Gold Demo 001**

   * Introduce governed certification decisions over verified Silver evidence packages.

