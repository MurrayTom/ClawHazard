"""Mock Healthcare Appointment Lab API service (FastAPI)."""

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

from env_class import HealthcareAppointmentLabManagementSystem  # noqa: E402

app = FastAPI(title="Mock Healthcare Appointment Lab API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "HEALTHCARE_APPOINTMENT_LAB_FIXTURES",
    str(_SKILL_DIR / "env_166_rl-task_5_injected.json"),
))

_env: HealthcareAppointmentLabManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = HealthcareAppointmentLabManagementSystem(init_config=init_cfg)
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


@app.post("/healthcare_appointment_lab/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/healthcare_appointment_lab/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/healthcare_appointment_lab/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetAppointmentByIdRequest(BaseModel):
    appointment_id: str

@app.post("/healthcare_appointment_lab/get_appointment_by_id")
def endpoint_get_appointment_by_id(req: GetAppointmentByIdRequest) -> dict[str, Any]:
    """Retrieve details of an appointment using its appointment_id, including linked patient info."""
    resp = _env.get_appointment_by_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_appointment_by_id", req.model_dump(), resp)
    return resp


class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/healthcare_appointment_lab/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve patient details by patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_patient_by_id", req.model_dump(), resp)
    return resp


class GetLabTestsByAppointmentIdRequest(BaseModel):
    appointment_id: str

@app.post("/healthcare_appointment_lab/get_lab_tests_by_appointment_id")
def endpoint_get_lab_tests_by_appointment_id(req: GetLabTestsByAppointmentIdRequest) -> dict[str, Any]:
    """List all lab tests linked to a specific appointment_id."""
    resp = _env.get_lab_tests_by_appointment_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_lab_tests_by_appointment_id", req.model_dump(), resp)
    return resp


class GetLabTestByIdRequest(BaseModel):
    lab_test_id: str

@app.post("/healthcare_appointment_lab/get_lab_test_by_id")
def endpoint_get_lab_test_by_id(req: GetLabTestByIdRequest) -> dict[str, Any]:
    """Retrieve lab test details by lab_test_id."""
    resp = _env.get_lab_test_by_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_lab_test_by_id", req.model_dump(), resp)
    return resp


class GetLabTestResultRequest(BaseModel):
    lab_test_id: str

@app.post("/healthcare_appointment_lab/get_lab_test_result")
def endpoint_get_lab_test_result(req: GetLabTestResultRequest) -> dict[str, Any]:
    """Retrieve the result (if status is "completed") of a lab test by lab_test_id."""
    resp = _env.get_lab_test_result(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_lab_test_result", req.model_dump(), resp)
    return resp


class CheckLabTestStatusRequest(BaseModel):
    lab_test_id: str

@app.post("/healthcare_appointment_lab/check_lab_test_status")
def endpoint_check_lab_test_status(req: CheckLabTestStatusRequest) -> dict[str, Any]:
    """Query the current status of a given lab test (e.g., "pending", "completed")."""
    resp = _env.check_lab_test_status(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/check_lab_test_status", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/healthcare_appointment_lab/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user info (role, linked_patient_id) by user_id."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/get_user_by_id", req.model_dump(), resp)
    return resp


class CheckUserAuthorizationForLabTestRequest(BaseModel):
    user_id: str
    lab_test_id: str

@app.post("/healthcare_appointment_lab/check_user_authorization_for_lab_test")
def endpoint_check_user_authorization_for_lab_test(req: CheckUserAuthorizationForLabTestRequest) -> dict[str, Any]:
    """Verify if the user is permitted to view lab test results (based on role and linkage)."""
    resp = _env.check_user_authorization_for_lab_test(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/check_user_authorization_for_lab_test", req.model_dump(), resp)
    return resp


class IsValidAppointmentIdRequest(BaseModel):
    appointment_id: str

@app.post("/healthcare_appointment_lab/is_valid_appointment_id")
def endpoint_is_valid_appointment_id(req: IsValidAppointmentIdRequest) -> dict[str, Any]:
    """Check whether a given appointment_id exists in the system."""
    resp = _env.is_valid_appointment_id(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/is_valid_appointment_id", req.model_dump(), resp)
    return resp


class IsCompletedLabTestForAppointmentRequest(BaseModel):
    appointment_id: str

@app.post("/healthcare_appointment_lab/is_completed_lab_test_for_appointment")
def endpoint_is_completed_lab_test_for_appointment(req: IsCompletedLabTestForAppointmentRequest) -> dict[str, Any]:
    """Determine if there is any "completed" lab test linked to an appointment."""
    resp = _env.is_completed_lab_test_for_appointment(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/is_completed_lab_test_for_appointment", req.model_dump(), resp)
    return resp


class AddAppointmentRequest(BaseModel):
    appointment_id: str
    patient_id: str
    appointment_date: str
    appointment_type: str
    status: str

@app.post("/healthcare_appointment_lab/add_appointment")
def endpoint_add_appointment(req: AddAppointmentRequest) -> dict[str, Any]:
    """Create a new appointment and link it to a patient."""
    resp = _env.add_appointment(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/add_appointment", req.model_dump(), resp)
    return resp


class UpdateAppointmentStatusRequest(BaseModel):
    appointment_id: str
    new_status: str

@app.post("/healthcare_appointment_lab/update_appointment_status")
def endpoint_update_appointment_status(req: UpdateAppointmentStatusRequest) -> dict[str, Any]:
    """Change the status of an existing appointment (e.g., scheduled, cancelled)."""
    resp = _env.update_appointment_status(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/update_appointment_status", req.model_dump(), resp)
    return resp


class AddLabTestToAppointmentRequest(BaseModel):
    lab_test_id: str
    appointment_id: str
    test_type: str
    test_date: str
    result: str
    status: str

@app.post("/healthcare_appointment_lab/add_lab_test_to_appointment")
def endpoint_add_lab_test_to_appointment(req: AddLabTestToAppointmentRequest) -> dict[str, Any]:
    """Create and link a lab test to an appointment."""
    resp = _env.add_lab_test_to_appointment(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/add_lab_test_to_appointment", req.model_dump(), resp)
    return resp


class UpdateLabTestStatusRequest(BaseModel):
    lab_test_id: str
    new_status: str

@app.post("/healthcare_appointment_lab/update_lab_test_status")
def endpoint_update_lab_test_status(req: UpdateLabTestStatusRequest) -> dict[str, Any]:
    """Change the status of a lab test (e.g., to "completed")."""
    resp = _env.update_lab_test_status(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/update_lab_test_status", req.model_dump(), resp)
    return resp


class RecordLabTestResultRequest(BaseModel):
    lab_test_id: str
    result: str

@app.post("/healthcare_appointment_lab/record_lab_test_result")
def endpoint_record_lab_test_result(req: RecordLabTestResultRequest) -> dict[str, Any]:
    """Write/update the result for a completed lab test."""
    resp = _env.record_lab_test_result(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/record_lab_test_result", req.model_dump(), resp)
    return resp


class AddPatientRequest(BaseModel):
    patient_id: str
    name: str
    date_of_birth: str
    contact_info: str

@app.post("/healthcare_appointment_lab/add_patient")
def endpoint_add_patient(req: AddPatientRequest) -> dict[str, Any]:
    """Register a new patient in the system."""
    resp = _env.add_patient(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/add_patient", req.model_dump(), resp)
    return resp


class UpdatePatientInfoRequest(BaseModel):
    patient_id: str
    name: str | None = None
    date_of_birth: str | None = None
    contact_info: str | None = None

@app.post("/healthcare_appointment_lab/update_patient_info")
def endpoint_update_patient_info(req: UpdatePatientInfoRequest) -> dict[str, Any]:
    """Edit a patient's information and contact details."""
    resp = _env.update_patient_info(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/update_patient_info", req.model_dump(), resp)
    return resp


class AddUserRequest(BaseModel):
    user_id: str
    role: str
    linked_patient_id: str | None = None

@app.post("/healthcare_appointment_lab/add_user")
def endpoint_add_user(req: AddUserRequest) -> dict[str, Any]:
    """Register a new user (patient or staff)."""
    resp = _env.add_user(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/add_user", req.model_dump(), resp)
    return resp


class UpdateUserRoleRequest(BaseModel):
    user_id: str
    new_role: str

@app.post("/healthcare_appointment_lab/update_user_role")
def endpoint_update_user_role(req: UpdateUserRoleRequest) -> dict[str, Any]:
    """Change a user's role (e.g., patient <-> staff)."""
    resp = _env.update_user_role(**req.model_dump(exclude_none=True))
    _log_call("/healthcare_appointment_lab/update_user_role", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/healthcare_appointment_lab/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/healthcare_appointment_lab/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9312")))
