#!/usr/bin/env bash
# tests/test_gold_decision_report_hardening_v0_4_1.sh
#
# Regression test for the ProofRail v0.4.1 Gold Decision Report
# Hardening package. v0.4.1 extends v0.4.0 with a third manifest subject
# (the derived decision report) and five new ordered verifier checks
# (R25..R29) bolted onto the inherited 24 v0.4.0 reasons. The v0.4.1
# verifier DELEGATES the inherited 24 checks to the co-located v0.4.0
# verifier (a repo tooling dependency).
#
# Numbered exercises (61 total):
#
#   Positive-path (6):
#     PP1   Pristine build with --self-validate
#     PP2   Pristine independent v0.4.1 verifier pass on the package
#     PP3   Inline structural check of manifest layout (3 subjects,
#           fixed roles, fixed order, bare-hex SHA-256, identifier
#           distinctness)
#     PP4   Inline structural check of bundled conformance report (24
#           pass entries, byte-identical to v0.4.0-shaped derivation)
#     PP5   Inline structural check of derived decision report (top-level
#           shape, decision_count, decision_rows, coverage_summary,
#           source_package_sha256 == subject[0].sha256)
#     PP6   Inline structural check that decision_report_id !=
#           conformance_report_id (manifest identifier distinctness)
#
#   Canonical verifier mutation cases (29 = 24 inherited + 5 v0.4.1):
#     case01..case24 — inherited v0.4.0 reasons relayed verbatim via
#                      the v0.4.1 verifier's subprocess delegation to
#                      the unchanged v0.4.0 verifier.
#     case25  gold_decision_report_not_object
#     case26  gold_decision_report_schema_invalid
#     case27  gold_decision_report_binding_invalid
#     case28  gold_decision_report_projection_invalid
#     case29  gold_decision_report_summary_invalid
#
#   Duplicate / secondary gold_manifest_invalid cases (15; all route to
#   gold_manifest_invalid; reported separately so the 29 canonical cases
#   remain exactly one-per-reason):
#     dup01   subject[0] path absolute
#     dup02   subject[0] path traversal
#     dup03   subject[1] path absolute
#     dup04   subject[1] path traversal
#     dup05   subject[2] path absolute
#     dup06   subject[2] path traversal
#     dup07   subject[0] file missing on disk
#     dup08   subject[0] size_bytes mismatch
#     dup09   subject[0] sha256 mismatch
#     dup10   wrong subject count (4 entries)
#     dup11   subject[0] role wrong
#     dup12   subject[2] role wrong
#     dup13   manifest package_id cross-anchor mismatch
#     dup14   manifest governed_reliance_demo_id cross-anchor mismatch
#     dup15   decision_report_id == conformance_report_id (identifier
#             collision; v0.4.1-specific)
#
#   Supplemental decision-report-binding case (1; routes to R27,
#   gold_decision_report_binding_invalid; reported separately from the
#   duplicate manifest-invalid set because source_package_sha256 lives in
#   the decision report, not the manifest):
#     sup01   decision report source_package_sha256 != subject[0].sha256
#             (folds to R27; supplemental coverage alongside case27 which
#             mutates the decision report's package_id binding instead of
#             its source_package_sha256 binding)
#
#   Runner-only refusal cases (6 exercises, 5 distinct reasons):
#     ro1     runner_input_path_missing
#     ro2     runner_input_path_forbidden       (absolute path)
#     ro2b    runner_input_path_forbidden       (parent-traversal path)
#     ro3     runner_input_file_missing
#     ro4     runner_input_read_failed          (directory, portable)
#     ro5     runner_input_json_invalid
#
#   Runner-relay-of-verifier (rel01):
#     rel01   --self-validate on a structurally bad v0.4.1 package body
#             relays the v0.4.1 verifier's OWN reason UNCHANGED, NOT
#             wrapped in a sixth runner-only code; staging directory is
#             removed.
#
#   Verifier-relay-of-inherited (rel02):
#     rel02   Mutation of the v0.4.1 package body subject[0] triggers
#             the inherited v0.4.0 verifier reason gold_package_schema_invalid
#             via the v0.4.1 verifier's subprocess delegation. The reason
#             must be relayed VERBATIM with no v0.4.1 wrapping, no INFRA:
#             diagnostic, and no R-code substitution.
#
#   Taxonomy gate (TG1):
#     TG1     Scan v0.4.1-owned files for reason-shaped tokens; every
#             such token must belong to the approved 29-reason verifier
#             set, the approved 5-reason runner-only set, or a narrow
#             documented allow-list. Additionally enforce an explicit
#             deny-list of environmental/wrapper escape token patterns
#             (substrings: see DENY_SUBSTRINGS in the TG1 block below)
#             so that any future drift toward wrapping environment
#             failures as public reasons trips the gate.
#
#   Scoped sha256 snapshot (SS):
#     SS      Scoped sha256 snapshot of committed v0.4.1-owned source
#             paths BEFORE and AFTER must be identical (the test does
#             not mutate v0.4.1-owned source files).
#
# Notes on subprocess delegation:
#   The v0.4.1 verifier subprocess-invokes the co-located v0.4.0
#   verifier. This is a repo tooling dependency; any change to the
#   co-located v0.4.0 verifier must rerun BOTH the v0.4.0 and v0.4.1
#   regression suites. The env-failure path (missing co-located v0.4.0
#   verifier) emits a non-reason-shaped INFRA: diagnostic and never
#   collapses into any of the 29 verifier reasons or 5 runner-only
#   refusal names.
#
# Hash-first re-anchoring:
#   Every mutation that lives INSIDE a subject body is followed by a
#   rehash_subject call to re-anchor the manifest's subject sha256 and
#   size_bytes. v0.4.1 uses BARE lowercase hex SHA-256 (no `sha256:`
#   label prefix) in every manifest sha256 field, the decision report's
#   source_package_sha256, and every internal fingerprint field.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/gold/build_gold_decision_report_hardening_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_decision_report_hardening_v0_1_0.py"
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"

