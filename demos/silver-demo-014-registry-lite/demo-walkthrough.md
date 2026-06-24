# Silver Demo 014 — Walkthrough (v0.3.7 Registry Lite)

This walkthrough shows the exact steps the v0.3.7 runner and verifier
perform on the deterministic local fixture.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.7).
- A working copy of ProofRail at v0.3.7 (HEAD includes
  `tools/silver/build_silver_registry_lite_v0_1_0.py` and
  `tools/silver/verify_silver_registry_lite_v0_1_0.py`).
- The committed canonical registry-lite fixture
  `fixtures/silver-registry-lite-v0.3.7/registry-lite.json`.

## Step 1 — Build the registry-lite package

```bash
python3 tools/silver/build_silver_registry_lite_v0_1_0.py \
  --input-registry fixtures/silver-registry-lite-v0.3.7/registry-lite.json \
  --manifest-id proofrail-silver-registry-lite-manifest-demo-001 \
  --report-id proofrail-silver-registry-lite-conformance-report-demo-001 \
  --generated-at 2026-08-15T00:30:00Z \
  --output-dir /tmp/proofrail-silver-registry-lite-v0.3.7 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-registry-lite-v0-3-7
```

Expected final stdout line:

```
PASS: silver registry lite v0.3.7 built at /tmp/proofrail-silver-registry-lite-v0.3.7
  manifest_id:  proofrail-silver-registry-lite-manifest-demo-001
  report_id:    proofrail-silver-registry-lite-conformance-report-demo-001
  registry_id:  proofrail-silver-registry-lite-demo-001
```

The runner performs these steps in this order:

1. **Phase A preflight** on `--input-registry` in five ordered checks
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
3. Byte-copy the input registry body to
   `<staging>/registry-lite.json` (subject [0]).
4. Re-derive the conformance report deterministically as canonical
   JSON bytes (`sort_keys=True`, `separators=(",",":"))` plus a
   trailing newline) — 24 entries, one per approved verifier check,
   each `status: pass` with a stable check_id and check_name — and
   write it to `<staging>/silver-registry-lite-conformance-report.json`
   (subject [1]).
5. Write the 2-subject manifest to
   `<staging>/silver-registry-lite-manifest.json` with canonical
   JSON. The manifest carries the `proofrail_release`,
   `hash_algorithm`, and a `registry_id` field cross-anchored
   against the registry body.
6. If `--self-validate`, subprocess-invoke the v0.3.7 verifier
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

## Step 2 — Verify the registry-lite package

```bash
python3 tools/silver/verify_silver_registry_lite_v0_1_0.py \
  --manifest /tmp/proofrail-silver-registry-lite-v0.3.7/silver-registry-lite-manifest.json
```

Expected output:

```
PASS: /tmp/proofrail-silver-registry-lite-v0.3.7/silver-registry-lite-manifest.json
```

The verifier runs 24 ordered checks against the 2-subject manifest:

1. `check_01` registry_manifest_invalid — manifest structure,
   document_type, proofrail_release, hash_algorithm, schema_version,
   manifest_id, two subjects in fixed roles (subject [0] role
   `registry_lite`, subject [1] role `conformance_report`) at fixed
   paths, each subject's recomputed sha256 / size_bytes match the
   recorded values, and `manifest.registry_id` equals the registry
   body's `registry_id`.
2. `check_02` registry_not_object — subject [0] body parses to a
   top-level JSON object.
3. `check_03` registry_schema_invalid — subject [0] `document_type`
   equals `proofrail.silver.registry_lite` and `schema_version`
   equals `v0.1.0`.
4. `check_04` registry_profile_unsupported — subject [0] `profile`
   equals `silver.registry_lite.v0.3.7`.
5. `check_05` registry_identity_invalid — `registry_id` matches the
   lowercase dotted identifier grammar and `registry_scope` is in
   the closed enum.
