#!/usr/bin/env bash
# tests/test_gold_governed_reliance_v0_4_0.sh
#
# Regression test for the ProofRail v0.4.0 Minimal Gold Governed
# Reliance Demo package.
#
# Numbered exercises (53 total):
#
#   Positive-path (4):
#     PP1   Pristine end-to-end build with --self-validate
#     PP2   Pristine independent verifier pass on the package
#     PP3   Inline structural cross-check of manifest subject layout
#     PP4   Inline structural cross-check of bundled conformance report
#
#   Scenario checks (5; one per single-scenario fixture):
#     SC1   scenario-clean-acceptance.json   builds and verifies
#     SC2   scenario-policy-rejection.json   builds and verifies
#     SC3   scenario-challenge-filed.json    builds and verifies
#     SC4   scenario-withdrawal.json         builds and verifies
#     SC5   scenario-supersession.json       builds and verifies
#
#   Canonical verifier mutation cases (24; one per approved reason):
#     case01  gold_manifest_invalid                  (manifest document_type)
#     case02  gold_package_not_object                (package body is JSON array)
#     case03  gold_package_schema_invalid            (package document_type)
#     case04  gold_profile_unsupported
#     case05  gold_package_identity_invalid          (package_id removed)
#     case06  silver_verification_input_invalid      (input_type not_a_type)
#     case07  silver_handoff_input_invalid           (expected_handoff_posture removed)
#     case08  policy_pack_input_invalid              (policy_pack_version removed)
#     case09  registry_lite_input_invalid            (registry_id grammar BadID)
#     case10  control_crosswalk_input_invalid        (control_pack_id removed)
#     case11  governed_decision_set_invalid          (governed_decisions = [])
#     case12  governed_decision_entry_invalid        (decision_id removed)
#     case13  decision_subject_binding_invalid       (subject_ref unknown)
#     case14  decision_policy_binding_invalid        (policy_pack_id mismatch)
#     case15  decision_registry_binding_invalid      (decision_authority_role bad)
#     case16  decision_action_scope_invalid          (protected_action_id bad)
#     case17  decision_status_invalid                (decision_status = maybe)
#     case18  acceptance_path_invalid                (acceptance_record_ref empty)
#     case19  rejection_path_invalid                 (silver_verification_passing = false)
#     case20  challenge_path_invalid                 (challenge_state bad)
#     case21  withdrawal_path_invalid                (withdrawal_trigger = random)
#     case22  supersession_path_invalid              (prior_decision_id nonexistent)
#     case23  non_claims_missing                     (non_claims = [])
#     case24  prohibited_gold_claim_present          (display_name carries "full Gold certified")
#
#   Duplicate manifest-invalid cases (11; secondary manifest defects that
#   all route to gold_manifest_invalid; reported separately so the 24
#   canonical cases above remain exactly one-per-reason):
#     dup01   subject[0] path absolute
#     dup02   subject[0] path traversal
#     dup03   subject[1] path absolute
#     dup04   subject[1] path traversal
#     dup05   subject[0] file missing on disk
#     dup06   subject[0] size_bytes mismatch
#     dup07   subject[0] sha256 mismatch
#     dup08   wrong subject count (3 instead of 2)
#     dup09   subject[0] role wrong
#     dup10   manifest package_id cross-anchor mismatch
#     dup11   conformance report disagreement on otherwise-valid package
#             (non-masking post-structural check)
#
#   Runner-only refusal cases (6; preflight only; covers 5 distinct
#   runner-only reasons, with runner_input_path_forbidden exercised
#   twice — once absolute, once traversal):
#     ro1     runner_input_path_missing
#     ro2     runner_input_path_forbidden       (absolute path)
#     ro2b    runner_input_path_forbidden       (parent-traversal path)
#     ro3     runner_input_file_missing
#     ro4     runner_input_read_failed          (directory, portable)
#     ro5     runner_input_json_invalid
#
#   Runner-relay-of-verifier (1):
#     rel01   --self-validate on a structurally bad package relays the
#             verifier's OWN reason UNCHANGED, NOT wrapped in a sixth
#             runner-only code; staging directory is removed.
#
#   Taxonomy gate (1):
#     TG1     Scan v0.4.0-owned files and v0.4.0-anchored sections of
#             cross-version docs for reason-like tokens; assert every
#             such token belongs to the approved 24-reason verifier set
#             or the approved 5-reason runner-only set.
#
#   Scoped sha256 snapshot (1):
#     SS      scoped sha256 snapshot of committed v0.4.0 source paths
#             BEFORE and AFTER must be identical (test does not mutate
#             v0.4.0-owned source files).
#
# Coverage summary:
#   * 24/24 stable verifier failure reasons covered by canonical cases.
#   * 5 single-scenario fixtures independently built and verified.
#   * 11 additional manifest-invalid defects route to gold_manifest_invalid.
#   * 5/5 runner-only refusal codes covered; runner_input_path_forbidden
#     exercised TWICE (ro2 absolute, ro2b traversal).
#   * rel01 asserts the runner does not wrap a verifier reason in a
#     sixth runner-only code (per the 5-reason runner closed set).
#   * Atomic --force semantics asserted for runner refusals: NO final
#     --output-dir and NO staging sibling on disk.
#   * TG1 enforces strict no-additions discipline against the approved
#     24 verifier reasons and 5 runner-only reasons.
#
# Hash-first re-anchoring:
#   Every mutation that lives INSIDE a subject body is followed by a
#   rehash_subject call to re-anchor the manifest's subject sha256 and
#   size_bytes. This guarantees the mutated case reaches its intended
#   structural check instead of short-circuiting on R01 manifest
#   integrity.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/gold/build_gold_governed_reliance_demo_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py"
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"

