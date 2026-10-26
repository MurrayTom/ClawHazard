"""Mock Employee Benefits Enrollment API service (FastAPI)."""

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

from env_class import EmployeeBenefitsEnrollmentPortal  # noqa: E402

app = FastAPI(title="Mock Employee Benefits Enrollment API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "EMPLOYEE_BENEFITS_ENROLLMENT_FIXTURES",
    str(_SKILL_DIR / "env_174_rl-task_2_injected.json"),
))

_env: EmployeeBenefitsEnrollmentPortal | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = EmployeeBenefitsEnrollmentPortal(init_config=init_cfg)
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


@app.post("/employee_benefits_enrollment/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/employee_benefits_enrollment/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/employee_benefits_enrollment/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetEmployeeByIdRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/get_employee_by_id")
def endpoint_get_employee_by_id(req: GetEmployeeByIdRequest) -> dict[str, Any]:
    """Retrieve info for a specific employee by ID."""
    resp = _env.get_employee_by_id(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/get_employee_by_id", req.model_dump(), resp)
    return resp


@app.post("/employee_benefits_enrollment/list_active_enrollment_periods")
def endpoint_list_active_enrollment_periods() -> dict[str, Any]:
    """Get all currently open enrollment periods (with is_active = True)."""
    resp = _env.list_active_enrollment_periods()
    _log_call("/employee_benefits_enrollment/list_active_enrollment_periods", {}, resp)
    return resp


@app.post("/employee_benefits_enrollment/get_current_active_enrollment_period")
def endpoint_get_current_active_enrollment_period() -> dict[str, Any]:
    """Return the (single) currently open enrollment period if one exists."""
    resp = _env.get_current_active_enrollment_period()
    _log_call("/employee_benefits_enrollment/get_current_active_enrollment_period", {}, resp)
    return resp


class GetEmployeeEligibilityProfileRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/get_employee_eligibility_profile")
def endpoint_get_employee_eligibility_profile(req: GetEmployeeEligibilityProfileRequest) -> dict[str, Any]:
    """Query the eligibility profile string of an employee."""
    resp = _env.get_employee_eligibility_profile(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/get_employee_eligibility_profile", req.model_dump(), resp)
    return resp


@app.post("/employee_benefits_enrollment/list_all_benefit_plans")
def endpoint_list_all_benefit_plans() -> dict[str, Any]:
    """Get all available benefit plans in the system (unfiltered)."""
    resp = _env.list_all_benefit_plans()
    _log_call("/employee_benefits_enrollment/list_all_benefit_plans", {}, resp)
    return resp


class ListBenefitPlansByTypeRequest(BaseModel):
    plan_type: str

@app.post("/employee_benefits_enrollment/list_benefit_plans_by_type")
def endpoint_list_benefit_plans_by_type(req: ListBenefitPlansByTypeRequest) -> dict[str, Any]:
    """Get benefit plans filtered by plan_type (e.g., "health insurance")."""
    resp = _env.list_benefit_plans_by_type(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/list_benefit_plans_by_type", req.model_dump(), resp)
    return resp


class ListEligibleBenefitPlansForEmployeeRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/list_eligible_benefit_plans_for_employee")
def endpoint_list_eligible_benefit_plans_for_employee(req: ListEligibleBenefitPlansForEmployeeRequest) -> dict[str, Any]:
    """List benefit plans that match the employee's eligibility profile and are available to them."""
    resp = _env.list_eligible_benefit_plans_for_employee(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/list_eligible_benefit_plans_for_employee", req.model_dump(), resp)
    return resp


class ListAvailablePlanOptionsForEmployeeInOpenEnrollmentRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/list_available_plan_options_for_employee_in_open_enrollment")
def endpoint_list_available_plan_options_for_employee_in_open_enrollment(req: ListAvailablePlanOptionsForEmployeeInOpenEnrollmentRequest) -> dict[str, Any]:
    """List benefit plans that are both eligible for the employee and selectable in the current active enrollment period."""
    resp = _env.list_available_plan_options_for_employee_in_open_enrollment(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/list_available_plan_options_for_employee_in_open_enrollment", req.model_dump(), resp)
    return resp


class GetPlanDetailsRequest(BaseModel):
    plan_id: str

@app.post("/employee_benefits_enrollment/get_plan_details")
def endpoint_get_plan_details(req: GetPlanDetailsRequest) -> dict[str, Any]:
    """Retrieve full details for a benefit plan by plan_id."""
    resp = _env.get_plan_details(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/get_plan_details", req.model_dump(), resp)
    return resp


class GetEmployeePlanSelectionsInPeriodRequest(BaseModel):
    employee_id: str
    enrollment_period_id: str

@app.post("/employee_benefits_enrollment/get_employee_plan_selections_in_period")
def endpoint_get_employee_plan_selections_in_period(req: GetEmployeePlanSelectionsInPeriodRequest) -> dict[str, Any]:
    """List employee’s plan selections for a given enrollment period."""
    resp = _env.get_employee_plan_selections_in_period(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/get_employee_plan_selections_in_period", req.model_dump(), resp)
    return resp


class GetEmployeeCurrentSelectionRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/get_employee_current_selection")
def endpoint_get_employee_current_selection(req: GetEmployeeCurrentSelectionRequest) -> dict[str, Any]:
    """Get the currently active plan selection for an employee (if any) during the active enrollment period."""
    resp = _env.get_employee_current_selection(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/get_employee_current_selection", req.model_dump(), resp)
    return resp


class EnrollEmployeeInPlanRequest(BaseModel):
    employee_id: str
    plan_id: str
    enrollment_period_id: str
    selection_date: str

@app.post("/employee_benefits_enrollment/enroll_employee_in_plan")
def endpoint_enroll_employee_in_plan(req: EnrollEmployeeInPlanRequest) -> dict[str, Any]:
    """Add or update an employee’s plan selection during an active enrollment period (must pass eligibility and active period checks)."""
    resp = _env.enroll_employee_in_plan(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/enroll_employee_in_plan", req.model_dump(), resp)
    return resp


class ChangeEmployeePlanSelectionRequest(BaseModel):
    employee_id: str
    new_plan_id: str

@app.post("/employee_benefits_enrollment/change_employee_plan_selection")
def endpoint_change_employee_plan_selection(req: ChangeEmployeePlanSelectionRequest) -> dict[str, Any]:
    """Modify/replace the selected plan for an employee within the current enrollment period."""
    resp = _env.change_employee_plan_selection(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/change_employee_plan_selection", req.model_dump(), resp)
    return resp


class WithdrawEmployeePlanSelectionRequest(BaseModel):
    employee_id: str

@app.post("/employee_benefits_enrollment/withdraw_employee_plan_selection")
def endpoint_withdraw_employee_plan_selection(req: WithdrawEmployeePlanSelectionRequest) -> dict[str, Any]:
    """Remove an employee’s plan selection (e.g., if they wish to opt out) for the current enrollment period."""
    resp = _env.withdraw_employee_plan_selection(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/withdraw_employee_plan_selection", req.model_dump(), resp)
    return resp


class CreateNewEnrollmentPeriodRequest(BaseModel):
    enrollment_period_id: str
    start_date: str
    end_date: str
    is_active: bool

@app.post("/employee_benefits_enrollment/create_new_enrollment_period")
def endpoint_create_new_enrollment_period(req: CreateNewEnrollmentPeriodRequest) -> dict[str, Any]:
    """Add a new enrollment period to the portal (admin action)."""
    resp = _env.create_new_enrollment_period(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/create_new_enrollment_period", req.model_dump(), resp)
    return resp


class ActivateEnrollmentPeriodRequest(BaseModel):
    enrollment_period_id: str

@app.post("/employee_benefits_enrollment/activate_enrollment_period")
def endpoint_activate_enrollment_period(req: ActivateEnrollmentPeriodRequest) -> dict[str, Any]:
    """Set an enrollment period’s status to active."""
    resp = _env.activate_enrollment_period(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/activate_enrollment_period", req.model_dump(), resp)
    return resp


class DeactivateEnrollmentPeriodRequest(BaseModel):
    enrollment_period_id: str

@app.post("/employee_benefits_enrollment/deactivate_enrollment_period")
def endpoint_deactivate_enrollment_period(req: DeactivateEnrollmentPeriodRequest) -> dict[str, Any]:
    """Set an enrollment period’s status to inactive."""
    resp = _env.deactivate_enrollment_period(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/deactivate_enrollment_period", req.model_dump(), resp)
    return resp


class AddBenefitPlanRequest(BaseModel):
    plan_id: str
    plan_type: str
    name: str
    coverage_details: str
    premiums: float
    eligibility_criteria: str

@app.post("/employee_benefits_enrollment/add_benefit_plan")
def endpoint_add_benefit_plan(req: AddBenefitPlanRequest) -> dict[str, Any]:
    """Add a new benefit plan to the catalog."""
    resp = _env.add_benefit_plan(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/add_benefit_plan", req.model_dump(), resp)
    return resp


class UpdateBenefitPlanRequest(BaseModel):
    plan_id: str
    plan_type: str | None = None
    name: str | None = None
    coverage_details: str | None = None
    premiums: float | None = None
    eligibility_criteria: str | None = None

@app.post("/employee_benefits_enrollment/update_benefit_plan")
def endpoint_update_benefit_plan(req: UpdateBenefitPlanRequest) -> dict[str, Any]:
    """Modify the attributes/details of a benefit plan (admin action)."""
    resp = _env.update_benefit_plan(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/update_benefit_plan", req.model_dump(), resp)
    return resp


class RemovePlanFromEmployeeSelectionRequest(BaseModel):
    employee_id: str
    enrollment_period_id: str
    plan_id: str

@app.post("/employee_benefits_enrollment/remove_plan_from_employee_selection")
def endpoint_remove_plan_from_employee_selection(req: RemovePlanFromEmployeeSelectionRequest) -> dict[str, Any]:
    """Remove a specific plan selection record for an employee (admin, or self-service if allowed)."""
    resp = _env.remove_plan_from_employee_selection(**req.model_dump(exclude_none=True))
    _log_call("/employee_benefits_enrollment/remove_plan_from_employee_selection", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/employee_benefits_enrollment/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/employee_benefits_enrollment/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9318")))
