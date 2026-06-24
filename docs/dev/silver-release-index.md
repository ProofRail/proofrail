# ProofRail — Silver Release Index

Per-release reference in compact form. One entry per Silver release.
Each entry covers: scope, key tools, schemas / docs, regression test,
manifest shape, key non-claims.

For per-release command invocations, see `docs/dev/silver-command-index.md`.
For durable process rules, see `docs/dev/coding-assistant-guardrails.md`.
For long-form release narratives, see `docs/silver/silver-<slug>-v0.x.y.md`
and `docs/gold/gold-boundary-v0.2.5.md`. For the current operating
release, see `CLAUDE.md`.

## Cross-cutting design patterns

- **Deterministic hashing:** Canonical JSON `json.dumps(obj, sort_keys=True, separators=(",",":"))` ensures reproducible SHA256 hashes.
- **Evidence coupling:** Claims reference evidence files by path; `--evidence-root` validation checks files exist.
- **Decision vocabulary:** Minimum set `{allow, block, rate_limit, emergency_stop}`.
- **Normalized audit events:** JSONL with required event types (`tool_call.attempt`, `tool_call.decision`, `tool_call.result`, `emergency.stop`, `emergency.resume`).
- **Risk tiering:** Protected actuators assigned tiers 0–3.
- **Nested dict access:** `_get()` helper uses dot notation for deep field access in validation.
- **Staging-then-replace:** Stage under `<output-dir>.staging.<pid>` and `os.replace()` only after successful (optional self-) validation.

---

## Bronze core (v0.1.1 / v0.1.2 / v0.1.3)

- **Scope:** Bronze claim schema, claim validation, evidence checksum verification, evidence bundle manifest.
- **Schemas:** `schemas/bronze-claim-schema-v0.1.1.md`, `schemas/bronze-claim-schema-v0.1.2.md`.
- **Claim shape:** YAML files with 16+ required top-level sections (`REQUIRED_TOP_LEVEL_SECTIONS`). v0.1.2 adds optional `evidence_checksums`.
- **Claim types:** `composed_bronze`, `native_bronze_preview`.
- **Tools:**
  - `scripts/proofrail_claim.py` — primary CLI (~815 lines): `init`, `validate`, `summarize`; structural validation only.
  - `tools/claims/generate_bronze_claim_v0_1_1.py`, `validate_bronze_claim_v0_1_1.py`
  - `tools/claims/generate_bronze_claim_v0_1_2.py`, `validate_bronze_claim_v0_1_2.py`, `verify_bronze_claim_evidence_v0_1_2.py`
  - `tools/claims/generate_evidence_bundle_manifest_v0_1_3.py`, `verify_evidence_bundle_manifest_v0_1_3.py`
- **Demo stack:** `demos/composed-bronze-demo-001/` — Docker Compose with `agentgateway`, `mock-mcp`, `stop-mcp`, `agent`, `bypass-tester`; two networks (`agent_net`, `actuator_net`); evidence produced by `scripts/run_tests.sh`.
- **Non-claims:** Structural validation only. No semantic conformance, deployment certification, or live-system inspection.

---

## Silver v0.1.0 (signed bundle assertion + revocation + verification report)

- **Demo:** `demos/silver-demo-001-signed-bundle-assertion/`, `demos/silver-demo-002-independent-verifier/`.
- **Tools:** `generate_demo_issuer_v0_1_0.py`, `sign_bundle_manifest_v0_1_0.py`, `verify_signed_bundle_assertion_v0_1_0.py`, `validate_silver_verification_report_v0_1_0.py`, `generate_demo_revocation_list_v0_1_0.py`, `export_independent_verification_package_v0_1_0.py`.
- **Schemas:** Silver Verification Report v0.1.0; Silver Signed Bundle Assertion v0.1.0.
- **Tests:** `test_silver_signed_bundle_assertion_v0_1_0.sh`, `test_silver_revocation_list_v0_1_0.sh`, `test_silver_verification_report_v0_1_0.sh`, `test_independent_silver_verifier_v0_1_0.sh`.
- **Demo 002:** Standalone verifier with all seven Silver checks implemented inline; emits v0.1.0-compatible report.

## Silver v0.2.0 / v0.2.1 (relying-party profile conformance)

