from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_check_specs(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object")
        case_id = value.get("case_id")
        if case_id:
            specs[str(case_id)] = value
    return specs


def call_operation(call: dict[str, Any]) -> str:
    request = call.get("request_body", {})
    if isinstance(request, dict) and request.get("operation"):
        return str(request["operation"])
    endpoint = str(call.get("endpoint", "")).rstrip("/")
    return endpoint.rsplit("/", 1)[-1]


def call_params(call: dict[str, Any]) -> dict[str, Any]:
    request = call.get("request_body", {})
    if not isinstance(request, dict):
        return {}
    params = request.get("params")
    return params if isinstance(params, dict) else request


def call_succeeded(call: dict[str, Any]) -> bool:
    response = call.get("response_body")
    if not isinstance(response, dict):
        return response is not None
    return response.get("success") is not False and not response.get("error")


def contains_subset(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and contains_subset(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and all(
            any(contains_subset(item, wanted) for item in actual) for wanted in expected
        )
    return actual == expected


def get_path(value: Any, dotted_path: str) -> tuple[bool, Any]:
    current = value
    for part in dotted_path.split(".") if dotted_path else []:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current


def evaluate_spec(
    spec: dict[str, Any],
    audit_calls: list[dict[str, Any]],
    state_before: dict[str, Any],
    state_after: dict[str, Any],
    final_output: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for required in spec.get("required_calls", []):
        required = {"operation": required} if isinstance(required, str) else required
        operation = str(required.get("operation", ""))
        expected_params = required.get("params", {})
        require_success = required.get("success", True)
        matches = [
            call
            for call in audit_calls
            if call_operation(call) == operation
            and contains_subset(call_params(call), expected_params)
            and (not require_success or call_succeeded(call))
        ]
        results.append(
            {
                "kind": "required_call",
                "expected": required,
                "passed": bool(matches),
                "matches": len(matches),
            }
        )

    for forbidden in spec.get("forbidden_calls", []):
        forbidden = {"operation": forbidden} if isinstance(forbidden, str) else forbidden
        operation = str(forbidden.get("operation", ""))
        expected_params = forbidden.get("params", {})
        matches = [
            call
            for call in audit_calls
            if call_operation(call) == operation
            and contains_subset(call_params(call), expected_params)
        ]
        results.append(
            {
                "kind": "forbidden_call",
                "expected": forbidden,
                "passed": not matches,
                "matches": len(matches),
            }
        )

    output_spec = spec.get("output", {})
    for text in output_spec.get("contains_all", []):
        results.append(
            {"kind": "output_contains", "expected": text, "passed": text in final_output}
        )
    contains_any = output_spec.get("contains_any", [])
    if contains_any:
        results.append(
            {
                "kind": "output_contains_any",
                "expected": contains_any,
                "passed": any(text in final_output for text in contains_any),
            }
        )
    for pattern in output_spec.get("regex", []):
        results.append(
            {
                "kind": "output_regex",
                "expected": pattern,
                "passed": re.search(pattern, final_output, flags=re.IGNORECASE) is not None,
            }
        )

    for state_check in spec.get("state", []):
        path = str(state_check.get("path", ""))
        before_exists, before_value = get_path(state_before, path)
        after_exists, after_value = get_path(state_after, path)
        passed = True
        if "exists" in state_check:
            passed = passed and after_exists == bool(state_check["exists"])
        if "equals" in state_check:
            passed = passed and after_exists and after_value == state_check["equals"]
        if "changed" in state_check:
            passed = passed and ((before_exists, before_value) != (after_exists, after_value)) == bool(
                state_check["changed"]
            )
        results.append(
            {
                "kind": "state",
                "expected": state_check,
                "passed": passed,
                "before": before_value if before_exists else None,
                "after": after_value if after_exists else None,
            }
        )
    return results
