"""Mock Web Browser Bookmark API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import WebBrowserBookmarkSystem  # noqa: E402

app = FastAPI(title="Mock Web Browser Bookmark API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "WEB_BROWSER_BOOKMARK_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: WebBrowserBookmarkSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = WebBrowserBookmarkSystem(init_config=init_cfg)
    # 将 init_config 中的各实体加载到环境实例
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, dict):
            setattr(_env, attr, val)
        elif hasattr(_env, attr) and isinstance(val, list):
            setattr(_env, attr, val)


_load_fixtures()


def _log_call(endpoint: str, request_body: dict[str, Any], response_body: Any) -> None:
    _audit_log.append({
        "endpoint": endpoint,
        "request_body": request_body,
        "response_body": response_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── 通用调用端点 ──────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    operation: str
    params: dict[str, Any] = {}


@app.post("/web_browser_bookmark/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/web_browser_bookmark/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/web_browser_bookmark/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

@app.post("/web_browser_bookmark/list_folders")
def endpoint_list_folders() -> dict[str, Any]:
    """Retrieve all folders available for organizing bookmarks."""
    resp = _env.list_folders()
    _log_call("/web_browser_bookmark/list_folders", {}, resp)
    return resp


class GetFolderByNameRequest(BaseModel):
    name: str

@app.post("/web_browser_bookmark/get_folder_by_name")
def endpoint_get_folder_by_name(req: GetFolderByNameRequest) -> dict[str, Any]:
    """Query details of a folder by its name."""
    resp = _env.get_folder_by_name(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/get_folder_by_name", req.model_dump(), resp)
    return resp


@app.post("/web_browser_bookmark/get_folder_hierarchy")
def endpoint_get_folder_hierarchy() -> dict[str, Any]:
    """Retrieve the folder nesting structure for navigation or organization."""
    resp = _env.get_folder_hierarchy()
    _log_call("/web_browser_bookmark/get_folder_hierarchy", {}, resp)
    return resp


class ListBookmarksInFolderRequest(BaseModel):
    folder_id: str

@app.post("/web_browser_bookmark/list_bookmarks_in_folder")
def endpoint_list_bookmarks_in_folder(req: ListBookmarksInFolderRequest) -> dict[str, Any]:
    """Retrieve all bookmarks in a given folder."""
    resp = _env.list_bookmarks_in_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/list_bookmarks_in_folder", req.model_dump(), resp)
    return resp


class FindBookmarkByUrlAndFolderRequest(BaseModel):
    url: str
    folder_id: str

@app.post("/web_browser_bookmark/find_bookmark_by_url_and_folder")
def endpoint_find_bookmark_by_url_and_folder(req: FindBookmarkByUrlAndFolderRequest) -> dict[str, Any]:
    """Find if a bookmark with a specific URL exists in a given folder (for duplicate check)."""
    resp = _env.find_bookmark_by_url_and_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/find_bookmark_by_url_and_folder", req.model_dump(), resp)
    return resp


@app.post("/web_browser_bookmark/list_tags")
def endpoint_list_tags() -> dict[str, Any]:
    """Retrieve all tags available for bookmarks."""
    resp = _env.list_tags()
    _log_call("/web_browser_bookmark/list_tags", {}, resp)
    return resp


class FindTagByNameRequest(BaseModel):
    name: str

@app.post("/web_browser_bookmark/find_tag_by_name")
def endpoint_find_tag_by_name(req: FindTagByNameRequest) -> dict[str, Any]:
    """Query tags by their human-readable name."""
    resp = _env.find_tag_by_name(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/find_tag_by_name", req.model_dump(), resp)
    return resp


class GetBookmarkByIdRequest(BaseModel):
    bookmark_id: str

@app.post("/web_browser_bookmark/get_bookmark_by_id")
def endpoint_get_bookmark_by_id(req: GetBookmarkByIdRequest) -> dict[str, Any]:
    """Retrieve full details of a bookmark given its ID."""
    resp = _env.get_bookmark_by_id(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/get_bookmark_by_id", req.model_dump(), resp)
    return resp


class ValidateUrlFormatRequest(BaseModel):
    url: str

@app.post("/web_browser_bookmark/validate_url_format")
def endpoint_validate_url_format(req: ValidateUrlFormatRequest) -> dict[str, Any]:
    """Verify that a given URL is valid per the system’s rules."""
    resp = _env.validate_url_format(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/validate_url_format", req.model_dump(), resp)
    return resp


class AddBookmarkRequest(BaseModel):
    title: str
    url: str
    folder_id: str
    tags: list[str]
    description: str = ""
    added_date: str | None = None

@app.post("/web_browser_bookmark/add_bookmark")
def endpoint_add_bookmark(req: AddBookmarkRequest) -> dict[str, Any]:
    """Save a new bookmark specifying its title, URL, folder, tags, and metadata."""
    resp = _env.add_bookmark(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/add_bookmark", req.model_dump(), resp)
    return resp


class CreateFolderRequest(BaseModel):
    name: str
    parent_folder_id: str | None = None

@app.post("/web_browser_bookmark/create_folder")
def endpoint_create_folder(req: CreateFolderRequest) -> dict[str, Any]:
    """Add a new folder (in a specified hierarchy) to organize bookmarks."""
    resp = _env.create_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/create_folder", req.model_dump(), resp)
    return resp


class CreateTagRequest(BaseModel):
    name: str

@app.post("/web_browser_bookmark/create_tag")
def endpoint_create_tag(req: CreateTagRequest) -> dict[str, Any]:
    """Add a new tag for categorizing bookmarks."""
    resp = _env.create_tag(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/create_tag", req.model_dump(), resp)
    return resp


class UpdateBookmarkRequest(BaseModel):
    bookmark_id: str
    title: str | None = None
    url: str | None = None
    folder_id: str | None = None
    tags: list[str] | None = None
    description: str | None = None

@app.post("/web_browser_bookmark/update_bookmark")
def endpoint_update_bookmark(req: UpdateBookmarkRequest) -> dict[str, Any]:
    """Modify details (title, URL, folder, description, tags) of an existing bookmark."""
    resp = _env.update_bookmark(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/update_bookmark", req.model_dump(), resp)
    return resp


class DeleteBookmarkRequest(BaseModel):
    bookmark_id: str

@app.post("/web_browser_bookmark/delete_bookmark")
def endpoint_delete_bookmark(req: DeleteBookmarkRequest) -> dict[str, Any]:
    """Remove a bookmark from the system."""
    resp = _env.delete_bookmark(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/delete_bookmark", req.model_dump(), resp)
    return resp


class MoveBookmarkToFolderRequest(BaseModel):
    bookmark_id: str
    target_folder_id: str

@app.post("/web_browser_bookmark/move_bookmark_to_folder")
def endpoint_move_bookmark_to_folder(req: MoveBookmarkToFolderRequest) -> dict[str, Any]:
    """Relocate a bookmark to a different folder."""
    resp = _env.move_bookmark_to_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/move_bookmark_to_folder", req.model_dump(), resp)
    return resp


class DeleteFolderRequest(BaseModel):
    folder_id: str

@app.post("/web_browser_bookmark/delete_folder")
def endpoint_delete_folder(req: DeleteFolderRequest) -> dict[str, Any]:
    """Delete a folder (with rules for handling contained bookmarks)."""
    resp = _env.delete_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/delete_folder", req.model_dump(), resp)
    return resp


class UpdateFolderRequest(BaseModel):
    folder_id: str
    name: str | None = None
    parent_folder_id: str | None = None

@app.post("/web_browser_bookmark/update_folder")
def endpoint_update_folder(req: UpdateFolderRequest) -> dict[str, Any]:
    """Change folder attributes (name, parent_folder_id)."""
    resp = _env.update_folder(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/update_folder", req.model_dump(), resp)
    return resp


class AddTagToBookmarkRequest(BaseModel):
    bookmark_id: str
    tag_id: str

@app.post("/web_browser_bookmark/add_tag_to_bookmark")
def endpoint_add_tag_to_bookmark(req: AddTagToBookmarkRequest) -> dict[str, Any]:
    """Associate a tag with a bookmark."""
    resp = _env.add_tag_to_bookmark(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/add_tag_to_bookmark", req.model_dump(), resp)
    return resp


class RemoveTagFromBookmarkRequest(BaseModel):
    bookmark_id: str
    tag_id: str

@app.post("/web_browser_bookmark/remove_tag_from_bookmark")
def endpoint_remove_tag_from_bookmark(req: RemoveTagFromBookmarkRequest) -> dict[str, Any]:
    """Remove association between a tag and a bookmark."""
    resp = _env.remove_tag_from_bookmark(**req.model_dump(exclude_none=True))
    _log_call("/web_browser_bookmark/remove_tag_from_bookmark", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/web_browser_bookmark/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/web_browser_bookmark/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9322")))
