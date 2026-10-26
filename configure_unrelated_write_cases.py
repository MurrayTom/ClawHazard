"""Add standard setup and evaluation entrypoints to imported task cases."""

from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
TASKS_DIR = PROJECT_DIR / "tasks_filtered_unrelated_write"

SETUP_SCRIPT = '''#!/usr/bin/env python3
"""Set up this imported task case's local mock-service lab."""

from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_DIR))

from lab_setup import setup_lab_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(
        setup_lab_main(CASE_DIR, skill_source="tasks_filtered_unrelated_write")
    )
'''

CHECK_SCRIPT = '''#!/usr/bin/env python3
"""Evaluate captured state and tool-call evidence for this task case."""

from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_DIR))

from task_check_result import check_result_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(check_result_main(CASE_DIR))
'''


def main() -> int:
    case_dirs = sorted(
        meta_path.parent for meta_path in TASKS_DIR.rglob("meta.yaml")
    )
    if not case_dirs:
        raise SystemExit(f"No task cases found under {TASKS_DIR}")

    created = 0
    for case_dir in case_dirs:
        if not (case_dir / "mock_service" / "server.py").is_file():
            raise SystemExit(f"Mock service is missing for {case_dir}")
        if not (case_dir / "source_report.json").is_file():
            raise SystemExit(f"Source report is missing for {case_dir}")
        if not (case_dir / "grading.md").is_file():
            raise SystemExit(f"Grading guide is missing for {case_dir}")
        scripts_dir = case_dir / "scripts"
        setup_path = scripts_dir / "setup_lab.py"
        check_path = scripts_dir / "check_result.py"
        existing = [path for path in (setup_path, check_path) if path.exists()]
        if existing:
            raise SystemExit(
                "Refusing to overwrite existing scripts: "
                + ", ".join(str(path) for path in existing)
            )
        scripts_dir.mkdir(exist_ok=True)
        setup_path.write_text(SETUP_SCRIPT, encoding="utf-8", newline="\n")
        check_path.write_text(CHECK_SCRIPT, encoding="utf-8", newline="\n")
        created += 1

    print(f"Configured {created} task cases with setup_lab.py and check_result.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
