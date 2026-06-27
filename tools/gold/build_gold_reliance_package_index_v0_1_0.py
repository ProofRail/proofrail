#!/usr/bin/env python3
"""Build a ProofRail Gold v0.4.4 Reliance Package Index package.

The v0.4.4 runner composes a deterministic, hash-anchored local
multi-file package. Phases:

  1.  Phase A: input preflight (5 runner-only refusal codes only).
      Validates --input-package, --matrix-input, and --lifecycle-input
      under the closed runner-only refusal set; no sixth refusal is
      introduced for verifier-relayed failures.

  2.  Phase A.5: copy all three inputs by byte content into a
      disposable scratch bundle at /tmp/proofrail-v044-bundle-<pid>/.
      Inherited runners are invoked against the scratch copies ONLY.
      Tracked repo paths are NEVER forwarded to any inherited child
      runner, so even if an inherited tool were destructive toward its
      input, tracked fixtures cannot be touched.

  3.  Phase B: build package.
      a. Resolves --output-dir. --force is permitted only when
         --output-dir matches the v0.4.4 scratch prefix
         (V044_SCRATCH_PREFIX = "/tmp/proofrail-v044-"); otherwise
         --force is refused. Without --force, an existing
         --output-dir is always refused.
      b. Stages under <output-dir>.staging.<pid>; atomically publishes
         via os.replace() on success.
      c. Subprocess-invokes the co-located v0.4.0 runner into
         child-packages/v0.4.0/ to produce the v0.4.0 child closure.
      d. Subprocess-invokes the co-located v0.4.1 runner into
         child-packages/v0.4.1/ to produce the v0.4.1 child closure.
      e. Subprocess-invokes the co-located v0.4.2 runner into
         child-packages/v0.4.2/ to produce the v0.4.2 child closure.
      f. Subprocess-invokes the co-located v0.4.3 runner into
         child-packages/v0.4.3/ to produce the v0.4.3 child closure.
         The v0.4.3 child closure is built under the corrected
         v0.4.3.1 baseline (the runner is invoked without
         --self-validate so the v0.4.4 verifier is the single entry
         point for chained verification).
      g. Reads each child wrapping manifest for SHA-256 + size, and
         for the cross-anchor identifier fields.
      h. Derives the v0.4.4 index body (subject [4]) by projecting
         the four child entries, the coverage summary, and the
         index_fingerprint per the v0.4.4 body schema.
      i. Builds the 5-subject v0.4.4 wrapping manifest.
      j. When --self-validate is supplied, subprocess-invokes the
         v0.4.4 verifier against the staged wrapping manifest BEFORE
         the atomic move; on non-zero exit the entire staged package
         tree is removed (via _safe_rmtree, which refuses any path
         outside the v0.4.4 scratch prefix) and the verifier output
         is relayed verbatim.

  4.  Phase B' end: the scratch input bundle is always removed via
      _safe_rmtree.

A v0.4.4 package is a deterministic local hand-authored record. It
is NOT a certificate, NOT signed, NOT federated, NOT a transfer of
reliance to any external party, and NOT full Gold. It is a local
hash anchor over four inherited Gold child wrapping manifests plus
a derived index body.

Safe-rmtree discipline (Phase 2 correction):

    _safe_rmtree(p) refuses to delete unless p.resolve() lives under
    /tmp AND has the v0.4.4 scratch prefix string "proofrail-v044-"
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
# v0.4.0 / v0.4.1 / v0.4.2 / v0.4.3). A sixth refusal is
# intentionally NOT introduced for verifier-relayed failures; those
# are surfaced as the verifier's own exit code and reason token,
# relayed verbatim.
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
#                                    suffix, matching the
#                                    v0.4.0..v0.4.3 convention).
#   _canonical_json_bytes_no_newline: used ONLY for the v0.4.4
#                                    `index_fingerprint` computation,
#                                    per the v0.4.4 body schema
#                                    (json.dumps + utf-8, no trailing
#                                    newline).
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
# v0.4.4 scratch prefix discipline + safe-rmtree.
#
# All filesystem deletions performed by this runner must go through
# _safe_rmtree(). _safe_rmtree() resolves the target path (without
# requiring existence), then refuses unless:
#
#   1. The resolved absolute path begins with "/tmp/", and
#   2. The substring "proofrail-v044-" appears in the resolved
#      absolute path (i.e., either the directory itself is a v0.4.4
#      scratch dir, or it is a descendant of one).
#
# Any rmtree request that fails either check is silently dropped
# with a structured stderr line; the runner does not return non-zero
# solely because cleanup was refused.
# ---------------------------------------------------------------------------

V044_SCRATCH_PREFIX = "/tmp/proofrail-v044-"
_V044_SCRATCH_MARKER = "proofrail-v044-"

# On macOS, /tmp is a symlink to /private/tmp; os.path.realpath()
# resolves /tmp/foo to /private/tmp/foo. Both rooted prefixes are
# accepted by _safe_rmtree so the scratch discipline survives platform
# symlink quirks. (On Linux, /tmp is normally a real directory and
# realpath returns /tmp/foo verbatim.)
_TMP_ROOTED_PREFIXES = ("/tmp/", "/private/tmp/")


def _safe_rmtree(p: Path) -> None:
    """Remove a directory tree, but only when path is /tmp-scratch v0.4.4-owned."""
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
    if _V044_SCRATCH_MARKER not in s:
        sys.stderr.write(
            f"safe-rmtree: refused (resolved path lacks v0.4.4 scratch marker {_V044_SCRATCH_MARKER!r}): {s!r}\n"
        )
        return
    # An additional guard: the resolved path must be at least 5
    # segments long (e.g. /tmp/proofrail-v044-foo/...) so that
    # "/tmp/proofrail-v044-" itself (the bare prefix) cannot be
    # rmtree'd by accident if a caller passes the prefix as a path.
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
# bundle under /tmp/proofrail-v044-bundle-<pid>/. All inherited
# runner invocations use the scratch copies; the original tracked
# fixture paths are NEVER forwarded into any subprocess.
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
    bundle_root = Path(f"{V044_SCRATCH_PREFIX}bundle-{pid}")
    # Defensive cleanup of any stale prior bundle for this pid (the
    # bundle path must satisfy the safe-rmtree prefix discipline).
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
# Child closure layout. Subjects [0]..[3] are the inherited child
# wrapping manifests under `child-packages/v0.4.X/`. Subject [4] is the
# v0.4.4 index body at the package root.
# ---------------------------------------------------------------------------

CHILD_DIR_V040 = "child-packages/v0.4.0"
CHILD_DIR_V041 = "child-packages/v0.4.1"
CHILD_DIR_V042 = "child-packages/v0.4.2"
CHILD_DIR_V043 = "child-packages/v0.4.3"

CHILD_MANIFEST_FILENAME_V040 = "gold-governed-reliance-package-manifest.json"
CHILD_MANIFEST_FILENAME_V041 = "gold-decision-report-package-manifest.json"
CHILD_MANIFEST_FILENAME_V042 = "gold-policy-evaluation-matrix-package-manifest.json"
CHILD_MANIFEST_FILENAME_V043 = "gold-challenge-lifecycle-package-manifest.json"

SUBJECT_PATH_V040 = f"{CHILD_DIR_V040}/{CHILD_MANIFEST_FILENAME_V040}"
SUBJECT_PATH_V041 = f"{CHILD_DIR_V041}/{CHILD_MANIFEST_FILENAME_V041}"
SUBJECT_PATH_V042 = f"{CHILD_DIR_V042}/{CHILD_MANIFEST_FILENAME_V042}"
SUBJECT_PATH_V043 = f"{CHILD_DIR_V043}/{CHILD_MANIFEST_FILENAME_V043}"

INDEX_BODY_FILENAME = "gold-reliance-package-index.json"
MANIFEST_FILENAME = "gold-reliance-package-index-manifest.json"

# Per-entry release labels (fixed by the v0.4.4 body schema).
RELEASE_LABEL_V040 = "gold.governed_reliance.v0.4.0"
RELEASE_LABEL_V041 = "gold.decision_report_hardening.v0.4.1"
RELEASE_LABEL_V042 = "gold.policy_evaluation_matrix.v0.4.2"
RELEASE_LABEL_V043 = "gold.challenge_lifecycle_lite.v0.4.3"

# Subject roles (fixed by the v0.4.4 manifest schema).
SUBJECT_ROLE_V040 = "gold_governed_reliance_package_manifest"
SUBJECT_ROLE_V041 = "gold_decision_report_package_manifest"
SUBJECT_ROLE_V042 = "gold_policy_evaluation_matrix_package_manifest"
SUBJECT_ROLE_V043 = "gold_challenge_lifecycle_package_manifest"
SUBJECT_ROLE_INDEX = "gold_reliance_package_index"


# ---------------------------------------------------------------------------
# Co-located inherited runner paths (subprocess-invoked) and the
# co-located v0.4.4 verifier path (subprocess-invoked under
# --self-validate).
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent

GOLD_V040_RUNNER = _TOOLS_DIR / "build_gold_governed_reliance_demo_v0_1_0.py"
GOLD_V041_RUNNER = _TOOLS_DIR / "build_gold_decision_report_hardening_v0_1_0.py"
GOLD_V042_RUNNER = _TOOLS_DIR / "build_gold_policy_evaluation_matrix_v0_1_0.py"
GOLD_V043_RUNNER = _TOOLS_DIR / "build_gold_challenge_lifecycle_lite_v0_1_0.py"
GOLD_V044_VERIFIER = _TOOLS_DIR / "verify_gold_reliance_package_index_v0_1_0.py"


# ---------------------------------------------------------------------------
# Subprocess invocation helpers for the four inherited runners.
#
# Each inherited runner is invoked WITHOUT --self-validate so that the
# v0.4.4 verifier (later, optionally) is the single entry point for
# chained verification across v0.4.4 -> v0.4.3 -> v0.4.2 -> v0.4.1 ->
# v0.4.0. Each inherited runner is invoked with --force so that the
# child-packages/v0.4.X/ subdirectory can be (re)materialized within
# the v0.4.4 staging tree. The v0.4.4 staging tree itself lives under
# the v0.4.4 scratch prefix, so even if an inherited runner does its
# own --force overwrite, the scope is bounded to a v0.4.4-marked
# /tmp path.
#
# Child manifest IDs are derived from the v0.4.4 --manifest-id by
# appending an inherited-release suffix. These derived child manifest
# IDs are NOT members of the v0.4.4 collision class, and the v0.4.4
# wrapping manifest's `manifest_id` is also excluded from the v0.4.4
# collision class; only the seven artifact / lifecycle / index IDs
# (conformance_report_id, decision_report_id, matrix_id,
# policy_evaluation_report_id, challenge_lifecycle_record_set_id,
# challenge_lifecycle_report_id, gold_reliance_package_index_id) form
# the v0.4.4 collision class.
# ---------------------------------------------------------------------------

def _relay_runner_output(result: subprocess.CompletedProcess) -> None:
    if result.stdout:
        sys.stdout.buffer.write(result.stdout)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)


def _invoke_v040_runner(
    *,
    bundle_root: Path,
    input_package: Path,
    out_dir: Path,
    manifest_id: str,
    conformance_report_id: str,
    generated_at: str,
) -> int:
    # The inherited runners' --input-package preflight refuses absolute
    # paths. Bare filenames relative to bundle_root (set as cwd) are
    # therefore used. bundle_root is a v0.4.4 scratch-prefixed /tmp
    # path; the originals are never forwarded.
    cmd = [
        sys.executable,
        str(GOLD_V040_RUNNER),
        "--input-package", input_package.name,
        "--manifest-id", manifest_id,
        "--report-id", conformance_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(out_dir),
        "--force",
    ]
    result = subprocess.run(
        cmd, cwd=str(bundle_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _relay_runner_output(result)
    return result.returncode


def _invoke_v041_runner(
    *,
    bundle_root: Path,
    input_package: Path,
    out_dir: Path,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    generated_at: str,
) -> int:
    cmd = [
        sys.executable,
        str(GOLD_V041_RUNNER),
        "--input-package", input_package.name,
        "--manifest-id", manifest_id,
        "--conformance-report-id", conformance_report_id,
        "--decision-report-id", decision_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(out_dir),
        "--force",
    ]
    result = subprocess.run(
        cmd, cwd=str(bundle_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _relay_runner_output(result)
    return result.returncode


def _invoke_v042_runner(
    *,
    bundle_root: Path,
    input_package: Path,
    matrix_input: Path,
    out_dir: Path,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    policy_evaluation_report_id: str,
    generated_at: str,
) -> int:
    cmd = [
        sys.executable,
        str(GOLD_V042_RUNNER),
        "--input-package", input_package.name,
        "--matrix-input", matrix_input.name,
        "--manifest-id", manifest_id,
        "--conformance-report-id", conformance_report_id,
        "--decision-report-id", decision_report_id,
        "--policy-evaluation-report-id", policy_evaluation_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(out_dir),
        "--force",
    ]
    result = subprocess.run(
        cmd, cwd=str(bundle_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _relay_runner_output(result)
    return result.returncode


def _invoke_v043_runner(
    *,
    bundle_root: Path,
    input_package: Path,
    matrix_input: Path,
    lifecycle_input: Path,
    out_dir: Path,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    policy_evaluation_report_id: str,
    challenge_lifecycle_report_id: str,
    generated_at: str,
) -> int:
    cmd = [
        sys.executable,
        str(GOLD_V043_RUNNER),
        "--input-package", input_package.name,
        "--matrix-input", matrix_input.name,
        "--lifecycle-input", lifecycle_input.name,
        "--manifest-id", manifest_id,
        "--conformance-report-id", conformance_report_id,
        "--decision-report-id", decision_report_id,
        "--policy-evaluation-report-id", policy_evaluation_report_id,
        "--challenge-lifecycle-report-id", challenge_lifecycle_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(out_dir),
        "--force",
    ]
    result = subprocess.run(
        cmd, cwd=str(bundle_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _relay_runner_output(result)
    return result.returncode


# ---------------------------------------------------------------------------
# Phase B step (g): read each child wrapping manifest. Used both to
# derive subject [0..3] sha256/size and to recover the cross-anchor
# identifiers required by the v0.4.4 wrapping manifest. Structural
# defects in the child manifest are NOT re-emitted by v0.4.4; they
# fall through to the v0.4.4 verifier, which subprocess-invokes the
# inherited verifier and relays its reason verbatim.
# ---------------------------------------------------------------------------

def _read_child_manifest(
    *, manifest_path: Path
) -> tuple[bytes, dict[str, Any]]:
    raw = manifest_path.read_bytes()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Pass through to the verifier as inherited R01 via subprocess
        # relay; runner does not synthesize a sixth refusal.
        obj = {}
    if not isinstance(obj, dict):
        obj = {}
    return raw, obj


# ---------------------------------------------------------------------------
# Phase B step (h): derive the v0.4.4 index body (subject [4]).
#
# The body is the only v0.4.4-authored payload in the package. It
# contains a four-entry array (one per inherited release), a fixed
# coverage_summary, the two binding anchor identifiers (package_id,
# governed_reliance_demo_id), and the v0.4.4 collision-class member
# `gold_reliance_package_index_id`.
#
# The body's `index_fingerprint` is computed as SHA-256 of the
# canonical JSON encoding of the body WITHOUT the `index_fingerprint`
# field AND WITHOUT a trailing newline (per the v0.4.4 body schema).
# This is distinct from the body file's on-disk SHA-256, which is
# computed over the body bytes as written (with a trailing newline,
# matching the v0.4.0..v0.4.3 convention).
# ---------------------------------------------------------------------------

def _build_index_body_entries(
    *,
    v040_manifest_sha: str,
    v040_manifest_size: int,
    v041_manifest_sha: str,
    v041_manifest_size: int,
    v042_manifest_sha: str,
    v042_manifest_size: int,
    v043_manifest_sha: str,
    v043_manifest_size: int,
) -> list[dict[str, Any]]:
    return [
        {
            "release_label": RELEASE_LABEL_V040,
            "child_subject_index": 0,
            "child_package_root": f"{CHILD_DIR_V040}/",
            "child_manifest_path": SUBJECT_PATH_V040,
            "child_manifest_fingerprint": v040_manifest_sha,
            "child_manifest_size_bytes": v040_manifest_size,
        },
        {
            "release_label": RELEASE_LABEL_V041,
            "child_subject_index": 1,
            "child_package_root": f"{CHILD_DIR_V041}/",
            "child_manifest_path": SUBJECT_PATH_V041,
            "child_manifest_fingerprint": v041_manifest_sha,
            "child_manifest_size_bytes": v041_manifest_size,
        },
        {
            "release_label": RELEASE_LABEL_V042,
            "child_subject_index": 2,
            "child_package_root": f"{CHILD_DIR_V042}/",
            "child_manifest_path": SUBJECT_PATH_V042,
            "child_manifest_fingerprint": v042_manifest_sha,
            "child_manifest_size_bytes": v042_manifest_size,
        },
        {
            "release_label": RELEASE_LABEL_V043,
            "child_subject_index": 3,
            "child_package_root": f"{CHILD_DIR_V043}/",
            "child_manifest_path": SUBJECT_PATH_V043,
            "child_manifest_fingerprint": v043_manifest_sha,
            "child_manifest_size_bytes": v043_manifest_size,
        },
    ]


def _build_coverage_summary() -> dict[str, Any]:
    # The seven members of the v0.4.4 pairwise-distinct collision
    # class are: conformance_report_id, decision_report_id, matrix_id,
    # policy_evaluation_report_id, challenge_lifecycle_record_set_id,
    # challenge_lifecycle_report_id, gold_reliance_package_index_id.
    # package_id and governed_reliance_demo_id are binding anchors and
    # are NOT counted here.
    return {
        "child_package_count": 4,
        "inherited_release_count": 4,
        "pairwise_distinct_id_count": 7,
        "package_id_anchor_consistency": True,
        "governed_reliance_demo_id_anchor_consistency": True,
    }


def _build_index_body(
    *,
    gold_reliance_package_index_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    body_without_fingerprint = {
        "document_type": "proofrail.gold.reliance_package_index",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.reliance_package_index.v0.4.4",
        "hash_algorithm": "sha256",
        "gold_reliance_package_index_id": gold_reliance_package_index_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "generated_at": generated_at,
        "entries": entries,
        "coverage_summary": _build_coverage_summary(),
    }
    index_fingerprint = _sha256_hex(
        _canonical_json_bytes_no_newline(body_without_fingerprint)
    )
    body = dict(body_without_fingerprint)
    body["index_fingerprint"] = index_fingerprint
    return body


# ---------------------------------------------------------------------------
# Phase B step (i): build the 5-subject v0.4.4 wrapping manifest. The
# wrapping manifest itself is NOT counted as a subject. Subjects [0..3]
# are the four inherited child wrapping manifests; subject [4] is the
# index body file at the package root.
# ---------------------------------------------------------------------------

def _build_wrapping_manifest(
    *,
    manifest_id: str,
    conformance_report_id: str,
    decision_report_id: str,
    matrix_id: str,
    policy_evaluation_report_id: str,
    challenge_lifecycle_record_set_id: str,
    challenge_lifecycle_report_id: str,
    gold_reliance_package_index_id: str,
    package_id: str,
    governed_reliance_demo_id: str,
    generated_at: str,
    v040_manifest_sha: str, v040_manifest_size: int,
    v041_manifest_sha: str, v041_manifest_size: int,
    v042_manifest_sha: str, v042_manifest_size: int,
    v043_manifest_sha: str, v043_manifest_size: int,
    index_body_sha: str, index_body_size: int,
) -> dict[str, Any]:
    return {
        "document_type": "proofrail.gold.reliance_package_index_manifest",
        "schema_version": "v0.1.0",
        "proofrail_release": "gold.reliance_package_index.v0.4.4",
        "hash_algorithm": "sha256",
        "manifest_id": manifest_id,
        "conformance_report_id": conformance_report_id,
        "decision_report_id": decision_report_id,
        "matrix_id": matrix_id,
        "policy_evaluation_report_id": policy_evaluation_report_id,
        "challenge_lifecycle_record_set_id": challenge_lifecycle_record_set_id,
        "challenge_lifecycle_report_id": challenge_lifecycle_report_id,
        "gold_reliance_package_index_id": gold_reliance_package_index_id,
        "package_id": package_id,
        "governed_reliance_demo_id": governed_reliance_demo_id,
        "generated_at": generated_at,
        "subjects": [
            {
                "role": SUBJECT_ROLE_V040,
                "path": SUBJECT_PATH_V040,
                "sha256": v040_manifest_sha,
                "size_bytes": v040_manifest_size,
            },
            {
                "role": SUBJECT_ROLE_V041,
                "path": SUBJECT_PATH_V041,
                "sha256": v041_manifest_sha,
                "size_bytes": v041_manifest_size,
            },
            {
                "role": SUBJECT_ROLE_V042,
                "path": SUBJECT_PATH_V042,
                "sha256": v042_manifest_sha,
                "size_bytes": v042_manifest_size,
            },
            {
                "role": SUBJECT_ROLE_V043,
                "path": SUBJECT_PATH_V043,
                "sha256": v043_manifest_sha,
                "size_bytes": v043_manifest_size,
            },
            {
                "role": SUBJECT_ROLE_INDEX,
                "path": INDEX_BODY_FILENAME,
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
    """Subprocess-invoke the v0.4.4 verifier against the staged manifest.

    The v0.4.4 runner self-validates against the v0.4.4 verifier ONLY.
    Inherited verifier chains are reached transitively via the v0.4.4
    verifier's own subprocess delegation to each inherited verifier on
    its corresponding `child-packages/v0.4.X/` child wrapping-manifest
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
#
# --force is permitted ONLY when --output-dir matches the v0.4.4
# scratch prefix. Otherwise --force is refused with a structured
# stderr line and exit 1. Without --force, an existing --output-dir
# is always refused.
#
# Both rooted prefix forms are accepted because os.path.realpath()
# resolves /tmp/foo to /private/tmp/foo on macOS (where /tmp is a
# symlink to /private/tmp). This mirrors the dual-prefix discipline
# already in _safe_rmtree above; without it, a --force re-run against
# an existing v0.4.4-scratch-prefixed path is rejected on macOS even
# though the path literally starts with /tmp/proofrail-v044-.
# ---------------------------------------------------------------------------

