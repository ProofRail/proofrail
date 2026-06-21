# Silver Relying-Party Profile v0.2.0

## 1. Purpose

This document defines the **Silver Relying-Party Profile v0.2.0** — the formal requirements a relying party must satisfy before accepting a ProofRail Silver evidence package.

A relying party may accept a ProofRail Silver evidence package only when:

- The required artifacts are present.
- The required checks pass.
- Revocation has been handled.
- A valid verification report is produced.
- The scope and limitations are explicit.

The profile does not certify a deployment. It defines the acceptance criteria for a signed, revocable, reportable, and optionally independently verifiable evidence package.

## 2. Scope

Silver profile conformance is **local relying-party verification**, not certification. It validates a Silver verification result — a structured report produced by a Silver verifier — against the profile's requirements.

Silver profile conformance does not:

- Certify a live AI system.
- Replace production PKI.
- Constitute third-party certification.
- Constitute Gold governance.
- Provide regulatory approval.
- Provide production audit opinion.

## 3. Relationship to Bronze

Silver builds on Bronze evidence bundles. A valid Bronze v0.1.3 evidence bundle manifest is a prerequisite for Silver verification. The Silver verifier checks the underlying Bronze bundle integrity as part of its verification flow.

The profile validator does not re-verify Bronze artifacts directly. It relies on the Silver verification report's `underlying_bundle_check` to confirm that the underlying Bronze bundle was verified.

## 4. Relationship to Silver Signed Bundle Assertion v0.1.0

The Silver Signed Bundle Assertion v0.1.0 is the cryptographic anchor for Silver verification. It contains:

- An Ed25519 signature over the raw bytes of a Bronze evidence bundle manifest.
- Issuer identity and key identity.
- Validity window (issued_at, expires_at).
- Subject metadata (bundle manifest path, type, SHA-256).

The profile requires that the verification report confirms the assertion was verified: issuer trusted, key trusted, algorithm valid, not expired, checksum matched, signature valid.

## 5. Relationship to Silver Revocation List v0.1.0

The Silver Revocation List v0.1.0 provides local relying-party trust withdrawal. A relying party can revoke trust in specific assertions, issuer keys, or bundles.

The profile has mode-dependent revocation requirements:

- `silver.base`: Revocation check should be performed. If not performed, the profile still passes but with a distinct warning reason code (`profile_requirements_satisfied_with_revocation_warning`).
- `silver.independent`: Revocation check must be performed and must pass.

## 6. Relationship to Silver Verification Report v0.1.0

The Silver Verification Report v0.1.0 is the primary evidence artifact consumed by the profile validator. The report records:

- Verifier identity.
- Structured inputs.
- Assertion, issuer, and subject metadata.
- Decision (pass/fail) with a stable reason code.
- Seven named check blocks.
- Limitations.

The profile validator confirms the report is structurally valid and that the decision and all required checks meet profile requirements.

## 7. Relationship to Independent Verifier Demo 002

Silver Demo 002 demonstrates relying-party separation: a standalone verifier operates on a portable verification package exported from the source repository, without importing or invoking the main ProofRail Silver verifier or Bronze bundle verifier.

The `silver.independent` profile mode validates that an independent verification was performed using such a package. The profile validator checks the package manifest structure and report verifier identity. Actual out-of-tree execution is demonstrated by the regression test, not asserted by the validator.

## 8. Profile Modes

### silver.base

The base Silver profile validates a Silver verification result produced by the main ProofRail Silver verifier or any verifier producing a conformant Silver Verification Report v0.1.0.

Required inputs:

- Silver Verification Report JSON.

### silver.independent

The independent Silver profile validates a Silver verification result produced by an independent verifier operating on an exported verification package.

Required inputs:

- Silver Verification Report JSON (from an independent verifier).
- Package manifest YAML (from the exported verification package).

`silver.independent` is a strictly stronger profile mode. It includes all `silver.base` requirements plus independent verification requirements.

## 9. Required Inputs

| Input | silver.base | silver.independent |
|-------|-------------|-------------------|
| Verification report (JSON) | Required | Required |
| Package manifest (YAML) | Not required | Required |

