# Silver Relying-Party Policy Pack Manifest v0.1.0

**Document type:** `proofrail.silver.relying_party_policy_pack_manifest`

The manifest is a small JSON document that binds the policy pack and
its independently re-derived conformance report under
content-addressed hashes.

## Top-level shape

```jsonc
{
  "document_type": "proofrail.silver.relying_party_policy_pack_manifest",
  "schema_version": "0.1.0",
  "proofrail_release": "v0.3.5",
  "manifest_id": "<stable-id-string>",
  "policy_pack_id": "<stable-id-string>",
  "generated_at": "<ISO-8601 UTC Z>",
  "hash_algorithm": "sha256",
  "subjects": [
    {
      "role": "policy_pack",
      "path": "silver-relying-party-policy-pack.json",
      "sha256": "sha256:<64-hex>",
      "size_bytes": <int>
    },
    {
      "role": "policy_pack_conformance_report",
      "path": "silver-relying-party-policy-pack-conformance-report.json",
      "sha256": "sha256:<64-hex>",
      "size_bytes": <int>
    }
  ]
}
```

## Fixed subject order

The `subjects` array must contain exactly two entries in the fixed
order:

1. `policy_pack` at `silver-relying-party-policy-pack.json`
2. `policy_pack_conformance_report` at
   `silver-relying-party-policy-pack-conformance-report.json`

All subject paths must be relative and must not contain `..` or be
absolute.

## Integrity contract

The verifier:

- Validates manifest top-level shape, `document_type`,
  `schema_version`, `proofrail_release`, `hash_algorithm`, and
  `subjects` array.
- Validates subject count = 2 and fixed role / path order.
- Recomputes SHA-256 and `size_bytes` for every subject from disk.
- Fails with `policy_pack_manifest_invalid` on any disagreement.

The bundled conformance report is **independently re-derived** by the
verifier from the bound policy pack only after all 24 policy-pack
structural checks pass; a re-derived report that disagrees with the
bundled subject [1] bytes also fails as `policy_pack_manifest_invalid`.
