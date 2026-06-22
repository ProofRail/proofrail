# ProofRail Silver Multi-Agent Demo Package Manifest Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-agent trust-boundary demo packages

---

## 1. Purpose

The Silver Multi-Agent Demo Package Manifest is a local hash-based integrity artifact for a packaged Silver multi-agent trust-boundary demo (v0.2.5). It enumerates SHA-256 digests for the package-level documentation and summary artifacts emitted by `tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py`, and it references the nested v0.2.4 harness evidence manifest.

It enables a relying party to detect tampering with:

- the package README;
- the package walkthrough;
- the demo summary;
- the nested harness evidence manifest pointer;
- and, by chain, every artifact already covered by the nested harness evidence manifest.

The manifest is **not**:

- a Silver Signed Bundle Assertion;
- a Silver Verifier Output Attestation;
- a Bronze evidence bundle manifest;
- a signed certification artifact;
- a Gold conformance certificate.

It is local hash-based integrity evidence only. v0.2.5 does not introduce new signed evidence or new verifier-output attestation logic.

---

## 2. Relationship to v0.2.4 Harness Evidence

The demo package manifest does **not** re-hash every nested harness subject. The nested `harness-evidence-manifest.json` already covers them.

The package manifest hashes only the nested manifest file itself (as a single package subject of role `nested_harness_evidence_manifest`). Verification of the nested subjects is delegated to the unchanged v0.2.4 verifier:

```text
tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py
```

This avoids duplicating per-event request and decision-report digests across two manifests while still binding the package to a specific nested evidence manifest by hash.

---

## 3. Format

JSON. UTF-8 encoded. Serialized with `json.dumps(obj, indent=2, sort_keys=True)` followed by a trailing newline for deterministic output.

---

## 4. Top-Level Structure

```json
{
  "document_type": "proofrail.silver.multi_agent_demo_package_manifest",
  "schema_version": "v0.1.0",
  "demo_id": "<string>",
  "proofrail_release": "v0.2.5",
  "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
  "generated_at": "<ISO-8601>",
  "package_root": ".",
  "hash_algorithm": "sha256",
  "subjects": [ ... ],
  "nested_verification": {
    "harness_evidence_verified": true,
    "verifier": "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py",
    "nested_manifest_path": "harness-evidence/harness-evidence-manifest.json"
  },
  "limitations": [ ... ]
}
```

All top-level fields are required.

| Field | Notes |
|---|---|
| `document_type` | Must equal `proofrail.silver.multi_agent_demo_package_manifest`. |
| `schema_version` | Must equal `v0.1.0`. |
| `demo_id` | Stable demo identifier, e.g. `proofrail-silver-demo-003-multi-agent-trust-boundary`. |
| `proofrail_release` | Must equal `v0.2.5`. |
| `generated_by` | Path to the packager tool. |
| `generated_at` | Wall-clock ISO-8601 UTC manifest creation time. Documentation only. |
| `package_root` | Logical package root anchor. Must be `"."`. |
| `hash_algorithm` | Must equal `sha256`. |
| `subjects` | Non-empty list of subject entries. |
| `nested_verification` | Mapping recording whether the v0.2.4 verifier was invoked on the nested manifest at packaging time. |
| `limitations` | Non-empty list of non-claim strings. |

---

## 5. Subject Entries

Each subject:

```json
{
  "role": "<enum>",
  "path": "<relative-path>",
  "sha256": "sha256:<64-hex>",
  "size_bytes": <int>
}
```

| `role` | Semantics |
|---|---|
| `demo_readme` | Package-level README copied into the output directory. |
| `demo_walkthrough` | Package-level walkthrough copied into the output directory. |
| `demo_summary` | Packager-emitted `demo-summary.json`. |
| `nested_harness_evidence_manifest` | The v0.2.4 `harness-evidence-manifest.json` produced by the harness runner. |

Paths are relative to the package root (the output directory containing this manifest). Paths **must not** contain `..` components and **must not** be absolute. The verifier rejects any subject path containing `..` or starting with `/` with `demo_subject_path_traversal`.

`sha256` is the literal lowercase hex digest of the raw file bytes, prefixed with `sha256:`.

`size_bytes` is the file size at manifest generation. The verifier recomputes hashes; the size field is metadata only.

---

## 6. Subject Ordering

Subjects are emitted in a deterministic order:

1. `demo_readme` (`README.md`)
2. `demo_walkthrough` (`demo-walkthrough.md`)
3. `demo_summary` (`demo-summary.json`)
4. `nested_harness_evidence_manifest` (`harness-evidence/harness-evidence-manifest.json`)

Additional package-level subjects, if any, must appear after these four in stable lexical order by `path`. The four roles above are mandatory.

---

## 7. Nested Verification Block

