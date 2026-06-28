#!/usr/bin/env bash
# tests/test_gold_local_minimal_profile_v0_4_6.sh
#
# Phase 3 regression harness for the ProofRail v0.4.6 Gold Local
# Minimal Profile. The v0.4.6 release is a validator-only profile
# (no builder, no JSON certificate, no runtime artifact). The
# v0.4.6 validator owns five new reasons (R62..R66) and RELAYS
# the inherited closed surface R01..R61 verbatim on inherited
# verifier failure without wrapping.
#
# 15 numbered exercises:
#
#   Positive-path (3):
#     pp1   py_compile of the validator source.
#     pp2   Validator PASS against the real repo with --skip-make
#           (structural R62/R63/R65/R66 checks only).
#     pp3   Validator PASS against the real repo with full make
#           execution (R64 exercises the real inherited Gold
#           chain).
#
#   v0.4.6-owned reason mutation cases (5; locked check order
#   R62 -> R63 -> R65 -> R66 -> R64):
#     r62   gold_local_minimal_profile_required_artifact_missing
#           (synth tempdir; remove one of the 46 required
#            inherited Gold artifacts)
#     r63   gold_local_minimal_profile_required_make_target_missing
#           (synth tempdir; rewrite Makefile to omit verify-gold-all)
#     r64   gold_local_minimal_profile_required_verifier_failed
#           (real repo + stub make whose first invocation exits 2
#            with no recognized inherited FAIL line)
#     r65   gold_local_minimal_profile_required_non_claim_missing
#           (synth tempdir; remove "no federation" non-claim
#            phrase from descriptor §6)
#     r66   gold_local_minimal_profile_descriptor_invalid
#           (synth tempdir; remove "## 9. Changelog" heading from
#            descriptor)
#
#   Inherited verbatim-relay case (1):
#     inh01 Real repo + stub make whose first invocation emits
#           `FAIL: r07_subject_path_mismatch: simulated v0.4.0
#           reason emission` to stderr and exits 1. The v0.4.6
#           validator must relay that line VERBATIM on stderr,
#           exit 1, and emit NO R64 wrapper token.
#
#   Infrastructure case (1):
#     env01 INFRA exit 3 via invalid --make-binary
#           (/tmp/proofrail-v046-nonexistent-make). The validator
#           must emit `INFRA: <message>` on stderr with no
#           `FAIL:` prefix.
#
#   Invocation-set audit (1):
#     audit01 Real repo + a logging stub make that succeeds on
#             every target and records each <target> arg to a
#             file. After a full validator run, the recorded set
#             must NOT contain `verify-gold-all` (invariant J2:
#             validator never invokes verify-gold-all).
#
#   Validator-write audit (1):
#     audit02 Validator under --skip-make against the real repo
#             must not create, modify, or delete any file
#             anywhere under the repo root or anywhere under
#             /tmp/proofrail-v046-* (other than this harness's
#             own $WORK scratch, which is created by the harness
#             itself, not by the validator). Verified by
#             before/after sha256 manifests.
#
#   No-residue (no_residue):
#     After all exercises complete, no /tmp/proofrail-v046-test.*
#     scratch dirs other than $WORK may remain. $WORK itself is
#     cleaned by EXIT trap.
#
#   Taxonomy gate (tg01):
#     Exact-token scan of the validator source. The five
#     v0.4.6-owned snake_case reason tokens must be exactly:
#       gold_local_minimal_profile_required_artifact_missing
#       gold_local_minimal_profile_required_make_target_missing
#       gold_local_minimal_profile_required_verifier_failed
#       gold_local_minimal_profile_required_non_claim_missing
#       gold_local_minimal_profile_descriptor_invalid
#     No drift, no extras, no wrapped variants.
#
#   Scoped SHA-256 snapshot (ss01):
#     3-file scoped snapshot of v0.4.6-owned source paths
#       schemas/gold-local-minimal-profile-v0.1.0.md
#       profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md
#       tools/gold/verify_gold_local_minimal_profile_v0_1_0.py
#     BEFORE and AFTER. Phase 3 performs no mutations on any of
#     these 3 paths. The harness itself is intentionally outside
#     the scoped set.
#
# Phase 3 scope: this harness is the only file added in Phase 3
# beyond the .git/-internal ledger files. It performs no
# mutations on the schema, descriptor, validator, Makefile,
# docs, demos, README.md, CLAUDE.md, indexes, or any inherited
# v0.4.0..v0.4.5 file. All transient scratch lives under
# /tmp/proofrail-v046-test.* and is cleaned up via EXIT trap.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

