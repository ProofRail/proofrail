# Coding-Assistant Guardrails

This file collects the durable process rules that bind any AI coding
assistant working in this repository. These rules are stable across
Silver and Gold release lines. Release-specific architecture lives in
`docs/dev/silver-release-index.md` (Bronze + Silver) and
`docs/dev/gold-release-index.md` (Gold); the day-to-day command matrix
lives in `docs/dev/silver-command-index.md`. The compact operating
index for the active release is `CLAUDE.md`.

These rules are non-negotiable. They are written here so they can be
referenced from `CLAUDE.md` without bloating the operating index.

## 1. Plan-first, then implement

- For any non-trivial release work (new schema, new runner, new
  verifier, new regression test, or any cross-file rename), produce a
  written implementation plan BEFORE writing or modifying code.
- The plan must enumerate: files to create, files to modify, files
  intentionally untouched, the closed verifier-reason taxonomy, the
  closed runner-only refusal-reason taxonomy, the case-to-reason
  mapping, the duplicate / secondary case coverage, the runner / verifier
  separation, the regression-test exercise count breakdown, and the
  drift-scan / taxonomy-gate strategy.
- The plan is for user review. Do not begin implementation until the
  user has approved the plan.

## 2. Compaction-stop rule

- If the conversation is summarized / compacted BEFORE the user has
  approved an implementation plan, the very next assistant turn must
  report status only. It must not start writing code, running tests,
  or modifying files based solely on a summarized plan.
- After compaction, restate (a) the last user instruction, (b) what
  was already approved, (c) what is still pending approval, (d) the
  current todo state, and wait for the user to confirm before
  resuming implementation.
- This rule prevents post-compaction drift from silently consuming
  context budget on speculative work.

## 3. Reason-taxonomy contract

- Each Silver release that introduces a verifier or runner declares a
  closed set of failure reasons.
- The set is split into two disjoint groups:
  - the verifier reasons (emitted only by the verifier),
  - the runner-only refusal reasons (emitted only by the runner).
- Reasons are listed verbatim in the release's regression-test
  taxonomy gate (TG1) and in the release's section of `CLAUDE.md`
  (operating-index pointer) and `docs/dev/silver-release-index.md`
  (Bronze + Silver releases) or `docs/dev/gold-release-index.md`
  (Gold releases) for the full taxonomy.
- A release MUST NOT introduce a new public reason mid-implementation
  without an explicit plan amendment.

## 4. No OR-accepted reasons

- Regression cases match the single specific reason they exist to
  exercise. Do not accept `reason_a OR reason_b` as a passing match.
- If two reasons appear reachable for the same input, redesign the
  reachability ordering so exactly one fires (see the v0.3.2 / v0.3.3 /
  v0.3.6 amendments for the pattern).

## 5. Non-masking reachability orderings

- Earlier checks must not mask later checks. If a structural defect can
  collapse into a generic upstream reason (for example
  `*_manifest_invalid`), reorder so the dedicated downstream reason is
  reachable from a minimal mutation.
- Path traversal is checked BEFORE exact subject-path equality.
- Trust-authority pre-checks run BEFORE the v0.2.6 adapter validator
  subprocess so adapter-tampering with `source_is_trust_authority:
  true` is always attributed to the dedicated reason.
- More-specific posture / status-downgrade reasons run BEFORE generic
  status-mismatch reasons.
- Bundled-report byte disagreement folds back into the manifest-level
  reason; it does not create a twenty-fifth public reason.

## 6. Hard taxonomy gate (TG1)

- Every Silver release that introduces a closed reason taxonomy ships
  a hard taxonomy gate (TG1) in its regression test.
- TG1 scans v0.3.x-owned files AND the v0.3.x-anchored sections of
  cross-version docs (`README.md`, `CLAUDE.md`, `tools/silver/README.md`,
  `docs/silver/silver-artifact-map-v0.1.7.md`,
  `docs/silver/silver-limitations-and-non-claims.md`,
  `docs/gold/gold-boundary-v0.2.5.md`).
- The reason-shaped-token regex matches any `\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b`
  ending with a release-relevant suffix (such as `_invalid`, `_missing`,
  `_unsupported`, `_present`, `_forbidden`, `_failed`, `_not_object`,
  or `_mismatch`).
