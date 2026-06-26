#!/usr/bin/env bash
# tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh
#
# Phase 3 regression harness for the ProofRail v0.4.3 Gold Challenge
# Lifecycle Lite package. v0.4.3 extends v0.4.2 with two new subjects
# (the hand-authored runtime records body and the derived lifecycle
# report) for a 7-subject manifest, ten new ordered verifier checks
# (R39..R48), and the canonical runtime-scalar contract: the runner
# injects top-level `policy_evaluation_report_sha256`, top-level
# `generated_at`, and per-record `lifecycle_fingerprint` into the
# runtime records body. The v0.4.3 verifier DELEGATES the inherited 38
# checks to the co-located v0.4.2 verifier (a repo tooling dependency);
# the v0.4.2 verifier in turn delegates 29 to v0.4.1 which delegates
# 24 to v0.4.0.
#
# Numbered exercises (Phase 2 = 8; Phase 3 = 8 + 48 + 4 + 23 + 5 + 6
# + 1 + 1 + 1 + 1 = 98 total):
#
#   Positive-path (6):
#     PP1   Pristine v0.4.3 build with --self-validate
#     PP2   Pristine independent v0.4.3 verifier pass
#     PP3   Inline manifest layout (7 subjects, 6-ID collision class)
#     PP4   Inline runtime records body scalar injection
#     PP5   Inline lifecycle report (5 rows + coverage_summary)
#     PP6   Inline 6-ID file-level distinctness
#
#   Canonical verifier mutation cases (48 = 38 inherited + 10 v0.4.3):
#     case01..case24  inherited from v0.4.0 (R01..R24) relayed via
#                     v0.4.3 -> v0.4.2 -> v0.4.1 -> v0.4.0
#     case25..case29  inherited from v0.4.1 (R25..R29 decision report)
#     case30..case38  inherited from v0.4.2 (R30..R38 matrix / eval)
#     case39  gold_challenge_lifecycle_records_not_object       (R39)
#     case40  gold_challenge_lifecycle_records_schema_invalid    (R40)
#     case41  gold_challenge_lifecycle_records_binding_invalid   (R41)
#     case42  gold_challenge_lifecycle_event_invalid             (R42)
#     case43  gold_challenge_lifecycle_transition_invalid        (R43)
#     case44  gold_challenge_lifecycle_report_not_object         (R44)
#     case45  gold_challenge_lifecycle_report_schema_invalid     (R45)
#     case46  gold_challenge_lifecycle_report_binding_invalid    (R46)
#     case47  gold_challenge_lifecycle_projection_invalid        (R47)
#     case48  gold_challenge_lifecycle_summary_invalid           (R48)
#
#   Runtime-scalar canonical cases (4; runner-injected scalars at
#   subject [5]):
#     rt1    drop records.policy_evaluation_report_sha256 -> R40
#     rt1b   drop records.generated_at                    -> R40
#     rt2    valid-hex records.policy_evaluation_report_sha256
#            != subjects[4].sha256                        -> R41
#     rt3    drop lifecycle_records[0].lifecycle_fingerprint -> R40
#
#   Duplicate gold_manifest_invalid cases (23; all route to R01):
#     dup01..dup07   subject[0..6] path absolute
#     dup08..dup10   subject path traversal (subj 0, 5, 6)
#     dup11..dup12   subject file missing on disk (records, report)
#     dup13..dup14   subject size_bytes mismatch (records, report)
#     dup15..dup16   subject sha256 mismatch (records, report)
#     dup17, dup18   wrong subject count (6 and 8)
#     dup19, dup20   subject role wrong (records, report)
#     dup21          challenge_lifecycle_record_set_id ==
#                    conformance_report_id (6-ID collision)
#     dup22          challenge_lifecycle_report_id ==
#                    policy_evaluation_report_id (6-ID collision)
#     dup23          challenge_lifecycle_report_id ==
#                    challenge_lifecycle_record_set_id (6-ID collision)
#
#   Supplementals (5; R42x1, R43x3, R46x1):
#     sup01  R42 withdrawn current_status without withdrawal_record_ref
#     sup02  R43 first event is not `filed`
#            (distinct from case43: targets lc-003 with under_review
#            rather than lc-001 with acknowledged)
#     sup03  R43 event occurs after a terminal event
#     sup04  R43 current_status disagrees with final event_status
#     sup05  R46 challenge_lifecycle_report_id collides with
#            policy_evaluation_report_id at the lifecycle report
#            body level (manifest unchanged; subject[6] sha256
#            recomputed so body integrity check is reached)
#
#   Runner-only refusal cases (6 exercises, 5 distinct reasons):
#     ro1   runner_input_path_missing
#     ro2   runner_input_path_forbidden       (absolute --input-package)
#     ro2b  runner_input_path_forbidden       (parent-traversal)
#     ro3   runner_input_file_missing
#     ro4   runner_input_read_failed          (directory, portable)
#     ro5   runner_input_json_invalid
#
#   Runner-relay-of-verifier (rel01):
#     rel01  Structurally bad v0.4.0-shaped --input-package; --self-
#            validate relays the inherited verifier reason verbatim,
#            unwrapped; staging dir cleaned up; destination not made.
#
#   Verifier-relay-of-inherited (rel02):
#     rel02  Mutation of v0.4.0-shaped subject [0] triggers
#            gold_package_schema_invalid via the v0.4.3 -> v0.4.2 ->
#            v0.4.1 -> v0.4.0 chained subprocess delegation. The
#            reason must be relayed VERBATIM with no v0.4.3 wrapping,
#            no INFRA: diagnostic, and no R-code substitution.
#
#   Environment-failure INFRA case (env01) — non-destructive trap:
#     env01  Copy the v0.4.3 verifier into a tempdir WITHOUT copying
#            its co-located v0.4.2 sibling. The copied v0.4.3 verifier
#            resolves GOLD_V042_VERIFIER relative to its own __file__
#            and finds nothing, emitting `INFRA: co-located v0.4.2
#            verifier unavailable...` on stderr + exit 3. The real
#            on-disk co-located verifiers are NEVER touched, so the
#            SS snapshot equality is preserved.
#
#   Positive determinism (sup_det):
#     sup_det Rebuild the package and confirm records body subject
#             sha, lifecycle report subject sha, every per-record
#             lifecycle_fingerprint, and report_fingerprint are
#             byte-identical across the two builds.
#
#   Taxonomy gate (TG1):
#     TG1    Scan v0.4.3-owned files for reason-shaped tokens; every
#            such token must belong to the approved 48-reason verifier
#            set, the approved 5-reason runner-only set, or a narrow
#            inherited data-field allowlist. Additionally enforce an
#            explicit deny-list of environmental/wrapper escape token
#            patterns so future drift toward wrapping environment
#            failures as public reasons trips the gate.
#
#   Scoped sha256 snapshot (SS):
#     SS     Scoped sha256 snapshot of v0.4.3-owned source paths
#            BEFORE and AFTER must be identical (Phase 3 performs no
#            mutations on v0.4.3-owned source files; the env01 trap
#            is non-destructive and uses only a tempdir copy of the
#            verifier).
#
# Notes on subprocess delegation:
#   The v0.4.3 verifier subprocess-invokes the co-located v0.4.2
#   verifier, which subprocess-invokes the v0.4.1 verifier, which
#   subprocess-invokes the v0.4.0 verifier. This is a chained repo
#   tooling dependency; any change to any co-located verifier requires
#   rerunning v0.4.0, v0.4.1, v0.4.2, and v0.4.3 regression suites.
#   The env-failure path (missing v0.4.2 verifier) emits a non-
#   reason-shaped `INFRA:` diagnostic and never collapses into any of
#   the 48 verifier reasons or 5 runner-only refusal names.
#
# Hash-first re-anchoring:
#   Every mutation that lives INSIDE a subject body is followed by a
#   rehash_subject call to re-anchor the manifest's subject sha256 and
#   size_bytes. v0.4.3 uses BARE lowercase hex SHA-256 (no `sha256:`
#   label prefix) in every manifest sha256 field, every source_*_sha256
#   cross-anchor, the runtime records body's
#   `policy_evaluation_report_sha256`, every per-record
#   `lifecycle_fingerprint`, and the lifecycle report's
#   `report_fingerprint`.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/tools/gold/build_gold_challenge_lifecycle_lite_v0_1_0.py"
VERIFIER="$REPO_ROOT/tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py"
PACKAGE_FIX_REL="fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json"
MATRIX_FIX_REL="fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json"
LIFECYCLE_FIX_REL="fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json"

WORK="$(mktemp -d -t proofrail-v0.4.3-test.XXXXXX)"
# Repo-local v0.4.3/test-owned scratch path for runner-input bad-input
# files (ro5, rel01). These files MUST live inside the repo because
# the runner's path preflight rejects absolute paths and traversal
# segments, which would otherwise mask runner_input_json_invalid
# (ro5) and the verifier-relay (rel01) under
# runner_input_path_forbidden. The scratch path is NOT a v0.4.3-owned
# source path and is NOT in the scoped SS source-set. v0.4.3 transient
# files MUST NEVER be written under any inherited-tier (v0.4.0,
# v0.4.1, v0.4.2) fixture, tool, or schema directory.
TMP_TEST_SCRATCH="$REPO_ROOT/tests/_tmp_gold_challenge_lifecycle_lite_v0_4_3"
TMP_TEST_SCRATCH_REL="tests/_tmp_gold_challenge_lifecycle_lite_v0_4_3"
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

