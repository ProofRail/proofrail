# Gold Local Minimal Profile Schema v0.1.0

Schema for the ProofRail **Gold Local Minimal Profile** descriptor.
The profile is consumed by a single validator-only Gold tool added
in release v0.4.6 (Gold Local Minimal Profile). This document
defines the descriptor file structure, the closed validator reason
surface, and the closed non-claim set the descriptor must carry
verbatim.

The descriptor instance that conforms to this schema is
`profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md`. Together,
schema + descriptor are the entire v0.4.6 Phase 1 surface.

## 1. Boundary

The Gold Local Minimal Profile is a **local, minimal, hash-anchored
profile** over the existing v0.4.0..v0.4.5 Gold artifacts in this
repository. It is not full Gold, not Platinum, not a certification,
not a federation handle, not a registry, not a transfer of reliance,
not a live policy engine, and not an institutional assurance.

It declares the closed set of inherited Gold artifacts, Makefile
targets, and explicit non-claim assertions that the v0.4.6 validator
must observe to report **profile conformance**.

The profile does not publish any new portable evidence package, any
JSON conformance certificate, or any new runtime artifact. The
validator emits a closed-vocabulary text result on stdout/stderr
plus exit codes; nothing else.

The schema does not modify any v0.4.0..v0.4.5 closed surface. It
adds an independent descriptor and validator surface.

## 2. Profile identity

| Field | Value |
|---|---|
| `profile_name` | `gold.local.minimal` |
| `profile_version` | `v0.1.0` |
| `proofrail_release` | `gold.local_minimal_profile.v0.4.6` |
| `descriptor_path` | `profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md` |
| `validator_path` | `tools/gold/verify_gold_local_minimal_profile_v0_1_0.py` (added Phase 2) |
| `make_target` | `verify-gold-local-minimal-profile-v0-4-6` (added Phase 4) |

The validator's `--profile` mode is fixed to `gold.local.minimal`;
there are no alternative modes.

## 3. Descriptor file format

The descriptor is a markdown file with the following **required
sections in the following fixed order**. Section headings must be
exact-match level-2 (`##`) headings; subsections (`###`) are
permitted.

| # | Heading | Purpose |
|---|---|---|
| 1 | `## 1. Profile Identity` | Declares `profile_name`, `profile_version`, `proofrail_release`. |
| 2 | `## 2. Scope and Boundary` | Records the local/minimal nature and the boundary against full Gold and certification. |
| 3 | `## 3. Required Inherited Gold Artifacts` | Closed list of v0.4.0..v0.4.5 schemas, tools, harnesses, docs, and demos. |
| 4 | `## 4. Required Makefile Targets` | Closed list of `verify-gold-*-v0-4-X` targets plus `verify-gold-all`. |
| 5 | `## 5. Validator Reason Surface` | Declares R62..R66 names, semantics, and check order; declares inherited R01..R61 verbatim-relay rule; declares INFRA exit 3 rule. |
| 6 | `## 6. Required Non-Claims` | The eight exact-phrase non-claim assertions the validator scans for under R65. |
| 7 | `## 7. Validator Surface` | Declares validator path, CLI shape, exit codes; declares no builder and no JSON certificate. |
| 8 | `## 8. Conformance Output` | Declares the closed text-only output discipline. |
| 9 | `## 9. Changelog` | Per-version notes. |

Missing, reordered, or duplicated required sections violate the
descriptor and surface as **R66**
(`gold_local_minimal_profile_descriptor_invalid`).

## 4. Required inherited Gold artifacts (R62 scope)

