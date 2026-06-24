# Silver Relying-Party Policy Pack v0.3.5 — Fixtures

Four hand-authored passing policy packs covering the v0.3.5 structural
shape and configuration variants.

| File | Variant |
|---|---|
| `policy-pack.json` | Canonical pack; all sections populated with representative values |
| `policy-pack-with-exception.json` | Multi-exception block; `record_and_pause_reuse` postures; tighter rejection set |
| `policy-pack-with-warning-policy.json` | Two attestors, two issuers, rich `warning_treatment.warnings`, three hard stops; `record_and_block_reuse` / `record_and_block_until_superseded` postures |
| `policy-pack-with-freshness-windows.json` | Tight freshness windows (2 h); no attestation required; `record_only` supersession |

Every fixture is a passing policy pack: it parses to a top-level JSON
object, satisfies the 24 ordered structural checks, contains non-empty
`scope_limitations` and `non_claims`, and contains no prohibited claim
tokens outside those two blocks.

The fixtures are inputs only. The runner emits the manifest, the
re-derived conformance report, and the packaged copy of the pack under
`/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/`. The
fixtures directory itself contains no manifests or reports.

## Non-claims

These fixtures are demonstration inputs. They do not certify any
relying party, do not constitute regulator or auditor approval, and
are not Gold governed reliance instruments.