GEN_AT="2026-10-01T00:30:00Z"
MANIFEST_ID="proofrail-gold-challenge-lifecycle-lite-manifest-test-001"
CONFORMANCE_REPORT_ID="proofrail-gold-challenge-lifecycle-lite-conformance-test-001"
# The v0.4.2 matrix template's `decision_report_ref` is hard-wired to
# this exact string (fixtures/gold-policy-evaluation-matrix-v0.4.2/
# policy-evaluation-matrix.json). The inherited v0.4.2 verifier's R32
# binding check (relayed through v0.4.3) requires the matrix template's
# decision_report_ref to equal the manifest's decision_report_id; this
# test mirrors that fixture value.
DECISION_REPORT_ID="proofrail-gold-decision-report-demo-001"
# The v0.4.3 records body template's `policy_evaluation_report_ref` is
# hard-wired to this string (fixtures/gold-challenge-lifecycle-lite-
# v0.4.3/challenge-lifecycle-records.json). The v0.4.3 verifier's R41
# binding check requires the manifest's policy_evaluation_report_id to
# equal the records body's policy_evaluation_report_ref; this test
# mirrors that fixture value. The same value flows into the v0.4.2
# inherited evaluation report's policy_evaluation_report_id.
POLICY_EVAL_REPORT_ID="proofrail-gold-policy-evaluation-report-demo-001"
CHALLENGE_LIFECYCLE_REPORT_ID="proofrail-gold-challenge-lifecycle-report-test-001"

# Subject file names (mirroring the v0.4.3 runner / verifier module
# constants `*_SUBJECT_PATH`).
PACKAGE_REL="governed-reliance-scenarios.json"
CONFORMANCE_REL_FILE="silver-gold-governed-reliance-conformance-report.json"
DECISION_REL_FILE="gold-governed-reliance-decision-report.json"
MATRIX_REL_FILE="gold-policy-evaluation-matrix.json"
EVAL_REL_FILE="gold-policy-evaluation-report.json"
RECORDS_REL_FILE="challenge-lifecycle-records.json"
LIFECYCLE_REPORT_REL_FILE="gold-challenge-lifecycle-report.json"
MANIFEST_REL_FILE="gold-challenge-lifecycle-package-manifest.json"

