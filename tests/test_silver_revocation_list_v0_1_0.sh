#!/usr/bin/env bash
set -euo pipefail

BRONZE_ROOT="demos/composed-bronze-demo-001"
SILVER_ROOT="demos/silver-demo-001"
CLAIM="$BRONZE_ROOT/claims/bronze-claim-demo-001.yaml"
BUNDLE_MANIFEST="$BRONZE_ROOT/evidence-bundle-manifest-v0.1.3.yaml"
PRIVATE_KEY="$SILVER_ROOT/runtime/issuer-a/private-key.pem"
ASSERTION="$SILVER_ROOT/runtime/silver-signed-bundle-assertion-v0.1.0.yaml"
TRUST_POLICY="$SILVER_ROOT/runtime/verifier-b/trust-policy.yaml"
REVOCATION_LIST="$SILVER_ROOT/runtime/verifier-b/revocation-list.yaml"

VERIFIER_ARGS="$ASSERTION $TRUST_POLICY --silver-root $SILVER_ROOT --bronze-package-root $BRONZE_ROOT --revocation-list $REVOCATION_LIST"

echo "=== Step 1: Generate v0.1.2 claim ==="
python3 tools/claims/generate_bronze_claim_v0_1_2.py "$BRONZE_ROOT"

echo "=== Step 2: Verify v0.1.2 evidence checksums ==="
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py "$CLAIM" "$BRONZE_ROOT"

echo "=== Step 3: Generate v0.1.3 bundle manifest ==="
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py "$BRONZE_ROOT"

echo "=== Step 4: Verify v0.1.3 bundle manifest ==="
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py "$BUNDLE_MANIFEST" "$BRONZE_ROOT"

echo "=== Step 5: Generate demo issuer keypair + trust policy ==="
python3 tools/silver/generate_demo_issuer_v0_1_0.py "$SILVER_ROOT" --force

echo "=== Step 6: Generate empty revocation list ==="
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force

echo "=== Step 7: Sign v0.1.3 bundle manifest ==="
python3 tools/silver/sign_bundle_manifest_v0_1_0.py "$SILVER_ROOT" \
  --private-key "$PRIVATE_KEY" \
  --output "$ASSERTION"

echo "=== Step 8: Verify assertion with empty revocation list — should pass ==="
PASS_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py $VERIFIER_ARGS 2>&1)

if echo "$PASS_OUTPUT" | grep -q "PASS: Silver signed bundle assertion verified"; then
    echo "PASS: empty revocation list accepted valid assertion"
else
    echo "FAIL: expected PASS with empty revocation list"
    echo "  Output: $PASS_OUTPUT"
    exit 1
fi

echo "=== Step 9: Revocation test — revoked assertion ID ==="
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force \
  --revoke-assertion proofrail-silver-demo-001 \
  --reason "demo assertion revocation"

REVOKE_ASSERTION_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py $VERIFIER_ARGS 2>&1 || true)

if echo "$REVOKE_ASSERTION_OUTPUT" | grep -q "assertion revoked"; then
    echo "PASS: assertion revocation detected"
else
    echo "FAIL: expected 'assertion revoked'"
    echo "  Output: $REVOKE_ASSERTION_OUTPUT"
    exit 1
fi

echo "=== Step 10: Revocation test — revoked issuer key ==="
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force \
  --revoke-issuer-key proofrail-demo-issuer-a:proofrail-demo-issuer-a-ed25519-001 \
  --reason "demo key revocation"

REVOKE_KEY_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py $VERIFIER_ARGS 2>&1 || true)

if echo "$REVOKE_KEY_OUTPUT" | grep -q "issuer key revoked"; then
    echo "PASS: issuer key revocation detected"
else
    echo "FAIL: expected 'issuer key revoked'"
    echo "  Output: $REVOKE_KEY_OUTPUT"
    exit 1
fi

echo "=== Step 11: Revocation test — revoked bundle hash ==="
# Extract the bundle_manifest_sha256 from the signed assertion
BUNDLE_SHA=$(python3 -c "
import yaml
from pathlib import Path
a = yaml.safe_load(Path('$ASSERTION').read_text())
print(a['subject']['bundle_manifest_sha256'])
")

python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force \
  --revoke-bundle-sha256 "$BUNDLE_SHA" \
  --reason "demo bundle revocation"

REVOKE_BUNDLE_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py $VERIFIER_ARGS 2>&1 || true)

if echo "$REVOKE_BUNDLE_OUTPUT" | grep -q "bundle revoked"; then
    echo "PASS: bundle revocation detected"
else
    echo "FAIL: expected 'bundle revoked'"
    echo "  Output: $REVOKE_BUNDLE_OUTPUT"
    exit 1
fi

echo "=== Step 12: Confirm runtime files ==="
# Restore empty revocation list for clean state
python3 tools/silver/generate_demo_revocation_list_v0_1_0.py "$SILVER_ROOT" --force

for F in "$PRIVATE_KEY" "$ASSERTION" "$TRUST_POLICY" "$REVOCATION_LIST"; do
    if [ ! -f "$F" ]; then
        echo "FAIL: expected runtime file not found: $F"
        exit 1
    fi
done
echo "PASS: all runtime files present under demos/silver-demo-001/runtime/"

echo "=== PASS: Silver revocation list v0.1.0 regression fixture valid ==="
