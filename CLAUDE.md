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
bash tests/test_silver_composed_gateway_evidence_v0_2_7.sh
bash tests/test_silver_relying_party_acceptance_record_v0_2_8.sh
bash tests/test_silver_revocation_challenge_drill_v0_2_9.sh
bash tests/test_silver_acceptance_handoff_v0_3_0.sh
bash tests/test_silver_handoff_inspector_v0_3_1.sh
bash tests/test_silver_trace_binding_v0_3_2.sh
bash tests/test_silver_adapter_pilot_v0_3_3.sh
bash tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh
bash tests/test_silver_relying_party_policy_pack_v0_3_5.sh

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

# Silver v0.2.7 composed gateway evidence demo
make run-silver-composed-gateway-demo-v0-2-7
make verify-silver-composed-gateway-demo-v0-2-7
bash tests/test_silver_composed_gateway_evidence_v0_2_7.sh

# Silver v0.2.7 composed gateway evidence tools standalone
python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py --demo-root <demo-dir> --adapter <adapter.json> --gateway-events <events.jsonl> --output-dir <output-dir> [--generated-at <ISO-8601>] [--force]
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py --manifest <composed-gateway-evidence-manifest.json>

# Silver v0.2.8 relying-party acceptance record demo
make run-silver-relying-party-acceptance-demo-v0-2-8
make verify-silver-relying-party-acceptance-demo-v0-2-8
bash tests/test_silver_relying_party_acceptance_record_v0_2_8.sh

# Silver v0.2.8 relying-party acceptance record tools standalone
python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py --policy <policy.json> --evidence-manifest <composed-gateway-evidence-manifest.json> --decision <accepted|rejected|accepted_with_exceptions> --purpose <purpose-id> --decision-maker <id> --generated-at <ISO-8601> --challenge-closes-at <ISO-8601> --output-dir <output-dir> [--force] [--challenge-opens-at <ISO-8601>] [--challenge-contact <id>] [--rejection-reason <text>] [--exception severity:description:effect_on_scope] [--scope-limitation <text>] [--non-claim <text>] [--record-id <id>] [--package-id <id>] [--self-validate]
python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py --manifest <acceptance-package-manifest.json> [--evidence-package-root <v0.2.7-package-dir>]

# Silver v0.2.9 revocation/challenge drill demo
make run-silver-revocation-challenge-drill-v0-2-9
make verify-silver-revocation-challenge-drill-v0-2-9
bash tests/test_silver_revocation_challenge_drill_v0_2_9.sh

# Silver v0.2.9 revocation/challenge drill tools standalone
python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py --acceptance-manifest <v0.2.8-acceptance-package-manifest.json> --review-events <review-events.jsonl> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--evidence-package-root <v0.2.7-package-dir>] [--self-validate]
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py --manifest <revocation-challenge-drill-manifest.json> [--evidence-package-root <v0.2.7-package-dir>]

# Silver v0.3.0 acceptance handoff demo
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
bash tests/test_silver_acceptance_handoff_v0_3_0.sh

# Silver v0.3.0 acceptance handoff tools standalone
python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py --composed-evidence-manifest <v0.2.7-composed-gateway-evidence-manifest.json> --acceptance-manifest <v0.2.8-acceptance-package-manifest.json> --drill-manifest <v0.2.9-revocation-challenge-drill-manifest.json> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--handoff-id <id>] [--handoff-purpose <text>] [--recipient-role <text>] [--source-package-family <text>] [--self-validate]
python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py --manifest <silver-acceptance-handoff-manifest.json>

# Silver v0.3.1 handoff inspector + Gold gap inventory demo
make run-silver-handoff-inspection-v0-3-1
make verify-silver-handoff-inspection-v0-3-1
bash tests/test_silver_handoff_inspector_v0_3_1.sh

# Silver v0.3.1 handoff inspection tools standalone
python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py --handoff-manifest <v0.3.0-silver-acceptance-handoff-manifest.json> --requirement-set <gold-boundary-requirements.json> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--inspection-id <id>] [--self-validate]
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py --manifest <silver-handoff-inspection-manifest.json>
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py --validate-requirement-set <gold-boundary-requirements.json>

# Silver v0.3.2 trace binding profile demo
make run-silver-trace-binding-v0-3-2
make verify-silver-trace-binding-v0-3-2
bash tests/test_silver_trace_binding_v0_3_2.sh

# Silver v0.3.2 trace binding tools standalone
python3 tools/silver/build_silver_trace_binding_v0_1_0.py --adapter <observability-trace-adapter.json> --trace-events <trace-events.jsonl> --bindings <trace-claim-bindings.json> --trace-binding-report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_trace_binding_v0_1_0.py --manifest <silver-trace-binding-manifest.json>

# Silver v0.3.3 adapter pilot package demo
make run-silver-adapter-pilot-v0-3-3
make verify-silver-adapter-pilot-v0-3-3
bash tests/test_silver_adapter_pilot_v0_3_3.sh

# Silver v0.3.3 adapter pilot tools standalone
python3 tools/silver/build_silver_adapter_pilot_v0_1_0.py --adapter <observability-trace-adapter.json> --source-export <source-otel-trace-export.jsonl> --normalization-map <normalization-map.json> --bindings <trace-claim-bindings.json> --adapter-pilot-report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py --manifest <silver-adapter-pilot-manifest.json>

# Silver v0.3.4 challenge / withdrawal record primitives demo
make run-silver-acceptance-handoff-v0-3-0
make run-silver-challenge-withdrawal-primitives-v0-3-4
make verify-silver-challenge-withdrawal-primitives-v0-3-4
bash tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh

# Silver v0.3.4 challenge / withdrawal record primitives tools standalone
python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py --target-handoff-root <v0.3.0-handoff-dir> --challenge-record <challenge-record.json> --withdrawal-record <withdrawal-record.json> --generated-at <ISO-8601> --output-dir <output-dir> [--manifest-id <id>] [--summary-id <id>] [--force] [--self-validate]
python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py --manifest <silver-challenge-withdrawal-manifest.json>

# Silver v0.3.5 relying-party policy pack demo
make run-silver-relying-party-policy-pack-v0-3-5
make verify-silver-relying-party-policy-pack-v0-3-5
bash tests/test_silver_relying_party_policy_pack_v0_3_5.sh

