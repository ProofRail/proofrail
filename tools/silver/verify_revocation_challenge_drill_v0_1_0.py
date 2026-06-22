#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.2.9 revocation/challenge drill package.

Hash-first, fail-fast. The verifier:

  1.  Parses the drill package manifest.
  2.  Validates manifest shape: document_type, schema_version,
      proofrail_release, hash_algorithm, package_root, drill_id,
      generated_at, subject count, subject order, role set,
      scope_limitations presence, non_claims presence.
  3.  Rejects any subject path containing '..' or that is absolute.
  4.  Checks each subject file exists.
  5.  Recomputes SHA-256 for each subject and compares to the recorded
      sha256.
  6.  Subprocess-invokes the v0.2.8 acceptance record validator on the
      nested acceptance-package/acceptance-package-manifest.json,
      optionally passing --evidence-package-root through.
  7.  Parses and structurally validates the drill report JSON.
  8.  Cross-checks drill report base_acceptance.* against the nested
      v0.2.8 acceptance record/policy and the recomputed
      acceptance-package-manifest.json sha256.
  9.  Requires base_acceptance.challenge_window.opens_at /
      closes_at to be present and ISO-8601 UTC Z-suffixed.
  10. Parses the review-events JSONL file.
  11. Recomputes the review-events file sha256 and compares against
      report.review_events.events_sha256.
  12. Splits events by event_type and verifies targets:
        - non-revocation events: target deviation ->
          review_event_target_mismatch
        - revocation.signal_received events: target deviation ->
          revocation_signal_target_mismatch
  13. Verifies event_time monotonicity.
  14. Verifies every report finding/trigger of type
      challenge_within_window references a challenge.received event
      whose event_time lies in the bound challenge_window
      (challenge_window_classification_mismatch), BEFORE checking that
      at least one such event exists (challenge_within_window_missing).
  15. Verifies at least one revocation.signal_received event exists
      (revocation_signal_missing).
  16. Verifies required findings and review triggers.
  17. Validates recommended_local_posture against the closed set, and
      rejects acceptance_stands_for_demo_scope when triggers are
      present.
  18. Requires non-empty scope_limitations and non_claims.

Stable failure reasons:

  invalid_drill_package_manifest
  drill_subject_file_missing
  drill_subject_path_traversal
  drill_subject_hash_mismatch
  nested_acceptance_package_invalid
  invalid_review_events
  invalid_drill_report
  acceptance_record_binding_mismatch
  review_events_hash_mismatch
  review_event_target_mismatch
  review_event_sequence_invalid
  challenge_window_missing
  challenge_within_window_missing
  challenge_window_classification_mismatch
  revocation_signal_missing
  revocation_signal_target_mismatch
  required_finding_missing
  required_review_trigger_missing
  recommended_posture_invalid
  scope_limitations_missing
  drill_non_claims_missing
  external_evidence_verification_failed

Note: 'acceptance_package_validation_failed' and
'review_fixture_insufficient' are runner-only codes (used by
run_revocation_challenge_drill_v0_1_0.py) and are never emitted by this
verifier.

Usage:
  python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \\
    [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]

Exit codes:
  0 - drill package valid
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
ACCEPTANCE_VALIDATOR = (
    REPO_ROOT / "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
)

REVIEW_EVENT_DOCUMENT_TYPE = "proofrail.silver.relying_party_review_event"
DRILL_REPORT_DOCUMENT_TYPE = (
    "proofrail.silver.revocation_challenge_drill_report"
)
DRILL_MANIFEST_DOCUMENT_TYPE = (
    "proofrail.silver.revocation_challenge_drill_manifest"
)
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.9"

SUBJECT_ORDER = [
    (
        "acceptance-package/acceptance-package-manifest.json",
        "nested_acceptance_package_manifest",
    ),
    ("review-events.jsonl", "review_events"),
    (
        "revocation-challenge-drill-report.json",
        "revocation_challenge_drill_report",
    ),
]

POSTURES = {
    "acceptance_stands_for_demo_scope",
    "acceptance_requires_review_before_reuse",
    "acceptance_not_reusable_without_governed_review",
}

EVENT_TYPES = {
    "challenge.received",
    "revocation.signal_received",
    "acceptance.revalidation_performed",
}

