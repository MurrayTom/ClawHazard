from __future__ import annotations

import ast
import json
import re
from typing import Any


class ToolCallMappingError(ValueError):
    pass


_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", flags=re.DOTALL)


def _resolve_operation(name: Any, allowed_operations: set[str]) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ToolCallMappingError("tool call has no function name")
    raw_name = name.strip()
    candidates = [raw_name]
    if "." in raw_name:
        candidates.append(raw_name.rsplit(".", 1)[-1])
    if "__" in raw_name:
        candidates.append(raw_name.rsplit("__", 1)[-1])
    for candidate in candidates:
        if candidate in allowed_operations:
            return candidate
    raise ToolCallMappingError(f"unknown operation: {raw_name!r}")


def _parse_arguments(raw_arguments: Any) -> dict[str, Any]:
    if raw_arguments is None or raw_arguments == "":
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not isinstance(raw_arguments, str):
        raise ToolCallMappingError("function arguments must be an object or JSON string")

    candidate = raw_arguments.strip()
    fence = _CODE_FENCE.fullmatch(candidate)
    if fence:
        candidate = fence.group(1).strip()
    value: Any = candidate
    for _ in range(2):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
            continue
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
                continue
            except (SyntaxError, ValueError) as error:
                preview = candidate[:240]
                raise ToolCallMappingError(
                    f"invalid function arguments: {preview!r}"
                ) from error
    if not isinstance(value, dict):
        raise ToolCallMappingError("function arguments must decode to an object")
    return value


def map_function_call(
    tool_call: dict[str, Any], allowed_operations: set[str]
) -> tuple[str, dict[str, Any], str]:
    """Normalize an OpenAI-compatible function call for local execution."""
    function = tool_call.get("function")
    if not isinstance(function, dict):
        raise ToolCallMappingError("tool call is missing function")
    operation = _resolve_operation(function.get("name"), allowed_operations)
    params = _parse_arguments(function.get("arguments", "{}"))
    call_id = str(tool_call.get("id") or f"call_{operation}")
    return operation, params, call_id
