"""Shared workspace and mock-service setup logic for versioned skill labs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import URLError

from mock_service_utils import (
    get_environment_snapshot,
    get_free_port,
    request_json,
    wait_for_mock_service,
)


LAB_MARKERS = {
    "skills_v1.0": ".v1-mock-service-lab",
    "skills_v2.0": ".v2-mock-service-lab",
    "tasks_filtered_unrelated_write": ".unrelated-write-task-lab",
}


def create_run_workspace(
    project_dir: Path,
    skill_source: str,
    skill_name: str,
) -> Path:
    """Create a unique empty workspace under one skill's run directory."""
    workspace_root = project_dir / "workspace" / skill_source / skill_name
    workspace_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(
        tempfile.mkdtemp(prefix=f"run-{timestamp}-", dir=workspace_root)
    ).resolve()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_meta_scalar(skill_dir: Path, field: str, default: str) -> str:
    """Read one top-level scalar without requiring a YAML dependency."""
    meta_path = skill_dir / "meta.yaml"
    if meta_path.is_file():
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip() == field:
                scalar = value.strip().strip("'\"")
                if scalar:
                    return scalar
    return default


def prepare_case_workspace(
    skill_dir: Path,
    workspace: Path,
    skill_source: str,
) -> None:
    """Create or reset a workspace that is owned by this skill lab.

    Re-running setup against a prior lab workspace is intentionally idempotent.
    Unmarked directories are never removed, so a misspelled ``--workspace`` cannot
    silently destroy unrelated user data.
    """
    marker = workspace / LAB_MARKERS[skill_source]
    if not workspace.exists() or not any(workspace.iterdir()):
        workspace.mkdir(parents=True, exist_ok=True)
        return

    if not marker.is_file():
        raise RuntimeError(
            "Refusing to overwrite a non-lab directory: "
            f"{workspace} (missing {marker.name})"
        )

    manifest_path = workspace / "run_manifest.json"
    manifest: dict[str, Any] | None = None
    if manifest_path.is_file():
        try:
            loaded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Refusing to overwrite a lab with an invalid manifest: {workspace}"
            ) from error
        if not isinstance(loaded_manifest, dict):
            raise RuntimeError(
                f"Refusing to overwrite a lab with an invalid manifest: {workspace}"
            )
        manifest = loaded_manifest
        expected_values = {
            "skill": skill_dir.name,
            "skill_source": skill_source,
            "workspace": str(workspace),
        }
        mismatches = [
            field
            for field, expected in expected_values.items()
            if manifest.get(field) != expected
        ]
        manifest_skill_dir = manifest.get("skill_dir")
        if (
            not isinstance(manifest_skill_dir, str)
            or Path(manifest_skill_dir).resolve() != skill_dir
        ):
            mismatches.append("skill_dir")
        if mismatches:
            fields = ", ".join(sorted(set(mismatches)))
            raise RuntimeError(
                "Refusing to overwrite a workspace owned by a different lab "
                f"({fields} do not match): {workspace}"
            )
    else:
        project_dir = Path(__file__).resolve().parent
        if skill_source == "tasks_filtered_unrelated_write":
            source_root = (project_dir / skill_source).resolve()
            try:
                case_relative_path = skill_dir.relative_to(source_root)
            except ValueError as error:
                raise RuntimeError(
                    f"Task case is outside {source_root}: {skill_dir}"
                ) from error
            expected_root = (
                project_dir / "workspace" / skill_source / case_relative_path
            ).resolve()
        else:
            expected_root = (
                project_dir / "workspace" / skill_source / skill_dir.name
            ).resolve()
        if workspace != expected_root and expected_root not in workspace.parents:
            raise RuntimeError(
                "Refusing to overwrite an incomplete lab outside the managed "
                f"workspace tree: {workspace}"
            )

    if manifest is not None and manifest.get("status") == "running":
        try:
            stop_case_lab(workspace)
        except Exception as error:
            # stop_case_lab always attempts service shutdown even when evidence
            # capture fails. A stale/dead prior run should not make reset unusable.
            print(
                f"Warning: prior lab shutdown was incomplete: {error}",
                file=sys.stderr,
            )

    print(f"Resetting existing lab workspace: {workspace}")
    shutil.rmtree(workspace)
    workspace.mkdir(parents=True)


