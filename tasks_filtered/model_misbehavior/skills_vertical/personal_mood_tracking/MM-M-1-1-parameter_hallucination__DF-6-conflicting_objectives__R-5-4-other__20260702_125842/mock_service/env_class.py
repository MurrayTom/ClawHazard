from typing import Dict, TypedDict
import time
import uuid
from typing import Optional, Dict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    account_info: str

class MoodEntryInfo(TypedDict):
    entry_id: str
    user_id: str
    mood_type: str
    timestamp: float
    description: str
    metadata: dict

class MoodTypeInfo(TypedDict):
    mood_type_id: str
    label: str
    color: str
    emoji: str

class PersonalMoodTrackingApplication:
    def __init__(self, init_config: dict):
        """
        Environment: Personal Mood Tracking Application
        """

        # Users: {_id: UserInfo}
        # Maps user IDs to user details.
        self.users: Dict[str, UserInfo] = {}

        # Mood Entries: {entry_id: MoodEntryInfo}
        # Maps entry IDs to mood records.
        self.mood_entries: Dict[str, MoodEntryInfo] = {}

        # Mood Types: {mood_type_id: MoodTypeInfo}
        # Maps possible moods to their definitions.
        self.mood_types: Dict[str, MoodTypeInfo] = {}

        # Constraints (to be enforced in logic):
        # - Each MoodEntry must be associated with a valid User.
        # - MoodEntry timestamps must not be in the future.
        # - Only valid MoodTypes can be recorded in MoodEntry.
        # - Users may only edit or delete their own MoodEntries.

        self.init_config = init_config

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve a user's information using their name.

        Args:
            name (str): The name of the user to look up.

        Returns:
            dict: 
                {"success": True, "data": UserInfo}   # If found
                or 
                {"success": False, "error": str}      # If not found

        Constraints:
            - Name matching is case-sensitive.
            - Returns the first match if multiple users share the same name.
        """

        for user_info in self.users.values():
            if user_info["name"] == name:
                return {"success": True, "data": user_info}

        return {"success": False, "error": "No user found with the given name"}

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user details by their unique ID.

        Args:
            _id (str): The user's unique identifier.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": UserInfo  # User details
                }
                On failure: {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - User ID must exist in the system.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_mood_types(self) -> dict:
        """
        Lists all valid mood types with their label, color, and emoji.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MoodTypeInfo]  # May be empty if there are no mood types defined
            }

        Notes:
            - If no mood types exist in the system, returns an empty list.
        """
        result = list(self.mood_types.values())
        return { "success": True, "data": result }

    def get_mood_type_by_id(self, mood_type_id: str) -> dict:
        """
        Retrieve details of a mood type by its unique mood_type_id.

        Args:
            mood_type_id (str): The identifier of the mood type to fetch.

        Returns:
            dict:
              - On success: {"success": True, "data": MoodTypeInfo}
              - On failure: {"success": False, "error": "Mood type not found"}

        Constraints:
            - mood_type_id must exist in self.mood_types.
        """
        mood_type = self.mood_types.get(mood_type_id)
        if not mood_type:
            return {"success": False, "error": "Mood type not found"}
        return {"success": True, "data": mood_type}

    def list_user_mood_entries(self, user_id: str) -> dict:
        """
        Retrieve all mood entries for the specified user.

        Args:
            user_id (str): The unique identifier of the User.

        Returns:
            dict:
                - If user exists: {
                    "success": True,
                    "data": List[MoodEntryInfo]  # All mood entries for this user (may be empty)
                  }
                - If user does not exist: {
                    "success": False,
                    "error": "User does not exist"
                  }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        results = [
            entry for entry in self.mood_entries.values()
            if entry["user_id"] == user_id
        ]

        return { "success": True, "data": results }

    def get_mood_entry_by_id(self, entry_id: str) -> dict:
        """
        Retrieve the details of a mood entry by its entry_id.

        Args:
            entry_id (str): The unique identifier of the mood entry.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": MoodEntryInfo  # The complete mood entry data.
                }
            or
                {
                    "success": False,
                    "error": str  # Reason, e.g., "Mood entry not found"
                }

        Constraints:
            - entry_id must exist in mood_entries.
        """
        if entry_id not in self.mood_entries:
            return { "success": False, "error": "Mood entry not found" }
        entry = self.mood_entries[entry_id]
        return { "success": True, "data": entry }

    def filter_mood_entries_by_time(self, user_id: str, start_time: float, end_time: float) -> dict:
        """
        Fetch mood entries within a specific (inclusive) time range for a user.

        Args:
            user_id (str): The user's unique ID.
            start_time (float): The lower-bound Unix timestamp (inclusive).
            end_time (float): The upper-bound Unix timestamp (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[MoodEntryInfo]  # All matching entries for user in time range (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: user not found, etc.
            }

        Constraints:
            - User must exist.
            - start_time and end_time are inclusive bounds.
            - If start_time > end_time, returns empty list.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        if start_time > end_time:
            return { "success": True, "data": [] }

        result = [
            entry for entry in self.mood_entries.values()
            if entry["user_id"] == user_id and start_time <= entry["timestamp"] <= end_time
        ]

        return { "success": True, "data": result }

    def filter_mood_entries_by_type(self, user_id: str, mood_type_id: str) -> dict:
        """
        Retrieve all mood entries for a specific user that match a specific mood type.

        Args:
            user_id (str): The ID of the user whose entries to filter.
            mood_type_id (str): The mood type ID to filter entries by.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": [MoodEntryInfo, ...]  # List of matching mood entry infos (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of error (invalid user or mood type)
                }
        Constraints:
            - user_id must exist in self.users
            - mood_type_id must exist in self.mood_types
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if mood_type_id not in self.mood_types:
            return { "success": False, "error": "Mood type does not exist" }

        result = [
            entry for entry in self.mood_entries.values()
            if entry["user_id"] == user_id and entry["mood_type"] == mood_type_id
        ]
        return { "success": True, "data": result }


    def add_mood_entry(
        self, 
        user_id: str, 
        mood_type: str, 
        description: str = "", 
        metadata: Optional[Dict[str, Any]] = None, 
        timestamp: Optional[float] = None
    ) -> dict:
        """
        Create a new mood entry for a user.

        Args:
            user_id (str): The ID of the user recording the mood.
            mood_type (str): The mood type to record (must exist in MoodTypes).
            description (str): Optional notes about the mood entry.
            metadata (dict, optional): Additional metadata. Defaults to empty dict.
            timestamp (float, optional): Unix timestamp for the mood entry. If None, uses current time.

        Returns:
            dict: 
                {"success": True, "message": "Mood entry created with id <entry_id>"}
            or
                {"success": False, "error": "reason"}
    
        Constraints:
            - User must exist.
            - MoodType must exist.
            - Timestamp must not be in the future.
        """
        now = time.time()
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if mood_type not in self.mood_types:
            return { "success": False, "error": "Mood type does not exist" }
        if timestamp is None:
            timestamp = now
        if timestamp > now + 1:  # Allow 1-second tolerance for clock skew
            return { "success": False, "error": "Timestamp is in the future" }
        entry_id = str(uuid.uuid4())
        if metadata is None or not isinstance(metadata, dict):
            metadata = {}
        mood_entry = {
            "entry_id": entry_id,
            "user_id": user_id,
            "mood_type": mood_type,
            "timestamp": timestamp,
            "description": description,
            "metadata": metadata
        }
        self.mood_entries[entry_id] = mood_entry
        return { "success": True, "message": f"Mood entry created with id {entry_id}" }

    def edit_mood_entry(
        self,
        entry_id: str,
        user_id: str,
        description: str = None,
        mood_type: str = None,
        metadata: dict = None,
        timestamp: float = None
    ) -> dict:
        """
        Update description, mood_type, metadata, or timestamp of a user's own mood entry.

        Args:
            entry_id (str): ID of the mood entry to edit.
            user_id (str): ID of the user requesting the edit.
            description (str, optional): New description.
            mood_type (str, optional): New mood_type. Must be valid.
            metadata (dict, optional): New metadata.
            timestamp (float, optional): New timestamp. Must not be in the future.

        Returns:
            dict: {
                "success": True,
                "message": "Mood entry updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - Only the owner can edit their mood entry.
            - Only valid mood types may be set.
            - Timestamps cannot be in the future.
        """

        if entry_id not in self.mood_entries:
            return {"success": False, "error": "Mood entry not found."}

        entry = self.mood_entries[entry_id]

        if entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: You can only edit your own mood entries."}

        # No fields to update
        if all(arg is None for arg in [description, mood_type, metadata, timestamp]):
            return {"success": False, "error": "No fields provided to update."}

        # Mood type check
        if mood_type is not None and mood_type not in self.mood_types:
            return {"success": False, "error": "Invalid mood_type specified."}

        # Timestamp check
        if timestamp is not None:
            now = time.time()
            if timestamp > now:
                return {"success": False, "error": "Timestamp cannot be in the future."}
            entry["timestamp"] = timestamp

        # Update other fields
        if description is not None:
            entry["description"] = description
        if mood_type is not None:
            entry["mood_type"] = mood_type
        if metadata is not None:
            entry["metadata"] = metadata

        self.mood_entries[entry_id] = entry
        return {"success": True, "message": "Mood entry updated successfully."}

    def delete_mood_entry(self, entry_id: str, current_user_id: str) -> dict:
        """
        Remove a mood entry, if and only if it belongs to the current user.

        Args:
            entry_id (str): Unique identifier for the mood entry to be deleted.
            current_user_id (str): User ID of the user requesting deletion.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Mood entry deleted successfully."
                }
                On error:
                {
                    "success": False,
                    "error": str  # Error message
                }

        Constraints:
            - Only the user who owns the mood entry may delete it.
            - If the entry doesn't exist, return a failure result.
        """
        entry = self.mood_entries.get(entry_id)
        if entry is None:
            return { "success": False, "error": "Mood entry not found." }

        if entry["user_id"] != current_user_id:
            return { "success": False, "error": "Permission denied: Cannot delete another user's mood entry." }

        del self.mood_entries[entry_id]

        return { "success": True, "message": "Mood entry deleted successfully." }

    def bulk_delete_user_mood_entries(self, user_id: str, entry_ids: list) -> dict:
        """
        Remove multiple mood entries belonging to the specified user.

        Args:
            user_id (str): The ID of the user whose mood entries should be deleted.
            entry_ids (list of str): List of mood entry IDs to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Deleted X of Y requested entries for user <user_id>.",
                "deleted_entries": List[str],  # Entry IDs that were actually deleted
                "skipped_entries": List[str],  # Entry IDs not deleted (not found or not belonging to user)
            }
            or
            {
                "success": False,
                "error": str  # e.g. user does not exist
            }

        Constraints:
            - Only mood entries belonging to the specified user will be deleted.
            - Entries that do not exist or do not belong to the user are skipped.
            - If user_id does not exist, operation fails.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        deleted_entries = []
        skipped_entries = []

        for entry_id in entry_ids:
            entry_info = self.mood_entries.get(entry_id)
            if entry_info is None:
                skipped_entries.append(entry_id)
            elif entry_info["user_id"] != user_id:
                skipped_entries.append(entry_id)
            else:
                # Entry belongs to user and exists; delete
                del self.mood_entries[entry_id]
                deleted_entries.append(entry_id)

        total_requested = len(entry_ids)
        total_deleted = len(deleted_entries)
        message = f"Deleted {total_deleted} of {total_requested} requested entries for user {user_id}."
        return {
            "success": True,
            "message": message,
            "deleted_entries": deleted_entries,
            "skipped_entries": skipped_entries,
        }

    def change_mood_type_label(
        self,
        mood_type_id: str,
        label: str = None,
        color: str = None,
        emoji: str = None
    ) -> dict:
        """
        Modify the label or other properties (color, emoji) of an existing MoodType.
        Only valid properties (label, color, emoji) can be modified.

        Args:
            mood_type_id (str): The ID of the mood type to modify.
            label (str, optional): New label for the mood type.
            color (str, optional): New color for the mood type.
            emoji (str, optional): New emoji for the mood type.

        Returns:
            dict: {
                "success": True,
                "message": "Mood type properties updated"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - mood_type_id must exist in mood_types.
            - At least one property to update (label, color, emoji) must be provided.
            - Only label, color, emoji can be modified.
        """
        if mood_type_id not in self.mood_types:
            return { "success": False, "error": "Mood type not found" }

        if label is None and color is None and emoji is None:
            return { "success": False, "error": "No update properties provided" }

        allowed_fields = ["label", "color", "emoji"]
        updated = False

        if label is not None:
            self.mood_types[mood_type_id]["label"] = label
            updated = True
        if color is not None:
            self.mood_types[mood_type_id]["color"] = color
            updated = True
        if emoji is not None:
            self.mood_types[mood_type_id]["emoji"] = emoji
            updated = True

        # Should always be True here since we've already checked for non-None
        return { "success": True, "message": "Mood type properties updated" }

    def restore_deleted_mood_entry(self, entry_id: str, user_id: str) -> dict:
        """
        Reinstate a previously deleted mood entry (if deletion is a soft delete or undo is supported).

        Args:
            entry_id (str): The ID of the mood entry to restore.
            user_id (str): The ID of the user requesting restoration.

        Returns:
            dict: {
                "success": True,
                "message": f"Mood entry {entry_id} successfully restored."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only owners may restore their own deleted entries.
            - Entry must exist and be marked deleted (soft delete).
            - Entry must reference a valid user and valid mood type (if applicable).
        """
        entry = self.mood_entries.get(entry_id)
        if entry is None:
            return {"success": False, "error": "Mood entry does not exist."}

        # Ensure there is a 'deleted' flag (if not, assume not deleted).
        deleted_flag = entry.get("deleted", False)
        if not deleted_flag:
            return {"success": False, "error": "Mood entry is not deleted or restore is not supported."}

        # Check that the user exists.
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist."}

        # Check ownership.
        if entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: cannot restore others' mood entries."}

        # Check mood type still valid
        mood_type_id = entry["mood_type"]
        if mood_type_id not in self.mood_types:
            return {"success": False, "error": "Mood type associated with entry no longer exists."}

        # Restore (set deleted=False)
        entry["deleted"] = False
        self.mood_entries[entry_id] = entry

        return {
            "success": True,
            "message": f"Mood entry {entry_id} successfully restored."
        }
