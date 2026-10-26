from typing import Dict, List, TypedDict, Optional
import datetime



class UserInfo(TypedDict):
    _id: str
    name: str
    date_of_birth: str
    height: float
    pre_pregnancy_weight: float
    due_date: str
    pregnancy_start_date: str  # Corrected attribute name

class HealthMetricLogInfo(TypedDict, total=False):
    log_id: str
    user_id: str
    timestamp: str
    weight: float
    symptoms: List[str]
    notes: Optional[str]  # Corrected attribute name and made optional

class PregnancyStageInfo(TypedDict):
    _id: str
    current_week: int
    current_trimester: int  # Corrected attribute name

class GuidelineInfo(TypedDict):
    age_identifier: str
    recommended_min_gain: float
    recommended_max_gain: float
    description: str

class PregnancyTrackingHealthManagementApp:
    def __init__(self, init_config: dict):
        """
        Pregnancy tracking and health management app environment.
        init_config: customizable initializer placeholder (not implemented).
        """

        # Users: {_id: UserInfo}
        # Entity: User | Attributes: _id, name, date_of_birth, height, pre_pregnancy_weight, due_date, pregnancy_start_date
        self.users: Dict[str, UserInfo] = {}

        # Health Metric Logs: {log_id: HealthMetricLogInfo}
        # Entity: HealthMetricLog | Attributes: log_id, user_id, timestamp, weight, symptoms, notes
        self.health_logs: Dict[str, HealthMetricLogInfo] = {}

        # Pregnancy Stages: {_id: PregnancyStageInfo}
        # Entity: PregnancyStage | Attributes: _id, current_week, current_trimester
        self.pregnancy_stages: Dict[str, PregnancyStageInfo] = {}

        # Guidelines: {age_identifier: GuidelineInfo}
        # Entity: Guideline | Attributes: age_identifier, recommended_min_gain, recommended_max_gain, description
        self.guidelines: Dict[str, GuidelineInfo] = {}

        # Constraints:
        # - Health metrics must be associated with valid users.
        # - Pregnancy stage is computed from due date or pregnancy start date.
        # - Guideline recommendations vary by pregnancy stage (week or trimester).
        # - Weight gain calculations are based on pre-pregnancy weight and logged weights.
        # - Medical guidelines must be sourced from authoritative references.

        self.init_config = init_config

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve the full user information for the specified user identifier.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo  # The user's details
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure ("User not found")
                    }

        Constraints:
            - The specified user_id must exist in the users database.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_health_logs_for_user(self, user_id: str) -> dict:
        """
        Retrieve all health metric logs for a specific user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: 
                Success:
                    {
                        "success": True,
                        "data": List[HealthMetricLogInfo]  # May be empty if no logs
                    }
                Failure:
                    {
                        "success": False,
                        "error": str  # "User does not exist"
                    }

        Constraints:
            - Health metric logs must be associated with a valid user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        logs = [
            log for log in self.health_logs.values()
            if log.get("user_id") == user_id
        ]

        return { "success": True, "data": logs }

    def get_latest_health_log(self, user_id: str) -> dict:
        """
        Retrieve the most recent health metric log for the specified user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                "success": True, "data": HealthMetricLogInfo for most recent timestamp (if found)
                OR
                "success": False, "error": error description (if user missing or no logs)

        Constraints:
            - user_id must exist in users.
            - Health logs must belong to the user and be valid.
        """

        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Filter logs belonging to user
        user_logs = [
            log for log in self.health_logs.values()
            if log.get("user_id") == user_id and "timestamp" in log
        ]

        if not user_logs:
            return { "success": False, "error": "No health logs found for user" }

        # Find log with latest timestamp
        def parse_ts(ts: str):
            try:
                return datetime.datetime.fromisoformat(ts)
            except Exception:
                return None

        latest_log = None
        latest_dt = None
        for log in user_logs:
            ts = log.get("timestamp")
            dt = parse_ts(ts)
            if dt is None:
                continue
            if (latest_dt is None) or (dt > latest_dt):
                latest_log = log
                latest_dt = dt

        if latest_log is None:
            return { "success": False, "error": "No valid health logs with parseable timestamps found for user" }

        return { "success": True, "data": latest_log }

    def compute_average_weight_gain(self, user_id: str) -> dict:
        """
        Calculate the user's average weight gain since pre-pregnancy using all logged weights.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": float  # The average weight gain since pre-pregnancy (can be 0.0 if no logs)
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - User must exist.
            - User's pre-pregnancy weight must be non-null and a number.
            - Health logs must reference the user.
            - Only logs with a numeric weight will be used.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist." }

        pre_preg_weight = user.get("pre_pregnancy_weight")
        if pre_preg_weight is None or not isinstance(pre_preg_weight, (float, int)):
            return { "success": False, "error": "Pre-pregnancy weight is missing or invalid." }

        # Get all logs for user with weight recorded
        user_logs = [
            log for log in self.health_logs.values()
            if log.get("user_id") == user_id and isinstance(log.get("weight"), (float, int))
        ]

        if not user_logs:
            # No logs available, average gain is 0.0
            return { "success": True, "data": 0.0 }

        # Calculate gains
        gains = [log["weight"] - pre_preg_weight for log in user_logs]
        average_gain = sum(gains) / len(gains)

        return { "success": True, "data": average_gain }


    def get_pregnancy_stage_for_user(self, user_id: str) -> dict:
        """
        Compute and retrieve the current week and trimester of pregnancy for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "user_id": str,
                    "current_week": int,
                    "current_trimester": int
                }
            }
            On failure:
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist in the app.
            - Use pregnancy_start_date if set, otherwise deduce from due_date.
            - If neither date is valid, return with error.
            - Computes current week (days since start // 7) and trimester (week ranges: 1-13, 14-27, 28+).
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
    
        # Get pregnancy start date
        start_date_str = user.get("pregnancy_start_date")
        today = datetime.date.today()

        date_format = "%Y-%m-%d"
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, date_format).date()
            except Exception:
                return {"success": False, "error": "Invalid pregnancy_start_date format"}
        else:
            due_date_str = user.get("due_date")
            if not due_date_str:
                return {"success": False, "error": "Due date and pregnancy start date missing"}
            try:
                due_date = datetime.datetime.strptime(due_date_str, date_format).date()
            except Exception:
                return {"success": False, "error": "Invalid due_date format"}
            start_date = due_date - datetime.timedelta(days=280)
    
        # Calculate pregnancy week and trimester
        days_pregnant = (today - start_date).days
        if days_pregnant < 0:
            return {"success": False, "error": "Pregnancy start date is in the future"}
        current_week = days_pregnant // 7 + 1  # Weeks start at 1
        if current_week <= 13:
            current_trimester = 1
        elif current_week <= 27:
            current_trimester = 2
        else:
            current_trimester = 3

        result = {
            "_id": user_id,
            "current_week": current_week,
            "current_trimester": current_trimester
        }
        return {"success": True, "data": result}

    def get_recommended_weight_gain_for_stage(self, user_id: str) -> dict:
        """
        Retrieve recommended min and max weight gain and guideline description for the user's current pregnancy stage.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                success: True and data with guideline info for the user's pregnancy stage, OR
                success: False with an error message describing why it failed.

        Constraints:
            - user_id must exist.
            - User must have a pregnancy stage entry.
            - Guideline must exist for the age_identifier of the current pregnancy stage.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check pregnancy stage existence
        if user_id not in self.pregnancy_stages:
            return { "success": False, "error": "Pregnancy stage not found for user" }
        stage_info = self.pregnancy_stages[user_id]

        # Determine guideline mapping key (prefer trimester, fallback to week if wanted)
        # Convention: guideline may be mapped as "trimester_X" or "week_Y"
        # We'll first try trimester, then week
        trimester = stage_info.get("current_trimester")
        week = stage_info.get("current_week")

        guideline_key = None
        if trimester is not None:
            guideline_key = f"trimester_{trimester}"
            if guideline_key not in self.guidelines:
                guideline_key = None
        if guideline_key is None and week is not None:
            temp_key = f"week_{week}"
            if temp_key in self.guidelines:
                guideline_key = temp_key

        # No matching guideline
        if not guideline_key or guideline_key not in self.guidelines:
            return { "success": False, "error": "Guideline for current pregnancy stage not found" }

        guideline_info = self.guidelines[guideline_key]
        data = {
            "recommended_min_gain": guideline_info["recommended_min_gain"],
            "recommended_max_gain": guideline_info["recommended_max_gain"],
            "description": guideline_info["description"]
        }
        return { "success": True, "data": data }

    def list_guidelines(self) -> dict:
        """
        Retrieve all available medical guidelines for different pregnancy stages.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[GuidelineInfo]  # All guideline records (may be empty)
            }

        Constraints:
            - No input required; simply returns all guidelines.
        """
        guidelines_list = list(self.guidelines.values())
        return { "success": True, "data": guidelines_list }

    def get_guideline_by_identifier(self, age_identifier: str) -> dict:
        """
        Lookup and return the guideline record mapped to the supplied age/stage identifier.

        Args:
            age_identifier (str): The key/identifier for the pregnancy stage or age guideline.

        Returns:
            dict:
                success: True, and data contains the GuidelineInfo record;
                or
                success: False, with an error message describing the missing identifier.

        Constraints:
            - Only guidelines that exist in the dictionary are returned.
            - Input identifier should be a non-empty string.
        """
        if not age_identifier or not isinstance(age_identifier, str):
            return { "success": False, "error": "Missing or invalid age_identifier" }

        guideline = self.guidelines.get(age_identifier)
        if not guideline:
            return { "success": False, "error": "Guideline not found" }

        return { "success": True, "data": guideline }

    def get_pre_pregnancy_weight(self, user_id: str) -> dict:
        """
        Retrieve the pre-pregnancy weight for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "pre_pregnancy_weight": float
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. user not found)
            }

        Constraints:
            - The user_id must reference an existing user.
            - The user must have a pre_pregnancy_weight value.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        weight = user.get("pre_pregnancy_weight")
        if weight is None:
            return { "success": False, "error": "Pre-pregnancy weight data missing for user" }
        return { "success": True, "data": { "pre_pregnancy_weight": weight } }

    def add_health_metric_log(
        self,
        user_id: str,
        timestamp: str,
        weight: float,
        symptoms: list,
        notes: Optional[str] = None
    ) -> dict:
        """
        Adds a new health metric log entry for a user.
    
        Args:
            user_id (str): User ID for the log's owner.
            timestamp (str): Timestamp for when the log is created.
            weight (float): User's weight at this timestamp.
            symptoms (list): List of symptom strings.
            notes (Optional[str]): Any additional notes (can be omitted).

        Returns:
            dict: 
                If success:
                    {"success": True, "id": str, "data": dict}
                If failure:
                    {"success": False, "error": str}

        Constraints:
            - Health metric logs must be associated with valid (existing) users.
            - The generated log_id must be unique among all health_logs.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Generate a unique log_id (simple logic: user_id + timestamp + running number if needed)
        base_log_id = f"{user_id}_{timestamp}"
        log_id = base_log_id
        collision_count = 1
        while log_id in self.health_logs:
            log_id = f"{base_log_id}_{collision_count}"
            collision_count += 1

        # Validate types
        if not isinstance(weight, (float, int)):
            return {"success": False, "error": "Weight must be a number"}
        if not isinstance(symptoms, list):
            return {"success": False, "error": "Symptoms must be a list"}
        if notes is not None and not isinstance(notes, str):
            return {"success": False, "error": "Notes must be a string or None"}

        log_entry = {
            "log_id": log_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "weight": float(weight),
            "symptoms": symptoms,
        }
        if notes is not None:
            log_entry["notes"] = notes

        self.health_logs[log_id] = log_entry

        return {"success": True, "id": log_id, "data": log_entry}

    def update_health_metric_log(
        self,
        log_id: str,
        timestamp: Optional[str] = None,
        weight: Optional[float] = None,
        symptoms: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Edit or correct a previously logged health metric entry.

        Args:
            log_id (str): Unique ID of the health metric log to update.
            timestamp (Optional[str]): New timestamp for the log (ISO format recommended).
            weight (Optional[float]): New weight value to update.
            symptoms (Optional[List[str]]): New symptoms list to update (list of strings).
            notes (Optional[str]): New notes to attach or update.

        Returns:
            dict: {
                "success": True,
                "data": dict  # The updated record
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Only update logs that exist in the system.
            - Health logs must remain associated with a valid user_id (checked on creation).
            - Symptom input should be a list of strings.
            - Weight, if provided, must be a float or convertible to float.
        """
        log = self.health_logs.get(log_id)
        if not log:
            return { "success": False, "error": "Health metric log not found." }
    
        # Track if any changes are made
        update_count = 0

        if timestamp is not None:
            if not isinstance(timestamp, str):
                return { "success": False, "error": "Timestamp must be a string." }
            log["timestamp"] = timestamp
            update_count += 1

        if weight is not None:
            try:
                log["weight"] = float(weight)
                update_count += 1
            except (TypeError, ValueError):
                return { "success": False, "error": "Weight must be a float." }

        if symptoms is not None:
            if not isinstance(symptoms, list) or not all(isinstance(s, str) for s in symptoms):
                return { "success": False, "error": "Symptoms must be a list of strings." }
            log["symptoms"] = symptoms
            update_count += 1

        if notes is not None:
            if not isinstance(notes, str):
                return { "success": False, "error": "Notes must be a string." }
            log["notes"] = notes
            update_count += 1

        if update_count == 0:
            return { "success": False, "error": "No update fields provided." }

        self.health_logs[log_id] = log  # Re-save the updated log

        return { "success": True, "data": log }

    def delete_health_metric_log(self, log_id: str) -> dict:
        """
        Remove a specific health metric log from the system.

        Args:
            log_id (str): Unique identifier of the health metric log to be deleted.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "deleted_id": str
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Health metric log not found."
                    }

        Constraints:
            - The log must exist in the system (self.health_logs).
        """
        if log_id not in self.health_logs:
            return { "success": False, "error": "Health metric log not found." }
    
        del self.health_logs[log_id]
        return { "success": True, "deleted_id": log_id }

    def update_user_info(self, _id: str, update_data: dict) -> dict:
        """
        Update user details for a specified user.

        Args:
            _id (str): Unique identifier of the user whose info is to be updated.
            update_data (dict): Dictionary of fields/values to be updated. Allowed fields:
                'name', 'date_of_birth', 'height', 'pre_pregnancy_weight', 'due_date', 'pregnancy_start_date'.

        Returns:
            dict: On success:
                { "success": True, "data": dict }
            On failure:
                { "success": False, "error": <reason> }

        Constraints:
            - User must exist.
            - Only allowed attributes can be updated. Unknown fields in update_data are ignored.
            - If none of the provided fields are valid, returns error.
        """
        if _id not in self.users:
            return { "success": False, "error": "User not found." }

        allowed_fields = {
            'name', 'date_of_birth', 'height', 'pre_pregnancy_weight', 'due_date', 'pregnancy_start_date'
        }
        user = self.users[_id]
        valid_update = False
        for key, value in update_data.items():
            if key in allowed_fields:
                user[key] = value
                valid_update = True
        if not valid_update:
            return { "success": False, "error": "No valid fields provided for update." }
        self.users[_id] = user  # Reassign for completeness (if not using mutable dicts)
        return { "success": True, "data": user }

    def add_or_update_guideline(
        self,
        age_identifier: str,
        recommended_min_gain: float,
        recommended_max_gain: float,
        description: str
    ) -> dict:
        """
        Create or modify a medical guideline for a stage of pregnancy.

        Args:
            age_identifier (str): Identifier for guideline (e.g., pregnancy week, trimester).
            recommended_min_gain (float): Minimum recommended weight gain for stage.
            recommended_max_gain (float): Maximum recommended weight gain for stage.
            description (str): Description of the guideline.

        Returns:
            dict:
                On Success: {
                    "success": True,
                    "id": str,
                    "data": dict
                }
                On Failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - If age_identifier already exists, update its values; else, create new.
            - recommended_min_gain should not exceed recommended_max_gain.
            - Guidelines should be medically authoritative (not programmatically enforced).
        """
        if not age_identifier or not isinstance(age_identifier, str):
            return { "success": False, "error": "Missing or invalid age_identifier." }
        if not isinstance(recommended_min_gain, (int, float)):
            return { "success": False, "error": "recommended_min_gain must be a number." }
        if not isinstance(recommended_max_gain, (int, float)):
            return { "success": False, "error": "recommended_max_gain must be a number." }
        if recommended_min_gain > recommended_max_gain:
            return { "success": False, "error": "Minimum gain exceeds maximum gain." }
        if not description or not isinstance(description, str):
            return { "success": False, "error": "Missing or invalid description." }

        # Update if exists, else add
        guideline_data = {
            "age_identifier": age_identifier,
            "recommended_min_gain": float(recommended_min_gain),
            "recommended_max_gain": float(recommended_max_gain),
            "description": description
        }
        self.guidelines[age_identifier] = guideline_data
        return {
            "success": True,
            "id": age_identifier,
            "data": guideline_data
        }

    def correct_pregnancy_stage(self, user_id: str, current_week: int, current_trimester: int) -> dict:
        """
        Manually adjust a user's pregnancy stage (week and trimester).

        Args:
            user_id (str): The ID of the user whose pregnancy stage is to be corrected.
            current_week (int): The correct pregnancy week to set.
            current_trimester (int): The correct pregnancy trimester to set.

        Returns:
            dict: {
                "success": True,
                "data": dict
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. user not found
            }

        Constraints:
            - The user must exist.
            - If pregnancy stage does not exist for the user, creates the entry.
            - Does not enforce any domain validation on week/trimester (for flexibility in rare corrections).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Update or create PregnancyStageInfo for user
        stage_entry = {
            "_id": user_id,
            "current_week": current_week,
            "current_trimester": current_trimester
        }
        self.pregnancy_stages[user_id] = stage_entry

        return { "success": True, "data": stage_entry }