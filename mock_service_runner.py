"""Run a generated mock service with test-only inspection endpoints."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import signal
import sys
from types import ModuleType
from typing import Any
from urllib.parse import urlencode, quote

from fastapi import BackgroundTasks, Request, Response
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn


# ---------------------------------------------------------------------------
# Shared audit log
# ---------------------------------------------------------------------------

_audit_calls: list[dict[str, Any]] = []

_INTERNAL_PATHS = {"/__snapshot", "/__shutdown", "/__audit", "/openapi.json", "/docs", "/redoc"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Record request/response pairs for every non-internal endpoint.

    The log is exposed via ``GET /__audit`` so that any harness (FC-loop,
    Codex, OpenClaw) can retrieve a uniform audit trail after the agent run.
    Servers that already expose their own ``/{family}/audit`` endpoint
    continue to work; this middleware provides a universal fallback.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        path = request.url.path

        # Skip internal/test endpoints and legacy per-family audit endpoints
        if path in _INTERNAL_PATHS or path.startswith("/__") or path.endswith("/audit"):
            return await call_next(request)
        # Skip MCP protocol endpoints
        if path == "/mcp" or path.endswith("/mcp"):
            return await call_next(request)

        # Capture request body
        request_body: Any = None
        try:
            raw = await request.body()
            if raw:
                request_body = json.loads(raw)
        except Exception:
            request_body = None

        response = await call_next(request)

        # Capture response body (read and re-wrap)
        body_bytes = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body_bytes += chunk.encode("utf-8")
            else:
                body_bytes += chunk

        response_body: Any = None
        try:
            response_body = json.loads(body_bytes)
        except Exception:
            response_body = body_bytes.decode("utf-8", errors="replace")

        _audit_calls.append({
            "endpoint": path,
            "method": request.method,
            "request_body": request_body if request_body is not None else dict(request.query_params),
            "response_body": response_body,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


# ---------------------------------------------------------------------------
# Server loading
# ---------------------------------------------------------------------------

def load_generated_server(server_script: Path) -> ModuleType:
    """Import a generated server module without executing its __main__ block."""
    server_script = server_script.resolve()
    sys.path.insert(0, str(server_script.parent))
    spec = importlib.util.spec_from_file_location("generated_mock_service", server_script)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load mock service from {server_script}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# OpenAPI → MCP tools/call bridge
# ---------------------------------------------------------------------------

def _build_openapi_route_table(
    app: Any,
) -> dict[str, dict[str, Any]]:
    """Scan the FastAPI app's OpenAPI schema and build a lookup table.

    Returns ``{operation_name: {"method": "GET"|"POST"|…, "path": "/…",
    "parameter_locations": {param: "query"|"path"|…}, "parameters": {…}}}``.

    This mirrors the logic in ``openapi_converter.py`` but runs inside the
    mock-service process so we don't need to import the eval package.
    """
    EXCLUDED = {"call", "audit", "reset", "__snapshot", "__shutdown"}
    HTTP_METHODS = ("get", "post", "put", "patch", "delete")

    document = app.openapi()
    routes: dict[str, dict[str, Any]] = {}

    def _resolve(value: Any) -> Any:
        if isinstance(value, list):
            return [_resolve(v) for v in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            cur: Any = document
            for part in str(value["$ref"]).removeprefix("#/").split("/"):
                cur = cur[part]
            resolved = copy.deepcopy(cur)
            resolved.update({k: v for k, v in value.items() if k != "$ref"})
            return _resolve(resolved)
        return {k: _resolve(v) for k, v in value.items()}

    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        name = path.rstrip("/").rsplit("/", 1)[-1]
        if name in EXCLUDED or "{" in name:
            continue
        for method in HTTP_METHODS:
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue
            param_locs: dict[str, str] = {}
            properties: dict[str, Any] = {}
            required: list[str] = []
            for raw_p in op.get("parameters", []):
                p = _resolve(raw_p)
                if not isinstance(p, dict) or not p.get("name"):
                    continue
                pname = str(p["name"])
                param_locs[pname] = str(p.get("in", "query"))
                pschema = _resolve(p.get("schema", {}))
                if p.get("description") and "description" not in pschema:
                    pschema["description"] = p["description"]
                properties[pname] = pschema
                if p.get("required"):
                    required.append(pname)
            content = op.get("requestBody", {}).get("content", {})
            media = content.get("application/json", {}) if isinstance(content, dict) else {}
            body_schema = _resolve(media.get("schema", {}))
            if isinstance(body_schema, dict):
                properties.update(body_schema.get("properties", {}))
                for rn in body_schema.get("required", []):
                    if rn not in required:
                        required.append(rn)

            input_schema: dict[str, Any] = {
                "type": "object",
                "properties": properties,
            }
            if required:
                input_schema["required"] = required

            routes[name] = {
                "method": method.upper(),
                "path": path,
                "parameter_locations": param_locs,
                "input_schema": input_schema,
                "description": op.get("description") or op.get("summary") or f"Call {name}",
            }
    return routes


def _mcp_tool_list(routes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Build MCP ``tools/list`` response items from the route table."""
    tools = []
    for name, info in routes.items():
        tools.append({
            "name": name,
            "description": info["description"],
            "inputSchema": info["input_schema"],
        })
    return tools