## 10. Required Checks

The profile validator performs six conformance checks:

| Check | Description |
|-------|-------------|
| `verification_report_valid` | Report is structurally valid per Silver Verification Report v0.1.0 |
| `decision_passed` | Report decision is `pass` with reason `all_checks_passed` |
| `required_checks_passed` | All six core verification checks passed: trust, algorithm, validity, bundle manifest checksum, signature, underlying bundle |
| `revocation_requirement` | Revocation check meets mode-dependent requirements |
| `independent_package_manifest_valid` | Package manifest is structurally valid with correct type and verifier metadata (silver.independent only; `not_applicable` for silver.base) |
| `limitations_present` | Report includes a non-empty limitations list |

## 11. Required Outputs

The profile validator emits a **profile conformance report** — a structured JSON artifact conforming to `schemas/silver-profile-conformance-report-v0.2.0.md`.

The conformance report includes:

- Profile metadata (mode, version).
- Input paths.
- Decision with stable reason code.
- Six named check blocks (all always present).
- Warnings list.
- Limitations list.

## 12. Verification Report Requirements

The Silver Verification Report must:

- Be valid JSON.
- Have `report_version == "v0.1.0"`.
- Have `report_type == "proofrail.silver.verification_report"`.
- Pass structural validation per `schemas/silver-verification-report-v0.1.0.md`.
- Have `decision.status == "pass"`.
- Have `decision.reason == "all_checks_passed"`.
- Include all seven check blocks.
- Include a non-empty limitations list.

## 13. Revocation Requirements

### silver.base

| Revocation state | Result |
|-----------------|--------|
| `performed == true`, `status == "pass"` | Profile passes with reason `profile_requirements_satisfied` |
| `performed == false`, `status == "not_performed"` | Profile passes with reason `profile_requirements_satisfied_with_revocation_warning` and an explicit warning |
| `performed == true`, `status == "fail"` | Profile fails with reason `required_check_failed` |

When revocation is not performed, the conformance report's `decision.reason` is `profile_requirements_satisfied_with_revocation_warning` and the `warnings` list includes: `"Revocation check was not performed. silver.base allows this but the relying-party acceptance is weaker without revocation."`

This ensures a consumer cannot mistake a warning-path pass for a clean pass.

### silver.independent

Revocation must be performed and must pass. There is no warning path.

| Revocation state | Result |
|-----------------|--------|
| `performed == true`, `status == "pass"` | Profile passes |
| Any other state | Profile fails with reason `revocation_not_performed` |

## 14. Independent Verification Requirements

For `silver.independent`, the profile validator checks:

1. `--package-manifest` is supplied.
2. Package manifest file exists and is valid YAML.
3. `package_type == "proofrail.silver.independent_verification_package"`.
4. Verifier metadata block exists with `verifier_demo`, `verifier_version`, `expected_report_schema`.
5. Report's `verifier.verifier_id == "proofrail-demo-independent-verifier"`.

These are structural checks on the package manifest and report verifier identity. The profile validator does not attempt out-of-tree execution — that is demonstrated by the regression test.

For `silver.base`, the `independent_package_manifest_valid` check has `status: "not_applicable"`.

## 15. Failure Semantics

The profile validator uses stable snake_case reason codes:

| Reason | Description |
|--------|-------------|
| `profile_requirements_satisfied` | All requirements met (clean pass) |
| `profile_requirements_satisfied_with_revocation_warning` | All requirements met but revocation was not performed (silver.base only) |
| `verification_report_invalid` | Report failed structural validation |
| `verification_report_failed` | Report decision is not pass/all_checks_passed |
| `required_check_failed` | One or more required verification checks did not pass |
| `revocation_not_performed` | Revocation check required but not performed (silver.independent) |
| `package_manifest_missing` | Package manifest required but not supplied or not found |
| `independence_requirement_failed` | Package manifest or verifier identity check failed |
| `limitations_missing` | Report limitations list is missing or empty |

## 16. Decision Semantics

The conformance report's `decision` block uses:

- `status: "pass"` — Profile requirements are satisfied. The relying party may accept the evidence package.
- `status: "fail"` — Profile requirements are not satisfied. The relying party should not accept the evidence package.

