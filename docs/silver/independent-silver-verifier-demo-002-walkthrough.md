# ProofRail Independent Silver Verifier Demo 002 — Walkthrough

**Suggested repo path:** `docs/walkthroughs/independent-silver-verifier-demo-002-walkthrough.md`  
**Demo:** `silver-demo-002-independent-verifier`  
**Repo milestone:** `v0.1.7`  
**Status:** Reviewed draft

---

## 1. Purpose

Silver Demo 002 demonstrates that a ProofRail Silver evidence package can be verified by an independent local verifier operating outside the original source tree.

This is the practical difference between Demo 001 and Demo 002:

```text
Silver Demo 001
  Internal demo flow inside the ProofRail repository.

Silver Demo 002
  Exported verification package plus independent verifier running outside the original repo checkout.
```

The demo is still local and demo-grade. It does not prove production verifier distribution, supply-chain integrity, third-party certification, or Gold governance.

It proves a narrower and important point:

> A relying party can verify a prepared ProofRail Silver evidence package without relying on the main ProofRail repository’s internal verifier layout.

---

## 2. Background

Before v0.1.7, ProofRail had:

1. **Bronze v0.1.2** — evidence checksums inside the Bronze claim.
2. **Bronze v0.1.3** — a bundle manifest for the portable evidence package.
3. **Silver Signed Bundle Assertion v0.1.0** — a signature over the bundle manifest.
4. **Silver Revocation List v0.1.0** — local relying-party revocation.
5. **Silver Verification Report v0.1.0** — structured verifier output.

Those pieces demonstrated a complete Silver flow, but the verifier still lived inside the same repository structure as the evidence-producing demo.

v0.1.7 adds a new separation boundary.

---

## 3. New Components

### 3.1 Export Tool

```text
tools/silver/export_independent_verification_package_v0_1_0.py
```

This tool exports a self-contained verification package from the existing Bronze and Silver Demo 001 artifacts.

It copies the necessary evidence package, signed assertion, trust policy, revocation list, schemas, and reference files into a portable package.

### 3.2 Independent Verifier

```text
demos/silver-demo-002-independent-verifier/verifier/independent_verify.py
```

This verifier performs the core Silver checks without importing or invoking:

```text
tools/silver/verify_signed_bundle_assertion_v0_1_0.py
tools/claims/verify_evidence_bundle_manifest_v0_1_3.py
```

It implements the necessary verification logic inline.

### 3.3 Package Documentation

```text
demos/silver-demo-002-independent-verifier/package-template/README.md
```

This explains the exported package layout and why the package preserves a subset of the original repo structure.

---

## 4. Why the Package Uses `source-repo-subset/`

The Bronze bundle manifest and Silver signed assertion contain relative paths.

The Silver assertion signs the **raw bytes** of the Bronze v0.1.3 bundle manifest.

If the export tool rewrote the bundle manifest paths, the manifest bytes would change, and the existing Ed25519 signature would no longer verify.

To avoid that, the export tool preserves the original bundle manifest bytes and creates a package layout like this:

```text
package/
  package-manifest.yaml
  source-repo-subset/
    demos/
      composed-bronze-demo-001/
      silver-demo-001/
    schemas/
    tools/
```

This keeps relative paths meaningful without rewriting the signed bundle manifest.

The package is larger than a minimal hand-curated verifier payload, but it proves the essential point: a relying-party verifier can operate outside the original repo checkout.

---

## 5. What the Independent Verifier Checks

The independent verifier performs the same conceptual checks as the main Silver verifier:

1. issuer trust;
2. key ID trust;
3. algorithm;
4. validity window;
5. bundle manifest raw-byte SHA-256;
6. revocation list;
7. Ed25519 signature over the raw bundle manifest bytes;
8. underlying bundle manifest file integrity.

The underlying bundle verification is implemented inline. The independent verifier loads the bundle manifest, iterates through its file list, recomputes raw-byte SHA-256 digests, compares sizes, and counts verified files.

This is not merely a wrapper around the main verifier.

---

## 6. How to Run

From the repository root:

```bash
python3 -m pip install -r requirements.txt

make silver-demo-001
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
```

The full chain is:

```bash
make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
make silver-demo-001
make verify-silver-demo-001
make verify-silver-revocation-demo-001
make verify-silver-report-demo-001
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
```

---

## 7. What the Regression Test Does

The regression test is:

```text
tests/test_independent_silver_verifier_v0_1_0.sh
```

It performs:

1. Bronze v0.1.2 claim generation.
2. Bronze v0.1.2 evidence checksum verification.
3. Bronze v0.1.3 bundle manifest generation.
4. Bronze v0.1.3 bundle manifest verification.
5. Demo issuer and trust policy generation.
6. Empty revocation list generation.
7. Signed assertion generation.
8. Main Silver verifier check.
9. Independent verification package export.
10. Copying both package and verifier to a temp directory outside the repo.
11. Running the independent verifier from the temp directory.
12. Validating the independent verifier’s Silver Verification Report.
13. Inline report checks.
14. Tampered-evidence failure test.
15. Tampered-manifest failure test.
16. Revoked-assertion failure test.

Expected final message:

```text
PASS: independent Silver verifier v0.1.0 regression fixture valid
```

---

## 8. What This Demo Proves

This demo proves that:

- a ProofRail Silver evidence package can be exported;
- an independent verifier can operate on the exported package;
- the verifier and package can run outside the original repo checkout;
- the independent verifier can validate the signed assertion;
- the independent verifier can validate the underlying Bronze evidence bundle;
- the independent verifier can detect tampered evidence;
- the independent verifier can detect tampered bundle manifests;
- the independent verifier can detect revoked assertions;
- the independent verifier emits a Silver Verification Report v0.1.0-compatible JSON report.

In short:

> ProofRail Silver verification can be separated from the environment that produced the evidence.

---

## 9. What This Demo Does Not Prove

This demo does not prove:

- production packaging;
- supply-chain security;
- trusted build provenance;
- PyPI distribution;
- Docker image distribution;
- third-party certification;
- public registry operation;
- regulator approval;
- Gold certification;
- production audit opinion;
- production deployment assurance.

The correct claim is:

> Silver Demo 002 demonstrates independent local verification of a prepared ProofRail Silver evidence package.

---

## 10. Why This Matters for v0.2.0

Silver v0.2.0 should define a relying-party verification profile.

A relying-party profile needs more than a signature. It needs clear obligations:

- what inputs must be supplied;
- which checks must be performed;
- how revocation is handled;
- how the report is generated;
- what failure means;
- whether verification can occur independently from the evidence producer.

v0.1.7 supplies the proof-of-concept for the independence requirement.

---

## 11. Summary

Silver Demo 002 moves ProofRail from an internal verification workflow to a portable verification package and independent verifier demonstration.

It is not Gold.

It is not production certification.

It is a tangible proof that Silver evidence can be exported and verified by a separate relying-party verifier.
