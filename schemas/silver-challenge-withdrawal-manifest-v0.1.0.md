# Silver Challenge/Withdrawal Manifest Schema v0.1.0 (ProofRail v0.3.4)

The v0.3.4 manifest is the deterministic hash anchor for the local
challenge/withdrawal primitives package.

## Document type

```text
proofrail.silver.challenge_withdrawal_manifest
```

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `document_type` | string | Must equal `proofrail.silver.challenge_withdrawal_manifest` |
| `schema_version` | string | Must equal `v0.1.0` |
| `proofrail_release` | string | Must equal `v0.3.4` |
| `manifest_id` | string | Non-empty |
| `generated_at` | string | ISO-8601 UTC, `Z`-suffixed |
| `hash_algorithm` | string | Must equal `sha256` |
| `subjects` | array of objects | Exactly four subjects in fixed order |
| `scope_limitations` | array of strings | Non-empty; no blank entries |
| `non_claims` | array of strings | Non-empty; no blank entries |

## Subject layout (exactly four, fixed order)

| Index | Path | Role |
|---|---|---|
| 0 | `target-handoff/silver-acceptance-handoff-manifest.json` | `target_handoff_manifest` |
| 1 | `records/challenge-record.json` | `challenge_record` |
| 2 | `records/withdrawal-record.json` | `withdrawal_record` |
| 3 | `silver-challenge-withdrawal-summary.json` | `challenge_withdrawal_summary` |

Each subject object carries:

```text
path        -- exact relative path as listed above
role        -- exact role string as listed above
sha256      -- "sha256:<64 hex>" of the file on disk
size_bytes  -- non-negative integer
```

The verifier rejects any subject path that is absolute or contains
`..` BEFORE comparing it to the fixed table. Path-traversal mutations
therefore always fire `challenge_withdrawal_subject_path_traversal`,
never the generic `invalid_challenge_withdrawal_manifest` reason.

## Scope and non-claims

The manifest binds:

- the copied target handoff manifest (subject [0]) — the full nested
  v0.3.0 acceptance handoff package is bound transitively by that
  manifest, not directly by the v0.3.4 manifest;
- the challenge record (subject [1]);
- the withdrawal record (subject [2]);
- the derived summary (subject [3]).

The manifest is an integrity anchor only. It is not a certificate, not
a regulator approval, not a legal revocation, not an adjudication, and
not Gold acceptance.
