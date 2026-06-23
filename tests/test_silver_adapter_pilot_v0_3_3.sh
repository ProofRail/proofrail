#!/usr/bin/env bash
# tests/test_silver_adapter_pilot_v0_3_3.sh
#
# Regression test for the ProofRail Silver v0.3.3 Adapter Pilot Package.
#
# Numbered exercises (36 total):
#
#   Positive-path (4):
#     PP1  Pristine end-to-end build with --self-validate
#     PP2  Pristine independent verifier pass on the package
#     PP3  Inline structural cross-check of manifest subject layout
#     PP4  Inline structural cross-check of adapter pilot report
#
#   Verifier mutation cases (25; cover 24 stable verifier reasons,
#   with adapter_pilot_subject_path_traversal exercised twice — once
#   for the `..` form and once for the absolute-path form):
#     case01   invalid_adapter_pilot_manifest
#     case02a  adapter_pilot_subject_path_traversal      (..)
#     case02b  adapter_pilot_subject_path_traversal      (absolute)
#     case03   adapter_pilot_subject_file_missing
#     case04   adapter_pilot_subject_hash_mismatch
#     case05   adapter_pilot_source_marked_authority     (pre-check)
#     case06   adapter_pilot_adapter_invalid             (v0.2.6 sub)
#     case07   source_export_invalid
#     case08   source_export_duplicate
#     case09   source_export_time_order_invalid
#     case10   normalization_map_invalid
#     case11   normalization_required_field_missing
#     case12   normalized_trace_invalid
#     case13   normalized_trace_mismatch
#     case14   nested_trace_binding_invalid
#     case15   nested_trace_binding_mismatch
#     case16   adapter_pilot_report_invalid
#     case17   adapter_pilot_report_binding_mismatch
#     case18   adapter_pilot_report_count_mismatch
#     case19   adapter_pilot_claim_missing
#     case20   adapter_pilot_claim_failed
#     case21   adapter_pilot_evidence_ref_invalid
#     case22   adapter_pilot_limitations_missing
#     case23   adapter_pilot_non_claims_missing
#     case24   adapter_pilot_overclaim                    (Amendment 3)
#
#   Runner-only refusal cases (6):
#     case25   adapter_validation_failed
#     case26   source_export_validation_failed
#     case27   normalization_map_validation_failed
#     case28   binding_set_validation_failed
#     case29   nested_trace_binding_generation_failed
#     case30   adapter_pilot_self_validation_failed
#
#   Scoped sha256 snapshot (1):
#     SS     scoped sha256 snapshot of 9 committed v0.3.3 source paths
#            BEFORE and AFTER all cases must be identical
#
# Coverage summary:
#   * 24/24 stable verifier failure reasons covered. No reason is
#     OR-accepted; each case asserts its exact stable reason.
#   * 6/6 runner-only refusal codes covered.
#   * Atomic --force semantics asserted: runner refusals leave NO final
#     --output-dir and NO staging sibling on disk.
#
# Notes on reachability (matches the four orderings documented in
# docs/silver/silver-adapter-pilot-package-v0.3.3.md):
#   * adapter_pilot_subject_path_traversal is DIRECTLY reachable. The
#     verifier checks each subject's `path` for traversal (`..`) or an
#     absolute prefix BEFORE comparing it against the fixed safe
#     SUBJECT_ORDER. Both forms therefore fire this exact reason.
#   * adapter_pilot_source_marked_authority is DIRECTLY reachable. The
#     verifier runs the adapter trust-authority pre-check BEFORE the
#     v0.2.6 adapter validator subprocess, so a tampered adapter with
#     `source_is_trust_authority: true` always fires this specific
#     reason instead of collapsing into adapter_pilot_adapter_invalid.
#   * normalized_trace_mismatch is DIRECTLY reachable. The verifier
#     re-derives normalized event bytes BEFORE invoking the nested
#     v0.3.2 verifier, so mutating the packaged normalized events file
#     (in a still-parseable way) fires this specific reason instead of
#     collapsing into nested_trace_binding_invalid.
#   * nested_trace_binding_invalid is DIRECTLY reachable. The verifier
#     runs the nested v0.3.2 verifier subprocess BEFORE the outer-vs-
#     nested subject-hash cross-check, so tampering the nested manifest
#     fires this specific reason instead of collapsing into
#     nested_trace_binding_mismatch.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER="$REPO_ROOT/tools/silver/build_silver_adapter_pilot_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_adapter_pilot_v0_1_0.py"
ADAPTER="$REPO_ROOT/examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json"
SOURCE_EXPORT="$REPO_ROOT/fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl"
NORM_MAP="$REPO_ROOT/fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json"
BINDINGS="$REPO_ROOT/fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json"

