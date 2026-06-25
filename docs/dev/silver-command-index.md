# ProofRail — Silver Command Index

Full per-release command matrix for ProofRail Bronze + Silver releases
through v0.3.7. Preserved verbatim from the prior `CLAUDE.md` Common
Commands section. The compact operating index (`CLAUDE.md`) only
references the essentials; everything else is here.

For release-by-release architecture / scope / non-claims, see
`docs/dev/silver-release-index.md`. For per-release release notes, see
`docs/silver/silver-<release-slug>-v0.x.y.md` and `docs/gold/gold-boundary-v0.2.5.md`.

## Setup + cross-version essentials

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
python -m pytest tests/test_proofrail_claim.py

# Verify the entire Bronze + Silver chain (regenerates Bronze runtime files)
make verify-silver-all
```

## Full regression-test list

```bash
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
bash tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh
bash tests/test_silver_registry_lite_v0_3_7.sh
```

## Bronze claim + evidence

```bash
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
```

## Silver v0.1.0 (signed bundle assertion)

```bash
# Run Silver demo (end-to-end: Bronze claim → bundle manifest → sign → verify)
make silver-demo-001
make verify-silver-demo-001
make verify-silver-revocation-demo-001
make verify-silver-report-demo-001

# Export and verify independent Silver verification package (Demo 002)
make export-independent-silver-package-demo-002
make verify-independent-silver-demo-002

# Silver tools standalone
python3 tools/silver/generate_demo_issuer_v0_1_0.py <silver-demo-root> --force
python3 tools/silver/sign_bundle_manifest_v0_1_0.py <silver-demo-root> --private-key <key.pem> --output <assertion.yaml>
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py <assertion.yaml> <trust-policy.yaml> --silver-root <silver-root> --bronze-package-root <bronze-root> [--revocation-list <revocation-list.yaml>] [--report <report.json>]
python3 tools/silver/validate_silver_verification_report_v0_1_0.py <report.json>
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py <silver-demo-root> [--revoke-assertion <id>] [--revoke-issuer-key <issuer_id:key_id>] [--revoke-bundle-sha256 <hash>]
```

## Silver v0.2.0 / v0.2.1 (relying-party profile conformance)

```bash
# Silver profile conformance
make validate-silver-profile-demo-001
make validate-silver-profile-demo-002

# Silver v0.2.1 profile conformance
make validate-silver-profile-v0-2-1-demo-001
make validate-silver-profile-v0-2-1-demo-002
make verify-silver-profile-v0-2-1
make verify-silver-profile-examples-v0-2-1

python3 tools/silver/validate_silver_profile_v0_2_0.py --profile-mode <mode> --verification-report <report.json> [--package-manifest <manifest.yaml>] [--output <conformance.json>]
python3 tools/silver/validate_silver_profile_v0_2_1.py --profile-mode <mode> --verification-report <report.json> [--package-manifest <manifest.yaml>] [--output <conformance.json>]
python3 tools/silver/export_independent_verification_package_v0_2_1.py --bronze-root <bronze-root> --silver-root <silver-root> --output <output-dir> --force
```

## Silver v0.2.2 (verifier output attestation)

```bash
make generate-silver-verifier-attestor-demo-001
make sign-silver-verifier-attestation-demo-001
make verify-silver-verifier-attestation-demo-001
make verify-silver-attestation-v0-2-2

python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py --output-root <dir> --attestor-id <id> --key-id <key-id> --force
python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py --verification-report <report.json> --conformance-report <conformance.json> --private-key <key.pem> --attestor-id <id> --attestor-version <version> --key-id <key-id> --output <attestation.json>
python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py --attestation <attestation.json> --trust-policy <trust-policy.yaml>
```

## Silver v0.2.3 (multi-principal authority)

```bash
make validate-silver-authority-fixtures-v0-2-3
make verify-silver-authority-v0-2-3
bash tests/test_silver_multi_principal_authority_v0_2_3.sh

