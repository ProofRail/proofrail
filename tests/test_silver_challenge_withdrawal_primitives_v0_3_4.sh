#!/usr/bin/env bash
# tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh
#
# Regression test for the ProofRail Silver v0.3.4 challenge/withdrawal
# primitives package.
#
# Numbered exercises (36 total):
#
#   Positive-path (4):
#     PP1  Pristine end-to-end build with --self-validate
#     PP2  Pristine independent verifier pass on the package
#     PP3  Inline structural cross-check of manifest subject layout
#     PP4  Inline structural cross-check of derived summary
#
#   Verifier mutation cases (25; cover the 24 stable verifier reasons,
#   with challenge_withdrawal_subject_path_traversal exercised twice
#   — once for the `..` form and once for the absolute-path form):
#     case01   invalid_challenge_withdrawal_manifest
#     case02a  challenge_withdrawal_subject_path_traversal   (..)
#     case02b  challenge_withdrawal_subject_path_traversal   (absolute)
#     case03   challenge_withdrawal_subject_file_missing
#     case04   challenge_withdrawal_subject_hash_mismatch
#     case05   nested_handoff_invalid                        (v0.3.0 sub)
#     case06   challenge_record_invalid
#     case07   withdrawal_record_invalid
#     case08   challenge_record_target_mismatch
#     case09   withdrawal_record_target_mismatch
#     case10   challenge_record_reason_invalid
#     case11   challenge_record_status_invalid
#     case12   challenge_record_evidence_ref_invalid
#     case13   withdrawal_record_reason_invalid
#     case14   withdrawal_record_status_invalid
#     case15   withdrawal_record_evidence_ref_invalid
#     case16   withdrawal_record_challenge_ref_mismatch
#     case17   challenge_withdrawal_time_order_invalid
#     case18   challenge_withdrawal_summary_invalid
#     case19   challenge_withdrawal_summary_binding_mismatch
#     case20   challenge_withdrawal_summary_count_mismatch
#     case21   challenge_withdrawal_posture_invalid
#     case22   challenge_withdrawal_overclaim                (Amendment 3)
#     case23   challenge_withdrawal_limitations_missing
#     case24   challenge_withdrawal_non_claims_missing
#
#   Runner-only refusal cases (5):
#     case25   handoff_validation_failed
#     case26   challenge_record_validation_failed
#     case27   withdrawal_record_validation_failed
#     case28   challenge_withdrawal_binding_failed
#     case29   challenge_withdrawal_self_validation_failed   (monkey-patch)
#
#   Taxonomy gate (1):
#     TG1    Scan v0.3.4-owned files (and the v0.3.4-anchored sections of
#            tools/silver/README.md) for reason-like tokens, asserting
#            every such token is in the approved verifier or runner
#            allowlist defined in this test.
#
#   Scoped sha256 snapshot (1):
#     SS     scoped sha256 snapshot of 9 committed v0.3.4 source paths
#            BEFORE and AFTER all cases must be identical
#
# Coverage summary:
#   * 24/24 stable verifier failure reasons covered. No reason is
#     OR-accepted; each case asserts its exact stable reason.
#   * 5/5 runner-only refusal codes covered. nested_handoff_invalid
#     (verifier) and handoff_validation_failed (runner) are treated as
#     distinct surfaces with their own direct tests.
#   * Atomic --force semantics asserted: runner refusals leave NO final
#     --output-dir and NO staging sibling on disk.
#   * Taxonomy gate enforces strict no-additions discipline against the
#     approved 24 verifier reasons and 5 runner-only refusal reasons.
#
# Reachability notes (matches the orderings documented in
# docs/silver/silver-challenge-withdrawal-primitives-v0.3.4.md):
#   * challenge_withdrawal_subject_path_traversal is DIRECTLY reachable.
#     The verifier checks each subject's `path` for traversal (`..`) or
#     an absolute prefix BEFORE comparing it to the fixed SUBJECT_ORDER.
#   * Closed-enum and evidence_refs problems on the packaged records
#     route to dedicated reasons (challenge_record_reason_invalid /
#     challenge_record_status_invalid / challenge_record_evidence_ref_invalid
#     and the withdrawal_record_* triple). The structural validators
#     deliberately skip these checks so the dedicated later steps fire
#     instead of collapsing into challenge_record_invalid /
#     withdrawal_record_invalid.
#   * challenge_record_target_mismatch and withdrawal_record_target_mismatch
#     are each a SINGLE consolidated reason that absorbs placeholder /
#     hash / record_id divergences against the target handoff. Each case
#     mutates one such variant; coverage of the consolidated step is
#     complete because all three sub-paths route to the same reason.
#   * challenge_withdrawal_overclaim is DIRECTLY reachable by mutating
#     the optional claim.description field (Amendment 3), which is the
#     designated free-text overclaim-scanned field.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER="$REPO_ROOT/tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py"
HANDOFF_RUNNER="$REPO_ROOT/tools/silver/build_silver_acceptance_handoff_v0_1_0.py"
CHALLENGE_FIX="$REPO_ROOT/fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json"
WITHDRAWAL_FIX="$REPO_ROOT/fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json"

