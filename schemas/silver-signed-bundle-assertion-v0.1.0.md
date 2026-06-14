# ProofRail Silver Signed Bundle Assertion Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-14
**Status:** Draft / Demo-informed schema
**Derived from:** Bronze Evidence Bundle Manifest v0.1.3
**Assertion family:** ProofRail Silver signed evidence assertions

---

## 1. Purpose

The ProofRail Silver Signed Bundle Assertion is a signed statement over a Bronze v0.1.3 evidence bundle manifest. It allows a relying party to verify that:

1. A Bronze claim exists and is structurally valid.
2. The Bronze evidence checksums are intact.
3. The Bronze evidence bundle manifest checksums the entire portable package.
4. A known issuer signed the exact bundle manifest being inspected.
5. The issuer key is trusted according to a local trust policy.

This is **Minimal Silver** — the smallest useful Silver step. It demonstrates signed evidence portability without implementing full Silver governance.

---

## 2. Relationship to Bronze Claim Schema v0.1.2

Bronze Claim Schema v0.1.2 defines the structured claim YAML with evidence checksums. The claim is the innermost evidence artifact.

The Silver assertion does not modify or replace the Bronze claim. It signs the bundle manifest that contains the claim's checksum.

---

## 3. Relationship to Bronze Evidence Bundle Manifest v0.1.3

Bronze Evidence Bundle Manifest v0.1.3 checksums the entire portable evidence package — claim file, evidence files, schemas, tooling, and documentation. It is unsigned.

The Silver assertion signs the bundle manifest's raw bytes, providing cryptographic assurance that the manifest has not been modified since signing.

### 3.1 Verification chain

```
Silver Signed Assertion
  └── signs → Bronze Bundle Manifest v0.1.3
                └── checksums → Bronze Claim v0.1.2
                └── checksums → Evidence files
                └── checksums → Schemas, tooling, documentation
```

---

## 4. What Is Signed

The signature covers the **raw bytes of the bundle manifest file**.

The signed assertion records:

- The relative path to the bundle manifest.
- The SHA-256 checksum of the bundle manifest raw bytes.
- The Ed25519 signature over those raw bytes.

---

## 5. Why Raw Bytes

The signature is over raw file bytes, not YAML-normalized or canonicalized content. This avoids canonicalization ambiguity and matches the v0.1.2/v0.1.3 pattern of raw-byte checksums.

A verifier reads the manifest file, computes SHA-256 over the exact bytes, and verifies the signature over those same bytes. Any byte-level change invalidates both the checksum and the signature.

---

## 6. Required Top-Level Fields

A v0.1.0 Silver Signed Bundle Assertion must include:

```yaml
assertion_version: "v0.1.0"
assertion_type: "proofrail.silver.signed_bundle_assertion"
assertion_id: string
assertion_label: string
issuer: mapping
subject: mapping
validity: mapping
signature: mapping
generated_by: string
```

### 6.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `assertion_version` | Yes | Schema version. Must be `v0.1.0`. |
| `assertion_type` | Yes | Must be `proofrail.silver.signed_bundle_assertion`. |
| `assertion_id` | Yes | Unique identifier for this assertion instance. |
| `assertion_label` | Yes | Human-readable assertion label. |
| `issuer` | Yes | Issuer identity and key metadata (see Section 7). |
| `subject` | Yes | Bundle manifest reference and checksum (see Section 8). |
| `validity` | Yes | Temporal validity window (see Section 9). |
| `signature` | Yes | Cryptographic signature metadata (see Section 10). |
| `generated_by` | Yes | Tool or process that generated this assertion. |

---

## 7. Issuer Structure

```yaml
issuer:
  issuer_id: string
  issuer_label: string
  key_id: string
  algorithm: "ed25519"
```

### 7.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `issuer_id` | Yes | Unique identifier for the issuing entity. |
| `issuer_label` | Yes | Human-readable issuer label. |
| `key_id` | Yes | Unique identifier for the signing key. |
| `algorithm` | Yes | Signing algorithm. Must be `ed25519` for v0.1.0. |

---

## 8. Subject Structure

```yaml
subject:
  bundle_manifest: string
  bundle_manifest_type: "proofrail.bronze.evidence_bundle"
  bundle_manifest_sha256: "sha256:<64 hex chars>"
  signed_payload: "raw_bundle_manifest_bytes"
```

### 8.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `bundle_manifest` | Yes | Relative path to the bundle manifest file. |
| `bundle_manifest_type` | Yes | Must be `proofrail.bronze.evidence_bundle`. |
| `bundle_manifest_sha256` | Yes | SHA-256 of the bundle manifest raw bytes, in `sha256:<64 hex>` format. |
| `signed_payload` | Yes | Describes what was signed. Must be `raw_bundle_manifest_bytes`. |

### 8.2 Path semantics

The `bundle_manifest` path is relative to the Silver demo root directory. It may use `../` to reference files in sibling directories.

---

## 9. Validity Structure

```yaml
validity:
  issued_at: "ISO-8601 UTC timestamp"
  expires_at: "ISO-8601 UTC timestamp"
```

### 9.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `issued_at` | Yes | Timestamp when the assertion was issued. UTC, ISO-8601 format. |
| `expires_at` | Yes | Timestamp when the assertion expires. UTC, ISO-8601 format. |

### 9.2 Expiry semantics

A verifier must reject an assertion if the current time is before `issued_at` or after `expires_at`. All timestamps are interpreted as UTC.

---

## 10. Signature Structure

```yaml
signature:
  algorithm: "ed25519"
  signature_encoding: "base64"
  signature_value: "<base64-encoded signature>"
  public_key_fingerprint_sha256: "sha256:<64 hex chars>"
```

