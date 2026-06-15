# ProofRail Minimal Silver Demo 001 — Signed Evidence Bundle Walkthrough

**Suggested repo path:** `docs/walkthroughs/minimal-silver-demo-001-signed-bundle-walkthrough.md`  
**Demo:** `silver-demo-001`  
**Repo milestone:** `v0.1.4`  
**Silver artifact schema:** `silver-signed-bundle-assertion-v0.1.0`  
**Date:** 2026-06-14  
**Status:** Demo-informed walkthrough

---

## 1. Purpose

Minimal Silver Demo 001 demonstrates that a ProofRail Bronze v0.1.3 evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy, while preserving the underlying Bronze evidence-integrity checks.

This is the first minimal Silver step in the ProofRail progression:

1. **Bronze v0.1.2** — generate a structured Bronze claim with evidence checksums.
2. **Bronze v0.1.3** — generate an unsigned evidence bundle manifest that checksums the whole portable package, including the claim file.
3. **Silver Signed Bundle Assertion v0.1.0** — sign the Bronze v0.1.3 bundle manifest and verify it against a local trust policy.

The demo is intentionally narrow. It does not implement revocation, public transparency logs, third-party certification, production PKI, DID/VC, OIDC, or regulator-grade governance.

---

## 2. Why Silver Starts Here

Bronze answers a local conformance question:

> Did this deployment produce structured evidence that the protected actuator set was declared, mediated, tested for bypass prevention, subjected to stop-control and rate-limit/circuit-breaker checks, and supported by normalized audit/performance evidence?

Bronze v0.1.2 added evidence checksums so that the evidence files referenced by the claim can be integrity-checked after generation.

Bronze v0.1.3 added a bundle manifest so that the whole portable evidence package can be described and checked externally. This solved the self-reference problem: the claim cannot include its own checksum, but a separate bundle manifest can checksum the claim.

Minimal Silver adds one more property:

> A relying party can verify that a trusted issuer signed the exact Bronze evidence bundle manifest being inspected.

That is the smallest meaningful Silver jump. It moves from local evidence integrity to signed relying-party verification.

---

## 3. What the Demo Builds On

### 3.1 Bronze v0.1.2 Claim

The Bronze v0.1.2 claim file is:

```text
demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml
```

It contains:

- Bronze claim metadata
- protected actuator set reference
- control results
- evidence file references
- `evidence_checksums`
- limitations and validation metadata

The checksum verifier recomputes SHA-256 digests over the raw bytes of the listed evidence files.

Relevant commands:

```bash
make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence
```

### 3.2 Bronze v0.1.3 Evidence Bundle Manifest

The Bronze v0.1.3 bundle manifest is:

```text
demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml
```

It checksums the portable package, including:

- the Bronze claim file
- evidence files
- schema files
- tooling scripts
- selected documentation

Relevant commands:

```bash
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle
```

The bundle manifest is local and unsigned. It is not a Silver assertion by itself. It is the object that Minimal Silver signs.

---

## 4. Minimal Silver Demo 001

Minimal Silver Demo 001 introduces:

```text
demos/silver-demo-001/
```

Key files:

```text
demos/silver-demo-001/README.md
demos/silver-demo-001/silver-input-v0.1.0.yaml
schemas/silver-signed-bundle-assertion-v0.1.0.md
tools/silver/generate_demo_issuer_v0_1_0.py
tools/silver/sign_bundle_manifest_v0_1_0.py
tools/silver/verify_signed_bundle_assertion_v0_1_0.py
tests/test_silver_signed_bundle_assertion_v0_1_0.sh
```

Runtime outputs are generated under:

```text
demos/silver-demo-001/runtime/
```

This directory is intentionally ignored by Git. It contains demo keys, the generated trust policy, the signed assertion, and the verification report.

Expected runtime outputs:

