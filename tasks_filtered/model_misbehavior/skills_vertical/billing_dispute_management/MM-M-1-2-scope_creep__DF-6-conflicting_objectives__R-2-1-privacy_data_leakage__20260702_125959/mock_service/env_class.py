from typing import Dict, TypedDict
from typing import Optional
from datetime import datetime
import time
import uuid
import datetime



class BillingItemInfo(TypedDict):
    billing_item_id: str
    amount: float
    description: str
    billing_date: str

class DisputeInfo(TypedDict):
    dispute_id: str
    billing_item_id: str
    dispute_reason: str
    submitter_id: str
    submit_date: str
    resolution_status: str
    resolution_details: str
    resolver_id: str
    resolution_date: str

class OperatorInfo(TypedDict):
    operator_id: str
    name: str
    role: str

class BillingDisputeManagementSystem:
    def __init__(self, init_config: dict):
        # Billing items: {billing_item_id: BillingItemInfo}
        self.billing_items: Dict[str, BillingItemInfo] = {}
        # Disputes: {dispute_id: DisputeInfo}
        self.disputes: Dict[str, DisputeInfo] = {}
        # Operators: {operator_id: OperatorInfo}
        self.operators: Dict[str, OperatorInfo] = {}

        # Constraints:
        # - A dispute must be linked to a valid billing item.
        # - Resolution status can only be updated by authorized operators.
        # - Resolution status values must be from an allowed set (e.g., "accepted", "rejected", "pending", etc.).
        # - Each resolution action must be timestamped and record the responsible operator.

        self.init_config = init_config

    def get_billing_item_by_id(self, billing_item_id: str) -> dict:
        """
        Retrieve a billing item's details using its unique billing_item_id.

        Args:
            billing_item_id (str): The unique identifier for the billing item.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": BillingItemInfo
                }
                - On failure: {
                    "success": False,
                    "error": "Billing item not found"
                }
        Constraints:
            - billing_item_id must exist within the system.
        """
        if not isinstance(billing_item_id, str) or not billing_item_id:
            return { "success": False, "error": "Invalid billing_item_id" }

        item = self.billing_items.get(billing_item_id)
        if item is None:
            return { "success": False, "error": "Billing item not found" }
    
        return { "success": True, "data": item }

    def get_dispute_by_billing_item_id(self, billing_item_id: str) -> dict:
        """
        Find the dispute(s) associated with a specific billing_item_id.

        Args:
            billing_item_id (str): The identifier of the billing item to look up disputes for.

        Returns:
            dict: {
                "success": True,
                "data": List[DisputeInfo]  # May be empty if no disputes found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - billing_item_id must exist in the system.
            - Returns all disputes linked to this billing item.
        """
        if billing_item_id not in self.billing_items:
            return { "success": False, "error": "Billing item does not exist" }
    
        disputes = [
            dispute_info for dispute_info in self.disputes.values()
            if dispute_info["billing_item_id"] == billing_item_id
        ]
        return { "success": True, "data": disputes }

    def get_dispute_by_id(self, dispute_id: str) -> dict:
        """
        Retrieve detailed information for the specified dispute_id.

        Args:
            dispute_id (str): Unique identifier of the dispute.

        Returns:
            dict:
                - {"success": True, "data": DisputeInfo} if found
                - {"success": False, "error": str} if not found

        Constraints:
            - dispute_id must exist in the system
        """
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": "Dispute not found" }
        return { "success": True, "data": dispute }

    def list_disputes_by_status(self, resolution_status: str) -> dict:
        """
        List all disputes matching a particular resolution status.

        Args:
            resolution_status (str): The desired resolution status to filter disputes by.

        Returns:
            dict: {
                "success": True,
                "data": List[DisputeInfo],  # List of disputes with the matching resolution_status
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., invalid resolution status
            }

        Constraints:
            - resolution_status must be in the allowed set (e.g., "accepted", "rejected", "pending", etc.)
            - Returns empty list if no disputes match.
        """
        # Get allowed resolution status values from the canonical source
        allowed_result = self.get_allowed_resolution_status_values()
        allowed_status = set(allowed_result["data"])

        if not isinstance(resolution_status, str) or resolution_status not in allowed_status:
            return {
                "success": False,
                "error": f"Invalid resolution status '{resolution_status}'. Allowed values: {sorted(allowed_status)}"
            }

        matches = [
            dispute_info
            for dispute_info in self.disputes.values()
            if dispute_info.get("resolution_status") == resolution_status
        ]

        return {
            "success": True,
            "data": matches
        }

    def get_allowed_resolution_status_values(self) -> dict:
        """
        Query the set of permitted values for dispute resolution_status.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # e.g., ["accepted", "rejected", "pending", ...]
            }
        """
        # Hardcoded, system-wide constant; would be maintained centrally in practice.
        allowed_statuses = ["accepted", "rejected", "pending", "under_review", "escalated", "resolved"]

        return { "success": True, "data": allowed_statuses }

    def get_operator_by_id(self, operator_id: str) -> dict:
        """
        Retrieve operator information by operator_id.

        Args:
            operator_id (str): The unique identifier of the operator.

        Returns:
            dict: {
                "success": True,
                "data": OperatorInfo  # Operator's info dictionary
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., operator not found
            }

        Constraints:
            - operator_id must exist in the system.
        """
        operator = self.operators.get(operator_id)
        if operator is None:
            return { "success": False, "error": "Operator not found" }
        return { "success": True, "data": operator }

    def get_operator_by_name(self, name: str) -> dict:
        """
        Find operator(s) details by their name.

        Args:
            name (str): The name of the operator to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[OperatorInfo],  # List of matching operator info dicts (may be empty)
            }

        Notes/Constraints:
            - Name matching is case sensitive and exact.
            - Multiple operators with the same name are supported (all will be returned).
        """
        result = [
            operator_info for operator_info in self.operators.values()
            if operator_info["name"] == name
        ]

        return { "success": True, "data": result }

    def get_dispute_resolution_history(self, dispute_id: str) -> dict:
        """
        Retrieve the resolution status change history and related actions for the specified dispute.

        Args:
            dispute_id (str): The ID of the dispute to lookup.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[dict],  # Each dict contains resolution_status, resolution_details, resolver_id, resolution_date
                  }
                - On error: {
                    "success": False,
                    "error": str  # Reason for failure (e.g., dispute not found, no history available)
                  }

        Constraints:
            - The dispute must exist in the system.
            - Resolution history may or may not be tracked. If not tracked, return empty list or an appropriate message.
        """

        # Check if dispute exists
        if dispute_id not in self.disputes:
            return { "success": False, "error": "Dispute does not exist" }

        # Check if resolution history tracking is present
        # We'll assume it is stored as: self.dispute_resolution_history: Dict[str, List[dict]]
        resolution_history = getattr(self, "dispute_resolution_history", None)
        if resolution_history is None or dispute_id not in resolution_history:
            # If not tracked, fall back to showing only current (latest) action
            latest = self.disputes[dispute_id]
            latest_entry = {
                "resolution_status": latest.get("resolution_status"),
                "resolution_details": latest.get("resolution_details"),
                "resolver_id": latest.get("resolver_id"),
                "resolution_date": latest.get("resolution_date"),
            }
            return {
                "success": True,
                "data": [latest_entry] if latest_entry["resolution_status"] is not None else []
            }

        # History is tracked
        return {
            "success": True,
            "data": resolution_history[dispute_id]
        }

    def validate_dispute_billing_item_relation(self, dispute_id: str) -> dict:
        """
        Check that a dispute is linked to a valid billing item.

        Args:
            dispute_id (str): The unique identifier for the dispute to validate.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "dispute_id": str,
                    "billing_item_id": str,
                    "linked": bool
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The dispute must exist.
            - The dispute's billing_item_id must exist in billing items.
        """
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": "Dispute not found" }

        billing_item_id = dispute["billing_item_id"]
        if billing_item_id in self.billing_items:
            return {
                "success": True,
                "data": {
                    "dispute_id": dispute_id,
                    "billing_item_id": billing_item_id,
                    "linked": True
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "dispute_id": dispute_id,
                    "billing_item_id": billing_item_id,
                    "linked": False
                }
            }


    def resolve_dispute(
        self,
        dispute_id: str,
        resolution_status: str,
        resolution_details: str,
        resolver_id: str
    ) -> dict:
        """
        Update a dispute's resolution_status, set resolution_details, record resolver_id and timestamp.

        Args:
            dispute_id (str): The unique ID of the dispute to resolve.
            resolution_status (str): The new status for the dispute (must be allowed).
            resolution_details (str): Details of the resolution decision.
            resolver_id (str): The operator ID who is performing the resolution.

        Returns:
            dict:
                success: True/False
                message: On success, brief description.
                error: On failure, reason for failure.

        Constraints:
            - Dispute must exist.
            - Operator must exist and be authorized (role != "viewer"/"guest").
            - Resolution_status must be from allowed set.
            - Must record the operator (resolver_id) and current timestamp in 'resolution_date'.
        """
        # Validate dispute
        dispute: Optional[DisputeInfo] = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": f"Dispute '{dispute_id}' does not exist." }

        # Validate operator
        operator: Optional[OperatorInfo] = self.operators.get(resolver_id)
        if not operator:
            return { "success": False, "error": f"Operator '{resolver_id}' does not exist." }
        if operator.get("role", "").lower() in ("viewer", "guest"):
            return { "success": False, "error": f"Operator '{resolver_id}' is not authorized to resolve disputes." }

        # Validate allowed status
        allowed_result = self.get_allowed_resolution_status_values()
        allowed_status = allowed_result["data"]

        if resolution_status not in allowed_status:
            return {
                "success": False,
                "error": f"Resolution status '{resolution_status}' is not allowed. Allowed values: {allowed_status}"
            }

        # Update dispute record
        dispute["resolution_status"] = resolution_status
        dispute["resolution_details"] = resolution_details
        dispute["resolver_id"] = resolver_id
        dispute["resolution_date"] = datetime.datetime.utcnow().isoformat()

        # (Persist if required -- here it's in-memory)
        self.disputes[dispute_id] = dispute

        return {
            "success": True,
            "status": resolution_status,
            "message": f"Dispute '{dispute_id}' resolved to status '{resolution_status}' by operator '{resolver_id}'."
        }


    def update_dispute_resolution_status(self, dispute_id: str, new_status: str, operator_id: str) -> dict:
        """
        Change the resolution_status value of a dispute after verifying:
        - Dispute exists and is linked to a valid billing item.
        - Operator exists and is authorized to update dispute statuses.
        - The new resolution_status is within the allowed status values.
        Automatically updates resolver_id and resolution_date with the operator and current timestamp.

        Args:
            dispute_id (str): The dispute to update.
            new_status (str): The status to assign (must be allowed).
            operator_id (str): The operator making the change.

        Returns:
            dict:
                { "success": True, "data": {...} }
                or
                { "success": False, "error": str }
        """
        # Check dispute exists
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return { "success": False, "error": "Dispute not found." }

        # Check dispute is linked to a valid billing item
        if dispute["billing_item_id"] not in self.billing_items:
            return { "success": False, "error": "Dispute is not linked to a valid billing item." }

        # Check operator exists
        operator = self.operators.get(operator_id)
        if not operator:
            return { "success": False, "error": "Operator not found." }

        # Check operator is authorized (assuming role 'resolver' is required)
        if operator.get("role", "").lower() not in ("resolver", "admin"):
            return { "success": False, "error": "Operator not authorized to update resolution status." }

        # Check new_status is allowed
        allowed_result = self.get_allowed_resolution_status_values()
        allowed_status_values = allowed_result["data"]
        if new_status not in allowed_status_values:
            return { "success": False, "error": f"Resolution status '{new_status}' is not allowed." }

        # Update dispute resolution status, timestamp, and resolver
        dispute["resolution_status"] = new_status
        dispute["resolver_id"] = operator_id
        dispute["resolution_date"] = str(time.time())  # Unix timestamp as a string

        # Persist change (if needed for actual DB)

        return { "success": True, "data": dispute }

    def add_dispute_resolution_details(self, dispute_id: str, resolution_details: str) -> dict:
        """
        Attach or update the resolution_details text field in the given dispute record.

        Args:
            dispute_id (str): Unique dispute identifier.
            resolution_details (str): Text to be attached or set as resolution details.

        Returns:
            dict: {
                "success": True,
                "id": dispute_id,
                "data": DisputeInfo
            }
            or
            {
                "success": False,
                "error": "Dispute does not exist"
            }

        Constraints:
            - The dispute record must exist.
            - Only the resolution_details field is modified (no change to status/timestamps/resolver).
        """
        if dispute_id not in self.disputes:
            return { "success": False, "error": "Dispute does not exist" }
    
        self.disputes[dispute_id]["resolution_details"] = resolution_details
        return {
            "success": True,
            "id": dispute_id,
            "data": self.disputes[dispute_id]
        }


    def add_dispute(
        self,
        billing_item_id: str,
        dispute_reason: str,
        submitter_id: str,
        submit_date: str = None
    ) -> dict:
        """
        Create a new dispute linked to a billing item.

        Args:
            billing_item_id (str): The billing item to dispute (must exist).
            dispute_reason (str): Reason for the dispute (non-empty).
            submitter_id (str): The user/customer submitting the dispute (non-empty).
            submit_date (str, optional): Submission timestamp, ISO format; if None, uses current time.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "id": <new_id>,
                    "data": DisputeInfo
                }
                Failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Billing item must exist.
            - Dispute reason and submitter ID must be provided.
            - Dispute ID is auto-generated and unique.
            - Resolution status initialized to 'pending', details blank, no resolver/date.
        """
        # Validate input
        if not billing_item_id or billing_item_id not in self.billing_items:
            return { "success": False, "error": "Invalid or non-existent billing_item_id" }
        if not dispute_reason or dispute_reason.strip() == "":
            return { "success": False, "error": "Dispute reason is required" }
        if not submitter_id or submitter_id.strip() == "":
            return { "success": False, "error": "Submitter ID is required" }
    
        # Generate unique dispute_id
        dispute_id = str(uuid.uuid4())
        while dispute_id in self.disputes:
            dispute_id = str(uuid.uuid4())

        # Timestamp
        if not submit_date:
            submit_date = datetime.datetime.utcnow().isoformat()

        # Create dispute record
        dispute_info = {
            "dispute_id": dispute_id,
            "billing_item_id": billing_item_id,
            "dispute_reason": dispute_reason,
            "submitter_id": submitter_id,
            "submit_date": submit_date,
            "resolution_status": "pending",
            "resolution_details": "",
            "resolver_id": "",
            "resolution_date": ""
        }
        self.disputes[dispute_id] = dispute_info

        return {
            "success": True,
            "id": dispute_id,
            "data": dispute_info
        }

    def delete_dispute(self, dispute_id: str) -> dict:
        """
        Remove (delete) or archive a dispute record corresponding to the provided dispute ID.

        Args:
            dispute_id (str): The unique identifier of the dispute to remove.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "deleted_id": dispute_id
                }
                On failure:
                {
                    "success": False,
                    "error": "Dispute does not exist."
                }

        Constraints:
            - The dispute must exist in the system.
        """
        if dispute_id not in self.disputes:
            return { "success": False, "error": "Dispute does not exist." }
    
        del self.disputes[dispute_id]
        return { "success": True, "deleted_id": dispute_id }

    def assign_dispute_resolver(self, dispute_id: str, operator_id: str) -> dict:
        """
        Set or update the responsible operator (resolver_id) for the specified dispute.

        Args:
            dispute_id (str): The unique identifier of the dispute.
            operator_id (str): The unique identifier of the operator to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "id": dispute_id,
                        "data": DisputeInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - The dispute_id must exist in self.disputes.
            - The operator_id must exist in self.operators.
            - Only sets or updates resolver_id; does not change resolution status/timestamps.
        """
        if dispute_id not in self.disputes:
            return { "success": False, "error": f"Dispute with id '{dispute_id}' does not exist." }
        if operator_id not in self.operators:
            return { "success": False, "error": f"Operator with id '{operator_id}' does not exist." }
    
        self.disputes[dispute_id]["resolver_id"] = operator_id
        return { "success": True, "id": dispute_id, "data": self.disputes[dispute_id] }

    def timestamp_dispute_resolution(self, dispute_id: str, resolution_date: str) -> dict:
        """
        Record or update the resolution_date field of a dispute when its resolution status changes.

        Args:
            dispute_id (str): The unique identifier of the dispute to update.
            resolution_date (str): The timestamp to record (expected ISO8601 string or similar).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": DisputeInfo
                }
            Or on failure:
                {
                    "success": False,
                    "error": "Dispute not found."
                }

        Constraints:
            - The dispute specified by dispute_id must exist.
            - Only the resolution_date field is updated in this operation.
        """
        dispute = self.disputes.get(dispute_id)
        if dispute is None:
            return { "success": False, "error": "Dispute not found." }

        dispute["resolution_date"] = resolution_date
        return { "success": True, "data": dispute }