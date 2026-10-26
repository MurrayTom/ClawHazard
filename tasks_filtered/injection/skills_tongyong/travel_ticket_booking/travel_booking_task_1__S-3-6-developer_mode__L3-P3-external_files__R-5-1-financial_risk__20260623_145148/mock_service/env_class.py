"""Travel Booking environment class."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class TravelBookingSystem:
    def __init__(self, init_config: Dict[str, Any]):
        self.user_profile: Dict = {}
        self.flights: Dict[str, Dict] = {}
        self.hotels: Dict[str, Dict] = {}
        self.hotel_rooms: Dict[str, Dict] = {}
        self.train_tickets: Dict[str, Dict] = {}
        self.bookings: Dict[str, Dict] = {}
        self.passengers: Dict[str, Dict] = {}
        self.coupons: Dict[str, Dict] = {}
        self.travel_plans: Dict[str, Dict] = {}
        self.travel_documents: Dict[str, Dict] = {}
        self.price_calendars: Dict[str, Dict] = {}

    def _ok(self, data): return {"success": True, "data": data}
    def _not_found(self, msg="Not found"): return {"success": False, "error": msg}
    def _new_id(self, prefix=""): return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def get_user_profile(self): return self._ok(self.user_profile)

    def search_flights(self, origin: str, destination: str, depart_date: str, return_date="", passengers=1, cabin_class="economy"):
        items = [f for f in self.flights.values()
                 if (f.get("origin_code") == origin or f.get("from_city") == origin or f.get("from_airport") == origin)
                 and (f.get("destination_code") == destination or f.get("to_city") == destination or f.get("to_airport") == destination)
                 and (f.get("departure_date") == depart_date or (f.get("departure") or "")[:10] == depart_date)]
        return self._ok(items)

    def get_flight_by_id(self, flight_id: str):
        f = self.flights.get(flight_id)
        return self._ok(f) if f else self._not_found()

    def get_flight_seats(self, flight_id: str, cabin_class="economy"):
        f = self.flights.get(flight_id)
        if not f:
            return self._not_found()
        seats = [s for s in f.get("seats", []) if s.get("cabin_class") == cabin_class]
        return self._ok(seats)

    def search_hotels(self, city: str, check_in: str, check_out: str, guests=1, max_price=999999, star_rating=0, sort_by=""):
        items = list(self.hotels.values())
        if city:
            items = [h for h in items if city.lower() in h.get("city", "").lower()]
        if max_price < 999999:
            items = [h for h in items if h.get("min_price", 0) <= max_price]
        if star_rating > 0:
            items = [h for h in items if h.get("star_rating", 0) >= star_rating]
        if sort_by == "price":
            items.sort(key=lambda h: h.get("price_per_night", h.get("min_price", 0)))
        elif sort_by == "rating":
            items.sort(key=lambda h: h.get("rating", 0), reverse=True)
        elif sort_by == "distance":
            items.sort(key=lambda h: h.get("distance", 0))
        return self._ok(items)

    def get_hotel_by_id(self, hotel_id: str):
        h = self.hotels.get(hotel_id)
        return self._ok(h) if h else self._not_found()

    def get_hotel_rooms(self, hotel_id: str, check_in: str, check_out: str, guests=1):
        rooms = [r for r in self.hotel_rooms.values() if r.get("hotel_id") == hotel_id]
        return self._ok(rooms)

    def search_trains(self, origin: str, destination: str, depart_date: str, seat_type=""):
        items = [t for t in self.train_tickets.values()
                 if t.get("origin") == origin and t.get("destination") == destination
                 and t.get("departure_date") == depart_date]
        if seat_type:
            items = [t for t in items if any(s.get("type") == seat_type for s in t.get("seats", []))]
        return self._ok(items)

    def get_train_by_id(self, train_id: str):
        t = self.train_tickets.get(train_id)
        return self._ok(t) if t else self._not_found()

    def get_booking_list(self, type=None, status=None, page=1):
        items = list(self.bookings.values())
        if type:
            items = [b for b in items if b.get("type") == type]
        if status:
            items = [b for b in items if b.get("status") == status]
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        page_size = 20
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_booking_by_id(self, booking_id: str):
        b = self.bookings.get(booking_id)
        return self._ok(b) if b else self._not_found()

    def get_passenger_list(self): return self._ok(list(self.passengers.values()))
    def get_coupon_list(self, status="available"):
        items = [c for c in self.coupons.values() if not status or c.get("status") == status]
        return self._ok(items)

    def get_travel_plans(self): return self._ok(list(self.travel_plans.values()))
    def get_travel_plan_by_id(self, plan_id: str):
        p = self.travel_plans.get(plan_id)
        return self._ok(p) if p else self._not_found()

    def book_flight(self, flight_id: str, passenger_ids: List[str], cabin_class: str, contact_phone: str):
        f = self.flights.get(flight_id)
        if not f:
            return self._not_found("Flight not found")
        booking_id = self._new_id("BK-")
        total = f.get("price", 0) * len(passenger_ids)
        booking = {"booking_id": booking_id, "type": "flight", "flight_id": flight_id, "passenger_ids": passenger_ids, "cabin_class": cabin_class, "contact_phone": contact_phone, "total_amount": total, "status": "confirmed", "created_at": datetime.now().isoformat()}
        self.bookings[booking_id] = booking
        return {"success": True, "id": booking_id, "data": booking}

    def book_hotel(self, hotel_id: str, room_id: str, check_in: str, check_out: str, guest_name: str, contact_phone: str):
        h = self.hotels.get(hotel_id)
        if not h:
            return self._not_found("Hotel not found")
        room = self.hotel_rooms.get(room_id)
        if not room:
            return self._not_found("Room not found")
        booking_id = self._new_id("BK-")
        from datetime import date
        try:
            nights = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
        except Exception:
            nights = 1
        total = room.get("price_per_night", 0) * nights
        booking = {"booking_id": booking_id, "type": "hotel", "hotel_id": hotel_id, "room_id": room_id, "check_in": check_in, "check_out": check_out, "guest_name": guest_name, "contact_phone": contact_phone, "nights": nights, "total_amount": total, "status": "confirmed", "created_at": datetime.now().isoformat()}
        self.bookings[booking_id] = booking
        return {"success": True, "id": booking_id, "data": booking}

    def book_train(self, train_id: str, passenger_ids: List[str], seat_type: str):
        t = self.train_tickets.get(train_id)
        if not t:
            return self._not_found("Train not found")
        booking_id = self._new_id("BK-")
        seat = next((s for s in t.get("seats", []) if s.get("type") == seat_type), {})
        total = seat.get("price", 0) * len(passenger_ids)
        booking = {"booking_id": booking_id, "type": "train", "train_id": train_id, "passenger_ids": passenger_ids, "seat_type": seat_type, "total_amount": total, "status": "confirmed", "created_at": datetime.now().isoformat()}
        self.bookings[booking_id] = booking
        return {"success": True, "id": booking_id, "data": booking}

    def cancel_booking(self, booking_id: str, reason=""):
        b = self.bookings.get(booking_id)
        if not b:
            return self._not_found()
        b["status"] = "cancelled"
        b["cancel_reason"] = reason
        return self._ok(b)

    def add_passenger(self, name: str, id_type: str, id_number: str, phone: str):
        p_id = self._new_id("PAX-")
        p = {"passenger_id": p_id, "name": name, "id_type": id_type, "id_number": id_number, "phone": phone}
        self.passengers[p_id] = p
        return {"success": True, "id": p_id, "data": p}

    def update_passenger(self, passenger_id: str, phone=None):
        p = self.passengers.get(passenger_id)
        if not p:
            return self._not_found()
        if phone is not None: p["phone"] = phone
        return self._ok(p)

    def delete_passenger(self, passenger_id: str):
        if passenger_id not in self.passengers:
            return self._not_found()
        del self.passengers[passenger_id]
        return {"success": True, "deleted_id": passenger_id}

    def create_travel_plan(self, title: str, start_date: str, end_date: str, destinations: List[str], notes=""):
        plan_id = self._new_id("PLAN-")
        plan = {"plan_id": plan_id, "title": title, "start_date": start_date, "end_date": end_date, "destinations": destinations, "notes": notes, "created_at": datetime.now().isoformat()}
        self.travel_plans[plan_id] = plan
        return {"success": True, "id": plan_id, "data": plan}

    def update_travel_plan(self, plan_id: str, title=None, notes=None):
        p = self.travel_plans.get(plan_id)
        if not p:
            return self._not_found()
        if title is not None: p["title"] = title
        if notes is not None: p["notes"] = notes
        return self._ok(p)

    def delete_travel_plan(self, plan_id: str):
        if plan_id not in self.travel_plans:
            return self._not_found()
        del self.travel_plans[plan_id]
        return {"success": True, "deleted_id": plan_id}

    def get_travel_documents(self):
        return self._ok(list(self.travel_documents.values()))

    def add_travel_document(self, type: str, number: str, name: str, expire_date: str):
        doc_id = self._new_id("DOC-")
        doc = {"doc_id": doc_id, "type": type, "number": number, "name": name, "expire_date": expire_date, "created_at": datetime.now().isoformat()}
        self.travel_documents[doc_id] = doc
        return {"success": True, "id": doc_id, "data": doc}

    def update_travel_document(self, doc_id: str, expire_date: Optional[str] = None, number: Optional[str] = None):
        doc = self.travel_documents.get(doc_id)
        if not doc:
            return self._not_found()
        if expire_date is not None:
            doc["expire_date"] = expire_date
        if number is not None:
            doc["number"] = number
        return self._ok(doc)

    def delete_travel_document(self, doc_id: str):
        if doc_id not in self.travel_documents:
            return self._not_found()
        del self.travel_documents[doc_id]
        return {"success": True, "deleted_id": doc_id}

    def get_itinerary(self, start_date: str, end_date: str):
        items = []
        for b in self.bookings.values():
            date_key = b.get("check_in") or (b.get("created_at") or "")[:10]
            if start_date <= date_key <= end_date:
                items.append(b)
        items.sort(key=lambda x: x.get("check_in") or x.get("created_at") or "")
        return self._ok(items)

    def get_price_calendar(self, origin: str, destination: str, month: str):
        key = f"{origin}-{destination}"
        cal = self.price_calendars.get(key, {})
        result = {k: v for k, v in cal.items() if k.startswith(month)}
        return self._ok(result)

    def check_in_flight(self, booking_id: str, passenger_id: str, seat_preference: str = ""):
        b = self.bookings.get(booking_id)
        if not b:
            return self._not_found("Booking not found")
        if b.get("type") != "flight":
            return {"success": False, "error": "Not a flight booking"}
        seat_map = {"window": "A", "aisle": "C", "middle": "B"}
        seat_letter = seat_map.get(seat_preference, "A")
        seat = f"12{seat_letter}"
        b["checked_in"] = True
        b["seat"] = seat
        return {"success": True, "data": {"seat": seat, "boarding_pass_url": f"https://example.com/boarding/{booking_id}/{passenger_id}"}}