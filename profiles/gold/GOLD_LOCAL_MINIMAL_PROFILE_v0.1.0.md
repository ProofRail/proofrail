# Gold Local Minimal Profile v0.1.0 — Descriptor

Instance descriptor conforming to
`schemas/gold-local-minimal-profile-v0.1.0.md`. This file is the
canonical declaration of the **Gold Local Minimal Profile**
(`gold.local.minimal`) consumed by the v0.4.6 validator-only Gold
tool added in ProofRail release v0.4.6.

The descriptor and its schema together are the entire v0.4.6
Phase 1 surface. The validator is added in Phase 2; the regression
harness in Phase 3; the Makefile target, long-form doc, demo
README, and `## Gold v0.4.6` index entry in Phase 4.

## 1. Profile Identity

| Field | Value |
|---|---|
| `profile_name` | `gold.local.minimal` |
| `profile_version` | `v0.1.0` |
| `proofrail_release` | `gold.local_minimal_profile.v0.4.6` |
| `schema_path` | `schemas/gold-local-minimal-profile-v0.1.0.md` |
| `descriptor_path` | `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` |
| `validator_path` | `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` (Phase 2) |
| `make_target` | `verify-gold-local-minimal-profile-v0-4-6` (Phase 4) |

The profile name `gold.local.minimal` is the only mode this
descriptor declares. There are no alternative modes.

## 2. Scope and Boundary

The Gold Local Minimal Profile is a **local, minimal, hash-anchored
named profile** over the existing v0.4.0..v0.4.5 Gold artifacts in
this repository. It consolidates v0.4.0..v0.4.5 into a single
named conformance target with a validator and a closed set of
explicit non-claims.

The profile is in scope for:

- Local relying-party self-inspection of this repository.
- Demonstrating that a closed inherited Gold surface is present,
  declared with its required Makefile entry points, and observed
  to pass under invocation.
- Documenting the closed non-claim set that local conformance does
  not transfer to any third party, certification body, registry,
  or production deployment.

The profile is **not** in scope for and explicitly does not claim:

- Full Gold conformance, Platinum conformance, or any future
  higher-tier profile.
- Third-party certification, accreditation, audit opinion, or
  regulatory approval.
- Federation, live registry trust, or transfer of reliance to any
  party outside this repository.
- Live policy engine evaluation or production runtime governance.
- Verifier revocation semantics or stale-registry handling.
- Cryptographic signing of any v0.4.6 output (the validator does
  not sign or publish anything).
- Any claim that local demo conformance equals institutional
  assurance.

The exact non-claim phrases enforced by validator reason R65 are
listed verbatim under §6.

## 3. Required Inherited Gold Artifacts

This section enumerates the closed set of v0.4.0..v0.4.5 Gold
artifact paths that must exist (regular file, readable) in the
repository for `gold.local.minimal` profile conformance. The
validator under R62 checks existence only; content correctness is
deferred to the inherited verifiers under R64.

The descriptor's enumeration below must equal the schema's §4
enumeration; R66 fires if they diverge.

### 3.1 Required Gold schemas (15)

- `schemas/gold-governed-reliance-package-v0.1.0.md`
- `schemas/gold-governed-reliance-package-manifest-v0.1.0.md`
- `schemas/gold-governed-reliance-conformance-report-v0.1.0.md`
- `schemas/gold-governed-reliance-decision-report-v0.1.0.md`
- `schemas/gold-decision-report-package-manifest-v0.1.0.md`
- `schemas/gold-policy-evaluation-matrix-v0.1.0.md`
- `schemas/gold-policy-evaluation-matrix-package-manifest-v0.1.0.md`
- `schemas/gold-policy-evaluation-report-v0.1.0.md`
- `schemas/gold-challenge-lifecycle-records-v0.1.0.md`
- `schemas/gold-challenge-lifecycle-report-v0.1.0.md`
- `schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md`
- `schemas/gold-reliance-package-index-v0.1.0.md`
- `schemas/gold-reliance-package-index-manifest-v0.1.0.md`
- `schemas/gold-multi-case-reliance-index-v0.1.0.md`
- `schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md`

### 3.2 Required Gold tools (12 — six build/verify pairs)

- `tools/gold/build_gold_governed_reliance_demo_v0_1_0.py`
- `tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py`
- `tools/gold/build_gold_decision_report_hardening_v0_1_0.py`
- `tools/gold/verify_gold_decision_report_hardening_v0_1_0.py`
- `tools/gold/build_gold_policy_evaluation_matrix_v0_1_0.py`
- `tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py`
- `tools/gold/build_gold_challenge_lifecycle_lite_v0_1_0.py`
- `tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py`
- `tools/gold/build_gold_reliance_package_index_v0_1_0.py`
- `tools/gold/verify_gold_reliance_package_index_v0_1_0.py`
- `tools/gold/build_gold_multi_case_reliance_v0_1_0.py`
- `tools/gold/verify_gold_multi_case_reliance_v0_1_0.py`

### 3.3 Required Gold harness scripts (6)

