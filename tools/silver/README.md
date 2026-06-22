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
- Silver Multi-Agent Harness Script v0.1.0
- Silver Multi-Agent Harness Run Report v0.1.0
- Silver Multi-Agent Harness Evidence Manifest v0.1.0
- Silver Multi-Agent Demo Package Manifest v0.1.0
- Silver Multi-Agent Demo Summary v0.1.0
- Silver Evidence Source Adapter Descriptor v0.1.0
- Silver Simulated Gateway Evidence Event v0.1.0
- Silver Composed Gateway Evidence Report v0.1.0
- Silver Composed Gateway Evidence Manifest v0.1.0

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

## Multi-Agent Attack Harness Runner

Runs a deterministic, scripted multi-principal agent attack harness against the v0.2.3 authority fixture. Produces a transcript, per-event protected action requests and decision reports, a structured run report, and a SHA-256 evidence manifest. No protected actions are executed.

```bash
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
  --script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --output-dir /tmp/proofrail-silver-multi-agent-harness-v0.2.4 \
  --force
```

The runner:

1. Validates harness script structure (type, version, non-empty unique events).
2. Copies the script and authority fixture into the output directory before hashing (no `..` in manifest paths).
3. For each event:
   - `agent_message` — recorded in transcript only (no evaluator call).
   - `protected_action_attempt` — renders a Silver Protected Action Request v0.1.0, evaluates it against the v0.2.3 fixture via the existing `evaluate_request` callable, writes the request and decision report, records the outcome in the transcript.
   - `bypass_attempt` — recorded in transcript as `bypass_blocked` with reason `bypass_attempt_detected`. No evaluator call, no request file, no decision report.
   - `revocation_marker` — recorded in transcript as `revocation_marked`. The fixture file is not mutated; the decision time on the next event drives revocation semantics.
