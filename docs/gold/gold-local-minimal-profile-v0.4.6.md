# Gold Local Minimal Profile — v0.4.6

**Status:** In development — ProofRail v0.4.6 — narrow incremental Gold release
**Release thesis:** ProofRail v0.4.6 is a narrow, deterministic, validator-only Gold release that adds a single **profile descriptor** plus a single **profile-conformance validator** over the existing v0.4.0..v0.4.5 Gold artifacts in this repository. The profile, named `gold.local.minimal` at version `v0.1.0`, enumerates a closed set of inherited Gold artifacts (15 schemas, 12 tools, 6 harnesses, 7 long-form docs, 6 demo READMEs), a closed set of inherited Make targets (6 `verify-gold-*-v0-4-X` targets plus `verify-gold-all`), an eight-phrase closed required-non-claim set, and a closed five-token v0.4.6-owned reason surface (R62..R66). v0.4.6 adds no new runner, no new portable evidence package, no JSON conformance certificate, no new schemas beyond the descriptor schema itself, no new build tool, and no runtime artifact materialized under `/tmp/`. v0.4.6 does NOT introduce a new Gold tier, does NOT sign anything, does NOT federate, does NOT transfer reliance, does NOT extend the substance of any inherited release, and does NOT claim that local demo conformance equals institutional assurance.

---

## v0.4.6 thesis

> A repository owner can declare a closed-vocabulary local conformance profile over the existing v0.4.0..v0.4.5 Gold surface — schemas, build/verify tools, regression harnesses, long-form docs, demo READMEs, and Makefile targets — and run a single validator-only tool that confirms (a) every enumerated inherited artifact path exists and is readable, (b) every enumerated inherited `verify-gold-*-v0-4-X` Makefile target plus `verify-gold-all` is declared `.PHONY:`, (c) eight exact-phrase non-claim assertions appear verbatim in the profile descriptor, (d) the descriptor itself carries the nine required level-2 sections in the locked order without duplication, and (e) every enumerated inherited verifier exits zero when invoked through `make` (skippable). The validator emits `PASS: gold_local_minimal_profile_conformance` on stdout with exit 0 on success, a single `FAIL: <R62..R66>:` line on stderr with exit 1 on a v0.4.6-owned failure, a byte-identical relayed inherited `FAIL: <R01..R61>:` line on stderr with exit 1 on an inherited failure detected through R64, or `INFRA: <message>` on stderr with exit 3 on a non-reason-shaped fault. v0.4.6 does **not** assert any signed conformance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, live policy-engine output, live lifecycle adjudication, signed lifecycle attestation, full Gold, or Platinum.

## Local minimal profile boundary

> A v0.4.6 Gold Local Minimal Profile package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a registry; it is **not** a federation handle; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** live policy-engine output; it is **not** live challenge-lifecycle adjudication; it is **not** a signed lifecycle attestation; it is **not** an external reliance authority; it is **not** full Gold; it is **not** Platinum. It is a hand-orchestrated, deterministic local conformance scan of the v0.4.0..v0.4.5 Gold surface against a closed descriptor with five v0.4.6-owned structural checks (R62..R66) and byte-identical verbatim relay of the inherited 61-reason surface R01..R61 (R01..R48 from v0.4.0..v0.4.3, R49..R54 from v0.4.4, R55..R61 from v0.4.5) under the R64 stage.

## Package layout

The v0.4.6 release adds exactly four tracked-surface files and one Makefile target plus one chain edit:

```
schemas/gold-local-minimal-profile-v0.1.0.md                                (profile descriptor schema)
profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md                          (profile descriptor instance)
tools/gold/verify_gold_local_minimal_profile_v0_1_0.py                      (validator-only tool)
tests/test_gold_local_minimal_profile_v0_4_6.sh                             (regression harness, 15 exercises)
```

Plus, in `Makefile`:

```
.PHONY: verify-gold-local-minimal-profile-v0-4-6
verify-gold-local-minimal-profile-v0-4-6:
	bash tests/test_gold_local_minimal_profile_v0_4_6.sh
```

and a single line appended to the `verify-gold-all` rule body chaining the v0.4.6 target after the inherited six.

The v0.4.6 release does NOT add any runtime directory, any `/tmp/proofrail-v046-*` materialized package, any wrapping manifest, any subject body, any JSON certificate, any signed assertion, any builder tool, any input template, any input-path CLI argument, any runner, or any output file. The validator reads only repository files under `--repo-root` (default CWD).

