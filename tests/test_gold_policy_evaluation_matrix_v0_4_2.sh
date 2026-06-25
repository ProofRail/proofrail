#!/usr/bin/env bash
# tests/test_gold_policy_evaluation_matrix_v0_4_2.sh
#
# Regression test for the ProofRail v0.4.2 Gold Policy Evaluation Matrix
# package. v0.4.2 extends v0.4.1 with two new subjects (the runtime
# matrix and the derived evaluation report) for a 5-subject manifest,
# nine new ordered verifier checks (R30..R38), and the canonical
# runtime-scalar contract: the runner injects `decision_report_sha256`
# and `generated_at` into the runtime matrix. The v0.4.2 verifier
# DELEGATES the inherited 29 checks to the co-located v0.4.1 verifier
# (a repo tooling dependency); the v0.4.1 verifier in turn delegates
# its inherited 24 checks to the co-located v0.4.0 verifier.
#
# Numbered exercises (78 total):
#
#   Positive-path (6):
#     PP1   Pristine build with --self-validate
#     PP2   Pristine independent v0.4.2 verifier pass on the package
#     PP3   Inline structural check of manifest layout (5 subjects,
#           fixed roles, fixed order, bare-hex SHA-256, identifier
#           distinctness across the four-quartet)
#     PP4   Inline structural check of runtime matrix (template fields
#           preserved; runner-injected scalars `decision_report_sha256`
#           and `generated_at` present; subject [3] sha is bare hex)
#     PP5   Inline structural check of derived evaluation report
#           (5 matched evaluation rows, zero unmatched/uncovered/conflict,
#           cross-anchors source_decision_report_sha256 == subject[2].sha,
#           source_matrix_sha256 == subject[3].sha)
#     PP6   Inline identifier distinctness across the manifest quartet
#           (conformance_report_id, decision_report_id, matrix_id,
#           policy_evaluation_report_id) and the subject files'
#           cross-anchored equivalents.
#
#   Canonical verifier mutation cases (38 = 29 inherited + 9 v0.4.2):
#     case01..case29 — inherited reasons relayed verbatim via the
#                      v0.4.2 verifier's subprocess delegation to the
#                      co-located v0.4.1 verifier (which itself relays
#                      24 from v0.4.0).
#     case30  gold_policy_matrix_not_object
#     case31  gold_policy_matrix_schema_invalid
#     case32  gold_policy_matrix_binding_invalid
#     case33  gold_policy_matrix_entry_invalid
#     case34  gold_policy_evaluation_report_not_object
#     case35  gold_policy_evaluation_report_schema_invalid
#     case36  gold_policy_evaluation_report_binding_invalid
#     case37  gold_policy_evaluation_result_invalid
#     case38  gold_policy_evaluation_summary_invalid
#
#   Runtime-scalar canonical cases (3; the runner-injected scalars at
#   subject [3]'s decision_report_sha256 and generated_at):
#     rt1     drop matrix.decision_report_sha256 (missing required field
#             at subject[3]) folds to R31 gold_policy_matrix_schema_invalid.
#     rt1b    drop matrix.generated_at (missing required field at
#             subject[3]) folds to R31 gold_policy_matrix_schema_invalid.
#     rt2     replace matrix.decision_report_sha256 with a valid bare-hex
#             string that does NOT equal manifest.subjects[2].sha256;
#             this is a binding violation that folds to R32
#             gold_policy_matrix_binding_invalid (NOT R31, since the
#             value is bare hex and only the cross-anchor is broken).
#
#   Duplicate / secondary gold_manifest_invalid cases (18; all route to
#   gold_manifest_invalid; reported separately so the 38 canonical cases
#   remain exactly one-per-reason):
#     dup01   subject[0] path absolute
#     dup02   subject[1] path absolute
#     dup03   subject[2] path absolute
#     dup04   subject[3] path absolute  (matrix)
#     dup05   subject[4] path absolute  (evaluation report)
#     dup06   subject[0] path traversal
#     dup07   subject[3] path traversal (matrix)
#     dup08   subject[0] file missing on disk
#     dup09   subject[3] file missing on disk (matrix)
#     dup10   subject[4] file missing on disk (evaluation report)
#     dup11   subject[0] size_bytes mismatch
#     dup12   subject[3] sha256 mismatch
#     dup13   subject[4] sha256 mismatch
#     dup14   wrong subject count (4 entries)
#     dup15   wrong subject count (6 entries)
#     dup16   subject[3] role wrong
#     dup17   subject[4] role wrong
#     dup18   matrix_id == policy_evaluation_report_id (manifest quartet
#             distinctness collision; v0.4.2-specific)
#
#   Supplemental evaluation-report-binding case (2 exercises; both route
#   to R36, gold_policy_evaluation_report_binding_invalid; reported
#   separately from the duplicate manifest-invalid set because the
#   source_*_sha256 anchors live in the evaluation report, not in the
#   manifest):
#     sup01   evaluation report source_decision_report_sha256 !=
#             subjects[2].sha256
#     sup02   evaluation report source_matrix_sha256 !=
#             subjects[3].sha256
#
#   Runner-only refusal cases (6 exercises, 5 distinct reasons):
#     ro1     runner_input_path_missing
#     ro2     runner_input_path_forbidden       (absolute --input-package)
#     ro2b    runner_input_path_forbidden       (parent-traversal --input-package)
#     ro3     runner_input_file_missing
#     ro4     runner_input_read_failed          (directory, portable)
#     ro5     runner_input_json_invalid
#
#   Runner-relay-of-verifier (rel01):
#     rel01   --self-validate on a structurally bad v0.4.0-shaped input
#             package body relays the v0.4.2 verifier's relayed inherited
#             reason verbatim, NOT wrapped in a sixth runner-only code;
#             staging directory is removed.
#
#   Verifier-relay-of-inherited (rel02):
#     rel02   Mutation of the v0.4.0-shaped package body subject[0] triggers
#             the inherited v0.4.0 verifier reason gold_package_schema_invalid
#             via the v0.4.2 verifier's subprocess delegation to v0.4.1
#             which itself delegates to v0.4.0. The reason must be relayed
#             VERBATIM with no v0.4.2 wrapping, no INFRA: diagnostic, and
#             no R-code substitution.
#
#   Environment-failure INFRA case (env01):
#     env01   Temporarily move the co-located v0.4.1 verifier file; expect
#             the v0.4.2 verifier to emit `INFRA: co-located v0.4.1
#             verifier unavailable...` on stderr and exit 3 without
#             emitting any of the 38 verifier reasons or 5 runner-only
#             refusal names. The v0.4.1 verifier is restored via a trap
#             before the test exits, regardless of failure.
#
#   Coverage-summary positive determinism (sup03):
#     sup03   Build the package twice and confirm the matrix subject sha,
#             evaluation report subject sha, and aggregate evaluation
#             fingerprint are byte-identical; canonical-JSON determinism
#             is a v0.4.2 contract for the runtime matrix and the derived
#             evaluation report.
#
#   Limitations-block prohibited-token allowance (sup04):
#     sup04   The matrix template's scope_limitations and non_claims
#             arrays contain the strings "Gold" / "Platinum" (the
#             non-claims clause is required to enumerate these names).
#             Confirm the v0.4.2 verifier passes this case end-to-end:
#             the prohibited-gold-claim deny is scoped to the package
#             body's relying_party.display_name, NOT the limitations or
#             non_claims blocks.
#
#   Taxonomy gate (TG1):
#     TG1     Scan v0.4.2-owned files for reason-shaped tokens; every
#             such token must belong to the approved 38-reason verifier
#             set, the approved 5-reason runner-only set, or a narrow
#             documented allow-list. Additionally enforce an explicit
#             deny-list of environmental/wrapper escape token patterns
#             (substrings: see DENY_SUBSTRINGS in the TG1 block below)
#             so that any future drift toward wrapping environment
#             failures as public reasons trips the gate.
#
#   Scoped sha256 snapshot (SS):
#     SS      Scoped sha256 snapshot of committed v0.4.2-owned source
#             paths BEFORE and AFTER must be identical (the test does
#             not mutate v0.4.2-owned source files; env01 restores the
#             co-located v0.4.1 verifier before SS is taken).
#
# Notes on subprocess delegation:
#   The v0.4.2 verifier subprocess-invokes the co-located v0.4.1
#   verifier, which subprocess-invokes the co-located v0.4.0 verifier.
#   This is a chained repo tooling dependency; any change to either
#   co-located verifier requires rerunning the v0.4.0, v0.4.1, and
#   v0.4.2 regression suites. The env-failure path (missing co-located
#   v0.4.1 verifier) emits a non-reason-shaped INFRA: diagnostic and
#   never collapses into any of the 38 verifier reasons or 5 runner-only
#   refusal names.
#
# Hash-first re-anchoring:
#   Every mutation that lives INSIDE a subject body is followed by a
#   rehash_subject call to re-anchor the manifest's subject sha256 and
#   size_bytes. v0.4.2 uses BARE lowercase hex SHA-256 (no `sha256:`
#   label prefix) in every manifest sha256 field, every source_*_sha256
#   cross-anchor, the runtime matrix's decision_report_sha256, and
#   every aggregate fingerprint.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/gold/build_gold_policy_evaluation_matrix_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py"
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
MATRIX_FIX_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"

