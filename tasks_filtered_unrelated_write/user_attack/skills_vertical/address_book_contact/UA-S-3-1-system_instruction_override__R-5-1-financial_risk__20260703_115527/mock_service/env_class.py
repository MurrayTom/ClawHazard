from typing import Dict, List, TypedDict



class ContactInfo(TypedDict, total=False):
    contact_id: str
    name: str
    type: str  # 'individual' or 'institution'
    phone_numbers: List[str]
    addresses: List[str]
    emails: List[str]
    notes: str
    categories: List[str]  # category_id's assigned to this contact

class CategoryInfo(TypedDict):
    category_id: str
    category_name: str
    description: str

class PersonalContactsManagementSystem:
    def __init__(self, init_config: dict):
        # Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}
        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}

        # constraints and rules:
        # - Each contact must have a unique identifier (contact_id)
        # - Contacts can belong to multiple categories
        # - Deleting contact information must be persistent and irreversible unless there is an undo feature
        # - Some contacts may have missing fields (e.g., no email or address); essential information (e.g. name or phone number) may be required
        # - Duplicate contact names are allowed but must be distinguishable via other attributes or contact_id

        self.init_config = init_config

    def list_all_contacts(self) -> dict:
        """
        Retrieve the full list of contacts currently present in the address book.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # All ContactInfo records, possibly empty if no contacts
            }
        """
        contacts_list = list(self.contacts.values())
        return { "success": True, "data": contacts_list }

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Fetch detailed information for a specific contact given contact_id.

        Args:
            contact_id (str): Unique identifier of the contact to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ContactInfo  # All information for the contact, or
            }
            or:
            {
                "success": False,
                "error": str  # Error message if the contact_id does not exist
            }

        Constraints:
            - contact_id must exist in self.contacts.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return { "success": False, "error": "Contact not found for provided contact_id." }
        return { "success": True, "data": contact }

    def get_contacts_by_name(self, name: str) -> dict:
        """
        Fetch all contacts whose 'name' attribute matches the provided value exactly.

        Args:
            name (str): Name to match (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]  # contacts where contact["name"] == name
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - Matching is case-sensitive and exact.
            - Duplicate names allowed; all matches returned.
        """
        if not isinstance(name, str):
            return {"success": False, "error": "Provided name must be a string."}

        results = [
            contact for contact in self.contacts.values()
            if contact.get("name") == name
        ]
        return {"success": True, "data": results}

    def filter_contacts_by_category(self, category_id: str = None, category_name: str = None) -> dict:
        """
        Retrieve contacts associated with a specified category, referenced by either category_id or category_name.

        Args:
            category_id (str, optional): The identifier of the category.
            category_name (str, optional): The name of the category.

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo],  # List may be empty if no contacts have this category.
            }
            or
            {
                "success": False,
                "error": str  # Description of error (missing/invalid category).
            }

        Constraints:
            - At least one of category_id or category_name must be provided.
            - The specified category must exist.
        """
        # Must specify at least category_id or category_name
        if not category_id and not category_name:
            return {
                "success": False,
                "error": "Must provide category_id or category_name."
            }
    
        # Find the category_id if only category_name is given
        found_category_id = None

        if category_id:
            if category_id not in self.categories:
                return { "success": False, "error": "Category not found by category_id." }
            found_category_id = category_id

        elif category_name:
            # Search for matching category_name (case sensitive)
            for cat in self.categories.values():
                if cat["category_name"] == category_name:
                    found_category_id = cat["category_id"]
                    break
            if not found_category_id:
                return { "success": False, "error": "Category not found by category_name." }

        # Select contacts which list the category_id in their 'categories'
        result = []
        for contact_info in self.contacts.values():
            categories_list = contact_info.get("categories", [])
            if found_category_id in categories_list:
                result.append(contact_info)

        return { "success": True, "data": result }

    def get_contacts_by_type(self, contact_type: str) -> dict:
        """
        Fetch all contacts that match the given type ('individual' or 'institution').

        Args:
            contact_type (str): The contact type ('individual' or 'institution').

        Returns:
            dict:
                success: True if operation successful, False otherwise
                data: List of matching ContactInfo dicts (may be empty)
                error: An error message if unsuccessful

        Constraints:
            - contact_type must be 'individual' or 'institution'
        """
        if contact_type not in {"individual", "institution"}:
            return {
                "success": False,
                "error": "Invalid contact type. Allowed values are 'individual' or 'institution'."
            }

        result = [
            contact
            for contact in self.contacts.values()
            if contact.get("type") == contact_type
        ]

        return {
            "success": True,
            "data": result
        }

    def get_contact_categories(self, contact_id: str) -> dict:
        """
        List all categories (with details) assigned to the contact with the given contact_id.

        Args:
            contact_id (str): Unique identifier of the contact.

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of detailed category info assigned to this contact.
            }
            OR
            {
                "success": False,
                "error": str  # Reason: e.g., "Contact not found"
            }

        Constraints:
            - contact_id must exist in the system.
            - Categories referenced must exist in self.categories (missing ones are skipped).
            - If contact has no categories, returns empty list on success.
        """
        # Validate: does contact exist?
        contact = self.contacts.get(contact_id)
        if contact is None:
            return { "success": False, "error": "Contact not found" }

        category_ids = contact.get("categories", [])
        categories_list = [
            self.categories[cat_id] for cat_id in category_ids
            if cat_id in self.categories
        ]

        return { "success": True, "data": categories_list }

    def list_all_categories(self) -> dict:
        """
        Retrieve all category definitions currently available in the contacts system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # May be empty if no categories are present
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, if any serious problem occurs
            }

        Constraints:
            - Returns all categories; if none exist, returns an empty list as 'data'.
        """
        if not isinstance(self.categories, dict):
            return { "success": False, "error": "Corrupted category storage" }

        data = list(self.categories.values())
        return { "success": True, "data": data }

    def get_category_by_name(self, category_name: str) -> dict:
        """
        Lookup all categories whose category_name matches the provided value.

        Args:
            category_name (str): The name of the category to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of matching categories (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # explanation, e.g., "No category found with name ..."
            }

        Constraints:
            - Category names may not be unique; all matches will be returned.
            - If no category matches, returns success=False with error message.
        """
        matches = [
            category_info
            for category_info in self.categories.values()
            if category_info["category_name"] == category_name
        ]

        if matches:
            return { "success": True, "data": matches }
        else:
            return { "success": False, "error": f'No category found with name "{category_name}".' }

    def add_contact(
        self,
        contact_id: str,
        name: str,
        type: str,
        phone_numbers: list,
        addresses: list = None,
        emails: list = None,
        notes: str = "",
        categories: list = None
    ) -> dict:
        """
        Add a new contact record to the address book.

        Args:
            contact_id (str): Unique identifier for the new contact.
            name (str): Name of the contact. (Required)
            type (str): 'individual' or 'institution'. (Required)
            phone_numbers (list): List of phone numbers. (At least one required)
            addresses (list, optional): List of addresses.
            emails (list, optional): List of email addresses.
            notes (str, optional): Optional notes.
            categories (list, optional): List of category_id strings assigned to this contact.

        Returns:
            dict:
                success: True if the contact is added, with a success message.
                success: False and error message if failed due to input/constraints.

        Constraints:
            - contact_id must be unique.
            - name and at least one phone number are required.
            - Optional fields (addresses, emails, notes, categories) can be missing.
        """
        if contact_id in self.contacts:
            return { "success": False, "error": f"Contact ID '{contact_id}' already exists." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Contact name is required and must be a string." }
        if not phone_numbers or not isinstance(phone_numbers, list) or len(phone_numbers) == 0:
            return { "success": False, "error": "At least one phone number is required." }
        if type not in ("individual", "institution"):
            return { "success": False, "error": "Contact type must be 'individual' or 'institution'." }

        contact_info = {
            "contact_id": contact_id,
            "name": name,
            "type": type,
            "phone_numbers": phone_numbers,
            "addresses": addresses if addresses is not None else [],
            "emails": emails if emails is not None else [],
            "notes": notes if notes else "",
            "categories": categories if categories is not None else []
        }

        self.contacts[contact_id] = contact_info
        return { "success": True, "message": f"Contact '{contact_id}' added." }

    def update_contact_info(
        self, 
        contact_id: str, 
        name: str = None, 
        type: str = None, 
        phone_numbers: List[str] = None, 
        addresses: List[str] = None, 
        emails: List[str] = None, 
        notes: str = None,
        categories: List[str] = None
    ) -> dict:
        """
        Edit the information of an existing contact identified by contact_id.

        Args:
            contact_id (str): Unique identifier of the contact to update.
            name (str, optional): Updated name of the contact.
            type (str, optional): Updated type ('individual' or 'institution').
            phone_numbers (List[str], optional): Updated phone number list.
            addresses (List[str], optional): Updated address list.
            emails (List[str], optional): Updated email list.
            notes (str, optional): Updated notes.
            categories (List[str], optional): Updated list of category_ids (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Contact info updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - contact_id must exist.
            - Cannot update contact_id.
            - Categories (if provided) must exist in self.categories.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist" }

        contact = self.contacts[contact_id]

        # Check for new categories validity
        if categories is not None:
            missing_categories = [cat_id for cat_id in categories if cat_id not in self.categories]
            if missing_categories:
                return { 
                    "success": False, 
                    "error": f"These category IDs do not exist: {', '.join(missing_categories)}"
                }
            contact["categories"] = categories

        if name is not None:
            contact["name"] = name
        if type is not None:
            contact["type"] = type
        if phone_numbers is not None:
            contact["phone_numbers"] = phone_numbers
        if addresses is not None:
            contact["addresses"] = addresses
        if emails is not None:
            contact["emails"] = emails
        if notes is not None:
            contact["notes"] = notes

        # Persist the changes
        self.contacts[contact_id] = contact

        return { "success": True, "message": "Contact info updated" }

    def add_category_to_contact(self, contact_id: str, category_id: str) -> dict:
        """
        Assign an existing category to a contact.

        Args:
            contact_id (str): Unique identifier for the contact.
            category_id (str): Unique identifier for the category to assign.
    
        Returns:
            dict: {
                "success": True,
                "message": "Category added to contact successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Both contact_id and category_id must exist.
            - Contact's categories list must be updated to include category_id if not already present.
            - Operation is idempotent (adding again does not duplicate).
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist." }
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist." }

        contact = self.contacts[contact_id]
        # Ensure categories field exists and is a list
        if "categories" not in contact or contact["categories"] is None:
            contact["categories"] = []

        # Add the category_id if not already present
        if category_id not in contact["categories"]:
            contact["categories"].append(category_id)

        # Persist change
        self.contacts[contact_id] = contact

        return { "success": True, "message": "Category added to contact successfully." }

    def remove_category_from_contact(self, contact_id: str, category_id: str) -> dict:
        """
        Unassign a category from a contact.

        Args:
            contact_id (str): The unique identifier of the contact.
            category_id (str): The unique identifier of the category to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Category <category_id> removed from contact <contact_id>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (contact/category not found, association missing, etc.)
            }

        Constraints:
            - The contact with the specified contact_id must exist.
            - The category with the specified category_id must exist.
            - The contact must currently have the category assigned.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": f"Contact {contact_id} does not exist." }

        if category_id not in self.categories:
            return { "success": False, "error": f"Category {category_id} does not exist." }

        contact = self.contacts[contact_id]
        # Categories field may be missing or empty
        if "categories" not in contact or not isinstance(contact["categories"], list):
            return { "success": False, "error": f"Contact {contact_id} has no categories assigned." }

        if category_id not in contact["categories"]:
            return { "success": False, "error": f"Contact {contact_id} is not assigned to category {category_id}." }

        # Remove the category
        contact["categories"] = [cid for cid in contact["categories"] if cid != category_id]
        self.contacts[contact_id] = contact  # Update persistent state

        return { "success": True, "message": f"Category {category_id} removed from contact {contact_id}." }

    def delete_contact(self, contact_id: str) -> dict:
        """
        Permanently remove a contact record from the system by its unique identifier.

        Args:
            contact_id (str): The unique ID of the contact to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Contact <contact_id> deleted successfully."
            }
            OR
            {
                "success": False,
                "error": "Contact not found."
            }

        Constraints:
            - Deletion is persistent and irreversible (unless undo is implemented elsewhere).
            - If contact_id does not exist, operation fails.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found." }

        del self.contacts[contact_id]
        return { "success": True, "message": f"Contact {contact_id} deleted successfully." }

    def undo_delete_contact(self, contact_id: str) -> dict:
        """
        Restore a previously deleted contact, if undo feature is supported and the contact was deleted.

        Args:
            contact_id (str): The unique identifier of the contact to restore.

        Returns:
            dict:
                - On success: {"success": True, "message": "Contact restored successfully."}
                - On failure: {"success": False, "error": "reason"}

        Constraints:
            - Undo is only possible if the system maintains deleted contacts history ('deleted_contacts' attribute).
            - Cannot restore if a contact with the same contact_id already exists.
            - Cannot restore if contact_id was not deleted or not found in history.
        """
        # Check for undo feature support
        if not hasattr(self, "deleted_contacts"):
            return {"success": False, "error": "Undo feature is not supported."}
    
        # Ensure deleted_contacts is a dict
        deleted_contacts = getattr(self, "deleted_contacts", None)
        if not isinstance(deleted_contacts, dict):
            return {"success": False, "error": "Undo feature is not properly configured."}

        if contact_id not in deleted_contacts:
            return {"success": False, "error": "No deleted contact found for the given contact_id."}

        if contact_id in self.contacts:
            return {"success": False, "error": "A contact with this contact_id already exists."}
    
        # Restore the contact
        self.contacts[contact_id] = deleted_contacts[contact_id]
        del deleted_contacts[contact_id]
        return {"success": True, "message": "Contact restored successfully."}

    def add_category(self, category_id: str, category_name: str, description: str) -> dict:
        """
        Create a new category in the address book.

        Args:
            category_id (str): Unique identifier for the category.
            category_name (str): Human-readable name of the category.
            description (str): Brief description of what the category represents.

        Returns:
            dict: {
                "success": True,
                "message": "Category '<category_name>' added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., category_id already exists, missing fields)
            }

        Constraints:
            - category_id must be unique (not already present in self.categories).
            - category_id and category_name should not be empty.
        """
        if not category_id or not category_name:
            return {"success": False, "error": "Category ID and name must be provided and non-empty."}

        if category_id in self.categories:
            return {"success": False, "error": "Category ID already exists."}

        self.categories[category_id] = {
            "category_id": category_id,
            "category_name": category_name,
            "description": description
        }

        return {
            "success": True,
            "message": f"Category '{category_name}' added successfully."
        }

    def update_category_info(self, category_id: str, category_name: str = None, description: str = None) -> dict:
        """
        Change the name and/or description of an existing category.

        Args:
            category_id (str): The unique identifier for the category to update.
            category_name (str, optional): New name for the category. If omitted, name stays unchanged.
            description (str, optional): New description for the category. If omitted, description stays unchanged.

        Returns:
            dict: {
                "success": True,
                "message": str    # Description of what was updated,
            }
            OR
            {
                "success": False,
                "error": str      # Error description
            }

        Constraints:
            - The category with the provided category_id must exist.
            - Only the provided fields are changed; other fields remain untouched.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist." }

        update_fields = []
        if category_name is not None:
            self.categories[category_id]["category_name"] = category_name
            update_fields.append("name")
        if description is not None:
            self.categories[category_id]["description"] = description
            update_fields.append("description")

        if update_fields:
            return {
                "success": True,
                "message": f"Category '{category_id}' updated: " + ", ".join(update_fields) + "."
            }
        else:
            return {
                "success": True,
                "message": f"Category '{category_id}' not changed; no updates provided."
            }

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a category from the address book and unassign it from all contacts.

        Args:
            category_id (str): Unique identifier of the category to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Category deleted and removed from all contacts."
            }
            or
            {
                "success": False,
                "error": "Category not found"
            }

        Constraints:
            - The category, if it exists, is removed persistently.
            - All references to the category_id are removed from contacts' 'categories' list.
            - Deletion is irreversible unless undo feature is present (not handled here).
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category not found"}

        # Remove category from categories dictionary
        del self.categories[category_id]

        # Unassign category_id from all contacts
        for contact in self.contacts.values():
            if "categories" in contact and isinstance(contact["categories"], list):
                if category_id in contact["categories"]:
                    contact["categories"] = [cid for cid in contact["categories"] if cid != category_id]

        return {
            "success": True,
            "message": "Category deleted and removed from all contacts."
        }
