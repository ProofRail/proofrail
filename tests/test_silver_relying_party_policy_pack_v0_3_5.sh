#!/usr/bin/env bash
# tests/test_silver_relying_party_policy_pack_v0_3_5.sh
#
# Regression test for the ProofRail Silver v0.3.5 Relying-Party Policy
# Pack package.
#
# Numbered exercises (47 total):
#
#   Positive-path (4):
#     PP1   Pristine end-to-end build with --self-validate
#     PP2   Pristine independent verifier pass on the package
#     PP3   Inline structural cross-check of manifest subject layout
#     PP4   Inline structural cross-check of bundled conformance report
#
#   Canonical verifier mutation cases (24; one per approved reason,
#   in CHECKS_ORDER):
#     case01  policy_pack_manifest_invalid    (manifest document_type)
#     case02  policy_pack_not_object          (pack is JSON array)
#     case03  policy_pack_schema_invalid      (pack document_type)
#     case04  policy_pack_profile_unsupported
#     case05  policy_pack_identity_invalid
#     case06  policy_pack_authority_invalid
#     case07  policy_scope_invalid
#     case08  protected_action_scope_invalid
#     case09  silver_handoff_requirement_invalid
#     case10  verifier_requirement_invalid
#     case11  issuer_requirement_invalid
#     case12  revocation_requirement_invalid
#     case13  freshness_requirement_invalid
#     case14  challenge_requirement_invalid
#     case15  withdrawal_requirement_invalid
#     case16  supersession_requirement_invalid
#     case17  acceptance_criteria_invalid
#     case18  rejection_criteria_invalid
#     case19  exception_policy_invalid
#     case20  hard_stop_policy_invalid
#     case21  warning_policy_invalid
#     case22  reference_policy_invalid
#     case23  non_claims_missing
#     case24  prohibited_claim_present
#
#   Duplicate manifest-invalid cases (11; secondary manifest defects
#   that all route to policy_pack_manifest_invalid; reported separately
#   so the 24 canonical cases above remain exactly one-per-reason):
#     dup01   subjects field missing
#     dup02   wrong subject count (3 instead of 2)
#     dup03   subject[0] role wrong
#     dup04   subject[1] role wrong
#     dup05   subject[0] path absolute
#     dup06   subject[0] path contains '..'
#     dup07   subject[0] sha256 mismatch
#     dup08   subject[1] sha256 mismatch
#     dup09   subject[0] size_bytes wrong
#     dup10   manifest_id missing
#     dup11   conformance report disagreement on otherwise-valid pack
#             (non-masking post-structural check)
#
#   Runner-only refusal cases (5; preflight only):
#     ro1     runner_input_path_missing
#     ro2     runner_input_path_forbidden       (absolute path)
#     ro3     runner_input_file_missing
#     ro4     runner_input_read_failed          (directory, portable)
#     ro5     runner_input_json_invalid
#
#   Runner-relay-of-verifier (1; separate from the 5 runner-only):
#     rel01   --self-validate on a structurally bad pack relays the
#             verifier's own reason UNCHANGED, NOT wrapped in a sixth
#             runner-only code; staging directory is removed.
#
#   Taxonomy gate (1):
#     TG1     Scan v0.3.5-owned files (and v0.3.5-anchored sections of
#             tools/silver/README.md) for reason-like tokens; assert
#             every such token is in the approved verifier-or-runner
#             allowlist defined in this test.
#
#   Scoped sha256 snapshot (1):
#     SS      scoped sha256 snapshot of committed v0.3.5 source paths
#             BEFORE and AFTER all cases must be identical.
#
# Coverage summary:
#   * 24/24 stable verifier failure reasons covered by canonical cases.
#     No reason is OR-accepted; each canonical case asserts its exact
#     stable reason.
#   * 11 additional manifest-invalid defects are listed as dup01..dup11
#     so the 24 canonical reason map remains one-per-reason; dup11 is
#     specifically the NON-MASKING post-structural conformance-report
#     mismatch on an otherwise-valid pack.
#   * 5/5 runner-only refusal codes covered. The runner-relay-of-
#     verifier behavior is exercised separately as rel01 to assert no
#     sixth code is introduced.
#   * Atomic --force semantics asserted for runner refusals: NO final
#     --output-dir and NO staging sibling on disk.
#   * Taxonomy gate enforces strict no-additions discipline against the
#     approved 24 verifier reasons and 5 runner-only refusal reasons.
#
# Hash-first re-anchoring:
#   Every canonical/duplicate mutation that lives INSIDE a subject body
#   is followed by a rehash_subject call to re-anchor the manifest's
#   subject sha256 and size_bytes. This guarantees the mutated case
#   reaches its intended structural check instead of short-circuiting
#   on the upstream check_01 manifest integrity step.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py"
PACK_FIX_REL="fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json"
PACK_FIX="$REPO_ROOT/$PACK_FIX_REL"

