# Release Note — ProofRail v0.1.4 Minimal Silver Demo 001

**Suggested repo path:** `docs/releases/2026-06-14-minimal-silver-demo-001-v0.1.4.md`  
**Release date:** 2026-06-14  
**Repo milestone:** `v0.1.4`  
**New Silver artifact schema:** `silver-signed-bundle-assertion-v0.1.0`  
**Demo:** `silver-demo-001`  
**Status:** Demo release / local verification milestone

---

## Summary

ProofRail v0.1.4 introduces **Minimal Silver Demo 001**, the first signed ProofRail evidence-bundle verification demo.

This release adds a **Silver Signed Bundle Assertion v0.1.0** that signs the Bronze v0.1.3 evidence bundle manifest using a demo Ed25519 issuer key. A relying-party verifier then checks the assertion against a local trust policy and verifies the underlying Bronze bundle integrity.

This is not full Silver governance. It is the smallest useful Silver step: signed, relying-party-verifiable evidence portability.

---

## What Changed

### Added Silver Signed Bundle Assertion v0.1.0

New schema:

```text
schemas/silver-signed-bundle-assertion-v0.1.0.md
```

The signed assertion records:

- assertion metadata;
- issuer identity and key ID;
- subject Bronze v0.1.3 bundle manifest;
- raw-byte SHA-256 of the bundle manifest;
- assertion validity window;
- Ed25519 signature;
- public key fingerprint.

The signature is over the **raw bytes** of the Bronze v0.1.3 bundle manifest.

### Added Minimal Silver Demo 001

New demo folder:

```text
demos/silver-demo-001/
```

New demo files:

```text
demos/silver-demo-001/README.md
demos/silver-demo-001/silver-input-v0.1.0.yaml
```

Runtime outputs are generated under:

```text
demos/silver-demo-001/runtime/
```

This directory is gitignored and contains demo keys, the generated trust policy, the signed assertion, and the verification report.

### Added Silver Tooling

New tools:

```text
tools/silver/generate_demo_issuer_v0_1_0.py
tools/silver/sign_bundle_manifest_v0_1_0.py
tools/silver/verify_signed_bundle_assertion_v0_1_0.py
tools/silver/README.md
```

The tools support:

- demo Ed25519 issuer keypair generation;
- local verifier trust policy generation;
- signing a Bronze v0.1.3 evidence bundle manifest;
- verifying issuer trust, signature, expiry, manifest checksum, and underlying bundle integrity.

### Added Silver Regression Test

New regression test:

```text
tests/test_silver_signed_bundle_assertion_v0_1_0.sh
```

The test verifies:

- happy-path signed assertion verification;
- tampered bundle-manifest rejection;
- tampered underlying evidence rejection;
- untrusted issuer rejection;
- expired assertion rejection.

### Added Make Targets

New targets:

```bash
make silver-demo-001
make verify-silver-demo-001
```

Existing Bronze targets continue to pass:

```bash
make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
```

---

## Dependencies

`cryptography` was added to the Python requirements for Ed25519 signing and verification.

Current dependency file:

```text
requirements.txt
```

Expected dependencies:

```text
PyYAML
cryptography
```

---

## Verification

Fresh-clone verification sequence:

```bash
python3 -m pip install -r requirements.txt

make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
make silver-demo-001
make verify-silver-demo-001
```

Expected key pass messages include:

```text
PASS: all 10 evidence checksums verified
PASS: all 16 bundle files verified
PASS: Silver signed bundle assertion verified
PASS: Silver assertion v0.1.0 inline checks valid
PASS: tamper test A — verifier detected tampered manifest
PASS: tamper test B — verifier detected tampered evidence
PASS: trust test — verifier rejected untrusted issuer
PASS: expiry test — verifier rejected expired assertion
=== All Silver v0.1.0 regression tests passed ===
```

The Bronze tamper tests deliberately produce `FAIL:` verifier output as part of their negative tests. Those are expected when followed by the corresponding tamper-detection pass messages.

---

## What This Release Proves

This release demonstrates that:

1. a Bronze v0.1.2 claim can be generated and structurally validated;
2. Bronze v0.1.2 evidence checksums can be verified;
3. a Bronze v0.1.3 evidence bundle manifest can checksum the portable evidence package;
4. a demo issuer can sign the v0.1.3 bundle manifest;
5. a relying-party verifier can verify the signature against a local trust policy;
6. the verifier can reject tampered manifests, tampered evidence, untrusted issuers, and expired assertions.

The main capability added by v0.1.4 is:

> signed relying-party verification of a ProofRail evidence bundle manifest.

---

## What This Release Does Not Prove

This release does not provide:

- production-grade PKI;
- revocation;
- public transparency logs;
- third-party certification;
- issuer accreditation;
- regulatory approval;
- hardware-backed signing;
- enterprise identity federation;
- full Silver governance;
- production deployment conformance.

The correct claim is:

> Minimal Silver Demo 001 demonstrates that a ProofRail Bronze v0.1.3 evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy.

---

## Files Added

```text
schemas/silver-signed-bundle-assertion-v0.1.0.md
tools/silver/generate_demo_issuer_v0_1_0.py
tools/silver/sign_bundle_manifest_v0_1_0.py
tools/silver/verify_signed_bundle_assertion_v0_1_0.py
tools/silver/README.md
demos/silver-demo-001/README.md
demos/silver-demo-001/silver-input-v0.1.0.yaml
tests/test_silver_signed_bundle_assertion_v0_1_0.sh
```

## Files Modified

```text
requirements.txt
.gitignore
Makefile
CLAUDE.md
```

---

## Versioning Notes

This release keeps the versioning separation clear:

```text
Repo milestone: v0.1.4
Silver schema artifact: silver-signed-bundle-assertion-v0.1.0
Bronze claim schema: v0.1.2
Bronze bundle manifest schema: v0.1.3
```

No Bronze schema version bump is required for this release.

---

## Suggested Tag

Suggested Git tag:

```text
minimal-silver-demo-001-v0.1.4
```

---

## Next Possible Iterations

Potential next steps:

1. **Silver revocation list**
   - Add local revocation support for assertion IDs, issuer keys, or bundle IDs.

2. **Signed verification report**
   - Produce a verifier-side report that can itself be signed or archived.

3. **Issuer profile**
   - Separate issuer metadata, scope, and authority from the local trust policy.

4. **Relying-party profile**
   - Define a reusable verifier policy profile for accepting Silver assertions.

5. **Independent verifier package**
   - Demonstrate verification from outside the ProofRail source tree.

---

## Release Interpretation

ProofRail v0.1.4 is a meaningful control-evidence milestone.

ProofRail now can demonstrate a path from:

```text
agentic actuation-control evidence
  → structured Bronze claim
  → evidence checksums
  → portable bundle manifest
  → signed Silver assertion
  → relying-party verification
```

This is still a demo, but it is the first complete ProofRail chain from local control evidence to signed external verification.
