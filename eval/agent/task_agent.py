from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from eval.cases.user_intent import load_user_intent
from eval.environment.claw_bias_env import ClawBiasEnvironment
from eval.models import AgentRun, CaseSpec

from .base import AgentBudget
from .llm_client import ChatClient
from .prompt_builder import build_system_prompt
from .response_parser import normalize_assistant_message
from .user_agent import UserAgent, UserAgentError


class TaskAgent:
    """OpenAI function-calling loop (the original FC-loop harness)."""

    harness_name: str = "fc_loop"

    def __init__(
        self,
        client: ChatClient,
        max_steps: int = 12,
        skill_prompt_mode: str = "full",
        budget: AgentBudget | None = None,
        *,
        user_agent: UserAgent | None = None,
        max_user_turns: int = 5,
    ):
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self.client = client
        self.max_steps = max_steps
        self.skill_prompt_mode = skill_prompt_mode
        self.budget = budget or AgentBudget(max_tool_calls=max_steps)
        if max_user_turns < 1:
            raise ValueError("max_user_turns must be positive")
        self.user_agent = user_agent
        self.max_user_turns = max_user_turns

    def run(self, case: CaseSpec, environment: ClawBiasEnvironment) -> AgentRun:
        user_agent = self.user_agent if case.category == "model_misbehavior" else None
        intent = load_user_intent(case) if user_agent else None
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": build_system_prompt(
                    case.skill_text, self.skill_prompt_mode
                ),
            }
        ]
        executions = []
        final_outputs: list[str] = []
        steps = 0
        user_turns = 0
        decisions: list[dict[str, Any]] = []

        def finish(reason: str, error: str | None = None) -> AgentRun:
            return AgentRun(
                messages=messages,
                final_output="\n".join(final_outputs),
                tool_executions=executions,
                stop_reason=reason,
                steps=steps,
                harness=self.harness_name,
                interactive=user_agent is not None,
                user_turns=user_turns,
                user_agent_decisions=decisions,
                user_agent_error=error,
                fixed_user_intent=intent,
            )

        # Appending follow-ups here does not alter the case's original messages.
        pending = list(case.user_messages)
        for user_content in pending:
            messages.append({"role": "user", "content": user_content})
            user_turns += 1
            turn_finished = False
            while not turn_finished and steps < self.max_steps:
                raw_message = self.client.complete(messages, environment.tools)
                assistant = normalize_assistant_message(raw_message)
                messages.append(assistant)
                steps += 1

                tool_calls = assistant.get("tool_calls", [])
                if tool_calls:
                    for tool_call in tool_calls:
                        if not isinstance(tool_call, dict):
                            continue
                        execution = environment.execute(tool_call)
                        executions.append(execution)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": execution.tool_call_id,
                                "name": execution.operation,
                                "content": json.dumps(
                                    execution.response, ensure_ascii=False
                                ),
                            }
                        )
                    continue

                output = str(assistant.get("content") or "")
                final_outputs.append(output)
                turn_finished = True

            if steps >= self.max_steps and not turn_finished:
                return finish("max_steps")
            if user_agent:
                # Never ask for a follow-up that the task agent cannot consume.
                if steps >= self.max_steps:
                    return finish("max_steps")
                if user_turns >= self.max_user_turns:
                    return finish("max_user_turns")
                try:
                    decision = user_agent.decide(intent, messages)
                except UserAgentError as error:
                    decisions.append(
                        {
                            "user_turn": user_turns,
                            "action": "error",
                            "attempt_errors": error.attempt_errors,
                        }
                    )
                    return finish("user_agent_error", str(error))
                decisions.append({"user_turn": user_turns, **asdict(decision)})
                if decision.action == "stop":
                    return finish("no_required_clarification")
                pending.append(decision.message)

        return finish("finished")


def serialize_agent_run(run: AgentRun) -> dict[str, Any]:
    data: dict[str, Any] = {
        "messages": run.messages,
        "final_output": run.final_output,
        "tool_executions": [asdict(item) for item in run.tool_executions],
        "stop_reason": run.stop_reason,
        "steps": run.steps,
        "harness": run.harness,
    }
    if run.normalized_messages is not None:
        data["normalized_messages"] = run.normalized_messages
    if run.diagnostics:
        data["diagnostics"] = run.diagnostics
    if run.interactive:
        data["interaction"] = {
            "mode": "interactive",
            "user_turns": run.user_turns,
            "decisions": run.user_agent_decisions,
            "error": run.user_agent_error,
            "fixed_user_intent": run.fixed_user_intent,
        }
    return data
