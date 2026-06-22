# Silver Demo 007 — Acceptance Handoff (v0.3.0)

This demo is the deterministic, local Silver acceptance handoff package
that ProofRail v0.3.0 composes from the existing v0.2.7 / v0.2.8 / v0.2.9
chain.

It answers a narrow question:

> Can the three already-verified Silver pipelines — composed gateway
> evidence (v0.2.7), relying-party acceptance (v0.2.8), and
> revocation/challenge drill (v0.2.9) — be assembled into a single
> portable, hash-anchored package that an independent reviewer can
> verify end to end, with a recommended local handoff posture that is
> never weaker than the nested v0.2.9 drill posture?

It does **not** answer:

- Should a downstream party rely on the underlying acceptance?
- Was the challenge resolved on the merits?
- Was the acceptance legally accepted or legally revoked?
- Did a regulator, auditor, or governing body approve the handoff?
- Has reliance been transferred from the original v0.2.8 relying party
  to anyone else?
- Is the system Gold-certified or production-approved?
- Has a real revocation service been queried?

## What the demo does

1. Runs the v0.2.7 composed gateway evidence demo into
   `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/`.
2. Runs the v0.2.8 relying-party acceptance generator into
   `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/`.
3. Runs the v0.2.9 revocation/challenge drill into
   `/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/`.
4. Builds the v0.3.0 acceptance handoff package into
   `/tmp/proofrail-silver-acceptance-handoff-v0.3.0/`, byte-copying the
   three nested package roots under fixed top-level directories and
   deriving a `silver-acceptance-handoff-summary.json` plus a
   `silver-acceptance-handoff-manifest.json` with four subjects.
5. Verifies the resulting handoff package with the v0.3.0 handoff
   verifier, which re-runs the nested v0.2.7 verifier, v0.2.8
   validator, and v0.2.9 verifier (each WITHOUT
   `--evidence-package-root`, so v0.3.0 owns the chain binding) and
   then performs the four v0.3.0-owned chain-binding cross-checks plus
   the posture rank check and overclaim guard.

The committed demo directory holds only this README and a walkthrough.
The runner writes all runtime output under `/tmp` and never stages
output into the repository.

## Commands

```bash
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
```

The `run-` target rebuilds the entire v0.2.7 → v0.2.8 → v0.2.9 → v0.3.0
chain end to end.

## Posture rank model

The v0.3.0 verifier maps the nested v0.2.9
`recommended_local_posture` onto a minimum handoff posture rank, and
rejects any `handoff_result.recommended_handoff_posture` that is weaker
than that minimum:

```
acceptance_stands_for_demo_scope               -> rank 0
acceptance_requires_review_before_reuse        -> rank 1
acceptance_not_reusable_without_governed_review -> rank 2

silver_handoff_complete_for_demo_scope               (rank 0)
silver_handoff_complete_review_required_before_reuse (rank 1)
silver_handoff_not_reusable_without_governed_review  (rank 2)
```

The deterministic demo fixture chain produces drill posture
`acceptance_requires_review_before_reuse`, so the v0.3.0 demo emits
handoff posture `silver_handoff_complete_review_required_before_reuse`.

## Non-claims

- The handoff package is not a certificate.
- The handoff package is not Gold conformance.
- The handoff package is not regulator approval, auditor approval, or
  legal acceptance.
- The handoff package does not transfer reliance from the original
  v0.2.8 relying party to any downstream party.
- The handoff package does not adjudicate any challenge or revocation
  signal.
- The handoff package does not approve the system for production
  reliance.
- v0.3.0 packages already-verified Silver evidence. It does not extend
  the substance of what that evidence asserts.
