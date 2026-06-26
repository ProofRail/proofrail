#!/usr/bin/env python3
"""Build a ProofRail Gold v0.4.3 Challenge Lifecycle Lite package.

The v0.4.3 runner composes a deterministic, hash-anchored local
7-subject package on top of a v0.4.2-shaped 5-subject inherited
package and a hand-authored v0.4.3 challenge lifecycle records
template. Phases:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package, --matrix-input, and --lifecycle-input
      under the closed runner-only refusal set; no other tokens are
      emitted here. A sixth runner-only refusal is intentionally NOT
      introduced for verifier-relayed failures.

  2.  Phase B: build package.
      a. Resolves --output-dir, refusing to overwrite without --force.
      b. Subprocess-invokes the co-located v0.4.2 runner against a
         private scratch directory to derive subjects [0..4]
         (governed reliance package, conformance report, decision
         report, policy evaluation matrix, policy evaluation report).
         The v0.4.3 runner does NOT inline-re-derive any inherited
         v0.4.2 / v0.4.1 / v0.4.0 logic.
      c. Stages under <output-dir>.staging.<pid>; atomically publishes
         via os.replace() on success.
      d. Byte-copies the five inherited subjects into the v0.4.3
         staging directory.
      e. Reads the lifecycle records template (subject [5]), injects
         the three runtime-bound fields (top-level
         `policy_evaluation_report_sha256`, top-level `generated_at`,
         and per-record `lifecycle_fingerprint`), and serializes
         canonically.
      f. Derives the v0.4.3 lifecycle report (subject [6]) by
         deterministic projection over the runtime records body and
         the three source SHA-256 anchors (records, policy evaluation
         report, decision report).
      g. Builds the 7-subject v0.4.3 manifest in fixed subject order.
      h. When --self-validate is supplied, subprocess-invokes the
         v0.4.3 verifier (NOT an inherited verifier directly) against
         the staged manifest BEFORE the atomic move; on non-zero exit
         the staging directory is removed and the verifier output is
         relayed verbatim.

A v0.4.3 package is a deterministic local hand-authored record. It
is NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold.
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
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Runner-only refusal vocabulary (closed set of 5, identical to v0.4.0 /
# v0.4.1 / v0.4.2). A sixth refusal is intentionally NOT introduced for
# verifier-relayed failures; those are surfaced as the verifier's own
# exit code and reason token, relayed verbatim.
# ---------------------------------------------------------------------------

REFUSAL_PATH_MISSING = "runner_input_path_missing"
REFUSAL_PATH_FORBIDDEN = "runner_input_path_forbidden"
REFUSAL_FILE_MISSING = "runner_input_file_missing"
REFUSAL_READ_FAILED = "runner_input_read_failed"
REFUSAL_JSON_INVALID = "runner_input_json_invalid"


def _refuse(reason: str, detail: str) -> None:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Canonical JSON serialization. Byte-identical between runner and verifier
# so derived report bytes survive cross-tool re-derivation.
# ---------------------------------------------------------------------------

def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


# ---------------------------------------------------------------------------
# Phase A: preflight only. Closed set of 5 runner-only refusal reasons.
# ---------------------------------------------------------------------------

def _preflight_input_path(input_path: str | None, arg_label: str) -> Path:
    if input_path is None or input_path == "":
        _refuse(REFUSAL_PATH_MISSING, f"{arg_label} is required and must be non-empty")
    p = input_path  # type: ignore[assignment]
    if os.path.isabs(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"absolute path is not permitted: {p!r}")
    if _has_traversal(p):
        _refuse(REFUSAL_PATH_FORBIDDEN, f"path traversal is not permitted: {p!r}")
    pp = Path(p)
    if not pp.exists():
        _refuse(REFUSAL_FILE_MISSING, f"input path does not exist: {p!r}")
    if pp.is_dir():
        _refuse(REFUSAL_READ_FAILED, f"input path is a directory, not a file: {p!r}")
    try:
        raw = pp.read_bytes()
    except OSError as e:
        _refuse(REFUSAL_READ_FAILED, f"cannot read input file: {p!r}: {e}")
    try:
        json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        _refuse(REFUSAL_JSON_INVALID, f"input is not valid JSON: {p!r}: {e}")
    return pp


# ---------------------------------------------------------------------------
# Subject paths and manifest filename. Subjects [0..4] are the inherited
# v0.4.2 subjects (filenames must match v0.4.2 runner output). Subjects
# [5] and [6] are v0.4.3-owned.
# ---------------------------------------------------------------------------

PACKAGE_SUBJECT_PATH = "governed-reliance-scenarios.json"
CONFORMANCE_SUBJECT_PATH = "silver-gold-governed-reliance-conformance-report.json"
DECISION_SUBJECT_PATH = "gold-governed-reliance-decision-report.json"
MATRIX_SUBJECT_PATH = "gold-policy-evaluation-matrix.json"
EVALUATION_SUBJECT_PATH = "gold-policy-evaluation-report.json"
RECORDS_SUBJECT_PATH = "challenge-lifecycle-records.json"
LIFECYCLE_REPORT_SUBJECT_PATH = "gold-challenge-lifecycle-report.json"
MANIFEST_FILENAME = "gold-challenge-lifecycle-package-manifest.json"

# v0.4.2 manifest filename (emitted by the v0.4.2 runner inside the
# inherited scratch directory; the v0.4.3 runner discards it after
# extracting the five inherited subject bytes).
INHERITED_V042_MANIFEST_FILENAME = "gold-policy-evaluation-matrix-package-manifest.json"

# ---------------------------------------------------------------------------
# Co-located v0.4.2 runner and v0.4.3 verifier paths (subprocess-invoked).
# ---------------------------------------------------------------------------

GOLD_V042_RUNNER = (
    Path(__file__).resolve().parent / "build_gold_policy_evaluation_matrix_v0_1_0.py"
)
GOLD_V043_VERIFIER = (
    Path(__file__).resolve().parent / "verify_gold_challenge_lifecycle_lite_v0_1_0.py"
)


# ---------------------------------------------------------------------------
# Phase B step (b): subprocess-delegate to the v0.4.2 runner to build the
# inherited 5-subject package in a private scratch directory.
# ---------------------------------------------------------------------------

def _invoke_v042_runner(
    *,
    input_package: Path,
    matrix_input: Path,
    inherited_out_dir: Path,
    inherited_manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    policy_evaluation_report_id: str,
    generated_at: str,
) -> int:
    """Subprocess-invoke the v0.4.2 runner to produce inherited subjects [0..4].

    The v0.4.2 runner is invoked without --self-validate so that the v0.4.3
    verifier (later, via --self-validate at the v0.4.3 layer) is the single
    entry point for chained verification (v0.4.3 → v0.4.2 → v0.4.1 → v0.4.0).
    The inherited manifest emitted by v0.4.2 is read for its subject sha256
    values, then discarded; it is NOT a subject of the v0.4.3 manifest.
    """
    cmd = [
        sys.executable,
        str(GOLD_V042_RUNNER),
        "--input-package", str(input_package),
        "--matrix-input", str(matrix_input),
        "--manifest-id", inherited_manifest_id,
        "--conformance-report-id", conformance_report_id,
        "--decision-report-id", decision_report_id,
        "--policy-evaluation-report-id", policy_evaluation_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(inherited_out_dir),
        "--force",
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    return result.returncode


# ---------------------------------------------------------------------------
# Phase B step (e): build the runtime v0.4.3 records body from the
# hand-authored template by injecting the three runtime-bound fields.
# ---------------------------------------------------------------------------

def _build_runtime_records_body(
    *,
    template_obj: dict[str, Any],
    policy_evaluation_report_sha256_hex: str,
    generated_at: str,
) -> dict[str, Any]:
    """Inject the three v0.4.3 runtime-bound fields and serialize records body.

    Top-level injections:
      - policy_evaluation_report_sha256 (bare lowercase hex SHA-256 of
        subject [4] bytes).
      - generated_at (from --generated-at).

    Per-record injection:
      - lifecycle_fingerprint = SHA-256(canonical_json(record_without_fp)).
    """
    runtime = dict(template_obj)
    runtime["policy_evaluation_report_sha256"] = policy_evaluation_report_sha256_hex
    runtime["generated_at"] = generated_at

    raw_records = runtime.get("lifecycle_records")
    if not isinstance(raw_records, list):
        # Template structural defect; pass through to verifier as
        # gold_challenge_lifecycle_records_schema_invalid.
        return runtime

    runtime_records: list[dict[str, Any]] = []
    for record in raw_records:
        if not isinstance(record, dict):
            runtime_records.append(record)
            continue
        record_for_fp = {
            k: v for k, v in record.items() if k != "lifecycle_fingerprint"
        }
        fp = _sha256_hex(_canonical_json_bytes(record_for_fp))
        new_record = dict(record_for_fp)
        new_record["lifecycle_fingerprint"] = fp
        runtime_records.append(new_record)
    runtime["lifecycle_records"] = runtime_records
    return runtime


# ---------------------------------------------------------------------------
# Phase B step (f): derive subject [6] lifecycle report by projection over
# the runtime records body. The projection is deterministic and
# byte-re-derivable from the records body bytes plus the three source
# SHA-256 anchors.
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES = frozenset({"resolved_locally", "superseded", "withdrawn"})

_ALL_STATUSES_ORDERED = (
    "filed",
    "acknowledged",
    "under_review",
    "resolved_locally",
    "superseded",
    "withdrawn",
)


def _project_lifecycle_row(idx: int, record: dict[str, Any]) -> dict[str, Any]:
    """Project a single records-body record into the lifecycle report row.

    Per the lifecycle report schema, the row carries scalars plus the
    record's own `lifecycle_fingerprint` re-included verbatim (not
    recomputed at projection time).
    """
    events = record.get("events") if isinstance(record.get("events"), list) else []
    event_count = len(events)
    if event_count > 0 and isinstance(events[0], dict):
        first_event_id = events[0].get("event_id")
    else:
        first_event_id = None
    if event_count > 0 and isinstance(events[event_count - 1], dict):
        final_event_id = events[event_count - 1].get("event_id")
        final_event_ts = events[event_count - 1].get("event_timestamp")
    else:
        final_event_id = None
        final_event_ts = None
    current_status = record.get("current_status")
    is_terminal = current_status in _TERMINAL_STATUSES
    return {
        "row_id": f"lc_row_{idx + 1:02d}",
        "lifecycle_id": record.get("lifecycle_id"),
        "target_decision_id": record.get("target_decision_id"),
        "target_decision_row_id": record.get("target_decision_row_id"),
        "current_status": current_status,
        "is_terminal": is_terminal,
        "event_count": event_count,
        "first_event_id": first_event_id,
        "final_event_id": final_event_id,
        "final_event_timestamp": final_event_ts,
        "lifecycle_fingerprint": record.get("lifecycle_fingerprint"),
    }


def _derive_coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the fixed-shape coverage_summary rollup over lifecycle_rows[]."""
    open_count = 0
    terminal_count = 0
    event_total = 0
    status_count = {s: 0 for s in _ALL_STATUSES_ORDERED}
    for r in rows:
        ec = r.get("event_count")
        if isinstance(ec, int):
            event_total += ec
        st = r.get("current_status")
        if isinstance(st, str) and st in status_count:
            status_count[st] += 1
        if r.get("is_terminal") is True:
            terminal_count += 1
        else:
            open_count += 1
    return {
        "lifecycle_record_count": len(rows),
        "lifecycle_event_count": event_total,
        "open_lifecycle_count": open_count,
        "terminal_lifecycle_count": terminal_count,
        "status_value_count": status_count,
    }


