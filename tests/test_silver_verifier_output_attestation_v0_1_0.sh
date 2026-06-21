#!/usr/bin/env bash
set -euo pipefail

BRONZE_ROOT="demos/composed-bronze-demo-001"
SILVER_ROOT="demos/silver-demo-001"
DEMO_002="demos/silver-demo-002-independent-verifier"
REPORT="$SILVER_ROOT/runtime/verification-report.json"
PACKAGE_DIR="$DEMO_002/runtime/package"
PACKAGE_MANIFEST="$PACKAGE_DIR/package-manifest.yaml"
INDEPENDENT_REPORT="$PACKAGE_DIR/verification-report.json"

# Temp directory for all generated and tampered artifacts — cleaned up on exit
TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

echo "=== Step 1: Generate + verify Bronze chain ==="
python3 tools/claims/generate_bronze_claim_v0_1_2.py "$BRONZE_ROOT"
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py \
  "$BRONZE_ROOT/claims/bronze-claim-demo-001.yaml" "$BRONZE_ROOT"
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py "$BRONZE_ROOT"
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py \
  "$BRONZE_ROOT/evidence-bundle-manifest-v0.1.3.yaml" "$BRONZE_ROOT"

echo "=== Step 2: Run silver-demo-001 ==="
make silver-demo-001

echo "=== Step 3: Copy VR to temp; generate v0.2.1 conformance report for silver.base ==="
TEMP_VR="$TMPDIR_ROOT/verification-report.json"
TEMP_CR="$TMPDIR_ROOT/silver-base-conformance.json"
cp "$REPORT" "$TEMP_VR"
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report "$TEMP_VR" \
  --output "$TEMP_CR"

echo "=== Step 4: Generate demo verifier attestor keys ==="
TEMP_ATTESTOR="$TMPDIR_ROOT/attestor-verifier-b"
python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
  --output-root "$TEMP_ATTESTOR" \
  --attestor-id proofrail-demo-verifier-b \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --force

# Verify 3 files created
for f in attestor-private-key.pem attestor-public-key.pem attestation-trust-policy.yaml; do
    if [ ! -f "$TEMP_ATTESTOR/$f" ]; then
        echo "FAIL: attestor key gen — missing $f"
        exit 1
    fi
done
echo "PASS: attestor key generation produced 3 files"

echo "=== Step 5: Sign attestation referencing temp copies of VR + CR ==="
TEMP_ATTESTATION="$TMPDIR_ROOT/attestation-base.json"
python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
  --verification-report "$TEMP_VR" \
  --conformance-report "$TEMP_CR" \
  --private-key "$TEMP_ATTESTOR/attestor-private-key.pem" \
  --attestor-id proofrail-demo-verifier-b \
  --attestor-version v0.2.2-demo \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --output "$TEMP_ATTESTATION"

if [ ! -f "$TEMP_ATTESTATION" ]; then
    echo "FAIL: attestation signing — output not created"
    exit 1
fi
echo "PASS: attestation signed successfully"

echo "=== Step 6: Verify attestation with trust policy ==="
python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_ATTESTATION" \
  --trust-policy "$TEMP_ATTESTOR/attestation-trust-policy.yaml"

echo "=== Step 7: Tamper VR → verify → expect subject_hash_mismatch ==="
echo "TAMPERED" >> "$TEMP_VR"

TAMPER_VR_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_ATTESTATION" \
  --trust-policy "$TEMP_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

if echo "$TAMPER_VR_OUTPUT" | grep -q "subject_hash_mismatch"; then
    echo "PASS: tampered VR detected (subject_hash_mismatch)"
else
    echo "FAIL: expected 'subject_hash_mismatch' for tampered VR"
    echo "  Output: $TAMPER_VR_OUTPUT"
    exit 1
fi

echo "=== Step 8: Restore VR; tamper CR → verify → expect subject_hash_mismatch ==="
# Restore VR from original
cp "$REPORT" "$TEMP_VR"
echo "TAMPERED" >> "$TEMP_CR"

TAMPER_CR_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_ATTESTATION" \
  --trust-policy "$TEMP_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

if echo "$TAMPER_CR_OUTPUT" | grep -q "subject_hash_mismatch"; then
    echo "PASS: tampered CR detected (subject_hash_mismatch)"
else
    echo "FAIL: expected 'subject_hash_mismatch' for tampered CR"
    echo "  Output: $TAMPER_CR_OUTPUT"
    exit 1
fi

# Restore CR for subsequent tests
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report "$TEMP_VR" \
  --output "$TEMP_CR"

