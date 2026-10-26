"""Mock Personal Nutrition Tracking API service (FastAPI)."""

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

from env_class import PersonalNutritionTrackingApp  # noqa: E402

app = FastAPI(title="Mock Personal Nutrition Tracking API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PERSONAL_NUTRITION_TRACKING_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: PersonalNutritionTrackingApp | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = PersonalNutritionTrackingApp(init_config=init_cfg)
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


@app.post("/personal_nutrition_tracking/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/personal_nutrition_tracking/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/personal_nutrition_tracking/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByNameRequest(BaseModel):
    name: str

@app.post("/personal_nutrition_tracking/get_user_by_name")
def endpoint_get_user_by_name(req: GetUserByNameRequest) -> dict[str, Any]:
    """Retrieve user information using the user's name."""
    resp = _env.get_user_by_name(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_user_by_name", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/personal_nutrition_tracking/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user information using the user's unique _id."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_user_by_id", req.model_dump(), resp)
    return resp


@app.post("/personal_nutrition_tracking/list_all_users")
def endpoint_list_all_users() -> dict[str, Any]:
    """List all registered users in the app."""
    resp = _env.list_all_users()
    _log_call("/personal_nutrition_tracking/list_all_users", {}, resp)
    return resp


class GetMealRecordsByUserRequest(BaseModel):
    user_id: str

@app.post("/personal_nutrition_tracking/get_meal_records_by_user")
def endpoint_get_meal_records_by_user(req: GetMealRecordsByUserRequest) -> dict[str, Any]:
    """Retrieve all meal records linked to a specific user."""
    resp = _env.get_meal_records_by_user(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_meal_records_by_user", req.model_dump(), resp)
    return resp


class GetMealRecordsByDateRangeRequest(BaseModel):
    user_id: str
    start_time: str
    end_time: str

@app.post("/personal_nutrition_tracking/get_meal_records_by_date_range")
def endpoint_get_meal_records_by_date_range(req: GetMealRecordsByDateRangeRequest) -> dict[str, Any]:
    """Retrieve all meal records for a user in a specific time/date interval."""
    resp = _env.get_meal_records_by_date_range(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_meal_records_by_date_range", req.model_dump(), resp)
    return resp


class SearchMealRecordsByNameRequest(BaseModel):
    user_id: str
    meal_name: str

@app.post("/personal_nutrition_tracking/search_meal_records_by_name")
def endpoint_search_meal_records_by_name(req: SearchMealRecordsByNameRequest) -> dict[str, Any]:
    """Search for meal records of a user matching a meal name."""
    resp = _env.search_meal_records_by_name(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/search_meal_records_by_name", req.model_dump(), resp)
    return resp


class GetMealRecordByIdRequest(BaseModel):
    record_id: str

@app.post("/personal_nutrition_tracking/get_meal_record_by_id")
def endpoint_get_meal_record_by_id(req: GetMealRecordByIdRequest) -> dict[str, Any]:
    """Retrieve details of a specific meal record by record_id."""
    resp = _env.get_meal_record_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_meal_record_by_id", req.model_dump(), resp)
    return resp


class GetUserNutritionSummaryRequest(BaseModel):
    user_id: str
    start_date: str
    end_date: str

@app.post("/personal_nutrition_tracking/get_user_nutrition_summary")
def endpoint_get_user_nutrition_summary(req: GetUserNutritionSummaryRequest) -> dict[str, Any]:
    """Aggregate total calories and meal counts for a user over a given period."""
    resp = _env.get_user_nutrition_summary(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/get_user_nutrition_summary", req.model_dump(), resp)
    return resp


class AddMealRecordRequest(BaseModel):
    user_id: str
    meal_name: str
    calories: float
    consumed_at: str
    record_id: str | None = None

@app.post("/personal_nutrition_tracking/add_meal_record")
def endpoint_add_meal_record(req: AddMealRecordRequest) -> dict[str, Any]:
    """Create and store a new MealRecord for a user, with meal name, calorie value, and consumption time (validates constraints)."""
    resp = _env.add_meal_record(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/add_meal_record", req.model_dump(), resp)
    return resp


class UpdateMealRecordRequest(BaseModel):
    record_id: str
    meal_name: str | None = None
    calories: float | None = None
    consumed_at: str | None = None

@app.post("/personal_nutrition_tracking/update_meal_record")
def endpoint_update_meal_record(req: UpdateMealRecordRequest) -> dict[str, Any]:
    """Modify details of an existing MealRecord (e.g., calories, meal name, consumed_at)."""
    resp = _env.update_meal_record(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/update_meal_record", req.model_dump(), resp)
    return resp


class DeleteMealRecordRequest(BaseModel):
    record_id: str

@app.post("/personal_nutrition_tracking/delete_meal_record")
def endpoint_delete_meal_record(req: DeleteMealRecordRequest) -> dict[str, Any]:
    """Remove a meal record from the app for a user."""
    resp = _env.delete_meal_record(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/delete_meal_record", req.model_dump(), resp)
    return resp


class BulkAddMealRecordsRequest(BaseModel):
    user_id: str
    records: list[dict[str, Any]]

@app.post("/personal_nutrition_tracking/bulk_add_meal_records")
def endpoint_bulk_add_meal_records(req: BulkAddMealRecordsRequest) -> dict[str, Any]:
    """Add multiple meal records simultaneously for a user."""
    resp = _env.bulk_add_meal_records(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/bulk_add_meal_records", req.model_dump(), resp)
    return resp


class CorrectMealRecordTimestampRequest(BaseModel):
    record_id: str
    new_timestamp: str

@app.post("/personal_nutrition_tracking/correct_meal_record_timestamp")
def endpoint_correct_meal_record_timestamp(req: CorrectMealRecordTimestampRequest) -> dict[str, Any]:
    """Update the consumed_at timestamp of a meal record to ensure validity."""
    resp = _env.correct_meal_record_timestamp(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/correct_meal_record_timestamp", req.model_dump(), resp)
    return resp


class AdjustMealRecordCaloriesRequest(BaseModel):
    record_id: str
    new_calories: float

@app.post("/personal_nutrition_tracking/adjust_meal_record_calories")
def endpoint_adjust_meal_record_calories(req: AdjustMealRecordCaloriesRequest) -> dict[str, Any]:
    """Update the calorie value of an existing meal record (ensures non-negative value)."""
    resp = _env.adjust_meal_record_calories(**req.model_dump(exclude_none=True))
    _log_call("/personal_nutrition_tracking/adjust_meal_record_calories", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/personal_nutrition_tracking/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/personal_nutrition_tracking/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9331")))
