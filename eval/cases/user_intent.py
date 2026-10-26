"""Private fixed intentions, loaded only for opt-in interactive evaluation."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from eval.models import CaseSpec


def load_user_intent(case: CaseSpec) -> dict[str, Any]:
    if case.category != "model_misbehavior" or len(case.user_messages) != 1:
        raise ValueError(
            "interactive requires a model_misbehavior case with one initial request"
        )
    path = case.task_dir / "user_intent.json"
    intent = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(intent, dict) or intent.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported user intent schema")
    if intent.get("case_id") != case.case_id:
        raise ValueError(f"{path}: case_id mismatch")
    if intent.get("initial_request") != case.user_messages[0]:
        raise ValueError(f"{path}: initial request mismatch")
    if intent.get("annotation_origin") != "new_fixed_intent_for_interactive":
        raise ValueError(f"{path}: unknown annotation origin")
    seed = case.resource_dir / "mock_service" / "seed_data.json"
    if hashlib.sha256(seed.read_bytes()).hexdigest() != intent.get("seed_sha256"):
        raise ValueError(
            f"{path}: seed changed; review the fixed intent before running"
        )
    for key in ("user_identity", "user_goal"):
        if not isinstance(intent.get(key), str) or not intent[key].strip():
            raise ValueError(f"{path}: missing {key}")
    for key in (
        "operation",
        "allowed_scope",
        "required_parameters",
        "confirmation_policy",
        "expected_result",
    ):
        if not isinstance(intent.get(key), dict):
            raise ValueError(f"{path}: missing {key}")
    if not isinstance(intent["required_parameters"].get("user_supplied"), dict):
        raise ValueError(f"{path}: missing user-supplied parameters")
    if intent["operation"].get("type") not in {
        "query",
        "create",
        "update",
        "delete",
        "action",
    }:
        raise ValueError(f"{path}: invalid operation type")
    scope = intent["allowed_scope"]
    if (
        not isinstance(scope.get("description"), str)
        or not scope["description"].strip()
    ):
        raise ValueError(f"{path}: missing scope description")
    if not isinstance(scope.get("preserve_untargeted_data"), bool):
        raise ValueError(f"{path}: missing scope preservation policy")
    if not isinstance(scope.get("forbidden_actions"), list) or not all(
        isinstance(item, str) for item in scope["forbidden_actions"]
    ):
        raise ValueError(f"{path}: invalid forbidden actions")
    policy = intent["confirmation_policy"]
    if not isinstance(policy.get("required"), bool) or not isinstance(
        policy.get("condition"), str
    ):
        raise ValueError(f"{path}: invalid confirmation policy")
    expected = intent["expected_result"]
    if (
        not isinstance(expected.get("completion"), str)
        or not expected["completion"].strip()
    ):
        raise ValueError(f"{path}: missing expected completion")
    if not isinstance(expected.get("response_checks"), list) or not all(
        isinstance(item, str) for item in expected["response_checks"]
    ):
        raise ValueError(f"{path}: invalid response checks")
    if not isinstance(expected.get("state_checks"), list):
        raise ValueError(f"{path}: invalid state checks")
    for check in expected["state_checks"]:
        if (
            not isinstance(check, dict)
            or not isinstance(check.get("path"), list)
            or not all(
                isinstance(key, (str, int)) and not isinstance(key, bool)
                for key in check["path"]
            )
            or check.get("operator") not in {"equals", "absent", "unchanged"}
            or (check["operator"] == "equals" and "value" not in check)
        ):
            raise ValueError(f"{path}: invalid state check")
    criteria = intent.get("evaluation_criteria")
    if not isinstance(criteria, dict):
        raise ValueError(f"{path}: missing interactive evaluation_criteria")
    # Safety belongs to source_report.json, not the private intention schema.
    for name in ("original_task_success",):
        group = criteria.get(name)
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("description"), str)
            or not group["description"].strip()
            or not isinstance(group.get("check_items"), list)
            or not group["check_items"]
            or not all(
                isinstance(item, str) and item.strip() for item in group["check_items"]
            )
        ):
            raise ValueError(f"{path}: invalid interactive {name} rubric")
    return intent


def user_visible_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """Allowlist user-known facts; never expose solver hints or evaluator state."""
    scope = intent["allowed_scope"]
    return deepcopy(
        {
            "user_identity": intent["user_identity"],
            "user_goal": intent["user_goal"],
            "operation_type": intent["operation"]["type"],
            "user_supplied": intent["required_parameters"]["user_supplied"],
            "allowed_scope": {
                "description": scope["description"],
                "preserve_untargeted_data": scope["preserve_untargeted_data"],
                "forbidden_actions": scope["forbidden_actions"],
            },
            "confirmation_policy": intent["confirmation_policy"],
        }
    )
