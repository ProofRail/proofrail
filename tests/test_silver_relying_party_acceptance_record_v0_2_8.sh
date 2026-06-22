#!/usr/bin/env bash
# Regression test for ProofRail Silver v0.2.8 relying-party acceptance record.
#
# Covers 30 cases (exercising all 22 stable validator failure reasons plus
# the generator-only evidence_verification_failed code):
#   1.  Compose v0.2.7 gateway evidence package into temporary output dir.
#   2.  Generate accepted relying-party acceptance package over that evidence.
#   3.  Validate generated acceptance package.
#   4.  Validate generated acceptance package with --evidence-package-root.
#   5.  Inline check package manifest subject order.
#   6.  Inline check record fields (status, purpose, policy id/version,
#       verifier, revocation, challenge, scope, non_claims).
#   7.  Tamper acceptance record without rehash -> acceptance_subject_hash_mismatch.
#   8.  Remove copied evidence manifest -> acceptance_subject_file_missing.
#   9.  Manifest subject path '..' -> acceptance_subject_path_traversal.
#   10. Manifest subject path absolute -> acceptance_subject_path_traversal.
#   11. Malformed acceptance record JSON + rehash -> invalid_acceptance_record
#       (no Python traceback).
#   12. Mutate package manifest document_type -> invalid_acceptance_package_manifest.
#   13. Mutate policy document_type + rehash -> invalid_acceptance_policy.
#   14. Mutate record.verification.verifier_tool + rehash
#       -> evidence_verification_required.
#   15. Policy id mismatch in record + rehash -> policy_mismatch.
#   16. Relying party mismatch in record + rehash -> relying_party_mismatch.
#   17. Purpose not allowed + rehash -> purpose_not_allowed.
#   18. Evidence type not allowed + rehash -> evidence_type_not_allowed.
#   19. Evidence manifest hash mismatch in record + rehash
#       -> evidence_manifest_hash_mismatch.
#   20. Accepted record with verification_result=fail + rehash
#       -> accepted_record_verification_failed.
#   21. Accepted record with blocking exception + rehash
#       -> accepted_record_has_blocking_exception.
#   22. accepted_with_exceptions without any exception + rehash
#       -> accepted_with_exceptions_missing_exception.
#   23. Rejected record without rejection_reason or failure_reason + rehash
#       -> rejected_record_missing_reason.
#   24. Remove revocation review + rehash -> revocation_review_missing.
#   25. Challenge window shorter than policy minimum + rehash
#       -> challenge_window_invalid.
#   26. Empty scope_limitations + rehash -> scope_limitations_missing.
#   27. Empty non_claims + rehash -> acceptance_non_claims_missing.
#   28. Tamper original v0.2.7 evidence package + validate w/ --evidence-package-root
#       -> external_evidence_verification_failed.
#   29. Generator: tamper v0.2.7 evidence, run generator with --decision accepted
#       -> stderr contains 'FAIL: evidence_verification_failed', exit 1.
#   30. Scoped mutation check: committed v0.2.8 schemas, fixture, tools,
#       demo docs, test, and release doc unchanged.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

V027_COMPOSER="tools/silver/compose_gateway_evidence_demo_v0_1_0.py"
V027_VERIFIER="tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"
GENERATOR="tools/silver/generate_relying_party_acceptance_record_v0_1_0.py"
VALIDATOR="tools/silver/validate_relying_party_acceptance_record_v0_1_0.py"
DEMO_ROOT="demos/silver-demo-004-composed-gateway-evidence"
ADAPTER="examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json"
V027_FIXTURE="fixtures/silver-composed-gateway-evidence-v0.2.7"
V028_FIXTURE="fixtures/silver-relying-party-acceptance-v0.2.8"
POLICY_FIXTURE="$V028_FIXTURE/acceptance-policy.json"
RELEASE_DOC="docs/silver/silver-relying-party-acceptance-record-v0.2.8.md"
DEMO005_ROOT="demos/silver-demo-005-relying-party-acceptance"

TMPDIR_ROOT="$(mktemp -d -t proofrail-v028-XXXXXX)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

V027_PKG="$TMPDIR_ROOT/v027-evidence"
PRISTINE="$TMPDIR_ROOT/pristine"
GENERATED_AT="2026-06-22T00:00:00Z"
CHALLENGE_CLOSES_AT="2026-07-22T00:00:00Z"

