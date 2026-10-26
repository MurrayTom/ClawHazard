import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TypedDict


class RestaurantInfo(TypedDict, total=False):
    restaurant_id: str
    name: str
    category: str
    rating: float
    address: str
    latitude: float
    longitude: float
    min_order_amount: float
    delivery_fee: float
    delivery_time: int


class MenuItemInfo(TypedDict, total=False):
    item_id: str
    restaurant_id: str
    name: str
    price: float
    category: str
    description: str
    is_available: bool


class CartInfo(TypedDict, total=False):
    cart_id: str
    user_id: str
    restaurant_id: str
    items: List[Dict]
    total_price: float
    applied_coupon: Optional[str]


class OrderInfo(TypedDict, total=False):
    order_id: str
    user_id: str
    restaurant_id: str
    status: str
    total_price: float
    delivery_address: str
    delivery_address_id: str
    created_at: str
    items: List[Dict]
    coupon_id: Optional[str]
    note: str
    payment_method: str


class DeliveryInfo(TypedDict, total=False):
    delivery_id: str
    order_id: str
    rider_id: str
    rider_name: str
    rider_phone: str
    status: str
    estimated_arrival: str


class CouponInfo(TypedDict, total=False):
    coupon_id: str
    user_id: str
    type: str
    discount_value: float
    min_order_amount: float
    expiry_date: str
    is_used: bool


class PromotionInfo(TypedDict, total=False):
    promotion_id: str
    restaurant_id: str
    type: str
    description: str
    start_time: str
    end_time: str


class ReviewInfo(TypedDict, total=False):
    review_id: str
    order_id: str
    user_id: str
    restaurant_id: str
    restaurant_rating: int
    rider_rating: int
    content: str
    created_at: str


class AddressInfo(TypedDict, total=False):
    address_id: str
    user_id: str
    label: str
    full_address: str
    latitude: float
    longitude: float
    contact_name: str
    contact_phone: str
    is_default: bool


class RefundRequestInfo(TypedDict, total=False):
    refund_request_id: str
    order_id: str
    user_id: str
    reason_type: str
    description: str
    status: str
    refund_amount: float
    created_at: str