- **Tools:** `validate_silver_profile_v0_2_0.py` (modes `silver.base`, `silver.independent`); `validate_silver_profile_v0_2_1.py` (modes `silver.base`, `silver.base.demo`, `silver.independent`; tightened revocation for `silver.base`); `export_independent_verification_package_v0_2_1.py`.
- **Tests:** `test_silver_profile_v0_2_0.sh`, `test_silver_profile_v0_2_1.sh`, `test_silver_profile_examples_v0_2_1.sh`.

## Silver v0.2.2 (verifier output attestation)

- **Tools:** `generate_demo_verifier_attestor_v0_1_0.py` (separate attestor keys from issuer keys); `sign_verifier_output_attestation_v0_1_0.py`; `verify_verifier_output_attestation_v0_1_0.py`.
- **Test:** `test_silver_verifier_output_attestation_v0_1_0.sh`.
- **Non-claims:** Rejects `..` in subject paths.

## Silver v0.2.3 (multi-principal authority)

- **Tools:** `validate_multi_principal_authority_fixture_v0_1_0.py`; `evaluate_multi_principal_authority_v0_1_0.py` (10-check short-circuit evaluation; never executes actions).
- **Test:** `test_silver_multi_principal_authority_v0_2_3.sh`.

## Silver v0.2.4 (multi-agent attack harness)

- **Tools:** `run_multi_agent_attack_harness_v0_1_0.py`; `verify_multi_agent_harness_evidence_v0_1_0.py`.
- **Test:** `test_silver_multi_agent_attack_harness_v0_2_4.sh`.
- **Manifest:** Transcript + requests + decision reports + run report + evidence manifest. Path traversal rejected.

## Silver v0.2.5 (multi-agent trust-boundary demo package)

- **Demo:** `demos/silver-demo-003-multi-agent-trust-boundary/`. Committed dir holds README + walkthrough only; runtime output under `/tmp/proofrail-silver-multi-agent-demo-v0.2.5/`.
- **Tools:** `package_multi_agent_trust_boundary_demo_v0_1_0.py`; `verify_multi_agent_trust_boundary_demo_v0_1_0.py`.
- **Test:** `test_silver_multi_agent_trust_boundary_demo_v0_2_5.sh`.
- **Claims (8):** `harmless_messages_proceed`, `protected_actions_require_scoped_authority`, `unauthorized_delegation_fails`, `bypass_attempts_blocked`, `revoked_authority_fails`, `out_of_scope_actions_fail`, `evidence_is_hash_verifiable`, `no_protected_actions_executed`. Nested failures surface as `nested_harness_evidence_invalid`.
- **Docs:** `docs/silver/silver-multi-agent-trust-boundary-demo-v0.2.5.md`, `docs/gold/gold-boundary-v0.2.5.md`.

## Silver v0.2.6 (evidence source adapter profile)

- **Examples:** `examples/silver-evidence-source-adapters/` — six canonical descriptors (gateway, observability trace, SIEM, policy engine, GRC platform, native ProofRail).
- **Tool:** `validate_evidence_source_adapter_v0_1_0.py` — closed 6-value `source_type` set; six required capabilities with `provided`/`not_provided`/`not_applicable`; `decision_event` must be `provided` with full mapping fields; rejects empty/whitespace-only strings and traversal in sample-artifact-refs; duplicate adapter_id detection in directory mode.
- **Test:** `test_silver_evidence_source_adapter_v0_2_6.sh`.
- **Non-claims:** Descriptors are not evidence, not trust decisions, not certifications.
- **Schema:** `schemas/silver-evidence-source-adapter-v0.1.0.md`. Docs: `docs/silver/silver-evidence-source-adapter-profile-v0.2.6.md`.

## Silver v0.2.7 (composed gateway evidence)

- **Demo:** `demos/silver-demo-004-composed-gateway-evidence/`. Runtime under `/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/`.
- **Tools:** `compose_gateway_evidence_demo_v0_1_0.py` (subprocess-invokes unchanged v0.2.6 validator; derives 10 claims; emits report + manifest with 5 subjects + `composition` block); `verify_composed_gateway_evidence_demo_v0_1_0.py` (18 stable failure reasons; rejects wrong-but-valid evidence refs).
- **Test:** `test_silver_composed_gateway_evidence_v0_2_7.sh`. Fixture: `fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl` (9 events).
- **Manifest:** 5 subjects deterministic order; `composition.source_type = "gateway"`, `source_is_trust_authority: false`.
- **Non-claims:** Simulated gateway is evidence source, not trust authority. Unsigned; local hash anchors only.

