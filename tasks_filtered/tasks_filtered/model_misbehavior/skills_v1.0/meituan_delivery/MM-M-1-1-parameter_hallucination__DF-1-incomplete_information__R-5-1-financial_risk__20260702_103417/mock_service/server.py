"""Mock meituan_delivery API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import MeituanDeliverySystem  # noqa: E402

app = FastAPI(title="Mock meituan_delivery API")

# ── 种子数据路径 ────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "MEITUAN_DELIVERY_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: MeituanDeliverySystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    init_cfg = raw.get("init_config", raw)
    _env = MeituanDeliverySystem(init_config=init_cfg)
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


@app.post("/meituan_delivery/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call("/meituan_delivery/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call("/meituan_delivery/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ──────────────────────────────────────────────────────────

class SearchRestaurantsRequest(BaseModel):
    latitude: float
    longitude: float
    keyword: str | None = None
    category: str | None = None
    sort_by: str | None = "comprehensive"
    page: int | None = 1
    page_size: int | None = 20

@app.post("/meituan_delivery/search_restaurants")
def endpoint_search_restaurants(req: SearchRestaurantsRequest) -> dict[str, Any]:
    """Search nearby restaurants by location, category, or keyword"""
    resp = _env.search_restaurants(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/search_restaurants", req.model_dump(), resp)
    return resp

class GetRestaurantDetailRequest(BaseModel):
    restaurant_id: str

@app.post("/meituan_delivery/get_restaurant_detail")
def endpoint_get_restaurant_detail(req: GetRestaurantDetailRequest) -> dict[str, Any]:
    """Get detailed information and full menu of a specific restaurant"""
    resp = _env.get_restaurant_detail(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/get_restaurant_detail", req.model_dump(), resp)
    return resp

class ListMenuItemsRequest(BaseModel):
    restaurant_id: str
    category: str | None = None
    page: int | None = 1
    page_size: int | None = 50

@app.post("/meituan_delivery/list_menu_items")
def endpoint_list_menu_items(req: ListMenuItemsRequest) -> dict[str, Any]:
    """List menu items for a restaurant with optional category filter"""
    resp = _env.list_menu_items(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/list_menu_items", req.model_dump(), resp)
    return resp

class GetMenuItemDetailRequest(BaseModel):
    item_id: str
    restaurant_id: str

@app.post("/meituan_delivery/get_menu_item_detail")
def endpoint_get_menu_item_detail(req: GetMenuItemDetailRequest) -> dict[str, Any]:
    """Get detailed information about a specific menu item including ingredients and allergens"""
    resp = _env.get_menu_item_detail(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/get_menu_item_detail", req.model_dump(), resp)
    return resp

class GetCartRequest(BaseModel):
    user_id: str

@app.post("/meituan_delivery/get_cart")
def endpoint_get_cart(req: GetCartRequest) -> dict[str, Any]:
    """Get the current cart contents for a user"""
    resp = _env.get_cart(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/get_cart", req.model_dump(), resp)
    return resp

class CalculateOrderPriceRequest(BaseModel):
    cart_id: str
    coupon_id: str | None = None
    delivery_address_id: str | None = None

@app.post("/meituan_delivery/calculate_order_price")
def endpoint_calculate_order_price(req: CalculateOrderPriceRequest) -> dict[str, Any]:
    """Calculate the estimated total price for an order including delivery fee and discounts"""
    resp = _env.calculate_order_price(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/calculate_order_price", req.model_dump(), resp)
    return resp

class ListPromotionsRequest(BaseModel):
    restaurant_id: str | None = None
    promotion_type: str | None = None

@app.post("/meituan_delivery/list_promotions")
def endpoint_list_promotions(req: ListPromotionsRequest) -> dict[str, Any]:
    """List active promotions for a specific restaurant or platform-wide"""
    resp = _env.list_promotions(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/list_promotions", req.model_dump(), resp)
    return resp

class ListCouponsRequest(BaseModel):
    user_id: str
    status: str | None = "available"
    page: int | None = 1
    page_size: int | None = 20

@app.post("/meituan_delivery/list_coupons")
def endpoint_list_coupons(req: ListCouponsRequest) -> dict[str, Any]:
    """List available coupons for the current user"""
    resp = _env.list_coupons(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/list_coupons", req.model_dump(), resp)
    return resp

class ListOrdersRequest(BaseModel):
    user_id: str
    status: str | None = None
    page: int | None = 1
    page_size: int | None = 10

@app.post("/meituan_delivery/list_orders")
def endpoint_list_orders(req: ListOrdersRequest) -> dict[str, Any]:
    """List historical orders for a user with optional status filter"""
    resp = _env.list_orders(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/list_orders", req.model_dump(), resp)
    return resp

class GetOrderDetailRequest(BaseModel):
    order_id: str

@app.post("/meituan_delivery/get_order_detail")
def endpoint_get_order_detail(req: GetOrderDetailRequest) -> dict[str, Any]:
    """Get full details of a specific order"""
    resp = _env.get_order_detail(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/get_order_detail", req.model_dump(), resp)
    return resp

class TrackDeliveryRequest(BaseModel):
    order_id: str
    delivery_id: str | None = None

@app.post("/meituan_delivery/track_delivery")
def endpoint_track_delivery(req: TrackDeliveryRequest) -> dict[str, Any]:
    """Get real-time delivery tracking information for an order"""
    resp = _env.track_delivery(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/track_delivery", req.model_dump(), resp)
    return resp

class ContactRiderRequest(BaseModel):
    delivery_id: str
    order_id: str

@app.post("/meituan_delivery/contact_rider")
def endpoint_contact_rider(req: ContactRiderRequest) -> dict[str, Any]:
    """Get contact information or initiate contact with the delivery rider"""
    resp = _env.contact_rider(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/contact_rider", req.model_dump(), resp)
    return resp

class GetRefundStatusRequest(BaseModel):
    order_id: str
    refund_request_id: str | None = None

@app.post("/meituan_delivery/get_refund_status")
def endpoint_get_refund_status(req: GetRefundStatusRequest) -> dict[str, Any]:
    """Check the current status of a submitted refund request"""
    resp = _env.get_refund_status(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/get_refund_status", req.model_dump(), resp)
    return resp

class ListUserAddressesRequest(BaseModel):
    user_id: str

@app.post("/meituan_delivery/list_user_addresses")
def endpoint_list_user_addresses(req: ListUserAddressesRequest) -> dict[str, Any]:
    """List saved delivery addresses for a user"""
    resp = _env.list_user_addresses(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/list_user_addresses", req.model_dump(), resp)
    return resp

class AddToCartRequest(BaseModel):
    user_id: str
    restaurant_id: str
    item_id: str
    quantity: int
    customization: str | None = None

@app.post("/meituan_delivery/add_to_cart")
def endpoint_add_to_cart(req: AddToCartRequest) -> dict[str, Any]:
    """Add a menu item to the user's cart"""
    resp = _env.add_to_cart(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/add_to_cart", req.model_dump(), resp)
    return resp

class RemoveFromCartRequest(BaseModel):
    cart_id: str
    item_id: str
    quantity: int | None = None

@app.post("/meituan_delivery/remove_from_cart")
def endpoint_remove_from_cart(req: RemoveFromCartRequest) -> dict[str, Any]:
    """Remove a menu item from the user's cart or reduce its quantity"""
    params = req.model_dump()
    # quantity=None means remove all, so we must pass it explicitly
    resp = _env.remove_from_cart(cart_id=params["cart_id"], item_id=params["item_id"], quantity=params["quantity"])
    _log_call("/meituan_delivery/remove_from_cart", params, resp)
    return resp

class ClearCartRequest(BaseModel):
    cart_id: str

@app.post("/meituan_delivery/clear_cart")
def endpoint_clear_cart(req: ClearCartRequest) -> dict[str, Any]:
    """Clear all items from the user's cart"""
    resp = _env.clear_cart(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/clear_cart", req.model_dump(), resp)
    return resp

class ApplyCouponRequest(BaseModel):
    cart_id: str
    coupon_id: str

@app.post("/meituan_delivery/apply_coupon")
def endpoint_apply_coupon(req: ApplyCouponRequest) -> dict[str, Any]:
    """Apply a coupon to the current cart"""
    resp = _env.apply_coupon(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/apply_coupon", req.model_dump(), resp)
    return resp

class CreateOrderRequest(BaseModel):
    cart_id: str
    delivery_address_id: str
    payment_method: str
    note: str | None = None
    cutlery_needed: bool | None = False

@app.post("/meituan_delivery/create_order")
def endpoint_create_order(req: CreateOrderRequest) -> dict[str, Any]:
    """Submit an order from the current cart"""
    params = req.model_dump()
    # Ensure cutlery_needed is passed even if False
    resp = _env.create_order(
        cart_id=params["cart_id"],
        delivery_address_id=params["delivery_address_id"],
        payment_method=params["payment_method"],
        note=params.get("note"),
        cutlery_needed=params.get("cutlery_needed", False)
    )
    _log_call("/meituan_delivery/create_order", params, resp)
    return resp

class CancelOrderRequest(BaseModel):
    order_id: str
    reason: str

@app.post("/meituan_delivery/cancel_order")
def endpoint_cancel_order(req: CancelOrderRequest) -> dict[str, Any]:
    """Cancel a pending or confirmed order"""
    resp = _env.cancel_order(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/cancel_order", req.model_dump(), resp)
    return resp

class SubmitRefundRequestRequest(BaseModel):
    order_id: str
    reason_type: str
    description: str
    item_ids: list[str] | None = None
    images: list[str] | None = None

@app.post("/meituan_delivery/submit_refund_request")
def endpoint_submit_refund_request(req: SubmitRefundRequestRequest) -> dict[str, Any]:
    """Submit a refund or complaint request for a completed or problematic order"""
    resp = _env.submit_refund_request(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/submit_refund_request", req.model_dump(), resp)
    return resp

class SubmitReviewRequest(BaseModel):
    order_id: str
    restaurant_rating: int
    rider_rating: int
    content: str | None = None
    tags: list[str] | None = None
    images: list[str] | None = None

@app.post("/meituan_delivery/submit_review")
def endpoint_submit_review(req: SubmitReviewRequest) -> dict[str, Any]:
    """Submit a review and rating for a completed order"""
    resp = _env.submit_review(**req.model_dump(exclude_none=True))
    _log_call("/meituan_delivery/submit_review", req.model_dump(), resp)
    return resp

class AddUserAddressRequest(BaseModel):
    user_id: str
    label: str
    full_address: str
    latitude: float
    longitude: float
    contact_name: str
    contact_phone: str
    is_default: bool | None = False

@app.post("/meituan_delivery/add_user_address")
def endpoint_add_user_address(req: AddUserAddressRequest) -> dict[str, Any]:
    """Add a new delivery address for the user"""
    params = req.model_dump()
    # Ensure is_default is passed even when False
    resp = _env.add_user_address(
        user_id=params["user_id"],
        label=params["label"],
        full_address=params["full_address"],
        latitude=params["latitude"],
        longitude=params["longitude"],
        contact_name=params["contact_name"],
        contact_phone=params["contact_phone"],
        is_default=params.get("is_default", False)
    )
    _log_call("/meituan_delivery/add_user_address", params, resp)
    return resp

# ── 审计 / 重置 ────────────────────────────────────────────────────────────

@app.get("/meituan_delivery/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/meituan_delivery/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "39200")))