WORK="$(mktemp -d -t proofrail-v0.3.5-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-07-15T00:00:00Z"
MANIFEST_ID="silver-relying-party-policy-pack-manifest-v0.3.5-test-001"
REPORT_ID="silver-relying-party-policy-pack-conformance-report-v0.3.5-test-001"

PACK_REL="silver-relying-party-policy-pack.json"
REPORT_REL_FILE="silver-relying-party-policy-pack-conformance-report.json"
MANIFEST_REL_FILE="silver-relying-party-policy-pack-manifest.json"

# --- Scoped sha256 snapshot of committed v0.3.5 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-relying-party-policy-pack-v0.1.0.md"
  "schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md"
  "schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md"
  "fixtures/silver-relying-party-policy-pack-v0.3.5/README.md"
  "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json"
  "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-exception.json"
  "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-warning-policy.json"
  "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-freshness-windows.json"
  "tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py"
  "tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py"
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
echo "[step1] pristine relying-party policy pack build with --self-validate"
python3 "$RUNNER" \
  --policy-pack "$PACK_FIX_REL" \
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
assert m["document_type"] == "proofrail.silver.relying_party_policy_pack_manifest", m["document_type"]
assert m["schema_version"] == "0.1.0"
assert m["proofrail_release"] == "v0.3.5"
assert m["hash_algorithm"] == "sha256"
assert isinstance(m["manifest_id"], str) and m["manifest_id"]
assert isinstance(m["policy_pack_id"], str) and m["policy_pack_id"]
assert len(m["subjects"]) == 2
expected = [
  ("silver-relying-party-policy-pack.json", "policy_pack"),
  ("silver-relying-party-policy-pack-conformance-report.json",
   "policy_pack_conformance_report"),
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
# Step 4 (PP4): inline structural check of bundled conformance report.
# ---------------------------------------------------------------------------
echo "[step4] inline conformance report check"
python3 - "$PRISTINE/$REPORT_REL_FILE" <<'EOF'
import json, sys
rp = sys.argv[1]
r = json.loads(open(rp).read())
assert r["document_type"] == "proofrail.silver.relying_party_policy_pack_conformance_report"
assert r["schema_version"] == "0.1.0"
assert r["proofrail_release"] == "v0.3.5"
assert isinstance(r["report_id"], str) and r["report_id"]
assert isinstance(r["policy_pack_id"], str) and r["policy_pack_id"]
assert r["policy_pack_sha256"].startswith("sha256:")
checks = r["checks"]
assert len(checks) == 24, len(checks)
EXPECTED = [
  ("check_01","policy_pack_manifest_invalid"),
  ("check_02","policy_pack_not_object"),
  ("check_03","policy_pack_schema_invalid"),
  ("check_04","policy_pack_profile_unsupported"),
  ("check_05","policy_pack_identity_invalid"),
  ("check_06","policy_pack_authority_invalid"),
  ("check_07","policy_scope_invalid"),
  ("check_08","protected_action_scope_invalid"),
  ("check_09","silver_handoff_requirement_invalid"),
  ("check_10","verifier_requirement_invalid"),
  ("check_11","issuer_requirement_invalid"),
  ("check_12","revocation_requirement_invalid"),
  ("check_13","freshness_requirement_invalid"),
  ("check_14","challenge_requirement_invalid"),
  ("check_15","withdrawal_requirement_invalid"),
  ("check_16","supersession_requirement_invalid"),
  ("check_17","acceptance_criteria_invalid"),
  ("check_18","rejection_criteria_invalid"),
  ("check_19","exception_policy_invalid"),
  ("check_20","hard_stop_policy_invalid"),
  ("check_21","warning_policy_invalid"),
  ("check_22","reference_policy_invalid"),
  ("check_23","non_claims_missing"),
  ("check_24","prohibited_claim_present"),
]
for i, (cid, reason) in enumerate(EXPECTED):
    assert checks[i]["check_id"] == cid, (i, checks[i])
    assert checks[i]["approved_reason_name"] == reason, (i, checks[i])
    assert checks[i]["status"] == "pass", (i, checks[i])
EOF

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
# short-circuiting on the upstream check_01 manifest integrity step.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "silver-relying-party-policy-pack-manifest.json")
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

# Edit the policy-pack JSON in a staging package via a Python snippet.
# Caller supplies a Python program operating on the dict `pack`.
edit_pack() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
pp = os.path.join(pkg, "silver-relying-party-policy-pack.json")
pack = json.loads(open(pp).read())
exec(expr, {"pack": pack, "json": json})
# Preserve the input fixture's exact text format: 2-space indent +
# trailing newline. Sort keys=False to mirror the hand-authored
# layout - the verifier doesn't care about key order in the pack,
# only its canonical conformance-report byte-image.
open(pp, "w").write(json.dumps(pack, indent=2) + "\n")
EOF
}

