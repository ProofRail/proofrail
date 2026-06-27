#!/usr/bin/env bash
# tests/test_gold_reliance_package_index_v0_4_4.sh
#
# Phase 3 regression harness for the ProofRail v0.4.4 Gold Reliance
# Package Index. The v0.4.4 package is a 5-subject wrapping manifest
# over (subjects [0..3]) the four byte-copied inherited Gold child
# wrapping manifests (v0.4.0, v0.4.1, v0.4.2, v0.4.3-under-v0.4.3.1)
# and (subject [4]) the v0.4.4-authored local index body. The v0.4.4
# verifier owns six new reasons (R49..R54) over the index body and
# DELEGATES the inherited 48 R01..R48 reasons over subjects [0..3] to
# the corresponding co-located inherited verifiers (v0.4.0, v0.4.1,
# v0.4.2, v0.4.3) via subprocess. A missing or non-FAIL non-zero
# inherited exit is non-reason INFRA: + exit 3.
#
# 103 numbered exercises (Phase 3):
#
#   Positive-path (6):
#     PP1   Pristine v0.4.4 build with --self-validate
#     PP2   Pristine independent v0.4.4 verifier pass
#     PP3   Inline manifest layout (5 subjects, 7-ID collision class)
#     PP4   Inline index body shape (4 entries + coverage_summary)
#     PP5   Inline cross-anchor body<->manifest consistency
#     PP6   Inline 7-ID file-level distinctness across body+manifest
#
#   Canonical verifier mutation cases (54 = 48 inherited + 6 v0.4.4):
#     case01..case24  inherited from v0.4.0 (R01..R24) — mutate the
#                     v0.4.0 child-closure body or the v0.4.0 child
#                     wrapping manifest itself; the v0.4.4 verifier's
#                     Phase 4 subprocess delegation relays the v0.4.0
#                     verifier reason verbatim.
#     case25..case29  inherited from v0.4.1 (R25..R29) — mutate the
#                     v0.4.1 child decision-report body within the
#                     v0.4.1 child closure.
#     case30..case38  inherited from v0.4.2 (R30..R38) — mutate the
#                     v0.4.2 matrix or evaluation-report body within
#                     the v0.4.2 child closure.
#     case39..case48  inherited from v0.4.3 (R39..R48) — mutate the
#                     v0.4.3 records body or lifecycle report body
#                     within the v0.4.3 child closure.
#     case49  gold_reliance_package_index_not_object       (R49)
#     case50  gold_reliance_package_index_schema_invalid   (R50)
#     case51  gold_reliance_package_index_binding_invalid  (R51)
#     case52  gold_reliance_package_index_entry_invalid    (R52)
#     case53  gold_reliance_package_index_summary_invalid  (R53)
#     case54  gold_reliance_package_index_fingerprint_invalid (R54)
#
#   Pairwise 7-ID collision cases (21 = C(7,2); all route to R01):
#     col_01_02..col_06_07  Each manifest-level pairwise collision of
#                           the 7-member v0.4.4 collision class
#                           {conformance_report_id, decision_report_id,
#                            matrix_id, policy_evaluation_report_id,
#                            challenge_lifecycle_record_set_id,
#                            challenge_lifecycle_report_id,
#                            gold_reliance_package_index_id}.
#
#   Subject sub/reorder cases (5; all route to R01):
#     sub01  swap subjects[0] <-> subjects[1]
#     sub02  subjects[0]["role"] = wrong
#     sub03  subjects[0]["path"] = absolute
#     sub04  subjects[0]["path"] = traversal
#     sub05  subject count = 4 (drop subjects[4])
#
#   Supplementals (5; v0.4.4-owned reachability variants):
#     sup01  R50 stray top-level key in index body
#     sup02  R52 entries[0].child_subject_index = 99
#     sup03  R52 entries[0].child_manifest_fingerprint non-hex
#     sup04  R53 coverage_summary.package_id_anchor_consistency = false
#     sup05  R51 entries[1].child_manifest_fingerprint mutated to a
#            distinct-but-shape-valid bare-hex SHA-256
#            (mismatched with manifest.subjects[1].sha256)
#
#   Runner-only refusal cases (5 distinct reasons):
#     ro1   runner_input_path_missing       (omit --input-package)
#     ro2   runner_input_path_forbidden     (absolute --input-package)
#     ro3   runner_input_file_missing       (no-such-file.json)
#     ro4   runner_input_read_failed        (directory, portable)
#     ro5   runner_input_json_invalid       (bad-JSON repo-local file)
#
#   Runner-relay-of-verifier (rel01):
#     rel01  Structurally bad v0.4.0-shaped --input-package; --self-
#            validate relays the chained inherited verifier reason
#            (gold_package_schema_invalid) verbatim, unwrapped;
#            destination not made; no staging leak.
#
#   Environment-failure INFRA case (env01) — non-destructive trap:
#     env01  Copy the v0.4.4 verifier into a tempdir WITHOUT copying
#            its co-located inherited siblings. The copied v0.4.4
#            verifier resolves the inherited verifier paths relative
#            to its own __file__ and finds nothing, emitting
#            `INFRA: co-located v0.4.0 verifier unavailable...` on
#            stderr + exit 3. The real on-disk co-located verifiers
#            are NEVER touched, so SS equality is preserved.
#
#   Positive determinism (sup_det):
#     sup_det Rebuild the v0.4.4 package and confirm wrapping-manifest
#             subjects[0..4].sha256 and the index body
#             index_fingerprint are byte-identical across two builds.
#
#   Idempotency (idem01):
#     idem01  Build the v0.4.4 package into a v0.4.4-scratch-prefixed
#             --output-dir, then re-build into the SAME --output-dir
#             with --force. Proves the runner's output-dir overwrite
#             guard accepts BOTH /tmp/proofrail-v044-* and
#             /private/tmp/proofrail-v044-* (the macOS realpath form),
#             so a make-style demo target can re-run --force against
#             the same scratch path without a refuse.
#
#   No-residue (no_residue):
#     Scratch dir empty before EXIT trap; no v0.4.4 transient file
#     residue under any inherited-tier (v0.4.0/v0.4.1/v0.4.2/v0.4.3)
#     fixture, tool, or schema directory.
#
#   Taxonomy gate (TG1):
#     5-file exact-token scan of v0.4.4-owned source paths. Every
#     reason-shaped token must belong to the approved 54-reason
#     verifier set or the approved 5-reason runner-only set, plus a
#     narrow inherited data-field allowlist. Explicit deny-list of
#     environmental/wrapper escape patterns surfaces any drift toward
#     wrapping environment failures as public reasons.
#
#   Scoped SHA-256 snapshot (SS):
#     8-file scoped snapshot of v0.4.4-owned source paths + the three
#     inherited input fixtures (governed-reliance-scenarios.json,
#     policy-evaluation-matrix.json, challenge-lifecycle-records.json),
#     BEFORE and AFTER. Phase 3 performs no mutations on any of these
#     paths; the env01 trap is non-destructive and uses only a tempdir
#     copy of the v0.4.4 verifier.
#
# Notes on subprocess delegation:
#   The v0.4.4 verifier subprocess-invokes each of the four inherited
#   verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) on its corresponding
#   child wrapping-manifest path under child-packages/v0.4.X/. Each
#   inherited verifier resolves its referenced subject files relative
#   to the child manifest's directory. Any inherited verifier reason
#   is relayed verbatim with no rewriting, no narrowing, no INFRA:
#   collapse, and no sixth runner-only refusal. A missing inherited
#   verifier file or a non-FAIL non-zero inherited exit becomes
#   INFRA: + exit 3.
#
# Hash-first re-anchoring:
#   Every mutation that lives INSIDE an inherited closure body file
#   triggers a full cascade rebuild of (1) the corresponding child
#   wrapping manifest's subjects[].sha256/size_bytes; (2) the v0.4.4
#   wrapping manifest's subjects[0..3].sha256/size_bytes against the
#   newly-written child manifest file bytes; (3) the index body's
#   entries[0..3].child_manifest_fingerprint/size_bytes; (4) the
#   index body's index_fingerprint over canonical-JSON bytes of the
#   body with the index_fingerprint field excluded; (5) the v0.4.4
#   wrapping manifest's subjects[4].sha256/size_bytes against the
#   newly-written index body file bytes. Without this cascade, a
#   body-level mutation would be masked by the v0.4.4 manifest's
#   own subject-integrity check (R01) before the inherited verifier
#   subprocess can reach the targeted R-code. v0.4.4 uses BARE
#   lowercase hex SHA-256 (no `sha256:` label prefix) throughout.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/gold/build_gold_reliance_package_index_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_reliance_package_index_v0_1_0.py"

# Co-located inherited verifier paths (subprocess-invoked by the
# v0.4.4 verifier). Listed here only so the env01 isolated-copy
# exercise can confirm that ABSENCE of these siblings at __file__
# resolution time yields INFRA + exit 3.
V040_VERIFIER="$REPO_ROOT/tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py"
V041_VERIFIER="$REPO_ROOT/tools/gold/verify_gold_decision_report_hardening_v0_1_0.py"
V042_VERIFIER="$REPO_ROOT/tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py"
V043_VERIFIER="$REPO_ROOT/tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py"

# Three preflighted inputs accepted by the v0.4.4 runner.
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
MATRIX_FIX_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"
LIFECYCLE_FIX_REL="fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json"