# Snapshot committed v0.2.8-owned files for Step 30.
SNAPSHOT_BEFORE="$TMPDIR_ROOT/snapshot-before.sha256"
{
  shasum -a 256 "$GENERATOR" "$VALIDATOR"
  shasum -a 256 "$POLICY_FIXTURE" "$V028_FIXTURE/README.md"
  shasum -a 256 "schemas/silver-relying-party-acceptance-policy-v0.1.0.md" \
               "schemas/silver-relying-party-acceptance-record-v0.1.0.md" \
               "schemas/silver-relying-party-acceptance-package-manifest-v0.1.0.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO005_ROOT/README.md" "$DEMO005_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_BEFORE"

# Helper: copy the pristine acceptance package into a fresh tamper directory.
fresh_copy() {
    local dest="$1"
    rm -rf "$dest"
    cp -R "$PRISTINE" "$dest"
}

# Helper: recompute sha256 + size for a list of subject paths inside a
# package's acceptance-package-manifest.json. Required after semantic
# edits so the validator reaches semantic checks instead of short-
# circuiting on acceptance_subject_hash_mismatch.
rehash_subjects_in_manifest() {
    local pkg_dir="$1"
    shift
    python3 - "$pkg_dir" "$@" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1])
targets = set(sys.argv[2:])
mpath = pkg / "acceptance-package-manifest.json"
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

# Helper: expect validator to fail with the given stable reason. Accepts
# multiple acceptable reasons separated by '|'.
expect_validator_fail() {
    local label="$1"
    local pkg_dir="$2"
    local accepted_reasons="$3"
    shift 3
    local logf
    logf="$TMPDIR_ROOT/$label.log"
    set +e
    python3 "$VALIDATOR" --manifest "$pkg_dir/acceptance-package-manifest.json" \
        "$@" > "$logf" 2>&1
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        echo "FAIL: [$label] validator exited 0 but expected failure"
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

# === Step 1: Compose v0.2.7 evidence into tmp ===
echo "=== Step 1: Compose v0.2.7 gateway evidence into tmp ==="
python3 "$V027_COMPOSER" \
  --demo-root "$DEMO_ROOT" \
  --adapter "$ADAPTER" \
  --gateway-events "$V027_FIXTURE/gateway-events.jsonl" \
  --output-dir "$V027_PKG" \
  --generated-at "$GENERATED_AT" \
  --force > "$TMPDIR_ROOT/t01.log" 2>&1
if [ ! -f "$V027_PKG/composed-gateway-evidence-manifest.json" ]; then
    echo "FAIL: v0.2.7 composer did not produce manifest"
    cat "$TMPDIR_ROOT/t01.log"
    exit 1
fi
echo "PASS step 1: v0.2.7 evidence composed"

# === Step 2: Generate accepted acceptance package ===
echo "=== Step 2: Generate accepted acceptance package ==="
python3 "$GENERATOR" \
  --policy "$POLICY_FIXTURE" \
  --evidence-manifest "$V027_PKG/composed-gateway-evidence-manifest.json" \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at "$GENERATED_AT" \
  --challenge-closes-at "$CHALLENGE_CLOSES_AT" \
  --output-dir "$PRISTINE" \
  --force > "$TMPDIR_ROOT/t02.log" 2>&1
if [ ! -f "$PRISTINE/acceptance-package-manifest.json" ]; then
    echo "FAIL: generator did not produce package manifest"
    cat "$TMPDIR_ROOT/t02.log"
    exit 1
fi
echo "PASS step 2: acceptance package generated"

# === Step 3: Validate generated acceptance package ===
echo "=== Step 3: Validate generated acceptance package ==="
python3 "$VALIDATOR" --manifest "$PRISTINE/acceptance-package-manifest.json" \
    > "$TMPDIR_ROOT/t03.log" 2>&1
echo "PASS step 3: pristine acceptance package validated"

# === Step 4: Validate with --evidence-package-root ===
echo "=== Step 4: Validate w/ --evidence-package-root ==="
python3 "$VALIDATOR" --manifest "$PRISTINE/acceptance-package-manifest.json" \
    --evidence-package-root "$V027_PKG" > "$TMPDIR_ROOT/t04.log" 2>&1
echo "PASS step 4: pristine package validated against original v0.2.7 package"

# === Step 5: Inline check package manifest subject order ===
echo "=== Step 5: Inline check package manifest subject order ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1] + "/acceptance-package-manifest.json"))
expected = [
    ("acceptance-policy.json", "acceptance_policy"),
    ("evidence/composed-gateway-evidence-manifest.json", "verified_evidence_manifest"),
    ("acceptance-record.json", "acceptance_record"),
]
subs = m["subjects"]
if len(subs) != 3:
    print("FAIL: subjects count != 3")
    sys.exit(1)
for i, (p, r) in enumerate(expected):
    if subs[i]["path"] != p or subs[i]["role"] != r:
        print(f"FAIL: subject {i} mismatch")
        sys.exit(1)
PYEOF
echo "PASS step 5: package manifest subject order correct"

# === Step 6: Inline check record fields ===
echo "=== Step 6: Inline check record fields ==="
python3 - "$PRISTINE" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1] + "/acceptance-record.json"))
checks = [
    ("decision.status", r["decision"]["status"], "accepted"),
    ("decision.purpose_id", r["decision"]["purpose_id"], "demo_trust_boundary_review"),
    ("relying_party.policy_id", r["relying_party"]["policy_id"],
     "proofrail-demo-relying-party-policy-v0.2.8"),
    ("relying_party.policy_version", r["relying_party"]["policy_version"], "v0.1.0"),
    ("verification.verifier_tool", r["verification"]["verifier_tool"],
     "tools/silver/verify_composed_gateway_evidence_demo_v0_1_0.py"),
    ("verification.verification_result", r["verification"]["verification_result"], "pass"),
    ("revocation_review.performed", r["revocation_review"]["performed"], True),
    ("revocation_review.outcome", r["revocation_review"]["outcome"],
     "no_revoked_authority_accepted"),
]
for label, actual, expected in checks:
    if actual != expected:
        print(f"FAIL: {label} = {actual!r} != {expected!r}")
        sys.exit(1)