WORK="$(mktemp -d -t proofrail-v0.4.1-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-09-15T00:30:00Z"
MANIFEST_ID="proofrail-gold-decision-report-manifest-test-001"
CONFORMANCE_REPORT_ID="proofrail-gold-decision-report-conformance-test-001"
DECISION_REPORT_ID="proofrail-gold-decision-report-test-001"

PACKAGE_REL="governed-reliance-scenarios.json"
CONFORMANCE_REL_FILE="silver-gold-governed-reliance-conformance-report.json"
DECISION_REL_FILE="gold-governed-reliance-decision-report.json"
MANIFEST_REL_FILE="gold-decision-report-package-manifest.json"

# --- Scoped sha256 snapshot of committed v0.4.1-owned source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/gold-governed-reliance-decision-report-v0.1.0.md"
  "schemas/gold-decision-report-package-manifest-v0.1.0.md"
  "fixtures/gold-decision-report-hardening-v0.4.1/README.md"
  "tools/gold/build_gold_decision_report_hardening_v0_1_0.py"
  "tools/gold/verify_gold_decision_report_hardening_v0_1_0.py"
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
echo "[step1] PP1 pristine v0.4.1 build with --self-validate"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] PP2 pristine independent v0.4.1 verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] PP3 inline manifest layout check"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" <<'EOF'
import json, sys, re
mp = sys.argv[1]
m = json.loads(open(mp).read())
assert m["document_type"] == "proofrail.gold.decision_report_package_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "gold.decision_report_hardening.v0.4.1"
assert m["hash_algorithm"] == "sha256"
for field in ("manifest_id", "conformance_report_id", "decision_report_id",
              "package_id", "governed_reliance_demo_id"):
    assert isinstance(m[field], str) and m[field], field
# v0.4.1 manifest deliberately carries NO generic report_id.
assert "report_id" not in m, "v0.4.1 manifest must not carry generic report_id"
# Identifier distinctness.
assert m["decision_report_id"] != m["conformance_report_id"], \
    "decision_report_id == conformance_report_id violates identifier distinctness"
assert len(m["subjects"]) == 3, len(m["subjects"])
expected = [
  ("governed-reliance-scenarios.json", "governed_reliance_package"),
  ("silver-gold-governed-reliance-conformance-report.json", "conformance_report"),
  ("gold-governed-reliance-decision-report.json", "decision_report"),
]
bare_hex = re.compile(r"^[0-9a-f]{64}$")
for i, (p, r) in enumerate(expected):
    assert m["subjects"][i]["path"] == p, (i, m["subjects"][i]["path"])
    assert m["subjects"][i]["role"] == r, (i, m["subjects"][i]["role"])
    sha = m["subjects"][i]["sha256"]
    assert bare_hex.match(sha), f"subject {i} sha not bare hex: {sha!r}"
    assert isinstance(m["subjects"][i]["size_bytes"], int)
    assert m["subjects"][i]["size_bytes"] > 0
EOF

# ---------------------------------------------------------------------------
# Step 4 (PP4): inline structural check of bundled conformance report.
# ---------------------------------------------------------------------------
echo "[step4] PP4 inline conformance report check"
python3 - "$PRISTINE/$CONFORMANCE_REL_FILE" <<'EOF'
import json, sys
rp = sys.argv[1]
r = json.loads(open(rp).read())
assert r["document_type"] == "proofrail.gold.governed_reliance_conformance_report", r["document_type"]
assert r["schema_version"] == "v0.1.0"
assert isinstance(r["entries"], list)
assert len(r["entries"]) == 24, len(r["entries"])
EXPECTED = [
  "gold_manifest_invalid", "gold_package_not_object", "gold_package_schema_invalid",
  "gold_profile_unsupported", "gold_package_identity_invalid",
  "silver_verification_input_invalid", "silver_handoff_input_invalid",
  "policy_pack_input_invalid", "registry_lite_input_invalid",
  "control_crosswalk_input_invalid", "governed_decision_set_invalid",
  "governed_decision_entry_invalid", "decision_subject_binding_invalid",
  "decision_policy_binding_invalid", "decision_registry_binding_invalid",
  "decision_action_scope_invalid", "decision_status_invalid",
  "acceptance_path_invalid", "rejection_path_invalid", "challenge_path_invalid",
  "withdrawal_path_invalid", "supersession_path_invalid", "non_claims_missing",
  "prohibited_gold_claim_present",
]
for i, reason in enumerate(EXPECTED):
    e = r["entries"][i]
    assert e["check_id"] == f"check_{i+1:02d}", (i, e["check_id"])
    assert e["check_name"] == reason, (i, e["check_name"], reason)
    assert e["status"] == "pass", (i, e["status"])
