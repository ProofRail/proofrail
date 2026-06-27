# Gold Multi-Case Reliance Package Manifest Schema v0.1.0

Schema for the v0.4.5 Gold Multi-Case Reliance Demo wrapping
manifest. The manifest is a local hash anchor over exactly two
byte-stable subjects: the v0.4.4 Gold Reliance Package Index
wrapping manifest (a single canonical v0.4.4 child closure) at
`child-packages/v0.4.4/gold-reliance-package-index-manifest.json`,
and the v0.4.5-authored Gold Multi-Case Reliance Index body file
`gold-multi-case-reliance-index.json` at the v0.4.5 package root.

## Boundary

The v0.4.5 wrapping manifest is a local hash anchor over two
byte-stable subjects. It is NOT a signature, NOT a certificate, NOT
federated, NOT a registry, NOT a federation handle, NOT a transfer
of reliance, and NOT full Gold. It is a local v0.4.5-owned
hash-bound index over one canonical v0.4.4 child closure.

The v0.4.5 package is a multi-file output: the wrapping manifest,
the v0.4.5 index body file, and a single `child-packages/v0.4.4/`
closure for the inherited v0.4.4 Gold Reliance Package Index. Files
underneath the v0.4.4 child closure (the v0.4.4 wrapping manifest's
own subjects, including subjects [0]..[3] under
`child-packages/v0.4.4/child-packages/v0.4.X/` for v0.4.0..v0.4.3,
plus the v0.4.4 index body file at the v0.4.4 closure root) are
runtime support files for the inherited v0.4.4 verifier; they are
NOT v0.4.5 wrapping-manifest subjects and carry no v0.4.5-owned
reason coverage of their own. Their integrity is enforced by the
v0.4.4 verifier (and transitively by v0.4.0..v0.4.3 verifiers) on
subprocess relay, under inherited reasons R01..R54.

The wrapping manifest itself is NOT counted as a subject. There is
NO `relying_party` top-level field on the v0.4.5 wrapping manifest;
`relying_party` is carried only on the v0.4.5 index body (sourced
from the v0.4.0 governed-reliance package body inside the v0.4.4
child closure).

## Top-Level Fields

The v0.4.5 wrapping manifest has exactly **12** top-level fields,
in the following fixed order:

| # | Field | Type | Required | Notes |
|---|---|---|---|---|
| 1 | `document_type` | string | yes | Must be `proofrail.gold.multi_case_reliance_package_manifest`. |
| 2 | `schema_version` | string | yes | Must be `v0.1.0`. |
| 3 | `proofrail_release` | string | yes | Must be `gold.multi_case_reliance.v0.4.5`. |
| 4 | `hash_algorithm` | string | yes | Must be `sha256`. |
| 5 | `manifest_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. v0.4.5-owned wrapping manifest identifier. MUST be distinct from any v0.4.4-child identifier (v0.4.4 wrapping manifest's `manifest_id`, `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `gold_reliance_package_index_id`, `package_id`, `governed_reliance_demo_id`). |
| 6 | `gold_multi_case_reliance_index_id` | string | yes | Same grammar. v0.4.5-owned. Cross-anchored to the v0.4.5 index body's `gold_multi_case_reliance_index_id`. MUST be distinct from any v0.4.4-child identifier. |
| 7 | `package_id` | string | yes | Same grammar. v0.4.5-owned. Cross-anchored to the v0.4.5 index body's `package_id`. MUST be distinct from any v0.4.4-child identifier. |
| 8 | `governed_reliance_demo_id` | string | yes | Same grammar. v0.4.5-owned. Cross-anchored to the v0.4.5 index body's `governed_reliance_demo_id`. MUST be distinct from any v0.4.4-child identifier. |
| 9 | `gold_reliance_package_index_ref` | string | yes | MUST equal `subjects[0].path`, i.e. `child-packages/v0.4.4/gold-reliance-package-index-manifest.json`. Relative three-segment path with fixed leading segments `child-packages/` and `v0.4.4/`. Path traversal (`..`) and absolute paths are rejected. |
| 10 | `decision_report_ref` | string | yes | MUST equal `child-packages/v0.4.4/child-packages/v0.4.1/gold-governed-reliance-decision-report.json` — the v0.4.1 decision-report body file reached through the v0.4.4 child closure. Same path constraints. |
| 11 | `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| 12 | `subjects` | array of exactly two objects | yes | Fixed order and roles (see `subjects[]`). |

## subjects[]

Exactly two entries in fixed order. The v0.4.5 wrapping manifest
does NOT carry a self-referential manifest-hash subject. The v0.4.4
child wrapping manifest lives under `child-packages/v0.4.4/`; the
v0.4.5 index body lives at the v0.4.5 package root.

### subjects[0]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_reliance_package_index_manifest`. |
| `path` | string | yes | Must equal `child-packages/v0.4.4/gold-reliance-package-index-manifest.json`. Relative three-segment path with fixed leading segments `child-packages/` and `v0.4.4/`. Path traversal (`..`) and absolute paths are rejected. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the byte-copied v0.4.4 wrapping-manifest bytes. No `sha256:` label prefix. |
| `size_bytes` | integer | yes | Byte length of the v0.4.4 wrapping-manifest file. |

