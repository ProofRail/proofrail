# ProofRail Silver Verifier Output Attestation Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Derived from:** Silver Verification Report v0.1.0, Silver Profile Conformance Report v0.2.1
**Attestation family:** ProofRail Silver verifier output attestations

---

## 1. Purpose

The ProofRail Silver Verifier Output Attestation is a detached, signed statement binding a verifier's identity to its outputs: a Silver Verification Report and a Silver Profile Conformance Report.

It allows a relying party to verify that:

1. A specific verifier produced a specific verification report and conformance report.
2. The report files have not been modified since the attestation was signed.
3. The attestor key is trusted according to a local attestation trust policy.
4. The attested profile decision and metadata match the report contents.

This is a tamper-evidence and attribution mechanism. It is not certification.

---

## 2. Relationship to Existing Artifacts

The attestation sits at the end of the Silver evidence chain:

```text
Bronze claim
  → evidence checksums
  → evidence bundle manifest
  → signed Silver assertion
  → local revocation list
  → Silver verification report
  → Silver profile conformance report
  → verifier output attestation     ← this artifact
```

The attestation does not modify or replace any existing artifact. It signs verifier outputs, not evidence packages.

---

## 3. Attestor Key vs Issuer Key

The **issuer key** signs the Bronze bundle manifest (Silver Signed Bundle Assertion). The **attestor key** signs verifier outputs (this artifact). These are different roles with different keypairs. A single entity may hold both, but they must not share the same key.

---

## 4. Top-Level Structure

```json
{
  "attestation_version": "v0.1.0",
  "attestation_type": "proofrail.silver.verifier_output_attestation",
  "signed_payload": { ... },
  "signature": { ... }
}
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `attestation_version` | string | Yes | Must be `v0.1.0`. |
| `attestation_type` | string | Yes | Must be `proofrail.silver.verifier_output_attestation`. |
| `signed_payload` | object | Yes | The payload covered by the signature (see Section 5). |
| `signature` | object | Yes | Cryptographic signature metadata (see Section 6). |

---

## 5. Signed Payload Structure

```json
{
  "attestation_id": "string",
  "generated_at": "ISO-8601 UTC",
  "generated_by": "string",
  "attestor": { ... },
  "profile": { ... },
  "decision": { ... },
  "subjects": { ... },
  "limitations": [ ... ]
}
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `attestation_id` | string | Yes | Unique attestation identifier. |
| `generated_at` | string | Yes | ISO-8601 UTC timestamp of attestation generation. |
| `generated_by` | string | Yes | Tool that generated this attestation. |
| `attestor` | object | Yes | Attestor identity (see Section 5.1). |
| `profile` | object | Yes | Profile metadata copied from conformance report (see Section 5.2). |
| `decision` | object | Yes | Decision copied from conformance report (see Section 5.3). |
| `subjects` | object | Yes | References to attested files (see Section 5.4). |
| `limitations` | array | Yes | Non-empty list of limitation strings. |

### 5.1 Attestor

```json
{
  "attestor_id": "string",
  "attestor_role": "silver_verifier",
  "attestor_version": "string",
  "key_id": "string",
  "signature_algorithm": "ed25519"
}
```

| Field | Required | Meaning |
|-------|----------|---------|
| `attestor_id` | Yes | Must match the `verifier_id` in the verification report. |
| `attestor_role` | Yes | Must be `silver_verifier`. |
| `attestor_version` | Yes | Version of the attestor tool/process. |
| `key_id` | Yes | Unique identifier for the attestor signing key. |
| `signature_algorithm` | Yes | Must be `ed25519` for v0.1.0. |

### 5.2 Profile

```json
{
  "profile_id": "proofrail.silver.profile",
  "profile_version": "v0.2.1",
  "profile_mode": "silver.base | silver.base.demo | silver.independent"
}
```

Copied from the conformance report's `profile` block.

### 5.3 Decision

```json
{
  "status": "pass | fail",
  "reason": "string"
}
```

Copied from the conformance report's `decision` block. The signer does not require `status == "pass"` — attestation covers both pass and fail reports.

### 5.4 Subjects

```json
{
  "verification_report": {
    "path": "string",
    "sha256": "sha256:<64 hex>",
    "report_version": "v0.1.0",
    "report_type": "proofrail.silver.verification_report"
  },
  "profile_conformance_report": {
    "path": "string",
    "sha256": "sha256:<64 hex>",
    "conformance_report_version": "v0.2.1",
    "conformance_report_type": "proofrail.silver.profile_conformance_report"
  },
  "package_manifest": null | {
    "path": "string",
    "sha256": "sha256:<64 hex>",
    "package_type": "proofrail.silver.independent_verification_package",
    "package_format_version": "v0.2.1"
  }
}
```

`package_manifest` is present for `silver.independent` mode and `null` otherwise.

Subject paths must not contain `..` components.

---

## 6. Signature Structure

```json
{
  "algorithm": "ed25519",
  "key_id": "string",
  "signature_encoding": "base64",
  "signature": "<base64-encoded signature>"
}
```

| Field | Required | Meaning |
|-------|----------|---------|
| `algorithm` | Yes | Must equal `signed_payload.attestor.signature_algorithm`. |
| `key_id` | Yes | Must equal `signed_payload.attestor.key_id`. |
| `signature_encoding` | Yes | Must be `base64`. |
| `signature` | Yes | Base64-encoded Ed25519 signature over canonical signed payload bytes. |

