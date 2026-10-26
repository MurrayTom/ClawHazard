from __future__ import annotations

from .resource_resolver import ResourceResolutionError


REQUIRED_META_FIELDS = ("id", "category", "skill_name", "skill_source")


def validate_metadata(metadata: dict[str, object], source: str) -> None:
    missing = [key for key in REQUIRED_META_FIELDS if not metadata.get(key)]
    if missing:
        raise ValueError(f"{source}: missing metadata fields: {', '.join(missing)}")


def validate_resource_name(skill_name: str, resource_dir_name: str) -> None:
    if not skill_name or not resource_dir_name:
        raise ResourceResolutionError("Skill and resource directory names must be non-empty")
