# CLAUDE.md

Compact operating index. Full reference lives in `docs/dev/`.

## Project

ProofRail is a vendor-neutral conformance and governance framework for
AI agent actuation control: an evidence layer for protected actions
(tool calls, API invocations). Two profiles: **Iron-plus** (MCP
reference) and **Bronze** (local-enterprise, native or composed).
Spec + tooling repo, not a distributed package.

## Status

- Latest committed release: Gold **v0.4.2** — Gold Policy Evaluation Matrix.

## Where to Find Things

- `docs/dev/coding-assistant-guardrails.md` — durable process rules.
- `docs/dev/silver-command-index.md` — full command matrix (`make`
  targets, standalone tool invocations, regression-test paths).
- `docs/dev/silver-release-index.md` — Bronze + Silver release-by-release
  architecture (closed at Silver v0.3.7).
- `docs/dev/gold-release-index.md` — Gold release-by-release architecture
  (v0.4.0 onward).
- `tools/silver/README.md` — per-tool reference.
- `docs/silver/silver-*.md`, `docs/gold/gold-boundary-v0.2.5.md` —
  long-form release and Gold-boundary docs.
- `schemas/`, `fixtures/`, `demos/` — schemas, committed fixtures,
  committed demo READMEs (runtime packages are written under `/tmp/`).

## Essential Commands

```bash
pip install -r requirements.txt                       # deps
python -m pytest tests/test_proofrail_claim.py        # Bronze unit tests
make run-gold-policy-evaluation-matrix-v0-4-2         # current runner
make verify-gold-policy-evaluation-matrix-v0-4-2      # current verifier
make verify-gold-all                                  # current Gold chain
make verify-silver-all                                # full Silver chain (regenerates Bronze runtime; do NOT run during docs-only work)
git diff --check && git status -sb                    # hygiene
```

All other invocations: `docs/dev/silver-command-index.md`.

## Non-Negotiable Rules

Full text: `docs/dev/coding-assistant-guardrails.md`. Always-loaded
summary:

1. **Plan-first**: produce and get user approval on a written plan
   before writing or modifying code for non-trivial work.
2. **Compaction-stop**: if the conversation is summarized / compacted
   before plan approval, the next assistant turn reports status only.
   Do not start implementation from a summarized plan. After
   compaction, restate the last user instruction, what was approved,
   what is still pending, and the todo state, then wait for user
   confirmation before resuming.
3. **Reason-taxonomy contract**: every release with a verifier or
   runner declares a closed reason set, split into verifier reasons
   and runner-only refusals; cases match one specific reason.
4. **Non-masking orderings**: more-specific reasons must be reachable
   (path-traversal before subject-path equality; trust-authority
   pre-checks before adapter validator subprocess; etc.).
5. **Hard TG1** + **scoped SS snapshot** ship in every release's
   regression test.
6. **Runner / verifier separation**: runner emits only runner-only
   refusals; verifier emits only verifier reasons; on `--self-validate`
   failure the runner relays the verifier's reason verbatim with no
   sixth wrapper; staging-then-replace.
7. **Bronze / runtime churn**: report regenerated Bronze fixtures;
   never silently restore, discard, stage, or commit them.
8. **No destructive git cleanup** without explicit user approval.
9. **No commit / tag / push / release** without explicit user
   authorization for the specific operation.
10. **Final review packet** at end of every implementation pass.

## Dependencies

PyYAML and cryptography (Ed25519). No CI/CD or lint pipelines.

## Release Anchors

Section markers required by the v0.3.6, v0.3.7, and v0.4.0 TG1
drift-scan gates. Silver substance lives in
`docs/dev/silver-release-index.md`; Gold substance lives in
`docs/dev/gold-release-index.md`.

### Silver Control Crosswalk + Protected Action Catalog Package: `demos/silver-demo-013-control-crosswalk-protected-action-catalog/`

See `docs/dev/silver-release-index.md`.

### Silver Registry Lite Package: `demos/silver-demo-014-registry-lite/`

See `docs/dev/silver-release-index.md`.

### Gold Governed Reliance Demo: `demos/gold-demo-001-governed-reliance/`

See `docs/dev/gold-release-index.md` and `docs/gold/minimal-gold-governed-reliance-v0.4.0.md`.

### Gold Decision Report Hardening Package: `demos/gold-demo-002-decision-report-hardening/`

See `docs/gold/gold-decision-report-hardening-v0.4.1.md`.

### Gold Policy Evaluation Matrix Package: `demos/gold-demo-003-policy-evaluation-matrix/`

See `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md`.
