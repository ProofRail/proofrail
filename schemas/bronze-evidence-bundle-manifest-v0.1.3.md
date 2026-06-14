# ProofRail Bronze Evidence Bundle Manifest Schema v0.1.3

**Version:** v0.1.3
**Date:** 2026-06-14
**Status:** Draft / Demo-informed schema
**Derived from:** v0.1.2 evidence checksum extension
**Manifest family:** ProofRail Bronze evidence bundle manifests

---

## 1. Purpose

The ProofRail Bronze Evidence Bundle Manifest is a self-describing, portable manifest that checksums the **entire evidence package** — claim file, evidence files, schema documents, tooling scripts, and documentation.

The bundle manifest enables integrity verification of a complete ProofRail evidence package as a single unit, complementing the per-evidence-file checksums introduced in Bronze Claim Schema v0.1.2.

This manifest is local and unsigned. It is not a Silver assertion, not a certification, and not a trust assertion. It lays the foundation for future signed bundle verification.

---

## 2. Relationship to v0.1.2

Bronze Claim Schema v0.1.2 introduced `evidence_checksums` — a mapping inside the claim YAML that records SHA-256 digests of evidence files referenced by the claim.

The v0.1.2 approach has a structural limitation: the claim file cannot contain its own checksum. The checksum of the claim would change each time the claim is regenerated, creating a circular dependency.

The v0.1.3 bundle manifest solves this by placing the claim's checksum in an **external** manifest file. The bundle manifest checksums the claim file alongside all other package files, providing complete package integrity verification without self-reference.

### 2.1 Scope comparison

| Artifact | v0.1.2 `evidence_checksums` | v0.1.3 bundle manifest |
|----------|----------------------------|------------------------|
| Evidence files | Yes | Yes |
| Claim file | No (self-reference) | Yes |
| Schema documents | No | Yes |
| Tooling scripts | No | Yes |
| Documentation | No | Yes |

---

## 3. Self-Reference

The bundle manifest itself is **NOT** included in its own file list. This avoids the same self-reference problem that v0.1.2 has with the claim file.

The bundle manifest is the outermost integrity wrapper. Its own integrity, if needed, would be established by a future signed assertion (Silver profile) or an external notarization mechanism.

---

## 4. Required Top-Level Fields

A v0.1.3 bundle manifest must include:

```yaml
manifest_version: "v0.1.3"
manifest_type: "proofrail.bronze.evidence_bundle"
bundle_id: string
bundle_label: string
profile: "bronze"
environment: "dev" | "test" | "staging" | "prod"
subject_claim: string
generated_at: ISO-8601 timestamp
generated_by: string
files: list
validation: mapping
```

### 4.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `manifest_version` | Yes | Schema version. Must be `v0.1.3`. |
| `manifest_type` | Yes | Must be `proofrail.bronze.evidence_bundle`. |
| `bundle_id` | Yes | Unique identifier for this bundle instance. |
| `bundle_label` | Yes | Human-readable bundle label. |
| `profile` | Yes | Must be `bronze`. |
| `environment` | Yes | Deployment environment: `dev`, `test`, `staging`, or `prod`. |
| `subject_claim` | Yes | Relative path to the claim file this bundle covers. |
| `generated_at` | Yes | Bundle generation timestamp in ISO-8601 UTC format. |
| `generated_by` | Yes | Tool or process that generated this manifest. |
| `files` | Yes | List of file entries (see Section 5). |
| `validation` | Yes | Validation metadata (see Section 8). |

---

## 5. File Entry Structure

Each entry in the `files` list describes one file in the bundle:

```yaml
- path: string
  role: string
  required: true | false
  sha256: "sha256:<64 hex chars>"
  size_bytes: integer
```

### 5.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `path` | Yes | File path relative to the package root. May use `../../` to reference files outside the package directory. |
| `role` | Yes | Semantic role of the file in the bundle (see Section 6). |
| `required` | Yes | Whether the file is required for a complete bundle. |
| `sha256` | Yes | SHA-256 digest in `sha256:<64 hex chars>` format, or `null` if file is missing. |
| `size_bytes` | Yes | File size in bytes, or `null` if file is missing. |

### 5.2 Path semantics

Paths in the manifest preserve the original relative path strings from the bundle input. This keeps the manifest portable across environments. Paths are resolved relative to the package root at verification time.

---

## 6. Roles

Each file in the bundle is assigned a semantic role. The following roles are defined for v0.1.3:

### 6.1 Claim and evidence roles

