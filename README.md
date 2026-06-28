# ProofRail

ProofRail is a vendor-neutral evidence and reliance framework for agentic AI control.

It asks a narrow question:

> Can a protected action be supported by structured evidence that an independent relying party can inspect?

ProofRail is not a gateway, SIEM, observability platform, GRC tool, policy engine, certification authority, auditor, regulator, or runtime truth oracle. External systems may produce events, traces, decisions, dashboards, or tickets. ProofRail defines portable evidence packages and verification steps for protected-action claims.

## Current Status

Latest release: **v0.4.6 — Gold Local Minimal Profile**

v0.4.6 is a narrow incremental Gold release that adds a single profile descriptor (`profile_name = gold.local.minimal`, `profile_version = v0.1.0`) plus a single validator-only tool that performs a closed five-check structural conformance scan of the existing v0.4.0..v0.4.5 Gold artifact surface in this repository (15 schemas, 12 build/verify tools, 6 regression harnesses, 7 long-form docs, 6 demo READMEs, 7 inherited Makefile targets). v0.4.6 ships no runner, no wrapping manifest, no subject body, no JSON certificate, no signed assertion, and no portable artifact whatsoever; the conformance scan is the artifact. It relays the inherited 61-reason verifier surface (R01..R61) verbatim via subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` targets, adds 5 v0.4.6-owned reasons under a locked five-check order (required-artifact scan → required-Makefile-target scan → required-non-claim scan → descriptor self-integrity scan → inherited-verifier subprocess sweep), and ships a 15-exercise regression harness. v0.4.6 is not a registry, certificate, federation layer, federation handle, full Gold, Platinum, live policy engine, or transfer of reliance. Local profile conformance does not equal institutional assurance. The v0.4.0..v0.4.5 annotated tags are preserved unchanged.

The Silver tier now provides the pre-Gold substrate needed to carry verified evidence toward governed reliance:

```text
Bronze: Can the deployment produce structured evidence that protected actions are controlled?
Silver: Can a relying party independently verify a specific evidence package?
Gold: Can verified evidence support a governed reliance decision under explicit policy?
```

## Why ProofRail Exists

Agentic AI systems increasingly take or request actions through tools, APIs, workflow systems, gateways, and other operational surfaces. Some of those actions are protected: releasing a payment, approving a vendor, exporting data, changing a deployment, rotating a secret, or otherwise crossing a meaningful trust boundary.

For those actions, logs alone are not enough. A relying party needs evidence that can be packaged, checked, challenged, and carried across organizational boundaries without assuming that one gateway, vendor, dashboard, or policy engine is the source of truth.

ProofRail is an attempt to define that evidence/reliance layer one primitive at a time.

## Tier Ladder

| Tier | Question | Current Status |
|---|---|---|
| Iron-plus | Can a live control primitive mediate protected actions? | Reference proof of concept completed outside this public repo. |
| Bronze | Can a deployment produce structured evidence that protected actions are controlled? | Public schemas, tools, and composed demo artifacts are present. |
| Silver | Can a relying party verify that evidence package independently? | Current Silver line completed through v0.3.7. |
| Minimal Gold | Can a Silver verification result become a governed reliance decision under explicit policy? | Completed at v0.4.0. |
| Full Gold / Platinum | Can this scale to institutional assurance, federation, certification, and public-interest governance? | Concept-note territory only; no realized implementation claim yet. |

## What Silver Now Includes

Silver began with signed verification of Bronze evidence and now includes the primitives needed to prepare for Minimal Gold.

| Release | Capability |
|---|---|
| v0.2.0 | Silver relying-party profiles: `silver.base` and `silver.independent`. |
| v0.2.1-v0.2.5 | Multi-principal authority fixtures, protected-action decisions, multi-agent harness, and trust-boundary demo package. |
| v0.2.6 | Evidence Source Adapter profile. |
| v0.2.7 | Composed Silver demo over simulated external gateway evidence. |
| v0.2.8 | Relying-Party Acceptance Record. |
| v0.2.9 | Revocation and Challenge Drill. |
| v0.3.0 | Silver Acceptance Handoff. |
| v0.3.1 | Silver Handoff Inspector + Gold Gap Inventory. |
| v0.3.2 | Silver Trace Binding Profile. |
| v0.3.3 | Silver Adapter Pilot Package. |
| v0.3.4 | Challenge / Withdrawal Record Primitives. |
| v0.3.5 | Relying-Party Policy Pack. |
| v0.3.6 | Control Crosswalk + Protected Action Catalog. |
| v0.3.7 | Registry Lite. |

## Latest Release: v0.4.3 Gold Challenge Lifecycle Lite

v0.4.3 is a narrow incremental Gold release. It pairs the unchanged v0.4.0 governed-reliance package body, v0.4.1 decision report, and v0.4.2 policy evaluation matrix and policy evaluation report with a deterministic local runtime challenge-lifecycle records body and a byte-re-derivable lifecycle report, bound by a 7-subject manifest cross-anchored to the v0.4.0 body, the v0.4.1 decision report, and the v0.4.2 policy-evaluation pair. The underlying decision outcomes remain the closed v0.4.0 set:

- accepted;
- rejected;
- challenged;
- withdrawn;
- superseded.

v0.4.3 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a transfer of reliance to any external party, does not consult any live policy engine or live lifecycle adjudication authority, and does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair.

The v0.4.3 release note is the best short summary:

- [ProofRail v0.4.3 release](https://github.com/ProofRail/proofrail/releases/tag/v0.4.3)

## Repository Map

| Path | Purpose |
|---|---|
| `schemas/` | Public schema documents for Bronze and Silver artifacts. |
| `tools/claims/` | Bronze claim and evidence-bundle tooling. |
| `tools/silver/` | Silver signing, packaging, verification, inspection, and conformance tools. |
| `fixtures/` | Committed test fixtures and example inputs. |
| `demos/` | Demo READMEs, walkthroughs, and committed demo scaffolding. Runtime packages are written outside the repo, usually under `/tmp/`. |
| `docs/silver/` | Silver release docs and explanations. |
| `docs/gold/` | Gold boundary planning notes. |
| `docs/dev/` | Maintainer-facing command indexes, release indexes, and coding-assistant guardrails. |
| `profiles/` | Silver relying-party profile documents. |

## Start Here

If you are new to ProofRail:

1. Read the [v0.4.0 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.4.0).
2. Review the [Gold release index](docs/dev/gold-release-index.md) and the [Bronze + Silver release index](docs/dev/silver-release-index.md).
3. Review [Minimal Gold Governed Reliance v0.4.0](docs/gold/minimal-gold-governed-reliance-v0.4.0.md).
4. Review the [Gold boundary note](docs/gold/gold-boundary-v0.2.5.md).
5. Review the [Silver tools README](tools/silver/README.md).
6. For the original Bronze path, start with the [Bronze claim schema v0.1.2](schemas/bronze-claim-schema-v0.1.2.md) and the [Bronze claim tools README](tools/claims/README.md).

## Verify Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the core Bronze unit tests:

```bash
python3 -m pytest tests/test_proofrail_claim.py
```

Run the latest Gold target:

```bash
make run-gold-challenge-lifecycle-lite-v0-4-3
make verify-gold-challenge-lifecycle-lite-v0-4-3
```

Run the current Gold chain:

```bash
make verify-gold-all
```

Run the full Bronze + Silver chain:

```bash
make verify-silver-all
```

Note: the full Silver chain may regenerate timestamped Bronze demo artifacts in a working tree. Maintainers should inspect `git status -sb` after running it.

## Development And Maintainer Notes

ProofRail uses coding assistants during development, but public failure/refusal reason names are treated as release contracts. Recent Silver releases include regression gates designed to prevent taxonomy drift, runner/verifier surface mixing, and overclaiming.

Maintainer-facing guidance lives in:

- [Coding assistant guardrails](docs/dev/coding-assistant-guardrails.md);
- [Silver command index](docs/dev/silver-command-index.md);
- [Gold release index](docs/dev/gold-release-index.md);
- [Bronze + Silver release index](docs/dev/silver-release-index.md).

The main README should remain a front door. Do not turn it into a release-by-release implementation log or taxonomy dump. Detailed release mechanics belong in release docs, `docs/dev/`, and `tools/silver/README.md`.

## Non-Claims

ProofRail does not currently claim:

- compliance with any external framework;
- legal enforceability;
- regulator approval;
- auditor approval;
- certification;
- production authorization;
- runtime truth;
- transferred trust;
- production PKI;
- federation;
- Gold governed reliance.

Silver verifies evidence packages. Minimal Gold demonstrates governed reliance decisions over verified evidence under explicit relying-party policy.

## Status

ProofRail is experimental specification and tooling work. It is intended to clarify evidence, verification, and reliance boundaries for agentic AI control. It is not a production control system by itself.

## What ProofRail v0.3.6 Adds

See the [v0.3.6 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.6) and the [Silver release index](docs/dev/silver-release-index.md).

## What ProofRail v0.3.7 Adds

See the [v0.3.7 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.7) and the [Silver release index](docs/dev/silver-release-index.md).

## What ProofRail v0.4.0 Adds

ProofRail v0.4.0 is the first Gold-tier release: the Minimal Gold Governed Reliance Demo. A v0.4.0 package is a deterministic local hand-authored record of 1..5 governed reliance decisions composed from Silver-shaped inputs (Silver verification result, Silver acceptance handoff, Silver relying-party policy pack, Silver registry lite, Silver control crosswalk), structurally validated under 24 ordered checks and bound by a 2-subject manifest cross-anchored by `package_id` and `governed_reliance_demo_id`. The v0.4.0 release is not a certificate, is not signed, is not federated, is not a transfer of reliance to any external party, and is not full Gold. See [`docs/gold/minimal-gold-governed-reliance-v0.4.0.md`](docs/gold/minimal-gold-governed-reliance-v0.4.0.md) and the [Gold release index](docs/dev/gold-release-index.md).

## What ProofRail v0.4.1 Adds

ProofRail v0.4.1 is a narrow Gold maintenance release: Gold Decision Report Hardening. v0.4.1 re-projects the unchanged v0.4.0 governed-reliance package body into a deterministic local Gold decision report, paired with the v0.4.0 conformance report and bound by a 3-subject manifest. v0.4.1 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a transfer of reliance to any external party, and does not extend the substance of the v0.4.0 body. See [`docs/gold/gold-decision-report-hardening-v0.4.1.md`](docs/gold/gold-decision-report-hardening-v0.4.1.md).

## What ProofRail v0.4.2 Adds

ProofRail v0.4.2 is a narrow Gold maintenance release: Gold Policy Evaluation Matrix. v0.4.2 pairs the unchanged v0.4.0 governed-reliance package body and the unchanged v0.4.1 decision report with a hand-authored local policy evaluation matrix (one matrix row per recognized scenario, in natural order) and a byte-re-derivable policy evaluation report, bound by a 5-subject manifest. v0.4.2 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a transfer of reliance to any external party, does not consult any live policy engine, and does not extend the substance of the v0.4.0 body or the v0.4.1 decision report. See [`docs/gold/gold-policy-evaluation-matrix-v0.4.2.md`](docs/gold/gold-policy-evaluation-matrix-v0.4.2.md).

## What ProofRail v0.4.3 Adds

ProofRail v0.4.3 is a narrow incremental Gold release: Gold Challenge Lifecycle Lite. v0.4.3 pairs the unchanged v0.4.0 governed-reliance package body, the unchanged v0.4.1 decision report, and the unchanged v0.4.2 policy evaluation matrix and policy evaluation report with a hand-authored deterministic local runtime challenge-lifecycle records body (one lifecycle record per governed decision row in natural order, with a closed-vocabulary event chain) and a deterministic local lifecycle report (row-per-record projection plus a closed-vocabulary coverage summary keyed on the six lifecycle status values), bound by a 7-subject manifest. v0.4.3 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a transfer of reliance to any external party, does not consult any live policy engine or live lifecycle adjudication authority, and does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, or the v0.4.2 policy-evaluation pair. See [`docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md`](docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md).

## What ProofRail v0.4.4 Adds

ProofRail v0.4.4 is a narrow incremental Gold release: Gold Reliance Package Index. v0.4.4 wraps the unchanged v0.4.0 Governed Reliance Demo, the unchanged v0.4.1 Decision Report Hardening package, the unchanged v0.4.2 Policy Evaluation Matrix package, and the unchanged v0.4.3 Challenge Lifecycle Lite package (verified under the corrected v0.4.3.1 baseline) under a single 5-subject index manifest plus a single byte-stable v0.4.4-owned index body. It preserves the inherited R01..R48 verifier reasons via subprocess relay, adds 6 v0.4.4-owned reasons R49..R54 over the v0.4.4 index body, introduces a 7-ID pairwise-distinctness invariant whose 21 pairwise collisions surface at the manifest-integrity layer under `gold_manifest_invalid` (R01), and regression-locks macOS `/tmp` → `/private/tmp` `--force` idempotency in the runner's output-dir overwrite guard. v0.4.4 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a registry, is not a federation handle, is not a transfer of reliance to any external party, does not consult any live service, and does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, or the v0.4.3 lifecycle pair. See [`docs/gold/gold-reliance-package-index-v0.4.4.md`](docs/gold/gold-reliance-package-index-v0.4.4.md).

## What ProofRail v0.4.5 Adds

ProofRail v0.4.5 is a narrow incremental Gold release: Gold Multi-Case Reliance Demo. v0.4.5 wraps ONE unchanged v0.4.4 Gold Reliance Package Index child closure (which itself wraps the unchanged v0.4.0 Governed Reliance Demo, v0.4.1 Decision Report Hardening, v0.4.2 Policy Evaluation Matrix, and v0.4.3 Challenge Lifecycle Lite under the corrected v0.4.3.1 baseline) under a single 2-subject wrapping manifest plus a single byte-stable v0.4.5-authored multi-case projection index body whose five `cases[]` entries enumerate the five v0.4.0 governed-reliance scenarios in fixed natural order. It relays the inherited 54-reason verifier surface (R01..R54) verbatim through the v0.4.4 chain, adds 7 v0.4.5-owned reasons over the v0.4.5 wrapping manifest and multi-case index body under a locked check order, preserves the five runner-only refusal names verbatim, and bundles input copies to a disposable scratch directory before forwarding to the v0.4.4 runner so tracked repo paths are never forwarded. v0.4.5 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a registry, is not a federation handle, is not a transfer of reliance to any external party, does not consult any live service, and does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, the v0.4.3 lifecycle pair, or the v0.4.4 reliance-package index. See [`docs/gold/gold-multi-case-reliance-v0.4.5.md`](docs/gold/gold-multi-case-reliance-v0.4.5.md).

## What ProofRail v0.4.6 Adds

ProofRail v0.4.6 is a narrow incremental Gold release: Gold Local Minimal Profile. v0.4.6 adds a single profile descriptor (`profile_name = gold.local.minimal`, `profile_version = v0.1.0`) plus a single validator-only tool that performs a closed five-check structural conformance scan of the existing v0.4.0..v0.4.5 Gold artifact surface in this repository (15 schemas, 12 build/verify tools, 6 regression harnesses, 7 long-form docs, 6 demo READMEs, 7 inherited Makefile targets) under a locked check order (required-artifact scan → required-Makefile-target scan → required-non-claim scan → descriptor self-integrity scan → inherited-verifier subprocess sweep). v0.4.6 ships no runner, no wrapping manifest, no subject body, no JSON certificate, no signed assertion, and no portable artifact whatsoever; the conformance scan is the artifact. It relays the inherited 61-reason verifier surface (R01..R61) verbatim via subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` targets (with `verify-gold-all` intentionally excluded from the execution-target set to prevent Phase 4 recursion), adds 5 v0.4.6-owned reasons over the validator's own structural checks, ships a 15-exercise regression harness, and writes no file under the repo or under `/tmp/`. v0.4.6 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a registry, is not a federation handle, is not a transfer of reliance to any external party, does not consult any live service, does not re-derive, summarize, or modify any inherited schema, body, manifest, or subject, and does not extend the substance of the v0.4.0 body, the v0.4.1 decision report, the v0.4.2 policy-evaluation pair, the v0.4.3 lifecycle pair, the v0.4.4 reliance-package index, or the v0.4.5 multi-case reliance demo. Local profile conformance does not equal institutional assurance. See [`docs/gold/gold-local-minimal-profile-v0.4.6.md`](docs/gold/gold-local-minimal-profile-v0.4.6.md).