VALIDATOR="$REPO_ROOT/tools/gold/verify_gold_local_minimal_profile_v0_1_0.py"
SCHEMA_REL="schemas/gold-local-minimal-profile-v0.1.0.md"
DESCRIPTOR_REL="profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md"
VALIDATOR_REL="tools/gold/verify_gold_local_minimal_profile_v0_1_0.py"

LONG_LOG="/tmp/proofrail-v046-last-run.log"
: > "$LONG_LOG"

WORK="$(mktemp -d /tmp/proofrail-v046-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

# -- Counters ----------------------------------------------------------

PASS_COUNT=0
EXPECTED_COUNT=15

note_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS %2d/%d  %s\n' "$PASS_COUNT" "$EXPECTED_COUNT" "$1"
}

die() {
  echo "FAIL (test-harness): $*" >&2
  echo "---- last captured output ----" >&2
  if [ -f "$WORK/last.out" ]; then
    echo "[stdout]" >&2; cat "$WORK/last.out" >&2
  fi
  if [ -f "$WORK/last.err" ]; then
    echo "[stderr]" >&2; cat "$WORK/last.err" >&2
  fi
  echo "---- full long log: $LONG_LOG ----" >&2
  exit 1
}

run_validator() {
  # Invocation helper; records last.out / last.err and appends to
  # $LONG_LOG. Does NOT exit on nonzero; caller inspects $?.
  rm -f "$WORK/last.out" "$WORK/last.err"
  set +e
  python3 "$VALIDATOR" "$@" \
    >"$WORK/last.out" 2>"$WORK/last.err"
  RC=$?
  set -e
  {
    printf -- '---- run_validator args: %s\n' "$*"
    printf -- '[rc=%d] [stdout]\n' "$RC"
    cat "$WORK/last.out"
    printf -- '[stderr]\n'
    cat "$WORK/last.err"
    printf -- '\n'
  } >> "$LONG_LOG"
}

# -- File hashing helpers ----------------------------------------------

file_sha256() {
  python3 -c "
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], 'rb') as f:
    for c in iter(lambda: f.read(65536), b''): h.update(c)
print(h.hexdigest())
" "$1"
}

# -- Scoped SHA-256 snapshot (ss01 BEFORE) -----------------------------

SCOPED_FILES=(
  "$SCHEMA_REL"
  "$DESCRIPTOR_REL"
  "$VALIDATOR_REL"
)
snapshot_scoped() {
  local out="$1"
  : > "$out"
  for rel in "${SCOPED_FILES[@]}"; do
    printf '%s  %s\n' "$(file_sha256 "$REPO_ROOT/$rel")" "$rel" \
      >> "$out"
  done
}
snapshot_scoped "$WORK/scoped.before"

# -- Synthetic fixture builder ----------------------------------------
#
# Builds a self-contained --repo-root tempdir that satisfies every
# v0.4.6 structural check (R62/R63/R65/R66). The 46 required
# inherited Gold artifacts are touched as empty files (R62 only
# checks existence + readability). The Makefile, schema, and
# descriptor are byte-copied from the real repo. Caller may
# subsequently mutate exactly one surface to target one reason.
#
# build_synth_fixture <dir>
build_synth_fixture() {
  local dir="$1"
  mkdir -p "$dir"

  # Touch all 46 required artifacts as empty files. The artifact
  # list is the validator's authoritative REQUIRED_ARTIFACTS
  # constant, loaded by import (no fragile regex).
  python3 - "$dir" << PYEOF
import importlib.util, os, sys
fixture = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "v046_validator", "$VALIDATOR"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
paths = mod.REQUIRED_ARTIFACTS
assert len(paths) == 46, f"expected 46 artifacts, got {len(paths)}"
for rel in paths:
    p = os.path.join(fixture, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").close()
PYEOF

  # Copy schema, descriptor, and Makefile byte-for-byte.
  mkdir -p "$dir/$(dirname "$SCHEMA_REL")"
  mkdir -p "$dir/$(dirname "$DESCRIPTOR_REL")"
  cp "$REPO_ROOT/$SCHEMA_REL"      "$dir/$SCHEMA_REL"
  cp "$REPO_ROOT/$DESCRIPTOR_REL"  "$dir/$DESCRIPTOR_REL"
  cp "$REPO_ROOT/Makefile"         "$dir/Makefile"
}

# -- Stub make builder -------------------------------------------------
#
# write_stub_make <dest> <mode>
#   Modes:
#     "log_pass": exit 0 on every invocation; append target arg to
#                 $STUB_LOG.
#     "fail_silent": exit 2 with no recognized FAIL line (used to
#                    trigger R64).
#     "fail_inherited": emit `FAIL: r07_subject_path_mismatch:
#                       simulated v0.4.0 reason emission` to stderr
#                       and exit 1 (used to trigger inh01 verbatim
#                       relay).
write_stub_make() {
  local dest="$1"
  local mode="$2"
  case "$mode" in
    log_pass)
      cat > "$dest" << 'SHEOF'
#!/usr/bin/env bash
# Logging stub make. Records the last arg (the target) to $STUB_LOG.
target=""
for a in "$@"; do target="$a"; done
if [ -n "${STUB_LOG:-}" ]; then
  printf '%s\n' "$target" >> "$STUB_LOG"
fi
exit 0
SHEOF
      ;;
    fail_silent)
      cat > "$dest" << 'SHEOF'