# --- Scoped sha256 snapshot of committed v0.4.3-owned source paths (BEFORE) ---
# The committed Makefile is excluded; it is shared across release
# versions and is mutated independently by future amendments. Phase 2
# does not yet ship the v0.4.3 doc or demo files; those will be added
# to SCOPED_FILES in a later phase.
SCOPED_FILES=(
  "schemas/gold-challenge-lifecycle-records-v0.1.0.md"
  "schemas/gold-challenge-lifecycle-report-v0.1.0.md"
  "schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md"
  "fixtures/gold-challenge-lifecycle-lite-v0.4.3/README.md"
  "fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json"
  "tools/gold/build_gold_challenge_lifecycle_lite_v0_1_0.py"
  "tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py"
  "tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh"
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
echo "[step1] PP1 pristine v0.4.3 build with --self-validate"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --matrix-input "$MATRIX_FIX_REL" \
  --lifecycle-input "$LIFECYCLE_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
  --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$PRISTINE" \
  --force \
  --self-validate >/dev/null

# ---------------------------------------------------------------------------
# Step 2 (PP2): pristine independent verifier pass.
# ---------------------------------------------------------------------------
echo "[step2] PP2 pristine independent v0.4.3 verifier pass"
python3 "$VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" >/dev/null

# ---------------------------------------------------------------------------
# Step 3 (PP3): inline structural check of manifest layout.
# Confirms the 7-subject manifest shape, fixed roles, fixed order, bare-hex
# SHA-256, and 6-ID pairwise distinctness (conformance_report_id,
# decision_report_id, matrix_id, policy_evaluation_report_id,
# challenge_lifecycle_record_set_id, challenge_lifecycle_report_id).
# ---------------------------------------------------------------------------
echo "[step3] PP3 inline manifest layout check"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" <<'EOF'
import json, sys, re
mp = sys.argv[1]
m = json.loads(open(mp).read())
assert m["document_type"] == "proofrail.gold.challenge_lifecycle_package_manifest", m["document_type"]
assert m["schema_version"] == "v0.1.0"
assert m["proofrail_release"] == "gold.challenge_lifecycle_lite.v0.4.3"
assert m["hash_algorithm"] == "sha256"
for field in ("manifest_id", "conformance_report_id", "decision_report_id",
              "matrix_id", "policy_evaluation_report_id",
              "challenge_lifecycle_record_set_id",
              "challenge_lifecycle_report_id",
              "package_id", "governed_reliance_demo_id"):
    assert isinstance(m[field], str) and m[field], field
# v0.4.3 manifest deliberately carries NO generic report_id.
assert "report_id" not in m, "v0.4.3 manifest must not carry generic report_id"
# 6-ID pairwise distinctness (the v0.4.3 collision class).
collision = ("conformance_report_id", "decision_report_id",
             "matrix_id", "policy_evaluation_report_id",
             "challenge_lifecycle_record_set_id",
             "challenge_lifecycle_report_id")
vals = [m[k] for k in collision]
assert len(set(vals)) == len(vals), f"6-ID collision-class violation: {vals}"
assert len(m["subjects"]) == 7, len(m["subjects"])
expected = [
  ("governed-reliance-scenarios.json", "governed_reliance_package"),
  ("silver-gold-governed-reliance-conformance-report.json", "conformance_report"),
  ("gold-governed-reliance-decision-report.json", "decision_report"),
  ("gold-policy-evaluation-matrix.json", "policy_evaluation_matrix"),
  ("gold-policy-evaluation-report.json", "policy_evaluation_report"),
  ("challenge-lifecycle-records.json", "challenge_lifecycle_records"),
  ("gold-challenge-lifecycle-report.json", "challenge_lifecycle_report"),
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
# Step 4 (PP4): inline structural check of runtime records body (subject [5]).
# Confirms the runner injected top-level `policy_evaluation_report_sha256`
# (bare-hex SHA-256 matching subjects[4].sha256), top-level `generated_at`
# (echoed CLI arg), and per-record `lifecycle_fingerprint` for each of
# the 5 lifecycle records.
# ---------------------------------------------------------------------------
echo "[step4] PP4 inline runtime records body scalar injection check"
python3 - "$PRISTINE/$RECORDS_REL_FILE" "$PRISTINE/$MANIFEST_REL_FILE" "$GEN_AT" <<'EOF'
import json, sys, re
rp, mp, gen_at = sys.argv[1], sys.argv[2], sys.argv[3]
r = json.loads(open(rp).read())
m = json.loads(open(mp).read())
assert r["document_type"] == "proofrail.gold.challenge_lifecycle_records", r["document_type"]
assert r["schema_version"] == "v0.1.0"
assert r["profile"] == "gold.challenge_lifecycle_lite.v0.4.3"
bare_hex = re.compile(r"^[0-9a-f]{64}$")
# Runner-injected top-level scalars.
assert bare_hex.match(r["policy_evaluation_report_sha256"]), r["policy_evaluation_report_sha256"]
assert r["policy_evaluation_report_sha256"] == m["subjects"][4]["sha256"], \
    "records body policy_evaluation_report_sha256 must equal manifest.subjects[4].sha256"
assert r["generated_at"] == gen_at, (r["generated_at"], gen_at)
# Template-preserved fields.
assert r["package_id"] == m["package_id"]
assert r["governed_reliance_demo_id"] == m["governed_reliance_demo_id"]
assert r["lifecycle_record_set_id"] == m["challenge_lifecycle_record_set_id"]
assert r["policy_evaluation_report_ref"] == m["policy_evaluation_report_id"]
# Five lifecycle records, in template input order.
assert isinstance(r["lifecycle_records"], list) and len(r["lifecycle_records"]) == 5
# Per-record runtime-injected lifecycle_fingerprint.
expected_lcids = ("lc-001", "lc-002", "lc-003", "lc-004", "lc-005")
expected_status = ("filed", "acknowledged", "resolved_locally", "withdrawn", "superseded")
for i, rec in enumerate(r["lifecycle_records"]):
    assert rec["lifecycle_id"] == expected_lcids[i], (i, rec["lifecycle_id"])
    assert rec["current_status"] == expected_status[i], (i, rec["current_status"])
    fp = rec.get("lifecycle_fingerprint")
    assert isinstance(fp, str) and bare_hex.match(fp), \
        f"record {i} lifecycle_fingerprint not bare hex: {fp!r}"
    # Closed event sequence: every record starts with event_status = filed.
    assert isinstance(rec["events"], list) and len(rec["events"]) >= 1
    assert rec["events"][0]["event_status"] == "filed", \
        f"record {i} first event must be filed, got {rec['events'][0]['event_status']!r}"
EOF

# ---------------------------------------------------------------------------
# Step 5 (PP5): inline structural check of derived lifecycle report (subject [6]).
# Confirms 5 rows in records-body input order, the 6-key coverage_summary
# rollup, sum equality, terminal+open equality, the expected canonical
# status_value_count distribution {filed:1, acknowledged:1, under_review:0,
# resolved_locally:1, superseded:1, withdrawn:1}, and the cross-anchors
# source_records_sha256 == subjects[5].sha256,
# source_policy_evaluation_report_sha256 == subjects[4].sha256,
# source_decision_report_sha256 == subjects[2].sha256.
# ---------------------------------------------------------------------------
echo "[step5] PP5 inline lifecycle report (5 rows + coverage) check"
python3 - "$PRISTINE/$LIFECYCLE_REPORT_REL_FILE" "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$RECORDS_REL_FILE" <<'EOF'
import json, sys, re
lp, mp, rp = sys.argv[1], sys.argv[2], sys.argv[3]
lr = json.loads(open(lp).read())
m  = json.loads(open(mp).read())
rb = json.loads(open(rp).read())
assert lr["document_type"] == "proofrail.gold.challenge_lifecycle_report", lr["document_type"]
assert lr["schema_version"] == "v0.1.0"
assert lr["profile"] == "gold.challenge_lifecycle_lite.v0.4.3"
assert lr["package_id"] == m["package_id"]
assert lr["governed_reliance_demo_id"] == m["governed_reliance_demo_id"]
assert lr["lifecycle_record_set_id"] == m["challenge_lifecycle_record_set_id"]
assert lr["challenge_lifecycle_report_id"] == m["challenge_lifecycle_report_id"]
assert lr["policy_evaluation_report_id"] == m["policy_evaluation_report_id"]
assert lr["generated_at"] == rb["generated_at"], \
    "lifecycle report generated_at must equal records body generated_at"
bare_hex = re.compile(r"^[0-9a-f]{64}$")
assert bare_hex.match(lr["source_records_sha256"])
assert bare_hex.match(lr["source_policy_evaluation_report_sha256"])
assert bare_hex.match(lr["source_decision_report_sha256"])
assert bare_hex.match(lr["report_fingerprint"])
assert lr["source_records_sha256"] == m["subjects"][5]["sha256"], \
    "lifecycle report source_records_sha256 must equal subjects[5].sha256"
assert lr["source_policy_evaluation_report_sha256"] == m["subjects"][4]["sha256"], \
    "lifecycle report source_policy_evaluation_report_sha256 must equal subjects[4].sha256"
assert lr["source_decision_report_sha256"] == m["subjects"][2]["sha256"], \
    "lifecycle report source_decision_report_sha256 must equal subjects[2].sha256"
# 5 rows expected against the canonical fixture pair (5 records).
assert isinstance(lr["lifecycle_rows"], list) and len(lr["lifecycle_rows"]) == 5
lc_row_re = re.compile(r"^lc_row_(0[1-9]|[1-9][0-9])$")
expected_status = ("filed", "acknowledged", "resolved_locally", "withdrawn", "superseded")
expected_terminal = (False, False, True, True, True)
expected_lcids = ("lc-001", "lc-002", "lc-003", "lc-004", "lc-005")
for i, row in enumerate(lr["lifecycle_rows"]):
    assert lc_row_re.match(row["row_id"]), (i, row["row_id"])
    assert row["row_id"] == f"lc_row_{i+1:02d}", (i, row["row_id"])
    assert row["lifecycle_id"] == expected_lcids[i], (i, row["lifecycle_id"])
    assert row["current_status"] == expected_status[i], (i, row["current_status"])
    assert row["is_terminal"] == expected_terminal[i], (i, row["is_terminal"])
    assert isinstance(row["event_count"], int) and row["event_count"] >= 1
    assert bare_hex.match(row["lifecycle_fingerprint"])
    # Row-level fingerprint must equal records-body record-level
    # fingerprint (R47 re-projection equivalence at file scope).
    assert row["lifecycle_fingerprint"] == rb["lifecycle_records"][i]["lifecycle_fingerprint"]
# coverage_summary keys and values.
cs = lr["coverage_summary"]
for field in ("lifecycle_record_count", "lifecycle_event_count",
              "open_lifecycle_count", "terminal_lifecycle_count",
              "status_value_count"):
    assert field in cs, field
assert cs["lifecycle_record_count"] == 5
assert cs["terminal_lifecycle_count"] == 3
assert cs["open_lifecycle_count"] == 2
assert cs["open_lifecycle_count"] + cs["terminal_lifecycle_count"] == cs["lifecycle_record_count"]
# Closed status_value_count key set.
svc = cs["status_value_count"]
assert set(svc.keys()) == {
  "filed", "acknowledged", "under_review",
  "resolved_locally", "superseded", "withdrawn",
}, f"status_value_count key set: {sorted(svc.keys())}"
expected_distribution = {
  "filed": 1, "acknowledged": 1, "under_review": 0,
  "resolved_locally": 1, "superseded": 1, "withdrawn": 1,
}
assert svc == expected_distribution, f"status_value_count distribution: {svc}"
assert sum(svc.values()) == cs["lifecycle_record_count"]
# lifecycle_event_count must equal sum of per-row event_count.
assert cs["lifecycle_event_count"] == sum(row["event_count"] for row in lr["lifecycle_rows"])
EOF

# ---------------------------------------------------------------------------
# Step 6 (PP6): inline identifier distinctness at the file level.
# Confirms the manifest's 6-ID collision class matches each subject body's
# cross-anchored ID, and that all six remain pairwise distinct.
# ---------------------------------------------------------------------------
echo "[step6] PP6 6-ID collision-class distinctness at file level"
python3 - "$PRISTINE/$MANIFEST_REL_FILE" "$PRISTINE/$CONFORMANCE_REL_FILE" \
  "$PRISTINE/$DECISION_REL_FILE" "$PRISTINE/$MATRIX_REL_FILE" "$PRISTINE/$EVAL_REL_FILE" \
  "$PRISTINE/$RECORDS_REL_FILE" "$PRISTINE/$LIFECYCLE_REPORT_REL_FILE" <<'EOF'
import json, sys
mp, cp, dp, xp, ep, rp, lp = sys.argv[1:8]
m  = json.loads(open(mp).read())
c  = json.loads(open(cp).read())
d  = json.loads(open(dp).read())
x  = json.loads(open(xp).read())
ev = json.loads(open(ep).read())
r  = json.loads(open(rp).read())
lr = json.loads(open(lp).read())
# Conformance report cross-anchors to top-level report_id (v0.4.0-shaped).
assert c["report_id"] == m["conformance_report_id"]
# Decision report cross-anchors to top-level decision_report_id (v0.4.1).
assert d["decision_report_id"] == m["decision_report_id"]
# Matrix cross-anchors to top-level matrix_id (v0.4.2).
assert x["matrix_id"] == m["matrix_id"]
# Evaluation report cross-anchors to top-level policy_evaluation_report_id (v0.4.2).
assert ev["policy_evaluation_report_id"] == m["policy_evaluation_report_id"]
# Records body cross-anchors to top-level lifecycle_record_set_id (v0.4.3).
assert r["lifecycle_record_set_id"] == m["challenge_lifecycle_record_set_id"]
# Lifecycle report cross-anchors to top-level challenge_lifecycle_report_id (v0.4.3).
assert lr["challenge_lifecycle_report_id"] == m["challenge_lifecycle_report_id"]
# 6-ID pairwise distinctness at the file level.
ids = [m["conformance_report_id"], m["decision_report_id"],
       m["matrix_id"], m["policy_evaluation_report_id"],
       m["challenge_lifecycle_record_set_id"],
       m["challenge_lifecycle_report_id"]]
assert len(set(ids)) == 6, f"6-ID collision-class violation at file level: {ids}"
EOF

# ===========================================================================
# Helpers (Phase 3).
# ===========================================================================

fresh_copy() {
  rm -rf "$2"
  cp -r "$1" "$2"
}

# v0.4.3 uses BARE lowercase hex SHA-256 in manifest subject sha256
# fields. Rehash subject [idx] (0..6) after a body mutation.
rehash_subject() {
  local pkg="$1" idx="$2"
  python3 - "$pkg" "$idx" <<'EOF'
import hashlib, json, os, sys
pkg, idx = sys.argv[1], int(sys.argv[2])
mp = os.path.join(pkg, "gold-challenge-lifecycle-package-manifest.json")
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

# Edit the v0.4.0-shaped package body subject [0] via a Python snippet
# operating on dict `pkg`. v0.4.0-shaped fixtures use indent=2 + trailing
# newline; preserve that.
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

# Edit the v0.4.3 manifest via a Python snippet operating on dict `m`.
# v0.4.3 manifest serialization: sort_keys + compact separators + trailing newline.
edit_manifest() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
mp = os.path.join(pkg, "gold-challenge-lifecycle-package-manifest.json")
m = json.loads(open(mp).read())
exec(expr, {"m": m, "json": json})
open(mp, "w").write(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the bundled v0.4.0 conformance report (subject [1]).
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

# Edit the bundled v0.4.1 decision report (subject [2]).
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

# Edit the runtime v0.4.2 policy evaluation matrix (subject [3]).
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

# Edit the v0.4.2 policy evaluation report (subject [4]).
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

# Edit the runtime v0.4.3 challenge lifecycle records body (subject [5]).
edit_records() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
rp = os.path.join(pkg, "challenge-lifecycle-records.json")
r = json.loads(open(rp).read())
exec(expr, {"r": r, "json": json})
open(rp, "w").write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
EOF
}

# Edit the v0.4.3 challenge lifecycle report (subject [6]).
edit_lifecycle_report() {
  local pkg="$1"
  shift
  python3 - "$pkg" "$@" <<'EOF'
import json, os, sys
pkg = sys.argv[1]
expr = sys.argv[2]
lp = os.path.join(pkg, "gold-challenge-lifecycle-report.json")
l = json.loads(open(lp).read())
exec(expr, {"l": l, "json": json})
open(lp, "w").write(json.dumps(l, sort_keys=True, separators=(",", ":")) + "\n")
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
  # co-located v0.4.2 verifier).
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

echo "[cases] 48 canonical + 4 runtime-scalar + 23 duplicate + 5 supplemental + 6 runner-only + rel01 + rel02 + env01 + sup_det + no-residue"

# ===========================================================================
# Canonical verifier mutation cases (48 = 38 inherited + 10 v0.4.3).
# Cases 01..24 mutate subject [0] (v0.4.0-shaped package body) and rely
# on the chained v0.4.3 -> v0.4.2 -> v0.4.1 -> v0.4.0 subprocess
# delegation to relay the inherited reason verbatim.
# Cases 25..29 mutate subject [2] (v0.4.1 decision report) and relay
# v0.4.1-introduced reasons.
# Cases 30..38 mutate subjects [3]/[4] (v0.4.2 matrix / evaluation
# report) and relay v0.4.2-introduced reasons.
# Cases 39..48 are v0.4.3-owned (R39..R48).
# ===========================================================================

# --- case01: gold_manifest_invalid (v0.4.3 manifest document_type) ----------
T="$WORK/c01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["document_type"] = "wrong"'
expect_verifier_fail "case01:gold_manifest_invalid" "$T" "gold_manifest_invalid"

# --- case02: gold_package_not_object (relayed) ------------------------------
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
# Mutating package_id/governed_reliance_demo_id would trip the v0.4.3
# manifest-side grammar check (R01) before reaching the v0.4.0 R05 path.
# Mutate relying_party.identity_id instead, which is package-body only and
# reaches R05 without crossing the manifest cross-anchor boundary.
T="$WORK/c05"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["relying_party"]["identity_id"] = "NotDotted Identity"'
rehash_subject "$T" 0
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
edit_package "$T" 'pkg["governed_decisions"][0]["decision_subject"]["subject_type"] = "not_a_type"'
rehash_subject "$T" 0
expect_verifier_fail "case13:decision_subject_binding_invalid" "$T" "decision_subject_binding_invalid"

# --- case14: decision_policy_binding_invalid (relayed) ----------------------
T="$WORK/c14"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["policy_binding"]["policy_pack_id"] = "wrong-policy-pack"'
rehash_subject "$T" 0
expect_verifier_fail "case14:decision_policy_binding_invalid" "$T" "decision_policy_binding_invalid"

# --- case15: decision_registry_binding_invalid (relayed) --------------------
T="$WORK/c15"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["registry_binding"]["decision_authority_role"] = "not_a_role"'
rehash_subject "$T" 0
expect_verifier_fail "case15:decision_registry_binding_invalid" "$T" "decision_registry_binding_invalid"

# --- case16: decision_action_scope_invalid (relayed) ------------------------
T="$WORK/c16"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["action_scope"]["action_category"] = "not_a_category"'
rehash_subject "$T" 0
expect_verifier_fail "case16:decision_action_scope_invalid" "$T" "decision_action_scope_invalid"

# --- case17: decision_status_invalid (relayed) ------------------------------
T="$WORK/c17"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 0
expect_verifier_fail "case17:decision_status_invalid" "$T" "decision_status_invalid"

# --- case18: acceptance_path_invalid (relayed) ------------------------------
T="$WORK/c18"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][0]["scenario_specific_state"].pop("acceptance_record_ref")'
rehash_subject "$T" 0
expect_verifier_fail "case18:acceptance_path_invalid" "$T" "acceptance_path_invalid"

# --- case19: rejection_path_invalid (relayed) -------------------------------
T="$WORK/c19"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][1]["scenario_specific_state"]["rejection_reason"] = "not_a_reason"'
rehash_subject "$T" 0
expect_verifier_fail "case19:rejection_path_invalid" "$T" "rejection_path_invalid"

# --- case20: challenge_path_invalid (relayed) -------------------------------
T="$WORK/c20"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][2]["scenario_specific_state"]["challenge_state"] = "not_a_state"'
rehash_subject "$T" 0
expect_verifier_fail "case20:challenge_path_invalid" "$T" "challenge_path_invalid"

# --- case21: withdrawal_path_invalid (relayed) ------------------------------
T="$WORK/c21"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][3]["scenario_specific_state"]["withdrawal_trigger"] = "not_a_trigger"'
rehash_subject "$T" 0
expect_verifier_fail "case21:withdrawal_path_invalid" "$T" "withdrawal_path_invalid"

