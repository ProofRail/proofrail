# Silver Demo 014 — Registry Lite (v0.3.7)

This demo is the deterministic, local Silver Registry Lite package
that ProofRail v0.3.7 derives from a single hand-authored input:

- the canonical registry-lite fixture
  (`fixtures/silver-registry-lite-v0.3.7/registry-lite.json`).

It answers a narrow question:

> Can a hand-authored registry-lite document — declaring at least one
> entry for each of the six Silver entity roles (issuer, verifier,
> relying party, policy authority, revocation source, protected
> action authority) under a closed enum / status / scope / role-
> specific vocabulary — be structurally validated against 24 ordered
> checks under that closed vocabulary, paired with a deterministically
> re-derived conformance report (24 pass entries, byte-identical
> re-derivation), and packaged alongside a 2-subject manifest — such
> that an independent Silver reviewer can re-run the unchanged v0.3.7
> verifier and re-derive every check without claiming that the
> registry constitutes production PKI, a certificate authority, a
> legal identity registry, an identity-proofing record, a federation
> registry, a regulator approval, an auditor approval, a third-party
> endorsement, a Gold artifact, an evaluation of any specific
> upstream Silver evidence against the registry, or a reliance
> instrument issued, transferred, or accepted against the registry?

It does **not** answer:

- Is the registry production PKI?
- Is the registry a certificate authority or certification authority?
- Is the registry a legal identity registry?
- Is the registry an identity-proofing record?
- Is the registry a federation registry or trust federation?
- Has the registry been approved by a regulator, auditor, or third
  party?
- Has any specific upstream Silver evidence (composed-gateway,
  trace-binding, acceptance record, revocation-challenge drill,
  acceptance-handoff, handoff-inspection, control-crosswalk, etc.)
  been re-evaluated against this registry in this demo?
- Has any reliance instrument been issued, transferred, or accepted
  against the registry?
- Is the registry legally enforceable?
- Is the registry Gold-conformant?

## What the demo does

1. Validates the `--input-registry` argv through 5 Phase A preflight
   checks (relative-path-only, no `..`, file exists, file is a
   regular file, file is valid JSON). Phase A emits only the 5
   approved runner-only refusal reasons: `runner_input_path_missing`,
   `runner_input_path_forbidden`, `runner_input_file_missing`,
   `runner_input_read_failed`, `runner_input_json_invalid`.
2. Stages output under `<output-dir>.staging.<pid>` and byte-copies
   the registry body to `<staging>/registry-lite.json`.
