#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.4 multi-agent attack harness.
#
# Covers:
#  - canonical fixture validation
#  - v0.2.3 authority regression (forwarded)
#  - harness run into a temporary output directory
#  - evidence verifier PASS on untampered outputs
#  - per-event outcome assertions
#  - every decision report has execution.performed == false
#  - run report has execution.protected_actions_performed == false
#  - tamper test: modify a decision report → subject_hash_mismatch
#  - tamper test: modify the transcript → subject_hash_mismatch
#  - tamper test: remove a subject file → subject_file_missing
#  - tamper test: rewrite manifest subject path with '..' or absolute → subject_path_traversal
#  - malformed harness script → nonzero exit
#  - no committed file outside tmp output dir was modified by the harness
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SCRIPT="fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml"
FIXTURE="fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml"

TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

# Snapshot the v0.2.4 paths the harness should NOT modify.
SNAPSHOT="$TMPDIR_ROOT/snapshot"
mkdir -p "$SNAPSHOT"
cp -R fixtures/silver-multi-agent-attack-harness-v0.2.4 "$SNAPSHOT/fixture"
cp -R fixtures/silver-multi-principal-authority-v0.2.3 "$SNAPSHOT/authority"
cp tools/silver/run_multi_agent_attack_harness_v0_1_0.py "$SNAPSHOT/runner.py"
cp tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py "$SNAPSHOT/verifier.py"

OUT="$TMPDIR_ROOT/harness-output"
TAMPER_OUT="$TMPDIR_ROOT/tamper-output"

echo "=== Step 1: Validate v0.2.3 authority fixture ==="
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py --fixture "$FIXTURE"
echo "PASS: v0.2.3 authority fixture valid"

echo "=== Step 2: Run v0.2.3 authority regression test ==="
bash tests/test_silver_multi_principal_authority_v0_2_3.sh > "$TMPDIR_ROOT/v0_2_3.log" 2>&1
echo "PASS: v0.2.3 authority regression test"

echo "=== Step 3: Run v0.2.4 harness into a temporary output directory ==="
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
  --script "$SCRIPT" \
  --authority-fixture "$FIXTURE" \
  --output-dir "$OUT" \
  --force
echo "PASS: harness completed"

echo "=== Step 4: Verify untampered harness evidence manifest ==="
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$OUT/harness-evidence-manifest.json"
echo "PASS: evidence verifier accepted untampered manifest"

echo "=== Step 5: Transcript exists and has one record per script event ==="
EVENT_COUNT=$(python3 -c "import yaml; print(len(yaml.safe_load(open('$SCRIPT'))['events']))")
TX_LINES=$(grep -c '"event_id"' "$OUT/transcript.jsonl" || echo 0)
if [ "$EVENT_COUNT" != "$TX_LINES" ]; then
    echo "FAIL: expected $EVENT_COUNT transcript lines, got $TX_LINES"
    exit 1
fi
echo "PASS: transcript has $TX_LINES records"

echo "=== Step 6-14: Per-event outcome assertions ==="
python3 - <<'PY' "$OUT/harness-run-report.json"
import json, sys
report = json.load(open(sys.argv[1]))
results = {e['event_id']: e for e in report['event_results']}

cases = [
    ("EVT-001-harmless-message", "message_delivered", None, None, None),
    ("EVT-002-allowed-payment-release", "action_allowed", "allow", "authority_requirements_satisfied", None),
    ("EVT-003-allowed-vendor-approval", "action_allowed", "allow", "authority_requirements_satisfied", None),
    ("EVT-004-delegation-laundering", "action_denied", "deny", "authority_subject_mismatch", None),
    ("EVT-005-bypass-payment-release", "bypass_blocked", None, None, "bypass_attempt_detected"),
    ("EVT-006-data-export-out-of-scope", "action_denied", "deny", "constraint_not_satisfied", None),
    ("EVT-007-deploy-change-out-of-scope", "action_denied", "deny", "constraint_not_satisfied", None),
    ("EVT-008-revocation-marker", "revocation_marked", None, None, None),
    ("EVT-009-vendor-approval-after-revocation", "action_denied", "deny", "authority_revoked", None),
]
failed = False
for ev_id, outcome, status, reason, harness_reason in cases:
    if ev_id not in results:
        print(f"FAIL: event {ev_id} missing from run report", file=sys.stderr)
        failed = True
        continue
    a = results[ev_id]['actual']
    if a['harness_outcome'] != outcome:
        print(f"FAIL: {ev_id} expected outcome={outcome} got {a['harness_outcome']}", file=sys.stderr); failed = True
    if a['decision_status'] != status:
        print(f"FAIL: {ev_id} expected status={status} got {a['decision_status']}", file=sys.stderr); failed = True
    if a['decision_reason'] != reason:
        print(f"FAIL: {ev_id} expected reason={reason} got {a['decision_reason']}", file=sys.stderr); failed = True
    if a['harness_reason'] != harness_reason:
        print(f"FAIL: {ev_id} expected harness_reason={harness_reason} got {a['harness_reason']}", file=sys.stderr); failed = True