WORK="$(mktemp -d -t proofrail-v0.4.0-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-09-15T00:30:00Z"
MANIFEST_ID="proofrail-gold-governed-reliance-manifest-test-001"
REPORT_ID="proofrail-gold-governed-reliance-conformance-report-test-001"

PACKAGE_REL="governed-reliance-scenarios.json"
REPORT_REL_FILE="silver-gold-governed-reliance-conformance-report.json"
MANIFEST_REL_FILE="gold-governed-reliance-package-manifest.json"

# --- Scoped sha256 snapshot of committed v0.4.0 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/gold-governed-reliance-package-v0.1.0.md"
  "schemas/gold-governed-reliance-package-manifest-v0.1.0.md"
  "schemas/gold-governed-reliance-conformance-report-v0.1.0.md"
  "fixtures/gold-governed-reliance-v0.4.0/README.md"
  "fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
  "fixtures/gold-governed-reliance-v0.4.0/scenario-clean-acceptance.json"
  "fixtures/gold-governed-reliance-v0.4.0/scenario-policy-rejection.json"
  "fixtures/gold-governed-reliance-v0.4.0/scenario-challenge-filed.json"
  "fixtures/gold-governed-reliance-v0.4.0/scenario-withdrawal.json"
  "fixtures/gold-governed-reliance-v0.4.0/scenario-supersession.json"
  "tools/gold/build_gold_governed_reliance_demo_v0_1_0.py"
  "tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py"
  "tools/gold/README.md"
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

PRISTINE="$WORK/pristine"

# ---------------------------------------------------------------------------
# Step 1 (PP1): pristine build with --self-validate.
# ---------------------------------------------------------------------------
echo "[step1] pristine gold governed reliance build with --self-validate"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --report-id   "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] pristine independent verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] inline manifest layout check"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" <<'EOF'
import json, sys
mp = sys.argv[1]
m = json.loads(open(mp).read())
assert m["document_type"] == "proofrail.gold.governed_reliance_package_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "gold.governed_reliance.v0.4.0"
assert m["hash_algorithm"] == "sha256"
assert isinstance(m["manifest_id"], str) and m["manifest_id"]
assert isinstance(m["report_id"], str) and m["report_id"]
assert isinstance(m["package_id"], str) and m["package_id"]
assert isinstance(m["governed_reliance_demo_id"], str) and m["governed_reliance_demo_id"]
assert len(m["subjects"]) == 2
expected = [
  ("governed-reliance-scenarios.json", "governed_reliance_package"),
  ("silver-gold-governed-reliance-conformance-report.json", "conformance_report"),
]
for i, (p, r) in enumerate(expected):
    assert m["subjects"][i]["path"] == p, (i, m["subjects"][i]["path"])
    assert m["subjects"][i]["role"] == r, (i, m["subjects"][i]["role"])
    assert m["subjects"][i]["sha256"].startswith("sha256:")
    assert len(m["subjects"][i]["sha256"]) == 7 + 64
    assert isinstance(m["subjects"][i]["size_bytes"], int)
    assert m["subjects"][i]["size_bytes"] >= 0
EOF

