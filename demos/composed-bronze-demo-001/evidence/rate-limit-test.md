# Rate-limit / circuit-breaker test

Configured desired behavior: 5 requests/minute local request rate limit.
This test sends 8 quick requests and records whether the gateway returns any throttle response.
[1] data: {"jsonrpc":"2.0","id":"rate-1","result":{"content":[{"type":"text","text":"mock actuator executed demo.read"}],"isError":false}}
[2] data: {"jsonrpc":"2.0","id":"rate-2","result":{"content":[{"type":"text","text":"mock actuator executed demo.read"}],"isError":false}}
[3] rate limit exceeded
[4] 
[5] 
[6] 
[7] 
[8] 
PASS: rate-limit/circuit-breaker behavior observed