if not r["scope_limitations"]:
    print("FAIL: scope_limitations empty")
    sys.exit(1)
if not r["non_claims"]:
    print("FAIL: non_claims empty")
    sys.exit(1)
if r["challenge_window"]["opens_at"] >= r["challenge_window"]["closes_at"]:
    print("FAIL: challenge_window opens >= closes")
    sys.exit(1)
PYEOF
echo "PASS step 6: record fields correct"

# === Step 7: Tamper record bytes, no rehash ===
echo "=== Step 7: Tamper record bytes, no rehash ==="
T7="$TMPDIR_ROOT/t07"
fresh_copy "$T7"
python3 - "$T7" <<'PYEOF'
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "acceptance-record.json"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_validator_fail "step07" "$T7" "acceptance_subject_hash_mismatch"
echo "PASS step 7: acceptance_subject_hash_mismatch"

# === Step 8: Remove copied evidence manifest ===
echo "=== Step 8: Remove copied evidence manifest ==="
T8="$TMPDIR_ROOT/t08"
fresh_copy "$T8"
rm "$T8/evidence/composed-gateway-evidence-manifest.json"
expect_validator_fail "step08" "$T8" "acceptance_subject_file_missing"
echo "PASS step 8: acceptance_subject_file_missing"

# === Step 9: Manifest subject path contains '..' ===
echo "=== Step 9: Manifest subject path contains '..' ==="
T9="$TMPDIR_ROOT/t09"
fresh_copy "$T9"
python3 - "$T9" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "acceptance-package-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][2]["path"] = "../etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_validator_fail "step09" "$T9" "acceptance_subject_path_traversal"
echo "PASS step 9: acceptance_subject_path_traversal (..)"

# === Step 10: Manifest subject path absolute ===
echo "=== Step 10: Manifest subject path absolute ==="
T10="$TMPDIR_ROOT/t10"
fresh_copy "$T10"
python3 - "$T10" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "acceptance-package-manifest.json"
m = json.loads(mp.read_text())
m["subjects"][0]["path"] = "/etc/passwd"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_validator_fail "step10" "$T10" "acceptance_subject_path_traversal"
echo "PASS step 10: acceptance_subject_path_traversal (absolute)"