### 6.1 Binding Constraint

The outer `signature.key_id` must equal `signed_payload.attestor.key_id`, and `signature.algorithm` must equal `signed_payload.attestor.signature_algorithm`. The verifier must reject the attestation if these do not match.

---

## 7. Canonical Signing Rule

The signature covers the canonical JSON serialization of the `signed_payload` object:

```python
json.dumps(signed_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

---

## 8. Attestation Trust Policy

```yaml
policy_type: proofrail.silver.verifier_attestation_trust_policy
policy_version: v0.1.0
trusted_attestors:
  - attestor_id: string
    key_id: string
    algorithm: ed25519
    public_key_path: string
    public_key_fingerprint_sha256: "sha256:<64 hex>"
limitations:
  - string
```

`public_key_path` is resolved relative to the trust policy file's parent directory.

---

## 9. Verification Semantics

A verifier should perform checks in the following order:

1. Parse attestation JSON, validate `attestation_version` and `attestation_type`.
2. Validate binding: `signature.key_id == signed_payload.attestor.key_id` and `signature.algorithm == signed_payload.attestor.signature_algorithm`.
3. Parse trust policy, validate `policy_type` and `policy_version`, find matching attestor.
4. Validate algorithm is `ed25519`.
5. Load public key from `public_key_path` (relative to trust policy parent directory).
6. Reconstruct canonical JSON bytes of `signed_payload`, verify Ed25519 signature.
7. Reject any subject path containing `..` components.
8. Recompute SHA-256 of all subject files, compare to attested hashes.
9. Cross-check verification report and conformance report metadata.
10. If `subjects.package_manifest` is not null, verify file exists and hash matches.
11. Confirm `limitations` is present and non-empty.

---

## 10. Failure Reason Codes

| Code | Meaning |
|------|---------|
| `invalid_attestation_structure` | Top-level structure invalid or binding mismatch |
| `invalid_trust_policy` | Trust policy type/version invalid |
| `attestor_not_trusted` | Attestor ID not in trust policy |
| `key_id_not_trusted` | Key ID not found for attestor |
| `unsupported_algorithm` | Not ed25519 |
| `signature_verification_failed` | Signature check failed |
| `subject_hash_mismatch` | File hash differs from attested hash |
| `subject_file_missing` | Attested file not found |
| `subject_path_traversal` | Subject path contains `..` component |
| `package_manifest_mismatch` | Package manifest metadata mismatch |
| `attestor_verifier_identity_mismatch` | attestor_id != verifier_id |
| `attested_metadata_mismatch` | Signed metadata differs from file content |
| `limitations_missing` | Limitations empty or absent |

### 10.1 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Verification passed. |
| 1 | Verification failed. |
| 2 | Usage or configuration error. |

---

## 11. Limitations

- Verifier output attestation is **not certification**. It records attribution and tamper evidence.
- Attestation is **not Gold certification**.
- The attestor key is **local demo PKI**, not production key management.
- Attestation does **not imply regulator approval**.
- Attestation does **not provide production deployment assurance**.
- The attestation signs verifier outputs, not the evidence package itself.

---

## 12. Example — `silver.base` Pass

```json
{
  "attestation_version": "v0.1.0",
  "attestation_type": "proofrail.silver.verifier_output_attestation",
  "signed_payload": {
    "attestation_id": "proofrail-demo-verifier-b-attestation-aabbccddeeff-silver-base",
    "generated_at": "2026-06-21T12:00:00+00:00",
    "generated_by": "tools/silver/sign_verifier_output_attestation_v0_1_0.py",
    "attestor": {
      "attestor_id": "proofrail-demo-verifier-b",
      "attestor_role": "silver_verifier",
      "attestor_version": "v0.2.2-demo",
      "key_id": "proofrail-demo-verifier-b-ed25519-attestation-001",
      "signature_algorithm": "ed25519"
    },
    "profile": {
      "profile_id": "proofrail.silver.profile",
      "profile_version": "v0.2.1",
      "profile_mode": "silver.base"
    },
    "decision": { "status": "pass", "reason": "profile_requirements_satisfied" },
    "subjects": {
      "verification_report": {
        "path": "verification-report.json",
        "sha256": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "report_version": "v0.1.0",
        "report_type": "proofrail.silver.verification_report"
      },
      "profile_conformance_report": {
        "path": "conformance-report.json",
        "sha256": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "conformance_report_version": "v0.2.1",
        "conformance_report_type": "proofrail.silver.profile_conformance_report"
      },
      "package_manifest": null
    },
    "limitations": [
      "Verifier output attestation is not certification.",
      "Not Gold certification.",
      "Not production PKI.",
      "Not regulator approval.",
      "Not production deployment assurance."
    ]
  },
  "signature": {
    "algorithm": "ed25519",
    "key_id": "proofrail-demo-verifier-b-ed25519-attestation-001",
    "signature_encoding": "base64",
    "signature": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  }
}
```

---

## 13. Change Log

### v0.1.0

- Initial release of the Silver Verifier Output Attestation schema.
- Ed25519 signatures over canonical JSON signed payloads.
- Binding constraint between outer signature and signed attestor identity.
- `..` path component rejection in subject paths.
- Support for `silver.base`, `silver.base.demo`, and `silver.independent` profile modes.
- `package_manifest` subject for `silver.independent` mode.

---

## 14. Recommended File Name

```text
schemas/silver-verifier-output-attestation-v0.1.0.md
```
