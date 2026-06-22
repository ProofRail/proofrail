#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.0 acceptance handoff package.

Hash-first, fail-fast. The verifier:

  1.  Parses the handoff package manifest.
  2.  Validates manifest shape: document_type, schema_version,
      proofrail_release, hash_algorithm, package_root, handoff_id,
      generated_at, subject count (exactly four), subject ordering,
      role set, scope_limitations presence, non_claims presence.
  3.  Rejects any subject path containing '..' or that is absolute.
  4.  Checks subject path equality against the deterministic
      SUBJECT_ORDER.
  5.  Checks each subject file exists.
  6.  Recomputes SHA-256 for each subject and compares to the
      recorded sha256.
  7.  Subprocess-invokes the v0.2.7 composed gateway evidence
      verifier on the nested composed-gateway-evidence manifest.
  8.  Subprocess-invokes the v0.2.8 acceptance record validator on
      the nested acceptance-package manifest (WITHOUT
      --evidence-package-root, so v0.3.0 owns the chain binding).
  9.  Subprocess-invokes the v0.2.9 drill verifier on the nested
      revocation-challenge-drill manifest (WITHOUT
      --evidence-package-root, so v0.3.0 owns the chain binding).
  10. Parses and structurally validates the handoff summary JSON.
  11. Cross-checks summary included_chain.*.manifest_sha256 against
      the recomputed sha256 of the corresponding manifest at the
      package-relative manifest_path.
  12. Performs the v0.3.0-owned four-check chain binding between
      the three subject sha256 values and the values recorded inside
      the nested v0.2.8 record (evidence_package.manifest_sha256) and
      v0.2.9 drill report
      (base_acceptance.acceptance_package_manifest_sha256), plus the
      two inner-copy cross-hashes.
  13. Cross-checks summary
      included_chain.relying_party_acceptance.acceptance_record_id
      and decision_status against the nested v0.2.8 record.
  14. Cross-checks summary
      included_chain.relying_party_acceptance.purpose_id against the
      nested v0.2.8 record's decision.purpose_id.
  15. Validates summary
      included_chain.revocation_challenge_drill.recommended_local_posture
      against the known v0.2.9 closed set, and
      handoff_result.recommended_handoff_posture against the v0.3.0
      closed set; rejects a downgrade (handoff posture rank lower than
      the rank required by the drill posture) as
      handoff_posture_downgrade.
  16. Scans every string in the summary (recursively) OUTSIDE the
      scope_limitations and non_claims arrays for positive overclaim
      tokens.
  17. Requires non-empty scope_limitations and non_claims in both the
      manifest and the summary.

Stable failure reasons:

  invalid_handoff_manifest
  handoff_subject_file_missing
  handoff_subject_path_traversal
  handoff_subject_hash_mismatch
  nested_composed_evidence_invalid
  nested_acceptance_package_invalid
  nested_revocation_challenge_drill_invalid
  handoff_summary_invalid
  handoff_summary_binding_mismatch
  handoff_chain_binding_mismatch
  handoff_record_mismatch
  handoff_purpose_mismatch
  handoff_posture_invalid
  handoff_posture_downgrade
  handoff_overclaim
  handoff_limitations_missing
  handoff_non_claims_missing

Note: composed_evidence_validation_failed,
acceptance_package_validation_failed, drill_package_validation_failed,
and handoff_chain_binding_failed are runner-only codes (used by
build_silver_acceptance_handoff_v0_1_0.py) and are never emitted by
this verifier.

Usage:
  python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json

Exit codes:
  0 - handoff package valid
  1 - verification failure (any stable failure reason above)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSED_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"
)
ACCEPTANCE_VALIDATOR = (
    REPO_ROOT / "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
)
DRILL_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_revocation_challenge_drill_v0_1_0.py"
)

SUMMARY_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_summary"
MANIFEST_DOCUMENT_TYPE = "proofrail.silver.acceptance_handoff_manifest"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.0"

