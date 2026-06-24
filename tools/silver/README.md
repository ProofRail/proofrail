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
- Silver Relying-Party Acceptance Policy v0.1.0
- Silver Relying-Party Acceptance Record v0.1.0
- Silver Relying-Party Acceptance Package Manifest v0.1.0
- Silver Relying-Party Review Event v0.1.0
- Silver Revocation/Challenge Drill Report v0.1.0
- Silver Revocation/Challenge Drill Manifest v0.1.0
- Silver Acceptance Handoff Summary v0.1.0
- Silver Acceptance Handoff Manifest v0.1.0
- Silver-to-Gold Requirement Set v0.1.0
- Silver Handoff Inspection Report v0.1.0
- Silver Handoff Inspection Manifest v0.1.0

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

## Acceptance Handoff Runner (v0.3.0)

Builds a deterministic, hash-anchored portable Silver acceptance handoff package by composing an already-verified v0.2.7 composed gateway evidence package, a v0.2.8 relying-party acceptance package, and a v0.2.9 revocation/challenge drill package. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial handoff package on disk.

```bash
python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py \
  --composed-evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --drill-manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  --generated-at 2026-06-28T00:00:00Z \
  --output-dir /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
  [--handoff-id <id>] [--handoff-purpose <text>] [--recipient-role <text>] \
  [--source-package-family <text>] [--force] [--self-validate]
```

The runner:

1. Subprocess-invokes the unchanged **v0.2.7 verifier** on the composed-evidence manifest and refuses with `FAIL: composed_evidence_validation_failed: <detail>` and exit code 1 if verification fails.
2. Subprocess-invokes the unchanged **v0.2.8 acceptance validator** on the acceptance manifest WITHOUT `--evidence-package-root` and refuses with `FAIL: acceptance_package_validation_failed: <detail>` and exit code 1 if validation fails.
3. Subprocess-invokes the unchanged **v0.2.9 drill verifier** on the drill manifest WITHOUT `--evidence-package-root` and refuses with `FAIL: drill_package_validation_failed: <detail>` and exit code 1 if verification fails.
4. Byte-copies the three nested package roots into a sibling staging directory under the fixed top-level names `composed-gateway-evidence/`, `acceptance-package/`, and `revocation-challenge-drill/`.
5. Performs four v0.3.0-owned chain-binding cross-checks: (a) top-level composed-gateway-evidence manifest sha256 = nested v0.2.8 record `evidence_package.manifest_sha256`; (b) top-level acceptance-package manifest sha256 = nested v0.2.9 drill report `base_acceptance.acceptance_package_manifest_sha256`; (c) inner copy `acceptance-package/evidence/composed-gateway-evidence-manifest.json` sha256 = subject [0] sha256; (d) inner copy `revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json` sha256 = subject [1] sha256. Any mismatch yields `FAIL: handoff_chain_binding_failed: <detail>` and exit code 1.
6. Maps the nested v0.2.9 `recommended_local_posture` onto a minimum handoff posture rank (`acceptance_stands_for_demo_scope` → rank 0, `acceptance_requires_review_before_reuse` → rank 1, `acceptance_not_reusable_without_governed_review` → rank 2) and selects `recommended_handoff_posture` from the matching closed set.
7. Emits `silver-acceptance-handoff-summary.json` and `silver-acceptance-handoff-manifest.json` with four subjects in the fixed v0.3.0 order (composed-gateway-evidence manifest, acceptance-package manifest, drill manifest, handoff summary).
8. With `--self-validate`, subprocess-invokes the v0.3.0 handoff verifier on the staged manifest BEFORE the atomic move; on failure it removes the staging directory, leaves the destination untouched, and refuses with `FAIL: self_validation_failed: <detail>` and exit code 1.
9. Atomically moves the staging directory to `--output-dir`.

### Runner-Only Refusal Codes

| Reason | Description |
|---|---|
| `composed_evidence_validation_failed` | Subprocess invocation of the unchanged v0.2.7 verifier on the supplied composed-evidence manifest fails |
| `acceptance_package_validation_failed` | Subprocess invocation of the unchanged v0.2.8 acceptance validator on the supplied acceptance manifest fails |
| `drill_package_validation_failed` | Subprocess invocation of the unchanged v0.2.9 drill verifier on the supplied drill manifest fails |
| `handoff_chain_binding_failed` | One or more of the four v0.3.0-owned chain-binding cross-checks fails during runner-side preparation |
| `self_validation_failed` | `--self-validate` subprocess invocation of the v0.3.0 handoff verifier on the staged package fails before the atomic move |

These five runner-only refusal codes are deliberately distinct from the 17 verifier failure reasons. The verifier never emits any of these codes.

Exit codes: 0 (handoff package written), 1 (refusal — no partial output), 2 (usage/input error).

## Acceptance Handoff Verifier (v0.3.0)

Validates a v0.3.0 Silver acceptance handoff package. Pure-stdlib. Hash-first ordering. The verifier owns the four v0.3.0-specific chain-binding cross-checks and re-runs the unchanged v0.2.7 verifier, v0.2.8 acceptance validator, and v0.2.9 drill verifier as subprocesses, each WITHOUT `--evidence-package-root`.

```bash
python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py \
  --manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json
```

The verifier delegates nested package validation to the three unchanged subordinate validators and re-derives the four v0.3.0-owned chain-binding cross-checks, the posture-rank ordering, and the overclaim guard independently.

### Handoff Verifier Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_handoff_manifest` | Manifest shape, type, version, hash algorithm, or subject count/order/roles invalid |
| `handoff_subject_file_missing` | A manifest subject file is missing |
| `handoff_subject_path_traversal` | A subject path contains `..` or is absolute |
| `handoff_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `nested_composed_evidence_invalid` | Subprocess invocation of the unchanged v0.2.7 verifier on the nested composed-gateway-evidence manifest fails |
| `nested_acceptance_package_invalid` | Subprocess invocation of the unchanged v0.2.8 acceptance validator on the nested acceptance-package manifest fails |
| `nested_revocation_challenge_drill_invalid` | Subprocess invocation of the unchanged v0.2.9 drill verifier on the nested drill manifest fails |
| `handoff_summary_invalid` | `silver-acceptance-handoff-summary.json` malformed or fails shape checks (wrong `document_type`, missing required fields, etc.) |
| `handoff_summary_binding_mismatch` | Summary's recorded composed/acceptance/drill manifest sha256 fields disagree with the recomputed subject hashes, or summary's `recommended_local_posture` disagrees with the nested v0.2.9 drill report |
| `handoff_chain_binding_mismatch` | One or more of the four v0.3.0-owned cross-copy chain-binding checks (a)/(b)/(c)/(d) fails on the assembled package |
| `handoff_record_mismatch` | Summary's recorded v0.2.8 acceptance record id, decision status, policy id, or related binding fields disagree with the nested v0.2.8 record |
| `handoff_purpose_mismatch` | Summary's recorded purpose id disagrees with the nested v0.2.8 record's purpose id |
| `handoff_posture_invalid` | `recommended_handoff_posture` is not in the closed set, or the nested drill `recommended_local_posture` is not in its closed set |
| `handoff_posture_downgrade` | `recommended_handoff_posture` rank is lower (weaker) than the minimum rank implied by the nested v0.2.9 drill posture |
| `handoff_overclaim` | A forbidden positive overclaim token (e.g., `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `gold certified`, `production-approved`, `trust transferred`) appears in a summary string outside `scope_limitations` / `non_claims` |
| `handoff_limitations_missing` | `handoff_summary.scope_limitations` is empty |
| `handoff_non_claims_missing` | `handoff_summary.non_claims` is empty |

