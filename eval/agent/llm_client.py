from __future__ import annotations

from typing import Any, Protocol

from openai import OpenAI, OpenAIError


class ChatClient(Protocol):
    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]: ...


class OpenAICompatibleClient:
    """OpenAI-compatible streaming client with ToolHazard-style FC assembly."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 120.0,
        max_retries: int = 2,
    ):
        self.model = model
        base = base_url.rstrip("/")
        endpoint_suffix = "/chat/completions"
        if base.endswith(endpoint_suffix):
            base = base[: -len(endpoint_suffix)]
        self.client = OpenAI(
            api_key=api_key,
            base_url=base,
            timeout=timeout,
            max_retries=max_retries,
        )

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **({"tools": tools, "tool_choice": "auto"} if tools else {}),
            )
            content_parts: list[str] = []
            reasoning_parts: list[str] = []
            tool_calls: dict[int, dict[str, Any]] = {}

            for chunk in completion:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if delta.content:
                    content_parts.append(delta.content)
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    reasoning_parts.append(str(reasoning))

                for fallback_index, fragment in enumerate(delta.tool_calls or []):
                    index = fragment.index
                    if index is None:
                        index = fallback_index
                    call = tool_calls.setdefault(
                        index,
                        {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )
                    if fragment.id:
                        call["id"] = fragment.id
                    if fragment.type:
                        call["type"] = fragment.type
                    if fragment.function:
                        if fragment.function.name:
                            call["function"]["name"] += fragment.function.name
                        if fragment.function.arguments:
                            call["function"]["arguments"] += fragment.function.arguments
        except OpenAIError as error:
            raise RuntimeError(f"LLM request failed: {error}") from error

        result: dict[str, Any] = {
            "role": "assistant",
            "content": "".join(content_parts),
            "tool_calls": [tool_calls[index] for index in sorted(tool_calls)],
        }
        if reasoning_parts:
            result["reasoning_content"] = "".join(reasoning_parts)
        if not result["content"] and not result["tool_calls"] and not reasoning_parts:
            raise RuntimeError("LLM response contained no content or tool calls")
        return result
