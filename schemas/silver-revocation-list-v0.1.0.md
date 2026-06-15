# ProofRail Silver Revocation List Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-14
**Status:** Draft / Demo-informed schema
**Related to:** Silver Signed Bundle Assertion v0.1.0
**Artifact family:** ProofRail Silver relying-party policy artifacts

---

## 1. Purpose

The ProofRail Silver Revocation List is a local relying-party policy artifact that allows a verifier to reject an otherwise valid Silver Signed Bundle Assertion.

Even when a signature is cryptographically valid and the issuer is trusted, a relying party may need to withdraw trust for a specific assertion, issuer key, or bundle. The revocation list makes trust withdrawable within the local verifier context.

This is **local demo revocation**, not production PKI revocation. It does not use OCSP, X.509 CRLs, transparency logs, or public certificate revocation infrastructure.

---

## 2. Relationship to Silver Signed Bundle Assertion v0.1.0

The Silver Signed Bundle Assertion proves that a trusted issuer signed a specific Bronze v0.1.3 evidence bundle manifest. The revocation list adds a post-signature rejection mechanism.

A verifier performs its standard checks (trust, algorithm, expiry, checksum, signature, underlying bundle) and additionally checks the revocation list if one is supplied. If any revocation entry matches, the assertion is rejected regardless of its cryptographic validity.

---

## 3. Relationship to Verifier Trust Policy

The trust policy establishes **who is trusted** — which issuers and keys a verifier accepts.

The revocation list **withdraws trust** for specific artifacts:

- A specific assertion instance (by assertion ID).
- A specific issuer key (by issuer ID + key ID).
- A specific bundle manifest (by SHA-256 hash).

Both artifacts are local relying-party policy. Neither implies public PKI or external certificate authority infrastructure.

---

## 4. Required Top-Level Fields

A v0.1.0 Silver Revocation List must include:

```yaml
revocation_list_version: "v0.1.0"
list_id: string
list_label: string
generated_at: ISO-8601 UTC timestamp
generated_by: string
revoked_assertions: list
revoked_issuer_keys: list
revoked_bundles: list
```

### 4.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `revocation_list_version` | Yes | Schema version. Must be `v0.1.0`. |
| `list_id` | Yes | Unique identifier for this revocation list instance. |
| `list_label` | Yes | Human-readable label. |
| `generated_at` | Yes | List generation timestamp in ISO-8601 UTC format. |
| `generated_by` | Yes | Tool or process that generated this list. |
| `revoked_assertions` | Yes | List of revoked assertion entries (may be empty). |
| `revoked_issuer_keys` | Yes | List of revoked issuer key entries (may be empty). |
| `revoked_bundles` | Yes | List of revoked bundle entries (may be empty). |

---

## 5. `revoked_assertions` Structure

Each entry revokes a specific assertion by its assertion ID.

```yaml
revoked_assertions:
  - assertion_id: string
    reason: string
    revoked_at: ISO-8601 UTC timestamp
```

### 5.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `assertion_id` | Yes | The assertion ID to revoke. Matched against `assertion.assertion_id`. |
| `reason` | Yes | Human-readable revocation reason. |
| `revoked_at` | Yes | Timestamp when the revocation was recorded. |

---

## 6. `revoked_issuer_keys` Structure

Each entry revokes a specific issuer key pair.

```yaml
revoked_issuer_keys:
  - issuer_id: string
    key_id: string
    reason: string
    revoked_at: ISO-8601 UTC timestamp
```

### 6.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `issuer_id` | Yes | The issuer ID. Matched against `assertion.issuer.issuer_id`. |
| `key_id` | Yes | The key ID. Matched against `assertion.issuer.key_id`. |
| `reason` | Yes | Human-readable revocation reason. |
| `revoked_at` | Yes | Timestamp when the revocation was recorded. |

### 6.2 Matching rule

Both `issuer_id` **and** `key_id` must match for the revocation to apply. Revoking an issuer key does not revoke other keys from the same issuer.

---

## 7. `revoked_bundles` Structure

Each entry revokes a specific bundle manifest by its SHA-256 hash.

```yaml
revoked_bundles:
  - bundle_manifest_sha256: "sha256:<64 hex chars>"
    reason: string
    revoked_at: ISO-8601 UTC timestamp
```

### 7.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `bundle_manifest_sha256` | Yes | The bundle manifest SHA-256 hash. Matched against `assertion.subject.bundle_manifest_sha256`. |
| `reason` | Yes | Human-readable revocation reason. |
| `revoked_at` | Yes | Timestamp when the revocation was recorded. |

---