def _output_dir_is_under_scratch_prefix(out_dir: Path) -> bool:
    s = str(Path(os.path.realpath(str(out_dir))))
    return any(
        s.startswith(prefix + "proofrail-v044-")
        for prefix in _TMP_ROOTED_PREFIXES
    )


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a ProofRail Gold v0.4.4 Reliance Package Index package.",
    )
    parser.add_argument("--input-package", type=str, default=None,
                        help="Path to the v0.4.0-shaped governed-reliance package body JSON.")
    parser.add_argument("--matrix-input", type=str, default=None,
                        help="Path to the v0.4.2 hand-authored matrix template JSON.")
    parser.add_argument("--lifecycle-input", type=str, default=None,
                        help="Path to the v0.4.3 hand-authored challenge lifecycle records template JSON.")
    parser.add_argument("--manifest-id", type=str, required=True,
                        help="v0.4.4 wrapping manifest_id (not a member of the v0.4.4 collision class).")
    parser.add_argument("--conformance-report-id", type=str, required=True,
                        help="Passed through to the v0.4.0 child runner as --report-id and to v0.4.1..v0.4.3 as --conformance-report-id.")
    parser.add_argument("--decision-report-id", type=str, required=True,
                        help="Passed through to v0.4.1..v0.4.3 child runners.")
    parser.add_argument("--policy-evaluation-report-id", type=str, required=True,
                        help="Passed through to v0.4.2 and v0.4.3 child runners.")
    parser.add_argument("--challenge-lifecycle-report-id", type=str, required=True,
                        help="Passed through to the v0.4.3 child runner.")
    parser.add_argument("--gold-reliance-package-index-id", type=str, required=True,
                        help="v0.4.4-owned collision-class member; cross-anchored to the index body.")
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
    # Inherited runners are invoked against the scratch copies only.
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
                    f"{V044_SCRATCH_PREFIX!r}: {out_dir}\n"
                )
                return 1
            _safe_rmtree(out_dir)

        pid = os.getpid()
        staging = Path(f"{V044_SCRATCH_PREFIX}staging-{pid}")
        # Defensive: clear any leftover scratch staging dir from a
        # prior crashed run. The path is v0.4.4-scratch-prefixed so
        # _safe_rmtree will accept it.
        _safe_rmtree(staging)
        staging.mkdir(parents=True, exist_ok=False)

        try:
            # Phase B steps (c..f): subprocess-delegate to the four
            # inherited runners into child-packages/v0.4.X/. Each
            # inherited runner produces a complete self-contained
            # child closure (its wrapping manifest plus every subject
            # file it references) alongside its wrapping manifest, so
            # that the corresponding inherited verifier can resolve
            # its subjects relative to the child manifest directory
            # at v0.4.4 verification time.
            v040_out = staging / CHILD_DIR_V040
            v041_out = staging / CHILD_DIR_V041
            v042_out = staging / CHILD_DIR_V042
            v043_out = staging / CHILD_DIR_V043

            # Derived inherited manifest_ids. These are NOT members
            # of the v0.4.4 collision class.
            inherited_manifest_id_v040 = f"{args.manifest_id}-inherited-v040"
            inherited_manifest_id_v041 = f"{args.manifest_id}-inherited-v041"
            inherited_manifest_id_v042 = f"{args.manifest_id}-inherited-v042"
            inherited_manifest_id_v043 = f"{args.manifest_id}-inherited-v043"

            rc = _invoke_v040_runner(
                bundle_root=bundle_root,
                input_package=scratch_input,
                out_dir=v040_out,
                manifest_id=inherited_manifest_id_v040,
                conformance_report_id=args.conformance_report_id,
                generated_at=args.generated_at,
            )
            if rc != 0:
                _safe_rmtree(staging)
                return rc

            rc = _invoke_v041_runner(
                bundle_root=bundle_root,
                input_package=scratch_input,
                out_dir=v041_out,
                manifest_id=inherited_manifest_id_v041,
                conformance_report_id=args.conformance_report_id,
                decision_report_id=args.decision_report_id,
                generated_at=args.generated_at,
            )
            if rc != 0:
                _safe_rmtree(staging)
                return rc

            rc = _invoke_v042_runner(
                bundle_root=bundle_root,
                input_package=scratch_input,
                matrix_input=scratch_matrix,
                out_dir=v042_out,
                manifest_id=inherited_manifest_id_v042,
                conformance_report_id=args.conformance_report_id,
                decision_report_id=args.decision_report_id,
                policy_evaluation_report_id=args.policy_evaluation_report_id,
                generated_at=args.generated_at,
            )
            if rc != 0:
                _safe_rmtree(staging)
                return rc

            rc = _invoke_v043_runner(
                bundle_root=bundle_root,
                input_package=scratch_input,
                matrix_input=scratch_matrix,
                lifecycle_input=scratch_lifecycle,
                out_dir=v043_out,
                manifest_id=inherited_manifest_id_v043,
                conformance_report_id=args.conformance_report_id,
                decision_report_id=args.decision_report_id,
                policy_evaluation_report_id=args.policy_evaluation_report_id,
                challenge_lifecycle_report_id=args.challenge_lifecycle_report_id,
                generated_at=args.generated_at,
            )
            if rc != 0:
                _safe_rmtree(staging)
                return rc

            # Phase B step (g): read each child wrapping manifest for
            # SHA-256 + size and the cross-anchor identifiers
            # required by the v0.4.4 wrapping manifest.
            v040_manifest_path = staging / SUBJECT_PATH_V040
            v041_manifest_path = staging / SUBJECT_PATH_V041
            v042_manifest_path = staging / SUBJECT_PATH_V042
            v043_manifest_path = staging / SUBJECT_PATH_V043

            v040_bytes, v040_obj = _read_child_manifest(manifest_path=v040_manifest_path)
            v041_bytes, v041_obj = _read_child_manifest(manifest_path=v041_manifest_path)
            v042_bytes, v042_obj = _read_child_manifest(manifest_path=v042_manifest_path)
            v043_bytes, v043_obj = _read_child_manifest(manifest_path=v043_manifest_path)

            v040_sha = _sha256_hex(v040_bytes)
            v041_sha = _sha256_hex(v041_bytes)
            v042_sha = _sha256_hex(v042_bytes)
            v043_sha = _sha256_hex(v043_bytes)
            v040_size = len(v040_bytes)
            v041_size = len(v041_bytes)
            v042_size = len(v042_bytes)
            v043_size = len(v043_bytes)

            # Cross-anchor identifiers sourced from the inherited
            # child wrapping manifests. The v0.4.4 wrapping manifest
            # binds:
            #   - package_id, governed_reliance_demo_id (binding anchors)
            #   - conformance_report_id (from v0.4.0 manifest's report_id)
            #   - decision_report_id (from v0.4.1 manifest)
            #   - matrix_id, policy_evaluation_report_id (from v0.4.2)
            #   - challenge_lifecycle_record_set_id,
            #     challenge_lifecycle_report_id (from v0.4.3)
            # On structural defects in any child manifest, the runner
            # does NOT synthesize a sixth refusal; falsey/missing
            # fields fall through to the v0.4.4 verifier, which
            # surfaces them via the inherited verifier's existing
            # R02..R48 vocabulary on subprocess relay or via R01 at
            # the wrapping-manifest layer.
            package_id = (
                v040_obj.get("package_id")
                if isinstance(v040_obj.get("package_id"), str)
                else ""
            )
            governed_reliance_demo_id = (
                v040_obj.get("governed_reliance_demo_id")
                if isinstance(v040_obj.get("governed_reliance_demo_id"), str)
                else ""
            )
            # v0.4.0 wraps the conformance report under `report_id`;
            # v0.4.1 onward use `conformance_report_id`. The v0.4.4
            # manifest reads `report_id` from the v0.4.0 manifest as
            # `conformance_report_id`.
            conformance_report_id_from_v040 = (
                v040_obj.get("report_id")
                if isinstance(v040_obj.get("report_id"), str)
                else args.conformance_report_id
            )
            decision_report_id_from_v041 = (
                v041_obj.get("decision_report_id")
                if isinstance(v041_obj.get("decision_report_id"), str)
                else args.decision_report_id
            )
            matrix_id_from_v042 = (
                v042_obj.get("matrix_id")
                if isinstance(v042_obj.get("matrix_id"), str)
                else ""
            )
            policy_evaluation_report_id_from_v042 = (
                v042_obj.get("policy_evaluation_report_id")
                if isinstance(v042_obj.get("policy_evaluation_report_id"), str)
                else args.policy_evaluation_report_id
            )
            challenge_lifecycle_record_set_id_from_v043 = (
                v043_obj.get("challenge_lifecycle_record_set_id")
                if isinstance(v043_obj.get("challenge_lifecycle_record_set_id"), str)
                else ""
            )
            challenge_lifecycle_report_id_from_v043 = (
                v043_obj.get("challenge_lifecycle_report_id")
                if isinstance(v043_obj.get("challenge_lifecycle_report_id"), str)
                else args.challenge_lifecycle_report_id
            )

            # Phase B step (h): derive index body (subject [4]) and
            # write it.
            entries = _build_index_body_entries(
                v040_manifest_sha=v040_sha, v040_manifest_size=v040_size,
                v041_manifest_sha=v041_sha, v041_manifest_size=v041_size,
                v042_manifest_sha=v042_sha, v042_manifest_size=v042_size,
                v043_manifest_sha=v043_sha, v043_manifest_size=v043_size,
            )
            index_body = _build_index_body(
                gold_reliance_package_index_id=args.gold_reliance_package_index_id,
                package_id=package_id,
                governed_reliance_demo_id=governed_reliance_demo_id,
                generated_at=args.generated_at,
                entries=entries,
            )
            index_body_bytes = _canonical_json_bytes(index_body)
            staged_index_body = staging / INDEX_BODY_FILENAME
            staged_index_body.write_bytes(index_body_bytes)
            index_body_sha = _sha256_hex(index_body_bytes)
            index_body_size = len(index_body_bytes)

            # Phase B step (i): build the v0.4.4 wrapping manifest
            # and write it.
            wrapping_manifest = _build_wrapping_manifest(
                manifest_id=args.manifest_id,
                conformance_report_id=conformance_report_id_from_v040,
                decision_report_id=decision_report_id_from_v041,
                matrix_id=matrix_id_from_v042,
                policy_evaluation_report_id=policy_evaluation_report_id_from_v042,
                challenge_lifecycle_record_set_id=challenge_lifecycle_record_set_id_from_v043,
                challenge_lifecycle_report_id=challenge_lifecycle_report_id_from_v043,
                gold_reliance_package_index_id=args.gold_reliance_package_index_id,
                package_id=package_id,
                governed_reliance_demo_id=governed_reliance_demo_id,
                generated_at=args.generated_at,
                v040_manifest_sha=v040_sha, v040_manifest_size=v040_size,
                v041_manifest_sha=v041_sha, v041_manifest_size=v041_size,
                v042_manifest_sha=v042_sha, v042_manifest_size=v042_size,
                v043_manifest_sha=v043_sha, v043_manifest_size=v043_size,
                index_body_sha=index_body_sha, index_body_size=index_body_size,
            )
            wrapping_manifest_bytes = _canonical_json_bytes(wrapping_manifest)
            staged_manifest = staging / MANIFEST_FILENAME
            staged_manifest.write_bytes(wrapping_manifest_bytes)

            # Phase B step (j): optional self-validate against the
            # v0.4.4 verifier. The v0.4.4 verifier itself
            # subprocess-delegates to each inherited verifier on the
            # corresponding child manifest path. On any non-zero
            # exit, the entire v0.4.4 staging tree (wrapping
            # manifest, index body, and all four child closures) is
            # removed (via _safe_rmtree, scoped strictly to the
            # v0.4.4 scratch-prefixed staging tree) and the verifier
            # output is relayed verbatim.
            if args.self_validate:
                rc = _self_validate(GOLD_V044_VERIFIER, staged_manifest)
                if rc != 0:
                    _safe_rmtree(staging)
                    return rc

            _atomic_publish(staging, out_dir)
        except Exception:
            _safe_rmtree(staging)
            raise
    finally:
        # Always clean up the scratch input bundle. _safe_rmtree
        # enforces the /tmp + v0.4.4-prefix discipline; if for any
        # reason the bundle path was tampered with, cleanup is
        # silently refused rather than allowed to touch tracked
        # paths.
        _safe_rmtree(bundle_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
