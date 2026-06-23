#!/usr/bin/env bash
# tests/test_silver_trace_binding_v0_3_2.sh
#
# Regression test for the ProofRail Silver v0.3.2 Trace Binding Profile.
#
# Top-level exercises (30 total):
#
#   Positive-path (4):
#     PP1  Pristine end-to-end build with --self-validate
#     PP2  Pristine third-party verifier pass on the package
#     PP3  Inline structural cross-check of manifest subject layout
#     PP4  Inline structural cross-check of report contents
#
#   Verifier mutation cases (22; one per stable failure reason):
#     case01  invalid_trace_binding_manifest
#     case02  trace_subject_path_traversal
#     case03  trace_subject_file_missing
#     case04  trace_subject_hash_mismatch
#     case05  trace_source_marked_authority           (Amendment 1)
#     case06  trace_adapter_invalid
#     case07  trace_events_invalid
#     case08  trace_event_duplicate
#     case09  trace_event_time_order_invalid
#     case10  trace_binding_set_invalid
#     case11  trace_binding_duplicate
#     case12  trace_binding_event_missing
#     case13  trace_binding_field_mismatch
#     case14  trace_binding_time_window_mismatch
#     case15  trace_report_invalid
#     case16  trace_report_binding_mismatch
#     case17  trace_warning_downgrade                 (Amendment 2)
#     case18  trace_report_status_mismatch
#     case19  trace_report_count_mismatch
#     case20  trace_limitations_missing
#     case21  trace_non_claims_missing
#     case22  trace_overclaim
#
#   Runner-only refusal cases (4):
#     case23  adapter_validation_failed
#     case24  trace_events_validation_failed
#     case25  trace_binding_set_validation_failed
#     case26  trace_binding_self_validation_failed
#
# Coverage summary:
#   * 22/22 stable verifier failure reasons covered. No reason is
#     OR-accepted; each case asserts its exact stable reason.
#   * 4/4 runner-only refusal codes covered.
#   * Scoped sha256 snapshot of 9 committed v0.3.2 source paths runs
#     before and after all cases to prove the test does not mutate
#     the repository.
#
# Notes on reachability:
#   * `trace_source_marked_authority` is DIRECTLY reachable. The
#     verifier runs the adapter trust-authority pre-check BEFORE the
#     v0.2.6 adapter validator subprocess per Amendment 1, so a tampered
#     adapter with `source_is_trust_authority: true` always fires this
#     specific reason instead of being collapsed into the generic
#     `trace_adapter_invalid`.
#   * `trace_warning_downgrade` is DIRECTLY reachable. The verifier runs
#     the downgrade check BEFORE the generic per-row mismatch check per
#     Amendment 2, so downgrading a `bound_with_warning` row's
#     `binding_status` to `bound` always fires this specific reason
#     instead of being collapsed into `trace_report_status_mismatch`.
#   * `trace_subject_path_traversal` is DIRECTLY reachable. The verifier
#     checks each subject's `path` for traversal (`..`) or an absolute
#     prefix BEFORE comparing it to the fixed safe SUBJECT_ORDER.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER="$REPO_ROOT/tools/silver/build_silver_trace_binding_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_trace_binding_v0_1_0.py"
ADAPTER="$REPO_ROOT/examples/silver-evidence-source-adapters/observability-trace-simulated-v0.2.6.json"
TRACE_EVENTS="$REPO_ROOT/fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl"
BINDINGS="$REPO_ROOT/fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json"

WORK="$(mktemp -d -t proofrail-v0.3.2-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

PRISTINE="$WORK/pristine"
GEN_AT="2026-06-22T00:00:00Z"
REPORT_ID="proofrail-trace-binding-report-test-001"

