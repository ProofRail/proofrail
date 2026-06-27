# Gold Demo 005 — Reliance Package Index (v0.4.4)

This demo is the deterministic, local Gold reliance-package-index package that ProofRail v0.4.4 derives from the unchanged inherited v0.4.3 input file chain (and no v0.4.4-introduced input template):

- the canonical 5-scenario v0.4.0 fixture
  (`fixtures/gold-governed-reliance-v0.4.0/governed-reliance-scenarios.json`);
- the canonical 5-row v0.4.2 matrix template
  (`fixtures/gold-policy-evaluation-matrix-v0.4.2/policy-evaluation-matrix.json`); and
- the canonical 5-record v0.4.3 lifecycle records template
  (`fixtures/gold-challenge-lifecycle-lite-v0.4.3/challenge-lifecycle-records.json`).

The v0.4.4 runner consumes these three inherited input files via `--input-package`, `--matrix-input`, and `--lifecycle-input`. There is no `--index-input` flag and no v0.4.4-introduced input template; the v0.4.4 index body is fully derived from the materialized inherited child wrapping manifests.

It is a narrow Gold-tier incremental release that wraps the unchanged v0.4.0 Governed Reliance Demo, v0.4.1 Decision Report Hardening, v0.4.2 Policy Evaluation Matrix, and v0.4.3 Challenge Lifecycle Lite (under the corrected v0.4.3.1 verifier baseline) under a single 5-subject index manifest plus a single byte-stable index body. It does not introduce a new Gold tier, does not consult any live service, does not federate, does not sign anything, and does not extend the substance of any inherited release. It re-projects the seven artifact identifiers into a closed pairwise-distinctness collision class, binds the four child wrapping manifests by SHA-256, size, and path, and adds six v0.4.4-owned structural checks on the index body (R49..R54) on top of the inherited 48-reason surface (R01..R48).

It answers a narrow question:

> Can the v0.4.0 Minimal Gold Governed Reliance Demo, the v0.4.1 Gold Decision Report Hardening, the v0.4.2 Gold Policy Evaluation Matrix, and the v0.4.3 Gold Challenge Lifecycle Lite (under the corrected v0.4.3.1 verifier baseline) be materialized as four independent child closures under `child-packages/v0.4.X/` subdirectories, pinned by SHA-256, size, and path under a 5-subject v0.4.4 wrapping manifest plus a byte-stable index body that asserts membership of seven artifact identifiers in a closed pairwise-distinctness collision class — such that an independent Gold reviewer can re-run the unchanged v0.4.4 verifier (which subprocess-invokes each of the four co-located inherited verifiers on its corresponding child wrapping manifest path) and re-derive every check, without claiming that the package constitutes a certificate, a signed reliance instrument, a federated acceptance, a registry, a federation handle, a transfer of reliance to any external party, a regulator or auditor approval, legal acceptance or enforceability, production authorization, signed lifecycle attestation, live lifecycle adjudication, full Gold, or Platinum?

It does **not** answer:

- Is the package a Gold certificate?
- Is the package signed?
- Has any external party accepted the recorded reliance?
- Has the index been federated?
- Has any regulator, auditor, or third party approved the recorded reliance state?
- Have any of the inherited subject bodies been re-evaluated against any live policy engine, lifecycle adjudication authority, or live external service?
- Has the upstream Silver evidence been re-verified end-to-end against any live service?
- Is the demo production-authorized?
- Is the demo full Gold or Platinum?

## What the demo does

