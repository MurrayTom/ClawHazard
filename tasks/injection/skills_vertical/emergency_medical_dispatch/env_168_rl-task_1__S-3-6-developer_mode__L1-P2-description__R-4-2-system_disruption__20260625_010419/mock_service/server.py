"""Mock Emergency Medical Dispatch API service (FastAPI)."""

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

from env_class import EmergencyMedicalDispatchSystem  # noqa: E402

app = FastAPI(title="Mock Emergency Medical Dispatch API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "EMERGENCY_MEDICAL_DISPATCH_FIXTURES",
    str(_SKILL_DIR / "env_168_rl-task_1.json"),
))

_env: EmergencyMedicalDispatchSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = EmergencyMedicalDispatchSystem(init_config=init_cfg)
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


@app.post("/emergency_medical_dispatch/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/emergency_medical_dispatch/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/emergency_medical_dispatch/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetPatientByNameRequest(BaseModel):
    name: str

@app.post("/emergency_medical_dispatch/get_patient_by_name")
def endpoint_get_patient_by_name(req: GetPatientByNameRequest) -> dict[str, Any]:
    """Retrieve patient details (ID, age, medical condition, contact info) by patient name, while preserving privacy."""
    resp = _env.get_patient_by_name(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_patient_by_name", req.model_dump(), resp)
    return resp


class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/emergency_medical_dispatch/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve patient details by unique patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_patient_by_id", req.model_dump(), resp)
    return resp


@app.post("/emergency_medical_dispatch/list_all_patients")
def endpoint_list_all_patients() -> dict[str, Any]:
    """List all registered patients in the system."""
    resp = _env.list_all_patients()
    _log_call("/emergency_medical_dispatch/list_all_patients", {}, resp)
    return resp


class GetLocationByAddressRequest(BaseModel):
    address: str

@app.post("/emergency_medical_dispatch/get_location_by_address")
def endpoint_get_location_by_address(req: GetLocationByAddressRequest) -> dict[str, Any]:
    """Retrieve location details (ID, GPS coordinates) from a provided address."""
    resp = _env.get_location_by_address(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_location_by_address", req.model_dump(), resp)
    return resp


class GetLocationByIdRequest(BaseModel):
    location_id: str

@app.post("/emergency_medical_dispatch/get_location_by_id")
def endpoint_get_location_by_id(req: GetLocationByIdRequest) -> dict[str, Any]:
    """Retrieve location details by location_id."""
    resp = _env.get_location_by_id(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_location_by_id", req.model_dump(), resp)
    return resp


class ListIncidentsByStatusRequest(BaseModel):
    status: str

@app.post("/emergency_medical_dispatch/list_incidents_by_status")
def endpoint_list_incidents_by_status(req: ListIncidentsByStatusRequest) -> dict[str, Any]:
    """List all incidents in the system filtered by their current status (e.g., requested, en route)."""
    resp = _env.list_incidents_by_status(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/list_incidents_by_status", req.model_dump(), resp)
    return resp


class GetIncidentByIdRequest(BaseModel):
    incident_id: str

@app.post("/emergency_medical_dispatch/get_incident_by_id")
def endpoint_get_incident_by_id(req: GetIncidentByIdRequest) -> dict[str, Any]:
    """Retrieve all information about a specific incident using its incident_id."""
    resp = _env.get_incident_by_id(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_incident_by_id", req.model_dump(), resp)
    return resp


@app.post("/emergency_medical_dispatch/list_all_ambulances")
def endpoint_list_all_ambulances() -> dict[str, Any]:
    """List all ambulances and their current status and location."""
    resp = _env.list_all_ambulances()
    _log_call("/emergency_medical_dispatch/list_all_ambulances", {}, resp)
    return resp


@app.post("/emergency_medical_dispatch/get_available_ambulances")
def endpoint_get_available_ambulances() -> dict[str, Any]:
    """Retrieve the list of ambulances that are marked as “available” and not assigned to any active incident."""
    resp = _env.get_available_ambulances()
    _log_call("/emergency_medical_dispatch/get_available_ambulances", {}, resp)
    return resp


class GetAmbulanceByIdRequest(BaseModel):
    ambulance_id: str

@app.post("/emergency_medical_dispatch/get_ambulance_by_id")
def endpoint_get_ambulance_by_id(req: GetAmbulanceByIdRequest) -> dict[str, Any]:
    """Retrieve all details about a specific ambulance using its ambulance_id."""
    resp = _env.get_ambulance_by_id(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_ambulance_by_id", req.model_dump(), resp)
    return resp


class GetAmbulanceCurrentIncidentRequest(BaseModel):
    ambulance_id: str

@app.post("/emergency_medical_dispatch/get_ambulance_current_incident")
def endpoint_get_ambulance_current_incident(req: GetAmbulanceCurrentIncidentRequest) -> dict[str, Any]:
    """Find out which incident, if any, a given ambulance is currently assigned to."""
    resp = _env.get_ambulance_current_incident(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/get_ambulance_current_incident", req.model_dump(), resp)
    return resp


class CheckIncidentLocationValidityRequest(BaseModel):
    address: str = ""
    gps_coordinates: str = ""

@app.post("/emergency_medical_dispatch/check_incident_location_validity")
def endpoint_check_incident_location_validity(req: CheckIncidentLocationValidityRequest) -> dict[str, Any]:
    """Verify that a location (by address or GPS) meets criteria for incident creation."""
    resp = _env.check_incident_location_validity(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/check_incident_location_validity", req.model_dump(), resp)
    return resp


class CreateIncidentRequest(BaseModel):
    incident_id: str
    type: str
    location_id: str
    timestamp: str
    patient_id: str

@app.post("/emergency_medical_dispatch/create_incident")
def endpoint_create_incident(req: CreateIncidentRequest) -> dict[str, Any]:
    """Create a new emergency incident, validating all required fields including precise location and patient association."""
    resp = _env.create_incident(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/create_incident", req.model_dump(), resp)
    return resp


class AssignAmbulanceToIncidentRequest(BaseModel):
    incident_id: str
    ambulance_id: str

@app.post("/emergency_medical_dispatch/assign_ambulance_to_incident")
def endpoint_assign_ambulance_to_incident(req: AssignAmbulanceToIncidentRequest) -> dict[str, Any]:
    """Assign an available ambulance to an incident, respecting assignment and ambulance availability constraints."""
    resp = _env.assign_ambulance_to_incident(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/assign_ambulance_to_incident", req.model_dump(), resp)
    return resp


class UpdateIncidentStatusRequest(BaseModel):
    incident_id: str
    new_status: str

@app.post("/emergency_medical_dispatch/update_incident_status")
def endpoint_update_incident_status(req: UpdateIncidentStatusRequest) -> dict[str, Any]:
    """Change the status of an incident to reflect ambulance progress ("requested", "en route", "arrived", "completed")."""
    resp = _env.update_incident_status(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/update_incident_status", req.model_dump(), resp)
    return resp


class UpdateAmbulanceAvailabilityRequest(BaseModel):
    ambulance_id: str
    availability_status: str

@app.post("/emergency_medical_dispatch/update_ambulance_availability")
def endpoint_update_ambulance_availability(req: UpdateAmbulanceAvailabilityRequest) -> dict[str, Any]:
    """Set ambulance availability status (“available”/“unavailable”) when assigned to or released from an incident."""
    resp = _env.update_ambulance_availability(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/update_ambulance_availability", req.model_dump(), resp)
    return resp


class ReleaseAmbulanceFromIncidentRequest(BaseModel):
    incident_id: str

@app.post("/emergency_medical_dispatch/release_ambulance_from_incident")
def endpoint_release_ambulance_from_incident(req: ReleaseAmbulanceFromIncidentRequest) -> dict[str, Any]:
    """Remove ambulance assignment from incident upon completion, making ambulance available again."""
    resp = _env.release_ambulance_from_incident(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/release_ambulance_from_incident", req.model_dump(), resp)
    return resp


class UpdateAmbulanceLocationRequest(BaseModel):
    ambulance_id: str
    new_location_id: str

@app.post("/emergency_medical_dispatch/update_ambulance_location")
def endpoint_update_ambulance_location(req: UpdateAmbulanceLocationRequest) -> dict[str, Any]:
    """Change the current location of an ambulance based on incident progress or repositioning."""
    resp = _env.update_ambulance_location(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/update_ambulance_location", req.model_dump(), resp)
    return resp


class ModifyIncidentDetailsRequest(BaseModel):
    incident_id: str
    type: str | None = None
    location: str | None = None
    patient_id: str | None = None

@app.post("/emergency_medical_dispatch/modify_incident_details")
def endpoint_modify_incident_details(req: ModifyIncidentDetailsRequest) -> dict[str, Any]:
    """Edit or update incident details (type, location, patient info) if correction/updates are needed."""
    resp = _env.modify_incident_details(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/modify_incident_details", req.model_dump(), resp)
    return resp


class AnonymizePatientInfoRequest(BaseModel):
    patient_id: str

@app.post("/emergency_medical_dispatch/anonymize_patient_info")
def endpoint_anonymize_patient_info(req: AnonymizePatientInfoRequest) -> dict[str, Any]:
    """Apply privacy safeguards by redacting personally identifiable data during queries or data export."""
    resp = _env.anonymize_patient_info(**req.model_dump(exclude_none=True))
    _log_call("/emergency_medical_dispatch/anonymize_patient_info", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/emergency_medical_dispatch/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/emergency_medical_dispatch/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9314")))
