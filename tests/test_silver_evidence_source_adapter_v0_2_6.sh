#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.6 evidence source adapter profile.
#
# Covers 20 cases:
#   1.  Validate each of six canonical adapter descriptors individually.
#   2.  Validate the examples directory in one --examples-dir invocation.
#   3.  Inline: every canonical example has trust_boundary.source_is_trust_authority == false.
#   4.  Inline: every canonical example has non-empty adapter_limitations and non_claims.
#   5.  Inline: every canonical example declares all six required evidence capabilities.
#   6.  Tamper: malformed JSON -> invalid_adapter_descriptor (no Python traceback leakage).
#   7.  Tamper: unsupported source_type -> invalid_source_type.
#   8.  Tamper: source_is_trust_authority=true -> source_marked_as_trust_authority.
#   9.  Tamper: missing control_surface field -> control_surface_missing.
#   10. Tamper: empty protected_action_ids -> protected_action_mapping_missing.
#   11. Tamper: missing evidence_capabilities key -> evidence_capability_missing.
#   12. Tamper: decision_event status != provided -> decision_event_mapping_missing.
#   13. Tamper: empty normalization_notes -> normalization_notes_missing.
#   14. Tamper: empty adapter_limitations -> adapter_limitations_missing.
#   15. Tamper: empty non_claims -> adapter_non_claims_missing.
#   16. Tamper: sample_artifact_refs path traversal ('..') -> evidence_artifact_path_traversal.
#   17. Tamper: duplicate adapter_id across directory -> duplicate_adapter_id.
#   18. Tamper: sample_artifact_refs absolute path -> evidence_artifact_path_traversal.
#   19. Tamper: non-provided capability with blank limitation -> evidence_capability_missing.
#   20. Scoped mutation check: schema, validator, and examples unchanged by this test.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VALIDATOR="tools/silver/validate_evidence_source_adapter_v0_1_0.py"
EXAMPLES_DIR="examples/silver-evidence-source-adapters"
SCHEMA="schemas/silver-evidence-source-adapter-v0.1.0.md"

EXAMPLES=(
  "native-proofrail-v0.2.6.json"
  "gateway-mcp-simulated-v0.2.6.json"
  "observability-trace-simulated-v0.2.6.json"
  "siem-log-simulated-v0.2.6.json"
  "policy-engine-simulated-v0.2.6.json"
  "grc-platform-simulated-v0.2.6.json"
)

TMPDIR_ROOT="$(mktemp -d -t proofrail-v026-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

# Snapshot committed files for Step 18.
SNAP_BEFORE="$TMPDIR_ROOT/snap-before.sha256"
{
  shasum -a 256 "$SCHEMA" "$VALIDATOR"
  for f in "${EXAMPLES[@]}"; do
    shasum -a 256 "$EXAMPLES_DIR/$f"
  done
} > "$SNAP_BEFORE"

# Helper: load a canonical example into a fresh temp directory and edit it
# via inline Python. The validator is then re-run on the tampered copy and the
# expected failure reason must appear in stderr/stdout.
expect_fail_reason() {
    local pretty="$1"
    local source_example="$2"
    local expected_reason="$3"
    local py_edit="$4"
    local work="$TMPDIR_ROOT/$pretty"
    mkdir -p "$work"
    cp "$EXAMPLES_DIR/$source_example" "$work/adapter.json"
    if [ -n "$py_edit" ]; then
        python3 - "$work/adapter.json" <<PYEOF
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
doc = json.loads(p.read_text())
${py_edit}
p.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
PYEOF
    fi
    set +e
    python3 "$VALIDATOR" --adapter "$work/adapter.json" > "$work/out.log" 2>&1
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        echo "FAIL: expected nonzero exit for $pretty, got 0"
        cat "$work/out.log"
        exit 1
    fi
    if ! grep -q "$expected_reason" "$work/out.log"; then
        echo "FAIL: expected reason '$expected_reason' for $pretty"
        cat "$work/out.log"
        exit 1
    fi
    # Ensure no Python traceback leaks for any structured failure.
    if grep -q "Traceback" "$work/out.log"; then
        echo "FAIL: Python traceback leaked for $pretty"
        cat "$work/out.log"
        exit 1
    fi
    echo "PASS: $pretty -> $expected_reason"
}

