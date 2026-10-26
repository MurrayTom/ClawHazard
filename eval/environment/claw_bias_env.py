from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from mock_service_utils import request_json

from eval.models import EnvironmentRecord, ToolExecution

from .openapi_converter import openapi_operations
from .service_manager import ServiceManager
from .tool_call_mapper import ToolCallMappingError, map_function_call


class ClawBiasEnvironment:
    def __init__(
        self,
        resource_dir: Path,
        skill_name: str,
        project_root: Path,
        start_timeout: float = 15.0,
    ):
        self.service = ServiceManager(
            resource_dir, skill_name, project_root, start_timeout
        )
        self.skill_name = skill_name
        self.family = skill_name
        self.tools: list[dict[str, Any]] = []
        self.routes: dict[str, dict[str, Any]] = {}
        self.allowed_operations: set[str] = set()
        self.audit_calls: list[dict[str, Any]] = []

    def start(self) -> "ClawBiasEnvironment":
        self.service.start()
        document = self.service.openapi()
        operations = openapi_operations(document)
        self.tools = [item["tool"] for item in operations.values()]
        self.routes = {
            name: item["route"] for name, item in operations.items()
        }
        self.allowed_operations = set(self.routes)
        if not self.tools:
            self.service.stop_process()
            raise RuntimeError(f"No callable operations found for {self.skill_name}")
        return self

    def _request_operation(self, operation: str, params: dict[str, Any]) -> Any:
        route = self.routes[operation]
        method = str(route["method"])
        path = str(route["path"])
        locations = route.get("parameter_locations", {})
        remaining = dict(params)
        query_params: dict[str, Any] = {}

        for name, location in locations.items():
            if name not in remaining:
                continue
            value = remaining.pop(name)
            if location == "path":
                path = path.replace(f"{{{name}}}", quote(str(value), safe=""))
            elif location == "query" and value is not None:
                query_params[name] = value

        url = f"{self.service.base_url}{path}"
        if query_params:
            url = f"{url}?{urlencode(query_params, doseq=True)}"
        payload = remaining if method not in {"GET", "DELETE"} and remaining else None
        return request_json(url, method=method, payload=payload)

    def execute(self, tool_call: dict[str, Any]) -> ToolExecution:
        operation = ""
        params: dict[str, Any] = {}
        call_id = str(tool_call.get("id") or "invalid_call")
        try:
            operation, params, call_id = map_function_call(
                tool_call, self.allowed_operations
            )
            response = self._request_operation(operation, params)
            self.audit_calls.append(
                {
                    "endpoint": self.routes[operation]["path"],
                    "method": self.routes[operation]["method"],
                    "request_body": {"operation": operation, "params": params},
                    "response_body": response,
                }
            )
            return ToolExecution(call_id, operation, params, response)
        except ToolCallMappingError as error:
            function = tool_call.get("function", {})
            return ToolExecution(
                call_id,
                str(function.get("name", "")),
                params,
                {"success": False, "error": str(error)},
                str(error),
            )
        except Exception as error:
            response = {"success": False, "error": str(error)}
            if operation:
                self.audit_calls.append(
                    {
                        "endpoint": self.routes[operation]["path"],
                        "method": self.routes[operation]["method"],
                        "request_body": {"operation": operation, "params": params},
                        "response_body": response,
                    }
                )
            return ToolExecution(call_id, operation, params, response, str(error))

    def record(self) -> EnvironmentRecord:
        # Merge local audit (populated by FC-loop's self.execute) with
        # service-side audit (populated by AuditMiddleware when Codex/OpenClaw
        # call through the MCP bridge).  Deduplicate by using service-side
        # audit when local is empty, otherwise prefer local.
        if self.audit_calls:
            merged = list(self.audit_calls)
        else:
            merged = self.service.audit(self.family)
        return EnvironmentRecord(
            base_url=self.service.base_url,
            state_before=self.service.state_before,
            state_after=self.service.snapshot(),
            audit_calls=merged,
        )

    def stop(self) -> None:
        self.service.stop_process()

    def __enter__(self) -> "ClawBiasEnvironment":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.stop()
