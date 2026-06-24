# Silver Demo 012 — Walkthrough (v0.3.5 Relying-Party Policy Pack)

This walkthrough shows the exact steps the v0.3.5 runner and verifier
perform on the deterministic local fixture.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.5).
- A working copy of ProofRail at v0.3.5 (HEAD includes
  `tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py` and
  `tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py`).
- The committed canonical policy pack fixture
  `fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json`.

## Step 1 — Build the relying-party policy pack package

```bash
python3 tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py \
  --policy-pack fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json \
  --manifest-id proofrail-silver-relying-party-policy-pack-manifest-demo-001 \
  --report-id proofrail-silver-relying-party-policy-pack-conformance-report-demo-001 \
  --generated-at 2026-07-06T00:30:00Z \
  --output-dir /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-relying-party-policy-pack-v0-3-5
```

Expected final stdout line:

```
PASS: silver relying-party policy pack v0.3.5 built at /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5
  manifest_id:    proofrail-silver-relying-party-policy-pack-manifest-demo-001
  report_id:      proofrail-silver-relying-party-policy-pack-conformance-report-demo-001
  policy_pack_id: proofrail-silver-relying-party-policy-pack-demo-001
```

The runner performs these steps in this order:

1. **Phase A preflight** on `--policy-pack` in five ordered checks
   (each emits a single, distinct runner-only reason):
   1. `runner_input_path_missing` — argv missing or empty;
   2. `runner_input_path_forbidden` — absolute path or contains `..`;
   3. `runner_input_file_missing` — relative path does not exist;
   4. `runner_input_read_failed` — path is a directory or unreadable;
   5. `runner_input_json_invalid` — file is not valid UTF-8 JSON.
   Phase A NEVER touches the output directory and NEVER stages
   anything. Refusals exit 1 with `FAIL: <reason>: <detail>` and
   leave no staging sibling.
2. **Phase B stage** the package directory under
   `<output-dir>.staging.<pid>`.
3. Byte-copy the input policy pack to
   `<staging>/silver-relying-party-policy-pack.json` (subject [0]).
4. Re-derive the conformance report deterministically as canonical
   JSON bytes (`sort_keys=True`, `separators=(",",":"))` plus a
   trailing newline) — 24 entries, one per approved verifier check,
   each `status: pass` with a stable check_id and check_name — and
   write it to
   `<staging>/silver-relying-party-policy-pack-conformance-report.json`
   (subject [1]).
5. Write the 2-subject manifest to
   `<staging>/silver-relying-party-policy-pack-manifest.json` with
   canonical JSON (`indent=2`, `sort_keys=True`).
6. If `--self-validate`, subprocess-invoke the v0.3.5 verifier
   against the staged manifest BEFORE the atomic publish. On
   self-validation failure the verifier's OWN stable reason is
   relayed UNCHANGED (the runner does NOT wrap it in a sixth
   runner-only code), the staging directory is removed, and
   `--output-dir` is left untouched.
7. Atomic publish: only AFTER a successful staging build and (if
   `--self-validate`) a successful self-validation does the runner
   remove an existing `--output-dir` (requires `--force`) and
   `os.replace()` the staging directory into place. Any earlier
   failure leaves staging cleaned up and `--output-dir` untouched.

## Step 2 — Verify the relying-party policy pack package

```bash
python3 tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py \
  --manifest /tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/silver-relying-party-policy-pack-manifest.json
```

Expected output:

```
PASS: Silver relying-party policy pack v0.3.5 valid (proofrail-silver-relying-party-policy-pack-manifest-demo-001)
```

The verifier runs 24 ordered checks against the 2-subject manifest:

1. `check_01` policy_pack_manifest_invalid — manifest structure,
   document_type, profile, schema_version, manifest_id, two subjects
   in fixed roles, each subject's recomputed sha256 / size_bytes
   match the recorded values.
