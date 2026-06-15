# Independent Silver Verifier

A standalone verifier that operates on a portable ProofRail Silver verification package without importing or invoking any tools from the main ProofRail source tree.

## Usage

```bash
python3 demos/silver-demo-002-independent-verifier/verifier/independent_verify.py \
  --package <package-dir> \
  [--report <report.json>]
```

## Inputs

The verifier reads a portable verification package directory containing:

- `package-manifest.yaml` — Package manifest with paths to all verification inputs.
- Signed Silver assertion YAML.
- Trust policy YAML.
- Revocation list YAML (optional).
- Bronze evidence bundle manifest YAML (original raw bytes, signature-preserving).
- Bronze package files (claims, evidence, docs).

The `--package` argument points to the root of the verification package. All paths are resolved from the `paths` block in `package-manifest.yaml`.

## Report Output

When `--report` is supplied, the verifier writes a Silver Verification Report v0.1.0-compatible JSON file. The report includes:

- Report metadata (`report_version`, `report_type`, `report_id`, `generated_at`, `generated_by`).
- Verifier identity (`proofrail-demo-independent-verifier`).
- Structured inputs (assertion path, trust policy, revocation list, roots).
- Assertion, issuer, and subject metadata.
- Decision block with `status` and stable snake_case `reason` code.
- Seven check blocks (all always present; unreached checks have `status: "not_performed"`).
- Limitations list.

The report can be validated with:

```bash
python3 tools/silver/validate_silver_verification_report_v0_1_0.py <report.json>
```

## Checks Performed

1. **Trust check** — Issuer ID and key ID are listed in the trust policy.
2. **Algorithm check** — Signature algorithm is Ed25519.
3. **Validity check** — Assertion has not expired and is not pre-dated.
4. **Bundle manifest checksum check** — SHA-256 of the raw bundle manifest bytes matches the assertion.
5. **Revocation check** — Assertion ID, issuer key, and bundle hash are not on the revocation list.
6. **Signature check** — Ed25519 signature over the raw bundle manifest bytes is valid.
7. **Underlying bundle check** — Every file listed in the bundle manifest exists and has matching SHA-256 and size.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Verification passed |
| 1 | Verification failed |
| 2 | Usage or configuration error |

## Dependencies

- Python 3.10+
- PyYAML
- cryptography (for Ed25519 signature verification)

## Limitations

- Local demo verification only.
- Independent verifier demo — not production.
- Not production PKI.
- Not third-party certification.
- Not Gold certification.
