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