# Silver v0.3.5 relying-party policy pack tools standalone
python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py --policy-pack <policy-pack.json> --manifest-id <id> --report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py --manifest <silver-relying-party-policy-pack-manifest.json>

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
- `compose_gateway_evidence_demo_v0_1_0.py` — Silver v0.2.7 composed gateway evidence composer (pure-stdlib; subprocess-invokes the unchanged v0.2.6 adapter validator; parses the static JSONL gateway event fixture with cross-field consistency checks; derives ten required claims; emits `composed-gateway-evidence-report.json` and `composed-gateway-evidence-manifest.json` with five subjects in deterministic order and a `composition` block)
- `verify_composed_gateway_evidence_demo_v0_1_0.py` — Silver v0.2.7 composed gateway evidence verifier (pure-stdlib; hash-first ordering; re-derives every required claim independently; validates the manifest `composition` block against the deterministic package layout; rejects wrong-but-valid evidence refs; 18 stable failure reasons including `composed_subject_hash_mismatch`, `adapter_invalid`, `source_event_invalid`, `gateway_protected_action_mismatch`, `gateway_decision_mismatch`, `gateway_bypass_mismatch`, `gateway_revocation_mismatch`, `normalized_evidence_ref_invalid`, `normalized_claim_failed`, and `execution_violation`)
- `generate_relying_party_acceptance_record_v0_1_0.py` — Silver v0.2.8 relying-party acceptance record generator (pure-stdlib; subprocess-invokes the v0.2.7 verifier; refuses `--decision accepted` with `FAIL: evidence_verification_failed: <detail>` and exit 1 when v0.2.7 verifier fails; derives `revocation_review.outcome` from the sibling composed gateway evidence report's `revoked_authority_fails` claim; emits `acceptance-policy.json`, `evidence/composed-gateway-evidence-manifest.json`, `acceptance-record.json`, and `acceptance-package-manifest.json` with three deterministic subjects)
- `validate_relying_party_acceptance_record_v0_1_0.py` — Silver v0.2.8 relying-party acceptance record validator (pure-stdlib; hash-first ordering; 21 stable failure reasons including `invalid_acceptance_package_manifest`, `acceptance_subject_path_traversal`, `acceptance_subject_hash_mismatch`, `invalid_acceptance_policy`, `invalid_acceptance_record`, `policy_mismatch`, `relying_party_mismatch`, `purpose_not_allowed`, `evidence_type_not_allowed`, `evidence_manifest_hash_mismatch`, `evidence_verification_required`, `accepted_record_verification_failed`, `accepted_record_has_blocking_exception`, `accepted_with_exceptions_missing_exception`, `rejected_record_missing_reason`, `revocation_review_missing`, `challenge_window_invalid`, `scope_limitations_missing`, `acceptance_non_claims_missing`, and `external_evidence_verification_failed`; never emits the generator-only `evidence_verification_failed`; optional `--evidence-package-root` subprocess-invokes the v0.2.7 verifier against the original package and re-checks the manifest sha256)
- `run_revocation_challenge_drill_v0_1_0.py` — Silver v0.2.9 revocation/challenge drill runner (pure-stdlib; subprocess-invokes the v0.2.8 acceptance validator; refuses with `FAIL: acceptance_package_validation_failed: <detail>` and exit 1 when the v0.2.8 validator fails on the supplied package; refuses with `FAIL: review_fixture_insufficient: <detail>` and exit 1 when the fixture lacks within-window challenges or revocation signals; stages all output in a sibling staging directory and atomically moves it into place so refused runs leave no partial output; emits `acceptance-package/` byte-copy plus `review-events.jsonl`, `revocation-challenge-drill-report.json`, and `revocation-challenge-drill-manifest.json` with three deterministic subjects)
- `verify_revocation_challenge_drill_v0_1_0.py` — Silver v0.2.9 revocation/challenge drill verifier (pure-stdlib; hash-first ordering; 22 stable failure reasons including `invalid_drill_package_manifest`, `drill_subject_file_missing`, `drill_subject_path_traversal`, `drill_subject_hash_mismatch`, `nested_acceptance_package_invalid`, `invalid_review_events`, `invalid_drill_report`, `acceptance_record_binding_mismatch`, `review_events_hash_mismatch`, `review_event_target_mismatch`, `review_event_sequence_invalid`, `challenge_window_missing`, `challenge_within_window_missing`, `challenge_window_classification_mismatch`, `revocation_signal_missing`, `revocation_signal_target_mismatch`, `required_finding_missing`, `required_review_trigger_missing`, `recommended_posture_invalid`, `scope_limitations_missing`, `drill_non_claims_missing`, and `external_evidence_verification_failed`; never emits the runner-only `acceptance_package_validation_failed` or `review_fixture_insufficient`; parses the drill report before checking review-events hash; splits target mismatches by event type so `review_event_target_mismatch` and `revocation_signal_target_mismatch` are distinct; checks classification before within-window-missing; optional `--evidence-package-root` propagates to the v0.2.8 validator)
- `build_silver_acceptance_handoff_v0_1_0.py` — Silver v0.3.0 acceptance handoff runner (pure-stdlib; subprocess-invokes the unchanged v0.2.7 verifier, v0.2.8 acceptance validator, and v0.2.9 drill verifier on the three input manifests, calling v0.2.8 and v0.2.9 WITHOUT `--evidence-package-root` so v0.3.0 owns the cross-copy chain binding; refuses with `FAIL: composed_evidence_validation_failed | acceptance_package_validation_failed | drill_package_validation_failed: <detail>` and exit 1 on any nested-validator failure; byte-copies the three nested package roots into a sibling staging directory under fixed top-level names `composed-gateway-evidence/`, `acceptance-package/`, `revocation-challenge-drill/`; performs four v0.3.0-owned chain-binding cross-checks against nested-record fields, refusing with `FAIL: handoff_chain_binding_failed: <detail>` on mismatch; maps the nested v0.2.9 `recommended_local_posture` onto a minimum handoff posture rank and selects the deterministic `recommended_handoff_posture`; emits `silver-acceptance-handoff-summary.json` and `silver-acceptance-handoff-manifest.json` with four deterministic subjects; with `--self-validate` invokes the v0.3.0 handoff verifier against the staging directory BEFORE the atomic move, removing the staging directory and leaving the destination untouched on self-validation failure)
- `verify_silver_acceptance_handoff_v0_1_0.py` — Silver v0.3.0 acceptance handoff verifier (pure-stdlib; hash-first ordering; 17 stable failure reasons: `invalid_handoff_manifest`, `handoff_subject_file_missing`, `handoff_subject_path_traversal`, `handoff_subject_hash_mismatch`, `nested_composed_evidence_invalid`, `nested_acceptance_package_invalid`, `nested_revocation_challenge_drill_invalid`, `handoff_summary_invalid`, `handoff_summary_binding_mismatch`, `handoff_chain_binding_mismatch`, `handoff_record_mismatch`, `handoff_purpose_mismatch`, `handoff_posture_invalid`, `handoff_posture_downgrade`, `handoff_overclaim`, `handoff_limitations_missing`, `handoff_non_claims_missing`; never emits the five runner-only refusal codes; re-runs the unchanged v0.2.7 verifier, v0.2.8 validator, and v0.2.9 verifier as subprocesses without `--evidence-package-root` so v0.3.0 owns the four chain-binding cross-checks; enforces posture rank ordering so any handoff posture weaker than the rank implied by the nested v0.2.9 drill posture yields `handoff_posture_downgrade`; recursive overclaim guard scans every string value in the summary outside `scope_limitations` and `non_claims` for 15 forbidden positive tokens including `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, and `trust transfer`)
- `inspect_silver_acceptance_handoff_v0_1_0.py` — Silver v0.3.1 handoff inspection runner (pure-stdlib; subprocess-invokes the unchanged v0.3.0 handoff verifier on `--handoff-manifest`, refusing with `FAIL: handoff_validation_failed: <detail>` and exit 1 on failure; subprocess-invokes the v0.3.1 verifier's `--validate-requirement-set` entry point on `--requirement-set`, refusing with `FAIL: requirement_set_validation_failed: <detail>` and exit 1 on failure; byte-copies the v0.3.0 handoff package root under `silver-acceptance-handoff/` and byte-copies the requirement set to the inspection package root; re-derives `base_handoff` / `handoff_summary` / `component_inspection` / `gold_gap_inventory` deterministically from the nested v0.3.0 summary and the requirement set; emits `silver-handoff-inspection-report.json` and `silver-handoff-inspection-manifest.json` with three deterministic subjects in fixed order; with `--self-validate` invokes the v0.3.1 verifier against the staging directory BEFORE the atomic move, removing the staging directory and leaving the destination untouched on self-validation failure, surfacing as `FAIL: inspection_self_validation_failed: <detail>` and exit 1)
- `verify_silver_handoff_inspection_v0_1_0.py` — Silver v0.3.1 handoff inspection verifier (pure-stdlib; hash-first ordering; 20 stable failure reasons: `invalid_inspection_manifest`, `inspection_subject_path_traversal`, `inspection_subject_file_missing`, `inspection_subject_hash_mismatch`, `inspection_limitations_missing`, `inspection_non_claims_missing`, `requirement_set_invalid`, `requirement_duplicate`, `requirement_domain_missing`, `inspection_report_invalid`, `inspection_report_binding_mismatch`, `inspection_handoff_summary_mismatch`, `inspection_review_posture_downgrade`, `inspection_component_status_mismatch`, `inspection_requirement_missing`, `inspection_requirement_status_mismatch`, `inspection_count_mismatch`, `inspection_gold_status_invalid`, `inspection_gold_overclaim`, `nested_handoff_invalid`; never emits the three runner-only refusal codes; subprocess-invokes the unchanged v0.3.0 handoff verifier on subject [0] (failure surfaces as `nested_handoff_invalid`); reserves `inspection_handoff_summary_mismatch` for non-posture summary fields only (`acceptance_record_id`, `decision_status`, `purpose_id`) and `inspection_review_posture_downgrade` for posture-rank-weaker or missing/blank `reuse_warning` when nested rank ≥ 1, so both reasons are independently reachable; reserves `requirement_duplicate` and `requirement_domain_missing` as dedicated reasons distinct from the generic structural `requirement_set_invalid`; early structural checks for `scope_limitations` and `non_claims` verify presence/type only, with emptiness / blank entries falling through to dedicated `inspection_limitations_missing` / `inspection_non_claims_missing`; recursive overclaim guard adds three new `gold-ready` / `gold ready` / `gold_ready` tokens to the v0.3.0 set of 15 forbidden positive tokens; exposes a `--validate-requirement-set` entry point used by the runner's pre-staging validation step)
- `build_silver_trace_binding_v0_1_0.py` — Silver v0.3.2 trace binding runner (pure-stdlib; structural trust-authority pre-check BEFORE the v0.2.6 adapter validator subprocess per Amendment 1; subprocess-invokes the unchanged v0.2.6 adapter validator; validates the trace events JSONL with strict `(event_time, event_id)` ordering and unique `event_id` and `(trace_id, span_id)`; validates the binding set with closed `expected_binding_status` and `required_decision` enums and the time-window constraint on every non-gap row; cross-checks every non-gap binding row against its resolved trace event per Amendment 4 so only `trace_gap_detected` rows may reference an absent event; staging directory plus `os.replace()` atomic publish; `--self-validate` invokes the v0.3.2 verifier against the staged package BEFORE the atomic move, removing the staging directory on self-validation failure; four runner-only refusal reasons: `adapter_validation_failed`, `trace_events_validation_failed`, `trace_binding_set_validation_failed`, `trace_binding_self_validation_failed`)
- `verify_silver_trace_binding_v0_1_0.py` — Silver v0.3.2 trace binding verifier (pure-stdlib; hash-first ordering; 22 stable failure reasons: `invalid_trace_binding_manifest`, `trace_subject_path_traversal`, `trace_subject_file_missing`, `trace_subject_hash_mismatch`, `trace_source_marked_authority`, `trace_adapter_invalid`, `trace_events_invalid`, `trace_event_duplicate`, `trace_event_time_order_invalid`, `trace_binding_set_invalid`, `trace_binding_duplicate`, `trace_binding_event_missing`, `trace_binding_field_mismatch`, `trace_binding_time_window_mismatch`, `trace_report_invalid`, `trace_report_binding_mismatch`, `trace_warning_downgrade`, `trace_report_status_mismatch`, `trace_report_count_mismatch`, `trace_limitations_missing`, `trace_non_claims_missing`, `trace_overclaim`; never emits the four runner-only refusal codes; Amendment 1 places `trace_source_marked_authority` BEFORE `trace_adapter_invalid` so a tampered adapter with `source_is_trust_authority: true` is always attributed to the specific reason; Amendment 2 places `trace_warning_downgrade` BEFORE the generic `trace_report_status_mismatch` so downgrades of `bound_with_warning` / `trace_gap_detected` / `out_of_scope_for_trace_binding` to `bound` are always attributed to the more specific reason; path traversal is checked BEFORE exact subject-path equality; limitations and non-claims emptiness checks are reserved for the dedicated `trace_limitations_missing` and `trace_non_claims_missing` reasons; recursive overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 22 forbidden positive tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance`)
- `build_silver_adapter_pilot_v0_1_0.py` — Silver v0.3.3 adapter pilot package runner (pure-stdlib; structural trust-authority pre-check BEFORE the v0.2.6 adapter validator subprocess; subprocess-invokes the unchanged v0.2.6 adapter validator on `--adapter`; validates the OpenTelemetry-shaped source-export JSONL with strict `(span.start_time, export_record_id)` ordering, unique `export_record_id`, unique `(trace_id, span_id)`, closed `export_format = "proofrail.simulated_otel_trace_export.v0.1"`, closed `proofrail.decision` enum, and all required `span.attributes["proofrail.*"]` fields; validates the normalization map under a tiny mapping language admitting only `<source.dot.path>` and `"constant:<literal>"` values; resolves dot paths using LONGEST-PREFIX KEY MATCHING at each step so OpenTelemetry-style flat-with-dots attribute keys can be addressed without quoting; derives normalized trace events deterministically, refusing with `normalization_map_validation_failed` on any required-field shortfall; subprocess-invokes the unchanged v0.3.2 trace-binding builder with `--force --self-validate` on the normalized files; emits `silver-adapter-pilot-report.json` and `silver-adapter-pilot-manifest.json` with exactly seven subjects in fixed order (adapter / source export / normalization map / normalized trace events / normalized trace claim bindings / nested v0.3.2 manifest / adapter pilot report); staging directory plus `os.replace()` atomic publish; `--self-validate` invokes the v0.3.3 verifier against the staged package BEFORE the atomic move, removing the staging directory on self-validation failure; six runner-only refusal reasons: `adapter_validation_failed`, `source_export_validation_failed`, `normalization_map_validation_failed`, `binding_set_validation_failed`, `nested_trace_binding_generation_failed`, `adapter_pilot_self_validation_failed`)
- `verify_silver_adapter_pilot_v0_1_0.py` — Silver v0.3.3 adapter pilot package verifier (pure-stdlib; hash-first ordering; 24 stable failure reasons across 25 ordered checks: `invalid_adapter_pilot_manifest` (steps 1 and 3), `adapter_pilot_subject_path_traversal`, `adapter_pilot_subject_file_missing`, `adapter_pilot_subject_hash_mismatch`, `adapter_pilot_source_marked_authority`, `adapter_pilot_adapter_invalid`, `source_export_invalid`, `source_export_duplicate`, `source_export_time_order_invalid`, `normalization_map_invalid`, `normalization_required_field_missing`, `normalized_trace_invalid`, `normalized_trace_mismatch`, `nested_trace_binding_invalid`, `nested_trace_binding_mismatch`, `adapter_pilot_report_invalid`, `adapter_pilot_report_binding_mismatch`, `adapter_pilot_report_count_mismatch`, `adapter_pilot_claim_missing`, `adapter_pilot_claim_failed`, `adapter_pilot_evidence_ref_invalid`, `adapter_pilot_limitations_missing`, `adapter_pilot_non_claims_missing`, `adapter_pilot_overclaim`; never emits the six runner-only refusal codes; four reachability orderings: (a) path traversal BEFORE exact subject-path equality; (b) adapter trust-authority pre-check BEFORE the v0.2.6 adapter validator subprocess; (c) re-derived normalized bytes BEFORE the nested v0.3.2 verifier subprocess; (d) nested v0.3.2 verifier subprocess BEFORE the nested-manifest hash cross-check pairing outer subjects [0]/[3]/[4] with nested subjects [0]/[1]/[2]; verifier-side normalization re-derivation uses byte-identical longest-prefix dot-path matching matching the runner; evidence_refs are whitelisted against the allowed package-local prefix set and rejected if absolute or containing `..`; limitations/non-claims emptiness checks are reserved for dedicated reasons; recursive overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 23 forbidden positive tokens including `runtime truth proved`, `opentelemetry conformance`, `vendor certified`, and `production approved`)
- `build_silver_challenge_withdrawal_primitives_v0_1_0.py` — Silver v0.3.4 challenge / withdrawal record primitives runner (pure-stdlib; subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier on `--target-handoff-root`, refusing with `FAIL: handoff_validation_failed: <detail>` and exit 1 on failure; structurally validates the input challenge and withdrawal records under v0.3.4 closed enums — accepting the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in `target.target_manifest_sha256` so the dedicated placeholder reason is reachable in a separately ordered verifier check per Amendment 1; runner-only refusal codes `challenge_record_validation_failed` and `withdrawal_record_validation_failed` for structural failures; performs four runner-only binding cross-checks against the parsed v0.3.0 handoff manifest (both records' `target.target_record_id` equal `handoff_id`; withdrawal's `related_challenge_record_id` equals challenge's `challenge_record_id`; monotone time-order chain; both records' `target.target_manifest_path` equal the packaged subject [0] path), refusing with `FAIL: challenge_withdrawal_binding_failed: <detail>` on mismatch; byte-copies the v0.3.0 handoff package root under `target-handoff/`; recomputes the SHA-256 of the copied target manifest and rewrites the literal placeholder in both packaged record copies to that recomputed hash label (Amendment 2: deterministic JSON output via `json.dumps(obj, indent=2, sort_keys=True)`, no byte-preservation promise); derives `silver-challenge-withdrawal-summary.json` deterministically with the seven required claims pre-baked at `status: pass` (optional `description` field admitted per Amendment 3) and the posture forced from the `withdrawal_effect → posture` closed mapping table; emits `silver-challenge-withdrawal-manifest.json` with four deterministic subjects in fixed order (target handoff manifest / challenge record / withdrawal record / summary); module constant `CHALLENGE_WITHDRAWAL_VERIFIER` exposes the verifier path for monkey-patching by the regression test (case29); with `--self-validate` invokes the v0.3.4 verifier against the staging directory BEFORE the atomic `os.replace()`, removing the staging directory and leaving the destination untouched on self-validation failure, surfacing as `FAIL: challenge_withdrawal_self_validation_failed: <detail>` and exit 1)
- `verify_silver_challenge_withdrawal_primitives_v0_1_0.py` — Silver v0.3.4 challenge / withdrawal record primitives verifier (pure-stdlib; hash-first ordering; 24 stable failure reasons across 29 ordered checks: `invalid_challenge_withdrawal_manifest` (covers steps 1–4, 6, 7, and the size-mismatch branch of 9), `challenge_withdrawal_subject_path_traversal`, `challenge_withdrawal_subject_file_missing`, `challenge_withdrawal_subject_hash_mismatch`, `nested_handoff_invalid` (covers steps 10–11), `challenge_record_invalid`, `withdrawal_record_invalid`, `challenge_record_reason_invalid`, `challenge_record_status_invalid`, `challenge_record_evidence_ref_invalid`, `withdrawal_record_reason_invalid`, `withdrawal_record_status_invalid`, `withdrawal_record_evidence_ref_invalid`, `challenge_record_target_mismatch` (consolidates placeholder-unbound + target manifest sha256 drift + target record id drift), `withdrawal_record_target_mismatch` (same three-variant consolidation), `withdrawal_record_challenge_ref_mismatch`, `challenge_withdrawal_time_order_invalid`, `challenge_withdrawal_summary_invalid` (also folds missing/failed required claims and bad summary evidence_refs), `challenge_withdrawal_summary_binding_mismatch` (also folds `challenge_status` / `withdrawal_status` / `withdrawal_effect` echo drift formerly in `_summary_status_mismatch`), `challenge_withdrawal_summary_count_mismatch` (singular), `challenge_withdrawal_posture_invalid`, `challenge_withdrawal_overclaim`, `challenge_withdrawal_limitations_missing`, `challenge_withdrawal_non_claims_missing`; never emits the five runner-only refusal codes (`handoff_validation_failed`, `challenge_record_validation_failed`, `withdrawal_record_validation_failed`, `challenge_withdrawal_binding_failed`, `challenge_withdrawal_self_validation_failed`); four reachability orderings: (a) path traversal BEFORE exact subject-path equality; (b) presence-only structural record validators BEFORE the dedicated `*_reason_invalid` / `*_status_invalid` / `*_evidence_ref_invalid` / `*_target_mismatch` checks so enum / evidence-ref / target failures never collapse into the generic `*_record_invalid` reason and the structural validators accept `sha256:TO_BE_BOUND_BY_RUNNER` as a syntactically valid value with the dedicated target-mismatch check rejecting it in packaged records; (c) subprocess-invokes the unchanged v0.3.0 handoff verifier on subject [0] with failure surfacing as `nested_handoff_invalid`; (d) posture-vs-effect, summary-binding, and count drift have distinct reasons (`challenge_withdrawal_posture_invalid`, `challenge_withdrawal_summary_binding_mismatch`, `challenge_withdrawal_summary_count_mismatch`); the overclaim guard scans every string value outside `scope_limitations` and `non_claims` for the 20+ forbidden positive tokens shared with v0.3.x including optional `claims[].description` strings; limitations and non-claims emptiness checks are reserved for dedicated reasons; evidence_refs in records are rejected if absolute or containing `..`, and evidence_refs in summary claims are additionally whitelisted against the allowed package-local prefix set)
- `build_silver_relying_party_policy_pack_v0_1_0.py` — Silver v0.3.5 relying-party policy pack runner (pure-stdlib; performs five distinct preflight checks under five stable runner-only refusal codes `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid` — the `runner_input_read_failed` exercise uses a directory path so the test is portable; byte-copies the policy pack into a staging directory; deterministically re-derives the 24-entry conformance report whose canonical-JSON byte image (`json.dumps(obj, sort_keys=True, separators=(",",":"))` with trailing newline) depends only on the policy pack; writes the 2-subject manifest (`json.dumps(obj, indent=2, sort_keys=True)` with trailing newline); atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed; on `--self-validate` failure relays the v0.3.5 verifier's own failure code UNCHANGED with NO sixth runner-only wrapper code)
- `verify_silver_relying_party_policy_pack_v0_1_0.py` — Silver v0.3.5 relying-party policy pack verifier (pure-stdlib; hash-first ordering; 24 stable failure reasons across 25 execution checks (1 manifest-integrity + 1 policy-pack-object + 22 policy-pack content structural + 1 post-structural conformance-report re-derivation, the last funneled back into `policy_pack_manifest_invalid`); non-masking ordering: the 23 ordered policy-pack checks `check_02..check_24` all run BEFORE the post-structural conformance-report byte-compare re-derivation, so any earlier structural defect surfaces with its dedicated reason (the only public emitted reason for a bundled-report disagreement is `policy_pack_manifest_invalid`); path-traversal BEFORE exact subject-path equality; never emits the five runner-only refusal codes; closed enum surface of 11 closed enums covering acceptance / challenge / withdrawal / supersession postures, verifier / issuer / revocation / freshness modes, supported signature algorithms, criteria result enums, warning treatments, related-artifact reference policy, exception / hard-stop modes; recursive overclaim guard scans every string value outside `scope_limitations`, `non_claims`, and `relying_party.contact` for 23 forbidden positive tokens including the v0.3.x shared set)

### Silver Multi-Agent Trust-Boundary Demo: `demos/silver-demo-003-multi-agent-trust-boundary/`

v0.2.5 packages the v0.2.4 multi-agent attack harness into a local demo. The committed demo directory holds only the README and walkthrough; the packager writes runtime output under `/tmp` (default `/tmp/proofrail-silver-multi-agent-demo-v0.2.5/`) and is never staged into the repository. Eight claims are derived deterministically from the v0.2.4 harness run report: `harmless_messages_proceed`, `protected_actions_require_scoped_authority`, `unauthorized_delegation_fails`, `bypass_attempts_blocked`, `revoked_authority_fails`, `out_of_scope_actions_fail`, `evidence_is_hash_verifiable`, and `no_protected_actions_executed`. The verifier re-invokes the unchanged v0.2.4 verifier on the nested manifest. See `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md` and `docs/gold/gold-boundary-v0.2.5.md`.

### Silver Evidence Source Adapter Profile: `examples/silver-evidence-source-adapters/`

v0.2.6 adds a descriptor profile for evidence sources (gateway, observability trace, SIEM, policy engine, GRC platform, native ProofRail). Six canonical static JSON descriptors live in `examples/silver-evidence-source-adapters/`. A descriptor declares how a source's events map to ProofRail-relevant evidence fields and what the source does **not** assert. Descriptors are not evidence, not trust decisions, and not certifications. The GRC platform example is explicitly framed as workflow / risk / approval evidence only, with limitations stating workflow approval is not technical enforcement and not sufficient by itself for protected-action reliance. The local structural validator `tools/silver/validate_evidence_source_adapter_v0_1_0.py` rejects out-of-set source types, missing capabilities, missing `decision_event` mapping, empty/whitespace-only strings, sample-artifact-ref path traversal, and duplicate adapter IDs in directory mode. See `docs/silver/silver-evidence-source-adapter-profile-v0.2.6.md` and `schemas/silver-evidence-source-adapter-v0.1.0.md`.

### Silver Composed Gateway Evidence Demo: `demos/silver-demo-004-composed-gateway-evidence/`

v0.2.7 composes a Silver evidence package from the v0.2.6 simulated gateway adapter descriptor and a static JSONL fixture of nine gateway events (`fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`). The committed demo directory holds only the README and walkthrough; the composer writes runtime output to `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/` and is never staged into the repository. The composer subprocess-invokes the unchanged v0.2.6 adapter validator, derives ten claims (`gateway_source_described_by_adapter`, `gateway_source_not_trust_authority`, `gateway_events_normalized`, `protected_actions_require_scoped_authority`, `unauthorized_delegation_fails`, `bypass_attempts_observed_or_blocked`, `revoked_authority_fails`, `out_of_scope_actions_fail`, `source_evidence_hash_verifiable`, `no_protected_actions_executed`), and emits `composed-gateway-evidence-report.json` plus `composed-gateway-evidence-manifest.json` with five subjects in deterministic order and a `composition` block (`source_type: "gateway"`, `source_is_trust_authority: false`, three subject paths). The verifier re-derives every claim independently and rejects wrong-but-valid evidence refs. The simulated gateway is an evidence source, not a trust authority. The composed report is not signed; v0.2.7 ships local hash anchors only. See `docs/silver/silver-composed-gateway-evidence-demo-v0.2.7.md`.

### Silver Relying-Party Acceptance Record: `demos/silver-demo-005-relying-party-acceptance/`

v0.2.8 records a single relying party's local acceptance decision over a verified v0.2.7 composed gateway evidence package. The committed demo directory holds only the README and walkthrough; the generator writes runtime output to `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/` and is never staged into the repository. The generator subprocess-invokes the unchanged v0.2.7 verifier on the supplied evidence manifest; for `--decision accepted` with a non-zero v0.2.7 verifier exit, it refuses with stderr `FAIL: evidence_verification_failed: <detail>` and exit code 1 (no partial package is written). The generator emits four files in a deterministic layout: the copied acceptance policy, the copied v0.2.7 evidence manifest under `evidence/`, an `acceptance-record.json` with `decision.status ∈ {accepted, rejected, accepted_with_exceptions}`, and an `acceptance-package-manifest.json` with three deterministic subjects (roles `acceptance_policy`, `verified_evidence_manifest`, `acceptance_record`). Three verification-related failure codes are deliberately distinct: `evidence_verification_required` (validator; record's verifier metadata missing or disagrees with policy), `evidence_verification_failed` (generator-only; never emitted by the validator), `external_evidence_verification_failed` (validator with `--evidence-package-root`; re-invocation of the v0.2.7 verifier fails or the external manifest sha256 disagrees with the record's). The validator runs 22 ordered checks against a 21-reason stable set and never emits `evidence_verification_failed`. A relying-party acceptance record is not a Gold certificate, regulator approval, third-party audit, or legal acceptance instrument. v0.2.8 records acceptance context. It does not execute acceptance governance. See `docs/silver/silver-relying-party-acceptance-record-v0.2.8.md`.

### Silver Revocation/Challenge Drill: `demos/silver-demo-006-revocation-challenge-drill/`

v0.2.9 layers a deterministic, local, post-acceptance review drill over a v0.2.8 relying-party acceptance record. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/` and is never staged into the repository. The runner subprocess-invokes the unchanged v0.2.8 acceptance validator on the supplied package manifest, refusing with `FAIL: acceptance_package_validation_failed: <detail>` and exit 1 when v0.2.8 validation fails, and refusing with `FAIL: review_fixture_insufficient: <detail>` and exit 1 when the review-events fixture contains no within-window challenges or no revocation signals. The runner stages output under a sibling `<output-dir>.staging.<pid>` directory and atomically replaces the destination only after successful generation. The drill package layout byte-copies the full v0.2.8 acceptance subdirectory into `acceptance-package/` and adds `review-events.jsonl`, `revocation-challenge-drill-report.json`, and `revocation-challenge-drill-manifest.json`. Three deterministic manifest subjects bind the nested v0.2.8 acceptance package manifest, the review-events JSONL, and the drill report. The drill report's `base_acceptance.*` block is derived from the nested record (acceptance_record_id, decision_status, purpose_id, policy id/version, package-manifest sha256, challenge window). The `recommended_local_posture` is drawn from the closed set `{acceptance_stands_for_demo_scope, acceptance_requires_review_before_reuse, acceptance_not_reusable_without_governed_review}`. The verifier (22 stable failure reasons; runner-only refusal codes are never emitted) parses the drill report before checking the review-events file hash, splits target mismatches by event type into `review_event_target_mismatch` and `revocation_signal_target_mismatch`, and checks `challenge_window_classification_mismatch` before `challenge_within_window_missing`. The v0.2.9 release is unsigned: it ships local hash anchors only. A revocation/challenge drill is not a Gold certificate, regulator approval, third-party audit, legal revocation, dispute resolution, or acceptance governance workflow. v0.2.9 records review triggers; it does not decide their merits. See `docs/silver/silver-revocation-challenge-drill-v0.2.9.md`.

### Silver Acceptance Handoff: `demos/silver-demo-007-acceptance-handoff/`

v0.3.0 composes the completed v0.2.7 / v0.2.8 / v0.2.9 Silver acceptance chain into a single portable, hash-anchored local handoff artifact. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-acceptance-handoff-v0.3.0/` and is never staged into the repository. The runner subprocess-invokes the unchanged v0.2.7 verifier, v0.2.8 acceptance validator, and v0.2.9 drill verifier (the latter two WITHOUT `--evidence-package-root` so v0.3.0 owns the cross-copy chain binding); refuses with `FAIL: composed_evidence_validation_failed | acceptance_package_validation_failed | drill_package_validation_failed: <detail>` and exit 1 on nested-validator failure. The handoff package layout byte-copies the three nested package roots under fixed top-level directories `composed-gateway-evidence/`, `acceptance-package/`, and `revocation-challenge-drill/`, plus `silver-acceptance-handoff-summary.json` and `silver-acceptance-handoff-manifest.json`. The manifest holds exactly four deterministic subjects in fixed order: the composed-gateway-evidence manifest, the acceptance-package manifest, the drill manifest, and the handoff summary. The runner performs four v0.3.0-owned chain-binding cross-checks: (a) top-level composed-gateway-evidence manifest sha256 = nested v0.2.8 record `evidence_package.manifest_sha256`; (b) top-level acceptance-package manifest sha256 = nested v0.2.9 drill report `base_acceptance.acceptance_package_manifest_sha256`; (c) inner copy `acceptance-package/evidence/composed-gateway-evidence-manifest.json` sha256 = subject [0]; (d) inner copy `revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json` sha256 = subject [1]. The v0.3.0 verifier (17 stable failure reasons including `handoff_chain_binding_mismatch`, `handoff_posture_downgrade`, and `handoff_overclaim`; never emits the runner-only refusal codes) re-runs the nested validators and re-derives the four chain-binding checks independently. The handoff posture model uses ordered severity ranks (rank 0 `for_demo_scope` < rank 1 `review_required_before_reuse` < rank 2 `not_reusable_without_governed_review`); any handoff posture weaker than the rank implied by the nested v0.2.9 drill posture is rejected as `handoff_posture_downgrade`; unknown drill or handoff postures are rejected as `handoff_posture_invalid`. A recursive overclaim guard scans every string value in the summary outside `scope_limitations` and `non_claims` for 15 forbidden positive tokens (`certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`). With `--self-validate` the runner invokes the v0.3.0 verifier against the staging directory BEFORE the atomic move and removes the staging directory on self-validation failure, leaving the destination untouched. The v0.3.0 release is unsigned: it ships local hash anchors only. v0.3.0 packages already-verified Silver evidence. It does not extend the substance of what that evidence asserts; it is not a certificate, Gold conformance, regulator approval, auditor approval, legal acceptance, or a transfer of reliance, and the `recommended_handoff_posture` is descriptive only. See `docs/silver/silver-acceptance-handoff-v0.3.0.md`.

### Silver Trace Binding Profile: `demos/silver-demo-009-trace-binding-profile/`

v0.3.2 binds protected-action claims to deterministic trace event evidence. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-trace-binding-v0.3.2/` and is never staged into the repository. The runner subprocess-invokes the unchanged v0.2.6 adapter validator against the simulated observability-trace adapter descriptor (`examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json`), validates the 8-event JSONL trace fixture (`fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl`) under strict `(event_time, event_id)` ordering / unique `event_id` / unique `(trace_id, span_id)` / closed `decision` enum, validates the 9-row binding set (`fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json`) under closed `expected_binding_status` and `required_decision` enums, and cross-checks every non-gap binding row against its resolved trace event so only `trace_gap_detected` rows may reference an absent event. The trace binding report is derived deterministically: `binding_summary` counts are recomputed from `bindings[].binding_status` and never hand-authored. The manifest holds exactly four deterministic subjects in fixed order: `adapter/observability-trace-simulated-v0.2.6.json`, `trace-events.jsonl`, `trace-claim-bindings.json`, `silver-trace-binding-report.json`. With `--self-validate` the runner invokes the v0.3.2 verifier against the staging directory BEFORE the atomic `os.replace()` and removes the staging directory on self-validation failure, so failed runs leave no partial output. The v0.3.2 verifier (22 stable failure reasons; never emits the four runner-only refusal codes) enforces two reachability orderings: `trace_source_marked_authority` is checked BEFORE the v0.2.6 adapter validator subprocess (Amendment 1), and `trace_warning_downgrade` is checked BEFORE the generic `trace_report_status_mismatch` (Amendment 2) so downgrades from `bound_with_warning` / `trace_gap_detected` / `out_of_scope_for_trace_binding` to `bound` are always attributed to the more specific reason. Path traversal is checked BEFORE exact subject-path equality. The overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 22 forbidden positive tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, and `opentelemetry conformance`. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority; `source_event_ref` values are opaque labels and v0.3.2 does not cross-validate them against any external package. The v0.3.2 release ships local hash anchors only; it is not signed, not OpenTelemetry conformance, not a Gold certificate, not regulator/auditor/legal acceptance, and does not authorize production reliance. See `docs/silver/silver-trace-binding-profile-v0.3.2.md`.

### Silver Adapter Pilot Package: `demos/silver-demo-010-adapter-pilot-package/`

v0.3.3 pilots a local external-evidence adapter flow that normalizes an OpenTelemetry-shaped local source-export fixture into v0.3.2 trace-binding inputs. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-adapter-pilot-v0.3.3/` and is never staged into the repository. The runner consumes the unchanged v0.2.6 simulated observability-trace adapter (`examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json`), the 8-line OpenTelemetry-shaped source-export fixture (`fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl`, `export_format: "proofrail.simulated_otel_trace_export.v0.1"`), the declarative normalization map (`fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json`, mapping language is `<source.dot.path>` and `constant:<literal>` only), and the unchanged v0.3.2 trace claim binding set (`fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json`). Dot-path resolution uses LONGEST-PREFIX KEY MATCHING at each step so OpenTelemetry-style flat-with-dots attribute keys (e.g. `proofrail.event_id`) can be addressed without quoting. The runner subprocess-invokes the unchanged v0.2.6 adapter validator and then the unchanged v0.3.2 trace-binding builder + verifier on the normalized files. The manifest holds exactly seven deterministic subjects in fixed order: `adapter/observability-trace-simulated-v0.2.6.json`, `source/source-otel-trace-export.jsonl`, `normalization/normalization-map.json`, `normalized/trace-events.jsonl`, `normalized/trace-claim-bindings.json`, `trace-binding/silver-trace-binding-manifest.json`, `silver-adapter-pilot-report.json`. With `--self-validate` the runner invokes the v0.3.3 verifier against the staging directory BEFORE the atomic `os.replace()` and removes the staging directory on self-validation failure, so failed runs leave no partial output and no staging sibling. The v0.3.3 verifier (24 stable failure reasons across 25 ordered checks; never emits the six runner-only refusal codes) enforces four reachability orderings: path traversal BEFORE exact subject-path equality; adapter trust-authority pre-check BEFORE the v0.2.6 adapter validator subprocess; re-derived normalized bytes BEFORE the nested v0.3.2 verifier subprocess; nested v0.3.2 verifier subprocess BEFORE the nested-manifest hash cross-check (outer subjects [0]/[3]/[4] vs nested subjects [0]/[1]/[2]). The verifier rejects wrong-but-valid evidence_refs that point outside the allowed package-local prefix set. The overclaim guard scans every string value outside `scope_limitations` and `non_claims` for 23 forbidden positive tokens including `runtime truth proved`. The simulated observability-trace adapter is an evidence-source descriptor, not a trust authority; `source_event_ref` values are carried unchanged through normalization as opaque labels and v0.3.3 does not cross-validate them against any external package. The v0.3.3 release ships local hash anchors only; it is not signed, not OpenTelemetry conformance, not a vendor certification, not a production integration, not a Gold certificate, not regulator/auditor/legal acceptance, and does not authorize production reliance. See `docs/silver/silver-adapter-pilot-package-v0.3.3.md`.

### Silver Challenge / Withdrawal Record Primitives: `demos/silver-demo-011-challenge-withdrawal-primitives/`

v0.3.4 introduces two deterministic local Silver evidence record primitives — a *challenge record* and a *withdrawal record* — and hash-anchors them to an unchanged v0.3.0 Silver acceptance handoff target inside a single packaged manifest. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/` and is never staged into the repository. The runner consumes the v0.3.0 acceptance handoff package root (`/tmp/proofrail-silver-acceptance-handoff-v0.3.0/`), the challenge record fixture (`fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json`, 10-value `challenge_reason` enum, 4-value `challenge_status` enum), and the withdrawal record fixture (`fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json`, 7-value `withdrawal_reason` enum, 4-value `withdrawal_status` enum, 4-value `withdrawal_effect` enum). The input fixtures may carry the literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in `target.target_manifest_sha256`; the runner recomputes the SHA-256 of the copied target handoff manifest and rewrites the packaged record copies to that label (Amendment 1 pre-bind / post-bind discipline). The runner subprocess-invokes the unchanged v0.3.0 acceptance handoff verifier on the target manifest, performs four binding cross-checks (both records' `target.target_record_id` equal `handoff_id`; withdrawal cites the challenge; monotone time-order chain `target.generated_at ≤ challenge.filed_at ≤ withdrawal.recorded_at ≤ withdrawal.effective_at`; both records' `target.target_manifest_path` equal the packaged subject [0] path), byte-copies the v0.3.0 handoff package root under `target-handoff/`, derives `silver-challenge-withdrawal-summary.json` deterministically with the seven required claims (`target_handoff_verified`, `challenge_record_valid`, `withdrawal_record_valid`, `challenge_and_withdrawal_target_same_handoff`, `withdrawal_cites_challenge`, `time_order_valid`, `no_adjudication_claimed`) pre-baked at `status: pass`, and emits `silver-challenge-withdrawal-manifest.json` with four deterministic subjects in fixed order (target handoff manifest / challenge record / withdrawal record / summary). The `summary.posture` is derived from `withdrawal_effect` via the closed mapping table: `local_reuse_paused_for_review`, `acceptance_reuse_blocked_pending_review` → `challenged_with_local_reuse_paused_for_review`; `local_reliance_withdrawn_for_review` → `challenged_with_local_reliance_withdrawn_for_review`; `record_superseded` → `record_superseded`. With `--self-validate` the runner invokes the v0.3.4 verifier against the staging directory BEFORE the atomic `os.replace()` and removes the staging directory on self-validation failure, so failed runs leave no partial output and no staging sibling. The v0.3.4 verifier (24 stable failure reasons across 25 ordered checks; never emits the five runner-only refusal codes) enforces four reachability orderings: path traversal BEFORE exact subject-path equality; structural record parse BEFORE the dedicated placeholder check; nested v0.3.0 verifier subprocess on subject [0]; and posture-vs-effect as a dedicated reason distinct from the status-echo check. The v0.3.4 release ships local hash anchors only; it is not signed, not an adjudication, not a legal revocation, not a target-handoff certification, not a Gold certificate, not regulator/auditor/legal acceptance, and does not authorize production reliance. See `docs/silver/silver-challenge-withdrawal-primitives-v0.3.4.md`.

### Silver Relying-Party Policy Pack: `demos/silver-demo-012-relying-party-policy-pack/`

v0.3.5 introduces a deterministic local Silver evidence primitive — a hand-authored *relying-party policy pack* paired with a byte-for-byte re-derivable *conformance report* inside a single 2-subject packaged manifest. The committed demo directory holds only the README and walkthrough; the runner writes runtime output to `/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/` and is never staged into the repository. The runner consumes the canonical fixture (`fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json`) plus three additional passing variants exercising the closed enum surface. The runner performs five distinct preflight checks under five stable runner-only refusal codes (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`), byte-copies the policy pack into a staging directory, deterministically re-derives a 24-entry conformance report (canonical JSON `sort_keys=True, separators=(",",":")` with trailing newline) whose byte image depends only on the policy pack, writes the 2-subject manifest (subjects: `policy-pack.json`, `silver-relying-party-policy-pack-conformance-report.json`), and atomically `os.replace()`s the staging directory into place only after staging build and (optional) self-validation succeed. On `--self-validate` failure the runner relays the v0.3.5 verifier's own failure code UNCHANGED with **no** sixth runner-only wrapper code (rel01 exercise asserts this explicitly). The v0.3.5 verifier (24 stable failure reasons across 25 execution checks (1 manifest-integrity + 1 policy-pack-object + 22 policy-pack content structural + 1 post-structural conformance-report re-derivation, the last funneled back into `policy_pack_manifest_invalid`); never emits the five runner-only refusal codes) enforces non-masking ordering: the 23 ordered policy-pack checks `check_02..check_24` all run BEFORE the post-structural conformance-report byte-compare re-derivation so any earlier structural defect surfaces with its dedicated reason; the only public emitted reason for a bundled-report disagreement is `policy_pack_manifest_invalid`; path-traversal is checked BEFORE exact subject-path equality. The closed enum surface holds 11 closed enums covering acceptance / challenge / withdrawal / supersession postures (3 values), verifier / issuer / revocation / freshness modes, supported signature algorithms, criteria result enums (4 values), warning treatments, related-artifact reference policy, and exception / hard-stop modes. The overclaim guard scans every string value outside `scope_limitations`, `non_claims`, and `relying_party.contact` for the v0.3.x shared set of 23 forbidden positive tokens including `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`, `gold-ready`, `gold ready`, `gold_ready`, `runtime proof`, `authoritative trace`, `runtime truth proved`, `vendor certified`, `production approved`. The regression test (`tests/test_silver_relying_party_policy_pack_v0_3_5.sh`) holds 47 numbered exercises: 4 positive-path (PP1..PP4), 24 canonical verifier reasons (case01..case24), 11 duplicate manifest-invalid exercises (dup01..dup11) confirming reason stability under multiple distinct mutations all sharing `invalid_relying_party_policy_pack_manifest`, 5 runner-only refusals (ro1..ro5), 1 runner-relay-of-verifier (rel01), 1 taxonomy gate (TG1) enforcing that every reason-shaped token in v0.3.5 source belongs to the 24-reason verifier set ∪ 5 runner-only set ∪ documented allow-list, and 1 scoped sha256 snapshot (SS) over the committed v0.3.5 source paths. The v0.3.5 release ships local hash anchors only; it is not signed, does not approve, audit, or certify the policy pack, does not adjudicate any specific challenge / withdrawal / supersession event against it, does not evaluate any specific upstream Silver evidence against it, does not transfer reliance, and does not constitute Gold readiness, regulator approval, auditor approval, legal acceptance, compliance certification, or production authorization. See `docs/silver/silver-relying-party-policy-pack-v0.3.5.md`.

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
