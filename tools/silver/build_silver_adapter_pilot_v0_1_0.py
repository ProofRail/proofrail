#!/usr/bin/env python3
"""
ProofRail v0.3.3 Silver adapter pilot package runner.

Reads:
  - a v0.2.6 evidence source adapter descriptor (the simulated
    observability-trace adapter);
  - a v0.3.3 OpenTelemetry-shaped local source-export fixture (JSONL);
  - a v0.3.3 normalization map (JSON);
  - the unchanged v0.3.2 trace claim binding set (JSON).

Validates inputs structurally, subprocess-invokes the unchanged v0.2.6
adapter validator, normalizes each source record into a ProofRail
v0.3.2 trace event by applying the simple normalization map
(<dot.path> or "constant:<literal>"), subprocess-invokes the unchanged
v0.3.2 trace binding builder over the normalized files, derives the
adapter pilot report, and writes a 7-subject package with a SHA-256
manifest:

  <output-dir>/
    adapter/<adapter-basename>                           (subject [0])
    source/source-otel-trace-export.jsonl                (subject [1])
    normalization/normalization-map.json                 (subject [2])
    normalized/trace-events.jsonl                        (subject [3])
    normalized/trace-claim-bindings.json                 (subject [4])
    trace-binding/
      adapter/...
      trace-events.jsonl
      trace-claim-bindings.json
      silver-trace-binding-report.json
      silver-trace-binding-manifest.json                 (subject [5])
    silver-adapter-pilot-report.json                     (subject [6])
    silver-adapter-pilot-manifest.json

If --self-validate is supplied, the v0.3.3 verifier is run against the
staged package BEFORE the atomic move into place. On any failure
(input, derivation, nested build, or self-validate), the staging
directory is removed and the destination is left untouched.

This script is pure Python stdlib. It is NOT a runtime decision, NOT
an authority, and does NOT claim that the source is authoritative,
that OpenTelemetry conformance has been established, that vendor
integration has been performed, or that runtime behaviour is proven.

Stable runner-only refusal reasons:
  adapter_validation_failed
  source_export_validation_failed
  normalization_map_validation_failed
  binding_set_validation_failed
  nested_trace_binding_generation_failed
  adapter_pilot_self_validation_failed
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

THIS_FILE = Path(__file__).resolve()
TOOLS_DIR = THIS_FILE.parent

ADAPTER_VALIDATOR = TOOLS_DIR / "validate_evidence_source_adapter_v0_1_0.py"
TRACE_BINDING_BUILDER = TOOLS_DIR / "build_silver_trace_binding_v0_1_0.py"
TRACE_BINDING_VERIFIER = TOOLS_DIR / "verify_silver_trace_binding_v0_1_0.py"
ADAPTER_PILOT_VERIFIER = TOOLS_DIR / "verify_silver_adapter_pilot_v0_1_0.py"

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.adapter_pilot_manifest"
REPORT_DOCUMENT_TYPE = "proofrail.silver.adapter_pilot_report"
NORMALIZATION_MAP_DOCUMENT_TYPE = (
    "proofrail.silver.adapter_pilot_normalization_map"
)
TARGET_TRACE_EVENT_DOCUMENT_TYPE = "proofrail.silver.trace_event"
TRACE_BINDING_SET_DOCUMENT_TYPE = "proofrail.silver.trace_claim_binding_set"

SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.3"
HASH_ALGORITHM = "sha256"

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

ISO_8601_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


# --------------------------------------------------------------------- #
# Helpers                                                               #
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


def sha256_file(p: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
    return f"sha256:{h.hexdigest()}", size


def refuse(reason: str, detail: str) -> int:
    sys.stderr.write(f"FAIL: {reason}: {detail}\n")
    return 1


def get_dot_path(obj: Any, dot_path: str) -> tuple[bool, Any]:
    """Resolve a dot-path into a nested dict.

    At each step, performs a longest-prefix key match. This allows
    OpenTelemetry-style attribute keys with literal dots (e.g.
    ``span.attributes["proofrail.event_id"]``) to be addressed by a
    single dot-path (``span.attributes.proofrail.event_id``) without a
    separate quoting syntax. Longest match wins deterministically.

    Returns (found, value). Found is False if at any step no key in
    the current dict matches any dot-joined prefix of the remaining
    parts, or the traversal lands on a non-dict before consuming all
    parts.
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
    """Set a dot-path inside a nested dict, creating intermediate dicts."""
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
# Adapter validation                                                    #
# --------------------------------------------------------------------- #