# ---------------------------------------------------------------------------
# Step 4 (PP4): inline structural check of bundled conformance report.
# ---------------------------------------------------------------------------
echo "[step4] inline conformance report check"
python3 - "$PRISTINE/$REPORT_REL_FILE" <<'EOF'
import json, sys
rp = sys.argv[1]
r = json.loads(open(rp).read())
assert r["document_type"] == "proofrail.gold.governed_reliance_conformance_report", r["document_type"]
assert r["schema_version"] == "v0.1.0"
assert isinstance(r["package_id"], str) and r["package_id"]
assert isinstance(r["governed_reliance_demo_id"], str) and r["governed_reliance_demo_id"]
assert isinstance(r["report_id"], str) and r["report_id"]
assert isinstance(r["entries"], list)
assert len(r["entries"]) == 24, len(r["entries"])
EXPECTED = [
  "gold_manifest_invalid",
  "gold_package_not_object",
  "gold_package_schema_invalid",
  "gold_profile_unsupported",
  "gold_package_identity_invalid",
  "silver_verification_input_invalid",
  "silver_handoff_input_invalid",
  "policy_pack_input_invalid",
  "registry_lite_input_invalid",
  "control_crosswalk_input_invalid",
  "governed_decision_set_invalid",
  "governed_decision_entry_invalid",
  "decision_subject_binding_invalid",
  "decision_policy_binding_invalid",
  "decision_registry_binding_invalid",
  "decision_action_scope_invalid",
  "decision_status_invalid",
  "acceptance_path_invalid",
  "rejection_path_invalid",
  "challenge_path_invalid",
  "withdrawal_path_invalid",
  "supersession_path_invalid",
  "non_claims_missing",
  "prohibited_gold_claim_present",
]
for i, reason in enumerate(EXPECTED):
    entry = r["entries"][i]
    assert entry["check_id"] == f"check_{i+1:02d}", (i, entry["check_id"])
    assert entry["check_name"] == reason, (i, entry["check_name"], reason)
    assert entry["status"] == "pass", (i, entry["status"])
EOF

# ---------------------------------------------------------------------------
# Scenario checks (SC1..SC5): each single-scenario fixture builds and
# verifies independently.
# ---------------------------------------------------------------------------
sc_build_and_verify() {
  local label="$1"
  local fixture_rel="$2"
  local outdir="$3"
  echo "[$label] single-scenario build+verify ($fixture_rel)"
  python3 "$RUNNER" \
    --input-package "$fixture_rel" \
    --manifest-id "$MANIFEST_ID-$label" \
    --report-id   "$REPORT_ID-$label" \
    --generated-at "$GEN_AT" \
    --output-dir "$outdir" \
    --force \
    --self-validate >/dev/null
  python3 "$VERIFIER" --manifest "$outdir/$MANIFEST_REL_FILE" >/dev/null
  echo "  $label: ok"
}

sc_build_and_verify "SC1" "fixtures/gold-governed-reliance-v0.4.0/scenario-clean-acceptance.json" "$WORK/sc1"
sc_build_and_verify "SC2" "fixtures/gold-governed-reliance-v0.4.0/scenario-policy-rejection.json" "$WORK/sc2"
sc_build_and_verify "SC3" "fixtures/gold-governed-reliance-v0.4.0/scenario-challenge-filed.json" "$WORK/sc3"
sc_build_and_verify "SC4" "fixtures/gold-governed-reliance-v0.4.0/scenario-withdrawal.json" "$WORK/sc4"
sc_build_and_verify "SC5" "fixtures/gold-governed-reliance-v0.4.0/scenario-supersession.json" "$WORK/sc5"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# Rehash subject [idx] (0 or 1) in the outer manifest after a body
# mutation. This is the hash-first re-anchoring required so a downstream
# structural defect can reach its intended check_NN reason instead of
# short-circuiting on R01 manifest integrity.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "gold-governed-reliance-package-manifest.json")
m = json.loads(open(mp).read())
sp = os.path.join(pkg, m["subjects"][idx]["path"])
h = hashlib.sha256()
with open(sp, "rb") as f:
    for c in iter(lambda: f.read(65536), b""):
        h.update(c)
m["subjects"][idx]["sha256"] = "sha256:" + h.hexdigest()
m["subjects"][idx]["size_bytes"] = os.path.getsize(sp)
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the gold package body via a Python snippet. Caller supplies a
# Python program operating on the dict `pkg`.
edit_package() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
pp = os.path.join(pkg, "governed-reliance-scenarios.json")
body = json.loads(open(pp).read())
exec(expr, {"pkg": body, "json": json})
# Preserve the input fixture's text format: 2-space indent + trailing
# newline.
open(pp, "w").write(json.dumps(body, indent=2) + "\n")
EOF
}