2. `check_02` policy_pack_not_object — subject [0] body parses to a
   top-level JSON object.
3. `check_03` policy_pack_schema_invalid — subject [0] document_type
   equals `proofrail.silver.relying_party_policy_pack` and
   schema_version equals `0.1.0`.
4. `check_04` policy_pack_profile_unsupported — subject [0] profile
   equals `relying_party_policy_pack.preview`.
5. `check_05` policy_pack_identity_invalid — `relying_party.identity_id`
   and `relying_party.identity_label` are present and non-empty.
6. `check_06` policy_pack_authority_invalid — `policy_authority.*`
   has approver_role, approver_id, approved_at.
7. `check_07` policy_scope_invalid — `policy.*` has policy_id,
   policy_version, in_scope_purposes list, effective_period with
   starts_at < ends_at.
8. `check_08` protected_action_scope_invalid —
   `applicable_protected_actions` is a non-empty list of non-empty
   strings.
9. `check_09` silver_handoff_requirement_invalid —
   `silver_handoff_requirements.minimum_handoff_posture` in the
   closed posture set; `required_chain_components` non-empty.
10. `check_10` verifier_requirement_invalid —
    `verifier_requirements.minimum_posture` in the closed set;
    `requires_self_validate` boolean.
11. `check_11` issuer_requirement_invalid —
    `issuer_requirements.required_signature_algorithm = ed25519`;
    `trusted_issuers` non-empty list of objects with id/role/key_id.
12. `check_12` revocation_requirement_invalid —
    `revocation_requirements.mode` in the closed set;
    booleans typed.
13. `check_13` freshness_requirement_invalid —
    `freshness_requirements.max_age_seconds` a non-negative integer;
    `tolerated_skew_seconds` non-negative.
14. `check_14` challenge_requirement_invalid —
    `challenge_handling.posture` in the closed challenge posture set.
15. `check_15` withdrawal_requirement_invalid —
    `withdrawal_handling.posture` in the closed withdrawal posture
    set.
16. `check_16` supersession_requirement_invalid —
    `supersession_handling.posture` in the closed supersession
    posture set.
17. `check_17` acceptance_criteria_invalid —
    `acceptance_criteria.required_silver_results` non-empty list
    drawn from the closed acceptance results enum.
18. `check_18` rejection_criteria_invalid —
    `rejection_criteria.blocking_silver_results` non-empty list
    drawn from the closed rejection results enum.
19. `check_19` exception_policy_invalid — each `exceptions[i]` has
    exception_id, severity, approver_id, justification,
    effect_on_scope.
20. `check_20` hard_stop_policy_invalid — each `hard_stops[i]` has
    hard_stop_id, condition, on_match, and `overridable_by_exception`
    is the literal boolean false.
21. `check_21` warning_policy_invalid —
    `warning_treatment.unknown_warning_default` in the closed enum;
    each `warnings[i]` has warning_id and treatment in the closed
    enum.
22. `check_22` reference_policy_invalid — `related_silver_artifacts`
    (if present) is a list of objects with non-empty kind / path,
    path is relative and contains no `..`.
23. `check_23` non_claims_missing — `scope_limitations` and
    `non_claims` are non-empty lists of non-empty strings.
24. `check_24` prohibited_claim_present — recursive scan of every
    string value in the policy pack OUTSIDE `scope_limitations`,
    `non_claims`, and `relying_party.contact` for the 23 forbidden
    positive tokens (`certified`, `approved`, `audited`,
    `compliance`, `compliant`, `regulator approved`, `auditor
    approved`, `gold accepted`, `gold certified`, `gold governed
    reliance`, `legally accepted`, `legally revoked`, `legally
    binding`, `production approved`, `production authorized`,
    `production ready`, `production-ready`, `risk approved`,
    `trust transferred`, `trust transfer`, `challenge resolved`,
    `withdrawal resolved`, `final ruling`).

