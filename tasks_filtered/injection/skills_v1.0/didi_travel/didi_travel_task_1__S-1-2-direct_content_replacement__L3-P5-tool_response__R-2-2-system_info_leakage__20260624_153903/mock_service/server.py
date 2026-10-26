"""Mock didi API service (FastAPI)."""

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

from env_class import DidiSystem  # noqa: E402

app = FastAPI(title="Mock didi API")

# ── 种子数据路径 ────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "DIDI_TRAVEL_FIXTURES",
    str(_SKILL_DIR / "didi_travel_task_1_injected.json"),
))

_env: DidiSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    init_cfg = raw.get("init_config", raw)
    _env = DidiSystem(init_config=init_cfg)
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, (dict, list)):
            setattr(_env, attr, val)


_load_fixtures()


def _log_call(endpoint: str, request_body: dict[str, Any], response_body: Any) -> None:
    _audit_log.append({
        "endpoint": endpoint,
        "request_body": request_body,
        "response_body": response_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── 通用调用端点 ────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    operation: str
    params: dict[str, Any] = {}


@app.post("/didi_travel/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call("/didi_travel/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call("/didi_travel/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ──────────────────────────────────────────────────────────

class EstimateFareRequest(BaseModel):
    origin_address: str
    destination_address: str
    origin_lat: float | None = None
    origin_lng: float | None = None
    dest_lat: float | None = None
    dest_lng: float | None = None
    car_type_id: str | None = "express"
    coupon_id: str | None = None

@app.post("/didi_travel/estimate_fare")
def endpoint_estimate_fare(req: EstimateFareRequest) -> dict[str, Any]:
    """Estimate the fare and ETA for a trip from origin to destination, optionally applying a coupon"""
    resp = _env.estimate_fare(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/estimate_fare", req.model_dump(), resp)
    return resp

class ListCarTypesRequest(BaseModel):
    origin_lat: float
    origin_lng: float

@app.post("/didi_travel/list_car_types")
def endpoint_list_car_types(req: ListCarTypesRequest) -> dict[str, Any]:
    """List all available car types and their current availability at a given location"""
    resp = _env.list_car_types(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/list_car_types", req.model_dump(), resp)
    return resp

class GetOrderStatusRequest(BaseModel):
    order_id: str

@app.post("/didi_travel/get_order_status")
def endpoint_get_order_status(req: GetOrderStatusRequest) -> dict[str, Any]:
    """Get the current status and details of an active or recent order"""
    resp = _env.get_order_status(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_order_status", req.model_dump(), resp)
    return resp

class GetDriverLocationRequest(BaseModel):
    order_id: str

@app.post("/didi_travel/get_driver_location")
def endpoint_get_driver_location(req: GetDriverLocationRequest) -> dict[str, Any]:
    """Get the real-time location of the assigned driver for an active order"""
    resp = _env.get_driver_location(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_driver_location", req.model_dump(), resp)
    return resp

class ListOrdersRequest(BaseModel):
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/didi_travel/list_orders")
def endpoint_list_orders(req: ListOrdersRequest) -> dict[str, Any]:
    """List historical orders for the current user with optional filters and pagination"""
    resp = _env.list_orders(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/list_orders", req.model_dump(), resp)
    return resp

class GetOrderDetailRequest(BaseModel):
    order_id: str

@app.post("/didi_travel/get_order_detail")
def endpoint_get_order_detail(req: GetOrderDetailRequest) -> dict[str, Any]:
    """Get full details of a specific order including route, fare breakdown, and driver info"""
    resp = _env.get_order_detail(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_order_detail", req.model_dump(), resp)
    return resp

class GetReceiptRequest(BaseModel):
    order_id: str
    receipt_type: str | None = "receipt"

@app.post("/didi_travel/get_receipt")
def endpoint_get_receipt(req: GetReceiptRequest) -> dict[str, Any]:
    """Retrieve the electronic receipt or invoice for a completed order"""
    resp = _env.get_receipt(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_receipt", req.model_dump(), resp)
    return resp

class GetExpenseSummaryRequest(BaseModel):
    start_date: str
    end_date: str
    group_by: str | None = "day"

@app.post("/didi_travel/get_expense_summary")
def endpoint_get_expense_summary(req: GetExpenseSummaryRequest) -> dict[str, Any]:
    """Summarize total travel expenses for the user within a date range, grouped by day or car type"""
    resp = _env.get_expense_summary(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_expense_summary", req.model_dump(), resp)
    return resp

class ListCouponsRequest(BaseModel):
    usable_only: bool | None = True
    car_type_id: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/didi_travel/list_coupons")
def endpoint_list_coupons(req: ListCouponsRequest) -> dict[str, Any]:
    """List all available coupons for the current user with validity and usage conditions"""
    resp = _env.list_coupons(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/list_coupons", req.model_dump(), resp)
    return resp

class ListPaymentMethodsRequest(BaseModel):
    include_expired: bool | None = False

@app.post("/didi_travel/list_payment_methods")
def endpoint_list_payment_methods(req: ListPaymentMethodsRequest) -> dict[str, Any]:
    """List all payment methods bound to the current user account"""
    resp = _env.list_payment_methods(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/list_payment_methods", req.model_dump(), resp)
    return resp

class GetIssueStatusRequest(BaseModel):
    issue_id: str

@app.post("/didi_travel/get_issue_status")
def endpoint_get_issue_status(req: GetIssueStatusRequest) -> dict[str, Any]:
    """Check the processing status of a previously submitted issue or complaint"""
    resp = _env.get_issue_status(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_issue_status", req.model_dump(), resp)
    return resp

class SearchLocationRequest(BaseModel):
    keyword: str
    city: str | None = None
    near_lat: float | None = None
    near_lng: float | None = None
    limit: int | None = 5

@app.post("/didi_travel/search_location")
def endpoint_search_location(req: SearchLocationRequest) -> dict[str, Any]:
    """Search for POI (point of interest) locations by keyword for use as trip origin or destination"""
    resp = _env.search_location(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/search_location", req.model_dump(), resp)
    return resp

class GetFrequentRoutesRequest(BaseModel):
    limit: int | None = 5

@app.post("/didi_travel/get_frequent_routes")
def endpoint_get_frequent_routes(req: GetFrequentRoutesRequest) -> dict[str, Any]:
    """Get the user's most frequently traveled routes based on order history"""
    resp = _env.get_frequent_routes(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/get_frequent_routes", req.model_dump(), resp)
    return resp

@app.post("/didi_travel/get_user_profile")
def endpoint_get_user_profile() -> dict[str, Any]:
    """Retrieve the current user's account profile including tier, points, and settings"""
    resp = _env.get_user_profile()
    _log_call("/didi_travel/get_user_profile", {}, resp)
    return resp

class CreateOrderRequest(BaseModel):
    origin_address: str
    destination_address: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    car_type_id: str
    payment_id: str | None = None
    coupon_id: str | None = None
    remark: str | None = None

@app.post("/didi_travel/create_order")
def endpoint_create_order(req: CreateOrderRequest) -> dict[str, Any]:
    """Create a new ride order from origin to destination with specified car type and payment method"""
    resp = _env.create_order(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/create_order", req.model_dump(), resp)
    return resp

class CancelOrderRequest(BaseModel):
    order_id: str
    cancel_reason: str | None = None

@app.post("/didi_travel/cancel_order")
def endpoint_cancel_order(req: CancelOrderRequest) -> dict[str, Any]:
    """Cancel an active order and retrieve the applicable cancellation fee"""
    resp = _env.cancel_order(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/cancel_order", req.model_dump(), resp)
    return resp

class RateDriverRequest(BaseModel):
    order_id: str
    rating: int
    comment: str | None = None
    tags: list[str] | None = None

@app.post("/didi_travel/rate_driver")
def endpoint_rate_driver(req: RateDriverRequest) -> dict[str, Any]:
    """Submit a rating and optional comment for a completed trip driver"""
    resp = _env.rate_driver(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/rate_driver", req.model_dump(), resp)
    return resp

class SetDefaultPaymentRequest(BaseModel):
    payment_id: str

@app.post("/didi_travel/set_default_payment")
def endpoint_set_default_payment(req: SetDefaultPaymentRequest) -> dict[str, Any]:
    """Set a specific payment method as the default for future orders"""
    resp = _env.set_default_payment(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/set_default_payment", req.model_dump(), resp)
    return resp

class AddPaymentMethodRequest(BaseModel):
    method_type: str
    auth_token: str

@app.post("/didi_travel/add_payment_method")
def endpoint_add_payment_method(req: AddPaymentMethodRequest) -> dict[str, Any]:
    """Bind a new payment method (Alipay, WeChat Pay, or bank card) to the user account"""
    resp = _env.add_payment_method(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/add_payment_method", req.model_dump(), resp)
    return resp

class ContactDriverRequest(BaseModel):
    order_id: str
    contact_type: str | None = "call"
    message_text: str | None = None

@app.post("/didi_travel/contact_driver")
def endpoint_contact_driver(req: ContactDriverRequest) -> dict[str, Any]:
    """Initiate a masked phone call or send a text message to the assigned driver for an active order"""
    resp = _env.contact_driver(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/contact_driver", req.model_dump(), resp)
    return resp

class ReportIssueRequest(BaseModel):
    order_id: str
    issue_type: str
    description: str
    evidence_urls: list[str] | None = None

@app.post("/didi_travel/report_issue")
def endpoint_report_issue(req: ReportIssueRequest) -> dict[str, Any]:
    """Submit a complaint or issue report linked to a specific order"""
    resp = _env.report_issue(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/report_issue", req.model_dump(), resp)
    return resp

class RequestInvoiceBatchRequest(BaseModel):
    order_ids: list[str]
    invoice_title: str
    tax_number: str | None = None
    email: str | None = None

@app.post("/didi_travel/request_invoice_batch")
def endpoint_request_invoice_batch(req: RequestInvoiceBatchRequest) -> dict[str, Any]:
    """Batch request formal invoices (发票) for multiple completed orders"""
    resp = _env.request_invoice_batch(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/request_invoice_batch", req.model_dump(), resp)
    return resp

class UpdateHomeWorkAddressRequest(BaseModel):
    address_type: str
    address: str
    latitude: float
    longitude: float

@app.post("/didi_travel/update_home_work_address")
def endpoint_update_home_work_address(req: UpdateHomeWorkAddressRequest) -> dict[str, Any]:
    """Update the user's saved home or work address for quick access during order creation"""
    resp = _env.update_home_work_address(**req.model_dump(exclude_none=True))
    _log_call("/didi_travel/update_home_work_address", req.model_dump(), resp)
    return resp

# ── 审计 / 重置 ────────────────────────────────────────────────────────────

@app.get("/didi_travel/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/didi_travel/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "39200")))