# --- Scoped sha256 snapshot of committed v0.3.2 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-trace-event-v0.1.0.md"
  "schemas/silver-trace-claim-binding-set-v0.1.0.md"
  "schemas/silver-trace-binding-report-v0.1.0.md"
  "schemas/silver-trace-binding-manifest-v0.1.0.md"
  "fixtures/silver-trace-binding-profile-v0.3.2/README.md"
  "fixtures/silver-trace-binding-profile-v0.3.2/trace-events.jsonl"
  "fixtures/silver-trace-binding-profile-v0.3.2/trace-claim-bindings.json"
  "tools/silver/build_silver_trace_binding_v0_1_0.py"
  "tools/silver/verify_silver_trace_binding_v0_1_0.py"
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
# Step 1: pristine build with --self-validate.
# ---------------------------------------------------------------------------
echo "[step1] pristine trace binding build with --self-validate"
python3 "$RUNNER" \
  --adapter "$ADAPTER" \
  --trace-events "$TRACE_EVENTS" \
  --bindings "$BINDINGS" \
  --trace-binding-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2: pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] pristine third-party verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/silver-trace-binding-manifest.json" >/dev/null

# ---------------------------------------------------------------------------
# Step 3: inline structural check of trace binding manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] inline manifest layout check"
python3 - <<EOF
import json
m = json.loads(open("$PRISTINE/silver-trace-binding-manifest.json").read())
assert m["document_type"] == "proofrail.silver.trace_binding_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "v0.3.2"
assert m["hash_algorithm"] == "sha256"
assert len(m["subjects"]) == 4
expected = [
  ("adapter/observability-trace-simulated-v0.2.6.json",
   "trace_source_adapter_descriptor"),
  ("trace-events.jsonl",
   "trace_events"),
  ("trace-claim-bindings.json",
   "trace_claim_binding_set"),
  ("silver-trace-binding-report.json",
   "silver_trace_binding_report"),
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
# Step 4: inline structural check of trace binding report contents.
# ---------------------------------------------------------------------------
echo "[step4] inline report contents check"
python3 - <<EOF
import json
r = json.loads(open("$PRISTINE/silver-trace-binding-report.json").read())
assert r["document_type"] == "proofrail.silver.trace_binding_report"
assert r["proofrail_release"] == "v0.3.2"
assert r["trace_source"]["source_is_trust_authority"] is False
assert r["trace_events"]["event_count"] == 8
assert r["binding_set"]["binding_count"] == 9
s = r["binding_summary"]
assert s["source_is_trust_authority"] is False
assert s["bound_count"] == 5, s
assert s["bound_with_warning_count"] == 1, s
assert s["trace_gap_detected_count"] == 1, s
assert s["out_of_scope_count"] == 2, s
assert len(r["bindings"]) == 9
EOF

# ---------------------------------------------------------------------------
# Helpers for tampered-package cases.
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# Recompute sha256 + size_bytes for a single subject index in the
# trace binding manifest, after a semantic edit. Lets a mutation reach
# the intended later check instead of short-circuiting on
# trace_subject_hash_mismatch.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "silver-trace-binding-manifest.json")
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

# expect_verifier_fail <label> <pkg_dir> <accepted_reason>
expect_verifier_fail() {
  local label="$1" pkg="$2" accepted="$3"
  set +e
  local out rc
  out="$(python3 "$VERIFIER" --manifest "$pkg/silver-trace-binding-manifest.json" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: $label: expected nonzero exit, got 0"
    echo "$out"
    exit 1
  fi
  if ! echo "$out" | grep -qE "^FAIL: ${accepted}:"; then
    echo "FAIL: $label: did not see expected reason ($accepted)"
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

echo "[cases] running 22 verifier mutation cases + 4 runner-only cases"

# ---------------------------------------------------------------------------
# Case 01: invalid_trace_binding_manifest — wrong document_type.
# ---------------------------------------------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-trace-binding-manifest.json"
m = json.loads(open(mp).read())
m["document_type"] = "proofrail.silver.NOT_a_trace_binding_manifest"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case01:invalid_trace_binding_manifest" "$T" \
  "invalid_trace_binding_manifest"

# ---------------------------------------------------------------------------
# Case 02: trace_subject_path_traversal — subject[0].path becomes
# "../etc/passwd". Checked BEFORE exact SUBJECT_ORDER equality.
# ---------------------------------------------------------------------------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-trace-binding-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][0]["path"] = "../etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02:trace_subject_path_traversal" "$T" \
  "trace_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 03: trace_subject_file_missing — delete subject[3] (report).
# ---------------------------------------------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
rm -f "$T/silver-trace-binding-report.json"
expect_verifier_fail "case03:trace_subject_file_missing" "$T" \
  "trace_subject_file_missing"

# ---------------------------------------------------------------------------
# Case 04: trace_subject_hash_mismatch — modify subject[3] without
# rehashing the manifest.
# ---------------------------------------------------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
printf "\n" >> "$T/silver-trace-binding-report.json"
expect_verifier_fail "case04:trace_subject_hash_mismatch" "$T" \
  "trace_subject_hash_mismatch"

# ---------------------------------------------------------------------------
# Case 05: trace_source_marked_authority (Amendment 1) — set the adapter's
# trust_boundary.source_is_trust_authority to true. Verifier's structural
# pre-check runs BEFORE the v0.2.6 adapter validator subprocess, so this
# fires the specific reason instead of being collapsed into
# trace_adapter_invalid. Requires rehashing subject[0].
# ---------------------------------------------------------------------------
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ap = sys.argv[1] + "/adapter/observability-trace-simulated-v0.2.6.json"
a = json.loads(open(ap).read())
a["trust_boundary"]["source_is_trust_authority"] = True
open(ap, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 0
expect_verifier_fail "case05:trace_source_marked_authority" "$T" \
  "trace_source_marked_authority"

# ---------------------------------------------------------------------------
# Case 06: trace_adapter_invalid — break the adapter in a way that does
# NOT touch the trust-authority flag, so it falls through to the
# unchanged v0.2.6 adapter validator subprocess. Wrong document_type
# is a generic v0.2.6 structural failure. Requires rehashing subject[0].
# ---------------------------------------------------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ap = sys.argv[1] + "/adapter/observability-trace-simulated-v0.2.6.json"
a = json.loads(open(ap).read())
a["document_type"] = "proofrail.silver.NOT_an_evidence_source_adapter"
open(ap, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 0
expect_verifier_fail "case06:trace_adapter_invalid" "$T" \
  "trace_adapter_invalid"

# ---------------------------------------------------------------------------
# Case 07: trace_events_invalid — events JSONL contains an unparseable
# record. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
printf "this is not a valid JSON line\n" >> "$T/trace-events.jsonl"
rehash_subject "$T" 1
expect_verifier_fail "case07:trace_events_invalid" "$T" \
  "trace_events_invalid"

# ---------------------------------------------------------------------------
# Case 08: trace_event_duplicate — duplicate event_id across two
# adjacent events. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ep = sys.argv[1] + "/trace-events.jsonl"
lines = [ln for ln in open(ep).read().splitlines() if ln.strip()]
# Rewrite line 1 (event 002) to reuse event_id from line 0 (event 001),
# preserving the (trace_id, span_id) uniqueness so that the duplicate
# event_id is the only structural problem to fire.
ev0 = json.loads(lines[0])
ev1 = json.loads(lines[1])
ev1["event_id"] = ev0["event_id"]
lines[1] = json.dumps(ev1)
open(ep, "w").write("\n".join(lines) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case08:trace_event_duplicate" "$T" \
  "trace_event_duplicate"

# ---------------------------------------------------------------------------
# Case 09: trace_event_time_order_invalid — swap event_time on adjacent
# events so the strict ascending (event_time, event_id) ordering breaks.
# Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
ep = sys.argv[1] + "/trace-events.jsonl"
lines = [ln for ln in open(ep).read().splitlines() if ln.strip()]
ev0 = json.loads(lines[0])
ev1 = json.loads(lines[1])
ev0["event_time"], ev1["event_time"] = ev1["event_time"], ev0["event_time"]
lines[0] = json.dumps(ev0)
lines[1] = json.dumps(ev1)
open(ep, "w").write("\n".join(lines) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case09:trace_event_time_order_invalid" "$T" \
  "trace_event_time_order_invalid"

# ---------------------------------------------------------------------------
# Case 10: trace_binding_set_invalid — wrong binding-set document_type.
# Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
b = json.loads(open(bp).read())
b["document_type"] = "proofrail.silver.NOT_a_trace_claim_binding_set"
open(bp, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case10:trace_binding_set_invalid" "$T" \
  "trace_binding_set_invalid"

# ---------------------------------------------------------------------------
# Case 11: trace_binding_duplicate — duplicate claim_id in binding set.
# Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
b = json.loads(open(bp).read())
b["bindings"][1]["claim_id"] = b["bindings"][0]["claim_id"]
open(bp, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case11:trace_binding_duplicate" "$T" \
  "trace_binding_duplicate"

# ---------------------------------------------------------------------------
# Case 12: trace_binding_event_missing — change a non-gap row's
# required_trace_event_id to a value that does not exist in the fixture.
# Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
b = json.loads(open(bp).read())
# Mutate the first row (a `bound` row, not a gap row).
b["bindings"][0]["required_trace_event_id"] = "TRACE-EVT-DOES-NOT-EXIST"
open(bp, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case12:trace_binding_event_missing" "$T" \
  "trace_binding_event_missing"

# ---------------------------------------------------------------------------
# Case 13: trace_binding_field_mismatch — change a non-gap row's
# required_protected_action_id to something the resolved event does not
# match. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
b = json.loads(open(bp).read())
# Row 0 references event 001 (payment.release); claim a wrong action.
b["bindings"][0]["required_protected_action_id"] = "wrong.action"
open(bp, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case13:trace_binding_field_mismatch" "$T" \
  "trace_binding_field_mismatch"

# ---------------------------------------------------------------------------
# Case 14: trace_binding_time_window_mismatch — shrink the
# trace_time_window so the last event falls outside it. Requires
# rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
b = json.loads(open(bp).read())
# Original window closes_at = 2026-06-22T00:10:00Z; last event time =
# 2026-06-22T00:08:00Z. Shrink closes_at to a time BEFORE the last
# event so the cross-check fires for the row referencing it.
b["trace_time_window"]["closes_at"] = "2026-06-22T00:07:30Z"
open(bp, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case14:trace_binding_time_window_mismatch" "$T" \
  "trace_binding_time_window_mismatch"

# ---------------------------------------------------------------------------
# Case 15: trace_report_invalid — wrong report document_type. Requires
# rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-trace-binding-report.json"
r = json.loads(open(rp).read())
r["document_type"] = "proofrail.silver.NOT_a_trace_binding_report"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case15:trace_report_invalid" "$T" \
  "trace_report_invalid"

# ---------------------------------------------------------------------------
# Case 16: trace_report_binding_mismatch — corrupt
# trace_events.events_sha256 in the report. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-trace-binding-report.json"
r = json.loads(open(rp).read())
r["trace_events"]["events_sha256"] = "sha256:" + "0" * 64
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case16:trace_report_binding_mismatch" "$T" \
  "trace_report_binding_mismatch"

# ---------------------------------------------------------------------------
# Case 17: trace_warning_downgrade (Amendment 2) — locate the row whose
# binding_set expected_binding_status is `bound_with_warning` and change
# the corresponding report row's binding_status to `bound`. Verifier
# runs the downgrade check BEFORE the generic per-row mismatch, so this
# fires the specific reason. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
rp = sys.argv[1] + "/silver-trace-binding-report.json"
b = json.loads(open(bp).read())
warn_row = next(x for x in b["bindings"]
                if x["expected_binding_status"] == "bound_with_warning")
target_claim = warn_row["claim_id"]
r = json.loads(open(rp).read())
for row in r["bindings"]:
    if row["claim_id"] == target_claim:
        row["binding_status"] = "bound"
        # Leave warning text intact so the downgrade fires on
        # binding_status, not on warning-null path.
        break
else:
    raise SystemExit("target claim not found")
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case17:trace_warning_downgrade" "$T" \
  "trace_warning_downgrade"

# ---------------------------------------------------------------------------
# Case 18: trace_report_status_mismatch — take the first `bound` row
# (expected `bound`) and rewrite the report row's `protected_action_id`
# to a value that does not match the resolved event. The downgrade
# check ignores rows whose expected status is `bound`, so this falls
# through to the generic per-row mismatch. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
bp = sys.argv[1] + "/trace-claim-bindings.json"
rp = sys.argv[1] + "/silver-trace-binding-report.json"
b = json.loads(open(bp).read())
bound_row = next(x for x in b["bindings"]
                 if x["expected_binding_status"] == "bound")
target_claim = bound_row["claim_id"]
r = json.loads(open(rp).read())
for row in r["bindings"]:
    if row["claim_id"] == target_claim:
        row["protected_action_id"] = "wrong.action.not.matching.event"
        break
else:
    raise SystemExit("target claim not found")
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case18:trace_report_status_mismatch" "$T" \
  "trace_report_status_mismatch"

# ---------------------------------------------------------------------------
# Case 19: trace_report_count_mismatch — corrupt binding_summary.bound_count
# without touching binding_status values. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-trace-binding-report.json"
r = json.loads(open(rp).read())
r["binding_summary"]["bound_count"] = r["binding_summary"]["bound_count"] + 7
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case19:trace_report_count_mismatch" "$T" \
  "trace_report_count_mismatch"

# ---------------------------------------------------------------------------
# Case 20: trace_limitations_missing — manifest-level scope_limitations
# becomes an empty list. Structural pre-check accepts an empty list of
# strings; the dedicated emptiness check fires later.
# ---------------------------------------------------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-trace-binding-manifest.json"
m = json.loads(open(mp).read())
m["scope_limitations"] = []
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case20:trace_limitations_missing" "$T" \
  "trace_limitations_missing"

# ---------------------------------------------------------------------------
# Case 21: trace_non_claims_missing — report-level non_claims becomes a
# list with a single blank entry. Requires rehashing subject[3] so the
# verifier reaches the dedicated emptiness check.
# ---------------------------------------------------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-trace-binding-report.json"
r = json.loads(open(rp).read())
r["non_claims"] = ["   "]
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case21:trace_non_claims_missing" "$T" \
  "trace_non_claims_missing"

# ---------------------------------------------------------------------------
# Case 22: trace_overclaim — inject a forbidden positive token into the
# report's trace_binding_report_id (which is structurally checked only
# for non-empty string, never cross-checked against the manifest).
# Requires rehashing subject[3]. Fires AFTER the count check.
# ---------------------------------------------------------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-trace-binding-report.json"
r = json.loads(open(rp).read())
r["trace_binding_report_id"] = (
    r["trace_binding_report_id"] + " runtime proof"
)
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case22:trace_overclaim" "$T" \
  "trace_overclaim"

echo "[runner] running 4 runner-only refusal cases"

# ---------------------------------------------------------------------------
# Case 23 (runner-only): adapter_validation_failed — adapter declares
# source_is_trust_authority: true. The runner's structural pre-check
# (Amendment 1) refuses before invoking the v0.2.6 validator subprocess.
# ---------------------------------------------------------------------------
TAMPER_ADAPTER="$WORK/c23-adapter.json"
python3 - "$ADAPTER" "$TAMPER_ADAPTER" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
a = json.loads(open(src).read())
a["trust_boundary"]["source_is_trust_authority"] = True
open(dst, "w").write(json.dumps(a, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c23-out"
expect_runner_fail "case23:adapter_validation_failed" \
  "adapter_validation_failed" "$OUT" \
  --adapter "$TAMPER_ADAPTER" \
  --trace-events "$TRACE_EVENTS" \
  --bindings "$BINDINGS" \
  --trace-binding-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 24 (runner-only): trace_events_validation_failed — events JSONL
# contains an unparseable record.
# ---------------------------------------------------------------------------
TAMPER_EVENTS="$WORK/c24-events.jsonl"
cp "$TRACE_EVENTS" "$TAMPER_EVENTS"
printf "this is not a valid JSON line\n" >> "$TAMPER_EVENTS"
OUT="$WORK/c24-out"
expect_runner_fail "case24:trace_events_validation_failed" \
  "trace_events_validation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --trace-events "$TAMPER_EVENTS" \
  --bindings "$BINDINGS" \
  --trace-binding-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 25 (runner-only): trace_binding_set_validation_failed — binding
# set has a duplicate claim_id, which the runner refuses up-front.
# ---------------------------------------------------------------------------
TAMPER_BINDINGS="$WORK/c25-bindings.json"
python3 - "$BINDINGS" "$TAMPER_BINDINGS" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
b = json.loads(open(src).read())
b["bindings"][1]["claim_id"] = b["bindings"][0]["claim_id"]
open(dst, "w").write(json.dumps(b, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c25-out"
expect_runner_fail "case25:trace_binding_set_validation_failed" \
  "trace_binding_set_validation_failed" "$OUT" \
  --adapter "$ADAPTER" \
  --trace-events "$TRACE_EVENTS" \
  --bindings "$TAMPER_BINDINGS" \
  --trace-binding-report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 26 (runner-only): trace_binding_self_validation_failed — all
# upstream inputs are valid, but the runner's self-validation subprocess
# is forced to fail by pointing the runner module's TRACE_BINDING_VERIFIER
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

OUT="$WORK/c26-out"
set +e
out="$(python3 - \
  "$REPO_ROOT/tools/silver" \
  "$WORK/stub_verifier.py" \
  "$ADAPTER" \
  "$TRACE_EVENTS" \
  "$BINDINGS" \
  "$REPORT_ID" \
  "$GEN_AT" \
  "$OUT" <<'EOF' 2>&1
import pathlib, sys
tools_dir, stub, adapter, events, bindings, rid, gen_at, outdir = sys.argv[1:9]
sys.path.insert(0, tools_dir)
import build_silver_trace_binding_v0_1_0 as m
m.TRACE_BINDING_VERIFIER = pathlib.Path(stub)
rc = m.main([
    "--adapter", adapter,
    "--trace-events", events,
    "--bindings", bindings,
    "--trace-binding-report-id", rid,
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
  echo "FAIL: case26:trace_binding_self_validation_failed: expected exit 1, got $rc"
  echo "$out"
  exit 1
fi
if ! echo "$out" | grep -qE "^FAIL: trace_binding_self_validation_failed:"; then
  echo "FAIL: case26:trace_binding_self_validation_failed: missing refusal prefix"
  echo "----- output -----"
  echo "$out"
  echo "------------------"
  exit 1
fi
if echo "$out" | grep -q "Traceback"; then
  echo "FAIL: case26:trace_binding_self_validation_failed: unexpected Traceback"
  echo "$out"
  exit 1
fi
if [ -e "$OUT" ]; then
  echo "FAIL: case26:trace_binding_self_validation_failed: output dir leaked at $OUT"
  exit 1
fi
if ls "${OUT}.staging."* >/dev/null 2>&1; then
  echo "FAIL: case26:trace_binding_self_validation_failed: staging dir leaked"
  exit 1
fi
echo "  case26:trace_binding_self_validation_failed: ok ($(echo "$out" | head -n1))"

# ---------------------------------------------------------------------------
# Final step: scoped sha256 snapshot of committed v0.3.2 source paths
# (AFTER) must equal the BEFORE snapshot. The test must never mutate
# the repository.
# ---------------------------------------------------------------------------
echo "[final] scoped source sha256 snapshot diff"
snapshot_scoped "$WORK/scoped.after"
if ! diff -u "$WORK/scoped.before" "$WORK/scoped.after"; then
  echo "FAIL: committed v0.3.2 source paths changed during test"
  exit 1
fi

echo "PASS: tests/test_silver_trace_binding_v0_3_2.sh (4 positive + 22 verifier + 4 runner-only = 30 top-level exercises; scoped snapshot identical)"