if failed:
    sys.exit(1)
print("PASS: all per-event outcomes match")
PY

echo "=== Step 15: Every decision report has execution.performed == false ==="
python3 - <<'PY' "$OUT/authority-decision-reports"
import json, sys, pathlib
root = pathlib.Path(sys.argv[1])
for p in sorted(root.glob("*.json")):
    r = json.load(open(p))
    if r.get("execution", {}).get("performed") is not False:
        print(f"FAIL: {p.name} execution.performed != false", file=sys.stderr); sys.exit(1)
print(f"PASS: all decision reports have execution.performed == false")
PY

echo "=== Step 16: Run report has execution.protected_actions_performed == false ==="
python3 -c "
import json,sys
r=json.load(open('$OUT/harness-run-report.json'))
assert r['execution']['protected_actions_performed'] is False, r['execution']
print('PASS: run report execution.protected_actions_performed == false')
"

echo "=== Step 17: Tamper test — modify a decision report ==="
cp -R "$OUT" "$TAMPER_OUT"
TARGET="$TAMPER_OUT/authority-decision-reports/EVT-002-allowed-payment-release.json"
python3 -c "
import json
d = json.load(open('$TARGET'))
d['decision']['reason'] = 'tampered_value'
open('$TARGET','w').write(json.dumps(d, indent=2, sort_keys=True) + '\n')
"
set +e
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$TAMPER_OUT/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t17.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ] || ! grep -q "subject_hash_mismatch" "$TMPDIR_ROOT/t17.log"; then
    echo "FAIL: expected subject_hash_mismatch on decision report tamper, got rc=$RC"
    cat "$TMPDIR_ROOT/t17.log"
    exit 1
fi
rm -rf "$TAMPER_OUT"
echo "PASS: decision-report tamper detected (subject_hash_mismatch)"

echo "=== Step 18: Tamper test — modify the transcript ==="
cp -R "$OUT" "$TAMPER_OUT"
printf '\n{"tampered":true}\n' >> "$TAMPER_OUT/transcript.jsonl"
set +e
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$TAMPER_OUT/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t18.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ] || ! grep -q "subject_hash_mismatch" "$TMPDIR_ROOT/t18.log"; then
    echo "FAIL: expected subject_hash_mismatch on transcript tamper, got rc=$RC"
    cat "$TMPDIR_ROOT/t18.log"
    exit 1
fi
rm -rf "$TAMPER_OUT"
echo "PASS: transcript tamper detected (subject_hash_mismatch)"

echo "=== Step 19: Tamper test — remove a subject file ==="
cp -R "$OUT" "$TAMPER_OUT"
rm "$TAMPER_OUT/authority-decision-reports/EVT-004-delegation-laundering.json"
set +e
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$TAMPER_OUT/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t19.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ] || ! grep -q "subject_file_missing" "$TMPDIR_ROOT/t19.log"; then
    echo "FAIL: expected subject_file_missing on removed subject, got rc=$RC"
    cat "$TMPDIR_ROOT/t19.log"
    exit 1
fi
rm -rf "$TAMPER_OUT"
echo "PASS: missing-subject detected (subject_file_missing)"

echo "=== Step 20: Tamper test — rewrite manifest subject path with '..' or absolute ==="
# Case A: '..' component
cp -R "$OUT" "$TAMPER_OUT"
python3 -c "
import json
m = json.load(open('$TAMPER_OUT/harness-evidence-manifest.json'))
m['subjects'][0]['path'] = '../' + m['subjects'][0]['path']
open('$TAMPER_OUT/harness-evidence-manifest.json','w').write(json.dumps(m, indent=2, sort_keys=True) + '\n')
"
set +e
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$TAMPER_OUT/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t20a.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ] || ! grep -q "subject_path_traversal" "$TMPDIR_ROOT/t20a.log"; then
    echo "FAIL: expected subject_path_traversal on '..' path tamper, got rc=$RC"
    cat "$TMPDIR_ROOT/t20a.log"
    exit 1
