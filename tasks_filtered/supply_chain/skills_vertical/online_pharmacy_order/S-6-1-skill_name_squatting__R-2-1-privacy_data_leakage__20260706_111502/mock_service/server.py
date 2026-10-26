"""Mock Online Pharmacy Order API service (FastAPI)."""

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

from env_class import OnlinePharmacyOrderManagementSystem  # noqa: E402

app = FastAPI(title="Mock Online Pharmacy Order API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "ONLINE_PHARMACY_ORDER_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: OnlinePharmacyOrderManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = OnlinePharmacyOrderManagementSystem(init_config=init_cfg)
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


@app.post("/online_pharmacy_order/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/online_pharmacy_order/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/online_pharmacy_order/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetMedicationByNameAndDosageRequest(BaseModel):
    name: str
    dosage: str

@app.post("/online_pharmacy_order/get_medication_by_name_and_dosage")
def endpoint_get_medication_by_name_and_dosage(req: GetMedicationByNameAndDosageRequest) -> dict[str, Any]:
    """Retrieve catalog entry for specified medication name and dosage."""
    resp = _env.get_medication_by_name_and_dosage(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_medication_by_name_and_dosage", req.model_dump(), resp)
    return resp


class CheckMedicationInventoryRequest(BaseModel):
    medication_id: str

@app.post("/online_pharmacy_order/check_medication_inventory")
def endpoint_check_medication_inventory(req: CheckMedicationInventoryRequest) -> dict[str, Any]:
    """Query current stock quantity for a medication."""
    resp = _env.check_medication_inventory(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/check_medication_inventory", req.model_dump(), resp)
    return resp


class IsPrescriptionRequiredRequest(BaseModel):
    medication_id: str

@app.post("/online_pharmacy_order/is_prescription_required")
def endpoint_is_prescription_required(req: IsPrescriptionRequiredRequest) -> dict[str, Any]:
    """Check whether a given medication requires a prescription."""
    resp = _env.is_prescription_required(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/is_prescription_required", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/online_pharmacy_order/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Get user profile by user_id."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_user_by_id", req.model_dump(), resp)
    return resp


class GetSavedAddressesForUserRequest(BaseModel):
    user_id: str

@app.post("/online_pharmacy_order/get_saved_addresses_for_user")
def endpoint_get_saved_addresses_for_user(req: GetSavedAddressesForUserRequest) -> dict[str, Any]:
    """List all saved shipping addresses for a specific user."""
    resp = _env.get_saved_addresses_for_user(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_saved_addresses_for_user", req.model_dump(), resp)
    return resp


class GetAddressByDetailsRequest(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    user_id: str | None = None

@app.post("/online_pharmacy_order/get_address_by_details")
def endpoint_get_address_by_details(req: GetAddressByDetailsRequest) -> dict[str, Any]:
    """Locate a user’s address by street, city, etc."""
    resp = _env.get_address_by_details(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_address_by_details", req.model_dump(), resp)
    return resp


class ValidateAddressForUserRequest(BaseModel):
    address_id: str
    user_id: str

@app.post("/online_pharmacy_order/validate_address_for_user")
def endpoint_validate_address_for_user(req: ValidateAddressForUserRequest) -> dict[str, Any]:
    """Confirm that a shipping address is valid and belongs to the user."""
    resp = _env.validate_address_for_user(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/validate_address_for_user", req.model_dump(), resp)
    return resp


class GetPrescriptionRecordRequest(BaseModel):
    user_id: str
    medication_id: str

@app.post("/online_pharmacy_order/get_prescription_record")
def endpoint_get_prescription_record(req: GetPrescriptionRecordRequest) -> dict[str, Any]:
    """Retrieve a user’s prescription record for a medication."""
    resp = _env.get_prescription_record(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_prescription_record", req.model_dump(), resp)
    return resp


class IsPrescriptionValidatedRequest(BaseModel):
    user_id: str
    medication_id: str

@app.post("/online_pharmacy_order/is_prescription_validated")
def endpoint_is_prescription_validated(req: IsPrescriptionValidatedRequest) -> dict[str, Any]:
    """Query if a user has a validated prescription for a specific medication."""
    resp = _env.is_prescription_validated(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/is_prescription_validated", req.model_dump(), resp)
    return resp


class VerifyDosageAndFormMatchRequest(BaseModel):
    medication_id: str
    requested_dosage: str
    requested_dosage_form: str

@app.post("/online_pharmacy_order/verify_dosage_and_form_match")
def endpoint_verify_dosage_and_form_match(req: VerifyDosageAndFormMatchRequest) -> dict[str, Any]:
    """Check that requested dosage and dosage form match medication catalog entry."""
    resp = _env.verify_dosage_and_form_match(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/verify_dosage_and_form_match", req.model_dump(), resp)
    return resp


class GetOrderByIdRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/get_order_by_id")
def endpoint_get_order_by_id(req: GetOrderByIdRequest) -> dict[str, Any]:
    """Retrieve order details using order_id."""
    resp = _env.get_order_by_id(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_order_by_id", req.model_dump(), resp)
    return resp


class GetOrderStatusRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/get_order_status")
def endpoint_get_order_status(req: GetOrderStatusRequest) -> dict[str, Any]:
    """Query fulfillment status of an order."""
    resp = _env.get_order_status(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_order_status", req.model_dump(), resp)
    return resp


class GetPaymentStatusRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/get_payment_status")
def endpoint_get_payment_status(req: GetPaymentStatusRequest) -> dict[str, Any]:
    """Check if an order has been paid."""
    resp = _env.get_payment_status(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_payment_status", req.model_dump(), resp)
    return resp


class GetFulfillmentDetailsRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/get_fulfillment_details")
def endpoint_get_fulfillment_details(req: GetFulfillmentDetailsRequest) -> dict[str, Any]:
    """Retrieve fulfillment and shipping details for an order."""
    resp = _env.get_fulfillment_details(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/get_fulfillment_details", req.model_dump(), resp)
    return resp


class CreateOrderRequest(BaseModel):
    user_id: str
    items: list
    delivery_address_id: str

@app.post("/online_pharmacy_order/create_order")
def endpoint_create_order(req: CreateOrderRequest) -> dict[str, Any]:
    """Create a new order for a user with specified medications, dosage, quantity, and delivery address."""
    resp = _env.create_order(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/create_order", req.model_dump(), resp)
    return resp


class ReserveMedicationInventoryRequest(BaseModel):
    medication_id: str
    quantity: int

@app.post("/online_pharmacy_order/reserve_medication_inventory")
def endpoint_reserve_medication_inventory(req: ReserveMedicationInventoryRequest) -> dict[str, Any]:
    """Decrement medication inventory by reserved quantity for an order (during order creation)."""
    resp = _env.reserve_medication_inventory(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/reserve_medication_inventory", req.model_dump(), resp)
    return resp


class ValidatePrescriptionForOrderRequest(BaseModel):
    order_id: str
    medication_id: str

@app.post("/online_pharmacy_order/validate_prescription_for_order")
def endpoint_validate_prescription_for_order(req: ValidatePrescriptionForOrderRequest) -> dict[str, Any]:
    """Process and mark a prescription as validated for an order item."""
    resp = _env.validate_prescription_for_order(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/validate_prescription_for_order", req.model_dump(), resp)
    return resp


class MarkOrderAsPaidRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/mark_order_as_paid")
def endpoint_mark_order_as_paid(req: MarkOrderAsPaidRequest) -> dict[str, Any]:
    """Update an order’s payment_status to "paid"."""
    resp = _env.mark_order_as_paid(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/mark_order_as_paid", req.model_dump(), resp)
    return resp


class UpdateOrderFulfillmentStatusRequest(BaseModel):
    order_id: str
    new_status: str

@app.post("/online_pharmacy_order/update_order_fulfillment_status")
def endpoint_update_order_fulfillment_status(req: UpdateOrderFulfillmentStatusRequest) -> dict[str, Any]:
    """Set the fulfillment status of an order (e.g., preparing, shipped, delivered)."""
    resp = _env.update_order_fulfillment_status(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/update_order_fulfillment_status", req.model_dump(), resp)
    return resp


class UpdateDeliveryDetailsRequest(BaseModel):
    order_id: str
    fulfillment_details: str

@app.post("/online_pharmacy_order/update_delivery_details")
def endpoint_update_delivery_details(req: UpdateDeliveryDetailsRequest) -> dict[str, Any]:
    """Assign shipping/tracking info to an order after fulfillment."""
    resp = _env.update_delivery_details(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/update_delivery_details", req.model_dump(), resp)
    return resp


class CancelOrderRequest(BaseModel):
    order_id: str

@app.post("/online_pharmacy_order/cancel_order")
def endpoint_cancel_order(req: CancelOrderRequest) -> dict[str, Any]:
    """Cancel an existing order and restore medication inventory if permitted."""
    resp = _env.cancel_order(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/cancel_order", req.model_dump(), resp)
    return resp


class ModifyOrderItemRequest(BaseModel):
    order_id: str
    order_item_idx: int
    medication_id: str | None = None
    dosage: str | None = None
    quantity: int | None = None

@app.post("/online_pharmacy_order/modify_order_item")
def endpoint_modify_order_item(req: ModifyOrderItemRequest) -> dict[str, Any]:
    """Adjust medication, dosage, or quantity of an order item prior to fulfillment."""
    resp = _env.modify_order_item(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/modify_order_item", req.model_dump(), resp)
    return resp


class AddAddressToUserRequest(BaseModel):
    user_id: str
    address_info: dict

@app.post("/online_pharmacy_order/add_address_to_user")
def endpoint_add_address_to_user(req: AddAddressToUserRequest) -> dict[str, Any]:
    """Save a new shipping address to a user’s profile."""
    resp = _env.add_address_to_user(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/add_address_to_user", req.model_dump(), resp)
    return resp


class RemoveAddressFromUserRequest(BaseModel):
    user_id: str
    address_id: str

@app.post("/online_pharmacy_order/remove_address_from_user")
def endpoint_remove_address_from_user(req: RemoveAddressFromUserRequest) -> dict[str, Any]:
    """Remove a shipping address from a user’s profile."""
    resp = _env.remove_address_from_user(**req.model_dump(exclude_none=True))
    _log_call("/online_pharmacy_order/remove_address_from_user", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/online_pharmacy_order/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/online_pharmacy_order/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9304")))