4. Compares actual outcomes to expected outcomes from each event's `expected:` block.
5. Emits `expected-outcomes.json` as a derived runtime artifact (the canonical oracle is the script's `expected:` blocks).
6. Writes `harness-run-report.json` with `execution.protected_actions_performed: false`.
7. Writes `harness-evidence-manifest.json` with deterministic subject ordering: script → fixture → expected outcomes → transcript → protected action requests (sorted) → decision reports (sorted) → run report.

Exit codes: 0 (all events matched expected outcomes), 1 (one or more mismatches), 2 (usage/input error).

## Multi-Agent Harness Evidence Verifier

Verifies a multi-agent harness evidence manifest by parsing the manifest, rejecting subject paths containing `..`, recomputing SHA-256 of every subject, and validating the run report and each decision report.

```bash
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py \
  --manifest /tmp/proofrail-silver-multi-agent-harness-v0.2.4/harness-evidence-manifest.json
```

The verifier checks:

1. Manifest type, version, hash algorithm, non-empty subjects, non-empty limitations.
2. No subject path contains `..` and no subject path is absolute.
3. Every subject file exists.
4. Recomputed SHA-256 matches the recorded hash for every subject.
5. Run report subject: `report_type`, `report_version`, `summary.status == "pass"`, `execution.protected_actions_performed is false`.
6. Each decision report subject: `report_type`, `execution.performed is false`.

### Harness Evidence Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_evidence_manifest` | Missing required fields or wrong type/version |
| `subject_path_traversal` | Subject path contains `..` or is absolute |
| `subject_file_missing` | Subject file not found |
| `subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `harness_run_failed` | Run report version, type, or summary status invalid |
| `execution_violation` | Run or decision report indicates a protected action was performed |
| `decision_report_invalid` | Decision report version/type invalid or unparseable |

Exit codes: 0 (evidence valid), 1 (evidence invalid), 2 (usage/input error).

## Multi-Agent Trust-Boundary Demo Packager (v0.2.5)

Packages the v0.2.4 multi-agent attack harness evidence into a local Silver multi-agent trust-boundary demo. The packager invokes the unchanged v0.2.4 harness runner and verifier as subprocesses, derives eight required claims from the nested run report and transcript, and emits a SHA-256 package manifest plus a demo summary.

```bash
python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py \
  --demo-root demos/silver-demo-003-multi-agent-trust-boundary \
  --harness-script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
  --output-dir /tmp/proofrail-silver-multi-agent-demo-v0.2.5 \
  --force
```

The packager:

1. Invokes the v0.2.4 harness runner against the v0.2.4 harness script and v0.2.3 fixture.
2. Invokes the v0.2.4 evidence verifier on the nested manifest.
3. Copies the committed demo `README.md` and `demo-walkthrough.md` into the package root.
4. Derives the eight required claims deterministically from the run report and transcript:
   - `harmless_messages_proceed`
   - `protected_actions_require_scoped_authority`
   - `unauthorized_delegation_fails`
   - `bypass_attempts_blocked`
   - `revoked_authority_fails`
   - `out_of_scope_actions_fail`
   - `evidence_is_hash_verifiable`
   - `no_protected_actions_executed`
5. Writes `demo-summary.json` (Silver Multi-Agent Demo Summary v0.1.0).
6. Writes `demo-package-manifest.json` (Silver Multi-Agent Demo Package Manifest v0.1.0) with four subjects in deterministic order: `demo_readme` → `demo_walkthrough` → `demo_summary` → `nested_harness_evidence_manifest`.

The `--generated-at` flag (ISO-8601) makes the manifest deterministic across runs. The `--force` flag overwrites an existing output directory.

Exit codes: 0 (package valid), 1 (packaging failure), 2 (usage/input error).

## Multi-Agent Trust-Boundary Demo Verifier (v0.2.5)

Verifies a Silver multi-agent trust-boundary demo package. The verifier parses the package manifest, recomputes SHA-256 for every package subject, validates the demo summary structure, cross-checks every claim against the nested run report and decision reports, and delegates nested evidence verification to the unchanged v0.2.4 verifier.

```bash
python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \
  --package-manifest /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json
```

Verification ordering (hash-first, then parse, then semantic cross-check, then nested):

1. Manifest structure (type, version, hash algorithm, subjects, limitations).
2. Path safety (no `..`, no absolute paths).
3. SHA-256 recomputation for every package subject.
4. Demo summary structural validation against Silver Multi-Agent Demo Summary v0.1.0.
5. Claim cross-checks against nested run report and decision reports.
6. Nested v0.2.4 evidence verification via subprocess.

### Demo Package Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_demo_package_manifest` | Missing required fields, wrong type/version, or malformed manifest JSON |
| `demo_subject_path_traversal` | Subject path contains `..` or is absolute |
| `demo_subject_file_missing` | Subject file not found |
| `demo_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `invalid_demo_summary` | Demo summary structure invalid or malformed JSON |
| `demo_execution_violation` | Demo summary indicates a protected action was performed |
| `demo_claim_missing` | One or more of the eight required claim IDs absent |
| `demo_claim_failed` | A required claim status is not `pass` |
| `demo_evidence_ref_invalid` | A claim's evidence reference does not satisfy the claim's derivation rule against nested evidence, or contains `..`/absolute path |
| `nested_harness_evidence_invalid` | Nested v0.2.4 verifier reported a failure (nested reason included as context, top-level reason stable) |

JSON parse errors on `demo-summary.json` are caught and surfaced as `invalid_demo_summary` — no Python traceback leaks. Nested verifier failures are surfaced as the stable top-level reason `nested_harness_evidence_invalid` with the underlying nested context included as a detail string (e.g., `subject_hash_mismatch`).

Exit codes: 0 (package valid), 1 (package invalid), 2 (usage/input error).

## Evidence Source Adapter Validator (v0.2.6)

Validates a Silver Evidence Source Adapter descriptor or a directory of descriptors. Pure-stdlib (no PyYAML, no cryptography). Operates only on the parsed JSON; reads no external logs, fetches no URLs, calls no vendor APIs, and makes no trust decisions.

```bash
# Validate a single descriptor
python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py \
  --adapter examples/silver-evidence-source-adapters/native-proofrail-v0.2.6.json

# Validate a directory of descriptors (with duplicate adapter_id detection)
python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py \
  --examples-dir examples/silver-evidence-source-adapters
```

Validation rules:

1. Top-level shape: required fields, `document_type`, `schema_version`, `proofrail_release`, `adapter_id` matches `^[a-z0-9][a-z0-9._-]*$`.
2. `source.source_type` must be one of: `native_proofrail`, `gateway`, `observability_trace`, `siem_log`, `policy_engine`, `grc_platform`.
3. `trust_boundary.source_is_trust_authority` must be exactly `false`; `proofrail_role` must equal `evidence_source`.
4. `control_surface` block fields present and non-empty (boolean for `controlled_path_required`).
5. `protected_action_mapping` has non-empty `protected_action_ids` (dotted identifiers) and non-empty source field strings.
6. All six required evidence capabilities present with `status` ∈ {`provided`, `not_provided`, `not_applicable`}; `provided` requires non-empty `description`; non-provided requires non-empty `limitation`.
7. `decision_event` must be `provided` and carry all five mapping fields (`event_type`, `timestamp_field`, `decision_field`, `reason_field`, `source_record_id_field`).
8. `normalization` carries a non-empty `normalized_event_type` and a non-empty `normalization_notes` list (no empty/whitespace-only entries).
9. `adapter_limitations` and `non_claims` are non-empty lists of non-empty/non-whitespace strings.
10. Optional `sample_artifact_refs[i].path` rejected if absolute or containing `..`.
11. Directory mode rejects two descriptors sharing the same `adapter_id`.

### Adapter Validator Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_adapter_descriptor` | Top-level shape error, missing required field, bad `adapter_id`, malformed JSON, etc. |
| `invalid_source_type` | `source.source_type` not in the v0.2.6 closed set |
| `source_marked_as_trust_authority` | `trust_boundary.source_is_trust_authority` is not exactly `false` |
| `control_surface_missing` | `control_surface` block missing or has missing/empty/wrong-typed fields |
| `protected_action_mapping_missing` | `protected_action_mapping` block missing or has empty / malformed protected action IDs / missing source fields |
| `evidence_capability_missing` | A required capability missing, has an unknown status, or lacks the required `description`/`limitation` |
| `decision_event_mapping_missing` | `decision_event` not `provided`, or its required mapping fields are absent/empty |
| `normalization_notes_missing` | `normalization` block missing, or `normalization_notes` empty / has empty entries |
| `adapter_limitations_missing` | `adapter_limitations` empty or has empty / whitespace-only entries |
| `adapter_non_claims_missing` | `non_claims` empty or has empty / whitespace-only entries |
| `evidence_artifact_path_traversal` | `sample_artifact_refs[i].path` is absolute or contains `..` |
| `duplicate_adapter_id` | Two descriptors in the same directory share an `adapter_id` |

JSON parse errors are caught and surfaced as `invalid_adapter_descriptor` — no Python traceback leaks.

Exit codes: 0 (valid), 1 (validation failure), 2 (usage / input-file error).

## Composed Gateway Evidence Composer (v0.2.7)

Composes a Silver evidence package from a v0.2.6 simulated gateway adapter descriptor and a static JSONL gateway event fixture. Pure-stdlib. Subprocess-invokes the unchanged v0.2.6 adapter validator. Does not integrate with any real gateway and does not execute any protected action.

```bash
python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
  --demo-root demos/silver-demo-004-composed-gateway-evidence \
  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
  --generated-at 2026-06-22T00:00:00Z \
  --force
```

The composer:

1. Refuses to overwrite a non-empty `--output-dir` unless `--force` is supplied.
2. Re-validates the adapter descriptor via the unchanged v0.2.6 validator (subprocess).
3. Confirms `source.source_type == "gateway"` and `trust_boundary.source_is_trust_authority == false`.
4. Parses the JSONL events line-by-line, validates each line against the simulated gateway event schema (cross-field consistency for bypass and revocation events included), and confirms exactly one event per required `scenario_event_id`.
5. Confirms every `protected_action_id` is within the adapter's `protected_action_mapping.protected_action_ids` (or `null` for `gateway.message_observed`).
6. Confirms every event has `execution.performed == false`.
7. Copies `README.md`, `demo-walkthrough.md`, the adapter descriptor (under `adapter/`), and the JSONL fixture (under `source/`) into the output directory.
8. Derives the ten required claims, writes `composed-gateway-evidence-report.json`.
9. Writes `composed-gateway-evidence-manifest.json` with five subjects in deterministic order and a `composition` block.

Exit codes: 0 (success), 1 (composition failure), 2 (usage/input error).

## Composed Gateway Evidence Verifier (v0.2.7)

Verifies a composed gateway evidence package. Pure-stdlib. Re-derives every required claim independently from the copied adapter and JSONL events; does not trust the composed report alone.

```bash
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \
  --manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json
```

Verification ordering (hash-first):

1. Parse manifest: shape, document type, version, hash algorithm, subject count and order, `composition` block.
2. Reject subject paths containing `..` or starting with `/`.
3. Reject missing subjects.
4. Recompute SHA-256 for every subject.
5. Re-validate the copied adapter via the unchanged v0.2.6 validator (subprocess); confirm `source_type == "gateway"`.
6. Re-parse the JSONL events: reject malformed lines, empty file, duplicates, out-of-scope `protected_action_id`, unknown decisions, inconsistent bypass/revocation events.
7. Load the report: reject shape errors, missing required claim IDs, wrong evidence-ref paths, wrong-but-valid evidence refs, and any claim whose composer-reported status disagrees with the independently re-derived status.
8. Reject any event with `execution.performed == true`, and any report with `execution.protected_actions_performed != false`.

### Composed Gateway Verifier Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_composed_gateway_manifest` | Manifest shape, type, version, hash algorithm, subjects, or `composition` block invalid |
| `composed_subject_file_missing` | A manifest subject file is missing |
| `composed_subject_path_traversal` | A subject path contains `..` or is absolute |
| `composed_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `adapter_invalid` | Copied adapter fails v0.2.6 validation |
| `adapter_not_gateway_source` | Copied adapter `source_type` is not `gateway` |
| `source_event_invalid` | A JSONL line is malformed or fails schema/cross-field checks (no Python traceback leaks) |
| `source_event_missing` | A required `scenario_event_id` is missing or the JSONL file is empty |
| `source_event_duplicate` | A `scenario_event_id` appears more than once |
| `gateway_protected_action_mismatch` | A source event references an unsupported `protected_action_id` for the adapter |
| `gateway_decision_mismatch` | A source event decision does not match its expected scenario decision |
| `gateway_bypass_mismatch` | A bypass event has inconsistent fields (e.g., `bypass_detected == false`) |
| `gateway_revocation_mismatch` | A revocation event has inconsistent fields (e.g., `revocation_checked == false`) |
| `normalized_report_invalid` | Report shape, type, or version invalid |
| `normalized_claim_missing` | A required claim ID is missing from the report |
| `normalized_claim_failed` | A required claim's re-derived status is not `pass`, or composer status disagrees with re-derived status |
| `normalized_evidence_ref_invalid` | A claim's evidence reference contains `..`, is absolute, or points at a wrong-but-valid event |
| `execution_violation` | A source event has `execution.performed == true`, or the report has `execution.protected_actions_performed != false` |

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (validation failure), 2 (usage/input error).

## Relying-Party Acceptance Record Generator (v0.2.8)

Generates a local, hash-anchored relying-party acceptance record over a verified v0.2.7 composed gateway evidence package. Pure-stdlib. Subprocess-invokes the unchanged v0.2.7 verifier. Does not sign the record, does not contact any real relying party, and does not execute any protected action.

```bash
python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py \
  --policy fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json \
  --evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at 2026-06-22T00:00:00Z \
  --challenge-closes-at 2026-07-22T00:00:00Z \
  --output-dir /tmp/proofrail-silver-relying-party-acceptance-v0.2.8 \
  --force
```

The generator:

1. Refuses to overwrite a non-empty `--output-dir` unless `--force` is supplied.
2. Validates ISO-8601 Z-suffixed `--generated-at`, `--challenge-closes-at`, and optional `--challenge-opens-at`.
3. Parses the acceptance policy and confirms `--decision` is in `policy.allowed_decisions` and `--purpose` is in `policy.allowed_purposes`.
4. Subprocess-invokes the v0.2.7 verifier on `--evidence-manifest` and captures pass/fail with first-line failure reason.
5. **Refusal:** for `--decision accepted` with a non-zero v0.2.7 verifier exit, prints `FAIL: evidence_verification_failed: <detail>` to stderr and exits **1** without writing any partial package.
6. Derives `revocation_review.outcome` from the sibling `composed-gateway-evidence-report.json`'s `revoked_authority_fails` claim status (`pass` → `no_revoked_authority_accepted`; `fail` or missing → `revoked_authority_rejected`).
7. Copies the policy and the evidence manifest into the output directory under their canonical paths (only the manifest is copied; the full v0.2.7 package remains external).
8. Emits `acceptance-record.json` with deterministic field shape.
9. Emits `acceptance-package-manifest.json` with three subjects in the fixed v0.2.8 order (`acceptance-policy.json`, `evidence/composed-gateway-evidence-manifest.json`, `acceptance-record.json`).
10. Optionally subprocess-invokes the v0.2.8 validator when `--self-validate` is supplied.

Exit codes: 0 (success), 1 (generation refused / self-validate failed), 2 (usage/input error).

## Relying-Party Acceptance Record Validator (v0.2.8)

Validates a v0.2.8 relying-party acceptance package. Pure-stdlib. Hash-first ordering. Optional `--evidence-package-root` re-invokes the v0.2.7 verifier against the original package.

```bash
python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py \
  --manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]