# --- case22: supersession_path_invalid (relayed) ----------------------------
T="$WORK/c22"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["governed_decisions"][4]["scenario_specific_state"]["prior_decision_id"] = "decision-999-nonexistent"'
rehash_subject "$T" 0
expect_verifier_fail "case22:supersession_path_invalid" "$T" "supersession_path_invalid"

# --- case23: non_claims_missing (relayed) -----------------------------------
T="$WORK/c23"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["non_claims"] = []'
rehash_subject "$T" 0
expect_verifier_fail "case23:non_claims_missing" "$T" "non_claims_missing"

# --- case24: prohibited_gold_claim_present (relayed) ------------------------
T="$WORK/c24"; fresh_copy "$PRISTINE" "$T"
edit_package "$T" 'pkg["relying_party"]["display_name"] = "Gold Certified Authority"'
rehash_subject "$T" 0
expect_verifier_fail "case24:prohibited_gold_claim_present" "$T" "prohibited_gold_claim_present"

# --- case25: gold_decision_report_not_object (relayed v0.4.1) ---------------
T="$WORK/c25"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$DECISION_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 2
expect_verifier_fail "case25:gold_decision_report_not_object" "$T" "gold_decision_report_not_object"

# --- case26: gold_decision_report_schema_invalid (relayed v0.4.1) -----------
T="$WORK/c26"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["document_type"] = "wrong"'
rehash_subject "$T" 2
expect_verifier_fail "case26:gold_decision_report_schema_invalid" "$T" "gold_decision_report_schema_invalid"

# --- case27: gold_decision_report_binding_invalid (relayed v0.4.1) ----------
T="$WORK/c27"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 2
expect_verifier_fail "case27:gold_decision_report_binding_invalid" "$T" "gold_decision_report_binding_invalid"