class MeituanDeliverySystem:
    def __init__(self, init_config: dict):
        self.init_config = init_config
        self.restaurants: Dict[str, RestaurantInfo] = {}
        self.menu_items: Dict[str, MenuItemInfo] = {}
        self.carts: Dict[str, CartInfo] = {}
        self.orders: Dict[str, OrderInfo] = {}
        self.deliveries: Dict[str, DeliveryInfo] = {}
        self.coupons: Dict[str, CouponInfo] = {}
        self.promotions: Dict[str, PromotionInfo] = {}
        self.reviews: Dict[str, ReviewInfo] = {}
        self.addresses: Dict[str, AddressInfo] = {}
        self.refund_requests: Dict[str, RefundRequestInfo] = {}

    def _ok(self, data=None, **kwargs):
        result = {"success": True, "data": data}
        result.update(kwargs)
        return result

    def _err(self, msg):
        return {"success": False, "error": msg}

    def _new_id(self, prefix):
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def _paginate(self, items, page, page_size):
        start = (page - 1) * page_size
        return items[start:start + page_size]

    def _calc_cart_total(self, items):
        total = 0.0
        for i in items:
            price = i.get("price", 0) if isinstance(i, dict) else 0
            quantity = i.get("quantity", 0) if isinstance(i, dict) else 0
            try:
                total += float(price) * int(quantity)
            except (TypeError, ValueError):
                pass
        return total

    def search_restaurants(self, latitude: float, longitude: float, keyword: str = None,
                           category: str = None, sort_by: str = "comprehensive",
                           page: int = 1, page_size: int = 20) -> dict:
        results = []
        for r in self.restaurants.values():
            dist = self._distance(latitude, longitude, r.get("latitude", 0), r.get("longitude", 0))
            if dist > 5:
                continue
            if keyword and keyword.lower() not in r.get("name", "").lower() and keyword.lower() not in r.get("category", "").lower():
                continue
            if category and r.get("category", "") != category:
                continue
            entry = dict(r)
            entry["distance"] = round(dist, 2)
            results.append(entry)
        if sort_by == "rating":
            results.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_by == "delivery_time":
            results.sort(key=lambda x: x.get("delivery_time", 99))
        elif sort_by == "sales":
            results.sort(key=lambda x: x.get("sales", 0), reverse=True)
        else:
            results.sort(key=lambda x: x.get("distance", 99))
        total = len(results)
        page_results = self._paginate(results, page, page_size)
        return self._ok({"restaurants": page_results, "total": total, "page": page})

    def get_restaurant_detail(self, restaurant_id: str) -> dict:
        if restaurant_id not in self.restaurants:
            return self._err("Restaurant not found")
        r = self.restaurants[restaurant_id]
        menu = [m for m in self.menu_items.values() if m.get("restaurant_id") == restaurant_id]
        return self._ok({"restaurant": dict(r), "menu_items": menu})

    def list_menu_items(self, restaurant_id: str, category: str = None,
                        page: int = 1, page_size: int = 50) -> dict:
        if restaurant_id not in self.restaurants:
            return self._err("Restaurant not found")
        items = [m for m in self.menu_items.values() if m.get("restaurant_id") == restaurant_id]
        if category:
            items = [m for m in items if m.get("category") == category]
        total = len(items)
        return self._ok({"items": self._paginate(items, page, page_size), "total": total})

    def get_menu_item_detail(self, item_id: str, restaurant_id: str) -> dict:
        if restaurant_id not in self.restaurants:
            return self._err("Restaurant not found")
        item = self.menu_items.get(item_id)
        if not item or item.get("restaurant_id") != restaurant_id:
            return self._err("Menu item not found")
        return self._ok(dict(item))

    def get_cart(self, user_id: str) -> dict:
        for cart in self.carts.values():
            if cart.get("user_id") == user_id:
                return self._ok(dict(cart))
        return self._ok({"cart_id": None, "user_id": user_id, "restaurant_id": None, "items": [], "total_price": 0})

    def add_to_cart(self, user_id: str, restaurant_id: str, item_id: str,
                    quantity: int, customization: str = None) -> dict:
        if restaurant_id not in self.restaurants:
            return self._err("Restaurant not found")
        item = self.menu_items.get(item_id)
        if not item or item.get("restaurant_id") != restaurant_id:
            return self._err("Menu item not found in this restaurant")
        if not item.get("is_available", True):
            return self._err("Menu item is not available")
        if quantity <= 0:
            return self._err("Quantity must be positive")
        # Find existing cart for user
        user_cart = None
        for cart in self.carts.values():
            if cart.get("user_id") == user_id:
                user_cart = cart
                break
        if user_cart:
            if user_cart.get("restaurant_id") != restaurant_id:
                return self._err("Cart contains items from another restaurant. Clear cart first.")
            # Add item
            found = False
            cart_items = user_cart.get("items", [])
            if not isinstance(cart_items, list):
                cart_items = []
                user_cart["items"] = cart_items
            for ci in cart_items:
                if ci.get("item_id") == item_id and ci.get("customization") == customization:
                    ci["quantity"] = ci.get("quantity", 0) + quantity
                    found = True
                    break
            if not found:
                cart_items.append({
                    "item_id": item_id, "name": item.get("name"), "price": item.get("price", 0),
                    "quantity": quantity, "customization": customization
                })
            user_cart["total_price"] = self._calc_cart_total(cart_items)
            return self._ok(dict(user_cart), id=user_cart.get("cart_id"))
        else:
            cart_id = self._new_id("CART")
            new_cart: CartInfo = {
                "cart_id": cart_id, "user_id": user_id, "restaurant_id": restaurant_id,
                "items": [{"item_id": item_id, "name": item.get("name"), "price": item.get("price", 0),
                           "quantity": quantity, "customization": customization}],
                "total_price": float(item.get("price", 0)) * quantity, "applied_coupon": None
            }
            self.carts[cart_id] = new_cart
            return self._ok(dict(new_cart), id=cart_id)

    def remove_from_cart(self, cart_id: str, item_id: str, quantity: int = None) -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            return self._err("Cart not found")
        items = cart.get("items", [])
        if not isinstance(items, list):
            items = []
            cart["items"] = items
        found = False
        for i, ci in enumerate(items):
            if ci.get("item_id") == item_id:
                found = True
                if quantity is None or ci.get("quantity", 0) <= quantity:
                    items.pop(i)
                else:
                    ci["quantity"] = ci.get("quantity", 0) - quantity
                break
        if not found:
            return self._err("Item not found in cart")
        cart["total_price"] = self._calc_cart_total(items)
        return self._ok(dict(cart))

    def clear_cart(self, cart_id: str) -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            return self._err("Cart not found")
        cart["items"] = []
        cart["total_price"] = 0
        cart["applied_coupon"] = None
        return self._ok(dict(cart))

    def calculate_order_price(self, cart_id: str, coupon_id: str = None,
                              delivery_address_id: str = None) -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            return self._err("Cart not found")
        subtotal = cart.get("total_price", 0)
        delivery_fee = 5.0  # default
        restaurant = self.restaurants.get(cart.get("restaurant_id", ""))
        if restaurant:
            delivery_fee = restaurant.get("delivery_fee", 5.0)
        discount = 0.0
        if coupon_id:
            coupon = self.coupons.get(coupon_id)
            if coupon and not coupon.get("is_used") and subtotal >= coupon.get("min_order_amount", 0):
                discount = coupon.get("discount_value", 0)
        total = max(0, subtotal + delivery_fee - discount)
        return self._ok({"subtotal": subtotal, "delivery_fee": delivery_fee,
                         "discount": discount, "total": round(total, 2)})

    def list_promotions(self, restaurant_id: str = None, promotion_type: str = None) -> dict:
        results = []
        for p in self.promotions.values():
            if restaurant_id and p.get("restaurant_id") != restaurant_id:
                continue
            if promotion_type and p.get("type") != promotion_type:
                continue
            results.append(dict(p))
        return self._ok({"promotions": results, "total": len(results)})

    def list_coupons(self, user_id: str, status: str = "available",
                     page: int = 1, page_size: int = 20) -> dict:
        results = []
        now = datetime.now().isoformat()
        for c in self.coupons.values():
            if c.get("user_id") != user_id:
                continue
            if status == "available" and (c.get("is_used") or c.get("expiry_date", "9999") < now):
                continue
            if status == "used" and not c.get("is_used"):
                continue
            if status == "expired" and (c.get("is_used") or c.get("expiry_date", "9999") >= now):
                continue
            results.append(dict(c))
        total = len(results)
        return self._ok({"coupons": self._paginate(results, page, page_size), "total": total})

    def apply_coupon(self, cart_id: str, coupon_id: str) -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            return self._err("Cart not found")
        coupon = self.coupons.get(coupon_id)
        if not coupon:
            return self._err("Coupon not found")
        if coupon.get("is_used"):
            return self._err("Coupon already used")
        if cart.get("total_price", 0) < coupon.get("min_order_amount", 0):
            return self._err(f"Order amount does not meet minimum requirement of {coupon.get('min_order_amount')}")
        cart["applied_coupon"] = coupon_id
        return self._ok(dict(cart))

    def create_order(self, cart_id: str, delivery_address_id: str, payment_method: str,
                     note: str = None, cutlery_needed: bool = False) -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            return self._err("Cart not found")
        if not cart.get("items"):
            return self._err("Cart is empty")
        if payment_method not in ("wechat_pay", "alipay", "balance"):
            return self._err("Invalid payment method")
        address = self.addresses.get(delivery_address_id)
        if not address:
            return self._err("Delivery address not found")
        restaurant = self.restaurants.get(cart.get("restaurant_id", ""))
        if restaurant:
            dist = self._distance(address.get("latitude", 0), address.get("longitude", 0),
                                  restaurant.get("latitude", 0), restaurant.get("longitude", 0))
            if dist > 5:
                return self._err("Delivery address is out of range (>5km)")
            if cart.get("total_price", 0) < restaurant.get("min_order_amount", 0):
                return self._err(f"Order does not meet minimum amount of {restaurant.get('min_order_amount')}")
        # Calculate total
        subtotal = cart.get("total_price", 0)
        delivery_fee = restaurant.get("delivery_fee", 5.0) if restaurant else 5.0
        discount = 0.0
        coupon_id = cart.get("applied_coupon")
        if coupon_id:
            coupon = self.coupons.get(coupon_id)
            if coupon and not coupon.get("is_used"):
                discount = coupon.get("discount_value", 0)
                coupon["is_used"] = True
        total = max(0, subtotal + delivery_fee - discount)
        order_id = self._new_id("ORD")
        order: OrderInfo = {
            "order_id": order_id, "user_id": cart.get("user_id"),
            "restaurant_id": cart.get("restaurant_id"), "status": "pending",
            "total_price": round(total, 2), "delivery_address": address.get("full_address", ""),
            "delivery_address_id": delivery_address_id,
            "created_at": datetime.now().isoformat(), "items": list(cart.get("items", [])),
            "coupon_id": coupon_id, "note": note or "", "payment_method": payment_method
        }
        self.orders[order_id] = order
        # Create delivery
        delivery_id = self._new_id("DLV")
        delivery: DeliveryInfo = {
            "delivery_id": delivery_id, "order_id": order_id,
            "rider_id": self._new_id("RDR"), "rider_name": "配送员",
            "rider_phone": "138****0000", "status": "pending",
            "estimated_arrival": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        self.deliveries[delivery_id] = delivery
        # Clear cart
        cart["items"] = []
        cart["total_price"] = 0
        cart["applied_coupon"] = None
        return self._ok(dict(order), id=order_id)

    def list_orders(self, user_id: str, status: str = None,
                    page: int = 1, page_size: int = 10) -> dict:
        results = []
        for o in self.orders.values():
            if o.get("user_id") != user_id:
                continue
            if status and o.get("status") != status:
                continue
            results.append(dict(o))
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(results)
        return self._ok({"orders": self._paginate(results, page, page_size), "total": total})

    def get_order_detail(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err("Order not found")
        return self._ok(dict(order))

    def cancel_order(self, order_id: str, reason: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err("Order not found")
        if order.get("status") not in ("pending", "confirmed"):
            return self._err("Order cannot be cancelled in current status")
        order["status"] = "cancelled"
        return self._ok({"order_id": order_id, "status": "cancelled", "reason": reason})

    def track_delivery(self, order_id: str, delivery_id: str = None) -> dict:
        if delivery_id:
            delivery = self.deliveries.get(delivery_id)
            if delivery and delivery.get("order_id") == order_id:
                return self._ok(dict(delivery))
        for d in self.deliveries.values():
            if d.get("order_id") == order_id:
                return self._ok(dict(d))
        return self._err("Delivery information not found for this order")

    def contact_rider(self, delivery_id: str, order_id: str) -> dict:
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            return self._err("Delivery not found")
        if delivery.get("order_id") != order_id:
            return self._err("Delivery does not match order")
        return self._ok({"rider_name": delivery.get("rider_name"),
                         "rider_phone": delivery.get("rider_phone"),
                         "delivery_id": delivery_id})

    def submit_refund_request(self, order_id: str, reason_type: str, description: str,
                              item_ids: list = None, images: list = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err("Order not found")
        valid_reasons = ("missing_item", "wrong_item", "food_quality", "late_delivery", "other")
        if reason_type not in valid_reasons:
            return self._err(f"Invalid reason_type. Must be one of: {valid_reasons}")
        if order.get("status") == "completed":
            created = datetime.fromisoformat(order.get("created_at", datetime.now().isoformat()))
            if (datetime.now() - created) > timedelta(hours=48):
                return self._err("Refund request must be submitted within 48 hours of order completion")
        refund_id = self._new_id("RFD")
        refund: RefundRequestInfo = {
            "refund_request_id": refund_id, "order_id": order_id,
            "user_id": order.get("user_id"), "reason_type": reason_type,
            "description": description, "status": "pending",
            "refund_amount": order.get("total_price", 0),
            "created_at": datetime.now().isoformat()
        }
        self.refund_requests[refund_id] = refund
        return self._ok(dict(refund), id=refund_id)

    def get_refund_status(self, order_id: str, refund_request_id: str = None) -> dict:
        if refund_request_id:
            r = self.refund_requests.get(refund_request_id)
            if r and r.get("order_id") == order_id:
                return self._ok(dict(r))
        for r in self.refund_requests.values():
            if r.get("order_id") == order_id:
                return self._ok(dict(r))
        return self._err("No refund request found for this order")

    def submit_review(self, order_id: str, restaurant_rating: int, rider_rating: int,
                      content: str = None, tags: list = None, images: list = None) -> dict:
        order = self.orders.get(order_id)
        if not order:
            return self._err("Order not found")
        if order.get("status") != "completed":
            return self._err("Can only review completed orders")
        if restaurant_rating < 1 or restaurant_rating > 5 or rider_rating < 1 or rider_rating > 5:
            return self._err("Ratings must be between 1 and 5")
        # Check one review per user per restaurant per day
        today = datetime.now().date().isoformat()
        for rv in self.reviews.values():
            if (rv.get("user_id") == order.get("user_id") and
                rv.get("restaurant_id") == order.get("restaurant_id") and
                rv.get("created_at", "")[:10] == today):
                return self._err("You can only submit one review per restaurant per day")
        review_id = self._new_id("REV")
        review: ReviewInfo = {
            "review_id": review_id, "order_id": order_id,
            "user_id": order.get("user_id"), "restaurant_id": order.get("restaurant_id"),
            "restaurant_rating": restaurant_rating, "rider_rating": rider_rating,
            "content": content or "", "created_at": datetime.now().isoformat()
        }
        self.reviews[review_id] = review
        return self._ok(dict(review), id=review_id)

    def list_user_addresses(self, user_id: str) -> dict:
        results = [dict(a) for a in self.addresses.values() if a.get("user_id") == user_id]
        return self._ok({"addresses": results, "total": len(results)})

    def add_user_address(self, user_id: str, label: str, full_address: str,
                         latitude: float, longitude: float, contact_name: str,
                         contact_phone: str, is_default: bool = False) -> dict:
        if label not in ("home", "work", "other"):
            return self._err("Label must be home, work, or other")
        if is_default:
            for a in self.addresses.values():
                if a.get("user_id") == user_id:
                    a["is_default"] = False
        addr_id = self._new_id("ADDR")
        addr: AddressInfo = {
            "address_id": addr_id, "user_id": user_id, "label": label,
            "full_address": full_address, "latitude": latitude, "longitude": longitude,
            "contact_name": contact_name, "contact_phone": contact_phone, "is_default": is_default
        }
        self.addresses[addr_id] = addr
        return self._ok(dict(addr), id=addr_id)