def run_adapter_validator(adapter_path: Path) -> tuple[bool, str]:
    """Subprocess-invoke the unchanged v0.2.6 adapter validator."""
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


def validate_adapter_source_is_not_authority(
    adapter_path: Path,
) -> tuple[bool, str]:
    """Refuse before running the generic v0.2.6 validator if the adapter
    declares the source as a trust authority. Keeps the runner-only
    reason `adapter_validation_failed` deterministic regardless of
    v0.2.6 validator behavior on that field."""
    try:
        doc = json.loads(adapter_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return False, f"adapter is not valid JSON: {e}"
    if not isinstance(doc, dict):
        return False, "adapter is not a JSON object"
    tb = doc.get("trust_boundary")
    if not isinstance(tb, dict):
        return False, "adapter missing trust_boundary object"
    flag = tb.get("source_is_trust_authority")
    if flag is not False:
        return False, (
            "adapter trust_boundary.source_is_trust_authority must be "
            f"exactly false, got {flag!r}"
        )
    return True, ""


# --------------------------------------------------------------------- #
# Source export validation                                              #
# --------------------------------------------------------------------- #


def validate_source_record(
    obj: Any, line_no: int
) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, f"line {line_no} is not a JSON object"
    for f in REQUIRED_SOURCE_TOP_FIELDS:
        if f not in obj:
            return False, f"line {line_no} missing required field {f!r}"
    if not non_empty_str(obj["export_format"]):
        return False, f"line {line_no} export_format is empty"
    if not non_empty_str(obj["export_record_id"]):
        return False, f"line {line_no} export_record_id is empty"
    if not isinstance(obj["resource"], dict):
        return False, f"line {line_no} resource is not an object"
    if not isinstance(obj["scope"], dict):
        return False, f"line {line_no} scope is not an object"
    span = obj["span"]
    if not isinstance(span, dict):
        return False, f"line {line_no} span is not an object"
    for f in REQUIRED_SOURCE_SPAN_FIELDS:
        if f not in span:
            return False, (
                f"line {line_no} span missing required field {f!r}"
            )
    if not non_empty_str(span["trace_id"]):
        return False, f"line {line_no} span.trace_id is empty"
    if not non_empty_str(span["span_id"]):
        return False, f"line {line_no} span.span_id is empty"
    if not non_empty_str(span["name"]):
        return False, f"line {line_no} span.name is empty"
    if parse_iso_8601_z(span["start_time"]) is None:
        return False, (
            f"line {line_no} span.start_time is not ISO-8601 UTC Z-suffixed"
        )
    if parse_iso_8601_z(span["end_time"]) is None:
        return False, (
            f"line {line_no} span.end_time is not ISO-8601 UTC Z-suffixed"
        )
    if not isinstance(span["attributes"], dict):
        return False, f"line {line_no} span.attributes is not an object"
    attrs = span["attributes"]
    for k in REQUIRED_SOURCE_PROOFRAIL_ATTRS:
        full = f"proofrail.{k}"
        if full not in attrs:
            return False, (
                f"line {line_no} span.attributes missing required "
                f"field {full!r}"
            )
        if not non_empty_str(attrs[full]):
            return False, (
                f"line {line_no} span.attributes[{full!r}] is empty"
            )
    decision = attrs["proofrail.decision"]
    if decision not in ALLOWED_SOURCE_DECISIONS:
        return False, (
            f"line {line_no} span.attributes['proofrail.decision'] "
            f"{decision!r} is not in {sorted(ALLOWED_SOURCE_DECISIONS)}"
        )
    return True, ""


def validate_source_export_file(
    p: Path,
) -> tuple[bool, str, list[dict]]:
    try:
        text = p.read_text()
    except OSError as e:
        return False, f"cannot read source export: {e}", []
    records: list[dict] = []
    seen_record_ids: set[str] = set()
    seen_trace_span: set[tuple[str, str]] = set()
    prev_key: tuple[str, str] | None = None
    lines = text.splitlines()
    if not lines:
        return False, "source export is empty", []
    for idx, line in enumerate(lines, start=1):
        if line == "":
            return False, f"line {idx} is blank", []
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            return False, f"line {idx} JSON parse error: {e}", []
        ok, detail = validate_source_record(obj, idx)
        if not ok:
            return False, detail, []
        rid = obj["export_record_id"]
        if rid in seen_record_ids:
            return False, (
                f"duplicate export_record_id {rid!r}"
            ), []
        seen_record_ids.add(rid)
        ts = (obj["span"]["trace_id"], obj["span"]["span_id"])
        if ts in seen_trace_span:
            return False, (
                f"duplicate (trace_id, span_id) "
                f"{(obj['span']['trace_id'], obj['span']['span_id'])!r}"
            ), []
        seen_trace_span.add(ts)
        key = (obj["span"]["start_time"], rid)
        if prev_key is not None and key < prev_key:
            return False, (
                f"source export not sorted ascending by "
                f"(span.start_time, export_record_id) between line "
                f"{idx - 1} and {idx}"
            ), []
        prev_key = key
        records.append(obj)
    return True, "", records


# --------------------------------------------------------------------- #
# Normalization map validation                                          #
# --------------------------------------------------------------------- #


def validate_normalization_map_doc(
    p: Path,
) -> tuple[bool, str, dict]:
    try:
        text = p.read_text()
    except OSError as e:
        return False, f"cannot read normalization map: {e}", {}
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f"normalization map JSON parse error: {e}", {}
    if not isinstance(doc, dict):
        return False, "normalization map is not a JSON object", {}
    for f in REQUIRED_NORMALIZATION_MAP_TOP_FIELDS:
        if f not in doc:
            return False, f"missing required field {f!r}", {}
    if doc["document_type"] != NORMALIZATION_MAP_DOCUMENT_TYPE:
        return False, (
            f"document_type must be {NORMALIZATION_MAP_DOCUMENT_TYPE!r}, "
            f"got {doc['document_type']!r}"
        ), {}
    if doc["schema_version"] != SCHEMA_VERSION:
        return False, (
            f"schema_version must be {SCHEMA_VERSION!r}, "
            f"got {doc['schema_version']!r}"
        ), {}
    if doc["proofrail_release"] != PROOFRAIL_RELEASE:
        return False, (
            f"proofrail_release must be {PROOFRAIL_RELEASE!r}, "
            f"got {doc['proofrail_release']!r}"
        ), {}
    if not non_empty_str(doc["normalization_map_id"]):
        return False, "normalization_map_id is empty", {}
    if not non_empty_str(doc["source_format"]):
        return False, "source_format is empty", {}
    if doc["target_document_type"] != TARGET_TRACE_EVENT_DOCUMENT_TYPE:
        return False, (
            f"target_document_type must be "
            f"{TARGET_TRACE_EVENT_DOCUMENT_TYPE!r}, "
            f"got {doc['target_document_type']!r}"
        ), {}
    fm = doc["field_mappings"]
    if not isinstance(fm, dict) or not fm:
        return False, "field_mappings must be a non-empty JSON object", {}
    for tgt_key, mapping_value in fm.items():
        if not non_empty_str(tgt_key):
            return False, (
                f"field_mappings target key {tgt_key!r} is empty"
            ), {}
        if any(p == "" for p in tgt_key.split(".")):
            return False, (
                f"field_mappings target key {tgt_key!r} contains "
                f"empty dot component"
            ), {}
        if not isinstance(mapping_value, str):
            return False, (
                f"field_mappings[{tgt_key!r}] mapping value must be a "
                f"string, got {type(mapping_value).__name__}"
            ), {}
        if mapping_value.startswith("constant:"):
            continue
        # else must be a non-empty dot path
        if not non_empty_str(mapping_value):
            return False, (
                f"field_mappings[{tgt_key!r}] mapping value is empty"
            ), {}
        if any(p == "" for p in mapping_value.split(".")):
            return False, (
                f"field_mappings[{tgt_key!r}] source dot-path "
                f"{mapping_value!r} contains empty dot component"
            ), {}
    rtf = doc["required_target_fields"]
    if not isinstance(rtf, list) or not rtf:
        return False, (
            "required_target_fields must be a non-empty array"
        ), {}
    for entry in rtf:
        if not non_empty_str(entry):
            return False, (
                f"required_target_fields entry {entry!r} is empty"
            ), {}
    if not isinstance(doc["scope_limitations"], list):
        return False, "scope_limitations must be an array", {}
    if not isinstance(doc["non_claims"], list):
        return False, "non_claims must be an array", {}
    return True, "", doc


# --------------------------------------------------------------------- #
# Binding set validation (v0.3.2 shape; subset check only)              #
# --------------------------------------------------------------------- #


def validate_binding_set_struct(
    p: Path,
) -> tuple[bool, str, dict]:
    try:
        text = p.read_text()
    except OSError as e:
        return False, f"cannot read binding set: {e}", {}
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f"binding set JSON parse error: {e}", {}
    if not isinstance(doc, dict):
        return False, "binding set is not a JSON object", {}
    if doc.get("document_type") != TRACE_BINDING_SET_DOCUMENT_TYPE:
        return False, (
            f"document_type must be {TRACE_BINDING_SET_DOCUMENT_TYPE!r}, "
            f"got {doc.get('document_type')!r}"
        ), {}
    if not isinstance(doc.get("bindings"), list) or not doc["bindings"]:
        return False, "bindings must be a non-empty array", {}
    return True, "", doc


# --------------------------------------------------------------------- #
# Normalization                                                         #
# --------------------------------------------------------------------- #


def apply_normalization(
    source_records: list[dict],
    normalization_map: dict,
) -> tuple[bool, str, list[dict]]:
    """Apply field_mappings to each source record.

    Returns (ok, detail, normalized_events). If a required_target_field
    cannot be resolved for any record, returns ok=False with a
    descriptive detail (raised by the runner as
    normalization_map_validation_failed)."""
    fm = normalization_map["field_mappings"]
    required_targets = set(normalization_map["required_target_fields"])
    out: list[dict] = []
    for idx, rec in enumerate(source_records, start=1):
        if rec.get("export_format") != normalization_map["source_format"]:
            return False, (
                f"line {idx} export_format {rec.get('export_format')!r} "
                f"does not equal normalization_map.source_format "
                f"{normalization_map['source_format']!r}"
            ), []
        ev: dict = {}
        for tgt_key, mapping_value in fm.items():
            if mapping_value.startswith("constant:"):
                literal = mapping_value[len("constant:"):]
                set_dot_path(ev, tgt_key, literal)
                continue
            found, value = get_dot_path(rec, mapping_value)
            if not found:
                # Required field missing?
                top = tgt_key.split(".")[0]
                if tgt_key in required_targets or top in required_targets:
                    return False, (
                        f"line {idx} source field {mapping_value!r} "
                        f"not present; required target field "
                        f"{tgt_key!r} cannot be populated"
                    ), []
                continue
            set_dot_path(ev, tgt_key, value)
        # Verify every required target field is populated.
        for rt in normalization_map["required_target_fields"]:
            found, val = get_dot_path(ev, rt)
            if not found:
                return False, (
                    f"line {idx} required target field {rt!r} is "
                    f"missing after normalization"
                ), []
            if rt != "attributes" and not non_empty_str(val) \
                    and not isinstance(val, (dict, list, int, float, bool)):
                return False, (
                    f"line {idx} required target field {rt!r} is empty"
                ), []
        out.append(ev)
    return True, "", out


def serialize_normalized_events_jsonl(events: list[dict]) -> bytes:
    """Deterministic line-delimited JSON serialization with sorted keys."""
    buf: list[str] = []
    for ev in events:
        buf.append(json.dumps(ev, sort_keys=True, separators=(",", ":")))
    return ("\n".join(buf) + "\n").encode("utf-8")


# --------------------------------------------------------------------- #
# Subprocess: nested v0.3.2 builder                                     #
# --------------------------------------------------------------------- #


def run_nested_v0_3_2_builder(
    adapter_path: Path,
    normalized_events_path: Path,
    normalized_bindings_path: Path,
    nested_output_dir: Path,
    nested_report_id: str,
    generated_at: str,
) -> tuple[bool, str]:
    if not TRACE_BINDING_BUILDER.exists():
        return False, (
            f"v0.3.2 builder not found at {TRACE_BINDING_BUILDER}"
        )
    cmd = [
        sys.executable, str(TRACE_BINDING_BUILDER),
        "--adapter", str(adapter_path),
        "--trace-events", str(normalized_events_path),
        "--bindings", str(normalized_bindings_path),
        "--trace-binding-report-id", nested_report_id,
        "--generated-at", generated_at,
        "--output-dir", str(nested_output_dir),
        "--force",
        "--self-validate",
    ]
    try:
        proc = subprocess.run(
            cmd, check=False, capture_output=True, text=True,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"subprocess error: {e}"
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip().splitlines()
        first = msg[0] if msg else "(no output)"
        return False, first
    return True, ""


# --------------------------------------------------------------------- #
# Report and manifest construction                                      #
# --------------------------------------------------------------------- #


def build_report(
    report_id: str,
    generated_at: str,
    adapter_rel: str,
    adapter_sha256: str,
    source_rel: str,
    source_sha256: str,
    source_record_count: int,
    source_format: str,
    normalization_rel: str,
    normalization_sha256: str,
    normalized_events_rel: str,
    normalized_events_sha256: str,
    normalized_event_count: int,
    nested_manifest_rel: str,
    nested_manifest_sha256: str,
) -> dict:
    return {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "adapter_pilot_report_id": report_id,
        "generated_at": generated_at,
        "adapter": {
            "adapter_path": adapter_rel,
            "adapter_sha256": adapter_sha256,
            "source_is_trust_authority": False,
        },
        "source_export": {
            "source_export_path": source_rel,
            "source_export_sha256": source_sha256,
            "source_record_count": source_record_count,
            "source_format": source_format,
        },
        "normalization": {
            "normalization_map_path": normalization_rel,
            "normalization_map_sha256": normalization_sha256,
            "normalized_trace_events_path": normalized_events_rel,
            "normalized_trace_events_sha256": normalized_events_sha256,
            "normalized_event_count": normalized_event_count,
        },
        "nested_trace_binding": {
            "manifest_path": nested_manifest_rel,
            "manifest_sha256": nested_manifest_sha256,
            "verification_status": "pass",
        },
        "pilot_summary": {
            "source_is_trust_authority": False,
            "normalization_status": "pass",
            "nested_trace_binding_status": "pass",
            "normalized_events_match_source": True,
            "runtime_truth_claimed": False,
        },
        "claims": [
            {
                "claim_id": "adapter_descriptor_valid",
                "status": "pass",
                "evidence_refs": [adapter_rel],
            },
            {
                "claim_id": "source_not_trust_authority",
                "status": "pass",
                "evidence_refs": [adapter_rel],
            },
            {
                "claim_id": "source_export_hash_verifiable",
                "status": "pass",
                "evidence_refs": [source_rel],
            },
            {
                "claim_id": "normalization_map_valid",
                "status": "pass",
                "evidence_refs": [normalization_rel],
            },
            {
                "claim_id": "normalized_trace_events_rederived",
                "status": "pass",
                "evidence_refs": [
                    normalized_events_rel,
                    source_rel,
                    normalization_rel,
                ],
            },
            {
                "claim_id": "nested_trace_binding_valid",
                "status": "pass",
                "evidence_refs": [nested_manifest_rel],
            },
            {
                "claim_id": "no_runtime_truth_claimed",
                "status": "pass",
                "evidence_refs": [
                    "silver-adapter-pilot-report.json"
                ],
            },
        ],
        "scope_limitations": [
            "This adapter pilot applies only to the deterministic v0.3.3 "
            "simulated source export fixture.",
            "The simulated observability-trace adapter is an evidence "
            "source, not a trust authority."
        ],
        "non_claims": [
            "This adapter pilot is not a vendor certification.",
            "This adapter pilot is not a production integration.",
            "This adapter pilot is not OpenTelemetry conformance.",
            "This adapter pilot does not prove runtime truth.",
            "This adapter pilot is not a regulator approval, third-party "
            "audit, legal acceptance, compliance certification, "
            "production authorization, or Gold readiness assessment."
        ],
    }


def build_manifest(
    report_id: str,
    generated_at: str,
    subjects: list[dict],
) -> dict:
    return {
        "document_type": MANIFEST_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "adapter_pilot_report_id": report_id,
        "generated_at": generated_at,
        "hash_algorithm": HASH_ALGORITHM,
        "subjects": subjects,
        "scope_limitations": [
            "This adapter pilot manifest binds only the deterministic "
            "v0.3.3 adapter pilot package subjects.",
            "The manifest is an integrity anchor, not a certificate, "
            "approval, audit, or trust transfer."
        ],
        "non_claims": [
            "This manifest is not a vendor certification.",
            "This manifest is not a production integration.",
            "This manifest is not OpenTelemetry conformance.",
            "This manifest does not prove runtime truth.",
            "This manifest is not a regulator approval, third-party "
            "audit, legal acceptance, compliance certification, "
            "production authorization, or Gold readiness assessment."
        ],
    }


# --------------------------------------------------------------------- #
# Main                                                                  #
# --------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "ProofRail v0.3.3 Silver adapter pilot package runner."
        )
    )
    parser.add_argument("--adapter", required=True,
                        help="Path to v0.2.6 evidence source adapter "
                             "descriptor (observability trace).")
    parser.add_argument("--source-export", required=True,
                        help="Path to OpenTelemetry-shaped source "
                             "export JSONL fixture.")
    parser.add_argument("--normalization-map", required=True,
                        help="Path to normalization map JSON.")
    parser.add_argument("--bindings", required=True,
                        help="Path to v0.3.2 trace claim binding set JSON.")
    parser.add_argument("--adapter-pilot-report-id", required=True,
                        help="Identifier for the generated adapter "
                             "pilot report.")
    parser.add_argument("--generated-at", required=True,
                        help="ISO-8601 UTC, Z-suffixed timestamp.")
    parser.add_argument("--output-dir", required=True,
                        help="Destination directory for the adapter "
                             "pilot package.")
    parser.add_argument("--force", action="store_true",
                        help="Replace existing --output-dir if present. "
                             "The existing directory is removed AFTER "
                             "the staged package has been built and "
                             "(if requested) self-validated.")
    parser.add_argument("--self-validate", action="store_true",
                        help="Run the v0.3.3 verifier on the staged "
                             "package before atomic publish.")
    args = parser.parse_args(argv)

    if parse_iso_8601_z(args.generated_at) is None:
        sys.stderr.write(
            f"ERROR: --generated-at {args.generated_at!r} is not "
            f"ISO-8601 UTC Z-suffixed\n"
        )
        return 2
    if not non_empty_str(args.adapter_pilot_report_id):
        sys.stderr.write(
            "ERROR: --adapter-pilot-report-id must be a non-empty string\n"
        )
        return 2

    adapter_path = Path(args.adapter).resolve()
    source_path = Path(args.source_export).resolve()
    normalization_path = Path(args.normalization_map).resolve()
    bindings_path = Path(args.bindings).resolve()
    output_dir = Path(args.output_dir).resolve()

    for p, label in (
        (adapter_path, "--adapter"),
        (source_path, "--source-export"),
        (normalization_path, "--normalization-map"),
        (bindings_path, "--bindings"),
    ):
        if not p.is_file():
            sys.stderr.write(f"ERROR: {label} not found: {p}\n")
            return 2

    if output_dir.exists():
        if not args.force:
            sys.stderr.write(
                f"ERROR: --output-dir {output_dir} already exists "
                f"(use --force to overwrite)\n"
            )
            return 2
        if not output_dir.is_dir():
            sys.stderr.write(
                f"ERROR: --output-dir {output_dir} exists and is not "
                f"a directory\n"
            )
            return 2

    # ----- Step 1: structural trust-authority pre-check on adapter -----
    ok, detail = validate_adapter_source_is_not_authority(adapter_path)
    if not ok:
        return refuse("adapter_validation_failed", detail)

    # ----- Step 2: subprocess v0.2.6 adapter validator -----
    ok, detail = run_adapter_validator(adapter_path)
    if not ok:
        return refuse("adapter_validation_failed", detail)

    # ----- Step 3: validate source export -----
    ok, detail, source_records = validate_source_export_file(source_path)
    if not ok:
        return refuse("source_export_validation_failed", detail)

    # ----- Step 4: validate normalization map -----
    ok, detail, norm_map = validate_normalization_map_doc(normalization_path)
    if not ok:
        return refuse("normalization_map_validation_failed", detail)

    # ----- Step 5: validate binding set (structural only; v0.3.2 owns
    #               full semantics) -----
    ok, detail, _ = validate_binding_set_struct(bindings_path)
    if not ok:
        return refuse("binding_set_validation_failed", detail)

    # ----- Step 6: stage the package -----
    staging = Path(str(output_dir) + f".staging.{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    try:
        staging.mkdir(parents=True)
        (staging / "adapter").mkdir()
        (staging / "source").mkdir()
        (staging / "normalization").mkdir()
        (staging / "normalized").mkdir()

        adapter_basename = adapter_path.name
        adapter_dest = staging / "adapter" / adapter_basename
        shutil.copyfile(adapter_path, adapter_dest)

        source_dest = staging / "source" / "source-otel-trace-export.jsonl"
        shutil.copyfile(source_path, source_dest)

        norm_dest = staging / "normalization" / "normalization-map.json"
        shutil.copyfile(normalization_path, norm_dest)

        # ----- Step 7: apply normalization -----
        ok, detail, normalized_events = apply_normalization(
            source_records, norm_map
        )
        if not ok:
            shutil.rmtree(staging, ignore_errors=True)
            return refuse(
                "normalization_map_validation_failed", detail
            )

        normalized_events_dest = (
            staging / "normalized" / "trace-events.jsonl"
        )
        normalized_events_dest.write_bytes(
            serialize_normalized_events_jsonl(normalized_events)
        )

        normalized_bindings_dest = (
            staging / "normalized" / "trace-claim-bindings.json"
        )
        shutil.copyfile(bindings_path, normalized_bindings_dest)

        # ----- Step 8: subprocess v0.3.2 builder -----
        nested_dir = staging / "trace-binding"
        nested_report_id = (
            f"{args.adapter_pilot_report_id}-nested-trace-binding"
        )
        ok, detail = run_nested_v0_3_2_builder(
            adapter_path=adapter_dest,
            normalized_events_path=normalized_events_dest,
            normalized_bindings_path=normalized_bindings_dest,
            nested_output_dir=nested_dir,
            nested_report_id=nested_report_id,
            generated_at=args.generated_at,
        )
        if not ok:
            shutil.rmtree(staging, ignore_errors=True)
            return refuse(
                "nested_trace_binding_generation_failed", detail
            )

        # ----- Step 9: compute subject hashes -----
        adapter_sha, adapter_size = sha256_file(adapter_dest)
        source_sha, source_size = sha256_file(source_dest)
        norm_sha, norm_size = sha256_file(norm_dest)
        nev_sha, nev_size = sha256_file(normalized_events_dest)
        nbi_sha, nbi_size = sha256_file(normalized_bindings_dest)
        nested_manifest_path = (
            nested_dir / "silver-trace-binding-manifest.json"
        )
        if not nested_manifest_path.is_file():
            shutil.rmtree(staging, ignore_errors=True)
            return refuse(
                "nested_trace_binding_generation_failed",
                f"nested manifest not found at {nested_manifest_path}",
            )
        nmf_sha, nmf_size = sha256_file(nested_manifest_path)

        # ----- Step 10: derive report -----
        report = build_report(
            report_id=args.adapter_pilot_report_id,
            generated_at=args.generated_at,
            adapter_rel=f"adapter/{adapter_basename}",
            adapter_sha256=adapter_sha,
            source_rel="source/source-otel-trace-export.jsonl",
            source_sha256=source_sha,
            source_record_count=len(source_records),
            source_format=norm_map["source_format"],
            normalization_rel="normalization/normalization-map.json",
            normalization_sha256=norm_sha,
            normalized_events_rel="normalized/trace-events.jsonl",
            normalized_events_sha256=nev_sha,
            normalized_event_count=len(normalized_events),
            nested_manifest_rel=(
                "trace-binding/silver-trace-binding-manifest.json"
            ),
            nested_manifest_sha256=nmf_sha,
        )
        report_dest = staging / "silver-adapter-pilot-report.json"
        report_dest.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        report_sha, report_size = sha256_file(report_dest)

        # ----- Step 11: build manifest -----
        subjects = [
            {
                "path": f"adapter/{adapter_basename}",
                "role": "adapter_descriptor",
                "sha256": adapter_sha,
                "size_bytes": adapter_size,
            },
            {
                "path": "source/source-otel-trace-export.jsonl",
                "role": "source_export",
                "sha256": source_sha,
                "size_bytes": source_size,
            },
            {
                "path": "normalization/normalization-map.json",
                "role": "normalization_map",
                "sha256": norm_sha,
                "size_bytes": norm_size,
            },
            {
                "path": "normalized/trace-events.jsonl",
                "role": "normalized_trace_events",
                "sha256": nev_sha,
                "size_bytes": nev_size,
            },
            {
                "path": "normalized/trace-claim-bindings.json",
                "role": "normalized_trace_claim_bindings",
                "sha256": nbi_sha,
                "size_bytes": nbi_size,
            },
            {
                "path": "trace-binding/silver-trace-binding-manifest.json",
                "role": "nested_trace_binding_manifest",
                "sha256": nmf_sha,
                "size_bytes": nmf_size,
            },
            {
                "path": "silver-adapter-pilot-report.json",
                "role": "adapter_pilot_report",
                "sha256": report_sha,
                "size_bytes": report_size,
            },
        ]
        manifest = build_manifest(
            report_id=args.adapter_pilot_report_id,
            generated_at=args.generated_at,
            subjects=subjects,
        )
        manifest_dest = staging / "silver-adapter-pilot-manifest.json"
        manifest_dest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )

        # ----- Step 12: optional self-validate (BEFORE atomic publish) ---
        if args.self_validate:
            if not ADAPTER_PILOT_VERIFIER.exists():
                shutil.rmtree(staging, ignore_errors=True)
                return refuse(
                    "adapter_pilot_self_validation_failed",
                    f"verifier not found at {ADAPTER_PILOT_VERIFIER}",
                )
            proc = subprocess.run(
                [sys.executable, str(ADAPTER_PILOT_VERIFIER),
                 "--manifest", str(manifest_dest)],
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                msg = (proc.stderr or proc.stdout or "").strip().splitlines()
                first = msg[0] if msg else "(no output)"
                shutil.rmtree(staging, ignore_errors=True)
                return refuse(
                    "adapter_pilot_self_validation_failed", first
                )

        # ----- Step 13: atomic publish -----
        # Per --force semantics: only AFTER staging build and (optional)
        # self-validation has succeeded do we touch the existing
        # output_dir. Failed runs above already cleaned up staging and
        # never touched output_dir.
        if output_dir.exists():
            shutil.rmtree(output_dir)
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    sys.stdout.write(
        f"PASS: silver adapter pilot package built at {output_dir}\n"
        f"  adapter_pilot_report_id: {args.adapter_pilot_report_id}\n"
        f"  adapter: adapter/{adapter_basename}\n"
        f"  source_export.source_record_count: {len(source_records)}\n"
        f"  normalization.normalized_event_count: "
        f"{len(normalized_events)}\n"
        f"  nested_trace_binding.verification_status: pass\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
