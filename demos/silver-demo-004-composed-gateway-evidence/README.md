# ProofRail Silver Demo 004 — Composed Gateway Evidence (v0.2.7)

**ProofRail release:** v0.2.7
**Demo ID:** `proofrail-silver-demo-004-composed-gateway-evidence`

> v0.2.7 demonstrates substrate-neutral evidence composition. It does not
> integrate with a real gateway or certify gateway enforcement.

The simulated gateway is an evidence source, not a trust authority.

---

## What this demo shows

A ProofRail Silver evidence package can be **composed** from:

1. a v0.2.6 simulated gateway adapter descriptor
   (`examples/silver-evidence-source-adapters/gateway-mcp-simulated-v0.2.6.json`), and
2. a v0.2.7 simulated gateway event fixture
   (`fixtures/silver-composed-gateway-evidence-v0.2.7/gateway-events.jsonl`),

and the resulting package can be **independently verified** with hash anchors,
re-derived claims, and trust-boundary preservation.

No real gateway is contacted, no live MCP traffic is exchanged, no protected
action is executed.

---

## Run

```bash
make run-silver-composed-gateway-demo-v0-2-7
```

This composes the package into
`/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/` and verifies it.

## Verify (regression test)

```bash
make verify-silver-composed-gateway-demo-v0-2-7
```

This runs `tests/test_silver_composed_gateway_evidence_v0_2_7.sh` which exercises
the composer, verifier, and a battery of tamper cases.

---

## Package layout (runtime)

```
/tmp/proofrail-silver-composed-gateway-demo-v0.2.7/
├── README.md
├── demo-walkthrough.md
├── adapter/
│   └── gateway-mcp-simulated-v0.2.6.json
├── source/
│   └── gateway-events.jsonl
├── composed-gateway-evidence-report.json
└── composed-gateway-evidence-manifest.json
```

The manifest anchors the five subjects in deterministic order: `README.md`,
`demo-walkthrough.md`, `adapter/gateway-mcp-simulated-v0.2.6.json`,
`source/gateway-events.jsonl`, `composed-gateway-evidence-report.json`.

---

## Required claim IDs

The composed report contains exactly ten claims, all with `status: "pass"`:

```
gateway_source_described_by_adapter
gateway_source_not_trust_authority
gateway_events_normalized
protected_actions_require_scoped_authority
unauthorized_delegation_fails
bypass_attempts_observed_or_blocked
revoked_authority_fails
out_of_scope_actions_fail
source_evidence_hash_verifiable
no_protected_actions_executed
```

See `demo-walkthrough.md` for the derivation table.

---

## Non-claims

- v0.2.7 does not integrate with any real MCP gateway, observability stack,
  SIEM, policy engine, or GRC platform.
- v0.2.7 does not certify gateway enforcement.
- v0.2.7 does not execute any protected action.
- v0.2.7 does not establish a new trust authority. The gateway remains an
  evidence source.
- v0.2.7 is not Gold acceptance, production assurance, compliance, or
  certification.
- The composed report is not signed; v0.2.7 ships local hash anchors only.
