# ProofRail v0.4.0 — Minimal Gold Governed Reliance Demo

ProofRail v0.4.0 introduces the first Minimal Gold boundary.

Silver verifies evidence packages. Minimal Gold shows how a relying party can turn a Silver verification result into a governed reliance decision: accepted, rejected, challenged, withdrawn, or superseded under an explicit local policy.

This release is intentionally narrow. It does not claim full Gold, certification, legal enforceability, production authorization, regulator approval, auditor approval, runtime truth, transferred trust, federation, or production PKI.

## What v0.4.0 Adds

v0.4.0 adds a deterministic local governed-reliance package that composes Silver-shaped inputs into five decision scenarios:

- clean acceptance;
- policy rejection despite a passing Silver verification result;
- challenge filed;
- withdrawal after challenge, revocation, or evidence defect;
- supersession after updated evidence or policy.

The package binds these decisions to:

- a Silver verification result;
- a Silver acceptance handoff;
- challenge / withdrawal primitives;
- a relying-party policy pack;
- a control crosswalk and protected action catalog;
- Registry Lite local authority fixtures.

The result is a portable demo package that shows how verified evidence can move from Silver verification toward governed reliance without claiming production governance or external legal effect.

## New Artifacts

This release adds:

- Gold governed-reliance schemas;
- canonical and single-scenario Gold fixtures;
- a Gold runner and verifier under `tools/gold/`;
- a 53-exercise v0.4.0 regression test;
- a Minimal Gold release narrative;
- the first Gold demo walkthrough.

The new Make targets are:

```bash
make run-gold-governed-reliance-v0-4-0
make verify-gold-governed-reliance-v0-4-0
make verify-gold-all
```

## Verification

Reported verification for the implementation:

- `make run-gold-governed-reliance-v0-4-0` passed;
- `make verify-gold-governed-reliance-v0-4-0` passed, 53/53 exercises;
- `make verify-gold-all` passed;
- `python3 -m pytest tests/test_proofrail_claim.py` passed, 27/27;
- v0.3.6 and v0.3.7 taxonomy regressions passed;
- `git diff --check` was clean.

The v0.4.0 regression covers:

- 4 positive-path checks;
- 5 Minimal Gold scenario checks;
- 24 canonical verifier failure reasons;
- 11 duplicate / secondary `gold_manifest_invalid` cases;
- 6 runner-only refusal exercises covering 5 distinct runner-only reasons;
- runner relay of verifier failure without a sixth wrapper reason;
- taxonomy drift scanning;
- scoped source immutability snapshot.

## Stable Public Taxonomy

v0.4.0 preserves the project rule that public failure and refusal reason names are release contracts.

The verifier exposes exactly 24 approved failure reasons. The runner exposes exactly 5 runner-only refusal reasons. Runner-only refusal reasons and verifier failure reasons remain separate public surfaces.

Human-readable detail may vary after the public reason token, but the public token must remain stable:

```text
FAIL: <approved_reason>: <human detail>
```

## Boundary

v0.4.0 is the first Gold boundary release, not full Gold.

It demonstrates a local governed-reliance decision record over Silver-shaped inputs. It does not re-evaluate upstream Silver evidence against a live policy engine, operate a registry, adjudicate legal reliance, certify compliance, sign artifacts, or authorize production action.

Full Gold and Platinum remain conceptual future tiers. Their eventual form should be shaped by feedback from real relying-party, assurance, governance, and implementation contexts rather than assumed in advance.

## Why This Matters

ProofRail has now completed the current Silver arc and crossed into Minimal Gold.

The project can show not only that evidence packages survive independent verification, but also how a relying party can record an explicit reliance posture over that verification result. That is the practical bridge from evidence verification to governed reliance.
