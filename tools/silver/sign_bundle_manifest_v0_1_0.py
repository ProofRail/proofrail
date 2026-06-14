#!/usr/bin/env python3
"""Sign a ProofRail Bronze v0.1.3 evidence bundle manifest with Ed25519.

Usage:
  python3 tools/silver/sign_bundle_manifest_v0_1_0.py demos/silver-demo-001 \
    --private-key demos/silver-demo-001/runtime/issuer-a/private-key.pem \
    --output demos/silver-demo-001/runtime/silver-signed-bundle-assertion-v0.1.0.yaml

Produces a Silver Signed Bundle Assertion v0.1.0 YAML file.
The signature is over the raw bytes of the bundle manifest file.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import sys
from datetime import datetime, timedelta, timezone
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
        PublicFormat,
        load_pem_private_key,
    )
except ImportError:
    print("ERROR: cryptography is required. Install with: pip install cryptography", file=sys.stderr)
    sys.exit(2)


DEFAULT_INPUT = "silver-input-v0.1.0.yaml"
DEFAULT_OUTPUT = "runtime/silver-signed-bundle-assertion-v0.1.0.yaml"


def public_key_fingerprint(public_key) -> str:
    """SHA-256 fingerprint of raw 32-byte Ed25519 public key."""
    raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sign a Bronze v0.1.3 bundle manifest with Ed25519"
    )
    parser.add_argument("demo_root", help="Silver demo root directory")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Input filename (default: {DEFAULT_INPUT})")
    parser.add_argument("--private-key", required=True, help="Path to Ed25519 private key PEM")
    parser.add_argument("--output", default=None, help=f"Output assertion path (default: <demo_root>/{DEFAULT_OUTPUT})")
    parser.add_argument("--validity-days", type=int, default=None, help="Validity period in days (default: from input or 90)")
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

    silver_meta = spec.get("silver", {})
    issuer_meta = spec.get("issuer", {})
    subject_meta = spec.get("subject", {})
    validity_meta = spec.get("validity", {})

    # Resolve bundle manifest
    bundle_manifest_rel = subject_meta.get("bundle_manifest", "")
    bundle_manifest_path = (demo_root / bundle_manifest_rel).resolve()

    if not bundle_manifest_path.exists():
        print(f"ERROR: bundle manifest not found: {bundle_manifest_path}", file=sys.stderr)
        return 1

    # Read raw bytes and compute checksum
    raw_bytes = bundle_manifest_path.read_bytes()
    manifest_sha256 = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()

    # Load private key
    private_key_path = Path(args.private_key)
    if not private_key_path.exists():
        print(f"ERROR: private key not found: {private_key_path}", file=sys.stderr)
        return 2

    private_key = load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        print("ERROR: private key is not Ed25519", file=sys.stderr)
        return 2

    # Sign raw bytes
    signature_bytes = private_key.sign(raw_bytes)
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    # Public key fingerprint
    public_key = private_key.public_key()
    fingerprint = public_key_fingerprint(public_key)

    # Validity timestamps (timezone-aware UTC)
    validity_days = args.validity_days or validity_meta.get("validity_days", 90)
    now = datetime.now(timezone.utc)
    issued_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_at = (now + timedelta(days=validity_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build assertion
    assertion: dict[str, Any] = {
        "assertion_version": silver_meta.get("assertion_version", "v0.1.0"),
        "assertion_type": silver_meta.get("assertion_type", "proofrail.silver.signed_bundle_assertion"),
        "assertion_id": silver_meta.get("assertion_id"),
        "assertion_label": silver_meta.get("assertion_label"),
        "issuer": {
            "issuer_id": issuer_meta.get("issuer_id"),
            "issuer_label": issuer_meta.get("issuer_label"),
            "key_id": issuer_meta.get("key_id"),
            "algorithm": "ed25519",
        },
        "subject": {
            "bundle_manifest": bundle_manifest_rel,
            "bundle_manifest_type": subject_meta.get("bundle_manifest_type"),
            "bundle_manifest_sha256": manifest_sha256,
            "signed_payload": "raw_bundle_manifest_bytes",
        },
        "validity": {
            "issued_at": issued_at,
            "expires_at": expires_at,
        },
        "signature": {
            "algorithm": "ed25519",
            "signature_encoding": "base64",
            "signature_value": signature_b64,
            "public_key_fingerprint_sha256": fingerprint,
        },
        "generated_by": spec.get("generated_by", "tools/silver/sign_bundle_manifest_v0_1_0.py"),
    }

    # Write output
    output_path = Path(args.output) if args.output else demo_root / DEFAULT_OUTPUT
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_text = yaml.safe_dump(assertion, sort_keys=False, allow_unicode=True)
    output_path.write_text(output_text)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
