"""Mock Electronic Health Record API service (FastAPI)."""

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

from env_class import ElectronicHealthRecordSystem  # noqa: E402

app = FastAPI(title="Mock Electronic Health Record API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "ELECTRONIC_HEALTH_RECORD_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: ElectronicHealthRecordSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = ElectronicHealthRecordSystem(init_config=init_cfg)


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


@app.post("/electronic_health_record/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/electronic_health_record/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/electronic_health_record/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

@app.post("/electronic_health_record/get_current_authenticated_patient")
def endpoint_get_current_authenticated_patient() -> dict[str, Any]:
    """Retrieve the currently authenticated patient (user) information."""
    resp = _env.get_current_authenticated_patient()
    _log_call("/electronic_health_record/get_current_authenticated_patient", {}, resp)
    return resp


class GetPatientInfoByIdRequest(BaseModel):
    patient_id: str

@app.post("/electronic_health_record/get_patient_info_by_id")
def endpoint_get_patient_info_by_id(req: GetPatientInfoByIdRequest) -> dict[str, Any]:
    """Retrieve information about a patient given their patient_id."""
    resp = _env.get_patient_info_by_id(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/get_patient_info_by_id", req.model_dump(), resp)
    return resp


@app.post("/electronic_health_record/list_patient_medical_records")
def endpoint_list_patient_medical_records() -> dict[str, Any]:
    """List all medical records belonging to the current authenticated patient."""
    resp = _env.list_patient_medical_records()
    _log_call("/electronic_health_record/list_patient_medical_records", {}, resp)
    return resp


class FilterMedicalRecordsByDateRangeRequest(BaseModel):
    start_date: str
    end_date: str

@app.post("/electronic_health_record/filter_medical_records_by_date_range")
def endpoint_filter_medical_records_by_date_range(req: FilterMedicalRecordsByDateRangeRequest) -> dict[str, Any]:
    """Retrieve medical records for the current patient within a specified date range."""
    resp = _env.filter_medical_records_by_date_range(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/filter_medical_records_by_date_range", req.model_dump(), resp)
    return resp


class GetMedicalRecordDetailsRequest(BaseModel):
    record_id: str

@app.post("/electronic_health_record/get_medical_record_details")
def endpoint_get_medical_record_details(req: GetMedicalRecordDetailsRequest) -> dict[str, Any]:
    """Retrieve detailed information for a specific medical record by record_id."""
    resp = _env.get_medical_record_details(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/get_medical_record_details", req.model_dump(), resp)
    return resp


@app.post("/electronic_health_record/list_all_providers")
def endpoint_list_all_providers() -> dict[str, Any]:
    """Retrieve the list of all healthcare providers registered in the system."""
    resp = _env.list_all_providers()
    _log_call("/electronic_health_record/list_all_providers", {}, resp)
    return resp


class GetProviderInfoByIdRequest(BaseModel):
    provider_id: str

@app.post("/electronic_health_record/get_provider_info_by_id")
def endpoint_get_provider_info_by_id(req: GetProviderInfoByIdRequest) -> dict[str, Any]:
    """Retrieve information for a provider given provider_id."""
    resp = _env.get_provider_info_by_id(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/get_provider_info_by_id", req.model_dump(), resp)
    return resp


class VerifyMedicalRecordAssociationRequest(BaseModel):
    record_id: str

@app.post("/electronic_health_record/verify_medical_record_association")
def endpoint_verify_medical_record_association(req: VerifyMedicalRecordAssociationRequest) -> dict[str, Any]:
    """Ensure that a medical record is associated with both a valid patient and provider."""
    resp = _env.verify_medical_record_association(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/verify_medical_record_association", req.model_dump(), resp)
    return resp


class UpdatePatientInfoRequest(BaseModel):
    patient_id: str
    contact_info: str | None = None
    account_status: str | None = None

@app.post("/electronic_health_record/update_patient_info")
def endpoint_update_patient_info(req: UpdatePatientInfoRequest) -> dict[str, Any]:
    """Update personal details (contact, status) for a patient."""
    resp = _env.update_patient_info(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/update_patient_info", req.model_dump(), resp)
    return resp


class AddMedicalRecordRequest(BaseModel):
    record_id: str
    patient_id: str
    event_date: str
    event_type: str
    provider_id: str
    details: str

@app.post("/electronic_health_record/add_medical_record")
def endpoint_add_medical_record(req: AddMedicalRecordRequest) -> dict[str, Any]:
    """Add a new medical event record to a patient's history (authorized roles only)."""
    resp = _env.add_medical_record(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/add_medical_record", req.model_dump(), resp)
    return resp


class EditMedicalRecordDetailsRequest(BaseModel):
    record_id: str
    new_details: str

@app.post("/electronic_health_record/edit_medical_record_details")
def endpoint_edit_medical_record_details(req: EditMedicalRecordDetailsRequest) -> dict[str, Any]:
    """Modify details of an existing medical record (authorized roles only)."""
    resp = _env.edit_medical_record_details(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/edit_medical_record_details", req.model_dump(), resp)
    return resp


class DeleteMedicalRecordRequest(BaseModel):
    record_id: str

@app.post("/electronic_health_record/delete_medical_record")
def endpoint_delete_medical_record(req: DeleteMedicalRecordRequest) -> dict[str, Any]:
    """Remove a medical record from the system (authorized roles only)."""
    resp = _env.delete_medical_record(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/delete_medical_record", req.model_dump(), resp)
    return resp


class AddProviderRequest(BaseModel):
    provider_id: str
    name: str
    specialty: str
    contact_info: str

@app.post("/electronic_health_record/add_provider")
def endpoint_add_provider(req: AddProviderRequest) -> dict[str, Any]:
    """Add a new healthcare provider to the system."""
    resp = _env.add_provider(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/add_provider", req.model_dump(), resp)
    return resp


class UpdateProviderInfoRequest(BaseModel):
    provider_id: str
    specialty: str | None = None
    contact_info: str | None = None

@app.post("/electronic_health_record/update_provider_info")
def endpoint_update_provider_info(req: UpdateProviderInfoRequest) -> dict[str, Any]:
    """Update contact or specialty information for an existing provider."""
    resp = _env.update_provider_info(**req.model_dump(exclude_none=True))
    _log_call("/electronic_health_record/update_provider_info", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/electronic_health_record/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/electronic_health_record/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9301")))