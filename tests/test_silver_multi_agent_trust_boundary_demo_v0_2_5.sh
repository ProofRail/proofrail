#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.5 multi-agent trust-boundary demo package.
#
# Covers 17 cases:
#   1.  v0.2.4 harness verifier passes against the packaged nested manifest
#       (i.e., the packager successfully invoked and verified v0.2.4 evidence).
#   2.  Package generation into a temporary directory succeeds.
#   3.  Package verifier accepts the untampered package.
#   4.  demo-summary.json contains all 8 required claim IDs with status 'pass'.
#   5.  demo-summary.json states execution.protected_actions_performed == false.
#   6.  Package manifest subject hashes are valid (re-checked explicitly).
#   7.  Tampering with demo-summary.json contents -> demo_subject_hash_mismatch.
#   8.  Removing a package subject -> demo_subject_file_missing.
#   9.  Rewriting a subject path to contain '..' -> demo_subject_path_traversal.
#   10. Rewriting a subject path to be absolute -> demo_subject_path_traversal.
#   11. Tampering nested harness evidence -> nested_harness_evidence_invalid.
#   12. Malformed demo-summary.json (invalid JSON) -> invalid_demo_summary
#       (no Python traceback leakage).
#   13. Missing required claim -> demo_claim_missing.
#   14. Required claim with status != 'pass' -> demo_claim_failed.
#   15. Evidence refs containing '..' or absolute paths -> demo_evidence_ref_invalid.
#   16. Wrong-but-valid evidence ref (bypass -> EVT-001 instead of EVT-005)
#       -> demo_claim_failed or demo_evidence_ref_invalid.
#   17. Committed v0.2.5 demo source files were not modified by the runtime.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PACKAGER="tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py"
VERIFIER="tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py"
NESTED_VERIFIER="tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py"
DEMO_ROOT="demos/silver-demo-003-multi-agent-trust-boundary"
HARNESS_SCRIPT="fixtures/silver-multi-agent-attack-harness-v0.2.4/harness-script.yaml"
AUTHORITY_FIXTURE="fixtures/silver-multi-principal-authority-v0.2.3/authority-fixture.yaml"

TMPDIR_ROOT="$(mktemp -d -t proofrail-v025-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

OUT="$TMPDIR_ROOT/pkg"
TAMPER="$TMPDIR_ROOT/tamper"

# Snapshot committed demo source files for Step 17.
DEMO_SOURCE_SNAPSHOT_BEFORE="$TMPDIR_ROOT/demo-source-before.sha256"
{
  shasum -a 256 "$DEMO_ROOT/README.md" "$DEMO_ROOT/demo-walkthrough.md"
  shasum -a 256 "$PACKAGER" "$VERIFIER" "$NESTED_VERIFIER"
  shasum -a 256 "$HARNESS_SCRIPT" "$AUTHORITY_FIXTURE"
} > "$DEMO_SOURCE_SNAPSHOT_BEFORE"

# Helper: recompute the sha256 of demo-summary.json inside a package's
# demo-package-manifest.json. Required after semantic edits to the summary
# so the package verifier reaches the intended semantic failure instead of
# short-circuiting on subject_hash_mismatch.
rehash_demo_summary_in_manifest() {
    local pkg_dir="$1"
    python3 - "$pkg_dir" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
m = json.loads((pkg / "demo-package-manifest.json").read_text())
summary_path = pkg / "demo-summary.json"
h = hashlib.sha256(summary_path.read_bytes()).hexdigest()
size = summary_path.stat().st_size
for s in m["subjects"]:
    if s.get("role") == "demo_summary":
        s["sha256"] = f"sha256:{h}"
        s["size_bytes"] = size
(pkg / "demo-package-manifest.json").write_text(
    json.dumps(m, indent=2, sort_keys=True) + "\n"
)
PYEOF
}

# === Step 1 + 2: Package generation, with nested v0.2.4 verification ===
echo "=== Step 1+2: Package generation (also exercises v0.2.4 verifier on nested manifest) ==="
python3 "$PACKAGER" \
  --demo-root "$DEMO_ROOT" \
  --harness-script "$HARNESS_SCRIPT" \
  --authority-fixture "$AUTHORITY_FIXTURE" \
  --output-dir "$OUT" \
  --generated-at 2026-06-21T12:30:01Z \
  --force > "$TMPDIR_ROOT/t01.log" 2>&1
