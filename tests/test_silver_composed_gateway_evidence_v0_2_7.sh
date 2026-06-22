#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.7 composed gateway evidence demo.
#
# Covers 28 cases (exercising all 18 stable failure reasons in the v0.2.7 verifier):
#   1.  v0.2.6 simulated gateway adapter descriptor validates.
#   2.  Composer runs into a temporary output directory.
#   3.  Verifier accepts the untampered composed package.
#   4.  Composed report contains all 10 required claim IDs with status 'pass'.
#   5.  Adapter copy has trust_boundary.source_is_trust_authority == false.
#   6.  Source events include all required scenario_event_id values.
#   7.  Manifest subject hashes are valid (re-checked explicitly).
#   8.  Tamper JSONL without rehash -> composed_subject_hash_mismatch.
#   9.  Tamper JSONL with rehash so EVT-002 decision becomes deny
#       -> gateway_decision_mismatch or normalized_claim_failed.
#   10. Tamper adapter so decision_event capability becomes not_provided,
#       then rehash -> adapter_invalid.
#   11. Tamper source event protected_action_id to an unsupported but
#       valid-looking ID, then rehash -> gateway_protected_action_mismatch.
#   12. Tamper bypass event so bypass_detected == false, then rehash
#       -> gateway_bypass_mismatch.
#   13. Tamper revocation event so revocation_checked == false, then rehash
#       -> gateway_revocation_mismatch.
#   14. Remove a required source event, then rehash -> source_event_missing.
#   15. Duplicate a required source event, then rehash -> source_event_duplicate.
#   16. Rewrite manifest subject path to contain '..' -> composed_subject_path_traversal.
#   17. Rewrite manifest subject path to be absolute -> composed_subject_path_traversal.
#   18. Tamper report claim status to 'fail', then rehash -> normalized_claim_failed.
#   19. Tamper report evidence ref to contain '..', then rehash
#       -> normalized_evidence_ref_invalid.
#   20. Tamper report evidence ref to point at wrong-but-valid event, then rehash
#       -> normalized_evidence_ref_invalid (or normalized_claim_failed).
#   21. Tamper execution flag to true in a source event, then rehash
#       -> execution_violation.
#   22. Malformed gateway-events JSONL line, then rehash -> source_event_invalid
#       (no Python traceback).
#   23. Mutate manifest composition.source_type to non-'gateway' value
#       -> invalid_composed_gateway_manifest.
#   24. Delete a referenced subject file (source/gateway-events.jsonl) without
#       touching the manifest -> composed_subject_file_missing.
#   25. Mutate adapter source.source_type to a v0.2.6-supported non-'gateway'
#       value ('policy_engine'), then rehash -> adapter_not_gateway_source.
#   26. Mutate report.document_type to an invalid value, then rehash
#       -> normalized_report_invalid.
#   27. Remove a required claim_id from report.claims, then rehash
#       -> normalized_claim_missing.
#   28. Scoped mutation check: committed v0.2.7 schemas, validator, composer,
#       verifier, fixture, walkthrough, and demo README are unchanged.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

COMPOSER="tools/silver/compose_gateway_evidence_demo_v0_1_0.py"
VERIFIER="tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"
ADAPTER_VALIDATOR="tools/silver/validate_evidence_source_adapter_v0_1_0.py"
DEMO_ROOT="demos/silver-demo-004-composed-gateway-evidence"
ADAPTER="examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json"
FIXTURE_ROOT="fixtures/silver-composed-gateway-evidence-v0.2.7"
EVENTS="$FIXTURE_ROOT/gateway-events.jsonl"

TMPDIR_ROOT="$(mktemp -d -t proofrail-v027-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

PRISTINE="$TMPDIR_ROOT/pristine"
GENERATED_AT="2026-06-22T00:00:00Z"

