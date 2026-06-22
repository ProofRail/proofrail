# ProofRail Silver Multi-Agent Demo Summary Schema v0.1.0

**Version:** v0.1.0
**Date:** 2026-06-21
**Status:** Draft / Demo-informed schema
**Claim family:** ProofRail Silver multi-agent trust-boundary demo summaries

---

## 1. Purpose

The Silver Multi-Agent Demo Summary is a deterministic mapping from the eight claims of the multi-agent trust-boundary demo (v0.2.5) to concrete v0.2.4 harness evidence references.

Every claim is derived from the v0.2.4 harness run report, transcript, and decision reports. The packager **must not** maintain a parallel hand-written expected-results source.

The demo summary is not a Bronze claim, not a Silver Signed Bundle Assertion, and not a Verifier Output Attestation. It is a local mapping document, hashed by the demo package manifest.

---

## 2. Format

JSON. UTF-8 encoded. Serialized with `json.dumps(obj, indent=2, sort_keys=True)` followed by a trailing newline for deterministic output.

---

## 3. Top-Level Structure

```json
{
  "document_type": "proofrail.silver.multi_agent_demo_summary",
  "schema_version": "v0.1.0",
  "demo_id": "<string>",
  "proofrail_release": "v0.2.5",
  "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
  "generated_at": "<ISO-8601>",
  "source_harness": {
    "harness_release": "v0.2.4",
    "harness_script_id": "<string>",
    "harness_manifest_path": "harness-evidence/harness-evidence-manifest.json",
    "harness_run_report_path": "harness-evidence/harness-run-report.json"
  },
  "claims": [ ... ],
  "execution": {
    "protected_actions_performed": false,
    "reason": "demo_evidence_only"
  },
  "limitations": [ ... ]
}
```

All top-level fields are required.

| Field | Notes |
|---|---|
| `document_type` | Must equal `proofrail.silver.multi_agent_demo_summary`. |
| `schema_version` | Must equal `v0.1.0`. |
| `demo_id` | Stable demo identifier, e.g. `proofrail-silver-demo-003-multi-agent-trust-boundary`. |
| `proofrail_release` | Must equal `v0.2.5`. |
| `generated_by` | Path to the packager tool. |
| `generated_at` | Wall-clock ISO-8601 UTC creation time. Documentation only. |
| `source_harness` | Mapping describing the v0.2.4 harness inputs used to derive the summary. |
| `claims` | Non-empty list of claim entries (see §4). Every required claim ID must be present. |
| `execution` | Must declare `protected_actions_performed: false` and a non-empty `reason` string. |
| `limitations` | Non-empty list of non-claim strings. |

---

## 4. Claim Entries

Each claim entry:

```json
{
  "claim_id": "<enum>",
  "description": "<string>",
  "status": "pass",
  "evidence_refs": [
    {
      "artifact": "harness-evidence/transcript.jsonl",
      "event_id": "EVT-001-harmless-message"
    },
    {
      "artifact": "harness-evidence/authority-decision-reports/EVT-002-allowed-payment-release.json"
    }
  ]
}
```

| Field | Notes |
|---|---|
| `claim_id` | One of the eight required IDs (see §5). |
| `description` | Short prose statement of the claim. Documentation only. |
| `status` | Must equal `pass` for every required claim. |
| `evidence_refs` | Non-empty list. Each entry must include `artifact` (relative path). May include `event_id` for transcript or decision-report references. |

Evidence reference rules:

- `artifact` is relative to the package root. It must not contain `..` and must not be absolute. Violations are reported as `demo_evidence_ref_invalid`.
- `artifact` must resolve to a file covered by the nested v0.2.4 harness evidence manifest (after the nested manifest is itself referenced from the package).
- For transcript references, `event_id` (when present) must match a `transcript.jsonl` record's `event_id`.
- For decision-report references, the referenced file path's basename without `.json` must equal the corresponding `event_id`.

---

## 5. Required Claim IDs and Evidence Derivation

The packager derives each required claim from the v0.2.4 harness run report and transcript using the rules below. The verifier cross-checks each claim against the nested data (not just structural presence).

