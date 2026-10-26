"""Mock Online Account Billing Portal API service (FastAPI)."""

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

from env_class import OnlineAccountBillingPortal  # noqa: E402

app = FastAPI(title="Mock Online Account Billing Portal API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "ONLINE_ACCOUNT_BILLING_PORTAL_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: OnlineAccountBillingPortal | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = OnlineAccountBillingPortal(init_config=init_cfg)
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


@app.post("/online_account_billing_portal/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/online_account_billing_portal/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/online_account_billing_portal/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class CheckUserAuthenticationStatusRequest(BaseModel):
    user_id: str

@app.post("/online_account_billing_portal/check_user_authentication_status")
def endpoint_check_user_authentication_status(req: CheckUserAuthenticationStatusRequest) -> dict[str, Any]:
    """Verify if a user is authenticated and allowed to access their billing history."""
    resp = _env.check_user_authentication_status(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/check_user_authentication_status", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/online_account_billing_portal/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user account details by user ID."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/get_user_by_id", req.model_dump(), resp)
    return resp


class ListUserInvoicesRequest(BaseModel):
    user_id: str

@app.post("/online_account_billing_portal/list_user_invoices")
def endpoint_list_user_invoices(req: ListUserInvoicesRequest) -> dict[str, Any]:
    """Retrieve all invoices associated with a specific user."""
    resp = _env.list_user_invoices(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/list_user_invoices", req.model_dump(), resp)
    return resp


class GetInvoiceDetailsRequest(BaseModel):
    invoice_id: str

@app.post("/online_account_billing_portal/get_invoice_details")
def endpoint_get_invoice_details(req: GetInvoiceDetailsRequest) -> dict[str, Any]:
    """Retrieve full details of a specific invoice, including dates and status."""
    resp = _env.get_invoice_details(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/get_invoice_details", req.model_dump(), resp)
    return resp


class ListInvoiceChargesRequest(BaseModel):
    invoice_id: str

@app.post("/online_account_billing_portal/list_invoice_charges")
def endpoint_list_invoice_charges(req: ListInvoiceChargesRequest) -> dict[str, Any]:
    """Retrieve all charge line items associated with a specific invoice."""
    resp = _env.list_invoice_charges(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/list_invoice_charges", req.model_dump(), resp)
    return resp


class ListUserPaymentsRequest(BaseModel):
    user_id: str

@app.post("/online_account_billing_portal/list_user_payments")
def endpoint_list_user_payments(req: ListUserPaymentsRequest) -> dict[str, Any]:
    """Retrieve all payment records associated with a specific user."""
    resp = _env.list_user_payments(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/list_user_payments", req.model_dump(), resp)
    return resp


class ListInvoicePaymentsRequest(BaseModel):
    invoice_id: str

@app.post("/online_account_billing_portal/list_invoice_payments")
def endpoint_list_invoice_payments(req: ListInvoicePaymentsRequest) -> dict[str, Any]:
    """Retrieve all payments made for a specific invoice."""
    resp = _env.list_invoice_payments(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/list_invoice_payments", req.model_dump(), resp)
    return resp


class GetPaymentDetailsRequest(BaseModel):
    user_id: str
    payment_id: str

@app.post("/online_account_billing_portal/get_payment_details")
def endpoint_get_payment_details(req: GetPaymentDetailsRequest) -> dict[str, Any]:
    """Retrieve details of a specific payment, including status, method, and amount."""
    resp = _env.get_payment_details(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/get_payment_details", req.model_dump(), resp)
    return resp


class SummarizeBillingHistoryRequest(BaseModel):
    user_id: str

@app.post("/online_account_billing_portal/summarize_billing_history")
def endpoint_summarize_billing_history(req: SummarizeBillingHistoryRequest) -> dict[str, Any]:
    """Produce a comprehensive summary of invoices, payments, and charges for a user."""
    resp = _env.summarize_billing_history(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/summarize_billing_history", req.model_dump(), resp)
    return resp


class UpdateAuthenticationStatusRequest(BaseModel):
    user_id: str
    new_status: str

@app.post("/online_account_billing_portal/update_authentication_status")
def endpoint_update_authentication_status(req: UpdateAuthenticationStatusRequest) -> dict[str, Any]:
    """Change a user’s authentication status (e.g., after login/logout)."""
    resp = _env.update_authentication_status(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/update_authentication_status", req.model_dump(), resp)
    return resp


class UpdateInvoiceStatusRequest(BaseModel):
    invoice_id: str
    new_status: str

@app.post("/online_account_billing_portal/update_invoice_status")
def endpoint_update_invoice_status(req: UpdateInvoiceStatusRequest) -> dict[str, Any]:
    """Set a new status for an invoice (e.g., "paid", "unpaid")."""
    resp = _env.update_invoice_status(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/update_invoice_status", req.model_dump(), resp)
    return resp


class AddPaymentRequest(BaseModel):
    payment_id: str
    user_id: str
    invoice_id: str
    payment_date: str
    amount: float
    payment_method: str
    status: str

@app.post("/online_account_billing_portal/add_payment")
def endpoint_add_payment(req: AddPaymentRequest) -> dict[str, Any]:
    """Record a new payment for a user and invoice, ensuring constraints are respected."""
    resp = _env.add_payment(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/add_payment", req.model_dump(), resp)
    return resp


class UpdatePaymentStatusRequest(BaseModel):
    payment_id: str
    new_status: str

@app.post("/online_account_billing_portal/update_payment_status")
def endpoint_update_payment_status(req: UpdatePaymentStatusRequest) -> dict[str, Any]:
    """Modify the status or outcome of an existing payment record."""
    resp = _env.update_payment_status(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/update_payment_status", req.model_dump(), resp)
    return resp


class AddChargeToInvoiceRequest(BaseModel):
    invoice_id: str
    charge_id: str
    description: str
    amount: float

@app.post("/online_account_billing_portal/add_charge_to_invoice")
def endpoint_add_charge_to_invoice(req: AddChargeToInvoiceRequest) -> dict[str, Any]:
    """Add a new charge line to an invoice (amount must be non-negative)."""
    resp = _env.add_charge_to_invoice(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/add_charge_to_invoice", req.model_dump(), resp)
    return resp


class UpdateChargeAmountRequest(BaseModel):
    charge_id: str
    new_amount: float

@app.post("/online_account_billing_portal/update_charge_amount")
def endpoint_update_charge_amount(req: UpdateChargeAmountRequest) -> dict[str, Any]:
    """Modify the amount for a specific charge, respecting invoice and non-negative constraints."""
    resp = _env.update_charge_amount(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/update_charge_amount", req.model_dump(), resp)
    return resp


class DeletePaymentRequest(BaseModel):
    payment_id: str

@app.post("/online_account_billing_portal/delete_payment")
def endpoint_delete_payment(req: DeletePaymentRequest) -> dict[str, Any]:
    """Remove an existing payment record."""
    resp = _env.delete_payment(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/delete_payment", req.model_dump(), resp)
    return resp


class DeleteChargeRequest(BaseModel):
    charge_id: str

@app.post("/online_account_billing_portal/delete_charge")
def endpoint_delete_charge(req: DeleteChargeRequest) -> dict[str, Any]:
    """Remove a specific charge from an invoice."""
    resp = _env.delete_charge(**req.model_dump(exclude_none=True))
    _log_call("/online_account_billing_portal/delete_charge", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/online_account_billing_portal/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/online_account_billing_portal/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9316")))
