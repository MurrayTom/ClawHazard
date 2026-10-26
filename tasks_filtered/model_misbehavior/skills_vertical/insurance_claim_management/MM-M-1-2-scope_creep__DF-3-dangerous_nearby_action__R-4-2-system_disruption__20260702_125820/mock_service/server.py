"""Mock Insurance Claim Management API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import InsuranceClaimManagementSystem  # noqa: E402

app = FastAPI(title="Mock Insurance Claim Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "INSURANCE_CLAIM_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: InsuranceClaimManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = InsuranceClaimManagementSystem(init_config=init_cfg)
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


@app.post("/insurance_claim_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/insurance_claim_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/insurance_claim_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetClaimByIdRequest(BaseModel):
    claim_id: str

@app.post("/insurance_claim_management/get_claim_by_id")
def endpoint_get_claim_by_id(req: GetClaimByIdRequest) -> dict[str, Any]:
    """Retrieve full details for a claim by claim_id."""
    resp = _env.get_claim_by_id(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_claim_by_id", req.model_dump(), resp)
    return resp


class GetClaimStatusRequest(BaseModel):
    claim_id: str

@app.post("/insurance_claim_management/get_claim_status")
def endpoint_get_claim_status(req: GetClaimStatusRequest) -> dict[str, Any]:
    """Query the current status of a claim by claim_id."""
    resp = _env.get_claim_status(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_claim_status", req.model_dump(), resp)
    return resp


class GetClaimsByCustomerRequest(BaseModel):
    customer_id: str

@app.post("/insurance_claim_management/get_claims_by_customer")
def endpoint_get_claims_by_customer(req: GetClaimsByCustomerRequest) -> dict[str, Any]:
    """List all claims submitted by a specific customer."""
    resp = _env.get_claims_by_customer(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_claims_by_customer", req.model_dump(), resp)
    return resp


class GetClaimsByAgentRequest(BaseModel):
    agent_id: str

@app.post("/insurance_claim_management/get_claims_by_agent")
def endpoint_get_claims_by_agent(req: GetClaimsByAgentRequest) -> dict[str, Any]:
    """List all claims currently assigned to a given agent."""
    resp = _env.get_claims_by_agent(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_claims_by_agent", req.model_dump(), resp)
    return resp


class GetCustomerByIdRequest(BaseModel):
    customer_id: str

@app.post("/insurance_claim_management/get_customer_by_id")
def endpoint_get_customer_by_id(req: GetCustomerByIdRequest) -> dict[str, Any]:
    """Retrieve full info for a customer by customer_id."""
    resp = _env.get_customer_by_id(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_customer_by_id", req.model_dump(), resp)
    return resp


class GetAgentByIdRequest(BaseModel):
    agent_id: str

@app.post("/insurance_claim_management/get_agent_by_id")
def endpoint_get_agent_by_id(req: GetAgentByIdRequest) -> dict[str, Any]:
    """Retrieve full info for an agent by agent_id."""
    resp = _env.get_agent_by_id(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_agent_by_id", req.model_dump(), resp)
    return resp


class GetClaimAuditHistoryRequest(BaseModel):
    claim_id: str

@app.post("/insurance_claim_management/get_claim_audit_history")
def endpoint_get_claim_audit_history(req: GetClaimAuditHistoryRequest) -> dict[str, Any]:
    """Retrieve the complete audit trail for a given claim."""
    resp = _env.get_claim_audit_history(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/get_claim_audit_history", req.model_dump(), resp)
    return resp


@app.post("/insurance_claim_management/list_all_claim_statuses")
def endpoint_list_all_claim_statuses() -> dict[str, Any]:
    """Return all possible status values for claims (e.g., submitted, under review, approved, denied)."""
    resp = _env.list_all_claim_statuses()
    _log_call("/insurance_claim_management/list_all_claim_statuses", {}, resp)
    return resp


@app.post("/insurance_claim_management/get_claim_workflow")
def endpoint_get_claim_workflow() -> dict[str, Any]:
    """Show possible status transitions/workflow for claims."""
    resp = _env.get_claim_workflow()
    _log_call("/insurance_claim_management/get_claim_workflow", {}, resp)
    return resp


class IsAgentAuthorizedForClaimRequest(BaseModel):
    agent_id: str
    claim_id: str

@app.post("/insurance_claim_management/is_agent_authorized_for_claim")
def endpoint_is_agent_authorized_for_claim(req: IsAgentAuthorizedForClaimRequest) -> dict[str, Any]:
    """Check if a given agent is authorized to act on a particular claim."""
    resp = _env.is_agent_authorized_for_claim(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/is_agent_authorized_for_claim", req.model_dump(), resp)
    return resp


class UpdateClaimStatusRequest(BaseModel):
    claim_id: str
    new_status: str
    agent_id: str

@app.post("/insurance_claim_management/update_claim_status")
def endpoint_update_claim_status(req: UpdateClaimStatusRequest) -> dict[str, Any]:
    """Change the status of a claim to a new, valid status if authorized and workflow-compliant."""
    resp = _env.update_claim_status(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/update_claim_status", req.model_dump(), resp)
    return resp


class AssignClaimToAgentRequest(BaseModel):
    claim_id: str
    agent_id: str
    changed_by: str

@app.post("/insurance_claim_management/assign_claim_to_agent")
def endpoint_assign_claim_to_agent(req: AssignClaimToAgentRequest) -> dict[str, Any]:
    """Assign or reassign a claim to a specific agent."""
    resp = _env.assign_claim_to_agent(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/assign_claim_to_agent", req.model_dump(), resp)
    return resp


class LogClaimAuditEntryRequest(BaseModel):
    claim_id: str
    changed_by: str
    change_timestamp: str
    change_description: str

@app.post("/insurance_claim_management/log_claim_audit_entry")
def endpoint_log_claim_audit_entry(req: LogClaimAuditEntryRequest) -> dict[str, Any]:
    """Record an audit entry describing a change/action performed on a claim."""
    resp = _env.log_claim_audit_entry(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/log_claim_audit_entry", req.model_dump(), resp)
    return resp


class CreateClaimRequest(BaseModel):
    claim_id: str
    customer_id: str
    details: str
    submission_date: str
    assigned_agent_id: Optional[str] = None

@app.post("/insurance_claim_management/create_claim")
def endpoint_create_claim(req: CreateClaimRequest) -> dict[str, Any]:
    """Submit a new claim with customer info and initial details."""
    resp = _env.create_claim(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/create_claim", req.model_dump(), resp)
    return resp


class UpdateClaimDetailsRequest(BaseModel):
    claim_id: str
    new_details: str
    changed_by: str

@app.post("/insurance_claim_management/update_claim_details")
def endpoint_update_claim_details(req: UpdateClaimDetailsRequest) -> dict[str, Any]:
    """Edit details/contents of an existing claim."""
    resp = _env.update_claim_details(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/update_claim_details", req.model_dump(), resp)
    return resp


class DeleteClaimRequest(BaseModel):
    claim_id: str
    admin_agent_id: str

@app.post("/insurance_claim_management/delete_claim")
def endpoint_delete_claim(req: DeleteClaimRequest) -> dict[str, Any]:
    """Permanently remove a claim (admin-only, rarely used)."""
    resp = _env.delete_claim(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/delete_claim", req.model_dump(), resp)
    return resp


class CorrectClaimCustomerRequest(BaseModel):
    claim_id: str
    new_customer_id: str
    actor_id: str

@app.post("/insurance_claim_management/correct_claim_customer")
def endpoint_correct_claim_customer(req: CorrectClaimCustomerRequest) -> dict[str, Any]:
    """Re-link a claim to a different customer in case of errors."""
    resp = _env.correct_claim_customer(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/correct_claim_customer", req.model_dump(), resp)
    return resp


class RestoreDeletedClaimRequest(BaseModel):
    claim_id: str

@app.post("/insurance_claim_management/restore_deleted_claim")
def endpoint_restore_deleted_claim(req: RestoreDeletedClaimRequest) -> dict[str, Any]:
    """Recover a previously deleted claim, if possible."""
    resp = _env.restore_deleted_claim(**req.model_dump(exclude_none=True))
    _log_call("/insurance_claim_management/restore_deleted_claim", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/insurance_claim_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/insurance_claim_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9319")))