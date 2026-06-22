#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.9 revocation/challenge drill.
#
# 33 top-level cases (covering all 22 stable verifier failure reasons,
# both runner-only refusal codes, two inline structural checks, and a
# scoped sha256 snapshot of committed v0.2.9 source paths):
#
#   1.  Compose v0.2.7 gateway evidence into tmp.
#   2.  Generate v0.2.8 relying-party acceptance package over that evidence.
#   3.  Run v0.2.9 drill against the v0.2.8 package.
#   4.  Verify pristine drill package (no --evidence-package-root).
#   5.  Verify pristine drill package (with --evidence-package-root).
#   6.  Inline check drill manifest subject order + roles.
#   7.  Inline check drill report fields (base_acceptance, posture, etc.).
#   8.  invalid_drill_package_manifest          (manifest document_type tampered)
#   9.  drill_subject_file_missing              (review-events.jsonl removed)
#   10. drill_subject_path_traversal            (subject path '..')
#   11. drill_subject_path_traversal            (subject path absolute)
#   12. drill_subject_hash_mismatch             (subject tampered, no rehash)
#   13. nested_acceptance_package_invalid       (nested record tampered)
#   14. invalid_review_events                   (malformed JSONL line)
#   15. invalid_drill_report                    (report document_type tampered)
#   16. acceptance_record_binding_mismatch      (report.base_acceptance.purpose_id)
#   17. review_events_hash_mismatch             (events file mutated, report sha stale)
#   18. review_event_target_mismatch            (challenge event target wrong)
#   19. review_event_sequence_invalid           (events reordered, monotonicity broken)
#   20. challenge_window_missing                (report.base_acceptance.challenge_window={})
#   21. challenge_within_window_missing         (challenge events removed + report references neutralized)
#   22. challenge_window_classification_mismatch (report opens_at moved past event_time)
#   23. revocation_signal_missing               (revocation event removed)
#   24. revocation_signal_target_mismatch       (revocation event target wrong)
#   25. required_finding_missing                (revocation_signal_recorded finding removed)
#   26. required_review_trigger_missing         (post_acceptance_revocation_signal trigger removed)
#   27. recommended_posture_invalid             (posture set to bogus value)
#   28. scope_limitations_missing               (report.scope_limitations=[])
#   29. drill_non_claims_missing                (report.non_claims=[])
#   30. external_evidence_verification_failed   (original v0.2.7 package tampered)
#   31. Runner refuses with acceptance_package_validation_failed when the
#       v0.2.8 acceptance package is tampered; no partial output written.
#   32. Runner refuses with review_fixture_insufficient when the review
#       events fixture contains no revocation signal.
#   33. Scoped mutation snapshot: committed v0.2.9 schemas, fixture, tools,
#       demo docs, test, and release doc unchanged after all cases above.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

V027_COMPOSER="tools/silver/compose_gateway_evidence_demo_v0_1_0.py"
V028_GENERATOR="tools/silver/generate_relying_party_acceptance_record_v0_1_0.py"
V028_VALIDATOR="tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
V029_RUNNER="tools/silver/run_revocation_challenge_drill_v0_1_0.py"
V029_VERIFIER="tools/silver/verify_revocation_challenge_drill_v0_1_0.py"

DEMO_ROOT="demos/silver-demo-004-composed-gateway-evidence"
ADAPTER="examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json"
V027_FIXTURE="fixtures/silver-composed-gateway-evidence-v0.2.7"
V028_FIXTURE="fixtures/silver-relying-party-acceptance-v0.2.8"
POLICY_FIXTURE="$V028_FIXTURE/acceptance-policy.json"
V029_FIXTURE="fixtures/silver-revocation-challenge-drill-v0.2.9"
REVIEW_EVENTS="$V029_FIXTURE/review-events.jsonl"

RELEASE_DOC="docs/silver/silver-revocation-challenge-drill-v0.2.9.md"
DEMO006_ROOT="demos/silver-demo-006-revocation-challenge-drill"

TMPDIR_ROOT="$(mktemp -d -t proofrail-v029-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

V027_PKG="$TMPDIR_ROOT/v027-evidence"
V028_PKG="$TMPDIR_ROOT/v028-acceptance"
PRISTINE="$TMPDIR_ROOT/pristine-drill"

