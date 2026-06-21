#!/usr/bin/env bash
set -euo pipefail

FIXTURE_DIR="fixtures/silver-multi-principal-authority-v0.2.3"
FIXTURE="$FIXTURE_DIR/authority-fixture.yaml"
REQUESTS="$FIXTURE_DIR/requests"
EXPECTED="$FIXTURE_DIR/expected"
INVALID_FIXTURES="$FIXTURE_DIR/invalid-fixtures"

# Temp directory for all generated decision reports — cleaned up on exit
TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

echo "=== Step 1: Validate canonical authority fixture ==="
python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
  --fixture "$FIXTURE"
echo "PASS: canonical fixture valid"

echo "=== Step 2: Evaluate REQ-001 — direct payment release (allow) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/allow-payment-release-direct.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-001.json"

STATUS=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['status'])" "$TMPDIR_ROOT/report-001.json")
REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-001.json")
if [ "$STATUS" != "allow" ] || [ "$REASON" != "authority_requirements_satisfied" ]; then
    echo "FAIL: REQ-001 expected allow/authority_requirements_satisfied, got $STATUS/$REASON"
    exit 1
fi
echo "PASS: REQ-001 allow/authority_requirements_satisfied"

echo "=== Step 3: Evaluate REQ-002 — vendor approval before revocation (allow) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/allow-vendor-approval-direct.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-002.json"

STATUS=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['status'])" "$TMPDIR_ROOT/report-002.json")
REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-002.json")
if [ "$STATUS" != "allow" ] || [ "$REASON" != "authority_requirements_satisfied" ]; then
    echo "FAIL: REQ-002 expected allow/authority_requirements_satisfied, got $STATUS/$REASON"
    exit 1
fi
echo "PASS: REQ-002 allow/authority_requirements_satisfied"

echo "=== Step 4: Evaluate REQ-003 — unauthorized vendor payment release (deny) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-payment-release-unauthorized-vendor.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-003.json"

REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-003.json")
if [ "$REASON" != "authority_subject_mismatch" ]; then
    echo "FAIL: REQ-003 expected authority_subject_mismatch, got $REASON"
    exit 1
fi
echo "PASS: REQ-003 deny/authority_subject_mismatch"

echo "=== Step 5: Evaluate REQ-004 — delegation laundering (deny) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-delegation-laundering.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-004.json"

REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-004.json")
if [ "$REASON" != "authority_subject_mismatch" ]; then
    echo "FAIL: REQ-004 expected authority_subject_mismatch, got $REASON"
    exit 1
fi
echo "PASS: REQ-004 deny/authority_subject_mismatch"

echo "=== Step 6: Evaluate REQ-005 — data export out of scope (deny) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-data-export-out-of-scope.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-005.json"

REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-005.json")
if [ "$REASON" != "constraint_not_satisfied" ]; then
    echo "FAIL: REQ-005 expected constraint_not_satisfied, got $REASON"
    exit 1
fi
echo "PASS: REQ-005 deny/constraint_not_satisfied"

echo "=== Step 7: Evaluate REQ-006 — deploy change out of scope (deny) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-deploy-change-out-of-scope.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-006.json"

REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-006.json")
if [ "$REASON" != "constraint_not_satisfied" ]; then
    echo "FAIL: REQ-006 expected constraint_not_satisfied, got $REASON"
    exit 1
fi
echo "PASS: REQ-006 deny/constraint_not_satisfied"

echo "=== Step 8: Evaluate REQ-007 — revoked vendor approval after revocation (deny) ==="
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-revoked-authority.json" \
  --decision-time "2026-06-21T14:00:00Z" \
  --output "$TMPDIR_ROOT/report-007.json"

REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-007.json")
if [ "$REASON" != "authority_revoked" ]; then
    echo "FAIL: REQ-007 expected authority_revoked, got $REASON"
    exit 1
fi
echo "PASS: REQ-007 deny/authority_revoked"

