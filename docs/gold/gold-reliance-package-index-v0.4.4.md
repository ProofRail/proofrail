# Gold Reliance Package Index — v0.4.4

**Status:** Released — ProofRail v0.4.4 — narrow incremental Gold release
**Release thesis:** ProofRail v0.4.4 is a narrow, deterministic wrapping of the four inherited Gold releases (v0.4.0 Governed Reliance Demo, v0.4.1 Decision Report Hardening, v0.4.2 Policy Evaluation Matrix, v0.4.3.1-baselined Challenge Lifecycle Lite) under a single 5-subject index manifest plus a single byte-stable index body. The index body asserts membership of seven artifact identifiers in a closed pairwise-distinctness collision class and re-binds the four child wrapping manifests by SHA-256, size, and path. v0.4.4 adds one new manifest layout (5 subjects: four child wrapping manifests plus the v0.4.4-owned index body), one new body file, six v0.4.4-owned verifier reasons (R49..R54), and a runtime closure layout (`child-packages/v0.4.X/`) that lets the v0.4.4 verifier subprocess-invoke each inherited verifier on its corresponding child manifest path without re-running any inherited builder. v0.4.4 does NOT introduce a new Gold tier, does NOT sign anything, does NOT federate, does NOT transfer reliance, and does NOT extend the substance of any inherited release.

---

## v0.4.4 thesis

> A package owner can re-use the unchanged v0.4.0 Minimal Gold Governed Reliance Demo, the unchanged v0.4.1 Gold Decision Report Hardening, the unchanged v0.4.2 Gold Policy Evaluation Matrix, and the unchanged v0.4.3 Gold Challenge Lifecycle Lite (under the corrected v0.4.3.1 verifier baseline), materialize each inherited release's complete child closure under its own `child-packages/v0.4.X/` subdirectory, project a deterministic local index body that pins each child wrapping manifest by SHA-256, size, and path and asserts membership of seven artifact identifiers in a closed pairwise-distinctness collision class, and bind the four child wrapping manifests and the index body under a 5-subject wrapping manifest. The v0.4.4 runner consumes exactly the inherited v0.4.3 input file chain (`--input-package`, `--matrix-input`, `--lifecycle-input`) and adds no new input template. The v0.4.4 verifier validates the wrapping manifest, validates the index body under six v0.4.4-owned structural checks (R49..R54), and then subprocess-invokes each of the four co-located inherited verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) on its corresponding child wrapping manifest path. Inherited reasons R02..R48 are relayed UNCHANGED. v0.4.4 does **not** assert any signed reliance instrument, certificate, federated acceptance, transferred reliance, regulator or auditor approval, legal acceptance, legal enforceability, production authorization, audit readiness, control operating effectiveness, runtime truth, live policy-engine output, live lifecycle adjudication, signed lifecycle attestation, full Gold, or Platinum.

## Reliance-index boundary

> A v0.4.4 Gold Reliance Package Index package is **not** a new Gold tier; it is **not** a certificate; it is **not** signed; it is **not** federated; it is **not** a transfer of reliance to any external party; it is **not** a regulator action, an auditor action, or a third-party endorsement; it is **not** legal acceptance, legal enforceability, or legal adjudication; it is **not** production authorization, production governance, or production PKI; it is **not** an audit-readiness assertion or a control-effectiveness assertion; it is **not** a runtime-truth oracle; it is **not** live policy-engine output; it is **not** live challenge-lifecycle adjudication; it is **not** a signed lifecycle attestation; it is **not** an external reliance authority; it is **not** a registry; it is **not** a federation handle; it is **not** full Gold; it is **not** Platinum. It is a hand-orchestrated structural wrapping of four inherited Gold releases under a 5-subject manifest and a byte-stable index body, with six v0.4.4-owned structural checks on the index body and inherited-verifier subprocess relay for the inherited 48-reason surface.

## Package layout

The runtime layout at `/tmp/proofrail-v044-reliance-package-index-demo/` is a multi-file output with one subdirectory per inherited release:

```
<output-dir>/
├── gold-reliance-package-index-manifest.json                       (wrapping manifest)
├── gold-reliance-package-index.json                                (subject [4]: index body)
├── child-packages/
│   ├── v0.4.0/
│   │   ├── gold-governed-reliance-package-manifest.json            (subject [0])
│   │   └── <every subject file referenced by the v0.4.0 manifest>
│   ├── v0.4.1/
│   │   ├── gold-decision-report-package-manifest.json              (subject [1])
│   │   └── <every subject file referenced by the v0.4.1 manifest>
│   ├── v0.4.2/
│   │   ├── gold-policy-evaluation-matrix-package-manifest.json     (subject [2])
│   │   └── <every subject file referenced by the v0.4.2 manifest>
│   └── v0.4.3/
│       ├── gold-challenge-lifecycle-package-manifest.json          (subject [3])
│       └── <every subject file referenced by the v0.4.3 manifest>
└── (no other v0.4.4-authored files)
```

The wrapping manifest carries:

- `document_type: proofrail.gold.reliance_package_index_manifest`
- `schema_version: v0.1.0`
- `proofrail_release: gold.reliance_package_index.v0.4.4`
- `hash_algorithm: sha256`
- `manifest_id` (NOT in the collision class), `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`, `gold_reliance_package_index_id` (all seven in the collision class)
- `package_id` and `governed_reliance_demo_id`, both cross-anchored to every child wrapping manifest and to the index body (binding anchors; NOT in the collision class)
- `generated_at` ISO-8601 UTC
- `subjects[0]`: role `gold_governed_reliance_package_manifest`, path `child-packages/v0.4.0/gold-governed-reliance-package-manifest.json`
- `subjects[1]`: role `gold_decision_report_package_manifest`, path `child-packages/v0.4.1/gold-decision-report-package-manifest.json`
- `subjects[2]`: role `gold_policy_evaluation_matrix_package_manifest`, path `child-packages/v0.4.2/gold-policy-evaluation-matrix-package-manifest.json`
- `subjects[3]`: role `gold_challenge_lifecycle_package_manifest`, path `child-packages/v0.4.3/gold-challenge-lifecycle-package-manifest.json`
- `subjects[4]`: role `gold_reliance_package_index`, path `gold-reliance-package-index.json`

Each subject carries a bare lowercase 64-hex `sha256` and an integer `size_bytes`. The wrapping manifest does NOT include a self-referential manifest-hash subject; v0.4.4 ships local hash anchors only.

The closure files under each `child-packages/v0.4.X/` subdirectory (every subject file the child wrapping manifest references) are runtime support files for the inherited verifier; they are NOT enumerated as v0.4.4 wrapping-manifest subjects and have no v0.4.4-owned reason coverage of their own. Their integrity is enforced by the inherited verifier's existing reasons (R02..R48) via subprocess relay.

## Index body

The index body at `gold-reliance-package-index.json` (subject [4]) is the only v0.4.4-authored payload. It carries:

- `document_type: proofrail.gold.reliance_package_index`
- `schema_version: v0.1.0`
- `proofrail_release: gold.reliance_package_index.v0.4.4`
- `hash_algorithm: sha256`
- `gold_reliance_package_index_id`, `package_id`, `governed_reliance_demo_id`, `generated_at`
- `entries[0..3]`: exactly four fixed-order entries, one per inherited release, each carrying `release_label`, `child_subject_index`, `child_package_root`, `child_manifest_path`, `child_manifest_fingerprint`, and `child_manifest_size_bytes`. The fingerprint and size of each entry must byte-match the wrapping manifest's `subjects[i].sha256` and `subjects[i].size_bytes`; the path must byte-match `subjects[i].path`.
- `coverage_summary`: closed-key object with five fields: `child_package_count = 4`, `inherited_release_count = 4`, `pairwise_distinct_id_count = 7`, `package_id_anchor_consistency = true`, `governed_reliance_demo_id_anchor_consistency = true`. Stray keys are rejected.
- `index_fingerprint`: bare lowercase 64-hex SHA-256 over `json.dumps(body_obj_without_index_fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")`.