WORK="$(mktemp -d -t proofrail-v0.4.2-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

GEN_AT="2026-09-15T00:30:00Z"
MANIFEST_ID="proofrail-gold-policy-evaluation-matrix-manifest-test-001"
CONFORMANCE_REPORT_ID="proofrail-gold-policy-evaluation-matrix-conformance-test-001"
# v0.4.2 matrix template's decision_report_ref is wired to this exact
# string (fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json).
# The v0.4.2 verifier's R32 binding check requires the matrix
# template's decision_report_ref to equal the manifest's
# decision_report_id; this test mirrors the fixture's value.
DECISION_REPORT_ID="proofrail-gold-decision-report-demo-001"
POLICY_EVAL_REPORT_ID="proofrail-gold-policy-evaluation-report-test-001"

PACKAGE_REL="governed-reliance-scenarios.json"
CONFORMANCE_REL_FILE="silver-gold-governed-reliance-conformance-report.json"
DECISION_REL_FILE="gold-governed-reliance-decision-report.json"
MATRIX_REL_FILE="gold-policy-evaluation-matrix.json"
EVAL_REL_FILE="gold-policy-evaluation-report.json"
MANIFEST_REL_FILE="gold-policy-evaluation-matrix-package-manifest.json"

# --- Scoped sha256 snapshot of committed v0.4.2-owned source paths (BEFORE) ---
# The committed Makefile is excluded; it is shared across release versions
# and is mutated independently by the Phase 3 amendment.
# The temporary checkpoint at /tmp/proofrail-v0.4.2-checkpoint.md is
# explicitly outside the release surface and excluded from the snapshot.
SCOPED_FILES=(
  "schemas/gold-policy-evaluation-matrix-v0.1.0.md"
  "schemas/gold-policy-evaluation-report-v0.1.0.md"
  "schemas/gold-policy-evaluation-matrix-package-manifest-v0.1.0.md"
  "fixtures/gold-policy-evaluation-matrix-v0.4.2/README.md"
  "fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"
  "tools/gold/build_gold_policy_evaluation_matrix_v0_1_0.py"
  "tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py"
  "tests/test_gold_policy_evaluation_matrix_v0_4_2.sh"
  "docs/gold/gold-policy-evaluation-matrix-v0.4.2.md"
  "demos/gold-demo-003-policy-evaluation-matrix/README.md"
  "demos/gold-demo-003-policy-evaluation-matrix/demo-walkthrough.md"
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
echo "[step1] PP1 pristine v0.4.2 build with --self-validate"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --matrix-input "$MATRIX_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] PP2 pristine independent v0.4.2 verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of manifest layout.
# ---------------------------------------------------------------------------
echo "[step3] PP3 inline manifest layout check"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" <<'EOF'
import json, sys, re
mp = sys.argv[1]
m = json.loads(open(mp).read())
assert m["document_type"] == "proofrail.gold.policy_evaluation_matrix_package_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "gold.policy_evaluation_matrix.v0.4.2"
assert m["hash_algorithm"] == "sha256"
for field in ("manifest_id", "conformance_report_id", "decision_report_id",
              "matrix_id", "policy_evaluation_report_id",
              "package_id", "governed_reliance_demo_id"):
    assert isinstance(m[field], str) and m[field], field
# v0.4.2 manifest deliberately carries NO generic report_id.
assert "report_id" not in m, "v0.4.2 manifest must not carry generic report_id"
# Quartet identifier distinctness.
quartet = ("conformance_report_id", "decision_report_id",
           "matrix_id", "policy_evaluation_report_id")
vals = [m[k] for k in quartet]
assert len(set(vals)) == len(vals), f"quartet identifier collision: {vals}"
assert len(m["subjects"]) == 5, len(m["subjects"])
expected = [
  ("governed-reliance-scenarios.json", "governed_reliance_package"),
  ("silver-gold-governed-reliance-conformance-report.json", "conformance_report"),
  ("gold-governed-reliance-decision-report.json", "decision_report"),
  ("gold-policy-evaluation-matrix.json", "policy_evaluation_matrix"),
  ("gold-policy-evaluation-report.json", "policy_evaluation_report"),
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
# Step 4 (PP4): inline structural check of runtime matrix (subject [3]).
# Confirms the runner injected `decision_report_sha256` (bare-hex SHA-256
# matching subjects[2].sha256) and `generated_at` (echoed CLI arg).
# ---------------------------------------------------------------------------
echo "[step4] PP4 inline runtime matrix scalar injection check"
python3 - "$PRISTINE/$MATRIX_REL_FILE" "$PRISTINE/$MANIFEST_REL_FILE" "$GEN_AT" <<'EOF'
import json, sys, re
xp, mp, gen_at = sys.argv[1], sys.argv[2], sys.argv[3]
x = json.loads(open(xp).read())
m = json.loads(open(mp).read())
assert x["document_type"] == "proofrail.gold.policy_evaluation_matrix", x["document_type"]
assert x["schema_version"] == "v0.1.0"
assert x["profile"] == "gold.policy_evaluation_matrix.v0.4.2"
bare_hex = re.compile(r"^[0-9a-f]{64}$")
# Runner-injected scalars.
assert bare_hex.match(x["decision_report_sha256"]), x["decision_report_sha256"]
assert x["decision_report_sha256"] == m["subjects"][2]["sha256"], \
    "runtime matrix decision_report_sha256 must equal manifest.subjects[2].sha256"
assert x["generated_at"] == gen_at, (x["generated_at"], gen_at)
# Template-preserved fields.
assert x["matrix_id"] == m["matrix_id"]
assert x["package_id"] == m["package_id"]
assert x["governed_reliance_demo_id"] == m["governed_reliance_demo_id"]
assert x["decision_report_ref"] == m["decision_report_id"]
assert isinstance(x["matrix_rows"], list) and 1 <= len(x["matrix_rows"]) <= 10
assert isinstance(x["scope_limitations"], list) and x["scope_limitations"]
assert isinstance(x["non_claims"], list) and x["non_claims"]
# matrix_row_id grammar and per-row presence of injected closed-set fields.
mrow_re = re.compile(r"^mrow_(0[1-9]|10)$")
for i, row in enumerate(x["matrix_rows"]):
    assert mrow_re.match(row["matrix_row_id"]), (i, row["matrix_row_id"])
    expected_id = f"mrow_{i+1:02d}"
    assert row["matrix_row_id"] == expected_id, (i, row["matrix_row_id"], expected_id)
EOF

# ---------------------------------------------------------------------------
# Step 5 (PP5): inline structural check of derived evaluation report.
# Confirms 5 matched rows, zero unmatched/uncovered/conflict, and the
# source_*_sha256 cross-anchors to subjects[2] and subjects[3].
# ---------------------------------------------------------------------------
echo "[step5] PP5 inline evaluation report (5 matched) check"
python3 - "$PRISTINE/$EVAL_REL_FILE" "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$MATRIX_REL_FILE" <<'EOF'
import json, sys, re, hashlib
ep, mp, xp = sys.argv[1], sys.argv[2], sys.argv[3]
e = json.loads(open(ep).read())
m = json.loads(open(mp).read())
x = json.loads(open(xp).read())
assert e["document_type"] == "proofrail.gold.policy_evaluation_report", e["document_type"]
assert e["schema_version"] == "v0.1.0"
assert e["profile"] == "gold.policy_evaluation_matrix.v0.4.2"
assert e["package_id"] == m["package_id"]
assert e["governed_reliance_demo_id"] == m["governed_reliance_demo_id"]
assert e["matrix_id"] == m["matrix_id"]
assert e["policy_evaluation_report_id"] == m["policy_evaluation_report_id"]
bare_hex = re.compile(r"^[0-9a-f]{64}$")
assert bare_hex.match(e["source_decision_report_sha256"])
assert bare_hex.match(e["source_matrix_sha256"])
assert e["source_decision_report_sha256"] == m["subjects"][2]["sha256"], \
    "evaluation report source_decision_report_sha256 must equal subjects[2].sha256"
assert e["source_matrix_sha256"] == m["subjects"][3]["sha256"], \
    "evaluation report source_matrix_sha256 must equal subjects[3].sha256"
# Five matched rows expected against the canonical fixture pair.
assert isinstance(e["evaluation_rows"], list) and len(e["evaluation_rows"]) == 5
for row in e["evaluation_rows"]:
    assert row["evaluation_status"] == "matched", row["evaluation_status"]
# coverage_summary keys and values.
cs = e["coverage_summary"]
for field in ("decision_row_count", "matrix_row_count", "matched_count",
              "unmatched_matrix_row_count", "uncovered_decision_row_count",
              "conflict_count", "aggregate_evaluation_fingerprint"):
    assert field in cs, field
assert cs["matched_count"] == 5
assert cs["unmatched_matrix_row_count"] == 0
assert cs["uncovered_decision_row_count"] == 0
assert cs["conflict_count"] == 0
assert bare_hex.match(cs["aggregate_evaluation_fingerprint"])
# scope_limitations and non_claims mirror the matrix template.
assert e["scope_limitations"] == x["scope_limitations"]
assert e["non_claims"] == x["non_claims"]
EOF

# ---------------------------------------------------------------------------
# Step 6 (PP6): inline identifier distinctness at the file level.
# ---------------------------------------------------------------------------
echo "[step6] PP6 quartet identifier distinctness at file level"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$CONFORMANCE_REL_FILE" \
  "$PRISTINE/$DECISION_REL_FILE" "$PRISTINE/$MATRIX_REL_FILE" "$PRISTINE/$EVAL_REL_FILE" <<'EOF'
import json, sys
mp, cp, dp, xp, ep = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
m = json.loads(open(mp).read())
c = json.loads(open(cp).read())
d = json.loads(open(dp).read())
x = json.loads(open(xp).read())
e = json.loads(open(ep).read())
# Conformance report cross-anchors to top-level report_id (v0.4.0-shaped).
assert c["report_id"] == m["conformance_report_id"]
# Decision report cross-anchors to top-level decision_report_id (v0.4.1).
assert d["decision_report_id"] == m["decision_report_id"]
# Matrix cross-anchors to top-level matrix_id (v0.4.2).
assert x["matrix_id"] == m["matrix_id"]
# Evaluation report cross-anchors to top-level policy_evaluation_report_id (v0.4.2).
assert e["policy_evaluation_report_id"] == m["policy_evaluation_report_id"]
# Quartet pairwise distinctness.
ids = [m["conformance_report_id"], m["decision_report_id"],
       m["matrix_id"], m["policy_evaluation_report_id"]]
assert len(set(ids)) == 4, f"quartet identifier collision at file level: {ids}"
EOF

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# v0.4.2 uses BARE lowercase hex SHA-256 in manifest subject sha256
# fields. Rehash subject [idx] (0..4) after a body mutation.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "gold-policy-evaluation-matrix-package-manifest.json")
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
# v0.4.2 manifest serialization: sort_keys + compact separators + trailing newline.
# Does NOT recompute subject hashes by itself.
edit_manifest() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
mp = os.path.join(pkg, "gold-policy-evaluation-matrix-package-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the bundled conformance report.
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

# Edit the bundled decision report.
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

# Edit the runtime matrix subject [3].
edit_matrix() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
xp = os.path.join(pkg, "gold-policy-evaluation-matrix.json")
x = json.loads(open(xp).read())
exec(expr, {"x": x, "json": json})
open(xp, "w").write(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the evaluation report subject [4].
edit_evaluation() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
ep = os.path.join(pkg, "gold-policy-evaluation-report.json")
e = json.loads(open(ep).read())
exec(expr, {"e": e, "json": json})
open(ep, "w").write(json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n")
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
  # co-located v0.4.1 verifier).
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

echo "[cases] 38 canonical + 3 runtime-scalar + 18 duplicate + 2 sup-binding + 2 sup-extras + 6 runner-only + rel01 + rel02 + env01 + TG1 + SS"

# ===========================================================================
# Canonical verifier mutation cases (38 = 29 inherited + 9 v0.4.2).
# Cases 01..24 mutate the v0.4.0-shaped package body subject [0] and
# rely on the v0.4.2 verifier's subprocess delegation to v0.4.1 (which
# itself delegates to v0.4.0) to relay the inherited reason verbatim.
# Cases 25..29 mutate the bundled v0.4.1 decision report subject [2]
# and rely on the v0.4.2 verifier's delegation to v0.4.1 to relay the
# inherited v0.4.1-introduced reason verbatim.
# Cases 30..38 are v0.4.2-owned (R30..R38).
# ===========================================================================

# --- case01: gold_manifest_invalid (v0.4.2 manifest document_type) ----------
# This R01 fold is emitted by the v0.4.2 verifier's own Phase 1 manifest
# integrity check BEFORE the subprocess delegation step.
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:gold_manifest_invalid" "$T" "gold_manifest_invalid"

# --- case02: gold_package_not_object (relayed from v0.4.0 via v0.4.1) -------
T="$WORK/c02"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$PACKAGE_REL', 'w') as f:
    f.write(json.dumps([1,2,3], indent=2) + '\n')
"
rehash_subject "$T" 0
expect_verifier_fail "case02:gold_package_not_object" "$T" "gold_package_not_object"

# --- case03: gold_package_schema_invalid (relayed) --------------------------
T="$WORK/c03"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["document_type"] = "wrong"'
rehash_subject "$T" 0
expect_verifier_fail "case03:gold_package_schema_invalid" "$T" "gold_package_schema_invalid"

# --- case04: gold_profile_unsupported (relayed) -----------------------------
T="$WORK/c04"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["profile"] = "some.other.profile"'
rehash_subject "$T" 0
expect_verifier_fail "case04:gold_profile_unsupported" "$T" "gold_profile_unsupported"

# --- case05: gold_package_identity_invalid (relayed) ------------------------
# Package_id must remain consistent across body, manifest, decision report,
# matrix, and synthesized inherited manifests; grammar violation on all four
# reaches R05.
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["package_id"] = "BadID"'
edit_manifest "$T" 'm["package_id"] = "BadID"'
edit_decision "$T" 'd["package_id"] = "BadID"'
edit_matrix "$T" 'x["package_id"] = "BadID"'
edit_evaluation "$T" 'e["package_id"] = "BadID"'
rehash_subject "$T" 0
rehash_subject "$T" 2
rehash_subject "$T" 3
rehash_subject "$T" 4
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

# --- case25: gold_decision_report_not_object (relayed from v0.4.1) ----------
T="$WORK/c25"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$DECISION_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 2
expect_verifier_fail "case25:gold_decision_report_not_object" "$T" "gold_decision_report_not_object"

# --- case26: gold_decision_report_schema_invalid (relayed) ------------------
T="$WORK/c26"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["document_type"] = "wrong"'
rehash_subject "$T" 2
expect_verifier_fail "case26:gold_decision_report_schema_invalid" "$T" "gold_decision_report_schema_invalid"

# --- case27: gold_decision_report_binding_invalid (relayed) -----------------
T="$WORK/c27"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 2
expect_verifier_fail "case27:gold_decision_report_binding_invalid" "$T" "gold_decision_report_binding_invalid"

# --- case28: gold_decision_report_projection_invalid (relayed) --------------
T="$WORK/c28"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["decision_rows"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 2
expect_verifier_fail "case28:gold_decision_report_projection_invalid" "$T" "gold_decision_report_projection_invalid"

# --- case29: gold_decision_report_summary_invalid (relayed) -----------------
T="$WORK/c29"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["coverage_summary"]["decision_count"] = 42'
rehash_subject "$T" 2
expect_verifier_fail "case29:gold_decision_report_summary_invalid" "$T" "gold_decision_report_summary_invalid"

# --- case30: gold_policy_matrix_not_object ----------------------------------
# Replace the matrix subject [3] with a top-level JSON array.
T="$WORK/c30"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$MATRIX_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 3
expect_verifier_fail "case30:gold_policy_matrix_not_object" "$T" "gold_policy_matrix_not_object"

# --- case31: gold_policy_matrix_schema_invalid ------------------------------
# Mutate the matrix document_type so schema check fires before binding.
T="$WORK/c31"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["document_type"] = "wrong"'
rehash_subject "$T" 3
expect_verifier_fail "case31:gold_policy_matrix_schema_invalid" "$T" "gold_policy_matrix_schema_invalid"

# --- case32: gold_policy_matrix_binding_invalid -----------------------------
# Mutate the matrix's package_id so it disagrees with the manifest's
# package_id (cross-anchor binding). Schema-shape remains valid.
T="$WORK/c32"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 3
expect_verifier_fail "case32:gold_policy_matrix_binding_invalid" "$T" "gold_policy_matrix_binding_invalid"

# --- case33: gold_policy_matrix_entry_invalid -------------------------------
# Mutate matrix_rows[0].matrix_row_id to a valid-grammar but
# wrong-position id (`mrow_05` at idx 0). R31 grammar check accepts it;
# R33 expected-id check fires.
T="$WORK/c33"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["matrix_rows"][0]["matrix_row_id"] = "mrow_05"'
rehash_subject "$T" 3
expect_verifier_fail "case33:gold_policy_matrix_entry_invalid" "$T" "gold_policy_matrix_entry_invalid"

# --- case34: gold_policy_evaluation_report_not_object -----------------------
# Replace the evaluation report subject [4] with a top-level JSON array.
T="$WORK/c34"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$EVAL_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 4
expect_verifier_fail "case34:gold_policy_evaluation_report_not_object" "$T" "gold_policy_evaluation_report_not_object"

# --- case35: gold_policy_evaluation_report_schema_invalid -------------------
# Mutate the evaluation report's document_type so R35 schema check fires
# before any R36 binding check.
T="$WORK/c35"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["document_type"] = "wrong"'
rehash_subject "$T" 4
expect_verifier_fail "case35:gold_policy_evaluation_report_schema_invalid" "$T" "gold_policy_evaluation_report_schema_invalid"

# --- case36: gold_policy_evaluation_report_binding_invalid ------------------
# Mutate the evaluation report's package_id so it disagrees with the
# manifest's package_id; schema-shape remains valid.
T="$WORK/c36"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 4
expect_verifier_fail "case36:gold_policy_evaluation_report_binding_invalid" "$T" "gold_policy_evaluation_report_binding_invalid"

# --- case37: gold_policy_evaluation_result_invalid --------------------------
# Mutate evaluation_rows[0].decision_status so the re-derived row
# disagrees with the bundled row. Per the R37/R38 split, per-row drift
# routes to R37, NOT R38 (which is reserved for coverage_summary drift).
T="$WORK/c37"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["evaluation_rows"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 4
expect_verifier_fail "case37:gold_policy_evaluation_result_invalid" "$T" "gold_policy_evaluation_result_invalid"

# --- case38: gold_policy_evaluation_summary_invalid -------------------------
# Mutate coverage_summary.matched_count so the derived summary disagrees.
# Per the R37/R38 split, coverage_summary drift routes to R38.
T="$WORK/c38"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["coverage_summary"]["matched_count"] = 42'
rehash_subject "$T" 4
expect_verifier_fail "case38:gold_policy_evaluation_summary_invalid" "$T" "gold_policy_evaluation_summary_invalid"

# ===========================================================================
# Runtime-scalar canonical cases (3; runner-injected scalars at subject [3]).
# ===========================================================================

# --- rt1: drop matrix.decision_report_sha256 → R31 --------------------------
T="$WORK/rt1"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'del x["decision_report_sha256"]'
rehash_subject "$T" 3
expect_verifier_fail "rt1:matrix_decision_report_sha256_drop" "$T" "gold_policy_matrix_schema_invalid"

# --- rt1b: drop matrix.generated_at → R31 -----------------------------------
T="$WORK/rt1b"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'del x["generated_at"]'
rehash_subject "$T" 3
expect_verifier_fail "rt1b:matrix_generated_at_drop" "$T" "gold_policy_matrix_schema_invalid"

# --- rt2: matrix.decision_report_sha256 valid hex but wrong value → R32 -----
# A valid bare-hex value (so R31 grammar passes) that does NOT equal
# manifest.subjects[2].sha256 trips the R32 binding cross-anchor.
T="$WORK/rt2"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["decision_report_sha256"] = "f" * 64'
rehash_subject "$T" 3
expect_verifier_fail "rt2:matrix_decision_report_sha256_anchor_mismatch" "$T" "gold_policy_matrix_binding_invalid"

# ===========================================================================
# Duplicate gold_manifest_invalid cases (18; all route to that reason).
# ===========================================================================

# --- dup01: subject[0] path absolute ----------------------------------------
T="$WORK/d01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "dup01:subject_0_path_absolute" "$T" "gold_manifest_invalid"

# --- dup02: subject[1] path absolute ----------------------------------------
T="$WORK/d02"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "/etc/hostname"'
expect_verifier_fail "dup02:subject_1_path_absolute" "$T" "gold_manifest_invalid"

# --- dup03: subject[2] path absolute ----------------------------------------
T="$WORK/d03"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][2]["path"] = "/etc/shells"'
expect_verifier_fail "dup03:subject_2_path_absolute" "$T" "gold_manifest_invalid"

# --- dup04: subject[3] path absolute (matrix) -------------------------------
T="$WORK/d04"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][3]["path"] = "/etc/services"'
expect_verifier_fail "dup04:subject_3_path_absolute" "$T" "gold_manifest_invalid"

# --- dup05: subject[4] path absolute (evaluation report) --------------------
T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][4]["path"] = "/etc/protocols"'
expect_verifier_fail "dup05:subject_4_path_absolute" "$T" "gold_manifest_invalid"

# --- dup06: subject[0] path traversal ---------------------------------------
T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "../escape-pkg.json"'
expect_verifier_fail "dup06:subject_0_path_traversal" "$T" "gold_manifest_invalid"

# --- dup07: subject[3] path traversal (matrix) ------------------------------
T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][3]["path"] = "../escape-matrix.json"'
expect_verifier_fail "dup07:subject_3_path_traversal" "$T" "gold_manifest_invalid"

# --- dup08: subject[0] file missing on disk ---------------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
rm "$T/$PACKAGE_REL"
expect_verifier_fail "dup08:subject_0_file_absent" "$T" "gold_manifest_invalid"

# --- dup09: subject[3] file missing on disk (matrix) ------------------------
T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
rm "$T/$MATRIX_REL_FILE"
expect_verifier_fail "dup09:subject_3_file_absent" "$T" "gold_manifest_invalid"

# --- dup10: subject[4] file missing on disk (evaluation report) -------------
T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
rm "$T/$EVAL_REL_FILE"
expect_verifier_fail "dup10:subject_4_file_absent" "$T" "gold_manifest_invalid"

# --- dup11: subject[0] size_bytes mismatch ----------------------------------
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["size_bytes"] = 0'
expect_verifier_fail "dup11:subject_0_size_mismatch" "$T" "gold_manifest_invalid"

# --- dup12: subject[3] sha256 mismatch (matrix, bare hex) -------------------
T="$WORK/d12"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][3]["sha256"] = "f" * 64'
expect_verifier_fail "dup12:subject_3_sha_mismatch" "$T" "gold_manifest_invalid"

# --- dup13: subject[4] sha256 mismatch (evaluation report, bare hex) --------
T="$WORK/d13"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][4]["sha256"] = "0" * 64'
expect_verifier_fail "dup13:subject_4_sha_mismatch" "$T" "gold_manifest_invalid"

# --- dup14: wrong subject count (4 entries) ---------------------------------
T="$WORK/d14"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"] = m["subjects"][:4]'
expect_verifier_fail "dup14:wrong_subject_count_four" "$T" "gold_manifest_invalid"

# --- dup15: wrong subject count (6 entries) ---------------------------------
T="$WORK/d15"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"0"*64,"size_bytes":0})'
expect_verifier_fail "dup15:wrong_subject_count_six" "$T" "gold_manifest_invalid"

