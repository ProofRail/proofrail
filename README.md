# ProofRail

ProofRail is a vendor-neutral evidence and reliance framework for agentic AI control.

It asks a narrow question:

> Can a protected action be supported by structured evidence that an independent relying party can inspect?

ProofRail is not a gateway, SIEM, observability platform, GRC tool, policy engine, certification authority, auditor, regulator, or runtime truth oracle. External systems may produce events, traces, decisions, dashboards, or tickets. ProofRail defines portable evidence packages and verification steps for protected-action claims.

## Current Status

Latest release: **v0.3.7 — Silver Registry Lite**

v0.3.7 is the last planned Silver release for now. The next planned release is **v0.4.0 — Minimal Gold Governed Reliance Demo**.

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
| Minimal Gold | Can a Silver verification result become a governed reliance decision under explicit policy? | Planned next as v0.4.0. |
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

## Latest Release: v0.3.7 Registry Lite

Registry Lite adds deterministic local registry fixtures for the entity roles needed to compose the Minimal Gold demo:

- issuers;
- verifiers;
- relying parties;
- policy authorities;
- revocation sources;
- protected-action authorities.

Registry Lite gives the demo local identifiers and role bindings. It does not create production PKI, legal identity, federation, certification, regulator approval, auditor approval, production authorization, or Gold governed reliance.

The v0.3.7 release note is the best short summary:

- [ProofRail v0.3.7 release](https://github.com/ProofRail/proofrail/releases/tag/v0.3.7)

## What Comes Next

The next planned release is **v0.4.0 Minimal Gold Governed Reliance Demo**.

Minimal Gold should show how a Silver verification result becomes one of several governed reliance outcomes under an explicit relying-party policy:

- accepted;
- rejected;
- challenged;
- withdrawn;
- superseded.

The v0.4.0 demo should include:

- clean acceptance;
- policy rejection despite Silver verification passing;
- challenge filed;
- withdrawal or supersession after challenge, revocation, or evidence defect.

Minimal Gold is intentionally narrow. It should not turn ProofRail into a broad governance platform, certification authority, compliance engine, or regulator substitute.

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

1. Read the [v0.3.7 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.7).
2. Review the [Silver release index](docs/dev/silver-release-index.md).
3. Review [Registry Lite v0.3.7](docs/silver/silver-registry-lite-v0.3.7.md).
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

Run the latest Silver target:

```bash
make run-silver-registry-lite-v0-3-7
make verify-silver-registry-lite-v0-3-7
```

Run the full Bronze + Silver chain:

```bash
make verify-silver-all
```

Note: the full chain may regenerate timestamped Bronze demo artifacts in a working tree. Maintainers should inspect `git status -sb` after running it.

## Development And Maintainer Notes

ProofRail uses coding assistants during development, but public failure/refusal reason names are treated as release contracts. Recent Silver releases include regression gates designed to prevent taxonomy drift, runner/verifier surface mixing, and overclaiming.

Maintainer-facing guidance lives in:

- [Coding assistant guardrails](docs/dev/coding-assistant-guardrails.md);
- [Silver command index](docs/dev/silver-command-index.md);
- [Silver release index](docs/dev/silver-release-index.md).

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

Silver verifies evidence packages. Minimal Gold, planned next, will demonstrate governed reliance decisions over verified evidence under explicit relying-party policy.

## Status

ProofRail is experimental specification and tooling work. It is intended to clarify evidence, verification, and reliance boundaries for agentic AI control. It is not a production control system by itself.

## What ProofRail v0.3.6 Adds

See the [v0.3.6 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.6) and the [Silver release index](docs/dev/silver-release-index.md).

## What ProofRail v0.3.7 Adds

See the [v0.3.7 release note](https://github.com/ProofRail/proofrail/releases/tag/v0.3.7) and the [Silver release index](docs/dev/silver-release-index.md).