# Edit the outer manifest via a Python snippet operating on dict `m`.
# Does NOT recompute subject hashes by itself.
edit_manifest() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
mp = os.path.join(pkg, "gold-governed-reliance-package-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the bundled conformance report via a Python snippet operating
# on dict `r`. Re-emits in the verifier's canonical
# (sort_keys, separators=(",",":")) byte image so subject [1] can be
# re-anchored cleanly via rehash_subject.
edit_report() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
rp = os.path.join(pkg, "silver-gold-governed-reliance-conformance-report.json")
r = json.loads(open(rp).read())
exec(expr, {"r": r, "json": json})
open(rp, "w").write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

expect_verifier_fail() {
  local label="$1" pkg="$2" expected="$3"
  set +e
  local out rc
  out="$(python3 "$VERIFIER" --manifest "$pkg/$MANIFEST_REL_FILE" 2>&1)"
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

expect_runner_fail() {
  local label="$1" expected="$2" outdir="$3"
  shift 3
  set +e
  local out rc
  out="$(python3 "$@" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -ne 1 ]; then
    echo "FAIL: $label: expected runner exit 1, got $rc"
    echo "$out"
    exit 1
  fi
  if ! echo "$out" | grep -qE "^FAIL: ${expected}:"; then
    echo "FAIL: $label: did not see expected refusal ($expected)"
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

echo "[cases] 24 canonical + 11 duplicate + 6 runner-only + 1 runner-relay + taxonomy gate"

# ===========================================================================
# Canonical verifier mutation cases (24, one per approved reason)
# ===========================================================================

# --- case01: gold_manifest_invalid ------------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:gold_manifest_invalid" "$T" "gold_manifest_invalid"

# --- case02: gold_package_not_object (package body is JSON array) -----------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$PACKAGE_REL', 'w') as f:
    f.write(json.dumps([1,2,3], indent=2) + '\n')
"
# The cross-anchor check requires manifest.package_id == package.package_id;
# the body is now a JSON array so package_id is unreadable. The verifier's
# R02 (not_object) fires before any cross-anchor check on the body.
rehash_subject "$T" 0
expect_verifier_fail "case02:gold_package_not_object" "$T" "gold_package_not_object"

# --- case03: gold_package_schema_invalid ------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["document_type"] = "wrong"'
rehash_subject "$T" 0
expect_verifier_fail "case03:gold_package_schema_invalid" "$T" "gold_package_schema_invalid"

# --- case04: gold_profile_unsupported ---------------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["profile"] = "some.other.profile"'
rehash_subject "$T" 0
expect_verifier_fail "case04:gold_profile_unsupported" "$T" "gold_profile_unsupported"

# --- case05: gold_package_identity_invalid ----------------------------------
# The verifier folds MISSING required top-level fields into R03 and
# reserves R05 for grammar violations on present identifiers. Setting
# package_id to a grammar-invalid value on both body and manifest (so
# the body⇄manifest cross-anchor still equates) reaches R05 cleanly.
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["package_id"] = "BadID"'
edit_manifest "$T" 'm["package_id"] = "BadID"'
rehash_subject "$T" 0
expect_verifier_fail "case05:gold_package_identity_invalid" "$T" "gold_package_identity_invalid"

# --- case06: silver_verification_input_invalid ------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["silver_verification"]["input_type"] = "not_a_type"'
rehash_subject "$T" 0
expect_verifier_fail "case06:silver_verification_input_invalid" "$T" "silver_verification_input_invalid"

# --- case07: silver_handoff_input_invalid -----------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["silver_handoff"].pop("expected_handoff_posture")'
rehash_subject "$T" 0
expect_verifier_fail "case07:silver_handoff_input_invalid" "$T" "silver_handoff_input_invalid"

# --- case08: policy_pack_input_invalid --------------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["policy_pack"].pop("policy_pack_version")'
rehash_subject "$T" 0
expect_verifier_fail "case08:policy_pack_input_invalid" "$T" "policy_pack_input_invalid"

# --- case09: registry_lite_input_invalid ------------------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["registry_lite"]["registry_id"] = "BadID"'
rehash_subject "$T" 0
expect_verifier_fail "case09:registry_lite_input_invalid" "$T" "registry_lite_input_invalid"

# --- case10: control_crosswalk_input_invalid --------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["control_crosswalk"].pop("control_pack_id")'
rehash_subject "$T" 0
expect_verifier_fail "case10:control_crosswalk_input_invalid" "$T" "control_crosswalk_input_invalid"

# --- case11: governed_decision_set_invalid ----------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case11:governed_decision_set_invalid" "$T" "governed_decision_set_invalid"

# --- case12: governed_decision_entry_invalid --------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0].pop("decision_id")'
rehash_subject "$T" 0
expect_verifier_fail "case12:governed_decision_entry_invalid" "$T" "governed_decision_entry_invalid"

# --- case13: decision_subject_binding_invalid -------------------------------
# Amendment 7: mutation must remain structurally valid. The subject_ref
# value below is grammar-valid but does not bind to any input.
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["decision_subject"]["subject_ref"] = "unknown-subject-ref-001"'
rehash_subject "$T" 0
expect_verifier_fail "case13:decision_subject_binding_invalid" "$T" "decision_subject_binding_invalid"

# --- case14: decision_policy_binding_invalid --------------------------------
# Amendment 7: structurally valid id; does not match inputs.policy_pack.policy_pack_id.
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["policy_binding"]["policy_pack_id"] = "policy-pack-mismatch-001"'
rehash_subject "$T" 0
expect_verifier_fail "case14:decision_policy_binding_invalid" "$T" "decision_policy_binding_invalid"

# --- case15: decision_registry_binding_invalid ------------------------------
# decision_authority_role outside the closed Registry Lite role set.
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["registry_binding"]["decision_authority_role"] = "not_a_role"'
rehash_subject "$T" 0
expect_verifier_fail "case15:decision_registry_binding_invalid" "$T" "decision_registry_binding_invalid"

# --- case16: decision_action_scope_invalid ----------------------------------
# protected_action_id outside the v0.3.6 control-crosswalk vocabulary.
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["action_scope"]["protected_action_id"] = "not_a_protected_action"'
rehash_subject "$T" 0
expect_verifier_fail "case16:decision_action_scope_invalid" "$T" "decision_action_scope_invalid"

# --- case17: decision_status_invalid ----------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["decision_status"] = "maybe"'
rehash_subject "$T" 0
expect_verifier_fail "case17:decision_status_invalid" "$T" "decision_status_invalid"

# --- case18: acceptance_path_invalid ----------------------------------------
# governed_decisions[0] is the clean_acceptance scenario. Empty
# acceptance_record_ref violates the scenario_specific_state requirement.
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["scenario_specific_state"]["acceptance_record_ref"] = ""'
rehash_subject "$T" 0
expect_verifier_fail "case18:acceptance_path_invalid" "$T" "acceptance_path_invalid"

# --- case19: rejection_path_invalid -----------------------------------------
# governed_decisions[1] is the policy_rejection scenario. Setting
# silver_verification_passing to false breaks the "rejection despite Silver
# passing" invariant required by the rejection_path check.
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][1]["scenario_specific_state"]["silver_verification_passing"] = False'
rehash_subject "$T" 0
expect_verifier_fail "case19:rejection_path_invalid" "$T" "rejection_path_invalid"

# --- case20: challenge_path_invalid -----------------------------------------
# governed_decisions[2] is the challenge_filed scenario. challenge_state
# outside its closed enum trips the challenge_path check.
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][2]["scenario_specific_state"]["challenge_state"] = "not_a_state"'
rehash_subject "$T" 0
expect_verifier_fail "case20:challenge_path_invalid" "$T" "challenge_path_invalid"

# --- case21: withdrawal_path_invalid ----------------------------------------
# governed_decisions[3] is the withdrawal scenario. withdrawal_trigger
# outside its closed enum trips the withdrawal_path check.
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][3]["scenario_specific_state"]["withdrawal_trigger"] = "random"'
rehash_subject "$T" 0
expect_verifier_fail "case21:withdrawal_path_invalid" "$T" "withdrawal_path_invalid"

