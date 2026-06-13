import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

PORT = int(os.getenv("PORT", "3006"))
app = FastAPI(title="ProofRail Stop MCP Server")


def _rpc_error(req_id: Any, code: int, message: str, data: Dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message, "data": data or {}}})


@app.get("/health")
def health():
    return {"status": "healthy", "service": "stop-mcp", "mode": "emergency_stop"}


@app.post("/mcp/")
@app.post("/mcp")
async def mcp(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _rpc_error(body.get("id"), -32099, "ProofRail stop control active", {"reason": "emergency_stop", "proofrail_demo": "stop_mode"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
