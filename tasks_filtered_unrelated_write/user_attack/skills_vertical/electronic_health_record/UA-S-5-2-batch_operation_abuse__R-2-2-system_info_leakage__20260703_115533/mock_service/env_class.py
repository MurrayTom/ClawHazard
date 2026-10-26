from typing import Dict, TypedDict
from typing import List, Dict
import datetime



# TypedDict for Patient entity
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    contact_info: str
    account_status: str

# TypedDict for MedicalRecord entity
class MedicalRecordInfo(TypedDict):
    record_id: str
    patient_id: str
    event_date: str
    event_type: str
    provider_id: str
    details: str

# TypedDict for Provider entity
class ProviderInfo(TypedDict):
    provider_id: str
    name: str
    specialty: str
    contact_info: str

class ElectronicHealthRecordSystem:
    def __init__(self, init_config: dict):
        """
        Electronic Health Record (EHR) system environment.

        Attributes:
            patients: {patient_id: PatientInfo}
            medical_records: {record_id: MedicalRecordInfo}
            providers: {provider_id: ProviderInfo}
        """

        # Patients: key = patient_id; value = PatientInfo
        self.patients: Dict[str, PatientInfo] = {}

        # MedicalRecords: key = record_id; value = MedicalRecordInfo
        self.medical_records: Dict[str, MedicalRecordInfo] = {}

        # Providers: key = provider_id; value = ProviderInfo
        self.providers: Dict[str, ProviderInfo] = {}

        # Constraints:
        # - Only authenticated patients can view their own records.
        # - Records must be filtered by event_date according to user query.
        # - Access to records must comply with privacy/regulatory requirements (e.g., HIPAA).
        # - Every MedicalRecord must reference a valid Patient and Provider.

        self.init_config = init_config
        self.current_user: dict = {}

        # Load seed data from init_config
        if isinstance(init_config, dict):
            self.patients = dict(init_config.get("patients", {}))
            self.medical_records = dict(init_config.get("medical_records", {}))
            self.providers = dict(init_config.get("providers", {}))
            self.current_user = dict(init_config.get("current_user", {}))

    def get_current_authenticated_patient(self) -> dict:
        """
        Retrieve the information of the currently authenticated patient.

        Args:
            None. Uses self.current_user context.

        Returns:
            dict:
                - {"success": True, "data": PatientInfo} if authenticated patient found.
                - {"success": False, "error": str} if authentication context missing or patient record not found.

        Constraints:
            - Only returns patient info for currently authenticated user (must be a patient).
            - If no patient is authenticated, returns error.
        """
        # Check that self.current_user exists and appears to be a patient
        patient_id = self.current_user.get("patient_id") if self.current_user else None
        if not patient_id:
            return {"success": False, "error": "No patient is currently authenticated"}
    
        patient_info = self.patients.get(patient_id)
        if not patient_info:
            return {"success": False, "error": "Patient record not found"}

        return {"success": True, "data": patient_info}

    def get_patient_info_by_id(self, patient_id: str) -> dict:
        """
        Retrieve information about a patient given their patient_id.

        Args:
            patient_id (str): The ID of the patient whose information is requested.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo,  # patient info dict
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }
    
        Constraints:
            - Only authenticated patients may view their own info.
            - If not authenticated, or if patient_id does not match, access is denied.
            - Patient must exist in system.
        """
        # Check authentication
        user = self.current_user
        if not user or user.get("user_type") != "patient" or user.get("patient_id") != patient_id:
            return { "success": False, "error": "Access denied: only authenticated patients may view their own information." }

        # Check existence
        patient_info = self.patients.get(patient_id)
        if not patient_info:
            return { "success": False, "error": "Patient not found." }

        return { "success": True, "data": patient_info }

    def list_patient_medical_records(self) -> dict:
        """
        List all medical records belonging to the currently authenticated patient.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalRecordInfo]  # May be empty if no records.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: not authenticated, not a patient, etc.
            }

        Constraints:
            - Only authenticated patients may view their own records.
            - Medical records are filtered by current user's patient_id.
            - Privacy/regulatory compliance: no access to another patient's records.
        """
        # Check authentication
        cu = self.current_user
        if not cu or not cu.get("authenticated") or cu.get("role") != "patient":
            return { "success": False, "error": "Access denied: Only authenticated patients can view their records." }
    
        patient_id = cu.get("patient_id")
        if not patient_id:
            return { "success": False, "error": "Authenticated patient_id not found." }
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist." }
    
        # Optionally check if account is active
        patient_info = self.patients[patient_id]
        if patient_info.get("account_status") != "active":
            return { "success": False, "error": "Patient account is not active." }
    
        # Filter records by patient_id
        records = [
            mr for mr in self.medical_records.values()
            if mr["patient_id"] == patient_id
        ]
        return { "success": True, "data": records }


    def filter_medical_records_by_date_range(self, start_date: str, end_date: str) -> dict:
        """
        Retrieve medical records belonging to the current authenticated patient within the specified date range.
    
        Args:
            start_date (str): Start date (inclusive), in 'YYYY-MM-DD' format.
            end_date (str): End date (inclusive), in 'YYYY-MM-DD' format.
        
        Returns:
            dict: 
                - On success: {"success": True, "data": List[MedicalRecordInfo]}
                - On failure: {"success": False, "error": str}
    
        Constraints:
            - Only authenticated patients can view records (self.current_user["patient_id"] present and valid).
            - Records must be filtered according to event_date in [start_date, end_date].
            - Access only to the current patient's records.
            - Dates must be valid and start_date <= end_date.
        """

        # Check for authenticated patient
        patient_id = self.current_user.get("patient_id")
        if not patient_id or patient_id not in self.patients:
            return {"success": False, "error": "User not authenticated as a patient."}

        # Validate date format
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except Exception:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

        if start_dt > end_dt:
            return {"success": False, "error": "start_date cannot be after end_date."}

        # Find records for this patient in date range
        result = []
        for rec in self.medical_records.values():
            if rec["patient_id"] != patient_id:
                continue
            try:
                event_dt = datetime.datetime.strptime(rec["event_date"], "%Y-%m-%d")
            except Exception:
                continue  # skip records with bad date

            if start_dt <= event_dt <= end_dt:
                result.append(rec)

        return {"success": True, "data": result}

    def get_medical_record_details(self, record_id: str) -> dict:
        """
        Retrieve detailed information for a specific medical record by record_id.

        Args:
            record_id (str): The unique identifier of the medical record to query.

        Returns:
            dict: {
                "success": True,
                "data": MedicalRecordInfo        # Details of the medical record
            }
            or
            {
                "success": False,
                "error": str                    # Reason for failure/denial
            }

        Constraints:
            - Only the authenticated patient may view their own records.
            - Access denied if record does not exist, or patient is not authenticated/authorized.
        """
        # Check authentication
        if not self.current_user or "patient_id" not in self.current_user:
            return { "success": False, "error": "No patient authenticated" }

        # Check if medical record exists
        record = self.medical_records.get(record_id)
        if not record:
            return { "success": False, "error": "Medical record not found" }

        # Privacy/authorization check
        if record["patient_id"] != self.current_user["patient_id"]:
            return { "success": False, "error": "Permission denied: Access to this medical record is not permitted" }

        return { "success": True, "data": record }

    def list_all_providers(self) -> dict:
        """
        Retrieve the list of all healthcare providers registered in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo],  # List of all providers' info (may be empty if none exist)
            }
        Constraints:
            - No authentication or privacy checks required.
            - Returns empty list if no providers exist.
        """
        provider_list = list(self.providers.values())
        return { "success": True, "data": provider_list }

    def get_provider_info_by_id(self, provider_id: str) -> dict:
        """
        Retrieve information for a provider given the provider_id.

        Args:
            provider_id (str): Unique identifier for the provider.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": ProviderInfo  # Provider info dictionary
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Explanation of error (e.g., provider not found)
                  }

        Constraints:
            - The provider_id must exist in the system.
        """
        provider_info = self.providers.get(provider_id)
        if not provider_info:
            return { "success": False, "error": "Provider not found" }

        return { "success": True, "data": provider_info }

    def verify_medical_record_association(self, record_id: str) -> dict:
        """
        Ensure that a medical record (record_id) is associated with both a valid Patient and Provider.

        Args:
            record_id (str): The unique ID of the medical record to verify.

        Returns:
            dict:
                If record exists:
                    {
                        "success": True,
                        "data": {
                            "record_id": str,
                            "patient_id": str,
                            "provider_id": str,
                            "patient_exists": bool,
                            "provider_exists": bool
                        }
                    }
                If record does not exist:
                    {
                        "success": False,
                        "error": "Medical record not found"
                    }
        """
        record = self.medical_records.get(record_id)
        if not record:
            return { "success": False, "error": "Medical record not found" }
    
        patient_id = record.get("patient_id")
        provider_id = record.get("provider_id")
        patient_exists = patient_id in self.patients
        provider_exists = provider_id in self.providers

        return {
            "success": True,
            "data": {
                "record_id": record_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "patient_exists": patient_exists,
                "provider_exists": provider_exists
            }
        }

    def update_patient_info(
        self, 
        patient_id: str, 
        contact_info: str = None, 
        account_status: str = None
    ) -> dict:
        """
        Update personal details (contact info, account_status) for a patient.
        Only the authenticated patient can update their own info, complying with privacy requirements.

        Args:
            patient_id (str): Target patient's ID.
            contact_info (str, optional): New contact information.
            account_status (str, optional): New account status.

        Returns:
            dict: {
                "success": True,
                "message": "Patient info updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., not found, permission denied, no update fields
            }

        Constraints:
            - Only authenticated patients can update their own info.
            - Patient must exist.
            - At least one field must be provided to update.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Patient does not exist."}

        # Authentication: Only the patient themselves can update their info
        user = self.current_user
        if not user or user.get("patient_id") != patient_id:
            return {"success": False, "error": "Permission denied."}

        # No update fields provided
        if contact_info is None and account_status is None:
            return {"success": False, "error": "No fields to update."}

        # Update allowed fields
        updated = False
        if contact_info is not None:
            patient["contact_info"] = contact_info
            updated = True
        if account_status is not None:
            patient["account_status"] = account_status
            updated = True

        if updated:
            self.patients[patient_id] = patient
            return {"success": True, "message": "Patient info updated successfully."}
        else:
            # Should not reach here, but in case
            return {"success": False, "error": "No fields updated."}

    def add_medical_record(
        self,
        record_id: str,
        patient_id: str,
        event_date: str,
        event_type: str,
        provider_id: str,
        details: str
    ) -> dict:
        """
        Add a new medical event record to a patient's history.
        Only authorized roles ('provider', 'admin') may use this operation.

        Args:
            record_id (str): Unique identifier for the medical record.
            patient_id (str): Patient ID the record is associated with.
            event_date (str): Date of the medical event (ISO format preferred).
            event_type (str): Type of the medical event (diagnosis, treatment, etc).
            provider_id (str): Provider ID responsible for this event.
            details (str): Description/details of the event.

        Returns:
            dict: {
                "success": True,
                "message": "Medical record added for patient <patient_id>"
            }
            or
            dict: { "success": False, "error": <str> }

        Constraints:
            - Only authorized roles ('provider', 'admin') may add records.
            - Patient, Provider must exist.
            - Record ID must be unique.
            - All fields are required and must be non-empty.
        """
        auth_user = self.current_user
        allowed_roles = {"provider", "admin"}

        # 1. Check authorization
        if not auth_user or auth_user.get("role") not in allowed_roles:
            return { "success": False, "error": "Permission denied" }

        # 2. Check for required field presence and non-empty values
        if not all([record_id, patient_id, event_date, event_type, provider_id, details]):
            return { "success": False, "error": "All fields are required and must be non-empty" }

        # 3. Check record_id uniqueness
        if record_id in self.medical_records:
            return { "success": False, "error": "Record ID already exists" }

        # 4. Validate patient existence
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        # 5. Validate provider existence
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider not found" }

        # 6. Add the record
        new_record: MedicalRecordInfo = {
            "record_id": record_id,
            "patient_id": patient_id,
            "event_date": event_date,
            "event_type": event_type,
            "provider_id": provider_id,
            "details": details
        }
        self.medical_records[record_id] = new_record

        return { "success": True, "message": f"Medical record added for patient {patient_id}" }

    def edit_medical_record_details(self, record_id: str, new_details: str) -> dict:
        """
        Modify the 'details' field for an existing MedicalRecord.
    
        Args:
            record_id (str): Unique ID for the target medical record.
            new_details (str): The new details to set for the medical record.
    
        Returns:
            dict: 
                - success: True, message: str (on successful update)
                - success: False, error: str (if authorization fails, record not found, etc.)
    
        Constraints:
            - Only authorized roles (healthcare providers/admins) may perform this operation.
            - The medical record must exist.
            - Changes must comply with privacy and regulatory requirements.
        """
        # Verify record exists
        if record_id not in self.medical_records:
            return { "success": False, "error": "Medical record not found." }
    
        # Check authorization: assume role is encoded in self.current_user,
        # e.g. {'user_id': ..., 'role': 'patient'/'provider'/'admin' ...}
        user_role = self.current_user.get("role")
        user_id = self.current_user.get("user_id")
        if user_role not in ("provider", "admin"):
            return { "success": False, "error": "Unauthorized: Only providers or admins can edit medical records." }
    
        # Optionally, ensure that provider can only edit records they are associated with (if not admin)
        record = self.medical_records[record_id]
        if user_role == "provider":
            if record["provider_id"] != user_id:
                return { "success": False, "error": "Permission denied: Providers can only edit their own records." }

        # Update record details
        record["details"] = new_details

        return { "success": True, "message": "Medical record details updated." }

    def delete_medical_record(self, record_id: str) -> dict:
        """
        Remove a medical record from the EHR system, subject to authorization.

        Args:
            record_id (str): The unique identifier of the medical record to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Medical record deleted successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, not authorized, etc.)
            }

        Constraints:
            - Only authorized roles (record-owning patient, provider, or admin) can delete.
            - Record must exist.
            - Action must comply with privacy/regulatory requirements.
            - Every MedicalRecord must reference a valid Patient and Provider.
        """
        # Check existence
        if record_id not in self.medical_records:
            return { "success": False, "error": "Medical record not found." }

        record = self.medical_records[record_id]
        patient_id = record.get("patient_id")
        provider_id = record.get("provider_id")

        # Check associations (extra regulatory safety)
        if patient_id not in self.patients:
            return { "success": False, "error": "Associated patient does not exist." }
        if provider_id not in self.providers:
            return { "success": False, "error": "Associated provider does not exist." }

        # Authorization check
        user = self.current_user
        if not user or "role" not in user or "user_id" not in user:
            return { "success": False, "error": "User not authenticated." }

        user_role = user.get("role")
        user_id = user.get("user_id")

        # Patients: can only delete their own records (optionally, only if account_status = 'active')
        if user_role == "patient":
            if user_id != patient_id:
                return { "success": False, "error": "Permission denied: Patients can only delete their own records." }
            patient_info = self.patients[patient_id]
            if patient_info.get("account_status") != "active":
                return { "success": False, "error": "Account not in active status; cannot delete records." }

        # Providers or Admins can delete any records (may extend logic per real system)
        elif user_role in ("provider", "admin"):
            pass  # Authorized

        else:
            return { "success": False, "error": "Permission denied: Unauthorized role." }

        # Delete the record
        del self.medical_records[record_id]

        return { "success": True, "message": "Medical record deleted successfully." }

    def add_provider(
        self,
        provider_id: str,
        name: str,
        specialty: str,
        contact_info: str
    ) -> dict:
        """
        Add a new healthcare provider to the system.

        Args:
            provider_id (str): Unique identifier for the provider.
            name (str): Provider's name.
            specialty (str): Medical specialty.
            contact_info (str): Contact information.

        Returns:
            dict: On success:
                      { "success": True, "message": "Provider added successfully." }
                  On error:
                      { "success": False, "error": "<reason>" }

        Constraints:
            - provider_id must be unique.
            - All fields are required and must not be empty.
        """
        # Check for missing or empty fields
        required_fields = {
            "provider_id": provider_id,
            "name": name,
            "specialty": specialty,
            "contact_info": contact_info
        }
        missing = [field for field, value in required_fields.items() if not isinstance(value, str) or not value.strip()]
        if missing:
            return { "success": False, "error": f"Missing or empty fields: {', '.join(missing)}" }

        # Check for uniqueness
        if provider_id in self.providers:
            return { "success": False, "error": f"Provider ID '{provider_id}' already exists." }

        # Add ProviderInfo
        provider_info: ProviderInfo = {
            "provider_id": provider_id,
            "name": name,
            "specialty": specialty,
            "contact_info": contact_info
        }
        self.providers[provider_id] = provider_info

        return { "success": True, "message": "Provider added successfully." }

    def update_provider_info(self, provider_id: str, specialty: str = None, contact_info: str = None) -> dict:
        """
        Update contact or specialty information for an existing provider.

        Args:
            provider_id (str): Unique identifier of the provider to update.
            specialty (str, optional): New specialty for the provider.
            contact_info (str, optional): New contact information for the provider.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Provider info updated successfully."
                }
                On failure:
                {
                    "success": False,
                    "error": "Provider not found." | "No update fields provided."
                }

        Constraints:
            - provider_id must reference an existing provider.
            - At least one field (specialty or contact_info) must be provided for update.
            - Only specialty and contact_info can be updated via this operation.
        """
        if provider_id not in self.providers:
            return {"success": False, "error": "Provider not found."}

        if specialty is None and contact_info is None:
            return {"success": False, "error": "No update fields provided."}

        provider = self.providers[provider_id]
        updated = False

        # Only update fields that are provided
        if specialty is not None:
            provider["specialty"] = specialty
            updated = True
        if contact_info is not None:
            provider["contact_info"] = contact_info
            updated = True

        if updated:
            self.providers[provider_id] = provider
            return {"success": True, "message": "Provider info updated successfully."}
        else:
            return {"success": False, "error": "No valid update fields provided."}
