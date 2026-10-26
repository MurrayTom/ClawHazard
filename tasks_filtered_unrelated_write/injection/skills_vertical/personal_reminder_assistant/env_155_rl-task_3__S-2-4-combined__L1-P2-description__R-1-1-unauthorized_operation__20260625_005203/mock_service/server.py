"""Mock Personal Reminder Assistant API service (FastAPI)."""

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

from env_class import MobileReminderSystem  # noqa: E402

app = FastAPI(title="Mock Personal Reminder Assistant API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "PERSONAL_REMINDER_ASSISTANT_FIXTURES",
    str(_SKILL_DIR / "env_155_rl-task_3.json"),
))

_env: MobileReminderSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = MobileReminderSystem(init_config=init_cfg)
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


@app.post("/personal_reminder_assistant/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/personal_reminder_assistant/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/personal_reminder_assistant/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

class GetUserByNameRequest(BaseModel):
    name: str

@app.post("/personal_reminder_assistant/get_user_by_name")
def endpoint_get_user_by_name(req: GetUserByNameRequest) -> dict[str, Any]:
    """Retrieve user info by name."""
    resp = _env.get_user_by_name(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_user_by_name", req.model_dump(), resp)
    return resp


class GetUserByIdRequest(BaseModel):
    user_id: str

@app.post("/personal_reminder_assistant/get_user_by_id")
def endpoint_get_user_by_id(req: GetUserByIdRequest) -> dict[str, Any]:
    """Retrieve user info by unique user ID."""
    resp = _env.get_user_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_user_by_id", req.model_dump(), resp)
    return resp


@app.post("/personal_reminder_assistant/list_all_users")
def endpoint_list_all_users() -> dict[str, Any]:
    """Retrieve all users registered in the system."""
    resp = _env.list_all_users()
    _log_call("/personal_reminder_assistant/list_all_users", {}, resp)
    return resp


class GetUserNotificationPreferenceRequest(BaseModel):
    user_id: str

@app.post("/personal_reminder_assistant/get_user_notification_preference")
def endpoint_get_user_notification_preference(req: GetUserNotificationPreferenceRequest) -> dict[str, Any]:
    """Query a user's notification preference (e.g., push, email, sms)."""
    resp = _env.get_user_notification_preference(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_user_notification_preference", req.model_dump(), resp)
    return resp


class ListUserRemindersRequest(BaseModel):
    user_id: str

@app.post("/personal_reminder_assistant/list_user_reminders")
def endpoint_list_user_reminders(req: ListUserRemindersRequest) -> dict[str, Any]:
    """Retrieve all reminders for a specific user."""
    resp = _env.list_user_reminders(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/list_user_reminders", req.model_dump(), resp)
    return resp


class GetReminderByIdRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/get_reminder_by_id")
def endpoint_get_reminder_by_id(req: GetReminderByIdRequest) -> dict[str, Any]:
    """Retrieve full info for a reminder via its ID."""
    resp = _env.get_reminder_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_reminder_by_id", req.model_dump(), resp)
    return resp


class ListRemindersByStatusRequest(BaseModel):
    status: str

@app.post("/personal_reminder_assistant/list_reminders_by_status")
def endpoint_list_reminders_by_status(req: ListRemindersByStatusRequest) -> dict[str, Any]:
    """List reminders filtered by status (pending, dismissed, snoozed)."""
    resp = _env.list_reminders_by_status(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/list_reminders_by_status", req.model_dump(), resp)
    return resp


class ListRemindersByCategoryRequest(BaseModel):
    category: str

@app.post("/personal_reminder_assistant/list_reminders_by_category")
def endpoint_list_reminders_by_category(req: ListRemindersByCategoryRequest) -> dict[str, Any]:
    """List reminders filtered by category (e.g., medication, appointment)."""
    resp = _env.list_reminders_by_category(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/list_reminders_by_category", req.model_dump(), resp)
    return resp


class GetReminderStatusRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/get_reminder_status")
def endpoint_get_reminder_status(req: GetReminderStatusRequest) -> dict[str, Any]:
    """Query current status of a specific reminder."""
    resp = _env.get_reminder_status(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_reminder_status", req.model_dump(), resp)
    return resp


class GetReminderRecurrenceRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/get_reminder_recurrence")
def endpoint_get_reminder_recurrence(req: GetReminderRecurrenceRequest) -> dict[str, Any]:
    """Query recurrence rule of a specific reminder."""
    resp = _env.get_reminder_recurrence(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_reminder_recurrence", req.model_dump(), resp)
    return resp


class GetReminderHistoryRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/get_reminder_history")
def endpoint_get_reminder_history(req: GetReminderHistoryRequest) -> dict[str, Any]:
    """Retrieve status change events for a given reminder."""
    resp = _env.get_reminder_history(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_reminder_history", req.model_dump(), resp)
    return resp


class ListReminderNotificationsRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/list_reminder_notifications")
def endpoint_list_reminder_notifications(req: ListReminderNotificationsRequest) -> dict[str, Any]:
    """Retrieve all notification records for a specific reminder."""
    resp = _env.list_reminder_notifications(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/list_reminder_notifications", req.model_dump(), resp)
    return resp


class GetNotificationByIdRequest(BaseModel):
    notification_id: str

@app.post("/personal_reminder_assistant/get_notification_by_id")
def endpoint_get_notification_by_id(req: GetNotificationByIdRequest) -> dict[str, Any]:
    """Retrieve notification info by notification ID."""
    resp = _env.get_notification_by_id(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_notification_by_id", req.model_dump(), resp)
    return resp


class GetNotificationDeliveryStatusRequest(BaseModel):
    notification_id: str

@app.post("/personal_reminder_assistant/get_notification_delivery_status")
def endpoint_get_notification_delivery_status(req: GetNotificationDeliveryStatusRequest) -> dict[str, Any]:
    """Query delivery status of a notification."""
    resp = _env.get_notification_delivery_status(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/get_notification_delivery_status", req.model_dump(), resp)
    return resp


class CreateReminderRequest(BaseModel):
    user_id: str
    message: str
    scheduled_time: str
    recurrence_rule: str
    category: str

@app.post("/personal_reminder_assistant/create_reminder")
def endpoint_create_reminder(req: CreateReminderRequest) -> dict[str, Any]:
    """Add a new reminder for a specific user with message, time, recurrence, etc."""
    resp = _env.create_reminder(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/create_reminder", req.model_dump(), resp)
    return resp


class UpdateReminderMessageRequest(BaseModel):
    reminder_id: str
    new_message: str

@app.post("/personal_reminder_assistant/update_reminder_message")
def endpoint_update_reminder_message(req: UpdateReminderMessageRequest) -> dict[str, Any]:
    """Change the text/message of an existing reminder."""
    resp = _env.update_reminder_message(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/update_reminder_message", req.model_dump(), resp)
    return resp


class UpdateReminderTimeRequest(BaseModel):
    reminder_id: str
    new_scheduled_time: str

@app.post("/personal_reminder_assistant/update_reminder_time")
def endpoint_update_reminder_time(req: UpdateReminderTimeRequest) -> dict[str, Any]:
    """Change the scheduled time of an existing reminder."""
    resp = _env.update_reminder_time(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/update_reminder_time", req.model_dump(), resp)
    return resp


class UpdateReminderRecurrenceRequest(BaseModel):
    reminder_id: str
    new_recurrence_rule: str

@app.post("/personal_reminder_assistant/update_reminder_recurrence")
def endpoint_update_reminder_recurrence(req: UpdateReminderRecurrenceRequest) -> dict[str, Any]:
    """Change the recurrence rule of an existing reminder."""
    resp = _env.update_reminder_recurrence(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/update_reminder_recurrence", req.model_dump(), resp)
    return resp


class UpdateReminderStatusRequest(BaseModel):
    reminder_id: str
    new_status: str

@app.post("/personal_reminder_assistant/update_reminder_status")
def endpoint_update_reminder_status(req: UpdateReminderStatusRequest) -> dict[str, Any]:
    """Manually change the status of a reminder (e.g., to dismissed or snoozed)."""
    resp = _env.update_reminder_status(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/update_reminder_status", req.model_dump(), resp)
    return resp


class DeleteReminderRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/delete_reminder")
def endpoint_delete_reminder(req: DeleteReminderRequest) -> dict[str, Any]:
    """Permanently remove a reminder from the system."""
    resp = _env.delete_reminder(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/delete_reminder", req.model_dump(), resp)
    return resp


class CreateNotificationRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/create_notification")
def endpoint_create_notification(req: CreateNotificationRequest) -> dict[str, Any]:
    """Manually trigger notification creation for a reminder."""
    resp = _env.create_notification(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/create_notification", req.model_dump(), resp)
    return resp


class UpdateNotificationDeliveryStatusRequest(BaseModel):
    notification_id: str
    new_status: str

@app.post("/personal_reminder_assistant/update_notification_delivery_status")
def endpoint_update_notification_delivery_status(req: UpdateNotificationDeliveryStatusRequest) -> dict[str, Any]:
    """Update the delivery status of a notification (e.g., mark as delivered or failed)."""
    resp = _env.update_notification_delivery_status(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/update_notification_delivery_status", req.model_dump(), resp)
    return resp


class DismissReminderRequest(BaseModel):
    reminder_id: str

@app.post("/personal_reminder_assistant/dismiss_reminder")
def endpoint_dismiss_reminder(req: DismissReminderRequest) -> dict[str, Any]:
    """Dismiss an active reminder (status → dismissed)."""
    resp = _env.dismiss_reminder(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/dismiss_reminder", req.model_dump(), resp)
    return resp


class SnoozeReminderRequest(BaseModel):
    reminder_id: str
    snooze_minutes: int = 10

@app.post("/personal_reminder_assistant/snooze_reminder")
def endpoint_snooze_reminder(req: SnoozeReminderRequest) -> dict[str, Any]:
    """Snooze a pending reminder, rescheduling its next notification."""
    resp = _env.snooze_reminder(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/snooze_reminder", req.model_dump(), resp)
    return resp


class SetUserNotificationPreferenceRequest(BaseModel):
    user_id: str
    new_preference: str

@app.post("/personal_reminder_assistant/set_user_notification_preference")
def endpoint_set_user_notification_preference(req: SetUserNotificationPreferenceRequest) -> dict[str, Any]:
    """Change the notification channel for a user (e.g., switch from push to email)."""
    resp = _env.set_user_notification_preference(**req.model_dump(exclude_none=True))
    _log_call("/personal_reminder_assistant/set_user_notification_preference", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/personal_reminder_assistant/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/personal_reminder_assistant/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9308")))
