#!/usr/bin/env python3
"""Generate a ProofRail Bronze Evidence Bundle Manifest v0.1.3.

Usage:
  python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py <package-root>
  python3 tools/claims/generate_evidence_bundle_manifest_v0_1_3.py <package-root> --input <input-yaml> --output <output-yaml>

The package root must contain a bundle input YAML (default: bundle-input-v0.1.3.yaml).

This tool checksums the entire portable evidence package — claim file, evidence
files, schema documents, tooling scripts, and documentation. It does not certify
production conformance.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


DEFAULT_INPUT = "bundle-input-v0.1.3.yaml"
DEFAULT_OUTPUT = "evidence-bundle-manifest-v0.1.3.yaml"


def file_sha256(path: Path) -> str:
    """Compute SHA-256 over raw file bytes."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: {path} must be a YAML mapping")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a ProofRail Bronze Evidence Bundle Manifest v0.1.3"
    )
    parser.add_argument(
        "package_root",
        help="Evidence package or demo root containing bundle input YAML",
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Bundle input filename relative to package root (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output manifest filename relative to package root (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit 0 even if required files are missing (record them in validation.missing_files)",
    )
    args = parser.parse_args()

    package_root = Path(args.package_root).resolve()
    input_path = package_root / args.input

    if not input_path.exists():
        print(f"ERROR: bundle input not found: {input_path}", file=sys.stderr)
        return 2

    spec = load_yaml(input_path)

    bundle_meta = spec.get("bundle", {})
    if not isinstance(bundle_meta, dict):
        print("ERROR: bundle section must be a mapping", file=sys.stderr)
        return 2

    files_spec = spec.get("files", [])
    if not isinstance(files_spec, list):
        print("ERROR: files section must be a list", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    enriched_files: list[dict[str, Any]] = []
    missing_files: list[str] = []

    for entry in files_spec:
        rel_path = entry.get("path", "")
        role = entry.get("role", "")
        required = entry.get("required", False)

        resolved = (package_root / rel_path).resolve()

        file_entry: dict[str, Any] = {
            "path": rel_path,
            "role": role,
            "required": required,
        }

        if resolved.exists():
            file_entry["sha256"] = file_sha256(resolved)
            file_entry["size_bytes"] = resolved.stat().st_size
        else:
            file_entry["sha256"] = None
            file_entry["size_bytes"] = None
            if required:
                missing_files.append(rel_path)

        enriched_files.append(file_entry)

    manifest: dict[str, Any] = {
        "manifest_version": bundle_meta.get("manifest_version", "v0.1.3"),
        "manifest_type": "proofrail.bronze.evidence_bundle",
        "bundle_id": bundle_meta.get("bundle_id"),
        "bundle_label": bundle_meta.get("bundle_label"),
        "profile": bundle_meta.get("profile", "bronze"),
        "environment": bundle_meta.get("environment"),
        "subject_claim": bundle_meta.get("subject_claim"),
        "generated_at": now,
        "generated_by": bundle_meta.get("generated_by"),
        "files": enriched_files,
        "validation": {
            "missing_files": missing_files,
            "file_count": len(enriched_files),
        },
    }

    output_path = package_root / args.output
    output_text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    output_path.write_text(output_text)

    print(output_path)

    if missing_files:
        print(f"WARNING: {len(missing_files)} required file(s) missing:", file=sys.stderr)
        for m in missing_files:
            print(f"  - {m}", file=sys.stderr)
        if not args.allow_missing:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
