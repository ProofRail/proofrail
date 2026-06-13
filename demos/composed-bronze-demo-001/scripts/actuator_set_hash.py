#!/usr/bin/env python3
"""Compute deterministic ProofRail protected actuator set hash."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evidence" / "protected_actuator_set.json"


def canonical_manifest(path: Path) -> bytes:
    data = json.loads(path.read_text())
    if "contents" not in data or not isinstance(data["contents"], list):
        raise SystemExit("manifest must contain a contents list")
    data["contents"] = sorted(data["contents"])
    if "risk_tiers" in data:
        data["risk_tiers"] = {k: data["risk_tiers"][k] for k in sorted(data["risk_tiers"])}
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST
    digest = hashlib.sha256(canonical_manifest(path)).hexdigest()
    print(f"sha256:{digest}")


if __name__ == "__main__":
    main()