if [ ! -f "$OUT/demo-package-manifest.json" ]; then
    echo "FAIL: package manifest not produced"
    cat "$TMPDIR_ROOT/t01.log"
    exit 1
fi
if [ ! -f "$OUT/harness-evidence/harness-evidence-manifest.json" ]; then
    echo "FAIL: nested harness manifest not produced"
    exit 1
fi
echo "PASS: package generated"

# Independent re-verification of the nested manifest with v0.2.4 verifier.
python3 "$NESTED_VERIFIER" --manifest "$OUT/harness-evidence/harness-evidence-manifest.json" > "$TMPDIR_ROOT/t01-nested.log" 2>&1
echo "PASS: v0.2.4 verifier passes against the packaged nested manifest"

# === Step 3: Verifier accepts untampered package ===
echo "=== Step 3: Verifier accepts untampered package ==="
python3 "$VERIFIER" --package-manifest "$OUT/demo-package-manifest.json" > "$TMPDIR_ROOT/t03.log" 2>&1
echo "PASS: untampered package verified"

# === Step 4: demo-summary.json contains all 8 required claim IDs with status pass ===
echo "=== Step 4: demo-summary.json has all 8 required claim IDs (status pass) ==="
python3 - "$OUT" <<'PYEOF'
import json, sys
required = [
    "harmless_messages_proceed",
    "protected_actions_require_scoped_authority",
    "unauthorized_delegation_fails",
    "bypass_attempts_blocked",
    "revoked_authority_fails",
    "out_of_scope_actions_fail",
    "evidence_is_hash_verifiable",
    "no_protected_actions_executed",
]
s = json.load(open(sys.argv[1] + "/demo-summary.json"))
by_id = {c["claim_id"]: c for c in s["claims"]}
for r in required:
    if r not in by_id:
        print(f"FAIL: missing claim {r}")
        sys.exit(1)
    if by_id[r]["status"] != "pass":
        print(f"FAIL: claim {r} status != pass")
        sys.exit(1)
PYEOF
echo "PASS: all 8 required claim IDs present with status 'pass'"

# === Step 5: execution.protected_actions_performed == false ===
echo "=== Step 5: demo-summary execution.protected_actions_performed == false ==="
python3 - "$OUT" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1] + "/demo-summary.json"))
if s.get("execution", {}).get("protected_actions_performed") is not False:
    print("FAIL: execution.protected_actions_performed != false")
    sys.exit(1)
PYEOF
echo "PASS: execution.protected_actions_performed == false"

# === Step 6: Package manifest subject hashes are valid ===
echo "=== Step 6: Package manifest subject hashes are valid ==="
python3 - "$OUT" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
m = json.loads((root / "demo-package-manifest.json").read_text())
for s in m["subjects"]:
    p = root / s["path"]
    actual = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != s["sha256"]:
        print(f"FAIL: subject {s['path']} hash mismatch")
        sys.exit(1)
PYEOF
echo "PASS: all package subject hashes valid"

# Tamper helper: copy untampered package to fresh dir.
fresh_tamper() {
    rm -rf "$TAMPER"
    cp -R "$OUT" "$TAMPER"
}

run_expect_fail() {
    local expected_reason="$1"
    local logfile="$2"
    set +e
    python3 "$VERIFIER" --package-manifest "$TAMPER/demo-package-manifest.json" > "$logfile" 2>&1
    local rc=$?
    set -e
    if [ "$rc" -ne 1 ]; then
        echo "FAIL: expected exit 1, got $rc"
        cat "$logfile"
        exit 1
    fi
    if ! grep -q "$expected_reason" "$logfile"; then
        echo "FAIL: expected reason '$expected_reason' not found"
        cat "$logfile"
        exit 1
    fi
}

# === Step 7: Tamper with demo-summary.json contents (no manifest rehash) ===
echo "=== Step 7: Tamper demo-summary.json contents -> demo_subject_hash_mismatch ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
s["limitations"].append("TAMPERED")
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
run_expect_fail "demo_subject_hash_mismatch" "$TMPDIR_ROOT/t07.log"
echo "PASS: demo-summary.json tamper detected (demo_subject_hash_mismatch)"

