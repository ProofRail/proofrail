#!/usr/bin/env bash
# tests/test_silver_handoff_inspector_v0_3_1.sh
#
# Regression test for the ProofRail Silver v0.3.1 Handoff Inspector +
# Gold Gap Inventory.
#
# Top-level exercises (30 total):
#
#   Positive-path (4):
#     PP1  Pristine end-to-end build with --self-validate
#     PP2  Pristine third-party verifier pass on the package
#     PP3  Inline structural cross-check of manifest subject layout
#     PP4  Inline structural cross-check of report counts
#
#   Verifier mutation cases (23; one per stable failure reason, with
#   Amendment-1 multi-path reasons split per subpath):
#     case01   invalid_inspection_manifest
#     case02   inspection_subject_path_traversal
#     case03   inspection_subject_file_missing
#     case04   inspection_subject_hash_mismatch
#     case05   inspection_limitations_missing
#     case06   inspection_non_claims_missing
#     case07   requirement_set_invalid
#     case08   requirement_duplicate
#     case09   requirement_domain_missing
#     case10   inspection_report_invalid
#     case11   inspection_report_binding_mismatch
#     case12a  inspection_handoff_summary_mismatch (acceptance_record_id)
#     case12b  inspection_handoff_summary_mismatch (decision_status)
#     case12c  inspection_handoff_summary_mismatch (purpose_id)
#     case13a  inspection_review_posture_downgrade (rank)
#     case13b  inspection_review_posture_downgrade (reuse_warning)
#     case14   inspection_component_status_mismatch
#     case15   inspection_requirement_missing
#     case16   inspection_requirement_status_mismatch
#     case17   inspection_count_mismatch
#     case18   inspection_gold_status_invalid
#     case19   inspection_gold_overclaim
#     case20   nested_handoff_invalid
#
#   Runner-only refusal cases (3):
#     case21   handoff_validation_failed
#     case22   requirement_set_validation_failed
#     case23   inspection_self_validation_failed
#
# Coverage summary:
#   * 20/20 stable verifier failure reasons covered.
#   * Two multi-path reasons (inspection_handoff_summary_mismatch with
#     three covered fields, inspection_review_posture_downgrade with two
#     subpaths) are split into separate sub-cases so each subpath is
#     independently exercised.
#   * 3/3 runner-only refusal codes covered.
#   * Scoped sha256 snapshot of 11 committed v0.3.1 source paths runs
#     before and after all cases to prove the test does not mutate the
#     repository.
#
# Notes on reachability:
#   * `inspection_subject_path_traversal` is DIRECTLY reachable. The
#     verifier checks each subject's `path` for traversal ("..") or an
#     absolute prefix BEFORE comparing it to the fixed safe
#     SUBJECT_ORDER. The test mutates subject[0].path to "../etc/passwd"
#     and asserts exactly `inspection_subject_path_traversal`.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER="$REPO_ROOT/tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_handoff_inspection_v0_1_0.py"
REQSET="$REPO_ROOT/fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json"

WORK="$(mktemp -d -t proofrail-v0.3.1-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

PRISTINE="$WORK/pristine"
GEN_AT="2026-06-29T00:00:00Z"