SUBJECT_ORDER = [
    (
        "composed-gateway-evidence/composed-gateway-evidence-manifest.json",
        "composed_gateway_evidence_manifest",
    ),
    (
        "acceptance-package/acceptance-package-manifest.json",
        "relying_party_acceptance_package_manifest",
    ),
    (
        "revocation-challenge-drill/revocation-challenge-drill-manifest.json",
        "revocation_challenge_drill_manifest",
    ),
    (
        "silver-acceptance-handoff-summary.json",
        "silver_acceptance_handoff_summary",
    ),
]

HANDOFF_POSTURES = (
    "silver_handoff_complete_for_demo_scope",
    "silver_handoff_complete_review_required_before_reuse",
    "silver_handoff_not_reusable_without_governed_review",
)
HANDOFF_POSTURE_RANK = {p: i for i, p in enumerate(HANDOFF_POSTURES)}

DRILL_POSTURE_MIN_RANK = {
    "acceptance_stands_for_demo_scope": 0,
    "acceptance_requires_review_before_reuse": 1,
    "acceptance_not_reusable_without_governed_review": 2,
}

OVERCLAIM_TOKENS = (
    "certified",
    "approved",
    "audited",
    "legally accepted",
    "legally revoked",
    "challenge resolved",
    "gold accepted",
    "gold certified",
    "compliant",
    "production-approved",
    "production-ready",
    "regulator-ready",
    "regulator approval",
    "trust transferred",
    "trust transfer",
)

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


def sha256_label(path: Path) -> str:
    return "sha256:" + sha256_hex(path)


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


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def non_empty_str_list(v: Any) -> bool:
    if not isinstance(v, list) or not v:
        return False
    return all(non_empty_str(x) for x in v)