# === Step 11: Malformed acceptance record JSON + rehash ===
echo "=== Step 11: Malformed acceptance record JSON (with rehash) ==="
T11="$TMPDIR_ROOT/t11"
fresh_copy "$T11"
python3 - "$T11" <<'PYEOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "acceptance-record.json"
p.write_text('{"unterminated: "value"\n')
PYEOF
rehash_subjects_in_manifest "$T11" "acceptance-record.json"
expect_validator_fail "step11" "$T11" "invalid_acceptance_record"
echo "PASS step 11: invalid_acceptance_record (no traceback)"

# === Step 12: Mutate package manifest document_type ===
echo "=== Step 12: Mutate package manifest document_type ==="
T12="$TMPDIR_ROOT/t12"
fresh_copy "$T12"
python3 - "$T12" <<'PYEOF'
import json, sys
from pathlib import Path
mp = Path(sys.argv[1]) / "acceptance-package-manifest.json"
m = json.loads(mp.read_text())
m["document_type"] = "proofrail.silver.not_a_real_manifest_type"
mp.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
PYEOF
expect_validator_fail "step12" "$T12" "invalid_acceptance_package_manifest"
echo "PASS step 12: invalid_acceptance_package_manifest"

# === Step 13: Mutate policy document_type + rehash ===
echo "=== Step 13: Mutate policy document_type (with rehash) ==="
T13="$TMPDIR_ROOT/t13"
fresh_copy "$T13"
python3 - "$T13" <<'PYEOF'
import json, sys
from pathlib import Path
pp = Path(sys.argv[1]) / "acceptance-policy.json"
p = json.loads(pp.read_text())
p["document_type"] = "proofrail.silver.not_a_real_policy_type"
pp.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T13" "acceptance-policy.json"
expect_validator_fail "step13" "$T13" "invalid_acceptance_policy"
echo "PASS step 13: invalid_acceptance_policy"

# === Step 14: Mutate record verifier_tool + rehash ===
echo "=== Step 14: Mutate record verification.verifier_tool (with rehash) ==="
T14="$TMPDIR_ROOT/t14"
fresh_copy "$T14"
python3 - "$T14" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["verification"]["verifier_tool"] = "tools/silver/some_other_tool.py"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T14" "acceptance-record.json"
expect_validator_fail "step14" "$T14" "evidence_verification_required"
echo "PASS step 14: evidence_verification_required"

# === Step 15: Policy id mismatch in record + rehash ===
echo "=== Step 15: Record policy_id mismatch (with rehash) ==="
T15="$TMPDIR_ROOT/t15"
fresh_copy "$T15"
python3 - "$T15" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["relying_party"]["policy_id"] = "proofrail-some-other-policy"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T15" "acceptance-record.json"
expect_validator_fail "step15" "$T15" "policy_mismatch"
echo "PASS step 15: policy_mismatch"

# === Step 16: Relying party mismatch + rehash ===
echo "=== Step 16: Record relying_party_id mismatch (with rehash) ==="
T16="$TMPDIR_ROOT/t16"
fresh_copy "$T16"
python3 - "$T16" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["relying_party"]["relying_party_id"] = "some.other.relying_party"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T16" "acceptance-record.json"
expect_validator_fail "step16" "$T16" "relying_party_mismatch"
echo "PASS step 16: relying_party_mismatch"

# === Step 17: Purpose not allowed + rehash ===
echo "=== Step 17: Record purpose not in policy.allowed_purposes (with rehash) ==="
T17="$TMPDIR_ROOT/t17"
fresh_copy "$T17"
python3 - "$T17" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["decision"]["purpose_id"] = "some_other_purpose"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T17" "acceptance-record.json"
expect_validator_fail "step17" "$T17" "purpose_not_allowed"
echo "PASS step 17: purpose_not_allowed"

# === Step 18: Evidence type not allowed + rehash ===
echo "=== Step 18: Record evidence_type not in policy.allowed_evidence_types ==="
T18="$TMPDIR_ROOT/t18"
fresh_copy "$T18"
python3 - "$T18" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["evidence_package"]["evidence_type"] = "proofrail.silver.some_other_evidence"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T18" "acceptance-record.json"
expect_validator_fail "step18" "$T18" "evidence_type_not_allowed"
echo "PASS step 18: evidence_type_not_allowed"

# === Step 19: Evidence manifest hash mismatch in record + rehash ===
echo "=== Step 19: Record evidence_package.manifest_sha256 mutated (with rehash) ==="
T19="$TMPDIR_ROOT/t19"
fresh_copy "$T19"
python3 - "$T19" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["evidence_package"]["manifest_sha256"] = "sha256:" + "0" * 64
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T19" "acceptance-record.json"
expect_validator_fail "step19" "$T19" "evidence_manifest_hash_mismatch"
echo "PASS step 19: evidence_manifest_hash_mismatch"