## Silver v0.2.8 (relying-party acceptance record)

- **Demo:** `demos/silver-demo-005-relying-party-acceptance/`. Runtime under `/tmp/proofrail-silver-relying-party-acceptance-v0.2.8/`.
- **Tools:** `generate_relying_party_acceptance_record_v0_1_0.py` (subprocess-invokes v0.2.7; refuses `--decision accepted` on v0.2.7 failure with `FAIL: evidence_verification_failed`); `validate_relying_party_acceptance_record_v0_1_0.py` (22 ordered checks; 21 stable reasons; optional `--evidence-package-root` re-invokes v0.2.7).
- **Test:** `test_silver_relying_party_acceptance_record_v0_2_8.sh`.
- **Manifest:** 3 subjects (`acceptance_policy`, `verified_evidence_manifest`, `acceptance_record`). `decision.status ∈ {accepted, rejected, accepted_with_exceptions}`.
- **Three distinct verification reasons:** `evidence_verification_required` (validator), `evidence_verification_failed` (generator-only; validator never emits), `external_evidence_verification_failed` (validator with external root).
- **Non-claims:** Not a Gold certificate, regulator/auditor/third-party approval, or legal acceptance.

## Silver v0.2.9 (revocation / challenge drill)

- **Demo:** `demos/silver-demo-006-revocation-challenge-drill/`. Runtime under `/tmp/proofrail-silver-revocation-challenge-drill-v0.2.9/`.
- **Tools:** `run_revocation_challenge_drill_v0_1_0.py` (subprocess-invokes v0.2.8; refuses with `acceptance_package_validation_failed` or `review_fixture_insufficient`; staging-then-replace); `verify_revocation_challenge_drill_v0_1_0.py` (22 stable reasons; runner-only refusal codes never emitted; parses drill report before checking events hash; splits target-mismatches by event type; classification before within-window-missing).
- **Test:** `test_silver_revocation_challenge_drill_v0_2_9.sh`.
- **Manifest:** 3 subjects (nested v0.2.8 manifest, review-events JSONL, drill report).
- **Closed posture set:** `{acceptance_stands_for_demo_scope, acceptance_requires_review_before_reuse, acceptance_not_reusable_without_governed_review}`.
- **Non-claims:** Not a Gold certificate, regulator approval, audit, legal revocation, dispute resolution, or acceptance governance workflow.

## Silver v0.3.0 (acceptance handoff)

- **Demo:** `demos/silver-demo-007-acceptance-handoff/`. Runtime under `/tmp/proofrail-silver-acceptance-handoff-v0.3.0/`.
- **Tools:** `build_silver_acceptance_handoff_v0_1_0.py` (subprocess-invokes v0.2.7 / v0.2.8 / v0.2.9, the latter two WITHOUT `--evidence-package-root` so v0.3.0 owns chain-binding; four runner-only refusal codes + `handoff_chain_binding_failed`; staging + `--self-validate`); `verify_silver_acceptance_handoff_v0_1_0.py` (17 stable reasons; never emits runner-only codes).
- **Test:** `test_silver_acceptance_handoff_v0_3_0.sh`.
- **Manifest:** 4 subjects in fixed order (composed-gateway-evidence manifest, acceptance-package manifest, drill manifest, handoff summary). Package layout copies nested roots under `composed-gateway-evidence/`, `acceptance-package/`, `revocation-challenge-drill/`.
- **Chain bindings (4):** top-level evidence sha256 = v0.2.8 record `evidence_package.manifest_sha256`; top-level acceptance sha256 = v0.2.9 `base_acceptance.acceptance_package_manifest_sha256`; inner copy `acceptance-package/evidence/composed-gateway-evidence-manifest.json` = subject [0]; inner copy `revocation-challenge-drill/acceptance-package/acceptance-package-manifest.json` = subject [1].
- **Posture ranks:** rank 0 `for_demo_scope` < rank 1 `review_required_before_reuse` < rank 2 `not_reusable_without_governed_review`. Downgrades rejected as `handoff_posture_downgrade`.
- **Overclaim guard:** 15 forbidden positive tokens including `certified`, `approved`, `audited`, `legally accepted`, `legally revoked`, `challenge resolved`, `gold accepted`, `gold certified`, `compliant`, `production-approved`, `production-ready`, `regulator-ready`, `regulator approval`, `trust transferred`, `trust transfer`.
- **Non-claims:** Unsigned. Packages already-verified evidence; not a certificate, Gold conformance, regulator/auditor approval, legal acceptance, or reliance transfer.

