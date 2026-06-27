# Gold Multi-Case Reliance Index Body Schema v0.1.0

Schema for the body file referenced as subject [1] of the v0.4.5
Gold Multi-Case Reliance Demo wrapping manifest. The index body is
the only v0.4.5-authored payload in the v0.4.5 package; subject [0]
is a byte-copy of the v0.4.4 Gold Reliance Package Index wrapping
manifest reached via a single canonical v0.4.4 child closure under
`child-packages/v0.4.4/`.

## Boundary

The index body is a local, derived multi-case projection over the
inherited v0.4.4 Gold Reliance Package Index child closure. It is
NOT a signature, NOT a certificate, NOT federated, NOT a registry,
NOT a federation handle, and NOT full Gold. It does NOT transfer
reliance.

The index body contains exactly five case entries (one per
governed_decisions[] entry in the v0.4.0 governed-reliance package
body reached through the v0.4.4 child closure, in natural v0.4.0
order), top-level cross-anchor binding identifiers, the SHA-256 of
the v0.4.4 index body, the SHA-256 of the v0.4.1 decision-report
body, and a single canonical-JSON SHA-256 fingerprint
(`multi_case_index_fingerprint`) computed over the canonical JSON
of the index body with the `multi_case_index_fingerprint` field
excluded.

## Top-Level Fields

The v0.4.5 index body has exactly **15** top-level fields, in the
following fixed order:

| # | Field | Type | Required | Notes |
|---|---|---|---|---|
| 1 | `document_type` | string | yes | Must be `proofrail.gold.multi_case_reliance_index`. |
| 2 | `schema_version` | string | yes | Must be `v0.1.0`. |
| 3 | `proofrail_release` | string | yes | Must be `gold.multi_case_reliance.v0.4.5`. |
| 4 | `hash_algorithm` | string | yes | Must be `sha256`. |
| 5 | `gold_multi_case_reliance_index_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. v0.4.5-owned. Cross-anchored to the wrapping manifest's `gold_multi_case_reliance_index_id`. MUST be distinct from any v0.4.4-child identifier. |
| 6 | `package_id` | string | yes | Same grammar. v0.4.5-owned. Cross-anchored to the wrapping manifest's `package_id`. MUST be distinct from any v0.4.4-child identifier. |
| 7 | `governed_reliance_demo_id` | string | yes | Same grammar. v0.4.5-owned. Cross-anchored to the wrapping manifest's `governed_reliance_demo_id`. MUST be distinct from any v0.4.4-child identifier. |
| 8 | `gold_reliance_package_index_ref` | string | yes | MUST equal the wrapping manifest's `gold_reliance_package_index_ref`, i.e. `child-packages/v0.4.4/gold-reliance-package-index-manifest.json`. Same path constraints. |
| 9 | `gold_reliance_package_index_sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.4 **index body** file at `child-packages/v0.4.4/gold-reliance-package-index.json` (NOT the v0.4.4 wrapping manifest). |
| 10 | `decision_report_ref` | string | yes | MUST equal the wrapping manifest's `decision_report_ref`, i.e. `child-packages/v0.4.4/child-packages/v0.4.1/gold-governed-reliance-decision-report.json`. Same path constraints. |
| 11 | `decision_report_sha256` | string | yes | Bare lowercase hex SHA-256 of the v0.4.1 decision-report body file reached through the v0.4.4 child closure at the path given by `decision_report_ref`. |
| 12 | `generated_at` | string | yes | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| 13 | `relying_party` | object | yes | Sourced from the v0.4.0 governed-reliance package body reached through the v0.4.4 child closure (at `child-packages/v0.4.4/child-packages/v0.4.0/governed-reliance-scenarios.json`), NOT from the v0.4.4 wrapping manifest. Byte-stable copy of the v0.4.0 body's `relying_party` object. |
| 14 | `cases` | array of exactly five objects | yes | Fixed order (natural v0.4.0 order, indexed 0..4). See `cases[]`. |
| 15 | `multi_case_index_fingerprint` | string | yes | Bare lowercase hex SHA-256 (64 chars, `[0-9a-f]{64}`) of the canonical-JSON byte-encoding of this body object with the `multi_case_index_fingerprint` field itself excluded. Canonical JSON is `json.dumps(obj, sort_keys=True, separators=(",",":")).encode("utf-8")`. |

## cases[]

Exactly five entries in natural v0.4.0 order (the order of
`governed_decisions[]` in the v0.4.0 governed-reliance package body
reached through the v0.4.4 child closure). Each entry pins one
case derived from one v0.4.0 `governed_decisions[]` entry plus its
projections in the v0.4.1 decision-report body, the v0.4.2
evaluation-report body, and the v0.4.3 lifecycle-records body, each
reached through the v0.4.4 child closure.