A `pass` with reason `profile_requirements_satisfied_with_revocation_warning` is a conditional pass. The relying party should note the warning and consider whether revocation checking is necessary for their use case.

## 17. Limitations and Non-Claims

Silver profile conformance is local demo conformance. It does not constitute:

- Gold certification or Gold governance.
- Third-party certification or regulatory approval.
- Production PKI or production key management.
- Production deployment assurance.
- Supply-chain security or trusted build provenance.
- Public accreditation or audit opinion.
- Evidence that the underlying AI system is correctly configured or that evidence files are truthful.

The correct claim for Silver profile conformance is:

> A relying party has validated that a signed, revocable, reportable, and optionally independently verifiable evidence package meets the Silver v0.2.0 profile requirements.

## 18. Conformance Report

The profile conformance report conforms to `schemas/silver-profile-conformance-report-v0.2.0.md`.

All six check blocks are always present in the conformance report, regardless of pass or fail. Checks not reached due to an earlier failure have `status: "not_performed"`. The `independent_package_manifest_valid` check has `status: "not_applicable"` for `silver.base`.

## 19. Examples

### Passing silver.base conformance report

```json
{
  "conformance_report_version": "v0.2.0",
  "conformance_report_type": "proofrail.silver.profile_conformance_report",
  "generated_at": "2026-06-21T12:00:00+00:00",
  "generated_by": "tools/silver/validate_silver_profile_v0_2_0.py",
  "profile": {
    "profile_id": "proofrail.silver.profile",
    "profile_version": "v0.2.0",
    "profile_mode": "silver.base"
  },
  "input": {
    "verification_report": "demos/silver-demo-001/runtime/verification-report.json",
    "package_manifest": null
  },
  "decision": {
    "status": "pass",
    "reason": "profile_requirements_satisfied"
  },
  "checks": {
    "verification_report_valid": { "status": "pass" },
    "decision_passed": { "status": "pass" },
    "required_checks_passed": { "status": "pass" },
    "revocation_requirement": { "status": "pass" },
    "independent_package_manifest_valid": { "status": "not_applicable" },
    "limitations_present": { "status": "pass" }
  },
  "warnings": [],
  "limitations": [
    "Silver profile conformance is local demo conformance.",
    "Not Gold certification.",
    "Not production certification."
  ]
}
```

### Passing silver.independent conformance report

```json
{
  "conformance_report_version": "v0.2.0",
  "conformance_report_type": "proofrail.silver.profile_conformance_report",
  "generated_at": "2026-06-21T12:00:00+00:00",
  "generated_by": "tools/silver/validate_silver_profile_v0_2_0.py",
  "profile": {
    "profile_id": "proofrail.silver.profile",
    "profile_version": "v0.2.0",
    "profile_mode": "silver.independent"
  },
  "input": {
    "verification_report": "path/to/independent-report.json",
    "package_manifest": "path/to/package-manifest.yaml"
  },
  "decision": {
    "status": "pass",
    "reason": "profile_requirements_satisfied"
  },
  "checks": {
    "verification_report_valid": { "status": "pass" },
    "decision_passed": { "status": "pass" },
    "required_checks_passed": { "status": "pass" },
    "revocation_requirement": { "status": "pass" },
    "independent_package_manifest_valid": { "status": "pass" },
    "limitations_present": { "status": "pass" }
  },
  "warnings": [],
  "limitations": [
    "Silver profile conformance is local demo conformance.",
    "Not Gold certification.",
    "Not production certification."
  ]
}
```

### silver.base with revocation warning

```json
{
  "decision": {
    "status": "pass",
    "reason": "profile_requirements_satisfied_with_revocation_warning"
  },
  "checks": {
    "revocation_requirement": { "status": "pass" }
  },
  "warnings": [
    "Revocation check was not performed. silver.base allows this but the relying-party acceptance is weaker without revocation."
  ]
}
```

## 20. Changelog

- **v0.2.0** — Initial release. Defines Silver relying-party profile with two modes (`silver.base`, `silver.independent`), required checks, revocation requirements, independent verification requirements, conformance report output, and failure reason codes.