# --- dup16: subject[3] role wrong (matrix) ----------------------------------
T="$WORK/d16"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][3]["role"] = "wrong_role"'
expect_verifier_fail "dup16:subject_3_role_wrong" "$T" "gold_manifest_invalid"

# --- dup17: subject[4] role wrong (evaluation report) -----------------------
T="$WORK/d17"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][4]["role"] = "wrong_role"'
expect_verifier_fail "dup17:subject_4_role_wrong" "$T" "gold_manifest_invalid"

# --- dup18: matrix_id == policy_evaluation_report_id (quartet collision) ----
# Per the v0.4.2 Phase 1 quartet distinctness check; folds to R01.
T="$WORK/d18"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["matrix_id"] = m["policy_evaluation_report_id"]'
expect_verifier_fail "dup18:matrix_id_eval_report_id_collision" "$T" "gold_manifest_invalid"

# ===========================================================================
# Supplemental evaluation-report-binding cases (2; route to R36).
# Reported separately from the duplicate manifest-invalid set because
# the source_*_sha256 cross-anchors live in the evaluation report
# subject [4], not in the manifest.
# ===========================================================================

# --- sup01: evaluation source_decision_report_sha256 != subjects[2].sha256 --
T="$WORK/s01"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["source_decision_report_sha256"] = "0" * 64'
rehash_subject "$T" 4
expect_verifier_fail "sup01:eval_source_decision_sha_anchor_mismatch" "$T" "gold_policy_evaluation_report_binding_invalid"

