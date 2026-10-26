"""Codex CLI harness adapter for Claw-Bias evaluation.

Launches a Codex CLI process against an isolated sandbox workspace, waits for
completion, then collects audit evidence from the Mock Service.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from eval.environment.claw_bias_env import ClawBiasEnvironment
from eval.models import AgentRun, CaseSpec, ToolExecution

from .base import AgentBudget
from .user_agent import UserAgent, UserAgentError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_PORT = "http://127.0.0.1:39200"
_PORT_PATTERN = re.compile(r"http://127\.0\.0\.1:\d+")


_SKILL_NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)


def render_skill_text(skill_text: str, actual_port: int) -> str:
    """Replace the template port placeholder with the real Mock Service port."""
    actual_url = f"http://127.0.0.1:{actual_port}"
    # Replace both the full URL pattern and the hardcoded default
    rendered = skill_text.replace(_DEFAULT_PORT, actual_url)
    return _PORT_PATTERN.sub(actual_url, rendered)


def _extract_skill_name(skill_text: str, fallback: str) -> str:
    """Extract the skill name from SKILL.md YAML frontmatter."""
    match = _SKILL_NAME_RE.search(skill_text)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return fallback


def _prepare_sandbox(
    case: CaseSpec,
    actual_port: int,
    budget: AgentBudget,
) -> Path:
    """Create an isolated workspace with only user-visible materials."""
    tmp_root = Path(__file__).resolve().parents[2] / "tmp" / "codex"
    tmp_root.mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="cx_", dir=tmp_root))

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
    mcporter_dir = sandbox / "config"
    mcporter_dir.mkdir(exist_ok=True)
    (mcporter_dir / "mcporter.json").write_text(
        json.dumps(mcporter_config, indent=2), encoding="utf-8"
    )

    return sandbox


def _build_first_prompt(case: CaseSpec, sandbox: Path) -> str:
    """Compose the initial prompt for the first turn.

    Mirrors the OpenClaw harness prompt style: give explicit absolute paths
    so the agent doesn't waste turns discovering files, and tell it exactly
    how to invoke tools via mcporter.  Only includes the first user message;
    subsequent messages are sent as follow-up turns via ``codex exec resume``.
    """
    skill_path = sandbox / "SKILL.md"
    ext_path = sandbox / "external_files"
    parts = [
        f"Read the file at {skill_path} to understand the available tools and service.",
        f"External reference files are in {ext_path}/ if present.",
        "Use `mcporter call <service>.<tool> --args '<json>'` to invoke tools described in the SKILL.",
        "Complete the following task:",
        "",
        case.user_messages[0],
        "",
    ]
    return "\n".join(parts)


def _build_task_prompt(case: CaseSpec, sandbox: Path) -> str:
    """Backward-compatible: delegates to _build_first_prompt."""
    return _build_first_prompt(case, sandbox)


_OPENCLAW_CONFIG_PATHS = [
    Path("/projects/.openclaw/openclaw.json"),
    Path.home() / ".openclaw" / "config.json",
]

_KEY_ENV_MAP = {
    "venus": "VENUS_API_KEY",
    "astra": "ASTRA_API_KEY",
    "yunwu": "YUNWU_API_KEY",
}


def _inject_provider_keys(env: dict[str, str]) -> None:
    """Read API keys from the OpenClaw config and inject as env vars.

    Only sets keys that are not already present in *env*.  This lets Codex
    use the same model providers that OpenClaw has configured.
    """
    for config_path in _OPENCLAW_CONFIG_PATHS:
        if not config_path.is_file():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        providers = data.get("models", {}).get("providers", {})
        for provider_name, env_var in _KEY_ENV_MAP.items():
            if env_var in env and env[env_var]:
                continue
            api_key = providers.get(provider_name, {}).get("apiKey", "")
            if api_key:
                env[env_var] = api_key
        break  # stop after first valid config


def _collect_audit(
    environment: ClawBiasEnvironment,
) -> list[dict[str, Any]]:
    """Pull the complete audit log from Mock Service."""
    return environment.service.audit(environment.family)


def _audit_to_executions(
    audit_calls: list[dict[str, Any]],
) -> list[ToolExecution]:
    """Convert Mock Service audit entries to ToolExecution objects."""
    executions = []
    for i, call in enumerate(audit_calls):
        endpoint = call.get("endpoint", "")
        # Use endpoint path as operation name, strip leading slash
        operation = endpoint.lstrip("/") if endpoint else ""
        method = call.get("method", "")
        request_body = call.get("request_body")
        params = request_body if isinstance(request_body, dict) else {}
        response = call.get("response_body")
        error = None
        if isinstance(response, dict) and response.get("error"):
            error = str(response["error"])
        executions.append(
            ToolExecution(
                tool_call_id=f"audit_{i}",
                operation=operation,
                params=params,
                response=response,
                error=error,
            )
        )
    return executions


def _parse_codex_output(stdout: str) -> tuple[str, list[dict[str, Any]]]:
    """Extract final output and a normalized message list from Codex JSONL stdout.

    Codex ``--json`` outputs one JSON object per line.  We parse both the
    legacy ``message`` shape (with ``role``) and the newer ``item.completed``
    event shape where assistant text lives in ``item.text`` and tool calls
    are ``item.type == "command_execution"``.
    """
    last_assistant_text: str = ""
    normalized: list[dict[str, Any]] = []

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        item = event.get("item") or {}
        item_type = item.get("type", "") if isinstance(item, dict) else ""

        # --- Newer Codex JSONL shape: item.completed events ---
        if event_type == "item.completed" and isinstance(item, dict):
            if item_type == "agent_message":
                text = item.get("text", "")
                if text:
                    last_assistant_text = str(text)
                    normalized.append({"role": "assistant", "content": str(text)})
                continue
            if item_type == "command_execution":
                cmd = item.get("command", "")
                output = item.get("aggregated_output", "")
                exit_code = item.get("exit_code")
                status = item.get("status", "")
                # Emit as a tool_call + tool_result pair for the judge
                call_id = item.get("id", "")
                normalized.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": "shell",
                            "arguments": json.dumps({"command": cmd}),
                        },
                    }],
                })
                result_text = str(output)
                if exit_code is not None and exit_code != 0:
                    result_text += f"\n[exit_code={exit_code}]"
                if status == "failed":
                    result_text += "\n[status=failed]"
                normalized.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": "shell",
                    "content": result_text,
                })
                continue

        # --- Legacy shape: top-level message with role ---
        msg = event.get("message") or event
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "assistant" and content:
            last_assistant_text = str(content)
            normalized.append({"role": "assistant", "content": str(content)})
        elif role == "tool" and content:
            normalized.append({
                "role": "tool",
                "tool_call_id": str(msg.get("tool_call_id", "")),
                "name": str(msg.get("name", "")),
                "content": str(content),
            })

    final_output = last_assistant_text.strip()
    # Fallback: if no structured events parsed, use raw stdout
    if not final_output:
        final_output = stdout.strip()
        if final_output:
            normalized = [{"role": "assistant", "content": final_output}]

    return final_output, normalized


def _extract_thread_id(stdout: str) -> str | None:
    """Extract the thread_id from Codex JSONL output.

    Codex emits a ``{"type": "thread.started", "thread_id": "..."}`` event
    at the beginning of each session.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "thread.started":
            tid = event.get("thread_id")
            if tid:
                return str(tid)
    return None


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CodexAgent:
    """Codex CLI harness adapter.

    Spawns a ``codex`` subprocess with the task prompt, pointed at the sandbox
    workspace.  After the process exits (or times out), evidence is collected
    from the Mock Service.
    """

    harness_name: str = "codex"

    # Retry on empty turn.failed errors (venus API streaming drops)
    MAX_RETRIES: int = 2

    def __init__(
        self,
        budget: AgentBudget | None = None,
        codex_binary: str = "codex",
        model: str | None = None,
        *,
        user_agent: UserAgent | None = None,
        max_user_turns: int = 5,
    ):
        self.budget = budget or AgentBudget()
        self.codex_binary = codex_binary
        self.model = model
        self.user_agent = user_agent
        self.max_user_turns = max_user_turns

    def run(self, case: CaseSpec, environment: ClawBiasEnvironment) -> AgentRun:
        port = environment.service.base_url.rsplit(":", 1)[-1]
        sandbox = _prepare_sandbox(case, int(port), self.budget)

        try:
            first_prompt = _build_first_prompt(case, sandbox)
            follow_ups = case.user_messages[1:]  # may be empty

            print(first_prompt)
            print("+++++++++++++++")

            raw_messages: list[dict[str, Any]] = []
            all_outputs: list[str] = []
            all_normalized: list[dict[str, Any]] = []
            stop_reason = "finished"
            thread_id: str | None = None

            # --- Turn 1: setup + first user message (with retries) ---
            attempts: list[dict[str, Any]] = []
            for attempt in range(1 + self.MAX_RETRIES):
                if attempt > 0:
                    print(f"[codex retry {attempt}/{self.MAX_RETRIES}] {case.case_id}", flush=True)

                stdout, stderr, return_code, timed_out = self._exec_codex(
                    first_prompt, sandbox
                )
                attempts.append({
                    "attempt": attempt + 1,
                    "returncode": return_code,
                    "timed_out": timed_out,
                    "stderr": stderr,
                })
                if timed_out or return_code != 0:
                    print(
                        f"[codex failure] case={case.case_id} "
                        f"attempt={attempt + 1} returncode={return_code} "
                        f"timed_out={timed_out}\n{stderr[-4000:]}",
                        file=sys.stderr,
                        flush=True,
                    )

                if timed_out:
                    stop_reason = "timeout"
                    break
                elif return_code != 0:
                    stop_reason = "error"
                    if attempt < self.MAX_RETRIES:
                        continue
                else:
                    stop_reason = "finished"
                    break

            # Extract thread_id for multi-turn resume
            thread_id = _extract_thread_id(stdout)

            raw_messages.append({"role": "user", "content": first_prompt})
            raw_messages.append({"role": "assistant", "content": stdout})
            output, normalized = _parse_codex_output(stdout)
            all_outputs.append(output)
            all_normalized.append({"role": "user", "content": case.user_messages[0]})
            all_normalized.extend(normalized)

            # --- Subsequent turns (multi-turn cases via codex exec resume) ---
            for msg in follow_ups:
                if stop_reason != "finished":
                    break
                if not thread_id:
                    print(
                        f"[codex] no thread_id for multi-turn resume, "
                        f"case={case.case_id}",
                        file=sys.stderr, flush=True,
                    )
                    break

                stdout, stderr, return_code, timed_out = self._exec_codex_resume(
                    thread_id, msg, sandbox
                )
                raw_messages.append({"role": "user", "content": msg})
                raw_messages.append({"role": "assistant", "content": stdout})
                output, normalized = _parse_codex_output(stdout)
                all_outputs.append(output)
                all_normalized.append({"role": "user", "content": msg})
                all_normalized.extend(normalized)

                if timed_out:
                    stop_reason = "timeout"
                elif return_code != 0:
                    stop_reason = "error"

            # --- Interactive loop: user-agent generates follow-up messages ---
            user_agent = self.user_agent if case.category == "model_misbehavior" else None
            intent: dict[str, Any] | None = None
            if user_agent:
                from eval.cases.user_intent import load_user_intent
                intent = load_user_intent(case)

            decisions: list[dict[str, Any]] = []
            user_turns = 1 + len([m for m in follow_ups if stop_reason == "finished"])

            if user_agent and intent and thread_id and stop_reason == "finished":
                while user_turns < self.max_user_turns:
                    try:
                        from dataclasses import asdict
                        decision = user_agent.decide(intent, all_normalized)
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

                    # Send the user-agent's follow-up message via codex exec resume.
                    user_turns += 1
                    stdout, stderr, return_code, timed_out = self._exec_codex_resume(
                        thread_id, decision.message, sandbox
                    )
                    raw_messages.append({"role": "user", "content": decision.message})
                    raw_messages.append({"role": "assistant", "content": stdout})
                    output, normalized = _parse_codex_output(stdout)
                    all_outputs.append(output)
                    all_normalized.append({"role": "user", "content": decision.message})
                    all_normalized.extend(normalized)

                    if timed_out:
                        stop_reason = "timeout"
                        break
                    elif return_code != 0:
                        stop_reason = "error"
                        break
                else:
                    # Exhausted max_user_turns without a stop decision.
                    if stop_reason == "finished":
                        stop_reason = "max_user_turns"

            # Collect evidence from Mock Service (always after all turns)
            audit_calls = _collect_audit(environment)
            state_after = environment.service.snapshot()
            executions = _audit_to_executions(audit_calls)

            final_output = "\n\n".join(o for o in all_outputs if o)

            # Refine stop reason with audit data
            if stop_reason == "finished" and len(audit_calls) >= self.budget.max_tool_calls:
                stop_reason = "max_tool_calls"

            # Build normalized transcript with proper user/assistant interleaving
            normalized_messages: list[dict[str, Any]] = [
                {"role": "system", "content": render_skill_text(case.skill_text, int(port))},
            ]
            normalized_messages.extend(all_normalized)

            return AgentRun(
                messages=[
                    {"role": "system", "content": "[codex harness — see normalized_messages]"},
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
                diagnostics={"attempts": attempts, "sandbox": str(sandbox),
                             "thread_id": thread_id},
            )
        finally:
            print(
                f"[codex sandbox] case={case.case_id}  "
                f"sandbox={sandbox}  "
                f"port={port}  "
                f"stop_reason={stop_reason if 'stop_reason' in dir() else 'unknown'}",
                flush=True,
            )
            # DEBUG: sandbox preserved for inspection; restore shutil.rmtree when done
            #shutil.rmtree(sandbox, ignore_errors=True)

    def _build_model_args(self) -> list[str]:
        """Return CLI flags for model selection."""
        args: list[str] = []
        if self.model:
            if "/" in self.model:
                provider, model_id = self.model.split("/", 1)
                args.extend(["--model", model_id])
                args.extend(["-c", f'model_provider="{provider}"'])
            else:
                args.extend(["--model", self.model])
        return args

    def _make_env(self) -> dict[str, str]:
        """Build env dict with injected provider keys."""
        env = os.environ.copy()
        _inject_provider_keys(env)
        return env

    @staticmethod
    def _redact(value: str | bytes | None, env: dict[str, str]) -> str:
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        text = value or ""
        for name, secret in env.items():
            if secret and any(part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
                text = text.replace(secret, "[REDACTED]")
        return re.sub(r"(?i)(Bearer\s+)[\w.\-]+", r"\1[REDACTED]", text)

    def _exec_codex(
        self, task_prompt: str, sandbox: Path
    ) -> tuple[str, str, int, bool]:
        """Run the first Codex turn and return (stdout, stderr, returncode, timed_out).

        Uses ``codex exec`` (non-interactive mode) with ``--cd`` pointing at
        the sandbox, ``--json`` for structured JSONL output.  Session files
        are persisted so that ``codex exec resume`` can continue the
        conversation for multi-turn cases.
        """
        cmd = [
            self.codex_binary, "exec",
            "--json",
            "--skip-git-repo-check",
            "--cd", str(sandbox),
        ]
        cmd.extend(self._build_model_args())
        # Use danger-full-access sandbox so the agent can reach the
        # mock-service on localhost (bubblewrap's default network namespace
        # blocks loopback even with network-full-access).
        cmd.extend(["-s", "danger-full-access"])
        cmd.append(task_prompt)

        env = self._make_env()
        timeout = self.budget.timeout_seconds or None
        try:
            result = subprocess.run(
                cmd, cwd=sandbox, env=env,
                capture_output=True, text=True, timeout=timeout,
            )
            return (
                self._redact(result.stdout, env),
                self._redact(result.stderr, env),
                result.returncode, False,
            )
        except subprocess.TimeoutExpired as exc:
            return self._redact(exc.stdout, env), self._redact(exc.stderr, env), -1, True

    def _exec_codex_resume(
        self, thread_id: str, message: str, sandbox: Path
    ) -> tuple[str, str, int, bool]:
        """Resume a Codex session with a follow-up message.

        Uses ``codex exec resume <thread_id> <message>`` to continue the
        conversation in an existing thread.
        """
        # Resume does not expose `-s`; override the sandbox mode so follow-up
        # turns retain the first turn's access to the localhost Mock Service.
        cmd = [
            self.codex_binary, "exec", "resume",
            "--json",
            "--skip-git-repo-check",
            "-c", 'sandbox_mode="danger-full-access"',
            thread_id,
            message,
        ]
        cmd.extend(self._build_model_args())

        env = self._make_env()
        timeout = self.budget.timeout_seconds or None
        try:
            result = subprocess.run(
                cmd, cwd=sandbox, env=env,
                capture_output=True, text=True, timeout=timeout,
            )
            return (
                self._redact(result.stdout, env),
                self._redact(result.stderr, env),
                result.returncode, False,
            )
        except subprocess.TimeoutExpired as exc:
            return self._redact(exc.stdout, env), self._redact(exc.stderr, env), -1, True
