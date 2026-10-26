from typing import Dict, List, TypedDict, Optional



class MachineInfo(TypedDict):
    machine_id: str
    type: str
    model: str
    current_condition: str   # Should be one of: "operational", "requires maintenance", "out of order"
    location: str            # location_id

class UsageStatisticsInfo(TypedDict):
    machine_id: str
    usage_hours: float
    usage_count: int
    last_used: str           # ISO timestamp or date string

class MaintenanceRecordInfo(TypedDict):
    record_id: str
    machine_id: str
    date: str                # ISO timestamp or date string
    action_performed: str
    staff_id: str
    notes: Optional[str]     # Inferred from attribute "no"

class LocationInfo(TypedDict):
    location_id: str
    name: str
    description: str

class StaffInfo(TypedDict):
    staff_id: str
    name: str
    role: str
    contact_info: str

class FitnessEquipmentManagementSystem:
    def __init__(self, init_config: dict):
        """
        Environment for fitness equipment management and tracking.
        init_config: external initializer (not implemented here).
        """

        # Machine dictionary mapping machine_id to MachineInfo
        # State space: Machine (machine_id, type, model, current_condition, location)
        self.machines: Dict[str, MachineInfo] = {}

        # Usage statistics per machine_id
        # State space: UsageStatistics (machine_id, usage_hours, usage_count, last_used)
        self.usage_stats: Dict[str, UsageStatisticsInfo] = {}

        # Maintenance records indexed by record_id
        # State space: MaintenanceRecord (record_id, machine_id, date, action_performed, staff_id, notes)
        self.maintenance_records: Dict[str, MaintenanceRecordInfo] = {}

        # Locations indexed by location_id
        # State space: Location (location_id, name, description)
        self.locations: Dict[str, LocationInfo] = {}

        # Staff indexed by staff_id
        # State space: Staff (staff_id, name, role, contact_info)
        self.staff: Dict[str, StaffInfo] = {}

        # Constraints:
        # - Each machine must have a unique machine_id.
        # - current_condition must be in {"operational", "requires maintenance", "out of order"}.
        # - Maintenance records must reference valid machine_ids and staff_ids.
        # - Machine location assignment must correspond to valid location_ids.

        self.init_config = init_config

    def get_machine_by_id(self, machine_id: str) -> dict:
        """
        Retrieve all information for the machine specified by its unique machine_id.

        Args:
            machine_id (str): The unique identifier for the target machine.

        Returns:
            dict: {
                "success": True,
                "data": MachineInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of error, such as machine not found
            }

        Constraints:
            - The provided machine_id must exist in the system.
        """
        machine = self.machines.get(machine_id)
        if not machine:
            return { "success": False, "error": "Not found" }
        return { "success": True, "data": machine }

    def get_machine_condition(self, machine_id: str) -> dict:
        """
        Query the current condition/status of a specific machine.

        Args:
            machine_id (str): Unique identifier of the machine.

        Returns:
            dict: {
                "success": True,
                "data": str  # The current condition of the machine ("operational", "requires maintenance", "out of order")
            }
            or
            {
                "success": False,
                "error": str  # Reason: Machine ID not found
            }

        Constraints:
            - machine_id must exist in the system.
            - Output condition is always one of the allowed states.
        """
        machine = self.machines.get(machine_id)
        if not machine:
            return { "success": False, "error": "Not found" }
    
        return { "success": True, "data": {"machine_id": machine_id, "current_condition": machine["current_condition"]} }

    def list_all_machines(self) -> dict:
        """
        Retrieve the complete list of fitness machines in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MachineInfo],  # Full list of all machine info dicts (may be empty)
            }

        Constraints:
            - Returns full machine list, no filtering or lookup.
            - If no machines exist, returns empty list.
        """
        machine_list = list(self.machines.values())
        return { "success": True, "data": machine_list }

    def list_machines_by_location(self, location_id: str) -> dict:
        """
        Get all machines assigned to a specified location.

        Args:
            location_id (str): The identifier for the location of interest.

        Returns:
            dict: {
                "success": True,
                "data": List[MachineInfo]  # List of machines found at the location
            }

        Constraints:
            - Only machines whose 'location' attribute matches location_id are returned
        """
        result = [
            machine_info for machine_info in self.machines.values()
            if machine_info["location"] == location_id
        ]

        return { "success": True, "data": result }

    def get_usage_statistics(self, machine_id: str) -> dict:
        """
        Retrieve usage statistics (hours, count, last used) for a specific machine.

        Args:
            machine_id (str): Unique identifier of the machine.

        Returns:
            dict: {
                "success": True,
                "data": UsageStatisticsInfo  # Usage data for the machine
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., machine not found or no statistics
            }

        Constraints:
            - machine_id must correspond to a valid machine in self.machines.
            - Usage statistics must be present for the machine_id in self.usage_stats.
        """
        if machine_id not in self.machines:
            return { "success": False, "error": "Not found" }

        usage_data = self.usage_stats.get(machine_id)
        if usage_data is None:
            return { "success": False, "error": "Not found" }

        return { "success": True, "data": usage_data }

    def get_maintenance_history(self, machine_id: str) -> dict:
        """
        Get all maintenance records associated with a given machine_id.

        Args:
            machine_id (str): Unique identifier of the machine.

        Returns:
            dict: 
                - On success: {"success": True, "data": List[MaintenanceRecordInfo]} (records may be empty).
                - On failure: {"success": False, "error": str}

        Constraints:
            - machine_id must exist in the system (self.machines).
            - Returns only records referencing the given machine_id.
        """
        if machine_id not in self.machines:
            return { "success": False, "error": "Not found" }

        records = [
            record for record in self.maintenance_records.values()
            if record["machine_id"] == machine_id
        ]
        return { "success": True, "data": records }

    def get_location_by_id(self, location_id: str) -> dict:
        """
        Retrieve details for a specified facility location.

        Args:
            location_id (str): The unique identifier for the location.

        Returns:
            dict: 
                - On success: {"success": True, "data": LocationInfo}
                - On failure: {"success": False, "error": "Not found"}

        Constraints:
            - The location_id must exist in the system.
        """
        location = self.locations.get(location_id)
        if location is None:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": location}

    def get_staff_by_id(self, staff_id: str) -> dict:
        """
        Retrieve information about a staff member given their staff_id.

        Args:
            staff_id (str): Unique identifier for the staff member.

        Returns:
            dict: 
                - On success: {"success": True, "data": StaffInfo}
                - On failure: {"success": False, "error": "Not found"}

        Constraints:
            - staff_id must exist in the system.
        """
        staff_info = self.staff.get(staff_id)
        if staff_info is None:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": staff_info}

    def list_all_locations(self) -> dict:
        """
        Retrieve all location entries available within the facility.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # List of all locations (may be empty if no locations exist)
            }
        """
        locations_list = list(self.locations.values())
        return { "success": True, "data": locations_list }

    def list_all_staff(self) -> dict:
        """
        Retrieve a list of all staff members registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[StaffInfo]  # List of all staff members; empty if no staff present
            }
        """
        staff_list = list(self.staff.values())
        return { "success": True, "data": staff_list }

    def update_machine_condition(self, machine_id: str, new_condition: str) -> dict:
        """
        Change a machine's current_condition to a new allowed state.

        Args:
            machine_id (str): The ID of the machine to update.
            new_condition (str): The new condition to set. Must be one of:
                "operational", "requires maintenance", "out of order"

        Returns:
            dict: {
                "success": True,
                "data": {...}
            }
            or
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The machine must exist in the system.
            - The new_condition must be one of the allowed states.
        """
        allowed_states = {"operational", "requires maintenance", "out of order"}
        if machine_id not in self.machines:
            return {"success": False, "error": "Machine ID does not exist"}
        if new_condition not in allowed_states:
            return {"success": False, "error": f"Invalid condition. Allowed: {', '.join(allowed_states)}"}
        self.machines[machine_id]["current_condition"] = new_condition
        return {"success": True, "data": self.machines[machine_id]}

    def assign_machine_location(self, machine_id: str, location_id: str) -> dict:
        """
        Move a machine to a new location by specifying the location_id.

        Args:
            machine_id (str): Unique identifier for the machine to move.
            location_id (str): Unique identifier for the new location.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "id": machine_id,
                    "data": {...}
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Error message detailing the failure.
                }

        Constraints:
            - machine_id must exist in the system.
            - location_id must exist in the system.
            - Assignment is idempotent if moving to the same location.
        """
        if machine_id not in self.machines:
            return { "success": False, "error": f"Machine {machine_id} does not exist." }
        if location_id not in self.locations:
            return { "success": False, "error": f"Location {location_id} does not exist." }
    
        self.machines[machine_id]["location"] = location_id
        return {
            "success": True,
            "id": machine_id,
            "data": self.machines[machine_id]
        }

    def add_maintenance_record(
        self,
        record_id: str,
        machine_id: str,
        date: str,
        action_performed: str,
        staff_id: str,
        notes: Optional[str] = None
    ) -> dict:
        """
        Create and store a new maintenance record for a machine, referencing valid staff.

        Args:
            record_id (str): Unique identifier for the maintenance record.
            machine_id (str): ID of the machine maintained (must exist).
            date (str): Date/time of maintenance (ISO/date string).
            action_performed (str): Description of maintenance performed.
            staff_id (str): ID of the staff member performing maintenance (must exist).
            notes (Optional[str]): Additional notes.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "id": record_id,
                        "data": {...}
                    }
                On error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - record_id must not already exist.
            - machine_id and staff_id must exist in the system.
            - All required fields except notes must be provided.
        """
        # Check record_id uniqueness
        if record_id in self.maintenance_records:
            return { "success": False, "error": "Record ID already exists." }

        # Validate machine_id
        if machine_id not in self.machines:
            return { "success": False, "error": f"Machine ID '{machine_id}' does not exist." }

        # Validate staff_id
        if staff_id not in self.staff:
            return { "success": False, "error": f"Staff ID '{staff_id}' does not exist." }

        # Required field checks (notes is optional)
        if not all([record_id, machine_id, date, action_performed, staff_id]):
            return { "success": False, "error": "Missing required field(s)." }

        record = {
            "record_id": record_id,
            "machine_id": machine_id,
            "date": date,
            "action_performed": action_performed,
            "staff_id": staff_id,
            "notes": notes,
        }
        self.maintenance_records[record_id] = record

        return {
            "success": True,
            "id": record_id,
            "data": record
        }

    def edit_maintenance_record(
        self,
        record_id: str,
        action_performed: Optional[str] = None,
        date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Update attributes ('action_performed', 'date', 'notes') of an existing maintenance record.

        Args:
            record_id (str): Unique identifier for the maintenance record to update.
            action_performed (Optional[str]): New action performed (if updating).
            date (Optional[str]): New date for the record (if updating).
            notes (Optional[str]): New notes for the record (if updating).

        Returns:
            dict:
                - success: True and data on success.
                - success: False and error on failure (record not found, no fields to update).

        Constraints:
            - record_id must exist in the records.
            - At least one attribute to update must be provided.
        """
        if record_id not in self.maintenance_records:
            return { "success": False, "error": "Maintenance record not found." }

        to_update = {}
        if action_performed is not None:
            if not isinstance(action_performed, str):
                return { "success": False, "error": "action_performed must be a string." }
            to_update['action_performed'] = action_performed
        if date is not None:
            if not isinstance(date, str):
                return { "success": False, "error": "date must be a string." }
            to_update['date'] = date
        if notes is not None:
            if not isinstance(notes, str):
                return { "success": False, "error": "notes must be a string." }
            to_update['notes'] = notes

        if not to_update:
            return { "success": False, "error": "No valid attribute provided to update." }

        # Perform updates
        self.maintenance_records[record_id].update(to_update)
        return { "success": True, "data": self.maintenance_records[record_id] }

    def delete_maintenance_record(self, record_id: str) -> dict:
        """
        Remove a maintenance record from the history.

        Args:
            record_id (str): The unique maintenance record identifier to be deleted.

        Returns:
            dict: {
                "success": True,
                "deleted_id": record_id
            }
            or
            {
                "success": False,
                "error": "Maintenance record not found."
            }

        Constraints:
            - The record_id must exist in the maintenance_records.
            - No need to check associated machine_id or staff_id for deletion.
        """
        if record_id not in self.maintenance_records:
            return { "success": False, "error": "Maintenance record not found." }

        del self.maintenance_records[record_id]
        return { "success": True, "deleted_id": record_id }

    def update_usage_statistics(
        self,
        machine_id: str,
        usage_hours: Optional[float] = None,
        usage_count: Optional[int] = None,
        last_used: Optional[str] = None
    ) -> dict:
        """
        Update the usage statistics for a specific machine.

        Args:
            machine_id (str): Unique identifier of the machine.
            usage_hours (Optional[float]): New total usage hours (must be non-negative if provided).
            usage_count (Optional[int]): New usage count (must be non-negative if provided).
            last_used (Optional[str]): New last-used timestamp/date string.

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
            - machine_id must exist in self.machines and self.usage_stats.
            - At least one of usage_hours, usage_count, last_used must be provided.
            - If provided, usage_hours/usage_count must be non-negative.
        """
        # Check machine existence
        if machine_id not in self.machines:
            return { "success": False, "error": "machine_id does not exist" }

        if machine_id not in self.usage_stats:
            # Initialize usage stats if not present
            self.usage_stats[machine_id] = {
                "machine_id": machine_id,
                "usage_hours": 0.0,
                "usage_count": 0,
                "last_used": ""
            }

        # Ensure at least one updating value provided
        if usage_hours is None and usage_count is None and last_used is None:
            return { "success": False, "error": "No update parameters provided" }

        usage_info = self.usage_stats[machine_id]

        # Validate and update usage_hours
        if usage_hours is not None:
            if not isinstance(usage_hours, (int, float)) or usage_hours < 0:
                return { "success": False, "error": "usage_hours must be a non-negative number" }
            usage_info["usage_hours"] = float(usage_hours)

        # Validate and update usage_count
        if usage_count is not None:
            if not isinstance(usage_count, int) or usage_count < 0:
                return { "success": False, "error": "usage_count must be a non-negative integer" }
            usage_info["usage_count"] = int(usage_count)

        # Update last_used
        if last_used is not None:
            if not isinstance(last_used, str):
                return { "success": False, "error": "last_used must be a string timestamp" }
            usage_info["last_used"] = last_used

        return { "success": True, "data": usage_info }

    def add_machine(
        self,
        machine_id: str,
        type: str,
        model: str,
        current_condition: str,
        location: str
    ) -> dict:
        """
        Add a new machine entry to the system.

        Args:
            machine_id (str): Unique identifier for the machine.
            type (str): Machine type (e.g., treadmill, bike).
            model (str): Model info.
            current_condition (str): One of "operational", "requires maintenance", "out of order".
            location (str): Location ID where this machine is placed.

        Returns:
            dict: {
                "success": True,
                "id": machine_id,
                "data": {...}
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - machine_id must be unique.
            - current_condition must be valid.
            - location must exist.
        """
        valid_conditions = {"operational", "requires maintenance", "out of order"}
        if machine_id in self.machines:
            return { "success": False, "error": "machine_id already exists." }
        if current_condition not in valid_conditions:
            return { "success": False, "error": "Invalid current_condition. Must be one of operational, requires maintenance, out of order." }
        if location not in self.locations:
            return { "success": False, "error": "Invalid location_id." }

        machine_info: MachineInfo = {
            "machine_id": machine_id,
            "type": type,
            "model": model,
            "current_condition": current_condition,
            "location": location
        }
        self.machines[machine_id] = machine_info
        return { "success": True, "id": machine_id, "data": machine_info }

    def remove_machine(self, machine_id: str) -> dict:
        """
        Delete a machine from the system (disposal), along with its associated usage statistics and maintenance records.

        Args:
            machine_id (str): Unique identifier of the machine to remove.

        Returns:
            dict: {
                "success": True,
                "deleted_id": machine_id
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure (e.g. machine does not exist)
            }

        Constraints:
            - Only removes machine if it exists.
            - Also deletes associated UsageStatistics and MaintenanceRecords for machine_id.
            - Location and staff objects are not modified.
        """
        if machine_id not in self.machines:
            return { "success": False, "error": "Machine does not exist." }

        # Remove the machine
        del self.machines[machine_id]

        # Remove associated usage statistics
        if machine_id in self.usage_stats:
            del self.usage_stats[machine_id]

        # Remove associated maintenance records
        records_to_delete = [record_id for record_id, rec in self.maintenance_records.items()
                             if rec["machine_id"] == machine_id]
        for record_id in records_to_delete:
            del self.maintenance_records[record_id]

        return {
            "success": True,
            "deleted_id": machine_id
        }

    def add_location(self, location_id: str, name: str, description: str) -> dict:
        """
        Add a new equipment location to the system.

        Args:
            location_id (str): Unique identifier for the location.
            name (str): Human-readable name of the location.
            description (str): Description/details of the location.

        Returns:
            dict: {
                "success": True,
                "id": location_id,
                "data": {...}
            }
            or
            {
                "success": False,
                "error": "Reason for failure (e.g., location_id already exists, invalid input)"
            }

        Constraints:
            - location_id must be unique.
            - name and description should not be empty.
        """
        if not location_id or not isinstance(location_id, str):
            return { "success": False, "error": "Invalid location_id." }

        if location_id in self.locations:
            return { "success": False, "error": "Location ID already exists." }

        if not name or not isinstance(name, str):
            return { "success": False, "error": "Location name cannot be empty." }

        if not description or not isinstance(description, str):
            return { "success": False, "error": "Location description cannot be empty." }

        location_data = {
            "location_id": location_id,
            "name": name,
            "description": description,
        }
        self.locations[location_id] = location_data

        return { "success": True, "id": location_id, "data": location_data }

    def update_location(self, location_id: str, name: Optional[str] = None, description: Optional[str] = None) -> dict:
        """
        Modify details (name, description) of an existing location.

        Args:
            location_id (str): The identifier of the location to update.
            name (Optional[str]): New name, if updating.
            description (Optional[str]): New description, if updating.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": {...}
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason, e.g., "Location does not exist"
                }

        Constraints:
            - location_id must exist in the system.
            - Only name/description are modifiable.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }

        location = self.locations[location_id]
        if name is not None:
            location["name"] = name
        if description is not None:
            location["description"] = description

        self.locations[location_id] = location

        return { 
            "success": True, 
            "data": self.locations[location_id]
        }

    def remove_location(self, location_id: str) -> dict:
        """
        Delete a location from the system, if and only if no machine is currently assigned to that location.

        Args:
            location_id (str): The unique identifier for the location to delete.

        Returns:
            dict: 
                On success:
                    { "success": True, "deleted_id": location_id }
                On failure:
                    { "success": False, "error": "Location does not exist." }
                    { "success": False, "error": "Cannot delete location: machine(s) assigned to this location." }

        Constraints:
            - Location must exist.
            - No machine may be assigned to this location.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist." }

        assigned_machines = [m for m in self.machines.values() if m["location"] == location_id]
        if assigned_machines:
            return {
                "success": False,
                "error": "Cannot delete location: machine(s) assigned to this location."
            }

        del self.locations[location_id]
        return {
            "success": True,
            "deleted_id": location_id
        }

    def add_staff(
        self,
        staff_id: str,
        name: str,
        role: str,
        contact_info: str
    ) -> dict:
        """
        Add a new staff member to the system.

        Args:
            staff_id (str): Unique identifier for the staff member.
            name (str): Human-readable staff name.
            role (str): Staff role (e.g., technician, manager).
            contact_info (str): Contact information for the staff member.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "id": staff_id,
                        "data": {...}
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - staff_id must be unique (cannot already exist).
            - All fields should be non-empty strings.
        """
        # Validate unique staff_id
        if staff_id in self.staff:
            return { "success": False, "error": "Staff ID already exists." }

        # Basic validation for input fields
        if not all(isinstance(f, str) and f.strip() for f in [staff_id, name, role, contact_info]):
            return { "success": False, "error": "All fields must be non-empty strings." }

        staff_info = {
            "staff_id": staff_id,
            "name": name,
            "role": role,
            "contact_info": contact_info
        }
        self.staff[staff_id] = staff_info
        return { "success": True, "id": staff_id, "data": staff_info }

    def update_staff(
        self,
        staff_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        contact_info: Optional[str] = None
    ) -> dict:
        """
        Edit the information of a staff member.

        Args:
            staff_id (str): Identifier of the staff member to update.
            name (Optional[str]): New name for staff member, if updating.
            role (Optional[str]): New role for staff member, if updating.
            contact_info (Optional[str]): New contact information, if updating.

        Returns:
            dict: {
                "success": True,
                "data": {...}
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - staff_id must exist in system.
            - At least one of name, role, contact_info must be provided for update.
        """
        # Check staff exists
        if staff_id not in self.staff:
            return { "success": False, "error": "Staff ID does not exist." }

        # Check at least one field to update
        if name is None and role is None and contact_info is None:
            return { "success": False, "error": "No update fields provided." }

        # Update fields in info
        staff_info = self.staff[staff_id]
        if name is not None:
            staff_info['name'] = name
        if role is not None:
            staff_info['role'] = role
        if contact_info is not None:
            staff_info['contact_info'] = contact_info

        self.staff[staff_id] = staff_info

        return { "success": True, "data": self.staff[staff_id] }

    def remove_staff(self, staff_id: str) -> dict:
        """
        Delete a staff member from the registry, if not referenced in maintenance records.

        Args:
            staff_id (str): Unique identifier for the staff member to remove.

        Returns:
            dict: {
                "success": True,
                "deleted_id": staff_id
                }
                OR
                {
                "success": False,
                "error": str
            }

        Constraints:
            - Staff member must exist.
            - Staff member must NOT be referenced in any maintenance record (maintenance_records[record_id]['staff_id'] == staff_id).
        """

        if staff_id not in self.staff:
            return { "success": False, "error": "Staff ID does not exist." }

        for record in self.maintenance_records.values():
            if record.get("staff_id") == staff_id:
                return { 
                    "success": False, 
                    "error": "Staff is referenced in maintenance records and cannot be removed." 
                }

        del self.staff[staff_id]

        return { 
            "success": True, 
            "deleted_id": staff_id
        }