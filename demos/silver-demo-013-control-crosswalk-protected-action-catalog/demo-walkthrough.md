# Silver Demo 013 — Walkthrough (v0.3.6 Control Crosswalk + Protected Action Catalog)

This walkthrough shows the exact steps the v0.3.6 runner and verifier
perform on the deterministic local fixture.

## Prerequisites

- Python 3.10+ (pure stdlib; no new runtime dependencies for v0.3.6).
- A working copy of ProofRail at v0.3.6 (HEAD includes
  `tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py`
  and
  `tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py`).
- The committed canonical control pack fixture
  `fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/control-pack.json`.

## Step 1 — Build the control crosswalk + protected action catalog package

```bash
python3 tools/silver/build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py \
  --input-pack fixtures/silver-control-crosswalk-protected-action-catalog-v0.3.6/control-pack.json \
  --manifest-id proofrail-silver-control-crosswalk-protected-action-catalog-manifest-demo-001 \
  --report-id proofrail-silver-control-crosswalk-protected-action-catalog-conformance-report-demo-001 \
  --generated-at 2026-07-20T00:30:00Z \
  --output-dir /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6 \
  --force \
  --self-validate
```

Equivalent Make target:

```bash
make run-silver-control-crosswalk-protected-action-catalog-v0-3-6
```

Expected final stdout line:

```
PASS: silver control crosswalk + protected action catalog v0.3.6 built at /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6
  manifest_id:    proofrail-silver-control-crosswalk-protected-action-catalog-manifest-demo-001
  report_id:      proofrail-silver-control-crosswalk-protected-action-catalog-conformance-report-demo-001
  control_pack_id: proofrail-silver-control-crosswalk-protected-action-catalog-demo-001
```

The runner performs these steps in this order:

1. **Phase A preflight** on `--input-pack` in five ordered checks
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
3. Byte-copy the input control pack to
   `<staging>/control-pack.json` (subject [0]).
4. Re-derive the conformance report deterministically as canonical
   JSON bytes (`sort_keys=True`, `separators=(",",":"))` plus a
   trailing newline) — 24 entries, one per approved verifier check,
   each `status: pass` with a stable check_id and check_name — and
   write it to
   `<staging>/silver-control-crosswalk-protected-action-catalog-conformance-report.json`
   (subject [1]).
5. Write the 2-subject manifest to
   `<staging>/silver-control-crosswalk-protected-action-catalog-manifest.json`
   with canonical JSON. The manifest carries the
   `proofrail_release`, `hash_algorithm`, and a `control_pack_id`
   field cross-anchored against the control pack body.
6. If `--self-validate`, subprocess-invoke the v0.3.6 verifier
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

## Step 2 — Verify the control crosswalk + protected action catalog package

```bash
python3 tools/silver/verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py \
  --manifest /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/silver-control-crosswalk-protected-action-catalog-manifest.json
```

Expected output:

```
PASS: /tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/silver-control-crosswalk-protected-action-catalog-manifest.json
```

The verifier runs 24 ordered checks across 25 ordered execution
steps against the 2-subject manifest:

1. `check_01` control_pack_manifest_invalid — manifest structure,
   document_type, proofrail_release, hash_algorithm, schema_version,
   manifest_id, two subjects in fixed roles (subject [0] role
   `control_pack`, subject [1] role `conformance_report`) at fixed
   paths, each subject's recomputed sha256 / size_bytes match the
   recorded values, and `manifest.control_pack_id` equals the
   control pack body's `control_pack_id`.
2. `check_02` control_pack_not_object — subject [0] body parses to a
   top-level JSON object.
3. `check_03` control_pack_schema_invalid — subject [0]
   `document_type` equals
   `proofrail.silver.control_crosswalk_protected_action_catalog` and
   `schema_version` equals `v0.1.0`.
4. `check_04` control_pack_profile_unsupported — subject [0]
   `profile` equals `silver.control_crosswalk.v0.3.6`.
5. `check_05` control_pack_identity_invalid — `package_owner.*`,
   `relying_party.*`, and `catalog_authority.*` each present with
   non-empty `identity_id`, `display_name`, and `role`.