WORK="$(mktemp -d -t proofrail-v0.3.3-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

PRISTINE="$WORK/pristine"
GEN_AT="2026-06-22T00:10:00Z"
REPORT_ID="silver-adapter-pilot-v0.3.3-test-001"

# --- Scoped sha256 snapshot of committed v0.3.3 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-adapter-pilot-manifest-v0.1.0.md"
  "schemas/silver-adapter-pilot-normalization-map-v0.1.0.md"
  "schemas/silver-adapter-pilot-report-v0.1.0.md"
  "schemas/silver-adapter-pilot-source-export-v0.1.0.md"
  "fixtures/silver-adapter-pilot-package-v0.3.3/README.md"
  "fixtures/silver-adapter-pilot-package-v0.3.3/normalization-map.json"
  "fixtures/silver-adapter-pilot-package-v0.3.3/source-otel-trace-export.jsonl"
  "tools/silver/build_silver_adapter_pilot_v0_1_0.py"
  "tools/silver/verify_silver_adapter_pilot_v0_1_0.py"
)
snapshot_scoped() {
  local out="$1"
  : > "$out"
  for rel in "${SCOPED_FILES[@]}"; do
    python3 -c "
import hashlib
p = '$REPO_ROOT/' + '$rel'
h = hashlib.sha256()
with open(p, 'rb') as f:
    for c in iter(lambda: f.read(65536), b''): h.update(c)
print('$rel', h.hexdigest())
" >> "$out"
  done
}
snapshot_scoped "$WORK/scoped.before"

# ---------------------------------------------------------------------------
# Step 1 (PP1): pristine build with --self-validate.
# ---------------------------------------------------------------------------
echo "[step1] pristine adapter pilot build with --self-validate"
python3 "$RUNNER" \
  --adapter "$ADAPTER" \
  --source-export "$SOURCE_EXPORT" \
  --normalization-map "$NORM_MAP" \
  --bindings "$BINDINGS" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] pristine independent verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/silver-adapter-pilot-manifest.json" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of adapter pilot manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] inline manifest layout check"
python3 - <<EOF
import json
m = json.loads(open("$PRISTINE/silver-adapter-pilot-manifest.json").read())
assert m["document_type"] == "proofrail.silver.adapter_pilot_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "v0.3.3"
assert m["hash_algorithm"] == "sha256"
assert len(m["subjects"]) == 7
expected = [
  ("adapter/observability-trace-simulated-v0.2.6.json",
   "adapter_descriptor"),
  ("source/source-otel-trace-export.jsonl",
   "source_export"),
  ("normalization/normalization-map.json",
   "normalization_map"),
  ("normalized/trace-events.jsonl",
   "normalized_trace_events"),
  ("normalized/trace-claim-bindings.json",
   "normalized_trace_claim_bindings"),
  ("trace-binding/silver-trace-binding-manifest.json",
   "nested_trace_binding_manifest"),
  ("silver-adapter-pilot-report.json",
   "adapter_pilot_report"),
]
for i, (p, r) in enumerate(expected):
    assert m["subjects"][i]["path"] == p, (i, m["subjects"][i]["path"])
    assert m["subjects"][i]["role"] == r, (i, m["subjects"][i]["role"])
    assert m["subjects"][i]["sha256"].startswith("sha256:")
    assert len(m["subjects"][i]["sha256"]) == 7 + 64
    assert isinstance(m["subjects"][i]["size_bytes"], int)
    assert m["subjects"][i]["size_bytes"] >= 0
assert isinstance(m["scope_limitations"], list) and len(m["scope_limitations"]) > 0
assert isinstance(m["non_claims"], list) and len(m["non_claims"]) > 0
EOF

