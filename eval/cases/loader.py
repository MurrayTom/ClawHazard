from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml

from eval.models import CaseSpec

from .prompt_parser import extract_user_input
from .resource_resolver import ResourceResolver
from .validators import validate_metadata


class CaseLoader:
    def __init__(self, tasks_root: Path, fallback_tasks_root: Path | None = None):
        self.tasks_root = tasks_root.resolve()
        self.resolver = ResourceResolver(self.tasks_root, fallback_tasks_root)

    def discover(
        self,
        categories: Iterable[str] | None = None,
        case_ids: Iterable[str] | None = None,
    ) -> list[CaseSpec]:
        category_filter = set(categories or [])
        id_filter = set(case_ids or [])
        cases: list[CaseSpec] = []
        for meta_path in sorted(self.tasks_root.glob("**/meta.yaml")):
            metadata = self._read_yaml(meta_path)
            if category_filter and metadata.get("category") not in category_filter:
                continue
            if id_filter and metadata.get("id") not in id_filter:
                continue
            cases.append(self._load(meta_path.parent, metadata))
        return cases

    def load_by_id(self, case_id: str) -> CaseSpec:
        matches = self.discover(case_ids=[case_id])
        if not matches:
            raise KeyError(f"Unknown case id: {case_id}")
        if len(matches) > 1:
            raise ValueError(f"Case id is not unique: {case_id}")
        return matches[0]

    def _load(self, task_dir: Path, metadata: dict[str, object]) -> CaseSpec:
        validate_metadata(metadata, str(task_dir / "meta.yaml"))
        resource_dir = self.resolver.resolve_case_resources(task_dir)
        prompt_path = task_dir / "prompt.md"
        prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        user_messages = self._read_user_messages(task_dir)
        prompt = extract_user_input(prompt_text)
        if not user_messages and prompt:
            user_messages = [prompt]
        if not user_messages:
            raise ValueError(f"{task_dir}: no user input found")

        return CaseSpec(
            case_id=str(metadata["id"]),
            category=str(metadata["category"]),
            skill_source=str(metadata["skill_source"]),
            skill_name=str(metadata["skill_name"]),
            task_dir=task_dir.resolve(),
            resource_dir=resource_dir,
            prompt=prompt or user_messages[0],
            user_messages=user_messages,
            skill_text=(resource_dir / "skill_files" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
            metadata=dict(metadata),
        )

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, object]:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a YAML mapping")
        return data

    @staticmethod
    def _read_user_messages(task_dir: Path) -> list[str]:
        path = task_dir / "attack_messages.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = data.get("messages", []) if isinstance(data, dict) else []
        return [
            str(message["content"])
            for message in messages
            if isinstance(message, dict)
            and message.get("role") == "user"
            and message.get("content")
        ]
