"""Regression tests for shared lab workspace setup behavior."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab_setup import prepare_case_workspace


class PrepareCaseWorkspaceTests(unittest.TestCase):
    def make_skill(self, root: Path, name: str = "example-skill") -> Path:
        skill_dir = root / "skills_v2.0" / name
        skill_dir.mkdir(parents=True)
        return skill_dir.resolve()

    def write_managed_workspace(
        self,
        workspace: Path,
        skill_dir: Path,
        *,
        status: str = "stopped",
    ) -> None:
        workspace.mkdir(parents=True)
        (workspace / ".v2-mock-service-lab").write_text("test\n", encoding="utf-8")
        manifest = {
            "skill": skill_dir.name,
            "skill_source": "skills_v2.0",
            "skill_dir": str(skill_dir),
            "workspace": str(workspace.resolve()),
            "status": status,
        }
        (workspace / "run_manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        (workspace / "stale-output.txt").write_text("old", encoding="utf-8")

    def test_existing_workspace_for_same_skill_is_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = self.make_skill(root)
            workspace = (root / "custom-workspace").resolve()
            self.write_managed_workspace(workspace, skill_dir)

            prepare_case_workspace(skill_dir, workspace, "skills_v2.0")

            self.assertTrue(workspace.is_dir())
            self.assertEqual(list(workspace.iterdir()), [])

    def test_running_workspace_is_stopped_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = self.make_skill(root)
            workspace = (root / "custom-workspace").resolve()
            self.write_managed_workspace(workspace, skill_dir, status="running")

            with patch("lab_setup.stop_case_lab") as stop_lab:
                prepare_case_workspace(skill_dir, workspace, "skills_v2.0")

            stop_lab.assert_called_once_with(workspace)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_unmanaged_nonempty_directory_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = self.make_skill(root)
            workspace = (root / "user-files").resolve()
            workspace.mkdir()
            user_file = workspace / "important.txt"
            user_file.write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "non-lab directory"):
                prepare_case_workspace(skill_dir, workspace, "skills_v2.0")

            self.assertEqual(user_file.read_text(encoding="utf-8"), "keep")

    def test_workspace_for_different_skill_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = self.make_skill(root)
            other_skill = self.make_skill(root, "other-skill")
            workspace = (root / "custom-workspace").resolve()
            self.write_managed_workspace(workspace, other_skill)

            with self.assertRaisesRegex(RuntimeError, "different lab"):
                prepare_case_workspace(skill_dir, workspace, "skills_v2.0")

            self.assertTrue((workspace / "stale-output.txt").is_file())


if __name__ == "__main__":
    unittest.main()
