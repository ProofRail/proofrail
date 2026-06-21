#!/usr/bin/env python3
"""Generate a demo Ed25519 attestor keypair and attestation trust policy.

Usage:
  python3 tools/silver/generate_demo_verifier_attestor_v0_1_0.py \
    --output-root demos/silver-demo-001/runtime/verifier-b \
    --attestor-id proofrail-demo-verifier-b \
    --key-id proofrail-demo-verifier-b-ed25519-attestation-001 \
    --force

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


def public_key_fingerprint(public_key) -> str:
    """SHA-256 fingerprint of raw 32-byte Ed25519 public key."""
    raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a demo Ed25519 attestor keypair and attestation trust policy"
    )
    parser.add_argument("--output-root", required=True, help="Output directory for keys and trust policy")
    parser.add_argument("--attestor-id", required=True, help="Attestor identity string")
    parser.add_argument("--key-id", required=True, help="Key identity string")
    parser.add_argument("--force", action="store_true", help="Overwrite existing keypair")
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    private_key_path = output_root / "attestor-private-key.pem"
    public_key_path = output_root / "attestor-public-key.pem"
    trust_policy_path = output_root / "attestation-trust-policy.yaml"

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

    # Build attestation trust policy
    fingerprint = public_key_fingerprint(public_key)

    trust_policy: dict[str, Any] = {
        "policy_type": "proofrail.silver.verifier_attestation_trust_policy",
        "policy_version": "v0.1.0",
        "trusted_attestors": [
            {
                "attestor_id": args.attestor_id,
                "key_id": args.key_id,
                "algorithm": "ed25519",
                "public_key_path": "attestor-public-key.pem",
                "public_key_fingerprint_sha256": fingerprint,
            }
        ],
        "limitations": [
            "Local demo trust policy only.",
            "Not production PKI.",
            "Not certification authority.",
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