## Subprocess delegation architecture

v0.4.4 does NOT re-implement any of the 47 inherited verifier-reason checks (R02..R48). The v0.4.4 **runner** subprocess-invokes each of the four co-located inherited runners (v0.4.0, v0.4.1, v0.4.2, v0.4.3) once, into its own `child-packages/v0.4.X/` subdirectory under the staging tree, where the inherited runner writes its complete child closure. The v0.4.3 child closure is built under the corrected v0.4.3.1 baseline. Each inherited runner is invoked with `--force` so the closure subdirectory can be (re)materialized within the v0.4.4 staging tree.

The v0.4.4 **verifier** subprocess-invokes each of the four co-located inherited verifiers (v0.4.0, v0.4.1, v0.4.2, v0.4.3) on its corresponding child wrapping-manifest path under `child-packages/v0.4.X/`. Each inherited verifier resolves its referenced subject files relative to the child manifest's directory using its own existing path-resolution rules. The inherited verifier's stdout/stderr is relayed verbatim; the v0.4.0, v0.4.1, v0.4.2, and v0.4.3 reason names appear unchanged in v0.4.4's failure output.

If any co-located inherited verifier is missing, non-executable, or crashes with a non-FAIL non-zero exit, the v0.4.4 verifier emits a non-reason-shaped `INFRA:` diagnostic on stderr and exits with code 3 (distinct from verifier-reason exit 1). The `INFRA:` diagnostic is deliberately not in the closed verifier reason set; it indicates an environmental failure, not a content failure of the v0.4.4-owned index body or of any inherited subject.

## Identifier grammar ownership

v0.4.4 owns the grammar of one identifier and inherits the grammar of the rest:

- v0.4.4-owned: `gold_reliance_package_index_id`. The v0.4.4 Phase 1 grammar check enforces the closed identifier grammar on this field and emits `gold_manifest_invalid` on failure. The wrapping manifest's `manifest_id` is also v0.4.4-tier but is NOT a member of the v0.4.4 collision class.
- Inherited from v0.4.0/v0.4.1/v0.4.2/v0.4.3: `package_id`, `governed_reliance_demo_id`, `conformance_report_id`, `decision_report_id`, `matrix_id`, `policy_evaluation_report_id`, `challenge_lifecycle_record_set_id`, `challenge_lifecycle_report_id`. Grammar of these eight identifiers is validated by inherited checks via subprocess relay; the v0.4.4 Phase 1 cross-anchors then enforce that the wrapping manifest's `package_id` and `governed_reliance_demo_id` equal every child wrapping manifest's matching fields and the index body's matching fields.

## 7-ID pairwise-distinctness collision class

The following **seven** identifiers MUST be pairwise distinct across the v0.4.4 wrapping manifest:

- `conformance_report_id`
- `decision_report_id`
- `matrix_id`
- `policy_evaluation_report_id`
- `challenge_lifecycle_record_set_id`
- `challenge_lifecycle_report_id`
- `gold_reliance_package_index_id`

All 21 pairwise collisions across this class surface at the manifest-integrity layer under R01 `gold_manifest_invalid`. They do NOT fold into the v0.4.4-owned R51 `gold_reliance_package_index_binding_invalid`, which is reserved for index-body-level cross-anchor mismatches.

Explicitly excluded from the collision class (these are cross-anchor binding identifiers, not report / lifecycle / index artifact IDs):

- `manifest_id`
- `package_id`
- `governed_reliance_demo_id`

The body's `coverage_summary.pairwise_distinct_id_count` MUST equal `7`; any other value surfaces under R53 `gold_reliance_package_index_summary_invalid`.

## 54 verifier reasons (48 inherited + 6 v0.4.4-owned)

The v0.4.4 verifier's closed reason set is the union of 48 inherited reasons R01..R48 (relayed verbatim from the co-located v0.4.0, v0.4.1, v0.4.2, and v0.4.3 verifiers via subprocess) and 6 v0.4.4-owned reasons R49..R54 over the new index body.

