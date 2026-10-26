"""Mock Counseling Service Management API service (FastAPI)."""

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

from env_class import CounselingServiceManagementSystem  # noqa: E402

app = FastAPI(title="Mock Counseling Service Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "COUNSELING_SERVICE_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: CounselingServiceManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = CounselingServiceManagementSystem(init_config=init_cfg)
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


@app.post("/counseling_service_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/counseling_service_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/counseling_service_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetCounselingTypeByNameRequest(BaseModel):
    type_name: str

@app.post("/counseling_service_management/get_counseling_type_by_name")
def endpoint_get_counseling_type_by_name(req: GetCounselingTypeByNameRequest) -> dict[str, Any]:
    """Retrieve counseling type entity (type_id, description) by type name (e.g., "general counseling")."""
    resp = _env.get_counseling_type_by_name(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_counseling_type_by_name", req.model_dump(), resp)
    return resp


class GetCounselingTypeByIdRequest(BaseModel):
    type_id: str

@app.post("/counseling_service_management/get_counseling_type_by_id")
def endpoint_get_counseling_type_by_id(req: GetCounselingTypeByIdRequest) -> dict[str, Any]:
    """Retrieve counseling type info using type_id."""
    resp = _env.get_counseling_type_by_id(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_counseling_type_by_id", req.model_dump(), resp)
    return resp


@app.post("/counseling_service_management/list_all_counseling_types")
def endpoint_list_all_counseling_types() -> dict[str, Any]:
    """List all active counseling service types currently offered."""
    resp = _env.list_all_counseling_types()
    _log_call("/counseling_service_management/list_all_counseling_types", {}, resp)
    return resp


class ListCounselorsByExpertiseRequest(BaseModel):
    counseling_type_id: str

@app.post("/counseling_service_management/list_counselors_by_expertise")
def endpoint_list_counselors_by_expertise(req: ListCounselorsByExpertiseRequest) -> dict[str, Any]:
    """Retrieve all counselors whose expertise_areas contain a specific counseling_type_id."""
    resp = _env.list_counselors_by_expertise(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/list_counselors_by_expertise", req.model_dump(), resp)
    return resp


class GetCounselorByIdRequest(BaseModel):
    counselor_id: str

@app.post("/counseling_service_management/get_counselor_by_id")
def endpoint_get_counselor_by_id(req: GetCounselorByIdRequest) -> dict[str, Any]:
    """Get detailed profile and status of a counselor by counselor_id."""
    resp = _env.get_counselor_by_id(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_counselor_by_id", req.model_dump(), resp)
    return resp


@app.post("/counseling_service_management/list_counselors")
def endpoint_list_counselors() -> dict[str, Any]:
    """Retrieve all registered counselors on the system."""
    resp = _env.list_counselors()
    _log_call("/counseling_service_management/list_counselors", {}, resp)
    return resp


class GetCounselorAvailabilityRequest(BaseModel):
    counselor_id: str

@app.post("/counseling_service_management/get_counselor_availability")
def endpoint_get_counselor_availability(req: GetCounselorAvailabilityRequest) -> dict[str, Any]:
    """Retrieve the availability schedule (free slots) for a counselor."""
    resp = _env.get_counselor_availability(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_counselor_availability", req.model_dump(), resp)
    return resp


class ListCounselorsAvailableForTypeRequest(BaseModel):
    counseling_type_id: str

@app.post("/counseling_service_management/list_counselors_available_for_type")
def endpoint_list_counselors_available_for_type(req: ListCounselorsAvailableForTypeRequest) -> dict[str, Any]:
    """List counselors with required expertise and at least one available time slot for a specified counseling type."""
    resp = _env.list_counselors_available_for_type(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/list_counselors_available_for_type", req.model_dump(), resp)
    return resp


class ListAppointmentsByCounselorAndTimeRequest(BaseModel):
    counselor_id: str
    start_time: str
    end_time: str

@app.post("/counseling_service_management/list_appointments_by_counselor_and_time")
def endpoint_list_appointments_by_counselor_and_time(req: ListAppointmentsByCounselorAndTimeRequest) -> dict[str, Any]:
    """Retrieve all appointments for a counselor in a given period (filtering for overlap)."""
    resp = _env.list_appointments_by_counselor_and_time(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/list_appointments_by_counselor_and_time", req.model_dump(), resp)
    return resp


class GetConfirmedAppointmentsForCounselorRequest(BaseModel):
    counselor_id: str

@app.post("/counseling_service_management/get_confirmed_appointments_for_counselor")
def endpoint_get_confirmed_appointments_for_counselor(req: GetConfirmedAppointmentsForCounselorRequest) -> dict[str, Any]:
    """List all "confirmed" appointments assigned to a counselor (for schedule blocking)."""
    resp = _env.get_confirmed_appointments_for_counselor(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_confirmed_appointments_for_counselor", req.model_dump(), resp)
    return resp


class GetClientByIdRequest(BaseModel):
    client_id: str

@app.post("/counseling_service_management/get_client_by_id")
def endpoint_get_client_by_id(req: GetClientByIdRequest) -> dict[str, Any]:
    """Retrieve information on a client by client_id."""
    resp = _env.get_client_by_id(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/get_client_by_id", req.model_dump(), resp)
    return resp


class ListAppointmentsByClientRequest(BaseModel):
    client_id: str

@app.post("/counseling_service_management/list_appointments_by_client")
def endpoint_list_appointments_by_client(req: ListAppointmentsByClientRequest) -> dict[str, Any]:
    """Retrieve all appointments assigned to a given client."""
    resp = _env.list_appointments_by_client(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/list_appointments_by_client", req.model_dump(), resp)
    return resp


class AssignAppointmentRequest(BaseModel):
    counselor_id: str
    client_id: str
    counseling_type_id: str
    scheduled_time: str

@app.post("/counseling_service_management/assign_appointment")
def endpoint_assign_appointment(req: AssignAppointmentRequest) -> dict[str, Any]:
    """Book a new appointment for a client with a specified counselor at a given time and for a specified counseling type."""
    resp = _env.assign_appointment(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/assign_appointment", req.model_dump(), resp)
    return resp


class UpdateAppointmentStatusRequest(BaseModel):
    appointment_id: str
    new_status: str

@app.post("/counseling_service_management/update_appointment_status")
def endpoint_update_appointment_status(req: UpdateAppointmentStatusRequest) -> dict[str, Any]:
    """Change the status of an existing appointment (e.g., from pending to confirmed or cancelled)."""
    resp = _env.update_appointment_status(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/update_appointment_status", req.model_dump(), resp)
    return resp


class ModifyCounselorScheduleRequest(BaseModel):
    counselor_id: str
    add_times: list[str] | None = None
    remove_times: list[str] | None = None

@app.post("/counseling_service_management/modify_counselor_schedule")
def endpoint_modify_counselor_schedule(req: ModifyCounselorScheduleRequest) -> dict[str, Any]:
    """Add or remove time slots from a counselor's availability."""
    resp = _env.modify_counselor_schedule(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/modify_counselor_schedule", req.model_dump(), resp)
    return resp


class UpdateCounselorExpertiseRequest(BaseModel):
    counselor_id: str
    add_types: list[str] | None = None
    remove_types: list[str] | None = None

@app.post("/counseling_service_management/update_counselor_expertise")
def endpoint_update_counselor_expertise(req: UpdateCounselorExpertiseRequest) -> dict[str, Any]:
    """Add or remove counseling types from a counselor's expertise areas."""
    resp = _env.update_counselor_expertise(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/update_counselor_expertise", req.model_dump(), resp)
    return resp


class CancelAppointmentRequest(BaseModel):
    appointment_id: str

@app.post("/counseling_service_management/cancel_appointment")
def endpoint_cancel_appointment(req: CancelAppointmentRequest) -> dict[str, Any]:
    """Cancel a specific appointment, releasing the time slot."""
    resp = _env.cancel_appointment(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/cancel_appointment", req.model_dump(), resp)
    return resp


class DeleteAppointmentRequest(BaseModel):
    appointment_id: str

@app.post("/counseling_service_management/delete_appointment")
def endpoint_delete_appointment(req: DeleteAppointmentRequest) -> dict[str, Any]:
    """Remove an appointment record entirely from the system."""
    resp = _env.delete_appointment(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/delete_appointment", req.model_dump(), resp)
    return resp


class CreateClientRequest(BaseModel):
    client_id: str
    name: str
    contact_info: str

@app.post("/counseling_service_management/create_client")
def endpoint_create_client(req: CreateClientRequest) -> dict[str, Any]:
    """Register a new client on the platform."""
    resp = _env.create_client(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/create_client", req.model_dump(), resp)
    return resp


class UpdateClientInfoRequest(BaseModel):
    client_id: str
    name: str | None = None
    contact_info: str | None = None

@app.post("/counseling_service_management/update_client_info")
def endpoint_update_client_info(req: UpdateClientInfoRequest) -> dict[str, Any]:
    """Modify the details or contact info of an existing client."""
    resp = _env.update_client_info(**req.model_dump(exclude_none=True))
    _log_call("/counseling_service_management/update_client_info", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/counseling_service_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/counseling_service_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9313")))
