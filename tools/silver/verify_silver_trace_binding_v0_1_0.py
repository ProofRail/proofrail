#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.2 trace binding package.

Hash-first, fail-fast. The verifier:

  1.  Parses the trace binding manifest.
  2.  Validates manifest structural fields (document_type,
      schema_version, proofrail_release, hash_algorithm,
      trace_binding_report_id, generated_at, exactly four subjects,
      scope_limitations presence/type, non_claims presence/type).
  3.  For each subject in fixed SUBJECT_ORDER:
        a. Rejects any subject path containing '..' or that is absolute
           (trace_subject_path_traversal) BEFORE exact equality.
        b. Checks exact path and role equality
           (invalid_trace_binding_manifest).
        c. Checks the subject file exists
           (trace_subject_file_missing).
        d. Recomputes SHA-256 and compares to the recorded sha256
           (trace_subject_hash_mismatch).
  4.  Structurally rejects the adapter descriptor if
      `trust_boundary.source_is_trust_authority` is not exactly false
      (trace_source_marked_authority). Per Amendment 1, this runs
      BEFORE the generic v0.2.6 adapter validator so that the reason
      stays directly reachable.
  5.  Subprocess-invokes the unchanged v0.2.6 adapter validator on
      the copied adapter descriptor (trace_adapter_invalid).
  6.  Parses trace events JSONL (trace_events_invalid). Catches JSON
      parse errors and structural field errors; never leaks Python
      tracebacks for expected malformed-input cases.
  7.  Rejects duplicate event_id and duplicate (trace_id, span_id)
      (trace_event_duplicate).
  8.  Rejects ordering violations on (event_time, event_id) ascending
      (trace_event_time_order_invalid).
  9.  Parses the binding set (trace_binding_set_invalid). Closed-enum
      checks for required_decision and expected_binding_status.
  10. Rejects duplicate claim_id (trace_binding_duplicate).
  11. For each non-gap binding row: the referenced event MUST exist
      (trace_binding_event_missing).
  12. For each non-gap binding row: required_* fields MUST equal the
      resolved event's fields (trace_binding_field_mismatch).
  13. For each non-gap binding row: the resolved event's event_time
      MUST lie inside trace_time_window inclusive
      (trace_binding_time_window_mismatch).
  14. Parses the trace binding report (trace_report_invalid).
  15. Cross-checks report binding hashes against manifest subject
      hashes (trace_report_binding_mismatch):
        report.trace_source.adapter_descriptor_sha256 == subject[0].sha256
        report.trace_events.events_sha256              == subject[1].sha256
        report.binding_set.bindings_sha256             == subject[2].sha256
        plus event_count, binding_count, time_window, ids.
  16. Per Amendment 2, BEFORE the generic status mismatch check,
      independently detects warning/gap/out-of-scope downgrades to
      `bound` (trace_warning_downgrade).
  17. Re-derives each binding row from the trace events and binding
      set and checks binding_status / trace_event_id / trace_id /
      span_id / protected_action_id / principal_id / decision /
      evidence_refs / warning equality (trace_report_status_mismatch).
  18. Recomputes binding_summary counts from bindings[]
      (trace_report_count_mismatch).
  19. Scans every string in the report and binding set OUTSIDE
      scope_limitations / non_claims for forbidden positive overclaim
      tokens (trace_overclaim).
  20. Re-checks manifest / binding set / report scope_limitations for
      emptiness or blank entries (trace_limitations_missing).
  21. Re-checks manifest / binding set / report non_claims for
      emptiness or blank entries (trace_non_claims_missing).

Stable failure reasons (22):

  invalid_trace_binding_manifest
  trace_subject_path_traversal
  trace_subject_file_missing
  trace_subject_hash_mismatch
  trace_source_marked_authority
  trace_adapter_invalid
  trace_events_invalid
  trace_event_duplicate
  trace_event_time_order_invalid
  trace_binding_set_invalid
  trace_binding_duplicate
  trace_binding_event_missing
  trace_binding_field_mismatch
  trace_binding_time_window_mismatch
  trace_report_invalid
  trace_report_binding_mismatch
  trace_warning_downgrade
  trace_report_status_mismatch
  trace_report_count_mismatch
  trace_limitations_missing
  trace_non_claims_missing
  trace_overclaim

Note: adapter_validation_failed, trace_events_validation_failed,
trace_binding_set_validation_failed, and
trace_binding_self_validation_failed are runner-only codes (emitted
by build_silver_trace_binding_v0_1_0.py) and are NEVER emitted by
this verifier.

Usage:
  python3 tools/silver/verify_silver_trace_binding_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-trace-binding-v0.3.2/silver-trace-binding-manifest.json

Exit codes:
  0 - trace binding package valid
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

THIS_FILE = Path(__file__).resolve()
TOOLS_DIR = THIS_FILE.parent
ADAPTER_VALIDATOR = TOOLS_DIR / "validate_evidence_source_adapter_v0_1_0.py"

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.trace_binding_manifest"
REPORT_DOCUMENT_TYPE = "proofrail.silver.trace_binding_report"
EVENT_DOCUMENT_TYPE = "proofrail.silver.trace_event"
BINDING_SET_DOCUMENT_TYPE = "proofrail.silver.trace_claim_binding_set"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.2"
HASH_ALGORITHM = "sha256"

# Fixed manifest subject layout (relative_path, role). Position is
# significant.
SUBJECT_ORDER: list[tuple[str, str]] = [
    ("adapter/", "trace_source_adapter_descriptor"),   # path prefix only
    ("trace-events.jsonl", "trace_events"),
    ("trace-claim-bindings.json", "trace_claim_binding_set"),
    ("silver-trace-binding-report.json",
     "silver_trace_binding_report"),
]
SUBJECT_COUNT = len(SUBJECT_ORDER)