# --- Scoped sha256 snapshot of committed v0.3.1 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-handoff-inspection-manifest-v0.1.0.md"
  "schemas/silver-handoff-inspection-report-v0.1.0.md"
  "schemas/silver-to-gold-requirement-set-v0.1.0.md"
  "fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json"
  "fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/README.md"
  "tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py"
  "tools/silver/verify_silver_handoff_inspection_v0_1_0.py"
  "demos/silver-demo-008-handoff-inspector-gap-inventory/README.md"
  "demos/silver-demo-008-handoff-inspector-gap-inventory/demo-walkthrough.md"
  "tests/test_silver_handoff_inspector_v0_3_1.sh"
  "docs/gold/silver-handoff-inspector-and-gap-inventory-v0.3.1.md"
)
snapshot_scoped() {
  local out="$1"
  : > "$out"
  for rel in "${SCOPED_FILES[@]}"; do
    python3 -c "
import hashlib, sys
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
# Step 1: rebuild the v0.2.7 -> v0.2.8 -> v0.2.9 -> v0.3.0 chain.
# ---------------------------------------------------------------------------
echo "[step1] rebuilding v0.2.7 -> v0.2.8 -> v0.2.9 -> v0.3.0 chain"
make -s -C "$REPO_ROOT" run-silver-acceptance-handoff-v0-3-0 >/dev/null

HANDOFF_PKG="/tmp/proofrail-silver-acceptance-handoff-v0.3.0"
HANDOFF_MANIFEST="$HANDOFF_PKG/silver-acceptance-handoff-manifest.json"
[ -f "$HANDOFF_MANIFEST" ] || { echo "FAIL: v0.3.0 handoff manifest not found"; exit 1; }

# ---------------------------------------------------------------------------
# Step 2: pristine build with --self-validate.
# ---------------------------------------------------------------------------
echo "[step2] pristine inspector build with --self-validate"
python3 "$RUNNER" \
  --handoff-manifest "$HANDOFF_MANIFEST" \
  --requirement-set "$REQSET" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 3: pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step3] pristine third-party verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/silver-handoff-inspection-manifest.json" >/dev/null

