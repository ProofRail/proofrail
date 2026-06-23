# Silver Challenge/Withdrawal Primitives Fixtures (v0.3.4)

This directory contains two deterministic input fixtures used by the
v0.3.4 runner:

- `challenge-record.json` — a Silver challenge record that targets a
  Silver acceptance handoff for stated post-acceptance review;
- `withdrawal-record.json` — a Silver withdrawal record that pauses
  local reuse pending review and cites the challenge record by id.

Both records carry the literal placeholder

```text
"target_manifest_sha256": "sha256:TO_BE_BOUND_BY_RUNNER"
```

before binding. The v0.3.4 runner rewrites this placeholder to the
actual SHA-256 of the copied target handoff manifest before publishing
the package; the verifier rejects any packaged record that still
contains the placeholder.

The fixture timestamps satisfy:

```text
target.generated_at (v0.3.0 handoff)  <= challenge.filed_at
challenge.filed_at                    <= withdrawal.recorded_at
withdrawal.recorded_at                <= withdrawal.effective_at
```

with the canonical demo timestamps:

```text
target.generated_at      = 2026-06-28T00:00:00Z   (from v0.3.0 demo)
challenge.filed_at       = 2026-06-29T00:10:00Z
withdrawal.recorded_at   = 2026-06-29T00:20:00Z
withdrawal.effective_at  = 2026-06-29T00:20:00Z
summary.generated_at     = 2026-06-29T00:30:00Z
```

## Non-claims

These fixtures are **not**:

- a challenge adjudication;
- a legal revocation;
- a certification withdrawal;
- a regulator filing;
- a Gold acceptance;
- a Gold rejection.

They are record primitives a local Silver reviewer can hash-bind and
verify.
