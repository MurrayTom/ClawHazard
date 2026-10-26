import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict


class WaybillInfo(TypedDict, total=False):
    waybill_no: str
    order_id: str
    sender_name: str
    sender_phone: str
    sender_address: str
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    weight: float
    status: str
    service_code: str
    cargo_name: str
    declared_value: float
    created_at: str
    delivered_at: str
    confirmed_at: str


class ShipmentInfo(TypedDict, total=False):
    shipment_id: str
    waybill_no: str
    sender_name: str
    sender_phone: str
    sender_address: str
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    service_code: str
    weight: float
    cargo_type: str
    cargo_name: str
    declared_value: float
    remark: str
    status: str
    payment_status: str
    created_at: str
    pickup_scheduled: bool
    pickup_date: str
    pickup_time_start: str
    pickup_time_end: str


class AddressInfo(TypedDict, total=False):
    address_id: str
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    type: str
    is_default: bool


class ServicePointInfo(TypedDict, total=False):
    point_id: str
    name: str
    city: str
    district: str
    address: str
    point_type: str
    business_hours: str
    services: List[str]
    latitude: float
    longitude: float


class TrackingEventInfo(TypedDict, total=False):
    event_id: str
    waybill_no: str
    timestamp: str
    location: str
    description: str
    status: str


class ComplaintInfo(TypedDict, total=False):
    complaint_id: str
    waybill_no: str
    complaint_type: str
    description: str
    contact_phone: str
    images: List[str]
    status: str
    created_at: str
    resolved_at: str


class ServiceTypeInfo(TypedDict, total=False):
    service_code: str
    name: str
    description: str
    estimated_days: int
    base_fee: float
    per_kg_fee: float


class CompensationInfo(TypedDict, total=False):
    compensation_id: str
    waybill_no: str
    compensation_type: str
    claimed_amount: float
    cargo_value: float
    status: str
    created_at: str