- `tests/test_gold_governed_reliance_v0_4_0.sh`
- `tests/test_gold_decision_report_hardening_v0_4_1.sh`
- `tests/test_gold_policy_evaluation_matrix_v0_4_2.sh`
- `tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh`
- `tests/test_gold_reliance_package_index_v0_4_4.sh`
- `tests/test_gold_multi_case_reliance_v0_4_5.sh`

### 3.4 Required Gold long-form docs (7)

- `docs/gold/minimal-gold-governed-reliance-v0.4.0.md`
- `docs/gold/gold-decision-report-hardening-v0.4.1.md`
- `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md`
- `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md`
- `docs/gold/gold-reliance-package-index-v0.4.4.md`
- `docs/gold/gold-multi-case-reliance-v0.4.5.md`
- `docs/gold/gold-boundary-v0.2.5.md`

### 3.5 Required Gold demo READMEs (6)

- `demos/gold-demo-001-governed-reliance/README.md`
- `demos/gold-demo-002-decision-report-hardening/README.md`
- `demos/gold-demo-003-policy-evaluation-matrix/README.md`
- `demos/gold-demo-004-challenge-lifecycle-lite/README.md`
- `demos/gold-demo-005-reliance-package-index/README.md`
- `demos/gold-demo-006-multi-case-reliance/README.md`

## 4. Required Makefile Targets

This section enumerates the closed set of `.PHONY:` Make targets
that must be declared in `Makefile`. Under R63 the validator checks
for textual presence of each target's `.PHONY:` declaration; it
does not execute any target under R63 (execution belongs to R64).

The descriptor's enumeration below must equal the schema's §5
enumeration; R66 fires if they diverge.

- `verify-gold-governed-reliance-v0-4-0`
- `verify-gold-decision-report-hardening-v0-4-1`
- `verify-gold-policy-evaluation-matrix-v0-4-2`
- `verify-gold-challenge-lifecycle-lite-v0-4-3`
- `verify-gold-reliance-package-index-v0-4-4`
- `verify-gold-multi-case-reliance-v0-4-5`
- `verify-gold-all`

The v0.4.6 own target `verify-gold-local-minimal-profile-v0-4-6`
(added in Phase 4) is intentionally **not** in the required set;
listing it would create a circular self-requirement.

## 5. Validator Reason Surface

### 5.1 v0.4.6-owned reasons (R62..R66)

The v0.4.6 validator emits exactly these five own reasons. No
others. Each surfaces as a `FAIL: <reason>:` line on stderr
followed by a single human-readable diagnostic.

| # | Reason | Trigger |
|---|---|---|
| R62 | `gold_local_minimal_profile_required_artifact_missing` | A path in §3 is missing or unreadable. |
| R63 | `gold_local_minimal_profile_required_make_target_missing` | A target in §4 is not declared `.PHONY:` in `Makefile`. |
| R64 | `gold_local_minimal_profile_required_verifier_failed` | An invoked inherited `verify-gold-*-v0-4-X` target exited nonzero **and** did not emit a recognized inherited `FAIL: <R01..R61>:` line. |
| R65 | `gold_local_minimal_profile_required_non_claim_missing` | A required non-claim phrase from §6 is not present in §6 of this descriptor (exact phrase, whitespace-normalized). |
| R66 | `gold_local_minimal_profile_descriptor_invalid` | Descriptor missing a required section, sections out of order, sections duplicated, or §3 / §4 enumerations diverging from schema. |

### 5.2 Inherited reason surface (R01..R61, verbatim relay)

The validator MAY invoke inherited `verify-gold-*-v0-4-X` targets
as subprocesses (R64 stage). When such an invocation exits nonzero
**and** its stderr contains a recognized `FAIL: <reason>:` line
where `<reason>` is one of the closed inherited tokens R01..R61:

- The validator **does NOT emit R64**.
- The validator **does NOT wrap, paraphrase, prepend, or append**
  to the inherited reason line.
- The validator **relays the inherited reason line verbatim** to
  its own stderr (the exact byte sequence of the recognized
  inherited `FAIL: ...` line) and exits 1.

The recognized inherited reason token set is fixed at exactly
**R01..R61** (R01..R48 from v0.4.0..v0.4.3, R49..R54 from v0.4.4,
R55..R61 from v0.4.5). v0.4.6 introduces no new inherited tokens
and removes none.

R64 fires only when the inherited verifier exits nonzero **and** no
recognized `FAIL: <R01..R61>:` line is present in its stderr (e.g.,
the inherited tool was unable to even start its own reason
emission). R64's diagnostic includes the invoked target name and
the verifier's nonzero exit code.

### 5.3 INFRA discipline (exit 3, non-reason-shaped)

The following surface as `INFRA: <message>` on stderr with exit 3,
non-reason-shaped:

- `make` binary not on PATH or otherwise unexecutable.
- Subprocess execution OSError.
- Descriptor file not readable as UTF-8.
- Any other infrastructure-shaped fault not equivalent to R62 or
  R63.

