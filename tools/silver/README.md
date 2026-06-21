# ProofRail Silver Tools

This directory contains tooling for ProofRail Minimal Silver signed bundle assertions.

## Current supported schemas

- Silver Signed Bundle Assertion v0.1.0
- Silver Revocation List v0.1.0
- Silver Verification Report v0.1.0
- Silver Relying-Party Profile v0.2.0
- Silver Relying-Party Profile v0.2.1
- Silver Verifier Output Attestation v0.1.0
- Silver Multi-Principal Authority Fixture v0.1.0
- Silver Protected Action Request v0.1.0
- Silver Protected Action Decision Report v0.1.0

## Demo Issuer Generator

Generates a demo Ed25519 keypair and a local verifier trust policy.

```bash
python3 tools/silver/generate_demo_issuer_v0_1_0.py demos/silver-demo-001
python3 tools/silver/generate_demo_issuer_v0_1_0.py demos/silver-demo-001 --force
```

Generated files (runtime-only, not committed):

```
demos/silver-demo-001/runtime/issuer-a/private-key.pem
demos/silver-demo-001/runtime/issuer-a/public-key.pem
demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml
```

The `--force` flag overwrites an existing keypair. Private keys are set to `0600` permissions.

## Bundle Manifest Signer

Signs a Bronze v0.1.3 evidence bundle manifest with Ed25519, producing a Silver Signed Bundle Assertion YAML.

```bash
python3 tools/silver/sign_bundle_manifest_v0_1_0.py demos/silver-demo-001 \
  --private-key demos/silver-demo-001/runtime/issuer-a/private-key.pem \
  --output demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml
```

The signature is over the raw bytes of the bundle manifest file. No YAML canonicalization is applied.

## Signed Assertion Verifier

Verifies a Silver Signed Bundle Assertion against a local trust policy.

```bash
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml \
  demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml \
  --silver-root demos/silver-demo-001 \
  --bronze-package-root demos/composed-bronze-demo-001 \
  --report demos/silver-demo-001/runtime/verification-report.json
```

The verifier checks:

1. Issuer and key_id are listed in the trust policy.
2. Signature algorithm is Ed25519.
3. Assertion has not expired.
4. Bundle manifest SHA-256 matches the recorded checksum.
5. Ed25519 signature over the bundle manifest raw bytes is valid.
6. Underlying v0.1.3 bundle manifest passes integrity verification.

Exit codes: 0 (pass), 1 (verification failed), 2 (usage error).

## Demo Revocation List Generator

Generates a local demo revocation list for relying-party trust withdrawal.

```bash
# Empty revocation list
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001

# Revoke an assertion ID
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
  --revoke-assertion proofrail-silver-demo-001 --reason "demo assertion revocation"

# Revoke an issuer key (issuer_id:key_id format)
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
  --revoke-issuer-key proofrail-demo-issuer-a:proofrail-demo-issuer-a-ed25519-001 \
  --reason "demo key revocation"

# Revoke a bundle hash
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
  --revoke-bundle-sha256 sha256:<64 hex> --reason "demo bundle revocation"
```

The `--force` flag overwrites an existing revocation list. Output is written to `demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml` by default.

The generator exits 0 on success, 1 if the output exists without `--force`, and 2 on usage error.

### Verifier Revocation List Support

The verifier accepts an optional `--revocation-list` flag:

```bash
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml \
  demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml \
  --silver-root demos/silver-demo-001 \
  --bronze-package-root demos/composed-bronze-demo-001 \
  --revocation-list demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml
```

When a revocation list is supplied, the verifier rejects the assertion if:

- The assertion ID is listed in `revoked_assertions` → `FAIL: assertion revoked`
- The issuer/key pair is listed in `revoked_issuer_keys` → `FAIL: issuer key revoked`
- The bundle manifest hash is listed in `revoked_bundles` → `FAIL: bundle revoked`

When no `--revocation-list` is supplied, existing behavior is unchanged.

## Verification Report

When the verifier is invoked with `--report`, it writes a structured Silver Verification Report v0.1.0 JSON file. The report conforms to `schemas/silver-verification-report-v0.1.0.md` and includes:

- Report metadata (`report_version`, `report_type`, `report_id`, `generated_at`, `generated_by`)
- Verifier identity
- Structured inputs (assertion path, trust policy, revocation list, roots)
- Assertion, issuer, and subject metadata
- Decision block with `status` (`pass` or `fail`) and a stable snake_case `reason` code
- Seven check blocks: `trust_check`, `algorithm_check`, `validity_check`, `bundle_manifest_checksum_check`, `revocation_check`, `signature_check`, `underlying_bundle_check`
- Limitations list

Every report — pass or fail — includes all seven check blocks. Checks not reached due to an earlier failure have `status: "not_performed"`.

The report is written on both pass and fail when `--report` is supplied.

The report is a verifier-generated evidence artifact. It is not signed in v0.1.0 and is not a Gold certification decision.

### Failure Reason Codes

| Reason | Description |
|---|---|
| `all_checks_passed` | All checks passed (decision status `pass`) |
| `issuer_not_trusted` | Issuer ID not in trust policy |
| `key_id_not_trusted` | Issuer found but key_id not matched |
| `unsupported_algorithm` | Algorithm is not ed25519 |
| `invalid_validity_timestamps` | Cannot parse timestamps |
| `assertion_not_yet_valid` | Current time before issued_at |
| `assertion_expired` | Current time after expires_at |
| `bundle_manifest_not_found` | Bundle manifest file missing |
| `bundle_manifest_checksum_mismatch` | SHA-256 mismatch |
| `assertion_revoked` | Assertion ID on revocation list |
| `issuer_key_revoked` | Issuer key on revocation list |
| `bundle_revoked` | Bundle hash on revocation list |
| `signature_verification_failed` | Ed25519 signature invalid |
| `underlying_bundle_verification_failed` | Bundle integrity check failed |
| `invalid_report_input` | Input files malformed |

## Verification Report Validator

Validates the structure of a Silver Verification Report v0.1.0. Does not rerun cryptographic verification.

```bash
python3 tools/silver/validate_silver_verification_report_v0_1_0.py <report.json>
```

Exit codes: 0 (valid), 1 (invalid), 2 (usage error).

## Independent Verification Package Export

Exports a portable verification package from Demo 001 artifacts for use with the independent verifier.

```bash
python3 tools/silver/export_independent_verification_package_v0_1_0.py \
  --bronze-root demos/composed-bronze-demo-001 \
  --silver-root demos/silver-demo-001 \
  --output demos/silver-demo-002-independent-verifier/runtime/package \
  --force
```

The export tool:

1. Validates that all required Bronze and Silver artifacts exist.
2. Creates a `source-repo-subset/` layout inside the output directory that preserves the repository directory structure, so the bundle manifest's relative paths resolve correctly and the Ed25519 signature remains valid over the original raw bytes.
3. Copies Bronze demo content (claims, evidence, docs, bundle manifest), Silver runtime artifacts (assertion, trust policy, revocation list), schemas, and reference tools.
4. Generates a `package-manifest.yaml` describing the package contents and paths.
5. Excludes private keys, public keys, verification reports, Python caches, and other non-essential files.

The `--force` flag overwrites an existing output directory.

Exit codes: 0 (success), 1 (output exists without `--force`), 2 (usage error or missing source artifacts).

### Independent Verifier Demo

The independent verifier (`demos/silver-demo-002-independent-verifier/verifier/independent_verify.py`) operates on the exported package and performs all seven Silver checks without importing or invoking any tools from the main ProofRail source tree. See `demos/silver-demo-002-independent-verifier/README.md` for details.

## Silver Profile Conformance Validator

Validates whether a Silver verification result satisfies the Silver Relying-Party Profile v0.2.0 requirements.

Two profile modes are supported:

- `silver.base` — Validates a verification report from any conformant Silver verifier.
- `silver.independent` — Validates a verification report from an independent verifier, additionally requiring a valid package manifest.

