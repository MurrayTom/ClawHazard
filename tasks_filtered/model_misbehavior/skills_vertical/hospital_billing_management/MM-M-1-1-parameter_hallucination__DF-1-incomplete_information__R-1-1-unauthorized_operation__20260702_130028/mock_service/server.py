"""Mock Hospital Billing Management API service (FastAPI)."""

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

from env_class import HospitalBillingManagementSystem  # noqa: E402

app = FastAPI(title="Mock Hospital Billing Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "HOSPITAL_BILLING_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: HospitalBillingManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = HospitalBillingManagementSystem(init_config=init_cfg)
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


@app.post("/hospital_billing_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/hospital_billing_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/hospital_billing_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetPatientByIdRequest(BaseModel):
    patient_id: str

@app.post("/hospital_billing_management/get_patient_by_id")
def endpoint_get_patient_by_id(req: GetPatientByIdRequest) -> dict[str, Any]:
    """Retrieve patient demographic and contact information by patient_id."""
    resp = _env.get_patient_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/get_patient_by_id", req.model_dump(), resp)
    return resp


class ListPatientBillsRequest(BaseModel):
    patient_id: str

@app.post("/hospital_billing_management/list_patient_bills")
def endpoint_list_patient_bills(req: ListPatientBillsRequest) -> dict[str, Any]:
    """Retrieve all bills associated with a specified patient."""
    resp = _env.list_patient_bills(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_patient_bills", req.model_dump(), resp)
    return resp


class GetBillByIdRequest(BaseModel):
    bill_id: str

@app.post("/hospital_billing_management/get_bill_by_id")
def endpoint_get_bill_by_id(req: GetBillByIdRequest) -> dict[str, Any]:
    """Get details of a specific bill given its bill_id."""
    resp = _env.get_bill_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/get_bill_by_id", req.model_dump(), resp)
    return resp


class ListPaymentsForBillRequest(BaseModel):
    bill_id: str

@app.post("/hospital_billing_management/list_payments_for_bill")
def endpoint_list_payments_for_bill(req: ListPaymentsForBillRequest) -> dict[str, Any]:
    """Retrieve all payment records associated with a bill."""
    resp = _env.list_payments_for_bill(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_payments_for_bill", req.model_dump(), resp)
    return resp


class GetBillBalanceRequest(BaseModel):
    bill_id: str

@app.post("/hospital_billing_management/get_bill_balance")
def endpoint_get_bill_balance(req: GetBillBalanceRequest) -> dict[str, Any]:
    """Calculate the outstanding balance (amount_due - total amount_paid) for a bill."""
    resp = _env.get_bill_balance(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/get_bill_balance", req.model_dump(), resp)
    return resp


class ListDisputesForPatientRequest(BaseModel):
    patient_id: str

@app.post("/hospital_billing_management/list_disputes_for_patient")
def endpoint_list_disputes_for_patient(req: ListDisputesForPatientRequest) -> dict[str, Any]:
    """Retrieve all disputes initiated by or associated with a given patient."""
    resp = _env.list_disputes_for_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_disputes_for_patient", req.model_dump(), resp)
    return resp


class ListDisputesForBillRequest(BaseModel):
    bill_id: str

@app.post("/hospital_billing_management/list_disputes_for_bill")
def endpoint_list_disputes_for_bill(req: ListDisputesForBillRequest) -> dict[str, Any]:
    """Retrieve all disputes linked to a specific bill."""
    resp = _env.list_disputes_for_bill(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_disputes_for_bill", req.model_dump(), resp)
    return resp


class GetDisputeByIdRequest(BaseModel):
    dispute_id: str

@app.post("/hospital_billing_management/get_dispute_by_id")
def endpoint_get_dispute_by_id(req: GetDisputeByIdRequest) -> dict[str, Any]:
    """Retrieve full details for a specific dispute."""
    resp = _env.get_dispute_by_id(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/get_dispute_by_id", req.model_dump(), resp)
    return resp


class ListCustomerSupportInteractionsForPatientRequest(BaseModel):
    patient_id: str

@app.post("/hospital_billing_management/list_customer_support_interactions_for_patient")
def endpoint_list_customer_support_interactions_for_patient(req: ListCustomerSupportInteractionsForPatientRequest) -> dict[str, Any]:
    """Retrieve all customer support interactions with a given patient."""
    resp = _env.list_customer_support_interactions_for_patient(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_customer_support_interactions_for_patient", req.model_dump(), resp)
    return resp


class ListCustomerSupportInteractionsForDisputeRequest(BaseModel):
    dispute_id: str

@app.post("/hospital_billing_management/list_customer_support_interactions_for_dispute")
def endpoint_list_customer_support_interactions_for_dispute(req: ListCustomerSupportInteractionsForDisputeRequest) -> dict[str, Any]:
    """Retrieve support interactions referencing a specific dispute."""
    resp = _env.list_customer_support_interactions_for_dispute(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/list_customer_support_interactions_for_dispute", req.model_dump(), resp)
    return resp


class CreateDisputeRequest(BaseModel):
    bill_id: str
    patient_id: str
    description: str
    date_created: str
    status: str

@app.post("/hospital_billing_management/create_dispute")
def endpoint_create_dispute(req: CreateDisputeRequest) -> dict[str, Any]:
    """Create a new dispute record for a specified bill and patient, subject to validation constraints."""
    resp = _env.create_dispute(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/create_dispute", req.model_dump(), resp)
    return resp


class UpdateDisputeStatusRequest(BaseModel):
    dispute_id: str
    new_status: str

@app.post("/hospital_billing_management/update_dispute_status")
def endpoint_update_dispute_status(req: UpdateDisputeStatusRequest) -> dict[str, Any]:
    """Change the status of an existing dispute (e.g., open, pending review, resolved)."""
    resp = _env.update_dispute_status(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/update_dispute_status", req.model_dump(), resp)
    return resp


class AddDisputeResolutionDetailRequest(BaseModel):
    dispute_id: str
    resolution_detail: str

@app.post("/hospital_billing_management/add_dispute_resolution_detail")
def endpoint_add_dispute_resolution_detail(req: AddDisputeResolutionDetailRequest) -> dict[str, Any]:
    """Record a resolution detail for a dispute once it is resolved."""
    resp = _env.add_dispute_resolution_detail(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/add_dispute_resolution_detail", req.model_dump(), resp)
    return resp


class LogCustomerSupportInteractionRequest(BaseModel):
    patient_id: str
    support_agent_id: str
    note: str
    timestamp: str
    dispute_id: str | None = None

@app.post("/hospital_billing_management/log_customer_support_interaction")
def endpoint_log_customer_support_interaction(req: LogCustomerSupportInteractionRequest) -> dict[str, Any]:
    """Record a new customer support interaction associated with a patient and optionally a dispute."""
    resp = _env.log_customer_support_interaction(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/log_customer_support_interaction", req.model_dump(), resp)
    return resp


class AddPaymentToBillRequest(BaseModel):
    bill_id: str
    payment_id: str
    date: str
    amount: float
    payment_method: str
    status: str

@app.post("/hospital_billing_management/add_payment_to_bill")
def endpoint_add_payment_to_bill(req: AddPaymentToBillRequest) -> dict[str, Any]:
    """Register a new payment to a bill, checking to ensure payment sum doesn’t exceed the amount_due."""
    resp = _env.add_payment_to_bill(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/add_payment_to_bill", req.model_dump(), resp)
    return resp


class UpdateBillStatusRequest(BaseModel):
    bill_id: str
    new_status: str

@app.post("/hospital_billing_management/update_bill_status")
def endpoint_update_bill_status(req: UpdateBillStatusRequest) -> dict[str, Any]:
    """Update the financial or workflow status of a bill (e.g., paid, overdue, disputed)."""
    resp = _env.update_bill_status(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/update_bill_status", req.model_dump(), resp)
    return resp


class ModifyBillDetailsRequest(BaseModel):
    bill_id: str
    treatment_details: str | None = None
    issue_date: str | None = None
    amount_due: float | None = None
    status: str | None = None

@app.post("/hospital_billing_management/modify_bill_details")
def endpoint_modify_bill_details(req: ModifyBillDetailsRequest) -> dict[str, Any]:
    """Edit treatment details, billing amount, or other bill-level information (admin)."""
    resp = _env.modify_bill_details(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/modify_bill_details", req.model_dump(), resp)
    return resp


class UpdatePatientContactInformationRequest(BaseModel):
    patient_id: str
    new_contact_information: str

@app.post("/hospital_billing_management/update_patient_contact_information")
def endpoint_update_patient_contact_information(req: UpdatePatientContactInformationRequest) -> dict[str, Any]:
    """Change or correct a patient’s contact details."""
    resp = _env.update_patient_contact_information(**req.model_dump(exclude_none=True))
    _log_call("/hospital_billing_management/update_patient_contact_information", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/hospital_billing_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/hospital_billing_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9311")))
