# Silver Verification Report Schema v0.1.0

## 1. Purpose

The Silver Verification Report is a structured JSON artifact emitted by the ProofRail Silver verifier after evaluating a Silver Signed Bundle Assertion. It records the verifier's decision, all checks performed, inputs consumed, issuer and subject metadata, and applicable limitations.

The report serves as a durable evidence artifact that can be referenced by downstream consumers — including a future Gold certifier — without requiring them to silently rerun Silver verification.

## 2. Relationship to Silver Signed Bundle Assertion v0.1.0

The verification report is produced by verifying a Silver Signed Bundle Assertion v0.1.0. The report references the assertion by ID, version, and type. It records the assertion's issuer, subject, and validity window.

The report does not replace the signed assertion. It records the verifier's evaluation of it.

## 3. Relationship to Silver Revocation List v0.1.0

If a revocation list is supplied to the verifier, the report records whether a revocation check was performed and its outcome. The revocation check may result in `pass` (no matches), `fail` (assertion, issuer key, or bundle hash revoked), or `not_performed` (no revocation list supplied).

## 4. Why a Verification Report Is Needed

Without a structured report, verification results exist only as console output and exit codes — transient, unstructured, and not referenceable. A schema-backed report:

- Provides a stable, machine-readable record of the verifier's decision.
- Enables downstream consumers to inspect individual check results.
- Allows a future Gold certifier to reference a specific verification report as input.
- Makes failure diagnostics structured and parseable.

## 5. Required Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `report_version` | string | Must be `"v0.1.0"`. |
| `report_type` | string | Must be `"proofrail.silver.verification_report"`. |
| `report_id` | string | Unique identifier for this report (derived from the assertion ID). |
| `generated_at` | string | ISO-8601 UTC timestamp of report generation. |
| `generated_by` | string | Tool that generated the report. |
| `verifier` | object | Verifier identity. |
| `inputs` | object | Paths and parameters supplied to the verifier. |
| `assertion` | object | Assertion metadata. |
| `issuer` | object | Issuer and key metadata. |
| `subject` | object | Subject (bundle manifest) metadata. |
| `decision` | object | The verifier's pass/fail decision with reason code. |
| `checks` | object | Per-check results. |
| `limitations` | array | List of limitation statements. |

## 6. `verifier` Structure

| Field | Type | Description |
|---|---|---|
| `verifier_id` | string | Unique identifier for the verifier. |
| `verifier_label` | string | Human-readable verifier label. |

## 7. `inputs` Structure

| Field | Type | Description |
|---|---|---|
| `assertion_path` | string | Path to the signed assertion YAML. |
| `trust_policy_path` | string | Path to the trust policy YAML. |
| `revocation_list_path` | string or null | Path to the revocation list YAML, or null if not supplied. |
| `silver_root` | string | Silver demo root directory. |
| `bronze_package_root` | string | Bronze evidence package root directory. |

## 8. `assertion` Structure

| Field | Type | Description |
|---|---|---|
| `assertion_id` | string | The assertion's unique identifier. |
| `assertion_version` | string | The assertion schema version (e.g., `"v0.1.0"`). |
| `assertion_type` | string | The assertion type (e.g., `"proofrail.silver.signed_bundle_assertion"`). |

## 9. `issuer` Structure

| Field | Type | Description |
|---|---|---|
| `issuer_id` | string | The issuer's unique identifier. |
| `key_id` | string | The key identifier used for signing. |
| `algorithm` | string | Signing algorithm (e.g., `"ed25519"`). |
| `public_key_fingerprint_sha256` | string | SHA-256 fingerprint of the public key in `sha256:<64 hex>` format. |

## 10. `subject` Structure

| Field | Type | Description |
|---|---|---|
| `bundle_manifest` | string | Relative path to the bundle manifest. |
| `bundle_manifest_type` | string | Type of the bundle manifest (e.g., `"proofrail.bronze.evidence_bundle"`). |
| `bundle_manifest_sha256` | string | SHA-256 hash of the bundle manifest as recorded in the assertion, in `sha256:<64 hex>` format. |

## 11. `decision` Structure

| Field | Type | Description |
|---|---|---|
| `status` | string | `"pass"` or `"fail"`. |
| `reason` | string | Stable snake_case reason code (see Section 14). |

On pass: `status` is `"pass"` and `reason` is `"all_checks_passed"`.

On fail: `status` is `"fail"` and `reason` is a stable failure reason code identifying the first check that failed.

## 12. `checks` Structure

