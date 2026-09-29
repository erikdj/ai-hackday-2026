"""Minimal MCP Streamable HTTP (JSON-RPC) for lineage tools. No mcp package."""

import json
import logging

from hallway.dashboard import queries

log = logging.getLogger(__name__)

_KNOWN_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
_DEFAULT_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "who_saw_identifiers",
        "description": (
            "Which Safe Scribe agents accessed patient identifiers "
            "(name, DOB, MRN, phone, address) on any case. "
            "Returns agent names from the Neo4j lineage graph."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_followups_by_owner",
        "description": (
            "Open follow-up commitments grouped by owner; "
            "'unresolved' bucket = no human owner. Optional owner filter."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"owner": {"type": "string"}},
        },
    },
    {
        "name": "patient_history",
        "description": "Prior encounters for a pseudonymous patient id (never a real identifier).",
        "inputSchema": {
            "type": "object",
            "properties": {"pseudo_id": {"type": "string"}},
            "required": ["pseudo_id"],
        },
    },
]


def _envelope(req_id, *, result=None, error=None):
    body = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return body


def _rpc_error(req_id, code, message):
    return _envelope(req_id, error={"code": code, "message": message})


def _tool_payload(data, *, is_error=False):
    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)
    structured = data if isinstance(data, dict) else {"message": text}
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
        "isError": is_error,
    }


def _followups(arguments):
    data = queries.open_followups()
    owner = arguments.get("owner") if isinstance(arguments, dict) else None
    if owner is None or owner == "":
        return data
    wanted = str(owner).casefold()
    for key, value in (data.get("by_owner") or {}).items():
        if str(key).casefold() == wanted:
            return {key: value}
    return {}


def _dispatch_tool(name, arguments):
    if name == "who_saw_identifiers":
        data = queries.who_saw_identifiers()
        return {
            k: v
            for k, v in data.items()
            if k not in ("expected_on_demo", "matches_expected")
        }
    if name == "open_followups_by_owner":
        return _followups(arguments)
    if name == "patient_history":
        pseudo_id = arguments.get("pseudo_id") if isinstance(arguments, dict) else None
        if not isinstance(pseudo_id, str) or not pseudo_id:
            raise ValueError("pseudo_id is required")
        return queries.patient_history(pseudo_id)
    return None


def _call_tool(params):
    if not isinstance(params, dict) or not isinstance(params.get("name"), str):
        return _tool_payload("tools/call requires params.name", is_error=True)
    name = params["name"]
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _tool_payload("params.arguments must be an object", is_error=True)
    try:
        result = _dispatch_tool(name, arguments)
    except Exception as exc:
        log.exception("MCP tool %s failed", name)
        return _tool_payload(str(exc), is_error=True)
    if result is None:
        return _tool_payload(f"Unknown tool: {name}", is_error=True)
    return _tool_payload(result, is_error=False)


def _initialize(params):
    version = _DEFAULT_VERSION
    if isinstance(params, dict) and params.get("protocolVersion") in _KNOWN_VERSIONS:
        version = params["protocolVersion"]
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "safe-scribe-lineage", "version": "0.1.0"},
    }


def handle(message: dict) -> dict | None:
    """JSON-RPC 2.0 dispatcher. Notifications return None."""
    if not isinstance(message, dict):
        return _rpc_error(None, -32600, "Invalid Request")
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return _rpc_error(message.get("id"), -32600, "Invalid Request")
    if "id" not in message:
        return None
    req_id = message["id"]
    method = message["method"]
    params = message.get("params") if message.get("params") is not None else {}
    if method == "initialize":
        return _envelope(req_id, result=_initialize(params))
    if method == "ping":
        return _envelope(req_id, result={})
    if method == "tools/list":
        return _envelope(req_id, result={"tools": TOOLS})
    if method == "tools/call":
        return _envelope(req_id, result=_call_tool(params))
    return _rpc_error(req_id, -32601, "Method not found")


def mount(app):
    """Register POST/GET /mcp and GET /mcp/health. FastAPI imported lazily."""
    from fastapi import Request
    from fastapi.concurrency import run_in_threadpool
    from fastapi.responses import JSONResponse, Response

    @app.post("/mcp")
    async def mcp_post(request: Request):
        try:
            payload = json.loads((await request.body()).decode() or "null")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JSONResponse(
                _rpc_error(None, -32700, "Parse error"),
                status_code=400,
            )
        if isinstance(payload, list):
            results = await run_in_threadpool(
                lambda: [item for msg in payload if (item := handle(msg)) is not None]
            )
            if not results:
                return Response(status_code=202)
            return JSONResponse(results)
        if isinstance(payload, dict):
            result = await run_in_threadpool(handle, payload)
            if result is None:
                return Response(status_code=202)
            return JSONResponse(result)
        return JSONResponse(_rpc_error(None, -32600, "Invalid Request"), status_code=400)

    @app.get("/mcp")
    def mcp_get():
        return JSONResponse(
            {"error": "SSE stream not supported; use POST"},
            status_code=405,
        )

    @app.get("/mcp/health")
    def mcp_health():
        return {"ok": True, "tools": [tool["name"] for tool in TOOLS]}
