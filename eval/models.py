from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    category: str
    skill_source: str
    skill_name: str
    task_dir: Path
    resource_dir: Path
    prompt: str
    user_messages: list[str]
    skill_text: str
    metadata: JsonObject

    def public_dict(self) -> JsonObject:
        data = asdict(self)
        data["task_dir"] = str(self.task_dir)
        data["resource_dir"] = str(self.resource_dir)
        data.pop("skill_text", None)
        return data


@dataclass
class ToolExecution:
    tool_call_id: str
    operation: str
    params: JsonObject
    response: Any
    error: str | None = None


@dataclass
class AgentRun:
    messages: list[JsonObject]
    final_output: str
    tool_executions: list[ToolExecution] = field(default_factory=list)
    stop_reason: str = "finished"
    steps: int = 0
    harness: str = "fc_loop"
    normalized_messages: list[JsonObject] | None = None
    # Interactive mode fields (FC-loop only)
    interactive: bool = False
    user_turns: int = 0
    user_agent_decisions: list[JsonObject] = field(default_factory=list)
    user_agent_error: str | None = None
    fixed_user_intent: JsonObject | None = None
    diagnostics: JsonObject = field(default_factory=dict)

    @property
    def judge_messages(self) -> list[JsonObject]:
        """Messages suitable for the LLM judge.

        Returns *normalized_messages* when available (Codex / OpenClaw adapters
        populate this with an OpenAI-compatible transcript), otherwise falls
        back to *messages* (FC-loop already uses OpenAI format).
        """
        return self.normalized_messages if self.normalized_messages is not None else self.messages


@dataclass
class EnvironmentRecord:
    base_url: str
    state_before: JsonObject
    state_after: JsonObject
    audit_calls: list[JsonObject]


@dataclass
class CaseResult:
    case: JsonObject
    agent: JsonObject
    environment: JsonObject
    safety: JsonObject
    utility: JsonObject
    error: str | None = None

    def as_dict(self) -> JsonObject:
        return asdict(self)
