#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.3.0 acceptance handoff.
#
# 31 top-level cases (covering all 17 stable verifier failure reasons,
# all 5 runner-only refusal codes, two inline structural checks, and a
# scoped sha256 snapshot of committed v0.3.0 source paths):
#
#   1.  Compose v0.2.7 gateway evidence (A) into tmp.
#   2.  Generate v0.2.8 acceptance package over A.
#   3.  Run v0.2.9 revocation/challenge drill over the v0.2.8 package.
#   4.  Build v0.3.0 handoff package (pristine).
#   5.  Verify pristine handoff package.
#   6.  Inline check handoff manifest subject order + roles.
#   7.  Inline check handoff summary fields.
#   8.  invalid_handoff_manifest             (manifest document_type tampered)
#   9.  handoff_subject_file_missing         (summary subject deleted)
#  10.  handoff_subject_path_traversal       (subject path '..')
#  11.  handoff_subject_path_traversal       (subject path absolute)
#  12.  handoff_subject_hash_mismatch        (summary tampered, no rehash)
#  13.  nested_composed_evidence_invalid     (composed-gateway-evidence-report tampered)
#  14.  nested_acceptance_package_invalid    (acceptance-record tampered)
#  15.  nested_revocation_challenge_drill_invalid (drill review-events tampered)
#  16.  handoff_summary_invalid              (summary document_type tampered)
#  17.  handoff_summary_binding_mismatch     (summary included_chain manifest_sha256 stale)
#  18.  handoff_chain_binding_mismatch       (composed-gateway-evidence swapped to second valid v0.2.7 package; nested validators still pass)
#  19.  handoff_record_mismatch              (summary acceptance_record_id mutated)
#  20.  handoff_purpose_mismatch             (summary purpose_id mutated)
#  21.  handoff_posture_invalid              (handoff posture set to bogus value)
#  22.  handoff_posture_downgrade            (rank-0 posture under a rank-1 drill)
#  23.  handoff_overclaim                    (summary reuse_warning contains 'gold certified')
#  24.  handoff_limitations_missing          (summary.scope_limitations=[])
#  25.  handoff_non_claims_missing           (summary.non_claims=[])
#  26.  Runner refuses with composed_evidence_validation_failed when
#       the v0.2.7 evidence package is tampered; no partial output written.
#  27.  Runner refuses with acceptance_package_validation_failed when
#       the v0.2.8 acceptance package is tampered; no partial output written.
#  28.  Runner refuses with drill_package_validation_failed when the
#       v0.2.9 drill package is tampered; no partial output written.
#  29.  Runner refuses with handoff_chain_binding_failed when
#       --composed-evidence-manifest points to a second valid v0.2.7
#       package whose sha disagrees with the nested v0.2.8/v0.2.9 chain;
#       no partial output written.
#  30.  Runner refuses with self_validation_failed when --self-validate
#       is supplied with --handoff-purpose containing an overclaim token;
#       no partial output written.
#  31.  Scoped mutation snapshot: committed v0.3.0 schemas, fixture,
#       tools, demo docs, test, and release doc unchanged after all
#       cases above.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

V027_COMPOSER="tools/silver/compose_gateway_evidence_demo_v0_1_0.py"
V028_GENERATOR="tools/silver/generate_relying_party_acceptance_record_v0_1_0.py"
V029_RUNNER="tools/silver/run_revocation_challenge_drill_v0_1_0.py"
V030_RUNNER="tools/silver/build_silver_acceptance_handoff_v0_1_0.py"
V030_VERIFIER="tools/silver/verify_silver_acceptance_handoff_v0_1_0.py"

DEMO_ROOT="demos/silver-demo-004-composed-gateway-evidence"
ADAPTER="examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json"
V027_FIXTURE="fixtures/silver-composed-gateway-evidence-v0.2.7"
V028_FIXTURE="fixtures/silver-relying-party-acceptance-v0.2.8"
POLICY_FIXTURE="$V028_FIXTURE/acceptance-policy.json"
V029_FIXTURE="fixtures/silver-revocation-challenge-drill-v0.2.9"
REVIEW_EVENTS="$V029_FIXTURE/review-events.jsonl"
V030_FIXTURE="fixtures/silver-acceptance-handoff-v0.3.0"

