# Silver Relying-Party Policy Pack — v0.3.5

**Status:** Draft / ProofRail v0.3.5
**Release thesis:** ProofRail v0.3.5 introduces a deterministic local
Silver evidence primitive — a *relying-party policy pack* — paired
with a byte-for-byte re-derivable *conformance report* and a
2-subject manifest. An independent Silver reviewer can re-run the
unchanged v0.3.5 verifier against the manifest and re-derive every
structural check — without claiming that the policy pack has been
approved by a regulator, auditor, or third party, that any specific
upstream Silver evidence has been evaluated against it, or that any
reliance instrument has been issued, transferred, or accepted.

---

## v0.3.5 thesis

> A relying party can hand-author a structured local policy pack that
> declares its Silver acceptance posture under a closed enum
> vocabulary; the v0.3.5 runner can byte-copy the policy pack into a
> deterministic package alongside a re-derivable conformance report
> with 24 pass entries; and the v0.3.5 verifier can re-run 24 ordered
> structural checks on the policy pack and byte-compare the re-derived
> report against the bundled report — while preserving the boundary
> that v0.3.5 does **not** approve, audit, or certify the policy
> pack, does **not** adjudicate any specific challenge / withdrawal /
> supersession event against it, does **not** evaluate any specific
> upstream Silver evidence against it, and does **not** authorize
> production reliance.

## Relying-party policy pack boundary

> A v0.3.5 relying-party policy pack package is **not** a regulator
> action, an auditor finding, a third-party endorsement, a
> certification, a Gold artifact, an adjudication, an
> evidence-evaluation result, or an authorization for production
> reuse. It is a deterministic local evidence artifact recording that
> a relying party has hand-authored a structured policy and that the
> policy satisfies a fixed set of 24 ordered structural checks, paired
> with a re-derivable conformance report that an independent reviewer
> can reproduce byte-for-byte from the policy pack alone.

v0.3.5 answers:

```
Can a relying party hand-author a structured local policy pack
  declaring its Silver acceptance posture under a closed enum
  vocabulary?
Can the runner byte-copy the policy pack into a deterministic local
  package?
Can the runner deterministically re-derive a 24-entry conformance
  report whose canonical-JSON byte image depends only on the policy
  pack?
Can the runner refuse five distinct preflight failures
  (path missing, path forbidden, file missing, read failed, JSON
  invalid) with stable runner-only refusal reasons that the
  downstream verifier never re-emits?
Can the runner relay the v0.3.5 verifier's own failure UNCHANGED on
  --self-validate, without wrapping it in a sixth runner-only code?
Can the verifier independently re-run 24 ordered structural checks
  on the policy pack and the manifest, including:
    document_type / profile / schema_version sanity,
    relying-party identity and policy authority,
    policy scope and applicable protected actions,
    silver_handoff / verifier / issuer / revocation / freshness
      requirements under closed enum vocabularies,
    challenge / withdrawal / supersession postures under closed
      enums,
    acceptance_criteria and rejection_criteria result enums,
    exception, hard_stop, warning treatment policy,
    related_silver_artifacts reference policy,
    scope_limitations and non_claims presence,
    a 23-token prohibited-claim guard outside scope_limitations,
      non_claims, and relying_party.contact?
Can the verifier byte-compare the bundled conformance report against
  a re-derivation drawn solely from the verified policy pack and
  reject any disagreement?
```

v0.3.5 does **not** answer:

```
Has the policy pack been approved by a regulator?
Has the policy pack been approved by an auditor?
Has the policy pack been endorsed by any third party?
Has the relying party adopted the policy pack into production?
Has any specific upstream Silver evidence been evaluated against
  the policy pack in this release?
Has any reliance instrument been issued, transferred, or accepted?
Is the policy pack legally binding on the relying party?
Is the policy pack Gold-conformant?
```

---

## Schemas

Three new v0.1.0 schemas ship with v0.3.5:

```
schemas/silver-relying-party-policy-pack-v0.1.0.md
schemas/silver-relying-party-policy-pack-manifest-v0.1.0.md
schemas/silver-relying-party-policy-pack-conformance-report-v0.1.0.md
```

### Policy pack (`proofrail.silver.relying_party_policy_pack`)

The hand-authored evidence primitive. Required top-level fields:

```
document_type, schema_version, proofrail_release, profile,
policy_pack_id, generated_at, relying_party, policy_authority,
policy, applicable_protected_actions,
silver_handoff_requirements, verifier_requirements,
issuer_requirements, revocation_requirements,
freshness_requirements, challenge_handling, withdrawal_handling,
supersession_handling, acceptance_criteria, rejection_criteria,
exceptions, hard_stops, warning_treatment,
related_silver_artifacts, scope_limitations, non_claims
```

