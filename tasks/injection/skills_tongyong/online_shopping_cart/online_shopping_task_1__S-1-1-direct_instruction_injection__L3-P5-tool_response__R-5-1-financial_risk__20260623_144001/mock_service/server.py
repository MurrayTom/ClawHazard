"""Online Shopping mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import OnlineShoppingSystem

app = FastAPI(title="Online Shopping Mock Server")

_seed_path = Path(__file__).parent / "online_shopping_task_1_injected.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = OnlineShoppingSystem(init_config=_seed["init_config"])
_env.user_profile = _seed["init_config"]["user_profile"]
_env.categories = _seed["init_config"]["categories"]
_env.products = _seed["init_config"]["products"]
_env.cart = _seed["init_config"]["cart"]
_env.orders = _seed["init_config"]["orders"]
_env.logistics = _seed["init_config"]["logistics"]
_env.addresses = _seed["init_config"]["addresses"]
_env.coupons = _seed["init_config"]["coupons"]
_env.wishlist = _seed["init_config"]["wishlist"]
_env.reviews = _seed["init_config"]["reviews"]


@app.get("/get_user_profile")
def get_user_profile(): return _env.get_user_profile()

@app.get("/search_products")
def search_products(query: str = "", category: str = "", min_price: float = 0, max_price: float = 999999, sort_by: str = "relevance", page: int = 1, page_size: int = 20):
    return _env.search_products(query=query, category=category, min_price=min_price, max_price=max_price, sort_by=sort_by, page=page, page_size=page_size)

@app.get("/get_product_by_id")
def get_product_by_id(product_id: str): return _env.get_product_by_id(product_id=product_id)

@app.get("/get_product_reviews")
def get_product_reviews(product_id: str, page: int = 1, page_size: int = 20, rating_filter: Optional[int] = None): return _env.get_product_reviews(product_id=product_id, page=page, page_size=page_size, rating_filter=rating_filter)

@app.get("/list_categories")
def list_categories(parent_id: Optional[str] = None): return _env.list_categories(parent_id=parent_id)

@app.get("/get_category_products")
def get_category_products(category_id: str, page: int = 1, page_size: int = 20): return _env.get_category_products(category_id=category_id, page=page, page_size=page_size)

@app.get("/get_cart")
def get_cart(): return _env.get_cart()

@app.get("/get_order_list")
def get_order_list(status: str = "", page: int = 1, page_size: int = 20): return _env.get_order_list(status=status or None, page=page, page_size=page_size)

@app.get("/get_order_by_id")
def get_order_by_id(order_id: str): return _env.get_order_by_id(order_id=order_id)

@app.get("/get_logistics_info")
def get_logistics_info(order_id: str): return _env.get_logistics_info(order_id=order_id)

@app.get("/get_address_list")
def get_address_list(): return _env.get_address_list()

@app.get("/get_coupon_list")
def get_coupon_list(available_only: Optional[bool] = None): return _env.get_coupon_list(available_only=available_only)

@app.get("/get_wishlist")
def get_wishlist(): return _env.get_wishlist()


class AddToCartRequest(BaseModel):
    product_id: str
    sku_id: str
    quantity: int

@app.post("/add_to_cart")
def add_to_cart(req: AddToCartRequest): return _env.add_to_cart(product_id=req.product_id, sku_id=req.sku_id, quantity=req.quantity)


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
    cart_item_ids: List[str]
    address_id: str
    coupon_id: Optional[str] = ""
    note: Optional[str] = ""

@app.post("/place_order")
def place_order(req: PlaceOrderRequest): return _env.place_order(cart_item_ids=req.cart_item_ids, address_id=req.address_id, coupon_id=req.coupon_id, note=req.note)


class CancelOrderRequest(BaseModel):
    order_id: str
    reason: str

@app.post("/cancel_order")
def cancel_order(req: CancelOrderRequest): return _env.cancel_order(order_id=req.order_id, reason=req.reason)


class RefundRequest(BaseModel):
    order_id: str
    reason: str
    refund_type: str
    amount: Optional[float] = None

@app.post("/apply_refund")
def apply_refund(req: RefundRequest): return _env.apply_refund(order_id=req.order_id, reason=req.reason, refund_type=req.refund_type, amount=req.amount)


class OrderIdRequest(BaseModel):
    order_id: str

@app.post("/confirm_receipt")
def confirm_receipt(req: OrderIdRequest): return _env.confirm_receipt(order_id=req.order_id)


class AddAddressRequest(BaseModel):
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: Optional[bool] = False

@app.post("/add_address")
def add_address(req: AddAddressRequest): return _env.add_address(name=req.name, phone=req.phone, province=req.province, city=req.city, district=req.district, detail=req.detail, is_default=req.is_default)


class UpdateAddressRequest(BaseModel):
    address_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    detail: Optional[str] = None
    is_default: Optional[bool] = None

@app.post("/update_address")
def update_address(req: UpdateAddressRequest): return _env.update_address(address_id=req.address_id, name=req.name, phone=req.phone, detail=req.detail, is_default=req.is_default)


class AddressIdRequest(BaseModel):
    address_id: str

@app.post("/delete_address")
def delete_address(req: AddressIdRequest): return _env.delete_address(address_id=req.address_id)


class ProductIdRequest(BaseModel):
    product_id: str

@app.post("/add_to_wishlist")
def add_to_wishlist(req: ProductIdRequest): return _env.add_to_wishlist(product_id=req.product_id)

@app.post("/remove_from_wishlist")
def remove_from_wishlist(req: ProductIdRequest): return _env.remove_from_wishlist(product_id=req.product_id)


class WriteReviewRequest(BaseModel):
    order_id: str
    product_id: str
    rating: int
    content: str
    images: Optional[List[str]] = None

@app.post("/write_review")
def write_review(req: WriteReviewRequest): return _env.write_review(order_id=req.order_id, product_id=req.product_id, rating=req.rating, content=req.content, images=req.images)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39207)