ALLOWED_DECISIONS = {"allow", "deny", "observe", "block"}
ALLOWED_BINDING_STATUSES = {
    "bound",
    "bound_with_warning",
    "trace_gap_detected",
    "out_of_scope_for_trace_binding",
}
NON_CLEAN_STATUSES = {
    "bound_with_warning",
    "trace_gap_detected",
    "out_of_scope_for_trace_binding",
}

REQUIRED_TRACE_EVENT_FIELDS = (
    "document_type",
    "schema_version",
    "proofrail_release",
    "event_id",
    "trace_id",
    "span_id",
    "event_time",
    "principal_id",
    "protected_action_id",
    "decision",
    "decision_reason",
    "source_event_ref",
    "attributes",
)

REQUIRED_BINDING_FIELDS = (
    "claim_id",
    "required_trace_event_id",
    "required_trace_id",
    "required_span_id",
    "required_protected_action_id",
    "required_principal_id",
    "required_decision",
    "expected_binding_status",
)

REQUIRED_REPORT_BINDING_ROW_FIELDS = (
    "claim_id",
    "trace_event_id",
    "trace_id",
    "span_id",
    "protected_action_id",
    "principal_id",
    "decision",
    "binding_status",
    "evidence_refs",
    "warning",
)

# Forbidden positive overclaim tokens (case-insensitive substring match).
FORBIDDEN_POSITIVE_TOKENS = [
    "gold-ready",
    "gold ready",
    "gold_ready",
    "ready for gold",
    "certified",
    "approved",
    "audited",
    "legally accepted",
    "legally revoked",
    "challenge resolved",
    "gold accepted",
    "compliant",
    "production-approved",
    "production-ready",
    "regulator-ready",
    "regulator approval",
    "trust transferred",
    "trust transfer",
    "runtime proof",
    "authoritative trace",
    "opentelemetry compliant",
    "opentelemetry conformance",
]

ISO_8601_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


# --------------------------------------------------------------------- #
# Output helpers                                                        #
# --------------------------------------------------------------------- #

def usage_error(msg: str) -> int:
    print(f"FAIL: usage_error: {msg}", file=sys.stderr)
    return 2


def fail(reason: str, detail: str) -> int:
    print(f"FAIL: {reason}: {detail}", file=sys.stderr)
    return 1


# --------------------------------------------------------------------- #
# Primitive helpers                                                     #
# --------------------------------------------------------------------- #

def parse_iso_8601_z(value: Any) -> datetime | None:
    if not isinstance(value, str) or not ISO_8601_Z_RE.match(value):
        return None
    try:
        return datetime.strptime(
            value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z"
        )
    except ValueError:
        try:
            return datetime.strptime(
                value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            return None


def non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def has_path_traversal(rel: str) -> bool:
    if not isinstance(rel, str) or rel == "":
        return True
    if rel.startswith("/"):
        return True
    parts = rel.replace("\\", "/").split("/")
    if ".." in parts:
        return True
    return False


def sha256_label(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
    return f"sha256:{h.hexdigest()}", size


def array_of_strings_present(arr: Any) -> bool:
    if not isinstance(arr, list):
        return False
    for entry in arr:
        if not isinstance(entry, str):
            return False
    return True


def array_of_strings_non_empty(arr: Any) -> bool:
    if not isinstance(arr, list) or len(arr) == 0:
        return False
    for entry in arr:
        if not non_empty_str(entry):
            return False
    return True


def collect_strings_outside(
    node: Any,
    exclude_keys: set[str],
    out: list[str],
) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k in exclude_keys:
                continue
            collect_strings_outside(v, exclude_keys, out)
    elif isinstance(node, list):
        for item in node:
            collect_strings_outside(item, exclude_keys, out)
    elif isinstance(node, str):
        out.append(node)


def detect_overclaim(node: Any) -> str | None:
    strings: list[str] = []
    collect_strings_outside(
        node, {"scope_limitations", "non_claims"}, strings
    )
    for s in strings:
        lower = s.lower()
        for token in FORBIDDEN_POSITIVE_TOKENS:
            if token in lower:
                return token
    return None


# --------------------------------------------------------------------- #
# Manifest validation                                                   #
# --------------------------------------------------------------------- #

def validate_manifest_shape(
    manifest: Any,
) -> tuple[str, str] | None:
    """Returns (reason, detail) on failure, None on pass.

    Per Amendment 2: only does presence/type for scope_limitations and
    non_claims here. Emptiness/blank entries are checked later under
    dedicated reasons.
    """
    if not isinstance(manifest, dict):
        return ("invalid_trace_binding_manifest",
                "manifest is not a JSON object")
    expected_fields = {
        "document_type": MANIFEST_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "hash_algorithm": HASH_ALGORITHM,
    }
    for k, expected in expected_fields.items():
        v = manifest.get(k)
        if v != expected:
            return ("invalid_trace_binding_manifest",
                    f"{k} must be {expected!r}, got {v!r}")
    if not non_empty_str(manifest.get("trace_binding_report_id")):
        return ("invalid_trace_binding_manifest",
                "trace_binding_report_id must be a non-empty string")
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return ("invalid_trace_binding_manifest",
                "generated_at must be ISO-8601 UTC Z-suffixed")
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return ("invalid_trace_binding_manifest",
                "subjects must be an array")
    if len(subjects) != SUBJECT_COUNT:
        return ("invalid_trace_binding_manifest",
                f"subjects must contain exactly {SUBJECT_COUNT} entries, "
                f"got {len(subjects)}")
    for i, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}] is not a JSON object")
        for k in ("path", "role", "sha256", "size_bytes"):
            if k not in subj:
                return ("invalid_trace_binding_manifest",
                        f"subjects[{i}] missing required field '{k}'")
        if not non_empty_str(subj["path"]):
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}].path must be a non-empty string")
        if not non_empty_str(subj["role"]):
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}].role must be a non-empty string")
        sha = subj["sha256"]
        if not isinstance(sha, str) or not sha.startswith("sha256:") \
                or len(sha) != len("sha256:") + 64:
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}].sha256 must be 'sha256:<64 hex>'")
        if not isinstance(subj["size_bytes"], int) \
                or subj["size_bytes"] < 0:
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}].size_bytes must be a non-negative "
                    f"integer")
    if not array_of_strings_present(manifest.get("scope_limitations")):
        return ("invalid_trace_binding_manifest",
                "scope_limitations must be an array of strings")
    if not array_of_strings_present(manifest.get("non_claims")):
        return ("invalid_trace_binding_manifest",
                "non_claims must be an array of strings")
    return None