# --- case22: supersession_path_invalid --------------------------------------
# governed_decisions[4] is the supersession scenario; the canonical fixture
# uses prior_decision_ref_kind=internal_decision_id, so prior_decision_id
# must resolve to another entry's decision_id. "nonexistent" does not.
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][4]["scenario_specific_state"]["prior_decision_id"] = "nonexistent"'
rehash_subject "$T" 0
expect_verifier_fail "case22:supersession_path_invalid" "$T" "supersession_path_invalid"

# --- case23: non_claims_missing ---------------------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["non_claims"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case23:non_claims_missing" "$T" "non_claims_missing"

# --- case24: prohibited_gold_claim_present ----------------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["relying_party"]["display_name"] = "Demo Local Relying Party (full Gold certified)"'
rehash_subject "$T" 0
expect_verifier_fail "case24:prohibited_gold_claim_present" "$T" "prohibited_gold_claim_present"

# ===========================================================================
# Duplicate gold_manifest_invalid cases (11; all route to that reason).
# ===========================================================================

# --- dup01: subject[0] path absolute ----------------------------------------
T="$WORK/d01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "dup01:subject_0_path_absolute" "$T" "gold_manifest_invalid"

# --- dup02: subject[0] path traversal ---------------------------------------
T="$WORK/d02"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "../escape.json"'
expect_verifier_fail "dup02:subject_0_path_traversal" "$T" "gold_manifest_invalid"

# --- dup03: subject[1] path absolute ----------------------------------------
T="$WORK/d03"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "/etc/hostname"'
expect_verifier_fail "dup03:subject_1_path_absolute" "$T" "gold_manifest_invalid"

# --- dup04: subject[1] path traversal ---------------------------------------
T="$WORK/d04"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "../escape-report.json"'
expect_verifier_fail "dup04:subject_1_path_traversal" "$T" "gold_manifest_invalid"

# --- dup05: subject[0] file missing on disk ---------------------------------
T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
rm "$T/$PACKAGE_REL"
expect_verifier_fail "dup05:subject_0_file_absent" "$T" "gold_manifest_invalid"

