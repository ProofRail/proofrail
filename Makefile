.PHONY: generate-bronze-demo-001b
generate-bronze-demo-001b:
	python3 tools/claims/generate_bronze_claim_v0_1_2.py demos/composed-bronze-demo-001
	python3 tools/claims/validate_bronze_claim_v0_1_2.py demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml

.PHONY: validate-bronze-demo-001b
validate-bronze-demo-001b:
	python3 tools/claims/validate_bronze_claim_v0_1_2.py demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml
	bash tests/test_bronze_claim_v0_1_2.sh

.PHONY: verify-bronze-demo-001b-evidence
verify-bronze-demo-001b-evidence:
	python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py \
		demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml \
		demos/composed-bronze-demo-001

.PHONY: bundle-bronze-demo-001b
bundle-bronze-demo-001b:
	python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py demos/composed-bronze-demo-001
	python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml demos/composed-bronze-demo-001

.PHONY: verify-bronze-demo-001b-bundle
verify-bronze-demo-001b-bundle:
	python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml demos/composed-bronze-demo-001
	bash tests/test_bronze_evidence_bundle_v0_1_3.sh

.PHONY: silver-demo-001
silver-demo-001:
	python3 tools/claims/generate_bronze_claim_v0_1_2.py demos/composed-bronze-demo-001
	python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml demos/composed-bronze-demo-001
	python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py demos/composed-bronze-demo-001
	python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml demos/composed-bronze-demo-001
	python3 tools/silver/generate_demo_issuer_v0_1_0.py demos/silver-demo-001 --force
	python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 --force
	python3 tools/silver/sign_bundle_manifest_v0_1_0.py demos/silver-demo-001 --private-key demos/silver-demo-001/runtime/issuer-a/private-key.pem --output demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml
	python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml --silver-root demos/silver-demo-001 --bronze-package-root demos/composed-bronze-demo-001 --revocation-list demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml --report demos/silver-demo-001/runtime/verification-report.json
	python3 tools/silver/validate_silver_verification_report_v0_1_0.py demos/silver-demo-001/runtime/verification-report.json

.PHONY: verify-silver-demo-001
verify-silver-demo-001:
	bash tests/test_silver_signed_bundle_assertion_v0_1_0.sh
	bash tests/test_silver_revocation_list_v0_1_0.sh
	bash tests/test_silver_verification_report_v0_1_0.sh

.PHONY: verify-silver-revocation-demo-001
verify-silver-revocation-demo-001:
	bash tests/test_silver_revocation_list_v0_1_0.sh

.PHONY: verify-silver-report-demo-001
verify-silver-report-demo-001:
	bash tests/test_silver_verification_report_v0_1_0.sh

.PHONY: export-independent-silver-package-demo-002
export-independent-silver-package-demo-002:
	python3 tools/silver/export_independent_verification_package_v0_1_0.py --bronze-root demos/composed-bronze-demo-001 --silver-root demos/silver-demo-001 --output demos/silver-demo-002-independent-verifier/runtime/package --force

.PHONY: verify-independent-silver-demo-002
verify-independent-silver-demo-002:
	bash tests/test_independent_silver_verifier_v0_1_0.sh

.PHONY: validate-silver-profile-demo-001
validate-silver-profile-demo-001:
	python3 tools/silver/validate_silver_profile_v0_2_0.py --profile-mode silver.base --verification-report demos/silver-demo-001/runtime/verification-report.json --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.0.json

.PHONY: validate-silver-profile-demo-002
validate-silver-profile-demo-002:
	bash tests/test_silver_profile_v0_2_0.sh

.PHONY: validate-silver-profile-v0-2-1-demo-001
validate-silver-profile-v0-2-1-demo-001:
	python3 tools/silver/validate_silver_profile_v0_2_1.py --profile-mode silver.base \
	  --verification-report demos/silver-demo-001/runtime/verification-report.json \
	  --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.1.json

.PHONY: validate-silver-profile-v0-2-1-demo-002
validate-silver-profile-v0-2-1-demo-002:
	bash tests/test_silver_profile_v0_2_1.sh

.PHONY: verify-silver-profile-v0-2-1
verify-silver-profile-v0-2-1:
	bash tests/test_silver_profile_v0_2_1.sh

.PHONY: verify-silver-profile-examples-v0-2-1
verify-silver-profile-examples-v0-2-1:
	bash tests/test_silver_profile_examples_v0_2_1.sh