EOF

# ---------------------------------------------------------------------------
# Step 5 (PP5): inline structural check of derived decision report.
# ---------------------------------------------------------------------------
echo "[step5] PP5 inline decision report check"
python3 - "$PRISTINE/$DECISION_REL_FILE" "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$PACKAGE_REL" <<'EOF'
import json, sys, re, hashlib
dp, mp, pp = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.loads(open(dp).read())
m = json.loads(open(mp).read())
assert d["document_type"] == "proofrail.gold.governed_reliance_decision_report", d["document_type"]
assert d["schema_version"] == "v0.1.0"
assert d["profile"] == "gold.decision_report_hardening.v0.4.1", d["profile"]
assert d["decision_report_id"] == m["decision_report_id"]
assert d["package_id"] == m["package_id"]
assert d["governed_reliance_demo_id"] == m["governed_reliance_demo_id"]
bare_hex = re.compile(r"^[0-9a-f]{64}$")
assert bare_hex.match(d["source_package_sha256"]), d["source_package_sha256"]
# Cross-anchor: source_package_sha256 == subject[0].sha256
assert d["source_package_sha256"] == m["subjects"][0]["sha256"], \
    "decision report's source_package_sha256 must equal subject[0].sha256"
# Recompute package SHA-256 on disk and confirm.
h = hashlib.sha256()
with open(pp, "rb") as f:
    for c in iter(lambda: f.read(65536), b""): h.update(c)
assert d["source_package_sha256"] == h.hexdigest(), \
    "decision report's source_package_sha256 must equal on-disk package SHA-256"
# decision_count == len(decision_rows)
assert d["decision_count"] == len(d["decision_rows"]) == 5, (d["decision_count"], len(d["decision_rows"]))
# row shape
for i, row in enumerate(d["decision_rows"]):
    for field in ("row_id", "source_decision_index", "decision_id",
                  "scenario_type", "decision_status", "decision_trigger",
                  "recorded_at", "decision_subject", "policy_binding",
                  "registry_binding", "action_scope",
                  "scenario_path_summary", "decision_fingerprint"):
        assert field in row, (i, field)
    assert row["source_decision_index"] == i, (i, row["source_decision_index"])
    assert bare_hex.match(row["decision_fingerprint"]), row["decision_fingerprint"]
    # scenario_path_summary == <scenario_type>:<decision_status>
    assert row["scenario_path_summary"] == f"{row['scenario_type']}:{row['decision_status']}", row["scenario_path_summary"]
# coverage_summary keys
cs = d["coverage_summary"]
for field in ("decision_count", "scenario_types_present",
              "decision_statuses_present", "protected_actions_present",
              "policy_decisions_present", "registry_roles_present",
              "aggregate_row_fingerprint"):
    assert field in cs, field
assert cs["decision_count"] == 5
assert bare_hex.match(cs["aggregate_row_fingerprint"])
# scope_limitations and non_claims must be non-empty
assert isinstance(d["scope_limitations"], list) and d["scope_limitations"]
assert isinstance(d["non_claims"], list) and d["non_claims"]
EOF

# ---------------------------------------------------------------------------
# Step 6 (PP6): inline identifier distinctness re-check at file level.
# ---------------------------------------------------------------------------
echo "[step6] PP6 identifier distinctness conformance_report_id != decision_report_id"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$CONFORMANCE_REL_FILE" "$PRISTINE/$DECISION_REL_FILE" <<'EOF'
import json, sys
mp, cp, dp = sys.argv[1], sys.argv[2], sys.argv[3]
m = json.loads(open(mp).read())
c = json.loads(open(cp).read())
d = json.loads(open(dp).read())
# Conformance report cross-anchors to top-level report_id (v0.4.0-shaped).
assert c["report_id"] == m["conformance_report_id"], \
    f"conformance.report_id ({c['report_id']!r}) != manifest.conformance_report_id ({m['conformance_report_id']!r})"
# Decision report cross-anchors to top-level decision_report_id (v0.4.1).
assert d["decision_report_id"] == m["decision_report_id"], \
    f"decision.decision_report_id ({d['decision_report_id']!r}) != manifest.decision_report_id ({m['decision_report_id']!r})"
assert m["conformance_report_id"] != m["decision_report_id"], \
    "manifest conformance_report_id and decision_report_id must differ"
EOF

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# v0.4.1 uses BARE lowercase hex SHA-256 in manifest subject sha256
# fields. Rehash subject [idx] (0, 1, or 2) after a body mutation.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "gold-decision-report-package-manifest.json")
m = json.loads(open(mp).read())
sp = os.path.join(pkg, m["subjects"][idx]["path"])
h = hashlib.sha256()
with open(sp, "rb") as f:
    for c in iter(lambda: f.read(65536), b""):
        h.update(c)
m["subjects"][idx]["sha256"] = h.hexdigest()
m["subjects"][idx]["size_bytes"] = os.path.getsize(sp)
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the gold package body via a Python snippet operating on dict `pkg`.
# v0.4.0-shaped fixtures use indent=2 + trailing newline; preserve that.
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
open(pp, "w").write(json.dumps(body, indent=2) + "\n")
EOF
}

