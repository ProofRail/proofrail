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

.PHONY: verify-silver-all
verify-silver-all:
	$(MAKE) verify-silver-demo-001
	$(MAKE) verify-independent-silver-demo-002
	$(MAKE) validate-silver-profile-demo-002
	$(MAKE) verify-silver-profile-v0-2-1
	$(MAKE) verify-silver-profile-examples-v0-2-1
	$(MAKE) verify-silver-attestation-v0-2-2
	$(MAKE) verify-silver-authority-v0-2-3
