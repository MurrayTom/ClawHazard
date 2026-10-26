from typing import Dict, TypedDict



class UserAccountInfo(TypedDict):
    _id: str
    name: str
    email: str
    authentication_status: str  # e.g., "authenticated", "unauthenticated"

class InvoiceInfo(TypedDict):
    invoice_id: str
    user_id: str  # must reference a UserAccount
    date_issued: str
    due_date: str
    total_amount: float
    status: str  # e.g., "unpaid", "paid", etc.

class PaymentInfo(TypedDict):
    payment_id: str
    user_id: str       # must reference UserAccount
    invoice_id: str    # must reference Invoice
    payment_date: str
    amount: float      # constraint: amount <= invoice total_amount
    payment_method: str
    status: str        # e.g., "success", "failed"

class ChargeInfo(TypedDict):
    charge_id: str
    invoice_id: str        # must reference Invoice
    description: str
    amount: float          # constraint: non-negative

class OnlineAccountBillingPortal:
    def __init__(self, init_config: dict):
        # Users: {_id: UserAccountInfo}
        # Entity mapping: UserAccount (_id, name, email, authentication_status)
        self.users: Dict[str, UserAccountInfo] = {}

        # Invoices: {invoice_id: InvoiceInfo}
        # Entity mapping: Invoice (invoice_id, user_id, date_issued, due_date, total_amount, status)
        self.invoices: Dict[str, InvoiceInfo] = {}

        # Payments: {payment_id: PaymentInfo}
        # Entity mapping: Payment (payment_id, user_id, invoice_id, payment_date, amount, payment_method, status)
        self.payments: Dict[str, PaymentInfo] = {}

        # Charges: {charge_id: ChargeInfo}
        # Entity mapping: Charge (charge_id, invoice_id, description, amount)
        self.charges: Dict[str, ChargeInfo] = {}

        # Constraints:
        # 1. Only authenticated users can access billing history.
        # 2. Each invoice must be associated with a single user.
        # 3. Payments must reference an invoice and user.
        # 4. Payment amount cannot exceed invoice total_amount.
        # 5. Charges must be non-negative and sum to the invoice's total_amount.

        self.init_config = init_config

    def check_user_authentication_status(self, user_id: str) -> dict:
        """
        Verify if a user is authenticated and allowed to access their billing history.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                success: True if the call is valid (user found), False otherwise.
                data: { "authenticated": bool } (True if authenticated, False otherwise) on success.
                error: Reason for failure if user ID does not exist.

        Constraints:
            - User must exist in the system.
            - Authentication status is checked against "authenticated".
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        authenticated = (user.get("authentication_status") == "authenticated")
        return { "success": True, "data": { "authenticated": authenticated } }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user account details for the given user ID.

        Args:
            user_id (str): The user ID whose account info is to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo  # The user's information
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., user not found
            }

        Constraints:
            - The specified user ID must exist in the portal.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "Not found" }
        return { "success": True, "data": user_info }

    def list_user_invoices(self, user_id: str) -> dict:
        """
        Retrieve all invoices associated with a specific user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict:
                If successful:
                    {
                        "success": True,
                        "data": List[InvoiceInfo],  # List of user's invoices (may be empty)
                    }
                If error (user missing or not authenticated):
                    {
                        "success": False,
                        "error": str,
                    }

        Constraints:
            - Only authenticated users can access their billing history.
            - User must exist.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        if user.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User is not authenticated"}

        user_invoices = [
            invoice for invoice in self.invoices.values()
            if invoice["user_id"] == user_id
        ]
        return {"success": True, "data": user_invoices}

    def get_invoice_details(self, invoice_id: str) -> dict:
        """
        Retrieve full details for a specific invoice (dates, amounts, user, status).

        Args:
            invoice_id (str): The unique identifier of the invoice.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": InvoiceInfo  # full invoice metadata
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Invoice not found"
                    }
        Constraints:
            - No authentication check performed (for this operation).
            - The invoice must exist in the system.
        """
        invoice = self.invoices.get(invoice_id)
        if invoice is None:
            return { "success": False, "error": "Not found" }
        return { "success": True, "data": invoice }

    def list_invoice_charges(self, invoice_id: str) -> dict:
        """
        Retrieve all charge line items associated with a specific invoice.

        Args:
            invoice_id (str): The ID of the invoice to lookup.

        Returns:
            dict: {
                "success": True,
                "data": List[ChargeInfo]    # List of charge info dictionaries (may be empty if no charges)
            }
            or
            {
                "success": False,
                "error": str                # Error message (invoice not found)
            }

        Constraints:
            - The invoice must exist.
        """
        if invoice_id not in self.invoices:
            return { "success": False, "error": "Invoice not found" }

        result = [
            charge_info for charge_info in self.charges.values()
            if charge_info["invoice_id"] == invoice_id
        ]

        return { "success": True, "data": result }

    def list_user_payments(self, user_id: str) -> dict:
        """
        Retrieve all payment records associated with a specific user.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[PaymentInfo]  # May be empty if no payments
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure ("User not found", "Access denied")
                    }

        Constraints:
            - Only authenticated users can access billing history.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        if user.get("authentication_status") != "authenticated":
            return { "success": False, "error": "Access denied: user not authenticated" }

        payments_list = [
            payment for payment in self.payments.values()
            if payment["user_id"] == user_id
        ]
        return { "success": True, "data": payments_list }

    def list_invoice_payments(self, invoice_id: str) -> dict:
        """
        Retrieve all payments associated with the specified invoice.

        Args:
            invoice_id (str): The ID of the invoice for which to list payments.

        Returns:
            dict: {
                "success": True,
                "data": List[PaymentInfo],  # All payments referencing the invoice_id (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. invoice does not exist
            }

        Constraints:
            - The invoice_id must exist in the system.
        """
        if invoice_id not in self.invoices:
            return { "success": False, "error": "Invoice does not exist" }

        payments = [
            payment_info for payment_info in self.payments.values()
            if payment_info["invoice_id"] == invoice_id
        ]
        return { "success": True, "data": payments }

    def get_payment_details(self, user_id: str, payment_id: str) -> dict:
        """
        Retrieve the details of a specific payment, including status, method, and amount.
        Only the authenticated owner of the payment can access its details.

        Args:
            user_id (str): The user's unique ID (requesting user, must be authenticated).
            payment_id (str): The payment's unique ID.

        Returns:
            dict: {
                "success": True,
                "data": PaymentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only authenticated users can access billing history.
            - User can only retrieve payments belonging to themselves.
            - Payment must exist.
        """
        # Verify user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        if user.get("authentication_status") != "authenticated":
            return {"success": False, "error": "User not authenticated"}
        # Verify payment exists
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Not found"}
        # Check ownership
        if payment.get("user_id") != user_id:
            return {"success": False, "error": "Payment does not belong to user"}
        return {"success": True, "data": payment}

    def summarize_billing_history(self, user_id: str) -> dict:
        """
        Produce a comprehensive summary of invoices, payments, and charges for a user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "invoices": List[InvoiceInfo],
                            "payments": List[PaymentInfo],
                            "charges": List[ChargeInfo]
                        }
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Reason (user not found or unauthenticated)
                    }

        Constraints:
            - Only authenticated users can access billing history.
            - All returned invoices/payments/charges must belong to the specified user.

        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "Not found"}
        if user.get("authentication_status", "unauthenticated") != "authenticated":
            return {"success": False, "error": "User not authenticated"}

        # Get all invoices for user
        user_invoices = [
            invoice for invoice in self.invoices.values()
            if invoice["user_id"] == user_id
        ]
        invoice_ids = {inv["invoice_id"] for inv in user_invoices}

        # All payments for these invoices (AND for this user)
        user_payments = [
            payment for payment in self.payments.values()
            if payment["user_id"] == user_id and payment["invoice_id"] in invoice_ids
        ]

        # All charges for these invoices
        user_charges = [
            charge for charge in self.charges.values()
            if charge["invoice_id"] in invoice_ids
        ]

        summary = {
            "invoices": user_invoices,
            "payments": user_payments,
            "charges": user_charges
        }

        return {"success": True, "data": summary}

    def update_authentication_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's authentication status (e.g., after login/logout).

        Args:
            user_id (str): The unique ID of the user whose authentication status is to be changed.
            new_status (str): The new authentication status (e.g., "authenticated", "unauthenticated").

        Returns:
            dict: {
                "success": True,
                "data": {...}  # Updated user record
            }
            or
            {
                "success": False,
                "error": "User does not exist"
            }

        Constraints:
            - user_id must exist in self.users.
            - new_status can be any string, but typical values are "authenticated" or "unauthenticated".
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        user["authentication_status"] = new_status
        return {
            "success": True,
            "data": user
        }

    def update_invoice_status(self, invoice_id: str, new_status: str) -> dict:
        """
        Update the status of an invoice (e.g., "paid", "unpaid").

        Args:
            invoice_id (str): The identifier of the invoice to update.
            new_status (str): The new status to set.

        Returns:
            dict: {
                "success": True,
                "data": {...}  # Updated invoice record
            }
            or
            {
                "success": False,
                "error": str    # Reason for failure, e.g. invoice not found
            }

        Constraints:
            - The invoice_id must exist in self.invoices.
        """
        if invoice_id not in self.invoices:
            return {"success": False, "error": "Invoice does not exist"}

        self.invoices[invoice_id]["status"] = new_status

        return {
            "success": True,
            "data": self.invoices[invoice_id]
        }

    def add_payment(
        self,
        payment_id: str,
        user_id: str,
        invoice_id: str,
        payment_date: str,
        amount: float,
        payment_method: str,
        status: str
    ) -> dict:
        """
        Record a new payment for a user and invoice, ensuring constraints:
          - User must exist and be authenticated.
          - Invoice must exist and belong to the user.
          - Payment amount must be non-negative and not exceed invoice total_amount.
          - Payment ID must not already exist.
          - Payment must reference both entities.

        Args:
            payment_id (str): New unique ID for the payment.
            user_id (str): ID of the user making payment.
            invoice_id (str): ID of the invoice being paid.
            payment_date (str): Payment date.
            amount (float): Payment amount (must be <= invoice total).
            payment_method (str): Payment method descriptor.
            status (str): Payment outcome/status ("success", "failed", etc.)

        Returns:
            dict: {
                "success": True,
                "id": "...",
                "data": {...}
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }
        """
        # Validate payment ID uniqueness
        if payment_id in self.payments:
            return { "success": False, "error": f"Payment ID '{payment_id}' already exists." }

        # Validate user existence and authentication
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": f"User '{user_id}' does not exist." }
        if user.get("authentication_status") != "authenticated":
            return { "success": False, "error": "User is not authenticated." }

        # Validate invoice existence and association with user
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return { "success": False, "error": f"Invoice '{invoice_id}' does not exist." }
        if invoice.get("user_id") != user_id:
            return { "success": False, "error": f"Invoice does not belong to user '{user_id}'." }

        # Validate amount
        if amount < 0.0:
            return { "success": False, "error": "Payment amount must be non-negative." }
        invoice_total = invoice.get("total_amount", 0.0)
        if amount > invoice_total:
            return { "success": False, "error": "Payment amount exceeds invoice total amount." }

        # Create PaymentInfo
        payment_info = {
            "payment_id": payment_id,
            "user_id": user_id,
            "invoice_id": invoice_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_method": payment_method,
            "status": status
        }
        self.payments[payment_id] = payment_info

        return {
            "success": True,
            "id": payment_id,
            "data": payment_info
        }

    def update_payment_status(self, payment_id: str, new_status: str) -> dict:
        """
        Modify the status/outcome of an existing payment record.

        Args:
            payment_id (str): Unique ID of payment to update.
            new_status (str): Desired status ("success", "failed", ...).

        Returns:
            dict: 
              {"success": True, "data": {...}}
              or
              {"success": False, "error": "Payment not found."}

        Constraints:
            - payment_id must exist.
            - No specific status value restrictions (any string accepted).
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found."}

        payment["status"] = new_status
        self.payments[payment_id] = payment
        return {"success": True, "data": payment}

    def add_charge_to_invoice(
        self,
        invoice_id: str,
        charge_id: str,
        description: str,
        amount: float
    ) -> dict:
        """
        Add a new charge line item to the given invoice.

        Args:
            invoice_id (str): The ID of the invoice to add the charge to.
            charge_id (str): The unique ID for this new charge.
            description (str): Description of the charge.
            amount (float): Charge amount (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "id": "...",
                "data": {...}
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - amount must be >= 0.
            - invoice_id must exist.
            - charge_id must be unique.
        """
        # Check invoice existence
        if invoice_id not in self.invoices:
            return { "success": False, "error": "Invoice does not exist." }

        # Check charge_id uniqueness
        if charge_id in self.charges:
            return { "success": False, "error": "Charge ID already exists." }

        # Check non-negative amount
        if amount < 0:
            return { "success": False, "error": "Charge amount must be non-negative." }

        # Add new charge
        new_charge: ChargeInfo = {
            "charge_id": charge_id,
            "invoice_id": invoice_id,
            "description": description,
            "amount": amount
        }
        self.charges[charge_id] = new_charge

        return { "success": True, "id": charge_id, "data": new_charge }

    def update_charge_amount(self, charge_id: str, new_amount: float) -> dict:
        """
        Modify the amount for a specific charge, enforcing:
          - Amount must be non-negative.

        Args:
            charge_id (str): The unique charge identifier to update.
            new_amount (float): The new amount to set for this charge.

        Returns:
            dict: 
                If success: {
                    "success": True,
                    "data": {...}
                }
                If failure: {
                    "success": False,
                    "error": "reason for failure"
                }
        """
        # Check charge existence
        charge = self.charges.get(charge_id)
        if charge is None:
            return { "success": False, "error": "Charge not found." }
    
        # Non-negative constraint
        if new_amount < 0:
            return { "success": False, "error": "Charge amount must be non-negative." }

        # Apply update
        charge["amount"] = new_amount
        self.charges[charge_id] = charge

        return { "success": True, "data": charge }

    def delete_payment(self, payment_id: str) -> dict:
        """
        Remove (delete) a payment record from the portal.

        Args:
            payment_id (str): Unique identifier of the payment to delete.

        Returns:
            dict: {
                "success": True,
                "deleted_id": "..."
            }
            OR
            {
                "success": False,
                "error": "Payment not found."
            }

        Constraints:
            - Only deletes the payment record if it exists.
        """
        if payment_id not in self.payments:
            return { "success": False, "error": "Payment not found." }

        del self.payments[payment_id]
        return { "success": True, "deleted_id": payment_id }

    def delete_charge(self, charge_id: str) -> dict:
        """
        Remove a specific charge from its associated invoice.

        Args:
            charge_id (str): The unique identifier of the charge to be removed.

        Returns:
            dict: {
                "success": True,
                "deleted_id": "..."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The charge must exist in the system.
            - The invoice referenced by the charge must exist.
            - After deletion, invoice's total_amount is updated to sum of remaining charges.
            - Charges must remain non-negative.

        Note: This function does NOT perform authentication/authorization checks.
        """
        # Check charge exists
        if charge_id not in self.charges:
            return { "success": False, "error": "Charge does not exist." }
    
        charge = self.charges[charge_id]
        invoice_id = charge.get("invoice_id")
    
        # Remove the charge
        del self.charges[charge_id]

        # Check invoice exists
        if invoice_id not in self.invoices:
            return { "success": False, "error": "Invoice referenced by charge does not exist." }
    
        # Recalculate invoice total
        total = 0.0
        for c in self.charges.values():
            if c["invoice_id"] == invoice_id:
                if c["amount"] < 0:
                    # Data corruption: charge amount negative
                    return { "success": False, "error": "Charge amount negative -- data corruption." }
                total += c["amount"]
    
        # Update invoice total_amount
        self.invoices[invoice_id]["total_amount"] = total

        return { "success": True, "deleted_id": charge_id }