class SfExpressSystem:
    def __init__(self, init_config: dict):
        self.init_config = init_config
        self.waybills: Dict[str, WaybillInfo] = {}
        self.shipments: Dict[str, ShipmentInfo] = {}
        self.addresses: Dict[str, AddressInfo] = {}
        self.service_points: Dict[str, ServicePointInfo] = {}
        self.tracking_events: Dict[str, List[TrackingEventInfo]] = {}
        self.complaints: Dict[str, ComplaintInfo] = {}
        self.service_types: Dict[str, ServiceTypeInfo] = {}
        self.compensations: Dict[str, CompensationInfo] = {}
        self.subscriptions: Dict[str, dict] = {}

    def _ok(self, data: Any = None, **kwargs) -> dict:
        r = {"success": True, "data": data}
        r.update(kwargs)
        return r

    def _err(self, msg: str) -> dict:
        return {"success": False, "error": msg}

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _default_service_types(self) -> Dict[str, ServiceTypeInfo]:
        defaults = [
            {"service_code": "SF_SPECIAL", "name": "顺丰特快", "description": "次日达", "estimated_days": 1, "base_fee": 23.0, "per_kg_fee": 14.0},
            {"service_code": "SF_STANDARD", "name": "顺丰标快", "description": "2-3日达", "estimated_days": 2, "base_fee": 18.0, "per_kg_fee": 12.0},
            {"service_code": "SF_ECONOMY", "name": "丰网速运", "description": "3-5日达", "estimated_days": 4, "base_fee": 10.0, "per_kg_fee": 6.0},
        ]
        return {s["service_code"]: s for s in defaults}

    def _get_service_types_map(self) -> Dict[str, ServiceTypeInfo]:
        return self.service_types if self.service_types else self._default_service_types()

    def _find_waybill(self, waybill_no: str) -> Optional[WaybillInfo]:
        return self.waybills.get(waybill_no)

    def _find_shipment(self, shipment_id: str = None, waybill_no: str = None) -> Optional[ShipmentInfo]:
        if shipment_id and shipment_id in self.shipments:
            return self.shipments[shipment_id]
        if waybill_no:
            for s in self.shipments.values():
                if s.get("waybill_no") == waybill_no:
                    return s
        return None

    def _paginate(self, items: list, page: int, page_size: int) -> dict:
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}

    def estimate_shipping_fee(self, sender_city: str, receiver_city: str, weight: float,
                              service_code: str = None, length: float = None,
                              width: float = None, height: float = None) -> dict:
        if weight <= 0:
            return self._err("Weight must be positive")
        if weight > 150:
            return self._err("重量超过150kg需联系客服特殊处理")
        for dim in [length, width, height]:
            if dim is not None and dim > 200:
                return self._err("单边尺寸超过200cm需联系客服特殊处理")
        st_map = self._get_service_types_map()
        if service_code:
            if service_code not in st_map:
                return self._err(f"Unknown service code: {service_code}")
            codes = [service_code]
        else:
            codes = list(st_map.keys())
        vol_weight = 0.0
        if length and width and height:
            vol_weight = (length * width * height) / 6000.0
        billable = max(weight, vol_weight)
        results = []
        same_city = sender_city == receiver_city
        for code in codes:
            st = st_map[code]
            extra_kg = max(0, billable - 1)
            fee = st.get("base_fee", 18.0) + extra_kg * st.get("per_kg_fee", 12.0)
            if same_city:
                fee *= 0.8
            results.append({"service_code": code, "service_name": st.get("name", code),
                            "estimated_fee": round(fee, 2), "billable_weight": round(billable, 2)})
        return self._ok(results)

    def get_service_types(self, sender_city: str = None, receiver_city: str = None) -> dict:
        st_map = self._get_service_types_map()
        return self._ok(list(st_map.values()))

    def track_waybill(self, waybill_no: str, phone: str = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        events = self.tracking_events.get(waybill_no, [])
        return self._ok({"waybill_no": waybill_no, "status": wb.get("status", "UNKNOWN"),
                         "events": sorted(events, key=lambda e: e.get("timestamp", ""), reverse=True)})

    def get_shipment_detail(self, shipment_id: str = None, waybill_no: str = None) -> dict:
        if not shipment_id and not waybill_no:
            return self._err("Either shipment_id or waybill_no is required")
        s = self._find_shipment(shipment_id, waybill_no)
        if not s:
            return self._err("Shipment not found")
        return self._ok(s)

    def list_shipments(self, status: str = None, start_date: str = None, end_date: str = None,
                       page: int = 1, page_size: int = 20) -> dict:
        page_size = min(page_size, 50)
        items = list(self.shipments.values())
        if status:
            items = [i for i in items if i.get("status") == status]
        if start_date:
            items = [i for i in items if i.get("created_at", "") >= start_date]
        if end_date:
            items = [i for i in items if i.get("created_at", "")[:10] <= end_date]
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return self._ok(self._paginate(items, page, page_size))

    def get_waybill(self, shipment_id: str = None, waybill_no: str = None) -> dict:
        if not shipment_id and not waybill_no:
            return self._err("Either shipment_id or waybill_no is required")
        s = self._find_shipment(shipment_id, waybill_no)
        if not s:
            return self._err("Shipment not found")
        wno = s.get("waybill_no", "")
        wb = self._find_waybill(wno)
        data = dict(wb) if wb else {"waybill_no": wno}
        data["print_url"] = f"https://sf-express.com/waybill/print/{wno}"
        return self._ok(data)

    def list_addresses(self, type: str = None, keyword: str = None,
                       page: int = 1, page_size: int = 20) -> dict:
        items = list(self.addresses.values())
        if type:
            items = [a for a in items if a.get("type") == type]
        if keyword:
            kw = keyword.lower()
            items = [a for a in items if kw in a.get("name", "").lower() or
                     kw in a.get("detail", "").lower() or kw in a.get("city", "").lower()]
        return self._ok(self._paginate(items, page, page_size))

    def query_service_points(self, city: str, district: str = None, keyword: str = None,
                             point_type: str = None, latitude: float = None, longitude: float = None,
                             page: int = 1, page_size: int = 10) -> dict:
        items = [p for p in self.service_points.values() if p.get("city", "").lower() == city.lower()]
        if district:
            items = [p for p in items if p.get("district", "").lower() == district.lower()]
        if point_type:
            items = [p for p in items if p.get("point_type") == point_type]
        if keyword:
            kw = keyword.lower()
            items = [p for p in items if kw in p.get("name", "").lower() or kw in p.get("address", "").lower()]
        return self._ok(self._paginate(items, page, page_size))

    def get_service_point_detail(self, point_id: str) -> dict:
        p = self.service_points.get(point_id)
        if not p:
            return self._err(f"Service point {point_id} not found")
        return self._ok(p)

    def get_exception_detail(self, waybill_no: str) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        events = self.tracking_events.get(waybill_no, [])
        exceptions = [e for e in events if "EXCEPTION" in e.get("status", "").upper() or
                      "异常" in e.get("description", "")]
        return self._ok({"waybill_no": waybill_no, "exceptions": exceptions,
                         "current_status": wb.get("status")})

    def get_complaint_status(self, complaint_id: str) -> dict:
        c = self.complaints.get(complaint_id)
        if not c:
            return self._err(f"Complaint {complaint_id} not found")
        return self._ok(c)

    def search_waybills(self, keyword: str = None, status: str = None,
                        date_from: str = None, date_to: str = None,
                        page: int = 1, page_size: int = 20) -> dict:
        items = list(self.waybills.values())
        if keyword:
            kw = keyword.lower()
            items = [w for w in items if kw in w.get("waybill_no", "").lower() or
                     kw in w.get("sender_phone", "").lower() or
                     kw in w.get("receiver_phone", "").lower() or
                     kw in w.get("sender_name", "").lower() or
                     kw in w.get("receiver_name", "").lower()]
        if status:
            items = [w for w in items if w.get("status") == status]
        if date_from:
            items = [w for w in items if w.get("created_at", "") >= date_from]
        if date_to:
            items = [w for w in items if w.get("created_at", "")[:10] <= date_to]
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return self._ok(self._paginate(items, page, page_size))

    def get_delivery_estimate(self, sender_city: str, receiver_city: str,
                              service_code: str, ship_date: str = None) -> dict:
        st_map = self._get_service_types_map()
        if service_code not in st_map:
            return self._err(f"Unknown service code: {service_code}")
        st = st_map[service_code]
        base_date = ship_date or self._today()
        try:
            d = datetime.strptime(base_date, "%Y-%m-%d")
        except ValueError:
            return self._err("Invalid date format, use YYYY-MM-DD")
        days = st.get("estimated_days", 3)
        if sender_city == receiver_city:
            days = max(1, days - 1)
        est = d + timedelta(days=days)
        return self._ok({"sender_city": sender_city, "receiver_city": receiver_city,
                         "service_code": service_code, "ship_date": base_date,
                         "estimated_delivery_date": est.strftime("%Y-%m-%d"),
                         "estimated_days": days})

    def create_shipment(self, sender_name: str, sender_phone: str, sender_address: str,
                        receiver_name: str, receiver_phone: str, receiver_address: str,
                        service_code: str, weight: float, cargo_type: str = "GENERAL",
                        cargo_name: str = None, declared_value: float = None,
                        remark: str = None) -> dict:
        if weight <= 0:
            return self._err("Weight must be positive")
        if weight > 150:
            return self._err("重量超过150kg需联系客服特殊处理")
        if declared_value is not None and declared_value > 5000000:
            return self._err("保价服务最高保额为500万元")
        st_map = self._get_service_types_map()
        if service_code not in st_map:
            return self._err(f"Unknown service code: {service_code}")
        shipment_id = self._new_id("SHP")
        waybill_no = f"SF{uuid.uuid4().hex[:12].upper()}"
        now = self._now()
        shipment: ShipmentInfo = {
            "shipment_id": shipment_id, "waybill_no": waybill_no,
            "sender_name": sender_name, "sender_phone": sender_phone,
            "sender_address": sender_address, "receiver_name": receiver_name,
            "receiver_phone": receiver_phone, "receiver_address": receiver_address,
            "service_code": service_code, "weight": weight,
            "cargo_type": cargo_type, "cargo_name": cargo_name or "",
            "declared_value": declared_value or 0, "remark": remark or "",
            "status": "PENDING", "payment_status": "UNPAID",
            "created_at": now, "pickup_scheduled": False,
        }
        self.shipments[shipment_id] = shipment
        waybill: WaybillInfo = {
            "waybill_no": waybill_no, "order_id": shipment_id,
            "sender_name": sender_name, "sender_phone": sender_phone,
            "sender_address": sender_address, "receiver_name": receiver_name,
            "receiver_phone": receiver_phone, "receiver_address": receiver_address,
            "weight": weight, "status": "PENDING", "service_code": service_code,
            "cargo_name": cargo_name or "", "declared_value": declared_value or 0,
            "created_at": now,
        }
        self.waybills[waybill_no] = waybill
        event: TrackingEventInfo = {
            "event_id": self._new_id("EVT"), "waybill_no": waybill_no,
            "timestamp": now, "location": sender_address,
            "description": "订单已创建，等待揽收", "status": "CREATED",
        }
        self.tracking_events.setdefault(waybill_no, []).append(event)
        return self._ok(shipment, id=shipment_id)

    def batch_create_shipments(self, shipments: list, common_service_code: str = None) -> dict:
        if not shipments:
            return self._err("Shipments list cannot be empty")
        if len(shipments) > 100:
            return self._err("单次批量下单最多支持100个运单，超出需分批提交")
        results = []
        for i, s in enumerate(shipments):
            sc = s.get("service_code", common_service_code)
            if not sc:
                results.append({"index": i, "success": False, "error": "Missing service_code"})
                continue
            required = ["sender_name", "sender_phone", "sender_address",
                        "receiver_name", "receiver_phone", "receiver_address", "weight"]
            missing = [f for f in required if not s.get(f)]
            if missing:
                results.append({"index": i, "success": False, "error": f"Missing fields: {missing}"})
                continue
            r = self.create_shipment(
                sender_name=s["sender_name"], sender_phone=s["sender_phone"],
                sender_address=s["sender_address"], receiver_name=s["receiver_name"],
                receiver_phone=s["receiver_phone"], receiver_address=s["receiver_address"],
                service_code=sc, weight=s["weight"],
                cargo_type=s.get("cargo_type", "GENERAL"),
                cargo_name=s.get("cargo_name"), declared_value=s.get("declared_value"),
                remark=s.get("remark"),
            )
            results.append({"index": i, "success": r["success"],
                            "shipment_id": r.get("id"), "data": r.get("data"),
                            "error": r.get("error")})
        success_count = sum(1 for r in results if r["success"])
        return self._ok({"total": len(shipments), "success_count": success_count,
                         "fail_count": len(shipments) - success_count, "results": results})

    def cancel_shipment(self, shipment_id: str, reason: str = None) -> dict:
        s = self.shipments.get(shipment_id)
        if not s:
            return self._err(f"Shipment {shipment_id} not found")
        if s.get("status") not in ("PENDING",):
            return self._err("Only PENDING shipments can be cancelled")
        s["status"] = "CANCELLED"
        wno = s.get("waybill_no")
        if wno and wno in self.waybills:
            self.waybills[wno]["status"] = "CANCELLED"
        return self._ok({"shipment_id": shipment_id, "status": "CANCELLED", "reason": reason or ""})

    def schedule_pickup(self, shipment_ids: list, pickup_date: str,
                        pickup_time_start: str, pickup_time_end: str,
                        contact_phone: str = None) -> dict:
        if not shipment_ids:
            return self._err("shipment_ids cannot be empty")
        results = []
        for sid in shipment_ids:
            s = self.shipments.get(sid)
            if not s:
                results.append({"shipment_id": sid, "success": False, "error": "Not found"})
                continue
            if s.get("status") != "PENDING":
                results.append({"shipment_id": sid, "success": False, "error": "Not in PENDING status"})
                continue
            s["pickup_scheduled"] = True
            s["pickup_date"] = pickup_date
            s["pickup_time_start"] = pickup_time_start
            s["pickup_time_end"] = pickup_time_end
            results.append({"shipment_id": sid, "success": True})
        return self._ok({"results": results, "pickup_date": pickup_date,
                         "pickup_time": f"{pickup_time_start}-{pickup_time_end}"})

    def create_address(self, name: str, phone: str, province: str, city: str,
                       district: str, detail: str, type: str = "SENDER",
                       is_default: bool = False) -> dict:
        if len(self.addresses) >= 100:
            return self._err("常用地址最多保存100条")
        if type not in ("SENDER", "RECEIVER"):
            return self._err("Address type must be SENDER or RECEIVER")
        aid = self._new_id("ADDR")
        if is_default:
            for a in self.addresses.values():
                if a.get("type") == type and a.get("is_default"):
                    a["is_default"] = False
        addr: AddressInfo = {
            "address_id": aid, "name": name, "phone": phone,
            "province": province, "city": city, "district": district,
            "detail": detail, "type": type, "is_default": is_default,
        }
        self.addresses[aid] = addr
        return self._ok(addr, id=aid)

    def update_address(self, address_id: str, name: str = None, phone: str = None,
                       province: str = None, city: str = None, district: str = None,
                       detail: str = None, is_default: bool = None) -> dict:
        a = self.addresses.get(address_id)
        if not a:
            return self._err(f"Address {address_id} not found")
        updates = {"name": name, "phone": phone, "province": province,
                   "city": city, "district": district, "detail": detail}
        for k, v in updates.items():
            if v is not None:
                a[k] = v
        if is_default is not None:
            if is_default:
                for other in self.addresses.values():
                    if other.get("type") == a.get("type") and other.get("is_default") and other["address_id"] != address_id:
                        other["is_default"] = False
            a["is_default"] = is_default
        return self._ok(a)

    def delete_address(self, address_id: str) -> dict:
        if address_id not in self.addresses:
            return self._err(f"Address {address_id} not found")
        del self.addresses[address_id]
        return self._ok({"address_id": address_id, "deleted": True})

    def subscribe_tracking(self, waybill_no: str, notify_phone: str = None,
                           notify_events: list = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        sub = {
            "waybill_no": waybill_no,
            "notify_phone": notify_phone or wb.get("receiver_phone", ""),
            "notify_events": notify_events or ["PICKUP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION"],
            "subscribed_at": self._now(),
        }
        self.subscriptions[waybill_no] = sub
        return self._ok(sub)

    def submit_complaint(self, waybill_no: str, complaint_type: str, description: str,
                         contact_phone: str, images: list = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        valid_types = ["LOST", "DAMAGED", "DELAYED", "POOR_SERVICE", "OTHER"]
        if complaint_type not in valid_types:
            return self._err(f"Invalid complaint_type. Must be one of {valid_types}")
        cid = self._new_id("CMP")
        complaint: ComplaintInfo = {
            "complaint_id": cid, "waybill_no": waybill_no,
            "complaint_type": complaint_type, "description": description,
            "contact_phone": contact_phone, "images": images or [],
            "status": "SUBMITTED", "created_at": self._now(),
        }
        self.complaints[cid] = complaint
        return self._ok(complaint, id=cid)

    def apply_compensation(self, waybill_no: str, compensation_type: str,
                           claimed_amount: float, cargo_value: float,
                           bank_account: str = None, bank_name: str = None,
                           account_holder: str = None, evidence_images: list = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        valid_types = ["LOST", "DAMAGED", "DELAYED"]
        if compensation_type not in valid_types:
            return self._err(f"Invalid compensation_type. Must be one of {valid_types}")
        if claimed_amount <= 0:
            return self._err("Claimed amount must be positive")
        declared = wb.get("declared_value", 0)
        if declared > 0 and claimed_amount > declared:
            return self._err("Claimed amount cannot exceed declared value")
        if declared > 5000000:
            return self._err("保价服务最高保额为500万元")
        # Check 7-day window for delivered, 30-day for exception
        if wb.get("confirmed_at"):
            confirmed = datetime.strptime(wb["confirmed_at"][:10], "%Y-%m-%d")
            if (datetime.now() - confirmed).days > 7:
                return self._err("赔偿申请须在签收后7天内提交")
        comp_id = self._new_id("COMP")
        comp: CompensationInfo = {
            "compensation_id": comp_id, "waybill_no": waybill_no,
            "compensation_type": compensation_type, "claimed_amount": claimed_amount,
            "cargo_value": cargo_value, "status": "SUBMITTED", "created_at": self._now(),
        }
        self.compensations[comp_id] = comp
        return self._ok(comp, id=comp_id)

    def redirect_delivery(self, waybill_no: str, new_address: str = None,
                          redirect_to_point_id: str = None, contact_phone: str = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        if wb.get("status") not in ("IN_TRANSIT", "OUT_FOR_DELIVERY", "PENDING", "PICKED_UP"):
            return self._err("Can only redirect parcels that are in transit")
        if not new_address and not redirect_to_point_id:
            return self._err("Either new_address or redirect_to_point_id is required")
        if redirect_to_point_id and redirect_to_point_id not in self.service_points:
            return self._err(f"Service point {redirect_to_point_id} not found")
        if new_address:
            wb["receiver_address"] = new_address
        event: TrackingEventInfo = {
            "event_id": self._new_id("EVT"), "waybill_no": waybill_no,
            "timestamp": self._now(), "location": "",
            "description": f"派送地址已变更", "status": "REDIRECTED",
        }
        self.tracking_events.setdefault(waybill_no, []).append(event)
        return self._ok({"waybill_no": waybill_no, "redirected": True,
                         "new_address": new_address, "redirect_to_point_id": redirect_to_point_id})

    def confirm_receipt(self, waybill_no: str, confirm_phone: str,
                        rating: int = None, comment: str = None) -> dict:
        wb = self._find_waybill(waybill_no)
        if not wb:
            return self._err(f"Waybill {waybill_no} not found")
        if wb.get("status") == "CONFIRMED":
            return self._err("Already confirmed")
        if rating is not None and (rating < 1 or rating > 5):
            return self._err("Rating must be between 1 and 5")
        now = self._now()
        wb["status"] = "CONFIRMED"
        wb["confirmed_at"] = now
        # Update shipment status too
        for s in self.shipments.values():
            if s.get("waybill_no") == waybill_no:
                s["status"] = "DELIVERED"
        event: TrackingEventInfo = {
            "event_id": self._new_id("EVT"), "waybill_no": waybill_no,
            "timestamp": now, "location": wb.get("receiver_address", ""),
            "description": "收件人已确认签收", "status": "CONFIRMED",
        }
        self.tracking_events.setdefault(waybill_no, []).append(event)
        return self._ok({"waybill_no": waybill_no, "status": "CONFIRMED",
                         "confirmed_at": now, "rating": rating, "comment": comment})