The descriptor lists the closed set of v0.4.0..v0.4.5 Gold artifact
paths that must exist (regular file, readable) in the repository.
The validator checks file existence only; it does not re-verify
file contents (that is the inherited verifiers' job under R64).

The closed required artifact set is exactly:

### Required Gold schemas (15)

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

### Required Gold tools (12 — six build/verify pairs)

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

### Required Gold harness scripts (6)

- `tests/test_gold_governed_reliance_v0_4_0.sh`
- `tests/test_gold_decision_report_hardening_v0_4_1.sh`
- `tests/test_gold_policy_evaluation_matrix_v0_4_2.sh`
- `tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh`
- `tests/test_gold_reliance_package_index_v0_4_4.sh`
- `tests/test_gold_multi_case_reliance_v0_4_5.sh`

### Required Gold long-form docs (7)

- `docs/gold/minimal-gold-governed-reliance-v0.4.0.md`
- `docs/gold/gold-decision-report-hardening-v0.4.1.md`
- `docs/gold/gold-policy-evaluation-matrix-v0.4.2.md`
- `docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md`
- `docs/gold/gold-reliance-package-index-v0.4.4.md`
- `docs/gold/gold-multi-case-reliance-v0.4.5.md`
- `docs/gold/gold-boundary-v0.2.5.md`

### Required Gold demo READMEs (6)

- `demos/gold-demo-001-governed-reliance/README.md`
- `demos/gold-demo-002-decision-report-hardening/README.md`
- `demos/gold-demo-003-policy-evaluation-matrix/README.md`
- `demos/gold-demo-004-challenge-lifecycle-lite/README.md`
- `demos/gold-demo-005-reliance-package-index/README.md`
- `demos/gold-demo-006-multi-case-reliance/README.md`

Missing or unreadable members of this closed set surface as **R62**
(`gold_local_minimal_profile_required_artifact_missing`), with the
specific missing path on stderr.

The descriptor MAY enumerate these paths under §3. The schema also
enumerates them here so the validator has a single canonical
reference; the descriptor reaffirms the same set. The descriptor's
list and the schema's list must be identical (R66 if mismatched).

## 5. Required Makefile targets (R63 scope)

The descriptor lists the closed set of Make targets that must be
exposed as `.PHONY:` entries in `Makefile`. The validator checks
for textual presence of the `.PHONY: <target>` declaration followed
by a target rule; it does NOT execute these targets under R63.
Execution belongs to R64.

The closed required target set is exactly:

- `verify-gold-governed-reliance-v0-4-0`
- `verify-gold-decision-report-hardening-v0-4-1`
- `verify-gold-policy-evaluation-matrix-v0-4-2`
- `verify-gold-challenge-lifecycle-lite-v0-4-3`
- `verify-gold-reliance-package-index-v0-4-4`
- `verify-gold-multi-case-reliance-v0-4-5`
- `verify-gold-all`

(The v0.4.6 own target `verify-gold-local-minimal-profile-v0-4-6`
is added in Phase 4 and is **not** part of the R63 closed required
set, to prevent a circular self-requirement.)

Missing targets surface as **R63**
(`gold_local_minimal_profile_required_make_target_missing`).

## 6. Validator reason surface (closed)

### 6.1 v0.4.6-owned reasons (R62..R66)

The v0.4.6 validator may emit exactly these five own reasons. No
others. Each is reported as a `FAIL: <reason>:` line on stderr
followed by a single human-readable diagnostic.

| # | Reason token | Trigger |
|---|---|---|
| R62 | `gold_local_minimal_profile_required_artifact_missing` | A path in the §4 required-artifact closed set is missing or unreadable. |
| R63 | `gold_local_minimal_profile_required_make_target_missing` | A target in the §5 required-target closed set is not declared `.PHONY:` in the repo `Makefile`. |
| R64 | `gold_local_minimal_profile_required_verifier_failed` | An invoked inherited `verify-gold-*-v0-4-X` target exited nonzero **and** did not emit a recognized `FAIL: <R01..R61>:` line. See §6.3. |
| R65 | `gold_local_minimal_profile_required_non_claim_missing` | The §7 closed non-claim phrase set is not fully present (exact-phrase, whitespace-normalized) in the descriptor. |
| R66 | `gold_local_minimal_profile_descriptor_invalid` | The descriptor is missing a required section, has sections in the wrong order, has duplicated sections, or the descriptor's enumeration of §4 or §5 contents does not match this schema's closed sets. |

### 6.2 Inherited reason surface (R01..R61, relayed verbatim)

The validator MAY invoke inherited verifiers as a subprocess (under
the R64 check stage). When an invoked inherited verifier exits
nonzero and **its stderr contains a recognized
`FAIL: <reason>:` line where `<reason>` is one of the closed
inherited tokens R01..R61**, the validator:

- **Does NOT emit R64.**
- **Does NOT wrap, paraphrase, prepend, or append** to the
  inherited reason line.
- **Relays the inherited reason line verbatim** to its own stderr
  (the exact byte sequence of the recognized inherited `FAIL: ...`
  line) and exits 1.

This preserves the inherited closed reason taxonomy. The v0.4.6
validator never introduces a sixth wrapper.

If the inherited verifier exits nonzero but no recognized
`FAIL: <R01..R61>:` line is present in its stderr, the validator
emits R64 with a diagnostic referencing the invoked target and the
verifier's nonzero exit code. R64 is the only v0.4.6-owned reason
for failed inherited execution.

The recognized inherited token set is fixed at exactly **R01..R61**
(R01..R48 from v0.4.0..v0.4.3, R49..R54 from v0.4.4, R55..R61 from
v0.4.5). No additions, no removals.

### 6.3 INFRA discipline (exit 3, non-reason-shaped)

Subprocess execution failure, missing executable (e.g. `make` not
on PATH), unreadable required tool, OSError, descriptor file not
readable as UTF-8, or any other non-reason-shaped infrastructure
fault is reported as `INFRA: <message>` on stderr with exit 3.

INFRA conditions that are equivalently characterizable as R62
(required artifact missing) or R63 (required target missing) take
the R62/R63 reason form, not INFRA. INFRA is reserved for
infrastructure-shaped faults that are not part of the closed
required surface.

### 6.4 Locked check order

The validator runs checks in this fixed order and stops at the first
failing check (single-FAIL discipline):

1. R62 — required-artifact existence scan over §4.
2. R63 — required-make-target scan over §5.
3. R65 — required-non-claim phrase scan over §7.
4. R66 — descriptor self-integrity scan (sections, ordering,
   enumeration parity with this schema).
5. R64 — inherited verifier subprocess sweep over §5
   (skipped under validator `--skip-make`).

If all five checks pass, the validator exits 0 and emits `PASS:
gold_local_minimal_profile_conformance` on stdout.

### 6.5 Closed reason discipline

The validator emits **exactly one** of:

- `PASS: gold_local_minimal_profile_conformance` on stdout, exit 0.
- `FAIL: <R62..R66>:` on stderr, exit 1.
- A verbatim inherited `FAIL: <R01..R61>:` line on stderr, exit 1
  (under R64 stage, recognized-inherited-reason path).
- `INFRA: <message>` on stderr, exit 3.

There are no other reason tokens. There is no JSON conformance
certificate. There is no runtime artifact written under
`/tmp/proofrail-v046-*/`.

## 7. Required non-claims (R65 closed set)

The descriptor MUST contain the following eight phrases verbatim,
each on its own line, inside the `## 6. Required Non-Claims`
section of the descriptor. The validator scans the descriptor's
non-claims section for each phrase using exact-phrase matching with
only trivial whitespace normalization (leading/trailing whitespace
trim, internal runs of whitespace collapsed to a single space). No
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

Any missing phrase surfaces as **R65**
(`gold_local_minimal_profile_required_non_claim_missing`) with the
missing phrase echoed verbatim on stderr.

## 8. Validator surface

### 8.1 CLI shape

```
python3 tools/gold/verify_gold_local_minimal_profile_v0_1_0.py \
  [--repo-root <path>]   # default: CWD
  [--make-binary <path>] # default: "make"
  [--skip-make]          # default: false; skip R64 subprocess stage
```

No `--input-package` or other input-path arguments. The validator
reads only repository files. Therefore the five v0.4.0 runner-only
refusal tokens are **not** part of the v0.4.6 reason surface.

### 8.2 Exit codes

- `0` — conformance PASS.
- `1` — conformance FAIL: one of R62..R66, or relayed inherited
  R01..R61.
- `3` — INFRA failure (non-reason-shaped).

### 8.3 No-builder, no-certificate rule

The v0.4.6 release is **validator-only**. There is no paired
`build_gold_local_minimal_profile_*` tool. The validator does not
publish a JSON conformance certificate, a signed assertion, or any
other portable artifact. Publishing such an artifact would imply
third-party attestation, which the profile explicitly disclaims
under §7.

## 9. Conformance output

Stdout on PASS contains exactly one line:

```
PASS: gold_local_minimal_profile_conformance
```

Stderr on FAIL contains exactly one `FAIL: <reason>:` line followed
by a single human-readable diagnostic (R62..R66 path), or one
verbatim inherited `FAIL: <R01..R61>:` line (under R64 relay path).

Stderr on INFRA contains exactly one `INFRA: <message>` line.

The validator does NOT write any file under the working tree, under
`/tmp/`, or under any other path. The `no_residue` discipline is
absolute.

## 10. Changelog

- **v0.1.0** — Initial schema. Defines descriptor section layout,
  closed required-artifact set (15 schemas, 12 tools, 6 harnesses,
  7 long-form docs, 6 demo READMEs), closed required-target set
  (6 v0.4.0..v0.4.5 verify targets + `verify-gold-all`), closed
  v0.4.6-owned reason set R62..R66, R64 verbatim-relay rule for
  inherited R01..R61, INFRA exit 3 discipline, locked check order
  R62 → R63 → R65 → R66 → R64, validator-only release shape, no
  JSON conformance certificate, eight exact-phrase required
  non-claims for R65.
