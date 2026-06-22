#!/usr/bin/env python3
"""Validate Silver Evidence Source Adapter v0.1.0 descriptors.

Local structural validator for Silver Evidence Source Adapter descriptors
(ProofRail v0.2.6). Validates descriptor shape and adapter claims only.
Does not read external logs, fetch URLs, call vendor APIs, or assert source
authenticity.

Usage:
  python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py \\
    --adapter <file.json>

  python3 tools/silver/validate_evidence_source_adapter_v0_1_0.py \\
    --examples-dir <dir>

Exit codes:
  0 - valid
  1 - validation failure
  2 - usage or input-file error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DOCUMENT_TYPE = "proofrail.silver.evidence_source_adapter"
SCHEMA_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "v0.2.6"

SUPPORTED_SOURCE_TYPES = {
    "native_proofrail",
    "gateway",
    "observability_trace",
    "siem_log",
    "policy_engine",
    "grc_platform",
}

REQUIRED_CAPABILITIES = [
    "decision_event",
    "bypass_evidence",
    "revocation_status",
    "subject_hashes",
    "source_identity",
    "timestamp_integrity",
]

CAPABILITY_STATUSES = {"provided", "not_provided", "not_applicable"}

DECISION_EVENT_MAPPING_FIELDS = [
    "event_type",
    "timestamp_field",
    "decision_field",
    "reason_field",
    "source_record_id_field",
]

REQUIRED_TOP_LEVEL = [
    "document_type",
    "schema_version",
    "proofrail_release",
    "adapter_id",
    "adapter_version",
    "source",
    "trust_boundary",
    "control_surface",
    "protected_action_mapping",
    "evidence_capabilities",
    "normalization",
    "adapter_limitations",
    "non_claims",
]

REQUIRED_SOURCE_FIELDS = [
    "source_type",
    "source_name",
    "vendor_or_project",
    "product_or_component",
    "source_version",
    "deployment_scope",
]

REQUIRED_TRUST_BOUNDARY_FIELDS = [
    "source_is_trust_authority",
    "proofrail_role",
    "reliance_statement",
]

REQUIRED_CONTROL_SURFACE_FIELDS = [
    "control_surface_type",
    "description",
    "controlled_path_required",
    "protected_action_channel",
    "bypass_observation_point",
    "revocation_observation_point",
]

REQUIRED_PROTECTED_ACTION_MAPPING_FIELDS = [
    "protected_action_ids",
    "source_action_field",
    "source_actor_field",
    "source_subject_field",
]

ADAPTER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._\-]*$")
PROTECTED_ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


class ValidationError(Exception):
    """Stable-reason validation error."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def fail(reason: str, detail: str) -> ValidationError:
    return ValidationError(reason, detail)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _validate_top_level(doc: Any) -> None:
    if not isinstance(doc, dict):
        raise fail("invalid_adapter_descriptor", "root must be a JSON object")
    for f in REQUIRED_TOP_LEVEL:
        if f not in doc:
            raise fail("invalid_adapter_descriptor", f"missing required field: {f}")
    if doc.get("document_type") != DOCUMENT_TYPE:
        raise fail(
            "invalid_adapter_descriptor",
            f"document_type must be '{DOCUMENT_TYPE}'",
        )
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise fail(
            "invalid_adapter_descriptor",
            f"schema_version must be '{SCHEMA_VERSION}'",
        )
    if doc.get("proofrail_release") != PROOFRAIL_RELEASE:
        raise fail(
            "invalid_adapter_descriptor",
            f"proofrail_release must be '{PROOFRAIL_RELEASE}'",
        )
    adapter_id = doc.get("adapter_id")
    if not isinstance(adapter_id, str) or not ADAPTER_ID_RE.match(adapter_id):
        raise fail(
            "invalid_adapter_descriptor",
            "adapter_id must match ^[a-z0-9][a-z0-9._-]*$",
        )
    if not _is_nonempty_string(doc.get("adapter_version")):
        raise fail("invalid_adapter_descriptor", "adapter_version must be non-empty")


def _validate_source(source: Any) -> None:
    if not isinstance(source, dict):
        raise fail("invalid_adapter_descriptor", "source must be an object")
    for f in REQUIRED_SOURCE_FIELDS:
        if f not in source:
            raise fail("invalid_adapter_descriptor", f"source.{f} missing")
        if f == "source_type":
            continue
        if not _is_nonempty_string(source.get(f)):
            raise fail(
                "invalid_adapter_descriptor",
                f"source.{f} must be a non-empty string",
            )
    source_type = source.get("source_type")
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise fail(
            "invalid_source_type",
            f"source.source_type '{source_type}' is not in the v0.2.6 closed set",
        )