```text
demos/silver-demo-001/runtime/issuer-a/private-key.pem
demos/silver-demo-001/runtime/issuer-a/public-key.pem
demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml
demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml
demos/silver-demo-001/runtime/verification-report.json
```

These files are reproducible demo artifacts, not source-controlled evidence.

---

## 5. What Is Signed

The Silver assertion signs the **raw bytes** of the Bronze v0.1.3 evidence bundle manifest:

```text
demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml
```

The signature is not over a YAML-normalized representation. It is not over a parsed data structure. It is over the exact byte sequence of the bundle manifest file.

This avoids ambiguity around YAML serialization, whitespace, line endings, ordering, and canonicalization.

The signed assertion records:

```yaml
subject:
  bundle_manifest: "../composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml"
  bundle_manifest_type: "proofrail.bronze.evidence_bundle"
  bundle_manifest_sha256: "sha256:<64 hex chars>"
  signed_payload: "raw_bundle_manifest_bytes"
```

The assertion does not include its own checksum. A later outer package could checksum or sign the assertion itself.

---

## 6. Issuer and Trust Policy

The demo issuer generator creates an Ed25519 keypair and a local relying-party trust policy.

Issuer keypair:

```text
demos/silver-demo-001/runtime/issuer-a/private-key.pem
demos/silver-demo-001/runtime/issuer-a/public-key.pem
```

Trust policy:

```text
demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml
```

The trust policy contains a trusted issuer entry with:

- `issuer_id`
- `issuer_label`
- `key_id`
- `algorithm`
- `public_key_pem`
- `public_key_fingerprint_sha256`

The verifier accepts only assertions whose issuer and key ID match an entry in this local trust policy.

This is not production PKI. It is a local demonstration of relying-party trust binding.

---

## 7. Verification Chain

The full Minimal Silver verification chain is:

```text
Bronze claim generation
  ↓
Bronze evidence checksum verification
  ↓
Bronze evidence bundle manifest generation
  ↓
Bronze evidence bundle manifest verification
  ↓
Demo issuer key generation
  ↓
Bundle manifest signing
  ↓
Silver signed assertion verification
  ↓
Underlying bundle integrity verification
```

The verifier checks:

1. assertion YAML is readable;
2. trust policy is readable;
3. issuer is trusted;
4. key ID is trusted;
5. algorithm is Ed25519;
6. assertion is not expired;
7. bundle manifest path resolves;
8. bundle manifest raw-byte SHA-256 matches the assertion;
9. Ed25519 signature verifies against the raw bundle manifest bytes;
10. underlying Bronze v0.1.3 bundle manifest verification passes.

The expected successful output is:

```text
PASS: Silver signed bundle assertion verified
```

---

## 8. How to Run

From a fresh clone with dependencies installed:

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

The end-to-end Silver target is:

```bash
make silver-demo-001
```

The full Silver regression target is:

```bash
make verify-silver-demo-001
```

---

## 9. Regression Tests

The Silver regression test is:

```text
tests/test_silver_signed_bundle_assertion_v0_1_0.sh
```

It performs:

1. Bronze v0.1.2 claim generation.
2. Bronze v0.1.2 evidence checksum verification.
3. Bronze v0.1.3 bundle manifest generation.
4. Bronze v0.1.3 bundle manifest verification.
5. Demo issuer keypair and trust policy generation.
6. Bronze v0.1.3 bundle manifest signing.
7. Signed Silver assertion verification.
8. Inline assertion structure checks.
9. Tampered-manifest failure test.
10. Tampered-evidence failure test.
11. Untrusted-issuer failure test.
12. Expired-assertion failure test.

Expected successful regression conclusion:

```text
=== All Silver v0.1.0 regression tests passed ===
```

The negative tests deliberately trigger verification failures. Those failures are expected and are treated as passes when the verifier rejects the corrupted or untrusted artifact for the intended reason.

---

## 10. Failure Modes Demonstrated

### 10.1 Tampered Manifest

