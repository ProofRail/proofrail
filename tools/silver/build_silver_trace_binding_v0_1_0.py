#!/usr/bin/env python3
"""
ProofRail v0.3.2 Silver trace binding package runner.

Reads:
  - a v0.2.6 evidence source adapter descriptor (typically the
    simulated observability trace adapter);
  - a v0.3.2 trace event fixture (JSONL);
  - a v0.3.2 trace claim binding set (JSON).

Validates inputs structurally, subprocess-invokes the unchanged
v0.2.6 adapter validator, derives a deterministic trace binding
report, and writes a 4-subject package with a SHA-256 manifest:

  <output-dir>/
    adapter/<adapter-basename>            (subject [0])
    trace-events.jsonl                    (subject [1])
    trace-claim-bindings.json             (subject [2])
    silver-trace-binding-report.json      (subject [3])
    silver-trace-binding-manifest.json

If --self-validate is supplied, the v0.3.2 verifier is run against
the staged package BEFORE the atomic move into place. On any failure
(input, derivation, or self-validate), the staging directory is
removed and the destination is left untouched.

This script is pure Python stdlib. It is NOT a runtime decision, NOT
an authority, and does NOT claim that the trace source is
authoritative, that OpenTelemetry conformance has been established,
or that runtime behaviour is proven.

Stable runner-only refusal reasons:
  adapter_validation_failed
  trace_events_validation_failed
  trace_binding_set_validation_failed
  trace_binding_self_validation_failed
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
TRACE_BINDING_VERIFIER = TOOLS_DIR / "verify_silver_trace_binding_v0_1_0.py"

MANIFEST_DOCUMENT_TYPE = "proofrail.silver.trace_binding_manifest"
REPORT_DOCUMENT_TYPE = "proofrail.silver.trace_binding_report"
EVENT_DOCUMENT_TYPE = "proofrail.silver.trace_event"
BINDING_SET_DOCUMENT_TYPE = "proofrail.silver.trace_claim_binding_set"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.3.2"
HASH_ALGORITHM = "sha256"

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

ISO_8601_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


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


# --------------------------------------------------------------------- #
# Input validation                                                      #
# --------------------------------------------------------------------- #


def run_adapter_validator(adapter_path: Path) -> tuple[bool, str]:
    """Subprocess-invoke the unchanged v0.2.6 adapter validator."""
    if not ADAPTER_VALIDATOR.exists():
        return False, f"v0.2.6 adapter validator not found at {ADAPTER_VALIDATOR}"
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


def validate_trace_event_obj(
    obj: Any, line_no: int
) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, f"line {line_no}: event is not a JSON object"
    for k in REQUIRED_TRACE_EVENT_FIELDS:
        if k not in obj:
            return False, f"line {line_no}: missing required field '{k}'"
    if obj["document_type"] != EVENT_DOCUMENT_TYPE:
        return False, (
            f"line {line_no}: document_type must be {EVENT_DOCUMENT_TYPE!r}, "
            f"got {obj['document_type']!r}"
        )
    if obj["schema_version"] != SCHEMA_VERSION:
        return False, (
            f"line {line_no}: schema_version must be {SCHEMA_VERSION!r}, "
            f"got {obj['schema_version']!r}"
        )
    if obj["proofrail_release"] != PROOFRAIL_RELEASE:
        return False, (
            f"line {line_no}: proofrail_release must be "
            f"{PROOFRAIL_RELEASE!r}, got {obj['proofrail_release']!r}"
        )
    for k in ("event_id", "trace_id", "span_id", "principal_id",
              "protected_action_id", "decision_reason",
              "source_event_ref"):
        if not non_empty_str(obj[k]):
            return False, (
                f"line {line_no}: '{k}' must be a non-empty string"
            )
    if has_path_traversal(obj["source_event_ref"]) and \
            (obj["source_event_ref"].startswith("/") or
             ".." in obj["source_event_ref"].replace("\\", "/").split("/")):
        return False, (
            f"line {line_no}: 'source_event_ref' is absolute or "
            f"contains '..'"
        )
    if parse_iso_8601_z(obj["event_time"]) is None:
        return False, (
            f"line {line_no}: 'event_time' must be ISO-8601 UTC Z-suffixed"
        )
    if obj["decision"] not in ALLOWED_DECISIONS:
        return False, (
            f"line {line_no}: 'decision' must be one of "
            f"{sorted(ALLOWED_DECISIONS)}, got {obj['decision']!r}"
        )
    if not isinstance(obj["attributes"], dict):
        return False, (
            f"line {line_no}: 'attributes' must be a JSON object"
        )
    return True, ""


def validate_trace_events_file(
    path: Path,
) -> tuple[bool, str, list[dict]]:
    events: list[dict] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    return False, (
                        f"line {line_no} is blank or whitespace-only"
                    ), []
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, f"line {line_no} JSON parse error: {e}", []
                ok, detail = validate_trace_event_obj(obj, line_no)
                if not ok:
                    return False, detail, []
                events.append(obj)
    except OSError as e:
        return False, f"could not read trace events: {e}", []
    if not events:
        return False, "trace events file is empty", []
    seen_event_ids: set[str] = set()
    seen_trace_span: set[tuple[str, str]] = set()
    for i, ev in enumerate(events):
        if ev["event_id"] in seen_event_ids:
            return False, (
                f"duplicate event_id {ev['event_id']!r}"
            ), []
        seen_event_ids.add(ev["event_id"])
        key = (ev["trace_id"], ev["span_id"])
        if key in seen_trace_span:
            return False, (
                f"duplicate (trace_id, span_id) "
                f"({ev['trace_id']!r}, {ev['span_id']!r})"
            ), []
        seen_trace_span.add(key)
    for i in range(1, len(events)):
        prev = events[i - 1]
        cur = events[i]
        pt = parse_iso_8601_z(prev["event_time"])
        ct = parse_iso_8601_z(cur["event_time"])
        if pt is None or ct is None:
            return False, "internal: event_time parse failed mid-ordering", []
        if (pt, prev["event_id"]) >= (ct, cur["event_id"]):
            return False, (
                f"events not sorted ascending by (event_time, event_id) "
                f"between index {i - 1} and {i}"
            ), []
    return True, "", events


def validate_binding_set(
    path: Path,
) -> tuple[bool, str, dict]:
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return False, f"binding set is not valid JSON: {e}", {}
    if not isinstance(doc, dict):
        return False, "binding set is not a JSON object", {}
    if doc.get("document_type") != BINDING_SET_DOCUMENT_TYPE:
        return False, (
            f"document_type must be {BINDING_SET_DOCUMENT_TYPE!r}, "
            f"got {doc.get('document_type')!r}"
        ), {}
    if doc.get("schema_version") != SCHEMA_VERSION:
        return False, (
            f"schema_version must be {SCHEMA_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        ), {}
    if doc.get("proofrail_release") != PROOFRAIL_RELEASE:
        return False, (
            f"proofrail_release must be {PROOFRAIL_RELEASE!r}, "
            f"got {doc.get('proofrail_release')!r}"
        ), {}
    if not non_empty_str(doc.get("binding_set_id")):
        return False, "binding_set_id must be a non-empty string", {}
    tw = doc.get("trace_time_window")
    if not isinstance(tw, dict):
        return False, "trace_time_window must be an object", {}
    o = parse_iso_8601_z(tw.get("opens_at"))
    c = parse_iso_8601_z(tw.get("closes_at"))
    if o is None or c is None:
        return False, (
            "trace_time_window.opens_at / closes_at must be ISO-8601 UTC Z"
        ), {}
    if not (o < c):
        return False, "trace_time_window.opens_at must be before closes_at", {}
    bindings = doc.get("bindings")
    if not isinstance(bindings, list) or len(bindings) == 0:
        return False, "bindings must be a non-empty array", {}
    seen: set[str] = set()
    for i, b in enumerate(bindings):
        if not isinstance(b, dict):
            return False, f"bindings[{i}] is not a JSON object", {}
        for k in REQUIRED_BINDING_FIELDS:
            if k not in b:
                return False, (
                    f"bindings[{i}] missing required field '{k}'"
                ), {}
            if not non_empty_str(b[k]):
                return False, (
                    f"bindings[{i}].{k} must be a non-empty string"
                ), {}
        if b["required_decision"] not in ALLOWED_DECISIONS:
            return False, (
                f"bindings[{i}].required_decision must be one of "
                f"{sorted(ALLOWED_DECISIONS)}, got {b['required_decision']!r}"
            ), {}
        if b["expected_binding_status"] not in ALLOWED_BINDING_STATUSES:
            return False, (
                f"bindings[{i}].expected_binding_status must be one of "
                f"{sorted(ALLOWED_BINDING_STATUSES)}, got "
                f"{b['expected_binding_status']!r}"
            ), {}
        if b["claim_id"] in seen:
            return False, (
                f"duplicate claim_id {b['claim_id']!r}"
            ), {}
        seen.add(b["claim_id"])
    for arr_name in ("scope_limitations", "non_claims"):
        arr = doc.get(arr_name)
        if not isinstance(arr, list) or not arr:
            return False, f"{arr_name} must be a non-empty array of strings", {}
        for j, s in enumerate(arr):
            if not non_empty_str(s):
                return False, (
                    f"{arr_name}[{j}] must be a non-blank string"
                ), {}
    return True, "", doc


# --------------------------------------------------------------------- #
# Report derivation                                                     #
# --------------------------------------------------------------------- #


def derive_binding_rows(
    bindings: list[dict], events_by_id: dict[str, dict],
) -> tuple[list[dict], dict[str, int]]:
    rows: list[dict] = []
    counts = {
        "bound_count": 0,
        "bound_with_warning_count": 0,
        "trace_gap_detected_count": 0,
        "out_of_scope_count": 0,
    }
    count_key = {
        "bound": "bound_count",
        "bound_with_warning": "bound_with_warning_count",
        "trace_gap_detected": "trace_gap_detected_count",
        "out_of_scope_for_trace_binding": "out_of_scope_count",
    }
    for b in bindings:
        expected = b["expected_binding_status"]
        ev = events_by_id.get(b["required_trace_event_id"])
        if expected == "trace_gap_detected":
            row = {
                "claim_id": b["claim_id"],
                "trace_event_id": b["required_trace_event_id"],
                "trace_id": b["required_trace_id"],
                "span_id": b["required_span_id"],
                "protected_action_id": b["required_protected_action_id"],
                "principal_id": b["required_principal_id"],
                "decision": "",
                "binding_status": "trace_gap_detected",
                "evidence_refs": [],
                "warning": (
                    "no matching trace event present for "
                    f"required_trace_event_id "
                    f"{b['required_trace_event_id']!r}; "
                    "gap preserved per binding-set expectation"
                ),
            }
        else:
            # bound / bound_with_warning / out_of_scope_for_trace_binding
            # all require the event to exist and match required_* fields.
            row = {
                "claim_id": b["claim_id"],
                "trace_event_id": ev["event_id"] if ev else b["required_trace_event_id"],
                "trace_id": ev["trace_id"] if ev else b["required_trace_id"],
                "span_id": ev["span_id"] if ev else b["required_span_id"],
                "protected_action_id": (
                    ev["protected_action_id"] if ev
                    else b["required_protected_action_id"]
                ),
                "principal_id": (
                    ev["principal_id"] if ev else b["required_principal_id"]
                ),
                "decision": ev["decision"] if ev else b["required_decision"],
                "binding_status": expected,
                "evidence_refs": (
                    [f"trace-events.jsonl#{ev['event_id']}"] if ev else []
                ),
                "warning": None,
            }
            if expected == "bound_with_warning":
                row["warning"] = (
                    "binding preserved with reviewer warning per "
                    "binding-set expectation; trace evidence input only"
                )
            elif expected == "out_of_scope_for_trace_binding":
                row["warning"] = (
                    "binding row declared out of scope for trace-binding "
                    "purposes per binding-set expectation; referenced "
                    "trace event still recorded for completeness"
                )
        rows.append(row)
        counts[count_key[expected]] += 1
    return rows, counts


def build_report(
    report_id: str,
    generated_at: str,
    adapter_rel_path: str,
    adapter_sha256: str,
    events_sha256: str,
    event_count: int,
    time_window: dict,
    binding_set: dict,
    bindings_sha256: str,
    binding_count: int,
    binding_rows: list[dict],
    counts: dict[str, int],
) -> dict:
    return {
        "document_type": REPORT_DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "proofrail_release": PROOFRAIL_RELEASE,
        "trace_binding_report_id": report_id,
        "generated_at": generated_at,
        "trace_source": {
            "source_type": "observability_trace",
            "source_is_trust_authority": False,
            "adapter_descriptor_path": adapter_rel_path,
            "adapter_descriptor_sha256": adapter_sha256,
        },
        "trace_events": {
            "events_path": "trace-events.jsonl",
            "events_sha256": events_sha256,
            "event_count": event_count,
            "time_window": {
                "opens_at": time_window["opens_at"],
                "closes_at": time_window["closes_at"],
            },
        },
        "binding_set": {
            "binding_set_id": binding_set["binding_set_id"],
            "bindings_path": "trace-claim-bindings.json",
            "bindings_sha256": bindings_sha256,
            "binding_count": binding_count,
        },
        "binding_summary": {
            "bound_count": counts["bound_count"],
            "bound_with_warning_count": counts["bound_with_warning_count"],
            "trace_gap_detected_count": counts["trace_gap_detected_count"],
            "out_of_scope_count": counts["out_of_scope_count"],
            "source_is_trust_authority": False,
        },
        "bindings": binding_rows,
        "scope_limitations": [
            "The trace binding report binds claims to the deterministic "
            "v0.3.2 trace fixture only.",
            "The report does not assert that the observability substrate "
            "is authoritative.",
        ],
        "non_claims": [
            "This trace binding report is not runtime proof.",
            "This trace binding report does not make the trace source "
            "authoritative.",
            "This trace binding report is not OpenTelemetry conformance.",
            "This trace binding report is not Gold conformance.",
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
        "trace_binding_report_id": report_id,
        "generated_at": generated_at,
        "hash_algorithm": HASH_ALGORITHM,
        "subjects": subjects,
        "scope_limitations": [
            "The trace binding manifest anchors the deterministic v0.3.2 "
            "trace binding package only.",
            "The manifest does not make the observability source "
            "authoritative.",
        ],
        "non_claims": [
            "The trace binding manifest is not a certificate.",
            "The trace binding manifest is not runtime proof.",
            "The trace binding manifest is not OpenTelemetry conformance.",
            "The trace binding manifest is not Gold conformance, "
            "regulator approval, auditor approval, legal acceptance, "
            "compliance certification, or production authorization.",
        ],
    }


# --------------------------------------------------------------------- #
# Main                                                                  #
# --------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("ProofRail v0.3.2 Silver trace binding package "
                     "runner.")
    )
    parser.add_argument("--adapter", required=True,
                        help="Path to v0.2.6 evidence source adapter "
                             "descriptor (observability trace).")
    parser.add_argument("--trace-events", required=True,
                        help="Path to trace events JSONL fixture.")
    parser.add_argument("--bindings", required=True,
                        help="Path to trace claim binding set JSON.")
    parser.add_argument("--trace-binding-report-id", required=True,
                        help="Identifier for the generated report.")
    parser.add_argument("--generated-at", required=True,
                        help="ISO-8601 UTC, Z-suffixed timestamp.")
    parser.add_argument("--output-dir", required=True,
                        help="Destination directory for the trace "
                             "binding package.")
    parser.add_argument("--force", action="store_true",
                        help="Remove existing --output-dir if present.")
    parser.add_argument("--self-validate", action="store_true",
                        help="Run the v0.3.2 verifier on the staged "
                             "package before atomic publish.")
    args = parser.parse_args(argv)

    if parse_iso_8601_z(args.generated_at) is None:
        sys.stderr.write(
            f"ERROR: --generated-at {args.generated_at!r} is not "
            f"ISO-8601 UTC Z-suffixed\n"
        )
        return 2
    if not non_empty_str(args.trace_binding_report_id):
        sys.stderr.write(
            "ERROR: --trace-binding-report-id must be a non-empty string\n"
        )
        return 2

    adapter_path = Path(args.adapter).resolve()
    events_path = Path(args.trace_events).resolve()
    bindings_path = Path(args.bindings).resolve()
    output_dir = Path(args.output_dir).resolve()

    for p, label in (
        (adapter_path, "--adapter"),
        (events_path, "--trace-events"),
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
                f"ERROR: --output-dir {output_dir} exists and is not a "
                f"directory\n"
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

    # ----- Step 3: validate trace events -----
    ok, detail, events = validate_trace_events_file(events_path)
    if not ok:
        return refuse("trace_events_validation_failed", detail)

    # ----- Step 4: validate binding set -----
    ok, detail, binding_set = validate_binding_set(bindings_path)
    if not ok:
        return refuse("trace_binding_set_validation_failed", detail)

    # Cross-check: bindings semantics versus events.
    events_by_id = {ev["event_id"]: ev for ev in events}
    tw = binding_set["trace_time_window"]
    tw_open = parse_iso_8601_z(tw["opens_at"])
    tw_close = parse_iso_8601_z(tw["closes_at"])
    for b in binding_set["bindings"]:
        expected = b["expected_binding_status"]
        if expected == "trace_gap_detected":
            continue
        ev = events_by_id.get(b["required_trace_event_id"])
        if ev is None:
            return refuse(
                "trace_binding_set_validation_failed",
                f"binding {b['claim_id']!r} references "
                f"required_trace_event_id {b['required_trace_event_id']!r} "
                f"which is not present in the trace event fixture "
                f"(only trace_gap_detected may lack a matching event)",
            )
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
                    f"{req_field}={b[req_field]!r} vs event.{ev_field}="
                    f"{ev[ev_field]!r}"
                )
        if mismatches:
            return refuse(
                "trace_binding_set_validation_failed",
                f"binding {b['claim_id']!r} field mismatch vs event "
                f"{ev['event_id']!r}: " + "; ".join(mismatches),
            )
        ev_time = parse_iso_8601_z(ev["event_time"])
        if ev_time is None or ev_time < tw_open or ev_time > tw_close:
            return refuse(
                "trace_binding_set_validation_failed",
                f"binding {b['claim_id']!r}: referenced event "
                f"{ev['event_id']!r} event_time {ev['event_time']!r} "
                f"lies outside trace_time_window "
                f"[{tw['opens_at']!r}, {tw['closes_at']!r}]",
            )

    # ----- Step 5: stage the package -----
    staging = Path(str(output_dir) + f".staging.{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    try:
        staging.mkdir(parents=True)
        (staging / "adapter").mkdir()
        adapter_basename = adapter_path.name
        adapter_dest = staging / "adapter" / adapter_basename
        shutil.copyfile(adapter_path, adapter_dest)
        events_dest = staging / "trace-events.jsonl"
        shutil.copyfile(events_path, events_dest)
        bindings_dest = staging / "trace-claim-bindings.json"
        shutil.copyfile(bindings_path, bindings_dest)

        adapter_sha, adapter_size = sha256_file(adapter_dest)
        events_sha, events_size = sha256_file(events_dest)
        bindings_sha, bindings_size = sha256_file(bindings_dest)

        # ----- Step 6: derive report -----
        binding_rows, counts = derive_binding_rows(
            binding_set["bindings"], events_by_id
        )
        report = build_report(
            report_id=args.trace_binding_report_id,
            generated_at=args.generated_at,
            adapter_rel_path=f"adapter/{adapter_basename}",
            adapter_sha256=adapter_sha,
            events_sha256=events_sha,
            event_count=len(events),
            time_window=tw,
            binding_set=binding_set,
            bindings_sha256=bindings_sha,
            binding_count=len(binding_set["bindings"]),
            binding_rows=binding_rows,
            counts=counts,
        )
        report_dest = staging / "silver-trace-binding-report.json"
        report_dest.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        report_sha, report_size = sha256_file(report_dest)

        # ----- Step 7: build manifest -----
        subjects = [
            {
                "path": f"adapter/{adapter_basename}",
                "role": "trace_source_adapter_descriptor",
                "sha256": adapter_sha,
                "size_bytes": adapter_size,
            },
            {
                "path": "trace-events.jsonl",
                "role": "trace_events",
                "sha256": events_sha,
                "size_bytes": events_size,
            },
            {
                "path": "trace-claim-bindings.json",
                "role": "trace_claim_binding_set",
                "sha256": bindings_sha,
                "size_bytes": bindings_size,
            },
            {
                "path": "silver-trace-binding-report.json",
                "role": "silver_trace_binding_report",
                "sha256": report_sha,
                "size_bytes": report_size,
            },
        ]
        manifest = build_manifest(
            report_id=args.trace_binding_report_id,
            generated_at=args.generated_at,
            subjects=subjects,
        )
        manifest_dest = staging / "silver-trace-binding-manifest.json"
        manifest_dest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )

        # ----- Step 8: optional self-validate -----
        if args.self_validate:
            if not TRACE_BINDING_VERIFIER.exists():
                shutil.rmtree(staging, ignore_errors=True)
                return refuse(
                    "trace_binding_self_validation_failed",
                    f"verifier not found at {TRACE_BINDING_VERIFIER}",
                )
            proc = subprocess.run(
                [sys.executable, str(TRACE_BINDING_VERIFIER),
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
                    "trace_binding_self_validation_failed", first
                )

        # ----- Step 9: atomic publish -----
        if output_dir.exists():
            shutil.rmtree(output_dir)
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    sys.stdout.write(
        f"PASS: silver trace binding package built at {output_dir}\n"
        f"  trace_binding_report_id: {args.trace_binding_report_id}\n"
        f"  adapter: adapter/{adapter_basename}\n"
        f"  trace_events.event_count: {len(events)}\n"
        f"  binding_set.binding_count: {len(binding_set['bindings'])}\n"
        f"  binding_summary: bound={counts['bound_count']} "
        f"bound_with_warning={counts['bound_with_warning_count']} "
        f"trace_gap_detected={counts['trace_gap_detected_count']} "
        f"out_of_scope={counts['out_of_scope_count']}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
