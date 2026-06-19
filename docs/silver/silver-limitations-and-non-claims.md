# ProofRail Silver v0.1.7 Limitations and Non-Claims

**Suggested repo path:** `docs/reference/silver-limitations-and-non-claims.md`  
**Status:** Reviewed reference note  
**Applies to:** ProofRail v0.1.7 and pre-v0.2.0 planning

---

## Purpose

This note defines what ProofRail Silver does and does not claim at the v0.1.7 stage.

Its purpose is to prevent overclaiming as the Silver machinery becomes more formal.

---

## Core Silver Claim

At v0.1.7, the defensible claim is:

> ProofRail demonstrates that a Bronze evidence package can be checksummed, bundled, signed, locally revoked, verified, reported, exported, and independently re-verified by a local relying-party verifier.

More compactly:

> Silver means signed, revocable, reportable, independently verifiable evidence-package reliance.

---

## What Silver v0.1.7 Does Claim

Silver v0.1.7 demonstrates the following:

1. A Bronze evidence bundle manifest can be signed.
2. The signature is over the raw bytes of the bundle manifest.
3. A verifier can check issuer trust using a local trust policy.
4. A verifier can check assertion expiry.
5. A verifier can check bundle-manifest integrity.
6. A verifier can check revocation by assertion ID, issuer key, or bundle hash.
7. A verifier can verify the underlying Bronze evidence bundle.
8. A verifier can emit a structured Silver Verification Report.
9. An independent verifier package can perform the same local verification outside the original source tree.

---

## What Silver Does Not Claim

Silver does **not** mean:

```text
certified safe
regulator-approved
production-grade PKI
third-party audited
publicly accredited
legally certified
Gold certified
production deployment assured
```

Silver does not certify that a live AI system is safe.

Silver does not certify that evidence files are truthful.

Silver does not certify that a deployment is correctly configured in production.

Silver does not certify that a party has legal authority to operate the system.

Silver verifies a package and records a relying-party verification decision.

---

## Specific Non-Claims

### No Production PKI

The demo uses Ed25519 keys and local trust policies.

It does not implement:

- certificate authorities;
- X.509;
- OCSP;
- public CRLs;
- hardware-backed keys;
- cloud KMS;
- enterprise key lifecycle management.

### No Public Revocation Infrastructure

The Silver Revocation List v0.1.0 demonstrates local relying-party revocation.

It does not implement:

- public revocation registries;
- transparency-log-backed revocation;
- regulator-backed revocation;
- signed revocation lists;
- distributed revocation propagation.

### No Third-Party Certification

A Silver verifier can be independent from the original source tree, but that does not make it a third-party certifier.

Silver does not claim:

- external audit;
- accredited assessment;
- legal certification;
- regulator acceptance.

### No Gold Governance

Gold will require governed certification decisions, authorized certifiers, defined review profiles, challenge paths, and revocation of certification decisions.

Silver stops earlier:

```text
Silver = relying-party verification
Gold = governed acceptance / certification decision
```

### No Production Deployment Assurance

The current demos use local evidence and test fixtures.

They do not prove:

- production configuration;
- production monitoring;
- production incident response;
- production control operation;
- complete enterprise control coverage.

---

## Correct Language to Use

Use:

```text
ProofRail v0.1.7 demonstrates a reproducible local evidence chain from Bronze control evidence to signed, revocable, independently verifiable Silver evidence packages.
```

Use:

```text
Silver v0.1.7 verification means the evidence package passed defined verifier checks under a local relying-party policy.
```

Avoid:

```text
ProofRail certifies the system is safe.
```

Avoid:

```text
The deployment is Gold certified.
```

Avoid:

```text
This is regulator-grade assurance.
```

Avoid:

```text
This proves production conformance.
```

---

## What v0.2.0 Should Clarify

Silver v0.2.0 should formalize:

- what inputs a relying-party verifier must receive;
- what checks it must perform;
- what failure modes must be recognized;
- what report must be produced;
- what revocation means;
- what independence means;
- what limitations must accompany any Silver acceptance.

The v0.2.0 profile should preserve this distinction:

> Silver is verifiable reliance on an evidence package, not certification of a live system.

---

## Summary

Silver v0.1.7 is significant because it makes ProofRail evidence portable, signed, revocable, reportable, and independently verifiable.

However, it remains a relying-party verification layer.

It is not certification.

It is not Gold.

It is the first implementation of the layer Gold can later rely on.
