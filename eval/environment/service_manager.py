from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from mock_service_utils import (
    get_environment_snapshot,
    get_free_port,
    request_json,
    wait_for_mock_service,
)


class ServiceManager:
    def __init__(
        self,
        resource_dir: Path,
        skill_name: str,
        project_root: Path,
        start_timeout: float = 15.0,
    ):
        self.resource_dir = resource_dir
        self.skill_name = skill_name
        self.project_root = project_root
        self.start_timeout = start_timeout
        self.process: subprocess.Popen[Any] | None = None
        self.base_url = ""
        self.state_before: dict[str, Any] = {}

    def start(self) -> "ServiceManager":
        port = get_free_port()
        self.base_url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env["PORT"] = str(port)
        server = self.resource_dir / "mock_service" / "server.py"
        runner = self.project_root / "mock_service_runner.py"
        self.process = subprocess.Popen(
            [sys.executable, str(runner), "--server", str(server)],
            cwd=server.parent,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_mock_service(self.process, self.base_url, self.start_timeout)
            self.state_before = get_environment_snapshot(self.base_url)
        except Exception:
            self.stop_process()
            raise
        return self

    def openapi(self) -> dict[str, Any]:
        document = request_json(f"{self.base_url}/openapi.json")
        if not isinstance(document, dict):
            raise RuntimeError("Mock service returned invalid OpenAPI JSON")
        return document

    def snapshot(self) -> dict[str, Any]:
        return get_environment_snapshot(self.base_url)

    def audit(self, family: str) -> list[dict[str, Any]]:
        """Fetch audit log, trying the legacy per-family endpoint first,
        then falling back to the universal ``/__audit`` endpoint."""
        for url in (
            f"{self.base_url}/{family}/audit",
            f"{self.base_url}/__audit",
        ):
            try:
                response = request_json(url)
            except Exception:
                continue
            calls = response.get("calls") if isinstance(response, dict) else None
            if isinstance(calls, list):
                return [call for call in calls if isinstance(call, dict)]
        raise RuntimeError(
            f"Mock service returned no valid audit log via /{family}/audit or /__audit"
        )

    def stop_process(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                request_json(f"{self.base_url}/__shutdown", method="POST", timeout=1.0)
                self.process.wait(timeout=3.0)
            except Exception:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=3.0)
        self.process = None

    def __enter__(self) -> "ServiceManager":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.stop_process()
