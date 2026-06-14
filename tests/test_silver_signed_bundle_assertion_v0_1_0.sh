#!/usr/bin/env bash
set -euo pipefail

BRONZE_ROOT="demos/composed-bronze-demo-001"
SILVER_ROOT="demos/silver-demo-001"
CLAIM="$BRONZE_ROOT/claims/bronze-claim-demo-001.yaml"
BUNDLE_MANIFEST="$BRONZE_ROOT/evidence-bundle-manifest-v0.1.3.yaml"
PRIVATE_KEY="$SILVER_ROOT/runtime/issuer-a/private-key.pem"
ASSERTION="$SILVER_ROOT/runtime/silver-signed-bundle-assertion-v0.1.0.yaml"
TRUST_POLICY="$SILVER_ROOT/runtime/verifier-b/trust-policy.yaml"

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

echo "=== Step 6: Sign v0.1.3 bundle manifest ==="
python3 tools/silver/sign_bundle_manifest_v0_1_0.py "$SILVER_ROOT" \
  --private-key "$PRIVATE_KEY" \
  --output "$ASSERTION"

echo "=== Step 7: Verify signed Silver assertion (happy path) ==="
python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$ASSERTION" "$TRUST_POLICY" \
  --silver-root "$SILVER_ROOT" \
  --bronze-package-root "$BRONZE_ROOT"

echo "=== Step 8: Inline regression checks ==="
python3 - <<'PY'
import re
import sys
from pathlib import Path
import yaml

assertion_path = Path("demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml")
assertion = yaml.safe_load(assertion_path.read_text())

checks = [
    ("assertion_version", assertion.get("assertion_version") == "v0.1.0"),
    ("assertion_type", assertion.get("assertion_type") == "proofrail.silver.signed_bundle_assertion"),
    ("issuer.issuer_id present", bool(assertion.get("issuer", {}).get("issuer_id"))),
    ("issuer.key_id present", bool(assertion.get("issuer", {}).get("key_id"))),
    ("signature.algorithm", assertion.get("signature", {}).get("algorithm") == "ed25519"),
    ("signature.signature_encoding", assertion.get("signature", {}).get("signature_encoding") == "base64"),
    (
        "bundle_manifest_sha256 format",
        bool(re.fullmatch(
            r"sha256:[0-9a-fA-F]{64}",
            assertion.get("subject", {}).get("bundle_manifest_sha256", ""),
        )),
    ),
    ("validity.issued_at present", bool(assertion.get("validity", {}).get("issued_at"))),
    ("validity.expires_at present", bool(assertion.get("validity", {}).get("expires_at"))),
]

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: Silver assertion v0.1.0 regression checks failed")
    for name in failed:
        print(f"- {name}")
    sys.exit(1)

print("PASS: Silver assertion v0.1.0 inline checks valid")
PY

echo "=== Step 9: Tamper test A — tampered bundle manifest ==="
TMPDIR_A=$(mktemp -d)
trap 'rm -rf "$TMPDIR_A"' EXIT

# Mirror repo structure so ../../ paths in manifest resolve
mkdir -p "$TMPDIR_A/demos"
cp -r "$BRONZE_ROOT" "$TMPDIR_A/demos/composed-bronze-demo-001"
cp -r "$SILVER_ROOT" "$TMPDIR_A/demos/silver-demo-001"
ln -s "$(pwd)/schemas" "$TMPDIR_A/schemas"
ln -s "$(pwd)/tools" "$TMPDIR_A/tools"

# Corrupt the bundle manifest in the temp copy
echo "TAMPERED" >> "$TMPDIR_A/demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml"

TAMPER_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$TMPDIR_A/demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml" \
  "$TMPDIR_A/demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml" \
  --silver-root "$TMPDIR_A/demos/silver-demo-001" \
  --bronze-package-root "$TMPDIR_A/demos/composed-bronze-demo-001" 2>&1 || true)