| `claim_id` | Source-of-truth in nested harness evidence | Pass condition |
|---|---|---|
| `harmless_messages_proceed` | Transcript event with `event_type == "agent_message"` and `actual.harness_outcome == "message_delivered"`. | At least one matching event (e.g., `EVT-001-harmless-message`). |
| `protected_actions_require_scoped_authority` | Decision reports where `decision.status == "allow"` AND `execution.performed == false`. | At least one matching decision report (e.g., `EVT-002`, `EVT-003`). |
| `unauthorized_delegation_fails` | Decision report with `decision.status == "deny"` and `decision.reason == "authority_subject_mismatch"`. | At least one matching decision report (e.g., `EVT-004`). |
| `bypass_attempts_blocked` | Transcript event with `event_type == "bypass_attempt"`, `actual.harness_outcome == "bypass_blocked"`, `actual.harness_reason == "bypass_attempt_detected"`. | At least one matching event (e.g., `EVT-005`). |
| `revoked_authority_fails` | A transcript `revocation_marker` event AND a later decision report with `decision.reason == "authority_revoked"`. | Both must be present (e.g., `EVT-008` marker + `EVT-009` denial). |
| `out_of_scope_actions_fail` | Decision report with `decision.status == "deny"` and `decision.reason == "constraint_not_satisfied"`. | At least one matching decision report (e.g., `EVT-006`, `EVT-007`). |
| `evidence_is_hash_verifiable` | The nested `harness-evidence-manifest.json` exists and the nested v0.2.4 verifier returns exit 0 against it. | Recorded in package manifest `nested_verification.harness_evidence_verified == true`. The package verifier still re-invokes the v0.2.4 verifier. |
| `no_protected_actions_executed` | The nested run report `execution.protected_actions_performed == false` AND every decision report `execution.performed == false`. | All checks must pass. |

The packager **must** derive these claim outcomes from the nested run report and transcript. It must not maintain a duplicated expected-results table.

---

## 6. Execution Invariant

`execution.protected_actions_performed` **must** be `false`. The accompanying `reason` should describe the demo's nature, for example `"demo_evidence_only"`.

This invariant mirrors the v0.2.3 decision report and v0.2.4 run report invariant: no real protected action is ever executed by the demo.

A package whose summary states `protected_actions_performed: true` is rejected with `demo_execution_violation`.

---

## 7. Limitations

The `limitations` list must be non-empty. Recommended entries:

```
Local deterministic demo summary only.
Derived from v0.2.4 multi-agent harness evidence.
No live agents executed.
No live actuators invoked.
Not natural-language prompt parsing.
Not prompt-injection detection.
Not Gold certification.
```

---

## 8. Example (abbreviated)

```json
{
  "claims": [
    {
      "claim_id": "harmless_messages_proceed",
      "description": "Harmless agent-to-agent messages do not invoke protected actions.",
      "evidence_refs": [
        { "artifact": "harness-evidence/transcript.jsonl", "event_id": "EVT-001-harmless-message" }
      ],
      "status": "pass"
    }
  ],
  "demo_id": "proofrail-silver-demo-003-multi-agent-trust-boundary",
  "document_type": "proofrail.silver.multi_agent_demo_summary",
  "execution": {
    "protected_actions_performed": false,
    "reason": "demo_evidence_only"
  },
  "generated_at": "2026-06-21T12:30:01Z",
  "generated_by": "tools/silver/package_multi_agent_trust_boundary_demo_v0_1_0.py",
  "limitations": [
    "Local deterministic demo summary only."
  ],
  "proofrail_release": "v0.2.5",
  "schema_version": "v0.1.0",
  "source_harness": {
    "harness_manifest_path": "harness-evidence/harness-evidence-manifest.json",
    "harness_release": "v0.2.4",
    "harness_run_report_path": "harness-evidence/harness-run-report.json",
    "harness_script_id": "proofrail-silver-multi-agent-attack-harness-v0.2.4"
  }
}
```

---

## 9. Verification Rules

The package verifier `tools/silver/verify_multi_agent_trust_boundary_demo_v0_1_0.py`:

1. Parses `demo-summary.json` after the package subject hash check. JSON parse errors are caught and surfaced as `invalid_demo_summary` (no Python traceback leakage).
2. Validates `document_type`, `schema_version`, `proofrail_release`, `source_harness`, `execution`, and non-empty `limitations`. → `invalid_demo_summary`.
3. Confirms every required claim ID in §5 is present and `status == "pass"`. → `demo_claim_missing` if any required claim is absent; `demo_claim_failed` if `status` is not `"pass"`.
4. Confirms each claim's `evidence_refs` is non-empty, paths are package-local, and the claim derivation rule from §5 is satisfied against the nested run report and decision reports. → `demo_claim_failed` if the derivation rule fails; `demo_evidence_ref_invalid` for malformed references or wrong event/file pointers.
5. Confirms `execution.protected_actions_performed == false`. → `demo_execution_violation`.

---

## 10. Changelog

- **v0.1.0 (2026-06-21):** Initial schema.