def _validate_trust_boundary(tb: Any) -> None:
    if not isinstance(tb, dict):
        raise fail("invalid_adapter_descriptor", "trust_boundary must be an object")
    for f in REQUIRED_TRUST_BOUNDARY_FIELDS:
        if f not in tb:
            raise fail("invalid_adapter_descriptor", f"trust_boundary.{f} missing")
    if tb.get("source_is_trust_authority") is not False:
        raise fail(
            "source_marked_as_trust_authority",
            "trust_boundary.source_is_trust_authority must be exactly false",
        )
    if tb.get("proofrail_role") != "evidence_source":
        raise fail(
            "invalid_adapter_descriptor",
            "trust_boundary.proofrail_role must equal 'evidence_source'",
        )
    if not _is_nonempty_string(tb.get("reliance_statement")):
        raise fail(
            "invalid_adapter_descriptor",
            "trust_boundary.reliance_statement must be a non-empty string",
        )


def _validate_control_surface(cs: Any) -> None:
    if not isinstance(cs, dict):
        raise fail("control_surface_missing", "control_surface must be an object")
    for f in REQUIRED_CONTROL_SURFACE_FIELDS:
        if f not in cs:
            raise fail("control_surface_missing", f"control_surface.{f} missing")
        if f == "controlled_path_required":
            if not isinstance(cs.get(f), bool):
                raise fail(
                    "control_surface_missing",
                    "control_surface.controlled_path_required must be a boolean",
                )
            continue
        if not _is_nonempty_string(cs.get(f)):
            raise fail(
                "control_surface_missing",
                f"control_surface.{f} must be a non-empty string",
            )


def _validate_protected_action_mapping(pam: Any) -> None:
    if not isinstance(pam, dict):
        raise fail(
            "protected_action_mapping_missing",
            "protected_action_mapping must be an object",
        )
    for f in REQUIRED_PROTECTED_ACTION_MAPPING_FIELDS:
        if f not in pam:
            raise fail(
                "protected_action_mapping_missing",
                f"protected_action_mapping.{f} missing",
            )
    ids = pam.get("protected_action_ids")
    if not isinstance(ids, list) or len(ids) == 0:
        raise fail(
            "protected_action_mapping_missing",
            "protected_action_ids must be a non-empty list",
        )
    for pid in ids:
        if not isinstance(pid, str) or not PROTECTED_ACTION_ID_RE.match(pid):
            raise fail(
                "protected_action_mapping_missing",
                f"protected_action_id '{pid}' is not a dotted identifier",
            )
    for f in ("source_action_field", "source_actor_field", "source_subject_field"):
        if not _is_nonempty_string(pam.get(f)):
            raise fail(
                "protected_action_mapping_missing",
                f"protected_action_mapping.{f} must be a non-empty string",
            )


def _validate_capability(name: str, cap: Any) -> None:
    if not isinstance(cap, dict):
        raise fail(
            "evidence_capability_missing",
            f"evidence_capabilities.{name} must be an object",
        )
    status = cap.get("status")
    if status not in CAPABILITY_STATUSES:
        raise fail(
            "evidence_capability_missing",
            f"evidence_capabilities.{name}.status must be one of "
            f"{sorted(CAPABILITY_STATUSES)}",
        )
    if status == "provided":
        if not _is_nonempty_string(cap.get("description")):
            raise fail(
                "evidence_capability_missing",
                f"evidence_capabilities.{name}.description must be a non-empty string",
            )
    else:
        if not _is_nonempty_string(cap.get("limitation")):
            raise fail(
                "evidence_capability_missing",
                f"evidence_capabilities.{name} status is '{status}' but limitation "
                "is missing or empty",
            )


def _validate_decision_event_mapping(cap: dict) -> None:
    if cap.get("status") != "provided":
        raise fail(
            "decision_event_mapping_missing",
            "evidence_capabilities.decision_event.status must be 'provided'",
        )
    for f in DECISION_EVENT_MAPPING_FIELDS:
        if not _is_nonempty_string(cap.get(f)):
            raise fail(
                "decision_event_mapping_missing",
                f"evidence_capabilities.decision_event.{f} must be a non-empty string",
            )


def _validate_evidence_capabilities(caps: Any) -> None:
    if not isinstance(caps, dict):
        raise fail("evidence_capability_missing", "evidence_capabilities must be an object")
    for required in REQUIRED_CAPABILITIES:
        if required not in caps:
            raise fail(
                "evidence_capability_missing",
                f"evidence_capabilities.{required} missing",
            )
    for name in REQUIRED_CAPABILITIES:
        _validate_capability(name, caps[name])
    _validate_decision_event_mapping(caps["decision_event"])


def _validate_sample_artifact_refs(refs: Any) -> None:
    if refs is None:
        return
    if not isinstance(refs, list):
        raise fail("invalid_adapter_descriptor", "sample_artifact_refs must be a list")
    for i, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise fail(
                "invalid_adapter_descriptor",
                f"sample_artifact_refs[{i}] must be an object",
            )
        path = ref.get("path")
        if not _is_nonempty_string(path):
            raise fail(
                "invalid_adapter_descriptor",
                f"sample_artifact_refs[{i}].path must be a non-empty string",
            )
        if ".." in Path(path).parts or path.startswith("/"):
            raise fail(
                "evidence_artifact_path_traversal",
                f"sample_artifact_refs[{i}].path '{path}' contains '..' or is absolute",
            )