python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py --fixture <fixture.yaml>
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py --fixture <fixture.yaml> --request <request.json> --decision-time <ISO-8601> --output <report.json>
```

## Silver v0.2.4 (multi-agent attack harness)

```bash
make run-silver-multi-agent-harness-v0-2-4
make verify-silver-multi-agent-harness-v0-2-4
bash tests/test_silver_multi_agent_attack_harness_v0_2_4.sh

python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py --script <harness-script.yaml> --authority-fixture <authority-fixture.yaml> --output-dir <output-dir> [--force]
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest <harness-evidence-manifest.json>
```

## Silver v0.2.5 (multi-agent trust-boundary demo package)

```bash
make run-silver-multi-agent-demo-v0-2-5
make verify-silver-multi-agent-demo-v0-2-5
bash tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh

python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py --demo-root <demo-dir> --harness-script <harness-script.yaml> --authority-fixture <authority-fixture.yaml> --output-dir <output-dir> [--generated-at <ISO-8601>] [--force]
python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py --package-manifest <demo-package-manifest.json>
```

## Silver v0.2.6 (evidence source adapter descriptors)

```bash
make validate-silver-evidence-source-adapters-v0-2-6
make verify-silver-evidence-source-adapter-v0-2-6
bash tests/test_silver_evidence_source_adapter_v0_2_6.sh

python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py --adapter <adapter.json>
python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py --examples-dir <dir>
```

## Silver v0.2.7 (composed gateway evidence)

```bash
make run-silver-composed-gateway-demo-v0-2-7
make verify-silver-composed-gateway-demo-v0-2-7
bash tests/test_silver_composed_gateway_evidence_v0_2_7.sh

python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py --demo-root <demo-dir> --adapter <adapter.json> --gateway-events <events.jsonl> --output-dir <output-dir> [--generated-at <ISO-8601>] [--force]
python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py --manifest <composed-gateway-evidence-manifest.json>
```

## Silver v0.2.8 (relying-party acceptance record)

```bash
make run-silver-relying-party-acceptance-demo-v0-2-8
make verify-silver-relying-party-acceptance-demo-v0-2-8
bash tests/test_silver_relying_party_acceptance_record_v0_2_8.sh

python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py --policy <policy.json> --evidence-manifest <composed-gateway-evidence-manifest.json> --decision <accepted|rejected|accepted_with_exceptions> --purpose <purpose-id> --decision-maker <id> --generated-at <ISO-8601> --challenge-closes-at <ISO-8601> --output-dir <output-dir> [--force] [--challenge-opens-at <ISO-8601>] [--challenge-contact <id>] [--rejection-reason <text>] [--exception severity:description:effect_on_scope] [--scope-limitation <text>] [--non-claim <text>] [--record-id <id>] [--package-id <id>] [--self-validate]
python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py --manifest <acceptance-package-manifest.json> [--evidence-package-root <v0.2.7-package-dir>]
```

## Silver v0.2.9 (revocation / challenge drill)

```bash
make run-silver-revocation-challenge-drill-v0-2-9
make verify-silver-revocation-challenge-drill-v0-2-9
bash tests/test_silver_revocation_challenge_drill_v0_2_9.sh

python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py --acceptance-manifest <v0.2.8-acceptance-package-manifest.json> --review-events <review-events.jsonl> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--evidence-package-root <v0.2.7-package-dir>] [--self-validate]
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py --manifest <revocation-challenge-drill-manifest.json> [--evidence-package-root <v0.2.7-package-dir>]
```

## Silver v0.3.0 (acceptance handoff)

```bash
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
bash tests/test_silver_acceptance_handoff_v0_3_0.sh

python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py --composed-evidence-manifest <v0.2.7-composed-gateway-evidence-manifest.json> --acceptance-manifest <v0.2.8-acceptance-package-manifest.json> --drill-manifest <v0.2.9-revocation-challenge-drill-manifest.json> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--handoff-id <id>] [--handoff-purpose <text>] [--recipient-role <text>] [--source-package-family <text>] [--self-validate]
python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py --manifest <silver-acceptance-handoff-manifest.json>
```

## Silver v0.3.1 (handoff inspector + Gold gap inventory)

```bash
make run-silver-handoff-inspection-v0-3-1
make verify-silver-handoff-inspection-v0-3-1
bash tests/test_silver_handoff_inspector_v0_3_1.sh