def _derive_lifecycle_report(
    *,
    records_body: dict[str, Any],
    challenge_lifecycle_report_id: str,
    generated_at: str,
    source_records_sha256_hex: str,
    source_policy_evaluation_report_sha256_hex: str,
    source_decision_report_sha256_hex: str,
) -> dict[str, Any]:
    """Derive the v0.4.3 lifecycle report (subject [6]) by projection.

    The projection preserves records-body input order, attaches the
    three source SHA-256 anchors, computes the fixed-shape coverage
    rollup, and finally appends `report_fingerprint` as a SHA-256 over
    the canonical-JSON serialization of the body without the fingerprint
    field itself.
    """
    raw_records = records_body.get("lifecycle_records")
    if not isinstance(raw_records, list):
        raw_records = []
    rows = [
        _project_lifecycle_row(idx, r)
        for idx, r in enumerate(raw_records)
        if isinstance(r, dict)
    ]
    coverage = _derive_coverage_summary(rows)
    body = {
        "document_type": "proofrail.gold.challenge_lifecycle_report",
        "schema_version": "v0.1.0",
        "profile": "gold.challenge_lifecycle_lite.v0.4.3",
        "challenge_lifecycle_report_id": challenge_lifecycle_report_id,
        "lifecycle_record_set_id": records_body.get("lifecycle_record_set_id"),
        "package_id": records_body.get("package_id"),
        "governed_reliance_demo_id": records_body.get("governed_reliance_demo_id"),
        "policy_evaluation_report_id": records_body.get("policy_evaluation_report_ref"),
        "source_records_sha256": source_records_sha256_hex,
        "source_policy_evaluation_report_sha256": source_policy_evaluation_report_sha256_hex,
        "source_decision_report_sha256": source_decision_report_sha256_hex,
        "generated_at": generated_at,
        "lifecycle_rows": rows,
        "coverage_summary": coverage,
    }
    body["report_fingerprint"] = _sha256_hex(_canonical_json_bytes(body))
    return body