```bash
# silver.base — requires only a verification report
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.base \
  --verification-report demos/silver-demo-001/runtime/verification-report.json \
  --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.0.json

# silver.independent — requires verification report + package manifest
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.independent \
  --verification-report <independent-report.json> \
  --package-manifest <package-manifest.yaml> \
  --output <conformance-report.json>
```

The validator performs six conformance checks:

1. **verification_report_valid** — Report passes structural validation (Silver Verification Report v0.1.0).
2. **decision_passed** — Report decision is `pass` with reason `all_checks_passed`.
3. **required_checks_passed** — All six core verification checks passed (trust, algorithm, validity, bundle manifest checksum, signature, underlying bundle).
4. **revocation_requirement** — Revocation check meets mode-dependent requirements:
   - `silver.base`: Revocation not performed → pass with warning and distinct reason code `profile_requirements_satisfied_with_revocation_warning`. Revocation performed and passed → clean pass. Revocation performed and failed → fail.
   - `silver.independent`: Revocation must be performed and must pass.
5. **independent_package_manifest_valid** — Package manifest is structurally valid with correct type and verifier metadata (`silver.independent` only; `not_applicable` for `silver.base`).
6. **limitations_present** — Report includes a non-empty limitations list.

The validator emits a profile conformance report conforming to `schemas/silver-profile-conformance-report-v0.2.0.md`.

### Profile Failure Reason Codes

| Reason | Status | Description |
|---|---|---|
| `profile_requirements_satisfied` | pass | All requirements met (clean pass) |
| `profile_requirements_satisfied_with_revocation_warning` | pass | All requirements met but revocation not performed (silver.base only) |
| `verification_report_invalid` | fail | Report failed structural validation |
| `verification_report_failed` | fail | Report decision is not pass/all_checks_passed |
| `required_check_failed` | fail | One or more required verification checks did not pass |
| `revocation_not_performed` | fail | Revocation check required but not performed (silver.independent) |
| `package_manifest_missing` | fail | Package manifest required but not supplied or not found |
| `independence_requirement_failed` | fail | Package manifest or verifier identity check failed |
| `limitations_missing` | fail | Report limitations list is missing or empty |

Exit codes: 0 (pass), 1 (fail), 2 (usage error).

## Silver Profile Conformance Validator v0.2.1

Validates whether a Silver verification result satisfies the Silver Relying-Party Profile v0.2.1 requirements.

Three profile modes are supported:

- `silver.base` — Validates a verification report from any conformant Silver verifier. Revocation must be performed and must pass.
- `silver.base.demo` — Preserves v0.2.0 `silver.base` semantics. Revocation not performed produces a conditional pass with warning.
- `silver.independent` — Validates a verification report from an independent verifier, additionally requiring a valid package manifest.

```bash
# silver.base — requires revocation
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report demos/silver-demo-001/runtime/verification-report.json \
  --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.1.json

# silver.base.demo — preserves v0.2.0 warning path
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base.demo \
  --verification-report demos/silver-demo-001/runtime/verification-report.json \
  --output <conformance-report.json>

# silver.independent — requires verification report + package manifest
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.independent \
  --verification-report <independent-report.json> \
  --package-manifest <package-manifest.yaml> \
  --output <conformance-report.json>
```

The validator emits a profile conformance report conforming to `schemas/silver-profile-conformance-report-v0.2.1.md`.

Exit codes: 0 (pass), 1 (fail), 2 (usage error).

## Independent Verification Package Export v0.2.1

Exports a portable verification package with enhanced manifest metadata.

```bash
python3 tools/silver/export_independent_verification_package_v0_2_1.py \
  --bronze-root demos/composed-bronze-demo-001 \
  --silver-root demos/silver-demo-001 \
  --output demos/silver-demo-002-independent-verifier/runtime/package \
  --force
```

The v0.2.1 exporter adds `package_format_version`, `profile_compatibility`, `inputs`, and `path_map` fields to the package manifest. All existing fields are preserved. The independent verifier requires no changes.

See `docs/silver/independent-verification-package-format-v0.2.1.md` for the package format specification.

Exit codes: 0 (success), 1 (output exists without `--force`), 2 (usage error or missing source artifacts).

## Demo Verifier Attestor Key Generator

