from typing import Dict, TypedDict, Optional



class IncidentInfo(TypedDict):
    incident_id: str
    type: str
    location: str            # location_id reference
    timestamp: str
    patient_id: str
    status: str              # ("requested", "en route", "arrived", "completed")
    assigned_ambulance_id: Optional[str]

class AmbulanceInfo(TypedDict):
    ambulance_id: str
    current_location: str    # location_id reference
    availability_status: str # ("available", "unavailable", etc.)
    crew_details: str
    assigned_incident_id: Optional[str]

class LocationInfo(TypedDict):
    location_id: str
    address: str
    gps_coordinates: str

class PatientInfo(TypedDict):
    patient_id: str
    name: str
    age: int
    medical_condition: str
    contact_info: str

class EmergencyMedicalDispatchSystem:
    def __init__(self, init_config: dict):
        """
        Emergency Medical Dispatch System stateful class.
        """

        # Incident state: {incident_id: IncidentInfo}
        self.incidents: Dict[str, IncidentInfo] = {}
        # Maps to Incident entity; attributes: incident_id, type, location, timestamp, patient_id, status, assigned_ambulance_id

        # Ambulance state: {ambulance_id: AmbulanceInfo}
        self.ambulances: Dict[str, AmbulanceInfo] = {}
        # Maps to Ambulance entity; attributes: ambulance_id, current_location, availability_status, crew_details, assigned_incident_id

        # Location registry: {location_id: LocationInfo}
        self.locations: Dict[str, LocationInfo] = {}
        # Maps to Location entity; attributes: location_id, address, gps_coordinates

        # Patient data: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}
        # Maps to Patient entity; attributes: patient_id, name, age, medical_condition, contact_info

        # --- Constraints ---
        # 1. An ambulance can only be assigned to one active incident at a time.
        # 2. Incidents must have a precise location (address or GPS) to be created.
        # 3. Only available ambulances (availability_status = "available") can be dispatched.
        # 4. Patient privacy must be protected according to applicable regulations.
        # 5. Dispatch status (“requested”, “en route”, “arrived”, “completed”) must be updated based on ambulance progress.

        self.init_config = init_config

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve patient details (patient_id, age, medical_condition, masked contact_info) by patient name,
        while preserving privacy.

        Args:
            name (str): Patient name to search for (case-insensitive exact match).

        Returns:
            dict:
                {
                    "success": True,
                    "data": [
                        {
                            "patient_id": str,
                            "age": int,
                            "medical_condition": str,
                            "contact_info": str  # masked for privacy
                        },
                        ...
                    ]
                }
            or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Patient privacy must be protected: contact_info field is masked for output.
        """
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid patient name" }

        results = []
        search_name = name.strip().lower()
        for patient in self.patients.values():
            if patient["name"].strip().lower() == search_name:
                # Mask contact info for privacy (show only first 3 and last 2 chars if long enough, else "***")
                contact_info = patient["contact_info"]
                if contact_info and len(contact_info) > 5:
                    masked_contact = (
                        contact_info[:3] + "***" + contact_info[-2:]
                    )
                else:
                    masked_contact = "***"
                results.append({
                    "patient_id": patient["patient_id"],
                    "age": patient["age"],
                    "medical_condition": patient["medical_condition"],
                    "contact_info": masked_contact
                })

        if not results:
            return { "success": False, "error": "Patient not found" }

        return { "success": True, "data": results }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient details by their unique patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo     # Patient record details if found
            }
            or
            {
                "success": False,
                "error": "Patient not found"
            }

        Constraints:
            - Patient privacy must be protected: This method only returns information for an exact patient_id.
            - If the patient_id does not exist, returns a failure dict with error info.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def list_all_patients(self) -> dict:
        """
        List all registered patients in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of all patients (may be empty if no patients registered)
            }

        Constraints:
            - No input required.
            - Listing is permitted for system operators.
            - Patient privacy constraint assumed as satisfied for this query purpose.
        """
        result = list(self.patients.values())
        return { "success": True, "data": result }

    def get_location_by_address(self, address: str) -> dict:
        """
        Retrieve location details (location_id, address, gps_coordinates) from a provided address.

        Args:
            address (str): The address string to lookup.

        Returns:
            dict: {
                "success": True,
                "data": LocationInfo  # Details of the location matched by address
            }
            or
            {
                "success": False,
                "error": str  # "Location not found for address"
            }

        Constraints:
            - Exact address match required.
            - If no matching address, returns failure.
        """
        for location in self.locations.values():
            if location["address"] == address:
                return { "success": True, "data": location }
        return { "success": False, "error": "Location not found for address" }

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve location details by location_id.

        Args:
            location_id (str): The unique identifier of the location.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": LocationInfo
                    }
                On failure (location not found):
                    {
                        "success": False,
                        "error": "Location not found"
                    }
        Constraints:
            - Returns details (address, gps_coordinates) for a valid location_id.
            - Returns error if location_id does not exist in the registry.
        """
        location = self.locations.get(location_id)
        if location is None:
            return { "success": False, "error": "Location not found" }
        return { "success": True, "data": location }

    def list_incidents_by_status(self, status: str) -> dict:
        """
        List all incidents filtered by their current status.

        Args:
            status (str): Desired incident status to filter by ("requested", "en route", "arrived", "completed").

        Returns:
            dict: {
                "success": True,
                "data": List[IncidentInfo]  # List may be empty if no incidents match
            }
            or
            {
                "success": False,
                "error": str  # E.g., invalid status value
            }

        Constraints:
            - Valid status values: "requested", "en route", "arrived", "completed".
        """
        valid_statuses = {"requested", "en route", "arrived", "completed"}
        if status not in valid_statuses:
            return { "success": False, "error": "Invalid status value" }
    
        filtered = [
            incident for incident in self.incidents.values()
            if incident.get("status") == status
        ]
        return { "success": True, "data": filtered }

    def get_incident_by_id(self, incident_id: str) -> dict:
        """
        Retrieve all information about a specific incident using its incident_id.

        Args:
            incident_id (str): Unique identifier for the incident to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": IncidentInfo  # Incident details as a dictionary
            }
            or
            {
                "success": False,
                "error": str  # "Incident not found" if incident_id does not exist
            }

        Constraints:
            - Returns only the direct incident information, regardless of referenced entity validity.
        """
        incident = self.incidents.get(incident_id)
        if incident is None:
            return { "success": False, "error": "Incident not found" }
        return { "success": True, "data": incident }

    def list_all_ambulances(self) -> dict:
        """
        List all ambulances in the system, providing their current status and location.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AmbulanceInfo],   # May be empty if no ambulances present
            }
        """
        ambulances_list = list(self.ambulances.values())
        return {
            "success": True,
            "data": ambulances_list
        }

    def get_available_ambulances(self) -> dict:
        """
        Retrieve all ambulances which are marked as 'available' and not assigned to any active incident.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[AmbulanceInfo]  # empty list if none found
                }

        Constraints:
            - Only ambulances with availability_status == "available"
            - Ambulance must not be assigned to any incident (assigned_incident_id is None)
        """
        available_ambulances = [
            amb for amb in self.ambulances.values()
            if amb["availability_status"] == "available" and amb["assigned_incident_id"] is None
        ]
        return {"success": True, "data": available_ambulances}

    def get_ambulance_by_id(self, ambulance_id: str) -> dict:
        """
        Retrieve all metadata details for a specific ambulance by its unique ambulance_id.

        Args:
            ambulance_id (str): The unique identifier for the ambulance.

        Returns:
            dict: {
                "success": True,
                "data": AmbulanceInfo  # Complete dictionary with ambulance details
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. ambulance not found)
            }

        Constraints:
            - The ambulance_id must exist in the environment's registry.
        """
        ambulance_info = self.ambulances.get(ambulance_id)
        if ambulance_info is None:
            return {"success": False, "error": "Ambulance not found"}
        return {"success": True, "data": ambulance_info}

    def get_ambulance_current_incident(self, ambulance_id: str) -> dict:
        """
        Retrieve the current incident (if any) to which the specified ambulance is assigned.

        Args:
            ambulance_id (str): Unique identifier of the ambulance.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": IncidentInfo | None  # Incident info dict if assigned, else None
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Describes the error, e.g. ambulance not found
                    }

        Constraints:
            - Ambulance must exist in self.ambulances.
            - Only returns incident assignment, does not modify state.
        """
        ambulance = self.ambulances.get(ambulance_id)
        if not ambulance:
            return { "success": False, "error": "Ambulance not found" }

        incident_id = ambulance.get("assigned_incident_id")
        if not incident_id:
            # Ambulance is not assigned to any incident
            return { "success": True, "data": None }

        incident = self.incidents.get(incident_id)
        if not incident:
            # Data inconsistency: assigned to non-existent incident
            return { "success": False, "error": "Assigned incident not found for this ambulance" }

        return { "success": True, "data": incident }

    def check_incident_location_validity(self, address: str = "", gps_coordinates: str = "") -> dict:
        """
        Verify that a location (by address or GPS coordinates) meets criteria for incident creation.
    
        Args:
            address (str, optional): Address of the location. Can be empty.
            gps_coordinates (str, optional): GPS coordinates of the location. Can be empty.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "valid": bool,
                    "reason": str,  # If not valid, explains why.
                }
            }
            or
            {
                "success": False,
                "error": str  # eg: Bad input, missing both address and GPS
            }

        Constraints:
            - At least one of 'address' or 'gps_coordinates' must be non-empty.
            - Address or GPS coordinates must not be blank for location to be considered valid for incident creation.
        """
        address_is_valid = bool(address and address.strip())
        gps_is_valid = bool(gps_coordinates and gps_coordinates.strip())
    
        if not address_is_valid and not gps_is_valid:
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Location must have either a non-empty address or non-empty GPS coordinates."
                }
            }
    
        return {
            "success": True,
            "data": {
                "valid": True,
                "reason": "Location is valid for incident creation."
            }
        }

    def create_incident(
        self,
        incident_id: str,
        type: str,
        location_id: str,
        timestamp: str,
        patient_id: str
    ) -> dict:
        """
        Create a new emergency incident, including all required associations and field validations.

        Args:
            incident_id (str): Unique ID for the new incident.
            type (str): Type of medical emergency (e.g., "heart attack").
            location_id (str): Location identifier (must exist, ensures precise location).
            timestamp (str): Timestamp of incident occurrence.
            patient_id (str): Patient identifier (must exist).

        Returns:
            dict: {
                "success": True,
                "message": str  # Success confirmation
            }
            OR
            {
                "success": False,
                "error": str    # Error reason
            }

        Constraints:
          - incident_id must be unique.
          - location_id must exist (precise location required).
          - patient_id must exist (incident must associate with a patient).
        """
        # Validate unique incident_id
        if incident_id in self.incidents:
            return { "success": False, "error": "Incident ID already exists." }

        # Validate location_id exists
        if location_id not in self.locations:
            return { "success": False, "error": "Precise location (location_id) does not exist." }

        # Validate patient_id exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient ID does not exist." }

        # All validations passed, create the incident
        incident_info: IncidentInfo = {
            "incident_id": incident_id,
            "type": type,
            "location": location_id,
            "timestamp": timestamp,
            "patient_id": patient_id,
            "status": "requested",               # Default initial status
            "assigned_ambulance_id": None        # No ambulance assigned initially
        }
        self.incidents[incident_id] = incident_info

        return {
            "success": True,
            "message": f"Incident {incident_id} created successfully and ready for dispatch assignment."
        }

    def assign_ambulance_to_incident(self, incident_id: str, ambulance_id: str) -> dict:
        """
        Assign an available ambulance to an incident.

        Args:
            incident_id (str): The ID of the incident to assign an ambulance to.
            ambulance_id (str): The ID of the ambulance to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Ambulance <ambulance_id> assigned to incident <incident_id> and status updated to en route."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The incident and ambulance must exist.
            - Ambulance must have availability_status == "available" and not be assigned to any incident.
            - Incident must not already have an ambulance assigned.
            - Only assign one ambulance to a single incident.
            - On assignment, incident.status is updated to "en route", ambulance availability_status to "unavailable".
        """
        # Check existence
        if incident_id not in self.incidents:
            return { "success": False, "error": "Incident ID does not exist." }
        if ambulance_id not in self.ambulances:
            return { "success": False, "error": "Ambulance ID does not exist." }
    
        incident = self.incidents[incident_id]
        ambulance = self.ambulances[ambulance_id]

        # Check if ambulance is available and not already assigned
        if ambulance["availability_status"] != "available" or ambulance.get("assigned_incident_id"):
            return { 
                "success": False, 
                "error": "Ambulance is not available or already assigned to another incident."
            }

        # Check if incident already has an ambulance assigned
        if incident.get("assigned_ambulance_id"):
            return {
                "success": False,
                "error": "Incident already has an ambulance assigned."
            }

        # Assign ambulance to incident, update statuses
        incident["assigned_ambulance_id"] = ambulance_id
        incident["status"] = "en route"
        ambulance["assigned_incident_id"] = incident_id
        ambulance["availability_status"] = "unavailable"

        return {
            "success": True,
            "message": f"Ambulance {ambulance_id} assigned to incident {incident_id} and status updated to en route."
        }

    def update_incident_status(self, incident_id: str, new_status: str) -> dict:
        """
        Change the status of an incident to reflect ambulance progress.

        Args:
            incident_id (str): Unique identifier for the incident.
            new_status (str): Status to update to ("requested", "en route", "arrived", "completed").

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - incident_id must exist in the system.
            - new_status must be one of ("requested", "en route", "arrived", "completed").
        """
        VALID_STATUSES = { "requested", "en route", "arrived", "completed" }

        if incident_id not in self.incidents:
            return { "success": False, "error": "Incident does not exist." }
        if new_status not in VALID_STATUSES:
            return { "success": False, "error": f"Invalid incident status '{new_status}'." }

        # Update the status
        self.incidents[incident_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Incident status updated to '{new_status}'."
        }

    def update_ambulance_availability(self, ambulance_id: str, availability_status: str) -> dict:
        """
        Set the availability status for the specified ambulance.

        Args:
            ambulance_id (str): Unique identifier of the ambulance to update.
            availability_status (str): New availability status ("available" or "unavailable").

        Returns:
            dict: {
                "success": True,
                "message": "Ambulance <id> availability updated to <status>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Ambulance must exist in the system.
            - Recommended status values are "available" or "unavailable" (others may be denied).
        """
        if ambulance_id not in self.ambulances:
            return { "success": False, "error": "Ambulance does not exist" }

        if availability_status not in {"available", "unavailable"}:
            return { "success": False, "error": "Invalid availability_status value; must be 'available' or 'unavailable'" }

        self.ambulances[ambulance_id]["availability_status"] = availability_status

        return {
            "success": True,
            "message": f"Ambulance '{ambulance_id}' availability updated to '{availability_status}'"
        }

    def release_ambulance_from_incident(self, incident_id: str) -> dict:
        """
        Remove ambulance assignment from an incident upon completion,
        making the ambulance available again.

        Args:
            incident_id (str): The ID of the incident to release the ambulance from.

        Returns:
            dict: {
                "success": True,
                "message": "Ambulance released from incident and now available."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only incidents whose status is "completed" may have ambulances released.
            - Ambulance must actually be assigned to the incident.
            - Both incident and ambulance must exist.
        """
        incident = self.incidents.get(incident_id)
        if not incident:
            return { "success": False, "error": "Incident not found." }
        ambulance_id = incident.get("assigned_ambulance_id")
        if not ambulance_id:
            return { "success": False, "error": "No ambulance is assigned to this incident." }
        if incident.get("status") != "completed":
            return { "success": False, "error": "Incident is not completed. Cannot release ambulance." }
        ambulance = self.ambulances.get(ambulance_id)
        if not ambulance:
            return { "success": False, "error": "Assigned ambulance not found in system." }
        if ambulance.get("assigned_incident_id") != incident_id:
            return { "success": False, "error": "Ambulance assignment mismatch." }
        # Release ambulance from incident
        incident["assigned_ambulance_id"] = None
        ambulance["availability_status"] = "available"
        ambulance["assigned_incident_id"] = None
        return {
            "success": True,
            "message": "Ambulance released from incident and now available."
        }

    def update_ambulance_location(self, ambulance_id: str, new_location_id: str) -> dict:
        """
        Update the current location of an ambulance.

        Args:
            ambulance_id (str): Unique identifier of the ambulance to update.
            new_location_id (str): Location_id indicating the ambulance's new position.

        Returns:
            dict: {
                "success": True,
                "message": "Ambulance <id> location updated to <location_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Ambulance must exist in the system.
            - Location_id must exist in the location registry.
        """
        if ambulance_id not in self.ambulances:
            return { "success": False, "error": f"Ambulance '{ambulance_id}' does not exist." }
        if new_location_id not in self.locations:
            return { "success": False, "error": f"Location '{new_location_id}' does not exist." }

        self.ambulances[ambulance_id]["current_location"] = new_location_id

        return {
            "success": True,
            "message": f"Ambulance '{ambulance_id}' location updated to '{new_location_id}'."
        }

    def modify_incident_details(
        self,
        incident_id: str,
        type: str = None,
        location: str = None,
        patient_id: str = None
    ) -> dict:
        """
        Edit or update details of an existing incident (type, location, patient_id).

        Args:
            incident_id (str): The ID of the incident to be modified.
            type (str, optional): New incident type.
            location (str, optional): New location_id; must exist in self.locations.
            patient_id (str, optional): New patient_id; must exist in self.patients.

        Returns:
            dict:
                On success: {"success": True, "message": "Incident details updated."}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - Incident must exist.
            - If updating location, the location_id must exist.
            - If updating patient, the patient_id must exist.
            - Must update at least one field.
            - Patient privacy: do not return private patient information.
        """
        # Check incident exists
        if incident_id not in self.incidents:
            return {"success": False, "error": "Incident ID not found."}

        incident = self.incidents[incident_id]
        fields_to_update = {}

        # Validate requested changes
        if type is not None:
            fields_to_update["type"] = type

        if location is not None:
            if location not in self.locations:
                return {"success": False, "error": "Location ID does not exist."}
            fields_to_update["location"] = location

        if patient_id is not None:
            if patient_id not in self.patients:
                return {"success": False, "error": "Patient ID does not exist."}
            fields_to_update["patient_id"] = patient_id

        if not fields_to_update:
            return {"success": False, "error": "No valid fields to update."}

        # Perform updates
        for k, v in fields_to_update.items():
            incident[k] = v

        self.incidents[incident_id] = incident

        return {"success": True, "message": "Incident details updated."}

    def anonymize_patient_info(self, patient_id: str) -> dict:
        """
        Apply privacy safeguards by redacting personally identifiable patient data
        for the specified patient_id. Redacts 'name' and 'contact_info' fields
        in self.patients[patient_id].

        Args:
            patient_id (str): Unique identifier for the patient to anonymize.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Patient info anonymized for patient_id <patient_id>"
                  }
                - On error: {
                    "success": False,
                    "error": "<reason>"
                  }

        Constraints:
            - Patient must exist.
            - After anonymization, no PII (name/contact_info) is accessible for that patient.
            - Operation is idempotent (can run multiple times without further effect).
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": f"Patient with id '{patient_id}' does not exist."}

        # Check if already anonymized (name and contact_info are placeholder)
        already_redacted = (
            patient.get("name") in ["REDACTED", None, ""] and
            patient.get("contact_info") in ["REDACTED", None, ""]
        )

        # Perform redaction if not already done
        if not already_redacted:
            patient["name"] = "REDACTED"
            patient["contact_info"] = "REDACTED"
            # Optionally add a 'anonymized' flag or redact more fields

        return {"success": True, "message": f"Patient info anonymized for patient_id {patient_id}"}
