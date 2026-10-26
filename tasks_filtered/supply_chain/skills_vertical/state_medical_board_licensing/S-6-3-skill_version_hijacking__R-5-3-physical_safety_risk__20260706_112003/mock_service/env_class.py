from typing import Dict, List, TypedDict
from datetime import datetime
import uuid



# Provider entity
class ProviderInfo(TypedDict):
    provider_id: str
    name: str
    date_of_birth: str
    profession: str
    contact_information: str

# License entity
class LicenseInfo(TypedDict):
    license_id: str
    provider_id: str
    license_number: str
    state: str
    status: str  # active, expired, suspended, revoked
    issuance_date: str
    expiration_date: str
    profession: str

# LicenseAction entity
class LicenseActionInfo(TypedDict):
    license_id: str
    action_type: str
    action_date: str
    action_description: str

class StateMedicalBoardProviderLicensingSystem:
    def __init__(self, init_config: dict):
        """
        State Medical Board Provider Licensing System environment.
        """

        # Providers (healthcare professionals)
        # {provider_id: ProviderInfo}
        self.providers: Dict[str, ProviderInfo] = {}

        # Licenses (official licensure entities)
        # {license_id: LicenseInfo}
        self.licenses: Dict[str, LicenseInfo] = {}

        # Historical licensure actions per license
        # {license_id: [LicenseActionInfo, ...]}
        self.license_actions: Dict[str, List[LicenseActionInfo]] = {}

        # Constraints:
        # - Providers may hold multiple licenses in different professions or states
        # - A license is valid only if status=="active" and expiration_date >= current date
        # - Disciplinary/compliance actions must be recorded in license_actions
        # - Licenses uniquely identified by license_number within a state and profession

        self.init_config = init_config

    def get_provider_by_name(self, name: str) -> dict:
        """
        Retrieve provider information(s) using a full or partial, case-insensitive name search.

        Args:
            name (str): The full or partial name to search for (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo],  # All matching providers, [] if none
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid
            }

        Constraints:
            - Match is case-insensitive substring.
            - Empty matches should return success with empty data.
        """
        if not isinstance(name, str):
            return { "success": False, "error": "Name must be a string." }
        name = name.strip()
        if not name:
            return { "success": True, "data": [] }

        lowered_name = name.lower()
        matches = [
            provider_info
            for provider_info in self.providers.values()
            if lowered_name in provider_info["name"].lower()
        ]

        return { "success": True, "data": matches }

    def get_provider_by_id(self, provider_id: str) -> dict:
        """
        Retrieve provider data (demographics, profession, contact) for the given provider_id.

        Args:
            provider_id (str): Unique identifier for the healthcare provider.

        Returns:
            dict:
                - If found: { "success": True, "data": ProviderInfo }
                - If not found: { "success": False, "error": "Provider not found" }
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return { "success": False, "error": "Provider not found" }
        return { "success": True, "data": provider }

    def list_all_providers(self) -> dict:
        """
        Obtain a list of all registered providers in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo]  # List of provider records (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (should not occur in normal query)
            }

        Constraints:
            - None: Returns all providers present in the system.
        """
        try:
            providers_list = list(self.providers.values())
            return { "success": True, "data": providers_list }
        except Exception as e:
            return { "success": False, "error": f"Internal error: {str(e)}" }

    def get_provider_licenses(self, provider_id: str) -> dict:
        """
        Fetch all licenses associated with the specified provider_id.

        Args:
            provider_id (str): Unique identifier for the provider.

        Returns:
            dict: {
                "success": True,
                "data": List[LicenseInfo],  # All licenses for this provider (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. Provider not found
            }

        Constraints:
            - provider_id must correspond to an existing provider in the system.
        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider not found" }

        licenses = [
            license_info
            for license_info in self.licenses.values()
            if license_info["provider_id"] == provider_id
        ]

        return { "success": True, "data": licenses }

    def get_license_by_number_state_profession(self, license_number: str, state: str, profession: str) -> dict:
        """
        Retrieve a license record by its license_number, state, and profession.

        Args:
            license_number (str): The license identifier (unique within state/profession)
            state (str): The state/jurisdiction in question
            profession (str): The healthcare profession in question

        Returns:
            dict: {
                "success": True,
                "data": LicenseInfo  # License details
            }
            or
            {
                "success": False,
                "error": str  # Explanation when license cannot be found
            }

        Constraints:
            - (license_number, state, profession) combination must uniquely identify a license.
        """
        # Find license matching all three criteria
        found = None
        for lic in self.licenses.values():
            if (
                lic["license_number"] == license_number and
                lic["state"] == state and
                lic["profession"] == profession
            ):
                found = lic
                break

        if found is None:
            return {
                "success": False,
                "error": "No license found for given license_number, state, and profession"
            }
        return {
            "success": True,
            "data": found
        }

    def list_licenses_by_state(self, state: str) -> dict:
        """
        List all licenses registered in the specified state.

        Args:
            state (str): The state for which to retrieve licenses.

        Returns:
            dict: {
                "success": True,
                "data": List[LicenseInfo],  # All licenses with matching state (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if the input is invalid
            }

        Constraints:
            - state should be a non-empty string.
            - No additional filtering or permission required.
        """
        if not isinstance(state, str) or not state.strip():
            return {"success": False, "error": "State must be a non-empty string."}

        licenses_in_state = [
            license_info for license_info in self.licenses.values()
            if license_info["state"] == state
        ]

        return {"success": True, "data": licenses_in_state}

    def list_licenses_by_status(self, status: str) -> dict:
        """
        List all licenses in the system with the specified status.

        Args:
            status (str): The license status to filter by (e.g., "active", "expired", "suspended", "revoked").

        Returns:
            dict: {
                "success": True,
                "data": List[LicenseInfo],  # List of licenses matching the status (possibly empty)
            }

        Constraints:
            - Accepts any status string; if no license matches, returns an empty list.
        """
        result = [
            license_info for license_info in self.licenses.values()
            if license_info["status"] == status
        ]
        return { "success": True, "data": result }


    def get_valid_licenses_for_provider_in_state(self, provider_id: str, state: str) -> dict:
        """
        Returns all currently valid (active, not expired) licenses for a given provider in a specified state.

        Args:
            provider_id (str): ID of the provider whose licenses to query.
            state (str): State in which to look for valid licenses.

        Returns:
            dict: {
                "success": True,
                "data": List[LicenseInfo],  # List of valid licenses for provider in state (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. provider not found
            }

        Constraints:
            - License must have status == 'active' and expiration_date >= current date.
            - provider_id must exist in the system.
        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider not found" }

        current_date = datetime.utcnow().date()
        valid_licenses = []
        for license_info in self.licenses.values():
            if (
                license_info["provider_id"] == provider_id
                and license_info["state"] == state
                and license_info["status"] == "active"
            ):
                try:
                    # Assume ISO date string (YYYY-MM-DD) for expiration_date
                    expiration = datetime.strptime(license_info["expiration_date"], "%Y-%m-%d").date()
                    if expiration >= current_date:
                        valid_licenses.append(license_info)
                except Exception:
                    # Skip licenses with invalid date format
                    continue

        return { "success": True, "data": valid_licenses }

    def get_license_status(self, license_id: str) -> dict:
        """
        Query the current status of a license, given its license_id.

        Args:
            license_id (str): Unique identifier for the license in the system.

        Returns:
            dict: 
                Success: {
                    "success": True,
                    "data": {
                        "license_id": str,
                        "status": str  # License status: active, expired, suspended, revoked
                    }
                }
                Failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g. license not found
                }
        Constraints:
            - The specified license_id must exist within the system.
        """
        license_info = self.licenses.get(license_id)
        if not license_info:
            return { "success": False, "error": "License not found" }
        return {
            "success": True,
            "data": {
                "license_id": license_id,
                "status": license_info["status"]
            }
        }

    def get_license_expiration_date(self, license_id: str) -> dict:
        """
        Query the expiration date of a license.

        Args:
            license_id (str): The unique identifier of the license.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": str  # The expiration date in string format (ISO or YYYY-MM-DD)
                }
                On failure (e.g. license not found):
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - None for query; license_id must exist.
        """

        license_info = self.licenses.get(license_id)
        if not license_info:
            return {"success": False, "error": "License not found"}

        return {"success": True, "data": license_info["expiration_date"]}

    def get_license_actions(self, license_id: str) -> dict:
        """
        List all historical disciplinary or compliance actions (e.g., suspensions, reinstatements)
        for a given license.

        Args:
            license_id (str): The unique ID of the license whose actions are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[LicenseActionInfo],  # List of actions, may be empty.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., License not found.
            }

        Constraints:
            - license_id must exist in the system.
        """
        if license_id not in self.licenses:
            return { "success": False, "error": "License not found" }

        actions = self.license_actions.get(license_id, [])
        return { "success": True, "data": actions }

    def check_license_validity(self, license_id: str, current_date: str) -> dict:
        """
        Verify if a license is valid (status is 'active' and expiration_date >= current_date).

        Args:
            license_id (str): The unique identifier for the license.
            current_date (str): The date to check validity against, in 'YYYY-MM-DD' format.

        Returns:
            dict: {
                "success": True,
                "result": bool,
                "details": str
            }
            or
            {
                "success": False,
                "error": str  # reason for failure: invalid license, wrong date format, etc.
            }

        Constraints:
            - License must exist.
            - License is valid only if status == 'active' and expiration_date >= current_date.
            - Assumes ISO date format ('YYYY-MM-DD') for date comparison.
        """
        license_info = self.licenses.get(license_id)
        if not license_info:
            return {"success": False, "error": "License does not exist"}

        status = license_info["status"]
        expiration_date = license_info["expiration_date"]

        # Compare dates: expiration_date >= current_date
        try:
            exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d")
            curr_dt = datetime.strptime(current_date, "%Y-%m-%d")
        except Exception:
            return {"success": False, "error": "Invalid date format; expected 'YYYY-MM-DD'"}

        is_valid = (status == "active") and (exp_dt >= curr_dt)

        if is_valid:
            details = f"License {license_id} is valid: status is '{status}' and expiration date {expiration_date} is on or after {current_date}."
        else:
            details = f"License {license_id} is not valid: status is '{status}', expiration date is {expiration_date}."

        return {"success": True, "result": is_valid, "details": details}


    def update_license_status(self, license_id: str, new_status: str, action_type: str = "status change", action_description: str = "") -> dict:
        """
        Change the status of a license (e.g., suspend, revoke, reinstate) and record the action.
    
        Args:
            license_id (str): The ID of the license to modify.
            new_status (str): The status to set ("active", "expired", "suspended", "revoked").
            action_type (str, optional): Type of action (default: "status change").
            action_description (str, optional): Details/reason for the status change.
        
        Returns:
            dict: {
                "success": True,
                "data": LicenseInfo  # Updated license record
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - License must exist.
            - Status must be one of the allowed values ("active", "expired", "suspended", "revoked").
            - Every status change is recorded as a LicenseAction.
        """
        allowed_statuses = {"active", "expired", "suspended", "revoked"}
        if license_id not in self.licenses:
            return { "success": False, "error": "License not found." }

        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status ('{new_status}'). Allowed: {', '.join(allowed_statuses)}" }

        old_status = self.licenses[license_id]["status"]
        self.licenses[license_id]["status"] = new_status

        # Record the license action (disciplinary/compliance event)
        action_record: LicenseActionInfo = {
            "license_id": license_id,
            "action_type": action_type,
            "action_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "action_description": action_description if action_description else f"Status changed from {old_status} to {new_status}."
        }
        if license_id not in self.license_actions:
            self.license_actions[license_id] = []
        self.license_actions[license_id].append(action_record)

        return { "success": True, "data": dict(self.licenses[license_id]) }

    def record_license_action(
        self, license_id: str, action_type: str, action_date: str, action_description: str
    ) -> dict:
        """
        Log a new action/event to the license's historical actions.

        Args:
            license_id (str): Unique identifier for the license to which the action applies.
            action_type (str): Type of action (e.g., suspension, notification, reinstatement).
            action_date (str): ISO date string when the action occurred.
            action_description (str): Brief details or explanation about the action.

        Returns:
            dict:
              - On success: { "success": True, "id": str, "timestamp": str }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - license_id must exist in self.licenses.
            - All input fields must be non-empty strings.
            - Action is appended to self.license_actions for that license_id.
        """

        if not license_id or license_id not in self.licenses:
            return { "success": False, "error": "License ID does not exist." }

        # Check input requirement: all fields non-empty
        if not all([action_type, action_date, action_description]):
            return { "success": False, "error": "All action fields must be provided and non-empty." }

        action_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        action_info = {
            "license_id": license_id,
            "action_type": action_type,
            "action_date": action_date,
            "action_description": action_description,
        }

        # If no record for this license_id, initialize
        if license_id not in self.license_actions:
            self.license_actions[license_id] = []

        self.license_actions[license_id].append(action_info)

        return { "success": True, "id": action_id, "timestamp": timestamp }

    def update_license_expiration_date(self, license_id: str, new_expiration_date: str) -> dict:
        """
        Modify the expiration date for a license.

        Args:
            license_id (str): Unique identifier of the license to update.
            new_expiration_date (str): New expiration date value (format: "YYYY-MM-DD").

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": LicenseInfo  # Updated license record
                }
                On error: {
                    "success": False,
                    "error": "License not found."
                }

        Constraints:
            - license_id must exist.
            - Upon update, a LicenseAction should be recorded.
        """
        if license_id not in self.licenses:
            return { "success": False, "error": "License not found." }

        # Update the expiration date
        self.licenses[license_id]["expiration_date"] = new_expiration_date

        # Record compliance/renewal event as a license action (per constraints)
        action = {
            "license_id": license_id,
            "action_type": "expiration_update",
            "action_date": new_expiration_date,  # using new expiration as the action date
            "action_description": f"Expiration date updated to {new_expiration_date}."
        }
        if license_id in self.license_actions:
            self.license_actions[license_id].append(action)
        else:
            self.license_actions[license_id] = [action]

        return {
            "success": True,
            "data": dict(self.licenses[license_id])
        }

    def add_license_for_provider(
        self,
        provider_id: str,
        license_number: str,
        state: str,
        status: str,
        issuance_date: str,
        expiration_date: str,
        profession: str
    ) -> dict:
        """
        Issue a new license to a provider (add new license record).

        Args:
            provider_id (str): The provider's unique ID.
            license_number (str): The license identifier in its jurisdiction.
            state (str): State in which license is issued.
            status (str): One of "active", "expired", "suspended", "revoked".
            issuance_date (str): Date license was issued (ISO format).
            expiration_date (str): Date license expires (ISO format).
            profession (str): Professional category covered by license.

        Returns:
            dict: {
                "success": True,
                "id": str,
                "data": LicenseInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Provider must exist.
            - License (license_number, state, profession) must not duplicate any existing license.
            - Status must be one of allowed values.
        """
        allowed_statuses = {"active", "expired", "suspended", "revoked"}
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid license status" }

        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        # Check for uniqueness: license_number, state, profession
        for lic in self.licenses.values():
            if (lic["license_number"] == license_number and
                lic["state"] == state and
                lic["profession"] == profession):
                return { "success": False, "error": "Duplicate license (license_number/state/profession) already exists." }

        # Generate unique license_id (simple auto-increment or UUID)
        license_id = str(uuid.uuid4())

        new_license: LicenseInfo = {
            "license_id": license_id,
            "provider_id": provider_id,
            "license_number": license_number,
            "state": state,
            "status": status,
            "issuance_date": issuance_date,
            "expiration_date": expiration_date,
            "profession": profession
        }

        self.licenses[license_id] = new_license
        # License actions empty at creation
        self.license_actions[license_id] = []

        return {
            "success": True,
            "id": license_id,
            "data": dict(new_license)
        }

    def delete_license(self, license_id: str) -> dict:
        """
        Remove a license from the system, including any associated license actions.

        Args:
            license_id (str): The unique ID of the license to delete.

        Returns:
            dict: 
                {"success": True, "deleted_id": str}
                OR
                {"success": False, "error": "License not found"}

        Constraints:
            - License must exist.
            - Associated LicenseActions for this license_id are also removed.
        """
        if license_id not in self.licenses:
            return {"success": False, "error": "License not found"}

        # Remove the license
        del self.licenses[license_id]

        # Remove associated license actions (if any)
        if license_id in self.license_actions:
            del self.license_actions[license_id]

        return {"success": True, "deleted_id": license_id}

    def update_provider_info(
        self,
        provider_id: str,
        name: str = None,
        date_of_birth: str = None,
        profession: str = None,
        contact_information: str = None
    ) -> dict:
        """
        Edit demographic or contact info for a provider.

        Args:
            provider_id (str): Unique identifier of the provider to update.
            name (str, optional): New name (if updating).
            date_of_birth (str, optional): New date of birth (if updating).
            profession (str, optional): New profession (if updating).
            contact_information (str, optional): New contact information (if updating).

        Returns:
            dict:
              - success: True and data with updated provider record.
              - success: False and error string if provider does not exist
                or no fields to update or invalid field.

        Constraints:
            - provider_id must exist in the system.
            - Only the provided fields are updated. Others left unchanged.
            - At least one updatable field must be provided.

        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        fields_to_update = {}
        if name is not None:
            fields_to_update["name"] = name
        if date_of_birth is not None:
            fields_to_update["date_of_birth"] = date_of_birth
        if profession is not None:
            fields_to_update["profession"] = profession
        if contact_information is not None:
            fields_to_update["contact_information"] = contact_information

        if not fields_to_update:
            return { "success": False, "error": "No fields specified for update" }

        for key, value in fields_to_update.items():
            self.providers[provider_id][key] = value

        return {
            "success": True,
            "data": dict(self.providers[provider_id])
        }