if echo "$TAMPER_OUTPUT" | grep -qE "checksum mismatch|signature verification failed"; then
    echo "PASS: tamper test A — verifier detected tampered manifest"
else
    echo "FAIL: tamper test A — expected checksum mismatch or signature failure"
    echo "  Output: $TAMPER_OUTPUT"
    exit 1
fi

echo "=== Step 10: Tamper test B — tampered evidence file ==="
# Reuse TMPDIR_A with fresh copies
rm -rf "$TMPDIR_A/demos"
mkdir -p "$TMPDIR_A/demos"
cp -r "$BRONZE_ROOT" "$TMPDIR_A/demos/composed-bronze-demo-001"
cp -r "$SILVER_ROOT" "$TMPDIR_A/demos/silver-demo-001"

# Corrupt an evidence file (not the manifest)
echo "TAMPERED_EVIDENCE" >> "$TMPDIR_A/demos/composed-bronze-demo-001/evidence/audit-sample.jsonl"

TAMPER_B_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$TMPDIR_A/demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml" \
  "$TMPDIR_A/demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml" \
  --silver-root "$TMPDIR_A/demos/silver-demo-001" \
  --bronze-package-root "$TMPDIR_A/demos/composed-bronze-demo-001" 2>&1 || true)

if echo "$TAMPER_B_OUTPUT" | grep -q "underlying bundle verification failed"; then
    echo "PASS: tamper test B — verifier detected tampered evidence"
else
    echo "FAIL: tamper test B — expected underlying bundle verification failure"
    echo "  Output: $TAMPER_B_OUTPUT"
    exit 1
fi

echo "=== Step 11: Trust test — untrusted issuer ==="
UNTRUSTED_POLICY=$(mktemp)
cat > "$UNTRUSTED_POLICY" <<'YAML'
trust_policy_version: "v0.1.0"
policy_id: "untrusted-policy"
policy_label: "Untrusted Policy"
trusted_issuers:
  - issuer_id: "some-other-issuer"
    issuer_label: "Some Other Issuer"
    key_id: "some-other-key"
    algorithm: "ed25519"
    public_key_pem: "not-a-real-key"
    public_key_fingerprint_sha256: "sha256:0000000000000000000000000000000000000000000000000000000000000000"
YAML

TRUST_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$ASSERTION" "$UNTRUSTED_POLICY" \
  --silver-root "$SILVER_ROOT" \
  --bronze-package-root "$BRONZE_ROOT" 2>&1 || true)

rm -f "$UNTRUSTED_POLICY"

if echo "$TRUST_OUTPUT" | grep -qE "issuer not trusted|key_id not trusted"; then
    echo "PASS: trust test — verifier rejected untrusted issuer"
else
    echo "FAIL: trust test — expected issuer not trusted"
    echo "  Output: $TRUST_OUTPUT"
    exit 1
fi

echo "=== Step 12: Expiry test — expired assertion ==="
EXPIRED_ASSERTION=$(mktemp)
python3 - "$ASSERTION" "$EXPIRED_ASSERTION" <<'PY'
import sys
import yaml
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

assertion = yaml.safe_load(src.read_text())
assertion["validity"]["expires_at"] = "2020-01-01T00:00:00Z"
assertion["validity"]["issued_at"] = "2019-01-01T00:00:00Z"

dst.write_text(yaml.safe_dump(assertion, sort_keys=False, allow_unicode=True))
PY

EXPIRY_OUTPUT=$(python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
  "$EXPIRED_ASSERTION" "$TRUST_POLICY" \
  --silver-root "$SILVER_ROOT" \
  --bronze-package-root "$BRONZE_ROOT" 2>&1 || true)

rm -f "$EXPIRED_ASSERTION"

if echo "$EXPIRY_OUTPUT" | grep -q "assertion expired"; then
    echo "PASS: expiry test — verifier rejected expired assertion"
else
    echo "FAIL: expiry test — expected assertion expired"
    echo "  Output: $EXPIRY_OUTPUT"
    exit 1
fi

echo "=== All Silver v0.1.0 regression tests passed ==="
