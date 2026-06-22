# ProofRail Silver Multi-Agent Harness Evidence Manifest Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-agent attack harness evidence manifests

---

## 1. Purpose

The Silver Multi-Agent Harness Evidence Manifest is a local hash-based integrity artifact for the output of a single harness execution. It enumerates SHA-256 digests for every harness input copied into the output directory and every harness output written into the output directory.

It enables a relying party to detect tampering with:

- the harness script (as copied into the output);
- the authority fixture (as copied into the output);
- the derived expected outcomes file;
- the transcript;
- per-event protected action requests;
- per-event authority decision reports;
- the harness run report.

The manifest is **not**:

- a Silver Signed Bundle Assertion;
- a Silver Verifier Output Attestation;
- a signed certification artifact;
- production-grade evidence packaging.

It is local hash-based integrity evidence only. Signing or packaging may be considered in a later release.

---

## 2. Relationship to v0.2.3 Decision Reports

The manifest hashes every Silver Protected Action Decision Report v0.1.0 file emitted by the harness. The decision reports themselves are produced by the unchanged v0.2.3 authority evaluator.

The manifest also hashes the input authority fixture as it was copied into the output directory. This binds the run to the exact authority truth that produced the decisions.

---

## 3. Format

JSON. UTF-8 encoded. Serialized with `json.dumps(obj, indent=2, sort_keys=True)` followed by a trailing newline for deterministic output.

---

## 4. Top-Level Structure

```json
{
  "manifest_type": "proofrail.silver.multi_agent_harness_evidence_manifest",
  "manifest_version": "v0.1.0",
  "script_id": "<string>",
  "generated_by": "tools/silver/run_multi_agent_attack_harness_v0_1_0.py",
  "generated_at": "<ISO-8601>",
  "hash_algorithm": "sha256",
  "subjects": [ ... ],
  "limitations": [ ... ]
}
```

All top-level fields are required.

| Field | Notes |
|---|---|
| `manifest_type` | Must equal `proofrail.silver.multi_agent_harness_evidence_manifest`. |
| `manifest_version` | Must equal `v0.1.0`. |
| `script_id` | Copied from the harness script. |
| `generated_by` | Path to the runner tool that emitted the manifest. |
| `generated_at` | Wall-clock ISO-8601 UTC manifest creation time. Documentation only. |
| `hash_algorithm` | Must equal `sha256`. |
| `subjects` | Non-empty list of subject entries. |
| `limitations` | Non-empty list of non-claim strings. |

---

## 5. Subject Entries

Each subject:

```json
{
  "subject_type": "<enum>",
  "path": "<relative-path>",
  "sha256": "sha256:<64-hex>",
  "size_bytes": <int>
}
```

| `subject_type` | Semantics |
|---|---|
| `harness_script` | Copy of the harness script YAML. |
| `authority_fixture` | Copy of the v0.2.3 authority fixture YAML. |
| `expected_outcomes` | Runner-derived per-event expected outcomes projection. |
| `transcript` | Harness transcript JSONL. |
| `protected_action_request` | Per-event request JSON. |
| `authority_decision_report` | Per-event decision report JSON. |
| `harness_run_report` | Harness run report JSON. |

Paths are relative to the manifest file location (the harness output directory). Paths **must not** contain `..` components. The verifier rejects any subject path containing `..` with `subject_path_traversal`.

`sha256` is the literal lowercase hex digest of the raw file bytes, prefixed with `sha256:`.

`size_bytes` is the file size at manifest generation. The verifier recomputes hashes; the size field is metadata only.

---

## 6. Subject Ordering

Subjects are emitted in a deterministic order:

1. `harness_script`
2. `authority_fixture`
3. `expected_outcomes`
4. `transcript`
5. all `protected_action_request` entries sorted lexicographically by path
6. all `authority_decision_report` entries sorted lexicographically by path
7. `harness_run_report`

This ordering makes the manifest reproducible across runs that have identical inputs.

---

## 7. Limitations

The `limitations` list must be non-empty. Recommended entries:

```
Local hash-based integrity evidence only.
Not a signed certification artifact.
Not production-grade evidence packaging.
Not Gold certification.
```

---

## 8. Example

```json
{
  "generated_at": "2026-06-21T12:10:01Z",
  "generated_by": "tools/silver/run_multi_agent_attack_harness_v0_1_0.py",
  "hash_algorithm": "sha256",
  "limitations": [
    "Local hash-based integrity evidence only."
  ],
  "manifest_type": "proofrail.silver.multi_agent_harness_evidence_manifest",
  "manifest_version": "v0.1.0",
  "script_id": "proofrail-silver-multi-agent-attack-harness-v0.2.4",
  "subjects": [
    {
      "path": "harness-script.yaml",
      "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 0,
      "subject_type": "harness_script"
    }
  ]
}
```

---

## 9. Verification Rules

The accompanying verifier `tools/silver/verify_multi_agent_harness_evidence_v0_1_0.py` performs:

1. Manifest structural validation (type, version, hash algorithm, non-empty subjects).
2. Reject `..` in any subject path (`subject_path_traversal`).
3. Confirm every subject file exists (`subject_file_missing`).
4. Recompute SHA-256 and compare to manifest (`subject_hash_mismatch`).
5. Parse the harness run report subject and confirm:
   - `report_type == "proofrail.silver.multi_agent_harness_run_report"`
   - `report_version == "v0.1.0"`
   - `summary.status == "pass"` (`harness_run_failed`)
   - `execution.protected_actions_performed == false` (`execution_violation`)
6. Parse every `authority_decision_report` subject and confirm:
   - `report_type == "proofrail.silver.protected_action_decision_report"` (`decision_report_invalid`)
   - `execution.performed == false` (`execution_violation`)

Verifier exit codes: `0` (valid), `1` (invalid), `2` (usage/input error).

---

## 10. Changelog

- **v0.1.0 (2026-06-21):** Initial schema.