# Edit the outer manifest via a Python snippet operating on dict `m`.
# v0.4.1 manifest serialization: sort_keys + compact separators + trailing newline.
# Does NOT recompute subject hashes by itself.
edit_manifest() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
mp = os.path.join(pkg, "gold-decision-report-package-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the bundled conformance report. v0.4.1 conformance report
# serialization: sort_keys + compact separators + trailing newline.
edit_conformance() {
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

# Edit the bundled decision report. v0.4.1 decision report
# serialization: sort_keys + compact separators + trailing newline.
edit_decision() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
dp = os.path.join(pkg, "gold-governed-reliance-decision-report.json")
d = json.loads(open(dp).read())
exec(expr, {"d": d, "json": json})
open(dp, "w").write(json.dumps(d, sort_keys=True, separators=(",", ":")) + "\n")
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
  # Verifier must NEVER emit an INFRA: diagnostic on a real package
  # defect (INFRA: is reserved for environment failures like a missing
  # co-located v0.4.0 verifier).
  if echo "$out" | grep -q "^INFRA:"; then
    echo "FAIL: $label: verifier emitted INFRA: on a package defect"
    echo "$out"
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

echo "[cases] 29 canonical + 15 duplicate + 1 supplemental + 6 runner-only + rel01 + rel02 + TG1 + SS"

# ===========================================================================
# Canonical verifier mutation cases (29 = 24 inherited + 5 v0.4.1).
# Cases 01..24 mutate the v0.4.0-shaped package body subject [0] and
# rely on the v0.4.1 verifier's subprocess delegation to the unchanged
# v0.4.0 verifier to relay the inherited reason verbatim.
# ===========================================================================

# --- case01: gold_manifest_invalid (v0.4.1 manifest document_type) ----------
# This R01 fold is emitted by the v0.4.1 verifier's own Phase 1 manifest
# integrity check BEFORE the subprocess delegation step.
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:gold_manifest_invalid" "$T" "gold_manifest_invalid"

# --- case02: gold_package_not_object (relayed from v0.4.0) ------------------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$PACKAGE_REL', 'w') as f:
    f.write(json.dumps([1,2,3], indent=2) + '\n')
"
rehash_subject "$T" 0
expect_verifier_fail "case02:gold_package_not_object" "$T" "gold_package_not_object"

# --- case03: gold_package_schema_invalid (relayed from v0.4.0) --------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["document_type"] = "wrong"'
rehash_subject "$T" 0
expect_verifier_fail "case03:gold_package_schema_invalid" "$T" "gold_package_schema_invalid"

# --- case04: gold_profile_unsupported (relayed from v0.4.0) -----------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["profile"] = "some.other.profile"'
rehash_subject "$T" 0
expect_verifier_fail "case04:gold_profile_unsupported" "$T" "gold_profile_unsupported"

# --- case05: gold_package_identity_invalid (relayed from v0.4.0) ------------
# Package_id must remain consistent across body, manifest, decision report,
# and synthesized v0.4.0 manifest; grammar violation on all four reaches R05.
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["package_id"] = "BadID"'
edit_manifest "$T" 'm["package_id"] = "BadID"'
edit_decision "$T" 'd["package_id"] = "BadID"'
rehash_subject "$T" 0
rehash_subject "$T" 2
expect_verifier_fail "case05:gold_package_identity_invalid" "$T" "gold_package_identity_invalid"

# --- case06: silver_verification_input_invalid (relayed) --------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["silver_verification"]["input_type"] = "not_a_type"'
rehash_subject "$T" 0
expect_verifier_fail "case06:silver_verification_input_invalid" "$T" "silver_verification_input_invalid"

# --- case07: silver_handoff_input_invalid (relayed) -------------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["silver_handoff"].pop("expected_handoff_posture")'
rehash_subject "$T" 0
expect_verifier_fail "case07:silver_handoff_input_invalid" "$T" "silver_handoff_input_invalid"

# --- case08: policy_pack_input_invalid (relayed) ----------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["policy_pack"].pop("policy_pack_version")'
rehash_subject "$T" 0
expect_verifier_fail "case08:policy_pack_input_invalid" "$T" "policy_pack_input_invalid"

# --- case09: registry_lite_input_invalid (relayed) --------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["registry_lite"]["registry_id"] = "BadID"'
rehash_subject "$T" 0
expect_verifier_fail "case09:registry_lite_input_invalid" "$T" "registry_lite_input_invalid"

# --- case10: control_crosswalk_input_invalid (relayed) ----------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["inputs"]["control_crosswalk"].pop("control_pack_id")'
rehash_subject "$T" 0
expect_verifier_fail "case10:control_crosswalk_input_invalid" "$T" "control_crosswalk_input_invalid"

# --- case11: governed_decision_set_invalid (relayed) ------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case11:governed_decision_set_invalid" "$T" "governed_decision_set_invalid"

# --- case12: governed_decision_entry_invalid (relayed) ----------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0].pop("decision_id")'
rehash_subject "$T" 0
expect_verifier_fail "case12:governed_decision_entry_invalid" "$T" "governed_decision_entry_invalid"

# --- case13: decision_subject_binding_invalid (relayed) ---------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["decision_subject"]["subject_ref"] = "unknown-subject-ref-001"'
rehash_subject "$T" 0
expect_verifier_fail "case13:decision_subject_binding_invalid" "$T" "decision_subject_binding_invalid"

# --- case14: decision_policy_binding_invalid (relayed) ----------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["policy_binding"]["policy_pack_id"] = "policy-pack-mismatch-001"'
rehash_subject "$T" 0
expect_verifier_fail "case14:decision_policy_binding_invalid" "$T" "decision_policy_binding_invalid"

# --- case15: decision_registry_binding_invalid (relayed) --------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["registry_binding"]["decision_authority_role"] = "not_a_role"'
rehash_subject "$T" 0
expect_verifier_fail "case15:decision_registry_binding_invalid" "$T" "decision_registry_binding_invalid"

# --- case16: decision_action_scope_invalid (relayed) ------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["action_scope"]["protected_action_id"] = "not_a_protected_action"'
rehash_subject "$T" 0
expect_verifier_fail "case16:decision_action_scope_invalid" "$T" "decision_action_scope_invalid"

# --- case17: decision_status_invalid (relayed) ------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["decision_status"] = "maybe"'
rehash_subject "$T" 0
expect_verifier_fail "case17:decision_status_invalid" "$T" "decision_status_invalid"

# --- case18: acceptance_path_invalid (relayed) ------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["scenario_specific_state"]["acceptance_record_ref"] = ""'
rehash_subject "$T" 0
expect_verifier_fail "case18:acceptance_path_invalid" "$T" "acceptance_path_invalid"

# --- case19: rejection_path_invalid (relayed) -------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][1]["scenario_specific_state"]["silver_verification_passing"] = False'
rehash_subject "$T" 0
expect_verifier_fail "case19:rejection_path_invalid" "$T" "rejection_path_invalid"

# --- case20: challenge_path_invalid (relayed) -------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][2]["scenario_specific_state"]["challenge_state"] = "not_a_state"'
rehash_subject "$T" 0
expect_verifier_fail "case20:challenge_path_invalid" "$T" "challenge_path_invalid"

# --- case21: withdrawal_path_invalid (relayed) ------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][3]["scenario_specific_state"]["withdrawal_trigger"] = "random"'
rehash_subject "$T" 0
expect_verifier_fail "case21:withdrawal_path_invalid" "$T" "withdrawal_path_invalid"

# --- case22: supersession_path_invalid (relayed) ----------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][4]["scenario_specific_state"]["prior_decision_id"] = "nonexistent"'
rehash_subject "$T" 0
expect_verifier_fail "case22:supersession_path_invalid" "$T" "supersession_path_invalid"

# --- case23: non_claims_missing (relayed) -----------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["non_claims"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case23:non_claims_missing" "$T" "non_claims_missing"

# --- case24: prohibited_gold_claim_present (relayed) ------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["relying_party"]["display_name"] = "Demo Local Relying Party (full Gold certified)"'
rehash_subject "$T" 0
expect_verifier_fail "case24:prohibited_gold_claim_present" "$T" "prohibited_gold_claim_present"

# --- case25: gold_decision_report_not_object --------------------------------
# Replace the bundled decision report with a top-level JSON array.
T="$WORK/c25"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$DECISION_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 2
expect_verifier_fail "case25:gold_decision_report_not_object" "$T" "gold_decision_report_not_object"

# --- case26: gold_decision_report_schema_invalid ----------------------------
# Mutate the decision report's document_type so schema check fires.
T="$WORK/c26"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["document_type"] = "wrong"'
rehash_subject "$T" 2
expect_verifier_fail "case26:gold_decision_report_schema_invalid" "$T" "gold_decision_report_schema_invalid"

# --- case27: gold_decision_report_binding_invalid ---------------------------
# Mutate the decision report's package_id so it disagrees with the
# manifest's package_id (binding cross-anchor).
T="$WORK/c27"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 2
expect_verifier_fail "case27:gold_decision_report_binding_invalid" "$T" "gold_decision_report_binding_invalid"

# --- case28: gold_decision_report_projection_invalid ------------------------
# Mutate decision_rows[0]["decision_status"] so the re-derived row
# disagrees with the bundled row. Per the R28/R29 split, row drift
# routes to R28, NOT R29 (which is reserved for coverage_summary drift).
T="$WORK/c28"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["decision_rows"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 2
expect_verifier_fail "case28:gold_decision_report_projection_invalid" "$T" "gold_decision_report_projection_invalid"

# --- case29: gold_decision_report_summary_invalid ---------------------------
# Mutate coverage_summary.decision_count so the derived summary disagrees.
# Per the R28/R29 split, coverage_summary drift routes to R29.
T="$WORK/c29"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["coverage_summary"]["decision_count"] = 42'
rehash_subject "$T" 2
expect_verifier_fail "case29:gold_decision_report_summary_invalid" "$T" "gold_decision_report_summary_invalid"

# ===========================================================================
# Duplicate gold_manifest_invalid cases (16; all route to that reason).
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

# --- dup05: subject[2] path absolute ----------------------------------------
T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][2]["path"] = "/etc/shells"'
expect_verifier_fail "dup05:subject_2_path_absolute" "$T" "gold_manifest_invalid"

# --- dup06: subject[2] path traversal ---------------------------------------
T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][2]["path"] = "../escape-decision.json"'
expect_verifier_fail "dup06:subject_2_path_traversal" "$T" "gold_manifest_invalid"

# --- dup07: subject[0] file missing on disk ---------------------------------
T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
rm "$T/$PACKAGE_REL"
expect_verifier_fail "dup07:subject_0_file_absent" "$T" "gold_manifest_invalid"

# --- dup08: subject[0] size_bytes mismatch ----------------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["size_bytes"] = 0'
expect_verifier_fail "dup08:subject_0_size_mismatch" "$T" "gold_manifest_invalid"

# --- dup09: subject[0] sha256 mismatch (bare hex) ---------------------------
T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["sha256"] = "f" * 64'
expect_verifier_fail "dup09:subject_0_sha_mismatch" "$T" "gold_manifest_invalid"

# --- dup10: wrong subject count (4 entries) ---------------------------------
T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"0"*64,"size_bytes":0})'
expect_verifier_fail "dup10:wrong_subject_count" "$T" "gold_manifest_invalid"

