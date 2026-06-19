# Release Note — ProofRail v0.1.7 Independent Silver Verifier Demo

**Suggested repo path:** `docs/releases/2026-06-15-proofrail-v0.1.7.md`  
**Release date:** 2026-06-15  
**Repo milestone:** `v0.1.7`  
**Demo:** `silver-demo-002-independent-verifier`  
**Status:** Demo release / Silver relying-party separation milestone

---

## Summary

ProofRail v0.1.7 adds the **Independent Silver Verifier Demo**, also called **Silver Demo 002**.

This release demonstrates that a prepared ProofRail Silver evidence package can be exported from the main ProofRail demo environment and verified by an independent local verifier operating outside the original source tree.

The core claim is:

> ProofRail v0.1.7 demonstrates that a prepared ProofRail Silver evidence package can be verified by an independent local verifier package outside the original source tree, producing a schema-backed Silver Verification Report.

This is an important Silver milestone because relying-party verification should not be merely an internal repository workflow.

---

## What Changed

### Added Independent Verifier Demo

New demo directory:

```text
demos/silver-demo-002-independent-verifier/
```

This demo contains:

```text
demos/silver-demo-002-independent-verifier/README.md
demos/silver-demo-002-independent-verifier/verifier/independent_verify.py
demos/silver-demo-002-independent-verifier/verifier/README.md
demos/silver-demo-002-independent-verifier/package-template/README.md
```

The independent verifier performs the Silver verification checks without importing or invoking the main ProofRail Silver verifier or Bronze bundle verifier.

### Added Export Tool

New export tool:

```text
tools/silver/export_independent_verification_package_v0_1_0.py
```

The export tool creates a portable verification package under:

```text
demos/silver-demo-002-independent-verifier/runtime/package/
```

The runtime package is gitignored.

The exported package uses a `source-repo-subset/` layout that preserves the relative paths expected by the signed assertion and Bronze bundle manifest. This avoids rewriting the signed bundle manifest and preserves the Ed25519 signature over the original raw bundle-manifest bytes.

### Added Independent Verifier Regression Test

New regression test:

```text
tests/test_independent_silver_verifier_v0_1_0.sh
```

The regression test confirms:

- the package can be exported;
- both the verifier and the package can be copied to a temporary directory outside the repository;
- the verifier can run from that temporary directory;
- the independent verifier emits a Silver Verification Report v0.1.0-compatible JSON report;
- tampered evidence is detected;
- tampered bundle manifest is detected;
- revoked assertion is detected.

### Added Make Targets

New Make targets:

```bash
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
make verify-silver-all
```

Existing Demo 001 targets remain unchanged.

---

## Verification

Fresh-clone verification passed with:

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
make verify-silver-report-demo-001
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
```

Key expected pass messages include:

```text
PASS: all 10 evidence checksums verified
PASS: all 16 bundle files verified
PASS: Silver signed bundle assertion verified
PASS: Silver verification report v0.1.0 structurally valid
PASS: independent Silver verification succeeded
PASS: independent verifier detected tampered evidence
PASS: independent verifier detected tampered manifest
PASS: independent verifier detected revoked assertion
PASS: independent Silver verifier v0.1.0 regression fixture valid
```

---

## What This Release Demonstrates

ProofRail v0.1.7 demonstrates local relying-party separation.

The verification chain now looks like:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → revocation list
  → verification report
  → exported verification package
  → independent verifier
```

The important new property is:

> Verification can occur outside the original source checkout using a prepared package and a standalone verifier.

This supports the future Silver v0.2.0 profile by showing that relying-party verification can be made operationally separate from evidence production.

---

## What This Release Does Not Claim

This release does not provide:

- production verifier distribution;
- PyPI packaging;
- Docker image publishing;
- supply-chain security;
- trusted build provenance;
- third-party certification;
- public registry;
- regulator approval;
- Gold certification;
- production audit opinion;
- production deployment assurance.

The correct claim is narrower:

> ProofRail v0.1.7 demonstrates independent local verification of a prepared ProofRail Silver evidence package, not production-grade verifier distribution or certification.

---

## Files Added

```text
tools/silver/export_independent_verification_package_v0_1_0.py
demos/silver-demo-002-independent-verifier/README.md
demos/silver-demo-002-independent-verifier/verifier/independent_verify.py
demos/silver-demo-002-independent-verifier/verifier/README.md
demos/silver-demo-002-independent-verifier/package-template/README.md
tests/test_independent_silver_verifier_v0_1_0.sh
```

## Files Modified

```text
.gitignore
Makefile
tools/silver/README.md
CLAUDE.md
```

---

## Versioning Notes

This release does not introduce a new Silver schema.

It relies on existing Silver artifacts:

```text
Silver Signed Bundle Assertion v0.1.0
Silver Revocation List v0.1.0
Silver Verification Report v0.1.0
```

The new concept is:

```text
Independent Silver Verifier Demo v0.1.0
```

The repo release is:

```text
v0.1.7
```

---

## Suggested Next Step

The next major milestone should be **Silver v0.2.0**.

v0.1.4 through v0.1.7 built the machinery. v0.2.0 should formalize the relying-party verification profile:

- required inputs;
- required checks;
- acceptable outcomes;
- report requirements;
- revocation requirements;
- verifier independence expectations;
- limitations and non-claims.

In short:

> v0.2.0 should define what it means for a relying party to accept a ProofRail Silver evidence package.