#!/usr/bin/env bash
# Stub make: exit 2 with no recognized FAIL line.
echo "stub make: target failed (no recognized inherited reason)" >&2
exit 2
SHEOF
      ;;
    fail_inherited)
      cat > "$dest" << 'SHEOF'
#!/usr/bin/env bash
# Stub make: emit a recognized inherited FAIL line and exit 1.
printf 'FAIL: r07_subject_path_mismatch: simulated v0.4.0 reason emission\n' >&2
exit 1
SHEOF
      ;;
    *)
      echo "write_stub_make: unknown mode: $mode" >&2
      exit 2
      ;;
  esac
  chmod +x "$dest"
}

# -- File-tree manifest (audit02 helper) ------------------------------
#
# manifest <root> <out>
#   Writes "<sha256>  <relpath>" lines, one per regular file under
#   <root>, sorted by relpath. Used to verify the validator under
#   --skip-make creates / modifies / deletes nothing under the real
#   repo root.
manifest() {
  local root="$1"
  local out="$2"
  python3 - "$root" > "$out" << 'PYEOF'
import hashlib, os, sys
root = sys.argv[1]
rows = []
for dirpath, dirnames, filenames in os.walk(root):
    # Skip .git internals (high-churn, irrelevant to validator).
    dirnames[:] = [d for d in dirnames if d != ".git"]
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            rel = os.path.relpath(p, root)
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for c in iter(lambda: f.read(65536), b""):
                    h.update(c)
            rows.append((rel, h.hexdigest()))
        except OSError:
            continue
rows.sort()
for rel, hx in rows:
    print(f"{hx}  {rel}")
PYEOF
}

# ----------------------------------------------------------------------
# pp1: py_compile validator
# ----------------------------------------------------------------------
{
  echo "==== pp1 py_compile ===="
  python3 -m py_compile "$VALIDATOR"
} >> "$LONG_LOG" 2>&1
note_pass "pp1 py_compile"

# ----------------------------------------------------------------------
# pp2: PASS with --skip-make against real repo
# ----------------------------------------------------------------------
run_validator --repo-root "$REPO_ROOT" --skip-make
[ "$RC" = "0" ] || die "pp2 expected rc=0, got $RC"
grep -q '^PASS: gold_local_minimal_profile_conformance$' "$WORK/last.out" \
  || die "pp2 missing PASS line on stdout"
[ ! -s "$WORK/last.err" ] || die "pp2 stderr must be empty"
note_pass "pp2 PASS --skip-make"

# ----------------------------------------------------------------------
# pp3: PASS with full make execution against real repo
# ----------------------------------------------------------------------
run_validator --repo-root "$REPO_ROOT" --make-binary make
[ "$RC" = "0" ] || die "pp3 expected rc=0, got $RC"
grep -q '^PASS: gold_local_minimal_profile_conformance$' "$WORK/last.out" \
  || die "pp3 missing PASS line on stdout"
[ ! -s "$WORK/last.err" ] || die "pp3 stderr must be empty"
note_pass "pp3 PASS full make"

# ----------------------------------------------------------------------
# r62: required artifact missing
# ----------------------------------------------------------------------
R62_FIX="$WORK/fixture-r62"
build_synth_fixture "$R62_FIX"
rm "$R62_FIX/schemas/gold-governed-reliance-package-v0.1.0.md"
run_validator --repo-root "$R62_FIX" --skip-make
[ "$RC" = "1" ] || die "r62 expected rc=1, got $RC"
grep -q '^FAIL: gold_local_minimal_profile_required_artifact_missing: schemas/gold-governed-reliance-package-v0.1.0.md$' \
  "$WORK/last.err" || die "r62 missing expected FAIL line"
