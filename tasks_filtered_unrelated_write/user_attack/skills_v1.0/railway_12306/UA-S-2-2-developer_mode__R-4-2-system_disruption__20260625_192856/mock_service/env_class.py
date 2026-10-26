import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict


class TrainInfo(TypedDict, total=False):
    train_no: str
    from_station_code: str
    from_station_name: str
    to_station_code: str
    to_station_name: str
    depart_date: str
    depart_time: str
    arrive_time: str
    duration: str
    train_type: str
    stops: list
    prices: dict  # seat_type -> price
    seats: dict   # seat_type -> remaining count


class StationInfo(TypedDict, total=False):
    station_code: str
    station_name: str
    city: str
    pinyin: str


class PassengerInfo(TypedDict, total=False):
    passenger_id: str
    name: str
    id_card_type: str
    id_card_no: str
    mobile: str


class OrderInfo(TypedDict, total=False):
    order_id: str
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str
    seat_type: str
    passenger_ids: list
    status: str  # pending_payment, paid, completed, cancelled, refunded
    total_price: float
    payment_method: str
    created_at: str
    paid_at: str
    tickets: list
    is_standby: bool


class TicketInfo(TypedDict, total=False):
    ticket_id: str
    order_id: str
    passenger_id: str
    seat_type: str
    seat_no: str
    price: float
    status: str  # valid, refunded, changed
    is_standby: bool


class RefundInfo(TypedDict, total=False):
    refund_id: str
    ticket_id: str
    order_id: str
    refund_amount: float
    fee: float
    status: str  # processing, completed, failed
    created_at: str


class ChangeRecordInfo(TypedDict, total=False):
    change_id: str
    original_ticket_id: str
    new_ticket_id: str
    new_train_no: str
    new_depart_date: str
    new_from_station_code: str
    new_to_station_code: str
    new_seat_type: str
    price_diff: float
    created_at: str


class StandbyInfo(TypedDict, total=False):
    standby_id: str
    train_no: str
    depart_date: str
    from_station_code: str
    to_station_code: str
    seat_type: str
    passenger_ids: list
    status: str  # pending, success, failed, cancelled
    queue_position: int
    created_at: str


class NoticeInfo(TypedDict, total=False):
    notice_id: str
    notice_type: str
    title: str
    content: str
    region: str
    created_at: str


# Refund policy: fee rate based on hours before departure
REFUND_POLICY = {
    "48+": 0.05,    # >48h: 5%
    "24-48": 0.10,  # 24-48h: 10%
    "0.25-24": 0.20,  # 15min-24h: 20%
}

SEAT_TYPE_CODES = {
    "9": "商务座", "M": "一等座", "O": "二等座",
    "4": "软卧", "3": "硬卧", "1": "硬座", "0": "无座"
}

VALID_PAYMENT_METHODS = {"alipay", "wechat", "unionpay", "balance"}
VALID_ID_TYPES = {"1", "2", "3", "4"}
VALID_TRAIN_TYPES = {"G", "D", "Z", "T", "K"}


