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
import re
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

NOT_PERFORMED = {"status": "not_performed"}


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


def _init_report(args) -> dict[str, Any]:
    """Build the report skeleton with metadata and empty checks."""
    return {
        "report_version": "v0.1.0",
        "report_type": "proofrail.silver.verification_report",
        "report_id": "",
        "generated_at": "",
        "generated_by": "tools/silver/verify_signed_bundle_assertion_v0_1_0.py",
        "verifier": {
            "verifier_id": "proofrail-demo-verifier-b",
            "verifier_label": "ProofRail Demo Verifier B",
        },
        "inputs": {
            "assertion_path": str(args.assertion),
            "trust_policy_path": str(args.trust_policy),
            "revocation_list_path": args.revocation_list,
            "silver_root": args.silver_root,
            "bronze_package_root": args.bronze_package_root,
        },
        "assertion": {},
        "issuer": {},
        "subject": {},
        "decision": {"status": "", "reason": ""},
        "checks": {
            "trust_check": dict(NOT_PERFORMED),
            "algorithm_check": dict(NOT_PERFORMED),
            "validity_check": dict(NOT_PERFORMED),
            "bundle_manifest_checksum_check": dict(NOT_PERFORMED),
            "revocation_check": {"performed": False, "status": "not_performed"},
            "signature_check": dict(NOT_PERFORMED),
            "underlying_bundle_check": dict(NOT_PERFORMED),
        },
        "limitations": [
            "Local demo verification only.",
            "Not production PKI.",
            "Not third-party certification.",
            "Not Gold certification.",
        ],
    }


def _fail(report: dict[str, Any], reason: str) -> dict[str, Any]:
    """Set the decision block to fail."""
    report["decision"] = {"status": "fail", "reason": reason}
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return report


def _pass(report: dict[str, Any]) -> dict[str, Any]:
    """Set the decision block to pass."""
    report["decision"] = {"status": "pass", "reason": "all_checks_passed"}
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return report