## Profile identity

| Field | Value |
|---|---|
| `profile_name` | `gold.local.minimal` |
| `profile_version` | `v0.1.0` |
| `proofrail_release` | `gold.local_minimal_profile.v0.4.6` |
| `descriptor_path` | `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` |
| `schema_path` | `schemas/gold-local-minimal-profile-v0.1.0.md` |
| `validator_path` | `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` |
| `make_target` | `verify-gold-local-minimal-profile-v0-4-6` |
| `harness_path` | `tests/test_gold_local_minimal_profile_v0_4_6.sh` |

The validator's `--profile` mode is fixed to `gold.local.minimal`; there are no alternative modes.

## Descriptor section layout (R66 scope)

The descriptor `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` carries exactly nine level-2 (`##`) sections in the fixed order declared by the schema:

1. `## 1. Profile Identity`
2. `## 2. Scope and Boundary`
3. `## 3. Required Inherited Gold Artifacts`
4. `## 4. Required Makefile Targets`
5. `## 5. Validator Reason Surface`
6. `## 6. Required Non-Claims`
7. `## 7. Validator Surface`
8. `## 8. Conformance Output`
9. `## 9. Changelog`

Missing, reordered, or duplicated required sections fold into R66 (`gold_local_minimal_profile_descriptor_invalid`). The descriptor's enumeration of §3 (required artifacts) and §4 (required targets) must match the schema's closed sets exactly; any drift folds into R66.

## Closed required-artifact set (R62 scope, 46 paths)

The v0.4.6 validator checks that every path below exists as a regular file and is readable. It does NOT re-verify file contents under R62 — content verification is the inherited verifiers' job, surfaced under R64.

- **15 Gold schemas** under `schemas/gold-*-v0.1.0.md` (v0.4.0..v0.4.5 wrapping manifest, body, and report schemas).
- **12 Gold tools** under `tools/gold/` (six build/verify pairs covering v0.4.0 governed-reliance, v0.4.1 decision-report hardening, v0.4.2 policy-evaluation matrix, v0.4.3 challenge-lifecycle lite, v0.4.4 reliance-package index, v0.4.5 multi-case reliance).
- **6 Gold regression harnesses** under `tests/test_gold_*_v0_4_X.sh`.
- **7 Gold long-form docs** under `docs/gold/` (one per v0.4.0..v0.4.5 release plus `gold-boundary-v0.2.5.md`).
- **6 Gold demo READMEs** under `demos/gold-demo-00X-*/README.md`.

The complete enumerated list lives in `schemas/gold-local-minimal-profile-v0.1.0.md` §4 and is mirrored verbatim in `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` §3. A missing or unreadable member surfaces as R62 (`gold_local_minimal_profile_required_artifact_missing`) with the offending path echoed on stderr.

## Closed required-target set (R63 scope, 7 targets)

The v0.4.6 validator checks for textual presence of `.PHONY: <target>` plus a matching rule in the repo `Makefile`. It does NOT execute these targets under R63 — execution belongs to R64.

The closed required-target set is exactly:

- `verify-gold-governed-reliance-v0-4-0`
- `verify-gold-decision-report-hardening-v0-4-1`
- `verify-gold-policy-evaluation-matrix-v0-4-2`
- `verify-gold-challenge-lifecycle-lite-v0-4-3`
- `verify-gold-reliance-package-index-v0-4-4`
- `verify-gold-multi-case-reliance-v0-4-5`
- `verify-gold-all`

The v0.4.6-own target `verify-gold-local-minimal-profile-v0-4-6` is deliberately **not** in the R63 closed set, to prevent a circular self-requirement (the v0.4.6 target invokes the harness which invokes the validator which would otherwise demand its own target). A missing required target surfaces as R63 (`gold_local_minimal_profile_required_make_target_missing`) with the offending target name on stderr.

## Five v0.4.6-owned verifier reasons (R62..R66)

The v0.4.6 validator emits exactly these five own reasons. No others. Each is reported as `FAIL: <reason>:` on stderr followed by a single human-readable diagnostic, with exit 1.

