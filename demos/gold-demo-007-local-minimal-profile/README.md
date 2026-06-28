# Gold Local Minimal Profile Demo — v0.4.6 (in development)

ProofRail v0.4.6 Gold Local Minimal Profile Demo. A narrow, deterministic, **validator-only** conformance scan of the v0.4.0..v0.4.5 Gold artifact surface against a closed local-profile descriptor. No runner. No portable evidence package. No JSON conformance certificate. No runtime artifact materialized under `/tmp/`. The demo is the conformance validation itself, not a built package.

The narrow question this package answers:

> Does the v0.4.0..v0.4.5 Gold surface present in this repository — 15 schemas, 12 build/verify tools (six pairs), 6 regression harnesses, 7 long-form docs, 6 demo READMEs, and 7 inherited Makefile targets (6 `verify-gold-*-v0-4-X` plus `verify-gold-all`) — pass a closed five-check structural conformance scan defined by a local profile descriptor (`profile_name = gold.local.minimal`, `profile_version = v0.1.0`), including an eight-phrase exact-phrase non-claim scan, a descriptor self-integrity scan against a fixed nine-section layout, and (optionally) a subprocess sweep that executes each of the six inherited per-release `verify-gold-*-v0-4-X` targets and relays any inherited `FAIL:` line verbatim with no v0.4.6-owned wrapper?

The narrow question this package does NOT answer:

- It is **not** a new Gold tier; **not** a certificate; **not** signed; **not** federated; **not** a registry; **not** a federation handle; **not** a transfer of reliance to any external party; **not** a regulator action, an auditor action, or a third-party endorsement; **not** legal acceptance, legal enforceability, or legal adjudication; **not** production authorization, production governance, or production PKI; **not** an audit-readiness assertion or a control-effectiveness assertion; **not** a runtime-truth oracle; **not** live policy-engine output; **not** live challenge-lifecycle adjudication; **not** a signed lifecycle attestation; **not** an external reliance authority; **not** full Gold; **not** Platinum. Local profile conformance does **not** equal institutional assurance.

## What the demo does

Runs the v0.4.6 validator over the repository in its current state. The validator:

1. Scans the closed required-artifact set (46 paths: 15 Gold schemas + 12 Gold tools + 6 Gold harnesses + 7 Gold long-form docs + 6 Gold demo READMEs) for existence and readability; missing or unreadable paths surface in the first v0.4.6-owned structural check.
2. Scans the repo `Makefile` for `.PHONY:` declarations of the closed required-target set (the six inherited `verify-gold-*-v0-4-X` targets plus `verify-gold-all`).
3. Scans the descriptor at `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` for the eight required exact-phrase non-claim assertions under whitespace-normalized matching.
4. Scans the descriptor for the nine required level-2 (`##`) sections in their fixed order, without duplication, and confirms that the descriptor's enumeration of required artifacts and required targets matches the schema's closed sets exactly.
5. Optionally (skippable via `--skip-make`) subprocess-invokes each of the six inherited per-release `verify-gold-*-v0-4-X` targets via `make`, captures stderr, and either relays a recognized inherited `FAIL: <R01..R61>:` line verbatim (no v0.4.6 wrapper) or, on non-recognizable nonzero exit, emits the single v0.4.6-owned reason for failed inherited execution.

On success, the validator emits exactly `PASS: gold_local_minimal_profile_conformance` on stdout and exits 0. The validator writes no file under the repo, under `/tmp/`, or under any other path.

## What runs at runtime

- **No runner.** v0.4.6 ships no `build_gold_local_minimal_profile_*` tool, no `--input-package` argument, no `--output-dir` argument, and no `--force` argument. There is no `run-gold-local-minimal-profile-v0-4-6` Makefile target.
- **Validator only.** `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` reads only repository files under `--repo-root` (default CWD). CLI shape:

  ```
  python3 tools/gold/verify_gold_local_minimal_profile_v0_1_0.py \
    [--repo-root <path>]   # default: CWD
    [--make-binary <path>] # default: "make"
    [--skip-make]          # default: false; skip inherited-verifier sweep
  ```

  Exit codes: `0` PASS, `1` FAIL (one v0.4.6-owned reason or one verbatim-relayed inherited reason), `3` INFRA (non-reason-shaped infrastructure fault).

