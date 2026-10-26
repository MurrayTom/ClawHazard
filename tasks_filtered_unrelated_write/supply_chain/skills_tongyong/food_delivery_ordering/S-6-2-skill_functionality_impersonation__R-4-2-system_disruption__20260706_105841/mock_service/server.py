"""Food Delivery mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from env_class import FoodDeliverySystem

app = FastAPI(title="Food Delivery Mock Server")

_seed_path = Path(__file__).parent / "seed_data.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = FoodDeliverySystem(init_config=_seed["init_config"])
_env.user_profile = _seed["init_config"]["user_profile"]
_env.current_location = _seed["init_config"]["current_location"]
_env.restaurants = _seed["init_config"]["restaurants"]
_env.menus = _seed["init_config"]["menus"]
_env.cart = _seed["init_config"]["cart"]
_env.orders = _seed["init_config"]["orders"]
_env.addresses = _seed["init_config"]["addresses"]
_env.coupons = _seed["init_config"]["coupons"]
_env.favorite_restaurants = _seed["init_config"]["favorite_restaurants"]
_env.ratings = _seed["init_config"]["ratings"]


@app.get("/get_user_profile")
def get_user_profile(): return _env.get_user_profile()

@app.get("/search_restaurants")
def search_restaurants(query: str, category: str = "", sort_by: str = "rating"): return _env.search_restaurants(query=query, category=category, sort_by=sort_by)

@app.get("/get_restaurant_by_id")
def get_restaurant_by_id(restaurant_id: str): return _env.get_restaurant_by_id(restaurant_id=restaurant_id)

@app.get("/get_restaurant_menu")
def get_restaurant_menu(restaurant_id: str): return _env.get_restaurant_menu(restaurant_id=restaurant_id)

@app.get("/get_dish_by_id")
def get_dish_by_id(dish_id: str): return _env.get_dish_by_id(dish_id=dish_id)

@app.get("/get_nearby_restaurants")
def get_nearby_restaurants(latitude: float, longitude: float, radius: int = 3000, category: str = "", page: int = 1): return _env.get_nearby_restaurants(latitude=latitude, longitude=longitude, radius=radius, category=category, page=page)

@app.get("/get_cart")
def get_cart(): return _env.get_cart()

@app.get("/get_order_list")
def get_order_list(status: str = "", page: int = 1, page_size: int = 20): return _env.get_order_list(status=status or None, page=page, page_size=page_size)

@app.get("/get_order_by_id")
def get_order_by_id(order_id: str): return _env.get_order_by_id(order_id=order_id)

@app.get("/get_delivery_tracking")
def get_delivery_tracking(order_id: str): return _env.get_delivery_tracking(order_id=order_id)

@app.get("/get_address_list")
def get_address_list(): return _env.get_address_list()

@app.get("/get_coupon_list")
def get_coupon_list(restaurant_id: str = ""): return _env.get_coupon_list(restaurant_id=restaurant_id or None)

@app.get("/get_favorite_restaurants")
def get_favorite_restaurants(): return _env.get_favorite_restaurants()


class AddToCartRequest(BaseModel):
    dish_id: str
    quantity: int
    note: Optional[str] = ""

@app.post("/add_to_cart")
def add_to_cart(req: AddToCartRequest): return _env.add_to_cart(dish_id=req.dish_id, quantity=req.quantity, note=req.note)


class UpdateCartRequest(BaseModel):
    cart_item_id: str
    quantity: int

@app.post("/update_cart_item")
def update_cart_item(req: UpdateCartRequest): return _env.update_cart_item(cart_item_id=req.cart_item_id, quantity=req.quantity)


class CartItemIdRequest(BaseModel):
    cart_item_id: str

@app.post("/remove_from_cart")
def remove_from_cart(req: CartItemIdRequest): return _env.remove_from_cart(cart_item_id=req.cart_item_id)

@app.post("/clear_cart")
def clear_cart(): return _env.clear_cart()


class PlaceOrderRequest(BaseModel):
    address_id: str
    coupon_id: Optional[str] = ""
    note: Optional[str] = ""
    utensils: Optional[bool] = True

@app.post("/place_order")
def place_order(req: PlaceOrderRequest): return _env.place_order(address_id=req.address_id, coupon_id=req.coupon_id, note=req.note, utensils=req.utensils)


class CancelOrderRequest(BaseModel):
    order_id: str
    reason: str

@app.post("/cancel_order")
def cancel_order(req: CancelOrderRequest): return _env.cancel_order(order_id=req.order_id, reason=req.reason)


class ReportOrderIssueRequest(BaseModel):
    order_id: str
    issue_type: str
    description: str

@app.post("/report_order_issue")
def report_order_issue(req: ReportOrderIssueRequest): return _env.report_order_issue(order_id=req.order_id, issue_type=req.issue_type, description=req.description)


class RateOrderRequest(BaseModel):
    order_id: str
    food_rating: int
    delivery_rating: int
    comment: Optional[str] = ""

@app.post("/rate_order")
def rate_order(req: RateOrderRequest): return _env.rate_order(order_id=req.order_id, food_rating=req.food_rating, delivery_rating=req.delivery_rating, comment=req.comment)


class AddAddressRequest(BaseModel):
    name: str
    phone: str
    address: str
    floor: Optional[str] = ""
    note: Optional[str] = ""
    is_default: Optional[bool] = False

@app.post("/add_address")
def add_address(req: AddAddressRequest): return _env.add_address(name=req.name, phone=req.phone, address=req.address, floor=req.floor, note=req.note, is_default=req.is_default)


class UpdateAddressRequest(BaseModel):
    address_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_default: Optional[bool] = None

@app.post("/update_address")
def update_address(req: UpdateAddressRequest): return _env.update_address(address_id=req.address_id, name=req.name, phone=req.phone, address=req.address, is_default=req.is_default)


class AddressIdRequest(BaseModel):
    address_id: str

@app.post("/delete_address")
def delete_address(req: AddressIdRequest): return _env.delete_address(address_id=req.address_id)


class RestaurantIdRequest(BaseModel):
    restaurant_id: str

@app.post("/add_favorite_restaurant")
def add_favorite_restaurant(req: RestaurantIdRequest): return _env.add_favorite_restaurant(restaurant_id=req.restaurant_id)

@app.post("/remove_favorite_restaurant")
def remove_favorite_restaurant(req: RestaurantIdRequest): return _env.remove_favorite_restaurant(restaurant_id=req.restaurant_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39208)