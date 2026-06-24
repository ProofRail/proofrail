# Silver Control Crosswalk + Protected Action Catalog Fixtures (v0.3.6)

These fixtures back the v0.3.6 Control Crosswalk + Protected Action Catalog
release. They are example data only.

## Files

- `control-pack.json` — happy-path pack with five protected actions and five
  crosswalk entries; used by `make run-silver-control-crosswalk-protected-action-catalog-v0-3-6`.
- `control-pack-with-dependencies.json` — exercises non-empty
  `dependency_references` across all three dependency reference types.
- `control-pack-with-limitations.json` — exercises a full
  `control_limitations` block plus exhaustive `non_claims`.

## Non-claims

These fixtures do NOT declare compliance, certification, audit approval,
regulator approval, auditor approval, production authorization, control
design effectiveness, control operating effectiveness, legal enforceability,
runtime truth, transferred trust, Gold governance, or governed reliance.
They demonstrate the structural shape of a Silver control crosswalk and
protected action catalog; they are not a control decision, compliance
decision, or authorization decision.

## Mutation tests

The regression suite at
`tests/test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh`
mutates copies of `control-pack.json` to exercise each approved verifier
failure reason. The fixture files in this directory are never mutated by the
test; the test asserts a scoped sha256 snapshot equality across all
v0.3.6-owned source files BEFORE and AFTER the run.