After the 22 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected report bytes from the verified policy pack, and byte-compares
the two. A disagreement is reported as the verifier-side reason
`policy_pack_manifest_invalid` (because the bundled report does not
describe a passing verification of this exact policy pack).

## Step 3 — Run the regression test

```bash
bash tests/test_silver_relying_party_policy_pack_v0_3_5.sh
```

Equivalent Make target:

```bash
make verify-silver-relying-party-policy-pack-v0-3-5
```

The regression test runs 47 ordered cases:

- **4 positive-path checks (PP1–PP4):** pristine build,
  pristine verify, inline manifest-layout check, inline
  conformance-report check.
- **24 canonical verifier reason mutations (case01–case24):** one
  targeted mutation per approved verifier reason. Each mutation
  hash-first re-anchors `subjects[i].sha256` and `size_bytes` so the
  targeted structural check fires instead of short-circuiting on
  `check_01`.
- **11 duplicate manifest-invalid mutations (dup01–dup11):** all
  routed to `policy_pack_manifest_invalid` (subjects list missing,
  wrong subject count, wrong role at [0]/[1], absolute / `..` path
  at [0], sha256 mismatch at [0]/[1], size mismatch at [0],
  manifest_id missing, and the non-masking post-structural
  conformance-report disagreement). dup11 also confirms the
  non-masking ordering: the verifier completes all 22 structural
  checks first, then catches the disagreement at the byte-image
  re-derivation step.
- **5 runner-only refusal cases (ro1–ro5):** one for each Phase A
  reason; each confirms exit 1, the exact reason, no Traceback, and
  no output directory or staging sibling left behind.
- **1 runner-relay-of-verifier-failure case (rel01):** a pack with
  the wrong document_type that reaches the verifier's check_03
  (`policy_pack_schema_invalid`) via `--self-validate`; the runner
  must relay that exact verifier reason UNCHANGED, must not emit a
  sixth wrapper code, and must leave no destination or staging
  sibling.
- **1 taxonomy gate (TG1):** scans all v0.3.5-owned files (the two
  Python tools, the regression test, the three schema docs, the
  release doc, this demo directory, and the fixture set) plus the
  v0.3.5-anchored sections of `tools/silver/README.md` for any
  reason-like token that is not in the approved 24+5 set (modulo a
  small documented allowlist for non-reason tokens that happen to
  match the regex). Drift anywhere in v0.3.5 surface area fails at
  regression time.
- **1 scoped sha256 snapshot (SS):** captures a sha256 of the
  v0.3.5-owned source files BEFORE and AFTER the run; the test fails
  if any file drifted in the meantime.

A clean run prints `OK: silver relying-party policy pack v0.3.5
regression (47 exercises)` and exits 0.

## Step 4 — Roll back

The runner writes to `/tmp` only; the committed repository is never
modified by the demo. A simple `rm -rf
/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5` removes the
emitted package. The regression test cleans up all of its own
temporary working directories on success.

## Failure modes (canonical reference)

The 24 verifier-side failure reasons and the 5 runner-only refusal
reasons are documented in:

- `docs/silver/silver-relying-party-policy-pack-v0.3.5.md`
- `schemas/silver-relying-party-policy-pack-v0.1.0.md`
- `schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md`
- `schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md`

No other failure codes are emitted by either the runner or the
verifier. The runner NEVER wraps a verifier failure in a sixth
runner-only code; the verifier's stable reason is relayed unchanged.

## Non-claims

The relying-party policy pack package is hand-authored input that the
v0.3.5 toolchain structurally validates and packages with a
deterministically derived conformance report. It is not a regulator,
auditor, or third-party endorsement; it is not a certification; it
does not adjudicate any specific Silver evidence or any specific
challenge / withdrawal / supersession event; it is not legally
binding; it does not authorize production reliance; it does not
advance the Gold boundary. v0.3.5 ships local hash anchors only.