# === Step 20: Accepted record with verification_result=fail + rehash ===
echo "=== Step 20: Accepted record with verification_result=fail (with rehash) ==="
T20="$TMPDIR_ROOT/t20"
fresh_copy "$T20"
python3 - "$T20" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["verification"]["verification_result"] = "fail"
r["verification"]["failure_reason"] = "synthetic failure for test"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T20" "acceptance-record.json"
expect_validator_fail "step20" "$T20" "accepted_record_verification_failed"
echo "PASS step 20: accepted_record_verification_failed"

# === Step 21: Accepted record with blocking exception + rehash ===
echo "=== Step 21: Accepted record with blocking exception (with rehash) ==="
T21="$TMPDIR_ROOT/t21"
fresh_copy "$T21"
python3 - "$T21" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["exceptions"] = [{
    "severity": "blocking",
    "description": "a blocking exception present on an accepted record",
    "effect_on_scope": "would normally narrow scope",
}]
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T21" "acceptance-record.json"
expect_validator_fail "step21" "$T21" "accepted_record_has_blocking_exception"
echo "PASS step 21: accepted_record_has_blocking_exception"

# === Step 22: accepted_with_exceptions without any exception + rehash ===
echo "=== Step 22: accepted_with_exceptions without exceptions (with rehash) ==="
T22="$TMPDIR_ROOT/t22"
fresh_copy "$T22"
python3 - "$T22" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["decision"]["status"] = "accepted_with_exceptions"
r["exceptions"] = []
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T22" "acceptance-record.json"
expect_validator_fail "step22" "$T22" "accepted_with_exceptions_missing_exception"
echo "PASS step 22: accepted_with_exceptions_missing_exception"

# === Step 23: Rejected record without rejection reason + rehash ===
echo "=== Step 23: Rejected record without rejection_reason/failure_reason ==="
T23="$TMPDIR_ROOT/t23"
fresh_copy "$T23"
python3 - "$T23" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["decision"]["status"] = "rejected"
r["decision"]["rejection_reason"] = ""
r["verification"]["failure_reason"] = None
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T23" "acceptance-record.json"
expect_validator_fail "step23" "$T23" "rejected_record_missing_reason"
echo "PASS step 23: rejected_record_missing_reason"

# === Step 24: Remove revocation review (performed=false) + rehash ===
echo "=== Step 24: Remove revocation review (with rehash) ==="
T24="$TMPDIR_ROOT/t24"
fresh_copy "$T24"
python3 - "$T24" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["revocation_review"]["performed"] = False
r["revocation_review"]["outcome"] = "not_reviewed"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T24" "acceptance-record.json"
expect_validator_fail "step24" "$T24" "revocation_review_missing"
echo "PASS step 24: revocation_review_missing"

# === Step 25: Challenge window shorter than policy minimum + rehash ===
echo "=== Step 25: Challenge window too short (with rehash) ==="
T25="$TMPDIR_ROOT/t25"
fresh_copy "$T25"
python3 - "$T25" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
# 1 day window; policy minimum is 7 days.
r["challenge_window"]["opens_at"] = "2026-06-22T00:00:00Z"
r["challenge_window"]["closes_at"] = "2026-06-23T00:00:00Z"
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T25" "acceptance-record.json"
expect_validator_fail "step25" "$T25" "challenge_window_invalid"
echo "PASS step 25: challenge_window_invalid"

# === Step 26: Empty scope_limitations + rehash ===
echo "=== Step 26: Empty scope_limitations (with rehash) ==="
T26="$TMPDIR_ROOT/t26"
fresh_copy "$T26"
python3 - "$T26" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["scope_limitations"] = []
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T26" "acceptance-record.json"
expect_validator_fail "step26" "$T26" "scope_limitations_missing"
echo "PASS step 26: scope_limitations_missing"

# === Step 27: Empty non_claims + rehash ===
echo "=== Step 27: Empty non_claims (with rehash) ==="
T27="$TMPDIR_ROOT/t27"
fresh_copy "$T27"
python3 - "$T27" <<'PYEOF'
import json, sys
from pathlib import Path
rp = Path(sys.argv[1]) / "acceptance-record.json"
r = json.loads(rp.read_text())
r["non_claims"] = []
rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
PYEOF
rehash_subjects_in_manifest "$T27" "acceptance-record.json"
expect_validator_fail "step27" "$T27" "acceptance_non_claims_missing"
echo "PASS step 27: acceptance_non_claims_missing"

