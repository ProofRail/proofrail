#!/usr/bin/env python3
"""Evidence bundle manifest verifier for ProofRail v0.1.3.

Recomputes SHA-256 checksums and file sizes for all files listed in a bundle
manifest and verifies they match the recorded values.

Usage:
  python3 tools/claims/verify_evidence_bundle_manifest_v0_1_3.py <manifest.yaml> <package-root>
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: verify_evidence_bundle_manifest_v0_1_3.py <manifest.yaml> <package-root>", file=sys.stderr)
        return 2

    manifest_path = Path(sys.argv[1])
    package_root = Path(sys.argv[2]).resolve()

    manifest = yaml.safe_load(manifest_path.read_text())
    if not isinstance(manifest, dict):
        print("FAIL: manifest root must be a mapping")
        return 1

    files = manifest.get("files")
    if not isinstance(files, list):
        print("FAIL: manifest files must be a list")
        return 1

    failures: list[str] = []
    verified = 0

    for entry in files:
        rel_path = entry.get("path", "")
        required = entry.get("required", False)
        expected_sha = entry.get("sha256")
        expected_size = entry.get("size_bytes")

        resolved = (package_root / rel_path).resolve()

        if not resolved.exists():
            if required:
                failures.append(f"MISSING: {rel_path}")
            continue

        actual_sha = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
        actual_size = resolved.stat().st_size

        if expected_sha and actual_sha != expected_sha:
            failures.append(f"MISMATCH: {rel_path} expected={expected_sha} actual={actual_sha}")
            continue

        if expected_size is not None and actual_size != expected_size:
            failures.append(f"SIZE_MISMATCH: {rel_path} expected={expected_size} actual={actual_size}")
            continue

        verified += 1

    if failures:
        print("FAIL: bundle verification failed")
        for f in failures:
            print(f"- {f}")
        return 1

    print(f"PASS: all {verified} bundle files verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