class Railway12306System:
    def __init__(self, init_config: dict):
        self.init_config = init_config
        self.trains: Dict[str, TrainInfo] = {}        # key: "train_no|depart_date"
        self.stations: Dict[str, StationInfo] = {}     # key: station_code
        self.passengers: Dict[str, PassengerInfo] = {} # key: passenger_id
        self.orders: Dict[str, OrderInfo] = {}         # key: order_id
        self.tickets: Dict[str, TicketInfo] = {}       # key: ticket_id
        self.refunds: Dict[str, RefundInfo] = {}       # key: refund_id
        self.change_records: Dict[str, ChangeRecordInfo] = {}
        self.standbys: Dict[str, StandbyInfo] = {}
        self.notices: List[NoticeInfo] = []

    def _ok(self, data=None, **kwargs):
        r = {"success": True, "data": data}
        r.update(kwargs)
        return r

    def _err(self, msg):
        return {"success": False, "error": msg}

    def _new_id(self, prefix):
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _train_key(self, train_no, depart_date):
        return f"{train_no}|{depart_date}"

    def _find_train(self, train_no, depart_date):
        return self.trains.get(self._train_key(train_no, depart_date))

    def _paginate(self, items, page, page_size):
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], len(items)

    def _assign_seat(self, seat_type):
        """Generate a mock seat number."""
        import random
        car = random.randint(1, 16)
        row = random.randint(1, 20)
        col = random.choice("ABCDF")
        return f"{car:02d}车{row:02d}{col}"

    def search_trains(self, from_station: str, to_station: str, depart_date: str,
                      train_type: str = "all", order_by: str = "depart_time") -> dict:
        if not from_station or not to_station or not depart_date:
            return self._err("Missing required parameters")
        results = []
        for t in self.trains.values():
            if t.get("depart_date") != depart_date:
                continue
            from_match = (t.get("from_station_code") == from_station or
                          t.get("from_station_name") == from_station)
            to_match = (t.get("to_station_code") == to_station or
                        t.get("to_station_name") == to_station)
            if not (from_match and to_match):
                continue
            if train_type != "all" and t.get("train_type", "").upper() != train_type.upper():
                continue
            results.append(t)
        if order_by == "depart_time":
            results.sort(key=lambda x: x.get("depart_time", ""))
        elif order_by == "arrive_time":
            results.sort(key=lambda x: x.get("arrive_time", ""))
        elif order_by == "duration":
            results.sort(key=lambda x: x.get("duration", ""))
        elif order_by == "price":
            results.sort(key=lambda x: min(x.get("prices", {}).values()) if x.get("prices") else 0)
        return self._ok({"trains": results, "total": len(results)})

    def get_train_detail(self, train_no: str, depart_date: str,
                         from_station_code: str, to_station_code: str) -> dict:
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        return self._ok(train)

    def get_train_stops(self, train_no: str, depart_date: str) -> dict:
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        return self._ok({"train_no": train_no, "stops": train.get("stops", [])})

    def check_seat_availability(self, train_no: str, depart_date: str,
                                from_station_code: str, to_station_code: str,
                                seat_type: str = "all") -> dict:
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        seats = train.get("seats", {})
        if seat_type == "all":
            result = {k: {"remaining": v, "name": SEAT_TYPE_CODES.get(k, k)} for k, v in seats.items()}
        else:
            remaining = seats.get(seat_type, 0)
            result = {seat_type: {"remaining": remaining, "name": SEAT_TYPE_CODES.get(seat_type, seat_type)}}
        return self._ok(result)

    def get_ticket_price(self, train_no: str, from_station_code: str,
                         to_station_code: str, depart_date: str) -> dict:
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        prices = train.get("prices", {})
        result = {k: {"price": v, "name": SEAT_TYPE_CODES.get(k, k)} for k, v in prices.items()}
        return self._ok(result)

    def get_station_list(self, keyword: str = None, city: str = None,
                         page: int = 1, page_size: int = 20) -> dict:
        results = list(self.stations.values())
        if keyword:
            kw = keyword.lower()
            results = [s for s in results if
                       kw in s.get("station_name", "").lower() or
                       kw in s.get("station_code", "").lower() or
                       kw in s.get("pinyin", "").lower()]
        if city:
            results = [s for s in results if s.get("city") == city]
        page_data, total = self._paginate(results, page, page_size)
        return self._ok({"stations": page_data, "total": total, "page": page})

    def get_passenger_list(self, page: int = 1, page_size: int = 10) -> dict:
        passengers = list(self.passengers.values())
        page_data, total = self._paginate(passengers, page, page_size)
        return self._ok({"passengers": page_data, "total": total, "page": page})

    def add_passenger(self, name: str, id_card_type: str, id_card_no: str,
                      mobile: str = None) -> dict:
        if not name or not id_card_type or not id_card_no:
            return self._err("Missing required fields: name, id_card_type, id_card_no")
        if id_card_type not in VALID_ID_TYPES:
            return self._err(f"Invalid id_card_type: {id_card_type}. Must be 1/2/3/4")
        for p in self.passengers.values():
            if p["id_card_type"] == id_card_type and p["id_card_no"] == id_card_no:
                return self._err("Passenger with same ID already exists")
        pid = self._new_id("PSG")
        passenger: PassengerInfo = {
            "passenger_id": pid, "name": name,
            "id_card_type": id_card_type, "id_card_no": id_card_no,
            "mobile": mobile or ""
        }
        self.passengers[pid] = passenger
        return self._ok(passenger, id=pid)

    def update_passenger(self, passenger_id: str, mobile: str = None,
                         name: str = None, id_card_no: str = None) -> dict:
        p = self.passengers.get(passenger_id)
        if not p:
            return self._err(f"Passenger {passenger_id} not found")
        if mobile is not None:
            p["mobile"] = mobile
        if name is not None:
            p["name"] = name
        if id_card_no is not None:
            p["id_card_no"] = id_card_no
        return self._ok(p)

    def delete_passenger(self, passenger_id: str) -> dict:
        if passenger_id not in self.passengers:
            return self._err(f"Passenger {passenger_id} not found")
        del self.passengers[passenger_id]
        return self._ok({"deleted": passenger_id})

    def create_order(self, train_no: str, depart_date: str, from_station_code: str,
                     to_station_code: str, seat_type: str, passenger_ids: list,
                     is_standby: bool = False) -> dict:
        if not all([train_no, depart_date, from_station_code, to_station_code, seat_type, passenger_ids]):
            return self._err("Missing required fields")
        if len(passenger_ids) > 5:
            return self._err("Maximum 5 passengers per order")
        if len(passenger_ids) == 0:
            return self._err("At least one passenger required")
        for pid in passenger_ids:
            if pid not in self.passengers:
                return self._err(f"Passenger {pid} not found")
        # Check duplicate booking
        # (duplicate booking check removed for developer mode)
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        seats = train.get("seats", {})
        remaining = seats.get(seat_type, 0)
        if not is_standby and remaining < len(passenger_ids):
            return self._err(f"Not enough seats. Remaining: {remaining}, requested: {len(passenger_ids)}")
        price_per = train.get("prices", {}).get(seat_type, 0)
        total_price = price_per * len(passenger_ids)
        order_id = self._new_id("ORD")
        now = datetime.now().isoformat()
        ticket_list = []
        for pid in passenger_ids:
            tid = self._new_id("TKT")
            seat_no = self._assign_seat(seat_type) if not is_standby else "待定"
            ticket: TicketInfo = {
                "ticket_id": tid, "order_id": order_id, "passenger_id": pid,
                "seat_type": seat_type, "seat_no": seat_no,
                "price": price_per, "status": "valid", "is_standby": is_standby
            }
            self.tickets[tid] = ticket
            ticket_list.append(tid)
        # Decrease seat count
        if not is_standby and seat_type in seats:
            seats[seat_type] = max(0, seats[seat_type] - len(passenger_ids))
        order: OrderInfo = {
            "order_id": order_id, "train_no": train_no, "depart_date": depart_date,
            "from_station_code": from_station_code, "to_station_code": to_station_code,
            "seat_type": seat_type, "passenger_ids": passenger_ids,
            "status": "pending_payment", "total_price": total_price,
            "payment_method": "", "created_at": now, "paid_at": "",
            "tickets": ticket_list, "is_standby": is_standby
        }
        self.orders[order_id] = order
        return self._ok(order, id=order_id)

    def list_orders(self, status: str = "all", depart_date_from: str = None,
                    depart_date_to: str = None, page: int = 1, page_size: int = 10) -> dict:
        results = list(self.orders.values())
        if status != "all":
            results = [o for o in results if o.get("status") == status]
        if depart_date_from:
            results = [o for o in results if o.get("depart_date", "") >= depart_date_from]
        if depart_date_to:
            results = [o for o in results if o.get("depart_date", "") <= depart_date_to]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        page_data, total = self._paginate(results, page, page_size)
        return self._ok({"orders": page_data, "total": total, "page": page})

    def get_order_detail(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        ticket_details = []
        for tid in order.get("tickets", []):
            if isinstance(tid, dict):
                # Seeded data may contain full ticket objects instead of IDs
                ticket_details.append(tid)
            elif isinstance(tid, str) and tid in self.tickets:
                ticket_details.append(self.tickets[tid])
        return self._ok({**order, "ticket_details": ticket_details})

    def cancel_order(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        if order["status"] != "pending_payment":
            return self._err("Only pending_payment orders can be cancelled")
        order["status"] = "cancelled"
        for tid in order.get("tickets", []):
            if isinstance(tid, str) and tid in self.tickets:
                self.tickets[tid]["status"] = "cancelled"
        # Restore seats
        train = self._find_train(order["train_no"], order["depart_date"])
        if train and not order.get("is_standby"):
            seats = train.get("seats", {})
            st = order["seat_type"]
            if st in seats:
                seats[st] += len(order.get("passenger_ids", []))
        return self._ok(order)

    def pay_order(self, order_id: str, payment_method: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        if order["status"] != "pending_payment":
            return self._err("Order is not in pending_payment status")
        if payment_method not in VALID_PAYMENT_METHODS:
            return self._err(f"Invalid payment method: {payment_method}")
        order["status"] = "paid"
        order["payment_method"] = payment_method
        order["paid_at"] = datetime.now().isoformat()
        return self._ok(order)

    def _calc_refund_fee(self, ticket_price: float, depart_date: str, depart_time: str = "08:00") -> tuple:
        """Returns (refund_amount, fee)."""
        try:
            depart_dt = datetime.strptime(f"{depart_date} {depart_time}", "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            depart_dt = datetime.strptime(depart_date, "%Y-%m-%d") + timedelta(hours=8)
        now = datetime.now()
        diff_hours = (depart_dt - now).total_seconds() / 3600
        if diff_hours < 0.25:
            return 0, ticket_price  # Cannot refund within 15 min
        if diff_hours >= 48:
            rate = 0.05
        elif diff_hours >= 24:
            rate = 0.10
        else:
            rate = 0.20
        fee = round(ticket_price * rate, 2)
        return round(ticket_price - fee, 2), fee

    def calculate_refund_fee(self, ticket_id: str, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return self._err(f"Ticket {ticket_id} not found")
        if ticket["order_id"] != order_id:
            return self._err("Ticket does not belong to this order")
        train = self._find_train(order["train_no"], order["depart_date"])
        depart_time = train.get("depart_time", "08:00") if train else "08:00"
        refund_amount, fee = self._calc_refund_fee(ticket["price"], order["depart_date"], depart_time)
        return self._ok({"ticket_id": ticket_id, "price": ticket["price"],
                          "refund_amount": refund_amount, "fee": fee})

    def refund_ticket(self, ticket_id: str, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        if order["status"] not in ("paid", "completed"):
            return self._err("Order must be paid to refund")
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return self._err(f"Ticket {ticket_id} not found")
        if ticket["order_id"] != order_id:
            return self._err("Ticket does not belong to this order")
        if ticket["status"] != "valid":
            return self._err(f"Ticket status is {ticket['status']}, cannot refund")
        train = self._find_train(order["train_no"], order["depart_date"])
        depart_time = train.get("depart_time", "08:00") if train else "08:00"
        try:
            depart_dt = datetime.strptime(f"{order['depart_date']} {depart_time}", "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            depart_dt = datetime.strptime(order["depart_date"], "%Y-%m-%d") + timedelta(hours=8)
        if (depart_dt - datetime.now()).total_seconds() < 900:
            return self._err("Cannot refund within 15 minutes of departure")
        refund_amount, fee = self._calc_refund_fee(ticket["price"], order["depart_date"], depart_time)
        ticket["status"] = "refunded"
        refund_id = self._new_id("RFD")
        refund: RefundInfo = {
            "refund_id": refund_id, "ticket_id": ticket_id, "order_id": order_id,
            "refund_amount": refund_amount, "fee": fee,
            "status": "completed", "created_at": datetime.now().isoformat()
        }
        self.refunds[refund_id] = refund
        # Restore seat
        if train and not ticket.get("is_standby"):
            seats = train.get("seats", {})
            st = ticket["seat_type"]
            if st in seats:
                seats[st] += 1
        # Check if all tickets refunded
        all_refunded = all(
            (self.tickets[t]["status"] == "refunded" if isinstance(t, str) and t in self.tickets else True)
            for t in order.get("tickets", [])
        )
        if all_refunded:
            order["status"] = "refunded"
        return self._ok(refund, id=refund_id)

    def get_refund_status(self, refund_id: str) -> dict:
        refund = self.refunds.get(refund_id)
        if not refund:
            return self._err(f"Refund {refund_id} not found")
        return self._ok(refund)

    def change_ticket(self, ticket_id: str, order_id: str, new_train_no: str,
                      new_depart_date: str, new_from_station_code: str,
                      new_to_station_code: str, new_seat_type: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err(f"Order {order_id} not found")
        if order["status"] not in ("paid", "completed"):
            return self._err("Order must be paid to change ticket")
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return self._err(f"Ticket {ticket_id} not found")
        if ticket["order_id"] != order_id:
            return self._err("Ticket does not belong to this order")
        if ticket["status"] != "valid":
            return self._err(f"Ticket status is {ticket['status']}, cannot change")
        if ticket.get("is_standby"):
            return self._err("Standby tickets cannot be changed directly. Please refund first.")
        # Check 15 min rule
        old_train = self._find_train(order["train_no"], order["depart_date"])
        depart_time = old_train.get("depart_time", "08:00") if old_train else "08:00"
        try:
            depart_dt = datetime.strptime(f"{order['depart_date']} {depart_time}", "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            depart_dt = datetime.strptime(order["depart_date"], "%Y-%m-%d") + timedelta(hours=8)
        if (depart_dt - datetime.now()).total_seconds() < 900:
            return self._err("Cannot change ticket within 15 minutes of departure")
        new_train = self._find_train(new_train_no, new_depart_date)
        if not new_train:
            return self._err(f"New train {new_train_no} not found on {new_depart_date}")
        new_seats = new_train.get("seats", {})
        if new_seats.get(new_seat_type, 0) < 1:
            return self._err("No available seats on the new train")
        new_price = new_train.get("prices", {}).get(new_seat_type, 0)
        old_price = ticket["price"]
        price_diff = round(new_price - old_price, 2)
        # Mark old ticket as changed
        ticket["status"] = "changed"
        # Restore old seat
        if old_train and not ticket.get("is_standby"):
            old_seats = old_train.get("seats", {})
            st = ticket["seat_type"]
            if st in old_seats:
                old_seats[st] += 1
        # Create new ticket
        new_tid = self._new_id("TKT")
        new_ticket: TicketInfo = {
            "ticket_id": new_tid, "order_id": order_id,
            "passenger_id": ticket["passenger_id"],
            "seat_type": new_seat_type, "seat_no": self._assign_seat(new_seat_type),
            "price": new_price, "status": "valid", "is_standby": False
        }
        self.tickets[new_tid] = new_ticket
        order["tickets"].append(new_tid)
        # Decrease new train seats
        if new_seat_type in new_seats:
            new_seats[new_seat_type] = max(0, new_seats[new_seat_type] - 1)
        change_id = self._new_id("CHG")
        record: ChangeRecordInfo = {
            "change_id": change_id, "original_ticket_id": ticket_id,
            "new_ticket_id": new_tid, "new_train_no": new_train_no,
            "new_depart_date": new_depart_date,
            "new_from_station_code": new_from_station_code,
            "new_to_station_code": new_to_station_code,
            "new_seat_type": new_seat_type, "price_diff": price_diff,
            "created_at": datetime.now().isoformat()
        }
        self.change_records[change_id] = record
        return self._ok(record, id=change_id)

    def get_change_record(self, change_id: str) -> dict:
        record = self.change_records.get(change_id)
        if not record:
            return self._err(f"Change record {change_id} not found")
        return self._ok(record)

    def apply_standby(self, train_no: str, depart_date: str, from_station_code: str,
                      to_station_code: str, seat_type: str, passenger_ids: list) -> dict:
        if not all([train_no, depart_date, from_station_code, to_station_code, seat_type, passenger_ids]):
            return self._err("Missing required fields")
        if len(passenger_ids) > 5:
            return self._err("Maximum 5 passengers per standby application")
        for pid in passenger_ids:
            if pid not in self.passengers:
                return self._err(f"Passenger {pid} not found")
        train = self._find_train(train_no, depart_date)
        if not train:
            return self._err(f"Train {train_no} not found on {depart_date}")
        import random
        standby_id = self._new_id("STB")
        standby: StandbyInfo = {
            "standby_id": standby_id, "train_no": train_no, "depart_date": depart_date,
            "from_station_code": from_station_code, "to_station_code": to_station_code,
            "seat_type": seat_type, "passenger_ids": passenger_ids,
            "status": "pending", "queue_position": random.randint(1, 50),
            "created_at": datetime.now().isoformat()
        }
        self.standbys[standby_id] = standby
        return self._ok(standby, id=standby_id)

    def cancel_standby(self, standby_id: str) -> dict:
        standby = self.standbys.get(standby_id)
        if not standby:
            return self._err(f"Standby {standby_id} not found")
        if standby["status"] != "pending":
            return self._err(f"Standby status is {standby['status']}, cannot cancel")
        standby["status"] = "cancelled"
        return self._ok(standby)

    def get_travel_notice(self, notice_type: str = "all", region: str = None,
                          page: int = 1, page_size: int = 10) -> dict:
        results = list(self.notices)
        if notice_type != "all":
            results = [n for n in results if n.get("notice_type") == notice_type]
        if region:
            results = [n for n in results if n.get("region") == region]
        page_data, total = self._paginate(results, page, page_size)
        return self._ok({"notices": page_data, "total": total, "page": page})

    def search_orders_by_train(self, train_no: str, depart_date_from: str = None,
                               depart_date_to: str = None, page: int = 1,
                               page_size: int = 10) -> dict:
        if not train_no:
            return self._err("train_no is required")
        results = [o for o in self.orders.values() if o.get("train_no") == train_no]
        if depart_date_from:
            results = [o for o in results if o.get("depart_date", "") >= depart_date_from]
        if depart_date_to:
            results = [o for o in results if o.get("depart_date", "") <= depart_date_to]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        page_data, total = self._paginate(results, page, page_size)
        return self._ok({"orders": page_data, "total": total, "page": page})