from typing import Dict, TypedDict
import uuid
from typing import Optional, Dict



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    role: str  # 'patient' or 'provider'
    authentication_credential: str

class ImageInfo(TypedDict):
    image_id: str
    user_id: str
    consultation_id: str
    file_location: str
    upload_timestamp: str
    body_location: str
    metadata: dict

class ConsultationInfo(TypedDict):
    consultation_id: str
    patient_id: str
    provider_id: str
    start_time: str
    end_time: str
    status: str
    note: str  # 'no' field (used for notes/details)

class TelemedicineDermatologyPlatform:
    def __init__(self, init_config: dict):
        """
        Telemedicine dermatology environment state.
        init_config: External initializer (unused at present).
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Images: {image_id: ImageInfo}
        self.images: Dict[str, ImageInfo] = {}
        # Consultations: {consultation_id: ConsultationInfo}
        self.consultations: Dict[str, ConsultationInfo] = {}

        # Constraints:
        # - Only authenticated users may upload images.
        # - Only patients may initiate new consultations.
        # - Images must be linked to an existing or new consultation.
        # - Image access must comply with privacy and medical data regulations.
        # - Providers can view only consultations assigned to them.

        self.init_config = init_config

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve a user's profile and role using their unique _id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # All user info if found
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if no such _id
            }

        Constraints:
            - The user_id must exist in the platform.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_email(self, email: str) -> dict:
        """
        Look up user identity and role by registered email.

        Args:
            email (str): The registered email address to look up. Search is case-insensitive.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # All info about the matched user
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. "User not found"
            }

        Constraints:
            - Email is assumed unique per user.
            - Case-insensitive search for email.
        """
        email_lower = email.strip().lower()
        for user in self.users.values():
            if user["email"].strip().lower() == email_lower:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_user_authentication(self, user_id: str, provided_credential: str) -> dict:
        """
        Verifies if the given user is authenticated (credential matches stored).

        Args:
            user_id (str): Unique user identifier.
            provided_credential (str): Credential provided by user for authentication.

        Returns:
            dict:
                {
                    "success": True,
                    "data": UserInfo  # User information dictionary
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for authentication failure
                }

        Constraints:
            - User must exist in the system (user_id present)
            - Credential must match user's authentication_credential
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found" }

        if user_info["authentication_credential"] != provided_credential:
            return { "success": False, "error": "Authentication failed: credential mismatch" }

        return { "success": True, "data": user_info }

    def get_user_role(self, user_id: str) -> dict:
        """
        Get the role ('patient' or 'provider') of a user by their ID.

        Args:
            user_id (str): The identifier of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": { "role": str }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - User must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": { "role": user_info["role"] } }

    def list_user_consultations(self, user_id: str) -> dict:
        """
        List all consultations where the specified user is a participant,
        either as a patient or provider.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ConsultationInfo],  # Consultations where user is patient or provider
            }
            or
            {
                "success": False,
                "error": str  # 'User not found' if invalid user_id
            }

        Constraints:
            - user_id must exist in platform users.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        consultations = [
            consultation for consultation in self.consultations.values()
            if consultation.get("patient_id") == user_id or consultation.get("provider_id") == user_id
        ]    

        return {
            "success": True,
            "data": consultations
        }

    def get_consultation_by_id(self, consultation_id: str) -> dict:
        """
        Retrieve the full details for a specific consultation session.

        Args:
            consultation_id (str): Unique identifier for the consultation.

        Returns:
            dict: 
                - On success: {'success': True, 'data': ConsultationInfo}
                - On failure: {'success': False, 'error': 'Consultation not found'}

        Constraints:
            - Consultation with the provided ID must exist.
        """
        consultation = self.consultations.get(consultation_id)
        if not consultation:
            return {"success": False, "error": "Consultation not found"}
        return {"success": True, "data": consultation}

    def list_provider_consultations(self, provider_id: str) -> dict:
        """
        List all consultations assigned to the specified provider.

        Args:
            provider_id (str): Unique user ID of provider.

        Returns:
            dict: {
                "success": True,
                "data": List[ConsultationInfo],  # All consultations where provider_id matches (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (provider does not exist or is not a provider)
            }

        Constraints:
            - provider_id must exist in self.users and must have role 'provider'.
        """
        provider = self.users.get(provider_id)
        if not provider:
            return {"success": False, "error": "Provider ID does not exist"}
        if provider["role"] != "provider":
            return {"success": False, "error": "User is not a provider"}

        consultations = [
            consult for consult in self.consultations.values()
            if consult["provider_id"] == provider_id
        ]

        return {"success": True, "data": consultations}

    def list_images_for_consultation(self, consultation_id: str) -> dict:
        """
        Retrieve all image files and associated metadata linked to a specific consultation.

        Args:
            consultation_id (str): Unique identifier for the target consultation.

        Returns:
            dict: {
                "success": True,
                "data": List[ImageInfo],  # may be empty if no images are linked
            }
            or
            {
                "success": False,
                "error": str  # error message, e.g. 'Consultation does not exist'
            }

        Constraints:
            - consultation_id must exist in the system.
            - No explicit privacy rules enforced in this query.
        """
        if consultation_id not in self.consultations:
            return { "success": False, "error": "Consultation does not exist" }

        images = [
            image_info for image_info in self.images.values()
            if image_info["consultation_id"] == consultation_id
        ]

        return { "success": True, "data": images }

    def get_image_metadata(self, image_id: str) -> dict:
        """
        Retrieve metadata for the specified image.

        Args:
            image_id (str): Unique identifier for the image.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "image_id": str,
                    "user_id": str,
                    "consultation_id": str,
                    "file_location": str,
                    "upload_timestamp": str,
                    "body_location": str,
                    "metadata": dict,
                }
            }
            or
            {
                "success": False,
                "error": "Image not found"
            }

        Constraints:
            - The image must exist in the platform's records.
            - No privacy/access checks performed in this method (for metadata only).
        """
        image_info = self.images.get(image_id)
        if not image_info:
            return { "success": False, "error": "Image not found" }

        return { "success": True, "data": {
            "image_id": image_info["image_id"],
            "user_id": image_info["user_id"],
            "consultation_id": image_info["consultation_id"],
            "file_location": image_info["file_location"],
            "upload_timestamp": image_info["upload_timestamp"],
            "body_location": image_info["body_location"],
            "metadata": image_info["metadata"],
        }}

    def can_user_access_image(self, user_id: str, image_id: str) -> dict:
        """
        Determine if a given user is permitted to access/view an image based on privacy and medical data rules.

        Args:
            user_id (str): The ID of the user requesting image access.
            image_id (str): The ID of the image to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if access is permitted, False otherwise.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user or image not found)
            }

        Constraints:
            - Providers can view only consultations assigned to them.
            - Images must comply with medical privacy (only patient and assigned provider may view).
        """
        # Validate user exists
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }

        # Validate image exists
        image_info = self.images.get(image_id)
        if image_info is None:
            return { "success": False, "error": "Image not found" }

        consultation_id = image_info.get("consultation_id")
        consultation_info = self.consultations.get(consultation_id)
        if consultation_info is None:
            return { "success": False, "error": "Consultation not found for image" }

        # Access is permitted if:
        # - user is the patient in the consultation
        # - user is the provider assigned to the consultation
        if user_id == consultation_info.get("patient_id") or user_id == consultation_info.get("provider_id"):
            return { "success": True, "data": True }
        else:
            return { "success": True, "data": False }

    def create_consultation(
        self, 
        patient_id: str, 
        provider_id: str, 
        start_time: str, 
        note: str = ""
    ) -> dict:
        """
        Initiate a new consultation (only allowed for users with role 'patient').

        Args:
            patient_id (str): User ID of the patient initiating the consultation.
            provider_id (str): User ID of the provider (must exist and have 'provider' role).
            start_time (str): Start time for the consultation (ISO format or string).
            note (str): Optional note for the consultation.

        Returns:
            dict:
                success (bool): True if creation succeeded, False otherwise.
                message (str): Success description if succeeded.
                error (str): Error reason if failed.

        Constraints:
            - patient_id and provider_id must refer to existing users.
            - Only patients can initiate (user[patient_id] must have role 'patient').
            - provider_id must have role 'provider'.
        """
        # Check patient exists
        patient = self.users.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient user does not exist." }
        if patient.get('role') != "patient":
            return { "success": False, "error": "Only users with role 'patient' may initiate a consultation." }
    
        # Check provider exists
        provider = self.users.get(provider_id)
        if not provider:
            return { "success": False, "error": "Provider user does not exist." }
        if provider.get('role') != "provider":
            return { "success": False, "error": "Consultation must be assigned to a user with role 'provider'." }
    
        # Generate unique consultation_id
        consultation_id = str(uuid.uuid4())

        # Create new consultation record
        new_consultation = {
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "start_time": start_time,
            "end_time": "",
            "status": "active",  # Initial status
            "note": note or "",
        }
        self.consultations[consultation_id] = new_consultation

        return { 
            "success": True, 
            "message": f"Consultation created with id {consultation_id}" 
        }


    def upload_image_to_consultation(
        self,
        user_id: str,
        authentication_credential: str,
        file_location: str,
        upload_timestamp: str,
        body_location: str,
        metadata: Dict,
        consultation_id: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> dict:
        """
        Upload a new dermatology analysis image, linking to an existing or new consultation.

        Args:
            user_id (str): The ID of the user uploading the image.
            authentication_credential (str): The credential/token for user authentication.
            file_location (str): The location/path of the uploaded image file.
            upload_timestamp (str): Timestamp marking when upload occurs.
            body_location (str): Human body location relevant to the image.
            metadata (dict): Any additional metadata for the image.
            consultation_id (Optional[str]): Existing consultation to link to, or None to create new.
            provider_id (Optional[str]): Required only when creating new consultation.

        Returns:
            dict: {
                "success": True,
                "message": "Image uploaded and linked to consultation"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only authenticated users may upload images.
            - If creating new consultation, only patients may initiate; must provide provider_id.
            - Images must be linked to an existing or new consultation.
        """
        # Authenticate user
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        if user["authentication_credential"] != authentication_credential:
            return {"success": False, "error": "Authentication failed"}

        # Determine consultation to link
        actual_consultation_id = consultation_id
        if consultation_id:
            consultation = self.consultations.get(consultation_id)
            if not consultation:
                return {"success": False, "error": "Consultation not found"}
        else:
            # Consultation creation is allowed only for patients
            if user["role"] != "patient":
                return {"success": False, "error": "Only patients may initiate a new consultation"}
            if not provider_id:
                return {"success": False, "error": "Must specify provider_id to create new consultation"}

            actual_consultation_id = str(uuid.uuid4())
            # Minimal consultation record (start_time assumed to be upload_timestamp)
            self.consultations[actual_consultation_id] = {
                "consultation_id": actual_consultation_id,
                "patient_id": user_id,
                "provider_id": provider_id,
                "start_time": upload_timestamp,
                "end_time": "",
                "status": "active",
                "note": "",
            }

        # Generate unique image_id
        image_id = str(uuid.uuid4())
        self.images[image_id] = {
            "image_id": image_id,
            "user_id": user_id,
            "consultation_id": actual_consultation_id,
            "file_location": file_location,
            "upload_timestamp": upload_timestamp,
            "body_location": body_location,
            "metadata": metadata,
        }

        return {
            "success": True,
            "message": f"Image uploaded and linked to consultation {actual_consultation_id}"
        }

    def update_consultation_note(self, consultation_id: str, note: str) -> dict:
        """
        Add or update the notes/details associated with a consultation record.

        Args:
            consultation_id (str): The unique identifier of the consultation to update.
            note (str): The textual note to set or modify.

        Returns:
            dict: {
                "success": True,
                "message": "Consultation note updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. consultation not found or invalid note
            }

        Constraints:
            - Consultation ID must correspond to an existing consultation.
            - Note must be a string.
        """
        if consultation_id not in self.consultations:
            return { "success": False, "error": "Consultation not found." }
        if not isinstance(note, str):
            return { "success": False, "error": "Note must be a string." }

        self.consultations[consultation_id]["note"] = note
        return { "success": True, "message": "Consultation note updated successfully." }

    def update_image_metadata(self, image_id: str, metadata_updates: dict) -> dict:
        """
        Modify metadata fields of a stored image (e.g., body_location).

        Args:
            image_id (str): The unique identifier for the image to update.
            metadata_updates (dict): Dictionary of metadata keys and their new values. For body_location, pass as a key.

        Returns:
            dict:
                - On success: { "success": True, "message": "Image metadata updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Image with the specified image_id must exist.
            - Only metadata fields and body_location can be updated.
            - No authentication/user access logic is enforced in this method.
        """
        image_info = self.images.get(image_id)
        if not image_info:
            return { "success": False, "error": "Image not found." }

        # Update body_location specifically if present in metadata_updates
        if "body_location" in metadata_updates:
            image_info["body_location"] = metadata_updates["body_location"]

        # Update other metadata keys
        if isinstance(image_info.get("metadata"), dict):
            for key, value in metadata_updates.items():
                if key != "body_location":
                    image_info["metadata"][key] = value
        else:
            # Defensive: metadata field missing or not a dict
            image_info["metadata"] = {k: v for k, v in metadata_updates.items() if k != "body_location"}

        return { "success": True, "message": "Image metadata updated." }

    def restrict_image_access(self, image_id: str, restrictions: dict) -> dict:
        """
        Apply or modify access restrictions on a given image to comply with privacy regulations.

        Args:
            image_id (str): The identifier of the image to restrict.
            restrictions (dict): Restriction details, e.g., {'restricted': True} or other access-control fields.

        Returns:
            dict: {
                "success": True,
                "message": "Access restrictions updated for image <image_id>"
            }
            OR
            {
                "success": False,
                "error": "Image not found or invalid restriction input"
            }

        Constraints:
            - Image must exist in platform.
            - Restrictions argument must be a dictionary.
            - Only restriction (access control) fields in metadata are modified; other metadata remains intact.
        """
        image_info = self.images.get(image_id)
        if not image_info:
            return { "success": False, "error": "Image not found" }
        if not isinstance(restrictions, dict):
            return { "success": False, "error": "Invalid restriction input; must be a dictionary" }

        metadata = image_info.get("metadata", {})
        # Update restrictions: overwrite any existing access control fields with those supplied
        metadata.update(restrictions)
        image_info["metadata"] = metadata
        self.images[image_id] = image_info  # Save back the changes

        return { "success": True, "message": f"Access restrictions updated for image {image_id}" }

    def remove_image_from_consultation(self, image_id: str, user_id: str) -> dict:
        """
        Delete an image from a consultation for privacy, error correction, or compliance reasons.

        Args:
            image_id (str): Unique identifier for the image to be removed.
            user_id (str): The user attempting the removal (for authentication/authorization).

        Returns:
            dict: {
                "success": True,
                "message": f"Image {image_id} removed from consultation."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only the image uploader, assigned provider in the consultation, or compliance/admin may remove the image.
            - The image must exist and be linked to a consultation.
            - Image access must comply with privacy/medical regulations.
        """
        if image_id not in self.images:
            return { "success": False, "error": "Image does not exist." }

        image_info = self.images[image_id]
        consultation_id = image_info.get("consultation_id")
        if not consultation_id or consultation_id not in self.consultations:
            return { "success": False, "error": "Image not linked to a valid consultation." }

        # Check user exists
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User does not exist." }

        # Authorization check:
        # 1. Image uploader
        # 2. Provider assigned in consultation
        # 3. Or compliance/admin (role == 'admin' assumed for extensibility, if any user has this)
        allowed = (
            user_id == image_info["user_id"] or
            user_id == self.consultations[consultation_id]["provider_id"] or
            user_info.get("role") == "admin"
        )
        if not allowed:
            return { "success": False, "error": "User not authorized to remove image." }

        # Remove image from records
        del self.images[image_id]
        # No need to update consultation unless there is a specific image list in consultation info (here there isn't)

        return { "success": True, "message": f"Image {image_id} removed from consultation." }
