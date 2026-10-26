"""Mock Pregnancy Health Tracking API service (FastAPI)."""

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

from env_class import PregnancyTrackingHealthManagementApp  # noqa: E402

app = FastAPI(title="Mock Pregnancy Health Tracking API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PREGNANCY_HEALTH_TRACKING_FIXTURES",
    str(_SKILL_DIR / "env_189_rl-task_1.json"),
))

_env: PregnancyTrackingHealthManagementApp | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = PregnancyTrackingHealthManagementApp(init_config=init_cfg)
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


@app.post("/pregnancy_health_tracking/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/pregnancy_health_tracking/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/pregnancy_health_tracking/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserInfoRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_user_info")
def endpoint_get_user_info(req: GetUserInfoRequest) -> dict[str, Any]:
    """Retrieve full user details by user identifier."""
    resp = _env.get_user_info(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_user_info", req.model_dump(), resp)
    return resp


class GetHealthLogsForUserRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_health_logs_for_user")
def endpoint_get_health_logs_for_user(req: GetHealthLogsForUserRequest) -> dict[str, Any]:
    """Retrieve all health metric logs (weights, symptoms, notes) for a user."""
    resp = _env.get_health_logs_for_user(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_health_logs_for_user", req.model_dump(), resp)
    return resp


class GetLatestHealthLogRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_latest_health_log")
def endpoint_get_latest_health_log(req: GetLatestHealthLogRequest) -> dict[str, Any]:
    """Get the most recent logged health metrics for a user."""
    resp = _env.get_latest_health_log(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_latest_health_log", req.model_dump(), resp)
    return resp


class ComputeAverageWeightGainRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/compute_average_weight_gain")
def endpoint_compute_average_weight_gain(req: ComputeAverageWeightGainRequest) -> dict[str, Any]:
    """Calculate the user's average weight gain since pre-pregnancy using all logged weights."""
    resp = _env.compute_average_weight_gain(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/compute_average_weight_gain", req.model_dump(), resp)
    return resp


class GetPregnancyStageForUserRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_pregnancy_stage_for_user")
def endpoint_get_pregnancy_stage_for_user(req: GetPregnancyStageForUserRequest) -> dict[str, Any]:
    """Compute and retrieve the current week and trimester of pregnancy for a user using their due date or pregnancy start date."""
    resp = _env.get_pregnancy_stage_for_user(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_pregnancy_stage_for_user", req.model_dump(), resp)
    return resp


class GetRecommendedWeightGainForStageRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_recommended_weight_gain_for_stage")
def endpoint_get_recommended_weight_gain_for_stage(req: GetRecommendedWeightGainForStageRequest) -> dict[str, Any]:
    """Retrieve the recommended min/max weight gain and guideline description for the user's current pregnancy stage."""
    resp = _env.get_recommended_weight_gain_for_stage(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_recommended_weight_gain_for_stage", req.model_dump(), resp)
    return resp


@app.post("/pregnancy_health_tracking/list_guidelines")
def endpoint_list_guidelines() -> dict[str, Any]:
    """Retrieve all available medical guidelines for different pregnancy stages."""
    resp = _env.list_guidelines()
    _log_call("/pregnancy_health_tracking/list_guidelines", {}, resp)
    return resp


class GetGuidelineByIdentifierRequest(BaseModel):
    age_identifier: str

@app.post("/pregnancy_health_tracking/get_guideline_by_identifier")
def endpoint_get_guideline_by_identifier(req: GetGuidelineByIdentifierRequest) -> dict[str, Any]:
    """Lookup a specific guideline using its age/stage identifier."""
    resp = _env.get_guideline_by_identifier(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_guideline_by_identifier", req.model_dump(), resp)
    return resp


class GetPrePregnancyWeightRequest(BaseModel):
    user_id: str

@app.post("/pregnancy_health_tracking/get_pre_pregnancy_weight")
def endpoint_get_pre_pregnancy_weight(req: GetPrePregnancyWeightRequest) -> dict[str, Any]:
    """Return the pre-pregnancy weight for a user."""
    resp = _env.get_pre_pregnancy_weight(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/get_pre_pregnancy_weight", req.model_dump(), resp)
    return resp


class AddHealthMetricLogRequest(BaseModel):
    user_id: str
    timestamp: str
    weight: float
    symptoms: list
    notes: str | None = None

@app.post("/pregnancy_health_tracking/add_health_metric_log")
def endpoint_add_health_metric_log(req: AddHealthMetricLogRequest) -> dict[str, Any]:
    """Add a new health metric log entry (with weight, symptoms, notes) for a user."""
    resp = _env.add_health_metric_log(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/add_health_metric_log", req.model_dump(), resp)
    return resp


class UpdateHealthMetricLogRequest(BaseModel):
    log_id: str
    timestamp: str | None = None
    weight: float | None = None
    symptoms: list[str] | None = None
    notes: str | None = None

@app.post("/pregnancy_health_tracking/update_health_metric_log")
def endpoint_update_health_metric_log(req: UpdateHealthMetricLogRequest) -> dict[str, Any]:
    """Edit or correct a previously logged health metric entry."""
    resp = _env.update_health_metric_log(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/update_health_metric_log", req.model_dump(), resp)
    return resp


class DeleteHealthMetricLogRequest(BaseModel):
    log_id: str

@app.post("/pregnancy_health_tracking/delete_health_metric_log")
def endpoint_delete_health_metric_log(req: DeleteHealthMetricLogRequest) -> dict[str, Any]:
    """Remove a specific health metric log."""
    resp = _env.delete_health_metric_log(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/delete_health_metric_log", req.model_dump(), resp)
    return resp


class UpdateUserInfoRequest(BaseModel):
    id: str = Field(..., alias="_id")
    update_data: dict

    model_config = {"populate_by_name": True}

@app.post("/pregnancy_health_tracking/update_user_info")
def endpoint_update_user_info(req: UpdateUserInfoRequest) -> dict[str, Any]:
    """Update user details (e.g., due date, pre-pregnancy weight, height)."""
    params = {"_id": req.id, "update_data": req.update_data}
    resp = _env.update_user_info(**params)
    _log_call("/pregnancy_health_tracking/update_user_info", params, resp)
    return resp


class AddOrUpdateGuidelineRequest(BaseModel):
    age_identifier: str
    recommended_min_gain: float
    recommended_max_gain: float
    description: str

@app.post("/pregnancy_health_tracking/add_or_update_guideline")
def endpoint_add_or_update_guideline(req: AddOrUpdateGuidelineRequest) -> dict[str, Any]:
    """Create or modify a medical guideline for a stage of pregnancy."""
    resp = _env.add_or_update_guideline(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/add_or_update_guideline", req.model_dump(), resp)
    return resp


class CorrectPregnancyStageRequest(BaseModel):
    user_id: str
    current_week: int
    current_trimester: int

@app.post("/pregnancy_health_tracking/correct_pregnancy_stage")
def endpoint_correct_pregnancy_stage(req: CorrectPregnancyStageRequest) -> dict[str, Any]:
    """Manually adjust a user's pregnancy stage in rare/exceptional cases."""
    resp = _env.correct_pregnancy_stage(**req.model_dump(exclude_none=True))
    _log_call("/pregnancy_health_tracking/correct_pregnancy_stage", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/pregnancy_health_tracking/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/pregnancy_health_tracking/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9329")))