6. `check_06` registry_authority_invalid — `registry_authority.*` is
   present with non-empty `identity_id`, `display_name`, and
   `contact`.
7. `check_07` registry_entity_set_invalid — `entities` is a
   non-empty list of objects and `scope_limitations` is a non-empty
   list of non-empty strings.
8. `check_08` registry_entity_entry_invalid — each entity entry has
   `entity_id`, `display_label`, `role`, `status`, and
   `effective_period`.
9. `check_09` registry_entity_identifier_invalid — `entity_id`
   matches the dotted-identifier grammar.
10. `check_10` registry_role_invalid — each entity entry's `role` is
    in the closed 6-role set.
11. `check_11` registry_status_invalid — each entity entry's
    `status` is in the closed 5-status set.
12. `check_12` registry_effective_period_invalid —
    `effective_period.starts_at <= effective_period.ends_at` and
    both ISO-8601 UTC.
13. `check_13` registry_key_reference_invalid — each
    `key_references[i]` has `key_id`, closed `algorithm` enum,
    closed `key_reference_type` enum, sha256 fingerprint where the
    type requires it, and relative paths only with no `..`.
14. `check_14` registry_key_binding_invalid — each `key_bindings[i]`
    has `binding_id`, `key_id` that resolves to a local
    `key_references[]` entry, and `binding_purpose` in the closed
    binding-purpose enum.
15. `check_15` issuer_entry_invalid — issuer-roled entries carry a
    well-formed `issuer.*` block under closed enums.
16. `check_16` verifier_entry_invalid — verifier-roled entries carry
    a well-formed `verifier.*` block under closed enums.
17. `check_17` relying_party_entry_invalid — relying-party-roled
    entries carry a well-formed `relying_party.*` block.
18. `check_18` policy_authority_entry_invalid —
    policy-authority-roled entries carry a well-formed
    `policy_authority.*` block.
19. `check_19` revocation_source_entry_invalid —
    revocation-source-roled entries carry a well-formed
    `revocation_source.*` block under closed enums.
20. `check_20` protected_action_authority_entry_invalid —
    protected-action-authority-roled entries carry a well-formed
    `protected_action_authority.*` block under closed enums.
21. `check_21` trust_relationship_invalid — each
    `trust_relationships[i]` has `relationship_id`, closed
    `relationship_verb`, and `from_entity_id` / `to_entity_id` that
    resolve in `entities[]`.
22. `check_22` version_binding_invalid — each `version_bindings[i]`
    has `binding_id`, `upstream_id` in the closed Silver
    upstream_id set, and `upstream_version` in the closed
    upstream_version set.
23. `check_23` non_claims_missing — `non_claims` is a non-empty list
    of non-empty strings.
24. `check_24` prohibited_registry_claim_present — recursive scan of
    every string value in the registry body OUTSIDE
    `scope_limitations` and `non_claims` for the 36 forbidden
    positive tokens (see release doc).

After the 24 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected report bytes from the verified registry body, and
byte-compares the two. A disagreement is reported as the
verifier-side reason `registry_manifest_invalid` (because the
bundled report does not describe a passing verification of this
exact registry). This is the non-masking funnel; no twenty-fifth
public reason is introduced.

## Step 3 — Run the regression test

```bash
bash tests/test_silver_registry_lite_v0_3_7.sh
```

Equivalent Make target:

```bash
make verify-silver-registry-lite-v0-3-7
```

The regression test runs 47 ordered cases:

- **4 positive-path checks (PP1–PP4):** pristine build, pristine
  verify, inline manifest-layout check, inline conformance-report
  check.
- **24 canonical verifier reason mutations (case01–case24):** one
  targeted mutation per approved verifier reason. Each mutation
  hash-first re-anchors `subjects[i].sha256` and `size_bytes` so the
  targeted structural check fires instead of short-circuiting on
  `check_01`.