# --- dup06: subject[0] size_bytes mismatch ----------------------------------
T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["size_bytes"] = 0'
expect_verifier_fail "dup06:subject_0_size_mismatch" "$T" "gold_manifest_invalid"

# --- dup07: subject[0] sha256 mismatch --------------------------------------
T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["sha256"] = "sha256:" + "f" * 64'
expect_verifier_fail "dup07:subject_0_sha_mismatch" "$T" "gold_manifest_invalid"

# --- dup08: wrong subject count (3 entries) ---------------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"sha256:" + "0"*64, "size_bytes":0})'
expect_verifier_fail "dup08:wrong_subject_count" "$T" "gold_manifest_invalid"

# --- dup09: subject[0] role wrong -------------------------------------------
T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["role"] = "wrong_role"'
expect_verifier_fail "dup09:subject_0_role_wrong" "$T" "gold_manifest_invalid"

# --- dup10: manifest package_id cross-anchor mismatch -----------------------
T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["package_id"] = "proofrail-gold-governed-reliance-anchor-mismatch-001"'
expect_verifier_fail "dup10:package_id_anchor_mismatch" "$T" "gold_manifest_invalid"

# --- dup11: conformance report disagrees on otherwise-valid package ---------
# Non-masking post-structural check: package passes all 23 structural
# checks; mutate the bundled report; rehash subject [1]; the verifier
# re-derives the report from the (unchanged) package and detects bundle
# disagreement, funnelling to gold_manifest_invalid.
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
edit_report "$T" 'r["entries"][0]["status"] = "fail"'
rehash_subject "$T" 1
expect_verifier_fail "dup11:conformance_report_disagrees" "$T" "gold_manifest_invalid"

# ===========================================================================
# Runner-only refusal cases (6 exercises, 5 distinct reasons).
# ===========================================================================

# --- ro1: runner_input_path_missing -----------------------------------------
RO1_OUT="$WORK/ro1-out"
expect_runner_fail "ro1:runner_input_path_missing" \
  "runner_input_path_missing" \
  "$RO1_OUT" \
  "$RUNNER" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO1_OUT" \
    --force

# --- ro2: runner_input_path_forbidden (absolute) ----------------------------
RO2_OUT="$WORK/ro2-out"
expect_runner_fail "ro2:runner_input_path_forbidden" \
  "runner_input_path_forbidden" \
  "$RO2_OUT" \
  "$RUNNER" \
    --input-package "/etc/hostname" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO2_OUT" \
    --force

# --- ro2b: runner_input_path_forbidden (parent-traversal) -------------------
# The runner's path-forbidden preflight rejects BOTH absolute paths and
# parent-traversal relative paths under the same single reason.
RO2B_OUT="$WORK/ro2b-out"
expect_runner_fail "ro2b:runner_input_path_forbidden_traversal" \
  "runner_input_path_forbidden" \
  "$RO2B_OUT" \
  "$RUNNER" \
    --input-package "../leak.json" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO2B_OUT" \
    --force

# --- ro3: runner_input_file_missing -----------------------------------------
RO3_OUT="$WORK/ro3-out"
expect_runner_fail "ro3:runner_input_file_missing" \
  "runner_input_file_missing" \
  "$RO3_OUT" \
  "$RUNNER" \
    --input-package "fixtures/gold-governed-reliance-v0.4.0/no-such-file.json" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO3_OUT" \
    --force

# --- ro4: runner_input_read_failed (directory, portable) --------------------
RO4_OUT="$WORK/ro4-out"
expect_runner_fail "ro4:runner_input_read_failed" \
  "runner_input_read_failed" \
  "$RO4_OUT" \
  "$RUNNER" \
    --input-package "fixtures/gold-governed-reliance-v0.4.0" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="fixtures/gold-governed-reliance-v0.4.0/_test_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --input-package "$BAD_INPUT_REL" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO5_OUT" \
    --force
ro5_rc=$?
set -e
rm -f "$BAD_INPUT_ABS"
if [ "$ro5_rc" -ne 0 ]; then
  exit "$ro5_rc"
fi

# ===========================================================================
# Runner-relay-of-verifier (rel01). The runner relays the verifier's
# OWN reason UNCHANGED; it does NOT wrap it in a sixth runner-only code.
# Staging directory must be cleaned up and destination must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
REL_INPUT_REL="fixtures/gold-governed-reliance-v0.4.0/_test_relay_bad.json"
REL_INPUT_ABS="$REPO_ROOT/$REL_INPUT_REL"
# A package body with the wrong document_type; passes Phase A but
# reaches the verifier's R03 -> gold_package_schema_invalid.
cat > "$REL_INPUT_ABS" <<'EOF'
{
  "document_type": "proofrail.gold.governed_reliance_package_WRONG",
  "schema_version": "v0.1.0",
  "profile": "gold.governed_reliance.v0.4.0",
  "package_id": "proofrail-gold-governed-reliance-rel01-bad-001",
  "governed_reliance_demo_id": "gold-governed-reliance-rel01-bad-001"
}
EOF

