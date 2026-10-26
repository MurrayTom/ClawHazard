from typing import Dict, TypedDict, Optional
import uuid
from typing import Optional, Dict



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    contact_information: str

class BillInfo(TypedDict):
    bill_id: str
    patient_id: str
    treatment_details: str
    issue_date: str
    amount_due: float
    amount_paid: float
    status: str

class PaymentInfo(TypedDict):
    payment_id: str
    bill_id: str
    date: str
    amount: float
    payment_method: str
    status: str

class DisputeInfo(TypedDict):
    dispute_id: str
    bill_id: str
    patient_id: str
    date_created: str
    description: str
    status: str
    resolution_detail: Optional[str]

class CustomerSupportInteractionInfo(TypedDict):
    interaction_id: str
    patient_id: str
    dispute_id: Optional[str]
    timestamp: str
    support_agent_id: str
    note: str

class HospitalBillingManagementSystem:
    def __init__(self, init_config: dict):
        """
        Hospital billing management system environment.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}
        # Bills: {bill_id: BillInfo}
        self.bills: Dict[str, BillInfo] = {}
        # Payments: {payment_id: PaymentInfo}
        self.payments: Dict[str, PaymentInfo] = {}
        # Disputes: {dispute_id: DisputeInfo}
        self.disputes: Dict[str, DisputeInfo] = {}
        # Customer Support Interactions: {interaction_id: CustomerSupportInteractionInfo}
        self.customer_support_interactions: Dict[str, CustomerSupportInteractionInfo] = {}

        # Constraints:
        # - Each bill must be associated with a single patient.
        # - Each payment must be linked to one bill, and multiple payments per bill are allowed.
        # - Disputes can only be created for valid, existing bills.
        # - The sum of payments for a bill cannot exceed the amount due for that bill.
        # - Dispute records must have an associated status (e.g., open, pending review, resolved).
        # - Customer support interactions must reference a valid patient and, if applicable, a dispute.

        self.init_config = init_config

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient demographic and contact information by patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # Patient demographic and contact info
            }
            or
            {
                "success": False,
                "error": str  # Error message if patient not found
            }

        Constraints:
            - patient_id must exist in the system (self.patients).
        """
        patient_info = self.patients.get(patient_id)
        if patient_info is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient_info }

    def list_patient_bills(self, patient_id: str) -> dict:
        """
        Retrieve all bills associated with a specified patient.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[BillInfo],  # List of all bills linked to the patient (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,  # Reason (e.g. patient not found)
                    }

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        bills_list = [
            bill_info for bill_info in self.bills.values()
            if bill_info["patient_id"] == patient_id
        ]

        return { "success": True, "data": bills_list }

    def get_bill_by_id(self, bill_id: str) -> dict:
        """
        Get details of a specific bill by its bill_id.

        Args:
            bill_id (str): The ID of the bill to retrieve.

        Returns:
            dict: 
                - On success: {"success": True, "data": BillInfo}
                - On failure: {"success": False, "error": "Bill with given ID does not exist"}

        Constraints:
            - The bill_id must exist in the system.
        """
        bill_info = self.bills.get(bill_id)
        if not bill_info:
            return {"success": False, "error": "Bill with given ID does not exist"}
        return {"success": True, "data": bill_info}

    def list_payments_for_bill(self, bill_id: str) -> dict:
        """
        Retrieve all payment records associated with a given bill.

        Args:
            bill_id (str): The unique identifier for the bill.

        Returns:
            dict: {
                "success": True,
                "data": List[PaymentInfo], # List of payments made against the bill (empty if none)
            }
            OR
            {
                "success": False,
                "error": str # Reason for failure, e.g., bill does not exist.
            }

        Constraints:
            - bill_id must refer to an existing bill.
        """
        if bill_id not in self.bills:
            return {"success": False, "error": "Bill does not exist"}

        payments = [
            payment_info for payment_info in self.payments.values()
            if payment_info["bill_id"] == bill_id
        ]

        return {"success": True, "data": payments}

    def get_bill_balance(self, bill_id: str) -> dict:
        """
        Calculate the outstanding balance (amount_due - total amount_paid) for a specified bill.

        Args:
            bill_id (str): The unique identifier of the bill.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "bill_id": str,
                    "amount_due": float,
                    "total_paid": float,
                    "balance": float
                }
            }
            or
            {
                "success": False,
                "error": str  # Bill does not exist
            }

        Constraints:
            - Bill must exist in the system.
            - Sums up all payments linked to the bill.
            - No additional permission checks.
        """
        bill = self.bills.get(bill_id)
        if not bill:
            return { "success": False, "error": "Bill not found" }

        amount_due = bill["amount_due"]
        # Sum all payments associated with the bill_id
        total_paid = sum(
            payment["amount"]
            for payment in self.payments.values()
            if payment["bill_id"] == bill_id
        )
        balance = amount_due - total_paid

        return {
            "success": True,
            "data": {
                "bill_id": bill_id,
                "amount_due": amount_due,
                "total_paid": total_paid,
                "balance": balance
            }
        }

    def list_disputes_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve all disputes initiated by or associated with a given patient.

        Args:
            patient_id (str): The unique identifier for the patient.

        Returns:
            dict:
                success (bool): True if found, False otherwise.
                data (List[DisputeInfo]): List of dispute records for the patient (may be empty if none).
                error (str): If patient does not exist.

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        disputes_for_patient = [
            dispute_info for dispute_info in self.disputes.values()
            if dispute_info["patient_id"] == patient_id
        ]

        return { "success": True, "data": disputes_for_patient }

    def list_disputes_for_bill(self, bill_id: str) -> dict:
        """
        Retrieve all disputes linked to a specific bill.

        Args:
            bill_id (str): The unique identifier of the bill to look up disputes for.

        Returns:
            dict: {
                "success": True,
                "data": List[DisputeInfo]   # List of disputes (may be empty if no disputes found)
            }
            OR
            {
                "success": False,
                "error": str    # Error message if bill does not exist
            }

        Constraints:
            - The bill_id must exist in the system.
        """
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill does not exist" }

        disputes = [
            dispute for dispute in self.disputes.values()
            if dispute["bill_id"] == bill_id
        ]

        return { "success": True, "data": disputes }

    def get_dispute_by_id(self, dispute_id: str) -> dict:
        """
        Retrieve full details for a specific dispute by its ID.

        Args:
            dispute_id (str): The unique identifier of the dispute to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": DisputeInfo  # Full details of the dispute
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. not found
            }

        Constraints:
            - The dispute must exist in the system.
        """
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": "Dispute not found" }

        return { "success": True, "data": dispute }

    def list_customer_support_interactions_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve all customer support interactions associated with the provided patient.

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[CustomerSupportInteractionInfo],  # May be empty
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason patient does not exist
                    }

        Constraints:
            - The patient_id must exist in self.patients (valid patient).
            - Interactions are selected where interaction['patient_id'] == patient_id.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        interactions = [
            interaction for interaction in self.customer_support_interactions.values()
            if interaction['patient_id'] == patient_id
        ]
        return { "success": True, "data": interactions }

    def list_customer_support_interactions_for_dispute(self, dispute_id: str) -> dict:
        """
        Retrieve all customer support interaction records referencing the specified dispute.

        Args:
            dispute_id (str): The unique identifier for the dispute.

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerSupportInteractionInfo]  # May be empty
            }
            or
            {
                "success": False,
                "error": "Dispute does not exist"
            }

        Constraints:
            - The dispute must exist in the system.
            - All returned interactions must reference the specified dispute_id.
        """
        if dispute_id not in self.disputes:
            return {"success": False, "error": "Dispute does not exist"}

        interactions = [
            interaction_info
            for interaction_info in self.customer_support_interactions.values()
            if interaction_info.get("dispute_id") == dispute_id
        ]

        return {"success": True, "data": interactions}

    def create_dispute(self, bill_id: str, patient_id: str, description: str, date_created: str, status: str) -> dict:
        """
        Create a new dispute record for a specified bill and patient, if constraints are satisfied.

        Args:
            bill_id (str): The ID of the bill to dispute.
            patient_id (str): The ID of the patient raising the dispute.
            description (str): Description/details of the dispute.
            date_created (str): Timestamp of dispute creation (ISO8601 or similar).
            status (str): Initial status for the dispute (e.g., 'open', 'pending review', etc.).

        Returns:
            dict: {
                "success": True,
                "id": <str>,
                "data": <dispute record>
            }
            or
            {
                "success": False,
                "error": <str error description>
            }

        Constraints:
            - Disputes can only be created for existing bills.
            - Bill must be associated with the patient raising the dispute.
            - Dispute record must have a non-empty status.
            - Description should not be empty.
        """
        # Bill exists?
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill not found." }

        # Patient exists?
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found." }

        # Bill belongs to patient?
        bill_info = self.bills[bill_id]
        if bill_info["patient_id"] != patient_id:
            return { "success": False, "error": "Bill does not belong to patient." }

        # Check status validity (not empty)
        if not status or not isinstance(status, str) or status.strip() == "":
            return { "success": False, "error": "Dispute status is required." }

        # Description validity
        if not description or not isinstance(description, str) or description.strip() == "":
            return { "success": False, "error": "Dispute description is required." }

        # Generate unique dispute_id
        base_id = f"D{len(self.disputes)+1}"
        i = 1
        dispute_id = base_id
        while dispute_id in self.disputes:
            dispute_id = f"{base_id}_{i}"
            i += 1

        # Create dispute record
        dispute_info: DisputeInfo = {
            "dispute_id": dispute_id,
            "bill_id": bill_id,
            "patient_id": patient_id,
            "date_created": date_created,
            "description": description,
            "status": status,
            "resolution_detail": None
        }
        self.disputes[dispute_id] = dispute_info

        return {
            "success": True,
            "id": dispute_id,
            "data": dispute_info
        }

    def update_dispute_status(self, dispute_id: str, new_status: str) -> dict:
        """
        Change the status of an existing dispute.

        Args:
            dispute_id (str): The dispute's unique identifier.
            new_status (str): The new status to apply (e.g., 'open', 'pending review', 'resolved').

        Returns:
            dict: {
                "success": True,
                "data": <updated dispute record>
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - dispute_id must exist in the disputes registry.
            - new_status must be a non-empty string.
            - Optionally, new_status should be one of allowed values ('open', 'pending review', 'resolved').
        """
        if dispute_id not in self.disputes:
            return { "success": False, "error": "Dispute not found." }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid new status." }

        # Optionally, enforce allowed statuses. Add here if needed:
        allowed_statuses = {"open", "pending review", "resolved"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Status '{new_status}' is not allowed." }

        self.disputes[dispute_id]["status"] = new_status
        return { "success": True, "data": self.disputes[dispute_id] }

    def add_dispute_resolution_detail(self, dispute_id: str, resolution_detail: str) -> dict:
        """
        Record (add or update) a resolution detail for a dispute once it is resolved.

        Args:
            dispute_id (str): The ID of the dispute to update.
            resolution_detail (str): The detail/text regarding the dispute's resolution.

        Returns:
            dict: {
                "success": True,
                "id": <dispute_id>,
                "data": <updated dispute record>
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (dispute not found, not resolved, etc.)
            }

        Constraints:
            - Dispute must exist.
            - Dispute status must be "resolved".
            - The resolution detail is saved to the dispute record.
        """
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": "Dispute does not exist." }
        if dispute["status"].lower() != "resolved":
            return { "success": False, "error": "Cannot add resolution detail unless dispute is resolved." }
        dispute["resolution_detail"] = resolution_detail
        return { "success": True, "id": dispute_id, "data": dispute }

    def log_customer_support_interaction(self, patient_id: str, support_agent_id: str, note: str, timestamp: str, dispute_id: Optional[str] = None) -> dict:
        """
        Record a new customer support interaction associated with a patient and optionally a dispute.

        Args:
            patient_id (str): The ID of the patient involved.
            support_agent_id (str): The staff agent recording the interaction.
            note (str): Notes or details for the interaction.
            timestamp (str): When the interaction occurred (ISO/datetime string).
            dispute_id (Optional[str]): If applicable, the dispute ID to associate.

        Returns:
            dict: {
                "success": True,
                "id": <interaction_id>,
                "timestamp": <timestamp>
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - patient_id must exist.
            - If dispute_id is provided, it must exist.
            - The new interaction will get a unique interaction_id.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist." }

        if dispute_id is not None and dispute_id not in self.disputes:
            return { "success": False, "error": "Dispute does not exist." }

        # Generate a unique interaction_id
        interaction_id = str(uuid.uuid4())

        interaction: CustomerSupportInteractionInfo = {
            "interaction_id": interaction_id,
            "patient_id": patient_id,
            "dispute_id": dispute_id,
            "timestamp": timestamp,
            "support_agent_id": support_agent_id,
            "note": note
        }

        self.customer_support_interactions[interaction_id] = interaction

        return {
            "success": True,
            "id": interaction_id,
            "timestamp": timestamp
        }

    def add_payment_to_bill(self, bill_id: str, payment_id: str, date: str, amount: float, payment_method: str, status: str) -> dict:
        """
        Register a new payment to a bill, ensuring the total paid does not exceed amount_due.

        Args:
            bill_id (str): The ID of the bill to add payment to.
            payment_id (str): The new payment's unique ID.
            date (str): Date of payment.
            amount (float): Amount of payment; must be positive.
            payment_method (str): Method of payment (e.g., cash, card).
            status (str): Status for this payment.

        Returns:
            dict:
                On success:
                    { "success": True, "id": <payment_id>, "data": <payment record> }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Bill must exist.
            - Payment ID must be unique (not already used).
            - The sum of bill.amount_paid + amount <= bill.amount_due.
            - amount must be positive.
        """

        if bill_id not in self.bills:
            return { "success": False, "error": "Bill ID does not exist" }

        if payment_id in self.payments:
            return { "success": False, "error": "Payment ID already exists" }

        if amount <= 0:
            return { "success": False, "error": "Payment amount must be positive" }

        bill = self.bills[bill_id]
        # Calculate current total paid (from amount_paid field)
        total_paid = bill.get("amount_paid", 0.0)
        amount_due = bill.get("amount_due", 0.0)

        if total_paid + amount > amount_due + 1e-6:  # Adding small epsilon for float safety
            return {
                "success": False,
                "error": f"Payment would exceed amount due. Amount due: {amount_due}, total paid: {total_paid}, attempted payment: {amount}"
            }

        # Create PaymentInfo
        payment_info = {
            "payment_id": payment_id,
            "bill_id": bill_id,
            "date": date,
            "amount": amount,
            "payment_method": payment_method,
            "status": status
        }
        self.payments[payment_id] = payment_info

        # Update bill's amount_paid
        bill["amount_paid"] = total_paid + amount
        self.bills[bill_id] = bill  # Redundant, but explicit update

        return {
            "success": True,
            "id": payment_id,
            "data": payment_info
        }

    def update_bill_status(self, bill_id: str, new_status: str) -> dict:
        """
        Updates the financial or workflow status of a bill, such as to 'paid', 'overdue', or 'disputed'.

        Args:
            bill_id (str): The unique identifier for the bill to update.
            new_status (str): The new desired status string for the bill.

        Returns:
            dict:
                On success:
                    { "success": True, "data": <updated bill record> }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - The bill with bill_id must exist.
            - new_status should be a non-empty string.
        """
        if bill_id not in self.bills:
            return { "success": False, "error": "Bill does not exist." }
        if not isinstance(new_status, str) or new_status.strip() == "":
            return { "success": False, "error": "New status is empty or invalid." }

        self.bills[bill_id]["status"] = new_status.strip()
        return { "success": True, "data": self.bills[bill_id] }

    def modify_bill_details(self, bill_id: str, treatment_details: Optional[str] = None, issue_date: Optional[str] = None, amount_due: Optional[float] = None, status: Optional[str] = None) -> dict:
        """
        Edit bill-level details for a given bill (admin operation).

        Args:
            bill_id (str): Unique identifier for the bill to modify.
            treatment_details (Optional[str]): New treatment details (if updating).
            issue_date (Optional[str]): New issue date (if updating).
            amount_due (Optional[float]): New billed amount (if updating).
            status (Optional[str]): New billing status (if updating).

        Returns:
            dict: {
                "success": True,
                "data": <updated bill record>
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - bill_id must exist.
            - amount_due cannot be set below the total paid.
            - amount_due must not be negative.
            - patient_id and amount_paid cannot be directly modified.
        """
        bill = self.bills.get(bill_id)
        if not bill:
            return { "success": False, "error": "Bill does not exist." }

        # Validate amount_due
        if amount_due is not None:
            if amount_due < 0:
                return { "success": False, "error": "amount_due cannot be negative." }
            total_paid = bill.get("amount_paid", 0.0)
            if total_paid > amount_due:
                return { 
                    "success": False,
                    "error": (
                        f"Cannot set amount_due below total paid ({total_paid:.2f})."
                    )
                }
            bill["amount_due"] = amount_due

        if treatment_details is not None:
            bill["treatment_details"] = treatment_details

        if issue_date is not None:
            bill["issue_date"] = issue_date

        if status is not None:
            bill["status"] = status

        return { "success": True, "data": bill }

    def update_patient_contact_information(self, patient_id: str, new_contact_information: str) -> dict:
        """
        Change or correct a patient's contact details.

        Args:
            patient_id (str): The unique identifier of the patient whose contact info is to be updated.
            new_contact_information (str): The new contact details to assign.

        Returns:
            dict:
                On success:
                    { "success": True, "data": <updated patient record> }
                On failure (patient not found):
                    { "success": False, "error": "Patient not found" }

        Constraints:
            - The patient_id must refer to an existing patient.
            - Contact info is updated directly; no format/content validation enforced.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        patient["contact_information"] = new_contact_information
        return { "success": True, "data": patient }