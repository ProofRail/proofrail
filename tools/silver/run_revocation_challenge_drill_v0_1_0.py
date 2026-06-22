#!/usr/bin/env python3
"""Run a ProofRail Silver v0.2.9 revocation/challenge drill.

The runner:

  1. Refuses to overwrite --output-dir unless --force is supplied.
  2. Validates --generated-at as ISO-8601 UTC Z-suffixed.
  3. Subprocess-invokes the v0.2.8 acceptance record validator on
     --acceptance-manifest, optionally passing --evidence-package-root.
  4. If the v0.2.8 validator fails, prints
         FAIL: acceptance_package_validation_failed: <detail>
     to stderr, removes any partial staging directory, and exits 1.
  5. Stages the full v0.2.8 acceptance package under
         <staging>/acceptance-package/
     and copies the --review-events fixture into
         <staging>/review-events.jsonl
  6. Parses the nested v0.2.8 acceptance record and acceptance policy.
  7. Parses the review-events JSONL strictly:
       - every event must use document_type
         proofrail.silver.relying_party_review_event
       - every event must use schema_version v0.1.0 and proofrail_release
         v0.2.9
       - every event must include event_id, event_type, event_time, and a
         target object with acceptance_record_id and purpose_id
       - target.acceptance_record_id and target.purpose_id must equal the
         bound v0.2.8 acceptance record's record_id and
         decision.purpose_id
       - event_time must be ISO-8601 UTC Z-suffixed and non-decreasing
       - event-type-specific required fields must be non-empty strings
  8. Refuses, with FAIL: review_fixture_insufficient: <detail>, exit 1,
     when the fixture contains zero within-window challenges or zero
     revocation signals.
  9. Derives findings, review triggers, and recommended_local_posture.
 10. Emits revocation-challenge-drill-report.json and
     revocation-challenge-drill-manifest.json.
 11. Atomically moves the staging directory to --output-dir.
 12. When --self-validate is supplied, subprocess-invokes the v0.2.9
     drill verifier on the resulting drill package manifest and exits
     non-zero on failure.

No external services, no real challenge submission, no real revocation
publication.

Usage:
  python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \\
    --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \\
    --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \\
    --generated-at 2026-06-27T00:00:00Z \\
    --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \\
    --force \\
    [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7] \\
    [--self-validate]

Exit codes:
  0 - drill package generated
  1 - drill refused (acceptance_package_validation_failed,
      review_fixture_insufficient, or self-validation failed)
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_VALIDATOR = (
    REPO_ROOT / "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
)
DRILL_VERIFIER = (
    REPO_ROOT / "tools/silver/verify_revocation_challenge_drill_v0_1_0.py"
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

ACCEPTANCE_VALIDATOR_REL = (
    "tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
)

EVENT_TYPES = {
    "challenge.received",
    "revocation.signal_received",
    "acceptance.revalidation_performed",
}

POSTURES = (
    "acceptance_stands_for_demo_scope",
    "acceptance_requires_review_before_reuse",
    "acceptance_not_reusable_without_governed_review",
)

DEFAULT_SCOPE_LIMITATIONS = [
    "The drill applies only to the deterministic v0.2.8 acceptance package "
    "and v0.2.9 review-event fixture.",
    "The drill does not adjudicate challenge merits.",
    "The drill does not revoke acceptance or execute governance.",
]
DEFAULT_NON_CLAIMS = [
    "This drill report is not a certificate.",
    "This drill report is not Gold conformance.",
    "This drill report is not regulator approval.",
    "This drill report does not execute a challenge or dispute process.",
]
DEFAULT_MANIFEST_SCOPE_LIMITATIONS = [
    "This drill manifest hash-anchors a local, demo revocation/challenge "
    "drill package; it is not signed.",
    "This drill manifest does not establish Gold conformance.",
]
DEFAULT_MANIFEST_NON_CLAIMS = [
    "This drill manifest does not adjudicate any challenge.",
    "This drill manifest does not revoke the v0.2.8 acceptance record.",
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


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def copy_tree(src: Path, dst: Path) -> None:
    """Copy directory tree src -> dst. dst must not yet exist."""
    shutil.copytree(src, dst)


def parse_review_events(path: Path) -> tuple[list[dict] | None, str]:
    try:
        text = path.read_text()
    except OSError as e:
        return None, f"cannot read {path}: {e}"
    events: list[dict] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            return None, f"line {lineno}: {e}"
        if not isinstance(obj, dict):
            return None, f"line {lineno}: not a JSON object"
        events.append(obj)
    return events, ""


def validate_event_shape(e: dict, lineno: int) -> str:
    for k, expected in (
        ("document_type", REVIEW_EVENT_DOCUMENT_TYPE),
        ("schema_version", SCHEMA_VERSION),
        ("proofrail_release", PROOFRAIL_RELEASE),
    ):
        if e.get(k) != expected:
            return f"line {lineno}: {k} != {expected}"
    for k in ("event_id", "event_type", "event_time"):
        if not non_empty_str(e.get(k)):
            return f"line {lineno}: {k} missing or empty"
    if e["event_type"] not in EVENT_TYPES:
        return f"line {lineno}: event_type not in closed set"
    if parse_iso_8601_z(e["event_time"]) is None:
        return f"line {lineno}: event_time not ISO-8601 UTC Z"
    target = e.get("target")
    if not isinstance(target, dict):
        return f"line {lineno}: target missing"
    for k in ("acceptance_record_id", "purpose_id"):
        if not non_empty_str(target.get(k)):
            return f"line {lineno}: target.{k} missing or empty"
    et = e["event_type"]
    if et == "challenge.received":
        for k in (
            "submitted_by",
            "challenge_reason",
            "challenge_summary",
            "expected_local_handling",
        ):
            if not non_empty_str(e.get(k)):
                return f"line {lineno}: {k} missing or empty"
    elif et == "revocation.signal_received":
        for k in (
            "signal_kind",
            "signal_source",
            "signal_summary",
            "expected_local_handling",
        ):
            if not non_empty_str(e.get(k)):
                return f"line {lineno}: {k} missing or empty"
    elif et == "acceptance.revalidation_performed":
        for k in ("validator_tool", "validation_result"):
            if not non_empty_str(e.get(k)):
                return f"line {lineno}: {k} missing or empty"
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a ProofRail Silver v0.2.9 revocation/challenge drill over "
            "a v0.2.8 relying-party acceptance package."
        )
    )
    parser.add_argument("--acceptance-manifest", required=True, type=Path)
    parser.add_argument("--review-events", required=True, type=Path)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--evidence-package-root",
        default=None,
        type=Path,
        help="Optional path to the original v0.2.7 composed gateway "
        "evidence package root. When supplied, passed through to the "
        "v0.2.8 acceptance validator.",
    )
    parser.add_argument(
        "--drill-id",
        default="proofrail-revocation-challenge-drill-demo-001",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output-dir if it already exists.",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Run the v0.2.9 drill verifier on the generated package "
        "before exiting.",
    )
    args = parser.parse_args(argv)

    # --- ISO-8601 sanity ---
    if parse_iso_8601_z(args.generated_at) is None:
        return usage_error("--generated-at must be ISO-8601 UTC Z-suffixed")

    # --- Input files exist ---
    accept_manifest = args.acceptance_manifest.resolve()
    if not accept_manifest.exists():
        return usage_error(f"--acceptance-manifest not found: {accept_manifest}")
    review_events_in = args.review_events.resolve()
    if not review_events_in.exists():
        return usage_error(f"--review-events not found: {review_events_in}")
    if args.evidence_package_root is not None:
        epr = args.evidence_package_root.resolve()
        if not epr.exists():
            return usage_error(
                f"--evidence-package-root not found: {epr}"
            )
    else:
        epr = None

    # --- Output dir resolution ---
    out = args.output_dir.resolve()
    if out.exists() and not args.force:
        return usage_error(
            f"--output-dir already exists: {out} (use --force)"
        )

    # --- Subprocess-invoke v0.2.8 acceptance validator FIRST ---
    cmd = [
        sys.executable,
        str(ACCEPTANCE_VALIDATOR),
        "--manifest",
        str(accept_manifest),
    ]
    if epr is not None:
        cmd.extend(["--evidence-package-root", str(epr)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stdout + proc.stderr).strip().replace("\n", " ; ")
        if not detail:
            detail = (
                f"v0.2.8 acceptance validator exited {proc.returncode}"
            )
        return fail("acceptance_package_validation_failed", detail)

    # --- Stage output in a sibling directory next to the destination ---
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = out.parent / f"{out.name}.staging.{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    try:
        staging.mkdir(parents=True)

        # --- Copy v0.2.8 acceptance package contents into staging ---
        accept_root = accept_manifest.parent.resolve()
        dest_accept = staging / "acceptance-package"
        copy_tree(accept_root, dest_accept)

        # --- Copy review-events fixture verbatim ---
        dest_events = staging / "review-events.jsonl"
        shutil.copyfile(review_events_in, dest_events)

        # --- Parse v0.2.8 acceptance record + policy ---
        record_path = dest_accept / "acceptance-record.json"
        policy_path = dest_accept / "acceptance-policy.json"
        if not record_path.exists() or not policy_path.exists():
            return fail(
                "acceptance_package_validation_failed",
                "v0.2.8 package missing acceptance-record.json or "
                "acceptance-policy.json after copy",
            )
        try:
            record = json.loads(record_path.read_text())
            policy = json.loads(policy_path.read_text())
        except json.JSONDecodeError as e:
            return fail(
                "acceptance_package_validation_failed",
                f"nested v0.2.8 record/policy not valid JSON: {e}",
            )

        record_id = record.get("record_id")
        purpose_id = record.get("decision", {}).get("purpose_id")
        decision_status = record.get("decision", {}).get("status")
        policy_id = record.get("relying_party", {}).get("policy_id")
        policy_version = record.get("relying_party", {}).get("policy_version")
        cw = record.get("challenge_window", {})
        cw_opens = cw.get("opens_at")
        cw_closes = cw.get("closes_at")
        cw_opens_dt = parse_iso_8601_z(cw_opens) if isinstance(cw_opens, str) else None
        cw_closes_dt = parse_iso_8601_z(cw_closes) if isinstance(cw_closes, str) else None
        if (
            not non_empty_str(record_id)
            or not non_empty_str(purpose_id)
            or not non_empty_str(decision_status)
            or not non_empty_str(policy_id)
            or not non_empty_str(policy_version)
            or cw_opens_dt is None
            or cw_closes_dt is None
        ):
            return fail(
                "acceptance_package_validation_failed",
                "nested v0.2.8 record missing required derived fields",
            )

        # --- Parse review events ---
        events, perr = parse_review_events(dest_events)
        if events is None:
            return fail(
                "acceptance_package_validation_failed",
                f"review-events.jsonl unreadable: {perr}",
            )
        prev_dt: datetime | None = None
        for i, e in enumerate(events, start=1):
            shape_err = validate_event_shape(e, i)
            if shape_err:
                return usage_error(
                    f"--review-events fixture invalid: {shape_err}"
                )
            if e["target"]["acceptance_record_id"] != record_id:
                return usage_error(
                    f"--review-events fixture event {e['event_id']} "
                    f"target.acceptance_record_id does not match bound "
                    f"acceptance record"
                )
            if e["target"]["purpose_id"] != purpose_id:
                return usage_error(
                    f"--review-events fixture event {e['event_id']} "
                    f"target.purpose_id does not match bound acceptance "
                    f"record"
                )
            cur = parse_iso_8601_z(e["event_time"])
            if prev_dt is not None and cur < prev_dt:
                return usage_error(
                    f"--review-events fixture event_time not monotonic at "
                    f"event {e['event_id']}"
                )
            prev_dt = cur

        # --- Classify ---
        within_window_challenges = []
        revocation_signals = []
        revalidations = []
        for e in events:
            et = e["event_type"]
            ts = parse_iso_8601_z(e["event_time"])
            if et == "challenge.received":
                if cw_opens_dt <= ts <= cw_closes_dt:
                    within_window_challenges.append(e)
            elif et == "revocation.signal_received":
                revocation_signals.append(e)
            elif et == "acceptance.revalidation_performed":
                revalidations.append(e)

        if not within_window_challenges:
            return fail(
                "review_fixture_insufficient",
                "fixture contains zero within-window challenge.received "
                "events",
            )
        if not revocation_signals:
            return fail(
                "review_fixture_insufficient",
                "fixture contains zero revocation.signal_received events",
            )

        # --- Build findings, triggers, posture ---
        findings = []
        findings.append(
            {
                "finding_id": "FINDING-001",
                "finding_type": "challenge_within_window",
                "result": "pass",
                "event_ids": [within_window_challenges[0]["event_id"]],
                "local_effect": "review_required",
            }
        )
        findings.append(
            {
                "finding_id": "FINDING-002",
                "finding_type": "revocation_signal_recorded",
                "result": "pass",
                "event_ids": [revocation_signals[0]["event_id"]],
                "local_effect": "review_required",
            }
        )
        if revalidations:
            findings.append(
                {
                    "finding_id": "FINDING-003",
                    "finding_type": "acceptance_revalidated",
                    "result": "pass",
                    "event_ids": [revalidations[0]["event_id"]],
                    "local_effect": "record_revalidation",
                }
            )

        review_triggers = [
            {
                "trigger_type": "challenge_within_window",
                "severity": "review_required",
                "event_id": within_window_challenges[0]["event_id"],
            },
            {
                "trigger_type": "post_acceptance_revocation_signal",
                "severity": "review_required",
                "event_id": revocation_signals[0]["event_id"],
            },
        ]

        recommended_local_posture = "acceptance_requires_review_before_reuse"

        # --- Hash anchors ---
        copied_accept_manifest = (
            dest_accept / "acceptance-package-manifest.json"
        )
        accept_manifest_sha = "sha256:" + sha256_hex(copied_accept_manifest)
        events_sha = "sha256:" + sha256_hex(dest_events)

        # --- Drill report ---
        report = {
            "document_type": DRILL_REPORT_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "drill_id": args.drill_id,
            "generated_at": args.generated_at,
            "base_acceptance": {
                "acceptance_record_id": record_id,
                "decision_status": decision_status,
                "purpose_id": purpose_id,
                "acceptance_policy_id": policy_id,
                "acceptance_policy_version": policy_version,
                "acceptance_package_manifest_sha256": accept_manifest_sha,
                "challenge_window": {
                    "opens_at": cw_opens,
                    "closes_at": cw_closes,
                },
            },
            "base_acceptance_validation": {
                "validator_tool": ACCEPTANCE_VALIDATOR_REL,
                "validation_result": "pass",
                "validated_at": args.generated_at,
                "failure_reason": None,
            },
            "review_events": {
                "events_path": "review-events.jsonl",
                "events_sha256": events_sha,
                "event_count": len(events),
            },
            "findings": findings,
            "review_triggers": review_triggers,
            "recommended_local_posture": recommended_local_posture,
            "scope_limitations": list(DEFAULT_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_NON_CLAIMS),
        }
        report_path = staging / "revocation-challenge-drill-report.json"
        report_path.write_text(dump_json(report))

        # --- Drill manifest ---
        subjects_spec = [
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
        subjects: list[dict] = []
        for rel, role in subjects_spec:
            full = staging / rel
            subjects.append(
                {
                    "path": rel,
                    "role": role,
                    "sha256": "sha256:" + sha256_hex(full),
                    "size_bytes": full.stat().st_size,
                }
            )
        manifest = {
            "document_type": DRILL_MANIFEST_DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "proofrail_release": PROOFRAIL_RELEASE,
            "drill_id": args.drill_id,
            "generated_at": args.generated_at,
            "hash_algorithm": "sha256",
            "package_root": ".",
            "subjects": subjects,
            "scope_limitations": list(DEFAULT_MANIFEST_SCOPE_LIMITATIONS),
            "non_claims": list(DEFAULT_MANIFEST_NON_CLAIMS),
        }
        manifest_path = staging / "revocation-challenge-drill-manifest.json"
        manifest_path.write_text(dump_json(manifest))

        # --- Atomically move staging into place ---
        if out.exists():
            shutil.rmtree(out)
        # os.replace is atomic on POSIX when src and dst are on the same fs.
        os.replace(str(staging), str(out))
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(f"PASS: revocation/challenge drill package generated at {out}")
    print(f"  drill_id: {args.drill_id}")
    print(f"  base_acceptance.acceptance_record_id: {record_id}")
    print(f"  base_acceptance.decision_status: {decision_status}")
    print(f"  review_events.event_count: {len(events)}")
    print(f"  recommended_local_posture: {recommended_local_posture}")

    if args.self_validate:
        sv = subprocess.run(
            [
                sys.executable,
                str(DRILL_VERIFIER),
                "--manifest",
                str(out / "revocation-challenge-drill-manifest.json"),
            ]
        )
        if sv.returncode != 0:
            return fail(
                "self_validate_failed",
                f"v0.2.9 drill verifier exited {sv.returncode}",
            )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