The `checks` object contains exactly seven check blocks, one for each verification step. Every report — pass or fail — includes all seven blocks.

### Check Status Values

Each check block includes a `status` field with one of:

| Status | Meaning |
|---|---|
| `pass` | Check was performed and succeeded. |
| `fail` | Check was performed and failed. |
| `not_performed` | Check was not reached due to an earlier failure, or was not applicable (e.g., no revocation list supplied). |

### `trust_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |

### `algorithm_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |

### `validity_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |
| `issued_at` | string | ISO-8601 timestamp from the assertion (present when status is `pass` or `fail`). |
| `expires_at` | string | ISO-8601 timestamp from the assertion (present when status is `pass` or `fail`). |

### `bundle_manifest_checksum_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |
| `expected_sha256` | string | SHA-256 hash from the assertion in `sha256:<64 hex>` format (present when status is `pass` or `fail`). |
| `actual_sha256` | string | SHA-256 hash computed from the manifest file in `sha256:<64 hex>` format (present when status is `pass` or `fail`). |

### `revocation_check`

| Field | Type | Description |
|---|---|---|
| `performed` | boolean | Whether a revocation check was performed. Always present. |
| `status` | string | `pass`, `fail`, or `not_performed`. |
| `revocation_list` | string | Path to the revocation list (present when `performed` is true). |

### `signature_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |
| `algorithm` | string | Signing algorithm (present when status is `pass` or `fail`). |

### `underlying_bundle_check`

| Field | Type | Description |
|---|---|---|
| `status` | string | `pass`, `fail`, or `not_performed`. |
| `bundle_file_count` | integer | Number of files verified in the bundle (present when status is `pass`). |

## 13. Check Ordering and Short-Circuit Behavior

The verifier performs checks in this order:

1. `trust_check`
2. `algorithm_check`
3. `validity_check`
4. `bundle_manifest_checksum_check`
5. `revocation_check`
6. `signature_check`
7. `underlying_bundle_check`

On failure, the verifier short-circuits: subsequent checks are not performed and their status is `"not_performed"`. The `decision.reason` identifies the first failing check.

On pass, all seven checks have status `"pass"` (or `"not_performed"` for `revocation_check` when no revocation list is supplied).

## 14. Failure Reason Codes

| Reason Code | Description |
|---|---|
| `all_checks_passed` | All checks passed. Used with `decision.status == "pass"`. |
| `issuer_not_trusted` | Issuer ID not found in trust policy. |
| `key_id_not_trusted` | Issuer found but key_id not matched. |
| `unsupported_algorithm` | Signature algorithm is not ed25519. |
| `invalid_validity_timestamps` | Cannot parse issued_at or expires_at. |
| `assertion_not_yet_valid` | Current time is before issued_at. |
| `assertion_expired` | Current time is after expires_at. |
| `bundle_manifest_not_found` | Bundle manifest file not found. |
| `bundle_manifest_checksum_mismatch` | SHA-256 of manifest file does not match assertion. |
| `assertion_revoked` | Assertion ID found on revocation list. |
| `issuer_key_revoked` | Issuer key pair found on revocation list. |
| `bundle_revoked` | Bundle manifest hash found on revocation list. |
| `signature_verification_failed` | Ed25519 signature verification failed. |
| `underlying_bundle_verification_failed` | Underlying Bronze bundle integrity check failed. |
| `invalid_report_input` | Input files are malformed (e.g., invalid YAML mapping). |

## 15. Limitations Field

The `limitations` field is a non-empty list of strings describing what the report does not assert. The standard limitations for v0.1.0 are:

```json
[
  "Local demo verification only.",
  "Not production PKI.",
  "Not third-party certification.",
  "Not Gold certification."
]
```

## 16. Non-Goals

This schema does not define:

- Signed verification reports. The report is unsigned in v0.1.0.
- Gold certification decisions. The report is a Silver verification artifact.
- Production audit opinions. The report records a demo verifier's result.
- Third-party certification. The report is generated by the same tooling that performs verification.
- Public registry publication. Reports are local artifacts.
- Transparency-log-backed verification. Reports are not logged in v0.1.0.

A future Gold certifier may rely on this report as an input, but the report itself is not a Gold certification decision.

## 17. Example Passing Report

