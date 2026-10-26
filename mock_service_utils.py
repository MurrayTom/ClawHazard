import json
import socket
import subprocess
import time
from typing import Any
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener


_LOCAL_OPENER = build_opener(ProxyHandler({}))


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 3.0,
) -> Any:
    """Send an HTTP request and decode its JSON response."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    # Mock services are local. Bypass HTTP_PROXY/HTTPS_PROXY so loopback
    # requests cannot be intercepted by a system or corporate proxy.
    with _LOCAL_OPENER.open(request, timeout=timeout) as response:
        return json.load(response)


def get_free_port() -> int:
    """Ask the OS for an unused local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get_environment_snapshot(base_url: str) -> dict[str, Any]:
    """Fetch the environment state exposed by the test-only service runner."""
    response = request_json(f"{base_url}/__snapshot")
    if not isinstance(response, dict) or not isinstance(response.get("state"), dict):
        raise RuntimeError(f"Mock service returned an invalid snapshot: {response}")
    return response["state"]


def wait_for_mock_service(
    process: subprocess.Popen[Any],
    base_url: str,
    timeout: float = 10.0,
) -> None:
    """Wait until a mock service accepts requests or fail with a useful error."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Mock service exited during startup (exit code {process.returncode})"
            )
        try:
            request_json(f"{base_url}/openapi.json", timeout=1.0)
            return
        except (OSError, URLError) as error:
            last_error = error
            time.sleep(0.1)

    raise TimeoutError(f"Mock service did not start within {timeout}s: {last_error}")
