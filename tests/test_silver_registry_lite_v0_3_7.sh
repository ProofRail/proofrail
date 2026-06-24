#!/usr/bin/env bash
# tests/test_silver_registry_lite_v0_3_7.sh
#
# Regression test for the ProofRail Silver v0.3.7 Registry Lite package.
#
# Numbered exercises (48 total):
#
#   Positive-path (4):
#     PP1   Pristine end-to-end build with --self-validate
#     PP2   Pristine independent verifier pass on the package
#     PP3   Inline structural cross-check of manifest subject layout
#     PP4   Inline structural cross-check of bundled conformance report
#
#   Canonical verifier mutation cases (24; one per approved reason,
#   in CHECKS_ORDER):
#     case01  registry_manifest_invalid               (manifest document_type)
#     case02  registry_not_object                     (registry body is JSON array)
#     case03  registry_schema_invalid                 (registry document_type)
#     case04  registry_profile_unsupported
#     case05  registry_identity_invalid               (registry_id grammar)
#     case06  registry_authority_invalid              (identity_id removed)
#     case07  registry_entity_set_invalid             (entities = [])
#     case08  registry_entity_entry_invalid           (display_label removed)
#     case09  registry_entity_identifier_invalid      (entity_id grammar)
#     case10  registry_role_invalid                   (role not in closed set)
#     case11  registry_status_invalid                 (status not in closed set)
#     case12  registry_effective_period_invalid       (starts_at > ends_at)
#     case13  registry_key_reference_invalid          (algorithm not in closed set)
#     case14  registry_key_binding_invalid            (key_id unknown)
#     case15  issuer_entry_invalid                    (issuer.issuer_scope removed)
#     case16  verifier_entry_invalid                  (verifier.verifier_profiles removed)
#     case17  relying_party_entry_invalid             (relying_party.reliance_scope removed)
#     case18  policy_authority_entry_invalid          (policy_authority.policy_scope removed)
#     case19  revocation_source_entry_invalid         (revocation_source.source_type removed)
#     case20  protected_action_authority_entry_invalid (protected_action_scope removed)
#     case21  trust_relationship_invalid              (to_entity_id unknown)
#     case22  version_binding_invalid                 (upstream_version not in closed set)
#     case23  non_claims_missing                      (non_claims = [])
#     case24  prohibited_registry_claim_present       (display_name carries "production PKI")
#
#   Duplicate manifest-invalid cases (11; secondary manifest defects
#   that all route to registry_manifest_invalid; reported separately
#   so the 24 canonical cases above remain exactly one-per-reason):
#     dup01   subject[0] path absolute
#     dup02   subject[0] path traversal
#     dup03   subject[1] path absolute
#     dup04   subject[1] path traversal
#     dup05   subject[0] file missing on disk
#     dup06   subject[0] size_bytes mismatch
#     dup07   subject[0] sha256 mismatch
#     dup08   wrong subject count (3 instead of 2)
#     dup09   subject[0] role wrong
#     dup10   manifest registry_id cross-anchor mismatch
#     dup11   conformance report disagreement on otherwise-valid registry
#             (non-masking post-structural check)
#
#   Runner-only refusal cases (6; preflight only):
#     ro1     runner_input_path_missing
#     ro2     runner_input_path_forbidden       (absolute path)
#     ro2b    runner_input_path_forbidden       (parent-traversal path)
#     ro3     runner_input_file_missing
#     ro4     runner_input_read_failed          (directory, portable)
#     ro5     runner_input_json_invalid
#
#   Runner-relay-of-verifier (1; separate from the 6 runner-only
#   refusal exercises covering 5 distinct runner-only reasons):
#     rel01   --self-validate on a structurally bad registry relays the
#             verifier's own reason UNCHANGED, NOT wrapped in a sixth
#             runner-only code; staging directory is removed.
#
#   Taxonomy gate (1):
#     TG1     Scan v0.3.7-owned files and v0.3.7-anchored sections of
#             6 cross-version docs for reason-like tokens; assert every
#             such token is in the approved verifier-or-runner
#             allowlist defined in this test.
#
#   Scoped sha256 snapshot (1):
#     SS      scoped sha256 snapshot of committed v0.3.7 source paths
#             BEFORE and AFTER all cases must be identical.
#
# Coverage summary:
#   * 24/24 stable verifier failure reasons covered by canonical cases.
#     No reason is OR-accepted; each canonical case asserts its exact
#     stable reason.
#   * 11 additional manifest-invalid defects are listed as dup01..dup11
#     so the 24 canonical reason map remains one-per-reason; dup11 is
#     specifically the NON-MASKING post-structural conformance-report
#     mismatch on an otherwise-valid registry.
#   * 5/5 runner-only refusal codes covered. runner_input_path_forbidden
#     is exercised TWICE (ro2 absolute, ro2b parent-traversal) to assert
#     both branches of the runner's path-forbidden preflight emit the
#     same single reason. The runner-relay-of-verifier behavior is
#     exercised separately as rel01 to assert no sixth code is
#     introduced.
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