The `nested_verification` mapping records whether the packager invoked the v0.2.4 verifier on the nested manifest at packaging time:

```json
{
  "harness_evidence_verified": true,
  "verifier": "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py",
  "nested_manifest_path": "harness-evidence/harness-evidence-manifest.json"
}
```

- `harness_evidence_verified` must be `true`. The packager refuses to emit a package manifest if the nested verifier exits non-zero.
- `verifier` must be the v0.2.4 verifier path.
- `nested_manifest_path` must equal the `path` of the `nested_harness_evidence_manifest` subject.

This block documents the packager's pre-flight check. The package verifier still re-runs the nested verifier on every verify invocation.

---

## 8. Limitations

The `limitations` list must be non-empty. Recommended entries:

```
Local hash-based integrity evidence only.
Not a signed certification artifact.
Not Bronze, Silver Signed Bundle Assertion, or Verifier Output Attestation evidence.
Not production-grade evidence packaging.
Not Gold certification.
```

---

## 9. Example

```json
{
  "demo_id": "proofrail-silver-demo-003-multi-agent-trust-boundary",
  "document_type": "proofrail.silver.multi_agent_demo_package_manifest",
  "generated_at": "2026-06-21T12:30:01Z",
  "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
  "hash_algorithm": "sha256",
  "limitations": [
    "Local hash-based integrity evidence only.",
    "Not a signed certification artifact.",
    "Not Gold certification."
  ],
  "nested_verification": {
    "harness_evidence_verified": true,
    "nested_manifest_path": "harness-evidence/harness-evidence-manifest.json",
    "verifier": "tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py"
  },
  "package_root": ".",
  "proofrail_release": "v0.2.5",
  "schema_version": "v0.1.0",
  "subjects": [
    {
      "path": "README.md",
      "role": "demo_readme",
      "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 0
    },
    {
      "path": "demo-walkthrough.md",
      "role": "demo_walkthrough",
      "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 0
    },
    {
      "path": "demo-summary.json",
      "role": "demo_summary",
      "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 0
    },
    {
      "path": "harness-evidence/harness-evidence-manifest.json",
      "role": "nested_harness_evidence_manifest",
      "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 0
    }
  ]
}
```

---

## 10. Verification Rules

The accompanying verifier `tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py` performs, in order:

1. Parse the package manifest JSON. Malformed JSON → `invalid_demo_package_manifest`.
2. Validate `document_type`, `schema_version`, `proofrail_release`, `hash_algorithm`, `package_root`, non-empty `subjects`, non-empty `limitations`, well-formed `nested_verification`. → `invalid_demo_package_manifest`.
3. Reject any subject `path` containing `..` or starting with `/`. → `demo_subject_path_traversal`.
4. Confirm every subject file exists under the package root. → `demo_subject_file_missing`.
5. Recompute SHA-256 for every subject and compare to the manifest. → `demo_subject_hash_mismatch`.
6. Parse and structurally validate `demo-summary.json`. Malformed JSON or structural errors → `invalid_demo_summary`. JSON parse errors are caught and surfaced as `invalid_demo_summary` (the verifier must not leak Python tracebacks).
7. Cross-check the demo summary's required claim IDs and their evidence references against the nested harness run report and decision reports. Missing claim → `demo_claim_missing`. Claim status not `pass` or required evidence cross-check fails → `demo_claim_failed`. Evidence ref points to a file or event that does not match the claim → `demo_evidence_ref_invalid`. Evidence ref containing `..` or absolute → `demo_evidence_ref_invalid`.
8. Confirm `execution.protected_actions_performed == false` in `demo-summary.json` and in the nested run report. → `demo_execution_violation`.
9. Invoke the v0.2.4 verifier on the nested `harness-evidence/harness-evidence-manifest.json` as a subprocess. Any nested verifier failure → top-level reason `nested_harness_evidence_invalid` (the underlying nested reason such as `subject_hash_mismatch` may be included as context only; the top-level stable reason is always `nested_harness_evidence_invalid`).
10. Exit 0 only if all checks pass.

Verifier exit codes: `0` (valid), `1` (invalid), `2` (usage/input error).

---

## 11. Stable Failure Reasons

```
invalid_demo_package_manifest
demo_subject_path_traversal
demo_subject_file_missing
demo_subject_hash_mismatch
invalid_demo_summary
demo_claim_missing
demo_claim_failed
demo_evidence_ref_invalid
demo_execution_violation
nested_harness_evidence_invalid
```

These reasons are stable. Relying-party tooling may match on them.

---

## 12. Non-Claims

```
v0.2.5 packages a deterministic local Silver demo. It does not certify live agents, production deployments, or governed institutional acceptance.
v0.2.5 names the Gold boundary. It does not cross it.
```

---

## 13. Changelog

- **v0.1.0 (2026-06-21):** Initial schema.