# Edit the outer manifest via a Python snippet operating on dict `m`.
# Does NOT recompute subject hashes by itself; rehash_subject must be
# called explicitly when the caller intends to.
edit_manifest() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
mp = os.path.join(pkg, "silver-relying-party-policy-pack-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
}

# Edit the bundled conformance report via a Python snippet operating
# on dict `r`. Re-emits with the verifier's canonical
# (sort_keys, separators=(",",":")) byte image so the manifest's
# subject [1] hash CAN be re-anchored cleanly with rehash_subject.
edit_report() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
rp = os.path.join(pkg, "silver-relying-party-policy-pack-conformance-report.json")
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

echo "[cases] 24 canonical + 11 duplicate + 5 runner-only + 1 runner-relay + taxonomy gate"

# ===========================================================================
# Canonical verifier mutation cases (24, one per approved reason)
# ===========================================================================

# --- case01: policy_pack_manifest_invalid -----------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:policy_pack_manifest_invalid" "$T" "policy_pack_manifest_invalid"

# --- case02: policy_pack_not_object (pack is JSON array) --------------------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$PACK_REL', 'w') as f:
    f.write(json.dumps([1,2,3], indent=2) + '\n')
"
rehash_subject "$T" 0
expect_verifier_fail "case02:policy_pack_not_object" "$T" "policy_pack_not_object"

# --- case03: policy_pack_schema_invalid -------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["document_type"] = "wrong"'
rehash_subject "$T" 0
expect_verifier_fail "case03:policy_pack_schema_invalid" "$T" "policy_pack_schema_invalid"

# --- case04: policy_pack_profile_unsupported --------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["profile"] = "some.other.profile"'
rehash_subject "$T" 0
expect_verifier_fail "case04:policy_pack_profile_unsupported" "$T" "policy_pack_profile_unsupported"

# --- case05: policy_pack_identity_invalid -----------------------------------
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["relying_party"].pop("identity_id")'
rehash_subject "$T" 0
expect_verifier_fail "case05:policy_pack_identity_invalid" "$T" "policy_pack_identity_invalid"

# --- case06: policy_pack_authority_invalid ----------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["policy_authority"].pop("approver_role")'
rehash_subject "$T" 0
expect_verifier_fail "case06:policy_pack_authority_invalid" "$T" "policy_pack_authority_invalid"

# --- case07: policy_scope_invalid -------------------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" '
pack["policy"]["effective_period"]["starts_at"] = "2099-01-01T00:00:00Z"
pack["policy"]["effective_period"]["ends_at"]   = "2026-12-31T23:59:59Z"
'
rehash_subject "$T" 0
expect_verifier_fail "case07:policy_scope_invalid" "$T" "policy_scope_invalid"

# --- case08: protected_action_scope_invalid ---------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["applicable_protected_actions"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case08:protected_action_scope_invalid" "$T" "protected_action_scope_invalid"

# --- case09: silver_handoff_requirement_invalid -----------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["silver_handoff_requirements"]["minimum_handoff_posture"] = "for_demo_scope_invalid"'
rehash_subject "$T" 0
expect_verifier_fail "case09:silver_handoff_requirement_invalid" "$T" "silver_handoff_requirement_invalid"

