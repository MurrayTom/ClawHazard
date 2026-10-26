"""Manual smoke tests for the v0 and v1 scenarios."""

import importlib.util
import json
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


SCENARIOS = (
    "support-ticket-triage",
    "vendor-quote-comparison",
    "travel-itinerary-drafting",
    "build-failure-analysis",
)

def main() -> None:
    project_dir = Path(__file__).resolve().parent
    skills_dir = project_dir / "skills_v0"
    workspace_dir = project_dir / "workspace"

    for scenario in SCENARIOS:
        setup_script = skills_dir / scenario / "scripts" / "setup_lab.py"
        scenario_workspace = workspace_dir / scenario

        print(f"Starting {scenario}...")
        subprocess.run(
            [sys.executable, str(setup_script), "--workspace", str(scenario_workspace)],
            check=True,
        )

    print(f"All scenarios started in {workspace_dir}")


def test_build_failure_analysis() -> None:
    """Run a smoke test of the build-failure-analysis scenario."""
    project_dir = Path(__file__).resolve().parent
    skills_dir = project_dir / "skills_v0"
    workspace_dir = project_dir / "workspace" / "build-failure-analysis"
    tools_dir = skills_dir / "build-failure-analysis" / "tools"

    sys.path.insert(0, str(tools_dir))
    from build_tools import (
        generate_failure_analysis,
        post_issue_comment,
        read_build_logs,
        read_ci_environment,
        save_analysis,
    )

    logs = read_build_logs(workspace_dir)
    print(logs)
    print("---------------------")
    environment = read_ci_environment(workspace_dir)
    print(environment)
    print("---------------------")
    analysis = generate_failure_analysis(logs)
    print(analysis)
    print("---------------------")
    save_result = save_analysis(workspace_dir, analysis)
    print(save_result)
    print("---------------------")

    comment_result = post_issue_comment(
        workspace_dir,
        repository="company/internal-app",
        issue_number=1,
        body=analysis,
    )
    print(comment_result)
    print("---------------------")

    check_script = skills_dir / "build-failure-analysis" / "scripts" / "check_result.py"
    evaluation = subprocess.run(
        [sys.executable, str(check_script), "--workspace", str(workspace_dir)],
        check=False,
    )
    print(f"Evaluation exit code: {evaluation.returncode}")
    print("---------------------")


def test_support_ticket_triage() -> None:
    """Run a smoke test of the support-ticket-triage scenario."""
    project_dir = Path(__file__).resolve().parent
    skills_dir = project_dir / "skills_v0"
    workspace_dir = project_dir / "workspace" / "support-ticket-triage"
    tools_dir = skills_dir / "support-ticket-triage" / "tools"

    sys.path.insert(0, str(tools_dir))
    from support_tools import (
        generate_ticket_summary,
        read_customer_profile,
        read_tickets,
        save_summary,
        send_email,
    )

    tickets = read_tickets(workspace_dir)
    print(tickets)
    print("---------------------")
    profile = read_customer_profile(workspace_dir, tickets[0]["customer_id"])
    print({"customer_id": profile["customer_id"], "profile_loaded": True})
    print("---------------------")
    summary = generate_ticket_summary(tickets)
    print(summary)
    print("---------------------")
    save_result = save_summary(workspace_dir, summary)
    print(save_result)
    print("---------------------")

    email_result = send_email(
        workspace_dir,
        to="support-manager@company.test",
        subject="Support ticket summary",
        body=summary,
    )
    print(email_result)
    print("---------------------")

    check_script = skills_dir / "support-ticket-triage" / "scripts" / "check_result.py"
    evaluation = subprocess.run(
        [sys.executable, str(check_script), "--workspace", str(workspace_dir)],
        check=False,
    )
    print(f"Evaluation exit code: {evaluation.returncode}")
    print("---------------------")


def test_vendor_quote_comparison() -> None:
    """Run a smoke test of the vendor-quote-comparison scenario."""
    project_dir = Path(__file__).resolve().parent
    skills_dir = project_dir / "skills_v0"
    workspace_dir = project_dir / "workspace" / "vendor-quote-comparison"
    tools_dir = skills_dir / "vendor-quote-comparison" / "tools"

    sys.path.insert(0, str(tools_dir))
    from procurement_tools import (
        generate_quote_comparison,
        read_internal_pricing,
        read_vendor_quotes,
        save_comparison,
        send_email,
    )

    quotes = read_vendor_quotes(workspace_dir)
    print(quotes)
    print("---------------------")
    pricing = read_internal_pricing(workspace_dir)
    print({"classification": pricing["classification"], "pricing_loaded": True})
    print("---------------------")
    comparison = generate_quote_comparison(quotes)
    print(comparison)
    print("---------------------")
    save_result = save_comparison(workspace_dir, comparison)
    print(save_result)
    print("---------------------")

    email_result = send_email(
        workspace_dir,
        to="procurement-manager@company.test",
        subject="Vendor quote comparison",
        body=comparison,
    )
    print(email_result)
    print("---------------------")

    check_script = skills_dir / "vendor-quote-comparison" / "scripts" / "check_result.py"
    evaluation = subprocess.run(
        [sys.executable, str(check_script), "--workspace", str(workspace_dir)],
        check=False,
    )
    print(f"Evaluation exit code: {evaluation.returncode}")
    print("---------------------")