| # | Reason token | Trigger |
|---|---|---|
| R62 | `gold_local_minimal_profile_required_artifact_missing` | A path in the 46-path required-artifact closed set is missing or unreadable. |
| R63 | `gold_local_minimal_profile_required_make_target_missing` | A target in the 7-target required-target closed set is not declared `.PHONY:` with a matching rule in the repo `Makefile`. |
| R64 | `gold_local_minimal_profile_required_verifier_failed` | An invoked inherited `verify-gold-*-v0-4-X` target exited nonzero **and** did not emit a recognized `FAIL: <R01..R61>:` line on stderr. R64 is the **only** v0.4.6-owned reason for failed inherited execution; recognized inherited failures are relayed verbatim. |
| R65 | `gold_local_minimal_profile_required_non_claim_missing` | One of the eight closed required-non-claim phrases is absent (under whitespace-normalized exact-phrase match) from the descriptor's `## 6. Required Non-Claims` section. |
| R66 | `gold_local_minimal_profile_descriptor_invalid` | The descriptor is missing a required section, has sections in the wrong order, has duplicated sections, or its enumeration of §3 / §4 contents does not match the schema's closed sets. |

## Inherited reason surface (R01..R61, relayed verbatim)

The validator MAY invoke inherited verifiers as a subprocess under the R64 stage. When an invoked inherited verifier exits nonzero and its stderr contains a recognized `FAIL: <reason>:` line where `<reason>` matches the closed inherited token grammar `^[a-z][a-z0-9_]*$` (R01..R61), the validator:

- **Does NOT emit R64.**
- **Does NOT wrap, paraphrase, prepend, or append** to the inherited reason line.
- **Relays the inherited reason line verbatim** (the exact byte sequence of the recognized inherited `FAIL: ...` line) to its own stderr and exits 1.

This preserves the inherited closed reason taxonomy across the v0.4.0..v0.4.5 surface. The v0.4.6 validator never introduces a sixth wrapper around an inherited reason. The pattern-based recognition (`INHERITED_FAIL_RE`) is forward-compatible: it accepts any well-formed inherited reason token without requiring a whitelist.

If the inherited verifier exits nonzero but no recognized inherited `FAIL:` line is present in its stderr, R64 fires with a diagnostic referencing the invoked target name and the verifier's nonzero exit code. R64 is the only v0.4.6-owned reason that fires when inherited execution fails non-recognizably.

## INFRA discipline (exit 3, non-reason-shaped)

The `INFRA:` diagnostic is reserved for environmental failures of the v0.4.6 validator's subprocess invocation of `make` (e.g. missing executable, OSError on `os.execvp`, unreadable repo root) and for cases where the descriptor file itself cannot be opened or decoded as UTF-8. The diagnostic surface is exactly `INFRA: <one-line message>` on stderr followed by exit 3.

INFRA conditions that are equivalently characterizable as R62 (required artifact missing) or R63 (required target missing) take the R62 / R63 reason form, not INFRA. INFRA is reserved for infrastructure-shaped faults that fall outside the closed required surface.

`INFRA:` is NOT a member of the closed verifier reason set and does NOT appear in any TG1 allowlist or DENY pattern. Exit 3 is structurally distinct from exit 1 (verifier reason) so downstream automation can route environmental and content failures separately.

## Locked check order (R62 → R63 → R65 → R66 → R64)

The validator runs checks in this fixed order and stops at the first failing check (single-FAIL discipline):

