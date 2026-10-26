from typing import Dict, List, TypedDict
from datetime import datetime
import uuid



class MeetingInfo(TypedDict):
    meeting_id: str
    topic: str
    schedule: str
    venue: str                # venue_id
    meeting_code: str
    participants_list: List[str]    # List of participant_ids
    recurrence_pattern: str

class ParticipantInfo(TypedDict):
    participant_id: str
    name: str
    contact_info: str
    registration_status: str

class MeetingParticipantInfo(TypedDict):
    meeting_id: str
    participant_id: str
    join_time: str
    attendance_status: str

class VenueInfo(TypedDict):
    venue_id: str
    address: str
    room_number: str
    capacity: int

class SupportGroupManagementSystem:
    def __init__(self, init_config: dict):
        """
        Support group meeting/stateful environment.

        Constraints:
        - Only participants who provide the correct meeting_code may join the corresponding meeting.
        - Meeting participant lists are updated upon successful joining and reflect current attendance.
        - Venue capacity must not be exceeded for any meeting.
        - Each meeting must have a unique meeting_code for access control.
        """

        # Meetings: {meeting_id: MeetingInfo}
        self.meetings: Dict[str, MeetingInfo] = {}

        # Participants: {participant_id: ParticipantInfo}
        self.participants: Dict[str, ParticipantInfo] = {}

        # Meeting Participants: {meeting_id: [MeetingParticipantInfo]}
        self.meeting_participants: Dict[str, List[MeetingParticipantInfo]] = {}

        # Venues: {venue_id: VenueInfo}
        self.venues: Dict[str, VenueInfo] = {}

        self.init_config = init_config

    def find_participant_by_name(self, name: str) -> dict:
        """
        Retrieve participant information by name.

        Args:
            name (str): The name of the participant to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo]  # List of matching participants (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (invalid input)
            }

        Constraints:
            - Name is matched case-insensitively.
            - Multiple participants with the same name are all returned.
            - If name is empty or not a string, returns an error.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Name must be a non-empty string"}

        name_query = name.strip().lower()
        matching_participants = [
            participant for participant in self.participants.values()
            if participant["name"].strip().lower() == name_query
        ]

        return {"success": True, "data": matching_participants}

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve full details for the participant with the given participant_id.

        Args:
            participant_id (str): The unique participant identifier.

        Returns:
            dict: {
                "success": True,
                "data": ParticipantInfo,
            }
            or
            {
                "success": False,
                "error": str,  # "Participant not found"
            }

        Constraints:
            - The participant_id must exist in the system.
        """
        participant = self.participants.get(participant_id)
        if not participant:
            return { "success": False, "error": "Participant not found" }

        return { "success": True, "data": participant }

    def list_all_participants(self) -> dict:
        """
        List all registered participants in the support group management system.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo],  # List of all participant info records (may be empty)
            }

        Constraints:
            - No specific constraints; returns all registered participants.
        """
        participants_list = list(self.participants.values())
        return { "success": True, "data": participants_list }

    def get_meeting_by_topic(self, topic: str) -> dict:
        """
        Search and return all meetings that match the given topic.

        Args:
            topic (str): The topic to filter meetings by.

        Returns:
            dict:
                - success (bool): True if query is valid.
                - data (list): Each element is {
                    "meeting_id": str,
                    "schedule": str,
                    "venue": str  # venue_id
                  } for each matching meeting.

                If topic is invalid (none or empty), return success False and error message.

        Constraints:
            - topic must be a non-empty string.
            - Returns all matching meetings, even if multiple.

        """
        if not topic or not isinstance(topic, str):
            return { "success": False, "error": "Invalid topic provided" }

        results = []
        for meeting in self.meetings.values():
            if meeting["topic"] == topic:
                results.append({
                    "meeting_id": meeting["meeting_id"],
                    "schedule": meeting["schedule"],
                    "venue": meeting["venue"]
                })

        return { "success": True, "data": results }

    def get_meeting_by_schedule_and_venue(self, schedule: str, venue_id: str) -> dict:
        """
        Find all meetings scheduled at a given time and venue.

        Args:
            schedule (str): The scheduled time string of the meeting.
            venue_id (str): The identifier for the venue.

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "data": List[MeetingInfo]   # List may be empty if no meetings found
                }
              - On error: {
                    "success": False,
                    "error": str   # Explanation (e.g. "Venue not found")
                }

        Constraints:
            - Venue must exist in the system.
            - Returns all meetings with a matching schedule and venue.
        """
        if venue_id not in self.venues:
            return { "success": False, "error": "Venue not found" }

        matches = [
            meeting for meeting in self.meetings.values()
            if meeting["schedule"] == schedule and meeting["venue"] == venue_id
        ]

        return { "success": True, "data": matches }

    def get_meeting_by_code(self, meeting_code: str) -> dict:
        """
        Retrieve meeting details given a meeting_code.

        Args:
            meeting_code (str): The unique access code of the meeting.

        Returns:
            dict: {
                "success": True,
                "data": MeetingInfo,  # Details of the matching meeting
            }
            or
            {
                "success": False,
                "error": str  # No meeting found with the specified code
            }

        Constraints:
            - Each meeting_code is unique to a meeting.
        """
        for meeting in self.meetings.values():
            if meeting["meeting_code"] == meeting_code:
                return { "success": True, "data": meeting }
        return { "success": False, "error": "Meeting with specified code not found" }

    def get_meeting_details(self, meeting_id: str) -> dict:
        """
        Retrieve full details for a meeting by its meeting_id, including topic, schedule,
        venue details (address, room_number, capacity), participants (names), meeting_code, and recurrence pattern.

        Args:
            meeting_id (str): The unique identifier for the meeting.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "meeting_id": str,
                    "topic": str,
                    "schedule": str,
                    "venue": {
                        "venue_id": str,
                        "address": str,
                        "room_number": str,
                        "capacity": int
                    },
                    "meeting_code": str,
                    "recurrence_pattern": str,
                    "participants": List[dict],  # List of participant info (id and name)
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - meeting_id must exist within the system.
            - Venue and participants referenced may be missing; partial info will be provided.
        """
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            return { "success": False, "error": "Meeting not found" }

        venue_id = meeting["venue"]
        venue = self.venues.get(venue_id)
        if venue:
            venue_info = {
                "venue_id": venue_id,
                "address": venue["address"],
                "room_number": venue["room_number"],
                "capacity": venue["capacity"],
            }
        else:
            venue_info = {
                "venue_id": venue_id,
                "address": None,
                "room_number": None,
                "capacity": None,
            }

        participant_infos = []
        for pid in meeting.get("participants_list", []):
            pinfo = self.participants.get(pid)
            if pinfo:
                participant_infos.append({"participant_id": pid, "name": pinfo["name"]})
            else:
                participant_infos.append({"participant_id": pid, "name": None})

        meeting_details = {
            "meeting_id": meeting_id,
            "topic": meeting["topic"],
            "schedule": meeting["schedule"],
            "venue": venue_info,
            "meeting_code": meeting["meeting_code"],
            "recurrence_pattern": meeting.get("recurrence_pattern", ""),
            "participants": participant_infos,
        }

        return { "success": True, "data": meeting_details }

    def get_meeting_participants(self, meeting_id: str) -> dict:
        """
        List current participants in a given meeting.

        Args:
            meeting_id (str): Unique identifier of the meeting.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo],  # Info for each current participant in the meeting
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., meeting does not exist)
            }

        Constraints:
            - Meeting must exist in system.
            - The returned participants reflect current attendance (i.e., present in MeetingInfo.participants_list).
        """
        if meeting_id not in self.meetings:
            return { "success": False, "error": "Meeting does not exist" }

        participant_ids = self.meetings[meeting_id].get("participants_list", [])
        data = []
        for pid in participant_ids:
            participant = self.participants.get(pid)
            if participant:
                data.append(participant)
            else:
                # Participant id listed for meeting but not in participants DB; skip it, don't fail.
                continue

        return { "success": True, "data": data }

    def get_venue_by_address(self, address: str) -> dict:
        """
        Retrieve venue information by street address.

        Args:
            address (str): The street address to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[VenueInfo]  # List of matching venues; empty if none found
            }
            or
            {
                "success": False,
                "error": str  # Reason (venue not found)
            }

        Constraints:
            - Matches venues where VenueInfo["address"] == address (exact match).
            - If multiple venues match, all are returned.
        """
        result = [
            venue_info for venue_info in self.venues.values()
            if venue_info["address"] == address
        ]
        if not result:
            return { "success": False, "error": "Venue not found for address" }
        return { "success": True, "data": result }

    def get_venue_details(self, venue_id: str) -> dict:
        """
        Retrieve venue details (address, room number, and capacity) by venue_id.

        Args:
            venue_id (str): The unique identifier of the venue.

        Returns:
            dict: {
                "success": True,
                "data": VenueInfo,  # VenueInfo dict containing all details
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., venue does not exist)
            }

        Constraints:
            - The venue_id must exist in the system (checked).
        """
        venue_info = self.venues.get(venue_id)
        if venue_info is None:
            return { "success": False, "error": "Venue does not exist" }

        return { "success": True, "data": venue_info }

    def get_meeting_capacity(self, meeting_id: str) -> dict:
        """
        Query the capacity (maximum number of participants) of the venue hosting a given meeting.

        Args:
            meeting_id (str): The unique identifier of the meeting.

        Returns:
            dict: {
                "success": True,
                "data": int  # Venue's capacity for this meeting
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g. meeting or venue does not exist
            }

        Constraints:
            - Meeting with meeting_id must exist.
            - Venue assigned to meeting must exist.
        """
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return { "success": False, "error": "Meeting does not exist." }
        venue_id = meeting.get("venue")
        venue = self.venues.get(venue_id)
        if not venue:
            return { "success": False, "error": "Venue associated with meeting does not exist." }
        capacity = venue.get("capacity")
        return { "success": True, "data": capacity }

    def get_meeting_attendance_history(self, meeting_id: str) -> dict:
        """
        Retrieve the full attendance/join history for a specified meeting.

        Args:
            meeting_id (str): Unique identifier for the meeting.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": List[MeetingParticipantInfo]  # Join records (may be empty if none)
                  }
                - On failure: {
                      "success": False,
                      "error": str  # Reason, e.g., meeting does not exist.
                  }

        Constraints:
            - meeting_id must exist in the meetings.
        """
        if meeting_id not in self.meetings:
            return {"success": False, "error": "Meeting does not exist"}

        attendance = self.meeting_participants.get(meeting_id, [])
        return {"success": True, "data": attendance}

    def register_new_participant(
        self,
        participant_id: str,
        name: str,
        contact_info: str,
        registration_status: str = "registered"
    ) -> dict:
        """
        Register a new participant in the support group management system.

        Args:
            participant_id (str): Unique identifier for the participant.
            name (str): Name of the participant.
            contact_info (str): Contact details for the participant.
            registration_status (str): Registration status (default: "registered").

        Returns:
            dict: {
                "success": True,
                "message": "Participant <name> registered successfully."
            }
            or
            {
                "success": False,
                "error": "Participant with ID <participant_id> already exists."
            }

        Constraints:
            - Participant ID must be unique in the system.
            - Participant registration_status defaults to "registered".
        """
        if participant_id in self.participants:
            return {
                "success": False,
                "error": f"Participant with ID {participant_id} already exists."
            }

        new_participant: ParticipantInfo = {
            "participant_id": participant_id,
            "name": name,
            "contact_info": contact_info,
            "registration_status": registration_status
        }

        self.participants[participant_id] = new_participant
        return {
            "success": True,
            "message": f"Participant {name} registered successfully."
        }


    def join_meeting(self, meeting_id: str, participant_id: str, meeting_code: str) -> dict:
        """
        Participant attempts to join a meeting.

        Args:
            meeting_id (str): ID of the meeting to join.
            participant_id (str): Participant's unique identifier who wants to join.
            meeting_code (str): The code required for access control.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message
            }
            or
            {
                "success": False,
                "error": str  # Description of why joining failed
            }

        Constraints:
            - Meeting and participant must exist.
            - Provided meeting_code must match.
            - Cannot join if already participating.
            - Venue capacity cannot be exceeded.
            - Participant list and attendance log are updated on success.
        """
        # Check meeting existence
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            return { "success": False, "error": "Meeting not found." }
    
        # Check participant existence
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant not found." }
    
        # Meeting code must match
        if meeting_code != meeting["meeting_code"]:
            return { "success": False, "error": "Incorrect meeting code." }
    
        # Check if participant already joined
        if participant_id in meeting["participants_list"]:
            return { "success": False, "error": "Participant has already joined this meeting." }
    
        # Check venue capacity
        venue_id = meeting["venue"]
        venue = self.venues.get(venue_id)
        if venue is None:
            return { "success": False, "error": "Meeting venue not found." }
        current_count = len(meeting["participants_list"])
        if current_count >= venue["capacity"]:
            return { "success": False, "error": "Venue capacity exceeded." }
    
        # All checks passed, add participant
        meeting["participants_list"].append(participant_id)
        join_time = datetime.now().isoformat()
        mp_record = {
            "meeting_id": meeting_id,
            "participant_id": participant_id,
            "join_time": join_time,
            "attendance_status": "joined"
        }
        if meeting_id not in self.meeting_participants:
            self.meeting_participants[meeting_id] = []
        self.meeting_participants[meeting_id].append(mp_record)
    
        return { "success": True, "message": f"Participant {participant_id} successfully joined meeting {meeting_id}." }

    def leave_meeting(self, meeting_id: str, participant_id: str) -> dict:
        """
        Remove a participant from a meeting’s participant list and update attendance status.

        Args:
            meeting_id (str): The ID of the meeting to leave.
            participant_id (str): The participant's ID.

        Returns:
            dict: {
                "success": True,
                "message": "Participant <participant_id> removed from meeting <meeting_id> and attendance status updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - meeting_id must exist.
            - participant_id must exist.
            - participant_id must currently be in meeting's participant list and attendance history.
        """

        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            return { "success": False, "error": "Meeting not found." }

        participant = self.participants.get(participant_id)
        if participant is None:
            return { "success": False, "error": "Participant not found." }

        if participant_id not in meeting["participants_list"]:
            return { "success": False, "error": "Participant is not part of this meeting." }

        # Remove participant from the meeting's participant list
        meeting["participants_list"].remove(participant_id)

        # Update attendance status in meeting_participants
        updated = False
        mp_list = self.meeting_participants.get(meeting_id, [])
        for mp in mp_list:
            if mp["participant_id"] == participant_id:
                mp["attendance_status"] = "left"
                updated = True

        if not updated:
            return { "success": False, "error": "Meeting attendance record for participant not found." }

        return {
            "success": True,
            "message": f"Participant {participant_id} removed from meeting {meeting_id} and attendance status updated."
        }

    def create_meeting(
        self,
        topic: str,
        schedule: str,
        venue_id: str,
        recurrence_pattern: str,
        meeting_code: str
    ) -> dict:
        """
        Schedule a new meeting with topic, time, venue, recurrence, and unique code.

        Args:
            topic (str): The topic of the meeting.
            schedule (str): Date/time info for the meeting.
            venue_id (str): The venue's unique identifier.
            recurrence_pattern (str): Recurrence info (e.g., weekly, monthly).
            meeting_code (str): Access code (must be unique across meetings).

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Meeting scheduled with meeting_id <id>."
                }
                or
                {
                    "success": False,
                    "error": str  # reason for failure
                }

        Constraints:
            - Venue must exist.
            - meeting_code must be unique.
            - participants_list is initialized empty.
            - meeting_id must be unique (auto-generate).
        """
        # Venue existence check
        if venue_id not in self.venues:
            return {"success": False, "error": "Venue does not exist."}

        # meeting_code uniqueness check
        for mtg in self.meetings.values():
            if mtg["meeting_code"] == meeting_code:
                return {"success": False, "error": "Meeting code already in use."}

        # Auto-generate meeting_id (simple increment or UUID)
        # We'll use integer as string from total count + 1, not production safe
        meeting_id = str(uuid.uuid4())

        meeting_info: MeetingInfo = {
            "meeting_id": meeting_id,
            "topic": topic,
            "schedule": schedule,
            "venue": venue_id,
            "meeting_code": meeting_code,
            "participants_list": [],
            "recurrence_pattern": recurrence_pattern
        }

        self.meetings[meeting_id] = meeting_info
        self.meeting_participants[meeting_id] = []

        return {
            "success": True,
            "message": f"Meeting scheduled with meeting_id {meeting_id}."
        }

    def edit_meeting_details(
        self,
        meeting_id: str,
        topic: str = None,
        schedule: str = None,
        venue: str = None,
        meeting_code: str = None,
        recurrence_pattern: str = None
    ) -> dict:
        """
        Update details of a meeting. Can update topic, schedule (time), venue, meeting_code, and recurrence_pattern.

        Args:
            meeting_id (str): ID of the meeting to update.
            topic (str, optional): New topic for the meeting.
            schedule (str, optional): New schedule/time for the meeting.
            venue (str, optional): New venue_id for the meeting.
            meeting_code (str, optional): New unique access code for the meeting.
            recurrence_pattern (str, optional): New recurrence pattern for the meeting.

        Returns:
            dict: {
                "success": True,
                "message": "Meeting details updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Meeting must exist.
            - New meeting_code must be unique among meetings.
            - New venue must exist.
            - At least one field must be provided to update.
        """
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return { "success": False, "error": "Meeting does not exist." }

        fields_to_update = {}
        # Prepare update dict
        if topic is not None:
            fields_to_update["topic"] = topic
        if schedule is not None:
            fields_to_update["schedule"] = schedule
        if venue is not None:
            fields_to_update["venue"] = venue
        if meeting_code is not None:
            fields_to_update["meeting_code"] = meeting_code
        if recurrence_pattern is not None:
            fields_to_update["recurrence_pattern"] = recurrence_pattern

        if not fields_to_update:
            return { "success": False, "error": "No fields provided for update." }

        # Constraints checks
        # 1. meeting_code uniqueness
        if "meeting_code" in fields_to_update:
            new_code = fields_to_update["meeting_code"]
            for mid, m in self.meetings.items():
                if mid != meeting_id and m["meeting_code"] == new_code:
                    return { "success": False, "error": "Meeting code must be unique." }

        # 2. venue existence
        if "venue" in fields_to_update:
            new_venue_id = fields_to_update["venue"]
            if new_venue_id not in self.venues:
                return { "success": False, "error": "Venue does not exist." }

        # Update fields
        for key, value in fields_to_update.items():
            meeting[key] = value
        # Changes are applied directly to self.meetings[meeting_id] (as dict is mutable)

        return { "success": True, "message": "Meeting details updated successfully." }

    def create_venue(self, venue_id: str, address: str, room_number: str, capacity: int) -> dict:
        """
        Add a new venue location into the system.

        Args:
            venue_id (str): Unique identifier for the venue.
            address (str): Physical address of the venue.
            room_number (str): Room number within the venue/address.
            capacity (int): Maximum number of participants allowed.

        Returns:
            dict: {
                "success": True,
                "message": "Venue created successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., duplicate ID, invalid capacity)
            }

        Constraints:
            - venue_id must be unique (not already exist in venues).
            - capacity must be > 0.
            - address and room_number must be non-empty strings.
        """
        if venue_id in self.venues:
            return {"success": False, "error": "Venue ID already exists."}
        if not address or not isinstance(address, str):
            return {"success": False, "error": "Address must be a non-empty string."}
        if not room_number or not isinstance(room_number, str):
            return {"success": False, "error": "Room number must be a non-empty string."}
        if not isinstance(capacity, int) or capacity <= 0:
            return {"success": False, "error": "Capacity must be a positive integer."}

        venue_info = {
            "venue_id": venue_id,
            "address": address,
            "room_number": room_number,
            "capacity": capacity
        }
        self.venues[venue_id] = venue_info
        return {"success": True, "message": "Venue created successfully."}

    def update_participant_status(self, participant_id: str, new_status: str) -> dict:
        """
        Change or update a participant’s registration status.

        Args:
            participant_id (str): The unique ID of the participant.
            new_status (str): The new registration status value to set.

        Returns:
            dict:
                - On success: {"success": True, "message": "Participant registration status updated"}
                - On failure: {"success": False, "error": "reason"}
    
        Constraints:
            - Participant must exist.
            - No other constraints.
        """
        participant = self.participants.get(participant_id)
        if participant is None:
            return { "success": False, "error": "Participant not found" }

        participant["registration_status"] = new_status
        return { "success": True, "message": "Participant registration status updated" }

    def remove_participant(self, participant_id: str) -> dict:
        """
        Delete a participant entirely from the system.

        Args:
            participant_id (str): ID of the participant to remove.

        Returns:
            dict:
                success: True and a message if removal succeeded.
                success: False and error message if participant not found.

        Constraints:
            - Participant is deleted from system records, meeting attendance history, and meetings' participant lists.
            - If participant is not found, returns error.
        """
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant not found." }

        # Remove from participants
        del self.participants[participant_id]

        # Remove from meetings' participants_list
        for meeting in self.meetings.values():
            if participant_id in meeting["participants_list"]:
                meeting["participants_list"].remove(participant_id)

        # Remove from meeting participants (attendance history)
        for meeting_id, attendance_list in self.meeting_participants.items():
            self.meeting_participants[meeting_id] = [
                record for record in attendance_list if record["participant_id"] != participant_id
            ]

        return {
            "success": True,
            "message": f"Participant {participant_id} removed from system."
        }
