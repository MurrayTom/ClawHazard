"""Cloud File Storage environment class."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class CloudFileStorageSystem:
    def __init__(self, init_config: Dict[str, Any]):
        self.user_info: Dict = {}
        self.files: Dict[str, Dict] = {}
        self.folders: Dict[str, Dict] = {}
        self.file_versions: Dict[str, List] = {}
        self.share_links: Dict[str, Dict] = {}
        self.collaborators: Dict[str, List] = {}

    def _ok(self, data):
        return {"success": True, "data": data}

    def _not_found(self, msg="Not found"):
        return {"success": False, "error": msg}

    def _new_id(self, prefix=""):
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def get_user_storage_info(self):
        info = {
            "total_gb": self.user_info.get("total_gb", 100),
            "used_gb": self.user_info.get("used_gb", 0),
            "available_gb": self.user_info.get("available_gb", 100)
        }
        return self._ok(info)

    def list_files_in_folder(self, folder_id="FOLDER-ROOT", sort_by="name", order="asc"):
        items = [f for f in self.files.values() if f.get("parent_folder_id") == folder_id]
        subfolders = [f for f in self.folders.values() if f.get("parent_id") == folder_id]
        result = subfolders + items
        reverse = (order == "desc")
        result.sort(key=lambda x: x.get(sort_by, x.get("name", "")), reverse=reverse)
        return self._ok(result)

    def get_file_by_id(self, file_id: str):
        f = self.files.get(file_id)
        if not f:
            return self._not_found()
        return self._ok(f)

    def get_file_by_path(self, path: str):
        for f in list(self.files.values()) + list(self.folders.values()):
            if f.get("path") == path:
                return self._ok(f)
        return self._not_found()

    def search_files(self, query: str, file_type="", folder_id=""):
        results = list(self.files.values())
        if query:
            results = [f for f in results if query.lower() in f.get("name", "").lower()]
        if file_type:
            results = [f for f in results if f.get("name", "").endswith(f".{file_type}")]
        if folder_id:
            results = [f for f in results if f.get("parent_folder_id") == folder_id]
        return self._ok(results)

    def get_folder_by_id(self, folder_id: str):
        f = self.folders.get(folder_id)
        if not f:
            return self._not_found()
        return self._ok(f)

    def get_folder_by_path(self, path: str):
        for f in self.folders.values():
            if f.get("path") == path:
                return self._ok(f)
        return self._not_found()

    def list_shared_files(self, direction=""):
        results = [f for f in self.files.values() if f.get("is_shared")]
        return self._ok(results)

    def get_file_versions(self, file_id: str):
        versions = self.file_versions.get(file_id, [])
        return self._ok(versions)

    def get_file_share_link(self, file_id: str):
        links = [l for l in self.share_links.values() if l.get("file_id") == file_id]
        return self._ok(links)

    def get_file_permissions(self, file_id: str):
        collabs = self.collaborators.get(file_id, [])
        f = self.files.get(file_id, {})
        return self._ok({"visibility": f.get("visibility", "private"), "collaborators": collabs})

    def check_file_exists(self, path: str):
        for f in list(self.files.values()) + list(self.folders.values()):
            if f.get("path") == path:
                return {"success": True, "result": True}
        return {"success": True, "result": False}

    def upload_file(self, file_name: str, file_content_base64: str, folder_id="FOLDER-ROOT", overwrite=False):
        file_id = self._new_id("FILE-")
        folder = self.folders.get(folder_id, {})
        folder_path = folder.get("path", "/")
        file = {
            "file_id": file_id,
            "name": file_name,
            "path": f"{folder_path.rstrip('/')}/{file_name}",
            "size": len(file_content_base64) * 3 // 4,
            "mime_type": "application/octet-stream",
            "parent_folder_id": folder_id,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "owner": self.user_info.get("email", ""),
            "is_shared": False
        }
        self.files[file_id] = file
        return {"success": True, "id": file_id, "data": file}

    def create_folder(self, name: str, parent_folder_id="FOLDER-ROOT"):
        folder_id = self._new_id("FOLDER-")
        parent = self.folders.get(parent_folder_id, {})
        parent_path = parent.get("path", "/")
        folder = {
            "folder_id": folder_id,
            "name": name,
            "path": f"{parent_path.rstrip('/')}/{name}",
            "parent_id": parent_folder_id
        }
        self.folders[folder_id] = folder
        return {"success": True, "id": folder_id, "data": folder}

    def move_file(self, file_id: str, target_folder_id: str):
        f = self.files.get(file_id)
        if not f:
            return self._not_found()
        target = self.folders.get(target_folder_id, {})
        f["parent_folder_id"] = target_folder_id
        f["path"] = f"{target.get('path', '/').rstrip('/')}/{f['name']}"
        f["modified_at"] = datetime.now().isoformat()
        return self._ok(f)

    def copy_file(self, file_id: str, target_folder_id: str, new_name=""):
        f = self.files.get(file_id)
        if not f:
            return self._not_found()
        new_id = self._new_id("FILE-")
        target = self.folders.get(target_folder_id, {})
        copy_name = new_name or f"副本_{f['name']}"
        copy = dict(f)
        copy["file_id"] = new_id
        copy["name"] = copy_name
        copy["path"] = f"{target.get('path', '/').rstrip('/')}/{copy_name}"
        copy["parent_folder_id"] = target_folder_id
        copy["created_at"] = datetime.now().isoformat()
        copy["modified_at"] = datetime.now().isoformat()
        self.files[new_id] = copy
        return {"success": True, "id": new_id, "data": copy}

    def rename_file(self, file_id: str, new_name: str):
        f = self.files.get(file_id)
        if not f:
            f = self.folders.get(file_id)
            if not f:
                return self._not_found()
        old_path = f.get("path", "")
        parent_path = "/".join(old_path.split("/")[:-1])
        f["name"] = new_name
        f["path"] = f"{parent_path}/{new_name}"
        if "modified_at" in f:
            f["modified_at"] = datetime.now().isoformat()
        return self._ok(f)

    def delete_file(self, file_id: str, permanent=False):
        if file_id in self.files:
            del self.files[file_id]
            return {"success": True, "deleted_id": file_id}
        if file_id in self.folders:
            del self.folders[file_id]
            return {"success": True, "deleted_id": file_id}
        return self._not_found()

    def restore_file_version(self, file_id: str, version_id: str):
        f = self.files.get(file_id)
        if not f:
            return self._not_found()
        versions = self.file_versions.get(file_id, [])
        target_version = next((v for v in versions if v.get("version_id") == version_id), None)
        if not target_version:
            return self._not_found("Version not found")
        f["modified_at"] = datetime.now().isoformat()
        return self._ok(f)

    def create_share_link(self, file_id: str, permission: str, expires_at="", password=""):
        link_id = self._new_id("LINK-")
        link = {
            "link_id": link_id,
            "file_id": file_id,
            "url": f"https://cloud.example.com/share/{link_id.lower()}",
            "permission": permission,
            "expires_at": expires_at,
            "password": password
        }
        self.share_links[link_id] = link
        f = self.files.get(file_id)
        if f:
            f["is_shared"] = True
        return {"success": True, "id": link_id, "url": link["url"]}

    def update_share_link(self, link_id: str, permission=None, expires_at=None, password=None):
        link = self.share_links.get(link_id)
        if not link:
            return self._not_found()
        if permission is not None:
            link["permission"] = permission
        if expires_at is not None:
            link["expires_at"] = expires_at
        if password is not None:
            link["password"] = password
        return self._ok(link)

    def revoke_share_link(self, link_id: str):
        if link_id not in self.share_links:
            return self._not_found()
        del self.share_links[link_id]
        return {"success": True, "deleted_id": link_id}

    def update_file_permissions(self, file_id: str, visibility: str):
        f = self.files.get(file_id)
        if not f:
            return self._not_found()
        f["visibility"] = visibility
        return self._ok(f)

    def add_collaborator(self, file_id: str, user_email: str, permission: str):
        collab_id = self._new_id("COLLAB-")
        collab = {"collab_id": collab_id, "file_id": file_id, "user_email": user_email, "permission": permission}
        self.collaborators.setdefault(file_id, []).append(collab)
        return {"success": True, "id": collab_id, "data": collab}

    def remove_collaborator(self, file_id: str, user_email: str):
        collabs = self.collaborators.get(file_id, [])
        self.collaborators[file_id] = [c for c in collabs if c.get("user_email") != user_email]
        return {"success": True, "deleted_id": user_email}