# ---------------------------------------------------------------------------
# Step 4 (PP4): inline structural check of adapter pilot report contents.
# ---------------------------------------------------------------------------
echo "[step4] inline report contents check"
python3 - <<EOF
import json
r = json.loads(open("$PRISTINE/silver-adapter-pilot-report.json").read())
assert r["document_type"] == "proofrail.silver.adapter_pilot_report"
assert r["proofrail_release"] == "v0.3.3"
assert r["adapter"]["source_is_trust_authority"] is False
assert r["source_export"]["source_record_count"] == 8, r["source_export"]
assert r["source_export"]["source_format"] == "proofrail.simulated_otel_trace_export.v0.1"
assert r["normalization"]["normalized_event_count"] == 8, r["normalization"]
assert r["nested_trace_binding"]["verification_status"] == "pass"
ps = r["pilot_summary"]
assert ps["source_is_trust_authority"] is False
assert ps["normalization_status"] == "pass"
assert ps["nested_trace_binding_status"] == "pass"
assert ps["normalized_events_match_source"] is True
assert ps["runtime_truth_claimed"] is False
claim_ids = {c["claim_id"] for c in r["claims"]}
required = {
    "adapter_descriptor_valid",
    "source_not_trust_authority",
    "source_export_hash_verifiable",
    "normalization_map_valid",
    "normalized_trace_events_rederived",
    "nested_trace_binding_valid",
    "no_runtime_truth_claimed",
}
assert required.issubset(claim_ids), (required - claim_ids)
for c in r["claims"]:
    assert c["status"] == "pass", c
EOF

# ---------------------------------------------------------------------------
# Helpers for tampered-package cases.
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# Recompute sha256 + size_bytes for a single subject index in the
# outer adapter pilot manifest, after a semantic edit. Lets a mutation
# reach the intended later check instead of short-circuiting on
# adapter_pilot_subject_hash_mismatch.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "silver-adapter-pilot-manifest.json")
m = json.loads(open(mp).read())
sp = os.path.join(pkg, m["subjects"][idx]["path"])
h = hashlib.sha256()
with open(sp, "rb") as f:
    for c in iter(lambda: f.read(65536), b""):
        h.update(c)
m["subjects"][idx]["sha256"] = "sha256:" + h.hexdigest()
m["subjects"][idx]["size_bytes"] = os.path.getsize(sp)
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
}

# expect_verifier_fail <label> <pkg_dir> <expected_reason>
expect_verifier_fail() {
  local label="$1" pkg="$2" expected="$3"
  set +e
  local out rc
  out="$(python3 "$VERIFIER" --manifest "$pkg/silver-adapter-pilot-manifest.json" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: $label: expected nonzero exit, got 0"
    echo "$out"
    exit 1
  fi
  if ! echo "$out" | grep -qE "^FAIL: ${expected}:"; then
    echo "FAIL: $label: did not see expected reason ($expected)"
    echo "----- verifier output -----"
    echo "$out"
    echo "---------------------------"
    exit 1
  fi
  if echo "$out" | grep -q "Traceback"; then
    echo "FAIL: $label: verifier produced an unexpected Traceback"
    echo "$out"
    exit 1
  fi
  echo "  $label: ok ($(echo "$out" | head -n1))"
}

# expect_runner_fail <label> <expected_code> <outdir> <runner-args...>
expect_runner_fail() {
  local label="$1" expected="$2" outdir="$3"
  shift 3
  set +e
  local out rc
  out="$(python3 "$RUNNER" "$@" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -ne 1 ]; then
    echo "FAIL: $label: expected runner exit 1, got $rc"
    echo "$out"
    exit 1
  fi
  if ! echo "$out" | grep -qE "^FAIL: ${expected}:"; then
    echo "FAIL: $label: did not see expected runner refusal ($expected)"
    echo "----- runner output -----"
    echo "$out"
    echo "-------------------------"
    exit 1
  fi
  if echo "$out" | grep -q "Traceback"; then
    echo "FAIL: $label: runner produced an unexpected Traceback"
    echo "$out"
    exit 1
  fi
  if [ -e "$outdir" ]; then
    echo "FAIL: $label: output dir was created despite refusal: $outdir"
    exit 1
  fi
  local stage_pattern="${outdir}.staging."
  if ls "${stage_pattern}"* >/dev/null 2>&1; then
    echo "FAIL: $label: staging dir leaked: ${stage_pattern}*"
    exit 1
  fi
  echo "  $label: ok ($(echo "$out" | head -n1))"
}

echo "[cases] running 25 verifier mutation cases + 6 runner-only cases"