# --- sup02: evaluation source_matrix_sha256 != subjects[3].sha256 ----------
T="$WORK/s02"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["source_matrix_sha256"] = "0" * 64'
rehash_subject "$T" 4
expect_verifier_fail "sup02:eval_source_matrix_sha_anchor_mismatch" "$T" "gold_policy_evaluation_report_binding_invalid"

# ===========================================================================
# Supplemental positive determinism (sup03): rebuild and confirm subject
# sha256 byte-identity for the matrix and evaluation report.
# ===========================================================================

REBUILT="$WORK/rebuilt"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --matrix-input "$MATRIX_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$REBUILT" \
  --force \
  --self-validate >/dev/null
python3 - "$PRISTINE/$MANIFEST_REL_FILE" "$REBUILT/$MANIFEST_REL_FILE" \
              "$PRISTINE/$EVAL_REL_FILE"     "$REBUILT/$EVAL_REL_FILE" <<'EOF'
import json, sys
m1 = json.loads(open(sys.argv[1]).read())
m2 = json.loads(open(sys.argv[2]).read())
assert m1["subjects"][3]["sha256"] == m2["subjects"][3]["sha256"], \
    "matrix subject sha drifted across rebuild"
assert m1["subjects"][4]["sha256"] == m2["subjects"][4]["sha256"], \
    "evaluation report subject sha drifted across rebuild"
