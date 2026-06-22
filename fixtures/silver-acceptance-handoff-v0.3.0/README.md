# Silver Acceptance Handoff Fixture — v0.3.0

This directory documents the v0.3.0 Silver acceptance handoff fixture
*by reference*. v0.3.0 does not introduce any static input fixture file.

## Why no static fixture

v0.3.0 is a composition release. Its inputs are the runtime outputs of
the v0.2.7, v0.2.8, and v0.2.9 pipelines:

```
/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/
  composed-gateway-evidence-manifest.json          (v0.2.7 manifest)

/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/
  acceptance-package-manifest.json                 (v0.2.8 manifest)

/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/
  revocation-challenge-drill-manifest.json         (v0.2.9 manifest)
```

Each upstream pipeline already pins its own canonical fixture under the
corresponding `fixtures/silver-*` directory. The v0.3.0 runner consumes
the three manifest paths produced by those pipelines and composes them
into a single portable handoff package.

The runner copies the full package root for each input manifest into a
deterministic layout under the v0.3.0 output directory:

```
<output-dir>/
  composed-gateway-evidence/                       (full byte-copy of v0.2.7 root)
  acceptance-package/                              (full byte-copy of v0.2.8 root)
  revocation-challenge-drill/                      (full byte-copy of v0.2.9 root)
  silver-acceptance-handoff-summary.json
  silver-acceptance-handoff-manifest.json
```

## Reproducing the v0.3.0 fixture chain

The single Make target
`run-silver-acceptance-handoff-v0-3-0` rebuilds the entire chain end to
end:

```
make run-silver-acceptance-handoff-v0-3-0
```

That target invokes, in order:

1. `tools/silver/compose_gateway_evidence_demo_v0_1_0.py` (v0.2.7)
2. `tools/silver/generate_relying_party_acceptance_record_v0_1_0.py` (v0.2.8)
3. `tools/silver/run_revocation_challenge_drill_v0_1_0.py` (v0.2.9)
4. `tools/silver/build_silver_acceptance_handoff_v0_1_0.py` (v0.3.0)
5. `tools/silver/verify_silver_acceptance_handoff_v0_1_0.py` (v0.3.0)

The full chain is also driven by the v0.3.0 regression test
`tests/test_silver_acceptance_handoff_v0_3_0.sh`, which builds every
input under `mktemp` directories and asserts every stable verifier and
runner-only failure reason.

## Non-claims

- v0.3.0 does not introduce new evidence content; it composes existing
  v0.2.7 / v0.2.8 / v0.2.9 evidence.
- v0.3.0 does not certify the included evidence chain.
- v0.3.0 does not transfer reliance from one relying party to another.
- v0.3.0 does not adjudicate any challenge or revocation signal.
- v0.3.0 does not establish Gold conformance, regulator approval,
  auditor approval, legal acceptance, or production authorization.