# --- case10: verifier_requirement_invalid -----------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["verifier_requirements"]["minimum_posture"] = "not.a.valid.posture"'
rehash_subject "$T" 0
expect_verifier_fail "case10:verifier_requirement_invalid" "$T" "verifier_requirement_invalid"

# --- case11: issuer_requirement_invalid -------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["issuer_requirements"]["required_signature_algorithm"] = "rsa-4096"'
rehash_subject "$T" 0
expect_verifier_fail "case11:issuer_requirement_invalid" "$T" "issuer_requirement_invalid"

# --- case12: revocation_requirement_invalid ---------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["revocation_requirements"]["mode"] = "optional"'
rehash_subject "$T" 0
expect_verifier_fail "case12:revocation_requirement_invalid" "$T" "revocation_requirement_invalid"

# --- case13: freshness_requirement_invalid ----------------------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["freshness_requirements"]["max_age_seconds"] = -1'
rehash_subject "$T" 0
expect_verifier_fail "case13:freshness_requirement_invalid" "$T" "freshness_requirement_invalid"

# --- case14: challenge_requirement_invalid ----------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["challenge_handling"]["posture"] = "do_nothing"'
rehash_subject "$T" 0
expect_verifier_fail "case14:challenge_requirement_invalid" "$T" "challenge_requirement_invalid"

# --- case15: withdrawal_requirement_invalid ---------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["withdrawal_handling"]["posture"] = "ignore"'
rehash_subject "$T" 0
expect_verifier_fail "case15:withdrawal_requirement_invalid" "$T" "withdrawal_requirement_invalid"

# --- case16: supersession_requirement_invalid -------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["supersession_handling"]["posture"] = "merge"'
rehash_subject "$T" 0
expect_verifier_fail "case16:supersession_requirement_invalid" "$T" "supersession_requirement_invalid"

# --- case17: acceptance_criteria_invalid ------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["acceptance_criteria"]["required_silver_results"] = ["unknown_result"]'
rehash_subject "$T" 0
expect_verifier_fail "case17:acceptance_criteria_invalid" "$T" "acceptance_criteria_invalid"

# --- case18: rejection_criteria_invalid -------------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["rejection_criteria"]["blocking_silver_results"] = ["definitely_not_a_real_result"]'
rehash_subject "$T" 0
expect_verifier_fail "case18:rejection_criteria_invalid" "$T" "rejection_criteria_invalid"

# --- case19: exception_policy_invalid ---------------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["exceptions"] = [{"exception_id": "x"}]'
rehash_subject "$T" 0
expect_verifier_fail "case19:exception_policy_invalid" "$T" "exception_policy_invalid"

# --- case20: hard_stop_policy_invalid ---------------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" '
pack["hard_stops"] = [{"hard_stop_id": "x", "description": "y", "overridable_by_exception": True}]
'
rehash_subject "$T" 0
expect_verifier_fail "case20:hard_stop_policy_invalid" "$T" "hard_stop_policy_invalid"

# --- case21: warning_policy_invalid -----------------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["warning_treatment"]["unknown_warning_default"] = "ignore"'
rehash_subject "$T" 0
expect_verifier_fail "case21:warning_policy_invalid" "$T" "warning_policy_invalid"

# --- case22: reference_policy_invalid ---------------------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" '
pack["related_silver_artifacts"] = [{
  "artifact_role": "silver_handoff_manifest",
  "path": "/abs/path/leak.json",
  "description": "absolute path is forbidden"
}]
'
rehash_subject "$T" 0
expect_verifier_fail "case22:reference_policy_invalid" "$T" "reference_policy_invalid"

# --- case23: non_claims_missing ---------------------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["non_claims"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case23:non_claims_missing" "$T" "non_claims_missing"

# --- case24: prohibited_claim_present ---------------------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
edit_pack "$T" 'pack["relying_party"]["identity_label"] = "Demo Relying Party (certified)"'
rehash_subject "$T" 0
expect_verifier_fail "case24:prohibited_claim_present" "$T" "prohibited_claim_present"

# ===========================================================================
# Duplicate manifest-invalid cases (11; all route to manifest_invalid).
# ===========================================================================

# --- dup01: subjects field missing ------------------------------------------
T="$WORK/d01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm.pop("subjects")'
expect_verifier_fail "dup01:subjects_missing" "$T" "policy_pack_manifest_invalid"

