"""Note Taking mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import NoteTakingSystem

app = FastAPI(title="Note Taking Mock Server")

_seed_path = Path(__file__).parent / "seed_data.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = NoteTakingSystem(init_config=_seed["init_config"])
_env.user_info = _seed["init_config"]["user_info"]
_env.notebooks = _seed["init_config"]["notebooks"]
_env.notes = _seed["init_config"]["notes"]
_env.note_versions = _seed["init_config"]["note_versions"]
_env.tags = _seed["init_config"]["tags"]


@app.get("/get_user_info")
def get_user_info():
    return _env.get_user_info()


@app.get("/list_notebooks")
def list_notebooks():
    return _env.list_notebooks()


@app.get("/get_notebook_by_id")
def get_notebook_by_id(notebook_id: str):
    return _env.get_notebook_by_id(notebook_id=notebook_id)


@app.get("/list_notes_in_notebook")
def list_notes_in_notebook(notebook_id: str, sort_by: str = "updated_at", order: str = "desc"):
    return _env.list_notes_in_notebook(notebook_id=notebook_id, sort_by=sort_by, order=order)


@app.get("/get_note_by_id")
def get_note_by_id(note_id: str):
    return _env.get_note_by_id(note_id=note_id)


@app.get("/search_notes")
def search_notes(query: str, notebook_id: str = "", tag: str = ""):
    return _env.search_notes(query=query, notebook_id=notebook_id, tag=tag)


@app.get("/get_notes_by_tag")
def get_notes_by_tag(tag_name: str):
    return _env.get_notes_by_tag(tag_name=tag_name)


@app.get("/list_all_tags")
def list_all_tags():
    return _env.list_all_tags()


@app.get("/get_note_versions")
def get_note_versions(note_id: str):
    return _env.get_note_versions(note_id=note_id)


@app.get("/get_shared_notes")
def get_shared_notes(direction: str = ""):
    return _env.get_shared_notes(direction=direction)


@app.get("/check_note_exists")
def check_note_exists(title: str, notebook_id: str = ""):
    return _env.check_note_exists(title=title, notebook_id=notebook_id)


class CreateNoteRequest(BaseModel):
    title: str
    content: str
    notebook_id: str
    tags: Optional[List[str]] = []


@app.post("/create_note")
def create_note(req: CreateNoteRequest):
    return _env.create_note(title=req.title, content=req.content, notebook_id=req.notebook_id, tags=req.tags)


class UpdateNoteContentRequest(BaseModel):
    note_id: str
    content: str


@app.post("/update_note_content")
def update_note_content(req: UpdateNoteContentRequest):
    return _env.update_note_content(note_id=req.note_id, content=req.content)


class UpdateNoteTitleRequest(BaseModel):
    note_id: str
    new_title: str


@app.post("/update_note_title")
def update_note_title(req: UpdateNoteTitleRequest):
    return _env.update_note_title(note_id=req.note_id, new_title=req.new_title)


class MoveNoteRequest(BaseModel):
    note_id: str
    target_notebook_id: str


@app.post("/move_note_to_notebook")
def move_note_to_notebook(req: MoveNoteRequest):
    return _env.move_note_to_notebook(note_id=req.note_id, target_notebook_id=req.target_notebook_id)


class TagNoteRequest(BaseModel):
    note_id: str
    tag_name: str


@app.post("/add_tag_to_note")
def add_tag_to_note(req: TagNoteRequest):
    return _env.add_tag_to_note(note_id=req.note_id, tag_name=req.tag_name)


@app.post("/remove_tag_from_note")
def remove_tag_from_note(req: TagNoteRequest):
    return _env.remove_tag_from_note(note_id=req.note_id, tag_name=req.tag_name)


class NoteIdRequest(BaseModel):
    note_id: str


@app.post("/delete_note")
def delete_note(req: NoteIdRequest):
    return _env.delete_note(note_id=req.note_id)


class RestoreVersionRequest(BaseModel):
    note_id: str
    version_id: str


@app.post("/restore_note_version")
def restore_note_version(req: RestoreVersionRequest):
    return _env.restore_note_version(note_id=req.note_id, version_id=req.version_id)


class CreateNotebookRequest(BaseModel):
    name: str
    description: Optional[str] = ""


@app.post("/create_notebook")
def create_notebook(req: CreateNotebookRequest):
    return _env.create_notebook(name=req.name, description=req.description)


class RenameNotebookRequest(BaseModel):
    notebook_id: str
    new_name: str


@app.post("/rename_notebook")
def rename_notebook(req: RenameNotebookRequest):
    return _env.rename_notebook(notebook_id=req.notebook_id, new_name=req.new_name)


class NotebookIdRequest(BaseModel):
    notebook_id: str


@app.post("/delete_notebook")
def delete_notebook(req: NotebookIdRequest):
    return _env.delete_notebook(notebook_id=req.notebook_id)


class ShareNoteRequest(BaseModel):
    note_id: str
    share_type: str
    user_email: Optional[str] = ""
    permission: Optional[str] = "view"


@app.post("/share_note")
def share_note(req: ShareNoteRequest):
    return _env.share_note(note_id=req.note_id, share_type=req.share_type, user_email=req.user_email, permission=req.permission)


class UnshareNoteRequest(BaseModel):
    note_id: str
    user_email: Optional[str] = ""


@app.post("/unshare_note")
def unshare_note(req: UnshareNoteRequest):
    return _env.unshare_note(note_id=req.note_id, user_email=req.user_email)


@app.post("/pin_note")
def pin_note(req: NoteIdRequest):
    return _env.pin_note(note_id=req.note_id)


@app.post("/unpin_note")
def unpin_note(req: NoteIdRequest):
    return _env.unpin_note(note_id=req.note_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39205)