# ---------------------------------------------------------------------------
# Step 4: inline structural check of inspection manifest layout.
# ---------------------------------------------------------------------------
echo "[step4] inline manifest layout check"
python3 - <<EOF
import json, sys
m = json.loads(open("$PRISTINE/silver-handoff-inspection-manifest.json").read())
assert m["document_type"] == "proofrail.silver.handoff_inspection_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "v0.3.1"
assert m["hash_algorithm"] == "sha256"
assert len(m["subjects"]) == 3
expected = [
  ("silver-acceptance-handoff/silver-acceptance-handoff-manifest.json",
   "silver_acceptance_handoff_manifest"),
  ("gold-boundary-requirements.json",
   "gold_boundary_requirement_set"),
  ("silver-handoff-inspection-report.json",
   "silver_handoff_inspection_report"),
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
# Step 5: inline structural check of inspection report contents.
# ---------------------------------------------------------------------------
echo "[step5] inline report contents check"
python3 - <<EOF
import json
r = json.loads(open("$PRISTINE/silver-handoff-inspection-report.json").read())
assert r["document_type"] == "proofrail.silver.handoff_inspection_report"
assert r["proofrail_release"] == "v0.3.1"
assert r["base_handoff"]["handoff_verification_status"] == "pass"
assert r["base_handoff"]["handoff_manifest_path"] == (
    "silver-acceptance-handoff/silver-acceptance-handoff-manifest.json"
)
assert len(r["component_inspection"]) == 4
for row in r["component_inspection"]:
    assert row["inspection_status"] == "present_and_verified"
inv = r["gold_gap_inventory"]
assert inv["gold_boundary_status"] == "gold_not_claimed"
assert inv["gold_prerequisites_unmet"] is True
assert inv["requirement_count"] == 13
c = inv["counts"]
assert c["silver_evidence_present"] == 1, c
assert c["silver_evidence_partial"] == 4, c
assert c["gold_prerequisite_unmet"] == 6, c
assert c["out_of_scope_for_silver"] == 2, c
EOF

# ---------------------------------------------------------------------------
# Helpers for tampered-package cases.
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# Recompute sha256 + size_bytes for a single subject index in the
# inspection manifest, after a semantic edit. This lets a mutation reach
# the intended later check instead of short-circuiting on
# inspection_subject_hash_mismatch.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "silver-handoff-inspection-manifest.json")
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

# expect_verifier_fail <label> <pkg_dir> <accepted_reasons_regex_alt>
expect_verifier_fail() {
  local label="$1" pkg="$2" accepted="$3"
  set +e
  local out rc
  out="$(python3 "$VERIFIER" --manifest "$pkg/silver-handoff-inspection-manifest.json" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: $label: expected nonzero exit, got 0"
    echo "$out"
    exit 1
  fi
  if ! echo "$out" | grep -qE "^FAIL: ($accepted):"; then
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

# expect_runner_fail <label> <runner-args...> <accepted_refusal_code>
# The last argument is the accepted refusal regex; all prior args are the
# runner argv. Asserts exit code 1, stderr contains FAIL: <code>:, and no
# output dir was created.
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
  if ! echo "$out" | grep -qE "^FAIL: ($expected):"; then
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
  # Also assert no leftover staging sibling.
  local stage_pattern="${outdir}.staging."
  if ls "${stage_pattern}"* >/dev/null 2>&1; then
    echo "FAIL: $label: staging dir leaked: ${stage_pattern}*"
    exit 1
  fi
  echo "  $label: ok ($(echo "$out" | head -n1))"
}

echo "[cases] running 20 verifier mutation cases + 3 runner-only cases"

# ---------------------------------------------------------------------------
# Case 01: invalid_inspection_manifest — wrong document_type.
# ---------------------------------------------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-handoff-inspection-manifest.json"
m = json.loads(open(mp).read())
m["document_type"] = "proofrail.silver.NOT_a_manifest"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case01:invalid_inspection_manifest" "$T" \
  "invalid_inspection_manifest"

# ---------------------------------------------------------------------------
# Case 02: inspection_subject_path_traversal.
# The verifier's validate_manifest_structure checks each subject path for
# absolute prefix or ".." components BEFORE comparing against the fixed
# SUBJECT_ORDER, so this stable failure reason is directly reachable.
# ---------------------------------------------------------------------------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-handoff-inspection-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][0]["path"] = "../etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02:inspection_subject_path_traversal" "$T" \
  "inspection_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 03: inspection_subject_file_missing — delete subject[2] file.
# ---------------------------------------------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
rm -f "$T/silver-handoff-inspection-report.json"
expect_verifier_fail "case03:inspection_subject_file_missing" "$T" \
  "inspection_subject_file_missing"

# ---------------------------------------------------------------------------
# Case 04: inspection_subject_hash_mismatch — modify subject[2] without
# rehashing the manifest.
# ---------------------------------------------------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
# Append a single whitespace newline to the report; manifest sha unchanged.
printf "\n" >> "$T/silver-handoff-inspection-report.json"
expect_verifier_fail "case04:inspection_subject_hash_mismatch" "$T" \
  "inspection_subject_hash_mismatch"

# ---------------------------------------------------------------------------
# Case 05: inspection_limitations_missing — manifest-level scope_limitations
# becomes empty. (Structural check accepts an empty list of strings; the
# emptiness check fires later per Amendment 2.)
# ---------------------------------------------------------------------------
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-handoff-inspection-manifest.json"
m = json.loads(open(mp).read())
m["scope_limitations"] = []
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case05:inspection_limitations_missing" "$T" \
  "inspection_limitations_missing"

# ---------------------------------------------------------------------------
# Case 06: inspection_non_claims_missing — report-level non_claims becomes
# a list with a single blank entry. Requires rehashing subject[2] so the
# verifier reaches step 16 instead of short-circuiting on subject hash.
# ---------------------------------------------------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["non_claims"] = ["   "]
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case06:inspection_non_claims_missing" "$T" \
  "inspection_non_claims_missing"

# ---------------------------------------------------------------------------
# Case 07: requirement_set_invalid — wrong document_type in requirement set.
# Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/gold-boundary-requirements.json"
r = json.loads(open(rp).read())
r["document_type"] = "proofrail.silver_to_gold.NOT_a_requirement_set"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case07:requirement_set_invalid" "$T" \
  "requirement_set_invalid"

# ---------------------------------------------------------------------------
# Case 08: requirement_duplicate — duplicate requirement_id in req set.
# Replaces requirements[1].requirement_id with requirements[0]'s.
# ---------------------------------------------------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/gold-boundary-requirements.json"
r = json.loads(open(rp).read())
r["requirements"][1]["requirement_id"] = r["requirements"][0]["requirement_id"]
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case08:requirement_duplicate" "$T" \
  "requirement_duplicate"

# ---------------------------------------------------------------------------
# Case 09: requirement_domain_missing — rename one required domain to a
# non-required name (creates a missing slot without duplicates).
# ---------------------------------------------------------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/gold-boundary-requirements.json"
r = json.loads(open(rp).read())
# Rename the production_use_authorization domain to a non-required value
# so the required set is missing it; per-row structural checks still pass.
for row in r["requirements"]:
    if row["domain"] == "production_use_authorization":
        row["domain"] = "demo_nonrequired_domain"
        break
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case09:requirement_domain_missing" "$T" \
  "requirement_domain_missing"

# ---------------------------------------------------------------------------
# Case 10: inspection_report_invalid — wrong report document_type.
# ---------------------------------------------------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["document_type"] = "proofrail.silver.NOT_an_inspection_report"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case10:inspection_report_invalid" "$T" \
  "inspection_report_invalid"

# ---------------------------------------------------------------------------
# Case 11: inspection_report_binding_mismatch — corrupt
# base_handoff.handoff_manifest_sha256.
# ---------------------------------------------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["base_handoff"]["handoff_manifest_sha256"] = "sha256:" + "0" * 64
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case11:inspection_report_binding_mismatch" "$T" \
  "inspection_report_binding_mismatch"

# ---------------------------------------------------------------------------
# Case 12a: inspection_handoff_summary_mismatch — corrupt
# handoff_summary.acceptance_record_id (non-posture field per Amendment 1).
# ---------------------------------------------------------------------------
T="$WORK/c12a"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["handoff_summary"]["acceptance_record_id"] = "wrong-acceptance-record-id"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case12a:inspection_handoff_summary_mismatch_acceptance_record_id" "$T" \
  "inspection_handoff_summary_mismatch"

# ---------------------------------------------------------------------------
# Case 12b: inspection_handoff_summary_mismatch — corrupt
# handoff_summary.decision_status (non-posture field per Amendment 1).
# ---------------------------------------------------------------------------
T="$WORK/c12b"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["handoff_summary"]["decision_status"] = "rejected"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case12b:inspection_handoff_summary_mismatch_decision_status" "$T" \
  "inspection_handoff_summary_mismatch"

# ---------------------------------------------------------------------------
# Case 12c: inspection_handoff_summary_mismatch — corrupt
# handoff_summary.purpose_id (non-posture field per Amendment 1).
# ---------------------------------------------------------------------------
T="$WORK/c12c"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["handoff_summary"]["purpose_id"] = "wrong-purpose-id"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case12c:inspection_handoff_summary_mismatch_purpose_id" "$T" \
  "inspection_handoff_summary_mismatch"

# ---------------------------------------------------------------------------
# Case 13a: inspection_review_posture_downgrade — downgrade report posture
# rank below the nested v0.3.0 summary's rank (Amendment 1 subpath A).
# ---------------------------------------------------------------------------
T="$WORK/c13a"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["handoff_summary"]["recommended_handoff_posture"] = (
    "silver_handoff_complete_for_demo_scope"
)
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case13a:inspection_review_posture_downgrade_rank" "$T" \
  "inspection_review_posture_downgrade"

# ---------------------------------------------------------------------------
# Case 13b: inspection_review_posture_downgrade — blank reuse_warning when
# the nested v0.3.0 summary's rank is >= 1 (Amendment 1 subpath B).
# ---------------------------------------------------------------------------
T="$WORK/c13b"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["handoff_summary"]["reuse_warning"] = ""
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case13b:inspection_review_posture_downgrade_reuse_warning" "$T" \
  "inspection_review_posture_downgrade"

# ---------------------------------------------------------------------------
# Case 14: inspection_component_status_mismatch — change first
# component's inspection_status from present_and_verified to not_inspected.
# ---------------------------------------------------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["component_inspection"][0]["inspection_status"] = "not_inspected"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case14:inspection_component_status_mismatch" "$T" \
  "inspection_component_status_mismatch"


# ---------------------------------------------------------------------------
# Case 15: inspection_requirement_missing — delete the GOLD-REQ-003 row
# (the lone silver_evidence_present row) from gold_gap_inventory.requirements
# while keeping count + recomputed counts internally consistent so the
# missing-row check is reached.
# ---------------------------------------------------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
inv = r["gold_gap_inventory"]
inv["requirements"] = [
    row for row in inv["requirements"]
    if row["requirement_id"] != "GOLD-REQ-003-independent-verifier-identity"
]
inv["requirement_count"] = len(inv["requirements"])
inv["counts"]["silver_evidence_present"] = 0
# gold_prerequisites_unmet remains True (4+6+2 > 0).
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case15:inspection_requirement_missing" "$T" \
  "inspection_requirement_missing"

# ---------------------------------------------------------------------------
# Case 16: inspection_requirement_status_mismatch — change GOLD-REQ-003's
# row gap_status to silver_evidence_partial; counts adjusted to match the
# row distribution so the per-row mismatch check is reached.
# ---------------------------------------------------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
inv = r["gold_gap_inventory"]
for row in inv["requirements"]:
    if row["requirement_id"] == "GOLD-REQ-003-independent-verifier-identity":
        row["gap_status"] = "silver_evidence_partial"
        break
inv["counts"]["silver_evidence_present"] = 0
inv["counts"]["silver_evidence_partial"] = 5
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case16:inspection_requirement_status_mismatch" "$T" \
  "inspection_requirement_status_mismatch"

# ---------------------------------------------------------------------------
# Case 17: inspection_count_mismatch — corrupt recorded counts only.
# ---------------------------------------------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["gold_gap_inventory"]["counts"]["silver_evidence_present"] = 99
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case17:inspection_count_mismatch" "$T" \
  "inspection_count_mismatch"

# ---------------------------------------------------------------------------
# Case 18: inspection_gold_status_invalid — set gold_boundary_status to
# the closed-set alternative "gold_gap_inventory_only" while
# gold_prerequisites_unmet remains True.
# ---------------------------------------------------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["gold_gap_inventory"]["gold_boundary_status"] = "gold_gap_inventory_only"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case18:inspection_gold_status_invalid" "$T" \
  "inspection_gold_status_invalid"

# ---------------------------------------------------------------------------
# Case 19: inspection_gold_overclaim — inject a forbidden positive token
# into base_handoff.handoff_id (outside scope_limitations / non_claims).
# ---------------------------------------------------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
rp = sys.argv[1] + "/silver-handoff-inspection-report.json"
r = json.loads(open(rp).read())
r["base_handoff"]["handoff_id"] = "certified-handoff-demo-001"
open(rp, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case19:inspection_gold_overclaim" "$T" \
  "inspection_gold_overclaim"

# ---------------------------------------------------------------------------
# Case 20: nested_handoff_invalid — corrupt the nested v0.3.0 handoff
# summary so the unchanged v0.3.0 verifier subprocess fails. The v0.3.1
# inspection manifest's subject[0] (nested handoff manifest) is NOT
# touched, so its sha256 still matches and step 7 is reached.
# ---------------------------------------------------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-acceptance-handoff/silver-acceptance-handoff-summary.json"
s = json.loads(open(sp).read())
# Remove a required nested field; v0.3.0 verifier will reject and the
# v0.3.1 verifier surfaces this as nested_handoff_invalid.
s.pop("handoff_id", None)
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case20:nested_handoff_invalid" "$T" \
  "nested_handoff_invalid"


# ---------------------------------------------------------------------------
# Case 21 (runner-only): handoff_validation_failed.
# Build a tampered v0.3.0 handoff package the v0.3.0 verifier will reject,
# then ensure the inspector refuses with the runner-only refusal code and
# does NOT create the output directory.
# ---------------------------------------------------------------------------
TAMPER_HANDOFF="$WORK/c21-handoff"
cp -r "$HANDOFF_PKG" "$TAMPER_HANDOFF"
# Corrupt the nested v0.3.0 summary so the v0.3.0 verifier rejects it.
python3 - "$TAMPER_HANDOFF" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-acceptance-handoff-summary.json"
s = json.loads(open(sp).read())
s.pop("handoff_id", None)
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c21-out"
expect_runner_fail "case21:handoff_validation_failed" \
  "handoff_validation_failed" "$OUT" \
  --handoff-manifest "$TAMPER_HANDOFF/silver-acceptance-handoff-manifest.json" \
  --requirement-set "$REQSET" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 22 (runner-only): requirement_set_validation_failed.
# ---------------------------------------------------------------------------
TAMPER_REQSET="$WORK/c22-reqset.json"
python3 - "$REQSET" "$TAMPER_REQSET" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
r = json.loads(open(src).read())
# Drop the production_use_authorization domain entirely (and keep a
# coherent structure otherwise) so the runner's --validate-requirement-set
# call fails with requirement_domain_missing.
r["requirements"] = [
    row for row in r["requirements"]
    if row["domain"] != "production_use_authorization"
]
open(dst, "w").write(json.dumps(r, indent=2, sort_keys=True) + "\n")
EOF
OUT="$WORK/c22-out"
expect_runner_fail "case22:requirement_set_validation_failed" \
  "requirement_set_validation_failed" "$OUT" \
  --handoff-manifest "$HANDOFF_MANIFEST" \
  --requirement-set "$TAMPER_REQSET" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT" \
  --force

# ---------------------------------------------------------------------------
# Case 23 (runner-only): inspection_self_validation_failed.
# All inspector inputs are valid (so handoff + requirement set subprocess
# calls pass), but the self-validation subprocess is forced to fail by
# pointing the runner module's INSPECTION_VERIFIER constant at a stub.
# This isolates the runner-only refusal code path; the v0.3.1 verifier
# itself never emits this code. The destination directory MUST NOT be
# created and the staging sibling MUST be cleaned up.
# ---------------------------------------------------------------------------
cat > "$WORK/stub_verifier.py" <<'EOF'
#!/usr/bin/env python3
# Pass through requirement-set validation (so the runner reaches the
# self-validate step) by delegating to the real verifier, then fail on
# the --manifest self-validate call so the runner refuses with
# inspection_self_validation_failed.
import os, subprocess, sys
REAL = os.environ["REAL_VERIFIER_FOR_STUB"]
if "--validate-requirement-set" in sys.argv[1:]:
    rc = subprocess.run([sys.executable, REAL] + sys.argv[1:]).returncode
    sys.exit(rc)
sys.stderr.write("FAIL: stub_self_validate_failure: forced\n")
sys.exit(1)
EOF
chmod +x "$WORK/stub_verifier.py"
export REAL_VERIFIER_FOR_STUB="$VERIFIER"

OUT="$WORK/c23-out"
set +e
out="$(python3 - \
  "$REPO_ROOT/tools/silver" \
  "$WORK/stub_verifier.py" \
  "$HANDOFF_MANIFEST" \
  "$REQSET" \
  "$GEN_AT" \
  "$OUT" <<'EOF' 2>&1
import pathlib, sys
tools_dir, stub, handoff, reqset, gen_at, outdir = sys.argv[1:7]
sys.path.insert(0, tools_dir)
import inspect_silver_acceptance_handoff_v0_1_0 as m
m.INSPECTION_VERIFIER = pathlib.Path(stub)
rc = m.main([
    "--handoff-manifest", handoff,
    "--requirement-set", reqset,
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
  echo "FAIL: case23:inspection_self_validation_failed: expected exit 1, got $rc"
  echo "$out"
  exit 1
fi
if ! echo "$out" | grep -qE "^FAIL: inspection_self_validation_failed:"; then
  echo "FAIL: case23:inspection_self_validation_failed: missing refusal prefix"
  echo "----- output -----"
  echo "$out"
  echo "------------------"
  exit 1
fi
if echo "$out" | grep -q "Traceback"; then
  echo "FAIL: case23:inspection_self_validation_failed: unexpected Traceback"
  echo "$out"
  exit 1
fi
if [ -e "$OUT" ]; then
  echo "FAIL: case23:inspection_self_validation_failed: output dir leaked at $OUT"
  exit 1
fi
if ls "${OUT}.staging."* >/dev/null 2>&1; then
  echo "FAIL: case23:inspection_self_validation_failed: staging dir leaked"
  exit 1
fi
echo "  case23:inspection_self_validation_failed: ok ($(echo "$out" | head -n1))"

# ---------------------------------------------------------------------------
# Final step: scoped sha256 snapshot of committed v0.3.1 source paths
# (AFTER) must equal the BEFORE snapshot. The test must never mutate
# the repository.
# ---------------------------------------------------------------------------
echo "[final] scoped source sha256 snapshot diff"
snapshot_scoped "$WORK/scoped.after"
if ! diff -u "$WORK/scoped.before" "$WORK/scoped.after"; then
  echo "FAIL: committed v0.3.1 source paths changed during test"
  exit 1
fi

echo "PASS: tests/test_silver_handoff_inspector_v0_3_1.sh (4 positive + 23 verifier + 3 runner-only = 30 top-level exercises; scoped snapshot identical)"