# ---------------------------------------------------------------------------
# Case 01: invalid_adapter_pilot_manifest — wrong manifest document_type.
# Fires at the structural manifest-shape validation step.
# ---------------------------------------------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-adapter-pilot-manifest.json"
m = json.loads(open(mp).read())
m["document_type"] = "proofrail.silver.NOT_an_adapter_pilot_manifest"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case01:invalid_adapter_pilot_manifest" "$T" \
  "invalid_adapter_pilot_manifest"

# ---------------------------------------------------------------------------
# Case 02a: adapter_pilot_subject_path_traversal — subject[0].path becomes
# "../etc/passwd". Checked BEFORE exact SUBJECT_ORDER equality.
# ---------------------------------------------------------------------------
T="$WORK/c02a"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-adapter-pilot-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][0]["path"] = "../etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02a:adapter_pilot_subject_path_traversal(..)" "$T" \
  "adapter_pilot_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 02b: adapter_pilot_subject_path_traversal — subject[6].path becomes
# an absolute path. Same reason, different traversal form.
# ---------------------------------------------------------------------------
T="$WORK/c02b"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-adapter-pilot-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][6]["path"] = "/etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02b:adapter_pilot_subject_path_traversal(absolute)" "$T" \
  "adapter_pilot_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 03: adapter_pilot_subject_file_missing — delete subject[6] (the
# adapter pilot report).
# ---------------------------------------------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
rm -f "$T/silver-adapter-pilot-report.json"
expect_verifier_fail "case03:adapter_pilot_subject_file_missing" "$T" \
  "adapter_pilot_subject_file_missing"

# ---------------------------------------------------------------------------
# Case 04: adapter_pilot_subject_hash_mismatch — modify subject[6] without
# rehashing the manifest.
# ---------------------------------------------------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
printf "\n" >> "$T/silver-adapter-pilot-report.json"
expect_verifier_fail "case04:adapter_pilot_subject_hash_mismatch" "$T" \
  "adapter_pilot_subject_hash_mismatch"