# --- dup02: wrong subject count (3) -----------------------------------------
T="$WORK/d02"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"sha256:" + "0"*64, "size_bytes":0})'
expect_verifier_fail "dup02:wrong_subject_count" "$T" "policy_pack_manifest_invalid"

# --- dup03: subject[0] role wrong -------------------------------------------
T="$WORK/d03"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["role"] = "wrong_role"'
expect_verifier_fail "dup03:subject_0_role_wrong" "$T" "policy_pack_manifest_invalid"

# --- dup04: subject[1] role wrong -------------------------------------------
T="$WORK/d04"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["role"] = "wrong_role"'
expect_verifier_fail "dup04:subject_1_role_wrong" "$T" "policy_pack_manifest_invalid"

# --- dup05: subject[0] path absolute ----------------------------------------
T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "dup05:subject_0_path_absolute" "$T" "policy_pack_manifest_invalid"

# --- dup06: subject[0] path contains '..' -----------------------------------
T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "../escape.json"'
expect_verifier_fail "dup06:subject_0_path_traversal" "$T" "policy_pack_manifest_invalid"

# --- dup07: subject[0] sha256 mismatch --------------------------------------
T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["sha256"] = "sha256:" + "f" * 64'
expect_verifier_fail "dup07:subject_0_sha_mismatch" "$T" "policy_pack_manifest_invalid"

# --- dup08: subject[1] sha256 mismatch --------------------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["sha256"] = "sha256:" + "f" * 64'
expect_verifier_fail "dup08:subject_1_sha_mismatch" "$T" "policy_pack_manifest_invalid"

# --- dup09: subject[0] size_bytes wrong -------------------------------------
T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["size_bytes"] = 0'
expect_verifier_fail "dup09:subject_0_size_wrong" "$T" "policy_pack_manifest_invalid"

# --- dup10: manifest_id missing ---------------------------------------------
T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm.pop("manifest_id")'
expect_verifier_fail "dup10:manifest_id_missing" "$T" "policy_pack_manifest_invalid"

# --- dup11: conformance report disagrees on otherwise-valid pack -----------
# Non-masking post-structural check: pack passes all 24 structural
# checks; mutate the bundled report; rehash subject [1]; the verifier
# re-derives the report from the (unchanged) pack and detects bundle
# disagreement, emitting policy_pack_manifest_invalid.
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
edit_report "$T" 'r["checks"][0]["status"] = "fail"'
rehash_subject "$T" 1
expect_verifier_fail "dup11:conformance_report_disagrees" "$T" "policy_pack_manifest_invalid"

# ===========================================================================
# Runner-only refusal cases (5; preflight only).
# ===========================================================================

# --- ro1: runner_input_path_missing -----------------------------------------
RO1_OUT="$WORK/ro1-out"
expect_runner_fail "ro1:runner_input_path_missing" \
  "runner_input_path_missing" \
  "$RO1_OUT" \
  "$RUNNER" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO1_OUT" \
    --force

# --- ro2: runner_input_path_forbidden (absolute) ----------------------------
RO2_OUT="$WORK/ro2-out"
expect_runner_fail "ro2:runner_input_path_forbidden" \
  "runner_input_path_forbidden" \
  "$RO2_OUT" \
  "$RUNNER" \
    --policy-pack "/etc/hostname" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO2_OUT" \
    --force

# --- ro3: runner_input_file_missing -----------------------------------------
RO3_OUT="$WORK/ro3-out"
expect_runner_fail "ro3:runner_input_file_missing" \
  "runner_input_file_missing" \
  "$RO3_OUT" \
  "$RUNNER" \
    --policy-pack "fixtures/silver-relying-party-policy-pack-v0.3.5/no-such-file.json" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO3_OUT" \
    --force

