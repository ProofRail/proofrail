#!/usr/bin/env python3
"""Verify a ProofRail Silver Signed Bundle Assertion v0.1.0.

Checks issuer trust, Ed25519 signature, assertion expiry, bundle manifest
checksum, and underlying v0.1.3 bundle integrity.

Usage:
  python3 tools/silver/verify_signed_bundle_assertion_v0_1_0.py \
    <assertion.yaml> <trust-policy.yaml> \
    --silver-root <silver-demo-root> \
    --bronze-package-root <bronze-demo-root>
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
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
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
except ImportError:
    print("ERROR: cryptography is required. Install with: pip install cryptography", file=sys.stderr)
    sys.exit(2)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="Verify a Silver Signed Bundle Assertion v0.1.0"
    )
    parser.add_argument("assertion", help="Path to signed assertion YAML")
    parser.add_argument("trust_policy", help="Path to trust policy YAML")
    parser.add_argument("--silver-root", required=True, help="Silver demo root directory")
    parser.add_argument("--bronze-package-root", required=True, help="Bronze evidence package root directory")
    parser.add_argument("--revocation-list", default=None, help="Path to revocation list YAML (optional)")
    parser.add_argument("--report", default=None, help="Path to write JSON verification report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    assertion_path = Path(args.assertion)
    trust_policy_path = Path(args.trust_policy)
    silver_root = Path(args.silver_root).resolve()
    bronze_root = Path(args.bronze_package_root).resolve()

    if not assertion_path.exists():
        print(f"ERROR: assertion not found: {assertion_path}", file=sys.stderr)
        return 2
    if not trust_policy_path.exists():
        print(f"ERROR: trust policy not found: {trust_policy_path}", file=sys.stderr)
        return 2

    assertion = yaml.safe_load(assertion_path.read_text())
    if not isinstance(assertion, dict):
        print("FAIL: assertion root must be a mapping")
        return 1

    policy = yaml.safe_load(trust_policy_path.read_text())
    if not isinstance(policy, dict):
        print("FAIL: trust policy root must be a mapping")
        return 1

    report: dict[str, Any] = {
        "assertion_path": str(assertion_path),
        "trust_policy_path": str(trust_policy_path),
        "checks": [],
    }

    def record(name: str, passed: bool, detail: str = ""):
        report["checks"].append({"check": name, "passed": passed, "detail": detail})

    # --- 1. Trust check ---
    issuer = assertion.get("issuer", {})
    assertion_issuer_id = issuer.get("issuer_id", "")
    assertion_key_id = issuer.get("key_id", "")

    trusted_issuers = policy.get("trusted_issuers", [])
    matched_issuer = None

    for ti in trusted_issuers:
        if ti.get("issuer_id") == assertion_issuer_id:
            if ti.get("key_id") == assertion_key_id:
                matched_issuer = ti
                break

    if matched_issuer is None:
        # Distinguish issuer vs key_id mismatch
        issuer_ids = [ti.get("issuer_id") for ti in trusted_issuers]
        if assertion_issuer_id not in issuer_ids:
            msg = f"FAIL: issuer not trusted (issuer_id={assertion_issuer_id})"
            print(msg)
            record("trust_check", False, msg)
        else:
            msg = f"FAIL: key_id not trusted (key_id={assertion_key_id})"
            print(msg)
            record("trust_check", False, msg)
        _write_report(args.report, report)
        return 1

    record("trust_check", True, f"issuer_id={assertion_issuer_id} key_id={assertion_key_id}")

    # --- 2. Algorithm check ---
    sig_meta = assertion.get("signature", {})
    if sig_meta.get("algorithm") != "ed25519":
        msg = f"FAIL: unsupported signature algorithm: {sig_meta.get('algorithm')}"
        print(msg)
        record("algorithm_check", False, msg)
        _write_report(args.report, report)
        return 1
    record("algorithm_check", True, "ed25519")

    # --- 3. Expiry check ---
    validity = assertion.get("validity", {})
    issued_at_str = validity.get("issued_at", "")
    expires_at_str = validity.get("expires_at", "")

    try:
        issued_at = datetime.fromisoformat(issued_at_str.replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        msg = f"FAIL: invalid validity timestamps: {e}"
        print(msg)
        record("expiry_check", False, msg)
        _write_report(args.report, report)
        return 1

    now = datetime.now(timezone.utc)
    if now < issued_at:
        msg = f"FAIL: assertion not yet valid (issued_at={issued_at_str})"
        print(msg)
        record("expiry_check", False, msg)
        _write_report(args.report, report)
        return 1
    if now > expires_at:
        msg = f"FAIL: assertion expired (expires_at={expires_at_str})"
        print(msg)
        record("expiry_check", False, msg)
        _write_report(args.report, report)
        return 1
    record("expiry_check", True, f"issued_at={issued_at_str} expires_at={expires_at_str}")

    # --- 4. Resolve and checksum bundle manifest ---
    subject = assertion.get("subject", {})
    bundle_manifest_rel = subject.get("bundle_manifest", "")
    bundle_manifest_path = (silver_root / bundle_manifest_rel).resolve()

    if not bundle_manifest_path.exists():
        msg = f"FAIL: bundle manifest not found: {bundle_manifest_rel}"
        print(msg)
        record("manifest_resolve", False, msg)
        _write_report(args.report, report)
        return 1

    raw_bytes = bundle_manifest_path.read_bytes()
    actual_sha = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    expected_sha = subject.get("bundle_manifest_sha256", "")

    if actual_sha != expected_sha:
        msg = f"FAIL: bundle manifest checksum mismatch (expected={expected_sha} actual={actual_sha})"
        print(msg)
        record("checksum_check", False, msg)
        _write_report(args.report, report)
        return 1
    record("checksum_check", True, actual_sha)

    # --- 5. Revocation check (optional) ---
    revocation_list_path = getattr(args, "revocation_list", None)
    if revocation_list_path:
        rev_path = Path(revocation_list_path)
        if not rev_path.exists():
            print(f"ERROR: revocation list not found: {revocation_list_path}", file=sys.stderr)
            report["revocation_check"] = {"performed": False, "status": "not_performed"}
            _write_report(args.report, report)
            return 2

        rev_list = yaml.safe_load(rev_path.read_text())
        if not isinstance(rev_list, dict):
            print("FAIL: revocation list root must be a mapping")
            report["revocation_check"] = {"performed": True, "status": "fail", "reason": "invalid_format"}
            _write_report(args.report, report)
            return 1

        assertion_id = assertion.get("assertion_id", "")

        # Check revoked assertions
        for entry in rev_list.get("revoked_assertions", []):
            if entry.get("assertion_id") == assertion_id:
                msg = f"FAIL: assertion revoked (assertion_id={assertion_id})"
                print(msg)
                record("revocation_check", False, msg)
                report["revocation_check"] = {
                    "performed": True,
                    "revocation_list": str(revocation_list_path),
                    "status": "fail",
                    "reason": "assertion_revoked",
                }
                _write_report(args.report, report)
                return 1

        # Check revoked issuer keys
        for entry in rev_list.get("revoked_issuer_keys", []):
            if (entry.get("issuer_id") == assertion_issuer_id
                    and entry.get("key_id") == assertion_key_id):
                msg = f"FAIL: issuer key revoked (issuer_id={assertion_issuer_id} key_id={assertion_key_id})"
                print(msg)
                record("revocation_check", False, msg)
                report["revocation_check"] = {
                    "performed": True,
                    "revocation_list": str(revocation_list_path),
                    "status": "fail",
                    "reason": "issuer_key_revoked",
                }
                _write_report(args.report, report)
                return 1

        # Check revoked bundles
        for entry in rev_list.get("revoked_bundles", []):
            if entry.get("bundle_manifest_sha256") == actual_sha:
                msg = f"FAIL: bundle revoked (bundle_manifest_sha256={actual_sha})"
                print(msg)
                record("revocation_check", False, msg)
                report["revocation_check"] = {
                    "performed": True,
                    "revocation_list": str(revocation_list_path),
                    "status": "fail",
                    "reason": "bundle_revoked",
                }
                _write_report(args.report, report)
                return 1

        record("revocation_check", True, "no revocation matches")
        report["revocation_check"] = {
            "performed": True,
            "revocation_list": str(revocation_list_path),
            "status": "pass",
        }
    else:
        report["revocation_check"] = {"performed": False, "status": "not_performed"}

    # --- 6. Signature check ---
    public_key_pem = matched_issuer.get("public_key_pem", "")
    if isinstance(public_key_pem, str):
        public_key_bytes = public_key_pem.encode("utf-8")
    else:
        public_key_bytes = public_key_pem

    try:
        public_key = load_pem_public_key(public_key_bytes)
    except Exception as e:
        msg = f"FAIL: cannot load public key from trust policy: {e}"
        print(msg)
        record("signature_check", False, msg)
        _write_report(args.report, report)
        return 1

    signature_b64 = sig_meta.get("signature_value", "")
    try:
        signature_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        msg = f"FAIL: cannot decode signature: {e}"
        print(msg)
        record("signature_check", False, msg)
        _write_report(args.report, report)
        return 1

    try:
        public_key.verify(signature_bytes, raw_bytes)
    except InvalidSignature:
        msg = "FAIL: signature verification failed"
        print(msg)
        record("signature_check", False, msg)
        _write_report(args.report, report)
        return 1
    except Exception as e:
        msg = f"FAIL: signature verification error: {e}"
        print(msg)
        record("signature_check", False, msg)
        _write_report(args.report, report)
        return 1
    record("signature_check", True, "ed25519 signature valid")

    # --- 7. Underlying bundle verification ---
    result = subprocess.run(
        [
            sys.executable,
            "tools/claims/verify_evidence_bundle_manifest_v0_1_3.py",
            str(bundle_manifest_path),
            str(bronze_root),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = "FAIL: underlying bundle verification failed"
        detail = result.stdout.strip() if result.stdout.strip() else result.stderr.strip()
        print(msg)
        if detail:
            print(f"  {detail}")
        record("bundle_check", False, f"{msg}: {detail}")
        _write_report(args.report, report)
        return 1
    record("bundle_check", True, result.stdout.strip())

    # --- All checks passed ---
    report["result"] = "PASS"
    report["issuer_id"] = assertion_issuer_id
    report["key_id"] = assertion_key_id
    report["signature_fingerprint"] = sig_meta.get("public_key_fingerprint_sha256", "")
    report["bundle_manifest_sha256"] = actual_sha
    report["issued_at"] = issued_at_str
    report["expires_at"] = expires_at_str

    print("PASS: Silver signed bundle assertion verified")
    _write_report(args.report, report)
    return 0


def _write_report(report_path: str | None, report: dict[str, Any]) -> None:
    if report_path:
        p = Path(report_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2, default=str) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
