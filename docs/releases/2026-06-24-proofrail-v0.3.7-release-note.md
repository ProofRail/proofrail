# ProofRail Silver v0.3.7 Release Note

## Registry Lite

ProofRail Silver v0.3.7 adds **Registry Lite**, the final planned Silver release before the Minimal Gold v0.4.0 demo.

Registry Lite introduces deterministic local registry fixtures for the identities and role bindings needed to compose governed reliance in the next release. It gives the demo a structured way to refer to issuers, verifiers, relying parties, policy authorities, revocation sources, and protected-action authorities without claiming production PKI, federation, legal identity, certification, or Gold governance.

## Why This Matters

The Silver series has been building toward a clear boundary:

> Silver verifies evidence packages.
> Gold governs reliance on verified evidence.

v0.3.7 completes the current pre-Gold substrate by adding the local registry layer needed to bind the pieces together in a deterministic demo environment.

With v0.3.7, the v0.4.0 Minimal Gold demo can compose:

- Silver verification results;
- Silver acceptance handoff artifacts;
- challenge and withdrawal records;
- relying-party policy packs;
- protected-action catalog and control crosswalk artifacts;
- local Registry Lite identities and role bindings.

That makes v0.4.0 ready to demonstrate the first Minimal Gold boundary:

> A Silver verification result becomes an accepted, rejected, challenged, withdrawn, or superseded governed reliance decision under an explicit relying-party policy.

## What v0.3.7 Adds

Registry Lite adds a local, hash-anchored Silver package with:

- one registry fixture containing at least one entry for each of six entity roles;
- local identifiers for issuers, verifiers, relying parties, policy authorities, revocation sources, and protected-action authorities;
- closed-vocabulary role, status, scope, key-reference, key-binding, trust-relationship, and version-binding fields;
- optional local trust relationships among registered entities;
- local version bindings to the relevant Silver releases;
- explicit limitations and non-claims;
- a two-subject manifest binding the registry and a re-derived conformance report.

The package remains deterministic and local. It does not query live services and does not introduce production identity infrastructure.

## Verification Model

v0.3.7 follows the hardened v0.3.x verification pattern:

- pure-stdlib runner and verifier;
- staged output and atomic publish;
- optional `--self-validate`;
- hash-first manifest validation;
- non-masking verifier order;
- byte-for-byte re-derived conformance report;
- strict runner/verifier reason separation;
- hard TG1 taxonomy gate;
- scoped source snapshot test.

The verifier exposes exactly 24 stable verifier-side failure reasons.

The runner exposes exactly 5 runner-only refusal reasons.

The regression suite covers 48 exercises:

- 4 positive-path exercises;
- 24 canonical verifier-reason exercises;
- 11 duplicate `registry_manifest_invalid` exercises;
- 6 runner-only refusal exercises covering 5 distinct runner-only reasons;
- 1 runner relay of verifier failure;
- 1 TG1 taxonomy gate;
- 1 scoped source snapshot.

## Guardrails Preserved

v0.3.7 continues the guardrails added during the late Silver series:

- public failure/refusal reason names are treated as release contracts;
- verifier reasons and runner-only refusals are separate public surfaces;
- no OR-accepted expected reasons are allowed in regression tests;
- duplicate manifest-invalid cases are reported separately from canonical reason coverage;
- runner self-validation relays verifier reasons without inventing a sixth runner-only refusal;
- path traversal and absolute path handling are explicitly tested;
- prohibited overclaim vocabulary is scanned outside limitations and non-claims blocks;
- narrative docs are scanned for reason-like token drift.

These guardrails were added because prior releases showed that coding assistants can drift from stable public reason names unless the taxonomy is executable.

## What v0.3.7 Does Not Claim

Registry Lite is not:

- production PKI;
- a certificate authority;
- a certification authority;
- legal identity proofing;
- a federation registry;
- a trust federation;
- regulator approval;
- auditor approval;
- compliance certification;
- audit readiness;
- production authorization;
- runtime truth;
- transferred trust;
- Gold governance;
- Gold governed reliance.

v0.3.7 packages local registry declarations. It does not evaluate any specific upstream Silver evidence against the registry, issue or transfer reliance, or make any governed reliance decision.

## Verification Summary

The v0.3.7 implementation was verified with:

- `make run-silver-registry-lite-v0-3-7`;
- `make verify-silver-registry-lite-v0-3-7`;
- `make verify-silver-all`;
- `python3 -m pytest tests/test_proofrail_claim.py`;
- `git diff --check`.

The targeted v0.3.7 regression suite passed 48/48 exercises. The full Bronze and Silver verification chain passed through v0.3.7.

## Silver Series Status

v0.3.7 is the last planned Silver release for now.

The current Silver ladder now includes:

- v0.2.0 Silver relying-party profile;
- v0.2.1 through v0.2.5 multi-principal and multi-agent Silver foundations;
- v0.2.6 evidence source adapter profile;
- v0.2.7 composed gateway evidence;
- v0.2.8 relying-party acceptance record;
- v0.2.9 revocation and challenge drill;
- v0.3.0 Silver acceptance handoff;
- v0.3.1 Silver handoff inspector and Gold gap inventory;
- v0.3.2 trace binding profile;
- v0.3.3 adapter pilot package;
- v0.3.4 challenge and withdrawal record primitives;
- v0.3.5 relying-party policy pack;
- v0.3.6 control crosswalk and protected action catalog;
- v0.3.7 Registry Lite.

## What Comes Next

The next planned release is **v0.4.0 Minimal Gold Governed Reliance Demo**.

Minimal Gold should not expand ProofRail into a broad governance platform. Its job is narrower:

> Turn a Silver verification result into a governed reliance decision under an explicit relying-party policy.

The v0.4.0 demo should show:

- clean acceptance;
- policy rejection despite Silver verification passing;
- challenge filed;
- withdrawal or supersession after challenge, revocation, or evidence defect.

Full Gold and Platinum remain concept-note territory for now. They can be described as future direction, but ProofRail realized should stay grounded in the primitives that have now been built and tested.