e1 = json.loads(open(sys.argv[3]).read())
e2 = json.loads(open(sys.argv[4]).read())
assert e1["coverage_summary"]["aggregate_evaluation_fingerprint"] == \
       e2["coverage_summary"]["aggregate_evaluation_fingerprint"], \
    "aggregate_evaluation_fingerprint drifted across rebuild"
EOF
echo "  sup03:positive_determinism_matrix_and_eval: ok"

# ===========================================================================
# Supplemental limitations-block prohibited-token allowance (sup04).
# Confirms the matrix template's scope_limitations and non_claims
# entries contain the strings "Gold" / "Platinum" (the deny on
# prohibited gold claims is scoped to the package body's
# relying_party.display_name, NOT the limitations/non_claims blocks).
# The pristine PP1 build already passed end-to-end, but this exercise
# documents the explicit allowance.
# ===========================================================================

python3 - "$PRISTINE/$MATRIX_REL_FILE" "$PRISTINE/$EVAL_REL_FILE" <<'EOF'
import json, sys
x = json.loads(open(sys.argv[1]).read())
e = json.loads(open(sys.argv[2]).read())
sl_blob = " ".join(x["scope_limitations"]) + " " + " ".join(x["non_claims"])
assert "Gold" in sl_blob, "matrix limitations/non_claims must mention Gold"
assert "Platinum" in sl_blob, "matrix limitations/non_claims must mention Platinum"
el_blob = " ".join(e["scope_limitations"]) + " " + " ".join(e["non_claims"])
assert "Gold" in el_blob, "evaluation limitations/non_claims must mention Gold"
assert "Platinum" in el_blob, "evaluation limitations/non_claims must mention Platinum"
EOF
echo "  sup04:limitations_block_prohibited_token_allowance: ok"