# === Step 1: Validate each canonical descriptor individually ===
echo "=== Step 1: Validate each of six canonical descriptors individually ==="
for f in "${EXAMPLES[@]}"; do
    python3 "$VALIDATOR" --adapter "$EXAMPLES_DIR/$f" > /dev/null
done
echo "PASS: all six individual descriptors valid"

# === Step 2: Directory mode ===
echo "=== Step 2: Validate examples directory in one command ==="
python3 "$VALIDATOR" --examples-dir "$EXAMPLES_DIR" > "$TMPDIR_ROOT/dir.log"
if ! grep -q "=== 6/6 adapter descriptors valid ===" "$TMPDIR_ROOT/dir.log"; then
    echo "FAIL: directory mode did not report 6/6"
    cat "$TMPDIR_ROOT/dir.log"
    exit 1
fi
echo "PASS: 6/6 directory-mode validation"

# === Step 3: Inline trust-authority check ===
echo "=== Step 3: Every canonical example has source_is_trust_authority == false ==="
python3 - <<'PYEOF'
import json, sys
from pathlib import Path
examples_dir = Path("examples/silver-evidence-source-adapters")
for p in sorted(examples_dir.glob("*.json")):
    doc = json.loads(p.read_text())
    tb = doc.get("trust_boundary", {})
    if tb.get("source_is_trust_authority") is not False:
        print(f"FAIL: {p.name} has source_is_trust_authority != false", file=sys.stderr)
        sys.exit(1)
PYEOF
echo "PASS: all canonical examples have source_is_trust_authority == false"

# === Step 4: Inline limitations/non_claims check ===
echo "=== Step 4: Every canonical example has non-empty adapter_limitations and non_claims ==="
python3 - <<'PYEOF'
import json, sys
from pathlib import Path
examples_dir = Path("examples/silver-evidence-source-adapters")
for p in sorted(examples_dir.glob("*.json")):
    doc = json.loads(p.read_text())
    for k in ("adapter_limitations", "non_claims"):
        v = doc.get(k)
        if not isinstance(v, list) or not v:
            print(f"FAIL: {p.name} field {k} empty or missing", file=sys.stderr)
            sys.exit(1)
        for entry in v:
            if not isinstance(entry, str) or not entry.strip():
                print(f"FAIL: {p.name} {k} entry empty/whitespace", file=sys.stderr)
                sys.exit(1)
PYEOF
echo "PASS: all canonical examples have non-empty adapter_limitations and non_claims"

# === Step 5: Inline capability completeness ===
echo "=== Step 5: Every canonical example declares all six required capabilities ==="
python3 - <<'PYEOF'
import json, sys
from pathlib import Path
required = [
    "decision_event",
    "bypass_evidence",
    "revocation_status",
    "subject_hashes",
    "source_identity",
    "timestamp_integrity",
]
examples_dir = Path("examples/silver-evidence-source-adapters")
for p in sorted(examples_dir.glob("*.json")):
    doc = json.loads(p.read_text())
    caps = doc.get("evidence_capabilities", {})
    missing = [k for k in required if k not in caps]
    if missing:
        print(f"FAIL: {p.name} missing capabilities {missing}", file=sys.stderr)
        sys.exit(1)
PYEOF
echo "PASS: all canonical examples declare all six required capabilities"

# === Step 6: Tamper -- malformed JSON ===
echo "=== Step 6: Malformed JSON -> invalid_adapter_descriptor ==="
MAL="$TMPDIR_ROOT/malformed.json"
echo '{"document_type": "proofrail.silver.evidence_source_adapter", "schema_version":' > "$MAL"
set +e
python3 "$VALIDATOR" --adapter "$MAL" > "$TMPDIR_ROOT/mal.log" 2>&1
RC=$?
set -e
if [ "$RC" -eq 0 ]; then
    echo "FAIL: expected nonzero exit for malformed JSON"
    cat "$TMPDIR_ROOT/mal.log"
    exit 1
