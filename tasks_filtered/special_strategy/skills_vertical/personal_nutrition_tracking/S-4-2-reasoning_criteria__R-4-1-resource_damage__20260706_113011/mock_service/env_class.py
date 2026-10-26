from typing import Dict, TypedDict
from typing import List, Dict
from datetime import datetime
import uuid
from typing import Optional
import re
from typing import List, Dict, Any



class UserInfo(TypedDict):
    _id: str           # Unique user identifier
    name: str          # User's name
    profile_info: str  # Arbitrary profile data (could be extended)

class MealRecordInfo(TypedDict):
    record_id: str     # Unique meal record identifier
    user_id: str       # References a User._id
    meal_name: str     # Descriptive meal name
    calories: float    # Non-negative calorie value
    consumed_at: str   # Timestamp (ISO string recommended)

class PersonalNutritionTrackingApp:
    def __init__(self, init_config: dict):
        """
        Environment for nutrition tracking.
        init_config: external initializer (not implemented here).
        """

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Meal records: {record_id: MealRecordInfo}
        self.meal_records: Dict[str, MealRecordInfo] = {}

        # Constraints:
        # - Each MealRecord must be linked to a specific User (user_id in users).
        # - Calorie values for a meal must be non-negative.
        # - consumed_at must be a valid timestamp string.
        # - Meal names should be descriptive with no restriction on duplication.

        self.init_config = init_config

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user(s) information using the user's name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": List[UserInfo]  # All users matching the name
                }
                Failure: {
                    "success": False,
                    "error": "No user found with that name"
                }

        Constraints:
            - Supports multiple users with the same name (returns all).
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info.get("name") == name or user_info.get("username") == name
        ]
        if not matches:
            return { "success": False, "error": "No user found with that name" }
        return { "success": True, "data": matches }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information using the user's unique _id.

        Args:
            user_id (str): The unique identifier of the user to retrieve.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": UserInfo  # User information dictionary
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The given user_id must exist in the application's users database.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        List all registered users in the nutrition tracking app.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all users' info (may be empty)
            }

        Constraints:
            - No constraints; returns all UserInfo in the system.
            - If no users are registered, returns an empty list (not an error).
        """
        all_users = list(self.users.values())
        return { "success": True, "data": all_users }

    def get_meal_records_by_user(self, user_id: str) -> dict:
        """
        Retrieve all meal records linked to a specific user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[MealRecordInfo]  # List of meal records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason, e.g. user not found
            }

        Constraints:
            - user_id must exist in self.users.
            - Each MealRecord must be linked to a specific User.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        records = [
            meal_record for meal_record in self.meal_records.values()
            if meal_record["user_id"] == user_id
        ]

        return { "success": True, "data": records }


    def get_meal_records_by_date_range(self, user_id: str, start_time: str, end_time: str) -> dict:
        """
        Retrieve all meal records for a user within a specific consumed_at time/date interval.

        Args:
            user_id (str): The user's unique identifier.
            start_time (str): ISO timestamp string (inclusive lower bound).
            end_time (str): ISO timestamp string (inclusive upper bound).

        Returns:
            dict:
                { "success": True, "data": List[MealRecordInfo] }
                or
                { "success": False, "error": str }

        Constraints:
            - user_id must correspond to an existing user.
            - start_time and end_time must be valid ISO timestamp strings.
            - All returned meal records must have consumed_at between start_time and end_time (inclusive).
        """
        # Validate user existence
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        # Validate timestamp format
        try:
            st = datetime.fromisoformat(start_time)
            et = datetime.fromisoformat(end_time)
        except Exception:
            return { "success": False, "error": "Invalid start_time or end_time format" }
    
        # Collect meal records for this user in date range
        result: List[MealRecordInfo] = []
        for rec in self.meal_records.values():
            if rec["user_id"] != user_id:
                continue
            try:
                consumed_dt = datetime.fromisoformat(rec["consumed_at"])
            except Exception:
                continue  # ignore records with bad consumed_at timestamp
            if st <= consumed_dt <= et:
                result.append(rec)
    
        return { "success": True, "data": result }

    def search_meal_records_by_name(self, user_id: str, meal_name: str) -> dict:
        """
        Search for meal records belonging to the specified user and matching the given meal name.

        Args:
            user_id (str): The user's unique identifier.
            meal_name (str): The meal name to search for (case-sensitive exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[MealRecordInfo],  # List of matching meal records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. if user does not exist
            }

        Constraints:
            - User with user_id must exist.
            - Meal name matching is by exact string match (case sensitive).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        matches = [
            record for record in self.meal_records.values()
            if record["user_id"] == user_id and record["meal_name"] == meal_name
        ]

        return { "success": True, "data": matches }

    def get_meal_record_by_id(self, record_id: str) -> dict:
        """
        Retrieve details of a specific meal record by its unique record_id.

        Args:
            record_id (str): Unique identifier for the meal record.

        Returns:
            dict: {
                "success": True,
                "data": MealRecordInfo
            }
            or
            {
                "success": False,
                "error": "Meal record not found"
            }

        Constraints:
            - record_id must exist in self.meal_records.
        """
        meal_record = self.meal_records.get(record_id)
        if meal_record is None:
            return { "success": False, "error": "Meal record not found" }
    
        return { "success": True, "data": meal_record }


    def get_user_nutrition_summary(self, user_id: str, start_date: str, end_date: str) -> dict:
        """
        Aggregate the total calories and meal counts logged by a user over a specified period.

        Args:
            user_id (str): The unique user identifier.
            start_date (str): Start of period, ISO format timestamp.
            end_date (str): End of period, ISO format timestamp.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "meal_count": int,
                    "calorie_total": float
                }
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - user_id must be present in users.
            - start_date and end_date must be valid ISO timestamps and start_date <= end_date.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Parse and validate dates
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except Exception:
            return { "success": False, "error": "Start or end date is not a valid ISO timestamp" }
        if start_dt > end_dt:
            return { "success": False, "error": "Start date must be before or equal to end date" }

        meal_count = 0
        calorie_total = 0.0

        for meal in self.meal_records.values():
            if meal["user_id"] != user_id:
                continue
            try:
                consumed_dt = datetime.fromisoformat(meal["consumed_at"])
            except Exception:
                continue  # Skip invalid timestamp
            if start_dt <= consumed_dt <= end_dt:
                meal_count += 1
                # Calories should be non-negative, but validate just in case
                cal = meal.get("calories", 0.0)
                if isinstance(cal, (int, float)) and cal >= 0:
                    calorie_total += cal

        return {
            "success": True,
            "data": {
                "meal_count": meal_count,
                "calorie_total": calorie_total
            }
        }


    def add_meal_record(self,
                        user_id: str,
                        meal_name: str,
                        calories: float,
                        consumed_at: str,
                        record_id: Optional[str] = None) -> dict:
        """
        Add a new MealRecord for a user, validating constraints.

        Args:
            user_id (str): User ID to link the record.
            meal_name (str): Descriptive name of the meal.
            calories (float): Non-negative calorie value.
            consumed_at (str): Timestamp (ISO string).
            record_id (Optional[str]): Record ID if supplied, else autogenerated.

        Returns:
            dict: {
                "success": True,
                "id": str,
                "data": MealRecordInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the constraint violation or failure
            }

        Constraints:
            - user_id must exist in users.
            - calories >= 0.
            - consumed_at must be a valid ISO timestamp.
            - record_id must be unique if given; autogenerated otherwise.
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User ID does not exist." }

        # Calorie constraint
        if not isinstance(calories, (int, float)) or calories < 0:
            return { "success": False, "error": "Calories value must be non-negative." }

        # consumed_at timestamp constraint
        try:
            dt = datetime.fromisoformat(consumed_at)
        except Exception:
            return { "success": False, "error": "consumed_at must be a valid ISO timestamp." }

        # Record ID: check uniqueness if supplied, else generate
        new_record_id = record_id if record_id is not None else str(uuid.uuid4())
        if new_record_id in self.meal_records:
            return { "success": False, "error": "record_id already exists." }

        # Prepare MealRecordInfo
        meal_record = {
            "record_id": new_record_id,
            "user_id": user_id,
            "meal_name": meal_name,
            "calories": calories,
            "consumed_at": consumed_at
        }

        self.meal_records[new_record_id] = meal_record

        return {
            "success": True,
            "id": new_record_id,
            "data": meal_record
        }

    def update_meal_record(
        self,
        record_id: str,
        meal_name: str = None,
        calories: float = None,
        consumed_at: str = None
    ) -> dict:
        """
        Modify details of an existing MealRecord.

        Args:
            record_id (str): The unique id of the MealRecord to modify.
            meal_name (str, optional): New meal name.
            calories (float, optional): New calories value (must be non-negative).
            consumed_at (str, optional): New timestamp (ISO string recommended).

        Returns:
            dict: 
                Success:
                    {"success": True, "data": MealRecordInfo}
                Failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - record_id must exist in self.meal_records.
            - If calories is provided, it must be non-negative.
            - If consumed_at is provided, it must be a valid ISO 8601 string.
            - At least one field to update should be provided.
        """
        # Check record existence
        record = self.meal_records.get(record_id)
        if not record:
            return {"success": False, "error": "MealRecord with given record_id does not exist."}

        # Validate there's something to update
        if meal_name is None and calories is None and consumed_at is None:
            return {"success": False, "error": "No update fields provided."}

        # Validate calories
        if calories is not None:
            if not isinstance(calories, (float, int)) or calories < 0:
                return {"success": False, "error": "Calorie value must be a non-negative number."}
            record["calories"] = float(calories)

        # Validate consumed_at (basic ISO 8601 check)
        if consumed_at is not None:
            # Very basic ISO format check (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            if not isinstance(consumed_at, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$", consumed_at):
                return {"success": False, "error": "consumed_at must be a valid ISO 8601 timestamp string."}
            record["consumed_at"] = consumed_at

        # Update meal_name
        if meal_name is not None:
            record["meal_name"] = meal_name

        # Save changes back (not strictly needed as dict is mutable)
        self.meal_records[record_id] = record

        return {"success": True, "data": record}

    def delete_meal_record(self, record_id: str) -> dict:
        """
        Remove a meal record from the app for a user.

        Args:
            record_id (str): Unique identifier of the meal record to be deleted.

        Returns:
            dict: 
                {
                    "success": True,
                    "deleted_id": str
                }
                or 
                {
                    "success": False,
                    "error": "Meal record not found."
                }

        Constraints:
            - The record_id must exist in the meal_records database.
            - No other constraints limit removal.

        """
        if record_id not in self.meal_records:
            return { "success": False, "error": "Meal record not found." }
        del self.meal_records[record_id]
        return { "success": True, "deleted_id": record_id }


    def bulk_add_meal_records(self, user_id: str, records: List[Dict[str, Any]]) -> dict:
        """
        Add multiple meal records simultaneously for a user.

        Args:
            user_id (str): Target user ID (must exist)
            records (List[Dict]): Each meal record dict containing:
                - meal_name (str): Name of meal
                - calories (float): Non-negative value
                - consumed_at (str): ISO-format timestamp
                - Optional: record_id (str): If omitted, auto-generated

        Returns:
            dict: 
                Success: { "success": True, "data": {...} }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - User must exist.
            - Calories must be non-negative.
            - consumed_at must be a valid ISO-format timestamp.
            - record_id must be unique (if supplied or auto-generated).
            - No partial adds (atomic): any bad item aborts all.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if not isinstance(records, list):
            return { "success": False, "error": "records input must be a list" }

        # Check all constraints. Collect MealRecordInfo for batch insert.
        new_records = []
        for idx, rec in enumerate(records):
            # Check required fields
            for k in ("meal_name", "calories", "consumed_at"):
                if k not in rec:
                    return { "success": False, "error": f"Missing '{k}' in record {idx}" }

            # Calories non-negative
            try:
                cal = float(rec["calories"])
                if cal < 0:
                    return { "success": False, "error": f"Negative calories in record {idx}" }
            except Exception:
                return { "success": False, "error": f"Invalid calories in record {idx}" }

            # Check timestamp
            try:
                datetime.fromisoformat(rec["consumed_at"])
            except Exception:
                return { "success": False, "error": f"Invalid timestamp in record {idx}" }

            # Assign or validate record_id
            record_id = rec.get("record_id", str(uuid.uuid4()))
            if record_id in self.meal_records:
                return { "success": False, "error": f"Duplicate record_id ({record_id}) in meal_records" }
            # Also check for duplicate IDs in the new batch
            if any(r["record_id"] == record_id for r in new_records):
                return { "success": False, "error": f"Duplicate record_id ({record_id}) in batch input" }

            meal_record: MealRecordInfo = {
                "record_id": record_id,
                "user_id": user_id,
                "meal_name": rec["meal_name"],
                "calories": cal,
                "consumed_at": rec["consumed_at"],
            }
            new_records.append(meal_record)

        # All inputs validated; commit
        for meal_record in new_records:
            self.meal_records[meal_record["record_id"]] = meal_record

        return {
            "success": True,
            "data": {
                "added_count": len(new_records),
                "records": new_records
            }
        }


    def correct_meal_record_timestamp(self, record_id: str, new_timestamp: str) -> dict:
        """
        Update the consumed_at timestamp of a meal record to ensure validity.

        Args:
            record_id (str): The unique identifier of the meal record to update.
            new_timestamp (str): The new timestamp to assign (should be valid ISO 8601 string).

        Returns:
            dict: {
                "success": True,
                "data": MealRecordInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. record not found, invalid timestamp
            }

        Constraints:
            - record_id must exist in self.meal_records.
            - new_timestamp must be a valid timestamp string (ISO 8601 format recommended).
        """
        record = self.meal_records.get(record_id)
        if not record:
            return { "success": False, "error": "Meal record not found." }

        # Validate timestamp format using datetime parsing
        try:
            # Accepts most ISO 8601 strings; adjust format if more strictness required
            datetime.fromisoformat(new_timestamp.replace("Z", "+00:00"))
        except Exception:
            return { "success": False, "error": "Invalid timestamp format." }

        # Update timestamp
        record["consumed_at"] = new_timestamp
        return { "success": True, "data": record }

    def adjust_meal_record_calories(self, record_id: str, new_calories: float) -> dict:
        """
        Update the calorie value for a given meal record.

        Args:
            record_id (str): Unique identifier of the meal record to update.
            new_calories (float): New calorie value to set. Must be non-negative.

        Returns:
            dict:
                On success: { "success": True, "data": MealRecordInfo }
                On failure:
                    - If meal record does not exist: { "success": False, "error": "Meal record not found." }
                    - If new_calories is negative: { "success": False, "error": "Calorie value must be non-negative." }

        Constraints:
            - Meal record must exist.
            - Calorie value must be >= 0.
        """
        if record_id not in self.meal_records:
            return { "success": False, "error": "Meal record not found." }
        if new_calories < 0:
            return { "success": False, "error": "Calorie value must be non-negative." }

        self.meal_records[record_id]['calories'] = new_calories
        return { "success": True, "data": self.meal_records[record_id] }