### Manifest (`proofrail.silver.relying_party_policy_pack_manifest`)

A 2-subject anchor over the policy pack and the conformance report
in fixed roles and fixed order:

```
[0] silver-relying-party-policy-pack.json                     role=policy_pack
[1] silver-relying-party-policy-pack-conformance-report.json  role=policy_pack_conformance_report
```

Each subject carries `sha256` (`sha256:<64hex>`) and `size_bytes`.

### Conformance report (`proofrail.silver.relying_party_policy_pack_conformance_report`)

A re-derivable record with 24 pass entries (one per approved
verifier check). The runner emits the report as canonical JSON bytes
(`sort_keys=True`, `separators=(",",":"))` with a trailing newline)
so the verifier can byte-compare its own re-derivation against the
bundled bytes.

---

## Verifier — 24 stable failure reasons (verifier-side)

The v0.3.5 verifier runs 24 ordered checks in fixed order with no
masking. Each check emits exactly one stable failure reason; the
verifier never invents a sixth wrapper code on a relayed failure.

| Check | Reason |
|---|---|
| `check_01` | `policy_pack_manifest_invalid` |
| `check_02` | `policy_pack_not_object` |
| `check_03` | `policy_pack_schema_invalid` |
| `check_04` | `policy_pack_profile_unsupported` |
| `check_05` | `policy_pack_identity_invalid` |
| `check_06` | `policy_pack_authority_invalid` |
| `check_07` | `policy_scope_invalid` |
| `check_08` | `protected_action_scope_invalid` |
| `check_09` | `silver_handoff_requirement_invalid` |
| `check_10` | `verifier_requirement_invalid` |
| `check_11` | `issuer_requirement_invalid` |
| `check_12` | `revocation_requirement_invalid` |
| `check_13` | `freshness_requirement_invalid` |
| `check_14` | `challenge_requirement_invalid` |
| `check_15` | `withdrawal_requirement_invalid` |
| `check_16` | `supersession_requirement_invalid` |
| `check_17` | `acceptance_criteria_invalid` |
| `check_18` | `rejection_criteria_invalid` |
| `check_19` | `exception_policy_invalid` |
| `check_20` | `hard_stop_policy_invalid` |
| `check_21` | `warning_policy_invalid` |
| `check_22` | `reference_policy_invalid` |
| `check_23` | `non_claims_missing` |
| `check_24` | `prohibited_claim_present` |

After the 22 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected canonical-JSON byte image from the verified policy pack,
and byte-compares the two. Disagreement surfaces as the verifier-side
reason `policy_pack_manifest_invalid` (subject [1] does not describe
a passing verification of this policy pack).

---

## Runner — 5 stable runner-only refusal reasons

The runner's Phase A preflight validates the `--policy-pack` argv
under five ordered, mutually exclusive checks. Each emits a single,
distinct runner-only refusal reason, and the runner never touches
the output directory or staging sibling on refusal:

| Phase A check | Reason |
|---|---|
| argv missing or empty | `runner_input_path_missing` |
| absolute path or contains `..` | `runner_input_path_forbidden` |
| relative path does not exist on disk | `runner_input_file_missing` |
| path is a directory or unreadable | `runner_input_read_failed` |
| file is not valid UTF-8 JSON | `runner_input_json_invalid` |

On `--self-validate` the runner subprocess-invokes the v0.3.5
verifier against the staged manifest BEFORE the atomic publish.
**The runner relays the verifier's OWN stable reason UNCHANGED.** It
does NOT wrap a verifier failure in a sixth runner-only code. The
staging directory is removed on self-validation failure and
`--output-dir` is left untouched. There is no
`runner_self_validation_failed` code anywhere in the v0.3.5
taxonomy; the regression test explicitly asserts that no such
sixth code is ever emitted.

---

## Closed enum surface

| Field path | Closed enum |
|---|---|
| `silver_handoff_requirements.minimum_handoff_posture` | `for_demo_scope`, `review_required_before_reuse`, `not_reusable_without_governed_review` |
| `verifier_requirements.minimum_posture` | `silver.base`, `silver.base.demo`, `silver.independent` |
| `issuer_requirements.required_signature_algorithm` | `ed25519` |
| `revocation_requirements.mode` | `required`, `required_with_warning_allowance`, `not_required` |
| `challenge_handling.posture` | `record_only`, `record_and_pause_reuse`, `record_and_require_review` |
| `withdrawal_handling.posture` | `record_only`, `record_and_pause_reuse`, `record_and_block_reuse` |
| `supersession_handling.posture` | `record_only`, `record_and_require_superseding_handoff`, `record_and_block_until_superseded` |
| `acceptance_criteria.required_silver_results[]` | `verifier_pass`, `issuer_trusted`, `revocation_check_performed`, `freshness_window_ok`, `attestation_present` |
| `rejection_criteria.blocking_silver_results[]` | `verifier_fail`, `issuer_untrusted`, `revocation_check_failed_or_skipped`, `freshness_window_exceeded`, `attestation_missing`, `posture_downgrade` |
| `warning_treatment.unknown_warning_default` | `block`, `review_required`, `allow_with_logging` |
| `warning_treatment.warnings[].treatment` | `block`, `review_required`, `allow_with_logging` |
| `hard_stops[].overridable_by_exception` | literal boolean `false` |

