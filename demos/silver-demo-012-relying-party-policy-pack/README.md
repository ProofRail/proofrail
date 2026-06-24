# Silver Demo 012 — Relying-Party Policy Pack (v0.3.5)

This demo is the deterministic, local Silver Relying-Party Policy Pack
package that ProofRail v0.3.5 derives from a single hand-authored
input:

- the canonical policy pack fixture
  (`fixtures/silver-relying-party-policy-pack-v0.3.5/policy-pack.json`).

It answers a narrow question:

> Can a hand-authored relying-party policy pack be structurally
> validated against 22 ordered checks under a closed posture / enum
> vocabulary, paired with a deterministically re-derived conformance
> report (24 pass entries, byte-identical re-derivation), and packaged
> alongside a 2-subject manifest — such that an independent Silver
> reviewer can re-run the unchanged v0.3.5 verifier and re-derive
> every check without claiming that the policy pack itself has been
> approved, audited, certified, or accepted by any external party?

It does **not** answer:

- Has the policy pack been approved by a regulator, auditor, or third
  party?
- Has the relying party adopted the policy pack into production?
- Have the silver_handoff_requirements / verifier_requirements /
  issuer_requirements been evaluated against any specific upstream
  evidence in this demo?
- Has any reliance instrument been issued, transferred, or accepted?
- Is the policy pack legally binding?
- Is the policy pack Gold-conformant?

## What the demo does

1. Validates the `--policy-pack` argv through 5 Phase A preflight
   checks (relative-path-only, no `..`, file exists, file is a
   regular file, file is valid JSON). Phase A emits only the 5
   approved runner-only refusal reasons: `runner_input_path_missing`,
   `runner_input_path_forbidden`, `runner_input_file_missing`,
   `runner_input_read_failed`, `runner_input_json_invalid`.
2. Stages output under `<output-dir>.staging.<pid>` and byte-copies
   the policy pack to
   `<staging>/silver-relying-party-policy-pack.json`.
3. Deterministically re-derives the conformance report (24 pass
   entries, one per approved verifier check) as canonical JSON
   bytes (`sort_keys=True`, `separators=(",",":"))` with a trailing
   newline, and writes it to
   `<staging>/silver-relying-party-policy-pack-conformance-report.json`.
4. Writes the 2-subject manifest at
   `<staging>/silver-relying-party-policy-pack-manifest.json`. The
   manifest carries `subjects[0]` = policy pack and `subjects[1]` =
   conformance report, each with `sha256` and `size_bytes`.
5. If `--self-validate`, subprocess-invokes the v0.3.5 verifier
   against the staged manifest BEFORE the atomic publish. Any
   verifier failure is relayed UNCHANGED (the verifier's own stable
   reason is emitted; the runner does NOT wrap it in a sixth
   runner-only code). On self-validation failure the staging
   directory is removed and `<output-dir>` is left untouched.
6. Atomic publish: only AFTER a successful staging build (and, if
   `--self-validate`, a successful self-validation) does the runner
   remove an existing `--output-dir` (requires `--force`) and
   `os.replace()` the staging directory into place.

The v0.3.5 verifier runs 24 ordered checks against the 2-subject
manifest. Checks fire in the documented order with no masking: 22
structural checks against the policy pack, then conformance-report
parse and byte-identical re-derivation. The verifier emits only the
24 approved verifier-side failure reasons listed in the schema and
release doc. It never invents a sixth runner-only wrapper code on a
relayed failure.

## Commands

```bash
make run-silver-relying-party-policy-pack-v0-3-5
make verify-silver-relying-party-policy-pack-v0-3-5
```

The `run-silver-relying-party-policy-pack-v0-3-5` target builds the
v0.3.5 package into
`/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/` with
`--force --self-validate`, then runs the v0.3.5 verifier against the
published manifest.

The `verify-silver-relying-party-policy-pack-v0-3-5` target runs the
dedicated regression test, which exercises 47 ordered cases (4
positive-path + 24 canonical verifier reason mutations + 11 duplicate
manifest-invalid mutations + 5 runner-only refusal cases + 1 runner
relay-of-verifier-failure case + 1 taxonomy gate + 1 scoped sha256
snapshot).

## Relying-party policy pack package layout

```
/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/
├── silver-relying-party-policy-pack.json                      (subject [0])
├── silver-relying-party-policy-pack-conformance-report.json   (subject [1])
└── silver-relying-party-policy-pack-manifest.json             (2-subject anchor)
```

## Closed enum surface

The policy pack body is governed by these closed enum vocabularies
(declared in `schemas/silver-relying-party-policy-pack-v0.1.0.md` and
enforced inside the verifier; see also the four fixture variants):

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
| `hard_stops[].overridable_by_exception` | literal `false` |

## Fixture variants

| File | Variant |
|---|---|
| `policy-pack.json` | Canonical pack; all sections populated with representative values |
| `policy-pack-with-exception.json` | Multi-exception block; `record_and_pause_reuse` postures; tighter rejection set |
| `policy-pack-with-warning-policy.json` | Two attestors, two issuers, rich `warning_treatment.warnings`, three hard stops; `record_and_block_reuse` / `record_and_block_until_superseded` postures |
| `policy-pack-with-freshness-windows.json` | Tight freshness windows (2 h); no attestation required; `record_only` supersession |

## Non-claims

- The relying-party policy pack package is not an approval.
- The relying-party policy pack package is not an audit.
- The relying-party policy pack package is not a certification.
- The relying-party policy pack package is not a regulator,
  auditor, or third-party endorsement of the relying party or its
  policy.
- The packaged conformance report describes only that the policy
  pack satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any upstream Silver evidence.
- The policy pack's `silver_handoff_requirements` /
  `verifier_requirements` / `issuer_requirements` /
  `revocation_requirements` / `freshness_requirements` are
  hand-authored policy text; v0.3.5 does not evaluate any specific
  upstream handoff, verifier, issuer, or evidence package against
  them.
- The policy pack's `exceptions`, `hard_stops`, and `warning_treatment`
  blocks describe local relying-party policy; they do not adjudicate
  any specific challenge, withdrawal, supersession, or warning event.
- The v0.3.5 package is unsigned: it ships local hash anchors only.
- v0.3.5 does not extend the substance of any earlier-release Silver
  evidence, does not authorize production reliance, and does not
  advance the Gold boundary.
