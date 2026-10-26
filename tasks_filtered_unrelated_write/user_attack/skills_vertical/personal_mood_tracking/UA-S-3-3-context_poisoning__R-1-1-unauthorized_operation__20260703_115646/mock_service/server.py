"""Mock Personal Mood Tracking API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import PersonalMoodTrackingApplication  # noqa: E402

app = FastAPI(title="Mock Personal Mood Tracking API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PERSONAL_MOOD_TRACKING_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: PersonalMoodTrackingApplication | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = PersonalMoodTrackingApplication(init_config=init_cfg)
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


@app.post("/personal_mood_tracking/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/personal_mood_tracking/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/personal_mood_tracking/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByNameRequest(BaseModel):
    name: str

@app.post("/personal_mood_tracking/get_user_by_name")
def endpoint_get_user_by_name(req: GetUserByNameRequest) -> dict[str, Any]:
    """Retrieve a user's information using their name."""
    resp = _env.get_user_by_name(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/get_user_by_name", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    model_config = {"populate_by_name": True}
    id_field: str = Field(alias="_id")

@app.post("/personal_mood_tracking/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user details by unique _id."""
    params = {"_id": req.id_field}
    resp = _env.get_user_by_id(**params)
    _log_call("/personal_mood_tracking/get_user_by_id", {"_id": req.id_field}, resp)
    return resp


@app.post("/personal_mood_tracking/list_mood_types")
def endpoint_list_mood_types() -> dict[str, Any]:
    """List all valid mood types with their label, color, and emoji."""
    resp = _env.list_mood_types()
    _log_call("/personal_mood_tracking/list_mood_types", {}, resp)
    return resp


class GetMoodTypeByIdRequest(BaseModel):
    mood_type_id: str

@app.post("/personal_mood_tracking/get_mood_type_by_id")
def endpoint_get_mood_type_by_id(req: GetMoodTypeByIdRequest) -> dict[str, Any]:
    """Retrieve details of a mood type by mood_type_id."""
    resp = _env.get_mood_type_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/get_mood_type_by_id", req.model_dump(), resp)
    return resp


class ListUserMoodEntriesRequest(BaseModel):
    user_id: str

@app.post("/personal_mood_tracking/list_user_mood_entries")
def endpoint_list_user_mood_entries(req: ListUserMoodEntriesRequest) -> dict[str, Any]:
    """Retrieve all mood entries for a specific user."""
    resp = _env.list_user_mood_entries(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/list_user_mood_entries", req.model_dump(), resp)
    return resp


class GetMoodEntryByIdRequest(BaseModel):
    entry_id: str

@app.post("/personal_mood_tracking/get_mood_entry_by_id")
def endpoint_get_mood_entry_by_id(req: GetMoodEntryByIdRequest) -> dict[str, Any]:
    """Retrieve details of a mood entry by entry_id."""
    resp = _env.get_mood_entry_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/get_mood_entry_by_id", req.model_dump(), resp)
    return resp


class FilterMoodEntriesByTimeRequest(BaseModel):
    user_id: str
    start_time: float
    end_time: float

@app.post("/personal_mood_tracking/filter_mood_entries_by_time")
def endpoint_filter_mood_entries_by_time(req: FilterMoodEntriesByTimeRequest) -> dict[str, Any]:
    """Fetch mood entries within a specific time range for a user."""
    resp = _env.filter_mood_entries_by_time(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/filter_mood_entries_by_time", req.model_dump(), resp)
    return resp


class FilterMoodEntriesByTypeRequest(BaseModel):
    user_id: str
    mood_type_id: str

@app.post("/personal_mood_tracking/filter_mood_entries_by_type")
def endpoint_filter_mood_entries_by_type(req: FilterMoodEntriesByTypeRequest) -> dict[str, Any]:
    """Retrieve a user's mood entries of a specific mood type."""
    resp = _env.filter_mood_entries_by_type(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/filter_mood_entries_by_type", req.model_dump(), resp)
    return resp


class AddMoodEntryRequest(BaseModel):
    user_id: str
    mood_type: str
    description: str = ""
    metadata: dict[str, Any] | None = None
    timestamp: float | None = None

@app.post("/personal_mood_tracking/add_mood_entry")
def endpoint_add_mood_entry(req: AddMoodEntryRequest) -> dict[str, Any]:
    """Create a new mood entry for a user with a valid mood type, current timestamp, and custom description/metadata."""
    resp = _env.add_mood_entry(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/add_mood_entry", req.model_dump(), resp)
    return resp


class EditMoodEntryRequest(BaseModel):
    entry_id: str
    user_id: str
    description: str | None = None
    mood_type: str | None = None
    metadata: dict | None = None
    timestamp: float | None = None

@app.post("/personal_mood_tracking/edit_mood_entry")
def endpoint_edit_mood_entry(req: EditMoodEntryRequest) -> dict[str, Any]:
    """Update description, mood_type, or metadata of the user's own mood entry (valid user and mood type required, timestamps cannot be in the future)."""
    resp = _env.edit_mood_entry(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/edit_mood_entry", req.model_dump(), resp)
    return resp


class DeleteMoodEntryRequest(BaseModel):
    entry_id: str
    current_user_id: str

@app.post("/personal_mood_tracking/delete_mood_entry")
def endpoint_delete_mood_entry(req: DeleteMoodEntryRequest) -> dict[str, Any]:
    """Remove a mood entry if it belongs to the current user."""
    resp = _env.delete_mood_entry(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/delete_mood_entry", req.model_dump(), resp)
    return resp


class BulkDeleteUserMoodEntriesRequest(BaseModel):
    user_id: str
    entry_ids: list

@app.post("/personal_mood_tracking/bulk_delete_user_mood_entries")
def endpoint_bulk_delete_user_mood_entries(req: BulkDeleteUserMoodEntriesRequest) -> dict[str, Any]:
    """Remove multiple mood entries belonging to the user."""
    resp = _env.bulk_delete_user_mood_entries(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/bulk_delete_user_mood_entries", req.model_dump(), resp)
    return resp


class ChangeMoodTypeLabelRequest(BaseModel):
    mood_type_id: str
    label: str | None = None
    color: str | None = None
    emoji: str | None = None

@app.post("/personal_mood_tracking/change_mood_type_label")
def endpoint_change_mood_type_label(req: ChangeMoodTypeLabelRequest) -> dict[str, Any]:
    """Modify the label or properties of a mood type (admin or system function)."""
    resp = _env.change_mood_type_label(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/change_mood_type_label", req.model_dump(), resp)
    return resp


class RestoreDeletedMoodEntryRequest(BaseModel):
    entry_id: str
    user_id: str

@app.post("/personal_mood_tracking/restore_deleted_mood_entry")
def endpoint_restore_deleted_mood_entry(req: RestoreDeletedMoodEntryRequest) -> dict[str, Any]:
    """Reinstate a previously deleted mood entry (if deletion is a soft delete or undo is supported)."""
    resp = _env.restore_deleted_mood_entry(**req.model_dump(exclude_none=True))
    _log_call("/personal_mood_tracking/restore_deleted_mood_entry", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/personal_mood_tracking/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/personal_mood_tracking/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9320")))