# === Step 8: Remove a package subject ===
echo "=== Step 8: Remove a package subject -> demo_subject_file_missing ==="
fresh_tamper
rm "$TAMPER/README.md"
run_expect_fail "demo_subject_file_missing" "$TMPDIR_ROOT/t08.log"
echo "PASS: missing subject detected (demo_subject_file_missing)"

# === Step 9: Rewrite subject path with '..' ===
echo "=== Step 9: Rewrite subject path with '..' -> demo_subject_path_traversal ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "demo-package-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "../" + m["subjects"][0]["path"]
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
run_expect_fail "demo_subject_path_traversal" "$TMPDIR_ROOT/t09.log"
echo "PASS: '..' subject path detected (demo_subject_path_traversal)"

# === Step 10: Rewrite subject path absolute ===
echo "=== Step 10: Rewrite subject path absolute -> demo_subject_path_traversal ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "demo-package-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "/etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
run_expect_fail "demo_subject_path_traversal" "$TMPDIR_ROOT/t10.log"
echo "PASS: absolute subject path detected (demo_subject_path_traversal)"

# === Step 11: Tamper nested harness evidence -> nested_harness_evidence_invalid ===
echo "=== Step 11: Tamper nested harness evidence -> nested_harness_evidence_invalid ==="
fresh_tamper
# Append a byte to a nested subject so its nested-manifest hash mismatches.
echo "TAMPER" >> "$TAMPER/harness-evidence/transcript.jsonl"
# Note: we do NOT rehash the nested manifest. The nested v0.2.4 verifier should
# detect subject_hash_mismatch internally; the package verifier must surface
# this at the package level as nested_harness_evidence_invalid.
# We must, however, leave the package-level subject ("nested manifest") hash
# intact - we did not modify the nested manifest itself, only an interior file.
run_expect_fail "nested_harness_evidence_invalid" "$TMPDIR_ROOT/t11.log"
# Also confirm the top-level reason is stable even though nested reason differs.
if ! grep -q "FAIL: nested_harness_evidence_invalid" "$TMPDIR_ROOT/t11.log"; then
    echo "FAIL: top-level stable reason 'nested_harness_evidence_invalid' missing"
    cat "$TMPDIR_ROOT/t11.log"
    exit 1
fi
echo "PASS: nested tamper surfaced as nested_harness_evidence_invalid"

# === Step 12: Malformed demo-summary.json -> invalid_demo_summary (no traceback) ===
echo "=== Step 12: Malformed demo-summary.json -> invalid_demo_summary (no traceback) ==="
fresh_tamper
echo "{not valid json" > "$TAMPER/demo-summary.json"
rehash_demo_summary_in_manifest "$TAMPER"
run_expect_fail "invalid_demo_summary" "$TMPDIR_ROOT/t12.log"
if grep -q "Traceback" "$TMPDIR_ROOT/t12.log"; then
    echo "FAIL: Python traceback leaked from malformed JSON"
    cat "$TMPDIR_ROOT/t12.log"
    exit 1
fi
echo "PASS: malformed demo summary handled cleanly (invalid_demo_summary, no traceback)"

# === Step 13: Missing required claim -> demo_claim_missing ===
echo "=== Step 13: Missing required claim -> demo_claim_missing ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
s["claims"] = [c for c in s["claims"] if c["claim_id"] != "bypass_attempts_blocked"]
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_demo_summary_in_manifest "$TAMPER"
run_expect_fail "demo_claim_missing" "$TMPDIR_ROOT/t13.log"
echo "PASS: missing required claim detected (demo_claim_missing)"

# === Step 14: Failed required claim (status != pass) -> demo_claim_failed ===
echo "=== Step 14: Failed required claim -> demo_claim_failed ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
for c in s["claims"]:
    if c["claim_id"] == "harmless_messages_proceed":
        c["status"] = "fail"
        break
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_demo_summary_in_manifest "$TAMPER"
run_expect_fail "demo_claim_failed" "$TMPDIR_ROOT/t14.log"
echo "PASS: failed required claim detected (demo_claim_failed)"