```

The validator runs 22 ordered checks and never emits the generator-only `evidence_verification_failed` code.

### Acceptance Validator Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_acceptance_package_manifest` | Manifest shape, type, version, hash algorithm, subject count/order/roles, or required limitations/non-claims invalid |
| `acceptance_subject_file_missing` | A manifest subject file is missing |
| `acceptance_subject_path_traversal` | A subject path contains `..` or is absolute |
| `acceptance_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `invalid_acceptance_policy` | Acceptance policy JSON malformed or fails structural checks (e.g., wrong `document_type`, missing `allowed_decisions` set) |
| `invalid_acceptance_record` | Acceptance record JSON malformed or fails structural checks (no Python traceback leaks) |
| `policy_mismatch` | Record's `relying_party.policy_id` or `policy_version` disagrees with the policy |
| `relying_party_mismatch` | Record's `relying_party.relying_party_id` disagrees with the policy |
| `purpose_not_allowed` | Record's `decision.purpose_id` is not in `policy.allowed_purposes` |
| `evidence_type_not_allowed` | Record's `evidence_package.evidence_type` is not in `policy.allowed_evidence_types` |
| `evidence_manifest_hash_mismatch` | Recomputed SHA-256 of copied evidence manifest disagrees with `record.evidence_package.manifest_sha256` |
| `evidence_verification_required` | Record's verifier metadata missing or disagrees with `policy.required_verification` |
| `accepted_record_verification_failed` | `decision.status == "accepted"` and `verification.verification_result` does not equal `policy.required_verification.required_result` |
| `accepted_record_has_blocking_exception` | `decision.status == "accepted"` but an exception with `severity == "blocking"` is present |
| `accepted_with_exceptions_missing_exception` | `decision.status == "accepted_with_exceptions"` but no exception with all three fields is present |
| `rejected_record_missing_reason` | `decision.status == "rejected"` but both `decision.rejection_reason` and `verification.failure_reason` are empty |
| `revocation_review_missing` | Policy mandates revocation review but `record.revocation_review.performed == false` or `outcome` is not in `policy.accepted_outcomes` |
| `challenge_window_invalid` | Policy mandates a challenge window but `opens_at >= closes_at` or span is outside `[minimum_days, maximum_days]` |
| `scope_limitations_missing` | `record.scope_limitations` is empty |
| `acceptance_non_claims_missing` | `record.non_claims` is empty |
| `external_evidence_verification_failed` | `--evidence-package-root` re-invocation of the v0.2.7 verifier fails, or the external manifest sha256 disagrees with `record.evidence_package.manifest_sha256` |

The generator-only code `evidence_verification_failed` is **never** emitted by the validator.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (validation failure), 2 (usage/input error).

## Revocation/Challenge Drill Runner (v0.2.9)

Stages a deterministic revocation/challenge drill over an existing v0.2.8 relying-party acceptance package. Pure-stdlib. Atomic staging-then-replace; a refused run leaves no partial drill package on disk.

```bash
python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
  --generated-at 2026-06-27T00:00:00Z \
  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
  --force \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7] \
  [--self-validate]
