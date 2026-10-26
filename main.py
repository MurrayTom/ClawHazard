"""Command-line entrypoint for setting up and stopping skill labs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from lab_setup import create_run_workspace, stop_case_lab


PROJECT_DIR = Path(__file__).resolve().parent
SKILL_SOURCES = ("skills_v1.0", "skills_v2.0")


def resolve_skill(skill_name: str) -> tuple[str, Path]:
    """Resolve one direct child from the supported skill collections."""
    if Path(skill_name).name != skill_name:
        raise ValueError("Skill must be a directory name, not a path")

    matches: list[tuple[str, Path]] = []
    for source in SKILL_SOURCES:
        source_dir = (PROJECT_DIR / source).resolve()
        skill_dir = (source_dir / skill_name).resolve()
        if skill_dir.parent == source_dir and skill_dir.is_dir():
            matches.append((source, skill_dir))

    if not matches:
        raise FileNotFoundError(f"Unknown skill: {skill_name}")
    if len(matches) > 1:
        sources = ", ".join(source for source, _ in matches)
        raise ValueError(f"Ambiguous skill {skill_name!r}; found in: {sources}")
    return matches[0]


def setup_command(args: argparse.Namespace) -> int:
    skill_source, skill_dir = resolve_skill(args.skill)
    setup_script = skill_dir / "scripts" / "setup_lab.py"
    if not setup_script.is_file():
        raise FileNotFoundError(f"Skill setup script not found: {setup_script}")

    workspace = (
        Path(args.workspace).resolve()
        if args.workspace
        else create_run_workspace(PROJECT_DIR, skill_source, args.skill)
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(setup_script),
            "--workspace",
            str(workspace),
            "--port",
            str(args.port),
        ],
        check=False,
    )
    return completed.returncode


def stop_command(args: argparse.Namespace) -> int:
    agent_output = args.agent_output
    if args.agent_output_file:
        agent_output = Path(args.agent_output_file).read_text(encoding="utf-8")
    manifest = stop_case_lab(Path(args.workspace), agent_output=agent_output)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    setup_parser = commands.add_parser("setup", help="Set up one supported skill")
    setup_parser.add_argument("--skill", required=True, help="Skill directory name")
    setup_parser.add_argument(
        "--workspace",
        help="Override the generated per-run workspace path",
    )
    setup_parser.add_argument(
        "--port",
        type=int,
        default=39200,
        help="Mock-service port; use 0 to select a free port",
    )
    setup_parser.set_defaults(handler=setup_command)

    stop_parser = commands.add_parser("stop", help="Stop a running case lab")
    stop_parser.add_argument("--workspace", required=True)
    output_group = stop_parser.add_mutually_exclusive_group()
    output_group.add_argument("--agent-output", help="Agent final response text")
    output_group.add_argument(
        "--agent-output-file",
        help="UTF-8 file containing the Agent final response",
    )
    stop_parser.set_defaults(handler=stop_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