fi
rm -rf "$TAMPER_OUT"
echo "PASS: '..' path tamper detected (subject_path_traversal)"

# Case B: absolute path
cp -R "$OUT" "$TAMPER_OUT"
python3 -c "
import json
m = json.load(open('$TAMPER_OUT/harness-evidence-manifest.json'))
m['subjects'][0]['path'] = '/etc/passwd'
open('$TAMPER_OUT/harness-evidence-manifest.json','w').write(json.dumps(m, indent=2, sort_keys=True) + '\n')
"
set +e
python3 tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py --manifest "$TAMPER_OUT/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t20b.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ] || ! grep -q "subject_path_traversal" "$TMPDIR_ROOT/t20b.log"; then
    echo "FAIL: expected subject_path_traversal on absolute path tamper, got rc=$RC"
    cat "$TMPDIR_ROOT/t20b.log"
    exit 1
fi
rm -rf "$TAMPER_OUT"
echo "PASS: absolute path tamper detected (subject_path_traversal)"

echo "=== Step 21: Malformed harness script exits nonzero ==="
BAD_SCRIPT="$TMPDIR_ROOT/bad-script.yaml"
cat > "$BAD_SCRIPT" <<'YAML'
script_type: proofrail.silver.multi_agent_harness_script
script_version: v0.1.0
script_id: bad-script
authority_fixture: ignored
description: malformed - duplicate event_id
events:
  - event_id: DUP-001
    event_type: agent_message
    timestamp: "2026-06-21T10:00:00Z"
    from_principal_id: buyerorg.agent
    to_principal_id: vendororg.agent
    description: first
    protected_action:
      attempted: false
    expected:
      harness_outcome: message_delivered
  - event_id: DUP-001
    event_type: agent_message
    timestamp: "2026-06-21T10:01:00Z"
    from_principal_id: buyerorg.agent
    to_principal_id: vendororg.agent
    description: duplicate
    protected_action:
      attempted: false
    expected:
      harness_outcome: message_delivered
limitations:
  - test
YAML
set +e
python3 tools/silver/run_multi_agent_attack_harness_v0_1_0.py \
  --script "$BAD_SCRIPT" \
  --authority-fixture "$FIXTURE" \
  --output-dir "$TMPDIR_ROOT/bad-output" \
  --force > "$TMPDIR_ROOT/t21.log" 2>&1
RC=$?
set -e
if [ "$RC" -eq 0 ]; then
    echo "FAIL: expected nonzero exit for malformed script"
    cat "$TMPDIR_ROOT/t21.log"
    exit 1
fi
if ! grep -q "invalid_harness_script" "$TMPDIR_ROOT/t21.log"; then
    echo "FAIL: expected invalid_harness_script reason"
    cat "$TMPDIR_ROOT/t21.log"
    exit 1
fi
echo "PASS: malformed script rejected with invalid_harness_script"

echo "=== Step 22: Confirm harness did not modify committed v0.2.4 paths ==="
diff -r "$SNAPSHOT/fixture" fixtures/silver-multi-agent-attack-harness-v0.2.4 > "$TMPDIR_ROOT/diff_fixture.log" 2>&1 || true
if [ -s "$TMPDIR_ROOT/diff_fixture.log" ]; then
    echo "FAIL: harness modified files under fixtures/silver-multi-agent-attack-harness-v0.2.4/"
    cat "$TMPDIR_ROOT/diff_fixture.log"
    exit 1
fi
diff -r "$SNAPSHOT/authority" fixtures/silver-multi-principal-authority-v0.2.3 > "$TMPDIR_ROOT/diff_auth.log" 2>&1 || true
if [ -s "$TMPDIR_ROOT/diff_auth.log" ]; then
    echo "FAIL: harness modified files under fixtures/silver-multi-principal-authority-v0.2.3/"
    cat "$TMPDIR_ROOT/diff_auth.log"
    exit 1
fi
if ! cmp -s "$SNAPSHOT/runner.py" tools/silver/run_multi_agent_attack_harness_v0_1_0.py; then
    echo "FAIL: harness runner source changed during test"; exit 1
fi
if ! cmp -s "$SNAPSHOT/verifier.py" tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py; then
    echo "FAIL: harness verifier source changed during test"; exit 1
fi
echo "PASS: v0.2.4 committed paths unchanged by harness execution"

echo ""
echo "=== All steps passed ==="