set +e
rel_out="$(python3 "$RUNNER" \
  --input-package "$REL_INPUT_REL" \
  --manifest-id "$MANIFEST_ID" \
  --report-id "$REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$REL_OUT" \
  --force \
  --self-validate 2>&1)"
rel_rc=$?
set -e
rm -f "$REL_INPUT_ABS"

if [ "$rel_rc" -ne 1 ]; then
  echo "FAIL: rel01: expected exit 1 (verifier relay), got $rel_rc"
  echo "$rel_out"
  exit 1
fi
# The relayed reason must be the verifier's own structural reason,
# NOT a sixth runner-only code.
if ! echo "$rel_out" | grep -qE "^FAIL: gold_package_schema_invalid:"; then
  echo "FAIL: rel01: expected verifier reason relayed, got:"
  echo "$rel_out"
  exit 1
fi
# Must not be wrapped under any runner-only refusal.
for ronly in runner_input_path_missing runner_input_path_forbidden \
             runner_input_file_missing runner_input_read_failed \
             runner_input_json_invalid; do
  if echo "$rel_out" | grep -qE "^FAIL: ${ronly}:"; then
    echo "FAIL: rel01: runner emitted a runner-only refusal on verifier failure: $ronly"
    echo "$rel_out"
    exit 1
  fi
done
# A speculative sixth wrapper code that does NOT exist must not appear.
# The sentinel name below is deliberately non-reason-shaped so the
# taxonomy gate does not treat it as a reason-like token.
if echo "$rel_out" | grep -qE "^FAIL: runner_wrapper_negative_assertion:"; then
  echo "FAIL: rel01: runner introduced a sixth wrapper code"
  echo "$rel_out"
  exit 1
fi
# Destination must not exist.
if [ -e "$REL_OUT" ]; then
  echo "FAIL: rel01: destination dir was created despite relay failure"
  exit 1
fi
# Staging sibling must not exist.
if ls "${REL_OUT}.staging."* >/dev/null 2>&1; then
  echo "FAIL: rel01: staging dir leaked"
  exit 1
fi
echo "  rel01:runner_relay_of_verifier_failure: ok (verifier reason relayed unchanged)"

# ===========================================================================
# Taxonomy gate (TG1).
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.4.0-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

