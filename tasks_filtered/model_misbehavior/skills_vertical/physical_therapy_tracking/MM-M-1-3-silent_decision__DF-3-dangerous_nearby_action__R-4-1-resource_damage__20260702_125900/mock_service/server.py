"""Mock Physical Therapy Tracking API service (FastAPI)."""

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

from env_class import PhysicalTherapyTrackingApplication  # noqa: E402

app = FastAPI(title="Mock Physical Therapy Tracking API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PHYSICAL_THERAPY_TRACKING_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: PhysicalTherapyTrackingApplication | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = PhysicalTherapyTrackingApplication(init_config=init_cfg)
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


@app.post("/physical_therapy_tracking/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/physical_therapy_tracking/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/physical_therapy_tracking/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByNameRequest(BaseModel):
    name: str

@app.post("/physical_therapy_tracking/get_user_by_name")
def endpoint_get_user_by_name(req: GetUserByNameRequest) -> dict[str, Any]:
    """Retrieve user information given a name."""
    resp = _env.get_user_by_name(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_user_by_name", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/physical_therapy_tracking/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user information given a user ID."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_user_by_id", req.model_dump(), resp)
    return resp


@app.post("/physical_therapy_tracking/list_all_users")
def endpoint_list_all_users() -> dict[str, Any]:
    """List all registered users (patients, therapists)."""
    resp = _env.list_all_users()
    _log_call("/physical_therapy_tracking/list_all_users", {}, resp)
    return resp


class GetUserRoleRequest(BaseModel):
    user_id: str

@app.post("/physical_therapy_tracking/get_user_role")
def endpoint_get_user_role(req: GetUserRoleRequest) -> dict[str, Any]:
    """Query whether a user is a patient or a therapist."""
    resp = _env.get_user_role(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_user_role", req.model_dump(), resp)
    return resp


class ListSessionsByUserRequest(BaseModel):
    user_id: str

@app.post("/physical_therapy_tracking/list_sessions_by_user")
def endpoint_list_sessions_by_user(req: ListSessionsByUserRequest) -> dict[str, Any]:
    """Get all therapy sessions associated with a specific user."""
    resp = _env.list_sessions_by_user(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/list_sessions_by_user", req.model_dump(), resp)
    return resp


class GetSessionByDateRequest(BaseModel):
    user_id: str
    date: str

@app.post("/physical_therapy_tracking/get_session_by_date")
def endpoint_get_session_by_date(req: GetSessionByDateRequest) -> dict[str, Any]:
    """Find a session for a user on a specific date."""
    resp = _env.get_session_by_date(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_session_by_date", req.model_dump(), resp)
    return resp


class GetSessionByIdRequest(BaseModel):
    session_id: str

@app.post("/physical_therapy_tracking/get_session_by_id")
def endpoint_get_session_by_id(req: GetSessionByIdRequest) -> dict[str, Any]:
    """Retrieve full details of a therapy session given its session_id."""
    resp = _env.get_session_by_id(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_session_by_id", req.model_dump(), resp)
    return resp


@app.post("/physical_therapy_tracking/list_exercises")
def endpoint_list_exercises() -> dict[str, Any]:
    """List all available exercises in the system."""
    resp = _env.list_exercises()
    _log_call("/physical_therapy_tracking/list_exercises", {}, resp)
    return resp


class GetExerciseByIdRequest(BaseModel):
    exercise_id: str

@app.post("/physical_therapy_tracking/get_exercise_by_id")
def endpoint_get_exercise_by_id(req: GetExerciseByIdRequest) -> dict[str, Any]:
    """Get details (name, description, category) of a specific exercise."""
    resp = _env.get_exercise_by_id(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_exercise_by_id", req.model_dump(), resp)
    return resp


class ListSessionExercisesRequest(BaseModel):
    session_id: str

@app.post("/physical_therapy_tracking/list_session_exercises")
def endpoint_list_session_exercises(req: ListSessionExercisesRequest) -> dict[str, Any]:
    """List all exercises logged for a given session."""
    resp = _env.list_session_exercises(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/list_session_exercises", req.model_dump(), resp)
    return resp


class GetSessionExerciseDetailsRequest(BaseModel):
    session_id: str
    exercise_id: str

@app.post("/physical_therapy_tracking/get_session_exercise_details")
def endpoint_get_session_exercise_details(req: GetSessionExerciseDetailsRequest) -> dict[str, Any]:
    """Retrieve sets/repetitions/intensity/progress details for a session-exercise pairing."""
    resp = _env.get_session_exercise_details(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/get_session_exercise_details", req.model_dump(), resp)
    return resp


class CreateTherapySessionRequest(BaseModel):
    user_id: str
    date: str
    duration: float
    notes: str | None = None
    actor_id: str | None = None

@app.post("/physical_therapy_tracking/create_therapy_session")
def endpoint_create_therapy_session(req: CreateTherapySessionRequest) -> dict[str, Any]:
    """Create a new therapy session for a user on a specified date and duration."""
    resp = _env.create_therapy_session(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/create_therapy_session", req.model_dump(), resp)
    return resp


class AddExerciseToSessionRequest(BaseModel):
    session_id: str
    exercise_id: str
    repetitions: int
    sets: int
    intensity: int

@app.post("/physical_therapy_tracking/add_exercise_to_session")
def endpoint_add_exercise_to_session(req: AddExerciseToSessionRequest) -> dict[str, Any]:
    """Associate an exercise with a session with specific repetitions, sets, and intensity."""
    resp = _env.add_exercise_to_session(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/add_exercise_to_session", req.model_dump(), resp)
    return resp


class AppendProgressNoteRequest(BaseModel):
    session_id: str
    exercise_id: str
    note: str
    operator_user_id: str

@app.post("/physical_therapy_tracking/append_progress_note")
def endpoint_append_progress_note(req: AppendProgressNoteRequest) -> dict[str, Any]:
    """Add a new progress note to an existing session-exercise (cannot overwrite)."""
    resp = _env.append_progress_note(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/append_progress_note", req.model_dump(), resp)
    return resp


class UpdateSessionDetailsRequest(BaseModel):
    session_id: str
    actor_id: str
    duration: float | None = None
    notes: str | None = None

@app.post("/physical_therapy_tracking/update_session_details")
def endpoint_update_session_details(req: UpdateSessionDetailsRequest) -> dict[str, Any]:
    """Update the session attributes (duration, notes) if the actor is a therapist or owner."""
    resp = _env.update_session_details(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/update_session_details", req.model_dump(), resp)
    return resp


class UpdateSessionExerciseParametersRequest(BaseModel):
    session_id: str
    exercise_id: str
    user_id: str
    repetitions: int | None = None
    sets: int | None = None
    intensity: int | None = None

@app.post("/physical_therapy_tracking/update_session_exercise_parameters")
def endpoint_update_session_exercise_parameters(req: UpdateSessionExerciseParametersRequest) -> dict[str, Any]:
    """Modify the repetitions, sets, or intensity of a session-exercise (if permitted)."""
    resp = _env.update_session_exercise_parameters(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/update_session_exercise_parameters", req.model_dump(), resp)
    return resp


class DeleteSessionExerciseRequest(BaseModel):
    session_id: str
    exercise_id: str
    request_user_id: str

@app.post("/physical_therapy_tracking/delete_session_exercise")
def endpoint_delete_session_exercise(req: DeleteSessionExerciseRequest) -> dict[str, Any]:
    """Remove an exercise entry from a specific therapy session (if permitted)."""
    resp = _env.delete_session_exercise(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/delete_session_exercise", req.model_dump(), resp)
    return resp


class DeleteTherapySessionRequest(BaseModel):
    session_id: str
    requester_id: str

@app.post("/physical_therapy_tracking/delete_therapy_session")
def endpoint_delete_therapy_session(req: DeleteTherapySessionRequest) -> dict[str, Any]:
    """Remove an entire therapy session (if permitted by therapist/owner rules)."""
    resp = _env.delete_therapy_session(**req.model_dump(exclude_none=True))
    _log_call("/physical_therapy_tracking/delete_therapy_session", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/physical_therapy_tracking/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/physical_therapy_tracking/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9306")))
