#!/usr/bin/env python3
"""Generate a ProofRail Bronze Claim Schema v0.1.2 YAML file.

Usage:
  python3 tools/claims/generate_bronze_claim_v0_1_2.py <package-root>
  python3 tools/claims/generate_bronze_claim_v0_1_2.py <package-root> --output <path>

The package root must contain:
  claim-input-v0.1.2.yaml

This tool performs deterministic claim assembly, evidence-path checks, and
evidence checksum computation. It does not certify production conformance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    raise SystemExit("ERROR: PyYAML is required. Install with: pip install pyyaml")


INPUT_NAME = "claim-input-v0.1.2.yaml"
DEFAULT_OUTPUT = "claims/bronze-claim-demo-001.yaml"


def canonical_sha256(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: {path} must be a YAML mapping")
    return data


def load_protected_actuator_set(package_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    pas_spec = spec.get("protected_actuator_set", {})
    if not isinstance(pas_spec, dict):
        raise SystemExit("ERROR: protected_actuator_set must be a mapping in claim input")

    manifest_rel = pas_spec.get("manifest")
    if not manifest_rel:
        raise SystemExit("ERROR: protected_actuator_set.manifest is required in claim input")

    manifest_path = package_root / manifest_rel
    if not manifest_path.exists():
        raise SystemExit(f"ERROR: protected actuator manifest not found: {manifest_rel}")

    manifest = json.loads(manifest_path.read_text())

    contents = manifest.get("contents", [])
    if isinstance(contents, list):
        manifest_for_hash = dict(manifest)
        manifest_for_hash["contents"] = sorted(contents)
    else:
        manifest_for_hash = manifest

    result = {
        "name": manifest.get("name"),
        "surface": manifest.get("surface"),
        "hash": canonical_sha256(manifest_for_hash),
    }

    if pas_spec.get("include_contents", True) and isinstance(contents, list):
        result["contents"] = contents

    return result


def evidence_missing(package_root: Path, evidence: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for value in evidence.values():
        if isinstance(value, str):
            p = package_root / value
            if not p.exists() or p.stat().st_size == 0:
                missing.append(value)
    return missing


def compute_evidence_checksums(package_root: Path, evidence: dict[str, Any]) -> dict[str, str]:
    """Compute SHA-256 checksums over raw bytes for all evidence files."""
    checksums: dict[str, str] = {}
    paths = sorted(v for v in evidence.values() if isinstance(v, str))
    for rel_path in paths:
        full = package_root / rel_path
        if full.exists() and full.stat().st_size > 0:
            digest = hashlib.sha256(full.read_bytes()).hexdigest()
            checksums[rel_path] = f"sha256:{digest}"
    return checksums


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_root", help="Evidence package or demo root containing claim-input-v0.1.2.yaml")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output claim path relative to package root. Default: {DEFAULT_OUTPUT}")
    args = parser.parse_args()

    package_root = Path(args.package_root).resolve()
    input_path = package_root / INPUT_NAME

    if not input_path.exists():
        raise SystemExit(f"ERROR: claim input not found: {input_path}")

    spec = load_yaml(input_path)

    claim_meta = spec.get("claim", {})
    if not isinstance(claim_meta, dict):
        raise SystemExit("ERROR: claim section must be a mapping")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    compact_now = now.replace("-", "").replace(":", "")

    claim_id_prefix = claim_meta.get("claim_id_prefix", "proofrail-bronze-claim")
    claim_id = claim_meta.get("claim_id") or f"{claim_id_prefix}-{compact_now}"

    evidence = spec.get("evidence", {})
    if not isinstance(evidence, dict):
        raise SystemExit("ERROR: evidence section must be a mapping")

    validation = spec.get("validation", {})
    if not isinstance(validation, dict):
        raise SystemExit("ERROR: validation section must be a mapping")

    claim: dict[str, Any] = {
        "spec_version": claim_meta.get("spec_version", "v0.1.2"),
        "claim_type": claim_meta.get("claim_type"),
        "claim_id": claim_id,
        "claim_label": claim_meta.get("claim_label"),
        "profile": claim_meta.get("profile", "bronze"),
        "mode": claim_meta.get("mode"),
        "environment": claim_meta.get("environment"),
        "surfaces_in_scope": claim_meta.get("surfaces_in_scope"),
        "substrate": spec.get("substrate"),
        "protected_actuator_set": load_protected_actuator_set(package_root, spec),
        "controls": spec.get("controls"),
        "control_details": spec.get("control_details"),
        "control_mapping": spec.get("control_mapping"),
        "evidence": evidence,
        "evidence_checksums": compute_evidence_checksums(package_root, evidence),
        "validation": {
            "type": validation.get("type"),
            "validator": validation.get("validator", "ProofRail Bronze claim validator v0.1.2 structural check"),
            "generated_at": now,
            "missing_evidence_files": evidence_missing(package_root, evidence),
        },
        "limitations": spec.get("limitations"),
    }

    output_path = package_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_text = yaml.safe_dump(claim, sort_keys=False, allow_unicode=True)
    output_path.write_text(output_text)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