def validate_manifest_shape(m: Any) -> str:
    if not isinstance(m, dict):
        return "manifest not object"
    for k, expected in (
        ("document_type", MANIFEST_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
        ("hash_algorithm", "sha256"),
        ("package_root", "."),
    ):
        if m.get(k) != expected:
            return f"{k} != {expected}"
    if not non_empty_str(m.get("handoff_id")):
        return "handoff_id"
    if not non_empty_str(m.get("generated_at")) or parse_iso_8601_z(
        m["generated_at"]
    ) is None:
        return "generated_at"
    for k in ("scope_limitations", "non_claims"):
        # NOTE: we only check that the field is a list of the right shape here;
        # non-emptiness is enforced later under the specific
        # handoff_limitations_missing / handoff_non_claims_missing reasons.
        if k not in m:
            return k
        if not isinstance(m[k], list):
            return k
        for entry in m[k]:
            if not isinstance(entry, str):
                return f"{k} entry"
    subjects = m.get("subjects")
    if not isinstance(subjects, list) or len(subjects) != len(SUBJECT_ORDER):
        return "subjects shape"
    for i, (_, expected_role) in enumerate(SUBJECT_ORDER):
        s = subjects[i]
        if not isinstance(s, dict):
            return f"subjects[{i}] not object"
        if not non_empty_str(s.get("path")):
            return f"subjects[{i}].path"
        if s.get("role") != expected_role:
            return f"subjects[{i}].role != {expected_role}"
        if not non_empty_str(s.get("sha256")) or not s["sha256"].startswith(
            "sha256:"
        ):
            return f"subjects[{i}].sha256"
        if not isinstance(s.get("size_bytes"), int) or isinstance(
            s["size_bytes"], bool
        ):
            return f"subjects[{i}].size_bytes"
    # NOTE: path equality against SUBJECT_ORDER is checked in main() AFTER
    # the path-traversal check so '..' surfaces under its specific reason.
    return ""


def validate_summary_shape(s: Any) -> str:
    if not isinstance(s, dict):
        return "summary not object"
    for k, expected in (
        ("document_type", SUMMARY_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
    ):
        if s.get(k) != expected:
            return f"{k} != {expected}"
    if not non_empty_str(s.get("handoff_id")):
        return "handoff_id"
    if not non_empty_str(s.get("generated_at")) or parse_iso_8601_z(
        s["generated_at"]
    ) is None:
        return "generated_at"
    hc = s.get("handoff_context")
    if not isinstance(hc, dict):
        return "handoff_context"
    for k in ("handoff_purpose", "recipient_role", "source_package_family"):
        if not non_empty_str(hc.get(k)):
            return f"handoff_context.{k}"
    ic = s.get("included_chain")
    if not isinstance(ic, dict):
        return "included_chain"

    cge = ic.get("composed_gateway_evidence")
    if not isinstance(cge, dict):
        return "included_chain.composed_gateway_evidence"
    for k in ("manifest_path", "manifest_sha256", "source_release"):
        if not non_empty_str(cge.get(k)):
            return f"included_chain.composed_gateway_evidence.{k}"
    if cge["source_release"] != "v0.2.7":
        return "included_chain.composed_gateway_evidence.source_release"

    rpa = ic.get("relying_party_acceptance")
    if not isinstance(rpa, dict):
        return "included_chain.relying_party_acceptance"
    for k in (
        "manifest_path",
        "manifest_sha256",
        "source_release",
        "acceptance_record_id",
        "decision_status",
        "purpose_id",
    ):
        if not non_empty_str(rpa.get(k)):
            return f"included_chain.relying_party_acceptance.{k}"
    if rpa["source_release"] != "v0.2.8":
        return "included_chain.relying_party_acceptance.source_release"
    if rpa["decision_status"] not in (
        "accepted",
        "rejected",
        "accepted_with_exceptions",
    ):
        return "included_chain.relying_party_acceptance.decision_status"

    rcd = ic.get("revocation_challenge_drill")
    if not isinstance(rcd, dict):
        return "included_chain.revocation_challenge_drill"
    for k in (
        "manifest_path",
        "manifest_sha256",
        "source_release",
        "recommended_local_posture",
    ):
        if not non_empty_str(rcd.get(k)):
            return f"included_chain.revocation_challenge_drill.{k}"
    if rcd["source_release"] != "v0.2.9":
        return "included_chain.revocation_challenge_drill.source_release"

    hr = s.get("handoff_result")
    if not isinstance(hr, dict):
        return "handoff_result"
    if hr.get("handoff_package_status") != "complete":
        return "handoff_result.handoff_package_status"
    if not non_empty_str(hr.get("recommended_handoff_posture")):
        return "handoff_result.recommended_handoff_posture"
    if not non_empty_str(hr.get("reuse_warning")):
        return "handoff_result.reuse_warning"

    # NOTE: scope_limitations / non_claims non-emptiness is intentionally
    # NOT checked here so it surfaces as the more specific reasons.
    for k in ("scope_limitations", "non_claims"):
        if k not in s or not isinstance(s[k], list):
            return k
        for entry in s[k]:
            if not isinstance(entry, str):
                return f"{k} entry"
    return ""


def collect_strings_outside(obj: Any, skip_keys: set[str], out: list[str]) -> None:
    """Recursively collect every string value in obj EXCEPT under
    top-level keys named in skip_keys."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip_keys:
                continue
            collect_strings_outside(v, skip_keys, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_strings_outside(v, skip_keys, out)
    elif isinstance(obj, str):
        out.append(obj)


def collect_fail_detail(proc: subprocess.CompletedProcess) -> str:
    detail = (proc.stdout + proc.stderr).strip().replace("\n", " ; ")
    if not detail:
        detail = f"subprocess exited {proc.returncode}"
    return detail


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.3.0 acceptance handoff package."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        return usage_error(f"--manifest not found: {manifest_path}")
    pkg_root = manifest_path.parent

    # --- (1) Parse manifest ---
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_handoff_manifest", f"{manifest_path}: {e}")

    # --- (2) Manifest shape ---
    shape_err = validate_manifest_shape(manifest)
    if shape_err:
        return fail("invalid_handoff_manifest", shape_err)

    # --- (3) Path traversal BEFORE path equality ---
    for s in manifest["subjects"]:
        if has_traversal(s["path"]):
            return fail("handoff_subject_path_traversal", s["path"])

    # --- (4) Path equality against deterministic SUBJECT_ORDER ---
    for i, (expected_path, _) in enumerate(SUBJECT_ORDER):
        if manifest["subjects"][i]["path"] != expected_path:
            return fail(
                "invalid_handoff_manifest",
                f"subjects[{i}].path != {expected_path}",
            )

    # --- (5) Subject file existence ---
    for s in manifest["subjects"]:
        full = pkg_root / s["path"]
        if not full.exists():
            return fail("handoff_subject_file_missing", s["path"])

    # --- (6) Subject SHA-256 recompute ---
    recomputed_hashes: dict[str, str] = {}
    for s in manifest["subjects"]:
        full = pkg_root / s["path"]
        recomputed = sha256_label(full)
        if recomputed != s["sha256"]:
            return fail(
                "handoff_subject_hash_mismatch",
                f"{s['path']}: recorded={s['sha256']}, recomputed={recomputed}",
            )
        recomputed_hashes[s["path"]] = recomputed

    subj0_sha = recomputed_hashes[SUBJECT_ORDER[0][0]]
    subj1_sha = recomputed_hashes[SUBJECT_ORDER[1][0]]
    subj2_sha = recomputed_hashes[SUBJECT_ORDER[2][0]]

    # --- (7) Subprocess v0.2.7 verifier on nested composed manifest ---
    nested_composed_manifest = pkg_root / SUBJECT_ORDER[0][0]
    proc = subprocess.run(
        [
            sys.executable,
            str(COMPOSED_VERIFIER),
            "--manifest",
            str(nested_composed_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "nested_composed_evidence_invalid", collect_fail_detail(proc)
        )

    # --- (8) Subprocess v0.2.8 acceptance validator (NO --evidence-package-root) ---
    nested_accept_manifest = pkg_root / SUBJECT_ORDER[1][0]
    proc = subprocess.run(
        [
            sys.executable,
            str(ACCEPTANCE_VALIDATOR),
            "--manifest",
            str(nested_accept_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "nested_acceptance_package_invalid", collect_fail_detail(proc)
        )

    # --- (9) Subprocess v0.2.9 drill verifier (NO --evidence-package-root) ---
    nested_drill_manifest = pkg_root / SUBJECT_ORDER[2][0]
    proc = subprocess.run(
        [
            sys.executable,
            str(DRILL_VERIFIER),
            "--manifest",
            str(nested_drill_manifest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return fail(
            "nested_revocation_challenge_drill_invalid",
            collect_fail_detail(proc),
        )

    # --- (10) Parse + shape-validate handoff summary ---
    summary_path = pkg_root / SUBJECT_ORDER[3][0]
    try:
        summary = json.loads(summary_path.read_text())
    except json.JSONDecodeError as e:
        return fail("handoff_summary_invalid", f"{summary_path}: {e}")
    sh_err = validate_summary_shape(summary)
    if sh_err:
        return fail("handoff_summary_invalid", sh_err)

    # --- (11) Summary included_chain manifest_sha256 binding ---
    ic = summary["included_chain"]
    summary_chain = [
        (
            "composed_gateway_evidence",
            ic["composed_gateway_evidence"]["manifest_path"],
            ic["composed_gateway_evidence"]["manifest_sha256"],
            SUBJECT_ORDER[0][0],
            subj0_sha,
        ),
        (
            "relying_party_acceptance",
            ic["relying_party_acceptance"]["manifest_path"],
            ic["relying_party_acceptance"]["manifest_sha256"],
            SUBJECT_ORDER[1][0],
            subj1_sha,
        ),
        (
            "revocation_challenge_drill",
            ic["revocation_challenge_drill"]["manifest_path"],
            ic["revocation_challenge_drill"]["manifest_sha256"],
            SUBJECT_ORDER[2][0],
            subj2_sha,
        ),
    ]
    for label, sum_path, sum_sha, expected_path, expected_sha in summary_chain:
        if sum_path != expected_path:
            return fail(
                "handoff_summary_binding_mismatch",
                f"included_chain.{label}.manifest_path={sum_path!r} != "
                f"{expected_path!r}",
            )
        if sum_sha != expected_sha:
            return fail(
                "handoff_summary_binding_mismatch",
                f"included_chain.{label}.manifest_sha256={sum_sha!r} != "
                f"recomputed {expected_sha!r}",
            )

    # --- (12) v0.3.0-owned chain binding (four cross-checks) ---
    # Load nested v0.2.8 record and v0.2.9 report
    nested_accept_root = nested_accept_manifest.parent
    nested_drill_root = nested_drill_manifest.parent
    try:
        record = json.loads(
            (nested_accept_root / "acceptance-record.json").read_text()
        )
        drill_report = json.loads(
            (
                nested_drill_root / "revocation-challenge-drill-report.json"
            ).read_text()
        )
    except (OSError, json.JSONDecodeError) as e:
        # If these files are missing/unreadable, the nested verifiers above
        # should already have rejected the package. Surface defensively here.
        return fail(
            "handoff_chain_binding_mismatch",
            f"nested record/report unreadable: {e}",
        )

    record_evp = record.get("evidence_package", {}) if isinstance(record, dict) else {}
    record_ev_sha = record_evp.get("manifest_sha256") if isinstance(record_evp, dict) else None
    drill_base = drill_report.get("base_acceptance", {}) if isinstance(drill_report, dict) else {}
    drill_accept_sha = drill_base.get("acceptance_package_manifest_sha256") if isinstance(drill_base, dict) else None
    if not non_empty_str(record_ev_sha):
        return fail(
            "handoff_chain_binding_mismatch",
            "nested v0.2.8 record evidence_package.manifest_sha256 missing",
        )
    if not non_empty_str(drill_accept_sha):
        return fail(
            "handoff_chain_binding_mismatch",
            "nested v0.2.9 drill report "
            "base_acceptance.acceptance_package_manifest_sha256 missing",
        )

    # (a) subject[0] sha256 == record.evidence_package.manifest_sha256
    if subj0_sha != record_ev_sha:
        return fail(
            "handoff_chain_binding_mismatch",
            f"composed-gateway-evidence manifest sha256 ({subj0_sha}) "
            f"!= nested v0.2.8 record "
            f"evidence_package.manifest_sha256 ({record_ev_sha})",
        )
    # (b) subject[1] sha256 == drill.base_acceptance.acceptance_package_manifest_sha256
    if subj1_sha != drill_accept_sha:
        return fail(
            "handoff_chain_binding_mismatch",
            f"acceptance-package manifest sha256 ({subj1_sha}) "
            f"!= nested v0.2.9 drill "
            f"base_acceptance.acceptance_package_manifest_sha256 "
            f"({drill_accept_sha})",
        )
    # (c) sha256 of v0.2.8's inner copy of the v0.2.7 manifest
    inner_accept_evidence_manifest = (
        nested_accept_root
        / "evidence"
        / "composed-gateway-evidence-manifest.json"
    )
    if not inner_accept_evidence_manifest.exists():
        return fail(
            "handoff_chain_binding_mismatch",
            "acceptance-package inner v0.2.7 manifest missing: "
            "acceptance-package/evidence/composed-gateway-evidence-manifest.json",
        )
    inner_accept_evidence_sha = sha256_label(inner_accept_evidence_manifest)
    if inner_accept_evidence_sha != subj0_sha:
        return fail(
            "handoff_chain_binding_mismatch",
            f"acceptance-package inner v0.2.7 manifest sha256 "
            f"({inner_accept_evidence_sha}) != top-level composed-gateway-"
            f"evidence manifest sha256 ({subj0_sha})",
        )
    # (d) sha256 of v0.2.9's inner copy of the v0.2.8 manifest
    inner_drill_accept_manifest = (
        nested_drill_root
        / "acceptance-package"
        / "acceptance-package-manifest.json"
    )
    if not inner_drill_accept_manifest.exists():
        return fail(
            "handoff_chain_binding_mismatch",
            "revocation-challenge-drill inner v0.2.8 manifest missing: "
            "revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json",
        )
    inner_drill_accept_sha = sha256_label(inner_drill_accept_manifest)
    if inner_drill_accept_sha != subj1_sha:
        return fail(
            "handoff_chain_binding_mismatch",
            f"revocation-challenge-drill inner v0.2.8 manifest sha256 "
            f"({inner_drill_accept_sha}) != top-level acceptance-package "
            f"manifest sha256 ({subj1_sha})",
        )

    # --- (13) handoff_record_mismatch on acceptance_record_id / decision_status ---
    rpa = ic["relying_party_acceptance"]
    nested_record_id = record.get("record_id")
    nested_decision_status = record.get("decision", {}).get("status")
    if rpa["acceptance_record_id"] != nested_record_id:
        return fail(
            "handoff_record_mismatch",
            f"included_chain.relying_party_acceptance.acceptance_record_id="
            f"{rpa['acceptance_record_id']!r} != nested v0.2.8 record "
            f"record_id={nested_record_id!r}",
        )
    if rpa["decision_status"] != nested_decision_status:
        return fail(
            "handoff_record_mismatch",
            f"included_chain.relying_party_acceptance.decision_status="
            f"{rpa['decision_status']!r} != nested v0.2.8 record "
            f"decision.status={nested_decision_status!r}",
        )

    # --- (14) handoff_purpose_mismatch ---
    nested_purpose_id = record.get("decision", {}).get("purpose_id")
    if rpa["purpose_id"] != nested_purpose_id:
        return fail(
            "handoff_purpose_mismatch",
            f"included_chain.relying_party_acceptance.purpose_id="
            f"{rpa['purpose_id']!r} != nested v0.2.8 record "
            f"decision.purpose_id={nested_purpose_id!r}",
        )

    # --- (15) Posture validation ---
    rcd = ic["revocation_challenge_drill"]
    drill_posture = rcd["recommended_local_posture"]
    if drill_posture not in DRILL_POSTURE_MIN_RANK:
        return fail(
            "handoff_posture_invalid",
            f"included_chain.revocation_challenge_drill."
            f"recommended_local_posture={drill_posture!r} not in known set",
        )
    # Cross-check that the summary value agrees with the nested drill report.
    nested_drill_posture = drill_report.get("recommended_local_posture")
    if drill_posture != nested_drill_posture:
        return fail(
            "handoff_posture_invalid",
            f"summary recommended_local_posture={drill_posture!r} != "
            f"nested v0.2.9 drill recommended_local_posture="
            f"{nested_drill_posture!r}",
        )
    handoff_posture = summary["handoff_result"]["recommended_handoff_posture"]
    if handoff_posture not in HANDOFF_POSTURE_RANK:
        return fail(
            "handoff_posture_invalid",
            f"handoff_result.recommended_handoff_posture="
            f"{handoff_posture!r} not in closed set",
        )
    required_rank = DRILL_POSTURE_MIN_RANK[drill_posture]
    actual_rank = HANDOFF_POSTURE_RANK[handoff_posture]
    if actual_rank < required_rank:
        return fail(
            "handoff_posture_downgrade",
            f"handoff_result.recommended_handoff_posture="
            f"{handoff_posture!r} (rank {actual_rank}) is weaker than the "
            f"rank required by nested v0.2.9 drill "
            f"recommended_local_posture={drill_posture!r} "
            f"(minimum rank {required_rank})",
        )

    # --- (16) Overclaim guard ---
    strings_to_scan: list[str] = []
    collect_strings_outside(
        summary, skip_keys={"scope_limitations", "non_claims"}, out=strings_to_scan
    )
    for s in strings_to_scan:
        lowered = s.lower()
        for token in OVERCLAIM_TOKENS:
            if token in lowered:
                return fail(
                    "handoff_overclaim",
                    f"forbidden token {token!r} found in summary string "
                    f"outside scope_limitations / non_claims: {s!r}",
                )

    # --- (17) scope_limitations / non_claims non-emptiness ---
    if not non_empty_str_list(manifest.get("scope_limitations")):
        return fail(
            "handoff_limitations_missing", "manifest.scope_limitations"
        )
    if not non_empty_str_list(summary.get("scope_limitations")):
        return fail(
            "handoff_limitations_missing", "summary.scope_limitations"
        )
    if not non_empty_str_list(manifest.get("non_claims")):
        return fail("handoff_non_claims_missing", "manifest.non_claims")
    if not non_empty_str_list(summary.get("non_claims")):
        return fail("handoff_non_claims_missing", "summary.non_claims")

    print(
        f"PASS: silver acceptance handoff valid ({summary['handoff_id']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