3. Deterministically re-derives the conformance report (24 pass
   entries, one per approved verifier check) as canonical JSON
   bytes (`sort_keys=True`, `separators=(",",":"))` with a trailing
   newline, and writes it to
   `<staging>/silver-registry-lite-conformance-report.json`.
4. Writes the 2-subject manifest at
   `<staging>/silver-registry-lite-manifest.json`. The manifest
   carries `subjects[0]` = registry body (role `registry_lite`) and
   `subjects[1]` = conformance report (role `conformance_report`),
   each with `sha256` (`sha256:<64hex>`) and `size_bytes`. The
   manifest also carries `proofrail_release:
   silver.registry_lite.v0.3.7`, `hash_algorithm: sha256`, and a
   `registry_id` cross-anchored to the registry body.
5. If `--self-validate`, subprocess-invokes the v0.3.7 verifier
   against the staged manifest BEFORE the atomic publish. Any
   verifier failure is relayed UNCHANGED (the verifier's own stable
   reason is emitted; the runner does NOT wrap it in a sixth
   runner-only code). On self-validation failure the staging
   directory is removed and `<output-dir>` is left untouched.
6. Atomic publish: only AFTER a successful staging build (and, if
   `--self-validate`, a successful self-validation) does the runner
   remove an existing `--output-dir` (requires `--force`) and
   `os.replace()` the staging directory into place.

The v0.3.7 verifier runs 24 ordered checks against the 2-subject
manifest. Checks fire in the documented order with no masking: 24
structural checks against the registry body and manifest, then
conformance-report parse and byte-identical re-derivation. A
re-derivation disagreement is funnelled back to
`registry_manifest_invalid`; no twenty-fifth public reason is
introduced. The verifier emits only the 24 approved verifier-side
failure reasons listed in the schema and release doc. It never
invents a sixth runner-only wrapper code on a relayed failure.

## Commands

```bash
make run-silver-registry-lite-v0-3-7
make verify-silver-registry-lite-v0-3-7
```

The `run-silver-registry-lite-v0-3-7` target builds the v0.3.7
package into `/tmp/proofrail-silver-registry-lite-v0.3.7/` with
`--force --self-validate`, then runs the v0.3.7 verifier against the
published manifest.

The `verify-silver-registry-lite-v0-3-7` target runs the dedicated
regression test, which exercises 48 ordered cases (4 positive-path +
24 canonical verifier reason mutations + 11 duplicate
manifest-invalid mutations + 6 runner-only refusal exercises covering
5 distinct runner-only reasons (ro1, ro2, ro2b, ro3..ro5) + 1
runner-relay-of-verifier-failure case + 1 taxonomy gate + 1 scoped
sha256 snapshot).

## Registry Lite package layout

```
/tmp/proofrail-silver-registry-lite-v0.3.7/
├── registry-lite.json                                        (subject [0])
├── silver-registry-lite-conformance-report.json              (subject [1])
└── silver-registry-lite-manifest.json                        (2-subject anchor)
```

## Closed enum surface

The registry body is governed by these closed enum vocabularies
(declared in `schemas/silver-registry-lite-v0.1.0.md` and enforced
inside the verifier; see also the three fixture variants):

| Field path | Closed enum |
|---|---|
| `document_type` | `proofrail.silver.registry_lite` |
| `schema_version` | `v0.1.0` |
| `profile` | `silver.registry_lite.v0.3.7` |
| `registry_scope` | `demo`, `staging`, `production`, `multi_environment`, `out_of_scope` |
| entity `role` | `issuer`, `verifier`, `relying_party`, `policy_authority`, `revocation_source`, `protected_action_authority` |
| entity `status` | `active`, `provisional`, `deprecated`, `withdrawn`, `out_of_scope` |
| `key_references[].algorithm` | `ed25519`, `ecdsa_p256`, `ecdsa_p384`, `rsa_2048`, `rsa_3072`, `rsa_4096` |
| `key_references[].key_reference_type` | `local_fingerprint`, `local_pem_path`, `local_jwk_path` |
| `key_bindings[].binding_purpose` | `issue_evidence`, `verify_evidence`, `sign_policy`, `sign_revocation`, `sign_authority_decision` |
| `verifier.verifier_posture` | `independent`, `self_attested`, `demo_only` |
| `policy_authority.authority_boundary` | `local_demo`, `local_enterprise`, `multi_party_governed` |
| `revocation_source.source_type` | `local_list`, `signed_revocation_record`, `challenge_drill_outcome` |
| `revocation_source.status_mode` | `pull`, `push`, `snapshot` |
| `protected_action_authority.delegation_boundary` | `principal_only`, `scoped_delegation`, `joint_principal`, `delegation_with_break_glass` |
| `trust_relationships[].relationship_verb` | `recognizes_issuer`, `accepts_verifier_output`, `references_policy_authority`, `consults_revocation_source`, `delegates_to_protected_action_authority`, `declares_role_binding` |
| `version_bindings[].upstream_id` | closed Silver upstream_id set (v0.2.1..v0.3.6) |

## Fixture variants

| File | Variant |
|---|---|
| `registry-lite.json` | Canonical pack: one entry per each of the six role types; empty `trust_relationships`; non-empty `version_bindings`; the issuer entry exercises `key_references[]` with `key_reference_type: local_fingerprint` and `key_bindings[]` with `binding_purpose: issue_evidence`. |
| `registry-lite-with-trust-relationships.json` | Exercises non-empty `trust_relationships[]` across all six closed `relationship_verb` values. |
| `registry-lite-with-revocation-source.json` | Exercises a full revocation-source entry with `source_type: signed_revocation_record`, `key_reference_type: local_pem_path`, and `binding_purpose: sign_revocation`. |

## Non-claims

- The registry-lite package is not a production PKI, certificate
  authority, certification authority, legal identity registry,
  identity-proofing record, federation registry, trust federation,
  or production trust registry.
- The package is not a regulator, auditor, or third-party
  endorsement and is not a certification, compliance attestation, or
  audit-readiness assertion.
- The packaged conformance report describes only that the registry
  body satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any specific upstream Silver
  evidence.
- v0.3.7 does not re-evaluate any specific upstream Silver evidence
  (composed-gateway, trace-binding, acceptance record,
  revocation-challenge drill, acceptance-handoff,
  handoff-inspection, control-crosswalk, etc.) against the registry.
  References are structural pointers only.
- v0.3.7 does not issue, transfer, or accept any reliance instrument
  against the registry.
- The v0.3.7 package is unsigned: it ships local hash anchors only.
- v0.3.7 does not extend the substance of any earlier-release Silver
  evidence, does not authorize production reliance, is not legally
  enforceable, is not a Gold artifact, and does not advance the
  Gold boundary.
