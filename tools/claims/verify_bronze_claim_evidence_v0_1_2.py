#!/usr/bin/env python3
"""Evidence checksum verifier for ProofRail Bronze Claim Schema v0.1.2.

Recomputes SHA-256 checksums for evidence files referenced in a claim's
evidence_checksums mapping and verifies they match the recorded values.

Usage:
  python3 tools/claims/verify_bronze_claim_evidence_v0_1_2.py <claim.yaml> <package-root>
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
        print("Usage: verify_bronze_claim_evidence_v0_1_2.py <claim.yaml> <package-root>", file=sys.stderr)
        return 2

    claim_path = Path(sys.argv[1])
    package_root = Path(sys.argv[2]).resolve()

    claim = yaml.safe_load(claim_path.read_text())
    if not isinstance(claim, dict):
        print("FAIL: claim root must be a mapping")
        return 1

    checksums = claim.get("evidence_checksums")
    if not isinstance(checksums, dict) or not checksums:
        print("FAIL: evidence_checksums is missing or empty")
        return 1

    failures: list[str] = []
    verified = 0

    for rel_path, expected in sorted(checksums.items()):
        full_path = package_root / rel_path
        if not full_path.exists():
            failures.append(f"MISSING: {rel_path}")
            continue
        actual = "sha256:" + hashlib.sha256(full_path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f"MISMATCH: {rel_path} expected={expected} actual={actual}")
        else:
            verified += 1

    if failures:
        print("FAIL: evidence checksum verification failed")
        for f in failures:
            print(f"- {f}")
        return 1

    print(f"PASS: all {verified} evidence checksums verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