def _validate_normalization(norm: Any) -> None:
    if not isinstance(norm, dict):
        raise fail("normalization_notes_missing", "normalization must be an object")
    if not _is_nonempty_string(norm.get("normalized_event_type")):
        raise fail(
            "normalization_notes_missing",
            "normalization.normalized_event_type must be a non-empty string",
        )
    notes = norm.get("normalization_notes")
    if not isinstance(notes, list) or len(notes) == 0:
        raise fail(
            "normalization_notes_missing",
            "normalization.normalization_notes must be a non-empty list",
        )
    for i, note in enumerate(notes):
        if not _is_nonempty_string(note):
            raise fail(
                "normalization_notes_missing",
                f"normalization.normalization_notes[{i}] must be a non-empty string",
            )


def _validate_string_list(value: Any, field_name: str, reason: str) -> None:
    if not isinstance(value, list) or len(value) == 0:
        raise fail(reason, f"{field_name} must be a non-empty list")
    for i, entry in enumerate(value):
        if not _is_nonempty_string(entry):
            raise fail(
                reason,
                f"{field_name}[{i}] must be a non-empty string",
            )


def validate_adapter(doc: Any) -> None:
    """Validate a parsed adapter descriptor; raise ValidationError on failure."""
    _validate_top_level(doc)
    _validate_source(doc["source"])
    _validate_trust_boundary(doc["trust_boundary"])
    _validate_control_surface(doc["control_surface"])
    _validate_protected_action_mapping(doc["protected_action_mapping"])
    _validate_evidence_capabilities(doc["evidence_capabilities"])
    _validate_sample_artifact_refs(doc.get("sample_artifact_refs"))
    _validate_normalization(doc["normalization"])
    _validate_string_list(
        doc.get("adapter_limitations"),
        "adapter_limitations",
        "adapter_limitations_missing",
    )
    _validate_string_list(
        doc.get("non_claims"),
        "non_claims",
        "adapter_non_claims_missing",
    )


def load_descriptor(path: Path) -> tuple[dict | None, ValidationError | None]:
    """Read and JSON-parse a descriptor file; returns (doc, None) or (None, err)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, fail("invalid_adapter_descriptor", f"cannot read '{path}': {e}")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return None, fail("invalid_adapter_descriptor", f"JSON parse error in '{path}': {e}")
    return doc, None


def validate_single(path: Path) -> int:
    doc, err = load_descriptor(path)
    if err is not None:
        print(f"FAIL: {err.reason}: {err.detail}", file=sys.stderr)
        return 1
    try:
        validate_adapter(doc)
    except ValidationError as e:
        print(f"FAIL: {e.reason}: {e.detail}", file=sys.stderr)
        return 1
    print(f"PASS: evidence source adapter valid ({doc['adapter_id']})")
    return 0


def validate_directory(directory: Path) -> int:
    if not directory.is_dir():
        print(f"ERROR: examples-dir '{directory}' is not a directory", file=sys.stderr)
        return 2
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".json")
    if not files:
        print(f"ERROR: no .json files found in '{directory}'", file=sys.stderr)
        return 2
    seen_ids: dict[str, Path] = {}
    failed = False
    for path in files:
        doc, err = load_descriptor(path)
        if err is not None:
            print(f"FAIL: {err.reason}: {err.detail}", file=sys.stderr)
            failed = True
            continue
        try:
            validate_adapter(doc)
        except ValidationError as e:
            print(f"FAIL: {e.reason}: {e.detail}", file=sys.stderr)
            failed = True
            continue
        adapter_id = doc["adapter_id"]
        if adapter_id in seen_ids:
            print(
                f"FAIL: duplicate_adapter_id: '{adapter_id}' appears in "
                f"both '{seen_ids[adapter_id]}' and '{path}'",
                file=sys.stderr,
            )
            failed = True
            continue
        seen_ids[adapter_id] = path
        print(f"PASS: evidence source adapter valid ({adapter_id})")
    if failed:
        return 1
    print(f"=== {len(files)}/{len(files)} adapter descriptors valid ===")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Silver Evidence Source Adapter v0.1.0 descriptors."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--adapter", type=Path, help="path to a single adapter descriptor JSON")
    group.add_argument(
        "--examples-dir",
        type=Path,
        help="path to a directory containing adapter descriptor JSON files",
    )
    args = parser.parse_args(argv)

    if args.adapter is not None:
        if not args.adapter.is_file():
            print(
                f"ERROR: adapter '{args.adapter}' is not a file",
                file=sys.stderr,
            )
            return 2
        return validate_single(args.adapter)
    return validate_directory(args.examples_dir)


if __name__ == "__main__":
    sys.exit(main())