async def _mcp_tool_call(
    name: str,
    arguments: dict[str, Any],
    routes: dict[str, dict[str, Any]],
    base_url: str,
) -> Any:
    """Execute one MCP tools/call by proxying to the local REST endpoint.

    Uses ``httpx`` (async) to call back into the same server so that FastAPI
    middleware (including AuditMiddleware) sees a normal HTTP request.
    """
    import httpx  # imported here to keep the top-level slim

    route = routes.get(name)
    if route is None:
        return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

    method: str = route["method"]
    path: str = route["path"]
    locations: dict[str, str] = route.get("parameter_locations", {})
    remaining = dict(arguments)
    query: dict[str, Any] = {}

    for pname, loc in locations.items():
        if pname not in remaining:
            continue
        val = remaining.pop(pname)
        if loc == "path":
            path = path.replace(f"{{{pname}}}", quote(str(val), safe=""))
        elif loc == "query" and val is not None:
            query[pname] = val

    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"

    body = remaining if method not in ("GET", "DELETE") and remaining else None

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method, url,
            json=body,
            headers={"Content-Type": "application/json"} if body else {},
        )

    try:
        payload = resp.json()
    except Exception:
        payload = resp.text

    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
    }


# ---------------------------------------------------------------------------
# Test and MCP endpoints
# ---------------------------------------------------------------------------

def add_test_endpoints(server_module: ModuleType) -> None:
    """Expose state inspection, shutdown, audit, and MCP bridge endpoints."""
    app = getattr(server_module, "app", None)
    if app is None:
        raise AttributeError("Generated server does not define 'app'")

    # Pre-build route table once the OpenAPI schema is stable.
    # Lazy-init on first /mcp request because FastAPI finalises the schema late.
    _route_cache: dict[str, dict[str, dict[str, Any]]] = {}

    def _get_routes() -> dict[str, dict[str, Any]]:
        if "routes" not in _route_cache:
            _route_cache["routes"] = _build_openapi_route_table(app)
        return _route_cache["routes"]

    @app.get("/__snapshot", include_in_schema=False)
    def snapshot_environment() -> dict[str, object]:
        environment = getattr(server_module, "_env", None)
        if environment is None:
            return {"state": None}
        state = copy.deepcopy(vars(environment))
        return {"state": jsonable_encoder(state)}

    @app.post("/__shutdown", include_in_schema=False)
    def shutdown_service(background_tasks: BackgroundTasks) -> dict[str, str]:
        background_tasks.add_task(os.kill, os.getpid(), signal.SIGTERM)
        return {"status": "stopping"}

    @app.get("/__audit", include_in_schema=False)
    def get_audit_log() -> dict[str, Any]:
        """Universal audit log — works for both v1.0 and v2.0 mock services."""
        return {"calls": _audit_calls}

    @app.post("/__audit/reset", include_in_schema=False)
    def reset_audit_log() -> dict[str, str]:
        _audit_calls.clear()
        return {"status": "reset"}

    # -----------------------------------------------------------------------
    # MCP Streamable-HTTP bridge  (POST /mcp)
    #
    # Translates JSON-RPC 2.0 MCP messages into local REST calls so that
    # Codex / OpenClaw harnesses can use ``mcporter call`` against the same
    # mock service without any changes to the service itself.
    #
    # Supported methods:
    #   - initialize            → capabilities handshake
    #   - notifications/initialized → no-op ack
    #   - tools/list            → derived from OpenAPI schema
    #   - tools/call            → proxied to REST endpoint
    # -----------------------------------------------------------------------

    @app.post("/mcp", include_in_schema=False)
    async def mcp_endpoint(request: Request) -> Response:
        try:
            body = await request.json()
        except Exception:
            return _mcp_error_response(None, -32700, "Parse error")

        # Handle batch requests (JSON-RPC 2.0 allows arrays)
        if isinstance(body, list):
            results = []
            for item in body:
                results.append(await _handle_mcp_message(item, request, _get_routes))
            # Filter out None results (notifications don't get responses)
            results = [r for r in results if r is not None]
            if not results:
                return Response(status_code=202)
            return Response(
                content=json.dumps(results, ensure_ascii=False),
                media_type="application/json",
            )

        result = await _handle_mcp_message(body, request, _get_routes)
        if result is None:
            # Notification — no response body
            return Response(status_code=202)
        return Response(
            content=json.dumps(result, ensure_ascii=False),
            media_type="application/json",
        )


# ---------------------------------------------------------------------------
# MCP JSON-RPC helpers (used by the /mcp bridge inside add_test_endpoints)
# ---------------------------------------------------------------------------

def _mcp_error_response(
    request_id: Any, code: int, message: str
) -> Response:
    """Return a JSON-RPC 2.0 error response."""
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    return Response(
        content=json.dumps(body, ensure_ascii=False),
        media_type="application/json",
    )


async def _handle_mcp_message(
    msg: Any,
    request: Request,
    get_routes: Any,
) -> dict[str, Any] | None:
    """Process one JSON-RPC 2.0 MCP message and return a response dict.

    Returns ``None`` for notifications (no ``id`` field).
    """
    if not isinstance(msg, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}

    method = msg.get("method", "")
    params = msg.get("params") or {}
    request_id = msg.get("id")  # None for notifications

    # Notifications (no id) — acknowledge silently
    if request_id is None:
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "claw-bias-mock-service",
                    "version": "1.0.0",
                },
            },
        }

    if method == "tools/list":
        routes = get_routes()
        tools = _mcp_tool_list(routes)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}
        routes = get_routes()
        base_url = str(request.base_url).rstrip("/")
        result = await _mcp_tool_call(tool_name, arguments, routes, base_url)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path, required=True)
    args = parser.parse_args()

    server_module = load_generated_server(args.server)
    add_test_endpoints(server_module)

    app = getattr(server_module, "app")
    app.add_middleware(AuditMiddleware)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "39200")),
    )


if __name__ == "__main__":
    main()