```json
{
  "report_version": "v0.1.0",
  "report_type": "proofrail.silver.verification_report",
  "report_id": "proofrail-silver-demo-001-verification-report",
  "generated_at": "2026-06-15T12:00:00+00:00",
  "generated_by": "tools/silver/verify_signed_bundle_assertion_v0_1_0.py",
  "verifier": {
    "verifier_id": "proofrail-demo-verifier-b",
    "verifier_label": "ProofRail Demo Verifier B"
  },
  "inputs": {
    "assertion_path": "demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml",
    "trust_policy_path": "demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml",
    "revocation_list_path": "demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml",
    "silver_root": "demos/silver-demo-001",
    "bronze_package_root": "demos/composed-bronze-demo-001"
  },
  "assertion": {
    "assertion_id": "proofrail-silver-demo-001",
    "assertion_version": "v0.1.0",
    "assertion_type": "proofrail.silver.signed_bundle_assertion"
  },
  "issuer": {
    "issuer_id": "proofrail-demo-issuer-a",
    "key_id": "proofrail-demo-issuer-a-ed25519-001",
    "algorithm": "ed25519",
    "public_key_fingerprint_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
  },
  "subject": {
    "bundle_manifest": "../composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml",
    "bundle_manifest_type": "proofrail.bronze.evidence_bundle",
    "bundle_manifest_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
  },
  "decision": {
    "status": "pass",
    "reason": "all_checks_passed"
  },
  "checks": {
    "trust_check": { "status": "pass" },
    "algorithm_check": { "status": "pass" },
    "validity_check": {
      "status": "pass",
      "issued_at": "2026-06-15T12:00:00+00:00",
      "expires_at": "2026-09-13T12:00:00+00:00"
    },
    "bundle_manifest_checksum_check": {
      "status": "pass",
      "expected_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "actual_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    },
    "revocation_check": {
      "performed": true,
      "status": "pass",
      "revocation_list": "demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml"
    },
    "signature_check": { "status": "pass", "algorithm": "ed25519" },
    "underlying_bundle_check": { "status": "pass", "bundle_file_count": 16 }
  },
  "limitations": [
    "Local demo verification only.",
    "Not production PKI.",
    "Not third-party certification.",
    "Not Gold certification."
  ]
}
```

## 18. Example Failing Report

```json
{
  "report_version": "v0.1.0",
  "report_type": "proofrail.silver.verification_report",
  "report_id": "proofrail-silver-demo-001-verification-report",
  "generated_at": "2026-06-15T12:00:00+00:00",
  "generated_by": "tools/silver/verify_signed_bundle_assertion_v0_1_0.py",
  "verifier": {
    "verifier_id": "proofrail-demo-verifier-b",
    "verifier_label": "ProofRail Demo Verifier B"
  },
  "inputs": {
    "assertion_path": "demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml",
    "trust_policy_path": "demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml",
    "revocation_list_path": "demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml",
    "silver_root": "demos/silver-demo-001",
    "bronze_package_root": "demos/composed-bronze-demo-001"
  },
  "assertion": {
    "assertion_id": "proofrail-silver-demo-001",
    "assertion_version": "v0.1.0",
    "assertion_type": "proofrail.silver.signed_bundle_assertion"
  },
  "issuer": {
    "issuer_id": "proofrail-demo-issuer-a",
    "key_id": "proofrail-demo-issuer-a-ed25519-001",
    "algorithm": "ed25519",
    "public_key_fingerprint_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
  },
  "subject": {
    "bundle_manifest": "../composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml",
    "bundle_manifest_type": "proofrail.bronze.evidence_bundle",
    "bundle_manifest_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
  },
  "decision": {
    "status": "fail",
    "reason": "assertion_revoked"
  },
  "checks": {
    "trust_check": { "status": "pass" },
    "algorithm_check": { "status": "pass" },
    "validity_check": {
      "status": "pass",
      "issued_at": "2026-06-15T12:00:00+00:00",
      "expires_at": "2026-09-13T12:00:00+00:00"
    },
    "bundle_manifest_checksum_check": {
      "status": "pass",
      "expected_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "actual_sha256": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    },
    "revocation_check": {
      "performed": true,
      "status": "fail",
      "revocation_list": "demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml"
    },
    "signature_check": { "status": "not_performed" },
    "underlying_bundle_check": { "status": "not_performed" }
  },
  "limitations": [
    "Local demo verification only.",
    "Not production PKI.",
    "Not third-party certification.",
    "Not Gold certification."
  ]
}
```

## 19. Changelog

### v0.1.0

- Initial release.
- Structured verification report with decision, checks, and limitations.
- Report emitted on both pass and fail.
- Seven check blocks always present; unreached checks have status `"not_performed"`.
- Stable snake_case failure reason codes.