REQUIRED_TRIGGER_TYPES = {
    "challenge_within_window",
    "post_acceptance_revocation_signal",
}

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
        ("document_type", DRILL_MANIFEST_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
        ("hash_algorithm", "sha256"),
        ("package_root", "."),
    ):
        if m.get(k) != expected:
            return f"{k} != {expected}"
    if not non_empty_str(m.get("drill_id")):
        return "drill_id"
    if not non_empty_str(m.get("generated_at")) or parse_iso_8601_z(
        m["generated_at"]
    ) is None:
        return "generated_at"
    for k in ("scope_limitations", "non_claims"):
        if not non_empty_str_list(m.get(k)):
            return k
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
    # NOTE: subject path equality with SUBJECT_ORDER is checked in main()
    # AFTER drill_subject_path_traversal so that a malicious '..' or
    # absolute path surfaces under its specific reason rather than as
    # invalid_drill_package_manifest.
    return ""


def validate_report_shape(r: Any) -> str:
    if not isinstance(r, dict):
        return "report not object"
    for k, expected in (
        ("document_type", DRILL_REPORT_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
    ):
        if r.get(k) != expected:
            return f"{k} != {expected}"
    if not non_empty_str(r.get("drill_id")):
        return "drill_id"
    if not non_empty_str(r.get("generated_at")) or parse_iso_8601_z(
        r["generated_at"]
    ) is None:
        return "generated_at"
    ba = r.get("base_acceptance")
    if not isinstance(ba, dict):
        return "base_acceptance"
    for k in (
        "acceptance_record_id",
        "decision_status",
        "purpose_id",
        "acceptance_policy_id",
        "acceptance_policy_version",
        "acceptance_package_manifest_sha256",
    ):
        if not non_empty_str(ba.get(k)):
            return f"base_acceptance.{k}"
    bav = r.get("base_acceptance_validation")
    if not isinstance(bav, dict):
        return "base_acceptance_validation"
    for k in ("validator_tool", "validation_result", "validated_at"):
        if not non_empty_str(bav.get(k)):
            return f"base_acceptance_validation.{k}"
    re_obj = r.get("review_events")
    if not isinstance(re_obj, dict):
        return "review_events"
    for k in ("events_path", "events_sha256"):
        if not non_empty_str(re_obj.get(k)):
            return f"review_events.{k}"
    if not isinstance(re_obj.get("event_count"), int) or isinstance(
        re_obj["event_count"], bool
    ):
        return "review_events.event_count"
    if not isinstance(r.get("findings"), list):
        return "findings"
    if not isinstance(r.get("review_triggers"), list):
        return "review_triggers"
    if not non_empty_str(r.get("recommended_local_posture")):
        return "recommended_local_posture"
    # NOTE: scope_limitations and non_claims are intentionally NOT checked
    # at the report shape level so that empty values surface as the more
    # specific scope_limitations_missing / drill_non_claims_missing
    # reasons later in main(), not invalid_drill_report.
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a ProofRail Silver v0.2.9 revocation/challenge drill "
            "package."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--evidence-package-root",
        default=None,
        type=Path,
        help="Optional path to the original v0.2.7 composed gateway "
        "evidence package root. Passed through to the v0.2.8 acceptance "
        "validator.",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        return usage_error(f"--manifest not found: {manifest_path}")
    pkg_root = manifest_path.parent

    # --- (1) Parse manifest ---
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_drill_package_manifest", f"{manifest_path}: {e}")

    # --- (2) Manifest shape ---
    shape_err = validate_manifest_shape(manifest)
    if shape_err:
        return fail("invalid_drill_package_manifest", shape_err)

    # --- (3) Path traversal (before path-equality so traversal surfaces specifically) ---
    for s in manifest["subjects"]:
        p = s["path"]
        if has_traversal(p):
            return fail("drill_subject_path_traversal", p)
    # --- (3b) Path equality against deterministic SUBJECT_ORDER ---
    for i, (expected_path, _) in enumerate(SUBJECT_ORDER):
        if manifest["subjects"][i]["path"] != expected_path:
            return fail(
                "invalid_drill_package_manifest",
                f"subjects[{i}].path != {expected_path}",
            )
    # --- (4) File existence ---
    for s in manifest["subjects"]:
        full = pkg_root / s["path"]
        if not full.exists():
            return fail("drill_subject_file_missing", s["path"])
    # --- (5) Hash check ---
    for s in manifest["subjects"]:
        full = pkg_root / s["path"]
        recomputed = "sha256:" + sha256_hex(full)
        if recomputed != s["sha256"]:
            return fail(
                "drill_subject_hash_mismatch",
                f"{s['path']}: recorded={s['sha256']}, recomputed={recomputed}",
            )

    # --- (6) Nested v0.2.8 acceptance package validation ---
    nested_manifest = pkg_root / SUBJECT_ORDER[0][0]
    cmd = [
        sys.executable,
        str(ACCEPTANCE_VALIDATOR),
        "--manifest",
        str(nested_manifest),
    ]
    if args.evidence_package_root is not None:
        epr = args.evidence_package_root.resolve()
        if not epr.exists():
            return usage_error(
                f"--evidence-package-root not found: {epr}"
            )
        cmd.extend(["--evidence-package-root", str(epr)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        out = (proc.stdout + proc.stderr)
        if (
            args.evidence_package_root is not None
            and "external_evidence_verification_failed" in out
        ):
            return fail(
                "external_evidence_verification_failed",
                out.strip().replace("\n", " ; "),
            )
        return fail(
            "nested_acceptance_package_invalid",
            out.strip().replace("\n", " ; ")
            or f"v0.2.8 validator exited {proc.returncode}",
        )

    # --- Load nested v0.2.8 record + policy (already known good) ---
    nested_root = nested_manifest.parent
    try:
        nested_record = json.loads(
            (nested_root / "acceptance-record.json").read_text()
        )
        nested_policy = json.loads(
            (nested_root / "acceptance-policy.json").read_text()
        )
    except json.JSONDecodeError as e:
        return fail("nested_acceptance_package_invalid", f"{e}")
    nested_manifest_sha = "sha256:" + sha256_hex(nested_manifest)

    # --- (7) Parse drill report (BEFORE checking events sha) ---
    report_path = pkg_root / SUBJECT_ORDER[2][0]
    try:
        report = json.loads(report_path.read_text())
    except json.JSONDecodeError as e:
        return fail("invalid_drill_report", f"{report_path}: {e}")
    shape_err = validate_report_shape(report)
    if shape_err:
        return fail("invalid_drill_report", shape_err)

    # --- (8) Cross-check base_acceptance against nested package ---
    ba = report["base_acceptance"]
    nested_record_id = nested_record.get("record_id")
    nested_decision_status = nested_record.get("decision", {}).get("status")
    nested_purpose_id = nested_record.get("decision", {}).get("purpose_id")
    nested_policy_id = nested_record.get("relying_party", {}).get("policy_id")
    nested_policy_version = nested_record.get("relying_party", {}).get(
        "policy_version"
    )
    bindings = [
        ("acceptance_record_id", ba["acceptance_record_id"], nested_record_id),
        ("decision_status", ba["decision_status"], nested_decision_status),
        ("purpose_id", ba["purpose_id"], nested_purpose_id),
        ("acceptance_policy_id", ba["acceptance_policy_id"], nested_policy_id),
        (
            "acceptance_policy_version",
            ba["acceptance_policy_version"],
            nested_policy_version,
        ),
        (
            "acceptance_package_manifest_sha256",
            ba["acceptance_package_manifest_sha256"],
            nested_manifest_sha,
        ),
    ]
    for k, got, want in bindings:
        if got != want:
            return fail(
                "acceptance_record_binding_mismatch",
                f"base_acceptance.{k}={got!r} != {want!r}",
            )
    # Also check nested_policy.policy_id/version agree with record (defensive)
    if (
        nested_policy.get("policy_id") != nested_policy_id
        or nested_policy.get("policy_version") != nested_policy_version
    ):
        return fail(
            "acceptance_record_binding_mismatch",
            "nested policy id/version disagree with nested record",
        )

    # --- (9) challenge_window opens_at/closes_at present and ISO-8601 ---
    cw = ba.get("challenge_window")
    if not isinstance(cw, dict):
        return fail("challenge_window_missing", "challenge_window not object")
    opens_at = cw.get("opens_at")
    closes_at = cw.get("closes_at")
    opens_dt = parse_iso_8601_z(opens_at) if isinstance(opens_at, str) else None
    closes_dt = (
        parse_iso_8601_z(closes_at) if isinstance(closes_at, str) else None
    )
    if opens_dt is None or closes_dt is None:
        return fail(
            "challenge_window_missing",
            "challenge_window.opens_at or closes_at missing/malformed",
        )

    # --- (10) Parse review events JSONL ---
    events_path = pkg_root / SUBJECT_ORDER[1][0]
    try:
        events_text = events_path.read_text()
    except OSError as e:
        return fail("invalid_review_events", f"{events_path}: {e}")
    events: list[dict] = []
    for lineno, raw in enumerate(events_text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            return fail("invalid_review_events", f"line {lineno}: {e}")
        if not isinstance(obj, dict):
            return fail(
                "invalid_review_events", f"line {lineno}: not a JSON object"
            )
        for k, expected in (
            ("document_type", REVIEW_EVENT_DOCUMENT_TYPE),
            ("schema_version", SCHEMA_VERSION),
            ("proofrail_release", PROOFRAIL_RELEASE),
        ):
            if obj.get(k) != expected:
                return fail(
                    "invalid_review_events",
                    f"line {lineno}: {k} != {expected}",
                )
        for k in ("event_id", "event_type", "event_time"):
            if not non_empty_str(obj.get(k)):
                return fail(
                    "invalid_review_events",
                    f"line {lineno}: {k} missing or empty",
                )
        if obj["event_type"] not in EVENT_TYPES:
            return fail(
                "invalid_review_events",
                f"line {lineno}: event_type not in closed set",
            )
        if parse_iso_8601_z(obj["event_time"]) is None:
            return fail(
                "invalid_review_events",
                f"line {lineno}: event_time not ISO-8601 UTC Z",
            )
        t = obj.get("target")
        if not isinstance(t, dict):
            return fail(
                "invalid_review_events", f"line {lineno}: target missing"
            )
        for k in ("acceptance_record_id", "purpose_id"):
            if not non_empty_str(t.get(k)):
                return fail(
                    "invalid_review_events",
                    f"line {lineno}: target.{k} missing or empty",
                )
        events.append(obj)

    # --- (11) Recompute review-events sha and compare ---
    events_sha = "sha256:" + sha256_hex(events_path)
    if report["review_events"]["events_sha256"] != events_sha:
        return fail(
            "review_events_hash_mismatch",
            f"recorded={report['review_events']['events_sha256']}, "
            f"recomputed={events_sha}",
        )
    if report["review_events"]["event_count"] != len(events):
        return fail(
            "invalid_drill_report",
            f"review_events.event_count={report['review_events']['event_count']} "
            f"!= parsed count {len(events)}",
        )

    # --- (12) Target checks split by event_type ---
    bound_record_id = ba["acceptance_record_id"]
    bound_purpose_id = ba["purpose_id"]
    for e in events:
        t = e["target"]
        et = e["event_type"]
        if et == "revocation.signal_received":
            if (
                t["acceptance_record_id"] != bound_record_id
                or t["purpose_id"] != bound_purpose_id
            ):
                return fail(
                    "revocation_signal_target_mismatch",
                    f"event {e['event_id']}: target={t!r}, "
                    f"bound=({bound_record_id!r}, {bound_purpose_id!r})",
                )
        else:
            if (
                t["acceptance_record_id"] != bound_record_id
                or t["purpose_id"] != bound_purpose_id
            ):
                return fail(
                    "review_event_target_mismatch",
                    f"event {e['event_id']}: target={t!r}, "
                    f"bound=({bound_record_id!r}, {bound_purpose_id!r})",
                )

    # --- (13) Monotonicity ---
    prev_dt: datetime | None = None
    for e in events:
        cur = parse_iso_8601_z(e["event_time"])
        if prev_dt is not None and cur < prev_dt:
            return fail(
                "review_event_sequence_invalid",
                f"event {e['event_id']} event_time precedes previous event",
            )
        prev_dt = cur

    # --- (14) Classification BEFORE missing-counts ---
    events_by_id = {e["event_id"]: e for e in events}
    # First: any report finding/trigger claiming challenge_within_window must
    # reference a challenge.received event whose event_time is in window.
    def _check_classification(claimed_event_ids: list[str], context: str) -> int | None:
        for eid in claimed_event_ids:
            ev = events_by_id.get(eid)
            if ev is None:
                return fail(
                    "challenge_window_classification_mismatch",
                    f"{context} references unknown event_id {eid!r}",
                )
            if ev["event_type"] != "challenge.received":
                return fail(
                    "challenge_window_classification_mismatch",
                    f"{context} references non-challenge event {eid!r}",
                )
            ts = parse_iso_8601_z(ev["event_time"])
            if not (opens_dt <= ts <= closes_dt):
                return fail(
                    "challenge_window_classification_mismatch",
                    f"{context} references event {eid!r} with event_time "
                    f"{ev['event_time']} outside [{opens_at}, {closes_at}]",
                )
        return None

    findings = report["findings"]
    review_triggers = report["review_triggers"]
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            return fail("invalid_drill_report", f"findings[{i}] not object")
        if f.get("finding_type") == "challenge_within_window":
            eids = f.get("event_ids")
            if not isinstance(eids, list) or not all(
                non_empty_str(x) for x in eids
            ) or not eids:
                return fail(
                    "invalid_drill_report",
                    f"findings[{i}].event_ids missing or empty",
                )
            rc = _check_classification(
                eids, f"findings[{i}] (challenge_within_window)"
            )
            if rc is not None:
                return rc
    for i, t in enumerate(review_triggers):
        if not isinstance(t, dict):
            return fail(
                "invalid_drill_report", f"review_triggers[{i}] not object"
            )
        if t.get("trigger_type") == "challenge_within_window":
            eid = t.get("event_id")
            if not non_empty_str(eid):
                return fail(
                    "invalid_drill_report",
                    f"review_triggers[{i}].event_id missing or empty",
                )
            rc = _check_classification(
                [eid], f"review_triggers[{i}] (challenge_within_window)"
            )
            if rc is not None:
                return rc

    # Then: actual within-window challenge events must exist somewhere.
    within_window_challenges = [
        e
        for e in events
        if e["event_type"] == "challenge.received"
        and opens_dt <= parse_iso_8601_z(e["event_time"]) <= closes_dt
    ]
    if not within_window_challenges:
        return fail(
            "challenge_within_window_missing",
            "no challenge.received events with event_time inside "
            f"[{opens_at}, {closes_at}]",
        )

    # --- (15) Revocation signal presence ---
    revocation_signals = [
        e for e in events if e["event_type"] == "revocation.signal_received"
    ]
    if not revocation_signals:
        return fail(
            "revocation_signal_missing",
            "no revocation.signal_received events in review-events.jsonl",
        )

    # --- (16) Required findings + triggers ---
    finding_types = {
        f.get("finding_type") for f in findings if isinstance(f, dict)
    }
    required_finding_types = {
        "challenge_within_window",
        "revocation_signal_recorded",
    }
    # acceptance_revalidated is required when any revalidation event exists
    revalidations = [
        e
        for e in events
        if e["event_type"] == "acceptance.revalidation_performed"
    ]
    if revalidations:
        required_finding_types.add("acceptance_revalidated")
    missing_findings = required_finding_types - finding_types
    if missing_findings:
        return fail(
            "required_finding_missing",
            f"missing finding types: {sorted(missing_findings)}",
        )

    trigger_types = {
        t.get("trigger_type") for t in review_triggers if isinstance(t, dict)
    }
    missing_triggers = REQUIRED_TRIGGER_TYPES - trigger_types
    if missing_triggers:
        return fail(
            "required_review_trigger_missing",
            f"missing trigger types: {sorted(missing_triggers)}",
        )

    # --- (17) Posture ---
    posture = report["recommended_local_posture"]
    if posture not in POSTURES:
        return fail(
            "recommended_posture_invalid",
            f"recommended_local_posture={posture!r} not in closed set",
        )
    triggers_present = bool(review_triggers)
    if triggers_present and posture == "acceptance_stands_for_demo_scope":
        return fail(
            "recommended_posture_invalid",
            "review_triggers present but recommended_local_posture is "
            "acceptance_stands_for_demo_scope",
        )

    # --- (18) scope_limitations / non_claims ---
    # Already validated for shape; re-check report-side non-emptiness here
    # explicitly, in case the report shape validator was loosened later.
    if not non_empty_str_list(report.get("scope_limitations")):
        return fail("scope_limitations_missing", "report.scope_limitations")
    if not non_empty_str_list(report.get("non_claims")):
        return fail("drill_non_claims_missing", "report.non_claims")

    print(
        f"PASS: revocation/challenge drill valid ({report['drill_id']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
