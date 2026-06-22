# Silver Relying-Party Acceptance Fixture — v0.2.8

This fixture provides a single, static, deterministic local relying-party
acceptance policy used by the ProofRail v0.2.8 demo and regression test.

```
acceptance-policy.json
```

## What this fixture is

- A local policy belonging to a fictional demo relying party
  (`demo.relying_party`).
- The input to
  `tools/silver/generate_relying_party_acceptance_record_v0_1_0.py`.
- A structural example of the
  `proofrail.silver.relying_party_acceptance_policy` schema v0.1.0.

## What this fixture is not

- Not a Gold certification policy.
- Not a third-party audit policy.
- Not regulator approval.
- Not a legal acceptance instrument.
- Not a production policy for any real relying party.

The relying party named here is fictional. The policy only describes what
the demo relying party will accept, for the `demo_trust_boundary_review`
purpose, over verified v0.2.7 composed gateway evidence.