The 48 inherited reasons appear in their original v0.4.0/v0.4.1/v0.4.2/v0.4.3 forms. The 6 v0.4.4-owned reasons are:

| # | Reason | Trigger |
|---|---|---|
| 49 | `gold_reliance_package_index_not_object` | Index body file does not parse as a JSON object. |
| 50 | `gold_reliance_package_index_schema_invalid` | Index body top-level shape violation: missing required field, wrong type, disallowed value, or stray key at top-level / per-entry / `coverage_summary` layer. |
| 51 | `gold_reliance_package_index_binding_invalid` | Index body cross-anchor mismatch: `package_id`, `governed_reliance_demo_id`, or `gold_reliance_package_index_id` disagrees with the wrapping manifest or with a child wrapping manifest; or per-entry `child_manifest_fingerprint`, `child_manifest_size_bytes`, or `child_manifest_path` disagrees with the wrapping manifest's `subjects[i]`. |
| 52 | `gold_reliance_package_index_entry_invalid` | Per-entry shape or value violation: wrong `release_label`, wrong `child_subject_index`, wrong `child_package_root`, wrong `child_manifest_path` grammar, non-hex / wrong-length `child_manifest_fingerprint`, non-integer `child_manifest_size_bytes`, wrong entry count, wrong entry order. |
| 53 | `gold_reliance_package_index_summary_invalid` | `coverage_summary` arithmetic or shape violation: wrong `child_package_count`, wrong `inherited_release_count`, wrong `pairwise_distinct_id_count`, `package_id_anchor_consistency` not `true`, `governed_reliance_demo_id_anchor_consistency` not `true`. |
| 54 | `gold_reliance_package_index_fingerprint_invalid` | Recomputed `index_fingerprint` does not byte-match the body's embedded `index_fingerprint`. |

The collision-class invariant (24 inherited R01 manifest-integrity failures from v0.4.0..v0.4.3 plus the v0.4.4-owned 21 pairwise-collision cases over the 7-ID class) is summarized:

> **54 = 48 inherited reasons R01..R48 + 6 v0.4.4-owned reasons R49..R54.**

## Reachability orderings (v0.4.4-owned phases)

- **Phase 1 — wrapping-manifest integrity.** Manifest shape, subject path constraints (path-traversal rejected BEFORE exact path equality), subject count == 5, subject role/order, subject SHA-256 / size_bytes match against the bytes on disk, identifier grammar on `manifest_id` and `gold_reliance_package_index_id`. All failures here fold into R01.
- **Phase 2 — wrapping-manifest cross-anchor.** `package_id` and `governed_reliance_demo_id` equality across the wrapping manifest, every child wrapping manifest, and the index body. The 6 inherited collision-class IDs equal their matching fields in the corresponding child wrapping manifests. The v0.4.4-owned `gold_reliance_package_index_id` equals the index body's matching field. All 21 pairwise collisions among the seven collision-class IDs fold into R01.
- **Phase 3 — index body re-derivation, fixed v0.4.4 order:** R49 → R50 → R52 → R53 → R51 → R54. R49 fires only when the body file does not parse as a JSON object. R50 fires for top-level / per-entry / `coverage_summary` shape violations. R52 fires for per-entry shape / value violations once the top-level shape is valid. R53 fires for `coverage_summary` shape and arithmetic violations once the per-entry shape is valid. R51 fires for index-body-level cross-anchor mismatches once shape and entries are valid. R54 fires last, only when shape, entries, summary, and bindings are all valid but the recomputed `index_fingerprint` does not byte-match. The order is asserted by the v0.4.4 regression harness's R49..R54 reachability fixtures (case49..case54).
- **Phase 4 — inherited verifier invocation, fixed order:** v0.4.0 verifier on `child-packages/v0.4.0/...`, then v0.4.1 verifier on `child-packages/v0.4.1/...`, then v0.4.2 verifier on `child-packages/v0.4.2/...`, then v0.4.3 verifier on `child-packages/v0.4.3/...`. Any inherited reason R02..R48 surfaces UNCHANGED. Environmental failure surfaces under a non-reason-shaped `INFRA:` diagnostic with exit code 3.

