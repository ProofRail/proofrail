#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="demos/composed-bronze-demo-001"
CLAIM="$PACKAGE_ROOT/claims/bronze-claim-demo-001.yaml"
MANIFEST="$PACKAGE_ROOT/evidence-bundle-manifest-v0.1.3.yaml"

echo "=== Step 1: Generate v0.1.2 claim (prerequisite) ==="
python3 tools/claims/generate_bronze_claim_v0_1_2.py "$PACKAGE_ROOT"

echo "=== Step 2: Verify v0.1.2 evidence checksums ==="
python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py "$CLAIM" "$PACKAGE_ROOT"

echo "=== Step 3: Generate v0.1.3 bundle manifest ==="
python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py "$PACKAGE_ROOT"

echo "=== Step 4: Verify v0.1.3 bundle manifest ==="
python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py "$MANIFEST" "$PACKAGE_ROOT"

echo "=== Step 5: Inline regression checks ==="
python3 - <<'PY'
import re
import sys
from pathlib import Path
import yaml

manifest_path = Path("demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml")
manifest = yaml.safe_load(manifest_path.read_text())

checks = [
    ("manifest_version", manifest.get("manifest_version") == "v0.1.3"),
    ("manifest_type", manifest.get("manifest_type") == "proofrail.bronze.evidence_bundle"),
    ("subject_claim", manifest.get("subject_claim") == "claims/bronze-claim-demo-001.yaml"),
]

files = manifest.get("files", [])

# Check that claim file is in the bundle
claim_roles = [f for f in files if f.get("role") == "claim"]
checks.append(("has_claim_role", len(claim_roles) == 1))

# Check that v0.1.2 schema is in the bundle
schema_roles = [f for f in files if f.get("role") == "claim_schema"]
checks.append(("has_claim_schema_role", len(schema_roles) == 1))

# Every file must have a valid sha256
for f in files:
    path = f.get("path", "unknown")
    sha = f.get("sha256", "")
    checks.append((
        f"sha256 format: {path}",
        isinstance(sha, str) and bool(re.fullmatch(r"sha256:[0-9a-fA-F]{64}", sha)),
    ))

# Every file must have size_bytes > 0
for f in files:
    path = f.get("path", "unknown")
    size = f.get("size_bytes")
    checks.append((
        f"size_bytes > 0: {path}",
        isinstance(size, int) and size > 0,
    ))

# validation.file_count must match len(files)
validation = manifest.get("validation", {})
checks.append((
    "file_count matches",
    validation.get("file_count") == len(files),
))

# File count is 16
checks.append((
    "file_count is 16",
    len(files) == 16,
))

# missing_files should be empty
checks.append((
    "no missing files",
    validation.get("missing_files") == [],
))

failed = [name for name, ok in checks if not ok]

if failed:
    print("FAIL: Bronze evidence bundle v0.1.3 regression checks failed")
    for name in failed:
        print(f"- {name}")
    sys.exit(1)

print("PASS: Bronze evidence bundle v0.1.3 regression fixture valid")
PY

echo "=== Step 6: Tamper detection test ==="
TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

# Mirror repo structure in temp directory so ../../ paths resolve
mkdir -p "$TMPDIR_ROOT/demos"
cp -r "$PACKAGE_ROOT" "$TMPDIR_ROOT/demos/composed-bronze-demo-001"
ln -s "$(pwd)/schemas" "$TMPDIR_ROOT/schemas"
ln -s "$(pwd)/tools" "$TMPDIR_ROOT/tools"

TAMPER_PACKAGE="$TMPDIR_ROOT/demos/composed-bronze-demo-001"
TAMPER_MANIFEST="$TAMPER_PACKAGE/evidence-bundle-manifest-v0.1.3.yaml"

# Copy the generated manifest into the temp copy
cp "$MANIFEST" "$TAMPER_MANIFEST"

# Corrupt one evidence file in the temp copy
echo "TAMPERED_CONTENT" >> "$TAMPER_PACKAGE/evidence/audit-sample.jsonl"

# The verifier should fail on the tampered file
if python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py "$TAMPER_MANIFEST" "$TAMPER_PACKAGE" 2>/dev/null; then
    echo "FAIL: tamper detection — verifier should have failed on tampered file"
    exit 1
else
    echo "PASS: tamper detection — verifier correctly detected tampered evidence"
fi

echo "=== All v0.1.3 regression tests passed ==="
