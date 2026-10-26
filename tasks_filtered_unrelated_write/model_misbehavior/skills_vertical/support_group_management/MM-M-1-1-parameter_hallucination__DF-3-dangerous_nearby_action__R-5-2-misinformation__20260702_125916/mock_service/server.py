"""Mock Support Group Management API service (FastAPI)."""

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

from env_class import SupportGroupManagementSystem  # noqa: E402

app = FastAPI(title="Mock Support Group Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "SUPPORT_GROUP_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: SupportGroupManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = SupportGroupManagementSystem(init_config=init_cfg)
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


@app.post("/support_group_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/support_group_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/support_group_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class FindParticipantByNameRequest(BaseModel):
    name: str

@app.post("/support_group_management/find_participant_by_name")
def endpoint_find_participant_by_name(req: FindParticipantByNameRequest) -> dict[str, Any]:
    """Retrieve participant information given their name (e.g., Sarah)."""
    resp = _env.find_participant_by_name(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/find_participant_by_name", req.model_dump(), resp)
    return resp


class GetParticipantByIdRequest(BaseModel):
    participant_id: str

@app.post("/support_group_management/get_participant_by_id")
def endpoint_get_participant_by_id(req: GetParticipantByIdRequest) -> dict[str, Any]:
    """Get full details of a participant using their participant_id."""
    resp = _env.get_participant_by_id(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_participant_by_id", req.model_dump(), resp)
    return resp


@app.post("/support_group_management/list_all_participants")
def endpoint_list_all_participants() -> dict[str, Any]:
    """List all registered participants in the system."""
    resp = _env.list_all_participants()
    _log_call("/support_group_management/list_all_participants", {}, resp)
    return resp


class GetMeetingByTopicRequest(BaseModel):
    topic: str

@app.post("/support_group_management/get_meeting_by_topic")
def endpoint_get_meeting_by_topic(req: GetMeetingByTopicRequest) -> dict[str, Any]:
    """Search/return meetings (meeting_id, time, venue) matching a given topic."""
    resp = _env.get_meeting_by_topic(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_by_topic", req.model_dump(), resp)
    return resp


class GetMeetingByScheduleAndVenueRequest(BaseModel):
    schedule: str
    venue_id: str

@app.post("/support_group_management/get_meeting_by_schedule_and_venue")
def endpoint_get_meeting_by_schedule_and_venue(req: GetMeetingByScheduleAndVenueRequest) -> dict[str, Any]:
    """Find meetings scheduled at a given time and venue."""
    resp = _env.get_meeting_by_schedule_and_venue(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_by_schedule_and_venue", req.model_dump(), resp)
    return resp


class GetMeetingByCodeRequest(BaseModel):
    meeting_code: str

@app.post("/support_group_management/get_meeting_by_code")
def endpoint_get_meeting_by_code(req: GetMeetingByCodeRequest) -> dict[str, Any]:
    """Retrieve meeting details given a meeting_code."""
    resp = _env.get_meeting_by_code(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_by_code", req.model_dump(), resp)
    return resp


class GetMeetingDetailsRequest(BaseModel):
    meeting_id: str

@app.post("/support_group_management/get_meeting_details")
def endpoint_get_meeting_details(req: GetMeetingDetailsRequest) -> dict[str, Any]:
    """Get details (topic, schedule, venue, capacity, participants, code) of a meeting by meeting_id."""
    resp = _env.get_meeting_details(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_details", req.model_dump(), resp)
    return resp


class GetMeetingParticipantsRequest(BaseModel):
    meeting_id: str

@app.post("/support_group_management/get_meeting_participants")
def endpoint_get_meeting_participants(req: GetMeetingParticipantsRequest) -> dict[str, Any]:
    """List current participants in a given meeting."""
    resp = _env.get_meeting_participants(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_participants", req.model_dump(), resp)
    return resp


class GetVenueByAddressRequest(BaseModel):
    address: str

@app.post("/support_group_management/get_venue_by_address")
def endpoint_get_venue_by_address(req: GetVenueByAddressRequest) -> dict[str, Any]:
    """Retrieve venue information using a street address."""
    resp = _env.get_venue_by_address(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_venue_by_address", req.model_dump(), resp)
    return resp


class GetVenueDetailsRequest(BaseModel):
    venue_id: str

@app.post("/support_group_management/get_venue_details")
def endpoint_get_venue_details(req: GetVenueDetailsRequest) -> dict[str, Any]:
    """Get venue details (address, room, capacity) by venue_id."""
    resp = _env.get_venue_details(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_venue_details", req.model_dump(), resp)
    return resp


class GetMeetingCapacityRequest(BaseModel):
    meeting_id: str

@app.post("/support_group_management/get_meeting_capacity")
def endpoint_get_meeting_capacity(req: GetMeetingCapacityRequest) -> dict[str, Any]:
    """Query the capacity of the venue hosting a meeting."""
    resp = _env.get_meeting_capacity(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_capacity", req.model_dump(), resp)
    return resp


class GetMeetingAttendanceHistoryRequest(BaseModel):
    meeting_id: str

@app.post("/support_group_management/get_meeting_attendance_history")
def endpoint_get_meeting_attendance_history(req: GetMeetingAttendanceHistoryRequest) -> dict[str, Any]:
    """Retrieve past attendance/join records for a given meeting."""
    resp = _env.get_meeting_attendance_history(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/get_meeting_attendance_history", req.model_dump(), resp)
    return resp


class RegisterNewParticipantRequest(BaseModel):
    participant_id: str
    name: str
    contact_info: str
    registration_status: str = "registered"

@app.post("/support_group_management/register_new_participant")
def endpoint_register_new_participant(req: RegisterNewParticipantRequest) -> dict[str, Any]:
    """Register a new participant in the system (e.g., Sarah if not already present)."""
    resp = _env.register_new_participant(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/register_new_participant", req.model_dump(), resp)
    return resp


class JoinMeetingRequest(BaseModel):
    meeting_id: str
    participant_id: str
    meeting_code: str

@app.post("/support_group_management/join_meeting")
def endpoint_join_meeting(req: JoinMeetingRequest) -> dict[str, Any]:
    """Participant attempts to join a meeting (must provide correct code; system checks capacity and updates participant list/attendance)."""
    resp = _env.join_meeting(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/join_meeting", req.model_dump(), resp)
    return resp


class LeaveMeetingRequest(BaseModel):
    meeting_id: str
    participant_id: str

@app.post("/support_group_management/leave_meeting")
def endpoint_leave_meeting(req: LeaveMeetingRequest) -> dict[str, Any]:
    """Remove a participant from a meeting’s participant list and update attendance status."""
    resp = _env.leave_meeting(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/leave_meeting", req.model_dump(), resp)
    return resp


class CreateMeetingRequest(BaseModel):
    topic: str
    schedule: str
    venue_id: str
    recurrence_pattern: str
    meeting_code: str

@app.post("/support_group_management/create_meeting")
def endpoint_create_meeting(req: CreateMeetingRequest) -> dict[str, Any]:
    """Schedule a new meeting with topic, time, venue, recurrence, and unique code."""
    resp = _env.create_meeting(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/create_meeting", req.model_dump(), resp)
    return resp


class EditMeetingDetailsRequest(BaseModel):
    meeting_id: str
    topic: str | None = None
    schedule: str | None = None
    venue: str | None = None
    meeting_code: str | None = None
    recurrence_pattern: str | None = None

@app.post("/support_group_management/edit_meeting_details")
def endpoint_edit_meeting_details(req: EditMeetingDetailsRequest) -> dict[str, Any]:
    """Update meeting information (topic, time, code, venue, etc.)."""
    resp = _env.edit_meeting_details(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/edit_meeting_details", req.model_dump(), resp)
    return resp


class CreateVenueRequest(BaseModel):
    venue_id: str
    address: str
    room_number: str
    capacity: int

@app.post("/support_group_management/create_venue")
def endpoint_create_venue(req: CreateVenueRequest) -> dict[str, Any]:
    """Add a new venue location into the system."""
    resp = _env.create_venue(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/create_venue", req.model_dump(), resp)
    return resp


class UpdateParticipantStatusRequest(BaseModel):
    participant_id: str
    new_status: str

@app.post("/support_group_management/update_participant_status")
def endpoint_update_participant_status(req: UpdateParticipantStatusRequest) -> dict[str, Any]:
    """Change or update a participant’s registration status."""
    resp = _env.update_participant_status(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/update_participant_status", req.model_dump(), resp)
    return resp


class RemoveParticipantRequest(BaseModel):
    participant_id: str

@app.post("/support_group_management/remove_participant")
def endpoint_remove_participant(req: RemoveParticipantRequest) -> dict[str, Any]:
    """Delete a participant entirely from the system."""
    resp = _env.remove_participant(**req.model_dump(exclude_none=True))
    _log_call("/support_group_management/remove_participant", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/support_group_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/support_group_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9324")))