R49..R54 are validated BEFORE any inherited verifier subprocess so that the v0.4.4-owned reasons are reachable without contaminating any inherited verifier's namespace.

## Runner architecture

Phase A (preflight) emits exactly the same 5 approved runner-only refusal reasons as v0.4.0..v0.4.3, applied to every input-path argument BEFORE any output directory touch:

- `runner_input_path_missing`
- `runner_input_path_forbidden`
- `runner_input_file_missing`
- `runner_input_read_failed`
- `runner_input_json_invalid`

The runner never wraps a verifier failure under a sixth runner-only refusal code. With `--self-validate`, a verifier failure is relayed verbatim from the v0.4.4 verifier's own stdout/stderr; the staging directory is removed and the destination is left untouched.

Phase B (staging) creates `<output-dir>.staging.<pid>`, subprocess-invokes the four inherited runners into their respective `child-packages/v0.4.X/` subdirectories, projects the seven collision-class IDs into the wrapping manifest, derives the index body from the materialized child wrapping manifests (per-entry fingerprint and size byte-match the materialized child wrapping manifests; `coverage_summary` arithmetic is byte-deterministic; `index_fingerprint` is recomputed last), writes the wrapping manifest and the index body, runs the v0.4.4 verifier under `--self-validate`, and atomically `os.replace()`s the staging directory into the destination.

## TG1 allowlist discipline (v0.4.4 harness)

The v0.4.4 regression harness ships TG1 with a closed allowlist limited to **inherited-tier short-form data-field labels** that share the v0.4.4 reason-shaped suffix grammar (`_invalid`, `_not_object`, `_missing`, `_forbidden`, `_failed`, `_unsupported`, `_present`). No v0.4.4-introduced data field is a substring of any v0.4.4 reason name in R49..R54: the v0.4.4 index body deliberately uses field names like `gold_reliance_package_index_id`, `child_manifest_fingerprint`, `child_manifest_size_bytes`, `child_manifest_path`, `pairwise_distinct_id_count`, `package_id_anchor_consistency`, and `governed_reliance_demo_id_anchor_consistency`, none of which match the reason-shaped suffix grammar.

The TG1 scanner's token-match regex is non-greedy with a trailing `\b` to prevent spurious capture of shorter tokens (e.g., `binding_invalid`) inside longer composite tokens (e.g., `binding_invalid_package_id`). The TG1 DENY patterns are string-concatenated at runtime so the literal full token never appears in the scanner's own source; otherwise the scanner self-trips when this file is scanned.

## INFRA diagnostic boundary

The `INFRA:` diagnostic is reserved for environmental failures of the v0.4.4 verifier's subprocess invocation of an inherited verifier. It is NOT a member of the closed verifier reason set and does NOT appear in any TG1 allowlist or DENY pattern. The diagnostic surface is exactly `INFRA: <one-line message>` on stderr followed by exit code 3.

## Test scratch path policy

The v0.4.4 regression harness scratch path is `tests/_tmp_gold_reliance_package_index_v0_4_4/` (test-owned; fail-safe pre-existence check, EXIT-trap cleanup, explicit no-residue assertion before SS-AFTER). No test artifact is ever written under an inherited-tier fixture directory.

## Non-claims

The v0.4.4 tooling does not certify, audit, approve, transfer, federate, register, sign, attest, adjudicate, or operate any production system. It records a deterministic local hand-orchestrated wrapping of four inherited Gold releases under a closed-vocabulary index body and a 5-subject wrapping manifest, validates structural shape, identifier grammar, the 7-ID pairwise-distinctness collision class, and byte-equality of per-entry fingerprints / sizes / paths against the materialized child wrapping manifests, and subprocess-relays the inherited 47-reason surface verbatim. It does not consult any live service, gateway, observability backend, policy engine, GRC platform, registry, federation, lifecycle adjudication authority, or external authority. It does not re-derive or summarize inherited subject bodies. It is not signed and ships local hash anchors only. It is not a new Gold tier. It is not full Gold. It is not Platinum.