### subjects[1]
| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Must be `gold_multi_case_reliance_index`. |
| `path` | string | yes | Must equal `gold-multi-case-reliance-index.json`. Relative single-segment file name. Path traversal (`..`) and absolute paths are rejected. |
| `sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.5 index body bytes (the canonical-JSON-encoded subject [1] file as written, including any file-level trailing newline). |
| `size_bytes` | integer | yes | Byte length of the v0.4.5 index body file. |

## Closed Reason Ownership (v0.4.5)

The v0.4.5 verifier owns a closed set of seven reasons, R55..R61.
The first two are owned by the wrapping manifest layer:

- R55 `gold_multi_case_reliance_manifest_invalid` — owns wrapping
  manifest structural integrity (required-field presence, type
  shape, closed identifier grammar, ISO-8601 UTC `generated_at`,
  fixed `document_type` / `schema_version` / `proofrail_release` /
  `hash_algorithm`, subject count exactly 2, subject role and order,
  per-subject required field shape, per-subject path traversal /
  absolute-path / exact-path equality, subject `sha256` bare
  lowercase hex grammar, subject `size_bytes` non-negative integer,
  cross-anchor with v0.4.5 index body for
  `gold_multi_case_reliance_index_id`, `package_id`, and
  `governed_reliance_demo_id`, exact equality of
  `gold_reliance_package_index_ref` with `subjects[0].path`, and
  path-grammar / traversal / absolute-path checks on both
  `gold_reliance_package_index_ref` and `decision_report_ref`).
  Path-traversal MUST be checked before exact-path equality
  (non-masking ordering).
- R56 `gold_multi_case_reliance_subject_digest_mismatch` — owns
  per-subject file-on-disk readability and integrity
  (existence/readability, declared `size_bytes` byte-match with
  actual byte length, declared `sha256` byte-match with re-derived
  SHA-256 over the on-disk file bytes).

Reasons R57..R61 are owned by the v0.4.5 index body layer (see
`gold-multi-case-reliance-index-v0.1.0.md`).

## Cross-Anchor Rules (manifest layer)

Wrapping-manifest-layer cross-anchor rules (all surface under R55):

- `gold_reliance_package_index_ref` MUST byte-match `subjects[0].path`.
- `decision_report_ref` MUST equal
  `child-packages/v0.4.4/child-packages/v0.4.1/gold-governed-reliance-decision-report.json`
  and MUST pass path-traversal / absolute-path checks.
- `gold_multi_case_reliance_index_id` MUST byte-match the v0.4.5
  index body's top-level `gold_multi_case_reliance_index_id`.
- `package_id` MUST byte-match the v0.4.5 index body's `package_id`.
- `governed_reliance_demo_id` MUST byte-match the v0.4.5 index
  body's `governed_reliance_demo_id`.

Cross-anchor between the v0.4.5 index body and the v0.4.4 child
closure (referenced v0.4.4 manifest SHA-256, the v0.4.4 index body
SHA-256, and the v0.4.1 decision-report body SHA-256) is owned by
the v0.4.5 index body layer (R58); see
`gold-multi-case-reliance-index-v0.1.0.md`.

## Path Constraints

- `subjects[0].path` is a relative three-segment path whose fixed
  leading two segments are exactly `child-packages/` and `v0.4.4/`;
  the third segment is the canonical v0.4.4 wrapping-manifest
  filename `gold-reliance-package-index-manifest.json`.
- `subjects[1].path` is a relative single-segment file name
  `gold-multi-case-reliance-index.json`.
- `gold_reliance_package_index_ref` MUST equal `subjects[0].path`.
- `decision_report_ref` is a relative five-segment path whose first
  four segments are exactly `child-packages/`, `v0.4.4/`,
  `child-packages/`, and `v0.4.1/`; the fifth segment is the v0.4.1
  decision-report-body filename
  `gold-governed-reliance-decision-report.json`.
- Absolute paths are rejected at every path field.
- Paths containing `..` are rejected at every path field.
- Subject count MUST be exactly 2.
- Subject roles and order are fixed:
  `gold_reliance_package_index_manifest`,
  `gold_multi_case_reliance_index`.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used. This
matches the v0.4.0..v0.4.4 convention.

## Child Package Closure Layout

The v0.4.5 package directory layout:

```
<package-root>/
├── gold-multi-case-reliance-package-manifest.json   (v0.4.5 wrapping manifest)
├── gold-multi-case-reliance-index.json              (v0.4.5 index body, subject[1])
└── child-packages/v0.4.4/
    ├── gold-reliance-package-index-manifest.json    (v0.4.4 wrapping manifest, subject[0])
    ├── gold-reliance-package-index.json             (v0.4.4 index body, NOT a v0.4.5 subject)
    └── child-packages/v0.4.X/                       (v0.4.0..v0.4.3 closures, NOT v0.4.5 subjects)
        └── <every subject file the v0.4.X manifest references>