echo "=== Step 9: Tamper signed_payload in attestation → signature failure ==="
TAMPERED_ATTESTATION="$TMPDIR_ROOT/attestation-tampered.json"
python3 - "$TEMP_ATTESTATION" "$TAMPERED_ATTESTATION" <<'PY'
import json
import sys
from pathlib import Path

att = json.loads(Path(sys.argv[1]).read_text())
att["signed_payload"]["attestation_id"] = "tampered-id"
Path(sys.argv[2]).write_text(json.dumps(att, indent=2) + "\n")
PY

TAMPER_SIG_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TAMPERED_ATTESTATION" \
  --trust-policy "$TEMP_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

if echo "$TAMPER_SIG_OUTPUT" | grep -q "signature_verification_failed"; then
    echo "PASS: tampered signed_payload detected (signature_verification_failed)"
else
    echo "FAIL: expected 'signature_verification_failed' for tampered payload"
    echo "  Output: $TAMPER_SIG_OUTPUT"
    exit 1
fi

echo "=== Step 10: Wrong trust policy → attestor_not_trusted ==="
TEMP_WRONG_ATTESTOR="$TMPDIR_ROOT/attestor-wrong"
python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
  --output-root "$TEMP_WRONG_ATTESTOR" \
  --attestor-id some-other-attestor \
  --key-id some-other-key-001 \
  --force

WRONG_TP_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_ATTESTATION" \
  --trust-policy "$TEMP_WRONG_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

if echo "$WRONG_TP_OUTPUT" | grep -q "attestor_not_trusted"; then
    echo "PASS: untrusted attestor rejected (attestor_not_trusted)"
else
    echo "FAIL: expected 'attestor_not_trusted'"
    echo "  Output: $WRONG_TP_OUTPUT"
    exit 1
fi

echo "=== Step 11: Export independent package via v0.2.1 exporter ==="
python3 tools/silver/export_independent_verification_package_v0_2_1.py \
  --bronze-root "$BRONZE_ROOT" \
  --silver-root "$SILVER_ROOT" \
  --output "$PACKAGE_DIR" \
  --force

echo "=== Step 12: Run independent verifier ==="
python3 "$DEMO_002/verifier/independent_verify.py" \
  --package "$PACKAGE_DIR" \
  --report "$INDEPENDENT_REPORT"

echo "=== Step 13: Copy independent VR + package manifest to temp; generate silver.independent CR ==="
TEMP_INDEP_VR="$TMPDIR_ROOT/independent-vr.json"
TEMP_INDEP_PM="$TMPDIR_ROOT/independent-pm.yaml"
TEMP_INDEP_CR="$TMPDIR_ROOT/independent-conformance.json"
cp "$INDEPENDENT_REPORT" "$TEMP_INDEP_VR"
cp "$PACKAGE_MANIFEST" "$TEMP_INDEP_PM"
# Generate conformance report using original package manifest path (validator resolves
# input paths relative to manifest parent), then copy the result to temp for signing.
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.independent \
  --verification-report "$TEMP_INDEP_VR" \
  --package-manifest "$PACKAGE_MANIFEST" \
  --output "$TEMP_INDEP_CR"

echo "=== Step 14: Generate attestor key for independent verifier ==="
TEMP_INDEP_ATTESTOR="$TMPDIR_ROOT/attestor-independent"
python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
  --output-root "$TEMP_INDEP_ATTESTOR" \
  --attestor-id proofrail-demo-independent-verifier \
  --key-id proofrail-demo-independent-verifier-ed25519-attestation-001 \
  --force

for f in attestor-private-key.pem attestor-public-key.pem attestation-trust-policy.yaml; do
    if [ ! -f "$TEMP_INDEP_ATTESTOR/$f" ]; then
        echo "FAIL: independent attestor key gen — missing $f"
        exit 1
    fi
done
echo "PASS: independent attestor key generation produced 3 files"

echo "=== Step 15: Sign independent attestation with --package-manifest ==="
TEMP_INDEP_ATTESTATION="$TMPDIR_ROOT/attestation-independent.json"
python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
  --verification-report "$TEMP_INDEP_VR" \
  --conformance-report "$TEMP_INDEP_CR" \
  --package-manifest "$TEMP_INDEP_PM" \
  --private-key "$TEMP_INDEP_ATTESTOR/attestor-private-key.pem" \
  --attestor-id proofrail-demo-independent-verifier \
  --attestor-version v0.2.2-demo \
  --key-id proofrail-demo-independent-verifier-ed25519-attestation-001 \
  --output "$TEMP_INDEP_ATTESTATION"

if [ ! -f "$TEMP_INDEP_ATTESTATION" ]; then
    echo "FAIL: independent attestation not created"
    exit 1
fi
echo "PASS: independent attestation signed successfully"

