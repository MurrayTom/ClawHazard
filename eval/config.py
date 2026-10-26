from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class EvalConfig:
    tasks_root: Path = PROJECT_ROOT / "tasks_filtered_unrelated_write"
    fallback_tasks_root: Path = PROJECT_ROOT / "tasks_filtered"
    utility_checks_path: Path = PROJECT_ROOT / "eval" / "specs" / "utility_checks.jsonl"
    results_root: Path = PROJECT_ROOT / "eval" / "results"
    max_steps: int = 12
    skill_prompt_mode: str = "full"
    request_timeout: float = 120.0
    service_start_timeout: float = 15.0
    interactive: bool = False
    max_user_turns: int = 5
