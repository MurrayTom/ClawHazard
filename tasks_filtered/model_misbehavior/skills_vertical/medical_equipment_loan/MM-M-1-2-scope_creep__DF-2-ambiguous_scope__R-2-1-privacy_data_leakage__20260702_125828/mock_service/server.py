"""Mock Medical Equipment Loan API service (FastAPI)."""

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

from env_class import MedicalEquipmentLoanManagementSystem  # noqa: E402

app = FastAPI(title="Mock Medical Equipment Loan API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "MEDICAL_EQUIPMENT_LOAN_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: MedicalEquipmentLoanManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = MedicalEquipmentLoanManagementSystem(init_config=init_cfg)
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


@app.post("/medical_equipment_loan/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/medical_equipment_loan/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/medical_equipment_loan/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByNameRequest(BaseModel):
    name: str

@app.post("/medical_equipment_loan/get_user_by_name")
def endpoint_get_user_by_name(req: GetUserByNameRequest) -> dict[str, Any]:
    """Retrieve user info (user_id, contact, type) by name."""
    resp = _env.get_user_by_name(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_user_by_name", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/medical_equipment_loan/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Get user information from user_id."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_user_by_id", req.model_dump(), resp)
    return resp


class ListActiveLoansByUserRequest(BaseModel):
    user_id: str

@app.post("/medical_equipment_loan/list_active_loans_by_user")
def endpoint_list_active_loans_by_user(req: ListActiveLoansByUserRequest) -> dict[str, Any]:
    """Get currently active loan transactions for a user."""
    resp = _env.list_active_loans_by_user(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/list_active_loans_by_user", req.model_dump(), resp)
    return resp


class GetLoanDetailsRequest(BaseModel):
    loan_id: str

@app.post("/medical_equipment_loan/get_loan_details")
def endpoint_get_loan_details(req: GetLoanDetailsRequest) -> dict[str, Any]:
    """Retrieve all details of a loan transaction (equipment, status, dates)."""
    resp = _env.get_loan_details(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_loan_details", req.model_dump(), resp)
    return resp


class GetEquipmentByIdRequest(BaseModel):
    equipment_id: str

@app.post("/medical_equipment_loan/get_equipment_by_id")
def endpoint_get_equipment_by_id(req: GetEquipmentByIdRequest) -> dict[str, Any]:
    """Retrieve info about a specific equipment item."""
    resp = _env.get_equipment_by_id(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_equipment_by_id", req.model_dump(), resp)
    return resp


class ListEquipmentByTypeRequest(BaseModel):
    equipment_type: str

@app.post("/medical_equipment_loan/list_equipment_by_type")
def endpoint_list_equipment_by_type(req: ListEquipmentByTypeRequest) -> dict[str, Any]:
    """List all equipment items of a given type (e.g. all wheelchairs)."""
    resp = _env.list_equipment_by_type(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/list_equipment_by_type", req.model_dump(), resp)
    return resp


class GetEquipmentByStatusRequest(BaseModel):
    status: str

@app.post("/medical_equipment_loan/get_equipment_by_status")
def endpoint_get_equipment_by_status(req: GetEquipmentByStatusRequest) -> dict[str, Any]:
    """List equipment items filtered by availability status."""
    resp = _env.get_equipment_by_status(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_equipment_by_status", req.model_dump(), resp)
    return resp


class GetEquipmentConditionAndLocationRequest(BaseModel):
    equipment_id: str

@app.post("/medical_equipment_loan/get_equipment_condition_and_location")
def endpoint_get_equipment_condition_and_location(req: GetEquipmentConditionAndLocationRequest) -> dict[str, Any]:
    """Query the current condition and location of equipment."""
    resp = _env.get_equipment_condition_and_location(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/get_equipment_condition_and_location", req.model_dump(), resp)
    return resp


class CheckLoanStatusRequest(BaseModel):
    loan_id: str

@app.post("/medical_equipment_loan/check_loan_status")
def endpoint_check_loan_status(req: CheckLoanStatusRequest) -> dict[str, Any]:
    """Query the current status (active, returned, overdue) of a loan transaction."""
    resp = _env.check_loan_status(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/check_loan_status", req.model_dump(), resp)
    return resp


class CheckUserRegistrationRequest(BaseModel):
    user_id: str

@app.post("/medical_equipment_loan/check_user_registration")
def endpoint_check_user_registration(req: CheckUserRegistrationRequest) -> dict[str, Any]:
    """Verify if a user is registered and eligible to borrow/return."""
    resp = _env.check_user_registration(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/check_user_registration", req.model_dump(), resp)
    return resp


class IsEquipmentOnActiveLoanRequest(BaseModel):
    equipment_id: str

@app.post("/medical_equipment_loan/is_equipment_on_active_loan")
def endpoint_is_equipment_on_active_loan(req: IsEquipmentOnActiveLoanRequest) -> dict[str, Any]:
    """Check if a given equipment item is currently loaned out."""
    resp = _env.is_equipment_on_active_loan(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/is_equipment_on_active_loan", req.model_dump(), resp)
    return resp


class CheckIfLoanIsOverdueRequest(BaseModel):
    loan_id: str

@app.post("/medical_equipment_loan/check_if_loan_is_overdue")
def endpoint_check_if_loan_is_overdue(req: CheckIfLoanIsOverdueRequest) -> dict[str, Any]:
    """Determine if a loan is overdue based on due_date and current date."""
    resp = _env.check_if_loan_is_overdue(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/check_if_loan_is_overdue", req.model_dump(), resp)
    return resp


class MarkLoanAsReturnedRequest(BaseModel):
    loan_id: str

@app.post("/medical_equipment_loan/mark_loan_as_returned")
def endpoint_mark_loan_as_returned(req: MarkLoanAsReturnedRequest) -> dict[str, Any]:
    """Update a loan transaction status to "returned", set returned_date, and release the equipment."""
    resp = _env.mark_loan_as_returned(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/mark_loan_as_returned", req.model_dump(), resp)
    return resp


class UpdateEquipmentAvailabilityRequest(BaseModel):
    equipment_id: str
    new_status: str

@app.post("/medical_equipment_loan/update_equipment_availability")
def endpoint_update_equipment_availability(req: UpdateEquipmentAvailabilityRequest) -> dict[str, Any]:
    """Change equipment status from "loaned" to "available" (or vice versa)."""
    resp = _env.update_equipment_availability(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/update_equipment_availability", req.model_dump(), resp)
    return resp


class UpdateEquipmentConditionAndLocationRequest(BaseModel):
    equipment_id: str
    condition: str | None = None
    location: str | None = None

@app.post("/medical_equipment_loan/update_equipment_condition_and_location")
def endpoint_update_equipment_condition_and_location(req: UpdateEquipmentConditionAndLocationRequest) -> dict[str, Any]:
    """Update condition and/or location attributes for equipment when returned."""
    resp = _env.update_equipment_condition_and_location(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/update_equipment_condition_and_location", req.model_dump(), resp)
    return resp


class TriggerOverdueAlertRequest(BaseModel):
    loan_id: str

@app.post("/medical_equipment_loan/trigger_overdue_alert")
def endpoint_trigger_overdue_alert(req: TriggerOverdueAlertRequest) -> dict[str, Any]:
    """Generate an alert if an item is returned late (overdue)."""
    resp = _env.trigger_overdue_alert(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/trigger_overdue_alert", req.model_dump(), resp)
    return resp


class CreateNewLoanTransactionRequest(BaseModel):
    equipment_id: str
    user_id: str
    borrowed_date: str
    due_date: str

@app.post("/medical_equipment_loan/create_new_loan_transaction")
def endpoint_create_new_loan_transaction(req: CreateNewLoanTransactionRequest) -> dict[str, Any]:
    """Record a new borrowing event for an available equipment item."""
    resp = _env.create_new_loan_transaction(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/create_new_loan_transaction", req.model_dump(), resp)
    return resp


class ModifyLoanDueDateRequest(BaseModel):
    loan_id: str
    new_due_date: str

@app.post("/medical_equipment_loan/modify_loan_due_date")
def endpoint_modify_loan_due_date(req: ModifyLoanDueDateRequest) -> dict[str, Any]:
    """Change the due_date for a loan (e.g., extension requests)."""
    resp = _env.modify_loan_due_date(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/modify_loan_due_date", req.model_dump(), resp)
    return resp


class ModifyUserProfileRequest(BaseModel):
    user_id: str
    name: str | None = None
    contact_info: str | None = None
    user_type: str | None = None

@app.post("/medical_equipment_loan/modify_user_profile")
def endpoint_modify_user_profile(req: ModifyUserProfileRequest) -> dict[str, Any]:
    """Update user information if needed (contact details, type, etc.)."""
    resp = _env.modify_user_profile(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/modify_user_profile", req.model_dump(), resp)
    return resp


class DeleteLoanTransactionRequest(BaseModel):
    loan_id: str
    requester_id: str

@app.post("/medical_equipment_loan/delete_loan_transaction")
def endpoint_delete_loan_transaction(req: DeleteLoanTransactionRequest) -> dict[str, Any]:
    """Remove a loan record from the system (admin/staff only)."""
    resp = _env.delete_loan_transaction(**req.model_dump(exclude_none=True))
    _log_call("/medical_equipment_loan/delete_loan_transaction", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/medical_equipment_loan/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/medical_equipment_loan/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9303")))