python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py --handoff-manifest <v0.3.0-silver-acceptance-handoff-manifest.json> --requirement-set <gold-boundary-requirements.json> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--inspection-id <id>] [--self-validate]
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py --manifest <silver-handoff-inspection-manifest.json>
python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py --validate-requirement-set <gold-boundary-requirements.json>
```

## Silver v0.3.2 (trace binding profile)

```bash
make run-silver-trace-binding-v0-3-2
make verify-silver-trace-binding-v0-3-2
bash tests/test_silver_trace_binding_v0_3_2.sh

python3 tools/silver/build_silver_trace_binding_v0_1_0.py --adapter <observability-trace-adapter.json> --trace-events <trace-events.jsonl> --bindings <trace-claim-bindings.json> --trace-binding-report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_trace_binding_v0_1_0.py --manifest <silver-trace-binding-manifest.json>
```

## Silver v0.3.3 (adapter pilot package)

```bash
make run-silver-adapter-pilot-v0-3-3
make verify-silver-adapter-pilot-v0-3-3
bash tests/test_silver_adapter_pilot_v0_3_3.sh

python3 tools/silver/build_silver_adapter_pilot_v0_1_0.py --adapter <observability-trace-adapter.json> --source-export <source-otel-trace-export.jsonl> --normalization-map <normalization-map.json> --bindings <trace-claim-bindings.json> --adapter-pilot-report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py --manifest <silver-adapter-pilot-manifest.json>
```

## Silver v0.3.4 (challenge / withdrawal record primitives)

```bash
make run-silver-acceptance-handoff-v0-3-0
make run-silver-challenge-withdrawal-primitives-v0-3-4
make verify-silver-challenge-withdrawal-primitives-v0-3-4
bash tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh

python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py --target-handoff-root <v0.3.0-handoff-dir> --challenge-record <challenge-record.json> --withdrawal-record <withdrawal-record.json> --generated-at <ISO-8601> --output-dir <output-dir> [--manifest-id <id>] [--summary-id <id>] [--force] [--self-validate]
python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py --manifest <silver-challenge-withdrawal-manifest.json>
```

## Silver v0.3.5 (relying-party policy pack)

```bash
make run-silver-relying-party-policy-pack-v0-3-5
make verify-silver-relying-party-policy-pack-v0-3-5
bash tests/test_silver_relying_party_policy_pack_v0_3_5.sh

python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py --policy-pack <policy-pack.json> --manifest-id <id> --report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py --manifest <silver-relying-party-policy-pack-manifest.json>
```

## Silver v0.3.6 (control crosswalk + protected action catalog)

```bash
make run-silver-control-crosswalk-protected-action-catalog-v0-3-6
make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
bash tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh

python3 tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py --input-pack <control-pack.json> --manifest-id <id> --report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py --manifest <silver-control-crosswalk-protected-action-catalog-manifest.json>
```

## Silver v0.3.7 (registry lite)

```bash
make run-silver-registry-lite-v0-3-7
make verify-silver-registry-lite-v0-3-7
bash tests/test_silver_registry_lite_v0_3_7.sh

python3 tools/silver/build_silver_registry_lite_v0_1_0.py --input-registry <registry-lite.json> --manifest-id <id> --report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/silver/verify_silver_registry_lite_v0_1_0.py --manifest <silver-registry-lite-manifest.json>
```

## Gold v0.4.0 (Minimal Gold Governed Reliance Demo)

```bash
make run-gold-governed-reliance-v0-4-0
make verify-gold-governed-reliance-v0-4-0
make verify-gold-all
bash tests/test_gold_governed_reliance_v0_4_0.sh

python3 tools/gold/build_gold_governed_reliance_demo_v0_1_0.py --input-package <governed-reliance-scenarios.json> --manifest-id <id> --report-id <id> --generated-at <ISO-8601> --output-dir <output-dir> [--force] [--self-validate]
python3 tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py --manifest <gold-governed-reliance-package-manifest.json>
```