# ===========================================================================
# Runner-only refusal cases (6 exercises, 5 distinct reasons). The
# runner's _preflight_input_path() runs first against --input-package;
# all six exercises target --input-package so the refusal fires before
# --matrix-input is inspected. --matrix-input is passed as the canonical
# fixture path to avoid ambiguity.
# ===========================================================================

# --- ro1: runner_input_path_missing -----------------------------------------
RO1_OUT="$WORK/ro1-out"
expect_runner_fail "ro1:runner_input_path_missing" \
  "runner_input_path_missing" \
  "$RO1_OUT" \
  "$RUNNER" \
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/_test_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --input-package "$BAD_INPUT_REL" \
    --matrix-input "$MATRIX_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
# Runner-relay-of-verifier (rel01). The runner relays the v0.4.2
# verifier's relayed inherited reason UNCHANGED; it does NOT wrap it
# in a sixth runner-only code. Staging directory must be cleaned up
# and destination must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
REL_INPUT_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/_test_relay_bad.json"
REL_INPUT_ABS="$REPO_ROOT/$REL_INPUT_REL"
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
  --matrix-input "$MATRIX_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
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
# The relayed reason must be the inherited v0.4.0-shaped structural
# reason (relayed through v0.4.1 to v0.4.2 to the runner).
if ! echo "$rel_out" | grep -qE "^FAIL: gold_package_schema_invalid:"; then
  echo "FAIL: rel01: expected inherited verifier reason relayed, got:"
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
echo "  rel01:runner_relay_of_verifier_failure: ok (inherited verifier reason relayed unchanged)"