```

The runner:

1. Subprocess-invokes the unchanged v0.2.8 acceptance validator on `--acceptance-manifest` and **refuses** with `FAIL: acceptance_package_validation_failed: <detail>` and exit code 1 if validation fails.
2. Byte-copies the full v0.2.8 acceptance package subdirectory into `acceptance-package/` (never mutates the source package).
3. Parses the JSONL review-events fixture line-by-line and **refuses** with `FAIL: review_fixture_insufficient: <detail>` and exit code 1 if the fixture contains zero within-window challenges or zero revocation signals.
4. Derives findings, review triggers, and a single `recommended_local_posture` from the closed set:
   - `acceptance_stands_for_demo_scope`
   - `acceptance_requires_review_before_reuse`
   - `acceptance_not_reusable_without_governed_review`
5. Emits `review-events.jsonl`, `revocation-challenge-drill-report.json`, and `revocation-challenge-drill-manifest.json` with three subjects in fixed order (roles `nested_acceptance_package_manifest`, `review_events`, `revocation_challenge_drill_report`).
6. Optionally subprocess-invokes the v0.2.9 verifier when `--self-validate` is supplied.

`acceptance_package_validation_failed` and `review_fixture_insufficient` are **runner-only** codes and are never emitted by the verifier.

Exit codes: 0 (success), 1 (drill refused / self-validate failed), 2 (usage/input error).

## Revocation/Challenge Drill Verifier (v0.2.9)

Validates a v0.2.9 revocation/challenge drill package. Pure-stdlib. Hash-first ordering. Optional `--evidence-package-root` re-invokes the v0.2.7 verifier against the original composed gateway evidence package.

```bash
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \
  --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]
