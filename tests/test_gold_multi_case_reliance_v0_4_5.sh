#!/usr/bin/env bash
# tests/test_gold_multi_case_reliance_v0_4_5.sh
#
# Phase 3 regression harness for the ProofRail v0.4.5 Gold Multi-Case
# Reliance Demo. The v0.4.5 package is a 2-subject wrapping manifest
# over (subjects[0]) ONE byte-copied v0.4.4 child wrapping manifest
# under child-packages/v0.4.4/ and (subjects[1]) the v0.4.5-authored
# multi_case_reliance_index body at the package root. The v0.4.5
# verifier owns seven new reasons (R55..R61) and DELEGATES the
# inherited 54 R01..R54 reasons to the co-located v0.4.4 verifier via
# subprocess (which transitively delegates to v0.4.0..v0.4.3). Any
# missing or non-FAIL non-zero inherited exit is non-reason
# `INFRA: ...` on stderr + exit 3.
#
# 21 numbered exercises:
#
#   Positive-path (2):
#     pp1   Pristine v0.4.5 build with --self-validate
#     pp2   Standalone v0.4.5 verifier PASS on pristine
#
#   Canonical verifier mutation cases (7; locked check order
#   R55 -> R56 -> R57 -> R58 -> R59 -> R60 -> R61):
#     r55   gold_multi_case_reliance_manifest_invalid
#           (drop document_type from v0.4.5 wrapping manifest)
#     r56   gold_multi_case_reliance_subject_digest_mismatch
#           (flip last hex char of subjects[1].sha256)
#     r57   gold_multi_case_reliance_index_invalid
#           (wrong document_type in index body; re-stamp subjects[1])
#     r58   gold_multi_case_reliance_child_manifest_binding_invalid
#           (index body package_id differs from manifest; re-stamp
#            multi_case_index_fingerprint then subjects[1])
#     r59   gold_multi_case_reliance_case_count_invalid
#           (drop last entry from cases[]; re-stamp fp + subjects[1])
#     r60   gold_multi_case_reliance_case_binding_invalid
#           (wrong-but-closed case_slug on cases[0]; re-stamp fp +
#            subjects[1])
#     r61   gold_multi_case_reliance_index_rederive_mismatch
#           (artifact-only single-hex-char flip of
#            multi_case_index_fingerprint; re-stamp subjects[1] so
#            R56 cannot shadow)
#
#   Inherited verifier relay (1; verbatim, no v0.4.5 wrapping):
#     inh01 v0.4.4 wrapping manifest document_type mutated, v0.4.5
#           subjects[0] re-stamped; v0.4.5 verifier delegates to
#           v0.4.4 verifier and relays FAIL: gold_manifest_invalid.
#
#   Runner-only refusal cases (5 distinct reasons):
#     ro1   runner_input_path_missing    (omit --input-package)
#     ro2   runner_input_path_forbidden  (absolute --input-package)
#     ro3   runner_input_file_missing    (relative no-such-file.json)
#     ro4   runner_input_read_failed     (relative path to directory)
#     ro5   runner_input_json_invalid    (non-JSON file)
#
#   Environment-failure INFRA case (env01) - non-destructive trap:
#     env01 Copy ONLY the v0.4.5 verifier into a tempdir WITHOUT its
#           co-located v0.4.4 sibling. The copied v0.4.5 verifier
#           resolves the v0.4.4 verifier path relative to its own
#           __file__ and finds nothing, emitting
#           `INFRA: co-located v0.4.4 verifier unavailable...` on
#           stderr + exit 3. The real on-disk co-located v0.4.4
#           verifier is NEVER touched, so SS equality is preserved.
#
#   Positive determinism (sup_det):
#     sup_det Build the v0.4.5 package twice with identical IDs +
#             identical --generated-at into two distinct --output-dir
#             paths; assert wrapping-manifest subjects[0..1].sha256
#             and index-body multi_case_index_fingerprint are
#             byte-identical across the two builds.
#
#   Idempotency (idem01):
#     idem01 Build the v0.4.5 package into a v0.4.5-scratch-prefixed
#            --output-dir, then re-build into the SAME --output-dir
#            with --force. The runner's prefix check accepts BOTH
#            realpath forms (/tmp/proofrail-v045-* and
#            /private/tmp/proofrail-v045-*), so --force re-runs are
#            accepted on both Linux and macOS.
#
#   No-residue (no_residue):
#     Assert no stray /tmp/proofrail-v045-bundle-* or
#     /tmp/proofrail-v045-staging-* scratch dirs leak after Phase 3,
#     and no v0.4.5 transient file residue under any inherited-tier
#     (v0.4.0..v0.4.4) fixture, tool, or schema directory.
#
#   Taxonomy gate (tg01):
#     5-file exact-token scan of v0.4.5-owned source paths (two
#     schemas + builder + verifier + this test file). Every
#     reason-shaped token must belong to the approved 7-reason
#     verifier set (R55..R61) or the approved 5-reason runner-only
#     set, plus a narrow inherited-data-field allowlist. Explicit
#     deny-list of environmental/wrapper escape patterns surfaces any
#     drift toward wrapping environment failures as public reasons.
#
#   Scoped SHA-256 snapshot (ss01):
#     4-file scoped snapshot of v0.4.5-owned source paths
#     (two schemas + builder + verifier), BEFORE and AFTER. Phase 3
#     performs no mutations on any of these paths; the env01 trap is
#     non-destructive and uses only a tempdir copy of the v0.4.5
#     verifier.
#
# Hash-first re-anchoring (intra-package):
#   Every mutation that lives INSIDE the v0.4.5 index body or the
#   v0.4.4 child wrapping manifest requires the corresponding v0.4.5
#   wrapping-manifest subject digest (subjects[1] for index body,
#   subjects[0] for v0.4.4 manifest) to be re-stamped so the R56
#   subject-digest check does not shadow the targeted R57..R61 or
#   inherited reason. For R58..R60 the mutation also changes the
#   canonical-JSON bytes of the index body, so multi_case_index_
#   fingerprint must be recomputed before re-stamping subjects[1] so
#   that R61 does not pre-empt the targeted earlier R-code. R61 is
#   the unique case where the fingerprint is mutated artifact-only
#   (single hex-char flip), with subjects[1] re-stamped over the
#   mutated body, so R56 passes and R57..R60 pass and R61 fires last.
#
# Phase 3 scope:
#   This harness is the only file in the Phase 3 write surface beyond
#   the .git/-internal ledger files. It performs no mutations on any
#   inherited v0.4.0..v0.4.4 file, fixture, schema, or tool; all
#   transient scratch is under /tmp/proofrail-v045-test.* and is
#   cleaned up via the EXIT trap.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# v0.4.5 runner + verifier under test.
RUNNER="$REPO_ROOT/tools/gold/build_gold_multi_case_reliance_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_multi_case_reliance_v0_1_0.py"

