# ProofRail Silver Tools

This directory contains tooling for ProofRail Minimal Silver signed bundle assertions.

## Current supported schemas

- Silver Signed Bundle Assertion v0.1.0
- Silver Revocation List v0.1.0
- Silver Verification Report v0.1.0

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

## Security Notes

- This is a demo signing system. Do not use generated keys for production.
- Private keys are runtime-only and must not be committed to version control.
- Revocation is local demo revocation — local relying-party policy, not production PKI revocation, public certificate revocation, OCSP, or transparency-log-backed revocation.
- This is Minimal Silver, not full Silver governance.