# --- case28: gold_decision_report_projection_invalid (relayed v0.4.1) -------
T="$WORK/c28"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["decision_rows"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 2
expect_verifier_fail "case28:gold_decision_report_projection_invalid" "$T" "gold_decision_report_projection_invalid"

# --- case29: gold_decision_report_summary_invalid (relayed v0.4.1) ----------
T="$WORK/c29"; fresh_copy "$PRISTINE" "$T"
edit_decision "$T" 'd["coverage_summary"]["decision_count"] = 42'
rehash_subject "$T" 2
expect_verifier_fail "case29:gold_decision_report_summary_invalid" "$T" "gold_decision_report_summary_invalid"

# --- case30: gold_policy_matrix_not_object (relayed v0.4.2) -----------------
T="$WORK/c30"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$MATRIX_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 3
expect_verifier_fail "case30:gold_policy_matrix_not_object" "$T" "gold_policy_matrix_not_object"

# --- case31: gold_policy_matrix_schema_invalid (relayed v0.4.2) -------------
T="$WORK/c31"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["document_type"] = "wrong"'
rehash_subject "$T" 3
expect_verifier_fail "case31:gold_policy_matrix_schema_invalid" "$T" "gold_policy_matrix_schema_invalid"

# --- case32: gold_policy_matrix_binding_invalid (relayed v0.4.2) ------------
T="$WORK/c32"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 3
expect_verifier_fail "case32:gold_policy_matrix_binding_invalid" "$T" "gold_policy_matrix_binding_invalid"

# --- case33: gold_policy_matrix_entry_invalid (relayed v0.4.2) --------------
T="$WORK/c33"; fresh_copy "$PRISTINE" "$T"
edit_matrix "$T" 'x["matrix_rows"][0]["matrix_row_id"] = "mrow_05"'
rehash_subject "$T" 3
expect_verifier_fail "case33:gold_policy_matrix_entry_invalid" "$T" "gold_policy_matrix_entry_invalid"

# --- case34: gold_policy_evaluation_report_not_object (relayed v0.4.2) ------
T="$WORK/c34"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$EVAL_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 4
expect_verifier_fail "case34:gold_policy_evaluation_report_not_object" "$T" "gold_policy_evaluation_report_not_object"

# --- case35: gold_policy_evaluation_report_schema_invalid (relayed v0.4.2) --
T="$WORK/c35"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["document_type"] = "wrong"'
rehash_subject "$T" 4
expect_verifier_fail "case35:gold_policy_evaluation_report_schema_invalid" "$T" "gold_policy_evaluation_report_schema_invalid"

# --- case36: gold_policy_evaluation_report_binding_invalid (relayed v0.4.2) -
T="$WORK/c36"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 4
expect_verifier_fail "case36:gold_policy_evaluation_report_binding_invalid" "$T" "gold_policy_evaluation_report_binding_invalid"

# --- case37: gold_policy_evaluation_result_invalid (relayed v0.4.2) ---------
T="$WORK/c37"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["evaluation_rows"][0]["decision_status"] = "rejected"'
rehash_subject "$T" 4
expect_verifier_fail "case37:gold_policy_evaluation_result_invalid" "$T" "gold_policy_evaluation_result_invalid"

# --- case38: gold_policy_evaluation_summary_invalid (relayed v0.4.2) --------
T="$WORK/c38"; fresh_copy "$PRISTINE" "$T"
edit_evaluation "$T" 'e["coverage_summary"]["matched_count"] = 42'
rehash_subject "$T" 4
expect_verifier_fail "case38:gold_policy_evaluation_summary_invalid" "$T" "gold_policy_evaluation_summary_invalid"

# --- case39: gold_challenge_lifecycle_records_not_object (R39) --------------
# Replace subject [5] with a top-level JSON array; verifier R39 fires
# before any R40 schema check.
T="$WORK/c39"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$RECORDS_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 5
expect_verifier_fail "case39:gold_challenge_lifecycle_records_not_object" "$T" "gold_challenge_lifecycle_records_not_object"

# --- case40: gold_challenge_lifecycle_records_schema_invalid (R40) ----------
# Mutate document_type so R40 schema fires before R41 binding.
T="$WORK/c40"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'r["document_type"] = "wrong"'
rehash_subject "$T" 5
expect_verifier_fail "case40:gold_challenge_lifecycle_records_schema_invalid" "$T" "gold_challenge_lifecycle_records_schema_invalid"

# --- case41: gold_challenge_lifecycle_records_binding_invalid (R41) ---------
# Mutate records body's package_id so it disagrees with manifest;
# schema-shape remains valid.
T="$WORK/c41"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'r["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 5
expect_verifier_fail "case41:gold_challenge_lifecycle_records_binding_invalid" "$T" "gold_challenge_lifecycle_records_binding_invalid"

# --- case42: gold_challenge_lifecycle_event_invalid (R42) -------------------
# Mutate one event's event_basis so the (status, basis) pair is not in
# the closed table. (R40 schema doesn't enforce pair-table; only R42.)
T="$WORK/c42"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'r["lifecycle_records"][0]["events"][0]["event_basis"] = "acknowledgement_record"'
rehash_subject "$T" 5
expect_verifier_fail "case42:gold_challenge_lifecycle_event_invalid" "$T" "gold_challenge_lifecycle_event_invalid"

# --- case43: gold_challenge_lifecycle_transition_invalid (R43) --------------
# Mutate lc-002's events: change first event's event_status from
# "filed" to "acknowledged" (still in closed set, status/basis pair
# adjusted to (acknowledged, acknowledgement_record) so R42 passes,
# then drop the lifecycle_effect that was on the original filed
# event). This trips R43 ("first event must be filed").
T="$WORK/c43"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" '
r["lifecycle_records"][0]["events"][0]["event_status"] = "acknowledged"
r["lifecycle_records"][0]["events"][0]["event_basis"] = "acknowledgement_record"
r["lifecycle_records"][0]["events"][0].pop("lifecycle_effect", None)
'
rehash_subject "$T" 5
expect_verifier_fail "case43:gold_challenge_lifecycle_transition_invalid" "$T" "gold_challenge_lifecycle_transition_invalid"

# --- case44: gold_challenge_lifecycle_report_not_object (R44) ---------------
# Replace subject [6] with a top-level JSON array.
T="$WORK/c44"; fresh_copy "$PRISTINE" "$T"
python3 -c "
import json
with open('$T/$LIFECYCLE_REPORT_REL_FILE', 'w') as f:
    f.write(json.dumps([1,2,3], sort_keys=True, separators=(',', ':')) + '\n')
"
rehash_subject "$T" 6
expect_verifier_fail "case44:gold_challenge_lifecycle_report_not_object" "$T" "gold_challenge_lifecycle_report_not_object"

# --- case45: gold_challenge_lifecycle_report_schema_invalid (R45) -----------
# Mutate document_type so R45 schema fires before R46 binding.
T="$WORK/c45"; fresh_copy "$PRISTINE" "$T"
edit_lifecycle_report "$T" 'l["document_type"] = "wrong"'
rehash_subject "$T" 6
expect_verifier_fail "case45:gold_challenge_lifecycle_report_schema_invalid" "$T" "gold_challenge_lifecycle_report_schema_invalid"

# --- case46: gold_challenge_lifecycle_report_binding_invalid (R46) ----------
# Mutate report's package_id so it disagrees with manifest;
# schema-shape remains valid.
T="$WORK/c46"; fresh_copy "$PRISTINE" "$T"
edit_lifecycle_report "$T" 'l["package_id"] = "proofrail-gold-governed-reliance-binding-mismatch-001"'
rehash_subject "$T" 6
expect_verifier_fail "case46:gold_challenge_lifecycle_report_binding_invalid" "$T" "gold_challenge_lifecycle_report_binding_invalid"

# --- case47: gold_challenge_lifecycle_projection_invalid (R47) --------------
# Mutate lifecycle_rows[0].current_status to a different closed-set
# value (so R45 schema still passes) while leaving the records body
# unchanged. The re-projected canonical bytes will mismatch the
# published row.
T="$WORK/c47"; fresh_copy "$PRISTINE" "$T"
edit_lifecycle_report "$T" 'l["lifecycle_rows"][0]["current_status"] = "acknowledged"'
rehash_subject "$T" 6
expect_verifier_fail "case47:gold_challenge_lifecycle_projection_invalid" "$T" "gold_challenge_lifecycle_projection_invalid"

# --- case48: gold_challenge_lifecycle_summary_invalid (R48) -----------------
# Bump coverage_summary.lifecycle_event_count from 12 to 42. R45 schema
# checks only that the field is a non-negative integer; R48 derivation
# over actual_rows recomputes the sum (12) and disagrees.
T="$WORK/c48"; fresh_copy "$PRISTINE" "$T"
edit_lifecycle_report "$T" 'l["coverage_summary"]["lifecycle_event_count"] = 42'
rehash_subject "$T" 6
expect_verifier_fail "case48:gold_challenge_lifecycle_summary_invalid" "$T" "gold_challenge_lifecycle_summary_invalid"

# ===========================================================================
# Runtime-scalar canonical cases (4; runner-injected scalars at subject [5]).
# ===========================================================================

# --- rt1: drop records.policy_evaluation_report_sha256 -> R40 ---------------
T="$WORK/rt1"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'del r["policy_evaluation_report_sha256"]'
rehash_subject "$T" 5
expect_verifier_fail "rt1:records_policy_evaluation_report_sha256_drop" "$T" "gold_challenge_lifecycle_records_schema_invalid"

# --- rt1b: drop records.generated_at -> R40 ---------------------------------
T="$WORK/rt1b"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'del r["generated_at"]'
rehash_subject "$T" 5
expect_verifier_fail "rt1b:records_generated_at_drop" "$T" "gold_challenge_lifecycle_records_schema_invalid"

# --- rt2: records.policy_evaluation_report_sha256 valid-hex wrong -> R41 ----
T="$WORK/rt2"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'r["policy_evaluation_report_sha256"] = "f" * 64'
rehash_subject "$T" 5
expect_verifier_fail "rt2:records_policy_evaluation_report_sha256_anchor_mismatch" "$T" "gold_challenge_lifecycle_records_binding_invalid"

# --- rt3: drop one lifecycle_records[i].lifecycle_fingerprint -> R40 --------
T="$WORK/rt3"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" 'del r["lifecycle_records"][0]["lifecycle_fingerprint"]'
rehash_subject "$T" 5
expect_verifier_fail "rt3:records_lifecycle_fingerprint_drop" "$T" "gold_challenge_lifecycle_records_schema_invalid"

# ===========================================================================
# Duplicate gold_manifest_invalid cases (23; all route to that reason).
# ===========================================================================

# --- dup01..dup07: subject[0..6] path absolute ------------------------------
T="$WORK/d01"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "/etc/passwd"'
expect_verifier_fail "dup01:subject_0_path_absolute" "$T" "gold_manifest_invalid"

T="$WORK/d02"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][1]["path"] = "/etc/hostname"'
expect_verifier_fail "dup02:subject_1_path_absolute" "$T" "gold_manifest_invalid"

T="$WORK/d03"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][2]["path"] = "/etc/shells"'
expect_verifier_fail "dup03:subject_2_path_absolute" "$T" "gold_manifest_invalid"

T="$WORK/d04"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][3]["path"] = "/etc/services"'
expect_verifier_fail "dup04:subject_3_path_absolute" "$T" "gold_manifest_invalid"

T="$WORK/d05"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][4]["path"] = "/etc/protocols"'
expect_verifier_fail "dup05:subject_4_path_absolute" "$T" "gold_manifest_invalid"

T="$WORK/d06"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][5]["path"] = "/etc/networks"'
expect_verifier_fail "dup06:subject_5_path_absolute_records" "$T" "gold_manifest_invalid"

T="$WORK/d07"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][6]["path"] = "/etc/group"'
expect_verifier_fail "dup07:subject_6_path_absolute_report" "$T" "gold_manifest_invalid"

# --- dup08, dup09, dup10: subject path traversal ----------------------------
T="$WORK/d08"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][0]["path"] = "../escape-pkg.json"'
expect_verifier_fail "dup08:subject_0_path_traversal" "$T" "gold_manifest_invalid"

T="$WORK/d09"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][5]["path"] = "../escape-records.json"'
expect_verifier_fail "dup09:subject_5_path_traversal_records" "$T" "gold_manifest_invalid"

T="$WORK/d10"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][6]["path"] = "../escape-report.json"'
expect_verifier_fail "dup10:subject_6_path_traversal_report" "$T" "gold_manifest_invalid"

# --- dup11, dup12: file missing on disk -------------------------------------
T="$WORK/d11"; fresh_copy "$PRISTINE" "$T"
rm "$T/$RECORDS_REL_FILE"
expect_verifier_fail "dup11:subject_5_file_absent_records" "$T" "gold_manifest_invalid"