1. Validates `--input-package`, `--matrix-input`, and `--lifecycle-input` argvs through the Phase A preflight against the v0.4.0 canonical fixture, the v0.4.2 matrix template, and the v0.4.3 records template. Phase A emits only the 5 approved runner-only refusal reasons.
2. Stages output under `<output-dir>.staging.<pid>` and subprocess-invokes each of the four co-located inherited runners (v0.4.0, v0.4.1, v0.4.2, v0.4.3) into its own `child-packages/v0.4.X/` subdirectory under the staging tree, where each inherited runner writes its complete child closure. The v0.4.3 child closure is built under the corrected v0.4.3.1 baseline.
3. Projects the seven v0.4.4 collision-class identifiers (`conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `gold_reliance_package_index_id`) into the wrapping manifest. `manifest_id`, `package_id`, and `governed_reliance_demo_id` are also projected but are NOT members of the collision class.
4. Derives the v0.4.4 index body (subject [4]) deterministically from the materialized child wrapping manifests: four fixed-order entries (one per inherited release, each with `release_label`, `child_subject_index`, `child_package_root`, `child_manifest_path`, `child_manifest_fingerprint`, and `child_manifest_size_bytes` byte-matching the wrapping manifest's `subjects[i]`), a closed-key `coverage_summary` (`child_package_count = 4`, `inherited_release_count = 4`, `pairwise_distinct_id_count = 7`, `package_id_anchor_consistency = true`, `governed_reliance_demo_id_anchor_consistency = true`), and a top-level `index_fingerprint` (bare lowercase hex SHA-256 over canonical JSON of the body excluding the fingerprint field itself).
5. Writes the 5-subject wrapping manifest cross-anchored by `package_id` and `governed_reliance_demo_id` to every child wrapping manifest and to the index body, by the six inherited collision-class IDs to their matching child wrapping manifest fields, by the v0.4.4-owned `gold_reliance_package_index_id` to the index body, and by each `subjects[i].sha256` / `subjects[i].size_bytes` / `subjects[i].path` to the on-disk file at the corresponding path.
6. With `--self-validate`, invokes the v0.4.4 verifier against the staging directory BEFORE the atomic `os.replace()`. On self-validation failure the staging directory is removed and the destination is left untouched; the runner relays the verifier's failure UNCHANGED with no sixth runner-only wrapper code.

## What runs at runtime

The runtime layout at `/tmp/proofrail-v044-reliance-package-index-demo/` is a multi-file output with four `child-packages/v0.4.X/` subdirectories: the v0.4.4 wrapping manifest at the root, the v0.4.4 index body at the root, and one complete child closure per inherited release under `child-packages/v0.4.0/`, `child-packages/v0.4.1/`, `child-packages/v0.4.2/`, and `child-packages/v0.4.3/`. The runtime directory is never staged into the repository.

## Run

```bash
make run-gold-reliance-package-index-v0-4-4
make verify-gold-reliance-package-index-v0-4-4
```

## Reference

See `docs/gold/gold-reliance-package-index-v0.4.4.md` for the release narrative, the closed 54-reason surface (48 inherited R01..R48 + 6 v0.4.4-owned R49..R54), reachability orderings, runner and verifier subprocess-delegation architecture, the 7-ID pairwise-distinctness collision class, the TG1 allowlist discipline, the INFRA diagnostic boundary, the test scratch path policy, and the non-claims.

## Non-claims

The v0.4.4 demo records a deterministic local hand-orchestrated wrapping of the v0.4.0 Governed Reliance Demo, the v0.4.1 Decision Report Hardening, the v0.4.2 Policy Evaluation Matrix, and the v0.4.3 Challenge Lifecycle Lite (under the corrected v0.4.3.1 verifier baseline) under a 5-subject wrapping manifest and a byte-stable index body. It does not approve, audit, certify, federate, register, sign, attest, adjudicate, prove identity, evaluate against any live policy engine, adjudicate any challenge lifecycle against any live external authority, issue, transfer, or accept reliance to any external party. It does not re-derive or summarize any inherited subject body. It does not extend the substance of any inherited release. It is not signed; it ships local hash anchors only. It is not a Gold certificate, not full Gold, not Platinum, not a transfer of reliance, not a registry, not a federation handle, not a signed reliance instrument, not regulator / auditor / legal approval, and not production authorization.
