from typing import Dict, List, TypedDict
import uuid
import datetime



# Represents Patient entity
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    gender: str
    contact_info: str
    medical_history: str

# Represents Department entity
class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    location: str

# Represents Procedure entity
class ProcedureInfo(TypedDict):
    procedure_id: str
    name: str
    description: str

# Represents SurgeryWaitlistEntry entity
class SurgeryWaitlistEntryInfo(TypedDict):
    entry_id: str
    patient_id: str
    department_id: str
    procedure_id: str
    status: str         # "pending", "scheduled", "completed", "cancelled"
    added_date: str
    scheduled_date: str

class HospitalPatientManagementSystem:
    def __init__(self, init_config: dict):
        """
        Hospital Patient Management System stateful environment.

        Constraints:
        - A patient can be on multiple departmental waitlists, but one entry per procedure per department.
        - Each SurgeryWaitlistEntry.status can be "pending", "scheduled", "completed", or "cancelled".
        - Patient must exist in the system before being added to a waitlist.
        - Procedure must be available and valid for the chosen department.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Departments: {department_id: DepartmentInfo}
        self.departments: Dict[str, DepartmentInfo] = {}

        # Procedures: {procedure_id: ProcedureInfo}
        self.procedures: Dict[str, ProcedureInfo] = {}

        # Surgery Waitlist Entries: {entry_id: SurgeryWaitlistEntryInfo}
        self.surgery_waitlist_entries: Dict[str, SurgeryWaitlistEntryInfo] = {}

        self.init_config = init_config

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve patient details and patient_id(s) using the patient's name.

        Args:
            name (str): The full name of the patient to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of patient infos matching the name
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., no match
            }

        Constraints:
            - If name is empty, operation fails (name must be specified).
            - If no patients match by name, operation fails.
            - Multiple patients with the same name are all returned.
        """
        if not name or not name.strip():
            return { "success": False, "error": "Patient name must be provided" }
    
        results = [info for info in self.patients.values() if info["name"] == name]

        if not results:
            return { "success": False, "error": "No patient found with the given name" }

        return { "success": True, "data": results }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient information for the given patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # Patient's complete information
            }
            OR
            {
                "success": False,
                "error": str  # "Patient not found"
            }

        Constraints:
            - The patient_id must exist in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def list_all_patients(self) -> dict:
        """
        Returns all patient records currently present in the hospital system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo],  # List of all patients' info (may be empty)
            }

        Constraints:
            - None.

        Edge cases:
            - If no patients exist in the system, 'data' will be an empty list.
        """
        result = list(self.patients.values())
        return { "success": True, "data": result }

    def get_department_by_name(self, name: str) -> dict:
        """
        Retrieve the department's details using its name.

        Args:
            name (str): The department's name to query.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": DepartmentInfo  # Includes department_id, name, location
                    }
                - On failure (not found):
                    {
                      "success": False,
                      "error": "Department not found"
                    }

        Constraints:
            - Department names are assumed unique.
        """
        for department_info in self.departments.values():
            if department_info["name"] == name:
                return { "success": True, "data": department_info }
        return { "success": False, "error": "Department not found" }

    def get_department_by_id(self, department_id: str) -> dict:
        """
        Retrieve department information by its unique department_id.

        Args:
            department_id (str): Unique identifier for the department.

        Returns:
            dict: {
                "success": True,
                "data": DepartmentInfo,  # Department data if found
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g. 'Department not found')
            }

        Constraints:
            - department_id must exist in the system.
        """
        department = self.departments.get(department_id)
        if department is None:
            return { "success": False, "error": "Department not found" }
        return { "success": True, "data": department }

    def list_departments(self) -> dict:
        """
        List all hospital departments available in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DepartmentInfo],  # A list of all department info (may be empty if no departments)
            }
        Constraints:
            - No input constraints. Returns all departments present in the system.
        """
        departments_list = list(self.departments.values())
        return {
            "success": True,
            "data": departments_list
        }

    def get_procedure_by_name(self, name: str) -> dict:
        """
        Retrieve details (including procedure_id) for a procedure given its name.

        Args:
            name (str): The name of the procedure to retrieve.

        Returns:
            dict: 
                On success: {"success": True, "data": ProcedureInfo}
                On failure: {"success": False, "error": "Procedure not found"}

        Constraints:
            - Exact name match is required.
        """
        for proc_info in self.procedures.values():
            if proc_info["name"] == name:
                return { "success": True, "data": proc_info }
        return { "success": False, "error": "Procedure not found" }

    def get_procedure_by_id(self, procedure_id: str) -> dict:
        """
        Retrieve procedure information by its unique procedure_id.

        Args:
            procedure_id (str): The unique identifier for the procedure.

        Returns:
            dict: {
                "success": True,
                "data": ProcedureInfo
            }
            or
            {
                "success": False,
                "error": str  # "Procedure not found"
            }

        Constraints:
            - procedure_id must exist in the system.
        """
        procedure = self.procedures.get(procedure_id)
        if procedure is None:
            return { "success": False, "error": "Procedure not found" }
        return { "success": True, "data": procedure }

    def list_procedures_for_department(self, department_id: str) -> dict:
        """
        List all valid procedure types available for a specific department.

        Args:
            department_id (str): The ID of the department for which to list procedures.

        Returns:
            dict: {
                "success": True,
                "data": List[ProcedureInfo],    # List may be empty if no procedures for the department
            }
            or
            {
                "success": False,
                "error": str      # If department does not exist
            }

        Constraints:
            - Department must exist.
            - Only list procedures that have been added/assigned to this department.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist"}

        # The department->procedures mapping is assumed to be available
        department_procedures = getattr(self, "department_procedures", None)
        if department_procedures is None or department_id not in department_procedures:
            # If no procedures assigned, return empty list
            return {"success": True, "data": []}

        procedure_ids = department_procedures[department_id]
        result = [
            self.procedures[proc_id]
            for proc_id in procedure_ids
            if proc_id in self.procedures
        ]
        return {"success": True, "data": result}

    def get_surgery_waitlist_entries_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve all surgery waitlist entries (with metadata) for a given patient.

        Args:
            patient_id (str): Unique identifier for the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[SurgeryWaitlistEntryInfo],  # May be empty if patient has no entries
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g. patient does not exist)
            }

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        waitlist_entries = [
            entry for entry in self.surgery_waitlist_entries.values()
            if entry["patient_id"] == patient_id
        ]
        return { "success": True, "data": waitlist_entries }

    def get_surgery_waitlist_entries_by_department_procedure(
        self,
        department_id: str,
        procedure_id: str
    ) -> dict:
        """
        Retrieve all waitlist entries for a given department and procedure.

        Args:
            department_id (str): Identifier of the department.
            procedure_id (str): Identifier of the procedure.

        Returns:
            dict: {
                "success": True,
                "data": List[SurgeryWaitlistEntryInfo],  # could be empty if none found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. department/procedure not found
            }

        Constraints:
            - department_id must exist in the system.
            - procedure_id must exist in the system.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist"}
        if procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist"}

        entries = [
            entry for entry in self.surgery_waitlist_entries.values()
            if entry["department_id"] == department_id and entry["procedure_id"] == procedure_id
        ]

        return {"success": True, "data": entries}

    def get_surgery_waitlist_entry_by_patient_department_procedure(
        self, patient_id: str, department_id: str, procedure_id: str
    ) -> dict:
        """
        Retrieve a specific waitlist entry for a given patient/procedure/department combination.

        Args:
            patient_id (str): The unique patient identifier.
            department_id (str): The unique department identifier.
            procedure_id (str): The unique procedure identifier.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": SurgeryWaitlistEntryInfo}
                - On failure (entry not found):
                    {"success": False, "error": "No waitlist entry found for the given patient, department, and procedure."}

        Constraints:
            - There should be at most one entry per patient/procedure/department combination.
        """
        # Search for the matching entry
        for entry in self.surgery_waitlist_entries.values():
            if (
                entry["patient_id"] == patient_id
                and entry["department_id"] == department_id
                and entry["procedure_id"] == procedure_id
            ):
                return {"success": True, "data": entry}
        return {
            "success": False,
            "error": "No waitlist entry found for the given patient, department, and procedure."
        }

    def get_surgery_waitlist_entry_by_id(self, entry_id: str) -> dict:
        """
        Retrieve full details of a waitlist entry by its entry_id.

        Args:
            entry_id (str): Unique identifier for the waitlist entry.

        Returns:
            dict: {
                "success": True,
                "data": SurgeryWaitlistEntryInfo
            }
            or
            {
                "success": False,
                "error": str  # "Waitlist entry not found"
            }

        Constraints:
            - entry_id must exist in the system.
            - No modifications; information query only.
        """
        entry = self.surgery_waitlist_entries.get(entry_id)
        if entry is None:
            return { "success": False, "error": "Waitlist entry not found" }
        return { "success": True, "data": entry }

    def get_waitlist_status(self, entry_id: str) -> dict:
        """
        Retrieve the current status of the surgery waitlist entry with the given entry_id.

        Args:
            entry_id (str): The identifier of the surgery waitlist entry.

        Returns:
            dict: {
                "success": True,
                "data": str  # status, one of "pending", "scheduled", "completed", "cancelled"
            }
            or
            {
                "success": False,
                "error": str  # Description if entry not found
            }

        Constraints:
            - The entry_id must exist in the waitlist.
            - Status must be one of the allowed status values.
        """
        entry = self.surgery_waitlist_entries.get(entry_id)
        if entry is None:
            return { "success": False, "error": "Surgery waitlist entry not found" }
    
        status = entry.get("status")
        valid_statuses = {"pending", "scheduled", "completed", "cancelled"}
        if status not in valid_statuses:
            return { "success": False, "error": "Invalid status value stored for entry" }

        return { "success": True, "data": status }

    def add_patient(
        self,
        patient_id: str,
        name: str,
        date_of_birth: str,
        gender: str,
        contact_info: str,
        medical_history: str
    ) -> dict:
        """
        Add a new patient record to the hospital patient database.

        Args:
            patient_id (str): Unique identifier for the patient.
            name (str): Patient's name.
            date_of_birth (str): Patient's date of birth.
            gender (str): Patient's gender.
            contact_info (str): Contact information.
            medical_history (str): Medical history description.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Patient added successfully." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - patient_id must be unique.
            - All attributes must be provided and non-empty.
        """
        if not patient_id or not name or not date_of_birth or not gender or not contact_info or not medical_history:
            return { "success": False, "error": "All patient fields must be provided and non-empty." }
    
        if patient_id in self.patients:
            return { "success": False, "error": "Patient ID already exists." }
    
        new_patient: PatientInfo = {
            "patient_id": patient_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "contact_info": contact_info,
            "medical_history": medical_history
        }
        self.patients[patient_id] = new_patient
        return { "success": True, "message": "Patient added successfully." }


    def add_patient_to_surgery_waitlist(
        self, 
        patient_id: str, 
        department_id: str, 
        procedure_id: str,
        scheduled_date: str = None
    ) -> dict:
        """
        Add a new waitlist entry for a patient for a specific procedure/department.

        Args:
            patient_id (str): Existing patient ID.
            department_id (str): Existing department ID.
            procedure_id (str): Existing procedure ID.
            scheduled_date (str, optional): Scheduled date for surgery (default: None/unset).

        Returns:
            dict:
                success: True if waitlist entry created, False if any error.
                message/error: Describes outcome.

        Constraints:
            - Patient must exist.
            - Department must exist.
            - Procedure must exist.
            - One entry per patient/procedure/department (pending or scheduled) only.
            - Status is set to "pending" on creation.
            - `added_date` assigned as current date (ISO format).
            - Procedure applicability to department may be checked if procedure-department mapping is available.
        """
        # Check existence of patient, department, procedure
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist"}
        if procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist"}

        # Check if procedure is valid for department
        # If a mapping like self.department_procedures exists: uncomment
        if hasattr(self, "department_procedures"):
            if procedure_id not in self.department_procedures.get(department_id, []):
                return {"success": False, "error": "Procedure not available for this department"}

        # Check uniqueness constraint: One entry per procedure per department per patient (pending or scheduled)
        for entry in self.surgery_waitlist_entries.values():
            if (
                entry["patient_id"] == patient_id and
                entry["department_id"] == department_id and
                entry["procedure_id"] == procedure_id and
                entry["status"] in ["pending", "scheduled"]
            ):
                return {"success": False, "error": "A waitlist entry for this patient/procedure/department already exists"}

        # Create entry
        entry_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        new_entry = {
            "entry_id": entry_id,
            "patient_id": patient_id,
            "department_id": department_id,
            "procedure_id": procedure_id,
            "status": "pending",
            "added_date": now,
            "scheduled_date": scheduled_date if scheduled_date is not None else ""
        }
        self.surgery_waitlist_entries[entry_id] = new_entry

        return {
            "success": True,
            "message": (
                f"Waitlist entry created for patient {patient_id} in department {department_id} "
                f"for procedure {procedure_id}."
            )
        }

    def update_surgery_waitlist_entry_status(self, entry_id: str, new_status: str) -> dict:
        """
        Modify the status of a surgery waitlist entry.

        Args:
            entry_id (str): The unique identifier for the SurgeryWaitlistEntry.
            new_status (str): The updated status value ("pending", "scheduled", "completed", "cancelled").

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Surgery waitlist entry status updated to <new_status>." }
                On failure:
                    { "success": False, "error": "reason" }

        Constraints:
            - entry_id must exist in the system.
            - new_status must be one of "pending", "scheduled", "completed", "cancelled".
        """
        allowed_statuses = {"pending", "scheduled", "completed", "cancelled"}

        if entry_id not in self.surgery_waitlist_entries:
            return { "success": False, "error": "Surgery waitlist entry does not exist." }

        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed: {', '.join(allowed_statuses)}." }

        self.surgery_waitlist_entries[entry_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Surgery waitlist entry status updated to {new_status}."
        }

    def remove_surgery_waitlist_entry(self, entry_id: str) -> dict:
        """
        Delete a surgery waitlist entry identified by entry_id.

        Args:
            entry_id (str): Unique identifier for the waitlist entry to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Waitlist entry removed successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., entry not found).
            }

        Constraints:
            - The entry to be removed must exist in the system.
            - No other integrity checks required as per environment rules.
        """
        if entry_id not in self.surgery_waitlist_entries:
            return { "success": False, "error": "Waitlist entry not found." }

        del self.surgery_waitlist_entries[entry_id]
        return { "success": True, "message": "Waitlist entry removed successfully." }

    def update_surgery_waitlist_entry_schedule(self, entry_id: str, scheduled_date: str) -> dict:
        """
        Set or reschedule the scheduled_date for a specified surgery waitlist entry.

        Args:
            entry_id (str): The unique identifier of the SurgeryWaitlistEntry to update.
            scheduled_date (str): The new scheduled date to set (format assumed to be string, e.g. "YYYY-MM-DD").

        Returns:
            dict: {
                "success": True,
                "message": "Scheduled date updated for waitlist entry <entry_id>."
            }
            or
            {
                "success": False,
                "error": "Waitlist entry with entry_id <entry_id> does not exist."
            }

        Constraints:
            - entry_id must exist in the system.
            - scheduled_date is accepted as a string (no format enforcement per environment spec).
        """
        entry = self.surgery_waitlist_entries.get(entry_id)
        if not entry:
            return { "success": False, "error": f"Waitlist entry with entry_id {entry_id} does not exist." }

        entry["scheduled_date"] = scheduled_date
        # Optionally, could update other timestamps if system tracks last modified, not specified here.

        return { "success": True, "message": f"Scheduled date updated for waitlist entry {entry_id}." }

    def edit_patient_info(
        self, 
        patient_id: str, 
        name: str = None, 
        date_of_birth: str = None, 
        gender: str = None, 
        contact_info: str = None, 
        medical_history: str = None
    ) -> dict:
        """
        Modify demographic or medical info for an existing patient record.
    
        Args:
            patient_id (str): Unique patient identifier.
            name (str, optional): Updated patient name.
            date_of_birth (str, optional): Updated date of birth.
            gender (str, optional): Updated gender.
            contact_info (str, optional): Updated contact information.
            medical_history (str, optional): Updated medical history.
        
        Returns:
            dict: {
                "success": True,
                "message": "Patient info updated"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., patient does not exist
            }
        
        Constraints:
            - Patient must exist in the system before editing info.
            - Only provided fields are updated. Unchanged fields left intact.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient does not exist"}

        # Update provided fields only
        if name is not None:
            patient["name"] = name
        if date_of_birth is not None:
            patient["date_of_birth"] = date_of_birth
        if gender is not None:
            patient["gender"] = gender
        if contact_info is not None:
            patient["contact_info"] = contact_info
        if medical_history is not None:
            patient["medical_history"] = medical_history

        return {"success": True, "message": "Patient info updated"}

    def add_procedure_to_department(self, department_id: str, procedure_id: str) -> dict:
        """
        Associate an existing procedure with a department.

        Args:
            department_id (str): The department to associate the procedure with.
            procedure_id (str): The procedure to be associated.

        Returns:
            dict: {
                "success": True,
                "message": "Procedure <procedure_id> successfully associated with department <department_id>."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - The department must exist.
            - The procedure must exist.
            - Procedure must not be associated with the department already.
            - Procedure must be available and valid for the department.
        """
        # Check department existence
        if department_id not in self.departments:
            return { "success": False, "error": f"Department {department_id} does not exist." }

        # Check procedure existence
        if procedure_id not in self.procedures:
            return { "success": False, "error": f"Procedure {procedure_id} does not exist." }

        # Create mapping if it doesn't exist
        if not hasattr(self, "department_procedures"):
            self.department_procedures: Dict[str, List[str]] = {}

        # Ensure department mapping exists
        if department_id not in self.department_procedures:
            self.department_procedures[department_id] = []

        # Check if procedure is already associated
        if procedure_id in self.department_procedures[department_id]:
            return { "success": False, "error": "Procedure is already associated with the department." }

        # Associate procedure
        self.department_procedures[department_id].append(procedure_id)

        return {
            "success": True,
            "message": f"Procedure {procedure_id} successfully associated with department {department_id}."
        }

    def remove_patient(self, patient_id: str) -> dict:
        """
        Delete a patient record from the system, along with any associated surgery waitlist entries.
    
        Args:
            patient_id (str): The unique identifier of the patient to be removed.
    
        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Patient deleted successfully" }
                On failure:
                    { "success": False, "error": "Patient does not exist" }
    
        Constraints:
            - Patient must exist.
            - Removes all SurgeryWaitlistEntries for this patient to maintain integrity.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }
    
        # Remove the patient
        del self.patients[patient_id]
    
        # Collect entry_ids to remove from waitlist
        waitlist_entries_to_remove = [
            entry_id for entry_id, entry in self.surgery_waitlist_entries.items()
            if entry["patient_id"] == patient_id
        ]
        for entry_id in waitlist_entries_to_remove:
            del self.surgery_waitlist_entries[entry_id]
    
        return { "success": True, "message": "Patient deleted successfully" }

    def add_department(self, department_id: str, name: str, location: str) -> dict:
        """
        Add a new department to the hospital system.

        Args:
            department_id (str): The unique identifier for the department.
            name (str): Name of the department.
            location (str): Physical location of the department.

        Returns:
            dict: {
                "success": True,
                "message": "Department added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of error.
            }

        Constraints:
            - department_id must be unique.
            - All parameters must be non-empty strings.
        """
        # Validate inputs
        if not department_id or not isinstance(department_id, str):
            return { "success": False, "error": "Invalid or empty department_id." }

        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or empty department name." }

        if not location or not isinstance(location, str):
            return { "success": False, "error": "Invalid or empty location." }

        if department_id in self.departments:
            return { "success": False, "error": "Department ID already exists." }

        self.departments[department_id] = {
            "department_id": department_id,
            "name": name,
            "location": location
        }

        return { "success": True, "message": "Department added successfully." }

    def add_procedure(self, procedure_id: str, name: str, description: str) -> dict:
        """
        Add a new procedure type to the hospital's procedure catalog.

        Args:
            procedure_id (str): The unique identifier for the new procedure.
            name (str): The human-readable name of the procedure.
            description (str): Details describing the procedure.

        Returns:
            dict: {
                "success": True,
                "message": "Procedure added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - procedure_id must be unique (not already present).
            - procedure name should be unique for clarity (checked).
        """
        if procedure_id in self.procedures:
            return { "success": False, "error": "Procedure ID already exists." }

        for proc in self.procedures.values():
            if proc['name'].lower() == name.lower():
                return { "success": False, "error": "Procedure name already exists." }

        self.procedures[procedure_id] = {
            "procedure_id": procedure_id,
            "name": name,
            "description": description
        }

        return { "success": True, "message": "Procedure added successfully." }