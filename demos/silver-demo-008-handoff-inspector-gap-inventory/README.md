# Silver Demo 008 — Handoff Inspector + Gold Gap Inventory (v0.3.1)

This demo is the deterministic, local Silver handoff inspection package
that ProofRail v0.3.1 derives from an already-verified v0.3.0 Silver
acceptance handoff package and a committed local Gold-boundary
requirement set.

It answers a narrow question:

> Can a verified v0.3.0 Silver acceptance handoff package be
> independently inspected against a committed local Gold-boundary
> requirement set, producing a deterministic review report that
> summarizes the verified chain, the carried-forward caution posture,
> and the unresolved Gold-boundary prerequisites — without claiming
> Gold readiness, Gold certification, legal acceptance, regulator
> approval, auditor approval, production authorization, or transferred
> reliance?

It does **not** answer:

- Has the system been Gold-certified, audited, approved, or
  regulator-approved?
- Has the handoff package been legally accepted or legally revoked?
- Did the relying party's challenge get adjudicated?
- Has reliance been transferred to a downstream party?
- Has a real revocation service been queried?
- Is the system approved for production reliance?

## What the demo does

1. Rebuilds the entire v0.2.7 → v0.2.8 → v0.2.9 → v0.3.0 chain end to
   end into `/tmp/proofrail-silver-acceptance-handoff-v0.3.0/`.
2. Runs the v0.3.1 inspector
   (`tools/silver/inspect_silver_acceptance_handoff_v0_1_0.py`) over:
   - the v0.3.0 handoff manifest, and
   - the committed Gold-boundary requirement set fixture at
     `fixtures/silver-handoff-inspector-gap-inventory-v0.3.1/gold-boundary-requirements.json`.
3. Writes the v0.3.1 inspection package into
   `/tmp/proofrail-silver-handoff-inspection-v0.3.1/`:
   - `silver-acceptance-handoff/` — a byte-identical copy of the
     v0.3.0 handoff package root (subject [0] anchor is the nested
     `silver-acceptance-handoff-manifest.json`);
   - `gold-boundary-requirements.json` — a byte-identical copy of the
     fixture requirement set (subject [1]);
   - `silver-handoff-inspection-report.json` — the re-derived
     inspection report (subject [2]);
   - `silver-handoff-inspection-manifest.json` — the package-level
     3-subject SHA-256 anchor.
4. Verifies the resulting inspection package with the v0.3.1
   verifier, which subprocess-invokes the unchanged v0.3.0 handoff
   verifier on subject [0] and then independently re-derives every
   field of the inspection report.

The committed demo directory holds only this README and a walkthrough.
The runner writes all runtime output under `/tmp` and never stages
output into the repository.

## Commands

```bash
make run-silver-handoff-inspection-v0-3-1
make verify-silver-handoff-inspection-v0-3-1
```

The `run-` target rebuilds the entire v0.2.7 → v0.2.8 → v0.2.9 → v0.3.0
chain, then runs the v0.3.1 inspector with `--self-validate` so the
inspection verifier passes on the staged package before the atomic move
into place.

## Inspection package layout

```
/tmp/proofrail-silver-handoff-inspection-v0.3.1/
├── silver-acceptance-handoff/                    (byte-copy of v0.3.0)
│   ├── composed-gateway-evidence/                (v0.2.7 nested)
│   ├── acceptance-package/                       (v0.2.8 nested)
│   ├── revocation-challenge-drill/               (v0.2.9 nested)
│   ├── silver-acceptance-handoff-summary.json
│   └── silver-acceptance-handoff-manifest.json   (subject [0])
├── gold-boundary-requirements.json               (subject [1])
├── silver-handoff-inspection-report.json         (subject [2])
└── silver-handoff-inspection-manifest.json       (3-subject anchor)
```

## Re-derivation guarantee

Every field in `silver-handoff-inspection-report.json` is re-derived
deterministically from the nested v0.3.0 handoff summary and the bound
requirement set. The v0.3.1 verifier independently re-derives the same
fields and rejects any disagreement under one of the 20 stable failure
reasons.

The non-posture handoff summary fields (`acceptance_record_id`,
`decision_status`, `purpose_id`) are reserved for the dedicated reason
`inspection_handoff_summary_mismatch`. The posture path
(`recommended_handoff_posture` rank and `reuse_warning`) is reserved
for the dedicated reason `inspection_review_posture_downgrade`, which
remains reachable even if the non-posture cross-checks pass.

## Gold-boundary gap inventory

The committed requirement set fixture covers exactly one requirement
per each of 13 governance domains. The deterministic demo distribution
is:

```
silver_evidence_present       1   (independent_verifier_identity)
silver_evidence_partial       4   (revocation_operations,
                                  challenge_dispute_process,
                                  audit_trail_and_review,
                                  runtime_operating_boundary)
gold_prerequisite_unmet       6
out_of_scope_for_silver       2
```

The report-level `gold_boundary_status` is always `gold_not_claimed`
for this demo because at least one row is partial / unmet /
out-of-scope.

`silver_evidence_present` means relevant Silver evidence is present
inside the ProofRail chain. It **does not** mean the corresponding
Gold prerequisite is satisfied.

## Non-claims

- The inspection package is not a Gold certificate.
- The inspection package is not a Gold readiness assessment.
- The inspection package is not regulator approval, auditor approval,
  or legal acceptance.
- The inspection package does not transfer reliance to any downstream
  party.
- The inspection package does not adjudicate any challenge or
  revocation signal preserved in the chain.
- The inspection package does not authorize production reliance.
- The inspection package does not extend the substance of what the
  underlying v0.2.7 / v0.2.8 / v0.2.9 / v0.3.0 evidence asserts.
- The bound Gold-boundary requirement set is a local ProofRail demo
  inventory, not an external compliance standard.