### Per-entry fields (closed set, fixed order)

| # | Field | Type | Required | Notes |
|---|---|---|---|---|
| 1 | `case_id` | string | yes | Closed grammar `^[a-z][a-z0-9_]*(-[a-z0-9]+)*$`. v0.4.5-owned per-case identifier. MUST be distinct across all five cases. MUST be distinct from any v0.4.4-child identifier. |
| 2 | `case_slug` | string | yes | Sourced verbatim from the v0.4.0 `governed_decisions[i].scenario_type`. Closed set: `clean_acceptance`, `policy_rejection`, `challenge_filed`, `withdrawal`, `supersession`. |
| 3 | `case_index` | integer | yes | Natural v0.4.0 index. MUST equal the position in `cases[]` (0..4). NOT a boolean. |
| 4 | `governed_decision_id` | string | yes | Sourced verbatim from the v0.4.0 `governed_decisions[i].decision_id`. |
| 5 | `decision_row_id` | string | yes | Sourced from the v0.4.1 decision-report body via `decision_rows[]`, by matching `decision_rows[].decision_id == governed_decision_id`. |
| 6 | `matrix_row_id` | string &#124; null | yes | Sourced from the v0.4.2 evaluation-report body via `evaluation_rows[]`, by matching `evaluation_rows[].decision_id == governed_decision_id`; the resulting `evaluation_rows[].matrix_row_id` is recorded here (this is a JOIN via `evaluation_rows[]`, NOT a direct lookup in `matrix_rows[]` by `decision_id`). May be `null` when the joined `evaluation_rows[]` entry's `matrix_row_id` is `null` (`decision_row_uncovered` evaluation status). |
| 7 | `evaluation_row_id` | string &#124; null | yes | Sourced from the v0.4.2 evaluation-report body via `evaluation_rows[]`, by matching `evaluation_rows[].decision_id == governed_decision_id`; the resulting `evaluation_rows[].evaluation_row_id` is recorded here. May be `null` if no matching evaluation row was produced for the decision. |
| 8 | `lifecycle_record_id` | string &#124; null | yes | Sourced from the v0.4.3 lifecycle-records body via `lifecycle_records[].lifecycle_id`, by matching `lifecycle_records[].target_decision_id == governed_decision_id`. May be `null` when the v0.4.3 body has no matching lifecycle record. |
| 9 | `lifecycle_record_fingerprint` | string &#124; null | yes | Bare lowercase hex SHA-256 (`[0-9a-f]{64}`) sourced from the v0.4.3 lifecycle-records body's matching `lifecycle_records[].lifecycle_fingerprint`. May be `null` only when `lifecycle_record_id` is also `null` (paired-null rule). When non-null, MUST be a bare lowercase 64-char hex string and MUST byte-match the v0.4.3 body's `lifecycle_records[].lifecycle_fingerprint`. |
| 10 | `outcome` | string | yes | Sourced verbatim from the v0.4.0 `governed_decisions[i].decision_status`. Closed set: `accepted`, `rejected`, `challenged`, `withdrawn`, `superseded`. |

### Paired-null rule

`lifecycle_record_id` and `lifecycle_record_fingerprint` MUST be
paired: either both `null` or both non-`null`. Any combination of
one null + one non-null is a structural violation (R60).

### case_index rule

`cases[i].case_index` MUST equal the integer position `i` (0..4) of
the entry in the `cases[]` array. Booleans are NOT valid integer
positions and are rejected.

## Closed Reason Ownership (index body layer)

The v0.4.5 verifier owns the following five index-body-layer
reasons:

- R57 `gold_multi_case_reliance_index_invalid` — owns
  not-a-JSON-object, top-level required-field presence, type shape,
  closed identifier grammar, closed value sets
  (`document_type`, `schema_version`, `proofrail_release`,
  `hash_algorithm`), ISO-8601 UTC `generated_at`,
  `gold_reliance_package_index_sha256` and
  `decision_report_sha256` bare lowercase hex grammar,
  `multi_case_index_fingerprint` bare lowercase hex grammar,
  `relying_party` object shape, stray-key discipline at the
  top level, and `gold_reliance_package_index_ref` /
  `decision_report_ref` path-grammar / traversal / absolute-path
  checks. Path-traversal MUST be checked before exact-path
  equality.
