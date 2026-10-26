"""Private evaluation evidence; never supplied to the simulated user."""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from eval.models import AgentRun, EnvironmentRecord


def business_state(state: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in state.items() if key != "init_config"}


def _resolve(value: Any, path: list[Any]) -> tuple[bool, Any]:
    try:
        for key in path:
            value = value[int(key)] if isinstance(value, list) else value[key]
        return True, value
    except (KeyError, IndexError, TypeError, ValueError):
        return False, None


def state_check_evidence(
    run: AgentRun, environment: EnvironmentRecord
) -> list[dict[str, Any]]:
    before = business_state(environment.state_before)
    after = business_state(environment.state_after)
    checks = []
    for check in run.fixed_user_intent["expected_result"]["state_checks"]:
        before_exists, before_value = _resolve(before, check["path"])
        after_exists, after_value = _resolve(after, check["path"])
        operator = check["operator"]
        if operator == "equals":
            satisfied = after_exists and after_value == check["value"]
        elif operator == "absent":
            satisfied = not after_exists
        elif operator == "unchanged":
            satisfied = (before_exists, before_value) == (after_exists, after_value)
        else:
            raise ValueError(f"Unknown fixed-intent state operator: {operator}")
        checks.append(
            {
                **check,
                "satisfied": satisfied,
                "before_exists": before_exists,
                "before": before_value,
                "after_exists": after_exists,
                "after": after_value,
            }
        )
    return checks


def numbered_transcript(run: AgentRun) -> list[dict[str, Any]]:
    transcript = []
    user_turn = 0
    for message in run.messages:
        if message.get("role") == "system":
            continue
        if message.get("role") == "user":
            user_turn += 1
        transcript.append(
            {
                "sequence": len(transcript) + 1,
                "user_turn": user_turn,
                **deepcopy(
                    {
                        key: value
                        for key, value in message.items()
                        if key != "reasoning_content"
                    }
                ),
            }
        )
    return transcript


def ordered_tool_executions(run: AgentRun) -> list[dict[str, Any]]:
    """Attach execution order to dialogue positions, without guessing consent.

    The task loop executes batch calls serially. Positional pairing, with IDs
    checked, preserves repeated IDs and includes failures absent from audit logs.
    """
    transcript = numbered_transcript(run)
    declarations = []
    results = defaultdict(deque)
    latest_user_sequence = None
    for message in transcript:
        if message["role"] == "user":
            latest_user_sequence = message["sequence"]
        elif message["role"] == "assistant":
            for batch_index, call in enumerate(message.get("tool_calls") or [], 1):
                if isinstance(call, dict):
                    declarations.append(
                        {
                            "tool_call_id": call.get("id"),
                            "request_sequence": message["sequence"],
                            "user_turn": message["user_turn"],
                            "batch_index": batch_index,
                            "last_user_sequence_before_call": latest_user_sequence,
                            "requested_arguments": (call.get("function") or {}).get(
                                "arguments"
                            ),
                        }
                    )
        elif message["role"] == "tool":
            results[message.get("tool_call_id")].append(message["sequence"])

    ordered = []
    for index, execution in enumerate(run.tool_executions):
        declaration = declarations[index] if index < len(declarations) else None
        aligned = (
            declaration is not None
            and declaration["tool_call_id"] == execution.tool_call_id
        )
        result_sequences = results[execution.tool_call_id]
        result_sequence = result_sequences.popleft() if result_sequences else None
        ordered.append(
            {
                **asdict(execution),
                "execution_order": index + 1,
                "request_sequence": (
                    declaration["request_sequence"] if aligned else None
                ),
                "user_turn": declaration["user_turn"] if aligned else None,
                "batch_index": declaration["batch_index"] if aligned else None,
                "last_user_sequence_before_call": (
                    declaration["last_user_sequence_before_call"] if aligned else None
                ),
                "requested_arguments": (
                    declaration["requested_arguments"] if aligned else None
                ),
                "result_sequence": result_sequence,
                "dialogue_alignment_verified": aligned
                and result_sequence is not None
                and result_sequence > declaration["request_sequence"],
            }
        )
    return ordered
