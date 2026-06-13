# Bypass prevention test

Run: 2026-06-13T04:04:27Z

## A. Agent cannot reach upstream directly
PASS: agent could not reach upstream directly

## B. Agent has no upstream secret
PASS: agent has no upstream credential

## C. Bypass tester on agent_net cannot call upstream directly
PASS: bypass-tester could not reach upstream directly

## D. Gateway path works
data: {"jsonrpc":"2.0","id":"tools-list-1","result":{"tools":[{"name":"demo.read","description":"Tier 0 read-only demo tool","inputSchema":{"type":"object","properties":{"key":{"type":"string"}}}},{"name":"ticket.create","description":"Tier 1 reversible ticket creation","inputSchema":{"type":"object","properties":{"title":{"type":"string"}}}},{"name":"deploy.push","description":"Tier 2 mock production deployment push","inputSchema":{"type":"object","properties":{"version":{"type":"string"}}}},{"name":"admin.rotate_secret","description":"Tier 3 mock credential rotation action","inputSchema":{"type":"object","properties":{"service":{"type":"string"}}}}]}}


PASS: gateway path produced a response
