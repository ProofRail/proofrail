# Gold Demo 001 — Walkthrough (v0.4.0 Minimal Gold Governed Reliance Demo)

This walkthrough shows the exact steps the v0.4.0 runner and verifier
perform on the deterministic local fixture.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.4.0).
- A working copy of ProofRail at v0.4.0 (HEAD includes
  `tools/gold/build_gold_governed_reliance_demo_v0_1_0.py` and
  `tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py`).
- The committed canonical fixture
  `fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`.

## Step 1 — Build the Minimal Gold Governed Reliance Demo package

```bash
python3 tools/gold/build_gold_governed_reliance_demo_v0_1_0.py \
  --input-package fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json \
  --manifest-id proofrail-gold-governed-reliance-manifest-demo-001 \
  --report-id proofrail-gold-governed-reliance-conformance-report-demo-001 \
  --generated-at 2026-09-15T00:30:00Z \
  --output-dir /tmp/proofrail-gold-governed-reliance-v0.4.0 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-gold-governed-reliance-v0-4-0
```

Expected final stdout line:

```
PASS: minimal gold governed reliance demo v0.4.0 built at /tmp/proofrail-gold-governed-reliance-v0.4.0
  manifest_id:                  proofrail-gold-governed-reliance-manifest-demo-001
  report_id:                    proofrail-gold-governed-reliance-conformance-report-demo-001
  package_id:                   proofrail-gold-governed-reliance-demo-001
  governed_reliance_demo_id:    gold-governed-reliance-demo-001
```

The runner performs these steps in this order:

1. **Phase A preflight** on `--input-package` in five ordered checks
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
3. Byte-copy the input package body to
   `<staging>/governed-reliance-scenarios.json` (subject [0]).
4. Re-derive the conformance report deterministically as canonical
   JSON bytes (`sort_keys=True`, `separators=(",",":"))` plus a
   trailing newline) — 24 entries, one per approved verifier check,
   each `status: pass` with a stable check_id and check_name — and
   write it to
   `<staging>/silver-gold-governed-reliance-conformance-report.json`
   (subject [1]).
5. Write the 2-subject manifest to
   `<staging>/gold-governed-reliance-package-manifest.json` with
   canonical JSON. The manifest carries the `proofrail_release`,
   `hash_algorithm`, and cross-anchored `package_id` and
   `governed_reliance_demo_id` fields against the package body.
6. If `--self-validate`, subprocess-invoke the v0.4.0 verifier
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

## Step 2 — Verify the Minimal Gold Governed Reliance Demo package

```bash
python3 tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py \
  --manifest /tmp/proofrail-gold-governed-reliance-v0.4.0/gold-governed-reliance-package-manifest.json
```

Expected output:

```
PASS: /tmp/proofrail-gold-governed-reliance-v0.4.0/gold-governed-reliance-package-manifest.json
```

The verifier runs 24 ordered checks against the 2-subject manifest:

1. `check_01` gold_manifest_invalid — manifest structure,
   document_type, proofrail_release, hash_algorithm, schema_version,
   manifest_id, two subjects in fixed roles (subject [0] role
   `governed_reliance_package`, subject [1] role `conformance_report`)
   at fixed paths, each subject's recomputed sha256 / size_bytes match
   the recorded values, and the manifest's `package_id` /
   `governed_reliance_demo_id` cross-anchor the package body's
   matching fields.
2. `check_02` gold_package_not_object — subject [0] body parses to a
   top-level JSON object.
3. `check_03` gold_package_schema_invalid — subject [0] `document_type`
   equals `proofrail.gold.governed_reliance_package`, `schema_version`
   equals `v0.1.0`, top-level required fields are present, and
   `scope_limitations` is a non-empty list of non-empty strings.
4. `check_04` gold_profile_unsupported — subject [0] `profile` equals
   `gold.governed_reliance.v0.4.0`.
5. `check_05` gold_package_identity_invalid — `package_id` and
   `governed_reliance_demo_id` match the lowercase dotted/dashed
   identifier grammar; `relying_party.identity_id` and `registry_ref`
   match the dotted identifier grammar; `display_name` and `contact`
   are non-empty.
6. `check_06` silver_verification_input_invalid —
   `inputs.silver_verification.input_type` equals
   `silver_verification_result`, `input_ref` non-empty, and
   `expected_status` in the closed `{pass, fail, skipped}` enum.
