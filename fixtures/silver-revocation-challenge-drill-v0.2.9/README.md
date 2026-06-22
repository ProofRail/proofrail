# Silver Revocation/Challenge Drill Fixture v0.2.9

This directory holds the deterministic review-event fixture consumed by
the v0.2.9 revocation/challenge drill runner.

## Files

- `review-events.jsonl` — three JSONL lines:
  1. `REVIEW-EVT-001-challenge-within-window`
     (`challenge.received`, within the demo acceptance record's
     challenge window)
  2. `REVIEW-EVT-002-post-acceptance-revocation-signal`
     (`revocation.signal_received`, after the demo acceptance time)
  3. `REVIEW-EVT-003-acceptance-package-revalidated`
     (`acceptance.revalidation_performed`)

All three events target:

- `target.acceptance_record_id`: `proofrail-acceptance-record-demo-001`
- `target.purpose_id`: `demo_trust_boundary_review`

`event_time` is monotonically non-decreasing.

## Non-claims about this fixture

- This fixture is a deterministic demo input. It is **not** a real
  challenge submission, real revocation list, legal notice, or governed
  dispute filing.
- The events do not by themselves revoke acceptance or alter the
  underlying v0.2.7 composed gateway evidence package or v0.2.8
  acceptance record.
- The fixture is not signed and does not establish Gold conformance.

## Related schemas

- `schemas/silver-relying-party-review-event-v0.1.0.md`
- `schemas/silver-revocation-challenge-drill-report-v0.1.0.md`
- `schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md`
