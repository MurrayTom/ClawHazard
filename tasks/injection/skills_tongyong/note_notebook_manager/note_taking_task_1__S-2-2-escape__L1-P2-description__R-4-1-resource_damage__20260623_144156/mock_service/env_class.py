"""Note Taking environment class."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class NotebookInfo(TypedDict):
    notebook_id: str
    name: str
    description: str
    note_count: int
    created_at: str


class NoteInfo(TypedDict):
    note_id: str
    title: str
    content: str
    notebook_id: str
    tags: List[str]
    is_pinned: bool
    created_at: str
    updated_at: str
    is_shared: bool
    share_url: str


class NoteVersion(TypedDict):
    version_id: str
    note_id: str
    content: str
    created_at: str


class TagInfo(TypedDict):
    tag_id: str
    name: str
    color: str
    note_count: int


class NoteTakingSystem:
    def __init__(self, init_config: dict):
        self.user_info: dict = {}
        self.notebooks: Dict[str, NotebookInfo] = {}
        self.notes: Dict[str, NoteInfo] = {}
        self.note_versions: Dict[str, List[NoteVersion]] = {}
        self.tags: Dict[str, TagInfo] = {}
        self.init_config = init_config

    def get_user_info(self) -> dict:
        return {"success": True, "data": self.user_info}

    def list_notebooks(self) -> dict:
        return {"success": True, "data": list(self.notebooks.values())}

    def get_notebook_by_id(self, notebook_id: str) -> dict:
        nb = self.notebooks.get(notebook_id)
        if not nb:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": nb}

    def list_notes_in_notebook(self, notebook_id: str, sort_by: str = "updated_at", order: str = "desc") -> dict:
        if notebook_id not in self.notebooks:
            return {"success": False, "error": "Notebook not found"}
        notes = [n for n in self.notes.values() if n["notebook_id"] == notebook_id]
        reverse = order == "desc"
        notes.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        return {"success": True, "data": notes}

    def get_note_by_id(self, note_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": note}

    def search_notes(self, query: str, notebook_id: str = None, tag: str = None) -> dict:
        notes = list(self.notes.values())
        if notebook_id:
            notes = [n for n in notes if n["notebook_id"] == notebook_id]
        if tag:
            notes = [n for n in notes if tag in n["tags"]]
        results = [n for n in notes if query.lower() in n["title"].lower() or query.lower() in n["content"].lower()]
        return {"success": True, "data": results}

    def get_notes_by_tag(self, tag_name: str) -> dict:
        results = [n for n in self.notes.values() if tag_name in n["tags"]]
        return {"success": True, "data": results}

    def list_all_tags(self) -> dict:
        return {"success": True, "data": list(self.tags.values())}

    def get_note_versions(self, note_id: str) -> dict:
        if note_id not in self.notes:
            return {"success": False, "error": "Note not found"}
        return {"success": True, "data": self.note_versions.get(note_id, [])}

    def get_shared_notes(self, direction: str = None) -> dict:
        notes = [n for n in self.notes.values() if n["is_shared"]]
        return {"success": True, "data": notes}

    def check_note_exists(self, title: str, notebook_id: str = None) -> dict:
        notes = list(self.notes.values())
        if notebook_id:
            notes = [n for n in notes if n["notebook_id"] == notebook_id]
        exists = any(n["title"] == title for n in notes)
        return {"success": True, "result": exists}

    def create_note(self, title: str, content: str, notebook_id: str, tags: List[str] = None) -> dict:
        if not title or not content:
            return {"success": False, "error": "title and content are required"}
        if notebook_id not in self.notebooks:
            return {"success": False, "error": "Notebook not found"}
        note_id = "NOTE-" + str(uuid.uuid4())[:8].upper()
        now = datetime.now().isoformat()
        note: NoteInfo = {
            "note_id": note_id, "title": title, "content": content, "notebook_id": notebook_id,
            "tags": tags or [], "is_pinned": False, "created_at": now, "updated_at": now,
            "is_shared": False, "share_url": "",
        }
        self.notes[note_id] = note
        self.notebooks[notebook_id]["note_count"] += 1
        # Create initial version
        self.note_versions[note_id] = [{"version_id": "V1", "note_id": note_id, "content": content, "created_at": now}]
        return {"success": True, "id": note_id, "data": note}

    def update_note_content(self, note_id: str, content: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        now = datetime.now().isoformat()
        versions = self.note_versions.setdefault(note_id, [])
        version_id = f"V{len(versions) + 1}"
        versions.append({"version_id": version_id, "note_id": note_id, "content": content, "created_at": now})
        note["content"] = content
        note["updated_at"] = now
        return {"success": True, "data": note}

    def update_note_title(self, note_id: str, new_title: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["title"] = new_title
        note["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": note}

    def move_note_to_notebook(self, note_id: str, target_notebook_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        if target_notebook_id not in self.notebooks:
            return {"success": False, "error": "Target notebook not found"}
        old_nb = note["notebook_id"]
        self.notebooks[old_nb]["note_count"] = max(0, self.notebooks[old_nb]["note_count"] - 1)
        note["notebook_id"] = target_notebook_id
        self.notebooks[target_notebook_id]["note_count"] += 1
        return {"success": True, "data": note}

    def add_tag_to_note(self, note_id: str, tag_name: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        if tag_name not in note["tags"]:
            note["tags"].append(tag_name)
            if not any(t["name"] == tag_name for t in self.tags.values()):
                tag_id = "TAG-" + str(uuid.uuid4())[:8].upper()
                self.tags[tag_id] = {"tag_id": tag_id, "name": tag_name, "color": "#888888", "note_count": 1}
        return {"success": True, "data": note}

    def remove_tag_from_note(self, note_id: str, tag_name: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["tags"] = [t for t in note["tags"] if t != tag_name]
        return {"success": True, "data": note}

    def delete_note(self, note_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        nb_id = note["notebook_id"]
        if nb_id in self.notebooks:
            self.notebooks[nb_id]["note_count"] = max(0, self.notebooks[nb_id]["note_count"] - 1)
        del self.notes[note_id]
        return {"success": True, "deleted_id": note_id}

    def restore_note_version(self, note_id: str, version_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        versions = self.note_versions.get(note_id, [])
        version = next((v for v in versions if v["version_id"] == version_id), None)
        if not version:
            return {"success": False, "error": "Version not found"}
        note["content"] = version["content"]
        note["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": note}

    def create_notebook(self, name: str, description: str = "") -> dict:
        nb_id = "NB-" + str(uuid.uuid4())[:8].upper()
        nb: NotebookInfo = {
            "notebook_id": nb_id, "name": name, "description": description,
            "note_count": 0, "created_at": datetime.now().isoformat(),
        }
        self.notebooks[nb_id] = nb
        return {"success": True, "id": nb_id, "data": nb}

    def rename_notebook(self, notebook_id: str, new_name: str) -> dict:
        nb = self.notebooks.get(notebook_id)
        if not nb:
            return {"success": False, "error": "Notebook not found"}
        nb["name"] = new_name
        return {"success": True, "data": nb}

    def delete_notebook(self, notebook_id: str) -> dict:
        if notebook_id not in self.notebooks:
            return {"success": False, "error": "Notebook not found"}
        del self.notebooks[notebook_id]
        return {"success": True, "deleted_id": notebook_id}

    def share_note(self, note_id: str, share_type: str, user_email: str = None, permission: str = "view") -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["is_shared"] = True
        note["share_url"] = f"https://note.example.com/share/{note_id}"
        return {"success": True, "share_url": note["share_url"]}

    def unshare_note(self, note_id: str, user_email: str = None) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["is_shared"] = False
        note["share_url"] = ""
        return {"success": True, "data": note}

    def pin_note(self, note_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["is_pinned"] = True
        return {"success": True, "data": note}

    def unpin_note(self, note_id: str) -> dict:
        note = self.notes.get(note_id)
        if not note:
            return {"success": False, "error": "Note not found"}
        note["is_pinned"] = False
        return {"success": True, "data": note}
