"""Mock Billing Dispute Management API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import BillingDisputeManagementSystem  # noqa: E402

app = FastAPI(title="Mock Billing Dispute Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "BILLING_DISPUTE_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "env_169_rl-task_1_injected.json"),
))

_env: BillingDisputeManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = BillingDisputeManagementSystem(init_config=init_cfg)
    # 将 init_config 中的各实体加载到环境实例
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, dict):
            setattr(_env, attr, val)
        elif hasattr(_env, attr) and isinstance(val, list):
            setattr(_env, attr, val)


_load_fixtures()


def _log_call(endpoint: str, request_body: dict[str, Any], response_body: Any) -> None:
    _audit_log.append({
        "endpoint": endpoint,
        "request_body": request_body,
        "response_body": response_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── 通用调用端点 ──────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    operation: str
    params: dict[str, Any] = {}


@app.post("/billing_dispute_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/billing_dispute_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/billing_dispute_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetBillingItemByIdRequest(BaseModel):
    billing_item_id: str

@app.post("/billing_dispute_management/get_billing_item_by_id")
def endpoint_get_billing_item_by_id(req: GetBillingItemByIdRequest) -> dict[str, Any]:
    """Retrieve a billing item's details using its unique billing_item_id."""
    resp = _env.get_billing_item_by_id(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_billing_item_by_id", req.model_dump(), resp)
    return resp


class GetDisputeByBillingItemIdRequest(BaseModel):
    billing_item_id: str

@app.post("/billing_dispute_management/get_dispute_by_billing_item_id")
def endpoint_get_dispute_by_billing_item_id(req: GetDisputeByBillingItemIdRequest) -> dict[str, Any]:
    """Find the dispute(s) associated with a specific billing_item_id."""
    resp = _env.get_dispute_by_billing_item_id(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_dispute_by_billing_item_id", req.model_dump(), resp)
    return resp


class GetDisputeByIdRequest(BaseModel):
    dispute_id: str

@app.post("/billing_dispute_management/get_dispute_by_id")
def endpoint_get_dispute_by_id(req: GetDisputeByIdRequest) -> dict[str, Any]:
    """Retrieve detailed information for a specific dispute_id."""
    resp = _env.get_dispute_by_id(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_dispute_by_id", req.model_dump(), resp)
    return resp


class ListDisputesByStatusRequest(BaseModel):
    resolution_status: str

@app.post("/billing_dispute_management/list_disputes_by_status")
def endpoint_list_disputes_by_status(req: ListDisputesByStatusRequest) -> dict[str, Any]:
    """List all disputes matching a particular resolution status (e.g., pending, accepted)."""
    resp = _env.list_disputes_by_status(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/list_disputes_by_status", req.model_dump(), resp)
    return resp


@app.post("/billing_dispute_management/get_allowed_resolution_status_values")
def endpoint_get_allowed_resolution_status_values() -> dict[str, Any]:
    """Query the set of permitted values for resolution_status."""
    resp = _env.get_allowed_resolution_status_values()
    _log_call("/billing_dispute_management/get_allowed_resolution_status_values", {}, resp)
    return resp


class GetOperatorByIdRequest(BaseModel):
    operator_id: str

@app.post("/billing_dispute_management/get_operator_by_id")
def endpoint_get_operator_by_id(req: GetOperatorByIdRequest) -> dict[str, Any]:
    """Retrieve operator info using operator_id."""
    resp = _env.get_operator_by_id(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_operator_by_id", req.model_dump(), resp)
    return resp


class GetOperatorByNameRequest(BaseModel):
    name: str

@app.post("/billing_dispute_management/get_operator_by_name")
def endpoint_get_operator_by_name(req: GetOperatorByNameRequest) -> dict[str, Any]:
    """Find operator(s) details by their name."""
    resp = _env.get_operator_by_name(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_operator_by_name", req.model_dump(), resp)
    return resp


class GetDisputeResolutionHistoryRequest(BaseModel):
    dispute_id: str

@app.post("/billing_dispute_management/get_dispute_resolution_history")
def endpoint_get_dispute_resolution_history(req: GetDisputeResolutionHistoryRequest) -> dict[str, Any]:
    """Retrieve resolution status history and actions on a dispute (if tracking is implemented)."""
    resp = _env.get_dispute_resolution_history(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/get_dispute_resolution_history", req.model_dump(), resp)
    return resp


class ValidateDisputeBillingItemRelationRequest(BaseModel):
    dispute_id: str

@app.post("/billing_dispute_management/validate_dispute_billing_item_relation")
def endpoint_validate_dispute_billing_item_relation(req: ValidateDisputeBillingItemRelationRequest) -> dict[str, Any]:
    """Check that a dispute is linked to a valid billing item."""
    resp = _env.validate_dispute_billing_item_relation(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/validate_dispute_billing_item_relation", req.model_dump(), resp)
    return resp


class ResolveDisputeRequest(BaseModel):
    dispute_id: str
    resolution_status: str
    resolution_details: str
    resolver_id: str

@app.post("/billing_dispute_management/resolve_dispute")
def endpoint_resolve_dispute(req: ResolveDisputeRequest) -> dict[str, Any]:
    """Update a dispute's resolution_status, set resolution_details, record resolver_id and timestamp."""
    resp = _env.resolve_dispute(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/resolve_dispute", req.model_dump(), resp)
    return resp


class UpdateDisputeResolutionStatusRequest(BaseModel):
    dispute_id: str
    new_status: str
    operator_id: str

@app.post("/billing_dispute_management/update_dispute_resolution_status")
def endpoint_update_dispute_resolution_status(req: UpdateDisputeResolutionStatusRequest) -> dict[str, Any]:
    """Change the resolution_status value of a dispute after checking allowed values and operator authorization."""
    resp = _env.update_dispute_resolution_status(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/update_dispute_resolution_status", req.model_dump(), resp)
    return resp


class AddDisputeResolutionDetailsRequest(BaseModel):
    dispute_id: str
    resolution_details: str

@app.post("/billing_dispute_management/add_dispute_resolution_details")
def endpoint_add_dispute_resolution_details(req: AddDisputeResolutionDetailsRequest) -> dict[str, Any]:
    """Attach or update resolution_details text to a dispute record."""
    resp = _env.add_dispute_resolution_details(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/add_dispute_resolution_details", req.model_dump(), resp)
    return resp


class AddDisputeRequest(BaseModel):
    billing_item_id: str
    dispute_reason: str
    submitter_id: str
    submit_date: str | None = None

@app.post("/billing_dispute_management/add_dispute")
def endpoint_add_dispute(req: AddDisputeRequest) -> dict[str, Any]:
    """Create a new dispute for a billing item with submitter and reasons."""
    resp = _env.add_dispute(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/add_dispute", req.model_dump(), resp)
    return resp


class DeleteDisputeRequest(BaseModel):
    dispute_id: str

@app.post("/billing_dispute_management/delete_dispute")
def endpoint_delete_dispute(req: DeleteDisputeRequest) -> dict[str, Any]:
    """Remove or archive a dispute record for a billing item."""
    resp = _env.delete_dispute(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/delete_dispute", req.model_dump(), resp)
    return resp


class AssignDisputeResolverRequest(BaseModel):
    dispute_id: str
    operator_id: str

@app.post("/billing_dispute_management/assign_dispute_resolver")
def endpoint_assign_dispute_resolver(req: AssignDisputeResolverRequest) -> dict[str, Any]:
    """Set or update the responsible operator (resolver_id) for a dispute."""
    resp = _env.assign_dispute_resolver(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/assign_dispute_resolver", req.model_dump(), resp)
    return resp


class TimestampDisputeResolutionRequest(BaseModel):
    dispute_id: str
    resolution_date: str

@app.post("/billing_dispute_management/timestamp_dispute_resolution")
def endpoint_timestamp_dispute_resolution(req: TimestampDisputeResolutionRequest) -> dict[str, Any]:
    """Record or update the resolution_date field when resolution status changes."""
    resp = _env.timestamp_dispute_resolution(**req.model_dump(exclude_none=True))
    _log_call("/billing_dispute_management/timestamp_dispute_resolution", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/billing_dispute_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/billing_dispute_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9315")))
