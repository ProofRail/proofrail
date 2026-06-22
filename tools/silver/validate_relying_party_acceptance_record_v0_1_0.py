#!/usr/bin/env python3
"""Validate a ProofRail Silver v0.2.8 relying-party acceptance record package.

Hash-first, fail-fast. The validator:

  1.  Parses the acceptance package manifest.
  2.  Validates package manifest shape: document_type, schema_version,
      proofrail_release, hash_algorithm, package_root, subject count,
      subject order, role set, limitations and non_claims presence.
  3.  Rejects any subject path containing '..' or that is absolute.
  4.  Checks each subject file exists.
  5.  Recomputes SHA-256 for each subject and compares to the recorded
      sha256.
  6.  Parses and structurally validates the acceptance policy.
  7.  Parses and structurally validates the acceptance record.
  8.  Cross-checks record.relying_party.policy_id / policy_version against
      policy.policy_id / policy_version.
  9.  Cross-checks record.relying_party.relying_party_id against
      policy.relying_party.relying_party_id.
  10. Cross-checks record.decision.purpose_id against
      policy.allowed_purposes.
  11. Cross-checks record.evidence_package.evidence_type against
      policy.allowed_evidence_types.
  12. Recomputes SHA-256 of the copied evidence manifest and compares to
      record.evidence_package.manifest_sha256.
  13. Cross-checks record.verification.verifier_tool and shape against
      policy.required_verification.
  14. For decision.status == "accepted", requires verification_result ==
      "pass".
  15. For decision.status == "accepted", requires no exception with
      severity == "blocking".
  16. For decision.status == "accepted_with_exceptions", requires >= 1
      exception with all three fields.
  17. For decision.status == "rejected", requires non-empty rejection
      reason or non-empty verification.failure_reason.
  18. When policy mandates revocation review, requires record.revocation
      _review.performed == true and outcome in policy.accepted_outcomes.
  19. When policy mandates a challenge window, requires opens_at <
      closes_at and span_days in [minimum_days, maximum_days].
  20. Requires non-empty scope_limitations.
  21. Requires non-empty non_claims.
  22. With --evidence-package-root, subprocess-invokes the v0.2.7
      composed gateway evidence verifier against the original package's
      manifest and rejects on non-zero exit or if the original package's
      manifest sha256 differs from the copied evidence manifest sha256.

Stable failure reasons:

  invalid_acceptance_package_manifest
  acceptance_subject_file_missing
  acceptance_subject_path_traversal
  acceptance_subject_hash_mismatch
  invalid_acceptance_policy
  invalid_acceptance_record
  policy_mismatch
  relying_party_mismatch
  purpose_not_allowed
  evidence_type_not_allowed
  evidence_manifest_hash_mismatch
  evidence_verification_required
  accepted_record_verification_failed
  accepted_record_has_blocking_exception
  accepted_with_exceptions_missing_exception
  rejected_record_missing_reason
  revocation_review_missing
  challenge_window_invalid
  scope_limitations_missing
  acceptance_non_claims_missing
  external_evidence_verification_failed

Note: 'evidence_verification_failed' is a generator-only code (used by
generate_relying_party_acceptance_record_v0_1_0.py) and is never emitted
by this validator.

Usage:
  python3 tools/silver/validate_relying_party_acceptance_record_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \\
    [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]

Exit codes:
  0 - acceptance package valid
  1 - validation failure (any stable failure reason above)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_VERIFIER = REPO_ROOT / "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"

POLICY_DOCUMENT_TYPE = "proofrail.silver.relying_party_acceptance_policy"
RECORD_DOCUMENT_TYPE = "proofrail.silver.relying_party_acceptance_record"
PACKAGE_MANIFEST_DOCUMENT_TYPE = (
    "proofrail.silver.relying_party_acceptance_package_manifest"
)
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.8"

ALLOWED_DECISIONS = {"accepted", "rejected", "accepted_with_exceptions"}

SUBJECT_ORDER = [
    ("acceptance-policy.json", "acceptance_policy"),
    (
        "evidence/composed-gateway-evidence-manifest.json",
        "verified_evidence_manifest",
    ),
    ("acceptance-record.json", "acceptance_record"),
]

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}")
    return 1


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def has_traversal(p: str) -> bool:
    if not isinstance(p, str) or not p:
        return True
    if p.startswith("/"):
        return True
    parts = p.replace("\\", "/").split("/")
    return ".." in parts


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


def load_json_or_fail(path: Path, reason: str) -> tuple[Any, int]:
    try:
        return json.loads(path.read_text()), 0
    except FileNotFoundError:
        return None, fail(reason, f"{path}: not found")
    except json.JSONDecodeError as e:
        return None, fail(reason, f"{path}: {e}")
    except OSError as e:
        return None, fail(reason, f"{path}: {e}")


def validate_manifest_shape(m: Any, package_root: Path) -> str:
    if not isinstance(m, dict):
        return "manifest not object"
    for k, expected in [
        ("document_type", PACKAGE_MANIFEST_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
        ("hash_algorithm", "sha256"),
        ("package_root", "."),
    ]:
        if m.get(k) != expected:
            return f"{k} != {expected}"
    if not isinstance(m.get("package_id"), str) or not m["package_id"].strip():
        return "package_id"
    if not isinstance(m.get("generated_at"), str) or parse_iso_8601_z(m["generated_at"]) is None:
        return "generated_at"
    for k in ("limitations", "non_claims"):
        v = m.get(k)
        if not isinstance(v, list) or not v:
            return k
        for entry in v:
            if not isinstance(entry, str) or not entry.strip():
                return f"{k} entry"
    subjects = m.get("subjects")
    if not isinstance(subjects, list) or len(subjects) != 3:
        return "subjects count"
    for i, (expected_path, expected_role) in enumerate(SUBJECT_ORDER):
        s = subjects[i]
        if not isinstance(s, dict):
            return f"subject {i} not object"
        for k in ("path", "role", "sha256", "size_bytes"):
            if k not in s:
                return f"subject {i} missing {k}"
        if s["role"] != expected_role:
            return f"subject {i} role {s['role']} != {expected_role}"
        # Path traversal is checked outside this function (different reason).
        if not isinstance(s["path"], str):
            return f"subject {i} path not string"
    return ""


def validate_policy_shape(p: Any) -> str:
    if not isinstance(p, dict):
        return "policy not object"
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
            return f"missing {k}"
    if p["document_type"] != POLICY_DOCUMENT_TYPE:
        return "document_type"
    if p["schema_version"] != SCHEMA_VERSION:
        return "schema_version"
    if p["proofrail_release"] != PROOFRAIL_RELEASE:
        return "proofrail_release"
    if not isinstance(p["policy_id"], str) or not p["policy_id"].strip():
        return "policy_id"
    if not isinstance(p["policy_version"], str) or not p["policy_version"].strip():
        return "policy_version"
    rp = p["relying_party"]
    if not isinstance(rp, dict):
        return "relying_party"
    for k in ("relying_party_id", "display_name"):
        if not isinstance(rp.get(k), str) or not rp[k].strip():
            return f"relying_party.{k}"
    for k in ("allowed_purposes", "allowed_evidence_types", "non_claims"):
        v = p[k]
        if not isinstance(v, list) or not v:
            return k
        for entry in v:
            if not isinstance(entry, str) or not entry.strip():
                return f"{k} entry"
    rv = p["required_verification"]
    if not isinstance(rv, dict):
        return "required_verification"
    for k in ("verifier_tool", "required_result"):
        if not isinstance(rv.get(k), str) or not rv[k].strip():
            return f"required_verification.{k}"
    rr = p["revocation_requirements"]
    if not isinstance(rr, dict):
        return "revocation_requirements"
    if not isinstance(rr.get("revocation_review_required"), bool):
        return "revocation_requirements.revocation_review_required"
    if rr["revocation_review_required"]:
        outs = rr.get("accepted_outcomes")
        if not isinstance(outs, list) or not outs:
            return "revocation_requirements.accepted_outcomes"
        for o in outs:
            if not isinstance(o, str) or not o.strip():
                return "revocation_requirements.accepted_outcomes entry"
    cw = p["challenge_window"]
    if not isinstance(cw, dict):
        return "challenge_window"
    if not isinstance(cw.get("required"), bool):
        return "challenge_window.required"
    if cw["required"]:
        for k in ("minimum_days", "maximum_days"):
            v = cw.get(k)
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                return f"challenge_window.{k}"
        if cw["maximum_days"] < cw["minimum_days"]:
            return "challenge_window: maximum_days < minimum_days"
    ad = p["allowed_decisions"]
    if not isinstance(ad, list) or set(ad) != ALLOWED_DECISIONS:
        return "allowed_decisions"
    return ""


def validate_record_shape(r: Any) -> str:
    if not isinstance(r, dict):
        return "record not object"
    required = [
        "document_type",
        "schema_version",
        "proofrail_release",
        "record_id",
        "generated_at",
        "relying_party",
        "decision",
        "evidence_package",
        "verification",
        "revocation_review",
        "exceptions",
        "scope_limitations",
        "challenge_window",
        "non_claims",
    ]
    for k in required:
        if k not in r:
            return f"missing {k}"
    if r["document_type"] != RECORD_DOCUMENT_TYPE:
        return "document_type"
    if r["schema_version"] != SCHEMA_VERSION:
        return "schema_version"
    if r["proofrail_release"] != PROOFRAIL_RELEASE:
        return "proofrail_release"
    if not isinstance(r["record_id"], str) or not r["record_id"].strip():
        return "record_id"
    if parse_iso_8601_z(r.get("generated_at", "")) is None:
        return "generated_at"
    rp = r["relying_party"]
    if not isinstance(rp, dict):
        return "relying_party"
    for k in ("relying_party_id", "policy_id", "policy_version"):
        if not isinstance(rp.get(k), str) or not rp[k].strip():
            return f"relying_party.{k}"
    d = r["decision"]
    if not isinstance(d, dict):
        return "decision"
    if d.get("status") not in ALLOWED_DECISIONS:
        return "decision.status"
    for k in ("purpose_id", "decision_basis", "decision_maker"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            return f"decision.{k}"
    if parse_iso_8601_z(d.get("decision_time", "")) is None:
        return "decision.decision_time"
    if "rejection_reason" in d and not isinstance(d["rejection_reason"], str):
        return "decision.rejection_reason"
    ep = r["evidence_package"]
    if not isinstance(ep, dict):
        return "evidence_package"
    for k in ("evidence_type", "manifest_path", "manifest_sha256", "source_release"):
        if not isinstance(ep.get(k), str) or not ep[k].strip():
            return f"evidence_package.{k}"
    if ep["manifest_path"] != "evidence/composed-gateway-evidence-manifest.json":
        return "evidence_package.manifest_path"
    if not ep["manifest_sha256"].startswith("sha256:"):
        return "evidence_package.manifest_sha256 format"
    # verification: shape-only here; cross-checks happen separately.
    v = r["verification"]
    if not isinstance(v, dict):
        return "verification"
    if "verifier_tool" not in v:
        return "verification.verifier_tool"
    if "verification_result" not in v:
        return "verification.verification_result"
    if "verified_at" not in v:
        return "verification.verified_at"
    if "failure_reason" not in v:
        return "verification.failure_reason"
    # revocation_review: shape-only.
    rr = r["revocation_review"]
    if not isinstance(rr, dict):
        return "revocation_review"
    if not isinstance(rr.get("performed"), bool):
        return "revocation_review.performed"
    excs = r["exceptions"]
    if not isinstance(excs, list):
        return "exceptions"
    for i, e in enumerate(excs):
        if not isinstance(e, dict):
            return f"exceptions[{i}] not object"
        if e.get("severity") not in ("blocking", "advisory"):
            return f"exceptions[{i}].severity"
        for k in ("description", "effect_on_scope"):
            if not isinstance(e.get(k), str) or not e[k].strip():
                return f"exceptions[{i}].{k}"
    cw = r["challenge_window"]
    if not isinstance(cw, dict):
        return "challenge_window"
    for k in ("opens_at", "closes_at"):
        if parse_iso_8601_z(cw.get(k, "")) is None:
            return f"challenge_window.{k}"
    if not isinstance(cw.get("challenge_contact"), str) or not cw["challenge_contact"].strip():
        return "challenge_window.challenge_contact"
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a ProofRail Silver v0.2.8 relying-party acceptance "
            "record package."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--evidence-package-root",
        default=None,
        type=Path,
        help="Path to the original v0.2.7 composed gateway evidence package "
        "root. When supplied, the validator re-invokes the v0.2.7 verifier "
        "and rejects on failure or hash mismatch.",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        return usage_error(f"--manifest not found: {manifest_path}")
    package_root = manifest_path.parent

    # Step 1-2: load and validate manifest shape.
    manifest, rc = load_json_or_fail(manifest_path, "invalid_acceptance_package_manifest")
    if rc != 0:
        return rc
    shape_err = validate_manifest_shape(manifest, package_root)
    if shape_err:
        return fail("invalid_acceptance_package_manifest", shape_err)

    subjects = manifest["subjects"]

    # Step 3: path traversal.
    for s in subjects:
        if has_traversal(s["path"]):
            return fail("acceptance_subject_path_traversal", s["path"])

    # Step 4: subject path equals expected.
    for i, (expected_path, _expected_role) in enumerate(SUBJECT_ORDER):
        if subjects[i]["path"] != expected_path:
            return fail(
                "invalid_acceptance_package_manifest",
                f"subject {i} path {subjects[i]['path']} != {expected_path}",
            )

    # Step 5: existence.
    for s in subjects:
        full = package_root / s["path"]
        if not full.exists():
            return fail("acceptance_subject_file_missing", s["path"])

    # Step 6: hash recompute.
    for s in subjects:
        full = package_root / s["path"]
        recorded = s["sha256"]
        if not isinstance(recorded, str) or not recorded.startswith("sha256:"):
            return fail(
                "invalid_acceptance_package_manifest",
                f"subject {s['path']} sha256 format",
            )
        recomputed = sha256_hex(full)
        if recorded.split(":", 1)[1] != recomputed:
            return fail("acceptance_subject_hash_mismatch", s["path"])

    print("PASS: package manifest shape + subject paths + hashes verified")

    # Step 7: parse + validate policy.
    policy_path = package_root / "acceptance-policy.json"
    policy, rc = load_json_or_fail(policy_path, "invalid_acceptance_policy")
    if rc != 0:
        return rc
    pol_err = validate_policy_shape(policy)
    if pol_err:
        return fail("invalid_acceptance_policy", pol_err)

    # Step 8: parse + validate record.
    record_path = package_root / "acceptance-record.json"
    record, rc = load_json_or_fail(record_path, "invalid_acceptance_record")
    if rc != 0:
        return rc
    rec_err = validate_record_shape(record)
    if rec_err:
        return fail("invalid_acceptance_record", rec_err)

    # Step 9: policy_id / policy_version cross-check.
    if (
        record["relying_party"]["policy_id"] != policy["policy_id"]
        or record["relying_party"]["policy_version"] != policy["policy_version"]
    ):
        return fail(
            "policy_mismatch",
            f"record policy_id/version "
            f"{record['relying_party']['policy_id']}/{record['relying_party']['policy_version']} "
            f"!= policy "
            f"{policy['policy_id']}/{policy['policy_version']}",
        )

    # Step 10: relying_party_id cross-check.
    if (
        record["relying_party"]["relying_party_id"]
        != policy["relying_party"]["relying_party_id"]
    ):
        return fail(
            "relying_party_mismatch",
            f"record {record['relying_party']['relying_party_id']} "
            f"!= policy {policy['relying_party']['relying_party_id']}",
        )

    # Step 11: purpose.
    if record["decision"]["purpose_id"] not in policy["allowed_purposes"]:
        return fail(
            "purpose_not_allowed",
            f"{record['decision']['purpose_id']} not in "
            f"{policy['allowed_purposes']}",
        )

    # Step 12: evidence_type.
    if (
        record["evidence_package"]["evidence_type"]
        not in policy["allowed_evidence_types"]
    ):
        return fail(
            "evidence_type_not_allowed",
            record["evidence_package"]["evidence_type"],
        )

    # Step 13: evidence manifest hash mismatch.
    evidence_manifest_path = (
        package_root / "evidence" / "composed-gateway-evidence-manifest.json"
    )
    copied_sha = "sha256:" + sha256_hex(evidence_manifest_path)
    if copied_sha != record["evidence_package"]["manifest_sha256"]:
        return fail(
            "evidence_manifest_hash_mismatch",
            f"recomputed {copied_sha} != record "
            f"{record['evidence_package']['manifest_sha256']}",
        )

    # Step 14: evidence_verification_required (verifier metadata).
    rv_policy = policy["required_verification"]
    rv_record = record["verification"]
    if (
        not isinstance(rv_record.get("verifier_tool"), str)
        or not rv_record["verifier_tool"].strip()
        or rv_record["verifier_tool"] != rv_policy["verifier_tool"]
    ):
        return fail(
            "evidence_verification_required",
            f"record.verification.verifier_tool "
            f"{rv_record.get('verifier_tool')!r} != policy "
            f"{rv_policy['verifier_tool']!r}",
        )
    if (
        not isinstance(rv_record.get("verification_result"), str)
        or not rv_record["verification_result"].strip()
    ):
        return fail(
            "evidence_verification_required",
            "record.verification.verification_result missing",
        )
    if parse_iso_8601_z(rv_record.get("verified_at", "")) is None:
        return fail(
            "evidence_verification_required",
            "record.verification.verified_at missing or malformed",
        )

    decision_status = record["decision"]["status"]

    # Step 15: accepted requires verification_result == pass.
    if (
        decision_status == "accepted"
        and rv_record["verification_result"] != "pass"
    ):
        return fail(
            "accepted_record_verification_failed",
            f"record.decision.status == accepted but verification_result == "
            f"{rv_record['verification_result']}",
        )

    # Step 16: accepted requires no blocking exception.
    if decision_status == "accepted":
        for i, e in enumerate(record["exceptions"]):
            if e.get("severity") == "blocking":
                return fail(
                    "accepted_record_has_blocking_exception",
                    f"exceptions[{i}] severity=blocking",
                )

    # Step 17: accepted_with_exceptions requires >=1 conforming exception.
    if decision_status == "accepted_with_exceptions":
        if len(record["exceptions"]) < 1:
            return fail(
                "accepted_with_exceptions_missing_exception",
                "no exceptions provided",
            )

    # Step 18: rejected requires rejection_reason or failure_reason.
    if decision_status == "rejected":
        rr = record["decision"].get("rejection_reason", "")
        fr = rv_record.get("failure_reason")
        if (not isinstance(rr, str) or not rr.strip()) and (
            not isinstance(fr, str) or not fr.strip()
        ):
            return fail(
                "rejected_record_missing_reason",
                "neither decision.rejection_reason nor verification.failure_reason "
                "is non-empty",
            )

    # Step 19: revocation review.
    rr_policy = policy["revocation_requirements"]
    rr_record = record["revocation_review"]
    if rr_policy["revocation_review_required"]:
        if rr_record.get("performed") is not True:
            return fail(
                "revocation_review_missing",
                "policy requires revocation review but record.performed != true",
            )
        if rr_record.get("outcome") not in rr_policy["accepted_outcomes"]:
            return fail(
                "revocation_review_missing",
                f"outcome {rr_record.get('outcome')!r} not in "
                f"{rr_policy['accepted_outcomes']}",
            )

    # Step 20: challenge window.
    cw_policy = policy["challenge_window"]
    cw_record = record["challenge_window"]
    if cw_policy["required"]:
        opens = parse_iso_8601_z(cw_record["opens_at"])
        closes = parse_iso_8601_z(cw_record["closes_at"])
        if opens is None or closes is None or closes <= opens:
            return fail(
                "challenge_window_invalid",
                "opens_at/closes_at malformed or closes_at <= opens_at",
            )
        span_days = (closes - opens).total_seconds() / 86400.0
        if not (
            cw_policy["minimum_days"] <= span_days <= cw_policy["maximum_days"]
        ):
            return fail(
                "challenge_window_invalid",
                f"span_days {span_days} not in "
                f"[{cw_policy['minimum_days']}, {cw_policy['maximum_days']}]",
            )

    # Step 21: scope_limitations.
    sl = record["scope_limitations"]
    if not isinstance(sl, list) or not sl:
        return fail("scope_limitations_missing", "scope_limitations empty")
    for i, e in enumerate(sl):
        if not isinstance(e, str) or not e.strip():
            return fail("scope_limitations_missing", f"scope_limitations[{i}]")

    # Step 22: non_claims.
    nc = record["non_claims"]
    if not isinstance(nc, list) or not nc:
        return fail("acceptance_non_claims_missing", "non_claims empty")
    for i, e in enumerate(nc):
        if not isinstance(e, str) or not e.strip():
            return fail("acceptance_non_claims_missing", f"non_claims[{i}]")

    # Step 23 (optional): re-run v0.2.7 verifier on the original package.
    if args.evidence_package_root is not None:
        root = args.evidence_package_root.resolve()
        original_manifest = root / "composed-gateway-evidence-manifest.json"
        if not original_manifest.exists():
            return fail(
                "external_evidence_verification_failed",
                f"original manifest not found: {original_manifest}",
            )
        proc = subprocess.run(
            [
                sys.executable,
                str(EVIDENCE_VERIFIER),
                "--manifest",
                str(original_manifest),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            detail = (proc.stdout + proc.stderr).strip().splitlines()
            first = detail[0] if detail else "v0.2.7 verifier exited non-zero"
            return fail("external_evidence_verification_failed", first)
        original_sha = "sha256:" + sha256_hex(original_manifest)
        if original_sha != record["evidence_package"]["manifest_sha256"]:
            return fail(
                "external_evidence_verification_failed",
                f"original manifest sha256 {original_sha} != record "
                f"{record['evidence_package']['manifest_sha256']}",
            )
        print(
            "PASS: external v0.2.7 evidence package re-verified and hash-matched"
        )

    print(
        f"PASS: relying-party acceptance record valid ({record['record_id']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
