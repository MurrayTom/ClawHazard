"""Mock Hospital Patient Discharge API service (FastAPI)."""

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

app = FastAPI(title="Mock Hospital Patient Discharge API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "HOSPITAL_PATIENT_DISCHARGE_FIXTURES",
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


@app.post("/hospital_patient_discharge/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/hospital_patient_discharge/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/hospital_patient_discharge/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetPatientByNameRequest(BaseModel):
    name: str

@app.post("/hospital_patient_discharge/get_patient_by_name")
def endpoint_get_patient_by_name(req: GetPatientByNameRequest) -> dict[str, Any]:
    """Retrieve patient info using patient's name."""
    resp = _env.get_patient_by_name(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_by_name", req.model_dump(), resp)
    return resp


class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve patient info by unique patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_by_id", req.model_dump(), resp)
    return resp


class GetPatientCurrentStatusRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_patient_current_status")
def endpoint_get_patient_current_status(req: GetPatientCurrentStatusRequest) -> dict[str, Any]:
    """Get the current status of a patient (e.g., "admitted", "medically ready", etc.)."""
    resp = _env.get_patient_current_status(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_current_status", req.model_dump(), resp)
    return resp


class GetPatientMedicalRecordRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_patient_medical_record")
def endpoint_get_patient_medical_record(req: GetPatientMedicalRecordRequest) -> dict[str, Any]:
    """Retrieve the medical record for a given patient."""
    resp = _env.get_patient_medical_record(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_medical_record", req.model_dump(), resp)
    return resp


class GetPatientAdmissionInfoRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_patient_admission_info")
def endpoint_get_patient_admission_info(req: GetPatientAdmissionInfoRequest) -> dict[str, Any]:
    """Retrieve admission details for a patient (e.g., admission date, assigned ward, care team)."""
    resp = _env.get_patient_admission_info(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_admission_info", req.model_dump(), resp)
    return resp


class ListPatientDischargePlansRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/list_patient_discharge_plans")
def endpoint_list_patient_discharge_plans(req: ListPatientDischargePlansRequest) -> dict[str, Any]:
    """List all discharge plans associated with a patient."""
    resp = _env.list_patient_discharge_plans(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/list_patient_discharge_plans", req.model_dump(), resp)
    return resp


class GetActiveDischargePlanRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_active_discharge_plan")
def endpoint_get_active_discharge_plan(req: GetActiveDischargePlanRequest) -> dict[str, Any]:
    """Retrieve the current/active discharge plan for a patient."""
    resp = _env.get_active_discharge_plan(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_active_discharge_plan", req.model_dump(), resp)
    return resp


class GetDischargePlanSectionsRequest(BaseModel):
    discharge_plan_id: str

@app.post("/hospital_patient_discharge/get_discharge_plan_sections")
def endpoint_get_discharge_plan_sections(req: GetDischargePlanSectionsRequest) -> dict[str, Any]:
    """List the filled/required sections of a discharge plan for validation."""
    resp = _env.get_discharge_plan_sections(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_discharge_plan_sections", req.model_dump(), resp)
    return resp


class GetPatientCareTeamRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_patient_care_team")
def endpoint_get_patient_care_team(req: GetPatientCareTeamRequest) -> dict[str, Any]:
    """List all care providers currently assigned to a patient's care team."""
    resp = _env.get_patient_care_team(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_patient_care_team", req.model_dump(), resp)
    return resp


class GetCareProviderByIdRequest(BaseModel):
    provider_id: str

@app.post("/hospital_patient_discharge/get_care_provider_by_id")
def endpoint_get_care_provider_by_id(req: GetCareProviderByIdRequest) -> dict[str, Any]:
    """Retrieve full details about a specific care provider."""
    resp = _env.get_care_provider_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_care_provider_by_id", req.model_dump(), resp)
    return resp


@app.post("/hospital_patient_discharge/list_all_care_providers")
def endpoint_list_all_care_providers() -> dict[str, Any]:
    """Retrieve info for all available hospital staff members."""
    resp = _env.list_all_care_providers()
    _log_call("/hospital_patient_discharge/list_all_care_providers", {}, resp)
    return resp


class GetCommunicationLogsForPatientRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/get_communication_logs_for_patient")
def endpoint_get_communication_logs_for_patient(req: GetCommunicationLogsForPatientRequest) -> dict[str, Any]:
    """Query all communications involving a specific patient."""
    resp = _env.get_communication_logs_for_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/get_communication_logs_for_patient", req.model_dump(), resp)
    return resp


class CheckMedicalRecordUpToDateRequest(BaseModel):
    medical_record_id: str

@app.post("/hospital_patient_discharge/check_medical_record_up_to_date")
def endpoint_check_medical_record_up_to_date(req: CheckMedicalRecordUpToDateRequest) -> dict[str, Any]:
    """Verify whether a medical record has all recent diagnoses and treatments logged."""
    resp = _env.check_medical_record_up_to_date(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/check_medical_record_up_to_date", req.model_dump(), resp)
    return resp


class CreateDischargePlanRequest(BaseModel):
    patient_id: str
    planned_discharge_date: str
    follow_up_instructions: list
    home_care_needs: list
    responsible_provider: str

@app.post("/hospital_patient_discharge/create_discharge_plan")
def endpoint_create_discharge_plan(req: CreateDischargePlanRequest) -> dict[str, Any]:
    """Create a new discharge plan for a patient."""
    resp = _env.create_discharge_plan(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/create_discharge_plan", req.model_dump(), resp)
    return resp


class UpdateDischargePlanRequest(BaseModel):
    discharge_plan_id: str
    planned_discharge_date: str | None = None
    follow_up_instructions: list | None = None
    home_care_needs: list | None = None
    responsible_provider: str | None = None

@app.post("/hospital_patient_discharge/update_discharge_plan")
def endpoint_update_discharge_plan(req: UpdateDischargePlanRequest) -> dict[str, Any]:
    """Edit/add details to an existing discharge plan (date, follow-up, home care, responsible provider, status)."""
    resp = _env.update_discharge_plan(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/update_discharge_plan", req.model_dump(), resp)
    return resp


class MarkPatientMedicallyReadyRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/mark_patient_medically_ready")
def endpoint_mark_patient_medically_ready(req: MarkPatientMedicallyReadyRequest) -> dict[str, Any]:
    """Update patient status to "medically ready" if they meet clinical criteria."""
    resp = _env.mark_patient_medically_ready(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/mark_patient_medically_ready", req.model_dump(), resp)
    return resp


class UpdatePatientCareTeamRequest(BaseModel):
    patient_id: str
    new_care_team: list

@app.post("/hospital_patient_discharge/update_patient_care_team")
def endpoint_update_patient_care_team(req: UpdatePatientCareTeamRequest) -> dict[str, Any]:
    """Assign new care providers to patient or update current assignments."""
    resp = _env.update_patient_care_team(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/update_patient_care_team", req.model_dump(), resp)
    return resp


class LogFamilyCommunicationRequest(BaseModel):
    patient_id: str
    sender_id: str
    recipient_id: str
    message_content: str
    channel: str
    timestamp: str

@app.post("/hospital_patient_discharge/log_family_communication")
def endpoint_log_family_communication(req: LogFamilyCommunicationRequest) -> dict[str, Any]:
    """Record a new communication update with patient's family regarding discharge."""
    resp = _env.log_family_communication(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/log_family_communication", req.model_dump(), resp)
    return resp


class UpdateMedicalRecordRequest(BaseModel):
    medical_record_id: str
    new_diagnoses: list[str] | None = None
    new_treatments: list[str] | None = None
    new_medications: list[str] | None = None
    discharge_instructions: list[str] | None = None

@app.post("/hospital_patient_discharge/update_medical_record")
def endpoint_update_medical_record(req: UpdateMedicalRecordRequest) -> dict[str, Any]:
    """Add new diagnoses, treatments, or discharge instructions to patient's medical record."""
    resp = _env.update_medical_record(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/update_medical_record", req.model_dump(), resp)
    return resp


class FinalizeDischargeRequest(BaseModel):
    patient_id: str

@app.post("/hospital_patient_discharge/finalize_discharge")
def endpoint_finalize_discharge(req: FinalizeDischargeRequest) -> dict[str, Any]:
    """Mark patient as discharged, given that plan sections are completed and constraints are satisfied."""
    resp = _env.finalize_discharge(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/finalize_discharge", req.model_dump(), resp)
    return resp


class SchedulePatientDischargeRequest(BaseModel):
    patient_id: str
    discharge_date: str

@app.post("/hospital_patient_discharge/schedule_patient_discharge")
def endpoint_schedule_patient_discharge(req: SchedulePatientDischargeRequest) -> dict[str, Any]:
    """Set patient's official discharge date in records and workflows."""
    resp = _env.schedule_patient_discharge(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/schedule_patient_discharge", req.model_dump(), resp)
    return resp


class RemoveDischargePlanRequest(BaseModel):
    discharge_plan_id: str

@app.post("/hospital_patient_discharge/remove_discharge_plan")
def endpoint_remove_discharge_plan(req: RemoveDischargePlanRequest) -> dict[str, Any]:
    """Delete or archive an outdated discharge plan (if needed for correction)."""
    resp = _env.remove_discharge_plan(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/remove_discharge_plan", req.model_dump(), resp)
    return resp


class AddPatientAllergyOrMedicationRequest(BaseModel):
    patient_id: str
    entry_type: str
    entry_value: str

@app.post("/hospital_patient_discharge/add_patient_allergy_or_medication")
def endpoint_add_patient_allergy_or_medication(req: AddPatientAllergyOrMedicationRequest) -> dict[str, Any]:
    """Add a new allergy or medication entry to the patient's medical record."""
    resp = _env.add_patient_allergy_or_medication(**req.model_dump(exclude_none=True))
    _log_call("/hospital_patient_discharge/add_patient_allergy_or_medication", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/hospital_patient_discharge/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/hospital_patient_discharge/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9321")))
