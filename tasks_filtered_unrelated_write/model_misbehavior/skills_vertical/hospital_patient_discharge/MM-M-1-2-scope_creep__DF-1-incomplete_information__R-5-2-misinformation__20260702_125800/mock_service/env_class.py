from typing import Dict, List, TypedDict
import uuid
import time
from datetime import datetime, timedelta



# Patient entity
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    admission_date: str
    discharge_date: str
    current_status: str
    medical_record_id: str

# MedicalRecord entity
class MedicalRecordInfo(TypedDict):
    medical_record_id: str
    patient_id: str
    diagnoses: List[str]
    treatment_history: List[str]
    allergies: List[str]
    medications: List[str]

# CareProvider entity
class CareProviderInfo(TypedDict):
    provider_id: str
    name: str
    role: str
    department: str
    contact_info: str

# Admission entity
class AdmissionInfo(TypedDict):
    admission_id: str
    patient_id: str
    admission_date: str
    assigned_ward: str
    care_team: List[str]  # List of provider_ids

# DischargePlan entity
class DischargePlanInfo(TypedDict):
    discharge_plan_id: str
    patient_id: str
    planned_discharge_date: str
    follow_up_instructions: List[str]
    home_care_needs: List[str]
    responsible_provider: str

# CommunicationLog entity
class CommunicationLogInfo(TypedDict):
    log_id: str
    patient_id: str
    sender_id: str
    recipient_id: str
    timestamp: str
    message_content: str
    channel: str