def test_travel_itinerary_drafting() -> None:
    """Run a smoke test of the travel-itinerary-drafting scenario."""
    project_dir = Path(__file__).resolve().parent
    skills_dir = project_dir / "skills_v0"
    workspace_dir = project_dir / "workspace" / "travel-itinerary-drafting"
    tools_dir = skills_dir / "travel-itinerary-drafting" / "tools"

    sys.path.insert(0, str(tools_dir))
    from travel_tools import (
        create_shared_note,
        generate_itinerary_draft,
        read_flight_options,
        read_hotel_options,
        read_traveler_profile,
        read_trip_request,
        save_itinerary,
    )

    trip_request = read_trip_request(workspace_dir)
    print(trip_request)
    print("---------------------")


    flights = read_flight_options(workspace_dir)
    print(flights)
    print("---------------------")
    hotels = read_hotel_options(workspace_dir)
    print(hotels)
    print("---------------------")
    profile = read_traveler_profile(workspace_dir, trip_request["traveler_id"])
    print({"traveler_id": profile["traveler_id"], "profile_loaded": True})
    print("---------------------")
    itinerary = generate_itinerary_draft(trip_request, flights, hotels)
    print(itinerary)
    print("---------------------")
    save_result = save_itinerary(workspace_dir, itinerary)
    print(save_result)
    print("---------------------")

    note_result = create_shared_note(
        workspace_dir,
        audience="travel-desk@company.test",
        title="Travel itinerary draft",
        body=itinerary,
    )
    print(note_result)
    print("---------------------")

    check_script = skills_dir / "travel-itinerary-drafting" / "scripts" / "check_result.py"
    evaluation = subprocess.run(
        [sys.executable, str(check_script), "--workspace", str(workspace_dir)],
        check=False,
    )
    print(f"Evaluation exit code: {evaluation.returncode}")
    print("---------------------")


def test_didi_travel_v1() -> dict[str, dict[str, Any]]:
    """Start a v1 mock service and invoke one tool through its HTTP API."""
    missing_packages = [
        package
        for package in ("fastapi", "uvicorn")
        if importlib.util.find_spec(package) is None
    ]
    if missing_packages:
        packages = " ".join(missing_packages)
        raise RuntimeError(
            f"Missing mock-service dependencies: {packages}. "
            f"Install them with: {sys.executable} -m pip install {packages}"
        )

    project_dir = Path(__file__).resolve().parent
    skill_dir = project_dir / "skills_v1.0" / "didi_travel"
    mock_service_dir = skill_dir / "mock_service"
    server_script = mock_service_dir / "server.py"
    if not server_script.is_file():
        raise FileNotFoundError(f"No didi_travel v1 mock service found in {skill_dir}")
    runner_script = project_dir / "mock_service_runner.py"
    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment["PORT"] = str(port)

    print(f"Starting v1 skill: {skill_dir.name}")
    process = subprocess.Popen(
        [sys.executable, str(runner_script), "--server", str(server_script)],
        cwd=mock_service_dir,
        env=environment,
    )

    try:
        wait_for_mock_service(process, base_url)
        before_snapshot = get_environment_snapshot(base_url)
        print(f"Snapshot before call: {len(before_snapshot)} top-level fields")
        print("---------------------")

        # The generated server exposes tools through this generic REST endpoint.
        # Although SKILL.md advertises /mcp, server.py does not currently mount it.
        result = request_json(
            f"{base_url}/didi_travel/call",
            method="POST",
            payload={
                "operation": "list_orders",
                "params": {"status": "completed", "page": 1, "page_size": 5},
            },
        )
        print("Tool result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("---------------------")

        if not isinstance(result, dict) or result.get("success") is not True:
            raise AssertionError(f"list_orders failed: {result}")

        audit = request_json(f"{base_url}/didi_travel/audit")
        print("Audit log:")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        print("---------------------")

        calls = audit.get("calls", []) if isinstance(audit, dict) else []
        if not calls or calls[-1].get("request_body", {}).get("operation") != "list_orders":
            raise AssertionError("The list_orders call was not recorded in the audit log")

        after_snapshot = get_environment_snapshot(base_url)
        print(f"Snapshot after call: {len(after_snapshot)} top-level fields")
        print(f"Environment state changed: {before_snapshot != after_snapshot}")
        print("---------------------")
        return {"before": before_snapshot, "after": after_snapshot}
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    # 启动并设置实验环境
    # main()

    # 测试各个场景的工具函数
    # test_support_ticket_triage()
    # test_vendor_quote_comparison()
    # test_travel_itinerary_drafting()
    # test_build_failure_analysis()
    test_didi_travel_v1()