GENERATED_AT_V027="2026-06-22T00:00:00Z"
GENERATED_AT_V028="2026-06-22T00:00:00Z"
GENERATED_AT_V029="2026-06-27T00:00:00Z"
CHALLENGE_CLOSES_AT="2026-07-22T00:00:00Z"

# Snapshot committed v0.2.9-owned files for Step 33.
SNAPSHOT_BEFORE="$TMPDIR_ROOT/snapshot-before.sha256"
{
  shasum -a 256 "$V029_RUNNER" "$V029_VERIFIER"
  shasum -a 256 "$REVIEW_EVENTS" "$V029_FIXTURE/README.md"
  shasum -a 256 "schemas/silver-relying-party-review-event-v0.1.0.md" \
               "schemas/silver-revocation-challenge-drill-report-v0.1.0.md" \
               "schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO006_ROOT/README.md" "$DEMO006_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_BEFORE"

# Helper: copy pristine drill package into a fresh tamper directory.
fresh_copy() {
    local dest="$1"
    rm -rf "$dest"
    cp -R "$PRISTINE" "$dest"
}

# Helper: recompute sha256 + size for a list of subject paths inside a
# drill package's revocation-challenge-drill-manifest.json. Required
# after semantic edits so the verifier reaches semantic checks instead of
# short-circuiting on drill_subject_hash_mismatch.
rehash_drill_subjects() {
    local pkg_dir="$1"
    shift
    python3 - "$pkg_dir" "$@" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
targets = set(sys.argv[2:])
mpath = pkg / "revocation-challenge-drill-manifest.json"
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
    python3 "$V029_VERIFIER" --manifest "$pkg_dir/revocation-challenge-drill-manifest.json" \
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

# === Step 1: Compose v0.2.7 evidence ===
echo "=== Step 1: Compose v0.2.7 gateway evidence into tmp ==="
python3 "$V027_COMPOSER" \
  --demo-root "$DEMO_ROOT" \
  --adapter "$ADAPTER" \
  --gateway-events "$V027_FIXTURE/gateway-events.jsonl" \
  --output-dir "$V027_PKG" \
  --generated-at "$GENERATED_AT_V027" \
  --force > "$TMPDIR_ROOT/t01.log" 2>&1
[ -f "$V027_PKG/composed-gateway-evidence-manifest.json" ] || {
    echo "FAIL step 1: v0.2.7 composer did not produce manifest"; cat "$TMPDIR_ROOT/t01.log"; exit 1; }
echo "PASS step 1"

# === Step 2: Generate v0.2.8 acceptance package ===
echo "=== Step 2: Generate v0.2.8 acceptance package ==="
python3 "$V028_GENERATOR" \
  --policy "$POLICY_FIXTURE" \
  --evidence-manifest "$V027_PKG/composed-gateway-evidence-manifest.json" \
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

# === Step 3: Run v0.2.9 drill (pristine) ===
echo "=== Step 3: Run v0.2.9 drill (pristine) ==="
python3 "$V029_RUNNER" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --review-events "$REVIEW_EVENTS" \
  --generated-at "$GENERATED_AT_V029" \
  --output-dir "$PRISTINE" \
  --force > "$TMPDIR_ROOT/t03.log" 2>&1
[ -f "$PRISTINE/revocation-challenge-drill-manifest.json" ] || {
    echo "FAIL step 3: drill runner did not produce manifest"; cat "$TMPDIR_ROOT/t03.log"; exit 1; }
echo "PASS step 3"

# === Step 4: Verify pristine drill (no --evidence-package-root) ===
echo "=== Step 4: Verify pristine drill ==="
python3 "$V029_VERIFIER" --manifest "$PRISTINE/revocation-challenge-drill-manifest.json" \
    > "$TMPDIR_ROOT/t04.log" 2>&1
echo "PASS step 4"

# === Step 5: Verify pristine drill (--evidence-package-root) ===
echo "=== Step 5: Verify pristine drill with --evidence-package-root ==="
python3 "$V029_VERIFIER" --manifest "$PRISTINE/revocation-challenge-drill-manifest.json" \
    --evidence-package-root "$V027_PKG" > "$TMPDIR_ROOT/t05.log" 2>&1
echo "PASS step 5"

# === Step 6: Inline check drill manifest subject order ===
echo "=== Step 6: Inline check drill manifest subject order ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1] + "/revocation-challenge-drill-manifest.json"))
expected = [
    ("acceptance-package/acceptance-package-manifest.json", "nested_acceptance_package_manifest"),
    ("review-events.jsonl", "review_events"),
    ("revocation-challenge-drill-report.json", "revocation_challenge_drill_report"),
]
subs = m["subjects"]
if len(subs) != 3:
    print("FAIL: subjects count != 3"); sys.exit(1)
for i, (p, r) in enumerate(expected):
    if subs[i]["path"] != p or subs[i]["role"] != r:
        print(f"FAIL: subject {i} mismatch (got {subs[i]!r})"); sys.exit(1)
PYEOF
echo "PASS step 6"

# === Step 7: Inline check drill report fields ===
echo "=== Step 7: Inline check drill report fields ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1] + "/revocation-challenge-drill-report.json"))
ba = r["base_acceptance"]
checks = [
    ("base_acceptance.acceptance_record_id", ba["acceptance_record_id"], "proofrail-acceptance-record-demo-001"),
    ("base_acceptance.decision_status", ba["decision_status"], "accepted"),
    ("base_acceptance.purpose_id", ba["purpose_id"], "demo_trust_boundary_review"),
    ("base_acceptance.acceptance_policy_id", ba["acceptance_policy_id"], "proofrail-demo-relying-party-policy-v0.2.8"),
    ("recommended_local_posture", r["recommended_local_posture"], "acceptance_requires_review_before_reuse"),
    ("base_acceptance_validation.validation_result", r["base_acceptance_validation"]["validation_result"], "pass"),
]
for label, actual, expected in checks:
    if actual != expected:
        print(f"FAIL: {label} = {actual!r} != {expected!r}"); sys.exit(1)
if not r["scope_limitations"]: print("FAIL: scope_limitations empty"); sys.exit(1)
if not r["non_claims"]: print("FAIL: non_claims empty"); sys.exit(1)
finding_types = {f["finding_type"] for f in r["findings"]}
for ft in ("challenge_within_window", "revocation_signal_recorded", "acceptance_revalidated"):
    if ft not in finding_types:
        print(f"FAIL: missing finding type {ft}"); sys.exit(1)
trigger_types = {t["trigger_type"] for t in r["review_triggers"]}
for tt in ("challenge_within_window", "post_acceptance_revocation_signal"):
    if tt not in trigger_types:
        print(f"FAIL: missing trigger type {tt}"); sys.exit(1)
PYEOF
echo "PASS step 7"

# === Step 8: invalid_drill_package_manifest ===
echo "=== Step 8: invalid_drill_package_manifest ==="
T8="$TMPDIR_ROOT/t08"; fresh_copy "$T8"
python3 - "$T8" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "revocation-challenge-drill-manifest.json"
m = json.loads(mp.read_text())
m["document_type"] = "proofrail.silver.not_a_real_manifest_type"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step08" "$T8" "invalid_drill_package_manifest"
echo "PASS step 8"

# === Step 9: drill_subject_file_missing ===
echo "=== Step 9: drill_subject_file_missing ==="
T9="$TMPDIR_ROOT/t09"; fresh_copy "$T9"
rm "$T9/review-events.jsonl"
expect_verifier_fail "step09" "$T9" "drill_subject_file_missing"
echo "PASS step 9"

# === Step 10: drill_subject_path_traversal (..) ===
echo "=== Step 10: drill_subject_path_traversal (..) ==="
T10="$TMPDIR_ROOT/t10"; fresh_copy "$T10"
python3 - "$T10" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "revocation-challenge-drill-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][1]["path"] = "../etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step10" "$T10" "drill_subject_path_traversal"
echo "PASS step 10"

# === Step 11: drill_subject_path_traversal (absolute) ===
echo "=== Step 11: drill_subject_path_traversal (absolute) ==="
T11="$TMPDIR_ROOT/t11"; fresh_copy "$T11"
python3 - "$T11" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "revocation-challenge-drill-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "/etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step11" "$T11" "drill_subject_path_traversal"
echo "PASS step 11"

# === Step 12: drill_subject_hash_mismatch ===
echo "=== Step 12: drill_subject_hash_mismatch ==="
T12="$TMPDIR_ROOT/t12"; fresh_copy "$T12"
# Tamper review-events.jsonl without rehashing the drill manifest subject.
python3 - "$T12" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "review-events.jsonl"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step12" "$T12" "drill_subject_hash_mismatch"
echo "PASS step 12"

# === Step 13: nested_acceptance_package_invalid ===
echo "=== Step 13: nested_acceptance_package_invalid ==="
T13="$TMPDIR_ROOT/t13"; fresh_copy "$T13"
# Tamper the nested acceptance-record bytes. The drill manifest subject is
# the nested acceptance-package-manifest, whose hash does NOT change; the
# v0.2.8 validator then fails on its own subject hash check.
python3 - "$T13" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "acceptance-package" / "acceptance-record.json"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_verifier_fail "step13" "$T13" "nested_acceptance_package_invalid"
echo "PASS step 13"

# === Step 14: invalid_review_events ===
echo "=== Step 14: invalid_review_events ==="
T14="$TMPDIR_ROOT/t14"; fresh_copy "$T14"
python3 - "$T14" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "review-events.jsonl"
p.write_text(p.read_text() + '{"unterminated: "value"\n')
PYEOF
rehash_drill_subjects "$T14" "review-events.jsonl"
expect_verifier_fail "step14" "$T14" "invalid_review_events"
echo "PASS step 14"

# === Step 15: invalid_drill_report ===
echo "=== Step 15: invalid_drill_report ==="
T15="$TMPDIR_ROOT/t15"; fresh_copy "$T15"
python3 - "$T15" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["document_type"] = "proofrail.silver.not_a_real_report_type"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T15" "revocation-challenge-drill-report.json"
expect_verifier_fail "step15" "$T15" "invalid_drill_report"
echo "PASS step 15"

# === Step 16: acceptance_record_binding_mismatch ===
echo "=== Step 16: acceptance_record_binding_mismatch ==="
T16="$TMPDIR_ROOT/t16"; fresh_copy "$T16"
python3 - "$T16" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["base_acceptance"]["purpose_id"] = "some_other_purpose"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T16" "revocation-challenge-drill-report.json"
expect_verifier_fail "step16" "$T16" "acceptance_record_binding_mismatch"
echo "PASS step 16"

# === Step 17: review_events_hash_mismatch ===
echo "=== Step 17: review_events_hash_mismatch ==="
T17="$TMPDIR_ROOT/t17"; fresh_copy "$T17"
# Append a blank line to events file. Parsing skips blank lines but the
# file sha changes; the report's events_sha256 stays stale.
python3 - "$T17" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "review-events.jsonl"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
rehash_drill_subjects "$T17" "review-events.jsonl"
expect_verifier_fail "step17" "$T17" "review_events_hash_mismatch"
echo "PASS step 17"

# === Step 18: review_event_target_mismatch ===
echo "=== Step 18: review_event_target_mismatch ==="
T18="$TMPDIR_ROOT/t18"; fresh_copy "$T18"
# Mutate non-revocation (challenge) event target. Update report's
# events_sha256 to bypass the hash check so the target check fires.
python3 - "$T18" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
ep = pkg / "review-events.jsonl"
lines = ep.read_text().splitlines()
obj = json.loads(lines[0])
assert obj["event_type"] == "challenge.received"
obj["target"]["acceptance_record_id"] = "some.other.acceptance.record"
lines[0] = json.dumps(obj, separators=(",", ":"))
ep.write_text("\n".join(lines) + "\n")
# Update report.review_events.events_sha256.
sha = "sha256:" + hashlib.sha256(ep.read_bytes()).hexdigest()
rp = pkg / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["review_events"]["events_sha256"] = sha
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T18" "review-events.jsonl" "revocation-challenge-drill-report.json"
expect_verifier_fail "step18" "$T18" "review_event_target_mismatch"
echo "PASS step 18"

# === Step 19: review_event_sequence_invalid ===
echo "=== Step 19: review_event_sequence_invalid ==="
T19="$TMPDIR_ROOT/t19"; fresh_copy "$T19"
# Swap lines 2 (revocation @06-26T00:00) and 3 (revalidation @06-26T00:05)
# so monotonicity breaks (revocation now follows revalidation).
python3 - "$T19" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
ep = pkg / "review-events.jsonl"
lines = ep.read_text().splitlines()
lines[1], lines[2] = lines[2], lines[1]
ep.write_text("\n".join(lines) + "\n")
sha = "sha256:" + hashlib.sha256(ep.read_bytes()).hexdigest()
rp = pkg / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["review_events"]["events_sha256"] = sha
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T19" "review-events.jsonl" "revocation-challenge-drill-report.json"
expect_verifier_fail "step19" "$T19" "review_event_sequence_invalid"
echo "PASS step 19"

# === Step 20: challenge_window_missing ===
echo "=== Step 20: challenge_window_missing ==="
T20="$TMPDIR_ROOT/t20"; fresh_copy "$T20"
python3 - "$T20" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["base_acceptance"]["challenge_window"] = {}
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T20" "revocation-challenge-drill-report.json"
expect_verifier_fail "step20" "$T20" "challenge_window_missing"
echo "PASS step 20"

# === Step 21: challenge_within_window_missing ===
echo "=== Step 21: challenge_within_window_missing ==="
# Per amendment: remove all challenge events AND neutralize the report's
# within-window challenge references in findings + review_triggers, so the
# verifier reaches the intended reason rather than failing earlier on
# challenge_window_classification_mismatch.
T21="$TMPDIR_ROOT/t21"; fresh_copy "$T21"
python3 - "$T21" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
ep = pkg / "review-events.jsonl"
# Strip out all challenge.received events.
kept_lines = []
for raw in ep.read_text().splitlines():
    if not raw.strip():
        continue
    obj = json.loads(raw)
    if obj["event_type"] == "challenge.received":
        continue
    kept_lines.append(raw)
ep.write_text("\n".join(kept_lines) + "\n")
sha = "sha256:" + hashlib.sha256(ep.read_bytes()).hexdigest()
rp = pkg / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
# Neutralize report.findings: drop challenge_within_window finding.
r["findings"] = [f for f in r["findings"] if f["finding_type"] != "challenge_within_window"]
# Neutralize report.review_triggers: drop challenge_within_window trigger.
r["review_triggers"] = [t for t in r["review_triggers"] if t["trigger_type"] != "challenge_within_window"]
r["review_events"]["events_sha256"] = sha
r["review_events"]["event_count"] = len(kept_lines)
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T21" "review-events.jsonl" "revocation-challenge-drill-report.json"
expect_verifier_fail "step21" "$T21" "challenge_within_window_missing"
echo "PASS step 21"

# === Step 22: challenge_window_classification_mismatch ===
echo "=== Step 22: challenge_window_classification_mismatch ==="
T22="$TMPDIR_ROOT/t22"; fresh_copy "$T22"
# Move report's base_acceptance.challenge_window.opens_at past REVIEW-EVT-001
# event_time so the finding/trigger classification fails.
python3 - "$T22" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["base_acceptance"]["challenge_window"]["opens_at"] = "2026-06-27T00:00:00Z"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T22" "revocation-challenge-drill-report.json"
expect_verifier_fail "step22" "$T22" "challenge_window_classification_mismatch"
echo "PASS step 22"

# === Step 23: revocation_signal_missing ===
echo "=== Step 23: revocation_signal_missing ==="
T23="$TMPDIR_ROOT/t23"; fresh_copy "$T23"
# Strip out all revocation.signal_received events; leave the report's
# revocation finding/trigger in place (classification only checks
# challenge_within_window types, so they don't trigger anything else
# before revocation_signal_missing fires).
python3 - "$T23" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
ep = pkg / "review-events.jsonl"
kept_lines = []
for raw in ep.read_text().splitlines():
    if not raw.strip():
        continue
    obj = json.loads(raw)
    if obj["event_type"] == "revocation.signal_received":
        continue
    kept_lines.append(raw)
ep.write_text("\n".join(kept_lines) + "\n")
sha = "sha256:" + hashlib.sha256(ep.read_bytes()).hexdigest()
rp = pkg / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["review_events"]["events_sha256"] = sha
r["review_events"]["event_count"] = len(kept_lines)
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T23" "review-events.jsonl" "revocation-challenge-drill-report.json"
expect_verifier_fail "step23" "$T23" "revocation_signal_missing"
echo "PASS step 23"

# === Step 24: revocation_signal_target_mismatch ===
echo "=== Step 24: revocation_signal_target_mismatch ==="
T24="$TMPDIR_ROOT/t24"; fresh_copy "$T24"
python3 - "$T24" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
ep = pkg / "review-events.jsonl"
lines = ep.read_text().splitlines()
# Find revocation.signal_received line and mutate target.
for i, raw in enumerate(lines):
    if not raw.strip(): continue
    obj = json.loads(raw)
    if obj["event_type"] == "revocation.signal_received":
        obj["target"]["acceptance_record_id"] = "some.other.acceptance.record"
        lines[i] = json.dumps(obj, separators=(",", ":"))
        break
ep.write_text("\n".join(lines) + "\n")
sha = "sha256:" + hashlib.sha256(ep.read_bytes()).hexdigest()
rp = pkg / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["review_events"]["events_sha256"] = sha
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T24" "review-events.jsonl" "revocation-challenge-drill-report.json"
expect_verifier_fail "step24" "$T24" "revocation_signal_target_mismatch"
echo "PASS step 24"

# === Step 25: required_finding_missing ===
echo "=== Step 25: required_finding_missing ==="
T25="$TMPDIR_ROOT/t25"; fresh_copy "$T25"
python3 - "$T25" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["findings"] = [f for f in r["findings"] if f["finding_type"] != "revocation_signal_recorded"]
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T25" "revocation-challenge-drill-report.json"
expect_verifier_fail "step25" "$T25" "required_finding_missing"
echo "PASS step 25"

# === Step 26: required_review_trigger_missing ===
echo "=== Step 26: required_review_trigger_missing ==="
T26="$TMPDIR_ROOT/t26"; fresh_copy "$T26"
python3 - "$T26" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["review_triggers"] = [t for t in r["review_triggers"]
                        if t["trigger_type"] != "post_acceptance_revocation_signal"]
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T26" "revocation-challenge-drill-report.json"
expect_verifier_fail "step26" "$T26" "required_review_trigger_missing"
echo "PASS step 26"

# === Step 27: recommended_posture_invalid ===
echo "=== Step 27: recommended_posture_invalid ==="
T27="$TMPDIR_ROOT/t27"; fresh_copy "$T27"
python3 - "$T27" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["recommended_local_posture"] = "some_bogus_posture"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T27" "revocation-challenge-drill-report.json"
expect_verifier_fail "step27" "$T27" "recommended_posture_invalid"
echo "PASS step 27"

# === Step 28: scope_limitations_missing ===
echo "=== Step 28: scope_limitations_missing ==="
T28="$TMPDIR_ROOT/t28"; fresh_copy "$T28"
python3 - "$T28" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["scope_limitations"] = []
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T28" "revocation-challenge-drill-report.json"
expect_verifier_fail "step28" "$T28" "scope_limitations_missing"
echo "PASS step 28"

# === Step 29: drill_non_claims_missing ===
echo "=== Step 29: drill_non_claims_missing ==="
T29="$TMPDIR_ROOT/t29"; fresh_copy "$T29"
python3 - "$T29" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "revocation-challenge-drill-report.json"
r = json.loads(rp.read_text())
r["non_claims"] = []
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_drill_subjects "$T29" "revocation-challenge-drill-report.json"
expect_verifier_fail "step29" "$T29" "drill_non_claims_missing"
echo "PASS step 29"

# === Step 30: external_evidence_verification_failed ===
echo "=== Step 30: external_evidence_verification_failed ==="
# Use a fresh copy of the original v0.2.7 package and tamper it. The
# pristine drill package is not modified; --evidence-package-root points
# at the tampered v0.2.7 copy.
TAMPER_V027="$TMPDIR_ROOT/tampered-v027"
rm -rf "$TAMPER_V027"
cp -R "$V027_PKG" "$TAMPER_V027"
# Append bytes to one of the v0.2.7 subjects (its event fixture copy).
EVENTS_COPY="$TAMPER_V027/source/gateway-events.jsonl"
if [ -f "$EVENTS_COPY" ]; then
    python3 - "$EVENTS_COPY" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
else
    # Fallback: tamper the composed gateway evidence report.
    python3 - "$TAMPER_V027/composed-gateway-evidence-report.json" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
fi
expect_verifier_fail "step30" "$PRISTINE" "external_evidence_verification_failed" \
    --evidence-package-root "$TAMPER_V027"
echo "PASS step 30"

# === Step 31: Runner refuses with acceptance_package_validation_failed ===
echo "=== Step 31: Runner refuses (acceptance_package_validation_failed) ==="
TAMPER_V028="$TMPDIR_ROOT/tampered-v028"
rm -rf "$TAMPER_V028"
cp -R "$V028_PKG" "$TAMPER_V028"
# Tamper the nested acceptance-record so v0.2.8 validator fails.
python3 - "$TAMPER_V028/acceptance-record.json" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
RUNNER_OUT="$TMPDIR_ROOT/runner-refused"
rm -rf "$RUNNER_OUT"
set +e
python3 "$V029_RUNNER" \
  --acceptance-manifest "$TAMPER_V028/acceptance-package-manifest.json" \
  --review-events "$REVIEW_EVENTS" \
  --generated-at "$GENERATED_AT_V029" \
  --output-dir "$RUNNER_OUT" \
  --force > "$TMPDIR_ROOT/t31.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 31: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t31.log"; exit 1
fi
if ! grep -q "acceptance_package_validation_failed" "$TMPDIR_ROOT/t31.log"; then
    echo "FAIL step 31: runner did not report acceptance_package_validation_failed"
    cat "$TMPDIR_ROOT/t31.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t31.log"; then
    echo "FAIL step 31: Python traceback leaked"
    cat "$TMPDIR_ROOT/t31.log"; exit 1
fi
if [ -d "$RUNNER_OUT" ]; then
    echo "FAIL step 31: runner left partial output directory at $RUNNER_OUT"
    ls -la "$RUNNER_OUT"; exit 1
fi
echo "PASS step 31"

# === Step 32: Runner refuses with review_fixture_insufficient ===
echo "=== Step 32: Runner refuses (review_fixture_insufficient) ==="
# Build a JSONL with only the revalidation event (no challenge, no
# revocation). Runner must refuse with review_fixture_insufficient.
INSUFFICIENT_EVENTS="$TMPDIR_ROOT/insufficient-events.jsonl"
python3 - "$REVIEW_EVENTS" "$INSUFFICIENT_EVENTS" <<'PYEOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
kept = []
for raw in open(src).read().splitlines():
    if not raw.strip(): continue
    obj = json.loads(raw)
    if obj["event_type"] == "acceptance.revalidation_performed":
        kept.append(raw)
open(dst, "w").write("\n".join(kept) + "\n")
PYEOF
RUNNER_OUT2="$TMPDIR_ROOT/runner-refused-2"
rm -rf "$RUNNER_OUT2"
set +e
python3 "$V029_RUNNER" \
  --acceptance-manifest "$V028_PKG/acceptance-package-manifest.json" \
  --review-events "$INSUFFICIENT_EVENTS" \
  --generated-at "$GENERATED_AT_V029" \
  --output-dir "$RUNNER_OUT2" \
  --force > "$TMPDIR_ROOT/t32.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL step 32: runner exit code $rc != 1"
    cat "$TMPDIR_ROOT/t32.log"; exit 1
fi
if ! grep -q "review_fixture_insufficient" "$TMPDIR_ROOT/t32.log"; then
    echo "FAIL step 32: runner did not report review_fixture_insufficient"
    cat "$TMPDIR_ROOT/t32.log"; exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t32.log"; then
    echo "FAIL step 32: Python traceback leaked"
    cat "$TMPDIR_ROOT/t32.log"; exit 1
fi
if [ -d "$RUNNER_OUT2" ]; then
    echo "FAIL step 32: runner left partial output directory at $RUNNER_OUT2"
    ls -la "$RUNNER_OUT2"; exit 1
fi
echo "PASS step 32"

# === Step 33: Scoped mutation snapshot of committed v0.2.9 source paths ===
echo "=== Step 33: Scoped mutation snapshot ==="
SNAPSHOT_AFTER="$TMPDIR_ROOT/snapshot-after.sha256"
{
  shasum -a 256 "$V029_RUNNER" "$V029_VERIFIER"
  shasum -a 256 "$REVIEW_EVENTS" "$V029_FIXTURE/README.md"
  shasum -a 256 "schemas/silver-relying-party-review-event-v0.1.0.md" \
               "schemas/silver-revocation-challenge-drill-report-v0.1.0.md" \
               "schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO006_ROOT/README.md" "$DEMO006_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_AFTER"
if ! diff -q "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" > /dev/null; then
    echo "FAIL step 33: committed v0.2.9 source paths mutated during test run"
    diff "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" || true
    exit 1
fi
echo "PASS step 33"

echo ""
echo "ALL PASS: 33 cases for ProofRail Silver v0.2.9 revocation/challenge drill"