If the signed bundle manifest itself is modified, the verifier should fail with a bundle-manifest checksum mismatch or signature verification failure.

This demonstrates that the signature binds to the exact raw bytes of the bundle manifest.

### 10.2 Tampered Evidence

If an evidence file listed by the bundle manifest is modified, the signature over the manifest may still verify, but the underlying Bronze v0.1.3 bundle verification must fail.

This demonstrates that Silver verification does not replace Bronze evidence integrity checks. It composes with them.

### 10.3 Untrusted Issuer

If the trust policy does not trust the issuer or key ID in the assertion, the verifier rejects the assertion.

This demonstrates that Silver requires a relying-party trust decision, not merely a mathematically valid signature.

### 10.4 Expired Assertion

If the assertion is past its `expires_at` timestamp, the verifier rejects it.

This demonstrates that a signed assertion is time-bounded.

---

## 11. What This Proves

Minimal Silver Demo 001 proves that:

- a Bronze v0.1.3 evidence bundle manifest can be signed;
- the signature is over raw bundle manifest bytes;
- a relying-party verifier can check issuer trust using a local trust policy;
- the verifier can reject tampered manifests;
- the verifier can reject tampered underlying evidence through bundle verification;
- the verifier can reject untrusted issuers;
- the verifier can reject expired assertions;
- Bronze integrity checks and Silver signature checks compose cleanly.

In short:

> ProofRail can now demonstrate a path from local actuation-control evidence to a portable evidence bundle to signed relying-party verification.

---

## 12. What This Does Not Prove

This demo does not prove:

- production-grade PKI;
- third-party certification;
- public regulator approval;
- revocation;
- transparency logging;
- issuer accreditation;
- enterprise identity federation;
- hardware-backed signing;
- cloud key management;
- live runtime monitoring;
- production conformance;
- full Silver governance.

The correct claim is narrower:

> Minimal Silver Demo 001 demonstrates that a ProofRail Bronze v0.1.3 evidence bundle manifest can be signed by a demo issuer and verified by a relying-party verifier using a local trust policy.

---

## 13. Why This Is the Smallest Useful Silver Step

A signature alone is not enough. A checksum alone is not enough. A claim alone is not enough.

Minimal Silver requires all of these pieces to compose:

```text
Claim → Evidence checksums → Bundle manifest → Signature → Trust policy → Verification result
```

The v0.1.4 demo therefore avoids overbuilding while adding one new key governance property: external relying-party verification.

This is the bridge from Bronze evidence hygiene to later Silver features such as revocation, issuer registries, transparency logs, delegated authority, and third-party assessment.

---

## 14. Suggested Next Steps

Possible next iterations:

1. **Silver v0.1.1 / repo v0.1.5 — Revocation list**
   - Add a local revocation list.
   - Reject revoked assertion IDs or bundle IDs.

2. **Silver v0.1.2 — Signed verification report**
   - Produce and optionally sign the verifier’s report.

3. **Silver v0.1.3 — Issuer profile**
   - Separate issuer metadata from the trust policy.
   - Add issuer scope and authority limits.

4. **Silver v0.2.0 — Relying-party profile**
   - Define what a verifier must check before accepting a Silver assertion.

5. **Demo 002 — Independent verifier package**
   - Separate the verifier into an independent directory or package to demonstrate third-party verification without source-tree coupling.

---

## 15. Summary

Minimal Silver Demo 001 is a documentation and verification milestone in the ProofRail progression.

Bronze v0.1.2 made evidence files checksum-verifiable.

Bronze v0.1.3 made the whole evidence package manifest-verifiable.

ProofRail v0.1.4 / Silver Signed Bundle Assertion v0.1.0 makes that bundle **signed and relying-party-verifiable**.

This is still a demo, but it is no longer merely a local evidence loop. It is the first complete ProofRail path from controlled agentic execution evidence to a signed artifact another party can verify.
