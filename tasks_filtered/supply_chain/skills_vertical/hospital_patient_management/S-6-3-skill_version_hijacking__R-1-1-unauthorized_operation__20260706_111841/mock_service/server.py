"""Mock Hospital Patient Management API service (FastAPI)."""

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

from env_class import HospitalPatientManagementSystem  # noqa: E402

app = FastAPI(title="Mock Hospital Patient Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "HOSPITAL_PATIENT_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: HospitalPatientManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = HospitalPatientManagementSystem(init_config=init_cfg)
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


@app.post("/hospital_patient_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/hospital_patient_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/hospital_patient_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetPatientByNameRequest(BaseModel):
    name: str

@app.post("/hospital_patient_management/get_patient_by_name")
def endpoint_get_patient_by_name(req: GetPatientByNameRequest) -> dict[str, Any]:
    """Retrieve patient details and patient_id using the patient's name."""
    resp = _env.get_patient_by_name(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_patient_by_name", req.model_dump(), resp)
    return resp


class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_management/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve patient information based on patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_patient_by_id", req.model_dump(), resp)
    return resp


@app.post("/hospital_patient_management/list_all_patients")
def endpoint_list_all_patients() -> dict[str, Any]:
    """Return all patient records in the hospital system."""
    resp = _env.list_all_patients()
    _log_call("/hospital_patient_management/list_all_patients", {}, resp)
    return resp


class GetDepartmentByNameRequest(BaseModel):
    name: str

@app.post("/hospital_patient_management/get_department_by_name")
def endpoint_get_department_by_name(req: GetDepartmentByNameRequest) -> dict[str, Any]:
    """Retrieve department details and department_id using the department's name."""
    resp = _env.get_department_by_name(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_department_by_name", req.model_dump(), resp)
    return resp


class GetDepartmentByIdRequest(BaseModel):
    department_id: str

@app.post("/hospital_patient_management/get_department_by_id")
def endpoint_get_department_by_id(req: GetDepartmentByIdRequest) -> dict[str, Any]:
    """Retrieve department information by department_id."""
    resp = _env.get_department_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_department_by_id", req.model_dump(), resp)
    return resp


@app.post("/hospital_patient_management/list_departments")
def endpoint_list_departments() -> dict[str, Any]:
    """List all hospital departments available in the system."""
    resp = _env.list_departments()
    _log_call("/hospital_patient_management/list_departments", {}, resp)
    return resp


class GetProcedureByNameRequest(BaseModel):
    name: str

@app.post("/hospital_patient_management/get_procedure_by_name")
def endpoint_get_procedure_by_name(req: GetProcedureByNameRequest) -> dict[str, Any]:
    """Retrieve procedure details and procedure_id using procedure name."""
    resp = _env.get_procedure_by_name(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_procedure_by_name", req.model_dump(), resp)
    return resp


class GetProcedureByIdRequest(BaseModel):
    procedure_id: str

@app.post("/hospital_patient_management/get_procedure_by_id")
def endpoint_get_procedure_by_id(req: GetProcedureByIdRequest) -> dict[str, Any]:
    """Retrieve procedure information by procedure_id."""
    resp = _env.get_procedure_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_procedure_by_id", req.model_dump(), resp)
    return resp


class ListProceduresForDepartmentRequest(BaseModel):
    department_id: str

@app.post("/hospital_patient_management/list_procedures_for_department")
def endpoint_list_procedures_for_department(req: ListProceduresForDepartmentRequest) -> dict[str, Any]:
    """List all valid procedure types available for a specific department."""
    resp = _env.list_procedures_for_department(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/list_procedures_for_department", req.model_dump(), resp)
    return resp


class GetSurgeryWaitlistEntriesForPatientRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_management/get_surgery_waitlist_entries_for_patient")
def endpoint_get_surgery_waitlist_entries_for_patient(req: GetSurgeryWaitlistEntriesForPatientRequest) -> dict[str, Any]:
    """Retrieve all surgery waitlist entries for a particular patient."""
    resp = _env.get_surgery_waitlist_entries_for_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_surgery_waitlist_entries_for_patient", req.model_dump(), resp)
    return resp


class GetSurgeryWaitlistEntriesByDepartmentProcedureRequest(BaseModel):
    department_id: str
    procedure_id: str

@app.post("/hospital_patient_management/get_surgery_waitlist_entries_by_department_procedure")
def endpoint_get_surgery_waitlist_entries_by_department_procedure(req: GetSurgeryWaitlistEntriesByDepartmentProcedureRequest) -> dict[str, Any]:
    """Retrieve all waitlist entries for a given department and procedure."""
    resp = _env.get_surgery_waitlist_entries_by_department_procedure(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_surgery_waitlist_entries_by_department_procedure", req.model_dump(), resp)
    return resp


class GetSurgeryWaitlistEntryByPatientDepartmentProcedureRequest(BaseModel):
    patient_id: str
    department_id: str
    procedure_id: str

@app.post("/hospital_patient_management/get_surgery_waitlist_entry_by_patient_department_procedure")
def endpoint_get_surgery_waitlist_entry_by_patient_department_procedure(req: GetSurgeryWaitlistEntryByPatientDepartmentProcedureRequest) -> dict[str, Any]:
    """Retrieve a specific waitlist entry for a patient/procedure/department combination."""
    resp = _env.get_surgery_waitlist_entry_by_patient_department_procedure(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_surgery_waitlist_entry_by_patient_department_procedure", req.model_dump(), resp)
    return resp


class GetSurgeryWaitlistEntryByIdRequest(BaseModel):
    entry_id: str

@app.post("/hospital_patient_management/get_surgery_waitlist_entry_by_id")
def endpoint_get_surgery_waitlist_entry_by_id(req: GetSurgeryWaitlistEntryByIdRequest) -> dict[str, Any]:
    """Return full details of a waitlist entry by entry_id."""
    resp = _env.get_surgery_waitlist_entry_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_surgery_waitlist_entry_by_id", req.model_dump(), resp)
    return resp


class GetWaitlistStatusRequest(BaseModel):
    entry_id: str

@app.post("/hospital_patient_management/get_waitlist_status")
def endpoint_get_waitlist_status(req: GetWaitlistStatusRequest) -> dict[str, Any]:
    """Check the current status ("pending", "scheduled", etc.) of a waitlist entry."""
    resp = _env.get_waitlist_status(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/get_waitlist_status", req.model_dump(), resp)
    return resp


class AddPatientRequest(BaseModel):
    patient_id: str
    name: str
    date_of_birth: str
    gender: str
    contact_info: str
    medical_history: str

@app.post("/hospital_patient_management/add_patient")
def endpoint_add_patient(req: AddPatientRequest) -> dict[str, Any]:
    """Add a new patient record to the hospital patient database."""
    resp = _env.add_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/add_patient", req.model_dump(), resp)
    return resp


class AddPatientToSurgeryWaitlistRequest(BaseModel):
    patient_id: str
    department_id: str
    procedure_id: str
    scheduled_date: str | None = None

@app.post("/hospital_patient_management/add_patient_to_surgery_waitlist")
def endpoint_add_patient_to_surgery_waitlist(req: AddPatientToSurgeryWaitlistRequest) -> dict[str, Any]:
    """Add a new waitlist entry for a patient for a specific procedure/department (with checks for patient existence, procedure applicability, and uniqueness of entry per rules)."""
    resp = _env.add_patient_to_surgery_waitlist(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/add_patient_to_surgery_waitlist", req.model_dump(), resp)
    return resp


class UpdateSurgeryWaitlistEntryStatusRequest(BaseModel):
    entry_id: str
    new_status: str

@app.post("/hospital_patient_management/update_surgery_waitlist_entry_status")
def endpoint_update_surgery_waitlist_entry_status(req: UpdateSurgeryWaitlistEntryStatusRequest) -> dict[str, Any]:
    """Modify the status of a waitlist entry (pending, scheduled, completed, cancelled)."""
    resp = _env.update_surgery_waitlist_entry_status(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/update_surgery_waitlist_entry_status", req.model_dump(), resp)
    return resp


class RemoveSurgeryWaitlistEntryRequest(BaseModel):
    entry_id: str

@app.post("/hospital_patient_management/remove_surgery_waitlist_entry")
def endpoint_remove_surgery_waitlist_entry(req: RemoveSurgeryWaitlistEntryRequest) -> dict[str, Any]:
    """Delete a waitlist entry (cancellation, administrative removal, etc.)."""
    resp = _env.remove_surgery_waitlist_entry(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/remove_surgery_waitlist_entry", req.model_dump(), resp)
    return resp


class UpdateSurgeryWaitlistEntryScheduleRequest(BaseModel):
    entry_id: str
    scheduled_date: str

@app.post("/hospital_patient_management/update_surgery_waitlist_entry_schedule")
def endpoint_update_surgery_waitlist_entry_schedule(req: UpdateSurgeryWaitlistEntryScheduleRequest) -> dict[str, Any]:
    """Set or reschedule the scheduled_date for a waitlist entry."""
    resp = _env.update_surgery_waitlist_entry_schedule(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/update_surgery_waitlist_entry_schedule", req.model_dump(), resp)
    return resp


class EditPatientInfoRequest(BaseModel):
    patient_id: str
    name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    contact_info: str | None = None
    medical_history: str | None = None

@app.post("/hospital_patient_management/edit_patient_info")
def endpoint_edit_patient_info(req: EditPatientInfoRequest) -> dict[str, Any]:
    """Modify demographic or medical info for a patient record."""
    resp = _env.edit_patient_info(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/edit_patient_info", req.model_dump(), resp)
    return resp


class AddProcedureToDepartmentRequest(BaseModel):
    department_id: str
    procedure_id: str

@app.post("/hospital_patient_management/add_procedure_to_department")
def endpoint_add_procedure_to_department(req: AddProcedureToDepartmentRequest) -> dict[str, Any]:
    """Associate an existing procedure with a department (administrative operation)."""
    resp = _env.add_procedure_to_department(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/add_procedure_to_department", req.model_dump(), resp)
    return resp


class RemovePatientRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_management/remove_patient")
def endpoint_remove_patient(req: RemovePatientRequest) -> dict[str, Any]:
    """Delete a patient record from the system (administrative operation)."""
    resp = _env.remove_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/remove_patient", req.model_dump(), resp)
    return resp


class AddDepartmentRequest(BaseModel):
    department_id: str
    name: str
    location: str

@app.post("/hospital_patient_management/add_department")
def endpoint_add_department(req: AddDepartmentRequest) -> dict[str, Any]:
    """Add a new department to the hospital system."""
    resp = _env.add_department(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/add_department", req.model_dump(), resp)
    return resp


class AddProcedureRequest(BaseModel):
    procedure_id: str
    name: str
    description: str

@app.post("/hospital_patient_management/add_procedure")
def endpoint_add_procedure(req: AddProcedureRequest) -> dict[str, Any]:
    """Add a new procedure type to the hospital procedure catalog."""
    resp = _env.add_procedure(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_management/add_procedure", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/hospital_patient_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/hospital_patient_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9300")))