# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProofRail is a vendor-neutral conformance and governance framework for AI agent actuation control. It defines an evidence layer proving that protected actions (tool calls, API invocations) are declared, mediated, rate-limited, stoppable, bypass-tested, auditable, and owned by accountable operators.

Two profiles exist:
- **Iron-plus**: Live reference profile for MCP actuation control
- **Bronze**: Local-enterprise conformance profile, implementable via ProofRail-native components or composed stacks using existing gateways/identity providers/observability tools

This is a specification and tooling repository, not a distributed package.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
python -m pytest tests/test_proofrail_claim.py

# Run regression tests
bash tests/test_bronze_claim_v0_1_1.sh
bash tests/test_bronze_claim_v0_1_2.sh
bash tests/test_bronze_evidence_bundle_v0_1_3.sh
bash tests/test_silver_signed_bundle_assertion_v0_1_0.sh
bash tests/test_silver_revocation_list_v0_1_0.sh
bash tests/test_silver_verification_report_v0_1_0.sh
bash tests/test_independent_silver_verifier_v0_1_0.sh
bash tests/test_silver_profile_v0_2_0.sh
bash tests/test_silver_profile_v0_2_1.sh
bash tests/test_silver_profile_examples_v0_2_1.sh
bash tests/test_silver_verifier_output_attestation_v0_1_0.sh
bash tests/test_silver_multi_principal_authority_v0_2_3.sh
bash tests/test_silver_multi_agent_attack_harness_v0_2_4.sh
bash tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh
bash tests/test_silver_evidence_source_adapter_v0_2_6.sh

# Validate a claim file
python3 scripts/proofrail_claim.py validate <claim.yaml>
python3 scripts/proofrail_claim.py validate <claim.yaml> --evidence-root <dir> --strict

# Generate a claim scaffold
python3 scripts/proofrail_claim.py init --profile bronze --type composed --out claim.yaml
python3 scripts/proofrail_claim.py init --profile bronze --type native --out claim.yaml

# Summarize a claim
python3 scripts/proofrail_claim.py summarize <claim.yaml>

# Generate and validate demo claim (Makefile targets)
make generate-bronze-demo-001b
make validate-bronze-demo-001b
make verify-bronze-demo-001b-evidence

# Verify evidence checksums standalone
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py <claim.yaml> <package-root>

# Generate and verify evidence bundle manifest (Makefile targets)
make bundle-bronze-demo-001b
make verify-bronze-demo-001b-bundle

# Generate evidence bundle manifest standalone
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py <package-root>

# Verify evidence bundle manifest standalone
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py <manifest.yaml> <package-root>

# Run Silver demo (end-to-end: Bronze claim → bundle manifest → sign → verify)
make silver-demo-001
make verify-silver-demo-001
make verify-silver-revocation-demo-001
make verify-silver-report-demo-001

# Export and verify independent Silver verification package (Demo 002)
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002
make verify-silver-all

# Silver profile conformance
make validate-silver-profile-demo-001
make validate-silver-profile-demo-002

# Silver v0.2.1 profile conformance
make validate-silver-profile-v0-2-1-demo-001
make validate-silver-profile-v0-2-1-demo-002
make verify-silver-profile-v0-2-1
make verify-silver-profile-examples-v0-2-1

# Silver v0.2.2 verifier output attestation
make generate-silver-verifier-attestor-demo-001
make sign-silver-verifier-attestation-demo-001
make verify-silver-verifier-attestation-demo-001
make verify-silver-attestation-v0-2-2

# Silver v0.2.3 multi-principal authority fixtures
make validate-silver-authority-fixtures-v0-2-3
make verify-silver-authority-v0-2-3
bash tests/test_silver_multi_principal_authority_v0_2_3.sh

# Silver v0.2.4 multi-agent attack harness
make run-silver-multi-agent-harness-v0-2-4
make verify-silver-multi-agent-harness-v0-2-4
bash tests/test_silver_multi_agent_attack_harness_v0_2_4.sh

# Silver v0.2.5 multi-agent trust-boundary demo package
make run-silver-multi-agent-demo-v0-2-5
make verify-silver-multi-agent-demo-v0-2-5
bash tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh

# Silver v0.2.6 evidence source adapter descriptors
make validate-silver-evidence-source-adapters-v0-2-6
make verify-silver-evidence-source-adapter-v0-2-6
bash tests/test_silver_evidence_source_adapter_v0_2_6.sh

