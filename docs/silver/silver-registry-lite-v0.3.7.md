# Silver Registry Lite — v0.3.7

**Status:** Draft / ProofRail v0.3.7
**Release thesis:** ProofRail v0.3.7 introduces a deterministic local
Silver evidence primitive — a *registry lite* — paired with a
byte-for-byte re-derivable *conformance report* and a 2-subject
manifest. The registry hand-authors a closed-vocabulary set of Silver
entity roles (issuer, verifier, relying party, policy authority,
revocation source, protected action authority), optional trust
relationships between those roles under a closed verb vocabulary, and
a closed set of upstream Silver version bindings. An independent
Silver reviewer can re-run the unchanged v0.3.7 verifier against the
manifest and re-derive every structural check — without claiming that
the registry constitutes production PKI, a certificate authority, a
legal identity registry, an identity-proofing record, a federation
registry, a regulator approval, an auditor approval, a third-party
endorsement, a Gold artifact, an evaluation of any specific upstream
Silver evidence against the registry, or a reliance instrument
issued, transferred, or accepted against the registry.

---

## v0.3.7 thesis

> A package owner can hand-author a structured local registry-lite
> document declaring at least one entry for each of the six Silver
> entity roles under closed enums for `role`, `status`,
> `registry_scope`, `release_binding`, key-reference type, key-binding
> purpose, and role-specific fields; the v0.3.7 runner can byte-copy
> the registry into a deterministic 2-subject package alongside a
> re-derivable conformance report with 24 pass entries; and the
> v0.3.7 verifier can re-run 24 ordered structural checks on the
> registry body and byte-compare the re-derived report against the
> bundled report — while preserving the boundary that v0.3.7 does
> **not** assert production PKI, certificate authority, legal
> identity, identity proofing, federation authority, certification,
> compliance, audit readiness, regulator approval, auditor approval,
> production authorization, legally enforceable instrument, runtime
> truth, transferred trust, Gold governance, an evaluation of
> upstream Silver evidence against the registry, or any reliance
> instrument.

## Registry-lite boundary

> A v0.3.7 registry-lite package is **not** a production PKI, a
> certificate authority, a certification authority, an identity-
> proofing record, a federation registry, a legal identity registry,
> a regulator action, an auditor action, a third-party endorsement, a
> Gold artifact, an upstream Silver evidence re-evaluation, or an
> authorization for production reuse. It is a deterministic local
> evidence artifact recording that a package owner has hand-authored
> a structured registry of Silver entity roles, that the structure
> satisfies a fixed set of 24 ordered structural checks, and that an
> independent reviewer can re-derive the same conformance report
> byte-for-byte from the registry body alone.

v0.3.7 answers:

```
Can a package owner hand-author a structured local registry
  declaring at least one entry for each of the six Silver entity
  roles (issuer, verifier, relying_party, policy_authority,
  revocation_source, protected_action_authority) under a closed
  role enum, a closed status enum, a closed registry_scope enum,
  and a closed release_binding enum?
Can the runner byte-copy the registry body into a deterministic
  local 2-subject package?
Can the runner deterministically re-derive a 24-entry conformance
  report whose canonical-JSON byte image depends only on the
  registry body?
Can the runner refuse five distinct preflight failures
  (path missing, path forbidden, file missing, read failed, JSON
  invalid) with stable runner-only refusal reasons that the
  downstream verifier never re-emits?
Can the runner relay the v0.3.7 verifier's own failure UNCHANGED on
  --self-validate, without wrapping it in a sixth runner-only code?
Can the verifier independently re-run 24 ordered structural checks
  on the registry body and the manifest, including:
    document_type / schema_version / profile sanity,
    registry_authority / registry_id identity,
    entities[] non-empty list,
    each entity entry's display_label / role / status /
      effective_period,
    each entity entry's identifier grammar
      (lowercase dotted identifier),
    each entity entry's key_references[] (closed algorithm enum,
      closed key_reference_type enum, sha256:<64hex> fingerprint
      grammar where required, relative paths only with no `..`,
      no private-key fields),
    each entity entry's key_bindings[] (key_id resolves within the
      same entity, binding_purpose in the closed binding-purpose
      enum),
    each role-typed entity entry's role-specific block (issuer,
      verifier, relying_party, policy_authority, revocation_source,
      protected_action_authority) under closed enums,
    trust_relationships[] entries (closed verb enum, from/to
      resolve in entities[]),
    version_bindings[] entries (closed upstream_id set, closed
      upstream_version set),
    scope_limitations and non_claims presence,
    a 36-token prohibited-claim guard outside scope_limitations and
      non_claims?
Can the verifier byte-compare the bundled conformance report against
  a re-derivation drawn solely from the verified registry body and
  reject any disagreement?
```

