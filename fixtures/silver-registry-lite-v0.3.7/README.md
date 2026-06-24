# Silver Registry Lite Fixtures (v0.3.7)

Hand-authored static JSON fixtures for the Silver Registry Lite package
(`silver.registry_lite.v0.3.7`).

| File | Variant |
|---|---|
| `registry-lite.json` | Canonical pack: one entry per each of the 6 role types (`issuer`, `verifier`, `relying_party`, `policy_authority`, `revocation_source`, `protected_action_authority`); empty `trust_relationships`; non-empty `version_bindings`; full `scope_limitations` and `non_claims`. The issuer entry also exercises `key_references[]` with `key_reference_type: local_fingerprint` and `key_bindings[]` with `binding_purpose: issue_evidence`. |
| `registry-lite-with-trust-relationships.json` | Exercises non-empty `trust_relationships[]` across all six closed `relationship_verb` values. |
| `registry-lite-with-revocation-source.json` | Exercises a full revocation-source entry with `source_type: signed_revocation_record`, `key_reference_type: local_pem_path`, and `binding_purpose: sign_revocation`. |

## Non-claims

These fixtures are example data only. They do not constitute production PKI
artifacts, certificate-authority records, federation registries, legal
identity records, identity-proofing records, regulator approvals, auditor
approvals, third-party endorsements, certifications, compliance
attestations, audit-ready postures, production authorizations, legally
enforceable instruments, runtime-truth oracles, transferred trust, governed
reliance, or Gold artifacts.
