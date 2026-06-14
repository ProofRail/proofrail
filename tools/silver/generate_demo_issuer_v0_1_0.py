#!/usr/bin/env python3
"""Generate a demo Ed25519 issuer keypair and trust policy for ProofRail Silver v0.1.0.

Usage:
  python3 tools/silver/generate_demo_issuer_v0_1_0.py demos/silver-demo-001
  python3 tools/silver/generate_demo_issuer_v0_1_0.py demos/silver-demo-001 --force

This is a demo key generator. Do not use generated keys for production purposes.
Private keys are written to a runtime directory that should be gitignored.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )
except ImportError:
    print("ERROR: cryptography is required. Install with: pip install cryptography", file=sys.stderr)
    sys.exit(2)


DEFAULT_INPUT = "silver-input-v0.1.0.yaml"


def public_key_fingerprint(public_key) -> str:
    """SHA-256 fingerprint of raw 32-byte Ed25519 public key."""
    raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a demo Ed25519 issuer keypair and trust policy"
    )
    parser.add_argument("demo_root", help="Silver demo root directory")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Input filename (default: {DEFAULT_INPUT})")
    parser.add_argument("--force", action="store_true", help="Overwrite existing keypair")
    args = parser.parse_args()

    demo_root = Path(args.demo_root).resolve()
    input_path = demo_root / args.input

    if not input_path.exists():
        print(f"ERROR: silver input not found: {input_path}", file=sys.stderr)
        return 2

    spec = yaml.safe_load(input_path.read_text())
    if not isinstance(spec, dict):
        print("ERROR: silver input must be a YAML mapping", file=sys.stderr)
        return 2

    issuer_meta = spec.get("issuer", {})
    silver_meta = spec.get("silver", {})

    # Directories
    issuer_dir = demo_root / "runtime" / "issuer-a"
    verifier_dir = demo_root / "runtime" / "verifier-b"
    issuer_dir.mkdir(parents=True, exist_ok=True)
    verifier_dir.mkdir(parents=True, exist_ok=True)

    private_key_path = issuer_dir / "private-key.pem"
    public_key_path = issuer_dir / "public-key.pem"
    trust_policy_path = verifier_dir / "trust-policy.yaml"

    if private_key_path.exists() and not args.force:
        print(f"ERROR: keypair already exists: {private_key_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    # Generate Ed25519 keypair
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Write private key PEM
    private_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    private_key_path.write_bytes(private_pem)
    try:
        os.chmod(private_key_path, 0o600)
    except OSError:
        pass  # Best-effort on platforms that don't support chmod

    # Write public key PEM
    public_pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    public_key_path.write_bytes(public_pem)

    # Build trust policy
    fingerprint = public_key_fingerprint(public_key)
    public_pem_str = public_pem.decode("utf-8")

    trust_policy: dict[str, Any] = {
        "trust_policy_version": "v0.1.0",
        "policy_id": "proofrail-silver-demo-001-verifier-b-trust-policy",
        "policy_label": "ProofRail Minimal Silver Demo 001 Verifier B Trust Policy",
        "trusted_issuers": [
            {
                "issuer_id": issuer_meta.get("issuer_id", "proofrail-demo-issuer-a"),
                "issuer_label": issuer_meta.get("issuer_label", "ProofRail Demo Issuer A"),
                "key_id": issuer_meta.get("key_id", "proofrail-demo-issuer-a-ed25519-001"),
                "algorithm": "ed25519",
                "public_key_pem": public_pem_str,
                "public_key_fingerprint_sha256": fingerprint,
            }
        ],
    }

    trust_policy_text = yaml.safe_dump(trust_policy, sort_keys=False, allow_unicode=True)
    trust_policy_path.write_text(trust_policy_text)

    print(private_key_path)
    print(public_key_path)
    print(trust_policy_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