- Every reason-shaped token must belong to the verifier set ∪ the
  runner-only set ∪ a small explicit allowlist for cross-release
  shared tokens. The allowlist should be empty by default; each entry
  requires an explicit justification.
- TG1 includes a self-check that every approved reason itself
  satisfies the gate's regex.

## 7. Scoped sha256 snapshot (SS)

- Each release's regression test ships a scoped sha256 snapshot that
  hashes the set of release-owned source paths BEFORE and AFTER the
  test run.
- The snapshot fails if any release-owned source file is mutated by
  the test, proving the test is read-only against the source tree.

## 8. Drift-scan placement

- Cross-version doc anchors are added under fixed section markers
  (such as `## What ProofRail v0.x.y Adds`, `## v0.x.y Notes`, `## v0.x.y
  <release> Non-Claims`).
- TG1 extracts these sections by exact-substring start markers with
  same-level `## ` / `### ` boundaries. Do not change established
  marker strings without updating every TG1 referring to them.

## 9. Runner / verifier separation

- The runner emits ONLY runner-only refusal codes during its preflight
  phase (Phase A). Phase A never touches the output directory or
  staging sibling.
- The verifier emits ONLY verifier reasons.
- On `--self-validate` failure the runner relays the verifier's own
  stable reason verbatim. It does NOT wrap a verifier failure in a
  sixth runner-only code.
- Staging-then-replace: stage all output under a sibling
  `<output-dir>.staging.<pid>` directory; atomically `os.replace()`
  into place only AFTER successful staging build and (optional)
  successful self-validation. On failure, the staging directory is
  removed and the destination is left untouched.

## 10. Bronze / runtime churn discipline

- Several `make verify-silver-*` and Bronze targets regenerate
  Bronze claim + evidence bundle manifest files under `demos/composed-bronze-demo-001/`
  (currently `demos/composed-bronze-demo-001/claims/bronze-claim-demo-001.yaml`
  and `demos/composed-bronze-demo-001/evidence-bundle-manifest-v0.1.3.yaml`).
- These are runtime regenerations. The assistant must report the
  churn in the final review packet, but MUST NOT silently restore,
  discard, stage, or commit them without explicit user approval.
- Do not run `make verify-silver-all` casually during documentation
  work. It will regenerate Bronze runtime files and contaminate
  `git status -sb`. Use the per-release `make verify-<release>` target
  or `python3 -m pytest tests/test_proofrail_claim.py` for non-Bronze
  cross-checks.

## 11. No destructive git cleanup

- The assistant must never run `git checkout --`, `git reset --hard`,
  `git clean -fd`, `git stash`, or any other destructive git operation
  on user-modified files without explicit user approval.
- The assistant must never run `git config`, `git push --force`,
  `git rebase`, `git commit --amend`, or skip hooks
  (`--no-verify`, `--no-gpg-sign`) unless the user explicitly
  authorizes the specific command.

## 12. No commit / tag / push / release without approval

- The assistant must never run `git commit`, `git tag`, `git push`, or
  `gh release create` without explicit user authorization for the
  specific commit / tag / push / release.
- The assistant must never amend an existing commit or rewrite shared
  history.
- The assistant must never publish to a remote or to a package
  registry on its own initiative.

## 13. Final review packet

- After completing an implementation pass, the assistant produces a
  final review packet listing:
  - files created (count + paths),
  - files modified (count + paths),
  - files intentionally untouched (categorical list),
  - exact commands run + outcomes,
  - per-target test results (regression test, dependency tests,
    `python3 -m pytest tests/test_proofrail_claim.py`,
    `git diff --check`, final `git status -sb`),
  - Bronze / runtime churn status (verbatim path list, no silent
    cleanup),
  - taxonomy audit (full verifier + runner-only reason sets verbatim,
    case-to-reason mapping, duplicate / secondary cases listed
    separately, runner-only refusal mapping, runner-relay exercise
    listed separately, path-traversal + absolute-path coverage
    callouts, regression-count breakdown, scoped sha256 snapshot
    result, drift-scan result, prohibited-token scan result),
  - non-claims preserved checklist,
  - explicit no-commit / no-tag / no-push / no-release attestation,
  - residual risk / follow-up for the next planned release.