[ ! -s "$WORK/last.out" ] || die "r62 stdout must be empty"
note_pass "r62 required_artifact_missing"

# ----------------------------------------------------------------------
# r63: required make target missing (verify-gold-all)
# ----------------------------------------------------------------------
R63_FIX="$WORK/fixture-r63"
build_synth_fixture "$R63_FIX"
# Strip verify-gold-all from the Makefile (both .PHONY and rule).
python3 - "$R63_FIX/Makefile" << 'PYEOF'
import re, sys
p = sys.argv[1]
text = open(p).read()
out_lines = []
skip_rule = False
for line in text.splitlines():
    if re.match(r'^\.PHONY:\s+verify-gold-all\s*$', line):
        continue
    if re.match(r'^verify-gold-all\s*:', line):
        skip_rule = True
        continue
    if skip_rule:
        if line.startswith('\t') or line.strip() == '':
            continue
        skip_rule = False
    out_lines.append(line)
with open(p, 'w') as f:
    f.write('\n'.join(out_lines) + '\n')
PYEOF
run_validator --repo-root "$R63_FIX" --skip-make
[ "$RC" = "1" ] || die "r63 expected rc=1, got $RC"
grep -q '^FAIL: gold_local_minimal_profile_required_make_target_missing: verify-gold-all$' \
  "$WORK/last.err" || die "r63 missing expected FAIL line"
note_pass "r63 required_make_target_missing"

# ----------------------------------------------------------------------
# r64: inherited verifier exits nonzero without recognized reason
# ----------------------------------------------------------------------
STUB_R64="$WORK/stub-make-fail-silent"
write_stub_make "$STUB_R64" fail_silent
run_validator --repo-root "$REPO_ROOT" --make-binary "$STUB_R64"
[ "$RC" = "1" ] || die "r64 expected rc=1, got $RC"
grep -q '^FAIL: gold_local_minimal_profile_required_verifier_failed: ' \
  "$WORK/last.err" || die "r64 missing R64 FAIL prefix"
grep -q "verify-gold-governed-reliance-v0-4-0" "$WORK/last.err" \
  || die "r64 expected first inherited target in diagnostic"
grep -q "without a recognized inherited FAIL: <reason>: line" \
  "$WORK/last.err" || die "r64 missing recognition diagnostic"
note_pass "r64 required_verifier_failed"

# ----------------------------------------------------------------------
# r65: required non-claim missing
# ----------------------------------------------------------------------
R65_FIX="$WORK/fixture-r65"
build_synth_fixture "$R65_FIX"
# Remove the `- no federation` bullet line from descriptor.
python3 - "$R65_FIX/$DESCRIPTOR_REL" << 'PYEOF'
import sys
p = sys.argv[1]
text = open(p).read()
out_lines = []
removed = False
for line in text.splitlines():
    s = line.strip()
    if s == 'no federation' or s == '- no federation' \
       or s == '`no federation`' or s == '- `no federation`':
        removed = True
        continue
    out_lines.append(line)
assert removed, "expected to strip a 'no federation' line"
with open(p, 'w') as f:
    f.write('\n'.join(out_lines) + '\n')
PYEOF
run_validator --repo-root "$R65_FIX" --skip-make
[ "$RC" = "1" ] || die "r65 expected rc=1, got $RC"
grep -q '^FAIL: gold_local_minimal_profile_required_non_claim_missing: no federation$' \
  "$WORK/last.err" || die "r65 missing expected FAIL line"
note_pass "r65 required_non_claim_missing"

# ----------------------------------------------------------------------
# r66: descriptor missing required section
# ----------------------------------------------------------------------
R66_FIX="$WORK/fixture-r66"
build_synth_fixture "$R66_FIX"
# Drop the `## 9. Changelog` heading entirely.
python3 - "$R66_FIX/$DESCRIPTOR_REL" << 'PYEOF'
import sys
p = sys.argv[1]
text = open(p).read()
out_lines = []
removed = False
for line in text.splitlines():
    if line.strip() == '## 9. Changelog':
        removed = True
        continue
    out_lines.append(line)
assert removed, "expected to strip the ## 9. Changelog heading"
with open(p, 'w') as f:
    f.write('\n'.join(out_lines) + '\n')