.PHONY: generate-silver-verifier-attestor-demo-001
generate-silver-verifier-attestor-demo-001:
	python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
	  --output-root demos/silver-demo-001/runtime/verifier-b \
	  --attestor-id proofrail-demo-verifier-b \
	  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
	  --force

.PHONY: sign-silver-verifier-attestation-demo-001
sign-silver-verifier-attestation-demo-001:
	python3 tools/silver/validate_silver_profile_v0_2_1.py --profile-mode silver.base \
	  --verification-report demos/silver-demo-001/runtime/verification-report.json \
	  --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.1.json
	python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
	  --verification-report demos/silver-demo-001/runtime/verification-report.json \
	  --conformance-report demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.1.json \
	  --private-key demos/silver-demo-001/runtime/verifier-b/attestor-private-key.pem \
	  --attestor-id proofrail-demo-verifier-b \
	  --attestor-version v0.2.2-demo \
	  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
	  --output demos/silver-demo-001/runtime/silver-verifier-output-attestation-v0.1.0.json

.PHONY: verify-silver-verifier-attestation-demo-001
verify-silver-verifier-attestation-demo-001:
	python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
	  --attestation demos/silver-demo-001/runtime/silver-verifier-output-attestation-v0.1.0.json \
	  --trust-policy demos/silver-demo-001/runtime/verifier-b/attestation-trust-policy.yaml

.PHONY: verify-silver-attestation-v0-2-2
verify-silver-attestation-v0-2-2:
	bash tests/test_silver_verifier_output_attestation_v0_1_0.sh

.PHONY: validate-silver-authority-fixtures-v0-2-3
validate-silver-authority-fixtures-v0-2-3:
	python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
	  --fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml

.PHONY: verify-silver-authority-v0-2-3
verify-silver-authority-v0-2-3:
	bash tests/test_silver_multi_principal_authority_v0_2_3.sh

.PHONY: run-silver-multi-agent-harness-v0-2-4
run-silver-multi-agent-harness-v0-2-4:
	python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
	  --script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
	  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
	  --output-dir /tmp/proofrail-silver-multi-agent-harness-v0.2.4 \
	  --force
	python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-multi-agent-harness-v0.2.4/harness-evidence-manifest.json

.PHONY: verify-silver-multi-agent-harness-v0-2-4
verify-silver-multi-agent-harness-v0-2-4:
	bash tests/test_silver_multi_agent_attack_harness_v0_2_4.sh

.PHONY: run-silver-multi-agent-demo-v0-2-5
run-silver-multi-agent-demo-v0-2-5:
	python3 tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py \
	  --demo-root demos/silver-demo-003-multi-agent-trust-boundary \
	  --harness-script fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml \
	  --authority-fixture fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml \
	  --output-dir /tmp/proofrail-silver-multi-agent-demo-v0.2.5 \
	  --force
	python3 tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py \
	  --package-manifest /tmp/proofrail-silver-multi-agent-demo-v0.2.5/demo-package-manifest.json

.PHONY: verify-silver-multi-agent-demo-v0-2-5
verify-silver-multi-agent-demo-v0-2-5:
	bash tests/test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh

.PHONY: validate-silver-evidence-source-adapters-v0-2-6
validate-silver-evidence-source-adapters-v0-2-6:
	python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py \
	  --examples-dir examples/silver-evidence-source-adapters

.PHONY: verify-silver-evidence-source-adapter-v0-2-6
verify-silver-evidence-source-adapter-v0-2-6:
	bash tests/test_silver_evidence_source_adapter_v0_2_6.sh

.PHONY: run-silver-composed-gateway-demo-v0-2-7
run-silver-composed-gateway-demo-v0-2-7:
	python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
	  --demo-root demos/silver-demo-004-composed-gateway-evidence \
	  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
	  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
	  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
	  --generated-at 2026-06-22T00:00:00Z \
	  --force
	python3 tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json

.PHONY: verify-silver-composed-gateway-demo-v0-2-7
verify-silver-composed-gateway-demo-v0-2-7:
	bash tests/test_silver_composed_gateway_evidence_v0_2_7.sh

.PHONY: run-silver-relying-party-acceptance-demo-v0-2-8
run-silver-relying-party-acceptance-demo-v0-2-8:
	python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
	  --demo-root demos/silver-demo-004-composed-gateway-evidence \
	  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
	  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
	  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
	  --generated-at 2026-06-22T00:00:00Z \
	  --force
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
	python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
	  --evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7

.PHONY: verify-silver-relying-party-acceptance-demo-v0-2-8
verify-silver-relying-party-acceptance-demo-v0-2-8:
	bash tests/test_silver_relying_party_acceptance_record_v0_2_8.sh