def check_subject_paths_and_roles(
    subjects: list[dict],
) -> tuple[str, str] | None:
    """Path-traversal check BEFORE exact path equality. Then exact
    path/role equality against SUBJECT_ORDER."""
    # Step A: path traversal first.
    for i, subj in enumerate(subjects):
        if has_path_traversal(subj["path"]):
            return ("trace_subject_path_traversal",
                    f"subjects[{i}].path {subj['path']!r} is absolute or "
                    f"contains '..'")
    # Step B: exact path / role equality.
    for i, subj in enumerate(subjects):
        expected_prefix, expected_role = SUBJECT_ORDER[i]
        path = subj["path"]
        role = subj["role"]
        if i == 0:
            # adapter subject lives under adapter/<filename>
            if not path.startswith(expected_prefix) \
                    or "/" not in path[len(expected_prefix):] + "/" \
                    or path == expected_prefix:
                return ("invalid_trace_binding_manifest",
                        f"subjects[0].path must be under "
                        f"{expected_prefix!r}, got {path!r}")
            # Reject any further '/' beyond adapter/<filename>
            remainder = path[len(expected_prefix):]
            if "/" in remainder:
                return ("invalid_trace_binding_manifest",
                        f"subjects[0].path must be exactly "
                        f"adapter/<filename>, got {path!r}")
        else:
            if path != expected_prefix:
                return ("invalid_trace_binding_manifest",
                        f"subjects[{i}].path must be {expected_prefix!r}, "
                        f"got {path!r}")
        if role != expected_role:
            return ("invalid_trace_binding_manifest",
                    f"subjects[{i}].role must be {expected_role!r}, got "
                    f"{role!r}")
    return None


# --------------------------------------------------------------------- #
# Adapter checks                                                        #
# --------------------------------------------------------------------- #

