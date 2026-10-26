"""Travel Booking mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import TravelBookingSystem

app = FastAPI(title="Travel Booking Mock Server")

_seed_path = Path(__file__).parent / "travel_booking_task_1_injected.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_cfg = _seed["init_config"]
_env = TravelBookingSystem(init_config=_cfg)
_env.user_profile       = _cfg.get("user_profile", {})
_env.flights            = _cfg.get("flights", {})
_env.hotels             = _cfg.get("hotels", {})
_env.hotel_rooms        = _cfg.get("hotel_rooms", {})
_env.train_tickets      = _cfg.get("train_tickets", {})
_env.bookings           = _cfg.get("bookings", {})
_env.passengers         = _cfg.get("passengers", {})
_env.coupons            = _cfg.get("coupons", {})
_env.travel_plans       = _cfg.get("travel_plans", {})
_env.travel_documents   = _cfg.get("travel_documents", {})
_env.price_calendars    = _cfg.get("price_calendars", {})


@app.get("/get_user_profile")
def get_user_profile(): return _env.get_user_profile()

@app.get("/search_flights")
def search_flights(origin: str, destination: str, depart_date: str, return_date: str = "", passengers: int = 1, cabin_class: str = "economy"):
    return _env.search_flights(origin=origin, destination=destination, depart_date=depart_date, return_date=return_date, passengers=passengers, cabin_class=cabin_class)

@app.get("/get_flight_by_id")
def get_flight_by_id(flight_id: str): return _env.get_flight_by_id(flight_id=flight_id)

@app.get("/get_flight_seats")
def get_flight_seats(flight_id: str, cabin_class: str = "economy"): return _env.get_flight_seats(flight_id=flight_id, cabin_class=cabin_class)

@app.get("/search_hotels")
def search_hotels(city: str, check_in: str, check_out: str, guests: int = 1, max_price: float = 999999, star_rating: int = 0, sort_by: str = ""):
    return _env.search_hotels(city=city, check_in=check_in, check_out=check_out, guests=guests, max_price=max_price, star_rating=star_rating, sort_by=sort_by)

@app.get("/get_hotel_by_id")
def get_hotel_by_id(hotel_id: str): return _env.get_hotel_by_id(hotel_id=hotel_id)

@app.get("/get_hotel_rooms")
def get_hotel_rooms(hotel_id: str, check_in: str, check_out: str, guests: int = 1): return _env.get_hotel_rooms(hotel_id=hotel_id, check_in=check_in, check_out=check_out, guests=guests)

@app.get("/search_trains")
def search_trains(origin: str, destination: str, depart_date: str, seat_type: str = ""): return _env.search_trains(origin=origin, destination=destination, depart_date=depart_date, seat_type=seat_type)

@app.get("/get_train_by_id")
def get_train_by_id(train_id: str): return _env.get_train_by_id(train_id=train_id)

@app.get("/get_booking_list")
def get_booking_list(type: str = "", status: str = "", page: int = 1): return _env.get_booking_list(type=type or None, status=status or None, page=page)

@app.get("/get_booking_by_id")
def get_booking_by_id(booking_id: str): return _env.get_booking_by_id(booking_id=booking_id)

@app.get("/get_travel_documents")
def get_travel_documents(): return _env.get_travel_documents()

@app.get("/get_itinerary")
def get_itinerary(start_date: str, end_date: str): return _env.get_itinerary(start_date=start_date, end_date=end_date)

@app.get("/get_price_calendar")
def get_price_calendar(origin: str, destination: str, month: str): return _env.get_price_calendar(origin=origin, destination=destination, month=month)

@app.get("/get_passenger_list")
def get_passenger_list(): return _env.get_passenger_list()

@app.get("/get_coupon_list")
def get_coupon_list(status: str = "available"): return _env.get_coupon_list(status=status)

@app.get("/get_travel_plans")
def get_travel_plans(): return _env.get_travel_plans()

@app.get("/get_travel_plan_by_id")
def get_travel_plan_by_id(plan_id: str): return _env.get_travel_plan_by_id(plan_id=plan_id)


class BookFlightRequest(BaseModel):
    flight_id: str
    passenger_ids: List[str]
    cabin_class: str
    contact_phone: str

@app.post("/book_flight")
def book_flight(req: BookFlightRequest): return _env.book_flight(flight_id=req.flight_id, passenger_ids=req.passenger_ids, cabin_class=req.cabin_class, contact_phone=req.contact_phone)


class BookHotelRequest(BaseModel):
    hotel_id: str
    room_id: str
    check_in: str
    check_out: str
    guest_name: str
    contact_phone: str

@app.post("/book_hotel")
def book_hotel(req: BookHotelRequest): return _env.book_hotel(hotel_id=req.hotel_id, room_id=req.room_id, check_in=req.check_in, check_out=req.check_out, guest_name=req.guest_name, contact_phone=req.contact_phone)


class BookTrainRequest(BaseModel):
    train_id: str
    passenger_ids: List[str]
    seat_type: str

@app.post("/book_train")
def book_train(req: BookTrainRequest): return _env.book_train(train_id=req.train_id, passenger_ids=req.passenger_ids, seat_type=req.seat_type)


class CancelBookingRequest(BaseModel):
    booking_id: str
    reason: Optional[str] = ""

@app.post("/cancel_booking")
def cancel_booking(req: CancelBookingRequest): return _env.cancel_booking(booking_id=req.booking_id, reason=req.reason)


class AddPassengerRequest(BaseModel):
    name: str
    id_type: str
    id_number: str
    phone: str

@app.post("/add_passenger")
def add_passenger(req: AddPassengerRequest): return _env.add_passenger(name=req.name, id_type=req.id_type, id_number=req.id_number, phone=req.phone)


class UpdatePassengerRequest(BaseModel):
    passenger_id: str
    phone: Optional[str] = None

@app.post("/update_passenger")
def update_passenger(req: UpdatePassengerRequest): return _env.update_passenger(passenger_id=req.passenger_id, phone=req.phone)


class PassengerIdRequest(BaseModel):
    passenger_id: str

@app.post("/delete_passenger")
def delete_passenger(req: PassengerIdRequest): return _env.delete_passenger(passenger_id=req.passenger_id)


class CheckInFlightRequest(BaseModel):
    booking_id: str
    passenger_id: str
    seat_preference: Optional[str] = ""

@app.post("/check_in_flight")
def check_in_flight(req: CheckInFlightRequest): return _env.check_in_flight(booking_id=req.booking_id, passenger_id=req.passenger_id, seat_preference=req.seat_preference)


class AddTravelDocumentRequest(BaseModel):
    type: str
    number: str
    name: str
    expire_date: str

@app.post("/add_travel_document")
def add_travel_document(req: AddTravelDocumentRequest): return _env.add_travel_document(type=req.type, number=req.number, name=req.name, expire_date=req.expire_date)


class UpdateTravelDocumentRequest(BaseModel):
    doc_id: str
    expire_date: Optional[str] = None
    number: Optional[str] = None

@app.post("/update_travel_document")
def update_travel_document(req: UpdateTravelDocumentRequest): return _env.update_travel_document(doc_id=req.doc_id, expire_date=req.expire_date, number=req.number)


class DocIdRequest(BaseModel):
    doc_id: str

@app.post("/delete_travel_document")
def delete_travel_document(req: DocIdRequest): return _env.delete_travel_document(doc_id=req.doc_id)


class CreateTravelPlanRequest(BaseModel):
    title: str
    start_date: str
    end_date: str
    destinations: List[str]
    notes: Optional[str] = ""

@app.post("/create_travel_plan")
def create_travel_plan(req: CreateTravelPlanRequest): return _env.create_travel_plan(title=req.title, start_date=req.start_date, end_date=req.end_date, destinations=req.destinations, notes=req.notes)


class UpdateTravelPlanRequest(BaseModel):
    plan_id: str
    title: Optional[str] = None
    notes: Optional[str] = None

@app.post("/update_travel_plan")
def update_travel_plan(req: UpdateTravelPlanRequest): return _env.update_travel_plan(plan_id=req.plan_id, title=req.title, notes=req.notes)


class PlanIdRequest(BaseModel):
    plan_id: str

@app.post("/delete_travel_plan")
def delete_travel_plan(req: PlanIdRequest): return _env.delete_travel_plan(plan_id=req.plan_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39211)