.PHONY: run-silver-revocation-challenge-drill-v0-2-9
run-silver-revocation-challenge-drill-v0-2-9:
	python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
	  --demo-root demos/silver-demo-004-composed-gateway-evidence \
	  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
	  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
	  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
	  --generated-at 2026-06-22T00:00:00Z \
	  --force
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
	python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
	  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
	  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
	  --generated-at 2026-06-27T00:00:00Z \
	  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
	  --force
	python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json

.PHONY: verify-silver-revocation-challenge-drill-v0-2-9
verify-silver-revocation-challenge-drill-v0-2-9:
	bash tests/test_silver_revocation_challenge_drill_v0_2_9.sh

.PHONY: run-silver-acceptance-handoff-v0-3-0
run-silver-acceptance-handoff-v0-3-0:
	python3 tools/silver/compose_gateway_evidence_demo_v0_1_0.py \
	  --demo-root demos/silver-demo-004-composed-gateway-evidence \
	  --adapter examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json \
	  --gateway-events fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl \
	  --output-dir /tmp/proofrail-silver-composed-gateway-demo-v0.2.7 \
	  --generated-at 2026-06-22T00:00:00Z \
	  --force
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
	python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
	  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
	  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
	  --generated-at 2026-06-27T00:00:00Z \
	  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
	  --force
	python3 tools/silver/build_silver_acceptance_handoff_v0_1_0.py \
	  --composed-evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
	  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
	  --drill-manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
	  --generated-at 2026-06-28T00:00:00Z \
	  --output-dir /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
	  --force
	python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json

.PHONY: verify-silver-acceptance-handoff-v0-3-0
verify-silver-acceptance-handoff-v0-3-0:
	bash tests/test_silver_acceptance_handoff_v0_3_0.sh

.PHONY: run-silver-handoff-inspection-v0-3-1
run-silver-handoff-inspection-v0-3-1: run-silver-acceptance-handoff-v0-3-0
	python3 tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py \
	  --handoff-manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json \
	  --requirement-set fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json \
	  --generated-at 2026-06-29T00:00:00Z \
	  --output-dir /tmp/proofrail-silver-handoff-inspection-v0.3.1 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_handoff_inspection_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-handoff-inspection-v0.3.1/silver-handoff-inspection-manifest.json

.PHONY: verify-silver-handoff-inspection-v0-3-1
verify-silver-handoff-inspection-v0-3-1:
	bash tests/test_silver_handoff_inspector_v0_3_1.sh

.PHONY: run-silver-trace-binding-v0-3-2
run-silver-trace-binding-v0-3-2:
	python3 tools/silver/build_silver_trace_binding_v0_1_0.py \
	  --adapter examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json \
	  --trace-events fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl \
	  --bindings fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json \
	  --trace-binding-report-id proofrail-trace-binding-report-demo-001 \
	  --generated-at 2026-06-22T00:00:00Z \
	  --output-dir /tmp/proofrail-silver-trace-binding-v0.3.2 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_trace_binding_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-manifest.json

.PHONY: verify-silver-trace-binding-v0-3-2
verify-silver-trace-binding-v0-3-2:
	bash tests/test_silver_trace_binding_v0_3_2.sh

.PHONY: run-silver-adapter-pilot-v0-3-3
run-silver-adapter-pilot-v0-3-3:
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
	python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-manifest.json

.PHONY: verify-silver-adapter-pilot-v0-3-3
verify-silver-adapter-pilot-v0-3-3:
	bash tests/test_silver_adapter_pilot_v0_3_3.sh

.PHONY: run-silver-challenge-withdrawal-primitives-v0-3-4
run-silver-challenge-withdrawal-primitives-v0-3-4:
	python3 tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py \
	  --target-handoff-root /tmp/proofrail-silver-acceptance-handoff-v0.3.0 \
	  --challenge-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json \
	  --withdrawal-record fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json \
	  --generated-at 2026-06-29T00:30:00Z \
	  --output-dir /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/silver-challenge-withdrawal-manifest.json

.PHONY: verify-silver-challenge-withdrawal-primitives-v0-3-4
verify-silver-challenge-withdrawal-primitives-v0-3-4:
	bash tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh

.PHONY: run-silver-relying-party-policy-pack-v0-3-5
run-silver-relying-party-policy-pack-v0-3-5:
	python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py \
	  --policy-pack fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json \
	  --manifest-id proofrail-silver-relying-party-policy-pack-manifest-demo-001 \
	  --report-id proofrail-silver-relying-party-policy-pack-conformance-report-demo-001 \
	  --generated-at 2026-07-06T00:30:00Z \
	  --output-dir /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/silver-relying-party-policy-pack-manifest.json