def _write_report(report_path: str | None, report: dict[str, Any]) -> None:
    if report_path:
        p = Path(report_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2, default=str) + "\n")


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

    report = _init_report(args)

    # Populate assertion/issuer/subject metadata from the assertion YAML
    assertion_id = assertion.get("assertion_id", "")
    report["report_id"] = f"{assertion_id}-verification-report" if assertion_id else "unknown-verification-report"

    report["assertion"] = {
        "assertion_id": assertion_id,
        "assertion_version": assertion.get("assertion_version", ""),
        "assertion_type": assertion.get("assertion_type", ""),
    }

    issuer_block = assertion.get("issuer", {})
    assertion_issuer_id = issuer_block.get("issuer_id", "")
    assertion_key_id = issuer_block.get("key_id", "")
    sig_meta = assertion.get("signature", {})

    report["issuer"] = {
        "issuer_id": assertion_issuer_id,
        "key_id": assertion_key_id,
        "algorithm": sig_meta.get("algorithm", ""),
        "public_key_fingerprint_sha256": sig_meta.get("public_key_fingerprint_sha256", ""),
    }

    subject_block = assertion.get("subject", {})
    report["subject"] = {
        "bundle_manifest": subject_block.get("bundle_manifest", ""),
        "bundle_manifest_type": subject_block.get("bundle_manifest_type", ""),
        "bundle_manifest_sha256": subject_block.get("bundle_manifest_sha256", ""),
    }

    # --- 1. Trust check ---
    trusted_issuers = policy.get("trusted_issuers", [])
    matched_issuer = None

    for ti in trusted_issuers:
        if ti.get("issuer_id") == assertion_issuer_id:
            if ti.get("key_id") == assertion_key_id:
                matched_issuer = ti
                break

    if matched_issuer is None:
        issuer_ids = [ti.get("issuer_id") for ti in trusted_issuers]
        if assertion_issuer_id not in issuer_ids:
            msg = f"FAIL: issuer not trusted (issuer_id={assertion_issuer_id})"
            print(msg)
            report["checks"]["trust_check"] = {"status": "fail"}
            _write_report(args.report, _fail(report, "issuer_not_trusted"))
            return 1
        else:
            msg = f"FAIL: key_id not trusted (key_id={assertion_key_id})"
            print(msg)
            report["checks"]["trust_check"] = {"status": "fail"}
            _write_report(args.report, _fail(report, "key_id_not_trusted"))
            return 1

    report["checks"]["trust_check"] = {"status": "pass"}

    # --- 2. Algorithm check ---
    if sig_meta.get("algorithm") != "ed25519":
        msg = f"FAIL: unsupported signature algorithm: {sig_meta.get('algorithm')}"
        print(msg)
        report["checks"]["algorithm_check"] = {"status": "fail"}
        _write_report(args.report, _fail(report, "unsupported_algorithm"))
        return 1
    report["checks"]["algorithm_check"] = {"status": "pass"}

    # --- 3. Validity check ---
    validity = assertion.get("validity", {})
    issued_at_str = validity.get("issued_at", "")
    expires_at_str = validity.get("expires_at", "")

    try:
        issued_at = datetime.fromisoformat(issued_at_str.replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        msg = f"FAIL: invalid validity timestamps: {e}"
        print(msg)
        report["checks"]["validity_check"] = {
            "status": "fail",
            "issued_at": issued_at_str,
            "expires_at": expires_at_str,
        }
        _write_report(args.report, _fail(report, "invalid_validity_timestamps"))
        return 1

    now = datetime.now(timezone.utc)
    if now < issued_at:
        msg = f"FAIL: assertion not yet valid (issued_at={issued_at_str})"
        print(msg)
        report["checks"]["validity_check"] = {
            "status": "fail",
            "issued_at": issued_at_str,
            "expires_at": expires_at_str,
        }
        _write_report(args.report, _fail(report, "assertion_not_yet_valid"))
        return 1
    if now > expires_at:
        msg = f"FAIL: assertion expired (expires_at={expires_at_str})"
        print(msg)
        report["checks"]["validity_check"] = {
            "status": "fail",
            "issued_at": issued_at_str,
            "expires_at": expires_at_str,
        }
        _write_report(args.report, _fail(report, "assertion_expired"))
        return 1
    report["checks"]["validity_check"] = {
        "status": "pass",
        "issued_at": issued_at_str,
        "expires_at": expires_at_str,
    }

    # --- 4. Bundle manifest checksum check ---
    bundle_manifest_rel = subject_block.get("bundle_manifest", "")
    bundle_manifest_path = (silver_root / bundle_manifest_rel).resolve()

    if not bundle_manifest_path.exists():
        msg = f"FAIL: bundle manifest not found: {bundle_manifest_rel}"
        print(msg)
        expected_sha = subject_block.get("bundle_manifest_sha256", "")
        report["checks"]["bundle_manifest_checksum_check"] = {
            "status": "fail",
            "expected_sha256": expected_sha,
            "actual_sha256": "",
        }
        _write_report(args.report, _fail(report, "bundle_manifest_not_found"))
        return 1

    raw_bytes = bundle_manifest_path.read_bytes()
    actual_sha = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    expected_sha = subject_block.get("bundle_manifest_sha256", "")

    if actual_sha != expected_sha:
        msg = f"FAIL: bundle manifest checksum mismatch (expected={expected_sha} actual={actual_sha})"
        print(msg)
        report["checks"]["bundle_manifest_checksum_check"] = {
            "status": "fail",
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
        }
        _write_report(args.report, _fail(report, "bundle_manifest_checksum_mismatch"))
        return 1
    report["checks"]["bundle_manifest_checksum_check"] = {
        "status": "pass",
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
    }

    # --- 5. Revocation check (optional) ---
    revocation_list_path = getattr(args, "revocation_list", None)
    if revocation_list_path:
        rev_path = Path(revocation_list_path)
        if not rev_path.exists():
            print(f"ERROR: revocation list not found: {revocation_list_path}", file=sys.stderr)
            report["checks"]["revocation_check"] = {"performed": False, "status": "not_performed"}
            _write_report(args.report, _fail(report, "invalid_report_input"))
            return 2

        rev_list = yaml.safe_load(rev_path.read_text())
        if not isinstance(rev_list, dict):
            print("FAIL: revocation list root must be a mapping")
            report["checks"]["revocation_check"] = {
                "performed": True,
                "status": "fail",
                "revocation_list": str(revocation_list_path),
            }
            _write_report(args.report, _fail(report, "invalid_report_input"))
            return 1

        assertion_id_val = assertion.get("assertion_id", "")

        # Check revoked assertions
        for entry in rev_list.get("revoked_assertions", []):
            if entry.get("assertion_id") == assertion_id_val:
                msg = f"FAIL: assertion revoked (assertion_id={assertion_id_val})"
                print(msg)
                report["checks"]["revocation_check"] = {
                    "performed": True,
                    "status": "fail",
                    "revocation_list": str(revocation_list_path),
                }
                _write_report(args.report, _fail(report, "assertion_revoked"))
                return 1

        # Check revoked issuer keys
        for entry in rev_list.get("revoked_issuer_keys", []):
            if (entry.get("issuer_id") == assertion_issuer_id
                    and entry.get("key_id") == assertion_key_id):
                msg = f"FAIL: issuer key revoked (issuer_id={assertion_issuer_id} key_id={assertion_key_id})"
                print(msg)
                report["checks"]["revocation_check"] = {
                    "performed": True,
                    "status": "fail",
                    "revocation_list": str(revocation_list_path),
                }
                _write_report(args.report, _fail(report, "issuer_key_revoked"))
                return 1

        # Check revoked bundles
        for entry in rev_list.get("revoked_bundles", []):
            if entry.get("bundle_manifest_sha256") == actual_sha:
                msg = f"FAIL: bundle revoked (bundle_manifest_sha256={actual_sha})"
                print(msg)
                report["checks"]["revocation_check"] = {
                    "performed": True,
                    "status": "fail",
                    "revocation_list": str(revocation_list_path),
                }
                _write_report(args.report, _fail(report, "bundle_revoked"))
                return 1

        report["checks"]["revocation_check"] = {
            "performed": True,
            "status": "pass",
            "revocation_list": str(revocation_list_path),
        }
    else:
        report["checks"]["revocation_check"] = {"performed": False, "status": "not_performed"}

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
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, _fail(report, "signature_verification_failed"))
        return 1

    signature_b64 = sig_meta.get("signature_value", "")
    try:
        signature_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        msg = f"FAIL: cannot decode signature: {e}"
        print(msg)
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, _fail(report, "signature_verification_failed"))
        return 1

    try:
        public_key.verify(signature_bytes, raw_bytes)
    except InvalidSignature:
        msg = "FAIL: signature verification failed"
        print(msg)
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, _fail(report, "signature_verification_failed"))
        return 1
    except Exception as e:
        msg = f"FAIL: signature verification error: {e}"
        print(msg)
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, _fail(report, "signature_verification_failed"))
        return 1
    report["checks"]["signature_check"] = {"status": "pass", "algorithm": "ed25519"}

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
        report["checks"]["underlying_bundle_check"] = {"status": "fail"}
        _write_report(args.report, _fail(report, "underlying_bundle_verification_failed"))
        return 1

    bundle_stdout = result.stdout.strip()
    bundle_file_count = None
    m = re.search(r"all\s+(\d+)\s+bundle", bundle_stdout)
    if m:
        bundle_file_count = int(m.group(1))

    ub_check: dict[str, Any] = {"status": "pass"}
    if bundle_file_count is not None:
        ub_check["bundle_file_count"] = bundle_file_count
    report["checks"]["underlying_bundle_check"] = ub_check

    # --- All checks passed ---
    _pass(report)
    print("PASS: Silver signed bundle assertion verified")
    _write_report(args.report, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
