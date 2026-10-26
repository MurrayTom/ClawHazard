from __future__ import annotations

import ast
import json
import re
from typing import Any


_TOOL_CALL_TAG = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", flags=re.IGNORECASE | re.DOTALL
)
_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", flags=re.DOTALL)


def text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return "" if content is None else str(content)


def _as_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json", exclude_none=True)
        return dumped if isinstance(dumped, dict) else None
    return None


def _decode_explicit_call(text: str) -> Any:
    candidate = text.strip()
    fence = _CODE_FENCE.fullmatch(candidate)
    if fence:
        candidate = fence.group(1).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(candidate)
        except (SyntaxError, ValueError):
            return None


def _normalize_tool_call(value: Any, index: int) -> dict[str, Any] | None:
    call = _as_dict(value)
    if not call:
        return None
    function = _as_dict(call.get("function"))
    if function is None and call.get("name"):
        function = {
            "name": call.get("name"),
            "arguments": call.get("arguments", {}),
        }
    if not function or not function.get("name"):
        return None
    arguments = function.get("arguments", "{}")
    if not isinstance(arguments, str):
        arguments = json.dumps(arguments, ensure_ascii=False)
    function_name = str(function["name"])
    return {
        "id": str(call.get("id") or f"call_{index}_{function_name}"),
        "type": "function",
        "function": {
            "name": function_name,
            "arguments": arguments or "{}",
        },
    }


def _calls_from_explicit_value(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        values = value
    elif isinstance(value, dict) and isinstance(value.get("tool_calls"), list):
        values = value["tool_calls"]
    else:
        values = [value]
    calls = []
    for index, item in enumerate(values):
        call = _normalize_tool_call(item, index)
        if call:
            calls.append(call)
    return calls


def extract_content_tool_calls(content: str) -> tuple[str, list[dict[str, Any]]]:
    tagged = _TOOL_CALL_TAG.findall(content)
    if tagged:
        calls: list[dict[str, Any]] = []
        for payload in tagged:
            calls.extend(_calls_from_explicit_value(_decode_explicit_call(payload)))
        return _TOOL_CALL_TAG.sub("", content).strip(), calls

    stripped = content.strip()
    if stripped.startswith(("{", "[", "```")):
        value = _decode_explicit_call(stripped)
        calls = _calls_from_explicit_value(value)
        if calls:
            return "", calls
    return content, []


def normalize_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    content = text_content(message.get("content"))
    raw_tool_calls = message.get("tool_calls") or []
    if not raw_tool_calls and message.get("function_call"):
        raw_tool_calls = [message["function_call"]]

    tool_calls = []
    if isinstance(raw_tool_calls, (list, tuple)):
        for index, item in enumerate(raw_tool_calls):
            call = _normalize_tool_call(item, index)
            if call:
                tool_calls.append(call)
    if not tool_calls and content:
        content, tool_calls = extract_content_tool_calls(content)

    normalized: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        normalized["tool_calls"] = tool_calls
    return normalized