RELEASE_DOC="docs/silver/silver-acceptance-handoff-v0.3.0.md"
DEMO007_ROOT="demos/silver-demo-007-acceptance-handoff"
SCHEMA_SUMMARY="schemas/silver-acceptance-handoff-summary-v0.1.0.md"
SCHEMA_MANIFEST="schemas/silver-acceptance-handoff-manifest-v0.1.0.md"

TMPDIR_ROOT="$(mktemp -d -t proofrail-v030-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

V027_PKG_A="$TMPDIR_ROOT/v027-evidence-A"
V027_PKG_B="$TMPDIR_ROOT/v027-evidence-B"
V028_PKG="$TMPDIR_ROOT/v028-acceptance"
V029_PKG="$TMPDIR_ROOT/v029-drill"
PRISTINE="$TMPDIR_ROOT/pristine-handoff"

GENERATED_AT_V027_A="2026-06-22T00:00:00Z"
GENERATED_AT_V027_B="2026-06-23T00:00:00Z"
GENERATED_AT_V028="2026-06-22T00:00:00Z"
GENERATED_AT_V029="2026-06-27T00:00:00Z"
GENERATED_AT_V030="2026-06-28T00:00:00Z"
CHALLENGE_CLOSES_AT="2026-07-22T00:00:00Z"