- **Regression harness.** `tests/test_gold_local_minimal_profile_v0_4_6.sh` exercises 15 named cases (positive paths, each v0.4.6-owned reason, an inherited verbatim-relay case, an INFRA case, a no-`verify-gold-all`-invocation audit, a no-file-write audit, a no-`/tmp` residue check, a token-count gate, and a byte-identical snapshot scope gate) using `mktemp -d /tmp/proofrail-v046-test.XXXXXX` scratch directories with EXIT-trap cleanup. All 15 exercises pass.

## Run

```bash
make verify-gold-local-minimal-profile-v0-4-6
```

`make verify-gold-local-minimal-profile-v0-4-6` runs the v0.4.6 regression harness `tests/test_gold_local_minimal_profile_v0_4_6.sh`, which exercises the validator against the live repository plus several synthetic mutated scratch fixtures (under `/tmp/proofrail-v046-test.XXXXXX/`) to confirm each v0.4.6-owned reason, the inherited verbatim-relay path, and the INFRA path.

There is no companion `make run-gold-local-minimal-profile-v0-4-6` target. The v0.4.6 release is validator-only: the conformance result IS the artifact.

The v0.4.6 target is also chained into `verify-gold-all`:

```bash
make verify-gold-all
```

`verify-gold-all` runs the six inherited per-release verifiers (v0.4.0..v0.4.5) and then the v0.4.6 local-minimal-profile verifier. The v0.4.6 validator itself iterates only the six inherited per-release targets under its R64 stage; it does NOT re-invoke `verify-gold-all`, so there is no recursion.

## Reference

- `docs/gold/gold-local-minimal-profile-v0.4.6.md` — full v0.4.6 narrative: validator-only release shape, closed five-token v0.4.6-owned reason surface, inherited verbatim-relay rule for the 61-reason R01..R61 inherited surface, locked check order, INFRA discipline, subprocess delegation architecture (six execution targets; `verify-gold-all` intentionally excluded), validator CLI shape, no-builder / no-certificate rule, conformance output discipline, closed eight-phrase non-claim set, TG1 numeric-count gate, test scratch path policy, and non-claims.
- `schemas/gold-local-minimal-profile-v0.1.0.md` — v0.4.6 profile descriptor schema: descriptor section layout (nine sections in fixed order), closed required-artifact set (46 paths), closed required-target set (7 targets), v0.4.6-owned reason taxonomy, inherited verbatim-relay rule, INFRA exit 3 rule, locked check order, eight required non-claims, validator surface.
- `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` — v0.4.6 profile descriptor instance.
- `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` — v0.4.6 validator-only tool.
- `tests/test_gold_local_minimal_profile_v0_4_6.sh` — v0.4.6 regression harness (15 exercises).
- Inherited v0.4.0..v0.4.5 long-form docs under `docs/gold/` cover the inherited 61-reason surface, the v0.4.0..v0.4.5 wrapping-manifest and body shapes, and the v0.4.3.1 verifier baseline used by the v0.4.4 and v0.4.5 closures. v0.4.6 wraps none of those surfaces; it scans them as files and (optionally) invokes their existing verifier targets.

## Non-claims

The v0.4.6 demo records a deterministic local conformance scan of the existing v0.4.0..v0.4.5 Gold artifact surface against a closed local-profile descriptor with five v0.4.6-owned structural checks and byte-identical verbatim relay of the inherited 61-reason surface (R01..R61) via subprocess invocation of the six inherited per-release `verify-gold-*-v0-4-X` Makefile targets. It does not certify, audit, approve, transfer, federate, register, sign, attest, adjudicate, or operate any production system; does not consult any live service, gateway, observability backend, policy engine, GRC platform, registry, federation, lifecycle adjudication authority, or external authority; does not re-derive, summarize, or modify any inherited schema, body, manifest, or subject; does not write any file under the repo or under `/tmp/`; is not signed and ships no portable artifact whatsoever; is not a new Gold tier; is not full Gold; is not Platinum; does not represent runtime truth. Local profile conformance does not equal institutional assurance.