.PHONY: verify-silver-relying-party-policy-pack-v0-3-5
verify-silver-relying-party-policy-pack-v0-3-5:
	bash tests/test_silver_relying_party_policy_pack_v0_3_5.sh

.PHONY: run-silver-control-crosswalk-protected-action-catalog-v0-3-6
run-silver-control-crosswalk-protected-action-catalog-v0-3-6:
	python3 tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py \
	  --input-pack fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/control-pack.json \
	  --manifest-id proofrail-silver-control-crosswalk-protected-action-catalog-manifest-demo-001 \
	  --report-id proofrail-silver-control-crosswalk-protected-action-catalog-conformance-report-demo-001 \
	  --generated-at 2026-07-20T00:30:00Z \
	  --output-dir /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/silver-control-crosswalk-protected-action-catalog-manifest.json

.PHONY: verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
verify-silver-control-crosswalk-protected-action-catalog-v0-3-6:
	bash tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh

.PHONY: run-silver-registry-lite-v0-3-7
run-silver-registry-lite-v0-3-7:
	python3 tools/silver/build_silver_registry_lite_v0_1_0.py \
	  --input-registry fixtures/silver-registry-lite-v0.3.7/registry-lite.json \
	  --manifest-id proofrail-silver-registry-lite-manifest-demo-001 \
	  --report-id proofrail-silver-registry-lite-conformance-report-demo-001 \
	  --generated-at 2026-08-15T00:30:00Z \
	  --output-dir /tmp/proofrail-silver-registry-lite-v0.3.7 \
	  --force \
	  --self-validate
	python3 tools/silver/verify_silver_registry_lite_v0_1_0.py \
	  --manifest /tmp/proofrail-silver-registry-lite-v0.3.7/silver-registry-lite-manifest.json

.PHONY: verify-silver-registry-lite-v0-3-7
verify-silver-registry-lite-v0-3-7:
	bash tests/test_silver_registry_lite_v0_3_7.sh

.PHONY: verify-silver-all
verify-silver-all:
	$(MAKE) verify-silver-demo-001
	$(MAKE) verify-independent-silver-demo-002
	$(MAKE) validate-silver-profile-demo-002
	$(MAKE) verify-silver-profile-v0-2-1
	$(MAKE) verify-silver-profile-examples-v0-2-1
	$(MAKE) verify-silver-attestation-v0-2-2
	$(MAKE) verify-silver-authority-v0-2-3
	$(MAKE) verify-silver-multi-agent-harness-v0-2-4
	$(MAKE) verify-silver-multi-agent-demo-v0-2-5
	$(MAKE) verify-silver-evidence-source-adapter-v0-2-6
	$(MAKE) verify-silver-composed-gateway-demo-v0-2-7
	$(MAKE) verify-silver-relying-party-acceptance-demo-v0-2-8
	$(MAKE) verify-silver-revocation-challenge-drill-v0-2-9
	$(MAKE) verify-silver-acceptance-handoff-v0-3-0
	$(MAKE) verify-silver-handoff-inspection-v0-3-1
	$(MAKE) verify-silver-trace-binding-v0-3-2
	$(MAKE) verify-silver-adapter-pilot-v0-3-3
	$(MAKE) verify-silver-challenge-withdrawal-primitives-v0-3-4
	$(MAKE) verify-silver-relying-party-policy-pack-v0-3-5
	$(MAKE) verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
	$(MAKE) verify-silver-registry-lite-v0-3-7

.PHONY: run-gold-governed-reliance-v0-4-0
run-gold-governed-reliance-v0-4-0:
	python3 tools/gold/build_gold_governed_reliance_demo_v0_1_0.py \
	  --input-package fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json \
	  --manifest-id proofrail-gold-governed-reliance-manifest-demo-001 \
	  --report-id proofrail-gold-governed-reliance-conformance-report-demo-001 \
	  --generated-at 2026-09-15T00:30:00Z \
	  --output-dir /tmp/proofrail-gold-governed-reliance-v0.4.0 \
	  --force \
	  --self-validate
	python3 tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py \
	  --manifest /tmp/proofrail-gold-governed-reliance-v0.4.0/gold-governed-reliance-package-manifest.json

.PHONY: verify-gold-governed-reliance-v0-4-0
verify-gold-governed-reliance-v0-4-0:
	bash tests/test_gold_governed_reliance_v0_4_0.sh

.PHONY: verify-gold-all
verify-gold-all:
	$(MAKE) verify-gold-governed-reliance-v0-4-0
