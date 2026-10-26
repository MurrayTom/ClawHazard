from typing import Dict, TypedDict



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    account_status: str

class ProfessionalInfo(TypedDict):
    professional_id: str
    name: str
    specialty: str
    profile_info: str

class ReviewInfo(TypedDict):
    view_id: str
    user_id: str
    professional_id: str
    rating: float
    review_text: str
    submission_date: str
    moderation_status: str

class OnlineProfessionalReviewPlatform:
    def __init__(self, init_config: dict):
        """
        Online professional review platform environment.
        Attributes model users, professionals, and reviews.
        """
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Professionals: {professional_id: ProfessionalInfo}
        self.professionals: Dict[str, ProfessionalInfo] = {}
        # Reviews: {view_id: ReviewInfo}
        self.reviews: Dict[str, ReviewInfo] = {}

        # Constraints:
        # - Only registered users can submit reviews
        # - Each review must be linked to a valid professional and user
        # - Each review must have a moderation status (pending, approved, rejected)
        # - Users can submit only one review per professional
        # - Aggregated ratings update for professionals when new approved reviews are submitted

        self.init_config = init_config

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user info by username.

        Args:
            username (str): The username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user information, if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user not found)
            }

        Constraints:
            - The username must exist within the users database.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return { "success": True, "data": user_info }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user information by user _id.

        Args:
            _id (str): Unique identifier of the user.

        Returns:
            dict: 
                - On success: {"success": True, "data": UserInfo}
                - On failure: {"success": False, "error": "User not found"}

        Constraints:
            - The user _id must exist in the platform.
        """
        user = self.users.get(_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def list_all_users(self) -> dict:
        """
        Return a list of all registered users in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all users' info (may be empty if no users)
            }
        Constraints:
            - None (simply lists all user records; returns empty list if none exist)
        """
        return { "success": True, "data": list(self.users.values()) }

    def get_professional_by_name(self, name: str) -> dict:
        """
        Retrieve professional info by their name.

        Args:
            name (str): The name of the professional.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, str or None]]
                    # Each dict: {
                    #   "professional_id": str,
                    #   "name": str,
                    #   "specialty": str
                    # }
                }
                OR
                {
                "success": False,
                "error": "Professional not found"
            }

        Constraints:
            - Only returns registered professionals.
            - If multiple professionals share the same name, all matching are returned.
        """
        matches = []
        for prof in self.professionals.values():
            if prof["name"] == name:
                matches.append({
                    "professional_id": prof["professional_id"],
                    "name": prof["name"],
                    "specialty": prof["specialty"]
                })
        if not matches:
            return { "success": False, "error": "Professional not found" }
        return { "success": True, "data": matches }

    def get_professional_by_id(self, professional_id: str) -> dict:
        """
        Retrieve professional information by their professional_id.

        Args:
            professional_id (str): The unique identifier for the professional.

        Returns:
            dict: {
                "success": True,
                "data": ProfessionalInfo  # Professional's profile information
            }
            or
            {
                "success": False,
                "error": str  # Error description if the professional does not exist
            }
    
        Constraints:
            - The professional_id must exist in the platform.
        """
        professional = self.professionals.get(professional_id)
        if professional is None:
            return {"success": False, "error": "Professional not found"}

        return {"success": True, "data": professional}

    def list_all_professionals(self) -> dict:
        """
        Returns a list of all professionals registered on the platform.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProfessionalInfo]  # May be empty if no professionals exist
                }
        """
        data = list(self.professionals.values())
        return { "success": True, "data": data }

    def get_reviews_by_user(self, user_id: str) -> dict:
        """
        Retrieve all reviews submitted by the specified user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[ReviewInfo],  # possibly an empty list
                }
                - On error: {
                    "success": False,
                    "error": str  # explanation of failure, e.g. user not found
                }

        Constraints:
            - user_id must exist in the platform (registered user).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        result = [
            review_info for review_info in self.reviews.values()
            if review_info["user_id"] == user_id
        ]

        return {"success": True, "data": result}

    def get_reviews_for_professional(self, professional_id: str) -> dict:
        """
        Retrieve all reviews (with full metadata) linked to the specified professional.

        Args:
            professional_id (str): Unique identifier of the professional.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],  # list of reviews for the professional (empty if none)
            }
            OR
            {
                "success": False,
                "error": str  # Reason why retrieval failed (e.g. professional does not exist)
            }

        Constraints:
            - professional_id must exist in the platform.
        """
        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional does not exist" }

        reviews_for_professional = [
            review for review in self.reviews.values()
            if review["professional_id"] == professional_id
        ]

        return { "success": True, "data": reviews_for_professional }

    def get_review_by_user_and_professional(self, user_id: str, professional_id: str) -> dict:
        """
        Retrieve the review submitted by a specific user for a specific professional, if it exists.

        Args:
            user_id (str): The ID of the user.
            professional_id (str): The ID of the professional.

        Returns:
            dict: {
                "success": True,
                "data": ReviewInfo or None  # If review exists, full info; else None
            }
            or
            {
                "success": False,
                "error": str  # Reason (user or professional does not exist)
            }

        Constraints:
            - Both user_id and professional_id must exist.
            - Only one review per user per professional exists.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional does not exist" }

        for review in self.reviews.values():
            if review["user_id"] == user_id and review["professional_id"] == professional_id:
                return { "success": True, "data": review }

        return { "success": True, "data": None }

    def get_review_by_id(self, view_id: str) -> dict:
        """
        Get the details of a review (ReviewInfo) by its unique view_id.

        Args:
            view_id (str): The unique identifier for the review.

        Returns:
            dict: {
                "success": True,
                "data": ReviewInfo  # The full dict for the review item
            }
            or
            {
                "success": False,
                "error": str  # Explanation if not found
            }

        Constraints:
            - The view_id must exist in the review database.
        """
        review = self.reviews.get(view_id)
        if review is None:
            return { "success": False, "error": "Review not found" }

        return { "success": True, "data": review }

    def get_review_moderation_status(self, view_id: str) -> dict:
        """
        Retrieve the moderation status of a specific review.

        Args:
            view_id (str): The unique identifier of the review.

        Returns:
            dict: 
              On success:
                  {
                    "success": True,
                    "data": str,  # Moderation status value ("pending", "approved", "rejected")
                  }
              On failure:
                  {
                    "success": False,
                    "error": str  # Reason for failure, e.g., review not found
                  }

        Constraints:
            - The specified review id must exist in the environment.
        """
        review = self.reviews.get(view_id)
        if not review:
            return { "success": False, "error": "Review not found" }

        return { "success": True, "data": review["moderation_status"] }

    def get_aggregated_rating_for_professional(self, professional_id: str) -> dict:
        """
        Get the average (aggregated) rating for a given professional.

        Args:
            professional_id (str): The unique ID of the professional.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "professional_id": str,
                    "average_rating": float or None,  # None if no approved reviews
                    "num_reviews": int                # Number of approved reviews
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Professional not found"
            }

        Constraints:
            - Only 'approved' reviews are considered.
            - Professional must exist.
        """

        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional not found" }

        approved_reviews = [
            review for review in self.reviews.values()
            if review["professional_id"] == professional_id and review["moderation_status"] == "approved"
        ]
        num_reviews = len(approved_reviews)
        if num_reviews == 0:
            avg_rating = None
        else:
            avg_rating = sum(review["rating"] for review in approved_reviews) / num_reviews

        return {
            "success": True,
            "data": {
                "professional_id": professional_id,
                "average_rating": avg_rating,
                "num_reviews": num_reviews
            }
        }

    def submit_review(
        self,
        user_id: str,
        professional_id: str,
        rating: float,
        review_text: str,
        submission_date: str
    ) -> dict:
        """
        Create and submit a new review for a professional by a registered user.
        Review constraints:
            - Only registered users can submit reviews.
            - Review must be linked to a valid professional.
            - Users can submit only one review per professional.
            - Moderation status will be 'pending' on submission.
            - Rating should be in [1.0, 5.0].
    
        Args:
            user_id (str): ID of the user submitting the review.
            professional_id (str): ID of the professional being reviewed.
            rating (float): Rating score (1.0 - 5.0).
            review_text (str): Review content.
            submission_date (str): Submission UTC datetime as string.

        Returns:
            dict: {
                "success": True,
                "message": "Review submitted and pending moderation."
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        # Check professional exists
        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional does not exist." }
        # Check for duplicate review
        for review in self.reviews.values():
            if review["user_id"] == user_id and review["professional_id"] == professional_id:
                return { "success": False, "error": "User has already submitted a review for this professional." }
        # Basic rating check
        if not (1.0 <= rating <= 5.0):
            return { "success": False, "error": "Rating must be between 1.0 and 5.0." }
        if not review_text.strip():
            return { "success": False, "error": "Review text cannot be empty." }
        # Generate unique review_id (simple auto-increment)
        review_id = f"review_{len(self.reviews)+1}"
        # Create review info
        new_review: ReviewInfo = {
            "view_id": review_id,
            "user_id": user_id,
            "professional_id": professional_id,
            "rating": rating,
            "review_text": review_text,
            "submission_date": submission_date,
            "moderation_status": "pending"
        }
        self.reviews[review_id] = new_review
        return { "success": True, "message": "Review submitted and pending moderation." }

    def edit_review(
        self,
        view_id: str,
        new_rating: float = None,
        new_review_text: str = None
    ) -> dict:
        """
        Modify the content or rating of an existing review.

        Args:
            view_id (str): The ID of the review to modify.
            new_rating (float, optional): The updated rating. If None, not changed.
            new_review_text (str, optional): The updated review text. If None, not changed.

        Returns:
            dict: {
                "success": True,
                "message": "Review updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - Review must exist.
            - Only allow editing while moderation_status == "pending".
            - At least one of new_rating or new_review_text must be provided.
        """
        review = self.reviews.get(view_id)
        if not review:
            return { "success": False, "error": "Review does not exist." }

        if review.get("moderation_status") != "pending":
            return { "success": False, "error": "Review cannot be edited after moderation." }

        if new_rating is None and new_review_text is None:
            return { "success": False, "error": "No new content provided to update." }

        updated = False
        if new_rating is not None:
            review["rating"] = new_rating
            updated = True
        if new_review_text is not None:
            review["review_text"] = new_review_text
            updated = True

        if not updated:
            return { "success": False, "error": "No valid updates made to the review." }

        return { "success": True, "message": "Review updated successfully." }

    def delete_review(self, review_id: str) -> dict:
        """
        Remove a review with the given review_id from the platform.

        Args:
            review_id (str): The unique identifier for the review to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Review deleted successfully."
            }
            or
            {
                "success": False,
                "error": str  # explanation of error, e.g. review not found
            }

        Constraints:
            - The review must exist.
            - No explicit authorization checks (user ownership/admin) here.
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review not found."}

        # Optionally: for future design, extract professional_id for rating updates if needed
        # professional_id = self.reviews[review_id]["professional_id"]
        # rating_was_approved = self.reviews[review_id]["moderation_status"] == "approved"

        del self.reviews[review_id]
        return {"success": True, "message": "Review deleted successfully."}

    def change_review_moderation_status(self, view_id: str, new_status: str) -> dict:
        """
        Update the moderation status of a review.

        Args:
            view_id (str): The unique ID of the review to update.
            new_status (str): The new moderation status ('pending', 'approved', 'rejected').

        Returns:
            dict: {
                "success": True,
                "message": "Review moderation status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Review must exist.
            - new_status must be one of ('pending', 'approved', 'rejected').
        """
        valid_statuses = {"pending", "approved", "rejected"}
        if view_id not in self.reviews:
            return { "success": False, "error": "Review does not exist." }
        if new_status not in valid_statuses:
            return { "success": False, "error": "Invalid moderation status. Must be 'pending', 'approved', or 'rejected'." }

        self.reviews[view_id]["moderation_status"] = new_status

        return {
            "success": True,
            "message": f"Review moderation status updated to '{new_status}'."
        }

    def update_professional_aggregated_rating(self, professional_id: str) -> dict:
        """
        Recalculate and update the professional's aggregated rating based on all 'approved' reviews.

        Args:
            professional_id (str): The ID of the professional whose aggregate rating is to be updated.

        Returns:
            dict:
                - success (bool): True if successful, False if failed.
                - message (str): Operation message if successful.
                - aggregated_rating (float or None): Updated average rating (None if no approved reviews).
                - error (str, optional): Error reason if unsuccessful.

        Constraints:
            - Only approved reviews are considered for aggregation.
            - Professional must exist.
            - The professional's aggregated rating is stored as 'aggregated_rating' field in their info.

        Note:
            If no approved reviews exist, aggregated_rating is set to None.
        """
        professional = self.professionals.get(professional_id)
        if not professional:
            return { "success": False, "error": "Professional does not exist" }

        # Gather approved reviews for the professional
        approved_ratings = [
            review["rating"] for review in self.reviews.values()
            if review["professional_id"] == professional_id and review["moderation_status"] == "approved"
        ]

        # Compute average rating
        if approved_ratings:
            aggregated_rating = sum(approved_ratings) / len(approved_ratings)
        else:
            aggregated_rating = None  # No approved reviews

        # Update professional profile with new aggregated rating.
        # Add 'aggregated_rating' field if it does not exist.
        professional["aggregated_rating"] = aggregated_rating

        return {
            "success": True,
            "message": "Aggregated rating updated",
            "aggregated_rating": aggregated_rating
        }
