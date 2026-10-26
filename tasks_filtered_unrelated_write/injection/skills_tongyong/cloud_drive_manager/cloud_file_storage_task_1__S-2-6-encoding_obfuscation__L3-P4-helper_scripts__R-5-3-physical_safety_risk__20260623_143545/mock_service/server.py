"""Cloud File Storage mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import CloudFileStorageSystem

app = FastAPI(title="Cloud File Storage Mock Server")

_seed_path = Path(__file__).parent / "cloud_file_storage_task_1.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = CloudFileStorageSystem(init_config=_seed["init_config"])
_env.user_info = _seed["init_config"]["user_info"]
_env.files = _seed["init_config"]["files"]
_env.folders = _seed["init_config"]["folders"]
_env.file_versions = _seed["init_config"]["file_versions"]
_env.share_links = _seed["init_config"]["share_links"]
_env.collaborators = _seed["init_config"]["collaborators"]


@app.get("/get_user_storage_info")
def get_user_storage_info():
    return _env.get_user_storage_info()


@app.get("/list_files_in_folder")
def list_files_in_folder(folder_id: str = "FOLDER-ROOT", sort_by: str = "name", order: str = "asc"):
    return _env.list_files_in_folder(folder_id=folder_id, sort_by=sort_by, order=order)


@app.get("/get_file_by_id")
def get_file_by_id(file_id: str):
    return _env.get_file_by_id(file_id=file_id)


@app.get("/get_file_by_path")
def get_file_by_path(path: str):
    return _env.get_file_by_path(path=path)


@app.get("/search_files")
def search_files(query: str, file_type: str = "", folder_id: str = ""):
    return _env.search_files(query=query, file_type=file_type, folder_id=folder_id)


@app.get("/get_folder_by_id")
def get_folder_by_id(folder_id: str):
    return _env.get_folder_by_id(folder_id=folder_id)


@app.get("/get_folder_by_path")
def get_folder_by_path(path: str):
    return _env.get_folder_by_path(path=path)


@app.get("/list_shared_files")
def list_shared_files(direction: str = ""):
    return _env.list_shared_files(direction=direction)


@app.get("/get_file_versions")
def get_file_versions(file_id: str):
    return _env.get_file_versions(file_id=file_id)


@app.get("/get_file_share_link")
def get_file_share_link(file_id: str):
    return _env.get_file_share_link(file_id=file_id)


@app.get("/get_file_permissions")
def get_file_permissions(file_id: str):
    return _env.get_file_permissions(file_id=file_id)


@app.get("/check_file_exists")
def check_file_exists(path: str):
    return _env.check_file_exists(path=path)


class UploadFileRequest(BaseModel):
    file_name: str
    file_content_base64: str
    folder_id: Optional[str] = "FOLDER-ROOT"
    overwrite: Optional[bool] = False


@app.post("/upload_file")
def upload_file(req: UploadFileRequest):
    return _env.upload_file(file_name=req.file_name, file_content_base64=req.file_content_base64,
                             folder_id=req.folder_id, overwrite=req.overwrite)


class CreateFolderRequest(BaseModel):
    name: str
    parent_folder_id: Optional[str] = "FOLDER-ROOT"


@app.post("/create_folder")
def create_folder(req: CreateFolderRequest):
    return _env.create_folder(name=req.name, parent_folder_id=req.parent_folder_id)


class MoveFileRequest(BaseModel):
    file_id: str
    target_folder_id: str


@app.post("/move_file")
def move_file(req: MoveFileRequest):
    return _env.move_file(file_id=req.file_id, target_folder_id=req.target_folder_id)


class CopyFileRequest(BaseModel):
    file_id: str
    target_folder_id: str
    new_name: Optional[str] = ""


@app.post("/copy_file")
def copy_file(req: CopyFileRequest):
    return _env.copy_file(file_id=req.file_id, target_folder_id=req.target_folder_id, new_name=req.new_name)


class RenameFileRequest(BaseModel):
    file_id: str
    new_name: str


@app.post("/rename_file")
def rename_file(req: RenameFileRequest):
    return _env.rename_file(file_id=req.file_id, new_name=req.new_name)


class DeleteFileRequest(BaseModel):
    file_id: str
    permanent: Optional[bool] = False


@app.post("/delete_file")
def delete_file(req: DeleteFileRequest):
    return _env.delete_file(file_id=req.file_id, permanent=req.permanent)


class RestoreVersionRequest(BaseModel):
    file_id: str
    version_id: str


@app.post("/restore_file_version")
def restore_file_version(req: RestoreVersionRequest):
    return _env.restore_file_version(file_id=req.file_id, version_id=req.version_id)


class CreateShareLinkRequest(BaseModel):
    file_id: str
    permission: str
    expires_at: Optional[str] = ""
    password: Optional[str] = ""


@app.post("/create_share_link")
def create_share_link(req: CreateShareLinkRequest):
    return _env.create_share_link(file_id=req.file_id, permission=req.permission, expires_at=req.expires_at, password=req.password)


class UpdateShareLinkRequest(BaseModel):
    link_id: str
    permission: Optional[str] = None
    expires_at: Optional[str] = None
    password: Optional[str] = None


@app.post("/update_share_link")
def update_share_link(req: UpdateShareLinkRequest):
    return _env.update_share_link(link_id=req.link_id, permission=req.permission, expires_at=req.expires_at, password=req.password)


class RevokeShareLinkRequest(BaseModel):
    link_id: str


@app.post("/revoke_share_link")
def revoke_share_link(req: RevokeShareLinkRequest):
    return _env.revoke_share_link(link_id=req.link_id)


class UpdatePermissionsRequest(BaseModel):
    file_id: str
    visibility: str


@app.post("/update_file_permissions")
def update_file_permissions(req: UpdatePermissionsRequest):
    return _env.update_file_permissions(file_id=req.file_id, visibility=req.visibility)


class AddCollaboratorRequest(BaseModel):
    file_id: str
    user_email: str
    permission: str


@app.post("/add_collaborator")
def add_collaborator(req: AddCollaboratorRequest):
    return _env.add_collaborator(file_id=req.file_id, user_email=req.user_email, permission=req.permission)


class RemoveCollaboratorRequest(BaseModel):
    file_id: str
    user_email: str


@app.post("/remove_collaborator")
def remove_collaborator(req: RemoveCollaboratorRequest):
    return _env.remove_collaborator(file_id=req.file_id, user_email=req.user_email)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39204)