# ---------------------------------------------------------------------------
# Case 05: adapter_pilot_source_marked_authority — set the adapter's
# trust_boundary.source_is_trust_authority to true. Verifier's structural
# pre-check runs BEFORE the v0.2.6 adapter validator subprocess, so this
# fires the specific reason instead of being collapsed into
# adapter_pilot_adapter_invalid. Requires rehashing subject[0].
# ---------------------------------------------------------------------------
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys, os
ad = os.path.join(sys.argv[1], "adapter")
fn = next(f for f in os.listdir(ad) if f.endswith(".json"))
ap = os.path.join(ad, fn)
a = json.loads(open(ap).read())
a["trust_boundary"]["source_is_trust_authority"] = True
open(ap, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 0
expect_verifier_fail "case05:adapter_pilot_source_marked_authority" "$T" \
  "adapter_pilot_source_marked_authority"

# ---------------------------------------------------------------------------
# Case 06: adapter_pilot_adapter_invalid — break the adapter in a way
# that does NOT touch source_is_trust_authority, so it falls through to
# the unchanged v0.2.6 adapter validator subprocess. Wrong document_type
# is a generic v0.2.6 structural failure. Requires rehashing subject[0].
# ---------------------------------------------------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys, os
ad = os.path.join(sys.argv[1], "adapter")
fn = next(f for f in os.listdir(ad) if f.endswith(".json"))
ap = os.path.join(ad, fn)
a = json.loads(open(ap).read())
a["document_type"] = "proofrail.silver.NOT_an_evidence_source_adapter"
open(ap, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 0
expect_verifier_fail "case06:adapter_pilot_adapter_invalid" "$T" \
  "adapter_pilot_adapter_invalid"

# ---------------------------------------------------------------------------
# Case 07: source_export_invalid — append an unparseable record to the
# source export. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
printf "this is not a valid JSON line\n" >> "$T/source/source-otel-trace-export.jsonl"
rehash_subject "$T" 1
expect_verifier_fail "case07:source_export_invalid" "$T" \
  "source_export_invalid"

# ---------------------------------------------------------------------------
# Case 08: source_export_duplicate — duplicate the (trace_id, span_id)
# pair across two adjacent records by copying record 0's span identifiers
# onto record 1. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ep = sys.argv[1] + "/source/source-otel-trace-export.jsonl"
lines = [ln for ln in open(ep).read().splitlines() if ln.strip()]
rec0 = json.loads(lines[0])
rec1 = json.loads(lines[1])
rec1["span"]["trace_id"] = rec0["span"]["trace_id"]
rec1["span"]["span_id"] = rec0["span"]["span_id"]
lines[1] = json.dumps(rec1, separators=(",", ":"))
open(ep, "w").write("\n".join(lines) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case08:source_export_duplicate" "$T" \
  "source_export_duplicate"

# ---------------------------------------------------------------------------
# Case 09: source_export_time_order_invalid — swap span.start_time on
# adjacent records so the strict ascending ordering breaks. Requires
# rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ep = sys.argv[1] + "/source/source-otel-trace-export.jsonl"
lines = [ln for ln in open(ep).read().splitlines() if ln.strip()]
rec0 = json.loads(lines[0])
rec1 = json.loads(lines[1])
rec0["span"]["start_time"], rec1["span"]["start_time"] = (
    rec1["span"]["start_time"], rec0["span"]["start_time"]
)
lines[0] = json.dumps(rec0, separators=(",", ":"))
lines[1] = json.dumps(rec1, separators=(",", ":"))
open(ep, "w").write("\n".join(lines) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case09:source_export_time_order_invalid" "$T" \
  "source_export_time_order_invalid"

# ---------------------------------------------------------------------------
# Case 10: normalization_map_invalid — wrong normalization-map
# document_type. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
np = sys.argv[1] + "/normalization/normalization-map.json"
n = json.loads(open(np).read())
n["document_type"] = "proofrail.silver.NOT_a_normalization_map"
open(np, "w").write(json.dumps(n, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case10:normalization_map_invalid" "$T" \
  "normalization_map_invalid"

# ---------------------------------------------------------------------------
# Case 11: normalization_required_field_missing — remove the
# field_mappings entry for `event_id` while keeping it in
# required_target_fields. parse_normalization_map still accepts the
# structurally valid map; derive_normalized_events then fires this
# reason on the first record. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
np = sys.argv[1] + "/normalization/normalization-map.json"
n = json.loads(open(np).read())
del n["field_mappings"]["event_id"]
open(np, "w").write(json.dumps(n, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case11:normalization_required_field_missing" "$T" \
  "normalization_required_field_missing"

# ---------------------------------------------------------------------------
# Case 12: normalized_trace_invalid — append an unparseable line to the
# packaged normalized trace events. parse_normalized_packaged (step 12)
# fires BEFORE the re-derive equality check. Requires rehashing
# subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
printf "this is not a valid JSON line\n" >> "$T/normalized/trace-events.jsonl"
rehash_subject "$T" 3
expect_verifier_fail "case12:normalized_trace_invalid" "$T" \
  "normalized_trace_invalid"

# ---------------------------------------------------------------------------
# Case 13: normalized_trace_mismatch — add an extra harmless attribute
# to one packaged normalized event so the file still parses as JSON,
# but its bytes no longer equal the re-derived bytes. Requires
# rehashing subject[3]. Step 13 runs BEFORE the nested v0.3.2 verifier
# subprocess (step 14), so this fires the specific reason.
# ---------------------------------------------------------------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ep = sys.argv[1] + "/normalized/trace-events.jsonl"
lines = [ln for ln in open(ep).read().splitlines() if ln.strip()]
ev0 = json.loads(lines[0])
ev0["__extra_test_attr"] = "x"
lines[0] = json.dumps(ev0, sort_keys=True, separators=(",", ":"))
open(ep, "w").write("\n".join(lines) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case13:normalized_trace_mismatch" "$T" \
  "normalized_trace_mismatch"

# ---------------------------------------------------------------------------
# Case 14: nested_trace_binding_invalid — break the nested v0.3.2
# manifest's document_type. The nested v0.3.2 verifier subprocess fails
# at step 14, BEFORE the outer-vs-nested subject-hash cross-check.
# Requires rehashing subject[5].
# ---------------------------------------------------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
np = sys.argv[1] + "/trace-binding/silver-trace-binding-manifest.json"
n = json.loads(open(np).read())
n["document_type"] = "proofrail.silver.NOT_a_trace_binding_manifest"
open(np, "w").write(json.dumps(n, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 5
expect_verifier_fail "case14:nested_trace_binding_invalid" "$T" \
  "nested_trace_binding_invalid"

# ---------------------------------------------------------------------------
# Case 15: nested_trace_binding_mismatch — re-emit the OUTER adapter
# file with a different JSON indent so its bytes (and sha256) differ
# from the nested adapter copy under trace-binding/adapter/. The nested
# v0.3.2 verifier still passes (it reads the unchanged nested copy);
# step 15 then fires because outer subjects[0].sha256 does not equal
# nested subjects[0].sha256. Requires rehashing outer subject[0].
# ---------------------------------------------------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys, os
ad = os.path.join(sys.argv[1], "adapter")
fn = next(f for f in os.listdir(ad) if f.endswith(".json"))
ap = os.path.join(ad, fn)
a = json.loads(open(ap).read())
# Re-emit with different indentation; same JSON value, different bytes.
open(ap, "w").write(json.dumps(a, indent=4, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 0
expect_verifier_fail "case15:nested_trace_binding_mismatch" "$T" \
  "nested_trace_binding_mismatch"

# ---------------------------------------------------------------------------
# Case 16: adapter_pilot_report_invalid — wrong report document_type.
# Requires rehashing subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["document_type"] = "proofrail.silver.NOT_an_adapter_pilot_report"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case16:adapter_pilot_report_invalid" "$T" \
  "adapter_pilot_report_invalid"

# ---------------------------------------------------------------------------
# Case 17: adapter_pilot_report_binding_mismatch — corrupt
# source_export.source_export_sha256 in the report. Requires rehashing
# subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["source_export"]["source_export_sha256"] = "sha256:" + "0" * 64
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case17:adapter_pilot_report_binding_mismatch" "$T" \
  "adapter_pilot_report_binding_mismatch"

# ---------------------------------------------------------------------------
# Case 18: adapter_pilot_report_count_mismatch — bump
# normalization.normalized_event_count to a wrong value without changing
# anything else. Requires rehashing subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["normalization"]["normalized_event_count"] = (
    r["normalization"]["normalized_event_count"] + 7
)
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case18:adapter_pilot_report_count_mismatch" "$T" \
  "adapter_pilot_report_count_mismatch"

# ---------------------------------------------------------------------------
# Case 19: adapter_pilot_claim_missing — drop the `no_runtime_truth_claimed`
# claim entry from the report. Requires rehashing subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["claims"] = [c for c in r["claims"]
               if c["claim_id"] != "no_runtime_truth_claimed"]
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case19:adapter_pilot_claim_missing" "$T" \
  "adapter_pilot_claim_missing"

# ---------------------------------------------------------------------------
# Case 20: adapter_pilot_claim_failed — change the `adapter_descriptor_valid`
# claim's status from "pass" to "fail". Requires rehashing subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
for c in r["claims"]:
    if c["claim_id"] == "adapter_descriptor_valid":
        c["status"] = "fail"
        break
else:
    raise SystemExit("target claim not found")
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case20:adapter_pilot_claim_failed" "$T" \
  "adapter_pilot_claim_failed"

# ---------------------------------------------------------------------------
# Case 21: adapter_pilot_evidence_ref_invalid — rewrite the
# `adapter_descriptor_valid` claim's evidence_refs[0] to a path-traversal
# value. The required-claim-status check (steps 19–20) still passes;
# step 21 then fires on the bad evidence ref. Requires rehashing
# subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
for c in r["claims"]:
    if c["claim_id"] == "adapter_descriptor_valid":
        c["evidence_refs"] = ["../etc/passwd"]
        break
else:
    raise SystemExit("target claim not found")
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case21:adapter_pilot_evidence_ref_invalid" "$T" \
  "adapter_pilot_evidence_ref_invalid"

# ---------------------------------------------------------------------------
# Case 22: adapter_pilot_limitations_missing — manifest-level
# scope_limitations becomes an empty list. Structural pre-check accepts
# an empty list of strings; the dedicated emptiness check fires later.
# ---------------------------------------------------------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-adapter-pilot-manifest.json"
m = json.loads(open(mp).read())
m["scope_limitations"] = []
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case22:adapter_pilot_limitations_missing" "$T" \
  "adapter_pilot_limitations_missing"

# ---------------------------------------------------------------------------
# Case 23: adapter_pilot_non_claims_missing — report-level non_claims
# becomes a list with a single blank entry. Requires rehashing
# subject[6] so the verifier reaches the dedicated emptiness check.
# ---------------------------------------------------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["non_claims"] = ["   "]
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case23:adapter_pilot_non_claims_missing" "$T" \
  "adapter_pilot_non_claims_missing"

# ---------------------------------------------------------------------------
# Case 24: adapter_pilot_overclaim (Amendment 3) — add an extra claim
# entry with claim_id "runtime_truth_proved" plus a structurally-
# permitted extra "description" field whose string value contains the
# forbidden positive phrase "runtime truth proved" (with spaces, which
# is the exact forbidden token form). The claims structural check
# (parse_report) accepts extra fields beyond claim_id/status/
# evidence_refs. The overclaim scanner walks all strings in the report
# outside scope_limitations / non_claims and trips on the forbidden
# substring. The required-claims check (steps 19–20) still passes
# because all seven required claims remain present with status=pass.
# Requires rehashing subject[6].
# ---------------------------------------------------------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-adapter-pilot-report.json"
r = json.loads(open(rp).read())
r["claims"].append({
    "claim_id": "runtime_truth_proved",
    "status": "pass",
    "evidence_refs": ["silver-adapter-pilot-report.json"],
    "description": "runtime truth proved",
})
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 6
expect_verifier_fail "case24:adapter_pilot_overclaim" "$T" \
  "adapter_pilot_overclaim"

echo "[runner] running 6 runner-only refusal cases"

# ---------------------------------------------------------------------------
# Case 25 (runner-only): adapter_validation_failed — adapter declares
# source_is_trust_authority: true. The runner's structural pre-check
# refuses before invoking the v0.2.6 validator subprocess.
# ---------------------------------------------------------------------------
TAMPER_ADAPTER="$WORK/c25-adapter.json"
python3 - "$ADAPTER" "$TAMPER_ADAPTER" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
a = json.loads(open(src).read())
a["trust_boundary"]["source_is_trust_authority"] = True
open(dst, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c25-out"
expect_runner_fail "case25:adapter_validation_failed" \
  "adapter_validation_failed" "$OUT" \
  --adapter "$TAMPER_ADAPTER" \
  --source-export "$SOURCE_EXPORT" \
  --normalization-map "$NORM_MAP" \
  --bindings "$BINDINGS" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 26 (runner-only): source_export_validation_failed — source export
# JSONL contains an unparseable record.
# ---------------------------------------------------------------------------
TAMPER_SOURCE="$WORK/c26-source.jsonl"
cp "$SOURCE_EXPORT" "$TAMPER_SOURCE"
printf "this is not a valid JSON line\n" >> "$TAMPER_SOURCE"
OUT="$WORK/c26-out"
expect_runner_fail "case26:source_export_validation_failed" \
  "source_export_validation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --source-export "$TAMPER_SOURCE" \
  --normalization-map "$NORM_MAP" \
  --bindings "$BINDINGS" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 27 (runner-only): normalization_map_validation_failed — wrong
# normalization-map document_type, refused up-front by the runner.
# ---------------------------------------------------------------------------
TAMPER_NORM="$WORK/c27-norm.json"
python3 - "$NORM_MAP" "$TAMPER_NORM" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
n = json.loads(open(src).read())
n["document_type"] = "proofrail.silver.NOT_a_normalization_map"
open(dst, "w").write(json.dumps(n, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c27-out"
expect_runner_fail "case27:normalization_map_validation_failed" \
  "normalization_map_validation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --source-export "$SOURCE_EXPORT" \
  --normalization-map "$TAMPER_NORM" \
  --bindings "$BINDINGS" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 28 (runner-only): binding_set_validation_failed — binding set
# has a wrong document_type. The runner's structural pre-check refuses
# up-front, before invoking the nested v0.3.2 builder. (Duplicate
# claim_ids are NOT detected at this layer; they fall through to the
# nested builder and surface as nested_trace_binding_generation_failed,
# which is exercised in case29.)
# ---------------------------------------------------------------------------
TAMPER_BINDINGS="$WORK/c28-bindings.json"
python3 - "$BINDINGS" "$TAMPER_BINDINGS" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
b = json.loads(open(src).read())
b["document_type"] = "proofrail.silver.NOT_a_trace_claim_binding_set"
open(dst, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c28-out"
expect_runner_fail "case28:binding_set_validation_failed" \
  "binding_set_validation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --source-export "$SOURCE_EXPORT" \
  --normalization-map "$NORM_MAP" \
  --bindings "$TAMPER_BINDINGS" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 29 (runner-only): nested_trace_binding_generation_failed — change
# the binding set's required_trace_event_id on a non-gap row to an ID
# that does not exist in the normalized trace events. The runner's
# structural binding-set check still accepts the document (it does not
# semantically resolve event IDs), but the nested v0.3.2 builder runs
# with --self-validate and rejects the package. The runner refuses with
# this code; the staging sibling is removed.
# ---------------------------------------------------------------------------
TAMPER_BINDINGS2="$WORK/c29-bindings.json"
python3 - "$BINDINGS" "$TAMPER_BINDINGS2" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
b = json.loads(open(src).read())
b["bindings"][0]["required_trace_event_id"] = "TRACE-EVT-DOES-NOT-EXIST"
open(dst, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c29-out"
expect_runner_fail "case29:nested_trace_binding_generation_failed" \
  "nested_trace_binding_generation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --source-export "$SOURCE_EXPORT" \
  --normalization-map "$NORM_MAP" \
  --bindings "$TAMPER_BINDINGS2" \
  --adapter-pilot-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 30 (runner-only): adapter_pilot_self_validation_failed — all
# upstream inputs are valid, but the runner's self-validation subprocess
# is forced to fail by pointing the runner module's ADAPTER_PILOT_VERIFIER
# constant at a stub. The destination directory MUST NOT be created and
# the staging sibling MUST be cleaned up.
# ---------------------------------------------------------------------------
cat > "$WORK/stub_verifier.py" <<'EOF'
#!/usr/bin/env python3
import sys
sys.stderr.write("FAIL: stub_self_validate_failure: forced\n")
sys.exit(1)
EOF
chmod +x "$WORK/stub_verifier.py"

OUT="$WORK/c30-out"
set +e
out="$(python3 - \
  "$REPO_ROOT/tools/silver" \
  "$WORK/stub_verifier.py" \
  "$ADAPTER" \
  "$SOURCE_EXPORT" \
  "$NORM_MAP" \
  "$BINDINGS" \
  "$REPORT_ID" \
  "$GEN_AT" \
  "$OUT" <<'EOF' 2>&1
import pathlib, sys
(tools_dir, stub, adapter, source_export, norm_map, bindings,
 rid, gen_at, outdir) = sys.argv[1:10]
sys.path.insert(0, tools_dir)
import build_silver_adapter_pilot_v0_1_0 as m
m.ADAPTER_PILOT_VERIFIER = pathlib.Path(stub)
rc = m.main([
    "--adapter", adapter,
    "--source-export", source_export,
    "--normalization-map", norm_map,
    "--bindings", bindings,
    "--adapter-pilot-report-id", rid,
    "--generated-at", gen_at,
    "--output-dir", outdir,
    "--force",
    "--self-validate",
])
sys.exit(rc)
EOF
)"
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
  echo "FAIL: case30:adapter_pilot_self_validation_failed: expected exit 1, got $rc"
  echo "$out"
  exit 1
fi
if ! echo "$out" | grep -qE "^FAIL: adapter_pilot_self_validation_failed:"; then
  echo "FAIL: case30:adapter_pilot_self_validation_failed: missing refusal prefix"
  echo "----- output -----"
  echo "$out"
  echo "------------------"
  exit 1
fi
if echo "$out" | grep -q "Traceback"; then
  echo "FAIL: case30:adapter_pilot_self_validation_failed: unexpected Traceback"
  echo "$out"
  exit 1
fi
if [ -e "$OUT" ]; then
  echo "FAIL: case30:adapter_pilot_self_validation_failed: output dir leaked at $OUT"
  exit 1
fi
if ls "${OUT}.staging."* >/dev/null 2>&1; then
  echo "FAIL: case30:adapter_pilot_self_validation_failed: staging dir leaked"
  exit 1
fi
echo "  case30:adapter_pilot_self_validation_failed: ok ($(echo "$out" | head -n1))"

# ---------------------------------------------------------------------------
# Final step (SS): scoped sha256 snapshot of committed v0.3.3 source paths
# (AFTER) must equal the BEFORE snapshot. The test must never mutate
# the repository.
# ---------------------------------------------------------------------------
echo "[final] scoped source sha256 snapshot diff"
snapshot_scoped "$WORK/scoped.after"
if ! diff -u "$WORK/scoped.before" "$WORK/scoped.after"; then
  echo "FAIL: committed v0.3.3 source paths changed during test"
  exit 1
fi

echo "PASS: tests/test_silver_adapter_pilot_v0_3_3.sh (4 positive + 25 verifier + 6 runner-only + 1 scoped snapshot = 36 numbered exercises; scoped snapshot identical)"