def adapter_source_is_not_authority(
    adapter_path: Path,
) -> tuple[bool, str]:
    """Per Amendment 1, runs BEFORE the generic v0.2.6 validator."""
    try:
        doc = json.loads(adapter_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        # Defer the structural error to the generic v0.2.6 validator.
        # We only inspect `source_is_trust_authority` when the JSON is
        # parseable AND the trust_boundary key is a dict; otherwise we
        # let v0.2.6 raise `trace_adapter_invalid`.
        return True, f"deferred to v0.2.6 validator: {e}"
    if not isinstance(doc, dict):
        return True, "deferred to v0.2.6 validator: not an object"
    tb = doc.get("trust_boundary")
    if not isinstance(tb, dict):
        return True, "deferred to v0.2.6 validator: no trust_boundary"
    flag = tb.get("source_is_trust_authority")
    if flag is not False:
        return False, (
            "adapter trust_boundary.source_is_trust_authority must be "
            f"exactly false, got {flag!r}"
        )
    return True, ""


def run_v0_2_6_adapter_validator(
    adapter_path: Path,
) -> tuple[bool, str]:
    if not ADAPTER_VALIDATOR.exists():
        return False, (
            f"v0.2.6 adapter validator not found at {ADAPTER_VALIDATOR}"
        )
    try:
        proc = subprocess.run(
            [sys.executable, str(ADAPTER_VALIDATOR),
             "--adapter", str(adapter_path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"subprocess error: {e}"
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip().splitlines()
        first = msg[0] if msg else "(no output)"
        return False, first
    return True, ""


# --------------------------------------------------------------------- #
# Trace events                                                          #
# --------------------------------------------------------------------- #

def parse_trace_events(
    events_path: Path,
) -> tuple[str, str] | tuple[None, list[dict]]:
    """Returns either (reason, detail) on failure, or (None, events) on
    pass. Catches all JSON parse errors and structural problems under
    `trace_events_invalid`, never leaks tracebacks for malformed input.
    """
    events: list[dict] = []
    try:
        with events_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    return ("trace_events_invalid",
                            f"line {line_no} is blank or whitespace-only")
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    return ("trace_events_invalid",
                            f"line {line_no} JSON parse error: {e}")
                if not isinstance(obj, dict):
                    return ("trace_events_invalid",
                            f"line {line_no} event is not a JSON object")
                for k in REQUIRED_TRACE_EVENT_FIELDS:
                    if k not in obj:
                        return ("trace_events_invalid",
                                f"line {line_no} missing required field "
                                f"'{k}'")
                if obj["document_type"] != EVENT_DOCUMENT_TYPE:
                    return ("trace_events_invalid",
                            f"line {line_no} document_type must be "
                            f"{EVENT_DOCUMENT_TYPE!r}, got "
                            f"{obj['document_type']!r}")
                if obj["schema_version"] != SCHEMA_VERSION:
                    return ("trace_events_invalid",
                            f"line {line_no} schema_version must be "
                            f"{SCHEMA_VERSION!r}, got "
                            f"{obj['schema_version']!r}")
                if obj["proofrail_release"] != PROOFRAIL_RELEASE:
                    return ("trace_events_invalid",
                            f"line {line_no} proofrail_release must be "
                            f"{PROOFRAIL_RELEASE!r}, got "
                            f"{obj['proofrail_release']!r}")
                for k in ("event_id", "trace_id", "span_id",
                          "principal_id", "protected_action_id",
                          "decision_reason", "source_event_ref"):
                    if not non_empty_str(obj[k]):
                        return ("trace_events_invalid",
                                f"line {line_no} '{k}' must be a "
                                f"non-empty string")
                if has_path_traversal(obj["source_event_ref"]):
                    return ("trace_events_invalid",
                            f"line {line_no} 'source_event_ref' is "
                            f"absolute or contains '..'")
                if parse_iso_8601_z(obj["event_time"]) is None:
                    return ("trace_events_invalid",
                            f"line {line_no} 'event_time' must be "
                            f"ISO-8601 UTC Z-suffixed")
                if obj["decision"] not in ALLOWED_DECISIONS:
                    return ("trace_events_invalid",
                            f"line {line_no} 'decision' must be one of "
                            f"{sorted(ALLOWED_DECISIONS)}, got "
                            f"{obj['decision']!r}")
                if not isinstance(obj["attributes"], dict):
                    return ("trace_events_invalid",
                            f"line {line_no} 'attributes' must be a "
                            f"JSON object")
                events.append(obj)
    except OSError as e:
        return ("trace_events_invalid",
                f"could not read trace events: {e}")
    if not events:
        return ("trace_events_invalid", "trace events file is empty")
    return (None, events)


def check_trace_event_uniqueness(
    events: list[dict],
) -> tuple[str, str] | None:
    seen_ids: dict[str, int] = {}
    seen_span: dict[tuple[str, str], int] = {}
    for i, ev in enumerate(events):
        if ev["event_id"] in seen_ids:
            return ("trace_event_duplicate",
                    f"duplicate event_id {ev['event_id']!r} "
                    f"(first at index {seen_ids[ev['event_id']]}, "
                    f"again at index {i})")
        seen_ids[ev["event_id"]] = i
        key = (ev["trace_id"], ev["span_id"])
        if key in seen_span:
            return ("trace_event_duplicate",
                    f"duplicate (trace_id, span_id) "
                    f"({ev['trace_id']!r}, {ev['span_id']!r}) "
                    f"(first at index {seen_span[key]}, "
                    f"again at index {i})")
        seen_span[key] = i
    return None


def check_trace_event_ordering(
    events: list[dict],
) -> tuple[str, str] | None:
    for i in range(1, len(events)):
        prev = events[i - 1]
        cur = events[i]
        pt = parse_iso_8601_z(prev["event_time"])
        ct = parse_iso_8601_z(cur["event_time"])
        if pt is None or ct is None:
            return ("trace_events_invalid",
                    f"event_time parse failed at index {i}")
        if (pt, prev["event_id"]) >= (ct, cur["event_id"]):
            return ("trace_event_time_order_invalid",
                    f"events not sorted ascending by "
                    f"(event_time, event_id) between index "
                    f"{i - 1} and {i}")
    return None


# --------------------------------------------------------------------- #
# Binding set                                                           #
# --------------------------------------------------------------------- #

def parse_binding_set(
    bindings_path: Path,
) -> tuple[str, str] | tuple[None, dict]:
    try:
        doc = json.loads(bindings_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return ("trace_binding_set_invalid",
                f"binding set is not valid JSON: {e}")
    if not isinstance(doc, dict):
        return ("trace_binding_set_invalid",
                "binding set is not a JSON object")
    if doc.get("document_type") != BINDING_SET_DOCUMENT_TYPE:
        return ("trace_binding_set_invalid",
                f"document_type must be {BINDING_SET_DOCUMENT_TYPE!r}, "
                f"got {doc.get('document_type')!r}")
    if doc.get("schema_version") != SCHEMA_VERSION:
        return ("trace_binding_set_invalid",
                f"schema_version must be {SCHEMA_VERSION!r}, "
                f"got {doc.get('schema_version')!r}")
    if doc.get("proofrail_release") != PROOFRAIL_RELEASE:
        return ("trace_binding_set_invalid",
                f"proofrail_release must be {PROOFRAIL_RELEASE!r}, "
                f"got {doc.get('proofrail_release')!r}")
    if not non_empty_str(doc.get("binding_set_id")):
        return ("trace_binding_set_invalid",
                "binding_set_id must be a non-empty string")
    tw = doc.get("trace_time_window")
    if not isinstance(tw, dict):
        return ("trace_binding_set_invalid",
                "trace_time_window must be an object")
    o = parse_iso_8601_z(tw.get("opens_at"))
    c = parse_iso_8601_z(tw.get("closes_at"))
    if o is None or c is None:
        return ("trace_binding_set_invalid",
                "trace_time_window.opens_at / closes_at must be "
                "ISO-8601 UTC Z")
    if not (o < c):
        return ("trace_binding_set_invalid",
                "trace_time_window.opens_at must be before closes_at")
    bindings = doc.get("bindings")
    if not isinstance(bindings, list) or len(bindings) == 0:
        return ("trace_binding_set_invalid",
                "bindings must be a non-empty array")
    for i, b in enumerate(bindings):
        if not isinstance(b, dict):
            return ("trace_binding_set_invalid",
                    f"bindings[{i}] is not a JSON object")
        for k in REQUIRED_BINDING_FIELDS:
            if k not in b:
                return ("trace_binding_set_invalid",
                        f"bindings[{i}] missing required field '{k}'")
            if not non_empty_str(b[k]):
                return ("trace_binding_set_invalid",
                        f"bindings[{i}].{k} must be a non-empty string")
        if b["required_decision"] not in ALLOWED_DECISIONS:
            return ("trace_binding_set_invalid",
                    f"bindings[{i}].required_decision must be one of "
                    f"{sorted(ALLOWED_DECISIONS)}, got "
                    f"{b['required_decision']!r}")
        if b["expected_binding_status"] not in ALLOWED_BINDING_STATUSES:
            return ("trace_binding_set_invalid",
                    f"bindings[{i}].expected_binding_status must be one "
                    f"of {sorted(ALLOWED_BINDING_STATUSES)}, got "
                    f"{b['expected_binding_status']!r}")
    if not array_of_strings_present(doc.get("scope_limitations")):
        return ("trace_binding_set_invalid",
                "scope_limitations must be an array of strings")
    if not array_of_strings_present(doc.get("non_claims")):
        return ("trace_binding_set_invalid",
                "non_claims must be an array of strings")
    return (None, doc)


def check_binding_set_duplicates(
    bindings: list[dict],
) -> tuple[str, str] | None:
    seen: dict[str, int] = {}
    for i, b in enumerate(bindings):
        if b["claim_id"] in seen:
            return ("trace_binding_duplicate",
                    f"duplicate claim_id {b['claim_id']!r} (first at "
                    f"index {seen[b['claim_id']]}, again at index {i})")
        seen[b["claim_id"]] = i
    return None


def cross_check_binding_set_against_events(
    binding_set: dict,
    events_by_id: dict[str, dict],
) -> tuple[str, str] | None:
    tw = binding_set["trace_time_window"]
    tw_open = parse_iso_8601_z(tw["opens_at"])
    tw_close = parse_iso_8601_z(tw["closes_at"])
    for b in binding_set["bindings"]:
        expected = b["expected_binding_status"]
        if expected == "trace_gap_detected":
            continue
        ev = events_by_id.get(b["required_trace_event_id"])
        if ev is None:
            return ("trace_binding_event_missing",
                    f"binding {b['claim_id']!r} references "
                    f"required_trace_event_id "
                    f"{b['required_trace_event_id']!r} which is not "
                    f"present in the trace event fixture")
        mismatches = []
        for req_field, ev_field in (
            ("required_trace_id", "trace_id"),
            ("required_span_id", "span_id"),
            ("required_protected_action_id", "protected_action_id"),
            ("required_principal_id", "principal_id"),
            ("required_decision", "decision"),
        ):
            if b[req_field] != ev[ev_field]:
                mismatches.append(
                    f"{req_field}={b[req_field]!r} vs event."
                    f"{ev_field}={ev[ev_field]!r}"
                )
        if mismatches:
            return ("trace_binding_field_mismatch",
                    f"binding {b['claim_id']!r} field mismatch vs event "
                    f"{ev['event_id']!r}: " + "; ".join(mismatches))
        ev_time = parse_iso_8601_z(ev["event_time"])
        if ev_time is None or ev_time < tw_open or ev_time > tw_close:
            return ("trace_binding_time_window_mismatch",
                    f"binding {b['claim_id']!r}: referenced event "
                    f"{ev['event_id']!r} event_time "
                    f"{ev['event_time']!r} lies outside "
                    f"trace_time_window "
                    f"[{tw['opens_at']!r}, {tw['closes_at']!r}]")
    return None


# --------------------------------------------------------------------- #
# Report                                                                #
# --------------------------------------------------------------------- #

def parse_report(
    report_path: Path,
) -> tuple[str, str] | tuple[None, dict]:
    try:
        doc = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return ("trace_report_invalid",
                f"report is not valid JSON: {e}")
    if not isinstance(doc, dict):
        return ("trace_report_invalid", "report is not a JSON object")
    expected_fields = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
    }
    for k, expected in expected_fields.items():
        v = doc.get(k)
        if v != expected:
            return ("trace_report_invalid",
                    f"{k} must be {expected!r}, got {v!r}")
    if not non_empty_str(doc.get("trace_binding_report_id")):
        return ("trace_report_invalid",
                "trace_binding_report_id must be a non-empty string")
    if parse_iso_8601_z(doc.get("generated_at")) is None:
        return ("trace_report_invalid",
                "generated_at must be ISO-8601 UTC Z-suffixed")
    ts = doc.get("trace_source")
    if not isinstance(ts, dict):
        return ("trace_report_invalid",
                "trace_source must be an object")
    if ts.get("source_type") != "observability_trace":
        return ("trace_report_invalid",
                f"trace_source.source_type must be "
                f"'observability_trace', got "
                f"{ts.get('source_type')!r}")
    if ts.get("source_is_trust_authority") is not False:
        return ("trace_report_invalid",
                "trace_source.source_is_trust_authority must be "
                f"exactly false, got "
                f"{ts.get('source_is_trust_authority')!r}")
    if not non_empty_str(ts.get("adapter_descriptor_path")) \
            or has_path_traversal(ts["adapter_descriptor_path"]):
        return ("trace_report_invalid",
                "trace_source.adapter_descriptor_path must be a safe "
                "relative path")
    if not isinstance(ts.get("adapter_descriptor_sha256"), str) \
            or not ts["adapter_descriptor_sha256"].startswith("sha256:"):
        return ("trace_report_invalid",
                "trace_source.adapter_descriptor_sha256 must be "
                "'sha256:<hex>'")
    te = doc.get("trace_events")
    if not isinstance(te, dict):
        return ("trace_report_invalid",
                "trace_events must be an object")
    if te.get("events_path") != "trace-events.jsonl":
        return ("trace_report_invalid",
                f"trace_events.events_path must be "
                f"'trace-events.jsonl', got {te.get('events_path')!r}")
    if not isinstance(te.get("events_sha256"), str) \
            or not te["events_sha256"].startswith("sha256:"):
        return ("trace_report_invalid",
                "trace_events.events_sha256 must be 'sha256:<hex>'")
    if not isinstance(te.get("event_count"), int) \
            or te["event_count"] < 1:
        return ("trace_report_invalid",
                "trace_events.event_count must be an integer >= 1")
    tw = te.get("time_window")
    if not isinstance(tw, dict) \
            or parse_iso_8601_z(tw.get("opens_at")) is None \
            or parse_iso_8601_z(tw.get("closes_at")) is None:
        return ("trace_report_invalid",
                "trace_events.time_window must contain ISO-8601 UTC Z "
                "opens_at and closes_at")
    bs = doc.get("binding_set")
    if not isinstance(bs, dict):
        return ("trace_report_invalid",
                "binding_set must be an object")
    if not non_empty_str(bs.get("binding_set_id")):
        return ("trace_report_invalid",
                "binding_set.binding_set_id must be a non-empty string")
    if bs.get("bindings_path") != "trace-claim-bindings.json":
        return ("trace_report_invalid",
                f"binding_set.bindings_path must be "
                f"'trace-claim-bindings.json', got "
                f"{bs.get('bindings_path')!r}")
    if not isinstance(bs.get("bindings_sha256"), str) \
            or not bs["bindings_sha256"].startswith("sha256:"):
        return ("trace_report_invalid",
                "binding_set.bindings_sha256 must be 'sha256:<hex>'")
    if not isinstance(bs.get("binding_count"), int) \
            or bs["binding_count"] < 1:
        return ("trace_report_invalid",
                "binding_set.binding_count must be an integer >= 1")
    summary = doc.get("binding_summary")
    if not isinstance(summary, dict):
        return ("trace_report_invalid",
                "binding_summary must be an object")
    for k in ("bound_count", "bound_with_warning_count",
              "trace_gap_detected_count", "out_of_scope_count"):
        if not isinstance(summary.get(k), int) or summary[k] < 0:
            return ("trace_report_invalid",
                    f"binding_summary.{k} must be a non-negative "
                    f"integer")
    if summary.get("source_is_trust_authority") is not False:
        return ("trace_report_invalid",
                "binding_summary.source_is_trust_authority must be "
                f"exactly false, got "
                f"{summary.get('source_is_trust_authority')!r}")
    rows = doc.get("bindings")
    if not isinstance(rows, list) or len(rows) == 0:
        return ("trace_report_invalid",
                "bindings must be a non-empty array")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            return ("trace_report_invalid",
                    f"bindings[{i}] is not a JSON object")
        for k in REQUIRED_REPORT_BINDING_ROW_FIELDS:
            if k not in row:
                return ("trace_report_invalid",
                        f"bindings[{i}] missing required field '{k}'")
        if not non_empty_str(row["claim_id"]):
            return ("trace_report_invalid",
                    f"bindings[{i}].claim_id must be a non-empty string")
        if row["binding_status"] not in ALLOWED_BINDING_STATUSES:
            return ("trace_report_invalid",
                    f"bindings[{i}].binding_status must be one of "
                    f"{sorted(ALLOWED_BINDING_STATUSES)}, got "
                    f"{row['binding_status']!r}")
        if not isinstance(row["evidence_refs"], list):
            return ("trace_report_invalid",
                    f"bindings[{i}].evidence_refs must be an array")
        for j, ref in enumerate(row["evidence_refs"]):
            if not isinstance(ref, str) or not ref:
                return ("trace_report_invalid",
                        f"bindings[{i}].evidence_refs[{j}] must be a "
                        f"non-empty string")
            if has_path_traversal(ref.split("#", 1)[0]):
                return ("trace_report_invalid",
                        f"bindings[{i}].evidence_refs[{j}] {ref!r} is "
                        f"absolute or contains '..'")
        warn = row["warning"]
        if warn is not None and not isinstance(warn, str):
            return ("trace_report_invalid",
                    f"bindings[{i}].warning must be a string or null")
    if not array_of_strings_present(doc.get("scope_limitations")):
        return ("trace_report_invalid",
                "scope_limitations must be an array of strings")
    if not array_of_strings_present(doc.get("non_claims")):
        return ("trace_report_invalid",
                "non_claims must be an array of strings")
    return (None, doc)


def cross_check_report_binding_hashes(
    report: dict,
    subjects: list[dict],
) -> tuple[str, str] | None:
    """Cross-check report's recorded hashes against manifest subject
    hashes and IDs / counts / time-window agreement."""
    if report["trace_source"]["adapter_descriptor_sha256"] \
            != subjects[0]["sha256"]:
        return ("trace_report_binding_mismatch",
                f"report.trace_source.adapter_descriptor_sha256 "
                f"({report['trace_source']['adapter_descriptor_sha256']!r}) "
                f"does not equal manifest subjects[0].sha256 "
                f"({subjects[0]['sha256']!r})")
    if report["trace_source"]["adapter_descriptor_path"] \
            != subjects[0]["path"]:
        return ("trace_report_binding_mismatch",
                f"report.trace_source.adapter_descriptor_path "
                f"({report['trace_source']['adapter_descriptor_path']!r}) "
                f"does not equal manifest subjects[0].path "
                f"({subjects[0]['path']!r})")
    if report["trace_events"]["events_sha256"] != subjects[1]["sha256"]:
        return ("trace_report_binding_mismatch",
                f"report.trace_events.events_sha256 "
                f"({report['trace_events']['events_sha256']!r}) "
                f"does not equal manifest subjects[1].sha256 "
                f"({subjects[1]['sha256']!r})")
    if report["binding_set"]["bindings_sha256"] != subjects[2]["sha256"]:
        return ("trace_report_binding_mismatch",
                f"report.binding_set.bindings_sha256 "
                f"({report['binding_set']['bindings_sha256']!r}) "
                f"does not equal manifest subjects[2].sha256 "
                f"({subjects[2]['sha256']!r})")
    return None


# --------------------------------------------------------------------- #
# Binding re-derivation                                                 #
# --------------------------------------------------------------------- #

def derive_expected_row(
    b: dict, events_by_id: dict[str, dict],
) -> dict:
    expected = b["expected_binding_status"]
    ev = events_by_id.get(b["required_trace_event_id"])
    if expected == "trace_gap_detected":
        return {
            "claim_id": b["claim_id"],
            "trace_event_id": b["required_trace_event_id"],
            "trace_id": b["required_trace_id"],
            "span_id": b["required_span_id"],
            "protected_action_id": b["required_protected_action_id"],
            "principal_id": b["required_principal_id"],
            "decision": "",
            "binding_status": "trace_gap_detected",
            "evidence_refs": [],
            "warning_required": True,
        }
    # bound / bound_with_warning / out_of_scope_for_trace_binding
    return {
        "claim_id": b["claim_id"],
        "trace_event_id": ev["event_id"],
        "trace_id": ev["trace_id"],
        "span_id": ev["span_id"],
        "protected_action_id": ev["protected_action_id"],
        "principal_id": ev["principal_id"],
        "decision": ev["decision"],
        "binding_status": expected,
        "evidence_refs": [f"trace-events.jsonl#{ev['event_id']}"],
        "warning_required": (expected != "bound"),
    }


def check_warning_downgrade(
    binding_set: dict,
    report: dict,
) -> tuple[str, str] | None:
    """Per Amendment 2, runs BEFORE the generic status mismatch check.

    Scans for any row whose source `expected_binding_status` is in
    NON_CLEAN_STATUSES while the report row's `binding_status` is
    `bound`, OR whose source `expected_binding_status` is in
    NON_CLEAN_STATUSES while the report row's `warning` is null.
    """
    report_by_claim = {r["claim_id"]: r for r in report["bindings"]}
    for b in binding_set["bindings"]:
        expected = b["expected_binding_status"]
        if expected not in NON_CLEAN_STATUSES:
            continue
        r = report_by_claim.get(b["claim_id"])
        if r is None:
            # Reachable only if claim_id absent; defer to status mismatch.
            continue
        if r["binding_status"] == "bound":
            return ("trace_warning_downgrade",
                    f"binding {b['claim_id']!r}: expected "
                    f"{expected!r}, report binding_status was "
                    f"downgraded to 'bound'")
        if r["warning"] is None or (
                isinstance(r["warning"], str) and not r["warning"].strip()
        ):
            return ("trace_warning_downgrade",
                    f"binding {b['claim_id']!r}: expected non-clean "
                    f"status {expected!r}, but report row 'warning' "
                    f"is missing or blank")
    return None


def check_report_rows(
    binding_set: dict,
    events_by_id: dict[str, dict],
    report: dict,
) -> tuple[str, str] | None:
    """Re-derives each row and compares. Emits
    trace_report_status_mismatch on any disagreement (except for
    warning downgrades which were already caught upstream)."""
    expected_rows = [
        derive_expected_row(b, events_by_id)
        for b in binding_set["bindings"]
    ]
    report_rows = report["bindings"]
    if len(expected_rows) != len(report_rows):
        return ("trace_report_status_mismatch",
                f"report bindings count {len(report_rows)} does not "
                f"equal binding-set rows {len(expected_rows)}")
    report_by_claim = {r["claim_id"]: r for r in report_rows}
    for exp in expected_rows:
        r = report_by_claim.get(exp["claim_id"])
        if r is None:
            return ("trace_report_status_mismatch",
                    f"binding {exp['claim_id']!r}: no matching row in "
                    f"report.bindings")
        # binding_status disagreement (non-downgrade direction):
        if r["binding_status"] != exp["binding_status"]:
            return ("trace_report_status_mismatch",
                    f"binding {exp['claim_id']!r}: report "
                    f"binding_status {r['binding_status']!r} does not "
                    f"equal expected {exp['binding_status']!r}")
        for field in ("trace_event_id", "trace_id", "span_id",
                      "protected_action_id", "principal_id",
                      "decision"):
            if r[field] != exp[field]:
                return ("trace_report_status_mismatch",
                        f"binding {exp['claim_id']!r}: report.{field} "
                        f"{r[field]!r} does not equal expected "
                        f"{exp[field]!r}")
        if r["evidence_refs"] != exp["evidence_refs"]:
            return ("trace_report_status_mismatch",
                    f"binding {exp['claim_id']!r}: report.evidence_refs "
                    f"{r['evidence_refs']!r} does not equal expected "
                    f"{exp['evidence_refs']!r}")
    return None


def check_report_counts(
    report: dict,
) -> tuple[str, str] | None:
    derived = {
        "bound_count": 0,
        "bound_with_warning_count": 0,
        "trace_gap_detected_count": 0,
        "out_of_scope_count": 0,
    }
    key = {
        "bound": "bound_count",
        "bound_with_warning": "bound_with_warning_count",
        "trace_gap_detected": "trace_gap_detected_count",
        "out_of_scope_for_trace_binding": "out_of_scope_count",
    }
    for r in report["bindings"]:
        derived[key[r["binding_status"]]] += 1
    recorded = report["binding_summary"]
    for k in derived:
        if recorded[k] != derived[k]:
            return ("trace_report_count_mismatch",
                    f"binding_summary.{k} recorded as {recorded[k]!r} "
                    f"but derived from bindings[] as {derived[k]!r}")
    bs = report["binding_set"]
    if bs["binding_count"] != len(report["bindings"]):
        return ("trace_report_count_mismatch",
                f"binding_set.binding_count recorded as "
                f"{bs['binding_count']!r} but len(bindings)="
                f"{len(report['bindings'])}")
    return None


# --------------------------------------------------------------------- #
# Main                                                                  #
# --------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("Verify a ProofRail Silver v0.3.2 trace binding "
                     "package.")
    )
    parser.add_argument("--manifest", required=True,
                        help="Path to silver-trace-binding-manifest.json")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        return usage_error(f"--manifest not found: {manifest_path}")
    package_root = manifest_path.parent

    # ---------------- Step 1: parse manifest ----------------
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return fail("invalid_trace_binding_manifest",
                    f"manifest is not valid JSON: {e}")

    # ---------------- Step 2: structural manifest validation ----------
    shape_err = validate_manifest_shape(manifest)
    if shape_err is not None:
        return fail(*shape_err)

    subjects: list[dict] = manifest["subjects"]

    # ---------------- Step 3: path traversal + path/role equality ----
    path_err = check_subject_paths_and_roles(subjects)
    if path_err is not None:
        return fail(*path_err)

    # ---------------- Step 4: subject existence and hash recompute ---
    for i, subj in enumerate(subjects):
        sp = (package_root / subj["path"]).resolve()
        # Defense in depth: ensure resolved path is under package_root.
        try:
            sp.relative_to(package_root)
        except ValueError:
            return fail("trace_subject_path_traversal",
                        f"subjects[{i}].path {subj['path']!r} resolves "
                        f"outside the package root")
        if not sp.is_file():
            return fail("trace_subject_file_missing",
                        f"subjects[{i}].path {subj['path']!r} not "
                        f"found under package root {package_root}")
        actual_sha, actual_size = sha256_label(sp)
        if actual_sha != subj["sha256"]:
            return fail("trace_subject_hash_mismatch",
                        f"subjects[{i}].sha256 recorded {subj['sha256']!r} "
                        f"but recomputed {actual_sha!r}")
        if actual_size != subj["size_bytes"]:
            return fail("trace_subject_hash_mismatch",
                        f"subjects[{i}].size_bytes recorded "
                        f"{subj['size_bytes']!r} but recomputed "
                        f"{actual_size!r}")

    adapter_path = (package_root / subjects[0]["path"]).resolve()
    events_path = (package_root / subjects[1]["path"]).resolve()
    bindings_path = (package_root / subjects[2]["path"]).resolve()
    report_path = (package_root / subjects[3]["path"]).resolve()

    # ---------------- Step 5 (Amendment 1): adapter authority pre-check
    ok, detail = adapter_source_is_not_authority(adapter_path)
    if not ok:
        return fail("trace_source_marked_authority", detail)

    # ---------------- Step 6: v0.2.6 adapter validator subprocess -----
    ok, detail = run_v0_2_6_adapter_validator(adapter_path)
    if not ok:
        return fail("trace_adapter_invalid", detail)

    # ---------------- Step 7: parse trace events ---------------------
    res = parse_trace_events(events_path)
    if res[0] is not None:
        return fail(res[0], res[1])
    events: list[dict] = res[1]

    # ---------------- Step 8: trace event uniqueness -----------------
    dup_err = check_trace_event_uniqueness(events)
    if dup_err is not None:
        return fail(*dup_err)

    # ---------------- Step 9: trace event ordering -------------------
    ord_err = check_trace_event_ordering(events)
    if ord_err is not None:
        return fail(*ord_err)

    events_by_id = {ev["event_id"]: ev for ev in events}

    # ---------------- Step 10: parse binding set ---------------------
    res2 = parse_binding_set(bindings_path)
    if res2[0] is not None:
        return fail(res2[0], res2[1])
    binding_set: dict = res2[1]

    # ---------------- Step 11: claim_id duplicates -------------------
    bdup_err = check_binding_set_duplicates(binding_set["bindings"])
    if bdup_err is not None:
        return fail(*bdup_err)

    # ---------------- Step 12: missing/mismatch/time-window ----------
    cross_err = cross_check_binding_set_against_events(
        binding_set, events_by_id
    )
    if cross_err is not None:
        return fail(*cross_err)

    # ---------------- Step 13: parse report --------------------------
    res3 = parse_report(report_path)
    if res3[0] is not None:
        return fail(res3[0], res3[1])
    report: dict = res3[1]

    # Verify trace_events.event_count and time_window match inputs.
    if report["trace_events"]["event_count"] != len(events):
        return fail("trace_report_binding_mismatch",
                    f"report.trace_events.event_count "
                    f"{report['trace_events']['event_count']!r} does "
                    f"not equal len(events) {len(events)!r}")
    tw_report = report["trace_events"]["time_window"]
    tw_bset = binding_set["trace_time_window"]
    if tw_report.get("opens_at") != tw_bset.get("opens_at") \
            or tw_report.get("closes_at") != tw_bset.get("closes_at"):
        return fail("trace_report_binding_mismatch",
                    f"report.trace_events.time_window does not equal "
                    f"binding_set.trace_time_window")
    if report["binding_set"]["binding_set_id"] \
            != binding_set["binding_set_id"]:
        return fail("trace_report_binding_mismatch",
                    f"report.binding_set.binding_set_id does not equal "
                    f"binding_set.binding_set_id")
    if report["binding_set"]["binding_count"] \
            != len(binding_set["bindings"]):
        return fail("trace_report_binding_mismatch",
                    f"report.binding_set.binding_count does not equal "
                    f"len(binding_set.bindings)")

    # ---------------- Step 14: cross-check report binding hashes -----
    bind_err = cross_check_report_binding_hashes(report, subjects)
    if bind_err is not None:
        return fail(*bind_err)

    # ---------------- Step 15 (Amendment 2): warning downgrade -------
    dgrade_err = check_warning_downgrade(binding_set, report)
    if dgrade_err is not None:
        return fail(*dgrade_err)

    # ---------------- Step 16: per-row mismatch ----------------------
    row_err = check_report_rows(binding_set, events_by_id, report)
    if row_err is not None:
        return fail(*row_err)

    # ---------------- Step 17: count recomputation -------------------
    count_err = check_report_counts(report)
    if count_err is not None:
        return fail(*count_err)

    # ---------------- Step 18: overclaim guard -----------------------
    for label, doc in (("report", report),
                       ("binding_set", binding_set)):
        over = detect_overclaim(doc)
        if over is not None:
            return fail("trace_overclaim",
                        f"{label} contains forbidden positive token "
                        f"{over!r} outside scope_limitations / "
                        f"non_claims")

    # ---------------- Step 19: limitations/non_claims emptiness ------
    for label, doc in (
        ("manifest", manifest),
        ("binding_set", binding_set),
        ("report", report),
    ):
        if not array_of_strings_non_empty(doc.get("scope_limitations")):
            return fail("trace_limitations_missing",
                        f"{label}.scope_limitations is empty or "
                        f"contains blank entries")
    for label, doc in (
        ("manifest", manifest),
        ("binding_set", binding_set),
        ("report", report),
    ):
        if not array_of_strings_non_empty(doc.get("non_claims")):
            return fail("trace_non_claims_missing",
                        f"{label}.non_claims is empty or contains "
                        f"blank entries")

    print(
        f"PASS: Silver trace binding valid "
        f"({report['trace_binding_report_id']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