# The v0.4.4 runner's --output-dir does NOT require the v0.4.4 scratch
# prefix on initial creation (only --force does). The runner's
# _output_dir_is_under_scratch_prefix() check accepts BOTH realpath
# forms (/tmp/proofrail-v044-* and /private/tmp/proofrail-v044-*) so a
# --force re-run against an existing v0.4.4-scratch-prefixed dir is
# accepted on both Linux and macOS. The 102 inherited cases below use
# unique per-case --output-dir paths under $WORK (no --force needed);
# the idem01 case below explicitly exercises the --force re-run path
# against a v0.4.4-scratch-prefixed dir to regression-cover the macOS
# /tmp -> /private/tmp realpath behavior in the prefix check. WORK is
# placed under /tmp with the v0.4.4 scratch marker for hygiene (so a
# crashed run leaves a clearly-attributable directory).
WORK="$(mktemp -d /tmp/proofrail-v044-test.XXXXXX)"

# Repo-local v0.4.4/test-owned scratch path for runner-input bad-input
# files (ro5, rel01). These files MUST live inside the repo because the
# runner's path preflight rejects absolute paths and traversal segments,
# which would otherwise mask the runner_input_json_invalid case (ro5)
# and the rel01 inherited-verifier relay case under
# runner_input_path_forbidden. The scratch path is NOT a v0.4.4-owned
# source path and is NOT in the scoped SS source-set. v0.4.4 transient
# files MUST NEVER be written under any inherited-tier (v0.4.0,
# v0.4.1, v0.4.2, v0.4.3) fixture, tool, or schema directory.
TMP_TEST_SCRATCH="$REPO_ROOT/tests/_tmp_gold_reliance_package_index_v0_4_4"
TMP_TEST_SCRATCH_REL="tests/_tmp_gold_reliance_package_index_v0_4_4"
if [ -e "$TMP_TEST_SCRATCH" ]; then
  echo "FAIL: test scratch path already exists at suite start:" >&2
  echo "  $TMP_TEST_SCRATCH" >&2
  echo "Refusing to silently reuse a stale scratch. Manual cleanup" >&2
  echo "required: remove $TMP_TEST_SCRATCH_REL and verify no untracked" >&2
  echo "residue (git status -sb) before re-running this suite." >&2
  exit 1
fi
mkdir -p "$TMP_TEST_SCRATCH"
trap 'rm -rf "$WORK" "$TMP_TEST_SCRATCH"' EXIT

GEN_AT="2026-11-01T00:30:00Z"
MANIFEST_ID="proofrail-gold-reliance-package-index-manifest-test-001"
CONFORMANCE_REPORT_ID="proofrail-gold-conformance-report-reliance-test-001"
DECISION_REPORT_ID="proofrail-gold-decision-report-demo-001"
POLICY_EVAL_REPORT_ID="proofrail-gold-policy-evaluation-report-demo-001"
CHALLENGE_LIFECYCLE_REPORT_ID="proofrail-gold-challenge-lifecycle-report-reliance-test-001"
GOLD_RELIANCE_PACKAGE_INDEX_ID="proofrail-gold-reliance-package-index-test-001"

# v0.4.4 wrapping-manifest filename and index body filename (mirror
# the runner / verifier module constants).
MANIFEST_REL_FILE="gold-reliance-package-index-manifest.json"
INDEX_BODY_REL_FILE="gold-reliance-package-index.json"

# Child closure roots and child wrapping-manifest filenames (mirror
# verifier / runner constants).
CHILD_DIR_V040="child-packages/v0.4.0"
CHILD_DIR_V041="child-packages/v0.4.1"
CHILD_DIR_V042="child-packages/v0.4.2"
CHILD_DIR_V043="child-packages/v0.4.3"

CHILD_MFST_V040="$CHILD_DIR_V040/gold-governed-reliance-package-manifest.json"
CHILD_MFST_V041="$CHILD_DIR_V041/gold-decision-report-package-manifest.json"
CHILD_MFST_V042="$CHILD_DIR_V042/gold-policy-evaluation-matrix-package-manifest.json"
CHILD_MFST_V043="$CHILD_DIR_V043/gold-challenge-lifecycle-package-manifest.json"

# Inherited subject body filenames (relative to each child closure).
# Discovered at runtime via the child wrapping manifest; these names
# are also enumerated here for direct mutation by the canonical case
# helpers. The v0.4.0 child closure ships 2 subjects; v0.4.1 ships
# 3; v0.4.2 ships 5; v0.4.3 ships 7 (per the inherited release
# layouts).
V040_PKG_BODY="$CHILD_DIR_V040/governed-reliance-scenarios.json"
V041_DECISION_BODY="$CHILD_DIR_V041/gold-governed-reliance-decision-report.json"
V042_MATRIX_BODY="$CHILD_DIR_V042/gold-policy-evaluation-matrix.json"
V042_EVAL_BODY="$CHILD_DIR_V042/gold-policy-evaluation-report.json"
V043_RECORDS_BODY="$CHILD_DIR_V043/challenge-lifecycle-records.json"
V043_REPORT_BODY="$CHILD_DIR_V043/gold-challenge-lifecycle-report.json"

# --- Scoped sha256 snapshot of committed v0.4.4-owned source paths +
# inherited input fixtures (BEFORE). Phase 3 performs no mutations on
# any of these 8 paths; the BEFORE/AFTER snapshot must be byte-
# identical. The committed Makefile is excluded; it is shared across
# release versions and is mutated independently by future amendments.
SCOPED_FILES=(
  "schemas/gold-reliance-package-index-manifest-v0.1.0.md"
  "schemas/gold-reliance-package-index-v0.1.0.md"
  "tools/gold/build_gold_reliance_package_index_v0_1_0.py"
  "tools/gold/verify_gold_reliance_package_index_v0_1_0.py"
  "tests/test_gold_reliance_package_index_v0_4_4.sh"
  "fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
  "fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"
  "fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json"
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

# --- Counters ----------------------------------------------------------------

PASS_COUNT=0
EXPECTED_COUNT=103

note_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS %3d/%d  %s\n' "$PASS_COUNT" "$EXPECTED_COUNT" "$1"
}

die() {
  echo "FAIL (test-harness): $*" >&2
  exit 1
}

# --- File hashing helpers ----------------------------------------------------

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

# --- Pristine build + fresh_copy ---------------------------------------------
# Build the canonical reference package exactly once; subsequent
# cases copy it. Avoid --force entirely (macOS realpath /tmp ->
# /private/tmp would defeat the runner's scratch-prefix check).

PRISTINE="$WORK/pristine"

build_pristine() {
  # Inputs must be RELATIVE per runner_input_path_forbidden;
  # harness has already `cd`'d to $REPO_ROOT.
  python3 "$RUNNER" \
    --input-package    "$PACKAGE_FIX_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                       "$MANIFEST_ID" \
    --conformance-report-id             "$CONFORMANCE_REPORT_ID" \
    --decision-report-id                "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id       "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id     "$CHALLENGE_LIFECYCLE_REPORT_ID" \
    --gold-reliance-package-index-id    "$GOLD_RELIANCE_PACKAGE_INDEX_ID" \
    --generated-at                      "$GEN_AT" \
    --output-dir                        "$PRISTINE" \
    >"$WORK/pristine.build.log" 2>&1 \
    || { cat "$WORK/pristine.build.log" >&2; die "pristine build failed"; }
}

# Make a fresh per-case copy of the pristine package. Caller supplies
# a unique destination directory under $WORK (so the runner-side path
# checks never matter; the copy is a passive duplicate, not a runner
# output).
fresh_copy() {
  local dest="$1"
  [ -e "$dest" ] && rm -rf "$dest"
  cp -R "$PRISTINE" "$dest"
}

# --- Cascade rebuild ---------------------------------------------------------
# Re-canonicalize every manifest and recompute every subject hash so
# the package is self-consistent under the v0.4.4 + inherited
# discipline:
#
#   * For each child closure (v0.4.0..v0.4.3): rehash all
#     child-manifest subject hashes from the on-disk bodies. v0.4.0
#     child uses the legacy 'sha256:' prefix; v0.4.1/2/3 use bare
#     lowercase hex. No child manifest carries a manifest-level
#     fingerprint.
#   * v0.4.4 wrapping manifest subjects[0..3]: rehash each child
#     manifest file with bare hex.
#   * v0.4.4 index body entries[0..3].child_manifest_fingerprint +
#     .child_manifest_size_bytes: byte-match subjects[0..3].
#   * v0.4.4 index body index_fingerprint: SHA-256 of
#     json.dumps(body_without_index_fingerprint, sort_keys=True,
#     separators=(',',':')).encode('utf-8'); no trailing newline in
#     the fingerprint domain.
#   * v0.4.4 wrapping manifest subjects[4]: rehash the index body
#     file (bare hex).
#
# All canonical-JSON outputs use sort_keys=True,
# separators=(',',':'), and end with a single trailing newline,
# matching the runner's serialization.
cascade_rebuild() {
  local root="$1"
  python3 - "$root" << 'PYEOF'
import hashlib, json, os, sys
ROOT = sys.argv[1]
def cj_bytes(o):
    return json.dumps(o, sort_keys=True, separators=(",",":")).encode("utf-8")
def write_canonical(p, o):
    with open(p, "wb") as f:
        f.write(cj_bytes(o)); f.write(b"\n")
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""): h.update(c)
    return h.hexdigest()
def size_file(p): return os.path.getsize(p)
CHILD = [
    ("v0.4.0", "gold-governed-reliance-package-manifest.json", True),
    ("v0.4.1", "gold-decision-report-package-manifest.json",    False),
    ("v0.4.2", "gold-policy-evaluation-matrix-package-manifest.json", False),
    ("v0.4.3", "gold-challenge-lifecycle-package-manifest.json", False),
]
# Step 1: rehash child-manifest subjects from on-disk bodies
for ver, name, prefixed in CHILD:
    cdir  = os.path.join(ROOT, "child-packages", ver)
    cmfst = os.path.join(cdir, name)
    j = json.load(open(cmfst))
    for s in j["subjects"]:
        body = os.path.join(cdir, s["path"])
        h = sha256_file(body)
        s["sha256"] = ("sha256:" + h) if prefixed else h
        s["size_bytes"] = size_file(body)
    write_canonical(cmfst, j)