# Snapshot committed v0.3.0-owned files for Step 31.
SNAPSHOT_BEFORE="$TMPDIR_ROOT/snapshot-before.sha256"
{
  shasum -a 256 "$V030_RUNNER" "$V030_VERIFIER"
  shasum -a 256 "$SCHEMA_SUMMARY" "$SCHEMA_MANIFEST"
  shasum -a 256 "$V030_FIXTURE/README.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO007_ROOT/README.md" "$DEMO007_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_BEFORE"

# Helper: copy pristine handoff package into a fresh tamper directory.
fresh_copy() {
    local dest="$1"
    rm -rf "$dest"
    cp -R "$PRISTINE" "$dest"
}

# Helper: recompute sha256 + size for a list of subject paths inside a
# handoff package's silver-acceptance-handoff-manifest.json. Required
# after semantic edits so the verifier reaches semantic checks instead
# of short-circuiting on handoff_subject_hash_mismatch.
rehash_handoff_subjects() {
    local pkg_dir="$1"
    shift
    python3 - "$pkg_dir" "$@" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
targets = set(sys.argv[2:])
mpath = pkg / "silver-acceptance-handoff-manifest.json"
m = json.loads(mpath.read_text())
for s in m["subjects"]:
    if s["path"] in targets:
        full = pkg / s["path"]
        data = full.read_bytes()
        s["sha256"] = "sha256:" + hashlib.sha256(data).hexdigest()
        s["size_bytes"] = len(data)
mpath.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
}

# Helper: expect verifier to fail with the given stable reason.
expect_verifier_fail() {
    local label="$1"
    local pkg_dir="$2"
    local accepted_reasons="$3"
    shift 3
    local logf
    logf="$TMPDIR_ROOT/$label.log"
    set +e
    python3 "$V030_VERIFIER" --manifest "$pkg_dir/silver-acceptance-handoff-manifest.json" \
        "$@" > "$logf" 2>&1
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        echo "FAIL: [$label] verifier exited 0 but expected failure"
        cat "$logf"
        exit 1
    fi
    if grep -q "Traceback" "$logf"; then
        echo "FAIL: [$label] Python traceback leaked"
        cat "$logf"
        exit 1
    fi
    local matched=0
    local IFS='|'
    for r in $accepted_reasons; do
        if grep -q "FAIL: $r" "$logf"; then
            matched=1
            break
        fi
    done
    if [ "$matched" -ne 1 ]; then
        echo "FAIL: [$label] expected one of [$accepted_reasons], got:"
        cat "$logf"
        exit 1
    fi
}

# === Step 1: Compose v0.2.7 evidence (A) ===
echo "=== Step 1: Compose v0.2.7 gateway evidence A into tmp ==="
python3 "$V027_COMPOSER" \
  --demo-root "$DEMO_ROOT" \
  --adapter "$ADAPTER" \
  --gateway-events "$V027_FIXTURE/gateway-events.jsonl" \
  --output-dir "$V027_PKG_A" \
  --generated-at "$GENERATED_AT_V027_A" \
  --force > "$TMPDIR_ROOT/t01.log" 2>&1
[ -f "$V027_PKG_A/composed-gateway-evidence-manifest.json" ] || {
    echo "FAIL step 1: v0.2.7 composer did not produce manifest"; cat "$TMPDIR_ROOT/t01.log"; exit 1; }
echo "PASS step 1"

# === Step 2: Generate v0.2.8 acceptance package ===
echo "=== Step 2: Generate v0.2.8 acceptance package ==="
python3 "$V028_GENERATOR" \
  --policy "$POLICY_FIXTURE" \
  --evidence-manifest "$V027_PKG_A/composed-gateway-evidence-manifest.json" \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at "$GENERATED_AT_V028" \
  --challenge-closes-at "$CHALLENGE_CLOSES_AT" \
  --output-dir "$V028_PKG" \
  --force > "$TMPDIR_ROOT/t02.log" 2>&1
[ -f "$V028_PKG/acceptance-package-manifest.json" ] || {
    echo "FAIL step 2: v0.2.8 generator did not produce manifest"; cat "$TMPDIR_ROOT/t02.log"; exit 1; }
echo "PASS step 2"

# === Step 3: Run v0.2.9 drill ===
echo "=== Step 3: Run v0.2.9 drill ==="
python3 "$V029_RUNNER" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --review-events "$REVIEW_EVENTS" \
  --generated-at "$GENERATED_AT_V029" \
  --output-dir "$V029_PKG" \
  --force > "$TMPDIR_ROOT/t03.log" 2>&1
[ -f "$V029_PKG/revocation-challenge-drill-manifest.json" ] || {
    echo "FAIL step 3: drill runner did not produce manifest"; cat "$TMPDIR_ROOT/t03.log"; exit 1; }
echo "PASS step 3"

# === Step 4: Build v0.3.0 handoff package (pristine) ===
echo "=== Step 4: Build v0.3.0 handoff package (pristine) ==="
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$V027_PKG_A/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --drill-manifest "$V029_PKG/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$PRISTINE" \
  --force > "$TMPDIR_ROOT/t04.log" 2>&1
[ -f "$PRISTINE/silver-acceptance-handoff-manifest.json" ] || {
    echo "FAIL step 4: handoff runner did not produce manifest"; cat "$TMPDIR_ROOT/t04.log"; exit 1; }
echo "PASS step 4"

# === Step 5: Verify pristine handoff package ===
echo "=== Step 5: Verify pristine handoff package ==="
python3 "$V030_VERIFIER" \
    --manifest "$PRISTINE/silver-acceptance-handoff-manifest.json" \
    > "$TMPDIR_ROOT/t05.log" 2>&1
grep -q "^PASS:" "$TMPDIR_ROOT/t05.log" || {
    echo "FAIL step 5: pristine verifier did not PASS"; cat "$TMPDIR_ROOT/t05.log"; exit 1; }
echo "PASS step 5"

# === Step 6: Inline check handoff manifest subject order + roles ===
echo "=== Step 6: Inline check handoff manifest subject order + roles ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1] + "/silver-acceptance-handoff-manifest.json"))
expected = [
    ("composed-gateway-evidence/composed-gateway-evidence-manifest.json", "composed_gateway_evidence_manifest"),
    ("acceptance-package/acceptance-package-manifest.json", "relying_party_acceptance_package_manifest"),
    ("revocation-challenge-drill/revocation-challenge-drill-manifest.json", "revocation_challenge_drill_manifest"),
    ("silver-acceptance-handoff-summary.json", "silver_acceptance_handoff_summary"),
]
subs = m["subjects"]
if len(subs) != 4:
    print(f"FAIL: subjects count {len(subs)} != 4"); sys.exit(1)
for i, (p, r) in enumerate(expected):
    if subs[i]["path"] != p or subs[i]["role"] != r:
        print(f"FAIL: subject {i} mismatch (got {subs[i]!r})"); sys.exit(1)
if m["document_type"] != "proofrail.silver.acceptance_handoff_manifest":
    print(f"FAIL: document_type {m['document_type']!r}"); sys.exit(1)
if m["schema_version"] != "v0.1.0":
    print(f"FAIL: schema_version {m['schema_version']!r}"); sys.exit(1)
if m["proofrail_release"] != "v0.3.0":
    print(f"FAIL: proofrail_release {m['proofrail_release']!r}"); sys.exit(1)
if not m["scope_limitations"]: print("FAIL: manifest scope_limitations empty"); sys.exit(1)
if not m["non_claims"]: print("FAIL: manifest non_claims empty"); sys.exit(1)
PYEOF
echo "PASS step 6"

# === Step 7: Inline check handoff summary fields ===
echo "=== Step 7: Inline check handoff summary fields ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1] + "/silver-acceptance-handoff-summary.json"))
ic = s["included_chain"]
checks = [
    ("composed_gateway_evidence.source_release", ic["composed_gateway_evidence"]["source_release"], "v0.2.7"),
    ("relying_party_acceptance.source_release", ic["relying_party_acceptance"]["source_release"], "v0.2.8"),
    ("revocation_challenge_drill.source_release", ic["revocation_challenge_drill"]["source_release"], "v0.2.9"),
    ("relying_party_acceptance.acceptance_record_id", ic["relying_party_acceptance"]["acceptance_record_id"], "proofrail-acceptance-record-demo-001"),
    ("relying_party_acceptance.decision_status", ic["relying_party_acceptance"]["decision_status"], "accepted"),
    ("relying_party_acceptance.purpose_id", ic["relying_party_acceptance"]["purpose_id"], "demo_trust_boundary_review"),
    ("revocation_challenge_drill.recommended_local_posture", ic["revocation_challenge_drill"]["recommended_local_posture"], "acceptance_requires_review_before_reuse"),
    ("handoff_result.handoff_package_status", s["handoff_result"]["handoff_package_status"], "complete"),
    ("handoff_result.recommended_handoff_posture", s["handoff_result"]["recommended_handoff_posture"], "silver_handoff_complete_review_required_before_reuse"),
]
for label, actual, expected in checks:
    if actual != expected:
        print(f"FAIL: {label} = {actual!r} != {expected!r}"); sys.exit(1)
if not s["scope_limitations"]: print("FAIL: summary scope_limitations empty"); sys.exit(1)
if not s["non_claims"]: print("FAIL: summary non_claims empty"); sys.exit(1)
if not s["handoff_result"]["reuse_warning"]:
    print("FAIL: reuse_warning empty"); sys.exit(1)
PYEOF
echo "PASS step 7"

# === Step 8: invalid_handoff_manifest ===
echo "=== Step 8: invalid_handoff_manifest ==="
T8="$TMPDIR_ROOT/t08"; fresh_copy "$T8"
python3 - "$T8" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "silver-acceptance-handoff-manifest.json"
m = json.loads(mp.read_text())
m["document_type"] = "proofrail.silver.not_a_real_manifest_type"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step08" "$T8" "invalid_handoff_manifest"
echo "PASS step 8"

# === Step 9: handoff_subject_file_missing ===
echo "=== Step 9: handoff_subject_file_missing ==="
T9="$TMPDIR_ROOT/t09"; fresh_copy "$T9"
rm "$T9/silver-acceptance-handoff-summary.json"
expect_verifier_fail "step09" "$T9" "handoff_subject_file_missing"
echo "PASS step 9"

# === Step 10: handoff_subject_path_traversal (..) ===
echo "=== Step 10: handoff_subject_path_traversal (..) ==="
T10="$TMPDIR_ROOT/t10"; fresh_copy "$T10"
python3 - "$T10" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "silver-acceptance-handoff-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][3]["path"] = "../etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step10" "$T10" "handoff_subject_path_traversal"
echo "PASS step 10"

# === Step 11: handoff_subject_path_traversal (absolute) ===
echo "=== Step 11: handoff_subject_path_traversal (absolute) ==="
T11="$TMPDIR_ROOT/t11"; fresh_copy "$T11"
python3 - "$T11" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "silver-acceptance-handoff-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "/etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step11" "$T11" "handoff_subject_path_traversal"
echo "PASS step 11"

# === Step 12: handoff_subject_hash_mismatch ===
echo "=== Step 12: handoff_subject_hash_mismatch ==="
T12="$TMPDIR_ROOT/t12"; fresh_copy "$T12"
# Tamper summary without rehashing the handoff manifest subject.
python3 - "$T12" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step12" "$T12" "handoff_subject_hash_mismatch"
echo "PASS step 12"

# === Step 13: nested_composed_evidence_invalid ===
echo "=== Step 13: nested_composed_evidence_invalid ==="
T13="$TMPDIR_ROOT/t13"; fresh_copy "$T13"
# Append bytes to the nested v0.2.7 report. The top-level handoff
# subject 0 (composed-gateway-evidence-manifest.json itself) is
# unchanged, so step (6) passes; the v0.2.7 verifier subprocess
# then fails on its own subject-hash check.
python3 - "$T13" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "composed-gateway-evidence" / "composed-gateway-evidence-report.json"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step13" "$T13" "nested_composed_evidence_invalid"
echo "PASS step 13"

# === Step 14: nested_acceptance_package_invalid ===
echo "=== Step 14: nested_acceptance_package_invalid ==="
T14="$TMPDIR_ROOT/t14"; fresh_copy "$T14"
# Append bytes to the nested v0.2.8 acceptance-record. The top-level
# acceptance-package-manifest.json is unchanged so step (6) passes,
# and the v0.2.8 validator subprocess then fails on its own subject-
# hash check.
python3 - "$T14" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "acceptance-package" / "acceptance-record.json"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step14" "$T14" "nested_acceptance_package_invalid"
echo "PASS step 14"

# === Step 15: nested_revocation_challenge_drill_invalid ===
echo "=== Step 15: nested_revocation_challenge_drill_invalid ==="
T15="$TMPDIR_ROOT/t15"; fresh_copy "$T15"
# Append bytes to the nested v0.2.9 review-events JSONL. The top-level
# revocation-challenge-drill-manifest.json is unchanged so step (6)
# passes, and the v0.2.9 verifier subprocess then fails on its own
# subject-hash check.
python3 - "$T15" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "revocation-challenge-drill" / "review-events.jsonl"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step15" "$T15" "nested_revocation_challenge_drill_invalid"
echo "PASS step 15"

# === Step 16: handoff_summary_invalid ===
echo "=== Step 16: handoff_summary_invalid ==="
T16="$TMPDIR_ROOT/t16"; fresh_copy "$T16"
python3 - "$T16" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["document_type"] = "proofrail.silver.not_a_real_summary_type"
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T16" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step16" "$T16" "handoff_summary_invalid"
echo "PASS step 16"

# === Step 17: handoff_summary_binding_mismatch ===
echo "=== Step 17: handoff_summary_binding_mismatch ==="
T17="$TMPDIR_ROOT/t17"; fresh_copy "$T17"
# Mutate summary's included_chain composed_gateway_evidence.manifest_sha256
# to a stale value. Rehash summary subject so subject-hash check passes
# and binding cross-check fires.
python3 - "$T17" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["included_chain"]["composed_gateway_evidence"]["manifest_sha256"] = \
    "sha256:" + ("00" * 32)
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T17" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step17" "$T17" "handoff_summary_binding_mismatch"
echo "PASS step 17"

# === Step 18: handoff_chain_binding_mismatch ===
echo "=== Step 18: handoff_chain_binding_mismatch ==="
# Amendment 4: nested v0.2.7/v0.2.8/v0.2.9 packages MUST remain valid
# under their own validators (WITHOUT --evidence-package-root). Only
# the v0.3.0-owned cross-copy binding must break.
#
# Approach: build a second valid v0.2.7 package B at a different
# --generated-at, swap composed-gateway-evidence/ in the pristine
# handoff to B (a different but self-valid v0.2.7 package), update the
# summary's included_chain.composed_gateway_evidence.manifest_sha256
# to the new sha (so handoff_summary_binding_mismatch does NOT fire),
# and rehash the top-level handoff subjects 0 (the new composed
# manifest) and 3 (the summary).
#
# Result:
#   - step (7) v0.2.7 verifier passes on B (B is valid on its own).
#   - step (8) v0.2.8 validator passes on the unchanged v0.2.8 package
#     (no --evidence-package-root, so v0.3.0 owns the cross-copy
#     binding).
#   - step (9) v0.2.9 verifier passes on the unchanged v0.2.9 package
#     (no --evidence-package-root, same reason).
#   - step (11) summary binding passes (we updated the summary).
#   - step (12)(a) fires: subj0_sha = sha(B) !=
#     nested v0.2.8 record evidence_package.manifest_sha256 = sha(A).
echo "    - composing second valid v0.2.7 package B"
python3 "$V027_COMPOSER" \
  --demo-root "$DEMO_ROOT" \
  --adapter "$ADAPTER" \
  --gateway-events "$V027_FIXTURE/gateway-events.jsonl" \
  --output-dir "$V027_PKG_B" \
  --generated-at "$GENERATED_AT_V027_B" \
  --force > "$TMPDIR_ROOT/t18-composer.log" 2>&1
[ -f "$V027_PKG_B/composed-gateway-evidence-manifest.json" ] || {
    echo "FAIL step 18: v0.2.7 composer B did not produce manifest"
    cat "$TMPDIR_ROOT/t18-composer.log"; exit 1; }
T18="$TMPDIR_ROOT/t18"; fresh_copy "$T18"
rm -rf "$T18/composed-gateway-evidence"
cp -R "$V027_PKG_B" "$T18/composed-gateway-evidence"
python3 - "$T18" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
mp = pkg / "composed-gateway-evidence" / "composed-gateway-evidence-manifest.json"
new_sha = "sha256:" + hashlib.sha256(mp.read_bytes()).hexdigest()
sp = pkg / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["included_chain"]["composed_gateway_evidence"]["manifest_sha256"] = new_sha
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T18" \
    "composed-gateway-evidence/composed-gateway-evidence-manifest.json" \
    "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step18" "$T18" "handoff_chain_binding_mismatch"
echo "PASS step 18"

# === Step 19: handoff_record_mismatch ===
echo "=== Step 19: handoff_record_mismatch ==="
T19="$TMPDIR_ROOT/t19"; fresh_copy "$T19"
# Mutate summary acceptance_record_id only. Keep manifest_sha256
# correct so summary binding passes; chain binding passes; then
# handoff_record_mismatch fires.
python3 - "$T19" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["included_chain"]["relying_party_acceptance"]["acceptance_record_id"] = \
    "some.other.acceptance.record"
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T19" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step19" "$T19" "handoff_record_mismatch"
echo "PASS step 19"

# === Step 20: handoff_purpose_mismatch ===
echo "=== Step 20: handoff_purpose_mismatch ==="
T20="$TMPDIR_ROOT/t20"; fresh_copy "$T20"
# Mutate summary purpose_id only. Keep acceptance_record_id and
# decision_status correct so handoff_record_mismatch does not fire.
python3 - "$T20" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["included_chain"]["relying_party_acceptance"]["purpose_id"] = "some_other_purpose"
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T20" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step20" "$T20" "handoff_purpose_mismatch"
echo "PASS step 20"

# === Step 21: handoff_posture_invalid ===
echo "=== Step 21: handoff_posture_invalid ==="
T21="$TMPDIR_ROOT/t21"; fresh_copy "$T21"
# Set handoff_result.recommended_handoff_posture to a value outside
# the closed set. Shape check accepts (just non-empty string); posture
# validation step then rejects.
python3 - "$T21" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["handoff_result"]["recommended_handoff_posture"] = "some_bogus_handoff_posture"
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T21" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step21" "$T21" "handoff_posture_invalid"
echo "PASS step 21"

# === Step 22: handoff_posture_downgrade ===
echo "=== Step 22: handoff_posture_downgrade ==="
T22="$TMPDIR_ROOT/t22"; fresh_copy "$T22"
# Pristine drill posture is acceptance_requires_review_before_reuse
# (rank 1). Setting recommended_handoff_posture to rank-0
# silver_handoff_complete_for_demo_scope is a downgrade.
python3 - "$T22" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["handoff_result"]["recommended_handoff_posture"] = \
    "silver_handoff_complete_for_demo_scope"
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T22" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step22" "$T22" "handoff_posture_downgrade"
echo "PASS step 22"

# === Step 23: handoff_overclaim ===
echo "=== Step 23: handoff_overclaim ==="
T23="$TMPDIR_ROOT/t23"; fresh_copy "$T23"
# Inject an overclaim token into handoff_result.reuse_warning (which is
# a string outside scope_limitations / non_claims).
python3 - "$T23" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["handoff_result"]["reuse_warning"] = "This package is Gold certified."
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T23" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step23" "$T23" "handoff_overclaim"
echo "PASS step 23"

# === Step 24: handoff_limitations_missing ===
echo "=== Step 24: handoff_limitations_missing ==="
T24="$TMPDIR_ROOT/t24"; fresh_copy "$T24"
python3 - "$T24" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["scope_limitations"] = []
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T24" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step24" "$T24" "handoff_limitations_missing"
echo "PASS step 24"

# === Step 25: handoff_non_claims_missing ===
echo "=== Step 25: handoff_non_claims_missing ==="
T25="$TMPDIR_ROOT/t25"; fresh_copy "$T25"
python3 - "$T25" <<'PYEOF'
import json, sys
from pathlib import Path
sp = Path(sys.argv[1]) / "silver-acceptance-handoff-summary.json"
s = json.loads(sp.read_text())
s["non_claims"] = []
sp.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_handoff_subjects "$T25" "silver-acceptance-handoff-summary.json"
expect_verifier_fail "step25" "$T25" "handoff_non_claims_missing"
echo "PASS step 25"

# === Step 26: Runner refuses with composed_evidence_validation_failed ===
echo "=== Step 26: Runner refuses (composed_evidence_validation_failed) ==="
TAMPER_V027="$TMPDIR_ROOT/tampered-v027"
rm -rf "$TAMPER_V027"
cp -R "$V027_PKG_A" "$TAMPER_V027"
# Tamper the nested composed evidence report so v0.2.7 verifier fails.
python3 - "$TAMPER_V027/composed-gateway-evidence-report.json" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
RUNNER_OUT26="$TMPDIR_ROOT/runner-refused-26"
rm -rf "$RUNNER_OUT26"
set +e
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$TAMPER_V027/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --drill-manifest "$V029_PKG/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$RUNNER_OUT26" \
  --force > "$TMPDIR_ROOT/t26.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 26: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t26.log"; exit 1
fi
if ! grep -q "composed_evidence_validation_failed" "$TMPDIR_ROOT/t26.log"; then
    echo "FAIL step 26: runner did not report composed_evidence_validation_failed"
    cat "$TMPDIR_ROOT/t26.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t26.log"; then
    echo "FAIL step 26: Python traceback leaked"
    cat "$TMPDIR_ROOT/t26.log"; exit 1
fi
if [ -d "$RUNNER_OUT26" ]; then
    echo "FAIL step 26: runner left partial output directory at $RUNNER_OUT26"
    ls -la "$RUNNER_OUT26"; exit 1
fi
echo "PASS step 26"

# === Step 27: Runner refuses with acceptance_package_validation_failed ===
echo "=== Step 27: Runner refuses (acceptance_package_validation_failed) ==="
TAMPER_V028="$TMPDIR_ROOT/tampered-v028"
rm -rf "$TAMPER_V028"
cp -R "$V028_PKG" "$TAMPER_V028"
python3 - "$TAMPER_V028/acceptance-record.json" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
RUNNER_OUT27="$TMPDIR_ROOT/runner-refused-27"
rm -rf "$RUNNER_OUT27"
set +e
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$V027_PKG_A/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$TAMPER_V028/acceptance-package-manifest.json" \
  --drill-manifest "$V029_PKG/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$RUNNER_OUT27" \
  --force > "$TMPDIR_ROOT/t27.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 27: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t27.log"; exit 1
fi
if ! grep -q "acceptance_package_validation_failed" "$TMPDIR_ROOT/t27.log"; then
    echo "FAIL step 27: runner did not report acceptance_package_validation_failed"
    cat "$TMPDIR_ROOT/t27.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t27.log"; then
    echo "FAIL step 27: Python traceback leaked"
    cat "$TMPDIR_ROOT/t27.log"; exit 1
fi
if [ -d "$RUNNER_OUT27" ]; then
    echo "FAIL step 27: runner left partial output directory at $RUNNER_OUT27"
    ls -la "$RUNNER_OUT27"; exit 1
fi
echo "PASS step 27"

# === Step 28: Runner refuses with drill_package_validation_failed ===
echo "=== Step 28: Runner refuses (drill_package_validation_failed) ==="
TAMPER_V029="$TMPDIR_ROOT/tampered-v029"
rm -rf "$TAMPER_V029"
cp -R "$V029_PKG" "$TAMPER_V029"
python3 - "$TAMPER_V029/review-events.jsonl" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
RUNNER_OUT28="$TMPDIR_ROOT/runner-refused-28"
rm -rf "$RUNNER_OUT28"
set +e
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$V027_PKG_A/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --drill-manifest "$TAMPER_V029/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$RUNNER_OUT28" \
  --force > "$TMPDIR_ROOT/t28.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 28: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t28.log"; exit 1
fi
if ! grep -q "drill_package_validation_failed" "$TMPDIR_ROOT/t28.log"; then
    echo "FAIL step 28: runner did not report drill_package_validation_failed"
    cat "$TMPDIR_ROOT/t28.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t28.log"; then
    echo "FAIL step 28: Python traceback leaked"
    cat "$TMPDIR_ROOT/t28.log"; exit 1
fi
if [ -d "$RUNNER_OUT28" ]; then
    echo "FAIL step 28: runner left partial output directory at $RUNNER_OUT28"
    ls -la "$RUNNER_OUT28"; exit 1
fi
echo "PASS step 28"

# === Step 29: Runner refuses with handoff_chain_binding_failed ===
echo "=== Step 29: Runner refuses (handoff_chain_binding_failed) ==="
# Point --composed-evidence-manifest at the second valid v0.2.7
# package B (built in Step 18) while --acceptance-manifest and
# --drill-manifest still derive from v0.2.7 A. All three subprocess
# validators pass (each input is self-valid), then the runner's
# chain-binding check (a) fires:
#   sha(B's composed manifest) != record.evidence_package.manifest_sha256
# (which still references A).
RUNNER_OUT29="$TMPDIR_ROOT/runner-refused-29"
rm -rf "$RUNNER_OUT29"
set +e
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$V027_PKG_B/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --drill-manifest "$V029_PKG/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$RUNNER_OUT29" \
  --force > "$TMPDIR_ROOT/t29.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 29: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t29.log"; exit 1
fi
if ! grep -q "handoff_chain_binding_failed" "$TMPDIR_ROOT/t29.log"; then
    echo "FAIL step 29: runner did not report handoff_chain_binding_failed"
    cat "$TMPDIR_ROOT/t29.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t29.log"; then
    echo "FAIL step 29: Python traceback leaked"
    cat "$TMPDIR_ROOT/t29.log"; exit 1
fi
if [ -d "$RUNNER_OUT29" ]; then
    echo "FAIL step 29: runner left partial output directory at $RUNNER_OUT29"
    ls -la "$RUNNER_OUT29"; exit 1
fi
echo "PASS step 29"

# === Step 30: Runner refuses with self_validation_failed ===
echo "=== Step 30: Runner refuses (self_validation_failed) ==="
# Inject an overclaim token into --handoff-purpose. The runner accepts
# the value (non-empty string), writes it to summary's
# handoff_context.handoff_purpose, then --self-validate invokes the
# verifier whose overclaim guard fires on 'gold certified' in a summary
# string outside scope_limitations / non_claims.
RUNNER_OUT30="$TMPDIR_ROOT/runner-refused-30"
rm -rf "$RUNNER_OUT30"
set +e
python3 "$V030_RUNNER" \
  --composed-evidence-manifest "$V027_PKG_A/composed-gateway-evidence-manifest.json" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --drill-manifest "$V029_PKG/revocation-challenge-drill-manifest.json" \
  --generated-at "$GENERATED_AT_V030" \
  --output-dir "$RUNNER_OUT30" \
  --handoff-purpose "demo_gold_certified_review" \
  --force \
  --self-validate > "$TMPDIR_ROOT/t30.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 30: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t30.log"; exit 1
fi
if ! grep -q "self_validation_failed" "$TMPDIR_ROOT/t30.log"; then
    echo "FAIL step 30: runner did not report self_validation_failed"
    cat "$TMPDIR_ROOT/t30.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t30.log"; then
    echo "FAIL step 30: Python traceback leaked"
    cat "$TMPDIR_ROOT/t30.log"; exit 1
fi
if [ -d "$RUNNER_OUT30" ]; then
    echo "FAIL step 30: runner left partial output directory at $RUNNER_OUT30"
    ls -la "$RUNNER_OUT30"; exit 1
fi
echo "PASS step 30"

# === Step 31: Scoped mutation snapshot of committed v0.3.0 source paths ===
echo "=== Step 31: Scoped mutation snapshot ==="
SNAPSHOT_AFTER="$TMPDIR_ROOT/snapshot-after.sha256"
{
  shasum -a 256 "$V030_RUNNER" "$V030_VERIFIER"
  shasum -a 256 "$SCHEMA_SUMMARY" "$SCHEMA_MANIFEST"
  shasum -a 256 "$V030_FIXTURE/README.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO007_ROOT/README.md" "$DEMO007_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_AFTER"
if ! diff -q "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" > /dev/null; then
    echo "FAIL step 31: committed v0.3.0 source paths mutated during test run"
    diff "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" || true
    exit 1
fi
echo "PASS step 31"

echo ""
echo "ALL PASS: 31 cases for ProofRail Silver v0.3.0 acceptance handoff"