# Co-located v0.4.4 verifier (subprocess-invoked by the v0.4.5
# verifier). Listed only so the env01 isolated-copy exercise can
# confirm that ABSENCE of this sibling at __file__ resolution time
# yields INFRA + exit 3. The real on-disk file is never mutated.
V044_VERIFIER="$REPO_ROOT/tools/gold/verify_gold_reliance_package_index_v0_1_0.py"

# Three preflighted inputs accepted by the v0.4.5 runner. These are
# forwarded byte-for-byte into a /tmp/proofrail-v045-bundle-<pid>/
# scratch tree and then handed to the v0.4.4 child runner.
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
MATRIX_FIX_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"
LIFECYCLE_FIX_REL="fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json"

# Long output for human triage of any failure (kept under /tmp; the
# user-facing Phase 3 contract requires this exact filename).
LONG_LOG="/tmp/proofrail-v045-last-run.log"
: > "$LONG_LOG"

# WORK is the per-suite scratch root. The /tmp/proofrail-v045-test.*
# prefix:
#   * is under the v0.4.5 scratch marker so the runner's _safe_rmtree
#     accepts cleanup of any subtree;
#   * is matched by the runner's _output_dir_is_under_scratch_prefix
#     check on both Linux (/tmp/proofrail-v045-*) and macOS
#     (/private/tmp/proofrail-v045-* via realpath), so --force
#     re-runs against $WORK-rooted --output-dir succeed under the
#     idem01 case below.
WORK="$(mktemp -d /tmp/proofrail-v045-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

# Canonical v0.4.5 + v0.4.4 ID set used by every positive build.
GEN_AT="2026-12-01T00:30:00Z"
V045_MANIFEST_ID="proofrail-gold-multi-case-reliance-manifest-test-001"
V045_PACKAGE_ID="proofrail-gold-multi-case-reliance-demo-test-001"
V045_INDEX_ID="proofrail-gold-multi-case-reliance-index-test-001"
V045_DEMO_ID="gold-multi-case-reliance-demo-test-001"
V044_MANIFEST_ID="proofrail-gold-reliance-package-index-manifest-test-001"
V044_CONFORMANCE_REPORT_ID="proofrail-gold-conformance-report-reliance-test-001"
V044_DECISION_REPORT_ID="proofrail-gold-decision-report-demo-001"
V044_POLICY_EVAL_REPORT_ID="proofrail-gold-policy-evaluation-report-demo-001"
V044_CHALLENGE_LIFECYCLE_REPORT_ID="proofrail-gold-challenge-lifecycle-report-reliance-test-001"
V044_GOLD_RELIANCE_PACKAGE_INDEX_ID="proofrail-gold-reliance-package-index-test-001"

# v0.4.5 file constants (mirror runner/verifier module constants).
V045_MANIFEST_REL_FILE="gold-multi-case-reliance-package-manifest.json"
V045_INDEX_BODY_REL_FILE="gold-multi-case-reliance-index.json"
V044_CHILD_REL_DIR="child-packages/v0.4.4"
V044_CHILD_MANIFEST_REL_FILE="$V044_CHILD_REL_DIR/gold-reliance-package-index-manifest.json"

# --- Scoped sha256 snapshot of committed v0.4.5-owned source paths
# (BEFORE). Phase 3 performs no mutations on any of these 4 paths;
# the BEFORE/AFTER snapshot must be byte-identical. This harness
# file is intentionally excluded from the scoped set (its presence
# would be the only delta on initial commit). Inherited v0.4.0..v0.4.4
# files are out of scope here; their own harnesses snapshot them.
SCOPED_FILES=(
  "schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md"
  "schemas/gold-multi-case-reliance-index-v0.1.0.md"
  "tools/gold/build_gold_multi_case_reliance_v0_1_0.py"
  "tools/gold/verify_gold_multi_case_reliance_v0_1_0.py"
)
snapshot_scoped() {
  local out="$1"
  : > "$out"
  for rel in "${SCOPED_FILES[@]}"; do
    python3 -c "
import hashlib, sys
p = sys.argv[1]
h = hashlib.sha256()
with open(p, 'rb') as f:
    for c in iter(lambda: f.read(65536), b''): h.update(c)
print(sys.argv[2], h.hexdigest())
" "$REPO_ROOT/$rel" "$rel" >> "$out"
  done
}
snapshot_scoped "$WORK/scoped.before"

# --- Counters ---------------------------------------------------------------

PASS_COUNT=0
EXPECTED_COUNT=21

note_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS %2d/%d  %s\n' "$PASS_COUNT" "$EXPECTED_COUNT" "$1"
}

die() {
  echo "FAIL (test-harness): $*" >&2
  echo "---- last captured output ($WORK/last.out) ----" >&2
  if [ -f "$WORK/last.out" ]; then cat "$WORK/last.out" >&2; fi
  echo "---- full long log: $LONG_LOG ----" >&2
  exit 1
}

# --- File hashing helpers --------------------------------------------------

file_sha256() {
  python3 -c "
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], 'rb') as f:
    for c in iter(lambda: f.read(65536), b''): h.update(c)
print(h.hexdigest())
" "$1"
}

file_size() {
  python3 -c "import os, sys; print(os.path.getsize(sys.argv[1]))" "$1"
}

