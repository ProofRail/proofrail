# Silver Evidence Source Adapter Profile — v0.2.6

**Status:** Draft / Profile-informed descriptor release
**Date:** 2026-06-21
**Schema:** `schemas/silver-evidence-source-adapter-v0.1.0.md`

---

## What v0.2.6 Adds

Silver v0.2.6 introduces the **Evidence Source Adapter** profile: a structured way for an evidence source (gateway, observability trace system, SIEM, policy engine, GRC platform, or native ProofRail tooling) to declare how its records map into ProofRail-relevant evidence fields.

A descriptor is a static JSON document. It is **not** a runtime integration, **not** evidence by itself, **not** a trust decision, and **not** a certification.

Core sentence:

> v0.2.6 defines how evidence sources describe their outputs. It does not make those sources trustworthy.

---

## Position in the Stack

| Layer | Role |
|---|---|
| Bronze | Claim about a deployment and its evidence files. |
| Silver | Cross-cutting controls — signing, revocation, conformance, attestation, fixtures, adapters. |
| Gold | Out of scope for v0.2.6. |

The adapter profile is a Silver-layer declaration. It sits **next to** Bronze evidence, not above or below it. A descriptor lets a relying party inspect the shape of source evidence before that evidence is folded into a Bronze claim or a Silver bundle.

ProofRail is not the gateway, not the SIEM, not the policy engine, and not the GRC platform. ProofRail records what evidence those sources contribute, and what each adapter does **not** assert.

---

## Closed Source Type Set

v0.2.6 supports exactly six source types:

| `source_type` | Typical role |
|---|---|
| `native_proofrail` | First-party ProofRail demo / Iron-plus / Bronze evidence emitter |
| `gateway` | MCP / API / actuator gateway (e.g., agentgateway) |
| `observability_trace` | Distributed trace collector |
| `siem_log` | Security log / correlator |
| `policy_engine` | Policy decision point |
| `grc_platform` | Governance / risk / compliance workflow source |

Any other `source_type` is rejected with `invalid_source_type`. The set is intentionally narrow for v0.2.6 and may expand in later releases.

---

## Required Evidence Capabilities

Every descriptor must declare all six capabilities. Each capability has a `status` of `provided`, `not_provided`, or `not_applicable`:

| Capability | Meaning |
|---|---|
| `decision_event` | Source records a decision (allow/deny/equivalent) for a protected action |
| `bypass_evidence` | Source can observe attempts to bypass the controlled path |
| `revocation_status` | Source records authority/policy revocation linkage |
| `subject_hashes` | Source emits content hashes of decision subjects |
| `source_identity` | Source identifies itself in its records |
| `timestamp_integrity` | Source records timestamps for events |

Conformance requirements:

- `decision_event` **must** be `provided`. Its full mapping fields (`event_type`, `timestamp_field`, `decision_field`, `reason_field`, `source_record_id_field`) must be present.
- Any capability whose status is **not** `provided` must include a non-empty `limitation` string explaining what the source cannot do.
- A `provided` capability must include a non-empty `description` string.

Whitespace-only strings are rejected for all required string fields.

---

## Trust Boundary

Every descriptor must declare `trust_boundary.source_is_trust_authority == false`. The descriptor is an evidence-source declaration, not a trust assertion.

`trust_boundary.proofrail_role` must equal `evidence_source`.

This is the same boundary the Iron-plus and Silver profiles already enforce: ProofRail relies on a Bronze claim, a signed Silver assertion, and a trust policy — not on a vendor's marketing self-claim.

---

## Canonical Examples

Six canonical descriptors live in `examples/silver-evidence-source-adapters/`:

| File | source_type | Capability shape |
|---|---|---|
| `native-proofrail-v0.2.6.json` | `native_proofrail` | All six capabilities `provided` |
| `gateway-mcp-simulated-v0.2.6.json` | `gateway` | All six capabilities `provided` |
| `observability-trace-simulated-v0.2.6.json` | `observability_trace` | decision/source/timestamp `provided`; bypass/revocation `not_provided`; subject_hashes `not_applicable` |
| `siem-log-simulated-v0.2.6.json` | `siem_log` | decision/bypass/source/timestamp `provided`; revocation/subject_hashes `not_provided` |
| `policy-engine-simulated-v0.2.6.json` | `policy_engine` | decision/revocation/subject/source/timestamp `provided`; bypass `not_applicable` |
| `grc-platform-simulated-v0.2.6.json` | `grc_platform` | decision (workflow approval) / source `provided`; revocation as approval withdrawal `provided`; bypass / subject_hashes / timestamp_integrity `not_provided` |

The GRC platform example is explicitly framed as **workflow / risk / approval decision evidence** only. Its `adapter_limitations` state that workflow approval is **not technical enforcement** and that workflow approval alone is **not sufficient** for protected-action reliance — technical decision evidence from a gateway, policy engine, or native ProofRail run is required.

All examples are static and simulated. None integrate with any real product.

---

## Validator

`tools/silver/validate_evidence_source_adapter_v0_1_0.py` is a pure-stdlib structural validator.

