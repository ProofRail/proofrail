# ProofRail Demo 001c Harness Cleanup

**Date:** 2026-06-13  
**Scope:** Test harness cleanup only.

Demo 001c cleans the MCP/rate-limit test harness so HTTP 429 responses during the explicit rate-limit test are treated as expected throttle evidence rather than MCP session initialization errors.

No control claim semantics changed.

The relevant improvement is that the helper script now distinguishes:

- unexpected initialize/session failures, which remain errors
- expected HTTP 429 responses during the rate-limit section, which are recorded as `THROTTLED`

This makes the rate-limit evidence clearer without changing the Bronze Claim Schema v0.1.1 fields.
