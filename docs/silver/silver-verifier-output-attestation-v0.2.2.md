# Silver Verifier Output Attestation — v0.2.2

**Version:** v0.2.2
**Date:** 2026-06-21
**Status:** Draft relying-party explainer

---

## What v0.2.2 Adds

ProofRail v0.2.2 adds **detached, signed attestations over verifier outputs**.

A verifier can now issue a tamper-evident, attributable record that binds together its verification report, profile conformance report, and (for `silver.independent`) the package manifest.

Core claim:

> "This verifier produced this report from these inputs under this profile."

No new profile version is introduced. Profile semantics from v0.2.1 are unchanged.

---

## What an Attestation Says

An attestation says:

1. A specific attestor identity (which must match the verifier identity in the verification report) produced a specific set of outputs.
2. The outputs have not been modified since the attestation was signed.
3. The attestor key is trusted according to a local attestation trust policy.
4. The attested profile mode and decision match the conformance report contents.

---

## What an Attestation Does Not Say

An attestation does **not** say:

- The verifier decision is correct.
- The evidence files are truthful.
- The deployment is correctly configured.
- The system is safe or certified.
- Any regulator or third party has reviewed or approved the result.
- The attestation constitutes Gold certification.

Attestation is attribution and tamper evidence, not judgment of the underlying evidence.

---

## Covered Files

An attestation covers:

| Subject | When |
|---------|------|
| Verification report | Always |
| Profile conformance report | Always |
| Package manifest | `silver.independent` mode only |

Each subject is referenced by path and SHA-256. The verifier recomputes hashes at verification time.

Subject paths must not contain `..` components. Both the signer and verifier reject such paths.

---

## Signature Computation

The signature covers the canonical JSON serialization of the `signed_payload` object:

```python
json.dumps(signed_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

The signature algorithm is Ed25519. The attestor key is separate from the issuer key used for Silver Signed Bundle Assertions.

---

## Verification Steps

1. Parse attestation JSON, validate version and type.
2. Validate binding: outer `signature.key_id` matches `signed_payload.attestor.key_id`; outer `signature.algorithm` matches `signed_payload.attestor.signature_algorithm`.
3. Parse attestation trust policy, find trusted attestor entry.
4. Load public key from `public_key_path` (relative to trust policy file).
5. Reconstruct canonical JSON bytes, verify Ed25519 signature.
6. Reject subject paths containing `..` components.
7. Recompute SHA-256 of all subject files, compare to attested hashes.
8. Cross-check verification report metadata (verifier identity, report version/type).
9. Cross-check conformance report metadata (profile, decision, version/type).
10. Soft-check: conformance report's `input.verification_report` path against attested `subjects.verification_report.path` (warn on mismatch).
11. If `silver.independent`: verify package manifest exists, hash matches, metadata correct.
12. Confirm limitations present and non-empty.

---

## Relationship to v0.2.1 Profile

The attestation capability is built on the v0.2.1 profile. It does not define a new profile version or change profile semantics.

The attestation references the v0.2.1 conformance report and copies its `profile` and `decision` blocks into the signed payload.

---

## Relationship to Gold

Gold will introduce governed certification decisions, authorized certifiers, review profiles, challenge paths, and certification revocation.

Verifier output attestation is a Silver-layer attribution mechanism. It provides the tamper-evident output identity that Gold can later rely on, but it is not itself a Gold artifact.

---

## Limitations

- Verifier output attestation is not certification.
- Not Gold certification.
- Not production PKI.
- Not regulator approval.
- Not production deployment assurance.
- The attestor key is demo-grade. Real deployments would use proper key management.
- Attestation signs verifier outputs, not the evidence package itself.
- A pass attestation means the verifier reported pass, not that the system is safe.
- A fail attestation is equally valid — it records that the verifier reported failure.
