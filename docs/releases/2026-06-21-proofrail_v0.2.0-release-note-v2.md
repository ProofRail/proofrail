# ProofRail v0.2.0 - Silver Relying-Party Profile

Release date: 2026-06-21

ProofRail v0.2.0 formalizes what it means for a relying party to accept a ProofRail Silver evidence package.

Earlier v0.1.x releases built the Silver mechanics: signed bundle assertions, local revocation, verification reports, and independent verification. v0.2.0 turns those mechanics into a defined Silver profile with explicit conformance checks.

## What Changed

This release adds the **Silver Relying-Party Profile v0.2.0**.

The profile defines two modes:

- `silver.base` - validates a Silver verification report from a conformant Silver verifier.
- `silver.independent` - validates a Silver verification report from an independent verifier package, with package manifest and verifier identity checks.

The independent mode preserves the key Silver idea:

> a relying party can verify a prepared evidence package outside the environment that produced it.

## New Artifacts

Added:

- `profiles/silver/SILVER_PROFILE_v0.2.0.md`
- `schemas/silver-profile-conformance-report-v0.2.0.md`
- `tools/silver/validate_silver_profile_v0_2_0.py`
- `tests/test_silver_profile_v0_2_0.sh`

Updated:

- `Makefile`
- `CLAUDE.md`
- `tools/silver/README.md`
- `demos/silver-demo-001/README.md`
- `demos/silver-demo-002-independent-verifier/README.md`
- `docs/silver/silver-artifact-map-v0.1.7.md`
- `docs/silver/silver-limitations-and-non-claims.md`

## Profile Validator

The new validator checks whether a Silver Verification Report satisfies the v0.2.0 profile.

Example:

```bash
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.base \
  --verification-report demos/silver-demo-001/runtime/verification-report.json \
  --output demos/silver-demo-001/runtime/silver-profile-conformance-report-v0.2.0.json
```

For independent verification:

```bash
python3 tools/silver/validate_silver_profile_v0_2_0.py \
  --profile-mode silver.independent \
  --verification-report <independent-report.json> \
  --package-manifest <package-manifest.yaml> \
  --output <conformance-report.json>
```

## Revocation Semantics

`silver.independent` requires revocation checking.

`silver.base` may pass without revocation checking only with an explicit warning reason:

```text
profile_requirements_satisfied_with_revocation_warning
```

This keeps demo compatibility while making the weaker relying-party posture visible.

## Verification

The v0.2.0 regression test covers:

- passing `silver.base` conformance;
- passing `silver.independent` conformance;
- failed verification report rejection;
- missing package manifest rejection;
- missing revocation rejection for `silver.independent`;
- warning-path behavior for `silver.base`.

Primary commands:

```bash
make validate-silver-profile-demo-001
make validate-silver-profile-demo-002
make verify-silver-all
```

All release verification targets passed.

## What Comes Next

The next ProofRail work should build on the Silver profile without jumping prematurely to Gold.

Likely next steps:

- tighten the `silver.base` revocation posture so ordinary relying-party acceptance increasingly expects revocation checking;
- refine the independent verification package format toward a cleaner relying-party handoff;
- add clearer examples of passing and failing profile conformance reports;
- explore signed or attestable verifier outputs without treating them as certification decisions;
- define the first Gold planning boundary: when a Silver verification report becomes an input to governed acceptance, review, challenge, and certification workflows.

The main transition is:

```text
Silver v0.2.0:
  defined relying-party verification profile

Next:
  stronger relying-party operating profile

Later:
  Gold governed acceptance / certification layer
```

Silver should remain the evidence-package reliance layer. Gold should begin only when the work shifts from verifier conformance to governed institutional acceptance.

## What This Release Does Not Claim

ProofRail v0.2.0 does not claim:

- Gold certification;
- third-party certification;
- regulator approval;
- production PKI;
- production deployment assurance;
- audit opinion;
- public accreditation.

The correct claim is:

> ProofRail v0.2.0 defines and validates a local Silver relying-party profile for accepting a signed, revocable, reportable evidence package, with a stronger independent verification mode.

## Summary

v0.2.0 is the point where Silver becomes more than a collection of demos.

It now has a profile, a conformance report, a validator, and regression coverage for relying-party acceptance.