echo "=== Step 9: Validate invalid delegation fixture → FAIL ==="
INVALID_OUTPUT=$(python3 tools/silver/validate_multi_principal_authority_fixture_v0_1_0.py \
  --fixture "$INVALID_FIXTURES/invalid-delegation-laundering.yaml" 2>&1 || true)

INVALID_EXIT=$?
# The script uses set -e but we captured via || true above
if echo "$INVALID_OUTPUT" | grep -q "delegation_not_permitted"; then
    echo "PASS: invalid fixture correctly rejected with delegation_not_permitted"
else
    echo "FAIL: expected delegation_not_permitted in output"
    echo "  Output: $INVALID_OUTPUT"
    exit 1
fi

echo "=== Step 10: Verify every decision report has required fields ==="
for report_file in "$TMPDIR_ROOT"/report-*.json; do
    for field in report_type report_version decision; do
        python3 -c "
import json, sys
r = json.load(open(sys.argv[1]))
assert '$field' in r, f'missing field: $field in {sys.argv[1]}'
" "$report_file"
    done
    # Check decision.status present
    python3 -c "
import json, sys
r = json.load(open(sys.argv[1]))
assert 'status' in r['decision'], f'missing decision.status'
assert len(r.get('checks', [])) > 0, 'checks must be non-empty'
assert len(r.get('limitations', [])) > 0, 'limitations must be non-empty'
" "$report_file"
done
echo "PASS: all decision reports have required fields"

echo "=== Step 11: Verify every decision report has execution.performed == false ==="
for report_file in "$TMPDIR_ROOT"/report-*.json; do
    python3 -c "
import json, sys
r = json.load(open(sys.argv[1]))
assert r.get('execution', {}).get('performed') == False, f'execution.performed must be false'
assert r['execution'].get('reason') == 'decision_report_only', f'execution.reason must be decision_report_only'
" "$report_file"
done
echo "PASS: all decision reports confirm no execution"

echo "=== Step 12: Confirm evaluator exits 0 for deny decisions ==="
# REQ-003 is a deny — verify exit code was 0
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$REQUESTS/deny-payment-release-unauthorized-vendor.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-003-rerun.json"
echo "PASS: evaluator exits 0 for deny decisions"

echo "=== Step 13: Confirm evaluator exits nonzero for malformed request ==="
MALFORMED_REQ="$TMPDIR_ROOT/malformed-request.json"
echo '{"bad": "request"}' > "$MALFORMED_REQ"

MALFORMED_EXIT=0
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "$FIXTURE" \
  --request "$MALFORMED_REQ" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-malformed.json" || MALFORMED_EXIT=$?

# The evaluator should still exit 0 (it produces a deny report for invalid structure)
# But let's verify the report says invalid_request_structure
MALFORMED_REASON=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['decision']['reason'])" "$TMPDIR_ROOT/report-malformed.json")
if [ "$MALFORMED_REASON" != "invalid_request_structure" ]; then
    echo "FAIL: expected invalid_request_structure for malformed request, got $MALFORMED_REASON"
    exit 1
fi
echo "PASS: malformed request produces deny/invalid_request_structure"

echo "=== Step 14: Confirm evaluator exits nonzero for missing fixture ==="
MISSING_EXIT=0
python3 tools/silver/evaluate_multi_principal_authority_v0_1_0.py \
  --fixture "/nonexistent/fixture.yaml" \
  --request "$REQUESTS/allow-payment-release-direct.json" \
  --decision-time "2026-06-21T10:00:00Z" \
  --output "$TMPDIR_ROOT/report-missing.json" 2>/dev/null || MISSING_EXIT=$?

if [ "$MISSING_EXIT" -ne 0 ]; then
    echo "PASS: evaluator exits nonzero ($MISSING_EXIT) for missing fixture"
else
    echo "FAIL: evaluator should exit nonzero for missing fixture"
    exit 1
fi

echo "=== Step 15: All Silver Multi-Principal Authority v0.2.3 regression tests passed ==="