- R58 `gold_multi_case_reliance_child_manifest_binding_invalid` —
  owns cross-anchor binding between the v0.4.5 index body and the
  v0.4.4 child closure: `gold_reliance_package_index_ref` byte-
  matches `subjects[0].path`,
  `gold_reliance_package_index_sha256` byte-matches the SHA-256
  re-derived from the v0.4.4 **index body** file on disk,
  `decision_report_ref` byte-matches the wrapping manifest's
  `decision_report_ref`, and `decision_report_sha256` byte-matches
  the SHA-256 re-derived from the v0.4.1 decision-report body
  reached through the v0.4.4 child closure. Cross-anchor of
  `relying_party` byte-equality against the v0.4.0
  governed-reliance package body (reached through the v0.4.4 child
  closure) also surfaces here.
- R59 `gold_multi_case_reliance_case_count_invalid` — owns the
  `cases[]` array shape (must be a JSON array, must contain
  exactly 5 entries), and the natural-order pin
  (`cases[i].case_index == i`).
- R60 `gold_multi_case_reliance_case_binding_invalid` — owns
  per-case shape and per-case cross-anchor: per-case required-
  field presence and type shape, closed `case_id` identifier
  grammar, `case_id` pairwise-distinct across the five cases,
  `case_id` distinct from any v0.4.4-child identifier, `case_slug`
  closed value set, `outcome` closed value set, `case_slug` /
  `governed_decision_id` / `outcome` byte-equality with the v0.4.0
  body's matching `governed_decisions[i]` entry, `decision_row_id`
  cross-join with the v0.4.1 body's `decision_rows[]` by
  `decision_id`, `matrix_row_id` and `evaluation_row_id` cross-
  join with the v0.4.2 body's `evaluation_rows[]` by
  `decision_id`, `lifecycle_record_id` cross-join with the v0.4.3
  body's `lifecycle_records[]` by `target_decision_id`,
  `lifecycle_record_fingerprint` byte-equality with the matching
  v0.4.3 `lifecycle_records[].lifecycle_fingerprint`, and the
  paired-null rule for `lifecycle_record_id` /
  `lifecycle_record_fingerprint`.
- R61 `gold_multi_case_reliance_index_rederive_mismatch` —
  owns the `multi_case_index_fingerprint` re-derivation: the
  verifier independently recomputes
  `sha256(canonical_json(body_without_multi_case_index_fingerprint))`
  and surfaces a byte-mismatch against the declared
  `multi_case_index_fingerprint` here. R61 MUST be testable by
  mutating only `multi_case_index_fingerprint` to a wrong but
  well-formed 64-char lowercase hex value (artifact-based
  mutation), with no importlib monkey-patching and no
  `_emit_fail` interception.

R55..R56 (manifest-layer reasons) are owned by the wrapping
manifest schema in `gold-multi-case-reliance-package-manifest-v0.1.0.md`.

## Check Order (locked)

The v0.4.5 verifier MUST evaluate the seven reason classes in the
following locked, non-masking order:

```
R55 -> R56 -> R57 -> R58 -> R59 -> R60 -> R61
```

R55 (manifest-layer structure) and R56 (per-subject digest) surface
at the wrapping manifest layer. R57..R61 surface at the index body
layer, in this exact order: R57 (top-level shape) before R58
(top-level cross-anchor binding) before R59 (cases[] count and
natural-order pin) before R60 (per-case shape and per-case
cross-anchor) before R61 (fingerprint re-derivation). The first
failing check returns its reason and stops further evaluation in
that pass; later checks do not run when an earlier check fails.

## Cross-Anchor Rules (body layer)

Index-body-layer cross-anchor rules (surface under R58 unless
otherwise specified):

- `gold_reliance_package_index_ref` MUST byte-match the wrapping
  manifest's `gold_reliance_package_index_ref` and MUST byte-match
  `subjects[0].path`.
- `gold_reliance_package_index_sha256` MUST byte-match the SHA-256
  re-derived from the v0.4.4 index body file
  (`child-packages/v0.4.4/gold-reliance-package-index.json`) as it
  exists on disk. This is the v0.4.4 **index body** file, not the
  v0.4.4 wrapping manifest file.
- `decision_report_ref` MUST byte-match the wrapping manifest's
  `decision_report_ref`.
- `decision_report_sha256` MUST byte-match the SHA-256 re-derived
  from the v0.4.1 decision-report body file
  (`child-packages/v0.4.4/child-packages/v0.4.1/gold-governed-reliance-decision-report.json`)
  as it exists on disk.
- `relying_party` MUST byte-equal (after canonical-JSON
  re-encoding) the `relying_party` object of the v0.4.0
  governed-reliance package body reached through the v0.4.4 child
  closure (at
  `child-packages/v0.4.4/child-packages/v0.4.0/governed-reliance-scenarios.json`).