T="$WORK/d12"; fresh_copy "$PRISTINE" "$T"
rm "$T/$LIFECYCLE_REPORT_REL_FILE"
expect_verifier_fail "dup12:subject_6_file_absent_report" "$T" "gold_manifest_invalid"

# --- dup13, dup14: size_bytes mismatch (records and report) -----------------
T="$WORK/d13"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][5]["size_bytes"] = 0'
expect_verifier_fail "dup13:subject_5_size_mismatch_records" "$T" "gold_manifest_invalid"

T="$WORK/d14"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][6]["size_bytes"] = 0'
expect_verifier_fail "dup14:subject_6_size_mismatch_report" "$T" "gold_manifest_invalid"

# --- dup15, dup16: sha256 mismatch (records and report, bare hex) -----------
T="$WORK/d15"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][5]["sha256"] = "f" * 64'
expect_verifier_fail "dup15:subject_5_sha_mismatch_records" "$T" "gold_manifest_invalid"

T="$WORK/d16"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][6]["sha256"] = "0" * 64'
expect_verifier_fail "dup16:subject_6_sha_mismatch_report" "$T" "gold_manifest_invalid"

# --- dup17, dup18: wrong subject count --------------------------------------
T="$WORK/d17"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"] = m["subjects"][:6]'
expect_verifier_fail "dup17:wrong_subject_count_six" "$T" "gold_manifest_invalid"

T="$WORK/d18"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"].append({"role":"extra","path":"x","sha256":"0"*64,"size_bytes":0})'
expect_verifier_fail "dup18:wrong_subject_count_eight" "$T" "gold_manifest_invalid"

# --- dup19, dup20: role wrong (records and report) --------------------------
T="$WORK/d19"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][5]["role"] = "wrong_role"'
expect_verifier_fail "dup19:subject_5_role_wrong" "$T" "gold_manifest_invalid"

T="$WORK/d20"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["subjects"][6]["role"] = "wrong_role"'
expect_verifier_fail "dup20:subject_6_role_wrong" "$T" "gold_manifest_invalid"

# --- dup21, dup22, dup23: 6-ID collision class violations -------------------
# All three folds happen at R01 (manifest Phase 1 pairwise distinctness).
T="$WORK/d21"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["challenge_lifecycle_record_set_id"] = m["conformance_report_id"]'
expect_verifier_fail "dup21:challenge_lifecycle_record_set_id_conformance_collision" "$T" "gold_manifest_invalid"

T="$WORK/d22"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["challenge_lifecycle_report_id"] = m["policy_evaluation_report_id"]'
expect_verifier_fail "dup22:challenge_lifecycle_report_id_policy_eval_report_collision" "$T" "gold_manifest_invalid"

T="$WORK/d23"; fresh_copy "$PRISTINE" "$T"
edit_manifest "$T" 'm["challenge_lifecycle_report_id"] = m["challenge_lifecycle_record_set_id"]'
expect_verifier_fail "dup23:challenge_lifecycle_report_id_record_set_id_collision" "$T" "gold_manifest_invalid"

# ===========================================================================
# Supplemental records-body / lifecycle-report binding cases (5 total).
#   Authoritative Phase 3 supplemental mapping (user-attested):
#     sup01 -> R42: `withdrawn` current_status without
#                  `withdrawal_record_ref`.
#     sup02 -> R43: first event is not `filed`.
#                  Distinct mutation from canonical case43 (different
#                  target record and a different non-`filed` status).
#     sup03 -> R43: event occurs after a terminal event.
#     sup04 -> R43: `current_status` disagrees with the final event.
#     sup05 -> R46: `challenge_lifecycle_report_id` collides with
#                  `policy_evaluation_report_id` at the lifecycle
#                  report body level. Manifest unchanged; subject[6]
#                  sha256 recomputed so the body integrity check is
#                  reached and R46 fires on the body-level collision.
#
# Per Phase 3 supplemental allocation: R42x1, R43x3, R46x1.
# ===========================================================================

# --- sup01: R42 withdrawn without withdrawal_record_ref ---------------------
# lc-004 has current_status=`withdrawn` with `withdrawal_record_ref`
# present in the fixture template. Delete that ref. R40 schema passes
# (the field is conditional, not required-always). R41 binding passes
# (record-level binding to package/manifest unaffected). R42 fires at
# the record-level current_status check inside the R42 block.
T="$WORK/s01"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" '
del r["lifecycle_records"][3]["withdrawal_record_ref"]
'
rehash_subject "$T" 5
expect_verifier_fail "sup01:event_invalid_withdrawn_without_withdrawal_record_ref" "$T" "gold_challenge_lifecycle_event_invalid"

# --- sup02: R43 first event is not `filed` (distinct from case43) ----------
# Canonical case43 mutates lc-001 events[0] to `acknowledged`. This
# supplemental mutates lc-003 events[0] to `under_review` to broaden
# reachability evidence for the same approved cause. Pair table for
# (under_review, review_update) is valid without lifecycle_effect, so
# R42 still passes; R43 fires on "first event must be `filed`".
T="$WORK/s02"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" '
r["lifecycle_records"][2]["events"][0]["event_status"] = "under_review"
r["lifecycle_records"][2]["events"][0]["event_basis"] = "review_update"
r["lifecycle_records"][2]["events"][0]["event_basis_ref"] = "review-update-lc-003-sup02-001"
if "lifecycle_effect" in r["lifecycle_records"][2]["events"][0]:
    del r["lifecycle_records"][2]["events"][0]["lifecycle_effect"]
'
rehash_subject "$T" 5
expect_verifier_fail "sup02:transition_first_event_not_filed" "$T" "gold_challenge_lifecycle_transition_invalid"

# --- sup03: R43 event occurs after a terminal event ------------------------
# lc-004 is [filed, acknowledged, withdrawn]; append a well-formed
# event after the terminal withdrawn. Pair table: (filed,
# challenge_record) carries lifecycle_effect=challenge_open. R42
# passes (the appended event is per-event valid); R43 fires because
# no event may follow a terminal event.
T="$WORK/s03"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" '
last = r["lifecycle_records"][3]["events"][-1]
tail_id = "lc-004-ev-099"
appended = {
    "event_id": tail_id,
    "event_status": "filed",
    "event_basis": "challenge_record",
    "actor_role": "system_recorder",
    "event_timestamp": last["event_timestamp"],
    "event_basis_ref": "challenge-record-lc-004-tail-001",
    "lifecycle_effect": "challenge_open",
}
r["lifecycle_records"][3]["events"].append(appended)
'
rehash_subject "$T" 5
expect_verifier_fail "sup03:transition_event_after_terminal" "$T" "gold_challenge_lifecycle_transition_invalid"

# --- sup04: R43 current_status disagrees with final event status ------------
# Mutate record-level current_status away from its final event_status
# but keep it inside the closed status set.
T="$WORK/s04"; fresh_copy "$PRISTINE" "$T"
edit_records "$T" '
# lc-001 final event_status == "filed"; set current_status to
# "acknowledged" (also closed) so R42 still passes but R43
# current-vs-final mismatch fires.
r["lifecycle_records"][0]["current_status"] = "acknowledged"
'
rehash_subject "$T" 5
expect_verifier_fail "sup04:transition_current_status_vs_final_event" "$T" "gold_challenge_lifecycle_transition_invalid"

# --- sup05: R46 challenge_lifecycle_report_id body-level collision ---------
# In the lifecycle report body (subject [6]) only, set
# `challenge_lifecycle_report_id` equal to `policy_evaluation_report_id`.
# The manifest is unchanged (both manifest-side IDs remain distinct),
# but the manifest's subjects[6].sha256 MUST be recomputed so the
# lifecycle-report body integrity check (R44/R45) is reached. R44
# (not-object) passes (body is still an object). R45 (schema) passes
# (the colliding value is still a valid closed-grammar string). R46
# fires on the body-vs-manifest mismatch of
# `challenge_lifecycle_report_id`. R01 (manifest 6-ID collision class)
# does NOT fire because the manifest itself is unmutated.
T="$WORK/s05"; fresh_copy "$PRISTINE" "$T"
edit_lifecycle_report "$T" 'l["challenge_lifecycle_report_id"] = l["policy_evaluation_report_id"]'
rehash_subject "$T" 6
expect_verifier_fail "sup05:report_challenge_lifecycle_report_id_collides_with_policy_eval_report_id" "$T" "gold_challenge_lifecycle_report_binding_invalid"

# ===========================================================================
# Runner-only refusal cases (6 exercises, 5 distinct reasons). The
# runner's _preflight_input_path() runs first against --input-package;
# all six exercises target --input-package so the refusal fires before
# --matrix-input or --lifecycle-input is inspected.
# ===========================================================================

# --- ro1: runner_input_path_missing -----------------------------------------
RO1_OUT="$WORK/ro1-out"
expect_runner_fail "ro1:runner_input_path_missing" \
  "runner_input_path_missing" \
  "$RO1_OUT" \
  "$RUNNER" \
    --matrix-input "$MATRIX_FIX_REL" \
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
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
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
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
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
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
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
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
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
    --generated-at "$GEN_AT" \
    --output-dir "$RO4_OUT" \
    --force

