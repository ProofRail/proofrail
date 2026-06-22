# Silver Acceptance Handoff — v0.3.0

**Status:** Draft / ProofRail v0.3.0
**Position on the v0.x ladder:** composition release that packages the
v0.2.7 / v0.2.8 / v0.2.9 Silver evidence chain into a portable,
hash-anchored local handoff artifact.

---

## Thesis

> ProofRail v0.3.0 packages the completed Silver acceptance chain into
> a portable handoff artifact that binds composed evidence,
> relying-party acceptance, and post-acceptance review signals without
> claiming Gold certification, regulatory approval, legal reliance, or
> governed acceptance.

The core, narrow claim is:

> The three already-verified Silver pipelines — composed gateway
> evidence (v0.2.7), relying-party acceptance (v0.2.8), and
> revocation/challenge drill (v0.2.9) — can be assembled into a single
> portable, hash-anchored package whose internal cross-references the
> v0.3.0 verifier owns and re-derives end to end, and whose
> recommended local handoff posture is never weaker than the rank
> required by the nested v0.2.9 drill posture.

The release does **not** claim Gold certification, regulator approval,
auditor approval, legal acceptance, governed acceptance, transferred
reliance, adjudicated challenges, legally revoked acceptance,
production approval, or any extension of what the underlying v0.2.7 /
v0.2.8 / v0.2.9 evidence asserts.

---

## Conceptual boundary

> A Silver acceptance handoff package is not a certificate, approval,
> adjudication, audit, or trust transfer. It is the integrity anchor
> over a portable evidence package whose internal cross-binding the
> v0.3.0 verifier owns and re-derives end to end.

Important sentence:

> v0.3.0 packages already-verified Silver evidence. It does not extend
> the substance of what that evidence asserts.

---

## Schemas introduced

- `schemas/silver-acceptance-handoff-summary-v0.1.0.md`
- `schemas/silver-acceptance-handoff-manifest-v0.1.0.md`

### Handoff summary

The summary records the included v0.2.7 / v0.2.8 / v0.2.9 manifest
hashes, the v0.2.8 acceptance record id, decision status, and
purpose, the v0.2.9 recommended local posture, the derived v0.3.0
handoff posture, and a non-empty `reuse_warning`. It is emitted by
`tools/silver/build_silver_acceptance_handoff_v0_1_0.py` and
re-derived by the v0.3.0 verifier from the nested packages.

### Handoff manifest

The manifest is the package-level hash anchor. It records exactly
four subjects, in this fixed order:

```
[0] composed-gateway-evidence/composed-gateway-evidence-manifest.json
    role: composed_gateway_evidence_manifest
[1] acceptance-package/acceptance-package-manifest.json
    role: relying_party_acceptance_package_manifest
[2] revocation-challenge-drill/revocation-challenge-drill-manifest.json
    role: revocation_challenge_drill_manifest
[3] silver-acceptance-handoff-summary.json
    role: silver_acceptance_handoff_summary
```

The full v0.2.7 / v0.2.8 / v0.2.9 package roots are byte-copied under
the three top-level directories. Those nested files are anchored
transitively through the three nested package manifests (subjects 0,
1, 2), which the v0.3.0 verifier re-validates via subprocess.

---

## Posture rank model

The v0.3.0 verifier maps the nested v0.2.9 `recommended_local_posture`
onto a minimum handoff posture rank:

```
acceptance_stands_for_demo_scope                -> rank 0
acceptance_requires_review_before_reuse         -> rank 1
acceptance_not_reusable_without_governed_review -> rank 2

silver_handoff_complete_for_demo_scope                (rank 0)
silver_handoff_complete_review_required_before_reuse  (rank 1)
silver_handoff_not_reusable_without_governed_review   (rank 2)
```

An unknown drill posture or unknown handoff posture is rejected as
`handoff_posture_invalid`. A handoff posture whose rank is **lower**
than the rank required by the drill posture is rejected as
`handoff_posture_downgrade`. Equal or stricter (higher-rank) handoff
postures pass.

---

## Chain binding (v0.3.0 owns this)

The v0.3.0 runner and verifier each perform the same four
cross-checks between the package's top-level manifests and the
recorded sha256 fields inside the nested packages:

```
(a) sha256(composed-gateway-evidence/composed-gateway-evidence-manifest.json)
    == nested v0.2.8 record evidence_package.manifest_sha256

(b) sha256(acceptance-package/acceptance-package-manifest.json)
    == nested v0.2.9 drill report
       base_acceptance.acceptance_package_manifest_sha256

(c) sha256(acceptance-package/evidence/composed-gateway-evidence-manifest.json)
    == subject [0] sha256

(d) sha256(revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json)
    == subject [1] sha256
```

These four checks are intentionally owned by v0.3.0 and not delegated
to the v0.2.8 / v0.2.9 `--evidence-package-root` cross-checks, so a
mismatch surfaces under the specific v0.3.0 reason
`handoff_chain_binding_mismatch` (verifier) or
`handoff_chain_binding_failed` (runner) rather than as a generic
nested-package failure.

---

## Stable failure reasons (verifier)

```
invalid_handoff_manifest
handoff_subject_file_missing
handoff_subject_path_traversal
handoff_subject_hash_mismatch
nested_composed_evidence_invalid
nested_acceptance_package_invalid
nested_revocation_challenge_drill_invalid
handoff_summary_invalid
handoff_summary_binding_mismatch
handoff_chain_binding_mismatch
handoff_record_mismatch
handoff_purpose_mismatch
handoff_posture_invalid
handoff_posture_downgrade
handoff_overclaim
handoff_limitations_missing
handoff_non_claims_missing
```

## Runner-only refusal codes

```
composed_evidence_validation_failed
acceptance_package_validation_failed
drill_package_validation_failed
handoff_chain_binding_failed
self_validation_failed
```

The runner-only codes are deliberately distinct from the verifier
codes. The verifier never emits them.

---

## Overclaim guard

The v0.3.0 verifier scans every string value in the handoff summary
(recursively) **outside** the `scope_limitations` and `non_claims`
arrays for positive overclaim wording. Forbidden positive tokens
(case-insensitive substring match):

```
"certified", "approved", "audited",
"legally accepted", "legally revoked",
"challenge resolved",
"gold accepted", "gold certified",
"compliant", "production-approved", "production-ready",
"regulator-ready", "regulator approval",
"trust transferred", "trust transfer"
```

Any positive occurrence raises `handoff_overclaim`. The same tokens
may appear inside `scope_limitations` and `non_claims` (where they
typically appear in negated form to **deny** the overclaim).

---

## Boundary statements

- v0.3.0 is composition. v0.3.0 does not introduce new evidence
  content.
- v0.3.0 does not certify the included evidence chain.
- v0.3.0 does not transfer reliance from one relying party to another.
- v0.3.0 does not adjudicate any challenge or revocation signal.
- v0.3.0 does not establish Gold conformance, regulator approval,
  auditor approval, legal acceptance, or production authorization.
- The `recommended_handoff_posture` is descriptive. It is not an
  approval, not a decision, and not a governance act.

---

## Demo

See `demos/silver-demo-007-acceptance-handoff/`.

Make targets:

```
make run-silver-acceptance-handoff-v0-3-0
make verify-silver-acceptance-handoff-v0-3-0
```

The `run-` target rebuilds the entire v0.2.7 → v0.2.8 → v0.2.9 → v0.3.0
chain end to end.

Regression test:

```
bash tests/test_silver_acceptance_handoff_v0_3_0.sh
```
