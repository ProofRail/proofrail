# Silver Demo 006 — Revocation/Challenge Drill (v0.2.9)

This demo is the deterministic, local revocation/challenge drill that
ProofRail v0.2.9 layers on top of the v0.2.8 relying-party acceptance
record.

It answers a narrow question:

> Can a relying party preserve evidence that an accepted Silver package
> was later subject to a challenge or revocation signal, classify those
> signals against the local acceptance record's challenge window, and
> produce a hash-anchored drill report that says whether local review is
> required before reusing the acceptance?

It does **not** answer:

- Was the challenge valid on the merits?
- Was the acceptance legally revoked?
- Did a regulator, auditor, or governing body approve the outcome?
- Has a real dispute process occurred?
- Has a live revocation service been queried?
- Is the accepted system production-safe?
- Is this Gold conformance?

## What the demo does

1. Runs the v0.2.7 composed gateway evidence demo into
   `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/`.
2. Runs the v0.2.8 relying-party acceptance generator into
   `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/`.
3. Runs the v0.2.9 drill over the v0.2.8 package, consuming
   `fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl`,
   into `/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/`.
4. Verifies the resulting drill package with the v0.2.9 drill verifier.

The committed demo directory holds only this README and a walkthrough.
The runner writes all runtime output under `/tmp` and never stages output
into the repository.

## Commands

```bash
make run-silver-revocation-challenge-drill-v0-2-9
make verify-silver-revocation-challenge-drill-v0-2-9
```

## Non-claims

- The drill report is not a certificate.
- The drill report is not Gold conformance.
- The drill report is not regulator or auditor approval.
- The drill report does not adjudicate any challenge on the merits.
- The drill report does not revoke the v0.2.8 acceptance record.
- The drill report does not alter the v0.2.7 composed gateway evidence
  package.
- v0.2.9 records review triggers. It does not decide their merits.