# --- ro5: runner_input_json_invalid -----------------------------------------
# The runner's path preflight requires a relative non-traversal path.
# Tempdirs under /var/folders/.. resolve to a relative path that begins
# with `..`, which is intercepted by runner_input_path_forbidden BEFORE
# the JSON-invalid check. We must therefore write the bad-JSON input
# inside the repo. We write it to the v0.4.3/test-owned scratch path
# ($TMP_TEST_SCRATCH_REL), which is NOT a v0.4.3-owned source path
# and is NOT under any inherited-tier fixture or tool directory. The
# bad-input file is removed after the exercise even on failure; the
# scratch dir is removed by the EXIT trap.
RO5_OUT="$WORK/ro5-out"
BAD_INPUT_REL="$TMP_TEST_SCRATCH_REL/ro5_bad_input.json"
BAD_INPUT_ABS="$REPO_ROOT/$BAD_INPUT_REL"
printf 'this is not json\n' > "$BAD_INPUT_ABS"
set +e
expect_runner_fail "ro5:runner_input_json_invalid" \
  "runner_input_json_invalid" \
  "$RO5_OUT" \
  "$RUNNER" \
    --input-package "$BAD_INPUT_REL" \
    --matrix-input "$MATRIX_FIX_REL" \
    --lifecycle-input "$LIFECYCLE_FIX_REL" \
    --manifest-id "$MANIFEST_ID" \
    --conformance-report-id "$CONFORMANCE_REPORT_ID" \
    --decision-report-id "$DECISION_REPORT_ID" \
    --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
    --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
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
# rel01 (runner-relay-of-verifier). The runner relays the v0.4.3
# verifier's reason UNCHANGED; it does NOT wrap it in a sixth
# runner-only code. Staging directory must be cleaned up and
# destination must not exist.
# ===========================================================================

REL_OUT="$WORK/rel01-out"
# The runner's path preflight rejects absolute paths and traversal
# segments, so the bad-input package must live inside the repo. We
# write it to the v0.4.3/test-owned scratch path ($TMP_TEST_SCRATCH_REL),
# which is NOT a v0.4.3-owned source path and is NOT under any
# inherited-tier fixture or tool directory. The file is removed
# explicitly below after the exercise; the scratch dir itself is
# removed by the EXIT trap.
REL_INPUT_REL="$TMP_TEST_SCRATCH_REL/rel01_bad_input.json"
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
  --lifecycle-input "$LIFECYCLE_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
  --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$REL_OUT" \
  --force \
  --self-validate 2>&1)"
rel_rc=$?
set -e

if [ "$rel_rc" -eq 0 ]; then
  echo "FAIL: rel01: expected nonzero exit (verifier relay), got 0"
  echo "$rel_out"
  exit 1
fi
# The relayed reason must be the inherited v0.4.0-shaped structural reason
# (relayed through v0.4.1 -> v0.4.2 -> v0.4.3 -> the runner).
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
rm -f "$REL_INPUT_ABS"
echo "  rel01:runner_relay_of_verifier_failure: ok (inherited verifier reason relayed unchanged)"

# ===========================================================================
# rel02 (verifier-relay-of-inherited). Mutate the v0.4.0-shaped package
# body subject [0] to trigger an inherited non-R01 reason; the v0.4.3
# verifier's chained subprocess delegation (v0.4.3 -> v0.4.2 -> v0.4.1
# -> v0.4.0) must relay the reason verbatim with no v0.4.3 wrapping,
# no INFRA: diagnostic, and no R-code substitution.
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
if ! echo "$rel2_out" | grep -qE "^FAIL: gold_package_schema_invalid:"; then
  echo "FAIL: rel02: expected inherited reason gold_package_schema_invalid"
  echo "----- v0.4.3 verifier output -----"
  echo "$rel2_out"
  echo "----------------------------------"
  exit 1
fi
# Must NOT be wrapped in any v0.4.3-introduced reason.
for v043_only in gold_challenge_lifecycle_records_not_object \
                 gold_challenge_lifecycle_records_schema_invalid \
                 gold_challenge_lifecycle_records_binding_invalid \
                 gold_challenge_lifecycle_event_invalid \
                 gold_challenge_lifecycle_transition_invalid \
                 gold_challenge_lifecycle_report_not_object \
                 gold_challenge_lifecycle_report_schema_invalid \
                 gold_challenge_lifecycle_report_binding_invalid \
                 gold_challenge_lifecycle_projection_invalid \
                 gold_challenge_lifecycle_summary_invalid; do
  if echo "$rel2_out" | grep -qE "^FAIL: ${v043_only}:"; then
    echo "FAIL: rel02: v0.4.3 verifier wrapped inherited reason in $v043_only"
    echo "$rel2_out"
    exit 1
  fi
done
if echo "$rel2_out" | grep -q "^INFRA:"; then
  echo "FAIL: rel02: v0.4.3 verifier emitted INFRA: on a real package defect"
  echo "$rel2_out"
  exit 1
fi
echo "  rel02:verifier_relay_of_inherited_failure: ok (gold_package_schema_invalid relayed unchanged)"

# ===========================================================================
# env01 (environment-failure). Non-destructive verifier-trap: copy the
# v0.4.3 verifier into an isolated tempdir WITHOUT copying its
# co-located v0.4.2 sibling. The copied v0.4.3 verifier resolves
# GOLD_V042_VERIFIER relative to its own __file__ and finds nothing,
# so it emits `INFRA: co-located v0.4.2 verifier unavailable...` on
# stderr and exits 3. The real on-disk co-located verifiers are NEVER
# touched, so SS snapshot equality is preserved.
# ===========================================================================

ENV01_DIR="$WORK/env01_isolated_tools"
mkdir -p "$ENV01_DIR"
cp "$VERIFIER" "$ENV01_DIR/verify_gold_challenge_lifecycle_lite_v0_1_0.py"
ENV01_VERIFIER="$ENV01_DIR/verify_gold_challenge_lifecycle_lite_v0_1_0.py"

set +e
env_out="$(python3 "$ENV01_VERIFIER" --manifest "$PRISTINE/$MANIFEST_REL_FILE" 2>&1)"
env_rc=$?
set -e

if [ "$env_rc" -ne 3 ]; then
  echo "FAIL: env01: expected exit 3 (INFRA), got $env_rc"
  echo "$env_out"
  exit 1
fi
if ! echo "$env_out" | grep -qE "^INFRA: co-located v0\.4\.2 verifier unavailable"; then
  echo "FAIL: env01: expected INFRA: co-located v0.4.2 verifier unavailable diagnostic"
  echo "----- v0.4.3 verifier output -----"
  echo "$env_out"
  echo "----------------------------------"
  exit 1
fi
# Must NOT collapse into any of the 48 verifier reasons.
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
         gold_policy_evaluation_summary_invalid \
         gold_challenge_lifecycle_records_not_object \
         gold_challenge_lifecycle_records_schema_invalid \
         gold_challenge_lifecycle_records_binding_invalid \
         gold_challenge_lifecycle_event_invalid \
         gold_challenge_lifecycle_transition_invalid \
         gold_challenge_lifecycle_report_not_object \
         gold_challenge_lifecycle_report_schema_invalid \
         gold_challenge_lifecycle_report_binding_invalid \
         gold_challenge_lifecycle_projection_invalid \
         gold_challenge_lifecycle_summary_invalid; do
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
echo "  env01:environment_failure_v042_verifier_unavailable: ok (INFRA: emitted, exit 3)"

# ===========================================================================
# sup_det (positive determinism). Rebuild the package and confirm
# records body subject sha, lifecycle report subject sha, every
# per-record lifecycle_fingerprint, and report_fingerprint are
# byte-identical across the two builds.
# ===========================================================================

REBUILT="$WORK/rebuilt"
python3 "$RUNNER" \
  --input-package "$PACKAGE_FIX_REL" \
  --matrix-input "$MATRIX_FIX_REL" \
  --lifecycle-input "$LIFECYCLE_FIX_REL" \
  --manifest-id "$MANIFEST_ID" \
  --conformance-report-id "$CONFORMANCE_REPORT_ID" \
  --decision-report-id "$DECISION_REPORT_ID" \
  --policy-evaluation-report-id "$POLICY_EVAL_REPORT_ID" \
  --challenge-lifecycle-report-id "$CHALLENGE_LIFECYCLE_REPORT_ID" \
  --generated-at "$GEN_AT" \
  --output-dir "$REBUILT" \
  --force \
  --self-validate >/dev/null

python3 - "$PRISTINE/$MANIFEST_REL_FILE" "$REBUILT/$MANIFEST_REL_FILE" \
              "$PRISTINE/$RECORDS_REL_FILE" "$REBUILT/$RECORDS_REL_FILE" \
              "$PRISTINE/$LIFECYCLE_REPORT_REL_FILE" "$REBUILT/$LIFECYCLE_REPORT_REL_FILE" <<'EOF'
import json, sys
m1 = json.loads(open(sys.argv[1]).read())
m2 = json.loads(open(sys.argv[2]).read())
assert m1["subjects"][5]["sha256"] == m2["subjects"][5]["sha256"], \
    "records body subject sha drifted across rebuild"
assert m1["subjects"][6]["sha256"] == m2["subjects"][6]["sha256"], \
    "lifecycle report subject sha drifted across rebuild"
r1 = json.loads(open(sys.argv[3]).read())
r2 = json.loads(open(sys.argv[4]).read())
assert len(r1["lifecycle_records"]) == len(r2["lifecycle_records"]) == 5
for i in range(5):
    assert r1["lifecycle_records"][i]["lifecycle_fingerprint"] == \
           r2["lifecycle_records"][i]["lifecycle_fingerprint"], \
        f"lifecycle_records[{i}].lifecycle_fingerprint drifted across rebuild"