# --- dup11: subject[0] role wrong -------------------------------------------
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["role"] = "wrong_role"'
expect_verifier_fail "dup11:subject_0_role_wrong" "$T" "gold_manifest_invalid"

# --- dup12: subject[2] role wrong -------------------------------------------
T="$WORK/d12"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][2]["role"] = "wrong_role"'
expect_verifier_fail "dup12:subject_2_role_wrong" "$T" "gold_manifest_invalid"

# --- dup13: manifest package_id cross-anchor mismatch -----------------------
T="$WORK/d13"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["package_id"] = "proofrail-gold-governed-reliance-anchor-mismatch-001"'
expect_verifier_fail "dup13:package_id_anchor_mismatch" "$T" "gold_manifest_invalid"

# --- dup14: manifest governed_reliance_demo_id cross-anchor mismatch --------
T="$WORK/d14"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["governed_reliance_demo_id"] = "gold-governed-reliance-demo-mismatch-001"'
expect_verifier_fail "dup14:demo_id_anchor_mismatch" "$T" "gold_manifest_invalid"

# --- dup15: decision_report_id == conformance_report_id (collision) ---------
# Per reviewer note: identifier collision is a manifest-level cross-anchor
# defect; folds to gold_manifest_invalid; no new R-code introduced.
T="$WORK/d15"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["decision_report_id"] = m["conformance_report_id"]'
expect_verifier_fail "dup15:identifier_collision" "$T" "gold_manifest_invalid"