APPROVED_VERIFIER = {
    "gold_manifest_invalid",
    "gold_package_not_object",
    "gold_package_schema_invalid",
    "gold_profile_unsupported",
    "gold_package_identity_invalid",
    "silver_verification_input_invalid",
    "silver_handoff_input_invalid",
    "policy_pack_input_invalid",
    "registry_lite_input_invalid",
    "control_crosswalk_input_invalid",
    "governed_decision_set_invalid",
    "governed_decision_entry_invalid",
    "decision_subject_binding_invalid",
    "decision_policy_binding_invalid",
    "decision_registry_binding_invalid",
    "decision_action_scope_invalid",
    "decision_status_invalid",
    "acceptance_path_invalid",
    "rejection_path_invalid",
    "challenge_path_invalid",
    "withdrawal_path_invalid",
    "supersession_path_invalid",
    "non_claims_missing",
    "prohibited_gold_claim_present",
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# Per Amendment 4: empty allowlist preserves strict no-additions
# discipline. The negative-assertion sentinels used in rel01
# (runner_wrapper_negative_assertion, subject0_file_absent) are
# deliberately non-reason-shaped under REASON_FILTER and therefore
# never enter the scanner's reason-like bucket.
ALLOWED_NON_REASON_TOKENS: set[str] = set()

APPROVED = APPROVED_VERIFIER | APPROVED_RUNNER | ALLOWED_NON_REASON_TOKENS

TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
REASON_FILTER = re.compile(
    r"(?:_(?:invalid|missing|unsupported|present|forbidden|failed))$|(?:_not_object)$"
)
# Self-check: every approved reason satisfies the test's own reason-like
# filter.
for r in APPROVED_VERIFIER | APPROVED_RUNNER:
    if not TOKEN_RE.fullmatch(r) or not REASON_FILTER.search(r):
        print(
            f"FAIL: taxonomy_gate: approved reason {r!r} does not satisfy "
            f"the test's own reason-like filter; gate is unsafe",
            file=sys.stderr,
        )
        sys.exit(1)

V0_4_0_FILES = [
    "tools/gold/build_gold_governed_reliance_demo_v0_1_0.py",
    "tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py",
    "tools/gold/README.md",
    "tests/test_gold_governed_reliance_v0_4_0.sh",
    "schemas/gold-governed-reliance-package-v0.1.0.md",
    "schemas/gold-governed-reliance-package-manifest-v0.1.0.md",
    "schemas/gold-governed-reliance-conformance-report-v0.1.0.md",
    "docs/gold/minimal-gold-governed-reliance-v0.4.0.md",
    "demos/gold-demo-001-governed-reliance/README.md",
    "demos/gold-demo-001-governed-reliance/demo-walkthrough.md",
    "fixtures/gold-governed-reliance-v0.4.0/README.md",
    "fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json",
    "fixtures/gold-governed-reliance-v0.4.0/scenario-clean-acceptance.json",
    "fixtures/gold-governed-reliance-v0.4.0/scenario-policy-rejection.json",
    "fixtures/gold-governed-reliance-v0.4.0/scenario-challenge-filed.json",
    "fixtures/gold-governed-reliance-v0.4.0/scenario-withdrawal.json",
    "fixtures/gold-governed-reliance-v0.4.0/scenario-supersession.json",
]

# v0.4.0-anchored section markers across the cross-version docs.
SECTION_MARKERS = {
    "README.md": [
        "## What ProofRail v0.4.0 Adds",
    ],
    "CLAUDE.md": [
        "### Gold Governed Reliance Demo: `demos/gold-demo-001-governed-reliance/`",
    ],
    "tools/gold/README.md": [
        "## Gold Governed Reliance Demo Runner (v0.4.0)",
        "## Gold Governed Reliance Demo Verifier (v0.4.0)",
    ],
    "docs/dev/silver-release-index.md": [
        "## Gold v0.4.0",
    ],
    "docs/gold/gold-boundary-v0.2.5.md": [
        "## v0.4.0 Notes",
    ],
}

def collect_unapproved_tokens(label: str, text: str) -> list[str]:
    bad: list[str] = []
    seen: set[str] = set()
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        if tok in seen:
            continue
        seen.add(tok)
        if not REASON_FILTER.search(tok):
            continue
        if tok in APPROVED:
            continue
        bad.append(tok)
    return bad

def extract_section(text: str, start_marker: str) -> str:
    i = text.find(start_marker)
    if i < 0:
        return ""
    rest = text[i + len(start_marker):]
    level = "## " if start_marker.startswith("## ") and not start_marker.startswith("### ") else "### "
    pat = r"^" + re.escape(level)
    m = re.search(pat, rest, flags=re.MULTILINE)
    if m is None:
        return text[i:]
    return text[i : i + len(start_marker) + m.start()]

errors: list[str] = []

for rel in V0_4_0_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.4.0-owned file: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    bad = collect_unapproved_tokens(rel, text)
    for tok in sorted(set(bad)):
        errors.append(f"{rel}: unapproved reason-like token: {tok}")

# Scoped scan of v0.4.0 sections in cross-version docs.
for rel, markers in SECTION_MARKERS.items():
    p = repo / rel
    if not p.exists():
        errors.append(f"missing cross-version doc: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for marker in markers:
        section = extract_section(text, marker)
        if not section:
            errors.append(
                f"{rel}: missing v0.4.0 section anchor ({marker!r})"
            )
            continue
        bad = collect_unapproved_tokens(marker, section)
        for tok in sorted(set(bad)):
            errors.append(
                f"{rel} [section {marker!r}]: "
                f"unapproved reason-like token: {tok}"
            )

if errors:
    print(
        "FAIL: taxonomy_gate: unapproved reason-like tokens found in "
        "v0.4.0-owned surface area",
        file=sys.stderr,
    )
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)

print("  TG1:taxonomy_gate: ok (no unapproved reason-like tokens)")
PYEOF

# ---------------------------------------------------------------------------
# Scoped sha256 snapshot (AFTER) and equality with BEFORE.
# ---------------------------------------------------------------------------
snapshot_scoped "$WORK/scoped.after"
if ! diff -u "$WORK/scoped.before" "$WORK/scoped.after"; then
  echo "FAIL: scoped sha256 snapshot drifted across test cases"
  exit 1
fi
echo "  SS:scoped_sha256_snapshot: ok (BEFORE == AFTER)"

# ---------------------------------------------------------------------------
# Done.
# ---------------------------------------------------------------------------
echo "PASS: tests/test_gold_governed_reliance_v0_4_0.sh"
echo "  53/53 exercises:"
echo "    - 4 positive-path (PP1..PP4)"
echo "    - 5 scenario checks (SC1..SC5)"
echo "    - 24 canonical verifier reasons (case01..case24)"
echo "    - 11 duplicate gold_manifest_invalid (dup01..dup11)"
echo "    - 6 runner-only refusals (ro1, ro2, ro2b, ro3..ro5)"
echo "    - 1 runner-relay-of-verifier (rel01)"
echo "    - 1 taxonomy gate (TG1)"
echo "    - 1 scoped sha256 snapshot (SS)"