l1 = json.loads(open(sys.argv[5]).read())
l2 = json.loads(open(sys.argv[6]).read())
assert l1["report_fingerprint"] == l2["report_fingerprint"], \
    "lifecycle report report_fingerprint drifted across rebuild"
EOF
echo "  sup_det:positive_determinism_records_and_report: ok"

# ===========================================================================
# Taxonomy gate (TG1).
# ===========================================================================
echo "[gate] TG1 taxonomy gate over v0.4.3-owned files"
python3 - "$REPO_ROOT" <<'PYEOF'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])

# 48 approved verifier reasons (38 inherited from v0.4.0/v0.4.1/v0.4.2
# + 10 v0.4.3).
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
    # inherited from v0.4.2:
    "gold_policy_matrix_not_object",
    "gold_policy_matrix_schema_invalid",
    "gold_policy_matrix_binding_invalid",
    "gold_policy_matrix_entry_invalid",
    "gold_policy_evaluation_report_not_object",
    "gold_policy_evaluation_report_schema_invalid",
    "gold_policy_evaluation_report_binding_invalid",
    "gold_policy_evaluation_result_invalid",
    "gold_policy_evaluation_summary_invalid",
    # introduced by v0.4.3:
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
}
APPROVED_RUNNER = {
    "runner_input_path_missing",
    "runner_input_path_forbidden",
    "runner_input_file_missing",
    "runner_input_read_failed",
    "runner_input_json_invalid",
}

# TG1 ALLOWLIST DISCIPLINE (v0.4.3)
# ---------------------------------
# Per Phase 0 amendment lock: the v0.4.3 data-field allowlist target was
# EMPTY for v0.4.3-OWNED data fields. None of the v0.4.3 coverage-summary
# keys or records-body / report field names end in _present / _missing /
# _invalid / _failed / _forbidden / _unsupported / _not_object, so no
# v0.4.3-INTRODUCED data-field name trips REASON_FILTER.
#
# However, the v0.4.3 runner internally derives a v0.4.1 decision report
# (it inherits the v0.4.1 decision-report hardening surface verbatim,
# via subprocess delegation to v0.4.2 which itself delegates to v0.4.1),
# so the v0.4.1 decision-report schema's `coverage_summary` enum-presence
# data-field names appear inside the v0.4.3 build tool indirectly when
# inherited fixtures are quoted. Those names are inherited verbatim from
# v0.4.1 and were already allowlisted under the v0.4.1 and v0.4.2 TG1
# with identical justification. They are LITERAL JSON FIELD NAMES under
# coverage_summary, not public reasons.
#
# Adding any further entry requires (a) the token is a verbatim data-field
# name already present in the v0.4.1, v0.4.2, or v0.4.3 schema, (b) a
# comment pointing at the schema clause that defines it, and (c)
# checkpoint-justified amendment per Phase 3 constraint #1.
ALLOWED_NON_REASON_TOKENS: set[str] = {
    # v0.4.1 decision-report coverage_summary enum-presence field names
    # (schemas/gold-governed-reliance-decision-report-v0.1.0.md,
    # `coverage_summary` clause). The v0.4.3 runner inherits the v0.4.1
    # decision report by chained subprocess delegation; these literal
    # field names appear in the inherited surface. They terminate in
    # `_present`, so REASON_FILTER admits them, but they are inherited
    # v0.4.1 data-field names, NOT public reasons.
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
# Per the v0.4.1/v0.4.2 deny-list pattern, extended to include v043_verifier.
# Substrings are spelled with explicit string concatenation so that the
# gate's own source does NOT contain a whole reason-shaped deny token
# (otherwise the deny-list literal would self-trip the gate when it
# scans this test file). The constituent halves never satisfy the
# REASON_FILTER suffix on their own.
DENY_SUBSTRINGS = (
    "v040" + "_verifier",
    "v041" + "_verifier",
    "v042" + "_verifier",
    "v043" + "_verifier",
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

V0_4_3_FILES = [
    "schemas/gold-challenge-lifecycle-records-v0.1.0.md",
    "schemas/gold-challenge-lifecycle-report-v0.1.0.md",
    "schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md",
    "fixtures/gold-challenge-lifecycle-lite-v0.4.3/README.md",
    "fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json",
    "tools/gold/build_gold_challenge_lifecycle_lite_v0_1_0.py",
    "tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py",
    "tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh",
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

for rel in V0_4_3_FILES:
    p = repo / rel
    if not p.exists():
        errors.append(f"missing v0.4.3-owned file: {rel}")
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
        "v0.4.3-owned surface area",
        file=sys.stderr,
    )
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)

print("  TG1:taxonomy_gate: ok (no unapproved or denied reason-like tokens)")
PYEOF

# ---------------------------------------------------------------------------
# No-residue assertion. Verifies that (a) the v0.4.3/test-owned scratch
# path contains no leftover files, and (b) no v0.4.3 transient file
# residue has leaked into any inherited-tier (v0.4.0 / v0.4.1 / v0.4.2)
# fixture, schema, or tool directory. The scratch directory itself is
# removed by the EXIT trap; this assertion runs while the scratch dir
# still exists and verifies it is empty.
# ---------------------------------------------------------------------------
echo "[no-residue] scratch + inherited-tier residue assertion"
scratch_residue="$(find "$TMP_TEST_SCRATCH" -mindepth 1 -print 2>/dev/null || true)"
if [ -n "$scratch_residue" ]; then
  echo "FAIL: no-residue: v0.4.3 test scratch path contains residue:" >&2
  echo "$scratch_residue" >&2
  exit 1
fi
inherited_search_paths=(
  "$REPO_ROOT/fixtures/gold-governed-reliance-v0.4.0"
  "$REPO_ROOT/fixtures/gold-policy-evaluation-matrix-v0.4.2"
)
if [ -d "$REPO_ROOT/fixtures/gold-governed-reliance-v0.4.1" ]; then
  inherited_search_paths+=("$REPO_ROOT/fixtures/gold-governed-reliance-v0.4.1")
fi
inherited_residue="$(find "${inherited_search_paths[@]}" \
    \( -name '_v043_*' -o -name 'ro5_*' -o -name 'rel01_*' \
       -o -name 'sup*_bad_*' \) \
    -print 2>/dev/null || true)"
if [ -n "$inherited_residue" ]; then
  echo "FAIL: no-residue: v0.4.3 transient file residue found under" >&2
  echo "inherited-tier paths (this is a non-touch guardrail violation):" >&2
  echo "$inherited_residue" >&2
  exit 1
fi
echo "  no-residue: ok (scratch empty; zero inherited-tier residue)"

# ---------------------------------------------------------------------------
# Scoped sha256 snapshot (AFTER) and equality with BEFORE.
# This Phase 2 harness performs no mutations on v0.4.3-owned source paths,
# so the BEFORE/AFTER snapshot must be byte-identical.
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
echo "PASS: tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh (Phase 3 full)"
echo "  99 / 99 Phase 3 exercises:"
echo "    - 6 positive-path (PP1..PP6)"
echo "        PP1 pristine v0.4.3 build with --self-validate"
echo "        PP2 pristine independent v0.4.3 verifier pass"
echo "        PP3 manifest layout (7 subjects, 6-ID collision class)"
echo "        PP4 runtime records body scalar injection"
echo "            (policy_evaluation_report_sha256, generated_at,"
echo "             per-record lifecycle_fingerprint)"
echo "        PP5 lifecycle report (5 rows + coverage_summary"
echo "            6-key status_value_count + cross-anchors)"
echo "        PP6 6-ID file-level distinctness"
echo "    - 48 canonical verifier reachability (case01..case48)"
echo "        case01..case24 inherited v0.4.0 R01..R24 (relayed)"
echo "        case25..case29 inherited v0.4.1 R25..R29 (relayed)"
echo "        case30..case38 inherited v0.4.2 R30..R38 (relayed)"
echo "        case39..case48 v0.4.3-owned R39..R48"
echo "    -  4 runtime-scalar mutation variants (rt1, rt1b, rt2, rt3)"
echo "    - 23 duplicates / subject-table / collision (dup01..dup23)"
echo "    -  5 supplementals (sup01..sup05: R42 x 1, R43 x 3, R46 x 1)"
echo "        sup01 R42 withdrawn without withdrawal_record_ref"
echo "        sup02 R43 first event is not filed (distinct from case43)"
echo "        sup03 R43 event after a terminal event"
echo "        sup04 R43 current_status disagrees with final event"
echo "        sup05 R46 challenge_lifecycle_report_id collides with"
echo "              policy_evaluation_report_id at the lifecycle report"
echo "              body level"
echo "    -  6 runner-only exercises across 5 approved reasons"
echo "        (ro1, ro2, ro2b, ro3, ro4, ro5)"
echo "    -  1 runner-relay-of-verifier (rel01: inherited reason verbatim)"
echo "    -  1 runner-relay across all v0.4.3-owned reasons (rel02)"
echo "    -  1 non-destructive env01 INFRA trap (tempdir/copy only)"
echo "    -  1 positive determinism re-run (sup_det: byte-identity"
echo "        of subject[5].sha256, subject[6].sha256, all 5 per-record"
echo "        lifecycle_fingerprint, and report_fingerprint)"
echo "    -  1 no-residue assertion (v0.4.3 scratch + inherited tiers)"
echo "    -  1 taxonomy gate with environmental-wrapper deny-list (TG1)"
echo "    -  1 scoped sha256 snapshot equality (SS)"
