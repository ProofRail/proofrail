# Silver Relying-Party Profile v0.2.1

## 1. Purpose

This document defines the **Silver Relying-Party Profile v0.2.1** — the formal requirements a relying party must satisfy before accepting a ProofRail Silver evidence package.

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

## 3. Relationship to v0.2.0

v0.2.0 introduced the Silver Relying-Party Profile with two modes (`silver.base`, `silver.independent`). In v0.2.0, `silver.base` allowed revocation absence with a warning path (`profile_requirements_satisfied_with_revocation_warning`).

v0.2.1 tightens `silver.base` to require revocation. The v0.2.0 warning path is preserved in a new `silver.base.demo` mode for demo and development use.

v0.2.0 made revocation absence visible. v0.2.1 makes revocation expected for ordinary Silver reliance.

v0.2.0 artifacts and tests remain unchanged and functional. The v0.2.0 validator (`validate_silver_profile_v0_2_0.py`) continues to operate with its original semantics.

## 4. Relationship to Bronze

Silver builds on Bronze evidence bundles. A valid Bronze v0.1.3 evidence bundle manifest is a prerequisite for Silver verification. The Silver verifier checks the underlying Bronze bundle integrity as part of its verification flow.

The profile validator does not re-verify Bronze artifacts directly. It relies on the Silver verification report's `underlying_bundle_check` to confirm that the underlying Bronze bundle was verified.

## 5. Relationship to Silver Signed Bundle Assertion v0.1.0

The Silver Signed Bundle Assertion v0.1.0 is the cryptographic anchor for Silver verification. It contains:

- An Ed25519 signature over the raw bytes of a Bronze evidence bundle manifest.
- Issuer identity and key identity.
- Validity window (issued_at, expires_at).
- Subject metadata (bundle manifest path, type, SHA-256).

The profile requires that the verification report confirms the assertion was verified: issuer trusted, key trusted, algorithm valid, not expired, checksum matched, signature valid.

## 6. Relationship to Silver Revocation List v0.1.0

The Silver Revocation List v0.1.0 provides local relying-party trust withdrawal. A relying party can revoke trust in specific assertions, issuer keys, or bundles.

The profile has mode-dependent revocation requirements:

- `silver.base`: Revocation check must be performed and must pass.
- `silver.base.demo`: Revocation check should be performed. If not performed, the profile still passes but with a distinct warning reason code (`profile_requirements_satisfied_with_revocation_warning`).
- `silver.independent`: Revocation check must be performed and must pass.

## 7. Relationship to Silver Verification Report v0.1.0

The Silver Verification Report v0.1.0 is the primary evidence artifact consumed by the profile validator. The report records:

- Verifier identity.
- Structured inputs.
- Assertion, issuer, and subject metadata.
- Decision (pass/fail) with a stable reason code.
- Seven named check blocks.
- Limitations.

The profile validator confirms the report is structurally valid and that the decision and all required checks meet profile requirements.

## 8. Profile Modes

### silver.base

The base Silver profile validates a Silver verification result produced by the main ProofRail Silver verifier or any verifier producing a conformant Silver Verification Report v0.1.0. Revocation must be performed and must pass.

Required inputs:

- Silver Verification Report JSON.

### silver.base.demo

The demo base Silver profile preserves the v0.2.0 `silver.base` semantics. Revocation is expected but not required — if not performed, the profile passes with a warning reason code.

This mode is intended for demo and development workflows where revocation infrastructure may not be configured.

Required inputs:

- Silver Verification Report JSON.

### silver.independent

The independent Silver profile validates a Silver verification result produced by an independent verifier operating on an exported verification package.

Required inputs:

- Silver Verification Report JSON (from an independent verifier).
- Package manifest YAML (from the exported verification package).

`silver.independent` is a strictly stronger profile mode. It includes all `silver.base` requirements plus independent verification requirements.

## 9. Relationship to Independent Verifier Demo 002

Silver Demo 002 demonstrates relying-party separation: a standalone verifier operates on a portable verification package exported from the source repository, without importing or invoking the main ProofRail Silver verifier or Bronze bundle verifier.

The `silver.independent` profile mode validates that an independent verification was performed using such a package. The profile validator checks the package manifest structure and report verifier identity. Actual out-of-tree execution is demonstrated by the regression test, not asserted by the validator.

## 10. Required Inputs

| Input | silver.base | silver.base.demo | silver.independent |
|-------|-------------|-------------------|-------------------|
| Verification report (JSON) | Required | Required | Required |
| Package manifest (YAML) | Not required | Not required | Required |