# === Step 15: Evidence ref with '..' -> demo_evidence_ref_invalid ===
echo "=== Step 15: Evidence ref containing '..' -> demo_evidence_ref_invalid ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
for c in s["claims"]:
    if c["claim_id"] == "harmless_messages_proceed":
        c["evidence_refs"][0]["artifact"] = "../etc/passwd"
        break
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_demo_summary_in_manifest "$TAMPER"
run_expect_fail "demo_evidence_ref_invalid" "$TMPDIR_ROOT/t15a.log"
echo "PASS: evidence ref with '..' detected (demo_evidence_ref_invalid)"

echo "=== Step 15b: Evidence ref absolute -> demo_evidence_ref_invalid ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
for c in s["claims"]:
    if c["claim_id"] == "harmless_messages_proceed":
        c["evidence_refs"][0]["artifact"] = "/etc/passwd"
        break
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_demo_summary_in_manifest "$TAMPER"
run_expect_fail "demo_evidence_ref_invalid" "$TMPDIR_ROOT/t15b.log"
echo "PASS: absolute evidence ref detected (demo_evidence_ref_invalid)"

# === Step 16: Wrong-but-valid evidence ref ===
# Bypass claim references EVT-001 (an agent_message) instead of EVT-005
# (the bypass_attempt). Both events exist on disk, so this is not a missing
# file; it is a semantic claim violation.
echo "=== Step 16: Wrong-but-valid evidence ref -> demo_claim_failed or demo_evidence_ref_invalid ==="
fresh_tamper
python3 - "$TAMPER" <<'PYEOF'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "demo-summary.json"
s = json.loads(p.read_text())
for c in s["claims"]:
    if c["claim_id"] == "bypass_attempts_blocked":
        # Point bypass_attempts_blocked at EVT-001 (an agent_message).
        c["evidence_refs"] = [
            {"artifact": "harness-evidence/transcript.jsonl",
             "event_id": "EVT-001-harmless-message"}
        ]
        break
p.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_demo_summary_in_manifest "$TAMPER"
set +e
python3 "$VERIFIER" --package-manifest "$TAMPER/demo-package-manifest.json" > "$TMPDIR_ROOT/t16.log" 2>&1
RC=$?
set -e
if [ "$RC" -ne 1 ]; then
    echo "FAIL: expected exit 1 for wrong-but-valid evidence ref, got $RC"
    cat "$TMPDIR_ROOT/t16.log"
    exit 1
fi
if ! grep -qE "(demo_claim_failed|demo_evidence_ref_invalid)" "$TMPDIR_ROOT/t16.log"; then
    echo "FAIL: expected demo_claim_failed or demo_evidence_ref_invalid"
    cat "$TMPDIR_ROOT/t16.log"
    exit 1
fi
echo "PASS: wrong-but-valid evidence ref detected"

# === Step 17: Committed v0.2.5 demo source files not modified by runtime ===
echo "=== Step 17: Committed v0.2.5 demo source files unchanged ==="
DEMO_SOURCE_SNAPSHOT_AFTER="$TMPDIR_ROOT/demo-source-after.sha256"
{
  shasum -a 256 "$DEMO_ROOT/README.md" "$DEMO_ROOT/demo-walkthrough.md"
  shasum -a 256 "$PACKAGER" "$VERIFIER" "$NESTED_VERIFIER"
  shasum -a 256 "$HARNESS_SCRIPT" "$AUTHORITY_FIXTURE"
} > "$DEMO_SOURCE_SNAPSHOT_AFTER"
if ! diff "$DEMO_SOURCE_SNAPSHOT_BEFORE" "$DEMO_SOURCE_SNAPSHOT_AFTER" > "$TMPDIR_ROOT/t17.diff"; then
    echo "FAIL: committed v0.2.5 demo source files were modified by the runtime:"
    cat "$TMPDIR_ROOT/t17.diff"
    exit 1
fi
echo "PASS: committed v0.2.5 demo source files unchanged"

echo
echo "===================================================================="
echo "ProofRail Silver v0.2.5 multi-agent trust-boundary demo: 17/17 PASS"
echo "===================================================================="
