"""Mock Telemedicine Dermatology API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import TelemedicineDermatologyPlatform  # noqa: E402

app = FastAPI(title="Mock Telemedicine Dermatology API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "TELEMEDICINE_DERMATOLOGY_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: TelemedicineDermatologyPlatform | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = TelemedicineDermatologyPlatform(init_config=init_cfg)
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


@app.post("/telemedicine_dermatology/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/telemedicine_dermatology/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/telemedicine_dermatology/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/telemedicine_dermatology/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve a user's profile and role using their unique _id."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/get_user_by_id", req.model_dump(), resp)
    return resp


class GetUserByEmailRequest(BaseModel):
    email: str

@app.post("/telemedicine_dermatology/get_user_by_email")
def endpoint_get_user_by_email(req: GetUserByEmailRequest) -> dict[str, Any]:
    """Look up user identity and role by registered email."""
    resp = _env.get_user_by_email(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/get_user_by_email", req.model_dump(), resp)
    return resp


class CheckUserAuthenticationRequest(BaseModel):
    user_id: str
    provided_credential: str

@app.post("/telemedicine_dermatology/check_user_authentication")
def endpoint_check_user_authentication(req: CheckUserAuthenticationRequest) -> dict[str, Any]:
    """Verify whether a user is authenticated to act (upload/view)."""
    resp = _env.check_user_authentication(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/check_user_authentication", req.model_dump(), resp)
    return resp


class GetUserRoleRequest(BaseModel):
    user_id: str

@app.post("/telemedicine_dermatology/get_user_role")
def endpoint_get_user_role(req: GetUserRoleRequest) -> dict[str, Any]:
    """Get the role of a user ("patient" or "provider") for access control."""
    resp = _env.get_user_role(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/get_user_role", req.model_dump(), resp)
    return resp


class ListUserConsultationsRequest(BaseModel):
    user_id: str

@app.post("/telemedicine_dermatology/list_user_consultations")
def endpoint_list_user_consultations(req: ListUserConsultationsRequest) -> dict[str, Any]:
    """List all consultations where a given user is a patient or provider."""
    resp = _env.list_user_consultations(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/list_user_consultations", req.model_dump(), resp)
    return resp


class GetConsultationByIdRequest(BaseModel):
    consultation_id: str

@app.post("/telemedicine_dermatology/get_consultation_by_id")
def endpoint_get_consultation_by_id(req: GetConsultationByIdRequest) -> dict[str, Any]:
    """Retrieve full details of a specific consultation session."""
    resp = _env.get_consultation_by_id(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/get_consultation_by_id", req.model_dump(), resp)
    return resp


class ListProviderConsultationsRequest(BaseModel):
    provider_id: str

@app.post("/telemedicine_dermatology/list_provider_consultations")
def endpoint_list_provider_consultations(req: ListProviderConsultationsRequest) -> dict[str, Any]:
    """List all consultations assigned to a specified provider."""
    resp = _env.list_provider_consultations(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/list_provider_consultations", req.model_dump(), resp)
    return resp


class ListImagesForConsultationRequest(BaseModel):
    consultation_id: str

@app.post("/telemedicine_dermatology/list_images_for_consultation")
def endpoint_list_images_for_consultation(req: ListImagesForConsultationRequest) -> dict[str, Any]:
    """Retrieve all image files and info linked to a given consultation."""
    resp = _env.list_images_for_consultation(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/list_images_for_consultation", req.model_dump(), resp)
    return resp


class GetImageMetadataRequest(BaseModel):
    image_id: str

@app.post("/telemedicine_dermatology/get_image_metadata")
def endpoint_get_image_metadata(req: GetImageMetadataRequest) -> dict[str, Any]:
    """Retrieve metadata for a specific image (body location, upload time, etc.)."""
    resp = _env.get_image_metadata(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/get_image_metadata", req.model_dump(), resp)
    return resp


class CanUserAccessImageRequest(BaseModel):
    user_id: str
    image_id: str

@app.post("/telemedicine_dermatology/can_user_access_image")
def endpoint_can_user_access_image(req: CanUserAccessImageRequest) -> dict[str, Any]:
    """Check if a given user is permitted to access/view an image based on privacy rules."""
    resp = _env.can_user_access_image(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/can_user_access_image", req.model_dump(), resp)
    return resp


class CreateConsultationRequest(BaseModel):
    patient_id: str
    provider_id: str
    start_time: str
    note: str = ""

@app.post("/telemedicine_dermatology/create_consultation")
def endpoint_create_consultation(req: CreateConsultationRequest) -> dict[str, Any]:
    """Initiate a new consultation (only for users with role "patient")."""
    resp = _env.create_consultation(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/create_consultation", req.model_dump(), resp)
    return resp


class UploadImageToConsultationRequest(BaseModel):
    user_id: str
    authentication_credential: str
    file_location: str
    upload_timestamp: str
    body_location: str
    metadata: Dict
    consultation_id: str | None = None
    provider_id: str | None = None

@app.post("/telemedicine_dermatology/upload_image_to_consultation")
def endpoint_upload_image_to_consultation(req: UploadImageToConsultationRequest) -> dict[str, Any]:
    """Upload a new image for dermatology analysis, linked to an existing or new consultation (only for authenticated users)."""
    resp = _env.upload_image_to_consultation(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/upload_image_to_consultation", req.model_dump(), resp)
    return resp


class UpdateConsultationNoteRequest(BaseModel):
    consultation_id: str
    note: str

@app.post("/telemedicine_dermatology/update_consultation_note")
def endpoint_update_consultation_note(req: UpdateConsultationNoteRequest) -> dict[str, Any]:
    """Add or update notes/details within a consultation record."""
    resp = _env.update_consultation_note(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/update_consultation_note", req.model_dump(), resp)
    return resp


class UpdateImageMetadataRequest(BaseModel):
    image_id: str
    metadata_updates: dict

@app.post("/telemedicine_dermatology/update_image_metadata")
def endpoint_update_image_metadata(req: UpdateImageMetadataRequest) -> dict[str, Any]:
    """Modify metadata fields of a stored image (e.g., body location)."""
    resp = _env.update_image_metadata(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/update_image_metadata", req.model_dump(), resp)
    return resp


class RestrictImageAccessRequest(BaseModel):
    image_id: str
    restrictions: dict

@app.post("/telemedicine_dermatology/restrict_image_access")
def endpoint_restrict_image_access(req: RestrictImageAccessRequest) -> dict[str, Any]:
    """Apply or modify access restrictions on images to comply with privacy regulations."""
    resp = _env.restrict_image_access(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/restrict_image_access", req.model_dump(), resp)
    return resp


class RemoveImageFromConsultationRequest(BaseModel):
    image_id: str
    user_id: str

@app.post("/telemedicine_dermatology/remove_image_from_consultation")
def endpoint_remove_image_from_consultation(req: RemoveImageFromConsultationRequest) -> dict[str, Any]:
    """Delete an image from a consultation (for privacy, error correction, or compliance reasons)."""
    resp = _env.remove_image_from_consultation(**req.model_dump(exclude_none=True))
    _log_call("/telemedicine_dermatology/remove_image_from_consultation", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/telemedicine_dermatology/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/telemedicine_dermatology/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9317")))