v0.3.7 does **not** answer:

```
Is the registry production PKI?
Is the registry a certificate authority or certification authority?
Is the registry a legal identity registry?
Is the registry an identity-proofing record?
Is the registry a federation authority or trust federation?
Has the registry been approved by a regulator?
Has the registry been approved by an auditor?
Has the registry been endorsed by any third party?
Has any specific upstream Silver evidence (composed-gateway,
  trace-binding, acceptance-record, revocation-challenge drill,
  acceptance-handoff, handoff-inspection, control-crosswalk, etc.)
  been re-evaluated against this registry in this release?
Has any reliance instrument been issued, transferred, or accepted
  against this registry?
Is the registry legally enforceable on the package owner or any
  relying party?
Is the registry Gold-conformant?
```

---

## Schemas

Three new v0.1.0 schemas ship with v0.3.7:

```
schemas/silver-registry-lite-v0.1.0.md
schemas/silver-registry-lite-manifest-v0.1.0.md
schemas/silver-registry-lite-conformance-report-v0.1.0.md
```

### Registry body (`proofrail.silver.registry_lite`)

The hand-authored evidence primitive. Required top-level fields:

```
document_type, schema_version, profile, registry_id, generated_at,
registry_scope, release_binding, registry_authority, entities,
trust_relationships, version_bindings, scope_limitations, non_claims
```

### Manifest (`proofrail.silver.registry_lite_manifest`)

A 2-subject anchor over the registry body and the conformance report
in fixed roles and fixed order:

```
[0] registry-lite.json                                role=registry_lite
[1] silver-registry-lite-conformance-report.json      role=conformance_report
```

Each subject carries `sha256` (`sha256:<64hex>`) and `size_bytes`.
The manifest carries `proofrail_release: silver.registry_lite.v0.3.7`,
`hash_algorithm: sha256`, and a `registry_id` that the verifier
cross-anchors against the registry body. There is no self-referential
manifest hash subject; the manifest is itself the anchor.

### Conformance report (`proofrail.silver.registry_lite_conformance_report`)

A re-derivable record with 24 pass entries (one per approved verifier
check). The runner emits the report as canonical JSON bytes
(`sort_keys=True`, `separators=(",",":"))` with a trailing newline)
so the verifier can byte-compare its own re-derivation against the
bundled bytes.

---

## Verifier — 24 stable failure reasons (verifier-side)

The v0.3.7 verifier runs 24 ordered checks in fixed order with no
masking. Each check emits exactly one stable failure reason; the
verifier never invents a sixth wrapper code on a relayed failure.

| Check | Reason |
|---|---|
| `check_01` | `registry_manifest_invalid` |
| `check_02` | `registry_not_object` |
| `check_03` | `registry_schema_invalid` |
| `check_04` | `registry_profile_unsupported` |
| `check_05` | `registry_identity_invalid` |
| `check_06` | `registry_authority_invalid` |
| `check_07` | `registry_entity_set_invalid` |
| `check_08` | `registry_entity_entry_invalid` |
| `check_09` | `registry_entity_identifier_invalid` |
| `check_10` | `registry_role_invalid` |
| `check_11` | `registry_status_invalid` |
| `check_12` | `registry_effective_period_invalid` |
| `check_13` | `registry_key_reference_invalid` |
| `check_14` | `registry_key_binding_invalid` |
| `check_15` | `issuer_entry_invalid` |
| `check_16` | `verifier_entry_invalid` |
| `check_17` | `relying_party_entry_invalid` |
| `check_18` | `policy_authority_entry_invalid` |
| `check_19` | `revocation_source_entry_invalid` |
| `check_20` | `protected_action_authority_entry_invalid` |
| `check_21` | `trust_relationship_invalid` |
| `check_22` | `version_binding_invalid` |
| `check_23` | `non_claims_missing` |
| `check_24` | `prohibited_registry_claim_present` |

After the 24 structural checks the verifier parses the bundled
conformance report at subject [1], deterministically re-derives the
expected canonical-JSON byte image from the verified registry body,
and byte-compares the two. Disagreement surfaces as the verifier-side
reason `registry_manifest_invalid` (subject [1] does not describe a
passing verification of this registry). This is the non-masking
funnel: no twenty-fifth public reason is introduced.