def setup_case_lab(
    skill_dir: Path,
    workspace: Path,
    port: int = 39200,
    *,
    skill_source: str | None = None,
) -> dict[str, Any]:
    """Create a skill workspace, start its service, and capture initial state."""
    skill_dir = skill_dir.resolve()
    workspace = workspace.resolve()
    project_dir = Path(__file__).resolve().parent
    skill_source = skill_source or skill_dir.parent.name
    if skill_source not in LAB_MARKERS:
        raise ValueError(f"Unsupported skill source: {skill_source}")
    family = read_meta_scalar(skill_dir, "skill_name", skill_dir.name)
    case_id = read_meta_scalar(skill_dir, "id", skill_dir.name)
    mock_service_dir = skill_dir / "mock_service"
    server_script = mock_service_dir / "server.py"
    runner_script = project_dir / "mock_service_runner.py"

    print("mock_service_dir", mock_service_dir)
    print("server_script", server_script)
    print("runner_script", runner_script)
    print("=================================")

    if not server_script.is_file():
        raise FileNotFoundError(f"Mock service not found: {server_script}")
    prepare_case_workspace(skill_dir, workspace, skill_source)
    (workspace / LAB_MARKERS[skill_source]).write_text(
        f"local synthetic {skill_source} experiment\n",
        encoding="utf-8",
    )

    selected_port = get_free_port() if port == 0 else port
    base_url = f"http://127.0.0.1:{selected_port}"
    environment = os.environ.copy()
    environment["PORT"] = str(selected_port)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUNBUFFERED"] = "1"

    log_path = workspace / "mock_service.log"
    popen_options: dict[str, Any] = {}
    if os.name == "nt":
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        popen_options["start_new_session"] = True

    with log_path.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [sys.executable, str(runner_script), "--server", str(server_script)],
            cwd=mock_service_dir,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            **popen_options,
        )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "family": family,
        "skill": skill_dir.name,
        "case": case_id,
        "skill_source": skill_source,
        "skill_dir": str(skill_dir),
        # Kept for consumers of manifests created before the flat layout.
        "case_dir": str(skill_dir),
        "workspace": str(workspace),
        "base_url": base_url,
        "port": selected_port,
        "pid": process.pid,
        "status": "starting",
        "started_at": utc_now(),
    }
    write_json(workspace / "run_manifest.json", manifest)

    try:
        wait_for_mock_service(process, base_url)
        state_before = get_environment_snapshot(base_url)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        manifest["status"] = "setup_failed"
        manifest["stopped_at"] = utc_now()
        write_json(workspace / "run_manifest.json", manifest)
        raise

    write_json(workspace / "state_before.json", state_before)
    write_json(workspace / "tool_calls.json", {"calls": []})
    (workspace / "agent_output.txt").write_text("", encoding="utf-8")
    manifest["status"] = "running"
    manifest["state_before_file"] = "state_before.json"
    manifest["agent_output_file"] = "agent_output.txt"
    manifest["tool_calls_file"] = "tool_calls.json"
    write_json(workspace / "run_manifest.json", manifest)
    return manifest


def stop_case_lab(
    workspace: Path,
    agent_output: str | None = None,
) -> dict[str, Any]:
    """Capture final evidence, persist Agent output, and stop the service."""
    workspace = workspace.resolve()
    if not any((workspace / marker).is_file() for marker in LAB_MARKERS.values()):
        raise RuntimeError(f"Not a supported lab workspace: {workspace}")

    manifest_path = workspace / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_url = manifest["base_url"]
    family = manifest["family"]
    finalize_error: Exception | None = None

    try:
        state_after = get_environment_snapshot(base_url)
        audit = request_json(f"{base_url}/{family}/audit")
        if not isinstance(audit, dict) or not isinstance(audit.get("calls"), list):
            raise RuntimeError(f"Mock service returned an invalid audit log: {audit}")

        write_json(workspace / "state_after.json", state_after)
        write_json(workspace / "tool_calls.json", audit)
        if agent_output is not None:
            (workspace / "agent_output.txt").write_text(agent_output, encoding="utf-8")

        state_before = json.loads(
            (workspace / "state_before.json").read_text(encoding="utf-8")
        )
        manifest["state_after_file"] = "state_after.json"
        manifest["state_changed"] = state_before != state_after
        manifest["finalized_at"] = utc_now()
        manifest["agent_output_bytes"] = (workspace / "agent_output.txt").stat().st_size
    except Exception as error:
        finalize_error = error
        manifest["finalize_error"] = f"{type(error).__name__}: {error}"

    stopped_via_http = False
    try:
        request_json(f"{base_url}/__shutdown", method="POST")
        stopped_via_http = True
    except (OSError, URLError):
        pid = int(manifest["pid"])
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    time.sleep(0.2)
    manifest["status"] = (
        "stopped" if finalize_error is None else "stopped_with_finalize_error"
    )
    manifest["stopped_at"] = utc_now()
    manifest["stopped_via_http"] = stopped_via_http
    write_json(manifest_path, manifest)
    if finalize_error is not None:
        raise RuntimeError(
            f"Service stopped, but final evidence capture failed: {finalize_error}"
        ) from finalize_error
    return manifest


def setup_lab_main(
    skill_dir: Path,
    argv: list[str] | None = None,
    *,
    skill_source: str | None = None,
) -> int:
    """CLI used by each skill-local scripts/setup_lab.py entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        required=True,
        help="Experiment directory; an existing workspace for this skill is reset",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=39200,
        help="Mock-service port; use 0 to select a free port",
    )
    args = parser.parse_args(argv)
    manifest = setup_case_lab(
        skill_dir,
        Path(args.workspace),
        args.port,
        skill_source=skill_source,
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0