Per-case cross-anchor rules (surface under R60):

- For each `i` in `[0..4]`,
  `cases[i].case_slug == v0.4.0.governed_decisions[i].scenario_type`.
- For each `i` in `[0..4]`,
  `cases[i].governed_decision_id == v0.4.0.governed_decisions[i].decision_id`.
- For each `i` in `[0..4]`,
  `cases[i].outcome == v0.4.0.governed_decisions[i].decision_status`.
- For each `i` in `[0..4]`, there MUST exist exactly one
  `decision_rows[]` entry in the v0.4.1 body with
  `decision_id == cases[i].governed_decision_id`, and
  `cases[i].decision_row_id` MUST equal that entry's `row_id`.
- For each `i` in `[0..4]`, there MUST exist exactly one
  `evaluation_rows[]` entry in the v0.4.2 body with
  `decision_id == cases[i].governed_decision_id`;
  `cases[i].matrix_row_id` MUST equal that entry's `matrix_row_id`
  (which may be `null` for `decision_row_uncovered`), and
  `cases[i].evaluation_row_id` MUST equal that entry's
  `evaluation_row_id`.
- For each `i` in `[0..4]`, there MUST be either zero or one
  `lifecycle_records[]` entry in the v0.4.3 body with
  `target_decision_id == cases[i].governed_decision_id`. If one,
  `cases[i].lifecycle_record_id` MUST equal that entry's
  `lifecycle_id`, and `cases[i].lifecycle_record_fingerprint` MUST
  byte-match that entry's `lifecycle_fingerprint`. If zero, both
  `cases[i].lifecycle_record_id` and
  `cases[i].lifecycle_record_fingerprint` MUST be `null` (paired-
  null rule).

## Fingerprint Rule

`multi_case_index_fingerprint` is computed exactly as:

```
canonical = json.dumps(body_obj_without_multi_case_index_fingerprint,
                       sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
multi_case_index_fingerprint = hashlib.sha256(canonical).hexdigest()
```

where `body_obj_without_multi_case_index_fingerprint` is the body
object with the `multi_case_index_fingerprint` key removed. The
output is bare lowercase hexadecimal (64 chars, `[0-9a-f]{64}`).
No `sha256:` label prefix.

R61 (`gold_multi_case_reliance_index_rederive_mismatch`) MUST be
artifact-reachable: mutating only `multi_case_index_fingerprint`
on the staged-and-published body file to a different but
well-formed 64-char lowercase hex value MUST cause the v0.4.5
verifier to emit R61 verbatim with exit code 1. R61 MUST NOT be
testable only via importlib monkey-patching or `_emit_fail`
interception.

## Path Constraints

- `gold_reliance_package_index_ref` is a relative three-segment
  path with fixed leading segments `child-packages/` and
  `v0.4.4/`, with the third segment being the canonical v0.4.4
  wrapping-manifest filename `gold-reliance-package-index-manifest.json`.
- `decision_report_ref` is a relative five-segment path whose
  first four segments are `child-packages/`, `v0.4.4/`,
  `child-packages/`, and `v0.4.1/`, with the fifth segment being
  the v0.4.1 decision-report-body filename
  `gold-governed-reliance-decision-report.json`.
- Absolute paths are rejected at every path field.
- Paths containing `..` are rejected at every path field.
- `cases[]` count is exactly 5.
- `cases[]` order is fixed: natural v0.4.0 order.

## Hash Format

SHA-256 values appear in bare lowercase hexadecimal (64 characters,
`[0-9a-f]{64}`). The `sha256:` label prefix is NOT used. This
matches the v0.4.0..v0.4.4 convention.

## Stray-Key Discipline

Top-level body fields and per-case fields are closed. Any stray key
at any of these layers surfaces under R57 (top-level) or R60 (per-
case). Closed discipline matches the v0.4.4 body schema's empty-TG
closed-allowlist discipline: no v0.4.5-named data field is a
substring of any v0.4.5 reason name in R55..R61.

## Non-Claims

The index body is not signed, not a certificate, not federated, not
a registry, not a federation handle, and not production PKI. It is
a local v0.4.5-owned multi-case projection over the inherited
v0.4.4 Gold Reliance Package Index child closure (which itself
indexes v0.4.0..v0.4.3). It does NOT transfer reliance, does NOT
authorize external acceptance, and is NOT Gold certification. It
does NOT re-derive or summarize inherited subject bodies beyond
what is locked in `cases[]`; per-case fields reference inherited
documents through join keys (`decision_id`, `target_decision_id`),
NOT by re-deriving them.
