"""Mock Professional Review Platform API service (FastAPI)."""

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

from env_class import OnlineProfessionalReviewPlatform  # noqa: E402

app = FastAPI(title="Mock Professional Review Platform API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PROFESSIONAL_REVIEW_PLATFORM_FIXTURES",
    str(_SKILL_DIR / "env_184_rl-task_5.json"),
))

_env: OnlineProfessionalReviewPlatform | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = OnlineProfessionalReviewPlatform(init_config=init_cfg)
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


@app.post("/professional_review_platform/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/professional_review_platform/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/professional_review_platform/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByUsernameRequest(BaseModel):
    username: str

@app.post("/professional_review_platform/get_user_by_username")
def endpoint_get_user_by_username(req: GetUserByUsernameRequest) -> dict[str, Any]:
    """Retrieve user info (including _id, username, and status) by username."""
    resp = _env.get_user_by_username(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_user_by_username", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    model_config = {"populate_by_name": True}
    id_field: str = Field(alias="_id")

@app.post("/professional_review_platform/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user info by _id."""
    resp = _env.get_user_by_id(_id=req.id_field)
    _log_call("/professional_review_platform/get_user_by_id", {"_id": req.id_field}, resp)
    return resp


@app.post("/professional_review_platform/list_all_users")
def endpoint_list_all_users() -> dict[str, Any]:
    """Return a list of all registered users."""
    resp = _env.list_all_users()
    _log_call("/professional_review_platform/list_all_users", {}, resp)
    return resp


class GetProfessionalByNameRequest(BaseModel):
    name: str

@app.post("/professional_review_platform/get_professional_by_name")
def endpoint_get_professional_by_name(req: GetProfessionalByNameRequest) -> dict[str, Any]:
    """Retrieve professional info (professional_id, name, specialty) by name."""
    resp = _env.get_professional_by_name(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_professional_by_name", req.model_dump(), resp)
    return resp


class GetProfessionalByIdRequest(BaseModel):
    professional_id: str

@app.post("/professional_review_platform/get_professional_by_id")
def endpoint_get_professional_by_id(req: GetProfessionalByIdRequest) -> dict[str, Any]:
    """Retrieve professional info by professional_id."""
    resp = _env.get_professional_by_id(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_professional_by_id", req.model_dump(), resp)
    return resp


@app.post("/professional_review_platform/list_all_professionals")
def endpoint_list_all_professionals() -> dict[str, Any]:
    """Return a list of all professionals on the platform."""
    resp = _env.list_all_professionals()
    _log_call("/professional_review_platform/list_all_professionals", {}, resp)
    return resp


class GetReviewsByUserRequest(BaseModel):
    user_id: str

@app.post("/professional_review_platform/get_reviews_by_user")
def endpoint_get_reviews_by_user(req: GetReviewsByUserRequest) -> dict[str, Any]:
    """Retrieve all reviews submitted by a particular user."""
    resp = _env.get_reviews_by_user(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_reviews_by_user", req.model_dump(), resp)
    return resp


class GetReviewsForProfessionalRequest(BaseModel):
    professional_id: str

@app.post("/professional_review_platform/get_reviews_for_professional")
def endpoint_get_reviews_for_professional(req: GetReviewsForProfessionalRequest) -> dict[str, Any]:
    """Retrieve all reviews linked to a given professional."""
    resp = _env.get_reviews_for_professional(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_reviews_for_professional", req.model_dump(), resp)
    return resp


class GetReviewByUserAndProfessionalRequest(BaseModel):
    user_id: str
    professional_id: str

@app.post("/professional_review_platform/get_review_by_user_and_professional")
def endpoint_get_review_by_user_and_professional(req: GetReviewByUserAndProfessionalRequest) -> dict[str, Any]:
    """Retrieve the review submitted by a user for a specific professional (if any)."""
    resp = _env.get_review_by_user_and_professional(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_review_by_user_and_professional", req.model_dump(), resp)
    return resp


class GetReviewByIdRequest(BaseModel):
    view_id: str

@app.post("/professional_review_platform/get_review_by_id")
def endpoint_get_review_by_id(req: GetReviewByIdRequest) -> dict[str, Any]:
    """Get the details of a review by its view_id."""
    resp = _env.get_review_by_id(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_review_by_id", req.model_dump(), resp)
    return resp


class GetReviewModerationStatusRequest(BaseModel):
    view_id: str

@app.post("/professional_review_platform/get_review_moderation_status")
def endpoint_get_review_moderation_status(req: GetReviewModerationStatusRequest) -> dict[str, Any]:
    """Retrieve the moderation status of a specific review (pending, approved, rejected)."""
    resp = _env.get_review_moderation_status(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_review_moderation_status", req.model_dump(), resp)
    return resp


class GetAggregatedRatingForProfessionalRequest(BaseModel):
    professional_id: str

@app.post("/professional_review_platform/get_aggregated_rating_for_professional")
def endpoint_get_aggregated_rating_for_professional(req: GetAggregatedRatingForProfessionalRequest) -> dict[str, Any]:
    """Get the current aggregated (average) rating for a given professional."""
    resp = _env.get_aggregated_rating_for_professional(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/get_aggregated_rating_for_professional", req.model_dump(), resp)
    return resp


class SubmitReviewRequest(BaseModel):
    user_id: str
    professional_id: str
    rating: float
    review_text: str
    submission_date: str

@app.post("/professional_review_platform/submit_review")
def endpoint_submit_review(req: SubmitReviewRequest) -> dict[str, Any]:
    """Create and submit a new review for a professional by a user, subject to constraints."""
    resp = _env.submit_review(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/submit_review", req.model_dump(), resp)
    return resp


class EditReviewRequest(BaseModel):
    view_id: str
    new_rating: float | None = None
    new_review_text: str | None = None

@app.post("/professional_review_platform/edit_review")
def endpoint_edit_review(req: EditReviewRequest) -> dict[str, Any]:
    """Modify the content or rating of an existing review (prior to moderation or per platform rules)."""
    params = {"view_id": req.view_id}
    if req.new_rating is not None:
        params["new_rating"] = req.new_rating
    if req.new_review_text is not None:
        params["new_review_text"] = req.new_review_text
    resp = _env.edit_review(**params)
    _log_call("/professional_review_platform/edit_review", req.model_dump(), resp)
    return resp


class DeleteReviewRequest(BaseModel):
    review_id: str

@app.post("/professional_review_platform/delete_review")
def endpoint_delete_review(req: DeleteReviewRequest) -> dict[str, Any]:
    """Remove a review submitted by a user."""
    resp = _env.delete_review(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/delete_review", req.model_dump(), resp)
    return resp


class ChangeReviewModerationStatusRequest(BaseModel):
    view_id: str
    new_status: str

@app.post("/professional_review_platform/change_review_moderation_status")
def endpoint_change_review_moderation_status(req: ChangeReviewModerationStatusRequest) -> dict[str, Any]:
    """Update the moderation status of a review (e.g., to approve or reject)."""
    resp = _env.change_review_moderation_status(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/change_review_moderation_status", req.model_dump(), resp)
    return resp


class UpdateProfessionalAggregatedRatingRequest(BaseModel):
    professional_id: str

@app.post("/professional_review_platform/update_professional_aggregated_rating")
def endpoint_update_professional_aggregated_rating(req: UpdateProfessionalAggregatedRatingRequest) -> dict[str, Any]:
    """Recalculate and update the professional's aggregated rating when a new approved review is added or changed."""
    resp = _env.update_professional_aggregated_rating(**req.model_dump(exclude_none=True))
    _log_call("/professional_review_platform/update_professional_aggregated_rating", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/professional_review_platform/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/professional_review_platform/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9302")))