echo "=== Step 16: Verify independent attestation ==="
python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_INDEP_ATTESTATION" \
  --trust-policy "$TEMP_INDEP_ATTESTOR/attestation-trust-policy.yaml"

echo "=== Step 17: Tamper package manifest → verify → subject_hash_mismatch ==="
echo "TAMPERED" >> "$TEMP_INDEP_PM"

TAMPER_PM_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$TEMP_INDEP_ATTESTATION" \
  --trust-policy "$TEMP_INDEP_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

if echo "$TAMPER_PM_OUTPUT" | grep -q "subject_hash_mismatch"; then
    echo "PASS: tampered package manifest detected (subject_hash_mismatch)"
else
    echo "FAIL: expected 'subject_hash_mismatch' for tampered package manifest"
    echo "  Output: $TAMPER_PM_OUTPUT"
    exit 1
fi

echo "=== Step 18: Sign with wrong verifier identity → identity mismatch at signing ==="
# Use verifier-b identity for the independent report (verifier_id mismatch)
MISMATCH_OUTPUT=$(python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
  --verification-report "$TEMP_INDEP_VR" \
  --conformance-report "$TEMP_INDEP_CR" \
  --private-key "$TEMP_ATTESTOR/attestor-private-key.pem" \
  --attestor-id proofrail-demo-verifier-b \
  --attestor-version v0.2.2-demo \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --output "$TMPDIR_ROOT/attestation-mismatch.json" 2>&1 || true)

if echo "$MISMATCH_OUTPUT" | grep -q "does not match verifier_id"; then
    echo "PASS: identity mismatch rejected at signing"
else
    echo "FAIL: expected 'does not match verifier_id' in stderr"
    echo "  Output: $MISMATCH_OUTPUT"
    exit 1
fi

echo "=== Step 19: Path traversal in subject path → signer rejects ==="
# Create a verification report at a path with '..' component
TRAVERSAL_DIR="$TMPDIR_ROOT/subdir"
mkdir -p "$TRAVERSAL_DIR"
cp "$REPORT" "$TRAVERSAL_DIR/vr.json"
# Re-generate conformance for this VR
python3 tools/silver/validate_silver_profile_v0_2_1.py \
  --profile-mode silver.base \
  --verification-report "$TRAVERSAL_DIR/vr.json" \
  --output "$TRAVERSAL_DIR/cr.json"

# Try signing with a path that uses '..'
TRAVERSAL_SIGNER_OUTPUT=$(python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
  --verification-report "$TRAVERSAL_DIR/../subdir/vr.json" \
  --conformance-report "$TRAVERSAL_DIR/cr.json" \
  --private-key "$TEMP_ATTESTOR/attestor-private-key.pem" \
  --attestor-id proofrail-demo-verifier-b \
  --attestor-version v0.2.2-demo \
  --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
  --output "$TMPDIR_ROOT/attestation-traversal.json" 2>&1 || true)

if echo "$TRAVERSAL_SIGNER_OUTPUT" | grep -q "subject path contains '..' component"; then
    echo "PASS: signer rejected path with '..' component"
else
    echo "FAIL: expected signer to reject path with '..' component"
    echo "  Output: $TRAVERSAL_SIGNER_OUTPUT"
    exit 1
fi

# Also test verifier rejects attestation with crafted '..' path
CRAFTED_TRAVERSAL="$TMPDIR_ROOT/attestation-crafted-traversal.json"
python3 - "$TEMP_ATTESTATION" "$CRAFTED_TRAVERSAL" <<'PY'
import json
import sys
from pathlib import Path

att = json.loads(Path(sys.argv[1]).read_text())
att["signed_payload"]["subjects"]["verification_report"]["path"] = "../outside/report.json"
Path(sys.argv[2]).write_text(json.dumps(att, indent=2) + "\n")
PY

TRAVERSAL_VERIFIER_OUTPUT=$(python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
  --attestation "$CRAFTED_TRAVERSAL" \
  --trust-policy "$TEMP_ATTESTOR/attestation-trust-policy.yaml" 2>&1 || true)

# Will fail with either signature_verification_failed (because we changed signed_payload)
# or subject_path_traversal (if somehow the signature still matched). Both are acceptable.
if echo "$TRAVERSAL_VERIFIER_OUTPUT" | grep -qE "subject_path_traversal|signature_verification_failed"; then
    echo "PASS: verifier rejected crafted path traversal attestation"
else
    echo "FAIL: expected path traversal or signature failure"
    echo "  Output: $TRAVERSAL_VERIFIER_OUTPUT"
    exit 1
fi

echo "=== Step 20: All Silver Verifier Output Attestation v0.1.0 regression tests passed ==="