```

The verifier delegates nested acceptance-package validation to the unchanged v0.2.8 validator and re-derives the drill report's classification, findings, and triggers independently from the review events.

### Drill Verifier Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_drill_package_manifest` | Manifest shape, type, version, hash algorithm, or subject count/order/roles invalid |
| `drill_subject_file_missing` | A manifest subject file is missing |
| `drill_subject_path_traversal` | A subject path contains `..` or is absolute |
| `drill_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `nested_acceptance_package_invalid` | Subprocess invocation of the v0.2.8 validator on the nested acceptance package fails |
| `invalid_review_events` | Review-events JSONL malformed, missing required fields, wrong document type/version, or has an out-of-set event type |
| `invalid_drill_report` | Drill report JSON malformed or fails shape checks (e.g., wrong `document_type`, missing required fields, invalid posture set members) |
| `acceptance_record_binding_mismatch` | Drill report's `base_acceptance.*` block disagrees with the nested v0.2.8 record, policy, or recomputed package manifest sha256 |
| `review_events_hash_mismatch` | Recomputed SHA-256 of `review-events.jsonl` disagrees with `drill_report.review_events.events_sha256` |
| `review_event_target_mismatch` | Non-revocation review event references an acceptance record / purpose other than the bound one |
| `review_event_sequence_invalid` | Review events are not monotonic in `event_time` |
| `challenge_window_missing` | Drill report omits the policy-derived challenge window when at least one `challenge.received` event is present |
| `challenge_within_window_missing` | At least one `challenge.received` event exists in the window but no `challenge_within_window` finding/trigger is recorded |
| `challenge_window_classification_mismatch` | A `challenge_within_window` finding/trigger references an event that is outside the policy challenge window, or vice-versa |
| `revocation_signal_missing` | Zero `revocation.signal_received` events in the fixture |
| `revocation_signal_target_mismatch` | A `revocation.signal_received` event references an acceptance record / purpose other than the bound one |
| `required_finding_missing` | A required finding type derived from the events is missing from the report |
| `required_review_trigger_missing` | A required review trigger type derived from the events is missing from the report |
| `recommended_posture_invalid` | `recommended_local_posture` is not in the closed set |
| `scope_limitations_missing` | `drill_report.scope_limitations` is empty |
| `drill_non_claims_missing` | `drill_report.non_claims` is empty |
| `external_evidence_verification_failed` | `--evidence-package-root` re-invocation of the v0.2.7 verifier fails on the original composed gateway evidence package |

The runner-only codes `acceptance_package_validation_failed` and `review_fixture_insufficient` are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Security Notes

- This is a demo signing system. Do not use generated keys for production.
- Private keys are runtime-only and must not be committed to version control.
- Revocation is local demo revocation — local relying-party policy, not production PKI revocation, public certificate revocation, OCSP, or transparency-log-backed revocation.
- This is Minimal Silver, not full Silver governance.
