from typing import Dict, List, TypedDict, Any
import uuid
import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    password_hash: str
    registration_date: str
    profile_info: Any  # Assume dict or str for now
    active_sta: str    # Interpreted as 'active_status'

class ChallengeInfo(TypedDict):
    challenge_id: str
    name: str
    description: str
    start_date: str
    end_date: str
    criteria: str

class ActivityLogInfo(TypedDict):
    log_id: str
    user_id: str
    challenge_id: str
    activity_type: str
    value: float
    timestamp: str

class LeaderboardEntryInfo(TypedDict):
    challenge_id: str
    user_id: str
    score: float
    rank: int

class FitnessChallengePlatform:
    def __init__(self, init_config: dict):
        """
        Fitness challenge platform stateful environment.
        init_config: external environment initializer (not implemented).
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Challenges: {challenge_id: ChallengeInfo}
        self.challenges: Dict[str, ChallengeInfo] = {}

        # Activity Logs: {log_id: ActivityLogInfo}
        self.activity_logs: Dict[str, ActivityLogInfo] = {}

        # Leaderboards: {challenge_id: List[LeaderboardEntryInfo]}
        self.leaderboards: Dict[str, List[LeaderboardEntryInfo]] = {}

        # Constraints:
        # - Usernames and emails must be unique.
        # - User accounts must be verified/activated before participating in challenges.
        # - Each activity log must be assigned to a valid user and challenge.
        # - Leaderboard updates are based on valid, verified activity logs.

        self.init_config = init_config

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve a user's information using their unique username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Full user information for the matching username,
            }
            or
            {
                "success": False,
                "error": str  # If username does not exist
            }

        Constraints:
            - Username must be unique across all users.
            - Returns only the user with the exact matching username, or error if not found.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User with this username does not exist" }

    def get_user_by_email(self, email: str) -> dict:
        """
        Retrieve a user's information using their email address.

        Args:
            email (str): The email address of the user to fetch.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": UserInfo  # The user's info, if found
                  }
                - On failure: {
                    "success": False,
                    "error": "No user found with this email"
                  }

        Constraints:
            - Emails must be unique per user, so at most one result.
        """
        for user_info in self.users.values():
            if user_info["email"] == email:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "No user found with this email"}

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve details for a user given their unique _id.

        Args:
            _id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User's information as dict
            }
            or
            {
                "success": False,
                "error": str  # 'User not found' if _id is invalid
            }

        Constraints:
            - The provided _id must exist in the platform's users.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all registered users on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],   # List of all registered users, may be empty
            }

        Constraints:
            - No input constraints.
            - Returns all user accounts with full metadata.
        """
        return {
            "success": True,
            "data": list(self.users.values())
        }

    def check_user_active_status(self, user_id: str) -> dict:
        """
        Check whether a given user account is activated/verified.

        Args:
            user_id (str): The unique user identifier (_id) to check.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": {
                        "active_status": str,     # Value of the active_sta field
                        "is_activated": bool      # True if user is considered active/verified
                    }
                }
                or
                {
                    "success": False,
                    "error": str  # Description of error (e.g. user not found)
                }

        Constraints:
            - The user must exist.
            - Convention: "active_sta" value of "active" means account is activated/verified.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
    
        status = user.get("active_sta", None)
        # Define what "activated" means. Convention: "active_sta" == "active" means activated.
        is_activated = str(status).lower() == "active"
        return {
            "success": True,
            "data": {
                "active_status": status,
                "is_activated": is_activated
            }
        }

    def list_challenges(self) -> dict:
        """
        Retrieve information on all fitness challenges available on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ChallengeInfo],  # List of all challenge info; may be empty if none exist
            }
        Constraints:
            - No constraints for this query; returns all challenge entries.
        """
        challenges_list = list(self.challenges.values())
        return { "success": True, "data": challenges_list }

    def get_challenge_by_id(self, challenge_id: str) -> dict:
        """
        Retrieve the full details (metadata) for a specific fitness challenge.

        Args:
            challenge_id (str): The unique identifier of the challenge to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ChallengeInfo,  # Challenge metadata, if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure; e.g., not found
            }

        Constraints:
            - Challenge must exist in the system.
        """
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return { "success": False, "error": "Challenge not found" }
        return { "success": True, "data": challenge }

    def get_user_activity_logs(self, user_id: str) -> dict:
        """
        List all activity logs associated with the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[ActivityLogInfo]  # List of activity logs (empty if no logs)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g. if user not found
                    }

        Constraints:
            - The user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        logs = [
            log for log in self.activity_logs.values()
            if log["user_id"] == user_id
        ]

        return {
            "success": True,
            "data": logs
        }

    def list_challenge_activity_logs(self, challenge_id: str) -> dict:
        """
        List all activity logs submitted for a specific challenge.

        Args:
            challenge_id (str): The unique identifier of the challenge.

        Returns:
            dict:
                - success: True if query succeeds, with
                  data: List of ActivityLogInfo dicts for the given challenge (may be empty).
                - success: False, with
                  error: Reason for failure (e.g., challenge does not exist).

        Constraints:
            - Provided challenge_id must exist in the platform.
        """
        if challenge_id not in self.challenges:
            return { "success": False, "error": "Challenge does not exist" }

        result = [
            log for log in self.activity_logs.values()
            if log["challenge_id"] == challenge_id
        ]
        return { "success": True, "data": result }

    def get_activity_log_by_id(self, log_id: str) -> dict:
        """
        Retrieve the details of a specific activity log by its log_id.

        Args:
            log_id (str): The unique identifier of the activity log.

        Returns:
            dict: {
                "success": True,
                "data": ActivityLogInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason why retrieval failed (e.g., not found)
            }

        Constraints:
            - log_id must exist within the platform's activity logs.
        """
        activity_log = self.activity_logs.get(log_id)
        if activity_log is None:
            return {"success": False, "error": "Activity log not found"}
        return {"success": True, "data": activity_log}

    def get_leaderboard_for_challenge(self, challenge_id: str) -> dict:
        """
        Retrieve the full leaderboard for the specified challenge.

        Args:
            challenge_id (str): Unique identifier for the challenge.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[LeaderboardEntryInfo]  # List may be empty if no entries
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # E.g. "Challenge does not exist"
                    }

        Constraints:
            - challenge_id must be present in self.challenges.
        """
        if challenge_id not in self.challenges:
            return { "success": False, "error": "Challenge does not exist" }
    
        leaderboard = self.leaderboards.get(challenge_id, [])
        return { "success": True, "data": leaderboard }

    def get_user_leaderboard_entry(self, challenge_id: str, user_id: str) -> dict:
        """
        Retrieve the leaderboard entry, score, and rank for a user in a specified challenge.

        Args:
            challenge_id (str): The ID of the challenge.
            user_id (str): The ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": LeaderboardEntryInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., user/challenge not found, entry missing)
            }

        Constraints:
            - challenge_id must exist in self.challenges.
            - user_id must exist in self.users.
            - User must have an entry on the leaderboard for the challenge.
        """
        if challenge_id not in self.challenges:
            return { "success": False, "error": "Challenge does not exist" }

        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        leaderboard = self.leaderboards.get(challenge_id, [])
        entry = next((e for e in leaderboard if e["user_id"] == user_id), None)

        if not entry:
            return { "success": False, "error": "No leaderboard entry found for user in this challenge" }

        return { "success": True, "data": entry }

    def create_user_account(self, username: str, email: str, password_hash: str, profile_info: Any = None) -> dict:
        """
        Register a new user account in the platform. Usernames and emails must be unique.

        Args:
            username (str): Desired unique username.
            email (str): Desired unique email address.
            password_hash (str): Secure password hash.
            profile_info (Any, optional): Initial profile details.

        Returns:
            dict: {
                "success": True,
                "message": "User account created successfully",
                "user_id": str  # Newly assigned user ID
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., username/email already exists)
            }

        Constraints:
            - Username and email must be unique.
            - Initializes account as inactive (pending activation).
        """
        # Check for unique username and email
        for u in self.users.values():
            if u["username"].lower() == username.lower():
                return { "success": False, "error": "Username already exists" }
            if u["email"].lower() == email.lower():
                return { "success": False, "error": "Email already exists" }

        # Generate unique user_id, e.g., using a counter or UUID
        new_user_id = str(uuid.uuid4())

        registration_date = datetime.datetime.utcnow().isoformat()

        user_data = {
            "_id": new_user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "registration_date": registration_date,
            "profile_info": profile_info if profile_info is not None else {},
            "active_sta": "inactive"  # New accounts start inactive
        }

        self.users[new_user_id] = user_data

        return {
            "success": True,
            "message": "User account created successfully",
            "user_id": new_user_id
        }

    def activate_user_account(self, user_id: str) -> dict:
        """
        Verify and activate a user account after registration.

        Args:
            user_id (str): The unique ID of the user whose account is to be activated.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "User account activated"
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Error description (user not found, already active, etc.)
                }
        Constraints:
            - User must exist.
            - Operation only succeeds if user is not already active.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        current_status = user.get("active_sta", None)
        if current_status == "active":
            return { "success": False, "error": "User account is already active" }

        user["active_sta"] = "active"
        return { "success": True, "message": "User account activated" }

    def update_user_profile(self, user_id: str, profile_info: Any) -> dict:
        """
        Modify a user's profile information.

        Args:
            user_id (str): ID of the user whose profile is to be updated.
            profile_info (Any): New profile information (typically a dict or str).

        Returns:
            dict: On success,
                { "success": True, "message": "User profile updated." }
                On failure,
                { "success": False, "error": "reason" }

        Constraints:
            - The user with the given user_id must exist.
            - No requirements for user activation for profile update.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }
        self.users[user_id]['profile_info'] = profile_info
        return { "success": True, "message": "User profile updated." }

    def create_challenge(
        self, 
        challenge_id: str, 
        name: str, 
        description: str, 
        start_date: str, 
        end_date: str, 
        criteria: str
    ) -> dict:
        """
        Add a new challenge event to the platform.

        Args:
            challenge_id (str): Unique identifier for the challenge (must not already exist).
            name (str): Challenge name.
            description (str): Challenge details/goal.
            start_date (str): Challenge start date (format YYYY-MM-DD or similar).
            end_date (str): Challenge end date (format YYYY-MM-DD or similar).
            criteria (str): Scoring/winning logic.

        Returns:
            dict: {
                "success": True,
                "message": "Challenge created successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - challenge_id must be unique/not already used.
        """
        # Validate challenge_id uniqueness
        if challenge_id in self.challenges:
            return { "success": False, "error": "Challenge ID already exists." }
    
        # Minimal field validation (fields cannot be empty)
        if not all([challenge_id, name, description, start_date, end_date, criteria]):
            return { "success": False, "error": "All fields are required." }
    
        # Optionally, ensure start_date <= end_date (lexical comparison suffices if using YYYY-MM-DD)
        if start_date > end_date:
            return { "success": False, "error": "Start date must not be after end date." }

        challenge_info: ChallengeInfo = {
            "challenge_id": challenge_id,
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "criteria": criteria
        }
        self.challenges[challenge_id] = challenge_info

        # Initialize leaderboard for the challenge (optional, but sensible)
        self.leaderboards[challenge_id] = []

        return { "success": True, "message": "Challenge created successfully." }

    def join_challenge(self, user_id: str, challenge_id: str) -> dict:
        """
        Register an activated user as a participant in a challenge.

        Args:
            user_id (str): The ID of the user.
            challenge_id (str): The ID of the challenge.

        Returns:
            dict: 
              Success: { "success": True, "message": "User joined challenge <challenge_id>." }
              Failure: { "success": False, "error": "Reason for failure." }

        Constraints:
            - User must exist and be activated (active_sta == "active").
            - Challenge must exist.
            - User must not already be registered for this challenge (no duplicate leaderboard entry).
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found." }

        # Check user is activated
        if user.get("active_sta") != "active":
            return { "success": False, "error": "User account is not activated." }

        # Check challenge exists
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return { "success": False, "error": "Challenge not found." }

        # Ensure leaderboard list exists for this challenge
        if challenge_id not in self.leaderboards:
            self.leaderboards[challenge_id] = []

        # Check if user is already registered (i.e., has a leaderboard entry)
        for entry in self.leaderboards[challenge_id]:
            if entry["user_id"] == user_id:
                return { "success": False, "error": "User has already joined this challenge." }

        # Register user with initial zero score, assign rank as new last place
        new_entry = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "score": 0.0,
            "rank": len(self.leaderboards[challenge_id]) + 1
        }
        self.leaderboards[challenge_id].append(new_entry)

        return { "success": True, "message": f"User joined challenge {challenge_id}." }


    def create_activity_log(
        self,
        user_id: str,
        challenge_id: str,
        activity_type: str,
        value: float,
        timestamp: str,
    ) -> dict:
        """
        Submit a new activity log for a valid user and challenge.

        Args:
            user_id (str): User ID performing the activity.
            challenge_id (str): Challenge ID the activity is submitted to.
            activity_type (str): Type of activity (e.g., "run", "swim").
            value (float): Quantitative value of the activity (must be positive).
            timestamp (str): When the activity occurred.

        Returns:
            dict:
                - On success: { "success": True, "message": "Activity log created" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - user_id must exist and user must be "active"
            - challenge_id must exist
            - activity_type must not be empty
            - value must be positive
            - Each log_id is unique (auto-generated)
        """
        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        # Check user active status ('active_sta' == 'active')
        if user.get("active_sta") != "active":
            return {"success": False, "error": "User is not active"}
        # Check challenge existence
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return {"success": False, "error": "Challenge does not exist"}
        # Check activity_type validity
        if not isinstance(activity_type, str) or not activity_type.strip():
            return {"success": False, "error": "Activity type must be a non-empty string"}
        # Check value validity
        if not (isinstance(value, (int, float)) and value > 0):
            return {"success": False, "error": "Activity value must be a positive number"}

        # Generate a unique log_id
        log_id = str(uuid.uuid4())
        while log_id in self.activity_logs:
            log_id = str(uuid.uuid4())

        # Create activity log
        new_log = {
            "log_id": log_id,
            "user_id": user_id,
            "challenge_id": challenge_id,
            "activity_type": activity_type,
            "value": value,
            "timestamp": timestamp,
        }
        self.activity_logs[log_id] = new_log

        return {"success": True, "message": "Activity log created"}

    def update_leaderboard_entry(self, challenge_id: str, user_id: str, score: float, rank: int) -> dict:
        """
        Update or create a user's leaderboard entry for a specific challenge with new score and rank.

        Args:
            challenge_id (str): ID of the associated fitness challenge.
            user_id (str): ID of the user whose leaderboard entry is being updated.
            score (float): New score value for the user.
            rank (int): New rank value for the user.

        Returns:
            dict: {
                "success": True,
                "message": "Leaderboard entry updated for user <username> in challenge <challenge name>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Challenge must exist.
            - User must exist and be active (activated).
            - Score must be non-negative, rank must be positive.
            - Creates entry if it does not exist; otherwise updates.
        """
        # Check challenge existence
        if challenge_id not in self.challenges:
            return { "success": False, "error": "Challenge does not exist." }

        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }
        if user["active_sta"] not in ("active", "activated", "verified"):
            return { "success": False, "error": "User is not activated; cannot update leaderboard." }

        # Validate score and rank
        if score < 0:
            return { "success": False, "error": "Score must be non-negative." }
        if rank <= 0:
            return { "success": False, "error": "Rank must be positive integer." }
    
        # Get leaderboard for challenge
        leaderboard = self.leaderboards.setdefault(challenge_id, [])
        entry_found = False
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                entry["score"] = score
                entry["rank"] = rank
                entry_found = True
                break

        if not entry_found:
            new_entry: LeaderboardEntryInfo = {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "score": score,
                "rank": rank
            }
            leaderboard.append(new_entry)

        username = user["username"]
        challenge_name = self.challenges[challenge_id]["name"]
        return {
            "success": True,
            "message": f"Leaderboard entry updated for user '{username}' in challenge '{challenge_name}'."
        }

    def deactivate_user_account(self, user_id: str) -> dict:
        """
        Deactivates or suspends a user account by setting its 'active_sta' (active_status)
        to 'inactive'.

        Args:
            user_id (str): The unique identifier of the user to deactivate.

        Returns:
            dict: Success or error message:
                {
                    "success": True,
                    "message": "User <username> deactivated"
                }
                or
                {
                    "success": False,
                    "error": "User not found" | "User already inactive"
                }

        Constraints:
            - User must exist in platform.
            - If already inactive/suspended, operation is idempotent and will report reason.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        curr_status = user.get("active_sta", "")
        if curr_status.lower() != "active":
            return { "success": False, "error": f"User is already not active (status: {curr_status})" }

        user["active_sta"] = "inactive"

        return {
            "success": True,
            "message": f"User '{user['username']}' deactivated"
        }

    def delete_user_account(self, user_id: str) -> dict:
        """
        Permanently remove a user and their associated data (activity logs, leaderboard entries) from the system.

        Args:
            user_id (str): Unique identifier of the user to remove.

        Returns:
            dict: 
                - On success: {"success": True, "message": "User and all associated data deleted."}
                - On failure: {"success": False, "error": "User does not exist."}

        Constraints:
            - User must exist in the system.
            - All activity logs and leaderboard entries associated with user are also removed.
        """

        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Remove user
        del self.users[user_id]

        # Remove user's activity logs
        logs_to_remove = [log_id for log_id, log in self.activity_logs.items() if log["user_id"] == user_id]
        for log_id in logs_to_remove:
            del self.activity_logs[log_id]

        # Remove user's leaderboard entries from each challenge
        for challenge_id, entries in self.leaderboards.items():
            filtered_entries = [entry for entry in entries if entry["user_id"] != user_id]
            self.leaderboards[challenge_id] = filtered_entries

        return { "success": True, "message": "User and all associated data deleted." }
