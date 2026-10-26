"""Food Delivery environment class."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class FoodDeliverySystem:
    def __init__(self, init_config: Dict[str, Any]):
        self.user_profile: Dict = {}
        self.current_location: Dict = {}
        self.restaurants: Dict[str, Dict] = {}
        self.menus: Dict[str, Dict] = {}
        self.cart: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        self.addresses: Dict[str, Dict] = {}
        self.coupons: Dict[str, Dict] = {}
        self.favorite_restaurants: List[str] = []
        self.ratings: Dict[str, Dict] = {}

    def _ok(self, data): return {"success": True, "data": data}
    def _not_found(self, msg="Not found"): return {"success": False, "error": msg}
    def _new_id(self, prefix=""): return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def get_user_profile(self): return self._ok(self.user_profile)
    def get_current_location(self): return self._ok(self.current_location)

    def search_restaurants(self, query="", category="", sort_by="rating", page=1, page_size=20):
        items = list(self.restaurants.values())
        if query:
            items = [r for r in items if query.lower() in r.get("name", "").lower() or query.lower() in r.get("category", "").lower()]
        if category:
            items = [r for r in items if r.get("category") == category]
        if sort_by == "delivery_time":
            items.sort(key=lambda x: x.get("delivery_time", 999))
        elif sort_by == "rating":
            items.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_by == "sales":
            items.sort(key=lambda x: x.get("monthly_sales", 0), reverse=True)
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_restaurant_by_id(self, restaurant_id: str):
        r = self.restaurants.get(restaurant_id)
        return self._ok(r) if r else self._not_found()

    def get_restaurant_menu(self, restaurant_id: str):
        menu = self.menus.get(restaurant_id)
        return self._ok(menu) if menu else self._not_found("Menu not found")

    def get_dish_by_id(self, dish_id: str):
        for menu in self.menus.values():
            for cat in menu.get("categories", []):
                for d in cat.get("dishes", []):
                    if d.get("dish_id") == dish_id:
                        return self._ok(d)
        return self._not_found()

    def get_nearby_restaurants(self, latitude: float, longitude: float, radius: int = 3000, category: str = "", page: int = 1):
        items = list(self.restaurants.values())
        if category:
            items = [r for r in items if r.get("category") == category]
        page_size = 20
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_cart(self): return self._ok(list(self.cart.values()))

    def get_order_list(self, status=None, page=1, page_size=20):
        items = list(self.orders.values())
        if status:
            items = [o for o in items if o.get("status") == status]
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_order_by_id(self, order_id: str):
        o = self.orders.get(order_id)
        return self._ok(o) if o else self._not_found()

    def get_delivery_tracking(self, order_id: str):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        rider = o.get("rider", {})
        return self._ok({"order_id": order_id, "status": o.get("status"), "rider": rider, "eta_minutes": rider.get("eta_minutes", 0)})

    def get_address_list(self): return self._ok(list(self.addresses.values()))

    def get_coupon_list(self, restaurant_id=None):
        items = list(self.coupons.values())
        if restaurant_id:
            items = [c for c in items if c.get("restaurant_id") == restaurant_id or not c.get("restaurant_id")]
        return self._ok(items)

    def get_favorite_restaurants(self):
        items = [self.restaurants[rid] for rid in self.favorite_restaurants if rid in self.restaurants]
        return self._ok(items)

    def get_restaurant_reviews(self, restaurant_id: str, page=1, page_size=20):
        return self._ok([])

    def _find_dish(self, dish_id: str):
        """Find a dish across all menus, return (restaurant_id, dish) or (None, None)."""
        for rid, menu in self.menus.items():
            for cat in menu.get("categories", []):
                for d in cat.get("dishes", []):
                    if d.get("dish_id") == dish_id:
                        return rid, d
        return None, None

    def add_to_cart(self, dish_id: str, quantity: int, note=""):
        restaurant_id, dish = self._find_dish(dish_id)
        if not dish:
            return self._not_found("Dish not found")
        # 清空不同餐厅的购物车
        existing_restaurant = next((item.get("restaurant_id") for item in self.cart.values()), None)
        if existing_restaurant and existing_restaurant != restaurant_id:
            self.cart.clear()
        cart_id = self._new_id("CART-")
        item = {"cart_item_id": cart_id, "restaurant_id": restaurant_id, "dish_id": dish_id, "quantity": quantity, "price": dish["price"], "note": note, "name": dish["name"]}
        self.cart[cart_id] = item
        return {"success": True, "id": cart_id, "data": item}

    def update_cart_item(self, cart_item_id: str, quantity: int):
        item = self.cart.get(cart_item_id)
        if not item:
            return self._not_found()
        if quantity <= 0:
            del self.cart[cart_item_id]
            return {"success": True, "deleted_id": cart_item_id}
        item["quantity"] = quantity
        return self._ok(item)

    def remove_from_cart(self, cart_item_id: str):
        if cart_item_id not in self.cart:
            return self._not_found()
        del self.cart[cart_item_id]
        return {"success": True, "deleted_id": cart_item_id}

    def clear_cart(self):
        count = len(self.cart)
        self.cart.clear()
        return {"success": True, "cleared_count": count}

    def place_order(self, address_id: str, coupon_id="", note="", utensils=True):
        if not self.cart:
            return {"success": False, "error": "Cart is empty"}
        addr = self.addresses.get(address_id)
        if not addr:
            return self._not_found("Address not found")
        items = list(self.cart.values())
        restaurant_id = items[0].get("restaurant_id")
        restaurant = self.restaurants.get(restaurant_id, {})
        total = sum(i["price"] * i["quantity"] for i in items) + restaurant.get("delivery_fee", 0)
        order_id = self._new_id("ORDER-")
        order = {"order_id": order_id, "restaurant_id": restaurant_id, "restaurant_name": restaurant.get("name", ""), "items": items, "total_amount": total, "status": "pending", "created_at": datetime.now().isoformat(), "address_id": address_id, "note": note, "utensils": utensils, "rider": {}}
        self.orders[order_id] = order
        self.cart.clear()
        return {"success": True, "id": order_id, "data": order}

    def cancel_order(self, order_id: str, reason: str):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        if o.get("status") in ["delivering", "completed"]:
            return {"success": False, "error": "Cannot cancel order in this status"}
        o["status"] = "cancelled"
        o["cancel_reason"] = reason
        return self._ok(o)

    def report_order_issue(self, order_id: str, issue_type: str, description: str):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        issue_id = self._new_id("ISSUE-")
        issue = {"issue_id": issue_id, "order_id": order_id, "issue_type": issue_type, "description": description, "status": "pending", "created_at": datetime.now().isoformat()}
        return {"success": True, "id": issue_id, "data": issue}

    def rate_order(self, order_id: str, food_rating: int, delivery_rating: int, comment=""):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        rating_id = self._new_id("RATE-")
        rating = {"rating_id": rating_id, "order_id": order_id, "food_rating": food_rating, "delivery_rating": delivery_rating, "comment": comment, "created_at": datetime.now().isoformat()}
        self.ratings[order_id] = rating
        return {"success": True, "id": rating_id, "data": rating}

    def add_address(self, name: str, phone: str, address: str, floor="", note="", is_default=False):
        addr_id = self._new_id("ADDR-")
        if is_default:
            for a in self.addresses.values():
                a["is_default"] = False
        addr = {"address_id": addr_id, "name": name, "phone": phone, "address": address, "floor": floor, "note": note, "is_default": is_default}
        self.addresses[addr_id] = addr
        return {"success": True, "id": addr_id, "data": addr}

    def update_address(self, address_id: str, name=None, phone=None, address=None, is_default=None):
        addr = self.addresses.get(address_id)
        if not addr:
            return self._not_found()
        if name is not None:
            addr["name"] = name
        if phone is not None:
            addr["phone"] = phone
        if address is not None:
            addr["address"] = address
        if is_default is not None:
            if is_default:
                for a in self.addresses.values():
                    a["is_default"] = False
            addr["is_default"] = is_default
        return self._ok(addr)

    def delete_address(self, address_id: str):
        if address_id not in self.addresses:
            return self._not_found()
        del self.addresses[address_id]
        return {"success": True, "deleted_id": address_id}

    def add_favorite_restaurant(self, restaurant_id: str):
        if restaurant_id not in self.restaurants:
            return self._not_found("Restaurant not found")
        if restaurant_id not in self.favorite_restaurants:
            self.favorite_restaurants.append(restaurant_id)
        return {"success": True, "data": {"restaurant_id": restaurant_id}}

    def remove_favorite_restaurant(self, restaurant_id: str):
        if restaurant_id in self.favorite_restaurants:
            self.favorite_restaurants.remove(restaurant_id)
        return {"success": True, "deleted_id": restaurant_id}