WORK="$(mktemp -d -t proofrail-v0.3.4-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-06-29T00:30:00Z"
MANIFEST_ID="silver-challenge-withdrawal-v0.3.4-test-001"
SUMMARY_ID="silver-challenge-withdrawal-summary-v0.3.4-test-001"

# --- Scoped sha256 snapshot of committed v0.3.4 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-challenge-record-v0.1.0.md"
  "schemas/silver-withdrawal-record-v0.1.0.md"
  "schemas/silver-challenge-withdrawal-summary-v0.1.0.md"
  "schemas/silver-challenge-withdrawal-manifest-v0.1.0.md"
  "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/README.md"
  "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json"
  "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json"
  "tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py"
  "tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py"
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

# --- Pre-step: ensure a v0.3.0 acceptance handoff target package exists ---
TARGET_HANDOFF_ROOT="$WORK/target-handoff-package"
echo "[pre] generating fresh v0.3.0 acceptance handoff target package"
python3 "$HANDOFF_RUNNER" \
  --composed-evidence-manifest /tmp/proofrail-silver-composed-gateway-demo-v0.2.7/composed-gateway-evidence-manifest.json \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --drill-manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  --generated-at 2026-06-28T00:00:00Z \
  --output-dir "$TARGET_HANDOFF_ROOT" \
  --force \
  --self-validate >/dev/null

PRISTINE="$WORK/pristine"

# ---------------------------------------------------------------------------
# Step 1 (PP1): pristine build with --self-validate.
# ---------------------------------------------------------------------------
echo "[step1] pristine challenge/withdrawal primitives build with --self-validate"
python3 "$RUNNER" \
  --target-handoff-root "$TARGET_HANDOFF_ROOT" \
  --challenge-record "$CHALLENGE_FIX" \
  --withdrawal-record "$WITHDRAWAL_FIX" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] pristine independent verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/silver-challenge-withdrawal-manifest.json" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] inline manifest layout check"
