"""Mock sf_express API service (FastAPI)."""

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

from env_class import SfExpressSystem  # noqa: E402

app = FastAPI(title="Mock sf_express API")

# ── 种子数据路径 ────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "SF_EXPRESS_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: SfExpressSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    init_cfg = raw.get("init_config", raw)
    _env = SfExpressSystem(init_config=init_cfg)
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


@app.post("/sf_express/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call("/sf_express/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call("/sf_express/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ──────────────────────────────────────────────────────────

class EstimateShippingFeeRequest(BaseModel):
    sender_city: str
    receiver_city: str
    weight: float
    service_code: str | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None

@app.post("/sf_express/estimate_shipping_fee")
def endpoint_estimate_shipping_fee(req: EstimateShippingFeeRequest) -> dict[str, Any]:
    """Estimate shipping fee based on sender/receiver location, weight, size, and service type"""
    resp = _env.estimate_shipping_fee(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/estimate_shipping_fee", req.model_dump(), resp)
    return resp

class GetServiceTypesRequest(BaseModel):
    sender_city: str | None = None
    receiver_city: str | None = None

@app.post("/sf_express/get_service_types")
def endpoint_get_service_types(req: GetServiceTypesRequest) -> dict[str, Any]:
    """Get all available SF Express service types with descriptions and pricing rules"""
    resp = _env.get_service_types(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_service_types", req.model_dump(), resp)
    return resp

class TrackWaybillRequest(BaseModel):
    waybill_no: str
    phone: str | None = None

@app.post("/sf_express/track_waybill")
def endpoint_track_waybill(req: TrackWaybillRequest) -> dict[str, Any]:
    """Track real-time logistics status and route for a waybill number"""
    resp = _env.track_waybill(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/track_waybill", req.model_dump(), resp)
    return resp

class GetShipmentDetailRequest(BaseModel):
    shipment_id: str | None = None
    waybill_no: str | None = None

@app.post("/sf_express/get_shipment_detail")
def endpoint_get_shipment_detail(req: GetShipmentDetailRequest) -> dict[str, Any]:
    """Get full details of a shipment order by shipment ID or waybill number"""
    resp = _env.get_shipment_detail(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_shipment_detail", req.model_dump(), resp)
    return resp

class ListShipmentsRequest(BaseModel):
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/sf_express/list_shipments")
def endpoint_list_shipments(req: ListShipmentsRequest) -> dict[str, Any]:
    """List shipment orders with optional filters and pagination"""
    resp = _env.list_shipments(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/list_shipments", req.model_dump(), resp)
    return resp

class GetWaybillRequest(BaseModel):
    shipment_id: str | None = None
    waybill_no: str | None = None

@app.post("/sf_express/get_waybill")
def endpoint_get_waybill(req: GetWaybillRequest) -> dict[str, Any]:
    """Retrieve waybill/label details including print URL for a shipment"""
    resp = _env.get_waybill(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_waybill", req.model_dump(), resp)
    return resp

class ListAddressesRequest(BaseModel):
    type: str | None = None
    keyword: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/sf_express/list_addresses")
def endpoint_list_addresses(req: ListAddressesRequest) -> dict[str, Any]:
    """List user's saved address book entries"""
    resp = _env.list_addresses(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/list_addresses", req.model_dump(), resp)
    return resp

class QueryServicePointsRequest(BaseModel):
    city: str
    district: str | None = None
    keyword: str | None = None
    point_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    page: int | None = 1
    page_size: int | None = 10

@app.post("/sf_express/query_service_points")
def endpoint_query_service_points(req: QueryServicePointsRequest) -> dict[str, Any]:
    """Search for SF Express service points (drop-off or pickup locations) near a location"""
    resp = _env.query_service_points(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/query_service_points", req.model_dump(), resp)
    return resp

class GetServicePointDetailRequest(BaseModel):
    point_id: str

@app.post("/sf_express/get_service_point_detail")
def endpoint_get_service_point_detail(req: GetServicePointDetailRequest) -> dict[str, Any]:
    """Get detailed information about a specific service point"""
    resp = _env.get_service_point_detail(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_service_point_detail", req.model_dump(), resp)
    return resp

class GetExceptionDetailRequest(BaseModel):
    waybill_no: str

@app.post("/sf_express/get_exception_detail")
def endpoint_get_exception_detail(req: GetExceptionDetailRequest) -> dict[str, Any]:
    """Get detailed information about an exception or abnormal logistics event for a waybill"""
    resp = _env.get_exception_detail(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_exception_detail", req.model_dump(), resp)
    return resp

class GetComplaintStatusRequest(BaseModel):
    complaint_id: str

@app.post("/sf_express/get_complaint_status")
def endpoint_get_complaint_status(req: GetComplaintStatusRequest) -> dict[str, Any]:
    """Query the processing status of a submitted complaint"""
    resp = _env.get_complaint_status(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_complaint_status", req.model_dump(), resp)
    return resp

class SearchWaybillsRequest(BaseModel):
    keyword: str | None = None
    status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/sf_express/search_waybills")
def endpoint_search_waybills(req: SearchWaybillsRequest) -> dict[str, Any]:
    """Search waybills by various criteria including sender/receiver phone or order number"""
    resp = _env.search_waybills(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/search_waybills", req.model_dump(), resp)
    return resp

class GetDeliveryEstimateRequest(BaseModel):
    sender_city: str
    receiver_city: str
    service_code: str
    ship_date: str | None = None

@app.post("/sf_express/get_delivery_estimate")
def endpoint_get_delivery_estimate(req: GetDeliveryEstimateRequest) -> dict[str, Any]:
    """Get estimated delivery date and time for a specific route and service type"""
    resp = _env.get_delivery_estimate(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/get_delivery_estimate", req.model_dump(), resp)
    return resp

class CreateShipmentRequest(BaseModel):
    sender_name: str
    sender_phone: str
    sender_address: str
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    service_code: str
    weight: float
    cargo_type: str | None = "GENERAL"
    cargo_name: str | None = None
    declared_value: float | None = None
    remark: str | None = None

@app.post("/sf_express/create_shipment")
def endpoint_create_shipment(req: CreateShipmentRequest) -> dict[str, Any]:
    """Create a new shipment order with sender, receiver, and cargo details"""
    resp = _env.create_shipment(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/create_shipment", req.model_dump(), resp)
    return resp

class BatchCreateShipmentsRequest(BaseModel):
    shipments: list[dict[str, Any]]
    common_service_code: str | None = None

@app.post("/sf_express/batch_create_shipments")
def endpoint_batch_create_shipments(req: BatchCreateShipmentsRequest) -> dict[str, Any]:
    """Create multiple shipment orders in a single request (max 100)"""
    resp = _env.batch_create_shipments(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/batch_create_shipments", req.model_dump(), resp)
    return resp

class CancelShipmentRequest(BaseModel):
    shipment_id: str
    reason: str | None = None

@app.post("/sf_express/cancel_shipment")
def endpoint_cancel_shipment(req: CancelShipmentRequest) -> dict[str, Any]:
    """Cancel an existing shipment order before pickup"""
    resp = _env.cancel_shipment(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/cancel_shipment", req.model_dump(), resp)
    return resp

class SchedulePickupRequest(BaseModel):
    shipment_ids: list[str]
    pickup_date: str
    pickup_time_start: str
    pickup_time_end: str
    contact_phone: str | None = None

@app.post("/sf_express/schedule_pickup")
def endpoint_schedule_pickup(req: SchedulePickupRequest) -> dict[str, Any]:
    """Schedule a courier pickup for one or more waybills"""
    resp = _env.schedule_pickup(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/schedule_pickup", req.model_dump(), resp)
    return resp

class CreateAddressRequest(BaseModel):
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    type: str | None = "SENDER"
    is_default: bool | None = False

@app.post("/sf_express/create_address")
def endpoint_create_address(req: CreateAddressRequest) -> dict[str, Any]:
    """Add a new address to the user's address book"""
    resp = _env.create_address(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/create_address", req.model_dump(), resp)
    return resp

class UpdateAddressRequest(BaseModel):
    address_id: str
    name: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    detail: str | None = None
    is_default: bool | None = None

@app.post("/sf_express/update_address")
def endpoint_update_address(req: UpdateAddressRequest) -> dict[str, Any]:
    """Update an existing address in the user's address book"""
    resp = _env.update_address(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/update_address", req.model_dump(), resp)
    return resp

class DeleteAddressRequest(BaseModel):
    address_id: str

@app.post("/sf_express/delete_address")
def endpoint_delete_address(req: DeleteAddressRequest) -> dict[str, Any]:
    """Delete an address from the user's address book"""
    resp = _env.delete_address(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/delete_address", req.model_dump(), resp)
    return resp

class SubscribeTrackingRequest(BaseModel):
    waybill_no: str
    notify_phone: str | None = None
    notify_events: list[str] | None = None

@app.post("/sf_express/subscribe_tracking")
def endpoint_subscribe_tracking(req: SubscribeTrackingRequest) -> dict[str, Any]:
    """Subscribe to real-time tracking notifications for a waybill"""
    resp = _env.subscribe_tracking(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/subscribe_tracking", req.model_dump(), resp)
    return resp

class SubmitComplaintRequest(BaseModel):
    waybill_no: str
    complaint_type: str
    description: str
    contact_phone: str
    images: list[str] | None = None

@app.post("/sf_express/submit_complaint")
def endpoint_submit_complaint(req: SubmitComplaintRequest) -> dict[str, Any]:
    """Submit a complaint or abnormal parcel report for a waybill"""
    resp = _env.submit_complaint(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/submit_complaint", req.model_dump(), resp)
    return resp

class ApplyCompensationRequest(BaseModel):
    waybill_no: str
    compensation_type: str
    claimed_amount: float
    cargo_value: float
    bank_account: str | None = None
    bank_name: str | None = None
    account_holder: str | None = None
    evidence_images: list[str] | None = None

@app.post("/sf_express/apply_compensation")
def endpoint_apply_compensation(req: ApplyCompensationRequest) -> dict[str, Any]:
    """Apply for compensation for a lost, damaged, or significantly delayed shipment"""
    resp = _env.apply_compensation(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/apply_compensation", req.model_dump(), resp)
    return resp

class RedirectDeliveryRequest(BaseModel):
    waybill_no: str
    new_address: str | None = None
    redirect_to_point_id: str | None = None
    contact_phone: str

@app.post("/sf_express/redirect_delivery")
def endpoint_redirect_delivery(req: RedirectDeliveryRequest) -> dict[str, Any]:
    """Request to redirect an in-transit parcel to a different delivery address or locker"""
    resp = _env.redirect_delivery(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/redirect_delivery", req.model_dump(), resp)
    return resp

class ConfirmReceiptRequest(BaseModel):
    waybill_no: str
    confirm_phone: str
    rating: int | None = None
    comment: str | None = None

@app.post("/sf_express/confirm_receipt")
def endpoint_confirm_receipt(req: ConfirmReceiptRequest) -> dict[str, Any]:
    """Confirm receipt of a delivered parcel by the receiver"""
    resp = _env.confirm_receipt(**req.model_dump(exclude_none=True))
    _log_call("/sf_express/confirm_receipt", req.model_dump(), resp)
    return resp

# ── 审计 / 重置 ────────────────────────────────────────────────────────────

@app.get("/sf_express/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/sf_express/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "39200")))