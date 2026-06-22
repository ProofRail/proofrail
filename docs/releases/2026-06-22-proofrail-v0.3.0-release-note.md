# ProofRail v0.3.0 - Silver Acceptance Handoff

Release date: 2026-06-22

Git tag: `v0.3.0`

ProofRail v0.3.0 adds a portable Silver acceptance handoff package.

v0.2.7 introduced composed Silver evidence over simulated external gateway evidence. v0.2.8 added a relying-party acceptance record. v0.2.9 added a revocation/challenge drill over that acceptance record. v0.3.0 packages that completed Silver chain into a single hash-anchored handoff artifact.

The narrow claim is:

> ProofRail can package the completed Silver acceptance chain for independent handoff review, binding composed evidence, relying-party acceptance, and post-acceptance review posture without certifying the chain, transferring reliance, adjudicating challenges, approving production use, or executing Gold governance.

## What Changed

This release adds the Silver Acceptance Handoff.

The handoff package binds:

- v0.2.7 composed gateway evidence;
- v0.2.8 relying-party acceptance;
- v0.2.9 revocation/challenge drill posture;
- a v0.3.0 handoff summary;
- a v0.3.0 handoff manifest.

The handoff runner copies the full nested v0.2.7, v0.2.8, and v0.2.9 package roots into one portable package, verifies each layer with the existing unchanged verifier or validator, checks cross-package chain binding, derives a handoff summary, and emits a deterministic manifest.

The handoff verifier revalidates the nested packages, recomputes hashes, re-derives the chain binding, checks the handoff summary, rejects posture downgrades, and rejects overclaims.

## New Artifacts

Added schemas:

- `schemas/silver-acceptance-handoff-summary-v0.1.0.md`
- `schemas/silver-acceptance-handoff-manifest-v0.1.0.md`

Added documentation:

- `docs/silver/silver-acceptance-handoff-v0.3.0.md`
- `demos/silver-demo-007-acceptance-handoff/README.md`
- `demos/silver-demo-007-acceptance-handoff/demo-walkthrough.md`
- `fixtures/silver-acceptance-handoff-v0.3.0/README.md`

Added tools:

- `tools/silver/build_silver_acceptance_handoff_v0_1_0.py`
- `tools/silver/verify_silver_acceptance_handoff_v0_1_0.py`

Added test:

- `tests/test_silver_acceptance_handoff_v0_3_0.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `README.md`
- `tools/silver/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`
- `docs/gold/gold-boundary-v0.2.5.md`

## Handoff Package

The runtime handoff package contains:

```text
composed-gateway-evidence/
acceptance-package/
revocation-challenge-drill/
silver-acceptance-handoff-summary.json
silver-acceptance-handoff-manifest.json
```

The handoff manifest hashes exactly four subjects in fixed order:

- `composed-gateway-evidence/composed-gateway-evidence-manifest.json`
- `acceptance-package/acceptance-package-manifest.json`
- `revocation-challenge-drill/revocation-challenge-drill-manifest.json`
- `silver-acceptance-handoff-summary.json`

The nested package manifests continue to bind their own package contents. v0.3.0 binds the package-level chain and the handoff summary.

## Runner

Example:

```bash
make run-silver-acceptance-handoff-v0-3-0
```

The runner:

- runs or consumes the v0.2.7 composed gateway evidence package;
- consumes the v0.2.8 relying-party acceptance package;
- consumes the v0.2.9 revocation/challenge drill package;
- invokes the unchanged v0.2.7 verifier, v0.2.8 validator, and v0.2.9 verifier;
- copies all three package roots into the handoff package;
- checks four v0.3.0-owned chain bindings;
- derives `silver-acceptance-handoff-summary.json`;
- emits `silver-acceptance-handoff-manifest.json`;
- optionally self-validates against the staging directory before atomic publish.

Refused runs leave no partial handoff package behind.

## Verifier

Example:

```bash
python3 tools/silver/verify_silver_acceptance_handoff_v0_1_0.py \
  --manifest /tmp/proofrail-silver-acceptance-handoff-v0.3.0/silver-acceptance-handoff-manifest.json