python3 - <<EOF
import json
m = json.loads(open("$PRISTINE/silver-challenge-withdrawal-manifest.json").read())
assert m["document_type"] == "proofrail.silver.challenge_withdrawal_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "v0.3.4"
assert m["hash_algorithm"] == "sha256"
assert len(m["subjects"]) == 4
expected = [
  ("target-handoff/silver-acceptance-handoff-manifest.json", "target_handoff_manifest"),
  ("records/challenge-record.json", "challenge_record"),
  ("records/withdrawal-record.json", "withdrawal_record"),
  ("silver-challenge-withdrawal-summary.json", "challenge_withdrawal_summary"),
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
# Step 4 (PP4): inline structural check of derived summary contents.
# ---------------------------------------------------------------------------
echo "[step4] inline summary contents check"
python3 - <<EOF
import json
s = json.loads(open("$PRISTINE/silver-challenge-withdrawal-summary.json").read())
assert s["document_type"] == "proofrail.silver.challenge_withdrawal_summary"
assert s["proofrail_release"] == "v0.3.4"
assert s["target"]["target_type"] == "silver_acceptance_handoff"
assert s["target"]["target_manifest_path"] == "target-handoff/silver-acceptance-handoff-manifest.json"
assert s["target"]["target_manifest_sha256"].startswith("sha256:")
assert s["records"]["challenge_record_path"] == "records/challenge-record.json"
assert s["records"]["withdrawal_record_path"] == "records/withdrawal-record.json"
assert s["summary"]["challenge_count"] == 1
assert s["summary"]["withdrawal_count"] == 1
assert s["summary"]["challenge_status"] == "filed"
assert s["summary"]["withdrawal_status"] == "withdrawal_recorded"
assert s["summary"]["withdrawal_effect"] == "local_reuse_paused_for_review"
assert s["summary"]["posture"] == "challenged_with_local_reuse_paused_for_review"
claim_ids = [c["claim_id"] for c in s["claims"]]
assert claim_ids == [
    "target_handoff_verified",
    "challenge_record_valid",
    "withdrawal_record_valid",
    "challenge_and_withdrawal_target_same_handoff",
    "withdrawal_cites_challenge",
    "time_order_valid",
    "no_adjudication_claimed",
], claim_ids
for c in s["claims"]:
    assert c["status"] == "pass", c
    assert isinstance(c["evidence_refs"], list) and len(c["evidence_refs"]) > 0, c
EOF

# Also verify packaged records are present and bound.
python3 - <<EOF
import json
c = json.loads(open("$PRISTINE/records/challenge-record.json").read())
w = json.loads(open("$PRISTINE/records/withdrawal-record.json").read())
assert c["target"]["target_manifest_sha256"] != "sha256:TO_BE_BOUND_BY_RUNNER"
assert w["target"]["target_manifest_sha256"] != "sha256:TO_BE_BOUND_BY_RUNNER"
assert c["target"]["target_manifest_sha256"].startswith("sha256:")
assert w["target"]["target_manifest_sha256"] == c["target"]["target_manifest_sha256"]
assert w["related_challenge_record_id"] == c["challenge_record_id"]
EOF

# ---------------------------------------------------------------------------
# Helpers for tampered-package cases.
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# Recompute sha256 + size_bytes for a single subject index in the
# outer challenge/withdrawal manifest, after a semantic edit. Lets a
# mutation reach the intended later check instead of short-circuiting
# on challenge_withdrawal_subject_hash_mismatch.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "silver-challenge-withdrawal-manifest.json")
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

expect_verifier_fail() {
  local label="$1" pkg="$2" expected="$3"
  set +e
  local out rc
  out="$(python3 "$VERIFIER" --manifest "$pkg/silver-challenge-withdrawal-manifest.json" 2>&1)"
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

echo "[cases] running 25 verifier mutation cases + 5 runner-only cases + taxonomy gate"

# ---------------------------------------------------------------------------
# Case 01: invalid_challenge_withdrawal_manifest — wrong manifest document_type.
# ---------------------------------------------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-challenge-withdrawal-manifest.json"
m = json.loads(open(mp).read())
m["document_type"] = "proofrail.silver.NOT_a_challenge_withdrawal_manifest"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case01:invalid_challenge_withdrawal_manifest" "$T" \
  "invalid_challenge_withdrawal_manifest"

# ---------------------------------------------------------------------------
# Case 02a: challenge_withdrawal_subject_path_traversal — subject[0].path
# becomes "../etc/passwd". Checked BEFORE exact SUBJECT_ORDER equality.
# ---------------------------------------------------------------------------
T="$WORK/c02a"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-challenge-withdrawal-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][0]["path"] = "../etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02a:challenge_withdrawal_subject_path_traversal(..)" "$T" \
  "challenge_withdrawal_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 02b: challenge_withdrawal_subject_path_traversal — absolute path.
# ---------------------------------------------------------------------------
T="$WORK/c02b"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
mp = sys.argv[1] + "/silver-challenge-withdrawal-manifest.json"
m = json.loads(open(mp).read())
m["subjects"][3]["path"] = "/etc/passwd"
open(mp, "w").write(json.dumps(m, indent=2, sort_keys=True) + "\n")
EOF
expect_verifier_fail "case02b:challenge_withdrawal_subject_path_traversal(absolute)" "$T" \
  "challenge_withdrawal_subject_path_traversal"

# ---------------------------------------------------------------------------
# Case 03: challenge_withdrawal_subject_file_missing — delete subject[3]
# (the summary file).
# ---------------------------------------------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
rm -f "$T/silver-challenge-withdrawal-summary.json"
expect_verifier_fail "case03:challenge_withdrawal_subject_file_missing" "$T" \
  "challenge_withdrawal_subject_file_missing"

# ---------------------------------------------------------------------------
# Case 04: challenge_withdrawal_subject_hash_mismatch — modify subject[3]
# without rehashing the manifest.
# ---------------------------------------------------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
printf "\n" >> "$T/silver-challenge-withdrawal-summary.json"
expect_verifier_fail "case04:challenge_withdrawal_subject_hash_mismatch" "$T" \
  "challenge_withdrawal_subject_hash_mismatch"

# ---------------------------------------------------------------------------
# Case 05: nested_handoff_invalid — delete a required nested file inside
# target-handoff/ to fail the unchanged v0.3.0 verifier subprocess. The
# top-level target-handoff manifest file (subject[0]) is unchanged so
# subject[0] sha256 still matches; the v0.3.0 verifier fires because a
# referenced subject inside it cannot be found.
# ---------------------------------------------------------------------------
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
rm -f "$T/target-handoff/silver-acceptance-handoff-summary.json"
expect_verifier_fail "case05:nested_handoff_invalid" "$T" \
  "nested_handoff_invalid"

# ---------------------------------------------------------------------------
# Case 06: challenge_record_invalid — packaged challenge record has wrong
# document_type. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["document_type"] = "proofrail.silver.NOT_a_challenge_record"
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case06:challenge_record_invalid" "$T" \
  "challenge_record_invalid"

# ---------------------------------------------------------------------------
# Case 07: withdrawal_record_invalid — packaged withdrawal record has
# wrong document_type. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["document_type"] = "proofrail.silver.NOT_a_withdrawal_record"
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case07:withdrawal_record_invalid" "$T" \
  "withdrawal_record_invalid"

# ---------------------------------------------------------------------------
# Case 08: challenge_record_target_mismatch — set a syntactically valid
# but wrong target_manifest_sha256 in the packaged challenge record.
# This is one of three sub-paths (placeholder / hash / record_id) that
# all route to the same consolidated reason in the verifier's Step 20.
# Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["target"]["target_manifest_sha256"] = "sha256:" + ("a" * 64)
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case08:challenge_record_target_mismatch" "$T" \
  "challenge_record_target_mismatch"

# ---------------------------------------------------------------------------
# Case 09: withdrawal_record_target_mismatch — same consolidated step
# on the withdrawal record (verifier's Step 21). Requires rehashing
# subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["target"]["target_manifest_sha256"] = "sha256:" + ("a" * 64)
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case09:withdrawal_record_target_mismatch" "$T" \
  "withdrawal_record_target_mismatch"

# ---------------------------------------------------------------------------
# Case 10: challenge_record_reason_invalid — set challenge.challenge_reason
# to a value outside the closed reason set. The structural validator
# deliberately skips this enum check so the dedicated later step fires.
# Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["challenge"]["challenge_reason"] = "not_a_valid_reason_value"
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case10:challenge_record_reason_invalid" "$T" \
  "challenge_record_reason_invalid"

# ---------------------------------------------------------------------------
# Case 11: challenge_record_status_invalid — set challenge.challenge_status
# to a value outside the closed status set. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["challenge"]["challenge_status"] = "not_a_valid_status_value"
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case11:challenge_record_status_invalid" "$T" \
  "challenge_record_status_invalid"

# ---------------------------------------------------------------------------
# Case 12: challenge_record_evidence_ref_invalid — add a path-traversal
# entry to the packaged challenge record's evidence_refs. The structural
# validator only checks the list type; the dedicated later step does
# the per-entry traversal check. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["evidence_refs"] = list(c.get("evidence_refs") or []) + ["../escape/secret.txt"]
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case12:challenge_record_evidence_ref_invalid" "$T" \
  "challenge_record_evidence_ref_invalid"

# ---------------------------------------------------------------------------
# Case 13: withdrawal_record_reason_invalid — set withdrawal.withdrawal_reason
# to a value outside the closed reason set. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["withdrawal"]["withdrawal_reason"] = "not_a_valid_reason_value"
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case13:withdrawal_record_reason_invalid" "$T" \
  "withdrawal_record_reason_invalid"

# ---------------------------------------------------------------------------
# Case 14: withdrawal_record_status_invalid — set withdrawal.withdrawal_status
# to a value outside the closed status set. Requires rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["withdrawal"]["withdrawal_status"] = "not_a_valid_status_value"
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case14:withdrawal_record_status_invalid" "$T" \
  "withdrawal_record_status_invalid"

# ---------------------------------------------------------------------------
# Case 15: withdrawal_record_evidence_ref_invalid — add a path-traversal
# entry to the packaged withdrawal record's evidence_refs. Requires
# rehashing subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["evidence_refs"] = list(w.get("evidence_refs") or []) + ["../escape/secret.txt"]
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case15:withdrawal_record_evidence_ref_invalid" "$T" \
  "withdrawal_record_evidence_ref_invalid"

# ---------------------------------------------------------------------------
# Case 16: withdrawal_record_challenge_ref_mismatch — change the packaged
# withdrawal record's related_challenge_record_id. Requires rehashing
# subject[2].
# ---------------------------------------------------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
wp = sys.argv[1] + "/records/withdrawal-record.json"
w = json.loads(open(wp).read())
w["related_challenge_record_id"] = "proofrail-not-the-real-challenge-id"
open(wp, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 2
expect_verifier_fail "case16:withdrawal_record_challenge_ref_mismatch" "$T" \
  "withdrawal_record_challenge_ref_mismatch"

# ---------------------------------------------------------------------------
# Case 17: challenge_withdrawal_time_order_invalid — set the packaged
# challenge.filed_at to a time BEFORE the target handoff's generated_at.
# The structural ISO-8601 parse succeeds, the binding cross-checks pass,
# and the time-order check fires. Requires rehashing subject[1].
# ---------------------------------------------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
cp = sys.argv[1] + "/records/challenge-record.json"
c = json.loads(open(cp).read())
c["filed_at"] = "2020-01-01T00:00:00Z"
open(cp, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 1
expect_verifier_fail "case17:challenge_withdrawal_time_order_invalid" "$T" \
  "challenge_withdrawal_time_order_invalid"

# ---------------------------------------------------------------------------
# Case 18: challenge_withdrawal_summary_invalid — packaged summary has
# wrong document_type. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["document_type"] = "proofrail.silver.NOT_a_summary"
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case18:challenge_withdrawal_summary_invalid" "$T" \
  "challenge_withdrawal_summary_invalid"

# ---------------------------------------------------------------------------
# Case 19: challenge_withdrawal_summary_binding_mismatch — set a
# syntactically valid but wrong target_manifest_sha256 in the summary.
# Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["target"]["target_manifest_sha256"] = "sha256:" + ("b" * 64)
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case19:challenge_withdrawal_summary_binding_mismatch" "$T" \
  "challenge_withdrawal_summary_binding_mismatch"

# ---------------------------------------------------------------------------
# Case 20: challenge_withdrawal_summary_count_mismatch — set
# summary.summary.challenge_count = 2. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["summary"]["challenge_count"] = 2
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case20:challenge_withdrawal_summary_count_mismatch" "$T" \
  "challenge_withdrawal_summary_count_mismatch"

# ---------------------------------------------------------------------------
# Case 21: challenge_withdrawal_posture_invalid — change
# summary.summary.posture to a value in the closed set that does NOT
# match the withdrawal_effect mapping table entry. Requires rehashing
# subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
# withdrawal_effect = local_reuse_paused_for_review =>
# expected posture = challenged_with_local_reuse_paused_for_review.
# We pick a different closed-set value to force the mapping mismatch.
s["summary"]["posture"] = "record_superseded"
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case21:challenge_withdrawal_posture_invalid" "$T" \
  "challenge_withdrawal_posture_invalid"

# ---------------------------------------------------------------------------
# Case 22: challenge_withdrawal_overclaim — set the optional
# description field on claims[0] to a string containing a forbidden
# token (Amendment 3). The description field is the designated free-text
# overclaim-scanned field, reachable for mutation without breaking any
# earlier check. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["claims"][0]["description"] = "This handoff received regulator approval after audit."
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case22:challenge_withdrawal_overclaim" "$T" \
  "challenge_withdrawal_overclaim"

# ---------------------------------------------------------------------------
# Case 23: challenge_withdrawal_limitations_missing — empty
# scope_limitations in the summary. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["scope_limitations"] = []
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case23:challenge_withdrawal_limitations_missing" "$T" \
  "challenge_withdrawal_limitations_missing"

# ---------------------------------------------------------------------------
# Case 24: challenge_withdrawal_non_claims_missing — empty non_claims
# in the summary. Requires rehashing subject[3].
# ---------------------------------------------------------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
python3 - "$T" <<'EOF'
import json, sys
sp = sys.argv[1] + "/silver-challenge-withdrawal-summary.json"
s = json.loads(open(sp).read())
s["non_claims"] = []
open(sp, "w").write(json.dumps(s, indent=2, sort_keys=True) + "\n")
EOF
rehash_subject "$T" 3
expect_verifier_fail "case24:challenge_withdrawal_non_claims_missing" "$T" \
  "challenge_withdrawal_non_claims_missing"

# ---------------------------------------------------------------------------
# Case 25 (runner-only): handoff_validation_failed — pass a target
# handoff root whose nested file is deleted so the v0.3.0 verifier
# subprocess fails.
# ---------------------------------------------------------------------------
BAD_HANDOFF="$WORK/bad-handoff"
cp -r "$TARGET_HANDOFF_ROOT" "$BAD_HANDOFF"
rm -f "$BAD_HANDOFF/silver-acceptance-handoff-summary.json"
OUT25="$WORK/r25"
expect_runner_fail "case25:handoff_validation_failed" \
  "handoff_validation_failed" "$OUT25" \
  "$RUNNER" \
  --target-handoff-root "$BAD_HANDOFF" \
  --challenge-record "$CHALLENGE_FIX" \
  --withdrawal-record "$WITHDRAWAL_FIX" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT25" \
  --force

# ---------------------------------------------------------------------------
# Case 26 (runner-only): challenge_record_validation_failed — pass a
# challenge record fixture with a wrong document_type.
# ---------------------------------------------------------------------------
BAD_CHALLENGE="$WORK/bad-challenge.json"
python3 - "$BAD_CHALLENGE" "$CHALLENGE_FIX" <<'EOF'
import json, sys
out, src = sys.argv[1], sys.argv[2]
c = json.loads(open(src).read())
c["document_type"] = "proofrail.silver.NOT_a_challenge_record"
open(out, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
OUT26="$WORK/r26"
expect_runner_fail "case26:challenge_record_validation_failed" \
  "challenge_record_validation_failed" "$OUT26" \
  "$RUNNER" \
  --target-handoff-root "$TARGET_HANDOFF_ROOT" \
  --challenge-record "$BAD_CHALLENGE" \
  --withdrawal-record "$WITHDRAWAL_FIX" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT26" \
  --force

# ---------------------------------------------------------------------------
# Case 27 (runner-only): withdrawal_record_validation_failed — pass a
# withdrawal record fixture with a wrong document_type.
# ---------------------------------------------------------------------------
BAD_WITHDRAWAL="$WORK/bad-withdrawal.json"
python3 - "$BAD_WITHDRAWAL" "$WITHDRAWAL_FIX" <<'EOF'
import json, sys
out, src = sys.argv[1], sys.argv[2]
w = json.loads(open(src).read())
w["document_type"] = "proofrail.silver.NOT_a_withdrawal_record"
open(out, "w").write(json.dumps(w, indent=2, sort_keys=True) + "\n")
EOF
OUT27="$WORK/r27"
expect_runner_fail "case27:withdrawal_record_validation_failed" \
  "withdrawal_record_validation_failed" "$OUT27" \
  "$RUNNER" \
  --target-handoff-root "$TARGET_HANDOFF_ROOT" \
  --challenge-record "$CHALLENGE_FIX" \
  --withdrawal-record "$BAD_WITHDRAWAL" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT27" \
  --force

# ---------------------------------------------------------------------------
# Case 28 (runner-only): challenge_withdrawal_binding_failed — pass a
# challenge record fixture whose target.target_record_id does NOT match
# the target handoff's handoff_id. Structural validation passes; cross-
# binding fails.
# ---------------------------------------------------------------------------
BAD_BIND_CHALLENGE="$WORK/bad-bind-challenge.json"
python3 - "$BAD_BIND_CHALLENGE" "$CHALLENGE_FIX" <<'EOF'
import json, sys
out, src = sys.argv[1], sys.argv[2]
c = json.loads(open(src).read())
c["target"]["target_record_id"] = "proofrail-some-other-handoff-id"
open(out, "w").write(json.dumps(c, indent=2, sort_keys=True) + "\n")
EOF
OUT28="$WORK/r28"
expect_runner_fail "case28:challenge_withdrawal_binding_failed" \
  "challenge_withdrawal_binding_failed" "$OUT28" \
  "$RUNNER" \
  --target-handoff-root "$TARGET_HANDOFF_ROOT" \
  --challenge-record "$BAD_BIND_CHALLENGE" \
  --withdrawal-record "$WITHDRAWAL_FIX" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT28" \
  --force

# ---------------------------------------------------------------------------
# Case 29 (runner-only): challenge_withdrawal_self_validation_failed —
# monkey-patch the runner's CHALLENGE_WITHDRAWAL_VERIFIER constant to
# point at a tiny verifier script that always exits 1, then invoke with
# --self-validate. The runner stages the package and fails self-
# validation, which must leave NO destination directory and NO staging
# sibling.
# ---------------------------------------------------------------------------
FAKE_VERIFIER="$WORK/fake-verifier.py"
cat > "$FAKE_VERIFIER" <<'EOF'
#!/usr/bin/env python3
import sys
print("FAIL: synthetic_self_validation_failure: forced by test", file=sys.stderr)
sys.exit(1)
EOF
chmod +x "$FAKE_VERIFIER"

WRAPPED_RUNNER="$WORK/wrapped-runner.py"
cat > "$WRAPPED_RUNNER" <<EOF
#!/usr/bin/env python3
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location(
    "runner_mod", "$RUNNER"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["runner_mod"] = mod
spec.loader.exec_module(mod)
mod.CHALLENGE_WITHDRAWAL_VERIFIER = Path("$FAKE_VERIFIER")
sys.exit(mod.main(sys.argv[1:]))
EOF
chmod +x "$WRAPPED_RUNNER"

OUT29="$WORK/r29"
expect_runner_fail "case29:challenge_withdrawal_self_validation_failed" \
  "challenge_withdrawal_self_validation_failed" "$OUT29" \
  "$WRAPPED_RUNNER" \
  --target-handoff-root "$TARGET_HANDOFF_ROOT" \
  --challenge-record "$CHALLENGE_FIX" \
  --withdrawal-record "$WITHDRAWAL_FIX" \
  --manifest-id "$MANIFEST_ID" \
  --summary-id "$SUMMARY_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$OUT29" \
  --force \
  --self-validate

# ---------------------------------------------------------------------------
# Exercise TG1: taxonomy gate.
#
# Scan every v0.3.4-owned source / schema / doc / fixture file (and the
# v0.3.4-anchored sections of tools/silver/README.md) for reason-like
# tokens matching `[a-z][a-z0-9]+(?:_[a-z0-9]+)+`. A token is treated as
# "reason-like" if it (a) starts with `invalid_`, OR (b) ends in one of
# the reason suffixes `_invalid`, `_mismatch`, `_missing`, `_failed`,
# `_traversal`, `_overclaim`. Every reason-like token must appear in
# the approved verifier (24) or runner (5) allowlists below, or in
# the small ALLOWED_NON_REASON_TOKENS escape hatch. The gate fails the
# test if any unapproved reason-like token is found.
#
# Allowlists are defined inline in this test so a drifted reason name
# introduced anywhere in v0.3.4 surface area is caught at regression
# time, with no documentation lag.
# ---------------------------------------------------------------------------
echo "[gate] TG1 taxonomy gate over v0.3.4-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

APPROVED_VERIFIER = {
    "invalid_challenge_withdrawal_manifest",
    "challenge_withdrawal_subject_file_missing",
    "challenge_withdrawal_subject_path_traversal",
    "challenge_withdrawal_subject_hash_mismatch",
    "nested_handoff_invalid",
    "challenge_record_invalid",
    "challenge_record_target_mismatch",
    "challenge_record_reason_invalid",
    "challenge_record_status_invalid",
    "challenge_record_evidence_ref_invalid",
    "withdrawal_record_invalid",
    "withdrawal_record_target_mismatch",
    "withdrawal_record_challenge_ref_mismatch",
    "withdrawal_record_reason_invalid",
    "withdrawal_record_status_invalid",
    "withdrawal_record_evidence_ref_invalid",
    "challenge_withdrawal_time_order_invalid",
    "challenge_withdrawal_summary_invalid",
    "challenge_withdrawal_summary_binding_mismatch",
    "challenge_withdrawal_summary_count_mismatch",
    "challenge_withdrawal_posture_invalid",
    "challenge_withdrawal_overclaim",
    "challenge_withdrawal_limitations_missing",
    "challenge_withdrawal_non_claims_missing",
}
APPROVED_RUNNER = {
    "handoff_validation_failed",
    "challenge_record_validation_failed",
    "withdrawal_record_validation_failed",
    "challenge_withdrawal_binding_failed",
    "challenge_withdrawal_self_validation_failed",
}

# Escape hatch for tokens that look reason-like under the regex filter
# but are deliberately not protocol reasons. Kept minimal on purpose;
# add only when a demonstrated false positive arises.
ALLOWED_NON_REASON_TOKENS = {
    # Synthetic stderr emitted by the in-test fake verifier used by
    # case29 to force a self-validation failure.
    "synthetic_self_validation_failure",
    # Helper function names that incidentally end in a reason-like
    # suffix (`_traversal`, `_overclaim`) but are private implementation
    # symbols, not public verifier reasons.
    "has_path_traversal",
    "scan_overclaim",
}

APPROVED = APPROVED_VERIFIER | APPROVED_RUNNER | ALLOWED_NON_REASON_TOKENS

# Sanity: every approved reason itself satisfies the reason-like
# filter we apply to scanned tokens. If this check ever fires it
# means the allowlist is being weakly enforced.
# Word-boundary anchors prevent the scanner from extracting a suffix
# fragment of a longer underscored identifier (so e.g. a prose phrase
# like `*_target_mismatch` does not yield a bare reason-like suffix).
TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
REASON_FILTER = re.compile(
    r"(?:^invalid_)|(?:_(?:invalid|mismatch|missing|failed|traversal|overclaim)$)"
)
for r in APPROVED_VERIFIER | APPROVED_RUNNER:
    if not TOKEN_RE.fullmatch(r) or not REASON_FILTER.search(r):
        print(
            f"FAIL: taxonomy_gate: approved reason {r!r} does not satisfy "
            f"the test's own reason-like filter; gate is unsafe",
            file=sys.stderr,
        )
        sys.exit(1)

V0_3_4_FILES = [
    "tools/silver/build_silver_challenge_withdrawal_primitives_v0_1_0.py",
    "tools/silver/verify_silver_challenge_withdrawal_primitives_v0_1_0.py",
    "tests/test_silver_challenge_withdrawal_primitives_v0_3_4.sh",
    "schemas/silver-challenge-record-v0.1.0.md",
    "schemas/silver-withdrawal-record-v0.1.0.md",
    "schemas/silver-challenge-withdrawal-manifest-v0.1.0.md",
    "schemas/silver-challenge-withdrawal-summary-v0.1.0.md",
    "docs/silver/silver-challenge-withdrawal-primitives-v0.3.4.md",
    "demos/silver-demo-011-challenge-withdrawal-primitives/README.md",
    "demos/silver-demo-011-challenge-withdrawal-primitives/demo-walkthrough.md",
    "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/README.md",
    "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/challenge-record.json",
    "fixtures/silver-challenge-withdrawal-primitives-v0.3.4/withdrawal-record.json",
]

V0_3_4_README_SECTION_MARKERS = [
    "## Silver Challenge / Withdrawal Record Primitives Runner (v0.3.4)",
    "## Silver Challenge / Withdrawal Record Primitives Verifier (v0.3.4)",
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

for rel in V0_3_4_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.3.4-owned file: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    bad = collect_unapproved_tokens(rel, text)
    for tok in sorted(set(bad)):
        errors.append(f"{rel}: unapproved reason-like token: {tok}")

# Scoped scan of tools/silver/README.md v0.3.4 sections (Runner + Verifier).
readme = repo / "tools/silver/README.md"
if readme.exists():
    rtext = readme.read_text(encoding="utf-8", errors="replace")
    for marker in V0_3_4_README_SECTION_MARKERS:
        section = extract_section(rtext, marker)
        if not section:
            errors.append(
                f"tools/silver/README.md: missing v0.3.4 section anchor "
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
        "v0.3.4-owned surface area",
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
echo "[snapshot] scoped sha256 snapshot stable across all v0.3.4 cases"

echo "PASS: silver challenge/withdrawal primitives v0.3.4 regression test"
