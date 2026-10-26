from __future__ import annotations

from pathlib import Path


class ResourceResolutionError(FileNotFoundError):
    pass


class ResourceResolver:
    """Resolve runtime assets without changing how task cases are selected."""

    def __init__(self, tasks_root: Path, fallback_tasks_root: Path | None = None):
        self.tasks_root = tasks_root.resolve()
        self.fallback_tasks_root = (
            fallback_tasks_root.resolve() if fallback_tasks_root else None
        )

    def resolve_case_resources(self, task_dir: Path) -> Path:
        candidates = [task_dir.resolve()]
        relative = task_dir.resolve().relative_to(self.tasks_root)
        if self.fallback_tasks_root:
            candidates.append(self.fallback_tasks_root / relative)

        # Some cases omit duplicated runtime assets. Reuse a complete sibling
        # for the same skill while keeping task input and metadata unchanged.
        candidates.extend(sorted(task_dir.parent.glob("*")))
        if self.fallback_tasks_root:
            fallback_skill_dir = (self.fallback_tasks_root / relative).parent
            candidates.extend(sorted(fallback_skill_dir.glob("*")))

        category, skill_source, skill_name = relative.parts[:3]
        project_root = self.tasks_root.parent
        candidates.append(project_root / skill_source / skill_name)
        for root in filter(None, (self.tasks_root, self.fallback_tasks_root)):
            for safe_category in ("user_attack", "model_misbehavior"):
                candidates.extend(
                    sorted((root / safe_category / skill_source / skill_name).glob("*"))
                )

        for candidate in candidates:
            if (candidate / "skill_files" / "SKILL.md").is_file() and (
                candidate / "mock_service" / "server.py"
            ).is_file():
                return candidate

        checked = ", ".join(str(path) for path in candidates)
        raise ResourceResolutionError(
            f"No complete skill/mock-service resources for {task_dir}; checked: {checked}"
        )
