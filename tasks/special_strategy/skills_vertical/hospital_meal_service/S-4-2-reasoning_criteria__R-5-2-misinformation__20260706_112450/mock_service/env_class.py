from typing import Dict, List, TypedDict
import uuid



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    medical_conditions: List[str]
    dietary_restrictions: List[str]
    room_num: str  # could also be int if needed

class MealInfo(TypedDict):
    meal_id: str
    name: str
    description: str
    dietary_properties: List[str]
    allergen_info: str

class MealScheduleInfo(TypedDict):
    meal_id: str
    scheduled_datetime: str  # e.g., ISO format datetime
    availability_sta: str    # e.g., 'available', 'unavailable'

class StaffInfo(TypedDict):
    staff_id: str
    name: str
    role: str

class HospitalMealManagementSystem:
    def __init__(self, init_config: dict):
        """
        Environment for hospital meal management system.
        init_config: external initializer.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Meals: {meal_id: MealInfo}
        self.meals: Dict[str, MealInfo] = {}

        # MealSchedules: {meal_id: List[MealScheduleInfo]}
        self.meal_schedules: Dict[str, List[MealScheduleInfo]] = {}

        # Staff: {staff_id: StaffInfo}
        self.staff: Dict[str, StaffInfo] = {}

        # Assignments list
        self.assignments: List[dict] = []

        # --- Constraints (see business logic for enforcement) ---
        # 1. Meal offerings must comply with patient dietary restrictions and medical conditions.
        # 2. Meal can only be assigned if available for the scheduled date/time.
        # 3. Allergen information must be accurate and current.
        # 4. Patients receive only meals appropriate for their care protocol.

        self.init_config = init_config

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve the complete profile of a patient, including dietary restrictions, by patient_id.

        Args:
            patient_id (str): Identifier of the patient to query.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # contains patient_id, name, medical_conditions, dietary_restrictions, room_num
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., patient not found
            }

        Constraints:
            - patient_id must exist within the system's patient records.
        """
        patient_info = self.patients.get(patient_id)
        if not patient_info:
            return {"success": False, "error": "Patient not found"}

        return {"success": True, "data": patient_info}

    def get_patients_by_condition(self, condition: str) -> dict:
        """
        List patients filtered by a specific medical condition.

        Args:
            condition (str): The medical condition to filter patients by.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo],  # Patient profiles matching condition (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid condition parameter)
            }

        Constraints:
            - Condition must be a non-empty string.
            - Performs case-sensitive match in patient['medical_conditions'] list.
        """
        if not isinstance(condition, str) or condition.strip() == "":
            return { "success": False, "error": "Medical condition must be a non-empty string." }

        result = [
            patient
            for patient in self.patients.values()
            if condition in patient.get("medical_conditions", [])
        ]

        return { "success": True, "data": result }

    def get_patient_dietary_restrictions(self, patient_id: str) -> dict:
        """
        Retrieve the dietary restrictions list for the specified patient.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[str]  # List of dietary restrictions, possibly empty
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (e.g. patient not found)
                    }
        Constraints:
            - patient_id must exist in the system.
        """
        patient_info = self.patients.get(patient_id)
        if patient_info is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient_info.get("dietary_restrictions", []) }

    def list_all_meals(self) -> dict:
        """
        Retrieve the full list of all meals currently available in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MealInfo]  # possibly empty if no meals exist
            }
            or
            {
                "success": False,
                "error": str  # description of the error
            }

        Constraints:
            - No specific constraints; just retrieves all meal entries.
        """
        if not hasattr(self, "meals") or not isinstance(self.meals, dict):
            return { "success": False, "error": "Meal data storage is corrupted or inaccessible." }

        return { "success": True, "data": list(self.meals.values()) }

    def get_meal_by_id(self, meal_id: str) -> dict:
        """
        Retrieve full meal details for a specified meal_id, including all properties and allergen information.

        Args:
            meal_id (str): The ID of the meal to query.

        Returns:
            dict: {
                "success": True,
                "data": MealInfo  # All details about the meal
            }
            or
            {
                "success": False,
                "error": str  # Reason meal could not be returned (e.g., not found)
            }

        Constraints:
            - Provided meal_id must exist in the system.
        """
        meal_info = self.meals.get(meal_id)
        if meal_info is None:
            return { "success": False, "error": "Meal not found" }

        return { "success": True, "data": meal_info }

    def get_meals_by_property(self, property: str) -> dict:
        """
        List all meals whose dietary_properties include the given property.

        Args:
            property (str): Dietary property (e.g., 'gluten-free', 'vegan', etc.)

        Returns:
            dict:
                success: True,
                data: List[MealInfo] (can be empty if no matches)
            or
                success: False,
                error: str (reason for error)

        Constraints:
            - property must be a non-empty string.
        """
        if not isinstance(property, str) or not property.strip():
            return { "success": False, "error": "Invalid property value" }

        property = property.strip().lower()
        matched_meals = [
            meal for meal in self.meals.values()
            if any(prop.lower() == property for prop in meal.get("dietary_properties", []))
        ]

        return { "success": True, "data": matched_meals }

    def get_meals_by_allergen(self, allergen: str, present: bool) -> dict:
        """
        Filter meals by the presence or absence of the given allergenic ingredient.
    
        Args:
            allergen (str): The allergen to check in meal allergen_info (e.g. 'nuts', 'gluten').
            present (bool): 
                - If True, return meals containing the allergen.
                - If False, return meals that do NOT contain the allergen.
            
        Returns:
            dict: 
                - success: True, plus 'data': List of MealInfo dicts matching the filter (may be empty).
                - success: False, plus 'error': Reason for query failure (e.g. missing allergen parameter).

        Constraints:
            - allergen string must be provided.
            - allergen_info checks are case-insensitive, split by comma or semicolon if present.
        """
        if not allergen or not isinstance(allergen, str):
            return { "success": False, "error": "Allergen must be specified as a non-empty string." }
    
        allergen_lower = allergen.strip().lower()
        filtered_meals = []
        for meal in self.meals.values():
            # Normalize allergen_info: split by comma, strip whitespace, lower case
            allergen_list = [
                a.strip().lower() for a in meal.get("allergen_info", "").replace(";", ",").split(",") if a.strip()
            ]
            if present:
                if allergen_lower in allergen_list:
                    filtered_meals.append(meal)
            else:
                if allergen_lower not in allergen_list:
                    filtered_meals.append(meal)

        return { "success": True, "data": filtered_meals }

    def get_meal_schedule_by_datetime(self, scheduled_datetime: str) -> dict:
        """
        Retrieve all meal schedule info matching the specified scheduled_datetime.

        Args:
            scheduled_datetime (str): The ISO-format datetime to filter for (e.g., "2024-07-09T12:00").

        Returns:
            dict: {
                "success": True,
                "data": List[MealScheduleInfo]  # All meal schedules at that datetime (may be empty)
            }
        """
        matched_schedules = []
        for meal_id, schedules in self.meal_schedules.items():
            for schedule in schedules:
                if schedule.get("scheduled_datetime") == scheduled_datetime:
                    matched_schedules.append(schedule)

        return { "success": True, "data": matched_schedules }

    def get_meals_available_for_patient_at_datetime(self, patient_id: str, scheduled_datetime: str) -> dict:
        """
        Return a list of meals available for a specific patient at a specified datetime,
        satisfying schedule availability and dietary compatibility constraints.

        Args:
            patient_id (str): Unique identifier for the patient.
            scheduled_datetime (str): Datetime string (ISO format) for the meal.

        Returns:
            dict: {
                "success": True,
                "data": List[MealInfo]  # List of meals matching constraints (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Patient must exist.
            - Only meals scheduled as 'available' for given datetime are considered.
            - Meals must satisfy patient's dietary_restrictions.
        """
        # Validate patient
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient ID does not exist" }
        dietary_restrictions = patient.get("dietary_restrictions", [])
        # Collect compatible, available meals
        compatible_meals = []
        for meal_id, meal in self.meals.items():
            # Check scheduling: is meal available at scheduled_datetime?
            schedules = self.meal_schedules.get(meal_id, [])
            schedule_ok = any(
                sch["scheduled_datetime"] == scheduled_datetime and sch["availability_sta"] == "available"
                for sch in schedules
            )
            if not schedule_ok:
                continue
            # Dietary check: every restriction must be satisfied by meal properties
            meal_props = set(prop.lower() for prop in meal.get("dietary_properties", []))
            restrictions = set(r.lower() for r in dietary_restrictions)
            if not restrictions <= meal_props:
                continue
            # If passed both checks, add meal
            compatible_meals.append(meal)
        return { "success": True, "data": compatible_meals }

    def get_staff_by_role(self, role: str) -> dict:
        """
        List staff members filtered by their role.

        Args:
            role (str): Staff role to match (e.g., 'dietitian', 'nurse', etc.).

        Returns:
            dict: {
                "success": True,
                "data": List[StaffInfo],  # List of matching staff infos, may be empty
            }
            or
            {
                "success": False,
                "error": str  # If input role is invalid (empty)
            }

        Constraints:
            - Input role must be a non-empty string.
            - Returns all staff matching the exact role.
            - Always succeeds (empty list if no matches).
        """
        if not isinstance(role, str) or not role.strip():
            return { "success": False, "error": "Role must be a non-empty string" }

        role_clean = role.strip().lower()
        result = [
            staff_info for staff_info in self.staff.values()
            if staff_info["role"].strip().lower() == role_clean
        ]

        return { "success": True, "data": result }

    def assign_meal_to_patient(self, patient_id: str, meal_id: str, scheduled_datetime: str) -> dict:
        """
        Assign a scheduled, compatible meal to a patient for a specific datetime.

        Args:
            patient_id (str): ID of the patient.
            meal_id (str): ID of the meal.
            scheduled_datetime (str): Datetime string (ISO format) for the meal assignment.

        Returns:
            dict: {
                "success": True,
                "id": str,
                "data": dict
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Patient must exist.
            - Meal must exist.
            - Meal must be available and scheduled for the requested datetime.
            - Meal dietary_properties/allergen_info must be compatible with patient's dietary_restrictions/medical_conditions.
            - Patient should only receive meals compliant with care protocol.
        """
        # Check patient existence
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient does not exist"}

        # Check meal existence
        meal = self.meals.get(meal_id)
        if not meal:
            return {"success": False, "error": "Meal does not exist"}

        # Find the meal schedule record for the requested datetime
        meal_schedules = self.meal_schedules.get(meal_id, [])
        relevant_schedule = [
            ms for ms in meal_schedules
            if ms["scheduled_datetime"] == scheduled_datetime and ms["availability_sta"] == "available"
        ]
        if not relevant_schedule:
            return {"success": False, "error": "Meal is not available at the requested datetime"}

        # Check dietary restriction compatibility
        incompatible = False
        for dr in patient["dietary_restrictions"]:
            if dr.lower() not in [prop.lower() for prop in meal["dietary_properties"]]:
                incompatible = True
                break
        # Further check medical_conditions if desired (for example, if certain medical conditions require exclusion).
        # Let's assume the same check, i.e. dietary_property must cover/restrict what the medical_condition demands:
        for cond in patient["medical_conditions"]:
            if cond.lower() not in [prop.lower() for prop in meal["dietary_properties"]]:
                incompatible = True
                break
        if incompatible:
            return {"success": False, "error": "Meal does not meet patient's dietary or medical restrictions"}

        # Check for allergen conflict (simple logic: allergen_info should not mention patient's restrictions)
        for allergen in patient["dietary_restrictions"]:
            if allergen.lower() in meal["allergen_info"].lower():
                return {"success": False, "error": "Meal contains allergens restricted by patient"}

        # Check for existing assignment for same patient, meal, datetime
        for assignment in self.assignments:
            if (assignment["patient_id"] == patient_id and
                assignment["meal_id"] == meal_id and
                assignment["scheduled_datetime"] == scheduled_datetime):
                return {"success": False, "error": "Meal already assigned to patient for this datetime"}

        # Record assignment
        assignment_id = str(uuid.uuid4())
        assignment_data = {
            "assignment_id": assignment_id,
            "patient_id": patient_id,
            "meal_id": meal_id,
            "scheduled_datetime": scheduled_datetime
        }
        self.assignments.append(assignment_data)

        return {
            "success": True,
            "id": assignment_id,
            "data": assignment_data
        }

    def update_patient_dietary_restrictions(self, patient_id: str, new_dietary_restrictions: List[str]) -> dict:
        """
        Modify dietary restrictions for a patient profile.

        Args:
            patient_id (str): Unique identifier of the patient.
            new_dietary_restrictions (List[str]): Updated list of dietary restriction names.

        Returns:
            dict: 
                - On success: { "success": True, "data": {...} }
                - On error: { "success": False, "error": "Patient not found." }

        Constraints:
            - patient_id must exist in the system.
            - Only updates dietary_restrictions field; other fields are untouched.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found." }
        if not isinstance(new_dietary_restrictions, list) or not all(isinstance(s, str) for s in new_dietary_restrictions):
            return { "success": False, "error": "new_dietary_restrictions must be a list of strings." }
    
        self.patients[patient_id]["dietary_restrictions"] = new_dietary_restrictions
        return { "success": True, "data": self.patients[patient_id] }

    def update_meal_properties(self, meal_id: str, dietary_properties: List[str]) -> dict:
        """
        Update the dietary properties (e.g., 'gluten-free', 'vegan') associated with a specified meal.

        Args:
            meal_id (str): The unique identifier of the meal to update.
            dietary_properties (List[str]): The new list of dietary properties for the meal.

        Returns:
            dict:
                - If successful: { "success": True, "data": {...} }
                - If error: { "success": False, "error": "<reason>" }

        Constraints:
            - The meal must exist.
            - Dietary properties should be a list of strings (basic validation).
            - Allergen info is not handled here.
        """
        if meal_id not in self.meals:
            return { "success": False, "error": f"Meal with id '{meal_id}' does not exist." }

        if not isinstance(dietary_properties, list) or not all(isinstance(prop, str) for prop in dietary_properties):
            return { "success": False, "error": "dietary_properties must be a list of strings." }

        # Update meal's dietary properties
        self.meals[meal_id]["dietary_properties"] = dietary_properties

        return {
            "success": True,
            "data": self.meals[meal_id]
        }

    def update_meal_allergen_info(self, meal_id: str, new_allergen_info: str) -> dict:
        """
        Modifies the allergen information for a specified meal.
    
        Args:
            meal_id (str): The ID of the meal to update.
            new_allergen_info (str): The updated allergen info to set (should be non-empty for food safety compliance).
    
        Returns:
            dict: 
                - On success: { "success": True, "data": {...} }
                - On failure: { "success": False, "error": "reason" }
            
        Constraints:
            - The provided meal_id must exist in the system.
            - Allergen info should be kept up-to-date for compliance.
        """
        if meal_id not in self.meals:
            return { "success": False, "error": "Meal ID does not exist." }
        if not isinstance(new_allergen_info, str) or new_allergen_info.strip() == "":
            return { "success": False, "error": "Allergen info must be a non-empty string." }

        self.meals[meal_id]["allergen_info"] = new_allergen_info.strip()
        return { "success": True, "data": self.meals[meal_id] }

    def update_meal_schedule_availability(self, meal_id: str, scheduled_datetime: str, availability_sta: str) -> dict:
        """
        Set or modify the availability status of a meal at a given scheduled datetime.

        Args:
            meal_id (str): The unique identifier of the meal.
            scheduled_datetime (str): ISO-format string for the scheduled datetime.
            availability_sta (str): The status to set ('available', 'unavailable').

        Returns:
            dict:
                Success: { "success": True, "data": {...} }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - meal_id must exist in meal_schedules.
            - scheduled_datetime must exist for the meal.
            - availability_sta should be 'available' or 'unavailable'.
        """
        # Valid status check (optional, enforce known values)
        if availability_sta not in ('available', 'unavailable'):
            return { "success": False, "error": "Invalid availability status; must be 'available' or 'unavailable'." }

        if meal_id not in self.meal_schedules:
            return { "success": False, "error": "Meal not found in schedule." }

        # Find schedule entry matching datetime
        for schedule in self.meal_schedules[meal_id]:
            if schedule["scheduled_datetime"] == scheduled_datetime:
                schedule["availability_sta"] = availability_sta
                return {
                    "success": True,
                    "data": schedule
                }
        return { "success": False, "error": "Meal schedule not found for specified datetime." }

    def create_meal_schedule(self, meal_id: str, scheduled_datetime: str, availability_sta: str) -> dict:
        """
        Add a new schedule entry for a meal at a specified date and time.

        Args:
            meal_id (str): ID of the meal to be scheduled.
            scheduled_datetime (str): Datetime string (preferably ISO format).
            availability_sta (str): Availability status ('available' or 'unavailable').

        Returns:
            dict:
                success: True, id and data if entry created.
                success: False and error description otherwise.

        Constraints:
            - The meal specified by meal_id must exist.
            - Prevent duplicate scheduling: cannot add two schedules for the same meal with identical datetime.
            - availability_sta must be 'available' or 'unavailable'.
        """
        # Validate meal existence
        if meal_id not in self.meals:
            return { "success": False, "error": "Meal ID does not exist." }

        # Validate availability status
        if availability_sta not in ['available', 'unavailable']:
            return { "success": False, "error": "Invalid availability status." }

        # Initialize schedule list if not present
        if meal_id not in self.meal_schedules:
            self.meal_schedules[meal_id] = []

        # Check for duplicate schedule entry
        for sched in self.meal_schedules[meal_id]:
            if sched['scheduled_datetime'] == scheduled_datetime:
                return { "success": False, "error": "Schedule for this meal already exists at the specified datetime." }

        # Create and add new schedule entry
        schedule_id = str(uuid.uuid4())
        new_schedule: MealScheduleInfo = {
            'schedule_id': schedule_id,
            'meal_id': meal_id,
            'scheduled_datetime': scheduled_datetime,
            'availability_sta': availability_sta
        }
        self.meal_schedules[meal_id].append(new_schedule)

        return { "success": True, "id": schedule_id, "data": new_schedule }

    def remove_meal_schedule(self, meal_id: str, scheduled_datetime: str) -> dict:
        """
        Delete a scheduled meal time entry for a specific meal from the system.

        Args:
            meal_id (str): The unique identifier of the meal.
            scheduled_datetime (str): The ISO format datetime string for the schedule entry to remove.

        Returns:
            dict: On success: { "success": True, "deleted_id": "..." }
                  On failure: { "success": False, "error": "reason for failure" }

        Constraints:
            - Meal_id must exist in the system's schedule records.
            - A scheduled meal entry with the given datetime must exist to be removed.
        """
        # Check meal_id exists in meal_schedules
        if meal_id not in self.meal_schedules:
            return { "success": False, "error": "Meal ID does not exist in schedules." }
    
        # Find and delete the specified scheduled_datetime entry
        schedules = self.meal_schedules[meal_id]
        initial_len = len(schedules)

        # Find the entry to get its id before removing
        deleted_id = None
        for entry in schedules:
            if entry["scheduled_datetime"] == scheduled_datetime:
                deleted_id = entry.get("schedule_id", f"{meal_id}_{scheduled_datetime}")
                break

        # Filter out the schedule targeted for removal
        filtered_schedules = [entry for entry in schedules if entry["scheduled_datetime"] != scheduled_datetime]
    
        if len(filtered_schedules) == initial_len:
            return { "success": False, "error": "Scheduled meal entry not found for provided datetime." }
    
        # Update the schedules; if empty, that's fine.
        self.meal_schedules[meal_id] = filtered_schedules

        return { "success": True, "deleted_id": deleted_id }