# Silver v0.2.6 evidence source adapter validator standalone
python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py --adapter <adapter.json>
python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py --examples-dir <dir>

# Silver multi-agent harness tools standalone
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py --script <harness-script.yaml> --authority-fixture <authority-fixture.yaml> --output-dir <output-dir> [--force]
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest <harness-evidence-manifest.json>

# Silver v0.2.5 multi-agent trust-boundary demo tools standalone
python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py --demo-root <demo-dir> --harness-script <harness-script.yaml> --authority-fixture <authority-fixture.yaml> --output-dir <output-dir> [--generated-at <ISO-8601>] [--force]
python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py --package-manifest <demo-package-manifest.json>

# Silver authority tools standalone
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py --fixture <fixture.yaml>
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py --fixture <fixture.yaml> --request <request.json> --decision-time <ISO-8601> --output <report.json>

# Silver tools standalone
python3 tools/silver/generate_demo_issuer_v0_1_0.py <silver-demo-root> --force
python3 tools/silver/sign_bundle_manifest_v0_1_0.py <silver-demo-root> --private-key <key.pem> --output <assertion.yaml>
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py <assertion.yaml> <trust-policy.yaml> --silver-root <silver-root> --bronze-package-root <bronze-root> [--revocation-list <revocation-list.yaml>] [--report <report.json>]
python3 tools/silver/validate_silver_verification_report_v0_1_0.py <report.json>
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py <silver-demo-root> [--revoke-assertion <id>] [--revoke-issuer-key <issuer_id:key_id>] [--revoke-bundle-sha256 <hash>]
python3 tools/silver/validate_silver_profile_v0_2_0.py --profile-mode <mode> --verification-report <report.json> [--package-manifest <manifest.yaml>] [--output <conformance.json>]
python3 tools/silver/validate_silver_profile_v0_2_1.py --profile-mode <mode> --verification-report <report.json> [--package-manifest <manifest.yaml>] [--output <conformance.json>]
python3 tools/silver/export_independent_verification_package_v0_2_1.py --bronze-root <bronze-root> --silver-root <silver-root> --output <output-dir> --force
python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py --output-root <dir> --attestor-id <id> --key-id <key-id> --force
python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py --verification-report <report.json> --conformance-report <conformance.json> --private-key <key.pem> --attestor-id <id> --attestor-version <version> --key-id <key-id> --output <attestation.json>
python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py --attestation <attestation.json> --trust-policy <trust-policy.yaml>
```

## Architecture

### Core Tool: `scripts/proofrail_claim.py`

The primary CLI tool (~815 lines) with three subcommands: `init`, `validate`, `summarize`. It performs **structural validation only** — it checks YAML structure, required fields, enum values, and evidence file existence. It intentionally does NOT certify deployments, verify semantic conformance, or inspect live systems.

Validation flow: `YAML file → yaml.safe_load() → validate_claim() → errors/warnings/checks → format_text()/format_json()`

### Claim Schema (v0.1.1 / v0.1.2)

Claims are YAML files with 16+ required top-level sections defined in `REQUIRED_TOP_LEVEL_SECTIONS`. The schema specifications live in `schemas/bronze-claim-schema-v0.1.1.md` and `schemas/bronze-claim-schema-v0.1.2.md`. v0.1.2 adds an optional `evidence_checksums` mapping for post-generation evidence integrity verification.

Two claim types: `composed_bronze` (uses existing infrastructure) and `native_bronze_preview` (ProofRail-native, future).

### Reusable Claim Tooling: `tools/claims/`

- `generate_bronze_claim_v0_1_1.py` — Deterministic claim assembly from a `claim-input-v0.1.1.yaml` template
- `validate_bronze_claim_v0_1_1.py` — Structural validator shim
- `generate_bronze_claim_v0_1_2.py` — Deterministic claim assembly with evidence checksum computation
- `validate_bronze_claim_v0_1_2.py` — Structural validator shim (v0.1.2)
- `verify_bronze_claim_evidence_v0_1_2.py` — Evidence checksum verifier (recomputes and compares SHA-256 digests)
- `generate_evidence_bundle_manifest_v0_1_3.py` — Evidence bundle manifest generator (checksums entire portable package)
- `verify_evidence_bundle_manifest_v0_1_3.py` — Evidence bundle manifest verifier (recomputes and compares bundle checksums)

### Minimal Silver Tooling: `tools/silver/`

- `generate_demo_issuer_v0_1_0.py` — Demo Ed25519 issuer keypair and trust policy generator
- `sign_bundle_manifest_v0_1_0.py` — Bundle manifest signer (produces Silver Signed Bundle Assertion YAML)
- `verify_signed_bundle_assertion_v0_1_0.py` — Signed assertion verifier (trust policy + signature + expiry + optional revocation check + underlying bundle); emits schema-backed Silver Verification Report v0.1.0 when `--report` is supplied
- `generate_demo_revocation_list_v0_1_0.py` — Demo local revocation list generator (revoke by assertion ID, issuer key, or bundle hash)
- `validate_silver_verification_report_v0_1_0.py` — Silver verification report structural validator
- `export_independent_verification_package_v0_1_0.py` — Portable independent verification package exporter (creates source-repo-subset layout preserving Ed25519 signature)
- `validate_silver_profile_v0_2_0.py` — Silver Relying-Party Profile v0.2.0 conformance validator (two modes: `silver.base`, `silver.independent`); emits profile conformance report
- `validate_silver_profile_v0_2_1.py` — Silver Relying-Party Profile v0.2.1 conformance validator (three modes: `silver.base`, `silver.base.demo`, `silver.independent`); tightened revocation for `silver.base`
- `export_independent_verification_package_v0_2_1.py` — Portable independent verification package exporter with enhanced manifest (v0.2.1 format fields)
- `generate_demo_verifier_attestor_v0_1_0.py` — Demo Ed25519 attestor keypair and attestation trust policy generator (separate from issuer keys)
- `sign_verifier_output_attestation_v0_1_0.py` — Verifier output attestation signer (binds verifier identity to verification report + conformance report); rejects `..` in subject paths
- `verify_verifier_output_attestation_v0_1_0.py` — Verifier output attestation verifier (trust policy + binding + signature + subject hashes + metadata cross-checks); rejects `..` in subject paths
- `validate_multi_principal_authority_fixture_v0_1_0.py` — Multi-principal authority fixture structural validator (principals, grants, delegation rules, constraints, revocations)
- `evaluate_multi_principal_authority_v0_1_0.py` — Protected action authority evaluator (10-check short-circuit evaluation producing decision reports; never executes actions)
- `run_multi_agent_attack_harness_v0_1_0.py` — Deterministic multi-principal agent attack harness runner (consumes harness script + v0.2.3 fixture; routes protected-action attempts through the existing `evaluate_request` callable; handles bypass and revocation events at harness level; emits transcript, requests, decision reports, run report, evidence manifest)
- `verify_multi_agent_harness_evidence_v0_1_0.py` — Harness evidence manifest verifier (manifest type/version, path traversal rejection, SHA-256 recomputation, run report and decision report semantic checks)
- `package_multi_agent_trust_boundary_demo_v0_1_0.py` — Silver v0.2.5 multi-agent trust-boundary demo packager (invokes v0.2.4 harness runner and verifier as subprocesses, derives the eight required claims from the nested run report and transcript, emits `demo-summary.json` and `demo-package-manifest.json`)
- `verify_multi_agent_trust_boundary_demo_v0_1_0.py` — Silver v0.2.5 demo package verifier (parses the package manifest, recomputes SHA-256 for every package subject, validates `demo-summary.json` and cross-checks claim rules against nested run report / decision reports, then delegates nested verification to the unchanged v0.2.4 verifier; surfaces nested failures as the stable top-level reason `nested_harness_evidence_invalid`)
- `validate_evidence_source_adapter_v0_1_0.py` — Silver v0.2.6 evidence source adapter descriptor validator (pure-stdlib structural validator; closed set of six `source_type` values; six required evidence capabilities with `provided`/`not_provided`/`not_applicable` statuses; `decision_event` must be `provided` with full mapping fields; rejects empty/whitespace-only strings; supports `--adapter <file>` and `--examples-dir <dir>` modes with duplicate adapter_id detection)

### Silver Multi-Agent Trust-Boundary Demo: `demos/silver-demo-003-multi-agent-trust-boundary/`

v0.2.5 packages the v0.2.4 multi-agent attack harness into a local demo. The committed demo directory holds only the README and walkthrough; the packager writes runtime output under `/tmp` (default `/tmp/proofrail-silver-multi-agent-demo-v0.2.5/`) and is never staged into the repository. Eight claims are derived deterministically from the v0.2.4 harness run report: `harmless_messages_proceed`, `protected_actions_require_scoped_authority`, `unauthorized_delegation_fails`, `bypass_attempts_blocked`, `revoked_authority_fails`, `out_of_scope_actions_fail`, `evidence_is_hash_verifiable`, and `no_protected_actions_executed`. The verifier re-invokes the unchanged v0.2.4 verifier on the nested manifest. See `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md` and `docs/gold/gold-boundary-v0.2.5.md`.

### Silver Evidence Source Adapter Profile: `examples/silver-evidence-source-adapters/`

v0.2.6 adds a descriptor profile for evidence sources (gateway, observability trace, SIEM, policy engine, GRC platform, native ProofRail). Six canonical static JSON descriptors live in `examples/silver-evidence-source-adapters/`. A descriptor declares how a source's events map to ProofRail-relevant evidence fields and what the source does **not** assert. Descriptors are not evidence, not trust decisions, and not certifications. The GRC platform example is explicitly framed as workflow / risk / approval evidence only, with limitations stating workflow approval is not technical enforcement and not sufficient by itself for protected-action reliance. The local structural validator `tools/silver/validate_evidence_source_adapter_v0_1_0.py` rejects out-of-set source types, missing capabilities, missing `decision_event` mapping, empty/whitespace-only strings, sample-artifact-ref path traversal, and duplicate adapter IDs in directory mode. See `docs/silver/silver-evidence-source-adapter-profile-v0.2.6.md` and `schemas/silver-evidence-source-adapter-v0.1.0.md`.

### Independent Silver Verifier Demo: `demos/silver-demo-002-independent-verifier/`

Demonstrates relying-party separation: a standalone verifier operates on a portable verification package exported from Demo 001, without importing or invoking the main ProofRail Silver verifier or Bronze bundle verifier. The independent verifier implements all seven Silver checks inline and emits a Silver Verification Report v0.1.0-compatible JSON report. Existing Bronze and Silver Demo 001 verification semantics remain unchanged.

### Demo Stack: `demos/composed-bronze-demo-001/`

A complete Docker Compose stack (5 services) demonstrating composed Bronze conformance:
- `agentgateway` — open-source MCP gateway (the mediation substrate)
- `mock-mcp` / `stop-mcp` — FastAPI mock MCP servers for protected actuators and stop control
- `agent` / `bypass-tester` — simulated agent and bypass prevention tester
- Two Docker networks (`agent_net`, `actuator_net`) enforce network segmentation

Evidence files (JSON, JSONL, Markdown) are generated by `scripts/run_tests.sh` and referenced by path in the claim YAML.

### Key Design Patterns

- **Deterministic hashing**: Canonical JSON serialization (`json.dumps(obj, sort_keys=True, separators=(",",":"))`) ensures reproducible SHA256 hashes for actuator sets and evidence bundles.
- **Evidence coupling**: Claims reference evidence files by path; `--evidence-root` validation checks these files exist on disk.
- **Decision vocabulary**: Extensible but requires minimum set: `{allow, block, rate_limit, emergency_stop}`.
- **Normalized audit events**: JSONL format with required event types (`tool_call.attempt`, `tool_call.decision`, `tool_call.result`, `emergency.stop`, `emergency.resume`).
- **Risk tiering**: Protected actuators are assigned risk tiers (0–3) indicating impact level.
- **Nested dict access**: `_get()` helper uses dot notation (e.g., `"identity_treatment.confidence_policy"`) for deep field access in validation.

## Dependencies

Two external dependencies: **PyYAML** and **cryptography** (for Ed25519 signing in Silver tools). No linting, formatting, or CI/CD pipelines are configured.

## Development Rules (v0.1.x)

- Do not change ProofRail control semantics unless explicitly instructed.
- Do not add new dependencies unless justified and approved.
- Do not commit secrets, logs, tgz archives, or runtime state.
- Preserve clean-clone reproducibility.
- Every change must have a Make target or test.
- Every schema change must update all five artifacts: (1) schema document, (2) generator, (3) validator, (4) demo fixture, (5) README or release note if user-facing.
- Do not start Demo 002 while working on v0.1.x cleanup.