RUNNER="$REPO_ROOT/tools/silver/build_silver_registry_lite_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/silver/verify_silver_registry_lite_v0_1_0.py"
REGISTRY_FIX_REL="fixtures/silver-registry-lite-v0.3.7/registry-lite.json"

WORK="$(mktemp -d -t proofrail-v0.3.7-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-08-15T00:30:00Z"
MANIFEST_ID="silver-registry-lite-manifest-v0.3.7-test-001"
REPORT_ID="silver-registry-lite-conformance-report-v0.3.7-test-001"

REGISTRY_REL="registry-lite.json"
REPORT_REL_FILE="silver-registry-lite-conformance-report.json"
MANIFEST_REL_FILE="silver-registry-lite-manifest.json"

# --- Scoped sha256 snapshot of committed v0.3.7 source paths (BEFORE) ---
SCOPED_FILES=(
  "schemas/silver-registry-lite-v0.1.0.md"
  "schemas/silver-registry-lite-manifest-v0.1.0.md"
  "schemas/silver-registry-lite-conformance-report-v0.1.0.md"
  "fixtures/silver-registry-lite-v0.3.7/README.md"
  "fixtures/silver-registry-lite-v0.3.7/registry-lite.json"
  "fixtures/silver-registry-lite-v0.3.7/registry-lite-with-trust-relationships.json"
  "fixtures/silver-registry-lite-v0.3.7/registry-lite-with-revocation-source.json"
  "tools/silver/build_silver_registry_lite_v0_1_0.py"
  "tools/silver/verify_silver_registry_lite_v0_1_0.py"
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
echo "[step1] pristine registry lite build with --self-validate"
python3 "$RUNNER" \
  --input-registry "$REGISTRY_FIX_REL" \
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
assert m["document_type"] == "proofrail.silver.registry_lite_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "silver.registry_lite.v0.3.7"
assert m["hash_algorithm"] == "sha256"
assert isinstance(m["manifest_id"], str) and m["manifest_id"]
assert isinstance(m["registry_id"], str) and m["registry_id"]
assert len(m["subjects"]) == 2
expected = [
  ("registry-lite.json", "registry_lite"),
  ("silver-registry-lite-conformance-report.json", "conformance_report"),
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
assert r["document_type"] == "proofrail.silver.registry_lite_conformance_report"
assert r["schema_version"] == "v0.1.0"
assert r["proofrail_release"] == "silver.registry_lite.v0.3.7"
assert isinstance(r["report_id"], str) and r["report_id"]
binding = r["registry_binding"]
assert isinstance(binding["registry_id"], str) and binding["registry_id"]
assert binding["profile"] == "silver.registry_lite.v0.3.7"
assert isinstance(binding["registry_sha256"], str) and len(binding["registry_sha256"]) == 64
summary = r["summary"]
assert summary["checks_total"] == 24
assert summary["checks_passed"] == 24
assert summary["checks_not_passing"] == 0
assert isinstance(r["checks"], list)
assert len(r["checks"]) == 24, len(r["checks"])
EXPECTED = [
  "registry_manifest_invalid",
  "registry_not_object",
  "registry_schema_invalid",
  "registry_profile_unsupported",
  "registry_identity_invalid",
  "registry_authority_invalid",
  "registry_entity_set_invalid",
  "registry_entity_entry_invalid",
  "registry_entity_identifier_invalid",
  "registry_role_invalid",
  "registry_status_invalid",
  "registry_effective_period_invalid",
  "registry_key_reference_invalid",
  "registry_key_binding_invalid",
  "issuer_entry_invalid",
  "verifier_entry_invalid",
  "relying_party_entry_invalid",
  "policy_authority_entry_invalid",
  "revocation_source_entry_invalid",
  "protected_action_authority_entry_invalid",
  "trust_relationship_invalid",
  "version_binding_invalid",
  "non_claims_missing",
  "prohibited_registry_claim_present",
]
for i, reason in enumerate(EXPECTED):
    entry = r["checks"][i]
    assert entry["reason"] == reason, (i, entry["reason"], reason)
    assert entry["status"] == "pass", (i, entry["status"])
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
mp = os.path.join(pkg, "silver-registry-lite-manifest.json")
m = json.loads(open(mp).read())
sp = os.path.join(pkg, m["subjects"][idx]["path"])
h = hashlib.sha256()
with open(sp, "rb") as f:
    for c in iter(lambda: f.read(65536), b""):
        h.update(c)
m["subjects"][idx]["sha256"] = "sha256:" + h.hexdigest()
m["subjects"][idx]["size_bytes"] = os.path.getsize(sp)
# Use canonical form to preserve the runner's exact byte image.
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the registry-lite JSON in a staging package via a Python snippet.
# Caller supplies a Python program operating on the dict `reg`.
edit_registry() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
rp = os.path.join(pkg, "registry-lite.json")
reg = json.loads(open(rp).read())
exec(expr, {"reg": reg, "json": json})
# Preserve the input fixture's text format: 2-space indent +
# trailing newline. The verifier doesn't care about key order in the
# registry, only that its bundled report byte-image equals re-derivation.
open(rp, "w").write(json.dumps(reg, indent=2) + "\n")
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
mp = os.path.join(pkg, "silver-registry-lite-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
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
rp = os.path.join(pkg, "silver-registry-lite-conformance-report.json")
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

echo "[cases] 24 canonical + 11 duplicate + 6 runner-only refusal exercises covering 5 distinct runner-only reasons + 1 runner-relay + taxonomy gate"

# ===========================================================================
# Canonical verifier mutation cases (24, one per approved reason)
# ===========================================================================

# --- case01: registry_manifest_invalid --------------------------------------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:registry_manifest_invalid" "$T" "registry_manifest_invalid"

# --- case02: registry_not_object (registry body is JSON array) --------------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$REGISTRY_REL', 'w') as f:
    f.write(json.dumps([1,2,3], indent=2) + '\n')
"
# registry_id cross-anchor: clear it on the manifest so the cross-anchor
# check is skipped (the body has no registry_id since it's now an array)
# and the not-object check is reached.
edit_manifest "$T" 'm["registry_id"] = "x"'
rehash_subject "$T" 0
expect_verifier_fail "case02:registry_not_object" "$T" "registry_not_object"

# --- case03: registry_schema_invalid ----------------------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["document_type"] = "wrong"'
rehash_subject "$T" 0
expect_verifier_fail "case03:registry_schema_invalid" "$T" "registry_schema_invalid"

# --- case04: registry_profile_unsupported -----------------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["profile"] = "some.other.profile"'
rehash_subject "$T" 0
expect_verifier_fail "case04:registry_profile_unsupported" "$T" "registry_profile_unsupported"

# --- case05: registry_identity_invalid --------------------------------------
# Set body.registry_id to a grammar-invalid value AND the manifest to
# the same value so the cross-anchor passes and check_05 grammar fires.
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["registry_id"] = "BadID"'
edit_manifest "$T" 'm["registry_id"] = "BadID"'
rehash_subject "$T" 0
expect_verifier_fail "case05:registry_identity_invalid" "$T" "registry_identity_invalid"

# --- case06: registry_authority_invalid -------------------------------------
T="$WORK/c06"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["registry_authority"].pop("identity_id")'
rehash_subject "$T" 0
expect_verifier_fail "case06:registry_authority_invalid" "$T" "registry_authority_invalid"

# --- case07: registry_entity_set_invalid (entities = []) --------------------
T="$WORK/c07"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case07:registry_entity_set_invalid" "$T" "registry_entity_set_invalid"

# --- case08: registry_entity_entry_invalid ----------------------------------
T="$WORK/c08"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0].pop("display_label")'
rehash_subject "$T" 0
expect_verifier_fail "case08:registry_entity_entry_invalid" "$T" "registry_entity_entry_invalid"

# --- case09: registry_entity_identifier_invalid -----------------------------
T="$WORK/c09"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["entity_id"] = "BadID"'
rehash_subject "$T" 0
expect_verifier_fail "case09:registry_entity_identifier_invalid" "$T" "registry_entity_identifier_invalid"

# --- case10: registry_role_invalid ------------------------------------------
T="$WORK/c10"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["role"] = "not_a_role"'
rehash_subject "$T" 0
expect_verifier_fail "case10:registry_role_invalid" "$T" "registry_role_invalid"

# --- case11: registry_status_invalid ----------------------------------------
T="$WORK/c11"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["status"] = "extreme"'
rehash_subject "$T" 0
expect_verifier_fail "case11:registry_status_invalid" "$T" "registry_status_invalid"

# --- case12: registry_effective_period_invalid ------------------------------
T="$WORK/c12"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["effective_period"]["starts_at"] = "2030-01-01T00:00:00Z"'
rehash_subject "$T" 0
expect_verifier_fail "case12:registry_effective_period_invalid" "$T" "registry_effective_period_invalid"

# --- case13: registry_key_reference_invalid ---------------------------------
T="$WORK/c13"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["key_references"][0]["algorithm"] = "md5"'
rehash_subject "$T" 0
expect_verifier_fail "case13:registry_key_reference_invalid" "$T" "registry_key_reference_invalid"

# --- case14: registry_key_binding_invalid -----------------------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["key_bindings"][0]["key_id"] = "no-such-key"'
rehash_subject "$T" 0
expect_verifier_fail "case14:registry_key_binding_invalid" "$T" "registry_key_binding_invalid"

# --- case15: issuer_entry_invalid -------------------------------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][0]["issuer"].pop("issuer_scope")'
rehash_subject "$T" 0
expect_verifier_fail "case15:issuer_entry_invalid" "$T" "issuer_entry_invalid"

# --- case16: verifier_entry_invalid -----------------------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][1]["verifier"].pop("verifier_profiles")'
rehash_subject "$T" 0
expect_verifier_fail "case16:verifier_entry_invalid" "$T" "verifier_entry_invalid"

# --- case17: relying_party_entry_invalid ------------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][2]["relying_party"].pop("reliance_scope")'
rehash_subject "$T" 0
expect_verifier_fail "case17:relying_party_entry_invalid" "$T" "relying_party_entry_invalid"

# --- case18: policy_authority_entry_invalid ---------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][3]["policy_authority"].pop("policy_scope")'
rehash_subject "$T" 0
expect_verifier_fail "case18:policy_authority_entry_invalid" "$T" "policy_authority_entry_invalid"

# --- case19: revocation_source_entry_invalid --------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][4]["revocation_source"].pop("source_type")'
rehash_subject "$T" 0
expect_verifier_fail "case19:revocation_source_entry_invalid" "$T" "revocation_source_entry_invalid"

# --- case20: protected_action_authority_entry_invalid -----------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["entities"][5]["protected_action_authority"].pop("protected_action_scope")'
rehash_subject "$T" 0
expect_verifier_fail "case20:protected_action_authority_entry_invalid" "$T" "protected_action_authority_entry_invalid"

# --- case21: trust_relationship_invalid -------------------------------------
# The canonical registry has trust_relationships=[]; inject a single
# entry whose to_entity_id does not exist in entities[].
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["trust_relationships"] = [{"relationship_id": "tr-bad", "from_entity_id": "proofrail.demo.relying_party", "to_entity_id": "no.such.entity", "relationship_verb": "recognizes_issuer", "effective_period": {"starts_at": "2026-01-01T00:00:00Z", "ends_at": "2027-01-01T00:00:00Z"}}]'
rehash_subject "$T" 0
expect_verifier_fail "case21:trust_relationship_invalid" "$T" "trust_relationship_invalid"

# --- case22: version_binding_invalid ----------------------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["version_bindings"][0]["upstream_version"] = "v9.9.9"'
rehash_subject "$T" 0
expect_verifier_fail "case22:version_binding_invalid" "$T" "version_binding_invalid"

# --- case23: non_claims_missing ---------------------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["non_claims"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case23:non_claims_missing" "$T" "non_claims_missing"

# --- case24: prohibited_registry_claim_present ------------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
edit_registry "$T" 'reg["registry_authority"]["display_name"] = "ProofRail demo (production PKI)"'
rehash_subject "$T" 0
expect_verifier_fail "case24:prohibited_registry_claim_present" "$T" "prohibited_registry_claim_present"

# ===========================================================================
# Duplicate registry_manifest_invalid cases (11; all route to that reason).
# ===========================================================================

# --- dup01: subject[0] path absolute ----------------------------------------
T="$WORK/d01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "dup01:subject_0_path_absolute" "$T" "registry_manifest_invalid"

# --- dup02: subject[0] path traversal ---------------------------------------
T="$WORK/d02"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "../escape.json"'
expect_verifier_fail "dup02:subject_0_path_traversal" "$T" "registry_manifest_invalid"

# --- dup03: subject[1] path absolute ----------------------------------------
T="$WORK/d03"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "/etc/hostname"'
expect_verifier_fail "dup03:subject_1_path_absolute" "$T" "registry_manifest_invalid"

# --- dup04: subject[1] path traversal ---------------------------------------
T="$WORK/d04"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "../escape-report.json"'
expect_verifier_fail "dup04:subject_1_path_traversal" "$T" "registry_manifest_invalid"

# --- dup05: subject[0] file missing on disk ---------------------------------
T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
rm "$T/registry-lite.json"
expect_verifier_fail "dup05:subject_0_file_absent" "$T" "registry_manifest_invalid"

# --- dup06: subject[0] size_bytes mismatch ----------------------------------
T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["size_bytes"] = 0'
expect_verifier_fail "dup06:subject_0_size_mismatch" "$T" "registry_manifest_invalid"

# --- dup07: subject[0] sha256 mismatch --------------------------------------
T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["sha256"] = "sha256:" + "f" * 64'
expect_verifier_fail "dup07:subject_0_sha_mismatch" "$T" "registry_manifest_invalid"

# --- dup08: wrong subject count (3 entries) ---------------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"sha256:" + "0"*64, "size_bytes":0})'
expect_verifier_fail "dup08:wrong_subject_count" "$T" "registry_manifest_invalid"

# --- dup09: subject[0] role wrong -------------------------------------------
T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["role"] = "wrong_role"'
expect_verifier_fail "dup09:subject_0_role_wrong" "$T" "registry_manifest_invalid"

# --- dup10: manifest registry_id cross-anchor mismatch ----------------------
T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["registry_id"] = "intentionally-different-id"'
expect_verifier_fail "dup10:registry_id_anchor_mismatch" "$T" "registry_manifest_invalid"

# --- dup11: conformance report disagrees on otherwise-valid registry --------
# Non-masking post-structural check: registry passes all 23 structural
# checks; mutate the bundled report; rehash subject [1]; the verifier
# re-derives the report from the (unchanged) registry and detects bundle
# disagreement, emitting registry_manifest_invalid.
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
edit_report "$T" 'r["summary"]["checks_total"] = r["summary"]["checks_total"] + 99'
rehash_subject "$T" 1
expect_verifier_fail "dup11:conformance_report_disagrees" "$T" "registry_manifest_invalid"

# ===========================================================================
# Runner-only refusal cases (5; preflight only).
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
    --input-registry "/etc/hostname" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO2_OUT" \
    --force

# --- ro2b: runner_input_path_forbidden (parent-traversal) -------------------
# The runner's path-forbidden preflight rejects BOTH absolute paths
# (ro2) AND parent-traversal relative paths (this case) under the
# same single reason. This asserts that the traversal branch is
# wired up at the runner level (Phase A), not only at the verifier
# level (where dup02 / dup04 already cover traversal inside subjects).
RO2B_OUT="$WORK/ro2b-out"
expect_runner_fail "ro2b:runner_input_path_forbidden_traversal" \
  "runner_input_path_forbidden" \
  "$RO2B_OUT" \
  "$RUNNER" \
    --input-registry "../leak.json" \
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
    --input-registry "fixtures/silver-registry-lite-v0.3.7/no-such-file.json" \
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
    --input-registry "fixtures/silver-registry-lite-v0.3.7" \
    --manifest-id "$MANIFEST_ID" \
    --report-id "$REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="fixtures/silver-registry-lite-v0.3.7/_test_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --input-registry "$BAD_INPUT_REL" \
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
# Runner-relay-of-verifier (1; rel01). The runner relays the verifier's
# OWN reason UNCHANGED; it does NOT wrap it in a sixth runner-only code.
# Staging directory must be cleaned up and destination must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
REL_INPUT_REL="fixtures/silver-registry-lite-v0.3.7/_test_relay_bad.json"
REL_INPUT_ABS="$REPO_ROOT/$REL_INPUT_REL"
# A registry with the wrong document_type; reaches the verifier's
# check_03 -> registry_schema_invalid.
cat > "$REL_INPUT_ABS" <<'EOF'
{
  "document_type": "proofrail.silver.registry_lite_WRONG",
  "schema_version": "v0.1.0",
  "registry_id": "rel01-bad"
}
EOF

set +e
rel_out="$(python3 "$RUNNER" \
  --input-registry "$REL_INPUT_REL" \
  --manifest-id "$MANIFEST_ID" \
  --report-id "$REPORT_ID" \
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
if ! echo "$rel_out" | grep -qE "^FAIL: registry_schema_invalid:"; then
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
# A speculative sixth wrapper code that does NOT exist must not appear.
# The sentinel name below is deliberately non-reason-shaped (suffix
# `_wrapper`, not in the verifier-reason filter) so the gate does not
# treat it as a reason-like token. If any implementer ever introduces a
# wrapper code by this name, this negative assertion will catch it.
if echo "$rel_out" | grep -qE "^FAIL: runner_self_validation_wrapper:"; then
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
# Scan v0.3.7-owned files and the v0.3.7-anchored sections of cross-version
# docs for reason-like tokens. The test fails if any unapproved
# reason-like token is found.
#
# Allowlists are defined inline in this test so a drifted reason name
# introduced anywhere in v0.3.7 surface area is caught at regression
# time, with no documentation lag.
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.3.7-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

APPROVED_VERIFIER = {
    "registry_manifest_invalid",
    "registry_not_object",
    "registry_schema_invalid",
    "registry_profile_unsupported",
    "registry_identity_invalid",
    "registry_authority_invalid",
    "registry_entity_set_invalid",
    "registry_entity_entry_invalid",
    "registry_entity_identifier_invalid",
    "registry_role_invalid",
    "registry_status_invalid",
    "registry_effective_period_invalid",
    "registry_key_reference_invalid",
    "registry_key_binding_invalid",
    "issuer_entry_invalid",
    "verifier_entry_invalid",
    "relying_party_entry_invalid",
    "policy_authority_entry_invalid",
    "revocation_source_entry_invalid",
    "protected_action_authority_entry_invalid",
    "trust_relationship_invalid",
    "version_binding_invalid",
    "non_claims_missing",
    "prohibited_registry_claim_present",
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# Escape hatch for tokens that look reason-like under the regex filter
# but are deliberately not protocol reasons. The audit pass removed
# every entry: each former entry was either dead (its suffix is not in
# REASON_FILTER), or renamed to a non-reason-shaped identifier, or
# rewritten in prose to use the full approved reason name. The empty
# set is preserved so the gate enforces strict no-additions discipline.
ALLOWED_NON_REASON_TOKENS: set[str] = set()

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

V0_3_7_FILES = [
    "tools/silver/build_silver_registry_lite_v0_1_0.py",
    "tools/silver/verify_silver_registry_lite_v0_1_0.py",
    "tests/test_silver_registry_lite_v0_3_7.sh",
    "schemas/silver-registry-lite-v0.1.0.md",
    "schemas/silver-registry-lite-manifest-v0.1.0.md",
    "schemas/silver-registry-lite-conformance-report-v0.1.0.md",
    "docs/silver/silver-registry-lite-v0.3.7.md",
    "demos/silver-demo-014-registry-lite/README.md",
    "demos/silver-demo-014-registry-lite/demo-walkthrough.md",
    "fixtures/silver-registry-lite-v0.3.7/README.md",
    "fixtures/silver-registry-lite-v0.3.7/registry-lite.json",
    "fixtures/silver-registry-lite-v0.3.7/registry-lite-with-trust-relationships.json",
    "fixtures/silver-registry-lite-v0.3.7/registry-lite-with-revocation-source.json",
]

# v0.3.7-anchored section markers across the six cross-version docs.
SECTION_MARKERS = {
    "README.md": [
        "## What ProofRail v0.3.7 Adds",
    ],
    "CLAUDE.md": [
        "### Silver Registry Lite Package: `demos/silver-demo-014-registry-lite/`",
    ],
    "tools/silver/README.md": [
        "## Silver Registry Lite Runner (v0.3.7)",
        "## Silver Registry Lite Verifier (v0.3.7)",
    ],
    "docs/silver/silver-artifact-map-v0.1.7.md": [
        "## v0.3.7 Registry Lite",
    ],
    "docs/silver/silver-limitations-and-non-claims.md": [
        "## v0.3.7 Registry Lite Non-Claims",
    ],
    "docs/gold/gold-boundary-v0.2.5.md": [
        "## v0.3.7 Notes",
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
    # Next section at the SAME level (matched by checking leading
    # marker prefix length). For "## " markers, the next "## " starts
    # a new section. For "### " markers, the next "### " starts a new
    # section.
    level = "## " if start_marker.startswith("## ") and not start_marker.startswith("### ") else "### "
    pat = r"^" + re.escape(level)
    m = re.search(pat, rest, flags=re.MULTILINE)
    if m is None:
        return text[i:]
    return text[i : i + len(start_marker) + m.start()]

errors: list[str] = []

for rel in V0_3_7_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.3.7-owned file: {rel}")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    bad = collect_unapproved_tokens(rel, text)
    for tok in sorted(set(bad)):
        errors.append(f"{rel}: unapproved reason-like token: {tok}")

# Scoped scan of v0.3.7 sections in cross-version docs.
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
                f"{rel}: missing v0.3.7 section anchor ({marker!r})"
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
        "v0.3.7-owned surface area",
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
echo "PASS: tests/test_silver_registry_lite_v0_3_7.sh"
echo "  48/48 exercises:"
echo "    - 4 positive-path (PP1..PP4)"
echo "    - 24 canonical verifier reasons (case01..case24)"
echo "    - 11 duplicate registry_manifest_invalid (dup01..dup11)"
echo "    - 6 runner-only refusals (ro1, ro2, ro2b, ro3..ro5)"
echo "    - 1 runner-relay-of-verifier (rel01)"
echo "    - 1 taxonomy gate (TG1)"
echo "    - 1 scoped sha256 snapshot (SS)"