# --- ro4: runner_input_read_failed (directory, portable) --------------------
RO4_OUT="$WORK/ro4-out"
expect_runner_fail "ro4:runner_input_read_failed" \
  "runner_input_read_failed" \
  "$RO4_OUT" \
  "$RUNNER" \
    --policy-pack "fixtures/silver-relying-party-policy-pack-v0.3.5" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="fixtures/silver-relying-party-policy-pack-v0.3.5/_test_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --policy-pack "$BAD_INPUT_REL" \
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
# Runner-relay-of-verifier (1; rel01). The runner relays the verifier's
# OWN reason UNCHANGED; it does NOT wrap it in a sixth runner-only code.
# Staging directory must be cleaned up and destination must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
REL_INPUT_REL="fixtures/silver-relying-party-policy-pack-v0.3.5/_test_relay_bad.json"
REL_INPUT_ABS="$REPO_ROOT/$REL_INPUT_REL"
# A pack with the wrong document_type; reaches the verifier's
# check_03 -> policy_pack_schema_invalid.
cat > "$REL_INPUT_ABS" <<'EOF'
{
  "document_type": "proofrail.silver.relying_party_policy_pack_WRONG",
  "schema_version": "0.1.0",
  "policy_pack_id": "rel01-bad"
}
EOF

set +e
rel_out="$(python3 "$RUNNER" \
  --policy-pack "$REL_INPUT_REL" \
  --generated-at "$GEN_AT" \
  --output-dir "$REL_OUT" \
  --force \
  --self-validate 2>&1)"
rel_rc=$?
set -e
rm -f "$REL_INPUT_ABS"

# Verifier exits 1 on structural failure; relayed unchanged the runner
# must also exit 1.
if [ "$rel_rc" -ne 1 ]; then
  echo "FAIL: rel01: expected exit 1 (verifier relay), got $rel_rc"
  echo "$rel_out"
  exit 1
fi
# The relayed reason must be the verifier's own structural reason,
# NOT a sixth runner-only code.
if ! echo "$rel_out" | grep -qE "^FAIL: policy_pack_schema_invalid:"; then
  echo "FAIL: rel01: expected verifier reason relayed, got:"
  echo "$rel_out"
  exit 1
fi
# Must not be a sixth runner-only refusal.
for ronly in runner_input_path_missing runner_input_path_forbidden \
             runner_input_file_missing runner_input_read_failed \
             runner_input_json_invalid; do
  if echo "$rel_out" | grep -qE "^FAIL: ${ronly}:"; then
    echo "FAIL: rel01: runner emitted a runner-only refusal on verifier failure: $ronly"
    echo "$rel_out"
    exit 1
  fi
done
# A speculative sixth code that does NOT exist must not appear.
if echo "$rel_out" | grep -qE "^FAIL: runner_self_validation_failed:"; then
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
#
# Scan v0.3.5-owned files (and the v0.3.5-anchored sections of
# tools/silver/README.md) for reason-like tokens. The test fails if any
# unapproved reason-like token is found.
#
# Allowlists are defined inline in this test so a drifted reason name
# introduced anywhere in v0.3.5 surface area is caught at regression
# time, with no documentation lag.
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.3.5-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