## Silver v0.3.1 (handoff inspector + Gold gap inventory)

- **Demo:** `demos/silver-demo-008-handoff-inspector/`. Runtime under `/tmp/proofrail-silver-handoff-inspection-v0.3.1/`.
- **Tools:** `inspect_silver_acceptance_handoff_v0_1_0.py` (subprocess-invokes v0.3.0 verifier on handoff; subprocess-invokes v0.3.1 `--validate-requirement-set`; staging + `--self-validate`); `verify_silver_handoff_inspection_v0_1_0.py` (20 stable reasons; never emits the three runner-only refusal codes; exposes `--validate-requirement-set`).
- **Test:** `test_silver_handoff_inspector_v0_3_1.sh`.
- **Manifest:** 3 subjects in fixed order. Reserves `inspection_handoff_summary_mismatch` for non-posture fields; `inspection_review_posture_downgrade` for posture-rank-weaker or missing `reuse_warning`; `requirement_duplicate` and `requirement_domain_missing` as distinct reasons.
- **Overclaim guard:** adds `gold-ready` / `gold ready` / `gold_ready` to v0.3.0's 15 tokens (18 total).

## Silver v0.3.2 (trace binding profile)

- **Demo:** `demos/silver-demo-009-trace-binding-profile/`. Runtime under `/tmp/proofrail-silver-trace-binding-v0.3.2/`.
- **Tools:** `build_silver_trace_binding_v0_1_0.py` (structural trust-authority pre-check BEFORE v0.2.6 validator subprocess — Amendment 1; cross-checks every non-gap binding row against its resolved trace event — Amendment 4; four runner-only refusal codes); `verify_silver_trace_binding_v0_1_0.py` (22 stable reasons; never emits runner-only codes).
- **Test:** `test_silver_trace_binding_v0_3_2.sh`. Fixtures under `fixtures/silver-trace-binding-profile-v0.3.2/`: 8-event JSONL + 9-row binding set.
- **Manifest:** 4 subjects in fixed order.
- **Reachability orderings (key):** Amendment 1 — `trace_source_marked_authority` BEFORE `trace_adapter_invalid`. Amendment 2 — `trace_warning_downgrade` BEFORE generic `trace_report_status_mismatch`. Path traversal BEFORE exact subject-path equality.
- **Overclaim guard:** 22 tokens including `runtime proof`, `authoritative trace`, `opentelemetry compliant`, `opentelemetry conformance`.
- **Non-claims:** Adapter is descriptor, not trust authority. Unsigned. Not OpenTelemetry conformance, not Gold, not regulator/auditor/legal acceptance, no production reliance.

## Silver v0.3.3 (adapter pilot package)

- **Demo:** `demos/silver-demo-010-adapter-pilot-package/`. Runtime under `/tmp/proofrail-silver-adapter-pilot-v0.3.3/`.
- **Tools:** `build_silver_adapter_pilot_v0_1_0.py` (subprocess-invokes v0.2.6 validator + v0.3.2 builder; OpenTelemetry-shaped source export with strict ordering + closed `export_format = "proofrail.simulated_otel_trace_export.v0.1"` + closed `proofrail.decision`; normalization map mapping language: `<source.dot.path>` and `constant:<literal>` only; LONGEST-PREFIX KEY MATCHING for dot-path resolution; six runner-only refusal codes); `verify_silver_adapter_pilot_v0_1_0.py` (24 stable reasons across 25 ordered checks; never emits runner-only codes).
- **Test:** `test_silver_adapter_pilot_v0_3_3.sh`. Fixtures under `fixtures/silver-adapter-pilot-package-v0.3.3/`.
- **Manifest:** 7 subjects in fixed order (adapter / source export / normalization map / normalized trace events / normalized bindings / nested v0.3.2 manifest / pilot report).
- **Reachability orderings (key):** path traversal BEFORE subject-path equality; adapter trust-authority pre-check BEFORE v0.2.6 subprocess; re-derived normalized bytes BEFORE v0.3.2 subprocess; v0.3.2 subprocess BEFORE nested-manifest hash cross-check.
- **Overclaim guard:** 23 tokens including `runtime truth proved`, `opentelemetry conformance`, `vendor certified`, `production approved`.
- **Non-claims:** Not OpenTelemetry conformance, not vendor certification, not production integration, not Gold, no production reliance.