Generates a demo Ed25519 attestor keypair and an attestation trust policy for verifier output attestations. The attestor key is separate from the issuer key used for Silver Signed Bundle Assertions.

```bash
python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
  --output-root demos/silver-demo-001/runtime/verifier-b \
  --attestor-id proofrail-demo-verifier-b \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --force
```

Generated files (runtime-only, not committed):

```
<output-root>/attestor-private-key.pem
<output-root>/attestor-public-key.pem
<output-root>/attestation-trust-policy.yaml
```

The same tool generates attestor keys for any verifier identity (e.g., `proofrail-demo-verifier-b` or `proofrail-demo-independent-verifier`).

The `--force` flag overwrites existing keys. Private keys are set to `0600` permissions.

Exit codes: 0 (success), 1 (output exists without `--force`), 2 (usage error).

## Verifier Output Attestation Signer

Signs a detached verifier output attestation binding a verifier's identity to its verification report and profile conformance report.

```bash
python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
  --verification-report demos/silver-demo-001/runtime/verification-report.json \
  --conformance-report demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.1.json \
  --private-key demos/silver-demo-001/runtime/verifier-b/attestor-private-key.pem \
  --attestor-id proofrail-demo-verifier-b \
  --attestor-version v0.2.2-demo \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --output demos/silver-demo-001/runtime/silver-verifier-output-attestation-v0.1.0.json
```

For `silver.independent` mode, add `--package-manifest <path>`.

The signer:

1. Validates verification report version and type.
2. Validates conformance report version, type, and profile mode.
3. Confirms `--attestor-id` matches `verifier_id` in the verification report.
4. Rejects subject paths containing `..` components.
5. Computes SHA-256 of each subject file.
6. Copies `profile` and `decision` from the conformance report.
7. Signs the canonical JSON of the `signed_payload` with Ed25519.
8. Writes attestation JSON with binding constraint: `signature.key_id == signed_payload.attestor.key_id`.

The signer does not require `decision.status == "pass"` — it attests both pass and fail reports.

Exit codes: 0 (success), 1 (signing/validation failure), 2 (usage/input error).

## Verifier Output Attestation Verifier

Verifies a Silver Verifier Output Attestation against an attestation trust policy.

```bash
python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation demos/silver-demo-001/runtime/silver-verifier-output-attestation-v0.1.0.json \
  --trust-policy demos/silver-demo-001/runtime/verifier-b/attestation-trust-policy.yaml
```

The verifier checks:

1. Attestation structure and version.
2. Binding: `signature.key_id == signed_payload.attestor.key_id` and `signature.algorithm == signed_payload.attestor.signature_algorithm`.
3. Attestor trust via attestation trust policy (type `proofrail.silver.verifier_attestation_trust_policy`).
4. Algorithm is Ed25519.
5. Public key loaded from `public_key_path` (relative to trust policy file).
6. Ed25519 signature over canonical JSON of `signed_payload`.
7. Subject paths do not contain `..` components.
8. SHA-256 of all subject files matches attested hashes.
9. Verification report metadata (verifier identity, report version/type).
10. Conformance report metadata (profile, decision, version/type).
11. If `silver.independent`: package manifest file integrity and metadata.
12. Limitations present and non-empty.

### Attestation Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_attestation_structure` | Top-level structure invalid or binding mismatch |
| `invalid_trust_policy` | Trust policy type/version invalid |
| `attestor_not_trusted` | Attestor ID not in trust policy |
| `key_id_not_trusted` | Key ID not found for attestor |
| `unsupported_algorithm` | Algorithm is not ed25519 |
| `signature_verification_failed` | Ed25519 signature invalid |
| `subject_hash_mismatch` | File hash differs from attested hash |
| `subject_file_missing` | Attested file not found |
| `subject_path_traversal` | Subject path contains `..` component |
| `package_manifest_mismatch` | Package manifest metadata mismatch |
| `attestor_verifier_identity_mismatch` | attestor_id != verifier_id |
| `attested_metadata_mismatch` | Signed metadata differs from file content |
| `limitations_missing` | Limitations empty or absent |

Exit codes: 0 (pass), 1 (fail), 2 (usage error).

