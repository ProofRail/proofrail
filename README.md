# ProofRail

ProofRail is a vendor-neutral evidence and reliance framework for agentic AI control.

It asks a narrow question:

> Can a protected action be supported by structured evidence that an independent relying party can inspect, verify, and evaluate for reliance?

ProofRail is currently a public reference project and conformance demonstration for protected-action evidence, verification, and governed reliance. Earlier Iron-plus work demonstrated controlled actuation outside this public repo. The current public repo focuses on portable evidence structures, verification tooling, Minimal Gold reliance artifacts, and non-claim discipline. It is not a live MCP mediation layer or production runtime control system.

ProofRail is not a gateway, SIEM, observability platform, GRC tool, policy engine, certification authority, auditor, regulator, or runtime truth oracle. External systems may produce events, traces, decisions, dashboards, or tickets. ProofRail defines portable evidence packages, verification steps, and reliance postures for protected-action claims.

## Current Status

The ProofRail concept paper was published on Zenodo on July 7, 2026.  The paper is available at Zenodo as [DOI: 10.5281/zenodo.21213739](https://doi.org/10.5281/zenodo.21213739).

Latest release: **v0.4.6 — Gold Local Minimal Profile**

v0.4.6 completes the current Minimal Viable Gold line by adding the Gold Local Minimal Profile: a validator-only conformance check over the existing v0.4.0–v0.4.5 Gold artifact surface. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

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
| Iron-plus | Can a live control primitive mediate protected actions? | Reference proof of concept completed outside this public repo. Current public work is not infrastructure-first; the repo focuses on evidence, verification, and governed-reliance artifacts. |
| Bronze | Can a deployment produce structured evidence that protected actions are controlled? | Public schemas, tools, and composed demo artifacts are present. |
| Silver | Can a relying party verify that evidence package independently? | Current Silver line completed through v0.3.7. |
| Minimal Gold | Can a Silver verification result become a governed reliance decision under explicit policy? | Completed at v0.4.6. |
| Full Gold / Platinum | Can this scale to institutional assurance, federation, and public-interest legitimacy? | Concept-note territory only; no realized implementation claim yet. |

## What Minimal Viable Gold Includes

Minimal Viable Gold ("MVG") builds on the foundation of the Silver releases and began with the Minimal Gold Governed Reliance Demo (v0.4.0). It now includes the complete initial set of MVG primitives.

| Release | Capability |
|---|---|
| v0.4.0 | Minimal Gold Governed Reliance Demo. |
| v0.4.1 | Minimal Gold Decision Report Hardening. |
| v0.4.2 | Minimal Gold Policy Evaluation Matrix. |
| v0.4.3 | Minimal Gold Challenge Lifecycle Lite. |
| v0.4.4 | Gold Reliance Package Index. |
| v0.4.5 | Gold Multi-Case Reliance Demo. |
| v0.4.6 | Gold Local Minimal Profile. |

## What Silver Includes

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

## Latest Release: v0.4.6 Gold Local Minimal Profile

v0.4.6 is a narrow incremental Gold release which implements the Gold Local Minimal Profile: a validator-only conformance check over the existing v0.4.0–v0.4.5 Gold artifact surface. The underlying decision outcomes remain the closed v0.4.0 set:

- accepted;
- rejected;
- challenged;
- withdrawn;
- superseded.

v0.4.6 does not introduce a new Gold tier, is not signed, is not a certificate, is not federated, is not a transfer of reliance to any external party, does not consult any live policy engine or live lifecycle adjudication authority, and does not extend the substance of the v0.4.0-v0.4.5 artifacts.

The v0.4.6 release note is the best short summary:

- [ProofRail v0.4.6 release](https://github.com/ProofRail/proofrail/releases/tag/v0.4.6)

## Repository Map

| Path | Purpose |
|---|---|
| `schemas/` | Public schema documents for Gold, Silver, and Bronze artifacts. |
| `tools/claims/` | Bronze claim and evidence-bundle tooling. |
| `tools/silver/` | Silver signing, packaging, verification, inspection, and conformance tools. |
| `fixtures/` | Committed test fixtures and example inputs. |
| `demos/` | Demo READMEs, walkthroughs, and committed demo scaffolding. Runtime packages are written outside the repo, usually under `/tmp/`. |
| `docs/silver/` | Silver release docs and explanations. |
| `docs/gold/` | Gold release documentation, boundary notes, and Minimal Gold artifacts. |
| `docs/dev/` | Maintainer-facing command indexes, release indexes, and coding-assistant guardrails. |
| `profiles/` | Silver relying-party profile documents. |

## Start Here

If you are new to ProofRail:

1. Read the [v0.4.6 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.4.6).
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
make verify-gold-local-minimal-profile-v0-4-6
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
- full Gold governed reliance;
- external institutional reliance;
- transferred reliance; 
- federation.

Silver verifies evidence packages. Minimal Gold demonstrates governed reliance decisions over verified evidence under explicit relying-party policy.

## Status

ProofRail is experimental specification and tooling work. It is intended to clarify evidence, verification, and reliance boundaries for agentic AI control. It is not a production control system by itself.

## What ProofRail v0.3.6 Adds

See the [v0.3.6 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.6) and the [Silver release index](docs/dev/silver-release-index.md).

## What ProofRail v0.3.7 Adds

See the [v0.3.7 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.7) and the [Silver release index](docs/dev/silver-release-index.md).

## What ProofRail v0.4.0 Adds

ProofRail v0.4.0 is the first Gold-tier release: the Minimal Gold Governed Reliance Demo, a package containing a deterministic local hand-authored record of 1..5 governed reliance decisions composed from Silver-shaped inputs (Silver verification result, Silver acceptance handoff, Silver relying-party policy pack, Silver registry lite, Silver control crosswalk), structurally validated under 24 ordered checks. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.1 Adds

ProofRail v0.4.1 is a narrow Gold maintenance release: Gold Decision Report Hardening, which re-projects the unchanged v0.4.0 governed-reliance package body into a deterministic local Gold decision report, paired with the v0.4.0 conformance report and bound by a 3-subject manifest. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.2 Adds

ProofRail v0.4.2 is a narrow Gold maintenance release: the Gold Policy Evaluation Matrix. v0.4.2 pairs the unchanged v0.4.0 governed-reliance package body and the unchanged v0.4.1 decision report with a hand-authored local policy evaluation matrix (one matrix row per recognized scenario, in natural order) and a byte-re-derivable policy evaluation report, bound by a 5-subject manifest. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.3 Adds

ProofRail v0.4.3 is a narrow incremental Gold release: Gold Challenge Lifecycle Lite. v0.4.3 pairs the unchanged v0.4.0 governed-reliance package body, the unchanged v0.4.1 decision report, and the unchanged v0.4.2 policy evaluation matrix and policy evaluation report with a hand-authored deterministic local runtime challenge-lifecycle records body (one lifecycle record per governed decision row in natural order, with a closed-vocabulary event chain) and a deterministic local lifecycle report (row-per-record projection plus a closed-vocabulary coverage summary keyed on the six lifecycle status values), bound by a 7-subject manifest.  It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.4 Adds

ProofRail v0.4.4 is a narrow incremental Gold release that continues the foundation work of v0.4.3, adding the Gold Reliance Package Index: the index is a wrapper for the Governed Reliance Demo, Decision Report Hardening package, Policy Evaluation Matrix package, and Challenge Lifecycle Lite package. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.5 Adds

ProofRail v0.4.5 is a narrow incremental Gold release that continues the Minimal Viable Gold foundation work of v0.4.4 by adding the Gold Multi-Case Reliance Demo: a Gold Reliance Package Index child closure under a wrapping manifest plus a multi-case projection index body. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.

## What ProofRail v0.4.6 Adds

v0.4.6 completes the current Minimal Viable Gold line by adding the Gold Local Minimal Profile: a validator-only conformance check over the existing v0.4.0–v0.4.5 Gold artifact surface. It does not create full Gold, federation, certification, runtime mediation, or transferred reliance.
