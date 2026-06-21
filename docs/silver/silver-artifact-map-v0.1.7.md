# ProofRail Silver Artifact Map v0.1.7

**Suggested repo path:** `docs/reference/silver-artifact-map-v0.1.7.md`  
**Status:** Reviewed draft reference note  
**Applies to:** ProofRail v0.1.7

---

## Purpose

ProofRail v0.1.7 contains several related but distinct artifacts. This map explains what each artifact does, where it appears in the evidence chain, and what it does not claim.

The main point:

> Bronze structures local control evidence. Silver makes that evidence signed, revocable, reportable, and independently verifiable.

---

## Artifact Table

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Bronze | Bronze Claim | v0.1.2 | Structured local evidence claim | `schemas/bronze-claim-schema-v0.1.2.md` |
| Bronze | Evidence Bundle Manifest | v0.1.3 | Portable package integrity | `schemas/bronze-evidence-bundle-manifest-v0.1.3.md` |
| Silver | Signed Bundle Assertion | v0.1.0 | Issuer signature over bundle manifest | `schemas/silver-signed-bundle-assertion-v0.1.0.md` |
| Silver | Revocation List | v0.1.0 | Local relying-party trust withdrawal | `schemas/silver-revocation-list-v0.1.0.md` |
| Silver | Verification Report | v0.1.0 | Structured verifier decision artifact | `schemas/silver-verification-report-v0.1.0.md` |
| Silver | Independent Verification Package | v0.1.0 | Portable verifier input package | `demos/silver-demo-002-independent-verifier/` |
| Silver | Independent Verifier | v0.1.0 | Relying-party verification outside source tree | `demos/silver-demo-002-independent-verifier/verifier/independent_verify.py` |

---

## Evidence Chain

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
```

---

## Artifact Descriptions

### Bronze Claim v0.1.2

The Bronze claim is the structured local evidence claim.

It records the protected actuator set, controls, evidence references, limitations, and evidence checksums.

It answers:

> What did this local deployment claim, and what evidence files support it?

It does not prove external reliance, issuer trust, or certification.

### Bronze Evidence Bundle Manifest v0.1.3

The bundle manifest checksums the full portable evidence package, including the Bronze claim itself.

It solves the claim self-reference problem: the claim cannot checksum itself, but an external manifest can checksum the claim.

It answers:

> Does this package still contain the same files that were bundled?

It is unsigned by itself.

### Silver Signed Bundle Assertion v0.1.0

The signed assertion records that a demo issuer signed the raw bytes of the Bronze v0.1.3 bundle manifest.

It answers:

> Did a trusted issuer sign this exact evidence bundle manifest?

It does not certify the deployment. It signs evidence, not a live system.

### Silver Revocation List v0.1.0

The revocation list lets a relying party reject an otherwise valid signed assertion.

It supports revocation by:

- assertion ID;
- issuer key;
- bundle manifest hash.

It answers:

> Has the relying party withdrawn trust from this assertion, key, or bundle?

It is local demo revocation, not production PKI revocation.

### Silver Verification Report v0.1.0

The verification report records the verifier’s decision, inputs, check results, revocation status, and underlying bundle status.

It answers:

> What did the verifier check, and what decision did it reach?

It is not signed in v0.1.0. It is not a Gold certification decision.

### Independent Verification Package v0.1.0

The independent package is an exported, portable set of files that can be verified outside the original source tree.

It answers:

> Can this Silver evidence package be moved and verified separately?

It is a demo package, not a production distribution format.

### Independent Verifier v0.1.0

The independent verifier runs outside the original repo checkout and performs the Silver checks without importing or invoking the main verifier.

It answers:

> Can a separate relying-party verifier reproduce the Silver verification result?

It is not production software distribution or third-party certification.

---

## Versioning Note

The repo version and artifact versions are intentionally different.

```text
Repo release: v0.1.7

Bronze Claim Schema: v0.1.2
Bronze Bundle Manifest: v0.1.3
Silver Signed Bundle Assertion: v0.1.0
Silver Revocation List: v0.1.0
Silver Verification Report: v0.1.0
Independent Silver Verifier Demo: v0.1.0
```

This avoids forcing every artifact schema to increment whenever the repository adds a new demo or capability.

---

## What Silver Means at v0.1.7

At v0.1.7, Silver means:

> signed, revocable, reportable, independently verifiable evidence-package reliance.

It does not mean:

- production certification;
- regulator approval;
- third-party audit;
- Gold governance;
- public PKI;
- public transparency infrastructure.

---

## v0.2.0 Update: Silver Relying-Party Profile

Silver v0.2.0 adds the Silver Relying-Party Profile — the formal acceptance criteria for a Silver evidence package.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Profile | v0.2.0 | Formal acceptance criteria for Silver evidence packages | `profiles/silver/SILVER_PROFILE_v0.2.0.md` |
| Silver | Profile Conformance Report | v0.2.0 | Structured conformance decision artifact | `schemas/silver-profile-conformance-report-v0.2.0.md` |

The profile defines two modes:

- `silver.base` — Validates a Silver verification report from any conformant verifier. Revocation not performed produces a conditional pass with warning.
- `silver.independent` — Validates a Silver verification report from an independent verifier, requiring a valid package manifest and mandatory revocation.

The profile validator (`tools/silver/validate_silver_profile_v0_2_0.py`) consumes a Silver Verification Report v0.1.0 and optionally a package manifest, producing a profile conformance report.

The extended evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → independent verification package
  → independent verifier
  → Silver profile conformance report
```

## v0.2.1 Update: Tightened Silver Profile

Silver v0.2.1 adds a third profile mode and tightens revocation requirements.

| Layer | Artifact | Version | Primary role | Main file/schema |
|---|---:|---:|---|---|
| Silver | Relying-Party Profile | v0.2.1 | Tightened acceptance criteria (revocation required for silver.base) | `profiles/silver/SILVER_PROFILE_v0.2.1.md` |
| Silver | Profile Conformance Report | v0.2.1 | Structured conformance decision artifact (three modes) | `schemas/silver-profile-conformance-report-v0.2.1.md` |
| Silver | Independent Verification Package Format | v0.2.1 | Package handoff format specification | `docs/silver/independent-verification-package-format-v0.2.1.md` |

The profile defines three modes:

- `silver.base` — Revocation required. No warning path.
- `silver.base.demo` — Preserves v0.2.0 `silver.base` semantics (revocation warning path).
- `silver.independent` — Unchanged from v0.2.0.

The v0.2.1 package exporter adds `package_format_version`, `profile_compatibility`, `inputs`, and `path_map` to the manifest. The independent verifier requires no changes.