fi
if ! grep -q "invalid_adapter_descriptor" "$TMPDIR_ROOT/mal.log"; then
    echo "FAIL: expected invalid_adapter_descriptor for malformed JSON"
    cat "$TMPDIR_ROOT/mal.log"
    exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/mal.log"; then
    echo "FAIL: Python traceback leaked for malformed JSON"
    cat "$TMPDIR_ROOT/mal.log"
    exit 1
fi
echo "PASS: malformed JSON -> invalid_adapter_descriptor (no traceback)"

# === Step 7: Tamper -- unsupported source_type ===
echo "=== Step 7: Unsupported source_type -> invalid_source_type ==="
expect_fail_reason "step07-bad-source-type" \
    "native-proofrail-v0.2.6.json" \
    "invalid_source_type" \
    'doc["source"]["source_type"] = "not_in_closed_set"'

# === Step 8: Tamper -- trust authority asserted ===
echo "=== Step 8: source_is_trust_authority=true -> source_marked_as_trust_authority ==="
expect_fail_reason "step08-trust-authority-true" \
    "native-proofrail-v0.2.6.json" \
    "source_marked_as_trust_authority" \
    'doc["trust_boundary"]["source_is_trust_authority"] = True'

# === Step 9: Tamper -- missing control_surface field ===
echo "=== Step 9: Missing control_surface field -> control_surface_missing ==="
expect_fail_reason "step09-missing-control-surface-field" \
    "gateway-mcp-simulated-v0.2.6.json" \
    "control_surface_missing" \
    'del doc["control_surface"]["bypass_observation_point"]'

# === Step 10: Tamper -- empty protected_action_ids ===
echo "=== Step 10: Empty protected_action_ids -> protected_action_mapping_missing ==="
expect_fail_reason "step10-empty-protected-action-ids" \
    "gateway-mcp-simulated-v0.2.6.json" \
    "protected_action_mapping_missing" \
    'doc["protected_action_mapping"]["protected_action_ids"] = []'

# === Step 11: Tamper -- missing required capability key ===
echo "=== Step 11: Missing evidence_capabilities key -> evidence_capability_missing ==="
expect_fail_reason "step11-missing-capability-key" \
    "policy-engine-simulated-v0.2.6.json" \
    "evidence_capability_missing" \
    'del doc["evidence_capabilities"]["subject_hashes"]'

# === Step 12: Tamper -- decision_event not provided ===
echo "=== Step 12: decision_event.status != provided -> decision_event_mapping_missing ==="
expect_fail_reason "step12-decision-event-not-provided" \
    "siem-log-simulated-v0.2.6.json" \
    "decision_event_mapping_missing" \
    'doc["evidence_capabilities"]["decision_event"] = {"status": "not_provided", "limitation": "withheld in this scenario"}'

# === Step 13: Tamper -- empty normalization_notes ===
echo "=== Step 13: Empty normalization_notes -> normalization_notes_missing ==="
expect_fail_reason "step13-empty-normalization-notes" \
    "observability-trace-simulated-v0.2.6.json" \
    "normalization_notes_missing" \
    'doc["normalization"]["normalization_notes"] = []'

# === Step 14: Tamper -- empty adapter_limitations entry (whitespace-only) ===
echo "=== Step 14: Whitespace-only adapter_limitations entry -> adapter_limitations_missing ==="
expect_fail_reason "step14-empty-adapter-limitations" \
    "observability-trace-simulated-v0.2.6.json" \
    "adapter_limitations_missing" \
    'doc["adapter_limitations"] = ["   "]'

