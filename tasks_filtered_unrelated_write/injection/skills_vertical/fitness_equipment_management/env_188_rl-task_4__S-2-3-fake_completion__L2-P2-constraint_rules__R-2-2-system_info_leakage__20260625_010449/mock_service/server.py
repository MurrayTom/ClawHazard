"""Mock Fitness Equipment Management API service (FastAPI)."""

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

from env_class import FitnessEquipmentManagementSystem  # noqa: E402

app = FastAPI(title="Mock Fitness Equipment Management API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "FITNESS_EQUIPMENT_MANAGEMENT_FIXTURES",
    str(_SKILL_DIR / "env_188_rl-task_4.json"),
))

_env: FitnessEquipmentManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = FitnessEquipmentManagementSystem(init_config=init_cfg)
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


@app.post("/fitness_equipment_management/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/fitness_equipment_management/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/fitness_equipment_management/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetMachineByIdRequest(BaseModel):
    machine_id: str

@app.post("/fitness_equipment_management/get_machine_by_id")
def endpoint_get_machine_by_id(req: GetMachineByIdRequest) -> dict[str, Any]:
    """Retrieve all info for a machine given its unique machine_id."""
    resp = _env.get_machine_by_id(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_machine_by_id", req.model_dump(), resp)
    return resp


class GetMachineConditionRequest(BaseModel):
    machine_id: str

@app.post("/fitness_equipment_management/get_machine_condition")
def endpoint_get_machine_condition(req: GetMachineConditionRequest) -> dict[str, Any]:
    """Query the current condition/status of a machine ("operational", "requires maintenance", "out of order")."""
    resp = _env.get_machine_condition(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_machine_condition", req.model_dump(), resp)
    return resp


@app.post("/fitness_equipment_management/list_all_machines")
def endpoint_list_all_machines() -> dict[str, Any]:
    """Retrieve the complete list of fitness machines in the system."""
    resp = _env.list_all_machines()
    _log_call("/fitness_equipment_management/list_all_machines", {}, resp)
    return resp


class ListMachinesByLocationRequest(BaseModel):
    location_id: str

@app.post("/fitness_equipment_management/list_machines_by_location")
def endpoint_list_machines_by_location(req: ListMachinesByLocationRequest) -> dict[str, Any]:
    """Get all machines placed in a specified location (by location_id)."""
    resp = _env.list_machines_by_location(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/list_machines_by_location", req.model_dump(), resp)
    return resp


class GetUsageStatisticsRequest(BaseModel):
    machine_id: str

@app.post("/fitness_equipment_management/get_usage_statistics")
def endpoint_get_usage_statistics(req: GetUsageStatisticsRequest) -> dict[str, Any]:
    """Retrieve usage data (hours, count, last used) for a specific machine."""
    resp = _env.get_usage_statistics(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_usage_statistics", req.model_dump(), resp)
    return resp


class GetMaintenanceHistoryRequest(BaseModel):
    machine_id: str

@app.post("/fitness_equipment_management/get_maintenance_history")
def endpoint_get_maintenance_history(req: GetMaintenanceHistoryRequest) -> dict[str, Any]:
    """Get all maintenance records associated with a given machine_id."""
    resp = _env.get_maintenance_history(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_maintenance_history", req.model_dump(), resp)
    return resp


class GetLocationByIdRequest(BaseModel):
    location_id: str

@app.post("/fitness_equipment_management/get_location_by_id")
def endpoint_get_location_by_id(req: GetLocationByIdRequest) -> dict[str, Any]:
    """Get details about a specified facility location."""
    resp = _env.get_location_by_id(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_location_by_id", req.model_dump(), resp)
    return resp


class GetStaffByIdRequest(BaseModel):
    staff_id: str

@app.post("/fitness_equipment_management/get_staff_by_id")
def endpoint_get_staff_by_id(req: GetStaffByIdRequest) -> dict[str, Any]:
    """Get information on staff members by staff_id."""
    resp = _env.get_staff_by_id(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/get_staff_by_id", req.model_dump(), resp)
    return resp


@app.post("/fitness_equipment_management/list_all_locations")
def endpoint_list_all_locations() -> dict[str, Any]:
    """Retrieve all locations available within the facility."""
    resp = _env.list_all_locations()
    _log_call("/fitness_equipment_management/list_all_locations", {}, resp)
    return resp


@app.post("/fitness_equipment_management/list_all_staff")
def endpoint_list_all_staff() -> dict[str, Any]:
    """Retrieve a list of all staff members registered in the system."""
    resp = _env.list_all_staff()
    _log_call("/fitness_equipment_management/list_all_staff", {}, resp)
    return resp


class UpdateMachineConditionRequest(BaseModel):
    machine_id: str
    new_condition: str

@app.post("/fitness_equipment_management/update_machine_condition")
def endpoint_update_machine_condition(req: UpdateMachineConditionRequest) -> dict[str, Any]:
    """Change a machine's current_condition to a new allowed state."""
    resp = _env.update_machine_condition(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/update_machine_condition", req.model_dump(), resp)
    return resp


class AssignMachineLocationRequest(BaseModel):
    machine_id: str
    location_id: str

@app.post("/fitness_equipment_management/assign_machine_location")
def endpoint_assign_machine_location(req: AssignMachineLocationRequest) -> dict[str, Any]:
    """Move a machine to a new location (location_id)."""
    resp = _env.assign_machine_location(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/assign_machine_location", req.model_dump(), resp)
    return resp


class AddMaintenanceRecordRequest(BaseModel):
    record_id: str
    machine_id: str
    date: str
    action_performed: str
    staff_id: str
    notes: str | None = None

@app.post("/fitness_equipment_management/add_maintenance_record")
def endpoint_add_maintenance_record(req: AddMaintenanceRecordRequest) -> dict[str, Any]:
    """Create and store a new maintenance record for a machine, referencing valid staff."""
    resp = _env.add_maintenance_record(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/add_maintenance_record", req.model_dump(), resp)
    return resp


class EditMaintenanceRecordRequest(BaseModel):
    record_id: str
    action_performed: str | None = None
    date: str | None = None
    notes: str | None = None

@app.post("/fitness_equipment_management/edit_maintenance_record")
def endpoint_edit_maintenance_record(req: EditMaintenanceRecordRequest) -> dict[str, Any]:
    """Update attributes (notes, action, date) of an existing maintenance record."""
    resp = _env.edit_maintenance_record(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/edit_maintenance_record", req.model_dump(), resp)
    return resp


class DeleteMaintenanceRecordRequest(BaseModel):
    record_id: str

@app.post("/fitness_equipment_management/delete_maintenance_record")
def endpoint_delete_maintenance_record(req: DeleteMaintenanceRecordRequest) -> dict[str, Any]:
    """Remove a maintenance record from the history."""
    resp = _env.delete_maintenance_record(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/delete_maintenance_record", req.model_dump(), resp)
    return resp


class UpdateUsageStatisticsRequest(BaseModel):
    machine_id: str
    usage_hours: float | None = None
    usage_count: int | None = None
    last_used: str | None = None

@app.post("/fitness_equipment_management/update_usage_statistics")
def endpoint_update_usage_statistics(req: UpdateUsageStatisticsRequest) -> dict[str, Any]:
    """Update usage hours, count, or last_used timestamp for a machine."""
    resp = _env.update_usage_statistics(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/update_usage_statistics", req.model_dump(), resp)
    return resp


class AddMachineRequest(BaseModel):
    machine_id: str
    type: str
    model: str
    current_condition: str
    location: str

@app.post("/fitness_equipment_management/add_machine")
def endpoint_add_machine(req: AddMachineRequest) -> dict[str, Any]:
    """Add a new machine entry to the system (with unique machine_id)."""
    resp = _env.add_machine(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/add_machine", req.model_dump(), resp)
    return resp


class RemoveMachineRequest(BaseModel):
    machine_id: str

@app.post("/fitness_equipment_management/remove_machine")
def endpoint_remove_machine(req: RemoveMachineRequest) -> dict[str, Any]:
    """Delete a machine from the system (in case of disposal)."""
    resp = _env.remove_machine(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/remove_machine", req.model_dump(), resp)
    return resp


class AddLocationRequest(BaseModel):
    location_id: str
    name: str
    description: str

@app.post("/fitness_equipment_management/add_location")
def endpoint_add_location(req: AddLocationRequest) -> dict[str, Any]:
    """Add a new equipment location to the system."""
    resp = _env.add_location(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/add_location", req.model_dump(), resp)
    return resp


class UpdateLocationRequest(BaseModel):
    location_id: str
    name: str | None = None
    description: str | None = None

@app.post("/fitness_equipment_management/update_location")
def endpoint_update_location(req: UpdateLocationRequest) -> dict[str, Any]:
    """Modify details of an existing location."""
    resp = _env.update_location(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/update_location", req.model_dump(), resp)
    return resp


class RemoveLocationRequest(BaseModel):
    location_id: str

@app.post("/fitness_equipment_management/remove_location")
def endpoint_remove_location(req: RemoveLocationRequest) -> dict[str, Any]:
    """Delete a location (if no machine is assigned)."""
    resp = _env.remove_location(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/remove_location", req.model_dump(), resp)
    return resp


class AddStaffRequest(BaseModel):
    staff_id: str
    name: str
    role: str
    contact_info: str

@app.post("/fitness_equipment_management/add_staff")
def endpoint_add_staff(req: AddStaffRequest) -> dict[str, Any]:
    """Add a new staff member record to the system."""
    resp = _env.add_staff(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/add_staff", req.model_dump(), resp)
    return resp


class UpdateStaffRequest(BaseModel):
    staff_id: str
    name: str | None = None
    role: str | None = None
    contact_info: str | None = None

@app.post("/fitness_equipment_management/update_staff")
def endpoint_update_staff(req: UpdateStaffRequest) -> dict[str, Any]:
    """Edit info for a staff member."""
    resp = _env.update_staff(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/update_staff", req.model_dump(), resp)
    return resp


class RemoveStaffRequest(BaseModel):
    staff_id: str

@app.post("/fitness_equipment_management/remove_staff")
def endpoint_remove_staff(req: RemoveStaffRequest) -> dict[str, Any]:
    """Delete a staff member from the registry, if not referenced in maintenance records."""
    resp = _env.remove_staff(**req.model_dump(exclude_none=True))
    _log_call("/fitness_equipment_management/remove_staff", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/fitness_equipment_management/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/fitness_equipment_management/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9328")))
