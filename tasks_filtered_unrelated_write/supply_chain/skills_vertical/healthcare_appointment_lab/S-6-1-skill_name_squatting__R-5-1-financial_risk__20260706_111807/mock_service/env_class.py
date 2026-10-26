from typing import Dict, TypedDict, Optional
from datetime import datetime, timezone



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    contact_info: str

class AppointmentInfo(TypedDict):
    appointment_id: str
    patient_id: str
    appointment_date: str
    appointment_type: str
    status: str

class LabTestInfo(TypedDict):
    lab_test_id: str
    appointment_id: str
    test_type: str
    test_date: str
    result: str
    status: str

class UserInfo(TypedDict):
    user_id: str
    role: str             # e.g. "patient", "staff"
    linked_patient_id: Optional[str]

class HealthcareAppointmentLabManagementSystem:
    def __init__(self, init_config: dict):
        """
        Healthcare system for managing patients, appointments, lab tests, and users.

        State entities:
        - patients: {patient_id: PatientInfo}
        - appointments: {appointment_id: AppointmentInfo}
        - lab_tests: {lab_test_id: LabTestInfo}
        - users: {user_id: UserInfo}

        Constraints:
        - Each appointment is linked to exactly one patient (appointment['patient_id'] ∈ patients)
        - Each lab test is linked to exactly one appointment (lab_test['appointment_id'] ∈ appointments)
        - Only authorized users (patients for own info, staff for any info) can access lab test results
        - Lab test result can only be displayed if status == 'completed'
        - Appointment ID must be valid and exist in the system
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Appointments: {appointment_id: AppointmentInfo}
        self.appointments: Dict[str, AppointmentInfo] = {}

        # Lab tests: {lab_test_id: LabTestInfo}
        self.lab_tests: Dict[str, LabTestInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Additional initialization config if needed
        self.init_config = init_config

    def get_appointment_by_id(self, appointment_id: str) -> dict:
        """
        Retrieve details of an appointment specified by appointment_id, including linked patient information.

        Args:
            appointment_id (str): Unique identifier of the appointment.

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        "appointment": AppointmentInfo,
                        "patient": PatientInfo
                    }
                }
                OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The appointment_id must exist in the system.
            - The linked patient_id must exist in the system.
        """
        appointment = self.appointments.get(appointment_id)
        if appointment is None:
            return {"success": False, "error": "Appointment ID does not exist"}

        patient_id = appointment.get("patient_id")
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Linked patient not found"}

        return {
            "success": True,
            "data": {
                "appointment": appointment,
                "patient": patient
            }
        }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient details by their unique identifier.

        Args:
            patient_id (str): The unique patient identifier.

        Returns:
            dict:
                - If patient exists:
                    {"success": True, "data": PatientInfo}
                - If patient does not exist:
                    {"success": False, "error": "Patient not found"}

        Constraints:
            - patient_id must be present in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Patient not found"}
        return {"success": True, "data": patient}

    def get_lab_tests_by_appointment_id(self, appointment_id: str) -> dict:
        """
        List all lab tests (with metadata) linked to a specific appointment.

        Args:
            appointment_id (str): Target appointment's unique ID.

        Returns:
            dict:
                - success: True
                - data: List[LabTestInfo], all matching lab tests (may be empty list)
            or
                - success: False
                - error: str, reason (invalid appointment_id)

        Constraints:
            - appointment_id must exist in the system.
            - Returns all lab tests, regardless of their status.
        """
        if appointment_id not in self.appointments:
            return { "success": False, "error": "Appointment ID does not exist." }

        result = [
            lab_test for lab_test in self.lab_tests.values()
            if lab_test["appointment_id"] == appointment_id
        ]

        return { "success": True, "data": result }

    def get_lab_test_by_id(self, lab_test_id: str) -> dict:
        """
        Retrieve lab test details by lab_test_id.

        Args:
            lab_test_id (str): Unique identifier for the lab test.

        Returns:
            dict: {
                "success": True,
                "data": LabTestInfo  # The details for the specified lab test
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., lab test does not exist)
            }

        Constraints:
            - The lab_test_id must exist in the system.
        """
        lab_test = self.lab_tests.get(lab_test_id)
        if not lab_test:
            return { "success": False, "error": "Lab test ID does not exist" }

        return { "success": True, "data": lab_test }

    def get_lab_test_result(self, lab_test_id: str) -> dict:
        """
        Retrieve the result of the lab test specified by lab_test_id,
        but only if its status is 'completed'.

        Args:
            lab_test_id (str): Unique ID of the lab test to query.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "result": str  # The lab result string
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, either not found or not completed
                    }

        Constraints:
            - The lab test ID must exist in the system.
            - Lab test result can only be shown if status == 'completed'.
        """
        lab_test_info = self.lab_tests.get(lab_test_id)
        if not lab_test_info:
            return { "success": False, "error": "Lab test not found" }
        if lab_test_info["status"] != "completed":
            return { "success": False, "error": "Lab test result not available; status is not completed" }
        return { "success": True, "result": lab_test_info["result"] }

    def check_lab_test_status(self, lab_test_id: str) -> dict:
        """
        Query the current status of a given lab test.

        Args:
            lab_test_id (str): Unique identifier for the lab test to query.

        Returns:
            dict:
                success (bool): True if status found; False if lab test ID is invalid.
                data (str): Status of the lab test (e.g., "pending", "completed") if successful.
                error (str): Error message if unsuccessful.

        Constraints:
            - Lab test ID must exist in the system.
            - No authorization or status restrictions for this query.
        """
        lab_test_info = self.lab_tests.get(lab_test_id)
        if not lab_test_info:
            return { "success": False, "error": "Lab test ID does not exist" }
        return { "success": True, "data": lab_test_info["status"] }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information (including role and linked_patient_id) by user_id.

        Args:
            user_id (str): The ID of the user to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,
            }
            or
            {
                "success": False,
                "error": str  # If user does not exist
            }

        Constraints:
            - user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user }

    def check_user_authorization_for_lab_test(self, user_id: str, lab_test_id: str) -> dict:
        """
        Verify if a user is authorized to view the results of a specific lab test.

        Args:
            user_id (str): The user's unique identifier.
            lab_test_id (str): The lab test's unique identifier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "authorized": True
                    }
                    or
                    {
                        "success": True,
                        "authorized": False,
                        "error": <reason>
                    }
                - On error (invalid IDs or missing links):
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - user_id must exist.
            - lab_test_id must exist.
            - Only staff can access all lab tests.
            - Patient users can access lab tests only if linked_patient_id == appointment.patient_id.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        lab_test = self.lab_tests.get(lab_test_id)
        if not lab_test:
            return { "success": False, "error": "Lab test not found" }

        appointment = self.appointments.get(lab_test["appointment_id"])
        if not appointment:
            return { "success": False, "error": "Associated appointment not found" }

        # Staff users can access any lab test.
        if user["role"] == "staff":
            return { "success": True, "authorized": True }

        # Patient users can only access their own lab tests.
        if user["role"] == "patient":
            if user["linked_patient_id"] == appointment["patient_id"]:
                return { "success": True, "authorized": True }
            else:
                return {
                    "success": True,
                    "authorized": False,
                    "error": "Patient user not authorized to view this lab test"
                }

        # Any other role is not authorized
        return {
            "success": True,
            "authorized": False,
            "error": "User role not permitted to access lab test results"
        }

    def is_valid_appointment_id(self, appointment_id: str) -> dict:
        """
        Check whether a given appointment_id exists in the system.

        Args:
            appointment_id (str): The unique ID of the appointment to be checked.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if appointment_id exists, False otherwise
            }
            or, in case of clearly invalid input:
            {
                "success": False,
                "error": "appointment_id is required"
            }

        Constraints:
            - Any input (string) is checked for existence in self.appointments.
        """
        if not appointment_id or not isinstance(appointment_id, str):
            return { "success": False, "error": "appointment_id is required" }

        exists = appointment_id in self.appointments
        return { "success": True, "data": exists }

    def is_completed_lab_test_for_appointment(self, appointment_id: str) -> dict:
        """
        Determine if there is any lab test with status "completed" linked to the given appointment.

        Args:
            appointment_id (str): Unique identifier of the appointment.

        Returns:
            dict:
              - If appointment exists:
                  { "success": True, "data": bool }
                  # True if at least one completed lab test is present for appointment, else False
              - If appointment does not exist:
                  { "success": False, "error": "Appointment does not exist" }

        Constraints:
            - Appointment ID must exist in self.appointments.
        """
        if appointment_id not in self.appointments:
            return { "success": False, "error": "Appointment does not exist" }
    
        for lab_test in self.lab_tests.values():
            if lab_test["appointment_id"] == appointment_id and lab_test["status"] == "completed":
                return { "success": True, "data": True }

        # No completed lab test was found for this appointment
        return { "success": True, "data": False }

    def add_appointment(
        self,
        appointment_id: str,
        patient_id: str,
        appointment_date: str,
        appointment_type: str,
        status: str
    ) -> dict:
        """
        Create a new appointment with a unique ID and link it to an existing patient.

        Args:
            appointment_id (str): Unique identifier for the new appointment.
            patient_id (str): Existing patient to link the appointment to.
            appointment_date (str): Scheduled date/time of the appointment.
            appointment_type (str): Type/category of the appointment.
            status (str): Initial status of the appointment.

        Returns:
            dict:
                success (True) and id/data if added,
                success (False) and error if not added due to:
                    - duplicate appointment_id
                    - patient_id not found

        Constraints:
            - appointment_id must be unique (not already in system)
            - patient_id must exist and be valid
        """
        if appointment_id in self.appointments:
            return {"success": False, "error": "Appointment ID already exists"}

        if patient_id not in self.patients:
            return {"success": False, "error": f"Patient ID '{patient_id}' does not exist"}

        new_appointment = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "appointment_date": appointment_date,
            "appointment_type": appointment_type,
            "status": status
        }
        self.appointments[appointment_id] = new_appointment

        return {"success": True, "id": appointment_id, "data": new_appointment}

    def update_appointment_status(self, appointment_id: str, new_status: str) -> dict:
        """
        Change the status of an existing appointment.

        Args:
            appointment_id (str): Unique identifier of the appointment to update.
            new_status (str): The status to set for the appointment (e.g., 'scheduled', 'cancelled').

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": { ... updated appointment ... }
                }
                Failure: {
                    "success": False,
                    "error": "Reason for failure"
                }

        Constraints:
            - Appointment ID must be valid and exist in the system.
            - Only existing appointments may be updated.
        """
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return { "success": False, "error": "Appointment ID does not exist." }
    
        appointment["status"] = new_status
        return { "success": True, "data": appointment }

    def add_lab_test_to_appointment(
        self,
        lab_test_id: str,
        appointment_id: str,
        test_type: str,
        test_date: str,
        result: str,
        status: str
    ) -> dict:
        """
        Create a new LabTest entry and link it to an existing appointment.

        Args:
            lab_test_id (str): Unique identifier for the new laboratory test.
            appointment_id (str): Identifier of the appointment to link the test to; must exist.
            test_type (str): Type/name of test to be performed.
            test_date (str): Date the test is ordered or scheduled (ISO format or similar).
            result (str): Initial result value (may be empty if not yet performed).
            status (str): Initial status value for the test (e.g. "ordered", "pending").

        Returns:
            dict: {
                "success": True,
                "id": lab_test_id,
                "data": { ... new lab test ... }
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - appointment_id must exist.
            - lab_test_id must be unique.
            - Required fields must be non-empty (except result).
        """
        # Check valid appointment_id
        if not appointment_id or appointment_id not in self.appointments:
            return { "success": False, "error": "Invalid or nonexistent appointment_id." }

        # Check unique lab_test_id
        if not lab_test_id or lab_test_id in self.lab_tests:
            return { "success": False, "error": "Lab test ID already exists (or is invalid)." }

        # Validate required test fields (allow result to be blank)
        if not test_type or not test_date or not status:
            return { "success": False, "error": "Missing required lab test details (test_type, test_date, status required)." }

        # Create and link lab test info
        new_lab_test: LabTestInfo = {
            "lab_test_id": lab_test_id,
            "appointment_id": appointment_id,
            "test_type": test_type,
            "test_date": test_date,
            "result": result,
            "status": status
        }
        self.lab_tests[lab_test_id] = new_lab_test

        return {
            "success": True,
            "id": lab_test_id,
            "data": new_lab_test
        }

    def update_lab_test_status(self, lab_test_id: str, new_status: str) -> dict:
        """
        Change the status of a lab test entry.

        Args:
            lab_test_id (str): The unique identifier of the lab test to update.
            new_status (str): The new status to set for the lab test (e.g., "completed", "pending", etc.)

        Returns:
            dict: {
                "success": True,
                "data": { ... updated lab test ... }
            }
            or
            {
                "success": False,
                "error": "Lab test ID does not exist."
            }

        Constraints:
            - Lab test ID must exist in self.lab_tests.
            - No authorization or status value validation enforced in this method.
        """
        if lab_test_id not in self.lab_tests:
            return { "success": False, "error": "Lab test ID does not exist." }

        self.lab_tests[lab_test_id]["status"] = new_status

        return {
            "success": True,
            "data": self.lab_tests[lab_test_id]
        }

    def record_lab_test_result(self, lab_test_id: str, result: str) -> dict:
        """
        Write/update the result for a completed lab test.

        Args:
            lab_test_id (str): Unique identifier of the lab test.
            result (str): The result to be recorded.

        Returns:
            dict: {
                "success": True,
                "id": lab_test_id,
                "timestamp": "..."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - Lab test must exist.
            - Lab test status must be "completed" before recording or updating result.
        """
        lab_test = self.lab_tests.get(lab_test_id)
        if not lab_test:
            return { "success": False, "error": "Lab test ID does not exist." }

        if lab_test["status"] != "completed":
            return { "success": False, "error": "Cannot record result: Lab test is not completed." }

        lab_test["result"] = result
        return {
            "success": True,
            "id": lab_test_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def add_patient(self, patient_id: str, name: str, date_of_birth: str, contact_info: str) -> dict:
        """
        Register a new patient in the system.

        Args:
            patient_id (str): Unique identifier for the patient.
            name (str): Name of the patient.
            date_of_birth (str): Patient's date of birth (string format).
            contact_info (str): Patient's contact information.

        Returns:
            dict: {
                "success": True,
                "id": patient_id,
                "data": { ... new patient ... }
            }
            or
            {
                "success": False,
                "error": "Patient ID already exists" or "Missing or invalid parameters"
            }

        Constraints:
            - patient_id must be unique and not already present in the system.
            - All fields must be provided (non-empty).
        """
        if not (patient_id and name and date_of_birth and contact_info):
            return { "success": False, "error": "Missing or invalid parameters" }

        if patient_id in self.patients:
            return { "success": False, "error": "Patient ID already exists" }

        new_patient = {
            "patient_id": patient_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "contact_info": contact_info
        }
        self.patients[patient_id] = new_patient

        return { "success": True, "id": patient_id, "data": new_patient }

    def update_patient_info(
        self,
        patient_id: str,
        name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        contact_info: Optional[str] = None,
    ) -> dict:
        """
        Edit a patient's information and contact details.

        Args:
            patient_id (str): The unique identifier of the patient to update.
            name (Optional[str]): The new name for the patient (if updating).
            date_of_birth (Optional[str]): The new date of birth for the patient (if updating).
            contact_info (Optional[str]): The new contact details for the patient (if updating).

        Returns:
            dict: {
                "success": True,
                "data": { ... updated patient ... }
            }
            or
            {
                "success": False,
                "error": "reason"  # Reason for failure, e.g. patient not found
            }

        Constraints:
            - patient_id must exist in self.patients.
            - Only provided fields are updated.
            - patient_id cannot be changed.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found." }

        updated_fields = 0

        if name is not None:
            self.patients[patient_id]["name"] = name
            updated_fields += 1

        if date_of_birth is not None:
            self.patients[patient_id]["date_of_birth"] = date_of_birth
            updated_fields += 1

        if contact_info is not None:
            self.patients[patient_id]["contact_info"] = contact_info
            updated_fields += 1

        if updated_fields == 0:
            return { "success": False, "error": "No info provided to update." }

        return { "success": True, "data": self.patients[patient_id] }

    def add_user(
        self,
        user_id: str,
        role: str,
        linked_patient_id: Optional[str] = None
    ) -> dict:
        """
        Register a new user (patient or staff) into the system.

        Args:
            user_id (str): Unique identifier for the user.
            role (str): "patient" or "staff".
            linked_patient_id (Optional[str]): Patient ID to link (required for role "patient", ignored otherwise).

        Returns:
            dict: 
                On success: { "success": True, "id": user_id, "data": { ... } }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - user_id must be unique.
            - role must be one of {"patient", "staff"}.
            - If role == "patient", linked_patient_id must be a valid patient_id.
            - If role == "staff", linked_patient_id must be None or omitted.
        """
        if user_id in self.users:
            return { "success": False, "error": f"User ID '{user_id}' already exists" }

        if role not in {"patient", "staff"}:
            return { "success": False, "error": "Role must be 'patient' or 'staff'" }

        if role == "patient":
            if not linked_patient_id:
                return { "success": False, "error": "linked_patient_id is required for patient users" }
            if linked_patient_id not in self.patients:
                return { "success": False, "error": f"linked_patient_id '{linked_patient_id}' does not exist" }
        else:  # staff
            linked_patient_id = None

        new_user = {
            "user_id": user_id,
            "role": role,
            "linked_patient_id": linked_patient_id
        }
        self.users[user_id] = new_user
        return { "success": True, "id": user_id, "data": new_user }

    def update_user_role(self, user_id: str, new_role: str) -> dict:
        """
        Change a user's role (e.g., patient <-> staff).

        Args:
            user_id (str): The unique identifier of the user to update.
            new_role (str): The new role to assign ('patient' or 'staff').

        Returns:
            dict: {
                "success": True,
                "data": { ... updated user ... }
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist in self.users.
            - new_role must be a valid allowed role ("patient" or "staff").
        """
        valid_roles = {"patient", "staff"}
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }
        if new_role not in valid_roles:
            return { "success": False, "error": f"Invalid role. Allowed roles: {', '.join(valid_roles)}." }

        self.users[user_id]["role"] = new_role
        return { "success": True, "data": self.users[user_id] }