7. `check_07` silver_handoff_input_invalid —
   `inputs.silver_handoff.input_type` equals
   `silver_acceptance_handoff`, `input_ref` non-empty, and
   `expected_handoff_posture` in the closed
   `{for_demo_scope, review_required_before_reuse, not_reusable_without_governed_review}`
   enum.
8. `check_08` policy_pack_input_invalid —
   `inputs.policy_pack.input_type` equals
   `silver_relying_party_policy_pack`, `input_ref` non-empty, and
   `policy_pack_id` / `policy_pack_version` present.
9. `check_09` registry_lite_input_invalid —
   `inputs.registry_lite.input_type` equals `silver_registry_lite`,
   `input_ref` non-empty, and `registry_id` present.
10. `check_10` control_crosswalk_input_invalid —
    `inputs.control_crosswalk.input_type` equals
    `silver_control_crosswalk`, `input_ref` non-empty, and
    `control_pack_id` present.
11. `check_11` governed_decision_set_invalid — `governed_decisions` is
    a list of 1..5 entries; `scenario_type` values are unique across
    the list; entries appear in the natural order
    `clean_acceptance` < `policy_rejection` < `challenge_filed` <
    `withdrawal` < `supersession`.
12. `check_12` governed_decision_entry_invalid — each entry carries a
    valid `decision_id`, `scenario_type`, `decision_status`,
    `decision_subject`, `policy_binding`, `registry_binding`,
    `action_scope`, `decision_trigger`, `scenario_specific_state`,
    and `recorded_at`.
13. `check_13` decision_subject_binding_invalid — each entry's
    `decision_subject.subject_type` is in the closed subject-type
    enum and `subject_ref` resolves to the matching `inputs.*` block.
14. `check_14` decision_policy_binding_invalid — each entry's
    `policy_binding.policy_pack_id` / `policy_pack_version` match the
    package's `inputs.policy_pack`, `policy_clause_refs` is a
    non-empty list, and `policy_decision` is in the closed
    `{allow, deny, review, withhold, conditional}` enum.
15. `check_15` decision_registry_binding_invalid — each entry's
    `registry_binding.relying_party_id` equals the package's
    `relying_party.identity_id` and `decision_authority_role` is in
    the closed `{relying_party, policy_authority, protected_action_authority}`
    enum.
16. `check_16` decision_action_scope_invalid — each entry's
    `action_scope` carries closed `protected_action_id`,
    `action_category`, and `action_environment` enums.
17. `check_17` decision_status_invalid — `decision_status` matches
    `scenario_type` under the closed mapping table.
18. `check_18` acceptance_path_invalid — for `clean_acceptance`
    entries, `scenario_specific_state.acceptance_record_ref` is
    non-empty.
19. `check_19` rejection_path_invalid — for `policy_rejection`
    entries, `rejection_reason` and `silver_verification_passing` are
    well-formed.
20. `check_20` challenge_path_invalid — for `challenge_filed`
    entries, `challenge_record_ref` is non-empty and `challenge_state`
    is in the closed challenge-state enum.
21. `check_21` withdrawal_path_invalid — for `withdrawal` entries,
    `withdrawal_record_ref` is non-empty and `withdrawal_trigger` is
    in the closed withdrawal-trigger enum.
22. `check_22` supersession_path_invalid — for `supersession`
    entries, `prior_decision_ref_kind` is in the closed
    `{internal_decision_id, external_decision_id}` enum,
    `prior_decision_id` is non-empty, `supersession_trigger` is in
    the closed enum, and `superseding_input_ref` is non-empty.
    `internal_decision_id` additionally requires `prior_decision_id`
    to resolve to another entry's `decision_id` in the same
    `governed_decisions[]`.
23. `check_23` non_claims_missing — `non_claims` is a non-empty list
    of non-empty strings.
24. `check_24` prohibited_gold_claim_present — recursive scan of
    every string value in the package body OUTSIDE
    `scope_limitations` and `non_claims` for the closed prohibited
    Gold-claim vocabulary (see release doc).

After the 24 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected report bytes from the verified package body, and byte-compares
the two. A disagreement is reported as the verifier-side reason
`gold_manifest_invalid` (because the bundled report does not describe
a passing verification of this exact package). This is the non-masking
funnel; no 25th public reason is introduced.

## Step 3 — Run the regression test

```bash
bash tests/test_gold_governed_reliance_v0_4_0.sh
```

Equivalent Make target:

```bash
make verify-gold-governed-reliance-v0-4-0
```

The regression test runs 53 ordered cases:

- **4 positive-path checks (PP1–PP4):** pristine build, pristine
  verify, inline manifest-layout check, inline conformance-report
  check.
- **5 single-scenario fixture build+verify (SC1–SC5):** each
  single-scenario slice is built and verified independently.
- **24 canonical verifier reason mutations (case01–case24):** one
  targeted mutation per approved verifier reason. Each mutation
  hash-first re-anchors `subjects[i].sha256` and `size_bytes` so the
  targeted structural check fires instead of short-circuiting on
  `check_01`.
- **11 duplicate manifest-invalid mutations (dup01–dup11):** all
  routed to `gold_manifest_invalid` (subject [0] absolute path,
  subject [0] `..` path, subject [1] absolute path, subject [1] `..`
  path, subject [0] file missing, subject [0] `size_bytes` mismatch,
  subject [0] `sha256` mismatch, wrong subject count, subject [0]
  role wrong, manifest `package_id` cross-anchor mismatch, and the
  non-masking post-structural conformance-report disagreement).
  dup11 also confirms the non-masking ordering: the verifier
  completes all 24 structural checks first, then catches the
  disagreement at the byte-image re-derivation step.
- **6 runner-only refusal exercises covering 5 distinct runner-only
  reasons (ro1, ro2, ro2b, ro3..ro5):** one for each Phase A reason,
  with `runner_input_path_forbidden` exercised twice (ro2 absolute
  input, ro2b parent-traversal input) to assert both branches of the
  runner's path-forbidden preflight emit the same single reason.
  Each confirms exit 1, the exact reason, no Traceback, and no
  output directory or staging sibling left behind.
- **1 runner-relay-of-verifier-failure case (rel01):** a package
  with the wrong document_type that reaches the verifier's check_03
  (`gold_package_schema_invalid`) via `--self-validate`; the runner
  must relay that exact verifier reason UNCHANGED, must not emit a
  sixth wrapper code, and must leave no destination or staging
  sibling.
- **1 taxonomy gate (TG1):** scans all v0.4.0-owned files (the two
  Python tools, the regression test, the three schema docs, the
  release doc, this demo directory, and the fixture set) plus the
  v0.4.0-anchored sections of `README.md`, `CLAUDE.md`,
  `tools/gold/README.md`, `docs/dev/silver-release-index.md`, and
  `docs/gold/gold-boundary-v0.2.5.md` for any reason-like token that
  is not in the approved 24-verifier-reason set or
  5-runner-only-reason set (the v0.4.0 allowlist is empty). Drift
  anywhere in v0.4.0 surface area fails at regression time.
- **1 scoped sha256 snapshot (SS):** captures a sha256 of the
  v0.4.0-owned source files BEFORE and AFTER the run; the test
  fails if any file drifted in the meantime.

A clean run prints `OK: gold governed reliance v0.4.0 regression
(53 exercises)` and exits 0.

## Step 4 — Roll back

The runner writes to `/tmp` only; the committed repository is never
modified by the demo. A simple
`rm -rf /tmp/proofrail-gold-governed-reliance-v0.4.0` removes the
emitted package. The regression test cleans up all of its own
temporary working directories on success.

## Failure modes (canonical reference)

The 24 verifier-side failure reasons and the 5 runner-only refusal
reasons are documented in:

- `docs/gold/minimal-gold-governed-reliance-v0.4.0.md`
- `schemas/gold-governed-reliance-package-v0.1.0.md`
- `schemas/gold-governed-reliance-package-manifest-v0.1.0.md`
- `schemas/gold-governed-reliance-conformance-report-v0.1.0.md`

No other failure codes are emitted by either the runner or the
verifier. The runner NEVER wraps a verifier failure in a sixth
runner-only code; the verifier's stable reason is relayed unchanged.

## Non-claims

The Minimal Gold Governed Reliance Demo package is hand-authored input
that the v0.4.0 toolchain structurally validates and packages with a
deterministically derived conformance report. It is not full Gold; it
is not Platinum; it is not signed; it is not a certificate; it is not
federated; it is not a transfer of reliance to any external party; it
is not a regulator, auditor, or third-party endorsement; it is not
legal acceptance, legal enforceability, or legal adjudication; it is
not production authorization, production governance, or production
PKI; it is not an audit-readiness assertion or a control-effectiveness
assertion; it does not re-evaluate any specific upstream Silver
evidence against any live service or external registry in this
release; the five `inputs.*` blocks are structural pointers under
closed input-type and ref grammar only; it does not represent runtime
truth. v0.4.0 ships local hash anchors only.
