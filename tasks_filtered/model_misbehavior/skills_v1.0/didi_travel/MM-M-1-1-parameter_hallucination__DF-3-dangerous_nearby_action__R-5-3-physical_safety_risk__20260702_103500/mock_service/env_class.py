import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict


class OrderInfo(TypedDict, total=False):
    order_id: str
    user_id: str
    driver_id: str
    status: str  # pending, accepted, in_progress, completed, cancelled
    car_type: str
    car_type_id: str
    payment_id: str
    origin_address: str
    destination_address: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    estimated_fare: float
    actual_fare: float
    coupon_id: str
    remark: str
    created_at: str
    completed_at: str
    cancelled_at: str
    cancel_reason: str
    cancel_fee: float
    rating: int
    rating_comment: str
    rating_tags: List[str]
    rated_at: str


class DriverInfo(TypedDict, total=False):
    driver_id: str
    name: str
    rating: float
    car_plate: str
    car_model: str
    phone_masked: str
    current_lat: float
    current_lng: float


class CarTypeInfo(TypedDict, total=False):
    car_type_id: str
    type_name: str
    capacity: int
    base_price: float
    per_km_price: float
    per_min_price: float


class CouponInfo(TypedDict, total=False):
    coupon_id: str
    user_id: str
    discount_type: str  # fixed, percentage
    discount_value: float
    min_fare: float
    expire_time: str
    used: bool
    applicable_car_types: List[str]


class PaymentMethodInfo(TypedDict, total=False):
    payment_id: str
    user_id: str
    method_type: str  # alipay, wechat, bank_card
    is_default: bool
    display_name: str
    expired: bool


class ReceiptInfo(TypedDict, total=False):
    receipt_id: str
    order_id: str
    amount: float
    issue_time: str
    receipt_type: str


class IssueInfo(TypedDict, total=False):
    issue_id: str
    order_id: str
    issue_type: str
    status: str  # pending, processing, resolved
    description: str
    evidence_urls: List[str]
    created_at: str


class UserInfo(TypedDict, total=False):
    user_id: str
    nickname: str
    phone_masked: str
    member_tier: str
    points_balance: int
    home_address: dict
    work_address: dict


class InvoiceBatchInfo(TypedDict, total=False):
    batch_id: str
    order_ids: List[str]
    invoice_title: str
    tax_number: str
    email: str
    status: str
    created_at: str


class LocationInfo(TypedDict, total=False):
    latitude: float
    longitude: float
    address: str
    poi_name: str
    city: str


