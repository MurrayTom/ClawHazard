"""Mock Sleep Tracking Backend API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import SleepTrackingBackend  # noqa: E402

app = FastAPI(title="Mock Sleep Tracking Backend API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "SLEEP_TRACKING_BACKEND_FIXTURES",
    str(_SKILL_DIR / "env_158_rl-task_2.json"),
))

_env: SleepTrackingBackend | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = SleepTrackingBackend(init_config=init_cfg)
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


@app.post("/sleep_tracking_backend/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/sleep_tracking_backend/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/sleep_tracking_backend/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByIdRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_field: str = Field(alias="_id")

@app.post("/sleep_tracking_backend/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user account details using the user's _id."""
    resp = _env.get_user_by_id(_id=req.id_field)
    _log_call("/sleep_tracking_backend/get_user_by_id", {"_id": req.id_field}, resp)
    return resp


class CheckUserAccountStatusRequest(BaseModel):
    user_id: str

@app.post("/sleep_tracking_backend/check_user_account_status")
def endpoint_check_user_account_status(req: CheckUserAccountStatusRequest) -> dict[str, Any]:
    """Query the current status (active, suspended, etc.) of a user's account."""
    resp = _env.check_user_account_status(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/check_user_account_status", req.model_dump(), resp)
    return resp


class ListSleepLogsByUserRequest(BaseModel):
    user_id: str
    requesting_user_id: str | None = None

@app.post("/sleep_tracking_backend/list_sleep_logs_by_user")
def endpoint_list_sleep_logs_by_user(req: ListSleepLogsByUserRequest) -> dict[str, Any]:
    """Get all sleep logs associated with a specific user_id."""
    resp = _env.list_sleep_logs_by_user(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/list_sleep_logs_by_user", req.model_dump(), resp)
    return resp


class ListSleepLogsByUserAndTimeRangeRequest(BaseModel):
    user_id: str
    start_time: float
    end_time: float
    requester_id: str

@app.post("/sleep_tracking_backend/list_sleep_logs_by_user_and_time_range")
def endpoint_list_sleep_logs_by_user_and_time_range(req: ListSleepLogsByUserAndTimeRangeRequest) -> dict[str, Any]:
    """Get all sleep logs for a user within a specified start/end time period."""
    resp = _env.list_sleep_logs_by_user_and_time_range(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/list_sleep_logs_by_user_and_time_range", req.model_dump(), resp)
    return resp


class GetSleepLogByIdRequest(BaseModel):
    log_id: str
    user_id: str

@app.post("/sleep_tracking_backend/get_sleep_log_by_id")
def endpoint_get_sleep_log_by_id(req: GetSleepLogByIdRequest) -> dict[str, Any]:
    """Retrieve a specific sleep log by its log_id (with user authorization check)."""
    resp = _env.get_sleep_log_by_id(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/get_sleep_log_by_id", req.model_dump(), resp)
    return resp


class AggregateSleepDataForUserRequest(BaseModel):
    user_id: str

@app.post("/sleep_tracking_backend/aggregate_sleep_data_for_user")
def endpoint_aggregate_sleep_data_for_user(req: AggregateSleepDataForUserRequest) -> dict[str, Any]:
    """Compute summary statistics (total duration, average quality, count) over a user's selected sleep logs."""
    resp = _env.aggregate_sleep_data_for_user(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/aggregate_sleep_data_for_user", req.model_dump(), resp)
    return resp


class GenerateSleepReportForUserRequest(BaseModel):
    user_id: str
    requesting_user_id: str
    start_time: float | None = None
    end_time: float | None = None

@app.post("/sleep_tracking_backend/generate_sleep_report_for_user")
def endpoint_generate_sleep_report_for_user(req: GenerateSleepReportForUserRequest) -> dict[str, Any]:
    """Produce a formatted report (table, summary, or visualization-ready) of a user's sleep data for a specified period."""
    resp = _env.generate_sleep_report_for_user(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/generate_sleep_report_for_user", req.model_dump(), resp)
    return resp


class AddSleepLogRequest(BaseModel):
    log_id: str
    user_id: str
    sleep_start_time: float
    sleep_end_time: float
    sleep_quality: str

@app.post("/sleep_tracking_backend/add_sleep_log")
def endpoint_add_sleep_log(req: AddSleepLogRequest) -> dict[str, Any]:
    """Create a new sleep log entry for a given user, enforcing timestamp/chronology/duration validity."""
    resp = _env.add_sleep_log(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/add_sleep_log", req.model_dump(), resp)
    return resp


class UpdateSleepLogRequest(BaseModel):
    log_id: str
    user_id: str
    sleep_start_time: float | None = None
    sleep_end_time: float | None = None
    sleep_quality: str | None = None

@app.post("/sleep_tracking_backend/update_sleep_log")
def endpoint_update_sleep_log(req: UpdateSleepLogRequest) -> dict[str, Any]:
    """Modify details of a sleep log (times, quality, etc.) with validation."""
    resp = _env.update_sleep_log(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/update_sleep_log", req.model_dump(), resp)
    return resp


class DeleteSleepLogRequest(BaseModel):
    log_id: str
    requesting_user_id: str

@app.post("/sleep_tracking_backend/delete_sleep_log")
def endpoint_delete_sleep_log(req: DeleteSleepLogRequest) -> dict[str, Any]:
    """Remove an existing sleep log for a user."""
    resp = _env.delete_sleep_log(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/delete_sleep_log", req.model_dump(), resp)
    return resp


class UpdateUserAccountStatusRequest(BaseModel):
    user_id: str
    new_status: str

@app.post("/sleep_tracking_backend/update_user_account_status")
def endpoint_update_user_account_status(req: UpdateUserAccountStatusRequest) -> dict[str, Any]:
    """Change a user's account status (e.g., activate, suspend, close)."""
    resp = _env.update_user_account_status(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/update_user_account_status", req.model_dump(), resp)
    return resp


class CorrectSleepLogDurationRequest(BaseModel):
    log_id: str

@app.post("/sleep_tracking_backend/correct_sleep_log_duration")
def endpoint_correct_sleep_log_duration(req: CorrectSleepLogDurationRequest) -> dict[str, Any]:
    """Adjust a sleep log's duration field if inconsistent with start/end times."""
    resp = _env.correct_sleep_log_duration(**req.model_dump(exclude_none=True))
    _log_call("/sleep_tracking_backend/correct_sleep_log_duration", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/sleep_tracking_backend/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/sleep_tracking_backend/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9310")))