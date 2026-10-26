from typing import Dict, List, Optional, TypedDict
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    name: str
    role: str  # 'patient' or 'therapist'

class TherapySessionInfo(TypedDict, total=False):
    session_id: str
    user_id: str
    date: str  # ISO date string
    duration: float
    notes: Optional[str]

class ExerciseInfo(TypedDict):
    exercise_id: str
    name: str
    description: str
    category: str

class SessionExerciseInfo(TypedDict, total=False):
    session_id: str
    exercise_id: str
    repetitions: int
    sets: int
    intensity: int
    progress_notes: Optional[str]

class PhysicalTherapyTrackingApplication:
    def __init__(self, init_config: dict):
        """
        Physical therapy tracking application environment.
        init_config: configuration (not implemented)
        """

        # Users: {_id: UserInfo}
        # Entity: User -- attributes: _id, name, role
        self.users: Dict[str, UserInfo] = {}

        # Therapy sessions: {session_id: TherapySessionInfo}
        # Entity: TherapySession -- attributes: session_id, user_id, date, duration, notes
        self.sessions: Dict[str, TherapySessionInfo] = {}

        # Exercises: {exercise_id: ExerciseInfo}
        # Entity: Exercise -- attributes: exercise_id, name, description, category
        self.exercises: Dict[str, ExerciseInfo] = {}

        # Session Exercises: {(session_id, exercise_id): SessionExerciseInfo}
        # Entity: SessionExercise -- attributes: session_id, exercise_id, repetitions, sets, intensity, progress_notes
        self.session_exercises: Dict[str, List[SessionExerciseInfo]] = {}
        
        # Constraints:
        # - Each therapy session must be associated with one user and one or more exercises.
        # - Session dates must be valid and in the past or present.
        # - Progress notes are optional but can only be appended to existing session exercises.
        # - Only therapists or the session owner can modify past entries.

        self.init_config = init_config

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information given a user name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or 
            {
                "success": False,
                "error": str  # e.g., "User not found"
            }

        Constraints:
            - Returns the first user found with the matching name.
            - If no user with the name exists, fails with an error.
        """
        for user in self.users.values():
            if user["name"] == name:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information given a user ID.

        Args:
            user_id (str): User identifier to query.

        Returns:
            dict:
                {
                    "success": True,
                    "data": UserInfo
                }
                or
                {
                    "success": False,
                    "error": str  # Reason, e.g. "User not found"
                }
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_all_users(self) -> dict:
        """
        List all registered users (patients, therapists).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],
            }
            or
            {
                "success": False,
                "error": str  # If there is a very unlikely internal data error
            }

        Notes:
            - If there are no users, data is an empty list.
            - No constraints or permissions required; anyone can query this.
        """
        try:
            users_list = list(self.users.values())
            return { "success": True, "data": users_list }
        except Exception as e:
            return { "success": False, "error": f"Internal error: {str(e)}" }

    def get_user_role(self, user_id: str) -> dict:
        """
        Query the role of a user (either 'patient' or 'therapist') by their user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": { "_id": user_id, "role": role }
                }
                On failure (user not found):
                {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": { "_id": user_id, "role": user["role"] } }

    def list_sessions_by_user(self, user_id: str) -> dict:
        """
        Get all therapy sessions associated with a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[TherapySessionInfo],  # List of session info for the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If the user does not exist
            }

        Constraints:
            - Only sessions where session.user_id == user_id are returned.
            - If user does not exist, operation fails.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        results = [session_info for session_info in self.sessions.values()
                   if session_info["user_id"] == user_id]

        return { "success": True, "data": results }

    def get_session_by_date(self, user_id: str, date: str) -> dict:
        """
        Find a therapy session for a specific user on a given date.

        Args:
            user_id (str): ID of the user whose session to look up.
            date (str): ISO date string of the session (e.g., "2024-06-07").

        Returns:
            dict: {
                "success": True,
                "data": TherapySessionInfo  # Complete info for the found session
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, such as user not found or no session on given date.
            }

        Constraints:
            - User must exist.
            - Searches for a session with matching user_id and date.
            - If multiple sessions exist for the same date, returns the first found.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        for session in self.sessions.values():
            if session.get("user_id") == user_id and session.get("date") == date:
                return { "success": True, "data": session }

        return { "success": False, "error": "No session found for the user on the given date" }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve full details of a therapy session by its session_id.

        Args:
            session_id (str): The unique identifier of the therapy session to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": TherapySessionInfo  # All attributes of the session
            }
            or
            {
                "success": False,
                "error": str  # Error message if session not found
            }

        Constraints:
            - None for simple information query; session must exist.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session ID not found" }
        return { "success": True, "data": session }

    def list_exercises(self) -> dict:
        """
        List all available exercises in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[ExerciseInfo],  # May be empty if no exercises
            }
        """
        exercises_list = list(self.exercises.values())
        return { "success": True, "data": exercises_list }

    def get_exercise_by_id(self, exercise_id: str) -> dict:
        """
        Get details of a specific exercise by its unique exercise_id.

        Args:
            exercise_id (str): Unique identifier for the exercise.

        Returns:
            dict: {
                "success": True,
                "data": ExerciseInfo  # Details of the found exercise
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g. not found)
            }

        Constraints:
            - The exercise_id must exist in the system.
            - No authorization required for this read operation.
        """
        exercise = self.exercises.get(exercise_id)
        if exercise is None:
            return { "success": False, "error": "Exercise not found" }
        return { "success": True, "data": exercise }

    def list_session_exercises(self, session_id: str) -> dict:
        """
        List all exercises (with details) that have been logged for the specified therapy session.

        Args:
            session_id (str): The identifier of the therapy session.

        Returns:
            dict: {
                "success": True,
                "data": List[SessionExerciseInfo]  # List of exercises logged for the session (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "Session not found"
            }

        Constraints:
            - The session_id must correspond to an existing therapy session.
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}

        exercises = self.session_exercises.get(session_id, [])

        return {"success": True, "data": exercises}

    def get_session_exercise_details(self, session_id: str, exercise_id: str) -> dict:
        """
        Retrieve execution details (sets, repetitions, intensity, and progress notes)
        for the exercise with exercise_id performed in the session with session_id.

        Args:
            session_id (str): ID of the therapy session.
            exercise_id (str): ID of the exercise in the session.

        Returns:
            dict: {
                "success": True,
                "data": SessionExerciseInfo  # Details for the session-exercise pairing
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - session_id must exist.
            - exercise_id must exist.
            - The (session_id, exercise_id) pairing must exist in session_exercises.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }
        if exercise_id not in self.exercises:
            return { "success": False, "error": "Exercise does not exist" }
        session_ex_list = self.session_exercises.get(session_id)
        if not session_ex_list:
            return { "success": False, "error": "No exercises recorded for this session" }
        for session_ex in session_ex_list:
            if session_ex.get("exercise_id") == exercise_id:
                return { "success": True, "data": session_ex }
        return { "success": False, "error": "Exercise not found in specified session" }

    def create_therapy_session(self, user_id: str, date: str, duration: float, notes: Optional[str] = None, actor_id: Optional[str] = None) -> dict:
        """
        Create a new therapy session for a user on a specified date and duration.

        Args:
            user_id (str): ID of the user for whom the session is created.
            date (str): ISO date (YYYY-MM-DD), must be today or in the past.
            duration (float): Duration of the session (in minutes or hours).
            notes (Optional[str]): Optional session notes.
            actor_id (Optional[str]): ID of the user performing the operation (must be the session owner or 'therapist').

        Returns:
            dict: {
                "success": True,
                "message": str,   # Session created
                "session_id": str # The created session's ID
            }
            or
            {
                "success": False,
                "error": str      # Error message
            }
        Constraints:
            - User must exist.
            - Date must be in the past or present.
            - Only the session owner (user) or a therapist can create a session.
        """

        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        # Actor permission check
        if actor_id is not None:
            if actor_id not in self.users:
                return { "success": False, "error": "Actor does not exist." }
            actor = self.users[actor_id]
            if actor_id != user_id and actor['role'] != 'therapist':
                return { "success": False, "error": "Only therapists or the session owner can create sessions." }

        # Validate date format and "past or present"
        try:
            session_date = datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return { "success": False, "error": "Invalid date format. Use YYYY-MM-DD." }
        today = datetime.now()
        if session_date.date() > today.date():
            return { "success": False, "error": "Session date cannot be in the future." }

        # Generate unique session_id (simple: user_id + date + count)
        count = sum(1 for s in self.sessions.values() if s['user_id'] == user_id and s['date'] == date)
        session_id = f"{user_id}_{date}_{count+1}"

        if session_id in self.sessions:
            return { "success": False, "error": "Session with this ID already exists." }

        session_info: TherapySessionInfo = {
            "session_id": session_id,
            "user_id": user_id,
            "date": date,
            "duration": duration,
        }
        if notes:
            session_info["notes"] = notes

        self.sessions[session_id] = session_info

        return {
            "success": True,
            "message": f"Therapy session created for user {user_id} on {date}.",
            "session_id": session_id
        }

    def add_exercise_to_session(
        self,
        session_id: str,
        exercise_id: str,
        repetitions: int,
        sets: int,
        intensity: int
    ) -> dict:
        """
        Associate an exercise with a therapy session with repetitions, sets, and intensity.
    
        Args:
            session_id (str): The ID of the target therapy session.
            exercise_id (str): The ID of the exercise to associate.
            repetitions (int): Number of repetitions for the exercise.
            sets (int): Number of sets for this exercise.
            intensity (int): Intensity level (scale defined by the application).

        Returns:
            dict: {
                "success": True,
                "message": "Exercise added to session successfully"
            }
            or on failure:
            {
                "success": False,
                "error": str  # Description of the error
            }
        Constraints:
            - session_id must exist.
            - exercise_id must exist.
            - The same exercise cannot be associated more than once with the same session.
        """
        # Check session exists
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }
        # Check exercise exists
        if exercise_id not in self.exercises:
            return { "success": False, "error": "Exercise does not exist" }
        # Check for duplicate in session
        existing_exercises = self.session_exercises.get(session_id, [])
        for se in existing_exercises:
            if se["exercise_id"] == exercise_id:
                return { "success": False, "error": "Exercise already associated with session" }
        # Create and add
        new_se: SessionExerciseInfo = {
            "session_id": session_id,
            "exercise_id": exercise_id,
            "repetitions": repetitions,
            "sets": sets,
            "intensity": intensity,
            # progress_notes omitted; can only be appended later
        }
        existing_exercises.append(new_se)
        self.session_exercises[session_id] = existing_exercises
        return { "success": True, "message": "Exercise added to session successfully" }

    def append_progress_note(
        self,
        session_id: str,
        exercise_id: str,
        note: str,
        operator_user_id: str
    ) -> dict:
        """
        Add (append) a new progress note to an existing session-exercise pair.
        Only the session owner (patient) or a therapist can perform this operation.
        This does not overwrite existing progress notes, but appends to them.

        Args:
            session_id (str): The ID of the therapy session.
            exercise_id (str): The ID of the exercise within the session.
            note (str): The note to append.
            operator_user_id (str): The user attempting to append (permission check).

        Returns:
            dict: {
                "success": True,
                "message": "Progress note appended to session-exercise."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - SessionExercise must exist.
            - Only therapists or session owner may append.
            - Existing notes are not overwritten.
        """

        # Check user exists
        operator = self.users.get(operator_user_id)
        if not operator:
            return {"success": False, "error": "Operator user not found"}

        # Check session exists
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Permission check: operator must be therapist or session owner
        session_owner_id = session.get("user_id")
        if operator["role"] != "therapist" and operator_user_id != session_owner_id:
            return {"success": False, "error": "Permission denied: only therapist or session owner may append progress note"}

        # Find session exercise
        session_ex_list = self.session_exercises.get(session_id)
        if not session_ex_list:
            return {"success": False, "error": "No exercises found for session"}

        found = False
        for se in session_ex_list:
            if se.get("exercise_id") == exercise_id:
                # Only append, do not overwrite existing notes
                if "progress_notes" in se and se["progress_notes"]:
                    se["progress_notes"] += f"\n{note}"
                else:
                    se["progress_notes"] = note
                found = True
                break

        if not found:
            return {"success": False, "error": "Session-Exercise pair not found"}

        return {
            "success": True,
            "message": "Progress note appended to session-exercise."
        }

    def update_session_details(
        self, 
        session_id: str, 
        actor_id: str, 
        duration: Optional[float] = None, 
        notes: Optional[str] = None
    ) -> dict:
        """
        Update attributes 'duration' and/or 'notes' for a therapy session, only if the actor is a therapist or the session's owner.

        Args:
            session_id (str): ID of the session to be updated.
            actor_id (str): ID of the user attempting to update.
            duration (Optional[float]): New duration. Update if not None.
            notes (Optional[str]): New notes. Update if not None.

        Returns:
            dict: {
                "success": True,
                "message": "Session details updated."
            }
            or
            dict: {
                "success": False,
                "error": str  # Reason: session/user not found, unauthorized, nothing to update, etc.
            }

        Constraints:
            - Only the session owner or a user with role 'therapist' can update session details.
            - Session must exist.
            - User (actor) must exist.
            - At least one of duration or notes must be provided to update.
        """
        # Check session existence
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session not found." }

        # Check user existence
        user = self.users.get(actor_id)
        if not user:
            return { "success": False, "error": "User (actor) not found." }

        # Authorization check: therapist or owner
        if user["role"] != "therapist" and session["user_id"] != actor_id:
            return { "success": False, "error": "Permission denied. Only therapists or the session owner can update session details." }

        # Nothing to update?
        if duration is None and notes is None:
            return { "success": False, "error": "No session details provided to update." }

        # Update fields
        updated = False
        if duration is not None:
            session["duration"] = duration
            updated = True
        if notes is not None:
            session["notes"] = notes
            updated = True

        if updated:
            self.sessions[session_id] = session  # Save change

            return {
                "success": True,
                "message": "Session details updated."
            }
        else:
            return { "success": False, "error": "No valid updates applied." }

    def update_session_exercise_parameters(
        self,
        session_id: str,
        exercise_id: str,
        user_id: str,
        repetitions: Optional[int] = None,
        sets: Optional[int] = None,
        intensity: Optional[int] = None
    ) -> dict:
        """
        Modify the repetitions, sets, or intensity of a session-exercise, if user is permitted.

        Args:
            session_id (str): The ID of the therapy session.
            exercise_id (str): The ID of the exercise within the session.
            user_id (str): The ID of the user attempting the update.
            repetitions (Optional[int]): New number of repetitions (optional).
            sets (Optional[int]): New number of sets (optional).
            intensity (Optional[int]): New intensity (optional).
    
        Returns:
            dict: {
                "success": True,
                "message": "Session exercise updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Only therapists or session owner may modify session exercises.
            - Session, exercise, and user IDs must be valid.
            - Only SessionExercise entries that exist may be updated.
        """
        # Validate user
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
    
        # Validate session
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found."}

        # Permission check
        is_therapist = (user.get("role") == "therapist")
        is_owner = (session.get("user_id") == user_id)
        if not (is_owner or is_therapist):
            return {"success": False, "error": "Permission denied. Only session owner or therapist may modify session exercises."}
    
        # Validate SessionExercise exists
        session_exercises = self.session_exercises.get(session_id, [])
        # Find the exercise (by exercise_id)
        se_found = None
        for se in session_exercises:
            if se.get("exercise_id") == exercise_id:
                se_found = se
                break
        if not se_found:
            return {"success": False, "error": "Session exercise not found in session."}
    
        # Update parameters (only those provided)
        if repetitions is not None:
            se_found["repetitions"] = repetitions
        if sets is not None:
            se_found["sets"] = sets
        if intensity is not None:
            se_found["intensity"] = intensity

        return {"success": True, "message": "Session exercise updated successfully."}

    def delete_session_exercise(self, session_id: str, exercise_id: str, request_user_id: str) -> dict:
        """
        Remove an exercise entry from a specific therapy session.

        Args:
            session_id (str): ID of the target therapy session.
            exercise_id (str): ID of the exercise to remove.
            request_user_id (str): ID of the user requesting the deletion (for permissions).

        Returns:
            dict:
              - On success: {"success": True, "message": "Exercise removed from session."}
              - On failure: {"success": False, "error": "Reason for failure"}

        Constraints:
            - Only the session owner or a user with role 'therapist' may delete entries.
            - You cannot remove the last exercise from a session.
            - Session and exercise must exist.
        """
        # Check session exists
        if session_id not in self.sessions:
            return {"success": False, "error": "Therapy session not found."}

        # Check user exists
        if request_user_id not in self.users:
            return {"success": False, "error": "Requesting user not found."}

        session_info = self.sessions[session_id]
        session_ex_list = self.session_exercises.get(session_id, [])

        # Find the session exercise index
        exercise_index = None
        for i, sess_ex in enumerate(session_ex_list):
            if sess_ex.get("exercise_id") == exercise_id:
                exercise_index = i
                break

        if exercise_index is None:
            return {"success": False, "error": "Exercise not found in session."}

        # Access control
        user_info = self.users[request_user_id]
        session_owner = session_info.get("user_id")
        if not (request_user_id == session_owner or user_info.get("role") == "therapist"):
            return {"success": False, "error": "Permission denied. Only therapist or session owner can delete this entry."}

        # Check last exercise
        if len(session_ex_list) <= 1:
            return {"success": False, "error": "Therapy session must have at least one exercise."}

        # Delete
        del session_ex_list[exercise_index]
        self.session_exercises[session_id] = session_ex_list

        return {"success": True, "message": "Exercise removed from session."}

    def delete_therapy_session(self, session_id: str, requester_id: str) -> dict:
        """
        Remove an entire therapy session, provided the requester is the session owner or a therapist.

        Args:
            session_id (str): Identifier of the therapy session to remove.
            requester_id (str): User ID of the requester performing the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Therapy session deleted."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, permission denied, etc.)
            }

        Constraints:
            - Only the session owner or a user with role 'therapist' can delete a session.
        """

        # Check if session exists
        session_info = self.sessions.get(session_id)
        if not session_info:
            return {"success": False, "error": "Therapy session does not exist."}

        # Check if requester exists
        requester_info = self.users.get(requester_id)
        if not requester_info:
            return {"success": False, "error": "Requester user does not exist."}

        # Check permissions: must be owner or therapist
        is_owner = session_info.get("user_id") == requester_id
        is_therapist = requester_info.get("role") == "therapist"
        if not (is_owner or is_therapist):
            return {"success": False, "error": "Permission denied. Only the session owner or a therapist may delete the session."}

        # Delete session
        del self.sessions[session_id]

        # Delete all session exercises associated with this session
        if session_id in self.session_exercises:
            del self.session_exercises[session_id]

        return {"success": True, "message": "Therapy session deleted."}