The verifier also cross-anchors `manifest.registry_id` against the
registry body's `registry_id`; disagreement surfaces as
`registry_manifest_invalid`.

---

## Runner — 5 stable runner-only refusal reasons

The runner's Phase A preflight validates the `--input-registry` argv
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

On `--self-validate` the runner subprocess-invokes the v0.3.7
verifier against the staged manifest BEFORE the atomic publish.
**The runner relays the verifier's OWN stable reason UNCHANGED.** It
does NOT wrap a verifier failure in a sixth runner-only code. The
staging directory is removed on self-validation failure and
`--output-dir` is left untouched. There is no sixth wrapper code
anywhere in the v0.3.7 taxonomy beyond the 5 runner-only refusal
codes listed above; the regression test explicitly asserts that no
such sixth wrapper code is ever emitted on a relayed verifier
failure.

---

## Closed enum surface

| Field path | Closed enum |
|---|---|
| `document_type` | `proofrail.silver.registry_lite` |
| `schema_version` | `v0.1.0` |
| `profile` | `silver.registry_lite.v0.3.7` |
| `registry_scope` | `demo`, `staging`, `production`, `multi_environment`, `out_of_scope` |
| `release_binding` | `silver.registry_lite.v0.3.7` |
| entity `role` | `issuer`, `verifier`, `relying_party`, `policy_authority`, `revocation_source`, `protected_action_authority` |
| entity `status` | `active`, `provisional`, `deprecated`, `withdrawn`, `out_of_scope` |
| `key_references[].algorithm` | `ed25519`, `ecdsa_p256`, `ecdsa_p384`, `rsa_2048`, `rsa_3072`, `rsa_4096` |
| `key_references[].key_reference_type` | `local_fingerprint`, `local_pem_path`, `local_jwk_path` |
| `key_bindings[].binding_purpose` | `issue_evidence`, `verify_evidence`, `sign_policy`, `sign_revocation`, `sign_authority_decision` |
| `issuer.issuer_scope` | closed subset (e.g. `silver_evidence_only`, `silver_evidence_with_attestation`) |
| `issuer.signed_artifact_types` | closed subset of v0.2.6/v0.3.x artifact_type |
| `issuer.supported_profiles` | closed v0.2.x/v0.3.x profile subset |
| `verifier.verifier_profiles` | closed v0.3.x profile subset |
| `verifier.verifier_posture` | `independent`, `self_attested`, `demo_only` |
| `relying_party.reliance_scope` | closed enum (e.g. `demo_only`, `staging_only`, `multi_environment`) |
| `policy_authority.policy_scope` | closed enum |
| `policy_authority.authority_boundary` | `local_demo`, `local_enterprise`, `multi_party_governed` |
| `revocation_source.source_type` | `local_list`, `signed_revocation_record`, `challenge_drill_outcome` |
| `revocation_source.status_mode` | `pull`, `push`, `snapshot` |
| `revocation_source.supported_subject_scope` | closed enum |
| `protected_action_authority.protected_action_scope` | closed enum |
| `protected_action_authority.delegation_boundary` | `principal_only`, `scoped_delegation`, `joint_principal`, `delegation_with_break_glass` |
| `trust_relationships[].relationship_verb` | `recognizes_issuer`, `accepts_verifier_output`, `references_policy_authority`, `consults_revocation_source`, `delegates_to_protected_action_authority`, `declares_role_binding` |
| `version_bindings[].upstream_id` | closed v0.2.1..v0.3.6 Silver upstream_id set |
| `version_bindings[].upstream_version` | closed v0.2.1..v0.3.6 upstream_version set |

---

## Prohibited-registry-claim guard

The verifier's recursive scan rejects any string value OUTSIDE
`scope_limitations` and `non_claims` that contains any of these 36
forbidden positive tokens (case-insensitive substring match):

```
production PKI, certificate authority, certification authority,
legal identity, legally authoritative identity,
identity proofing, proofed identity,
federated trust, trust federation,
production trust registry, authoritative trust registry,
certified, certification, compliant, compliance,
legally enforceable, legal enforceability,
production authorized, production authorization,
authorized for production,
regulator approved, regulator approval, approved by regulator,
auditor approved, auditor approval, approved by auditor,
audit ready, operating effectiveness, design effectiveness,
runtime truth, proves runtime truth,
transferred trust, trust transferred,
gold governed reliance, gold governance, gold accepted,
gold certified
```