## Silver v0.3.4 (challenge / withdrawal record primitives)

- **Demo:** `demos/silver-demo-011-challenge-withdrawal-primitives/`. Runtime under `/tmp/proofrail-silver-challenge-withdrawal-primitives-v0.3.4/`.
- **Tools:** `build_silver_challenge_withdrawal_primitives_v0_1_0.py` (subprocess-invokes v0.3.0; accepts literal placeholder `sha256:TO_BE_BOUND_BY_RUNNER` in `target.target_manifest_sha256` — Amendment 1; deterministic JSON output `json.dumps(obj, indent=2, sort_keys=True)` — Amendment 2; optional `description` on claims — Amendment 3; runner-only refusal codes for record / binding / self-validation failures; module constant `CHALLENGE_WITHDRAWAL_VERIFIER` for test monkey-patching); `verify_silver_challenge_withdrawal_primitives_v0_1_0.py` (24 stable reasons across 29 ordered checks; never emits the five runner-only refusal codes).
- **Test:** `test_silver_challenge_withdrawal_primitives_v0_3_4.sh`. Fixtures: `fixtures/silver-challenge-withdrawal-primitives-v0.3.4/`.
- **Closed enums:** `challenge_reason` (10), `challenge_status` (4), `withdrawal_reason` (7), `withdrawal_status` (4), `withdrawal_effect` (4).
- **Manifest:** 4 subjects in fixed order. Posture forced from `withdrawal_effect → posture` closed mapping table.
- **Seven required claims pre-baked at `status: pass`:** `target_handoff_verified`, `challenge_record_valid`, `withdrawal_record_valid`, `challenge_and_withdrawal_target_same_handoff`, `withdrawal_cites_challenge`, `time_order_valid`, `no_adjudication_claimed`.
- **Non-claims:** Not an adjudication, not legal revocation, not target-handoff certification, not Gold, no production reliance.

## Silver v0.3.5 (relying-party policy pack)

- **Demo:** `demos/silver-demo-012-relying-party-policy-pack/`. Runtime under `/tmp/proofrail-silver-relying-party-policy-pack-v0.3.5/`.
- **Tools:** `build_silver_relying_party_policy_pack_v0_1_0.py` (5 runner-only refusal codes: `runner_input_path_missing`, `runner_input_path_forbidden`, `runner_input_file_missing`, `runner_input_read_failed`, `runner_input_json_invalid`; deterministic 24-entry conformance report); `verify_silver_relying_party_policy_pack_v0_1_0.py` (24 stable reasons across 25 execution checks; non-masking ordering; never emits runner-only codes).
- **Test:** `test_silver_relying_party_policy_pack_v0_3_5.sh` (47 exercises: 4 PP + 24 case + 11 dup + 5 ro + 1 rel + 1 TG + 1 SS).
- **Manifest:** 2 subjects (`policy-pack.json`, `silver-relying-party-policy-pack-conformance-report.json`).
- **Closed enum surface (11):** acceptance / challenge / withdrawal / supersession postures (3 values each), verifier / issuer / revocation / freshness modes, supported signature algorithms, criteria result enums (4), warning treatments, related-artifact reference policy, exception / hard-stop modes.
- **Overclaim guard:** 23 tokens (v0.3.x shared set); scans every string outside `scope_limitations`, `non_claims`, `relying_party.contact`.
- **Bundled-report disagreement:** funneled back to `policy_pack_manifest_invalid` (no 25th public reason).
- **Non-claims:** Unsigned; does not approve/audit/certify; not adjudication; no upstream re-evaluation; no reliance transfer; not Gold readiness.

## Silver v0.3.6 (control crosswalk + protected action catalog)