6. `check_06` protected_action_catalog_invalid —
   `protected_action_catalog` is a non-empty list of objects.
7. `check_07` protected_action_entry_invalid — each catalog entry
   has `action_id`, `description`, `category`, `environment_scope`,
   `actor_scope`, `authority`, and `risk_boundary`.
8. `check_08` protected_action_identifier_invalid — `action_id`
   matches the lowercase dotted identifier grammar
   (`^[a-z][a-z0-9_]*(\.[a-z0-9][a-z0-9_]*)*$`).
9. `check_09` protected_action_scope_invalid — `category`,
   `environment_scope`, `actor_scope` each in their closed enums.
10. `check_10` protected_action_authority_invalid —
    `authority.posture` in the closed posture set,
    `delegation_allowed` boolean, `scoped_principals` a non-empty
    list of non-empty strings.
11. `check_11` protected_action_risk_boundary_invalid —
    `risk_boundary.risk_class` in the closed risk-class set,
    `blast_radius` and `rationale` non-empty strings.
12. `check_12` control_crosswalk_invalid — `control_crosswalk` is a
    non-empty list of objects.
13. `check_13` crosswalk_entry_invalid — each crosswalk entry has
    `mapping_id`, `action_id`, `artifact_type`, `artifact_path`,
    `relationship`, `control_concept_id`, `control_objective`, and
    `claim`.
14. `check_14` catalog_crosswalk_consistency_invalid — every
    crosswalk `action_id` resolves to a catalog entry, and every
    catalog entry's `action_id` is referenced by at least one
    crosswalk entry.
15. `check_15` proofrail_artifact_reference_invalid — each crosswalk
    entry's `artifact_type` is in the closed 43-entry repo-derived
    ProofRail artifact_type set; each `artifact_path` is relative
    and contains no `..`.
16. `check_16` evidence_relationship_invalid — each crosswalk
    entry's `relationship` is in the closed evidence-relationship
    enum.
17. `check_17` control_concept_reference_invalid —
    `control_concept_id` matches the lowercase dotted identifier
    grammar.
18. `check_18` control_objective_invalid — `control_objective` is a
    non-empty string.
19. `check_19` control_claim_invalid — `claim.verb` in the closed
    claim-verb set (`may_inform`, `may_evidence`, `may_support`)
    and `claim.scope_text` is a non-empty string.
20. `check_20` control_limitation_invalid — each
    `control_limitations[i]` has `limitation_id`, `summary` (non-empty
    string), and `domain` in the closed control-limitation domain
    enum.
21. `check_21` dependency_reference_invalid — each
    `dependency_references[i]` has `dependency_id`, `reference_type`
    in the closed reference-type enum, `upstream_id`, and
    `upstream_version`.
22. `check_22` version_binding_invalid — each `version_bindings[i]`
    has `binding_id`, `upstream_id` in the closed Silver upstream_id
    set, and `upstream_version`.
23. `check_23` non_claims_missing — `scope_limitations` and
    `non_claims` are non-empty lists of non-empty strings.
24. `check_24` prohibited_compliance_claim_present — recursive scan
    of every string value in the control pack OUTSIDE
    `scope_limitations`, `non_claims`, and `control_limitations` for
    the 32 forbidden positive tokens (`certified`, `certification`,
    `compliant`, `compliance`, `soc 2`, `soc2`, `iso 27001`,
    `iso27001`, `nist 800-53`, `nist800-53`, `pci dss`, `pci-dss`,
    `hipaa`, `regulator approved`, `auditor approved`, `control
    design effective`, `control operating effective`, `control
    design effectiveness`, `control operating effectiveness`,
    `audit ready`, `audit-ready`, `audited`, `production
    approved`, `production authorized`, `production ready`,
    `production-ready`, `legally enforceable`, `legally binding`,
    `trust transferred`, `trust transfer`, `runtime truth`,
    `governed reliance`, `gold governed reliance`, `gold
    certified`, `gold accepted`).