# ===========================================================================
# Supplemental decision-report-binding case (1 exercise; routes to R27).
# Reported separately from the duplicate manifest-invalid set above because
# source_package_sha256 lives in the decision report, not in the manifest.
# ===========================================================================

# --- sup01: decision report source_package_sha256 != subject[0].sha256 ------
# Mutate the decision report's source_package_sha256 cross-anchor field
# (bare hex). source_package_sha256 lives in the decision report (not in the
# manifest), so this is a decision-report-binding defect and the verifier
# correctly emits R27 (gold_decision_report_binding_invalid). sup01 thus
# provides supplemental coverage for R27 alongside case27 (which mutates the
# package_id binding instead of the source_package_sha256 binding).
T="$WORK/s01"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["source_package_sha256"] = "0" * 64'
rehash_subject "$T" 2
expect_verifier_fail "sup01:source_package_sha_anchor_mismatch" "$T" "gold_decision_report_binding_invalid"

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
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
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
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO2_OUT" \
    --force

# --- ro2b: runner_input_path_forbidden (parent-traversal) -------------------
RO2B_OUT="$WORK/ro2b-out"
expect_runner_fail "ro2b:runner_input_path_forbidden_traversal" \
  "runner_input_path_forbidden" \
  "$RO2B_OUT" \
  "$RUNNER" \
    --input-package "../leak.json" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
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
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
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
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="fixtures/gold-decision-report-hardening-v0.4.1/_test_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --input-package "$BAD_INPUT_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
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
# Runner-relay-of-verifier (rel01). The runner relays the v0.4.1
# verifier's OWN reason UNCHANGED; it does NOT wrap it in a sixth
# runner-only code. Staging directory must be cleaned up and destination
# must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
REL_INPUT_REL="fixtures/gold-decision-report-hardening-v0.4.1/_test_relay_bad.json"
REL_INPUT_ABS="$REPO_ROOT/$REL_INPUT_REL"
# A v0.4.0-shaped package body with wrong document_type. The runner
# completes Phase A (valid JSON, valid path), then derives a 3-subject
# package. --self-validate runs the v0.4.1 verifier against the staging
# directory; the v0.4.1 verifier delegates inherited checks to the
# v0.4.0 verifier which emits gold_package_schema_invalid; the v0.4.1
# verifier relays that reason verbatim; the runner relays the v0.4.1
# verifier's exit code verbatim.
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
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$REL_OUT" \
  --force \
  --self-validate 2>&1)"
rel_rc=$?
set -e
rm -f "$REL_INPUT_ABS"

if [ "$rel_rc" -eq 0 ]; then
  echo "FAIL: rel01: expected nonzero exit (verifier relay), got 0"
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
# Sentinel deliberately non-reason-shaped so the taxonomy gate does not
# treat it as a reason-like token.
if echo "$rel_out" | grep -qE "^FAIL: runner_wrapper_negative_assertion:"; then
  echo "FAIL: rel01: runner introduced a sixth wrapper code"
  echo "$rel_out"
  exit 1