## 11. Required Checks

The profile validator performs six conformance checks:

| Check | Description |
|-------|-------------|
| `verification_report_valid` | Report is structurally valid per Silver Verification Report v0.1.0 |
| `decision_passed` | Report decision is `pass` with reason `all_checks_passed` |
| `required_checks_passed` | All six core verification checks passed: trust, algorithm, validity, bundle manifest checksum, signature, underlying bundle |
| `revocation_requirement` | Revocation check meets mode-dependent requirements |
| `independent_package_manifest_valid` | Package manifest is structurally valid with correct type and verifier metadata (silver.independent only; `not_applicable` for silver.base and silver.base.demo) |
| `limitations_present` | Report includes a non-empty limitations list |

## 12. Required Outputs

The profile validator emits a **profile conformance report** — a structured JSON artifact conforming to `schemas/silver-profile-conformance-report-v0.2.1.md`.

The conformance report includes:

- Profile metadata (mode, version).
- Input paths.
- Decision with stable reason code.
- Six named check blocks (all always present).
- Warnings list.
- Limitations list.

## 13. Verification Report Requirements

The Silver Verification Report must:

- Be valid JSON.
- Have `report_version == "v0.1.0"`.
- Have `report_type == "proofrail.silver.verification_report"`.
- Pass structural validation per `schemas/silver-verification-report-v0.1.0.md`.
- Have `decision.status == "pass"`.
- Have `decision.reason == "all_checks_passed"`.
- Include all seven check blocks.
- Include a non-empty limitations list.

## 14. Revocation Requirements

### silver.base

Revocation must be performed and must pass.

| Revocation state | Result |
|-----------------|--------|
| `performed == true`, `status == "pass"` | Profile passes with reason `profile_requirements_satisfied` |
| `performed == true`, `status == "fail"` | Profile fails with reason `required_check_failed` |
| `performed == false` or not performed | Profile fails with reason `revocation_not_performed` |

### silver.base.demo

Preserves the v0.2.0 `silver.base` revocation semantics.

| Revocation state | Result |
|-----------------|--------|
| `performed == true`, `status == "pass"` | Profile passes with reason `profile_requirements_satisfied` |
| `performed == false`, `status == "not_performed"` | Profile passes with reason `profile_requirements_satisfied_with_revocation_warning` and an explicit warning |
| `performed == true`, `status == "fail"` | Profile fails with reason `required_check_failed` |

When revocation is not performed in `silver.base.demo`, the conformance report's `decision.reason` is `profile_requirements_satisfied_with_revocation_warning` and the `warnings` list includes: `"Revocation check was not performed. silver.base.demo allows this but the relying-party acceptance is weaker without revocation."`

This ensures a consumer cannot mistake a warning-path pass for a clean pass.

### silver.independent

Revocation must be performed and must pass. There is no warning path.

| Revocation state | Result |
|-----------------|--------|
| `performed == true`, `status == "pass"` | Profile passes |
| Any other state | Profile fails with reason `revocation_not_performed` |

## 15. Independent Verification Requirements

For `silver.independent`, the profile validator checks:

1. `--package-manifest` is supplied.
2. Package manifest file exists and is valid YAML.
3. `package_type == "proofrail.silver.independent_verification_package"`.
4. Verifier metadata block exists with `verifier_demo`, `verifier_version`, `expected_report_schema`.
5. Report's `verifier.verifier_id == "proofrail-demo-independent-verifier"`.

These are structural checks on the package manifest and report verifier identity. The profile validator does not attempt out-of-tree execution — that is demonstrated by the regression test.

For `silver.base` and `silver.base.demo`, the `independent_package_manifest_valid` check has `status: "not_applicable"`.

## 16. Failure Semantics

The profile validator uses stable snake_case reason codes:

| Reason | Description |
|--------|-------------|
| `profile_requirements_satisfied` | All requirements met (clean pass) |
| `profile_requirements_satisfied_with_revocation_warning` | All requirements met but revocation was not performed (silver.base.demo only) |
| `verification_report_invalid` | Report failed structural validation |
| `verification_report_failed` | Report decision is not pass/all_checks_passed |
| `required_check_failed` | One or more required verification checks did not pass |
| `revocation_not_performed` | Revocation check required but not performed (silver.base and silver.independent) |
| `package_manifest_missing` | Package manifest required but not supplied or not found |
| `independence_requirement_failed` | Package manifest or verifier identity check failed |
| `limitations_missing` | Report limitations list is missing or empty |