- **Inputs:** `--adapter <file.json>` or `--examples-dir <dir>`.
- **Output:** `PASS: evidence source adapter valid (<adapter_id>)` per descriptor; a final `=== N/N adapter descriptors valid ===` line for directory mode.
- **Failures:** stable reason codes printed on stderr; nonzero exit.
- **Side effects:** none. The validator reads its input file and writes only to stdout/stderr.

Stable failure reasons:

| Reason | When |
|---|---|
| `invalid_adapter_descriptor` | Top-level shape errors, missing required fields, bad `adapter_id`, malformed JSON, etc. |
| `invalid_source_type` | `source.source_type` not in the closed set |
| `source_marked_as_trust_authority` | `trust_boundary.source_is_trust_authority` is anything other than `false` |
| `control_surface_missing` | `control_surface` block missing or has missing/empty/wrong-typed fields |
| `protected_action_mapping_missing` | `protected_action_mapping` block missing or has empty / malformed protected action IDs |
| `evidence_capability_missing` | One of the six required capabilities is missing, has an unknown status, or lacks the required `description` / `limitation` string |
| `decision_event_mapping_missing` | `decision_event` is not `provided`, or its required mapping fields are absent / empty |
| `normalization_notes_missing` | `normalization` block missing, or `normalization_notes` empty / has empty entries |
| `adapter_limitations_missing` | `adapter_limitations` empty or has empty / whitespace-only entries |
| `adapter_non_claims_missing` | `non_claims` empty or has empty / whitespace-only entries |
| `evidence_artifact_path_traversal` | `sample_artifact_refs[i].path` is absolute or contains `..` |
| `duplicate_adapter_id` | Two descriptors in the same directory share an `adapter_id` |

Empty or whitespace-only strings are rejected wherever a non-empty string is required (`adapter_limitations`, `non_claims`, `normalization_notes`, capability `description` / `limitation`, mapping fields, reliance statement, control-surface strings).

---

## Validator Boundaries (Non-Claims)

The validator does **not**:

- read external logs, fetch URLs, or call vendor APIs;
- assert that the declared source actually behaves as described;
- prove that any declared product or component is conformant;
- decide whether the declared evidence is sufficient for any particular relying-party purpose;
- replace Bronze claim validation, Silver signed bundle verification, conformance validation, attestation verification, multi-principal authority evaluation, or the multi-agent harness verifier.

A passing descriptor only states: this JSON document is a structurally well-formed evidence source adapter declaration that fits the v0.2.6 closed schema.

---

## Regression Test

`tests/test_silver_evidence_source_adapter_v0_2_6.sh` runs 20 cases:

1. Validate each of the six canonical descriptors individually.
2. Validate the examples directory in one command.
3. Inline check: every canonical descriptor has `trust_boundary.source_is_trust_authority == false`.
4. Inline check: every canonical descriptor has non-empty `adapter_limitations` and `non_claims`.
5. Inline check: every canonical descriptor declares all six required evidence capabilities.
6. Malformed JSON → `invalid_adapter_descriptor` with no Python traceback.
7. Unsupported `source_type` → `invalid_source_type`.
8. `source_is_trust_authority = true` → `source_marked_as_trust_authority`.
9. Missing `control_surface` field → `control_surface_missing`.
10. Empty `protected_action_ids` → `protected_action_mapping_missing`.
11. Missing capability key → `evidence_capability_missing`.
12. `decision_event` not `provided` → `decision_event_mapping_missing`.
13. Empty `normalization_notes` → `normalization_notes_missing`.
14. Whitespace-only `adapter_limitations` entry → `adapter_limitations_missing`.
15. Empty `non_claims` → `adapter_non_claims_missing`.
16. `sample_artifact_refs` path traversal (`..`) → `evidence_artifact_path_traversal`.
17. Duplicate `adapter_id` across directory → `duplicate_adapter_id`.
18. `sample_artifact_refs` absolute path → `evidence_artifact_path_traversal`.
19. Non-provided capability with blank (whitespace-only) `limitation` → `evidence_capability_missing`.
20. Scoped mutation check: the schema, validator, and committed canonical examples are unchanged by the test runtime.

The test prints `=== ProofRail Silver v0.2.6 evidence source adapter: 20/20 PASS ===` on success.

---

## Make Targets

- `make validate-silver-evidence-source-adapters-v0-2-6` — run the validator against `examples/silver-evidence-source-adapters/` in directory mode.
- `make verify-silver-evidence-source-adapter-v0-2-6` — run the 18-step regression test.

Both targets are appended to `verify-silver-all`.

---

## What v0.2.6 Does Not Do

- Does not certify any real gateway, observability stack, SIEM, policy engine, or GRC platform.
- Does not assert that a descriptor matches what its source actually emits.
- Does not change Bronze, Silver signed-bundle, revocation, verification-report, conformance, attestation, multi-principal-authority, or multi-agent-harness semantics.
- Does not impose runtime integration. Descriptors are static documents.
- Does not establish a new trust authority. Sources remain evidence sources.

The v0.2.6 release is a profile and descriptor release, intentionally narrow in scope and conservative in claim.
