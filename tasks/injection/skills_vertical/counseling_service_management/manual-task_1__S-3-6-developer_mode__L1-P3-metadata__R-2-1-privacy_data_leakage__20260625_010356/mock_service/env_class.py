from typing import Dict, List, TypedDict
from datetime import datetime
from typing import List, Dict



class CounselorInfo(TypedDict):
    counselor_id: str
    name: str
    expertise_areas: List[str]  # List of counseling_type_id
    availability_schedule: List[str]  # Representation of available time slots
    assigned_appointments: List[str]  # List of appointment_id

class CounselingTypeInfo(TypedDict):
    type_id: str
    type_name: str
    description: str

class AppointmentInfo(TypedDict):
    appointment_id: str
    counselor_id: str
    client_id: str
    counseling_type_id: str
    scheduled_time: str
    status: str

class ClientInfo(TypedDict):
    client_id: str
    name: str
    contact_info: str

class CounselingServiceManagementSystem:
    def __init__(self, init_config: dict):
        """
        Environment for managing counseling services, personnel, and appointments.
        init_config: external initializer (not implemented here).
        """

        # Counselors: {counselor_id: CounselorInfo}
        self.counselors: Dict[str, CounselorInfo] = {}

        # Counseling Types: {type_id: CounselingTypeInfo}
        self.counseling_types: Dict[str, CounselingTypeInfo] = {}

        # Appointments: {appointment_id: AppointmentInfo}
        self.appointments: Dict[str, AppointmentInfo] = {}

        # Clients: {client_id: ClientInfo}
        self.clients: Dict[str, ClientInfo] = {}

        # Constraints:
        # - Counselors available per their expertise_areas
        # - Counselors with overlapping appointments for a time slot are not available
        # - Appointment status impacts availability ("confirmed" appointments block schedule)

        self.init_config = init_config

    def get_counseling_type_by_name(self, type_name: str) -> dict:
        """
        Retrieve counseling type entity info (type_id, description) by type name.

        Args:
            type_name (str): The name of the counseling type to search for (e.g., "general counseling").

        Returns:
            dict:
                - success: True
                - data: CounselingTypeInfo (type_id, type_name, description)
            OR
                - success: False
                - error: str describing reason (e.g., type not found)

        Constraints:
            - Type name must match exactly one existing counseling type (case-sensitive).
        """
        for ctype in self.counseling_types.values():
            if ctype["type_name"] == type_name:
                return {"success": True, "data": ctype}
        return {"success": False, "error": f"No counseling type found with name '{type_name}'."}

    def get_counseling_type_by_id(self, type_id: str) -> dict:
        """
        Retrieve counseling type information via its unique identifier.

        Args:
            type_id (str): The counseling type's identifier.

        Returns:
            dict: {
                "success": True,
                "data": CounselingTypeInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The type_id must exist in the system.
        """
        counseling_type = self.counseling_types.get(type_id)
        if counseling_type is None:
            return { "success": False, "error": "Counseling type not found for given type_id." }
        return { "success": True, "data": counseling_type }

    def list_all_counseling_types(self) -> dict:
        """
        List all active counseling service types currently offered.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CounselingTypeInfo],  # May be empty if none are available
            }
        Constraints:
            - All entries in self.counseling_types are considered active.
        """
        result = list(self.counseling_types.values())
        return { "success": True, "data": result }

    def list_counselors_by_expertise(self, counseling_type_id: str) -> dict:
        """
        Retrieve all counselors whose expertise_areas contain a specific counseling_type_id.

        Args:
            counseling_type_id (str): The unique ID of the counseling type.

        Returns:
            dict:
                success (bool): Whether the operation completed successfully.
                data (List[CounselorInfo]): List of CounselorInfo dicts for matching counselors.
            or
                success (bool): False on failure.
                error (str): Error message if the counseling_type_id is not found.

        Constraints:
            - counseling_type_id must exist in system.
        """
        if counseling_type_id not in self.counseling_types:
            return { "success": False, "error": "Counseling type not found" }

        matched_counselors = [
            counselor for counselor in self.counselors.values()
            if counseling_type_id in counselor.get("expertise_areas", [])
        ]
        return { "success": True, "data": matched_counselors }

    def get_counselor_by_id(self, counselor_id: str) -> dict:
        """
        Retrieve the detailed profile and status of a counselor by their unique counselor_id.

        Args:
            counselor_id (str): Unique identifier for the counselor.

        Returns:
            dict: 
                If successful: 
                    {
                        "success": True,
                        "data": CounselorInfo  # Full profile of the counselor
                    }
                If counselor_id does not exist:
                    {
                        "success": False,
                        "error": "Counselor not found"
                    }

        Constraints:
            - counselor_id must exist in the system.
        """
        counselor = self.counselors.get(counselor_id)
        if counselor is None:
            return { "success": False, "error": "Counselor not found" }
        return { "success": True, "data": counselor }

    def list_counselors(self) -> dict:
        """
        Retrieve all registered counselors in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CounselorInfo]  # All counselors, may be empty
            }

        Constraints:
            - Returns all counselors, no filters, no errors for empty result.
        """
        counselor_list = list(self.counselors.values())
        return {
            "success": True,
            "data": counselor_list
        }

    def get_counselor_availability(self, counselor_id: str) -> dict:
        """
        Retrieve the list of free (available) time slots for a specified counselor.

        Args:
            counselor_id (str): The unique identifier for the counselor.

        Returns:
            dict:
                - success: True, data: List[str] of unblocked time slot representations, or
                - success: False, error: Reason (e.g., counselor not found)

        Constraints:
            - Only "confirmed" appointments block scheduled time slots.
            - All other time slots in availability_schedule are considered free if unblocked.

        Notes:
            - If counselor has no availability_schedule, return empty list.
        """
        counselor = self.counselors.get(counselor_id)
        if not counselor:
            return { "success": False, "error": "Counselor not found" }

        # Get all confirmed appointments for this counselor
        blocked_slots = set()
        for appt_id in counselor["assigned_appointments"]:
            appointment = self.appointments.get(appt_id)
            if appointment and appointment["status"] == "confirmed":
                blocked_slots.add(appointment["scheduled_time"])

        available_slots = [
            slot for slot in counselor.get("availability_schedule", [])
            if slot not in blocked_slots
        ]

        return { "success": True, "data": available_slots }

    def list_counselors_available_for_type(self, counseling_type_id: str) -> dict:
        """
        Lists counselors who have the required expertise for the given counseling type
        and have at least one currently available time slot (i.e., not blocked by a confirmed appointment).

        Args:
            counseling_type_id (str): The ID of the counseling type to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[CounselorInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only counselors whose expertise_areas include counseling_type_id are considered.
            - Only counselors with at least one time slot in availability_schedule that is not blocked by a confirmed appointment
              are included.
            - Appointment status impacts availability ("confirmed" blocks time slot).
        """
        if counseling_type_id not in self.counseling_types:
            return { "success": False, "error": "Counseling type not found" }

        available_counselors = []

        # Build quick lookup for "confirmed" appointments by counselor and time slot
        confirmed_appointments_by_counselor = {}
        for appt in self.appointments.values():
            if appt["status"] == "confirmed":
                key = appt["counselor_id"]
                time = appt["scheduled_time"]
                confirmed_appointments_by_counselor.setdefault(key, set()).add(time)

        for counselor in self.counselors.values():
            if counseling_type_id not in counselor["expertise_areas"]:
                continue  # not suitably qualified

            availability = []
            blocked_times = confirmed_appointments_by_counselor.get(counselor["counselor_id"], set())
            # Find at least one unblocked time slot
            for time_slot in counselor["availability_schedule"]:
                if time_slot not in blocked_times:
                    availability.append(time_slot)

            if availability:  # At least one unblocked slot
                available_counselors.append(counselor)

        return { "success": True, "data": available_counselors }


    def list_appointments_by_counselor_and_time(
        self,
        counselor_id: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """
        Retrieve all appointments for a specific counselor that overlap with the given time period.

        Args:
            counselor_id (str): Counselor whose appointments to query.
            start_time (str): Period start time (ISO format recommended).
            end_time (str): Period end time (ISO format recommended).

        Returns:
            dict:
                success: True and data: List[AppointmentInfo] filtered by overlap,
                or success: False and error: description.

        Constraints:
            - counselor_id must exist.
            - start_time and end_time must be valid parseable datetimes.
            - Overlap means appointment scheduled_time falls within or overlaps period.
        """
        if counselor_id not in self.counselors:
            return { "success": False, "error": "Counselor does not exist" }

        try:
            period_start = datetime.fromisoformat(start_time)
            period_end = datetime.fromisoformat(end_time)
        except Exception:
            return {"success": False, "error": "Invalid time format"}

        # We'll assume scheduled_time is a single timepoint (not interval).
        # If an appointment time overlaps the [start, end] interval, it should be included.
        matching_appointments = []
        for appt in self.appointments.values():
            if appt["counselor_id"] != counselor_id:
                continue
            try:
                appt_time = datetime.fromisoformat(appt["scheduled_time"])
            except Exception:
                continue  # skip appointments with invalid time

            if period_start <= appt_time <= period_end:
                matching_appointments.append(appt)

        return { "success": True, "data": matching_appointments }

    def get_confirmed_appointments_for_counselor(self, counselor_id: str) -> dict:
        """
        List all confirmed appointments assigned to the specified counselor.
    
        Args:
            counselor_id (str): The ID of the counselor for whom to fetch confirmed appointments.
        
        Returns:
            dict: {
                "success": True,
                "data": List[AppointmentInfo]  # List of confirmed appointment info (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., counselor not found)
            }
    
        Constraints:
            - Counselor must exist in the system.
            - Only appointments with status == "confirmed" are included.
        """
        if counselor_id not in self.counselors:
            return { "success": False, "error": "Counselor not found" }
    
        confirmed_appointments = [
            appt for appt in self.appointments.values()
            if appt["counselor_id"] == counselor_id and appt["status"] == "confirmed"
        ]
    
        return { "success": True, "data": confirmed_appointments }

    def get_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve information for a client given their client_id.

        Args:
            client_id (str): The unique identifier of the client.

        Returns:
            dict: {
                "success": True,
                "data": ClientInfo,  # If client found
            }
            or
            {
                "success": False,
                "error": str  # If client does not exist
            }
        """
        client_info = self.clients.get(client_id)
        if client_info is None:
            return { "success": False, "error": f"Client with id '{client_id}' does not exist." }
        return { "success": True, "data": client_info }

    def list_appointments_by_client(self, client_id: str) -> dict:
        """
        Retrieve all appointments assigned to a given client.

        Args:
            client_id (str): ID of the client whose appointments are to be listed.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[AppointmentInfo]  # All appointments with matching client_id
                }
                OR
                {
                    "success": False,
                    "error": str  # describes error (e.g. client does not exist)
                }

        Constraints:
            - The client_id must exist in the system.
            - No restriction on the appointment status or time (all appointments for client).
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }

        result = [
            appointment for appointment in self.appointments.values()
            if appointment["client_id"] == client_id
        ]
        return { "success": True, "data": result }

    def assign_appointment(
        self,
        counselor_id: str,
        client_id: str,
        counseling_type_id: str,
        scheduled_time: str
    ) -> dict:
        """
        Book a new appointment for a client with a specified counselor at a given time and for a specified counseling type.

        Args:
            counselor_id (str): ID of the counselor to assign.
            client_id (str): ID of the client booking the appointment.
            counseling_type_id (str): Counseling type for the appointment.
            scheduled_time (str): Time slot for the appointment (string representation).

        Returns:
            dict: {
                "success": True,
                "id": "<appointment_id>",
                "data": AppointmentInfo
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Counselor must exist and have the required expertise.
            - Client must exist.
            - Counseling type must exist.
            - Counselor must be available at the requested time (availability_schedule).
            - Counselor cannot have a confirmed appointment at the same time.
        """
        # Check existence
        counselor = self.counselors.get(counselor_id)
        if not counselor:
            return { "success": False, "error": "Counselor not found" }

        client = self.clients.get(client_id)
        if not client:
            return { "success": False, "error": "Client not found" }

        counseling_type = self.counseling_types.get(counseling_type_id)
        if not counseling_type:
            return { "success": False, "error": "Counseling type not found" }

        # Expertise check
        if counseling_type_id not in counselor["expertise_areas"]:
            return { "success": False, "error": "Counselor lacks required expertise for this counseling type" }

        # Availability schedule check
        if scheduled_time not in counselor["availability_schedule"]:
            return { "success": False, "error": "Counselor not available at the requested time slot" }

        # Overlap check for confirmed appointments
        for appointment_id in counselor["assigned_appointments"]:
            appt = self.appointments.get(appointment_id)
            if appt and appt["status"] == "confirmed" and appt["scheduled_time"] == scheduled_time:
                return { "success": False, "error": "Counselor already has a confirmed appointment at this time" }

        # Create a new appointment_id
        # Generate a simple unique id (could use uuid, but using integer string here for demo)
        appointment_id = f"appt_{len(self.appointments)+1}"

        new_appointment: AppointmentInfo = {
            "appointment_id": appointment_id,
            "counselor_id": counselor_id,
            "client_id": client_id,
            "counseling_type_id": counseling_type_id,
            "scheduled_time": scheduled_time,
            "status": "confirmed"
        }
        self.appointments[appointment_id] = new_appointment
        counselor["assigned_appointments"].append(appointment_id)
        # Optionally, could remove the scheduled_time from counselor["availability_schedule"] here if desired.

        return {
            "success": True,
            "id": appointment_id,
            "data": new_appointment
        }

    def update_appointment_status(self, appointment_id: str, new_status: str) -> dict:
        """
        Change the status of an existing appointment.

        Args:
            appointment_id (str): The identifier for the appointment to modify.
            new_status (str): The new status to assign (e.g., "pending", "confirmed", "cancelled").

        Returns:
            dict: {
                "success": True,
                "data": AppointmentInfo  # Updated record
            }
            or
            {
                "success": False,
                "error": str  # Error description, for example if appointment not found or invalid status
            }

        Constraints:
            - The appointment_id must exist in the appointments collection.
            - Status should be a valid value ("pending", "confirmed", "cancelled").
        """
        allowed_statuses = {"pending", "confirmed", "cancelled"}
        if appointment_id not in self.appointments:
            return { "success": False, "error": "Appointment not found." }

        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed: {allowed_statuses}" }

        self.appointments[appointment_id]["status"] = new_status
        return { "success": True, "data": self.appointments[appointment_id] }

    def modify_counselor_schedule(
        self,
        counselor_id: str,
        add_times: List[str] = None,
        remove_times: List[str] = None
    ) -> dict:
        """
        Add or remove time slots in a counselor's availability schedule.
    
        Args:
            counselor_id (str): The counselor whose schedule to modify.
            add_times (List[str], optional): Time slots to add.
            remove_times (List[str], optional): Time slots to remove.
        
        Returns:
            dict:
                If successful:
                    {
                        "success": True,
                        "data": CounselorInfo  # Updated counselor record
                    }
                If failure (e.g., counselor not found):
                    {
                        "success": False,
                        "error": str
                    }
    
        Constraints:
            - can only remove time slots if no confirmed appointment exists at that time.
            - cannot add duplicate time slots.
            - counselor_id must exist.
        """
        if counselor_id not in self.counselors:
            return { "success": False, "error": "Counselor not found." }

        counselor = self.counselors[counselor_id]
        original_schedule = set(counselor["availability_schedule"])
        added = []
        removed = []
        not_removed = []

        # Add time slots
        if add_times:
            for t in add_times:
                if t not in original_schedule:
                    counselor["availability_schedule"].append(t)
                    added.append(t)
            # Ensure no duplicates
            counselor["availability_schedule"] = list(set(counselor["availability_schedule"]))
    
        # Remove time slots
        if remove_times:
            for t in remove_times:
                # Cannot remove if blocked by confirmed appointment at this time
                blocked = False
                for appt in self.appointments.values():
                    if (
                        appt["counselor_id"] == counselor_id
                        and appt["scheduled_time"] == t
                        and appt["status"] == "confirmed"
                    ):
                        blocked = True
                        break
                if blocked:
                    not_removed.append(t)
                elif t in counselor["availability_schedule"]:
                    counselor["availability_schedule"].remove(t)
                    removed.append(t)

        self.counselors[counselor_id] = counselor
        return {
            "success": True,
            "data": counselor
        }

    def update_counselor_expertise(
        self,
        counselor_id: str,
        add_types: List[str] = None,
        remove_types: List[str] = None
    ) -> dict:
        """
        Add or remove counseling types (by type_id) from a counselor's expertise areas.

        Args:
            counselor_id (str): The ID of the counselor to update.
            add_types (List[str], optional): Counseling type IDs to add.
            remove_types (List[str], optional): Counseling type IDs to remove.

        Returns:
            dict: {
                "success": True,
                "data": CounselorInfo  # Updated counselor record
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only valid counseling_type_id can be added or removed.
            - No duplicate type_ids in expertise_areas.
        """
        if counselor_id not in self.counselors:
            return { "success": False, "error": "Counselor does not exist" }
        counselor_info = self.counselors[counselor_id]
        expertise_areas = set(counselor_info.get("expertise_areas", []))

        # Validate type IDs
        valid_type_ids = set(self.counseling_types.keys())
        add_types = add_types or []
        remove_types = remove_types or []

        # Check for invalid type IDs
        invalid_add = [tid for tid in add_types if tid not in valid_type_ids]
        invalid_remove = [tid for tid in remove_types if tid not in valid_type_ids]

        if invalid_add:
            return {
                "success": False,
                "error": f"Invalid counseling_type_id(s) in add_types: {invalid_add}"
            }
        if invalid_remove:
            return {
                "success": False,
                "error": f"Invalid counseling_type_id(s) in remove_types: {invalid_remove}"
            }

        # Remove requested types
        expertise_areas.difference_update(remove_types)
        # Add requested types
        expertise_areas.update(add_types)

        counselor_info["expertise_areas"] = list(expertise_areas)
        self.counselors[counselor_id] = counselor_info

        return {
            "success": True,
            "data": counselor_info
        }

    def cancel_appointment(self, appointment_id: str) -> dict:
        """
        Cancel a specific appointment and release the time slot.

        Args:
            appointment_id (str): The unique identifier of the appointment to cancel.

        Returns:
            dict: 
              - On success: {
                    "success": True,
                    "status": "cancelled",
                    "message": "Appointment <id> cancelled and time slot released"
                }
              - On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The appointment must exist.
            - Updates the appointment status to "cancelled".
            - Removes appointment from counselor's assigned_appointments (if present).
            - Cancelled appointments should not block counselor's schedule.
        """
        # Check appointment existence
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment not found"}

        if appointment.get("status") == "cancelled":
            return {"success": False, "error": "Appointment is already cancelled"}

        # Update status
        appointment["status"] = "cancelled"
        self.appointments[appointment_id] = appointment

        # Update counselor's assigned_appointments
        counselor_id = appointment.get("counselor_id")
        counselor = self.counselors.get(counselor_id)
        if counselor:
            assigned_list = counselor.get("assigned_appointments", [])
            if appointment_id in assigned_list:
                assigned_list.remove(appointment_id)
                counselor["assigned_appointments"] = assigned_list
                self.counselors[counselor_id] = counselor

        return {
            "success": True,
            "status": "cancelled",
            "message": f"Appointment {appointment_id} cancelled and time slot released"
        }

    def delete_appointment(self, appointment_id: str) -> dict:
        """
        Remove an appointment record entirely from the system.

        Args:
            appointment_id (str): Unique identifier for the appointment to delete.

        Returns:
            dict: 
                - On success: {"success": True, "deleted_id": "<appointment_id>"}
                - On error: {"success": False, "error": <reason>}
    
        Constraints:
            - Appointment must exist.
            - Appointment is removed from appointments DB.
            - If possible, remove appointment ID from counselor's assigned_appointments list.
        """
        # Check if appointment exists
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return { "success": False, "error": "Appointment ID does not exist." }

        counselor_id = appointment["counselor_id"]

        # Remove from appointment records
        del self.appointments[appointment_id]

        # Update counselor assignment (if counselor exists)
        if counselor_id in self.counselors:
            assigned = self.counselors[counselor_id]["assigned_appointments"]
            if appointment_id in assigned:
                assigned.remove(appointment_id)
            # No error if appointment_id is not in the list (silent ignore)

        return { "success": True, "deleted_id": appointment_id }

    def create_client(self, client_id: str, name: str, contact_info: str) -> dict:
        """
        Register a new client on the platform.

        Args:
            client_id (str): Unique identifier for the client.
            name (str): Name of the client.
            contact_info (str): Contact information (e.g. email, phone).

        Returns:
            dict: 
                On success: { "success": True, "id": "<client_id>", "data": ClientInfo }
                If client_id exists: { "success": False, "error": "Client ID already exists." }
                If missing fields: { "success": False, "error": "Missing required client information." }

        Constraints:
            - client_id must be unique within the system.
            - name and contact_info must be non-empty strings.
        """
        if not client_id or not name or not contact_info:
            return { "success": False, "error": "Missing required client information." }

        if client_id in self.clients:
            return { "success": False, "error": "Client ID already exists." }

        new_client: ClientInfo = {
            "client_id": client_id,
            "name": name,
            "contact_info": contact_info,
        }
        self.clients[client_id] = new_client
        return { "success": True, "id": client_id, "data": new_client }

    def update_client_info(self, client_id: str, name: str = None, contact_info: str = None) -> dict:
        """
        Modify the details (name/contact_info) of an existing client.

        Args:
            client_id (str): Unique identifier of the client to update.
            name (str, optional): New name for the client.
            contact_info (str, optional): New contact info for the client.

        Returns:
            dict: {
                "success": True,
                "data": ClientInfo  # Updated record
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - client_id must exist in the system.
            - Only provided fields (name/contact_info) are updated; missing ones are unchanged.
            - If neither name nor contact_info is provided, no changes are made.
        """
        client = self.clients.get(client_id)
        if client is None:
            return { "success": False, "error": "Client not found" }
        if name is None and contact_info is None:
            return { "success": False, "error": "No update parameters provided" }

        if name is not None:
            client["name"] = name
        if contact_info is not None:
            client["contact_info"] = contact_info

        return { "success": True, "data": client }