| Role | Description |
|------|-------------|
| `claim` | The Bronze claim YAML file. |
| `protected_actuator_set_manifest` | Canonical protected actuator set manifest (JSON). |
| `bypass_evidence` | Bypass prevention test results. |
| `stop_control_evidence` | Stop-control or emergency-stop test evidence. |
| `rate_limit_evidence` | Rate-limit, throttling, or circuit-breaker evidence. |
| `audit_sample` | Structured or normalized audit event sample. |
| `performance_evidence` | Latency or performance measurement evidence. |
| `substrate_log_sample` | Raw log sample from the mediation substrate. |

### 6.2 Documentation roles

| Role | Description |
|------|-------------|
| `architecture_notes` | Architecture description for the deployment. |
| `runbook` | Operational runbook. |
| `demo_summary` | Demo results summary. |

### 6.3 Schema and tooling roles

| Role | Description |
|------|-------------|
| `claim_schema` | The claim schema document used by this bundle. |
| `bundle_manifest_schema` | This bundle manifest schema document. |
| `claim_generator` | The claim generator tool. |
| `claim_validator` | The claim structural validator tool. |
| `claim_evidence_verifier` | The claim evidence checksum verifier tool. |

### 6.4 Extensibility

Additional roles may be defined in future versions. Validators should accept unknown roles without error to support forward compatibility.

---

## 7. Checksum Semantics

### 7.1 Computation rule

Checksums are computed over raw file bytes (not decoded text). The digest is lowercase hexadecimal, prefixed with `sha256:`.

```python
import hashlib
digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
```

### 7.2 Format

All checksum values must match:

```
sha256:[0-9a-f]{64}
```

### 7.3 Missing files

If a file listed in the bundle input does not exist at generation time:
- `sha256` is set to `null`.
- `size_bytes` is set to `null`.
- If `required: true`, the file path is added to `validation.missing_files`.

---

## 8. Validation Section

The manifest includes a `validation` section:

```yaml
validation:
  missing_files:
    - string
  file_count: integer
```

### 8.1 Field meanings

| Field | Required | Meaning |
|-------|----------|---------|
| `missing_files` | Yes | List of required file paths that were missing at generation time. Empty list for a complete bundle. |
| `file_count` | Yes | Total number of file entries in the `files` list. |

---

## 9. Verification Semantics

A bundle verifier should:

1. Load the manifest YAML.
2. For each file entry in `files`:
   - Resolve `path` relative to the package root.
   - If missing and `required: true`: record failure.
   - If exists: compute SHA-256 over raw bytes and compare to `sha256`.
   - If exists: compare `size_bytes` to actual file size.
   - If any mismatch: record failure.
3. If any failures: report `FAIL` with details, exit 1.
4. If all files verified: report `PASS`, exit 0.

### 9.1 Exit codes

| Code | Meaning |
|------|---------|
| 0 | All bundle files verified. |
| 1 | Verification failed (missing files, checksum mismatch, or size mismatch). |
| 2 | Usage error (bad arguments, missing manifest). |

---

## 10. Limitations

- The bundle manifest is **local only**. It does not imply federation, cross-organization trust, or external certification.
- The bundle manifest is **unsigned**. It does not provide cryptographic non-repudiation.
- The bundle manifest is **not a Silver assertion**. Silver-profile features (signatures, revocation, federation) are out of scope for v0.1.3.
- The bundle manifest is **not a certification**. It records checksums for integrity verification, not conformance certification.
- The bundle manifest does **not include itself** in the file list. Its own integrity must be established by external means if required.

---

## 11. Example

Minimal valid v0.1.3 bundle manifest:

```yaml
manifest_version: "v0.1.3"
manifest_type: "proofrail.bronze.evidence_bundle"
bundle_id: "example-bundle"
bundle_label: "Example Evidence Bundle"
profile: "bronze"
environment: "test"
subject_claim: "claims/example-claim.yaml"
generated_at: "2026-06-14T00:00:00Z"
generated_by: "tools/claims/generate_evidence_bundle_manifest_v0_1_3.py"
files:
  - path: "claims/example-claim.yaml"
    role: "claim"
    required: true
    sha256: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    size_bytes: 2048
  - path: "evidence/audit-sample.jsonl"
    role: "audit_sample"
    required: true
    sha256: "sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    size_bytes: 1024
validation:
  missing_files: []
  file_count: 2
```

---

## 12. Change Log

### v0.1.3

- Initial release of the Bronze Evidence Bundle Manifest schema.
- Checksums the entire portable package: claim file, evidence files, schema documents, tooling scripts, and documentation.
- Solves the v0.1.2 self-reference limitation by placing the claim's checksum in an external manifest.
- Local and unsigned — not a Silver assertion.

---

## 13. Recommended File Name

```text
schemas/bronze-evidence-bundle-manifest-v0.1.3.md
```
