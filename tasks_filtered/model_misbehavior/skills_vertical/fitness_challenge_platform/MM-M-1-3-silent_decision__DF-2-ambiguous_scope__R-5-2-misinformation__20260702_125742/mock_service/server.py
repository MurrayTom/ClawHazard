"""Mock Fitness Challenge Platform API service (FastAPI)."""

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

from env_class import FitnessChallengePlatform  # noqa: E402

app = FastAPI(title="Mock Fitness Challenge Platform API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "FITNESS_CHALLENGE_PLATFORM_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: FitnessChallengePlatform | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = FitnessChallengePlatform(init_config=init_cfg)
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


@app.post("/fitness_challenge_platform/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/fitness_challenge_platform/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/fitness_challenge_platform/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByUsernameRequest(BaseModel):
    username: str

@app.post("/fitness_challenge_platform/get_user_by_username")
def endpoint_get_user_by_username(req: GetUserByUsernameRequest) -> dict[str, Any]:
    """Retrieve a user's information using their username."""
    resp = _env.get_user_by_username(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_user_by_username", req.model_dump(), resp)
    return resp


class GetUserByEmailRequest(BaseModel):
    email: str

@app.post("/fitness_challenge_platform/get_user_by_email")
def endpoint_get_user_by_email(req: GetUserByEmailRequest) -> dict[str, Any]:
    """Retrieve a user's information using their email."""
    resp = _env.get_user_by_email(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_user_by_email", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    model_config = {"populate_by_name": True}
    id: str = Field(alias="_id")

@app.post("/fitness_challenge_platform/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve details for a user given their unique _id."""
    resp = _env.get_user_by_id(_id=req.id)
    _log_call("/fitness_challenge_platform/get_user_by_id", req.model_dump(by_alias=True), resp)
    return resp


@app.post("/fitness_challenge_platform/list_all_users")
def endpoint_list_all_users() -> dict[str, Any]:
    """Retrieve a list of all registered users."""
    resp = _env.list_all_users()
    _log_call("/fitness_challenge_platform/list_all_users", {}, resp)
    return resp


class CheckUserActiveStatusRequest(BaseModel):
    user_id: str

@app.post("/fitness_challenge_platform/check_user_active_status")
def endpoint_check_user_active_status(req: CheckUserActiveStatusRequest) -> dict[str, Any]:
    """Check if a given user account is activated/verified."""
    resp = _env.check_user_active_status(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/check_user_active_status", req.model_dump(), resp)
    return resp


@app.post("/fitness_challenge_platform/list_challenges")
def endpoint_list_challenges() -> dict[str, Any]:
    """Retrieve information on all challenges available."""
    resp = _env.list_challenges()
    _log_call("/fitness_challenge_platform/list_challenges", {}, resp)
    return resp


class GetChallengeByIdRequest(BaseModel):
    challenge_id: str

@app.post("/fitness_challenge_platform/get_challenge_by_id")
def endpoint_get_challenge_by_id(req: GetChallengeByIdRequest) -> dict[str, Any]:
    """Retrieve full details for a specific challenge."""
    resp = _env.get_challenge_by_id(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_challenge_by_id", req.model_dump(), resp)
    return resp


class GetUserActivityLogsRequest(BaseModel):
    user_id: str

@app.post("/fitness_challenge_platform/get_user_activity_logs")
def endpoint_get_user_activity_logs(req: GetUserActivityLogsRequest) -> dict[str, Any]:
    """List all activity logs associated with a particular user."""
    resp = _env.get_user_activity_logs(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_user_activity_logs", req.model_dump(), resp)
    return resp


class ListChallengeActivityLogsRequest(BaseModel):
    challenge_id: str

@app.post("/fitness_challenge_platform/list_challenge_activity_logs")
def endpoint_list_challenge_activity_logs(req: ListChallengeActivityLogsRequest) -> dict[str, Any]:
    """List all activity logs submitted for a specific challenge."""
    resp = _env.list_challenge_activity_logs(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/list_challenge_activity_logs", req.model_dump(), resp)
    return resp


class GetActivityLogByIdRequest(BaseModel):
    log_id: str

@app.post("/fitness_challenge_platform/get_activity_log_by_id")
def endpoint_get_activity_log_by_id(req: GetActivityLogByIdRequest) -> dict[str, Any]:
    """Retrieve the details of a specific activity log by log_id."""
    resp = _env.get_activity_log_by_id(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_activity_log_by_id", req.model_dump(), resp)
    return resp


class GetLeaderboardForChallengeRequest(BaseModel):
    challenge_id: str

@app.post("/fitness_challenge_platform/get_leaderboard_for_challenge")
def endpoint_get_leaderboard_for_challenge(req: GetLeaderboardForChallengeRequest) -> dict[str, Any]:
    """Retrieve the full leaderboard for a given challenge."""
    resp = _env.get_leaderboard_for_challenge(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_leaderboard_for_challenge", req.model_dump(), resp)
    return resp


class GetUserLeaderboardEntryRequest(BaseModel):
    challenge_id: str
    user_id: str

@app.post("/fitness_challenge_platform/get_user_leaderboard_entry")
def endpoint_get_user_leaderboard_entry(req: GetUserLeaderboardEntryRequest) -> dict[str, Any]:
    """Retrieve a user's leaderboard entry, score, and rank in a challenge."""
    resp = _env.get_user_leaderboard_entry(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/get_user_leaderboard_entry", req.model_dump(), resp)
    return resp


class CreateUserAccountRequest(BaseModel):
    username: str
    email: str
    password_hash: str
    profile_info: Any | None = None

@app.post("/fitness_challenge_platform/create_user_account")
def endpoint_create_user_account(req: CreateUserAccountRequest) -> dict[str, Any]:
    """Register a new user with unique username and email; set initial attributes."""
    resp = _env.create_user_account(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/create_user_account", req.model_dump(), resp)
    return resp


class ActivateUserAccountRequest(BaseModel):
    user_id: str

@app.post("/fitness_challenge_platform/activate_user_account")
def endpoint_activate_user_account(req: ActivateUserAccountRequest) -> dict[str, Any]:
    """Verify and activate a user account after registration."""
    resp = _env.activate_user_account(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/activate_user_account", req.model_dump(), resp)
    return resp


class UpdateUserProfileRequest(BaseModel):
    user_id: str
    profile_info: Any

@app.post("/fitness_challenge_platform/update_user_profile")
def endpoint_update_user_profile(req: UpdateUserProfileRequest) -> dict[str, Any]:
    """Modify a user's profile information."""
    resp = _env.update_user_profile(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/update_user_profile", req.model_dump(), resp)
    return resp


class CreateChallengeRequest(BaseModel):
    challenge_id: str
    name: str
    description: str
    start_date: str
    end_date: str
    criteria: str

@app.post("/fitness_challenge_platform/create_challenge")
def endpoint_create_challenge(req: CreateChallengeRequest) -> dict[str, Any]:
    """Add a new challenge event to the platform."""
    resp = _env.create_challenge(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/create_challenge", req.model_dump(), resp)
    return resp


class JoinChallengeRequest(BaseModel):
    user_id: str
    challenge_id: str

@app.post("/fitness_challenge_platform/join_challenge")
def endpoint_join_challenge(req: JoinChallengeRequest) -> dict[str, Any]:
    """Register an activated user as a participant in a challenge."""
    resp = _env.join_challenge(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/join_challenge", req.model_dump(), resp)
    return resp


class CreateActivityLogRequest(BaseModel):
    user_id: str
    challenge_id: str
    activity_type: str
    value: float
    timestamp: str

@app.post("/fitness_challenge_platform/create_activity_log")
def endpoint_create_activity_log(req: CreateActivityLogRequest) -> dict[str, Any]:
    """Submit a new activity log for a valid user-challenge pair."""
    resp = _env.create_activity_log(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/create_activity_log", req.model_dump(), resp)
    return resp


class UpdateLeaderboardEntryRequest(BaseModel):
    challenge_id: str
    user_id: str
    score: float
    rank: int

@app.post("/fitness_challenge_platform/update_leaderboard_entry")
def endpoint_update_leaderboard_entry(req: UpdateLeaderboardEntryRequest) -> dict[str, Any]:
    """Update a user's score and rank on the leaderboard after valid activity is logged."""
    resp = _env.update_leaderboard_entry(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/update_leaderboard_entry", req.model_dump(), resp)
    return resp


class DeactivateUserAccountRequest(BaseModel):
    user_id: str

@app.post("/fitness_challenge_platform/deactivate_user_account")
def endpoint_deactivate_user_account(req: DeactivateUserAccountRequest) -> dict[str, Any]:
    """Deactivate or suspend a user account (e.g., for admin or system rules)."""
    resp = _env.deactivate_user_account(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/deactivate_user_account", req.model_dump(), resp)
    return resp


class DeleteUserAccountRequest(BaseModel):
    user_id: str

@app.post("/fitness_challenge_platform/delete_user_account")
def endpoint_delete_user_account(req: DeleteUserAccountRequest) -> dict[str, Any]:
    """Permanently remove a user and their associated data from the system."""
    resp = _env.delete_user_account(**req.model_dump(exclude_none=True))
    _log_call("/fitness_challenge_platform/delete_user_account", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/fitness_challenge_platform/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/fitness_challenge_platform/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9307")))