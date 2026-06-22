# ProofRail Silver Demo 005 — Relying-Party Acceptance Record (v0.2.8)

**ProofRail release:** v0.2.8
**Demo ID:** `proofrail-silver-demo-005-relying-party-acceptance`

> v0.2.8 records a relying party's local acceptance decision over verified
> Silver evidence. It does not certify the evidence, the system, the gateway,
> or the relying party.

A relying-party acceptance record is not a Gold certificate, regulator
approval, third-party audit, or legal acceptance instrument.

v0.2.8 records acceptance context. It does not execute acceptance governance.

---

## What this demo shows

A demo relying party (`demo.relying_party`) holds a static local policy
(`fixtures/silver-relying-party-acceptance-v0.2.8/acceptance-policy.json`)
that describes what kinds of Silver evidence the relying party will accept,
for which purpose, under which verification and revocation expectations,
and within which challenge window.

The demo produces a deterministic, hash-anchored **acceptance package**
that binds:

1. the relying party's local policy,
2. a verified copy of the v0.2.7 composed gateway evidence manifest, and
3. an acceptance record (status `accepted` / `rejected` /
   `accepted_with_exceptions`) carrying the verifier outcome, revocation
   review, exceptions, scope limitations, challenge window, and non-claims.

No real relying party is contacted, no live MCP traffic is exchanged, no
protected action is executed, no signing is performed, and no governance
workflow is invoked.

---

## Run

```bash
make run-silver-relying-party-acceptance-demo-v0-2-8
```

This composes the underlying v0.2.7 evidence into a temporary directory and
then generates the v0.2.8 acceptance package alongside it.

## Verify (regression test)

```bash
make verify-silver-relying-party-acceptance-demo-v0-2-8
```

This runs `tests/test_silver_relying_party_acceptance_record_v0_2_8.sh`,
which exercises the generator, validator, and a 30-case tamper battery
covering every stable v0.2.8 validator failure reason plus the
generator-only `evidence_verification_failed` refusal.

---

## Package layout (runtime)

```
/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/
├── acceptance-policy.json
├── evidence/
│   └── composed-gateway-evidence-manifest.json
├── acceptance-record.json
└── acceptance-package-manifest.json
```

The package manifest anchors the three subjects in deterministic order:

1. `acceptance-policy.json` (role `acceptance_policy`)
2. `evidence/composed-gateway-evidence-manifest.json`
   (role `verified_evidence_manifest`)
3. `acceptance-record.json` (role `acceptance_record`)

Only the copied **evidence manifest** is included. The full v0.2.7 package
remains external. The acceptance record records its sha256 anchor and the
verifier's pass result.

---

## Non-claims

- v0.2.8 records local reliance decisions over verified Silver evidence.
  It does not certify the evidence, the system, the gateway, or the
  relying party.
- v0.2.8 is not Gold acceptance, regulator approval, third-party audit, or
  legal acceptance instrument.
- v0.2.8 records acceptance context. It does not execute acceptance
  governance.
- v0.2.8 does not sign the acceptance record.
- v0.2.8 does not modify any Bronze, Silver Signed Bundle Assertion,
  Revocation List, Verification Report, Profile, Verifier Output
  Attestation, Multi-principal Authority, Multi-agent Harness, Multi-agent
  Trust-boundary, Evidence Source Adapter, or Composed Gateway Evidence
  semantics.
- The relying party named here (`demo.relying_party`) is fictional. No
  real relying party authored this policy.