## 17. Decision Semantics

The conformance report's `decision` block uses:

- `status: "pass"` — Profile requirements are satisfied. The relying party may accept the evidence package.
- `status: "fail"` — Profile requirements are not satisfied. The relying party should not accept the evidence package.

A `pass` with reason `profile_requirements_satisfied_with_revocation_warning` is a conditional pass available only in `silver.base.demo` mode. The relying party should note the warning and consider whether revocation checking is necessary for their use case.

## 18. Limitations and Non-Claims

Silver profile conformance is local demo conformance. It does not constitute:

- Gold certification or Gold governance.
- Third-party certification or regulatory approval.
- Production PKI or production key management.
- Production deployment assurance.
- Supply-chain security or trusted build provenance.
- Public accreditation or audit opinion.
- Evidence that the underlying AI system is correctly configured or that evidence files are truthful.

The correct claim for Silver profile conformance is:

> A relying party has validated that a signed, revocable, reportable, and optionally independently verifiable evidence package meets the Silver v0.2.1 profile requirements.

## 19. Conformance Report

The profile conformance report conforms to `schemas/silver-profile-conformance-report-v0.2.1.md`.

All six check blocks are always present in the conformance report, regardless of pass or fail. Checks not reached due to an earlier failure have `status: "not_performed"`. The `independent_package_manifest_valid` check has `status: "not_applicable"` for `silver.base` and `silver.base.demo`.

## 20. Examples

### Passing silver.base conformance report

```json
{
  "conformance_report_version": "v0.2.1",
  "conformance_report_type": "proofrail.silver.profile_conformance_report",
  "generated_at": "2026-06-21T12:00:00+00:00",
  "generated_by": "tools/silver/validate_silver_profile_v0_2_1.py",
  "profile": {
    "profile_id": "proofrail.silver.profile",
    "profile_version": "v0.2.1",
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

### Passing silver.base.demo with revocation warning

This conformance report is produced when the input verification report's `revocation_check` has `performed == false` and `status == "not_performed"`:

```jsonc
// Input verification report's revocation check (triggers the warning path):
"revocation_check": {
  "performed": false,
  "status": "not_performed"
}
```

Resulting conformance report:

```json
{
  "conformance_report_version": "v0.2.1",
  "conformance_report_type": "proofrail.silver.profile_conformance_report",
  "generated_at": "2026-06-21T12:00:00+00:00",
  "generated_by": "tools/silver/validate_silver_profile_v0_2_1.py",
  "profile": {
    "profile_id": "proofrail.silver.profile",
    "profile_version": "v0.2.1",
    "profile_mode": "silver.base.demo"
  },
  "input": {
    "verification_report": "demos/silver-demo-001/runtime/verification-report.json",
    "package_manifest": null
  },
  "decision": {
    "status": "pass",
    "reason": "profile_requirements_satisfied_with_revocation_warning"
  },
  "checks": {
    "verification_report_valid": { "status": "pass" },
    "decision_passed": { "status": "pass" },
    "required_checks_passed": { "status": "pass" },
    "revocation_requirement": { "status": "pass" },
    "independent_package_manifest_valid": { "status": "not_applicable" },
    "limitations_present": { "status": "pass" }
  },
  "warnings": [
    "Revocation check was not performed. silver.base.demo allows this but the relying-party acceptance is weaker without revocation."
  ],
  "limitations": [
    "Silver profile conformance is local demo conformance.",
    "Not Gold certification.",
    "Not production certification."
  ]
}
```

Note: with `silver.base` (not `silver.base.demo`), the same input report would produce a `fail` with reason `revocation_not_performed`.

### Passing silver.independent conformance report

```json
{
  "conformance_report_version": "v0.2.1",
  "conformance_report_type": "proofrail.silver.profile_conformance_report",
  "generated_at": "2026-06-21T12:00:00+00:00",
  "generated_by": "tools/silver/validate_silver_profile_v0_2_1.py",
  "profile": {
    "profile_id": "proofrail.silver.profile",
    "profile_version": "v0.2.1",
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

## 21. Changelog

- **v0.2.1** — Adds `silver.base.demo` mode preserving v0.2.0 warning path. Tightens `silver.base` to require revocation. Adds package handoff format documentation. Adds canonical conformance examples.
- **v0.2.0** — Initial release. Defines Silver relying-party profile with two modes (`silver.base`, `silver.independent`), required checks, revocation requirements, independent verification requirements, conformance report output, and failure reason codes.
