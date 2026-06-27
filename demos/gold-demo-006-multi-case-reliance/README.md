# Gold Multi-Case Reliance Demo — v0.4.5 (in development)

ProofRail v0.4.5 Gold Multi-Case Reliance Demo. A narrow, deterministic, hand-orchestrated wrapping of ONE unchanged v0.4.4 Gold Reliance Package Index child closure (which itself wraps the unchanged v0.4.0 Governed Reliance Demo, v0.4.1 Decision Report Hardening, v0.4.2 Policy Evaluation Matrix, and v0.4.3 Challenge Lifecycle Lite under the corrected v0.4.3.1 baseline) under a single 2-subject wrapping manifest and a single byte-stable v0.4.5-authored multi-case projection index body.

The narrow question this package answers:

> Given the unchanged v0.4.4 reliance-package index, can the same five v0.4.0 governed-reliance scenarios be projected, in natural v0.4.0 order, as a closed five-entry multi-case index body, bound to that v0.4.4 surface by a 2-subject wrapping manifest that re-anchors the v0.4.4 wrapping-manifest sha256 / size_bytes / path and the v0.4.5-authored body sha256 / size_bytes, and validated end-to-end via subprocess relay to the v0.4.4 verifier?

The narrow question this package does NOT answer:

- It is **not** a new Gold tier; **not** a certificate; **not** signed; **not** federated; **not** a registry; **not** a federation handle; **not** a transfer of reliance to any external party; **not** a regulator action, an auditor action, or a third-party endorsement; **not** legal acceptance, legal enforceability, or legal adjudication; **not** production authorization, production governance, or production PKI; **not** an audit-readiness assertion or a control-effectiveness assertion; **not** a runtime-truth oracle; **not** live policy-engine output; **not** live challenge-lifecycle adjudication; **not** a signed lifecycle attestation; **not** an external reliance authority; **not** full Gold; **not** Platinum.

## What the demo does

Materializes ONE v0.4.4 child closure under `child-packages/v0.4.4/` (the v0.4.4 runner is invoked exactly once and the v0.4.3 child closure is built under the corrected v0.4.3.1 baseline), projects the five v0.4.0 governed-reliance scenarios as fixed-order case entries in a v0.4.5-authored multi-case index body, computes a closed-key `coverage_summary` (`case_count = 5`, `case_slug_count = 5`, plus three anchor-consistency booleans), recomputes a top-level `multi_case_index_fingerprint` over canonical JSON of the body excluding the fingerprint field, and binds the materialized v0.4.4 wrapping manifest and the v0.4.5 index body under a 2-subject v0.4.5 wrapping manifest. The v0.4.5 verifier then subprocess-invokes the v0.4.4 verifier on the materialized v0.4.4 wrapping-manifest path under `child-packages/v0.4.4/...`; the v0.4.4 verifier in turn subprocess-invokes each of the four co-located v0.4.0..v0.4.3 verifiers. All inherited reasons R02..R54 surface verbatim through the chain.

## What runs at runtime

- v0.4.5 runner (`tools/gold/build_gold_multi_case_reliance_v0_1_0.py`) reads the same three inherited input files as the v0.4.4 runner (`--input-package`, `--matrix-input`, `--lifecycle-input`), copies all three by byte content into a disposable scratch input bundle, subprocess-invokes the v0.4.4 runner against the scratch copies into `child-packages/v0.4.4/` under the v0.4.5 staging tree, derives the v0.4.5 index body and the 2-subject v0.4.5 wrapping manifest, runs the v0.4.5 verifier under `--self-validate`, and atomically `os.replace()`s the staging directory into `/tmp/proofrail-v045-multi-case-reliance-demo/`.
- v0.4.5 verifier (`tools/gold/verify_gold_multi_case_reliance_v0_1_0.py`) validates the v0.4.5 wrapping manifest and the v0.4.5-owned index body under the seven v0.4.5-owned structural checks in their locked order, then subprocess-invokes the v0.4.4 verifier on the materialized v0.4.4 wrapping-manifest path. Inherited failures R02..R54 are relayed verbatim with no v0.4.5 wrapper; environmental failures surface under a non-reason-shaped `INFRA:` diagnostic with exit code 3.

## Run

```bash
make run-gold-multi-case-reliance-v0-4-5
make verify-gold-multi-case-reliance-v0-4-5
```

`make run-gold-multi-case-reliance-v0-4-5` materializes the package under `/tmp/proofrail-v045-multi-case-reliance-demo/`. Re-runs are byte-identical (the runner uses `--force --self-validate` under the v0.4.5 scratch prefix). `make verify-gold-multi-case-reliance-v0-4-5` runs the v0.4.5 regression harness `tests/test_gold_multi_case_reliance_v0_4_5.sh`.

## Reference

- `docs/gold/gold-multi-case-reliance-v0.4.5.md` — full v0.4.5 narrative: 61-reason surface (54 inherited from v0.4.0..v0.4.4 + 7 v0.4.5-owned), reachability orderings (locked per-case order), runner and verifier subprocess-delegation architecture, identifier grammar ownership, closed case-slug vocabulary, TG1 allowlist discipline, INFRA diagnostic boundary, test scratch path policy, and non-claims.
- `schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md` — v0.4.5 wrapping-manifest schema (2 subjects, cross-anchor fields, identifier grammar, manifest-layer reason coverage).
- `schemas/gold-multi-case-reliance-index-v0.1.0.md` — v0.4.5 multi-case index body schema (five fixed-order case entries, closed-key `coverage_summary`, fingerprint derivation, body-layer reason coverage, locked check order).
- `docs/gold/gold-reliance-package-index-v0.4.4.md` — inherited v0.4.4 narrative; v0.4.5 wraps exactly one v0.4.4 child closure verbatim.

## Non-claims

The v0.4.5 demo records a deterministic local hand-orchestrated wrapping of one v0.4.4 child closure under a v0.4.5-authored multi-case projection index body and a 2-subject wrapping manifest. It does not certify, audit, approve, transfer, federate, register, sign, attest, adjudicate, or operate any production system; does not consult any live service, gateway, observability backend, policy engine, GRC platform, registry, federation, lifecycle adjudication authority, or external authority; does not re-derive or summarize any inherited subject body; is not signed and ships local hash anchors only; is not a new Gold tier; is not full Gold; is not Platinum; does not represent runtime truth.