# === Step 15: Tamper -- empty non_claims ===
echo "=== Step 15: Empty non_claims -> adapter_non_claims_missing ==="
expect_fail_reason "step15-empty-non-claims" \
    "grc-platform-simulated-v0.2.6.json" \
    "adapter_non_claims_missing" \
    'doc["non_claims"] = []'

# === Step 16: Tamper -- sample_artifact_refs path traversal ===
echo "=== Step 16: sample_artifact_refs path traversal -> evidence_artifact_path_traversal ==="
expect_fail_reason "step16-path-traversal" \
    "native-proofrail-v0.2.6.json" \
    "evidence_artifact_path_traversal" \
    'doc["sample_artifact_refs"] = [{"path": "../etc/passwd", "description": "tamper"}]'

# === Step 17: Tamper -- duplicate adapter_id across directory ===
echo "=== Step 17: Duplicate adapter_id -> duplicate_adapter_id ==="
DUPE_DIR="$TMPDIR_ROOT/dupe-dir"
mkdir -p "$DUPE_DIR"
cp "$EXAMPLES_DIR"/*.json "$DUPE_DIR/"
# Create a second file containing the same adapter_id as native-proofrail.
python3 - "$DUPE_DIR" <<'PYEOF'
import json, sys, shutil
from pathlib import Path
d = Path(sys.argv[1])
src = d / "native-proofrail-v0.2.6.json"
dst = d / "native-proofrail-duplicate.json"
shutil.copy(src, dst)
# Same adapter_id, different file name -> directory mode must report duplicate_adapter_id.
PYEOF
set +e
python3 "$VALIDATOR" --examples-dir "$DUPE_DIR" > "$TMPDIR_ROOT/dupe.log" 2>&1
RC=$?
set -e
if [ "$RC" -eq 0 ]; then
    echo "FAIL: expected nonzero exit for duplicate adapter_id"
    cat "$TMPDIR_ROOT/dupe.log"
    exit 1
fi
if ! grep -q "duplicate_adapter_id" "$TMPDIR_ROOT/dupe.log"; then
    echo "FAIL: expected duplicate_adapter_id in output"
    cat "$TMPDIR_ROOT/dupe.log"
    exit 1
fi
echo "PASS: duplicate adapter_id -> duplicate_adapter_id"

# === Step 18: Tamper -- sample_artifact_refs absolute path ===
echo "=== Step 18: sample_artifact_refs absolute path -> evidence_artifact_path_traversal ==="
expect_fail_reason "step18-absolute-path" \
    "native-proofrail-v0.2.6.json" \
    "evidence_artifact_path_traversal" \
    'doc["sample_artifact_refs"] = [{"path": "/etc/passwd", "description": "absolute path tamper"}]'

# === Step 19: Tamper -- non-provided capability with blank limitation ===
echo "=== Step 19: Non-provided capability with blank limitation -> evidence_capability_missing ==="
expect_fail_reason "step19-blank-limitation" \
    "observability-trace-simulated-v0.2.6.json" \
    "evidence_capability_missing" \
    'doc["evidence_capabilities"]["bypass_evidence"] = {"status": "not_provided", "limitation": "   "}'

# === Step 20: Scoped mutation check ===
echo "=== Step 20: Schema, validator, and canonical examples unchanged by this test ==="
SNAP_AFTER="$TMPDIR_ROOT/snap-after.sha256"
{
  shasum -a 256 "$SCHEMA" "$VALIDATOR"
  for f in "${EXAMPLES[@]}"; do
    shasum -a 256 "$EXAMPLES_DIR/$f"
  done
} > "$SNAP_AFTER"
if ! diff "$SNAP_BEFORE" "$SNAP_AFTER" > "$TMPDIR_ROOT/snap.diff"; then
    echo "FAIL: committed v0.2.6 adapter files were modified by the test runtime:"
    cat "$TMPDIR_ROOT/snap.diff"
    exit 1
fi
echo "PASS: schema, validator, and canonical examples unchanged"

echo
echo "===================================================================="
echo "=== ProofRail Silver v0.2.6 evidence source adapter: 20/20 PASS ==="
echo "===================================================================="