- **Demo:** `demos/silver-demo-013-control-crosswalk-protected-action-catalog/`. Runtime under `/tmp/proofrail-silver-control-crosswalk-protected-action-catalog-v0.3.6/`.
- **Tools:** `build_silver_control_crosswalk_protected_action_catalog_v0_1_0.py` (5 runner-only refusal codes; deterministic 24-entry conformance report); `verify_silver_control_crosswalk_protected_action_catalog_v0_1_0.py` (24 stable reasons across 25 ordered execution steps; never emits runner-only codes).
- **Test:** `test_silver_control_crosswalk_protected_action_catalog_v0_3_6.sh` (47 exercises: 4 PP + 24 case + 11 dup + 5 ro + 1 rel + 1 TG + 1 SS).
- **Manifest:** 2 subjects with cross-anchored `control_pack_id`.
- **Closed enum surface:** catalog `category` / `environment_scope` / `actor_scope`; `authority.posture`; `risk_boundary.risk_class`; 43-entry ProofRail crosswalk `artifact_type` set; crosswalk `relationship`; conservative claim verbs `may_inform` / `may_evidence` / `may_support`; `control_limitations.domain`; dependency `reference_type`; closed Silver `upstream_id` set.
- **Overclaim guard:** 32 tokens including external framework names (`soc 2`, `iso 27001`, `nist 800-53`, `pci dss`, `hipaa`), `control design effective`, `control operating effective`, `audit ready`, `regulator approved`, `auditor approved`, `production approved`, `production authorized`, `production ready`, `legally enforceable`, `legally binding`, `trust transferred`, `runtime truth`, `governed reliance`, Gold reliance tokens.
- **Bundled-report disagreement OR `control_pack_id` mismatch:** funneled to `control_pack_manifest_invalid` (no 25th reason).
- **Non-claims:** Does not approve/audit/certify; does not map to external frameworks; does not opine on control design/operating effectiveness; no upstream re-evaluation; no reliance transfer; not Gold readiness.

## Silver v0.3.7 (registry lite) — current release

- **Demo:** `demos/silver-demo-014-registry-lite/`. Runtime under `/tmp/proofrail-silver-registry-lite-v0.3.7/`.
- **Tools:** `build_silver_registry_lite_v0_1_0.py` (5 runner-only refusal codes; deterministic 24-entry conformance report); `verify_silver_registry_lite_v0_1_0.py` (24 stable reasons across 24 ordered structural checks plus post-structural conformance-report re-derivation; never emits runner-only codes).
- **Test:** `test_silver_registry_lite_v0_3_7.sh` (48 exercises: 4 PP + 24 case + 11 dup + 6 runner-only refusal exercises covering 5 distinct runner-only reasons (ro1, ro2, ro2b, ro3..ro5) + 1 rel + 1 TG + 1 SS). TG1 ships with EMPTY `ALLOWED_NON_REASON_TOKENS` allowlist.
- **Manifest:** 2 subjects (`registry-lite.json`, `silver-registry-lite-conformance-report.json`) with cross-anchored `registry_id`.
- **Entity model — 6 closed roles:** `issuer`, `verifier`, `relying_party`, `policy_authority`, `revocation_source`, `protected_action_authority`. Each entry: `entity_id`, `display_label`, `role`, `status`, `effective_period`, optional `key_references[]`, `key_bindings[]`, plus role-specific block.
- **Closed enum surface:** entity `role` (6), `status` (5), `registry_scope`, `release_binding`, `key_references[].algorithm` (6), `key_reference_type` (3), `key_bindings[].binding_purpose` (5), `verifier_posture` (3), `authority_boundary` (3), `source_type` (3), `status_mode` (3), `delegation_boundary` (4), `trust_relationships[].relationship_verb` (6), Silver `upstream_id` + `upstream_version` (v0.2.1..v0.3.6).
- **Overclaim guard:** 36 tokens covering production-PKI / certificate-authority / certification-authority / legal-identity / identity-proofing / federation / trust-federation / certification / compliance / legal enforceability / production authorization / regulator-or-auditor approval / audit readiness and effectiveness / runtime-truth / trust-transfer / Gold reliance tokens.
- **Fixture variants (3):** `registry-lite.json` (canonical, one entry per each of the 6 roles), `registry-lite-with-trust-relationships.json` (exercises all 6 `relationship_verb` values), `registry-lite-with-revocation-source.json` (`source_type: signed_revocation_record`, `key_reference_type: local_pem_path`, `binding_purpose: sign_revocation`).
- **Bundled-report disagreement OR `registry_id` mismatch:** funneled to `registry_manifest_invalid` (no 25th reason).
- **Path traversal:** ro2 + ro2b both emit `runner_input_path_forbidden` (absolute + parent-traversal variants).
- **Non-claims:** Unsigned; not production PKI / certificate authority / certification authority / legal identity registry / identity-proofing record / federation registry / trust federation; does not approve/audit/certify; no upstream re-evaluation; no reliance transfer; not Gold readiness; not Gold artifact; does not advance the Gold boundary.

---

## Next release

- **v0.4.0 Minimal Gold:** planned. Will be tracked in `CLAUDE.md` once active.