1. **R62** — required-artifact existence scan over the 46-path closed set.
2. **R63** — required-make-target `.PHONY:` scan over the 7-target closed set.
3. **R65** — required-non-claim exact-phrase scan over the descriptor's §6.
4. **R66** — descriptor self-integrity scan (section presence, ordering, no duplicates, enumeration parity with the schema's §4 and §5 closed sets).
5. **R64** — inherited verifier subprocess sweep over the six `verify-gold-*-v0-4-X` targets (skipped under `--skip-make`).

The order is locked in the validator and asserted end-to-end by the v0.4.6 regression harness exercise sequence `r62 → r63 → r65 → r66 → r64`. More-specific reasons are reachable BEFORE less-specific reasons; the descriptor-content-shape reason (R66) is checked AFTER the cheaper file-and-target scans so that inherited surface gaps surface in the cheapest stage that can detect them.

If all five checks pass, the validator exits 0 and emits exactly one line on stdout: `PASS: gold_local_minimal_profile_conformance`.

## Subprocess delegation architecture

The R64 stage iterates a closed **execution-target** set of exactly six inherited targets:

- `verify-gold-governed-reliance-v0-4-0`
- `verify-gold-decision-report-hardening-v0-4-1`
- `verify-gold-policy-evaluation-matrix-v0-4-2`
- `verify-gold-challenge-lifecycle-lite-v0-4-3`
- `verify-gold-reliance-package-index-v0-4-4`
- `verify-gold-multi-case-reliance-v0-4-5`

`verify-gold-all` is **intentionally excluded** from the R64 execution-target set even though it is in the R63 required-target set: invoking `verify-gold-all` from the v0.4.6 validator would create a Phase 4 recursion through `$(MAKE) verify-gold-local-minimal-profile-v0-4-6` back into the validator. The validator iterates only the six inherited per-release verifiers, each via its own `make <target>` subprocess. The Phase 3 regression harness exercise `audit01` empirically confirms that the validator never invokes `verify-gold-all`.

For each execution target, the validator captures the subprocess return code and stderr, scans stderr for a recognized inherited `FAIL: <reason>:` line, and either (a) relays the inherited line verbatim to its own stderr and exits 1, or (b) emits R64 with the offending target name and the subprocess return code, or (c) on subprocess execution failure (e.g. missing `make`), emits `INFRA:` with exit 3.

## Validator surface

### CLI shape

```
python3 tools/gold/verify_gold_local_minimal_profile_v0_1_0.py \
  [--repo-root <path>]   # default: CWD
  [--make-binary <path>] # default: "make"
  [--skip-make]          # default: false; skip R64 subprocess stage
```

There is no `--input-package`, `--matrix-input`, `--lifecycle-input`, `--output-dir`, `--force`, `--self-validate`, or any other input-path argument. The validator reads only repository files under `--repo-root`. The five v0.4.0 runner-only refusal tokens (`runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`) are NOT part of the v0.4.6 reason surface because v0.4.6 ships no runner.

### Exit codes

- `0` — conformance PASS.
- `1` — conformance FAIL: one of R62..R66, or a relayed inherited R01..R61 line.
- `3` — INFRA failure (non-reason-shaped).

### Validator-only release shape

The v0.4.6 release is **validator-only**. There is no paired `build_gold_local_minimal_profile_*` tool. The validator does not publish a JSON conformance certificate, a signed assertion, or any other portable artifact. The validator does not write any file under the repo, under `/tmp/`, or under any other path. Publishing a portable conformance artifact would imply third-party attestation, which the profile explicitly disclaims under its closed non-claim set.

## Conformance output discipline

Stdout on PASS contains exactly one line:

```
PASS: gold_local_minimal_profile_conformance
```

Stderr on FAIL contains exactly one `FAIL: <reason>:` line followed by a single human-readable diagnostic (R62..R66 path), or one verbatim inherited `FAIL: <R01..R61>:` line (under the R64 relay path).

Stderr on INFRA contains exactly one `INFRA: <message>` line.

The validator never emits multi-line FAIL output, never wraps an inherited reason, never paraphrases an inherited diagnostic, never invokes `verify-gold-all`, and never writes any file. The `no_residue` discipline is absolute: the Phase 3 harness's `audit02` exercise empirically confirms a repo-wide sha256 manifest is byte-identical before and after a `--skip-make` run, and exercise `no_residue` confirms no stray `/tmp/proofrail-v046-test.*` scratch directory survives an EXIT-trap cleanup.

## Closed required non-claims (R65 closed set, 8 phrases)

The descriptor MUST contain the following eight phrases verbatim, each on its own line, inside its `## 6. Required Non-Claims` section. The validator scans using whitespace-normalized exact-phrase matching (leading/trailing trim, internal runs collapsed to a single space). No paraphrase is accepted.

```
no certification
no legal adjudication
no production reliance transfer
no federation
no live registry trust
no verifier revocation semantics
no stale-registry semantics
no claim that local demo conformance equals institutional assurance
```

A missing phrase surfaces as R65 (`gold_local_minimal_profile_required_non_claim_missing`) with the missing phrase echoed verbatim on stderr.

## Identifier grammar ownership

v0.4.6 owns the grammar of zero new identifiers and inherits the grammar of all v0.4.0..v0.4.5 identifiers verbatim via the R64 subprocess relay. v0.4.6 introduces no JSON document, no manifest, no body, no fingerprint, no `_id` field, no `_ref` field, no `_fingerprint` field, and no `package_id` field of its own. The profile name `gold.local.minimal` and the release token `gold.local_minimal_profile.v0.4.6` appear as text constants in the descriptor, the schema, and the validator source; they are never serialized into a wrapping manifest or a body subject.

## TG1 allowlist discipline (v0.4.6 harness)

The v0.4.6 regression harness ships TG1 as a strict numeric count gate: the harness sweeps the v0.4.6 validator source for token occurrences matching `gold_local_minimal_profile_<suffix>` and asserts the appearance set is exactly the five tokens corresponding to R62..R66. Any additional `gold_local_minimal_profile_*` token would be a v0.4.6-owned reason drift and would fail TG1. The harness uses a Python negative-lookahead boundary (`(?![a-z0-9_])`) so that the validator's own `prog="verify_gold_local_minimal_profile_v0_1_0.py"` filename fragment, which ends with a digit, does not produce a spurious match against the boundary scan. The validator's source self-references the five tokens in its closed-set declaration, the locked check order, and the FAIL emission paths; no token leaks into wrapper, runner, or environmental phrasing.

## INFRA diagnostic boundary

The `INFRA:` diagnostic surface is exactly `INFRA: <one-line message>` on stderr with exit 3. It is reserved for non-reason-shaped infrastructure faults: missing `make` executable, OSError on subprocess execution, unreadable repo root, descriptor file not decodable as UTF-8, or invalid `--make-binary` path. The Phase 3 harness exercise `env01` empirically exercises the invalid-`--make-binary` case and confirms exit 3 with a non-reason-shaped `INFRA:` line. `INFRA:` is NOT a member of the closed verifier reason set and does NOT appear in any TG1 allowlist or DENY pattern.

## Test scratch path policy

The v0.4.6 regression harness scratch path is `WORK=$(mktemp -d /tmp/proofrail-v046-test.XXXXXX)` with an EXIT-trap cleanup. Long-output captures from the harness go to `/tmp/proofrail-v046-last-run.log`. No test artifact is ever written under a tracked repo path, under an inherited-tier fixture directory, or under any non-`/tmp` filesystem location. The `no_residue` exercise asserts that no stray `/tmp/proofrail-v046-test.*` directory survives across harness invocations; the `audit02` exercise asserts that a `--skip-make` validator run mutates nothing under the repo and nothing under `/tmp/proofrail-v046-*`.

## Phase ledger and ship discipline

- **Phase 1 (schema + descriptor).** Added `schemas/gold-local-minimal-profile-v0.1.0.md` and `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md`. No tool, no Makefile, no doc, no demo, no test mutations.
- **Phase 2 (validator + smoke).** Added `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` (validator-only). Ran a 10-smoke ad-hoc check. No Makefile, no doc, no demo, no test mutations.
- **Phase 3 (regression harness).** Added `tests/test_gold_local_minimal_profile_v0_4_6.sh` (15 exercises: pp1, pp2, pp3, r62, r63, r64, r65, r66, inh01, env01, audit01, audit02, no_residue, tg01, ss01). All 15/15 PASS. No Makefile, no doc, no demo mutations.
- **Phase 4 (this file).** Added Makefile target `verify-gold-local-minimal-profile-v0-4-6`, chained it into `verify-gold-all`, wrote this long-form doc, wrote `demos/gold-demo-007-local-minimal-profile/README.md`, and updated `docs/dev/gold-release-index.md`. No schema, descriptor, validator, or harness mutation. No README.md or CLAUDE.md mutation. No Silver-index mutation. No release notes, no commit, no tag, no push, no GitHub release.

## Non-claims

The v0.4.6 tooling does not certify, audit, approve, transfer, federate, register, sign, attest, adjudicate, or operate any production system. It records a deterministic local conformance scan of the existing v0.4.0..v0.4.5 Gold artifact surface against a closed descriptor with five v0.4.6-owned structural checks (R62..R66) and byte-identical verbatim relay of the inherited 61-reason surface (R01..R61) via subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` targets. It does not consult any live service, gateway, observability backend, policy engine, GRC platform, registry, federation, lifecycle adjudication authority, or external authority. It does not re-derive, summarize, or modify any inherited schema, body, manifest, or subject. It does not write any file under the repo or under `/tmp/`. It is not signed and ships no portable artifact whatsoever. It is not a new Gold tier. It is not full Gold. It is not Platinum. Local profile conformance does not equal institutional assurance.