# ===========================================================================
# Verifier-relay-of-inherited (rel02). The v0.4.2 verifier delegates
# inherited 29 checks to the co-located v0.4.1 verifier (which itself
# delegates 24 to v0.4.0) via subprocess. Mutating the package body to
# trigger an inherited non-R01 reason must surface that reason verbatim
# with no v0.4.2 wrapping. This is a dedicated negative-assertion
# against any future drift toward wrapping inherited reasons in a
# v0.4.2-specific code.
# ===========================================================================

T="$WORK/rel02"
fresh_copy "$PRISTINE" "$T"
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
  echo "----- v0.4.2 verifier output -----"
  echo "$rel2_out"
  echo "----------------------------------"
  exit 1
fi
# Must NOT be wrapped in any v0.4.2-introduced reason.
for v042_only in gold_policy_matrix_not_object \
                 gold_policy_matrix_schema_invalid \
                 gold_policy_matrix_binding_invalid \
                 gold_policy_matrix_entry_invalid \
                 gold_policy_evaluation_report_not_object \
                 gold_policy_evaluation_report_schema_invalid \
                 gold_policy_evaluation_report_binding_invalid \
                 gold_policy_evaluation_result_invalid \
                 gold_policy_evaluation_summary_invalid; do
  if echo "$rel2_out" | grep -qE "^FAIL: ${v042_only}:"; then
    echo "FAIL: rel02: v0.4.2 verifier wrapped inherited reason in $v042_only"
    echo "$rel2_out"
    exit 1
  fi
done
# Must NOT wrap as a runner-only refusal (verifier never emits those).
for ronly in runner_input_path_missing runner_input_path_forbidden \
             runner_input_file_missing runner_input_read_failed \
             runner_input_json_invalid; do
  if echo "$rel2_out" | grep -qE "^FAIL: ${ronly}:"; then
    echo "FAIL: rel02: v0.4.2 verifier emitted runner-only refusal $ronly"
    echo "$rel2_out"
    exit 1
  fi
done
# Must NOT emit any INFRA: diagnostic on a real package defect.
if echo "$rel2_out" | grep -q "^INFRA:"; then
  echo "FAIL: rel02: v0.4.2 verifier emitted INFRA: on a real package defect"
  echo "$rel2_out"
  exit 1
fi
echo "  rel02:verifier_relay_of_inherited_failure: ok (gold_package_schema_invalid relayed unchanged)"

# ===========================================================================
# Environment-failure (env01). Temporarily move the co-located v0.4.1
# verifier file. The v0.4.2 verifier must emit `INFRA: co-located
# v0.4.1 verifier unavailable...` on stderr and exit 3 without
# emitting any of the 38 verifier reasons or 5 runner-only refusal
# names. The v0.4.1 verifier is restored via trap before exit.
# ===========================================================================

V041_VERIFIER_REAL="$REPO_ROOT/tools/gold/verify_gold_decision_report_hardening_v0_1_0.py"
V041_VERIFIER_SAVE="$WORK/v041_verifier_backup.py"
restore_v041() {
  if [ -f "$V041_VERIFIER_SAVE" ] && [ ! -f "$V041_VERIFIER_REAL" ]; then
    mv "$V041_VERIFIER_SAVE" "$V041_VERIFIER_REAL"
  fi
}
trap 'restore_v041; rm -rf "$WORK"' EXIT

mv "$V041_VERIFIER_REAL" "$V041_VERIFIER_SAVE"

set +e
env_out="$(python3 "$VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" 2>&1)"
env_rc=$?
set -e

# Restore immediately so any subsequent failure path leaves the
# repo state clean.
restore_v041

if [ "$env_rc" -ne 3 ]; then
  echo "FAIL: env01: expected exit 3 (INFRA), got $env_rc"
  echo "$env_out"
  exit 1
fi
if ! echo "$env_out" | grep -qE "^INFRA: co-located v0\.4\.1 verifier unavailable"; then
  echo "FAIL: env01: expected INFRA: co-located v0.4.1 verifier unavailable diagnostic"
  echo "----- v0.4.2 verifier output -----"
  echo "$env_out"
  echo "----------------------------------"
  exit 1
fi
# Must NOT collapse into any of the 38 verifier reasons.
for r in gold_manifest_invalid gold_package_not_object \
         gold_package_schema_invalid gold_profile_unsupported \
         gold_package_identity_invalid silver_verification_input_invalid \
         silver_handoff_input_invalid policy_pack_input_invalid \
         registry_lite_input_invalid control_crosswalk_input_invalid \
         governed_decision_set_invalid governed_decision_entry_invalid \
         decision_subject_binding_invalid decision_policy_binding_invalid \
         decision_registry_binding_invalid decision_action_scope_invalid \
         decision_status_invalid acceptance_path_invalid \
         rejection_path_invalid challenge_path_invalid \
         withdrawal_path_invalid supersession_path_invalid \
         non_claims_missing prohibited_gold_claim_present \
         gold_decision_report_not_object gold_decision_report_schema_invalid \
         gold_decision_report_binding_invalid \
         gold_decision_report_projection_invalid \
         gold_decision_report_summary_invalid \
         gold_policy_matrix_not_object gold_policy_matrix_schema_invalid \
         gold_policy_matrix_binding_invalid gold_policy_matrix_entry_invalid \
         gold_policy_evaluation_report_not_object \
         gold_policy_evaluation_report_schema_invalid \
         gold_policy_evaluation_report_binding_invalid \
         gold_policy_evaluation_result_invalid \
         gold_policy_evaluation_summary_invalid; do
  if echo "$env_out" | grep -qE "^FAIL: ${r}:"; then
    echo "FAIL: env01: environment failure collapsed into verifier reason $r"
    echo "$env_out"
    exit 1
  fi
