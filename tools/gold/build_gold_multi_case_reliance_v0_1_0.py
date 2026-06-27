#!/usr/bin/env python3
"""Build a ProofRail Gold v0.4.5 Multi-Case Reliance Demo package.

The v0.4.5 runner composes a deterministic, hash-anchored local
multi-file package whose contents are exactly one v0.4.4 child
closure plus a v0.4.5-authored 2-subject wrapping manifest and a
v0.4.5-authored index body with five case entries.

Phases:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package, --matrix-input, and --lifecycle-input
      under the closed runner-only refusal set inherited verbatim
      from v0.4.0..v0.4.4; no sixth refusal is introduced.

  2.  Phase A.5: copy all three inputs by byte content into a
      disposable scratch bundle at /tmp/proofrail-v045-bundle-<pid>/.
      The v0.4.4 runner is invoked against the scratch copies ONLY.
      Tracked repo paths are NEVER forwarded to the v0.4.4 runner,
      so even if an inherited tool were destructive toward its
      input, tracked fixtures cannot be touched.

  3.  Phase B: build package.
      a. Resolves --output-dir. --force is permitted only when
         --output-dir matches the v0.4.5 scratch prefix
         (V045_SCRATCH_PREFIX = "/tmp/proofrail-v045-"); otherwise
         --force is refused. Without --force, an existing
         --output-dir is always refused.
      b. Stages under /tmp/proofrail-v045-staging-<pid>/; atomically
         publishes via os.replace() on success.
      c. Subprocess-invokes the co-located v0.4.4 runner EXACTLY ONCE
         into child-packages/v0.4.4/ to produce the single canonical
         v0.4.4 child closure. The v0.4.4 runner is invoked without
         --self-validate so the v0.4.5 verifier is the single entry
         point for chained verification (the v0.4.5 verifier in turn
         subprocess-invokes the v0.4.4 verifier on the same closure).
         No per-case generated matrix/lifecycle templates are
         produced; the v0.4.4 child closure is used as-is.
      d. Reads the v0.4.4 wrapping manifest, the v0.4.4 index body,
         the v0.4.0 governed-reliance package body, the v0.4.1
         decision-report body, the v0.4.2 evaluation-report body,
         and the v0.4.3 lifecycle-records body, all reached through
         the v0.4.4 child closure layout.
      e. Derives the v0.4.5 index body (subject [1]) by projecting
         the five cases in natural v0.4.0 order, computing the
         multi_case_index_fingerprint per the v0.4.5 body schema.
      f. Builds the 2-subject v0.4.5 wrapping manifest.
      g. When --self-validate is supplied, subprocess-invokes the
         v0.4.5 verifier against the staged wrapping manifest BEFORE
         the atomic move; on non-zero exit the entire staged package
         tree is removed (via _safe_rmtree, which refuses any path
         outside the v0.4.5 scratch prefix) and the verifier output
         is relayed verbatim.

  4.  Phase B' end: the scratch input bundle is always removed via
      _safe_rmtree.

A v0.4.5 package is a deterministic local hand-authored record. It
is NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold. It is a local
hash anchor over one v0.4.4 Gold Reliance Package Index child
closure plus a v0.4.5-authored multi-case projection index body.

Safe-rmtree discipline:

    _safe_rmtree(p) refuses to delete unless p.resolve() lives under
    /tmp AND has the v0.4.5 scratch marker string "proofrail-v045-"
    in its absolute path. This guarantees the runner cannot delete
    anything under tools/, fixtures/, schemas/, repo root, or any
    tracked path even if input invariants are violated.
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
# Runner-only refusal vocabulary (closed set of 5, identical to
# v0.4.0..v0.4.4). A sixth refusal is intentionally NOT introduced
# for verifier-relayed failures; those are surfaced as the verifier's
# own exit code and reason token, relayed verbatim.
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
# Canonical JSON serialization helpers.
#
#   _canonical_json_bytes:           used for FILE writes (with `\n`
#                                    suffix, matching v0.4.0..v0.4.4).
#   _canonical_json_bytes_no_newline: used ONLY for the v0.4.5
#                                    `multi_case_index_fingerprint`
#                                    computation, per the v0.4.5 body
#                                    schema (json.dumps + utf-8, no
#                                    trailing newline).
# ---------------------------------------------------------------------------

def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return (s + "\n").encode("utf-8")


def _canonical_json_bytes_no_newline(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.($|/)")


def _has_traversal(p: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(p))


# ---------------------------------------------------------------------------
# v0.4.5 scratch prefix discipline + safe-rmtree.
#
# All filesystem deletions performed by this runner must go through
# _safe_rmtree(). _safe_rmtree() resolves the target path (without
# requiring existence), then refuses unless:
#
#   1. The resolved absolute path begins with "/tmp/" (or
#      "/private/tmp/" on macOS where /tmp is a symlink), and
#   2. The substring "proofrail-v045-" appears in the resolved
#      absolute path.
#
# Any rmtree request that fails either check is silently dropped
# with a structured stderr line; the runner does not return non-zero
# solely because cleanup was refused.
# ---------------------------------------------------------------------------

V045_SCRATCH_PREFIX = "/tmp/proofrail-v045-"
_V045_SCRATCH_MARKER = "proofrail-v045-"

_TMP_ROOTED_PREFIXES = ("/tmp/", "/private/tmp/")


def _safe_rmtree(p: Path) -> None:
    """Remove a directory tree, but only when path is /tmp-scratch v0.4.5-owned."""
    try:
        rp = Path(os.path.realpath(str(p)))
    except OSError as e:
        sys.stderr.write(
            f"safe-rmtree: refused (realpath failure on {p!s}): {type(e).__name__}: {e}\n"
        )
        return
    s = str(rp)
    if not any(s.startswith(prefix) for prefix in _TMP_ROOTED_PREFIXES):
        sys.stderr.write(
            f"safe-rmtree: refused (resolved path is not under /tmp/ or /private/tmp/): {s!r}\n"
        )
        return
    if _V045_SCRATCH_MARKER not in s:
        sys.stderr.write(
            f"safe-rmtree: refused (resolved path lacks v0.4.5 scratch marker {_V045_SCRATCH_MARKER!r}): {s!r}\n"
        )
        return
    if len(rp.parts) < 3:
        sys.stderr.write(
            f"safe-rmtree: refused (resolved path is too shallow): {s!r}\n"
        )
        return
    if not rp.exists():
        return
    shutil.rmtree(rp, ignore_errors=True)


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
# Phase A.5: byte-copy preflighted inputs into a disposable scratch
# bundle under /tmp/proofrail-v045-bundle-<pid>/. The v0.4.4 runner
# is invoked against the scratch copies; the original tracked fixture
# paths are NEVER forwarded into any subprocess.
# ---------------------------------------------------------------------------

def _make_input_bundle(
    *,
    input_package_path: Path,
    matrix_input_path: Path,
    lifecycle_input_path: Path,
) -> tuple[Path, Path, Path, Path]:
    """Copy preflighted inputs into a /tmp scratch bundle. Returns
    (bundle_root, copy_input_package, copy_matrix, copy_lifecycle)."""
    pid = os.getpid()
    bundle_root = Path(f"{V045_SCRATCH_PREFIX}bundle-{pid}")
    _safe_rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=False)

    def _copy(src: Path, basename: str) -> Path:
        dest = bundle_root / basename
        dest.write_bytes(src.read_bytes())
        return dest

    cp_input = _copy(input_package_path, "input-package.json")
    cp_matrix = _copy(matrix_input_path, "matrix-input.json")
    cp_lifecycle = _copy(lifecycle_input_path, "lifecycle-input.json")
    return bundle_root, cp_input, cp_matrix, cp_lifecycle


# ---------------------------------------------------------------------------
# Child closure layout. Subject [0] is the v0.4.4 wrapping manifest
# under `child-packages/v0.4.4/`. Subject [1] is the v0.4.5 index
# body at the package root. Files underneath `child-packages/v0.4.4/`
# (including the v0.4.4 index body and the v0.4.4 child closures for
# v0.4.0..v0.4.3) are NOT v0.4.5 subjects but are read by the v0.4.5
# runner to derive the v0.4.5 index body's case entries.
# ---------------------------------------------------------------------------

V044_CHILD_DIR = "child-packages/v0.4.4"
V044_MANIFEST_FILENAME = "gold-reliance-package-index-manifest.json"
V044_INDEX_BODY_FILENAME = "gold-reliance-package-index.json"

# Paths inside the v0.4.4 child closure (the v0.4.4 runner produces
# these alongside its wrapping manifest).
V044_V040_REL = "child-packages/v0.4.0/governed-reliance-scenarios.json"
V044_V041_REL = "child-packages/v0.4.1/gold-governed-reliance-decision-report.json"
V044_V042_REL = "child-packages/v0.4.2/gold-policy-evaluation-report.json"
V044_V043_REL = "child-packages/v0.4.3/challenge-lifecycle-records.json"

V045_SUBJECT_PATH_V044_MANIFEST = f"{V044_CHILD_DIR}/{V044_MANIFEST_FILENAME}"
V045_INDEX_BODY_FILENAME = "gold-multi-case-reliance-index.json"
V045_MANIFEST_FILENAME = "gold-multi-case-reliance-package-manifest.json"

V045_DECISION_REPORT_REF = (
    f"{V044_CHILD_DIR}/child-packages/v0.4.1/gold-governed-reliance-decision-report.json"
)

V045_SUBJECT_ROLE_V044_MANIFEST = "gold_reliance_package_index_manifest"
V045_SUBJECT_ROLE_INDEX = "gold_multi_case_reliance_index"


# ---------------------------------------------------------------------------
# Co-located v0.4.4 runner and v0.4.5 verifier paths.
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent

GOLD_V044_RUNNER = _TOOLS_DIR / "build_gold_reliance_package_index_v0_1_0.py"
GOLD_V045_VERIFIER = _TOOLS_DIR / "verify_gold_multi_case_reliance_v0_1_0.py"


def _relay_runner_output(result: subprocess.CompletedProcess) -> None:
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)


def _invoke_v044_runner(
    *,
    bundle_root: Path,
    input_package: Path,
    matrix_input: Path,
    lifecycle_input: Path,
    out_dir: Path,
    v044_manifest_id: str,
    v044_conformance_report_id: str,
    v044_decision_report_id: str,
    v044_policy_evaluation_report_id: str,
    v044_challenge_lifecycle_report_id: str,
    v044_gold_reliance_package_index_id: str,
    generated_at: str,
) -> int:
    # The v0.4.4 runner's preflight refuses absolute paths. Bare
    # filenames relative to bundle_root (set as cwd) are used. The
    # bundle_root is a v0.4.5-prefixed /tmp path; the v0.4.4 runner
    # in turn copies inputs into its own v0.4.4 scratch bundle. The
    # v0.4.4 runner's --output-dir must satisfy the v0.4.4 scratch
    # prefix for --force, but here we pass a path inside the v0.4.5
    # staging tree that does NOT yet exist, so --force is never
    # required (the v0.4.4 runner only requires --force when its
    # --output-dir already exists). Pristine staging.
    cmd = [
        sys.executable,
        str(GOLD_V044_RUNNER),
        "--input-package", input_package.name,
        "--matrix-input", matrix_input.name,
        "--lifecycle-input", lifecycle_input.name,
        "--manifest-id", v044_manifest_id,
        "--conformance-report-id", v044_conformance_report_id,
        "--decision-report-id", v044_decision_report_id,
        "--policy-evaluation-report-id", v044_policy_evaluation_report_id,
        "--challenge-lifecycle-report-id", v044_challenge_lifecycle_report_id,
        "--gold-reliance-package-index-id", v044_gold_reliance_package_index_id,
        "--generated-at", generated_at,
        "--output-dir", str(out_dir),
    ]
    result = subprocess.run(
        cmd, cwd=str(bundle_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _relay_runner_output(result)
    return result.returncode


# ---------------------------------------------------------------------------
# Phase B step (d): read v0.4.4 closure files for v0.4.5 index body
# derivation. Structural defects in v0.4.4 closure files are NOT
# re-emitted by the v0.4.5 runner; they fall through to the v0.4.5
# verifier, which subprocess-invokes the v0.4.4 verifier and relays
# its reason verbatim.
# ---------------------------------------------------------------------------

def _read_json_or_empty(path: Path) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError:
        return b"", {}
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw, {}
    if not isinstance(obj, dict):
        return raw, {}
    return raw, obj


def _list_or_empty(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


# ---------------------------------------------------------------------------
# Phase B step (e): derive the v0.4.5 index body cases[].
#
# Per the v0.4.5 body schema, cases[] is exactly 5 entries in
# natural v0.4.0 order. Each entry projects:
#   - case_slug   <- v0.4.0 governed_decisions[i].scenario_type
#   - case_index  == i
#   - governed_decision_id <- v0.4.0 governed_decisions[i].decision_id
#   - outcome     <- v0.4.0 governed_decisions[i].decision_status
#   - decision_row_id <- v0.4.1 decision_rows[] join on decision_id
#   - matrix_row_id, evaluation_row_id
#                   <- v0.4.2 evaluation_rows[] join on decision_id
#                      (matrix_row_id JOIN via evaluation_rows[], NOT
#                       direct matrix_rows[] lookup)
#   - lifecycle_record_id, lifecycle_record_fingerprint
#                   <- v0.4.3 lifecycle_records[] join on
#                      target_decision_id; paired-null when no match
# ---------------------------------------------------------------------------

def _build_cases(
    *,
    case_id_prefix: str,
    v040_body: dict[str, Any],
    v041_body: dict[str, Any],
    v042_body: dict[str, Any],
    v043_body: dict[str, Any],
) -> list[dict[str, Any]]:
    governed_decisions = _list_or_empty(v040_body.get("governed_decisions"))
    decision_rows = _list_or_empty(v041_body.get("decision_rows"))
    evaluation_rows = _list_or_empty(v042_body.get("evaluation_rows"))
    lifecycle_records = _list_or_empty(v043_body.get("lifecycle_records"))

    drow_by_did = {
        r.get("decision_id"): r
        for r in decision_rows
        if isinstance(r, dict)
    }
    erow_by_did = {
        r.get("decision_id"): r
        for r in evaluation_rows
        if isinstance(r, dict)
    }
    lrec_by_did = {
        r.get("target_decision_id"): r
        for r in lifecycle_records
        if isinstance(r, dict)
    }

    cases: list[dict[str, Any]] = []
    for idx, gd in enumerate(governed_decisions):
        if not isinstance(gd, dict):
            gd = {}
        did = gd.get("decision_id") if isinstance(gd.get("decision_id"), str) else ""
        scenario_type = gd.get("scenario_type") if isinstance(gd.get("scenario_type"), str) else ""
        decision_status = gd.get("decision_status") if isinstance(gd.get("decision_status"), str) else ""

        drow = drow_by_did.get(did, {}) if isinstance(drow_by_did.get(did), dict) else {}
        decision_row_id = drow.get("row_id") if isinstance(drow.get("row_id"), str) else ""

        erow = erow_by_did.get(did, {}) if isinstance(erow_by_did.get(did), dict) else {}
        evaluation_row_id = erow.get("evaluation_row_id") if isinstance(erow.get("evaluation_row_id"), str) else None
        matrix_row_id = erow.get("matrix_row_id") if isinstance(erow.get("matrix_row_id"), str) else None
        # If the entire erow is missing, both stay None (covered by R60
        # if the v0.4.2 body is well-formed; otherwise inherited
        # verifier surfaces the v0.4.2-side defect).
        if not erow:
            evaluation_row_id = None
            matrix_row_id = None

        lrec = lrec_by_did.get(did)
        if isinstance(lrec, dict):
            lifecycle_record_id = lrec.get("lifecycle_id") if isinstance(lrec.get("lifecycle_id"), str) else None
            lifecycle_record_fingerprint = (
                lrec.get("lifecycle_fingerprint")
                if isinstance(lrec.get("lifecycle_fingerprint"), str)
                else None
            )
            # Paired-null: if either is null, force both null.
            if lifecycle_record_id is None or lifecycle_record_fingerprint is None:
                lifecycle_record_id = None
                lifecycle_record_fingerprint = None
        else:
            lifecycle_record_id = None
            lifecycle_record_fingerprint = None

        case_id = f"{case_id_prefix}-{idx + 1:03d}"
        cases.append({
            "case_id": case_id,
            "case_slug": scenario_type,
            "case_index": idx,
            "governed_decision_id": did,
            "decision_row_id": decision_row_id,
            "matrix_row_id": matrix_row_id,
            "evaluation_row_id": evaluation_row_id,
            "lifecycle_record_id": lifecycle_record_id,
            "lifecycle_record_fingerprint": lifecycle_record_fingerprint,
            "outcome": decision_status,
        })
    return cases


def _build_index_body(
    *,
    gold_multi_case_reliance_index_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    gold_reliance_package_index_sha256: str,
    decision_report_sha256: str,
    relying_party: Any,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    body_without_fp = {
        "document_type": "proofrail.gold.multi_case_reliance_index",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.multi_case_reliance.v0.4.5",
        "hash_algorithm": "sha256",
        "gold_multi_case_reliance_index_id": gold_multi_case_reliance_index_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "gold_reliance_package_index_ref": V045_SUBJECT_PATH_V044_MANIFEST,
        "gold_reliance_package_index_sha256": gold_reliance_package_index_sha256,
        "decision_report_ref": V045_DECISION_REPORT_REF,
        "decision_report_sha256": decision_report_sha256,
        "generated_at": generated_at,
        "relying_party": relying_party,
        "cases": cases,
    }
    multi_case_index_fingerprint = _sha256_hex(
        _canonical_json_bytes_no_newline(body_without_fp)
    )
    body = dict(body_without_fp)
    body["multi_case_index_fingerprint"] = multi_case_index_fingerprint
    return body


# ---------------------------------------------------------------------------
# Phase B step (f): build the 2-subject v0.4.5 wrapping manifest.
# ---------------------------------------------------------------------------

def _build_wrapping_manifest(
    *,
    manifest_id: str,
    gold_multi_case_reliance_index_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    v044_manifest_sha: str,
    v044_manifest_size: int,
    index_body_sha: str,
    index_body_size: int,
) -> dict[str, Any]:
    return {
        "document_type": "proofrail.gold.multi_case_reliance_package_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.multi_case_reliance.v0.4.5",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "gold_multi_case_reliance_index_id": gold_multi_case_reliance_index_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "gold_reliance_package_index_ref": V045_SUBJECT_PATH_V044_MANIFEST,
        "decision_report_ref": V045_DECISION_REPORT_REF,
        "generated_at": generated_at,
        "subjects": [
            {
                "role": V045_SUBJECT_ROLE_V044_MANIFEST,
                "path": V045_SUBJECT_PATH_V044_MANIFEST,
                "sha256": v044_manifest_sha,
                "size_bytes": v044_manifest_size,
            },
            {
                "role": V045_SUBJECT_ROLE_INDEX,
                "path": V045_INDEX_BODY_FILENAME,
                "sha256": index_body_sha,
                "size_bytes": index_body_size,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Atomic publish + self-validate subprocess.
# ---------------------------------------------------------------------------

def _atomic_publish(staging: Path, dest: Path) -> None:
    os.replace(staging, dest)


def _self_validate(verifier_path: Path, manifest_path: Path) -> int:
    """Subprocess-invoke the v0.4.5 verifier against the staged manifest.

    The v0.4.5 runner self-validates against the v0.4.5 verifier ONLY.
    The inherited v0.4.4 chain (and transitively v0.4.0..v0.4.3) is
    reached via the v0.4.5 verifier's own subprocess delegation to the
    v0.4.4 verifier on the `child-packages/v0.4.4/` wrapping-manifest
    path.
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
# Output-dir overwrite guard.
# ---------------------------------------------------------------------------