## Multi-Principal Authority Fixture Validator

Validates the structural integrity of a Silver Multi-Principal Authority Fixture v0.1.0.

```bash
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml
```

The validator checks:

1. Required top-level fields and type/version.
2. Canonical principals present (`buyerorg.agent`, `vendororg.agent`, `verifier.auditor`).
3. Canonical protected actions present (`payment.release`, `vendor.approve`, `data.export`, `deploy.change`).
4. Grant ID uniqueness.
5. Principal references resolve.
6. Scope references resolve to known protected actions.
7. Delegated grant parent exists.
8. Parent grant permits delegation.
9. Delegated scopes are subset of parent.
10. Delegated constraints do not weaken parent (numeric <=, lists subset).
11. Revocation targets reference existing grants.
12. Limitations present and non-empty.

### Fixture Validation Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_fixture_structure` | Missing required top-level fields or wrong type/version |
| `missing_canonical_principal` | Required canonical principal absent |
| `missing_protected_action` | Required canonical action absent |
| `duplicate_grant_id` | Non-unique grant ID |
| `unknown_principal_reference` | Grant references non-existent principal |
| `unknown_scope_reference` | Grant scope not in protected_actions |
| `unknown_parent_grant` | Delegated grant parent doesn't exist |
| `delegation_not_permitted` | Parent grant has delegation.permitted == false |
| `delegation_scope_expanded` | Delegated scopes not subset of parent |
| `delegation_constraints_weakened` | Delegated constraint exceeds parent |
| `unknown_revocation_target` | Revocation references non-existent grant |
| `limitations_missing` | Limitations empty or absent |

Exit codes: 0 (valid), 1 (invalid), 2 (usage/input error).

## Authority Evaluator

Evaluates a protected action request against a multi-principal authority fixture, producing a decision report.

```bash
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --request fixtures/silver-multi-principal-authority-v0.2.3/requests/allow-payment-release-direct.json \
  --decision-time 2026-06-21T10:00:00Z \
  --output /tmp/decision-report.json
```

The evaluator performs 10 ordered checks (short-circuit on first deny):

1. **request_structure** — Valid request format.
2. **principal_known** — Principal exists in fixture.
3. **action_known** — Action exists in fixture.
4. **grant_exists** — Claimed grant exists.
5. **grant_subject_match** — Grant subject == requesting principal.
6. **delegation_chain_valid** — Chain from grant to root is valid.
7. **grant_not_revoked** — No applicable revocation at decision time.
8. **grant_not_expired** — All grants in chain within validity period.
9. **scope_authorized** — Action scope in grant scopes.
10. **constraints_satisfied** — Request parameters satisfy all constraints.

### Authority Deny Reason Codes

| Reason | Description |
|---|---|
| `authority_requirements_satisfied` | All checks passed (allow) |
| `invalid_request_structure` | Request type/version/fields malformed |
| `unknown_principal` | Principal not in fixture |
| `unknown_protected_action` | Action not in fixture |
| `unknown_authority_grant` | Grant ID not in fixture |
| `authority_subject_mismatch` | Grant subject != requesting principal |
| `delegation_chain_invalid` | Delegation chain broken or cyclic |
| `delegation_not_permitted` | Parent grant disallows delegation |
| `authority_revoked` | Grant or chain member revoked at decision time |
| `authority_expired` | Grant or chain member expired at decision time |
| `scope_not_authorized` | Action scope not in grant scopes |
| `constraint_not_satisfied` | Request parameter violates constraint |
| `constraint_value_missing` | Required request parameter absent |

Every decision report includes `"execution": { "performed": false, "reason": "decision_report_only" }` confirming no protected action was executed.

Exit codes: 0 (decision report produced — both allow and deny), 1 (evaluation failure), 2 (usage/input error).

## Security Notes

- This is a demo signing system. Do not use generated keys for production.
- Private keys are runtime-only and must not be committed to version control.
- Revocation is local demo revocation — local relying-party policy, not production PKI revocation, public certificate revocation, OCSP, or transparency-log-backed revocation.
- This is Minimal Silver, not full Silver governance.