The five runner-only refusal codes (`composed_evidence_validation_failed`, `acceptance_package_validation_failed`, `drill_package_validation_failed`, `handoff_chain_binding_failed`, `self_validation_failed`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Silver Handoff Inspector Runner (v0.3.1)

Builds a deterministic, local Silver handoff inspection package over an already-verified v0.3.0 Silver acceptance handoff and a committed local Gold-boundary requirement set. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial inspection package on disk.

```bash
python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py \
  --handoff-manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json \
  --requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json \
  --generated-at 2026-06-29T00:00:00Z \
  --output-dir /tmp/proofrail-silver-handoff-inspection-v0.3.1 \
  [--inspection-id <id>] [--force] [--self-validate]
```

The runner:

1. Subprocess-invokes the unchanged **v0.3.0 handoff verifier** on `--handoff-manifest` and refuses with `FAIL: handoff_validation_failed: <detail>` and exit code 1 if verification fails.
2. Subprocess-invokes the **v0.3.1 verifier with `--validate-requirement-set`** on `--requirement-set` and refuses with `FAIL: requirement_set_validation_failed: <detail>` and exit code 1 if validation fails.
3. Byte-copies the v0.3.0 handoff package root into a sibling staging directory under the fixed top-level name `silver-acceptance-handoff/`, and byte-copies the requirement set fixture to `gold-boundary-requirements.json`.
4. Parses the nested v0.3.0 handoff summary and re-derives the four blocks of the inspection report:
   - `base_handoff` — bound handoff id and manifest sha256;
   - `handoff_summary` — `acceptance_record_id`, `decision_status`, `purpose_id`, `recommended_handoff_posture`, `reuse_warning`;
   - `component_inspection` — four rows for v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0, each `present_and_verified`;
   - `gold_gap_inventory` — recomputed counts and a `gold_boundary_status` forced to `gold_not_claimed` whenever any row is `silver_evidence_partial`, `gold_prerequisite_unmet`, or `out_of_scope_for_silver`.
5. Emits `silver-handoff-inspection-report.json` and `silver-handoff-inspection-manifest.json` with three subjects in the fixed v0.3.1 order (handoff manifest, requirement set, inspection report).
6. With `--self-validate`, subprocess-invokes the v0.3.1 verifier on the staged manifest BEFORE the atomic move; on failure it removes the staging directory, leaves the destination untouched, and refuses with `FAIL: inspection_self_validation_failed: <detail>` and exit code 1.
7. Atomically moves the staging directory to `--output-dir`.

### Runner-Only Refusal Codes

| Reason | Description |
|---|---|
| `handoff_validation_failed` | Subprocess invocation of the unchanged v0.3.0 handoff verifier on the supplied handoff manifest fails |
| `requirement_set_validation_failed` | Subprocess invocation of the v0.3.1 verifier with `--validate-requirement-set` on the supplied requirement set fails |
| `inspection_self_validation_failed` | `--self-validate` subprocess invocation of the v0.3.1 verifier on the staged package fails before the atomic move |

These three runner-only refusal codes are deliberately distinct from the 20 verifier failure reasons. The verifier never emits any of these codes.

Exit codes: 0 (inspection package written), 1 (refusal — no partial output), 2 (usage/input error).

## Silver Handoff Inspection Verifier (v0.3.1)

Validates a v0.3.1 Silver handoff inspection package. Pure-stdlib. Hash-first ordering. The verifier owns every cross-check of the inspection report against the nested v0.3.0 handoff summary and the bound Gold-boundary requirement set, and re-runs the unchanged **v0.3.0 handoff verifier** on the nested handoff manifest as a subprocess.

```bash
# Full inspection package verification
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \
  --manifest /tmp/proofrail-silver-handoff-inspection-v0.3.1/silver-handoff-inspection-manifest.json

# Requirement-set-only validation entry point (used by the runner)
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \
  --validate-requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json
```

The verifier:

1. Validates the inspection manifest shape: `document_type`, `schema_version`, `proofrail_release`, hash algorithm, exactly three subjects in the fixed order, non-empty limitations and non-claims (presence/type only at this stage).
2. Rejects subject paths containing `..` or starting with `/`.
3. Rejects missing subject files.
4. Recomputes SHA-256 for every subject and rejects any mismatch.
5. Subprocess-invokes the unchanged **v0.3.0 handoff verifier** on subject [0] and surfaces failure as the stable top-level reason `nested_handoff_invalid`.
6. Re-validates the requirement set bound at subject [1]: structural shape → duplicate id/domain detection → required-domain completeness check (all 13 domains) → recursive overclaim guard.
7. Validates the inspection report shape (presence/type only at this stage).
8. Cross-checks `base_handoff` binding against subject [0] sha256.
9. Reads the nested v0.3.0 handoff summary and runs the two-path summary cross-check:
   - non-posture summary fields (`acceptance_record_id`, `decision_status`, `purpose_id`) → `inspection_handoff_summary_mismatch`;
   - posture path (`recommended_handoff_posture` rank, `reuse_warning`) → `inspection_review_posture_downgrade` (reached independently even when non-posture cross-checks pass).
10. Cross-checks `component_inspection` rows (4 entries, each `present_and_verified`).
11. Cross-checks `gold_gap_inventory`: `requirements_sha256` matches subject [1], per-row id/domain/status matches, recomputed counts match, and `gold_boundary_status` is forced.
12. Runs a recursive overclaim guard over the inspection report (excluding `scope_limitations` and `non_claims`) against 18 forbidden positive tokens.
13. Re-checks emptiness of `scope_limitations` and `non_claims` for the manifest, requirement set, and inspection report (reachable even when early structural checks pass).

### Inspection Verifier Failure Reason Codes

| Reason | Description |
|---|---|
| `invalid_inspection_manifest` | Manifest shape, type, version, hash algorithm, or subject count/order/roles invalid |
| `inspection_subject_path_traversal` | A subject path contains `..` or is absolute |
| `inspection_subject_file_missing` | A manifest subject file is missing |
| `inspection_subject_hash_mismatch` | Recomputed SHA-256 differs from recorded hash |
| `inspection_limitations_missing` | `scope_limitations` empty or contains only whitespace entries in the manifest, requirement set, or inspection report |
| `inspection_non_claims_missing` | `non_claims` empty or contains only whitespace entries in the manifest, requirement set, or inspection report |
| `requirement_set_invalid` | Requirement set JSON malformed, wrong `document_type`, or contains a row with an unknown status |
| `requirement_duplicate` | Two requirement rows share an `id` or `domain` |
| `requirement_domain_missing` | One or more of the 13 required governance domains is absent from the requirement set |
| `inspection_report_invalid` | Inspection report JSON malformed or fails shape checks (no Python traceback leaks) |
| `inspection_report_binding_mismatch` | Report `base_handoff.handoff_manifest_sha256` disagrees with subject [0] sha256 |
| `inspection_handoff_summary_mismatch` | Non-posture summary field (`acceptance_record_id`, `decision_status`, or `purpose_id`) disagrees with the nested v0.3.0 summary |
| `inspection_review_posture_downgrade` | `recommended_handoff_posture` rank is weaker than the nested v0.3.0 summary's rank, OR `reuse_warning` is missing/blank when the nested rank is ≥ 1 |
| `inspection_component_status_mismatch` | A `component_inspection` row references the wrong component id or its `status` is not `present_and_verified` |
| `inspection_requirement_missing` | A row in `gold_gap_inventory.requirements` is missing relative to the bound requirement set |
| `inspection_requirement_status_mismatch` | A row's id, domain, or status disagrees with the bound requirement set |
| `inspection_count_mismatch` | `gold_gap_inventory.counts` disagrees with the recomputed per-status counts |
| `inspection_gold_status_invalid` | `gold_boundary_status` is not in the closed set `{gold_not_claimed, gold_gap_inventory_only}` |
| `inspection_gold_overclaim` | `gold_boundary_status` is `gold_gap_inventory_only` when at least one row is partial / unmet / out-of-scope (forced status mismatch), OR a forbidden positive overclaim token appears in a report string outside `scope_limitations` / `non_claims` |
| `nested_handoff_invalid` | Subprocess invocation of the unchanged v0.3.0 handoff verifier on subject [0] fails |

The three runner-only refusal codes (`handoff_validation_failed`, `requirement_set_validation_failed`, `inspection_self_validation_failed`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Silver Trace Binding Runner (v0.3.2)

Builds a deterministic, local Silver trace binding package that anchors a static fixture of trace events plus a binding set of expectations to an unchanged v0.2.6 observability-trace adapter descriptor. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial trace binding package on disk.

```bash
python3 tools/silver/build_silver_trace_binding_v0_1_0.py \
  --adapter examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json \
  --trace-events fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl \
  --bindings fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json \
  --trace-binding-report-id proofrail-trace-binding-report-demo-001 \
  --generated-at 2026-06-22T00:00:00Z \
  --output-dir /tmp/proofrail-silver-trace-binding-v0.3.2 \
  --force \
  --self-validate
```

The runner performs nine ordered steps:

1. Structural pre-check (Amendment 1): refuses if the adapter's `trust_boundary.source_is_trust_authority` is not exactly `false`. Surfaces as the runner-only refusal reason `adapter_validation_failed`.
2. Subprocess-invokes the unchanged **v0.2.6 adapter validator** on the supplied adapter (same runner-only reason on failure).
3. Validates the trace events JSONL: closed `decision` enum, unique `event_id`, unique `(trace_id, span_id)`, strict `(event_time, event_id)` ascending order. Surfaces as `trace_events_validation_failed`.
4. Validates the binding set JSON: closed `expected_binding_status` and `required_decision` enums, unique `claim_id`, time-window correctness, and the cross-check that every non-gap row resolves to an existing event with all `required_*` fields equal (Amendment 4). Surfaces as `trace_binding_set_validation_failed`.
5. Stages the package directory under a sibling staging path.
6. Derives `silver-trace-binding-report.json` deterministically; `binding_summary` counts are recomputed from `bindings[].binding_status` and may not be hand-authored.
7. Emits `silver-trace-binding-manifest.json` with four subjects in the fixed v0.3.2 order: `adapter/<filename>`, `trace-events.jsonl`, `trace-claim-bindings.json`, `silver-trace-binding-report.json`.
8. With `--self-validate`, subprocess-invokes the v0.3.2 verifier on the staged manifest BEFORE the atomic move; on failure it removes the staging directory, leaves the destination untouched, and refuses with `FAIL: trace_binding_self_validation_failed: <detail>` and exit code 1.
9. Atomically `os.replace()` the staging directory into `--output-dir`.

Runner-only refusal reasons (4):

| Reason | Triggered when |
|---|---|
| `adapter_validation_failed` | Adapter trust-authority pre-check fails OR v0.2.6 adapter validator subprocess fails |
| `trace_events_validation_failed` | Trace events JSONL fails structural / enum / ordering / uniqueness checks |
| `trace_binding_set_validation_failed` | Binding set JSON fails structural / enum / cross-check / time-window checks |
| `trace_binding_self_validation_failed` | `--self-validate` subprocess invocation of the v0.3.2 verifier on the staged package fails before the atomic move |

Exit codes: 0 (success), 1 (trace binding refused or self-validation failed), 2 (usage/input error).

## Silver Trace Binding Verifier (v0.3.2)

Validates a v0.3.2 Silver trace binding package. Pure-stdlib. Hash-first ordering. The verifier owns every cross-check of the trace binding report against the trace events fixture and the binding set, and subprocess-invokes the unchanged **v0.2.6 adapter validator** on the adapter subject.

```bash
python3 tools/silver/verify_silver_trace_binding_v0_1_0.py \
  --manifest /tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-manifest.json
```

Ordered verifier checks (each maps to a single stable failure reason; no OR-accept):

1. Parse and structurally validate the manifest (`invalid_trace_binding_manifest`).
2. Subject path traversal — checked BEFORE exact path equality (`trace_subject_path_traversal`).
3. Exact subject path + role equality against the fixed v0.3.2 SUBJECT_ORDER (`invalid_trace_binding_manifest`).
4. Subject file existence (`trace_subject_file_missing`).
5. Subject SHA-256 and size recomputation (`trace_subject_hash_mismatch`).
6. Adapter structural pre-check (Amendment 1, BEFORE the v0.2.6 validator subprocess) — refuses any adapter whose `trust_boundary.source_is_trust_authority` is not exactly `false` (`trace_source_marked_authority`).
7. Subprocess-invokes the unchanged v0.2.6 adapter validator (`trace_adapter_invalid`).
8. Parses trace events; field and enum checks (`trace_events_invalid`).
9. Unique `event_id` and unique `(trace_id, span_id)` (`trace_event_duplicate`).
10. Strict `(event_time, event_id)` ordering (`trace_event_time_order_invalid`).
11. Parses binding set; field and enum checks (`trace_binding_set_invalid`).
12. Unique `claim_id` (`trace_binding_duplicate`).
13. Non-gap rows: referenced event exists (`trace_binding_event_missing`).
14. Non-gap rows: `required_*` fields equal resolved event fields (`trace_binding_field_mismatch`).
15. Non-gap rows: `event_time` inside `trace_time_window` (`trace_binding_time_window_mismatch`).
16. Parses report; field and enum checks (`trace_report_invalid`).
17. Cross-check report hashes / counts / time-window / ids vs manifest and inputs (`trace_report_binding_mismatch`).
18. Warning/gap/out-of-scope downgrade (Amendment 2, BEFORE generic status mismatch) (`trace_warning_downgrade`).
19. Per-row re-derivation equality (`trace_report_status_mismatch`).
20. Re-compute `binding_summary` counts (`trace_report_count_mismatch`).
21. Overclaim scan OUTSIDE `scope_limitations` / `non_claims` for 22 forbidden positive tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance` (`trace_overclaim`).
22. `scope_limitations` non-empty / non-blank across manifest, binding set, and report (`trace_limitations_missing`).
23. `non_claims` non-empty / non-blank across manifest, binding set, and report (`trace_non_claims_missing`).

Stable verifier failure reasons (22 total):

| Reason | Triggered when |
|---|---|
| `invalid_trace_binding_manifest` | Manifest is unparseable, missing required fields, has wrong `document_type` / `schema_version`, or subject layout / roles do not match the fixed v0.3.2 order |
| `trace_subject_path_traversal` | Any subject path is absolute or contains `..` |
| `trace_subject_file_missing` | Any subject file is missing on disk |
| `trace_subject_hash_mismatch` | Recomputed SHA-256 or size disagrees with the manifest |
| `trace_source_marked_authority` | Adapter declares `trust_boundary.source_is_trust_authority` other than exactly `false` |
| `trace_adapter_invalid` | Subprocess invocation of the unchanged v0.2.6 adapter validator on the adapter subject fails |
| `trace_events_invalid` | Trace events JSONL has structural, field, or enum errors |
| `trace_event_duplicate` | Duplicate `event_id` or duplicate `(trace_id, span_id)` |
| `trace_event_time_order_invalid` | Events not strictly ordered by `(event_time, event_id)` ascending |
| `trace_binding_set_invalid` | Binding set has structural, field, or enum errors |
| `trace_binding_duplicate` | Duplicate `claim_id` in the binding set |
| `trace_binding_event_missing` | A non-gap binding row references an event absent from the trace fixture |
| `trace_binding_field_mismatch` | A non-gap binding row's `required_*` fields disagree with the resolved event |
| `trace_binding_time_window_mismatch` | A non-gap binding row resolves to an event with `event_time` outside `trace_time_window` |
| `trace_report_invalid` | Report has structural, field, or enum errors |
| `trace_report_binding_mismatch` | Report hashes / counts / time-window / ids disagree with the manifest, events, or binding set |
| `trace_warning_downgrade` | A row whose `expected_binding_status` is `bound_with_warning`, `trace_gap_detected`, or `out_of_scope_for_trace_binding` has been silently downgraded to `bound` |
| `trace_report_status_mismatch` | Any per-row re-derivation disagrees (non-downgrade case) |
| `trace_report_count_mismatch` | Recomputed `binding_summary` counts disagree with `bindings[].binding_status` |
| `trace_limitations_missing` | `scope_limitations` empty or blank across manifest, binding set, or report |
| `trace_non_claims_missing` | `non_claims` empty or blank across manifest, binding set, or report |
| `trace_overclaim` | Any string outside `scope_limitations` / `non_claims` contains a forbidden positive token |

The four runner-only refusal codes (`adapter_validation_failed`, `trace_events_validation_failed`, `trace_binding_set_validation_failed`, `trace_binding_self_validation_failed`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Silver Adapter Pilot Package Runner (v0.3.3)

Builds a deterministic, local Silver adapter pilot package that normalizes an OpenTelemetry-shaped local source-export fixture into ProofRail v0.3.2 trace-binding inputs under a declarative, evidence-only mapping. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial adapter pilot package on disk and no staging sibling.

```bash
python3 tools/silver/build_silver_adapter_pilot_v0_1_0.py \
  --adapter examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json \
  --source-export fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl \
  --normalization-map fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json \
  --bindings fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json \
  --adapter-pilot-report-id silver-adapter-pilot-v0.3.3-demo-001 \
  --generated-at 2026-06-22T00:10:00Z \
  --output-dir /tmp/proofrail-silver-adapter-pilot-v0.3.3 \
  --force \
  --self-validate
```

What the runner does, in order:

1. Structural pre-check: refuse if the adapter declares `trust_boundary.source_is_trust_authority` other than exactly `false` (`adapter_validation_failed`).
2. Subprocess-invokes the unchanged v0.2.6 adapter validator on `--adapter` (`adapter_validation_failed`).
3. Parses the OpenTelemetry-shaped source-export JSONL: closed `export_format = "proofrail.simulated_otel_trace_export.v0.1"`, closed `proofrail.decision` enum, required `span.attributes["proofrail.*"]` fields, unique `export_record_id`, unique `(trace_id, span_id)`, strict `(span.start_time, export_record_id)` ascending ordering (`source_export_validation_failed`).
4. Parses and structurally validates the normalization map JSON: mapping language admits only `<source.dot.path>` and `"constant:<literal>"` values; `source_format` and `target_document_type` are closed (`normalization_map_validation_failed`).
5. Parses the v0.3.2 binding set JSON structurally (`binding_set_validation_failed`).
6. Stages the package directory under `<output-dir>.staging.<pid>`.
7. Applies the normalization map to derive normalized trace events. Dot-path resolution uses LONGEST-PREFIX KEY MATCHING at each step so OpenTelemetry-style flat-with-dots attribute keys (e.g. `proofrail.event_id`) can be addressed without quoting. Any required-field shortfall is surfaced as `normalization_map_validation_failed`.
8. Subprocess-invokes the unchanged v0.3.2 trace-binding builder with `--force --self-validate` on the normalized files; failure is surfaced as `nested_trace_binding_generation_failed`.
9. Derives `silver-adapter-pilot-report.json` deterministically; pre-bakes the seven required claims with `status: pass` and forces every `source_is_trust_authority` / `runtime_truth_claimed` / `normalization_status` / `normalized_events_match_source` / `nested_trace_binding_status` flag.
10. Emits `silver-adapter-pilot-manifest.json` with exactly seven subjects in fixed order: `adapter/<filename>` / `source/source-otel-trace-export.jsonl` / `normalization/normalization-map.json` / `normalized/trace-events.jsonl` / `normalized/trace-claim-bindings.json` / `trace-binding/silver-trace-binding-manifest.json` / `silver-adapter-pilot-report.json`.
11. With `--self-validate`, subprocess-invokes the v0.3.3 verifier on the staged manifest BEFORE the atomic move; on failure it removes the staging directory, leaves the destination untouched, and refuses with `FAIL: adapter_pilot_self_validation_failed: <detail>` and exit code 1.
12. Atomic publish: only AFTER staging build and (optional) self-validation succeed does the runner remove an existing `--output-dir` (required `--force`) and `os.replace()` the staging directory into place. Any earlier failure leaves staging cleaned up and `--output-dir` untouched.

Runner-only refusal reasons (6):

| Reason | Triggered when |
|---|---|
| `adapter_validation_failed` | Adapter trust-authority pre-check fails, or the v0.2.6 adapter validator subprocess fails |
| `source_export_validation_failed` | Source-export JSONL fails structural / enum / uniqueness / ordering / required-attribute checks |
| `normalization_map_validation_failed` | Normalization map JSON fails structural checks, or a required v0.3.2 target field cannot be populated for any record |
| `binding_set_validation_failed` | Binding set JSON fails structural checks |
| `nested_trace_binding_generation_failed` | Subprocess invocation of the unchanged v0.3.2 trace-binding builder on the normalized files fails |
| `adapter_pilot_self_validation_failed` | `--self-validate` subprocess invocation of the v0.3.3 verifier on the staged package fails before the atomic move |

Exit codes: 0 (success), 1 (adapter pilot refused or self-validation failed), 2 (usage/input error).

## Silver Adapter Pilot Package Verifier (v0.3.3)

Validates a v0.3.3 Silver adapter pilot package. Pure-stdlib. Hash-first ordering. The verifier owns every cross-check of the adapter pilot report against the source export, normalization map, normalized trace events, normalized binding set, and nested v0.3.2 manifest. Subprocess-invokes the unchanged **v0.2.6 adapter validator** on the adapter subject and the unchanged **v0.3.2 trace-binding verifier** on the nested manifest.

```bash
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \
  --manifest /tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-manifest.json
```

Ordered verifier checks (25 numbered steps mapping to 24 stable failure reasons; steps 1 and 3 share `invalid_adapter_pilot_manifest`; no OR-accept):

1. Parse and structurally validate the manifest (`invalid_adapter_pilot_manifest`).
2. Subject path traversal — checked BEFORE exact path equality (`adapter_pilot_subject_path_traversal`).
3. Exact subject path + role equality against the fixed v0.3.3 SUBJECT_ORDER (`invalid_adapter_pilot_manifest`).
4. Subject file existence (`adapter_pilot_subject_file_missing`).
5. Subject SHA-256 and size recomputation (`adapter_pilot_subject_hash_mismatch`).
6. Adapter structural pre-check (BEFORE the v0.2.6 validator subprocess) — refuses any adapter whose `trust_boundary.source_is_trust_authority` is not exactly `false` (`adapter_pilot_source_marked_authority`).
7. Subprocess-invokes the unchanged v0.2.6 adapter validator (`adapter_pilot_adapter_invalid`).
8. Parses the source export; field and enum checks (`source_export_invalid`).
9. Unique `export_record_id` and unique `(trace_id, span_id)` (`source_export_duplicate`).
10. Strict `(span.start_time, export_record_id)` ascending ordering (`source_export_time_order_invalid`).
11. Parses the normalization map; field and mapping-language checks (`normalization_map_invalid`).
12. Re-derives normalized events; required v0.3.2 target field must be populated per record (`normalization_required_field_missing`).
13. Parses the packaged normalized trace events (`normalized_trace_invalid`).
14. Re-derived normalized bytes equal packaged normalized bytes (`normalized_trace_mismatch`).
15. Subprocess-invokes the unchanged v0.3.2 verifier on the nested manifest (`nested_trace_binding_invalid`).
16. Cross-check nested manifest subjects [0]/[1]/[2] hashes equal outer subjects [0]/[3]/[4] (`nested_trace_binding_mismatch`).
17. Parses the report; field and enum checks (`adapter_pilot_report_invalid`).
18. Cross-check report hashes / paths / source_format / target_document_type / report ids vs manifest and inputs (`adapter_pilot_report_binding_mismatch`).
19. Re-compute `source_record_count` and `normalized_event_count` (`adapter_pilot_report_count_mismatch`).
20. Required claim IDs present (`adapter_pilot_claim_missing`).
21. Required claims status equals `pass` (`adapter_pilot_claim_failed`).
22. Evidence refs package-local and safe — no `..`, no absolute paths, whitelisted prefix (`adapter_pilot_evidence_ref_invalid`).
23. `scope_limitations` non-empty / non-blank across manifest and report (`adapter_pilot_limitations_missing`).
24. `non_claims` non-empty / non-blank across manifest and report (`adapter_pilot_non_claims_missing`).
25. Overclaim scan OUTSIDE `scope_limitations` / `non_claims` for 23 forbidden positive tokens including `runtime truth proved`, `opentelemetry conformance`, `vendor certified`, and `production approved` (`adapter_pilot_overclaim`).

Stable verifier failure reasons (24 total):

| Reason | Triggered when |
|---|---|
| `invalid_adapter_pilot_manifest` | Manifest is unparseable, missing required fields, has wrong `document_type` / `schema_version`, or subject layout / roles do not match the fixed v0.3.3 order |
| `adapter_pilot_subject_path_traversal` | Any subject path is absolute or contains `..` |
| `adapter_pilot_subject_file_missing` | Any subject file is missing on disk |
| `adapter_pilot_subject_hash_mismatch` | Recomputed SHA-256 or size disagrees with the manifest |
| `adapter_pilot_source_marked_authority` | Adapter declares `trust_boundary.source_is_trust_authority` other than exactly `false` |
| `adapter_pilot_adapter_invalid` | Subprocess invocation of the unchanged v0.2.6 adapter validator on the adapter subject fails |
| `source_export_invalid` | Source-export JSONL has structural, field, or enum errors |
| `source_export_duplicate` | Duplicate `export_record_id` or duplicate `(trace_id, span_id)` |
| `source_export_time_order_invalid` | Records not strictly ordered by `(span.start_time, export_record_id)` ascending |
| `normalization_map_invalid` | Normalization map JSON has structural, field, or mapping-language errors |
| `normalization_required_field_missing` | A required v0.3.2 target field cannot be populated from the source export under the mapping |
| `normalized_trace_invalid` | Packaged normalized trace events JSONL fails to parse |
| `normalized_trace_mismatch` | Verifier-side re-derived normalized bytes disagree with the packaged normalized bytes |
| `nested_trace_binding_invalid` | Subprocess invocation of the unchanged v0.3.2 verifier on the nested manifest fails |
| `nested_trace_binding_mismatch` | Nested manifest subjects [0]/[1]/[2] hashes disagree with outer subjects [0]/[3]/[4] |
| `adapter_pilot_report_invalid` | Report has structural, field, or enum errors |
| `adapter_pilot_report_binding_mismatch` | Report hashes / paths / source_format / target_document_type / ids disagree with the manifest or inputs |
| `adapter_pilot_report_count_mismatch` | Recomputed `source_record_count` / `normalized_event_count` disagrees with the report |
| `adapter_pilot_claim_missing` | A required claim id is missing from the report |
| `adapter_pilot_claim_failed` | A required claim status is not `pass` |
| `adapter_pilot_evidence_ref_invalid` | An `evidence_refs` entry is absolute, contains `..`, or points outside the allowed package-local prefix set |
| `adapter_pilot_limitations_missing` | `scope_limitations` empty or blank in manifest or report |
| `adapter_pilot_non_claims_missing` | `non_claims` empty or blank in manifest or report |
| `adapter_pilot_overclaim` | Any string outside `scope_limitations` / `non_claims` contains a forbidden positive token |

The six runner-only refusal codes (`adapter_validation_failed`, `source_export_validation_failed`, `normalization_map_validation_failed`, `binding_set_validation_failed`, `nested_trace_binding_generation_failed`, `adapter_pilot_self_validation_failed`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Silver Challenge / Withdrawal Record Primitives Runner (v0.3.4)

Builds a deterministic, local Silver challenge / withdrawal primitives package over an unchanged v0.3.0 acceptance handoff target. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial package on disk and no staging sibling.

```bash
python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py \
  --target-handoff-root /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
  --challenge-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json \
  --withdrawal-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json \
  --generated-at 2026-06-29T00:30:00Z \
  --output-dir /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4 \
  --force \
  --self-validate
```

What the runner does, in order:

1. Subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier against `<target-handoff-root>/silver-acceptance-handoff-manifest.json` (`handoff_validation_failed`).
2. Structurally validates the input challenge record under the v0.3.4 closed enum vocabulary (10 reasons, 4 statuses). Accepts the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` as a syntactically valid `target.target_manifest_sha256` value so input fixtures can be authored independently of the target hash (`challenge_record_validation_failed`).
3. Structurally validates the input withdrawal record under the v0.3.4 closed enum vocabulary (7 reasons, 4 statuses, 4 effects) and the same placeholder rule (`withdrawal_record_validation_failed`).
4. Performs four binding cross-checks against the parsed v0.3.0 handoff manifest (`challenge_withdrawal_binding_failed`):
   - both records' `target.target_record_id` equal the v0.3.0 handoff manifest's `handoff_id`;
   - the withdrawal record's `related_challenge_record_id` equals the input challenge record's `challenge_record_id`;
   - the time-order chain `target.generated_at ≤ challenge.filed_at ≤ withdrawal.recorded_at ≤ withdrawal.effective_at` is monotone;
   - both records' `target.target_manifest_path` equal the packaged subject [0] path `target-handoff/silver-acceptance-handoff-manifest.json`.
5. Stages the package directory under `<output-dir>.staging.<pid>`.
6. Byte-copies the v0.3.0 handoff package root into `target-handoff/`.
7. Recomputes the SHA-256 of the copied target handoff manifest and rewrites the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in both packaged record copies under `records/` to that recomputed hash label.
8. Derives `silver-challenge-withdrawal-summary.json` deterministically from the copied target manifest, the bound challenge record, and the bound withdrawal record; pre-bakes the seven required claims with `status: pass`; forces `summary.posture` from the closed `withdrawal_effect → posture` mapping table.
9. Emits `silver-challenge-withdrawal-manifest.json` with exactly four subjects in fixed order: `target-handoff/silver-acceptance-handoff-manifest.json` / `records/challenge-record.json` / `records/withdrawal-record.json` / `silver-challenge-withdrawal-summary.json`.
10. With `--self-validate`, subprocess-invokes the v0.3.4 verifier on the staged manifest BEFORE the atomic move; on failure it removes the staging directory, leaves the destination untouched, and refuses with `FAIL: challenge_withdrawal_self_validation_failed: <detail>` and exit code 1.
11. Atomic publish: only AFTER staging build and (optional) self-validation succeed does the runner remove an existing `--output-dir` (required `--force`) and `os.replace()` the staging directory into place. Any earlier failure leaves staging cleaned up and `--output-dir` untouched.

Runner-only refusal reasons (5):

| Reason | Triggered when |
|---|---|
| `handoff_validation_failed` | Subprocess invocation of the unchanged v0.3.0 acceptance handoff verifier on the target handoff manifest fails |
| `challenge_record_validation_failed` | Input challenge record fails structural / enum / placeholder-syntax checks |
| `withdrawal_record_validation_failed` | Input withdrawal record fails structural / enum / placeholder-syntax checks |
| `challenge_withdrawal_binding_failed` | Any of the four runner-owned binding cross-checks against the parsed v0.3.0 handoff manifest disagree |
| `challenge_withdrawal_self_validation_failed` | `--self-validate` subprocess invocation of the v0.3.4 verifier on the staged package fails before the atomic move |

Exit codes: 0 (success), 1 (package refused or self-validation failed), 2 (usage/input error).

## Silver Challenge / Withdrawal Record Primitives Verifier (v0.3.4)

Validates a v0.3.4 Silver challenge / withdrawal primitives package. Pure-stdlib. Hash-first ordering. The verifier owns every cross-check of the summary against the target handoff manifest, the bound challenge record, and the bound withdrawal record. Subprocess-invokes the unchanged **v0.3.0 acceptance handoff verifier** on subject [0].

```bash
python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py \
  --manifest /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-manifest.json
```

Ordered verifier checks (29 numbered steps mapping to 24 stable failure reasons; manifest structural failures throughout steps 1–9 share `invalid_challenge_withdrawal_manifest`; step 29 covers both `_limitations_missing` and `_non_claims_missing`; no OR-accept):

1. Parse manifest JSON (`invalid_challenge_withdrawal_manifest`).
2. Manifest top-level shape: `document_type`, `schema_version`, `proofrail_release`, `manifest_id`, `generated_at`, `hash_algorithm`, and presence-only `scope_limitations` / `non_claims` (`invalid_challenge_withdrawal_manifest`).
3. Subjects array shape: exactly 4 entries (`invalid_challenge_withdrawal_manifest`).
4. Each subject is an object with a non-empty `path` string (`invalid_challenge_withdrawal_manifest`).
5. Subject path traversal — checked BEFORE exact path equality (`challenge_withdrawal_subject_path_traversal`).
6. Exact subject path + role equality against the fixed v0.3.4 SUBJECT_ORDER (`invalid_challenge_withdrawal_manifest`).
7. Each subject `sha256` / `size_bytes` shape (`invalid_challenge_withdrawal_manifest`).
8. Each subject file exists on disk (`challenge_withdrawal_subject_file_missing`).
9. Recompute SHA-256 and size for each subject; size mismatches fold to `invalid_challenge_withdrawal_manifest` while hash mismatches surface as `challenge_withdrawal_subject_hash_mismatch`.
10. Subprocess-invokes the unchanged v0.3.0 handoff verifier on subject [0] (`nested_handoff_invalid`).
11. Parses the target handoff manifest for `handoff_id` / `generated_at` cross-checks (`nested_handoff_invalid`).
12. Parses and structurally validates (presence-only) the packaged challenge record (`challenge_record_invalid`).
13. Parses and structurally validates (presence-only) the packaged withdrawal record (`withdrawal_record_invalid`).
14. Closed-enum check on `challenge.challenge_reason` (`challenge_record_reason_invalid`).
15. Closed-enum check on `challenge.challenge_status` (`challenge_record_status_invalid`).
16. Challenge record `evidence_refs` validation — no `..`, no absolute, all non-empty strings (`challenge_record_evidence_ref_invalid`).
17. Closed-enum check on `withdrawal.withdrawal_reason` (`withdrawal_record_reason_invalid`).
18. Closed-enum check on `withdrawal.withdrawal_status` (`withdrawal_record_status_invalid`).
19. Withdrawal record `evidence_refs` validation — no `..`, no absolute, all non-empty strings (`withdrawal_record_evidence_ref_invalid`).
20. Packaged challenge record target binding — chains placeholder-unbound → `target_manifest_sha256` drift vs subject [0] → `target_record_id` drift vs the parsed v0.3.0 `handoff_id`; every variant emits the single consolidated reason (`challenge_record_target_mismatch`).
21. Packaged withdrawal record target binding — same three checks chained, single consolidated reason (`withdrawal_record_target_mismatch`).
22. Withdrawal's `related_challenge_record_id` equals challenge's `challenge_record_id` (`withdrawal_record_challenge_ref_mismatch`).
23. Monotone time-order chain across target / challenge / withdrawal (`challenge_withdrawal_time_order_invalid`).
24. Parses and structurally validates the summary, including the seven required claims list (claim count, `claim_id` order, `status: pass`, non-empty `evidence_refs` within the allowed package-local prefix set with no `..`, optional `description` non-empty); any structural problem with the claims folds into `challenge_withdrawal_summary_invalid` (the approved taxonomy intentionally has no dedicated reason for a missing or failing required claim).
25. Summary `target.*` and `records.*` cross-bind to manifest subjects, AND `challenge_status` / `withdrawal_status` / `withdrawal_effect` echo the bound records — all surface as `challenge_withdrawal_summary_binding_mismatch` (the previous `_summary_status_mismatch` reason is folded into this single reason).
26. `summary.summary.challenge_count == 1` and `withdrawal_count == 1` (`challenge_withdrawal_summary_count_mismatch`, singular).
27. `summary.summary.posture` is in the closed set AND matches the closed `withdrawal_effect → posture` table (`challenge_withdrawal_posture_invalid`).
28. Overclaim scan OUTSIDE `scope_limitations` / `non_claims` including the optional `claim.description` field (`challenge_withdrawal_overclaim`).
29. `scope_limitations` non-empty / non-blank across manifest and summary (`challenge_withdrawal_limitations_missing`), then `non_claims` non-empty / non-blank across manifest and summary (`challenge_withdrawal_non_claims_missing`).

Stable verifier failure reasons (24 total):

| Reason | Triggered when |
|---|---|
| `invalid_challenge_withdrawal_manifest` | Manifest is unparseable, missing required fields, has wrong `document_type` / `schema_version`, has a malformed subjects array, has subject `sha256` / `size_bytes` of the wrong shape, has a size mismatch, or subject layout / roles do not match the fixed v0.3.4 order |
| `challenge_withdrawal_subject_path_traversal` | Any subject path is absolute or contains `..` (checked BEFORE exact path equality) |
| `challenge_withdrawal_subject_file_missing` | Any subject file is missing on disk |
| `challenge_withdrawal_subject_hash_mismatch` | Recomputed SHA-256 disagrees with the manifest |
| `nested_handoff_invalid` | Subprocess invocation of the unchanged v0.3.0 handoff verifier on subject [0] fails, or its manifest can't be re-parsed for the `handoff_id` / `generated_at` cross-checks |
| `challenge_record_invalid` | Packaged challenge record fails presence-only structural checks (shape / required fields / target block / scope_limitations / non_claims / evidence_refs list type) |
| `withdrawal_record_invalid` | Packaged withdrawal record fails presence-only structural checks (same family) |
| `challenge_record_target_mismatch` | Packaged challenge record `target.target_manifest_sha256` still equals the literal placeholder, OR disagrees with subject [0] sha256, OR `target.target_record_id` disagrees with the v0.3.0 handoff `handoff_id` (single consolidated reason for all three variants) |
| `withdrawal_record_target_mismatch` | Packaged withdrawal record `target.target_manifest_sha256` still equals the literal placeholder, OR disagrees with subject [0] sha256, OR `target.target_record_id` disagrees with the v0.3.0 handoff `handoff_id` (single consolidated reason for all three variants) |
| `challenge_record_reason_invalid` | Packaged challenge record `challenge.challenge_reason` is outside the closed 10-value enum |
| `challenge_record_status_invalid` | Packaged challenge record `challenge.challenge_status` is outside the closed 4-value enum |
| `challenge_record_evidence_ref_invalid` | Packaged challenge record `evidence_refs` contains an absolute path, a `..` segment, or a non-string / empty entry |
| `withdrawal_record_reason_invalid` | Packaged withdrawal record `withdrawal.withdrawal_reason` is outside the closed 7-value enum |
| `withdrawal_record_status_invalid` | Packaged withdrawal record `withdrawal.withdrawal_status` is outside the closed 4-value enum |
| `withdrawal_record_evidence_ref_invalid` | Packaged withdrawal record `evidence_refs` contains an absolute path, a `..` segment, or a non-string / empty entry |
| `withdrawal_record_challenge_ref_mismatch` | Withdrawal's `related_challenge_record_id` disagrees with the challenge's `challenge_record_id` |
| `challenge_withdrawal_time_order_invalid` | Time-order chain across target / challenge / withdrawal is not monotone |
| `challenge_withdrawal_summary_invalid` | Summary has structural / field / enum errors, OR a required claim id is missing or out of order, OR a required claim has `status` other than `pass`, OR a required claim has an unsafe / out-of-prefix-set `evidence_refs` entry, OR an optional `claim.description` is present but blank |
| `challenge_withdrawal_summary_binding_mismatch` | Summary `target.*` / `records.*` ids / hashes / paths disagree with the manifest subjects, OR `summary.summary.challenge_status` / `withdrawal_status` / `withdrawal_effect` disagree with the bound records (folded into a single binding reason) |
| `challenge_withdrawal_summary_count_mismatch` | `summary.summary.challenge_count` or `withdrawal_count` is not exactly 1 |
| `challenge_withdrawal_posture_invalid` | `summary.summary.posture` is out of the closed set, OR disagrees with the closed `withdrawal_effect → posture` mapping table |
| `challenge_withdrawal_overclaim` | Any string outside `scope_limitations` / `non_claims` (including optional `claim.description`) contains a forbidden positive token |
| `challenge_withdrawal_limitations_missing` | `scope_limitations` empty, missing, or contains a blank entry in manifest or summary |
| `challenge_withdrawal_non_claims_missing` | `non_claims` empty, missing, or contains a blank entry in manifest or summary |

The five runner-only refusal codes (`handoff_validation_failed`, `challenge_record_validation_failed`, `withdrawal_record_validation_failed`, `challenge_withdrawal_binding_failed`, `challenge_withdrawal_self_validation_failed`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Silver Relying-Party Policy Pack Runner (v0.3.5)

Builds a deterministic, local Silver Relying-Party Policy Pack package from a single hand-authored input. Pure-stdlib. Atomic staging-then-replace; a refused or self-validation-failed run leaves no partial package on disk and no staging sibling.

```bash
python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py \
  --policy-pack fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json \
  --manifest-id proofrail-silver-relying-party-policy-pack-manifest-demo-001 \
  --report-id proofrail-silver-relying-party-policy-pack-conformance-report-demo-001 \
  --generated-at 2026-07-06T00:30:00Z \
  --output-dir /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5 \
  --force \
  --self-validate
```

What the runner does, in order:

1. Phase A preflight on `--policy-pack` runs five ordered, mutually exclusive checks, each emitting one of the five runner-only refusal reasons (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`). Phase A never touches the output directory and never creates a staging sibling.
2. Stages the package under `<output-dir>.staging.<pid>`.
3. Byte-copies the input policy pack to `<staging>/silver-relying-party-policy-pack.json` (subject [0]).
4. Re-derives the conformance report deterministically as canonical JSON bytes (`sort_keys=True`, `separators=(",",":"))` plus a trailing newline) — 24 entries, one per approved verifier check, each `status: pass` — and writes it to `<staging>/silver-relying-party-policy-pack-conformance-report.json` (subject [1]).
5. Writes the 2-subject manifest at `<staging>/silver-relying-party-policy-pack-manifest.json`.
6. With `--self-validate`, subprocess-invokes the v0.3.5 verifier on the staged manifest BEFORE the atomic move. The runner relays the verifier's OWN stable failure reason UNCHANGED and does NOT wrap it in a sixth runner-only code. On self-validation failure the staging directory is removed and `--output-dir` is left untouched.
7. Atomic publish: only AFTER staging build and (optional) self-validation succeed does the runner remove an existing `--output-dir` (required `--force`) and `os.replace()` the staging directory into place.

Runner-only refusal reasons (5):

| Reason | Triggered when |
|---|---|
| `runner_input_path_missing` | `--policy-pack` argv is missing or empty |
| `runner_input_path_forbidden` | `--policy-pack` is an absolute path or contains a `..` segment |
| `runner_input_file_missing` | `--policy-pack` relative path does not exist on disk |
| `runner_input_read_failed` | `--policy-pack` path is a directory or otherwise unreadable |
| `runner_input_json_invalid` | `--policy-pack` file is not valid UTF-8 JSON |

The runner never wraps a verifier failure in a sixth runner-only code. The regression test explicitly asserts that no `runner_self_validation_failed` (or any other sixth wrapper) is ever emitted.

Exit codes: 0 (success), 1 (package refused, self-validation failed, or verifier relay), 2 (usage/input error).

## Silver Relying-Party Policy Pack Verifier (v0.3.5)

Validates a v0.3.5 Silver Relying-Party Policy Pack package. Pure-stdlib. Non-masking ordering: all 22 structural checks against the policy pack body run BEFORE the conformance-report byte-image re-derivation. The verifier owns every check; no subprocess invocations.

```bash
python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py \
  --manifest /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/silver-relying-party-policy-pack-manifest.json
```

Ordered verifier checks (24 numbered steps mapping to 24 stable failure reasons; subject [1] conformance-report disagreement folds to `policy_pack_manifest_invalid`; no OR-accept):

1. Parse manifest JSON and re-anchor subjects (`policy_pack_manifest_invalid`).
2. Subject [0] (policy pack) top-level is a JSON object (`policy_pack_not_object`).
3. Subject [0] `document_type` / `schema_version` shape (`policy_pack_schema_invalid`).
4. Subject [0] `profile` equals `relying_party_policy_pack.preview` (`policy_pack_profile_unsupported`).
5. Subject [0] `relying_party.identity_id` / `identity_label` (`policy_pack_identity_invalid`).
6. Subject [0] `policy_authority.*` (`policy_pack_authority_invalid`).
7. Subject [0] `policy.*` with `effective_period.starts_at < ends_at` (`policy_scope_invalid`).
8. Subject [0] `applicable_protected_actions` non-empty (`protected_action_scope_invalid`).
9. Subject [0] `silver_handoff_requirements.*` closed enums (`silver_handoff_requirement_invalid`).
10. Subject [0] `verifier_requirements.*` closed enums (`verifier_requirement_invalid`).
11. Subject [0] `issuer_requirements.*` ed25519-only (`issuer_requirement_invalid`).
12. Subject [0] `revocation_requirements.*` closed enums (`revocation_requirement_invalid`).
13. Subject [0] `freshness_requirements.*` non-negative integers (`freshness_requirement_invalid`).
14. Subject [0] `challenge_handling.posture` closed enum (`challenge_requirement_invalid`).
15. Subject [0] `withdrawal_handling.posture` closed enum (`withdrawal_requirement_invalid`).
16. Subject [0] `supersession_handling.posture` closed enum (`supersession_requirement_invalid`).
17. Subject [0] `acceptance_criteria.required_silver_results[]` closed enum (`acceptance_criteria_invalid`).
18. Subject [0] `rejection_criteria.blocking_silver_results[]` closed enum (`rejection_criteria_invalid`).
19. Subject [0] `exceptions[]` shape (`exception_policy_invalid`).
20. Subject [0] `hard_stops[]` with `overridable_by_exception == false` literal (`hard_stop_policy_invalid`).
21. Subject [0] `warning_treatment.*` closed enums (`warning_policy_invalid`).
22. Subject [0] `related_silver_artifacts[]` relative-path shape (`reference_policy_invalid`).
23. Subject [0] `scope_limitations` and `non_claims` non-empty (`non_claims_missing`).
24. Subject [0] recursive prohibited-token scan outside `scope_limitations`, `non_claims`, and `relying_party.contact` (`prohibited_claim_present`).

After the 22 structural checks, the verifier parses subject [1] and deterministically re-derives the expected canonical-JSON byte image from the verified subject [0]. Any byte-image disagreement folds to `policy_pack_manifest_invalid` (the bundled report does not describe a passing verification of this policy pack). This ordering is non-masking: subject [0] structural problems always surface as their own dedicated reasons, not as a downstream report disagreement.

Stable verifier failure reasons (24 total):

| Reason | Triggered when |
|---|---|
| `policy_pack_manifest_invalid` | Manifest unparseable / wrong document_type / wrong profile / wrong schema_version / wrong subject count / wrong subject roles / wrong subject paths / wrong subject sha256 / wrong subject size_bytes, OR subject [1] conformance report disagrees byte-for-byte with the re-derivation |
| `policy_pack_not_object` | Subject [0] does not parse to a top-level JSON object |
| `policy_pack_schema_invalid` | Subject [0] `document_type` is wrong, or `schema_version` is wrong |
| `policy_pack_profile_unsupported` | Subject [0] `profile` is not `relying_party_policy_pack.preview` |
| `policy_pack_identity_invalid` | Subject [0] `relying_party.identity_id` / `identity_label` missing or empty |
| `policy_pack_authority_invalid` | Subject [0] `policy_authority.approver_role` / `approver_id` / `approved_at` missing or empty |
| `policy_scope_invalid` | Subject [0] `policy.policy_id` / `policy_version` / `in_scope_purposes` / `effective_period.starts_at < ends_at` malformed |
| `protected_action_scope_invalid` | Subject [0] `applicable_protected_actions` empty / not a list / contains a non-string or empty entry |
| `silver_handoff_requirement_invalid` | Subject [0] `silver_handoff_requirements.minimum_handoff_posture` outside the closed posture set, or `required_chain_components` empty |
| `verifier_requirement_invalid` | Subject [0] `verifier_requirements.minimum_posture` outside the closed set, or `requires_self_validate` not a boolean |
| `issuer_requirement_invalid` | Subject [0] `issuer_requirements.required_signature_algorithm != ed25519`, or `trusted_issuers` empty / missing fields |
| `revocation_requirement_invalid` | Subject [0] `revocation_requirements.mode` outside the closed set, or booleans malformed |
| `freshness_requirement_invalid` | Subject [0] `freshness_requirements.max_age_seconds` or `tolerated_skew_seconds` not a non-negative integer |
| `challenge_requirement_invalid` | Subject [0] `challenge_handling.posture` outside the closed challenge posture set |
| `withdrawal_requirement_invalid` | Subject [0] `withdrawal_handling.posture` outside the closed withdrawal posture set |
| `supersession_requirement_invalid` | Subject [0] `supersession_handling.posture` outside the closed supersession posture set |
| `acceptance_criteria_invalid` | Subject [0] `acceptance_criteria.required_silver_results` is empty, or contains a value outside the closed acceptance-results enum |
| `rejection_criteria_invalid` | Subject [0] `rejection_criteria.blocking_silver_results` is empty, or contains a value outside the closed rejection-results enum |
| `exception_policy_invalid` | Subject [0] `exceptions[i]` is missing `exception_id` / `severity` / `approver_id` / `justification` / `effect_on_scope` |
| `hard_stop_policy_invalid` | Subject [0] `hard_stops[i]` is missing `hard_stop_id` / `condition` / `on_match`, or `overridable_by_exception` is not the literal boolean false |
| `warning_policy_invalid` | Subject [0] `warning_treatment.unknown_warning_default` outside the closed enum, or `warnings[i]` missing fields or with an out-of-enum `treatment` |
| `reference_policy_invalid` | Subject [0] `related_silver_artifacts[i]` missing `kind` / `path`, or `path` is absolute or contains `..` |
| `non_claims_missing` | Subject [0] `scope_limitations` or `non_claims` empty, missing, not a list, or contains a non-string / blank entry |
| `prohibited_claim_present` | Any string value in subject [0] OUTSIDE `scope_limitations`, `non_claims`, and `relying_party.contact` contains a forbidden positive token |

The five runner-only refusal codes (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`) are **never** emitted by the verifier.

JSON parse errors are caught and surfaced as the appropriate stable reason — no Python traceback leaks.

Exit codes: 0 (valid), 1 (verification failure), 2 (usage/input error).

## Security Notes

- This is a demo signing system. Do not use generated keys for production.
- Private keys are runtime-only and must not be committed to version control.
- Revocation is local demo revocation — local relying-party policy, not production PKI revocation, public certificate revocation, OCSP, or transparency-log-backed revocation.
- This is Minimal Silver, not full Silver governance.
