#!/usr/bin/env python3
"""Sign a ProofRail Silver Verifier Output Attestation v0.1.0.

Produces a detached, signed attestation binding a verifier's identity to its
verification report and profile conformance report.

Usage:
  python3 tools/silver/sign_verifier_output_attestation_v0_1_0.py \
    --verification-report <report.json> \
    --conformance-report <conformance.json> \
    --private-key <attestor-private-key.pem> \
    --attestor-id <id> \
    --attestor-version <version> \
    --key-id <key-id> \
    --output <attestation.json>

For silver.independent mode, add:
    --package-manifest <package-manifest.yaml>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
except ImportError:
    print("ERROR: cryptography is required. Install with: pip install cryptography", file=sys.stderr)
    sys.exit(2)


LIMITATIONS = [
    "Verifier output attestation is not certification.",
    "Not Gold certification.",
    "Not production PKI.",
    "Not regulator approval.",
    "Not production deployment assurance.",
]


def _sha256_file(path: Path) -> str:
    """Compute sha256:<hex> of a file."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _check_path_traversal(path_str: str, label: str) -> str | None:
    """Return error message if path contains '..' component, else None."""
    parts = Path(path_str).parts
    if ".." in parts:
        return f"subject path contains '..' component: {label}={path_str}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sign a Silver Verifier Output Attestation v0.1.0"
    )
    parser.add_argument("--verification-report", required=True, help="Path to Silver Verification Report JSON")
    parser.add_argument("--conformance-report", required=True, help="Path to Silver Profile Conformance Report JSON")
    parser.add_argument("--package-manifest", default=None, help="Path to package manifest YAML (required for silver.independent)")
    parser.add_argument("--private-key", required=True, help="Path to Ed25519 attestor private key PEM")
    parser.add_argument("--attestor-id", required=True, help="Attestor identity (must match verifier_id in verification report)")
    parser.add_argument("--attestor-version", required=True, help="Attestor version string")
    parser.add_argument("--key-id", required=True, help="Attestor key identity string")
    parser.add_argument("--attestation-id", default=None, help="Explicit attestation ID (default: derived)")
    parser.add_argument("--output", required=True, help="Output attestation JSON path")
    args = parser.parse_args()

    # --- Load and validate verification report ---
    vr_path = Path(args.verification_report)
    if not vr_path.exists():
        print(f"ERROR: verification report not found: {vr_path}", file=sys.stderr)
        return 2

    try:
        vr = json.loads(vr_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in verification report: {e}", file=sys.stderr)
        return 2

    if not isinstance(vr, dict):
        print("ERROR: verification report root must be a JSON object", file=sys.stderr)
        return 2

    if vr.get("report_version") != "v0.1.0":
        print(f"ERROR: expected report_version 'v0.1.0', got '{vr.get('report_version')}'", file=sys.stderr)
        return 2

    if vr.get("report_type") != "proofrail.silver.verification_report":
        print(f"ERROR: expected report_type 'proofrail.silver.verification_report', got '{vr.get('report_type')}'", file=sys.stderr)
        return 2

    # --- Load and validate conformance report ---
    cr_path = Path(args.conformance_report)
    if not cr_path.exists():
        print(f"ERROR: conformance report not found: {cr_path}", file=sys.stderr)
        return 2

    try:
        cr = json.loads(cr_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in conformance report: {e}", file=sys.stderr)
        return 2

    if not isinstance(cr, dict):
        print("ERROR: conformance report root must be a JSON object", file=sys.stderr)
        return 2

    if cr.get("conformance_report_version") != "v0.2.1":
        print(f"ERROR: expected conformance_report_version 'v0.2.1', got '{cr.get('conformance_report_version')}'", file=sys.stderr)
        return 2

    if cr.get("conformance_report_type") != "proofrail.silver.profile_conformance_report":
        print(f"ERROR: expected conformance_report_type 'proofrail.silver.profile_conformance_report', got '{cr.get('conformance_report_type')}'", file=sys.stderr)
        return 2

    profile_block = cr.get("profile", {})
    profile_mode = profile_block.get("profile_mode", "")
    valid_modes = {"silver.base", "silver.base.demo", "silver.independent"}
    if profile_mode not in valid_modes:
        print(f"ERROR: invalid profile_mode '{profile_mode}' in conformance report", file=sys.stderr)
        return 2

    # --- Verify attestor identity matches verifier identity ---
    verifier_id = vr.get("verifier", {}).get("verifier_id", "")
    if args.attestor_id != verifier_id:
        print(f"ERROR: --attestor-id '{args.attestor_id}' does not match verifier_id '{verifier_id}' in verification report", file=sys.stderr)
        return 1

    # --- Check package manifest requirement ---
    if profile_mode == "silver.independent" and not args.package_manifest:
        print("ERROR: --package-manifest is required for silver.independent profile mode", file=sys.stderr)
        return 2

    # --- Validate subject paths for '..' ---
    vr_path_str = str(args.verification_report)
    cr_path_str = str(args.conformance_report)

    traversal_err = _check_path_traversal(vr_path_str, "verification-report")
    if traversal_err:
        print(f"ERROR: {traversal_err}", file=sys.stderr)
        return 1

    traversal_err = _check_path_traversal(cr_path_str, "conformance-report")
    if traversal_err:
        print(f"ERROR: {traversal_err}", file=sys.stderr)
        return 1

    if args.package_manifest:
        traversal_err = _check_path_traversal(str(args.package_manifest), "package-manifest")
        if traversal_err:
            print(f"ERROR: {traversal_err}", file=sys.stderr)
            return 1

    # --- Load private key ---
    private_key_path = Path(args.private_key)
    if not private_key_path.exists():
        print(f"ERROR: private key not found: {private_key_path}", file=sys.stderr)
        return 2

    private_key = load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        print("ERROR: private key is not Ed25519", file=sys.stderr)
        return 2

    # --- Compute subject hashes ---
    vr_sha256 = _sha256_file(vr_path)
    cr_sha256 = _sha256_file(cr_path)

    # --- Build subjects ---
    subjects: dict[str, Any] = {
        "verification_report": {
            "path": vr_path_str,
            "sha256": vr_sha256,
            "report_version": "v0.1.0",
            "report_type": "proofrail.silver.verification_report",
        },
        "profile_conformance_report": {
            "path": cr_path_str,
            "sha256": cr_sha256,
            "conformance_report_version": "v0.2.1",
            "conformance_report_type": "proofrail.silver.profile_conformance_report",
        },
        "package_manifest": None,
    }

    if args.package_manifest:
        pm_path = Path(args.package_manifest)
        if not pm_path.exists():
            print(f"ERROR: package manifest not found: {pm_path}", file=sys.stderr)
            return 2
        pm_sha256 = _sha256_file(pm_path)
        subjects["package_manifest"] = {
            "path": str(args.package_manifest),
            "sha256": pm_sha256,
            "package_type": "proofrail.silver.independent_verification_package",
            "package_format_version": "v0.2.1",
        }

    # --- Derive attestation ID ---
    vr_sha256_hex = vr_sha256.replace("sha256:", "")
    mode_slug = profile_mode.replace(".", "-")
    if args.attestation_id:
        attestation_id = args.attestation_id
    else:
        attestation_id = f"{args.attestor_id}-attestation-{vr_sha256_hex[:12]}-{mode_slug}"

    # --- Build signed payload ---
    signed_payload: dict[str, Any] = {
        "attestation_id": attestation_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "tools/silver/sign_verifier_output_attestation_v0_1_0.py",
        "attestor": {
            "attestor_id": args.attestor_id,
            "attestor_role": "silver_verifier",
            "attestor_version": args.attestor_version,
            "key_id": args.key_id,
            "signature_algorithm": "ed25519",
        },
        "profile": {
            "profile_id": profile_block.get("profile_id", "proofrail.silver.profile"),
            "profile_version": profile_block.get("profile_version", "v0.2.1"),
            "profile_mode": profile_mode,
        },
        "decision": {
            "status": cr.get("decision", {}).get("status", ""),
            "reason": cr.get("decision", {}).get("reason", ""),
        },
        "subjects": subjects,
        "limitations": list(LIMITATIONS),
    }

    # --- Sign canonical JSON ---
    canonical_bytes = json.dumps(
        signed_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")

    signature_bytes = private_key.sign(canonical_bytes)
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    # --- Build attestation ---
    attestation: dict[str, Any] = {
        "attestation_version": "v0.1.0",
        "attestation_type": "proofrail.silver.verifier_output_attestation",
        "signed_payload": signed_payload,
        "signature": {
            "algorithm": "ed25519",
            "key_id": args.key_id,
            "signature_encoding": "base64",
            "signature": signature_b64,
        },
    }

    # --- Write output ---
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(attestation, indent=2, default=str) + "\n")

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
