from __future__ import annotations

from copy import deepcopy
from typing import Any


EXCLUDED_OPERATIONS = {"call", "audit", "reset", "__snapshot", "__shutdown"}
HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def _resolve_refs(value: Any, document: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_resolve_refs(item, document) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        current: Any = document
        for part in str(value["$ref"]).removeprefix("#/").split("/"):
            current = current[part]
        resolved = deepcopy(current)
        resolved.update({key: val for key, val in value.items() if key != "$ref"})
        return _resolve_refs(resolved, document)
    return {key: _resolve_refs(val, document) for key, val in value.items()}


def _operation_schema(
    operation_spec: dict[str, Any], document: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, str]]:
    schema: dict[str, Any] = {"type": "object", "properties": {}}
    required: list[str] = []
    parameter_locations: dict[str, str] = {}

    for raw_parameter in operation_spec.get("parameters", []):
        parameter = _resolve_refs(raw_parameter, document)
        if not isinstance(parameter, dict) or not parameter.get("name"):
            continue
        name = str(parameter["name"])
        property_schema = _resolve_refs(parameter.get("schema", {}), document)
        if not isinstance(property_schema, dict):
            property_schema = {}
        if parameter.get("description") and "description" not in property_schema:
            property_schema["description"] = parameter["description"]
        schema["properties"][name] = property_schema
        parameter_locations[name] = str(parameter.get("in", "query"))
        if parameter.get("required"):
            required.append(name)

    content = operation_spec.get("requestBody", {}).get("content", {})
    media = content.get("application/json", {}) if isinstance(content, dict) else {}
    body_schema = _resolve_refs(media.get("schema", {}), document)
    if isinstance(body_schema, dict):
        properties = body_schema.get("properties", {})
        if isinstance(properties, dict):
            schema["properties"].update(properties)
        for name in body_schema.get("required", []):
            if name not in required:
                required.append(name)
        for key in ("additionalProperties", "minProperties", "maxProperties"):
            if key in body_schema:
                schema[key] = body_schema[key]

    if required:
        schema["required"] = required
    return schema, parameter_locations


def openapi_operations(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build function schemas and HTTP routes from an OpenAPI document."""
    operations: dict[str, dict[str, Any]] = {}
    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        name = path.rstrip("/").rsplit("/", 1)[-1]
        if name in EXCLUDED_OPERATIONS or "{" in name:
            continue
        for method in HTTP_METHODS:
            operation_spec = path_item.get(method)
            if not isinstance(operation_spec, dict):
                continue
            if name in operations:
                raise ValueError(f"Duplicate OpenAPI operation name: {name}")
            parameters, parameter_locations = _operation_schema(
                operation_spec, document
            )
            operations[name] = {
                "tool": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": operation_spec.get("description")
                        or operation_spec.get("summary")
                        or f"Call {name}",
                        "parameters": parameters,
                    },
                },
                "route": {
                    "method": method.upper(),
                    "path": path,
                    "parameter_locations": parameter_locations,
                },
            }
    return operations


def openapi_to_tools(document: dict[str, Any]) -> list[dict[str, Any]]:
    return [item["tool"] for item in openapi_operations(document).values()]