# Snapshot committed v0.2.7-owned files for Step 28.
SNAPSHOT_BEFORE="$TMPDIR_ROOT/snapshot-before.sha256"
{
  shasum -a 256 "$COMPOSER" "$VERIFIER"
  shasum -a 256 "$ADAPTER_VALIDATOR" "$ADAPTER"
  shasum -a 256 "$EVENTS" "$FIXTURE_ROOT/README.md"
  shasum -a 256 "$DEMO_ROOT/README.md" "$DEMO_ROOT/demo-walkthrough.md"
  shasum -a 256 "schemas/silver-simulated-gateway-evidence-event-v0.1.0.md" \
               "schemas/silver-composed-gateway-evidence-report-v0.1.0.md" \
               "schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md"
  shasum -a 256 "docs/silver/silver-composed-gateway-evidence-demo-v0.2.7.md"
} > "$SNAPSHOT_BEFORE"

# Helper: copy the pristine package into a fresh tamper directory.
fresh_copy() {
    local dest="$1"
    rm -rf "$dest"
    cp -R "$PRISTINE" "$dest"
}

# Helper: recompute sha256 + size for a list of subject paths inside a
# package's composed-gateway-evidence-manifest.json. Required after
# semantic edits so the package verifier reaches semantic validation
# instead of short-circuiting on composed_subject_hash_mismatch.
rehash_subjects_in_manifest() {
    local pkg_dir="$1"
    shift
    python3 - "$pkg_dir" "$@" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
targets = set(sys.argv[2:])
mpath = pkg / "composed-gateway-evidence-manifest.json"
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
# Accepts multiple acceptable reasons separated by '|'.
expect_verifier_fail() {
    local label="$1"
    local pkg_dir="$2"
    local accepted_reasons="$3"
    local logf
    logf="$TMPDIR_ROOT/$label.log"
    set +e
    python3 "$VERIFIER" --manifest "$pkg_dir/composed-gateway-evidence-manifest.json" \
        >"$logf" 2>&1
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

# === Step 1: Adapter descriptor validates ===
echo "=== Step 1: v0.2.6 simulated gateway adapter descriptor validates ==="
python3 "$ADAPTER_VALIDATOR" --adapter "$ADAPTER" > "$TMPDIR_ROOT/t01.log" 2>&1
echo "PASS step 1: adapter descriptor valid"

# === Step 2: Composer runs ===
echo "=== Step 2: Composer runs into temporary output directory ==="
python3 "$COMPOSER" \
  --demo-root "$DEMO_ROOT" \
  --adapter "$ADAPTER" \
  --gateway-events "$EVENTS" \
  --output-dir "$PRISTINE" \
  --generated-at "$GENERATED_AT" \
  --force > "$TMPDIR_ROOT/t02.log" 2>&1
if [ ! -f "$PRISTINE/composed-gateway-evidence-manifest.json" ]; then
    echo "FAIL: composer did not produce manifest"
    cat "$TMPDIR_ROOT/t02.log"
    exit 1
fi
echo "PASS step 2: composer produced manifest"

# === Step 3: Verifier accepts untampered package ===
echo "=== Step 3: Verifier accepts untampered composed package ==="
python3 "$VERIFIER" --manifest "$PRISTINE/composed-gateway-evidence-manifest.json" \
    > "$TMPDIR_ROOT/t03.log" 2>&1
echo "PASS step 3: untampered composed package verified"

# === Step 4: All 10 required claim IDs with status pass ===
echo "=== Step 4: Composed report has all 10 required claim IDs (status pass) ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
required = [
    "gateway_source_described_by_adapter",
    "gateway_source_not_trust_authority",
    "gateway_events_normalized",
    "protected_actions_require_scoped_authority",
    "unauthorized_delegation_fails",
    "bypass_attempts_observed_or_blocked",
    "revoked_authority_fails",
    "out_of_scope_actions_fail",
    "source_evidence_hash_verifiable",
    "no_protected_actions_executed",
]
r = json.load(open(sys.argv[1] + "/composed-gateway-evidence-report.json"))
by_id = {c["claim_id"]: c for c in r["claims"]}
for cid in required:
    if cid not in by_id:
        print(f"FAIL: missing claim {cid}")
        sys.exit(1)
    if by_id[cid]["status"] != "pass":
        print(f"FAIL: claim {cid} status != pass")
        sys.exit(1)
PYEOF
echo "PASS step 4: all required claim IDs present with status pass"

# === Step 5: Adapter copy source_is_trust_authority == false ===
echo "=== Step 5: Adapter copy source_is_trust_authority == false ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
a = json.load(open(sys.argv[1] + "/adapter/gateway-mcp-simulated-v0.2.6.json"))
if a["trust_boundary"]["source_is_trust_authority"] is not False:
    print("FAIL: adapter copy source_is_trust_authority != false")
    sys.exit(1)
PYEOF
echo "PASS step 5: adapter copy source_is_trust_authority == false"

# === Step 6: Source events include all required scenario_event_id values ===
echo "=== Step 6: Source events include all required scenario_event_id values ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
required = [
    "EVT-001-harmless-message",
    "EVT-002-payment-release-direct",
    "EVT-003-vendor-approval-direct",
    "EVT-004-delegation-laundering",
    "EVT-005-bypass-payment-release",
    "EVT-006-data-export-out-of-scope",
    "EVT-007-deploy-change-out-of-scope",
    "EVT-008-revocation-marker",
    "EVT-009-vendor-approval-after-revocation",
]
ids = []
with open(sys.argv[1] + "/source/gateway-events.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        ids.append(json.loads(line)["scenario_event_id"])
for r in required:
    if r not in ids:
        print(f"FAIL: missing scenario {r}")
        sys.exit(1)
PYEOF
echo "PASS step 6: all required scenario_event_id values present"

# === Step 7: Manifest subject hashes are valid (explicit recheck) ===
echo "=== Step 7: Manifest subject hashes are valid ==="
python3 - "$PRISTINE" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
m = json.loads((root / "composed-gateway-evidence-manifest.json").read_text())
for s in m["subjects"]:
    actual = hashlib.sha256((root / s["path"]).read_bytes()).hexdigest()
    if s["sha256"] != f"sha256:{actual}":
        print(f"FAIL: hash mismatch for {s['path']}")
        sys.exit(1)
PYEOF
echo "PASS step 7: manifest subject hashes are valid"

# === Step 8: Tamper JSONL without rehash -> composed_subject_hash_mismatch ===
echo "=== Step 8: Tamper source JSONL without rehash ==="
T8="$TMPDIR_ROOT/t08"
fresh_copy "$T8"
printf '\n' >> "$T8/source/gateway-events.jsonl"  # append nothing visible
# Actually mutate one byte.
python3 - "$T8" <<'PYEOF'
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
data = p.read_bytes()
p.write_bytes(data + b"\n")
PYEOF
expect_verifier_fail "step08" "$T8" "composed_subject_hash_mismatch"
echo "PASS step 8: composed_subject_hash_mismatch"

# === Step 9: Tamper JSONL with rehash so EVT-002 becomes deny ===
echo "=== Step 9: Tamper JSONL so EVT-002 decision becomes deny (with rehash) ==="
T9="$TMPDIR_ROOT/t09"
fresh_copy "$T9"
python3 - "$T9" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = p.read_text().splitlines()
new_lines = []
for ln in lines:
    if not ln.strip():
        continue
    obj = json.loads(ln)
    if obj.get("scenario_event_id") == "EVT-002-payment-release-direct":
        obj["decision"] = "deny"
    new_lines.append(json.dumps(obj))
p.write_text("\n".join(new_lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T9" "source/gateway-events.jsonl"
expect_verifier_fail "step09" "$T9" "normalized_claim_failed|gateway_decision_mismatch"
echo "PASS step 9: normalized_claim_failed or gateway_decision_mismatch"

# === Step 10: Tamper adapter decision_event capability to not_provided ===
echo "=== Step 10: Tamper adapter decision_event -> not_provided (with rehash) ==="
T10="$TMPDIR_ROOT/t10"
fresh_copy "$T10"
python3 - "$T10" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "adapter/gateway-mcp-simulated-v0.2.6.json"
a = json.loads(p.read_text())
a["evidence_capabilities"]["decision_event"] = {
    "status": "not_provided",
    "limitation": "decision_event disabled for test",
}
p.write_text(json.dumps(a, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T10" "adapter/gateway-mcp-simulated-v0.2.6.json"
expect_verifier_fail "step10" "$T10" "adapter_invalid"
echo "PASS step 10: adapter_invalid"

# === Step 11: Tamper source event protected_action_id to unsupported ===
echo "=== Step 11: Tamper source event protected_action_id to unsupported ID (with rehash) ==="
T11="$TMPDIR_ROOT/t11"
fresh_copy "$T11"
python3 - "$T11" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = []
for ln in p.read_text().splitlines():
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-002-payment-release-direct":
        o["protected_action_id"] = "admin.rotate_secret"
    lines.append(json.dumps(o))
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T11" "source/gateway-events.jsonl"
expect_verifier_fail "step11" "$T11" "gateway_protected_action_mismatch"
echo "PASS step 11: gateway_protected_action_mismatch"

# === Step 12: Tamper bypass event bypass_detected -> false ===
echo "=== Step 12: Tamper EVT-005 bypass_detected -> false (with rehash) ==="
T12="$TMPDIR_ROOT/t12"
fresh_copy "$T12"
python3 - "$T12" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = []
for ln in p.read_text().splitlines():
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-005-bypass-payment-release":
        o["bypass_detected"] = False
    lines.append(json.dumps(o))
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T12" "source/gateway-events.jsonl"
expect_verifier_fail "step12" "$T12" "gateway_bypass_mismatch"
echo "PASS step 12: gateway_bypass_mismatch"

# === Step 13: Tamper revocation event revocation_checked -> false ===
echo "=== Step 13: Tamper EVT-008 revocation_checked -> false (with rehash) ==="
T13="$TMPDIR_ROOT/t13"
fresh_copy "$T13"
python3 - "$T13" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = []
for ln in p.read_text().splitlines():
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-008-revocation-marker":
        o["revocation_checked"] = False
    lines.append(json.dumps(o))
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T13" "source/gateway-events.jsonl"
expect_verifier_fail "step13" "$T13" "gateway_revocation_mismatch"
echo "PASS step 13: gateway_revocation_mismatch"

# === Step 14: Remove a required source event ===
echo "=== Step 14: Remove EVT-005 source event (with rehash) ==="
T14="$TMPDIR_ROOT/t14"
fresh_copy "$T14"
python3 - "$T14" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = []
for ln in p.read_text().splitlines():
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-005-bypass-payment-release":
        continue
    lines.append(json.dumps(o))
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T14" "source/gateway-events.jsonl"
expect_verifier_fail "step14" "$T14" "source_event_missing"
echo "PASS step 14: source_event_missing"

# === Step 15: Duplicate a required source event ===
echo "=== Step 15: Duplicate EVT-002 source event (with rehash) ==="
T15="$TMPDIR_ROOT/t15"
fresh_copy "$T15"
python3 - "$T15" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = p.read_text().splitlines()
dup = None
for ln in lines:
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-002-payment-release-direct":
        dup = ln
        break
lines.append(dup)
p.write_text("\n".join([l for l in lines if l.strip()]) + "\n")
PYEOF
rehash_subjects_in_manifest "$T15" "source/gateway-events.jsonl"
expect_verifier_fail "step15" "$T15" "source_event_duplicate"
echo "PASS step 15: source_event_duplicate"

# === Step 16: Manifest subject path with '..' ===
echo "=== Step 16: Manifest subject path contains '..' ==="
T16="$TMPDIR_ROOT/t16"
fresh_copy "$T16"
python3 - "$T16" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "composed-gateway-evidence-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][3]["path"] = "../etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step16" "$T16" "composed_subject_path_traversal"
echo "PASS step 16: composed_subject_path_traversal (..)"

# === Step 17: Manifest subject path absolute ===
echo "=== Step 17: Manifest subject path is absolute ==="
T17="$TMPDIR_ROOT/t17"
fresh_copy "$T17"
python3 - "$T17" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "composed-gateway-evidence-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "/etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step17" "$T17" "composed_subject_path_traversal"
echo "PASS step 17: composed_subject_path_traversal (absolute)"

# === Step 18: Tamper claim status -> fail ===
echo "=== Step 18: Tamper a report claim status to 'fail' (with rehash) ==="
T18="$TMPDIR_ROOT/t18"
fresh_copy "$T18"
python3 - "$T18" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "composed-gateway-evidence-report.json"
r = json.loads(rp.read_text())
for c in r["claims"]:
    if c["claim_id"] == "unauthorized_delegation_fails":
        c["status"] = "fail"
        break
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T18" "composed-gateway-evidence-report.json"
expect_verifier_fail "step18" "$T18" "normalized_claim_failed"
echo "PASS step 18: normalized_claim_failed"

# === Step 19: Tamper evidence ref to contain '..' ===
echo "=== Step 19: Tamper report evidence ref to contain '..' (with rehash) ==="
T19="$TMPDIR_ROOT/t19"
fresh_copy "$T19"
python3 - "$T19" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "composed-gateway-evidence-report.json"
r = json.loads(rp.read_text())
for c in r["claims"]:
    if c["claim_id"] == "bypass_attempts_observed_or_blocked":
        c["evidence_refs"][0]["artifact"] = "../etc/passwd"
        break
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T19" "composed-gateway-evidence-report.json"
expect_verifier_fail "step19" "$T19" "normalized_evidence_ref_invalid"
echo "PASS step 19: normalized_evidence_ref_invalid (..)"

# === Step 20: Wrong-but-valid evidence ref ===
echo "=== Step 20: Bypass claim references EVT-001 instead of EVT-005 (with rehash) ==="
T20="$TMPDIR_ROOT/t20"
fresh_copy "$T20"
python3 - "$T20" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "composed-gateway-evidence-report.json"
r = json.loads(rp.read_text())
for c in r["claims"]:
    if c["claim_id"] == "bypass_attempts_observed_or_blocked":
        c["evidence_refs"] = [{
            "artifact": "source/gateway-events.jsonl",
            "source_event_id": "GW-EVT-001-harmless-message",
            "scenario_event_id": "EVT-001-harmless-message",
        }]
        break
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T20" "composed-gateway-evidence-report.json"
expect_verifier_fail "step20" "$T20" "normalized_evidence_ref_invalid|normalized_claim_failed"
echo "PASS step 20: normalized_evidence_ref_invalid or normalized_claim_failed"

# === Step 21: execution.performed = true in a source event ===
echo "=== Step 21: Source event execution.performed = true (with rehash) ==="
T21="$TMPDIR_ROOT/t21"
fresh_copy "$T21"
python3 - "$T21" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
lines = []
for ln in p.read_text().splitlines():
    if not ln.strip():
        continue
    o = json.loads(ln)
    if o.get("scenario_event_id") == "EVT-002-payment-release-direct":
        o["execution"]["performed"] = True
    lines.append(json.dumps(o))
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T21" "source/gateway-events.jsonl"
expect_verifier_fail "step21" "$T21" "execution_violation"
echo "PASS step 21: execution_violation"

# === Step 22: Malformed JSONL line ===
echo "=== Step 22: Malformed JSONL line (with rehash) ==="
T22="$TMPDIR_ROOT/t22"
fresh_copy "$T22"
python3 - "$T22" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
data = p.read_text()
# Replace the first '{' of the first line with garbage so json.loads fails.
lines = data.splitlines()
lines[0] = '{"unterminated: "value"'
p.write_text("\n".join(lines) + "\n")
PYEOF
rehash_subjects_in_manifest "$T22" "source/gateway-events.jsonl"
expect_verifier_fail "step22" "$T22" "source_event_invalid"
echo "PASS step 22: source_event_invalid (no Python traceback)"

# === Step 23: Manifest composition.source_type != 'gateway' ===
echo "=== Step 23: Manifest composition.source_type != 'gateway' ==="
T23="$TMPDIR_ROOT/t23"
fresh_copy "$T23"
python3 - "$T23" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "composed-gateway-evidence-manifest.json"
m = json.loads(mp.read_text())
m["composition"]["source_type"] = "policy_engine"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_verifier_fail "step23" "$T23" "invalid_composed_gateway_manifest"
echo "PASS step 23: invalid_composed_gateway_manifest"

# === Step 24: Subject file missing ===
echo "=== Step 24: Referenced subject file missing (no manifest edit) ==="
T24="$TMPDIR_ROOT/t24"
fresh_copy "$T24"
rm "$T24/source/gateway-events.jsonl"
expect_verifier_fail "step24" "$T24" "composed_subject_file_missing"
echo "PASS step 24: composed_subject_file_missing"

# === Step 25: Adapter source.source_type != 'gateway' (v0.2.6 still valid) ===
echo "=== Step 25: Adapter source.source_type -> 'policy_engine' (with rehash) ==="
T25="$TMPDIR_ROOT/t25"
fresh_copy "$T25"
python3 - "$T25" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "adapter/gateway-mcp-simulated-v0.2.6.json"
a = json.loads(p.read_text())
a["source"]["source_type"] = "policy_engine"
p.write_text(json.dumps(a, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T25" "adapter/gateway-mcp-simulated-v0.2.6.json"
expect_verifier_fail "step25" "$T25" "adapter_not_gateway_source"
echo "PASS step 25: adapter_not_gateway_source"

# === Step 26: Report document_type invalid ===
echo "=== Step 26: report.document_type invalid (with rehash) ==="
T26="$TMPDIR_ROOT/t26"
fresh_copy "$T26"
python3 - "$T26" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "composed-gateway-evidence-report.json"
r = json.loads(rp.read_text())
r["document_type"] = "proofrail.silver.not_a_real_doc_type"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T26" "composed-gateway-evidence-report.json"
expect_verifier_fail "step26" "$T26" "normalized_report_invalid"
echo "PASS step 26: normalized_report_invalid"

# === Step 27: Required claim_id removed from report.claims ===
echo "=== Step 27: Remove required claim_id from report.claims (with rehash) ==="
T27="$TMPDIR_ROOT/t27"
fresh_copy "$T27"
python3 - "$T27" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "composed-gateway-evidence-report.json"
r = json.loads(rp.read_text())
r["claims"] = [c for c in r["claims"] if c["claim_id"] != "out_of_scope_actions_fail"]
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T27" "composed-gateway-evidence-report.json"
expect_verifier_fail "step27" "$T27" "normalized_claim_missing"
echo "PASS step 27: normalized_claim_missing"

# === Step 28: Scoped mutation check ===
echo "=== Step 28: Committed v0.2.7 source files unchanged ==="
SNAPSHOT_AFTER="$TMPDIR_ROOT/snapshot-after.sha256"
{
  shasum -a 256 "$COMPOSER" "$VERIFIER"
  shasum -a 256 "$ADAPTER_VALIDATOR" "$ADAPTER"
  shasum -a 256 "$EVENTS" "$FIXTURE_ROOT/README.md"
  shasum -a 256 "$DEMO_ROOT/README.md" "$DEMO_ROOT/demo-walkthrough.md"
  shasum -a 256 "schemas/silver-simulated-gateway-evidence-event-v0.1.0.md" \
               "schemas/silver-composed-gateway-evidence-report-v0.1.0.md" \
               "schemas/silver-composed-gateway-evidence-manifest-v0.1.0.md"
  shasum -a 256 "docs/silver/silver-composed-gateway-evidence-demo-v0.2.7.md"
} > "$SNAPSHOT_AFTER"
if ! diff -q "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" > /dev/null; then
    echo "FAIL: committed v0.2.7 source files were modified by the test"
    diff "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER"
    exit 1
fi
echo "PASS step 28: committed v0.2.7 source files unchanged"

echo
echo "=== ProofRail Silver v0.2.7 composed gateway evidence demo: 28/28 PASS ==="
