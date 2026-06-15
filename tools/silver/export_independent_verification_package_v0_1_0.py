#!/usr/bin/env python3
"""Export a portable independent Silver verification package.

Builds a self-contained package that mirrors enough of the source repo
structure so that the signed bundle manifest's relative paths resolve
correctly, preserving the Ed25519 signature over raw bytes.

Usage:
  python3 tools/silver/export_independent_verification_package_v0_1_0.py \
    --bronze-root demos/composed-bronze-demo-001 \
    --silver-root demos/silver-demo-001 \
    --output demos/silver-demo-002-independent-verifier/runtime/package \
    --force
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

EXCLUDED_NAMES = {
    "private-key.pem",
    "public-key.pem",
    "verification-report.json",
    "__pycache__",
    ".DS_Store",
}

EXCLUDED_SUFFIXES = {".pyc", ".tgz"}

EXCLUDED_DIRS = {"evidence-freezes", "__pycache__"}


def _should_exclude(path: Path) -> bool:
    if path.name in EXCLUDED_NAMES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree_filtered(src_dir: Path, dst_dir: Path) -> int:
    """Copy directory tree, excluding unwanted files. Returns count of files copied."""
    count = 0
    for src_file in sorted(src_dir.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_dir)
        if _should_exclude(rel):
            continue
        _copy_file(src_file, dst_dir / rel)
        count += 1
    return count


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Export a portable independent Silver verification package"
    )
    parser.add_argument("--bronze-root", required=True, help="Bronze evidence package root")
    parser.add_argument("--silver-root", required=True, help="Silver demo root")
    parser.add_argument("--output", required=True, help="Output package directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    args = parser.parse_args()

    bronze_root = Path(args.bronze_root).resolve()
    silver_root = Path(args.silver_root).resolve()
    output_dir = Path(args.output)

    # Validate required source artifacts
    required_files = {
        "Bronze claim": bronze_root / "claims" / "bronze-claim-demo-001.yaml",
        "Bronze bundle manifest": bronze_root / "evidence-bundle-manifest-v0.1.3.yaml",
        "Silver signed assertion": silver_root / "runtime" / "silver-signed-bundle-assertion-v0.1.0.yaml",
        "Trust policy": silver_root / "runtime" / "verifier-b" / "trust-policy.yaml",
        "Revocation list": silver_root / "runtime" / "verifier-b" / "revocation-list.yaml",
    }

    missing = [label for label, path in required_files.items() if not path.exists()]
    if missing:
        for label in missing:
            print(f"ERROR: {label} not found: {required_files[label]}", file=sys.stderr)
        return 2

    # Handle output directory
    if output_dir.exists():
        if not args.force:
            print(f"ERROR: output directory already exists: {output_dir}", file=sys.stderr)
            print("  Use --force to overwrite.", file=sys.stderr)
            return 1
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine repo root (two levels up from bronze_root: demos/composed-bronze-demo-001)
    repo_root = bronze_root.parent.parent

    subset = output_dir / "source-repo-subset"

    # 1. Copy Bronze demo content (claims, evidence, docs, results, bundle manifest)
    bronze_dst = subset / "demos" / "composed-bronze-demo-001"
    bronze_files = _copy_tree_filtered(bronze_root, bronze_dst)

    # 2. Copy Silver runtime artifacts (assertion, trust policy, revocation list)
    silver_runtime_dst = subset / "demos" / "silver-demo-001" / "runtime"
    assertion_src = silver_root / "runtime" / "silver-signed-bundle-assertion-v0.1.0.yaml"
    _copy_file(assertion_src, silver_runtime_dst / "silver-signed-bundle-assertion-v0.1.0.yaml")
    _copy_file(
        silver_root / "runtime" / "verifier-b" / "trust-policy.yaml",
        silver_runtime_dst / "verifier-b" / "trust-policy.yaml",
    )
    _copy_file(
        silver_root / "runtime" / "verifier-b" / "revocation-list.yaml",
        silver_runtime_dst / "verifier-b" / "revocation-list.yaml",
    )

    # 3. Copy schemas
    schemas_src = repo_root / "schemas"
    schema_files = [
        "bronze-claim-schema-v0.1.2.md",
        "bronze-evidence-bundle-manifest-v0.1.3.md",
        "silver-signed-bundle-assertion-v0.1.0.md",
        "silver-revocation-list-v0.1.0.md",
        "silver-verification-report-v0.1.0.md",
    ]
    schemas_dst = subset / "schemas"
    for sf in schema_files:
        src = schemas_src / sf
        if src.exists():
            _copy_file(src, schemas_dst / sf)

    # 4. Copy reference tools (for auditability, not used by independent verifier)
    tools_claims_src = repo_root / "tools" / "claims"
    tools_claims_dst = subset / "tools" / "claims"
    claim_tools = [
        "generate_bronze_claim_v0_1_2.py",
        "validate_bronze_claim_v0_1_2.py",
        "verify_bronze_claim_evidence_v0_1_2.py",
        "generate_evidence_bundle_manifest_v0_1_3.py",
        "verify_evidence_bundle_manifest_v0_1_3.py",
    ]
    for ct in claim_tools:
        src = tools_claims_src / ct
        if src.exists():
            _copy_file(src, tools_claims_dst / ct)

    tools_silver_dst = subset / "tools" / "silver"
    report_validator_src = repo_root / "tools" / "silver" / "validate_silver_verification_report_v0_1_0.py"
    if report_validator_src.exists():
        _copy_file(report_validator_src, tools_silver_dst / "validate_silver_verification_report_v0_1_0.py")

    # 5. Generate package manifest
    manifest = {
        "package_version": "v0.1.0",
        "package_type": "proofrail.silver.independent_verification_package",
        "package_id": "proofrail-silver-demo-002-package",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "tools/silver/export_independent_verification_package_v0_1_0.py",
        "source": {
            "bronze_root": str(args.bronze_root),
            "silver_root": str(args.silver_root),
        },
        "verifier": {
            "verifier_demo": "silver-demo-002-independent-verifier",
            "verifier_version": "v0.1.0",
            "expected_report_schema": "silver-verification-report-v0.1.0",
        },
        "paths": {
            "signed_assertion": "source-repo-subset/demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml",
            "trust_policy": "source-repo-subset/demos/silver-demo-001/runtime/verifier-b/trust-policy.yaml",
            "revocation_list": "source-repo-subset/demos/silver-demo-001/runtime/verifier-b/revocation-list.yaml",
            "bundle_manifest": "source-repo-subset/demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml",
            "bronze_package_root": "source-repo-subset/demos/composed-bronze-demo-001",
            "report_output": "verification-report.json",
        },
        "limitations": [
            "Local independent verifier demo only.",
            "Not production packaging.",
            "Not third-party certification.",
            "Not Gold certification.",
        ],
    }

    manifest_path = output_dir / "package-manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))

    print(str(output_dir.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
