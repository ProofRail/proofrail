import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
import uvicorn

PORT = int(os.getenv("PORT", "3005"))
SECRET_FILE = os.getenv("MCP_SERVER_API_KEY_FILE", "/run/secrets/upstream_mcp_api_key")

TOOLS = [
    {
        "name": "demo.read",
        "description": "Tier 0 read-only demo tool",
        "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}},
    },
    {
        "name": "ticket.create",
        "description": "Tier 1 reversible ticket creation",
        "inputSchema": {"type": "object", "properties": {"title": {"type": "string"}}},
    },
    {
        "name": "deploy.push",
        "description": "Tier 2 mock production deployment push",
        "inputSchema": {"type": "object", "properties": {"version": {"type": "string"}}},
    },
    {
        "name": "admin.rotate_secret",
        "description": "Tier 3 mock credential rotation action",
        "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}},
    },
]

app = FastAPI(title="ProofRail Mock MCP Actuator Server")


def _expected_key() -> str:
    try:
        return Path(SECRET_FILE).read_text().strip()
    except Exception:
        return os.getenv("UPSTREAM_MCP_API_KEY", "")


def _params_hash(params: Dict[str, Any]) -> str:
    encoded = json.dumps(params or {}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _rpc_result(req_id: Any, result: Dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def _rpc_error(req_id: Any, code: int, message: str, data: Dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message, "data": data or {}}})


@app.get("/health")
def health():
    return {"status": "healthy", "service": "mock-mcp", "tools": len(TOOLS)}


@app.post("/mcp/")
@app.post("/mcp")
async def mcp(request: Request, x_upstream_api_key: str | None = Header(default=None)):
    expected = _expected_key()
    if expected and x_upstream_api_key != expected:
        return _rpc_error(None, -32040, "unauthorized upstream actuator access", {"proofrail_demo": "missing_or_wrong_upstream_key"})

    started = time.perf_counter()
    body = await request.json()
    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params") or {}

    if method == "initialize":
        return _rpc_result(req_id, {"protocolVersion": "2025-11-25", "serverInfo": {"name": "proofrail-mock-mcp", "version": "0.1.0"}, "capabilities": {"tools": {}}})

    if method == "ping":
        return _rpc_result(req_id, {})

    if method == "tools/list":
        return _rpc_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        allowed = {t["name"] for t in TOOLS}
        if tool_name not in allowed:
            return _rpc_error(req_id, -32602, "unknown tool", {"tool": tool_name})
        elapsed_ms = (time.perf_counter() - started) * 1000
        return _rpc_result(req_id, {
            "content": [{"type": "text", "text": f"mock actuator executed {tool_name}"}],
            "isError": False,
            "proofrail_mock": {
                "tool": tool_name,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "parameters_hash": _params_hash(tool_args),
                "upstream_latency_ms": round(elapsed_ms, 3),
            }
        })

    return _rpc_error(req_id, -32601, "method not found", {"method": method})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
