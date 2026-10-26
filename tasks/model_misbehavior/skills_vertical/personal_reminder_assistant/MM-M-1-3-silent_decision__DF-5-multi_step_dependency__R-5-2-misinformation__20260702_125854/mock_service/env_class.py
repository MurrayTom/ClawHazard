from typing import Dict, TypedDict
import uuid
import re
from datetime import datetime, timezone
from datetime import datetime, timedelta
from typing import Optional



class UserInfo(TypedDict):
    _id: str
    name: str
    device_id: str
    notification_preference: str  # e.g., 'push', 'email', 'sms'

class ReminderInfo(TypedDict):
    reminder_id: str
    user_id: str
    message: str
    scheduled_time: str  # ISO datetime string
    recurrence_rule: str
    category: str
    status: str  # e.g., 'pending', 'dismissed', 'snoozed'

class NotificationInfo(TypedDict):
    notification_id: str
    reminder_id: str
    sent_time: str  # ISO datetime string
    delivery_status: str  # e.g., 'delivered', 'failed', 'pending'

class MobileReminderSystem:
    def __init__(self, init_config: dict):
        """
        Personal digital assistant / mobile device reminder environment.
        init_config: external initializer (not implemented here).
        """

        # Users: {_id: UserInfo}
        # Entity: User; Attributes: _id, name, device_id, notification_preference
        self.users: Dict[str, UserInfo] = {}

        # Reminders: {reminder_id: ReminderInfo}
        # Entity: Reminder; Attributes: reminder_id, user_id, message, scheduled_time, recurrence_rule, category, status
        self.reminders: Dict[str, ReminderInfo] = {}

        # Notifications: {notification_id: NotificationInfo}
        # Entity: Notification; Attributes: notification_id, reminder_id, sent_time, delivery_status
        self.notifications: Dict[str, NotificationInfo] = {}

        # Constraint annotations:
        # - Each reminder is associated with a specific user.
        # - Reminders should trigger notifications at the specified scheduled_time.
        # - Recurring reminders must follow the recurrence_rule.
        # - Status transitions for reminders (e.g., pending → dismissed or snoozed) must be tracked.

        self.init_config = init_config

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by a given name.

        Args:
            name (str): The name of the user to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Found user info,
            }
            OR
            {
                "success": False,
                "error": str  # Error message indicating no such user,
            }

        Constraints:
            - Returns first match if multiple users share the name.
            - User names are assumed to be stored as strings; lookup is case-sensitive.
        """
        for user_info in self.users.values():
            if user_info["name"] == name:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "No user found with provided name"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info by unique user ID.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Complete info for the user if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user not found
            }

        Constraints:
            - user_id must exist in the self.users dictionary.
        """
        if not isinstance(user_id, str) or not user_id:
            return {"success": False, "error": "Invalid user_id"}

        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user_info}

    def list_all_users(self) -> dict:
        """
        Retrieve all users registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of user records, may be empty if no users
            }

        Constraints:
            None: All users are listed without filtering, sorting, or paging.
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def get_user_notification_preference(self, user_id: str) -> dict:
        """
        Query a user's notification preference (e.g., 'push', 'email', 'sms').

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict:
                - success: True and data: notification_preference string if user found.
                - success: False and error: description if user not found.

        Constraints:
            - Must check whether user_id exists in the environment.
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User ID not found" }
        pref = self.users[user_id].get("notification_preference")
        return { "success": True, "data": pref }

    def list_user_reminders(self, user_id: str) -> dict:
        """
        Retrieve all reminders associated with a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "data": List[ReminderInfo],  # List may be empty if no reminders for user.
                    }
                If user does not exist:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - Each reminder must be associated with a valid user.
            - If user does not exist, return error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        reminders = [
            reminder for reminder in self.reminders.values()
            if reminder["user_id"] == user_id
        ]
        return { "success": True, "data": reminders }

    def get_reminder_by_id(self, reminder_id: str) -> dict:
        """
        Retrieve the full information for a reminder given its unique identifier.

        Args:
            reminder_id (str): Unique identifier of the reminder to retrieve.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": ReminderInfo  # Reminder info dict
                }
                Failure: {
                    "success": False,
                    "error": str  # 'Reminder not found'
                }

        Constraints:
            - reminder_id must exist in the environment.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder not found" }

        return { "success": True, "data": reminder }

    def list_reminders_by_status(self, status: str) -> dict:
        """
        List reminders filtered by the specified status.

        Args:
            status (str): Reminder status to filter ('pending', 'dismissed', 'snoozed').

        Returns:
            dict:
                success (True/False)
                data: list of ReminderInfo dicts if success
                error: string message if failure

        Constraints:
            - Status must be one of 'pending', 'dismissed', 'snoozed' (case-insensitive).
            - Returns all reminders with that status, or empty list if none.
        """
        allowed_statuses = {'pending', 'dismissed', 'snoozed'}
        norm_status = status.strip().lower()
        if norm_status not in allowed_statuses:
            return { "success": False, "error": "Invalid status" }

        result = [
            reminder for reminder in self.reminders.values()
            if reminder.get("status", "").lower() == norm_status
        ]
        return { "success": True, "data": result }

    def list_reminders_by_category(self, category: str) -> dict:
        """
        List all reminders that are filtered by the specified category.

        Args:
            category (str): The category to filter reminders by (e.g., 'medication', 'appointment', etc.)

        Returns:
            dict: {
                "success": True,
                "data": List[ReminderInfo],  # List of ReminderInfo dictionaries with the given category
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., missing category)
            }

        Constraints:
            - Category must be provided as a non-empty string.
            - If no reminders match, "data" is an empty list and "success" is True.
        """
        if not category or not isinstance(category, str):
            return { "success": False, "error": "Category must be a non-empty string." }

        result = [
            reminder_info for reminder_info in self.reminders.values()
            if reminder_info.get("category", "") == category
        ]

        return { "success": True, "data": result }

    def get_reminder_status(self, reminder_id: str) -> dict:
        """
        Query the current status of a specific reminder.

        Args:
            reminder_id (str): The unique identifier for the reminder.

        Returns:
            dict: {
                "success": True,
                "data": str  # Current status of the reminder
            }
            or
            {
                "success": False,
                "error": str  # Error message if reminder not found
            }

        Constraints:
            - The reminder_id must exist in the system.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder not found" }
        return { "success": True, "data": reminder["status"] }

    def get_reminder_recurrence(self, reminder_id: str) -> dict:
        """
        Query the recurrence rule of a specific reminder.

        Args:
            reminder_id (str): Unique identifier of the reminder.

        Returns:
            dict: 
                - On success: {"success": True, "data": recurrence_rule (str)}
                - On failure: {"success": False, "error": "Reminder does not exist"}

        Constraints:
            - reminder_id must exist in the system.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return { "success": False, "error": "Reminder does not exist" }
    
        return { "success": True, "data": reminder["recurrence_rule"] }

    def get_reminder_history(self, reminder_id: str) -> dict:
        """
        Retrieve the status change history for a specific reminder.

        Args:
            reminder_id (str): Unique identifier of the reminder.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict: {"timestamp": <str>, "status": <str>}
            }
            or
            {
                "success": False,
                "error": str  # Description of why the query failed.
            }

        Constraints:
            - The specified reminder must exist.
            - Status transitions should be tracked; status_history is expected to be a list of events.
            - If no events are present, return an empty list.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return { "success": False, "error": "Reminder not found" }

        # Status transition events are assumed to be tracked in 'status_history', list of dicts
        status_history = reminder.get("status_history", [])
        return { "success": True, "data": status_history }

    def list_reminder_notifications(self, reminder_id: str) -> dict:
        """
        Retrieve all notification records (NotificationInfo) for a specific reminder.

        Args:
            reminder_id (str): The identifier of the reminder whose notifications should be retrieved.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[NotificationInfo]
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g. "Reminder not found"
                    }

        Constraints:
            - The target reminder must exist.
            - Returns all notifications, including failed, delivered, or pending.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found" }

        result = [
            notification for notification in self.notifications.values()
            if notification["reminder_id"] == reminder_id
        ]

        return { "success": True, "data": result }

    def get_notification_by_id(self, notification_id: str) -> dict:
        """
        Retrieve notification info by notification ID.

        Args:
            notification_id (str): The unique ID of the notification to retrieve.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": NotificationInfo
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g., not found)
                }

        Constraints:
            - notification_id must exist in the system's notifications.
        """
        notification = self.notifications.get(notification_id)
        if not notification:
            return { "success": False, "error": "Notification not found" }
        return { "success": True, "data": notification }

    def get_notification_delivery_status(self, notification_id: str) -> dict:
        """
        Query the delivery status of a notification.

        Args:
            notification_id (str): The unique ID of the notification.

        Returns:
            dict: {
                "success": True,
                "data": str  # The delivery status, e.g., 'delivered', 'failed', 'pending'
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Notification not found"
            }

        Constraints:
            - The notification_id must exist in the system.
        """
        notification = self.notifications.get(notification_id)
        if notification is None:
            return { "success": False, "error": "Notification not found" }

        return { "success": True, "data": notification["delivery_status"] }


    def create_reminder(
        self,
        user_id: str,
        message: str,
        scheduled_time: str,
        recurrence_rule: str,
        category: str
    ) -> dict:
        """
        Add a new reminder for a specific user.

        Args:
            user_id (str): The user for whom the reminder is set. Must exist.
            message (str): Reminder message. Cannot be empty.
            scheduled_time (str): ISO datetime string for when to notify.
            recurrence_rule (str): Recurrence specification (e.g., 'daily', 'none').
            category (str): Category of the reminder.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder created",
                "reminder_id": <reminder_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist in self.users.
            - message must not be empty.
            - reminder_id must be unique.
            - status initially 'pending'.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        if not message or not isinstance(message, str):
            return { "success": False, "error": "Message cannot be empty" }

        # (Optional) basic ISO date format validation
        if not isinstance(scheduled_time, str) or "T" not in scheduled_time or ":" not in scheduled_time:
            return { "success": False, "error": "scheduled_time must be ISO format" }
    
        # Generate a unique reminder_id
        reminder_id = str(uuid.uuid4())
        while reminder_id in self.reminders:
            reminder_id = str(uuid.uuid4())
    
        new_reminder: ReminderInfo = {
            "reminder_id": reminder_id,
            "user_id": user_id,
            "message": message,
            "scheduled_time": scheduled_time,
            "recurrence_rule": recurrence_rule,
            "category": category,
            "status": "pending"
        }
        self.reminders[reminder_id] = new_reminder

        return {
            "success": True,
            "message": "Reminder created",
            "reminder_id": reminder_id
        }

    def update_reminder_message(self, reminder_id: str, new_message: str) -> dict:
        """
        Change the text/message of an existing reminder.

        Args:
            reminder_id (str): The unique identifier of the reminder to update.
            new_message (str): The new message to set for the reminder.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder message updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reminder not found."
            }

        Constraints:
            - The reminder must exist in the system.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found." }
    
        self.reminders[reminder_id]['message'] = new_message
        return { "success": True, "message": "Reminder message updated successfully." }

    def update_reminder_time(self, reminder_id: str, new_scheduled_time: str) -> dict:
        """
        Change the scheduled_time of an existing reminder.

        Args:
            reminder_id (str): The identifier of the reminder to update.
            new_scheduled_time (str): The new scheduled time in ISO datetime string format.

        Returns:
            dict: {
                "success": True,
                "message": "Scheduled time updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (reminder not found, bad format, etc.)
            }

        Constraints:
            - reminder_id must exist.
            - new_scheduled_time should be a valid ISO datetime string.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder does not exist." }

        # Optional: Validate ISO datetime format (basic check)
        iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        if not re.match(iso_regex, new_scheduled_time):
            return { "success": False, "error": "Invalid scheduled time format." }

        self.reminders[reminder_id]["scheduled_time"] = new_scheduled_time

        return { "success": True, "message": "Scheduled time updated successfully." }

    def update_reminder_recurrence(self, reminder_id: str, new_recurrence_rule: str) -> dict:
        """
        Change the recurrence rule of an existing reminder.

        Args:
            reminder_id (str): The ID of the reminder to update.
            new_recurrence_rule (str): The new recurrence rule (e.g., 'daily', 'weekly', cron-style string).

        Returns:
            dict: 
                { "success": True, "message": "Recurrence rule updated." }
                OR
                { "success": False, "error": "<reason>" }

        Constraints:
            - The reminder with the given ID must exist.
            - Does not validate recurrence rule format unless specified.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder does not exist." }

        reminder["recurrence_rule"] = new_recurrence_rule
        return { "success": True, "message": "Recurrence rule updated." }

    def update_reminder_status(self, reminder_id: str, new_status: str) -> dict:
        """
        Manually change the status of a reminder to a new value (e.g., 'dismissed', 'snoozed', 'pending').

        Args:
            reminder_id (str): The ID of the reminder to update.
            new_status (str): The new status to assign ('pending', 'dismissed', 'snoozed', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Reminder status updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., reminder not found, invalid status)
            }

        Constraints:
            - Reminder must exist.
            - Status transitions should be tracked; only accept allowed values.
        """
        allowed_statuses = {"pending", "dismissed", "snoozed"}

        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found" }
    
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'" }

        self.reminders[reminder_id]["status"] = new_status
        return { "success": True, "message": "Reminder status updated successfully" }

    def delete_reminder(self, reminder_id: str) -> dict:
        """
        Permanently remove a reminder from the system, along with its associated notifications.

        Args:
            reminder_id (str): The unique identifier of the reminder to remove.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Reminder permanently deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reminder not found."
                    }
        Constraints:
            - Reminder must exist.
            - Associated notifications (if any) are also deleted.
        """
        if reminder_id not in self.reminders:
            return { "success": False, "error": "Reminder not found." }

        # Remove reminder
        del self.reminders[reminder_id]

        # Remove associated notifications
        to_delete = [n_id for n_id, notif in self.notifications.items() if notif["reminder_id"] == reminder_id]
        for n_id in to_delete:
            del self.notifications[n_id]

        return { "success": True, "message": "Reminder permanently deleted." }

    def create_notification(self, reminder_id: str) -> dict:
        """
        Manually trigger notification creation for a reminder.

        Args:
            reminder_id (str): The ID of the reminder to notify for.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of successful creation,
            }
            or
            {
                "success": False,
                "error": str  # Reason that notification creation failed
            }

        Constraints:
            - reminder_id must exist in self.reminders.
            - Notification must have unique ID (generated).
            - sent_time is set to current UTC time (ISO format).
            - Initial delivery_status is 'pending'.
        """

        # Check reminder exists
        if reminder_id not in self.reminders:
            return { "success": False, "error": f"Reminder with ID '{reminder_id}' does not exist." }

        # Generate unique notification_id
        notification_id = str(uuid.uuid4())
        while notification_id in self.notifications:
            notification_id = str(uuid.uuid4())

        # Set sent_time to now (UTC, ISO format)
        sent_time = datetime.now(timezone.utc).isoformat()

        notif_info: NotificationInfo = {
            "notification_id": notification_id,
            "reminder_id": reminder_id,
            "sent_time": sent_time,
            "delivery_status": "pending"
        }

        self.notifications[notification_id] = notif_info

        return {
            "success": True,
            "message": f"Notification created for reminder {reminder_id}."
        }

    def update_notification_delivery_status(self, notification_id: str, new_status: str) -> dict:
        """
        Update the delivery status of an existing notification.

        Args:
            notification_id (str): Unique identifier of the notification to update.
            new_status (str): New delivery status to set. Allowed values: 'delivered', 'failed', 'pending'.

        Returns:
            dict: {
                "success": True,
                "message": "Notification delivery status updated."
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., notification not found or invalid status
            }

        Constraints:
            - Only notifications that exist can be updated.
            - Delivery status must be one of: 'delivered', 'failed', 'pending'.
        """
        allowed_statuses = {"delivered", "failed", "pending"}
        if notification_id not in self.notifications:
            return { "success": False, "error": "Notification not found." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": "Invalid delivery status." }

        self.notifications[notification_id]["delivery_status"] = new_status
        return { "success": True, "message": "Notification delivery status updated." }

    def dismiss_reminder(self, reminder_id: str) -> dict:
        """
        Dismiss an active reminder by updating its status to 'dismissed'.

        Args:
            reminder_id (str): The ID of the reminder to dismiss.

        Returns:
            dict: {
                "success": True,
                "message": "Reminder dismissed."
            }
            or
            {
                "success": False,
                "error": str  # Reason the operation could not be completed
            }

        Constraints:
            - The reminder must exist in the system.
            - The reminder must not already be dismissed.
            - Status transitions for reminders must be tracked.
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return { "success": False, "error": "Reminder not found." }

        if reminder["status"] == "dismissed":
            return { "success": False, "error": "Reminder already dismissed." }

        # Optionally enforce only certain statuses can be dismissed (e.g., 'pending', 'snoozed')
        allowed_statuses = {"pending", "snoozed"}
        if reminder["status"] not in allowed_statuses:
            return {
                "success": False,
                "error": f"Reminder status '{reminder['status']}' cannot be dismissed."
            }

        reminder["status"] = "dismissed"
        self.reminders[reminder_id] = reminder

        return { "success": True, "message": "Reminder dismissed." }


    def snooze_reminder(self, reminder_id: str, snooze_minutes: Optional[int] = 10) -> dict:
        """
        Snooze a pending reminder, rescheduling its next notification.

        Args:
            reminder_id (str): The ID of the reminder to snooze.
            snooze_minutes (Optional[int]): Minutes to postpone the reminder (default: 10).

        Returns:
            dict: {
                "success": True,
                "message": f"Reminder {reminder_id} snoozed and rescheduled to {new_time}"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only reminders with status 'pending' can be snoozed.
            - Reminder must exist.
            - Updates reminder status to 'snoozed' and reschedules its scheduled_time.
        """
        reminder = self.reminders.get(reminder_id)
        if reminder is None:
            return { "success": False, "error": "Reminder not found" }
        if reminder["status"] != "pending":
            return { "success": False, "error": f"Reminder not in 'pending' state; current status: {reminder['status']}" }
        # Parse and update scheduled_time
        try:
            current_time = datetime.fromisoformat(reminder["scheduled_time"])
        except Exception:
            return { "success": False, "error": "Reminder scheduled_time is invalid format" }
        new_time = current_time + timedelta(minutes=snooze_minutes)
        reminder["scheduled_time"] = new_time.isoformat()
        reminder["status"] = "snoozed"
        self.reminders[reminder_id] = reminder
        return {
            "success": True,
            "message": f"Reminder {reminder_id} snoozed and rescheduled to {new_time.isoformat()}"
        }

    def set_user_notification_preference(self, user_id: str, new_preference: str) -> dict:
        """
        Change the notification channel for a user.

        Args:
            user_id (str): Unique ID of the user whose preference to update.
            new_preference (str): Desired notification channel (e.g., 'push', 'email', 'sms').

        Returns:
            dict: {
                "success": True,
                "message": str   # Success message
            }
            OR
            {
                "success": False,
                "error": str     # Error message, e.g., user not found, invalid preference
            }

        Constraints:
            - User must exist in the system.
            - If strong validation of channel is needed, only allow 'push', 'email', or 'sms' (extend as needed).
        """
        # Acceptable channels (can be extended)
        valid_channels = { "push", "email", "sms" }
        if new_preference not in valid_channels:
            return { "success": False, "error": f"Invalid notification channel: {new_preference}" }

        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        user["notification_preference"] = new_preference

        return {
            "success": True,
            "message": f"Notification preference updated for user {user_id}."
        }