def _output_dir_is_under_scratch_prefix(out_dir: Path) -> bool:
    s = str(Path(os.path.realpath(str(out_dir))))
    return any(
        s.startswith(prefix + "proofrail-v045-")
        for prefix in _TMP_ROOTED_PREFIXES
    )


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a ProofRail Gold v0.4.5 Multi-Case Reliance Demo package.",
    )
    parser.add_argument("--input-package", type=str, default=None,
                        help="Path to the v0.4.0 governed-reliance package body JSON.")
    parser.add_argument("--matrix-input", type=str, default=None,
                        help="Path to the v0.4.2 hand-authored matrix template JSON.")
    parser.add_argument("--lifecycle-input", type=str, default=None,
                        help="Path to the v0.4.3 hand-authored challenge lifecycle records template JSON.")
    parser.add_argument("--manifest-id", type=str, required=True,
                        help="v0.4.5 wrapping manifest_id (must be distinct from any v0.4.4-child identifier).")
    parser.add_argument("--gold-multi-case-reliance-index-id", type=str, required=True,
                        help="v0.4.5-owned index identifier; cross-anchored to the v0.4.5 index body.")
    parser.add_argument("--package-id", type=str, required=True,
                        help="v0.4.5-owned package_id (must be distinct from any v0.4.4-child identifier).")
    parser.add_argument("--governed-reliance-demo-id", type=str, required=True,
                        help="v0.4.5-owned governed_reliance_demo_id (must be distinct from any v0.4.4-child identifier).")
    parser.add_argument("--v044-manifest-id", type=str, required=True,
                        help="v0.4.4 wrapping manifest_id (forwarded to the v0.4.4 runner).")
    parser.add_argument("--v044-conformance-report-id", type=str, required=True,
                        help="Forwarded to the v0.4.4 runner.")
    parser.add_argument("--v044-decision-report-id", type=str, required=True,
                        help="Forwarded to the v0.4.4 runner.")
    parser.add_argument("--v044-policy-evaluation-report-id", type=str, required=True,
                        help="Forwarded to the v0.4.4 runner.")
    parser.add_argument("--v044-challenge-lifecycle-report-id", type=str, required=True,
                        help="Forwarded to the v0.4.4 runner.")
    parser.add_argument("--v044-gold-reliance-package-index-id", type=str, required=True,
                        help="Forwarded to the v0.4.4 runner; v0.4.4-owned collision-class member.")
    parser.add_argument("--case-id-prefix", type=str, default="case",
                        help="Prefix for synthesized case_id values (default 'case'; produces case-001..case-005).")
    parser.add_argument("--generated-at", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-validate", action="store_true")
    args = parser.parse_args(argv)

    # Phase A: preflight all three external inputs under the closed
    # 5-refusal vocabulary. No sixth refusal is introduced.
    input_package_path = _preflight_input_path(args.input_package, "--input-package")
    matrix_input_path = _preflight_input_path(args.matrix_input, "--matrix-input")
    lifecycle_input_path = _preflight_input_path(args.lifecycle_input, "--lifecycle-input")

    # Phase A.5: copy preflighted inputs into a /tmp scratch bundle.
    # The v0.4.4 runner is invoked against the scratch copies only.
    bundle_root, scratch_input, scratch_matrix, scratch_lifecycle = _make_input_bundle(
        input_package_path=input_package_path,
        matrix_input_path=matrix_input_path,
        lifecycle_input_path=lifecycle_input_path,
    )

    try:
        # Phase B begins.
        out_dir = Path(args.output_dir)
        if out_dir.exists() and not args.force:
            sys.stderr.write(
                f"refuse: output dir already exists; pass --force to overwrite: {out_dir}\n"
            )
            return 1
        if out_dir.exists() and args.force:
            if not _output_dir_is_under_scratch_prefix(out_dir):
                sys.stderr.write(
                    "refuse: --force is permitted only when --output-dir is under "
                    f"{V045_SCRATCH_PREFIX!r}: {out_dir}\n"
                )
                return 1
            _safe_rmtree(out_dir)

        pid = os.getpid()
        staging = Path(f"{V045_SCRATCH_PREFIX}staging-{pid}")
        _safe_rmtree(staging)
        staging.mkdir(parents=True, exist_ok=False)

        try:
            # Phase B step (c): subprocess-invoke the v0.4.4 runner
            # EXACTLY ONCE into child-packages/v0.4.4/. The v0.4.4
            # runner publishes its own staging tree via os.replace()
            # into the requested --output-dir; os.replace() requires
            # the destination's parent directory to already exist,
            # so pre-create child-packages/ here.
            v044_out = staging / V044_CHILD_DIR
            v044_out.parent.mkdir(parents=True, exist_ok=False)

            rc = _invoke_v044_runner(
                bundle_root=bundle_root,
                input_package=scratch_input,
                matrix_input=scratch_matrix,
                lifecycle_input=scratch_lifecycle,
                out_dir=v044_out,
                v044_manifest_id=args.v044_manifest_id,
                v044_conformance_report_id=args.v044_conformance_report_id,
                v044_decision_report_id=args.v044_decision_report_id,
                v044_policy_evaluation_report_id=args.v044_policy_evaluation_report_id,
                v044_challenge_lifecycle_report_id=args.v044_challenge_lifecycle_report_id,
                v044_gold_reliance_package_index_id=args.v044_gold_reliance_package_index_id,
                generated_at=args.generated_at,
            )
            if rc != 0:
                _safe_rmtree(staging)
                return rc

            # Phase B step (d): read v0.4.4 wrapping manifest +
            # closure body files for v0.4.5 index body derivation.
            v044_manifest_path = staging / V045_SUBJECT_PATH_V044_MANIFEST
            v044_index_body_path = staging / V044_CHILD_DIR / V044_INDEX_BODY_FILENAME
            v040_path = staging / V044_CHILD_DIR / V044_V040_REL
            v041_path = staging / V044_CHILD_DIR / V044_V041_REL
            v042_path = staging / V044_CHILD_DIR / V044_V042_REL
            v043_path = staging / V044_CHILD_DIR / V044_V043_REL

            v044_manifest_bytes, _v044_manifest_obj = _read_json_or_empty(v044_manifest_path)
            v044_index_body_bytes, _v044_index_body_obj = _read_json_or_empty(v044_index_body_path)
            _v040_bytes, v040_body = _read_json_or_empty(v040_path)
            _v041_bytes, v041_body = _read_json_or_empty(v041_path)
            _v042_bytes, v042_body = _read_json_or_empty(v042_path)
            _v043_bytes, v043_body = _read_json_or_empty(v043_path)

            v044_manifest_sha = _sha256_hex(v044_manifest_bytes)
            v044_manifest_size = len(v044_manifest_bytes)
            v044_index_body_sha = _sha256_hex(v044_index_body_bytes)
            v041_decision_report_sha = _sha256_hex(_v041_bytes)

            relying_party = v040_body.get("relying_party")
            # On structural defects in the v0.4.0 body, falsey
            # relying_party falls through to the v0.4.5 verifier R57
            # (relying_party shape) and/or R58 (cross-anchor mismatch);
            # the runner does not synthesize a sixth refusal.

            # Phase B step (e): derive v0.4.5 index body and write it.
            cases = _build_cases(
                case_id_prefix=args.case_id_prefix,
                v040_body=v040_body,
                v041_body=v041_body,
                v042_body=v042_body,
                v043_body=v043_body,
            )
            index_body = _build_index_body(
                gold_multi_case_reliance_index_id=args.gold_multi_case_reliance_index_id,
                package_id=args.package_id,
                governed_reliance_demo_id=args.governed_reliance_demo_id,
                generated_at=args.generated_at,
                gold_reliance_package_index_sha256=v044_index_body_sha,
                decision_report_sha256=v041_decision_report_sha,
                relying_party=relying_party,
                cases=cases,
            )
            index_body_bytes = _canonical_json_bytes(index_body)
            staged_index_body = staging / V045_INDEX_BODY_FILENAME
            staged_index_body.write_bytes(index_body_bytes)
            index_body_sha = _sha256_hex(index_body_bytes)
            index_body_size = len(index_body_bytes)

            # Phase B step (f): build the v0.4.5 wrapping manifest
            # and write it.
            wrapping_manifest = _build_wrapping_manifest(
                manifest_id=args.manifest_id,
                gold_multi_case_reliance_index_id=args.gold_multi_case_reliance_index_id,
                package_id=args.package_id,
                governed_reliance_demo_id=args.governed_reliance_demo_id,
                generated_at=args.generated_at,
                v044_manifest_sha=v044_manifest_sha,
                v044_manifest_size=v044_manifest_size,
                index_body_sha=index_body_sha,
                index_body_size=index_body_size,
            )
            wrapping_manifest_bytes = _canonical_json_bytes(wrapping_manifest)
            staged_manifest = staging / V045_MANIFEST_FILENAME
            staged_manifest.write_bytes(wrapping_manifest_bytes)

            # Phase B step (g): optional self-validate against the
            # v0.4.5 verifier. The v0.4.5 verifier itself subprocess-
            # delegates to the v0.4.4 verifier on the v0.4.4 child
            # wrapping-manifest path.
            if args.self_validate:
                rc = _self_validate(GOLD_V045_VERIFIER, staged_manifest)
                if rc != 0:
                    _safe_rmtree(staging)
                    return rc

            _atomic_publish(staging, out_dir)
        except Exception:
            _safe_rmtree(staging)
            raise
    finally:
        # Always clean up the scratch input bundle.
        _safe_rmtree(bundle_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
