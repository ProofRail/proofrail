#!/usr/bin/env python3
"""Independent Silver Verification — ProofRail Demo.

A standalone verifier that operates on a portable verification package
without importing the main ProofRail Silver verifier or Bronze bundle
verifier. Produces a Silver Verification Report v0.1.0-compatible JSON.

Usage:
  python3 independent_verify.py --package <package-dir> [--report <report.json>]
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
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


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Independent Silver verification from a portable package"
    )
    parser.add_argument("--package", required=True, help="Path to verification package directory")
    parser.add_argument("--report", default=None, help="Path to write JSON verification report")
    args = parser.parse_args()

    pkg = Path(args.package).resolve()

    # Load package manifest
    manifest_path = pkg / "package-manifest.yaml"
    if not manifest_path.exists():
        print(f"ERROR: package manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = yaml.safe_load(manifest_path.read_text())
    if not isinstance(manifest, dict):
        print("ERROR: package manifest root must be a mapping", file=sys.stderr)
        return 2

    paths = manifest.get("paths", {})

    # Resolve package-local paths
    assertion_path = pkg / paths.get("signed_assertion", "")
    trust_policy_path = pkg / paths.get("trust_policy", "")
    revocation_list_path_str = paths.get("revocation_list", "")
    revocation_list_path = pkg / revocation_list_path_str if revocation_list_path_str else None
    bundle_manifest_path = pkg / paths.get("bundle_manifest", "")
    bronze_root = pkg / paths.get("bronze_package_root", "")

    for label, p in [("assertion", assertion_path), ("trust_policy", trust_policy_path),
                      ("bundle_manifest", bundle_manifest_path)]:
        if not p.exists():
            print(f"ERROR: {label} not found: {p}", file=sys.stderr)
            return 2

    # Load assertion and trust policy
    assertion = yaml.safe_load(assertion_path.read_text())
    if not isinstance(assertion, dict):
        print("FAIL: independent assertion root must be a mapping")
        return 1

    policy = yaml.safe_load(trust_policy_path.read_text())
    if not isinstance(policy, dict):
        print("FAIL: independent trust policy root must be a mapping")
        return 1

    # Build report skeleton
    assertion_id = assertion.get("assertion_id", "")
    issuer_block = assertion.get("issuer", {})
    assertion_issuer_id = issuer_block.get("issuer_id", "")
    assertion_key_id = issuer_block.get("key_id", "")
    sig_meta = assertion.get("signature", {})
    subject_block = assertion.get("subject", {})

    report: dict[str, Any] = {
        "report_version": "v0.1.0",
        "report_type": "proofrail.silver.verification_report",
        "report_id": "proofrail-silver-demo-002-independent-verifier-report",
        "generated_at": "",
        "generated_by": "demos/silver-demo-002-independent-verifier/verifier/independent_verify.py",
        "verifier": {
            "verifier_id": "proofrail-demo-independent-verifier",
            "verifier_label": "ProofRail Demo Independent Verifier",
        },
        "inputs": {
            "assertion_path": str(paths.get("signed_assertion", "")),
            "trust_policy_path": str(paths.get("trust_policy", "")),
            "revocation_list_path": revocation_list_path_str or None,
            "silver_root": str(paths.get("signed_assertion", "")).rsplit("/runtime/", 1)[0] if "/runtime/" in str(paths.get("signed_assertion", "")) else "",
            "bronze_package_root": str(paths.get("bronze_package_root", "")),
        },
        "assertion": {
            "assertion_id": assertion_id,
            "assertion_version": assertion.get("assertion_version", ""),
            "assertion_type": assertion.get("assertion_type", ""),
        },
        "issuer": {
            "issuer_id": assertion_issuer_id,
            "key_id": assertion_key_id,
            "algorithm": sig_meta.get("algorithm", ""),
            "public_key_fingerprint_sha256": sig_meta.get("public_key_fingerprint_sha256", ""),
        },
        "subject": {
            "bundle_manifest": subject_block.get("bundle_manifest", ""),
            "bundle_manifest_type": subject_block.get("bundle_manifest_type", ""),
            "bundle_manifest_sha256": subject_block.get("bundle_manifest_sha256", ""),
        },
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
            "Independent verifier demo — not production.",
            "Not production PKI.",
            "Not third-party certification.",
            "Not Gold certification.",
        ],
    }

    def fail(reason: str) -> dict[str, Any]:
        report["decision"] = {"status": "fail", "reason": reason}
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        return report

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
            print(f"FAIL: independent issuer not trusted (issuer_id={assertion_issuer_id})")
            report["checks"]["trust_check"] = {"status": "fail"}
            _write_report(args.report, fail("issuer_not_trusted"))
            return 1
        else:
            print(f"FAIL: independent key_id not trusted (key_id={assertion_key_id})")
            report["checks"]["trust_check"] = {"status": "fail"}
            _write_report(args.report, fail("key_id_not_trusted"))
            return 1

    report["checks"]["trust_check"] = {"status": "pass"}

    # --- 2. Algorithm check ---
    if sig_meta.get("algorithm") != "ed25519":
        print(f"FAIL: independent unsupported algorithm: {sig_meta.get('algorithm')}")
        report["checks"]["algorithm_check"] = {"status": "fail"}
        _write_report(args.report, fail("unsupported_algorithm"))
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
        print(f"FAIL: independent invalid validity timestamps: {e}")
        report["checks"]["validity_check"] = {
            "status": "fail", "issued_at": issued_at_str, "expires_at": expires_at_str,
        }
        _write_report(args.report, fail("invalid_validity_timestamps"))
        return 1

    now = datetime.now(timezone.utc)
    if now < issued_at:
        print(f"FAIL: independent assertion not yet valid (issued_at={issued_at_str})")
        report["checks"]["validity_check"] = {
            "status": "fail", "issued_at": issued_at_str, "expires_at": expires_at_str,
        }
        _write_report(args.report, fail("assertion_not_yet_valid"))
        return 1
    if now > expires_at:
        print(f"FAIL: independent assertion expired (expires_at={expires_at_str})")
        report["checks"]["validity_check"] = {
            "status": "fail", "issued_at": issued_at_str, "expires_at": expires_at_str,
        }
        _write_report(args.report, fail("assertion_expired"))
        return 1
    report["checks"]["validity_check"] = {
        "status": "pass", "issued_at": issued_at_str, "expires_at": expires_at_str,
    }

    # --- 4. Bundle manifest checksum check ---
    raw_bytes = bundle_manifest_path.read_bytes()
    actual_sha = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    expected_sha = subject_block.get("bundle_manifest_sha256", "")

    if actual_sha != expected_sha:
        print(f"FAIL: independent bundle checksum mismatch (expected={expected_sha} actual={actual_sha})")
        report["checks"]["bundle_manifest_checksum_check"] = {
            "status": "fail", "expected_sha256": expected_sha, "actual_sha256": actual_sha,
        }
        _write_report(args.report, fail("bundle_manifest_checksum_mismatch"))
        return 1
    report["checks"]["bundle_manifest_checksum_check"] = {
        "status": "pass", "expected_sha256": expected_sha, "actual_sha256": actual_sha,
    }

    # --- 5. Revocation check ---
    if revocation_list_path and revocation_list_path.exists():
        rev_list = yaml.safe_load(revocation_list_path.read_text())
        if not isinstance(rev_list, dict):
            print("FAIL: independent revocation list root must be a mapping")
            report["checks"]["revocation_check"] = {
                "performed": True, "status": "fail",
                "revocation_list": revocation_list_path_str,
            }
            _write_report(args.report, fail("invalid_report_input"))
            return 1

        # Check revoked assertions
        for entry in rev_list.get("revoked_assertions", []):
            if entry.get("assertion_id") == assertion_id:
                print(f"FAIL: independent assertion revoked (assertion_id={assertion_id})")
                report["checks"]["revocation_check"] = {
                    "performed": True, "status": "fail",
                    "revocation_list": revocation_list_path_str,
                }
                _write_report(args.report, fail("assertion_revoked"))
                return 1

        # Check revoked issuer keys
        for entry in rev_list.get("revoked_issuer_keys", []):
            if (entry.get("issuer_id") == assertion_issuer_id
                    and entry.get("key_id") == assertion_key_id):
                print(f"FAIL: independent issuer key revoked (issuer_id={assertion_issuer_id} key_id={assertion_key_id})")
                report["checks"]["revocation_check"] = {
                    "performed": True, "status": "fail",
                    "revocation_list": revocation_list_path_str,
                }
                _write_report(args.report, fail("issuer_key_revoked"))
                return 1

        # Check revoked bundles
        for entry in rev_list.get("revoked_bundles", []):
            if entry.get("bundle_manifest_sha256") == actual_sha:
                print(f"FAIL: independent bundle revoked (bundle_manifest_sha256={actual_sha})")
                report["checks"]["revocation_check"] = {
                    "performed": True, "status": "fail",
                    "revocation_list": revocation_list_path_str,
                }
                _write_report(args.report, fail("bundle_revoked"))
                return 1

        report["checks"]["revocation_check"] = {
            "performed": True, "status": "pass",
            "revocation_list": revocation_list_path_str,
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
        print(f"FAIL: independent cannot load public key: {e}")
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, fail("signature_verification_failed"))
        return 1

    signature_b64 = sig_meta.get("signature_value", "")
    try:
        signature_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        print(f"FAIL: independent cannot decode signature: {e}")
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, fail("signature_verification_failed"))
        return 1

    try:
        public_key.verify(signature_bytes, raw_bytes)
    except InvalidSignature:
        print("FAIL: independent signature verification failed")
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, fail("signature_verification_failed"))
        return 1
    except Exception as e:
        print(f"FAIL: independent signature verification error: {e}")
        report["checks"]["signature_check"] = {"status": "fail", "algorithm": "ed25519"}
        _write_report(args.report, fail("signature_verification_failed"))
        return 1
    report["checks"]["signature_check"] = {"status": "pass", "algorithm": "ed25519"}

    # --- 7. Underlying bundle check (inline, no imports from main tree) ---
    bundle_manifest = yaml.safe_load(raw_bytes)
    if not isinstance(bundle_manifest, dict):
        print("FAIL: independent underlying bundle verification failed — manifest not a mapping")
        report["checks"]["underlying_bundle_check"] = {"status": "fail"}
        _write_report(args.report, fail("underlying_bundle_verification_failed"))
        return 1

    files_list = bundle_manifest.get("files")
    if not isinstance(files_list, list):
        print("FAIL: independent underlying bundle verification failed — files not a list")
        report["checks"]["underlying_bundle_check"] = {"status": "fail"}
        _write_report(args.report, fail("underlying_bundle_verification_failed"))
        return 1

    bronze_root_resolved = bronze_root.resolve()
    bundle_failures: list[str] = []
    verified_count = 0

    for entry in files_list:
        rel_path = entry.get("path", "")
        required = entry.get("required", False)
        exp_sha = entry.get("sha256")
        exp_size = entry.get("size_bytes")

        resolved = (bronze_root_resolved / rel_path).resolve()

        if not resolved.exists():
            if required:
                bundle_failures.append(f"MISSING: {rel_path}")
            continue

        file_bytes = resolved.read_bytes()
        file_sha = "sha256:" + hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)

        if exp_sha and file_sha != exp_sha:
            bundle_failures.append(f"MISMATCH: {rel_path} expected={exp_sha} actual={file_sha}")
            continue

        if exp_size is not None and file_size != exp_size:
            bundle_failures.append(f"SIZE_MISMATCH: {rel_path} expected={exp_size} actual={file_size}")
            continue

        verified_count += 1

    if bundle_failures:
        print("FAIL: independent underlying bundle verification failed")
        for bf in bundle_failures:
            print(f"  - {bf}")
        report["checks"]["underlying_bundle_check"] = {"status": "fail"}
        _write_report(args.report, fail("underlying_bundle_verification_failed"))
        return 1

    report["checks"]["underlying_bundle_check"] = {
        "status": "pass",
        "bundle_file_count": verified_count,
    }

    # --- All checks passed ---
    report["decision"] = {"status": "pass", "reason": "all_checks_passed"}
    report["generated_at"] = datetime.now(timezone.utc).isoformat()

    print("PASS: independent Silver verification succeeded")
    _write_report(args.report, report)
    return 0


def _write_report(report_path: str | None, report: dict[str, Any]) -> None:
    if report_path:
        p = Path(report_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2, default=str) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