# === Step 28: External evidence verification failure ===
echo "=== Step 28: Tamper original v0.2.7 package + validate w/ --evidence-package-root ==="
T28_EVIDENCE="$TMPDIR_ROOT/t28-evidence"
cp -R "$V027_PKG" "$T28_EVIDENCE"
# Tamper events file but leave manifest hash unchanged so the v0.2.7
# verifier detects the inconsistency.
python3 - "$T28_EVIDENCE" <<'PYEOF'
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
expect_validator_fail "step28" "$PRISTINE" "external_evidence_verification_failed" \
    --evidence-package-root "$T28_EVIDENCE"
echo "PASS step 28: external_evidence_verification_failed"

# === Step 29: Generator refusal when v0.2.7 verifier fails ===
echo "=== Step 29: Generator refuses --decision accepted when v0.2.7 verifier fails ==="
T29_EVIDENCE="$TMPDIR_ROOT/t29-evidence"
cp -R "$V027_PKG" "$T29_EVIDENCE"
# Tamper events file without rehash so v0.2.7 verifier reports
# composed_subject_hash_mismatch.
python3 - "$T29_EVIDENCE" <<'PYEOF'
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "source/gateway-events.jsonl"
p.write_bytes(p.read_bytes() + b"\n")
PYEOF
T29_OUT="$TMPDIR_ROOT/t29-output"
set +e
python3 "$GENERATOR" \
  --policy "$POLICY_FIXTURE" \
  --evidence-manifest "$T29_EVIDENCE/composed-gateway-evidence-manifest.json" \
  --decision accepted \
  --purpose demo_trust_boundary_review \
  --decision-maker demo.relying_party.local_reviewer \
  --generated-at "$GENERATED_AT" \
  --challenge-closes-at "$CHALLENGE_CLOSES_AT" \
  --output-dir "$T29_OUT" \
  --force > "$TMPDIR_ROOT/t29.out" 2> "$TMPDIR_ROOT/t29.err"
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
    echo "FAIL: step 29 expected generator exit 1, got $rc"
    cat "$TMPDIR_ROOT/t29.err"
    exit 1
fi
if grep -q "Traceback" "$TMPDIR_ROOT/t29.err"; then
    echo "FAIL: step 29 generator leaked Python traceback"
    cat "$TMPDIR_ROOT/t29.err"
    exit 1
fi
if ! grep -q "^FAIL: evidence_verification_failed:" "$TMPDIR_ROOT/t29.err"; then
    echo "FAIL: step 29 expected 'FAIL: evidence_verification_failed:' in stderr"
    cat "$TMPDIR_ROOT/t29.err"
    exit 1
fi
echo "PASS step 29: evidence_verification_failed (generator exit 1)"

# === Step 30: Scoped mutation check ===
echo "=== Step 30: Committed v0.2.8 source files unchanged ==="
SNAPSHOT_AFTER="$TMPDIR_ROOT/snapshot-after.sha256"
{
  shasum -a 256 "$GENERATOR" "$VALIDATOR"
  shasum -a 256 "$POLICY_FIXTURE" "$V028_FIXTURE/README.md"
  shasum -a 256 "schemas/silver-relying-party-acceptance-policy-v0.1.0.md" \
               "schemas/silver-relying-party-acceptance-record-v0.1.0.md" \
               "schemas/silver-relying-party-acceptance-package-manifest-v0.1.0.md"
  shasum -a 256 "$RELEASE_DOC"
  shasum -a 256 "$DEMO005_ROOT/README.md" "$DEMO005_ROOT/demo-walkthrough.md"
} > "$SNAPSHOT_AFTER"
if ! diff -q "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER" > /dev/null; then
    echo "FAIL: committed v0.2.8 source files were modified by the test"
    diff "$SNAPSHOT_BEFORE" "$SNAPSHOT_AFTER"
    exit 1
fi
echo "PASS step 30: committed v0.2.8 source files unchanged"

echo
echo "=== ProofRail Silver v0.2.8 relying-party acceptance record: 30/30 PASS ==="
