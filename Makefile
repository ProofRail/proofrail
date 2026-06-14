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