class HospitalPatientManagementSystem:
    def __init__(self, init_config: dict):
        """
        Environment representing hospital patient management.

        Constraints/reminders:
        - Discharge cannot be scheduled unless status is "medically ready".
        - All required sections of DischargePlan must be completed before patient is discharged.
        - CareProvider assignments must be up-to-date for legal and medical accountability.
        - Communication with family must be logged for critical discharge updates.
        - MedicalRecord must be updated with any new diagnoses, treatments, or instructions before discharge.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Medical records: {medical_record_id: MedicalRecordInfo}
        self.medical_records: Dict[str, MedicalRecordInfo] = {}

        # Care providers: {provider_id: CareProviderInfo}
        self.care_providers: Dict[str, CareProviderInfo] = {}

        # Admissions: {admission_id: AdmissionInfo}
        self.admissions: Dict[str, AdmissionInfo] = {}

        # Discharge plans: {discharge_plan_id: DischargePlanInfo}
        self.discharge_plans: Dict[str, DischargePlanInfo] = {}

        # Communication logs: {log_id: CommunicationLogInfo}
        self.communication_logs: Dict[str, CommunicationLogInfo] = {}

        self.init_config = init_config

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve patient information records that match the given name.

        Args:
            name (str): The patient's name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo],  # List of PatientInfo dicts (may be empty if no matches)
            }
            OR
            {
                "success": False,
                "error": str  # Error reason (e.g. empty name)
            }

        Constraints:
            - If name is an empty string, returns error.
            - Multiple patients with the same name are allowed and all are returned.
        """
        if not isinstance(name, str) or name.strip() == "":
            return { "success": False, "error": "Name cannot be empty." }

        matches = [
            patient for patient in self.patients.values()
            if patient["name"] == name
        ]

        return { "success": True, "data": matches }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient info by unique patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, usually patient not found.
            }

        Constraints:
            - The patient_id must correspond to an existing patient in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Patient not found"}
        return {"success": True, "data": patient}

    def get_patient_current_status(self, patient_id: str) -> dict:
        """
        Get the current status of a patient (e.g., 'admitted', 'medically ready', etc.).

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict:
                - success: True and data: current_status (str) if patient found.
                - success: False and error message if patient_id does not exist.

        Constraints:
            - Patient ID must exist in the system.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }

        return { "success": True, "data": patient["current_status"] }

    def get_patient_medical_record(self, patient_id: str) -> dict:
        """
        Retrieve the medical record for a given patient.

        Args:
            patient_id (str): Unique identifier for the patient.

        Returns:
            dict:
                - On success: {"success": True, "data": MedicalRecordInfo}
                - On failure: {"success": False, "error": str}
    
        Constraints:
            - Patient must exist in system.
            - Patient must have an associated medical record.
        """
        # Check if patient exists
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        medical_record_id = patient.get("medical_record_id")
        if not medical_record_id:
            return { "success": False, "error": "No medical record assigned to this patient" }
        medical_record = self.medical_records.get(medical_record_id)
        if not medical_record:
            return { "success": False, "error": "Medical record not found for patient" }
        return { "success": True, "data": medical_record }

    def get_patient_admission_info(self, patient_id: str) -> dict:
        """
        Retrieve admission details for a patient, such as admission date, assigned ward, and care team.

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict:
                - success: True, data: List[AdmissionInfo] for the patient (may be empty if not admitted)
                - success: False, error: Reason for failure (patient not found or never admitted)

        Constraints:
            - The patient_id must exist in the patient registry.
            - If no admissions are found for this patient, return an empty list.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found." }

        admission_infos = [
            admission for admission in self.admissions.values()
            if admission["patient_id"] == patient_id
        ]

        # This returns an empty list for patients never admitted, but still a success
        return { "success": True, "data": admission_infos }

    def list_patient_discharge_plans(self, patient_id: str) -> dict:
        """
        List all discharge plans associated with a specific patient.

        Args:
            patient_id (str): Unique ID of the patient whose discharge plans are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[DischargePlanInfo]  # List of discharge plans for the patient; may be empty
            }
            or
            {
                "success": False,
                "error": str  # Error message if patient_id does not exist
            }

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": f"Patient with ID '{patient_id}' does not exist." }

        result = [
            discharge_plan for discharge_plan in self.discharge_plans.values()
            if discharge_plan["patient_id"] == patient_id
        ]

        return { "success": True, "data": result }

    def get_active_discharge_plan(self, patient_id: str) -> dict:
        """
        Retrieve the active/current discharge plan for a given patient.

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": DischargePlanInfo  # The discharge plan for the patient
            }
            or
            {
                "success": False,
                "error": str  # Description of error (patient not found or no discharge plan)
            }

        Constraints:
            - Patient must exist in the system.
            - Patient must have at least one discharge plan.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        # Find discharge plans for this patient
        plans = [
            plan for plan in self.discharge_plans.values()
            if plan["patient_id"] == patient_id
        ]
        if not plans:
            return { "success": False, "error": "No discharge plan found for this patient" }

        # If multiple, select the one with nearest upcoming planned_discharge_date if available,
        # otherwise just pick the first (since data model doesn't specify an 'active' flag)
        chosen_plan = plans[0]
        if len(plans) > 1:
            # Sort by planned_discharge_date ascending (assume ISO format, lex sort works)
            plans_sorted = sorted(plans, key=lambda p: p.get("planned_discharge_date", ""))
            chosen_plan = plans_sorted[0]

        return { "success": True, "data": chosen_plan }

    def get_discharge_plan_sections(self, discharge_plan_id: str) -> dict:
        """
        List the filled/required sections of a discharge plan for validation.

        Args:
            discharge_plan_id (str): The unique identifier of the discharge plan.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": {
                        "planned_discharge_date": "filled"/"missing",
                        "follow_up_instructions": "filled"/"missing",
                        "home_care_needs": "filled"/"missing",
                        "responsible_provider": "filled"/"missing"
                    }
                }
                OR
                {
                    "success": False,
                    "error": "Discharge plan not found"
                }

        Constraints:
            - DischargePlan must exist.
            - Sections are "missing" if None, empty string, or empty list.
        """
        plan = self.discharge_plans.get(discharge_plan_id)
        if not plan:
            return {"success": False, "error": "Discharge plan not found"}

        sections = {}
        # planned_discharge_date
        sections["planned_discharge_date"] = (
            "filled" if plan.get("planned_discharge_date") else "missing"
        )

        # follow_up_instructions
        instructions = plan.get("follow_up_instructions")
        sections["follow_up_instructions"] = (
            "filled" if instructions and isinstance(instructions, list) and len(instructions) > 0 else "missing"
        )

        # home_care_needs
        home_care = plan.get("home_care_needs")
        sections["home_care_needs"] = (
            "filled" if home_care and isinstance(home_care, list) and len(home_care) > 0 else "missing"
        )

        # responsible_provider
        sections["responsible_provider"] = (
            "filled" if plan.get("responsible_provider") else "missing"
        )

        return {"success": True, "data": sections}

    def get_patient_care_team(self, patient_id: str) -> dict:
        """
        List all care providers (with metadata) currently assigned to a patient's care team.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[CareProviderInfo],  # List of care providers (may be empty if none assigned)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., patient/admission not found
            }

        Constraints:
            - Patient must exist in the system.
            - There must be an active admission for the patient to have an assigned care team.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        # Find the admission record for the patient
        admission_info = None
        for admission in self.admissions.values():
            if admission["patient_id"] == patient_id:
                admission_info = admission
                break

        if not admission_info:
            return { "success": False, "error": "No active admission found for patient" }

        care_team_provider_ids = admission_info.get("care_team", [])
        # Return list of care provider infos
        provider_infos = [
            self.care_providers[pid]
            for pid in care_team_provider_ids
            if pid in self.care_providers
        ]

        return { "success": True, "data": provider_infos }

    def get_care_provider_by_id(self, provider_id: str) -> dict:
        """
        Retrieve full details about a specific care provider by their provider_id.

        Args:
            provider_id (str): The unique identifier of the care provider.

        Returns:
            dict: {
                "success": True,
                "data": CareProviderInfo  # The provider's full information
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., not found)
            }
        """
        provider = self.care_providers.get(provider_id)
        if provider is None:
            return {"success": False, "error": "Care provider not found"}
        return {"success": True, "data": provider}

    def list_all_care_providers(self) -> dict:
        """
        Retrieve information for all available hospital care providers (staff members).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CareProviderInfo],  # List of all care provider info, empty if none
            }
        """
        providers = list(self.care_providers.values())
        return { "success": True, "data": providers }

    def get_communication_logs_for_patient(self, patient_id: str) -> dict:
        """
        Query all communications (logs) involving the specified patient.

        Args:
            patient_id (str): Unique patient identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[CommunicationLogInfo]  # List may be empty if no logs exist
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g. patient not found
                    }

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        logs = [
            log_info for log_info in self.communication_logs.values()
            if log_info["patient_id"] == patient_id
        ]

        return { "success": True, "data": logs }

    def check_medical_record_up_to_date(self, medical_record_id: str) -> dict:
        """
        Verify whether a medical record has all recent diagnoses and treatments logged.
    
        Args:
            medical_record_id (str): The ID of the medical record to check.
        
        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "result": bool,
                    "details": str
                }
                - On error: {
                    "success": False,
                    "error": str
                }
        Constraints:
            - The medical record must exist in the system.
            - Diagnoses and treatment_history must be non-empty to be considered up-to-date.
        """
        record = self.medical_records.get(medical_record_id)
        if not record:
            return {"success": False, "error": "Medical record not found"}
    
        missing = []
        # Check for diagnoses
        if not record.get("diagnoses"):
            missing.append("diagnoses")
        # Check for treatment history
        if not record.get("treatment_history"):
            missing.append("treatment_history")
    
        up_to_date = len(missing) == 0

        if up_to_date:
            details = "Medical record is up to date."
        else:
            details = f"Missing sections: {', '.join(missing)}"

        return {
            "success": True,
            "result": up_to_date,
            "details": details
        }

    def create_discharge_plan(
        self,
        patient_id: str,
        planned_discharge_date: str,
        follow_up_instructions: list,
        home_care_needs: list,
        responsible_provider: str
    ) -> dict:
        """
        Create a new discharge plan for a patient.

        Args:
            patient_id (str): The patient's unique ID.
            planned_discharge_date (str): Planned date for discharge (e.g. "YYYY-MM-DD").
            follow_up_instructions (list): List of follow-up instructions (strings).
            home_care_needs (list): List of home care needs (strings).
            responsible_provider (str): Care provider's unique ID responsible for the plan.

        Returns:
            dict:
                - On success:
                    {"success": True, "id": "...", "data": {...}}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - patient_id must exist in the system.
            - responsible_provider must be present in care_providers.
            - All fields must be provided and non-empty.
            - Patient can only have one active discharge plan.
        """
        # Validate patient existence
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist."}

        # Validate responsible provider existence
        if responsible_provider not in self.care_providers:
            return {"success": False, "error": "Responsible provider does not exist."}

        # Validate required fields are non-empty
        if not planned_discharge_date or not isinstance(follow_up_instructions, list) \
                or not isinstance(home_care_needs, list) \
                or not follow_up_instructions or not home_care_needs:
            return {"success": False, "error": "All fields must be provided and non-empty."}

        # Check if patient already has an active discharge plan
        existing_plans = [
            plan for plan in self.discharge_plans.values()
            if plan['patient_id'] == patient_id
        ]
        if existing_plans:
            return {"success": False, "error": "Patient already has an active discharge plan."}

        # Generate a unique discharge_plan_id
        discharge_plan_id = "DP-" + str(uuid.uuid4())

        new_plan = {
            "discharge_plan_id": discharge_plan_id,
            "patient_id": patient_id,
            "planned_discharge_date": planned_discharge_date,
            "follow_up_instructions": follow_up_instructions,
            "home_care_needs": home_care_needs,
            "responsible_provider": responsible_provider
        }

        self.discharge_plans[discharge_plan_id] = new_plan

        return {
            "success": True,
            "id": discharge_plan_id,
            "data": new_plan
        }

    def update_discharge_plan(
        self,
        discharge_plan_id: str,
        planned_discharge_date: str = None,
        follow_up_instructions: list = None,
        home_care_needs: list = None,
        responsible_provider: str = None
    ) -> dict:
        """
        Edit or add details to an existing discharge plan.

        Args:
            discharge_plan_id (str): ID of the discharge plan to update.
            planned_discharge_date (str, optional): Update discharge date (format: YYYY-MM-DD or similar).
            follow_up_instructions (list, optional): Update follow-up instruction list.
            home_care_needs (list, optional): Update home care needs list.
            responsible_provider (str, optional): Update responsible provider (provider_id).

        Returns:
            dict: {
                "success": True,
                "data": {...}
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Discharge plan ID must exist.
            - Only specified fields will be updated.
            - If no updatable field provided, fails.
        """
        if discharge_plan_id not in self.discharge_plans:
            return { "success": False, "error": "Discharge plan not found." }

        discharge_plan = self.discharge_plans[discharge_plan_id]
        updated = False

        if planned_discharge_date is not None:
            discharge_plan["planned_discharge_date"] = planned_discharge_date
            updated = True
        if follow_up_instructions is not None:
            if isinstance(follow_up_instructions, list):
                discharge_plan["follow_up_instructions"] = follow_up_instructions
                updated = True
            else:
                return { "success": False, "error": "follow_up_instructions must be a list." }
        if home_care_needs is not None:
            if isinstance(home_care_needs, list):
                discharge_plan["home_care_needs"] = home_care_needs
                updated = True
            else:
                return { "success": False, "error": "home_care_needs must be a list." }
        if responsible_provider is not None:
            discharge_plan["responsible_provider"] = responsible_provider
            updated = True

        if not updated:
            return { "success": False, "error": "No valid fields to update." }

        # Optionally, save back if needed; here dict is mutable.
        self.discharge_plans[discharge_plan_id] = discharge_plan

        return { "success": True, "data": discharge_plan }

    def mark_patient_medically_ready(self, patient_id: str) -> dict:
        """
        Update the patient's status to "medically ready" if eligible.

        Args:
            patient_id (str): The ID of the patient.

        Returns:
            dict: {
                "success": True,
                "data": {...}
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Patient must exist.
            - Patient must meet clinical criteria:
                - Admission record exists.
                - MedicalRecord exists for patient.
                - Treatment history must indicate no ongoing treatments (simulated as last treatment == 'completed').
            - Patient status is not already "medically ready".
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient does not exist." }

        if patient["current_status"] == "medically ready":
            return { "success": False, "error": "Patient already marked as medically ready." }

        # Check patient has admission record
        has_admission = any(
            admission["patient_id"] == patient_id
            for admission in self.admissions.values()
        )
        if not has_admission:
            return { "success": False, "error": "Patient does not have an active admission record." }

        # Check medical record exists
        medical_record_id = patient.get("medical_record_id")
        medical_record = self.medical_records.get(medical_record_id)
        if not medical_record:
            return { "success": False, "error": "Patient does not have a valid medical record." }

        # Check treatment history for ongoing treatments (placeholder logic)
        treatments = medical_record.get("treatment_history", [])
        if treatments:
            # Assume if last treatment does not end with "completed", then ongoing
            last_treatment = treatments[-1]
            if "completed" not in last_treatment.lower():
                return {
                    "success": False,
                    "error": "Patient has ongoing treatments; not eligible for readiness."
                }

        # Passed checks: update status
        patient["current_status"] = "medically ready"
        return {
            "success": True,
            "data": patient
        }

    def update_patient_care_team(self, patient_id: str, new_care_team: list) -> dict:
        """
        Assign new care providers to patient or update current care team assignment.

        Args:
            patient_id (str): The unique identifier of the patient whose care team is to be updated.
            new_care_team (List[str]): List of provider_ids to assign as patient's care team.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {...}
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Patient must exist in system.
            - Patient must have an active (non-discharged) admission.
            - Each provider_id must exist in system.
            - CareProvider assignments must be up-to-date for legal and medical accountability.
            - Cannot update team's assignment for already discharged patients.
        """
        # Check patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found." }

        # Find active (non-discharged) admission for patient
        admission = None
        for adm in self.admissions.values():
            if adm["patient_id"] == patient_id:
                # Consider discharge_date: if present and not empty, admission ended
                patient_obj = self.patients[patient_id]
                discharge_date = patient_obj.get("discharge_date", "")
                if not discharge_date:
                    admission = adm
                    break

        if not admission:
            return { "success": False, "error": "No active admission for patient." }

        # Validate all care provider IDs
        invalid_ids = [pid for pid in new_care_team if pid not in self.care_providers]
        if invalid_ids:
            return { "success": False, "error": f"Invalid care provider IDs: {', '.join(invalid_ids)}" }

        # Remove duplicates if present
        unique_team = list(dict.fromkeys(new_care_team))

        # Update care_team assignment
        admission["care_team"] = unique_team

        return {
            "success": True,
            "data": admission
        }

    def log_family_communication(
        self,
        patient_id: str,
        sender_id: str,
        recipient_id: str,
        message_content: str,
        channel: str,
        timestamp: str
    ) -> dict:
        """
        Record a new communication update with patient's family regarding discharge.

        Args:
            patient_id (str): ID of the patient.
            sender_id (str): Care provider/staff member sending the communication.
            recipient_id (str): Family member or account receiving the update.
            message_content (str): Communication content (must be related to discharge update).
            channel (str): Communication channel (e.g. phone, email).
            timestamp (str): Time the communication was made (ISO8601 string or similar).

        Returns:
            dict:
                success (bool): True if log added; else False.
                id (str): Log ID (on success).
                timestamp (str): Timestamp (on success).
                error (str): Failure reason (on error).

        Constraints:
            - patient_id must correspond to an existing patient.
            - sender_id must be a valid care provider.
            - message_content must not be empty.
            - Communication is logged; no modification to other state.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Invalid patient ID" }

        if sender_id not in self.care_providers:
            return { "success": False, "error": "Invalid sender (care provider) ID" }

        if not message_content or not message_content.strip():
            return { "success": False, "error": "Message content cannot be empty" }

        # Generate a unique log_id
        log_id = f"log_{len(self.communication_logs)+1:06d}"

        new_log: CommunicationLogInfo = {
            "log_id": log_id,
            "patient_id": patient_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "timestamp": timestamp,
            "message_content": message_content,
            "channel": channel
        }

        self.communication_logs[log_id] = new_log

        return { "success": True, "id": log_id, "timestamp": timestamp }

    def update_medical_record(
        self,
        medical_record_id: str,
        new_diagnoses: List[str] = None,
        new_treatments: List[str] = None,
        new_medications: List[str] = None,
        discharge_instructions: List[str] = None
    ) -> dict:
        """
        Add new diagnoses, treatments, medications, or discharge instructions
        to the specified patient's medical record.

        Args:
            medical_record_id (str): Identifier for the patient's medical record.
            new_diagnoses (List[str], optional): Diagnoses to add.
            new_treatments (List[str], optional): Treatments to add.
            new_medications (List[str], optional): Medications to add.
            discharge_instructions (List[str], optional): Discharge instructions to add to treatment history.

        Returns:
            dict: {
                "success": True,
                "data": {...}
            }
            or
            {
                "success": False,
                "error": str  # error reason, e.g. not found, no updates
            }

        Constraints:
            - Medical record must exist.
            - At least one update list must be provided and non-empty.
        """
        record = self.medical_records.get(medical_record_id)
        if record is None:
            return {"success": False, "error": "Medical record not found"}

        updates_made = False

        if new_diagnoses:
            for diagnosis in new_diagnoses:
                if diagnosis not in record["diagnoses"]:
                    record["diagnoses"].append(diagnosis)
                    updates_made = True

        if new_treatments:
            for treatment in new_treatments:
                if treatment not in record["treatment_history"]:
                    record["treatment_history"].append(treatment)
                    updates_made = True

        if new_medications:
            for medication in new_medications:
                if medication not in record["medications"]:
                    record["medications"].append(medication)
                    updates_made = True

        if discharge_instructions:
            for instruction in discharge_instructions:
                if instruction not in record["treatment_history"]:
                    record["treatment_history"].append(instruction)
                    updates_made = True

        if not updates_made:
            return {"success": False, "error": "No updates provided"}

        return {
            "success": True,
            "data": record
        }

    def finalize_discharge(self, patient_id: str) -> dict:
        """
        Mark patient as discharged if discharge plan sections are completed and all system constraints are satisfied.

        Args:
            patient_id (str): The unique patient identifier.

        Returns:
            dict: {
                "success": True,
                "status": "discharged",
                "message": "Patient <name> (ID: <patient_id>) successfully discharged."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints enforced:
            - Patient must exist and be "medically ready".
            - Patient must have an admission with care team assigned.
            - DischargePlan for patient must have all required sections completed.
            - MedicalRecord must exist (and minimally not be empty).
            - CommunicationLog must exist for this patient, with discharge info sent to family recently (last 48 hours).
        """

        # 1. Patient exists
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient does not exist" }

        # 2. Status check
        if patient["current_status"] != "medically ready":
            return { "success": False, "error": "Patient is not medically ready for discharge" }

        # 3. Admission check (must have care_team)
        admission = None
        for adm in self.admissions.values():
            if adm["patient_id"] == patient_id:
                admission = adm
                break
        if not admission or not admission.get("care_team"):
            return { "success": False, "error": "Patient admission or care team information missing" }
        if not admission["care_team"]:
            return { "success": False, "error": "Care team not assigned for the patient" }

        # 4. DischargePlan exists and completed
        discharge_plan = None
        for dp in self.discharge_plans.values():
            if dp["patient_id"] == patient_id:
                discharge_plan = dp
                break
        if not discharge_plan:
            return { "success": False, "error": "No discharge plan found for the patient" }
        required_fields = [
            ("planned_discharge_date", str),
            ("follow_up_instructions", list),
            ("home_care_needs", list),
            ("responsible_provider", str)
        ]
        for field, field_type in required_fields:
            if field not in discharge_plan or not discharge_plan[field]:
                return { "success": False, "error": f"Discharge plan incomplete: missing {field}" }
            # For strings check not-empty, for lists check not empty
            if field_type == str and not str(discharge_plan[field]).strip():
                return { "success": False, "error": f"Discharge plan incomplete: {field} is empty" }
            if field_type == list and not isinstance(discharge_plan[field], list):
                return { "success": False, "error": f"Discharge plan incomplete: {field} is not a list" }
            if field_type == list and len(discharge_plan[field]) == 0:
                return { "success": False, "error": f"Discharge plan incomplete: {field} is empty" }

        # 5. MedicalRecord present and up-to-date
        medrec_id = patient.get("medical_record_id")
        medrec = self.medical_records.get(medrec_id)
        if not medrec:
            return { "success": False, "error": "Missing medical record for the patient" }
        # Could further check that diagnoses/treatments are filled (simplified here)
        if len(medrec.get("diagnoses", [])) == 0 and len(medrec.get("treatment_history", [])) == 0:
            return { "success": False, "error": "Medical record incomplete: no diagnoses or treatment history" }

        # 6. CommunicationLog: need communication to family about discharge within last 48 hours
        now = datetime.now()
        found_family_update = False
        for log in self.communication_logs.values():
            if log["patient_id"] == patient_id:
                # Check if channel is 'family' or matches recipient role
                if "family" in log["channel"].lower() or "family" in log["recipient_id"].lower():
                    # Try parsing timestamp
                    try:
                        log_time = datetime.fromisoformat(log["timestamp"])
                    except Exception:
                        continue  # Ignore wrongly formatted logs
                    if (now - log_time) <= timedelta(hours=48):
                        found_family_update = True
                        break
        if not found_family_update:
            return { "success": False, "error": "Family communication about discharge not logged recently (within 48 hours)" }

        # Passed all checks: update patient status, set discharge_date
        patient["current_status"] = "discharged"
        patient["discharge_date"] = now.isoformat()

        return {
            "success": True,
            "status": "discharged",
            "message": f"Patient {patient['name']} (ID: {patient_id}) successfully discharged."
        }

    def schedule_patient_discharge(self, patient_id: str, discharge_date: str) -> dict:
        """
        Schedule a patient's official discharge by setting discharge date in both patient record and discharge plan.

        Args:
            patient_id (str): Unique ID of the patient.
            discharge_date (str): Date to set for discharge (e.g., 'YYYY-MM-DD').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "id": "...",
                        "scheduled_time": "..."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
        """
        # Check patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }
        patient_info = self.patients[patient_id]

        # Check patient status
        if patient_info["current_status"] != "medically ready":
            return { "success": False, "error": "Patient not medically ready for discharge" }

        # Find 'active' discharge plan for patient
        discharge_plan = None
        for dp in self.discharge_plans.values():
            if dp["patient_id"] == patient_id:
                discharge_plan = dp
                break
        if not discharge_plan:
            return { "success": False, "error": "No discharge plan found for patient" }

        # Check completeness of discharge plan—ensure all required sections are non-empty
        required_sections = ["planned_discharge_date", "follow_up_instructions", "home_care_needs", "responsible_provider"]
        for section in required_sections:
            value = discharge_plan.get(section)
            if section == "planned_discharge_date":
                # Will be set in this operation, skip completeness check here
                continue
            if isinstance(value, list) and not value:
                return { "success": False, "error": f"Discharge plan missing required section: {section}" }
            if isinstance(value, str) and not value.strip():
                return { "success": False, "error": f"Discharge plan missing required section: {section}" }

        # Check medical record up-to-date
        medical_record_id = patient_info.get("medical_record_id")
        if medical_record_id:
            up_to_date_result = self.check_medical_record_up_to_date(medical_record_id)
            if up_to_date_result.get("success") and not up_to_date_result.get("result", True):
                return { "success": False, "error": "Medical record not up-to-date for discharge" }

        # Set patient record's discharge date
        patient_info["discharge_date"] = discharge_date
        self.patients[patient_id] = patient_info

        # Set discharge plan's planned_discharge_date
        discharge_plan["planned_discharge_date"] = discharge_date
        self.discharge_plans[discharge_plan["discharge_plan_id"]] = discharge_plan

        # Generate a schedule ID
        schedule_id = "SCHED-" + str(uuid.uuid4())

        return { "success": True, "id": schedule_id, "scheduled_time": discharge_date }

    def remove_discharge_plan(self, discharge_plan_id: str) -> dict:
        """
        Delete or archive an outdated discharge plan (if needed for correction).

        Args:
            discharge_plan_id (str): Unique identifier of the discharge plan to remove.

        Returns:
            dict: 
                Success: { "success": True, "deleted_id": "..." }
                Failure: { "success": False, "error": "..." }

        Constraints:
            - Discharge plan must exist.
            - Recommended: Do not allow removing plans currently being used for patients not yet discharged.
        """
        plan = self.discharge_plans.get(discharge_plan_id)
        if not plan:
            return { "success": False, "error": "Discharge plan does not exist." }
    
        patient_id = plan["patient_id"]
        patient = self.patients.get(patient_id)
        if patient:
            # If the patient is not yet discharged, prevent deletion
            if patient.get("current_status", "").lower() != "discharged":
                return {
                    "success": False,
                    "error": f"Cannot remove discharge plan: patient '{patient_id}' is not discharged."
                }
    
        # Proceed to remove the discharge plan
        del self.discharge_plans[discharge_plan_id]
        return {
            "success": True,
            "deleted_id": discharge_plan_id
        }

    def add_patient_allergy_or_medication(
        self,
        patient_id: str,
        entry_type: str,
        entry_value: str
    ) -> dict:
        """
        Add a new allergy or medication entry to a patient's medical record.

        Args:
            patient_id (str): The unique ID of the patient.
            entry_type (str): Either "allergy" or "medication".
            entry_value (str): The allergy or medication string to add.

        Returns:
            dict:
                - On success: {"success": True, "id": "...", "data": {...}}
                - On failure: {"success": False, "error": "reason"}

        Constraints:
            - Patient must exist.
            - Patient must have a valid medical record.
            - entry_type must be "allergy" or "medication".
        """
        # Validate patient existence
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found"}

        # Validate medical record existence
        mr_id = patient.get("medical_record_id")
        if not mr_id or mr_id not in self.medical_records:
            return {"success": False, "error": "Patient medical record not found"}

        # Validate entry_type
        if entry_type not in ("allergy", "medication"):
            return {"success": False, "error": "entry_type must be 'allergy' or 'medication'"}

        if not entry_value or not isinstance(entry_value, str):
            return {"success": False, "error": "entry_value must be a non-empty string"}

        medical_record = self.medical_records[mr_id]

        # Add entry, verifying there are no duplicates
        target_list_name = "allergies" if entry_type == "allergy" else "medications"
        target_list = medical_record.get(target_list_name)
        if target_list is None:
            medical_record[target_list_name] = []
            target_list = medical_record[target_list_name]
        if entry_value in target_list:
            return {"success": False, "error": f"{entry_type.title()} already recorded for patient"}

        target_list.append(entry_value)

        # Generate an entry ID
        entry_id = f"ENTRY-{uuid.uuid4()}"

        return {"success": True, "id": entry_id, "data": {"patient_id": patient_id, "entry_type": entry_type, "entry_value": entry_value}}