fi
# No INFRA: line on a real package defect.
if echo "$rel_out" | grep -q "^INFRA:"; then
  echo "FAIL: rel01: runner/verifier emitted INFRA: on a real package defect"
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
# Verifier-relay-of-inherited (rel02). The v0.4.1 verifier delegates
# inherited 24 checks to the co-located v0.4.0 verifier via subprocess.
# Mutating the package body to trigger an inherited non-R01 reason must
# surface that reason verbatim with no v0.4.1 wrapping. This is a
# dedicated negative-assertion against any future drift toward
# wrapping inherited reasons in a v0.4.1-specific code.
# ===========================================================================

T="$WORK/rel02"
fresh_copy "$PRISTINE" "$T"
# Mutate subject[0] document_type; rehash subject[0] so the v0.4.1
# verifier Phase 1 manifest integrity passes; the subprocess delegation
# step then emits gold_package_schema_invalid via the v0.4.0 verifier.
edit_package "$T" 'pkg["document_type"] = "wrong"'
rehash_subject "$T" 0

set +e
rel2_out="$(python3 "$VERIFIER" --manifest "$T/$MANIFEST_REL_FILE" 2>&1)"
rel2_rc=$?
set -e
if [ "$rel2_rc" -eq 0 ]; then
  echo "FAIL: rel02: expected nonzero exit, got 0"
  echo "$rel2_out"
  exit 1
fi
# Must surface the inherited reason verbatim.
if ! echo "$rel2_out" | grep -qE "^FAIL: gold_package_schema_invalid:"; then
  echo "FAIL: rel02: expected inherited reason gold_package_schema_invalid"
  echo "----- v0.4.1 verifier output -----"
  echo "$rel2_out"
  echo "----------------------------------"
  exit 1
fi
# Must NOT be wrapped in any v0.4.1-introduced reason.
for v041_only in gold_decision_report_not_object \
                 gold_decision_report_schema_invalid \
                 gold_decision_report_binding_invalid \
                 gold_decision_report_projection_invalid \
                 gold_decision_report_summary_invalid; do
  if echo "$rel2_out" | grep -qE "^FAIL: ${v041_only}:"; then
    echo "FAIL: rel02: v0.4.1 verifier wrapped inherited reason in $v041_only"
    echo "$rel2_out"
    exit 1
  fi
done
# Must NOT wrap as a runner-only refusal (verifier never emits those).
for ronly in runner_input_path_missing runner_input_path_forbidden \
             runner_input_file_missing runner_input_read_failed \
             runner_input_json_invalid; do
  if echo "$rel2_out" | grep -qE "^FAIL: ${ronly}:"; then
    echo "FAIL: rel02: v0.4.1 verifier emitted runner-only refusal $ronly"
    echo "$rel2_out"
    exit 1
  fi
done
# Must NOT emit any INFRA: diagnostic on a real package defect.
if echo "$rel2_out" | grep -q "^INFRA:"; then
  echo "FAIL: rel02: v0.4.1 verifier emitted INFRA: on a real package defect"
  echo "$rel2_out"
  exit 1
fi
echo "  rel02:verifier_relay_of_inherited_failure: ok (gold_package_schema_invalid relayed unchanged)"

# ===========================================================================
# Taxonomy gate (TG1).
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.4.1-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