INFRA conditions that are equivalently characterizable as R62
(required artifact missing) or R63 (required target missing) take
the R62/R63 reason form, not INFRA.

### 5.4 Locked check order

The validator runs checks in this fixed order and stops at the
first failing check (single-FAIL discipline):

1. **R62** — required-artifact existence scan over §3.
2. **R63** — required-make-target scan over §4.
3. **R65** — required-non-claim phrase scan over §6.
4. **R66** — descriptor self-integrity scan (sections, ordering,
   enumeration parity with schema).
5. **R64** — inherited verifier subprocess sweep over §4
   (skipped under `--skip-make`; when skipped, R64 cannot fire and
   the relay path is unreachable, by design).

If all five checks pass, the validator exits 0 and emits a single
`PASS: gold_local_minimal_profile_conformance` line on stdout.

## 6. Required Non-Claims

The validator under R65 scans this section for each of the
following eight phrases. Exact-phrase matching is used with only
trivial whitespace normalization (leading/trailing whitespace trim;
internal runs of whitespace collapsed to a single space). No
paraphrase is accepted.

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

Each phrase asserts a closed non-claim of `gold.local.minimal`
conformance:

- `no certification` — local profile conformance is not a
  certification of any kind.
- `no legal adjudication` — local profile conformance is not a
  legal finding, opinion, or determination.
- `no production reliance transfer` — local profile conformance
  does not transfer reliance to any production system or
  third-party relying party.
- `no federation` — local profile conformance is not a federation
  handle, federation membership, or federation interop claim.
- `no live registry trust` — local profile conformance does not
  imply trust in any live registry, directory, or external trust
  list.
- `no verifier revocation semantics` — local profile conformance
  does not implement verifier revocation, blocklist consultation,
  or revocation-aware trust decisions.
- `no stale-registry semantics` — local profile conformance does
  not implement stale-registry detection, freshness windows, or
  registry-cache-aging policy.
- `no claim that local demo conformance equals institutional
  assurance` — local profile conformance is bounded to this
  repository and this descriptor; it does not equal any external
  institutional assurance, audit, or attestation.

Any missing phrase surfaces as R65 with the missing phrase echoed
verbatim on stderr.

## 7. Validator Surface

### 7.1 CLI shape

```
python3 tools/gold/verify_gold_local_minimal_profile_v0_1_0.py \
  [--repo-root <path>]   # default: CWD
  [--make-binary <path>] # default: "make"
  [--skip-make]          # default: false; skip R64 subprocess stage
```

The validator accepts no `--input-package` or other input-path
arguments. It reads only repository files relative to `--repo-root`
and invokes the `--make-binary` to drive inherited Gold verifiers
under the R64 stage.

Because the validator accepts no caller-supplied evidence package
path, the five v0.4.0 runner-only refusal tokens are **not** part
of the v0.4.6 reason surface. v0.4.6 has zero runner-only refusal
tokens.

### 7.2 Exit codes

- `0` — conformance PASS.
- `1` — conformance FAIL: one of R62..R66, or a verbatim-relayed
  inherited R01..R61.
- `3` — INFRA failure (non-reason-shaped).

### 7.3 No-builder, no-certificate rule

The v0.4.6 release is **validator-only**. There is no paired
`build_gold_local_minimal_profile_*` tool. The validator does not
publish a JSON conformance certificate, a signed assertion, a
manifest, or any other portable artifact. Publishing such an
artifact would imply third-party attestation, which §6
explicitly disclaims.

## 8. Conformance Output

The validator emits **exactly one** of the following on each run:

- `PASS: gold_local_minimal_profile_conformance` on stdout, exit 0.
- `FAIL: <R62..R66>:` on stderr, exit 1 — one of the five
  v0.4.6-owned reason tokens, followed by a single
  human-readable diagnostic.
- A verbatim inherited `FAIL: <R01..R61>:` line on stderr, exit 1
  — relayed unchanged from an invoked inherited Gold verifier
  under the R64 stage (the recognized-inherited-reason path).
- `INFRA: <message>` on stderr, exit 3 — for non-reason-shaped
  infrastructure faults.

The validator writes **no file** to the working tree, no file under
`/tmp/`, and no file under any other path. The `no_residue`
discipline is absolute. There is no JSON conformance certificate
under any circumstance.

## 9. Changelog

- **v0.1.0** — Initial descriptor conforming to
  `schemas/gold-local-minimal-profile-v0.1.0.md`. Declares
  `gold.local.minimal` profile name, closed required-artifact set
  (15 schemas, 12 tools, 6 harnesses, 7 long-form docs, 6 demo
  READMEs), closed required-target set (6 v0.4.0..v0.4.5 verify
  targets + `verify-gold-all`), closed v0.4.6-owned reason set
  R62..R66, R64 verbatim-relay rule for inherited R01..R61, INFRA
  exit 3 discipline, locked check order R62 → R63 → R65 → R66 →
  R64, validator-only release shape, no JSON conformance
  certificate, and the eight exact-phrase required non-claims for
  R65.