```

The single v0.4.4 child closure is produced by exactly ONE
subprocess invocation of the co-located v0.4.4 runner against the
canonical v0.4.0/v0.4.2/v0.4.3 input fixtures. Files underneath
`child-packages/v0.4.4/` are NOT enumerated as v0.4.5
wrapping-manifest subjects. Their integrity is enforced by the
inherited v0.4.4 verifier (and transitively by v0.4.0..v0.4.3
verifiers) via subprocess relay under R01..R54.

## Verifier Reachability

The v0.4.5 verifier validates the wrapping manifest (R55) and
per-subject file-on-disk digests (R56) before any index-body layer
fold (R57..R61) and before invoking the inherited v0.4.4 verifier.
Path-traversal is checked before exact-path equality (non-masking).
The v0.4.5 verifier validates the index body (R57..R61) BEFORE
invoking the inherited v0.4.4 verifier, because R57..R61 are owned
by v0.4.5 and must be reachable without contaminating any inherited
verifier subprocess.

Inherited v0.4.4 verifier is invoked exactly once, on
`child-packages/v0.4.4/gold-reliance-package-index-manifest.json`.
Any inherited reason (R01..R54) is relayed verbatim by the v0.4.5
verifier with no rewriting, no narrowing, and no v0.4.5-owned
wrapper or synonym. The v0.4.5 verifier does NOT re-run the v0.4.4
builder; it verifies the supplied closure via the inherited
verifier.

If the inherited v0.4.4 verifier is missing or crashes with a
non-FAIL non-zero exit (i.e. anything other than 0 or 1), the
v0.4.5 verifier emits a non-reason-shaped `INFRA:` diagnostic on
stderr, exits with code 3 (distinct from verifier-reason exit 1),
and MUST NOT emit any public reason-shaped token (no R55..R61, no
inherited R01..R54, no runner-only refusal name).

## Runner-Only Refusal Vocabulary

The v0.4.5 runner reuses the same closed set of five runner-only
refusals from v0.4.0..v0.4.4 verbatim:

- `runner_input_path_missing`
- `runner_input_path_forbidden`
- `runner_input_file_missing`
- `runner_input_read_failed`
- `runner_input_json_invalid`

No sixth refusal is introduced. Runner-only refusals exit 1 and
are emitted only by the runner, never by the verifier.

## Exit Code Discipline

- Public verifier reasons (R55..R61 and inherited R01..R54 relayed
  verbatim) exit 1.
- Runner-only refusals exit 1.
- INFRA diagnostics (non-reason-shaped, prefixed `INFRA:` on
  stderr) exit 3.
- `argparse`'s own usage-error exit 2 is NOT a planned ProofRail
  refusal.

## Non-Claims

The wrapping manifest is not signed, not a certificate, not
federated, not a registry, not a federation handle, and not
production PKI. It is a local hash anchor for the v0.4.5 Gold
Multi-Case Reliance Demo. It does not transfer reliance, does not
authorize external acceptance, is not Gold certification, does not
redefine R01..R54, does not introduce a sixth runner-only refusal,
and does not re-derive the inherited v0.4.4 child manifest via any
builder during verification.
