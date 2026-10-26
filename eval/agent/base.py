"""Agent harness protocol and budget definitions.

Every harness adapter (FC-loop, Codex, OpenClaw) implements :class:`AgentHarness`
so ``run_main.py`` can dispatch to any of them with a single interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from eval.environment.claw_bias_env import ClawBiasEnvironment
from eval.models import AgentRun, CaseSpec


@dataclass(frozen=True)
class AgentBudget:
    """Unified resource budget shared by all harnesses.

    *max_tool_calls* caps the number of mock-service operations the agent may
    invoke.  *max_llm_turns* caps the total number of LLM round-trips (only
    meaningful for the FC-loop; external harnesses rely on *timeout_seconds*).
    *timeout_seconds* is a hard wall-clock limit; 0 means no timeout.
    """

    max_tool_calls: int = 12
    max_llm_turns: int = 20
    timeout_seconds: int = 300


class AgentHarness(Protocol):
    """Minimal interface that every harness adapter must satisfy."""

    harness_name: str

    def run(self, case: CaseSpec, environment: ClawBiasEnvironment) -> AgentRun:
        """Execute the case and return a completed :class:`AgentRun`."""
        ...
