from typing import Dict, List, TypedDict
import uuid
from datetime import datetime



class MedicationInfo(TypedDict):
    medication_id: str
    name: str
    dosage: str
    dosage_form: str
    quantity_in_stock: int
    prescription_required: bool
    manufac: str

class UserInfo(TypedDict):
    _id: str
    name: str
    saved_addresses: List[str]
    contact_info: str
    prescription_record: dict

class AddressInfo(TypedDict):
    address_id: str
    user_id: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class OrderItemInfo(TypedDict):
    order_id: str
    medication_id: str
    dosage: str
    quantity: int
    prescription_validated: bool

class OrderInfo(TypedDict):
    order_id: str
    user_id: str
    order_items: List[OrderItemInfo]
    delivery_address_id: str
    status: str
    payment_status: str
    fulfillment_details: str
    timestamp: str

class OnlinePharmacyOrderManagementSystem:
    def __init__(self, init_config: dict):
        # Medication catalog: {medication_id: MedicationInfo}
        self.medications: Dict[str, MedicationInfo] = {}

        # User profiles: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Shipping addresses: {address_id: AddressInfo}
        self.addresses: Dict[str, AddressInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Constraints and business rules:
        # - Medication must be in stock for quantity ordered.
        # - If prescription_required is true, a valid prescription must be on file and validated before order fulfillment.
        # - Only valid shipping addresses from user's profile may be used for delivery.
        # - Orders may not be fulfilled until payment_status is marked as paid.
        # - Dosage and form ordered must match entry in catalog.

        self.init_config = init_config

    def get_medication_by_name_and_dosage(self, name: str, dosage: str) -> dict:
        """
        Retrieve catalog entry (or entries) for the specified medication name and dosage.

        Args:
            name (str): Medication name to search for.
            dosage (str): Dosage string to match.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicationInfo]  # List of matching medications (may be empty)
            }
            If the input is blank:
                {
                    "success": False,
                    "error": "Medication name and dosage must be provided"
                }

        Constraints:
            - No error if no matching medication: return empty list in "data" field.
        """
        if not name or not dosage:
            return {
                "success": False,
                "error": "Medication name and dosage must be provided"
            }

        matches = [
            med for med in self.medications.values()
            if med["name"] == name and med["dosage"] == dosage
        ]

        return {
            "success": True,
            "data": matches
        }

    def check_medication_inventory(self, medication_id: str) -> dict:
        """
        Query the current stock quantity for a medication.

        Args:
            medication_id (str): The unique ID of the medication to check.

        Returns:
            dict: {
                "success": True,
                "data": int,  # The quantity_in_stock of the medication
            }
            or
            {
                "success": False,
                "error": str  # Explanation if medication is not found
            }

        Constraints:
            - The medication must exist in the medication catalog.
        """
        med = self.medications.get(medication_id)
        if not med:
            return { "success": False, "error": "Medication not found" }
        return { "success": True, "data": med["quantity_in_stock"] }

    def is_prescription_required(self, medication_id: str) -> dict:
        """
        Check whether the medication with the given medication_id requires a prescription.

        Args:
            medication_id (str): The unique identifier of the medication.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if prescription required, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. medication not found
            }

        Constraints:
            - medication_id must exist in the medication catalog.
        """
        medication = self.medications.get(medication_id)
        if medication is None:
            return {"success": False, "error": "Medication not found"}
        return {"success": True, "data": medication["prescription_required"]}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the user profile for a specified user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user's profile information
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "User not found"
            }

        Constraints:
            - The user ID must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user_info}

    def get_saved_addresses_for_user(self, user_id: str) -> dict:
        """
        List all saved shipping addresses for a specific user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[AddressInfo]  # List of existing addresses (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # "User not found"
            }

        Constraints:
            - Only addresses that both exist in self.addresses and are in the user's saved_addresses list are returned.
            - If user_id is invalid (user does not exist), fails.
            - If user has no addresses saved, returns empty list (success).
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        address_ids = user.get("saved_addresses", [])
        addresses = [
            self.addresses[address_id]
            for address_id in address_ids
            if address_id in self.addresses
        ]
        return { "success": True, "data": addresses }

    def get_address_by_details(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        country: str,
        user_id: str = None
    ) -> dict:
        """
        Locate a user's address given street, city, state, zip, country, and optionally user_id.

        Args:
            street (str): Street address to search for.
            city (str): City of the address.
            state (str): State of the address.
            zip_code (str): Zip code of the address.
            country (str): Country of the address.
            user_id (str, optional): Restrict lookup to addresses owned by this user.

        Returns:
            dict: {
                "success": True,
                "data": AddressInfo   # Address info object with match
            }
            or
            {
                "success": False,
                "error": str          # Reason for failure
            }

        Constraints:
            - All details must match exactly.
            - If user_id is given, only addresses associated with that user are considered.

        Edge cases:
            - If address is not found, returns error.
            - If fields are empty, treat as non-match.
        """
        for addr in self.addresses.values():
            if (
                addr["street"] == street and
                addr["city"] == city and
                addr["state"] == state and
                addr["zip_code"] == zip_code and
                addr["country"] == country and
                (user_id is None or addr["user_id"] == user_id)
            ):
                return { "success": True, "data": addr }
        return { "success": False, "error": "Address not found" }

    def validate_address_for_user(self, address_id: str, user_id: str) -> dict:
        """
        Confirm that a shipping address (by address_id) is valid and belongs to the specified user.

        Args:
            address_id (str): The address ID to validate.
            user_id (str): The user ID.

        Returns:
            dict:
                - On success: {"success": True, "data": True}
                - On failure: {"success": False, "error": str}

        Constraints:
            - The user must exist.
            - The address must exist.
            - The address must be owned by the user (address.user_id == user_id).
            - The address_id must be present in user's saved_addresses.
        """
        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check address existence
        address = self.addresses.get(address_id)
        if not address:
            return { "success": False, "error": "Address does not exist" }

        # Check that address belongs to user
        if address["user_id"] != user_id:
            return { "success": False, "error": "Address does not belong to user" }

        # Check that address is registered in user's saved_addresses
        if address_id not in user["saved_addresses"]:
            return { "success": False, "error": "Address not listed in user profile" }

        return { "success": True, "data": True }

    def get_prescription_record(self, user_id: str, medication_id: str) -> dict:
        """
        Retrieve a user's prescription record for a specified medication.

        Args:
            user_id (str): User identifier.
            medication_id (str): Medication identifier.

        Returns:
            dict: 
              If user is found:
                {
                    "success": True,
                    "data": prescription_info or None  # If found, details; else None
                }
              If user is not found:
                {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - The user_id must exist.
            - If prescription record for medication is not present, returns None.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        prescription_record = user.get("prescription_record", {})
        # The prescription_record might not have the medication_id
        prescription_info = prescription_record.get(medication_id, None)
        return { "success": True, "data": prescription_info }

    def is_prescription_validated(self, user_id: str, medication_id: str) -> dict:
        """
        Query if a user has a validated prescription for a specific medication.

        Args:
            user_id (str): The user's ID to check.
            medication_id (str): The ID of the medication.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if prescription validated, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Error reason (e.g. user or medication not found)
            }

        Constraints:
            - User must exist.
            - Medication must exist.
            - If no prescription record is present for that medication, treated as not validated.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        if medication_id not in self.medications:
            return { "success": False, "error": "Medication not found" }

        user = self.users[user_id]
        prescription_record = user.get("prescription_record", {})
        med_presc_info = prescription_record.get(medication_id)
        if med_presc_info and isinstance(med_presc_info, dict):
            validated = med_presc_info.get("validated", False)
            return { "success": True, "data": bool(validated) }
        else:
            # No record exists for this medication
            return { "success": True, "data": False }

    def verify_dosage_and_form_match(self, medication_id: str, requested_dosage: str, requested_dosage_form: str) -> dict:
        """
        Check that the requested dosage and dosage form match the catalog entry for a medication.

        Args:
            medication_id (str): ID of the medication to check.
            requested_dosage (str): Dosage string requested.
            requested_dosage_form (str): Dosage form requested.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": bool  # True if match, False if not
                    }
                - On error:
                    {
                        "success": False,
                        "error": "Medication not found"
                    }

        Constraints:
            - Dosage and dosage_form must exactly match the catalog entry for that medication.
        """
        medication = self.medications.get(medication_id)
        if not medication:
            return { "success": False, "error": "Medication not found" }

        match = (
            medication["dosage"] == requested_dosage and
            medication["dosage_form"] == requested_dosage_form
        )
        return { "success": True, "data": match }

    def get_order_by_id(self, order_id: str) -> dict:
        """
        Retrieve order details using order_id.

        Args:
            order_id (str): The unique identifier of the order.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": OrderInfo   # Full details of the order
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Order not found"
                    }

        Constraints:
            - order_id must exist in the system's orders.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order not found"}
        return {"success": True, "data": self.orders[order_id]}

    def get_order_status(self, order_id: str) -> dict:
        """
        Query fulfillment status of an order.
    
        Args:
            order_id (str): Unique identifier for the order.
        
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": status  # (str) Current fulfillment status of the order
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Order not found"
                    }
                
        Constraints:
            - Order with given order_id must exist.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }
        return { "success": True, "data": order["status"] }

    def get_payment_status(self, order_id: str) -> dict:
        """
        Check if an order has been paid.

        Args:
            order_id (str): Unique identifier of the order.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": str  # payment_status ("paid", "unpaid", etc.)
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, usually "Order not found"
                }

        Constraints:
            - The order_id must exist in the system.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }
        return { "success": True, "data": order["payment_status"] }

    def get_fulfillment_details(self, order_id: str) -> dict:
        """
        Retrieve the fulfillment and shipping details for a given order.

        Args:
            order_id (str): The unique identifier of the order.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "order_id": str,
                    "fulfillment_details": str,
                    "shipping_address": AddressInfo | None
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., order not found
            }

        Constraints:
            - order_id must exist in the system.
            - If delivery_address_id is missing in addresses, shipping_address will be None.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }

        address_info = self.addresses.get(order["delivery_address_id"])
        # It's possible for address_info to be None if delivery_address_id not found.

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "fulfillment_details": order.get("fulfillment_details", ""),
                "shipping_address": address_info
            }
        }

    def create_order(
        self,
        user_id: str,
        items: list,
        delivery_address_id: str
    ) -> dict:
        """
        Create a new order for a user for specified medications/dosages/quantities and a delivery address.

        Args:
            user_id (str): ID of the user placing the order.
            items (list): List of dicts:
                [
                    {
                        "medication_id": str,
                        "dosage": str,
                        "quantity": int
                    },
                    ...
                ]
            delivery_address_id (str): ID of shipping address (must belong to the user).

        Returns:
            dict:
                If successful:
                    {
                        "success": True,
                        "message": "Order created",
                        "order_id": str
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
        - Medication must exist and have matching dosage/dosage_form.
        - Medication must be in stock for the requested quantity.
        - If prescription_required, a valid prescription must be on file.
        - Shipping address must be one of user's saved addresses.
        - Order starts with status 'created' and payment_status 'pending'.
        """


        # 1. Validate user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # 2. Validate address exists and belongs to user
        address = self.addresses.get(delivery_address_id)
        if not address or address["user_id"] != user_id or delivery_address_id not in user["saved_addresses"]:
            return {"success": False, "error": "Invalid shipping address for user"}

        order_items = []
        for item in items:
            medication_id = item.get("medication_id")
            dosage = item.get("dosage")
            quantity = item.get("quantity")

            # Validate medication exists
            med = self.medications.get(medication_id)
            if not med:
                return {"success": False, "error": f"Medication {medication_id} not found"}

            # Validate dosage matches
            if med["dosage"] != dosage:
                return {"success": False, "error": f"Dosage {dosage} does not match catalog for medication {medication_id}"}

            # Validate stock
            if med["quantity_in_stock"] < quantity:
                return {"success": False, "error": f"Insufficient stock for medication {medication_id}"}

            # Validate prescription if required
            prescription_validated = True
            if med["prescription_required"]:
                rx_record = user.get("prescription_record", {})
                # Simple check: does record have key for medication and is it validated?
                rx_status = rx_record.get(medication_id)
                if not rx_status or rx_status != "validated":
                    prescription_validated = False
                    return {"success": False, "error": f"Valid prescription not found for medication {medication_id}"}

            order_items.append({
                "order_id": "",  # Temporary; will set below
                "medication_id": medication_id,
                "dosage": dosage,
                "quantity": quantity,
                "prescription_validated": prescription_validated
            })

        # Generate new order_id
        order_id = str(uuid.uuid4())
        for oi in order_items:
            oi["order_id"] = order_id

        order_info = {
            "order_id": order_id,
            "user_id": user_id,
            "order_items": order_items,
            "delivery_address_id": delivery_address_id,
            "status": "created",
            "payment_status": "pending",
            "fulfillment_details": "",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.orders[order_id] = order_info

        return {"success": True, "message": "Order created", "order_id": order_id}

    def reserve_medication_inventory(self, medication_id: str, quantity: int) -> dict:
        """
        Decrement medication inventory by the reserved quantity for an order.

        Args:
            medication_id (str): The ID of the medication to reserve.
            quantity (int): Number of units to reserve (must be positive).

        Returns:
            dict: {
                "success": True,
                "message": "Reserved <quantity> units of medication_id <medication_id>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., not enough stock, invalid medication, bad input
            }

        Constraints:
            - Medication must exist in the catalog.
            - Quantity must be positive.
            - quantity_in_stock >= quantity.
        """
        med = self.medications.get(medication_id)
        if not med:
            return { "success": False, "error": "Medication does not exist" }

        if not isinstance(quantity, int) or quantity <= 0:
            return { "success": False, "error": "Invalid quantity requested" }

        if med["quantity_in_stock"] < quantity:
            return { "success": False, "error": "Insufficient inventory for medication" }

        # Reserve inventory
        med["quantity_in_stock"] -= quantity
        return {
            "success": True,
            "message": f"Reserved {quantity} units of medication_id {medication_id}."
        }

    def validate_prescription_for_order(self, order_id: str, medication_id: str) -> dict:
        """
        Processes and marks a prescription as validated for an order item.

        Args:
            order_id (str): The ID of the order containing the medication.
            medication_id (str): The medication ID to validate prescription for.

        Returns:
            dict: {
                "success": True,
                "message": "Prescription validated for order item"
            }
            or
            dict: {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Order must exist.
            - Order item for medication_id must exist in order.
            - Medication must require a prescription.
            - User must have a valid prescription for this medication.
            - If already validated, return success.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }

        # Find matching order item
        item = next((oi for oi in order["order_items"] if oi["medication_id"] == medication_id), None)
        if not item:
            return { "success": False, "error": "Order item for medication not found" }

        medication = self.medications.get(medication_id)
        if not medication:
            return { "success": False, "error": "Medication not found in catalog" }

        # If prescription not required, just mark as validated (if not already)
        if not medication["prescription_required"]:
            if not item["prescription_validated"]:
                item["prescription_validated"] = True
            return { "success": True, "message": "Prescription validation not required; order item marked as validated." }

        # Already validated
        if item["prescription_validated"]:
            return { "success": True, "message": "Prescription already validated for order item." }

        user = self.users.get(order["user_id"])
        if not user:
            return { "success": False, "error": "User not found for order." }

        # Check prescription record (structure is opaque, so simple existence for medication_id; could be more detailed)
        prescription_record = user.get("prescription_record", {})
        valid_prescription = prescription_record.get(medication_id)

        if not valid_prescription:
            return { "success": False, "error": "No valid prescription on record for this medication." }

        # Mark as validated
        item["prescription_validated"] = True
        return { "success": True, "message": "Prescription validated for order item." }

    def mark_order_as_paid(self, order_id: str) -> dict:
        """
        Updates the payment_status of the specified order to "paid".
    
        Args:
            order_id (str): The unique identifier for the order.

        Returns:
            dict:
                success (bool): True if update succeeds, False otherwise.
                message (str): Success message on payment marked as paid.
                error (str): Present if operation fails (e.g., order not found).

        Constraints:
            - order_id must exist.
            - Does not update cancelled orders ("status" == "cancelled").
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found." }

        if order.get("status") == "cancelled":
            return { "success": False, "error": "Cannot update payment status for cancelled order." }

        order["payment_status"] = "paid"
        # Optionally, update timestamp or other audit info here.

        return { "success": True, "message": "Order payment_status updated to paid." }

    def update_order_fulfillment_status(self, order_id: str, new_status: str) -> dict:
        """
        Update the fulfillment status of an order.
    
        Args:
            order_id (str): The ID of the order to update.
            new_status (str): The new status to set (e.g., "preparing", "shipped", "delivered").
    
        Returns:
            dict: 
              - On success: { "success": True, "message": "Order status updated to <new_status>" }
              - On failure: { "success": False, "error": str }
    
        Constraints:
            - Order must exist.
            - Orders may not be fulfilled (i.e., status beyond 'pending' or pre-payment) until payment_status is 'paid'.
            - Status must be a valid string.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order does not exist" }
    
        # Statuses that imply fulfillment, requiring payment to be 'paid'.
        fulfillment_statuses = {"preparing", "shipped", "delivered", "fulfilled", "completed"}
        if new_status.lower() in fulfillment_statuses:
            if order["payment_status"].lower() != "paid":
                return {
                    "success": False,
                    "error": f"Cannot update order status to '{new_status}' before payment is marked as 'paid'."
                }
    
        # Update the status.
        order["status"] = new_status
        # Update the order entry.
        self.orders[order_id] = order
    
        return {
            "success": True,
            "message": f"Order status updated to '{new_status}'"
        }

    def update_delivery_details(self, order_id: str, fulfillment_details: str) -> dict:
        """
        Assign shipping/tracking info to an order after it has been fulfilled.

        Args:
            order_id (str): The order to update.
            fulfillment_details (str): The shipping or tracking information to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Delivery details updated for order <order_id>."
            }
            or {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
        - The order must exist.
        - The order's status must be 'fulfilled', 'shipped', or equivalent before details can be assigned.
        - Does not update if order not fulfilled.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": f"Order '{order_id}' does not exist."}

        if order["status"].lower() not in ("fulfilled", "shipped"):
            return {"success": False, "error": "Delivery details can only be updated after order fulfillment."}

        order["fulfillment_details"] = fulfillment_details

        return {"success": True, "message": f"Delivery details updated for order {order_id}."}

    def cancel_order(self, order_id: str) -> dict:
        """
        Cancel an existing order. If permitted, restores medication inventory by 
        incrementing the quantities for the ordered items.

        Args:
            order_id (str): The unique identifier of the order to cancel.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Order <order_id> cancelled and inventory restored."
                }
                - On failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Order must exist.
            - Order may only be cancelled if its status is not 'fulfilled', 'shipped', 'delivered', or 'cancelled'.
            - Inventory restoration only happens at cancellation.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": f"Order {order_id} does not exist." }

        if order["status"].lower() in ["fulfilled", "shipped", "delivered", "cancelled"]:
            return { 
                "success": False, 
                "error": f"Order {order_id} cannot be cancelled in its current status ({order['status']})."
            }
    
        # Restore medication inventory
        for item in order["order_items"]:
            medication_id = item["medication_id"]
            quantity = item["quantity"]
            medication = self.medications.get(medication_id)
            if medication:
                medication["quantity_in_stock"] += quantity

        # Mark order as cancelled
        order["status"] = "cancelled"
        # Optionally clear fulfillment_details, etc.

        return {
            "success": True,
            "message": f"Order {order_id} cancelled and inventory restored."
        }

    def modify_order_item(
        self,
        order_id: str,
        order_item_idx: int,
        medication_id: str = None,
        dosage: str = None,
        quantity: int = None
    ) -> dict:
        """
        Adjust medication, dosage, or quantity of an order item prior to order fulfillment.

        Args:
            order_id (str): ID of the order containing the item to modify.
            order_item_idx (int): Index within the order's order_items list (0-based).
            medication_id (str, optional): New medication_id to set (if changing medication).
            dosage (str, optional): New dosage to set (if changing dosage).
            quantity (int, optional): New quantity (if changing quantity).

        Returns:
            dict: {
                "success": True,
                "message": "Order item updated for order <order_id>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - May only modify items for orders that are not yet fulfilled/cancelled/completed.
            - The medication_id and dosage must exist in catalog and match.
            - Quantity must not exceed available stock.
            - Index must be valid in order_items list.
        """
        # 1. Find the order
        order = self.orders.get(order_id)
        if order is None:
            return {"success": False, "error": "Order not found."}

        if order["status"] in ("fulfilled", "shipped", "delivered", "cancelled", "completed"):
            return {"success": False, "error": "Order cannot be modified after fulfillment has started."}

        # 2. Validate index
        if (
            not isinstance(order_item_idx, int)
            or order_item_idx < 0 
            or order_item_idx >= len(order["order_items"])
        ):
            return {"success": False, "error": "Invalid order item index."}

        item = order["order_items"][order_item_idx]

        # Fields to update
        new_medication_id = medication_id if medication_id is not None else item["medication_id"]
        new_dosage = dosage if dosage is not None else item["dosage"]
        new_quantity = quantity if quantity is not None else item["quantity"]

        # 3. Medication/dosage checks
        med = self.medications.get(new_medication_id)
        if med is None:
            return {"success": False, "error": "Medication not found in catalog."}

        if med["dosage"] != new_dosage:
            return {"success": False, "error": "Dosage does not match medication catalog."}

        # 4. Inventory check
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            return {"success": False, "error": "Quantity must be positive integer."}

        if med["quantity_in_stock"] < new_quantity:
            return {"success": False, "error": "Insufficient inventory for requested quantity."}

        # 5. Update the item
        item["medication_id"] = new_medication_id
        item["dosage"] = new_dosage
        item["quantity"] = new_quantity
        # You might reset prescription validation if necessary (not specified here)

        return {
            "success": True,
            "message": f"Order item updated for order {order_id}."
        }

    def add_address_to_user(self, user_id: str, address_info: dict) -> dict:
        """
        Save a new shipping address to a user's profile.

        Args:
            user_id (str): ID of the user to add the address to.
            address_info (dict): Includes street, city, state, zip_code, country.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Address added successfully"
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The user_id must exist.
            - The address must include all required fields: street, city, state, zip_code, country.
            - Address must not already exist for the user (same street/city/state/zip/country).
            - The newly created address object is stored in self.addresses and address_id added to user's saved_addresses.
        """
        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        required_fields = ["street", "city", "state", "zip_code", "country"]
        for field in required_fields:
            if field not in address_info or not address_info[field]:
                return { "success": False, "error": f"Missing required address field: {field}" }

        # Check for address duplication (by address content for this user)
        for addr_id in user["saved_addresses"]:
            addr = self.addresses.get(addr_id)
            if addr and all(addr[field] == address_info[field] for field in required_fields):
                return { "success": False, "error": "Address already exists for this user" }
    
        # Generate unique address_id (simple random + user_id + count)
        address_id = str(uuid.uuid4())

        # Create AddressInfo
        new_address = {
            "address_id": address_id,
            "user_id": user_id,
            "street": address_info["street"],
            "city": address_info["city"],
            "state": address_info["state"],
            "zip_code": address_info["zip_code"],
            "country": address_info["country"]
        }

        # Save in system
        self.addresses[address_id] = new_address
        user["saved_addresses"].append(address_id)

        return { "success": True, "message": "Address added successfully" }

    def remove_address_from_user(self, user_id: str, address_id: str) -> dict:
        """
        Removes a shipping address from a user's profile, if it is associated.

        Args:
            user_id (str): The user ID.
            address_id (str): The address ID to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Address removed from user profile"
            }
            or
            {
                "success": False,
                "error": str  # explanation of the failure reason
            }

        Constraints:
            - User must exist.
            - Address must exist.
            - Address must belong to user.
            - Address must be present in user's saved_addresses.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        address = self.addresses.get(address_id)
        if not address:
            return { "success": False, "error": "Address does not exist" }

        if address["user_id"] != user_id:
            return { "success": False, "error": "Address does not belong to user" }

        if address_id not in user["saved_addresses"]:
            return { "success": False, "error": "Address not found in user's saved addresses" }

        user["saved_addresses"].remove(address_id)
        return { "success": True, "message": "Address removed from user profile" }