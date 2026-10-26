from typing import Dict, TypedDict, Optional
import datetime
import uuid



# State Space Mappings
class EquipmentInfo(TypedDict):
    equipment_id: str      # Unique identifier for equipment (from 'quipment_id')
    type: str              # e.g. wheelchair, monitor
    model: str             # e.g. brand/model
    condition: str         # e.g. 'good', 'damaged'
    location: str          # current location in facility
    availability_status: str   # e.g. 'available', 'loaned'

class UserInfo(TypedDict):
    user_id: str          # Unique identifier for user (from '_id')
    name: str
    contact_info: str     # e.g. phone or email
    user_type: str        # e.g. 'patient', 'staff'

class LoanTransactionInfo(TypedDict):
    loan_id: str
    equipment_id: str
    user_id: str
    borrowed_date: str
    due_date: str
    returned_date: Optional[str]
    status: str           # e.g. 'active', 'returned', 'overdue'

class MedicalEquipmentLoanManagementSystem:
    def __init__(self, init_config: dict):
        # Equipment Inventory: equipment_id -> EquipmentInfo
        self.equipment: Dict[str, EquipmentInfo] = {}

        # User Profiles: user_id -> UserInfo
        self.users: Dict[str, UserInfo] = {}

        # Loan Transactions: loan_id -> LoanTransactionInfo
        self.loans: Dict[str, LoanTransactionInfo] = {}

        # Constraints:
        # - Equipment can only have one active loan at a time (must be available to be borrowed)
        # - Loan periods may be limited; overdue items can trigger alerts
        # - On return, equipment condition and location should be verified and updated
        # - Users must be registered to borrow equipment

        self.init_config = init_config

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by their name.

        Args:
            name (str): The name of the user to look up.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[UserInfo],  # List of user info dicts for users whose name matches
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "No user found with that name"
                    }

        Constraints:
            - User must be registered in the system.
            - Multiple users may share the same name; all matching entries are returned.
        """
        matched_users = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        if not matched_users:
            return { "success": False, "error": "No user found with that name" }
        return { "success": True, "data": matched_users }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Get user information based on the provided user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo # If user found
            }
            or
            {
                "success": False,
                "error": str # Reason for failure, e.g., user not found
            }

        Constraints:
            - The user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user_info }

    def list_active_loans_by_user(self, user_id: str) -> dict:
        """
        Get currently active loan transactions for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[LoanTransactionInfo],  # May be empty if no active loans
            }
            or
            {
                "success": False,
                "error": str  # Reason message, e.g. user is not registered
            }

        Constraints:
            - User must be registered (exist in self.users)
            - Only loans with status 'active' are returned
        """
        if user_id not in self.users:
            return { "success": False, "error": "User is not registered" }
    
        active_loans = [
            loan for loan in self.loans.values()
            if loan["user_id"] == user_id and loan["status"] == "active"
        ]

        return { "success": True, "data": active_loans }

    def get_loan_details(self, loan_id: str) -> dict:
        """
        Retrieve all details for a specific loan transaction.

        Args:
            loan_id (str): The unique identifier of the loan transaction.

        Returns:
            dict: {
                "success": True,
                "data": LoanTransactionInfo  # All fields of the loan transaction
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. loan transaction not found
            }

        Constraints:
            - loan_id must exist in the system.
        """
        loan = self.loans.get(loan_id)
        if loan is None:
            return { "success": False, "error": "Loan transaction not found" }

        return { "success": True, "data": loan }

    def get_equipment_by_id(self, equipment_id: str) -> dict:
        """
        Retrieve info about a specific equipment item using its unique ID.

        Args:
            equipment_id (str): Unique identifier for the equipment.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": EquipmentInfo  # Metadata about equipment
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason equipment wasn't found
                }

        Constraints:
            - Equipment ID must exist in inventory.
        """
        info = self.equipment.get(equipment_id)
        if info is None:
            return { "success": False, "error": "Equipment with the specified ID does not exist." }
        return { "success": True, "data": info }

    def list_equipment_by_type(self, equipment_type: str) -> dict:
        """
        List all equipment items of the specified type.

        Args:
            equipment_type (str): The type of equipment to list (e.g., 'wheelchair', 'monitor').

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[EquipmentInfo],  # List of all equipment matching the type (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of error if input is invalid
                }

        Constraints:
            - equipment_type must be a non-empty string.
            - Returns all items matching type. If none exist, returns empty list with success.
        """
        if not equipment_type or not isinstance(equipment_type, str) or equipment_type.strip() == "":
            return {"success": False, "error": "Equipment type must be a non-empty string."}

        result = [
            equipment_info for equipment_info in self.equipment.values()
            if equipment_info.get("type") == equipment_type
        ]
        return {"success": True, "data": result}

    def get_equipment_by_status(self, status: str) -> dict:
        """
        List equipment items filtered by their availability status.
    
        Args:
            status (str): The target 'availability_status' to filter equipment by (e.g., 'available', 'loaned').
    
        Returns:
            dict: {
                "success": True,
                "data": List[EquipmentInfo]  # List of equipment records with the given status (may be empty if none match)
            }
            or
            {
                "success": False,
                "error": str  # Description of input error
            }
    
        Constraints:
            - 'status' must be a non-empty string.
        """
        if not isinstance(status, str) or not status.strip():
            return { "success": False, "error": "Invalid equipment status: must be a non-empty string." }
    
        filtered_equipment = [
            info for info in self.equipment.values()
            if info.get("availability_status") == status
        ]

        return { "success": True, "data": filtered_equipment }

    def get_equipment_condition_and_location(self, equipment_id: str) -> dict:
        """
        Query the current condition and location of a specific medical equipment item.

        Args:
            equipment_id (str): Unique identifier of the equipment.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "condition": str,
                    "location": str
                }
            }
            or
            {
                "success": False,
                "error": "Equipment not found"
            }

        Constraints:
            - The equipment_id must exist in the system's inventory.
        """
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return { "success": False, "error": "Equipment not found" }

        result = {
            "condition": equipment["condition"],
            "location": equipment["location"]
        }
        return { "success": True, "data": result }

    def check_loan_status(self, loan_id: str) -> dict:
        """
        Query the current status (active, returned, overdue) of a loan transaction.

        Args:
            loan_id (str): The unique identifier of the loan transaction.

        Returns:
            dict: {
                "success": True,
                "data": str  # One of 'active', 'returned', 'overdue'
            }
            or
            {
                "success": False,
                "error": str  # Reason such as "Loan transaction not found"
            }

        Constraints:
            - The loan_id must exist in the system.
        """
        loan_info = self.loans.get(loan_id)
        if loan_info is None:
            return { "success": False, "error": "Loan transaction not found" }
        return { "success": True, "data": loan_info["status"] }

    def check_user_registration(self, user_id: str) -> dict:
        """
        Verify if a user is registered and eligible to borrow/return equipment.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # Information about the user
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., not registered)
            }

        Constraints:
            - The user must exist in the system (self.users).
            - All registered users are considered eligible.
        """
        if not user_id or not isinstance(user_id, str):
            return { "success": False, "error": "Invalid user_id input" }

        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User is not registered" }

        return { "success": True, "data": user_info }

    def is_equipment_on_active_loan(self, equipment_id: str) -> dict:
        """
        Check whether a given equipment item (by equipment_id) is currently on active loan.

        Args:
            equipment_id (str): Unique identifier for the equipment.

        Returns:
            dict: {
                "success": True,
                "data": bool   # True if on active loan, False otherwise
            }
            or
            {
                "success": False,
                "error": str   # Reason for failure, e.g., equipment not found
            }

        Constraints:
            - Equipment must exist in system.
        """
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment not found" }

        for loan in self.loans.values():
            if loan["equipment_id"] == equipment_id and loan["status"] == "active":
                return { "success": True, "data": True }

        return { "success": True, "data": False }


    def check_if_loan_is_overdue(self, loan_id: str) -> dict:
        """
        Determine if a loan transaction is overdue based on due_date and current date.

        Args:
            loan_id (str): The unique identifier for the loan transaction.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True if overdue, False if not
            }
            or
            {
                "success": False,
                "error": str   # Reason for failure (e.g., loan not found or date parsing error)
            }

        Constraints:
            - If the loan is already returned, it cannot be overdue.
            - Dates must be in 'YYYY-MM-DD' format.
        """
        loan = self.loans.get(loan_id)
        if loan is None:
            return { "success": False, "error": "Loan not found" }

        if loan.get("returned_date"):
            # Already returned
            return { "success": True, "data": False }

        due_date_str = loan.get("due_date")
        try:
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            today = datetime.datetime.today().date()
        except Exception:
            return { "success": False, "error": "Invalid due_date format" }

        overdue = today > due_date
        return { "success": True, "data": overdue }

    def mark_loan_as_returned(self, loan_id: str) -> dict:
        """
        Mark a loan transaction as returned, update returned_date, and release equipment.

        Args:
            loan_id (str): The identifier of the loan transaction.

        Returns:
            dict: {
                "success": True,
                "message": "Loan marked as returned and equipment released."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - loan_id must exist
            - Loan status must be 'active' or 'overdue'
            - Associated equipment must exist
            - Equipment will be set to 'available'
            - Loan returned_date is set to now in ISO format
        """

        # Check loan existence
        loan = self.loans.get(loan_id)
        if loan is None:
            return {"success": False, "error": "Loan transaction not found."}

        # Only active or overdue loans can be returned
        if loan["status"] not in ("active", "overdue"):
            return {"success": False, "error": f"Loan status is '{loan['status']}', not eligible for return."}

        equipment_id = loan["equipment_id"]
        equipment = self.equipment.get(equipment_id)
        if equipment is None:
            return {"success": False, "error": "Associated equipment not found."}

        # Update loan info
        current_time = datetime.datetime.now().isoformat()
        loan["returned_date"] = current_time
        loan["status"] = "returned"

        # Release equipment (set availability)
        equipment["availability_status"] = "available"

        # Write back changes
        self.loans[loan_id] = loan
        self.equipment[equipment_id] = equipment

        return {"success": True, "message": "Loan marked as returned and equipment released."}

    def update_equipment_availability(self, equipment_id: str, new_status: str) -> dict:
        """
        Change the availability status of a piece of equipment.
        Only allows transitions between 'available' and 'loaned'.

        Args:
            equipment_id (str): Unique identifier of equipment to update.
            new_status (str): 'available' or 'loaned'

        Returns:
            dict: 
                { "success": True, "message": "Equipment availability updated." }
                or
                { "success": False, "error": "Reason for failure." }

        Constraints:
            - Equipment must exist in inventory.
            - Only status transitions between 'available' and 'loaned' are allowed.
            - To loan equipment, must be currently 'available' (enforces one active loan).
            - To make equipment 'available', must be currently 'loaned'.
        """

        # Check equipment exists
        if equipment_id not in self.equipment:
            return { "success": False, "error": "Equipment not found." }

        allowed_statuses = {"available", "loaned"}
        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status. Must be 'available' or 'loaned'." }

        curr_status = self.equipment[equipment_id]["availability_status"]

        # Enforce allowed transitions
        if new_status == "loaned":
            if curr_status != "available":
                return { "success": False, "error": f"Cannot set to 'loaned'; current status is '{curr_status}'." }
        elif new_status == "available":
            if curr_status != "loaned":
                return { "success": False, "error": f"Cannot set to 'available'; current status is '{curr_status}'." }

        # Update status
        self.equipment[equipment_id]["availability_status"] = new_status

        return { "success": True, "message": f"Equipment availability updated to '{new_status}'." }

    def update_equipment_condition_and_location(
        self, 
        equipment_id: str, 
        condition: Optional[str] = None, 
        location: Optional[str] = None
    ) -> dict:
        """
        Update the condition and/or location attributes of a given equipment item.

        Args:
            equipment_id (str): The unique identifier of the equipment to update.
            condition (Optional[str]): The new condition ("good", "damaged", etc.), or None if not changing.
            location (Optional[str]): The new location (e.g., room number), or None if not changing.

        Returns:
            dict: {
                "success": True,
                "message": "Equipment condition and location updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Equipment must exist.
            - At least one of 'condition' or 'location' must be provided.
        """
        eq = self.equipment.get(equipment_id)
        if not eq:
            return { "success": False, "error": "Equipment not found." }

        # At least one update parameter required
        if condition is None and location is None:
            return { "success": False, "error": "No update parameters provided." }

        updated = False
        if condition is not None:
            eq["condition"] = condition
            updated = True
        if location is not None:
            eq["location"] = location
            updated = True

        if not updated:
            return { "success": False, "error": "No attributes were updated." }
        return { "success": True, "message": "Equipment condition and location updated." }

    def trigger_overdue_alert(self, loan_id: str) -> dict:
        """
        Generate an alert if the specified loan transaction is overdue.

        Args:
            loan_id (str): The unique identifier of the loan transaction.

        Returns:
            dict:
                - success: True and a descriptive alert message if the loan is overdue
                - success: False and error message if the loan does not exist or is not overdue

        Constraints:
            - The loan_id must exist.
            - The loan's status must be 'overdue' to trigger the alert.
        """
        loan = self.loans.get(loan_id)
        if not loan:
            return { "success": False, "error": "Loan transaction not found" }

        if loan.get("status") != "overdue":
            return { "success": False, "error": "Loan is not overdue; no alert triggered" }

        equipment_id = loan.get("equipment_id")
        user_id = loan.get("user_id")
        equipment = self.equipment.get(equipment_id, {})
        user = self.users.get(user_id, {})

        equipment_info = equipment.get("type", "Unknown") + " " + equipment.get("model", "")
        user_name = user.get("name", "Unknown")

        message = (
            f"Alert triggered: Equipment '{equipment_info}' (loan ID: {loan_id}) is overdue. "
            f"Borrower: {user_name} (user ID: {user_id})."
        )
        # In a real system, this may log, email, or otherwise escalate; here, it's a returned message.

        return { "success": True, "message": message }

    def create_new_loan_transaction(
        self,
        equipment_id: str,
        user_id: str,
        borrowed_date: str,
        due_date: str
    ) -> dict:
        """
        Record a new borrowing event for an available equipment item.

        Args:
            equipment_id (str): Unique ID of the equipment to be loaned.
            user_id (str): Unique ID of the user borrowing the equipment.
            borrowed_date (str): Start date of the loan (ISO 8601/string format).
            due_date (str): Due/return deadline (ISO 8601/string format).

        Returns:
            dict: {
                "success": True,
                "message": "Loan transaction created for equipment <equipment_id> and user <user_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Equipment must exist and be available (not currently loaned out).
            - User must be registered (exist in system).
            - Equipment can only have one active loan at a time.
            - Equipment availability_status will be updated to 'loaned' on success.
        """
        # Check equipment exists
        if equipment_id not in self.equipment:
            return {"success": False, "error": "Equipment does not exist."}

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist or is not registered."}

        # Check equipment is available
        equipment_info = self.equipment[equipment_id]
        if equipment_info["availability_status"] != "available":
            return {"success": False, "error": "Equipment is not available for loan."}

        # Generate new loan ID (simple auto-increment or unique string)
        loan_id = str(uuid.uuid4())

        # Create loan transaction record
        new_loan: LoanTransactionInfo = {
            "loan_id": loan_id,
            "equipment_id": equipment_id,
            "user_id": user_id,
            "borrowed_date": borrowed_date,
            "due_date": due_date,
            "returned_date": None,
            "status": "active"
        }
        self.loans[loan_id] = new_loan

        # Update equipment status to 'loaned'
        self.equipment[equipment_id]["availability_status"] = "loaned"

        return {
            "success": True,
            "message": f"Loan transaction created for equipment {equipment_id} and user {user_id}."
        }

    def modify_loan_due_date(self, loan_id: str, new_due_date: str) -> dict:
        """
        Change the due_date for a given loan transaction, e.g. for extension requests.

        Args:
            loan_id (str): Unique identifier for the loan transaction.
            new_due_date (str): New due date (expected as a date string, format not validated here).

        Returns:
            dict: 
              - On success: { "success": True, "message": "Loan due date updated." }
              - On failure: { "success": False, "error": str }
    
        Constraints:
            - The loan must exist.
            - The loan status must be 'active' to allow modification.
            - new_due_date must not be empty.
        """
        # Check the loan exists
        loan = self.loans.get(loan_id)
        if not loan:
            return { "success": False, "error": "Loan transaction not found." }

        # Check loan is active
        if loan['status'] != 'active':
            return { "success": False, "error": "Loan due date can only be changed for active loans." }

        # Check new_due_date is present
        if not new_due_date or not isinstance(new_due_date, str):
            return { "success": False, "error": "Invalid new due date provided." }

        # Perform update
        loan['due_date'] = new_due_date

        # Optionally, update the loan object in the dictionary (redundant for reference types)
        self.loans[loan_id] = loan

        return { "success": True, "message": "Loan due date updated." }

    def modify_user_profile(
        self, 
        user_id: str, 
        name: str = None, 
        contact_info: str = None, 
        user_type: str = None
    ) -> dict:
        """
        Update information for a registered user.

        Args:
            user_id (str): The unique identifier for the user to update.
            name (str, optional): New name for user, if changing.
            contact_info (str, optional): New contact info, if changing.
            user_type (str, optional): New user type, e.g. 'patient', 'staff'.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "User profile updated." }
                On error:
                    { "success": False, "error": "reason/description" }

        Constraints:
            - Only registered users can be modified.
            - At least one field to update should be provided.
            - Updates fields only if non-None and non-empty (for name/contact/user_type).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        user_info = self.users[user_id]
        updated = False

        if name is not None and name.strip() != "":
            user_info["name"] = name
            updated = True
        if contact_info is not None and contact_info.strip() != "":
            user_info["contact_info"] = contact_info
            updated = True
        if user_type is not None and user_type.strip() != "":
            user_info["user_type"] = user_type
            updated = True

        if not updated:
            return { "success": False, "error": "No valid attribute to update was provided." }

        self.users[user_id] = user_info
        return { "success": True, "message": "User profile updated." }

    def delete_loan_transaction(self, loan_id: str, requester_id: str) -> dict:
        """
        Remove a loan transaction record from the system.
        Admins and staff users only.

        Args:
            loan_id (str): Unique identifier of the loan transaction to delete.
            requester_id (str): User ID of the person requesting deletion.

        Returns:
            dict: 
                {"success": True, "message": "Loan transaction deleted."}
                or
                {"success": False, "error": "<reason>"}
    
        Constraints:
            - Only users with user_type 'staff' or 'admin' can perform deletion.
            - If the loan is 'active', associated equipment status will be set to 'available'.
            - Loan record must exist.
            - Requester must exist and be authorized.
        """
        # Check requester exists
        requester = self.users.get(requester_id)
        if not requester:
            return { "success": False, "error": "Requester not found; unauthorized operation." }

        # Only 'staff' or 'admin' allowed
        if requester["user_type"] not in ("staff", "admin"):
            return { "success": False, "error": "Permission denied. Only staff/admin can delete loans." }

        # Check loan exists
        loan = self.loans.get(loan_id)
        if not loan:
            return { "success": False, "error": "Loan transaction not found." }

        # If loan is active, update equipment status to available
        equipment_id = loan["equipment_id"]
        if loan["status"] == "active" and equipment_id in self.equipment:
            self.equipment[equipment_id]["availability_status"] = "available"

        # Remove the loan record
        del self.loans[loan_id]

        return { "success": True, "message": "Loan transaction deleted." }