PYEOF
run_validator --repo-root "$R66_FIX" --skip-make
[ "$RC" = "1" ] || die "r66 expected rc=1, got $RC"
grep -q '^FAIL: gold_local_minimal_profile_descriptor_invalid: descriptor missing required section: ## 9\. Changelog$' \
  "$WORK/last.err" || die "r66 missing expected FAIL line"
note_pass "r66 descriptor_invalid"

# ----------------------------------------------------------------------
# inh01: inherited verbatim relay; no R64 wrapper
# ----------------------------------------------------------------------
STUB_INH="$WORK/stub-make-fail-inherited"
write_stub_make "$STUB_INH" fail_inherited
run_validator --repo-root "$REPO_ROOT" --make-binary "$STUB_INH"
[ "$RC" = "1" ] || die "inh01 expected rc=1, got $RC"
# Stderr must equal exactly the simulated inherited FAIL line (one
# line, byte-for-byte). The validator must NOT prepend, wrap, or
# append. We verify by exact line match and by absence of the R64
# token.
EXPECTED_INH='FAIL: r07_subject_path_mismatch: simulated v0.4.0 reason emission'
ACTUAL_INH="$(cat "$WORK/last.err")"
[ "$ACTUAL_INH" = "$EXPECTED_INH" ] \
  || die "inh01 stderr not byte-identical to inherited FAIL line"
grep -q 'gold_local_minimal_profile_required_verifier_failed' \
  "$WORK/last.err" \
  && die "inh01 R64 wrapper token leaked on stderr"
grep -q 'gold_local_minimal_profile' "$WORK/last.err" \
  && die "inh01 v0.4.6-owned token leaked on stderr"
[ ! -s "$WORK/last.out" ] || die "inh01 stdout must be empty"
note_pass "inh01 inherited verbatim relay"

# ----------------------------------------------------------------------
# env01: INFRA via invalid --make-binary
# ----------------------------------------------------------------------
INFRA_MAKE="/tmp/proofrail-v046-nonexistent-make-$$"
[ -e "$INFRA_MAKE" ] && die "env01 precondition: $INFRA_MAKE exists"
run_validator --repo-root "$REPO_ROOT" --make-binary "$INFRA_MAKE"
[ "$RC" = "3" ] || die "env01 expected rc=3, got $RC"
grep -q "^INFRA: make binary not found on PATH or as a file: $INFRA_MAKE$" \
  "$WORK/last.err" || die "env01 missing expected INFRA line"
grep -q '^FAIL:' "$WORK/last.err" \
  && die "env01 INFRA line must not begin with FAIL:"
note_pass "env01 INFRA invalid --make-binary"

# ----------------------------------------------------------------------
# audit01: validator never invokes verify-gold-all
# ----------------------------------------------------------------------
STUB_LOG_FILE="$WORK/stub-make-invocations.log"
STUB_LOG_PASS="$WORK/stub-make-log-pass"
write_stub_make "$STUB_LOG_PASS" log_pass
: > "$STUB_LOG_FILE"
STUB_LOG="$STUB_LOG_FILE" run_validator \
  --repo-root "$REPO_ROOT" --make-binary "$STUB_LOG_PASS"
[ "$RC" = "0" ] || die "audit01 expected rc=0 (stub make passes all), got $RC"
grep -q '^PASS: gold_local_minimal_profile_conformance$' "$WORK/last.out" \
  || die "audit01 missing PASS line"
grep -q '^verify-gold-all$' "$STUB_LOG_FILE" \
  && die "audit01 verify-gold-all was invoked by the validator"
# Sanity: confirm the 6 inherited verifiers WERE invoked, in order.
EXPECTED_AUDIT01=$(cat << 'EOF'
verify-gold-governed-reliance-v0-4-0
verify-gold-decision-report-hardening-v0-4-1
verify-gold-policy-evaluation-matrix-v0-4-2
verify-gold-challenge-lifecycle-lite-v0-4-3
verify-gold-reliance-package-index-v0-4-4
verify-gold-multi-case-reliance-v0-4-5
EOF
)
ACTUAL_AUDIT01="$(cat "$STUB_LOG_FILE")"
[ "$ACTUAL_AUDIT01" = "$EXPECTED_AUDIT01" ] \
  || die "audit01 invocation set not exactly the 6 inherited verifiers"
note_pass "audit01 verify-gold-all never invoked"