After the 24 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected report bytes from the verified control pack, and
byte-compares the two. A disagreement is reported as the
verifier-side reason `control_pack_manifest_invalid` (because the
bundled report does not describe a passing verification of this
exact control pack). This is the non-masking funnel; no
twenty-fifth public reason is introduced.

## Step 3 — Run the regression test

```bash
bash tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh
```

Equivalent Make target:

```bash
make verify-silver-control-crosswalk-protected-action-catalog-v0-3-6
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
  routed to `control_pack_manifest_invalid` (subject [0] absolute
  path, subject [0] `..` path, subject [1] absolute path, subject [1]
  `..` path, subject [0] file missing, subject [0] `size_bytes`
  mismatch, subject [0] `sha256` mismatch, wrong subject count,
  subject [0] role wrong, `control_pack_id` cross-anchor mismatch,
  and the non-masking post-structural conformance-report
  disagreement). dup11 also confirms the non-masking ordering: the
  verifier completes all 24 structural checks first, then catches
  the disagreement at the byte-image re-derivation step.
- **5 runner-only refusal cases (ro1–ro5):** one for each Phase A
  reason; each confirms exit 1, the exact reason, no Traceback, and
  no output directory or staging sibling left behind.
- **1 runner-relay-of-verifier-failure case (rel01):** a pack with
  the wrong document_type that reaches the verifier's check_03
  (`control_pack_schema_invalid`) via `--self-validate`; the runner
  must relay that exact verifier reason UNCHANGED, must not emit a
  sixth wrapper code, and must leave no destination or staging
  sibling.
- **1 taxonomy gate (TG1):** scans all v0.3.6-owned files (the two
  Python tools, the regression test, the three schema docs, the
  release doc, this demo directory, and the fixture set) plus the
  v0.3.6-anchored sections of `README.md`, `CLAUDE.md`,
  `tools/silver/README.md`,
  `docs/silver/silver-artifact-map-v0.1.7.md`,
  `docs/silver/silver-limitations-and-non-claims.md`, and
  `docs/gold/gold-boundary-v0.2.5.md` for any reason-like token that
  is not in the approved 24+5 set (modulo a small documented
  allowlist for non-reason tokens that happen to match the regex).
  Drift anywhere in v0.3.6 surface area fails at regression time.
- **1 scoped sha256 snapshot (SS):** captures a sha256 of the
  v0.3.6-owned source files BEFORE and AFTER the run; the test fails
  if any file drifted in the meantime.

A clean run prints `OK: silver control crosswalk + protected action
catalog v0.3.6 regression (47 exercises)` and exits 0.

## Step 4 — Roll back

The runner writes to `/tmp` only; the committed repository is never
modified by the demo. A simple `rm -rf
/tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6`
removes the emitted package. The regression test cleans up all of
its own temporary working directories on success.

## Failure modes (canonical reference)

The 24 verifier-side failure reasons and the 5 runner-only refusal
reasons are documented in:

- `docs/silver/silver-control-crosswalk-protected-action-catalog-v0.3.6.md`
- `schemas/silver-control-crosswalk-protected-action-catalog-v0.1.0.md`
- `schemas/silver-control-crosswalk-protected-action-catalog-manifest-v0.1.0.md`
- `schemas/silver-control-crosswalk-protected-action-catalog-conformance-report-v0.1.0.md`

No other failure codes are emitted by either the runner or the
verifier. The runner NEVER wraps a verifier failure in a sixth
runner-only code; the verifier's stable reason is relayed unchanged.

## Non-claims

The control crosswalk + protected action catalog package is
hand-authored input that the v0.3.6 toolchain structurally validates
and packages with a deterministically derived conformance report. It
is not a regulator, auditor, or third-party endorsement; it is not a
SOC 2 / ISO 27001 / NIST 800-53 / PCI DSS / HIPAA or any other
external framework mapping; it is not an opinion on control design
effectiveness or control operating effectiveness; it does not
re-evaluate any specific upstream Silver evidence against the
crosswalk in this release; it does not issue, transfer, or accept
any reliance instrument; it is not legally enforceable; it does not
authorize production reliance; it does not advance the Gold
boundary. v0.3.6 ships local hash anchors only.
