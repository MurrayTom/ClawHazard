"""Online Shopping environment class."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class OnlineShoppingSystem:
    def __init__(self, init_config: Dict[str, Any]):
        self.user_profile: Dict = {}
        self.categories: Dict[str, Dict] = {}
        self.products: Dict[str, Dict] = {}
        self.cart: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        self.logistics: Dict[str, Dict] = {}
        self.addresses: Dict[str, Dict] = {}
        self.coupons: Dict[str, Dict] = {}
        self.wishlist: List[str] = []
        self.reviews: Dict[str, List] = {}

    def _ok(self, data): return {"success": True, "data": data}
    def _not_found(self, msg="Not found"): return {"success": False, "error": msg}
    def _new_id(self, prefix=""): return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def get_user_profile(self): return self._ok(self.user_profile)

    def search_products(self, query="", category="", min_price=0, max_price=999999, sort_by="relevance", page=1, page_size=20):
        items = list(self.products.values())
        if query:
            items = [p for p in items if query.lower() in p.get("name", "").lower() or query.lower() in p.get("description", "").lower()]
        if category:
            items = [p for p in items if p.get("category_id") == category]
        if min_price > 0:
            items = [p for p in items if p.get("price", 0) >= min_price]
        if max_price < 999999:
            items = [p for p in items if p.get("price", 0) <= max_price]
        if sort_by == "price_asc":
            items.sort(key=lambda x: x.get("price", 0))
        elif sort_by == "price_desc":
            items.sort(key=lambda x: x.get("price", 0), reverse=True)
        elif sort_by == "sales":
            items.sort(key=lambda x: x.get("sales", 0), reverse=True)
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_product_by_id(self, product_id: str):
        p = self.products.get(product_id)
        return self._ok(p) if p else self._not_found()

    def get_product_reviews(self, product_id: str, page=1, page_size=20, rating_filter=None):
        all_reviews = []
        for order_reviews in self.reviews.values():
            all_reviews.extend([r for r in order_reviews if r.get("product_id") == product_id])
        if rating_filter is not None:
            all_reviews = [r for r in all_reviews if r.get("rating") == rating_filter]
        start = (page - 1) * page_size
        return self._ok(all_reviews[start:start + page_size])

    def list_categories(self, parent_id=None):
        items = list(self.categories.values())
        if parent_id is not None:
            items = [c for c in items if c.get("parent_id") == parent_id]
        return self._ok(items)

    def get_category_products(self, category_id: str, page=1, page_size=20):
        items = [p for p in self.products.values() if p.get("category_id") == category_id]
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def get_cart(self):
        return self._ok(list(self.cart.values()))

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

    def get_logistics_info(self, order_id: str):
        order = self.orders.get(order_id)
        if not order:
            return self._not_found("Order not found")
        log = self.logistics.get(order.get("logistics_id", ""))
        return self._ok(log) if log else self._not_found("Logistics not found")

    def get_address_list(self):
        return self._ok(list(self.addresses.values()))

    def get_coupon_list(self, available_only=None):
        items = list(self.coupons.values())
        if available_only:
            items = [c for c in items if c.get("status") == "available"]
        return self._ok(items)

    def get_wishlist(self):
        items = [self.products[pid] for pid in self.wishlist if pid in self.products]
        return self._ok(items)

    def add_to_cart(self, product_id: str, sku_id: str, quantity: int):
        p = self.products.get(product_id)
        if not p:
            return self._not_found("Product not found")
        sku = next((s for s in p.get("skus", []) if s["sku_id"] == sku_id), None)
        if not sku:
            return self._not_found("SKU not found")
        cart_id = self._new_id("CART-")
        item = {"cart_item_id": cart_id, "product_id": product_id, "sku_id": sku_id, "quantity": quantity, "price": sku["price"], "name": f"{p['name']} {sku['name']}"}
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

    def place_order(self, cart_item_ids: List[str], address_id: str, coupon_id="", note=""):
        addr = self.addresses.get(address_id)
        if not addr:
            return self._not_found("Address not found")
        items = [self.cart[cid] for cid in cart_item_ids if cid in self.cart]
        if not items:
            return {"success": False, "error": "No valid cart items"}
        total = sum(i["price"] * i["quantity"] for i in items)
        order_id = self._new_id("ORDER-")
        order = {"order_id": order_id, "items": items, "total_amount": total, "status": "pending_payment", "created_at": datetime.now().isoformat(), "address_id": address_id}
        if note:
            order["note"] = note
        self.orders[order_id] = order
        for cid in cart_item_ids:
            self.cart.pop(cid, None)
        return {"success": True, "id": order_id, "data": order}

    def cancel_order(self, order_id: str, reason: str):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        if o.get("status") in ["shipped", "completed"]:
            return {"success": False, "error": "Cannot cancel shipped or completed orders"}
        o["status"] = "cancelled"
        o["cancel_reason"] = reason
        return self._ok(o)

    def apply_refund(self, order_id: str, reason: str, refund_type: str, amount: float = None):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        o["status"] = "refund_pending"
        o["refund_reason"] = reason
        o["refund_type"] = refund_type
        if amount is not None:
            o["refund_amount"] = amount
        return {"success": True, "id": order_id, "data": o}

    def confirm_receipt(self, order_id: str):
        o = self.orders.get(order_id)
        if not o:
            return self._not_found()
        o["status"] = "completed"
        return self._ok(o)

    def add_address(self, name: str, phone: str, province: str, city: str, district: str, detail: str, is_default=False):
        addr_id = self._new_id("ADDR-")
        if is_default:
            for a in self.addresses.values():
                a["is_default"] = False
        addr = {"address_id": addr_id, "name": name, "phone": phone, "province": province, "city": city, "district": district, "detail": detail, "is_default": is_default}
        self.addresses[addr_id] = addr
        return {"success": True, "id": addr_id, "data": addr}

    def update_address(self, address_id: str, name: str = None, phone: str = None, detail: str = None, is_default: bool = None):
        addr = self.addresses.get(address_id)
        if not addr:
            return self._not_found()
        if name is not None:
            addr["name"] = name
        if phone is not None:
            addr["phone"] = phone
        if detail is not None:
            addr["detail"] = detail
        if is_default is not None:
            addr["is_default"] = is_default
        return self._ok(addr)

    def delete_address(self, address_id: str):
        if address_id not in self.addresses:
            return self._not_found()
        del self.addresses[address_id]
        return {"success": True, "deleted_id": address_id}

    def add_to_wishlist(self, product_id: str):
        if product_id not in self.products:
            return self._not_found("Product not found")
        if product_id not in self.wishlist:
            self.wishlist.append(product_id)
        return {"success": True, "product_id": product_id}

    def remove_from_wishlist(self, product_id: str):
        if product_id in self.wishlist:
            self.wishlist.remove(product_id)
        return {"success": True, "deleted_id": product_id}

    def write_review(self, order_id: str, product_id: str, rating: int, content: str, images: List[str] = None):
        review_id = self._new_id("REV-")
        review = {"review_id": review_id, "order_id": order_id, "product_id": product_id, "rating": rating, "content": content, "created_at": datetime.now().isoformat()}
        if images:
            review["images"] = images
        self.reviews.setdefault(order_id, []).append(review)
        return {"success": True, "id": review_id, "data": review}