# ----------------------------------------------------------------------
# audit02: validator writes no files (under --skip-make)
# ----------------------------------------------------------------------
manifest "$REPO_ROOT" "$WORK/repo.before"
# Snapshot /tmp top-level entries (cheap; we only check that the
# validator doesn't materialize new /tmp/proofrail-v046-* outputs).
ls -1 /tmp > "$WORK/tmp.before"
run_validator --repo-root "$REPO_ROOT" --skip-make
[ "$RC" = "0" ] || die "audit02 expected rc=0, got $RC"
manifest "$REPO_ROOT" "$WORK/repo.after"
ls -1 /tmp > "$WORK/tmp.after"
diff -u "$WORK/repo.before" "$WORK/repo.after" > "$WORK/repo.diff" \
  || die "audit02 repo state changed under --skip-make"
# /tmp may show benign churn (other processes); we only forbid new
# proofrail-v046-* entries created by the validator itself.
TMP_NEW="$(comm -13 \
  <(sort -u "$WORK/tmp.before") \
  <(sort -u "$WORK/tmp.after") \
  | grep -E '^proofrail-v046-' || true)"
[ -z "$TMP_NEW" ] \
  || die "audit02 validator materialized new /tmp/proofrail-v046-* paths: $TMP_NEW"
note_pass "audit02 validator writes no files"

# ----------------------------------------------------------------------
# no_residue: no stray /tmp/proofrail-v046-test.* dirs
# ----------------------------------------------------------------------
STRAY="$(find /tmp -maxdepth 1 -name 'proofrail-v046-test.*' -type d \
  ! -path "$WORK" 2>/dev/null || true)"
[ -z "$STRAY" ] \
  || die "no_residue stray test dirs: $STRAY"
note_pass "no_residue"

# ----------------------------------------------------------------------
# tg01: taxonomy gate — exactly R62..R66, no drift
# ----------------------------------------------------------------------
# Find every snake_case token of shape
#   gold_local_minimal_profile_<lower_snake>
# in the validator source, where the trailing boundary must NOT be
# another `[a-z0-9_]`. This excludes false-positive prefix matches
# of the validator's own filename token
# `gold_local_minimal_profile_v0_1_0` (the trailing `v0` digit fails
# the boundary). The remaining set must equal the closed 5 reasons
# plus the PASS-line suffix token `gold_local_minimal_profile_conformance`.
ACTUAL_TG="$(python3 - "$VALIDATOR" << 'PYEOF'
import re, sys
src = open(sys.argv[1]).read()
toks = re.findall(
    r'gold_local_minimal_profile_[a-z][a-z_]*(?![a-z0-9_])', src,
)
for t in sorted(set(toks)):
    print(t)
PYEOF
)"
EXPECTED_TG=$(cat << 'EOF'
gold_local_minimal_profile_conformance
gold_local_minimal_profile_descriptor_invalid
gold_local_minimal_profile_required_artifact_missing
gold_local_minimal_profile_required_make_target_missing
gold_local_minimal_profile_required_non_claim_missing
gold_local_minimal_profile_required_verifier_failed
EOF
)
# Note: gold_local_minimal_profile_conformance is the PASS-line
# suffix, not a reason; it is allowed in the source. Subtract it
# and assert the remaining 5 are exactly R62..R66.
ACTUAL_REASONS="$(printf '%s\n' "$ACTUAL_TG" \
  | grep -v '^gold_local_minimal_profile_conformance$')"
EXPECTED_REASONS=$(cat << 'EOF'
gold_local_minimal_profile_descriptor_invalid
gold_local_minimal_profile_required_artifact_missing
gold_local_minimal_profile_required_make_target_missing
gold_local_minimal_profile_required_non_claim_missing
gold_local_minimal_profile_required_verifier_failed
EOF
)
[ "$ACTUAL_REASONS" = "$EXPECTED_REASONS" ] \
  || die "tg01 reason-token set drift; got:
$ACTUAL_REASONS
expected:
$EXPECTED_REASONS"
note_pass "tg01 taxonomy gate"

# ----------------------------------------------------------------------
# ss01: scoped SHA-256 snapshot (AFTER) byte-identical to BEFORE
# ----------------------------------------------------------------------
snapshot_scoped "$WORK/scoped.after"
diff -u "$WORK/scoped.before" "$WORK/scoped.after" \
  || die "ss01 scoped source files were mutated during Phase 3"
note_pass "ss01 scoped snapshot byte-identical"

# -- Final tally --------------------------------------------------------

if [ "$PASS_COUNT" -ne "$EXPECTED_COUNT" ]; then
  die "expected $EXPECTED_COUNT pass, got $PASS_COUNT"
fi
echo "ALL $PASS_COUNT/$EXPECTED_COUNT PASS"
