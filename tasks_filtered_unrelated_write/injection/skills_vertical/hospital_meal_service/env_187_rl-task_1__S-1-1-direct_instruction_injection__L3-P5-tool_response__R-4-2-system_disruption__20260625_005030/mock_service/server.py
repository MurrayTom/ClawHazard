"""Mock Hospital Meal Service API service (FastAPI)."""

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

from env_class import HospitalMealManagementSystem  # noqa: E402

app = FastAPI(title="Mock Hospital Meal Service API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "HOSPITAL_MEAL_SERVICE_FIXTURES",
    str(_SKILL_DIR / "env_187_rl-task_1_injected.json"),
))

_env: HospitalMealManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = HospitalMealManagementSystem(init_config=init_cfg)
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


@app.post("/hospital_meal_service/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/hospital_meal_service/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/hospital_meal_service/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/hospital_meal_service/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve full profile and dietary restrictions of a patient by patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_patient_by_id", req.model_dump(), resp)
    return resp


class GetPatientsByConditionRequest(BaseModel):
    condition: str

@app.post("/hospital_meal_service/get_patients_by_condition")
def endpoint_get_patients_by_condition(req: GetPatientsByConditionRequest) -> dict[str, Any]:
    """List patients filtered by a specific medical condition (e.g., celiac disease)."""
    resp = _env.get_patients_by_condition(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_patients_by_condition", req.model_dump(), resp)
    return resp


class GetPatientDietaryRestrictionsRequest(BaseModel):
    patient_id: str

@app.post("/hospital_meal_service/get_patient_dietary_restrictions")
def endpoint_get_patient_dietary_restrictions(req: GetPatientDietaryRestrictionsRequest) -> dict[str, Any]:
    """Retrieve dietary restrictions for a specified patient."""
    resp = _env.get_patient_dietary_restrictions(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_patient_dietary_restrictions", req.model_dump(), resp)
    return resp


@app.post("/hospital_meal_service/list_all_meals")
def endpoint_list_all_meals() -> dict[str, Any]:
    """Retrieve the full list of available meals in the system."""
    resp = _env.list_all_meals()
    _log_call("/hospital_meal_service/list_all_meals", {}, resp)
    return resp


class GetMealByIdRequest(BaseModel):
    meal_id: str

@app.post("/hospital_meal_service/get_meal_by_id")
def endpoint_get_meal_by_id(req: GetMealByIdRequest) -> dict[str, Any]:
    """Get full meal details (properties, allergens) for a specified meal_id."""
    resp = _env.get_meal_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_meal_by_id", req.model_dump(), resp)
    return resp


class GetMealsByPropertyRequest(BaseModel):
    property: str

@app.post("/hospital_meal_service/get_meals_by_property")
def endpoint_get_meals_by_property(req: GetMealsByPropertyRequest) -> dict[str, Any]:
    """List meals matching certain dietary properties (e.g., gluten-free)."""
    resp = _env.get_meals_by_property(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_meals_by_property", req.model_dump(), resp)
    return resp


class GetMealsByAllergenRequest(BaseModel):
    allergen: str
    present: bool

@app.post("/hospital_meal_service/get_meals_by_allergen")
def endpoint_get_meals_by_allergen(req: GetMealsByAllergenRequest) -> dict[str, Any]:
    """Filter meals by absence/presence of allergenic ingredients."""
    resp = _env.get_meals_by_allergen(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_meals_by_allergen", req.model_dump(), resp)
    return resp


class GetMealScheduleByDatetimeRequest(BaseModel):
    scheduled_datetime: str

@app.post("/hospital_meal_service/get_meal_schedule_by_datetime")
def endpoint_get_meal_schedule_by_datetime(req: GetMealScheduleByDatetimeRequest) -> dict[str, Any]:
    """Retrieve meal schedule info for a specific date/time."""
    resp = _env.get_meal_schedule_by_datetime(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_meal_schedule_by_datetime", req.model_dump(), resp)
    return resp


class GetMealsAvailableForPatientAtDatetimeRequest(BaseModel):
    patient_id: str
    scheduled_datetime: str

@app.post("/hospital_meal_service/get_meals_available_for_patient_at_datetime")
def endpoint_get_meals_available_for_patient_at_datetime(req: GetMealsAvailableForPatientAtDatetimeRequest) -> dict[str, Any]:
    """Return a list of meals available for a specific patient at a specified datetime, supporting dietary compatibility and schedule constraints."""
    resp = _env.get_meals_available_for_patient_at_datetime(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_meals_available_for_patient_at_datetime", req.model_dump(), resp)
    return resp


class GetStaffByRoleRequest(BaseModel):
    role: str

@app.post("/hospital_meal_service/get_staff_by_role")
def endpoint_get_staff_by_role(req: GetStaffByRoleRequest) -> dict[str, Any]:
    """List staff members filtered by their role (dietitian, nurse, etc.)."""
    resp = _env.get_staff_by_role(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/get_staff_by_role", req.model_dump(), resp)
    return resp


class AssignMealToPatientRequest(BaseModel):
    patient_id: str
    meal_id: str
    scheduled_datetime: str

@app.post("/hospital_meal_service/assign_meal_to_patient")
def endpoint_assign_meal_to_patient(req: AssignMealToPatientRequest) -> dict[str, Any]:
    """Assign a scheduled, compatible meal to a patient for a specific time."""
    resp = _env.assign_meal_to_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/assign_meal_to_patient", req.model_dump(), resp)
    return resp


class UpdatePatientDietaryRestrictionsRequest(BaseModel):
    patient_id: str
    new_dietary_restrictions: list[str]

@app.post("/hospital_meal_service/update_patient_dietary_restrictions")
def endpoint_update_patient_dietary_restrictions(req: UpdatePatientDietaryRestrictionsRequest) -> dict[str, Any]:
    """Modify dietary restrictions for a patient profile."""
    resp = _env.update_patient_dietary_restrictions(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/update_patient_dietary_restrictions", req.model_dump(), resp)
    return resp


class UpdateMealPropertiesRequest(BaseModel):
    meal_id: str
    dietary_properties: list[str]

@app.post("/hospital_meal_service/update_meal_properties")
def endpoint_update_meal_properties(req: UpdateMealPropertiesRequest) -> dict[str, Any]:
    """Change dietary properties associated with a meal."""
    resp = _env.update_meal_properties(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/update_meal_properties", req.model_dump(), resp)
    return resp


class UpdateMealAllergenInfoRequest(BaseModel):
    meal_id: str
    new_allergen_info: str

@app.post("/hospital_meal_service/update_meal_allergen_info")
def endpoint_update_meal_allergen_info(req: UpdateMealAllergenInfoRequest) -> dict[str, Any]:
    """Modify the allergen info for food safety compliance."""
    resp = _env.update_meal_allergen_info(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/update_meal_allergen_info", req.model_dump(), resp)
    return resp


class UpdateMealScheduleAvailabilityRequest(BaseModel):
    meal_id: str
    scheduled_datetime: str
    availability_sta: str

@app.post("/hospital_meal_service/update_meal_schedule_availability")
def endpoint_update_meal_schedule_availability(req: UpdateMealScheduleAvailabilityRequest) -> dict[str, Any]:
    """Set or modify the availability status of a meal at a given time."""
    resp = _env.update_meal_schedule_availability(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/update_meal_schedule_availability", req.model_dump(), resp)
    return resp


class CreateMealScheduleRequest(BaseModel):
    meal_id: str
    scheduled_datetime: str
    availability_sta: str

@app.post("/hospital_meal_service/create_meal_schedule")
def endpoint_create_meal_schedule(req: CreateMealScheduleRequest) -> dict[str, Any]:
    """Add a new schedule entry for a meal (new time, availability)."""
    resp = _env.create_meal_schedule(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/create_meal_schedule", req.model_dump(), resp)
    return resp


class RemoveMealScheduleRequest(BaseModel):
    meal_id: str
    scheduled_datetime: str

@app.post("/hospital_meal_service/remove_meal_schedule")
def endpoint_remove_meal_schedule(req: RemoveMealScheduleRequest) -> dict[str, Any]:
    """Delete a scheduled meal time entry from the system."""
    resp = _env.remove_meal_schedule(**req.model_dump(exclude_none=True))
    _log_call("/hospital_meal_service/remove_meal_schedule", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/hospital_meal_service/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/hospital_meal_service/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9327")))
