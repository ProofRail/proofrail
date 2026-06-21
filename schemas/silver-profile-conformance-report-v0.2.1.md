# Silver Profile Conformance Report Schema v0.2.1

## 1. Purpose

This schema defines the structure of a Silver Profile Conformance Report — the output of the Silver profile validator. The conformance report records whether a Silver verification result meets the requirements of the Silver Relying-Party Profile v0.2.1.

## 2. Relationship to Silver Profile v0.2.1

The Silver profile validator (`tools/silver/validate_silver_profile_v0_2_1.py`) implements this schema. This document is the normative definition; the validator is the reference implementation.

## 3. Relationship to v0.2.0

v0.2.1 adds the `silver.base.demo` profile mode and tightens `silver.base` revocation requirements. The `profile_requirements_satisfied_with_revocation_warning` reason is now restricted to `silver.base.demo` only.

## 4. Relationship to Silver Verification Report v0.1.0

The conformance report consumes a Silver Verification Report v0.1.0 as input and records whether the report satisfies profile requirements. The conformance report does not replicate the verification report's content — it references it by path.

## 5. Format

JSON. UTF-8 encoded. Single root object.

## 6. Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `conformance_report_version` | string | Must be `"v0.2.1"` |
| `conformance_report_type` | string | Must be `"proofrail.silver.profile_conformance_report"` |
| `generated_at` | string | ISO-8601 UTC timestamp |
| `generated_by` | string | Tool path that generated the report |
| `profile` | object | Profile metadata |
| `input` | object | Input paths |
| `decision` | object | Conformance decision |
| `checks` | object | Six named check blocks |
| `warnings` | array | List of warning strings (may be empty) |
| `limitations` | array | Non-empty list of limitation strings |

## 7. Profile Block

| Field | Type | Description |
|-------|------|-------------|
| `profile_id` | string | Must be `"proofrail.silver.profile"` |
| `profile_version` | string | Must be `"v0.2.1"` |
| `profile_mode` | string | `"silver.base"`, `"silver.base.demo"`, or `"silver.independent"` |

## 8. Input Block

| Field | Type | Description |
|-------|------|-------------|
| `verification_report` | string | Path to the Silver Verification Report JSON |
| `package_manifest` | string or null | Path to the package manifest YAML (null for silver.base and silver.base.demo) |

## 9. Decision Block

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"pass"` or `"fail"` |
| `reason` | string | Stable snake_case reason code |

### Reason Codes

| Reason | Status | Description |
|--------|--------|-------------|
| `profile_requirements_satisfied` | pass | All requirements met (clean pass) |
| `profile_requirements_satisfied_with_revocation_warning` | pass | All requirements met but revocation was not performed (silver.base.demo only) |
| `verification_report_invalid` | fail | Report failed structural validation |
| `verification_report_failed` | fail | Report decision is not pass/all_checks_passed |
| `required_check_failed` | fail | One or more required verification checks did not pass |
| `revocation_not_performed` | fail | Revocation check required but not performed (silver.base and silver.independent) |
| `package_manifest_missing` | fail | Package manifest required but not supplied or not found |
| `independence_requirement_failed` | fail | Package manifest or verifier identity check failed |
| `limitations_missing` | fail | Report limitations list is missing or empty |

## 10. Checks Block

Six named check blocks are always present. Each check block has at minimum a `status` field.

| Check | Description |
|-------|-------------|
| `verification_report_valid` | Report is structurally valid per Silver Verification Report v0.1.0 |
| `decision_passed` | Report decision is pass with reason all_checks_passed |
| `required_checks_passed` | All six core verification checks passed |
| `revocation_requirement` | Revocation check meets mode-dependent requirements |
| `independent_package_manifest_valid` | Package manifest is structurally valid (silver.independent only) |
| `limitations_present` | Report includes a non-empty limitations list |

### Check Statuses

| Status | Meaning |
|--------|---------|
| `pass` | Check requirement satisfied |
| `fail` | Check requirement not satisfied |
| `not_performed` | Check was not reached due to an earlier failure |
| `not_applicable` | Check does not apply to this profile mode |

The `not_applicable` status is used only for `independent_package_manifest_valid` in `silver.base` and `silver.base.demo` modes.

## 11. Warnings

An array of human-readable warning strings. May be empty.

The primary use case is the revocation warning for `silver.base.demo` when `revocation_check.performed == false`:

```json
"warnings": [
  "Revocation check was not performed. silver.base.demo allows this but the relying-party acceptance is weaker without revocation."
]
```

## 12. Limitations

A non-empty list of limitation strings. The conformance report must include its own limitations, distinct from the verification report's limitations.

Standard limitations:

```json
"limitations": [
  "Silver profile conformance is local demo conformance.",
  "Not Gold certification.",
  "Not production certification."
]
```

## 13. Validation Rules

A conformance report is structurally valid when:

1. All required top-level fields are present.
2. `conformance_report_version` is `"v0.2.1"`.
3. `conformance_report_type` is `"proofrail.silver.profile_conformance_report"`.
4. `profile.profile_mode` is `"silver.base"`, `"silver.base.demo"`, or `"silver.independent"`.
5. `decision.status` is `"pass"` or `"fail"`.
6. `decision.reason` is a non-empty string.
7. All six check blocks are present with valid statuses.
8. `warnings` is a list (may be empty).
9. `limitations` is a non-empty list.

## 14. Non-Goals

This schema does not define:

- Gold certification decisions.
- Signed conformance reports.
- Production certification semantics.
- External audit workflows.

## 15. Changelog

- **v0.2.1** — Adds `silver.base.demo` profile mode. Restricts `profile_requirements_satisfied_with_revocation_warning` to `silver.base.demo` only. `silver.base` now requires revocation.
- **v0.2.0** — Initial release.