done
# Must NOT collapse into any runner-only refusal name either.
for ronly in runner_input_path_missing runner_input_path_forbidden \
             runner_input_file_missing runner_input_read_failed \
             runner_input_json_invalid; do
  if echo "$env_out" | grep -qE "^FAIL: ${ronly}:"; then
    echo "FAIL: env01: environment failure collapsed into runner-only refusal $ronly"
    echo "$env_out"
    exit 1
  fi
done
echo "  env01:environment_failure_v041_verifier_unavailable: ok (INFRA: emitted, exit 3)"

# ===========================================================================
# Taxonomy gate (TG1).
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.4.2-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

# 38 approved verifier reasons (29 inherited from v0.4.0/v0.4.1 + 9 v0.4.2).
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
    # inherited from v0.4.1:
    "gold_decision_report_not_object",
    "gold_decision_report_schema_invalid",
    "gold_decision_report_binding_invalid",
    "gold_decision_report_projection_invalid",
    "gold_decision_report_summary_invalid",
    # introduced by v0.4.2:
    "gold_policy_matrix_not_object",
    "gold_policy_matrix_schema_invalid",
    "gold_policy_matrix_binding_invalid",
    "gold_policy_matrix_entry_invalid",
    "gold_policy_evaluation_report_not_object",
    "gold_policy_evaluation_report_schema_invalid",
    "gold_policy_evaluation_report_binding_invalid",
    "gold_policy_evaluation_result_invalid",
    "gold_policy_evaluation_summary_invalid",
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# TG1 ALLOWLIST DISCIPLINE (v0.4.2)
# ---------------------------------
# Per Phase 0 amendment lock: the v0.4.2 data-field allowlist target was
# EMPTY for v0.4.2-OWNED data fields. None of the v0.4.2 coverage-summary
# keys end in _present/_missing/_invalid/_failed/_forbidden/_unsupported/
# _not_object, so no v0.4.2-INTRODUCED data-field name trips
# REASON_FILTER.
#
# However, the v0.4.2 runner internally derives a v0.4.1 decision report
# (it inherits the v0.4.1 decision-report hardening surface verbatim), so
# the v0.4.1 decision-report schema's `coverage_summary` enum-presence
# data-field names appear inside the v0.4.2 build tool. Those names are
# inherited verbatim from v0.4.1 and were already allowlisted under the
# v0.4.1 TG1 with identical justification. They are LITERAL JSON FIELD
# NAMES under coverage_summary, not public reasons.
#
# Adding any further entry requires (a) the token is a verbatim data-field
# name already present in the v0.4.1 or v0.4.2 schema, (b) a comment
# pointing at the schema clause that defines it, and (c) checkpoint-
# justified amendment per Phase 3 constraint #1.
ALLOWED_NON_REASON_TOKENS: set[str] = {
    # v0.4.1 decision-report coverage_summary enum-presence field names
    # (schemas/gold-governed-reliance-decision-report-v0.1.0.md,
    # `coverage_summary` clause). The v0.4.2 runner derives a v0.4.1
    # decision report internally and references these literal field
    # names. They terminate in `_present`, so REASON_FILTER admits
    # them, but they are inherited v0.4.1 data-field names, NOT public
    # reasons.
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
# Per the v0.4.1 deny-list pattern, extended to include v042_verifier.
# Substrings are spelled with explicit string concatenation so that the
# gate's own source does NOT contain a whole reason-shaped deny token
# (otherwise the deny-list literal would self-trip the gate when it
# scans this test file). The constituent halves never satisfy the
# REASON_FILTER suffix on their own.
DENY_SUBSTRINGS = (
    "v040" + "_verifier",
    "v041" + "_verifier",
    "v042" + "_verifier",
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

V0_4_2_FILES = [
    "schemas/gold-policy-evaluation-matrix-v0.1.0.md",
    "schemas/gold-policy-evaluation-report-v0.1.0.md",
    "schemas/gold-policy-evaluation-matrix-package-manifest-v0.1.0.md",
    "fixtures/gold-policy-evaluation-matrix-v0.4.2/README.md",
    "fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json",
    "tools/gold/build_gold_policy_evaluation_matrix_v0_1_0.py",
    "tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py",
    "tests/test_gold_policy_evaluation_matrix_v0_4_2.sh",
    "docs/gold/gold-policy-evaluation-matrix-v0.4.2.md",
    "demos/gold-demo-003-policy-evaluation-matrix/README.md",
    "demos/gold-demo-003-policy-evaluation-matrix/demo-walkthrough.md",
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

for rel in V0_4_2_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.4.2-owned file: {rel}")
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
        "v0.4.2-owned surface area",
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
echo "PASS: tests/test_gold_policy_evaluation_matrix_v0_4_2.sh"
echo "  78/78 exercises:"
echo "    - 6 positive-path (PP1..PP6)"
echo "    - 38 canonical verifier reasons (case01..case38)"
echo "        24 inherited from v0.4.0 via subprocess delegation"
echo "        5  inherited from v0.4.1 via subprocess delegation"
echo "        9  v0.4.2-introduced (R30..R38)"
echo "    - 3 runtime-scalar canonicals (rt1, rt1b, rt2;"
echo "        fold to R31 missing / R32 mismatched)"
echo "    - 18 duplicate / secondary manifest-invalid (dup01..dup18)"
echo "    - 4 supplementals (sup01, sup02 binding;"
echo "        sup03 positive determinism;"
echo "        sup04 limitations-block prohibited-token allowance)"
echo "    - 6 runner-only refusal exercises (ro1, ro2, ro2b, ro3..ro5;"
echo "        covering exactly the locked 5 runner-only reasons)"
echo "    - 1 runner-relay-of-verifier (rel01)"
echo "    - 1 verifier-relay-of-inherited (rel02)"
echo "    - 1 environment-failure INFRA diagnostic (env01)"
echo "    - 1 taxonomy gate with environmental-wrapper deny-list (TG1)"
echo "    - 1 scoped sha256 snapshot equality (SS)"
