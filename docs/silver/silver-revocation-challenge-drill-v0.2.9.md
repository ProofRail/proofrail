# Silver Revocation/Challenge Drill — v0.2.9

**Status:** Draft / ProofRail v0.2.9
**Position on the v0.2.x ladder:** post-acceptance review drill layered
on the v0.2.8 relying-party acceptance record.

---

## Thesis

> ProofRail v0.2.9 demonstrates that a Silver relying-party acceptance
> record can be stress-tested after acceptance by deterministic
> revocation and challenge signals, while preserving the boundary that
> Silver records acceptance context and does not execute Gold
> governance.

The core, narrow claim is:

> A relying party can preserve evidence that an accepted Silver package
> was later subject to a challenge or revocation signal, classify those
> signals against the local acceptance record's challenge window and
> revocation posture, and produce a hash-anchored drill report that
> says whether local review is required before reusing the acceptance.

The release does **not** claim Gold certification, dispute resolution,
legal challenge processing, regulator approval, auditor approval,
production revocation handling, cross-party governance, or that a
challenge/revocation drill changes the legal or operational status of an
acceptance record.

---

## Conceptual boundary

> A revocation/challenge drill report is not a decision, certificate,
> adjudication, or governance workflow. It is a deterministic local
> evidence artifact showing that post-acceptance review signals were
> detected, classified, and bound to a specific Silver acceptance
> package.

Important sentence:

> v0.2.9 drills post-acceptance review signals over a Silver
> relying-party acceptance record. It does not adjudicate challenges,
> revoke acceptance, certify evidence, or execute Gold governance.

---

## Schemas introduced

- `schemas/silver-relying-party-review-event-v0.1.0.md`
- `schemas/silver-revocation-challenge-drill-report-v0.1.0.md`
- `schemas/silver-revocation-challenge-drill-manifest-v0.1.0.md`

### Review event

One JSONL line per event. Every event:

```
document_type     "proofrail.silver.relying_party_review_event"
schema_version    "v0.1.0"
proofrail_release "v0.2.9"
event_id          non-empty string
event_type        challenge.received |
                  revocation.signal_received |
                  acceptance.revalidation_performed
event_time        ISO-8601 UTC Z-suffixed
target            { acceptance_record_id, purpose_id }
```

Event-type-specific required fields are documented in the review event
schema.

### Drill report

The report binds the nested v0.2.8 acceptance record (by id, decision
status, purpose, policy id/version, copied package manifest sha256) and
the review events file (by sha256). It records derived findings and
review triggers and a single `recommended_local_posture` from the
closed set:

```
acceptance_stands_for_demo_scope
acceptance_requires_review_before_reuse
acceptance_not_reusable_without_governed_review
```

### Drill manifest

Three subjects in deterministic order:

```
[0] acceptance-package/acceptance-package-manifest.json
    role: nested_acceptance_package_manifest
[1] review-events.jsonl
    role: review_events
[2] revocation-challenge-drill-report.json
    role: revocation_challenge_drill_report
```

---

## Package layout

```
<output-dir>/
  acceptance-package/                          (full byte copy of v0.2.8 package)
    acceptance-policy.json
    acceptance-record.json
    acceptance-package-manifest.json
    evidence/
      composed-gateway-evidence-manifest.json
  review-events.jsonl
  revocation-challenge-drill-report.json
  revocation-challenge-drill-manifest.json
```

The drill package does **not** copy the entire v0.2.7 composed gateway
evidence package. It may optionally re-validate against the original
v0.2.7 package root with `--evidence-package-root` on both the runner
and the verifier.

---

## Runner

```
tools/silver/run_revocation_challenge_drill_v0_1_0.py
```

```bash
python3 tools/silver/run_revocation_challenge_drill_v0_1_0.py \
  --acceptance-manifest /tmp/proofrail-silver-relying-party-acceptance-v0.2.8/acceptance-package-manifest.json \
  --review-events fixtures/silver-revocation-challenge-drill-v0.2.9/review-events.jsonl \
  --generated-at 2026-06-27T00:00:00Z \
  --output-dir /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9 \
  --force \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7] \
  [--self-validate]
```

The runner subprocess-invokes the v0.2.8 acceptance validator on the
supplied manifest. It refuses, with `FAIL:
acceptance_package_validation_failed: <detail>` and exit code 1, when
the v0.2.8 validator fails. All output is staged in a sibling
directory and atomically moved into place; a refused run leaves no
partial drill package on disk.

The runner also refuses, with `FAIL: review_fixture_insufficient:
<detail>` and exit code 1, when the fixture has zero within-window
challenges or zero revocation signals.

Runner exit codes:

```
0  success
1  drill refused (acceptance_package_validation_failed,
   review_fixture_insufficient, or self-validation failed)
2  usage or input-file error
```

`acceptance_package_validation_failed` and `review_fixture_insufficient`
are runner-only codes. They are never emitted by the verifier.

---

## Verifier

```
tools/silver/verify_revocation_challenge_drill_v0_1_0.py
```

```bash
python3 tools/silver/verify_revocation_challenge_drill_v0_1_0.py \
  --manifest /tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/revocation-challenge-drill-manifest.json \
  [--evidence-package-root /tmp/proofrail-silver-composed-gateway-demo-v0.2.7]
```

The verifier:

1. Validates the drill manifest shape, subject order, subject roles,
   subject path safety, file existence, and recomputed SHA-256.
2. Subprocess-invokes the v0.2.8 acceptance validator on the nested
   acceptance package manifest. Surfaces v0.2.8 failures as
   `nested_acceptance_package_invalid` (or
   `external_evidence_verification_failed` when
   `--evidence-package-root` is in play and the v0.2.8 output names that
   code).
3. Parses the drill report **before** checking
   `review_events.events_sha256` against the report.
4. Cross-checks `base_acceptance.*` against the nested v0.2.8 record,
   policy, and the recomputed nested package manifest sha256.
5. Parses the review-events JSONL strictly.
6. Distinguishes target mismatches by event type:
   `review_event_target_mismatch` for non-revocation events,
   `revocation_signal_target_mismatch` for revocation signals.
7. Checks `event_time` monotonicity.
8. Checks every report `challenge_within_window` finding/trigger
   references a `challenge.received` event in window
   (`challenge_window_classification_mismatch`) **before** checking
   whether at least one within-window challenge exists
   (`challenge_within_window_missing`).
9. Enforces required findings, required triggers, posture validity, and
   non-empty scope_limitations / non_claims.

### Stable failure reasons

```
invalid_drill_package_manifest
drill_subject_file_missing
drill_subject_path_traversal
drill_subject_hash_mismatch
nested_acceptance_package_invalid
invalid_review_events
invalid_drill_report
acceptance_record_binding_mismatch
review_events_hash_mismatch
review_event_target_mismatch
review_event_sequence_invalid
challenge_window_missing
challenge_within_window_missing
challenge_window_classification_mismatch
revocation_signal_missing
revocation_signal_target_mismatch
required_finding_missing
required_review_trigger_missing
recommended_posture_invalid
scope_limitations_missing
drill_non_claims_missing
external_evidence_verification_failed
```

Verifier exit codes:

```
0  drill package valid
1  verification failure
2  usage or input-file error
```

Verifier output:

```
PASS: revocation/challenge drill valid (<drill_id>)
FAIL: <reason>: <detail>
```

JSON parse errors are caught; no Python tracebacks leak for expected
malformed-input cases.

---

## Regression coverage

`tests/test_silver_revocation_challenge_drill_v0_2_9.sh` covers 33
top-level cases: end-to-end setup, two pristine verifier passes, all 22
stable verifier failure reasons, both runner-only refusal codes
(`acceptance_package_validation_failed`, `review_fixture_insufficient`),
two inline structural checks, and a scoped sha256 snapshot of committed
v0.2.9 source paths verifying that runtime did not mutate the
repository.

---

## Relationship to v0.2.8

- The drill never mutates a v0.2.8 acceptance package: the full
  subdirectory is byte-copied into `acceptance-package/`.
- The runner refuses to emit output when the v0.2.8 validator fails on
  the input package (runner-only
  `acceptance_package_validation_failed`).
- The verifier delegates nested validation to the unchanged v0.2.8
  validator. v0.2.8 failures surface as
  `nested_acceptance_package_invalid`. The v0.2.8 code
  `external_evidence_verification_failed` is preserved as a distinct
  v0.2.9 reason when `--evidence-package-root` is supplied.
- v0.2.9 introduces no new fields in v0.2.8 schemas. The drill report's
  `base_acceptance.*` block is derived from the nested package, not
  authored by hand.

---

## Relationship to v0.3.0

v0.3.0 is the planned consolidated Silver acceptance handoff release.
v0.2.9 does not anticipate or pre-bind v0.3.0. v0.2.9 still does not
claim Gold conformance or certification.

---

## Non-claims

- The drill report is not a Gold certificate, regulator approval,
  third-party audit, legal revocation, dispute resolution, or
  acceptance governance workflow.
- v0.2.9 records review triggers. It does not decide their merits.
- The drill does not query live revocation services, real challenge
  systems, real gateways, real SIEM, real GRC, or any external service.
- The drill does not alter the v0.2.7 composed gateway evidence package
  or the v0.2.8 acceptance record.
