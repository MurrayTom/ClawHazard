"""Mock State Medical Board Licensing API service (FastAPI)."""

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

from env_class import StateMedicalBoardProviderLicensingSystem  # noqa: E402

app = FastAPI(title="Mock State Medical Board Licensing API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "STATE_MEDICAL_BOARD_LICENSING_FIXTURES",
    str(_SKILL_DIR / "seed_data.json"),
))

_env: StateMedicalBoardProviderLicensingSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = StateMedicalBoardProviderLicensingSystem(init_config=init_cfg)
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


@app.post("/state_medical_board_licensing/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/state_medical_board_licensing/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/state_medical_board_licensing/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetProviderByNameRequest(BaseModel):
    name: str

@app.post("/state_medical_board_licensing/get_provider_by_name")
def endpoint_get_provider_by_name(req: GetProviderByNameRequest) -> dict[str, Any]:
    """Retrieve provider info by full or partial name."""
    resp = _env.get_provider_by_name(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_provider_by_name", req.model_dump(), resp)
    return resp


class GetProviderByIdRequest(BaseModel):
    provider_id: str

@app.post("/state_medical_board_licensing/get_provider_by_id")
def endpoint_get_provider_by_id(req: GetProviderByIdRequest) -> dict[str, Any]:
    """Retrieve provider data (demographics, profession, contact) via provider_id."""
    resp = _env.get_provider_by_id(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_provider_by_id", req.model_dump(), resp)
    return resp


@app.post("/state_medical_board_licensing/list_all_providers")
def endpoint_list_all_providers() -> dict[str, Any]:
    """Obtain a list of all registered providers in the system."""
    resp = _env.list_all_providers()
    _log_call("/state_medical_board_licensing/list_all_providers", {}, resp)
    return resp


class GetProviderLicensesRequest(BaseModel):
    provider_id: str

@app.post("/state_medical_board_licensing/get_provider_licenses")
def endpoint_get_provider_licenses(req: GetProviderLicensesRequest) -> dict[str, Any]:
    """Fetch all licenses associated with a particular provider_id."""
    resp = _env.get_provider_licenses(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_provider_licenses", req.model_dump(), resp)
    return resp


class GetLicenseByNumberStateProfessionRequest(BaseModel):
    license_number: str
    state: str
    profession: str

@app.post("/state_medical_board_licensing/get_license_by_number_state_profession")
def endpoint_get_license_by_number_state_profession(req: GetLicenseByNumberStateProfessionRequest) -> dict[str, Any]:
    """Retrieve a license record by its license_number, state, and profession (enforcing uniqueness constraint)."""
    resp = _env.get_license_by_number_state_profession(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_license_by_number_state_profession", req.model_dump(), resp)
    return resp


class ListLicensesByStateRequest(BaseModel):
    state: str

@app.post("/state_medical_board_licensing/list_licenses_by_state")
def endpoint_list_licenses_by_state(req: ListLicensesByStateRequest) -> dict[str, Any]:
    """List all licenses in a given state."""
    resp = _env.list_licenses_by_state(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/list_licenses_by_state", req.model_dump(), resp)
    return resp


class ListLicensesByStatusRequest(BaseModel):
    status: str

@app.post("/state_medical_board_licensing/list_licenses_by_status")
def endpoint_list_licenses_by_status(req: ListLicensesByStatusRequest) -> dict[str, Any]:
    """List all licenses with a specific status ("active", "expired", etc.)."""
    resp = _env.list_licenses_by_status(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/list_licenses_by_status", req.model_dump(), resp)
    return resp


class GetValidLicensesForProviderInStateRequest(BaseModel):
    provider_id: str
    state: str

@app.post("/state_medical_board_licensing/get_valid_licenses_for_provider_in_state")
def endpoint_get_valid_licenses_for_provider_in_state(req: GetValidLicensesForProviderInStateRequest) -> dict[str, Any]:
    """Return all currently valid (active, not expired) licenses for a given provider in a specified state."""
    resp = _env.get_valid_licenses_for_provider_in_state(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_valid_licenses_for_provider_in_state", req.model_dump(), resp)
    return resp


class GetLicenseStatusRequest(BaseModel):
    license_id: str

@app.post("/state_medical_board_licensing/get_license_status")
def endpoint_get_license_status(req: GetLicenseStatusRequest) -> dict[str, Any]:
    """Query the current status of a license, given its license_id."""
    resp = _env.get_license_status(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_license_status", req.model_dump(), resp)
    return resp


class GetLicenseExpirationDateRequest(BaseModel):
    license_id: str

@app.post("/state_medical_board_licensing/get_license_expiration_date")
def endpoint_get_license_expiration_date(req: GetLicenseExpirationDateRequest) -> dict[str, Any]:
    """Query the expiration date of a license."""
    resp = _env.get_license_expiration_date(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_license_expiration_date", req.model_dump(), resp)
    return resp


class GetLicenseActionsRequest(BaseModel):
    license_id: str

@app.post("/state_medical_board_licensing/get_license_actions")
def endpoint_get_license_actions(req: GetLicenseActionsRequest) -> dict[str, Any]:
    """List all historical actions (suspensions, reinstatements, etc.) for a particular license."""
    resp = _env.get_license_actions(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/get_license_actions", req.model_dump(), resp)
    return resp


class CheckLicenseValidityRequest(BaseModel):
    license_id: str
    current_date: str

@app.post("/state_medical_board_licensing/check_license_validity")
def endpoint_check_license_validity(req: CheckLicenseValidityRequest) -> dict[str, Any]:
    """Verify if a license is valid (active and not expired) given license_id and current date."""
    resp = _env.check_license_validity(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/check_license_validity", req.model_dump(), resp)
    return resp


class UpdateLicenseStatusRequest(BaseModel):
    license_id: str
    new_status: str
    action_type: str = "status change"
    action_description: str = ""

@app.post("/state_medical_board_licensing/update_license_status")
def endpoint_update_license_status(req: UpdateLicenseStatusRequest) -> dict[str, Any]:
    """Change the status of a license (e.g., suspend, revoke, reinstate)."""
    resp = _env.update_license_status(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/update_license_status", req.model_dump(), resp)
    return resp


class RecordLicenseActionRequest(BaseModel):
    license_id: str
    action_type: str
    action_date: str
    action_description: str

@app.post("/state_medical_board_licensing/record_license_action")
def endpoint_record_license_action(req: RecordLicenseActionRequest) -> dict[str, Any]:
    """Log a new action to the license's history (e.g., suspension, notification)."""
    resp = _env.record_license_action(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/record_license_action", req.model_dump(), resp)
    return resp


class UpdateLicenseExpirationDateRequest(BaseModel):
    license_id: str
    new_expiration_date: str

@app.post("/state_medical_board_licensing/update_license_expiration_date")
def endpoint_update_license_expiration_date(req: UpdateLicenseExpirationDateRequest) -> dict[str, Any]:
    """Modify the expiration date for a license, as part of renewal or compliance."""
    resp = _env.update_license_expiration_date(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/update_license_expiration_date", req.model_dump(), resp)
    return resp


class AddLicenseForProviderRequest(BaseModel):
    provider_id: str
    license_number: str
    state: str
    status: str
    issuance_date: str
    expiration_date: str
    profession: str

@app.post("/state_medical_board_licensing/add_license_for_provider")
def endpoint_add_license_for_provider(req: AddLicenseForProviderRequest) -> dict[str, Any]:
    """Issue a new license to a provider (add new license record)."""
    resp = _env.add_license_for_provider(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/add_license_for_provider", req.model_dump(), resp)
    return resp


class DeleteLicenseRequest(BaseModel):
    license_id: str

@app.post("/state_medical_board_licensing/delete_license")
def endpoint_delete_license(req: DeleteLicenseRequest) -> dict[str, Any]:
    """Remove a license for a provider (admin operation)."""
    resp = _env.delete_license(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/delete_license", req.model_dump(), resp)
    return resp


class UpdateProviderInfoRequest(BaseModel):
    provider_id: str
    name: str | None = None
    date_of_birth: str | None = None
    profession: str | None = None
    contact_information: str | None = None

@app.post("/state_medical_board_licensing/update_provider_info")
def endpoint_update_provider_info(req: UpdateProviderInfoRequest) -> dict[str, Any]:
    """Edit demographic or contact info for a provider."""
    resp = _env.update_provider_info(**req.model_dump(exclude_none=True))
    _log_call("/state_medical_board_licensing/update_provider_info", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/state_medical_board_licensing/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/state_medical_board_licensing/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9309")))
