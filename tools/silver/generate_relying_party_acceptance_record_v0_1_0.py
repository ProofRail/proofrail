#!/usr/bin/env python3
"""Generate a ProofRail Silver v0.2.8 relying-party acceptance record package.

The generator:

  1. Refuses to overwrite --output-dir unless --force is provided.
  2. Parses and structurally validates the supplied acceptance policy.
  3. Verifies --decision is in policy.allowed_decisions.
  4. Verifies --purpose is in policy.allowed_purposes.
  5. Subprocess-invokes the v0.2.7 composed gateway evidence verifier on
     --evidence-manifest. Captures pass/fail and any failure detail.
  6. If --decision == "accepted" and the v0.2.7 verifier exited non-zero,
     refuses generation and prints:
         FAIL: evidence_verification_failed: <detail>
     with exit code 1. Otherwise proceeds.
  7. Copies acceptance-policy.json and the evidence manifest into the
     output directory (only the manifest is copied; not the full v0.2.7
     package).
  8. Derives revocation_review.outcome from the sibling composed gateway
     evidence report when available.
  9. Emits acceptance-record.json with deterministic field shape.
 10. Emits acceptance-package-manifest.json with three subjects in the
     deterministic order required by the v0.2.8 schema.
 11. Optionally self-validates the generated package when --self-validate
     is supplied.

No external services, no real logs, no network fetch, no vendor APIs.

Usage:
  python3 tools/silver/generate_relying_party_acceptance_record_v0_1_0.py \\
    --policy fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json \\
    --evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \\
    --decision accepted \\
    --purpose demo_trust_boundary_review \\
    --decision-maker demo.relying_party.local_reviewer \\
    --generated-at 2026-06-22T00:00:00Z \\
    --challenge-closes-at 2026-07-22T00:00:00Z \\
    --output-dir /tmp/proofrail-silver-relying-party-acceptance-v0.2.8 \\
    --force

Exit codes:
  0 - acceptance package generated
  1 - generation refused (evidence_verification_failed; or self-validation failed)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_VERIFIER = REPO_ROOT / "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"
ACCEPTANCE_VALIDATOR = REPO_ROOT / "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"

POLICY_DOCUMENT_TYPE = "proofrail.silver.relying_party_acceptance_policy"
RECORD_DOCUMENT_TYPE = "proofrail.silver.relying_party_acceptance_record"
PACKAGE_MANIFEST_DOCUMENT_TYPE = (
    "proofrail.silver.relying_party_acceptance_package_manifest"
)
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.8"

ALLOWED_DECISIONS = {"accepted", "rejected", "accepted_with_exceptions"}
DEFAULT_SCOPE_LIMITATIONS = [
    "Acceptance applies only to the deterministic v0.2.7 simulated gateway "
    "evidence demo.",
    "Acceptance does not apply to real gateway enforcement.",
]
DEFAULT_NON_CLAIMS = [
    "This record is not a certificate.",
    "This record is not Gold conformance.",
    "This record is not regulator approval.",
]
DEFAULT_MANIFEST_LIMITATIONS = [
    "This manifest hash-anchors a local, demo relying-party acceptance "
    "package; it is not signed.",
    "This manifest does not establish Gold conformance.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This manifest does not certify the underlying evidence.",
    "This manifest does not record an institutional or legal acceptance.",
]

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def parse_iso_8601_z(value: str) -> datetime | None:
    if not isinstance(value, str) or not ISO_8601_RE.match(value):
        return None
    try:
        return datetime.strptime(value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            return datetime.strptime(
                value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            return None


def load_policy(path: Path) -> tuple[dict | None, str]:
    if not path.exists():
        return None, f"policy not found: {path}"
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return None, f"policy not valid JSON: {e}"
    if not isinstance(data, dict):
        return None, "policy not a JSON object"
    return data, ""


def validate_policy_shape(p: dict) -> str:
    """Return empty string if shape is OK; otherwise return a detail."""
    required = [
        "document_type",
        "schema_version",
        "proofrail_release",
        "policy_id",
        "policy_version",
        "relying_party",
        "allowed_purposes",
        "allowed_evidence_types",
        "required_verification",
        "revocation_requirements",
        "challenge_window",
        "allowed_decisions",
        "non_claims",
    ]
    for k in required:
        if k not in p:
            return f"policy missing {k}"
    if p["document_type"] != POLICY_DOCUMENT_TYPE:
        return f"policy.document_type != {POLICY_DOCUMENT_TYPE}"
    if p["schema_version"] != SCHEMA_VERSION:
        return f"policy.schema_version != {SCHEMA_VERSION}"
    if p["proofrail_release"] != PROOFRAIL_RELEASE:
        return f"policy.proofrail_release != {PROOFRAIL_RELEASE}"
    if not isinstance(p["policy_id"], str) or not p["policy_id"].strip():
        return "policy.policy_id"
    if not isinstance(p["policy_version"], str) or not p["policy_version"].strip():
        return "policy.policy_version"
    rp = p["relying_party"]
    if not isinstance(rp, dict):
        return "policy.relying_party"
    for k in ("relying_party_id", "display_name"):
        if not isinstance(rp.get(k), str) or not rp[k].strip():
            return f"policy.relying_party.{k}"
    for k in ("allowed_purposes", "allowed_evidence_types", "non_claims"):
        v = p[k]
        if not isinstance(v, list) or not v:
            return f"policy.{k}"
        for entry in v:
            if not isinstance(entry, str) or not entry.strip():
                return f"policy.{k} entry"
    rv = p["required_verification"]
    if not isinstance(rv, dict):
        return "policy.required_verification"
    for k in ("verifier_tool", "required_result"):
        if not isinstance(rv.get(k), str) or not rv[k].strip():
            return f"policy.required_verification.{k}"
    rr = p["revocation_requirements"]
    if not isinstance(rr, dict):
        return "policy.revocation_requirements"
    if not isinstance(rr.get("revocation_review_required"), bool):
        return "policy.revocation_requirements.revocation_review_required"
    if rr["revocation_review_required"]:
        outs = rr.get("accepted_outcomes")
        if not isinstance(outs, list) or not outs:
            return "policy.revocation_requirements.accepted_outcomes"
        for o in outs:
            if not isinstance(o, str) or not o.strip():
                return "policy.revocation_requirements.accepted_outcomes entry"
    cw = p["challenge_window"]
    if not isinstance(cw, dict):
        return "policy.challenge_window"
    if not isinstance(cw.get("required"), bool):
        return "policy.challenge_window.required"
    if cw["required"]:
        for k in ("minimum_days", "maximum_days"):
            v = cw.get(k)
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                return f"policy.challenge_window.{k}"
        if cw["maximum_days"] < cw["minimum_days"]:
            return "policy.challenge_window.maximum_days < minimum_days"
    ad = p["allowed_decisions"]
    if not isinstance(ad, list) or set(ad) != ALLOWED_DECISIONS:
        return "policy.allowed_decisions"
    return ""


def derive_revocation_review(
    evidence_manifest_path: Path,
    reviewed_at: str,
    policy_accepted_outcomes: list[str],
) -> dict:
    """Derive revocation review from sibling composed report.

    For the demo happy path, the composed report contains the
    'revoked_authority_fails' claim with status 'pass', which corresponds
    to 'no_revoked_authority_accepted'.
    """
    sibling_report = evidence_manifest_path.parent / "composed-gateway-evidence-report.json"
    if not sibling_report.exists():
        return {
            "performed": False,
            "outcome": "report_unavailable",
            "reviewed_at": reviewed_at,
            "notes": (
                "Composed gateway evidence report was not available next to "
                "the supplied evidence manifest; revocation review could not "
                "be performed."
            ),
        }
    try:
        report = json.loads(sibling_report.read_text())
    except json.JSONDecodeError:
        return {
            "performed": False,
            "outcome": "report_unparseable",
            "reviewed_at": reviewed_at,
            "notes": (
                "Composed gateway evidence report was present but did not "
                "parse as JSON."
            ),
        }
    claims = report.get("claims", []) if isinstance(report, dict) else []
    by_id = {c.get("claim_id"): c for c in claims if isinstance(c, dict)}
    rev_claim = by_id.get("revoked_authority_fails")
    if rev_claim is not None and rev_claim.get("status") == "pass":
        outcome = "no_revoked_authority_accepted"
    else:
        outcome = "revoked_authority_rejected"
    # If the resolved outcome is not in the policy's accepted_outcomes, we
    # still record it honestly; the validator will reject if policy
    # mandates revocation review and the outcome is not accepted.
    return {
        "performed": True,
        "outcome": outcome,
        "reviewed_at": reviewed_at,
        "notes": (
            "Composed gateway evidence includes revocation marker and "
            "post-revocation denial."
        ),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a ProofRail Silver v0.2.8 relying-party acceptance "
            "record package over a verified v0.2.7 composed gateway "
            "evidence manifest."
        )
    )
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--evidence-manifest", required=True, type=Path)
    parser.add_argument(
        "--decision", required=True, choices=sorted(ALLOWED_DECISIONS)
    )
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--decision-maker", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--challenge-closes-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--challenge-opens-at",
        default=None,
        help="Defaults to --generated-at when omitted.",
    )
    parser.add_argument(
        "--challenge-contact",
        default="demo-relying-party@example.invalid",
    )
    parser.add_argument(
        "--rejection-reason",
        default=None,
        help="Required (non-empty) for --decision rejected if the underlying "
        "verifier did not produce a failure reason.",
    )
    parser.add_argument(
        "--exception",
        action="append",
        default=[],
        help="Format: <severity>:<description>:<effect_on_scope>. "
        "May be supplied multiple times. severity must be 'blocking' or "
        "'advisory'.",
    )
    parser.add_argument(
        "--scope-limitation",
        action="append",
        default=None,
        help="Non-empty scope limitation string. May be supplied multiple "
        "times. Defaults to a built-in demo list when omitted.",
    )
    parser.add_argument(
        "--non-claim",
        action="append",
        default=None,
        help="Non-empty non-claim string. May be supplied multiple times. "
        "Defaults to a built-in demo list when omitted.",
    )
    parser.add_argument(
        "--record-id",
        default="proofrail-acceptance-record-demo-001",
    )
    parser.add_argument(
        "--package-id",
        default="proofrail-acceptance-package-demo-001",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Run the v0.2.8 acceptance record validator on the generated "
        "package before exiting.",
    )
    args = parser.parse_args(argv)

    # --- ISO-8601 sanity ---
    for label, value in (
        ("--generated-at", args.generated_at),
        ("--challenge-closes-at", args.challenge_closes_at),
    ):
        if parse_iso_8601_z(value) is None:
            return usage_error(f"{label} must be ISO-8601 UTC Z-suffixed")
    opens_at = args.challenge_opens_at or args.generated_at
    if parse_iso_8601_z(opens_at) is None:
        return usage_error("--challenge-opens-at must be ISO-8601 UTC Z-suffixed")

    # --- Output dir ---
    out = args.output_dir.resolve()
    if out.exists():
        if not args.force:
            return usage_error(
                f"--output-dir already exists: {out} (use --force)"
            )
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "evidence").mkdir()

    # --- Policy parse + shape ---
    policy, perr = load_policy(args.policy)
    if policy is None:
        return usage_error(perr)
    shape_err = validate_policy_shape(policy)
    if shape_err:
        return usage_error(f"invalid policy: {shape_err}")

    if args.decision not in policy["allowed_decisions"]:
        return usage_error(
            f"--decision {args.decision} not in policy.allowed_decisions"
        )
    if args.purpose not in policy["allowed_purposes"]:
        return usage_error(
            f"--purpose {args.purpose} not in policy.allowed_purposes"
        )

    # --- Evidence manifest existence ---
    ev_manifest = args.evidence_manifest.resolve()
    if not ev_manifest.exists():
        return usage_error(f"--evidence-manifest not found: {ev_manifest}")

    # --- Subprocess-invoke v0.2.7 verifier ---
    proc = subprocess.run(
        [sys.executable, str(EVIDENCE_VERIFIER), "--manifest", str(ev_manifest)],
        capture_output=True,
        text=True,
    )
    verifier_passed = proc.returncode == 0
    verifier_detail = (proc.stdout + proc.stderr).strip()
    if verifier_passed:
        verification_result = "pass"
        failure_reason: str | None = None
    else:
        verification_result = "fail"
        # Try to extract a "FAIL: <reason>: ..." line.
        failure_reason = None
        for line in verifier_detail.splitlines():
            if line.startswith("FAIL:"):
                failure_reason = line[len("FAIL:") :].strip()
                break
        if not failure_reason:
            failure_reason = "v0.2.7 verifier exited non-zero"

    # --- Generator refusal: --decision accepted + verifier failed ---
    if args.decision == "accepted" and not verifier_passed:
        # Generator-side failure code per v0.2.8 design:
        return fail(
            "evidence_verification_failed",
            f"v0.2.7 verifier failed; refusing --decision accepted: "
            f"{failure_reason}",
        )

    # --- Copy policy and evidence manifest into output dir ---
    copied_policy = out / "acceptance-policy.json"
    copied_policy.write_text(dump_json(policy))
    copied_evidence = out / "evidence" / "composed-gateway-evidence-manifest.json"
    shutil.copyfile(ev_manifest, copied_evidence)

    # --- Compute SHA-256 of copied evidence manifest ---
    copied_evidence_sha = "sha256:" + sha256_hex(copied_evidence)

    # --- Exceptions ---
    exceptions: list[dict] = []
    for raw in args.exception:
        parts = raw.split(":", 2)
        if len(parts) != 3:
            return usage_error(
                f"--exception must be <severity>:<description>:<effect>; "
                f"got {raw!r}"
            )
        severity, description, effect = (s.strip() for s in parts)
        if severity not in ("blocking", "advisory"):
            return usage_error(
                f"--exception severity must be blocking or advisory; got "
                f"{severity!r}"
            )
        if not description or not effect:
            return usage_error("--exception description and effect must be non-empty")
        exceptions.append(
            {
                "severity": severity,
                "description": description,
                "effect_on_scope": effect,
            }
        )

    # --- Revocation review ---
    revocation_review = derive_revocation_review(
        ev_manifest,
        reviewed_at=args.generated_at,
        policy_accepted_outcomes=policy["revocation_requirements"].get(
            "accepted_outcomes", []
        ),
    )

    # --- Scope limitations / non_claims defaults ---
    scope_limitations = (
        args.scope_limitation if args.scope_limitation else list(DEFAULT_SCOPE_LIMITATIONS)
    )
    non_claims = args.non_claim if args.non_claim else list(DEFAULT_NON_CLAIMS)

    # --- Acceptance record ---
    record = {
        "document_type": RECORD_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "record_id": args.record_id,
        "generated_at": args.generated_at,
        "relying_party": {
            "relying_party_id": policy["relying_party"]["relying_party_id"],
            "policy_id": policy["policy_id"],
            "policy_version": policy["policy_version"],
        },
        "decision": {
            "status": args.decision,
            "purpose_id": args.purpose,
            "decision_basis": "verified_silver_evidence_package",
            "decision_maker": args.decision_maker,
            "decision_time": args.generated_at,
            "rejection_reason": (
                args.rejection_reason
                if args.rejection_reason is not None
                else ""
            ),
        },
        "evidence_package": {
            "evidence_type": "proofrail.silver.composed_gateway_evidence_manifest",
            "manifest_path": "evidence/composed-gateway-evidence-manifest.json",
            "manifest_sha256": copied_evidence_sha,
            "source_release": "v0.2.7",
        },
        "verification": {
            "verifier_tool": policy["required_verification"]["verifier_tool"],
            "verification_result": verification_result,
            "verified_at": args.generated_at,
            "failure_reason": failure_reason,
        },
        "revocation_review": revocation_review,
        "exceptions": exceptions,
        "scope_limitations": scope_limitations,
        "challenge_window": {
            "opens_at": opens_at,
            "closes_at": args.challenge_closes_at,
            "challenge_contact": args.challenge_contact,
        },
        "non_claims": non_claims,
    }
    record_path = out / "acceptance-record.json"
    record_path.write_text(dump_json(record))

    # --- Package manifest ---
    subjects_order = [
        ("acceptance-policy.json", "acceptance_policy"),
        (
            "evidence/composed-gateway-evidence-manifest.json",
            "verified_evidence_manifest",
        ),
        ("acceptance-record.json", "acceptance_record"),
    ]
    subjects: list[dict] = []
    for rel, role in subjects_order:
        full = out / rel
        subjects.append(
            {
                "path": rel,
                "role": role,
                "sha256": "sha256:" + sha256_hex(full),
                "size_bytes": full.stat().st_size,
            }
        )
    pkg_manifest = {
        "document_type": PACKAGE_MANIFEST_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "package_id": args.package_id,
        "generated_at": args.generated_at,
        "hash_algorithm": "sha256",
        "package_root": ".",
        "subjects": subjects,
        "limitations": list(DEFAULT_MANIFEST_LIMITATIONS),
        "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
    }
    pkg_manifest_path = out / "acceptance-package-manifest.json"
    pkg_manifest_path.write_text(dump_json(pkg_manifest))

    print(f"PASS: acceptance package generated at {out}")
    print(f"  policy: {copied_policy.relative_to(out)}")
    print(f"  evidence: {copied_evidence.relative_to(out)}")
    print(f"  record: {record_path.relative_to(out)}")
    print(f"  package manifest: {pkg_manifest_path.relative_to(out)}")
    print(f"  verification: {verification_result}")

    if args.self_validate:
        sv = subprocess.run(
            [
                sys.executable,
                str(ACCEPTANCE_VALIDATOR),
                "--manifest",
                str(pkg_manifest_path),
            ],
        )
        if sv.returncode != 0:
            return fail(
                "self_validate_failed",
                f"acceptance validator exited {sv.returncode}",
            )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