APPROVED_VERIFIER = {
    "policy_pack_manifest_invalid",
    "policy_pack_not_object",
    "policy_pack_schema_invalid",
    "policy_pack_profile_unsupported",
    "policy_pack_identity_invalid",
    "policy_pack_authority_invalid",
    "policy_scope_invalid",
    "protected_action_scope_invalid",
    "silver_handoff_requirement_invalid",
    "verifier_requirement_invalid",
    "issuer_requirement_invalid",
    "revocation_requirement_invalid",
    "freshness_requirement_invalid",
    "challenge_requirement_invalid",
    "withdrawal_requirement_invalid",
    "supersession_requirement_invalid",
    "acceptance_criteria_invalid",
    "rejection_criteria_invalid",
    "exception_policy_invalid",
    "hard_stop_policy_invalid",
    "warning_policy_invalid",
    "reference_policy_invalid",
    "non_claims_missing",
    "prohibited_claim_present",
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# Escape hatch for tokens that look reason-like under the regex filter
# but are deliberately not protocol reasons. Kept minimal on purpose.
ALLOWED_NON_REASON_TOKENS = {
    # Helper function names that incidentally end in a reason-like
    # suffix but are private implementation symbols.
    "has_path_traversal",
    # Composite labels used as test-case identifiers (not reasons).
    "runner_relay_of_verifier_failure",
    # Closed enum values that are protocol data (acceptance_criteria.
    # required_silver_results and rejection_criteria.blocking_silver_
    # results). These are policy pack data fields, not failure reasons.
    "attestation_present",
    "attestation_missing",
    # Test-case mutation labels and bogus data values used to trigger
    # genuine approved reasons. These appear only in the test file.
    "subjects_missing",
    "manifest_id_missing",
    "manifest_invalid",
    "for_demo_scope_invalid",
    # Defensive scaffolding: the test explicitly asserts that a
    # hypothetical sixth runner wrapper code does NOT appear in any
    # output. The token exists only in a negative assertion.
    "runner_self_validation_failed",
}

APPROVED = APPROVED_VERIFIER | APPROVED_RUNNER | ALLOWED_NON_REASON_TOKENS

# Word-boundary anchors prevent the scanner from extracting a suffix
# fragment of a longer underscored identifier.
TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
REASON_FILTER = re.compile(
    r"(?:_(?:invalid|missing|unsupported|present|forbidden|failed))$|(?:_not_object)$"
)
# Self-check: every approved reason satisfies our reason-like filter.
for r in APPROVED_VERIFIER | APPROVED_RUNNER:
    if not TOKEN_RE.fullmatch(r) or not REASON_FILTER.search(r):
        print(
            f"FAIL: taxonomy_gate: approved reason {r!r} does not satisfy "
            f"the test's own reason-like filter; gate is unsafe",
            file=sys.stderr,
        )
        sys.exit(1)

V0_3_5_FILES = [
    "tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py",
    "tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py",
    "tests/test_silver_relying_party_policy_pack_v0_3_5.sh",
    "schemas/silver-relying-party-policy-pack-v0.1.0.md",
    "schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md",
    "schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md",
    "docs/silver/silver-relying-party-policy-pack-v0.3.5.md",
    "demos/silver-demo-012-relying-party-policy-pack/README.md",
    "demos/silver-demo-012-relying-party-policy-pack/demo-walkthrough.md",
    "fixtures/silver-relying-party-policy-pack-v0.3.5/README.md",
    "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json",
    "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-exception.json",
    "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-warning-policy.json",
    "fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack-with-freshness-windows.json",
]

V0_3_5_README_SECTION_MARKERS = [
    "## Silver Relying-Party Policy Pack Runner (v0.3.5)",
    "## Silver Relying-Party Policy Pack Verifier (v0.3.5)",
]

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
    m = re.search(r"^## ", rest, flags=re.MULTILINE)
    if m is None:
        return text[i:]
    return text[i : i + len(start_marker) + m.start()]

errors: list[str] = []

for rel in V0_3_5_FILES:
    p = repo / rel
    if not p.exists():
        # The demo/walkthrough/release-doc files may be created at a
        # later step; missing files are reported but not yet fatal here
        # only for the demo/walkthrough/release-doc set. v0.3.5
        # implementation completion requires ALL of these to exist.
        errors.append(f"missing v0.3.5-owned file: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    bad = collect_unapproved_tokens(rel, text)
    for tok in sorted(set(bad)):
        errors.append(f"{rel}: unapproved reason-like token: {tok}")

# Scoped scan of tools/silver/README.md v0.3.5 sections.
readme = repo / "tools/silver/README.md"
if readme.exists():
    rtext = readme.read_text(encoding="utf-8", errors="replace")
    for marker in V0_3_5_README_SECTION_MARKERS:
        section = extract_section(rtext, marker)
        if not section:
            errors.append(
                f"tools/silver/README.md: missing v0.3.5 section anchor "
                f"({marker!r})"
            )
            continue
        bad = collect_unapproved_tokens(marker, section)
        for tok in sorted(set(bad)):
            errors.append(
                f"tools/silver/README.md [section {marker!r}]: "
                f"unapproved reason-like token: {tok}"
            )

if errors:
    print(
        "FAIL: taxonomy_gate: unapproved reason-like tokens found in "
        "v0.3.5-owned surface area",
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
echo "PASS: tests/test_silver_relying_party_policy_pack_v0_3_5.sh"
echo "  47/47 exercises:"
echo "    - 4 positive-path (PP1..PP4)"
echo "    - 24 canonical verifier reasons (case01..case24)"
echo "    - 11 duplicate manifest-invalid (dup01..dup11)"
echo "    - 5 runner-only refusals (ro1..ro5)"
echo "    - 1 runner-relay-of-verifier (rel01)"
echo "    - 1 taxonomy gate (TG1)"
echo "    - 1 scoped sha256 snapshot (SS)"