# ---------------------------------------------------------------------------
# Phase B step (g): build the 7-subject v0.4.3 manifest. Subject order is
# fixed by schema; runner does not enforce the 6-ID collision class (that
# is the verifier's job under the appropriate v0.4.3 binding reasons).
# ---------------------------------------------------------------------------

def _build_manifest(
    *,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    matrix_id: str,
    policy_evaluation_report_id: str,
    challenge_lifecycle_record_set_id: str,
    challenge_lifecycle_report_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    package_path: Path,
    conformance_path: Path,
    decision_path: Path,
    matrix_path: Path,
    evaluation_path: Path,
    records_path: Path,
    lifecycle_report_path: Path,
    package_sha256_hex: str,
    conformance_sha256_hex: str,
    decision_sha256_hex: str,
    matrix_sha256_hex: str,
    evaluation_sha256_hex: str,
    records_sha256_hex: str,
    lifecycle_report_sha256_hex: str,
) -> dict[str, Any]:
    return {
        "document_type": "proofrail.gold.challenge_lifecycle_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.challenge_lifecycle_lite.v0.4.3",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "conformance_report_id": conformance_report_id,
        "decision_report_id": decision_report_id,
        "matrix_id": matrix_id,
        "policy_evaluation_report_id": policy_evaluation_report_id,
        "challenge_lifecycle_record_set_id": challenge_lifecycle_record_set_id,
        "challenge_lifecycle_report_id": challenge_lifecycle_report_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "generated_at": generated_at,
        "subjects": [
            {
                "role": "governed_reliance_package",
                "path": PACKAGE_SUBJECT_PATH,
                "sha256": package_sha256_hex,
                "size_bytes": package_path.stat().st_size,
            },
            {
                "role": "conformance_report",
                "path": CONFORMANCE_SUBJECT_PATH,
                "sha256": conformance_sha256_hex,
                "size_bytes": conformance_path.stat().st_size,
            },
            {
                "role": "decision_report",
                "path": DECISION_SUBJECT_PATH,
                "sha256": decision_sha256_hex,
                "size_bytes": decision_path.stat().st_size,
            },
            {
                "role": "policy_evaluation_matrix",
                "path": MATRIX_SUBJECT_PATH,
                "sha256": matrix_sha256_hex,
                "size_bytes": matrix_path.stat().st_size,
            },
            {
                "role": "policy_evaluation_report",
                "path": EVALUATION_SUBJECT_PATH,
                "sha256": evaluation_sha256_hex,
                "size_bytes": evaluation_path.stat().st_size,
            },
            {
                "role": "challenge_lifecycle_records",
                "path": RECORDS_SUBJECT_PATH,
                "sha256": records_sha256_hex,
                "size_bytes": records_path.stat().st_size,
            },
            {
                "role": "challenge_lifecycle_report",
                "path": LIFECYCLE_REPORT_SUBJECT_PATH,
                "sha256": lifecycle_report_sha256_hex,
                "size_bytes": lifecycle_report_path.stat().st_size,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Helpers: atomic publish, staging cleanup, self-validate subprocess.
# ---------------------------------------------------------------------------

def _atomic_publish(staging: Path, dest: Path) -> None:
    os.replace(staging, dest)


def _remove_dir(d: Path) -> None:
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.4.3 verifier against the staged manifest.

    The v0.4.3 runner self-validates against the v0.4.3 verifier ONLY.
    Inherited verifier chains are reached transitively via the v0.4.3
    verifier's own subprocess delegation to the v0.4.2 verifier (which
    itself delegates to v0.4.1, then v0.4.0).
    """
    result = subprocess.run(
        [sys.executable, str(verifier_path), "--manifest", str(manifest_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    return result.returncode


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a ProofRail Gold v0.4.3 Challenge Lifecycle Lite package.",
    )
    parser.add_argument("--input-package", type=str, default=None,
                        help="Path to the v0.4.0-shaped governed-reliance package body JSON.")
    parser.add_argument("--matrix-input", type=str, default=None,
                        help="Path to the v0.4.2 hand-authored matrix template JSON.")
    parser.add_argument("--lifecycle-input", type=str, default=None,
                        help="Path to the v0.4.3 hand-authored challenge lifecycle records template JSON.")
    parser.add_argument("--manifest-id", type=str, required=True,
                        help="v0.4.3 manifest_id.")
    parser.add_argument("--conformance-report-id", type=str, required=True,
                        help="Passed through to the v0.4.2 runner for subject [1].")
    parser.add_argument("--decision-report-id", type=str, required=True,
                        help="Passed through to the v0.4.2 runner for subject [2].")
    parser.add_argument("--policy-evaluation-report-id", type=str, required=True,
                        help="Passed through to the v0.4.2 runner for subject [4].")
    parser.add_argument("--challenge-lifecycle-report-id", type=str, required=True,
                        help="v0.4.3 lifecycle report id (subject [6]).")
    parser.add_argument("--generated-at", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-validate", action="store_true")
    args = parser.parse_args(argv)

    # Phase A: preflight all three external inputs under the closed
    # 5-refusal vocabulary.
    input_package_path = _preflight_input_path(args.input_package, "--input-package")
    matrix_input_path = _preflight_input_path(args.matrix_input, "--matrix-input")
    lifecycle_input_path = _preflight_input_path(args.lifecycle_input, "--lifecycle-input")

    # Phase B begins.
    out_dir = Path(args.output_dir)
    if out_dir.exists() and not args.force:
        sys.stderr.write(
            f"refuse: output dir already exists; pass --force to overwrite: {out_dir}\n"
        )
        return 1
    if out_dir.exists() and args.force:
        shutil.rmtree(out_dir)

    pid = os.getpid()
    staging = out_dir.with_suffix(out_dir.suffix + f".staging.{pid}")
    inherited_dir = out_dir.with_suffix(out_dir.suffix + f".inherited.staging.{pid}")
    _remove_dir(staging)
    _remove_dir(inherited_dir)
    staging.mkdir(parents=True, exist_ok=False)

    try:
        # Phase B step (b): subprocess-delegate to v0.4.2 runner.
        inherited_manifest_id = f"{args.manifest_id}-inherited-v042"
        rc = _invoke_v042_runner(
            input_package=input_package_path,
            matrix_input=matrix_input_path,
            inherited_out_dir=inherited_dir,
            inherited_manifest_id=inherited_manifest_id,
            conformance_report_id=args.conformance_report_id,
            decision_report_id=args.decision_report_id,
            policy_evaluation_report_id=args.policy_evaluation_report_id,
            generated_at=args.generated_at,
        )
        if rc != 0:
            _remove_dir(staging)
            _remove_dir(inherited_dir)
            return rc

        # Read the inherited v0.4.2 manifest to extract its subject sha256
        # values. The inherited manifest itself is NOT a subject of the
        # v0.4.3 manifest; it is consumed here and discarded with the
        # inherited_dir at the end.
        inherited_manifest_path = inherited_dir / INHERITED_V042_MANIFEST_FILENAME
        try:
            inherited_manifest = json.loads(
                inherited_manifest_path.read_bytes().decode("utf-8")
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            sys.stderr.write(
                f"refuse: cannot read inherited v0.4.2 manifest at {inherited_manifest_path}: {e}\n"
            )
            _remove_dir(staging)
            _remove_dir(inherited_dir)
            return 1

        inherited_subjects = inherited_manifest.get("subjects") or []
        if not isinstance(inherited_subjects, list) or len(inherited_subjects) != 5:
            sys.stderr.write(
                "refuse: inherited v0.4.2 manifest does not declare exactly 5 subjects\n"
            )
            _remove_dir(staging)
            _remove_dir(inherited_dir)
            return 1

        # Pull inherited matrix_id (the v0.4.2 manifest carries it as a
        # top-level field; v0.4.3 uses the same value verbatim so that
        # subject [3]'s downstream binding rule passes).
        inherited_matrix_id = inherited_manifest.get("matrix_id")
        if not isinstance(inherited_matrix_id, str) or not inherited_matrix_id:
            sys.stderr.write(
                "refuse: inherited v0.4.2 manifest is missing matrix_id\n"
            )
            _remove_dir(staging)
            _remove_dir(inherited_dir)
            return 1
        inherited_package_id = inherited_manifest.get("package_id")
        inherited_demo_id = inherited_manifest.get("governed_reliance_demo_id")
        if not isinstance(inherited_package_id, str) or not isinstance(
            inherited_demo_id, str
        ):
            sys.stderr.write(
                "refuse: inherited v0.4.2 manifest is missing package_id or governed_reliance_demo_id\n"
            )
            _remove_dir(staging)
            _remove_dir(inherited_dir)
            return 1

        # Phase B step (d): byte-copy inherited subjects into v0.4.3 staging.
        inherited_paths = {
            PACKAGE_SUBJECT_PATH: inherited_dir / PACKAGE_SUBJECT_PATH,
            CONFORMANCE_SUBJECT_PATH: inherited_dir / CONFORMANCE_SUBJECT_PATH,
            DECISION_SUBJECT_PATH: inherited_dir / DECISION_SUBJECT_PATH,
            MATRIX_SUBJECT_PATH: inherited_dir / MATRIX_SUBJECT_PATH,
            EVALUATION_SUBJECT_PATH: inherited_dir / EVALUATION_SUBJECT_PATH,
        }
        inherited_bytes: dict[str, bytes] = {}
        for sub_name, src_path in inherited_paths.items():
            try:
                inherited_bytes[sub_name] = src_path.read_bytes()
            except OSError as e:
                sys.stderr.write(
                    f"refuse: cannot read inherited subject {sub_name} at {src_path}: {e}\n"
                )
                _remove_dir(staging)
                _remove_dir(inherited_dir)
                return 1
            (staging / sub_name).write_bytes(inherited_bytes[sub_name])

        package_sha256_hex = _sha256_hex(inherited_bytes[PACKAGE_SUBJECT_PATH])
        conformance_sha256_hex = _sha256_hex(inherited_bytes[CONFORMANCE_SUBJECT_PATH])
        decision_sha256_hex = _sha256_hex(inherited_bytes[DECISION_SUBJECT_PATH])
        matrix_sha256_hex = _sha256_hex(inherited_bytes[MATRIX_SUBJECT_PATH])
        evaluation_sha256_hex = _sha256_hex(inherited_bytes[EVALUATION_SUBJECT_PATH])

        # Phase B step (e): build the runtime v0.4.3 records body
        # (subject [5]) from the lifecycle template by injecting the
        # three runtime-bound fields.
        try:
            lifecycle_template = json.loads(
                lifecycle_input_path.read_bytes().decode("utf-8")
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            # Pre-flighted above; should not occur, but pass through as
            # template-shape defect for the verifier to surface as
            # gold_challenge_lifecycle_records_schema_invalid.
            lifecycle_template = {}
        if not isinstance(lifecycle_template, dict):
            lifecycle_template = {}

        records_body = _build_runtime_records_body(
            template_obj=lifecycle_template,
            policy_evaluation_report_sha256_hex=evaluation_sha256_hex,
            generated_at=args.generated_at,
        )
        records_bytes = _canonical_json_bytes(records_body)
        staged_records = staging / RECORDS_SUBJECT_PATH
        staged_records.write_bytes(records_bytes)
        records_sha256_hex = _sha256_hex(records_bytes)

        # Phase B step (f): derive subject [6] lifecycle report.
        lifecycle_report = _derive_lifecycle_report(
            records_body=records_body,
            challenge_lifecycle_report_id=args.challenge_lifecycle_report_id,
            generated_at=args.generated_at,
            source_records_sha256_hex=records_sha256_hex,
            source_policy_evaluation_report_sha256_hex=evaluation_sha256_hex,
            source_decision_report_sha256_hex=decision_sha256_hex,
        )
        lifecycle_report_bytes = _canonical_json_bytes(lifecycle_report)
        staged_lifecycle_report = staging / LIFECYCLE_REPORT_SUBJECT_PATH
        staged_lifecycle_report.write_bytes(lifecycle_report_bytes)
        lifecycle_report_sha256_hex = _sha256_hex(lifecycle_report_bytes)

        # Phase B step (g): build the 7-subject v0.4.3 manifest.
        # `challenge_lifecycle_record_set_id` is sourced from the records
        # body's hand-authored `lifecycle_record_set_id` (template-based
        # artifact convention, mirroring v0.4.2's matrix_id sourcing).
        record_set_id = records_body.get("lifecycle_record_set_id")
        if not isinstance(record_set_id, str) or not record_set_id:
            record_set_id = "gold-challenge-lifecycle-record-set-unknown"

        manifest_obj = _build_manifest(
            manifest_id=args.manifest_id,
            conformance_report_id=args.conformance_report_id,
            decision_report_id=args.decision_report_id,
            matrix_id=inherited_matrix_id,
            policy_evaluation_report_id=args.policy_evaluation_report_id,
            challenge_lifecycle_record_set_id=record_set_id,
            challenge_lifecycle_report_id=args.challenge_lifecycle_report_id,
            package_id=inherited_package_id,
            governed_reliance_demo_id=inherited_demo_id,
            generated_at=args.generated_at,
            package_path=staging / PACKAGE_SUBJECT_PATH,
            conformance_path=staging / CONFORMANCE_SUBJECT_PATH,
            decision_path=staging / DECISION_SUBJECT_PATH,
            matrix_path=staging / MATRIX_SUBJECT_PATH,
            evaluation_path=staging / EVALUATION_SUBJECT_PATH,
            records_path=staged_records,
            lifecycle_report_path=staged_lifecycle_report,
            package_sha256_hex=package_sha256_hex,
            conformance_sha256_hex=conformance_sha256_hex,
            decision_sha256_hex=decision_sha256_hex,
            matrix_sha256_hex=matrix_sha256_hex,
            evaluation_sha256_hex=evaluation_sha256_hex,
            records_sha256_hex=records_sha256_hex,
            lifecycle_report_sha256_hex=lifecycle_report_sha256_hex,
        )
        manifest_bytes = _canonical_json_bytes(manifest_obj)
        staged_manifest = staging / MANIFEST_FILENAME
        staged_manifest.write_bytes(manifest_bytes)

        # The inherited scratch dir is no longer needed; remove before
        # atomic publish so the inherited v0.4.2 manifest does not leak
        # into the v0.4.3 output.
        _remove_dir(inherited_dir)

        # Phase B step (h): optional self-validate against the v0.4.3
        # verifier. The v0.4.3 verifier itself will subprocess-delegate
        # to v0.4.2 (and on to v0.4.1, v0.4.0).
        if args.self_validate:
            rc = _self_validate(GOLD_V043_VERIFIER, staged_manifest)
            if rc != 0:
                _remove_dir(staging)
                return rc

        _atomic_publish(staging, out_dir)
    except Exception:
        _remove_dir(staging)
        _remove_dir(inherited_dir)
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