## 8. Revocation Matching Semantics

All matching is **exact string comparison**.

The verifier checks three lists in order:

1. **Assertion revocation:** If `assertion.assertion_id` equals any `revoked_assertions[].assertion_id`, the assertion is revoked.
2. **Issuer key revocation:** If `assertion.issuer.issuer_id` and `assertion.issuer.key_id` both match any entry in `revoked_issuer_keys`, the assertion is revoked.
3. **Bundle revocation:** If `assertion.subject.bundle_manifest_sha256` equals any `revoked_bundles[].bundle_manifest_sha256`, the assertion is revoked.

If any match is found, the verifier rejects the assertion with a specific failure message.

---

## 9. Verification Semantics

The revocation check integrates into the Silver verifier's existing check sequence:

1. Trust check
2. Algorithm check
3. Expiry check
4. Bundle manifest checksum check
5. **Revocation check** (if revocation list supplied)
6. Signature check
7. Underlying bundle verification

The revocation check is placed after the checksum check (which provides the bundle hash needed for bundle revocation matching) and before the more expensive signature verification and underlying bundle checks.

### 9.1 Failure messages

| Revocation type | Message |
|-----------------|---------|
| Assertion ID revoked | `FAIL: assertion revoked` |
| Issuer key revoked | `FAIL: issuer key revoked` |
| Bundle hash revoked | `FAIL: bundle revoked` |

### 9.2 Optional check

If no `--revocation-list` flag is supplied to the verifier, the revocation check is skipped and existing behavior is unchanged.

---

## 10. Limitations

- This is **local demo revocation**. It demonstrates the concept of trust withdrawal within a local verifier context.
- It is **not production PKI revocation**. It does not use certificate authorities, OCSP responders, or X.509 CRL distribution points.
- It is **not public certificate revocation**. The revocation list is a local file, not a publicly distributed artifact.
- It is **not transparency-log-backed**. There is no append-only log or public verifiability of revocation events.
- It is **not regulator-backed**. No regulatory authority or external auditor is involved.
- The revocation list is **not signed**. A future version could sign the revocation list itself.
- The revocation list is **not distributed**. It is a local file managed by the relying-party verifier.

---

## 11. Non-Goals

The following are explicitly out of scope for v0.1.0:

- Gold certifier role or Gold profile.
- Public PKI revocation (OCSP, X.509 CRLs).
- Transparency logs or public append-only revocation records.
- Regulator or external auditor workflows.
- Multi-party quorum for revocation decisions.
- Cloud KMS or hardware attestation.
- DID/VC revocation registries.
- Automated revocation propagation.
- Signed revocation lists.

---

## 12. Example Empty List

```yaml
revocation_list_version: "v0.1.0"
list_id: "proofrail-silver-demo-001-verifier-b-revocation-list"
list_label: "ProofRail Minimal Silver Demo 001 Verifier B Revocation List"
generated_at: "2026-06-14T00:00:00Z"
generated_by: "tools/silver/generate_demo_revocation_list_v0_1_0.py"
revoked_assertions: []
revoked_issuer_keys: []
revoked_bundles: []
```

---

## 13. Example Populated List

```yaml
revocation_list_version: "v0.1.0"
list_id: "proofrail-silver-demo-001-verifier-b-revocation-list"
list_label: "ProofRail Minimal Silver Demo 001 Verifier B Revocation List"
generated_at: "2026-06-14T12:00:00Z"
generated_by: "tools/silver/generate_demo_revocation_list_v0_1_0.py"

revoked_assertions:
  - assertion_id: "proofrail-silver-demo-001"
    reason: "demo assertion revocation"
    revoked_at: "2026-06-14T12:00:00Z"

revoked_issuer_keys:
  - issuer_id: "proofrail-demo-issuer-a"
    key_id: "proofrail-demo-issuer-a-ed25519-001"
    reason: "demo key revocation"
    revoked_at: "2026-06-14T12:00:00Z"

revoked_bundles:
  - bundle_manifest_sha256: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    reason: "demo bundle revocation"
    revoked_at: "2026-06-14T12:00:00Z"
```

---

## 14. Change Log

### v0.1.0

- Initial release of the Silver Revocation List schema.
- Three revocation targets: assertion ID, issuer key, bundle manifest hash.
- Local relying-party policy artifact — not production PKI, not public certificate revocation, not OCSP, not transparency-log-backed.
- Optional integration with Silver verifier via `--revocation-list` flag.
- Exact string matching for all revocation entries.

---

## 15. Recommended File Name

```text
schemas/silver-revocation-list-v0.1.0.md
```