---

## Prohibited-claim guard

The verifier's recursive scan rejects any string value OUTSIDE
`scope_limitations`, `non_claims`, and `relying_party.contact` that
contains any of these 23 forbidden positive tokens:

```
certified, approved, audited, compliance, compliant,
regulator approved, auditor approved, gold accepted,
gold certified, gold governed reliance, legally accepted,
legally revoked, legally binding, production approved,
production authorized, production ready, production-ready,
risk approved, trust transferred, trust transfer,
challenge resolved, withdrawal resolved, final ruling
```

The scope_limitations / non_claims escape applies only to those two
lists by exact key match; nested objects with the same key elsewhere
do not benefit. The `relying_party.contact` escape exists so a
contact_url containing tokens like "audit" does not falsely trigger.

---

## Package layout

```
<output-dir>/
├── silver-relying-party-policy-pack.json                      (subject [0])
├── silver-relying-party-policy-pack-conformance-report.json   (subject [1])
└── silver-relying-party-policy-pack-manifest.json             (2-subject anchor)
```

---

## Fixtures

Four hand-authored passing policy packs ship under
`fixtures/silver-relying-party-policy-pack-v0.3.5/`:

| File | Variant |
|---|---|
| `policy-pack.json` | Canonical pack; all sections populated with representative values |
| `policy-pack-with-exception.json` | Multi-exception block; `record_and_pause_reuse` postures; tighter rejection set |
| `policy-pack-with-warning-policy.json` | Two attestors, two issuers, rich `warning_treatment.warnings`, three hard stops; `record_and_block_reuse` / `record_and_block_until_superseded` postures |
| `policy-pack-with-freshness-windows.json` | Tight freshness windows (2 h); no attestation required; `record_only` supersession |

Every fixture is a passing policy pack: parses to a top-level JSON
object, satisfies the 24 ordered structural checks, contains
non-empty `scope_limitations` and `non_claims`, and contains no
prohibited claim tokens outside those two blocks.

---

## Tools

```
tools/silver/build_silver_relying_party_policy_pack_v0_1_0.py
tools/silver/verify_silver_relying_party_policy_pack_v0_1_0.py
```

Pure-stdlib. No new runtime dependencies for v0.3.5.

---

## Make targets

```
make run-silver-relying-party-policy-pack-v0-3-5
make verify-silver-relying-party-policy-pack-v0-3-5
```

`verify-silver-all` chains the v0.3.5 regression test after v0.3.4.

---

## Regression test

```
tests/test_silver_relying_party_policy_pack_v0_3_5.sh
```

47 ordered exercises:

- 4 positive-path checks (pristine build + verify, inline manifest
  layout, inline conformance report)
- 24 canonical verifier reason mutations (one per approved reason),
  hash-first re-anchored
- 11 duplicate manifest-invalid mutations (all routed to
  `policy_pack_manifest_invalid`, including the non-masking
  post-structural conformance-report disagreement)
- 5 runner-only refusal cases (one per Phase A reason)
- 1 runner-relay-of-verifier-failure case (verifier reason relayed
  UNCHANGED; no sixth wrapper)
- 1 taxonomy gate (TG1) over all v0.3.5-owned files and the
  v0.3.5-anchored sections of `tools/silver/README.md`
- 1 scoped sha256 snapshot before / after

---

## Limitations and non-claims

- The relying-party policy pack package is not an approval, audit,
  or certification.
- The packaged conformance report describes only that the policy
  pack satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any specific upstream Silver
  evidence in this release.
- v0.3.5 does not evaluate any specific upstream handoff,
  verifier, issuer, or evidence package against the
  hand-authored requirements blocks.
- v0.3.5 does not adjudicate any specific challenge, withdrawal,
  supersession, or warning event against the hand-authored
  posture blocks.
- v0.3.5 ships local hash anchors only; the package is unsigned.
- v0.3.5 does not extend the substance of any earlier-release
  Silver evidence, does not authorize production reliance, is
  not regulator approval, is not auditor approval, is not
  legally binding, is not a Gold artifact, and does not advance
  the Gold boundary.
