from typing import Dict, List, Optional, TypedDict
import re
from datetime import datetime
import uuid



class BookmarkInfo(TypedDict):
    bookmark_id: str
    title: str
    url: str
    added_date: str
    folder_id: str
    tags: List[str]     # List of tag_id strings
    description: str

class FolderInfo(TypedDict):
    folder_id: str
    name: str
    parent_folder_id: Optional[str]  # None for root folders

class TagInfo(TypedDict):
    tag_id: str
    name: str

class WebBrowserBookmarkSystem:
    def __init__(self, init_config: dict):
        """
        Web browser bookmark system environment state.
        init_config: external configuration (not implemented here).
        """
        # Bookmarks: {bookmark_id: BookmarkInfo}
        self.bookmarks: Dict[str, BookmarkInfo] = {}

        # Folders: {folder_id: FolderInfo}
        self.folders: Dict[str, FolderInfo] = {}

        # Tags: {tag_id: TagInfo}
        self.tags: Dict[str, TagInfo] = {}

        # Constraints:
        # - Each bookmark must have a valid URL.
        # - Bookmark titles should not be empty.
        # - Bookmarks can be organized into folders, and folders may be nested.
        # - No duplicate bookmarks (same URL and folder) are allowed within the same folder.

        self.init_config = init_config

    def list_folders(self) -> dict:
        """
        Retrieve all folders available for organizing bookmarks.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FolderInfo],  # List of all folder info (may be empty if no folders exist)
            }

        Constraints:
            - None directly applicable; always returns all folders present in self.folders.
        """
        folder_list = list(self.folders.values())
        return { "success": True, "data": folder_list }

    def get_folder_by_name(self, name: str) -> dict:
        """
        Query details of folder(s) by folder name.

        Args:
            name (str): The name of the folder to query.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[FolderInfo]  # List of matching folders (could be empty)
                }
                On error:
                {
                    "success": False,
                    "error": str  # If no folder found with the given name
                }

        Constraints:
            - Folder names may not be unique, so return all matches.
        """
        result = [
            folder_info
            for folder_info in self.folders.values()
            if folder_info["name"] == name
        ]

        if not result:
            return { "success": False, "error": "No folder found with the specified name" }
        return { "success": True, "data": result }

    def get_folder_hierarchy(self) -> dict:
        """
        Retrieve the folder nesting structure as a hierarchy tree for navigation/organization.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # List of root folders, each containing nested subfolders
            }
            or
            {
                "success": False,
                "error": str  # Unexpected error description (unlikely)
            }

        Constraints:
            - Folders may be nested. Tree structure only; no cycles.
            - If there are no folders, returns empty list.
        """
        # Build helper: mapping from folder_id -> list of child FolderInfo
        children_map = {fid: [] for fid in self.folders}
        for folder in self.folders.values():
            pid = folder["parent_folder_id"]
            if pid and pid in children_map:
                children_map[pid].append(folder["folder_id"])

        # Recursive builder for folder tree
        def build_tree(folder_id: str) -> dict:
            folder = self.folders[folder_id]
            return {
                "folder_id": folder["folder_id"],
                "name": folder["name"],
                "children": [build_tree(child_id) for child_id in children_map[folder_id]]
            }

        # Collect roots (folders with no parent)
        roots = [
            build_tree(folder_id)
            for folder_id, folder in self.folders.items()
            if folder["parent_folder_id"] is None
        ]

        return {"success": True, "data": roots}

    def list_bookmarks_in_folder(self, folder_id: str) -> dict:
        """
        Retrieve all bookmarks located in the specified folder.

        Args:
            folder_id (str): The ID of the folder whose bookmarks should be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[BookmarkInfo]  # All bookmarks in the folder (empty list if none).
            }
            or
            {
                "success": False,
                "error": str  # Explanation if the folder_id is invalid.
            }

        Constraints:
            - The folder_id must exist in the system.
        """
        if folder_id not in self.folders:
            return { "success": False, "error": "Folder does not exist" }
    
        bookmarks_in_folder = [
            bookmark for bookmark in self.bookmarks.values()
            if bookmark["folder_id"] == folder_id
        ]
        return { "success": True, "data": bookmarks_in_folder }

    def find_bookmark_by_url_and_folder(self, url: str, folder_id: str) -> dict:
        """
        Determines whether a bookmark with the specified URL exists in the given folder.

        Args:
            url (str): The URL of the web resource to check.
            folder_id (str): The folder to search within.

        Returns:
            dict: {
                "success": True,
                "data": List[BookmarkInfo],  # All matching bookmarks (normally max one per constraints)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., folder not found)
            }

        Constraints:
            - folder_id must refer to an existing folder.
            - (URL validation for finding is not strictly required.)
        """
        if folder_id not in self.folders:
            return { "success": False, "error": "Folder does not exist." }
        # Find all bookmarks with matching url and folder_id
        matches = [
            bm_info for bm_info in self.bookmarks.values()
            if bm_info["url"] == url and bm_info["folder_id"] == folder_id
        ]
        return { "success": True, "data": matches }

    def list_tags(self) -> dict:
        """
        Retrieve all tags available for bookmarks.

        Args:
            None

        Returns:
            dict:
                - success (bool): True if operation succeeded.
                - data (List[TagInfo]): List of all tag information dictionaries. Empty if no tags.

        Constraints:
            - No input or filtering. All existing tags are listed.
        """
        tags_list = list(self.tags.values())
        return { "success": True, "data": tags_list }

    def find_tag_by_name(self, name: str) -> dict:
        """
        Query tags by their human-readable name.

        Args:
            name (str): The name of the tag to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo]  # List of tags matching the name (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error message for invalid input
            }

        Constraints:
            - 'name' must be a non-empty string.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Tag name must be a non-empty string."}

        matches = [tag_info for tag_info in self.tags.values() if tag_info["name"] == name]

        return {"success": True, "data": matches}

    def get_bookmark_by_id(self, bookmark_id: str) -> dict:
        """
        Retrieve full details of a bookmark given its unique bookmark_id.

        Args:
            bookmark_id (str): The unique identifier for the bookmark.

        Returns:
            dict:
                - success: True, data: BookmarkInfo dict if bookmark found
                - success: False, error: Reason string if not found
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if bookmark is None:
            return { "success": False, "error": "Bookmark ID not found" }

        return { "success": True, "data": bookmark }

    def validate_url_format(self, url: str) -> dict:
        """
        Verify that a given URL is valid per the system’s rules.

        Args:
            url (str): The URL string to validate.

        Returns:
            dict: {
                "success": True,
                "data": True  # If valid
            } or {
                "success": True,
                "data": False # If not valid
            } or {
                "success": False,
                "error": str  # If the input itself is invalid (not a string)
            }

        Constraints:
            - URL must be a non-empty string.
            - URL should start with 'http://' or 'https://'.
        """
        if not isinstance(url, str):
            return { "success": False, "error": "URL must be a string" }
        url = url.strip()
        if not url:
            return { "success": True, "data": False }
        if url.startswith("http://") or url.startswith("https://"):
            # Further check: common format, must not have spaces
            if " " in url:
                return { "success": True, "data": False }
            # Optionally: check for a domain and a dot
            if '.' in url.split("//", 1)[-1]:
                return { "success": True, "data": True }
            else:
                return { "success": True, "data": False }
        else:
            return { "success": True, "data": False }

    def add_bookmark(
        self,
        title: str,
        url: str,
        folder_id: str,
        tags: List[str],
        description: str = "",
        added_date: Optional[str] = None
    ) -> dict:
        """
        Save a new bookmark specifying title, URL, folder, tags, and metadata.

        Args:
            title (str): Title for the bookmark (must be non-empty).
            url (str): URL to bookmark (must be valid format).
            folder_id (str): ID of the folder to contain this bookmark.
            tags (List[str]): List of tag_ids to associate.
            description (str, optional): Description of the bookmark.
            added_date (str, optional): Date when added (ISO8601 recommended), auto-set if not provided.

        Returns:
            dict:
                - success: True/False
                - message: Success message (if True)
                - error: Reason for failure (if False)

        Constraints:
            - Title must not be empty.
            - URL must be valid format.
            - Bookmark must not already exist in same folder with same URL.
            - Folder must exist.
            - Each tag in tags must exist in self.tags.
        """

        # Title check
        if not title or title.strip() == "":
            return { "success": False, "error": "Bookmark title must not be empty." }

        # Folder existence
        if folder_id not in self.folders:
            return { "success": False, "error": "Specified folder does not exist." }

        # URL format validation (simple regex for HTTP/HTTPS)
        url_pattern = r"^https?://[^\s]+$"
        if not re.match(url_pattern, url):
            return { "success": False, "error": "Bookmark URL is not valid." }

        # Duplicate check: same URL and folder
        for bm in self.bookmarks.values():
            if bm["url"] == url and bm["folder_id"] == folder_id:
                return { "success": False, "error": "Bookmark with this URL already exists in the specified folder." }

        # Tag existence check
        invalid_tags = [tag_id for tag_id in tags if tag_id not in self.tags]
        if invalid_tags:
            return { "success": False, "error": f"Invalid tag_ids: {', '.join(invalid_tags)}" }

        # Generate bookmark_id (simple unique by time and folder count)
        bookmark_id = f"bm_{len(self.bookmarks)+1}_{int(datetime.utcnow().timestamp())}"

        # Set added_date to now if not provided
        if not added_date:
            added_date = datetime.utcnow().isoformat()

        new_bookmark = {
            "bookmark_id": bookmark_id,
            "title": title,
            "url": url,
            "added_date": added_date,
            "folder_id": folder_id,
            "tags": tags,
            "description": description
        }

        self.bookmarks[bookmark_id] = new_bookmark

        return { "success": True, "message": "Bookmark added successfully." }

    def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> dict:
        """
        Add a new folder to organize bookmarks.

        Args:
            name (str): Name of the new folder (must not be empty).
            parent_folder_id (Optional[str]): If provided, creates as a child of this folder id;
                if None, creates as root-level folder.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Folder '<name>' created with id <folder_id>"
                  }
                - On failure: {
                    "success": False,
                    "error": "<error description>"
                  }

        Constraints:
            - Folder name must not be empty.
            - If parent_folder_id is provided, it must exist.
        """
        if not name or not name.strip():
            return {"success": False, "error": "Folder name must not be empty"}

        if parent_folder_id is not None and parent_folder_id not in self.folders:
            return {"success": False, "error": "Parent folder does not exist"}

        # Generate a unique folder_id
        folder_id = str(uuid.uuid4())

        folder_info = {
            "folder_id": folder_id,
            "name": name,
            "parent_folder_id": parent_folder_id
        }

        self.folders[folder_id] = folder_info

        return {
            "success": True,
            "message": f"Folder '{name}' created with id {folder_id}"
        }

    def create_tag(self, name: str) -> dict:
        """
        Create a new tag for categorizing bookmarks.

        Args:
            name (str): The name for the new tag.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Tag '<name>' created with id '<tag_id>'."}
                - On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Tag names should not be empty or whitespace only.
            - No duplicate tag names allowed.
        """
        # Check that name is not empty or whitespace
        if not name or not name.strip():
            return {"success": False, "error": "Tag name cannot be empty."}

        # Check for uniqueness
        for tag in self.tags.values():
            if tag["name"].strip().lower() == name.strip().lower():
                return {"success": False, "error": f"Tag '{name.strip()}' already exists."}

        # Generate a tag_id
        tag_id = f"tag_{len(self.tags)+1}"
        tag_info: TagInfo = {"tag_id": tag_id, "name": name.strip()}
        self.tags[tag_id] = tag_info

        return {
            "success": True,
            "message": f"Tag '{name.strip()}' created with id '{tag_id}'."
        }

    def update_bookmark(
        self,
        bookmark_id: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Modify details of an existing bookmark. Only provided fields will be updated.

        Args:
            bookmark_id (str): ID of bookmark to update.
            title (Optional[str]): New title (cannot be empty if provided).
            url (Optional[str]): New URL (must be valid if provided).
            folder_id (Optional[str]): New folder to move bookmark to (must exist).
            tags (Optional[List[str]]): New tags for the bookmark (must all exist).
            description (Optional[str]): New description.

        Returns:
            dict: {
                "success": True,
                "message": "Bookmark updated successfully"
            }
            or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - bookmark_id must exist.
            - Provided title (if any) must not be empty.
            - Provided url (if any) must be valid format and not conflict with another bookmark in target folder.
            - Provided folder_id (if any) must exist.
            - Provided tags (if any) must all exist.
            - After update, no duplicate bookmark (same URL and folder).
        """
        # Check if bookmark exists
        if bookmark_id not in self.bookmarks:
            return {"success": False, "error": "Bookmark does not exist"}

        bookmark = self.bookmarks[bookmark_id]
        new_title = title if title is not None else bookmark["title"]
        new_url = url if url is not None else bookmark["url"]
        new_folder_id = folder_id if folder_id is not None else bookmark["folder_id"]
        new_tags = tags if tags is not None else bookmark["tags"]
        new_description = description if description is not None else bookmark["description"]

        # Title constraint
        if title is not None and title.strip() == "":
            return {"success": False, "error": "Title cannot be empty"}

        # URL constraint
        if url is not None:
            # Minimal validation: not empty, starts with http or https
            if not url.strip():
                return {"success": False, "error": "URL cannot be empty"}
            if not (url.startswith("http://") or url.startswith("https://")):
                return {"success": False, "error": "Invalid URL format"}

        # Folder constraint
        if folder_id is not None and folder_id not in self.folders:
            return {"success": False, "error": "Target folder does not exist"}

        # Tags constraint
        if tags is not None:
            for tag_id in tags:
                if tag_id not in self.tags:
                    return {"success": False, "error": f"Tag '{tag_id}' does not exist"}

        # No duplicate bookmarks constraint (same URL in same folder)
        for other_bm_id, other_bm in self.bookmarks.items():
            if other_bm_id != bookmark_id:
                if other_bm["folder_id"] == new_folder_id and other_bm["url"] == new_url:
                    return {"success": False, "error": "Duplicate bookmark with same URL exists in target folder"}

        # Perform update
        bookmark["title"] = new_title
        bookmark["url"] = new_url
        bookmark["folder_id"] = new_folder_id
        bookmark["tags"] = new_tags
        bookmark["description"] = new_description

        self.bookmarks[bookmark_id] = bookmark

        return {"success": True, "message": "Bookmark updated successfully"}

    def delete_bookmark(self, bookmark_id: str) -> dict:
        """
        Remove a bookmark from the system given its unique identifier.

        Args:
            bookmark_id (str): Unique identifier of the bookmark to remove.

        Returns:
            dict:
                success: True and a success message if deleted;
                success: False and an error description if bookmark not found or id invalid.

        Constraints:
            - The bookmark with the given id must exist.
        """
        if not bookmark_id or bookmark_id not in self.bookmarks:
            return {
                "success": False,
                "error": "Bookmark not found."
            }
        del self.bookmarks[bookmark_id]
        return {
            "success": True,
            "message": "Bookmark deleted successfully."
        }

    def move_bookmark_to_folder(self, bookmark_id: str, target_folder_id: str) -> dict:
        """
        Relocate a bookmark to a different folder.

        Args:
            bookmark_id (str): The unique ID of the bookmark to move.
            target_folder_id (str): The target folder's ID.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Bookmark moved to folder."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The bookmark must exist.
            - The target folder must exist.
            - No duplicate bookmarks (same URL and folder) allowed within the same folder.
        """
        if bookmark_id not in self.bookmarks:
            return {"success": False, "error": "Bookmark does not exist."}

        if target_folder_id not in self.folders:
            return {"success": False, "error": "Target folder does not exist."}

        bookmark = self.bookmarks[bookmark_id]

        # Check for duplicate URL in target folder
        for other_bookmark in self.bookmarks.values():
            if (other_bookmark["folder_id"] == target_folder_id and
                other_bookmark["url"] == bookmark["url"] and
                other_bookmark["bookmark_id"] != bookmark_id):
                return {
                    "success": False,
                    "error": "A bookmark with the same URL already exists in the target folder."
                }

        # Move bookmark
        self.bookmarks[bookmark_id]["folder_id"] = target_folder_id

        return {"success": True, "message": "Bookmark moved to folder."}

    def delete_folder(self, folder_id: str) -> dict:
        """
        Delete the specified folder and recursively its subfolders;
        Also deletes all bookmarks that belong to these folders.

        Args:
            folder_id (str): ID of the folder to delete.

        Returns:
            dict:
                If success:
                    {
                        "success": True,
                        "message": "Folder <folder_id> and N bookmarks deleted."
                    }
                If failure:
                    {
                        "success": False,
                        "error": "Folder not found."
                    }

        Constraints:
            - Removes the folder and all its descendant subfolders.
            - Deletes all bookmarks in the deleted folders.
            - Folder_id must exist.
        """
        if folder_id not in self.folders:
            return { "success": False, "error": "Folder not found." }

        # Collect all folders to delete (recursive)
        folders_to_delete = set()
        def collect_descendants(fid):
            folders_to_delete.add(fid)
            for f in self.folders.values():
                if f.get("parent_folder_id") == fid:
                    collect_descendants(f["folder_id"])
        collect_descendants(folder_id)

        # Collect all bookmarks to delete
        bookmarks_to_delete = [
            b_id for b_id, b_info in self.bookmarks.items()
            if b_info["folder_id"] in folders_to_delete
        ]
        num_bookmarks = len(bookmarks_to_delete)

        # Delete bookmarks
        for b_id in bookmarks_to_delete:
            del self.bookmarks[b_id]
    
        # Delete folders
        for fid in folders_to_delete:
            del self.folders[fid]

        return {
            "success": True,
            "message": f"Folder '{folder_id}' and {num_bookmarks} bookmarks deleted."
        }

    def update_folder(self, folder_id: str, name: Optional[str] = None, parent_folder_id: Optional[str] = None) -> dict:
        """
        Change folder attributes (name, parent_folder_id).

        Args:
            folder_id (str): The folder to modify.
            name (Optional[str]): New name for the folder. Must not be empty if provided.
            parent_folder_id (Optional[str]): New parent folder id (None for root). Must not create cycles.

        Returns:
            dict: {
                "success": True,
                "message": "Folder updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Folder must exist.
            - If name is provided, it must not be empty.
            - If parent_folder_id is provided: parent folder must exist or be None; cannot create cycles.
        """
        if folder_id not in self.folders:
            return { "success": False, "error": "Folder does not exist." }
    
        # Patch object
        folder = self.folders[folder_id]

        # Name validation
        if name is not None:
            if not name.strip():
                return { "success": False, "error": "Folder name must not be empty." }
            folder["name"] = name

        # Parent folder validation
        if parent_folder_id is not None:
            if parent_folder_id == folder_id:
                return { "success": False, "error": "Folder cannot be its own parent." }
            if parent_folder_id is not None and parent_folder_id not in self.folders:
                return { "success": False, "error": "New parent folder does not exist." }
            # Prevent cycles: cannot set parent to a descendant folder
            # Traverse descendants of folder_id; if parent_folder_id is found among them, it's a cycle
            def is_descendant(child_id: str, target_id: str) -> bool:
                stack = [child_id]
                while stack:
                    current = stack.pop()
                    for f in self.folders.values():
                        if f.get("parent_folder_id") == current:
                            if f["folder_id"] == target_id:
                                return True
                            stack.append(f["folder_id"])
                return False

            if parent_folder_id is not None and is_descendant(folder_id, parent_folder_id):
                return { "success": False, "error": "Cannot set parent_folder_id to a descendant (would create cycle)." }
        
            folder["parent_folder_id"] = parent_folder_id

        # Update in storage
        self.folders[folder_id] = folder
        return { "success": True, "message": "Folder updated successfully." }

    def add_tag_to_bookmark(self, bookmark_id: str, tag_id: str) -> dict:
        """
        Associate a tag with a bookmark.

        Args:
            bookmark_id (str): The ID of the bookmark to which the tag will be added.
            tag_id (str): The ID of the tag to associate with the bookmark.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Tag added to bookmark."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The bookmark must exist.
            - The tag must exist.
            - No duplicate association (cannot add the same tag twice).
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark:
            return {"success": False, "error": "Bookmark does not exist."}

        if tag_id not in self.tags:
            return {"success": False, "error": "Tag does not exist."}

        if tag_id in bookmark["tags"]:
            return {"success": False, "error": "Tag already associated with bookmark."}

        bookmark["tags"].append(tag_id)
        return {"success": True, "message": "Tag added to bookmark."}

    def remove_tag_from_bookmark(self, bookmark_id: str, tag_id: str) -> dict:
        """
        Remove association between a tag and a bookmark.

        Args:
            bookmark_id (str): ID of the bookmark to update.
            tag_id (str): ID of the tag to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Tag <tag_id> removed from bookmark <bookmark_id>."
            }
            or
            {
                "success": False,
                "error": "Reason why removal failed."
            }

        Constraints:
            - Bookmark must exist.
            - Tag must exist.
            - Tag must be currently associated with bookmark.
        """
        # Check if the bookmark exists
        if bookmark_id not in self.bookmarks:
            return { "success": False, "error": f"Bookmark '{bookmark_id}' not found." }

        # Check if the tag exists
        if tag_id not in self.tags:
            return { "success": False, "error": f"Tag '{tag_id}' not found." }

        bookmark = self.bookmarks[bookmark_id]
        if tag_id not in bookmark["tags"]:
            return { "success": False, "error": f"Tag '{tag_id}' is not associated with bookmark '{bookmark_id}'." }

        # Remove the tag from the bookmark's tags list
        bookmark["tags"].remove(tag_id)

        return { "success": True, "message": f"Tag '{tag_id}' removed from bookmark '{bookmark_id}'." }
