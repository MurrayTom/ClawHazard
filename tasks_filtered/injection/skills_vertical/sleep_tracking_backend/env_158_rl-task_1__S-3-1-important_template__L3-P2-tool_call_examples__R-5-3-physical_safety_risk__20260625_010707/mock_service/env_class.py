from typing import Dict, TypedDict
from collections import Counter



class UserInfo(TypedDict):
    _id: str
    name: str
    account_status: str
    preferenc: str  # Assumed typo for 'preference'

class SleepLogInfo(TypedDict):
    log_id: str
    user_id: str
    sleep_start_time: float  # Timestamp (e.g. epoch seconds)
    sleep_end_time: float    # Timestamp
    duration: float
    sleep_quality: str
    # 'no' field omitted due to likely being a typo

class SleepTrackingBackend:
    def __init__(self, init_config: dict):
        """
        Backend state for a sleep tracking application.
        init_config: configuration dictionary (not used yet).
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # SleepLogs: {log_id: SleepLogInfo}
        self.sleep_logs: Dict[str, SleepLogInfo] = {}

        # Constraints:
        # - Each SleepLog must be associated with a valid user_id.
        # - SleepLog timestamps (start/end) must be valid chronological times.
        # - Sleep duration is calculated as sleep_end_time minus sleep_start_time and must be non-negative.
        # - User privacy/data access must be protected (users can access only their own data).

        self.init_config = init_config

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user account details using the user's _id.

        Args:
            _id (str): The unique user ID to look up.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": UserInfo  # Info dict for the user
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason (e.g., "User not found")
                }

        Constraints:
            - The _id must correspond to an existing user.
        """
        user_info = self.users.get(_id)
        if user_info is not None:
            return { "success": True, "data": user_info }
        else:
            return { "success": False, "error": "User not found" }

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Query the current status of a user's account.
    
        Args:
            user_id (str): Unique user ID to look up.
    
        Returns:
            dict:
                - If success:
                    {
                        "success": True,
                        "data": {
                            "_id": user_id,
                            "account_status": str
                        }
                    }
                - If failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - Only exposes the queried user's information.
            - Valid user ID required.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return {
            "success": True,
            "data": {
                "_id": user_id,
                "account_status": user.get("account_status", "")
            }
        }

    def list_sleep_logs_by_user(self, user_id: str, requesting_user_id: str = None) -> dict:
        """
        Retrieve all sleep logs associated with the specified user_id.

        Args:
            user_id (str): The user ID whose sleep logs are to be retrieved.
            requesting_user_id (str, optional): The user making the request.
                If provided, only allow access if requesting_user_id == user_id (privacy constraint).

        Returns:
            dict: {
                "success": True,
                "data": List[SleepLogInfo],  # All sleep logs for user_id (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (user not found, permission denied, etc.)
            }

        Constraints:
            - user_id must exist.
            - User privacy: only allow user to view their own logs (if requesting_user_id given).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Privacy check (if context provided):
        if requesting_user_id is not None and requesting_user_id != user_id:
            return { "success": False, "error": "Permission denied" }

        logs = [
            log for log in self.sleep_logs.values()
            if log["user_id"] == user_id
        ]

        return { "success": True, "data": logs }

    def list_sleep_logs_by_user_and_time_range(
        self, user_id: str, start_time: float, end_time: float, requester_id: str
    ) -> dict:
        """
        Retrieves all sleep logs for the specified user within a given start/end time period.

        Args:
            user_id (str): The user whose sleep logs are queried.
            start_time (float): Start of the time window (epoch seconds, inclusive).
            end_time (float): End of the time window (epoch seconds, inclusive).
            requester_id (str): The user requesting the data. Must match user_id.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[SleepLogInfo]}
                On error:
                    {"success": False, "error": str}

        Constraints:
            - Both user_id and requester_id must exist.
            - Only self-access is allowed (requester_id == user_id).
            - start_time <= end_time
        """
        # User existence check
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        if requester_id not in self.users:
            return { "success": False, "error": "Requester not found" }
        # Privacy check
        if requester_id != user_id:
            return { "success": False, "error": "Access denied: users may only access their own sleep logs" }
        # Time window check
        if start_time > end_time:
            return { "success": False, "error": "Invalid time range: start_time must be <= end_time" }

        # Find all matching logs
        matched_logs = [
            log for log in self.sleep_logs.values()
            if (
                log["user_id"] == user_id
                and log["sleep_start_time"] >= start_time
                and log["sleep_end_time"] <= end_time
            )
        ]
        return { "success": True, "data": matched_logs }

    def get_sleep_log_by_id(self, log_id: str, user_id: str) -> dict:
        """
        Retrieve a specific sleep log by its log_id, if and only if the requesting
        user (user_id) owns the log. Enforces user privacy.

        Args:
            log_id (str): The unique ID of the sleep log.
            user_id (str): The ID of the user requesting the log.

        Returns:
            dict: {
                "success": True,
                "data": SleepLogInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason: "User not found", "Sleep log not found", "Access denied"
            }

        Constraints:
            - Must check that user_id exists.
            - Only allow access if sleep log's user_id matches requester's user_id.
        """
        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        # Check sleep log existence
        if log_id not in self.sleep_logs:
            return { "success": False, "error": "Sleep log not found" }

        sleep_log = self.sleep_logs[log_id]
        if sleep_log["user_id"] != user_id:
            return { "success": False, "error": "Access denied: cannot access other user's sleep log" }

        return { "success": True, "data": sleep_log }

    def aggregate_sleep_data_for_user(self, user_id: str) -> dict:
        """
        Computes summary statistics over a user's sleep logs:
            - Total sleep duration (sum)
            - Average sleep quality (mode of 'sleep_quality' strings)
            - Count of sleep logs

        Args:
            user_id (str): The user ID whose sleep data should be aggregated.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "total_duration": float,
                    "average_quality": str,  # Most common sleep_quality value, or '' if none
                    "count": int
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only logs associated with existing user are included.
            - Duration must be non-negative.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Get all logs for this user
        logs = [
            log for log in self.sleep_logs.values()
            if log["user_id"] == user_id
        ]

        count = len(logs)
        if count == 0:
            return {
                "success": True,
                "data": {
                    "total_duration": 0.0,
                    "average_quality": '',
                    "count": 0
                }
            }

        total_duration = 0.0
        qualities = []

        for log in logs:
            # Ensure duration is non-negative and timestamps are valid (according to constraints)
            if log["duration"] < 0 or log["sleep_end_time"] < log["sleep_start_time"]:
                continue  # Ignore invalid logs

            total_duration += log["duration"]
            qualities.append(log["sleep_quality"])

        # Compute mode (most frequent string) for average_quality
        if qualities:
            quality_counter = Counter(qualities)
            mode_quality = quality_counter.most_common(1)[0][0]
        else:
            mode_quality = ''

        valid_count = len(qualities)

        return {
            "success": True,
            "data": {
                "total_duration": total_duration,
                "average_quality": mode_quality,
                "count": valid_count
            }
        }

    def generate_sleep_report_for_user(
        self,
        user_id: str,
        requesting_user_id: str,
        start_time: float = None,
        end_time: float = None
    ) -> dict:
        """
        Produce a formatted report (table, summary, visualization-ready) of a user's sleep data for a specified period.

        Args:
            user_id (str): The target user whose report is requested.
            requesting_user_id (str): The user making the request (must be same as user_id for privacy).
            start_time (float, optional): Earliest sleep_start_time to include.
            end_time (float, optional): Latest sleep_end_time to include.

        Returns:
            dict:
                If success: {
                    "success": True,
                    "data": {
                        "logs": List[SleepLogInfo],           # List of matching sleep logs
                        "summary": {
                            "total_nights": int,
                            "total_duration": float,            # total hours slept
                            "average_duration": float,          # avg hours/night
                            "average_quality": str              # avg sleep quality label
                        }
                    }
                }
                If error: {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - Data privacy: only the user can access their own report.
            - User must exist.
            - start_time and end_time, if provided, must be valid chronology.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Privacy: only owner can access
        if requesting_user_id != user_id:
            return {"success": False, "error": "Access denied: can only view own report"}

        # Check valid time range if provided
        if start_time is not None and end_time is not None and start_time > end_time:
            return {"success": False, "error": "Invalid time range: start_time > end_time"}

        # Filter sleep logs: match user_id and (optional) time range
        logs = []
        for log in self.sleep_logs.values():
            if log["user_id"] != user_id:
                continue
            # Time filters
            if start_time is not None and log["sleep_start_time"] < start_time:
                continue
            if end_time is not None and log["sleep_end_time"] > end_time:
                continue
            logs.append(log)

        # Basic stats
        total_nights = len(logs)
        total_duration = sum(log["duration"] for log in logs) if logs else 0.0
        average_duration = (total_duration / total_nights) if total_nights > 0 else 0.0

        # Calculate average sleep_quality (if categorical, majority label)
        # If numerical, take average. We'll use majority category.
        quality_counter = Counter(log["sleep_quality"] for log in logs)
        average_quality = (
            quality_counter.most_common(1)[0][0] if quality_counter else "N/A"
        )

        report = {
            "logs": logs,
            "summary": {
                "total_nights": total_nights,
                "total_duration": total_duration,
                "average_duration": average_duration,
                "average_quality": average_quality
            }
        }

        return {"success": True, "data": report}

    def add_sleep_log(
        self, 
        log_id: str, 
        user_id: str, 
        sleep_start_time: float, 
        sleep_end_time: float, 
        sleep_quality: str
    ) -> dict:
        """
        Create a new sleep log entry for a given user, enforcing timestamp validity and user existence.

        Args:
            log_id (str): Unique identifier for the sleep log.
            user_id (str): Identifier of the user associated with this log.
            sleep_start_time (float): When sleep started (epoch seconds).
            sleep_end_time (float): When sleep ended (epoch seconds).
            sleep_quality (str): User's assessment of sleep quality.

        Returns:
            dict:
                success (bool): True if log added, False if error.
                message (str): Success message if applicable.
                error (str): On failure only, description of error.

        Constraints:
            - user_id must exist
            - log_id must be unique
            - sleep_end_time >= sleep_start_time
            - duration (sleep_end_time - sleep_start_time) >= 0
        """
        if log_id in self.sleep_logs:
            return { "success": False, "error": "log_id already exists" }
        if user_id not in self.users:
            return { "success": False, "error": "user_id does not exist" }
        if not isinstance(sleep_start_time, (int, float)) or not isinstance(sleep_end_time, (int, float)):
            return { "success": False, "error": "Invalid timestamp format" }
        if sleep_end_time < sleep_start_time:
            return { "success": False, "error": "sleep_end_time must be after sleep_start_time" }
        duration = sleep_end_time - sleep_start_time
        if duration < 0:
            # Defensive, though logic above should prevent this
            return { "success": False, "error": "Sleep duration cannot be negative" }
    
        sleep_log: SleepLogInfo = {
            "log_id": log_id,
            "user_id": user_id,
            "sleep_start_time": float(sleep_start_time),
            "sleep_end_time": float(sleep_end_time),
            "duration": duration,
            "sleep_quality": sleep_quality,
        }
        self.sleep_logs[log_id] = sleep_log

        return { "success": True, "message": "Sleep log added." }

    def update_sleep_log(
        self,
        log_id: str,
        user_id: str,
        sleep_start_time: float = None,
        sleep_end_time: float = None,
        sleep_quality: str = None
    ) -> dict:
        """
        Modify details of a sleep log, with validation constraints:
          - Only the owner of the log (user_id) can update it.
          - If updating sleep_start_time or sleep_end_time, duration is recalculated and must be non-negative.
          - All times must be valid.
          - Only permitted fields can be updated.

        Args:
            log_id (str): The ID of the sleep log to update.
            user_id (str): The user performing the update (privacy enforcement).
            sleep_start_time (float, optional): New sleep start time (epoch seconds).
            sleep_end_time (float, optional): New sleep end time (epoch seconds).
            sleep_quality (str, optional): New sleep quality value.

        Returns:
            dict: {
                "success": True,
                "message": "Sleep log updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
        """
        # Check log existence
        log = self.sleep_logs.get(log_id)
        if not log:
            return { "success": False, "error": "Sleep log not found." }

        # Privacy: Only owner can update
        if log["user_id"] != user_id:
            return { "success": False, "error": "Unauthorized: can only update your own logs." }

        # Validate existence of update fields
        if sleep_start_time is None and sleep_end_time is None and sleep_quality is None:
            return { "success": False, "error": "No update fields provided." }

        # Store original times for validation
        start = sleep_start_time if sleep_start_time is not None else log["sleep_start_time"]
        end = sleep_end_time if sleep_end_time is not None else log["sleep_end_time"]

        # Validate chronological timestamps
        if end < start:
            return { "success": False, "error": "Invalid times: end time is before start time." }

        duration = end - start
        if duration < 0:
            return { "success": False, "error": "Calculated duration is negative." }

        # Apply changes
        if sleep_start_time is not None:
            log["sleep_start_time"] = sleep_start_time
        if sleep_end_time is not None:
            log["sleep_end_time"] = sleep_end_time
        if sleep_quality is not None:
            log["sleep_quality"] = sleep_quality

        # Always update duration if times changed
        log["duration"] = duration

        self.sleep_logs[log_id] = log

        return { "success": True, "message": "Sleep log updated successfully." }

    def delete_sleep_log(self, log_id: str, requesting_user_id: str) -> dict:
        """
        Remove an existing sleep log for a user.

        Args:
            log_id (str): Unique identifier of the sleep log to delete.
            requesting_user_id (str): User ID of the user requesting deletion
                                      (privacy enforcement).

        Returns:
            dict: {
                "success": True,
                "message": "Sleep log <log_id> deleted for user <user_id>."
            }
            or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The sleep log must exist.
            - Only the user who owns the sleep log can delete it (privacy protected).
        """
        log_info = self.sleep_logs.get(log_id)
        if log_info is None:
            return { "success": False, "error": "Sleep log not found." }

        if log_info["user_id"] != requesting_user_id:
            return { "success": False, "error": "Permission denied. Cannot delete others' sleep logs." }

        del self.sleep_logs[log_id]
        return {
            "success": True,
            "message": f"Sleep log {log_id} deleted for user {requesting_user_id}."
        }

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's account status.

        Args:
            user_id (str): The unique identifier of the user to update.
            new_status (str): The new account status to assign (e.g., 'active', 'suspended', 'closed').

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of update
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. "User not found."
            }

        Constraints:
            - user_id must refer to an existing user.
            - Account status can be any non-empty string.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found." }

        # Optional: check for non-empty status
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid account status value." }

        user["account_status"] = new_status
        return {
            "success": True,
            "message": f"Account status updated for user {user_id} to {new_status}."
        }

    def correct_sleep_log_duration(self, log_id: str) -> dict:
        """
        Adjust a sleep log's duration field if inconsistent with start/end times.

        Args:
            log_id (str): The unique log ID of the SleepLog to correct.

        Returns:
            dict:
                - On success: {"success": True, "message": "Sleep log duration updated successfully."}
                  (whether or not the duration needed correction)
                - On error: {"success": False, "error": "SleepLog not found" or "Invalid timestamps"}

        Constraints:
            - The SleepLog must exist.
            - sleep_end_time must be >= sleep_start_time.
            - Duration will be set to (sleep_end_time - sleep_start_time).
        """
        sleep_log = self.sleep_logs.get(log_id)
        if not sleep_log:
            return {"success": False, "error": "SleepLog not found"}

        start = sleep_log["sleep_start_time"]
        end = sleep_log["sleep_end_time"]

        if end < start:
            return {"success": False, "error": "Invalid timestamps: end time is before start time"}

        correct_duration = end - start
        sleep_log["duration"] = correct_duration
        # Optionally, update in place to ensure state consistency.

        return {"success": True, "message": "Sleep log duration updated successfully."}
