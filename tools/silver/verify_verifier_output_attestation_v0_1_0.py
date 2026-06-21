#!/usr/bin/env python3
"""Verify a ProofRail Silver Verifier Output Attestation v0.1.0.

Checks attestation structure, binding constraints, attestor trust, Ed25519
signature, subject file integrity, and metadata consistency.

Usage:
  python3 tools/silver/verify_verifier_output_attestation_v0_1_0.py \
    --attestation <attestation.json> \
    --trust-policy <attestation-trust-policy.yaml>
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
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


def _sha256_file(path: Path) -> str:
    """Compute sha256:<hex> of a file."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fail(reason: str, detail: str = "") -> int:
    """Print failure and return exit code 1."""
    msg = f"FAIL: {reason}"
    if detail:
        msg += f" ({detail})"
    print(msg)
    return 1


def _has_path_traversal(path_str: str) -> bool:
    """Check if a path string contains '..' components."""
    return ".." in Path(path_str).parts


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Verify a Silver Verifier Output Attestation v0.1.0"
    )
    parser.add_argument("--attestation", required=True, help="Path to attestation JSON")
    parser.add_argument("--trust-policy", required=True, help="Path to attestation trust policy YAML")
    args = parser.parse_args()

    attestation_path = Path(args.attestation)
    trust_policy_path = Path(args.trust_policy)

    if not attestation_path.exists():
        print(f"ERROR: attestation not found: {attestation_path}", file=sys.stderr)
        return 2
    if not trust_policy_path.exists():
        print(f"ERROR: trust policy not found: {trust_policy_path}", file=sys.stderr)
        return 2

    # --- 1. Parse attestation JSON ---
    try:
        attestation = json.loads(attestation_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in attestation: {e}", file=sys.stderr)
        return 2

    if not isinstance(attestation, dict):
        return _fail("invalid_attestation_structure", "root must be a JSON object")

    if attestation.get("attestation_version") != "v0.1.0":
        return _fail("invalid_attestation_structure", f"expected attestation_version 'v0.1.0', got '{attestation.get('attestation_version')}'")

    if attestation.get("attestation_type") != "proofrail.silver.verifier_output_attestation":
        return _fail("invalid_attestation_structure", f"expected attestation_type 'proofrail.silver.verifier_output_attestation'")

    signed_payload = attestation.get("signed_payload")
    if not isinstance(signed_payload, dict):
        return _fail("invalid_attestation_structure", "signed_payload must be an object")

    sig_block = attestation.get("signature")
    if not isinstance(sig_block, dict):
        return _fail("invalid_attestation_structure", "signature must be an object")

    # --- 2. Binding checks ---
    attestor_block = signed_payload.get("attestor", {})
    payload_key_id = attestor_block.get("key_id", "")
    payload_algorithm = attestor_block.get("signature_algorithm", "")

    if sig_block.get("key_id") != payload_key_id:
        return _fail("invalid_attestation_structure", f"signature.key_id '{sig_block.get('key_id')}' != signed_payload.attestor.key_id '{payload_key_id}'")

    if sig_block.get("algorithm") != payload_algorithm:
        return _fail("invalid_attestation_structure", f"signature.algorithm '{sig_block.get('algorithm')}' != signed_payload.attestor.signature_algorithm '{payload_algorithm}'")

    # --- 3. Parse trust policy ---
    try:
        policy = yaml.safe_load(trust_policy_path.read_text())
    except Exception as e:
        print(f"ERROR: cannot parse trust policy: {e}", file=sys.stderr)
        return 2

    if not isinstance(policy, dict):
        return _fail("invalid_trust_policy", "trust policy root must be a mapping")

    if policy.get("policy_type") != "proofrail.silver.verifier_attestation_trust_policy":
        return _fail("invalid_trust_policy", f"expected policy_type 'proofrail.silver.verifier_attestation_trust_policy'")

    if policy.get("policy_version") != "v0.1.0":
        return _fail("invalid_trust_policy", f"expected policy_version 'v0.1.0'")

    # Find matching attestor
    payload_attestor_id = attestor_block.get("attestor_id", "")
    trusted_attestors = policy.get("trusted_attestors", [])
    matched_attestor = None

    attestor_ids_in_policy = []
    for ta in trusted_attestors:
        aid = ta.get("attestor_id", "")
        attestor_ids_in_policy.append(aid)
        if aid == payload_attestor_id and ta.get("key_id") == payload_key_id:
            matched_attestor = ta
            break

    if matched_attestor is None:
        if payload_attestor_id not in attestor_ids_in_policy:
            return _fail("attestor_not_trusted", f"attestor_id='{payload_attestor_id}'")
        else:
            return _fail("key_id_not_trusted", f"key_id='{payload_key_id}' for attestor_id='{payload_attestor_id}'")

    # --- 4. Algorithm check ---
    if payload_algorithm != "ed25519":
        return _fail("unsupported_algorithm", f"algorithm='{payload_algorithm}'")

    # --- 5. Load public key ---
    public_key_path_str = matched_attestor.get("public_key_path", "")
    if not public_key_path_str:
        return _fail("invalid_trust_policy", "public_key_path missing in matched attestor entry")

    # Resolve relative to trust policy parent directory
    pk_path = Path(public_key_path_str)
    if not pk_path.is_absolute():
        pk_path = trust_policy_path.parent / pk_path

    pk_path = pk_path.resolve()
    if not pk_path.exists():
        return _fail("invalid_trust_policy", f"public key not found: {pk_path}")

    try:
        public_key = load_pem_public_key(pk_path.read_bytes())
    except Exception as e:
        return _fail("invalid_trust_policy", f"cannot load public key: {e}")

    # --- 6. Verify signature ---
    canonical_bytes = json.dumps(
        signed_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")

    signature_b64 = sig_block.get("signature", "")
    try:
        signature_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        return _fail("signature_verification_failed", f"cannot decode signature: {e}")

    try:
        public_key.verify(signature_bytes, canonical_bytes)
    except InvalidSignature:
        return _fail("signature_verification_failed", "Ed25519 signature invalid")
    except Exception as e:
        return _fail("signature_verification_failed", f"signature verification error: {e}")

    # --- 7. Check subject paths for traversal ---
    subjects = signed_payload.get("subjects", {})

    for subject_name in ["verification_report", "profile_conformance_report"]:
        subject = subjects.get(subject_name)
        if not isinstance(subject, dict):
            return _fail("invalid_attestation_structure", f"subjects.{subject_name} must be an object")
        subject_path_str = subject.get("path", "")
        if _has_path_traversal(subject_path_str):
            return _fail("subject_path_traversal", f"subjects.{subject_name}.path contains '..' component: {subject_path_str}")

    pm_subject = subjects.get("package_manifest")
    if pm_subject is not None:
        if not isinstance(pm_subject, dict):
            return _fail("invalid_attestation_structure", "subjects.package_manifest must be an object or null")
        pm_path_str = pm_subject.get("path", "")
        if _has_path_traversal(pm_path_str):
            return _fail("subject_path_traversal", f"subjects.package_manifest.path contains '..' component: {pm_path_str}")

    # --- 8. Verify subject file hashes ---
    for subject_name in ["verification_report", "profile_conformance_report"]:
        subject = subjects[subject_name]
        subject_path = Path(subject["path"])
        if not subject_path.exists():
            return _fail("subject_file_missing", f"{subject_name}: {subject['path']}")

        actual_sha = _sha256_file(subject_path)
        expected_sha = subject.get("sha256", "")
        if actual_sha != expected_sha:
            return _fail("subject_hash_mismatch", f"{subject_name}: expected={expected_sha} actual={actual_sha}")

    # --- 9. Cross-check verification report metadata ---
    vr_subject = subjects["verification_report"]
    vr_path = Path(vr_subject["path"])
    try:
        vr = json.loads(vr_path.read_text())
    except Exception:
        return _fail("subject_file_missing", "cannot parse verification report")

    # Check verifier identity matches attestor
    vr_verifier_id = vr.get("verifier", {}).get("verifier_id", "")
    if payload_attestor_id != vr_verifier_id:
        return _fail("attestor_verifier_identity_mismatch", f"attestor_id='{payload_attestor_id}' verifier_id='{vr_verifier_id}'")

    # Check report version/type
    if vr_subject.get("report_version") != vr.get("report_version", ""):
        return _fail("attested_metadata_mismatch", f"verification_report report_version: attested='{vr_subject.get('report_version')}' actual='{vr.get('report_version')}'")
    if vr_subject.get("report_type") != vr.get("report_type", ""):
        return _fail("attested_metadata_mismatch", f"verification_report report_type: attested='{vr_subject.get('report_type')}' actual='{vr.get('report_type')}'")

    # --- 10. Cross-check conformance report metadata ---
    cr_subject = subjects["profile_conformance_report"]
    cr_path = Path(cr_subject["path"])
    try:
        cr = json.loads(cr_path.read_text())
    except Exception:
        return _fail("subject_file_missing", "cannot parse conformance report")

    # Check conformance report version/type
    if cr_subject.get("conformance_report_version") != cr.get("conformance_report_version", ""):
        return _fail("attested_metadata_mismatch", f"conformance_report_version: attested='{cr_subject.get('conformance_report_version')}' actual='{cr.get('conformance_report_version')}'")
    if cr_subject.get("conformance_report_type") != cr.get("conformance_report_type", ""):
        return _fail("attested_metadata_mismatch", f"conformance_report_type: attested='{cr_subject.get('conformance_report_type')}' actual='{cr.get('conformance_report_type')}'")

    # Check profile and decision match signed payload
    cr_profile = cr.get("profile", {})
    payload_profile = signed_payload.get("profile", {})
    for key in ["profile_id", "profile_version", "profile_mode"]:
        if cr_profile.get(key) != payload_profile.get(key):
            return _fail("attested_metadata_mismatch", f"profile.{key}: signed='{payload_profile.get(key)}' report='{cr_profile.get(key)}'")

    cr_decision = cr.get("decision", {})
    payload_decision = signed_payload.get("decision", {})
    for key in ["status", "reason"]:
        if cr_decision.get(key) != payload_decision.get(key):
            return _fail("attested_metadata_mismatch", f"decision.{key}: signed='{payload_decision.get(key)}' report='{cr_decision.get(key)}'")

    # Soft cross-check: conformance report's input.verification_report path
    cr_input_vr = cr.get("input", {}).get("verification_report", "")
    attested_vr_path = vr_subject.get("path", "")
    if cr_input_vr and attested_vr_path and cr_input_vr != attested_vr_path:
        print(f"WARNING: conformance report input.verification_report path '{cr_input_vr}' differs from attested subject path '{attested_vr_path}' (may be equivalent)")

    # --- 11. Verify package manifest if present ---
    if pm_subject is not None:
        pm_path = Path(pm_subject["path"])
        if not pm_path.exists():
            return _fail("subject_file_missing", f"package_manifest: {pm_subject['path']}")

        actual_pm_sha = _sha256_file(pm_path)
        expected_pm_sha = pm_subject.get("sha256", "")
        if actual_pm_sha != expected_pm_sha:
            return _fail("subject_hash_mismatch", f"package_manifest: expected={expected_pm_sha} actual={actual_pm_sha}")

        # Check package manifest metadata
        try:
            pm_data = yaml.safe_load(pm_path.read_text())
        except Exception:
            return _fail("package_manifest_mismatch", "cannot parse package manifest YAML")

        if not isinstance(pm_data, dict):
            return _fail("package_manifest_mismatch", "package manifest root must be a mapping")

        if pm_subject.get("package_type") != pm_data.get("package_type", ""):
            return _fail("package_manifest_mismatch", f"package_type: attested='{pm_subject.get('package_type')}' actual='{pm_data.get('package_type')}'")

        if pm_subject.get("package_format_version") != pm_data.get("package_format_version", ""):
            return _fail("package_manifest_mismatch", f"package_format_version: attested='{pm_subject.get('package_format_version')}' actual='{pm_data.get('package_format_version')}'")

    # --- 12. Limitations check ---
    limitations = signed_payload.get("limitations", [])
    if not isinstance(limitations, list) or len(limitations) == 0:
        return _fail("limitations_missing")

    # --- All checks passed ---
    print("PASS: Silver verifier output attestation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
