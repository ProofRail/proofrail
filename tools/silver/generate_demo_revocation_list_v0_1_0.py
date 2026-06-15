#!/usr/bin/env python3
"""Generate a demo Silver Revocation List v0.1.0.

Usage:
  python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001
  python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
    --revoke-assertion proofrail-silver-demo-001 --reason "demo assertion revocation"
  python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
    --revoke-issuer-key proofrail-demo-issuer-a:proofrail-demo-issuer-a-ed25519-001 \
    --reason "demo key revocation"
  python3 tools/silver/generate_demo_revocation_list_v0_1_0.py demos/silver-demo-001 \
    --revoke-bundle-sha256 sha256:<64 hex> --reason "demo bundle revocation"

This is a demo revocation list generator for local relying-party revocation.
It does not implement production PKI revocation, OCSP, or public certificate
revocation infrastructure.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


DEFAULT_OUTPUT = "runtime/verifier-b/revocation-list.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a demo Silver Revocation List v0.1.0"
    )
    parser.add_argument("demo_root", help="Silver demo root directory")
    parser.add_argument("--output", default=None, help=f"Output path (default: <demo_root>/{DEFAULT_OUTPUT})")
    parser.add_argument("--force", action="store_true", help="Overwrite existing revocation list")
    parser.add_argument("--revoke-assertion", default=None, help="Assertion ID to revoke")
    parser.add_argument("--revoke-issuer-key", default=None, help="Issuer key to revoke (format: issuer_id:key_id)")
    parser.add_argument("--revoke-bundle-sha256", default=None, help="Bundle manifest SHA-256 to revoke")
    parser.add_argument("--reason", default="demo revocation", help="Revocation reason (default: demo revocation)")
    args = parser.parse_args()

    demo_root = Path(args.demo_root).resolve()
    output_path = Path(args.output).resolve() if args.output else demo_root / DEFAULT_OUTPUT

    if output_path.exists() and not args.force:
        print(f"ERROR: revocation list already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    revoked_assertions: list[dict[str, str]] = []
    revoked_issuer_keys: list[dict[str, str]] = []
    revoked_bundles: list[dict[str, str]] = []

    if args.revoke_assertion:
        revoked_assertions.append({
            "assertion_id": args.revoke_assertion,
            "reason": args.reason,
            "revoked_at": now,
        })

    if args.revoke_issuer_key:
        parts = args.revoke_issuer_key.split(":", 1)
        if len(parts) != 2:
            print("ERROR: --revoke-issuer-key must be in format issuer_id:key_id", file=sys.stderr)
            return 2
        revoked_issuer_keys.append({
            "issuer_id": parts[0],
            "key_id": parts[1],
            "reason": args.reason,
            "revoked_at": now,
        })

    if args.revoke_bundle_sha256:
        revoked_bundles.append({
            "bundle_manifest_sha256": args.revoke_bundle_sha256,
            "reason": args.reason,
            "revoked_at": now,
        })

    revocation_list: dict[str, Any] = {
        "revocation_list_version": "v0.1.0",
        "list_id": "proofrail-silver-demo-001-verifier-b-revocation-list",
        "list_label": "ProofRail Minimal Silver Demo 001 Verifier B Revocation List",
        "generated_at": now,
        "generated_by": "tools/silver/generate_demo_revocation_list_v0_1_0.py",
        "revoked_assertions": revoked_assertions,
        "revoked_issuer_keys": revoked_issuer_keys,
        "revoked_bundles": revoked_bundles,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_text = yaml.safe_dump(revocation_list, sort_keys=False, allow_unicode=True)
    output_path.write_text(output_text)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
