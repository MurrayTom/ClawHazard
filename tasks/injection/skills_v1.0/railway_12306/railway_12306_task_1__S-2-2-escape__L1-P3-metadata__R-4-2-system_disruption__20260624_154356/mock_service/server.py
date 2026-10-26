"""Mock railway_12306 API service (FastAPI)."""

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

from env_class import Railway12306System  # noqa: E402

app = FastAPI(title="Mock railway_12306 API")

# ── 种子数据路径 ────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "RAILWAY_12306_FIXTURES",
    str(_SKILL_DIR / "railway_12306_task_1.json"),
))

_env: Railway12306System | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    init_cfg = raw.get("init_config", raw)
    _env = Railway12306System(init_config=init_cfg)
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, (dict, list)):
            setattr(_env, attr, val)
    # If seeded tickets are stored inside orders as dicts, register them in _env.tickets
    for order in _env.orders.values():
        ticket_ids = []
        for i, t in enumerate(order.get("tickets", [])):
            if isinstance(t, dict):
                tid = t.get("ticket_id")
                if tid and tid not in _env.tickets:
                    _env.tickets[tid] = t
                if tid:
                    ticket_ids.append(tid)
            else:
                ticket_ids.append(t)
        order["tickets"] = ticket_ids


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


@app.post("/railway_12306/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call("/railway_12306/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call("/railway_12306/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ──────────────────────────────────────────────────────────

class SearchTrainsRequest(BaseModel):
    from_station: str
    to_station: str
    depart_date: str
    train_type: str | None = "all"
    order_by: str | None = "depart_time"

@app.post("/railway_12306/search_trains")
def endpoint_search_trains(req: SearchTrainsRequest) -> dict[str, Any]:
    """Search available trains between two stations on a given date"""
    resp = _env.search_trains(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/search_trains", req.model_dump(), resp)
    return resp

class GetTrainDetailRequest(BaseModel):
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str

@app.post("/railway_12306/get_train_detail")
def endpoint_get_train_detail(req: GetTrainDetailRequest) -> dict[str, Any]:
    """Get detailed information about a specific train"""
    resp = _env.get_train_detail(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_train_detail", req.model_dump(), resp)
    return resp

class GetTrainStopsRequest(BaseModel):
    train_no: str
    depart_date: str

@app.post("/railway_12306/get_train_stops")
def endpoint_get_train_stops(req: GetTrainStopsRequest) -> dict[str, Any]:
    """Get all stop stations for a specific train"""
    resp = _env.get_train_stops(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_train_stops", req.model_dump(), resp)
    return resp

class CheckSeatAvailabilityRequest(BaseModel):
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str
    seat_type: str | None = "all"

@app.post("/railway_12306/check_seat_availability")
def endpoint_check_seat_availability(req: CheckSeatAvailabilityRequest) -> dict[str, Any]:
    """Check real-time seat availability for a specific train and seat type"""
    resp = _env.check_seat_availability(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/check_seat_availability", req.model_dump(), resp)
    return resp

class GetTicketPriceRequest(BaseModel):
    train_no: str
    from_station_code: str
    to_station_code: str
    depart_date: str

@app.post("/railway_12306/get_ticket_price")
def endpoint_get_ticket_price(req: GetTicketPriceRequest) -> dict[str, Any]:
    """Get ticket prices for all seat types on a given train segment"""
    resp = _env.get_ticket_price(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_ticket_price", req.model_dump(), resp)
    return resp

class GetStationListRequest(BaseModel):
    keyword: str | None = None
    city: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/railway_12306/get_station_list")
def endpoint_get_station_list(req: GetStationListRequest) -> dict[str, Any]:
    """Get list of all railway stations, optionally filtered by city or keyword"""
    resp = _env.get_station_list(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_station_list", req.model_dump(), resp)
    return resp

class GetPassengerListRequest(BaseModel):
    page: int | None = 1
    page_size: int | None = 10

@app.post("/railway_12306/get_passenger_list")
def endpoint_get_passenger_list(req: GetPassengerListRequest) -> dict[str, Any]:
    """Get the saved passenger profiles for the current user account"""
    resp = _env.get_passenger_list(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_passenger_list", req.model_dump(), resp)
    return resp

class ListOrdersRequest(BaseModel):
    status: str | None = "all"
    depart_date_from: str | None = None
    depart_date_to: str | None = None
    page: int | None = 1
    page_size: int | None = 10

@app.post("/railway_12306/list_orders")
def endpoint_list_orders(req: ListOrdersRequest) -> dict[str, Any]:
    """List all orders for the current user account with optional filters"""
    resp = _env.list_orders(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/list_orders", req.model_dump(), resp)
    return resp

class GetOrderDetailRequest(BaseModel):
    order_id: str

@app.post("/railway_12306/get_order_detail")
def endpoint_get_order_detail(req: GetOrderDetailRequest) -> dict[str, Any]:
    """Get full details of a specific order"""
    resp = _env.get_order_detail(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_order_detail", req.model_dump(), resp)
    return resp

class CalculateRefundFeeRequest(BaseModel):
    ticket_id: str
    order_id: str

@app.post("/railway_12306/calculate_refund_fee")
def endpoint_calculate_refund_fee(req: CalculateRefundFeeRequest) -> dict[str, Any]:
    """Calculate the refund fee for a specific ticket before submitting refund"""
    resp = _env.calculate_refund_fee(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/calculate_refund_fee", req.model_dump(), resp)
    return resp

class GetRefundStatusRequest(BaseModel):
    refund_id: str

@app.post("/railway_12306/get_refund_status")
def endpoint_get_refund_status(req: GetRefundStatusRequest) -> dict[str, Any]:
    """Query the current status of a refund request"""
    resp = _env.get_refund_status(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_refund_status", req.model_dump(), resp)
    return resp

class GetChangeRecordRequest(BaseModel):
    change_id: str

@app.post("/railway_12306/get_change_record")
def endpoint_get_change_record(req: GetChangeRecordRequest) -> dict[str, Any]:
    """Get details of a specific ticket change record"""
    resp = _env.get_change_record(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_change_record", req.model_dump(), resp)
    return resp

class GetTravelNoticeRequest(BaseModel):
    notice_type: str | None = "all"
    region: str | None = None
    page: int | None = 1
    page_size: int | None = 10

@app.post("/railway_12306/get_travel_notice")
def endpoint_get_travel_notice(req: GetTravelNoticeRequest) -> dict[str, Any]:
    """Get current travel notices, service alerts, or platform announcements"""
    resp = _env.get_travel_notice(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/get_travel_notice", req.model_dump(), resp)
    return resp

class SearchOrdersByTrainRequest(BaseModel):
    train_no: str
    depart_date_from: str | None = None
    depart_date_to: str | None = None
    page: int | None = 1
    page_size: int | None = 10

@app.post("/railway_12306/search_orders_by_train")
def endpoint_search_orders_by_train(req: SearchOrdersByTrainRequest) -> dict[str, Any]:
    """Search orders filtered by train number and date range"""
    resp = _env.search_orders_by_train(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/search_orders_by_train", req.model_dump(), resp)
    return resp

class AddPassengerRequest(BaseModel):
    name: str
    id_card_type: str
    id_card_no: str
    mobile: str | None = None

@app.post("/railway_12306/add_passenger")
def endpoint_add_passenger(req: AddPassengerRequest) -> dict[str, Any]:
    """Add a new passenger profile to the current user account"""
    resp = _env.add_passenger(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/add_passenger", req.model_dump(), resp)
    return resp

class UpdatePassengerRequest(BaseModel):
    passenger_id: str
    mobile: str | None = None
    name: str | None = None
    id_card_no: str | None = None

@app.post("/railway_12306/update_passenger")
def endpoint_update_passenger(req: UpdatePassengerRequest) -> dict[str, Any]:
    """Update an existing passenger profile"""
    resp = _env.update_passenger(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/update_passenger", req.model_dump(), resp)
    return resp

class DeletePassengerRequest(BaseModel):
    passenger_id: str

@app.post("/railway_12306/delete_passenger")
def endpoint_delete_passenger(req: DeletePassengerRequest) -> dict[str, Any]:
    """Delete a passenger profile from the current user account"""
    resp = _env.delete_passenger(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/delete_passenger", req.model_dump(), resp)
    return resp

class CreateOrderRequest(BaseModel):
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str
    seat_type: str
    passenger_ids: list[str]
    is_standby: bool | None = False

@app.post("/railway_12306/create_order")
def endpoint_create_order(req: CreateOrderRequest) -> dict[str, Any]:
    """Submit a ticket booking order for one or more passengers"""
    resp = _env.create_order(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/create_order", req.model_dump(), resp)
    return resp

class CancelOrderRequest(BaseModel):
    order_id: str

@app.post("/railway_12306/cancel_order")
def endpoint_cancel_order(req: CancelOrderRequest) -> dict[str, Any]:
    """Cancel an unpaid order"""
    resp = _env.cancel_order(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/cancel_order", req.model_dump(), resp)
    return resp

class PayOrderRequest(BaseModel):
    order_id: str
    payment_method: str

@app.post("/railway_12306/pay_order")
def endpoint_pay_order(req: PayOrderRequest) -> dict[str, Any]:
    """Initiate payment for a pending order"""
    resp = _env.pay_order(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/pay_order", req.model_dump(), resp)
    return resp

class RefundTicketRequest(BaseModel):
    ticket_id: str
    order_id: str

@app.post("/railway_12306/refund_ticket")
def endpoint_refund_ticket(req: RefundTicketRequest) -> dict[str, Any]:
    """Submit a refund request for a specific ticket"""
    resp = _env.refund_ticket(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/refund_ticket", req.model_dump(), resp)
    return resp

class ChangeTicketRequest(BaseModel):
    ticket_id: str
    order_id: str
    new_train_no: str
    new_depart_date: str
    new_from_station_code: str
    new_to_station_code: str
    new_seat_type: str

@app.post("/railway_12306/change_ticket")
def endpoint_change_ticket(req: ChangeTicketRequest) -> dict[str, Any]:
    """Submit a ticket change (gaiqian) request to a different train or seat"""
    resp = _env.change_ticket(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/change_ticket", req.model_dump(), resp)
    return resp

class ApplyStandbyRequest(BaseModel):
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str
    seat_type: str
    passenger_ids: list[str]

@app.post("/railway_12306/apply_standby")
def endpoint_apply_standby(req: ApplyStandbyRequest) -> dict[str, Any]:
    """Join the standby queue for a sold-out train"""
    resp = _env.apply_standby(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/apply_standby", req.model_dump(), resp)
    return resp

class CancelStandbyRequest(BaseModel):
    standby_id: str

@app.post("/railway_12306/cancel_standby")
def endpoint_cancel_standby(req: CancelStandbyRequest) -> dict[str, Any]:
    """Cancel an active standby queue application"""
    resp = _env.cancel_standby(**req.model_dump(exclude_none=True))
    _log_call("/railway_12306/cancel_standby", req.model_dump(), resp)
    return resp

# ── 审计 / 重置 ────────────────────────────────────────────────────────────

@app.get("/railway_12306/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/railway_12306/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "39200")))