# Step 2: load v0.4.4 manifest + index body
m_path  = os.path.join(ROOT, "gold-reliance-package-index-manifest.json")
ib_path = os.path.join(ROOT, "gold-reliance-package-index.json")
m  = json.load(open(m_path))
ib = json.load(open(ib_path))
# Step 3: rehash subjects[0..3] (child manifests) on both layers
for i, (ver, name, _) in enumerate(CHILD):
    cmfst = os.path.join(ROOT, "child-packages", ver, name)
    h = sha256_file(cmfst); sz = size_file(cmfst)
    m["subjects"][i]["sha256"]    = h
    m["subjects"][i]["size_bytes"] = sz
    ib["entries"][i]["child_manifest_fingerprint"] = h
    ib["entries"][i]["child_manifest_size_bytes"]  = sz
# Step 4: recompute index_fingerprint (no trailing newline; key excluded)
ib_no_fp = {k: v for k, v in ib.items() if k != "index_fingerprint"}
ib["index_fingerprint"] = hashlib.sha256(cj_bytes(ib_no_fp)).hexdigest()
write_canonical(ib_path, ib)
# Step 5: rehash subjects[4] (index body)
m["subjects"][4]["sha256"]    = sha256_file(ib_path)
m["subjects"][4]["size_bytes"] = size_file(ib_path)
# Step 6: write v0.4.4 wrapping manifest
write_canonical(m_path, m)
PYEOF
}

# --- Expectation helpers -----------------------------------------------------
# All four helpers capture combined stdout+stderr to $WORK/last.out
# and assert exit-code + first-line discipline. None of them echo
# subprocess output to the test's stdout; failures dump captured
# output via die() for diagnosis. The first-line FAIL/PASS/INFRA
# discipline matches the verifier/runner contract:
#
#   verifier PASS  : exit 0, first line '^PASS\b'
#   verifier FAIL  : exit 1, first line '^FAIL: REASON: <reason>'
#   runner   PASS  : exit 0 (no per-line discipline asserted)
#   runner   FAIL  : exit 1, first line '^FAIL: REASON: <reason>'
#   runner   INFRA : exit 3, first line '^INFRA:'

expect_verifier_pass() {
  local label="$1"; shift
  if "$@" >"$WORK/last.out" 2>&1; then
    head -n1 "$WORK/last.out" | grep -qE '^PASS\b' \
      || { cat "$WORK/last.out" >&2; die "$label: verifier PASS expected, first line wrong"; }
    grep -qE '^FAIL: ' "$WORK/last.out" \
      && { cat "$WORK/last.out" >&2; die "$label: verifier PASS but FAIL line present"; }
    grep -qE '^INFRA:' "$WORK/last.out" \
      && { cat "$WORK/last.out" >&2; die "$label: verifier PASS but INFRA line present"; }
    grep -qE 'Traceback' "$WORK/last.out" \
      && { cat "$WORK/last.out" >&2; die "$label: verifier PASS but Traceback present"; }
    note_pass "$label"
  else
    local rc=$?
    cat "$WORK/last.out" >&2
    die "$label: verifier PASS expected, got exit=$rc"
  fi
}

expect_verifier_fail() {
  local label="$1"; local reason="$2"; shift 2
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  [ "$rc" -eq 0 ] \
    && { cat "$WORK/last.out" >&2; die "$label: verifier FAIL expected (reason=$reason), got exit=0"; }
  head -n1 "$WORK/last.out" \
    | grep -qE "^FAIL: $reason([[:space:]:]|\$)" \
    || { cat "$WORK/last.out" >&2; die "$label: first line not 'FAIL: $reason'"; }
  grep -qE '^INFRA:' "$WORK/last.out" \
    && { cat "$WORK/last.out" >&2; die "$label: verifier FAIL but INFRA present"; }
  grep -qE 'Traceback' "$WORK/last.out" \
    && { cat "$WORK/last.out" >&2; die "$label: verifier FAIL but Traceback present"; }
  note_pass "$label"
}

expect_runner_fail() {
  local label="$1"; local reason="$2"; local outdir="$3"; shift 3
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  [ "$rc" -eq 1 ] \
    || { cat "$WORK/last.out" >&2; die "$label: runner FAIL exit=1 expected, got $rc"; }
  head -n1 "$WORK/last.out" \
    | grep -qE "^FAIL: $reason([[:space:]:]|\$)" \
    || { cat "$WORK/last.out" >&2; die "$label: first line not 'FAIL: $reason'"; }
  grep -qE 'Traceback' "$WORK/last.out" \
    && { cat "$WORK/last.out" >&2; die "$label: runner FAIL but Traceback present"; }
  if [ -n "$outdir" ] && [ -e "$outdir" ]; then
    die "$label: runner FAIL but output dir $outdir exists"
  fi
  # Staging leak guard: no '*.staging-*' anywhere under $WORK.
  if find "$WORK" -maxdepth 4 -name '*.staging-*' -print -quit 2>/dev/null | grep -q .; then
    die "$label: runner FAIL but staging dir leaked under \$WORK"
  fi
  note_pass "$label"
}

expect_runner_infra() {
  local label="$1"; local infra_re="$2"; local outdir="$3"; shift 3
  local rc
  if "$@" >"$WORK/last.out" 2>&1; then rc=0; else rc=$?; fi
  [ "$rc" -eq 3 ] \
    || { cat "$WORK/last.out" >&2; die "$label: runner INFRA exit=3 expected, got $rc"; }
  head -n1 "$WORK/last.out" \
    | grep -qE "^INFRA:[[:space:]]" \
    || { cat "$WORK/last.out" >&2; die "$label: first line not 'INFRA: ...'"; }
  head -n1 "$WORK/last.out" \
    | grep -qE "$infra_re" \
    || { cat "$WORK/last.out" >&2; die "$label: INFRA line does not match: $infra_re"; }
  grep -qE 'Traceback' "$WORK/last.out" \
    && { cat "$WORK/last.out" >&2; die "$label: runner INFRA but Traceback present"; }
  if [ -n "$outdir" ] && [ -e "$outdir" ]; then
    die "$label: runner INFRA but output dir $outdir exists"
  fi
  note_pass "$label"
}

# Build the pristine reference package now so per-case fresh_copy()
# calls are cheap.
build_pristine