# --- Re-anchor helpers -----------------------------------------------------
# rehash_subject0_manifest <pkg_root>
#   After mutating the v0.4.4 wrapping manifest in place, re-stamp
#   v0.4.5 subjects[0].sha256 + subjects[0].size_bytes so R56 does
#   not shadow the targeted inherited verifier reason.
rehash_subject0_manifest() {
  python3 - "$1" << 'PYEOF'
import hashlib, json, os, sys
root = sys.argv[1]
m_path = os.path.join(root, "gold-multi-case-reliance-package-manifest.json")
child  = os.path.join(root, "child-packages/v0.4.4",
                      "gold-reliance-package-index-manifest.json")
m = json.load(open(m_path))
h = hashlib.sha256()
with open(child, "rb") as f:
    for c in iter(lambda: f.read(65536), b""): h.update(c)
m["subjects"][0]["sha256"]     = h.hexdigest()
m["subjects"][0]["size_bytes"] = os.path.getsize(child)
with open(m_path, "wb") as f:
    f.write(json.dumps(m, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# rehash_subject1_index <pkg_root>
#   After mutating the v0.4.5 index body in place (and either leaving
#   multi_case_index_fingerprint stale for the R57/R58/R59/R60 cases
#   or having explicitly flipped one hex char for the R61 case), re-
#   stamp v0.4.5 subjects[1].sha256 + subjects[1].size_bytes so the
#   on-disk index-body bytes match the manifest claim and R56 does
#   not shadow.
rehash_subject1_index() {
  python3 - "$1" << 'PYEOF'
import hashlib, json, os, sys
root = sys.argv[1]
m_path = os.path.join(root, "gold-multi-case-reliance-package-manifest.json")
ib_path = os.path.join(root, "gold-multi-case-reliance-index.json")
m = json.load(open(m_path))
h = hashlib.sha256()
with open(ib_path, "rb") as f:
    for c in iter(lambda: f.read(65536), b""): h.update(c)
m["subjects"][1]["sha256"]     = h.hexdigest()
m["subjects"][1]["size_bytes"] = os.path.getsize(ib_path)
with open(m_path, "wb") as f:
    f.write(json.dumps(m, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# restamp_index_fingerprint <pkg_root>
#   Recompute multi_case_index_fingerprint = SHA-256(canonical-JSON
#   bytes of the index body with multi_case_index_fingerprint
#   excluded) and write the body back in canonical form. Used for
#   R58/R59/R60 cases that mutate the body shape (other than the
#   fingerprint itself) and need the rederived fingerprint to match
#   so that R61 cannot pre-empt the targeted earlier R-code.
restamp_index_fingerprint() {
  python3 - "$1" << 'PYEOF'
import hashlib, json, os, sys
root = sys.argv[1]
ib_path = os.path.join(root, "gold-multi-case-reliance-index.json")
ib = json.load(open(ib_path))
ib_no_fp = {k: v for k, v in ib.items() if k != "multi_case_index_fingerprint"}
canon = json.dumps(ib_no_fp, sort_keys=True, separators=(",",":")).encode("utf-8")
ib["multi_case_index_fingerprint"] = hashlib.sha256(canon).hexdigest()
with open(ib_path, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# _edit_json_canonical <file_path> <python_expr>
#   Apply <python_expr> against the loaded JSON object `o` (alias
#   `m` for manifest, `b` for body) and re-serialize canonically.
_edit_json_canonical() {
  python3 - "$1" "$2" <<'PYEOF'
import json, sys
p = sys.argv[1]; expr = sys.argv[2]
with open(p) as f: o = json.load(f)
exec(expr, {"o": o, "m": o, "b": o, "json": json})
with open(p, "wb") as f:
    f.write(json.dumps(o, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

edit_v045_manifest() { _edit_json_canonical "$1/$V045_MANIFEST_REL_FILE"        "$2"; }
edit_v045_index()    { _edit_json_canonical "$1/$V045_INDEX_BODY_REL_FILE"      "$2"; }
edit_v044_manifest() { _edit_json_canonical "$1/$V044_CHILD_MANIFEST_REL_FILE"  "$2"; }

# --- Expectation helpers ---------------------------------------------------
# All four helpers capture combined stdout+stderr to $WORK/last.out
# and assert exit-code + first-line discipline. The contract matches
# the v0.4.4 harness (and the runner/verifier contracts):
#
#   verifier PASS  : exit 0, first line '^PASS\b'
#   verifier FAIL  : exit 1, first line '^FAIL: <reason>'
#   runner   PASS  : exit 0 (no per-line discipline asserted)
#   runner   FAIL  : exit 1, first line '^FAIL: <reason>'
#   verifier INFRA : exit 3, first line '^INFRA: <detail>'
#
# Captured output is appended to LONG_LOG with the case label, so a
# failed run leaves a navigable trace in /tmp/proofrail-v045-last-run.log.

_log_captured() {
  {
    echo "==== $1 ===="
    if [ -f "$WORK/last.out" ]; then cat "$WORK/last.out"; fi
    echo
  } >> "$LONG_LOG"
}

expect_verifier_pass() {
  local label="$1"; shift
  if "$@" >"$WORK/last.out" 2>&1; then
    _log_captured "$label"
    head -n1 "$WORK/last.out" | grep -qE '^PASS\b' \
      || die "$label: verifier PASS expected, first line wrong"
    grep -qE '^FAIL: ' "$WORK/last.out" \
      && die "$label: verifier PASS but FAIL line present"
    grep -qE '^INFRA:' "$WORK/last.out" \
      && die "$label: verifier PASS but INFRA line present"
    grep -qE 'Traceback' "$WORK/last.out" \
      && die "$label: verifier PASS but Traceback present"
    note_pass "$label"
  else
    local rc=$?
    _log_captured "$label"
    die "$label: verifier PASS expected, got exit=$rc"
  fi
}

expect_verifier_fail() {
  local label="$1"; local reason="$2"; shift 2
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  _log_captured "$label"
  [ "$rc" -eq 0 ] \
    && die "$label: verifier FAIL expected (reason=$reason), got exit=0"
  head -n1 "$WORK/last.out" \
    | grep -qE "^FAIL: $reason([[:space:]:]|\$)" \
    || die "$label: first line not 'FAIL: $reason'"
  grep -qE '^INFRA:' "$WORK/last.out" \
    && die "$label: verifier FAIL but INFRA present"
  grep -qE 'Traceback' "$WORK/last.out" \
    && die "$label: verifier FAIL but Traceback present"
  note_pass "$label"
}

expect_runner_fail() {
  local label="$1"; local reason="$2"; local outdir="$3"; shift 3
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  _log_captured "$label"
  [ "$rc" -eq 1 ] \
    || die "$label: runner FAIL exit=1 expected, got $rc"
  head -n1 "$WORK/last.out" \
    | grep -qE "^FAIL: $reason([[:space:]:]|\$)" \
    || die "$label: first line not 'FAIL: $reason'"
  grep -qE 'Traceback' "$WORK/last.out" \
    && die "$label: runner FAIL but Traceback present"
  if [ -n "$outdir" ] && [ -e "$outdir" ]; then
    die "$label: runner FAIL but output dir $outdir exists"
  fi
  note_pass "$label"
}

expect_verifier_infra() {
  local label="$1"; local infra_re="$2"; shift 2
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  _log_captured "$label"
  [ "$rc" -eq 3 ] \
    || die "$label: verifier INFRA exit=3 expected, got $rc"
  head -n1 "$WORK/last.out" \
    | grep -qE "^INFRA:[[:space:]]" \
    || die "$label: first line not 'INFRA: ...'"
  head -n1 "$WORK/last.out" \
    | grep -qE "$infra_re" \
    || die "$label: INFRA line does not match: $infra_re"
  grep -qE 'Traceback' "$WORK/last.out" \
    && die "$label: verifier INFRA but Traceback present"
  note_pass "$label"
}

# --- Pristine build --------------------------------------------------------
# Build the canonical reference package exactly once with
# --self-validate so pp1 covers both the runner happy path and the
# runner -> verifier relay PASS contract. Subsequent per-case cases
# copy from this tree (fresh_copy) so mutations are scoped per case
# and the pristine bytes are byte-stable for ss01 cmp.

PRISTINE="$WORK/pristine"

build_pristine() {
  python3 "$RUNNER" \
    --input-package                            "$PACKAGE_FIX_REL" \
    --matrix-input                             "$MATRIX_FIX_REL" \
    --lifecycle-input                          "$LIFECYCLE_FIX_REL" \
    --manifest-id                              "$V045_MANIFEST_ID" \
    --gold-multi-case-reliance-index-id        "$V045_INDEX_ID" \
    --package-id                               "$V045_PACKAGE_ID" \
    --governed-reliance-demo-id                "$V045_DEMO_ID" \
    --v044-manifest-id                         "$V044_MANIFEST_ID" \
    --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID" \
    --v044-decision-report-id                  "$V044_DECISION_REPORT_ID" \
    --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID" \
    --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID" \
    --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID" \
    --generated-at                             "$GEN_AT" \
    --output-dir                               "$PRISTINE" \
    --self-validate \
    >"$WORK/last.out" 2>&1 \
    || { _log_captured "pp1 pristine build (--self-validate)"; die "pp1: pristine build failed"; }
  _log_captured "pp1 pristine build (--self-validate)"
  [ -f "$PRISTINE/$V045_MANIFEST_REL_FILE" ] \
    || die "pp1: pristine missing wrapping manifest"
  [ -f "$PRISTINE/$V045_INDEX_BODY_REL_FILE" ] \
    || die "pp1: pristine missing index body"
  [ -f "$PRISTINE/$V044_CHILD_MANIFEST_REL_FILE" ] \
    || die "pp1: pristine missing v0.4.4 child manifest"
  note_pass "pp1 pristine_build_self_validate"
}

fresh_copy() {
  local dest="$1"
  [ -e "$dest" ] && rm -rf "$dest"
  cp -R "$PRISTINE" "$dest"
}

build_pristine

# --- pp2: standalone v0.4.5 verifier PASS on pristine ----------------------
expect_verifier_pass "pp2 standalone_verifier_pass" \
  python3 "$VERIFIER" --manifest "$PRISTINE/$V045_MANIFEST_REL_FILE"

# --- R55..R61: canonical verifier mutation cases ---------------------------
# Table-driven loop. Each row:
#   label  reason  mutator-fn  [reanchor-flags...]
# reanchor-flags drive the post-mutation cascade so the verifier's
# locked check order reaches the targeted R-code without earlier
# checks shadowing.
#
# Mutator functions:
#   _mut_r55  drop document_type from v0.4.5 wrapping manifest
#   _mut_r56  flip last hex char of subjects[1].sha256 (manifest only)
#   _mut_r57  set wrong document_type on index body
#   _mut_r58  set index body package_id to a distinct-but-shape-valid
#             string (differs from manifest package_id)
#   _mut_r59  drop last entry from cases[]
#   _mut_r60  set cases[0].case_slug to a closed-vocabulary value that
#             does not match the canonical mapping for case_index=0
#   _mut_r61  flip last hex char of multi_case_index_fingerprint only
#
# Re-anchor flags (post-mutation, in fixed order):
#   --restamp-fp   recompute multi_case_index_fingerprint over body
#                  (skipped for R61 - that case mutates the fp itself)
#   --restamp-s1   re-stamp v0.4.5 subjects[1] over the post-mutation
#                  body bytes (skipped for R55/R56 - those don't touch
#                  the body)

_mut_r55() { edit_v045_manifest "$1" 'm.pop("document_type", None)'; }

_mut_r56() {
  python3 - "$1" << 'PYEOF'
import json, sys
m_path = sys.argv[1] + "/gold-multi-case-reliance-package-manifest.json"
m = json.load(open(m_path))
h = m["subjects"][1]["sha256"]
last = h[-1]
flip = "f" if last != "f" else "e"
m["subjects"][1]["sha256"] = h[:-1] + flip
with open(m_path, "wb") as f:
    f.write(json.dumps(m, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

_mut_r57() { edit_v045_index "$1" 'b["document_type"] = "proofrail.gold.NOT_the_index"'; }

_mut_r58() {
  # Use a shape-valid package_id (matches PACKAGE_ID_RE:
  # ^[a-z][a-z0-9_]*(-[a-z0-9]+)*$) that differs from the
  # manifest's package_id; the cross-anchor check then fires R58
  # binding_invalid. The replacement must stay lowercase-
  # alphanumeric-with-dashes so the index-body identifier-shape
  # check (R57) does not pre-empt R58.
  edit_v045_index "$1" 'b["package_id"] = "proofrail-gold-multi-case-reliance-demo-test-002"'
}

_mut_r59() {
  edit_v045_index "$1" 'b["cases"] = b["cases"][:-1]'
}

_mut_r60() {
  # Replace cases[0].case_slug with a closed-vocabulary value that
  # is NOT the canonical mapping for case_index=0 ("clean_acceptance").
  # The replacement value must be in SCENARIO_TYPES so the per-case
  # shape check passes and R60 fires on the case_index<->case_slug
  # binding instead of an upstream shape reason.
  edit_v045_index "$1" 'b["cases"][0]["case_slug"] = "supersession"'
}

_mut_r61() {
  python3 - "$1" << 'PYEOF'
import json, sys
ib_path = sys.argv[1] + "/gold-multi-case-reliance-index.json"
ib = json.load(open(ib_path))
fp = ib["multi_case_index_fingerprint"]
last = fp[-1]
flip = "f" if last != "f" else "e"
ib["multi_case_index_fingerprint"] = fp[:-1] + flip
with open(ib_path, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# Row schema:  "label|reason|mutator|reanchor"
# reanchor:    "none" | "s1" | "fp_s1" | "s1_only"
# Where:
#   none    : no post-mutation cascade (R55, R56)
#   s1_only : re-stamp subjects[1] only (R57: body shape break,
#             fingerprint check unreachable so fp re-stamp not needed)
#   fp_s1   : restamp_index_fingerprint then rehash_subject1_index
#             (R58, R59, R60: body shape valid, fp must match,
#             targeted earlier R-code fires)
#   s1_only_r61 : rehash_subject1_index only (R61: fp was just
#             flipped by mutator, must NOT restamp it; re-stamp s1
#             over the new body so R56 does not shadow)
CASE_ROWS=(
  "r55|gold_multi_case_reliance_manifest_invalid|_mut_r55|none"
  "r56|gold_multi_case_reliance_subject_digest_mismatch|_mut_r56|none"
  "r57|gold_multi_case_reliance_index_invalid|_mut_r57|s1_only"
  "r58|gold_multi_case_reliance_child_manifest_binding_invalid|_mut_r58|fp_s1"
  "r59|gold_multi_case_reliance_case_count_invalid|_mut_r59|fp_s1"
  "r60|gold_multi_case_reliance_case_binding_invalid|_mut_r60|fp_s1"
  "r61|gold_multi_case_reliance_index_rederive_mismatch|_mut_r61|s1_only_r61"
)

for row in "${CASE_ROWS[@]}"; do
  IFS='|' read -r label reason mutator reanchor <<<"$row"
  pkg="$WORK/$label"
  fresh_copy "$pkg"
  "$mutator" "$pkg"
  case "$reanchor" in
    none)        : ;;
    s1_only)     rehash_subject1_index "$pkg" ;;
    fp_s1)       restamp_index_fingerprint "$pkg"; rehash_subject1_index "$pkg" ;;
    s1_only_r61) rehash_subject1_index "$pkg" ;;
    *)           die "$label: unknown reanchor=$reanchor" ;;
  esac
  expect_verifier_fail "$label $reason" "$reason" \
    python3 "$VERIFIER" --manifest "$pkg/$V045_MANIFEST_REL_FILE"
done

# --- inh01: inherited verifier relay (verbatim, no v0.4.5 wrapping) --------
# Mutate the v0.4.4 child wrapping manifest's document_type, re-stamp
# v0.4.5 subjects[0] so R56 does not shadow, then run the v0.4.5
# verifier. R55..R61 all pass; v0.4.5 Phase 3 subprocess-delegates to
# the v0.4.4 verifier which emits FAIL: gold_manifest_invalid (R01).
# The v0.4.5 verifier relays this verbatim with exit 1 and no v0.4.5
# wrapping reason.
INH01="$WORK/inh01"
fresh_copy "$INH01"
edit_v044_manifest "$INH01" 'm["document_type"] = "wrong"'
rehash_subject0_manifest "$INH01"
expect_verifier_fail "inh01 inherited_relay_gold_manifest_invalid" \
  "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$INH01/$V045_MANIFEST_REL_FILE"

# --- ro1..ro5: runner-only refusals ----------------------------------------
# Table-driven loop. Each row:
#   label|reason|mode|payload
# mode payload semantics:
#   omit              : payload unused; --input-package arg omitted
#   absolute          : payload is the absolute path passed verbatim
#                       (path itself need not exist; the absoluteness
#                        check refuses before existence is probed)
#   rel_nonexistent   : payload is a /tmp/proofrail-v045-test.*-relative
#                       string for a file that does NOT exist; harness
#                       cd's into $WORK before invocation
#   rel_directory     : payload is a /tmp/proofrail-v045-test.*-relative
#                       string for a pre-created directory under $WORK;
#                       harness cd's into $WORK before invocation
#   rel_badjson       : payload is a /tmp/proofrail-v045-test.*-relative
#                       string for a pre-created non-JSON file under
#                       $WORK; harness cd's into $WORK before invocation
#
# All five rows route --input-package as the first preflight failure,
# so --matrix-input and --lifecycle-input never reach their own
# preflight (they may be omitted entirely; argparse default is None
# which would itself be path_missing if reached, but isn't).
#
# Each row passes a unique --output-dir under $WORK. The runner
# refuses before any output-dir creation, so expect_runner_fail
# asserts that the named output-dir does NOT exist on exit.

# Pre-create the ro4 directory + ro5 bad-JSON file under $WORK.
mkdir -p "$WORK/ro4_dir"
printf 'not valid json {' > "$WORK/ro5_bad.json"
# An absolute path for ro2 - need not exist; the absoluteness check
# refuses first.
RO2_ABSPATH="$WORK/never-touched-absolute.json"

RO_ROWS=(
  "ro1|runner_input_path_missing|omit|"
  "ro2|runner_input_path_forbidden|absolute|$RO2_ABSPATH"
  "ro3|runner_input_file_missing|rel_nonexistent|no-such-input.json"
  "ro4|runner_input_read_failed|rel_directory|ro4_dir"
  "ro5|runner_input_json_invalid|rel_badjson|ro5_bad.json"
)

_run_ro_case() {
  local label="$1" reason="$2" mode="$3" payload="$4"
  local outdir="$WORK/$label-out"
  # Build the common args once per row. For modes that need a
  # relative path, we cd into $WORK so the relative path resolves
  # there; --matrix-input + --lifecycle-input are then unreachable
  # from cwd, but the runner never gets there - --input-package
  # preflight refuses first. We pass them as bare basenames that
  # also live under $WORK so any future reordering would surface a
  # distinct FAIL rather than masking under runner_input_*.
  local cwd_was; cwd_was="$(pwd)"
  case "$mode" in
    omit)
      # No --input-package arg at all. cwd does not matter; the
      # path_missing refusal fires before any fs lookup.
      local rc
      if python3 "$RUNNER" \
        --matrix-input    "$MATRIX_FIX_REL" \
        --lifecycle-input "$LIFECYCLE_FIX_REL" \
        --manifest-id                              "$V045_MANIFEST_ID-$label" \
        --gold-multi-case-reliance-index-id        "$V045_INDEX_ID-$label" \
        --package-id                               "$V045_PACKAGE_ID-$label" \
        --governed-reliance-demo-id                "$V045_DEMO_ID-$label" \
        --v044-manifest-id                         "$V044_MANIFEST_ID-$label" \
        --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID-$label" \
        --v044-decision-report-id                  "$V044_DECISION_REPORT_ID-$label" \
        --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID-$label" \
        --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID-$label" \
        --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID-$label" \
        --generated-at                             "$GEN_AT" \
        --output-dir                               "$outdir" \
        >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
      ;;
    absolute)
      local rc
      if python3 "$RUNNER" \
        --input-package   "$payload" \
        --matrix-input    "$MATRIX_FIX_REL" \
        --lifecycle-input "$LIFECYCLE_FIX_REL" \
        --manifest-id                              "$V045_MANIFEST_ID-$label" \
        --gold-multi-case-reliance-index-id        "$V045_INDEX_ID-$label" \
        --package-id                               "$V045_PACKAGE_ID-$label" \
        --governed-reliance-demo-id                "$V045_DEMO_ID-$label" \
        --v044-manifest-id                         "$V044_MANIFEST_ID-$label" \
        --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID-$label" \
        --v044-decision-report-id                  "$V044_DECISION_REPORT_ID-$label" \
        --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID-$label" \
        --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID-$label" \
        --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID-$label" \
        --generated-at                             "$GEN_AT" \
        --output-dir                               "$outdir" \
        >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
      ;;
    rel_nonexistent|rel_directory|rel_badjson)
      # Switch cwd into $WORK so the relative payload resolves
      # there. Matrix + lifecycle args are PROBABLY unreachable
      # (input-package preflights first), but we pass them as bare
      # absolute paths so that any future reordering would route to
      # runner_input_path_forbidden (a distinct closed-vocabulary
      # refusal) rather than silently producing a stale-cwd error.
      cd "$WORK"
      local rc
      if python3 "$RUNNER" \
        --input-package   "$payload" \
        --matrix-input    "$REPO_ROOT/$MATRIX_FIX_REL" \
        --lifecycle-input "$REPO_ROOT/$LIFECYCLE_FIX_REL" \
        --manifest-id                              "$V045_MANIFEST_ID-$label" \
        --gold-multi-case-reliance-index-id        "$V045_INDEX_ID-$label" \
        --package-id                               "$V045_PACKAGE_ID-$label" \
        --governed-reliance-demo-id                "$V045_DEMO_ID-$label" \
        --v044-manifest-id                         "$V044_MANIFEST_ID-$label" \
        --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID-$label" \
        --v044-decision-report-id                  "$V044_DECISION_REPORT_ID-$label" \
        --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID-$label" \
        --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID-$label" \
        --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID-$label" \
        --generated-at                             "$GEN_AT" \
        --output-dir                               "$outdir" \
        >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
      cd "$cwd_was"
      ;;
    *) die "$label: unknown mode=$mode" ;;
  esac
  _log_captured "$label $reason ($mode)"
  [ "$rc" -eq 1 ] \
    || die "$label: runner FAIL exit=1 expected, got $rc"
  head -n1 "$WORK/last.out" \
    | grep -qE "^FAIL: $reason([[:space:]:]|\$)" \
    || die "$label: first line not 'FAIL: $reason'"
  grep -qE 'Traceback' "$WORK/last.out" \
    && die "$label: runner FAIL but Traceback present"
  if [ -e "$outdir" ]; then
    die "$label: runner FAIL but output dir $outdir exists"
  fi
  note_pass "$label $reason"
}

for row in "${RO_ROWS[@]}"; do
  IFS='|' read -r label reason mode payload <<<"$row"
  _run_ro_case "$label" "$reason" "$mode" "$payload"
done

# --- env01: INFRA exit 3 when co-located v0.4.4 verifier is missing --------
# Copy ONLY the v0.4.5 verifier into a /tmp tempdir. The v0.4.5
# verifier resolves the v0.4.4 verifier path relative to its own
# __file__; with no sibling present the verifier emits
# `INFRA: co-located v0.4.4 verifier unavailable ...` on stderr and
# exits 3. The real on-disk v0.4.4 verifier is NEVER touched.

ENV01_TOOLS="$WORK/env01-tools"
mkdir -p "$ENV01_TOOLS"
cp "$VERIFIER" "$ENV01_TOOLS/verify_gold_multi_case_reliance_v0_1_0.py"
expect_verifier_infra "env01 infra_missing_v0_4_4_verifier" \
  "co-located v0\\.4\\.4 verifier unavailable" \
  python3 "$ENV01_TOOLS/verify_gold_multi_case_reliance_v0_1_0.py" \
    --manifest "$PRISTINE/$V045_MANIFEST_REL_FILE"

# --- sup_det: positive determinism ----------------------------------------
# Build the v0.4.5 package twice with identical IDs + identical
# --generated-at into two distinct --output-dir paths; assert
# subjects[0..1].sha256 + multi_case_index_fingerprint are
# byte-identical across the two builds.
SUPDET_A="$WORK/supdet-a"
SUPDET_B="$WORK/supdet-b"
_supdet_build() {
  python3 "$RUNNER" \
    --input-package                            "$PACKAGE_FIX_REL" \
    --matrix-input                             "$MATRIX_FIX_REL" \
    --lifecycle-input                          "$LIFECYCLE_FIX_REL" \
    --manifest-id                              "$V045_MANIFEST_ID-supdet" \
    --gold-multi-case-reliance-index-id        "$V045_INDEX_ID-supdet" \
    --package-id                               "$V045_PACKAGE_ID-supdet" \
    --governed-reliance-demo-id                "$V045_DEMO_ID-supdet" \
    --v044-manifest-id                         "$V044_MANIFEST_ID-supdet" \
    --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID-supdet" \
    --v044-decision-report-id                  "$V044_DECISION_REPORT_ID-supdet" \
    --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID-supdet" \
    --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID-supdet" \
    --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID-supdet" \
    --generated-at                             "$GEN_AT" \
    --output-dir                               "$1" \
    >"$WORK/last.out" 2>&1 \
    || { _log_captured "sup_det build $1"; die "sup_det: build $1 failed"; }
  _log_captured "sup_det build $1"
}
_supdet_build "$SUPDET_A"
_supdet_build "$SUPDET_B"
python3 - "$SUPDET_A" "$SUPDET_B" << 'PYEOF' || die "sup_det: nondeterministic"
import json, sys
a, b = sys.argv[1], sys.argv[2]
ma = json.load(open(a + "/gold-multi-case-reliance-package-manifest.json"))
mb = json.load(open(b + "/gold-multi-case-reliance-package-manifest.json"))
ia = json.load(open(a + "/gold-multi-case-reliance-index.json"))
ib = json.load(open(b + "/gold-multi-case-reliance-index.json"))
errs = []
for i in range(2):
    if ma["subjects"][i]["sha256"] != mb["subjects"][i]["sha256"]:
        errs.append(("subjects[%d].sha256" % i,
                     ma["subjects"][i]["sha256"], mb["subjects"][i]["sha256"]))
if ia["multi_case_index_fingerprint"] != ib["multi_case_index_fingerprint"]:
    errs.append(("multi_case_index_fingerprint",
                 ia["multi_case_index_fingerprint"],
                 ib["multi_case_index_fingerprint"]))
if errs:
    for e in errs: print("DET DRIFT:", e)
    sys.exit(1)
PYEOF
note_pass "sup_det subjects_and_index_fingerprint_byte_identical"

# --- idem01: --force re-run idempotency -----------------------------------
# Build the v0.4.5 package into a v0.4.5-scratch-prefixed
# --output-dir, then re-build into the SAME --output-dir with
# --force. The runner's prefix check accepts BOTH realpath forms
# (/tmp/proofrail-v045-* and /private/tmp/proofrail-v045-*) so the
# second --force build succeeds on both Linux and macOS. The first
# build asserts byte-identical wrapping manifest + index body
# bytes across the two runs (no --self-validate so we test the
# pure runner determinism here; pp1 + pp2 cover --self-validate).
IDEM_OUT="$WORK/idem01-out"
_idem_build() {
  local force_flag="$1"
  python3 "$RUNNER" \
    --input-package                            "$PACKAGE_FIX_REL" \
    --matrix-input                             "$MATRIX_FIX_REL" \
    --lifecycle-input                          "$LIFECYCLE_FIX_REL" \
    --manifest-id                              "$V045_MANIFEST_ID-idem01" \
    --gold-multi-case-reliance-index-id        "$V045_INDEX_ID-idem01" \
    --package-id                               "$V045_PACKAGE_ID-idem01" \
    --governed-reliance-demo-id                "$V045_DEMO_ID-idem01" \
    --v044-manifest-id                         "$V044_MANIFEST_ID-idem01" \
    --v044-conformance-report-id               "$V044_CONFORMANCE_REPORT_ID-idem01" \
    --v044-decision-report-id                  "$V044_DECISION_REPORT_ID-idem01" \
    --v044-policy-evaluation-report-id         "$V044_POLICY_EVAL_REPORT_ID-idem01" \
    --v044-challenge-lifecycle-report-id       "$V044_CHALLENGE_LIFECYCLE_REPORT_ID-idem01" \
    --v044-gold-reliance-package-index-id      "$V044_GOLD_RELIANCE_PACKAGE_INDEX_ID-idem01" \
    --generated-at                             "$GEN_AT" \
    --output-dir                               "$IDEM_OUT" \
    $force_flag \
    >"$WORK/last.out" 2>&1
}
_idem_build "" \
  || { _log_captured "idem01 first build"; die "idem01: first build (no --force) failed"; }
_log_captured "idem01 first build"
[ -f "$IDEM_OUT/$V045_MANIFEST_REL_FILE" ] \
  || die "idem01: first build did not produce wrapping manifest"
IDEM_FIRST_MANIFEST_SHA="$(file_sha256 "$IDEM_OUT/$V045_MANIFEST_REL_FILE")"
IDEM_FIRST_INDEX_SHA="$(file_sha256 "$IDEM_OUT/$V045_INDEX_BODY_REL_FILE")"

_idem_build "--force" \
  || { _log_captured "idem01 second build (--force)"; die "idem01: second build (--force) failed"; }
_log_captured "idem01 second build (--force)"
[ -f "$IDEM_OUT/$V045_MANIFEST_REL_FILE" ] \
  || die "idem01: second build did not produce wrapping manifest"
IDEM_SECOND_MANIFEST_SHA="$(file_sha256 "$IDEM_OUT/$V045_MANIFEST_REL_FILE")"
IDEM_SECOND_INDEX_SHA="$(file_sha256 "$IDEM_OUT/$V045_INDEX_BODY_REL_FILE")"
[ "$IDEM_FIRST_MANIFEST_SHA" = "$IDEM_SECOND_MANIFEST_SHA" ] \
  || die "idem01: wrapping manifest sha256 drift across --force re-run"
[ "$IDEM_FIRST_INDEX_SHA" = "$IDEM_SECOND_INDEX_SHA" ] \
  || die "idem01: index body sha256 drift across --force re-run"
note_pass "idem01 double_force_run_byte_identical"

# --- no_residue: assert no v0.4.5 scratch dirs leak under /tmp -------------
# The runner cleans up its bundle + staging dirs on both success and
# failure paths. Phase 3 must leave none behind. Also assert no
# v0.4.5 file residue under inherited-tier (v0.4.0..v0.4.4) fixture,
# tool, or schema directories - all v0.4.5 source paths are
# uniquely-named so a substring match against the inherited dirs
# would only match a leak.

_tmp_leak=$(find /tmp /private/tmp -maxdepth 1 -mindepth 1 \
  \( -name 'proofrail-v045-bundle-*' -o -name 'proofrail-v045-staging-*' \) \
  -print 2>/dev/null | head -n 5)
[ -z "$_tmp_leak" ] \
  || die "no_residue: leftover v0.4.5 scratch under /tmp: $_tmp_leak"

_INHERITED_TIER_DIRS=(
  "$REPO_ROOT/fixtures/gold-governed-reliance-v0.4.0"
  "$REPO_ROOT/fixtures/gold-policy-evaluation-matrix-v0.4.2"
  "$REPO_ROOT/fixtures/gold-challenge-lifecycle-lite-v0.4.3"
)
# Inherited tool + schema dirs are intentionally allowed to contain
# the four v0.4.5 source files (those are the approved write surface
# in tools/gold/ and schemas/). The inherited-tier check below
# scrutinizes only the inherited-fixture dirs, which must contain
# zero v0.4.5-prefixed files.
_nores_leak=""
for d in "${_INHERITED_TIER_DIRS[@]}"; do
  while IFS= read -r f; do
    case "$(basename "$f")" in
      *multi-case-reliance*|*proofrail-v045-*) _nores_leak="$_nores_leak $f" ;;
    esac
  done < <(find "$d" -type f 2>/dev/null)
done
[ -z "$_nores_leak" ] \
  || die "no_residue: v0.4.5 transient residue under inherited fixture dirs:$_nores_leak"
note_pass "no_residue no_v045_scratch_or_inherited_residue"

# --- tg01: 5-file exact-token taxonomy gate -------------------------------
# Scan the v0.4.5-owned source paths (two schemas + builder + verifier
# + this test file) for reason-shaped tokens. The closed approved set
# is exactly the 7-reason verifier vocabulary (R55..R61) + the 5
# runner-only refusal vocabulary. A narrow inherited-data-field
# allowlist covers short-form labels used by this harness only. The
# deny-list surfaces any drift toward wrapping-environment-failure-
# as-public-reason patterns.
python3 - "$REPO_ROOT" << 'PYEOF' || die "tg01: taxonomy drift"
import os, re, sys
ROOT = sys.argv[1]
FILES = [
  "schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md",
  "schemas/gold-multi-case-reliance-index-v0.1.0.md",
  "tools/gold/build_gold_multi_case_reliance_v0_1_0.py",
  "tools/gold/verify_gold_multi_case_reliance_v0_1_0.py",
  "tests/test_gold_multi_case_reliance_v0_4_5.sh",
]
APPROVED_VERIFIER = {
  "gold_multi_case_reliance_manifest_invalid",                   # R55
  "gold_multi_case_reliance_subject_digest_mismatch",            # R56
  "gold_multi_case_reliance_index_invalid",                      # R57
  "gold_multi_case_reliance_child_manifest_binding_invalid",     # R58
  "gold_multi_case_reliance_case_count_invalid",                 # R59
  "gold_multi_case_reliance_case_binding_invalid",               # R60
  "gold_multi_case_reliance_index_rederive_mismatch",            # R61
}
assert len(APPROVED_VERIFIER) == 7, len(APPROVED_VERIFIER)
APPROVED_RUNNER = {
  "runner_input_path_missing",
  "runner_input_path_forbidden",
  "runner_input_file_missing",
  "runner_input_read_failed",
  "runner_input_json_invalid",
}
assert len(APPROVED_RUNNER) == 5
# Narrow allowlist of snake_case identifiers that match the reason-
# suffix regex but are intentionally NOT v0.4.5 public reason names.
# These appear in this harness, in the schemas, or in the runner/
# verifier as either:
#   * short-form case labels in prose (e.g. "index_invalid" in a
#     comment talking about R57)
#   * inherited reason names emitted by the v0.4.4 / v0.4.0-3
#     verifiers and relayed verbatim by the v0.4.5 verifier (a
#     public-API contract that this harness explicitly exercises
#     via inh01)
INHERITED_DATA_ALLOW = {
  "inherited_relay_gold_manifest_invalid",
  "gold_manifest_invalid",
  "gold_package_schema_invalid",
  "index_invalid",
  "binding_invalid",
  "path_missing",
}
# Deny-list of environmental/wrapper-escape patterns that must NOT
# appear in the v0.4.5-owned source-set as public reason vocabulary.
# Each pattern is assembled by string concatenation so the literal
# full token never appears in this scanner's own source (which would
# otherwise self-trip the deny check when this very file is scanned).
DENY_PATTERNS = [
  r"\b" + "wrapping_" + "environment_failure" + r"\b",
  r"\b" + "verifier_" + "environment_failure" + r"\b",
  r"\b" + "harness_" + "internal_error" + r"\b",
  r"\b" + "runner_relay_" + "of_verifier_failure" + r"\b",
]
SUFFIX = r"(?:_invalid|_not_object|_missing|_forbidden|_failed|_unsupported|_present|_mismatch)"
TOK_RE = re.compile(r"\b([a-z][a-z0-9_]*?" + SUFFIX + r")\b")
errors = []
for rel in FILES:
  p = os.path.join(ROOT, rel)
  with open(p, encoding="utf-8") as f:
    text = f.read()
  for m in TOK_RE.finditer(text):
    tok = m.group(1)
    if tok in APPROVED_VERIFIER: continue
    if tok in APPROVED_RUNNER: continue
    if tok in INHERITED_DATA_ALLOW: continue
    errors.append((rel, tok))
  for pat in DENY_PATTERNS:
    mm = re.search(pat, text)
    if mm:
      errors.append((rel, "DENY:" + mm.group(0)))
if errors:
  for e in errors[:50]:
    print("DRIFT", e)
  sys.exit(1)
PYEOF
note_pass "tg01 reason_taxonomy_closed"

# --- ss01: 4-file scoped SHA-256 snapshot AFTER, byte-identical to BEFORE
# Phase 3 must perform no mutations on any scoped file. This harness
# file is excluded from the scoped set (its own creation is the
# Phase 3 write surface delta).
snapshot_scoped "$WORK/scoped.after"
if cmp -s "$WORK/scoped.before" "$WORK/scoped.after"; then
  note_pass "ss01 scoped_byte_identical"
else
  echo "--- BEFORE ---" >&2; cat "$WORK/scoped.before" >&2
  echo "--- AFTER  ---" >&2; cat "$WORK/scoped.after"  >&2
  die "ss01: scoped source-set mutated during Phase 3"
fi

# =============================================================================
# Final tally
# =============================================================================
if [ "$PASS_COUNT" -ne "$EXPECTED_COUNT" ]; then
  die "harness: PASS=$PASS_COUNT EXPECTED=$EXPECTED_COUNT"
fi
echo "ALL ${EXPECTED_COUNT} PASS"