The `scope_limitations` / `non_claims` escape applies only to those
two lists by exact key match; nested objects with the same key
elsewhere do not benefit.

---

## Package layout

```
<output-dir>/
├── registry-lite.json                                        (subject [0])
├── silver-registry-lite-conformance-report.json              (subject [1])
└── silver-registry-lite-manifest.json                        (2-subject anchor)
```

---

## Fixtures

Three hand-authored passing registries ship under
`fixtures/silver-registry-lite-v0.3.7/`:

| File | Variant |
|---|---|
| `registry-lite.json` | Canonical pack: one entry per each of the six role types; empty `trust_relationships`; non-empty `version_bindings`; full `scope_limitations` and `non_claims`. The issuer entry also exercises `key_references[]` with `key_reference_type: local_fingerprint` and `key_bindings[]` with `binding_purpose: issue_evidence`. |
| `registry-lite-with-trust-relationships.json` | Exercises non-empty `trust_relationships[]` across all six closed `relationship_verb` values. |
| `registry-lite-with-revocation-source.json` | Exercises a full revocation-source entry with `source_type: signed_revocation_record`, `key_reference_type: local_pem_path`, and `binding_purpose: sign_revocation`. |

Every fixture is a passing registry: parses to a top-level JSON
object, satisfies the 24 ordered structural checks, contains
non-empty `scope_limitations` and `non_claims`, and contains no
prohibited claim tokens outside those two blocks.

---

## Tools

```
tools/silver/build_silver_registry_lite_v0_1_0.py
tools/silver/verify_silver_registry_lite_v0_1_0.py
```

Pure-stdlib. No new runtime dependencies for v0.3.7.

---

## Make targets

```
make run-silver-registry-lite-v0-3-7
make verify-silver-registry-lite-v0-3-7
```

`verify-silver-all` chains the v0.3.7 regression test after v0.3.6.

---

## Regression test

```
tests/test_silver_registry_lite_v0_3_7.sh
```

48 ordered exercises:

- 4 positive-path checks (pristine build + verify, inline manifest
  layout, inline conformance report)
- 24 canonical verifier reason mutations (one per approved reason),
  hash-first re-anchored
- 11 duplicate manifest-invalid mutations (all routed to
  `registry_manifest_invalid`, including subject [0] / [1] absolute
  path, subject [0] / [1] traversal, subject [0] file missing,
  subject [0] `size_bytes` mismatch, subject [0] `sha256` mismatch,
  wrong subject count, subject [0] role wrong, `registry_id`
  cross-anchor mismatch, and the non-masking post-structural
  conformance-report disagreement)
- 6 runner-only refusal cases (one per Phase A reason; ro2 and ro2b
  both exercise `runner_input_path_forbidden` for absolute and
  parent-traversal inputs respectively)
- 1 runner-relay-of-verifier-failure case (verifier reason relayed
  UNCHANGED; no sixth wrapper)
- 1 taxonomy gate (TG1) over all v0.3.7-owned files and the
  v0.3.7-anchored sections of README.md, CLAUDE.md,
  `tools/silver/README.md`,
  `docs/silver/silver-artifact-map-v0.1.7.md`,
  `docs/silver/silver-limitations-and-non-claims.md`, and
  `docs/gold/gold-boundary-v0.2.5.md`
- 1 scoped sha256 snapshot before / after

---

## Limitations and non-claims

- The v0.3.7 registry-lite package is not a production PKI,
  certificate authority, certification authority, legal identity
  registry, identity-proofing record, federation registry, trust
  federation, or production trust registry.
- The package is not a regulator, auditor, or third-party
  endorsement and is not a certification, compliance attestation, or
  audit-readiness assertion.
- The packaged conformance report describes only that the registry
  body satisfies the 24 ordered structural checks; it does not
  describe a substantive review of any specific upstream Silver
  evidence in this release.
- v0.3.7 does not re-evaluate any specific upstream Silver evidence
  (composed-gateway, trace-binding, acceptance-record,
  revocation-challenge drill, acceptance-handoff,
  handoff-inspection, control-crosswalk, etc.) against the registry.
  References are structural pointers only.
- v0.3.7 does not issue, transfer, or accept any reliance instrument
  against the registry.
- v0.3.7 ships local hash anchors only; the package is unsigned.
- v0.3.7 does not authorize production reliance, is not legally
  enforceable, is not a Gold artifact, and does not advance the Gold
  boundary.