# -----------------------------------------------------------------------------
# Subject-4-only rehash helper (used by Phase-3 cases that mutate the
# index body and need R01 / cross-anchor checks to pass so the
# verifier reaches Phase 3 R49..R54). Does NOT recompute
# index_fingerprint; for fingerprint cases the caller mutates the
# fingerprint explicitly and then calls rehash_subject4.
# -----------------------------------------------------------------------------
rehash_subject4() {
  local root="$1"
  python3 - "$root" << 'PYEOF'
import json, hashlib, os, sys
ROOT = sys.argv[1]
m_path  = os.path.join(ROOT, "gold-reliance-package-index-manifest.json")
ib_path = os.path.join(ROOT, "gold-reliance-package-index.json")
m = json.load(open(m_path))
h = hashlib.sha256()
with open(ib_path, "rb") as f:
    for c in iter(lambda: f.read(65536), b""): h.update(c)
m["subjects"][4]["sha256"]    = h.hexdigest()
m["subjects"][4]["size_bytes"] = os.path.getsize(ib_path)
with open(m_path, "wb") as f:
    f.write(json.dumps(m, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# Common runner-invocation wrapper for ro2..ro5; differs only in the
# --input-package value. Caller supplies LABEL, REASON, OUTDIR, and
# INPUT_PACKAGE (relative path); helper supplies a unique tag suffix
# for the collision-class IDs so re-runs do not collide.
_ro_invoke() {
  local label="$1"; local reason="$2"; local outdir="$3"
  local input_package="$4"; local tag="$5"
  expect_runner_fail "$label" "$reason" "$outdir" \
    python3 "$RUNNER" \
      --input-package    "$input_package" \
      --matrix-input     "$MATRIX_FIX_REL" \
      --lifecycle-input  "$LIFECYCLE_FIX_REL" \
      --manifest-id                    "$MANIFEST_ID-$tag" \
      --conformance-report-id          "$CONFORMANCE_REPORT_ID-$tag" \
      --decision-report-id             "$DECISION_REPORT_ID" \
      --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID" \
      --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-$tag" \
      --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-$tag" \
      --generated-at                   "$GEN_AT" \
      --output-dir                     "$outdir"
}

# =============================================================================
# Subphase 3B: PP1..PP6 + case49..case54 + ro1..ro5 + env01
# =============================================================================

# --- PP1: pristine verifier PASS ---
expect_verifier_pass "PP1 pristine_verifier_pass" \
  python3 "$VERIFIER" --manifest "$PRISTINE/gold-reliance-package-index-manifest.json"

# --- PP2: fresh_copy then verifier PASS ---
PP2="$WORK/pp2"; fresh_copy "$PP2"
expect_verifier_pass "PP2 fresh_copy_verifier_pass" \
  python3 "$VERIFIER" --manifest "$PP2/gold-reliance-package-index-manifest.json"

# --- PP3: cascade_rebuild on fresh copy then verifier PASS ---
PP3="$WORK/pp3"; fresh_copy "$PP3"; cascade_rebuild "$PP3"
expect_verifier_pass "PP3 cascade_rebuild_verifier_pass" \
  python3 "$VERIFIER" --manifest "$PP3/gold-reliance-package-index-manifest.json"

# --- PP4: runner --self-validate exits 0 ---
PP4_OUT="$WORK/pp4-out"
if python3 "$RUNNER" \
    --input-package    "$PACKAGE_FIX_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID-pp4" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID-pp4" \
    --decision-report-id             "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-pp4" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-pp4" \
    --generated-at                   "$GEN_AT" \
    --output-dir                     "$PP4_OUT" \
    --self-validate >"$WORK/pp4.out" 2>&1; then
  note_pass "PP4 runner_self_validate_exit0"
else
  cat "$WORK/pp4.out" >&2
  die "PP4: runner --self-validate non-zero exit"
fi

# --- PP5: alternate --generated-at produces a verifying package ---
PP5_OUT="$WORK/pp5-out"
if python3 "$RUNNER" \
    --input-package    "$PACKAGE_FIX_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID-pp5" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID-pp5" \
    --decision-report-id             "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-pp5" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-pp5" \
    --generated-at                   "2026-11-02T00:30:00Z" \
    --output-dir                     "$PP5_OUT" >"$WORK/pp5.build.out" 2>&1; then
  : OK
else
  cat "$WORK/pp5.build.out" >&2
  die "PP5: alt gen_at build failed"
fi
expect_verifier_pass "PP5 alt_gen_at_verifier_pass" \
  python3 "$VERIFIER" --manifest "$PP5_OUT/gold-reliance-package-index-manifest.json"

# --- PP6: cascade_rebuild is byte-idempotent ---
PP6="$WORK/pp6"; fresh_copy "$PP6"; cascade_rebuild "$PP6"
PP6_SHA_FIRST=$(file_sha256 "$PP6/gold-reliance-package-index-manifest.json")
PP6_IB_FIRST=$(file_sha256 "$PP6/gold-reliance-package-index.json")
cascade_rebuild "$PP6"
PP6_SHA_SECOND=$(file_sha256 "$PP6/gold-reliance-package-index-manifest.json")
PP6_IB_SECOND=$(file_sha256 "$PP6/gold-reliance-package-index.json")
[ "$PP6_SHA_FIRST" = "$PP6_SHA_SECOND" ] \
  || die "PP6: manifest changed across cascade: $PP6_SHA_FIRST vs $PP6_SHA_SECOND"
[ "$PP6_IB_FIRST"  = "$PP6_IB_SECOND" ] \
  || die "PP6: index body changed across cascade: $PP6_IB_FIRST vs $PP6_IB_SECOND"
note_pass "PP6 cascade_rebuild_byte_idempotent"

# -----------------------------------------------------------------------------
# case49..case54: v0.4.4-owned reasons R49..R54
# -----------------------------------------------------------------------------

# case49 R49 not_object: replace index body with a JSON array
C49="$WORK/case49"; fresh_copy "$C49"
printf '[]\n' > "$C49/gold-reliance-package-index.json"
rehash_subject4 "$C49"
expect_verifier_fail "case49 R49 not_object" \
  "gold_reliance_package_index_not_object" \
  python3 "$VERIFIER" --manifest "$C49/gold-reliance-package-index-manifest.json"

# case50 R50 schema_invalid: remove required top-level field document_type
C50="$WORK/case50"; fresh_copy "$C50"
python3 - "$C50/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
del ib["document_type"]
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_subject4 "$C50"
expect_verifier_fail "case50 R50 schema_invalid_missing_document_type" \
  "gold_reliance_package_index_schema_invalid" \
  python3 "$VERIFIER" --manifest "$C50/gold-reliance-package-index-manifest.json"

# case51 R51 binding_invalid: body.package_id != manifest.package_id
C51="$WORK/case51"; fresh_copy "$C51"
python3 - "$C51/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["package_id"] = "proofrail-bogus-distinct-package-id"
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_subject4 "$C51"
expect_verifier_fail "case51 R51 binding_invalid_package_id" \
  "gold_reliance_package_index_binding_invalid" \
  python3 "$VERIFIER" --manifest "$C51/gold-reliance-package-index-manifest.json"

# case52 R52 entry_invalid: entries[0].child_subject_index=9 (must be 0)
C52="$WORK/case52"; fresh_copy "$C52"
python3 - "$C52/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["entries"][0]["child_subject_index"] = 9
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_subject4 "$C52"
expect_verifier_fail "case52 R52 entry_invalid_child_subject_index" \
  "gold_reliance_package_index_entry_invalid" \
  python3 "$VERIFIER" --manifest "$C52/gold-reliance-package-index-manifest.json"

# case53 R53 summary_invalid: coverage_summary.child_package_count=3
C53="$WORK/case53"; fresh_copy "$C53"
python3 - "$C53/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["coverage_summary"]["child_package_count"] = 3
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_subject4 "$C53"
expect_verifier_fail "case53 R53 summary_invalid_child_package_count" \
  "gold_reliance_package_index_summary_invalid" \
  python3 "$VERIFIER" --manifest "$C53/gold-reliance-package-index-manifest.json"

# case54 R54 fingerprint_invalid: flip one nibble of index_fingerprint
C54="$WORK/case54"; fresh_copy "$C54"
python3 - "$C54/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
fp = ib["index_fingerprint"]
flipped = ("f" if fp[0] != "f" else "0") + fp[1:]
ib["index_fingerprint"] = flipped
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_subject4 "$C54"
expect_verifier_fail "case54 R54 fingerprint_invalid" \
  "gold_reliance_package_index_fingerprint_invalid" \
  python3 "$VERIFIER" --manifest "$C54/gold-reliance-package-index-manifest.json"

# -----------------------------------------------------------------------------
# ro1..ro5: runner-only refusals (exit 1, no Traceback, no output dir)
# -----------------------------------------------------------------------------

# ro1 PATH_MISSING: omit --input-package entirely
RO1_OUT="$WORK/ro1-out"
expect_runner_fail "ro1 runner_input_path_missing" "runner_input_path_missing" "$RO1_OUT" \
  python3 "$RUNNER" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID-ro1" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID-ro1" \
    --decision-report-id             "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-ro1" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-ro1" \
    --generated-at                   "$GEN_AT" \
    --output-dir                     "$RO1_OUT"

# ro2 PATH_FORBIDDEN: absolute --input-package
RO2_OUT="$WORK/ro2-out"
_ro_invoke "ro2 runner_input_path_forbidden_absolute" \
  "runner_input_path_forbidden" "$RO2_OUT" \
  "$REPO_ROOT/$PACKAGE_FIX_REL" "ro2"

# ro3 FILE_MISSING: relative path to a non-existent file
RO3_OUT="$WORK/ro3-out"
_ro_invoke "ro3 runner_input_file_missing" \
  "runner_input_file_missing" "$RO3_OUT" \
  "$TMP_TEST_SCRATCH_REL/no_such_file.json" "ro3"

# ro4 READ_FAILED: relative path that is a directory
mkdir -p "$TMP_TEST_SCRATCH/ro4_dir"
RO4_OUT="$WORK/ro4-out"
_ro_invoke "ro4 runner_input_read_failed_directory" \
  "runner_input_read_failed" "$RO4_OUT" \
  "$TMP_TEST_SCRATCH_REL/ro4_dir" "ro4"

# ro5 JSON_INVALID: file exists but contents are not valid JSON
printf 'not valid json {' > "$TMP_TEST_SCRATCH/ro5_bad.json"
RO5_OUT="$WORK/ro5-out"
_ro_invoke "ro5 runner_input_json_invalid" \
  "runner_input_json_invalid" "$RO5_OUT" \
  "$TMP_TEST_SCRATCH_REL/ro5_bad.json" "ro5"

# -----------------------------------------------------------------------------
# env01: INFRA exit 3 when a co-located inherited verifier is missing
# -----------------------------------------------------------------------------
# Operate on an ISOLATED copy of the v0.4.4 verifier so the real
# tools/gold/ tree is untouched. The inherited verifiers are NOT
# copied; v0.4.0 is checked first, so INFRA names v0.4.0.

ENV01_TOOLS="$WORK/env01-tools"
mkdir -p "$ENV01_TOOLS"
cp "$VERIFIER" "$ENV01_TOOLS/verify_gold_reliance_package_index_v0_1_0.py"
expect_runner_infra "env01 infra_missing_v0_4_0_verifier" \
  "co-located v0\\.4\\.0 verifier unavailable" "" \
  python3 "$ENV01_TOOLS/verify_gold_reliance_package_index_v0_1_0.py" \
    --manifest "$PRISTINE/gold-reliance-package-index-manifest.json"

# ---------------------------------------------------------------------------
# 3C helpers: edit one body or manifest within a v0.4.4 child closure.
# Caller is responsible for calling cascade_rebuild afterwards (except
# for case01 which intentionally avoids cascade so v0.4.4 R01 fires).
# ---------------------------------------------------------------------------

_edit_json_canonical() {
  # $1=file_path  $2=python_expr (operates on dict-or-list `o`)
  python3 - "$1" "$2" <<'PYEOF'
import json, sys
p = sys.argv[1]; expr = sys.argv[2]
with open(p) as f: o = json.load(f)
exec(expr, {"o": o, "m": o, "pkg": o, "d": o, "x": o, "e": o, "r": o, "l": o, "json": json})
with open(p, "wb") as f:
    f.write(json.dumps(o, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

edit_v044_manifest()  { _edit_json_canonical "$1/gold-reliance-package-index-manifest.json" "$2"; }
edit_v040_body()      { _edit_json_canonical "$1/child-packages/v0.4.0/governed-reliance-scenarios.json" "$2"; }
edit_v041_decision()  { _edit_json_canonical "$1/child-packages/v0.4.1/gold-governed-reliance-decision-report.json" "$2"; }
edit_v042_matrix()    { _edit_json_canonical "$1/child-packages/v0.4.2/gold-policy-evaluation-matrix.json" "$2"; }
edit_v042_eval()      { _edit_json_canonical "$1/child-packages/v0.4.2/gold-policy-evaluation-report.json" "$2"; }
edit_v043_records()   { _edit_json_canonical "$1/child-packages/v0.4.3/challenge-lifecycle-records.json" "$2"; }
edit_v043_lreport()   { _edit_json_canonical "$1/child-packages/v0.4.3/gold-challenge-lifecycle-report.json" "$2"; }

_replace_body_with_array() {
  # $1=file_path. Writes top-level JSON array so verifier R(not_object) fires.
  python3 -c "
import json
with open('$1','w') as f: f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
}

_v044_verifier_cmd() {
  # Helper: emits the v0.4.4 verifier command for a given package root.
  echo "python3 $VERIFIER --manifest $1/gold-reliance-package-index-manifest.json"
}

# ---------------------------------------------------------------------------
# 3C: 48 inherited canonical relay cases (case01..case48).
#
# case01 trips v0.4.4's OWN R01 (no cascade). case02..case48 trip the
# matching inherited reason via subprocess relay (cascade_rebuild
# preserves all v0.4.4 manifest + cross-anchor + index body invariants
# so the verifier reaches Phase 4 cleanly).
# ---------------------------------------------------------------------------

# --- case01: R01 gold_manifest_invalid (v0.4.4 own check) -------------------
T="$WORK/case01"; fresh_copy "$T"
edit_v044_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01 R01 gold_manifest_invalid" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case02: R02 gold_package_not_object (v0.4.0 relay) --------------------
T="$WORK/case02"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.0/governed-reliance-scenarios.json"
cascade_rebuild "$T"
expect_verifier_fail "case02 R02 gold_package_not_object" "gold_package_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case03: R03 gold_package_schema_invalid -------------------------------
T="$WORK/case03"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case03 R03 gold_package_schema_invalid" "gold_package_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case04: R04 gold_profile_unsupported ----------------------------------
T="$WORK/case04"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["profile"] = "some.other.profile"'
cascade_rebuild "$T"
expect_verifier_fail "case04 R04 gold_profile_unsupported" "gold_profile_unsupported" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case05: R05 gold_package_identity_invalid -----------------------------
# v0.4.0 R05 covers several identity-grammar fields. Use body-only
# mutation (display_name empty) so v0.4.4 Phase 1/2 cross-anchors stay
# intact and the v0.4.0 verifier reaches its R05 fold.
T="$WORK/case05"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["relying_party"]["display_name"] = ""'
cascade_rebuild "$T"
expect_verifier_fail "case05 R05 gold_package_identity_invalid" "gold_package_identity_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case06: R06 silver_verification_input_invalid -------------------------
T="$WORK/case06"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["inputs"]["silver_verification"]["input_type"] = "not_a_type"'
cascade_rebuild "$T"
expect_verifier_fail "case06 R06 silver_verification_input_invalid" "silver_verification_input_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case07: R07 silver_handoff_input_invalid ------------------------------
T="$WORK/case07"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["inputs"]["silver_handoff"].pop("expected_handoff_posture")'
cascade_rebuild "$T"
expect_verifier_fail "case07 R07 silver_handoff_input_invalid" "silver_handoff_input_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case08: R08 policy_pack_input_invalid ---------------------------------
T="$WORK/case08"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["inputs"]["policy_pack"].pop("policy_pack_version")'
cascade_rebuild "$T"
expect_verifier_fail "case08 R08 policy_pack_input_invalid" "policy_pack_input_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case09: R09 registry_lite_input_invalid -------------------------------
T="$WORK/case09"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["inputs"]["registry_lite"]["registry_id"] = "BadID"'
cascade_rebuild "$T"
expect_verifier_fail "case09 R09 registry_lite_input_invalid" "registry_lite_input_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case10: R10 control_crosswalk_input_invalid ---------------------------
T="$WORK/case10"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["inputs"]["control_crosswalk"].pop("control_pack_id")'
cascade_rebuild "$T"
expect_verifier_fail "case10 R10 control_crosswalk_input_invalid" "control_crosswalk_input_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case11: R11 governed_decision_set_invalid -----------------------------
T="$WORK/case11"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"] = []'
cascade_rebuild "$T"
expect_verifier_fail "case11 R11 governed_decision_set_invalid" "governed_decision_set_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case12: R12 governed_decision_entry_invalid ---------------------------
T="$WORK/case12"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0].pop("decision_id")'
cascade_rebuild "$T"
expect_verifier_fail "case12 R12 governed_decision_entry_invalid" "governed_decision_entry_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case13: R13 decision_subject_binding_invalid --------------------------
T="$WORK/case13"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["decision_subject"]["subject_ref"] = "unknown-subject-ref-001"'
cascade_rebuild "$T"
expect_verifier_fail "case13 R13 decision_subject_binding_invalid" "decision_subject_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case14: R14 decision_policy_binding_invalid ---------------------------
T="$WORK/case14"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["policy_binding"]["policy_pack_id"] = "policy-pack-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case14 R14 decision_policy_binding_invalid" "decision_policy_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case15: R15 decision_registry_binding_invalid -------------------------
T="$WORK/case15"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["registry_binding"]["decision_authority_role"] = "not_a_role"'
cascade_rebuild "$T"
expect_verifier_fail "case15 R15 decision_registry_binding_invalid" "decision_registry_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case16: R16 decision_action_scope_invalid -----------------------------
T="$WORK/case16"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["action_scope"]["protected_action_id"] = "not_a_protected_action"'
cascade_rebuild "$T"
expect_verifier_fail "case16 R16 decision_action_scope_invalid" "decision_action_scope_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case17: R17 decision_status_invalid -----------------------------------
T="$WORK/case17"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["decision_status"] = "maybe"'
cascade_rebuild "$T"
expect_verifier_fail "case17 R17 decision_status_invalid" "decision_status_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case18: R18 acceptance_path_invalid -----------------------------------
T="$WORK/case18"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][0]["scenario_specific_state"]["acceptance_record_ref"] = ""'
cascade_rebuild "$T"
expect_verifier_fail "case18 R18 acceptance_path_invalid" "acceptance_path_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case19: R19 rejection_path_invalid ------------------------------------
T="$WORK/case19"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][1]["scenario_specific_state"]["silver_verification_passing"] = False'
cascade_rebuild "$T"
expect_verifier_fail "case19 R19 rejection_path_invalid" "rejection_path_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case20: R20 challenge_path_invalid ------------------------------------
T="$WORK/case20"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][2]["scenario_specific_state"]["challenge_state"] = "not_a_state"'
cascade_rebuild "$T"
expect_verifier_fail "case20 R20 challenge_path_invalid" "challenge_path_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case21: R21 withdrawal_path_invalid -----------------------------------
T="$WORK/case21"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][3]["scenario_specific_state"]["withdrawal_trigger"] = "random"'
cascade_rebuild "$T"
expect_verifier_fail "case21 R21 withdrawal_path_invalid" "withdrawal_path_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case22: R22 supersession_path_invalid ---------------------------------
T="$WORK/case22"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["governed_decisions"][4]["scenario_specific_state"]["prior_decision_id"] = "nonexistent"'
cascade_rebuild "$T"
expect_verifier_fail "case22 R22 supersession_path_invalid" "supersession_path_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case23: R23 non_claims_missing ----------------------------------------
T="$WORK/case23"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["non_claims"] = []'
cascade_rebuild "$T"
expect_verifier_fail "case23 R23 non_claims_missing" "non_claims_missing" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case24: R24 prohibited_gold_claim_present -----------------------------
T="$WORK/case24"; fresh_copy "$T"
edit_v040_body "$T" 'pkg["relying_party"]["display_name"] = "Demo Local Relying Party (full Gold certified)"'
cascade_rebuild "$T"
expect_verifier_fail "case24 R24 prohibited_gold_claim_present" "prohibited_gold_claim_present" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case25: R25 gold_decision_report_not_object (v0.4.1 relay) ------------
T="$WORK/case25"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.1/gold-governed-reliance-decision-report.json"
cascade_rebuild "$T"
expect_verifier_fail "case25 R25 gold_decision_report_not_object" "gold_decision_report_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case26: R26 gold_decision_report_schema_invalid -----------------------
T="$WORK/case26"; fresh_copy "$T"
edit_v041_decision "$T" 'd["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case26 R26 gold_decision_report_schema_invalid" "gold_decision_report_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case27: R27 gold_decision_report_binding_invalid ----------------------
T="$WORK/case27"; fresh_copy "$T"
edit_v041_decision "$T" 'd["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case27 R27 gold_decision_report_binding_invalid" "gold_decision_report_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case28: R28 gold_decision_report_projection_invalid -------------------
T="$WORK/case28"; fresh_copy "$T"
edit_v041_decision "$T" 'd["decision_rows"][0]["decision_status"] = "rejected"'
cascade_rebuild "$T"
expect_verifier_fail "case28 R28 gold_decision_report_projection_invalid" "gold_decision_report_projection_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case29: R29 gold_decision_report_summary_invalid ----------------------
T="$WORK/case29"; fresh_copy "$T"
edit_v041_decision "$T" 'd["coverage_summary"]["decision_count"] = 42'
cascade_rebuild "$T"
expect_verifier_fail "case29 R29 gold_decision_report_summary_invalid" "gold_decision_report_summary_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case30: R30 gold_policy_matrix_not_object (v0.4.2 relay) --------------
T="$WORK/case30"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.2/gold-policy-evaluation-matrix.json"
cascade_rebuild "$T"
expect_verifier_fail "case30 R30 gold_policy_matrix_not_object" "gold_policy_matrix_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case31: R31 gold_policy_matrix_schema_invalid -------------------------
T="$WORK/case31"; fresh_copy "$T"
edit_v042_matrix "$T" 'x["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case31 R31 gold_policy_matrix_schema_invalid" "gold_policy_matrix_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case32: R32 gold_policy_matrix_binding_invalid ------------------------
T="$WORK/case32"; fresh_copy "$T"
edit_v042_matrix "$T" 'x["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case32 R32 gold_policy_matrix_binding_invalid" "gold_policy_matrix_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case33: R33 gold_policy_matrix_entry_invalid --------------------------
T="$WORK/case33"; fresh_copy "$T"
edit_v042_matrix "$T" 'x["matrix_rows"][0]["matrix_row_id"] = "mrow_05"'
cascade_rebuild "$T"
expect_verifier_fail "case33 R33 gold_policy_matrix_entry_invalid" "gold_policy_matrix_entry_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case34: R34 gold_policy_evaluation_report_not_object ------------------
T="$WORK/case34"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.2/gold-policy-evaluation-report.json"
cascade_rebuild "$T"
expect_verifier_fail "case34 R34 gold_policy_evaluation_report_not_object" "gold_policy_evaluation_report_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case35: R35 gold_policy_evaluation_report_schema_invalid --------------
T="$WORK/case35"; fresh_copy "$T"
edit_v042_eval "$T" 'e["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case35 R35 gold_policy_evaluation_report_schema_invalid" "gold_policy_evaluation_report_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case36: R36 gold_policy_evaluation_report_binding_invalid -------------
T="$WORK/case36"; fresh_copy "$T"
edit_v042_eval "$T" 'e["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case36 R36 gold_policy_evaluation_report_binding_invalid" "gold_policy_evaluation_report_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case37: R37 gold_policy_evaluation_result_invalid ---------------------
T="$WORK/case37"; fresh_copy "$T"
edit_v042_eval "$T" 'e["evaluation_rows"][0]["decision_status"] = "rejected"'
cascade_rebuild "$T"
expect_verifier_fail "case37 R37 gold_policy_evaluation_result_invalid" "gold_policy_evaluation_result_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case38: R38 gold_policy_evaluation_summary_invalid --------------------
T="$WORK/case38"; fresh_copy "$T"
edit_v042_eval "$T" 'e["coverage_summary"]["matched_count"] = 42'
cascade_rebuild "$T"
expect_verifier_fail "case38 R38 gold_policy_evaluation_summary_invalid" "gold_policy_evaluation_summary_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case39: R39 gold_challenge_lifecycle_records_not_object (v0.4.3 relay) -
T="$WORK/case39"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.3/challenge-lifecycle-records.json"
cascade_rebuild "$T"
expect_verifier_fail "case39 R39 gold_challenge_lifecycle_records_not_object" "gold_challenge_lifecycle_records_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case40: R40 gold_challenge_lifecycle_records_schema_invalid -----------
T="$WORK/case40"; fresh_copy "$T"
edit_v043_records "$T" 'r["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case40 R40 gold_challenge_lifecycle_records_schema_invalid" "gold_challenge_lifecycle_records_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case41: R41 gold_challenge_lifecycle_records_binding_invalid ----------
T="$WORK/case41"; fresh_copy "$T"
edit_v043_records "$T" 'r["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case41 R41 gold_challenge_lifecycle_records_binding_invalid" "gold_challenge_lifecycle_records_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case42: R42 gold_challenge_lifecycle_event_invalid --------------------
T="$WORK/case42"; fresh_copy "$T"
edit_v043_records "$T" 'r["lifecycle_records"][0]["events"][0]["event_basis"] = "acknowledgement_record"'
cascade_rebuild "$T"
expect_verifier_fail "case42 R42 gold_challenge_lifecycle_event_invalid" "gold_challenge_lifecycle_event_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case43: R43 gold_challenge_lifecycle_transition_invalid ---------------
T="$WORK/case43"; fresh_copy "$T"
edit_v043_records "$T" '
r["lifecycle_records"][0]["events"][0]["event_status"] = "acknowledged"
r["lifecycle_records"][0]["events"][0]["event_basis"] = "acknowledgement_record"
r["lifecycle_records"][0]["events"][0].pop("lifecycle_effect", None)
'
cascade_rebuild "$T"
expect_verifier_fail "case43 R43 gold_challenge_lifecycle_transition_invalid" "gold_challenge_lifecycle_transition_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case44: R44 gold_challenge_lifecycle_report_not_object ----------------
T="$WORK/case44"; fresh_copy "$T"
_replace_body_with_array "$T/child-packages/v0.4.3/gold-challenge-lifecycle-report.json"
cascade_rebuild "$T"
expect_verifier_fail "case44 R44 gold_challenge_lifecycle_report_not_object" "gold_challenge_lifecycle_report_not_object" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case45: R45 gold_challenge_lifecycle_report_schema_invalid ------------
T="$WORK/case45"; fresh_copy "$T"
edit_v043_lreport "$T" 'l["document_type"] = "wrong"'
cascade_rebuild "$T"
expect_verifier_fail "case45 R45 gold_challenge_lifecycle_report_schema_invalid" "gold_challenge_lifecycle_report_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case46: R46 gold_challenge_lifecycle_report_binding_invalid -----------
T="$WORK/case46"; fresh_copy "$T"
edit_v043_lreport "$T" 'l["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
cascade_rebuild "$T"
expect_verifier_fail "case46 R46 gold_challenge_lifecycle_report_binding_invalid" "gold_challenge_lifecycle_report_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case47: R47 gold_challenge_lifecycle_projection_invalid ---------------
T="$WORK/case47"; fresh_copy "$T"
edit_v043_lreport "$T" 'l["lifecycle_rows"][0]["current_status"] = "acknowledged"'
cascade_rebuild "$T"
expect_verifier_fail "case47 R47 gold_challenge_lifecycle_projection_invalid" "gold_challenge_lifecycle_projection_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# --- case48: R48 gold_challenge_lifecycle_summary_invalid ------------------
T="$WORK/case48"; fresh_copy "$T"
edit_v043_lreport "$T" 'l["coverage_summary"]["lifecycle_event_count"] = 42'
cascade_rebuild "$T"
expect_verifier_fail "case48 R48 gold_challenge_lifecycle_summary_invalid" "gold_challenge_lifecycle_summary_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# =============================================================================
# Subphase 3D: collisions (col_*) + subject sub/reorder (sub*) + supplementals
# (sup*). 21 + 5 + 5 = 31 cases.
# =============================================================================

# rehash_index_fingerprint: recompute body's index_fingerprint over current
# body bytes (key excluded, no trailing newline in fingerprint domain), write
# body back canonical. Used by sup* cases where the caller wants R50/R52/R53/
# R51 to surface (Phase 3) without R54 (fingerprint) firing first or R01
# (Phase 1 subject-integrity) firing earlier. Caller is responsible for
# calling rehash_subject4 afterwards to re-stamp subjects[4].sha256.
rehash_index_fingerprint() {
  local root="$1"
  python3 - "$root" << 'PYEOF'
import hashlib, json, os, sys
ROOT = sys.argv[1]
ib_path = os.path.join(ROOT, "gold-reliance-package-index.json")
ib = json.load(open(ib_path))
ib_no_fp = {k: v for k, v in ib.items() if k != "index_fingerprint"}
ib["index_fingerprint"] = hashlib.sha256(
    json.dumps(ib_no_fp, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
with open(ib_path, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
}

# -----------------------------------------------------------------------------
# col_*: 21 pairwise collisions across the 7-member v0.4.4 collision class
# (Phase 1 distinctness check → R01 gold_manifest_invalid). Field index 1..7
# matches the header documentation:
#   1=conformance_report_id, 2=decision_report_id, 3=matrix_id,
#   4=policy_evaluation_report_id, 5=challenge_lifecycle_record_set_id,
#   6=challenge_lifecycle_report_id, 7=gold_reliance_package_index_id.
# Each case sets manifest[field_b] = manifest[field_a] for the pair (a,b).
# cascade_rebuild not required: subject sha/size on disk are already valid
# (fresh_copy), and collision is purely a manifest-id check at Phase 1.
# -----------------------------------------------------------------------------
_COL_FIELDS=(
  "conformance_report_id"
  "decision_report_id"
  "matrix_id"
  "policy_evaluation_report_id"
  "challenge_lifecycle_record_set_id"
  "challenge_lifecycle_report_id"
  "gold_reliance_package_index_id"
)

_run_col() {
  local i="$1"; local j="$2"
  local fi="${_COL_FIELDS[$((i-1))]}"
  local fj="${_COL_FIELDS[$((j-1))]}"
  local label
  label=$(printf 'col_%02d_%02d %s_collides_with_%s' "$i" "$j" "$fi" "$fj")
  local T
  T=$(printf '%s/col_%02d_%02d' "$WORK" "$i" "$j")
  fresh_copy "$T"
  edit_v044_manifest "$T" "m[\"$fj\"] = m[\"$fi\"]"
  expect_verifier_fail "$label" "gold_manifest_invalid" \
    python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"
}

for _i in 1 2 3 4 5 6; do
  for _j in 2 3 4 5 6 7; do
    if [ "$_j" -gt "$_i" ]; then
      _run_col "$_i" "$_j"
    fi
  done
done

# -----------------------------------------------------------------------------
# sub01..sub05: subjects[] integrity (Phase 1 → R01 gold_manifest_invalid).
# Per harness header:
#   sub01  swap subjects[0] <-> subjects[1]
#   sub02  subjects[0]["role"] = wrong
#   sub03  subjects[0]["path"] = absolute
#   sub04  subjects[0]["path"] = traversal
#   sub05  subject count = 4 (drop subjects[4])
# All five route to R01. cascade_rebuild deliberately NOT run after the
# mutation (it would either re-hash from disk - masking the integrity defect -
# or crash trying to open an absolute/traversal path).
# -----------------------------------------------------------------------------

# sub01
T="$WORK/sub01"; fresh_copy "$T"
edit_v044_manifest "$T" 'm["subjects"][0], m["subjects"][1] = m["subjects"][1], m["subjects"][0]'
expect_verifier_fail "sub01 swap_subjects_0_and_1" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sub02
T="$WORK/sub02"; fresh_copy "$T"
edit_v044_manifest "$T" 'm["subjects"][0]["role"] = "wrong_role_value"'
expect_verifier_fail "sub02 subject0_role_wrong" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sub03
T="$WORK/sub03"; fresh_copy "$T"
edit_v044_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "sub03 subject0_path_absolute" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sub04
T="$WORK/sub04"; fresh_copy "$T"
edit_v044_manifest "$T" 'm["subjects"][0]["path"] = "../../etc/passwd"'
expect_verifier_fail "sub04 subject0_path_traversal" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sub05
T="$WORK/sub05"; fresh_copy "$T"
edit_v044_manifest "$T" 'del m["subjects"][4]'
expect_verifier_fail "sub05 subject_count_4" "gold_manifest_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# -----------------------------------------------------------------------------
# sup01..sup05: v0.4.4-owned reachability variants on the index body.
# Per harness header (Phase 3 ordering R49→R50→R52→R53→R51→R54):
#   sup01  R50 stray top-level key in index body
#   sup02  R52 entries[0].child_subject_index = 99
#   sup03  R52 entries[0].child_manifest_fingerprint non-hex
#   sup04  R53 coverage_summary.package_id_anchor_consistency = false
#   sup05  R51 entries[1].child_manifest_fingerprint mutated to a distinct-
#          but-shape-valid bare-hex SHA-256 (mismatched with subjects[1])
# Pattern: fresh_copy → cascade_rebuild (consistent baseline) → mutate body →
# rehash_index_fingerprint (so R54 does not fire) → rehash_subject4 (so
# Phase 1 R01 does not fire).
# -----------------------------------------------------------------------------

# sup01: stray top-level key in index body → R50.
T="$WORK/sup01"; fresh_copy "$T"; cascade_rebuild "$T"
python3 - "$T/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["unexpected_top_level_key"] = "stray"
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_index_fingerprint "$T"
rehash_subject4 "$T"
expect_verifier_fail "sup01 R50_stray_top_level_key" \
  "gold_reliance_package_index_schema_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sup02: entries[0].child_subject_index = 99 → R52.
T="$WORK/sup02"; fresh_copy "$T"; cascade_rebuild "$T"
python3 - "$T/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["entries"][0]["child_subject_index"] = 99
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_index_fingerprint "$T"
rehash_subject4 "$T"
expect_verifier_fail "sup02 R52_child_subject_index_99" \
  "gold_reliance_package_index_entry_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sup03: entries[0].child_manifest_fingerprint non-hex → R52.
T="$WORK/sup03"; fresh_copy "$T"; cascade_rebuild "$T"
python3 - "$T/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["entries"][0]["child_manifest_fingerprint"] = "NOTHEX"
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_index_fingerprint "$T"
rehash_subject4 "$T"
expect_verifier_fail "sup03 R52_child_manifest_fingerprint_non_hex" \
  "gold_reliance_package_index_entry_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sup04: coverage_summary.package_id_anchor_consistency = false → R53.
T="$WORK/sup04"; fresh_copy "$T"; cascade_rebuild "$T"
python3 - "$T/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["coverage_summary"]["package_id_anchor_consistency"] = False
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_index_fingerprint "$T"
rehash_subject4 "$T"
expect_verifier_fail "sup04 R53_package_id_anchor_consistency_false" \
  "gold_reliance_package_index_summary_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# sup05: entries[1].child_manifest_fingerprint mutated to distinct valid hex
# (mismatched with manifest.subjects[1].sha256) → R51 (cross-anchor binding).
# Shape-valid bare hex (64 lowercase hex chars) passes R52; mismatch with
# subjects[1].sha256 fires R51 at Phase 3 step "binding".
T="$WORK/sup05"; fresh_copy "$T"; cascade_rebuild "$T"
python3 - "$T/gold-reliance-package-index.json" << 'PYEOF'
import json, sys
p = sys.argv[1]
ib = json.load(open(p))
ib["entries"][1]["child_manifest_fingerprint"] = "0" * 64
with open(p, "wb") as f:
    f.write(json.dumps(ib, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
rehash_index_fingerprint "$T"
rehash_subject4 "$T"
expect_verifier_fail "sup05 R51_child_manifest_fingerprint_mismatch" \
  "gold_reliance_package_index_binding_invalid" \
  python3 "$VERIFIER" --manifest "$T/gold-reliance-package-index-manifest.json"

# =============================================================================
# Subphase 3E: rel01 + sup_det + no_residue + tg01 + ss01
# =============================================================================

# -----------------------------------------------------------------------------
# rel01: runner --self-validate relays the chained inherited verifier reason
# `gold_package_schema_invalid` (R03 from v0.4.0) verbatim. The bad input is
# valid JSON (passes preflight) but lacks the v0.4.0 package grammar so the
# co-located v0.4.0 verifier (subprocess-invoked by the v0.4.4 verifier
# during --self-validate) rejects it. expect_runner_fail asserts exit=1, the
# first line `FAIL: gold_package_schema_invalid`, no Traceback, no output
# dir, and no staging leak.
# -----------------------------------------------------------------------------
REL01_BAD="$TMP_TEST_SCRATCH/rel01-bad-v040-input.json"
REL01_BAD_REL="$TMP_TEST_SCRATCH_REL/rel01-bad-v040-input.json"
# Copy the good v0.4.0 input and mutate ONLY document_type. The runner
# byte-copies the input through to the v0.4.0 child body; the cross-anchor
# IDs (package_id, governed_reliance_demo_id) stay valid so v0.4.4 Phase 1
# and Phase 2 pass; v0.4.4 Phase 3 sees a well-formed index body; Phase 4
# subprocess-delegates to the v0.4.0 verifier which rejects the body on
# closed-shape document_type and emits FAIL: gold_package_schema_invalid
# (R03), relayed verbatim by the runner's _self_validate.
python3 - "$PACKAGE_FIX_REL" "$REL01_BAD" << 'PYEOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src))
d["document_type"] = "wrong"
with open(dst, "wb") as f:
    f.write(json.dumps(d, sort_keys=True, separators=(",",":")).encode("utf-8"))
    f.write(b"\n")
PYEOF
REL01_OUT="$WORK/rel01-out"
expect_runner_fail "rel01 inherited_relay_gold_package_schema_invalid" \
  "gold_package_schema_invalid" "$REL01_OUT" \
  python3 "$RUNNER" \
    --input-package    "$REL01_BAD_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID-rel01" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID-rel01" \
    --decision-report-id             "$DECISION_REPORT_ID-rel01" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID-rel01" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-rel01" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-rel01" \
    --generated-at                   "$GEN_AT" \
    --output-dir                     "$REL01_OUT" \
    --self-validate

# -----------------------------------------------------------------------------
# sup_det: positive determinism. Build the v0.4.4 package twice with
# identical IDs + identical --generated-at into two distinct --output-dir
# locations; assert wrapping-manifest subjects[0..4].sha256 and index-body
# index_fingerprint are byte-identical across the two builds.
# -----------------------------------------------------------------------------
SUPDET_A="$WORK/supdet-a"
SUPDET_B="$WORK/supdet-b"
_supdet_build() {
  local out="$1"
  python3 "$RUNNER" \
    --input-package    "$PACKAGE_FIX_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID-supdet" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID-supdet" \
    --decision-report-id             "$DECISION_REPORT_ID-supdet" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID-supdet" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID-supdet" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID-supdet" \
    --generated-at                   "$GEN_AT" \
    --output-dir                     "$out" >"$WORK/supdet.out" 2>&1 \
    || { cat "$WORK/supdet.out" >&2; die "sup_det: build $out failed"; }
}
_supdet_build "$SUPDET_A"
_supdet_build "$SUPDET_B"
python3 - "$SUPDET_A" "$SUPDET_B" << 'PYEOF' || die "sup_det: nondeterministic"
import json, sys
a, b = sys.argv[1], sys.argv[2]
ma = json.load(open(a + "/gold-reliance-package-index-manifest.json"))
mb = json.load(open(b + "/gold-reliance-package-index-manifest.json"))
ia = json.load(open(a + "/gold-reliance-package-index.json"))
ib = json.load(open(b + "/gold-reliance-package-index.json"))
errs = []
for i in range(5):
    if ma["subjects"][i]["sha256"] != mb["subjects"][i]["sha256"]:
        errs.append(("subjects[%d].sha256" % i,
                     ma["subjects"][i]["sha256"], mb["subjects"][i]["sha256"]))
if ia["index_fingerprint"] != ib["index_fingerprint"]:
    errs.append(("index_fingerprint",
                 ia["index_fingerprint"], ib["index_fingerprint"]))
if errs:
    for e in errs: print("DET DRIFT:", e)
    sys.exit(1)
PYEOF
note_pass "sup_det subjects_and_index_fingerprint_byte_identical"

# -----------------------------------------------------------------------------
# idem01: --force re-run idempotency. Build the v0.4.4 package into a
# v0.4.4-scratch-prefixed --output-dir, then re-build into the SAME
# --output-dir with --force. The runner's prefix check must accept BOTH
# realpath forms (/tmp/proofrail-v044-* and /private/tmp/proofrail-v044-*)
# so the second --force build succeeds on both Linux and macOS. Without
# the dual-prefix discipline, on macOS the second build is refused with
# `refuse: --force is permitted only when --output-dir is under
# '/tmp/proofrail-v044-'` because os.path.realpath() resolves /tmp/foo
# to /private/tmp/foo. The idempotency dir is placed under $WORK (which
# is itself v0.4.4-scratch-prefixed) and is cleaned up via the EXIT trap.
# -----------------------------------------------------------------------------
IDEM_OUT="$WORK/idem01-out"
_idem_build() {
  local force_flag="$1"
  # Use canonical IDs (matching the pristine build) so the matrix
  # fixture's pinned decision_report_ref binds correctly under
  # --self-validate. The point of idem01 is the --force re-run
  # discipline of the output-dir prefix check, not ID variation.
  python3 "$RUNNER" \
    --input-package    "$PACKAGE_FIX_REL" \
    --matrix-input     "$MATRIX_FIX_REL" \
    --lifecycle-input  "$LIFECYCLE_FIX_REL" \
    --manifest-id                    "$MANIFEST_ID" \
    --conformance-report-id          "$CONFORMANCE_REPORT_ID" \
    --decision-report-id             "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id    "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id  "$CHALLENGE_LIFECYCLE_REPORT_ID" \
    --gold-reliance-package-index-id "$GOLD_RELIANCE_PACKAGE_INDEX_ID" \
    --generated-at                   "$GEN_AT" \
    --output-dir                     "$IDEM_OUT" \
    $force_flag \
    --self-validate >"$WORK/idem01.out" 2>&1
}
_idem_build "" \
  || { cat "$WORK/idem01.out" >&2; die "idem01: first build (no --force) failed"; }
[ -f "$IDEM_OUT/$MANIFEST_REL_FILE" ] \
  || die "idem01: first build did not produce wrapping manifest"
_idem_build "--force" \
  || { cat "$WORK/idem01.out" >&2; die "idem01: second build (--force) failed"; }
[ -f "$IDEM_OUT/$MANIFEST_REL_FILE" ] \
  || die "idem01: second build did not produce wrapping manifest"
note_pass "idem01 double_force_run_idempotent"

# -----------------------------------------------------------------------------
# no_residue: assert no transient v0.4.4 file residue under any inherited-
# tier (v0.4.0/v0.4.1/v0.4.2/v0.4.3) fixture, tool, or schema directory,
# and assert no leftover v0.4.4 scratch dirs under /tmp or /private/tmp
# (the runner's bundle/staging subdirs are always cleaned at end-of-run on
# both success and failure paths). The test scratch (TMP_TEST_SCRATCH) is
# allowed to contain ONLY the explicit test-owned bad-input file rel01
# wrote above; everything else is residue.
# -----------------------------------------------------------------------------
_INHERITED_TIER_DIRS=(
  "$REPO_ROOT/fixtures/gold-governed-reliance-v0.4.0"
  "$REPO_ROOT/fixtures/gold-policy-evaluation-matrix-v0.4.2"
  "$REPO_ROOT/fixtures/gold-challenge-lifecycle-lite-v0.4.3"
  "$REPO_ROOT/tools/gold"
  "$REPO_ROOT/schemas"
)
_NORES_ALLOW_V044=(
  "$REPO_ROOT/tools/gold/build_gold_reliance_package_index_v0_1_0.py"
  "$REPO_ROOT/tools/gold/verify_gold_reliance_package_index_v0_1_0.py"
  "$REPO_ROOT/schemas/gold-reliance-package-index-manifest-v0.1.0.md"
  "$REPO_ROOT/schemas/gold-reliance-package-index-v0.1.0.md"
)
_nores_leak=""
for d in "${_INHERITED_TIER_DIRS[@]}"; do
  while IFS= read -r f; do
    keep=1
    case "$(basename "$f")" in
      *gold-reliance*|*proofrail-v044-*|*reliance-package-index*) keep=0 ;;
    esac
    if [ "$keep" -eq 0 ]; then
      ok=0
      for allow in "${_NORES_ALLOW_V044[@]}"; do
        if [ "$f" = "$allow" ]; then ok=1; break; fi
      done
      if [ "$ok" -eq 0 ]; then _nores_leak="$_nores_leak $f"; fi
    fi
  done < <(find "$d" -type f 2>/dev/null)
done
[ -z "$_nores_leak" ] \
  || die "no_residue: v0.4.4 transient residue under inherited tier dirs:$_nores_leak"
# Stray /tmp scratch dirs (bundle/staging) outside this harness's WORK.
_tmp_leak=$(find /tmp /private/tmp -maxdepth 1 -mindepth 1 \
  \( -name 'proofrail-v044-bundle-*' -o -name 'proofrail-v044-staging-*' \) \
  -print 2>/dev/null | head -n 5)
[ -z "$_tmp_leak" ] \
  || die "no_residue: leftover scratch under /tmp: $_tmp_leak"
# Test scratch should contain only the explicit test-owned bad-input files
# (ro5 bad-JSON file from 3B and rel01 bad-v0.4.0 input file from 3E).
_scratch_extra=$(find "$TMP_TEST_SCRATCH" -mindepth 1 -type f \
  ! -name 'rel01-bad-v040-input.json' \
  ! -name 'ro5_bad.json' \
  -print 2>/dev/null)
[ -z "$_scratch_extra" ] \
  || die "no_residue: unexpected files in test scratch: $_scratch_extra"
note_pass "no_residue no_inherited_tier_residue"

# -----------------------------------------------------------------------------
# tg01: 5-file exact-token taxonomy gate. Scan the v0.4.4-owned source paths
# (two schemas + runner + verifier + test file) for reason-shaped tokens. The
# closed approved set is exactly the 54-reason verifier vocabulary + the 5
# runner-only refusal vocabulary. A small inherited-data-field allowlist
# covers narrow snake_case identifiers that legitimately end in one of the
# matched suffixes but are NOT reasons. The deny-list surfaces any drift
# toward wrapping-environment-failure-as-public-reason patterns.
# -----------------------------------------------------------------------------
python3 - "$REPO_ROOT" << 'PYEOF' || die "tg01: taxonomy drift"
import os, re, sys
ROOT = sys.argv[1]
FILES = [
  "schemas/gold-reliance-package-index-manifest-v0.1.0.md",
  "schemas/gold-reliance-package-index-v0.1.0.md",
  "tools/gold/build_gold_reliance_package_index_v0_1_0.py",
  "tools/gold/verify_gold_reliance_package_index_v0_1_0.py",
  "tests/test_gold_reliance_package_index_v0_4_4.sh",
]
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
  "gold_decision_report_not_object",
  "gold_decision_report_schema_invalid",
  "gold_decision_report_binding_invalid",
  "gold_decision_report_projection_invalid",
  "gold_decision_report_summary_invalid",
  "gold_policy_matrix_not_object",
  "gold_policy_matrix_schema_invalid",
  "gold_policy_matrix_binding_invalid",
  "gold_policy_matrix_entry_invalid",
  "gold_policy_evaluation_report_not_object",
  "gold_policy_evaluation_report_schema_invalid",
  "gold_policy_evaluation_report_binding_invalid",
  "gold_policy_evaluation_result_invalid",
  "gold_policy_evaluation_summary_invalid",
  "gold_challenge_lifecycle_records_not_object",
  "gold_challenge_lifecycle_records_schema_invalid",
  "gold_challenge_lifecycle_records_binding_invalid",
  "gold_challenge_lifecycle_event_invalid",
  "gold_challenge_lifecycle_transition_invalid",
  "gold_challenge_lifecycle_report_not_object",
  "gold_challenge_lifecycle_report_schema_invalid",
  "gold_challenge_lifecycle_report_binding_invalid",
  "gold_challenge_lifecycle_projection_invalid",
  "gold_challenge_lifecycle_summary_invalid",
  "gold_reliance_package_index_not_object",
  "gold_reliance_package_index_schema_invalid",
  "gold_reliance_package_index_binding_invalid",
  "gold_reliance_package_index_entry_invalid",
  "gold_reliance_package_index_summary_invalid",
  "gold_reliance_package_index_fingerprint_invalid",
}
assert len(APPROVED_VERIFIER) == 54, len(APPROVED_VERIFIER)
APPROVED_RUNNER = {
  "runner_input_path_missing",
  "runner_input_path_forbidden",
  "runner_input_file_missing",
  "runner_input_read_failed",
  "runner_input_json_invalid",
}
assert len(APPROVED_RUNNER) == 5
# Narrow allowlist: snake_case identifiers that match the reason-suffix
# regex but are intentionally NOT public reason names. These are short-form
# case labels used by the harness for human-readable test identification
# only; they never appear in runner/verifier source as emitted reasons.
INHERITED_DATA_ALLOW = {
  "schema_invalid",
  "binding_invalid",
  "entry_invalid",
  "summary_invalid",
  "fingerprint_invalid",
  "inherited_relay_gold_package_schema_invalid",
}
# Deny-list of environmental/wrapper-escape patterns that must NOT appear
# in the v0.4.4-owned source-set as public reason vocabulary. Each pattern
# is assembled by string concatenation so the literal full token never
# appears in this scanner's own source — which would otherwise self-trip
# the deny check when this very file is scanned below.
DENY_PATTERNS = [
  r"\b" + "wrapping_" + "environment_failure" + r"\b",
  r"\b" + "verifier_" + "environment_failure" + r"\b",
  r"\b" + "harness_" + "internal_error" + r"\b",
  r"\b" + "runner_relay_" + "of_verifier_failure" + r"\b",
]
SUFFIX = r"(?:_invalid|_not_object|_missing|_forbidden|_failed|_unsupported|_present)"
# Non-greedy with anchoring \b at end so `binding_invalid` inside
# `binding_invalid_package_id` is NOT spuriously captured as a token.
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
    m = re.search(pat, text)
    if m:
      errors.append((rel, "DENY:" + m.group(0)))
if errors:
  for e in errors[:50]:
    print("DRIFT", e)
  sys.exit(1)
PYEOF
note_pass "tg01 reason_taxonomy_closed"

# -----------------------------------------------------------------------------
# ss01: 8-file scoped SHA-256 snapshot AFTER, byte-identical to the BEFORE
# snapshot captured at suite start. Phase 3 must perform no mutations on any
# scoped file. The committed Makefile is excluded (shared across release
# versions, mutated independently).
# -----------------------------------------------------------------------------
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

# === BODY_BOUNDARY ===