```

The verifier checks:

- manifest structure;
- subject order and roles;
- subject path safety;
- subject existence;
- subject hashes;
- nested v0.2.7 composed evidence validity;
- nested v0.2.8 acceptance package validity;
- nested v0.2.9 drill package validity;
- handoff summary structure;
- summary-to-manifest binding;
- cross-package chain binding;
- acceptance record id, decision status, and purpose id;
- closed-set handoff posture;
- posture downgrade prevention;
- scope limitations and non-claims;
- overclaim language outside limitations and non-claims.

Successful verification prints:

```text
PASS: silver acceptance handoff valid (proofrail-silver-acceptance-handoff-demo-001)
```

## Stable Failure Reasons

The v0.3.0 verifier exposes 17 stable failure reasons:

- `invalid_handoff_manifest`
- `handoff_subject_file_missing`
- `handoff_subject_path_traversal`
- `handoff_subject_hash_mismatch`
- `nested_composed_evidence_invalid`
- `nested_acceptance_package_invalid`
- `nested_revocation_challenge_drill_invalid`
- `handoff_summary_invalid`
- `handoff_summary_binding_mismatch`
- `handoff_chain_binding_mismatch`
- `handoff_record_mismatch`
- `handoff_purpose_mismatch`
- `handoff_posture_invalid`
- `handoff_posture_downgrade`
- `handoff_overclaim`
- `handoff_limitations_missing`
- `handoff_non_claims_missing`

The runner also has refusal reasons for build-time failures:

- `composed_evidence_validation_failed`
- `acceptance_package_validation_failed`
- `drill_package_validation_failed`
- `handoff_chain_binding_failed`
- `self_validation_failed`

## Regression Coverage

The v0.3.0 regression test covers 31 cases.

Coverage includes:

- full v0.2.7 -> v0.2.8 -> v0.2.9 -> v0.3.0 package generation;
- happy-path handoff verification;
- handoff manifest subject order;
- handoff summary fields;
- subject path traversal;
- missing subject detection;
- subject hash mismatch detection;
- malformed summary handling without Python tracebacks;
- nested package tampering;
- summary binding mismatch;
- chain binding mismatch;
- record and purpose mismatch;
- invalid posture;
- posture downgrade;
- overclaim detection;
- missing limitations and non-claims;
- runner refusal for invalid v0.2.7, v0.2.8, and v0.2.9 inputs;
- runner refusal for broken handoff chain binding;
- runner refusal for self-validation failure before atomic publish;
- scoped mutation checks.

Primary commands:

```bash
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
make verify-silver-all
python3 -m pytest tests/test_proofrail_claim.py
git diff --check
```

Reported verification:

- `make run-silver-acceptance-handoff-v0-3-0` passed;
- `make verify-silver-acceptance-handoff-v0-3-0` passed with 31/31 cases;
- `make verify-silver-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed with 27 tests;
- `git diff --check` passed.

## What This Release Does Not Claim

ProofRail v0.3.0 does not claim:

- Gold certification;
- Gold conformance;
- regulator approval;
- auditor approval;
- legal acceptance;
- legal revocation;
- compliance certification;
- production authorization;
- transferred trust;
- challenge adjudication;
- dispute resolution;
- governed acceptance.

The handoff package is evidence for review. It is not a decision that another relying party should reuse the acceptance.

## What Comes Next

v0.3.0 closes the current Silver acceptance-handoff arc.

The next work should keep the boundary explicit:

```text
v0.3.0:
  portable Silver acceptance handoff

Next:
  stronger Silver-to-Gold planning package

Later:
  governed acceptance, external accountability, retained evidence, challenge handling, and certification boundaries
```

The next milestone should decide what belongs in Gold and what must remain outside local Silver evidence packaging.

## Summary

ProofRail v0.3.0 introduces a portable Silver acceptance handoff package that binds v0.2.7 composed evidence, v0.2.8 relying-party acceptance, and v0.2.9 post-acceptance review posture into one independently verifiable artifact.

It does not certify the chain, transfer reliance, adjudicate challenges, approve production use, or execute Gold governance.
