#!/usr/bin/env python3
"""Verify a ProofRail Silver v0.3.3 adapter pilot package.

Hash-first, fail-fast. The verifier:

  1.  Parses the adapter pilot manifest.
  2.  Validates manifest structural fields (document_type,
      schema_version, proofrail_release, hash_algorithm,
      adapter_pilot_report_id, generated_at, exactly seven subjects,
      scope_limitations presence/type, non_claims presence/type).
  3.  For each subject in fixed SUBJECT_ORDER:
        a. Rejects any subject path containing '..' or that is absolute
           (adapter_pilot_subject_path_traversal) BEFORE exact equality.
        b. Checks exact path and role equality
           (invalid_adapter_pilot_manifest).
        c. Checks the subject file exists
           (adapter_pilot_subject_file_missing).
        d. Recomputes SHA-256 and compares to the recorded sha256
           (adapter_pilot_subject_hash_mismatch).
  4.  Structurally rejects the adapter descriptor if
      `trust_boundary.source_is_trust_authority` is not exactly false
      (adapter_pilot_source_marked_authority). This runs BEFORE the
      generic v0.2.6 adapter validator so the reason stays directly
      reachable.
  5.  Subprocess-invokes the unchanged v0.2.6 adapter validator on
      the copied adapter descriptor (adapter_pilot_adapter_invalid).
  6.  Parses the source-export JSONL (source_export_invalid). Catches
      JSON parse errors and structural field errors; never leaks
      Python tracebacks for expected malformed-input cases.
  7.  Rejects duplicate export_record_id and duplicate
      (trace_id, span_id) (source_export_duplicate).
  8.  Rejects ordering violations on (span.start_time, export_record_id)
      ascending (source_export_time_order_invalid).
  9.  Parses the normalization map (normalization_map_invalid).
      Mapping language admits only <source.dot.path> and
      'constant:<literal>' values.
  10. Re-derives normalized trace events from the source export +
      normalization map. If any required_target_field cannot be
      resolved for any record, raises
      normalization_required_field_missing.
  11. Parses the packaged normalized trace-events.jsonl
      (normalized_trace_invalid).
  12. Per Amendment 5: compares re-derived bytes to packaged bytes
      (normalized_trace_mismatch).
  13. Subprocess-invokes the unchanged v0.3.2 verifier against
      `trace-binding/silver-trace-binding-manifest.json`
      (nested_trace_binding_invalid).
  14. Cross-checks the nested v0.3.2 manifest's subjects[0]/[1]/[2]
      hashes against the v0.3.3 manifest's subjects[0]/[3]/[4] hashes
      (nested_trace_binding_mismatch).
  15. Parses the adapter pilot report (adapter_pilot_report_invalid).
  16. Cross-checks the report's recorded hashes / paths against the
      manifest subject hashes and source format / source record count
      (adapter_pilot_report_binding_mismatch).
  17. Re-derives source_record_count and normalized_event_count
      (adapter_pilot_report_count_mismatch).
  18. Checks the required claim IDs are present
      (adapter_pilot_claim_missing).
  19. Checks every required claim has status == 'pass'
      (adapter_pilot_claim_failed).
  20. Validates evidence_refs are package-local and safe
      (adapter_pilot_evidence_ref_invalid).
  21. Re-checks manifest / report scope_limitations for emptiness or
      blank entries (adapter_pilot_limitations_missing).
  22. Re-checks manifest / report non_claims for emptiness or blank
      entries (adapter_pilot_non_claims_missing).
  23. Scans every string in the report OUTSIDE scope_limitations /
      non_claims for forbidden positive overclaim tokens
      (adapter_pilot_overclaim).

Stable failure reasons (24):

  invalid_adapter_pilot_manifest
  adapter_pilot_subject_path_traversal
  adapter_pilot_subject_file_missing
  adapter_pilot_subject_hash_mismatch
  adapter_pilot_source_marked_authority
  adapter_pilot_adapter_invalid
  source_export_invalid
  source_export_duplicate
  source_export_time_order_invalid
  normalization_map_invalid
  normalization_required_field_missing
  normalized_trace_invalid
  normalized_trace_mismatch
  nested_trace_binding_invalid
  nested_trace_binding_mismatch
  adapter_pilot_report_invalid
  adapter_pilot_report_binding_mismatch
  adapter_pilot_report_count_mismatch
  adapter_pilot_claim_missing
  adapter_pilot_claim_failed
  adapter_pilot_evidence_ref_invalid
  adapter_pilot_limitations_missing
  adapter_pilot_non_claims_missing
  adapter_pilot_overclaim

Note: adapter_validation_failed, source_export_validation_failed,
normalization_map_validation_failed, binding_set_validation_failed,
nested_trace_binding_generation_failed, and
adapter_pilot_self_validation_failed are runner-only codes (emitted
by build_silver_adapter_pilot_v0_1_0.py) and are NEVER emitted by
this verifier.

Usage:
  python3 tools/silver/verify_silver_adapter_pilot_v0_1_0.py \\
    --manifest /tmp/proofrail-silver-adapter-pilot-v0.3.3/silver-adapter-pilot-manifest.json

Exit codes:
  0 - adapter pilot package valid
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
TRACE_BINDING_VERIFIER = (
    TOOLS_DIR / "verify_silver_trace_binding_v0_1_0.py"
)

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.adapter_pilot_manifest"
REPORT_DOCUMENT_TYPE = "proofrail.silver.adapter_pilot_report"
NORMALIZATION_MAP_DOCUMENT_TYPE = (
    "proofrail.silver.adapter_pilot_normalization_map"
)
TARGET_TRACE_EVENT_DOCUMENT_TYPE = "proofrail.silver.trace_event"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.3"
HASH_ALGORITHM = "sha256"

# Fixed manifest subject layout (relative_path, role, kind). 'kind'
# is "exact" for full path equality and "prefix" for the
# adapter/<basename> case.
SUBJECT_ORDER: list[tuple[str, str, str]] = [
    ("adapter/", "adapter_descriptor", "prefix"),
    ("source/source-otel-trace-export.jsonl", "source_export", "exact"),
    ("normalization/normalization-map.json",
     "normalization_map", "exact"),
    ("normalized/trace-events.jsonl",
     "normalized_trace_events", "exact"),
    ("normalized/trace-claim-bindings.json",
     "normalized_trace_claim_bindings", "exact"),
    ("trace-binding/silver-trace-binding-manifest.json",
     "nested_trace_binding_manifest", "exact"),
    ("silver-adapter-pilot-report.json",
     "adapter_pilot_report", "exact"),
]
SUBJECT_COUNT = len(SUBJECT_ORDER)

ALLOWED_SOURCE_DECISIONS = {"allow", "deny", "observe", "block"}

REQUIRED_SOURCE_TOP_FIELDS = (
    "export_format",
    "export_record_id",
    "resource",
    "scope",
    "span",
)

REQUIRED_SOURCE_SPAN_FIELDS = (
    "trace_id",
    "span_id",
    "name",
    "start_time",
    "end_time",
    "attributes",
)

REQUIRED_SOURCE_PROOFRAIL_ATTRS = (
    "event_id",
    "principal_id",
    "protected_action_id",
    "decision",
    "decision_reason",
    "source_event_ref",
    "scenario_id",
)

REQUIRED_NORMALIZATION_MAP_TOP_FIELDS = (
    "document_type",
    "schema_version",
    "proofrail_release",
    "normalization_map_id",
    "source_format",
    "target_document_type",
    "field_mappings",
    "required_target_fields",
    "scope_limitations",
    "non_claims",
)

REQUIRED_PILOT_CLAIMS = (
    "adapter_descriptor_valid",
    "source_not_trust_authority",
    "source_export_hash_verifiable",
    "normalization_map_valid",
    "normalized_trace_events_rederived",
    "nested_trace_binding_valid",
    "no_runtime_truth_claimed",
)

ALLOWED_PACKAGE_LOCAL_PREFIXES = (
    "adapter/",
    "source/",
    "normalization/",
    "normalized/",
    "trace-binding/",
    "silver-adapter-pilot-report.json",
)

# Forbidden positive overclaim tokens (case-insensitive substring
# match). Aligned with the v0.3.2 verifier list.
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
    "runtime truth proved",
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
    sys.stderr.write(f"FAIL: usage_error: {msg}\n")
    return 2


def fail(reason: str, detail: str) -> int:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
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


def get_dot_path(obj: Any, dot_path: str) -> tuple[bool, Any]:
    """Resolve a dot-path with longest-prefix key match at each step.

    Mirrors build_silver_adapter_pilot_v0_1_0.get_dot_path so the
    verifier re-derives the same normalized events as the runner.
    """
    parts = dot_path.split(".")
    cur: Any = obj
    i = 0
    while i < len(parts):
        if not isinstance(cur, dict):
            return False, None
        matched = False
        for end in range(len(parts), i, -1):
            key = ".".join(parts[i:end])
            if key in cur:
                cur = cur[key]
                i = end
                matched = True
                break
        if not matched:
            return False, None
    return True, cur


def set_dot_path(target: dict, dot_path: str, value: Any) -> None:
    parts = dot_path.split(".")
    cur = target
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


# --------------------------------------------------------------------- #
# Manifest validation                                                   #
# --------------------------------------------------------------------- #

def validate_manifest_shape(
    manifest: Any,
) -> tuple[str, str] | None:
    if not isinstance(manifest, dict):
        return ("invalid_adapter_pilot_manifest",
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
            return ("invalid_adapter_pilot_manifest",
                    f"{k} must be {expected!r}, got {v!r}")
    if not non_empty_str(manifest.get("adapter_pilot_report_id")):
        return ("invalid_adapter_pilot_manifest",
                "adapter_pilot_report_id must be a non-empty string")
    if parse_iso_8601_z(manifest.get("generated_at")) is None:
        return ("invalid_adapter_pilot_manifest",
                "generated_at must be ISO-8601 UTC Z-suffixed")
    subjects = manifest.get("subjects")
    if not isinstance(subjects, list):
        return ("invalid_adapter_pilot_manifest",
                "subjects must be an array")
    if len(subjects) != SUBJECT_COUNT:
        return ("invalid_adapter_pilot_manifest",
                f"subjects must contain exactly {SUBJECT_COUNT} "
                f"entries, got {len(subjects)}")
    for i, subj in enumerate(subjects):
        if not isinstance(subj, dict):
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}] is not a JSON object")
        for k in ("path", "role", "sha256", "size_bytes"):
            if k not in subj:
                return ("invalid_adapter_pilot_manifest",
                        f"subjects[{i}] missing required field '{k}'")
        if not non_empty_str(subj["path"]):
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}].path must be a non-empty string")
        if not non_empty_str(subj["role"]):
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}].role must be a non-empty string")
        sha = subj["sha256"]
        if not isinstance(sha, str) or not sha.startswith("sha256:") \
                or len(sha) != len("sha256:") + 64:
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}].sha256 must be 'sha256:<64 hex>'")
        if not isinstance(subj["size_bytes"], int) \
                or subj["size_bytes"] < 0:
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}].size_bytes must be a non-negative "
                    f"integer")
    if not array_of_strings_present(manifest.get("scope_limitations")):
        return ("invalid_adapter_pilot_manifest",
                "scope_limitations must be an array of strings")
    if not array_of_strings_present(manifest.get("non_claims")):
        return ("invalid_adapter_pilot_manifest",
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
            return ("adapter_pilot_subject_path_traversal",
                    f"subjects[{i}].path {subj['path']!r} is absolute "
                    f"or contains '..'")
    # Step B: exact path / role equality.
    for i, subj in enumerate(subjects):
        expected, expected_role, kind = SUBJECT_ORDER[i]
        path = subj["path"]
        role = subj["role"]
        if kind == "prefix":
            # adapter subject lives under adapter/<filename> (exactly
            # one component after the prefix).
            if not path.startswith(expected) or path == expected:
                return ("invalid_adapter_pilot_manifest",
                        f"subjects[{i}].path must be under "
                        f"{expected!r}, got {path!r}")
            remainder = path[len(expected):]
            if "/" in remainder:
                return ("invalid_adapter_pilot_manifest",
                        f"subjects[{i}].path must be exactly "
                        f"{expected}<filename>, got {path!r}")
        else:
            if path != expected:
                return ("invalid_adapter_pilot_manifest",
                        f"subjects[{i}].path must be {expected!r}, "
                        f"got {path!r}")
        if role != expected_role:
            return ("invalid_adapter_pilot_manifest",
                    f"subjects[{i}].role must be {expected_role!r}, "
                    f"got {role!r}")
    return None


# --------------------------------------------------------------------- #
# Adapter checks                                                        #
# --------------------------------------------------------------------- #

def adapter_source_is_not_authority(
    adapter_path: Path,
) -> tuple[bool, str]:
    """Runs BEFORE the generic v0.2.6 validator so the reason
    `adapter_pilot_source_marked_authority` stays directly reachable."""
    try:
        doc = json.loads(adapter_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
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
# Source export                                                         #
# --------------------------------------------------------------------- #

def parse_source_export(
    p: Path,
) -> tuple[str, str] | tuple[None, list[dict]]:
    records: list[dict] = []
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return ("source_export_invalid",
                f"could not read source export: {e}")
    lines = text.splitlines()
    if not lines:
        return ("source_export_invalid", "source export is empty")
    for line_no, line in enumerate(lines, start=1):
        if line == "":
            return ("source_export_invalid",
                    f"line {line_no} is blank or whitespace-only")
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            return ("source_export_invalid",
                    f"line {line_no} JSON parse error: {e}")
        if not isinstance(obj, dict):
            return ("source_export_invalid",
                    f"line {line_no} is not a JSON object")
        for f in REQUIRED_SOURCE_TOP_FIELDS:
            if f not in obj:
                return ("source_export_invalid",
                        f"line {line_no} missing required field {f!r}")
        if not non_empty_str(obj["export_format"]):
            return ("source_export_invalid",
                    f"line {line_no} export_format is empty")
        if not non_empty_str(obj["export_record_id"]):
            return ("source_export_invalid",
                    f"line {line_no} export_record_id is empty")
        if not isinstance(obj["resource"], dict):
            return ("source_export_invalid",
                    f"line {line_no} resource is not an object")
        if not isinstance(obj["scope"], dict):
            return ("source_export_invalid",
                    f"line {line_no} scope is not an object")
        span = obj["span"]
        if not isinstance(span, dict):
            return ("source_export_invalid",
                    f"line {line_no} span is not an object")
        for f in REQUIRED_SOURCE_SPAN_FIELDS:
            if f not in span:
                return ("source_export_invalid",
                        f"line {line_no} span missing required field "
                        f"{f!r}")
        if not non_empty_str(span["trace_id"]):
            return ("source_export_invalid",
                    f"line {line_no} span.trace_id is empty")
        if not non_empty_str(span["span_id"]):
            return ("source_export_invalid",
                    f"line {line_no} span.span_id is empty")
        if not non_empty_str(span["name"]):
            return ("source_export_invalid",
                    f"line {line_no} span.name is empty")
        if parse_iso_8601_z(span["start_time"]) is None:
            return ("source_export_invalid",
                    f"line {line_no} span.start_time is not ISO-8601 "
                    f"UTC Z-suffixed")
        if parse_iso_8601_z(span["end_time"]) is None:
            return ("source_export_invalid",
                    f"line {line_no} span.end_time is not ISO-8601 "
                    f"UTC Z-suffixed")
        if not isinstance(span["attributes"], dict):
            return ("source_export_invalid",
                    f"line {line_no} span.attributes is not an object")
        attrs = span["attributes"]
        for k in REQUIRED_SOURCE_PROOFRAIL_ATTRS:
            full = f"proofrail.{k}"
            if full not in attrs:
                return ("source_export_invalid",
                        f"line {line_no} span.attributes missing "
                        f"required field {full!r}")
            if not non_empty_str(attrs[full]):
                return ("source_export_invalid",
                        f"line {line_no} span.attributes[{full!r}] "
                        f"is empty")
        decision = attrs["proofrail.decision"]
        if decision not in ALLOWED_SOURCE_DECISIONS:
            return ("source_export_invalid",
                    f"line {line_no} "
                    f"span.attributes['proofrail.decision'] "
                    f"{decision!r} is not in "
                    f"{sorted(ALLOWED_SOURCE_DECISIONS)}")
        records.append(obj)
    return (None, records)


def check_source_uniqueness(
    records: list[dict],
) -> tuple[str, str] | None:
    seen_rid: dict[str, int] = {}
    seen_span: dict[tuple[str, str], int] = {}
    for i, rec in enumerate(records):
        rid = rec["export_record_id"]
        if rid in seen_rid:
            return ("source_export_duplicate",
                    f"duplicate export_record_id {rid!r} (first at "
                    f"index {seen_rid[rid]}, again at index {i})")
        seen_rid[rid] = i
        ts = (rec["span"]["trace_id"], rec["span"]["span_id"])
        if ts in seen_span:
            return ("source_export_duplicate",
                    f"duplicate (trace_id, span_id) {ts!r} (first at "
                    f"index {seen_span[ts]}, again at index {i})")
        seen_span[ts] = i
    return None


def check_source_ordering(
    records: list[dict],
) -> tuple[str, str] | None:
    prev_key: tuple[str, str] | None = None
    for i, rec in enumerate(records):
        key = (rec["span"]["start_time"], rec["export_record_id"])
        if prev_key is not None and key <= prev_key:
            return ("source_export_time_order_invalid",
                    f"source export not strictly ascending by "
                    f"(span.start_time, export_record_id) between "
                    f"index {i - 1} and {i}: {prev_key!r} -> "
                    f"{key!r}")
        prev_key = key
    return None


# --------------------------------------------------------------------- #
# Normalization map                                                     #
# --------------------------------------------------------------------- #

def parse_normalization_map(
    p: Path,
) -> tuple[str, str] | tuple[None, dict]:
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return ("normalization_map_invalid",
                f"could not read normalization map: {e}")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return ("normalization_map_invalid",
                f"normalization map JSON parse error: {e}")
    if not isinstance(doc, dict):
        return ("normalization_map_invalid",
                "normalization map is not a JSON object")
    for f in REQUIRED_NORMALIZATION_MAP_TOP_FIELDS:
        if f not in doc:
            return ("normalization_map_invalid",
                    f"missing required field {f!r}")
    if doc["document_type"] != NORMALIZATION_MAP_DOCUMENT_TYPE:
        return ("normalization_map_invalid",
                f"document_type must be "
                f"{NORMALIZATION_MAP_DOCUMENT_TYPE!r}, got "
                f"{doc['document_type']!r}")
    if doc["schema_version"] != SCHEMA_VERSION:
        return ("normalization_map_invalid",
                f"schema_version must be {SCHEMA_VERSION!r}, got "
                f"{doc['schema_version']!r}")
    if doc["proofrail_release"] != PROOFRAIL_RELEASE:
        return ("normalization_map_invalid",
                f"proofrail_release must be {PROOFRAIL_RELEASE!r}, "
                f"got {doc['proofrail_release']!r}")
    if not non_empty_str(doc["normalization_map_id"]):
        return ("normalization_map_invalid",
                "normalization_map_id is empty")
    if not non_empty_str(doc["source_format"]):
        return ("normalization_map_invalid", "source_format is empty")
    if doc["target_document_type"] != TARGET_TRACE_EVENT_DOCUMENT_TYPE:
        return ("normalization_map_invalid",
                f"target_document_type must be "
                f"{TARGET_TRACE_EVENT_DOCUMENT_TYPE!r}, got "
                f"{doc['target_document_type']!r}")
    fm = doc["field_mappings"]
    if not isinstance(fm, dict) or not fm:
        return ("normalization_map_invalid",
                "field_mappings must be a non-empty JSON object")
    for tgt_key, mapping_value in fm.items():
        if not non_empty_str(tgt_key):
            return ("normalization_map_invalid",
                    f"field_mappings target key {tgt_key!r} is empty")
        if any(p == "" for p in tgt_key.split(".")):
            return ("normalization_map_invalid",
                    f"field_mappings target key {tgt_key!r} contains "
                    f"empty dot component")
        if not isinstance(mapping_value, str):
            return ("normalization_map_invalid",
                    f"field_mappings[{tgt_key!r}] mapping value must "
                    f"be a string, got "
                    f"{type(mapping_value).__name__}")
        if mapping_value.startswith("constant:"):
            continue
        if not non_empty_str(mapping_value):
            return ("normalization_map_invalid",
                    f"field_mappings[{tgt_key!r}] mapping value is "
                    f"empty")
        if any(p == "" for p in mapping_value.split(".")):
            return ("normalization_map_invalid",
                    f"field_mappings[{tgt_key!r}] source dot-path "
                    f"{mapping_value!r} contains empty dot component")
    rtf = doc["required_target_fields"]
    if not isinstance(rtf, list) or not rtf:
        return ("normalization_map_invalid",
                "required_target_fields must be a non-empty array")
    for entry in rtf:
        if not non_empty_str(entry):
            return ("normalization_map_invalid",
                    f"required_target_fields entry {entry!r} is empty")
    if not isinstance(doc["scope_limitations"], list):
        return ("normalization_map_invalid",
                "scope_limitations must be an array")
    if not isinstance(doc["non_claims"], list):
        return ("normalization_map_invalid",
                "non_claims must be an array")
    return (None, doc)


# --------------------------------------------------------------------- #
# Normalization derivation                                              #
# --------------------------------------------------------------------- #

def derive_normalized_events(
    source_records: list[dict],
    normalization_map: dict,
) -> tuple[str, str] | tuple[None, list[dict]]:
    fm = normalization_map["field_mappings"]
    required_targets = set(normalization_map["required_target_fields"])
    out: list[dict] = []
    for idx, rec in enumerate(source_records, start=1):
        if rec.get("export_format") != normalization_map["source_format"]:
            return ("normalization_required_field_missing",
                    f"line {idx} export_format "
                    f"{rec.get('export_format')!r} does not equal "
                    f"normalization_map.source_format "
                    f"{normalization_map['source_format']!r}")
        ev: dict = {}
        for tgt_key, mapping_value in fm.items():
            if mapping_value.startswith("constant:"):
                literal = mapping_value[len("constant:"):]
                set_dot_path(ev, tgt_key, literal)
                continue
            found, value = get_dot_path(rec, mapping_value)
            if not found:
                top = tgt_key.split(".")[0]
                if tgt_key in required_targets \
                        or top in required_targets:
                    return ("normalization_required_field_missing",
                            f"line {idx} source field "
                            f"{mapping_value!r} not present; required "
                            f"target field {tgt_key!r} cannot be "
                            f"populated")
                continue
            set_dot_path(ev, tgt_key, value)
        for rt in normalization_map["required_target_fields"]:
            found, val = get_dot_path(ev, rt)
            if not found:
                return ("normalization_required_field_missing",
                        f"line {idx} required target field {rt!r} is "
                        f"missing after normalization")
        out.append(ev)
    return (None, out)


def serialize_normalized_events_jsonl(events: list[dict]) -> bytes:
    buf: list[str] = []
    for ev in events:
        buf.append(json.dumps(ev, sort_keys=True, separators=(",", ":")))
    return ("\n".join(buf) + "\n").encode("utf-8")


def parse_normalized_packaged(
    p: Path,
) -> tuple[str, str] | tuple[None, list[dict], bytes]:
    try:
        raw = p.read_bytes()
    except OSError as e:
        return ("normalized_trace_invalid",
                f"could not read normalized trace events: {e}")
    if not raw:
        return ("normalized_trace_invalid",
                "normalized trace events file is empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return ("normalized_trace_invalid",
                f"normalized trace events not valid UTF-8: {e}")
    lines = text.splitlines()
    events: list[dict] = []
    for line_no, line in enumerate(lines, start=1):
        if line == "":
            return ("normalized_trace_invalid",
                    f"normalized line {line_no} is blank")
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            return ("normalized_trace_invalid",
                    f"normalized line {line_no} JSON parse error: {e}")
        if not isinstance(obj, dict):
            return ("normalized_trace_invalid",
                    f"normalized line {line_no} is not a JSON object")
        events.append(obj)
    return (None, events, raw)


# --------------------------------------------------------------------- #
# Nested v0.3.2 verifier                                                #
# --------------------------------------------------------------------- #

def run_nested_v0_3_2_verifier(
    nested_manifest_path: Path,
) -> tuple[bool, str]:
    if not TRACE_BINDING_VERIFIER.exists():
        return False, (
            f"v0.3.2 trace binding verifier not found at "
            f"{TRACE_BINDING_VERIFIER}"
        )
    try:
        proc = subprocess.run(
            [sys.executable, str(TRACE_BINDING_VERIFIER),
             "--manifest", str(nested_manifest_path)],
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


def cross_check_nested_subject_hashes(
    nested_manifest_path: Path,
    outer_subjects: list[dict],
) -> tuple[str, str] | None:
    """Compare nested v0.3.2 manifest subjects[0]/[1]/[2] against
    outer v0.3.3 manifest subjects[0]/[3]/[4] by SHA-256."""
    try:
        nested = json.loads(nested_manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return ("nested_trace_binding_mismatch",
                f"could not parse nested manifest: {e}")
    if not isinstance(nested, dict):
        return ("nested_trace_binding_mismatch",
                "nested manifest is not a JSON object")
    nested_subjects = nested.get("subjects")
    if not isinstance(nested_subjects, list) \
            or len(nested_subjects) < 3:
        return ("nested_trace_binding_mismatch",
                f"nested manifest subjects must be an array of at "
                f"least 3 entries, got "
                f"{len(nested_subjects) if isinstance(nested_subjects, list) else type(nested_subjects).__name__}")
    pairs = [
        (0, 0, "adapter descriptor"),
        (1, 3, "normalized trace events"),
        (2, 4, "normalized trace claim binding set"),
    ]
    for nested_idx, outer_idx, label in pairs:
        nsubj = nested_subjects[nested_idx]
        if not isinstance(nsubj, dict) or "sha256" not in nsubj:
            return ("nested_trace_binding_mismatch",
                    f"nested subjects[{nested_idx}] missing 'sha256'")
        if nsubj["sha256"] != outer_subjects[outer_idx]["sha256"]:
            return ("nested_trace_binding_mismatch",
                    f"{label}: nested subjects[{nested_idx}].sha256 "
                    f"{nsubj['sha256']!r} does not equal outer "
                    f"subjects[{outer_idx}].sha256 "
                    f"{outer_subjects[outer_idx]['sha256']!r}")
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
        return ("adapter_pilot_report_invalid",
                f"report is not valid JSON: {e}")
    if not isinstance(doc, dict):
        return ("adapter_pilot_report_invalid",
                "report is not a JSON object")
    expected_fields = {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
    }
    for k, expected in expected_fields.items():
        v = doc.get(k)
        if v != expected:
            return ("adapter_pilot_report_invalid",
                    f"{k} must be {expected!r}, got {v!r}")
    if not non_empty_str(doc.get("adapter_pilot_report_id")):
        return ("adapter_pilot_report_invalid",
                "adapter_pilot_report_id must be a non-empty string")
    if parse_iso_8601_z(doc.get("generated_at")) is None:
        return ("adapter_pilot_report_invalid",
                "generated_at must be ISO-8601 UTC Z-suffixed")
    adapter = doc.get("adapter")
    if not isinstance(adapter, dict):
        return ("adapter_pilot_report_invalid",
                "adapter must be an object")
    if not non_empty_str(adapter.get("adapter_path")) \
            or has_path_traversal(adapter["adapter_path"]):
        return ("adapter_pilot_report_invalid",
                "adapter.adapter_path must be a safe relative path")
    if not isinstance(adapter.get("adapter_sha256"), str) \
            or not adapter["adapter_sha256"].startswith("sha256:"):
        return ("adapter_pilot_report_invalid",
                "adapter.adapter_sha256 must be 'sha256:<hex>'")
    if adapter.get("source_is_trust_authority") is not False:
        return ("adapter_pilot_report_invalid",
                "adapter.source_is_trust_authority must be exactly "
                f"false, got {adapter.get('source_is_trust_authority')!r}")
    se = doc.get("source_export")
    if not isinstance(se, dict):
        return ("adapter_pilot_report_invalid",
                "source_export must be an object")
    if not non_empty_str(se.get("source_export_path")) \
            or has_path_traversal(se["source_export_path"]):
        return ("adapter_pilot_report_invalid",
                "source_export.source_export_path must be a safe "
                "relative path")
    if not isinstance(se.get("source_export_sha256"), str) \
            or not se["source_export_sha256"].startswith("sha256:"):
        return ("adapter_pilot_report_invalid",
                "source_export.source_export_sha256 must be "
                "'sha256:<hex>'")
    if not isinstance(se.get("source_record_count"), int) \
            or se["source_record_count"] < 1:
        return ("adapter_pilot_report_invalid",
                "source_export.source_record_count must be an integer "
                ">= 1")
    if not non_empty_str(se.get("source_format")):
        return ("adapter_pilot_report_invalid",
                "source_export.source_format must be a non-empty string")
    nm = doc.get("normalization")
    if not isinstance(nm, dict):
        return ("adapter_pilot_report_invalid",
                "normalization must be an object")
    if not non_empty_str(nm.get("normalization_map_path")) \
            or has_path_traversal(nm["normalization_map_path"]):
        return ("adapter_pilot_report_invalid",
                "normalization.normalization_map_path must be a safe "
                "relative path")
    if not isinstance(nm.get("normalization_map_sha256"), str) \
            or not nm["normalization_map_sha256"].startswith("sha256:"):
        return ("adapter_pilot_report_invalid",
                "normalization.normalization_map_sha256 must be "
                "'sha256:<hex>'")
    if not non_empty_str(nm.get("normalized_trace_events_path")) \
            or has_path_traversal(nm["normalized_trace_events_path"]):
        return ("adapter_pilot_report_invalid",
                "normalization.normalized_trace_events_path must be a "
                "safe relative path")
    if not isinstance(nm.get("normalized_trace_events_sha256"), str) \
            or not nm["normalized_trace_events_sha256"].startswith(
                "sha256:"):
        return ("adapter_pilot_report_invalid",
                "normalization.normalized_trace_events_sha256 must be "
                "'sha256:<hex>'")
    if not isinstance(nm.get("normalized_event_count"), int) \
            or nm["normalized_event_count"] < 1:
        return ("adapter_pilot_report_invalid",
                "normalization.normalized_event_count must be an "
                "integer >= 1")
    ntb = doc.get("nested_trace_binding")
    if not isinstance(ntb, dict):
        return ("adapter_pilot_report_invalid",
                "nested_trace_binding must be an object")
    if not non_empty_str(ntb.get("manifest_path")) \
            or has_path_traversal(ntb["manifest_path"]):
        return ("adapter_pilot_report_invalid",
                "nested_trace_binding.manifest_path must be a safe "
                "relative path")
    if not isinstance(ntb.get("manifest_sha256"), str) \
            or not ntb["manifest_sha256"].startswith("sha256:"):
        return ("adapter_pilot_report_invalid",
                "nested_trace_binding.manifest_sha256 must be "
                "'sha256:<hex>'")
    if ntb.get("verification_status") != "pass":
        return ("adapter_pilot_report_invalid",
                f"nested_trace_binding.verification_status must be "
                f"'pass', got {ntb.get('verification_status')!r}")
    ps = doc.get("pilot_summary")
    if not isinstance(ps, dict):
        return ("adapter_pilot_report_invalid",
                "pilot_summary must be an object")
    if ps.get("source_is_trust_authority") is not False:
        return ("adapter_pilot_report_invalid",
                f"pilot_summary.source_is_trust_authority must be "
                f"exactly false, got "
                f"{ps.get('source_is_trust_authority')!r}")
    if ps.get("normalization_status") != "pass":
        return ("adapter_pilot_report_invalid",
                f"pilot_summary.normalization_status must be 'pass', "
                f"got {ps.get('normalization_status')!r}")
    if ps.get("nested_trace_binding_status") != "pass":
        return ("adapter_pilot_report_invalid",
                f"pilot_summary.nested_trace_binding_status must be "
                f"'pass', got "
                f"{ps.get('nested_trace_binding_status')!r}")
    if ps.get("normalized_events_match_source") is not True:
        return ("adapter_pilot_report_invalid",
                f"pilot_summary.normalized_events_match_source must "
                f"be exactly true, got "
                f"{ps.get('normalized_events_match_source')!r}")
    if ps.get("runtime_truth_claimed") is not False:
        return ("adapter_pilot_report_invalid",
                f"pilot_summary.runtime_truth_claimed must be exactly "
                f"false, got {ps.get('runtime_truth_claimed')!r}")
    claims = doc.get("claims")
    if not isinstance(claims, list) or not claims:
        return ("adapter_pilot_report_invalid",
                "claims must be a non-empty array")
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            return ("adapter_pilot_report_invalid",
                    f"claims[{i}] is not a JSON object")
        for k in ("claim_id", "status", "evidence_refs"):
            if k not in c:
                return ("adapter_pilot_report_invalid",
                        f"claims[{i}] missing required field {k!r}")
        if not non_empty_str(c["claim_id"]):
            return ("adapter_pilot_report_invalid",
                    f"claims[{i}].claim_id must be a non-empty string")
        if not non_empty_str(c["status"]):
            return ("adapter_pilot_report_invalid",
                    f"claims[{i}].status must be a non-empty string")
        if not isinstance(c["evidence_refs"], list):
            return ("adapter_pilot_report_invalid",
                    f"claims[{i}].evidence_refs must be an array")
    if not array_of_strings_present(doc.get("scope_limitations")):
        return ("adapter_pilot_report_invalid",
                "scope_limitations must be an array of strings")
    if not array_of_strings_present(doc.get("non_claims")):
        return ("adapter_pilot_report_invalid",
                "non_claims must be an array of strings")
    return (None, doc)


def cross_check_report_bindings(
    report: dict,
    subjects: list[dict],
    source_format_from_map: str,
    source_record_count_from_source: int,
    normalized_event_count_from_derive: int,
) -> tuple[str, str] | None:
    if report["adapter"]["adapter_sha256"] != subjects[0]["sha256"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.adapter.adapter_sha256 "
                f"({report['adapter']['adapter_sha256']!r}) does not "
                f"equal manifest subjects[0].sha256 "
                f"({subjects[0]['sha256']!r})")
    if report["adapter"]["adapter_path"] != subjects[0]["path"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.adapter.adapter_path "
                f"({report['adapter']['adapter_path']!r}) does not "
                f"equal manifest subjects[0].path "
                f"({subjects[0]['path']!r})")
    if report["source_export"]["source_export_sha256"] \
            != subjects[1]["sha256"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.source_export.source_export_sha256 "
                f"({report['source_export']['source_export_sha256']!r}) "
                f"does not equal manifest subjects[1].sha256 "
                f"({subjects[1]['sha256']!r})")
    if report["source_export"]["source_export_path"] \
            != subjects[1]["path"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.source_export.source_export_path "
                f"({report['source_export']['source_export_path']!r}) "
                f"does not equal manifest subjects[1].path "
                f"({subjects[1]['path']!r})")
    if report["normalization"]["normalization_map_sha256"] \
            != subjects[2]["sha256"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.normalization.normalization_map_sha256 "
                f"does not equal manifest subjects[2].sha256")
    if report["normalization"]["normalization_map_path"] \
            != subjects[2]["path"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.normalization.normalization_map_path does "
                f"not equal manifest subjects[2].path")
    if report["normalization"]["normalized_trace_events_sha256"] \
            != subjects[3]["sha256"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.normalization.normalized_trace_events_sha256 "
                f"does not equal manifest subjects[3].sha256")
    if report["normalization"]["normalized_trace_events_path"] \
            != subjects[3]["path"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.normalization.normalized_trace_events_path "
                f"does not equal manifest subjects[3].path")
    if report["nested_trace_binding"]["manifest_sha256"] \
            != subjects[5]["sha256"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.nested_trace_binding.manifest_sha256 does "
                f"not equal manifest subjects[5].sha256")
    if report["nested_trace_binding"]["manifest_path"] \
            != subjects[5]["path"]:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.nested_trace_binding.manifest_path does not "
                f"equal manifest subjects[5].path")
    if report["source_export"]["source_format"] \
            != source_format_from_map:
        return ("adapter_pilot_report_binding_mismatch",
                f"report.source_export.source_format "
                f"({report['source_export']['source_format']!r}) "
                f"does not equal normalization map source_format "
                f"({source_format_from_map!r})")
    return None


def check_report_counts(
    report: dict,
    source_record_count: int,
    normalized_event_count: int,
) -> tuple[str, str] | None:
    if report["source_export"]["source_record_count"] \
            != source_record_count:
        return ("adapter_pilot_report_count_mismatch",
                f"report.source_export.source_record_count "
                f"({report['source_export']['source_record_count']!r}) "
                f"does not equal derived count "
                f"({source_record_count!r})")
    if report["normalization"]["normalized_event_count"] \
            != normalized_event_count:
        return ("adapter_pilot_report_count_mismatch",
                f"report.normalization.normalized_event_count "
                f"({report['normalization']['normalized_event_count']!r}) "
                f"does not equal derived count "
                f"({normalized_event_count!r})")
    return None


def check_required_claims(
    report: dict,
) -> tuple[str, str] | None:
    by_id = {c["claim_id"]: c for c in report["claims"]}
    for cid in REQUIRED_PILOT_CLAIMS:
        if cid not in by_id:
            return ("adapter_pilot_claim_missing",
                    f"required claim {cid!r} is missing from "
                    f"report.claims")
    for cid in REQUIRED_PILOT_CLAIMS:
        c = by_id[cid]
        if c["status"] != "pass":
            return ("adapter_pilot_claim_failed",
                    f"required claim {cid!r} status is "
                    f"{c['status']!r}, expected 'pass'")
    return None


def check_evidence_refs(
    report: dict,
) -> tuple[str, str] | None:
    for i, c in enumerate(report["claims"]):
        refs = c["evidence_refs"]
        for j, ref in enumerate(refs):
            if not isinstance(ref, str) or not ref:
                return ("adapter_pilot_evidence_ref_invalid",
                        f"claims[{i}].evidence_refs[{j}] must be a "
                        f"non-empty string")
            head = ref.split("#", 1)[0]
            if has_path_traversal(head):
                return ("adapter_pilot_evidence_ref_invalid",
                        f"claims[{i}].evidence_refs[{j}] {ref!r} is "
                        f"absolute or contains '..'")
            if not any(
                head == p or head.startswith(p)
                for p in ALLOWED_PACKAGE_LOCAL_PREFIXES
            ):
                return ("adapter_pilot_evidence_ref_invalid",
                        f"claims[{i}].evidence_refs[{j}] {ref!r} is "
                        f"not under a recognized package-local "
                        f"location")
    return None


# --------------------------------------------------------------------- #
# Main                                                                  #
# --------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("Verify a ProofRail Silver v0.3.3 adapter pilot "
                     "package.")
    )
    parser.add_argument("--manifest", required=True,
                        help="Path to silver-adapter-pilot-manifest.json")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        return usage_error(f"--manifest not found: {manifest_path}")
    package_root = manifest_path.parent

    # ---------------- Step 1: parse manifest ----------------
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return fail("invalid_adapter_pilot_manifest",
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
        try:
            sp.relative_to(package_root)
        except ValueError:
            return fail("adapter_pilot_subject_path_traversal",
                        f"subjects[{i}].path {subj['path']!r} resolves "
                        f"outside the package root")
        if not sp.is_file():
            return fail("adapter_pilot_subject_file_missing",
                        f"subjects[{i}].path {subj['path']!r} not "
                        f"found under package root {package_root}")
        actual_sha, actual_size = sha256_label(sp)
        if actual_sha != subj["sha256"]:
            return fail("adapter_pilot_subject_hash_mismatch",
                        f"subjects[{i}].sha256 recorded "
                        f"{subj['sha256']!r} but recomputed "
                        f"{actual_sha!r}")
        if actual_size != subj["size_bytes"]:
            return fail("adapter_pilot_subject_hash_mismatch",
                        f"subjects[{i}].size_bytes recorded "
                        f"{subj['size_bytes']!r} but recomputed "
                        f"{actual_size!r}")

    adapter_path = (package_root / subjects[0]["path"]).resolve()
    source_path = (package_root / subjects[1]["path"]).resolve()
    norm_map_path = (package_root / subjects[2]["path"]).resolve()
    norm_events_path = (package_root / subjects[3]["path"]).resolve()
    norm_bindings_path = (package_root / subjects[4]["path"]).resolve()
    nested_manifest_path = (
        package_root / subjects[5]["path"]
    ).resolve()
    report_path = (package_root / subjects[6]["path"]).resolve()
    _ = norm_bindings_path  # not used directly here

    # ---------------- Step 5: adapter authority pre-check ------------
    ok, detail = adapter_source_is_not_authority(adapter_path)
    if not ok:
        return fail("adapter_pilot_source_marked_authority", detail)

    # ---------------- Step 6: v0.2.6 adapter validator subprocess -----
    ok, detail = run_v0_2_6_adapter_validator(adapter_path)
    if not ok:
        return fail("adapter_pilot_adapter_invalid", detail)

    # ---------------- Step 7: parse source export --------------------
    res = parse_source_export(source_path)
    if res[0] is not None:
        return fail(res[0], res[1])
    source_records: list[dict] = res[1]

    # ---------------- Step 8: source uniqueness ----------------------
    dup_err = check_source_uniqueness(source_records)
    if dup_err is not None:
        return fail(*dup_err)

    # ---------------- Step 9: source ordering ------------------------
    ord_err = check_source_ordering(source_records)
    if ord_err is not None:
        return fail(*ord_err)

    # ---------------- Step 10: parse normalization map ---------------
    res2 = parse_normalization_map(norm_map_path)
    if res2[0] is not None:
        return fail(res2[0], res2[1])
    norm_map: dict = res2[1]

    # ---------------- Step 11: re-derive normalized events -----------
    res3 = derive_normalized_events(source_records, norm_map)
    if res3[0] is not None:
        return fail(res3[0], res3[1])
    derived_events: list[dict] = res3[1]
    derived_bytes = serialize_normalized_events_jsonl(derived_events)

    # ---------------- Step 12: parse packaged normalized events ------
    res4 = parse_normalized_packaged(norm_events_path)
    if res4[0] is not None:
        return fail(res4[0], res4[1])
    _packaged_events: list[dict] = res4[1]
    packaged_bytes: bytes = res4[2]

    # ---------------- Step 13: re-derived equals packaged ------------
    if derived_bytes != packaged_bytes:
        return fail("normalized_trace_mismatch",
                    f"re-derived normalized trace events bytes "
                    f"(len {len(derived_bytes)}) do not equal "
                    f"packaged normalized trace events bytes "
                    f"(len {len(packaged_bytes)})")

    # ---------------- Step 14: nested v0.3.2 verifier subprocess -----
    ok, detail = run_nested_v0_3_2_verifier(nested_manifest_path)
    if not ok:
        return fail("nested_trace_binding_invalid", detail)

    # ---------------- Step 15: nested subject hash cross-check -------
    nested_err = cross_check_nested_subject_hashes(
        nested_manifest_path, subjects
    )
    if nested_err is not None:
        return fail(*nested_err)

    # ---------------- Step 16: parse report --------------------------
    res5 = parse_report(report_path)
    if res5[0] is not None:
        return fail(res5[0], res5[1])
    report: dict = res5[1]

    # ---------------- Step 17: report binding cross-check ------------
    bind_err = cross_check_report_bindings(
        report,
        subjects,
        source_format_from_map=norm_map["source_format"],
        source_record_count_from_source=len(source_records),
        normalized_event_count_from_derive=len(derived_events),
    )
    if bind_err is not None:
        return fail(*bind_err)

    # ---------------- Step 18: report count recomputation ------------
    cnt_err = check_report_counts(
        report,
        source_record_count=len(source_records),
        normalized_event_count=len(derived_events),
    )
    if cnt_err is not None:
        return fail(*cnt_err)

    # ---------------- Step 19: required claim IDs present ------------
    # ---------------- Step 20: required claim status=pass ------------
    claim_err = check_required_claims(report)
    if claim_err is not None:
        return fail(*claim_err)

    # ---------------- Step 21: evidence refs package-local -----------
    ref_err = check_evidence_refs(report)
    if ref_err is not None:
        return fail(*ref_err)

    # ---------------- Step 22: limitations non-empty -----------------
    for label, doc in (("manifest", manifest), ("report", report)):
        if not array_of_strings_non_empty(doc.get("scope_limitations")):
            return fail("adapter_pilot_limitations_missing",
                        f"{label}.scope_limitations is empty or "
                        f"contains blank entries")

    # ---------------- Step 23: non_claims non-empty ------------------
    for label, doc in (("manifest", manifest), ("report", report)):
        if not array_of_strings_non_empty(doc.get("non_claims")):
            return fail("adapter_pilot_non_claims_missing",
                        f"{label}.non_claims is empty or contains "
                        f"blank entries")

    # ---------------- Step 24: overclaim token scan ------------------
    over = detect_overclaim(report)
    if over is not None:
        return fail("adapter_pilot_overclaim",
                    f"report contains forbidden positive token "
                    f"{over!r} outside scope_limitations / non_claims")

    sys.stdout.write(
        f"PASS: Silver adapter pilot valid "
        f"({report['adapter_pilot_report_id']})\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