### 10.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `algorithm` | Yes | Must be `ed25519`. |
| `signature_encoding` | Yes | Must be `base64`. |
| `signature_value` | Yes | Base64-encoded Ed25519 signature over the bundle manifest raw bytes. |
| `public_key_fingerprint_sha256` | Yes | SHA-256 of the raw 32-byte Ed25519 public key, in `sha256:<64 hex>` format. |

### 10.2 Fingerprint computation

The public key fingerprint is computed as:

```python
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)  # 32 bytes
fingerprint = "sha256:" + hashlib.sha256(raw).hexdigest()
```

---

## 11. Trust Policy Structure

A verifier uses a local trust policy to determine which issuers and keys are trusted.

```yaml
trust_policy_version: "v0.1.0"
policy_id: string
policy_label: string
trusted_issuers:
  - issuer_id: string
    issuer_label: string
    key_id: string
    algorithm: "ed25519"
    public_key_pem: |
      -----BEGIN PUBLIC KEY-----
      ...
      -----END PUBLIC KEY-----
    public_key_fingerprint_sha256: "sha256:<64 hex chars>"
```

### 11.1 Trust matching

A verifier must find an entry in `trusted_issuers` where both `issuer_id` and `key_id` match the assertion's issuer. If no match is found, the assertion is rejected.

### 11.2 Public key source

The verifier loads the public key PEM from the matched trust policy entry. The trust policy is the single source of trusted public keys in Minimal Silver.

---

## 12. Verification Semantics

A verifier should perform checks in the following order:

1. **Trust check:** Confirm `issuer_id` and `key_id` are trusted.
2. **Algorithm check:** Confirm signature algorithm is `ed25519`.
3. **Expiry check:** Confirm current time is within `[issued_at, expires_at]`.
4. **Checksum check:** Recompute SHA-256 of bundle manifest raw bytes, compare to `bundle_manifest_sha256`.
5. **Signature check:** Verify Ed25519 signature over bundle manifest raw bytes using the trusted public key.
6. **Bundle check:** Verify the underlying v0.1.3 bundle manifest (all file checksums and sizes).

All six checks must pass for the assertion to be considered verified.

---

## 13. Failure Semantics

Each failure mode has a distinct message:

| Failure | Message |
|---------|---------|
| Issuer not in trust policy | `FAIL: issuer not trusted` |
| Key ID not in trust policy | `FAIL: key_id not trusted` |
| Assertion expired or not yet valid | `FAIL: assertion expired` |
| Bundle manifest checksum mismatch | `FAIL: bundle manifest checksum mismatch` |
| Ed25519 signature invalid | `FAIL: signature verification failed` |
| Underlying bundle integrity failure | `FAIL: underlying bundle verification failed` |

### 13.1 Exit codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed. |
| 1 | Verification failed. |
| 2 | Usage or configuration error. |

---

## 14. Limitations

- This is **Minimal Silver**, not full Silver governance.
- The assertion is **local only**. It does not imply federation, cross-organization trust, or ecosystem-wide trust propagation.
- The assertion is **not a certification**. It does not prove production deployment conformance.
- The assertion **does not provide revocation**. A compromised key cannot be revoked through the assertion mechanism.
- The assertion **signs the manifest, not the live system**. It proves the manifest was signed by a trusted issuer, not that the deployment is correctly configured.
- The trust policy is **local and manually managed**. There is no automated trust distribution.

---

## 15. Non-Goals

The following are explicitly out of scope for v0.1.0:

- Revocation lists or certificate revocation.
- Public transparency logs.
- Regulator or auditor roles.
- Third-party certification.
- DID/VC integration.
- OAuth/OIDC integration.
- PKI hierarchy or certificate chains.
- Cloud key management (KMS).
- Hardware attestation (TPM/HSM).
- Enterprise identity federation.
- Production-grade key management.

---

## 16. Example

Minimal valid v0.1.0 Silver Signed Bundle Assertion:

```yaml
assertion_version: "v0.1.0"
assertion_type: "proofrail.silver.signed_bundle_assertion"
assertion_id: "proofrail-silver-demo-001"
assertion_label: "ProofRail Minimal Silver Demo 001 — signed Bronze v0.1.3 bundle manifest"

issuer:
  issuer_id: "proofrail-demo-issuer-a"
  issuer_label: "ProofRail Demo Issuer A"
  key_id: "proofrail-demo-issuer-a-ed25519-001"
  algorithm: "ed25519"

subject:
  bundle_manifest: "../composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml"
  bundle_manifest_type: "proofrail.bronze.evidence_bundle"
  bundle_manifest_sha256: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  signed_payload: "raw_bundle_manifest_bytes"

validity:
  issued_at: "2026-06-14T00:00:00Z"
  expires_at: "2026-09-12T00:00:00Z"

signature:
  algorithm: "ed25519"
  signature_encoding: "base64"
  signature_value: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  public_key_fingerprint_sha256: "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

generated_by: "tools/silver/sign_bundle_manifest_v0_1_0.py"
```

---

## 17. Change Log

### v0.1.0

- Initial release of the Silver Signed Bundle Assertion schema.
- Ed25519 signatures over Bronze v0.1.3 evidence bundle manifest raw bytes.
- Local trust policy for issuer/key verification.
- Validity window with `issued_at` and `expires_at`.
- Verification chain: Silver assertion → bundle manifest → claim + evidence.
- Minimal Silver — no revocation, no federation, no certification.

---

## 18. Recommended File Name

```text
schemas/silver-signed-bundle-assertion-v0.1.0.md
```