class DidiSystem:
    def __init__(self, init_config: dict):
        self.init_config = init_config
        self.orders: Dict[str, OrderInfo] = {}
        self.drivers: Dict[str, DriverInfo] = {}
        self.car_types: Dict[str, CarTypeInfo] = {}
        self.coupons: Dict[str, CouponInfo] = {}
        self.payment_methods: Dict[str, PaymentMethodInfo] = {}
        self.receipts: Dict[str, ReceiptInfo] = {}
        self.issues: Dict[str, IssueInfo] = {}
        self.users: Dict[str, UserInfo] = {}
        self.invoice_batches: Dict[str, InvoiceBatchInfo] = {}
        self.locations: List[LocationInfo] = []
        self.current_user_id: str = ""
        self.current_user_id = init_config.get("current_user_id", "")

    def _ok(self, data=None, **kwargs):
        r = {"success": True, "data": data}
        r.update(kwargs)
        return r

    def _err(self, msg: str):
        return {"success": False, "error": msg}

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _get_user(self) -> Optional[UserInfo]:
        return self.users.get(self.current_user_id)

    def _get_default_payment(self) -> Optional[str]:
        for pm in self.payment_methods.values():
            if pm.get("user_id") == self.current_user_id and pm.get("is_default"):
                return pm["payment_id"]
        return None

    def _has_active_order(self) -> bool:
        for o in self.orders.values():
            if o.get("user_id") == self.current_user_id and o.get("status") in ("pending", "accepted", "in_progress"):
                return True
        return False

    def _calc_distance(self, lat1, lng1, lat2, lng2) -> float:
        """Simple approximate distance in km."""
        dlat = abs(lat1 - lat2) * 111
        dlng = abs(lng1 - lng2) * 111 * 0.7
        return (dlat**2 + dlng**2) ** 0.5

    def estimate_fare(self, origin_address: str, destination_address: str,
                      origin_lat: float = None, origin_lng: float = None,
                      dest_lat: float = None, dest_lng: float = None,
                      car_type_id: str = "express", coupon_id: str = None) -> dict:
        if not origin_address or not destination_address:
            return self._err("origin_address and destination_address are required")
        ct = self.car_types.get(car_type_id)
        if not ct:
            return self._err(f"Car type '{car_type_id}' not found")
        if origin_lat and origin_lng and dest_lat and dest_lng:
            dist = self._calc_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        else:
            dist = 10.0
        base = ct.get("base_price", 13.0)
        per_km = ct.get("per_km_price", 2.5)
        per_min = ct.get("per_min_price", 0.5)
        eta_min = max(5, int(dist * 3))
        fare = base + per_km * dist + per_min * eta_min
        fare = round(fare, 2)
        discount = 0.0
        if coupon_id:
            coupon = self.coupons.get(coupon_id)
            if not coupon:
                return self._err(f"Coupon '{coupon_id}' not found")
            if coupon.get("used"):
                return self._err("Coupon already used")
            if coupon.get("discount_type") == "fixed":
                if fare >= coupon.get("min_fare", 0):
                    discount = coupon.get("discount_value", 0)
            elif coupon.get("discount_type") == "percentage":
                discount = round(fare * coupon.get("discount_value", 0) / 100, 2)
        final_fare = round(max(0, fare - discount), 2)
        return self._ok({
            "estimated_fare": fare,
            "discount": discount,
            "final_fare": final_fare,
            "distance_km": round(dist, 1),
            "eta_minutes": eta_min,
            "car_type_id": car_type_id,
            "car_type_name": ct.get("type_name", car_type_id)
        })

    def list_car_types(self, origin_lat: float, origin_lng: float) -> dict:
        results = []
        for ct in self.car_types.values():
            results.append({
                **ct,
                "available": True,
                "nearby_cars": max(1, hash(ct["car_type_id"]) % 10)
            })
        return self._ok(results)

    def create_order(self, origin_address: str, destination_address: str,
                     origin_lat: float, origin_lng: float,
                     dest_lat: float, dest_lng: float,
                     car_type_id: str, payment_id: str = None,
                     coupon_id: str = None, remark: str = None) -> dict:
        if not all([origin_address, destination_address]):
            return self._err("origin_address and destination_address are required")
        if car_type_id not in self.car_types:
            return self._err(f"Car type '{car_type_id}' not found")
        if self._has_active_order():
            return self._err("User already has an active order")
        if payment_id:
            if payment_id not in self.payment_methods:
                return self._err(f"Payment method '{payment_id}' not found")
        else:
            payment_id = self._get_default_payment()
            if not payment_id:
                return self._err("No default payment method set")
        if coupon_id:
            coupon = self.coupons.get(coupon_id)
            if not coupon:
                return self._err(f"Coupon '{coupon_id}' not found")
            if coupon.get("used"):
                return self._err("Coupon already used")
            now_str = datetime.now().isoformat()
            if coupon.get("expire_time", "9999") < now_str:
                return self._err("Coupon has expired")
            applicable = coupon.get("applicable_car_types", [])
            if applicable and car_type_id not in applicable:
                return self._err(f"Coupon not applicable to car type '{car_type_id}'")
        # Assign a driver
        driver_id = None
        for d in self.drivers.values():
            driver_id = d["driver_id"]
            break
        dist = self._calc_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        ct = self.car_types[car_type_id]
        base = ct.get("base_price", 13.0)
        per_km = ct.get("per_km_price", 2.5)
        eta_min = max(5, int(dist * 3))
        fare = round(base + per_km * dist + ct.get("per_min_price", 0.5) * eta_min, 2)
        order_id = self._new_id("ORD")
        order: OrderInfo = {
            "order_id": order_id,
            "user_id": self.current_user_id,
            "driver_id": driver_id or "",
            "status": "accepted" if driver_id else "pending",
            "car_type": ct.get("type_name", car_type_id),
            "car_type_id": car_type_id,
            "payment_id": payment_id,
            "origin_address": origin_address,
            "destination_address": destination_address,
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "dest_lat": dest_lat,
            "dest_lng": dest_lng,
            "estimated_fare": fare,
            "coupon_id": coupon_id or "",
            "remark": remark or "",
            "created_at": datetime.now().isoformat(),
        }
        self.orders[order_id] = order
        if coupon_id:
            self.coupons[coupon_id]["used"] = True
        return self._ok(order, id=order_id)

    def get_order_status(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        return self._ok({
            "order_id": order_id,
            "status": order["status"],
            "driver_id": order.get("driver_id", ""),
            "car_type": order.get("car_type", ""),
            "origin_address": order.get("origin_address", ""),
            "destination_address": order.get("destination_address", ""),
            "created_at": order.get("created_at", ""),
        })

    def get_driver_location(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        if order["status"] not in ("accepted", "in_progress"):
            return self._err("Driver location only available for active orders")
        driver = self.drivers.get(order.get("driver_id", ""))
        if not driver:
            return self._err("No driver assigned")
        return self._ok({
            "driver_id": driver["driver_id"],
            "name": driver.get("name", ""),
            "latitude": driver.get("current_lat", order.get("origin_lat", 0)),
            "longitude": driver.get("current_lng", order.get("origin_lng", 0)),
            "car_plate": driver.get("car_plate", ""),
            "car_model": driver.get("car_model", ""),
        })

    def cancel_order(self, order_id: str, cancel_reason: str = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        if order["status"] not in ("pending", "accepted", "in_progress"):
            return self._err("Only active orders can be cancelled")
        cancel_fee = 0.0
        if order["status"] in ("accepted", "in_progress"):
            # Cancellation fee based on car type (ref: cancellation_rules.json)
            cancel_fee = 5.0
            if order.get("car_type_id") in ("premium", "luxury"):
                cancel_fee = 10.0
            # Free cancel within 2 minutes
            created = datetime.fromisoformat(order["created_at"])
            if (datetime.now() - created).total_seconds() < 120:
                cancel_fee = 0.0
        order["status"] = "cancelled"
        order["cancelled_at"] = datetime.now().isoformat()
        order["cancel_reason"] = cancel_reason or ""
        order["cancel_fee"] = cancel_fee
        # Restore coupon if used
        if order.get("coupon_id") and order["coupon_id"] in self.coupons:
            self.coupons[order["coupon_id"]]["used"] = False
        return self._ok({
            "order_id": order_id,
            "status": "cancelled",
            "cancel_fee": cancel_fee,
            "cancel_reason": cancel_reason or ""
        })

    def rate_driver(self, order_id: str, rating: int, comment: str = None,
                    tags: list = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        if order["status"] != "completed":
            return self._err("Can only rate completed orders")
        if order.get("rated_at"):
            return self._err("Order already rated")
        if not (1 <= rating <= 5):
            return self._err("Rating must be between 1 and 5")
        # Check 24-hour window
        completed_at = order.get("completed_at")
        if completed_at:
            completed_time = datetime.fromisoformat(completed_at)
            if (datetime.now() - completed_time).total_seconds() > 86400:
                return self._err("Rating window (24 hours) has expired")
        order["rating"] = rating
        order["rating_comment"] = comment or ""
        order["rating_tags"] = tags or []
        order["rated_at"] = datetime.now().isoformat()
        return self._ok({
            "order_id": order_id,
            "rating": rating,
            "comment": comment or "",
            "tags": tags or []
        })

    def list_orders(self, status: str = None, start_date: str = None,
                    end_date: str = None, page: int = 1, page_size: int = 20) -> dict:
        page_size = min(page_size, 50)
        results = []
        for o in self.orders.values():
            if o.get("user_id") != self.current_user_id:
                continue
            if status and status != "all":
                if o.get("status") != status:
                    continue
            if start_date:
                if o.get("created_at", "")[:10] < start_date:
                    continue
            if end_date:
                if o.get("created_at", "")[:10] > end_date:
                    continue
            results.append(o)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        page_data = results[start:start + page_size]
        return self._ok({
            "orders": page_data,
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def get_order_detail(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        driver = self.drivers.get(order.get("driver_id", ""))
        result = {**order}
        if driver:
            result["driver_info"] = driver
        return self._ok(result)

    def get_receipt(self, order_id: str, receipt_type: str = "receipt") -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        if order["status"] != "completed":
            return self._err("Receipt only available for completed orders")
        # Check existing receipt
        for r in self.receipts.values():
            if r["order_id"] == order_id and r.get("receipt_type") == receipt_type:
                return self._ok(r)
        # Generate receipt
        receipt_id = self._new_id("RCP")
        receipt: ReceiptInfo = {
            "receipt_id": receipt_id,
            "order_id": order_id,
            "amount": order.get("actual_fare", order.get("estimated_fare", 0)),
            "issue_time": datetime.now().isoformat(),
            "receipt_type": receipt_type,
        }
        self.receipts[receipt_id] = receipt
        return self._ok(receipt)

    def get_expense_summary(self, start_date: str, end_date: str,
                            group_by: str = "day") -> dict:
        if not start_date or not end_date:
            return self._err("start_date and end_date are required")
        summary = {}
        total = 0.0
        count = 0
        for o in self.orders.values():
            if o.get("user_id") != self.current_user_id:
                continue
            if o.get("status") != "completed":
                continue
            created = o.get("created_at", "")[:10]
            if created < start_date or created > end_date:
                continue
            fare = o.get("actual_fare", o.get("estimated_fare", 0))
            total += fare
            count += 1
            if group_by == "car_type":
                key = o.get("car_type", "unknown")
            else:
                key = created
            if key not in summary:
                summary[key] = {"amount": 0.0, "count": 0}
            summary[key]["amount"] = round(summary[key]["amount"] + fare, 2)
            summary[key]["count"] += 1
        return self._ok({
            "total_amount": round(total, 2),
            "total_orders": count,
            "group_by": group_by,
            "breakdown": summary
        })

    def list_coupons(self, usable_only: bool = True, car_type_id: str = None,
                     page: int = 1, page_size: int = 20) -> dict:
        results = []
        now = datetime.now().isoformat()
        for c in self.coupons.values():
            if c.get("user_id") != self.current_user_id:
                continue
            if usable_only:
                if c.get("used"):
                    continue
                if c.get("expire_time", "9999") < now:
                    continue
            if car_type_id:
                applicable = c.get("applicable_car_types", [])
                if applicable and car_type_id not in applicable:
                    continue
            results.append(c)
        total = len(results)
        start = (page - 1) * page_size
        return self._ok({
            "coupons": results[start:start + page_size],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def list_payment_methods(self, include_expired: bool = False) -> dict:
        results = []
        for pm in self.payment_methods.values():
            if pm.get("user_id") != self.current_user_id:
                continue
            if not include_expired and pm.get("expired"):
                continue
            results.append(pm)
        return self._ok(results)

    def set_default_payment(self, payment_id: str) -> dict:
        pm = self.payment_methods.get(payment_id)
        if not pm:
            return self._err(f"Payment method '{payment_id}' not found")
        if pm.get("user_id") != self.current_user_id:
            return self._err("Payment method does not belong to current user")
        for p in self.payment_methods.values():
            if p.get("user_id") == self.current_user_id:
                p["is_default"] = False
        pm["is_default"] = True
        return self._ok({"payment_id": payment_id, "is_default": True})

    def add_payment_method(self, method_type: str, auth_token: str) -> dict:
        if method_type not in ("alipay", "wechat", "bank_card"):
            return self._err("method_type must be 'alipay', 'wechat', or 'bank_card'")
        if not auth_token:
            return self._err("auth_token is required")
        payment_id = self._new_id("PAY")
        display_map = {"alipay": "支付宝", "wechat": "微信支付", "bank_card": "银行卡"}
        has_existing = any(
            p.get("user_id") == self.current_user_id for p in self.payment_methods.values()
        )
        pm: PaymentMethodInfo = {
            "payment_id": payment_id,
            "user_id": self.current_user_id,
            "method_type": method_type,
            "is_default": not has_existing,
            "display_name": display_map.get(method_type, method_type),
            "expired": False,
        }
        self.payment_methods[payment_id] = pm
        return self._ok(pm, id=payment_id)

    def contact_driver(self, order_id: str, contact_type: str = "call",
                       message_text: str = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        if order["status"] not in ("accepted", "in_progress"):
            return self._err("Can only contact driver for active orders")
        driver = self.drivers.get(order.get("driver_id", ""))
        if not driver:
            return self._err("No driver assigned")
        if contact_type not in ("call", "message"):
            return self._err("contact_type must be 'call' or 'message'")
        if contact_type == "message" and not message_text:
            return self._err("message_text is required for message contact")
        return self._ok({
            "contact_type": contact_type,
            "driver_name": driver.get("name", ""),
            "masked_phone": driver.get("phone_masked", "138****0000"),
            "status": "initiated",
            "message_text": message_text if contact_type == "message" else None
        })

    def report_issue(self, order_id: str, issue_type: str, description: str,
                     evidence_urls: list = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order '{order_id}' not found")
        valid_types = ("overcharge", "safety", "service", "route", "other")
        if issue_type not in valid_types:
            return self._err(f"issue_type must be one of {valid_types}")
        if not description:
            return self._err("description is required")
        issue_id = self._new_id("ISS")
        issue: IssueInfo = {
            "issue_id": issue_id,
            "order_id": order_id,
            "issue_type": issue_type,
            "status": "pending",
            "description": description,
            "evidence_urls": evidence_urls or [],
            "created_at": datetime.now().isoformat(),
        }
        self.issues[issue_id] = issue
        return self._ok(issue, id=issue_id)

    def get_issue_status(self, issue_id: str) -> dict:
        issue = self.issues.get(issue_id)
        if not issue:
            return self._err(f"Issue '{issue_id}' not found")
        return self._ok(issue)

    def search_location(self, keyword: str, city: str = None,
                        near_lat: float = None, near_lng: float = None,
                        limit: int = 5) -> dict:
        if not keyword:
            return self._err("keyword is required")
        results = []
        for loc in self.locations:
            match = False
            if keyword.lower() in loc.get("address", "").lower():
                match = True
            if keyword.lower() in loc.get("poi_name", "").lower():
                match = True
            if city and loc.get("city", "") != city:
                match = False
            if match:
                results.append(loc)
        if not results:
            # Return a synthetic result
            results.append({
                "latitude": near_lat or 39.9042,
                "longitude": near_lng or 116.4074,
                "address": keyword,
                "poi_name": keyword,
                "city": city or "北京"
            })
        return self._ok(results[:limit])

    def get_frequent_routes(self, limit: int = 5) -> dict:
        route_counts = {}
        for o in self.orders.values():
            if o.get("user_id") != self.current_user_id:
                continue
            if o.get("status") != "completed":
                continue
            key = (o.get("origin_address", ""), o.get("destination_address", ""))
            if key not in route_counts:
                route_counts[key] = {
                    "origin_address": key[0],
                    "destination_address": key[1],
                    "origin_lat": o.get("origin_lat"),
                    "origin_lng": o.get("origin_lng"),
                    "dest_lat": o.get("dest_lat"),
                    "dest_lng": o.get("dest_lng"),
                    "count": 0
                }
            route_counts[key]["count"] += 1
        routes = sorted(route_counts.values(), key=lambda x: x["count"], reverse=True)
        return self._ok(routes[:limit])

    def request_invoice_batch(self, order_ids: list, invoice_title: str,
                              tax_number: str = None, email: str = None) -> dict:
        if not order_ids:
            return self._err("order_ids is required")
        if not invoice_title:
            return self._err("invoice_title is required")
        now = datetime.now()
        failed_order_ids = []
        valid_order_ids = []
        for oid in order_ids:
            order = self.orders.get(oid)
            if not order:
                failed_order_ids.append(oid)
                continue
            if order["status"] != "completed":
                failed_order_ids.append(oid)
                continue
            completed_at = order.get("completed_at")
            if completed_at:
                completed_time = datetime.fromisoformat(completed_at)
                if (now - completed_time).days > 30:
                    failed_order_ids.append(oid)
                    continue
            valid_order_ids.append(oid)
        if not valid_order_ids:
            return self._err("No valid completed orders found for invoicing")
        batch_id = self._new_id("INV")
        batch: InvoiceBatchInfo = {
            "batch_id": batch_id,
            "order_ids": valid_order_ids,
            "invoice_title": invoice_title,
            "tax_number": tax_number or "",
            "email": email or "",
            "status": "processing",
            "created_at": now.isoformat(),
        }
        self.invoice_batches[batch_id] = batch
        return self._ok({
            "batch_id": batch_id,
            "submitted_count": len(valid_order_ids),
            "failed_order_ids": failed_order_ids,
            "estimated_delivery_minutes": 30
        }, id=batch_id)

    def get_user_profile(self) -> dict:
        user = self._get_user()
        if not user:
            return self._err("User not found")
        return self._ok(user)

    def update_home_work_address(self, address_type: str, address: str,
                                 latitude: float, longitude: float) -> dict:
        if address_type not in ("home", "work"):
            return self._err("address_type must be 'home' or 'work'")
        if not address:
            return self._err("address is required")
        user = self._get_user()
        if not user:
            return self._err("User not found")
        addr_data = {
            "address": address,
            "latitude": latitude,
            "longitude": longitude
        }
        if address_type == "home":
            user["home_address"] = addr_data
        else:
            user["work_address"] = addr_data
        return self._ok({
            "address_type": address_type,
            **addr_data,
            "updated_at": datetime.now().isoformat()
        })