# 29 approved verifier reasons (24 inherited + 5 v0.4.1).
APPROVED_VERIFIER = {
    # inherited from v0.4.0:
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
    # introduced by v0.4.1:
    "gold_decision_report_not_object",
    "gold_decision_report_schema_invalid",
    "gold_decision_report_binding_invalid",
    "gold_decision_report_projection_invalid",
    "gold_decision_report_summary_invalid",
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# Strict no-additions discipline. The negative-assertion sentinels in
# this test (runner_wrapper_negative_assertion, subject_0_*, etc.) are
# deliberately non-reason-shaped under REASON_FILTER and therefore
# never enter the scanner's reason-like bucket.
#
# TG1 ALLOWLIST DISCIPLINE
# ------------------------
# The allowlist below is intentionally CLOSED and TINY. Each entry must be
# an EXACT data-field name from the v0.4.1 decision report schema that
# coincidentally trips the REASON_FILTER suffix (here: the `_present`
# suffix used to denote enum-presence indicators inside coverage_summary).
# These are NOT public verifier reasons, NOT runner-only refusal codes,
# and NOT semantic synonyms of either. They are LITERAL JSON FIELD NAMES.
#
# Disallowed in this allowlist:
#   - Any token that names or paraphrases a failure mode.
#   - Any broad regex / pattern allowance.
#   - Any token used purely in prose, comments, or non-schema contexts.
#   - Any wildcard or family-shaped entry (e.g., `*_present`).
#
# Adding a new entry requires (a) the token is a verbatim data-field name
# already present in the v0.4.1 decision report schema, and (b) a comment
# pointing at the schema clause that defines it.
ALLOWED_NON_REASON_TOKENS: set[str] = {
    # Coverage-summary enum-presence field names from the v0.4.1 decision
    # report schema (schemas/gold-governed-reliance-decision-report-v0.1.0.md,
    # `coverage_summary` clause). Each is the literal JSON key under
    # `coverage_summary` carrying a deduplicated, sorted list of the
    # enum values exercised across `decision_rows[]`. They terminate in
    # `_present`, so REASON_FILTER admits them, but they are data-field
    # names, NOT public reasons.
    "decision_statuses_present",
    "policy_decisions_present",
    "protected_actions_present",
    "registry_roles_present",
    "scenario_types_present",
}

APPROVED = APPROVED_VERIFIER | APPROVED_RUNNER | ALLOWED_NON_REASON_TOKENS

TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
REASON_FILTER = re.compile(
    r"(?:_(?:invalid|missing|unsupported|present|forbidden|failed))$|(?:_not_object)$"
)

# Explicit deny-list patterns for environmental/wrapper escape tokens.
# Per reviewer note 3B: future drift toward wrapping environment
# failures (missing co-located v0.4.0 verifier, subprocess crashes, etc.)
# as public reasons must trip the gate. This deny-list is checked
# AGAINST EVERY reason-shaped token, not just unknown ones, so that an
# environmental wrapper can never be smuggled in by also adding it to
# the APPROVED set. The substring-based check intentionally matches
# common wrapper-shaped fragments.
# Substrings are spelled with explicit string concatenation so that the
# gate's own source does NOT contain a whole reason-shaped deny token
# (otherwise the deny-list literal would self-trip the gate when it
# scans this test file). The constituent halves never satisfy the
# REASON_FILTER suffix on their own.
DENY_SUBSTRINGS = (
    "v040" + "_verifier",
    "v041" + "_verifier",
    "sub" + "process_",
    "_sub" + "process",
    "inherited" + "_verifier_",
    "tool" + "_unavailable",
    "environment" + "_failure",
    "infra" + "_failure",
    "delegation" + "_failure",
)

# Self-check: every approved reason satisfies the test's own reason-like
# filter and does NOT collide with the deny-list.
for r in APPROVED_VERIFIER | APPROVED_RUNNER:
    if not TOKEN_RE.fullmatch(r) or not REASON_FILTER.search(r):
        print(
            f"FAIL: TG1: approved reason {r!r} does not satisfy "
            f"the test's own reason-like filter; gate is unsafe",
            file=sys.stderr,
        )
        sys.exit(1)
    for sub in DENY_SUBSTRINGS:
        if sub in r:
            print(
                f"FAIL: TG1: approved reason {r!r} collides with deny "
                f"substring {sub!r}",
                file=sys.stderr,
            )
            sys.exit(1)

V0_4_1_FILES = [
    "schemas/gold-governed-reliance-decision-report-v0.1.0.md",
    "schemas/gold-decision-report-package-manifest-v0.1.0.md",
    "fixtures/gold-decision-report-hardening-v0.4.1/README.md",
    "tools/gold/build_gold_decision_report_hardening_v0_1_0.py",
    "tools/gold/verify_gold_decision_report_hardening_v0_1_0.py",
    "tests/test_gold_decision_report_hardening_v0_4_1.sh",
    "docs/gold/gold-decision-report-hardening-v0.4.1.md",
    "demos/gold-demo-002-decision-report-hardening/README.md",
    "demos/gold-demo-002-decision-report-hardening/demo-walkthrough.md",
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

def collect_deny_hits(label: str, text: str) -> list[str]:
    """Find any reason-shaped token that contains a deny-list substring.

    This catches the failure mode where someone adds an environmental
    wrapper token to the APPROVED set AND uses it in source; the
    self-check above prevents the APPROVED collision; this check
    catches usages in source that bypassed APPROVED."""
    hits: list[str] = []
    seen: set[str] = set()
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        if tok in seen:
            continue
        seen.add(tok)
        if not REASON_FILTER.search(tok):
            continue
        for sub in DENY_SUBSTRINGS:
            if sub in tok:
                hits.append(tok)
                break
    return hits

errors: list[str] = []

for rel in V0_4_1_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.4.1-owned file: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for tok in sorted(set(collect_unapproved_tokens(rel, text))):
        errors.append(f"{rel}: unapproved reason-like token: {tok}")
    for tok in sorted(set(collect_deny_hits(rel, text))):
        errors.append(
            f"{rel}: reason-like token matches environmental wrapper "
            f"deny-list: {tok}"
        )

if errors:
    print(
        "FAIL: TG1: unapproved or denied reason-like tokens in "
        "v0.4.1-owned surface area",
        file=sys.stderr,
    )
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)

print("  TG1:taxonomy_gate: ok (no unapproved or denied reason-like tokens)")
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
echo "PASS: tests/test_gold_decision_report_hardening_v0_4_1.sh"
echo "  61/61 exercises:"
echo "    - 6 positive-path (PP1..PP6)"
echo "    - 29 canonical verifier reasons (case01..case29)"
echo "        24 inherited via subprocess delegation to v0.4.0"
echo "        5  v0.4.1-introduced (R25..R29)"
echo "    - 15 duplicate / secondary gold_manifest_invalid (dup01..dup15)"
echo "    - 1 supplemental decision-report binding case (sup01;"
echo "        folds to gold_decision_report_binding_invalid)"
echo "    - 6 runner-only refusals (ro1, ro2, ro2b, ro3..ro5)"
echo "    - 1 runner-relay-of-verifier (rel01)"
echo "    - 1 verifier-relay-of-inherited (rel02)"
echo "    - 1 taxonomy gate with environmental-wrapper deny-list (TG1)"
echo "    - 1 scoped sha256 snapshot (SS)"