- **11 duplicate manifest-invalid mutations (dup01–dup11):** all
  routed to `registry_manifest_invalid` (subject [0] absolute path,
  subject [0] `..` path, subject [1] absolute path, subject [1]
  `..` path, subject [0] file missing, subject [0] `size_bytes`
  mismatch, subject [0] `sha256` mismatch, wrong subject count,
  subject [0] role wrong, `registry_id` cross-anchor mismatch, and
  the non-masking post-structural conformance-report disagreement).
  dup11 also confirms the non-masking ordering: the verifier
  completes all 24 structural checks first, then catches the
  disagreement at the byte-image re-derivation step.
- **6 runner-only refusal exercises covering 5 distinct runner-only
  reasons (ro1, ro2, ro2b, ro3..ro5):** one for each Phase A reason,
  with `runner_input_path_forbidden` exercised twice (ro2 absolute
  input, ro2b parent-traversal input) to assert both branches of the
  runner's path-forbidden preflight emit the same single reason. Each
  confirms exit 1, the exact reason, no Traceback, and no output
  directory or staging sibling left behind.
- **1 runner-relay-of-verifier-failure case (rel01):** a registry
  with the wrong document_type that reaches the verifier's check_03
  (`registry_schema_invalid`) via `--self-validate`; the runner
  must relay that exact verifier reason UNCHANGED, must not emit a
  sixth wrapper code, and must leave no destination or staging
  sibling.
- **1 taxonomy gate (TG1):** scans all v0.3.7-owned files (the two
  Python tools, the regression test, the three schema docs, the
  release doc, this demo directory, and the fixture set) plus the
  v0.3.7-anchored sections of `README.md`, `CLAUDE.md`,
  `tools/silver/README.md`,
  `docs/silver/silver-artifact-map-v0.1.7.md`,
  `docs/silver/silver-limitations-and-non-claims.md`, and
  `docs/gold/gold-boundary-v0.2.5.md` for any reason-like token that
  is not in the approved 24+5 set (modulo a small documented
  allowlist for non-reason tokens that happen to match the regex).
  Drift anywhere in v0.3.7 surface area fails at regression time.
- **1 scoped sha256 snapshot (SS):** captures a sha256 of the
  v0.3.7-owned source files BEFORE and AFTER the run; the test
  fails if any file drifted in the meantime.

A clean run prints `OK: silver registry lite v0.3.7 regression
(48 exercises)` and exits 0.

## Step 4 — Roll back

The runner writes to `/tmp` only; the committed repository is never
modified by the demo. A simple
`rm -rf /tmp/proofrail-silver-registry-lite-v0.3.7` removes the
emitted package. The regression test cleans up all of its own
temporary working directories on success.

## Failure modes (canonical reference)

The 24 verifier-side failure reasons and the 5 runner-only refusal
reasons are documented in:

- `docs/silver/silver-registry-lite-v0.3.7.md`
- `schemas/silver-registry-lite-v0.1.0.md`
- `schemas/silver-registry-lite-manifest-v0.1.0.md`
- `schemas/silver-registry-lite-conformance-report-v0.1.0.md`

No other failure codes are emitted by either the runner or the
verifier. The runner NEVER wraps a verifier failure in a sixth
runner-only code; the verifier's stable reason is relayed unchanged.

## Non-claims

The registry-lite package is hand-authored input that the v0.3.7
toolchain structurally validates and packages with a
deterministically derived conformance report. It is not a production
PKI; it is not a certificate authority or certification authority;
it is not a legal identity registry, identity-proofing record,
federation registry, or trust federation; it is not a regulator,
auditor, or third-party endorsement; it is not a certification,
compliance attestation, or audit-readiness assertion; it does not
re-evaluate any specific upstream Silver evidence against the
registry in this release; it does not issue, transfer, or accept any
reliance instrument; it is not legally enforceable; it does not
authorize production reliance; it does not advance the Gold
boundary. v0.3.7 ships local hash anchors only.
