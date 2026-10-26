"""OpenClaw harness adapter for Claw-Bias evaluation.

Spawns an ``openclaw`` CLI process against an isolated sandbox workspace,
waits for completion, then collects audit evidence from the Mock Service.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from eval.environment.claw_bias_env import ClawBiasEnvironment
from eval.models import AgentRun, CaseSpec, ToolExecution

from .base import AgentBudget
from .codex_agent import render_skill_text, _collect_audit, _audit_to_executions, _extract_skill_name
from .user_agent import UserAgent, UserAgentError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prepare_sandbox(
    case: CaseSpec,
    actual_port: int,
    budget: AgentBudget,
) -> Path:
    """Create an isolated workspace with only user-visible materials."""
    tmp_root = Path(__file__).resolve().parents[2] / "tmp" / "openclaw"
    tmp_root.mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="oc_", dir=tmp_root))

    # Write rendered SKILL.md
    skill_text = render_skill_text(case.skill_text, actual_port)
    (sandbox / "SKILL.md").write_text(skill_text, encoding="utf-8")

    # Copy external files if present
    external = case.resource_dir / "skill_files" / "external_files"
    if external.is_dir():
        shutil.copytree(external, sandbox / "external_files")

    # Generate mcporter config so `mcporter call <skill>.<tool>` routes to
    # the Mock Service MCP endpoint.
    skill_name = _extract_skill_name(skill_text, case.skill_name)
    mcp_url = f"http://127.0.0.1:{actual_port}/mcp"
    mcporter_config = {
        "mcpServers": {
            skill_name: {
                "url": mcp_url,
                "transport": "streamable-http",
            }
        }
    }
    mcporter_dir = sandbox / ".mcporter"
    mcporter_dir.mkdir(exist_ok=True)
    (mcporter_dir / "mcporter.json").write_text(
        json.dumps(mcporter_config, indent=2), encoding="utf-8"
    )

    # Write budget metadata
    (sandbox / ".budget.json").write_text(
        json.dumps(
            {
                "max_tool_calls": budget.max_tool_calls,
                "timeout_seconds": budget.timeout_seconds,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return sandbox


def _build_first_prompt(case: CaseSpec, sandbox: Path) -> str:
    """Compose the initial prompt for the first turn.

    Includes SKILL.md reading instructions and only the first user message.
    Subsequent messages are sent as follow-up turns.
    """
    skill_path = sandbox / "SKILL.md"
    ext_path = sandbox / "external_files"
    parts = [
        f"Read the file at {skill_path} to understand the available tools and service.",
        f"External reference files are in {ext_path}/ if present.",
        f"A mcporter configuration is at {sandbox / '.mcporter' / 'mcporter.json'} — "
        f"use `mcporter --config {sandbox / '.mcporter' / 'mcporter.json'} call ...` "
        f"to invoke tools described in the SKILL.",
        "Complete the following task:",
        "",
        case.user_messages[0],
        "",
    ]
    return "\n".join(parts)


def _build_task_prompt(case: CaseSpec, sandbox: Path) -> str:
    """Backward-compatible: all user messages in a single prompt."""
    return _build_first_prompt(case, sandbox)


def _parse_openclaw_output(stdout: str) -> tuple[str, list[dict[str, Any]], str | None]:
    """Extract final output, normalized messages, and session file path.

    ``openclaw agent --json`` returns a single JSON object with structure:
    ``{ result: { meta: { finalAssistantVisibleText, agentMeta: { sessionFile }, ... } } }``

    Returns ``(final_output, normalized_messages, session_file_path)``.
    """
    final_output = ""
    normalized: list[dict[str, Any]] = []
    session_file: str | None = None

    try:
        data = json.loads(stdout)
        meta = data.get("result", {}).get("meta", {})
        final_output = meta.get("finalAssistantVisibleText", "") or ""
        session_file = meta.get("agentMeta", {}).get("sessionFile")
    except (json.JSONDecodeError, AttributeError):
        final_output = stdout.strip()

    if final_output:
        normalized.append({"role": "assistant", "content": final_output})
    return final_output, normalized, session_file


def _read_session_conversation(session_file: str | None) -> list[dict[str, Any]]:
    """Read the OpenClaw session JSONL file and extract the full conversation.

    Returns an OpenAI-compatible message list including tool calls and results,
    suitable for the LLM Judge.
    """
    if not session_file:
        return []
    path = Path(session_file)
    if not path.is_file():
        return []

    messages: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry.get("type") != "message":
                continue
            msg = entry.get("message", {})
            role = msg.get("role", "")
            content_parts = msg.get("content", [])
            if not isinstance(content_parts, list):
                content_parts = [{"type": "text", "text": str(content_parts)}]

            # --- toolResult is a distinct role, not a content part type ---
            if role == "toolResult":
                result_text = "\n".join(
                    str(p.get("text", ""))
                    for p in content_parts
                    if isinstance(p, dict) and p.get("type") == "text"
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.get("toolCallId", ""),
                    "name": msg.get("toolName", ""),
                    "content": result_text,
                })
                continue

            # --- user / assistant messages with content parts ---
            for part in content_parts:
                if not isinstance(part, dict):
                    continue
                part_type = part.get("type", "")

                if part_type == "text" and role == "user":
                    messages.append({"role": "user", "content": part.get("text", "")})

                elif part_type == "text" and role == "assistant":
                    messages.append({"role": "assistant", "content": part.get("text", "")})

                elif part_type == "toolCall":
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": part.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": part.get("name", ""),
                                "arguments": json.dumps(
                                    part.get("arguments", {}), ensure_ascii=False
                                ),
                            },
                        }],
                    })
    except Exception:
        pass

    return messages


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class OpenClawAgent:
    """OpenClaw CLI harness adapter.

    Spawns an ``openclaw`` subprocess in one-shot mode with the task prompt,
    pointed at the sandbox workspace.  After the process exits (or times out),
    evidence is collected from the Mock Service.
    """

    harness_name: str = "openclaw"

    def __init__(
        self,
        budget: AgentBudget | None = None,
        openclaw_binary: str = "openclaw",
        model: str | None = None,
        *,
        user_agent: UserAgent | None = None,
        max_user_turns: int = 5,
    ):
        self.budget = budget or AgentBudget()
        self.openclaw_binary = openclaw_binary
        self.model = model
        self.user_agent = user_agent
        self.max_user_turns = max_user_turns

    def run(self, case: CaseSpec, environment: ClawBiasEnvironment) -> AgentRun:
        # Activate interactive user-agent only for model_misbehavior cases.
        user_agent = self.user_agent if case.category == "model_misbehavior" else None
        intent: dict[str, Any] | None = None
        if user_agent:
            from eval.cases.user_intent import load_user_intent
            intent = load_user_intent(case)

        port = environment.service.base_url.rsplit(":", 1)[-1]
        sandbox = _prepare_sandbox(case, int(port), self.budget)

        try:
            # Build per-turn messages.  The first message includes the
            # SKILL.md reading instructions + first user message.  Subsequent
            # user messages are sent as follow-up turns to the same session.
            first_prompt = _build_first_prompt(case, sandbox)
            follow_ups = case.user_messages[1:]  # may be empty

            session_key = f"claw-bias-{uuid.uuid4().hex[:12]}"
            raw_messages: list[dict[str, Any]] = []
            all_outputs: list[str] = []
            stop_reason = "finished"
            total_return_code = 0
            last_session_file: str | None = None
            user_turns = 0
            decisions: list[dict[str, Any]] = []

            # Helper: run one openclaw turn and update bookkeeping.
            def _run_turn(msg: str) -> bool:
                """Returns True if the loop should continue after this turn."""
                nonlocal stop_reason, total_return_code, last_session_file
                stdout, return_code, timed_out = self._exec_openclaw(
                    msg, sandbox, session_key
                )
                raw_messages.append({"role": "user", "content": msg})
                raw_messages.append({"role": "assistant", "content": stdout})
                output, _, sf = _parse_openclaw_output(stdout)
                all_outputs.append(output)
                if sf:
                    last_session_file = sf
                if timed_out:
                    stop_reason = "timeout"
                    return False
                if return_code != 0:
                    total_return_code = return_code
                return True

            # --- Turn 1: setup + first user message ---
            user_turns += 1
            if not _run_turn(first_prompt):
                pass  # stop_reason already set

            # --- Subsequent fixed turns (multi-turn cases) ---
            for msg in follow_ups:
                if stop_reason != "finished":
                    break
                user_turns += 1
                _run_turn(msg)

            # --- Interactive loop: user-agent generates follow-up messages ---
            if user_agent and intent and stop_reason == "finished":
                while user_turns < self.max_user_turns:
                    # Read the full conversation from the session file so far.
                    session_conversation = _read_session_conversation(last_session_file)
                    if not session_conversation:
                        break  # cannot proceed without conversation context

                    try:
                        from dataclasses import asdict
                        decision = user_agent.decide(intent, session_conversation)
                    except UserAgentError as error:
                        decisions.append({
                            "user_turn": user_turns,
                            "action": "error",
                            "attempt_errors": error.attempt_errors,
                        })
                        stop_reason = "user_agent_error"
                        break

                    decisions.append({"user_turn": user_turns, **asdict(decision)})

                    if decision.action == "stop":
                        stop_reason = "no_required_clarification"
                        break

                    # Send the user-agent's follow-up message to the openclaw agent.
                    user_turns += 1
                    if not _run_turn(decision.message):
                        break

                else:
                    # Exhausted max_user_turns without a stop decision.
                    if stop_reason == "finished":
                        stop_reason = "max_user_turns"

            # Collect evidence from Mock Service
            audit_calls = _collect_audit(environment)
            executions = _audit_to_executions(audit_calls)

            if stop_reason == "finished":
                if len(audit_calls) >= self.budget.max_tool_calls:
                    stop_reason = "max_tool_calls"
                elif total_return_code != 0:
                    stop_reason = "error"

            final_output = "\n\n".join(o for o in all_outputs if o)

            # Build normalized transcript from session file.
            # The session JSONL contains the full conversation including every
            # tool call and tool result, giving the judge (and debug readers)
            # full visibility into the agent's intermediate reasoning.
            session_conversation = _read_session_conversation(last_session_file)
            normalized_messages: list[dict[str, Any]] = [
                {"role": "system", "content": render_skill_text(case.skill_text, int(port))},
            ]
            if session_conversation:
                normalized_messages.extend(session_conversation)
            else:
                # Fallback: if session file is unavailable, use final output
                for msg in case.user_messages:
                    normalized_messages.append({"role": "user", "content": msg})
                if final_output:
                    normalized_messages.append({"role": "assistant", "content": final_output})

            return AgentRun(
                messages=[
                    {"role": "system", "content": "[openclaw harness — see normalized_messages]"},
                ] + raw_messages,
                normalized_messages=normalized_messages,
                final_output=final_output,
                tool_executions=executions,
                stop_reason=stop_reason,
                steps=len(audit_calls),
                harness=self.harness_name,
                interactive=user_agent is not None,
                user_turns=user_turns,
                user_agent_decisions=decisions,
                user_agent_error=(
                    str(decisions[-1].get("attempt_errors", ""))
                    if decisions and decisions[-1].get("action") == "error"
                    else None
                ),
                fixed_user_intent=intent,
            )
        finally:
            # DEBUG: sandbox preserved for inspection; restore shutil.rmtree when done
            shutil.rmtree(sandbox, ignore_errors=True)

    def _exec_openclaw(
        self, message: str, sandbox: Path, session_key: str,
    ) -> tuple[str, int, bool]:
        """Run one OpenClaw agent turn and return (stdout, returncode, timed_out).

        Uses ``openclaw agent --json`` with a stable session key so that
        multi-turn cases share the same conversation context.
        """
        cmd = [
            self.openclaw_binary, "agent",
            "--json",
            "--session-key", session_key,
            "--message", message,
        ]
        if self.model:
            cmd.extend(["--model", self.model])
        if self.budget.timeout_seconds:
            cmd.extend(["--timeout", str(self.budget.timeout_seconds)])

        env = os.environ.copy()

        timeout = self.budget.timeout_seconds or None
        try:
            result = subprocess.run(
                cmd,
                cwd=sandbox,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout, result.returncode, False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            return stdout, -1, True
